# Zorveus Python SDK specification (`zorveus-python`)

Specification for building `zorveus` (the official Python SDK for the Zorveus AI Infrastructure Platform).

---

## 1. Executive summary & goals

The `zorveus` Python SDK provides Python 3.9+ developers with typed, synchronous, and asynchronous access to:
1. **Zorveus AI Gateway (Data Plane):** Chat completions, SSE streaming, model discovery, metadata attribution, and spend cap tracking.
2. **Zorveus Control Plane (Management API):** End-user profile management, credit grants ledger, and BYOK provider credentials administration via Organization Service Keys.
3. **Zorveus OAuth 2.0 PKCE:** Isomorphic PKCE generation, consent URL construction, state validation, and token exchange.

### Key design principles
- **Dual sync and async support:** Native `Zorveus` and `AsyncZorveus` clients powered by `httpx`.
- **Strict type safety and validation:** Pydantic v2 models for all request and response payloads.
- **Financial precision:** High-precision decimal strings for credit amounts (`"25.000000000000"`).
- **Zero bloat:** Clean error hierarchy (`ZorveusError`, `AuthenticationError`, `RateLimitError`, `InvalidDecimalError`).

---

## 2. Platform architecture & API endpoints

```
+-------------------------------------------------------------------------------+
|                             Zorveus Platform API                              |
+---------------------------------------+---------------------------------------+
                                        |
     +----------------------------------+----------------------------------+
     |                                                                     |
     v                                                                     v
+---------------------------------------+ +---------------------------------------+
|        AI Gateway (Data Plane)        | |     Control Plane (Management API)    |
|   https://api.zorveus.com/v1          | |     https://api.zorveus.com         |
|   (Inference Key / User OAuth Token)  | |     (Organization Service Key)      |
+---------------------------------------+ +---------------------------------------+
| • POST /v1/chat/completions           | | • PUT  /product-users/by-external-id |
| • GET  /v1/models                     | | • GET  /product-users/by-external-id |
| • GET  /inference-keys/usage          | | • POST /product-users/.../grants    |
|                                       | | • POST /provider-credentials/...    |
|                                       | | • POST /oauth/token                 |
+---------------------------------------+ +---------------------------------------+
```

---

## 3. Package layout and module design

Target directory tree for `zorveus-python`:

```text
zorveus-python/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
├── src/
│   └── zorveus/
│       ├── __init__.py
│       ├── _client.py               # Main Zorveus & AsyncZorveus clients
│       ├── _service_client.py       # ZorveusServiceClient & AsyncZorveusServiceClient
│       ├── _oauth.py                # ZorveusOAuth PKCE helper utilities
│       ├── _version.py              # SDK version constant ("0.1.0")
│       ├── errors.py                # Exception hierarchy
│       ├── http/
│       │   ├── __init__.py
│       │   ├── transport.py         # Sync HTTPTransport (httpx.Client wrapper)
│       │   ├── async_transport.py   # Async HTTPTransport (httpx.AsyncClient wrapper)
│       │   └── sse.py               # SSE stream parser
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── chat.py              # Sync & Async Chat Completions
│       │   ├── models.py            # Sync & Async Model Discovery
│       │   ├── product_users.py     # Sync & Async Product End-Users & Credits
│       │   └── provider_credentials.py # Sync & Async BYOK Provider Credentials
│       ├── types/
│       │   ├── __init__.py
│       │   ├── chat.py              # Pydantic models for chat
│       │   ├── models.py            # Pydantic models for models list
│       │   ├── product_users.py     # Pydantic models for product users & credits
│       │   └── provider_credentials.py # Pydantic models for provider credentials
│       └── utils/
│           ├── __init__.py
│           ├── decimal.py           # Decimal string validator
│           └── pkce.py              # Crypto PKCE generators (hashlib + secrets)
├── tests/
│   ├── test_chat.py
│   ├── test_product_users.py
│   ├── test_provider_credentials.py
│   ├── test_oauth.py
│   └── test_errors.py
└── examples/
    ├── basic_inference.py
    ├── user_management.py
    └── oauth_pkce_flow.py
```

---

## 4. Dependencies (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "zorveus"
version = "0.1.0"
description = "Official Python client library for the Zorveus AI Infrastructure Platform"
readme = "README.md"
requires-python = ">=3.9"
license = { text = "MIT" }
authors = [
    { name = "Zorveus Inc.", email = "engineering@zorveus.com" }
]
keywords = ["zorveus", "ai-gateway", "llm", "openai", "anthropic", "gemini", "sdk"]
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.5.0",
    "typing-extensions>=4.8.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "respx>=0.20.0",
    "mypy>=1.7.0",
    "ruff>=0.1.0"
]
```

---

## 5. Client implementations

### 5.1 Data Plane inference client (`Zorveus` and `AsyncZorveus`)

```python
import os
from typing import Optional, Dict, Any, List, AsyncGenerator, Iterator
from zorveus.resources.chat import ChatResource, AsyncChatResource
from zorveus.resources.models import ModelsResource, AsyncModelsResource
from zorveus.types.usage import UsageResponse
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport

class Zorveus:
    """Client for AI inference, chat streaming, model discovery, and spend queries."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")
        
        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")
        self._transport = SyncHTTPTransport(api_key=key, base_url=base_url, timeout=timeout)
        
        self.chat = ChatResource(self._transport)
        self.models = ModelsResource(self._transport)

    def get_usage() -> UsageResponse:
        """Query live spend cap, period spend, and remaining allowance."""
        return self._transport.get("/inference-keys/usage", response_model=UsageResponse)


class AsyncZorveus:
    """Asynchronous client for AI inference, chat streaming, and model discovery."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")
        
        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")
        self._transport = AsyncHTTPTransport(api_key=key, base_url=base_url, timeout=timeout)
        
        self.chat = AsyncChatResource(self._transport)
        self.models = AsyncModelsResource(self._transport)

    async def get_usage(self) -> UsageResponse:
        """Query live spend cap, period spend, and remaining allowance asynchronously."""
        return await self._transport.get("/inference-keys/usage", response_model=UsageResponse)
