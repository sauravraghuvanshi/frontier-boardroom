import { QRCodeSVG } from "qrcode.react";
import { useStore, type Role } from "../store";
import { getRoleMeta } from "./MessageBubble";

const ROLES: Role[] = ["CEO", "CFO", "CMO", "CTO", "Legal"];

const FOUNDRY_AGENT_BASE_MODEL: Record<string, string> = {
  "CEO@5": "gpt-5 · RAG",
  "CEO@2": "gpt-5",
  "CEO@1": "gpt-5",
  "CMO@3": "grok-4-1-fast-reasoning · RAG",
  "CMO@2": "grok-4 · RAG",
  "CMO@1": "grok-4-20-reasoning",
  "CTO@6": "gpt-4.1 · RAG",
  "CTO@3": "gpt-4.1 · RAG",
  "gpt-4.1": "gpt-4.1",
  "CTO@2": "DeepSeek · RAG",
  "CTO@1": "DeepSeek-V3.2-Speciale",
  "gpt-5": "gpt-5",
};

function modelLabel(ref: string) {
  if (ref.startsWith("databricks:")) {
    return ref.replace("databricks:", "").replace(/^databricks-/, "");
  }
  const r = ref.replace("foundry:", "");
  return FOUNDRY_AGENT_BASE_MODEL[r] || r;
}

export function ParticipantsRail() {
  const speakingAgent = useStore((s) => s.speakingAgent);
  const models = useStore((s) => s.modelByRole);
  const citations = useStore((s) => s.citations);

  const audienceUrl =
    (import.meta.env.VITE_AUDIENCE_URL as string | undefined) ||
    `${window.location.origin}/audience-question`;

  const seen = new Set<string>();
  const uniqueCites = citations.filter((c) => {
    const k = `${c.agent}|${c.source_uri}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });

  return (
    <aside className="w-[340px] shrink-0 bg-[#11131f] border-l border-white/5 flex flex-col">
      <div className="px-4 py-3 border-b border-white/5">
        <div className="text-[11px] uppercase tracking-wider text-white/40">
          Members · {ROLES.length}
        </div>
      </div>
      <div className="px-2 py-2 space-y-1">
        {ROLES.map((role) => {
          const meta = getRoleMeta(role);
          const live = speakingAgent === role;
          return (
            <div
              key={role}
              className={`rounded-md px-2.5 py-2 ${
                live ? "bg-white/5" : "hover:bg-white/[0.03]"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <div className="relative">
                  <div
                    className={`w-8 h-8 rounded-full ${meta.bg} flex items-center justify-center text-xs font-semibold text-white`}
                  >
                    {role[0]}
                  </div>
                  <span
                    className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#11131f] ${
                      live ? "bg-emerald-400 animate-pulse" : "bg-emerald-500/70"
                    }`}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">
                    {meta.name}
                  </div>
                  <div className="text-[11px] text-white/40 truncate">
                    {role} · {meta.title.split(" ").slice(-1)[0]}
                  </div>
                </div>
                {live && (
                  <span className="text-[10px] text-emerald-400">speaking</span>
                )}
              </div>
              <div className="mt-2 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-[11px] text-white/80 font-mono">
                {modelLabel(models[role])}
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-white/5 px-4 py-3">
        <div className="text-[11px] uppercase tracking-wider text-white/40 mb-2">
          Citations · {uniqueCites.length}
        </div>
        <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
          {uniqueCites.length === 0 && (
            <div className="text-xs text-white/40">
              Sources cited by agents will appear here.
            </div>
          )}
          {uniqueCites.map((c, i) => (
            <div
              key={i}
              className="bg-black/30 border border-white/5 rounded p-2 text-xs"
            >
              <div className="flex justify-between items-center mb-0.5">
                <span className="font-semibold text-white/90">{c.agent}</span>
                <span className="text-white/40 text-[10px]">
                  {Math.round(c.confidence * 100)}% · {c.hops}h
                </span>
              </div>
              <div className="text-white/70 line-clamp-2">{c.snippet}</div>
              <div className="text-white/30 text-[10px] truncate mt-0.5">
                {c.source_uri}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-auto border-t border-white/5 px-4 py-3 flex gap-3 items-center bg-gradient-to-br from-indigo-500/5 to-cyan-500/5">
        <QRCodeSVG
          value={audienceUrl}
          size={64}
          bgColor="#11131f"
          fgColor="#818cf8"
        />
        <div className="text-xs text-white/60">
          <div className="uppercase tracking-wider text-[10px] text-cyan-300/80 mb-0.5">
            Audience Q
          </div>
          <div>Scan to submit a live question.</div>
          <div className="text-white/30 text-[10px] mt-0.5 truncate max-w-[180px]">
            {audienceUrl}
          </div>
        </div>
      </div>
    </aside>
  );
}
