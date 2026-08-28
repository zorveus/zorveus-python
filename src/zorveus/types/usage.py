from typing import Optional
from pydantic import BaseModel, Field

class UsageResponse(BaseModel):
    key_id: Optional[str] = None
    spend_cap: Optional[str] = None
    period_spend: Optional[str] = None
    remaining_allowance: Optional[str] = None
    currency: str = "USD"
