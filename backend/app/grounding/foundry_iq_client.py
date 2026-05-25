"""FoundryIQ agentic-RAG client (§6.5).

All knowledge retrieval flows through `retrieve()`. When configured, this calls
the Azure AI Search **Knowledge Base** retrieve endpoint (the GA agentic
retrieval API). The Foundry agents (CEO/CMO/CTO) reach the SAME KB natively
through their `knowledge` tool attachment — this client exists so the central
orchestrator can build the briefing block that's prepended to every Databricks
persona's user turn (CFO, Legal — they can't reach Foundry IQ directly).

When offline / no creds / endpoint missing, falls back to a manifest stub so
the boardroom never goes silent.

Migrated 2026-05-25 from `/openai/v1/responses` + `file_search` against a
hardcoded vector_store_id to the AI Search KB retrieve endpoint
(`{search}/knowledgebases('{kb}')/retrieve?api-version=2026-04-01`).
Token scope: `https://search.azure.com/.default`. Request body uses the GA
`intents` shape; preview-only `messages` is rejected by 2026-04-01.
"""

from __future__ import annotations

import json
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import httpx

from ..config import get_settings
from ..telemetry import get_logger
from .citations import Citation

log = get_logger("foundry_iq")

try:
    from azure.identity import DefaultAzureCredential  # type: ignore

    _AZ_OK = True
except Exception:  # noqa: BLE001
    _AZ_OK = False


@lru_cache(maxsize=1)
def _local_manifest() -> list[dict[str, Any]]:
    p = Path(__file__).parents[2] / "data" / "sample_seed" / "MANIFEST.json"
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                return raw
            if isinstance(raw, dict):
                return raw.get("sources", []) or []
        except Exception:  # noqa: BLE001
            pass
    return []


_PERSONA_BIAS = {
    "CEO": ("strategy", "market"),
    "CFO": ("financials", "market"),
    "CMO": ("marketing", "market", "competition"),
    "CTO": ("product",),
    "Legal": ("legal", "hr"),
}


_TOKEN: dict[str, Any] = {"value": None, "exp": 0.0}


def _get_token() -> str | None:
    if not _AZ_OK:
        return None
    now = time.time()
    if _TOKEN["value"] and _TOKEN["exp"] - 60 > now:
        return _TOKEN["value"]
    try:
        cred = DefaultAzureCredential()
        tok = cred.get_token("https://search.azure.com/.default")
        _TOKEN["value"] = tok.token
        _TOKEN["exp"] = float(tok.expires_on)
        return tok.token
    except Exception as e:  # noqa: BLE001
        log.warning("foundry_iq: token acquisition failed: %s", e)
        return None


_KB_API_VERSION = os.environ.get("AZURE_FOUNDRY_KB_API_VERSION", "2026-04-01")


def _parse_response(body: dict) -> list[dict]:
    """Pull docs out of the KB retrieve response.

    `references[]` is the structured shape; each item carries `sourceData` with
    the index field values plus `docKey` and `rerankerScore`. We prefer it.
    Fall back to parsing the JSON-encoded grounding string under `response[].content[].text`.
    """
    refs = body.get("references")
    if isinstance(refs, list) and refs:
        out = []
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            sd = ref.get("sourceData") or {}
            snippet = sd.get("content") or sd.get("text") or ""
            source = sd.get("source_uri") or sd.get("title") or ref.get("docKey") or "boardroom-iq"
            try:
                score = float(ref.get("rerankerScore", 0.7))
            except (TypeError, ValueError):
                score = 0.7
            # Search reranker scores are 0-4; normalize to 0-1.
            confidence = max(0.0, min(1.0, score / 4.0)) if score > 1.0 else score
            out.append({"snippet": str(snippet)[:480], "source_uri": str(source), "confidence": confidence})
        if out:
            return out

    # Fallback: parse the grounding text string.
    resp = body.get("response") or []
    if isinstance(resp, list):
        for msg in resp:
            content = (msg or {}).get("content") or []
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    txt = c.get("text") or ""
                    try:
                        items = json.loads(txt) if txt else []
                    except (ValueError, TypeError):
                        items = []
                    if isinstance(items, list):
                        return [
                            {
                                "snippet": str((it or {}).get("content") or "")[:480],
                                "source_uri": str((it or {}).get("title") or (it or {}).get("source_uri") or "boardroom-iq"),
                                "confidence": 0.7,
                            }
                            for it in items
                            if isinstance(it, dict)
                        ]
    return []


