"""WebSocket /ws/debate/{session_id} (§7.2 + §7.3)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..public_demo_guard import UsageLimitExceeded, client_id, model_run_slot
from ..telemetry import get_logger
from .routes_debate import DEBATE_EVENTS, PENDING_DEBATES
from .routes_session import get_session, get_session_owner

router = APIRouter()
log = get_logger("ws")


@router.websocket("/ws/debate/{session_id}")
async def ws_debate(ws: WebSocket, session_id: str) -> None:
    await ws.accept()
    if get_session(session_id) is None:
        await ws.send_json({"type": "error", "message": "unknown session"})
        await ws.close()
        return

    # Wait for /debate POST to arm a question, but cap the wait.
    ev = DEBATE_EVENTS.setdefault(session_id, asyncio.Event())
    try:
        await asyncio.wait_for(ev.wait(), timeout=60)
    except asyncio.TimeoutError:
        await ws.send_json({"type": "error", "message": "no debate started"})
        await ws.close()
        return

    spec = PENDING_DEBATES.pop(session_id, None)
    ev.clear()
    if not spec:
        await ws.send_json({"type": "error", "message": "debate spec missing"})
        await ws.close()
        return

    from ..orchestrator.boardroom import Boardroom  # local import to avoid cycles

    boardroom = Boardroom()

    async def emit(event: dict[str, Any]) -> None:
        try:
            await ws.send_text(json.dumps(event))
        except Exception as e:  # noqa: BLE001
            log.warning("ws_send_failed", error=str(e))

    owner = get_session_owner(session_id)
    if owner is None or owner != client_id(ws):
        await emit({"type": "error", "message": "unknown session"})
        await ws.close()
        return

    try:
        async with model_run_slot(owner):
            await boardroom.run(
                question=spec["question"],
                scenario_id=spec.get("scenario_id"),
                emit=emit,
            )
    except UsageLimitExceeded as exc:
        await emit({
            "type": "error",
            "message": exc.message,
            "retry_after": exc.retry_after,
        })
    except WebSocketDisconnect:
        log.info("ws_disconnect", session_id=session_id)
    except Exception as e:  # noqa: BLE001
        log.exception("debate_failed")
        await emit({"type": "error", "message": str(e)})
    finally:
        try:
            await ws.close()
        except Exception:  # noqa: BLE001
            pass
