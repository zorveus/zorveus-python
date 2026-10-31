from zorveus.types.product_user_activity import ProductUserActivityResponse, ProductUserActivityType
from typing import Optional, Dict, Any, Final, Union, Mapping
from enum import Enum
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.product_users import (
    ProductUserResponse,
    CreditGrant,
    UpsertProductUserResponse,
    GrantCreditResponse,
    ProductUserCreditSummaryResponse,
    ProductUserCreditGrantListResponse,
    RevokeCreditResponse,
    ProductUserAllowanceDebtSummaryResponse,
)
from zorveus.utils.decimal import validate_decimal_string
from zorveus.errors import ZorveusError

def _product_user_read_headers(
    upsert_if_missing: Optional[bool], extra_headers: Optional[Mapping[str, str]],
) -> Optional[Mapping[str, str]]:
    if upsert_if_missing is None:
        return extra_headers
    if not isinstance(upsert_if_missing, bool):
        raise TypeError("upsert_if_missing must be a boolean")
    return {
        **{name: value for name, value in (extra_headers or {}).items()
           if name.lower() != "x-zorveus-upsert-product-user"},
        "X-Zorveus-Upsert-Product-User": "true" if upsert_if_missing else "false",
    }


def _selected_key_headers(
    inference_key: Optional[str], key_alias: Optional[str], headers: Optional[Mapping[str, str]],
) -> Mapping[str, str]:
    selected: Final = {
        **({"X-Zorveus-Inference-Key": inference_key} if inference_key is not None else {}),
        **({"X-Zorveus-Key-Alias": key_alias} if key_alias is not None else {}),
    }
    selected_names: Final = frozenset(name.lower() for name in selected)
    return {
        **{name: value for name, value in (headers or {}).items() if name.lower() not in selected_names},
        **selected,
    }


