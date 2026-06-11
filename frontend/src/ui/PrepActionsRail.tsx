import { useStore, type PrepMode, type Role } from "../store";
import { SCENARIOS } from "./ChannelList";
import { getRoleMeta } from "./MessageBubble";

const ALL_SEATS: Role[] = ["CEO", "CFO", "CMO", "CTO", "Legal"];

type Props = {
  seat: Role | null;
  agendaId: string | null;
  onPickAgenda: (id: string | null, topic: string) => void;
  onPickMode: (m: PrepMode, simulateRole?: Role) => void;
};

export function PrepActionsRail({ seat, agendaId, onPickAgenda, onPickMode }: Props) {
  const subMode = useStore((s) => s.prepSubMode);
  const citations = useStore((s) => s.prepCitations);
  const seatModel = useStore((s) =>
    seat ? s.modelByRole[seat] : null,
  );

  const otherSeats = seat ? ALL_SEATS.filter((r) => r !== seat) : [];

  // Dedup citations by source_uri (last write wins).
  const dedup = new Map<string, (typeof citations)[number]>();
  for (const c of citations) dedup.set(c.source_uri, c);
  const uniqueCites = Array.from(dedup.values()).slice(-8);

  return (
    <aside className="w-[320px] shrink-0 bg-[#11131f] border-l border-white/5 flex flex-col overflow-hidden">
      {seat ? (
        <>
          <SeatCard seat={seat} model={seatModel} />

          <Section title="Agenda topic">
            <div className="space-y-1">
              <button
                onClick={() => onPickAgenda(null, "Open prep — no fixed agenda")}
                className={`w-full text-left rounded-md px-2.5 py-1.5 text-[13px] border transition ${
                  agendaId === null
                    ? "bg-[#4338ca]/30 text-white border-indigo-400/40"
                    : "text-white/70 hover:bg-white/5 border-transparent"
                }`}
              >
                <span className="text-white/40 mr-1">○</span> Open prep
              </button>
              {SCENARIOS.map((s) => {
                const isActive = agendaId === s.id;
                return (
                  <button
                    key={s.id}
                    onClick={() => onPickAgenda(s.id, s.topic)}
                    className={`w-full text-left rounded-md px-2.5 py-1.5 text-[13px] border transition ${
                      isActive
                        ? "bg-[#4338ca]/30 text-white border-indigo-400/40"
                        : "text-white/70 hover:bg-white/5 border-transparent"
                    }`}
                  >
                    <span className="text-white/40 mr-1">#</span> {s.label}
                  </button>
                );
              })}
            </div>
          </Section>

          <Section title="Sub-mode">
            <div className="grid grid-cols-2 gap-2">
              <ModeBtn
                active={subMode === "coach"}
                onClick={() => onPickMode("coach")}
                label="Coach me"
                hint="Sharpen your argument"
              />
              <ModeBtn
                active={subMode === "drill"}
                onClick={() => onPickMode("drill")}
                label="Drill me"
                hint="Tough Qs, one at a time"
              />
            </div>
            <div className="mt-3">
              <div className="text-[11px] uppercase tracking-wider text-white/40 mb-1.5">
                Simulate seat
              </div>
              <div className="grid grid-cols-2 gap-2">
                {otherSeats.map((r) => {
                  const meta = getRoleMeta(r);
                  return (
                    <button
                      key={r}
                      onClick={() => onPickMode("simulate", r)}
                      className="rounded-md px-2 py-1.5 text-[12px] border border-white/10 hover:bg-white/5 text-white/80 flex items-center gap-2"
                    >
                      <span
                        className={`w-5 h-5 rounded-full ${meta.bg} flex items-center justify-center text-[10px] font-semibold text-white shrink-0`}
                      >
                        {r[0]}
                      </span>
                      <span className="truncate">Ask {r}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </Section>

          <Section title="Sources">
            {uniqueCites.length === 0 ? (
              <div className="text-[12px] text-white/40">
                Citations will appear here as your AI counterpart pulls grounded
                excerpts.
              </div>
            ) : (
              <ul className="space-y-1.5">
                {uniqueCites.map((c, i) => (
                  <li key={i}>
                    <a
                      href={c.source_uri}
                      target="_blank"
                      rel="noreferrer"
                      title={c.snippet}
                      className="block text-[12px] text-white/70 hover:text-white truncate"
                    >
                      <span className="text-white/40 mr-1">·</span>
                      {sourceName(c.source_uri)}
                      <span className="ml-1 text-white/40">
                        {Math.round(c.confidence * 100)}%
                      </span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </Section>
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center text-center px-6">
          <div className="text-sm text-white/50">
            Pick a seat on the left rail to start prep.
          </div>
        </div>
      )}
    </aside>
  );
}

function SeatCard({ seat, model }: { seat: Role; model: string | null }) {
  const meta = getRoleMeta(seat);
  return (
    <div className="px-4 py-3 border-b border-white/5 flex items-center gap-3">
      <span
        className={`w-10 h-10 rounded-full ${meta.bg} flex items-center justify-center text-base font-semibold text-white shrink-0`}
      >
        {seat[0]}
      </span>
      <div className="min-w-0">
        <div className="text-sm font-semibold text-white truncate">
          AI {meta.name}
        </div>
        <div className="text-[11px] text-white/50 truncate">{meta.title}</div>
        {model && (
          <div className="mt-0.5 text-[10px] font-mono text-white/40 truncate">
            {model.replace("foundry:", "").replace("databricks:", "")}
          </div>
        )}
      </div>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="px-3 py-3 border-b border-white/5">
      <div className="text-[11px] uppercase tracking-wider text-white/40 mb-2">
        {title}
      </div>
      {children}
    </div>
  );
}

function ModeBtn({
  active,
  onClick,
  label,
  hint,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  hint: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-2.5 py-2 text-left transition border ${
        active
          ? "bg-[#4338ca]/40 text-white border-indigo-400/40"
          : "text-white/80 hover:bg-white/5 border-white/10"
      }`}
    >
      <div className="text-[13px] font-medium">{label}</div>
      <div className="text-[10px] text-white/50 mt-0.5">{hint}</div>
    </button>
  );
}

function sourceName(uri: string) {
  try {
    const last = uri.split("/").filter(Boolean).pop() || uri;
    return last.length > 28 ? last.slice(0, 28) + "…" : last;
  } catch {
    return uri;
  }
}
