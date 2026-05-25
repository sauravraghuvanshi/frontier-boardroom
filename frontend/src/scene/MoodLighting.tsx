import { useStore } from "../store";

const MOOD_COLORS: Record<string, string> = {
  cordial: "#7dd3fc",
  debating: "#fcd34d",
  heated: "#f87171",
  converging: "#a7f3d0",
  resolved: "#86efac",
};

export function MoodLighting() {
  const label = useStore((s) => s.mood.label);
  const value = useStore((s) => s.mood.value);
  const color = MOOD_COLORS[label] || "#7dd3fc";
  const intensity = 0.8 + value * 1.4;
  return (
    <>
      <ambientLight intensity={0.35} color={color} />
      <directionalLight castShadow intensity={intensity} position={[3, 5, 2]} color={color} />
      <pointLight intensity={0.6} position={[-3, 2, -2]} color={color} />
    </>
  );
}
