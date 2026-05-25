# 2025 win/loss analysis — Contoso AI

Sample: 312 closed-out enterprise deals, 2025-01-01 → 2025-12-31. "Enterprise" defined as engineering org > 50 devs.

## Top-line
- Win rate (India): **38%** (118 won of 311 contested)
- Win rate (SEA pilots): **19%** (12 won of 64 contested)
- Win rate (US lighthouse): **22%** (3 won of 14 contested)
- Average ACV at close: $112K (India), $148K (SEA), $396K (US)

## Top loss reasons (SEA, weighted by deal value)
1. **"No local entity / no SEA support"** — 81% of lost SEA deals cite this. Primary, structural blocker.
2. **Data residency uncertainty** — 63% (often cited together with #1).
3. **"Foundation-model vendor lock-in fear"** — 27%. Buyers worried we depend on a single LLM provider; addressed by model-agnostic router (see `architecture-model-router.md`).
4. **Pricing — competitor undercut** — 22%.
5. **Hindi-language UI in admin console** — 14% (now resolved in v4.6 release).

## Top win factors
- **Founder-led sales** in SEA pilots — every won SEA deal had a CEO or CTO in at least 2 customer meetings.
- **Code Review Agent demo on customer's own repo** — close rate 4.1x baseline when prospect runs Contoso against a real PR before signing.
- **Same-region data residency commit** — closes the regulated-industry buyer 2.7x more often than "data resident in Singapore".

## Acquisition target (Cohort.dev) economics
- **Price**: $8M in Contoso stock (paid as 4.8M shares at $1.67/share — implies $250M post-money basis).
- **ARR acquired**: $3.1M.
- **Logos acquired**: 22 enterprise (SG: 14, TH: 5, MY: 2, PH: 1).
- **Implied EV/ARR**: 2.6x — below Series B comparable transactions (3.5–5.5x), reflects single-product / single-region risk.
- **Synergy NPV (modeled)**: $11M over 3yr — comes from cross-sell of On-Call + Test-Gen agents into the acquired base.
