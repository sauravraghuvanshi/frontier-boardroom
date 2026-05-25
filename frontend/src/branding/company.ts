// Single source of truth for the fictional company the boardroom debates.
// Numbers anchored to backend/data/sample_seed/ so the About page stays
// consistent with what agents cite during debates.

export const COMPANY = {
  name: "Contoso AI",
  productName: "Contoso AI Boardroom",
  productByline: "A Frontier Firm",
  tagline: "World-class AI agents that automate the daily work of engineers.",
  blurb:
    "Contoso AI builds world-class AI agents that automate the daily tasks of engineers — built in India, for the world.",
  stage: "Series B (in flight)",
  hq: "Delhi, India",
  founded: "2021",
  website: "contoso.ai",

  financials: {
    cash: "$25.2M",
    cashAsOf: "EOM Apr 2026",
    burnPerMonth: "$1.4M",
    runwayMonths: 18,
    runwayWithSEA: "~14 months if SEA greenlit",
    termSheet: "$30M @ 2x participating pref (under review)",
    arrIndia: "$18.4M ARR (FY25)",
  },

  people: {
    headcountToday: 110,
    breakdown: [
      { region: "India (Delhi HQ)", count: 92 },
      { region: "United States", count: 18 },
      { region: "Southeast Asia (planned)", count: 0 },
    ],
    hiring2026: {
      india: 24,
      sea: 12,
      us: 3,
      note: "SEA hires conditional on Q1 pipeline trigger (≥30% MoM growth).",
    },
  },

  markets: [
    {
      name: "India (core)",
      detail: "84% of revenue. CAC payback ~9 months. Land-and-expand motion.",
    },
    {
      name: "Southeast Asia (expansion target)",
      detail: "SG → ID → VN sequence. TAM $4.1B by 2028 (Gartner).",
    },
    {
      name: "United States (anchor enterprise)",
      detail: "3 lighthouse accounts. Sales-led, partner-amplified.",
    },
  ],

  team: [
    { role: "CEO" as const, focus: "Vision, fundraising, board" },
    { role: "CFO" as const, focus: "Capital allocation, runway discipline" },
    { role: "CMO" as const, focus: "Brand, demand gen, SEA GTM" },
    { role: "CTO" as const, focus: "Platform, AI infra, technical debt" },
    { role: "Legal" as const, focus: "Compliance, IP, data residency" },
  ],

  stack: [
    "Microsoft Foundry — OpenAI GPT-5, xAI Grok, Meta Llama",
    "Azure Databricks Mosaic AI — Anthropic Claude Sonnet 4.5 + Opus",
    "Azure Speech (neural voices) · Azure App Insights · Key Vault",
    "FastAPI · Microsoft Agent Framework · React + Vite",
  ],
} as const;

export type Company = typeof COMPANY;
