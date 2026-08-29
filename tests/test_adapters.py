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


@pytest.mark.skipif(not HAS_LANGCHAIN, reason="langchain-openai not installed")
def test_chat_zorveus_langchain_kwargs():
    llm = ChatZorveus(
        api_key="zrv_test_key",
        external_user_id="cus_12345",
        display_name="Ada Lovelace",
        user_metadata={"plan": "pro"},
    )
    expected_body = {
        "metadata": {
            "external_user_id": "cus_12345",
            "product_user": {
                "display_name": "Ada Lovelace",
                "metadata": {"plan": "pro"},
            },
        }
    }
    assert llm.model_kwargs["extra_body"] == expected_body


@pytest.mark.skipif(not HAS_LLAMAINDEX, reason="llama-index-llms-openai not installed")
def test_zorveus_llm_llamaindex_kwargs():
    llm = ZorveusLLM(
        api_key="zrv_test_key",
        external_user_id="cus_12345",
        display_name="Ada Lovelace",
        user_metadata={"plan": "pro"},
    )
    expected_body = {
        "metadata": {
            "external_user_id": "cus_12345",
            "product_user": {
                "display_name": "Ada Lovelace",
                "metadata": {"plan": "pro"},
            },
        }
    }
    assert llm.additional_kwargs["extra_body"] == expected_body
