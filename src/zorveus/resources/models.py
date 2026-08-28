from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.models import ModelListResponse, ModelObject

class ModelsResource:
    """Synchronous models discovery resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def list(self) -> ModelListResponse:
        """Lists available models."""
        return self._transport.get("/models", response_model=ModelListResponse)

    def get(self, model_id: str) -> ModelObject:
        """Retrieves single model metadata."""
        return self._transport.get(f"/models/{model_id}", response_model=ModelObject)


class AsyncModelsResource:
    """Asynchronous models discovery resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def list(self) -> ModelListResponse:
        """Lists available models asynchronously."""
        return await self._transport.get("/models", response_model=ModelListResponse)

    async def get(self, model_id: str) -> ModelObject:
        """Retrieves single model metadata asynchronously."""
        return await self._transport.get(f"/models/{model_id}", response_model=ModelObject)
