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
        "this_period": {
            "sell_cost": "0.000000000000",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "request_count": 0,
        },
        "period_start": "2026-10-01T00:00:00.000Z",
        "period_end": "2026-10-31T23:59:59.000Z",
        "total": {
            "sell_cost": "0.000000000000",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "request_count": 0,
        },
    },
    "cap": None,
    "direct_cap": None,
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


@respx.mock
def test_product_user_credit_summary_and_grants_list():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    summary_data = {
        "currency": "USD",
        "available_credits": "15.500000000000",
        "active_grant_count": 2,
        "expiring_soon_amount": "0.000000000000",
        "spent_this_month": "5.000000000000",
        "spent_total": "10.000000000000",
        "last_grant_at": None,
        "last_used_at": None,
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id/credit-summary").mock(
        return_value=httpx.Response(200, json=summary_data)
    )

    summary = service.product_users.get_credit_summary_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
    )
    assert summary.available_credits == "15.500000000000"
    assert summary.active_grant_count == 2
    assert summary.spent_this_month == "5.000000000000"

    grants_data = {
        "credit_grants": [
            {
                "credit_grant_id": "cgrt_1",
                "org_id": "org_123",
                "app_id": "app_123",
                "product_end_user_id": "peu_101",
                "amount": "10.000000000000",
                "remaining_amount": "10.000000000000",
                "currency": "USD",
                "source": "promotion",
                "status": "active",
            }
        ]
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(200, json=grants_data)
    )

    grants_list = service.product_users.list_credit_grants_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
        status="active",
    )
    assert len(grants_list.credit_grants) == 1
    assert grants_list.credit_grants[0].credit_grant_id == "cgrt_1"
    assert grants_list.credit_grants[0].remaining_amount == "10.000000000000"


@pytest.mark.asyncio
@respx.mock
async def test_async_product_user_credit_summary_and_grants():
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test")

    summary_data = {
        "currency": "USD",
        "available_credits": "30.000000000000",
        "active_grant_count": 1,
        "expiring_soon_amount": "0.000000000000",
        "spent_this_month": "0.000000000000",
        "spent_total": "0.000000000000",
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id/credit-summary").mock(
        return_value=httpx.Response(200, json=summary_data)
    )

    summary = await service.product_users.get_credit_summary_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
    )
    assert summary.available_credits == "30.000000000000"

    grants_data = {
        "credit_grants": [
            {
                "credit_grant_id": "cgrt_2",
                "org_id": "org_123",
                "app_id": "app_123",
                "product_end_user_id": "peu_101",
                "amount": "30.000000000000",
                "remaining_amount": "30.000000000000",
                "currency": "USD",
                "status": "active",
            }
        ]
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(200, json=grants_data)
    )

    grants = await service.product_users.list_credit_grants_by_external_id(
        app_id="app_123",
        external_user_id="ext_101",
    )
    assert len(grants.credit_grants) == 1
    assert grants.credit_grants[0].credit_grant_id == "cgrt_2"


