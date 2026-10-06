import { describe, expect, it } from 'vitest';
import type { HeadPose } from '../src/contracts/world';
import { DUST_MASS_CAP, MAX_CLUMPS, MAX_CRUMBS, MAX_STRANDS } from '../src/simulation/constants';
import { DirtRenderer } from '../src/simulation/render/DirtRenderer';
import { invariantError, makeSim, snapshot } from './simHelpers';

const TOL = (added: number) => 1e-6 * Math.max(1, added);

describe('sim: accounting', () => {
  it('added ≈ collected + remaining through deposit, pickup, more deposit and reset', () => {
    const sim = makeSim(4);
    expect(sim.getRemainingFraction()).toBe(0); // empty state
    const kinds = ['dust', 'hair', 'pet', 'crumbs', 'mixed'] as const;
    let ret = 0;
    for (const k of kinds) ret += sim.addScatter(k, 'heavy', -0.2, 0.1);
    ret += sim.addStroke('mixed', 'medium', -0.4, -0.3, 0.4, -0.2, 1 / 60);
    ret += sim.addPreset(9);
    const a0 = sim.getAccounting();
    expect(a0.added).toBeCloseTo(ret, 6);
    expect(a0.remaining).toBeCloseTo(sim.recomputeRemaining(), 6);
    expect(invariantError(sim)).toBeLessThan(TOL(a0.added));

    let prev: HeadPose = { x: -0.6, z: -0.4, yaw: 0 };
    let t = 0;
    for (let f = 0; f < 400; f++) {
      t += 1 / 60;
      const next = { x: -0.6 + 1.2 * (f / 400), z: 0.4 * Math.sin(t * 3), yaw: 0.4 * Math.sin(t) };
      sim.step(1 / 60, prev, next, true);
      prev = next;
      if (f % 50 === 0) {
        expect(invariantError(sim)).toBeLessThan(TOL(sim.getAccounting().added));
        expect(sim.getAccounting().remaining).toBeCloseTo(sim.recomputeRemaining(), 6);
      }
    }
    const a1 = sim.getAccounting();
    expect(a1.collected).toBeGreaterThan(0);
    expect(a1.added).toBe(a0.added);
    // pickup events add up to collected
    const ev = sim.drainPickups().reduce((s, e) => s + e.mass, 0);
    expect(ev).toBeCloseTo(a1.collected, 6);
    expect(sim.getRemainingFraction()).toBeCloseTo(a1.remaining / a1.added, 9);

    sim.addScatter('mixed', 'heavy', 0.3, 0.3);
    expect(invariantError(sim)).toBeLessThan(TOL(sim.getAccounting().added));

    sim.clearFloor();
    expect(sim.getAccounting()).toEqual({ added: 0, collected: 0, remaining: 0 });
    expect(sim.recomputeRemaining()).toBe(0);
    expect(sim.drainPickups().length).toBe(0); // reset is not "vacuumed"
    expect(sim.getRemainingFraction()).toBe(0);
  });

  it('cleaning everything reachable drives the remaining fraction below 0.5 %', () => {
    const sim = makeSim(8);
    sim.addPreset(31);
    const a = sim.area;
    let prev: HeadPose = { x: a.minX, z: a.minZ, yaw: 0 };
    // boustrophedon passes over the whole play area (head centre can reach the area bounds)
    const lanes = 14;
    for (let l = 0; l <= lanes; l++) {
      const x = a.minX + ((a.maxX - a.minX) * l) / lanes;
      const z0 = l % 2 ? a.maxZ : a.minZ;
      const z1 = l % 2 ? a.minZ : a.maxZ;
      const start = { x, z: z0, yaw: 0 };
      sim.step(1 / 60, prev, start, false);
      prev = start;
      for (let f = 1; f <= 60; f++) {
        const next = { x, z: z0 + ((z1 - z0) * f) / 60, yaw: 0 };
        sim.step(1 / 60, prev, next, true);
        prev = next;
      }
      for (let k = 0; k < 20; k++) sim.step(1 / 60, prev, prev, true);
    }
    expect(sim.getRemainingFraction()).toBeLessThan(0.005);
    expect(invariantError(sim)).toBeLessThan(TOL(sim.getAccounting().added));
  });
});

