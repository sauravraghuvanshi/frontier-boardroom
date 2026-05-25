# The Frontier Org Boardroom — Implementation Plan

> **Purpose of this document:** This is the master build plan for a live-demo web app called **Frontier Boardroom**. Give this entire file to GitHub Copilot (drop it into `.github/copilot-instructions.md` or open it in the workspace) and ask it to scaffold the project step by step. Each section is written so Copilot can act on it without further clarification.

---

## 1. What We Are Building

A cinematic web application that shows **five AI agents acting as a virtual C-suite** debating a strategic founder question in real time.

- **CEO Agent** — orchestrator, runs on **GPT-5 (Azure OpenAI, served via Microsoft Foundry — 1st party)**
- **CFO Agent** — runs on **Claude Sonnet 4.5 (Anthropic, served via Azure Databricks Mosaic AI Model Serving)**
- **CMO Agent** — runs on **Grok (xAI, Foundry catalog — 1st party)**
- **CTO Agent** — runs on **Llama 3.3 / Mistral Large (Foundry catalog — 1st party Models-as-a-Service)**
- **Legal Agent** — runs on **Claude Opus (Anthropic, served via Azure Databricks Mosaic AI Model Serving)**

> **Tenant constraint:** Anthropic models are **not** available as 1st-party on this tenant's Foundry. They are accessed through **Azure Databricks Mosaic AI** (which has Anthropic Claude available via Foundation Model APIs / external model endpoints). Only OpenAI, xAI, Meta, and Mistral are reachable via Foundry as 1st party here.

They debate a question like *"Should we expand to Southeast Asia next quarter?"*, ground their arguments in **Microsoft Foundry IQ** (which retrieves from sample data in Azure Blob Storage), and converge on a recommendation.

The audience sees a **3D animated boardroom** where the five characters sit around a table. Their facial expressions, posture, and idle activities (sipping coffee, leaning forward, gesturing, scribbling on iPad) change with the **emotional intensity of the conversation**. The active speaker is highlighted with cinematic camera cuts. Each agent speaks in a **distinct neural voice** (Azure Speech). Subtitles appear with the speaker's name and which model is responding.

---

## 2. The Wow Factors (must be visible to the audience)

| # | Wow Factor | How It Shows Up |
|---|------------|-----------------|
| 1 | **Multiple frontier models on one platform** | Each speaker badge says `GPT-5`, `Claude Sonnet 4.5`, `Grok`, `Llama 3.3`, `Claude Opus`. Audience sees Microsoft is the only platform offering this mix. |
| 2 | **Agent-to-Agent (A2A) debate** | CFO challenges CMO. CTO interrupts. CEO synthesizes. Real disagreement, not a round-robin. |
| 3 | **FoundryIQ grounding in real time** | When an agent cites a number ("our SEA pipeline is $4.2M"), a side panel flashes the **retrieved source document** from blob storage. |
| 4 | **Emotional intensity engine** | Faces and postures change live. Mood meter on side: 🟢 Cordial → 🟡 Debating → 🔴 Heated → 🟢 Converging. |
| 5 | **Cinematic camera + voice** | Auto cuts to the speaker. Distinct neural voice per persona. Lip-sync via Azure visemes. |
| 6 | **Live model swap** | A "🎛️ Swap Model" button on each chair — change CFO from Claude to GPT-5 mid-debate. Zero code change. Audience picks. |
| 7 | **Audience-driven question** | A QR code lets a founder in the room type their own question. The board debates *their* problem. |
| 8 | **Governance overlay** | A toggle reveals the Agent 365 observability panel — token spend per agent, tools called, policies enforced. |

---

## 3. Folder Structure (mirror this exactly)