@respx.mock
def test_product_user_full_payload_with_allowance_and_getters():
    from decimal import Decimal
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    full_payload = {
        "product_end_user_id": "peu_full_1",
        "org_id": "org_abc",
        "app_id": "app_xyz",
        "external_user_id": "ext_full_1",
        "display_name": "Full User",
        "email_hash": "hash_xyz",
        "status": "active",
        "metadata": {"tier": "pro"},
        "allowance_starts_at": "2026-10-02T02:07:26.535Z",
        "last_app_connection_id": "conn_999",
        "usage": {
            "this_period": {
                "sell_cost": "1.250000000000",
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
                "request_count": 10,
            },
            "period_start": "2026-10-01T00:00:00.000Z",
            "period_end": "2026-10-31T23:59:59.000Z",
            "total": {
                "sell_cost": "3.500000000000",
                "input_tokens": 3000,
                "output_tokens": 1500,
                "total_tokens": 4500,
                "request_count": 25,
            },
        },
        "cap": {
            "source": "product_end_user",
            "cap_rule_id": "rule_cap_1",
            "amount": "20.000000000000",
            "currency": "USD",
            "period": "daily",
            "spent_this_period": "5.000000000000",
            "period_start": "2026-10-02T00:00:00.000Z",
            "period_end": "2026-10-02T23:59:59.000Z",
            "reset_at": "2026-10-03T00:00:00.000Z",
            "status": "active",
            "updated_at": "2026-10-02T02:07:26.535Z",
        },
        "direct_cap": {
            "source": "product_end_user",
            "cap_rule_id": "rule_direct_1",
            "amount": "999.000000000000",
            "currency": "USD",
            "period": "monthly",
            "spent_this_period": "888.000000000000",
            "status": "disabled",
        },
        "credits": {
            "currency": "USD",
            "available_credits": "10.000000000000",
            "active_grant_count": 2,
            "expiring_soon_amount": "0.000000000000",
            "spent_this_month": "2.000000000000",
            "spent_total": "5.000000000000",
            "last_grant_at": "2026-10-01T12:00:00.000Z",
            "last_used_at": "2026-10-02T01:00:00.000Z",
        },
        "allowance": {
            "app_connection_id": "conn_999",
            "cap_source": "org",
            "cap_rule_id": "rule_cap_1",
            "credit_mode": "disabled",
            "overrun_policy": "limit_output",
            "currency": "USD",
            "period": "daily",
            "period_start": "2026-10-02T00:00:00.000Z",
            "period_end": "2026-10-02T23:59:59.000Z",
            "cap_amount": "20.000000000000",
            "spent_this_period": "5.000000000000",
            "remaining_base_allowance": "15.000000000000",
            "available_credits": "10.000000000000",
            "available_allowance": "25.000000000000",
        },
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=full_payload)
    )

    user = service.product_users.get_by_external_id(
        app_id="app_xyz",
        external_user_id="ext_full_1",
    )

    # Core and metadata
    assert user.product_end_user_id == "peu_full_1"
    assert user.allowance_starts_at == "2026-10-02T02:07:26.535Z"
    assert user.last_app_connection_id == "conn_999"

    # Allowance sub-object
    assert user.allowance is not None
    assert user.allowance.available_allowance == "25.000000000000"
    assert user.allowance.cap_amount == "20.000000000000"
    assert user.allowance.spent_this_period == "5.000000000000"

    # Cap sub-object
    assert user.cap is not None
    assert user.cap.amount == "20.000000000000"
    assert user.cap.source == "product_end_user"

    # Direct cap sub-object deserialization
    assert user.direct_cap is not None
    assert user.direct_cap.amount == "999.000000000000"
    assert user.direct_cap.spent_this_period == "888.000000000000"
    assert user.direct_cap.status == "disabled"

    # Usage sub-object
    assert user.usage is not None
    assert user.usage.this_period.sell_cost == "1.250000000000"
    assert user.usage.this_period.total_tokens == 1500
    assert user.usage.total.sell_cost == "3.500000000000"

    # Getters
    assert user.get_available_allowance() == "25.000000000000"
    assert user.total_available_allowance == "25.000000000000"
    assert user.get_total_available_to_spend() == "25.000000000000"
    assert user.total_available_to_spend == "25.000000000000"
    assert user.get_available_credits() == "10.000000000000"
    assert user.get_total_credits() == "10.000000000000"
    assert user.total_credits == "10.000000000000"
    # Ignores direct_cap: returns 20, not 999
    assert user.get_total_allowance() == "20.000000000000"
    # Ignores direct_cap: returns 5, not 888
    assert user.get_cap_spent() == "5.000000000000"
    assert user.cap_spent == "5.000000000000"
    assert user.get_remaining_base_allowance() == "15.000000000000"
    assert user.has_available_allowance() is True
    assert user.get_usage_cost("this_period") == "1.250000000000"
    assert user.get_usage_cost("total") == "3.500000000000"

    # Decimal getters
    assert user.get_available_allowance_decimal() == Decimal("25.000000000000")
    assert user.get_total_available_to_spend_decimal() == Decimal("25.000000000000")
    assert user.get_total_credits_decimal() == Decimal("10.000000000000")
    assert user.get_cap_spent_decimal() == Decimal("5.000000000000")


