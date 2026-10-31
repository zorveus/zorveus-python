from typing import Mapping, Optional
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.models import ModelListResponse, ModelObject

class ModelsResource:
    """Synchronous models discovery resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def list(self, *, extra_headers: Optional[Mapping[str, str]] = None) -> ModelListResponse:
        """Lists available models."""
        return self._transport.get("/models", response_model=ModelListResponse, headers=extra_headers)

    def get(self, model_id: str, *, extra_headers: Optional[Mapping[str, str]] = None) -> ModelObject:
        """Retrieves single model metadata."""
        return self._transport.get(f"/models/{model_id}", response_model=ModelObject, headers=extra_headers)


class AsyncModelsResource:
    """Asynchronous models discovery resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def list(self, *, extra_headers: Optional[Mapping[str, str]] = None) -> ModelListResponse:
        """Lists available models asynchronously."""
        return await self._transport.get("/models", response_model=ModelListResponse, headers=extra_headers)

    async def get(self, model_id: str, *, extra_headers: Optional[Mapping[str, str]] = None) -> ModelObject:
        """Retrieves single model metadata asynchronously."""
        return await self._transport.get(f"/models/{model_id}", response_model=ModelObject, headers=extra_headers)
