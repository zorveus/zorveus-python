"""Interactive runner for the public Zorveus Python SDK features.

Run from the repository root with:

    uv run python examples/runner.py

The runner loads ``.env`` from the repository root or ``examples/.env``. Most
values can also be entered when an action asks for them.
"""

from __future__ import annotations

import asyncio
import base64
import os
import traceback
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import Any, Callable

from _env import load_env_file
from zorveus import (
    AsyncZorveus,
    AsyncZorveusServiceClient,
    Zorveus,
    ZorveusOAuth,
    ZorveusOpenAI,
    ZorveusServiceClient,
    parse_zorveus_gateway_error,
)
from zorveus.adapters.langchain import ChatZorveus
from zorveus.adapters.llamaindex import ZorveusLLM

load_env_file()

BASE_URL = os.getenv("ZORVEUS_BASE_URL", "http://localhost:8000")
GATEWAY_URL = os.getenv("ZORVEUS_GATEWAY_URL", "http://localhost:4000/v1")


def ask(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    answer = input(f"{label}{suffix}: ").strip()
    return answer or default or ""


def required(label: str, env_name: str) -> str:
    value = ask(label, os.getenv(env_name))
    if not value:
        raise ValueError(f"{env_name} is required for this action")
    return value


def dump(value: Any) -> None:
    if hasattr(value, "model_dump"):
        pprint(value.model_dump(mode="json"), sort_dicts=False)
    else:
        pprint(value, sort_dicts=False)


def inference_client() -> Zorveus:
    return Zorveus(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        base_url=BASE_URL,
        gateway_url=GATEWAY_URL,
    )


def service_client() -> ZorveusServiceClient:
    return ZorveusServiceClient(
        service_key=required("Service key", "ZORVEUS_SERVICE_KEY"),
        base_url=BASE_URL,
    )


def app_id() -> str:
    return required("App ID", "ZORVEUS_APP_ID")


def external_user_id() -> str:
    return required("External product user ID", "ZORVEUS_TEST_EXTERNAL_USER_ID")


def model_id(client: Zorveus | None = None) -> str:
    configured = os.getenv("ZORVEUS_MODEL") or os.getenv("ZORVEUS_TEST_MODEL")
    if configured:
        return configured
    if client is None:
        return required("Model", "ZORVEUS_MODEL")
    models = client.models.list().data
    return required("Model", "ZORVEUS_MODEL") if not models else ask("Model", models[0].id)


def get_usage() -> None:
    with_client(inference_client(), lambda client: dump(client.get_usage()))


def list_models() -> None:
    with_client(inference_client(), lambda client: dump(client.models.list()))


def get_model() -> None:
    def run(client: Zorveus) -> None:
        dump(client.models.get(model_id(client)))

    with_client(inference_client(), run)


def chat_completion() -> None:
    def run(client: Zorveus) -> None:
        response = client.chat.completions.create(
            model=model_id(client),
            messages=[{"role": "user", "content": ask("Prompt", "Reply with OK")}],
            user=external_user_id(),
        )
        dump(response)

    with_client(inference_client(), run)


def streaming_chat_completion() -> None:
    def run(client: Zorveus) -> None:
        stream = client.chat.completions.create(
            model=model_id(client),
            messages=[{"role": "user", "content": ask("Prompt", "Count from one to five")}],
            user=external_user_id(),
            stream=True,
        )
        for chunk in stream:
            print(chunk.choices[0].delta.content or "", end="", flush=True)
        print()

    with_client(inference_client(), run)


def embedding() -> None:
    with_client(
        inference_client(),
        lambda client: dump(
            client.embeddings.create(
                model=ask("Embedding model", os.getenv("ZORVEUS_EMBEDDING_MODEL", "text-embedding-3-small")),
                input=ask("Text to embed", "Zorveus SDK test"),
                user=external_user_id(),
            )
        ),
    )


def upsert_product_user() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.product_users.create_or_update(
                app_id=app_id(),
                external_user_id=external_user_id(),
                display_name=ask("Display name", "SDK Test User"),
                email=ask("Email", "sdk-test@example.com"),
            )
        ),
    )


def get_product_user() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.product_users.get_by_external_id(
                app_id=app_id(), external_user_id=external_user_id()
            )
        ),
    )


