# Zorveus Python SDK (`zorveus`)

Official Python client library for the Zorveus AI Infrastructure Platform.

See [DOCUMENTATION.md](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/DOCUMENTATION.md) for full codebase reference documentation and API details.

## Installation

Standard installation:
```bash
pip install zorveus
```

With framework adapters:
```bash
# OpenAI SDK integration
pip install zorveus[openai]

# LangChain integration
pip install zorveus[langchain]

# LlamaIndex integration
pip install zorveus[llamaindex]
```

---

## Environment variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `ZORVEUS_INFERENCE_KEY` | Data Plane inference key (`zrv_live_...`) | None |
| `ZORVEUS_GATEWAY_URL` | Data Plane API base URL | `https://api.zorveus.com/v1` |
| `ZORVEUS_SERVICE_KEY` | Control Plane service key (`zrv_svc_...`) | None |
| `ZORVEUS_BASE_URL` | Control Plane API base URL | `https://api.zorveus.com` |

Copy [examples/.env.example](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/.env.example) to `.env` to configure environment variables.

---

## Usage

### 1. Data Plane inference client (`Zorveus` and `AsyncZorveus`)

#### Non-streaming chat completion
```python
from zorveus import Zorveus

client = Zorveus(api_key="zrv_live_123...")

response = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Explain AI gateways in one sentence."}],
    zorveus_metadata={"external_user_id": "usr_sara_101"}
)
print(response.choices[0].message.content)
```

#### SSE streaming completion
```python
from zorveus import Zorveus

client = Zorveus(api_key="zrv_live_123...")

stream = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Count from 1 to 5."}],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)
```

#### Async inference client
```python
import asyncio
from zorveus import AsyncZorveus

async def main():
    client = AsyncZorveus(api_key="zrv_live_123...")
    response = await client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hello world!"}]
    )
    print(response.choices[0].message.content)
    await client.close()

asyncio.run(main())
```

#### Query live spend & allowance
```python
from zorveus import Zorveus

client = Zorveus(api_key="zrv_live_123...")
usage = client.get_usage()

print(f"Spend cap: ${usage.spend_cap}")
print(f"Period spend: ${usage.period_spend}")
print(f"Remaining allowance: ${usage.remaining_allowance}")
```

---

### 2. OpenAI SDK integration (`ZorveusOpenAI`)

If you prefer using official `openai` SDK types, install `zorveus[openai]` and use `ZorveusOpenAI`:

```python
from zorveus.openai import ZorveusOpenAI

client = ZorveusOpenAI(
    api_key="zrv_live_123...",
    external_user_id="cus_12345",
    display_name="Ada Lovelace",
    email="ada@example.com",
    user_metadata={"plan": "pro", "workspace_id": "workspace_789"}
)

response = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hello from OpenAI wrapper!"}]
)

print(response.choices[0].message.content)
```

---

### 3. Control Plane service client (`ZorveusServiceClient`)

#### Provision user profile & grant credits
```python
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient(api_key="zrv_svc_123...")
app_id = "app_startup_123"
external_id = "usr_sara_101"

# 1. Create or update profile
user_res = service.product_users.create_or_update(
    app_id=app_id,
    external_user_id=external_id,
    display_name="Sara Connor",
    email="sara@example.com"
)

# 2. Grant credits with 12-decimal string precision
grant_res = service.product_users.grant_credit_by_external_id(
    app_id=app_id,
    external_user_id=external_id,
    amount="25.000000000000",
    source="promotion",
    reason="Welcome Bonus"
)

print(f"Available balance: ${grant_res.credit_summary.available_credits}")
```

#### Register BYOK provider credentials
```python
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient(api_key="zrv_svc_123...")

credential = service.provider_credentials.create(
    app_id="app_startup_123",
    provider="openai",
    api_key="sk-proj-..."
)
print("Credential registered:", credential.provider_credential.id)
```

---

### 4. OAuth 2.0 PKCE flow (`ZorveusOAuth`)

```python
from zorveus import ZorveusOAuth

# 1. Generate PKCE parameters
pkce = ZorveusOAuth.generate_pkce()

# 2. Build authorization URL
auth_url = ZorveusOAuth.get_authorization_url(
    client_id="zrv_client_123",
    redirect_uri="https://yourapp.com/oauth/callback",
    state=pkce.state,
    code_challenge=pkce.code_challenge
)

# 3. Validate callback URL
validation = ZorveusOAuth.validate_callback(
    "https://yourapp.com/oauth/callback?code=auth_code_123&state=" + pkce.state,
    expected_state=pkce.state
)

# 4. Exchange authorization code for access token
if validation.valid and validation.code:
    token_res = ZorveusOAuth.exchange_token(
        client_id="zrv_client_123",
        code=validation.code,
        code_verifier=pkce.code_verifier,
        redirect_uri="https://yourapp.com/oauth/callback"
    )
    print("Access token:", token_res.access_token)
```

---

## License

MIT
