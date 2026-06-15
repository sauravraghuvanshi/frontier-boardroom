"""Prep mode delegation orchestrator.

Handles CEO→{CFO|CMO|CTO|Legal} agent delegation within a prep session. When
CEO types `@CTO ...` in prep, this module:

1. Validates hierarchy (only CEO can delegate).
2. Retrieves persona-filtered grounding for the delegated agent.
3. Streams the delegated agent's full reply as a visible bubble in the chat
   thread (turn_start → tokens → turn_end with `agent: to_role`).
4. Returns the streamed text so the caller can inject it into the originating
   agent's grounded prompt for synthesis.

Prior to 2026-06-15c this module did silent retrieval only — no visible bubble
for the delegated agent — which made the delegation indistinguishable from a
plain CEO turn from the user's perspective.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from ..agents.registry import PREP_REGISTRY
from ..grounding.foundry_iq_client import retrieve
from ..orchestrator.briefing import build_briefing
from ..telemetry import agent_event, get_logger

log = get_logger("prep_delegate")

# Hierarchy: only CEO can delegate.
_DELEGATION_HIERARCHY = {
    "CEO": {"CFO", "CMO", "CTO", "Legal"},
    "CFO": set(),
    "CMO": set(),
    "CTO": set(),
    "Legal": set(),
}


class _FenceStripper:
    """Strip a leading ```markdown / ``` fence and the matching trailing ```
    from a token stream. CTO (`foundry:gpt-4.1`) and CMO (`foundry:gpt-4o`)
    routinely wrap entire replies in a code fence even when told not to;
    without this the body renders as a literal block and asterisks leak.
    """

    def __init__(self) -> None:
        self._lead_buf: list[str] = []
        self._lead_done = False
        self._tail = ""

    def feed(self, tok: str) -> str:
        if not self._lead_done:
            self._lead_buf.append(tok)
            joined = "".join(self._lead_buf)
            stripped = joined.lstrip()
            if stripped.startswith("```"):
                nl = stripped.find("\n")
                if nl == -1:
                    return ""
                rest = stripped[nl + 1:]
                self._lead_done = True
                self._lead_buf = []
                return self._holdback(rest)
            if stripped and not stripped.startswith("`"):
                self._lead_done = True
                out = joined
                self._lead_buf = []
                return self._holdback(out)
            return ""
        return self._holdback(tok)

    def _holdback(self, s: str) -> str:
        combined = self._tail + s
        if len(combined) <= 8:
            self._tail = combined
            return ""
        emit = combined[:-8]
        self._tail = combined[-8:]
        return emit

    def flush(self) -> str:
        if not self._lead_done:
            out = "".join(self._lead_buf)
            self._lead_buf = []
            self._lead_done = True
        else:
            out = self._tail
        self._tail = ""
        rstripped = out.rstrip()
        if rstripped.endswith("```"):
            return rstripped[:-3].rstrip()
        return out


async def stream_delegate_response(
    *,
    from_role: str,
    to_role: str,
    question: str,
    emit: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    """Stream a delegated agent's full response as a visible bubble.

    Emits citation events, turn_start, streaming tokens, and turn_end for
    `to_role` so the human sees a full bubble in the chat thread. The complete
    streamed text is captured and returned so the caller can inject it into
    the originating agent's grounded prompt.

    Args:
        from_role: "CEO" (only role currently allowed to delegate).
        to_role: "CFO" | "CMO" | "CTO" | "Legal".
        question: User's question (mentions already stripped by the caller).
        emit: Async callable to emit WS events.

    Returns:
        {
            "response": full streamed text from to_role,
            "citations": [citation dicts],
            "briefing_block": full streamed text for caller-side prompt injection
        }

    Raises:
        ValueError: if hierarchy violation or unknown role.
    """
    t0 = time.perf_counter()

    allowed = _DELEGATION_HIERARCHY.get(from_role, set())
    if to_role not in allowed:
        raise ValueError(
            f"Delegation not allowed: {from_role} cannot call {to_role}. "
            f"Only: {allowed or 'no one'}"
        )
    if to_role not in PREP_REGISTRY:
        raise ValueError(f"Unknown agent role: {to_role}")

    agent = PREP_REGISTRY[to_role]

    await emit({
        "type": "delegation_start",
        "from_role": from_role,
        "to_role": to_role,
        "question": question,
        "timestamp": time.time(),
    })

    # Persona-filtered RAG for the delegated agent.
    citations = await retrieve(query=question, persona=to_role, k=3)
    for c in citations:
        await emit({
            "type": "citation",
            "agent": to_role,
            "source_uri": c.get("source_uri", ""),
            "snippet": c.get("snippet", ""),
            "confidence": c.get("confidence", 0.5),
            "hops": c.get("hops", 1),
        })

    briefing_block = build_briefing(citations)
    grounded_turn = (
        f"{briefing_block}\n\n"
        f"You are being consulted by the {from_role} during prep for an "
        f"upcoming board meeting. Answer this specific question from your "
        f"domain perspective, using the briefing above.\n\n"
        f"{from_role} asked: {question}\n\n"
        "Respond directly in your persona. Cite source filenames inline. "
        "If a number you would normally cite is not in the briefing above, "
        "say 'I don't have that figure in our briefing materials.' "
        "Do NOT think out loud, do NOT narrate your reasoning, do NOT "
        "preface with 'we need to' or 'let me' — speak directly as the executive."
    )

    await emit({
        "type": "turn_start",
        "agent": to_role,
        "model": agent.model_ref,
        "timestamp": time.time(),
        "delegated_from": from_role,
    })
    agent_event(
        to_role,
        "delegate_turn_start",
        model=agent.model_ref,
        from_role=from_role,
    )

    buffer: list[str] = []
    tokens = 0
    stripper = _FenceStripper()
    try:
        async for tok in agent.think(grounded_turn, history=[]):
            clean = stripper.feed(tok)
            if clean:
                buffer.append(clean)
                tokens += 1
                await emit({"type": "token", "agent": to_role, "text": clean})
    except Exception as e:  # noqa: BLE001
        err_msg = f"[{to_role} provider error: {type(e).__name__}: {e}]"
        log.error("delegate_turn_failed", role=to_role, error=str(e))
        await emit({"type": "token", "agent": to_role, "text": err_msg})
        buffer.append(err_msg)

    tail = stripper.flush()
    if tail:
        buffer.append(tail)
        tokens += 1
        await emit({"type": "token", "agent": to_role, "text": tail})

    full_text = "".join(buffer).strip() or f"[{to_role} produced no tokens]"

    duration_ms = int((time.perf_counter() - t0) * 1000)
    await emit({
        "type": "turn_end",
        "agent": to_role,
        "duration_ms": duration_ms,
        "tokens": tokens,
    })
    agent_event(
        to_role,
        "delegate_turn_end",
        duration_ms=duration_ms,
        tokens=tokens,
    )

    await emit({
        "type": "delegation_end",
        "to_role": to_role,
        "citation_count": len(citations),
        "timestamp": time.time(),
    })

    log.info(
        "delegation_visible: %s→%s, %d citations, %d tokens, %dms",
        from_role,
        to_role,
        len(citations),
        tokens,
        duration_ms,
    )

    return {
        "response": full_text,
        "citations": citations,
        "briefing_block": full_text,
    }