describe('sim: budgets', () => {
  it('caps stop adding gracefully and never evict existing items', () => {
    const sim = makeSim(12);
    sim.addScatter('crumbs', 'heavy', 0, 0);
    sim.addScatter('hair', 'heavy', 0.2, 0);
    sim.addScatter('pet', 'heavy', -0.2, 0);
    const first = snapshot(sim);
    let guard = 0;
    while (!(sim.isFull('crumbs') && sim.isFull('hair') && sim.isFull('pet') && sim.isFull('dust')) && guard++ < 4000) {
      sim.addStroke('mixed', 'heavy', -0.6, -0.4 + (guard % 9) * 0.1, 0.6, -0.4 + (guard % 7) * 0.12, 0.1);
      sim.addScatter('crumbs', 'heavy', -0.5 + (guard % 11) * 0.1, 0);
    }
    expect(sim.isFull('crumbs')).toBe(true);
    expect(sim.isFull('hair')).toBe(true);
    expect(sim.isFull('pet')).toBe(true);
    expect(sim.isFull('dust')).toBe(true);
    expect(sim.crumbCount).toBe(MAX_CRUMBS);
    expect(sim.strandCount).toBe(MAX_STRANDS);
    expect(sim.clumpCount).toBe(MAX_CLUMPS);
    expect(sim.getKindAccounting('dust').remaining).toBeLessThan(DUST_MASS_CAP * 1.01);
    // further additions add nothing
    const before = sim.getAccounting();
    expect(sim.addScatter('crumbs', 'heavy', 0.1, 0.1)).toBe(0);
    expect(sim.addScatter('hair', 'heavy', 0.1, 0.1)).toBe(0);
    expect(sim.addScatter('pet', 'heavy', 0.1, 0.1)).toBe(0);
    expect(sim.addScatter('dust', 'heavy', 0.1, 0.1)).toBe(0);
    expect(sim.getAccounting()).toEqual(before);
    // the very first items are all still present, unmoved
    const now = snapshot(sim);
    for (const id of Object.keys(first.crumbs)) expect(now.crumbs[Number(id)]).toBeDefined();
    for (const id of Object.keys(first.hair)) expect(now.hair[Number(id)]).toEqual(first.hair[Number(id)]);
    for (const id of Object.keys(first.pet)) expect(now.pet[Number(id)]).toEqual(first.pet[Number(id)]);
    expect(invariantError(sim)).toBeLessThan(TOL(sim.getAccounting().added));
    // collecting frees budget again
    const p = { x: 0, z: 0, yaw: 0 };
    sim.step(1 / 60, p, { x: 0, z: -0.1, yaw: 0 }, true);
    expect(sim.isFull('crumbs')).toBe(false);
  });
});

describe('sim: quality switching', () => {
  it('switching quality (sim and renderer) keeps logical mass, IDs and positions', () => {
    const sim = makeSim(19);
    sim.addPreset(5);
    const rest = { x: sim.area.maxX, z: sim.area.maxZ, yaw: 0 };
    sim.step(0.5, rest, rest, false);
    const r = new DirtRenderer(sim, { quality: 'high' });
    r.sync(0);
    const acc = sim.getAccounting();
    const snap = snapshot(sim);
    for (const tier of ['balanced', 'high', 'balanced'] as const) {
      sim.setQuality(tier);
      r.setQuality(tier);
      r.sync(1);
      sim.step(1 / 60, rest, rest, false);
      expect(sim.getAccounting()).toEqual(acc);
      expect(snapshot(sim)).toEqual(snap);
    }
    r.setSurface('carpet');
    sim.setSurface('carpet');
    r.sync(2);
    expect(snapshot(sim)).toEqual(snap);
    r.dispose();
  });
});