@respx.mock
def test_product_user_fallback_when_allowance_absent():
    from decimal import Decimal
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    payload_no_allowance = {
        "product_end_user_id": "peu_fallback",
        "app_id": "app_xyz",
        "external_user_id": "ext_fb",
        "credits": {
            "available_credits": "7.500000000000",
        },
        "cap": {
            "amount": "10.000000000000",
            "spent_this_period": "3.000000000000",
        },
    }

    respx.get("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=payload_no_allowance)
    )

    user = service.product_users.get_by_external_id(
        app_id="app_xyz",
        external_user_id="ext_fb",
    )

    assert user.allowance is None
    assert user.get_available_allowance() == "7.500000000000"
    assert user.get_total_available_to_spend() == "7.500000000000"
    assert user.total_available_to_spend == "7.500000000000"
    assert user.get_available_credits() == "7.500000000000"
    assert user.get_total_allowance() == "10.000000000000"
    assert user.get_cap_spent() == "3.000000000000"
    assert user.get_remaining_base_allowance() is None
    assert user.has_available_allowance() is True


def test_product_user_empty_financials():
    from zorveus.types import ProductUserResponse

    user = ProductUserResponse(
        app_id="app_1",
        external_user_id="ext_1",
    )

    assert user.get_available_allowance() == "0.000000000000"
    assert user.get_total_available_to_spend() == "0.000000000000"
    assert user.total_available_to_spend == "0.000000000000"
    assert user.get_available_credits() == "0.000000000000"
    assert user.get_total_allowance() is None
    assert user.get_cap_spent() == "0.000000000000"
    assert user.get_remaining_base_allowance() is None
    assert user.has_available_allowance() is False
    assert user.get_usage_cost("this_period") == "0.000000000000"


def test_product_user_direct_cap_ignored_in_calculations():
    from zorveus.types import ProductUserResponse, ProductUserCapResponse

    user = ProductUserResponse(
        app_id="app_1",
        external_user_id="ext_1",
        direct_cap=ProductUserCapResponse(
            amount="50.000000000000",
            spent_this_period="12.000000000000",
        ),
    )

    # When cap and allowance are not configured, direct_cap must be ignored
    assert user.get_total_allowance() is None
    assert user.get_cap_spent() == "0.000000000000"


def test_product_user_decimal_validation():
    from zorveus import InvalidDecimalError
    from zorveus.types import ProductUserAllowanceResponse, ProductUserCapResponse

    with pytest.raises(InvalidDecimalError):
        ProductUserAllowanceResponse(available_allowance="invalid_number")

    with pytest.raises(InvalidDecimalError):
        ProductUserCapResponse(amount="not_a_valid_decimal")


def test_product_user_usage_mutual_fallback():
    from zorveus.types import ProductUserResponse

    # Test payload with this_month only
    user_legacy = ProductUserResponse.model_validate({
        "app_id": "app_1",
        "external_user_id": "ext_1",
        "usage": {
            "this_month": {
                "sell_cost": "0.500000000000",
            },
        },
    })
    assert user_legacy.usage.this_period is not None
    assert user_legacy.usage.this_period.sell_cost == "0.500000000000"
    assert user_legacy.get_usage_cost("this_period") == "0.500000000000"
    assert user_legacy.get_usage_cost("this_month") == "0.500000000000"

    # Test payload with this_period only
    user_new = ProductUserResponse.model_validate({
        "app_id": "app_1",
        "external_user_id": "ext_1",
        "usage": {
            "this_period": {
                "sell_cost": "0.750000000000",
            },
        },
    })
    assert user_new.usage.this_month is not None
    assert user_new.usage.this_month.sell_cost == "0.750000000000"
    assert user_new.get_usage_cost("this_period") == "0.750000000000"
    assert user_new.get_usage_cost("this_month") == "0.750000000000"


