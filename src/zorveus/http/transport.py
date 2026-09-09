from typing import Optional, Dict, Any, Type, TypeVar, Iterator
import httpx
from pydantic import BaseModel
from zorveus import __version__
from zorveus.errors import (
    ZorveusError,
    AuthenticationError,
    PaymentRequiredError,
    PermissionDeniedError,
    ProductUserAllowanceInsufficientError,
    ProductUserAllowanceInsufficientParams,
    CapExceededError,
    InvalidProductUserError,
    AppConnectionNotFoundError,
    NotFoundError,
    ConflictError,
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
    code: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

    request_id = response.headers.get("x-zorveus-request-id")
    reservation_id = response.headers.get("x-zorveus-reservation-id")

    try:
        raw_body = response.json()
        if isinstance(raw_body, dict):
            err_obj = None
            if "error" in raw_body and isinstance(raw_body["error"], dict):
                top_err = raw_body["error"]
                psf = top_err.get("provider_specific_fields")
                if isinstance(psf, dict) and "error" in psf and isinstance(psf["error"], dict):
                    err_obj = psf["error"]
                else:
                    err_obj = top_err

            if err_obj:
                message = err_obj.get("message", message)
                code = err_obj.get("code")
                params = err_obj.get("params")
            elif "detail" in raw_body and isinstance(raw_body["detail"], str):
                message = raw_body["detail"]
            elif "message" in raw_body and isinstance(raw_body["message"], str):
                message = raw_body["message"]
    except Exception:
        pass

    normalized_code = (code or "").lower()

    if status == 401:
        raise AuthenticationError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 402:
        raise PaymentRequiredError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code or "zorveus_reservation_insufficient_balance",
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 403:
        if (
            normalized_code == "zorveus_product_user_allowance_insufficient"
            or normalized_code == "zorveus_product_user_credits_insufficient"
            or "allowance" in normalized_code
        ):
            allowance_params = ProductUserAllowanceInsufficientParams.from_dict(params)
            raise ProductUserAllowanceInsufficientError(
                message,
                status_code=status,
                raw_body=raw_body,
                code=code,
                request_id=request_id,
                reservation_id=reservation_id,
                params=allowance_params,
            )

        if normalized_code == "zorveus_cap_exceeded" or "cap_exceed" in normalized_code:
            raise CapExceededError(
                message,
                status_code=status,
                raw_body=raw_body,
                code=code,
                request_id=request_id,
                reservation_id=reservation_id,
            )

        if (
            normalized_code in (
                "zorveus_product_user_not_found",
                "zorveus_invalid_product_user",
                "zorveus_product_user_identity_error",
            )
            or "product_user_not_found" in normalized_code
            or "invalid_product_user" in normalized_code
        ):
            raise InvalidProductUserError(
                message,
                status_code=status,
                raw_body=raw_body,
                code=code,
                request_id=request_id,
                reservation_id=reservation_id,
            )

        if normalized_code == "zorveus_app_connection_not_found" or "app_connection_not_found" in normalized_code:
            raise AppConnectionNotFoundError(
                message,
                status_code=status,
                raw_body=raw_body,
                code=code,
                request_id=request_id,
                reservation_id=reservation_id,
            )

        raise PermissionDeniedError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 404:
        raise NotFoundError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 409:
        raise ConflictError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code or "zorveus_reservation_conflict",
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 422:
        raise UnprocessableEntityError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )

    if status == 429:
        raise RateLimitError(
            message,
            status_code=status,
            raw_body=raw_body,
            code=code,
            request_id=request_id,
            reservation_id=reservation_id,
        )

    raise ZorveusError(
        message,
        status_code=status,
        raw_body=raw_body,
        code=code,
        request_id=request_id,
        reservation_id=reservation_id,
    )


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
            "User-Agent": f"Zorveus-Python/{__version__}",
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

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

        model_instance = response_model.model_validate(response.json())
        req_id = response.headers.get("x-zorveus-request-id")
        res_id = response.headers.get("x-zorveus-reservation-id")
        if req_id and hasattr(model_instance, "request_id") and getattr(model_instance, "request_id") is None:
            try:
                setattr(model_instance, "request_id", req_id)
            except Exception:
                pass
        if res_id and hasattr(model_instance, "reservation_id") and getattr(model_instance, "reservation_id") is None:
            try:
                setattr(model_instance, "reservation_id", res_id)
            except Exception:
                pass

        return model_instance

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        return self.request("GET", path, params=params, response_model=response_model)

    def post(
        self,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        return self.request(
            "POST",
            path,
            json_data=json_data,
            response_model=response_model,
        )

    def put(
        self,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        return self.request(
            "PUT",
            path,
            json_data=json_data,
            response_model=response_model,
        )

    def patch(
        self,
        path: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        return self.request(
            "PATCH",
            path,
            json_data=json_data,
            response_model=response_model,
        )

    def delete(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Any:
        return self.request(
            "DELETE",
            path,
            params=params,
            response_model=response_model,
        )

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
