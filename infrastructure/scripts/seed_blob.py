"""
seed_blob.py — generates realistic synthetic content for every file in the
§5 sample data plan, writes locally to backend/data/sample_seed/, and uploads
to Azure Blob Storage container `boardroom-knowledge`.

Numbers are kept *internally consistent* across files so agents citing them
produce a coherent debate. Re-running is idempotent.
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

ROOT = Path(__file__).resolve().parents[2] / "backend" / "data" / "sample_seed"
ACCOUNT = os.environ.get("AZURE_STORAGE_ACCOUNT", "stfrontierboardroom")
CONTAINER = os.environ.get("AZURE_BLOB_CONTAINER", "boardroom-knowledge")

# ---- Single source of truth for numbers used across documents ----
NUMBERS = {
    "sea_pipeline_q1_2026_musd": 4.2,
    "india_cac_usd": 320,
    "sea_cac_usd": 736,
    "cac_ratio_sea_over_india": 2.3,
    "runway_months": 18,
    "burn_monthly_musd": 1.4,
    "cash_balance_musd": 25.2,
    "arr_musd": 18.6,
    "arr_growth_yoy_pct": 71,
    "engineers_total": 142,
    "engineers_sea_localization_required": 9,
    "tech_debt_p0_count": 7,
    "data_residency_countries": ["SG", "ID", "VN", "TH", "PH", "MY"],
    "term_sheet_musd": 30,
    "term_sheet_valuation_musd": 220,
    "competitor_acquire_price_musd": 8,
    "competitor_arr_musd": 3.1,
    "infra_cost_india_monthly_kusd": 220,
    "infra_cost_sea_monthly_kusd_est": 380,
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
    """Returns manifest entries while writing files to disk."""
    n = NUMBERS
    manifest: list[dict] = []

    # ---------------- financials ----------------
    w(
        "financials/2025-Q4-pnl.md",
        f"""# 2025 Q4 P&L Summary

- ARR exit: ${n['arr_musd']}M (+{n['arr_growth_yoy_pct']}% YoY)
- Gross margin: 71%
- Monthly burn: ${n['burn_monthly_musd']}M
- Cash balance: ${n['cash_balance_musd']}M
- Implied runway: {n['runway_months']} months at current burn

Top drivers: India enterprise expansion, ARR per FTE up 18% QoQ.
Drags: Higher cloud spend due to 2 new regions (Mumbai + Hyderabad redundancy).
""",
    )

    w(
        "financials/2026-Q1-forecast.md",
        f"""# 2026 Q1 Forecast

| Region | Pipeline (USD) | Probability-weighted | Notes |
|--------|----------------|-----------------------|-------|
| India  | $12.1M | $7.3M | Core market |
| SEA    | ${n['sea_pipeline_q1_2026_musd']}M | $1.4M | New, lower conversion |
| ME     | $1.8M | $0.9M | Stable |

If SEA expansion is greenlit, projected incremental Q1 spend: $2.1M (sales hires, marketing, localization).
""",
    )

    w(
        "financials/runway-and-cash.md",
        f"""# Runway & Cash

- Cash on hand (EOM Apr 2026): ${n['cash_balance_musd']}M
- Monthly burn: ${n['burn_monthly_musd']}M
- Runway: {n['runway_months']} months
- SEA expansion incremental burn (steady state): +$0.65M/mo → runway drops to ~14mo

Trigger: if cash < $12M and SEA hasn't shown 30% MoM pipeline growth → freeze SEA hiring.
""",
    )

    w(
        "financials/unit-economics-by-region.csv",
        csv_str([
            ["region", "cac_usd", "ltv_usd", "ltv_cac", "payback_months"],
            ["India", n['india_cac_usd'], 4100, 12.8, 9],
            ["SEA-SG", n['sea_cac_usd'], 5200, 7.1, 14],
            ["SEA-ID", 690, 3900, 5.7, 17],
            ["SEA-TH", 720, 4200, 5.8, 16],
            ["SEA-VN", 610, 3700, 6.1, 15],
        ]),
    )

    # ---------------- market ----------------
    w(
        "market/sea-market-tam-sam-som.md",
        """# SEA SaaS market sizing (2026)

- TAM (SEA enterprise SaaS, our category): $9.4B
- SAM (mid-market + upper SMB, English-capable buyers): $2.1B
- SOM (year-1 realistic, with our current product fit): $48M

