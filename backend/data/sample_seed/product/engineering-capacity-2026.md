# Contoso AI — engineering capacity 2026

## Headcount today
- Engineers total: **142**
  - Agent platform team (Code Review / PR Triage / Test-Gen): 48
  - On-Call & Infra-Ops agent team: 28
  - ML / model fine-tuning / eval: 22
  - SRE / infra / GPU pool ops: 18
  - Frontend (IDE plugins, admin console): 14
  - Security / SOC 2 / residency: 8
  - QA & release engineering: 4

## Allocation pressure (Q1–Q2 2026)
- **SEA localization + residency sprint** requires **9 engineers** across i18n (2), SG/ID/VN PoP infra (4), DPA tooling (1), customer-data isolation (2). Duration: **~10 weeks**.
- **Net impact**: pushes the India "advanced analytics" feature (Code Review Agent reviewer leaderboard, requested by 4 of top-10 India accounts) out by **6 weeks**.
- **SOC 2 Type II remediation**: 3 engineers (security team), 8 weeks. Critical-path for 3 enterprise deals worth $1.6M ARR.

## Velocity benchmarks
- PR throughput per engineer: 4.2 PRs/week (median, agent-platform team).
- Time to ship new agent action (idea → prod): 3.4 weeks median.
- Eng-driven incidents (P0/P1): 2.1 per quarter — within target.

## Build-vs-buy posture
- **Cohort.dev acquisition** would add ~28 engineers (their entire team if all stayed). Realistic post-acquisition retention: 60–70% over 12 months. Adds capacity but adds integration overhead (8–12 engineer-weeks).
- **Foundation models**: continue to rent (Foundry + Databricks). Building own foundation model is not financially viable at current ARR scale; revisit at $50M+ ARR.

## 2026 capacity outlook
- Net new hires (per `hiring-plan-2026.md`): +12 engineers (India) + 0 SEA eng + 0 US eng.
- Ending headcount: ~154 engineers.
- Capacity surplus available for opportunistic projects: ~4 engineer-quarters (one major experimental agent, e.g. "Doc-Gen Agent").
