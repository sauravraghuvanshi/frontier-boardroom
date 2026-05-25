# Data residency requirements — Contoso AI agent platform

Contoso AI's agents process customer source code, PRs, on-call alerts, and infrastructure telemetry. All of this is "personal data" or "regulated data" under most APAC regimes. Below is the per-country posture as of May 2026.

| Country | Law | Resident data required? | Contoso AI status | Notes |
|---------|-----|--------------------------|-------------------|-------|
| **India** | DPDP Act 2023 | YES — for "significant data fiduciaries" (most banks, all fintechs) | ✅ Compliant. Mumbai + Hyderabad regions, inference in-country. | All India banking customers run on India-resident plane. |
| **SG** | PDPA + MAS guidelines (fin services) | Recommended | ⏳ Partial. Inference today proxied via SG control plane but compute in India — flagged in 4/14 SEA customer interviews. | Need dedicated SG inference cluster before SG financial-services close. |
| **ID** | PP 71 / UU PDP | YES — strict; local PoP mandatory for regulated industries | ❌ Not compliant. No ID PoP today. Blocks all ID financial-services deals. | Build Jakarta region (~6 engineer-weeks + $0.4M annual infra). |
| **VN** | Decree 53/2022 | YES — for some sectors (banking, telecom, government) | ❌ Not compliant. | Local rep required; LLC formation 4–6 months. |
| **TH** | PDPA 2019 | No, with controls | ⏳ Partial. Cross-border notification process not yet templated. | Document DPA template before any TH close. |
| **PH** | Data Privacy Act 2012 | Recommended | ✅ Compliant via NPC registration in flight. | NPC registration application filed 2026-03-04. |
| **MY** | PDPA 2010 (revised 2024) | No | ✅ Compliant. Cross-border permitted with consent. | |
| **UAE** | PDPL 2021 | Recommended for "important data" | ✅ Compliant. UAE region not built; we use SG control + India inference. | Acceptable for non-banking customers. |
| **US** | sector-specific (HIPAA, FERPA, GLBA) | varies | ⏳ Partial. SOC 2 Type II in flight (target Mar 2026). | No HIPAA controls yet — blocks healthcare buyer Mayo Clinic. |
| **EU** | GDPR | n/a (data residency not required, but transfer mechanisms required) | ❌ Not compliant for production workloads — no SCCs in MSA. | EU not in 2026 plan. |

## Engineering effort estimate to reach full SEA compliance
| Country | Effort | Annual recurring infra cost |
|---------|--------|------------------------------|
| SG dedicated inference cluster | 4 engineer-weeks | $180K/yr |
| ID Jakarta PoP | 6 engineer-weeks | $400K/yr |
| VN HCMC PoP | 8 engineer-weeks (incl. LLC formation legal) | $260K/yr |
| TH cross-border DPA template | 1 engineer-week + legal | $0 |
| **Total** | **~19 engineer-weeks** | **~$840K/yr** |
