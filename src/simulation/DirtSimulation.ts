/**
 * Authoritative dirt simulation (brief §9). Pure TypeScript, no DOM, deterministic (seeded PRNG).
 *
 * Model summary
 * - Dust: CPU Float32 density field (longest side 512 cells, square ~2.7 mm cells over the play
 *   area) + a tone (hue variation) channel. Always full resolution; quality affects only the renderer.
 * - Long hair: strands of 6–12 segments (≤13 points), 3–15 cm. Capture when a point enters the intake
 *   rectangle while pickup is active; ingested points leave the strand, neighbouring points become
 *   leaders that are fed toward the intake attach point at HAIR_FEED_SPEED; the rest of the chain
 *   follows through a pull-only segment-length constraint, so uncaptured parts stay until pulled.
 * - Pet hair: clumps of ~38–56 short fibers (1–3 cm). Near the intake (attraction band) the clump loosens
 *   and elongates; once a fiber is ingested the clump is captured and its fibers collapse into the intake.
 * - Crumbs: stable-ID instances, 2–10 mm, shape index 0..5, damped settle bounce, small hop/roll and
 *   acceleration toward the intake inside the narrow attraction band, collected when their centre is
 *   inside the intake rectangle. Crumbs inside the outer shell footprint are flagged `underShell`
 *   (renderers hide them so nothing pokes through the cover).
 * - Motes: sparse visual-only airborne specks spawned in proportion to dust actually removed.
 *
 * Pickup is evaluated along the swept pose path prev→next (x, z and yaw interpolated) in substeps of at
 * most 40 % of the intake depth and 3° of yaw. Pickup geometry is idempotent (a cell/item inside the
 * footprint is removed regardless of how many substeps saw it), so results are frame-rate independent.
 * Dynamics (bounce, attraction, feeding, motes) run on fixed 1/120 s steps with ≤ 8 catch-up steps.
 *
 * Accounting: per-kind running sums in float64. Every removal adds exactly the removed mass to
 * `collected`; `remaining` is the running sum of stored mass (dust deltas are computed from the actual
 * float32 values written). Invariant |added − collected − remaining| ≤ 1e-6 · max(1, added); tests also
 * recompute `remaining` from the raw state. clearFloor zeroes all three; caps never evict.
 */
import type { DirtSimulationAPI, BaseDirtKind, MassAccounting, PickupEvent } from '../contracts/simulation';
import type { DirtDensity, DirtKind, QualityTier, SurfaceKind } from '../contracts/types';
import type { HeadPose, PlayArea } from '../contracts/world';
import { PLAY_AREA, headLocalToWorld } from '../contracts/world';
import type { NozzleGeometry } from '../contracts/rig';
import { DEFAULT_NOZZLE } from '../config/product';
import { Rng, fbm, hash2 } from './rng';
import { SpatialHash } from './SpatialHash';
import {
  ATTRACT_BAND,
  DUST_FIELD_W,
  DUST_MASS_CAP,
  DUST_MASS_PER_CM2,
  EDGE_JITTER,
  HAIR_FEED_SPEED,
  HAIR_MASS_PER_CM,
  MAX_CATCHUP_STEPS,
  MAX_CLUMPS,
  MAX_CRUMBS,
  MAX_FIBERS_PER_CLUMP,
  MAX_MOTES,
  MAX_STRANDS,
  MAX_STRAND_POINTS,
  MOTES_BALANCED,
  PET_FIBER_MASS,
  REACH_MARGIN,
  SIM_DT,
  SUBSTEP_DEPTH_FRACTION,
  SUBSTEP_MAX_YAW,
  TELEPORT_DISTANCE,
  crumbMass,
} from './constants';

export interface DirtSimulationOptions {
  area?: PlayArea;
  nozzle?: NozzleGeometry;
  quality?: QualityTier;
  seed?: number;
}

const K_DUST = 0;
const K_HAIR = 1;
const K_PET = 2;
const K_CRUMBS = 3;
const KIND_NAMES: readonly BaseDirtKind[] = ['dust', 'hair', 'pet', 'crumbs'];

/** Crumb state flags. */
export const CRUMB_SETTLING = 1;
export const CRUMB_ATTRACTED = 2;
export const CRUMB_HOPPED = 4;
export const CRUMB_UNDER_SHELL = 8;

const DENSITY_MULT: Record<DirtDensity, number> = { light: 0.5, medium: 1, heavy: 1.8 };
const GRAVITY = 9.81;

const HAIR_PALETTE = [
  [0.07, 0.055, 0.05],
  [0.16, 0.1, 0.065],
  [0.3, 0.19, 0.11],
  [0.42, 0.25, 0.13],
  [0.58, 0.45, 0.29],
  [0.5, 0.49, 0.47],
] as const;
const HAIR_PALETTE_W = [0.25, 0.28, 0.2, 0.1, 0.11, 0.06];

/** Realistic dog/cat hair mix (sRGB): cream, tan, light grey, white, grey-brown, dark brown, near-black. */
const PET_PALETTE = [
  [0.84, 0.77, 0.63],
  [0.66, 0.5, 0.33],
  [0.66, 0.65, 0.63],
  [0.92, 0.9, 0.86],
  [0.47, 0.42, 0.36],
  [0.26, 0.18, 0.12],
  [0.1, 0.085, 0.075],
] as const;
const PET_PALETTE_W = [0.17, 0.18, 0.13, 0.1, 0.14, 0.15, 0.13];

const CRUMB_PALETTE = [
  [0.78, 0.6, 0.36], // toast tan
  [0.62, 0.42, 0.22], // crust brown
  [0.86, 0.7, 0.42], // golden
  [0.45, 0.29, 0.15], // dark crust
  [0.9, 0.82, 0.62], // pale crumb
  [0.7, 0.5, 0.28],
] as const;

function wrapAngle(a: number): number {
  while (a > Math.PI) a -= 2 * Math.PI;
  while (a < -Math.PI) a += 2 * Math.PI;
  return a;
}

function pickWeighted(rng: Rng, w: readonly number[]): number {
  let t = rng.next();
  for (let i = 0; i < w.length; i++) {
    t -= w[i];
    if (t <= 0) return i;
  }
  return w.length - 1;
}

export class DirtSimulation implements DirtSimulationAPI {
  readonly area: PlayArea;
  readonly nozzle: NozzleGeometry;
  quality: QualityTier;
  surface: SurfaceKind = 'oak';

  // ---------------- dust ----------------
  /** Field resolution: the longer area side gets DUST_FIELD_W cells, the other keeps cells ~square. */
  readonly fieldW: number;
  readonly fieldH: number;
  readonly cellW: number;
  readonly cellH: number;
  /** Density 0..1 per cell, row-major, row j ↔ z (row 0 = minZ), column i ↔ x (col 0 = minX). */
  readonly dust: Float32Array;
  /** Hue variation 0..1 per cell (meaningful where dust > 0). */
  readonly dustTone: Float32Array;
  private readonly rowMass: Float64Array;
  private readonly cellMass: number;
  private dirtyX0 = 0;
  private dirtyY0 = 0;
  private dirtyX1 = -1;
  private dirtyY1 = -1;
  dustVersion = 0;

  // ---------------- crumbs ----------------
  readonly crumbAlive = new Uint8Array(MAX_CRUMBS);
  readonly crumbFlags = new Uint8Array(MAX_CRUMBS);
  readonly crumbId = new Uint32Array(MAX_CRUMBS);
  readonly crumbX = new Float32Array(MAX_CRUMBS);
  readonly crumbZ = new Float32Array(MAX_CRUMBS);
  /** Height of the crumb's lowest point above the floor (bounce/hop). */
  readonly crumbY = new Float32Array(MAX_CRUMBS);
  readonly crumbVX = new Float32Array(MAX_CRUMBS);
  readonly crumbVZ = new Float32Array(MAX_CRUMBS);
  readonly crumbVY = new Float32Array(MAX_CRUMBS);
  readonly crumbYaw = new Float32Array(MAX_CRUMBS);
  /** Accumulated roll angle and the world-XZ direction (radians) of the roll motion. */
  readonly crumbRoll = new Float32Array(MAX_CRUMBS);
  readonly crumbRollDir = new Float32Array(MAX_CRUMBS);
  /** Diameter in meters. */
  readonly crumbSize = new Float32Array(MAX_CRUMBS);
  readonly crumbShape = new Uint8Array(MAX_CRUMBS);
  /** sRGB colour, 3 floats per crumb. */
  readonly crumbColor = new Float32Array(MAX_CRUMBS * 3);
  private readonly crumbMassArr = new Float64Array(MAX_CRUMBS);
  crumbCount = 0;
  /** Slots [0, crumbHigh) may be alive. */
  crumbHigh = 0;
  crumbVersion = 0;
  private readonly crumbFree = new Int32Array(MAX_CRUMBS);
  private crumbFreeN = 0;

  // ---------------- long hair ----------------
  readonly strandAlive = new Uint8Array(MAX_STRANDS);
  readonly strandId = new Uint32Array(MAX_STRANDS);
  readonly strandN = new Uint8Array(MAX_STRANDS);
  readonly strandSeg = new Float32Array(MAX_STRANDS);
  readonly strandWidth = new Float32Array(MAX_STRANDS);
  readonly strandColor = new Float32Array(MAX_STRANDS * 3);
  readonly strandCaptured = new Uint8Array(MAX_STRANDS);
  private readonly strandAttachLx = new Float32Array(MAX_STRANDS);
  private readonly strandPointMass = new Float64Array(MAX_STRANDS);
  /** Points: index s * MAX_STRAND_POINTS + p. */
  readonly strandPX = new Float32Array(MAX_STRANDS * MAX_STRAND_POINTS);
  readonly strandPZ = new Float32Array(MAX_STRANDS * MAX_STRAND_POINTS);
  /** 1 while the point is still on the floor (not ingested, strand alive, p < n). */
  readonly strandPointLive = new Uint8Array(MAX_STRANDS * MAX_STRAND_POINTS);
  strandCount = 0;
  hairVersion = 0;

