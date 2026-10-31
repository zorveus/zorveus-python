from typing import Any, Dict, Mapping, Optional

from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.http.transport import SyncHTTPTransport
from zorveus.types.embeddings import EmbeddingCreateResponse, EmbeddingInput

from zorveus.types.usage_metadata import UsageMetadata


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
        usage_metadata: Optional[UsageMetadata] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> EmbeddingCreateResponse:
        payload: Dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not None:
            payload["encoding_format"] = encoding_format
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if user is not None:
            payload["user"] = user
        metadata = dict(zorveus_metadata or {})
        if usage_metadata is not None:
            metadata["usage_metadata"] = dict(usage_metadata)
        if product_end_user_id and "product_end_user_id" not in metadata:
            metadata["product_end_user_id"] = product_end_user_id
        if user and "external_user_id" not in metadata:
            metadata["external_user_id"] = user
        if metadata:
            payload["metadata"] = metadata
        return self._transport.post(
            "/embeddings", json_data=payload, response_model=EmbeddingCreateResponse, headers=extra_headers
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
        usage_metadata: Optional[UsageMetadata] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> EmbeddingCreateResponse:
        payload: Dict[str, Any] = {"model": model, "input": input}
        if encoding_format is not None:
            payload["encoding_format"] = encoding_format
        if dimensions is not None:
            payload["dimensions"] = dimensions
        if user is not None:
            payload["user"] = user
        metadata = dict(zorveus_metadata or {})
        if usage_metadata is not None:
            metadata["usage_metadata"] = dict(usage_metadata)
        if product_end_user_id and "product_end_user_id" not in metadata:
            metadata["product_end_user_id"] = product_end_user_id
        if user and "external_user_id" not in metadata:
            metadata["external_user_id"] = user
        if metadata:
            payload["metadata"] = metadata
        return await self._transport.post(
            "/embeddings", json_data=payload, response_model=EmbeddingCreateResponse, headers=extra_headers
        )
