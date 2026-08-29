# Zorveus Python SDK (`zorveus`) codebase documentation

Comprehensive reference documentation for the `zorveus` Python SDK, covering installation, environment setup, architecture, Data Plane inference clients, OpenAI SDK integration, Control Plane administration, OAuth 2.0 PKCE utilities, error handling, and Pydantic v2 schemas.

---

## 1. Overview and platform architecture

The `zorveus` SDK provides Python 3.9+ developers with typed, synchronous, and asynchronous interfaces for the Zorveus AI Infrastructure Platform.

```text
+-------------------------------------------------------------------------------+
|                             Zorveus Platform API                              |
+---------------------------------------+---------------------------------------+
                                        |
     +----------------------------------+----------------------------------+
     |                                                                     |
     v                                                                     v
+---------------------------------------+ +---------------------------------------+
|        AI Gateway (Data Plane)        | |     Control Plane (Management API)    |
|   https://api.zorveus.com/v1          | |     https://api.zorveus.com         |
|   (Inference Key / User OAuth Token)  | |     (Organization Service Key)      |
+---------------------------------------+ +---------------------------------------+
| • POST /v1/chat/completions           | | • PUT  /product-users/by-external-id |
| • GET  /v1/models                     | | • GET  /product-users/by-external-id |
| • GET  /v1/inference-keys/usage       | | • POST /product-users/.../grants    |
|                                       | | • POST /provider-credentials        |
|                                       | | • POST /oauth/token                 |
+---------------------------------------+ +---------------------------------------+
```

---

## 2. Installation and environment variables

### 2.1 Installation

Standard installation:
```bash
pip install zorveus
```

With official OpenAI SDK adapter extra:
```bash
pip install zorveus[openai]
```

Development dependencies:
```bash
pip install zorveus[dev]
```

### 2.2 Environment variables

| Variable | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `ZORVEUS_INFERENCE_KEY` | `str` | Inference API Key (`zrv_live_...`) for Data Plane | `None` |
| `ZORVEUS_GATEWAY_URL` | `str` | Data Plane gateway endpoint URL | `https://api.zorveus.com/v1` |
| `ZORVEUS_SERVICE_KEY` | `str` | Organization Service Key (`zrv_svc_...`) for Control Plane | `None` |
| `ZORVEUS_BASE_URL` | `str` | Control Plane platform endpoint URL | `https://api.zorveus.com` |
| `ZORVEUS_CLIENT_ID` | `str` | OAuth 2.0 application client ID | `None` |
| `ZORVEUS_CLIENT_SECRET` | `str` | OAuth 2.0 application client secret | `None` |
| `ZORVEUS_REDIRECT_URI` | `str` | OAuth 2.0 redirect URL | `None` |

Environment template file: [examples/.env.example](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/.env.example)

---

## 3. Data Plane inference client (`Zorveus` and `AsyncZorveus`)

Module: `zorveus._client`

### 3.1 Synchronous client (`Zorveus`)

#### Constructor
```python
Zorveus(
    api_key: Optional[str] = None,
    *,
    gateway_url: Optional[str] = None,
    timeout: float = 60.0
)
```
If `api_key` is omitted, reads `ZORVEUS_INFERENCE_KEY` from `os.environ`.
If `gateway_url` is omitted, reads `ZORVEUS_GATEWAY_URL` or defaults to `https://api.zorveus.com/v1`.

#### Chat completions (`client.chat.completions.create`)
```python
client.chat.completions.create(
    *,
    model: str,
    messages: List[Union[ChatMessage, Dict[str, Any]]],
    stream: bool = False,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    zorveus_metadata: Optional[Dict[str, Any]] = None,
    **extra_kwargs: Any
) -> Union[ChatCompletionResponse, Iterator[ChatCompletionChunk]]
```
- When `stream=False` (default): Returns `ChatCompletionResponse`.
- When `stream=True`: Returns `Iterator[ChatCompletionChunk]` parsing Server-Sent Events (SSE).

Example:
```python
from zorveus import Zorveus

client = Zorveus(api_key="zrv_live_123...")

# Non-streaming
resp = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Explain quantum computing."}],
    zorveus_metadata={"external_user_id": "usr_101"}
)
print(resp.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Count from 1 to 5."}],
    stream=True
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

#### Model discovery (`client.models`)
- `client.models.list() -> ModelListResponse`: Returns list of available models.
- `client.models.get(model_id: str) -> ModelObject`: Retrieves metadata for a single model.

#### Live spend queries (`client.get_usage()`)
```python
usage = client.get_usage()
# UsageResponse fields:
# - key_id: Optional[str]
# - spend_cap: Optional[str]
# - period_spend: Optional[str]
# - remaining_allowance: Optional[str]
# - currency: str ("USD")
```

---

### 3.2 Asynchronous client (`AsyncZorveus`)

Equivalent asynchronous interface powered by `httpx.AsyncClient`.

```python
import asyncio
from zorveus import AsyncZorveus

