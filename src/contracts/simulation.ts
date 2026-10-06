import type { DirtDensity, DirtKind, QualityTier, SurfaceKind } from './types';
import type { HeadPose, PlayArea } from './world';
import type { NozzleGeometry } from './rig';

export type BaseDirtKind = Exclude<DirtKind, 'mixed'>;

export interface MassAccounting {
  added: number;
  collected: number;
  remaining: number;
}

export interface PickupEvent {
  kind: BaseDirtKind;
  mass: number;
}

/**
 * Tick order per frame (lead-owned loop):
 *   1. input -> InputTarget
 *   2. motion controller -> HeadPose (fixed steps)
 *   3. sim.step(dt, prevPose, pose, pickupActive)   (fixed 1/120 s substeps internally, capped catch-up)
 *   4. renderers.sync()  (reads sim state; no React state)
 *   5. render
 */
export interface DirtSimulationAPI {
  readonly area: PlayArea;
  readonly nozzle: NozzleGeometry;
  /** Single tap scatter around a point. Returns mass actually added (0 when budget full). */
  addScatter(kind: DirtKind, density: DirtDensity, x: number, z: number): number;
  /** Paint along a stroke segment; contribution is by distance travelled + bounded dt, not frame count. */
  addStroke(kind: DirtKind, density: DirtDensity, x0: number, z0: number, x1: number, z1: number, dt: number): number;
  /** Bounded mixed preset placed in reachable space (keeps existing mess, subject to caps). */
  addPreset(seed?: number): number;
  /** Small intro patch in front of a head pose. */
  addIntroPatch(pose: HeadPose): number;
  clearFloor(): void;
  /** Advance; pickup only if pickupActive. Uses the swept path prev->next including yaw. */
  step(dt: number, prev: HeadPose, next: HeadPose, pickupActive: boolean): void;
  getAccounting(): MassAccounting;
  /** Weighted remaining fraction relative to added (0 when nothing added). */
  getRemainingFraction(): number;
  /** Local dirt density (0..1) in front of/under the head; drives motor/audio intensity. */
  getLocalDensity(pose: HeadPose): number;
  /** Drain pickup events since last call (for audio transients/feedback). */
  drainPickups(): PickupEvent[];
  /** Representation-only change; never alters logical mass, IDs or positions. */
  setQuality(tier: QualityTier): void;
  setSurface(surface: SurfaceKind): void;
  /** True when budget for a kind is exhausted. */
  isFull(kind: BaseDirtKind): boolean;
}
