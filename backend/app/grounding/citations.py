"""Citation model + helpers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_uri: str
    snippet: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    hops: int = 1
