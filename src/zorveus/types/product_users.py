from typing import Optional
from pydantic import BaseModel, Field, field_validator
from zorveus.utils.decimal import validate_decimal_string

class ProductUser(BaseModel):
    id: str
    app_id: str
    external_user_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CreditSummary(BaseModel):
    available_credits: str
    total_granted: str
    total_spent: str
    currency: str = "USD"

    @field_validator("available_credits", "total_granted", "total_spent", mode="before")
    @classmethod
    def validate_decimals(cls, v: str) -> str:
        return validate_decimal_string(str(v))

class CreditGrant(BaseModel):
    id: str
    product_user_id: str
    amount: str
    source: Optional[str] = None
    reason: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: str) -> str:
        return validate_decimal_string(str(v))

class ProductUserResponse(BaseModel):
    product_user: ProductUser
    credit_summary: Optional[CreditSummary] = None

class GrantCreditResponse(BaseModel):
    credit_grant: CreditGrant
    credit_summary: CreditSummary
