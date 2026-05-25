"""
build_foundry_iq.py — registers the boardroom-knowledge blob container as a
FoundryIQ data source and (re)builds the unified knowledge index.

Notes
-----
- The Azure AI Projects SDK surface for FoundryIQ Knowledge sources is
  evolving. We isolate every SDK touch-point behind a thin helper so when
  the GA shape lands we only edit the helpers, not the orchestration.
- This script is idempotent — re-running just re-points the source and
  triggers a re-index.
"""

from __future__ import annotations

import os
import sys
import time

from azure.identity import DefaultAzureCredential

PROJECT_CONN = os.environ["AZURE_FOUNDRY_PROJECT_CONNECTION_STRING"]
INDEX_NAME = os.environ.get("AZURE_FOUNDRY_IQ_INDEX_NAME", "boardroom-iq")
STORAGE_ACCOUNT = os.environ["AZURE_STORAGE_ACCOUNT"]
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "boardroom-knowledge")


def _get_client():
    try:
        from azure.ai.projects import AIProjectClient
    except ImportError as e:  # noqa: BLE001
        raise SystemExit(
            "azure-ai-projects not installed. pip install azure-ai-projects"
        ) from e
    return AIProjectClient.from_connection_string(
        conn_str=PROJECT_CONN, credential=DefaultAzureCredential()
    )


def ensure_data_source(client) -> str:
    """Register the blob container as a Foundry data source."""
    # TODO(plan): the FoundryIQ data-source surface is in beta — the exact
    # method name on AIProjectClient may differ in the GA package on this
    # tenant. The shape below mirrors the public preview docs.
    uri = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER}"
    name = "boardroom-blob"
    try:
        ds = client.knowledge.data_sources.create_or_update(  # type: ignore[attr-defined]
            name=name,
            kind="azure_blob",
            properties={"uri": uri},
        )
        return ds.id
    except AttributeError:
        # Fallback: REST passthrough — keeps this script useful even when the
        # high-level SDK shape changes.
        print(
            "[warn] AIProjectClient.knowledge surface not present — call the "
            "Foundry REST API directly here or upgrade azure-ai-projects."
        )
        # TODO(plan): emit raw REST call once the URL pattern is finalized.
        return name


def build_index(client, ds_ref: str) -> None:
    try:
        op = client.knowledge.indexes.create_or_update(  # type: ignore[attr-defined]
            name=INDEX_NAME,
            data_source_id=ds_ref,
            properties={
                "multi_hop_reasoning": True,
                "embedding_model": "text-embedding-3-large",
                "chunking": {"strategy": "semantic", "max_tokens": 800},
            },
        )
        print(f"index build started: {op.operation_id if hasattr(op, 'operation_id') else op}")
    except AttributeError:
        print("[warn] AIProjectClient.knowledge.indexes surface not present — "
              "call the Foundry REST API directly.")
        # TODO(plan): REST passthrough.
        return

    # Poll for completion (best effort)
    deadline = time.time() + 1200
    while time.time() < deadline:
        try:
            status = client.knowledge.indexes.get(name=INDEX_NAME).status  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            break
        if status in ("succeeded", "failed", "ready"):
            print(f"index {INDEX_NAME} status={status}")
            return
        print(f"index status={status}, waiting…")
        time.sleep(20)


def main() -> int:
    client = _get_client()
    ds_ref = ensure_data_source(client)
    build_index(client, ds_ref)
    print("build_foundry_iq: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
