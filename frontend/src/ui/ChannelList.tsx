import { useState } from "react";
import { useStore } from "../store";
import { Logo } from "../branding/Logo";
import { COMPANY } from "../branding/company";

export const SCENARIOS = [
  {
    id: "sea-expansion",
    label: "SEA Expansion",
    topic: "Q1 2026 expansion: SEA vs double-down India",
    question:
      "Should we expand to Southeast Asia in Q1 2026 or double down in India given our $25.2M cash and 18-month runway?",
  },
  {
    id: "term-sheet",
    label: "$30M Term Sheet",
    topic: "Series B — accept 2x participating pref?",
    question:
      "Should we accept the $30M Series B term sheet with a 2x participating liquidation preference?",
  },
  {
    id: "competitor",
    label: "Competitor Launch",
    topic: "Competitor free tier — quarterly response",
    question:
      "A well-funded competitor just launched a free tier in SEA — how do we respond this quarter given our win/loss trends?",
  },
  {
    id: "ai-safety",
    label: "AI Safety Incident",
    topic: "Harmful output — 72h response plan",
    question:
      "A customer reports our AI feature produced harmful output. What is our 72-hour response under GDPR + PDPA obligations?",
  },
  {
    id: "runway-cut",
    label: "Runway Trigger",
    topic: "Cash <$12M — freeze SEA or cut India?",
    question:
      "If cash drops below the $12M trigger in our Q1 forecast, do we freeze SEA hiring or cut India headcount?",
  },
  {
    id: "pricing-cut",
    label: "Pricing Response",
    topic: "Match -30% competitor pricing?",
    question:
      "Given the latest pricing comparison and our unit economics by region, do we match the competitor's -30% cut or hold premium positioning?",
  },
  {
    id: "hiring-mix",
    label: "2026 Hiring Plan",
    topic: "Approve 24 India + 12 SEA + 3 US?",
    question:
      "Should we approve the 2026 hiring plan of 24 India + 12 SEA + 3 US given SEA compensation benchmarks and talent availability?",
  },
  {
    id: "data-residency",
    label: "Data Residency",
    topic: "Per-country residency — now or later?",
    question:
      "Do we build per-country data residency now or wait until the first enterprise SEA deal, given current employment-law exposure?",
  },
  {
    id: "partner-channel",
    label: "SEA GTM",
    topic: "Direct sales vs partner-led in SEA",
    question:
      "For our SEA go-to-market, should we lead with direct sales or lean on the regional partner ecosystem?",
  },
  {
    id: "tech-debt",
    label: "Tech Debt Pause",
    topic: "Pause features 1Q to pay down debt?",
    question:
      "Should we pause feature work for one quarter to pay down the tech-debt register, given 2026 engineering capacity and infra cost trends?",
  },
];

type Props = {
  activeId: string | null;
  onPick: (q: string, id?: string) => void;
};

export function ChannelList({ activeId, onPick }: Props) {
  const [custom, setCustom] = useState("");
  const connected = useStore((s) => s.connected);
  const speakingAgent = useStore((s) => s.speakingAgent);

  return (
    <aside className="w-[260px] shrink-0 bg-[#11131f] border-r border-white/5 flex flex-col">
      <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2.5">
        <Logo size={32} />
        <div className="min-w-0">
          <div className="font-semibold text-white text-sm leading-tight truncate">
            {COMPANY.productName}
          </div>
          <div className="text-[10px] uppercase tracking-widest text-white/40">
            Virtual C-Suite
          </div>
        </div>
      </div>

      <div className="px-3 pt-3 pb-1 text-[11px] uppercase tracking-wider text-white/40">
        Channels
      </div>
      <ul className="px-2 space-y-0.5">
        {SCENARIOS.map((s) => {
          const active = activeId === s.id;
          return (
            <li key={s.id}>
              <button
                onClick={() => onPick(s.question, s.id)}
                className={`channel-row w-full text-left rounded-md pl-3.5 pr-2.5 py-1.5 text-sm flex items-center gap-2 transition ${
                  active
                    ? "is-active bg-[#4338ca]/40 text-white"
                    : "text-white/80 hover:bg-white/5"
                }`}
              >
                <span className="text-white/40">#</span>
                <span className="flex-1 truncate">{s.label}</span>
                {active && speakingAgent && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                )}
              </button>
            </li>
          );
        })}
      </ul>

      <div className="mt-auto px-3 py-3 border-t border-white/5 space-y-2">
        <div className="text-[11px] uppercase tracking-wider text-white/40">
          New topic
        </div>
        <textarea
          value={custom}
          onChange={(e) => setCustom(e.target.value)}
          placeholder="Ask the board a question…"
          rows={2}
          className="w-full bg-black/30 border border-white/10 rounded-md px-2 py-1.5 text-sm resize-none outline-none focus:border-[#7b83eb]"
        />
        <button
          disabled={!custom.trim()}
          onClick={() => {
            if (custom.trim()) {
              onPick(custom.trim());
              setCustom("");
            }
          }}
          className="w-full bg-gradient-to-r from-indigo-500 to-indigo-400 hover:from-indigo-400 hover:to-cyan-400 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 text-white text-sm font-medium rounded-md py-1.5 transition"
        >
          Start debate
        </button>
        <div className="flex items-center gap-2 text-[11px] text-white/40 pt-1">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connected ? "bg-emerald-400" : "bg-white/30"
            }`}
          />
          {connected ? "Connected" : "Idle"}
        </div>
      </div>
    </aside>
  );
}
