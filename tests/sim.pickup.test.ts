import { describe, expect, it } from 'vitest';
import type { HeadPose } from '../src/contracts/world';
import { worldToHeadLocal } from '../src/contracts/world';
import { ATTRACT_BAND, MAX_STRAND_POINTS } from '../src/simulation/constants';
import { definitelySweptCells, invariantError, lerpPose, makeSim, snapshot, untouchableCell } from './simHelpers';

const STROKE_FILL = (sim: ReturnType<typeof makeSim>) => sim.fillDustRect(-0.55, -0.45, 0.55, 0.45, 0.2);

function strokeInFrames(sim: ReturnType<typeof makeSim>, from: HeadPose, to: HeadPose, frames: number, dt: number, active = true) {
  let prev = from;
  for (let f = 1; f <= frames; f++) {
    const next = lerpPose(from, to, f / frames);
    sim.step(dt, prev, next, active);
    prev = next;
  }
}

describe('sim: swept pickup', () => {
  it('slow and very fast forward strokes leave no tunneling gaps', () => {
    const from = { x: 0, z: 0.3, yaw: 0 };
    const to = { x: 0, z: -0.3, yaw: 0 }; // forward (yaw 0 front = −Z)
    for (const frames of [120, 1]) {
      const sim = makeSim();
      STROKE_FILL(sim);
      strokeInFrames(sim, from, to, frames, 1 / 60);
      const cells = definitelySweptCells(sim, from, to);
      expect(cells.length).toBeGreaterThan(1000);
      const dirty = cells.filter((k) => sim.dust[k] > 0);
      expect(dirty.length, `frames=${frames}`).toBe(0);
    }
  });

  it('fast sideways and rotating strokes (yaw changes inside one frame) leave no gaps', () => {
    const paths: [HeadPose, HeadPose][] = [
      [{ x: -0.25, z: 0, yaw: 0 }, { x: 0.25, z: 0.05, yaw: 0 }],
      [{ x: -0.2, z: 0.15, yaw: 0.2 }, { x: 0.2, z: -0.1, yaw: 1.4 }],
      [{ x: 0.1, z: 0, yaw: -2.5 }, { x: 0.1, z: 0, yaw: 2.9 }], // pure rotation across ±π
    ];
    for (const [from, to] of paths) {
      const sim = makeSim();
      STROKE_FILL(sim);
      sim.step(1 / 30, from, to, true);
      const cells = definitelySweptCells(sim, from, to);
      const dirty = cells.filter((k) => sim.dust[k] > 0);
      expect(dirty.length).toBe(0);
    }
  });

  it('dirt outside the swept intake region is unchanged (dust, crumbs, hair, pet hair)', () => {
    const sim = makeSim(11);
    STROKE_FILL(sim);
    // discrete debris well away from the path (outside band + shell): left and right of the stroke
    for (const x of [-0.42, 0.42]) {
      sim.addScatter('crumbs', 'heavy', x, 0);
      sim.addScatter('hair', 'medium', x, -0.2);
      sim.addScatter('pet', 'medium', x, 0.2);
    }
    sim.step(0.5, { x: 0, z: 0, yaw: 0 }, { x: 0, z: 0, yaw: 0 }, false); // let crumbs settle
    const before = snapshot(sim);
    const from = { x: 0, z: 0.35, yaw: 0 };
    const to = { x: 0, z: -0.35, yaw: 0 };
    strokeInFrames(sim, from, to, 40, 1 / 60);
    for (let k = 0; k < 30; k++) sim.step(1 / 60, to, to, true);
    const after = snapshot(sim);
    // dust cells outside the grown footprint are bit-identical
    let checked = 0;
    for (let j = 0; j < sim.fieldH; j += 3)
      for (let i = 0; i < sim.fieldW; i += 3) {
        if (!untouchableCell(sim, from, to, i, j, 60)) continue;
        checked++;
        const k = j * sim.fieldW + i;
        if (after.dust[k] !== before.dust[k]) throw new Error(`cell ${i},${j} changed`);
      }
    expect(checked).toBeGreaterThan(5000);
    expect(after.crumbs).toEqual(before.crumbs);
    expect(after.hair).toEqual(before.hair);
    expect(after.pet).toEqual(before.pet);
  });

  it('attraction is a narrow band: crumbs 2.5 cm+ outside the intake never move', () => {
    const sim = makeSim(3);
    const pose = { x: 0, z: 0, yaw: 0 };
    const n = sim.nozzle;
    // world positions for local points: yaw 0 → world z = −lz, world x = −lx
    const inside = { x: 0, z: -(n.intakeZMax + ATTRACT_BAND * 0.5) }; // in the band, in front
    const outside = { x: 0, z: -(n.shellZMax + 0.03) }; // 3 cm beyond the shell front
    sim.addScatter('crumbs', 'light', inside.x, inside.z);
    const nBand = sim.crumbCount;
    sim.addScatter('crumbs', 'light', outside.x, outside.z);
    sim.step(0.3, pose, pose, false);
    const before = snapshot(sim);
    const far = Object.entries(before.crumbs).filter(([, [x, z]]) => {
      const l = worldToHeadLocal(pose, x, z);
      return l.lz > n.intakeZMax + ATTRACT_BAND + 0.005 || Math.abs(l.lx) > n.intakeWidth / 2 + ATTRACT_BAND + 0.005;
    });
    expect(far.length).toBeGreaterThan(0);
    for (let k = 0; k < 120; k++) sim.step(1 / 60, pose, pose, true);
    const after = snapshot(sim);
    for (const [id, pos] of far) expect(after.crumbs[Number(id)]).toEqual(pos);
    // crumbs in the band were drawn in and collected
    expect(sim.getKindAccounting('crumbs').collected).toBeGreaterThan(0);
    expect(nBand).toBeGreaterThan(0);
  });

  it('reverse (backward) strokes collect through the intake as well', () => {
    const sim = makeSim(5);
    STROKE_FILL(sim);
    sim.addScatter('crumbs', 'heavy', 0, 0);
    sim.addScatter('hair', 'heavy', 0, 0.05);
    sim.addScatter('pet', 'heavy', 0, -0.05);
    sim.step(0.5, { x: 0, z: -0.3, yaw: 0 }, { x: 0, z: -0.3, yaw: 0 }, false);
    const from = { x: 0, z: -0.3, yaw: 0 };
    const to = { x: 0, z: 0.35, yaw: 0 }; // moving toward +Z = backwards for yaw 0
    strokeInFrames(sim, from, to, 50, 1 / 60);
    for (let k = 0; k < 60; k++) sim.step(1 / 60, to, to, true);
    const dirty = definitelySweptCells(sim, from, to).filter((k) => sim.dust[k] > 0);
    expect(dirty.length).toBe(0);
    // every crumb whose centre lay on the swept path is gone
    for (let i = 0; i < sim.crumbHigh; i++) {
      if (!sim.crumbAlive[i]) continue;
      expect(Math.abs(sim.crumbX[i])).toBeGreaterThan(sim.nozzle.intakeWidth / 2 - 0.001);
    }
    expect(sim.getKindAccounting('crumbs').collected).toBeGreaterThan(0);
    expect(sim.getKindAccounting('hair').collected).toBeGreaterThan(0);
    expect(sim.getKindAccounting('pet').collected).toBeGreaterThan(0);
  });

  it('pickupActive = false never removes or collects anything', () => {
    const sim = makeSim(9);
    sim.addPreset(42);
    sim.step(0.5, { x: 0, z: 0, yaw: 0 }, { x: 0, z: 0, yaw: 0 }, false);
    const acc0 = sim.getAccounting();
    const before = snapshot(sim);
    let t = 0;
    let prev: HeadPose = { x: -0.5, z: -0.4, yaw: 0 };
    for (let f = 0; f < 600; f++) {
      t += 1 / 60;
      const next = { x: Math.sin(t * 1.3) * 0.6, z: Math.cos(t * 0.9) * 0.45, yaw: t * 0.7 };
      sim.step(1 / 60, prev, next, false);
      prev = next;
    }
    const acc1 = sim.getAccounting();
    expect(acc1.collected).toBe(0);
    expect(acc1.remaining).toBe(acc0.remaining);
    expect(sim.drainPickups().length).toBe(0);
    const after = snapshot(sim);
    expect(after.dust).toEqual(before.dust);
    expect(Object.keys(after.crumbs)).toEqual(Object.keys(before.crumbs));
    expect(after.hair).toEqual(before.hair);
    expect(after.pet).toEqual(before.pet);
  });

  it('a captured hair strand feeds in over several steps; mass leaves only as it is ingested', () => {
    const sim = makeSim(21);
    sim.addScatter('hair', 'light', 0, 0);
    expect(sim.strandCount).toBeGreaterThanOrEqual(1);
    const s = sim.strandAlive.indexOf(1);
    const base = s * MAX_STRAND_POINTS;
    const n = sim.strandN[s];
    // place the head so that only point 0 of strand s is just inside the intake front edge
    const px = sim.strandPX[base];
    const pz = sim.strandPZ[base];
    let pose: HeadPose | null = null;
    for (let yi = 0; yi < 64 && !pose; yi++) {
      const yaw = (yi / 64) * Math.PI * 2;
      const lz = sim.nozzle.intakeZMax - 0.003;
      const c = Math.cos(yaw + Math.PI);
      const sn = Math.sin(yaw + Math.PI);
      const cand = { x: px - lz * sn, z: pz - lz * c, yaw };
      let othersInside = 0;
      for (let p = 1; p < n; p++) {
        const l = worldToHeadLocal(cand, sim.strandPX[base + p], sim.strandPZ[base + p]);
        if (Math.abs(l.lx) <= sim.nozzle.intakeWidth / 2 && l.lz >= sim.nozzle.intakeZMin && l.lz <= sim.nozzle.intakeZMax) othersInside++;
      }
      if (othersInside === 0) pose = cand;
    }
    expect(pose).not.toBeNull();
    const live = () => {
      let c = 0;
      for (let p = 0; p < n; p++) c += sim.strandPointLive[base + p];
      return sim.strandAlive[s] ? c : 0;
    };
    const series: number[] = [];
    for (let k = 0; k < 240 && live() > 0; k++) {
      sim.step(1 / 120, pose!, pose!, true);
      series.push(live());
    }
    expect(live()).toBe(0);
    // gradual: point 0 captured first, then the rest fed in over many steps (≈ length / feed speed)
    expect(series[0]).toBe(n - 1);
    expect(series.length).toBeGreaterThan(4);
    for (let k = 1; k < series.length; k++) expect(series[k]).toBeLessThanOrEqual(series[k - 1]);
    expect(invariantError(sim)).toBeLessThan(1e-9);
  });

  it('releasing pickup mid-feed leaves the uncaptured part of the strand on the floor', () => {
    const sim = makeSim(21);
    sim.addScatter('hair', 'light', 0, 0);
    const s = sim.strandAlive.indexOf(1);
    const base = s * MAX_STRAND_POINTS;
    const pose = { x: sim.strandPX[base], z: sim.strandPZ[base] + 0.02, yaw: 0 };
    sim.step(1 / 120, pose, pose, true);
    sim.step(1 / 120, pose, pose, false);
    const left = sim.getKindAccounting('hair').remaining;
    for (let k = 0; k < 60; k++) sim.step(1 / 60, pose, pose, false);
    expect(sim.getKindAccounting('hair').remaining).toBe(left);
  });
});

