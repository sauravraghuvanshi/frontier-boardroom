# Competitor landscape — AI agents for engineering teams

Contoso AI competes in the "AI agents for engineering productivity" segment. Comparison below is for the SEA + India region; US competitors (Cursor, Devin, Cognition) tracked separately.

| Vendor | HQ / stronghold | Primary agent product | Pricing band (per dev seat / mo) | Strength | Weakness |
|--------|-----------------|------------------------|----------------------------------|----------|----------|
| Acme Devbots | Singapore | PR review bot, basic code completion | $39 (starter), $79 (pro), $149 (enterprise) | Strong SG brand, MAS-compliant infra | Slow agent latency (~12s median); no on-call agent |
| BetaCode | Jakarta | Test generation, code search | $19 / $59 / $129 | Aggressive pricing; large ID dev community | No SLA; English docs weak |
| GammaShip | Bangkok | DevOps + on-call assistant | $29 / $89 / $189 | Strong Thai market presence | Limited English language support; thin code review |
| **Contoso AI (us)** | Chennai, India | Full suite: Code Review, PR Triage, On-Call, Test-Gen, Infra-Ops | $25 (starter), $89 (pro), $249 (enterprise) | 5-agent suite, India-data-resident, model-agnostic backbone | No local presence in SEA yet |
| Cursor (US, observed) | San Francisco | IDE + agent | $20 / $40 | Best-in-class IDE integration | Not localized; no on-call; no enterprise data residency in IN/SEA |
| Acquisition target ("Cohort.dev", SG-based, in due-diligence) | Singapore | Code review only | n/a | 22 enterprise SG+TH logos, $3.1M ARR | Single-product, weak retention (NRR 102%) |

## Why we win in India
- India-resident inference (Chennai + Mumbai GPU pool) — competitors all proxy through SG.
- Native Hindi/Indic-language commit-message and PR-description generation.
- Per-seat pricing 38% below Acme Devbots at enterprise tier.

## Why we lose in SEA (today)
1. No local entity → 81% of lost SEA deals cite "no Singapore/Jakarta presence" as primary blocker (see `win-loss-report-2025.md`).
2. Brand awareness gap (aided awareness SG: 11%, ID: 4% — see `brand-awareness-sea.csv`).
3. No dedicated SEA-region data plane (cross-border inference triggers PDPA/UU PDP review).

## Movement to watch
- **Acme Devbots** raised $40M Series C in Feb 2026 — telegraphed in Tech in Asia interview that they intend to enter India market in Q3.
- **Cursor** announced "Cursor Cloud" with regional residency in Apr 2026 — could leapfrog Acme in SG fintech.
- **Cohort.dev** (potential acquisition target): preliminary $8M-in-stock offer made, awaiting board decision. Adds 22 SG+TH logos and a local entity overnight.
