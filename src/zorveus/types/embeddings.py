from typing import List, Union

from pydantic import BaseModel


EmbeddingInput = Union[str, List[str], List[int], List[List[int]]]


class EmbeddingData(BaseModel):
    index: int
    object: str = "embedding"
    embedding: List[float]


class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int


class EmbeddingCreateResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: EmbeddingUsage