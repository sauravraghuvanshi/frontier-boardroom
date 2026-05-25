#!/usr/bin/env bash
# Frontier Boardroom — one-shot deploy
# Usage: bash deploy.sh dev

set -euo pipefail

ENV=${1:-dev}
RG="rg-frontier-boardroom-${ENV}"
LOC=${LOCATION:-centralindia}

echo "==> Resource group"
az group create -n "$RG" -l "$LOC" -o none

echo "==> Bicep what-if"
az deployment group what-if -g "$RG" \
  -f infrastructure/bicep/main.bicep \
  -p env="$ENV" \
  -p adminObjectId="$(az ad signed-in-user show --query id -o tsv)" \
  -p anthropicApiKey="${ANTHROPIC_API_KEY:-}"

echo "==> Bicep deploy"
DEPLOY_OUT=$(az deployment group create -g "$RG" \
  -f infrastructure/bicep/main.bicep \
  -p env="$ENV" \
  -p adminObjectId="$(az ad signed-in-user show --query id -o tsv)" \
  -p anthropicApiKey="${ANTHROPIC_API_KEY:-}" \
  -o json)

ACR=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['acrLoginServer']['value'])")
BACKEND=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['backendUrl']['value'])")
FRONTEND=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['frontendUrl']['value'])")
KEYVAULT=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['keyVaultName']['value'])")
DBW_URL=$(echo "$DEPLOY_OUT" | python -c "import sys,json;print(json.load(sys.stdin)['properties']['outputs']['databricksWorkspaceUrl']['value'])")

export KEYVAULT_NAME="$KEYVAULT"
export DATABRICKS_HOST="https://${DBW_URL}"

echo "==> Databricks Mosaic AI setup"
python infrastructure/scripts/setup_databricks.py

echo "==> Seed blob"
python infrastructure/scripts/seed_blob.py

echo "==> Build FoundryIQ index"
python infrastructure/scripts/build_foundry_iq.py

echo "==> Docker images"
az acr login -n "${ACR%%.*}"
docker build -t "${ACR}/frontier-backend:latest" backend/
docker build -t "${ACR}/frontier-frontend:latest" frontend/
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
