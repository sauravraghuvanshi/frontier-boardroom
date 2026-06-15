"""
seed_cto_knowledge.py — generates CTO-exclusive technical & infrastructure data,
writes locally to backend/data/cto_seed/, and uploads to Azure Blob Storage
container `cto-knowledge`.

CTO-exclusive docs contain tech spend, infrastructure costs, and engineering
capacity data that only the CTO persona retrieves.

Numbers are intentionally conservative and grounded in AWS/Azure pricing.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

ROOT = Path(__file__).resolve().parents[2] / "backend" / "data" / "cto_seed"
ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "stfrontierboardroom")
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER_CTO", "cto-knowledge")

# ---- CTO-specific numbers ----
CTO_NUMBERS = {
    # SEA infrastructure costs (3-year projection)
    "infra_sea_yr1_musd": 1.2,
    "infra_sea_yr2_musd": 1.8,
    "infra_sea_yr3_musd": 2.4,
    # Regional breakdown
    "infra_sg_annual_kusd": 480,  # Primary hub, AWS/Azure premium
    "infra_id_annual_kusd": 360,  # Jakarta, secondary hub
    "infra_th_annual_kusd": 240,  # Bangkok, tertiary
    "infra_vn_annual_kusd": 180,  # HCMC, customer-facing only
    # Localization & compliance
    "localization_eng_weeks": 10,
    "localization_eng_cost_weekly_kusd": 12,  # blended rate
    "compliance_infra_annual_kusd": 180,  # Data residency, audit logs, monitoring
    # Headcount for SEA expansion
    "sea_eng_headcount_yr1": 9,
    "sea_eng_avg_cost_monthly_kusd": 8,
    "sea_devops_headcount": 2,
    "sea_qa_headcount": 2,
    # Scaling constraints
    "current_peak_rps_capacity": 8000,
    "required_rps_for_sea_y1": 2400,
    "new_region_min_vm_count": 6,
    "vm_cost_monthly_usd": 3200,
}


def w(relpath: str, content: str | bytes) -> Path:
    p = ROOT / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        p.write_bytes(content)
    else:
        p.write_text(content, encoding="utf-8")
    return p


def csv_str(rows: list[list]) -> str:
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    return buf.getvalue()


def build_files() -> list[dict]:
    """Returns manifest entries while writing CTO-exclusive files to disk."""
    n = CTO_NUMBERS
    manifest: list[dict] = []

    # ---- tech-spend: regional infrastructure costs ----
    w(
        "tech-spend/sea-infrastructure-costs-3yr.md",
        f"""# SEA Infrastructure Costs — 3-Year Projection

## Summary
Expanding to SEA (SG primary, ID secondary, TH/VN customer-facing) requires $5.4M over 3 years:

| Year | Annual Cost | Notes |
|------|-------------|-------|
| Y1 | ${n['infra_sea_yr1_musd']}M | Core hub setup (SG) + pilot replicas (ID/TH) |
| Y2 | ${n['infra_sea_yr2_musd']}M | ID hub elevation + TH scaling |
| Y3 | ${n['infra_sea_yr3_musd']}M | Full redundancy + compliance monitoring |

## Breakdown by Region (Annual, Steady State)

| Region | Use Case | Monthly Cost | Annual | Assumptions |
|--------|----------|--------------|--------|-------------|
| Singapore | Primary hub + failover | ${n['infra_sg_annual_kusd'] / 12:.0f}k | ${n['infra_sg_annual_kusd']}k | 3x compute, managed DB, WAF |
| Indonesia | Jakarta cluster + failover | ${n['infra_id_annual_kusd'] / 12:.0f}k | ${n['infra_id_annual_kusd']}k | 2x compute, read replicas |
| Thailand | Bangkok customer-facing | ${n['infra_th_annual_kusd'] / 12:.0f}k | ${n['infra_th_annual_kusd']}k | 2x app tier, shared DB read |
| Vietnam | HCMC edge cache only | ${n['infra_vn_annual_kusd'] / 12:.0f}k | ${n['infra_vn_annual_kusd']}k | CloudFront + Redis cluster |