async def main():
    client = AsyncZorveus(api_key="zrv_live_123...")

    resp = await client.chat.completions.create(
        model="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "Hello async!"}]
    )
    print(resp.choices[0].message.content)

    usage = await client.get_usage()
    print("Spend cap:", usage.spend_cap)

    await client.close()

asyncio.run(main())
```

---

## 4. OpenAI SDK integration (`ZorveusOpenAI` and `AsyncZorveusOpenAI`)

Module: `zorveus.openai`

`ZorveusOpenAI` and `AsyncZorveusOpenAI` inherit directly from official `openai.OpenAI` and `openai.AsyncOpenAI` classes. They allow developers using the `openai` package to route requests through Zorveus while returning native OpenAI types.

### Constructor
```python
ZorveusOpenAI(
    api_key: Optional[str] = None,
    *,
    gateway_url: Optional[str] = None,
    external_user_id: Optional[str] = None,
    display_name: Optional[str] = None,
    email: Optional[str] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    default_headers: Optional[Mapping[str, str]] = None,
    **kwargs: Any
)
```

### Supported endpoints
- `client.chat.completions.create(...)`
- `client.responses.create(...)` (OpenAI Responses API `/v1/responses`)

### User metadata payload translation
`ZorveusOpenAI` automatically translates client-level or per-request parameters (`external_user_id`, `display_name`, `email`, `user_metadata`) into the JSON request body `extra_body["metadata"]`:

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
```

Dispatched JSON HTTP request body:
```json
{
  "model": "openai/gpt-4.1-mini",
  "messages": [{"role": "user", "content": "Hello from OpenAI wrapper!"}],
  "metadata": {
    "external_user_id": "cus_12345",
    "product_user": {
      "display_name": "Ada Lovelace",
      "email": "ada@example.com",
      "metadata": {
        "plan": "pro",
        "workspace_id": "workspace_789"
      }
    }
  }
}
```

Per-request override:
```python
response = client.chat.completions.create(
    model="openai/gpt-4.1-mini",
    messages=[{"role": "user", "content": "Hi"}],
    external_user_id="cus_99999",
    display_name="Grace Hopper",
    email="grace@example.com",
    user_metadata={"plan": "enterprise"}
)
```

---

## 5. Control Plane administration client (`ZorveusServiceClient`)

Module: `zorveus._service_client`

Used by backend applications to manage product end-users, issue credit grants, and administer provider credentials via Organization Service Keys (`zrv_svc_...`).

### 5.1 Product users resource (`service.product_users`)

#### Profile upsert (`create_or_update`)
```python
service.product_users.create_or_update(
    *,
    app_id: str,
    external_user_id: str,
    display_name: Optional[str] = None,
    email: Optional[str] = None
) -> ProductUserResponse
```
PUT `/product-users/by-external-id`

#### Profile fetch (`get_by_external_id`)
```python
service.product_users.get_by_external_id(
    *,
    app_id: str,
    external_user_id: str
) -> ProductUserResponse
```
GET `/product-users/by-external-id`

#### Credit grant (`grant_credit_by_external_id`)
```python
service.product_users.grant_credit_by_external_id(
    *,
    app_id: str,
    external_user_id: str,
    amount: str,
    source: Optional[str] = None,
    reason: Optional[str] = None
) -> GrantCreditResponse
```
POST `/product-users/by-external-id/grants`

> [!IMPORTANT]
> The `amount` parameter requires high-precision string validation (up to 12 decimal places, e.g. `"25.000000000000"`). Invalid decimal formats raise `InvalidDecimalError`.

Example:
```python
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient(api_key="zrv_svc_123...")

grant = service.product_users.grant_credit_by_external_id(
    app_id="app_123",
    external_user_id="usr_101",
    amount="25.000000000000",
    source="promotion",
    reason="Welcome Bonus"
)
print("Available balance:", grant.credit_summary.available_credits)
```

---

### 5.2 Provider credentials resource (`service.provider_credentials`)

#### Register credential (`create`)
```python
service.provider_credentials.create(
    *,
    app_id: str,
    provider: str,
    api_key: str
) -> ProviderCredentialResponse
```
POST `/provider-credentials`

#### List credentials (`list`)
```python
service.provider_credentials.list(
    *,
    app_id: str
) -> ProviderCredentialListResponse
```
GET `/provider-credentials`

