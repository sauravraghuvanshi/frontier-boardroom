import { useEffect, useRef } from "react";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const POLL_MS = 3000;

// Polls the backend audience inbox. On hit, calls onQuestion(text).
// Only mount on the main presenter view.
export function useAudiencePoll(onQuestion: (q: string, name?: string) => void) {
  const cbRef = useRef(onQuestion);
  cbRef.current = onQuestion;

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const res = await fetch(`${API}/api/v1/audience-question/poll`);
        if (!res.ok) return;
        const body = await res.json();
        if (cancelled) return;
        if (body?.question?.question) {
          cbRef.current(body.question.question, body.question.name ?? undefined);
        }
      } catch {
        /* network blips are fine — we'll try again next interval */
      }
    }

    const id = window.setInterval(tick, POLL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);
}
