from typing import Any
from zorveus._version import __version__
from zorveus._client import Zorveus, AsyncZorveus
from zorveus._service_client import ZorveusServiceClient, AsyncZorveusServiceClient
from zorveus._oauth import ZorveusOAuth, PKCEData, TokenResponse, ValidationResult
from zorveus.errors import (
    ZorveusError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
    RateLimitError,
    InvalidDecimalError,
)

def __getattr__(name: str) -> Any:
    if name in ("ZorveusOpenAI", "AsyncZorveusOpenAI"):
        import zorveus.openai as _zorveus_openai
        return getattr(_zorveus_openai, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "__version__",
    "Zorveus",
    "AsyncZorveus",
    "ZorveusServiceClient",
    "AsyncZorveusServiceClient",
    "ZorveusOAuth",
    "PKCEData",
    "TokenResponse",
    "ValidationResult",
    "ZorveusError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "UnprocessableEntityError",
    "RateLimitError",
    "InvalidDecimalError",
    "ZorveusOpenAI",
    "AsyncZorveusOpenAI",
]
