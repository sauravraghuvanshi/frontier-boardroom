import { useEffect, useRef, useState } from "react";
import { useStore, type PrepMode, type Role } from "../store";
import { usePrepStream } from "../usePrepStream";
import { PrepSeatPicker } from "./PrepSeatPicker";
import { PrepThread } from "./PrepThread";
import { PrepActionsRail } from "./PrepActionsRail";

export function PrepShell() {
  const seat = useStore((s) => s.prepSeat);
  const agendaId = useStore((s) => s.prepAgendaId);
  const agendaTopic = useStore((s) => s.prepAgendaTopic);
  const subMode = useStore((s) => s.prepSubMode);
  const prepSessionId = useStore((s) => s.prepSessionId);
  const setPrepSeat = useStore((s) => s.setPrepSeat);
  const setPrepAgenda = useStore((s) => s.setPrepAgenda);
  const setPrepSubMode = useStore((s) => s.setPrepSubMode);
  const resetPrep = useStore((s) => s.resetPrep);

  const { start, send, close } = usePrepStream();
  const [simulateRole, setSimulateRole] = useState<Role | null>(null);
  const [busy, setBusy] = useState(false);

  // The active prep_session_id is bound to (seat, agendaId). When either flips,
  // the existing session is no longer valid — close the WS and force a fresh
  // /api/v1/prep-session POST on the next send.
  const sessionKey = useRef<string | null>(null);
  useEffect(() => {
    const key = seat ? `${seat}|${agendaId ?? "open"}` : null;
    if (sessionKey.current && sessionKey.current !== key) {
      close();
      resetPrep();
    }
    sessionKey.current = key;
  }, [seat, agendaId, close, resetPrep]);

  useEffect(() => () => close(), [close]);

  function pickSeat(r: Role) {
    if (r === seat) return;
    setPrepSeat(r);
    // Default to "Open prep" when the seat first lands; user can refine.
    if (!agendaId && !agendaTopic) {
      setPrepAgenda(null, "Open prep — no fixed agenda");
    }
  }

  function pickAgenda(id: string | null, topic: string) {
    setPrepAgenda(id, topic);
  }

  function pickMode(m: PrepMode, sim?: Role) {
    setPrepSubMode(m);
    setSimulateRole(m === "simulate" ? sim ?? null : null);
  }

  async function handleSend(text: string) {
    if (!seat) return;
    setBusy(true);
    try {
      let sid = prepSessionId;
      if (!sid || sessionKey.current !== `${seat}|${agendaId ?? "open"}`) {
        sid = await start(seat, agendaId, agendaTopic ?? "Open prep — no fixed agenda");
        sessionKey.current = `${seat}|${agendaId ?? "open"}`;
      }
      await send(sid, text, subMode, simulateRole);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PrepSeatPicker active={seat} onPick={pickSeat} />
      <PrepThread
        seat={seat}
        agendaTopic={agendaTopic}
        onSend={handleSend}
        disabled={busy}
      />
      <PrepActionsRail
        seat={seat}
        agendaId={agendaId}
        onPickAgenda={pickAgenda}
        onPickMode={pickMode}
      />
    </>
  );
}
