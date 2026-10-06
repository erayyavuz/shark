import type { QualityTier } from '../contracts/types';
import type { PlayArea } from '../contracts/world';
import { PLAY_AREA } from '../contracts/world';

/** Initial tier guess; the PerfGovernor then adapts pixel ratio / shadows with hysteresis. */
export function detectTier(): QualityTier {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const coarse = matchMedia('(pointer: coarse)').matches;
  const small = Math.min(screen.width, screen.height) < 700;
  if (coarse || small || (nav.deviceMemory ?? 8) <= 4 || (nav.hardwareConcurrency ?? 8) <= 4) return 'balanced';
  return 'high';
}

export const DPR_STEPS = [1, 1.25, 1.5, 1.75, 2];

export function initialDpr(tier: QualityTier): number {
  const cap = tier === 'high' ? 2 : 1.5;
  return Math.min(cap, window.devicePixelRatio || 1);
}

/** Portrait screens get a narrower, deeper play rectangle so dirt stays readable. */
export const PLAY_AREA_PORTRAIT: PlayArea = { minX: -0.45, maxX: 0.45, minZ: -0.55, maxZ: 0.55 };

export function playAreaFor(aspect: number): PlayArea {
  return aspect < 0.85 ? PLAY_AREA_PORTRAIT : PLAY_AREA;
}
