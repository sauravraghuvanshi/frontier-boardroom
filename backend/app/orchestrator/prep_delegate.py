"""Prep mode delegation orchestrator.

Handles CEO→CTO (and future CEO→CFO/CMO/Legal) agent delegation within a prep session.
When CEO types @CTO within prep, this module:
1. Validates hierarchy (only CEO can delegate)
2. Retrieves CTO-exclusive data
3. Streams CTO response through the same WS connection
4. Returns briefing block to inject into CEO's context
"""

from __future__ import annotations

from typing import Any, Callable

from ..agents.registry import PREP_REGISTRY
from ..grounding.foundry_iq_client import retrieve
from ..orchestrator.briefing import build_briefing
from ..telemetry import get_logger

log = get_logger("prep_delegate")

# Hierarchy: only CEO can delegate to others
_DELEGATION_HIERARCHY = {
    "CEO": {"CFO", "CMO", "CTO", "Legal"},
    "CFO": set(),
    "CMO": set(),
    "CTO": set(),
    "Legal": set(),
}


async def stream_delegate_response(
    *,
    from_role: str,
    to_role: str,
    question: str,
    emit: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    """Retrieve delegated agent briefing context within a prep session.

    Args:
        from_role: "CEO" (only role allowed to delegate)
        to_role: "CTO" | "CFO" | "CMO" | "Legal" (must be in DELEGATION_HIERARCHY[from_role])
        question: User's question to delegate
        emit: Async callable to emit WS events (used for delegation markers only)

    Returns:
        {
            "response": briefing_block,
            "citations": [citation dicts],
            "briefing_block": formatted briefing text for injection
        }

    Raises:
        ValueError: if hierarchy violation or invalid role
    """
    t0 = __import__("time").perf_counter()

    # Validate hierarchy
    allowed = _DELEGATION_HIERARCHY.get(from_role, set())
    if to_role not in allowed:
        raise ValueError(
            f"Delegation not allowed: {from_role} cannot call {to_role}. "
            f"Only: {allowed or 'no one'}"
        )

    # Validate to_role exists in registry
    if to_role not in PREP_REGISTRY:
        raise ValueError(f"Unknown agent role: {to_role}")

    # Emit delegation start marker (no visible response bubble)
    await emit({
        "type": "delegation_start",
        "from_role": from_role,
        "to_role": to_role,
        "question": question,
        "timestamp": __import__("time").time(),
    })

    # Retrieve agent-exclusive data (silent briefing retrieval)
    citations = await retrieve(query=question, persona=to_role, k=3)
    briefing_block = build_briefing(citations)

    # Emit delegation end marker
    await emit({
        "type": "delegation_end",
        "to_role": to_role,
        "citation_count": len(citations),
        "timestamp": __import__("time").time(),
    })

    log.info(
        "delegation: %s→%s silent briefing, %d citations, %.0fms",
        from_role,
        to_role,
        len(citations),
        ((__import__("time").perf_counter() - t0) * 1000),
    )

    return {
        "response": briefing_block,
        "citations": citations,
        "briefing_block": briefing_block,
    }
