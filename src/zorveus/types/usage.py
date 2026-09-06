from typing import Any, Optional
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

