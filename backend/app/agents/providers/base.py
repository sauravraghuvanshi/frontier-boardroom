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


def consolidate_messages(messages: Sequence["ChatMessage"]) -> list[dict]:
    """Merge consecutive same-role messages into one.

    Anthropic on Databricks Mosaic AI rejects/hangs on non-alternating
    user/assistant sequences. The boardroom orchestrator appends a peer's
    turn as a `user` message to every other agent's history, then
    `base_agent.think()` appends the per-turn grounded_turn as another
    `user` message — so by turn 2 the next speaker has 2-3 consecutive
    user messages. Collapse them with `\\n\\n` separators before sending.
    """
    out: list[dict] = []
    for m in messages:
        role = m.get("role", "user")
        content = (m.get("content") or "")
        if out and out[-1]["role"] == role:
            out[-1]["content"] = f"{out[-1]['content']}\n\n{content}"
        else:
            out.append({"role": role, "content": content})
    return out


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
