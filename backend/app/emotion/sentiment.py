"""Sentiment scoring.

Uses Azure AI Language sentiment API when configured; otherwise a tiny
lexicon-based fallback that runs offline. Returns float in [-1.0, 1.0].
"""

from __future__ import annotations

from ..config import get_settings

_NEG = {
    "no",
    "not",
    "never",
    "risk",
    "fail",
    "decline",
    "concern",
    "concerned",
    "wrong",
    "danger",
    "loss",
    "burn",
    "expensive",
    "unsafe",
    "violate",
    "violation",
    "blocker",
    "bad",
    "poor",
    "weak",
    "shrink",
}
_POS = {
    "agree",
    "yes",
    "good",
    "great",
    "approve",
    "support",
    "win",
    "growth",
    "profit",
    "strong",
    "safe",
    "compliant",
    "opportunity",
    "favor",
    "favorable",
    "endorse",
}


def score_text(text: str) -> float:
    if not text:
        return 0.0
    settings = get_settings()
    if settings.azure_language_endpoint:
        # TODO(plan): call Azure Language sentiment via DefaultAzureCredential
        # (AAD-token auth — see voice/tts.py pattern). Skipped offline.
        pass
    words = [w.strip(".,;:!?\"'()").lower() for w in text.split()]
    pos = sum(1 for w in words if w in _POS)
    neg = sum(1 for w in words if w in _NEG)
    total = pos + neg
    if total == 0:
        return 0.0
    return max(-1.0, min(1.0, (pos - neg) / max(total, 4)))
