#!/usr/bin/env bash
# Frontier Boardroom — one-shot deploy
# Usage: bash deploy.sh dev

set -euo pipefail

ENV=${1:-dev}
RG="rg-frontier-boardroom-${ENV}"
LOC=${LOCATION:-centralindia}
ENABLE_ENTRA_AUTH=${ENABLE_ENTRA_AUTH:-false}
ENTRA_CLIENT_ID=${ENTRA_CLIENT_ID:-}

if [[ "$ENABLE_ENTRA_AUTH" == "true" && -z "$ENTRA_CLIENT_ID" ]]; then
  echo "ENTRA_CLIENT_ID is required when ENABLE_ENTRA_AUTH=true" >&2
  exit 1
fi

echo "==> Resource group"
az group create -n "$RG" -l "$LOC" -o none

echo "==> Bicep what-if"
az deployment group what-if -g "$RG" \
  -f infrastructure/bicep/main.bicep \
  -p env="$ENV" \
  -p adminObjectId="$(az ad signed-in-user show --query id -o tsv)" \
  -p enableEntraAuth="$ENABLE_ENTRA_AUTH" \
  -p entraClientId="$ENTRA_CLIENT_ID" \
  -p anthropicApiKey="${ANTHROPIC_API_KEY:-}"

echo "==> Bicep deploy"
DEPLOY_OUT=$(az deployment group create -g "$RG" \
  -f infrastructure/bicep/main.bicep \
  -p env="$ENV" \
  -p adminObjectId="$(az ad signed-in-user show --query id -o tsv)" \
  -p enableEntraAuth="$ENABLE_ENTRA_AUTH" \
  -p entraClientId="$ENTRA_CLIENT_ID" \
  -p anthropicApiKey="${ANTHROPIC_API_KEY:-}" \
  -o json)

ACR=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['acrLoginServer']['value'])")
BACKEND=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['backendUrl']['value'])")
FRONTEND=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['frontendUrl']['value'])")
KEYVAULT=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['keyVaultName']['value'])")
DBW_URL=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['databricksWorkspaceUrl']['value'])")

export KEYVAULT_NAME="$KEYVAULT"
export DATABRICKS_HOST="https://${DBW_URL}"
export AZURE_RESOURCE_GROUP="$RG"
export AZURE_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"

echo "==> Databricks Mosaic AI setup"
python infrastructure/scripts/setup_databricks.py

echo "==> Seed blob"
python infrastructure/scripts/seed_blob.py

echo "==> Build FoundryIQ index"
python infrastructure/scripts/build_foundry_iq.py

echo "==> Docker images"
az acr login -n "${ACR%%.*}"
docker build -t "${ACR}/frontier-backend:latest" backend/
docker build \
  --build-arg "VITE_API_BASE=${FRONTEND}" \
  --build-arg "VITE_WS_BASE=${FRONTEND/https:/wss:}" \
  --build-arg "VITE_ENTRA_AUTH_ENABLED=${ENABLE_ENTRA_AUTH}" \
  -t "${ACR}/frontier-frontend:latest" \
  frontend/
docker push "${ACR}/frontier-backend:latest"
docker push "${ACR}/frontier-frontend:latest"

echo "==> Update web apps"
az webapp restart -g "$RG" -n "app-frontier-${ENV}-backend"
az webapp restart -g "$RG" -n "app-frontier-${ENV}-frontend"

echo "==> Smoke test"
curl -fsS "${BACKEND}/health" && echo
curl -fsS "${BACKEND}/dev/router-probe" || echo "[warn] router-probe non-200"

echo "==> Done"
echo "Backend:  ${BACKEND}"
echo "Frontend: ${FRONTEND}"
