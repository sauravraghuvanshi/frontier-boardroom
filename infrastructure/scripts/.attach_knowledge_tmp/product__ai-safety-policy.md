# Contoso AI — AI safety & responsible deployment policy v3.1

Effective date: 2026-01-15. Reviewed by: Chief Legal Officer, CTO, CEO.

## Principle 1 — No training on customer data
- Customer source code, PRs, on-call payloads, infrastructure logs are **never** used to train Contoso's models or any third-party foundation model.
- Foundation-model providers (Foundry, Databricks Mosaic AI) are contractually bound to zero-retention inference for Contoso traffic. This is documented in our Schedule A vendor amendments.
- Internal eval datasets are constructed exclusively from synthetic data + permissively-licensed open-source repos.

## Principle 2 — Human-in-loop for irreversible actions
- Agents may **propose** code changes, infra changes, on-call actions — but **never auto-execute** an irreversible operation without a human approving in the customer's existing review interface.
- "Irreversible" defined per agent in `agent-execution-policy.md` (e.g. for Infra-Ops Agent: any `terraform destroy`, any IAM role attach, any DNS change).
- The On-Call Agent is explicitly forbidden from auto-resolving incidents — it only drafts the triage.

## Principle 3 — 72-hour response on harmful output
- If an agent emits a harmful output (broadly: insecure code that leaks secrets, biased PR comments, dangerous infra suggestions), the SLA from customer report to Contoso response is **72 hours**.
- Response workflow: contain → reproduce → root cause → patch → notify all affected tenants. Coordinated by Trust & Safety on-call rotation (3 senior engineers).
- 2025 incidents: 2 reports, both resolved within SLA. Both were Test-Gen Agent generating a unit test that exposed a secret in a fixture file. Patched with secret-scrubbing pre-output filter.

## Principle 4 — Transparency
- Every agent output is tagged with the model version + provider + timestamp + audit-log ID, accessible to the customer's compliance team.
- Public model-card published per agent (see contoso.ai/model-cards) — discloses training data, evaluations, known failure modes.

## Principle 5 — Refuse capability that crosses safety lines
- No malware / offensive cyber agents.
- No agents that auto-generate fake commit signatures or impersonate humans without disclosure.
- No fully-autonomous customer-facing communication agents (e.g. responding to customer support tickets without disclosure of AI involvement).

## Governance
- Quarterly AI safety review attended by CEO, CTO, CLO, head of T&S.
- External red-team engagement: contracted with HiddenLayer AI (US) for quarterly adversarial evaluation.
- Bug bounty for safety issues: $500 – $25,000 sliding scale.
