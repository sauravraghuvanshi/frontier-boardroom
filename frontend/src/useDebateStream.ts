import { useEffect, useRef } from "react";
import { useStore } from "./store";
import { backendFetch } from "./auth";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export function useDebateStream() {
  const wsRef = useRef<WebSocket | null>(null);
  const setSession = useStore((s) => s.setSession);
  const setConnected = useStore((s) => s.setConnected);
  const onEvent = useStore((s) => s.onEvent);
  const resetDebate = useStore((s) => s.resetDebate);

  async function start(question: string, scenarioId?: string) {
    // Close any in-flight socket and wipe state from the previous debate so
    // new turns never stream below a pinned decision card from a prior run.
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      try {
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.close();
      } catch {
        /* ignore */
      }
    }
    resetDebate();

    const sessRes = await backendFetch(`${API}/api/v1/session`, {
      method: "POST",
    });
    if (!sessRes.ok) {
      throw new Error(`session create failed: ${sessRes.status}`);
    }
    const { session_id } = await sessRes.json();
    setSession(session_id);

    const ws = new WebSocket(`${WS}/ws/debate/${session_id}`);
    ws.onopen = () => {
      setConnected(true);
      void backendFetch(`${API}/api/v1/debate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ session_id, question, scenario_id: scenarioId }),
      });
    };
    ws.onmessage = (e) => {
      // Drop messages from a socket we've already replaced.
      if (wsRef.current !== ws) return;
      try {
        onEvent(JSON.parse(e.data));
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      if (wsRef.current === ws) setConnected(false);
    };
    wsRef.current = ws;
  }

  useEffect(() => () => wsRef.current?.close(), []);
  return { start };
}

export async function swapModel(role: string, modelRef: string) {
  await backendFetch(`${API}/api/v1/agent/${role}/swap-model`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ model_ref: modelRef }),
  });
}
