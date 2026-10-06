import { DirtSimulation } from '../src/simulation/DirtSimulation';
import { EDGE_JITTER, MAX_CLUMPS, MAX_FIBERS_PER_CLUMP, MAX_STRANDS, MAX_STRAND_POINTS } from '../src/simulation/constants';
import { PLAY_AREA, worldToHeadLocal, type HeadPose } from '../src/contracts/world';

export const makeSim = (seed = 7) => new DirtSimulation({ area: PLAY_AREA, seed });

export function lerpPose(a: HeadPose, b: HeadPose, t: number): HeadPose {
  let dy = b.yaw - a.yaw;
  while (dy > Math.PI) dy -= 2 * Math.PI;
  while (dy < -Math.PI) dy += 2 * Math.PI;
  return { x: a.x + (b.x - a.x) * t, z: a.z + (b.z - a.z) * t, yaw: a.yaw + dy * t };
}

/**
 * Cells that a continuous sweep from→to definitely covered (inside the intake rect shrunk by the edge
 * jitter + half a cell diagonal at some densely sampled pose). These must all be clean.
 */
export function definitelySweptCells(sim: DirtSimulation, from: HeadPose, to: HeadPose, samples = 2000): number[] {
  const n = sim.nozzle;
  const shrink = EDGE_JITTER + Math.hypot(sim.cellW, sim.cellH) * 0.5 + 1e-4;
  const hw = n.intakeWidth / 2 - shrink;
  const zMin = n.intakeZMin + shrink;
  const zMax = n.intakeZMax - shrink;
  const out = new Set<number>();
  for (let s = 0; s <= samples; s++) {
    const p = lerpPose(from, to, s / samples);
    const r = 0.2;
    const i0 = sim.cellCol(p.x - r);
    const i1 = sim.cellCol(p.x + r);
    const j0 = sim.cellRow(p.z - r);
    const j1 = sim.cellRow(p.z + r);
    for (let j = j0; j <= j1; j++)
      for (let i = i0; i <= i1; i++) {
        const l = worldToHeadLocal(p, sim.cellCenterX(i), sim.cellCenterZ(j));
        if (Math.abs(l.lx) <= hw && l.lz >= zMin && l.lz <= zMax) out.add(j * sim.fieldW + i);
      }
  }
  return [...out];
}

/** Cells that no pose of the sweep could touch (outside the rect grown by jitter + cell diagonal). */
export function untouchableCell(sim: DirtSimulation, from: HeadPose, to: HeadPose, i: number, j: number, samples = 400): boolean {
  const n = sim.nozzle;
  const grow = EDGE_JITTER + Math.hypot(sim.cellW, sim.cellH) + 1e-4;
  for (let s = 0; s <= samples; s++) {
    const p = lerpPose(from, to, s / samples);
    const l = worldToHeadLocal(p, sim.cellCenterX(i), sim.cellCenterZ(j));
    if (Math.abs(l.lx) <= n.intakeWidth / 2 + grow && l.lz >= n.intakeZMin - grow && l.lz <= n.intakeZMax + grow) return false;
  }
  return true;
}

/** Snapshot of every logical item position + the dust field. */
export function snapshot(sim: DirtSimulation) {
  const crumbs: Record<number, [number, number, number]> = {};
  for (let i = 0; i < sim.crumbHigh; i++) if (sim.crumbAlive[i]) crumbs[sim.crumbId[i]] = [sim.crumbX[i], sim.crumbZ[i], sim.crumbSize[i]];
  const hair: Record<number, number[]> = {};
  for (let s = 0; s < MAX_STRANDS; s++) {
    if (!sim.strandAlive[s]) continue;
    const pts: number[] = [];
    for (let p = 0; p < MAX_STRAND_POINTS; p++) {
      const k = s * MAX_STRAND_POINTS + p;
      if (sim.strandPointLive[k]) pts.push(p, sim.strandPX[k], sim.strandPZ[k]);
    }
    hair[sim.strandId[s]] = pts;
  }
  const pet: Record<number, number[]> = {};
  for (let c = 0; c < MAX_CLUMPS; c++) {
    if (!sim.clumpAlive[c]) continue;
    const f: number[] = [];
    for (let k = 0; k < MAX_FIBERS_PER_CLUMP; k++) {
      const idx = c * MAX_FIBERS_PER_CLUMP + k;
      if (sim.fibAlive[idx]) f.push(k, sim.fibX[idx], sim.fibZ[idx], sim.fibLen[idx] * sim.fibStretch[idx]);
    }
    pet[sim.clumpId[c]] = f;
  }
  return { dust: Float32Array.from(sim.dust), crumbs, hair, pet };
}

export function invariantError(sim: DirtSimulation): number {
  const a = sim.getAccounting();
  return Math.abs(a.added - a.collected - a.remaining);
}