**Steady-state annual (Y2+):** ${(n['infra_sg_annual_kusd'] + n['infra_id_annual_kusd'] + n['infra_th_annual_kusd'] + n['infra_vn_annual_kusd']) / 1000:.1f}M

### Cost Drivers
- **Compute:** t4g.large / t4g.xlarge (Graviton, 30% cheaper) across 4 regions
- **Networking:** ~15% of compute (NAT, cross-region replication, CDN)
- **Storage:** PostgreSQL Multi-AZ + S3 replication, ~10% of compute
- **Premium:** AWS/Azure local presence tax (SG ~20% over US pricing; ID ~35%)

### Optimization Levers
- Move non-critical workloads to Spot (saves ~25% on dev/staging)
- Use Reserved Instances for 12-month commitment (saves ~18% on production)
- Co-locate with CDN PoPs to reduce transit (saves ~8%)
""",
    )

    w(
        "tech-spend/localization-and-compliance-costs.md",
        f"""# Localization & Compliance Infrastructure Costs

## Engineering Effort (One-time)

| Task | Engineers | Weeks | Cost |
|------|-----------|-------|------|
| Multi-tenant row-level encryption | 2 | {n['localization_eng_weeks'] // 2} | ${n['localization_eng_weeks'] // 2 * n['localization_eng_cost_weekly_kusd'] * 2:.0f}k |
| Payment gateway localization (stripe → local) | 1.5 | {n['localization_eng_weeks'] // 3} | ${n['localization_eng_weeks'] // 3 * n['localization_eng_cost_weekly_kusd'] * 1.5:.0f}k |
| Compliance monitoring & audit logs | 1 | {n['localization_eng_weeks'] // 5} | ${n['localization_eng_weeks'] // 5 * n['localization_eng_cost_weekly_kusd']:.0f}k |
| Regional failover + disaster recovery | 2 | {n['localization_eng_weeks'] // 3} | ${n['localization_eng_weeks'] // 3 * n['localization_eng_cost_weekly_kusd'] * 2:.0f}k |

**Total one-time engineering:** ${n['localization_eng_weeks'] * n['localization_eng_cost_weekly_kusd'] * (2 + 1.5 + 1 + 2) / (2 + 1.5 + 1 + 2):.0f}k (blended ~${n['localization_eng_weeks'] * n['localization_eng_cost_weekly_kusd']:.0f}k)

## Ongoing Infrastructure (Annual)

- **Compliance monitoring:** ${n['compliance_infra_annual_kusd']}k/yr (Cloudflare + DataDog)
  - WAF for data residency enforcement: $40k/yr
  - Audit log retention (7 years, SG/ID/TH): $80k/yr
  - Real-time encryption monitoring: $60k/yr

## Regulatory Framework by Country

| Country | Law | Data Residency Requirement | Our Response |
|---------|-----|---------------------------|--------------|
| Singapore | PDPA + MAS | Recommended (cross-border allowed with controls) | Local read-replica + encryption in transit |
| Indonesia | UU PDP | **Mandatory** local processing for regulated industries | Jakarta cluster, encryption at rest |
| Thailand | PDPA 2019 | Notification only (no mandatory local storage) | Local PoP acceptable, CDN preferred |
| Vietnam | Decree 53 | Local storage required for regulated data | HCMC edge only for non-PII analytics |

**Key risk:** If customer is fintech/banking, Indonesia enforcement is strict. Budget 8–12 week engagement with local counsel (~$120k) before contract signature.
""",
    )

    w(
        "tech-spend/engineering-capacity-by-region.md",
        f"""# Engineering Capacity for SEA Rollout

## Headcount Plan (Year 1)

| Role | SG | ID | TH | Total | Monthly Cost (blended) |
|------|----|----|----|-----------|----|
| Backend Engineer | 3 | 2 | 1 | 6 | ${6 * n['sea_eng_avg_cost_monthly_kusd']}k |
| DevOps / Platform | 1 | 1 | 0 | {n['sea_devops_headcount']} | ${n['sea_devops_headcount'] * n['sea_eng_avg_cost_monthly_kusd']}k |
| QA / Automation | 1 | 1 | 0 | {n['sea_qa_headcount']} | ${n['sea_qa_headcount'] * n['sea_eng_avg_cost_monthly_kusd']}k |

**Total Y1 SEA eng:** {n['sea_eng_headcount_yr1']} FTE @ ${n['sea_eng_headcount_yr1'] * n['sea_eng_avg_cost_monthly_kusd']}k/mo = ${n['sea_eng_headcount_yr1'] * n['sea_eng_avg_cost_monthly_kusd'] * 12:.0f}k/yr

Recruitment timeline: 8–10 weeks per hire (SG fast, ID/TH slower).

## Impact on India Roadmap

Dedicating 9 engineers to SEA localization (10 weeks) will:
- **Delay:** Advanced analytics feature (reporting, cohort analysis) → slip from Q2 to Q3
- **Maintain:** Q2 deliverables (bug fixes, performance) — current team capacity sufficient
- **Defer:** Mobile app v2 optimization → Q3

Net: India team productivity neutral, but feature velocity dips ~2 weeks.

## Scaling Constraints

### Current Platform Limits
- **Peak RPS capacity:** {n['current_peak_rps_capacity']}k RPS (10x safety margin)
- **Multi-region replication lag:** 200–500ms (acceptable for non-transactional queries)
- **Max concurrent connections:** 5,000 (PostgreSQL hard limit at our tier)

### Required for SEA Year 1
- **Projected peak RPS:** {n['required_rps_for_sea_y1']} RPS (30% of capacity)
- **Minimum instance count per region:** {n['new_region_min_vm_count']} (3 app, 2 cache, 1 monitoring)
- **VM cost per instance:** ${n['vm_cost_monthly_usd']}/mo
- **New region bootstrap cost:** {n['new_region_min_vm_count']} × ${n['vm_cost_monthly_usd']} = ${n['new_region_min_vm_count'] * n['vm_cost_monthly_usd']}/mo

### Upgrade Path if We Hit Limits
- Shard by country (6–8 weeks eng effort, $400k)
- Multi-region active-active (12 weeks, $600k + 3 new FTEs)
- Migrate to Managed Postgres Hyperscale (8 weeks, $200k one-time)

**Recommendation:** Reach out to AWS/Azure TAM at sign-off; negotiate reserved capacity for Y1–Y2.
""",
    )

    # ---- tech-debt ----
    w(
        "tech-debt/p0-items-sea-expansion.md",
        """# P0 Tech Debt Items (Blocking SEA Expansion)

## Must Close Before Rollout

1. **Multi-tenant row-level encryption** (6 eng-weeks)
   - Current: encrypted at rest (KMS), but plaintext in app memory
   - Required: field-level encryption + key per tenant
   - Risk: PDPA/UU PDP audits will flag plaintext ETL

2. **Replication lag monitoring** (2 eng-weeks)
   - Current: monitoring via custom script, no alerts
   - Required: CloudWatch metrics, Datadog alert + auto-failover
   - Risk: Customer data inconsistency during peak load

3. **Payment gateway localization** (3 eng-weeks)
   - Current: Stripe only (US entity, not registered in SEA)
   - Required: Stripe + Adyen + local gateway per region (MY via PermataBay, ID via DOKU)
   - Risk: Compliance block in regulated verticals

4. **Disaster recovery testing** (2 eng-weeks)
   - Current: DR plan exists, never tested in multi-region
   - Required: 2-region failover + 1-hour RTO SLA
   - Risk: 2AM production incident = uncontrolled chaos

5. **Audit logging for compliance** (3 eng-weeks)
   - Current: basic audit trail, local retention only
   - Required: immutable ledger (S3 Object Lock), 7-year retention per region
   - Risk: Regulatory audit failure

**Total:** 16 eng-weeks (~8 FTE weeks over 4 weeks of focus) or ~$200k contractor spend

## Optional (Nice-to-have, doesn't block launch)

- GraphQL batching (2 weeks) — helps with thin-client mobile apps
- Redis Cluster failover (1 week) — improves SG cache reliability
- Container orchestration (Kubernetes, 4 weeks) — for future scaling
""",
    )

    # ---- product / localization ----
    w(
        "product/localization-status.md",
        """# Product Localization Status

## i18n Readiness

| Language | Status | ETA | Notes |
|----------|--------|-----|-------|
| English | ✅ Complete | — | All strings extracted, 2,847 keys |
| Indonesian | ✅ Complete | — | Native QA in Jakarta team |
| Thai | ✅ Complete | — | Crowdsourced + native review |
| Vietnamese | ⏳ 60% | May 2026 | Translator on contract, date format tricky |
| Tagalog | ❌ Not planned | Q3+ | SKU deferral |
| Malay | ❌ Not planned | Q3+ | SKU deferral |

## UI/UX Localization

- **Date/Time formats:** SG (ISO 8601), ID/TH/VN (locale-specific) — 3-day effort to verify
- **Currency display:** SGD, IDR, THB, VND — pricing tier display needs review
- **RTL support:** Not required (all target languages LTR)
- **Mobile keyboard:** Thai + Vietnamese input methods tested on iOS 17.3

## Payment & Compliance UI

- **PCI compliance:** Forms use hosted Stripe tokenization (zero plaintext exposure)
- **Local payment methods:** Displays 8+ local wallets per region (GCash, GoPay, OVO, etc.)
- **Regional T&Cs:** Separate legal docs per country (120 hours contractor time, ~$18k)

**Launch readiness:** 90% for SG/ID, 75% for TH, 60% for VN
""",
    )

    w(
        "product/platform-performance-targets.csv",
        csv_str([
            ["metric", "current_india", "target_sea", "strategy"],
            ["p50_latency_ms", "120", "180", "Accept regional penalty; caching helps"],
            ["p99_latency_ms", "680", "950", "Read replicas reduce contention"],
            ["availability_99.95", "99.95", "99.9", "Multi-region failover complexity"],
            ["cache_hit_rate_pct", "82", "78", "TH/VN edge cache; backfill async"],
        ]),
    )

    # Build manifest
    for p in sorted(ROOT.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            tags = [rel.split("/")[0], "cto_exclusive"]
            manifest.append({
                "path": rel,
                "title": p.stem.replace("-", " ").title(),
                "owner": "cto_exclusive",
                "date": "2026-06-15",
                "tags": tags,
            })

    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def upload(manifest: list[dict]) -> None:
    bsc = BlobServiceClient(
        f"https://{ACCOUNT}.blob.core.windows.net",
        credential=DefaultAzureCredential(),
    )
    container = bsc.get_container_client(CONTAINER)
    try:
        container.create_container()
    except Exception:
        pass
    for item in manifest:
        with (ROOT / item["path"]).open("rb") as f:
            container.upload_blob(name=item["path"], data=f, overwrite=True)
        print(f"uploaded {item['path']}")
    with (ROOT / "MANIFEST.json").open("rb") as f:
        container.upload_blob(name="MANIFEST.json", data=f, overwrite=True)
    print("uploaded MANIFEST.json")


def main() -> int:
    manifest = build_files()
    print(f"generated {len(manifest)} CTO-exclusive files under {ROOT}")
    if os.environ.get("SEED_BLOB_UPLOAD", "true").lower() == "true":
        try:
            upload(manifest)
        except Exception as e:  # noqa: BLE001
            print(f"upload skipped: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
