import os
from typing import Optional
from zorveus.resources.chat import ChatResource, AsyncChatResource
from zorveus.resources.models import ModelsResource, AsyncModelsResource
from zorveus.types.usage import UsageResponse
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport

class Zorveus:
    """Client for AI inference, chat streaming, model discovery, and spend queries."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")

        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")
        self._transport = SyncHTTPTransport(api_key=key, base_url=base_url, timeout=timeout)

        self.chat = ChatResource(self._transport)
        self.models = ModelsResource(self._transport)

    def get_usage(self) -> UsageResponse:
        """Query live spend cap, period spend, and remaining allowance."""
        return self._transport.get("/inference-keys/usage", response_model=UsageResponse)

    def close(self) -> None:
        self._transport.close()


class AsyncZorveus:
    """Asynchronous client for AI inference, chat streaming, and model discovery."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        timeout: float = 60.0,
    ) -> None:
        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")

        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")
        self._transport = AsyncHTTPTransport(api_key=key, base_url=base_url, timeout=timeout)

        self.chat = AsyncChatResource(self._transport)
        self.models = AsyncModelsResource(self._transport)

    async def get_usage(self) -> UsageResponse:
        """Query live spend cap, period spend, and remaining allowance asynchronously."""
        return await self._transport.get("/inference-keys/usage", response_model=UsageResponse)

    async def close(self) -> None:
        await self._transport.close()
