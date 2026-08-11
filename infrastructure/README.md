# Frontier Boardroom - Infrastructure

Production application releases are automated:

1. A push to `master` runs `.github/workflows/ci.yml`.
2. Successful push CI triggers `.github/workflows/deploy-app.yml`.
3. ACR builds immutable backend and frontend images tagged with the tested commit SHA.
4. The workflow confirms the SHA is still the tip of `master` before building and
   again before changing production.
5. App Service is pinned to those SHA-tagged images and the workflow verifies
   health and protected-route behavior.

Fork pull requests cannot enter the production OIDC job. Manual deployment remains
available through `workflow_dispatch`.

## Full infrastructure provisioning

Use the full provisioning path only for creating or changing Azure resources:

```bash
IMAGE_TAG="$(git rev-parse HEAD)"
az group create -n rg-frontier-boardroom-dev -l centralindia
az deployment group what-if -g rg-frontier-boardroom-dev -f bicep/main.bicep \
  -p env=dev containerImageTag="$IMAGE_TAG" \
  -p adminObjectId=$(az ad signed-in-user show --query id -o tsv) \
  -p enableEntraAuth=false entraClientId=''
az deployment group create -g rg-frontier-boardroom-dev -f bicep/main.bicep \
  -p env=dev containerImageTag="$IMAGE_TAG" \
  -p adminObjectId=$(az ad signed-in-user show --query id -o tsv) \
  -p enableEntraAuth=false entraClientId='' \
  -p anthropicApiKey=$ANTHROPIC_API_KEY
```

Always pass the immutable tag you intend the App Services to run. The one-shot
script uses the current Git commit by default and builds that exact tag.

The one-shot script performs the remaining setup in order:

```bash
bash scripts/deploy.sh dev
```

`setup_databricks.py` writes the Databricks host and token through Azure Resource
Manager. This is intentional: Key Vault public access is disabled, so a
GitHub-hosted runner cannot use the vault's public data-plane endpoint.

## Production security model

- The production frontend requires single-tenant Microsoft Entra sign-in.
- Browser API and WebSocket traffic stays on the authenticated frontend origin
  and is reverse-proxied over the VNet to a private backend.
- The frontend pins App Service's VNet DNS resolver so private backend
  resolution remains stable across container restarts.
- Releases patch only the `linuxFxVersion` config resource, producing one App
  Service write per app. The backend image embeds its commit SHA; the workflow
  waits for the existing frontend proxy to report that SHA before updating the
  frontend image, then verifies the frontend's own SHA response header.
- Failed releases restore both previously pinned image references and wait for
  the prior frontend/backend pair to become healthy.
- Production verification allows a bounded 15-minute recovery window. The live
  B1 plan required about 10 minutes to restore private proxy health during the
  2026-08-11 release, exceeding the prior eight-minute window.
- Backend public network access is disabled, and the backend also rejects
  proxied requests that lack the Easy Auth principal header.
- HTTPS-only is enabled, TLS 1.2 is the minimum, HTTP/2 is enabled, and FTP/FTPS
  publishing is disabled.
- GitHub authenticates to Azure with OIDC; no Azure client secret is stored.
- App Service reads the Databricks token through a Key Vault reference.
- Key Vault public access is disabled and the backend reaches it through VNet
  integration and a private endpoint.
- Production images use immutable commit SHA tags.
- Every release validates the Bicep-declared S1 tier and fails on drift before
  replacing containers.
- Paid-model operations retain per-client/global quotas and concurrency caps as
  defense in depth after sign-in.
- Releases validate those Bicep-managed safety settings before changing images
  and fail on drift instead of recycling the backend during an app release.
- Provider probes and model swapping are unavailable publicly.
- Runtime RBAC is scoped to the individual ACR, Key Vault secret or vault,
  storage account, Search service, Speech/Language account, and Foundry project.

## Configure production Entra authentication

Create or update the single-tenant app registration and write its generated
30-day credential directly to the private Key Vault through ARM:

```bash
python infrastructure/scripts/configure_entra_auth.py \
  --environment prod \
  --rotate-secret
```

The script prints the non-secret `ENTRA_CLIENT_ID`. Use it for the infrastructure
what-if and deployment:

```bash
export ENABLE_ENTRA_AUTH=true
export ENTRA_CLIENT_ID="<application-client-id>"

az deployment group what-if \
  -g rg-frontier-boardroom-prod \
  -f infrastructure/bicep/main.bicep \
  -p env=prod \
  containerImageTag="<currently deployed commit SHA>" \
  adminObjectId="$(az ad signed-in-user show --query id -o tsv)" \
     enableEntraAuth=true \
     entraClientId="$ENTRA_CLIENT_ID" \
     runtimeSecretsReady=true
```

The registration requests no Microsoft Graph permissions. The issuer is pinned
to the subscription tenant, so tenant members and invited guests can sign in;
tokens from other tenants are rejected.

Never place model credentials in Bicep parameter files, workflow YAML, App Service
plain-text settings, documentation, or command output.

## Session record - 2026-08-09/10

Completed:

- Audited tracked files, Git history, unreachable objects, and GitHub secret
  scanning; no exposed credential was found.
- Rotated and validated the Databricks credential for Claude Sonnet and Claude
  Opus, then stored it in Key Vault.
- Added private Key Vault connectivity for the backend.
- Added public-demo quotas, concurrency controls, session ownership, and
  administrator-only sensitive routes with focused tests.
- Added GitHub OIDC CI/CD from `master` to App Service with fork and stale-release
  protections.
- Repaired clean-runner Python and frontend build issues.
- Verified automatic CI and deployment for commit `8bb8357`.
- Verified live health, protected routes, immutable images, and complete cited
  CFO/Sonnet and Legal/Opus WebSocket responses.

Key learnings:

- Key Vault trusted-service bypass does not provide App Service access in this
  topology; private endpoint plus VNet integration is required.
- Secret rotation from a hosted runner must use an allowed management-plane
  mechanism when the vault data plane is private.
- A `workflow_run` deployment must validate the source event and repository, not
  only the workflow conclusion.
- Check release freshness both before a long image build and immediately before
  production mutation.
- Invoke pytest as `python -m pytest` so imports behave consistently on clean
  Linux runners.
- Local container tooling is not required for authoritative validation when ACR
  no-push builds are available.
- The Bicep template declares an S1 App Service plan, but live validation on
  2026-08-10 reported B1. Releases now block on that drift before replacing
  containers; production was reconciled to S1 on 2026-08-11.
- A subsequent B1 release on 2026-08-11 restored private proxy health about
  10 minutes after verification began; deployment checks now retain a
  15-minute hard deadline as defense in depth.
