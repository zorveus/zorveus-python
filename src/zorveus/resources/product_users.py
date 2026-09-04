from typing import Optional, Dict, Any
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.product_users import (
    ProductUserResponse,
    UpsertProductUserResponse,
    GrantCreditResponse,
)
from zorveus.utils.decimal import validate_decimal_string

class ProductUsersResource:
    """Synchronous product users and credit management resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def create_or_update(
        self,
        *,
        app_id: str,
        external_user_id: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UpsertProductUserResponse:
        """Upserts a product user profile."""
        payload: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
        }
        if display_name is not None:
            payload["display_name"] = display_name
        if email is not None:
            payload["email"] = email
        if metadata is not None:
            payload["metadata"] = metadata

        return self._transport.put(
            "/product-users/by-external-id",
            json_data=payload,
            response_model=UpsertProductUserResponse,
        )

    def get_by_external_id(self, *, app_id: str, external_user_id: str) -> ProductUserResponse:
        """Retrieves a product user profile and credit summary."""
        params = {"app_id": app_id, "external_user_id": external_user_id}
        return self._transport.get(
            "/product-users/by-external-id",
            params=params,
            response_model=ProductUserResponse,
        )

    def grant_credit_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        amount: str,
        source: Optional[str] = None,
        reason: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GrantCreditResponse:
        """Grants credits to a product user with 12-decimal precision validation."""
        valid_amount = validate_decimal_string(amount)
        payload: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "amount": valid_amount,
        }
        if source is not None:
            payload["source"] = source
        if reason is not None:
            payload["reason"] = reason
        if expires_at is not None:
            payload["expires_at"] = expires_at
        if metadata is not None:
            payload["metadata"] = metadata

        return self._transport.post(
            "/product-users/by-external-id/credit-grants",
            json_data=payload,
            response_model=GrantCreditResponse,
        )


class AsyncProductUsersResource:
    """Asynchronous product users and credit management resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def create_or_update(
        self,
        *,
        app_id: str,
        external_user_id: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UpsertProductUserResponse:
        """Upserts a product user profile asynchronously."""
        payload: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
        }
        if display_name is not None:
            payload["display_name"] = display_name
        if email is not None:
            payload["email"] = email
        if metadata is not None:
            payload["metadata"] = metadata

        return await self._transport.put(
            "/product-users/by-external-id",
            json_data=payload,
            response_model=UpsertProductUserResponse,
        )

    async def get_by_external_id(self, *, app_id: str, external_user_id: str) -> ProductUserResponse:
        """Retrieves a product user profile asynchronously."""
        params = {"app_id": app_id, "external_user_id": external_user_id}
        return await self._transport.get(
            "/product-users/by-external-id",
            params=params,
            response_model=ProductUserResponse,
        )

    async def grant_credit_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        amount: str,
        source: Optional[str] = None,
        reason: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GrantCreditResponse:
        """Grants credits to a product user asynchronously."""
        valid_amount = validate_decimal_string(amount)
        payload: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "amount": valid_amount,
        }
        if source is not None:
            payload["source"] = source
        if reason is not None:
            payload["reason"] = reason
        if expires_at is not None:
            payload["expires_at"] = expires_at
        if metadata is not None:
            payload["metadata"] = metadata

        return await self._transport.post(
            "/product-users/by-external-id/credit-grants",
            json_data=payload,
            response_model=GrantCreditResponse,
        )
