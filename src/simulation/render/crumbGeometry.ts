import * as THREE from 'three';
import { mergeVertices } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/**
 * Procedural crumb library: six irregular, softly beveled shapes built from displaced icosahedra.
 * Unit size: ~1 across (instance scale = crumb diameter in meters). Lowest point at y = 0.
 * detail 1 (80 tris) on high, 0 (20 tris) on balanced.
 */
const SHAPES: { scale: [number, number, number]; amp: number; freq: number; flatTop: number }[] = [
  { scale: [1.0, 0.72, 0.9], amp: 0.18, freq: 2.2, flatTop: 1 }, // chunky
  { scale: [1.1, 0.4, 0.85], amp: 0.12, freq: 2.6, flatTop: 1 }, // flake
  { scale: [1.4, 0.58, 0.7], amp: 0.15, freq: 2.0, flatTop: 1 }, // elongated
  { scale: [1.0, 0.75, 1.0], amp: 0.2, freq: 2.4, flatTop: 0.18 }, // wedge / cut face
  { scale: [0.9, 0.78, 0.9], amp: 0.08, freq: 1.8, flatTop: 1 }, // roundish
  { scale: [1.0, 0.62, 0.95], amp: 0.28, freq: 3.4, flatTop: 1 }, // crusty
];

export const CRUMB_SHAPE_COUNT = SHAPES.length;

function lumpy(x: number, y: number, z: number, f: number, seed: number): number {
  return (
    Math.sin(x * f * 3.1 + seed) * Math.sin(y * f * 2.7 + seed * 1.7) * Math.sin(z * f * 3.3 + seed * 0.6) * 0.6 +
    Math.sin(x * f * 6.3 + seed * 2.1 + y * 4.0) * 0.25 +
    Math.sin(z * f * 5.1 - seed + x * 3.0) * 0.15
  );
}

export function makeCrumbGeometry(shape: number, detail: number): THREE.BufferGeometry {
  const s = SHAPES[shape % SHAPES.length];
  let g: THREE.BufferGeometry = new THREE.IcosahedronGeometry(0.5, detail);
  g.deleteAttribute('normal');
  g.deleteAttribute('uv');
  g = mergeVertices(g);
  const pos = g.getAttribute('position') as THREE.BufferAttribute;
  const seed = 1.3 + shape * 2.17;
  let minY = Infinity;
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);
    const len = Math.hypot(x, y, z) || 1;
    const nx = x / len;
    const ny = y / len;
    const nz = z / len;
    const r = 0.5 * (1 + s.amp * lumpy(nx, ny, nz, s.freq, seed));
    x = nx * r * s.scale[0];
    y = ny * r * s.scale[1];
    z = nz * r * s.scale[2];
    if (y > s.flatTop * s.scale[1] * 0.5) y = s.flatTop * s.scale[1] * 0.5 + (y - s.flatTop * s.scale[1] * 0.5) * 0.25;
    // flatter underside so crumbs rest on the floor
    if (y < 0) y *= 0.8;
    pos.setXYZ(i, x, y, z);
    if (y < minY) minY = y;
  }
  g.translate(0, -minY, 0);
  g.computeVertexNormals();
  g.computeBoundingSphere();
  return g;
}
