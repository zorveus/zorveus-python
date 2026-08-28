import pytest
import respx
import httpx
from zorveus import ZorveusOAuth

def test_oauth_pkce_generation():
    pkce = ZorveusOAuth.generate_pkce()
    assert len(pkce.code_verifier) > 10
    assert len(pkce.code_challenge) > 10
    assert len(pkce.state) > 10

def test_authorization_url_construction():
    url = ZorveusOAuth.get_authorization_url(
        client_id="client_123",
        redirect_uri="https://app.example.com/callback",
        state="state_xyz",
        code_challenge="challenge_xyz",
    )
    assert "client_id=client_123" in url
    assert "redirect_uri=https%3A%2F%2Fapp.example.com%2Fcallback" in url
    assert "state=state_xyz" in url
    assert "code_challenge=challenge_xyz" in url
    assert "code_challenge_method=S256" in url

def test_callback_validation():
    # Valid redirect URL
    res = ZorveusOAuth.validate_callback(
        "https://app.example.com/callback?code=code_abc&state=state_xyz",
        expected_state="state_xyz",
    )
    assert res.valid is True
    assert res.code == "code_abc"
    assert res.state == "state_xyz"

    # State mismatch
    res_invalid = ZorveusOAuth.validate_callback(
        "https://app.example.com/callback?code=code_abc&state=wrong_state",
        expected_state="state_xyz",
    )
    assert res_invalid.valid is False
    assert res_invalid.error == "state_mismatch"

    # OAuth error response
    res_err = ZorveusOAuth.validate_callback(
        "https://app.example.com/callback?error=access_denied&error_description=User+cancelled",
    )
    assert res_err.valid is False
    assert res_err.error == "access_denied"
    assert res_err.error_description == "User cancelled"

@respx.mock
def test_token_exchange():
    respx.post("https://api.zorveus.com/oauth/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "token_live_123",
                "token_type": "Bearer",
                "app_connection_id": "conn_123",
            },
        )
    )

    token = ZorveusOAuth.exchange_token(
        client_id="client_123",
        code="code_abc",
        code_verifier="verifier_xyz",
        redirect_uri="https://app.example.com/callback",
    )
    assert token.access_token == "token_live_123"
    assert token.token_type == "Bearer"
    assert token.app_connection_id == "conn_123"
