import { useCallback, useEffect, useRef } from "react";
import { useStore, type Role, type PrepMode } from "./store";
import { parseMentions } from "./utils/mentionParser";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS = import.meta.env.VITE_WS_BASE || "ws://localhost:8000";

export function usePrepStream() {
  const wsRef = useRef<WebSocket | null>(null);
  const setPrepSession = useStore((s) => s.setPrepSession);
  const setPrepConnected = useStore((s) => s.setPrepConnected);
  const onPrepEvent = useStore((s) => s.onPrepEvent);
  const resetPrep = useStore((s) => s.resetPrep);

  // Stable function refs are load-bearing: PrepShell has
  // `useEffect(() => () => close(), [close])` for unmount-cleanup. If the
  // returned `close` reference changes every render, that effect's cleanup
  // fires on every render and tears down the WebSocket between Send and the
  // first frame — surfacing as
  // "WebSocket is closed before the connection is established".
  const start = useCallback(
    async (seat: Role, agendaId: string | null, agendaTopic: string) => {
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
    },
    [setPrepSession, setPrepConnected, onPrepEvent, resetPrep],
  );

  const send = useCallback(
    async (sid: string, text: string, mode: PrepMode) => {
      const { mentions } = parseMentions(text);
      await fetch(`${API}/api/v1/prep-session/${sid}/message`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text, mode, mentions }),
      });
    },
    [],
  );

  const close = useCallback(() => {
    try {
      wsRef.current?.close();
    } catch {
      /* ignore */
    }
    wsRef.current = null;
  }, []);

  useEffect(() => () => wsRef.current?.close(), []);
  return { start, send, close };
}
