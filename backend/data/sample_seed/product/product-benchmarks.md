# Contoso AI — product benchmarks (Q1 2026)

Internal benchmarks measured against externally-available competitors using the SWE-Bench-Lite-2026 evaluation set and Contoso's proprietary "RealPRSuite" eval (1,840 real PRs from open-source repositories Apache-2.0+).

## Code Review Agent — accuracy

| Vendor | SWE-Bench-Lite pass rate | RealPRSuite reviewer-accept rate | Median latency P50 |
|--------|---------------------------|-----------------------------------|--------------------|
| Contoso AI Code Review | 47.2% | 64% | 2.8s |
| Acme Devbots | 38.1% | 51% | 12.4s |
| BetaCode | 31.7% | 44% | 6.1s |
| Cursor (review mode) | 41.5% | 58% | 3.2s |
| GitHub Copilot (review) | 44.3% | 61% | 2.4s |

## Test-Gen Agent — quality

| Vendor | Generated-test merge rate (unmodified) | False positive rate |
|--------|----------------------------------------|----------------------|
| Contoso AI Test-Gen | 51% | 7% |
| Acme Devbots | 39% | 14% |
| BetaCode | 42% | 19% |

## On-Call Agent — incident triage quality

Measured on 312 real Sev1/Sev2 incidents from 4 design partners (anonymized).

| Metric | Contoso On-Call | Industry baseline |
|--------|-----------------|---------------------|
| Median MTTR reduction | **31%** | n/a |
| First-correct-runbook identification | 71% | n/a |
| False-positive page suppression | 42% of paged events suppressed correctly | n/a |
| Engineer satisfaction (NPS in monthly survey) | **+58** | n/a |

## Performance — first-token latency

All measured at P95 for the customer's selected region:

| Agent | India P95 | SG P95 (cross-border) | Target |
|-------|-----------|-----------------------|--------|
| Code Review | 720ms | 1100ms | 800ms |
| On-Call | 980ms | 1340ms | 1200ms |
| PR Triage | 1.6s | 2.1s | 2.0s |
| Test-Gen | 3.7s | 4.4s | 4.0s |

SG cross-border numbers exceed targets — fixing once SG-dedicated inference cluster live (see `data-residency-by-country.md`).
