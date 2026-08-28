import json
from typing import Iterator, AsyncIterator, TypeVar, Type, Optional
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

def parse_sse_line(line: str) -> Optional[str]:
    """Parses single SSE line, returning data payload or None."""
    line = line.strip()
    if not line or line.startswith(":"):
        return None
    if line.startswith("data: "):
        return line[6:]
    if line == "data:":
        return ""
    return None

def parse_sync_sse_stream(lines: Iterator[str], model_cls: Type[T]) -> Iterator[T]:
    """Parses synchronous SSE lines into Pydantic model instances."""
    for raw_line in lines:
        data = parse_sse_line(raw_line)
        if data is None:
            continue
        if data == "[DONE]":
            break
        payload = json.loads(data)
        yield model_cls.model_validate(payload)

async def parse_async_sse_stream(lines: AsyncIterator[str], model_cls: Type[T]) -> AsyncIterator[T]:
    """Parses asynchronous SSE lines into Pydantic model instances."""
    async for raw_line in lines:
        data = parse_sse_line(raw_line)
        if data is None:
            continue
        if data == "[DONE]":
            break
        payload = json.loads(data)
        yield model_cls.model_validate(payload)
