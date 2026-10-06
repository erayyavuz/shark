import { describe, expect, it } from 'vitest';
import { MotionController } from '../src/interaction/MotionController';
import { ACTIVE, MOTION } from '../src/config/tuning';
import { Timeline } from '../src/app/timeline';

const wrap = (a: number) => Math.atan2(Math.sin(a), Math.cos(a));

function run(m: MotionController, seconds: number, frameDt: number, path: (t: number) => { x: number; z: number }) {
  let t = 0;
  const trace: { x: number; z: number; yaw: number }[] = [];
  while (t < seconds) {
    const p = path(t);
    m.target.x = p.x;
    m.target.z = p.z;
    m.update(frameDt);
    t += frameDt;
    trace.push({ ...m.pose });
  }
  return trace;
}

describe('MotionController', () => {
  it('never teleports: per-step displacement is bounded by max speed', () => {
    const m = new MotionController();
    m.reset(0, 0, ACTIVE.yaw);
    m.target = { x: 0.7, z: 0.5, active: true };
    let prev = { ...m.pose };
    for (let i = 0; i < 240; i++) {
      m.update(1 / 60);
      const d = Math.hypot(m.pose.x - prev.x, m.pose.z - prev.z);
      expect(d).toBeLessThanOrEqual(MOTION.maxSpeed / 60 + 1e-6);
      prev = { ...m.pose };
    }
    expect(Math.hypot(m.pose.x - 0.7, m.pose.z - 0.5)).toBeLessThan(0.01);
  });

  it('reverse strokes do not spin the head around', () => {
    const m = new MotionController();
    m.reset(0, 0, ACTIVE.yaw);
    const fx = -Math.sin(ACTIVE.yaw);
    const fz = -Math.cos(ACTIVE.yaw);
    // forward, then straight back along the same line, repeatedly
    const trace = run(m, 4, 1 / 60, (t) => {
      const s = Math.sin(t * Math.PI) * 0.3;
      return { x: fx * s, z: fz * s };
    });
    for (const p of trace) expect(Math.abs(wrap(p.yaw - ACTIVE.yaw))).toBeLessThan(0.35);
  });

  it('yaw stays inside the allowed range for lateral sweeps', () => {
    const m = new MotionController();
    m.reset(0, 0, ACTIVE.yaw);
    const trace = run(m, 6, 1 / 60, (t) => ({ x: Math.sin(t * 2) * 0.6, z: Math.cos(t * 1.3) * 0.4 }));
    for (const p of trace) expect(Math.abs(wrap(p.yaw - ACTIVE.yaw))).toBeLessThanOrEqual(ACTIVE.yawRange + 1e-6);
  });

  it('is frame-rate independent (30 / 60 / 144 Hz end within 1 cm)', () => {
    const path = (t: number) => ({ x: Math.sin(t * 1.7) * 0.4, z: Math.sin(t * 1.1) * 0.3 });
    const ends = [1 / 30, 1 / 60, 1 / 144].map((dt) => {
      const m = new MotionController();
      m.reset(0, 0, ACTIVE.yaw);
      const tr = run(m, 3, dt, path);
      return tr[tr.length - 1];
    });
    for (const e of ends) expect(Math.hypot(e.x - ends[1].x, e.z - ends[1].z)).toBeLessThan(0.01);
  });

  it('caps catch-up work after a long hitch', () => {
    const m = new MotionController();
    m.reset(0, 0, ACTIVE.yaw);
    m.target = { x: 0.5, z: 0, active: true };
    const steps = m.update(5);
    expect(steps).toBeLessThanOrEqual(MOTION.maxCatchUpSteps);
  });
});

describe('Timeline', () => {
  it('finish() fires every cue exactly once and completes once', () => {
    let cues = 0;
    let done = 0;
    const tl = new Timeline(2, () => done++);
    tl.cue(0.5, () => cues++).cue(1.5, () => cues++);
    tl.advance(0.6);
    tl.finish();
    tl.finish();
    tl.advance(5);
    expect(cues).toBe(2);
    expect(done).toBe(1);
  });

  it('cancel() never completes', () => {
    let done = 0;
    const tl = new Timeline(1, () => done++);
    tl.cancel();
    tl.advance(2);
    expect(done).toBe(0);
  });
});
