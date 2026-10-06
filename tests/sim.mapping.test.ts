import { describe, expect, it } from 'vitest';
import { PLAY_AREA, fieldToWorld, worldToField, headLocalToWorld, worldToHeadLocal } from '../src/contracts/world';
import { makeSim } from './simHelpers';
import { DirtSimulation } from '../src/simulation/DirtSimulation';

describe('sim: world ↔ field mapping', () => {
  const sim = makeSim();
  const a = PLAY_AREA;

  it('field cells are square and cover the play area exactly', () => {
    expect(Math.max(sim.fieldW, sim.fieldH)).toBe(512);
    expect(Math.abs(sim.cellW - sim.cellH) / sim.cellW).toBeLessThan(0.01);
    expect(sim.cellW * sim.fieldW).toBeCloseTo(a.maxX - a.minX, 9);
    expect(sim.cellH * sim.fieldH).toBeCloseTo(a.maxZ - a.minZ, 9);
  });

  it('corners and centre map to the expected cells and agree with the contract worldToField', () => {
    const eps = 1e-6;
    const cases: [number, number, number, number][] = [
      [a.minX + eps, a.minZ + eps, 0, 0],
      [a.maxX - eps, a.minZ + eps, sim.fieldW - 1, 0],
      [a.minX + eps, a.maxZ - eps, 0, sim.fieldH - 1],
      [a.maxX - eps, a.maxZ - eps, sim.fieldW - 1, sim.fieldH - 1],
      [(a.minX + a.maxX) / 2 + eps, (a.minZ + a.maxZ) / 2 + eps, Math.floor(sim.fieldW / 2), Math.floor(sim.fieldH / 2)],
    ];
    for (const [x, z, ci, cj] of cases) {
      expect(sim.cellCol(x)).toBe(ci);
      expect(sim.cellRow(z)).toBe(cj);
      const uv = worldToField({ x, z });
      expect(Math.floor(uv.u * sim.fieldW)).toBe(ci);
      expect(Math.floor(uv.v * sim.fieldH)).toBe(cj);
      // cell centre round-trips through the contract helpers
      const w = fieldToWorld((ci + 0.5) / sim.fieldW, (cj + 0.5) / sim.fieldH);
      expect(sim.cellCenterX(ci)).toBeCloseTo(w.x, 9);
      expect(sim.cellCenterZ(cj)).toBeCloseTo(w.z, 9);
    }
  });

  it('portrait play areas get square-ish cells with the long side at 512', () => {
    const p = new DirtSimulation({ area: { minX: -0.45, maxX: 0.45, minZ: -0.55, maxZ: 0.55 }, seed: 1 });
    expect(p.fieldH).toBe(512);
    expect(Math.abs(p.cellW - p.cellH) / p.cellW).toBeLessThan(0.01);
    expect(p.cellCol(0.45 - 1e-6)).toBe(p.fieldW - 1);
  });

  it('a deposit lands in the cell under its world position', () => {
    const s = makeSim();
    s.fillDustRect(0.3, -0.2, 0.3, -0.2, 0.8);
    expect(s.dustAt(0.3, -0.2)).toBeCloseTo(0.8, 6);
    expect(s.dust[s.cellRow(-0.2) * s.fieldW + s.cellCol(0.3)]).toBeCloseTo(0.8, 6);
    expect(s.dustAt(-0.3, 0.2)).toBe(0);
  });

  it('head-local transforms: yaw 0 front faces world −Z, round trip is exact', () => {
    const p = { x: 0.1, z: -0.2, yaw: 0 };
    const f = headLocalToWorld(p, 0, 0.1);
    expect(f.x).toBeCloseTo(0.1, 9);
    expect(f.z).toBeCloseTo(-0.3, 9);
    const q = { x: -0.3, z: 0.25, yaw: 1.1 };
    const w = headLocalToWorld(q, 0.07, -0.03);
    const l = worldToHeadLocal(q, w.x, w.z);
    expect(l.lx).toBeCloseTo(0.07, 9);
    expect(l.lz).toBeCloseTo(-0.03, 9);
  });
});
