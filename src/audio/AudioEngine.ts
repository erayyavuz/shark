import type { BaseDirtKind } from '../contracts/simulation';

/**
 * One managed Web Audio graph. All sounds are synthesized (not recordings of the product).
 * Created lazily on the first user gesture that enables sound; gains are ramped, never re-created per event.
 *
 *  motor: noise -> bandpass ┐
 *         saw   -> lowpass  ├-> motorGain -> master -> destination
 *         sine (whine)      ┘
 *  pickups: short noise bursts through a shared filter -> pickupGain -> master
 */
export class AudioEngine {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private motorGain!: GainNode;
  private whine!: OscillatorNode;
  private whineGain!: GainNode;
  private saw!: OscillatorNode;
  private body!: BiquadFilterNode;
  private air!: BiquadFilterNode;
  private pickupGain!: GainNode;
  private pickupFilter!: BiquadFilterNode;
  private noise!: AudioBuffer;
  private enabled = false;
  private power = 0;
  private lastTick = 0;
  private disposed = false;

  get isEnabled() {
    return this.enabled;
  }

  /** Must be called from a user gesture handler. */
  async enable() {
    if (this.disposed) return;
    if (!this.ctx) this.build();
    this.enabled = true;
    await this.ctx!.resume().catch(() => undefined);
    this.ramp(this.master.gain, 0.5, 0.25);
  }

  disable() {
    this.enabled = false;
    if (!this.ctx) return;
    this.ramp(this.master.gain, 0, 0.15);
  }

  /** tab hidden / visible */
  suspend() {
    this.ctx?.suspend().catch(() => undefined);
  }
  resume() {
    if (this.enabled) this.ctx?.resume().catch(() => undefined);
  }

  private build() {
    const ctx = new AudioContext();
    this.ctx = ctx;
    this.master = ctx.createGain();
    this.master.gain.value = 0;
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -18;
    this.master.connect(comp).connect(ctx.destination);

    const len = ctx.sampleRate * 2;
    this.noise = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = this.noise.getChannelData(0);
    let b0 = 0, b1 = 0;
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1;
      b0 = 0.99765 * b0 + w * 0.099046;
      b1 = 0.963 * b1 + w * 0.2965;
      d[i] = (b0 + b1 + w * 0.18) * 0.35;
    }

    this.motorGain = ctx.createGain();
    this.motorGain.gain.value = 0;
    this.motorGain.connect(this.master);

    const src = ctx.createBufferSource();
    src.buffer = this.noise;
    src.loop = true;
    this.air = ctx.createBiquadFilter();
    this.air.type = 'bandpass';
    this.air.frequency.value = 900;
    this.air.Q.value = 0.6;
    src.connect(this.air).connect(this.motorGain);
    src.start();

    this.saw = ctx.createOscillator();
    this.saw.type = 'sawtooth';
    this.saw.frequency.value = 118;
    this.body = ctx.createBiquadFilter();
    this.body.type = 'lowpass';
    this.body.frequency.value = 420;
    const sawGain = ctx.createGain();
    sawGain.gain.value = 0.06;
    this.saw.connect(this.body).connect(sawGain).connect(this.motorGain);
    this.saw.start();

    this.whine = ctx.createOscillator();
    this.whine.type = 'sine';
    this.whine.frequency.value = 1850;
    this.whineGain = ctx.createGain();
    this.whineGain.gain.value = 0.012;
    this.whine.connect(this.whineGain).connect(this.motorGain);
    this.whine.start();

    this.pickupFilter = ctx.createBiquadFilter();
    this.pickupFilter.type = 'bandpass';
    this.pickupFilter.frequency.value = 2400;
    this.pickupFilter.Q.value = 1.2;
    this.pickupGain = ctx.createGain();
    this.pickupGain.gain.value = 0.9;
    this.pickupFilter.connect(this.pickupGain).connect(this.master);
  }

  private ramp(p: AudioParam, v: number, t: number) {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    p.cancelScheduledValues(now);
    p.setValueAtTime(p.value, now);
    p.linearRampToValueAtTime(v, now + t);
  }

  click() {
    if (!this.ctx || !this.enabled) return;
    this.burst(0.03, 3800, 0.35, 6);
  }

  /** Called per frame (cheap; uses setTargetAtTime). power 0..1, cleaning bool, density 0..1 */
  update(power: number, cleaning: boolean, density: number, speed: number) {
    this.power = power;
    if (!this.ctx || !this.enabled) return;
    const now = this.ctx.currentTime;
    const level = power * (0.32 + (cleaning ? 0.12 : 0) + density * 0.18);
    this.motorGain.gain.setTargetAtTime(level, now, 0.12);
    const boost = density * 0.25 + (cleaning ? 0.06 : 0);
    this.saw.frequency.setTargetAtTime(110 + power * 10 + boost * 40, now, 0.25);
    this.whine.frequency.setTargetAtTime(1700 + power * 150 + boost * 520, now, 0.3);
    this.air.frequency.setTargetAtTime(750 + boost * 900 + speed * 120, now, 0.2);
  }

  pickup(kind: BaseDirtKind, mass: number) {
    if (!this.ctx || !this.enabled || this.power < 0.1) return;
    const now = this.ctx.currentTime;
    if (now - this.lastTick < 0.028) return;
    this.lastTick = now;
    const m = Math.min(1, mass * 4);
    switch (kind) {
      case 'crumbs':
        this.burst(0.018, 3200 + Math.random() * 1600, 0.12 + m * 0.25, 4);
        break;
      case 'hair':
      case 'pet':
        this.burst(0.09, 5200, 0.05 + m * 0.08, 0.8);
        break;
      case 'dust':
        this.burst(0.05, 6500, 0.025 + m * 0.05, 0.6);
        break;
    }
  }

  private burst(dur: number, freq: number, gain: number, q: number) {
    const ctx = this.ctx!;
    const now = ctx.currentTime;
    const src = ctx.createBufferSource();
    src.buffer = this.noise;
    const g = ctx.createGain();
    g.gain.setValueAtTime(0, now);
    g.gain.linearRampToValueAtTime(gain, now + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    this.pickupFilter.frequency.setValueAtTime(freq, now);
    this.pickupFilter.Q.setValueAtTime(q, now);
    src.connect(g).connect(this.pickupFilter);
    src.start(now, Math.random() * 1.5, dur + 0.02);
    src.onended = () => g.disconnect();
  }

  stopMotor() {
    this.power = 0;
    if (this.ctx) this.ramp(this.motorGain.gain, 0, 0.3);
  }

  dispose() {
    this.disposed = true;
    this.ctx?.close().catch(() => undefined);
    this.ctx = null;
  }
}
