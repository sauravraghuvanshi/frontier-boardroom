import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useStore, type Role, type TurnEntry, type Citation } from "../store";

const ROLE_META: Record<
  Role,
  { name: string; title: string; bg: string; ring: string }
> = {
  CEO: {
    name: "Aanya",
    title: "Chief Executive Officer",
    bg: "bg-sky-500",
    ring: "ring-sky-400/40",
  },
  CFO: {
    name: "Senthil",
    title: "Chief Financial Officer",
    bg: "bg-rose-500",
    ring: "ring-rose-400/40",
  },
  CMO: {
    name: "Priya",
    title: "Chief Marketing Officer",
    bg: "bg-emerald-500",
    ring: "ring-emerald-400/40",
  },
  CTO: {
    name: "Karthik",
    title: "Chief Technology Officer",
    bg: "bg-fuchsia-500",
    ring: "ring-fuchsia-400/40",
  },
  Legal: {
    name: "Meera",
    title: "General Counsel",
    bg: "bg-amber-500",
    ring: "ring-amber-400/40",
  },
};

export function getRoleMeta(role: Role) {
  return ROLE_META[role];
}

// Foundry agent ref → underlying base model name (display only).
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

function modelBadge(model: string) {
  if (model.startsWith("databricks:")) {
    const raw = model.replace("databricks:", "").replace(/^databricks-/, "");
    return { label: raw, cls: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30" };
  }
  const ref = model.replace("foundry:", "");
  const base = FOUNDRY_AGENT_BASE_MODEL[ref] || ref;
  return { label: base, cls: "bg-sky-500/15 text-sky-300 border-sky-500/30" };
}

type Props = {
  turn: TurnEntry;
  index: number;
  citations: Citation[];
  // When true, render as a right-aligned human bubble (no avatar, indigo bg).
  // The `turn.text` is treated as the human's prompt; agent fields are ignored.
  userMessage?: boolean;
  liveOverride?: boolean;
};

export function MessageBubble({ turn, citations, userMessage, liveOverride }: Props) {
  const speakingAgent = useStore((s) => s.speakingAgent);

  if (userMessage) {
    return (
      <div className="flex justify-end px-6 py-2">
        <div className="max-w-[70%] bg-[#3b3f8c] text-white rounded-2xl rounded-tr-sm px-4 py-2 shadow-sm">
          <div className="text-[15px] leading-relaxed whitespace-pre-wrap">
            {turn.text}
          </div>
        </div>
      </div>
    );
  }

  const meta = ROLE_META[turn.agent];
  const isLive =
    liveOverride !== undefined
      ? liveOverride
      : !turn.done && speakingAgent === turn.agent;
  const badge = modelBadge(turn.model);
  const turnCites = citations.filter((c) => c.agent === turn.agent);

  return (
    <div className="flex gap-3 px-6 py-3 hover:bg-white/[0.02] group">
      <div
        className={`w-9 h-9 rounded-full ${meta.bg} flex items-center justify-center text-sm font-semibold text-white shrink-0 ring-2 ${
          isLive ? meta.ring + " ring-offset-2 ring-offset-[#1a1a1e]" : "ring-transparent"
        }`}
      >
        {turn.agent[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-baseline flex-wrap gap-x-2">
          <span className="font-semibold text-white">{meta.name}</span>
          <span className="text-xs text-white/40">{meta.title}</span>
          <span
            className={`text-[10px] px-1.5 py-0.5 rounded border ${badge.cls} font-mono`}
            title={turn.model}
          >
            {badge.label}
          </span>
          {isLive && (
            <span className="text-[10px] text-emerald-400 flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-emerald-400 animate-pulse" />
              typing
            </span>
          )}
        </div>
        <div className="text-[15px] leading-relaxed text-white/90 mt-0.5 md-body">
          {turn.text ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => (
                  <a
                    {...props}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[#8aa4ff] hover:underline"
                  />
                ),
                code: ({ node, className, children, ...props }: any) => {
                  const inline = !className;
                  return inline ? (
                    <code className="bg-white/10 rounded px-1 py-0.5 text-[13px] font-mono" {...props}>
                      {children}
                    </code>
                  ) : (
                    <pre className="bg-black/40 border border-white/10 rounded p-2 overflow-x-auto text-[13px] font-mono my-2">
                      <code {...props}>{children}</code>
                    </pre>
                  );
                },
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto my-2">
                    <table className="border-collapse text-sm" {...props} />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th className="border border-white/15 px-2 py-1 bg-white/5 text-left" {...props} />
                ),
                td: ({ node, ...props }) => (
                  <td className="border border-white/10 px-2 py-1 align-top" {...props} />
                ),
                ul: ({ node, ...props }) => (
                  <ul className="list-disc pl-5 my-1 space-y-0.5" {...props} />
                ),
                ol: ({ node, ...props }) => (
                  <ol className="list-decimal pl-5 my-1 space-y-0.5" {...props} />
                ),
                h1: ({ node, ...props }) => (
                  <h1 className="text-lg font-semibold mt-2 mb-1" {...props} />
                ),
                h2: ({ node, ...props }) => (
                  <h2 className="text-base font-semibold mt-2 mb-1" {...props} />
                ),
                h3: ({ node, ...props }) => (
                  <h3 className="text-sm font-semibold uppercase tracking-wide text-white/80 mt-2 mb-1" {...props} />
                ),
                hr: () => <hr className="border-white/10 my-2" />,
                blockquote: ({ node, ...props }) => (
                  <blockquote className="border-l-2 border-[#7b83eb]/40 pl-3 my-2 text-white/80 italic" {...props} />
                ),
              }}
            >
              {turn.text}
            </ReactMarkdown>
          ) : isLive ? (
            <span className="text-white/40">…</span>
          ) : null}
        </div>
        {turnCites.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {turnCites.map((c, i) => (
              <a
                key={i}
                href={c.source_uri}
                target="_blank"
                rel="noreferrer"
                className="text-[11px] px-2 py-0.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 text-white/70"
                title={c.snippet}
              >
                {sourceName(c.source_uri)} · {Math.round(c.confidence * 100)}%
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function sourceName(uri: string) {
  try {
    const last = uri.split("/").filter(Boolean).pop() || uri;
    return last.length > 32 ? last.slice(0, 32) + "…" : last;
  } catch {
    return uri;
  }
}
