import os
from zorveus import Zorveus, ZorveusOAuth
from _env import load_env_file

def main() -> None:
    load_env_file()

    print("==================================================")
    print("Zorveus Interactive OAuth PKCE Demo (RFC 7636)")
    print("==================================================\n")

    client_id = os.environ.get("ZORVEUS_CLIENT_ID", "zrv_client_demo_123")
    client_secret = os.environ.get("ZORVEUS_CLIENT_SECRET") or None
    redirect_uri = os.environ.get("ZORVEUS_REDIRECT_URI", "http://localhost:5173/oauth/callback")
    base_url = os.environ.get("ZORVEUS_BASE_URL", "https://api.zorveus.com")
    gateway_url = os.environ.get("ZORVEUS_GATEWAY_URL", f"{base_url.rstrip('/')}/v1")

    print("1. Generating Cryptographic PKCE Data...")
    pkce = ZorveusOAuth.generate_pkce()
    print(f"- Code Verifier:  {pkce.code_verifier}")
    print(f"- Code Challenge: {pkce.code_challenge}")
    print(f"- CSRF State:      {pkce.state}")

    print("\n2. Generating Authorization URL...")
    auth_url = ZorveusOAuth.get_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=pkce.state,
        code_challenge=pkce.code_challenge,
        base_url=base_url,
        scopes=["inference:write", "models:*"],
    )

    print("\nCopy and paste this URL into your browser to authorize:\n")
    print(f"👉 {auth_url}\n")

    print("Waiting for user authorization...\n")
    try:
        raw_input = input("Paste the full redirect URL (or auth code) from your browser:\n> ")
    except (EOFError, KeyboardInterrupt):
        print("\nDemo cancelled.")
        return

    user_input = raw_input.strip()
    if not user_input:
        print("\nError: No input provided. Demo cancelled.")
        return

    print("\n3. Validating Callback Parameters & CSRF State Token...")
    has_url_query = user_input.startswith("http") or "code=" in user_input
    url_or_query = user_input if has_url_query else f"?code={user_input}&state={pkce.state}"
    expected_state = pkce.state if has_url_query else None

    validation = ZorveusOAuth.validate_callback(url_or_query, expected_state=expected_state)
    if not validation.valid or not validation.code:
        print(f"\nValidation Error ({validation.error}): {validation.error_description or 'Invalid response'}")
        return

    print(f"✓ Authorization Code Extracted: {validation.code}")

    print("\n4. Exchanging Authorization Code for Access Token...")
    try:
        token_res = ZorveusOAuth.exchange_token(
            client_id=client_id,
            code=validation.code,
            code_verifier=pkce.code_verifier,
            redirect_uri=redirect_uri,
            client_secret=client_secret,
            base_url=base_url,
        )

        print("\n==================================================")
        print("OAuth Token Exchange Successful!")
        print(f"- Access Token:      {token_res.access_token}")
        print(f"- App Connection ID: {token_res.app_connection_id}")
        print("==================================================\n")

        print("5. Running Live Inference Test with Issued Access Token...")
        client = Zorveus(
            api_key=token_res.access_token,
            gateway_url=gateway_url,
        )

        completion = client.chat.completions.create(
            model="openai/gpt-4.1-mini",
            messages=[{"role": "user", "content": "Hello from Zorveus OAuth PKCE demo!"}],
        )

        print("\nAI Response:")
        print(completion.choices[0].message.content)

    except Exception as err:
        print("\nToken exchange step reached.")
        print(f"Result: {err}")

if __name__ == "__main__":
    main()
