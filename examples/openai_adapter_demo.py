import os
from _env import load_env_file

def main() -> None:
    load_env_file()

    try:
        from zorveus.openai import ZorveusOpenAI
    except ImportError as err:
        print("To run this demo, install the optional openai extra:")
        print("  pip install zorveus[openai]")
        print(f"Error details: {err}")
        return

    api_key = os.environ.get("ZORVEUS_INFERENCE_KEY", "zrv_live_demo")
    client = ZorveusOpenAI(
        api_key=api_key,
        external_user_id="demo_usr_101",
    )

    print("--- Non-streaming completion using ZorveusOpenAI ---")
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "Say hello from OpenAI adapter!"}],
        )
        print("Response:", response.choices[0].message.content)
    except Exception as err:
        print("Network call result:", err)

if __name__ == "__main__":
    main()
