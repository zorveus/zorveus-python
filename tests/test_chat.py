import pytest
import respx
import httpx
from zorveus import Zorveus, AsyncZorveus

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
