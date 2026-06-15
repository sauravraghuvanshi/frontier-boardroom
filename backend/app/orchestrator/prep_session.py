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

import re
import time
from typing import Awaitable, Callable, Literal

_MENTION_RE = re.compile(r"@(CEO|CFO|CMO|CTO|Legal)\b", re.IGNORECASE)


def _strip_mentions(text: str) -> str:
    """Remove @ROLE tokens so the model doesn't echo the routing syntax."""
    return _MENTION_RE.sub("", text).replace("  ", " ").strip()

from ..agents.providers.base import ChatMessage
from ..agents.registry import PREP_REGISTRY
from ..emotion.mood_state import MoodState
from ..emotion.sentiment import score_text
from ..grounding.foundry_iq_client import retrieve
from ..telemetry import agent_event, get_logger
from ..voice.tts import synthesize_with_visemes
from .briefing import build_briefing
from .prep_delegate import stream_delegate_response

log = get_logger("prep")

Emit = Callable[[dict], Awaitable[None]]
Mode = Literal["coach", "drill", "simulate"]


class _FenceStripper:
    """Strip a leading ```markdown / ``` fence and the matching trailing ```
    from a token stream. gpt-4o (CMO) and gpt-4.1 (CTO) habitually wrap their
    entire reply in a code fence even when told not to — that turns the body
    into a literal block and asterisks render raw in the chat bubble.

    Stream-aware: buffers the head until it can decide if a fence is opening,
    and holds back the last few chars so a trailing fence never reaches the
    client. Mid-text ``` (legitimate code blocks) pass through unchanged.
    """

    def __init__(self) -> None:
        self._lead_buf: list[str] = []
        self._lead_done = False
        self._tail = ""

    def feed(self, tok: str) -> str:
        if not self._lead_done:
            self._lead_buf.append(tok)
            joined = "".join(self._lead_buf)
            stripped = joined.lstrip()
            if stripped.startswith("```"):
                nl = stripped.find("\n")
                if nl == -1:
                    return ""  # opening fence header not finished yet
                rest = stripped[nl + 1:]
                self._lead_done = True
                self._lead_buf = []
                return self._holdback(rest)
            if stripped and not stripped.startswith("`"):
                self._lead_done = True
                out = joined
                self._lead_buf = []
                return self._holdback(out)
            return ""
        return self._holdback(tok)

    def _holdback(self, s: str) -> str:
        combined = self._tail + s
        if len(combined) <= 8:
            self._tail = combined
            return ""
        emit = combined[:-8]
        self._tail = combined[-8:]
        return emit

    def flush(self) -> str:
        if not self._lead_done:
            out = "".join(self._lead_buf)
            self._lead_buf = []
            self._lead_done = True
        else:
            out = self._tail
        self._tail = ""
        rstripped = out.rstrip()
        if rstripped.endswith("```"):
            return rstripped[:-3].rstrip()
        return out


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
        # Accumulated briefing blocks from delegated agents (CEO calls CTO, etc.)
        self._delegate_briefings: dict[str, str] = {}

    async def handle_turn(
        self,
        *,
        user_text: str,
        mode: Mode,
        simulate_role: str | None,
        mentions: list[str] | None,
        emit: Emit,
    ) -> None:
        """Run one prep turn — optionally delegate, retrieve → brief → ask agent → stream tokens.

        Args:
            user_text: The human's input
            mode: "coach" | "drill" | "simulate"
            simulate_role: If mode="simulate", which role to simulate
            mentions: List of agent names to delegate to (e.g., ["CTO"])
            emit: WS event emitter callback
        """
        if mode == "simulate":
            responder = simulate_role or self.role
            if responder not in PREP_REGISTRY:
                responder = self.role
        else:
            responder = self.role
        agent = PREP_REGISTRY[responder]
        t0 = time.perf_counter()

        # Strip @ROLE tokens for downstream use (model + KB retrieval). The raw
        # text still goes back to the UI via user_message so the human sees what
        # they typed.
        clean_text = _strip_mentions(user_text) if mentions else user_text

        # Echo the human's message FIRST so it appears before delegations (L-9)
        await emit({
            "type": "user_message",
            "text": user_text,
            "mode": mode,
            "simulate_role": simulate_role if mode == "simulate" else None,
            "timestamp": time.time(),
        })

        # Handle delegations after user's message is displayed
        if mentions and self.role == "CEO":
            for to_role in mentions:
                try:
                    result = await stream_delegate_response(
                        from_role=self.role,
                        to_role=to_role,
                        question=clean_text,
                        emit=emit,
                    )
                    # Accumulate the briefing block for later injection
                    self._delegate_briefings[to_role] = result["briefing_block"]
                    log.info(
                        "delegation_accumulated: %s added to briefings, block length=%d",
                        to_role,
                        len(result["briefing_block"]),
                    )
                except Exception as e:
                    log.error("delegation_failed: %s: %s", to_role, e, exc_info=True)
                    await emit({
                        "type": "error",
                        "message": f"Delegation to {to_role} failed: {str(e)}",
                    })
        elif mentions:
            log.warning(
                "delegation_not_allowed: only CEO can delegate, got %s",
                self.role
            )

        # Retrieve grounding for THIS prep question, persona-filtered.
        retrieval_query = f"{self.agenda_topic}\n\n{clean_text}"
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

        # Inject accumulated delegation briefings if any
        if self._delegate_briefings:
            log.info("injecting_delegation_briefings: agents=%s", list(self._delegate_briefings.keys()))
            delegation_section = "Additional context from delegated agents:\n"
            for agent_name, briefing in self._delegate_briefings.items():
                delegation_section += f"\n**{agent_name} provided:**\n{briefing}\n"
            briefing_block = f"{briefing_block}\n\n{delegation_section}"
            log.info("injected: briefing_block now %d chars", len(briefing_block))
        else:
            log.info("no_delegated_briefings: _delegate_briefings empty")

        mode_marker = f"[Mode: {mode}]"
        if mode == "simulate":
            sim_hint = (
                f" The human asked about how {simulate_role} would push back; "
                f"answer in your own ({responder}) voice with that lens."
            )
            mode_marker = f"[Mode: simulate]{sim_hint}"

        delegation_directive = ""
        if self._delegate_briefings:
            delegated_names = ", ".join(self._delegate_briefings.keys())
            delegation_directive = (
                f" You delegated parts of this question to {delegated_names}; "
                "their grounded findings appear in the briefing above under "
                "'Additional context from delegated agents:'. Weave those "
                "specific numbers, source filenames, and conclusions into your "
                "answer — do not ignore them."
            )

        grounded_turn = (
            f"{briefing_block}\n\n"
            f"Upcoming board meeting agenda: {self.agenda_topic}\n"
            f"{mode_marker}\n"
            f"Human {self.role}: {clean_text}\n\n"
            "Respond in your prep persona. Cite source filenames inline. "
            "If a number you would normally cite is not in the briefing above, "
            "say 'I don't have that figure in our briefing materials.' "
            "Do NOT think out loud, do NOT narrate your reasoning."
            f"{delegation_directive}"
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
        stripper = _FenceStripper()
        try:
            async for tok in agent.think(grounded_turn, history=self._history[responder]):
                clean = stripper.feed(tok)
                if clean:
                    buffer.append(clean)
                    tokens += 1
                    await emit({"type": "token", "agent": responder, "text": clean})
        except Exception as e:  # noqa: BLE001
            err_msg = f"[{responder} provider error: {type(e).__name__}: {e}]"
            log.error("prep_turn_failed", role=responder, error=str(e), model=agent.model_ref)
            await emit({"type": "token", "agent": responder, "text": err_msg})
            buffer.append(err_msg)

        tail = stripper.flush()
        if tail:
            buffer.append(tail)
            tokens += 1
            await emit({"type": "token", "agent": responder, "text": tail})

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
