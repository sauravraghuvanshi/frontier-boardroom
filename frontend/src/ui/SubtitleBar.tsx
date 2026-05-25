import { useStore } from "../store";

export function SubtitleBar() {
  const turns = useStore((s) => s.turns);
  const last = turns[turns.length - 1];
  if (!last) return null;
  return (
    <div className="absolute bottom-6 left-6 right-6 max-w-3xl mx-auto bg-black/70 rounded-xl p-4 backdrop-blur">
      <div className="text-xs uppercase tracking-wider text-boardroom-accent mb-1">
        {last.agent} <span className="text-white/40">· {last.model}</span>
      </div>
      <div className="text-lg leading-snug" aria-live="polite">
        {last.text || "…"}
      </div>
    </div>
  );
}
