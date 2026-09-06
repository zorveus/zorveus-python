from typing import Optional, Dict, Any, List
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.provider_credentials import (
    ProviderCredentialResponse,
    ProviderCredentialListResponse,
)

class ProviderCredentialsResource:
    """Synchronous provider credentials management resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    def create(
        self,
        *,
        provider: str,
        api_key: str,
        credential_name: Optional[str] = None,
        secret_kind: str = "api_key",
        routing_mode: str = "auto_resolve",
        routing_priority: int = 100,
        app_id: Optional[str] = None,
        default_model_policy: Optional[List[str]] = None,
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> ProviderCredentialResponse:
        """Registers a provider credential with a service key."""
        name = credential_name or f"{provider}_credential"
        payload: Dict[str, Any] = {
            "provider": provider,
            "credential_name": name,
            "secret": api_key,
            "secret_kind": secret_kind,
            "routing_mode": routing_mode,
            "routing_priority": routing_priority,
        }
        if default_model_policy is not None:
            payload["default_model_policy"] = default_model_policy
        if provider_config is not None:
            payload["provider_config"] = provider_config

        return self._transport.post(
            "/provider-credentials/org-programmatic",
            json_data=payload,
            response_model=ProviderCredentialResponse,
        )

    def list(self, *, app_id: Optional[str] = None) -> ProviderCredentialListResponse:
        """Lists registered provider credentials for the organization."""
        params: Dict[str, Any] = {}
        if app_id is not None:
            params["app_id"] = app_id
        return self._transport.get(
            "/provider-credentials/org-programmatic",
            params=params or None,
            response_model=ProviderCredentialListResponse,
        )


class AsyncProviderCredentialsResource:
    """Asynchronous provider credentials management resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    async def create(
        self,
        *,
        provider: str,
        api_key: str,
        credential_name: Optional[str] = None,
        secret_kind: str = "api_key",
        routing_mode: str = "auto_resolve",
        routing_priority: int = 100,
        app_id: Optional[str] = None,
        default_model_policy: Optional[List[str]] = None,
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> ProviderCredentialResponse:
        """Registers a provider credential asynchronously with a service key."""
        name = credential_name or f"{provider}_credential"
        payload: Dict[str, Any] = {
            "provider": provider,
            "credential_name": name,
            "secret": api_key,
            "secret_kind": secret_kind,
            "routing_mode": routing_mode,
            "routing_priority": routing_priority,
        }
        if default_model_policy is not None:
            payload["default_model_policy"] = default_model_policy
        if provider_config is not None:
            payload["provider_config"] = provider_config

        return await self._transport.post(
            "/provider-credentials/org-programmatic",
            json_data=payload,
            response_model=ProviderCredentialResponse,
        )

    async def list(self, *, app_id: Optional[str] = None) -> ProviderCredentialListResponse:
        """Lists registered provider credentials asynchronously for the organization."""
        params: Dict[str, Any] = {}
        if app_id is not None:
            params["app_id"] = app_id
        return await self._transport.get(
            "/provider-credentials/org-programmatic",
            params=params or None,
            response_model=ProviderCredentialListResponse,
        )

