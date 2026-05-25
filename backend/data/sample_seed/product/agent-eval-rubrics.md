# Contoso AI — agent evaluation rubrics

How we measure agent quality before promoting any change to production.

## Code Review Agent
- **Eval set**: SWE-Bench-Lite-2026 (publicly comparable) + RealPRSuite (1,840 real PRs, internal).
- **Metrics**:
  - Pass rate (test patches that compile and pass test suite).
  - Reviewer accept rate (in a held-out user study, what % of suggestions get adopted unmodified).
  - False-positive rate (suggestions reviewers explicitly mark as noise).
  - First-token latency P95.
- **Promotion gate**: ≥45% SWE-Bench-Lite, ≥60% RealPRSuite accept, ≤10% false-positive, P95 latency ≤800ms India / ≤1.2s cross-border.

## PR Triage Agent
- **Eval**: 12,000-PR backtest across 14 customer repos (with permission).
- **Metrics**:
  - Reviewer-assignment correctness (did the agent pick the right reviewer per CODEOWNERS + historic patterns).
  - Summary helpfulness (Likert 1-5, scored by 3 human reviewers).
- **Promotion gate**: ≥85% reviewer-assignment correctness, ≥3.8 helpfulness.

## Test-Gen Agent
- **Eval**: TestGenBench-2026 (internal) — pairs of (code change, ideal test).
- **Metrics**:
  - Merge-without-modification rate.
  - Mutation-testing coverage delta (does the generated test detect injected bugs).
- **Promotion gate**: ≥45% merge-unmodified, ≥0.18 mutation-score delta.

## On-Call Agent
- **Eval**: IncidentBench-2026 — 312 real Sev1/Sev2 incidents (anonymized).
- **Metrics**:
  - First-correct-runbook identification rate.
  - MTTR reduction in side-by-side A/B with engineers using agent vs not.
- **Promotion gate**: ≥65% runbook accuracy, ≥25% MTTR reduction.

## Infra-Ops Agent (paid beta, no promotion gates yet — collecting data for GA criteria)

## Cadence
- Full eval suite run weekly on every model + agent + prompt pair currently in production.
- Pre-prod eval gates run on every PR that modifies an agent or model router.
- Eval infrastructure runs on Azure Databricks Mosaic AI (`Llama-4-405B` as judge for subjective scoring, with human spot-check on 5% of judgments).
