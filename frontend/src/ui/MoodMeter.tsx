import { useStore } from "../store";

export function MoodMeter() {
  const { value, label } = useStore((s) => s.mood);
  return (
    <div className="border-t border-white/10 p-3">
      <div className="flex justify-between text-xs uppercase tracking-wider text-white/60">
        <span>Mood</span>
        <span>{label}</span>
      </div>
      <div className="h-2 bg-white/10 rounded mt-2 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-rose-400 via-amber-300 to-emerald-300"
          style={{ width: `${value * 100}%` }}
        />
      </div>
    </div>
  );
}
