"""Server-authoritative mood state machine (§6.6).

States: cordial -> debating -> heated -> converging -> resolved.
Drives lighting, camera, music intensity on the client.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Tuple

LABEL = ("cordial", "debating", "heated", "converging", "resolved")


@dataclass
class MoodState:
    window_seconds: float = 30.0
    _samples: Deque[Tuple[float, float]] = field(default_factory=deque)  # (timestamp, sentiment)
    _challenges: int = 0
    _agreements: int = 0
    _last_label: str = "cordial"

    def observe(self, sentiment: float) -> tuple[float, str]:
        now = time.time()
        self._samples.append((now, sentiment))
        cutoff = now - self.window_seconds
        while self._samples and self._samples[0][0] < cutoff:
            self._samples.popleft()
        if sentiment < -0.15:
            self._challenges += 1
        elif sentiment > 0.15:
            self._agreements += 1

        avg = sum(s for _, s in self._samples) / max(len(self._samples), 1)
        # Map avg in [-1,1] to value in [0,1] for client lighting.
        value = max(0.0, min(1.0, (avg + 1.0) / 2.0))

        label = self._label_from(avg)
        self._last_label = label
        return value, label

    def _label_from(self, avg: float) -> str:
        if self._agreements >= 4 and avg > 0.25:
            return "resolved"
        if avg > 0.1 and self._agreements > self._challenges:
            return "converging"
        if avg < -0.35:
            return "heated"
        if avg < -0.05 or self._challenges >= 2:
            return "debating"
        return "cordial"
