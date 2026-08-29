import os
from typing import Optional, Dict, Any, Mapping
from zorveus._version import __version__

try:
    from openai import OpenAI as _OpenAI, AsyncOpenAI as _AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    _OpenAI = object  # type: ignore
    _AsyncOpenAI = object  # type: ignore


def _merge_zorveus_metadata(
    existing_extra_body: Optional[Dict[str, Any]],
    client_ext_id: Optional[str],
    client_display_name: Optional[str],
    client_email: Optional[str],
    client_user_metadata: Optional[Dict[str, Any]],
    kwargs: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    ext_id = kwargs.pop("external_user_id", client_ext_id)
    display_name = kwargs.pop("display_name", client_display_name)
    email = kwargs.pop("email", client_email)
    user_meta = kwargs.pop("user_metadata", client_user_metadata)

    if not any([ext_id, display_name, email, user_meta]):
        return existing_extra_body

    extra_body = dict(existing_extra_body or {})
    metadata = dict(extra_body.get("metadata") or {})

    if ext_id and "external_user_id" not in metadata:
        metadata["external_user_id"] = ext_id

    product_user = dict(metadata.get("product_user") or {})
    if display_name and "display_name" not in product_user:
        product_user["display_name"] = display_name
    if email and "email" not in product_user:
        product_user["email"] = email
    if user_meta and "metadata" not in product_user:
        product_user["metadata"] = user_meta

    if product_user:
        metadata["product_user"] = product_user

    extra_body["metadata"] = metadata
    return extra_body


class _ZorveusCompletionsWrapper:
    def __init__(
        self,
        completions_resource: Any,
        client_ext_id: Optional[str],
        client_display_name: Optional[str],
        client_email: Optional[str],
        client_user_metadata: Optional[Dict[str, Any]],
    ) -> None:
        self._completions = completions_resource
        self._ext_id = client_ext_id
        self._display_name = client_display_name
        self._email = client_email
        self._user_metadata = client_user_metadata

    def create(self, *args: Any, **kwargs: Any) -> Any:
        extra_body = _merge_zorveus_metadata(
            kwargs.get("extra_body"),
            self._ext_id,
            self._display_name,
            self._email,
            self._user_metadata,
            kwargs,
        )
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        return self._completions.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _AsyncZorveusCompletionsWrapper:
    def __init__(
        self,
        completions_resource: Any,
        client_ext_id: Optional[str],
        client_display_name: Optional[str],
        client_email: Optional[str],
        client_user_metadata: Optional[Dict[str, Any]],
    ) -> None:
        self._completions = completions_resource
        self._ext_id = client_ext_id
        self._display_name = client_display_name
        self._email = client_email
        self._user_metadata = client_user_metadata

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        extra_body = _merge_zorveus_metadata(
            kwargs.get("extra_body"),
            self._ext_id,
            self._display_name,
            self._email,
            self._user_metadata,
            kwargs,
        )
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        return await self._completions.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _ZorveusResponsesWrapper:
    def __init__(
        self,
        responses_resource: Any,
        client_ext_id: Optional[str],
        client_display_name: Optional[str],
        client_email: Optional[str],
        client_user_metadata: Optional[Dict[str, Any]],
    ) -> None:
        self._responses = responses_resource
        self._ext_id = client_ext_id
        self._display_name = client_display_name
        self._email = client_email
        self._user_metadata = client_user_metadata

    def create(self, *args: Any, **kwargs: Any) -> Any:
        extra_body = _merge_zorveus_metadata(
            kwargs.get("extra_body"),
            self._ext_id,
            self._display_name,
            self._email,
            self._user_metadata,
            kwargs,
        )
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        return self._responses.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._responses, name)


class _AsyncZorveusResponsesWrapper:
    def __init__(
        self,
        responses_resource: Any,
        client_ext_id: Optional[str],
        client_display_name: Optional[str],
        client_email: Optional[str],
        client_user_metadata: Optional[Dict[str, Any]],
    ) -> None:
        self._responses = responses_resource
        self._ext_id = client_ext_id
        self._display_name = client_display_name
        self._email = client_email
        self._user_metadata = client_user_metadata

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        extra_body = _merge_zorveus_metadata(
            kwargs.get("extra_body"),
            self._ext_id,
            self._display_name,
            self._email,
            self._user_metadata,
            kwargs,
        )
        if extra_body is not None:
            kwargs["extra_body"] = extra_body

        return await self._responses.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._responses, name)


class ZorveusOpenAI(_OpenAI):
    """Zorveus wrapper around official OpenAI client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        external_user_id: Optional[str] = None,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        if not HAS_OPENAI:
            raise ImportError(
                "The 'openai' package is required to use ZorveusOpenAI. "
                "Install it with 'pip install zorveus[openai]'."
            )

        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")

        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")

        headers = dict(default_headers or {})
        headers["User-Agent"] = f"zorveus-python/{__version__}"

        super().__init__(
            api_key=key,
            base_url=base_url,
            default_headers=headers,
            **kwargs,
        )

        self.chat.completions = _ZorveusCompletionsWrapper(  # type: ignore
            self.chat.completions, external_user_id, display_name, email, user_metadata
        )
        if hasattr(self, "responses") and getattr(self, "responses") is not None:
            self.responses = _ZorveusResponsesWrapper(  # type: ignore
                self.responses, external_user_id, display_name, email, user_metadata
            )


class AsyncZorveusOpenAI(_AsyncOpenAI):
    """Async Zorveus wrapper around official OpenAI async client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        external_user_id: Optional[str] = None,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        if not HAS_OPENAI:
            raise ImportError(
                "The 'openai' package is required to use AsyncZorveusOpenAI. "
                "Install it with 'pip install zorveus[openai]'."
            )

        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")

        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")

        headers = dict(default_headers or {})
        headers["User-Agent"] = f"zorveus-python/{__version__}"

        super().__init__(
            api_key=key,
            base_url=base_url,
            default_headers=headers,
            **kwargs,
        )

        self.chat.completions = _AsyncZorveusCompletionsWrapper(  # type: ignore
            self.chat.completions, external_user_id, display_name, email, user_metadata
        )
        if hasattr(self, "responses") and getattr(self, "responses") is not None:
            self.responses = _AsyncZorveusResponsesWrapper(  # type: ignore
                self.responses, external_user_id, display_name, email, user_metadata
            )
