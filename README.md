# Zorveus Python SDK

Use Zorveus for inference, customer allowance, and OAuth connections. The SDK supports Python 3.9+, synchronous clients, and asynchronous clients

```bash
pip install zorveus
```

## Make an attributed inference request

Create an app and inference key in the [dashboard](https://app.zorveus.com). Fund the organization's wallet or configure BYOK, then set `ZORVEUS_INFERENCE_KEY` and an available `ZORVEUS_MODEL_ID` on your server

```python
import os
from zorveus import Zorveus

client = Zorveus()
try:
    response = client.chat.completions.create(
        model=os.environ["ZORVEUS_MODEL_ID"],
        messages=[{"role": "user", "content": "Hello"}],
        usage_metadata={"activity_id": "reply_123", "activity_label": "Agent replied"},
        extra_headers={"X-Zorveus-External-User-ID": authenticated_user_id},
    )
    print(response.choices[0].message.content)
finally:
    client.close()
```

Get `authenticated_user_id` from your server's authenticated session. Choose the model with `client.models.list()`. Attach identity to each request so a shared client can safely serve multiple customers. `AsyncZorveus` provides the same methods with `await`, including `await client.close()`

Request activity uses `usage_metadata`; profile metadata remains separate. Read [attach business context to usage](DOCUMENTATION.md#attach-business-context-to-usage) for body and header options, adapters, and validation rules

## Call a service action

Create an organization service key with `product_users:read` or `product_users:write` and set `ZORVEUS_SERVICE_KEY`. Service keys stay on your server and cannot make inference requests

```python
import os
from zorveus import ZorveusServiceClient

service = ZorveusServiceClient()
try:
    result = service.product_users.create_or_update(
        app_id=os.environ["ZORVEUS_APP_ID"],
        external_user_id=authenticated_user_id,
        display_name="Example user",
    )
    print(result.created, result.product_user.external_user_id)

    profile = service.product_users.get_by_external_id(
        app_id=os.environ["ZORVEUS_APP_ID"],
        external_user_id=authenticated_user_id,
    )
    print(profile.get_total_available_to_spend())
finally:
    service.close()
```

The upsert returns an envelope with `product_user`; the read returns the profile directly. Read the [service action guide](DOCUMENTATION.md) for anchors, credits, allowance debt, routing, and OAuth revocation

For async request handlers, use `AsyncZorveusServiceClient` and await its methods. Reuse clients through your application's lifecycle instead of creating them for every request

## Recover a credit grant

Supply `external_reference` when calling `service.product_users.grant_credit_by_external_id`. After a timeout, repeat the same grant parameters and reference, or retrieve it with `get_credit_grant_by_external_reference(app_id=..., external_user_id=..., external_reference=...)`. See the [grant and recovery examples](DOCUMENTATION.md#grant-credits-after-a-verified-business-event)

## Use the OpenAI adapter

```bash
pip install 'zorveus[openai]'
```

```python
import os
from zorveus.openai import ZorveusOpenAI

client = ZorveusOpenAI(api_key=os.environ["ZORVEUS_INFERENCE_KEY"])
try:
    response = client.responses.create(
        model=os.environ["ZORVEUS_MODEL_ID"],
        input="Hello",
        external_user_id=authenticated_user_id,
    )
    print(response.output_text)
finally:
    client.close()
```

The OpenAI adapter supports the official client's resources. The native `Zorveus` client provides chat completions, embeddings, model discovery, and inference-key usage. Optional framework integrations are available through `zorveus[langchain]` and `zorveus[llamaindex]`

Follow [Integrate your product](https://docs.zorveus.com/getting-started/integrate-your-product) for Business setup or [OAuth](https://docs.zorveus.com/oauth/overview) when users fund inference through their own Zorveus account

## Develop locally

```bash
pip install -e '.[dev,openai]'
python -m pytest
```

Runnable scripts are in [examples](examples). Keep environment files and generated media local

## License

MIT


## Read allowance before the first AI request

Use the service client and pass the inference key selected by your application's subscription logic. For a routing key, supply its member alias or use its configured default. Your database remains the source of the customer's plan

```typescript
const user = await service.productUsers.getByExternalId({
	appId,
	externalUserId: authenticatedUserId,
	inferenceKey: selectedInferenceOrRoutingKey,
	keyAlias: selectedRoutingAlias,
	upsertIfMissing: true,
});
console.log(user.allowance?.remaining_credit_units);
```

```python
user = service.product_users.get_by_external_id(
	app_id=app_id,
	external_user_id=authenticated_user_id,
	inference_key=selected_inference_or_routing_key,
	key_alias=selected_routing_alias,
	upsert_if_missing=True,
)
print(user.allowance.remaining_credit_units if user.allowance else None)
```

Python supports the same arguments on the asynchronous service client. Omit the alias for a direct inference key. Both SDKs send the selection in headers, keeping the service key in `Authorization`

```http
GET /product-users/by-external-id?app_id=app_example&external_user_id=shop_123
Authorization: Bearer <organization-service-key>
X-Zorveus-Inference-Key: <inference-or-routing-key>
X-Zorveus-Key-Alias: pro
X-Zorveus-Upsert-Product-User: true
```

The selected key must be active and belong to the service key's app and organization. An invalid selection returns an error without falling back or creating a user. Read-only product-user permission is sufficient. Keep both credentials on your backend

For a $5 monthly allowance at 1,000 credit units per USD, a first read with no usage or grants returns `allowance.remaining_credit_units: "5000"`. Selecting a new plan key on the next read reflects that policy immediately, using the customer's shared usage and grants. The read does not assign a plan or change the last-used connection

Without the optional key, the profile continues to use its direct cap or last-used connection. A user with no usable cap has null allowance. `credits.remaining_credit_units` counts grants only. The complete base-plus-grants total is in `allowance.remaining_credit_units`


## Credit units and conversion rates

Set your app's `credit_units_per_usd` in app settings. A USD grant can supply its own rate. Omit the override to save the app default on the new grant

```typescript
const receipt = await service.productUsers.grantCreditByExternalId({
	appId,
	externalUserId: authenticatedUserId,
	externalReference: `purchase:${verifiedPayment.id}`,
	amount: "2.000000000000",
	creditUnitsPerUsd: "1500",
	source: "purchase",
});
console.log(receipt.credit_grant.remaining_credit_units);
```

```python
receipt = service.product_users.grant_credit_by_external_id(
	app_id=app_id,
	external_user_id=authenticated_user_id,
	external_reference=f"purchase:{verified_payment.id}",
	amount="2.000000000000",
	credit_units_per_usd="1500",
	source="purchase",
)
print(receipt.credit_grant.remaining_credit_units)
```

The $2 grant above starts with 3,000 credit units. Its saved rate stays fixed when the app default changes. Referenced retries preserve the original rate. Changing an explicitly supplied rate under the same reference returns HTTP 409

Grant creation, lists, reference lookup, and revocation return `credit_units_per_usd` and `remaining_credit_units`. An older grant without a saved rate uses the current app default. If neither rate exists, a positive balance has null credit units. Zero remaining USD returns zero units

`credit_summary.remaining_credit_units` sums all usable grants at their respective rates, independently of the grant list limit. If any positive usable grant has no conversion, the total is null. USD fields such as `remaining_amount` and `available_credits` retain their existing meaning

`allowance.remaining_credit_units` includes the remaining base allowance at the current app rate plus grants permitted by the selected connection. It is the field to display for the customer's total remaining credit units. Credit units and rates are exact decimal strings. Keep their precision when displaying or processing them

Rates must be positive finite decimal values with at most 12 digits before and 12 digits after the decimal point. An explicit grant rate requires USD. Existing grants in other currencies remain supported without conversion


## Credit units charged

Usage items include nullable `charged_credit_units`. Zorveus saves this quantity at settlement from the actual base and grant allocations. For example, $0.01 from base allowance at 1,000 units/USD plus $0.01 from a grant at 1,500 units/USD produces `charged_credit_units: "25"`

The original `amount` remains the signed USD charge. The unit charge is a positive exact decimal string. Changing app defaults does not recalculate old usage. Reservations and releases are not settled charges. Refunds do not reprice the original usage row

Historical usage without a recorded quantity returns null. A charge with a missing conversion or funding that has not been allocated also returns null rather than a partial total. Known zero charges return zero
