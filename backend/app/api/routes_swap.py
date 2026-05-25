"""Hot model swap (§7.1)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.registry import AGENT_REGISTRY

router = APIRouter(tags=["swap"])


class SwapRequest(BaseModel):
    model_ref: str  # e.g. "foundry:gpt-5" or "databricks:claude-sonnet-4-5"


class SwapResponse(BaseModel):
    role: str
    model_ref: str


@router.post("/agent/{role}/swap-model", response_model=SwapResponse)
async def swap_model(role: str, req: SwapRequest) -> SwapResponse:
    if ":" not in req.model_ref:
        raise HTTPException(status_code=400, detail="model_ref must be '<provider>:<endpoint>'")
    role_norm = role.upper() if role.upper() in AGENT_REGISTRY else role
    if role_norm not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"role {role!r} not found")
    AGENT_REGISTRY[role_norm].model_ref = req.model_ref
    return SwapResponse(role=role_norm, model_ref=req.model_ref)
