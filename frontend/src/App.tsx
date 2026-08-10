import { useEffect, useState } from "react";
import { useDebateStream } from "./useDebateStream";
import { ChannelList, SCENARIOS } from "./ui/ChannelList";
import { ChatThread } from "./ui/ChatThread";
import { ParticipantsRail } from "./ui/ParticipantsRail";
import { AboutPage } from "./ui/AboutPage";
import { AudienceQuestionPage } from "./ui/AudienceQuestionPage";
import { PrepShell } from "./ui/PrepShell";
import { Logo } from "./branding/Logo";
import { COMPANY } from "./branding/company";
import { useAudiencePoll } from "./useAudiencePoll";
import { useStore } from "./store";
import { ENTRA_AUTH_ENABLED, signOut } from "./auth";

type View = "boardroom" | "about" | "audience" | "prep";

function detectInitialView(): View {
  if (typeof window === "undefined") return "boardroom";
  const p = window.location.pathname;
  if (p.startsWith("/audience-question")) return "audience";
  if (p.startsWith("/about")) return "about";
  if (p.startsWith("/prep")) return "prep";
  return "boardroom";
}

export default function App() {
  const initialView = detectInitialView();
  const { start } = useDebateStream();
  const [view, setView] = useState<View>(initialView);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [topic, setTopic] = useState<string | null>(null);
  const [question, setQuestion] = useState<string | null>(null);
  const connected = useStore((s) => s.connected);

  function handlePick(q: string, id?: string) {
    const scenario = id ? SCENARIOS.find((s) => s.id === id) : null;
    setActiveId(id || "custom");
    setTopic(scenario ? scenario.topic : "Custom topic");
    setQuestion(q);
    setView("boardroom");
    start(q, id);
  }

  // Audience-submitted question routes through the same start() flow.
  useAudiencePoll((q, name) => {
    setActiveId("audience");
    setTopic(name ? `Audience question — ${name}` : "Audience question");
    setQuestion(q);
    setView("boardroom");
    start(q);
  });

  // Sync history so refreshes keep the user on the same view.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const path =
      view === "audience"
        ? "/audience-question"
        : view === "about"
        ? "/about"
        : view === "prep"
        ? "/prep"
        : "/";
    if (window.location.pathname !== path) {
      window.history.replaceState(null, "", path);
    }
  }, [view]);

  // Audience phones see only the form — no header, no rails.
  if (view === "audience") return <AudienceQuestionPage />;

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0a0b14] text-white overflow-hidden font-sans">
      {/* Top header bar */}
      <header className="flex items-center gap-4 px-5 h-[52px] border-b border-white/5 bg-[#0a0b14]/95 backdrop-blur shrink-0 bg-board-grid">
        <div className="flex items-center gap-2.5">
          <Logo size={28} />
          <div className="leading-tight">
            <div className="text-sm font-semibold tracking-tight">
              {COMPANY.productName}
            </div>
            <div className="text-[10px] uppercase tracking-widest text-white/40">
              {COMPANY.productByline}
            </div>
          </div>
        </div>

        <nav className="ml-6 flex items-center gap-1 text-sm">
          <NavBtn active={view === "boardroom"} onClick={() => setView("boardroom")}>
            Boardroom
          </NavBtn>
          <NavBtn active={view === "prep"} onClick={() => setView("prep")}>
            Prep
          </NavBtn>
          <NavBtn active={view === "about"} onClick={() => setView("about")}>
            About {COMPANY.name}
          </NavBtn>
        </nav>

        <div className="ml-auto flex items-center gap-2 text-[11px] text-white/50">
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connected ? "bg-emerald-400 animate-pulse" : "bg-white/30"
            }`}
          />
          {connected ? "Live" : "Idle"}
          {ENTRA_AUTH_ENABLED && (
            <button
              type="button"
              onClick={signOut}
              className="ml-2 rounded-md border border-white/10 px-2 py-1 text-white/60 transition hover:border-white/20 hover:text-white"
            >
              Sign out
            </button>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {view === "about" ? (
          <AboutPage />
        ) : view === "prep" ? (
          <PrepShell />
        ) : (
          <>
            <ChannelList activeId={activeId} onPick={handlePick} />
            <ChatThread topic={topic} questionAsked={question} />
            <ParticipantsRail />
          </>
        )}
      </div>
    </div>
  );
}

function NavBtn({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-md transition ${
        active
          ? "bg-white/10 text-white"
          : "text-white/60 hover:text-white hover:bg-white/5"
      }`}
    >
      {children}
    </button>
  );
}
