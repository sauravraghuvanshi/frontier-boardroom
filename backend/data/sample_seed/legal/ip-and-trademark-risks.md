# IP & trademark — Contoso AI

## Wordmark / brand
- "**Contoso AI**" — registered in India (TM journal #2024-1812, granted Aug 2024), US (USPTO Reg #7,488,902), and Singapore (IPOS #40202412345).
- Unregistered in MY, VN, ID, TH, PH, KR, JP.
- **Risk**: cybersquatting and trademark squatting in unregistered jurisdictions. One known squatter in VN registered `contoso-ai.vn` and `contoso-ai.com.vn` in 2025-Q4 — handled via UDRP, recovered Apr 2026.
- **Recommendation**: file Madrid Protocol designating all ASEAN + JP + KR + AU before public SEA announce. Cost: ~$15K legal, 9-month timeline.

## Code / model IP
- All inference performed on customer data is **not** used to train base models (see `ai-safety-policy.md` and Section 3 of MSA).
- Contoso AI's fine-tuned 13B Code Review model trained on **permissively-licensed open-source repositories only** (Apache 2.0, MIT, BSD). Audit logs of training data sources retained.
- **Risk**: ongoing litigation in US over training data provenance for LLMs (Doe v. GitHub Copilot etc.) — none directly against Contoso AI, but watch list. Mitigation: strict licensing audit on training corpus.

## Patents
- Two pending patent applications (US):
  - US Application 18/123,456 — "Multi-model routing for code-modification agent calls with safety-policy enforcement"
  - US Application 18/124,789 — "Speculative execution of code-review agents with rollback"
- Both pending examination. Not yet granted.

## Customer IP indemnification
- MSA includes a **$5M cap IP indemnity** for Contoso-generated code suggestions. Above $5M handled via the cyber + tech-E&O policy ($25M total).
- No claim filed in 2025. One inquiry from a Mumbai bank customer about a code suggestion that resembled an Apache 2.0 fragment — resolved with attribution.
