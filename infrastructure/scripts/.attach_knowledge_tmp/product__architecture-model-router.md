# Contoso AI — model router architecture

The model router is Contoso AI's most strategic engineering asset: a single Python service (`model_router.py`) that dispatches every agent inference call to the right foundation model on the right cloud.

## Why it exists
- **Foundation-model neutrality** is the #3 buying criterion in `customer-interviews-sea.md` (8/14 buyers explicitly raised it).
- **Cost optimization**: 22% inference unit-cost reduction in Q4-2025 attributable to router-driven model arbitrage.
- **Compliance**: India banking customers need India-resident inference; the router enforces residency by selecting the in-region provider.

## Providers wired today (May 2026)
| Provider | Cloud | Models | Primary use case |
|----------|-------|--------|-------------------|
| Microsoft Foundry | Azure | OpenAI GPT-5, xAI Grok-4, Meta Llama 4 (70B + 405B), Mistral Large | Code Review (GPT-5), planning/reasoning (Grok-4), low-cost summarization (Llama 4 70B) |
| Azure Databricks Mosaic AI | Azure (Databricks Premium) | Anthropic Claude Sonnet 4.5, Claude Opus 4.x | High-fidelity code review (Sonnet), legal/policy review (Opus) |
| Contoso Fine-tuned 13B | On-prem Azure GPU pool, India | Code Review specialist (fine-tuned on Apache 2.0 + MIT corpora) | Cost-sensitive Code Review at scale |

## Routing dimensions
- **Region** (residency): customer org's residency requirement narrows provider list first.
- **Task class**: code-review, planning, summarization, policy-check, etc.
- **Cost tier**: starter / pro / enterprise — different models per tier.
- **Latency budget**: hard SLA per customer.
- **Fallback**: if primary provider unhealthy, automatic switch (currently P1 tech debt — see `tech-debt-register.md` item #3).

## Strict architectural rule
Anthropic Claude (Sonnet 4.5, Opus) runs **on Azure Databricks Mosaic AI Model Serving** — never on Foundry. OpenAI / xAI / Meta / Mistral run on **Foundry** as 1st party. The router enforces this — bypassing the router is a CI-blocking lint rule.

## Performance targets (P95 first-token latency)
- Code Review Agent: ≤ 800ms.
- On-Call Agent: ≤ 1.2s.
- PR Triage Agent: ≤ 2.0s.
- Test-Gen Agent: ≤ 4.0s.

## Recent observed regressions
- DeepSeek-V3.2 evaluated for CTO agent in demo product — leaked chain-of-thought through `output_text` channel. Switched off DeepSeek to `foundry:gpt-5` (recorded as L-13 in `lessons.md`).
