import { DPR_STEPS } from '../config/quality';

/**
 * Adapts pixel ratio from measured frame times with hysteresis + cooldown so quality never
 * oscillates. Logical simulation is never touched.
 */
export class PerfGovernor {
  private samples: number[] = [];
  private cooldown = 2;
  private idx: number;
  constructor(private maxDpr: number, start: number, private apply: (dpr: number) => void) {
    this.idx = DPR_STEPS.findIndex((d) => d >= start - 1e-3);
    if (this.idx < 0) this.idx = DPR_STEPS.length - 1;
  }

  get dpr() {
    return DPR_STEPS[this.idx];
  }

  frame(dt: number) {
    if (dt <= 0 || dt > 0.25) return; // ignore hitches from tab switches
    this.samples.push(dt);
    if (this.samples.length > 90) this.samples.shift();
    this.cooldown -= dt;
    if (this.cooldown > 0 || this.samples.length < 90) return;
    const sorted = [...this.samples].sort((a, b) => a - b);
    const p90 = sorted[Math.floor(sorted.length * 0.9)];
    if (p90 > 1 / 40 && this.idx > 0) {
      // a level that proved too slow becomes the new ceiling (prevents raise/drop oscillation)
      this.maxDpr = Math.min(this.maxDpr, DPR_STEPS[this.idx] - 0.01);
      this.idx--;
      this.commit(3);
    } else if (p90 < 1 / 56 && this.idx < DPR_STEPS.length - 1 && DPR_STEPS[this.idx + 1] <= this.maxDpr) {
      this.idx++;
      this.commit(8);
    }
  }

  private commit(cooldown: number) {
    this.apply(DPR_STEPS[this.idx]);
    this.samples.length = 0;
    this.cooldown = cooldown;
  }
}
