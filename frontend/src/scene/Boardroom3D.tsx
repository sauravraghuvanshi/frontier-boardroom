import { Canvas } from "@react-three/fiber";
import { Environment, OrbitControls } from "@react-three/drei";
import { Suspense } from "react";
import { Characters } from "./Characters";
import { CameraDirector } from "./CameraDirector";
import { MoodLighting } from "./MoodLighting";
import { Table } from "./Table";

export function Boardroom3D() {
  return (
    <Canvas shadows camera={{ position: [0, 1.6, 4.5], fov: 42 }}>
      <Suspense fallback={null}>
        <MoodLighting />
        <Environment preset="city" />
        <Table />
        <Characters />
        <CameraDirector />
        <OrbitControls enablePan={false} maxDistance={9} minDistance={2.5} />
      </Suspense>
    </Canvas>
  );
}
