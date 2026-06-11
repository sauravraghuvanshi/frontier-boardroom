"""Boardroom — orchestrates a single debate using the Microsoft Agent Framework
shape (Workflow + agents). When the official package GA's we swap this for the
native primitive; for now we keep a thin, dependency-free coordinator.

Emits §7.3 events via the `emit` callable.
"""

from __future__ import annotations

import time
from typing import Awaitable, Callable

from ..agents.registry import AGENT_REGISTRY
from ..config import get_settings
from ..emotion.mood_state import MoodState
from ..emotion.sentiment import score_text
from ..grounding.foundry_iq_client import retrieve
from ..telemetry import agent_event, get_logger
from ..voice.tts import synthesize_with_visemes
from .a2a_protocol import A2AMessage
from .briefing import build_briefing
from .convergence import ConvergenceState
from .turn_taking import turn_sequence

log = get_logger("boardroom")
Emit = Callable[[dict], Awaitable[None]]


class Boardroom:
    def __init__(self, max_rounds: int = 3) -> None:
        self.max_rounds = max_rounds
        self.mood = MoodState()

    async def run(
        self,
        *,
        question: str,
        scenario_id: str | None,
        emit: Emit,
    ) -> None:
        settings = get_settings()
        convergence = ConvergenceState()
        history_for_role: dict[str, list[dict]] = {role: [] for role in AGENT_REGISTRY}
        seed_user = (
            f"Boardroom question (scenario={scenario_id or 'open'}): {question}\n"
            "Discuss, challenge, cite sources, and converge on a decision."
        )
        for role in AGENT_REGISTRY:
            history_for_role[role].append({"role": "user", "content": seed_user})

        spoken_roles: set[str] = set()

        for role in turn_sequence(self.max_rounds):
            agent = AGENT_REGISTRY[role]
            t0 = time.perf_counter()

            # Retrieve grounding for this turn (persona-filtered).
            citations = await retrieve(query=question, persona=role, k=3)
            for c in citations:
                await emit({
                    "type": "citation",
                    "agent": role,
                    "source_uri": c.get("source_uri", ""),
                    "snippet": c.get("snippet", ""),
                    "confidence": c.get("confidence", 0.5),
                    "hops": c.get("hops", 1),
                })

            # Build a Boardroom briefing block from the retrieved snippets and
            # inject it as the user turn. Every persona prompt expects this.
            briefing_block = build_briefing(citations)
            grounded_turn = (
                f"{briefing_block}\n\n"
                f"Boardroom question (scenario={scenario_id or 'open'}): {question}\n"
                "Respond in your persona. Cite source filenames inline. "
                "If a number you would normally cite is not in the briefing above, "
                "say 'I don't have that figure in our briefing materials.' "
                "Do NOT think out loud, do NOT narrate your reasoning, do NOT "
                "preface with 'we need to' or 'let me' — speak directly as the executive."
            )

            await emit({
                "type": "turn_start",
                "agent": role,
                "model": agent.model_ref,
                "timestamp": time.time(),
            })
            agent_event(role, "turn_start", model=agent.model_ref)

            buffer: list[str] = []
            tokens = 0
            try:
                async for tok in agent.think(grounded_turn, history=history_for_role[role]):
                    buffer.append(tok)
                    tokens += 1
                    await emit({"type": "token", "agent": role, "text": tok})
            except Exception as e:  # noqa: BLE001
                err_msg = f"[{role} provider error: {type(e).__name__}: {e}]"
                log.error("turn_failed", role=role, error=str(e), model=agent.model_ref)
                await emit({"type": "token", "agent": role, "text": err_msg})
                buffer.append(err_msg)

            full_text = "".join(buffer).strip() or f"[{role} produced no tokens]"
            history_for_role[role].append({"role": "assistant", "content": full_text})
            spoken_roles.add(role)
            # Share assistant's text with peers as context.
            for other_role in AGENT_REGISTRY:
                if other_role != role:
                    history_for_role[other_role].append(
                        {"role": "user", "content": f"{role} said: {full_text}"}
                    )

            intent = "summary" if (role == "CEO" and "decision" in full_text.lower()) else "support"
            a2a = A2AMessage(**{"from": role, "to": "ALL", "intent": intent, "content": full_text})
            convergence.update_after_turn(role, intent)

            # Mood update (server-authoritative).
            sentiment = score_text(full_text)
            mood_value, mood_label = self.mood.observe(sentiment)
            convergence.mood_label = mood_label
            await emit({"type": "mood", "value": mood_value, "label": mood_label})

            # TTS + visemes (best-effort; skipped if Speech not configured).
            try:
                audio_b64, viseme_frames = await synthesize_with_visemes(
                    text=full_text, voice=agent.persona.voice
                )
                if audio_b64:
                    await emit({"type": "audio_chunk", "agent": role, "base64": audio_b64})
                if viseme_frames:
                    await emit({"type": "viseme", "agent": role, "frames": viseme_frames})
            except Exception as e:  # noqa: BLE001
                log.warning("tts_failed", role=role, error=str(e))

            duration_ms = int((time.perf_counter() - t0) * 1000)
            await emit({
                "type": "turn_end",
                "agent": role,
                "duration_ms": duration_ms,
                "tokens": tokens,
            })
            agent_event(role, "turn_end", duration_ms=duration_ms, tokens=tokens)

            if convergence.should_end() and "Legal" in spoken_roles:
                break

        decision = _extract_decision(history_for_role.get("CEO", []))
        vote = {r: _parse_vote(history_for_role.get(r, [])) for r in AGENT_REGISTRY}
        await emit({
            "type": "debate_end",
            "decision": decision,
            "vote": vote,
        })
        log.info("debate_end", decision=decision, settings_fake=settings.use_fake_debate)


_NO_TOKENS = (
    "reject",
    "oppose",
    "i object",
    "vote no",
    "vote against",
    "i'd vote no",
    "i would vote no",
    "would not approve",
    "do not approve",
    "no-go",
    "i disagree",
    "position: reject",
)

_YES_TOKENS = (
    "approve",
    "endorse",
    "agree",
    "i support",
    "vote yes",
    "i'd vote yes",
    "in favor",
    "favour",
    "go ahead",
    "go-ahead",
    "position: approve",
)

_ABSTAIN_TOKENS = (
    "abstain",
    "need more data",
    "more data",
    "defer",
    "table this",
    "position: abstain",
)


def _last_assistant_text(history: list[dict]) -> str:
    for h in reversed(history):
        if h.get("role") == "assistant":
            return (h.get("content") or "").strip()
    return ""


def _parse_vote(history: list[dict]) -> str:
    text = _last_assistant_text(history).lower()
    if not text:
        return "abstain"
    # Reject wins over approve when both appear (critic stance).
    if any(t in text for t in _NO_TOKENS):
        return "no"
    if any(t in text for t in _ABSTAIN_TOKENS):
        return "abstain"
    if any(t in text for t in _YES_TOKENS):
        return "yes"
    return "abstain"


def _extract_decision(ceo_history: list[dict]) -> str:
    text = _last_assistant_text(ceo_history)
    if not text:
        return "No decision recorded — board did not converge."
    # Prefer a bold **Decision:** line if the CEO emitted one.
    for line in text.splitlines():
        s = line.strip().lstrip("*-• ").strip()
        low = s.lower()
        if low.startswith("decision:") or low.startswith("**decision:"):
            return s.replace("**", "").strip()
    # Fallback: last non-empty line.
    for line in reversed(text.splitlines()):
        s = line.strip()
        if s:
            return s.replace("**", "")
    return "No decision recorded."
