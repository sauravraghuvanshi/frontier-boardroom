# Customer case study — AcmeBank India (anonymized)

**Industry**: Mid-tier private bank, India.
**Size**: 320 application developers, 8 product lines (retail banking, cards, wealth, NBFC, etc.).
**Contoso AI products used**: Code Review Agent, PR Triage Agent, On-Call Agent.
**Region**: India-resident.

## Before
- PR review queue median wait: 28 hours.
- Top 10% of senior engineers spent ~9 hours/week on PR review (estimated through manual time-tracking sample).
- Sev2 incidents per quarter: 14, with median MTTR 3h 50min.
- Code-related security findings caught at PR-time: 22% (rest caught post-merge or by quarterly audit).

## Deployment
- Pilot: 25 developer seats in retail banking team, Sep 2025.
- Expansion: 320 seats across all product lines, Mar 2026.
- Setup time: 4 hours (DevOps team) + 1-day workshop with Contoso AI customer success.
- Special requirements: India-resident inference (Mumbai PoP). All audit logs exported to bank's SIEM (Splunk).

## After (6 months in)
- PR review queue median wait: **6 hours** (-79%).
- Senior engineers PR-review time: **~3 hours/week** (-67%).
- Sev2 incidents: 9 per quarter (-36%) with median MTTR **2h 10min** (-44%).
- Security findings caught at PR-time: **61%** (+39pp). On-Call Agent runbook-lookup accuracy: 72%.

## ROI
- Contractual ARR: $249/seat/mo × 320 = $80K/mo = **$956K/yr**.
- Estimated engineer-time saved: 320 devs × 1.2h/wk × $30/hr × 50wk = **$576K/yr**.
- Estimated incident-cost reduction: 5 fewer Sev2 × $25K avg cost = **$125K/yr**.
- Net direct ROI: ROI-positive at 18 months; intangible benefits (security posture, audit confidence) not modeled.

## Customer quote (provided by their VP Engineering, used with permission)
> "We adopted Contoso AI's Code Review Agent because we needed the inference in-country for our regulator. We kept it because the on-call agent saved us a Sunday-night escalation that would have been a Page-1 incident."
