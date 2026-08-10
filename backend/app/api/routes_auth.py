"""Authenticated session metadata supplied by Azure App Service Easy Auth."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["auth"])


class AuthSessionResponse(BaseModel):
    authenticated: bool
    user_name: str | None = None
    principal_id: str | None = None


@router.get("/auth/session", response_model=AuthSessionResponse)
async def auth_session(request: Request) -> AuthSessionResponse:
    user_name = request.headers.get("x-ms-client-principal-name")
    principal_id = request.headers.get("x-ms-client-principal-id")
    return AuthSessionResponse(
        authenticated=bool(user_name or principal_id),
        user_name=user_name,
        principal_id=principal_id,
    )
