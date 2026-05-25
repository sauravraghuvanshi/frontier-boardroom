import { create } from "zustand";

export type Role = "CEO" | "CFO" | "CMO" | "CTO" | "Legal";
export type MoodLabel = "cordial" | "debating" | "heated" | "converging" | "resolved";

export type Citation = {
  agent: Role;
  source_uri: string;
  snippet: string;
  confidence: number;
  hops: number;
};

export type TurnEntry = {
  agent: Role;
  model: string;
  text: string;
  done: boolean;
};

type State = {
  sessionId: string | null;
  connected: boolean;
  speakingAgent: Role | null;
  turns: TurnEntry[];
  citations: Citation[];
  mood: { value: number; label: MoodLabel };
  decision: string | null;
  vote: Record<string, string> | null;
  frozen: boolean;
  modelByRole: Record<Role, string>;
  setSession: (id: string) => void;
  setConnected: (v: boolean) => void;
  onEvent: (evt: any) => void;
  swapModel: (role: Role, ref: string) => void;
  resetDebate: () => void;
};

const empty: Record<Role, string> = {
  CEO: "foundry:CEO@5",
  CFO: "databricks:databricks-claude-sonnet-4-6",
  CMO: "foundry:CMO@3",
  CTO: "foundry:CTO@3",
  Legal: "databricks:databricks-claude-opus-4-6",
};

export const useStore = create<State>((set, get) => ({
  sessionId: null,
  connected: false,
  speakingAgent: null,
  turns: [],
  citations: [],
  mood: { value: 0.5, label: "cordial" },
  decision: null,
  vote: null,
  frozen: false,
  modelByRole: empty,
  setSession: (id) => set({ sessionId: id }),
  setConnected: (v) => set({ connected: v }),
  swapModel: (role, ref) =>
    set((s) => ({ modelByRole: { ...s.modelByRole, [role]: ref } })),
  resetDebate: () =>
    set({
      turns: [],
      citations: [],
      decision: null,
      vote: null,
      speakingAgent: null,
      frozen: false,
      mood: { value: 0.5, label: "cordial" },
    }),
  onEvent: (evt) => {
    const s = get();
    // Once a debate is frozen, ignore every event except a fresh reset.
    // Defensive: stale audio_chunk / viseme / late turn_start packets
    // that arrive after debate_end must not append bubbles below the
    // pinned decision card.
    if (s.frozen && evt.type !== "error") return;
    switch (evt.type) {
      case "turn_start":
        set({
          speakingAgent: evt.agent,
          turns: [
            ...s.turns,
            { agent: evt.agent, model: evt.model, text: "", done: false },
          ],
          modelByRole: { ...s.modelByRole, [evt.agent as Role]: evt.model },
        });
        break;
      case "token": {
        const turns = [...s.turns];
        const last = turns[turns.length - 1];
        if (last && last.agent === evt.agent) {
          last.text += evt.text;
          set({ turns });
        }
        break;
      }
      case "citation":
        set({ citations: [...s.citations, evt] });
        break;
      case "turn_end": {
        const turns = [...s.turns];
        const last = turns[turns.length - 1];
        if (last && last.agent === evt.agent) {
          last.done = true;
          set({ turns });
        }
        break;
      }
      case "mood":
        set({ mood: { value: evt.value, label: evt.label } });
        break;
      case "debate_end":
        set({
          decision: evt.decision,
          vote: evt.vote,
          speakingAgent: null,
          frozen: true,
        });
        break;
      case "audio_chunk":
      case "viseme":
      case "tool_call":
      case "error":
      default:
        break;
    }
  },
}));
