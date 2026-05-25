# Contoso AI — AI safety incident history (public-facing summary)

Maintained per `ai-safety-policy.md` Principle 4 (transparency). Full incident postmortems available in the customer trust portal.

## 2025-Q2
**Incident A2025-04-14** — Test-Gen Agent generated a unit test that hard-coded a fixture file containing an AWS access key. Customer's secret-scanner flagged at PR time. Contoso added a secret-scrub pre-output filter; no customer secret leaked beyond the PR. Time to fix: 28 hours from report.

## 2025-Q4
**Incident A2025-11-12** — Code Review Agent generated a suggestion that closely matched a snippet from a permissively-licensed Apache 2.0 library without attribution. Customer raised a license question. Resolved by adding attribution and updating the agent's prompt to surface license provenance. Time to fix: 17 hours from report.

## 2026-Q1
**Incident A2026-02-19** — On-Call Agent suggested a remediation step ("restart the Kafka consumer") that, if auto-applied, would have lost ~6 minutes of customer telemetry. Per Principle 2, the suggestion required human approval and was not auto-executed. The customer's SRE applied the suggestion intentionally with full context. We classify this as "near miss — policy worked." Postmortem published.

## Summary stats
- Reported safety incidents YTD: **3** (2025), **1** (2026 so far).
- Median time-to-resolution: **22 hours** (target: 72 hours).
- Customer data exposure: **0 incidents** to date.
- Auto-executed irreversible actions: **0** (policy prevented all).
