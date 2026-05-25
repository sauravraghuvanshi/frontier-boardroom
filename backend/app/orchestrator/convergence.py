"""Convergence detector (§6.4).

Ends a debate when:
  - CEO produced a 'summary' turn AND
  - rolling sentiment label is 'cordial' or 'converging' AND
  - >= 3 of 5 agents have signaled 'support' or 'vote' since last summary
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConvergenceState:
    last_ceo_summary_idx: int = -1
    supports_since_summary: set[str] = field(default_factory=set)
    mood_label: str = "cordial"
    turn_count: int = 0

    def update_after_turn(self, role: str, intent: str | None) -> None:
        self.turn_count += 1
        if role == "CEO" and intent == "summary":
            self.last_ceo_summary_idx = self.turn_count
            self.supports_since_summary.clear()
        elif intent in ("support", "vote"):
            self.supports_since_summary.add(role)

    def should_end(self) -> bool:
        return (
            self.last_ceo_summary_idx >= 0
            and self.mood_label in ("cordial", "converging", "resolved")
            and len(self.supports_since_summary) >= 3
        )
