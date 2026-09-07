# Zorveus frontend and SDK finance integration guide

This guide defines the API contracts, accounting behavior, error handling, and display rules that frontend dashboards and client SDKs must implement following the Zorveus finance model

---

## 1. Key shifts from the previous model

The finance engine has been updated to provide clean accounting and predictable client behavior. Frontend and SDK developers should note four key changes:

1. **Base cap is consumed before credits**: When an inference cap exists, usage consumes the base allowance first. Product-user credits are reserved and deducted only after the base cap is exhausted
2. **Virtual spend is distinct from wallet charge**: A single inference call produces three separate amounts: virtual spend, wallet charge, and provider cost. Dashboards must not interchange them
3. **HTTP 402 is strictly for wallet funding**: `402 Payment Required` means the payer organization wallet cannot fund a request or platform fee. Cap or credit exhaustion returns `403 Forbidden`
4. **Unified reservation lifecycle**: Both wallet-funded and BYOK requests share the same reservation lifecycle, eliminating phantom in-flight holes and duplicate client flows

---

## 2. The three financial amounts

Every inference request produces three separate financial values:

| Amount | Definition | Applies to wallet mode | Applies to BYOK | Frontend display label |
| --- | --- | --- | --- | --- |
| `virtual_spend` | Reference-priced value of AI usage consumed against caps and credits | Yes | Yes | "Usage value" or "Virtual spend" |
| `sell_cost` | Actual amount deducted from the organization wallet balance | Yes | No ($0.00 provider charge; explicit fee may apply) | "Billed to wallet" |
| `provider_cost` | Raw upstream cost charged by the model provider (OpenAI, Anthropic, etc.) | Yes (cost reporting) | Yes (cost reporting & fee calculation) | "Provider cost" |

### Display rules for frontend dashboards

- Never show `provider_cost` as the user's usage amount unless your pricing snapshot defines sell price equal to provider cost
- For BYOK requests, show `sell_cost` as `$0.00` (or the explicit BYOK fee if one was charged), but always show the full `virtual_spend`
- Virtual spend is calculated with identical reference pricing regardless of whether the call was funded by wallet or BYOK

---

## 3. Allowance formula and consumption order

When an inference key has a configured cap, the available allowance is:

```text
remaining allowance = remaining base allowance + available product-user credits
```

The remaining base allowance is:

```text
remaining base allowance = max(0, cap amount - completed period virtual spend - active reservations)
```

### Consumption order: base cap first

Usage consumes allowance in this order:

1. **Remaining base allowance** on the inference key
2. **Available product-user credits** (oldest expiring grants first)
3. **Uncovered virtual spend** (in non-blocking `track_only` mode or overruns)

### Example

```text
Configured monthly cap:        $10.00
Virtual spend so far:           $8.00
Remaining base allowance:       $2.00
Available user credits:         $5.00

Incoming request estimate:      $3.00
Base allowance reserved:        $2.00
Credits reserved:               $1.00
Remaining credits after call:   $4.00
```

Notice that the first $2.00 is covered by the cap. Only the $1.00 excess touches user credits

### When no cap exists

If an inference key has no cap rule, virtual allowance is unlimited across all credit modes:
- The request is allowed through
- Virtual spend is recorded
- Zero product-user credits are consumed
- User credits remain untouched because credits only extend a configured cap; they do not create a cap where none exists

---

## 4. Credit enforcement modes

Inference keys configure a `credit_mode` on their app connection. Frontends and SDKs must anticipate the following behavior:

| Mode | Request includes product user | Request has no product user | Client impact |
| --- | --- | --- | --- |
| `enforce_if_present` (default) | Enforces base cap plus credits | Bypasses cap checks; records virtual spend | Recommended for mixed keys serving internal and external traffic |
| `enforce` | Enforces base cap plus credits | Enforces key-level cap for requests without a product user | Strict enforcement; rejects if allowance is exhausted |
| `track_only` | Allocates base cap and credits without blocking | Allocates base cap without blocking | Never rejects for allowance; records `uncovered_virtual_spend` |
| `disabled` | Bypasses cap checks; records virtual spend | Bypasses cap checks; records virtual spend | Virtual spend recorded for analytics without quota enforcement |

