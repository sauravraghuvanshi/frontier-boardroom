"""Audience live-question inbox.

Single-slot in-memory queue. Audience phones POST a question via the QR
landing page; the main presenter display polls every few seconds and, on
hit, starts a new debate with that question via the existing flow.

Demo-safe: no DB, no persistence — if the backend restarts the inbox is
empty, which is the right behavior between sessions.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["audience"])


class AudienceQuestion(BaseModel):
    question: str = Field(min_length=4, max_length=500)
    name: Optional[str] = Field(default=None, max_length=80)


class SubmitResponse(BaseModel):
    ok: bool = True


class PollResponse(BaseModel):
    question: Optional[AudienceQuestion] = None


_INBOX: dict[str, Optional[AudienceQuestion]] = {"current": None}


@router.post("/audience-question", response_model=SubmitResponse)
async def submit(q: AudienceQuestion) -> SubmitResponse:
    _INBOX["current"] = q
    return SubmitResponse(ok=True)


@router.get("/audience-question/poll", response_model=PollResponse)
async def poll() -> PollResponse:
    q = _INBOX["current"]
    _INBOX["current"] = None
    return PollResponse(question=q)
