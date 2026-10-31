# Python service action guide

Start with the [README](README.md) for installation and inference. All `service` examples below run on your backend using an organization service key

## Create a service client

```python
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient()
```

The client reads `ZORVEUS_SERVICE_KEY`. Pass `api_key=` explicitly when your secret store supplies the value. It uses `https://api.zorveus.com`, without `/v1`; override with `base_url=` for another environment. Call `service.close()` on shutdown. `AsyncZorveusServiceClient` has matching methods and requires `await`, including shutdown

| Scope | Actions |
| --- | --- |
| `product_users:read` | Read profiles, credit summaries, grants, and allowance debt |
| `product_users:write` | Upsert customers and grant credits, including product-user reads |

Register apps, configure caps, manage existing connections, change product-user status, revoke credit grants, and configure webhooks in the dashboard. The legacy `revoke_credit()` SDK method rejects locally with `zorveus_dashboard_session_required`

## Set customer details and the subscription anchor

```python
result = service.product_users.create_or_update(
    app_id="app_123",
    external_user_id="customer_42",
    display_name="Example user",
    metadata={"plan": "pro"},
    allowance_starts_at="2026-10-10T00:00:00Z",
)
print(result.created)
print(result.product_user.external_user_id)
print(result.product_user.allowance_starts_at)
```

