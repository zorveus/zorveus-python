from decimal import Decimal
import pytest
import respx
import httpx
from zorveus import (
    Zorveus,
    PaymentRequiredError,
    PermissionDeniedError,
    ProductUserAllowanceInsufficientError,
    CapExceededError,
    AppConnectionNotFoundError,
    ConflictError,
    ZorveusError,
)


@respx.mock
def test_payment_required_402():
    client = Zorveus(api_key="test_key")

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            402,
            json={
                "error": {
                    "code": "zorveus_reservation_insufficient_balance",
                    "message": "Organization wallet balance is insufficient to fund this request.",
                }
            },
            headers={
                "x-zorveus-request-id": "zreq_wallet_fail",
                "x-zorveus-reservation-id": "resv_wallet_fail",
            },
        )
    )

    with pytest.raises(PaymentRequiredError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hello"}],
        )

    err = exc_info.value
    assert err.status_code == 402
    assert err.code == "zorveus_reservation_insufficient_balance"
    assert err.request_id == "zreq_wallet_fail"
    assert err.reservation_id == "resv_wallet_fail"
    assert "Organization wallet balance is insufficient" in err.message
    assert isinstance(err, ZorveusError)


@respx.mock
def test_product_user_allowance_insufficient_403():
    client = Zorveus(api_key="test_key")

    payload = {
        "error": {
            "code": "zorveus_product_user_allowance_insufficient",
            "message": "This request is estimated to cost 0.010000000000 USD, but the product user has 0.004720000000 USD of AI allowance remaining.",
            "params": {
                "cap_rule_id": "cap_123",
                "cap_period": "monthly",
                "currency": "USD",
                "cap_amount": "0.010000000000",
                "settled_spend_this_period": "0.005280000000",
                "active_reservations_amount": "0.000000000000",
                "remaining_base_allowance": "0.004720000000",
                "promotional_credit_balance": "0.000000000000",
                "available_allowance": "0.004720000000",
                "estimated_request_cost": "0.010000000000",
                "shortfall": "0.005280000000",
            },
        }
    }

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            403,
            json=payload,
            headers={
                "x-zorveus-request-id": "zreq_allowance_fail",
                "x-zorveus-reservation-id": "resv_allowance_fail",
            },
        )
    )

    with pytest.raises(ProductUserAllowanceInsufficientError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "hello"}],
        )

    err = exc_info.value
    assert err.status_code == 403
    assert err.code == "zorveus_product_user_allowance_insufficient"
    assert err.request_id == "zreq_allowance_fail"
    assert err.reservation_id == "resv_allowance_fail"
    assert isinstance(err, PermissionDeniedError)
    assert isinstance(err, ZorveusError)

    # Verify decimal parsing
    assert err.params.cap_rule_id == "cap_123"
    assert err.params.cap_period == "monthly"
    assert err.params.currency == "USD"
    assert err.params.cap_amount == Decimal("0.010000000000")
    assert err.params.settled_spend_this_period == Decimal("0.005280000000")
    assert err.params.active_reservations_amount == Decimal("0.000000000000")
    assert err.params.remaining_base_allowance == Decimal("0.004720000000")
    assert err.params.promotional_credit_balance == Decimal("0.000000000000")
    assert err.params.available_allowance == Decimal("0.004720000000")
    assert err.params.estimated_request_cost == Decimal("0.010000000000")
    assert err.params.shortfall == Decimal("0.005280000000")


@respx.mock
def test_gateway_nested_error_format():
    client = Zorveus(api_key="test_key")

    nested_payload = {
        "error": {
            "message": "Top level gateway error",
            "type": "zorveus_error",
            "provider_specific_fields": {
                "error": {
                    "code": "zorveus_product_user_allowance_insufficient",
                    "message": "Nested shortfall message",
                    "params": {
                        "cap_amount": "50.000000000000",
                        "shortfall": "10.000000000000",
                    },
                }
            },
        }
    }

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(403, json=nested_payload)
    )

    with pytest.raises(ProductUserAllowanceInsufficientError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

    err = exc_info.value
    assert err.message == "Nested shortfall message"
    assert err.params.cap_amount == Decimal("50.000000000000")
    assert err.params.shortfall == Decimal("10.000000000000")


@respx.mock
def test_legacy_credits_insufficient_fallback():
    client = Zorveus(api_key="test_key")

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            403,
            json={
                "error": {
                    "code": "zorveus_product_user_credits_insufficient",
                    "message": "Legacy credits insufficient",
                    "params": {"shortfall": "1.000000000000"},
                }
            },
        )
    )

    with pytest.raises(ProductUserAllowanceInsufficientError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

    assert exc_info.value.params.shortfall == Decimal("1.000000000000")


@respx.mock
def test_cap_exceeded_403():
    client = Zorveus(api_key="test_key")

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            403,
            json={
                "error": {
                    "code": "zorveus_cap_exceeded",
                    "message": "Key cap exceeded",
                }
            },
        )
    )

    with pytest.raises(CapExceededError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

    assert isinstance(exc_info.value, PermissionDeniedError)


@respx.mock
def test_app_connection_not_found_403():
    client = Zorveus(api_key="test_key")

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            403,
            json={
                "error": {
                    "code": "zorveus_app_connection_not_found",
                    "message": "App connection not found or revoked",
                }
            },
        )
    )

    with pytest.raises(AppConnectionNotFoundError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

    assert isinstance(exc_info.value, PermissionDeniedError)


@respx.mock
def test_conflict_409():
    client = Zorveus(api_key="test_key")

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            409,
            json={
                "error": {
                    "code": "zorveus_reservation_conflict",
                    "message": "Idempotency key reused with conflicting parameters",
                }
            },
        )
    )

    with pytest.raises(ConflictError) as exc_info:
        client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "test"}],
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "zorveus_reservation_conflict"
    assert isinstance(exc_info.value, ZorveusError)
