"""BaseAgent — wraps router + persona + tools (§6.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator, Callable, Sequence

from .model_router import stream_chat
from .providers.base import ChatMessage


@dataclass
class AgentPersona:
    role: str  # "CEO" | "CFO" | "CMO" | "CTO" | "Legal"
    name: str
    title: str
    voice: str  # Azure Speech voice name
    avatar: str  # path to .glb
    system_prompt: str
    model_ref: str  # "<provider>:<endpoint>" — mutable; swapped via /agent/{role}/swap-model
    tools: list[str] = field(default_factory=list)  # e.g. ["foundry_iq.retrieve"]
    temperature: float = 0.4


class BaseAgent:
    def __init__(self, persona: AgentPersona) -> None:
        self.persona = persona

    @property
    def role(self) -> str:
        return self.persona.role

    @property
    def model_ref(self) -> str:
        return self.persona.model_ref

    @model_ref.setter
    def model_ref(self, ref: str) -> None:
        self.persona.model_ref = ref

    async def think(
        self,
        user_turn: str,
        *,
        history: Sequence[ChatMessage] | None = None,
        on_token: Callable[[str], None] | None = None,
    ) -> AsyncIterator[str]:
        msgs: list[ChatMessage] = [ChatMessage(role="system", content=self.persona.system_prompt)]
        if history:
            msgs.extend(history)
        msgs.append(ChatMessage(role="user", content=user_turn))
        async for tok in stream_chat(
            self.persona.model_ref, msgs, temperature=self.persona.temperature
        ):
            if on_token:
                on_token(tok)
            yield tok
