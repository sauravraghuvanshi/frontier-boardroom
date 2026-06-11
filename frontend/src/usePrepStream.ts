import { useEffect, useRef } from "react";
import { useStore, type Role, type PrepMode } from "./store";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export function usePrepStream() {
  const wsRef = useRef<WebSocket | null>(null);
  const setPrepSession = useStore((s) => s.setPrepSession);
  const setPrepConnected = useStore((s) => s.setPrepConnected);
  const onPrepEvent = useStore((s) => s.onPrepEvent);
  const resetPrep = useStore((s) => s.resetPrep);

  async function start(seat: Role, agendaId: string | null, agendaTopic: string) {
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
      try {
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.close();
      } catch {
        /* ignore */
      }
    }
    resetPrep();

    const res = await fetch(`${API}/api/v1/prep-session`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        role: seat,
        agenda_topic: agendaTopic,
        agenda_id: agendaId,
      }),
    });
    if (!res.ok) throw new Error(`prep-session create failed: ${res.status}`);
    const { prep_session_id } = await res.json();
    setPrepSession(prep_session_id);

    const ws = new WebSocket(`${WS}/ws/prep/${prep_session_id}`);
    ws.onopen = () => setPrepConnected(true);
    ws.onmessage = (e) => {
      if (wsRef.current !== ws) return;
      try {
        onPrepEvent(JSON.parse(e.data));
      } catch {
        /* ignore */
      }
    };
    ws.onclose = () => {
      if (wsRef.current === ws) setPrepConnected(false);
    };
    wsRef.current = ws;
    return prep_session_id as string;
  }

  async function send(
    sid: string,
    text: string,
    mode: PrepMode,
    simulateRole?: Role | null,
  ) {
    await fetch(`${API}/api/v1/prep-session/${sid}/message`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        text,
        mode,
        simulate_role: mode === "simulate" ? simulateRole : null,
      }),
    });
  }

  function close() {
    try {
      wsRef.current?.close();
    } catch {
      /* ignore */
    }
    wsRef.current = null;
  }

  useEffect(() => () => wsRef.current?.close(), []);
  return { start, send, close };
}
