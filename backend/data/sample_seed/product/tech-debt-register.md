# Contoso AI — tech debt register (May 2026)

## Severity distribution
- **P0** (critical, must clear before next major release): **7 items**.
- **P1** (significant, planned within 2 quarters): 14 items.
- **P2** (deferred, opportunistic): 28 items.

## P0 items (7)
1. **Multi-tenant row-level data residency enforcement** — today residency is enforced at cluster level. Some on-call agent payloads (rare) leak cross-region in failover. **Effort**: ~6 engineer-weeks. **Blocks**: ID PoP launch, SG financial-services close.
2. **Agent action audit log immutability** — write-once log requested by 3 enterprise customers and required for SOC 2 Type II CC-7 controls. **Effort**: ~3 engineer-weeks.
3. **Model router fallback path** — single point of failure if Foundry has a regional outage; need fallback to Databricks-served models. Lead investor's diligence flagged this. **Effort**: ~4 engineer-weeks.
4. **Customer data isolation in fine-tuned models** — currently shared 13B Code Review model; need per-tenant adapter or per-tenant LoRA. **Effort**: ~8 engineer-weeks.
5. **Localization layer** — incomplete for Vietnamese, partially complete for Indonesian/Thai. **Effort**: ~3 engineer-weeks per language.
6. **On-Call Agent webhook signing & replay protection** — current HMAC implementation accepts replay within 5min window; security audit flagged. **Effort**: ~1 engineer-week.
7. **GPU bin-packing for inference** — current scheduler wastes ~18% of GPU capacity due to model-warmup overhead. **Effort**: ~5 engineer-weeks.

## P0 items that must clear before SEA multi-region rollout
Items **#1, #2, #3, #4, #5** — five of the seven. Total effort: ~24 engineer-weeks. At current capacity (9 engineers allocated to SEA sprint) = ~3 calendar weeks of pure-debt sprint, plus integration testing.

## Cost of *not* fixing
- Item #1: blocks all ID + VN regulated industry deals (~$1.8M ARR pipeline).
- Item #3: lead investor has flagged as condition of Series B close.
- Item #6: subject to a fine of up to $200K per Indonesia DPA template clause.
