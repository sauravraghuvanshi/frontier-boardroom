"""Provision the single-tenant Entra registration used by App Service Easy Auth.

The generated client secret is never printed or written to disk. It is sent
directly to the existing private Key Vault through the ARM management plane.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx
from azure.identity import AzureCliCredential

APP_DISPLAY_NAME = "Frontier Boardroom Production"
AUTH_SECRET_NAME = "appservice-auth-client-secret"


def _az_json(*args: str) -> Any:
    result = subprocess.run(
        ["az", *args, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class AzureClients:
    def __init__(self, tenant_id: str) -> None:
        credential = AzureCliCredential(tenant_id=tenant_id)
        self._graph_token = credential.get_token(
            "https://graph.microsoft.com/.default"
        ).token
        self._arm_token = credential.get_token(
            "https://management.azure.com/.default"
        ).token

    def graph(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        response = httpx.request(
            method,
            f"https://graph.microsoft.com/v1.0{path}",
            headers={
                "Authorization": f"Bearer {self._graph_token}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    def put_secret(
        self,
        *,
        subscription_id: str,
        resource_group: str,
        vault_name: str,
        secret_name: str,
        value: str,
    ) -> None:
        url = (
            "https://management.azure.com"
            f"/subscriptions/{subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.KeyVault/vaults/{vault_name}"
            f"/secrets/{secret_name}"
        )
        response = httpx.put(
            url,
            params={"api-version": "2023-07-01"},
            headers={
                "Authorization": f"Bearer {self._arm_token}",
                "Content-Type": "application/json",
            },
            json={"properties": {"value": value}},
            timeout=60,
        )
        response.raise_for_status()


def ensure_application(
    clients: AzureClients,
    *,
    frontend_url: str,
) -> tuple[dict[str, Any], bool]:
    escaped_name = APP_DISPLAY_NAME.replace("'", "''")
    query = quote(f"displayName eq '{escaped_name}'")
    matches = clients.graph("GET", f"/applications?$filter={query}").get("value", [])
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple app registrations named {APP_DISPLAY_NAME!r} exist; refusing to guess."
        )

    web = {
        "homePageUrl": frontend_url,
        "logoutUrl": f"{frontend_url}/.auth/logout",
        "redirectUris": [
            f"{frontend_url}/.auth/login/aad/callback",
        ],
    }
    if matches:
        application = matches[0]
        clients.graph(
            "PATCH",
            f"/applications/{application['id']}",
            {"signInAudience": "AzureADMyOrg", "web": web},
        )
        application = clients.graph("GET", f"/applications/{application['id']}")
        created = False
    else:
        application = clients.graph(
            "POST",
            "/applications",
            {
                "displayName": APP_DISPLAY_NAME,
                "signInAudience": "AzureADMyOrg",
                "api": {"requestedAccessTokenVersion": 2},
                "requiredResourceAccess": [],
                "web": web,
            },
        )
        created = True

    app_id = application["appId"]
    principals = clients.graph(
        "GET", f"/servicePrincipals?$filter={quote(f'appId eq {app_id!r}')}"
    ).get("value", [])
    if not principals:
        clients.graph("POST", "/servicePrincipals", {"appId": app_id})
    return application, created


def rotate_secret(clients: AzureClients, application_id: str) -> str:
    expires = datetime.now(UTC) + timedelta(days=180)
    result = clients.graph(
        "POST",
        f"/applications/{application_id}/addPassword",
        {
            "passwordCredential": {
                "displayName": "App Service Easy Auth",
                "endDateTime": expires.isoformat().replace("+00:00", "Z"),
            }
        },
    )
    return str(result["secretText"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="prod")
    parser.add_argument(
        "--rotate-secret",
        action="store_true",
        help="Create a new 180-day credential and replace the Key Vault secret.",
    )
    args = parser.parse_args()

    account = _az_json("account", "show")
    subscription_id = account["id"]
    tenant_id = account["tenantId"]
    resource_group = f"rg-frontier-boardroom-{args.environment}"
    prefix = f"frontier-{args.environment}"
    frontend_url = f"https://app-{prefix}-frontend.azurewebsites.net"

    vaults = _az_json("keyvault", "list", "--resource-group", resource_group)
    if len(vaults) != 1:
        raise RuntimeError(
            f"Expected exactly one Key Vault in {resource_group}, found {len(vaults)}."
        )

    clients = AzureClients(tenant_id)
    application, created = ensure_application(
        clients,
        frontend_url=frontend_url,
    )
    if created or args.rotate_secret:
        secret = rotate_secret(clients, application["id"])
        clients.put_secret(
            subscription_id=subscription_id,
            resource_group=resource_group,
            vault_name=vaults[0]["name"],
            secret_name=AUTH_SECRET_NAME,
            value=secret,
        )
        print(f"Stored a new Easy Auth credential in {vaults[0]['name']}.")
    else:
        print("Reused the existing app registration without rotating its credential.")

    print(f"ENTRA_TENANT_ID={tenant_id}")
    print(f"ENTRA_CLIENT_ID={application['appId']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
