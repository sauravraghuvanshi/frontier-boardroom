"""Provider base contract.

All providers expose:
  async stream_chat(messages, **kwargs) -> AsyncIterator[str]
  async probe() -> dict
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Sequence


class ChatMessage(dict):
    """OpenAI-compatible {'role': 'system|user|assistant', 'content': str}."""


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def stream_chat(
        self,
        endpoint: str,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> AsyncIterator[str]:
        """Yield text tokens as they arrive."""
        raise NotImplementedError
        yield ""  # pragma: no cover  (makes mypy treat as async generator)

    @abstractmethod
    async def probe(self, endpoint: str) -> dict:
        """Smoke test endpoint reachability — returns {provider, endpoint, ok, latency_ms?, error?}."""
