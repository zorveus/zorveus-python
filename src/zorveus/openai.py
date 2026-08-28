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


class _ZorveusCompletionsWrapper:
    def __init__(self, completions_resource: Any, client_external_user_id: Optional[str]) -> None:
        self._completions = completions_resource
        self._external_user_id = client_external_user_id

    def create(self, *args: Any, **kwargs: Any) -> Any:
        external_id = kwargs.pop("external_user_id", self._external_user_id)
        if external_id:
            extra_body = dict(kwargs.get("extra_body") or {})
            metadata = dict(extra_body.get("metadata") or {})
            if "external_user_id" not in metadata:
                metadata["external_user_id"] = external_id
            extra_body["metadata"] = metadata
            kwargs["extra_body"] = extra_body

        return self._completions.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _AsyncZorveusCompletionsWrapper:
    def __init__(self, completions_resource: Any, client_external_user_id: Optional[str]) -> None:
        self._completions = completions_resource
        self._external_user_id = client_external_user_id

    async def create(self, *args: Any, **kwargs: Any) -> Any:
        external_id = kwargs.pop("external_user_id", self._external_user_id)
        if external_id:
            extra_body = dict(kwargs.get("extra_body") or {})
            metadata = dict(extra_body.get("metadata") or {})
            if "external_user_id" not in metadata:
                metadata["external_user_id"] = external_id
            extra_body["metadata"] = metadata
            kwargs["extra_body"] = extra_body

        return await self._completions.create(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class ZorveusOpenAI(_OpenAI):
    """Zorveus wrapper around official OpenAI client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        external_user_id: Optional[str] = None,
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

        self.chat.completions = _ZorveusCompletionsWrapper(self.chat.completions, external_user_id)  # type: ignore


class AsyncZorveusOpenAI(_AsyncOpenAI):
    """Async Zorveus wrapper around official OpenAI async client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        external_user_id: Optional[str] = None,
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

        self.chat.completions = _AsyncZorveusCompletionsWrapper(self.chat.completions, external_user_id)  # type: ignore
