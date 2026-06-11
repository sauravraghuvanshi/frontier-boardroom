"""Briefing block builder — shared between Boardroom (debate) and PrepSession.

L-12 invariant: every persona prompt is anchored on the exact header
"Boardroom briefing — verbatim excerpts from the company knowledge base:".
Both flows MUST inject this block into the user turn passed to `agent.think()`.
Emitting `citation` WS events alone does NOT ground the model.
"""

from __future__ import annotations

from typing import Sequence


BRIEFING_HEADER = "Boardroom briefing — verbatim excerpts from the company knowledge base:"


def build_briefing(citations: Sequence[dict]) -> str:
    """Render retrieved citations as the briefing block injected into the LLM turn."""
    lines = [BRIEFING_HEADER]
    for c in citations:
        src = c.get("source_uri", "unknown")
        snip = (c.get("snippet") or "").strip()
        if snip:
            lines.append(f"- [{src}] {snip}")
    if len(lines) == 1:
        lines.append("- (no excerpts returned for this query)")
    return "\n".join(lines)
