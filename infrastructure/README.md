# Frontier Boardroom — Infrastructure

```bash
az group create -n rg-frontier-boardroom-dev -l centralindia
az deployment group what-if -g rg-frontier-boardroom-dev -f bicep/main.bicep \
  -p env=dev adminObjectId=$(az ad signed-in-user show --query id -o tsv)
az deployment group create -g rg-frontier-boardroom-dev -f bicep/main.bicep \
  -p env=dev adminObjectId=$(az ad signed-in-user show --query id -o tsv) \
  -p anthropicApiKey=$ANTHROPIC_API_KEY
```

Then run, in order:

```bash
python scripts/setup_databricks.py
python scripts/seed_blob.py
python scripts/build_foundry_iq.py
bash scripts/deploy.sh dev
```

`deploy.sh` is idempotent — re-running it just updates app images and re-seeds
if `data-version.txt` changed.
