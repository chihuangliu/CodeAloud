import asyncio
import os
import random
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


_MOCK_RESPONSES = [
    "That's an interesting approach! Let's talk about **time complexity**.\n\n"
    "- What's the Big-O of your current solution?\n"
    "- Can you think of a way to bring it down to `O(n)`?",
    "I see what you're going for. Have you considered these **edge cases**?\n\n"
    "1. Empty input `[]`\n"
    "2. A single element `[1]`\n"
    "3. Negative numbers like `[-3, -1, 0]`\n\n"
    "Try running through one of them mentally.",
    "Good start. Before writing more code, walk me through your **thought process**:\n\n"
    "> What data structure are you using and *why*?\n\n"
    "For example, a `dict` gives you `O(1)` lookup — is that what you need here?",
    "Hmm, that might work for small inputs, but think about **scalability**.\n\n"
    "```\n"
    "n = 10      → 100 ops    ✓\n"
    "n = 10,000  → 100,000,000 ops  ✗\n"
    "```\n\n"
    "Your nested loop is `O(n²)`. Can you do better?",
    "Nice! Now let's **stress-test** your solution. Try to find an input that breaks it:\n\n"
    "- What if all elements are the same?\n"
    "- What about `Integer.MAX_VALUE` overflow?\n"
    "- What about an *already sorted* array?\n\n"
    "Pick one and trace through your code.",
    "Let's take a step back. Can you explain the problem **in your own words**?\n\n"
    "A good framework:\n"
    "1. **Input** — what are you given?\n"
    "2. **Output** — what should you return?\n"
    "3. **Constraints** — any limits on size or values?",
    "I notice you're using a nested loop here. Consider the **two-pointer** technique:\n\n"
    "```python\n"
    "left, right = 0, len(arr) - 1\n"
    "while left < right:\n"
    "    # adjust pointers based on condition\n"
    "```\n\n"
    "This brings it down to a **single pass** — `O(n)` time.",
    "That's one way to do it. What if I told you there's a `HashMap` solution?\n\n"
    "**Hint:** instead of searching for the complement with a loop, "
    "store what you've *already seen*:\n\n"
    "```python\n"
    "seen = {}\n"
    "for num in nums:\n"
    "    complement = target - num\n"
    "    if complement in seen:\n"
    "        # found it!\n"
    "```\n\n"
    "What's the time complexity of this approach?",
    "⏰ We're running a bit low on time. Let's wrap up:\n\n"
    "1. **Finish** your current approach — even pseudocode is fine\n"
    "2. **Explain** what you'd optimize with more time\n"
    "3. **Mention** any alternative algorithms you considered\n\n"
    "Don't worry about perfect code — I want to see your *thinking*.",
    "Interesting choice of algorithm. Let's compare the **tradeoffs**:\n\n"
    "| Approach | Time | Space |\n"
    "|----------|------|-------|\n"
    "| Brute force | `O(n²)` | `O(1)` |\n"
    "| Hash map | `O(n)` | `O(n)` |\n"
    "| Sort + two-pointer | `O(n log n)` | `O(1)` |\n\n"
    "Which tradeoff makes sense for your use case?",
]


class MockClient:
    async def stream(self, messages: list[dict], system: str) -> AsyncIterator[str]:
        response = random.choice(_MOCK_RESPONSES)
        for char in response:
            yield char
            await asyncio.sleep(0.02)


def get_llm_client() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "mock":
        return MockClient()
    if provider == "anthropic":
        return AnthropicClient()
    return OpenAIClient()
