# Contoso AI — SLA, uptime, and reliability

## Customer SLA tiers

| Tier | Uptime SLA | Credit | First-response (P1) | Restoration target (P1) |
|------|------------|--------|----------------------|--------------------------|
| Starter | 99.5% | 5% of monthly fee if breached | 4 hours | 12 hours |
| Pro | 99.9% | 15% of monthly fee if breached | 1 hour | 4 hours |
| Enterprise | 99.95% | 30% credit + named TAM | 15 minutes | 2 hours |

## Achieved uptime (last 12 months)
- Code Review Agent: **99.92%** (~6 hours of downtime spread across 4 incidents)
- On-Call Agent: **99.97%** (one minor outage 2026-02)
- PR Triage / Test-Gen: **99.95%**
- Infra-Ops Agent (beta tier — no SLA): 99.8%

## Major incidents (2025-04 → 2026-04)
- **2025-08-12** Foundry regional outage (Asia-East) — 2h 14min impact on Code Review Agent for non-India customers. Mitigation: model router fallback to Databricks Mosaic AI Sonnet 4.5 (manual flip — automation in tech debt #3).
- **2025-11-04** Customer-data-router config push regression — 47-minute Sev2; 0 customer-data exposure. Postmortem published, RCA added a regression test.
- **2026-02-19** Brief On-Call Agent outage (8min) — Kafka consumer-lag in event pipeline. Auto-recovered.

## Reliability roadmap
- Auto-failover model router (tech-debt #3): cuts manual-flip exposure to zero.
- Multi-region active-active for Code Review Agent (planned Q3 2026).
- Chaos engineering monthly cadence introduced 2026-04 (using Azure Chaos Studio).