---

## 6. OAuth 2.0 PKCE helper (`ZorveusOAuth`)

Module: `zorveus._oauth`

Helper class for implementing RFC 7636 OAuth 2.0 Authorization Code Flow with PKCE.

### 6.1 PKCE generation (`generate_pkce`)
```python
ZorveusOAuth.generate_pkce(byte_length: int = 32) -> PKCEData
```
Returns `PKCEData` object containing `code_verifier`, `code_challenge` (S256), and `state`.

### 6.2 Authorization URL construction (`get_authorization_url`)
```python
ZorveusOAuth.get_authorization_url(
    client_id: str,
    redirect_uri: str,
    state: str,
    code_challenge: str,
    *,
    scopes: Optional[List[str]] = None,
    base_url: str = "https://api.zorveus.com"
) -> str
```
Returns OAuth 2.0 authorization URL (`/oauth/authorize`).

### 6.3 Callback validation (`validate_callback`)
```python
ZorveusOAuth.validate_callback(
    url_or_query: str,
    expected_state: Optional[str] = None
) -> ValidationResult
```
Parses redirect URL or query string. Validates CSRF `state` parameter and extracts authorization `code`.

### 6.4 Access token exchange (`exchange_token`)
```python
ZorveusOAuth.exchange_token(
    client_id: str,
    code: str,
    code_verifier: str,
    redirect_uri: str,
    *,
    client_secret: Optional[str] = None,
    base_url: str = "https://api.zorveus.com"
) -> TokenResponse
```
POST `/oauth/token`. Returns `TokenResponse` containing `access_token`, `token_type`, `app_connection_id`, and `funding_org_id`.

Example interactive script: [examples/oauth_pkce_flow.py](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/oauth_pkce_flow.py)

---

## 7. Exception hierarchy

Module: `zorveus.errors`

```text
ZorveusError (base exception)
├── AuthenticationError        (HTTP 401)
├── PermissionDeniedError      (HTTP 403)
├── NotFoundError              (HTTP 404)
├── UnprocessableEntityError  (HTTP 422)
├── RateLimitError             (HTTP 429)
└── InvalidDecimalError        (Credit string decimal validation failure)
```

Attributes on `ZorveusError`:
- `message: str`
- `status_code: Optional[int]`
- `raw_body: Optional[Dict[str, Any]]`

---

## 8. Pydantic v2 models reference

Module: `zorveus.types`

### Chat completion models
- `ChatMessage`: `role`, `content`, `name`, `tool_calls`
- `ChatCompletionUsage`: `prompt_tokens`, `completion_tokens`, `total_tokens`
- `ChatCompletionChoice`: `index`, `message`, `finish_reason`
- `ChatCompletionResponse`: `id`, `object`, `created`, `model`, `choices`, `usage`
- `ChatCompletionChunkDelta`: `role`, `content`
- `ChatCompletionChunkChoice`: `index`, `delta`, `finish_reason`
- `ChatCompletionChunk`: `id`, `object`, `created`, `model`, `choices`

### Model discovery models
- `ModelObject`: `id`, `object`, `created`, `owned_by`
- `ModelListResponse`: `object`, `data: List[ModelObject]`

### Product users & credit models
- `ProductUser`: `id`, `app_id`, `external_user_id`, `display_name`, `email`, `created_at`, `updated_at`
- `CreditSummary`: `available_credits`, `total_granted`, `total_spent`, `currency`
- `CreditGrant`: `id`, `product_user_id`, `amount`, `source`, `reason`, `created_at`
- `ProductUserResponse`: `product_user`, `credit_summary`
- `GrantCreditResponse`: `credit_grant`, `credit_summary`

### Provider credentials models
- `ProviderCredential`: `id`, `app_id`, `provider`, `created_at`, `updated_at`
- `ProviderCredentialResponse`: `provider_credential`
- `ProviderCredentialListResponse`: `data: List[ProviderCredential]`

### Usage tracking model
- `UsageResponse`: `key_id`, `spend_cap`, `period_spend`, `remaining_allowance`, `currency`

---

## 9. Runnable examples

The `examples/` directory contains runnable reference scripts:

- [examples/basic_inference.py](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/basic_inference.py): Synchronous and streaming chat completions.
- [examples/user_management.py](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/user_management.py): User provisioning and 12-decimal credit grants.
- [examples/oauth_pkce_flow.py](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/oauth_pkce_flow.py): Interactive CLI PKCE flow.
- [examples/openai_adapter_demo.py](file:///Users/peterakande/DevProjects/SDKs/zorveus-python/examples/openai_adapter_demo.py): OpenAI adapter integration (`ZorveusOpenAI`).