def test_prorated_allowance_uses_effective_cap_and_preserves_adjustment():
    from zorveus.types import ProductUserResponse

    user = ProductUserResponse.model_validate(
        {
            **SAMPLE_USER_PAYLOAD,
            "cap": {"amount": "50.000000000000"},
            "allowance": {
                "cap_amount": "30.000000000000",
                "spent_this_period": "8.000000000000",
                "available_allowance": "22.000000000000",
                "adjustment": {
                    "type": "prorate_increase",
                    "configured_cap_amount": "50.000000000000",
                    "effective_at": "2026-06-16T00:00:00Z",
                },
            },
        },
    )
    assert user.get_total_allowance() == "30.000000000000"
    assert user.get_available_allowance() == "22.000000000000"
    assert user.allowance is not None
    assert user.allowance.adjustment is not None
    assert user.cap is not None
    assert user.allowance.adjustment.configured_cap_amount == user.cap.amount


@pytest.mark.parametrize("anchor", ["omitted", None, "2026-07-17T09:00:00Z"])
@respx.mock
def test_upsert_preserves_or_clears_allowance_anchor(anchor):
    import json

    route = respx.put("https://api.zorveus.com/product-users/by-external-id").respond(
        200, json={"product_user": SAMPLE_USER_PAYLOAD, "created": False}
    )
    service = ZorveusServiceClient(api_key="zrv_svc_test")
    try:
        kwargs = {} if anchor == "omitted" else {"allowance_starts_at": anchor}
        result = service.product_users.create_or_update(app_id="app_123", external_user_id="ext_101", **kwargs)
        payload = json.loads(route.calls.last.request.content)
        assert ("allowance_starts_at" in payload) == (anchor != "omitted")
        if anchor != "omitted":
            assert payload["allowance_starts_at"] == anchor
        assert result.product_user.external_user_id == payload["external_user_id"]
    finally:
        service.close()


@pytest.mark.asyncio
@respx.mock
async def test_async_anchor_update_and_allowance_debt():
    import json

    debt_payload = {
        "outstanding_amount": "1.25",
        "repaid_by_credits_total": "2.00",
        "repaid_by_base_total": "3.00",
        "currency": "USD",
        "oldest_debt_at": None,
    }
    upsert = respx.put("https://api.zorveus.com/product-users/by-external-id").respond(
        200, json={"product_user": SAMPLE_USER_PAYLOAD, "created": False}
    )
    debt_route = respx.get("https://api.zorveus.com/product-users/by-external-id/allowance-debt").respond(
        200, json=debt_payload
    )
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test")
    try:
        await service.product_users.create_or_update(
            app_id="app_123", external_user_id="ext_101", allowance_starts_at=None
        )
        assert json.loads(upsert.calls.last.request.content)["allowance_starts_at"] is None
        debt = await service.product_users.get_allowance_debt_by_external_id(
            app_id="app_123", external_user_id="ext_101"
        )
        assert debt.outstanding_amount == debt_payload["outstanding_amount"]
        assert debt_route.calls.last.request.url.params["external_user_id"] == "ext_101"
    finally:
        await service.close()


@respx.mock
def test_sync_allowance_debt_uses_customer_and_currency():
    debt_payload = {
        "outstanding_amount": "1.25",
        "repaid_by_credits_total": "2.00",
        "repaid_by_base_total": "3.00",
        "currency": "USD",
        "oldest_debt_at": None,
    }
    route = respx.get("https://api.zorveus.com/product-users/by-external-id/allowance-debt").respond(
        200, json=debt_payload
    )
    service = ZorveusServiceClient(api_key="zrv_svc_test")
    try:
        debt = service.product_users.get_allowance_debt_by_external_id(
            app_id="app_123", external_user_id="customer / test", currency="USD"
        )
        assert debt.model_dump() == debt_payload
        assert route.calls.last.request.url.params["external_user_id"] == "customer / test"
        assert route.calls.last.request.url.params["currency"] == debt.currency
    finally:
        service.close()


