import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useStore, type PrepMode, type Role } from "../store";
import { MessageBubble } from "./MessageBubble";

type Props = {
  seat: Role | null;
  agendaTopic: string | null;
  onSend: (text: string) => void;
  disabled?: boolean;
};

const MOOD_TONE: Record<string, string> = {
  cordial: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  debating: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  heated: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  converging: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  resolved: "bg-violet-500/15 text-violet-300 border-violet-500/30",
};

const MODE_LABEL: Record<PrepMode, string> = {
  coach: "Coach me",
  drill: "Drill me",
};

export function PrepThread({ seat, agendaTopic, onSend, disabled }: Props) {
  const messages = useStore((s) => s.prepMessages);
  const citations = useStore((s) => s.prepCitations);
  const mood = useStore((s) => s.prepMood);
  const speaking = useStore((s) => s.prepSpeakingAgent);
  const subMode = useStore((s) => s.prepSubMode);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length, messages[messages.length - 1]]);

  const moodCls = MOOD_TONE[mood.label] || "bg-white/10 text-white/70 border-white/20";

  function submit() {
    const trimmed = draft.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setDraft("");
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <section className="flex-1 min-w-0 flex flex-col bg-[#0a0b14] bg-board-grid">
      <header className="border-b border-white/5 px-6 py-3 flex items-center justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-white/40">@</span>
            <h2 className="font-semibold text-white truncate">
              {seat ? `Prep with AI ${seat}` : "Pick a seat to begin prep"}
            </h2>
          </div>
          {agendaTopic && (
            <div className="text-xs text-white/50 mt-1 truncate max-w-2xl">
              Agenda: {agendaTopic}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-white/40">
              Mode
            </div>
            <div className="text-xs px-2 py-0.5 rounded-full border bg-indigo-500/15 text-indigo-200 border-indigo-500/30 mt-0.5">
              {MODE_LABEL[subMode]}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-white/40">
              Tone
            </div>
            <div
              className={`text-xs px-2 py-0.5 rounded-full border mt-0.5 ${moodCls}`}
            >
              {mood.label}
            </div>
          </div>
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto py-3">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center px-6">
            <div className="hero-gradient w-full max-w-xl rounded-2xl p-[1px] shadow-2xl shadow-indigo-900/40">
              <div className="bg-[#0a0b14]/85 rounded-2xl px-8 py-10 backdrop-blur">
                <div className="w-14 h-14 mx-auto rounded-full bg-indigo-500/20 border border-indigo-400/40 flex items-center justify-center text-2xl mb-4">
                  🎯
                </div>
                <div className="text-white font-semibold text-lg">
                  {seat
                    ? agendaTopic
                      ? `Ready to prep on: ${agendaTopic}`
                      : "Pick an agenda topic on the right →"
                    : "Pick a seat on the left to begin"}
                </div>
                <div className="text-sm text-white/60 mt-2 max-w-md mx-auto">
                  Coach mode sharpens your argument · Drill mode hits you with
                  3-4 contradicting questions per turn.
                </div>
              </div>
            </div>
          </div>
        )}
        {messages.map((m, i) => {
          if (m.kind === "user") {
            return (
              <MessageBubble
                key={i}
                index={i}
                citations={[]}
                userMessage
                turn={{
                  agent: "CEO",
                  model: "",
                  text: m.text,
                  done: true,
                }}
              />
            );
          }
          return (
            <MessageBubble
              key={i}
              index={i}
              citations={citations}
              liveOverride={!m.done && speaking === m.agent}
              turn={{
                agent: m.agent,
                model: m.model,
                text: m.text,
                done: m.done,
              }}
            />
          );
        })}
      </div>

      <div className="border-t border-white/5 px-6 py-3">
        <div className="bg-black/30 border border-white/10 rounded-md px-3 py-2 flex items-end gap-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKey}
            placeholder={
              seat
                ? `Ask AI ${seat} to ${
                    subMode === "coach"
                      ? "sharpen your argument…"
                      : "drill you with 3-4 contradicting board questions…"
                  }`
                : "Pick a seat first"
            }
            rows={2}
            disabled={disabled || !seat}
            className="flex-1 bg-transparent text-sm text-white outline-none resize-none placeholder-white/40 disabled:opacity-50"
          />
          <button
            disabled={disabled || !seat || !draft.trim()}
            onClick={submit}
            className="bg-gradient-to-r from-indigo-500 to-indigo-400 hover:from-indigo-400 hover:to-cyan-400 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 text-white text-sm font-medium rounded-md px-3 py-1.5 transition shrink-0"
          >
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
