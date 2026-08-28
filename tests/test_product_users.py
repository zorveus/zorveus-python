import pytest
import respx
import httpx
from zorveus import ZorveusServiceClient, AsyncZorveusServiceClient, InvalidDecimalError

@respx.mock
def test_product_user_upsert_and_grant():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    user_response = {
        "product_user": {
            "id": "usr_101",
            "app_id": "app_123",
            "external_user_id": "ext_101",
            "display_name": "Sara Connor",
            "email": "sara@example.com",
        }
    }

    respx.put("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=user_response)
    )

    user_res = service.product_users.create_or_update(
        app_id="app_123",
        external_user_id="ext_101",
        display_name="Sara Connor",
        email="sara@example.com",
    )

    assert user_res.product_user.id == "usr_101"
    assert user_res.product_user.display_name == "Sara Connor"

    grant_response = {
        "credit_grant": {
            "id": "grt_1",
            "product_user_id": "usr_101",
            "amount": "25.000000000000",
            "source": "promotion",
            "reason": "Welcome",
        },
        "credit_summary": {
            "available_credits": "25.000000000000",
            "total_granted": "25.000000000000",
            "total_spent": "0.000000000000",
            "currency": "USD",
        },
    }

    respx.post("https://api.zorveus.com/product-users/by-external-id/grants").mock(
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
    assert grant_res.credit_summary.available_credits == "25.000000000000"

    with pytest.raises(InvalidDecimalError):
        service.product_users.grant_credit_by_external_id(
            app_id="app_123",
            external_user_id="ext_101",
            amount="invalid_amount",
        )
