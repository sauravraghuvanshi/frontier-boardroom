# Demo Runbook — The Frontier Boardroom

Total run time: **~9 minutes**. Practice cues and use the configured production
models; public model swapping is intentionally disabled.

The room is a Teams-style chat: left rail = scenario channels, center = live
message stream with mood pill and decision card, right rail = participants,
citation drawer, and audience-question QR. (The 3D scene was retired 2026-05-20
- see AD-11.)

## 0:00 — Cold open (15s)
- Speaker: *"What if your entire C-suite met for a strategic decision in 90 seconds, with citations on every claim?"*
- Click **Channels → SEA Expansion**. Mood pill resets to **cordial**.

## 0:30 — The debate begins
- CEO (`foundry:CEO@5` — GPT-5 on Foundry) opens. The bubble shows the model chip; citation chips appear inline as the briefing block is grounded.
- Right rail begins filling the citation drawer in real time.

## 1:30 - CFO presents the numbers (the multi-provider moment)
- CFO (`databricks:databricks-claude-sonnet-4-6`) gives the SEA pipeline figure and CAC math.
- **Pause here.** Speaker: *"Notice the chip - CFO is Claude Sonnet 4.6 running on Azure Databricks Mosaic AI, while the chair runs through Microsoft Foundry."*
- Speaker: *"Same boardroom, different model providers. The router decides who goes where, while every agent shares the same grounding layer."*
- Do not expose or enable the administrator-only model-swap route for a public demo.

## 3:00 — CMO/CTO push back
- CMO (`foundry:gpt-4o`) brings brand-awareness signals and softened coach/drill framing (L-19).
- CTO (`foundry:gpt-4.1`) raises infra latency and SLOs.
- Mood pill tilts **debating**; bubbles tighten in cadence.

## 4:30 — Legal's risk read
- Legal (`databricks:databricks-claude-opus-4-6`) cites the DPDP analog and SG/MY DPA requirement.
- Right-rail citation drawer highlights `legal/dpdp_brief.md` with confidence and hops.
- Vote parser will require Legal in `spoken_roles` before convergence fires (L-16).

## 6:00 — Convergence
- CEO synthesizes. Mood pill slides **converging**.
- Convergence detector fires after Legal has spoken; debate stream freezes on `debate_end` (no further tokens allowed).

## 7:00 — Decision card
- Inline decision card pins in the center pane with parsed votes (reject wins ties — see boardroom.py vote parser).
- Speaker: *"That's a fully-grounded, multi-provider, citation-backed decision in seven minutes."*

## 7:30 — Prep mode encore (optional)
- Open **Prep** tab → pick **CEO** seat → choose **drill** sub-mode → ask `@CTO what's the infrastructure cost increase if we expand to SEA?`
- Speaker: *"One human, one agent — and the CEO can pull a second voice in mid-thread. Watch the delegated agents block surface inside the briefing."*

## 8:00 — Audience QR
- Scan the right-rail QR; audience submits a prompt that re-runs the debate at lower fidelity.

## 8:45 - Outro
- Show the model chips and explain that role-to-model assignments are
  configuration-driven rather than hardcoded in agent logic.
- Close on the citation drawer and decision card.

## Fallback
- Before the event, explicitly enable and validate recorded-debate mode in the
  controlled demo environment.
- The public production deployment intentionally returns `404` for diagnostic and
  administrative routes, including `/dev/fake-debate`.
- Do not change production safety settings live on stage. Keep the validated
  fallback environment open in a separate browser tab.

## Pre-demo production checks

- Confirm backend `/health` returns `{"status":"ok"}`.
- Confirm `/dev/router-probe`, `/dev/fake-debate`, and model-swap routes are not
  publicly accessible.
- Run one CFO/Sonnet and one Legal/Opus prep turn and confirm each streams a
  complete response with citations.
- Confirm the frontend and backend use the same immutable commit SHA.
- Never paste or display model credentials, Key Vault values, or deployment logs.