---

## 5. HTTP error contracts for SDKs and frontend clients

The API returns distinct HTTP status codes and machine-readable error codes. SDKs must branch on status code and `code`, not message strings:

| HTTP status | Error code (`code`) | Meaning | Recommended SDK / frontend action |
| --- | --- | --- | --- |
| `402 Payment Required` | `zorveus_reservation_insufficient_balance` | Organization wallet lacks funds for the estimated wallet charge or BYOK platform fee | Prompt organization admin to top up the wallet |
| `403 Forbidden` | `zorveus_product_user_allowance_insufficient` | The estimated request cost exceeds the product user's remaining base allowance plus promotional credits | Show the shortfall. Let the user reduce the request, increase the cap, or purchase credits |
| `403 Forbidden` | `zorveus_cap_exceeded` | The key or member cap has been reached and no credits are available | Alert team admin that the key quota has been reached |
| `403 Forbidden` | `zorveus_app_connection_not_found` | Supplied inference key or connection is invalid or revoked | Prompt developer to check API key configuration |
| `409 Conflict` | `zorveus_reservation_conflict` | Idempotency key reused with mismatched request parameters | Fix client-side request generation or generate a new key |

### Standard error payload format

```json
{
  "error": {
    "code": "zorveus_product_user_allowance_insufficient",
    "message": "This request is estimated to cost 0.010000000000 USD, but the product user has 0.004720000000 USD of AI allowance remaining.",
    "params": {
      "cap_rule_id": "cap_123",
      "cap_period": "monthly",
      "currency": "USD",
      "cap_amount": "0.010000000000",
      "settled_spend_this_period": "0.005280000000",
      "active_reservations_amount": "0.000000000000",
      "remaining_base_allowance": "0.004720000000",
      "promotional_credit_balance": "0.000000000000",
      "available_allowance": "0.004720000000",
      "estimated_request_cost": "0.010000000000",
      "shortfall": "0.005280000000"
    }
  }
}
```

All money values in `params` are decimal strings with 12 fractional digits. SDKs must parse them with a decimal type instead of binary floating point

The OpenAI-compatible gateway places this object at `error.provider_specific_fields.error`. During rollout, SDKs should also recognize the previous `zorveus_product_user_credits_insufficient` code. New UI copy must use the allowance error because the available amount includes both the base cap and promotional credits

The allowance error parameters have these meanings:

| Parameter | Meaning |
| --- | --- |
| `cap_rule_id` | The applicable cap rule that limited the request |
| `cap_period` | The cap period: `daily`, `monthly`, or `lifetime` |
| `currency` | The currency for every amount in the error |
| `cap_amount` | The configured base allowance for the cap period |
| `settled_spend_this_period` | Completed virtual spend counted in the current cap period |
| `active_reservations_amount` | Estimated virtual spend held by unfinished requests |
| `remaining_base_allowance` | `max(0, cap_amount - settled_spend_this_period - active_reservations_amount)` |
| `promotional_credit_balance` | Promotional credits available when Zorveus evaluated the request |
| `available_allowance` | `remaining_base_allowance + promotional_credit_balance` |
| `estimated_request_cost` | Virtual spend that Zorveus attempted to reserve for the new request |
| `shortfall` | `max(0, estimated_request_cost - available_allowance)` |

SDKs should expose this response as a typed `ProductUserAllowanceInsufficientError`. Do not retry the same request without a policy or request change. A retry can succeed after the application increases the cap, adds promotional credits, reduces the request estimate, or an active reservation is released

---

## 6. SDK request attribution and payload structure

Zorveus runs an OpenAI-compatible gateway. Client SDKs (official OpenAI SDK, Python, Node, curl) do not use custom request headers for user attribution. Attribution is passed directly through the standard OpenAI request body:

