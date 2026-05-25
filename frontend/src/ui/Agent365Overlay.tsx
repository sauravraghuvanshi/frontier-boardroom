import { useStore } from "../store";

export function Agent365Overlay() {
  const turns = useStore((s) => s.turns);
  const tokens = turns.reduce((acc, t) => acc + t.text.split(" ").length, 0);
  return (
    <div className="border-t border-white/10 p-3 text-xs text-white/60">
      <div className="uppercase tracking-wider mb-1">Agent 365</div>
      <div>turns: {turns.length}</div>
      <div>~tokens spoken: {tokens}</div>
    </div>
  );
}
