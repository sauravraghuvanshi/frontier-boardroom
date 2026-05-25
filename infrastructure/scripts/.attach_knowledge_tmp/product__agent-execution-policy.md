# Agent execution policy — what each agent may and may not do

This file is referenced by `ai-safety-policy.md` Principle 2 and is enforced in code (`backend/app/agents/execution_policy.py`).

## Code Review Agent
- ✅ May post comments on PRs (suggestions, questions).
- ✅ May label PRs (`/needs-tests`, `/security-review-requested`).
- ❌ May not merge PRs.
- ❌ May not force-push to any branch.
- ❌ May not modify CODEOWNERS or branch protection.
- ❌ May not approve PRs (we explicitly disallow "AI approvers" — humans only).

## PR Triage Agent
- ✅ May label, assign reviewers, post summary comment.
- ❌ May not close PRs without a human confirming.
- ❌ May not delete branches.

## Test-Gen Agent
- ✅ May add files in test directories.
- ❌ May not modify production code paths.
- ❌ May not modify CI configuration.

## On-Call Agent
- ✅ May post incident triage to incident chat channel.
- ✅ May query observability platform (Datadog, Honeycomb) read-only.
- ❌ May not page humans (only PagerDuty/Opsgenie page humans).
- ❌ May not auto-resolve incidents.
- ❌ May not restart services, restart pods, scale resources, fail over.

## Infra-Ops Agent
- ✅ May post comments on Terraform/Bicep PRs.
- ✅ May simulate cost impact (read-only).
- ❌ May not apply Terraform.
- ❌ May not modify IAM, KMS, or network policies in any form.
- ❌ May not run any infrastructure mutation command.

## Audit
All agent actions logged immutably to per-customer audit log (one of the P0 tech-debt items being hardened — see `tech-debt-register.md` item #2). Customers receive monthly export of all agent actions in their tenant.