async def retrieve(*, query: str, persona: str, k: int = 3) -> list[dict]:
    s = get_settings()
    search_endpoint = (
        getattr(s, "azure_search_endpoint", "")
        or os.environ.get("AZURE_SEARCH_ENDPOINT", "")
    ).rstrip("/")
    kb_name = getattr(s, "azure_foundry_kb_name", "") or os.environ.get(
        "AZURE_FOUNDRY_KB_NAME", "boardroom-iq"
    )
    ks_name = getattr(s, "azure_search_knowledge_source", "") or os.environ.get(
        "AZURE_SEARCH_KNOWLEDGE_SOURCE", "boardroom-knowledge-ks"
    )
    if not search_endpoint or not kb_name:
        return _stub_retrieve(query=query, persona=persona, k=k)

    token = _get_token()
    if not token:
        return _stub_retrieve(query=query, persona=persona, k=k)

    url = f"{search_endpoint}/knowledgebases('{kb_name}')/retrieve"
    payload: dict[str, Any] = {
        "intents": [{"type": "semantic", "search": query}],
        "maxOutputSizeInTokens": 8000,
        "includeActivity": False,
        "knowledgeSourceParams": [
            {
                "kind": "searchIndex",
                "knowledgeSourceName": ks_name,
                "includeReferences": True,
                "includeReferenceSourceData": True,
            }
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                url,
                params={"api-version": _KB_API_VERSION},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if r.status_code >= 400:
            log.warning(
                "foundry_iq: kb.retrieve %s -> %s %s",
                url,
                r.status_code,
                r.text[:200],
            )
            return _stub_retrieve(query=query, persona=persona, k=k)
        body = r.json() if r.content else {}
        hits = _parse_response(body if isinstance(body, dict) else {})
        out: list[dict] = []
        for hit in hits[:k]:
            snippet = hit.get("snippet") or f"{persona} reference for: {query}"
            out.append(
                Citation(
                    source_uri=hit.get("source_uri", "boardroom-iq"),
                    snippet=snippet,
                    confidence=float(hit.get("confidence", 0.7)),
                    hops=1,
                ).model_dump()
            )
        if not out:
            return _stub_retrieve(query=query, persona=persona, k=k)
        log.info("foundry_iq: kb.retrieve ok kb=%s hits=%d", kb_name, len(out))
        return out
    except Exception as e:  # noqa: BLE001
        log.warning("foundry_iq: kb.retrieve failed (%s); using stub", e)
        return _stub_retrieve(query=query, persona=persona, k=k)


def _stub_retrieve(*, query: str, persona: str, k: int) -> list[dict]:
    bias = _PERSONA_BIAS.get(persona, ("market",))
    manifest = _local_manifest()
    pool = [
        s
        for s in manifest
        if (s.get("owner") in bias or any(t in bias for t in (s.get("tags") or [])))
    ] or manifest
    out: list[dict] = []
    for src in pool[:k]:
        out.append(
            Citation(
                source_uri=src.get("uri") or src.get("path", "stub://"),
                snippet=src.get("summary") or src.get("title", f"{persona} reference for: {query}"),
                confidence=0.55,
                hops=1,
            ).model_dump()
        )
    while len(out) < k:
        out.append(
            Citation(
                source_uri=f"stub://{persona.lower()}/{len(out)}",
                snippet=f"Synthetic {persona} grounding for query: {query}",
                confidence=0.4,
                hops=1,
            ).model_dump()
        )
    return out


def configured() -> bool:
    s = get_settings()
    return bool(
        getattr(s, "azure_search_endpoint", "")
        and getattr(s, "azure_foundry_kb_name", "")
    )
