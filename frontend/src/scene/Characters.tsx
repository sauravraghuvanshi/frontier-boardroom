import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { Role } from "../store";
import { useStore } from "../store";

type Seat = { role: Role; angle: number; color: string };

const SEATS: Seat[] = [
  { role: "CEO", angle: 0, color: "#7dd3fc" },
  { role: "CFO", angle: (Math.PI * 2) / 5, color: "#fcd34d" },
  { role: "CMO", angle: (Math.PI * 4) / 5, color: "#f472b6" },
  { role: "CTO", angle: (Math.PI * 6) / 5, color: "#86efac" },
  { role: "Legal", angle: (Math.PI * 8) / 5, color: "#fda4af" },
];

function seatPosition(angle: number, r = 1.9): [number, number, number] {
  return [Math.sin(angle) * r, 0.55, Math.cos(angle) * r];
}

function Character({ seat }: { seat: Seat }) {
  const ref = useRef<THREE.Group>(null!);
  const speaking = useStore((s) => s.speakingAgent === seat.role);
  const mood = useStore((s) => s.mood.label);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime();
    // idle bob
    ref.current.position.y = 0.55 + Math.sin(t * 1.2 + seat.angle) * 0.01;
    // lean forward when speaking
    const targetTilt = speaking ? -0.18 : 0;
    ref.current.rotation.x = THREE.MathUtils.lerp(ref.current.rotation.x, targetTilt, 0.08);
    // mood-driven head shake on heated
    if (mood === "heated" && speaking) {
      ref.current.rotation.y = Math.sin(t * 6) * 0.06;
    } else {
      ref.current.rotation.y = THREE.MathUtils.lerp(ref.current.rotation.y, 0, 0.1);
    }
  });

  const [x, y, z] = seatPosition(seat.angle);
  return (
    <group ref={ref} position={[x, y, z]} rotation={[0, -seat.angle, 0]}>
      {/* Placeholder body — swap with .glb avatar via useGLTF when assets land.
          TODO(plan): load /avatars/{role}.glb */}
      <mesh castShadow>
        <capsuleGeometry args={[0.22, 0.5, 4, 12]} />
        <meshStandardMaterial color={seat.color} emissive={speaking ? seat.color : "#000"} emissiveIntensity={speaking ? 0.4 : 0} />
      </mesh>
      <mesh position={[0, 0.45, 0]} castShadow>
        <sphereGeometry args={[0.18, 24, 24]} />
        <meshStandardMaterial color="#f3d6b5" />
      </mesh>
      {/* Mouth proxy for visemes */}
      <mesh position={[0, 0.4, 0.17]} scale={speaking ? [0.05, 0.025, 0.01] : [0.05, 0.008, 0.01]}>
        <boxGeometry />
        <meshStandardMaterial color="#3b1f1f" />
      </mesh>
    </group>
  );
}

export function Characters() {
  return (
    <group>
      {SEATS.map((s) => (
        <Character key={s.role} seat={s} />
      ))}
    </group>
  );
}

export const SEAT_ANGLES: Record<Role, number> = Object.fromEntries(
  SEATS.map((s) => [s.role, s.angle]),
) as Record<Role, number>;
