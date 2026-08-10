"""WebSocket /ws/prep/{sid} (§7.2 + §7.3, prep variant).

Multi-turn loop: accept the WS, look up the PrepSession, then drain the per-session
asyncio.Queue forever — calling `prep_session.handle_turn()` for each queued
human message — until the client disconnects.

Handles two types of queued messages:
1. Normal messages: {"text", "mode", "simulate_role", "mentions"}
2. Delegation messages: {"type": "delegate", "from_role", "to_role", "question"}
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..orchestrator.prep_delegate import stream_delegate_response
from ..public_demo_guard import UsageLimitExceeded, client_id, model_run_slot
from ..telemetry import get_logger
from .routes_prep import get_prep_owner, get_prep_queue, get_prep_session

router = APIRouter()
log = get_logger("ws_prep")


@router.websocket("/ws/prep/{sid}")
async def ws_prep(ws: WebSocket, sid: str) -> None:
    await ws.accept()
    session = get_prep_session(sid)
    if session is None:
        await ws.send_json({"type": "error", "message": "unknown prep session"})
        await ws.close()
        return

    queue = get_prep_queue(sid)
    if queue is None:
        await ws.send_json({"type": "error", "message": "prep queue missing"})
        await ws.close()
        return

    async def emit(event: dict[str, Any]) -> None:
        try:
            await ws.send_text(json.dumps(event))
        except Exception as e:  # noqa: BLE001
            log.warning("ws_send_failed", error=str(e))

    await emit({
        "type": "prep_ready",
        "role": session.role,
        "agenda_topic": session.agenda_topic,
        "agenda_id": session.agenda_id,
    })

    # Watcher coroutine: detect client-initiated disconnect so we can break the
    # outer loop even when blocked on queue.get().
    disconnect_evt = asyncio.Event()

    async def watch_disconnect() -> None:
        try:
            while True:
                # receive_text() raises WebSocketDisconnect on close; we swallow
                # any text the client might send (no protocol from client→server
                # mid-session — messages arrive via HTTP POST).
                await ws.receive_text()
        except WebSocketDisconnect:
            disconnect_evt.set()
        except Exception:  # noqa: BLE001
            disconnect_evt.set()

    watcher = asyncio.create_task(watch_disconnect())

    try:
        while not disconnect_evt.is_set():
            get_task = asyncio.create_task(queue.get())
            disc_task = asyncio.create_task(disconnect_evt.wait())
            done, pending = await asyncio.wait(
                {get_task, disc_task}, return_when=asyncio.FIRST_COMPLETED
            )
            for t in pending:
                t.cancel()
            if disc_task in done:
                # Drop the (possibly-fetched) message; client is gone.
                if get_task in done and not get_task.cancelled():
                    try:
                        get_task.result()
                    except Exception:  # noqa: BLE001
                        pass
                break
            msg = get_task.result()
            try:
                owner = get_prep_owner(sid)
                if owner is None or owner != client_id(ws):
                    await emit({"type": "error", "message": "unknown prep session"})
                    break
                async with model_run_slot(owner):
                    if msg.get("type") == "delegate":
                        # Route delegation directly to stream_delegate_response
                        await stream_delegate_response(
                            from_role=msg["from_role"],
                            to_role=msg["to_role"],
                            question=msg["question"],
                            emit=emit,
                        )
                    else:
                        # Normal message: route to session.handle_turn()
                        await session.handle_turn(
                            user_text=msg["text"],
                            mode=msg["mode"],
                            simulate_role=msg.get("simulate_role"),
                            mentions=msg.get("mentions", []),
                            emit=emit,
                        )
            except UsageLimitExceeded as exc:
                await emit({
                    "type": "error",
                    "message": exc.message,
                    "retry_after": exc.retry_after,
                })
            except Exception as e:  # noqa: BLE001
                log.exception("prep_turn_failed", sid=sid)
                await emit({"type": "error", "message": str(e)})
    finally:
        watcher.cancel()
        try:
            await ws.close()
        except Exception:  # noqa: BLE001
            pass
