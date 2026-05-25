# Customer case study — FintechCo SG (anonymized)

**Industry**: B2B payments fintech, Singapore. Series C-stage.
**Size**: 110 developers.
**Contoso AI products**: Code Review Agent, PR Triage, Test-Gen (full pro suite).
**Region**: today routes via SG control + India inference; will move to SG-dedicated inference when GA in Q3 2026.

## Use case
FintechCo processes ~$2.4B/yr in B2B payments across SEA. Engineering org grew from 40 to 110 devs in 18 months. PR review backlog became material drag on velocity.

## Deployment
- Pilot: 22 devs in 2 squads, Jan 2026.
- Expansion: 110 devs, May 2026.
- ARR: 110 × $89/mo × 12 = **$117,480 ARR**.
- 12-month commit signed; expansion to all 110 happened 4 months earlier than projected.

## Results (3 months in)
- PR queue length (P50): from 14h → 4h.
- Test-Gen Agent contribution: ~38% of new tests merged were started by the agent.
- Code Review Agent caught **6** material security regressions (auth-bypass patterns) at PR-time over the first quarter.

## Quote
> "We chose Contoso because we needed an agent that respected the MAS data-handling rules without us having to read the entire DPA twice. The fact that it caught two PCI-relevant regressions in month one paid for the deal." — Head of Platform, FintechCo

## Notes
- Contingent on SG-dedicated inference being GA by Sep 2026 — customer flagged latency P95 > 1100ms unacceptable for production code review on time-sensitive PRs.
- Largest at-risk renewal in SG pipeline for 2026-Q4.
