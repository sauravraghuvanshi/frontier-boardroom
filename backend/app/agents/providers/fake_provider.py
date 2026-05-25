"""Fake provider — replays canned text so /dev/fake-debate always works."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Sequence

from .base import BaseProvider, ChatMessage

_CANNED = {
    "CEO": "Let's align on the SEA expansion question and weigh capital, brand, and risk.",
    "CFO": "Numbers: SEA Q1 pipeline is $4.2M with CAC of $736 vs $320 in India — twice the burn.",
    "CMO": "Brand awareness in SEA is 11 percent vs 64 percent at home; we need 6 months of seeding.",
    "CTO": "Infra-wise, our stack runs in Singapore region today; latency budget is fine.",
    "Legal": "DPDP-equivalents in SG and MY require localized DPAs before any pilot launch.",
}


class FakeProvider(BaseProvider):
    name = "fake"

    async def stream_chat(
        self,
        endpoint: str,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> AsyncIterator[str]:
        role_hint = endpoint.upper()
        text = _CANNED.get(role_hint, f"[fake:{endpoint}] stub reply.")
        for word in text.split(" "):
            await asyncio.sleep(0.02)
            yield word + " "

    async def probe(self, endpoint: str) -> dict:
        return {"provider": self.name, "endpoint": endpoint, "ok": True, "latency_ms": 1}
