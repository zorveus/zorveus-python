import pytest
import respx
import httpx
from zorveus import ZorveusServiceClient, AsyncZorveusServiceClient, InvalidDecimalError

SAMPLE_USER_PAYLOAD = {
    "product_end_user_id": "peu_101",
    "org_id": "org_123",
    "app_id": "app_123",
    "external_user_id": "ext_101",
    "display_name": "Sara Connor",
    "email_hash": None,
    "status": "active",
    "metadata": None,
    "usage": {
        "this_month": {
            "sell_cost": "0.000000000000",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "request_count": 0,
        },
        "total": {
            "sell_cost": "0.000000000000",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "request_count": 0,
        },
    },
    "cap": None,
    "credits": {
        "currency": "USD",
        "available_credits": "25.000000000000",
        "active_grant_count": 1,
        "expiring_soon_amount": "0.000000000000",
        "spent_this_month": "0.000000000000",
        "spent_total": "0.000000000000",
        "last_grant_at": None,
        "last_used_at": None,
    },
}

@respx.mock
def test_product_user_get_by_external_id():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    respx.get("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=SAMPLE_USER_PAYLOAD)
    )

    user = service.product_users.get_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
    )

    assert user.product_end_user_id == "peu_101"
    assert user.id == "peu_101"
    assert user.external_user_id == "ext_101"
    assert user.credits.available_credits == "25.000000000000"
    assert user.credit_summary.available_credits == "25.000000000000"

@respx.mock
def test_product_user_upsert_and_grant():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    upsert_response = {
        "product_user": SAMPLE_USER_PAYLOAD,
        "created": True,
    }

    respx.put("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=upsert_response)
    )

    user_res = service.product_users.create_or_update(
        app_id="app_123",
        external_user_id="ext_101",
        display_name="Sara Connor",
        email="sara@example.com",
    )

    assert user_res.product_user.id == "peu_101"
    assert user_res.product_user.display_name == "Sara Connor"
    assert user_res.created is True

    grant_response = {
        "product_user": SAMPLE_USER_PAYLOAD,
        "credit_grant": {
            "credit_grant_id": "grt_1",
            "product_end_user_id": "peu_101",
            "amount": "25.000000000000",
            "remaining_amount": "25.000000000000",
            "currency": "USD",
            "source": "promotion",
            "reason": "Welcome",
            "status": "active",
        },
        "credit_summary": {
            "currency": "USD",
            "available_credits": "25.000000000000",
            "active_grant_count": 1,
            "expiring_soon_amount": "0.000000000000",
            "spent_this_month": "0.000000000000",
            "spent_total": "0.000000000000",
        },
    }

    respx.post("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(200, json=grant_response)
    )

    grant_res = service.product_users.grant_credit_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
        amount="25.000000000000",
        source="promotion",
        reason="Welcome",
    )

    assert grant_res.credit_grant.amount == "25.000000000000"
    assert grant_res.credit_grant.id == "grt_1"
    assert grant_res.credit_summary.available_credits == "25.000000000000"

    with pytest.raises(InvalidDecimalError):
        service.product_users.grant_credit_by_external_id(
            app_id="app_123",
            external_user_id="ext_101",
            amount="invalid_amount",
        )

@pytest.mark.asyncio
@respx.mock
async def test_async_product_user_get_and_grant():
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test")

    respx.get("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=SAMPLE_USER_PAYLOAD)
    )

    user = await service.product_users.get_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
    )
    assert user.product_end_user_id == "peu_101"
    assert user.credits.available_credits == "25.000000000000"

