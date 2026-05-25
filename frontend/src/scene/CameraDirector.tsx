import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { useStore } from "../store";
import { SEAT_ANGLES } from "./Characters";

export function CameraDirector() {
  const last = useRef<string | null>(null);
  useFrame(({ camera, clock }) => {
    const speaker = useStore.getState().speakingAgent;
    const mood = useStore.getState().mood.label;
    let target = new THREE.Vector3(0, 0.55, 0);
    let pos = new THREE.Vector3(0, 1.6, 4.5);

    if (speaker) {
      const angle = SEAT_ANGLES[speaker];
      target = new THREE.Vector3(Math.sin(angle) * 1.9, 0.7, Math.cos(angle) * 1.9);
      pos = new THREE.Vector3(Math.sin(angle) * 3.6, 1.5, Math.cos(angle) * 3.6);
    }

    // heated -> mild handheld shake
    if (mood === "heated") {
      const t = clock.getElapsedTime();
      pos.x += Math.sin(t * 11) * 0.03;
      pos.y += Math.cos(t * 9) * 0.02;
    }

    camera.position.lerp(pos, 0.045);
    camera.lookAt(target);
    last.current = speaker;
  });
  return null;
}
