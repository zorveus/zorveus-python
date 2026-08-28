import os
from typing import Optional
from zorveus.resources.product_users import ProductUsersResource, AsyncProductUsersResource
from zorveus.resources.provider_credentials import ProviderCredentialsResource, AsyncProviderCredentialsResource
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport

class ZorveusServiceClient:
    """Client for organization administration, product users, and credit grants."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_SERVICE_KEY")
        if not key:
            raise ValueError("Service key is required. Pass api_key or set ZORVEUS_SERVICE_KEY.")

        url = base_url or os.environ.get("ZORVEUS_BASE_URL", "https://api.zorveus.com")
        self._transport = SyncHTTPTransport(api_key=key, base_url=url, timeout=timeout)

        self.product_users = ProductUsersResource(self._transport)
        self.provider_credentials = ProviderCredentialsResource(self._transport)

    def close(self) -> None:
        self._transport.close()


class AsyncZorveusServiceClient:
    """Asynchronous client for organization administration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_SERVICE_KEY")
        if not key:
            raise ValueError("Service key is required. Pass api_key or set ZORVEUS_SERVICE_KEY.")

        url = base_url or os.environ.get("ZORVEUS_BASE_URL", "https://api.zorveus.com")
        self._transport = AsyncHTTPTransport(api_key=key, base_url=url, timeout=timeout)

        self.product_users = AsyncProductUsersResource(self._transport)
        self.provider_credentials = AsyncProviderCredentialsResource(self._transport)

    async def close(self) -> None:
        await self._transport.close()