### Request payload parameters

| Field in request body | Type | Description |
| --- | --- | --- |
| `user` | String | Standard OpenAI end-user ID from your main product (e.g. `"usr_123"`). Mapped directly to `external_user_id` |
| `metadata.external_user_id` | String | Alternative way to pass your product's end-user ID inside the metadata object |
| `metadata.product_end_user_id` | String | Internal Zorveus product user identifier (`"peu_..."`) if already known |
| `metadata.product_user` | Object | Optional user metadata object: `{"display_name": "Jane Doe", "email": "jane@example.com", "metadata": {...}}` |
| `metadata.product_user_display_name` | String | Optional flat fallback for display name |
| `metadata.product_user_email` | String | Optional flat fallback for email address |

### Example OpenAI SDK call in Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.zorveus.com/v1",
    api_key="zorveus_live_...",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
    user="usr_cust_987",  # Maps directly to external_user_id
    extra_body={
        "metadata": {
            "product_user": {
                "display_name": "Jane Doe",
                "email": "jane@example.com",
            }
        }
    },
)
```

### Key-bound attribution

When an API key is provisioned specifically for one end-user, Zorveus binds `zorveus_product_end_user_id` to that key in the database. Requests using that key automatically inherit the product user without passing any body fields

### Response headers returned by Zorveus

Zorveus returns tracking headers in every inference response:

| Response header | Description |
| --- | --- |
| `x-zorveus-request-id` | Unique request identifier (`zreq_...`) for debugging and audit tracing |
| `x-zorveus-reservation-id` | The reservation identifier (`resv_...`) held for this request |

### Scoping rules

- When a product user is supplied, spend and cap consumption are isolated to that specific product user
- Requests without a product user do not consume a named product user's allowance
- If a supplied product user identifier cannot be resolved, Zorveus returns `403 Forbidden`. It will not treat an invalid user as an unmetered request

---

## 7. Reporting metrics and dashboard cards

When designing billing and usage views, use these exact metrics:

### Product user credit cards

- **Available credits**: Sum of remaining unexpired credit grants owned by the user
- **Credits spent this month** (`credits.spent_this_month`): Amount deducted from credit grants this month. This does not represent total virtual spend
- **Total virtual spend**: Complete reference-priced AI usage across base allowance and credits

### Usage event table fields

In the usage event logs, expose the following columns:

| Field | Type | Description |
| --- | --- | --- |
| `virtual_spend` | Decimal | Total reference-priced allowance used |
| `sell_cost` | Decimal | Amount charged to the wallet ($0 for BYOK unless fee applied) |
| `provider_cost` | Decimal | Upstream model provider cost |
| `uncovered_virtual_spend` | Decimal | Virtual spend exceeding cap and credits in `track_only` mode or overruns |
| `unfunded_wallet_charge` | Decimal | Wallet charge that could not be debited due to wallet exhaustion during overrun |
| `billing_mode` | String | `wallet` or `byok_external` |
| `status` | String | `succeeded`, `partially_settled`, `failed` |

---

## 8. BYOK platform fees and fallback display

### BYOK platform fees

- The platform fee applies only to provider spend exceeding the organization's monthly free threshold (e.g. 5% on spend above $10,000/month)
- The organization wallet pays this fee. Product-user credits never pay it
- If the wallet lacks funds to cover the estimated fee, the request returns `402 Payment Required` before calling the provider

### Wallet fallback indicator

When an organization enables `auto_fallback_to_wallet`:
- If all BYOK keys fail due to upstream rate limits (429), quota exhaustion, or timeouts, Zorveus automatically falls back to Zorveus-managed wallet routes
- The usage log indicates fallback by displaying `billing_mode: "wallet"` and listing the prior failed BYOK attempts in the provider attempt history
- Fallback never occurs on invalid prompts, context length errors, or bad parameters (HTTP 400)
