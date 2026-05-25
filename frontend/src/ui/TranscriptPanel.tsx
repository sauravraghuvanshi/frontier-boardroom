import { useEffect, useRef } from "react";
import { useStore } from "../store";

const ROLE_COLOR: Record<string, string> = {
  CEO: "text-sky-300",
  CFO: "text-pink-300",
  CMO: "text-emerald-300",
  CTO: "text-fuchsia-300",
  Legal: "text-amber-300",
};

export function TranscriptPanel() {
  const turns = useStore((s) => s.turns);
  const speakingAgent = useStore((s) => s.speakingAgent);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [turns.length, turns[turns.length - 1]?.text]);

  return (
    <div className="border-t border-white/10 p-3 flex-1 min-h-0 flex flex-col">
      <div className="text-xs uppercase tracking-wider text-white/60 mb-2">
        Transcript
      </div>
      <div ref={ref} className="flex-1 overflow-y-auto space-y-3 pr-1">
        {turns.length === 0 && (
          <div className="text-white/40 text-sm">
            No turns yet. Pick a scenario to start the debate.
          </div>
        )}
        {turns.map((t, i) => {
          const isLive = !t.done && speakingAgent === t.agent;
          const color = ROLE_COLOR[t.agent] ?? "text-white";
          const providerChip = t.model.startsWith("databricks:")
            ? "bg-emerald-500/20 text-emerald-200"
            : "bg-sky-500/20 text-sky-200";
          return (
            <div key={i} className="bg-black/30 rounded p-2">
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-semibold ${color}`}>
                  {t.agent}
                  {isLive && <span className="ml-1 animate-pulse">●</span>}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${providerChip}`}>
                  {t.model}
                </span>
              </div>
              <div className="text-sm text-white/90 whitespace-pre-wrap">
                {t.text || "…"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
