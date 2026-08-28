import os
from zorveus import Zorveus
from _env import load_env_file

def main() -> None:
    load_env_file()
    api_key = os.environ.get("ZORVEUS_INFERENCE_KEY", "zrv_live_demo")
    client = Zorveus(api_key=api_key)

    print("--- Non-streaming completion ---")
    response = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Explain AI gateways in one sentence."}],
        zorveus_metadata={"external_user_id": "demo_usr_101"},
    )
    print("Response:", response.choices[0].message.content)

    print("\n--- Streaming completion ---")
    stream = client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Count from 1 to 5."}],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
    print()

if __name__ == "__main__":
    main()