```
frontier-boardroom/
├── .claude/
│   ├── memory/
│   │   └── MEMORY.md
│   ├── skills/
│   │   ├── add-agent-persona/        # scaffold a new boardroom agent (model, voice, prompt, avatar)
│   │   ├── add-api-endpoint/         # FastAPI route + Pydantic schema
│   │   ├── add-foundry-iq-source/    # register a new doc in FoundryIQ index
│   │   ├── add-frontend-scene/       # add a new react-three-fiber scene
│   │   ├── add-blob-dataset/         # upload + index a new dataset to blob + FoundryIQ
│   │   ├── deploy/                   # deploy to Azure App Service
│   │   ├── run-tests/                # pytest + vitest
│   │   ├── troubleshoot-deploy/      # common Azure deploy fixes
│   │   └── voice-pipeline/           # neural voice + viseme lip-sync helpers
│   ├── architecture.md
│   ├── CLAUDE.md
│   ├── lessons.md
│   ├── patterns.md
│   └── project-memory.md
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # lint + test on PR
│   │   └── deploy.yml                # build + push + deploy to App Service
│   └── copilot-instructions.md
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # abstract persona w/ model adapter
│   │   │   ├── ceo_agent.py           # GPT-5, orchestrator
│   │   │   ├── cfo_agent.py           # Claude Sonnet 4.5
│   │   │   ├── cmo_agent.py           # Grok
│   │   │   ├── cto_agent.py           # Llama 3.3 / Mistral
│   │   │   └── legal_agent.py         # Claude Opus
│   │   ├── orchestrator/
│   │   │   ├── boardroom.py           # Microsoft Agent Framework workflow
│   │   │   ├── a2a_protocol.py        # agent-to-agent messaging
│   │   │   ├── turn_taking.py         # who speaks next + interruption logic
│   │   │   └── convergence.py         # detects when board reaches a decision
│   │   ├── grounding/
│   │   │   ├── foundry_iq_client.py   # FoundryIQ retrieval (agentic RAG)
│   │   │   └── citations.py           # map answers back to source docs
│   │   ├── emotion/
│   │   │   ├── sentiment.py           # Azure AI Language sentiment + tone
│   │   │   └── mood_state.py          # boardroom mood state machine
│   │   ├── voice/
│   │   │   ├── tts.py                 # Azure Speech neural voices
│   │   │   └── visemes.py             # lip-sync frame data
│   │   ├── api/
│   │   │   ├── routes_session.py      # POST /session, GET /session/{id}
│   │   │   ├── routes_debate.py       # POST /debate (kicks off the discussion)
│   │   │   ├── routes_swap.py         # POST /agent/{role}/swap-model
│   │   │   └── ws_stream.py           # WebSocket: streams turns + emotion deltas
│   │   ├── config.py                  # env vars, model registry
│   │   ├── main.py                    # FastAPI app
│   │   └── telemetry.py               # App Insights + Agent 365 hooks
│   ├── data/
│   │   └── sample_seed/               # raw sample docs before upload
│   ├── tests/
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── public/
│   │   └── assets/
│   │       ├── avatars/               # .glb files for each persona
│   │       ├── boardroom.glb          # the room geometry
│   │       └── audio/                 # ambient sound
│   ├── src/
│   │   ├── scenes/
│   │   │   ├── Boardroom.tsx          # react-three-fiber main scene
│   │   │   ├── Character.tsx          # animated avatar w/ emotion blendshapes
│   │   │   ├── CameraDirector.tsx     # cinematic cuts to active speaker
│   │   │   └── MoodLighting.tsx       # changes room lighting w/ mood
│   │   ├── components/
│   │   │   ├── SpeakerBadge.tsx       # shows persona + model name
│   │   │   ├── SubtitleBar.tsx
│   │   │   ├── MoodMeter.tsx          # cordial → heated gauge
│   │   │   ├── CitationPanel.tsx      # FoundryIQ retrieved source
│   │   │   ├── ModelSwapDial.tsx      # change model mid-debate
│   │   │   ├── Agent365Overlay.tsx    # governance / token usage
│   │   │   └── QRPromptCard.tsx       # audience question entry
│   │   ├── hooks/
│   │   │   ├── useDebateStream.ts     # WebSocket consumer
│   │   │   ├── useEmotionState.ts
│   │   │   └── useTTS.ts              # plays audio + drives visemes
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   └── visemeMap.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── theme.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── infrastructure/
│   ├── bicep/
│   │   ├── main.bicep                 # resource group composition
│   │   ├── appservice.bicep
│   │   ├── storage.bicep              # blob + container
│   │   ├── foundry.bicep              # Foundry project + IQ index
│   │   ├── speech.bicep
│   │   ├── insights.bicep
│   │   └── modules/
│   ├── scripts/
│   │   ├── seed_blob.py               # uploads sample data
│   │   ├── build_foundry_iq.py        # builds the FoundryIQ index
│   │   └── deploy.sh
│   └── README.md
├── docs/
│   ├── demo-runbook.md                # what to say on stage, in what order
│   ├── architecture.md
│   ├── sample-scenarios.md
│   └── screenshots/
├── .env.example
├── .gitignore
├── docker-compose.yml                 # local dev (backend + frontend)
├── README.md
└── LICENSE
```

