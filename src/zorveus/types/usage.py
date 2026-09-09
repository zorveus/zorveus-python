from typing import Any, List, Optional
from pydantic import BaseModel


class UsageResponse(BaseModel):
    app_connection_id: Optional[str] = None
    key_id: Optional[str] = None
    status: Optional[str] = None
    app_id: Optional[str] = None
    period: Optional[str] = None
    currency: str = "USD"
    spend_cap: Optional[str] = None
    spent_this_period: Optional[str] = None
    period_spend: Optional[str] = None
    remaining_balance: Optional[str] = None
    remaining_allowance: Optional[str] = None
    reset_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.key_id and self.app_connection_id:
            self.key_id = self.app_connection_id
        elif not self.app_connection_id and self.key_id:
            self.app_connection_id = self.key_id

        if not self.period_spend and self.spent_this_period:
            self.period_spend = self.spent_this_period
        elif not self.spent_this_period and self.period_spend:
            self.spent_this_period = self.period_spend

        if not self.remaining_allowance and self.remaining_balance:
            self.remaining_allowance = self.remaining_balance
        elif not self.remaining_balance and self.remaining_allowance:
            self.remaining_balance = self.remaining_allowance


class UsageEvent(BaseModel):
    """A single inference usage event returned by the usage-events API.

    Monetary fields are decimal strings. Parse them with Decimal(), not float().
    Cache fields follow the guide's cache-aware settlement spec.
    """

    usage_event_id: Optional[str] = None
    zorveus_request_id: Optional[str] = None
    app_id: Optional[str] = None
    app_connection_id: Optional[str] = None
    product_end_user_id: Optional[str] = None
    external_user_id: Optional[str] = None
    member_user_id: Optional[str] = None
    org_member_id: Optional[str] = None
    org_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    provider_model: Optional[str] = None

    # Token counts
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_creation_1h_input_tokens: int = 0

    # Cache settlement metadata
    cache_usage_breakdown_status: Optional[str] = None
    pricing_service_tier: Optional[str] = None
    cache_pricing_fallback_reason: Optional[str] = None
    # Decimal string: reference-price allowance saved by cache reads
    cache_savings: Optional[str] = None

    # Monetary fields (all decimal strings)
    virtual_spend: Optional[str] = None
    uncovered_virtual_spend: Optional[str] = None
    provider_cost: Optional[str] = None
    sell_cost: Optional[str] = None
    usage_cost: Optional[str] = None
    unfunded_wallet_charge: Optional[str] = None

    # Billing metadata
    billing_mode: Optional[str] = None
    overrun_policy: Optional[str] = None
    overrun_reason: Optional[str] = None
    reservation_id: Optional[str] = None
    provider_credential_id: Optional[str] = None
    provider_credential_version_id: Optional[str] = None
    requested_max_output_tokens: Optional[int] = None
    applied_max_output_tokens: Optional[int] = None

    status: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[str] = None


class UsageEventListResponse(BaseModel):
    """Paginated list of usage events from GET /dashboard-api/usage/events."""

    events: List[UsageEvent] = []
    next_cursor: Optional[str] = None
    has_more: bool = False
    limit: Optional[int] = None


def normal_input_tokens(event: UsageEvent) -> Optional[int]:
    """Returns uncached input tokens when the gateway reported a breakdown."""
    if event.cache_usage_breakdown_status != "reported" or event.input_tokens is None:
        return None
    return max(
        0,
        event.input_tokens
        - event.cache_read_input_tokens
        - event.cache_creation_input_tokens
        - event.cache_creation_1h_input_tokens,
    )

