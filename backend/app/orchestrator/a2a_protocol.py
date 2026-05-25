"""A2A (agent-to-agent) message protocol (§6.2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["challenge", "support", "question", "data_request", "summary", "vote"]


class A2AMessage(BaseModel):
    from_: str = Field(alias="from")
    to: str  # "ALL" | role name
    intent: Intent
    content: str
    citations: list[dict] = Field(default_factory=list)

    class Config:
        populate_by_name = True
