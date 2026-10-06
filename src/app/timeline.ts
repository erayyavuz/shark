/** Minimal explicit timeline — the single animation owner for camera/rig transitions. */
export type Ease = (t: number) => number;

export const easeInOutCubic: Ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
export const easeOutCubic: Ease = (t) => 1 - Math.pow(1 - t, 3);
export const easeInOutSine: Ease = (t) => -(Math.cos(Math.PI * t) - 1) / 2;
export const linear: Ease = (t) => t;

interface Track {
  start: number;
  duration: number;
  ease: Ease;
  update: (k: number) => void;
  begin?: () => void;
  started: boolean;
  done: boolean;
}

interface Cue {
  at: number;
  fn: () => void;
  fired: boolean;
}

export class Timeline {
  private tracks: Track[] = [];
  private cues: Cue[] = [];
  time = 0;
  private finished = false;
  constructor(public readonly duration: number, private onComplete?: () => void) {}

  tween(start: number, end: number, update: (k: number) => void, ease: Ease = easeInOutCubic, begin?: () => void) {
    this.tracks.push({ start, duration: Math.max(1e-4, end - start), ease, update, begin, started: false, done: false });
    return this;
  }

  cue(at: number, fn: () => void) {
    this.cues.push({ at, fn, fired: false });
    return this;
  }

  get isFinished() {
    return this.finished;
  }

  advance(dt: number) {
    if (this.finished) return;
    this.time += dt;
    for (const c of this.cues) {
      if (!c.fired && this.time >= c.at) {
        c.fired = true;
        c.fn();
      }
    }
    for (const t of this.tracks) {
      if (t.done || this.time < t.start) continue;
      if (!t.started) {
        t.started = true;
        t.begin?.();
      }
      const k = Math.min(1, (this.time - t.start) / t.duration);
      t.update(t.ease(k));
      if (k >= 1) t.done = true;
    }
    if (this.time >= this.duration) this.finish();
  }

  /** Jump to the end state of every track and fire every cue (used by Skip intro). */
  finish() {
    if (this.finished) return;
    for (const c of this.cues) {
      if (!c.fired) {
        c.fired = true;
        c.fn();
      }
    }
    for (const t of this.tracks) {
      if (!t.started) t.begin?.();
      if (!t.done) t.update(t.ease(1));
      t.started = t.done = true;
    }
    this.finished = true;
    this.onComplete?.();
  }

  /** Abandon without completing (used by Back / unmount). */
  cancel() {
    this.finished = true;
  }
}

export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export function lerpAngle(a: number, b: number, k: number) {
  let d = b - a;
  while (d > Math.PI) d -= Math.PI * 2;
  while (d < -Math.PI) d += Math.PI * 2;
  return a + d * k;
}
