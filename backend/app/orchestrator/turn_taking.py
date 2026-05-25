"""Turn-taking policy (§6.3).

Order: CEO opens, then CFO, CMO, CTO, Legal challenge in interest order,
CEO summarizes every 2 rounds, then votes.
"""

from __future__ import annotations

from typing import Iterator

DEFAULT_ORDER = ["CEO", "CFO", "CMO", "CTO", "Legal"]


def turn_sequence(max_rounds: int = 3) -> Iterator[str]:
    """Yields the role-name sequence for the entire debate."""
    for r in range(max_rounds):
        for role in DEFAULT_ORDER:
            yield role
        # CEO synthesis pass at end of each round
        yield "CEO"
