# Contoso AI — localization readiness

Customer-facing surfaces: admin console, agent commit messages, agent PR descriptions, agent slack/teams notifications, sales website.

| Surface | English | Hindi | Bahasa Indonesia | Bahasa Melayu | Thai | Vietnamese | Tagalog | Arabic |
|---------|---------|-------|------------------|----------------|------|------------|---------|--------|
| Admin console | ✅ | ✅ | ⏳ (Q2 2026) | ⏳ | ⏳ (Q2 2026) | ⏳ (Q3 2026) | ❌ | ❌ |
| Agent commit messages | ✅ | ✅ | ⏳ | ⏳ | ⏳ | ❌ | ❌ | ❌ |
| Agent PR descriptions | ✅ | ✅ | ⏳ | ⏳ | ⏳ | ❌ | ❌ | ❌ |
| Slack/Teams notifications | ✅ | ✅ | ⏳ | ⏳ | ⏳ | ❌ | ❌ | ❌ |
| Sales website | ✅ | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Documentation | ✅ | ⏳ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Customer demand signal (from `customer-interviews-sea.md`)
- 14/14 SEA interviewees prefer **English admin UI** even in non-English-default markets.
- However, agent-generated artifacts (commits, PR descriptions) **should** support local language so end-users see native communication.

## Recommendation
- **Prioritize**: agent output localization (commit/PR/notification) for Bahasa Indonesia + Thai by end Q2 2026.
- **De-prioritize**: admin console localization (low ROI given English preference).
- **De-prioritize**: documentation localization (English docs are sufficient per interview signal).

## Cost
- ~2 engineer-weeks per language for agent-output localization (i18n keys + LLM prompt-side language directive).
- ~5 engineer-weeks per language for admin console (UI translation + RTL where needed).
