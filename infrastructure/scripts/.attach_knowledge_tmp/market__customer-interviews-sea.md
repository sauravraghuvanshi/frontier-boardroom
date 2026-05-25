# SEA customer interviews — n=14 engineering leaders

Conducted Jan–Mar 2026 by Priya Menon (CMO) and Ravi Kapoor (VP Sales).
Sample: 14 VPs/Directors of Engineering in SG, ID, TH, VN at companies 50–800 devs.

## Buying criteria (ranked)
1. **Data residency** — 11/14 require local data residency *at the country level*, not just regional. Cross-border-with-consent considered insufficient by regulated buyers (banking, fintech, healthcare).
2. **SLA-backed local PoPs** — 9/14 willing to pay 15% premium for SLA-backed in-country inference. Latency expectation: P95 ≤ 800ms for Code Review Agent.
3. **Foundation-model neutrality** — 8/14 explicitly stated preference for a vendor that can swap models (OpenAI/Anthropic/Llama/open-source) without changing contracts.
4. **Per-seat predictability** — 7/14 prefer per-seat to per-action pricing for budgeting.
5. **Hindi-language UI** *not preferred* — 14/14 prefer English admin UI even in India-adjacent SEA markets.

## Switch drivers (4 interviewees actively using a competitor today)
- **Pricing flexibility** — willingness to negotiate per-seat tier, multi-year discount.
- **Better English support docs** — competitor docs poor or translated unevenly.
- **Test-Gen agent quality** — Contoso's test-gen demo on customer code outperformed competitor by 23% (measured by reviewer accept rate).

## Pain points with current tools
- "Acme Devbots PR review takes 12 seconds — engineers ignore it." — VP Eng, SG fintech
- "BetaCode test generation generates tests for code paths we've already deprecated." — Director, ID e-commerce
- "We need an on-call agent that doesn't page humans for predictable transient errors. Today we get woken at 3am for Kafka consumer-lag false alarms." — SRE Lead, TH bank

## Won deals from interview pool (3 of 14)
- SG fintech (110 devs) — closed at $89/seat/mo (Pro tier), 12-month commit. $117K ARR.
- ID e-commerce (220 devs) — pilot signed at 40 seats, full expansion conditional on Jakarta PoP being live by Sep 2026.
- TH bank (180 devs) — Code Review Agent only, $79/seat × 180 = $14K/mo. $170K ARR.

## Lost deals from interview pool (4 of 14, all primary reason: no local entity / residency)
- SG private bank (300 devs)
- ID megabank (400 devs)
- VN payments fintech (90 devs)
- SG telco (150 devs)
