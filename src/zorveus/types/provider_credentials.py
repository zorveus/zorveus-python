from typing import List, Optional
from pydantic import BaseModel

class ProviderCredential(BaseModel):
    id: str
    app_id: str
    provider: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProviderCredentialResponse(BaseModel):
    provider_credential: ProviderCredential

class ProviderCredentialListResponse(BaseModel):
    data: List[ProviderCredential]
