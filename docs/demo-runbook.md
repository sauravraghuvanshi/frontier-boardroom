# Demo Runbook — The Frontier Boardroom

Total run time: **~9 minutes**. Practice cues, do not improvise model swaps.

## 0:00 — Cold open (15s)
- Lights dim, ambient hum.
- Speaker: *"What if your entire C-suite met for a strategic decision in 90 seconds, with citations on every claim?"*
- Click **Scenario → SEA Expansion**.

## 0:30 — The debate begins
- CEO (`foundry:gpt-5`) opens. Mood meter pulses **cordial**.
- Watch the citation panel populate as the CEO asks for data.

## 1:30 — CFO presents the numbers (the model-swap moment)
- CFO (`databricks:claude-sonnet-4-5`) gives the SEA pipeline figure ($4.2M Q1) and CAC math.
- **Pause here.** Speaker: *"Notice the chip — CFO is Claude Sonnet 4.5 running on Azure Databricks Mosaic AI. Watch what happens when I swap him to GPT-5 on Foundry mid-debate."*
- Open **Model Swap** panel → set CFO to `foundry:gpt-5` → next CFO turn shows new chip and a noticeably different style/voice.
- Speaker: *"Same boardroom, different brain. The router decides who routes where."*

## 3:00 — CMO/CTO push back
- CMO (`foundry:grok-3`) brings brand-awareness signals.
- CTO (`foundry:llama-3.3-70b-instruct`) raises infra latency and SLOs.
- Mood meter tilts **debating** → camera goes handheld for a beat.

## 4:30 — Legal's risk read
- Legal (`databricks:claude-opus-4`) cites the DPDP analog and SG/MY DPA requirement.
- Citation panel highlights `legal/dpdp_brief.md` with confidence and hops.

## 6:00 — Convergence
- CEO synthesizes, mood meter slides **converging** → lighting warms.
- 3 of 5 agents support → convergence detector fires.

## 7:00 — Decision card
- Decision card appears with vote breakdown.
- Speaker: *"That's a fully-grounded, multi-provider, citation-backed decision in seven minutes."*

## 8:00 — Audience QR
- Scan QR; demo audience-question route ingests a prompt and re-runs the debate at lower fidelity.

## 8:45 — Outro
- Hot-swap CEO to Grok-3 to show provider-agnostic chair.
- Cut to model registry view.

## Fallback
- If any provider 5xx's: hit `GET /dev/fake-debate` (or set `USE_FAKE_DEBATE=true`).
- The fixture replays a recorded SEA debate.
