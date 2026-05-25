/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
      colors: {
        boardroom: {
          bg: "#0a0b14",
          panel: "#11131f",
          rail: "#11131f",
          accent: "#6366f1",
          accentSoft: "#818cf8",
          active: "#4338ca",
          decision: "#fbbf24",
          cyan: "#22d3ee",
        },
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(251,191,36,0.45)" },
          "50%": { boxShadow: "0 0 18px 4px rgba(251,191,36,0.35)" },
        },
        slideInLeft: {
          "0%": { transform: "translateX(-4px)", opacity: 0 },
          "100%": { transform: "translateX(0)", opacity: 1 },
        },
        gradientShift: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
      animation: {
        "pulse-glow": "pulseGlow 2.4s ease-in-out infinite",
        "slide-in-left": "slideInLeft 180ms ease-out",
        "gradient-shift": "gradientShift 10s ease infinite",
      },
    },
  },
  plugins: [],
};
