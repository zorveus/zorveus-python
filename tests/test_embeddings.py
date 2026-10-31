import json

import httpx
import pytest
import respx

from zorveus import AsyncZorveus, Zorveus

EMBEDDING_RESPONSE = {
    "object": "list",
    "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
    "model": "text-embedding-3-small",
    "usage": {"prompt_tokens": 2, "total_tokens": 2},
}


@pytest.mark.parametrize("usage_metadata", [{}, {"activity_id": "embedding_123", "details": {"document_id": "document_123"}}])
@respx.mock
def test_sync_embedding_attribution(usage_metadata):
    route = respx.post("https://api.zorveus.com/v1/embeddings").mock(
        return_value=httpx.Response(200, json=EMBEDDING_RESPONSE)
    )
    client = Zorveus(api_key="test_key")
    try:
        client.embeddings.create(
            model="text-embedding-3-small",
            input="hello",
            user="customer_123",
            product_end_user_id="peu_456",
            zorveus_metadata={"request_tag": "embedding-test", "usage_metadata": {"activity_id": "old"}},
            usage_metadata=usage_metadata,
            extra_headers={"X-Zorveus-Usage-Metadata": json.dumps({"channel": "documents"})},
        )
    finally:
        client.close()

    assert json.loads(route.calls[0].request.headers["X-Zorveus-Usage-Metadata"]) == {"channel": "documents"}
    payload = json.loads(route.calls[0].request.content)
    assert payload == {
        "model": "text-embedding-3-small",
        "input": "hello",
        "user": "customer_123",
        "metadata": {
            "request_tag": "embedding-test",
            "usage_metadata": usage_metadata,
            "external_user_id": "customer_123",
            "product_end_user_id": "peu_456",
        },
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("usage_metadata", [{}, {"activity_id": "embedding_123", "details": {"document_id": "document_123"}}])
@respx.mock
async def test_async_embedding_attribution(usage_metadata):
    route = respx.post("https://api.zorveus.com/v1/embeddings").mock(
        return_value=httpx.Response(200, json=EMBEDDING_RESPONSE)
    )
    client = AsyncZorveus(api_key="test_key")
    try:
        await client.embeddings.create(
            model="text-embedding-3-small",
            input="hello",
            user="customer_123",
            product_end_user_id="peu_456",
            zorveus_metadata={"request_tag": "embedding-test", "usage_metadata": {"activity_id": "old"}},
            usage_metadata=usage_metadata,
            extra_headers={"X-Zorveus-Usage-Metadata": json.dumps({"channel": "documents"})},
        )
    finally:
        await client.close()

    assert json.loads(route.calls[0].request.headers["X-Zorveus-Usage-Metadata"]) == {"channel": "documents"}
    payload = json.loads(route.calls[0].request.content)
    assert payload == {
        "model": "text-embedding-3-small",
        "input": "hello",
        "user": "customer_123",
        "metadata": {
            "request_tag": "embedding-test",
            "usage_metadata": usage_metadata,
            "external_user_id": "customer_123",
            "product_end_user_id": "peu_456",
        },
    }


@pytest.mark.parametrize("metadata", [{}, {"activity_id": "reply_123", "details": {"parts": [1, True, None]}}])
def test_usage_event_retains_business_metadata(metadata):
    from zorveus.types import UsageEvent
    event = UsageEvent.model_validate({"usage_event_id": "usage_123", "usage_metadata": metadata})
    assert event.usage_metadata == metadata
    assert event.model_dump()["usage_metadata"] == metadata
    assert UsageEvent(usage_event_id="older_usage").usage_metadata is None
