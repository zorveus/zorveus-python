from decimal import Decimal
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, field_validator
from zorveus.utils.decimal import validate_decimal_string


class CreditSummary(BaseModel):
    currency: str = "USD"
    available_credits: str
    active_grant_count: int = 0
    expiring_soon_amount: Optional[str] = None
    spent_this_month: Optional[str] = None
    spent_total: Optional[str] = None
    last_grant_at: Optional[str] = None
    last_used_at: Optional[str] = None
    # Amount beyond the cap and available credits in track_only or overrun cases.
    # Zero means the request was fully covered.
    uncovered_virtual_spend: Optional[str] = None
    # For backward compatibility
    total_granted: Optional[str] = None
    total_spent: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.total_spent and self.spent_total:
            self.total_spent = self.spent_total
        elif not self.spent_total and self.total_spent:
            self.spent_total = self.total_spent

    @field_validator(
        "available_credits",
        "expiring_soon_amount",
        "spent_this_month",
        "spent_total",
        "total_granted",
        "total_spent",
        mode="before",
    )
    @classmethod
    def validate_decimals(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_decimal_string(str(v))


ProductUserCreditSummaryResponse = CreditSummary


class CreditGrant(BaseModel):
    credit_grant_id: Optional[str] = None
    id: Optional[str] = None
    org_id: Optional[str] = None
    app_id: Optional[str] = None
    product_end_user_id: Optional[str] = None
    product_user_id: Optional[str] = None
    amount: str
    remaining_amount: Optional[str] = None
    currency: str = "USD"
    source: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.credit_grant_id and self.id:
            self.credit_grant_id = self.id
        elif not self.id and self.credit_grant_id:
            self.id = self.credit_grant_id

        if not self.product_end_user_id and self.product_user_id:
            self.product_end_user_id = self.product_user_id
        elif not self.product_user_id and self.product_end_user_id:
            self.product_user_id = self.product_end_user_id

    @field_validator("amount", "remaining_amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_decimal_string(str(v))


class ProductUserCreditGrantListResponse(BaseModel):
    credit_grants: List[CreditGrant]


class ProductUserUsageBucket(BaseModel):
    sell_cost: str = "0.000000000000"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    request_count: int = 0

    @field_validator("sell_cost", mode="before")
    @classmethod
    def validate_sell_cost(cls, v: Optional[str]) -> str:
        if v is None:
            return "0.000000000000"
        return validate_decimal_string(str(v))


class ProductUserUsageSummary(BaseModel):
    this_period: Optional[ProductUserUsageBucket] = None
    this_month: Optional[ProductUserUsageBucket] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    total: Optional[ProductUserUsageBucket] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.this_period and self.this_month:
            self.this_period = self.this_month
        elif not self.this_month and self.this_period:
            self.this_month = self.this_period


class ProductUserCapResponse(BaseModel):
    source: Optional[str] = None
    cap_rule_id: Optional[str] = None
    amount: Optional[str] = None
    currency: str = "USD"
    period: Optional[str] = None
    spent_this_period: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    reset_at: Optional[str] = None
    status: Optional[str] = "active"
    updated_at: Optional[str] = None

    @field_validator("amount", "spent_this_period", mode="before")
    @classmethod
    def validate_decimals(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_decimal_string(str(v))


ProductUserCap = ProductUserCapResponse


class ProductUserAllowanceResponse(BaseModel):
    app_connection_id: Optional[str] = None
    cap_source: Optional[str] = None
    cap_rule_id: Optional[str] = None
    credit_mode: Optional[str] = None
    overrun_policy: Optional[str] = None
    currency: str = "USD"
    period: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    cap_amount: Optional[str] = None
    spent_this_period: Optional[str] = None
    remaining_base_allowance: Optional[str] = None
    available_credits: Optional[str] = None
    available_allowance: Optional[str] = None

    @field_validator(
        "cap_amount",
        "spent_this_period",
        "remaining_base_allowance",
        "available_credits",
        "available_allowance",
        mode="before",
    )
    @classmethod
    def validate_decimals(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return validate_decimal_string(str(v))


ProductUserAllowance = ProductUserAllowanceResponse


class ProductUserResponse(BaseModel):
    product_end_user_id: Optional[str] = None
    id: Optional[str] = None
    org_id: Optional[str] = None
    app_id: str
    external_user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    email_hash: Optional[str] = None
    status: Optional[str] = "active"
    metadata: Optional[Dict[str, Any]] = None
    allowance_starts_at: Optional[str] = None
    last_app_connection_id: Optional[str] = None
    usage: Optional[ProductUserUsageSummary] = None
    cap: Optional[ProductUserCapResponse] = None
    direct_cap: Optional[ProductUserCapResponse] = None
    credits: Optional[CreditSummary] = None
    credit_summary: Optional[CreditSummary] = None
    allowance: Optional[ProductUserAllowanceResponse] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.product_end_user_id:
            self.id = self.product_end_user_id
        elif not self.product_end_user_id and self.id:
            self.product_end_user_id = self.id

        if not self.credit_summary and self.credits:
            self.credit_summary = self.credits
        elif not self.credits and self.credit_summary:
            self.credits = self.credit_summary

    # --- Financial and allowance helper getters ---

    def get_available_allowance(self) -> str:
        """Returns the total spendable allowance available right now.

        Uses allowance.available_allowance if present.
        Falls back to credits.available_credits if no allowance object exists.
        Returns '0.000000000000' if neither is available.
        """
        if self.allowance and self.allowance.available_allowance is not None:
            return self.allowance.available_allowance

        if self.credits and self.credits.available_credits is not None:
            return self.credits.available_credits

        return "0.000000000000"

    def get_total_available_to_spend(self) -> str:
        """Returns the total amount the user can spend right now across base allowance and credits."""
        return self.get_available_allowance()

    def get_available_credits(self) -> str:
        """Returns available promotional credits."""
        if self.credits and self.credits.available_credits is not None:
            return self.credits.available_credits

        if self.allowance and self.allowance.available_credits is not None:
            return self.allowance.available_credits

        return "0.000000000000"

    def get_total_credits(self) -> str:
        """Alias for get_available_credits."""
        return self.get_available_credits()

    def get_total_allowance(self) -> Optional[str]:
        """Returns the configured cap amount from allowance or active cap (ignoring direct_cap)."""
        if self.allowance and self.allowance.cap_amount is not None:
            return self.allowance.cap_amount

        if self.cap and self.cap.amount is not None:
            return self.cap.amount

        return None

    def get_cap_spent(self) -> str:
        """Returns the amount spent against the cap in the current period from allowance or active cap."""
        if self.allowance and self.allowance.spent_this_period is not None:
            return self.allowance.spent_this_period

        if self.cap and self.cap.spent_this_period is not None:
            return self.cap.spent_this_period

        return "0.000000000000"

    def get_remaining_base_allowance(self) -> Optional[str]:
        """Returns remaining base allowance before promotional credits are consumed."""
        if not self.allowance:
            return None
        return self.allowance.remaining_base_allowance

    def get_usage_cost(self, period: str = "this_period") -> str:
        """Returns usage sell cost for 'this_period' ('this_month') or 'total'."""
        if not self.usage:
            return "0.000000000000"

        if period in ("this_period", "this_month"):
            bucket = self.usage.this_period or self.usage.this_month
            if bucket:
                return bucket.sell_cost

        if period == "total" and self.usage.total:
            return self.usage.total.sell_cost

        return "0.000000000000"

    def has_available_allowance(self) -> bool:
        """Returns True if the user has spendable allowance or credits remaining."""
        return Decimal(self.get_available_allowance()) > Decimal("0")

    def get_available_allowance_decimal(self) -> Decimal:
        """Returns available allowance as a Decimal."""
        return Decimal(self.get_available_allowance())

    def get_total_available_to_spend_decimal(self) -> Decimal:
        """Returns total spendable amount as a Decimal."""
        return self.get_available_allowance_decimal()

    def get_available_credits_decimal(self) -> Decimal:
        """Returns available credits as a Decimal."""
        return Decimal(self.get_available_credits())

    def get_total_credits_decimal(self) -> Decimal:
        """Alias for get_available_credits_decimal."""
        return self.get_available_credits_decimal()

    def get_total_allowance_decimal(self) -> Optional[Decimal]:
        """Returns configured cap amount as a Decimal if configured."""
        val = self.get_total_allowance()
        if val is None:
            return None
        return Decimal(val)

    def get_cap_spent_decimal(self) -> Decimal:
        """Returns cap spent this period as a Decimal."""
        return Decimal(self.get_cap_spent())

    # --- Property accessors ---

    @property
    def total_available_allowance(self) -> str:
        return self.get_available_allowance()

    @property
    def total_available_to_spend(self) -> str:
        return self.get_total_available_to_spend()

    @property
    def total_credits(self) -> str:
        return self.get_available_credits()

    @property
    def cap_spent(self) -> str:
        return self.get_cap_spent()


class UpsertProductUserResponse(BaseModel):
    product_user: ProductUserResponse
    created: bool = False


class GrantCreditResponse(BaseModel):
    product_user: Optional[ProductUserResponse] = None
    credit_grant: CreditGrant
    credit_summary: CreditSummary


class RevokeCreditResponse(BaseModel):
    credit_grant: Optional[CreditGrant] = None
    revoked: bool = True


GrantProductUserCreditsResponse = GrantCreditResponse
ProductUser = ProductUserResponse


