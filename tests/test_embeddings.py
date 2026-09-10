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


@respx.mock
def test_sync_embedding_attribution():
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
        )
    finally:
        client.close()

    payload = json.loads(route.calls[0].request.content)
    assert payload["metadata"]["external_user_id"] == "customer_123"
    assert payload["metadata"]["product_end_user_id"] == "peu_456"
    assert payload["zorveus_metadata"] == payload["metadata"]


@pytest.mark.asyncio
@respx.mock
async def test_async_embedding_attribution():
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
        )
    finally:
        await client.close()

    payload = json.loads(route.calls[0].request.content)
    assert payload["metadata"]["external_user_id"] == "customer_123"
    assert payload["metadata"]["product_end_user_id"] == "peu_456"
    assert payload["zorveus_metadata"] == payload["metadata"]
