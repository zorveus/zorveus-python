import pytest
import respx
import httpx
from zorveus import ZorveusServiceClient

@respx.mock
def test_provider_credentials():
    service = ZorveusServiceClient(api_key="zrv_svc_test")

    create_resp = {
        "provider_credential": {
            "id": "cred_1",
            "app_id": "app_123",
            "provider": "openai",
        }
    }

    respx.post("https://api.zorveus.com/provider-credentials").mock(
        return_value=httpx.Response(200, json=create_resp)
    )

    created = service.provider_credentials.create(
        app_id="app_123",
        provider="openai",
        api_key="sk-openai-key",
    )
    assert created.provider_credential.id == "cred_1"
    assert created.provider_credential.provider == "openai"

    list_resp = {
        "data": [
            {
                "id": "cred_1",
                "app_id": "app_123",
                "provider": "openai",
            }
        ]
    }

    respx.get("https://api.zorveus.com/provider-credentials").mock(
        return_value=httpx.Response(200, json=list_resp)
    )

    items = service.provider_credentials.list(app_id="app_123")
    assert len(items.data) == 1
    assert items.data[0].id == "cred_1"