describe('sim: frame-rate consistency', () => {
  const path = (t: number): HeadPose => ({
    x: -0.45 + 0.9 * (t / 3) + 0.08 * Math.sin(t * 4),
    z: 0.25 * Math.sin(t * 2.2),
    yaw: 0.6 * Math.sin(t * 1.7),
  });

  function run(hz: number) {
    const sim = makeSim(77);
    sim.addPreset(1234);
    sim.step(0.5, path(0), path(0), false); // settle
    const dt = 1 / hz;
    const frames = Math.round(3 * hz);
    let prev = path(0);
    for (let f = 1; f <= frames; f++) {
      const next = path(f * dt);
      sim.step(dt, prev, next, true);
      prev = next;
    }
    // let in-flight items finish at the end pose
    for (let k = 0; k < Math.round(0.5 * hz); k++) sim.step(dt, prev, prev, true);
    return sim;
  }

  it('the same trajectory at 30 / 60 / 144 Hz collects nearly the same mass', () => {
    const r = [30, 60, 144].map(run);
    const c = r.map((s) => s.getAccounting().collected);
    expect(c[0]).toBeGreaterThan(5);
    for (const v of c) expect(Math.abs(v - c[1]) / c[1]).toBeLessThan(0.02);
    // dust is geometric → essentially identical
    const d = r.map((s) => s.getKindAccounting('dust').collected);
    for (const v of d) expect(Math.abs(v - d[1]) / d[1]).toBeLessThan(0.002);
  });
});
