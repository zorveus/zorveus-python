from typing import Optional, Dict, Any, Type, TypeVar, Iterator
import httpx
from pydantic import BaseModel
from zorveus import __version__
from zorveus.errors import (
    ZorveusError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
    RateLimitError,
)
from zorveus.http.sse import parse_sync_sse_stream

T = TypeVar("T", bound=BaseModel)

def raise_for_status(response: httpx.Response) -> None:
    """Raises appropriate SDK exception if HTTP response status is 4xx or 5xx."""
    if response.is_success:
        return

    status = response.status_code
    message = f"HTTP {status}: {response.text}"
    raw_body = None

    try:
        raw_body = response.json()
        if isinstance(raw_body, dict):
            if "error" in raw_body and isinstance(raw_body["error"], dict):
                message = raw_body["error"].get("message", message)
            elif "message" in raw_body and isinstance(raw_body["message"], str):
                message = raw_body["message"]
    except Exception:
        pass

    if status == 401:
        raise AuthenticationError(message, status_code=status, raw_body=raw_body)
    if status == 403:
        raise PermissionDeniedError(message, status_code=status, raw_body=raw_body)
    if status == 404:
        raise NotFoundError(message, status_code=status, raw_body=raw_body)
    if status == 422:
        raise UnprocessableEntityError(message, status_code=status, raw_body=raw_body)
    if status == 429:
        raise RateLimitError(message, status_code=status, raw_body=raw_body)

    raise ZorveusError(message, status_code=status, raw_body=raw_body)


class SyncHTTPTransport:
    """Synchronous HTTP transport wrapping httpx.Client."""

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
        self.client = httpx.Client(base_url=self.base_url, headers=headers, timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        """Sends HTTP request and validates JSON response against Pydantic model."""
        response = self.client.request(method, path, json=json_data, params=params)
        raise_for_status(response)

        if response_model is None:
            return response.json()

        return response_model.model_validate(response.json())

    def get(self, path: str, *, params: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return self.request("GET", path, params=params, response_model=response_model)

    def post(self, path: str, *, json_data: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return self.request("POST", path, json_data=json_data, response_model=response_model)

    def put(self, path: str, *, json_data: Optional[Dict[str, Any]] = None, response_model: Optional[Type[T]] = None) -> Any:
        return self.request("PUT", path, json_data=json_data, response_model=response_model)

    def stream(
        self,
        method: str,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        response_model: Type[T],
    ) -> Iterator[T]:
        """Sends HTTP streaming request and yields parsed SSE objects."""
        req = self.client.build_request(method, path, json=json_data)
        response = self.client.send(req, stream=True)
        raise_for_status(response)
        return parse_sync_sse_stream(response.iter_lines(), response_model)

    def close(self) -> None:
        self.client.close()
