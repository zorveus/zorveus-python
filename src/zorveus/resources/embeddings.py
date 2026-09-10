from typing import Any, Dict, Optional

from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.http.transport import SyncHTTPTransport
from zorveus.types.embeddings import EmbeddingCreateResponse, EmbeddingInput


class EmbeddingsResource:
    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        model: str,
        input: EmbeddingInput,
        encoding_format: Optional[str] = None,
        dimensions: Optional[int] = None,
        user: Optional[str] = None,
        product_end_user_id: Optional[str] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingCreateResponse:
        payload: Dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not None:
            payload["encoding_format"] = encoding_format
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if user is not None:
            payload["user"] = user
        metadata = dict(zorveus_metadata or {})
        if product_end_user_id and "product_end_user_id" not in metadata:
            metadata["product_end_user_id"] = product_end_user_id
        if user and "external_user_id" not in metadata:
            metadata["external_user_id"] = user
        if metadata:
            payload["metadata"] = metadata
            payload["zorveus_metadata"] = metadata
        return self._transport.post(
            "/embeddings", json_data=payload, response_model=EmbeddingCreateResponse
        )


class AsyncEmbeddingsResource:
    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        model: str,
        input: EmbeddingInput,
        encoding_format: Optional[str] = None,
        dimensions: Optional[int] = None,
        user: Optional[str] = None,
        product_end_user_id: Optional[str] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
    ) -> EmbeddingCreateResponse:
        payload: Dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not None:
            payload["encoding_format"] = encoding_format
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if user is not None:
            payload["user"] = user
        metadata = dict(zorveus_metadata or {})
        if product_end_user_id and "product_end_user_id" not in metadata:
            metadata["product_end_user_id"] = product_end_user_id
        if user and "external_user_id" not in metadata:
            metadata["external_user_id"] = user
        if metadata:
            payload["metadata"] = metadata
            payload["zorveus_metadata"] = metadata
        return await self._transport.post(
            "/embeddings", json_data=payload, response_model=EmbeddingCreateResponse
        )
