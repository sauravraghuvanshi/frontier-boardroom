"""Prep-mode session lifecycle (§7.1, prep variant).

POST /api/v1/prep-session         — create a 1:1 prep thread (seat + agenda).
POST /api/v1/prep-session/{sid}/message — queue a human turn for the WS loop.

Bridges HTTP POSTs into the WS run loop via a per-session asyncio.Queue, mirroring
the PENDING_DEBATES + DEBATE_EVENTS pattern in `routes_debate.py` but without the
single-shot Event (prep is multi-turn, so a queue is the natural fit).
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents.registry import PREP_REGISTRY
from ..orchestrator.prep_session import PrepSession

router = APIRouter(tags=["prep"])

# Process-local prep stores. Production swaps for Redis.
_PREP_SESSIONS: Dict[str, PrepSession] = {}
_PREP_QUEUES: Dict[str, asyncio.Queue[dict]] = {}


def get_prep_session(sid: str) -> PrepSession | None:
    return _PREP_SESSIONS.get(sid)


def get_prep_queue(sid: str) -> asyncio.Queue[dict] | None:
    return _PREP_QUEUES.get(sid)


class CreatePrepSessionRequest(BaseModel):
    role: str = Field(min_length=2, max_length=16)
    agenda_topic: str = Field(min_length=2, max_length=2000)
    agenda_id: Optional[str] = None


class CreatePrepSessionResponse(BaseModel):
    prep_session_id: str
    role: str


class PrepMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    mode: Literal["coach", "drill", "simulate"]
    simulate_role: Optional[str] = None


class PrepMessageResponse(BaseModel):
    queued: bool


@router.post("/prep-session", response_model=CreatePrepSessionResponse)
async def create_prep_session(req: CreatePrepSessionRequest) -> CreatePrepSessionResponse:
    if req.role not in PREP_REGISTRY:
        raise HTTPException(
            status_code=400, detail=f"unknown role: {req.role}"
        )
    sid = uuid.uuid4().hex
    _PREP_SESSIONS[sid] = PrepSession(
        role=req.role,
        agenda_topic=req.agenda_topic,
        agenda_id=req.agenda_id,
        sid=sid,
    )
    _PREP_QUEUES[sid] = asyncio.Queue()
    return CreatePrepSessionResponse(prep_session_id=sid, role=req.role)


@router.post(
    "/prep-session/{sid}/message", response_model=PrepMessageResponse
)
async def post_prep_message(sid: str, req: PrepMessageRequest) -> PrepMessageResponse:
    if sid not in _PREP_SESSIONS:
        raise HTTPException(status_code=404, detail="prep session not found")
    if req.mode == "simulate":
        if not req.simulate_role or req.simulate_role not in PREP_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail="simulate mode requires a valid simulate_role",
            )
    queue = _PREP_QUEUES.setdefault(sid, asyncio.Queue())
    await queue.put({
        "text": req.text,
        "mode": req.mode,
        "simulate_role": req.simulate_role,
    })
    return PrepMessageResponse(queued=True)
