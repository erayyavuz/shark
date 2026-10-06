/**
 * Product constants. Target SKU (user-selected 2026-10-05, from the user's own video): IP3251EUT — Shark PowerDetect
 * Clean & Empty (TR). Stick 1158 H × 263 W × 393 D mm (= IP1251 hardware); system with dock 1177 × 263 × 472 mm
 * (see PRODUCT_REFERENCE_IP3251.md, TECHNICAL_REFERENCE_IP3251.md).
 */
import type { NozzleGeometry } from '../contracts/rig';

export const PRODUCT = {
  sku: 'IP3251EUT',
  name: 'Shark PowerDetect Clean & Empty',
  overallHeight: 1.177,
  overallWidth: 0.263,
  overallDepth: 0.472,
  /** docked pose: the rear wheels stand on the 13.5 mm dock base plate and the nose stays on the floor, so the
   * stick tips ~5° nose-down about the front contact line (dock agent, video frame JCGX t0020.3) */
  dockedTilt: 0.087,
} as const;

/**
 * Nozzle pickup geometry in FloorHead-local meters. Initial values; the asset build writes
 * measured values into assets/manifest.json and public/models/rig.json, which override these at load.
 */
export const DEFAULT_NOZZLE: NozzleGeometry = {
  intakeWidth: 0.232,
  intakeZMin: -0.045,
  intakeZMax: 0.065,
  shellWidth: 0.263,
  shellZMin: -0.13,
  shellZMax: 0.09,
};
