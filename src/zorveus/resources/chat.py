from typing import Optional, List, Dict, Any, Union, Iterator, AsyncIterator, overload, Literal
from zorveus.http.transport import SyncHTTPTransport
from zorveus.http.async_transport import AsyncHTTPTransport
from zorveus.types.chat import (
    ChatMessage,
    ChatCompletionResponse,
    ChatCompletionChunk,
)

class CompletionsResource:
    """Synchronous chat completions resource."""

    def __init__(self, transport: SyncHTTPTransport) -> None:
        self._transport = transport

    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: Literal[True],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> Iterator[ChatCompletionChunk]: ...

    @overload
    def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> ChatCompletionResponse: ...

    def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> Union[ChatCompletionResponse, Iterator[ChatCompletionChunk]]:
        """Creates a chat completion or stream."""
        formatted_messages = [
            msg.model_dump(exclude_unset=True) if isinstance(msg, ChatMessage) else msg
            for msg in messages
        ]

        payload: Dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "stream": stream,
            **extra_kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if zorveus_metadata is not None:
            payload["zorveus_metadata"] = zorveus_metadata

        if stream:
            return self._transport.stream(
                "POST",
                "/chat/completions",
                json_data=payload,
                response_model=ChatCompletionChunk,
            )

        return self._transport.post(
            "/chat/completions",
            json_data=payload,
            response_model=ChatCompletionResponse,
        )


class AsyncCompletionsResource:
    """Asynchronous chat completions resource."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: Literal[True],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> AsyncIterator[ChatCompletionChunk]: ...

    @overload
    async def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: Literal[False] = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> ChatCompletionResponse: ...

    async def create(
        self,
        *,
        model: str,
        messages: List[Union[ChatMessage, Dict[str, Any]]],
        stream: bool = False,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        zorveus_metadata: Optional[Dict[str, Any]] = None,
        **extra_kwargs: Any,
    ) -> Union[ChatCompletionResponse, AsyncIterator[ChatCompletionChunk]]:
        """Creates a chat completion or stream asynchronously."""
        formatted_messages = [
            msg.model_dump(exclude_unset=True) if isinstance(msg, ChatMessage) else msg
            for msg in messages
        ]

        payload: Dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "stream": stream,
            **extra_kwargs,
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if zorveus_metadata is not None:
            payload["zorveus_metadata"] = zorveus_metadata

        if stream:
            return await self._transport.stream(
                "POST",
                "/chat/completions",
                json_data=payload,
                response_model=ChatCompletionChunk,
            )

        return await self._transport.post(
            "/chat/completions",
            json_data=payload,
            response_model=ChatCompletionResponse,
        )


class ChatResource:
    def __init__(self, transport: SyncHTTPTransport) -> None:
        self.completions = CompletionsResource(transport)


class AsyncChatResource:
    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self.completions = AsyncCompletionsResource(transport)
