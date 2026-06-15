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
    """Stream a delegated agent response within a prep session.

    Args:
        from_role: "CEO" (only role allowed to delegate)
        to_role: "CTO" | "CFO" | "CMO" | "Legal" (must be in DELEGATION_HIERARCHY[from_role])
        question: User's question to delegate
        emit: Async callable to emit WS events

    Returns:
        {
            "response": full_response_text,
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

    # Get the agent
    agent = PREP_REGISTRY[to_role]

    # Emit delegation start
    await emit({
        "type": "delegation_start",
        "from_role": from_role,
        "to_role": to_role,
        "question": question,
        "timestamp": __import__("time").time(),
    })

    # Emit turn_start so frontend creates a new message bubble
    await emit({
        "type": "turn_start",
        "agent": to_role,
        "model": agent.model_ref,
        "timestamp": __import__("time").time(),
    })

    # Retrieve CTO-exclusive data
    citations = await retrieve(query=question, persona=to_role, k=3)

    # Build grounded turn (same pattern as prep_session)
    briefing_block = build_briefing(citations)
    grounded_turn = (
        f"{briefing_block}\n\n"
        f"Context: You are being consulted by {from_role} during a prep session.\n"
        f"{from_role}'s question: {question}\n\n"
        f"Respond directly and concisely. Cite source filenames inline. "
        f"Keep under 150 words."
    )

    # Stream agent response
    full_response = ""
    try:
        # Get agent history (empty for delegation, we're starting fresh)
        history = []
        async for token in agent.think(grounded_turn, history=history):
            full_response += token
            # Emit token event (same structure as normal turn)
            await emit({
                "type": "token",
                "agent": to_role,
                "text": token,
            })
    except Exception as e:
        log.error("delegation: agent.think failed for %s: %s", to_role, e)
        error_msg = f"Error consulting {to_role}: {str(e)[:100]}"
        await emit({
            "type": "token",
            "agent": to_role,
            "text": error_msg,
        })
        full_response = error_msg

    # Emit delegation end
    await emit({
        "type": "delegation_end",
        "to_role": to_role,
        "response_length": len(full_response),
        "citation_count": len(citations),
        "timestamp": __import__("time").time(),
    })

    # Emit turn_end to mark delegation complete
    await emit({
        "type": "turn_end",
        "agent": to_role,
        "duration_ms": int(((__import__("time").perf_counter() - t0) * 1000)),
        "tokens": len(full_response.split()),
    })

    log.info(
        "delegation: %s consulted %s, response %d chars, %d citations",
        from_role,
        to_role,
        len(full_response),
        len(citations),
    )

    return {
        "response": full_response,
        "citations": citations,
        "briefing_block": briefing_block,
    }
