# Contoso AI — security posture (May 2026)

## Certifications & attestations
- **SOC 2 Type I**: ✅ obtained Aug 2025 (Schellman). Annual renewal.
- **SOC 2 Type II**: ⏳ in flight (Schellman). Observation period closes Mar 2026; report due Mar 2026.
- **ISO 27001:2022**: ⏳ stage-1 audit Apr 2026 (BSI). Stage-2 target Aug 2026.
- **ISO 27701** (privacy): planned 2026-Q4 after 27001.
- **HIPAA**: ❌ not pursued in 2026 (no healthcare customer in plan).
- **FedRAMP**: ❌ not pursued.
- **CERT-In empanelment (India)**: ⏳ application in flight, ~12-month process. Required for India government / PSU customers.
- **PDPA SG / DPDP India**: ✅ compliance reviewed by external counsel Apr 2026.

## Encryption
- At rest: customer data encrypted with AES-256, per-tenant data encryption keys (BYOK option via Azure Key Vault).
- In transit: TLS 1.3 minimum; mTLS for agent → router service-to-service.
- Customer-managed keys offered on enterprise tier; default is Contoso-managed in regional Key Vaults.

## Identity & access
- SSO: SAML 2.0 + OIDC. Mandatory for enterprise tier.
- MFA: enforced for all admin users.
- Principle of least privilege: agent service accounts scoped to one tenant only; no cross-tenant identity exists.

## Audit logging
- Every agent action and admin action recorded with `(tenant_id, timestamp, principal, action_type, target_resource, outcome)` in tamper-evident log.
- Log retention: 7 years for enterprise tier; 1 year for pro tier.
- Customer-accessible export API (monthly cadence, included in enterprise).

## Vulnerability management
- All container images scanned in CI (Trivy + Snyk).
- External pen-test: HackerOne crowdsourced + annual specialist engagement with NCC Group.
- Last pen-test (Apr 2026): 0 critical, 3 high, 11 medium findings — all remediated within 60 days.

## Incident response
- 24/7 on-call rotation, 3-tier (Tier 1 customer support → Tier 2 SRE → Tier 3 platform engineering).
- Sev1 SLA: detect → ack < 15 minutes; customer comms < 60 minutes; postmortem published < 5 business days.
- 2025 incident summary: 2 Sev2 (both data-router misroute, no customer data loss), 0 Sev1.

## Known open security tech debt
- **Item #6 (P0)**: On-Call Agent webhook signing accepts replay within 5min window. Effort: 1 engineer-week.
- **Item #4 (P0)**: customer data isolation in fine-tuned models — per-tenant LoRA needed. Effort: 8 engineer-weeks. Material for SOC 2 Type II close.