Anchor markets in order of fit: Singapore, Indonesia (Jakarta only), Thailand (Bangkok), Vietnam (HCMC).
Avoid year-1: Philippines (long sales cycles), Malaysia (price-sensitive).
""",
    )

    w(
        "market/india-vs-sea-cac-benchmarks.csv",
        csv_str([
            ["metric", "india", "sea"],
            ["blended_cac_usd", n['india_cac_usd'], n['sea_cac_usd']],
            ["sales_cycle_days", 42, 71],
            ["enterprise_conversion_pct", 22, 14],
            ["churn_annual_pct", 7, 11],
        ]),
    )

    w(
        "market/analyst-reports/gartner-sea-saas-2026.md",
        "# Gartner: SEA SaaS 2026 (excerpt)\n\nSEA mid-market SaaS spend +24% YoY. Top buyer concern: data residency.\nSingapore-based vendors win 38% of cross-border ASEAN deals.\n",
    )

    w(
        "market/analyst-reports/idc-india-cloud-2026.md",
        "# IDC: India Cloud 2026 (excerpt)\n\nIndia cloud spend +29% YoY, $17B by 2027. Domestic-listed buyers prefer India-resident data.\n",
    )

    w(
        "market/customer-interviews-sea.md",
        """# Customer interviews — SEA (n=14)

- 11/14 require local data residency at the country level (not just regional).
- 9/14 willing to pay 15% premium for SLA-backed local POPs.
- 4/14 already use a competitor; switch driver = pricing flexibility and Hindi-free interface.
""",
    )

    # ---------------- competition ----------------
    w(
        "competition/competitor-landscape-sea.md",
        """# SEA competitor landscape

| Vendor | Stronghold | Pricing | Weakness |
|--------|------------|---------|----------|
| Acme SG | Singapore | Premium | Slow product velocity |
| BetaCo  | Indonesia  | Aggressive | No SLA |
| GammaSys| Thailand   | Mid       | Poor English support |
| Ours    | India     | Flexible  | No local presence yet |
""",
    )

    w(
        "competition/win-loss-report-2025.md",
        f"""# 2025 win/loss

- Win rate (India): 38%
- Win rate (SEA pilots): 19% — primary loss reason: 'no local entity'
- Top win factor SEA: founder-led sales
- Acquisition target (${n['competitor_acquire_price_musd']}M in stock) → ARR ${n['competitor_arr_musd']}M, 22 enterprise logos in SG+TH.
""",
    )

    w(
        "competition/pricing-comparison.csv",
        csv_str([
            ["vendor", "starter_usd_mo", "pro_usd_mo", "enterprise_usd_mo"],
            ["Acme SG", 99, 399, 1499],
            ["BetaCo", 49, 199, 799],
            ["GammaSys", 79, 299, 1199],
            ["Ours", 69, 249, 999],
        ]),
    )

    # ---------------- product ----------------
    w(
        "product/tech-debt-register.md",
        f"""# Tech debt register

- P0 items: {n['tech_debt_p0_count']} (5 must clear before SEA multi-region rollout)
- Largest: multi-tenant row-level data residency (~6 engineer-weeks)
- Localization layer ready for Indonesian + Thai (incomplete for Vietnamese)
""",
    )

    w(
        "product/engineering-capacity-2026.md",
        f"""# Engineering capacity 2026

- Engineers total: {n['engineers_total']}
- SEA localization sprint requires {n['engineers_sea_localization_required']} engineers across i18n, infra, and product for ~10 weeks.
- Net impact: pushes 1 major India feature (advanced analytics) out by 6 weeks.
""",
    )

    w(
        "product/infra-cost-by-region.csv",
        csv_str([
            ["region", "monthly_cost_usd"],
            ["India", n['infra_cost_india_monthly_kusd'] * 1000],
            ["SEA (estimated)", n['infra_cost_sea_monthly_kusd_est'] * 1000],
            ["ME", 90000],
        ]),
    )

    w(
        "product/localization-readiness.md",
        "# Localization readiness\n\n- English: ✅\n- Bahasa Indonesia: ✅\n- Thai: ✅\n- Vietnamese: ⏳ (Q2 2026)\n- Tagalog: ❌\n- Bahasa Melayu: ⏳\n",
    )

    # ---------------- legal ----------------
    w(
        "legal/data-residency-by-country.md",
        """# Data residency requirements — SEA

