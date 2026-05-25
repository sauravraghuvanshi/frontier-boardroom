import { useState } from "react";
import { Logo } from "../branding/Logo";
import { COMPANY } from "../branding/company";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";

type Status = "idle" | "sending" | "sent" | "error";

export function AudienceQuestionPage() {
  const [question, setQuestion] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (question.trim().length < 4) return;
    setStatus("sending");
    setErrorMsg(null);
    try {
      const res = await fetch(`${API}/api/v1/audience-question`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          question: question.trim(),
          name: name.trim() || null,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setStatus("sent");
      setQuestion("");
    } catch (err: any) {
      setStatus("error");
      setErrorMsg(err?.message ?? "Failed to send");
    }
  }

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#0a0b14] via-[#11131f] to-[#1e1b4b] text-white flex flex-col items-center px-5 py-10">
      <div className="flex items-center gap-3 mb-8">
        <Logo size={40} />
        <div>
          <div className="text-lg font-semibold leading-tight">
            {COMPANY.productName}
          </div>
          <div className="text-[11px] uppercase tracking-widest text-white/40">
            Audience Question
          </div>
        </div>
      </div>

      <form
        onSubmit={submit}
        className="w-full max-w-md bg-[#11131f]/80 backdrop-blur border border-white/10 rounded-2xl p-6 shadow-2xl shadow-indigo-900/30"
      >
        <h1 className="text-xl font-semibold">Ask the board</h1>
        <p className="text-sm text-white/60 mt-1 mb-5">
          Your question will be sent live to the {COMPANY.name} virtual C-suite
          and debated on screen.
        </p>

        <label className="block text-[11px] uppercase tracking-wider text-white/50 mb-1">
          Your name (optional)
        </label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={80}
          placeholder="Anonymous"
          className="w-full bg-black/30 border border-white/10 rounded-md px-3 py-2 text-sm outline-none focus:border-indigo-400 mb-4"
        />

        <label className="block text-[11px] uppercase tracking-wider text-white/50 mb-1">
          Question for the board
        </label>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={5}
          maxLength={500}
          required
          placeholder="e.g. Should we IPO in 2027 or stay private?"
          className="w-full bg-black/30 border border-white/10 rounded-md px-3 py-2 text-sm resize-none outline-none focus:border-indigo-400"
        />
        <div className="text-[11px] text-white/40 text-right mt-1">
          {question.length}/500
        </div>

        <button
          type="submit"
          disabled={status === "sending" || question.trim().length < 4}
          className="mt-4 w-full bg-gradient-to-r from-indigo-500 to-indigo-400 hover:from-indigo-400 hover:to-cyan-400 disabled:from-white/10 disabled:to-white/10 disabled:text-white/40 text-white font-medium py-2.5 rounded-md transition"
        >
          {status === "sending" ? "Sending…" : "Send to the board"}
        </button>

        {status === "sent" && (
          <div className="mt-4 text-center bg-emerald-500/10 border border-emerald-400/30 text-emerald-300 text-sm rounded-md py-2">
            ✓ Sent. The board will pick it up shortly.
          </div>
        )}
        {status === "error" && (
          <div className="mt-4 text-center bg-rose-500/10 border border-rose-400/30 text-rose-300 text-sm rounded-md py-2">
            Couldn’t send — {errorMsg}. Try again.
          </div>
        )}
      </form>

      <div className="mt-8 text-[11px] text-white/40 text-center max-w-sm">
        {COMPANY.productByline}. Questions are anonymous unless you give a name.
      </div>
    </div>
  );
}
