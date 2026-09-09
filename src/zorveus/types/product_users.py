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
    usage: Optional[Dict[str, Any]] = None
    cap: Optional[Dict[str, Any]] = None
    credits: Optional[CreditSummary] = None
    credit_summary: Optional[CreditSummary] = None
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


class ProductUserListResponse(BaseModel):
    product_users: List[ProductUserResponse] = []
    data: List[ProductUserResponse] = []
    next_cursor: Optional[str] = None
    has_more: bool = False

    def model_post_init(self, __context: Any) -> None:
        if not self.data and self.product_users:
            self.data = self.product_users
        elif not self.product_users and self.data:
            self.product_users = self.data


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

