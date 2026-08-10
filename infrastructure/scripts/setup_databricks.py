"""
setup_databricks.py — create Mosaic AI Model Serving endpoints for Anthropic Claude
Sonnet 4.5 and Claude Opus, configured as external models. Stores the Anthropic
API key in a Databricks secret scope and writes the workspace host + PAT into
Key Vault so the backend App Service can pick them up via managed identity.

Run *after* `az deployment group create` and *before* `seed_blob.py`.
"""

from __future__ import annotations

import os
import sys
import time

import httpx
from azure.identity import DefaultAzureCredential

DATABRICKS_HOST = os.environ["DATABRICKS_HOST"].rstrip("/")
DATABRICKS_TOKEN = os.environ["DATABRICKS_TOKEN"]
KEYVAULT_NAME = os.environ["KEYVAULT_NAME"]
AZURE_SUBSCRIPTION_ID = os.environ["AZURE_SUBSCRIPTION_ID"]
AZURE_RESOURCE_GROUP = os.environ["AZURE_RESOURCE_GROUP"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SECRET_SCOPE = os.environ.get("DATABRICKS_SECRET_SCOPE", "frontier-boardroom")

ENDPOINTS = [
    {"name": "claude-sonnet-4-5", "anthropic_model": "claude-sonnet-4-5"},
    {"name": "claude-opus-4", "anthropic_model": "claude-opus-4-20250514"},
]

_headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}", "Content-Type": "application/json"}


def _api(method: str, path: str, json: dict | None = None) -> dict:
    url = f"{DATABRICKS_HOST}/api/2.0/{path}"
    r = httpx.request(method, url, headers=_headers, json=json, timeout=60)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path} → {r.status_code} {r.text}")
    return r.json() if r.content else {}


def ensure_secret_scope() -> None:
    try:
        _api(
            "POST",
            "secrets/scopes/create",
            {"scope": SECRET_SCOPE, "scope_backend_type": "DATABRICKS"},
        )
        print(f"created secret scope {SECRET_SCOPE}")
    except RuntimeError as e:
        if "already exists" not in str(e).lower():
            raise


def put_anthropic_secret() -> None:
    _api(
        "POST",
        "secrets/put",
        {"scope": SECRET_SCOPE, "key": "anthropic-api-key", "string_value": ANTHROPIC_API_KEY},
    )
    print("wrote anthropic-api-key into Databricks secret scope")


def ensure_endpoint(name: str, anthropic_model: str) -> None:
    body = {
        "name": name,
        "config": {
            "served_entities": [
                {
                    "name": name,
                    "external_model": {
                        "name": anthropic_model,
                        "provider": "anthropic",
                        "task": "llm/v1/chat",
                        "anthropic_config": {
                            "anthropic_api_key": (
                                "{{secrets/" + SECRET_SCOPE + "/anthropic-api-key}}"
                            ),
                        },
                    },
                }
            ]
        },
    }
    try:
        _api("POST", "serving-endpoints", body)
        print(f"created serving endpoint {name}")
    except RuntimeError as e:
        if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
            _api(
                "PUT",
                f"serving-endpoints/{name}/config",
                {"served_entities": body["config"]["served_entities"]},
            )
            print(f"updated serving endpoint {name}")
        else:
            raise


def wait_ready(name: str, timeout_s: int = 600) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        info = _api("GET", f"serving-endpoints/{name}")
        state = (info.get("state") or {}).get("ready", "")
        if state == "READY":
            print(f"endpoint {name} READY")
            return
        print(f"endpoint {name} state={state}, waiting…")
        time.sleep(15)
    raise TimeoutError(f"endpoint {name} never became READY")


def smoke_test(name: str) -> None:
    url = f"{DATABRICKS_HOST}/serving-endpoints/{name}/invocations"
    r = httpx.post(
        url,
        headers=_headers,
        json={
            "messages": [{"role": "user", "content": "Reply with the single word: pong."}],
            "max_tokens": 8,
        },
        timeout=30,
    )
    r.raise_for_status()
    print(f"smoke ✓ {name}: {r.json()['choices'][0]['message']['content'][:40]!r}")


def write_kv() -> None:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default").token
    base_url = (
        "https://management.azure.com"
        f"/subscriptions/{AZURE_SUBSCRIPTION_ID}"
        f"/resourceGroups/{AZURE_RESOURCE_GROUP}"
        f"/providers/Microsoft.KeyVault/vaults/{KEYVAULT_NAME}/secrets"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    for name, value in (
        ("databricks-host", DATABRICKS_HOST),
        ("databricks-token", DATABRICKS_TOKEN),
    ):
        response = httpx.put(
            f"{base_url}/{name}",
            params={"api-version": "2023-07-01"},
            headers=headers,
            json={"properties": {"value": value}},
            timeout=30,
        )
        response.raise_for_status()
    print(f"wrote databricks-host + databricks-token into {KEYVAULT_NAME}")


def main() -> int:
    ensure_secret_scope()
    put_anthropic_secret()
    for ep in ENDPOINTS:
        ensure_endpoint(ep["name"], ep["anthropic_model"])
    for ep in ENDPOINTS:
        wait_ready(ep["name"])
        smoke_test(ep["name"])
    write_kv()
    print("setup_databricks: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
