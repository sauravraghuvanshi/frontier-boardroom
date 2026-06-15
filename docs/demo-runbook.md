# Demo Runbook — The Frontier Boardroom

Total run time: **~9 minutes**. Practice cues, do not improvise model swaps.

The room is a Teams-style chat: left rail = scenario channels, center = live message stream with mood pill + decision card, right rail = participants with inline model-swap dropdown + citation drawer + audience-question QR. (The 3D scene was retired 2026-05-20 — see AD-11.)

## 0:00 — Cold open (15s)
- Speaker: *"What if your entire C-suite met for a strategic decision in 90 seconds, with citations on every claim?"*
- Click **Channels → SEA Expansion**. Mood pill resets to **cordial**.

## 0:30 — The debate begins
- CEO (`foundry:CEO@5` — GPT-5 on Foundry) opens. The bubble shows the model chip; citation chips appear inline as the briefing block is grounded.
- Right rail begins filling the citation drawer in real time.

## 1:30 — CFO presents the numbers (the model-swap moment)
- CFO (`databricks:databricks-claude-sonnet-4-6`) gives the SEA pipeline figure and CAC math.
- **Pause here.** Speaker: *"Notice the chip — CFO is Claude Sonnet 4.6 running on Azure Databricks Mosaic AI. Watch what happens when I swap him to GPT-5 on Foundry mid-debate."*
- In the **Participants** rail, click CFO → model dropdown → `foundry:CEO@5`. The next CFO turn renders the new chip and a noticeably different voice.
- Speaker: *"Same boardroom, different brain. The router (`model_router.py`) decides who goes where — never bypassed."*

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

## 8:45 — Outro
- Hot-swap CEO to a different Foundry model to show provider-agnostic chair.
- Show the Participants rail full model registry.

## Fallback
- If any provider 5xx's: hit `GET /dev/fake-debate` (or set `USE_FAKE_DEBATE=true`).
- The fixture replays a recorded SEA debate end-to-end so the demo never goes silent.
