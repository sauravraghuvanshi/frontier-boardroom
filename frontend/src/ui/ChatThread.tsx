import { useEffect, useRef } from "react";
import { useStore } from "../store";
import { MessageBubble } from "./MessageBubble";

type Props = {
  topic: string | null;
  questionAsked: string | null;
};

const MOOD_TONE: Record<string, string> = {
  cordial: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  debating: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  heated: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  converging: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  resolved: "bg-violet-500/15 text-violet-300 border-violet-500/30",
};

export function ChatThread({ topic, questionAsked }: Props) {
  const turns = useStore((s) => s.turns);
  const citations = useStore((s) => s.citations);
  const mood = useStore((s) => s.mood);
  const decision = useStore((s) => s.decision);
  const vote = useStore((s) => s.vote);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [turns.length, turns[turns.length - 1]?.text, decision]);

  const moodCls = MOOD_TONE[mood.label] || "bg-white/10 text-white/70 border-white/20";
  const moodPulse = mood.label === "heated" || mood.label === "debating";

  return (
    <section className="flex-1 min-w-0 flex flex-col bg-[#0a0b14] bg-board-grid">
      <header className="border-b border-white/5 px-6 py-3 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-white/40">#</span>
            <h2 className="font-semibold text-white">
              {topic || "Pick a channel to begin"}
            </h2>
          </div>
          {questionAsked && (
            <div className="text-xs text-white/50 mt-1 max-w-2xl">
              {questionAsked}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-white/40">
              Room mood
            </div>
            <div className={`text-xs px-2 py-0.5 rounded-full border mt-0.5 ${moodCls} ${moodPulse ? "animate-pulse" : ""}`}>
              {mood.label}
            </div>
          </div>
          <div className="w-24 h-1.5 bg-white/10 rounded overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-rose-400 via-amber-300 to-emerald-300 transition-all"
              style={{ width: `${mood.value * 100}%` }}
            />
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-3">
        {turns.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <div className="hero-gradient w-full max-w-xl rounded-2xl p-[1px] shadow-2xl shadow-indigo-900/40">
              <div className="bg-[#0a0b14]/85 rounded-2xl px-8 py-10 backdrop-blur">
                <div className="w-14 h-14 mx-auto rounded-full bg-indigo-500/20 border border-indigo-400/40 flex items-center justify-center text-2xl mb-4">
                  💼
                </div>
                <div className="text-white font-semibold text-lg">
                  {topic ? "Convening the boardroom…" : "Pick a channel to start the debate"}
                </div>
                <div className="text-sm text-white/60 mt-2 max-w-md mx-auto">
                  {topic
                    ? "Agents are reading the briefing. The CEO will open shortly."
                    : "Each channel routes the C-suite to a real strategic question grounded in the company's seeded briefing documents."}
                </div>
              </div>
            </div>
          </div>
        )}
        {turns.map((t, i) => (
          <MessageBubble key={i} turn={t} index={i} citations={citations} />
        ))}
        {decision && (
          <div className="px-6 py-4">
            <div className="bg-gradient-to-br from-amber-400/15 to-amber-600/10 border border-amber-400/40 rounded-lg p-4 animate-pulse-glow">
              <div className="text-[10px] uppercase tracking-widest text-amber-300 font-semibold">
                Boardroom Decision
              </div>
              <div className="text-lg font-semibold text-white mt-1">
                {decision}
              </div>
              {vote && (
                <div className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
                  {Object.entries(vote).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-white/5 py-1">
                      <span className="text-white/70">{k}</span>
                      <span className="text-amber-200 font-medium">{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-white/5 px-6 py-3">
        <div className="bg-black/30 border border-white/10 rounded-md px-3 py-2 text-sm text-white/40">
          Live agent debate — audience can submit questions via the QR code on
          the right.
        </div>
      </div>
    </section>
  );
}
