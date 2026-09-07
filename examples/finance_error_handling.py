import os
import sys
from decimal import Decimal
from zorveus import (
    Zorveus,
    ZorveusError,
    ProductUserAllowanceInsufficientError,
    PaymentRequiredError,
    CapExceededError,
    ConflictError,
    RateLimitError,
)
from zorveus.errors import ProductUserAllowanceInsufficientParams
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


def handle_simulated_allowance_error() -> None:
    print("=== 1. Handling Product User Allowance Shortfall (HTTP 403) ===")
    raw_params = {
        "cap_rule_id": "cap_sample_rule_123",
        "cap_period": "monthly",
        "currency": "USD",
        "cap_amount": "10.000000000000",
        "settled_spend_this_period": "9.985000000000",
        "active_reservations_amount": "0.000000000000",
        "remaining_base_allowance": "0.015000000000",
        "promotional_grant_remaining": "0.000000000000",
        "paid_grant_remaining": "0.000000000000",
        "available_allowance": "0.015000000000",
        "estimated_reservation_amount": "0.020000000000",
        "shortfall": "0.005000000000",
    }
    typed_params = ProductUserAllowanceInsufficientParams.from_dict(raw_params)
    simulated_err = ProductUserAllowanceInsufficientError(
        message="This request is estimated to cost 0.02 USD, but the product user has 0.015 USD remaining.",
        status_code=403,
        error_code="zorveus_product_user_allowance_insufficient",
        params=typed_params,
        request_id="req_sample_12345",
        reservation_id="resv_sample_67890",
    )

    try:
        raise simulated_err
    except ProductUserAllowanceInsufficientError as err:
        print("Caught ProductUserAllowanceInsufficientError:")
        print(f"  Message:        {err.message}")
        print(f"  Status Code:    {err.status_code}")
        print(f"  Request ID:     {err.request_id}")
        print(f"  Reservation ID: {err.reservation_id}")

        if err.params:
            print("Typed Finance Shortfall Metrics:")
            print(f"  Available:  {err.params.available_allowance} {err.params.currency}")
            print(f"  Shortfall:  {err.params.shortfall} {err.params.currency}")
            print(f"  Period:     {err.params.cap_period}")

            if err.params.shortfall and err.params.shortfall > Decimal("0"):
                print(f"Action: Prompt end user to purchase at least {err.params.shortfall} {err.params.currency} in credits.\n")


def handle_live_inference_call() -> None:
    print("=== 2. Live Inference Call with Finance Error Handling ===")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Ping"}],
            user="end_user_with_cap",
        )
        print("Call succeeded:")
        print(f"  Response: {response.choices[0].message.content}")
        print(f"  Request ID: {response.request_id}")
    except ProductUserAllowanceInsufficientError as err:
        print(f"Blocked by Product User Allowance: {err.message}")
        if err.params:
            print(f"  Shortfall: {err.params.shortfall} {err.params.currency}")
        print(f"  Trace ID: {err.request_id}")
    except PaymentRequiredError as err:
        print(f"Blocked by Organization Balance (HTTP 402): {err.message}")
        print(f"  Action: Top up organization balance at dashboard. Trace: {err.request_id}")
    except CapExceededError as err:
        print(f"Blocked by Spend Cap (HTTP 403): {err.message}")
        print(f"  Trace ID: {err.request_id}")
    except ConflictError as err:
        print(f"Idempotency Conflict (HTTP 409): {err.message}")
        print(f"  Action: Retry with a new idempotency key. Trace: {err.request_id}")
    except RateLimitError as err:
        print(f"Rate Limit / Upstream Quota Reached (HTTP 429): {err.message}")
    except ZorveusError as err:
        print(f"Other Zorveus Error ({err.status_code}): {err.message}")
        print(f"  Trace ID: {err.request_id}")


def main() -> None:
    handle_simulated_allowance_error()
    handle_live_inference_call()


if __name__ == "__main__":
    main()
