import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Optional, List
import httpx
from pydantic import BaseModel
from zorveus.utils.pkce import generate_code_verifier, generate_code_challenge, generate_state
from zorveus.http.transport import raise_for_status

class PKCEData(BaseModel):
    code_verifier: str
    code_challenge: str
    state: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    app_connection_id: Optional[str] = None
    funding_org_id: Optional[str] = None

class ValidationResult(BaseModel):
    valid: bool
    code: Optional[str] = None
    state: Optional[str] = None
    error: Optional[str] = None
    error_description: Optional[str] = None


class ZorveusOAuth:
    """OAuth 2.0 PKCE and token management utilities."""

    @staticmethod
    def generate_pkce(byte_length: int = 32) -> PKCEData:
        """Generates RFC 7636 PKCE code_verifier, code_challenge (S256), and state."""
        verifier = generate_code_verifier(byte_length)
        challenge = generate_code_challenge(verifier)
        state = generate_state(byte_length)
        return PKCEData(code_verifier=verifier, code_challenge=challenge, state=state)

    @staticmethod
    def get_authorization_url(
        client_id: str,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        *,
        scopes: Optional[List[str]] = None,
        base_url: str = "https://api.zorveus.com",
    ) -> str:
        """Constructs Zorveus OAuth 2.0 authorization URL."""
        scope_str = " ".join(scopes) if scopes else "inference:write models:*"
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "response_type": "code",
            "scope": scope_str,
        }
        return f"{base_url.rstrip('/')}/oauth/authorize?{urlencode(params)}"

    @staticmethod
    def validate_callback(url_or_query: str, expected_state: Optional[str] = None) -> ValidationResult:
        """Validates OAuth redirect URL or query string against expected state token."""
        parsed = urlparse(url_or_query)
        params = parse_qs(parsed.query or url_or_query)

        raw_error = params.get("error", [None])[0]
        if raw_error:
            desc = params.get("error_description", [None])[0]
            return ValidationResult(valid=False, error=raw_error, error_description=desc)

        code = params.get("code", [None])[0]
        if not code:
            return ValidationResult(
                valid=False,
                error="invalid_response",
                error_description="Missing authorization code",
            )

        state = params.get("state", [None])[0]
        if expected_state and state != expected_state:
            return ValidationResult(
                valid=False,
                error="state_mismatch",
                error_description="State parameter does not match expected CSRF token",
            )

        return ValidationResult(valid=True, code=code, state=state)

    @staticmethod
    def exchange_token(
        client_id: str,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        *,
        client_secret: Optional[str] = None,
        base_url: str = "https://api.zorveus.com",
    ) -> TokenResponse:
        """Exchanges authorization code for Bearer access token."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        }
        if client_secret:
            payload["client_secret"] = client_secret

        with httpx.Client() as client:
            resp = client.post(f"{base_url.rstrip('/')}/oauth/token", data=payload)
            raise_for_status(resp)
            return TokenResponse.model_validate(resp.json())
