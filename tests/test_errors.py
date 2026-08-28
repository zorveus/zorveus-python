import pytest
import respx
import httpx
from zorveus import (
    Zorveus,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
    RateLimitError,
    InvalidDecimalError,
)
from zorveus.utils.decimal import validate_decimal_string

def test_decimal_validation():
    assert validate_decimal_string("25.000000000000") == "25.000000000000"
    assert validate_decimal_string("10.5") == "10.5"
    assert validate_decimal_string("100") == "100"

    with pytest.raises(InvalidDecimalError):
        validate_decimal_string("invalid")

    with pytest.raises(InvalidDecimalError):
        validate_decimal_string("25.1234567890123")  # 13 decimal places

    with pytest.raises(InvalidDecimalError):
        validate_decimal_string(100)  # Not a string


@respx.mock
def test_error_status_codes():
    client = Zorveus(api_key="test_key")

    respx.get("https://api.zorveus.com/v1/models").mock(
        return_value=httpx.Response(401, json={"error": {"message": "Invalid API key"}})
    )
    with pytest.raises(AuthenticationError) as exc_info:
        client.models.list()
    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.message

    respx.get("https://api.zorveus.com/v1/models").mock(
        return_value=httpx.Response(403, json={"error": {"message": "Forbidden"}})
    )
    with pytest.raises(PermissionDeniedError):
        client.models.list()

    respx.get("https://api.zorveus.com/v1/models").mock(
        return_value=httpx.Response(404, json={"error": {"message": "Not Found"}})
    )
    with pytest.raises(NotFoundError):
        client.models.list()

    respx.get("https://api.zorveus.com/v1/models").mock(
        return_value=httpx.Response(422, json={"error": {"message": "Unprocessable"}})
    )
    with pytest.raises(UnprocessableEntityError):
        client.models.list()

    respx.get("https://api.zorveus.com/v1/models").mock(
        return_value=httpx.Response(429, json={"error": {"message": "Rate limited"}})
    )
    with pytest.raises(RateLimitError):
        client.models.list()
