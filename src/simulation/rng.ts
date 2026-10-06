/** Deterministic PRNG (mulberry32) and stateless hash noise. No Math.random anywhere in the sim. */
export class Rng {
  private s: number;
  constructor(seed: number) {
    this.s = seed >>> 0 || 0x9e3779b9;
  }
  next(): number {
    let t = (this.s = (this.s + 0x6d2b79f5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  range(a: number, b: number): number {
    return a + (b - a) * this.next();
  }
  int(a: number, bInclusive: number): number {
    return a + Math.floor(this.next() * (bInclusive - a + 1));
  }
  /** Approximately normal(0,1) (sum of 3 uniforms). */
  gauss(): number {
    return (this.next() + this.next() + this.next() - 1.5) * 2;
  }
  /** Random point in unit disc → writes into out[0], out[1]. */
  disc(out: Float64Array): void {
    const r = Math.sqrt(this.next());
    const a = this.next() * Math.PI * 2;
    out[0] = r * Math.cos(a);
    out[1] = r * Math.sin(a);
  }
}

/** Integer hash → [0,1). */
export function hash2(i: number, j: number, seed = 0): number {
  let h = Math.imul(i | 0, 0x27d4eb2d) ^ Math.imul(j | 0, 0x165667b1) ^ Math.imul(seed | 0, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

/** Smooth 2D value noise in [0,1]. */
export function valueNoise(x: number, y: number, seed = 0): number {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const xf = x - xi;
  const yf = y - yi;
  const u = xf * xf * (3 - 2 * xf);
  const v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi, seed);
  const b = hash2(xi + 1, yi, seed);
  const c = hash2(xi, yi + 1, seed);
  const d = hash2(xi + 1, yi + 1, seed);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

/** 3-octave fbm in [0,1]. */
export function fbm(x: number, y: number, seed = 0): number {
  return (valueNoise(x, y, seed) * 0.57 + valueNoise(x * 2.03, y * 2.03, seed + 17) * 0.29 + valueNoise(x * 4.1, y * 4.1, seed + 31) * 0.14);
}
