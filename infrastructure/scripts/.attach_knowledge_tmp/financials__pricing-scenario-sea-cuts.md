# Pricing Scenario — Unit Economics Under SEA List-Price Cuts

Sensitivity of LTV, LTV/CAC, and payback to a list-price reduction applied **only to SEA regions** (SG, ID, TH, VN). India, US, ME pricing held constant. Modeled by Finance 2026-05-22.

## Assumptions
- ARPU scales linearly with list price (no offsetting volume lift modeled — Marketing's elasticity work is still in flight).
- Gross margin held at current per-region levels; cost base does not flex within the modeling horizon.
- Churn unchanged at current cohort levels (no churn-rescue benefit assumed from lower price).
- NRR held constant; expansion ARR per logo unchanged.
- LTV recomputed as `gross_margin × ARPU / churn`; CAC held flat at current marketing efficiency.

## SEA-SG (baseline LTV $5,200, CAC $736, LTV/CAC 7.1, payback 14 mo)

| price_cut | ltv_usd | ltv_cac | payback_months |
|---|---|---|---|
| 0% (current) | 5200 | 7.1 | 14 |
| -10% | 4680 | 6.4 | 16 |
| -20% | 4160 | 5.7 | 17 |
| -30% | 3640 | 4.9 | 19 |
| -40% | 3120 | 4.2 | 22 |

## SEA-ID (baseline LTV $3,900, CAC $690, LTV/CAC 5.7, payback 17 mo)

| price_cut | ltv_usd | ltv_cac | payback_months |
|---|---|---|---|
| 0% (current) | 3900 | 5.7 | 17 |
| -10% | 3510 | 5.1 | 19 |
| -20% | 3120 | 4.5 | 21 |
| -30% | 2730 | 4.0 | 24 |
| -40% | 2340 | 3.4 | 28 |

## SEA-TH (baseline LTV $4,200, CAC $720, LTV/CAC 5.8, payback 16 mo)

| price_cut | ltv_usd | ltv_cac | payback_months |
|---|---|---|---|
| 0% (current) | 4200 | 5.8 | 16 |
| -10% | 3780 | 5.3 | 18 |
| -20% | 3360 | 4.7 | 20 |
| -30% | 2940 | 4.1 | 23 |
| -40% | 2520 | 3.5 | 27 |

## SEA-VN (baseline LTV $3,700, CAC $610, LTV/CAC 6.1, payback 15 mo)

| price_cut | ltv_usd | ltv_cac | payback_months |
|---|---|---|---|
| 0% (current) | 3700 | 6.1 | 15 |
| -10% | 3330 | 5.5 | 17 |
| -20% | 2960 | 4.9 | 19 |
| -30% | 2590 | 4.2 | 22 |
| -40% | 2220 | 3.6 | 26 |

## Board-defensibility thresholds (Finance position)

- **LTV/CAC ≥ 5.0** — defensible
- **LTV/CAC 4.0–4.9** — yellow zone, requires offset (volume lift, churn improvement)
- **LTV/CAC < 4.0** — Finance will not defend to the board

A blanket -30% list-price cut across all SEA regions pushes SEA-ID and SEA-TH below the 4.0 threshold and SEA-SG into the yellow zone. Payback breaches the 18-month covenant on SEA-ID, SEA-TH, and SEA-VN.

## Recommended bound

Cap any SEA promo at **-15% off list, time-boxed to a single quarter**, applied at the deal desk rather than re-platforming list pricing. This keeps LTV/CAC ≥ 5.0 in all four SEA regions and payback ≤ 18 months.
