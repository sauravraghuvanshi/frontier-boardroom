"""attach_knowledge.py — wire the boardroom seed corpus into Foundry agents.

What it does (idempotent):

1. Mints a Foundry agent token via DefaultAzureCredential.
2. Downloads every file from the boardroom-knowledge blob container.
3. Uploads each to the project's `/openai/v1/files` endpoint (purpose=assistants).
4. Creates (or refreshes) a vector store named `boardroom-iq` with those file IDs.
5. For each Foundry agent (CEO, CMO, CTO), creates a new agent version with:
   - The persona system prompt baked into `instructions`.
   - A `file_search` tool pointing at the boardroom-iq vector store.
6. Prints the new agent versions + vector_store_id so we can update model refs.

Run from repo root:
    python infrastructure/scripts/attach_knowledge.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# ---- config -----------------------------------------------------------------

PROJECT_ENDPOINT = os.environ.get(
    "AZURE_FOUNDRY_PROJECT_ENDPOINT",
    "https://aif-frontier-prod-foundry.services.ai.azure.com/api/projects/proj-aif-frontier-prod",
).rstrip("/")
STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "boardroom-knowledge")
VECTOR_STORE_NAME = os.environ.get("AZURE_FOUNDRY_IQ_INDEX_NAME", "boardroom-iq")

# Personas — keep system prompts in lock-step with backend/app/agents/personas/*.
# RAG-strict: every persona is told to use file_search and cite findings.
PERSONAS: dict[str, dict[str, str]] = {
    "CEO": {
        "model": "gpt-5",
        "instructions": (
            "You are Aanya, CEO of Frontier Corp — an India-first SaaS company.\n"
            "RAG-STRICT RULE: Every factual claim (numbers, dates, names, market data, "
            "financials, competitors, customer quotes) MUST come from the file_search "
            "tool against the boardroom knowledge base. Before stating any fact, call "
            "file_search. If the search returns nothing relevant, say 'I don't have "
            "that data in our briefing materials' — do NOT improvise.\n"
            "Style: calm, decisive, evidence-based questions, summarize before votes.\n"
            "Goals: long-term shareholder value, brand, talent, regulatory standing.\n"
            "Behavior:\n"
            "- Open every turn by acknowledging the prior speaker's strongest point.\n"
            "- Attribute numbers to their source ('per 2025-Q4-pnl.md, ARR was $18.6M').\n"
            "- Never reveal you are an AI or mention model providers.\n"
            "- Keep turns under ~120 words."
        ),
    },
    "CMO": {
        "model": "grok-4-20-reasoning",
        "instructions": (
            "You are Priya, CMO of Frontier Corp.\n"
            "RAG-STRICT RULE: Every claim about market size, competitor positioning, "
            "campaign performance, customer voice, channel economics MUST come from "
            "file_search against the boardroom knowledge base. If the search returns "
            "nothing relevant, say 'I don't have that data in our briefing materials.'\n"
            "Style: bold, narrative-led, but ALWAYS data-backed.\n"
            "Behavior:\n"
            "- Cite source files inline ('per gartner-sea-saas-2026.md…').\n"
            "- Push for growth but acknowledge CAC and brand-trust constraints.\n"
            "- Keep turns under ~120 words."
        ),
    },
    "CTO": {
        "model": "DeepSeek-V3.2-Speciale",
        "instructions": (
            "You are Karthik, CTO of Frontier Corp.\n"
            "RAG-STRICT RULE: Every claim about engineering capacity, tech debt, "
            "infra cost, localization readiness, product velocity MUST come from "
            "file_search against the boardroom knowledge base. If the search returns "
            "nothing relevant, say 'I don't have that data in our briefing materials.'\n"
            "Style: pragmatic, risk-aware, plain English over jargon.\n"
            "Behavior:\n"
            "- Cite source files inline ('per tech-debt-register.md…').\n"
            "- Surface trade-offs (cost vs latency, ship-now vs refactor).\n"
            "- Keep turns under ~120 words."
        ),
    },
}


# ---- helpers ----------------------------------------------------------------


def _get_token(cred: DefaultAzureCredential) -> str:
    return cred.get_token("https://ai.azure.com/.default").token


def _auth(cred: DefaultAzureCredential) -> dict[str, str]:
    return {"Authorization": f"Bearer {_get_token(cred)}"}


def _download_blobs(local_dir: Path) -> list[Path]:
    cred = DefaultAzureCredential()
    svc = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=cred,
    )
    container = svc.get_container_client(CONTAINER)
    local_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for blob in container.list_blobs():
        # Skip the MANIFEST itself — it's metadata not knowledge.
        if blob.name.lower().endswith("manifest.json"):
            continue
        target = local_dir / blob.name.replace("/", "__")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as fh:
            stream = container.download_blob(blob.name)
            fh.write(stream.readall())
        paths.append(target)
        print(f"  downloaded {blob.name} -> {target.name}")
    return paths


def _list_existing_files(client: httpx.Client, cred: DefaultAzureCredential) -> dict[str, str]:
    url = f"{PROJECT_ENDPOINT}/openai/v1/files?purpose=assistants&limit=1000"
    r = client.get(url, headers=_auth(cred), timeout=30)
    r.raise_for_status()
    return {f.get("filename"): f["id"] for f in r.json().get("data", [])}


def _upload_file(client: httpx.Client, cred: DefaultAzureCredential, path: Path) -> str:
    url = f"{PROJECT_ENDPOINT}/openai/v1/files"
    with path.open("rb") as fh:
        files = {"file": (path.name, fh, "application/octet-stream")}
        data = {"purpose": "assistants"}
        r = client.post(url, headers=_auth(cred), files=files, data=data, timeout=60)
    r.raise_for_status()
    return r.json()["id"]


def _create_vector_store(
    client: httpx.Client, cred: DefaultAzureCredential, file_ids: list[str]
) -> str:
    list_url = f"{PROJECT_ENDPOINT}/openai/v1/vector_stores"
    vs_id: str | None = None
    r = client.get(list_url, headers=_auth(cred), timeout=30)
    r.raise_for_status()
    for vs in r.json().get("data", []):
        if vs.get("name") == VECTOR_STORE_NAME:
            vs_id = vs["id"]
            print(f"  reusing existing vector store: {vs_id}")
            break

    if vs_id is None:
        r = client.post(
            list_url,
            headers={**_auth(cred), "Content-Type": "application/json"},
            json={"name": VECTOR_STORE_NAME},
            timeout=60,
        )
        if r.status_code >= 400:
            print(f"  [ERROR] vector store create: {r.status_code} {r.text}")
            r.raise_for_status()
        vs_id = r.json()["id"]
        print(f"  created empty vector store: {vs_id}")

    # Attach files one by one (bulk file_ids on create returns 400 on this endpoint).
    print(f"  attaching {len(file_ids)} files…")
    for fid in file_ids:
        ar = client.post(
            f"{list_url}/{vs_id}/files",
            headers={**_auth(cred), "Content-Type": "application/json"},
            json={"file_id": fid},
            timeout=30,
        )
        if ar.status_code >= 400:
            # 409 = already attached; OK on re-runs.
            if ar.status_code != 409:
                print(f"    [WARN] attach {fid}: {ar.status_code} {ar.text[:160]}")
    return vs_id


def _poll_vector_store(
    client: httpx.Client, cred: DefaultAzureCredential, vs_id: str, *, timeout_s: int = 900
) -> str:
    url = f"{PROJECT_ENDPOINT}/openai/v1/vector_stores/{vs_id}"
    deadline = time.time() + timeout_s
    last = ""
    while time.time() < deadline:
        r = client.get(url, headers=_auth(cred), timeout=30)
        r.raise_for_status()
        body = r.json()
        status = body.get("status", "unknown")
        counts = body.get("file_counts", {})
        msg = f"status={status} files={counts}"
        if msg != last:
            print(f"  vector store: {msg}")
            last = msg
        if status in ("completed", "ready", "succeeded"):
            return status
        if status in ("failed", "cancelled", "expired"):
            raise RuntimeError(f"vector store entered terminal state: {status}")
        time.sleep(10)
    return "timeout"


def _create_agent_version(
    client: httpx.Client,
    cred: DefaultAzureCredential,
    *,
    agent_name: str,
    model: str,
    instructions: str,
    vector_store_id: str,
) -> dict[str, Any]:
    # New version on existing agent → POST /agents/{name}/versions.
    # First-time create (404) → POST /agents.
    versions_url = f"{PROJECT_ENDPOINT}/agents/{agent_name}/versions?api-version=v1"
    payload = {
        "definition": {
            "kind": "prompt",
            "model": model,
            "instructions": instructions,
            "tools": [
                {
                    "type": "file_search",
                    "vector_store_ids": [vector_store_id],
                    "max_num_results": 12,
                }
            ],
        },
    }
    r = client.post(
        versions_url,
        headers={**_auth(cred), "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if r.status_code == 404:
        create_url = f"{PROJECT_ENDPOINT}/agents?api-version=v1"
        full_payload = {"name": agent_name, **payload}
        r = client.post(
            create_url,
            headers={**_auth(cred), "Content-Type": "application/json"},
            json=full_payload,
            timeout=60,
        )
    if r.status_code >= 400:
        print(f"  [ERROR] agent {agent_name} create failed: {r.status_code} {r.text}")
        r.raise_for_status()
    return r.json()


# ---- orchestration ----------------------------------------------------------


def main() -> int:
    print(f"Project endpoint: {PROJECT_ENDPOINT}")
    print(f"Blob source     : {STORAGE_ACCOUNT}/{CONTAINER}")
    print(f"Vector store    : {VECTOR_STORE_NAME}")
    print()

    cred = DefaultAzureCredential()

    tmp = Path(__file__).parent / ".attach_knowledge_tmp"
    print("Step 1/5  Downloading blobs…")
    files = _download_blobs(tmp)
    print(f"  {len(files)} files staged locally")

    with httpx.Client() as client:
        print("\nStep 2/5  Uploading to Foundry files endpoint…")
        existing = _list_existing_files(client, cred)
        print(f"  {len(existing)} files already on project; will reuse by filename")
        file_ids: list[str] = []
        for p in files:
            if p.name in existing:
                fid = existing[p.name]
                file_ids.append(fid)
                print(f"  {p.name} -> {fid} (reused)")
                continue
            try:
                fid = _upload_file(client, cred, p)
                file_ids.append(fid)
                print(f"  {p.name} -> {fid}")
            except httpx.HTTPStatusError as e:
                print(f"  [WARN] upload failed for {p.name}: {e.response.status_code} {e.response.text[:200]}")

        if not file_ids:
            print("[FATAL] no files uploaded; aborting.")
            return 2

        print(f"\nStep 3/5  Creating/refreshing vector store '{VECTOR_STORE_NAME}'…")
        vs_id = _create_vector_store(client, cred, file_ids)
        print(f"  vector_store_id = {vs_id}")

        print("\nStep 4/5  Polling for ingestion…")
        status = _poll_vector_store(client, cred, vs_id)
        print(f"  final status: {status}")

        print("\nStep 5/5  Creating agent versions with file_search attached…")
        results: dict[str, Any] = {"vector_store_id": vs_id, "agents": {}}
        for agent_name, spec in PERSONAS.items():
            print(f"  -> {agent_name} (model={spec['model']})")
            try:
                created = _create_agent_version(
                    client,
                    cred,
                    agent_name=agent_name,
                    model=spec["model"],
                    instructions=spec["instructions"],
                    vector_store_id=vs_id,
                )
                version = created.get("version") or created.get("agent_version") or "?"
                results["agents"][agent_name] = {
                    "name": created.get("name", agent_name),
                    "version": version,
                }
                print(f"     created version: {version}")
            except Exception as e:  # noqa: BLE001
                results["agents"][agent_name] = {"error": str(e)}
                print(f"     [ERROR] {e}")

    out = Path(__file__).parent / "attach_knowledge.result.json"
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nDone. Wrote {out}")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
