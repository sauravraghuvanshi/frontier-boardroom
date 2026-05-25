import clsx from "clsx";
import { useStore } from "../store";

export function SpeakerBadge() {
  const speaker = useStore((s) => s.speakingAgent);
  const model = useStore((s) => (speaker ? s.modelByRole[speaker] : null));
  if (!speaker) return null;
  const provider = model?.split(":")[0] ?? "?";
  return (
    <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/60 px-3 py-1.5 rounded-full text-sm">
      <span className="font-semibold">{speaker}</span>
      <span
        className={clsx(
          "uppercase text-[10px] tracking-widest px-2 py-0.5 rounded-full",
          provider === "foundry" ? "bg-sky-500/30 text-sky-200" : "bg-emerald-500/30 text-emerald-200",
        )}
      >
        {provider}
      </span>
      <span className="text-white/60 text-xs">{model}</span>
    </div>
  );
}
