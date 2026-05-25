import { useStore, type Role } from "../store";
import { swapModel } from "../useDebateStream";

const CHOICES: Record<Role, string[]> = {
  CEO: ["foundry:gpt-5", "foundry:grok-3"],
  CFO: ["databricks:claude-sonnet-4-5", "foundry:gpt-5"],
  CMO: ["foundry:grok-3", "foundry:gpt-5"],
  CTO: ["foundry:llama-3.3-70b-instruct", "foundry:gpt-5"],
  Legal: ["databricks:claude-opus-4", "databricks:claude-sonnet-4-5"],
};

export function ModelSwapDial() {
  const models = useStore((s) => s.modelByRole);
  const swap = useStore((s) => s.swapModel);
  return (
    <div className="border-t border-white/10 p-3 space-y-2">
      <div className="text-xs uppercase tracking-wider text-white/60">Model Swap</div>
      {(Object.keys(CHOICES) as Role[]).map((role) => (
        <div key={role} className="flex items-center gap-2 text-sm">
          <span className="w-12 font-semibold">{role}</span>
          <select
            className="flex-1 bg-black/30 rounded px-2 py-1"
            value={models[role]}
            onChange={async (e) => {
              swap(role, e.target.value);
              await swapModel(role, e.target.value);
            }}
          >
            {CHOICES[role].map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
      ))}
    </div>
  );
}
