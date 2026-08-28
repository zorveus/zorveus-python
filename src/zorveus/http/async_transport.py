from typing import Optional, Dict, Any, Type, TypeVar, AsyncIterator
import httpx
from pydantic import BaseModel
from zorveus import __version__
from zorveus.http.transport import raise_for_status
from zorveus.http.sse import parse_async_sse_stream

T = TypeVar("T", bound=BaseModel)

class AsyncHTTPTransport:
    """Asynchronous HTTP transport wrapping httpx.AsyncClient."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": f"zorveus-python/{__version__}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=headers, timeout=timeout)

    async def request(
        self,
        method: str,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        """Sends async HTTP request and validates JSON response against Pydantic model."""
        response = await self.client.request(method, path, json=json_data, params=params)
        raise_for_status(response)

        if response_model is None:
            return response.json()

        return response_model.model_validate(response.json())

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return await self.request("GET", path, params=params, response_model=response_model)

    async def post(self, path: str, *, json_data: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return await self.request("POST", path, json_data=json_data, response_model=response_model)

    async def put(self, path: str, *, json_data: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return await self.request("PUT", path, json_data=json_data, response_model=response_model)

    async def stream(
        self,
        method: str,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        response_model: Type[T],
    ) -> AsyncIterator[T]:
        """Sends async HTTP streaming request and yields parsed SSE objects."""
        req = self.client.build_request(method, path, json=json_data)
        response = await self.client.send(req, stream=True)
        raise_for_status(response)
        return parse_async_sse_stream(response.aiter_lines(), response_model)

    async def close(self) -> None:
        await self.client.aclose()
