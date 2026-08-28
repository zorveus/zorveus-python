from typing import Optional, Dict, Any

class ZorveusError(Exception):
    """Base exception for all Zorveus SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        raw_body: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_body = raw_body

class AuthenticationError(ZorveusError):
    """Raised on 401 Unauthorized errors."""

class PermissionDeniedError(ZorveusError):
    """Raised on 403 Forbidden errors."""

class NotFoundError(ZorveusError):
    """Raised on 404 Not Found errors."""

class UnprocessableEntityError(ZorveusError):
    """Raised on 422 Validation errors."""

class RateLimitError(ZorveusError):
    """Raised on 429 Too Many Requests errors."""

class InvalidDecimalError(ZorveusError):
    """Raised when credit amount is not a valid decimal string."""