---

## 4. Tech Stack (locked choices — do not substitute)

**Backend**
- Python 3.12, FastAPI, Uvicorn, WebSockets
- **Microsoft Agent Framework** (open source, A2A + MCP)
- Azure AI Foundry SDK (`azure-ai-projects`, `azure-ai-inference`) — for GPT-5, Grok, Llama, Mistral
- **Azure Databricks SDK + Mosaic AI Model Serving REST API** — for Anthropic Claude (Sonnet 4.5, Opus)
  - Anthropic models are exposed as **Databricks Model Serving endpoints** that speak the OpenAI-compatible chat-completions schema, so the same client pattern works with a different base URL + token.
- FoundryIQ retrieval API (shared by all agents regardless of where their model is hosted)
- Azure Speech SDK (neural voices, visemes)
- Azure AI Language (sentiment + tone)
- Azure Blob SDK (`azure-storage-blob`)
- App Insights (`opentelemetry-azure-monitor`)
- Pydantic v2, pytest

**Frontend**
- React 18 + TypeScript + Vite
- **react-three-fiber** + **drei** + Three.js (3D boardroom)
- **@react-three/postprocessing** for cinematic look (depth of field, bloom)
- Framer Motion (UI transitions)
- Zustand (state)
- TailwindCSS + shadcn/ui
- Howler.js (ambient audio)
- WebSocket native API

**Infra**
- Azure App Service (Linux, containers) — one for backend, one for frontend
- Azure Container Registry
- Azure Storage (blob + static website fallback)
- Azure AI Foundry project (with FoundryIQ enabled) — hosts GPT-5, Grok, Llama, Mistral
- **Azure Databricks workspace** with **Mosaic AI Model Serving** endpoints for Anthropic Claude Sonnet 4.5 and Claude Opus (configured as external model endpoints inside Databricks)
- Azure Speech, Azure AI Language
- App Insights
- Bicep + GitHub Actions

---

## 5. Sample Data Plan (Azure Blob Storage)

Storage account `stfrontierboardroom`, container `boardroom-knowledge`. The seed script `infrastructure/scripts/seed_blob.py` uploads these on first run.

Folder structure inside the container:

```
boardroom-knowledge/
├── financials/
│   ├── 2025-Q4-pnl.pdf
│   ├── 2026-Q1-forecast.xlsx
│   ├── runway-and-cash.md
│   └── unit-economics-by-region.csv
├── market/
│   ├── sea-market-tam-sam-som.pdf
│   ├── india-vs-sea-cac-benchmarks.csv
│   ├── analyst-reports/
│   │   ├── gartner-sea-saas-2026.pdf
│   │   └── idc-india-cloud-2026.pdf
│   └── customer-interviews-sea.md
├── competition/
│   ├── competitor-landscape-sea.md
│   ├── win-loss-report-2025.pdf
│   └── pricing-comparison.csv
├── product/
│   ├── tech-debt-register.md
│   ├── engineering-capacity-2026.xlsx
│   ├── infra-cost-by-region.csv
│   └── localization-readiness.md
├── legal/
│   ├── data-residency-by-country.md       # SG, ID, VN, TH, PH, MY
│   ├── gdpr-and-pdpa-summary.md
│   ├── employment-law-sea.md
│   └── ip-and-trademark-risks.md
├── marketing/
│   ├── brand-awareness-sea.csv
│   ├── go-to-market-playbook.md
│   ├── partner-ecosystem-sea.md
│   └── campaign-history-2025.csv
└── hr/
    ├── hiring-plan-2026.xlsx
    ├── talent-availability-sea.md
    └── compensation-benchmarks-sea.csv
```

**Generate realistic synthetic data** for each file. Numbers should be internally consistent across files so agents citing them produce a coherent debate. Add a `MANIFEST.json` listing each file's title, owner, date, tags — used by FoundryIQ for filtered retrieval.

---

## 6. FoundryIQ Integration

