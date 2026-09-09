from typing import Optional, Dict, Any, List
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.provider_credentials import (
    ProviderCredentialResponse,
    ProviderCredentialListResponse,
    RotateProviderCredentialResponse,
    UpdateProviderCredentialRoutingPriorityResponse,
    DeleteProviderCredentialResponse,
    GrantProviderCredentialResponse,
    ProviderCatalogResponse,
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
            "api_key": api_key,
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

    def get(self, provider_credential_id: str) -> ProviderCredentialResponse:
        return self._transport.get(
            f"/provider-credentials/org-programmatic/{provider_credential_id}",
            response_model=ProviderCredentialResponse,
        )

    def list_providers(self) -> ProviderCatalogResponse:
        return self._transport.get(
            "/provider-credentials/providers", response_model=ProviderCatalogResponse
        )

    def rotate(
        self,
        *,
        provider_credential_id: str,
        api_key: str,
        secret_kind: str = "api_key",
    ) -> RotateProviderCredentialResponse:
        """Rotates the secret key of an existing provider credential."""
        payload = {
            "secret": api_key,
            "api_key": api_key,
            "secret_kind": secret_kind,
        }
        return self._transport.post(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/rotate",
            json_data=payload,
            response_model=RotateProviderCredentialResponse,
        )

    def update_routing_priority(
        self,
        *,
        provider_credential_id: str,
        routing_priority: int,
    ) -> UpdateProviderCredentialRoutingPriorityResponse:
        """Updates the routing priority for a provider credential."""
        payload = {
            "routing_priority": routing_priority,
        }
        return self._transport.patch(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/routing-priority",
            json_data=payload,
            response_model=UpdateProviderCredentialRoutingPriorityResponse,
        )

    def delete(
        self,
        *,
        provider_credential_id: str,
    ) -> DeleteProviderCredentialResponse:
        """Deletes a provider credential."""
        return self._transport.delete(
            f"/provider-credentials/org-programmatic/{provider_credential_id}",
            response_model=DeleteProviderCredentialResponse,
        )

    def grant_to_app_connection(
        self,
        *,
        provider_credential_id: str,
        app_connection_id: str,
    ) -> GrantProviderCredentialResponse:
        """Grants a provider credential to an app connection."""
        payload = {
            "app_connection_id": app_connection_id,
        }
        return self._transport.post(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/app-connections",
            json_data=payload,
            response_model=GrantProviderCredentialResponse,
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

    async def get(self, provider_credential_id: str) -> ProviderCredentialResponse:
        return await self._transport.get(
            f"/provider-credentials/org-programmatic/{provider_credential_id}",
            response_model=ProviderCredentialResponse,
        )

    async def list_providers(self) -> ProviderCatalogResponse:
        return await self._transport.get(
            "/provider-credentials/providers", response_model=ProviderCatalogResponse
        )

    async def rotate(
        self,
        *,
        provider_credential_id: str,
        api_key: str,
        secret_kind: str = "api_key",
    ) -> RotateProviderCredentialResponse:
        """Rotates the secret key of an existing provider credential asynchronously."""
        payload = {
            "secret": api_key,
            "secret_kind": secret_kind,
        }
        return await self._transport.post(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/rotate",
            json_data=payload,
            response_model=RotateProviderCredentialResponse,
        )

    async def update_routing_priority(
        self,
        *,
        provider_credential_id: str,
        routing_priority: int,
    ) -> UpdateProviderCredentialRoutingPriorityResponse:
        """Updates the routing priority for a provider credential asynchronously."""
        payload = {
            "routing_priority": routing_priority,
        }
        return await self._transport.patch(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/routing-priority",
            json_data=payload,
            response_model=UpdateProviderCredentialRoutingPriorityResponse,
        )

    async def delete(
        self,
        *,
        provider_credential_id: str,
    ) -> DeleteProviderCredentialResponse:
        """Deletes a provider credential asynchronously."""
        return await self._transport.delete(
            f"/provider-credentials/org-programmatic/{provider_credential_id}",
            response_model=DeleteProviderCredentialResponse,
        )

    async def grant_to_app_connection(
        self,
        *,
        provider_credential_id: str,
        app_connection_id: str,
    ) -> GrantProviderCredentialResponse:
        """Grants a provider credential to an app connection asynchronously."""
        payload = {
            "app_connection_id": app_connection_id,
        }
        return await self._transport.post(
            f"/provider-credentials/org-programmatic/{provider_credential_id}/app-connections",
            json_data=payload,
            response_model=GrantProviderCredentialResponse,
        )