class _Unset(Enum):
    VALUE = "unset"


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
        allowance_starts_at: Union[str, None, _Unset] = _Unset.VALUE,
    ) -> UpsertProductUserResponse:
        """Upserts a product user profile."""
        payload: Final = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            **({"display_name": display_name} if display_name is not None else {}),
            **({"email": email} if email is not None else {}),
            **({"metadata": metadata} if metadata is not None else {}),
            **({"allowance_starts_at": allowance_starts_at} if allowance_starts_at is not _Unset.VALUE else {}),
        }

        return self._transport.put(
            "/product-users/by-external-id",
            json_data=payload,
            response_model=UpsertProductUserResponse,
        )

    def get_by_external_id(
        self, *, app_id: str, external_user_id: str,
        inference_key: Optional[str] = None,
        key_alias: Optional[str] = None,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserResponse:
        """Retrieves a product user profile and credit summary."""
        params = {"app_id": app_id, "external_user_id": external_user_id}
        return self._transport.get(
            "/product-users/by-external-id",
            params=params,
            response_model=ProductUserResponse,
            headers=_selected_key_headers(
                inference_key, key_alias, _product_user_read_headers(upsert_if_missing, extra_headers)
            ),
        )

    def get_credit_summary_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        currency: str = "USD",
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserCreditSummaryResponse:
        """Retrieves live credit summary for a product user by external ID."""
        params = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "currency": currency,
        }
        return self._transport.get(
            "/product-users/by-external-id/credit-summary",
            params=params,
            response_model=ProductUserCreditSummaryResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    def list_activity_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        activity_type: Optional[ProductUserActivityType] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        currency: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserActivityResponse:
        params: Final = {
            "app_id": app_id, "external_user_id": external_user_id, "limit": limit,
            **({"type": activity_type} if activity_type is not None else {}),
            **({"from": from_date} if from_date is not None else {}),
            **({"to": to_date} if to_date is not None else {}),
            **({"currency": currency} if currency is not None else {}),
            **({"cursor": cursor} if cursor is not None else {}),
        }
        return self._transport.get(
            "/product-users/by-external-id/activity",
            params=params,
            response_model=ProductUserActivityResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    def list_credit_grants_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserCreditGrantListResponse:
        """Lists credit grants for a product user by external ID."""
        params: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "limit": limit,
        }
        if status is not None:
            params["status"] = status
        if source is not None:
            params["source"] = source

        return self._transport.get(
            "/product-users/by-external-id/credit-grants",
            params=params,
            response_model=ProductUserCreditGrantListResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    def get_credit_grant_by_external_reference(
        self, *, app_id: str, external_user_id: str, external_reference: str,
    ) -> CreditGrant:
        return self._transport.get(
            "/product-users/by-external-id/credit-grants/by-reference",
            params={"app_id": app_id, "external_user_id": external_user_id, "external_reference": external_reference},
            response_model=CreditGrant,
        )

    def grant_credit_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        amount: str,
        currency: str = "USD",
        source: Optional[str] = None,
        reason: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        external_reference: Optional[str] = None,
        credit_units_per_usd: Optional[str] = None,
    ) -> GrantCreditResponse:
        """Grants credits to a product user with 12-decimal precision validation."""
        valid_amount: Final = validate_decimal_string(amount)
        payload: Final = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "amount": valid_amount,
            "currency": currency,
            **({"external_reference": external_reference} if external_reference is not None else {}),
            **({"credit_units_per_usd": validate_decimal_string(credit_units_per_usd)}
               if credit_units_per_usd is not None else {}),
            **({"source": source} if source is not None else {}),
            **({"reason": reason} if reason is not None else {}),
            **({"expires_at": expires_at} if expires_at is not None else {}),
            **({"metadata": metadata} if metadata is not None else {}),
        }

        return self._transport.post(
            "/product-users/by-external-id/credit-grants",
            json_data=payload,
            response_model=GrantCreditResponse,
        )

    def revoke_credit(
        self, product_end_user_id: str, credit_grant_id: str
    ) -> RevokeCreditResponse:
        raise ZorveusError(
            "Credit-grant revocation requires a dashboard session. Revoke the grant in the Zorveus dashboard.",
            code="zorveus_dashboard_session_required",
        )

    def get_allowance_debt_by_external_id(
        self, *, app_id: str, external_user_id: str, currency: str = "USD",
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserAllowanceDebtSummaryResponse:
        params: Final = {"app_id": app_id, "external_user_id": external_user_id, "currency": currency}
        return self._transport.get(
            "/product-users/by-external-id/allowance-debt",
            params=params,
            response_model=ProductUserAllowanceDebtSummaryResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
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
        allowance_starts_at: Union[str, None, _Unset] = _Unset.VALUE,
    ) -> UpsertProductUserResponse:
        """Upserts a product user profile asynchronously."""
        payload: Final = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            **({"display_name": display_name} if display_name is not None else {}),
            **({"email": email} if email is not None else {}),
            **({"metadata": metadata} if metadata is not None else {}),
            **({"allowance_starts_at": allowance_starts_at} if allowance_starts_at is not _Unset.VALUE else {}),
        }

        return await self._transport.put(
            "/product-users/by-external-id",
            json_data=payload,
            response_model=UpsertProductUserResponse,
        )

    async def get_by_external_id(
        self, *, app_id: str, external_user_id: str,
        inference_key: Optional[str] = None,
        key_alias: Optional[str] = None,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserResponse:
        """Retrieves a product user profile asynchronously."""
        params = {"app_id": app_id, "external_user_id": external_user_id}
        return await self._transport.get(
            "/product-users/by-external-id",
            params=params,
            response_model=ProductUserResponse,
            headers=_selected_key_headers(
                inference_key, key_alias, _product_user_read_headers(upsert_if_missing, extra_headers)
            ),
        )

    async def get_credit_summary_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        currency: str = "USD",
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserCreditSummaryResponse:
        """Retrieves live credit summary for a product user by external ID asynchronously."""
        params = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "currency": currency,
        }
        return await self._transport.get(
            "/product-users/by-external-id/credit-summary",
            params=params,
            response_model=ProductUserCreditSummaryResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    async def list_activity_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        activity_type: Optional[ProductUserActivityType] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        currency: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserActivityResponse:
        params: Final = {
            "app_id": app_id, "external_user_id": external_user_id, "limit": limit,
            **({"type": activity_type} if activity_type is not None else {}),
            **({"from": from_date} if from_date is not None else {}),
            **({"to": to_date} if to_date is not None else {}),
            **({"currency": currency} if currency is not None else {}),
            **({"cursor": cursor} if cursor is not None else {}),
        }
        return await self._transport.get(
            "/product-users/by-external-id/activity",
            params=params,
            response_model=ProductUserActivityResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    async def list_credit_grants_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        status: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserCreditGrantListResponse:
        """Lists credit grants for a product user by external ID asynchronously."""
        params: Dict[str, Any] = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "limit": limit,
        }
        if status is not None:
            params["status"] = status
        if source is not None:
            params["source"] = source

        return await self._transport.get(
            "/product-users/by-external-id/credit-grants",
            params=params,
            response_model=ProductUserCreditGrantListResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )

    async def get_credit_grant_by_external_reference(
        self, *, app_id: str, external_user_id: str, external_reference: str,
    ) -> CreditGrant:
        return await self._transport.get(
            "/product-users/by-external-id/credit-grants/by-reference",
            params={"app_id": app_id, "external_user_id": external_user_id, "external_reference": external_reference},
            response_model=CreditGrant,
        )

    async def grant_credit_by_external_id(
        self,
        *,
        app_id: str,
        external_user_id: str,
        amount: str,
        currency: str = "USD",
        source: Optional[str] = None,
        reason: Optional[str] = None,
        expires_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        external_reference: Optional[str] = None,
        credit_units_per_usd: Optional[str] = None,
    ) -> GrantCreditResponse:
        """Grants credits to a product user asynchronously."""
        valid_amount: Final = validate_decimal_string(amount)
        payload: Final = {
            "app_id": app_id,
            "external_user_id": external_user_id,
            "amount": valid_amount,
            "currency": currency,
            **({"external_reference": external_reference} if external_reference is not None else {}),
            **({"credit_units_per_usd": validate_decimal_string(credit_units_per_usd)}
               if credit_units_per_usd is not None else {}),
            **({"source": source} if source is not None else {}),
            **({"reason": reason} if reason is not None else {}),
            **({"expires_at": expires_at} if expires_at is not None else {}),
            **({"metadata": metadata} if metadata is not None else {}),
        }

        return await self._transport.post(
            "/product-users/by-external-id/credit-grants",
            json_data=payload,
            response_model=GrantCreditResponse,
        )

    async def revoke_credit(
        self, product_end_user_id: str, credit_grant_id: str
    ) -> RevokeCreditResponse:
        raise ZorveusError(
            "Credit-grant revocation requires a dashboard session. Revoke the grant in the Zorveus dashboard.",
            code="zorveus_dashboard_session_required",
        )

    async def get_allowance_debt_by_external_id(
        self, *, app_id: str, external_user_id: str, currency: str = "USD",
        upsert_if_missing: Optional[bool] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> ProductUserAllowanceDebtSummaryResponse:
        params: Final = {"app_id": app_id, "external_user_id": external_user_id, "currency": currency}
        return await self._transport.get(
            "/product-users/by-external-id/allowance-debt",
            params=params,
            response_model=ProductUserAllowanceDebtSummaryResponse,
            headers=_product_user_read_headers(upsert_if_missing, extra_headers),
        )
