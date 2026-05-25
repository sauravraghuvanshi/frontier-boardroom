"""WebSocket event protocol (§7.3). Pydantic models for every emit shape."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "turn_start", "token", "citation", "turn_end",
    "mood", "viseme", "audio_chunk", "debate_end",
    "tool_call", "error",
]


class TurnStartEvent(BaseModel):
    type: Literal["turn_start"] = "turn_start"
    agent: str
    model: str
    timestamp: float


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    agent: str
    text: str


class CitationEvent(BaseModel):
    type: Literal["citation"] = "citation"
    agent: str
    source_uri: str
    snippet: str
    confidence: float = 0.0
    hops: int = 1


class TurnEndEvent(BaseModel):
    type: Literal["turn_end"] = "turn_end"
    agent: str
    duration_ms: int
    tokens: int = 0


class MoodEvent(BaseModel):
    type: Literal["mood"] = "mood"
    value: float = Field(ge=0.0, le=1.0)
    label: Literal["cordial", "debating", "heated", "converging", "resolved"]


class VisemeEvent(BaseModel):
    type: Literal["viseme"] = "viseme"
    agent: str
    frames: list[dict]  # [{visemeId:int, offset_ms:int}]


class AudioChunkEvent(BaseModel):
    type: Literal["audio_chunk"] = "audio_chunk"
    agent: str
    base64: str


class ToolCallEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    agent: str
    tool: str
    args: dict


class DebateEndEvent(BaseModel):
    type: Literal["debate_end"] = "debate_end"
    decision: str
    vote: dict[str, str]


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
