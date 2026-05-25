import { Logo } from "../branding/Logo";
import { COMPANY } from "../branding/company";

// Profile assembled from backend/data/sample_seed numbers. Single source of
// truth lives in branding/company.ts so a CFO-style edit is one-line.
export function AboutPage() {
  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-[#0a0b14] via-[#11131f] to-[#1e1b4b] text-white">
      <div className="max-w-4xl mx-auto px-8 py-10">
        {/* Hero */}
        <div className="flex items-center gap-4 mb-10">
          <Logo size={64} />
          <div>
            <div className="text-3xl font-semibold tracking-tight">
              {COMPANY.name}
            </div>
            <div className="text-sm text-white/60 mt-1">{COMPANY.tagline}</div>
            <div className="text-[11px] uppercase tracking-widest text-cyan-300/80 mt-2">
              {COMPANY.stage} · HQ {COMPANY.hq} · Founded {COMPANY.founded}
            </div>
          </div>
        </div>

        <p className="text-white/80 leading-relaxed text-[15px] mb-12 max-w-3xl">
          {COMPANY.blurb}
        </p>

        {/* Financials */}
        <Section title="Financials">
          <Grid>
            <Stat label="Cash on hand" value={COMPANY.financials.cash} sub={COMPANY.financials.cashAsOf} />
            <Stat label="Burn / month" value={COMPANY.financials.burnPerMonth} />
            <Stat label="Runway" value={`${COMPANY.financials.runwayMonths} mo`} sub={COMPANY.financials.runwayWithSEA} />
            <Stat label="ARR (India)" value={COMPANY.financials.arrIndia} />
          </Grid>
          <div className="mt-4 text-sm text-white/70">
            Active term sheet: <span className="text-amber-300">{COMPANY.financials.termSheet}</span>
          </div>
        </Section>

        {/* People */}
        <Section title="People">
          <div className="text-sm text-white/70 mb-3">
            <span className="text-white text-lg font-semibold">{COMPANY.people.headcountToday}</span> employees globally today.
          </div>
          <Grid>
            {COMPANY.people.breakdown.map((b) => (
              <Stat key={b.region} label={b.region} value={`${b.count}`} />
            ))}
          </Grid>
          <div className="mt-5 text-sm text-white/70">
            2026 hiring plan: <span className="text-cyan-300">+{COMPANY.people.hiring2026.india} India</span>,{" "}
            <span className="text-cyan-300">+{COMPANY.people.hiring2026.sea} SEA</span>,{" "}
            <span className="text-cyan-300">+{COMPANY.people.hiring2026.us} US</span>.
            <div className="text-[12px] text-white/40 mt-1">{COMPANY.people.hiring2026.note}</div>
          </div>
        </Section>

        {/* Markets */}
        <Section title="Markets">
          <ul className="space-y-3">
            {COMPANY.markets.map((m) => (
              <li
                key={m.name}
                className="bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3"
              >
                <div className="text-white font-medium text-sm">{m.name}</div>
                <div className="text-white/60 text-[13px] mt-0.5">{m.detail}</div>
              </li>
            ))}
          </ul>
        </Section>

        {/* Team */}
        <Section title="Virtual C-Suite">
          <Grid>
            {COMPANY.team.map((t) => (
              <div
                key={t.role}
                className="bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3"
              >
                <div className="text-[11px] uppercase tracking-wider text-indigo-300">
                  {t.role}
                </div>
                <div className="text-white/80 text-sm mt-1">{t.focus}</div>
              </div>
            ))}
          </Grid>
        </Section>

        {/* Stack */}
        <Section title="Powered by">
          <ul className="text-sm text-white/70 space-y-1.5">
            {COMPANY.stack.map((s) => (
              <li key={s} className="flex gap-2">
                <span className="text-cyan-400">▸</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
          <div className="text-[11px] text-white/40 mt-6">
            {COMPANY.productByline}. Numbers above align with the briefing
            documents the agents cite live in debate.
          </div>
        </Section>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-10">
      <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-3">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-2 md:grid-cols-3 gap-3">{children}</div>;
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="bg-white/[0.03] border border-white/10 rounded-lg px-4 py-3">
      <div className="text-[11px] uppercase tracking-wider text-white/40">{label}</div>
      <div className="text-white text-lg font-semibold mt-1">{value}</div>
      {sub && <div className="text-[11px] text-white/50 mt-0.5">{sub}</div>}
    </div>
  );
}
