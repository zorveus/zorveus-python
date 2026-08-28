from typing import Optional, Dict, Any
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.provider_credentials import (
    ProviderCredentialResponse,
    ProviderCredentialListResponse,
)

class ProviderCredentialsResource:
    """Synchronous provider credentials management resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def create(self, *, app_id: str, provider: str, api_key: str) -> ProviderCredentialResponse:
        """Registers provider credential."""
        payload = {
            "app_id": app_id,
            "provider": provider,
            "api_key": api_key,
        }
        return self._transport.post(
            "/provider-credentials",
            json_data=payload,
            response_model=ProviderCredentialResponse,
        )

    def list(self, *, app_id: str) -> ProviderCredentialListResponse:
        """Lists registered provider credentials for an app."""
        params = {"app_id": app_id}
        return self._transport.get(
            "/provider-credentials",
            params=params,
            response_model=ProviderCredentialListResponse,
        )


class AsyncProviderCredentialsResource:
    """Asynchronous provider credentials management resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def create(self, *, app_id: str, provider: str, api_key: str) -> ProviderCredentialResponse:
        """Registers provider credential asynchronously."""
        payload = {
            "app_id": app_id,
            "provider": provider,
            "api_key": api_key,
        }
        return await self._transport.post(
            "/provider-credentials",
            json_data=payload,
            response_model=ProviderCredentialResponse,
        )

    async def list(self, *, app_id: str) -> ProviderCredentialListResponse:
        """Lists registered provider credentials for an app asynchronously."""
        params = {"app_id": app_id}
        return await self._transport.get(
            "/provider-credentials",
            params=params,
            response_model=ProviderCredentialListResponse,
        )