1. Create a Foundry project; enable **FoundryIQ Knowledge** with a unified knowledge base.
2. Register `boardroom-knowledge` blob container as a data source.
3. Configure agentic RAG with multi-hop reasoning enabled.
4. Each agent calls `foundry_iq_client.retrieve(query, persona_filter)` — `persona_filter` biases retrieval by folder (CFO → `financials/`, `competition/pricing-comparison.csv`; Legal → `legal/`; etc.).
5. Every retrieval returns `{ snippet, source_uri, confidence, hops }`. The backend pushes this to the frontend over WebSocket so the **Citation Panel** flashes the source the moment an agent cites it.

---

## 7. Agent Architecture (Microsoft Agent Framework)

### 7.0 Model Router (the key change)

Because Anthropic lives on Databricks and everything else lives on Foundry, every agent calls a **model router**, not a direct SDK. The router picks the right backend based on the `provider` field in the model registry.

```python
# backend/app/agents/model_router.py
from typing import AsyncIterator
from .providers.foundry_provider import FoundryProvider
from .providers.databricks_provider import DatabricksProvider

PROVIDERS = {
    "foundry":    FoundryProvider(),     # GPT-5, Grok, Llama, Mistral
    "databricks": DatabricksProvider(),  # Anthropic Claude Sonnet 4.5, Claude Opus
}

# Registry resolved from MODEL_<ROLE> env vars at boot.
# Format: "<provider>:<deployment-or-endpoint-name>"
# Examples:
#   foundry:gpt-5
#   foundry:grok-3
#   foundry:llama-3.3-70b-instruct
#   databricks:claude-sonnet-4-5
#   databricks:claude-opus-4

async def stream_chat(model_ref: str, messages, tools=None) -> AsyncIterator[dict]:
    provider_key, deployment = model_ref.split(":", 1)
    provider = PROVIDERS[provider_key]
    async for event in provider.stream_chat(deployment, messages, tools=tools):
        yield event   # normalized: {type: "token"|"tool_call"|"end", ...}
```

```python
# backend/app/agents/providers/foundry_provider.py
# Uses azure-ai-inference. Endpoints + keys resolved via Foundry project connection.

# backend/app/agents/providers/databricks_provider.py
# Hits https://<workspace>.azuredatabricks.net/serving-endpoints/<endpoint>/invocations
# with a Databricks PAT or service principal OAuth token. The endpoint is configured
# inside Databricks as an "external model" pointing at Anthropic, exposing the
# OpenAI-compatible chat-completions schema. Streaming via SSE.
```

**Why a router and not direct SDK calls inside each agent:**
- Hot-swap UI flips one env var at runtime — router re-resolves.
- `/dev/fake-debate` fallback (see §16 rule 10) is a third provider implementation.
- Telemetry, retry, token-counting, and citation-injection live in one place.

### 7.1 Persona definition (one file per agent)

```python
# backend/app/agents/cfo_agent.py
from .base_agent import PersonaAgent

class CFOAgent(PersonaAgent):
    role = "CFO"
    display_name = "Anika Desai"
    model_ref = "databricks:claude-sonnet-4-5"       # routed to Databricks Mosaic AI
    voice = "en-IN-NeerjaNeural"                     # Azure Speech
    avatar = "avatars/cfo_anika.glb"
    chair_position = 2

    system_prompt = """
    You are Anika Desai, CFO of a Series B startup. You speak with precise numbers
    and care about runway, burn, unit economics, and capital efficiency. You will
    push back hard on plans that don't math out. You cite figures from our
    financial knowledge base via FoundryIQ. Keep responses under 3 sentences in
    debate mode. Be respectful but direct. End with a clear position.
    """

    tools = ["foundry_iq.retrieve", "calculator", "scenario_modeler"]
```

Set the other personas' `model_ref` like so:
- CEO → `foundry:gpt-5`
- CMO → `foundry:grok-3`
- CTO → `foundry:llama-3.3-70b-instruct`
- Legal → `databricks:claude-opus-4`

Vary tone, expected vocabulary, and decision biases per persona. **Tools (including FoundryIQ retrieval) are model-agnostic** — they work identically whether the model is on Foundry or Databricks because the router normalizes tool-call events.

### 7.2 Orchestration (`boardroom.py`)

- Built on Microsoft Agent Framework's `Workflow` primitives.
- **CEO Agent** is the **orchestrator** — opens the debate, names speakers, prompts disagreement, calls for convergence after N turns or when sentiment stabilizes.
- **Turn-taking**: weighted by topic relevance + recency. CFO speaks more on financial topics, Legal interrupts when risk threshold crossed.
- **A2A messages** flow as structured objects: `{from, to, intent: 'challenge'|'support'|'question'|'data_request', content, citations}`.
- **Convergence detector** ends the debate when (a) the CEO summarizes, (b) sentiment shifts from heated back to cordial, AND (c) ≥3 of 5 agents have signaled agreement.

