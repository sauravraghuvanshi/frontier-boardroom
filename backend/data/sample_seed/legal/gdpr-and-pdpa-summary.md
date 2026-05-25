# GDPR vs PDPA / DPDP — implications for Contoso AI agents

Contoso AI's agents ingest customer source code, code review comments, PR descriptions, on-call alert payloads, and infrastructure logs. Every regime below classifies most of this as personal data because it includes (a) commit-author email/identity, (b) on-call engineer name/contact, (c) sometimes embedded customer/end-user data inside repositories.

## Core obligations shared across PDPA (SG/MY/TH/PH) and DPDP (India)
- **Lawful basis**: customer-supplied consent + contract performance. Documented in DPA appendix to MSA.
- **Purpose limitation**: data ingested for code-review/on-call agent execution may not be used to train base foundation models without separate consent. Contoso's stance: zero training on customer data (see `ai-safety-policy.md`).
- **Retention**: ephemeral inference context retained 7 days for debugging; persistent fine-tunes default OFF, opt-in only.
- **Subject rights**: access, correction, deletion within 30 days (60 in some regimes).

## Where regimes diverge — cross-border transfer
- **GDPR**: Standard Contractual Clauses (SCCs) + Transfer Impact Assessment. Contoso AI **has not** completed SCCs — EU customers blocked.
- **PDPA SG**: consent-based, written notification adequate.
- **PDPA TH**: notification + DPO appointment within 30 days of close.
- **DPDP India**: Data Protection Board may notify "restricted countries"; today none, but watch list.
- **UU PDP Indonesia**: country-of-origin storage strongly preferred for sensitive sectors.

## Contoso AI per-country DPA templates (status)
- ✅ India DPA template (signed by all 6 India banking customers)
- ✅ Singapore DPA template
- ⏳ Indonesia DPA template (draft in legal review — blocks ID financial-services pipeline)
- ❌ Vietnam DPA template (not started)
- ❌ EU GDPR DPA + SCCs (not started)

## Recommendation
Document a per-country DPA template before any SEA close. Critical path: Indonesia DPA template (~2 legal-weeks).
