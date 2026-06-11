"""PrepSession — single-agent 1:1 prep flow.

Mirrors `Boardroom.run()` but for a HUMAN ↔ single AI agent thread:
- Human picks a seat (CEO/CFO/CMO/CTO/Legal). The AI agent for that seat answers.
- Each turn carries a sub-mode marker:
    [Mode: coach]    — second-person, sharpen the human's own argument
    [Mode: drill]    — pressure-test with one tough question at a time
    [Mode: simulate] — speak as a different seat (the human is asking
                       "what would Legal/CFO/etc. push back with?")
- Briefing-injection invariant (L-12) is preserved via the shared
  `briefing.build_briefing()` builder.
- Reasoning-fallback (L-15) lives inside `foundry_provider.py` and applies
  unchanged — PrepSession streams whatever tokens the provider yields.
"""

from __future__ import annotations

import time
from typing import Awaitable, Callable, Literal

from ..agents.providers.base import ChatMessage
from ..agents.registry import PREP_REGISTRY
from ..emotion.mood_state import MoodState
from ..emotion.sentiment import score_text
from ..grounding.foundry_iq_client import retrieve
from ..telemetry import agent_event, get_logger
from ..voice.tts import synthesize_with_visemes
from .briefing import build_briefing

log = get_logger("prep")

Emit = Callable[[dict], Awaitable[None]]
Mode = Literal["coach", "drill", "simulate"]


class PrepSession:
    def __init__(
        self,
        *,
        role: str,
        agenda_topic: str,
        agenda_id: str | None,
        sid: str,
    ) -> None:
        if role not in PREP_REGISTRY:
            raise ValueError(f"unknown prep role: {role}")
        self.role = role
        self.agenda_topic = agenda_topic
        self.agenda_id = agenda_id
        self.sid = sid
        self.mood = MoodState()
        # Per-speaker conversation history. Keyed by responding role so
        # simulated other-seat turns keep their own coherent thread without
        # contaminating the primary seat's history.
        self._history: dict[str, list[ChatMessage]] = {r: [] for r in PREP_REGISTRY}

    async def handle_turn(
        self,
        *,
        user_text: str,
        mode: Mode,
        simulate_role: str | None,
        emit: Emit,
    ) -> None:
        """Run one prep turn — retrieve → brief → ask agent → stream tokens."""
        if mode == "simulate":
            responder = simulate_role or self.role
            if responder not in PREP_REGISTRY:
                responder = self.role
        else:
            responder = self.role
        agent = PREP_REGISTRY[responder]
        t0 = time.perf_counter()

        # Echo the human's message so the frontend can render the right-aligned
        # user bubble through the same WS event protocol (L-9).
        await emit({
            "type": "user_message",
            "text": user_text,
            "mode": mode,
            "simulate_role": simulate_role if mode == "simulate" else None,
            "timestamp": time.time(),
        })

        # Retrieve grounding for THIS prep question, persona-filtered.
        retrieval_query = f"{self.agenda_topic}\n\n{user_text}"
        citations = await retrieve(query=retrieval_query, persona=responder, k=3)
        for c in citations:
            await emit({
                "type": "citation",
                "agent": responder,
                "source_uri": c.get("source_uri", ""),
                "snippet": c.get("snippet", ""),
                "confidence": c.get("confidence", 0.5),
                "hops": c.get("hops", 1),
            })

        briefing_block = build_briefing(citations)

        mode_marker = f"[Mode: {mode}]"
        if mode == "simulate":
            sim_hint = (
                f" The human asked about how {simulate_role} would push back; "
                f"answer in your own ({responder}) voice with that lens."
            )
            mode_marker = f"[Mode: simulate]{sim_hint}"

        grounded_turn = (
            f"{briefing_block}\n\n"
            f"Upcoming board meeting agenda: {self.agenda_topic}\n"
            f"{mode_marker}\n"
            f"Human {self.role}: {user_text}\n\n"
            "Respond in your prep persona. Cite source filenames inline. "
            "If a number you would normally cite is not in the briefing above, "
            "say 'I don't have that figure in our briefing materials.' "
            "Do NOT think out loud, do NOT narrate your reasoning."
        )

        await emit({
            "type": "turn_start",
            "agent": responder,
            "model": agent.model_ref,
            "mode": mode,
            "timestamp": time.time(),
        })
        agent_event(responder, "prep_turn_start", model=agent.model_ref, mode=mode)

        buffer: list[str] = []
        tokens = 0
        try:
            async for tok in agent.think(grounded_turn, history=self._history[responder]):
                buffer.append(tok)
                tokens += 1
                await emit({"type": "token", "agent": responder, "text": tok})
        except Exception as e:  # noqa: BLE001
            err_msg = f"[{responder} provider error: {type(e).__name__}: {e}]"
            log.error("prep_turn_failed", role=responder, error=str(e), model=agent.model_ref)
            await emit({"type": "token", "agent": responder, "text": err_msg})
            buffer.append(err_msg)

        full_text = "".join(buffer).strip() or f"[{responder} produced no tokens]"
        # Persist the conversation: the human's prompt + the agent reply, scoped
        # to the responder's history so each simulated seat keeps its own thread.
        self._history[responder].append(
            ChatMessage(role="user", content=grounded_turn)
        )
        self._history[responder].append(
            ChatMessage(role="assistant", content=full_text)
        )

        # Mood update — feeds the same UI pill as debate mode.
        sentiment = score_text(full_text)
        mood_value, mood_label = self.mood.observe(sentiment)
        await emit({"type": "mood", "value": mood_value, "label": mood_label})

        # TTS + visemes (best-effort).
        try:
            audio_b64, viseme_frames = await synthesize_with_visemes(
                text=full_text, voice=agent.persona.voice
            )
            if audio_b64:
                await emit({"type": "audio_chunk", "agent": responder, "base64": audio_b64})
            if viseme_frames:
                await emit({"type": "viseme", "agent": responder, "frames": viseme_frames})
        except Exception as e:  # noqa: BLE001
            log.warning("prep_tts_failed", role=responder, error=str(e))

        duration_ms = int((time.perf_counter() - t0) * 1000)
        await emit({
            "type": "turn_end",
            "agent": responder,
            "duration_ms": duration_ms,
            "tokens": tokens,
        })
        agent_event(responder, "prep_turn_end", duration_ms=duration_ms, tokens=tokens)