### 7.3 Streaming protocol (WebSocket `/ws/debate`)

The backend streams events to the frontend:

```json
{"type":"turn_start","agent":"CFO","model":"claude-sonnet-4-5","timestamp":...}
{"type":"token","agent":"CFO","text":"Our SEA pipeline is "}
{"type":"citation","agent":"CFO","source_uri":"financials/2026-Q1-forecast.xlsx","snippet":"SEA Q1 pipeline: $4.2M"}
{"type":"token","agent":"CFO","text":"$4.2M, but CAC is 2.3x India."}
{"type":"turn_end","agent":"CFO","duration_ms":4200,"tokens":58}
{"type":"mood","value":0.62,"label":"debating"}
{"type":"viseme","agent":"CFO","frames":[...]}
{"type":"audio_chunk","agent":"CFO","base64":"..."}
{"type":"debate_end","decision":"...","vote":{"CEO":"yes","CFO":"conditional",...}}
```

---

## 8. Emotion & Animation Engine

### 8.1 Mood state machine

States: `cordial → debating → heated → converging → resolved`.

Drivers (rolling 30s window):
- Average Azure AI Language sentiment across last 5 turns
- Density of `challenge` A2A messages
- Interruption rate
- Use of strong-tone tokens ("disagree", "wrong", "actually", "no")

Mood value `0.0 (cordial) → 1.0 (heated)` is broadcast on the `mood` event.

### 8.2 Per-character expression

Each character has:
- **Blendshape rig** (Ready Player Me avatars or Mixamo + ARKit blendshapes): `mouthSmile`, `browFurrow`, `eyeWide`, `jawOpen`, etc.
- **Emotion preset blends** mapped from each agent's per-turn sentiment: `neutral`, `confident`, `concerned`, `frustrated`, `amused`, `decisive`.
- **Idle activity loops**: sipping coffee, scrolling iPad, leaning back, taking notes, glancing at neighbor, checking watch. Loops chosen by a Markov chain so they look organic, not scripted.
- **Speaking loop**: subtle head/hand gestures + visemes driven by Azure Speech viseme stream (lip-sync).
- **Reactions**: when another agent challenges them, brief reaction (raised brow, slight head shake) before responding.

### 8.3 Camera director

`CameraDirector.tsx` runs a small rules engine:
- Default: medium two-shot of the table.
- On `turn_start`: cut to close-up of speaker (slight Dutch angle if mood > 0.7).
- On strong challenge: quick whip-pan to challenger then back.
- Every ~25s if no turn change: slow dolly-in.
- On `debate_end`: pull back to wide group shot.

### 8.4 Lighting & ambience

- Mood-driven lighting via `MoodLighting.tsx`: cool blues when cordial, warm amber as it heats up, slight red rim light when heated.
- Background audio: low ambient boardroom hum, subtle keyboard taps from CTO, distant traffic. Howler.js. Ducked when an agent speaks.

---

## 9. Voice Pipeline

| Agent | Azure Neural Voice | Personality cue |
|-------|---------------------|-----------------|
| CEO (Aarav) | `en-IN-PrabhatNeural` | Calm, authoritative |
| CFO (Anika) | `en-IN-NeerjaNeural` | Precise, slightly skeptical |
| CMO (Maya) | `en-US-JennyMultilingualNeural` | Energetic, trend-aware |
| CTO (Rohan) | `en-IN-AaravNeural` | Measured, technical |
| Legal (Priya) | `en-GB-LibbyNeural` | Formal, careful |

- Use SSML to inject pauses, emphasis on numbers, and slight rate changes based on mood (faster + higher pitch when heated, slower when cordial).
- Azure Speech returns **viseme stream** alongside audio — pipe both to frontend; frontend drives lip-sync from visemes.
- Pre-warm voices at session start to avoid first-byte latency.

---

