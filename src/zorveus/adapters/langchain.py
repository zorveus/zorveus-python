import os
from typing import Optional, Dict, Any

try:
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    ChatOpenAI = object  # type: ignore


class ChatZorveus(ChatOpenAI):
    """Zorveus LangChain ChatOpenAI adapter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        gateway_url: Optional[str] = None,
        external_user_id: Optional[str] = None,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        user_metadata: Optional[Dict[str, Any]] = None,
        model: str = "openai/gpt-4.1-mini",
        model_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        if not HAS_LANGCHAIN:
            raise ImportError(
                "The 'langchain-openai' package is required to use ChatZorveus. "
                "Install it with 'pip install zorveus[langchain]'."
            )

        key = api_key or os.environ.get("ZORVEUS_INFERENCE_KEY")
        if not key:
            raise ValueError("API key is required. Pass api_key or set ZORVEUS_INFERENCE_KEY.")

        base_url = gateway_url or os.environ.get("ZORVEUS_GATEWAY_URL", "https://api.zorveus.com/v1")

        m_kwargs = dict(model_kwargs or {})
        extra_body = dict(m_kwargs.get("extra_body") or {})
        metadata = dict(extra_body.get("metadata") or {})

        if external_user_id and "external_user_id" not in metadata:
            metadata["external_user_id"] = external_user_id

        product_user = dict(metadata.get("product_user") or {})
        if display_name and "display_name" not in product_user:
            product_user["display_name"] = display_name
        if email and "email" not in product_user:
            product_user["email"] = email
        if user_metadata and "metadata" not in product_user:
            product_user["metadata"] = user_metadata

        if product_user:
            metadata["product_user"] = product_user

        if metadata:
            extra_body["metadata"] = metadata
            m_kwargs["extra_body"] = extra_body

        super().__init__(
            api_key=key,
            base_url=base_url,
            model=model,
            model_kwargs=m_kwargs,
            **kwargs,
        )