@respx.mock
def test_service_client_does_not_send_dashboard_credit_revocation():
    from zorveus import ZorveusError

    service = ZorveusServiceClient(api_key="zrv_svc_test")
    with pytest.raises(ZorveusError) as error:
        service.product_users.revoke_credit("user_test", "grant_test")
    assert error.value.code == "zorveus_dashboard_session_required"
    assert len(respx.calls) == 0
    service.close()


@pytest.mark.asyncio
@respx.mock
async def test_async_service_client_does_not_send_dashboard_credit_revocation():
    from zorveus import ZorveusError

    service = AsyncZorveusServiceClient(api_key="zrv_svc_test")
    with pytest.raises(ZorveusError) as error:
        await service.product_users.revoke_credit("user_test", "grant_test")
    assert error.value.code == "zorveus_dashboard_session_required"
    assert len(respx.calls) == 0
    await service.close()


ACTIVITY_PAYLOAD = {'product_end_user_id': 'peu_123', 'items': [{'id': 'ue_123', 'type': 'usage', 'charged_credit_units': None, 'label': 'Agent replied', 'amount': '-4.000000000000', 'currency': 'USD', 'status': 'succeeded', 'created_at': '2026-10-26T12:00:00Z', 'model': 'test-model', 'usage_metadata': {'activity_label': 'Agent replied', 'category': 'support'}, 'base_allowance_charge_amount': '1.000000000000', 'credit_charge_amount': '3.000000000000', 'uncovered_charge_amount': '0.000000000000', 'credit_allocations': [{'credit_grant_id': 'grant_123', 'amount': '3.000000000000', 'currency': 'USD', 'metadata': {'credits_per_usd': '1500'}}]}, {'id': 'entry_123', 'type': 'credit_added', 'label': 'Credit purchase', 'amount': '10.000000000000', 'currency': 'USD', 'status': 'completed', 'created_at': '2026-10-25T12:00:00Z', 'credit_grant_id': 'grant_123', 'metadata': {'credits_per_usd': '1500'}}], 'next_cursor': 'next_page', 'has_more': True, 'limit': 2}


@pytest.mark.parametrize("is_async", [False, True])
@respx.mock
async def test_activity_history_preserves_usage_breakdown_grant_metadata_and_query_filters(is_async):
    route = respx.get("https://api.zorveus.com/product-users/by-external-id/activity").mock(
        return_value=httpx.Response(200, json=ACTIVITY_PAYLOAD)
    )
    params = {
        "app_id": "app_123", "external_user_id": "user_123", "activity_type": "usage",
        "from_date": "2026-10-01T00:00:00Z", "to_date": "2026-11-01T00:00:00Z",
        "currency": "USD", "cursor": "previous_page", "limit": 2,
        "extra_headers": {"X-Request-ID": "history_123"},
    }
    if is_async:
        service = AsyncZorveusServiceClient(api_key="zrv_svc_test")
        result = await service.product_users.list_activity_by_external_id(**params)
        await service.close()
    else:
        service = ZorveusServiceClient(api_key="zrv_svc_test")
        result = service.product_users.list_activity_by_external_id(**params)
        service.close()
    assert result.model_dump() == ACTIVITY_PAYLOAD
    assert dict(route.calls[0].request.url.params) == {
        "app_id": "app_123", "external_user_id": "user_123", "type": "usage",
        "from": "2026-10-01T00:00:00Z", "to": "2026-11-01T00:00:00Z",
        "currency": "USD", "cursor": "previous_page", "limit": "2",
    }
    assert route.calls[0].request.headers["authorization"] == "Bearer zrv_svc_test"
    assert route.calls[0].request.headers["x-request-id"] == "history_123"