## 10. Backend API Surface

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/session` | Create a debate session; returns `session_id` |
| `POST` | `/debate` | Body: `{session_id, question, scenario_id?}` — kicks off the debate |
| `WS`   | `/ws/debate/{session_id}` | Streams the events from §7.3 |
| `POST` | `/agent/{role}/swap-model` | Hot-swap a model mid-debate |
| `GET`  | `/scenarios` | Pre-baked questions for quick demos |
| `POST` | `/audience-question` | Founder submits via QR — enqueues a debate |
| `GET`  | `/telemetry/session/{id}` | Token spend, latencies, tools called, sources cited |
| `GET`  | `/health` | Liveness + readiness |

---

## 11. Frontend UX Notes

- **Landing screen**: animated logo, "Press space to convene the board." Plays a brief intro sting.
- **Main scene**: 3D boardroom fills the screen. Subtitle bar at bottom with speaker name and `model: claude-sonnet-4-5` chip.
- **Right rail (collapsible)**: Mood meter, Citation panel, Token-spend ticker.
- **Left rail (collapsible)**: Model swap dials for each chair, Agent 365 overlay toggle, Scenario picker.
- **Top-right**: QR code for audience questions.
- **Bottom-right**: Big red **`End Debate & Show Decision`** button — produces a one-page recommendation card with the board's final vote.
- All overlays should be **hide-able with a single keystroke** so the room is clean for a "pure cinema" moment.

---

## 12. Pre-baked Scenarios (for the live demo)

Ship 4 scenarios in `/scenarios` so you can demo even if the audience doesn't submit one:

1. **"Should we expand to Southeast Asia next quarter?"** (the headline scenario)
2. **"Should we accept the $30M term sheet from a US fund at a flat valuation?"**
3. **"Should we deprecate our on-prem product to go cloud-only in 12 months?"**
4. **"Should we acquire our smaller competitor for $8M in stock?"**

Each scenario seeds different documents in the knowledge base for richer citations.

---

## 13. Azure Infrastructure (Bicep)

`infrastructure/bicep/main.bicep` provisions:

- Resource group `rg-frontier-boardroom-{env}`
- App Service plan (Linux, P1v3)
- Two Web Apps (containers): `app-frontier-backend-{env}`, `app-frontier-frontend-{env}`
- Storage account + container `boardroom-knowledge`
- Foundry project + FoundryIQ index
- **Azure Databricks workspace** (`dbw-frontier-boardroom-{env}`) with Premium tier (required for Model Serving)
- Speech service, Language service
- App Insights + Log Analytics workspace
- Key Vault for model API keys + Databricks PAT (or service principal OAuth)
- Managed identity wired through everywhere (no keys in app settings)

> **Note on Databricks Bicep:** the workspace itself is Bicep-provisionable (`Microsoft.Databricks/workspaces`). The **Model Serving endpoints** and **external model** (Anthropic) wiring are configured via the Databricks REST API or the Databricks Terraform/SDK after the workspace exists — keep that in a separate `scripts/setup_databricks.py` step.

`scripts/deploy.sh`:
1. `az deployment group create -f main.bicep`
2. `python scripts/setup_databricks.py` — creates the Mosaic AI Model Serving endpoints for `claude-sonnet-4-5` and `claude-opus-4`, points them at Anthropic as **external models**, stores the Anthropic API key in Databricks secret scope, and writes the endpoint URLs to Key Vault.
3. `python scripts/seed_blob.py`
4. `python scripts/build_foundry_iq.py`
5. `docker build && docker push` for both apps
6. `az webapp config container set ...` for both
7. Smoke test `/health` on both apps **and** hit a one-shot `/dev/router-probe` endpoint that calls every configured model once to confirm both Foundry and Databricks routes are alive.

---

## 14. GitHub Actions

`.github/workflows/ci.yml` — on PR:
- Lint backend (ruff), type-check (mypy), test (pytest)
- Lint frontend (eslint), type-check (tsc), test (vitest)
- Bicep what-if on infra changes

`.github/workflows/deploy.yml` — on push to `main`:
- Build & push both Docker images to ACR (OIDC, no secrets)
- `az deployment group create` for infra drift
- Deploy both Web Apps
- Run `seed_blob.py` and `build_foundry_iq.py` if `infrastructure/data-version.txt` changed
- Post smoke-test results to PR / commit

---

## 15. Environment Variables (`.env.example`)

```
# Foundry (1st party: GPT-5, Grok, Llama, Mistral)
AZURE_FOUNDRY_PROJECT_CONNECTION_STRING=
AZURE_FOUNDRY_IQ_INDEX_NAME=boardroom-iq

