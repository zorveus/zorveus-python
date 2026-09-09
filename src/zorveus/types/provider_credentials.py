from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderCredentialResponse(BaseModel):
    provider_credential_id: Optional[str] = None
    id: Optional[str] = None
    org_id: Optional[str] = None
    app_id: Optional[str] = None
    provider: str
    credential_name: Optional[str] = None
    status: Optional[str] = "active"
    routing_health: Optional[str] = "ready"
    routing_mode: Optional[str] = "auto_resolve"
    routing_priority: Optional[int] = 100
    default_model_policy: Optional[List[str]] = Field(default_factory=list)
    provider_config: Optional[Dict[str, Any]] = None
    active_secret_version_id: Optional[str] = None
    secret_fingerprint: Optional[str] = None
    last_validated_at: Optional[str] = None
    last_used_at: Optional[str] = None
    last_quota_exhausted_at: Optional[str] = None
    cooldown_expires_at: Optional[str] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.provider_credential_id:
            self.id = self.provider_credential_id
        elif not self.provider_credential_id and self.id:
            self.provider_credential_id = self.id

    @property
    def provider_credential(self) -> "ProviderCredentialResponse":
        return self


class ProviderCredentialListResponse(BaseModel):
    provider_credentials: List[ProviderCredentialResponse] = Field(default_factory=list)
    data: List[ProviderCredentialResponse] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        if not self.data and self.provider_credentials:
            self.data = self.provider_credentials
        elif not self.provider_credentials and self.data:
            self.provider_credentials = self.data

    @property
    def credentials(self) -> List[ProviderCredentialResponse]:
        return self.provider_credentials


class RotateProviderCredentialResponse(BaseModel):
    provider_credential: ProviderCredentialResponse
    rotated: bool = True


class UpdateProviderCredentialRoutingPriorityResponse(BaseModel):
    provider_credential: ProviderCredentialResponse


class DeleteProviderCredentialResponse(BaseModel):
    provider_credential: ProviderCredentialResponse
    deleted: bool = True
    revoked_grant_count: int = 0
    retired_version_count: int = 0


class GrantProviderCredentialResponse(BaseModel):
    grant: Dict[str, Any]


class ProviderInfo(BaseModel):
    provider: str
    label: Optional[str] = None
    display_name: Optional[str] = None
    supported_auth_types: List[str] = Field(default_factory=list)
    docs_url: Optional[str] = None
    supports_auto_resolve: Optional[bool] = None
    supports_manual: Optional[bool] = None

    model_config = {"extra": "allow"}

    def model_post_init(self, __context: Any) -> None:
        if not self.display_name:
            self.display_name = self.label or self.provider


class ProviderCatalogResponse(BaseModel):
    providers: List[ProviderInfo] = Field(default_factory=list)


ProviderCredential = ProviderCredentialResponse