Get the user and plan from trusted server state. Omitting `allowance_starts_at` preserves the stored anchor. A timestamp sets it; explicit `None` clears it. For allowance increases between plan keys, read [prorated plan changes](https://docs.zorveus.com/startups/prorated-plan-changes). The upsert policy does not select a new plan key by itself

## Read allowance and debt

```python
profile = service.product_users.get_by_external_id(
    app_id="app_123", external_user_id="customer_42",
)
print(profile.get_total_available_to_spend())
print(profile.get_total_available_to_spend_decimal())

debt = service.product_users.get_allowance_debt_by_external_id(
    app_id="app_123", external_user_id="customer_42", currency="USD",
)
print(debt.outstanding_amount, debt.repaid_by_credits_total, debt.repaid_by_base_total)
```

A missing user returns `404` by default. To create one during a read, pass `upsert_if_missing=True`. The profile's spendable balance includes base allowance and credits. It uses the applicable direct cap or last connection cap. A plan change can select a different connection, so do not use the old allowance to reject a request on the new key

Helpers read `allowance.available_allowance`, fall back to available credits, then zero. Zero is not evidence of exhaustion on an uncapped connection. A positive balance permits an attempt under an enforced cap but does not guarantee that the request will fit. The gateway still checks estimates, active reservations, and funding

Monetary fields remain decimal strings. Use the `*_decimal()` profile helpers or `decimal.Decimal` for arithmetic

## Opt into creating missing users on reads

```python
profile = service.product_users.get_by_external_id(
	app_id="app_123",
	external_user_id=authenticated_user_id,
	upsert_if_missing=True,
)
```

The `upsert_if_missing` argument also works on `get_credit_summary_by_external_id`, `get_allowance_debt_by_external_id`, `list_credit_grants_by_external_id`, and `list_activity_by_external_id`, including asynchronous methods. Pass a boolean. The SDK sends `X-Zorveus-Upsert-Product-User` automatically. With no option or header, reads remain lookup-only. Explicit `False` disables creation and overrides a conflicting raw header. Existing raw-header calls remain supported when this argument is omitted

Creation is scoped to an owned, non-deleted app. Existing profiles and statuses are preserved. The caller still needs the normal product-user read scope. Explicit upsert and credit-grant writes retain their creation behavior

## Grant credits after a verified business event

```python
grant = service.product_users.grant_credit_by_external_id(
    app_id="app_123", external_user_id="customer_42",
    amount="10.00", currency="USD", source="purchase",
    reason="Purchase purchase_123", metadata={"purchase_id": "purchase_123"},
    external_reference="purchase:purchase_123",
)
print(grant.credit_grant.credit_grant_id)
print(grant.product_user.get_total_available_to_spend())

page = service.product_users.list_credit_grants_by_external_id(
    app_id="app_123", external_user_id="customer_42", limit=100,
)
print(page.credit_grants)
```

Omit `source` to use the backend's `service_key` default. Set `external_reference` to a stable purchase or award ID. Repeating that reference and the same grant parameters recovers the existing grant. Changed parameters return `ConflictError` with code `zorveus_product_user_credit_reference_conflict`

```python
grant = service.product_users.get_credit_grant_by_external_reference(
	app_id="app_123", external_user_id="customer_42",
	external_reference="purchase:purchase_123",
)
print(grant.credit_grant_id, grant.remaining_amount, grant.status)
```

Lookup requires `product_users:read` or a scope that includes it. It returns the grant directly with its current balance and status. `AsyncZorveusServiceClient` exposes both methods with `await`. A lookup that returns 404 can race an unfinished creation. Repeat the original POST with the same reference and parameters to recover safely

The reference remains occupied after expiry, exhaustion, or revocation and survives service-key rotation. Calls without a reference still create independent grants. Metadata alone does not deduplicate. The SDK does not automatically replay grant POSTs. Keep purchase verification and durable receipts in the application. Grant listing has a limit and no cursor. See [grant retry rules](https://docs.zorveus.com/platform/idempotency)

Credits extend a configured cap. An uncapped connection has unlimited virtual allowance and does not consume customer credits. Carried debt can be repaid before credits become spendable. Read [billing integration](https://docs.zorveus.com/startups/billing-integration) before implementing purchase fulfillment

Configure app connections, inference keys, and BYOK credentials in the [dashboard](https://app.zorveus.com). Use the inference key with this SDK after setup

## Select a routing key alias per request

```python
from zorveus import Zorveus

client = Zorveus(api_key=os.environ["ZORVEUS_ROUTING_KEY"])
response = client.chat.completions.create(
    model=os.environ["ZORVEUS_MODEL_ID"],
    messages=[{"role": "user", "content": "Hello"}],
    extra_headers={
        "X-Zorveus-External-User-ID": authenticated_user_id,
        "X-Zorveus-Key-Alias": "pro",
        "X-Zorveus-Allowance-Change-Policy": "prorate_increase",
    },
)
usage = client.get_usage(extra_headers={"X-Zorveus-Key-Alias": "pro"})
client.close()
```

Choose the alias from trusted subscription state. Per-request `extra_headers` work for chat, embeddings, model discovery, and usage; `default_headers` on the client is suitable for headers shared by all requests. Do not place customer-specific headers on a client shared across customers

`get_usage()` calls `/inference-keys/usage` outside `/v1`. Detailed finance-event APIs require a dashboard session, so a service key cannot authenticate them

## List customer activity

```python
page = service.product_users.list_activity_by_external_id(
	app_id="app_123",
	external_user_id=authenticated_user_id,
	limit=20,
)
for item in page.items:
	print(item.label, item.amount, item.currency)
	if item.type == "usage":
		print(item.usage_metadata, item.credit_allocations)
```

The async service client uses the same method with `await`. Optional filters are `activity_type`, `from_date`, `to_date`, and `currency`. Pass `cursor=page.next_cursor` only when `page.has_more`, retaining the same app, user, and filters

The response combines AI usage and recorded permanent credit movements. Usage amounts are negative product-user charges after markup. Usage items include `base_allowance_charge_amount`, `credit_charge_amount`, `uncovered_charge_amount`, and per-grant allocations with saved conversion metadata. Older events return `None` for unknown base and uncovered portions. Monetary fields remain decimal strings

This customer-scoped endpoint accepts a service key with `product_users:read`, returns 404 for missing users unless the upsert header is enabled, and does not expose organization wholesale costs. Read [Product-user activity](https://docs.zorveus.com/startups/product-user-activity) for raw HTTP examples, item types, pagination, date boundaries, and UI rules

## Attach business context to usage

Pass `usage_metadata` on native chat and embedding calls. The SDK sends it as `metadata.usage_metadata`, separate from product-user profile metadata

```python
import json
import os
from zorveus import Zorveus

client = Zorveus()
try:
	response = client.embeddings.create(
		model=os.environ["ZORVEUS_EMBEDDING_MODEL_ID"],
		input="Text to embed",
		user=authenticated_user_id,
		usage_metadata={
			"activity_id": "index_123",
			"activity_label": "Indexed document",
			"document_id": "doc_123",
		},
		extra_headers={
			"X-Zorveus-Usage-Metadata": json.dumps({"channel": "documents"}),
		},
	)
finally:
	client.close()
```

Get `authenticated_user_id` from trusted application state. Async clients accept the same arguments with `await`. Streaming chat calls also accept `usage_metadata`. An explicit argument replaces any `usage_metadata` value supplied through raw `metadata` or `zorveus_metadata`, including when the explicit argument is `{}`

### OpenAI and framework adapters

The Zorveus OpenAI adapter accepts `usage_metadata` per request:

```python
from zorveus.openai import ZorveusOpenAI

with ZorveusOpenAI() as client:
	response = client.responses.create(
		model=os.environ["ZORVEUS_MODEL_ID"],
		input="Reply to the customer",
		external_user_id=authenticated_user_id,
		usage_metadata={"activity_id": "reply_123", "activity_label": "Agent replied"},
	)
```

`AsyncZorveusOpenAI` uses the same per-request option. With the official OpenAI Python client, send the object through `extra_body={"metadata": {"usage_metadata": activity}}` or use `extra_headers`. Do not pass `usage_metadata` directly to the official client

```python
from zorveus.adapters.langchain import ChatZorveus
from zorveus.adapters.llamaindex import ZorveusLLM

activity = {"activity_id": "reply_123", "activity_label": "Agent replied"}
chat = ChatZorveus(
	model=os.environ["ZORVEUS_MODEL_ID"],
	external_user_id=authenticated_user_id,
	usage_metadata=activity,
)
llm = ZorveusLLM(
	model=os.environ["ZORVEUS_MODEL_ID"],
	external_user_id=authenticated_user_id,
	usage_metadata=activity,
)
```

Install `zorveus[langchain]` or `zorveus[llamaindex]` for the relevant adapter. These framework options attach metadata to requests from that instance. Use a separate instance when the activity changes

### Merge rules and saved events

The gateway shallow-merges the JSON object in `X-Zorveus-Usage-Metadata` with the body object. Body keys win. Nested objects are replaced rather than recursively merged. Each input and the merged object must fit within 4,096 UTF-8 bytes using compact JSON encoding, and the raw header also has a 4,096-byte limit. Invalid JSON, arrays or scalar values, non-finite numbers, and oversized metadata fail before a billing reservation is created

The backend saves the captured context on usage events and removes it before forwarding the provider request. `UsageEvent.usage_metadata` is a typed JSON object or `None`. Older events have `None`; an empty object remains `{}`. Existing dashboard permissions still apply, and diagnostic views without usage-detail permission redact the field

`activity_id` and `activity_label` are optional application-defined fields. They do not group events, deduplicate calls, or change the amount charged. Use `service.product_users.list_activity_by_external_id()` for customer activity history. Read the [raw HTTP contract](https://docs.zorveus.com/inference/product-user-metadata#attach-business-context-to-usage-events) for equivalent requests

## Connect and disconnect with OAuth

```python
from zorveus import ZorveusOAuth

pkce = ZorveusOAuth.generate_pkce()
authorization_url = ZorveusOAuth.get_authorization_url(
    client_id="YOUR_CLIENT_ID", redirect_uri="https://example.com/callback",
    state=pkce.state, code_challenge=pkce.code_challenge,
    scopes=["inference:write", "models:*"],
)
```

Save `pkce.state` and `pkce.code_verifier` in the initiating session before redirecting. Retrieve those saved values at the callback and validate state before accepting either a code or an OAuth error

```python
validation = ZorveusOAuth.validate_callback(callback_url, expected_state=saved_state)
if not validation.valid or not validation.code:
    raise ValueError(validation.error_description or "OAuth callback failed")

token = ZorveusOAuth.exchange_token(
    client_id="YOUR_CLIENT_ID", code=validation.code,
    code_verifier=saved_verifier, redirect_uri="https://example.com/callback",
)

result = ZorveusOAuth.revoke_token(client_id="YOUR_CLIENT_ID", token=token.access_token)
print(result.revoked)
```

The token exchange and revocation helpers are synchronous. Run them outside an async handler's event loop. Public clients omit `client_secret`; confidential backends include it. Clear the local session after a confirmed revocation response, including `revoked=False`. A network error leaves remote access uncertain. The token response has no refresh-token flow

## Handle API errors

Catch `ZorveusError` or its specific subclasses from `zorveus.errors`. `AuthenticationError`, `PermissionDeniedError`, `NotFoundError`, `UnprocessableEntityError`, and `RateLimitError` expose the HTTP failure category. `InvalidDecimalError` reports malformed monetary arguments before a request

Inspect `status_code` and `raw_body` when troubleshooting. Never log service keys, inference tokens, provider secrets, or unnecessary customer details

## Selected-key allowance reads and credit units

The service client can read a customer's allowance using the direct inference key or routing key selected by your application. Keep both credentials on your backend. The service key authorizes the read, while the inference key selects the policy through a header

```python
user = service.product_users.get_by_external_id(
	app_id=app_id,
	external_user_id=authenticated_user_id,
	inference_key=selected_inference_or_routing_key,
	key_alias=selected_routing_alias,
	upsert_if_missing=True,
)
print(user.allowance.remaining_credit_units if user.allowance else None)

receipt = service.product_users.grant_credit_by_external_id(
	app_id=app_id,
	external_user_id=authenticated_user_id,
	external_reference=f"purchase:{verified_payment.id}",
	amount="2.000000000000",
	credit_units_per_usd="1500",
	source="purchase",
)
```

Omit the alias for a direct key. Routing keys accept a member alias or their configured default. The upsert option enables the first read before any AI request. Changing the selected key reflects a new plan immediately without assigning a subscription inside Zorveus

`allowance.remaining_credit_units` includes base allowance at the current app rate plus applicable grants at their own rates. `credits.remaining_credit_units` and `credit_summary.remaining_credit_units` count grants only. Existing amount getters and USD fields retain their currency meaning

The $2 grant above starts with 3,000 units. Omit its rate to save the app default. A saved grant rate does not change when the app default changes. Older grants without a saved rate use the current app default. Include the same explicit rate when retrying a grant reference

Activity returns `charged_credit_units`, saved from the actual allocations at settlement. Later app-rate changes do not recalculate it. Rates and quantities are decimal strings. Quantities can have more than 12 decimal places, and null means unavailable rather than zero

The asynchronous service client supports the same arguments and response fields with `await`