```

---

### 5.2 Control Plane administration client (`ZorveusServiceClient`)

```python
import os
from typing import Optional
from zorveus.resources.product_users import ProductUsersResource, AsyncProductUsersResource
from zorveus.resources.provider_credentials import ProviderCredentialsResource, AsyncProviderCredentialsResource
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport

class ZorveusServiceClient:
    """Client for organization administration, product users, and credit grants."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_SERVICE_KEY")
        if not key:
            raise ValueError("Service key is required. Pass api_key or set ZORVEUS_SERVICE_KEY.")
        
        url = base_url or os.environ.get("ZORVEUS_BASE_URL", "https://api.zorveus.com")
        self._transport = SyncHTTPTransport(api_key=key, base_url=url, timeout=timeout)
        
        self.product_users = ProductUsersResource(self._transport)
        self.provider_credentials = ProviderCredentialsResource(self._transport)


class AsyncZorveusServiceClient:
    """Asynchronous client for organization administration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 60.0
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_SERVICE_KEY")
        if not key:
            raise ValueError("Service key is required. Pass api_key or set ZORVEUS_SERVICE_KEY.")
        
        url = base_url or os.environ.get("ZORVEUS_BASE_URL", "https://api.zorveus.com")
        self._transport = AsyncHTTPTransport(api_key=key, base_url=url, timeout=timeout)
        
        self.product_users = AsyncProductUsersResource(self._transport)
        self.provider_credentials = AsyncProviderCredentialsResource(self._transport)
```

---

## 6. OAuth 2.0 PKCE helper (`ZorveusOAuth`)

```python
import secrets
import hashlib
import base64
from urllib.parse import urlencode, parse_qs, urlparse
from typing import Dict, Any, Optional, List
import httpx
from pydantic import BaseModel, Field

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
        verifier_bytes = secrets.token_bytes(byte_length)
        code_verifier = base64.urlsafe_b64encode(verifier_bytes).decode("ascii").rstrip("=")
        
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        
        state_bytes = secrets.token_bytes(32)
        state = base64.urlsafe_b64encode(state_bytes).decode("ascii").rstrip("=")
        
        return PKCEData(code_verifier=code_verifier, code_challenge=code_challenge, state=state)

    @staticmethod
    def get_authorization_url(
        client_id: str,
        redirect_uri: str,
        state: str,
        code_challenge: str,
        *,
        scopes: Optional[List[str]] = None,
        base_url: str = "https://api.zorveus.com"
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
            "scope": scope_str
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
            return ValidationResult(valid=False, error="invalid_response", error_description="Missing authorization code")
        
        state = params.get("state", [None])[0]
        if expected_state and state != expected_state:
            return ValidationResult(valid=False, error="state_mismatch", error_description="State parameter does not match expected CSRF token")
        
        return ValidationResult(valid=True, code=code, state=state)

    @staticmethod
    def exchange_token(
        client_id: str,
        code: str,
        code_verifier: str,
        redirect_uri: str,
        *,
        client_secret: Optional[str] = None,
        base_url: str = "https://api.zorveus.com"
    ) -> TokenResponse:
        """Exchanges authorization code for Bearer access token."""
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri
        }
        if client_secret:
            payload["client_secret"] = client_secret

        with httpx.Client() as client:
            resp = client.post(f"{base_url.rstrip('/')}/oauth/token", data=payload)
            resp.raise_for_status()
            return TokenResponse.model_validate(resp.json())
```

---

## 7. Error handling hierarchy

```python
class ZorveusError(Exception):
    """Base exception for all Zorveus SDK errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, raw_body: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_body = raw_body

class AuthenticationError(ZorveusError):
    """Raised on 401 Unauthorized errors."""

class PermissionDeniedError(ZorveusError):
    """Raised on 403 Forbidden errors."""

class NotFoundError(ZorveusError):
    """Raised on 404 Not Found errors."""

class UnprocessableEntityError(ZorveusError):
    """Raised on 422 Validation errors."""

class RateLimitError(ZorveusError):
    """Raised on 429 Too Many Requests errors."""

class InvalidDecimalError(ZorveusError):
    """Raised when credit amount is not a valid decimal string."""
```

---

## 8. Usage examples

### 8.1 Streaming AI Chat Completions

```python
from zorveus import Zorveus

client = Zorveus(api_key="zrv_live_123...")

stream = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Explain quantum computing simply."}],
    stream=True,
    zorveus_metadata={"external_user_id": "usr_sara_101"}
)

for chunk in stream:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)
```

### 8.2 Product User Provisioning & Credit Granting

```python
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient(api_key="zrv_svc_123...")
app_id = "app_startup_123"
external_id = "usr_sara_101"

# 1. Upsert profile
user = service.product_users.create_or_update(
    app_id=app_id,
    external_user_id=external_id,
    display_name="Sara Connor",
    email="sara@example.com"
)

# 2. Grant credits
grant = service.product_users.grant_credit_by_external_id(
    app_id=app_id,
    external_user_id=external_id,
    amount="25.000000000000",
    source="promotion",
    reason="Welcome Bonus"
)

print(f"New Balance: ${grant.credit_summary.available_credits}")
```
