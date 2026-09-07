import os
import sys
from _env import load_env_file

load_env_file()

try:
    from zorveus.openai import ZorveusOpenAI
except ImportError as err:
    print("To run this demo, install the optional openai dependency:")
    print("  uv add openai")
    print(f"Error details: {err}")
    sys.exit(1)

api_key = os.getenv("ZORVEUS_INFERENCE_KEY")
gateway_url = os.getenv("ZORVEUS_GATEWAY_URL", "http://localhost:4000/v1")
model = os.getenv("ZORVEUS_MODEL", "gemini/gemini-2.5-flash-lite")

if not api_key:
    print("Error: ZORVEUS_INFERENCE_KEY environment variable is required.")
    sys.exit(1)

# ZorveusOpenAI drops in as a standard OpenAI client with Zorveus attribution metadata injected
client = ZorveusOpenAI(
    api_key=api_key,
    base_url=gateway_url,
    product_end_user_id="peu_demo_end_user_101",
    external_user_id="demo_end_user_101",
    zorveus_metadata={"tier": "pro_tier"},
)


def run_non_streaming() -> None:
    print(f"=== 1. ZorveusOpenAI Non-Streaming Completion ({model}) ===")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Explain what an OpenAI adapter does in one sentence."},
            ],
            user="demo_end_user_101",
        )
        content = response.choices[0].message.content
        print(f"Content: {content}\n")
    except Exception as err:
        print(f"Call returned: {err}\n")


def run_streaming() -> None:
    print(f"=== 2. ZorveusOpenAI Streaming Completion ({model}) ===")
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Count from 1 to 3 with commas."},
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
        print(f"Call returned: {err}\n")


def main() -> None:
    run_non_streaming()
    run_streaming()


if __name__ == "__main__":
    main()