def get_credit_summary() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.product_users.get_credit_summary_by_external_id(
                app_id=app_id(),
                external_user_id=external_user_id(),
                currency=ask("Currency", "USD"),
            )
        ),
    )


def list_credit_grants() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.product_users.list_credit_grants_by_external_id(
                app_id=app_id(),
                external_user_id=external_user_id(),
                status=ask("Status filter, blank for all") or None,
                source=ask("Source filter, blank for all") or None,
                limit=int(ask("Limit", "20")),
            )
        ),
    )


def grant_credit() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.product_users.grant_credit_by_external_id(
                app_id=app_id(),
                external_user_id=external_user_id(),
                amount=ask("Credit amount as a decimal string", "1.000000000000"),
                source=ask("Source", "service_key"),
                reason=ask("Reason", "SDK runner test grant"),
            )
        ),
    )


def list_provider_credentials() -> None:
    def run(client: ZorveusServiceClient) -> None:
        selected_app_id = ask("App ID filter, blank for all", os.getenv("ZORVEUS_APP_ID"))
        dump(client.provider_credentials.list(app_id=selected_app_id or None))

    with_client(service_client(), run)


def list_providers() -> None:
    with_client(service_client(), lambda client: dump(client.provider_credentials.list_providers()))


def parse_gateway_error() -> None:
    dump(
        parse_zorveus_gateway_error(
            {
                "error": {
                    "provider_specific_fields": {
                        "error": {
                            "code": "zorveus_product_user_allowance_insufficient",
                            "message": "Allowance exhausted",
                            "params": {"shortfall": "1.000000000000"},
                        }
                    }
                }
            },
            status_code=403,
        )
    )


def create_provider_credential() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.provider_credentials.create(
                provider=required("Provider", "ZORVEUS_TEST_PROVIDER"),
                api_key=required("Disposable provider API key", "ZORVEUS_TEST_PROVIDER_API_KEY"),
                credential_name=ask("Credential name", "SDK runner credential"),
                routing_priority=int(ask("Routing priority", "100")),
            )
        ),
    )


def rotate_provider_credential() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.provider_credentials.rotate(
                provider_credential_id=required(
                    "Provider credential ID", "ZORVEUS_TEST_PROVIDER_CREDENTIAL_ID"
                ),
                api_key=required(
                    "New disposable provider API key", "ZORVEUS_TEST_PROVIDER_ROTATED_API_KEY"
                ),
            )
        ),
    )


def update_provider_routing_priority() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.provider_credentials.update_routing_priority(
                provider_credential_id=required(
                    "Provider credential ID", "ZORVEUS_TEST_PROVIDER_CREDENTIAL_ID"
                ),
                routing_priority=int(ask("Routing priority", "100")),
            )
        ),
    )


def grant_provider_to_app_connection() -> None:
    with_client(
        service_client(),
        lambda client: dump(
            client.provider_credentials.grant_to_app_connection(
                provider_credential_id=required(
                    "Provider credential ID", "ZORVEUS_TEST_PROVIDER_CREDENTIAL_ID"
                ),
                app_connection_id=required("App connection ID", "ZORVEUS_TEST_APP_CONNECTION_ID"),
            )
        ),
    )


def delete_provider_credential() -> None:
    credential_id = required("Provider credential ID", "ZORVEUS_TEST_PROVIDER_CREDENTIAL_ID")
    if ask(f"Type {credential_id} to confirm deletion") != credential_id:
        raise RuntimeError("Deletion cancelled")
    with_client(
        service_client(),
        lambda client: dump(
            client.provider_credentials.delete(provider_credential_id=credential_id)
        ),
    )


def oauth_pkce_and_url() -> None:
    pkce = ZorveusOAuth.generate_pkce()
    dump(pkce)
    print(
        ZorveusOAuth.get_authorization_url(
            client_id=required("OAuth client ID", "ZORVEUS_CLIENT_ID"),
            redirect_uri=ask(
                "Redirect URI",
                os.getenv("ZORVEUS_REDIRECT_URI", "http://localhost:5173/oauth/callback"),
            ),
            state=pkce.state,
            code_challenge=pkce.code_challenge,
            base_url=BASE_URL,
            scopes=["inference:write", "models:*"],
        )
    )


def oauth_validate_callback() -> None:
    dump(
        ZorveusOAuth.validate_callback(
            ask("Full callback URL or query string"),
            expected_state=ask("Expected state, blank to skip") or None,
        )
    )


