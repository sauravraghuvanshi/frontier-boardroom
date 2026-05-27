"""Microsoft Foundry provider — calls 1st-party Foundry Agents (CEO, CMO, CTO).

Uses azure-ai-projects AIProjectClient → OpenAI client → responses.create
with `agent_reference` extra_body. Auth is managed identity only
(local-auth is disabled on the corp sub).

Model ref format: ``foundry:<AgentName>@<version>`` (e.g. ``foundry:CEO@2``).

NEVER call Anthropic through this provider — that goes through DatabricksProvider.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from typing import AsyncIterator, Sequence

from .base import BaseProvider, ChatMessage


# Endpoints whose output_text channel leaks chain-of-thought (Grok reasoning,
# DeepSeek, OpenAI o-series). We buffer their full reply and strip preamble
# before yielding. Streaming-first-token is sacrificed for these models.
_COT_PRONE = ("cmo@", "grok", "reasoning", "deepseek", "o1", "o3", "o4")

# Markers that indicate "the real answer starts here" — match at start of line.
# We keep everything from the LAST match onward (since multi-pass reasoners
# often draft a candidate, critique it, then restate the final).
_ANSWER_MARKERS = re.compile(
    r"^(?:\*\*)?(?:Priya|Final answer|Final\b|Answer|Response|Output)\b"
    r"|^(?:Priya|Maya|Daniel|Arjun|Sam)\s*\([A-Z]{2,5}\)",
    re.IGNORECASE | re.MULTILINE,
)

# Preamble lines we drop wholesale when no clear answer-marker is found.
_PREAMBLE_PATTERNS = re.compile(
    r"^(?:first,|my persona|do i need|draft\s*[:\d]|word count|rag-strict|"
    r"step \d|let me|i need to|i should|i'll|i will|the user|the question|"
    r"thinking:|reasoning:|plan:|approach:|analysis:).*$",
    re.IGNORECASE | re.MULTILINE,
)


def _is_cot_prone(endpoint: str) -> bool:
    e = endpoint.lower()
    return any(tag in e for tag in _COT_PRONE)


def _strip_cot_preamble(text: str) -> str:
    """Best-effort sanitiser for reasoning-model output_text leaks."""
    if not text:
        return text
    matches = list(_ANSWER_MARKERS.finditer(text))
    if matches:
        return text[matches[-1].start():].strip()
    cleaned = _PREAMBLE_PATTERNS.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or text.strip()

try:
    from azure.ai.projects.aio import AIProjectClient  # type: ignore
    from azure.identity.aio import DefaultAzureCredential  # type: ignore

    _SDK_OK = True
except Exception:  # noqa: BLE001
    _SDK_OK = False


_ANTHROPIC_HINTS = ("claude", "anthropic", "opus", "sonnet", "haiku")


def _parse_agent_ref(endpoint: str) -> tuple[str, str]:
    """``CEO@2`` -> (``CEO``, ``2``).  Bare ``CEO`` defaults to version ``1``."""
    if "@" in endpoint:
        name, version = endpoint.split("@", 1)
        return name.strip(), version.strip() or "1"
    return endpoint.strip(), "1"


class FoundryProvider(BaseProvider):
    name = "foundry"

    def __init__(self) -> None:
        self.project_endpoint = os.environ.get("AZURE_FOUNDRY_PROJECT_ENDPOINT", "")

    @staticmethod
    def _assert_not_anthropic(endpoint: str) -> None:
        lower = endpoint.lower()
        if any(h in lower for h in _ANTHROPIC_HINTS):
            raise RuntimeError(
                f"FoundryProvider refuses Anthropic endpoint {endpoint!r}; "
                "route Claude through DatabricksProvider."
            )

    async def stream_chat(
        self,
        endpoint: str,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> AsyncIterator[str]:
        self._assert_not_anthropic(endpoint)

        if not _SDK_OK or not self.project_endpoint:
            from ._stub import stub_role_stream

            async for tok in stub_role_stream("foundry", endpoint, messages):
                yield tok
            return

        agent_name, agent_version = _parse_agent_ref(endpoint)
        # Responses API requires each input item to carry an explicit `type`.
        # System messages aren't accepted as input items — fold them into the
        # first user message as preamble.
        input_payload: list[dict] = []
        preamble = ""
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "") or ""
            if role == "system":
                preamble = f"{preamble}\n{content}".strip()
                continue
            text = content
            if preamble and role == "user":
                text = f"{preamble}\n\n{text}"
                preamble = ""
            input_payload.append({"type": "message", "role": role, "content": text})
        if preamble:  # no user message ever appeared
            input_payload.append({"type": "message", "role": "user", "content": preamble})

        # Collapse consecutive same-role messages (e.g. user→user from peer
        # quotes + grounded_turn). gpt-5 tolerates non-alternation but
        # reasoning models on agent_reference don't always — be defensive.
        if input_payload:
            collapsed: list[dict] = [input_payload[0]]
            for item in input_payload[1:]:
                if item["role"] == collapsed[-1]["role"]:
                    collapsed[-1]["content"] = f"{collapsed[-1]['content']}\n\n{item['content']}"
                else:
                    collapsed.append(item)
            input_payload = collapsed

        cred = DefaultAzureCredential()
        try:
            async with AIProjectClient(endpoint=self.project_endpoint, credential=cred) as project:
                openai_client = project.get_openai_client()
                # If the endpoint is `Name@Version` we invoke the agent;
                # otherwise we treat it as a raw model deployment name and
                # bypass agent_reference. Used for `foundry:gpt-5` etc.
                if "@" in endpoint:
                    create_kwargs = {
                        "input": input_payload,
                        "stream": True,
                        "extra_body": {
                            "agent_reference": {
                                "name": agent_name,
                                "version": agent_version,
                                "type": "agent_reference",
                            }
                        },
                    }
                else:
                    create_kwargs = {
                        "model": endpoint,
                        "input": input_payload,
                        "stream": True,
                        "max_output_tokens": max_tokens,
                    }
                stream = await openai_client.responses.create(**create_kwargs)
                cot_prone = _is_cot_prone(endpoint)
                output_emitted = False
                reasoning_buffer: list[str] = []
                output_buffer: list[str] = []
                async for event in stream:
                    etype = getattr(event, "type", "")
                    if "reasoning" in etype or "thinking" in etype:
                        delta = getattr(event, "delta", None)
                        if isinstance(delta, str) and delta:
                            reasoning_buffer.append(delta)
                        continue
                    if etype == "response.output_text.delta":
                        delta = getattr(event, "delta", None)
                        if delta:
                            output_emitted = True
                            if cot_prone:
                                output_buffer.append(delta)
                            else:
                                yield delta
                if cot_prone and output_buffer:
                    yield _strip_cot_preamble("".join(output_buffer))
                elif not output_emitted and reasoning_buffer:
                    yield _strip_cot_preamble("".join(reasoning_buffer))
        finally:
            await cred.close()

    async def probe(self, endpoint: str) -> dict:
        try:
            self._assert_not_anthropic(endpoint)
        except RuntimeError as e:
            return {"provider": self.name, "endpoint": endpoint, "ok": False, "error": str(e)}
        t0 = time.perf_counter()
        try:
            count = 0
            async for _ in self.stream_chat(
                endpoint,
                [ChatMessage(role="user", content="ping")],
                max_tokens=4,
            ):
                count += 1
                if count >= 1:
                    break
            return {
                "provider": self.name,
                "endpoint": endpoint,
                "ok": True,
                "latency_ms": int((time.perf_counter() - t0) * 1000),
            }
        except Exception as e:  # noqa: BLE001
            return {"provider": self.name, "endpoint": endpoint, "ok": False, "error": str(e)}