| Country | Law | Resident data required? | Notes |
|---------|-----|--------------------------|-------|
| SG | PDPA + MAS guidelines (fin services) | Recommended | Cross-border with consent |
| ID | PP 71 / UU PDP | YES — strict | Local PoP mandatory for regulated industries |
| VN | Decree 53/2022 | YES — for some sectors | Local rep required |
| TH | PDPA 2019 | No, with controls | Notification obligations |
| PH | Data Privacy Act 2012 | Recommended | NPC registration |
| MY | PDPA 2010 (revised 2024) | No | Cross-border permitted with consent |
""",
    )

    w(
        "legal/gdpr-and-pdpa-summary.md",
        "# GDPR vs PDPA (SG, MY, TH, PH)\n\nPDPA regimes share core principles (consent, purpose limitation, retention) but diverge sharply on cross-border transfer mechanics. Document a per-country DPA template before any SEA close.\n",
    )

    w(
        "legal/employment-law-sea.md",
        "# Employment law (hiring in SEA)\n\n- SG: EP/S Pass timelines 2–4 weeks. No local entity strictly required if employing via EOR.\n- ID: PT PMA required to hire directly; EOR available for first 2 roles.\n- VN: Rep office permitted for sales-only; product/eng requires LLC.\n- TH: BOI promotion possible (15-yr tax incentives) for tech.\n",
    )

    w(
        "legal/ip-and-trademark-risks.md",
        "# IP & trademark — SEA\n\n- Our wordmark is unregistered in MY and VN. Risk: cybersquatting. Recommendation: file Madrid Protocol designating ASEAN before public announce.\n",
    )

    # ---------------- marketing ----------------
    w(
        "marketing/brand-awareness-sea.csv",
        csv_str([
            ["country", "aided_awareness_pct", "unaided_pct"],
            ["SG", 11, 2],
            ["ID", 4, 0],
            ["TH", 6, 1],
            ["VN", 3, 0],
        ]),
    )

    w(
        "marketing/go-to-market-playbook.md",
        """# SEA GTM playbook

1. Anchor on Singapore (HQ, English, regulatory clarity).
2. Land via 3 founder-led design partners by end of Q1.
3. Hire local SDR + AE in Singapore + Jakarta by end of Q2.
4. PR moment at Tech in Asia (June) with named design partners.
5. Channel partner deal with a regional SI for ID + VN.
""",
    )

    w(
        "marketing/partner-ecosystem-sea.md",
        "# Partner ecosystem SEA\n\n- Microsoft Indonesia, AWS Singapore, NCS (SG), MII (ID).\n- Two interested SI partners with active proposals.\n",
    )

    w(
        "marketing/campaign-history-2025.csv",
        csv_str([
            ["campaign", "region", "spend_usd", "mqls"],
            ["LinkedIn-Q3", "India", 80000, 1240],
            ["LinkedIn-Q3", "SEA", 40000, 280],
            ["TechInAsia booth", "SEA", 25000, 95],
        ]),
    )

    # ---------------- hr ----------------
    w(
        "hr/hiring-plan-2026.md",
        """# 2026 hiring plan

- India: +24 (eng 12, sales 8, ops 4)
- SEA: +12 if greenlit (SG 6, ID 4, VN 2)
- US: +3 (enterprise sales)
""",
    )

    w(
        "hr/talent-availability-sea.md",
        "# Talent availability — SEA\n\n- SG: high cost, low supply (3-month median time-to-hire).\n- ID: mid cost, growing supply.\n- VN: low cost, fast supply, lower English fluency.\n",
    )

    w(
        "hr/compensation-benchmarks-sea.csv",
        csv_str([
            ["role", "country", "median_total_comp_usd"],
            ["AE-Enterprise", "SG", 180000],
            ["AE-Enterprise", "ID", 95000],
            ["AE-Enterprise", "VN", 70000],
            ["SDR", "SG", 78000],
            ["SDR", "ID", 38000],
        ]),
    )

    # ---------------- term-sheet specifics (scenario 2) ----------------
    w(
        "financials/term-sheet-details.md",
        f"""# Inbound term sheet — Apr 2026

- Amount: ${n['term_sheet_musd']}M
- Pre-money: ${n['term_sheet_valuation_musd']}M (flat from last round)
- Liquidation pref: 1x non-participating
- Board: +1 from investor
- Pro-rata: yes, on next round
""",
    )

    # Build manifest
    for p in sorted(ROOT.rglob("*")):
        if p.is_file():
            rel = p.relative_to(ROOT).as_posix()
            tags = [rel.split("/")[0]]
            manifest.append({
                "path": rel,
                "title": p.stem.replace("-", " ").title(),
                "owner": tags[0],
                "date": "2026-05-01",
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
    print(f"generated {len(manifest)} files under {ROOT}")
    if os.environ.get("SEED_BLOB_UPLOAD", "true").lower() == "true":
        try:
            upload(manifest)
        except Exception as e:  # noqa: BLE001
            print(f"upload skipped: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
