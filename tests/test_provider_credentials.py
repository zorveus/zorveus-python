import pytest
import respx
import httpx
from zorveus import ZorveusServiceClient, AsyncZorveusServiceClient

SAMPLE_CREDENTIAL = {
    "provider_credential_id": "pc_101",
    "org_id": "org_123",
    "provider": "openai",
    "credential_name": "OpenAI Main",
    "status": "active",
    "routing_health": "ready",
    "routing_mode": "auto_resolve",
    "routing_priority": 100,
    "default_model_policy": [],
    "provider_config": None,
    "active_secret_version_id": "pcv_101",
    "secret_fingerprint": "fp_101",
    "last_validated_at": "2026-09-04T12:00:00Z",
    "last_used_at": None,
}

@respx.mock
def test_provider_credentials():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    respx.post("https://api.zorveus.com/provider-credentials/org-programmatic").mock(
        return_value=httpx.Response(201, json=SAMPLE_CREDENTIAL)
    )

    created = service.provider_credentials.create(
        app_id="app_123",
        provider="openai",
        api_key="sk-openai-key",
    )
    assert created.provider_credential_id == "pc_101"
    assert created.id == "pc_101"
    assert created.provider == "openai"
    assert created.provider_credential.id == "pc_101"

    list_resp = {
        "provider_credentials": [SAMPLE_CREDENTIAL]
    }

    respx.get("https://api.zorveus.com/provider-credentials/org-programmatic").mock(
        return_value=httpx.Response(200, json=list_resp)
    )

    items = service.provider_credentials.list(app_id="app_123")
    assert len(items.provider_credentials) == 1
    assert items.provider_credentials[0].provider_credential_id == "pc_101"
    assert len(items.data) == 1
    assert items.data[0].id == "pc_101"

@pytest.mark.asyncio
@respx.mock
async def test_async_provider_credentials():
    service = AsyncZorveusServiceClient(api_key="zrv_svc_test")

    list_resp = {
        "provider_credentials": [SAMPLE_CREDENTIAL]
    }

    respx.get("https://api.zorveus.com/provider-credentials/org-programmatic").mock(
        return_value=httpx.Response(200, json=list_resp)
    )

    items = await service.provider_credentials.list()
    assert len(items.provider_credentials) == 1
    assert items.provider_credentials[0].id == "pc_101"