@respx.mock
def test_activity_history_defaults_and_unknown_historical_breakdown():
    payload = {
        **ACTIVITY_PAYLOAD,
        "items": [{**ACTIVITY_PAYLOAD["items"][0], "base_allowance_charge_amount": None, "uncovered_charge_amount": None, "usage_metadata": None}],
    }
    route = respx.get("https://api.zorveus.com/product-users/by-external-id/activity").mock(
        return_value=httpx.Response(200, json=payload)
    )
    service = ZorveusServiceClient(api_key="zrv_svc_test")
    result = service.product_users.list_activity_by_external_id(app_id="app_123", external_user_id="user_123")
    service.close()
    assert result.model_dump() == payload
    assert dict(route.calls[0].request.url.params) == {"app_id": "app_123", "external_user_id": "user_123", "limit": "20"}


READ_UPSERT_CASES = [
    ("get_by_external_id", "", SAMPLE_USER_PAYLOAD, "external_user_id", "ext_101"),
    ("get_credit_summary_by_external_id", "/credit-summary", {
        "available_credits": "0.000000000000", "active_grant_count": 0,
    }, "available_credits", "0.000000000000"),
    ("get_allowance_debt_by_external_id", "/allowance-debt", {
        "outstanding_amount": "0.000000000000", "repaid_by_credits_total": "0.000000000000",
        "repaid_by_base_total": "0.000000000000", "currency": "USD",
    }, "outstanding_amount", "0.000000000000"),
    ("list_credit_grants_by_external_id", "/credit-grants", {"credit_grants": []}, "credit_grants", []),
    ("list_activity_by_external_id", "/activity", {
        "product_end_user_id": "peu_123", "items": [], "next_cursor": None, "has_more": False, "limit": 20,
    }, "items", []),
]


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("method, suffix, payload, field, expected", READ_UPSERT_CASES)
@respx.mock
async def test_product_user_reads_require_explicit_upsert_header_and_preserve_authentication(
    is_async, method, suffix, payload, field, expected,
):
    from zorveus.errors import NotFoundError

    route = respx.get("https://api.zorveus.com/product-users/by-external-id" + suffix)
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test") if is_async else ZorveusServiceClient(api_key="zrv_svc_test")
    read = getattr(service.product_users, method)
    try:
        route.respond(404, json={"error": {"code": "zorveus_product_user_not_found", "message": "User not found"}})
        with pytest.raises(NotFoundError):
            if is_async:
                await read(app_id="app_123", external_user_id="ext_101")
            else:
                read(app_id="app_123", external_user_id="ext_101")
        assert "x-zorveus-upsert-product-user" not in route.calls.last.request.headers
        route.respond(200, json=payload)
        params = {
            "app_id": "app_123", "external_user_id": "ext_101",
            "extra_headers": {"X-Zorveus-Upsert-Product-User": "true"},
        }
        result = await read(**params) if is_async else read(**params)
        assert getattr(result, field) == expected
        assert route.calls.last.request.headers["x-zorveus-upsert-product-user"] == "true"
        assert route.calls.last.request.headers["authorization"] == "Bearer zrv_svc_test"
        assert len(route.calls) == 2
    finally:
        if is_async:
            await service.close()
        else:
            service.close()


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("upsert_if_missing", [False, True])
@pytest.mark.parametrize("method, suffix, payload, field, expected", READ_UPSERT_CASES)
@respx.mock
async def test_direct_upsert_option_controls_creation_and_overrides_conflicting_headers(
    is_async, upsert_if_missing, method, suffix, payload, field, expected,
):
    route = respx.get("https://api.zorveus.com/product-users/by-external-id" + suffix).respond(200, json=payload)
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test") if is_async else ZorveusServiceClient(api_key="zrv_svc_test")
    read = getattr(service.product_users, method)
    extra_headers = {
        "x-zorveus-upsert-product-user": "false" if upsert_if_missing else "true",
        "X-Request-ID": "read_123",
    }
    params = {
        "app_id": "app_123", "external_user_id": "ext_101",
        "upsert_if_missing": upsert_if_missing, "extra_headers": extra_headers,
    }
    try:
        result = await read(**params) if is_async else read(**params)
        assert getattr(result, field) == expected
        request = route.calls.last.request
        assert request.headers.get_list("x-zorveus-upsert-product-user") == ["true" if upsert_if_missing else "false"]
        assert request.headers["authorization"] == "Bearer zrv_svc_test"
        assert request.headers["x-request-id"] == "read_123"
        assert "upsert_if_missing" not in request.url.params
        assert request.content == b""
        assert extra_headers == {
            "x-zorveus-upsert-product-user": "false" if upsert_if_missing else "true", "X-Request-ID": "read_123",
        }
    finally:
        if is_async:
            await service.close()
        else:
            service.close()


