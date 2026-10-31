import json
import pytest
import respx
import httpx
from zorveus import Zorveus, AsyncZorveus
from zorveus.errors import AuthenticationError


@respx.mock
def test_sync_chat_completion():
    client = Zorveus(api_key="test_key")

    mock_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858227,
        "model": "openai/gpt-4.1-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello there!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21},
    }

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    resp = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    assert resp.id == "chatcmpl-123"
    assert resp.choices[0].message.content == "Hello there!"


@respx.mock
def test_sync_chat_completion_stream():
    client = Zorveus(api_key="test_key")

    sse_body = (
        'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1677858227,"model":"openai/gpt-4.1-mini","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n\n'
        'data: {"id":"chatcmpl-1","object":"chat.completion.chunk","created":1677858227,"model":"openai/gpt-4.1-mini","choices":[{"index":0,"delta":{"content":" world!"},"finish_reason":"stop"}]}\n\n'
        "data: [DONE]\n\n"
    )

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, text=sse_body, headers={"content-type": "text/event-stream"})
    )

    chunks = list(
        client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )
    )

    assert len(chunks) == 2
    assert chunks[0].choices[0].delta.content == "Hello"
    assert chunks[1].choices[0].delta.content == " world!"


@respx.mock
def test_sync_chat_completion_stream_reads_error_body():
    client = Zorveus(api_key="test_key")
    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"message": "x-api-key header is required"}},
        )
    )

    with pytest.raises(AuthenticationError, match="x-api-key header is required"):
        client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )


@pytest.mark.asyncio
@respx.mock
async def test_async_chat_completion_stream_reads_error_body():
    client = AsyncZorveus(api_key="test_key")
    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            401,
            json={"error": {"message": "x-api-key header is required"}},
        )
    )

    with pytest.raises(AuthenticationError, match="x-api-key header is required"):
        await client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "Hi"}],
            stream=True,
        )
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_async_chat_completion():
    client = AsyncZorveus(api_key="test_key")

    mock_response = {
        "id": "chatcmpl-async-123",
        "object": "chat.completion",
        "created": 1677858227,
        "model": "openai/gpt-4.1-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Async hello!"},
                "finish_reason": "stop",
            }
        ],
    }

    respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    resp = await client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hi"}],
    )

    assert resp.id == "chatcmpl-async-123"
    assert resp.choices[0].message.content == "Async hello!"
    await client.close()


@respx.mock
def test_chat_attribution_and_tracking_headers():
    import json
    client = Zorveus(api_key="test_key")

    mock_response = {
        "id": "chatcmpl-attr-123",
        "object": "chat.completion",
        "created": 1677858227,
        "model": "openai/gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Attribution verified"},
                "finish_reason": "stop",
            }
        ],
    }

    route = respx.post("https://api.zorveus.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json=mock_response,
            headers={
                "x-zorveus-request-id": "zreq_trace_123",
                "x-zorveus-reservation-id": "resv_trace_456",
            },
        )
    )

    resp = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": "Hello"}],
        user="usr_cust_123",
        product_end_user_id="peu_999",
    )

    assert resp.id == "chatcmpl-attr-123"
    assert resp.request_id == "zreq_trace_123"
    assert resp.reservation_id == "resv_trace_456"

    # Verify request payload sent to gateway
    sent_request = route.calls.last.request
    sent_payload = json.loads(sent_request.content)
    assert sent_payload["user"] == "usr_cust_123"
    assert sent_payload["metadata"]["external_user_id"] == "usr_cust_123"
    assert sent_payload["metadata"]["product_end_user_id"] == "peu_999"


@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.asyncio
@respx.mock
async def test_native_client_uses_request_headers_without_cross_user_leakage(is_async):
    import json

    response = {"id": "completion_test", "created": 0, "model": "zorveus/test-model", "choices": []}
    route = respx.post("https://api.zorveus.com/v1/chat/completions").respond(200, json=response)
    cls = AsyncZorveus if is_async else Zorveus
    client = cls(api_key="zrv_route_test", default_headers={"X-Zorveus-Key-Alias": "free"})
    try:
        for user_id in ("customer_1", "customer_2"):
            pending = client.chat.completions.create(
                model=response["model"],
                messages=[{"role": "user", "content": "Hello"}],
                extra_headers={"X-Zorveus-External-User-ID": user_id, "X-Zorveus-Key-Alias": "pro"},
            )
            if is_async:
                await pending
        assert [call.request.headers["X-Zorveus-External-User-ID"] for call in route.calls] == [
            "customer_1",
            "customer_2",
        ]
        assert all(call.request.headers["X-Zorveus-Key-Alias"] == "pro" for call in route.calls)
        assert all("extra_headers" not in json.loads(call.request.content) for call in route.calls)
    finally:
        if is_async:
            await client.close()
        else:
            client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("is_async", [False, True])
@pytest.mark.parametrize("is_stream", [False, True])
@respx.mock
async def test_usage_metadata_and_header_preserve_attribution_for_sync_async_and_streaming(is_async, is_stream):
    completion = {
        "id": "completion_123", "object": "chat.completion", "created": 0, "model": "test-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Reply"}, "finish_reason": "stop"}],
    }
    chunk = {
        "id": "completion_123", "object": "chat.completion.chunk", "created": 0, "model": "test-model",
        "choices": [{"index": 0, "delta": {"content": "Reply"}, "finish_reason": "stop"}],
    }
    response = (
        httpx.Response(200, text="data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n",
                       headers={"content-type": "text/event-stream"})
        if is_stream else httpx.Response(200, json=completion)
    )
    route = respx.post("https://api.zorveus.com/v1/chat/completions").mock(return_value=response)
    client = AsyncZorveus(api_key="test_key") if is_async else Zorveus(api_key="test_key")
    params = {
        "model": "test-model", "messages": [{"role": "user", "content": "Hello"}], "stream": is_stream,
        "user": "user_123", "usage_metadata": {"activity_id": "reply_123"},
        "zorveus_metadata": {"product_user": {"metadata": {"plan": "pro"}}},
        "extra_headers": {"X-Zorveus-Usage-Metadata": json.dumps({"channel": "whatsapp"})},
    }
    try:
        result = await client.chat.completions.create(**params) if is_async else client.chat.completions.create(**params)
        if is_stream:
            chunks = [item async for item in result] if is_async else list(result)
            assert "".join(item.choices[0].delta.content or "" for item in chunks) == "Reply"
        else:
            assert result.choices[0].message.content == "Reply"
    finally:
        if is_async:
            await client.close()
        else:
            client.close()
    request = route.calls[0].request
    assert json.loads(request.content) == {
        "model": "test-model", "messages": [{"role": "user", "content": "Hello"}], "stream": is_stream,
        "user": "user_123", "metadata": {
            "external_user_id": "user_123", "product_user": {"metadata": {"plan": "pro"}},
            "usage_metadata": {"activity_id": "reply_123"},
        },
    }
    assert json.loads(request.headers["X-Zorveus-Usage-Metadata"]) == {"channel": "whatsapp"}
