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

## Live deployment

- Frontend: https://app-frontier-dev-frontend.azurewebsites.net
- Backend:  https://app-frontier-dev-backend.azurewebsites.net (`/health` 200)
- RG `rg-frontier-boardroom-dev` (subscription details kept out of public docs).
- See internal `DEPLOYMENT.md` for full resource inventory, rebuild commands, and the
  list of parked items (Anthropic key, Databricks PAT, Foundry model deployments,
  Speech/Language keys) needed before live debates work end-to-end.
