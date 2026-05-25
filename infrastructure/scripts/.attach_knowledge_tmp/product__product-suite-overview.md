# Contoso AI — product suite overview

Contoso AI builds **world-class AI agents that automate the daily work of engineers** — built in India, for the world. Five production agents and one in beta.

## 1. Code Review Agent (GA, anchor product — 41% of ARR)
- Reviews pull requests automatically: bugs, security, style, dependency drift.
- Median review latency: **2.8 seconds** (P95: 4.6s) — fastest in the segment per internal benchmarks.
- Languages: Python, TypeScript/JavaScript, Go, Java, Kotlin, Rust, C#, PHP. Beta: Swift, Ruby.
- Accept rate (median across enterprise customers): **64%** of reviewer suggestions adopted.
- Pricing: included in all paid tiers.

## 2. PR Triage Agent (GA — bundled with Code Review, ~22% of ARR with Test-Gen)
- Labels, assigns, summarizes incoming PRs.
- Drafts a 200-word summary attached as the first PR comment.
- Auto-requests review from the appropriate CODEOWNERS based on touched paths + historical reviewers.
- Per-customer setup time: ~12 minutes.

## 3. Test-Gen Agent (GA — bundled with PR Triage)
- Generates unit + integration tests for new code in PRs.
- Reviewer accept rate: **51%** of generated tests merged without modification.
- Caveat: known weakness in distributed-systems integration tests (eg Kafka, Spanner) — flagged in roadmap.

## 4. On-Call Agent (GA — 26% of ARR, fastest-growing product line)
- Companion to PagerDuty / Opsgenie / VictorOps.
- Drafts the first 2 minutes of incident triage: runbook lookup, log query templates, suggested next steps.
- Reduces median MTTR by **31%** (measured across 14 enterprise customers).
- Refuses to auto-execute remediation (human-in-loop policy — see `ai-safety-policy.md`).

## 5. Infra-Ops Agent (Paid beta — 7% of ARR; promotion to GA targeted Q3 2026)
- Reviews Terraform/Bicep PRs for cost regressions, security misconfigurations, drift from established standards.
- Most-used feature: "predict monthly cost change of this Terraform diff" (latency <3s).
- Caveat: no AWS support yet — Azure + GCP only.

## 6. Doc-Gen Agent (Experimental — not commercially available)
- Generates and maintains technical docs from code.
- Currently used internally; no external customers.

## Architecture
All agents share a common backbone: the model router (see `architecture-model-router.md`), per-tenant policy engine, audit log, and a single multi-tenant code-context vector store. New agent products take ~3.4 weeks from idea to prod (per `engineering-capacity-2026.md`).

## What Contoso AI is *not*
- Not an IDE (no plugin that replaces VS Code/Cursor).
- Not a CI/CD tool (we plug into GitHub Actions, Jenkins, CircleCI).
- Not a code-completion product (compete on review + ops, not on inline completion).
