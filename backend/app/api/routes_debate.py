"""Debate kickoff (§7.1)."""

from __future__ import annotations

import asyncio
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .routes_session import get_session

router = APIRouter(tags=["debate"])

# session_id -> debate spec (consumed by WS handler)
PENDING_DEBATES: Dict[str, dict] = {}
DEBATE_EVENTS: Dict[str, asyncio.Event] = {}


class StartDebateRequest(BaseModel):
    session_id: str
    question: str = Field(min_length=4, max_length=2000)
    scenario_id: Optional[str] = None


class StartDebateResponse(BaseModel):
    debate_id: str


@router.post("/debate", response_model=StartDebateResponse)
async def start_debate(req: StartDebateRequest) -> StartDebateResponse:
    if get_session(req.session_id) is None:
        raise HTTPException(status_code=404, detail="session not found")
    debate_id = uuid.uuid4().hex
    PENDING_DEBATES[req.session_id] = {
        "debate_id": debate_id,
        "question": req.question,
        "scenario_id": req.scenario_id,
    }
    ev = DEBATE_EVENTS.setdefault(req.session_id, asyncio.Event())
    ev.set()
    return StartDebateResponse(debate_id=debate_id)
