"""Databricks Mosaic AI provider — Claude lives here, NOT in Foundry.

Calls the OpenAI-compatible chat-completions API at:
  {DATABRICKS_HOST}/serving-endpoints/{endpoint}/invocations
With SSE streaming.
"""

from __future__ import annotations

import json
import os
import time
from typing import AsyncIterator, Sequence

import httpx

from .base import BaseProvider, ChatMessage


class DatabricksProvider(BaseProvider):
    name = "databricks"

    def __init__(self) -> None:
        host = os.environ.get("DATABRICKS_HOST", "").strip().rstrip("/")
        if host and not host.startswith(("http://", "https://")):
            host = f"https://{host}"
        self.host = host
        self.token = os.environ.get("DATABRICKS_TOKEN", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def stream_chat(
        self,
        endpoint: str,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.4,
        max_tokens: int = 800,
    ) -> AsyncIterator[str]:
        if not self.host or not self.token:
            # TODO(plan): swap in real creds; role-aware stub for offline dev.
            from ._stub import stub_role_stream

            async for tok in stub_role_stream("databricks", endpoint, messages):
                yield tok
            return

        url = f"{self.host}/serving-endpoints/{endpoint}/invocations"
        body = {
            "messages": [dict(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=self._headers(), json=body) as resp:
                resp.raise_for_status()
                async for raw in resp.aiter_lines():
                    if not raw or not raw.startswith("data:"):
                        continue
                    data = raw[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for ch in chunk.get("choices", []):
                        delta = ch.get("delta", {})
                        text = delta.get("content")
                        if text:
                            yield text

    async def probe(self, endpoint: str) -> dict:
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
