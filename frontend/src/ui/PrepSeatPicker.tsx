import type { Role } from "../store";
import { getRoleMeta } from "./MessageBubble";

const SEATS: Role[] = ["CEO", "CFO", "CMO", "CTO", "Legal"];

type Props = {
  active: Role | null;
  onPick: (r: Role) => void;
};

export function PrepSeatPicker({ active, onPick }: Props) {
  return (
    <aside className="w-[260px] shrink-0 bg-[#11131f] border-r border-white/5 flex flex-col">
      <div className="px-4 py-3 border-b border-white/5">
        <div className="text-sm font-semibold text-white">Boardroom Prep</div>
        <div className="text-[10px] uppercase tracking-widest text-white/40">
          1:1 sparring with your AI counterpart
        </div>
      </div>
      <div className="px-3 pt-3 pb-1 text-[11px] uppercase tracking-wider text-white/40">
        I am the…
      </div>
      <ul className="px-2 space-y-1">
        {SEATS.map((seat) => {
          const meta = getRoleMeta(seat);
          const isActive = active === seat;
          return (
            <li key={seat}>
              <button
                onClick={() => onPick(seat)}
                className={`w-full text-left rounded-md px-2.5 py-2 flex items-center gap-3 transition border ${
                  isActive
                    ? "bg-[#4338ca]/40 text-white border-indigo-400/40"
                    : "text-white/80 hover:bg-white/5 border-transparent"
                }`}
              >
                <span
                  className={`w-9 h-9 rounded-full ${meta.bg} flex items-center justify-center text-sm font-semibold text-white shrink-0`}
                >
                  {seat[0]}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block text-sm font-medium truncate">
                    {meta.name}
                    <span className="ml-1.5 text-[11px] font-normal text-white/40">
                      · {seat}
                    </span>
                  </span>
                  <span className="block text-[11px] text-white/50 truncate">
                    {meta.title}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      <div className="mt-auto px-4 py-3 border-t border-white/5 text-[11px] text-white/40 leading-relaxed">
        Pick the seat you'll occupy in the upcoming board meeting. Your AI
        counterpart will coach you, then drill you hard.
      </div>
    </aside>
  );
}
