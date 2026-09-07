import os
import sys
from zorveus import Zorveus
from _env import load_env_file

load_env_file()

api_key = os.getenv("ZORVEUS_INFERENCE_KEY")
gateway_url = os.getenv("ZORVEUS_GATEWAY_URL")
base_url = os.getenv("ZORVEUS_BASE_URL")
model = os.getenv("ZORVEUS_MODEL", "gemini/gemini-2.5-flash-lite")

if not api_key:
    print("Error: ZORVEUS_INFERENCE_KEY environment variable is required.")
    sys.exit(1)

client = Zorveus(
    api_key=api_key,
    gateway_url=gateway_url,
    base_url=base_url,
)


def inspect_usage() -> None:
    print("=== 1. Checking Key Spend Cap and Allowance ===")
    try:
        usage = client.get_usage()
        print(f"App Connection ID:   {usage.app_connection_id}")
        print(f"Currency:            {usage.currency}")
        print(f"Monthly Spend Cap:   {usage.spend_cap}")
        print(f"Spent This Period:   {usage.period_spend}")
        print(f"Remaining Allowance: {usage.remaining_allowance}")
        print(f"Reset Timestamp:     {usage.reset_at}\n")
    except Exception as err:
        print(f"Failed to query usage: {err}\n")


def list_models() -> None:
    print("=== 2. Discovering Catalog Models ===")
    try:
        models_response = client.models.list()
        total_models = len(models_response.data)
        print(f"Total catalog models available: {total_models}")
        sample = [m.id for m in models_response.data[:5]]
        print(f"Sample models: {', '.join(sample)}\n")
    except Exception as err:
        print(f"Failed to list models: {err}\n")


def run_chat_completion() -> None:
    print(f"=== 3. Non-Streaming Chat Completion ({model}) ===")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a concise assistant."},
                {"role": "user", "content": "Explain what an AI gateway is in one sentence."},
            ],
            user="demo_end_user_101",
            product_end_user_id="peu_demo_end_user_101",
            temperature=0.7,
        )

        content = response.choices[0].message.content
        print(f"Content: {content}\n")
        print("Tracking Headers:")
        print(f"  Request ID:     {response.request_id}")
        print(f"  Reservation ID: {response.reservation_id}\n")
    except Exception as err:
        print(f"Chat completion call returned: {err}\n")


def run_streaming_completion() -> None:
    print(f"=== 4. Streaming Chat Completion ({model}) ===")
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Count from 1 to 5 with commas."},
            ],
            user="demo_end_user_101",
            stream=True,
        )

        print("Stream chunks: ", end="", flush=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
        print("\n")
    except Exception as err:
        print(f"Streaming completion call returned: {err}\n")


def main() -> None:
    inspect_usage()
    list_models()
    run_chat_completion()
    run_streaming_completion()


if __name__ == "__main__":
    main()
