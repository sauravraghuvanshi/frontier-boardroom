import { create } from "zustand";

export type Role = "CEO" | "CFO" | "CMO" | "CTO" | "Legal";
export type MoodLabel = "cordial" | "debating" | "heated" | "converging" | "resolved";
export type PrepMode = "coach" | "drill";

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

// PrepMessage covers BOTH the human's right-aligned bubble (kind=user) and the
// AI seat's reply (kind=agent). A single message list keeps render order trivial.
export type PrepMessage =
  | {
      kind: "user";
      text: string;
      mode: PrepMode;
      timestamp: number;
    }
  | {
      kind: "agent";
      agent: Role;
      model: string;
      text: string;
      done: boolean;
      mode: PrepMode;
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

  // Prep slice — parallel to debate, separate WS connection.
  prepSessionId: string | null;
  prepConnected: boolean;
  prepSeat: Role | null;
  prepAgendaId: string | null;
  prepAgendaTopic: string | null;
  prepSubMode: PrepMode;
  prepMessages: PrepMessage[];
  prepCitations: Citation[];
  prepMood: { value: number; label: MoodLabel };
  prepSpeakingAgent: Role | null;

  setSession: (id: string) => void;
  setConnected: (v: boolean) => void;
  onEvent: (evt: any) => void;
  swapModel: (role: Role, ref: string) => void;
  resetDebate: () => void;

  // Prep actions.
  setPrepSession: (id: string) => void;
  setPrepConnected: (v: boolean) => void;
  setPrepSeat: (r: Role | null) => void;
  setPrepAgenda: (id: string | null, topic: string | null) => void;
  setPrepSubMode: (m: PrepMode) => void;
  onPrepEvent: (evt: any) => void;
  resetPrep: () => void;
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

  prepSessionId: null,
  prepConnected: false,
  prepSeat: null,
  prepAgendaId: null,
  prepAgendaTopic: null,
  prepSubMode: "coach",
  prepMessages: [],
  prepCitations: [],
  prepMood: { value: 0.5, label: "cordial" },
  prepSpeakingAgent: null,
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

  // ───────────────────────── Prep slice ─────────────────────────
  setPrepSession: (id) => set({ prepSessionId: id }),
  setPrepConnected: (v) => set({ prepConnected: v }),
  setPrepSeat: (r) => set({ prepSeat: r }),
  setPrepAgenda: (id, topic) =>
    set({ prepAgendaId: id, prepAgendaTopic: topic }),
  setPrepSubMode: (m) => set({ prepSubMode: m }),
  resetPrep: () =>
    set({
      prepMessages: [],
      prepCitations: [],
      prepMood: { value: 0.5, label: "cordial" },
      prepSpeakingAgent: null,
    }),
  onPrepEvent: (evt) => {
    const s = get();
    switch (evt.type) {
      case "prep_ready":
        // Server echo on WS connect — no UI state change needed beyond mood reset.
        break;
      case "user_message":
        set({
          prepMessages: [
            ...s.prepMessages,
            {
              kind: "user",
              text: evt.text,
              mode: evt.mode,
              timestamp: evt.timestamp || Date.now() / 1000,
            },
          ],
        });
        break;
      case "turn_start":
        set({
          prepSpeakingAgent: evt.agent,
          prepMessages: [
            ...s.prepMessages,
            {
              kind: "agent",
              agent: evt.agent,
              model: evt.model,
              text: "",
              done: false,
              mode: evt.mode || "coach",
            },
          ],
        });
        break;
      case "token": {
        const msgs = [...s.prepMessages];
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i];
          if (m.kind === "agent" && m.agent === evt.agent && !m.done) {
            msgs[i] = { ...m, text: m.text + evt.text };
            set({ prepMessages: msgs });
            break;
          }
        }
        break;
      }
      case "citation":
        set({ prepCitations: [...s.prepCitations, evt] });
        break;
      case "turn_end": {
        const msgs = [...s.prepMessages];
        for (let i = msgs.length - 1; i >= 0; i--) {
          const m = msgs[i];
          if (m.kind === "agent" && m.agent === evt.agent && !m.done) {
            msgs[i] = { ...m, done: true };
            set({ prepMessages: msgs, prepSpeakingAgent: null });
            break;
          }
        }
        break;
      }
      case "mood":
        set({ prepMood: { value: evt.value, label: evt.label } });
        break;
      case "delegation_start":
        // Delegation begins; store the delegated agent for UI feedback if needed
        // For now, no UI state change — all delegation events flow as tokens
        break;
      case "delegation_end":
        // Delegation complete; briefing block will be injected into next turn
        // onPrepEvent doesn't track briefings directly — that's done server-side
        break;
      case "audio_chunk":
      case "viseme":
      case "error":
      default:
        break;
    }
  },
}));
