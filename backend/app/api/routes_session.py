"""Session lifecycle (§7.1)."""

from __future__ import annotations

import uuid
from time import monotonic
from typing import Dict

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ..public_demo_guard import enforce_http_quota

router = APIRouter(tags=["session"])

# Process-local session store. Production swaps for Redis.
_SESSIONS: Dict[str, dict] = {}
_SESSION_TTL_SECONDS = 2 * 60 * 60


class CreateSessionResponse(BaseModel):
    session_id: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session(request: Request) -> CreateSessionResponse:
    owner = await enforce_http_quota(request, "session")
    now = monotonic()
    expired = [
        sid
        for sid, session in _SESSIONS.items()
        if now - session["created_at"] >= _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _SESSIONS[sid]

    sid = uuid.uuid4().hex
    _SESSIONS[sid] = {"debates": [], "owner": owner, "created_at": now}
    return CreateSessionResponse(session_id=sid)


def get_session(session_id: str) -> dict | None:
    return _SESSIONS.get(session_id)


def get_session_owner(session_id: str) -> str | None:
    session = get_session(session_id)
    return session.get("owner") if session else None
