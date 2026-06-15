"""Prep mode delegation routes.

POST /api/v1/prep-session/{sid}/delegate — queue a delegation request (CEO calls CTO, etc.)

Delegates are queued through the same asyncio.Queue as normal turns, so the WS loop
processes them in order. The ws_prep handler detects {"type": "delegate"} and routes
to prep_delegate.stream_delegate_response().
"""

from __future__ import annotations

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..agents.registry import PREP_REGISTRY

router = APIRouter(tags=["prep"])


def get_prep_queue(sid: str) -> asyncio.Queue[dict] | None:
    """Import from routes_prep to avoid circular dependency."""
    from .routes_prep import _PREP_QUEUES
    return _PREP_QUEUES.get(sid)


class DelegateRequest(BaseModel):
    from_role: str = Field(default="CEO")
    to_role: str = Field(min_length=2, max_length=16)
    question: str = Field(min_length=1, max_length=4000)


class DelegateResponse(BaseModel):
    queued: bool


@router.post(
    "/prep-session/{sid}/delegate", response_model=DelegateResponse
)
async def post_prep_delegate(sid: str, req: DelegateRequest) -> DelegateResponse:
    """Queue a delegation request.

    Args:
        sid: Prep session ID
        req: { from_role, to_role, question }

    Returns:
        { queued: true }

    Errors:
        404: session not found
        400: invalid role or hierarchy violation
    """
    # Get the queue (will raise 404 if session doesn't exist)
    from .routes_prep import _PREP_SESSIONS

    if sid not in _PREP_SESSIONS:
        raise HTTPException(status_code=404, detail="prep session not found")

    # Validate roles
    if req.to_role not in PREP_REGISTRY:
        raise HTTPException(
            status_code=400, detail=f"unknown to_role: {req.to_role}"
        )

    # Note: hierarchy validation happens in prep_delegate.stream_delegate_response()
    # during actual streaming. Here we just queue it.

    queue = get_prep_queue(sid)
    if not queue:
        raise HTTPException(status_code=500, detail="prep queue not found")

    await queue.put({
        "type": "delegate",
        "from_role": req.from_role,
        "to_role": req.to_role,
        "question": req.question,
    })
    return DelegateResponse(queued=True)
