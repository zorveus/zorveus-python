from typing import Annotated, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, JsonValue
from typing_extensions import TypeAlias

from zorveus.types.usage_metadata import UsageMetadata

ProductUserActivityType: TypeAlias = Literal[
    "usage", "credit_added", "credit_revoked", "credit_expired", "credit_refunded",
    "credit_adjusted", "allowance_debt_repayment",
]


class ProductUserCreditAllocation(BaseModel):
    credit_grant_id: str
    amount: str
    currency: str
    metadata: Optional[Dict[str, JsonValue]] = None


class ProductUserUsageActivity(BaseModel):
    charged_credit_units: Optional[str] = None
    id: str
    type: Literal["usage"]
    label: str
    amount: str
    currency: str
    status: str
    created_at: str
    model: str
    usage_metadata: Optional[UsageMetadata] = None
    base_allowance_charge_amount: Optional[str] = None
    credit_charge_amount: str
    uncovered_charge_amount: Optional[str] = None
    credit_allocations: List[ProductUserCreditAllocation]


class ProductUserCreditActivity(BaseModel):
    id: str
    type: Literal[
        "credit_added", "credit_revoked", "credit_expired", "credit_refunded",
        "credit_adjusted", "allowance_debt_repayment",
    ]
    label: str
    amount: str
    currency: str
    status: Literal["completed"]
    created_at: str
    credit_grant_id: Optional[str] = None
    metadata: Optional[Dict[str, JsonValue]] = None


ProductUserActivityItem: TypeAlias = Annotated[
    Union[ProductUserUsageActivity, ProductUserCreditActivity], Field(discriminator="type")
]


class ProductUserActivityResponse(BaseModel):
    product_end_user_id: str
    items: List[ProductUserActivityItem]
    next_cursor: Optional[str] = None
    has_more: bool
    limit: int