@pytest.mark.parametrize("is_async", [False, True])
@respx.mock
async def test_direct_upsert_option_rejects_string_booleans_before_sending_requests(is_async):
    route = respx.get("https://api.zorveus.com/product-users/by-external-id").respond(200, json=SAMPLE_USER_PAYLOAD)
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test") if is_async else ZorveusServiceClient(api_key="zrv_svc_test")
    try:
        with pytest.raises(TypeError, match="upsert_if_missing must be a boolean"):
            if is_async:
                await service.product_users.get_by_external_id(app_id="app_123", external_user_id="ext_101", upsert_if_missing="false")
            else:
                service.product_users.get_by_external_id(app_id="app_123", external_user_id="ext_101", upsert_if_missing="false")
        assert not route.called
    finally:
        if is_async:
            await service.close()
        else:
            service.close()


REFERENCED_GRANT = {
    "credit_grant_id": "pucg_retry", "external_reference": "purchase:payment/123?part=1",
    "product_end_user_id": "peu_101", "amount": "5.000000000000",
    "remaining_amount": "3.000000000000", "currency": "USD", "source": "purchase", "status": "active",
}


@pytest.mark.asyncio
@respx.mock
async def test_sync_and_async_grant_references_and_direct_lookup():
    import json

    result = {"product_user": SAMPLE_USER_PAYLOAD, "credit_grant": REFERENCED_GRANT,
              "credit_summary": SAMPLE_USER_PAYLOAD["credits"]}
    create_route = respx.post("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(201, json=result),
    )
    lookup_route = respx.get("https://api.zorveus.com/product-users/by-external-id/credit-grants/by-reference").mock(
        return_value=httpx.Response(200, json=REFERENCED_GRANT),
    )
    sync = ZorveusServiceClient(api_key="zrv_svc_retry")
    async_client = AsyncZorveusServiceClient(api_key="zrv_svc_retry")
    try:
        params = {"app_id": "app_123", "external_user_id": "ext_101",
                  "external_reference": REFERENCED_GRANT["external_reference"]}
        sync_result = sync.product_users.grant_credit_by_external_id(
            **params, amount="5.000000000000", source="purchase",
        )
        async_result = await async_client.product_users.grant_credit_by_external_id(
            **params, amount="5.000000000000", source="purchase",
        )
        sync_lookup = sync.product_users.get_credit_grant_by_external_reference(**params)
        async_lookup = await async_client.product_users.get_credit_grant_by_external_reference(**params)
        assert sync_result.credit_grant.external_reference == params["external_reference"]
        assert async_result.credit_grant.external_reference == params["external_reference"]
        assert sync_lookup == async_lookup == sync_result.credit_grant
        assert [json.loads(call.request.content) for call in create_route.calls] == [
            {**params, "amount": "5.000000000000", "currency": "USD", "source": "purchase"},
            {**params, "amount": "5.000000000000", "currency": "USD", "source": "purchase"},
        ]
        assert [dict(call.request.url.params) for call in lookup_route.calls] == [params, params]
        assert [call.request.headers["authorization"] for call in lookup_route.calls] == [
            "Bearer zrv_svc_retry", "Bearer zrv_svc_retry",
        ]
    finally:
        sync.close()
        await async_client.close()


