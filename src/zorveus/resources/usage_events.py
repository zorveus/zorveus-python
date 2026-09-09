from typing import Any, Dict, Optional

from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.http.transport import SyncHTTPTransport
from zorveus.types.usage import UsageEventListResponse


class UsageEventsResource:
    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def list(
        self,
        *,
        org_id: Optional[str] = None,
        app_id: Optional[str] = None,
        app_connection_id: Optional[str] = None,
        product_end_user_id: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        billing_mode: Optional[str] = None,
        status: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> UsageEventListResponse:
        params: Dict[str, Any] = {
            key: value
            for key, value in {
                "org_id": org_id,
                "app_id": app_id,
                "app_connection_id": app_connection_id,
                "product_end_user_id": product_end_user_id,
                "model": model,
                "provider": provider,
                "billing_mode": billing_mode,
                "status": status,
                "created_after": created_after,
                "created_before": created_before,
                "limit": limit,
                "cursor": cursor,
            }.items()
            if value is not None
        }
        return self._transport.get(
            "/dashboard-api/usage/events",
            params=params or None,
            response_model=UsageEventListResponse,
        )


class AsyncUsageEventsResource:
    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def list(self, **kwargs: Any) -> UsageEventListResponse:
        params = {key: value for key, value in kwargs.items() if value is not None}
        return await self._transport.get(
            "/dashboard-api/usage/events",
            params=params or None,
            response_model=UsageEventListResponse,
        )