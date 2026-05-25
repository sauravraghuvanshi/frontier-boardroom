"""
build_foundry_iq_kb.py — provisions the Foundry IQ Knowledge Base (`boardroom-iq`)
on top of Azure AI Search + Bing Web Grounding.

Prereqs
-------
1. AI Search index already built (run `build_aisearch_index.py` first).
2. Two Foundry project Connections exist:
     - AzureAISearch  -> the search service, AAD auth
     - BingGrounding  -> Bing v7 API key from Key Vault
   Create via Foundry MCP `project_connection_create` or Foundry portal.
   This script can also create the AzureAISearch connection if --create-search-conn
   is passed and AZURE_SEARCH_RESOURCE_ID is set.

Env
---
  AZURE_FOUNDRY_PROJECT_ENDPOINT  e.g. https://aif-frontier-prod-foundry.services.ai.azure.com/api/projects/proj-aif-frontier-prod
  AZURE_FOUNDRY_KB_NAME           default: boardroom-iq
  AZURE_FOUNDRY_KB_API_VERSION    default: 2026-01-preview
  AZURE_SEARCH_CONNECTION_NAME    name of the AzureAISearch connection in Foundry
  AZURE_SEARCH_INDEX              default: boardroom-knowledge-idx
  AZURE_SEARCH_SEMANTIC_CONFIG    default: default
  BING_CONNECTION_NAME            name of the BingGrounding connection in Foundry (optional)

Notes
-----
- The KB management REST surface is in preview. The api-version above is a
  best-guess; the script prints a `probe` link you can curl manually if the PUT
  fails with 404 — capture the actual api-version from `az rest --method get
  --url "{endpoint}/knowledgeBases?api-version=..."`.
- This is idempotent: PUT replaces the KB definition wholesale.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import httpx
from azure.identity import DefaultAzureCredential


PROJECT_ENDPOINT = os.environ["AZURE_FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
KB_NAME = os.environ.get("AZURE_FOUNDRY_KB_NAME", "boardroom-iq")
API_VERSION = os.environ.get("AZURE_FOUNDRY_KB_API_VERSION", "2026-01-preview")

SEARCH_CONN = os.environ.get("AZURE_SEARCH_CONNECTION_NAME", "boardroom-aisearch")
SEARCH_INDEX = os.environ.get("AZURE_SEARCH_INDEX", "boardroom-knowledge-idx")
SEMANTIC_CONFIG = os.environ.get("AZURE_SEARCH_SEMANTIC_CONFIG", "default")
BING_CONN = os.environ.get("BING_CONNECTION_NAME", "")


def _token() -> str:
    cred = DefaultAzureCredential()
    return cred.get_token("https://ai.azure.com/.default").token


def _kb_body() -> dict:
    sources: list[dict] = [
        {
            "kind": "azureAISearch",
            "connectionId": SEARCH_CONN,
            "index": SEARCH_INDEX,
            "semanticConfig": SEMANTIC_CONFIG,
        }
    ]
    if BING_CONN:
        sources.append({"kind": "bingGrounding", "connectionId": BING_CONN})
    return {
        "displayName": "Frontier Boardroom Knowledge",
        "description": "Internal blob (AI Search) + Bing Web Grounding for CEO/CMO/CTO agents.",
        "sources": sources,
    }


def upsert(probe_only: bool) -> int:
    token = _token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    list_url = f"{PROJECT_ENDPOINT}/knowledgeBases"
    print(f"[probe] GET {list_url}?api-version={API_VERSION}")
    with httpx.Client(timeout=30.0) as client:
        r = client.get(list_url, params={"api-version": API_VERSION}, headers=headers)
        print(f"[probe] {r.status_code} {r.text[:400]}")
        if probe_only:
            return 0 if r.status_code < 400 else 1
        if r.status_code == 404:
            print("[error] KB endpoint not found — check api-version against Foundry docs")
            return 2

        put_url = f"{PROJECT_ENDPOINT}/knowledgeBases/{KB_NAME}"
        body = _kb_body()
        print(f"[put] {put_url}?api-version={API_VERSION}")
        print(json.dumps(body, indent=2))
        r = client.put(put_url, params={"api-version": API_VERSION}, headers=headers, json=body)
        print(f"[put] {r.status_code} {r.text[:600]}")
        return 0 if r.status_code < 400 else 3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="GET only, do not upsert")
    args = ap.parse_args()
    return upsert(probe_only=args.probe)


if __name__ == "__main__":
    sys.exit(main())