# Azure Databricks (Anthropic Claude via Mosaic AI Model Serving)
DATABRICKS_HOST=https://<workspace>.azuredatabricks.net
DATABRICKS_TOKEN=                                # PAT or SP OAuth (prefer SP via MI)
DATABRICKS_ENDPOINT_CLAUDE_SONNET=claude-sonnet-4-5     # Model Serving endpoint name
DATABRICKS_ENDPOINT_CLAUDE_OPUS=claude-opus-4

# Model registry (format: "<provider>:<deployment-or-endpoint-name>")
MODEL_CEO=foundry:gpt-5
MODEL_CFO=databricks:claude-sonnet-4-5
MODEL_CMO=foundry:grok-3
MODEL_CTO=foundry:llama-3.3-70b-instruct
MODEL_LEGAL=databricks:claude-opus-4

# Storage
AZURE_STORAGE_ACCOUNT=stfrontierboardroom
AZURE_BLOB_CONTAINER=boardroom-knowledge

# Speech & Language
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=centralindia
AZURE_LANGUAGE_ENDPOINT=

# Telemetry
APPINSIGHTS_CONNECTION_STRING=

# Frontend
VITE_API_BASE_URL=
VITE_WS_BASE_URL=
```

Production reads everything from Key Vault via managed identity. Never commit a real `.env`.

---

## 16. `.github/copilot-instructions.md` (drop this in verbatim)

```markdown
# Copilot Instructions — Frontier Boardroom

You are helping build Frontier Boardroom, a live-demo web app that shows five AI
agents acting as a virtual C-suite (CEO, CFO, CMO, CTO, Legal) debating strategic
questions. Each runs on a different frontier model. **OpenAI GPT-5, xAI Grok,
Meta Llama, and Mistral are served via Microsoft Foundry (1st party).
Anthropic Claude Sonnet 4.5 and Claude Opus are served via Azure Databricks
Mosaic AI Model Serving (Anthropic is not available as 1st party on Foundry
in this tenant).** A backend model router (`agents/model_router.py`) abstracts
this split so agents stay model-agnostic. All agents ground their arguments in
Foundry IQ over an Azure Blob knowledge base. The audience sees a cinematic 3D
boardroom with animated avatars whose faces and posture shift with the
conversation's emotional intensity, and each agent speaks in a distinct Azure
neural voice.

## Non-negotiable rules

1. **Models are configurable, never hardcoded inside agent logic.** Read from
   `MODEL_<ROLE>` env vars in the form `<provider>:<endpoint>`. The "Swap Model"
   UI must work end-to-end across both providers.
1a. **Anthropic is only available via Azure Databricks Mosaic AI on this tenant.**
   Never attempt to call Anthropic models through Foundry — they are not
   provisioned there. The model router (`agents/model_router.py`) is the only
   place that knows which backend serves which model. All Anthropic traffic
   flows through `providers/databricks_provider.py`. All OpenAI / xAI / Meta /
   Mistral traffic flows through `providers/foundry_provider.py`.
2. **All retrieval goes through `foundry_iq_client.retrieve(...)`.** Never call
   blob storage directly from an agent. FoundryIQ is shared by all agents
   regardless of where their model lives.
3. **Stream everything over WebSocket.** No polling, no blocking HTTP for debates.
4. **Lip-sync is driven by Azure Speech visemes, not heuristics.**
5. **Managed identity in Azure; no keys in app settings.** Local dev uses `.env`.
6. **Every agent response must include citations** when it asserts a fact.
   The frontend renders them — if there are no citations, show "no source"
   amber pill.
7. **Mood state is server-authoritative.** Frontend never decides mood on its own.
8. **Latency budget**: first-token < 800ms, full turn end-to-end < 6s. Profile
   in App Insights.
9. **Accessibility**: all subtitles, no demo blocked by audio-only.
10. **Demo safety**: a `/dev/fake-debate` endpoint replays a recorded debate
    if any live model is down. Always have a fallback for the keynote.

## Style

- Backend: Python 3.12, FastAPI, async/await everywhere, Pydantic v2 models for
  every payload. Tests with pytest + pytest-asyncio. Ruff + mypy.
- Frontend: TypeScript strict, function components, hooks. State in Zustand.
  Tailwind utility classes; reusable atoms in `components/ui/`.
- Commits: Conventional Commits. PR titles match.
- One concern per PR. Keep diffs reviewable.

## When unsure

