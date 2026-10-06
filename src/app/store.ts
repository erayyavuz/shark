import { create } from 'zustand';
import type { ActiveTool, DirtDensity, DirtKind, ExperienceState, SurfaceKind } from '../contracts/types';

/**
 * UI-facing state only. Written on transitions / discrete changes, never per frame.
 * The imperative Experience controller owns simulation, rig and camera.
 */
export interface UIState {
  phase: ExperienceState;
  tool: ActiveTool;
  dirtKind: DirtKind;
  density: DirtDensity;
  surface: SurfaceKind;
  sound: boolean;
  /** Lighting mode: studio day light or a dark room lit by the product's own LEDs + soft practicals. */
  night: boolean;
  drawerOpen: boolean;
  allClear: boolean;
  detecting: boolean;
  controlsVisible: boolean;
  strokeActive: boolean;
  budgetFull: boolean;
  /** Loading: bytes loaded and total if known (null = unknown). */
  loadedBytes: number;
  totalBytes: number | null;
  errorMessage: string | null;
  unsupportedReason: string | null;
  reducedMotion: boolean;
  set: (patch: Partial<UIState>) => void;
}

export const useUI = create<UIState>((set) => ({
  phase: 'loading',
  tool: 'clean',
  dirtKind: 'mixed',
  density: 'medium',
  surface: 'oak',
  sound: false, // muted by default (brief §6.4)
  night: false,
  drawerOpen: false,
  allClear: false,
  detecting: false,
  controlsVisible: false,
  strokeActive: false,
  budgetFull: false,
  loadedBytes: 0,
  totalBytes: null,
  errorMessage: null,
  unsupportedReason: null,
  reducedMotion: typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches,
  set: (patch) => set(patch),
}));