  // ---------------- pet hair ----------------
  readonly clumpAlive = new Uint8Array(MAX_CLUMPS);
  readonly clumpId = new Uint32Array(MAX_CLUMPS);
  readonly clumpN = new Uint8Array(MAX_CLUMPS);
  readonly clumpCaptured = new Uint8Array(MAX_CLUMPS);
  private readonly clumpNear = new Uint8Array(MAX_CLUMPS);
  private readonly clumpAttachLx = new Float32Array(MAX_CLUMPS);
  /** Fibers: index c * MAX_FIBERS_PER_CLUMP + f. Base position is the fiber's root end. */
  readonly fibAlive = new Uint8Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  readonly fibX = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  readonly fibZ = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  readonly fibAng = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  readonly fibLen = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  /** Curvature (rad/m) of the fiber. */
  readonly fibCurl = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  /** Length multiplier (1 at rest, up to ~1.6 while being sucked in). */
  readonly fibStretch = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  readonly fibColor = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP * 3);
  private readonly fibV = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  private readonly fibDelay = new Float32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  clumpCount = 0;
  petVersion = 0;

  // ---------------- motes (visual only) ----------------
  readonly moteAlive = new Uint8Array(MAX_MOTES);
  readonly moteX = new Float32Array(MAX_MOTES);
  readonly moteY = new Float32Array(MAX_MOTES);
  readonly moteZ = new Float32Array(MAX_MOTES);
  private readonly moteVX = new Float32Array(MAX_MOTES);
  private readonly moteVY = new Float32Array(MAX_MOTES);
  private readonly moteVZ = new Float32Array(MAX_MOTES);
  readonly moteLife = new Float32Array(MAX_MOTES);
  readonly moteMaxLife = new Float32Array(MAX_MOTES);
  moteCount = 0;
  private dustRemovedPending = 0;

  // ---------------- accounting ----------------
  private readonly added = new Float64Array(4);
  private readonly collected = new Float64Array(4);
  private readonly remaining = new Float64Array(4);
  private readonly pendingPickup = new Float64Array(4);
  private crumbEvents: PickupEvent[] = [];

  // ---------------- infrastructure ----------------
  private readonly rng: Rng;
  private nextId = 1;
  private accumulator = 0;
  private readonly crumbHash: SpatialHash;
  private readonly hairHash: SpatialHash;
  private readonly fibHash: SpatialHash;
  private crumbHashDirty = true;
  private hairHashDirty = true;
  private fibHashDirty = true;
  private readonly gatherBuf: Int32Array;
  private readonly tmpPose: HeadPose = { x: 0, z: 0, yaw: 0 };
  private readonly lastPose: HeadPose = { x: 0, z: 0, yaw: 0 };
  private hasLastPose = false;
  private readonly disc = new Float64Array(2);
  // per-pose transform cache (set by setPose)
  private pc = 1;
  private ps = 0;
  private px = 0;
  private pz = 0;

  constructor(opts: DirtSimulationOptions = {}) {
    this.area = opts.area ?? PLAY_AREA;
    this.nozzle = opts.nozzle ?? DEFAULT_NOZZLE;
    this.quality = opts.quality ?? 'high';
    this.rng = new Rng(opts.seed ?? 1);
    const w = this.area.maxX - this.area.minX;
    const d = this.area.maxZ - this.area.minZ;
    if (w >= d) {
      this.fieldW = DUST_FIELD_W;
      this.fieldH = Math.max(16, Math.round((DUST_FIELD_W * d) / w));
    } else {
      this.fieldH = DUST_FIELD_W;
      this.fieldW = Math.max(16, Math.round((DUST_FIELD_W * w) / d));
    }
    this.cellW = w / this.fieldW;
    this.cellH = d / this.fieldH;
    this.cellMass = this.cellW * this.cellH * 1e4 * DUST_MASS_PER_CM2;
    this.dust = new Float32Array(this.fieldW * this.fieldH);
    this.dustTone = new Float32Array(this.fieldW * this.fieldH);
    this.rowMass = new Float64Array(this.fieldH);
    const hashCell = 0.025;
    this.crumbHash = new SpatialHash(this.area.minX, this.area.minZ, w, d, hashCell, MAX_CRUMBS);
    this.hairHash = new SpatialHash(this.area.minX, this.area.minZ, w, d, hashCell, MAX_STRANDS * MAX_STRAND_POINTS);
    this.fibHash = new SpatialHash(this.area.minX, this.area.minZ, w, d, hashCell, MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
    this.gatherBuf = new Int32Array(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP);
  }

  // =====================================================================================
  // Field mapping
  // =====================================================================================

  /** Column of the cell containing world x (clamped). */
  cellCol(x: number): number {
    const i = Math.floor((x - this.area.minX) / this.cellW);
    return i < 0 ? 0 : i >= this.fieldW ? this.fieldW - 1 : i;
  }
  cellRow(z: number): number {
    const j = Math.floor((z - this.area.minZ) / this.cellH);
    return j < 0 ? 0 : j >= this.fieldH ? this.fieldH - 1 : j;
  }
  cellCenterX(i: number): number {
    return this.area.minX + (i + 0.5) * this.cellW;
  }
  cellCenterZ(j: number): number {
    return this.area.minZ + (j + 0.5) * this.cellH;
  }
  /** Dust density at a world point (nearest cell; 0 outside the area). */
  dustAt(x: number, z: number): number {
    if (x < this.area.minX || x >= this.area.maxX || z < this.area.minZ || z >= this.area.maxZ) return 0;
    return this.dust[this.cellRow(z) * this.fieldW + this.cellCol(x)];
  }

  /**
   * Returns the dirty cell rectangle since the last call (inclusive [x0,y0,x1,y1]) and resets it.
   * False when nothing changed.
   */
  takeDustDirty(out: Int32Array): boolean {
    if (this.dirtyX1 < this.dirtyX0 || this.dirtyY1 < this.dirtyY0) return false;
    out[0] = this.dirtyX0;
    out[1] = this.dirtyY0;
    out[2] = this.dirtyX1;
    out[3] = this.dirtyY1;
    this.dirtyX0 = this.fieldW;
    this.dirtyY0 = this.fieldH;
    this.dirtyX1 = -1;
    this.dirtyY1 = -1;
    return true;
  }

  private markDirty(x0: number, y0: number, x1: number, y1: number): void {
    if (this.dirtyX1 < this.dirtyX0) {
      this.dirtyX0 = x0;
      this.dirtyY0 = y0;
      this.dirtyX1 = x1;
      this.dirtyY1 = y1;
    } else {
      if (x0 < this.dirtyX0) this.dirtyX0 = x0;
      if (y0 < this.dirtyY0) this.dirtyY0 = y0;
      if (x1 > this.dirtyX1) this.dirtyX1 = x1;
      if (y1 > this.dirtyY1) this.dirtyY1 = y1;
    }
    this.dustVersion++;
  }

  // =====================================================================================
  // Pose transform helpers (match src/contracts/world.ts headLocalToWorld / worldToHeadLocal)
  // =====================================================================================

  private setPose(p: HeadPose): void {
    this.pc = Math.cos(p.yaw + Math.PI);
    this.ps = Math.sin(p.yaw + Math.PI);
    this.px = p.x;
    this.pz = p.z;
  }
  private localX(wx: number, wz: number): number {
    return (wx - this.px) * this.pc - (wz - this.pz) * this.ps;
  }
  private localZ(wx: number, wz: number): number {
    return (wx - this.px) * this.ps + (wz - this.pz) * this.pc;
  }
  private worldX(lx: number, lz: number): number {
    return this.px + lx * this.pc + lz * this.ps;
  }
  private worldZ(lx: number, lz: number): number {
    return this.pz - lx * this.ps + lz * this.pc;
  }
  /** World AABB of a head-local rectangle, written to this.aabb. */
  private readonly aabb = new Float64Array(4);
  private localRectAabb(x0: number, z0: number, x1: number, z1: number): void {
    let minX = Infinity;
    let minZ = Infinity;
    let maxX = -Infinity;
    let maxZ = -Infinity;
    for (let k = 0; k < 4; k++) {
      const lx = k & 1 ? x1 : x0;
      const lz = k & 2 ? z1 : z0;
      const wx = this.worldX(lx, lz);
      const wz = this.worldZ(lx, lz);
      if (wx < minX) minX = wx;
      if (wx > maxX) maxX = wx;
      if (wz < minZ) minZ = wz;
      if (wz > maxZ) maxZ = wz;
    }
    this.aabb[0] = minX;
    this.aabb[1] = minZ;
    this.aabb[2] = maxX;
    this.aabb[3] = maxZ;
  }
  /** Grow this.aabb to also cover the same box translated by (dx, dz). */
  private extendAabb(dx: number, dz: number): void {
    if (dx < 0) this.aabb[0] += dx;
    else this.aabb[2] += dx;
    if (dz < 0) this.aabb[1] += dz;
    else this.aabb[3] += dz;
  }
  private inIntake(lx: number, lz: number): boolean {
    const n = this.nozzle;
    return lx >= -n.intakeWidth / 2 && lx <= n.intakeWidth / 2 && lz >= n.intakeZMin && lz <= n.intakeZMax;
  }
  private inBand(lx: number, lz: number): boolean {
    const n = this.nozzle;
    const b = ATTRACT_BAND;
    return lx >= -n.intakeWidth / 2 - b && lx <= n.intakeWidth / 2 + b && lz >= n.intakeZMin - b && lz <= n.intakeZMax + b;
  }
  private inShell(lx: number, lz: number, pad: number): boolean {
    const n = this.nozzle;
    return lx >= -n.shellWidth / 2 - pad && lx <= n.shellWidth / 2 + pad && lz >= n.shellZMin - pad && lz <= n.shellZMax + pad;
  }
  private get intakeCenterZ(): number {
    return (this.nozzle.intakeZMin + this.nozzle.intakeZMax) / 2;
  }

  // =====================================================================================
  // Public API: deposition
  // =====================================================================================

  addScatter(kind: DirtKind, density: DirtDensity, x: number, z: number): number {
    const m = DENSITY_MULT[density];
    const rng = this.rng;
    const p = this.clampReach(x, z, REACH_MARGIN);
    x = p[0];
    z = p[1];
    let added = 0;
    if (kind === 'dust' || kind === 'mixed') {
      const r = 0.03 + 0.02 * m;
      added += this.depositDustCluster(rng, x, z, r * 1.2, 0.45 + 0.3 * m);
    }
    if (kind === 'crumbs' || kind === 'mixed') {
      const n = Math.round((kind === 'mixed' ? 6 : 12) * m);
      added += this.scatterCrumbs(rng, x, z, 0.025 + 0.02 * m, n);
    }
    if (kind === 'hair' || (kind === 'mixed' && rng.next() < 0.6)) {
      const n = kind === 'mixed' ? 1 : Math.max(1, Math.round(3 * m));
      for (let i = 0; i < n; i++) {
        rng.disc(this.disc);
        added += this.addStrand(rng, x + this.disc[0] * 0.04, z + this.disc[1] * 0.04);
      }
    }
    if (kind === 'pet' || (kind === 'mixed' && rng.next() < 0.5)) {
      const n = kind === 'mixed' ? 1 : Math.max(1, Math.round(1.2 * m));
      for (let i = 0; i < n; i++) {
        rng.disc(this.disc);
        added += this.addClump(rng, x + this.disc[0] * 0.035, z + this.disc[1] * 0.035, m);
      }
    }
    return added;
  }

  addStroke(kind: DirtKind, density: DirtDensity, x0: number, z0: number, x1: number, z1: number, dt: number): number {
    const m = DENSITY_MULT[density];
    const rng = this.rng;
    const dist = Math.hypot(x1 - x0, z1 - z0);
    // Distance travelled plus a bounded dwell contribution (≤ 1.5 cm equivalent per call).
    const len = dist + 0.15 * Math.min(Math.max(dt, 0), 0.1);
    if (len <= 0) return 0;
    let added = 0;
    const dx = dist > 1e-9 ? (x1 - x0) / dist : 0;
    const dz = dist > 1e-9 ? (z1 - z0) / dist : 0;
    const sample = (spread: number) => {
      const t = rng.next();
      const lat = rng.gauss() * spread;
      const p = this.clampReach(x0 + (x1 - x0) * t - dz * lat, z0 + (z1 - z0) * t + dx * lat, REACH_MARGIN);
      return p;
    };
    const count = (ratePerM: number) => {
      const e = ratePerM * len;
      let n = Math.floor(e);
      if (rng.next() < e - n) n++;
      return n;
    };
    if (kind === 'dust' || kind === 'mixed') {
      const n = count(45 * (0.6 + 0.4 * m));
      const dir = dist > 1e-9 ? Math.atan2(z1 - z0, x1 - x0) : rng.next() * Math.PI;
      for (let i = 0; i < n; i++) {
        const p = sample(0.008);
        added += this.depositDustCluster(rng, p[0], p[1], rng.range(0.022, 0.034), 0.32 + 0.22 * m, REACH_MARGIN, dir + rng.gauss() * 0.15);
      }
    }
    if (kind === 'crumbs' || kind === 'mixed') {
      const n = count((kind === 'mixed' ? 45 : 110) * m);
      for (let i = 0; i < n; i++) {
        const p = sample(0.018);
        added += this.addCrumb(rng, p[0], p[1]);
      }
    }
    if (kind === 'hair' || kind === 'mixed') {
      const n = count((kind === 'mixed' ? 6 : 16) * m);
      for (let i = 0; i < n; i++) {
        const p = sample(0.02);
        added += this.addStrand(rng, p[0], p[1]);
      }
    }
    if (kind === 'pet' || kind === 'mixed') {
      const n = count((kind === 'mixed' ? 4 : 10) * m);
      for (let i = 0; i < n; i++) {
        const p = sample(0.02);
        added += this.addClump(rng, p[0], p[1], m);
      }
    }
    return added;
  }

  addPreset(seed?: number): number {
    const rng = seed === undefined ? this.rng : new Rng(seed);
    const inset = this.nozzle.intakeWidth / 2 + 0.04;
    const a = this.area;
    const rx = (t: number) => a.minX + inset + t * (a.maxX - a.minX - 2 * inset);
    const rz = (t: number) => a.minZ + inset + t * (a.maxZ - a.minZ - 2 * inset);
    let added = 0;
    // Dust patches with overlapping density, some elongated (traffic paths).
    const nDust = 6;
    for (let i = 0; i < nDust; i++) {
      const cx = rx(rng.next());
      const cz = rz(rng.next());
      added += this.depositDustCluster(rng, cx, cz, rng.range(0.05, 0.09), rng.range(0.4, 0.7), inset);
    }
    // Crumb clusters.
    for (let c = 0; c < 4; c++) {
      const cx = rx(rng.next());
      const cz = rz(rng.next());
      const n = rng.int(10, 22);
      added += this.scatterCrumbs(rng, cx, cz, rng.range(0.03, 0.06), n, inset);
    }
    // Long hair.
    for (let i = 0; i < 10; i++) added += this.addStrand(rng, rx(rng.next()), rz(rng.next()), inset);
    // Pet hair clumps.
    for (let i = 0; i < 5; i++) added += this.addClump(rng, rx(rng.next()), rz(rng.next()), 1, inset);
    return added;
  }

  addIntroPatch(pose: HeadPose): number {
    const rng = this.rng;
    let added = 0;
    // Compact, clearly visible patch ≈ 25 cm (across the head) × 18 cm (depth), 16–34 cm in front.
    // One warped core film plus two faint overlapping films so the outline stays irregular.
    const core = headLocalToWorld(pose, 0, 0.25);
    const cq = this.clampReach(core.x, core.z, REACH_MARGIN);
    // long axis across the head (head-local X in world)
    const across = Math.atan2(-Math.sin(pose.yaw + Math.PI), Math.cos(pose.yaw + Math.PI));
    added += this.depositFilm(rng, cq[0], cq[1], 0.13, 0.085, across + rng.gauss() * 0.1, 0.65, rng.next(), REACH_MARGIN);
    for (let i = 0; i < 2; i++) {
      const l = headLocalToWorld(pose, rng.range(-0.07, 0.07), rng.range(0.2, 0.3));
      const q = this.clampReach(l.x, l.z, REACH_MARGIN);
      added += this.depositFilm(rng, q[0], q[1], rng.range(0.06, 0.09), rng.range(0.03, 0.045), across + rng.gauss() * 0.4, 0.35, rng.next(), REACH_MARGIN);
    }
    for (let i = 0; i < 30; i++) {
      const l = headLocalToWorld(pose, rng.range(-0.11, 0.11) * (0.6 + 0.4 * rng.next()), rng.range(0.17, 0.33));
      const q = this.clampReach(l.x, l.z, REACH_MARGIN);
      added += this.addCrumb(rng, q[0], q[1]);
    }
    return added;
  }

  /**
   * Uniform dust over a world rectangle (tests / QA captures). Accounted like any deposition and
   * subject to the dust cap. Returns mass actually added.
   */
  fillDustRect(x0: number, z0: number, x1: number, z1: number, density: number): number {
    const i0 = this.cellCol(Math.min(x0, x1));
    const i1 = this.cellCol(Math.max(x0, x1));
    const j0 = this.cellRow(Math.min(z0, z1));
    const j1 = this.cellRow(Math.max(z0, z1));
    const target = Math.fround(Math.min(1, Math.max(0, density)));
    let dmass = 0;
    for (let j = j0; j <= j1; j++) {
      let row = 0;
      for (let i = i0; i <= i1; i++) {
        if (this.remaining[K_DUST] + (dmass + row) * this.cellMass >= DUST_MASS_CAP) break;
        const k = j * this.fieldW + i;
        const old = this.dust[k];
        if (target <= old) continue;
        this.dust[k] = target;
        this.dustTone[k] = 0.5;
        row += target - old;
      }
      this.rowMass[j] += row;
      dmass += row;
    }
    this.markDirty(i0, j0, i1, j1);
    const m = dmass * this.cellMass;
    this.added[K_DUST] += m;
    this.remaining[K_DUST] += m;
    return m;
  }

  clearFloor(): void {
    this.dust.fill(0);
    this.dustTone.fill(0);
    this.rowMass.fill(0);
    this.markDirty(0, 0, this.fieldW - 1, this.fieldH - 1);
    this.crumbAlive.fill(0);
    this.crumbFlags.fill(0);
    this.crumbCount = 0;
    this.crumbHigh = 0;
    this.crumbFreeN = 0;
    this.strandAlive.fill(0);
    this.strandPointLive.fill(0);
    this.strandCaptured.fill(0);
    this.strandCount = 0;
    this.clumpAlive.fill(0);
    this.clumpCaptured.fill(0);
    this.fibAlive.fill(0);
    this.clumpCount = 0;
    this.moteAlive.fill(0);
    this.moteCount = 0;
    this.dustRemovedPending = 0;
    this.added.fill(0);
    this.collected.fill(0);
    this.remaining.fill(0);
    this.pendingPickup.fill(0);
    this.crumbEvents.length = 0;
    this.crumbHashDirty = this.hairHashDirty = this.fibHashDirty = true;
    this.crumbVersion++;
    this.hairVersion++;
    this.petVersion++;
  }

  // =====================================================================================
  // Deposition internals
  // =====================================================================================

  private readonly reachOut = new Float64Array(2);
  private clampReach(x: number, z: number, margin: number): Float64Array {
    const a = this.area;
    this.reachOut[0] = Math.min(a.maxX - margin, Math.max(a.minX + margin, x));
    this.reachOut[1] = Math.min(a.maxZ - margin, Math.max(a.minZ + margin, z));
    return this.reachOut;
  }

  /** A cluster of noise-modulated anisotropic blobs plus a faint haze. Returns mass actually added. */
  /**
   * One irregular dust film: an elongated, domain-warped fbm mask with a wide feathered edge, varying
   * density inside and a faint fiber-like streak grain along its long axis. Deliberately a single
   * continuous shape (no sub-blob composition), so it never reads as lobes / paw prints / puffs.
   * `ang` is the direction of the long axis in world XZ (radians from +X toward +Z); random if omitted.
   */
  private depositDustCluster(rng: Rng, x: number, z: number, radius: number, peak: number, margin = REACH_MARGIN, ang?: number): number {
    const a = ang ?? rng.next() * Math.PI;
    const rx = radius * rng.range(1.0, 1.35);
    const rz = rx * rng.range(0.38, 0.7);
    return this.depositFilm(rng, x, z, rx, rz, a, peak, rng.next(), margin);
  }

  private depositFilm(rng: Rng, x: number, z: number, rx: number, rz: number, ang: number, peak: number, tone: number, margin: number): number {
    const capLeft = DUST_MASS_CAP - this.remaining[K_DUST];
    // the last 0.5 % of the budget counts as full (the scaled-down films approach the cap asymptotically)
    if (capLeft <= DUST_MASS_CAP * 0.005) return 0;
    // Expected mass ≈ peak · ellipse area · 0.42 (feathered mask × interior noise) — scales down near the cap.
    const est = (peak * Math.PI * rx * rz * 0.42) / (this.cellW * this.cellH) * this.cellMass;
    if (est > capLeft) peak *= capLeft / est;
    const ar = this.area;
    const reach = Math.max(rx, rz) * 1.35;
    const i0 = this.cellCol(Math.max(ar.minX + margin, x - reach));
    const i1 = this.cellCol(Math.min(ar.maxX - margin, x + reach));
    const j0 = this.cellRow(Math.max(ar.minZ + margin, z - reach));
    const j1 = this.cellRow(Math.min(ar.maxZ - margin, z + reach));
    if (i1 < i0 || j1 < j0) return 0;
    const ca = Math.cos(ang);
    const sa = Math.sin(ang);
    const s0 = (rng.next() * 997) | 0;
    const o1 = rng.next() * 50;
    const o2 = rng.next() * 50;
    const o3 = rng.next() * 50;
    const warp = 0.32;
    let dmass = 0;
    const W = this.fieldW;
    for (let j = j0; j <= j1; j++) {
      const wz = this.cellCenterZ(j);
      let rowDelta = 0;
      for (let i = i0; i <= i1; i++) {
        const wx = this.cellCenterX(i);
        const dx = wx - x;
        const dz = wz - z;
        const along = dx * ca + dz * sa;
        const across = -dx * sa + dz * ca;
        const u = along / rx;
        const v = across / rz;
        if (u * u + v * v > 2.2) continue;
        // domain warp in shape-normalized space → irregular, non-circular outline
        const wu = u + warp * (fbm(u * 1.4 + o1, v * 1.4, s0) - 0.5) * 2;
        const wv = v + warp * (fbm(u * 1.4, v * 1.4 + o2, s0 + 5) - 0.5) * 2;
        const r = Math.sqrt(wu * wu + wv * wv) + (fbm(u * 3.5 + o3, v * 3.5, s0 + 9) - 0.5) * 0.3;
        if (r >= 1) continue;
        // wide feathered edge
        const t = r <= 0.25 ? 0 : (r - 0.25) / 0.75;
        const mask = 1 - t * t * (3 - 2 * t);
        // interior density variation (soft, low contrast)
        const inner = 0.55 + 0.45 * fbm(u * 1.8 + o2, v * 1.8 + o1, s0 + 13);
        // faint fiber streaks: noise stretched along the long axis (≈12 mm × 3 mm cells)
        const streak = 0.75 + 0.5 * fbm(along / 0.012, across / 0.003, s0 + 21);
        const add = peak * mask * inner * streak;
        if (add <= 1e-5) continue;
        const k = j * W + i;
        const old = this.dust[k];
        const nv = Math.fround(Math.min(1, old + add));
        if (nv <= old) continue;
        this.dust[k] = nv;
        const realAdd = nv - old;
        this.dustTone[k] = old > 0 ? (old * this.dustTone[k] + realAdd * tone) / nv : tone;
        rowDelta += realAdd;
      }
      if (rowDelta > 0) {
        this.rowMass[j] += rowDelta;
        dmass += rowDelta;
      }
    }
    if (dmass > 0) {
      this.markDirty(i0, j0, i1, j1);
      const m = dmass * this.cellMass;
      this.added[K_DUST] += m;
      this.remaining[K_DUST] += m;
      return m;
    }
    return 0;
  }

  private scatterCrumbs(rng: Rng, x: number, z: number, radius: number, n: number, margin = REACH_MARGIN): number {
    let added = 0;
    // 1–3 sub-clusters so the scatter is never a uniform disc
    const subs = 1 + Math.floor(rng.next() * 3);
    const sx = [0, 0, 0];
    const sz = [0, 0, 0];
    for (let s = 0; s < subs; s++) {
      rng.disc(this.disc);
      sx[s] = x + this.disc[0] * radius * 0.6;
      sz[s] = z + this.disc[1] * radius * 0.6;
    }
    for (let i = 0; i < n; i++) {
      const s = i % subs;
      const r = radius * (0.25 + 0.75 * Math.pow(rng.next(), 1.6));
      const a = rng.next() * Math.PI * 2;
      const p = this.clampReach(sx[s] + Math.cos(a) * r, sz[s] + Math.sin(a) * r, margin);
      const m = this.addCrumb(rng, p[0], p[1]);
      if (m === 0 && this.isFull('crumbs')) break;
      added += m;
    }
    return added;
  }

  private addCrumb(rng: Rng, x: number, z: number): number {
    if (this.crumbCount >= MAX_CRUMBS) return 0;
    const i = this.crumbFreeN > 0 ? this.crumbFree[--this.crumbFreeN] : this.crumbHigh++;
    const size = 0.002 + 0.008 * Math.pow(rng.next(), 2.2);
    this.crumbAlive[i] = 1;
    this.crumbFlags[i] = CRUMB_SETTLING;
    this.crumbId[i] = this.nextId++;
    this.crumbX[i] = x;
    this.crumbZ[i] = z;
    this.crumbY[i] = rng.range(0.003, 0.009);
    this.crumbVY[i] = 0;
    this.crumbVX[i] = 0;
    this.crumbVZ[i] = 0;
    this.crumbYaw[i] = rng.next() * Math.PI * 2;
    this.crumbRoll[i] = 0;
    this.crumbRollDir[i] = 0;
    this.crumbSize[i] = size;
    this.crumbShape[i] = Math.min(5, Math.floor(rng.next() * 6));
    const c = CRUMB_PALETTE[Math.min(5, Math.floor(rng.next() * 6))];
    const v = rng.range(0.88, 1.08);
    this.crumbColor[i * 3] = Math.min(1, c[0] * v);
    this.crumbColor[i * 3 + 1] = Math.min(1, c[1] * v * rng.range(0.96, 1.03));
    this.crumbColor[i * 3 + 2] = Math.min(1, c[2] * v * rng.range(0.92, 1.05));
    const m = crumbMass(size);
    this.crumbMassArr[i] = m;
    this.crumbCount++;
    this.added[K_CRUMBS] += m;
    this.remaining[K_CRUMBS] += m;
    this.crumbHashDirty = true;
    this.crumbVersion++;
    return m;
  }

  private addStrand(rng: Rng, cx: number, cz: number, margin = REACH_MARGIN): number {
    if (this.strandCount >= MAX_STRANDS) return 0;
    let s = -1;
    for (let k = 0; k < MAX_STRANDS; k++)
      if (!this.strandAlive[k]) {
        s = k;
        break;
      }
    if (s < 0) return 0;
    const L = 0.03 + 0.12 * Math.pow(rng.next(), 1.25);
    const segs = Math.min(12, Math.max(6, Math.round(L / 0.011)));
    const n = segs + 1;
    const seg = L / segs;
    const base = s * MAX_STRAND_POINTS;
    // Curved chain: smoothly varying curvature, occasional tight curl.
    let ang = rng.next() * Math.PI * 2;
    let k = rng.range(-1, 1) * (rng.next() < 0.3 ? 70 : 22);
    let px = 0;
    let pz = 0;
    let sx = 0;
    let sz = 0;
    for (let p = 0; p < n; p++) {
      this.strandPX[base + p] = px;
      this.strandPZ[base + p] = pz;
      sx += px;
      sz += pz;
      ang += k * seg + rng.gauss() * 0.12;
      k += rng.gauss() * 12;
      px += Math.cos(ang) * seg;
      pz += Math.sin(ang) * seg;
    }
    // centre on (cx, cz), then shift fully inside the reachable area
    let minX = Infinity;
    let maxX = -Infinity;
    let minZ = Infinity;
    let maxZ = -Infinity;
    const ox = cx - sx / n;
    const oz = cz - sz / n;
    for (let p = 0; p < n; p++) {
      const x = (this.strandPX[base + p] += ox);
      const z = (this.strandPZ[base + p] += oz);
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }
    const a = this.area;
    let shx = 0;
    let shz = 0;
    if (minX < a.minX + margin) shx = a.minX + margin - minX;
    else if (maxX > a.maxX - margin) shx = a.maxX - margin - maxX;
    if (minZ < a.minZ + margin) shz = a.minZ + margin - minZ;
    else if (maxZ > a.maxZ - margin) shz = a.maxZ - margin - maxZ;
    for (let p = 0; p < MAX_STRAND_POINTS; p++) {
      if (p < n) {
        this.strandPX[base + p] += shx;
        this.strandPZ[base + p] += shz;
      }
      this.strandPointLive[base + p] = p < n ? 1 : 0;
    }
    const col = HAIR_PALETTE[pickWeighted(rng, HAIR_PALETTE_W)];
    const v = rng.range(0.85, 1.12);
    this.strandColor[s * 3] = Math.min(1, col[0] * v);
    this.strandColor[s * 3 + 1] = Math.min(1, col[1] * v);
    this.strandColor[s * 3 + 2] = Math.min(1, col[2] * v);
    this.strandWidth[s] = rng.range(0.0005, 0.0008);
    this.strandAlive[s] = 1;
    this.strandId[s] = this.nextId++;
    this.strandN[s] = n;
    this.strandSeg[s] = seg;
    this.strandCaptured[s] = 0;
    const mass = L * 100 * HAIR_MASS_PER_CM;
    this.strandPointMass[s] = mass / n;
    this.strandCount++;
    this.added[K_HAIR] += mass;
    this.remaining[K_HAIR] += mass;
    this.hairHashDirty = true;
    this.hairVersion++;
    return mass;
  }

  private addClump(rng: Rng, cx: number, cz: number, m: number, margin = REACH_MARGIN): number {
    if (this.clumpCount >= MAX_CLUMPS) return 0;
    let c = -1;
    for (let k = 0; k < MAX_CLUMPS; k++)
      if (!this.clumpAlive[k]) {
        c = k;
        break;
      }
    if (c < 0) return 0;
    const R = rng.range(0.011, 0.02 + 0.005 * m);
    const nf = Math.min(MAX_FIBERS_PER_CLUMP, Math.round(rng.range(38, 56) * (0.85 + 0.15 * m)));
    const ori = rng.next() * Math.PI;
    const elong = rng.range(0.45, 1);
    const col = PET_PALETTE[pickWeighted(rng, PET_PALETTE_W)];
    // a secondary coat colour mixed into some fibers (tabby / two-tone undercoat)
    const col2 = PET_PALETTE[pickWeighted(rng, PET_PALETTE_W)];
    const mix2 = rng.next() < 0.5 ? rng.range(0.15, 0.4) : 0;
    const a = this.area;
    // keep the whole clump (radius + fiber length) inside the reachable area
    const pad = margin + R + 0.03;
    cx = Math.min(a.maxX - pad, Math.max(a.minX + pad, cx));
    cz = Math.min(a.maxZ - pad, Math.max(a.minZ + pad, cz));
    const co = Math.cos(ori);
    const so = Math.sin(ori);
    const base = c * MAX_FIBERS_PER_CLUMP;
    for (let f = 0; f < MAX_FIBERS_PER_CLUMP; f++) {
      const idx = base + f;
      if (f >= nf) {
        this.fibAlive[idx] = 0;
        continue;
      }
      // denser centre: gaussian-ish radius
      const u = rng.gauss() * 0.5 * R;
      const v = rng.gauss() * 0.5 * R * elong;
      const len = rng.range(0.012, 0.03);
      // matted tuft: fibers mostly follow a local flow direction (swirling slightly across the clump)
      const fa = ori + (u / R) * 0.6 + rng.gauss() * 0.4 + (rng.next() < 0.3 ? Math.PI : 0);
      // place the fiber so its midpoint sits at (u, v)
      const mx = cx + u * co - v * so;
      const mz = cz + u * so + v * co;
      this.fibX[idx] = mx - Math.cos(fa) * len * 0.5;
      this.fibZ[idx] = mz - Math.sin(fa) * len * 0.5;
      this.fibAng[idx] = fa;
      this.fibLen[idx] = len;
      this.fibCurl[idx] = rng.range(-45, 45);
      this.fibStretch[idx] = 1;
      this.fibV[idx] = 0;
      this.fibDelay[idx] = rng.range(0, 0.12);
      const t = rng.range(0.85, 1.08);
      const cc = mix2 > 0 && rng.next() < mix2 ? col2 : col;
      this.fibColor[idx * 3] = Math.min(1, cc[0] * t);
      this.fibColor[idx * 3 + 1] = Math.min(1, cc[1] * t);
      this.fibColor[idx * 3 + 2] = Math.min(1, cc[2] * t * rng.range(0.95, 1.04));
      this.fibAlive[idx] = 1;
    }
    this.clumpAlive[c] = 1;
    this.clumpId[c] = this.nextId++;
    this.clumpN[c] = nf;
    this.clumpCaptured[c] = 0;
    this.clumpNear[c] = 0;
    this.clumpCount++;
    const mass = nf * PET_FIBER_MASS;
    this.added[K_PET] += mass;
    this.remaining[K_PET] += mass;
    this.fibHashDirty = true;
    this.petVersion++;
    return mass;
  }

  // =====================================================================================
  // Step: swept pickup + fixed-step dynamics
  // =====================================================================================

  step(dt: number, prev: HeadPose, next: HeadPose, pickupActive: boolean): void {
    if (!(dt > 0)) dt = 0;
    this.rebuildHashes();
    this.clumpNear.fill(0);
    // 1) Swept pickup over the full path (geometry; frame-rate independent).
    if (pickupActive) this.sweep(prev, next);
    // 2) Fixed-step dynamics with capped catch-up.
    this.accumulator += dt;
    let n = Math.floor(this.accumulator / SIM_DT + 1e-9);
    if (n > MAX_CATCHUP_STEPS) {
      n = MAX_CATCHUP_STEPS;
      this.accumulator = 0;
    } else {
      this.accumulator -= n * SIM_DT;
      if (this.accumulator < 0) this.accumulator = 0;
    }
    for (let k = 1; k <= n; k++) {
      this.lerpPose(prev, next, k / n, this.tmpPose);
      this.dynamics(SIM_DT, this.tmpPose, pickupActive);
    }
    // 3) Occlusion flags at the final pose.
    this.updateUnderShell(next);
    this.lastPose.x = next.x;
    this.lastPose.z = next.z;
    this.lastPose.yaw = next.yaw;
    this.hasLastPose = true;
  }

  private rebuildHashes(): void {
    if (this.crumbHashDirty) {
      this.crumbHash.rebuild(this.crumbHigh, this.crumbX, this.crumbZ, this.crumbAlive);
      this.crumbHashDirty = false;
    }
    if (this.hairHashDirty) {
      this.hairHash.rebuild(MAX_STRANDS * MAX_STRAND_POINTS, this.strandPX, this.strandPZ, this.strandPointLive);
      this.hairHashDirty = false;
    }
    if (this.fibHashDirty) {
      this.fibHash.rebuild(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP, this.fibX, this.fibZ, this.fibAlive);
      this.fibHashDirty = false;
    }
  }

  private lerpPose(a: HeadPose, b: HeadPose, t: number, out: HeadPose): void {
    out.x = a.x + (b.x - a.x) * t;
    out.z = a.z + (b.z - a.z) * t;
    out.yaw = a.yaw + wrapAngle(b.yaw - a.yaw) * t;
  }

  /** Number of pickup evaluations used for the last sweep (exposed for tests/diagnostics). */
  lastSubsteps = 0;

  private sweep(from: HeadPose, to: HeadPose): void {
    const dist = Math.hypot(to.x - from.x, to.z - from.z);
    const dyaw = Math.abs(wrapAngle(to.yaw - from.yaw));
    if (dist > TELEPORT_DISTANCE) {
      this.lastSubsteps = 1;
      this.pickupSegment(to, to);
      return;
    }
    const depth = this.nozzle.intakeZMax - this.nozzle.intakeZMin;
    const n = Math.min(512, Math.max(1, Math.ceil(dist / (SUBSTEP_DEPTH_FRACTION * depth)), Math.ceil(dyaw / SUBSTEP_MAX_YAW)));
    this.lastSubsteps = n;
    this.lerpPose(from, to, 0, this.segA);
    for (let k = 1; k <= n; k++) {
      this.lerpPose(from, to, k / n, this.segB);
      this.pickupSegment(this.segA, this.segB);
      this.segA.x = this.segB.x;
      this.segA.z = this.segB.z;
      this.segA.yaw = this.segB.yaw;
    }
  }

  private readonly segA: HeadPose = { x: 0, z: 0, yaw: 0 };
  private readonly segB: HeadPose = { x: 0, z: 0, yaw: 0 };
  /** Head motion during the current sub-segment, expressed in the segment's (mid-yaw) local frame. */
  private sdx = 0;
  private sdz = 0;

  /**
   * True when a world point (given in segment-local coords relative to the segment start) lies inside
   * the local rect [x0,x1]×[z0,z1] at SOME time t∈[0,1] of the sub-segment. Translation is handled
   * exactly (Minkowski sweep of the rectangle along the segment); rotation within a substep (≤ 1.5°)
   * is approximated by the mid-yaw frame.
   */
  private sweptIn(lx: number, lz: number, x0: number, x1: number, z0: number, z1: number): boolean {
    let t0 = 0;
    let t1 = 1;
    const dx = this.sdx;
    if (dx > 1e-12 || dx < -1e-12) {
      let a = (lx - x1) / dx;
      let b = (lx - x0) / dx;
      if (a > b) {
        const t = a;
        a = b;
        b = t;
      }
      if (a > t0) t0 = a;
      if (b < t1) t1 = b;
    } else if (lx < x0 || lx > x1) return false;
    const dz = this.sdz;
    if (dz > 1e-12 || dz < -1e-12) {
      let a = (lz - z1) / dz;
      let b = (lz - z0) / dz;
      if (a > b) {
        const t = a;
        a = b;
        b = t;
      }
      if (a > t0) t0 = a;
      if (b < t1) t1 = b;
    } else if (lz < z0 || lz > z1) return false;
    return t0 <= t1;
  }

  /**
   * Remove everything the intake footprint touches while moving A→B (one substep); flag attraction
   * candidates. The frame is anchored at A with the mid-substep yaw.
   */
  private pickupSegment(A: HeadPose, Bp: HeadPose): void {
    this.tmpPose.x = A.x;
    this.tmpPose.z = A.z;
    this.tmpPose.yaw = A.yaw + wrapAngle(Bp.yaw - A.yaw) * 0.5;
    this.setPose(this.tmpPose);
    const mwx = Bp.x - A.x;
    const mwz = Bp.z - A.z;
    this.sdx = this.localX(A.x + mwx, A.z + mwz);
    this.sdz = this.localZ(A.x + mwx, A.z + mwz);
    const nz = this.nozzle;
    const hw = nz.intakeWidth / 2;
    // ---- dust ----
    const J = EDGE_JITTER;
    this.localRectAabb(-hw - J, nz.intakeZMin - J, hw + J, nz.intakeZMax + J);
    this.extendAabb(mwx, mwz);
    const i0 = this.cellCol(this.aabb[0]);
    const i1 = this.cellCol(this.aabb[2]);
    const j0 = this.cellRow(this.aabb[1]);
    const j1 = this.cellRow(this.aabb[3]);
    const a = this.area;
    if (this.aabb[2] >= a.minX && this.aabb[0] < a.maxX && this.aabb[3] >= a.minZ && this.aabb[1] < a.maxZ) {
      const W = this.fieldW;
      let removed = 0;
      let dx0 = W;
      let dx1 = -1;
      let dy0 = this.fieldH;
      let dy1 = -1;
      for (let j = j0; j <= j1; j++) {
        if (this.rowMass[j] <= 0) continue;
        const wz = this.cellCenterZ(j);
        let rowRemoved = 0;
        for (let i = i0; i <= i1; i++) {
          const k = j * W + i;
          const d = this.dust[k];
          if (d <= 0) continue;
          const wx = this.cellCenterX(i);
          const lx = this.localX(wx, wz);
          const lz = this.localZ(wx, wz);
          // static per-cell edge jitter: slightly irregular track edge, deterministic and pass-independent
          const jx = (hash2(i, j, 11) - 0.5) * 2 * J;
          const jz = (hash2(i, j, 23) - 0.5) * 2 * J;
          if (!this.sweptIn(lx, lz, -hw - jx, hw + jx, nz.intakeZMin - jz, nz.intakeZMax + jz)) continue;
          this.dust[k] = 0;
          rowRemoved += d;
          if (i < dx0) dx0 = i;
          if (i > dx1) dx1 = i;
        }
        if (rowRemoved > 0) {
          this.rowMass[j] -= rowRemoved;
          if (this.rowMass[j] < 1e-9) this.rowMass[j] = Math.max(0, this.recomputeRow(j));
          removed += rowRemoved;
          if (j < dy0) dy0 = j;
          if (j > dy1) dy1 = j;
        }
      }
      if (removed > 0) {
        const m = removed * this.cellMass;
        this.collectMass(K_DUST, m);
        this.dustRemovedPending += m;
        this.markDirty(dx0, dy0, dx1, dy1);
      }
    }
    // ---- crumbs ----
    const pad = 0.012; // hash staleness padding (attracted crumbs move a few mm per step)
    const B = ATTRACT_BAND;
    this.localRectAabb(-hw - B, nz.intakeZMin - B, hw + B, nz.intakeZMax + B);
    this.extendAabb(mwx, mwz);
    const iz0 = nz.intakeZMin;
    const iz1 = nz.intakeZMax;
    const buf = this.gatherBuf;
    let cnt = this.crumbHash.gather(this.aabb[0] - pad, this.aabb[1] - pad, this.aabb[2] + pad, this.aabb[3] + pad, buf);
    for (let q = 0; q < cnt; q++) {
      const i = buf[q];
      if (!this.crumbAlive[i]) continue;
      const lx = this.localX(this.crumbX[i], this.crumbZ[i]);
      const lz = this.localZ(this.crumbX[i], this.crumbZ[i]);
      if (this.sweptIn(lx, lz, -hw, hw, iz0, iz1)) this.collectCrumb(i);
      else if (this.sweptIn(lx, lz, -hw - B, hw + B, iz0 - B, iz1 + B)) this.crumbFlags[i] |= CRUMB_ATTRACTED;
    }
    // ---- long hair ----
    cnt = this.hairHash.gather(this.aabb[0] - pad, this.aabb[1] - pad, this.aabb[2] + pad, this.aabb[3] + pad, buf);
    for (let q = 0; q < cnt; q++) {
      const idx = buf[q];
      if (!this.strandPointLive[idx]) continue;
      const lx = this.localX(this.strandPX[idx], this.strandPZ[idx]);
      const lz = this.localZ(this.strandPX[idx], this.strandPZ[idx]);
      if (!this.sweptIn(lx, lz, -hw, hw, iz0, iz1)) continue;
      const s = (idx / MAX_STRAND_POINTS) | 0;
      const p = idx - s * MAX_STRAND_POINTS;
      // First contact captures the strand at that point (held by the roller); the rest is fed in by
      // the dynamics at HAIR_FEED_SPEED, so a strand never vanishes all at once.
      if (!this.strandCaptured[s]) {
        this.strandCaptured[s] = 1;
        this.strandAttachLx[s] = Math.max(-hw * 0.92, Math.min(hw * 0.92, lx));
        this.ingestPoint(s, p);
      }
    }
    // ---- pet hair ----
    cnt = this.fibHash.gather(this.aabb[0] - pad - 0.03, this.aabb[1] - pad - 0.03, this.aabb[2] + pad + 0.03, this.aabb[3] + pad + 0.03, buf);
    for (let q = 0; q < cnt; q++) {
      const idx = buf[q];
      if (!this.fibAlive[idx]) continue;
      const c = (idx / MAX_FIBERS_PER_CLUMP) | 0;
      // test both fiber ends
      const L = this.fibLen[idx] * this.fibStretch[idx];
      const bx = this.fibX[idx];
      const bz = this.fibZ[idx];
      const tx = bx + Math.cos(this.fibAng[idx]) * L;
      const tz = bz + Math.sin(this.fibAng[idx]) * L;
      const lbx = this.localX(bx, bz);
      const lbz = this.localZ(bx, bz);
      const ltx = this.localX(tx, tz);
      const ltz = this.localZ(tx, tz);
      if (this.sweptIn(lbx, lbz, -hw, hw, iz0, iz1) || this.sweptIn(ltx, ltz, -hw, hw, iz0, iz1)) {
        if (!this.clumpCaptured[c]) {
          this.clumpCaptured[c] = 1;
          this.clumpAttachLx[c] = Math.max(-hw * 0.92, Math.min(hw * 0.92, lbx));
        }
        this.ingestFiber(idx);
      } else if (this.sweptIn(lbx, lbz, -hw - B, hw + B, iz0 - B, iz1 + B) || this.sweptIn(ltx, ltz, -hw - B, hw + B, iz0 - B, iz1 + B)) {
        this.clumpNear[c] = 1;
      }
    }
  }

  private recomputeRow(j: number): number {
    let s = 0;
    const W = this.fieldW;
    for (let i = 0, k = j * W; i < W; i++, k++) s += this.dust[k];
    return s;
  }

  private isLeader(s: number, p: number): boolean {
    const base = s * MAX_STRAND_POINTS;
    const n = this.strandN[s];
    if (!this.strandPointLive[base + p]) return false;
    return (p > 0 && !this.strandPointLive[base + p - 1]) || (p < n - 1 && !this.strandPointLive[base + p + 1]);
  }

  private collectMass(k: number, m: number): void {
    this.collected[k] += m;
    this.remaining[k] -= m;
    if (this.remaining[k] < 0 && this.remaining[k] > -1e-9) this.remaining[k] = 0;
    this.pendingPickup[k] += m;
  }

  private collectCrumb(i: number): void {
    const m = this.crumbMassArr[i];
    this.crumbAlive[i] = 0;
    this.crumbFlags[i] = 0;
    this.crumbFree[this.crumbFreeN++] = i;
    this.crumbCount--;
    this.collected[K_CRUMBS] += m;
    this.remaining[K_CRUMBS] -= m;
    if (this.crumbEvents.length < 24) this.crumbEvents.push({ kind: 'crumbs', mass: m });
    else this.pendingPickup[K_CRUMBS] += m;
    this.crumbHashDirty = true;
    this.crumbVersion++;
  }

  private ingestPoint(s: number, p: number): void {
    const idx = s * MAX_STRAND_POINTS + p;
    if (!this.strandPointLive[idx]) return;
    this.strandPointLive[idx] = 0;
    this.collectMass(K_HAIR, this.strandPointMass[s]);
    this.hairHashDirty = true;
    this.hairVersion++;
    const base = s * MAX_STRAND_POINTS;
    const n = this.strandN[s];
    for (let k = 0; k < n; k++) if (this.strandPointLive[base + k]) return;
    this.strandAlive[s] = 0;
    this.strandCaptured[s] = 0;
    this.strandCount--;
  }

  private ingestFiber(idx: number): void {
    if (!this.fibAlive[idx]) return;
    this.fibAlive[idx] = 0;
    this.collectMass(K_PET, PET_FIBER_MASS);
    this.fibHashDirty = true;
    this.petVersion++;
    const c = (idx / MAX_FIBERS_PER_CLUMP) | 0;
    const base = c * MAX_FIBERS_PER_CLUMP;
    for (let f = 0; f < MAX_FIBERS_PER_CLUMP; f++) if (this.fibAlive[base + f]) return;
    this.clumpAlive[c] = 0;
    this.clumpCaptured[c] = 0;
    this.clumpCount--;
  }

  // ---------------------------------------------------------------------------------
  // Dynamics
  // ---------------------------------------------------------------------------------

  private dynamics(h: number, pose: HeadPose, active: boolean): void {
    this.setPose(pose);
    this.stepCrumbs(h, active);
    this.stepHair(h, active);
    this.stepPet(h, active);
    this.stepMotes(h, active);
  }

  private stepCrumbs(h: number, active: boolean): void {
    const nz = this.nozzle;
    const hw = nz.intakeWidth / 2;
    const rest = this.surface === 'carpet' ? 0.12 : this.surface === 'stone' ? 0.38 : 0.3;
    const rng = this.rng;
    let changed = false;
    for (let i = 0; i < this.crumbHigh; i++) {
      if (!this.crumbAlive[i]) continue;
      let f = this.crumbFlags[i];
      if (!(f & (CRUMB_SETTLING | CRUMB_ATTRACTED)) && this.crumbVX[i] === 0 && this.crumbVZ[i] === 0) continue;
      changed = true;
      let x = this.crumbX[i];
      let z = this.crumbZ[i];
      if (f & CRUMB_ATTRACTED) {
        const lx = this.localX(x, z);
        const lz = this.localZ(x, z);
        if (!active || !this.inBand(lx, lz)) {
          f &= ~CRUMB_ATTRACTED;
        } else {
          // accelerate toward the nearest point inside the intake (a few mm inside its edge)
          const tx = Math.max(-hw + 0.004, Math.min(hw - 0.004, lx));
          const tz = Math.max(nz.intakeZMin + 0.004, Math.min(nz.intakeZMax - 0.004, lz));
          const wx = this.worldX(tx, tz) - x;
          const wz = this.worldZ(tx, tz) - z;
          const d = Math.hypot(wx, wz) || 1;
          const acc = 3.2 / (0.6 + this.crumbSize[i] * 80);
          this.crumbVX[i] += (wx / d) * acc * h;
          this.crumbVZ[i] += (wz / d) * acc * h;
          if (!(f & CRUMB_HOPPED)) {
            f |= CRUMB_HOPPED | CRUMB_SETTLING;
            this.crumbVY[i] = rng.range(0.12, 0.3) * (this.surface === 'carpet' ? 0.6 : 1);
          }
        }
      }
      // rolling friction
      const fr = f & CRUMB_ATTRACTED ? 0.5 : this.surface === 'carpet' ? 14 : 9;
      const damp = Math.exp(-fr * h);
      this.crumbVX[i] *= damp;
      this.crumbVZ[i] *= damp;
      const sp = Math.hypot(this.crumbVX[i], this.crumbVZ[i]);
      if (!(f & CRUMB_ATTRACTED) && sp < 0.002) {
        this.crumbVX[i] = 0;
        this.crumbVZ[i] = 0;
      } else {
        x += this.crumbVX[i] * h;
        z += this.crumbVZ[i] * h;
        this.crumbRoll[i] += (sp * h) / Math.max(0.001, this.crumbSize[i] * 0.5);
        this.crumbRollDir[i] = Math.atan2(this.crumbVZ[i], this.crumbVX[i]);
      }
      // vertical settle / hop
      if (f & CRUMB_SETTLING) {
        this.crumbVY[i] -= GRAVITY * h;
        let y = this.crumbY[i] + this.crumbVY[i] * h;
        if (y <= 0) {
          y = 0;
          if (this.crumbVY[i] < -0.06) this.crumbVY[i] = -this.crumbVY[i] * rest;
          else {
            this.crumbVY[i] = 0;
            f &= ~CRUMB_SETTLING;
          }
        }
        this.crumbY[i] = y;
      }
      const a = this.area;
      x = Math.min(a.maxX - 0.001, Math.max(a.minX + 0.001, x));
      z = Math.min(a.maxZ - 0.001, Math.max(a.minZ + 0.001, z));
      this.crumbX[i] = x;
      this.crumbZ[i] = z;
      this.crumbFlags[i] = f;
      if (active && this.inIntake(this.localX(x, z), this.localZ(x, z))) this.collectCrumb(i);
    }
    if (changed) {
      this.crumbHashDirty = true;
      this.crumbVersion++;
    }
  }

  private stepHair(h: number, active: boolean): void {
    const zc = this.intakeCenterZ;
    for (let s = 0; s < MAX_STRANDS; s++) {
      if (!this.strandAlive[s] || !this.strandCaptured[s]) continue;
      if (!active) {
        this.strandCaptured[s] = 0;
        continue;
      }
      const base = s * MAX_STRAND_POINTS;
      const n = this.strandN[s];
      const seg = this.strandSeg[s];
      const ax = this.worldX(this.strandAttachLx[s], zc);
      const az = this.worldZ(this.strandAttachLx[s], zc);
      const feed = HAIR_FEED_SPEED * h;
      // move leaders toward the attach point; ingest when they reach the intake
      for (let p = 0; p < n; p++) {
        if (!this.isLeader(s, p)) continue;
        const idx = base + p;
        let x = this.strandPX[idx];
        let z = this.strandPZ[idx];
        const dx = ax - x;
        const dz = az - z;
        const d = Math.hypot(dx, dz);
        // the roller holds the leader: it never lags the attach point by more than 1 cm
        const mv = Math.max(feed, d - 0.01);
        if (d <= mv) {
          x = ax;
          z = az;
        } else {
          x += (dx / d) * mv;
          z += (dz / d) * mv;
        }
        this.strandPX[idx] = x;
        this.strandPZ[idx] = z;
        if (d <= feed) this.ingestPoint(s, p);
        if (!this.strandAlive[s]) break;
      }
      if (!this.strandAlive[s]) continue;
      // pull-only follow-the-leader constraints (forward for pieces led from below, backward for above)
      let ingBefore = false;
      for (let p = 0; p < n; p++) {
        const idx = base + p;
        if (!this.strandPointLive[idx]) {
          ingBefore = true;
          continue;
        }
        if (ingBefore && p > 0 && this.strandPointLive[idx - 1]) this.constrain(idx, idx - 1, seg);
      }
      let ingAfter = false;
      for (let p = n - 1; p >= 0; p--) {
        const idx = base + p;
        if (!this.strandPointLive[idx]) {
          ingAfter = true;
          continue;
        }
        if (ingAfter && p < n - 1 && this.strandPointLive[idx + 1]) this.constrain(idx, idx + 1, seg);
      }
      this.hairHashDirty = true;
      this.hairVersion++;
    }
  }

  /** Pull point `i` toward `j` so their distance is at most `len` (never pushes). */
  private constrain(i: number, j: number, len: number): void {
    const dx = this.strandPX[i] - this.strandPX[j];
    const dz = this.strandPZ[i] - this.strandPZ[j];
    const d = Math.hypot(dx, dz);
    if (d <= len || d === 0) return;
    const k = len / d;
    this.strandPX[i] = this.strandPX[j] + dx * k;
    this.strandPZ[i] = this.strandPZ[j] + dz * k;
  }

  private stepPet(h: number, active: boolean): void {
    const zc = this.intakeCenterZ;
    for (let c = 0; c < MAX_CLUMPS; c++) {
      if (!this.clumpAlive[c]) continue;
      const base = c * MAX_FIBERS_PER_CLUMP;
      if (this.clumpCaptured[c] && !active) this.clumpCaptured[c] = 0;
      if (this.clumpCaptured[c]) {
        const ax = this.worldX(this.clumpAttachLx[c], zc);
        const az = this.worldZ(this.clumpAttachLx[c], zc);
        for (let f = 0; f < MAX_FIBERS_PER_CLUMP; f++) {
          const idx = base + f;
          if (!this.fibAlive[idx]) continue;
          if (this.fibDelay[idx] > 0) {
            this.fibDelay[idx] -= h;
            this.fibStretch[idx] += (1.3 - this.fibStretch[idx]) * Math.min(1, 10 * h);
            continue;
          }
          const v = (this.fibV[idx] = Math.min(0.9, this.fibV[idx] + 4 * h));
          const dx = ax - this.fibX[idx];
          const dz = az - this.fibZ[idx];
          const d = Math.hypot(dx, dz) || 1e-6;
          const stepLen = Math.min(d, v * h);
          this.fibX[idx] += (dx / d) * stepLen;
          this.fibZ[idx] += (dz / d) * stepLen;
          // fibers trail away from the intake while being drawn in
          const trail = Math.atan2(-dz, -dx);
          this.fibAng[idx] += wrapAngle(trail - this.fibAng[idx]) * Math.min(1, 9 * h);
          this.fibStretch[idx] += (1.6 - this.fibStretch[idx]) * Math.min(1, 8 * h);
          if (d <= v * h || this.inIntake(this.localX(this.fibX[idx], this.fibZ[idx]), this.localZ(this.fibX[idx], this.fibZ[idx]))) {
            this.ingestFiber(idx);
            if (!this.clumpAlive[c]) break;
          }
        }
        this.fibHashDirty = true;
        this.petVersion++;
      } else if (this.clumpNear[c] && active) {
        // loosen/elongate and drift slightly toward the intake
        const nzz = this.nozzle;
        const hw = nzz.intakeWidth / 2;
        for (let f = 0; f < MAX_FIBERS_PER_CLUMP; f++) {
          const idx = base + f;
          if (!this.fibAlive[idx]) continue;
          this.fibStretch[idx] += (1.25 - this.fibStretch[idx]) * Math.min(1, 6 * h);
          const lx = this.localX(this.fibX[idx], this.fibZ[idx]);
          const lz = this.localZ(this.fibX[idx], this.fibZ[idx]);
          const tx = Math.max(-hw, Math.min(hw, lx));
          const tz = Math.max(nzz.intakeZMin, Math.min(nzz.intakeZMax, lz));
          const dx = this.worldX(tx, tz) - this.fibX[idx];
          const dz = this.worldZ(tx, tz) - this.fibZ[idx];
          const d = Math.hypot(dx, dz);
          if (d > 1e-6) {
            const m = Math.min(d, 0.03 * h);
            this.fibX[idx] += (dx / d) * m;
            this.fibZ[idx] += (dz / d) * m;
          }
        }
        this.fibHashDirty = true;
        this.petVersion++;
      } else {
        // relax back toward rest length
        let moved = false;
        for (let f = 0; f < MAX_FIBERS_PER_CLUMP; f++) {
          const idx = base + f;
          if (!this.fibAlive[idx] || this.fibStretch[idx] === 1) continue;
          const sNew = this.fibStretch[idx] + (1 - this.fibStretch[idx]) * Math.min(1, 2 * h);
          this.fibStretch[idx] = Math.abs(sNew - 1) < 1e-3 ? 1 : sNew;
          moved = true;
        }
        if (moved) this.petVersion++;
      }
    }
  }

  private stepMotes(h: number, active: boolean): void {
    const cap = this.quality === 'high' ? MAX_MOTES : MOTES_BALANCED;
    // update
    let alive = 0;
    for (let m = 0; m < MAX_MOTES; m++) {
      if (!this.moteAlive[m]) continue;
      this.moteLife[m] += h;
      if (this.moteLife[m] >= this.moteMaxLife[m]) {
        this.moteAlive[m] = 0;
        continue;
      }
      this.moteVY[m] -= 0.25 * h; // light settling
      const dmp = Math.exp(-3 * h);
      this.moteVX[m] *= dmp;
      this.moteVZ[m] *= dmp;
      this.moteX[m] += this.moteVX[m] * h;
      this.moteY[m] = Math.max(0.0008, this.moteY[m] + this.moteVY[m] * h);
      this.moteZ[m] += this.moteVZ[m] * h;
      alive++;
    }
    // spawn in proportion to dust actually removed (sparse: ~5 per MU, max 3 per step)
    if (active && this.dustRemovedPending > 0) {
      const rng = this.rng;
      let want = this.dustRemovedPending * 5;
      this.dustRemovedPending = 0;
      let n = Math.floor(want);
      if (rng.next() < want - n) n++;
      if (n > 3) n = 3;
      const nz = this.nozzle;
      for (let m = 0; m < MAX_MOTES && n > 0 && alive < cap; m++) {
        if (this.moteAlive[m]) continue;
        const lx = rng.range(-nz.intakeWidth / 2, nz.intakeWidth / 2) * 0.95;
        const lz = nz.intakeZMax + rng.range(0.004, 0.02);
        this.moteX[m] = this.worldX(lx, lz);
        this.moteZ[m] = this.worldZ(lx, lz);
        this.moteY[m] = rng.range(0.002, 0.012);
        // drift toward the intake (local −Z) and slightly up
        const sp = rng.range(0.03, 0.12);
        this.moteVX[m] = -this.ps * sp + rng.gauss() * 0.015;
        this.moteVZ[m] = -this.pc * sp + rng.gauss() * 0.015;
        this.moteVY[m] = rng.range(0.01, 0.06);
        this.moteLife[m] = 0;
        this.moteMaxLife[m] = rng.range(0.25, 0.7);
        this.moteAlive[m] = 1;
        alive++;
        n--;
      }
    } else if (!active) this.dustRemovedPending = 0;
    this.moteCount = alive;
  }

  private updateUnderShell(pose: HeadPose): void {
    this.setPose(pose);
    for (let i = 0; i < this.crumbHigh; i++) {
      if (!this.crumbAlive[i]) continue;
      const lx = this.localX(this.crumbX[i], this.crumbZ[i]);
      const lz = this.localZ(this.crumbX[i], this.crumbZ[i]);
      const under = this.inShell(lx, lz, this.crumbSize[i] * 0.5);
      const f = this.crumbFlags[i];
      const nf = under ? f | CRUMB_UNDER_SHELL : f & ~CRUMB_UNDER_SHELL;
      if (nf !== f) {
        this.crumbFlags[i] = nf;
        this.crumbVersion++;
      }
    }
  }

  // =====================================================================================
  // Queries
  // =====================================================================================

  getAccounting(): MassAccounting {
    let a = 0;
    let c = 0;
    let r = 0;
    for (let k = 0; k < 4; k++) {
      a += this.added[k];
      c += this.collected[k];
      r += Math.max(0, this.remaining[k]);
    }
    return { added: a, collected: c, remaining: r };
  }

  /** Per-kind accounting (diagnostics/tests). */
  getKindAccounting(kind: BaseDirtKind): MassAccounting {
    const k = KIND_NAMES.indexOf(kind);
    return { added: this.added[k], collected: this.collected[k], remaining: Math.max(0, this.remaining[k]) };
  }

  /** Recompute remaining mass from the raw state (independent of the running sums). */
  recomputeRemaining(): number {
    let dust = 0;
    for (let k = 0; k < this.dust.length; k++) dust += this.dust[k];
    let total = dust * this.cellMass;
    for (let i = 0; i < this.crumbHigh; i++) if (this.crumbAlive[i]) total += this.crumbMassArr[i];
    for (let s = 0; s < MAX_STRANDS; s++) {
      if (!this.strandAlive[s]) continue;
      const base = s * MAX_STRAND_POINTS;
      for (let p = 0; p < this.strandN[s]; p++) if (this.strandPointLive[base + p]) total += this.strandPointMass[s];
    }
    for (let f = 0; f < this.fibAlive.length; f++) if (this.fibAlive[f]) total += PET_FIBER_MASS;
    return total;
  }

  getRemainingFraction(): number {
    const a = this.getAccounting();
    if (a.added <= 0) return 0;
    return Math.min(1, Math.max(0, a.remaining / a.added));
  }

  getLocalDensity(pose: HeadPose): number {
    this.rebuildHashes();
    this.setPose(pose);
    const nz = this.nozzle;
    const hw = nz.intakeWidth / 2;
    const z0 = nz.intakeZMin;
    const z1 = nz.intakeZMax + 0.04;
    let sum = 0;
    const NX = 12;
    const NZ = 6;
    for (let a = 0; a < NX; a++) {
      const lx = -hw + ((a + 0.5) / NX) * 2 * hw;
      for (let b = 0; b < NZ; b++) {
        const lz = z0 + ((b + 0.5) / NZ) * (z1 - z0);
        sum += this.dustAt(this.worldX(lx, lz), this.worldZ(lx, lz));
      }
    }
    let score = (sum / (NX * NZ)) * 2.5;
    this.localRectAabb(-hw, z0, hw, z1);
    const buf = this.gatherBuf;
    let cnt = this.crumbHash.gather(this.aabb[0], this.aabb[1], this.aabb[2], this.aabb[3], buf);
    for (let q = 0; q < cnt; q++) {
      const i = buf[q];
      if (!this.crumbAlive[i]) continue;
      const lx = this.localX(this.crumbX[i], this.crumbZ[i]);
      const lz = this.localZ(this.crumbX[i], this.crumbZ[i]);
      if (lx >= -hw && lx <= hw && lz >= z0 && lz <= z1) score += 0.06;
    }
    cnt = this.hairHash.gather(this.aabb[0], this.aabb[1], this.aabb[2], this.aabb[3], buf);
    for (let q = 0; q < cnt; q++) {
      const i = buf[q];
      if (!this.strandPointLive[i]) continue;
      const lx = this.localX(this.strandPX[i], this.strandPZ[i]);
      const lz = this.localZ(this.strandPX[i], this.strandPZ[i]);
      if (lx >= -hw && lx <= hw && lz >= z0 && lz <= z1) score += 0.025;
    }
    cnt = this.fibHash.gather(this.aabb[0], this.aabb[1], this.aabb[2], this.aabb[3], buf);
    for (let q = 0; q < cnt; q++) {
      const i = buf[q];
      if (!this.fibAlive[i]) continue;
      const lx = this.localX(this.fibX[i], this.fibZ[i]);
      const lz = this.localZ(this.fibX[i], this.fibZ[i]);
      if (lx >= -hw && lx <= hw && lz >= z0 && lz <= z1) score += 0.008;
    }
    return Math.min(1, score);
  }

  drainPickups(): PickupEvent[] {
    const out: PickupEvent[] = this.crumbEvents;
    this.crumbEvents = [];
    for (let k = 0; k < 4; k++) {
      if (this.pendingPickup[k] > 0) {
        out.push({ kind: KIND_NAMES[k], mass: this.pendingPickup[k] });
        this.pendingPickup[k] = 0;
      }
    }
    return out;
  }

  setQuality(tier: QualityTier): void {
    // Representation only: logical caps are tier-independent; only the visual mote cap follows the tier.
    this.quality = tier;
  }

  setSurface(surface: SurfaceKind): void {
    this.surface = surface;
  }

  isFull(kind: BaseDirtKind): boolean {
    switch (kind) {
      case 'dust':
        return this.remaining[K_DUST] >= DUST_MASS_CAP * 0.995;
      case 'crumbs':
        return this.crumbCount >= MAX_CRUMBS;
      case 'hair':
        return this.strandCount >= MAX_STRANDS;
      case 'pet':
        return this.clumpCount >= MAX_CLUMPS;
    }
  }

  /** Last pose passed to step() (for renderers), or null before the first step. */
  getLastPose(): HeadPose | null {
    return this.hasLastPose ? this.lastPose : null;
  }
}