def oauth_exchange_token() -> None:
    dump(
        ZorveusOAuth.exchange_token(
            client_id=required("OAuth client ID", "ZORVEUS_CLIENT_ID"),
            code=required("Authorization code", "ZORVEUS_TEST_AUTHORIZATION_CODE"),
            code_verifier=required("PKCE code verifier", "ZORVEUS_TEST_CODE_VERIFIER"),
            redirect_uri=required("Redirect URI", "ZORVEUS_REDIRECT_URI"),
            client_secret=os.getenv("ZORVEUS_CLIENT_SECRET"),
            base_url=BASE_URL,
        )
    )


def openai_adapter() -> None:
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        response = client.chat.completions.create(
            model=model_id(),
            messages=[{"role": "user", "content": ask("Prompt", "Reply with OK")}],
        )
        dump(response)
    finally:
        client.close()


def openai_responses_adapter() -> None:
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        dump(
            client.responses.create(
                model=model_id(),
                input=ask("Prompt", "Reply with OK"),
            )
        )
    finally:
        client.close()


def openai_text_to_speech() -> None:
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        response = client.audio.speech.create(
            model=ask("Speech model", os.getenv("ZORVEUS_SPEECH_MODEL", "gemini/gemini-2.5-flash-preview-tts")),
            voice=ask("Voice", "achird"),
            input=ask("Text", "Hello from the Zorveus Python SDK."),
            # response_format=ask("Audio format", "mp3"),
            response_format=ask("Audio format", "pcm16"),
        )
        output_path = Path(ask("Output audio path", "examples/output/speech.mp3"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        print(f"Saved speech audio to {output_path}")
    finally:
        client.close()


def openai_transcribe_audio() -> None:
    audio_path = Path(required("Audio file path", "ZORVEUS_TEST_AUDIO_PATH"))
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        with audio_path.open("rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=ask("Transcription model", os.getenv("ZORVEUS_TRANSCRIPTION_MODEL", "whisper-1")),
                file=audio_file,
            )
        dump(response)
    finally:
        client.close()


def openai_translate_audio() -> None:
    audio_path = Path(required("Audio file path", "ZORVEUS_TEST_AUDIO_PATH"))
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        with audio_path.open("rb") as audio_file:
            response = client.audio.translations.create(
                model=ask("Translation model", os.getenv("ZORVEUS_TRANSLATION_MODEL", "whisper-1")),
                file=audio_file,
            )
        dump(response)
    finally:
        client.close()


def openai_generate_image() -> None:
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        response = client.images.generate(
            model=ask("Image model", os.getenv("ZORVEUS_IMAGE_MODEL", "dall-e-3")),
            prompt=ask("Image prompt", "A simple geometric illustration of an AI gateway"),
            n=1,
            size=ask("Image size", "1024x1024"),
            response_format="b64_json",
        )
        image_data = response.data[0]
        output_path = Path(ask("Output image path", "examples/output/generated-image.png"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if image_data.b64_json:
            output_path.write_bytes(base64.b64decode(image_data.b64_json))
            print(f"Saved generated image to {output_path}")
        else:
            print(f"Generated image URL: {image_data.url}")
    finally:
        client.close()


def openai_moderate_content() -> None:
    client = ZorveusOpenAI(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
    )
    try:
        response = client.moderations.create(
            model=ask("Moderation model", os.getenv("ZORVEUS_MODERATION_MODEL", "omni-moderation-latest")),
            input=ask("Content", "Check this text for safety."),
        )
        dump(response)
    finally:
        client.close()


def langchain_adapter() -> None:
    client = ChatZorveus(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
        model=model_id(),
    )
    dump(client.invoke(ask("Prompt", "Reply with OK")))


def llamaindex_adapter() -> None:
    client = ZorveusLLM(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        gateway_url=GATEWAY_URL,
        external_user_id=external_user_id(),
        model=model_id(),
    )
    dump(client.complete(ask("Prompt", "Reply with OK")))


async def async_client_smoke_test() -> None:
    inference = AsyncZorveus(
        api_key=required("Inference key", "ZORVEUS_INFERENCE_KEY"),
        base_url=BASE_URL,
        gateway_url=GATEWAY_URL,
    )
    service = AsyncZorveusServiceClient(
        service_key=required("Service key", "ZORVEUS_SERVICE_KEY"), base_url=BASE_URL
    )
    try:
        usage, models, user = await asyncio.gather(
            inference.get_usage(),
            inference.models.list(),
            service.product_users.get_by_external_id(
                app_id=app_id(), external_user_id=external_user_id()
            ),
        )
        dump({"usage": usage.model_dump(), "models": models.model_dump(), "user": user.model_dump()})
    finally:
        await inference.close()
        await service.close()


def run_async_client_smoke_test() -> None:
    asyncio.run(async_client_smoke_test())


def with_client(client: Any, operation: Callable[[Any], None]) -> None:
    try:
        operation(client)
    finally:
        client.close()


@dataclass(frozen=True)
class Action:
    name: str
    run: Callable[[], None]
    mutates: bool = False


ACTIONS = [
    Action("Get inference-key usage", get_usage),
    Action("List models", list_models),
    Action("Get one model", get_model),
    Action("Create a chat completion", chat_completion),
    Action("Create a streaming chat completion", streaming_chat_completion),
    Action("Create an embedding", embedding),
    Action("Create or update a product user", upsert_product_user, True),
    Action("Get a product user", get_product_user),
    Action("Get a product user's credit summary", get_credit_summary),
    Action("List a product user's credit grants", list_credit_grants),
    Action("Grant credit to a product user", grant_credit, True),
    Action("List provider credentials", list_provider_credentials),
    Action("List supported providers", list_providers),
    Action("Parse a gateway error", parse_gateway_error),
    Action("Create a provider credential", create_provider_credential, True),
    Action("Rotate a provider credential", rotate_provider_credential, True),
    Action("Update provider routing priority", update_provider_routing_priority, True),
    Action("Grant a provider credential to an app connection", grant_provider_to_app_connection, True),
    Action("Delete a provider credential", delete_provider_credential, True),
    Action("Generate OAuth PKCE data and authorization URL", oauth_pkce_and_url),
    Action("Validate an OAuth callback", oauth_validate_callback),
    Action("Exchange an OAuth authorization code", oauth_exchange_token, True),
    Action("Run an OpenAI adapter completion", openai_adapter),
    Action("Run an OpenAI Responses adapter completion", openai_responses_adapter),
    Action("Generate speech audio", openai_text_to_speech),
    Action("Transcribe an audio file", openai_transcribe_audio),
    Action("Translate an audio file", openai_translate_audio),
    Action("Generate an image", openai_generate_image),
    Action("Moderate text or multimodal content", openai_moderate_content),
    Action("Run a LangChain adapter completion", langchain_adapter),
    Action("Run a LlamaIndex adapter completion", llamaindex_adapter),
    Action("Smoke-test the async clients", run_async_client_smoke_test),
]


def print_menu() -> None:
    print("\nZorveus Python SDK runner\n")
    for index, action in enumerate(ACTIONS, 1):
        marker = " [changes data]" if action.mutates else ""
        print(f"{index:2}. {action.name}{marker}")
    print(" s. Run all read-only actions")
    print(" a. Run every action, with confirmation")
    print(" q. Quit")


def run_action(action: Action) -> None:
    print(f"\n--- {action.name} ---")
    try:
        action.run()
    except (EOFError, KeyboardInterrupt):
        print("CANCELLED")
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        print("Traceback:")
        traceback.print_exc()
    else:
        print("PASS")


def main() -> None:
    print(f"Control plane: {BASE_URL}")
    print(f"Gateway: {GATEWAY_URL}")
    while True:
        print_menu()
        selection = input("\nChoose one or more actions: ").strip().lower()
        if selection == "q":
            return
        if selection == "s":
            selected = [action for action in ACTIONS if not action.mutates]
        elif selection == "a":
            if ask("Type RUN ALL to include actions that change or delete data") != "RUN ALL":
                print("Run-all cancelled.")
                continue
            selected = ACTIONS
        else:
            try:
                selected = [ACTIONS[int(value.strip()) - 1] for value in selection.split(",")]
                if not selected or any(int(value.strip()) < 1 for value in selection.split(",")):
                    raise ValueError
            except (ValueError, IndexError):
                print("Choose listed numbers separated by commas, s, a, or q.")
                continue
        for action in selected:
            run_action(action)


if __name__ == "__main__":
    main()
