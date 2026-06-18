import os
from typing import AsyncIterator, Protocol, runtime_checkable

import anthropic
import openai


@runtime_checkable
class LLMClient(Protocol):
    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]: ...


class AnthropicClient:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=os.environ["LLM_API_KEY"])
        self._model = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")

    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=1024,
            system=system,
            cache_control={"type": "ephemeral"},
            messages=messages,
        ) as s:
            async for text in s.text_stream:
                yield text


class OpenAIClient:
    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(
            base_url=os.environ.get("LLM_BASE_URL"),
            api_key=os.environ.get("LLM_API_KEY", ""),
        )
        self._model = os.environ.get("LLM_MODEL", "gpt-4o")

    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system}] + messages
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=full_messages,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


def get_llm_client() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        return AnthropicClient()
    return OpenAIClient()
