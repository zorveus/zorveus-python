import pytest
from unittest.mock import patch, MagicMock
from zorveus.openai import ZorveusOpenAI, AsyncZorveusOpenAI, HAS_OPENAI

def test_openai_missing_import():
    with patch("zorveus.openai.HAS_OPENAI", False):
        with pytest.raises(ImportError) as exc_info:
            ZorveusOpenAI(api_key="zrv_test")
        assert "pip install zorveus[openai]" in str(exc_info.value)

        with pytest.raises(ImportError) as exc_info:
            AsyncZorveusOpenAI(api_key="zrv_test")
        assert "pip install zorveus[openai]" in str(exc_info.value)


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
def test_zorveus_openai_initialization_and_metadata_wrapper():
    client = ZorveusOpenAI(
        api_key="zrv_test_key",
        external_user_id="cus_12345",
        display_name="Ada Lovelace",
        email="ada@example.com",
        user_metadata={"plan": "pro", "workspace_id": "workspace_789"},
    )
    assert client.api_key == "zrv_test_key"
    assert str(client.base_url) == "https://api.zorveus.com/v1/"

    # Mock wrapped completions.create
    mock_create = MagicMock(return_value={"id": "chatcmpl-mock"})
    with patch.object(client.chat.completions._completions, "create", mock_create):
        client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "hello"}],
        )

        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        expected_body = {
            "metadata": {
                "external_user_id": "cus_12345",
                "product_user": {
                    "display_name": "Ada Lovelace",
                    "email": "ada@example.com",
                    "metadata": {"plan": "pro", "workspace_id": "workspace_789"},
                },
            }
        }
        assert kwargs["extra_body"] == expected_body


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
def test_zorveus_openai_responses_wrapper():
    client = ZorveusOpenAI(
        api_key="zrv_test_key",
        external_user_id="cus_12345",
        display_name="Ada Lovelace",
    )

    if hasattr(client, "responses") and client.responses is not None:
        mock_resp_create = MagicMock(return_value={"id": "resp-mock"})
        with patch.object(client.responses._responses, "create", mock_resp_create):
            client.responses.create(
                model="openai/gpt-4.1-mini",
                input="hello",
            )
            mock_resp_create.assert_called_once()
            _, kwargs = mock_resp_create.call_args
            expected_body = {
                "metadata": {
                    "external_user_id": "cus_12345",
                    "product_user": {
                        "display_name": "Ada Lovelace",
                    },
                }
            }
            assert kwargs["extra_body"] == expected_body
