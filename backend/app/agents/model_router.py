"""Model router — single chokepoint for all model calls.

Parses '<provider>:<endpoint>' refs and delegates to the right provider.
NEVER bypass this router. NEVER call Anthropic through Foundry.

CLI:
    python -m app.agents.model_router probe
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator, Sequence

from ..config import get_settings
from .providers.base import BaseProvider, ChatMessage
from .providers.databricks_provider import DatabricksProvider
from .providers.fake_provider import FakeProvider
from .providers.foundry_provider import FoundryProvider

_PROVIDERS: dict[str, BaseProvider] = {
    "foundry": FoundryProvider(),
    "databricks": DatabricksProvider(),
    "fake": FakeProvider(),
}


def _split(ref: str) -> tuple[str, str]:
    if ":" not in ref:
        raise ValueError(f"model_ref {ref!r} must be '<provider>:<endpoint>'")
    provider, endpoint = ref.split(":", 1)
    provider = provider.strip().lower()
    if provider not in _PROVIDERS:
        raise ValueError(f"unknown provider {provider!r} (expected one of {list(_PROVIDERS)})")
    return provider, endpoint.strip()


async def stream_chat(
    model_ref: str,
    messages: Sequence[ChatMessage],
    *,
    temperature: float = 0.4,
    max_tokens: int = 800,
) -> AsyncIterator[str]:
    provider, endpoint = _split(model_ref)
    async for tok in _PROVIDERS[provider].stream_chat(
        endpoint, messages, temperature=temperature, max_tokens=max_tokens
    ):
        yield tok


async def probe_all() -> dict:
    settings = get_settings()
    out: dict = {"results": []}
    for role, ref in settings.model_registry().items():
        try:
            provider, endpoint = _split(ref)
            res = await _PROVIDERS[provider].probe(endpoint)
        except Exception as e:  # noqa: BLE001
            res = {"provider": "?", "endpoint": ref, "ok": False, "error": str(e)}
        res["role"] = role
        res["model_ref"] = ref
        out["results"].append(res)
    out["ok"] = all(r.get("ok") for r in out["results"])
    return out


def _main() -> None:
    import json
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "probe":
        print(json.dumps(asyncio.run(probe_all()), indent=2))
        return
    print("usage: python -m app.agents.model_router probe")


if __name__ == "__main__":
    _main()
