import { useState } from "react";

const SCENARIOS = [
  {
    id: "sea-expansion",
    label: "SEA Expansion",
    question: "Should we expand to Southeast Asia in Q1 2026 or double down in India?",
  },
  {
    id: "term-sheet",
    label: "$30M Term Sheet",
    question: "Should we accept the $30M Series B term sheet with a 2x participating liquidation preference?",
  },
  {
    id: "competitor",
    label: "Competitor Launch",
    question: "A well-funded competitor just launched a free tier — how do we respond this quarter?",
  },
  {
    id: "ai-safety",
    label: "AI Safety Incident",
    question: "A customer reports our AI feature produced harmful output. What is our 72-hour response?",
  },
];

export function ScenarioPicker({ onStart }: { onStart: (q: string, id?: string) => void }) {
  const [q, setQ] = useState("");
  return (
    <div className="p-3 border-b border-white/10 space-y-2">
      <div className="text-xs uppercase tracking-wider text-white/60">Scenario</div>
      <div className="grid grid-cols-2 gap-2">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            className="bg-black/30 hover:bg-boardroom-accent/30 rounded p-2 text-sm text-left"
            onClick={() => onStart(s.question, s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div className="flex gap-2 mt-2">
        <input
          className="flex-1 bg-black/40 rounded px-2 py-1 text-sm"
          placeholder="Custom question…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          className="bg-boardroom-accent text-black rounded px-3 py-1 text-sm font-semibold"
          onClick={() => q && onStart(q)}
        >
          Start
        </button>
      </div>
    </div>
  );
}
