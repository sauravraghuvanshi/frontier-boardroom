import { useStore } from "../store";

export function CitationPanel() {
  const citations = useStore((s) => s.citations);
  const seen = new Set<string>();
  const unique = citations.filter((c) => {
    const key = `${c.agent}|${c.source_uri}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  return (
    <div className="border-t border-white/10 p-3 overflow-y-auto max-h-64">
      <div className="text-xs uppercase tracking-wider text-white/60 mb-2">Citations</div>
      <ul className="space-y-2 text-sm">
        {unique.map((c, i) => (
          <li key={i} className="bg-black/30 rounded p-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold">{c.agent}</span>
              <span className="text-white/40 text-xs">conf {Math.round(c.confidence * 100)}% · {c.hops}hop</span>
            </div>
            <div className="text-white/80">{c.snippet}</div>
            <div className="text-white/40 text-[11px] break-all">{c.source_uri}</div>
          </li>
        ))}
        {unique.length === 0 && <li className="text-white/40">No citations yet.</li>}
      </ul>
    </div>
  );
}