Re-read `docs/architecture.md` and the section in `FRONTIER_BOARDROOM_PLAN.md`
that maps to the file you are editing. If still unsure, leave a `// TODO(plan):`
comment with the question rather than guessing.
```

---

## 17. Build Order (give Copilot these as sequential prompts)

1. **Scaffold repo** with the folder structure in §3 and the files listed in §16 and §15.
2. **Bicep infra** (§13) — App Service, Storage, Foundry project, **Databricks workspace (Premium)**, Speech, Language, Key Vault, App Insights. Stop and verify a `what-if` succeeds.
3. **Databricks setup script** (`infrastructure/scripts/setup_databricks.py`) — creates two Mosaic AI Model Serving endpoints (`claude-sonnet-4-5`, `claude-opus-4`) configured as **external models** pointing at Anthropic, stores the Anthropic API key in a Databricks secret scope, and writes endpoint URLs back to Key Vault. Test each endpoint with a curl-like one-shot before moving on.
4. **Sample data generator** (`infrastructure/scripts/seed_blob.py`) — generates realistic synthetic content for every file listed in §5, uploads to blob.
5. **FoundryIQ index builder** (`build_foundry_iq.py`).
6. **Backend skeleton**: FastAPI app, config, telemetry, WebSocket plumbing (§10, §7.3).
7. **Model router + both providers** (§7.0) — `FoundryProvider` and `DatabricksProvider`. Write a tiny CLI test (`python -m app.agents.model_router probe`) that pings every configured model once and prints first-token latency.
8. **Agent base + 5 personas** (§7.1) with system prompts, calling through the router.
9. **Orchestrator + A2A + turn-taking + convergence** (§7.2).
10. **Grounding** (§6) — `foundry_iq_client` + citation passthrough on the event stream.
11. **Emotion engine** (§8.1) — sentiment + mood state machine.
12. **Voice pipeline** (§9) — TTS + viseme stream piped through WebSocket.
13. **Frontend scaffold** — Vite + R3F + Tailwind. Empty boardroom scene loads.
14. **Characters** — load 5 avatar `.glb`s into chairs; idle animation loops.
15. **WebSocket consumer** — render subtitles + speaker badge + model chip (chip must show `foundry:` or `databricks:` prefix so the audience sees the two backends).
16. **Lip-sync + audio playback** from streamed visemes + audio chunks.
17. **Emotion blendshapes** wired to per-agent sentiment events; **mood lighting** wired to mood event.
18. **Camera director** (§8.3) — auto-cuts on `turn_start`.
19. **Citation panel + mood meter + model swap dial + Agent 365 overlay**. Swap dial must offer both Foundry and Databricks options.
20. **Scenario picker + QR audience question flow**.
21. **End-debate decision card**.
22. **CI/CD workflows** (§14), deploy to a `dev` slot, smoke-test, then `prod` slot.
23. **Demo runbook** (`docs/demo-runbook.md`) — exact stage script with timings.
24. **Fallback recorded debate** for `/dev/fake-debate` (§16, rule 10).

---

## 18. Demo-Day Runbook (already written, just polish later)

`docs/demo-runbook.md` should cover:
- 30s pre-flight checklist (network, mic, fake-debate ready, blob primed)
- The exact line you say before clicking **Convene the Board**
- When to swap a model on stage for max effect (suggested: swap CFO from `databricks:claude-sonnet-4-5` → `foundry:gpt-5` during the second turn so the audience watches both the badge **and** the backend prefix flip live — perfect setup for the "Microsoft uniquely gives you OpenAI on Foundry AND Anthropic on Databricks on one Azure footprint" message)
- When to toggle the Agent 365 overlay (right before you talk governance)
- The audience QR moment (after scenario #1 wraps)
- The 60s landing — final decision card → flip back to your slides

---

## 19. Stretch Ideas (only if time permits)

- **"Sidebar" mode**: pull two agents into a side conversation while the others wait — shows nested workflows.
- **Tools beyond retrieval**: CTO calls a real "infra cost estimator" MCP tool; CFO calls a scenario modeler.
- **Memory across debates**: each session updates a "board memory" so debate #2 references decisions from debate #1.
- **Audience vote**: after the board decides, audience phones vote agree/disagree via QR — show the split.

---

**End of plan. Hand this whole file to GitHub Copilot in `.github/copilot-instructions.md` (or as a pinned doc in the workspace) and walk it through §17 step by step.**
