type Props = {
  size?: number;
  className?: string;
};

// Five satellite nodes (one per C-suite role) around a central core.
// Subtle indigo→cyan gradient, glow on hover via parent CSS.
export function Logo({ size = 28, className }: Props) {
  const r = size / 2;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Contoso AI Boardroom logo"
    >
      <defs>
        <radialGradient id="core" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#a5b4fc" />
          <stop offset="100%" stopColor="#4338ca" />
        </radialGradient>
        <linearGradient id="ring" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.0" />
          <stop offset="50%" stopColor="#818cf8" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {/* outer ring */}
      <circle
        cx={r * 2}
        cy={r * 2}
        r={28}
        fill="none"
        stroke="url(#ring)"
        strokeWidth="1.5"
      />

      {/* connector lines from core to each satellite */}
      {satellites.map(([cx, cy], i) => (
        <line
          key={`l${i}`}
          x1="32"
          y1="32"
          x2={cx}
          y2={cy}
          stroke="#4338ca"
          strokeWidth="1"
          strokeOpacity="0.55"
        />
      ))}

      {/* satellites */}
      {satellites.map(([cx, cy], i) => (
        <circle key={`s${i}`} cx={cx} cy={cy} r="3.6" fill="#a5b4fc" />
      ))}

      {/* core */}
      <circle cx="32" cy="32" r="8" fill="url(#core)" />
      <circle cx="32" cy="32" r="3" fill="#e0e7ff" />
    </svg>
  );
}

// Five points on a circle radius 22 around (32,32), starting at top.
const satellites: ReadonlyArray<[number, number]> = (() => {
  const out: Array<[number, number]> = [];
  const R = 22;
  for (let i = 0; i < 5; i++) {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
    out.push([+(32 + R * Math.cos(a)).toFixed(2), +(32 + R * Math.sin(a)).toFixed(2)]);
  }
  return out;
})();
