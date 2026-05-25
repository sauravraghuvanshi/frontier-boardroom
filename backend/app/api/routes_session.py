"""Session lifecycle (§7.1)."""

from __future__ import annotations

import uuid
from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["session"])

# Process-local session store. Production swaps for Redis.
_SESSIONS: Dict[str, dict] = {}


class CreateSessionResponse(BaseModel):
    session_id: str


@router.post("/session", response_model=CreateSessionResponse)
async def create_session() -> CreateSessionResponse:
    sid = uuid.uuid4().hex
    _SESSIONS[sid] = {"debates": []}
    return CreateSessionResponse(session_id=sid)


def get_session(session_id: str) -> dict | None:
    return _SESSIONS.get(session_id)