@pytest.mark.asyncio
@respx.mock
async def test_sync_and_async_grants_preserve_reference_conflicts():
    from zorveus.errors import ConflictError

    route = respx.post("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(409, json={"error": {
            "code": "zorveus_product_user_credit_reference_conflict", "message": "Different grant parameters",
        }}),
    )
    sync = ZorveusServiceClient(api_key="zrv_svc_retry")
    async_client = AsyncZorveusServiceClient(api_key="zrv_svc_retry")
    try:
        params = {"app_id": "app_123", "external_user_id": "ext_101", "amount": "6.000000000000",
                  "external_reference": REFERENCED_GRANT["external_reference"]}
        with pytest.raises(ConflictError) as sync_error:
            sync.product_users.grant_credit_by_external_id(**params)
        with pytest.raises(ConflictError) as async_error:
            await async_client.product_users.grant_credit_by_external_id(**params)
        assert sync_error.value.status_code == async_error.value.status_code == 409
        assert sync_error.value.code == async_error.value.code == "zorveus_product_user_credit_reference_conflict"
        assert route.call_count == 2
    finally:
        sync.close()
        await async_client.close()


@pytest.mark.parametrize("use_async", [False, True])
@respx.mock
async def test_selected_allowance_key_is_sent_in_headers_and_units_keep_precision(use_async):
    exact_units = "1.123456789012345678901234"
    payload = {**SAMPLE_USER_PAYLOAD, "allowance": {"remaining_credit_units": exact_units}}
    route = respx.get("https://api.zorveus.com/product-users/by-external-id").mock(
        return_value=httpx.Response(200, json=payload)
    )
    arguments = {
        "app_id": "app_123", "external_user_id": "ext_101", "inference_key": "zrv_routing_test",
        "key_alias": "pro", "upsert_if_missing": True,
    }
    if use_async:
        client = AsyncZorveusServiceClient(api_key="zrv_svc_test")
        try:
            user = await client.product_users.get_by_external_id(**arguments)
        finally:
            await client.close()
    else:
        client = ZorveusServiceClient(api_key="zrv_svc_test")
        try:
            user = client.product_users.get_by_external_id(**arguments)
        finally:
            client.close()
    request = route.calls[0].request
    assert request.headers["Authorization"] == "Bearer zrv_svc_test"
    assert request.headers["X-Zorveus-Inference-Key"] == "zrv_routing_test"
    assert request.headers["X-Zorveus-Key-Alias"] == "pro"
    assert request.headers["X-Zorveus-Upsert-Product-User"] == "true"
    assert "zrv_routing_test" not in str(request.url)
    assert user.allowance.remaining_credit_units == exact_units


@pytest.mark.parametrize("use_async", [False, True])
@respx.mock
async def test_grant_sends_saved_credit_unit_rate_and_preserves_response_units(use_async):
    import json

    route = respx.post("https://api.zorveus.com/product-users/by-external-id/credit-grants").mock(
        return_value=httpx.Response(201, json={
            "product_user": SAMPLE_USER_PAYLOAD,
            "credit_grant": {"amount": "2", "credit_units_per_usd": "1500", "remaining_credit_units": "3000"},
            "credit_summary": {"available_credits": "2", "remaining_credit_units": "3000"},
        })
    )
    arguments = {"app_id": "app_123", "external_user_id": "ext_101", "amount": "2", "credit_units_per_usd": "1500"}
    if use_async:
        client = AsyncZorveusServiceClient(api_key="zrv_svc_test")
        try:
            receipt = await client.product_users.grant_credit_by_external_id(**arguments)
        finally:
            await client.close()
    else:
        client = ZorveusServiceClient(api_key="zrv_svc_test")
        try:
            receipt = client.product_users.grant_credit_by_external_id(**arguments)
        finally:
            client.close()
    assert json.loads(route.calls[0].request.content)["credit_units_per_usd"] == "1500"
    assert receipt.credit_grant.remaining_credit_units == "3000"
    assert receipt.credit_summary.remaining_credit_units == "3000"
