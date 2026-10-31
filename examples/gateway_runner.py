"""Run every gateway example with one user and the built-in defaults.

Usage:

    uv run python examples/gateway_runner.py USER_ID

Set ``ZORVEUS_INFERENCE_KEY`` before running. The user ID may instead come
from ``ZORVEUS_GATEWAY_USER`` or ``ZORVEUS_TEST_EXTERNAL_USER_ID``.
"""

from __future__ import annotations

import argparse
import os
import time
from typing import Any

import runner

from _env import load_env_file

load_env_file()

OUTPUT_LIMIT = 5


def list_models() -> None:
    def run(client: Any) -> None:
        response = client.models.list()
        payload = response.model_dump(mode="json")
        total = len(payload["data"])
        payload["data"] = payload["data"][:OUTPUT_LIMIT]
        payload["shown"] = min(OUTPUT_LIMIT, total)
        payload["total"] = total
        runner.dump(payload)

    runner.with_client(runner.inference_client(), run)


def embedding() -> None:
    def run(client: Any) -> None:
        response = client.embeddings.create(
            model=runner.ask(
                "Embedding model",
                os.getenv("ZORVEUS_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
            ),
            input=runner.ask("Text to embed", "Zorveus SDK test"),
            user=runner.external_user_id(),
        )
        payload = response.model_dump(mode="json")
        for item in payload["data"]:
            values = item["embedding"]
            item["embedding"] = values[:OUTPUT_LIMIT]
            item["values_shown"] = min(OUTPUT_LIMIT, len(values))
            item["dimensions"] = len(values)
        runner.dump(payload)

    runner.with_client(runner.inference_client(), run)


GATEWAY_ACTIONS = [
    # runner.Action("Get inference-key usage", runner.get_usage),
    # runner.Action("List models", list_models),
    # runner.Action("Create a chat completion", runner.chat_completion),
    # runner.Action(
    #     "Create a streaming chat completion", runner.streaming_chat_completion
    # ),
    # runner.Action("Create an embedding", embedding),
    # runner.Action("Run an OpenAI adapter completion", runner.openai_adapter),
    # runner.Action(
    #     "Run an OpenAI Responses adapter completion",
    #     runner.openai_responses_adapter,
    # ),
    # runner.Action("Generate speech audio", runner.openai_text_to_speech),
    # runner.Action("Transcribe an audio file", runner.openai_transcribe_audio),
    runner.Action("Translate an audio file", runner.openai_translate_audio),
    runner.Action("Generate an image", runner.openai_generate_image),
    runner.Action("Generate a video", runner.openai_generate_video),
    # runner.Action("Moderate content", runner.openai_moderate_content),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all Zorveus gateway examples with their default inputs."
    )
    parser.add_argument(
        "gateway_user",
        nargs="?",
        default=os.getenv("ZORVEUS_GATEWAY_USER")
        or os.getenv("ZORVEUS_TEST_EXTERNAL_USER_ID"),
        help="External user ID used for gateway attribution",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("ZORVEUS_MODEL")
        or os.getenv("ZORVEUS_TEST_MODEL")
        or "gemini/gemini-2.5-flash-lite",
        help="Model used by chat and Responses calls",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Seconds to wait between actions to reduce rate-limit errors",
    )
    parser.add_argument(
        "--output-limit",
        type=int,
        default=5,
        help="Models and embedding values to print",
    )
    return parser.parse_args()


def use_default(label: str, default: str | None = None) -> str:
    if label == "Output audio path" and default == "examples/output/speech.mp3":
        return "examples/output/speech.pcm"
    return default or ""


def main() -> None:
    global OUTPUT_LIMIT

    args = parse_args()
    gateway_user = args.gateway_user or input("Gateway user: ").strip()
    if not gateway_user:
        raise ValueError("A gateway user is required")
    if not os.getenv("ZORVEUS_INFERENCE_KEY"):
        raise ValueError("ZORVEUS_INFERENCE_KEY is required")
    if args.delay < 0:
        raise ValueError("--delay cannot be negative")
    if args.output_limit < 1:
        raise ValueError("--output-limit must be at least 1")
    OUTPUT_LIMIT = args.output_limit

    runner.ask = use_default
    runner.external_user_id = lambda: gateway_user
    runner.model_id = lambda client=None: args.model

    print(f"Gateway: {runner.GATEWAY_URL}")
    print(f"Gateway user: {gateway_user}")
    print(f"Chat model: {args.model}")
    print("Running all gateway actions with their default values.")
    for index, action in enumerate(GATEWAY_ACTIONS):
        if index:
            time.sleep(args.delay)
        runner.run_action(action)


if __name__ == "__main__":
    main()
