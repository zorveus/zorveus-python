from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass(frozen=True)
class ProductUserAllowanceInsufficientParams:
    """Structured parameters returned on allowance exhaustion errors."""

    cap_rule_id: Optional[str] = None
    cap_period: Optional[str] = None
    currency: str = "USD"
    cap_amount: Optional[Decimal] = None
    settled_spend_this_period: Optional[Decimal] = None
    active_reservations_amount: Optional[Decimal] = None
    remaining_base_allowance: Optional[Decimal] = None
    promotional_credit_balance: Optional[Decimal] = None
    promotional_grant_remaining: Optional[Decimal] = None
    paid_grant_remaining: Optional[Decimal] = None
    available_allowance: Optional[Decimal] = None
    estimated_request_cost: Optional[Decimal] = None
    shortfall: Optional[Decimal] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ProductUserAllowanceInsufficientParams":
        if not data or not isinstance(data, dict):
            return cls()

        def parse_decimal(val: Any) -> Optional[Decimal]:
            if val is None:
                return None
            try:
                return Decimal(str(val))
            except (InvalidOperation, TypeError, ValueError):
                return None

        return cls(
            cap_rule_id=data.get("cap_rule_id"),
            cap_period=data.get("cap_period"),
            currency=data.get("currency", "USD"),
            cap_amount=parse_decimal(data.get("cap_amount")),
            settled_spend_this_period=parse_decimal(data.get("settled_spend_this_period")),
            active_reservations_amount=parse_decimal(data.get("active_reservations_amount")),
            remaining_base_allowance=parse_decimal(data.get("remaining_base_allowance")),
            promotional_credit_balance=parse_decimal(data.get("promotional_credit_balance")),
            promotional_grant_remaining=parse_decimal(data.get("promotional_grant_remaining")),
            paid_grant_remaining=parse_decimal(data.get("paid_grant_remaining")),
            available_allowance=parse_decimal(data.get("available_allowance")),
            estimated_request_cost=parse_decimal(data.get("estimated_request_cost")),
            shortfall=parse_decimal(data.get("shortfall")),
        )


class ZorveusError(Exception):
    """Base exception for all Zorveus SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        raw_body: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        reservation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_body = raw_body
        self.code = code
        self.request_id = request_id
        self.reservation_id = reservation_id


class AuthenticationError(ZorveusError):
    """Raised on 401 Unauthorized errors."""


class PaymentRequiredError(ZorveusError):
    """Raised on 402 Payment Required errors (e.g. insufficient organization wallet balance)."""


class PermissionDeniedError(ZorveusError):
    """Raised on 403 Forbidden errors."""


class ProductUserAllowanceInsufficientError(PermissionDeniedError):
    """Raised when request cost exceeds product user base cap plus promotional credits."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = 403,
        raw_body: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
        reservation_id: Optional[str] = None,
        params: Optional[ProductUserAllowanceInsufficientParams] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )
        self.params = params or ProductUserAllowanceInsufficientParams()


class CapExceededError(PermissionDeniedError):
    """Raised when an inference key or organization cap is exceeded."""


class InvalidProductUserError(PermissionDeniedError):
    """Raised when the supplied product-user identifier cannot be resolved for the org and app.

    The guide requires this to be a distinct 403 from allowance exhaustion.
    Do not treat an invalid product-user identifier as an absent product user.
    """


class AppConnectionNotFoundError(PermissionDeniedError):
    """Raised when an inference key or connection is missing or revoked."""


class NotFoundError(ZorveusError):
    """Raised on 404 Not Found errors."""


class ConflictError(ZorveusError):
    """Raised on 409 Conflict errors (e.g. idempotency key parameter mismatch)."""


class UnprocessableEntityError(ZorveusError):
    """Raised on 422 Validation errors."""


class RateLimitError(ZorveusError):
    """Raised on 429 Too Many Requests errors."""


class InvalidDecimalError(ZorveusError):
    """Raised when credit amount is not a valid decimal string."""
