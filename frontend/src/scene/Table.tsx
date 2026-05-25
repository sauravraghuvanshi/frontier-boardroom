export function Table() {
  return (
    <group position={[0, 0, 0]}>
      <mesh receiveShadow position={[0, -0.05, 0]}>
        <cylinderGeometry args={[1.6, 1.6, 0.1, 64]} />
        <meshStandardMaterial color="#1d2330" roughness={0.35} metalness={0.2} />
      </mesh>
      <mesh position={[0, -0.55, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 0.9, 16]} />
        <meshStandardMaterial color="#0e1118" />
      </mesh>
      <mesh receiveShadow position={[0, -1.05, 0]}>
        <boxGeometry args={[10, 0.05, 10]} />
        <meshStandardMaterial color="#070a10" />
      </mesh>
    </group>
  );
}
