"""Shared stub stream used by Foundry/Databricks providers when creds are missing.

Role-aware and provider-aware so the orchestrator's convergence detector can
still fire offline, AND so the offline transcript reads like an actual debate
(challenge → data → counter → concession → agreement).

Provider-aware: a model-swap mid-debate changes the voice noticeably.
"""

from __future__ import annotations

import asyncio
import random
import re
from typing import AsyncIterator, Sequence

from .base import ChatMessage

_ROLE_RE = re.compile(r"You are\s+\w+,\s*(CEO|CFO|CMO|CTO|Legal)", re.IGNORECASE)

# Each line is one turn's worth of text. Multiple variants per (provider, role)
# so successive rounds don't repeat verbatim. CEO lines must contain "decision"
# (lowercase substring) so convergence.summary fires.
_CANNED: dict[str, dict[str, list[str]]] = {
    "foundry": {
        "CEO": [
            "Team, I want to hear the strongest cases for and against the Singapore pilot. "
            "Vikram, walk us through the numbers — I want CAC, payback, and the dilution math. "
            "Priya, brand-awareness gap and how long seeding takes. Arjun, infra readiness. "
            "Meera, the compliance picture. Let's stay evidence-driven.",
            "Decision: we approve a capped Singapore pilot at $1.5M with DPAs locked first "
            "and a $1M ARR checkpoint before any further expansion. Strong support across "
            "the table — I endorse the plan and we proceed. Compliant, focused, and growth-positive.",
        ],
        "CMO": [
            "I support the pilot, but I want to push back on timing. Brand awareness in Singapore "
            "is only 11 percent versus 64 percent at home — that is a real gap. Six months of "
            "seeded content and partner channels gives us a favorable runway and a strong launch.",
            "Agree on the cap. We endorse a phased seeding plan; growth comes from compounding "
            "awareness, not just paid acquisition.",
        ],
        "CTO": [
            "From a platform standpoint we are ready and safe. Singapore region p99 sits at "
            "142 milliseconds with 2.4x headroom. No blockers, no scaling concerns. "
            "I support the pilot — we can absorb the load without any compliant gap.",
            "I endorse the plan. Infra is strong and compliant; we are good to proceed.",
        ],
    },
    "databricks": {
        "CFO": [
            "Let me ground this in numbers. SEA Q1 pipeline is a favorable $4.2M opportunity. "
            "Yes, customer-acquisition cost runs higher than India — roughly 2.3x — but at a $1.5M "
            "cap we preserve runway and stay in a strong growth posture. I agree with a capped "
            "pilot; I would not endorse an uncapped build-out.",
            "I support the plan. Caps protect us; the upside on a favorable SEA opportunity "
            "is worth the spend. We endorse.",
        ],
        "Legal": [
            "I support the pilot, conditional on DPAs. Singapore PDPA and Malaysia PDPA require "
            "localized data-processing agreements before any pilot launch. With DPAs in place "
            "we are compliant and safe; without them we are exposed. I endorse the cap and "
            "the DPA-first sequencing — that is the favorable path.",
            "I agree we proceed. DPAs first, then launch — that keeps us compliant and strong.",
        ],
    },
}

# Fallbacks if a provider swap puts (provider, role) into a combo we did not pre-seed.
# Example: Legal swapped to foundry:gpt-5 — we still need a Legal line.
_GENERIC: dict[str, list[str]] = {
    "CEO": [
        "Decision: we endorse the capped pilot, DPAs locked first, $1M ARR checkpoint. "
        "Strong support across the table; we proceed and stay compliant.",
    ],
    "CFO": [
        "I support the capped pilot. Numbers are favorable at this spend; growth stays strong "
        "and I endorse the plan.",
    ],
    "CMO": [
        "I agree we proceed. Singapore is a favorable brand opportunity; I support the seeding plan.",
    ],
    "CTO": [
        "Infra is strong and safe — I support the pilot. No platform blocker; I endorse it.",
    ],
    "Legal": [
        "With DPAs in place we are compliant; I support and endorse the pilot.",
    ],
}


def _detect_role(messages: Sequence[ChatMessage]) -> str:
    for m in messages:
        if m.get("role") == "system":
            match = _ROLE_RE.search(m.get("content", ""))
            if match:
                return match.group(1)
    return ""


def _count_prior_assistant_turns(messages: Sequence[ChatMessage]) -> int:
    return sum(1 for m in messages if m.get("role") == "assistant")


def _pick(provider: str, role: str, idx: int) -> str:
    variants = _CANNED.get(provider, {}).get(role) or _GENERIC.get(role) or []
    if not variants:
        return f"[{provider}:{role.lower()} stub] no canned line."
    return variants[min(idx, len(variants) - 1)]


async def stub_role_stream(
    provider: str,
    endpoint: str,
    messages: Sequence[ChatMessage],
) -> AsyncIterator[str]:
    role = _detect_role(messages)
    if not role:
        yield f"[{provider}:{endpoint} stub] no live creds; stub stream."
        return
    round_idx = _count_prior_assistant_turns(messages)
    text = _pick(provider, role, round_idx)
    # Stream word-by-word with light jitter so the UI feels alive.
    for word in text.split(" "):
        await asyncio.sleep(0.02 + random.uniform(0, 0.015))
        yield word + " "
