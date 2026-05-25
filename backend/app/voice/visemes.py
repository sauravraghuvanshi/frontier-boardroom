"""Heuristic viseme fallback (dev only — §16 rule 7 forbids in prod)."""

from __future__ import annotations

# Rough Azure Speech viseme IDs cycled per word.
_VISEME_CYCLE = [1, 4, 7, 11, 13, 19]


def heuristic_visemes(text: str, ms_per_word: int = 250) -> list[dict]:
    frames: list[dict] = []
    offset = 0
    for i, _word in enumerate(text.split()):
        frames.append({"visemeId": _VISEME_CYCLE[i % len(_VISEME_CYCLE)], "offset_ms": offset})
        offset += ms_per_word
    frames.append({"visemeId": 0, "offset_ms": offset})
    return frames
