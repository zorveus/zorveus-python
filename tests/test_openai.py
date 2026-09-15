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


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
def test_zorveus_openai_user_param_and_product_end_user_id():
    client = ZorveusOpenAI(
        api_key="zrv_test_key",
        product_end_user_id="peu_init_999",
    )

    mock_create = MagicMock(return_value={"id": "chatcmpl-mock"})
    with patch.object(client.chat.completions._completions, "create", mock_create):
        client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "hello"}],
            user="usr_std_open_ai",
            extra_body={"metadata": {"product_user": {"display_name": "Test User"}}},
        )

        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["user"] == "usr_std_open_ai"
        assert kwargs["extra_body"]["metadata"]["external_user_id"] == "usr_std_open_ai"
        assert kwargs["extra_body"]["metadata"]["product_end_user_id"] == "peu_init_999"
        assert (
            kwargs["extra_body"]["metadata"]["product_user"]["display_name"]
            == "Test User"
        )


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
@pytest.mark.parametrize(
    ("resource_path", "method_name"),
    [
        (("embeddings",), "create"),
        (("audio", "speech"), "create"),
        (("audio", "transcriptions"), "create"),
        (("audio", "translations"), "create"),
        (("images",), "generate"),
        (("videos",), "create"),
        (("moderations",), "create"),
    ],
)
def test_zorveus_openai_injects_attribution_into_all_inference_resources(
    resource_path, method_name
):
    client = ZorveusOpenAI(
        api_key="zrv_test_key",
        external_user_id="customer_123",
        product_end_user_id="peu_456",
        display_name="Test User",
    )
    resource = client
    for segment in resource_path:
        resource = getattr(resource, segment)

    mock_method = MagicMock(return_value={"id": "mock"})
    with patch.object(resource._resource, method_name, mock_method):
        getattr(resource, method_name)(model="test-model")

    _, kwargs = mock_method.call_args
    assert "user" not in kwargs
    assert kwargs["extra_body"] == {
        "metadata": {
            "external_user_id": "customer_123",
            "product_end_user_id": "peu_456",
            "product_user": {"display_name": "Test User"},
        }
    }


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
def test_zorveus_openai_video_create_and_poll_keeps_attribution():
    client = ZorveusOpenAI(
        api_key="zrv_test_key",
        external_user_id="customer_123",
    )
    if not hasattr(client, "videos"):
        pytest.skip("installed openai package does not support videos")

    created = MagicMock(id="video_123", status="queued")
    completed = MagicMock(id="video_123", status="completed")
    with (
        patch.object(client.videos._resource, "create", return_value=created) as create,
        patch.object(client.videos._resource, "poll", return_value=completed) as poll,
    ):
        result = client.videos.create_and_poll(
            model="sora-2",
            prompt="A paper airplane in flight",
            seconds="4",
            size="1280x720",
            poll_interval_ms=250,
        )

    assert result is completed
    create.assert_called_once_with(
        model="sora-2",
        prompt="A paper airplane in flight",
        seconds="4",
        size="1280x720",
        extra_body={"metadata": {"external_user_id": "customer_123"}},
    )
    poll.assert_called_once_with("video_123", poll_interval_ms=250)


@pytest.mark.skipif(not HAS_OPENAI, reason="openai package not installed")
def test_zorveus_openai_video_create_and_poll_waits_while_processing():
    client = ZorveusOpenAI(api_key="zrv_test_key")
    if not hasattr(client, "videos"):
        pytest.skip("installed openai package does not support videos")

    processing = MagicMock(id="video_123", status="processing")
    completed = MagicMock(id="video_123", status="completed")
    with (
        patch.object(client.videos._resource, "create", return_value=processing),
        patch.object(client.videos._resource, "poll", return_value=completed) as poll,
        patch("zorveus.openai.time.sleep") as sleep,
    ):
        result = client.videos.create_and_poll(
            model="gemini/veo-3.1-lite-generate-preview",
            prompt="A paper airplane in flight",
            poll_interval_ms=250,
        )

    assert result is completed
    sleep.assert_called_once_with(0.25)
    poll.assert_called_once_with("video_123", poll_interval_ms=250)
