from typing import List, Optional
from pydantic import BaseModel

class ModelObject(BaseModel):
    id: str
    object: str = "model"
    created: Optional[int] = None
    owned_by: str = "zorveus"

class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelObject]
