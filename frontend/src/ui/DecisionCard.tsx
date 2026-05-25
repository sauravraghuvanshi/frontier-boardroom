import { useStore } from "../store";

export function DecisionCard() {
  const decision = useStore((s) => s.decision);
  const vote = useStore((s) => s.vote);
  if (!decision) return null;
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-black/70">
      <div className="bg-boardroom-panel border border-white/10 rounded-2xl p-6 max-w-lg">
        <div className="text-xs uppercase tracking-widest text-boardroom-accent">Decision</div>
        <div className="text-2xl font-semibold mt-2">{decision}</div>
        {vote && (
          <ul className="mt-4 text-sm space-y-1">
            {Object.entries(vote).map(([k, v]) => (
              <li key={k} className="flex justify-between">
                <span>{k}</span>
                <span className="text-emerald-300">{v}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
