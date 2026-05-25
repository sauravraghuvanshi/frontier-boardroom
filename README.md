# Frontier Boardroom

> Five frontier AI models, one boardroom channel. CEO (GPT-5) · CFO (Claude Sonnet 4.5) · CMO (Grok-4) · CTO (GPT-4.1) · Legal (Claude Opus). Debating *your* question, live, in a Microsoft Teams-style chat — built for founders and CXOs.

OpenAI, xAI, Meta, and Mistral are served via **Microsoft Foundry** (1st party).
Anthropic Claude is served via **Azure Databricks Mosaic AI Model Serving** (external model).
A backend [`model_router.py`](backend/app/agents/model_router.py) abstracts both. Same agent code, two clouds.

---

## Live (prod, corp sub)

- **Frontend:** https://app-frontier-prod-frontend.azurewebsites.net
- **Backend:**  https://app-frontier-prod-backend.azurewebsites.net/health
- Full Azure resource inventory, parked items, and rebuild/redeploy commands: [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Status (2026-05-25 late — live-deploy hardening; backend `rag-2026-05-25b` / frontend `prod-2026-05-25b`)

All five seats produce grounded, markdown-formatted turns. Three earlier 05-25 bugs (CEO wall-of-prose, CMO empty bubble, Legal silent + all-yes vote) plus three late-day deploy bugs are fixed:

- **CEO (Aanya) wall of prose:** added the same `FORMAT (MANDATORY)` GFM directive the other personas already had — bold key terms, 2–4 bullet trade-offs, final `**Decision:**` / `**Ask:**` line.
- **CMO (Priya) empty bubble:** `grok-4-1-fast-reasoning` routes its entire final answer through reasoning-channel events, so the L-13 CoT filter silenced it. `foundry_provider.py` now buffers reasoning deltas and yields them only when `output_text` produced zero tokens (L-15).
- **Legal silent + all-yes hardcoded vote:** `boardroom.py` tracks `spoken_roles` (Legal must be in it before convergence breaks), `_parse_vote()` regex-matches each persona's last message with reject-wins-on-tie, and `_extract_decision()` prefers a `**Decision:**` line from the CEO (L-16).
- **Live frontend hung on "Convening the boardroom…":** the deployed bundle had `http://localhost:8000` baked in (Vite inlines `import.meta.env.VITE_*` at build, L-6). Rebuilt `frontier-frontend:prod-2026-05-25b` with `--build-arg VITE_API_BASE=https://...backend.azurewebsites.net` + `VITE_WS_BASE=wss://...`. App Service was caching `:latest` so the explicit tag had to be pinned on the web app (L-18) to force a pull.
- **CTO (Ravi) using DeepSeek + leaking CoT preamble:** `MODEL_CTO=foundry:CTO@1` was version-pinned to the old DeepSeek-backed agent revision; rebinding the Foundry agent to gpt-4.1 at `@6` did NOT update the backend (L-17). Switched `MODEL_CTO=foundry:gpt-4.1` (raw deployment) to bypass the agent wrapper, which had stale `file_search` + MCP tools causing the "Ravi typing" hang.
- **Model chip showed "CTO@6":** added `"CTO@6": "gpt-4.1 · RAG"` and `"gpt-4.1": "gpt-4.1"` mappings to `MessageBubble.tsx` + `ParticipantsRail.tsx`.

Also live: ten grounded scenario channels, About page for fictional "Aksara Cloud", branded indigo/cyan/amber palette + logo + Inter typography, audience-question QR flow (`/audience-question` form → in-memory inbox → 3s poll on main display starts a new debate).

### Next session

1. **BUG — debate keeps running after decision pins.** Observed 2026-05-25 PM on SEA Expansion: decision card + full vote panel rendered, yet **all five agents kept talking** below it. Decision must be terminal — orchestrator should `return` from `Boardroom.run` immediately after emitting `debate_end`, and the frontend should freeze the thread on receipt of `debate_end`.
2. **Manual UI smoke** on the live frontend — Ravi chip reads `gpt-4.1` (no DeepSeek leak), Legal disagrees, decision card pins amber on convergence, audience-question QR round-trips.
3. **Optional follow-ups:** rotate the Databricks PAT; wire the Language sentiment SDK call in `backend/app/voice/sentiment.py`; refresh `docs/demo-runbook.md` for the 10 channels + audience flow + CTO=gpt-4.1; promote briefing-injection (L-12), reasoning-fallback (L-15), vote-parsing (L-16), MODEL_* version-pinning audit (L-17), and explicit-tag container deploys (L-18) into `.claude/patterns.md`.

```bash
# Smoke
curl -fsS https://app-frontier-dev-backend.azurewebsites.net/health

# Provider probe (once Foundry + Databricks creds are wired)
az webapp ssh -g rg-frontier-boardroom-dev -n app-frontier-dev-backend \
  --command "python -m app.agents.model_router probe"

# Tail backend logs
az webapp log tail -g rg-frontier-boardroom-dev -n app-frontier-dev-backend
```

Walk [`docs/demo-runbook.md`](docs/demo-runbook.md) for the full stage script
(model-swap moment is the keynote payoff).

---

## Quick start (under 10 minutes)

```bash
# 1. Clone & enter
git clone <repo> frontier-boardroom && cd frontier-boardroom

# 2. Fill in .env (only the bits you have — fake-debate works without credentials)
cp .env.example .env

# 3a. Native (recommended for local dev)
cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000 &
cd ../frontend && npm install && npm run dev -- --host 0.0.0.0

# 3b. Or Docker
docker compose up --build

# 4. Open the boardroom
open http://localhost:5173
```

The landing screen is a Microsoft Teams-style chat — left rail lists 4 scenario channels (SEA Expansion, $30M Term Sheet, Competitor Launch, AI Safety Incident) plus a "New topic" composer. Click a channel and the C-suite starts posting in the center pane; participants and their live model assignments sit on the right rail.

If you have no Foundry / Databricks credentials configured, the app automatically serves a recorded debate from [`backend/app/dev/fake_debate.json`](backend/app/dev/fake_debate.json).

### Run a real debate against live models

Set in `.env`:

```
AZURE_FOUNDRY_PROJECT_CONNECTION_STRING=...
DATABRICKS_HOST=https://<workspace>.azuredatabricks.net
DATABRICKS_TOKEN=...
AZURE_SPEECH_KEY=...
AZURE_LANGUAGE_ENDPOINT=...
```

Then probe every wired model in one command:

```bash
docker compose exec backend python -m app.agents.model_router probe
```

You should see five green check-marks — one per role — with first-token latency.

---

## Architecture (one paragraph)

A FastAPI backend hosts five `PersonaAgent` instances. Each agent's `model_ref` is
of the form `<provider>:<endpoint>` (`foundry:gpt-5`, `databricks:claude-sonnet-4-5`,
…). The model router dispatches to `FoundryProvider` or `DatabricksProvider`. The
orchestrator (`boardroom.py`) runs Microsoft Agent Framework workflows: turn-taking,
A2A challenge/support/question messages, and convergence detection. Every factual
claim is grounded by `foundry_iq_client.retrieve(...)` against an Azure Blob
container indexed in FoundryIQ. Sentiment from Azure Language drives a server-
authoritative mood state machine (`cordial → debating → heated → converging →
resolved`). The frontend is a React 18 + TypeScript + Vite Microsoft Teams-style chat
shell — scenario channels on the left, a streaming message thread in the center
(avatars + name/title + provider-coded model chip + citation footnotes + an inline
decision card on convergence), and a participants rail on the right with inline
model-swap dropdowns. TTS + visemes from Azure Speech still stream over WebSocket
(`audio_chunk`/`viseme` events) but the chat UI ignores them; the older 3D R3F
boardroom is retired (see `.claude/architecture.md` AD-11).

See [`docs/architecture.md`](docs/architecture.md) for diagrams.

---

## Folder layout

See [§3 of the plan](.github/FRONTIER_BOARDROOM_PLAN.md#3-folder-structure-mirror-this-exactly).

---

## Deploy to Azure

```bash
bash infrastructure/scripts/deploy.sh dev
```

Bicep provisions everything in §13. The script then runs `setup_databricks.py`
(creates Mosaic AI external-model endpoints for Anthropic), seeds blob,
builds the FoundryIQ index, pushes images to ACR, and updates both Web Apps.

---

## Live demo runbook

[`docs/demo-runbook.md`](docs/demo-runbook.md) — exact stage script.
The **model-swap moment** (CFO `databricks:claude-sonnet-4-5` → `foundry:gpt-5`,
mid-debate, no code change) is the keynote payoff.

---

## License

MIT.
