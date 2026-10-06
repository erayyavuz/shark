/**
 * Simulation constants (normalized units, not grams). See DirtSimulation.ts header for the model.
 *
 * MASS WEIGHTS — "weighted visual mess units" (MU). Chosen so that one visible thing of each kind
 * contributes a comparable amount to the progress figure (collected / added):
 *   dust   : 0.5 MU per cm² of floor at density 1.0  (default 2.73 mm cell at density 1 ≈ 0.037 MU)
 *   hair   : 0.15 MU per cm of strand length          (10 cm strand = 1.5 MU), split evenly over its points
 *   pet    : 0.06 MU per fiber                        (40-fiber clump ≈ 2.4 MU)
 *   crumbs : 0.4 + 2·s² MU, s = crumb size in cm      (5 mm ≈ 0.9 MU, 10 mm = 2.4 MU)
 */
export const DUST_MASS_PER_CM2 = 0.5;
export const HAIR_MASS_PER_CM = 0.15;
export const PET_FIBER_MASS = 0.06;
export const crumbMass = (sizeM: number) => {
  const s = sizeM * 100;
  return 0.4 + 2 * s * s;
};

/**
 * Authoritative dust field resolution: the longer play-area side gets 512 cells and the other side is
 * scaled to keep cells square (default 1.4 × 1.0 m area → 512 × 366, ~2.73 mm cells; the brief's
 * "512²" scaled to the non-square area). Quality never changes this; balanced only downsamples the
 * render texture by 2 (256 × 183).
 */
export const DUST_FIELD_W = 512;

/**
 * BUDGETS (brief §9.7). The LOGICAL caps are the high-tier values for every quality tier, so a quality
 * change can never delete or hide logical mess. Balanced simplifies representation only
 * (dust texture resolution, crumb mesh detail, no crumb shadows, fewer ribbon subdivisions, motes cap).
 */
export const MAX_CRUMBS = 1000;
export const MAX_STRANDS = 100;
export const MAX_CLUMPS = 45;
/** Visual-only, so the cap follows the tier. */
export const MAX_MOTES = 120;
export const MOTES_BALANCED = 40;
/** Dust budget: remaining dust mass cap (≈ 2400 cm² fully dense ≈ 12.5 % of the play area). */
export const DUST_MASS_CAP = 1200;

export const MAX_STRAND_POINTS = 13; // 6–12 segments
export const MAX_FIBERS_PER_CLUMP = 56;

/** Fixed internal step and catch-up cap. */
export const SIM_DT = 1 / 120;
export const MAX_CATCHUP_STEPS = 8;
/** Swept pickup substep limits. */
export const SUBSTEP_DEPTH_FRACTION = 0.4;
/** 1.5° keeps the mid-yaw approximation error at the shell corners below ~2 mm. */
export const SUBSTEP_MAX_YAW = (1.5 * Math.PI) / 180;
/** A pose jump longer than this is treated as a teleport (only the end pose is evaluated). */
export const TELEPORT_DISTANCE = 0.6;
/** Narrow attraction band outside the intake rectangle (not a force field). */
export const ATTRACT_BAND = 0.02;
/** Max ± jitter (m) of the per-cell intake edge, for slight physical irregularity of the cleaned track. */
export const EDGE_JITTER = 0.0012;
/** Placement inset from the play-area edge for user placement. */
export const REACH_MARGIN = 0.02;
/** Long-hair feed speed into the intake (m/s). */
export const HAIR_FEED_SPEED = 0.7;
