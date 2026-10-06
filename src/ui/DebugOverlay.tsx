import { useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';

/** Development-only renderer counters (?debug). Absent from the default experience. */
export function DebugProbe({ target }: { target: HTMLElement | null }) {
  const { gl } = useThree();
  const acc = useRef({ t: 0, n: 0, worst: 0, frames: [] as number[] });
  useFrame((_, dt) => {
    const a = acc.current;
    a.t += dt;
    a.n++;
    a.frames.push(dt * 1000);
    if (a.frames.length > 240) a.frames.shift();
    if (a.t > 0.5 && target) {
      const s = [...a.frames].sort((x, y) => x - y);
      const p95 = s[Math.floor(s.length * 0.95)] ?? 0;
      const i = gl.info;
      target.textContent = `fps ${(a.n / a.t).toFixed(0)}  p95 ${p95.toFixed(1)}ms  calls ${i.render.calls}  tris ${(i.render.triangles / 1000).toFixed(0)}k  geo ${i.memory.geometries}  tex ${i.memory.textures}  dpr ${gl.getPixelRatio()}`;
      a.t = 0;
      a.n = 0;
    }
  });
  return null;
}
