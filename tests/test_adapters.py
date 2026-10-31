import json

import httpx
import respx
import pytest
from unittest.mock import patch
from zorveus.adapters.langchain import ChatZorveus, HAS_LANGCHAIN
from zorveus.adapters.llamaindex import ZorveusLLM, HAS_LLAMAINDEX


def test_langchain_missing_import():
    with patch("zorveus.adapters.langchain.HAS_LANGCHAIN", False):
        with pytest.raises(ImportError) as exc_info:
            ChatZorveus(api_key="zrv_test")
        assert "pip install zorveus[langchain]" in str(exc_info.value)


def test_llamaindex_missing_import():
    with patch("zorveus.adapters.llamaindex.HAS_LLAMAINDEX", False):
        with pytest.raises(ImportError) as exc_info:
            ZorveusLLM(api_key="zrv_test")
        assert "pip install zorveus[llamaindex]" in str(exc_info.value)


@pytest.mark.parametrize("framework", ["langchain", "llamaindex"])
@pytest.mark.parametrize("has_profile", [False, True])
@respx.mock
def test_framework_adapter_sends_usage_metadata_and_preserves_profile_in_the_http_request(framework, has_profile):
    if framework == "langchain" and not HAS_LANGCHAIN:
        pytest.skip("langchain-openai is not installed")
    if framework == "llamaindex" and not HAS_LLAMAINDEX:
        pytest.skip("llama-index-llms-openai is not installed")
    route = respx.post("https://api.zorveus.com/v1/chat/completions").mock(return_value=httpx.Response(200, json={
        "id": "completion_123", "object": "chat.completion", "created": 0, "model": "gpt-4.1-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Reply"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }))
    usage_metadata = {"activity_id": "reply_123", "details": {"channel": "whatsapp"}}
    params = {
        "api_key": "test_key", "model": "gpt-4.1-mini", "usage_metadata": usage_metadata,
        **({"external_user_id": "user_123", "product_end_user_id": "peu_123", "display_name": "Product User",
            "user_metadata": {"plan": "pro"}} if has_profile else {}),
    }
    if framework == "langchain":
        result = ChatZorveus(**params).invoke("Hello")
        assert result.content == "Reply"
    else:
        result = ZorveusLLM(**params).complete("Hello")
        assert result.text == "Reply"
    assert json.loads(route.calls[0].request.content)["metadata"] == {
        "usage_metadata": usage_metadata,
        **({"external_user_id": "user_123", "product_end_user_id": "peu_123",
            "product_user": {"display_name": "Product User", "metadata": {"plan": "pro"}}} if has_profile else {}),
    }
