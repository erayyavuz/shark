import * as THREE from 'three';
import type { ActiveTool, ExperienceState, QualityTier, SurfaceKind } from '../contracts/types';
import type { HeadPose, PlayArea } from '../contracts/world';
import { clampToArea } from '../contracts/world';
import { ACTIVE, DOCK, HERO, INTRO, MOTION, RETURN } from '../config/tuning';
import { playAreaFor } from '../config/quality';
import { PRODUCT } from '../config/product';
import { Studio } from '../scene/Studio';
import { Floor } from '../scene/Floor';
import { CameraDirector, clonePose, type CamPose, type ViewInsets } from '../scene/CameraDirector';
import { VacuumRig } from '../product/VacuumRig';
import { MotionController } from '../interaction/MotionController';
import { InputController } from '../interaction/InputController';
import { AudioEngine } from '../audio/AudioEngine';
import { DirtSimulation } from '../simulation/DirtSimulation';
import { DirtRenderer } from '../simulation/render/DirtRenderer';
import { Timeline, easeInOutCubic, easeInOutSine, easeOutCubic, lerp, lerpAngle, linear } from './timeline';
import { useUI } from './store';

export interface ExperienceDeps {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  stage: HTMLElement;
  tier: QualityTier;
  invalidate: () => void;
}

/** Fraction of added mass that may remain for "All clear" (0.5%; brief §9.6). */
const ALL_CLEAR_TOLERANCE = 0.005;

/**
 * The imperative owner of the experience: one scene, one loop, one simulation clock.
 * React only renders UI from the zustand store, which this class writes on discrete changes.
 */
export class Experience {
  readonly studio: Studio;
  readonly floor: Floor;
  readonly director: CameraDirector;
  readonly motion = new MotionController();
  readonly audio = new AudioEngine();
  readonly input: InputController;
  rig: VacuumRig | null = null;
  sim!: DirtSimulation;
  dirt!: DirtRenderer;
  area!: PlayArea;

  private phase: ExperienceState = 'loading';
  private timeline: Timeline | null = null;
  private tier: QualityTier;
  private power = 0;
  private pitchBase = 0;
  private dynWeight = 0;
  private pitchDyn = 0;
  private rollDyn = 0;
  private fold = 0;
  /** docked nose-down tilt (rad); animates to 0 as the head rolls off the dock base plate */
  private raise: number = PRODUCT.dockedTilt;
  private pickupActive = false;
  private demoPickup = false;
  private strokeActive = false;
  private grabOffset = { x: 0, z: 0 };
  /** offset decays toward zero when the stroke began away from the head (glide under the pointer, never teleport) */
  private decayOffset = false;
  private lastHit = { x: 0, z: 0 };
  private lastAdd = { x: 0, z: 0, t: 0 };
  private time = 0;
  private lastAllClearCheck = 0;
  private reveal = 0;
  private parked = false;
  private contactShadow: THREE.Mesh;
  private ray = new THREE.Raycaster();
  private ndc = new THREE.Vector2();
  private plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  private v3 = new THREE.Vector3();
  private heroCam!: CamPose;
  private activeCam!: CamPose;
  private inspectOrbit = { theta: 0, phi: 1.2, radius: 2.4 };
  private inspectBase = new THREE.Vector3();
  private savedPose: HeadPose | null = null;
  private viewport = { w: 1, h: 1 };
  private startButton: HTMLElement | null = null;
  private disposed = false;
  private onVisibility = () => {
    if (document.hidden) this.audio.suspend();
    else this.audio.resume();
  };

  constructor(private deps: ExperienceDeps) {
    const { renderer, scene, camera, stage, tier } = deps;
    this.tier = tier;
    this.studio = new Studio(renderer, scene, tier);
    this.floor = new Floor();
    scene.add(this.floor.mesh);
    this.director = new CameraDirector(camera);
    camera.near = 0.03;
    camera.far = 40;

    this.contactShadow = makeContactShadow();
    scene.add(this.contactShadow);


    this.input = new InputController(stage, {
      mode: () => {
        if (this.phase === 'inspect') return 'inspect';
        if (this.phase !== 'active') return 'none';
        return useUI.getState().tool;
      },
      floorHit: (cx, cy, out) => this.floorHit(cx, cy, out),
      blocked: (cx, cy) => blockedByUI(cx, cy),
      beginClean: (hit) => this.beginClean(hit),
      moveClean: (hit) => this.moveClean(hit),
      endClean: () => this.endClean(),
      addPoint: (hit, first) => this.addPoint(hit, first),
      endAdd: () => undefined,
      orbit: (dx, dy) => this.orbit(dx, dy),
      zoom: (f) => this.zoom(f),
      key: (a) => {
        if (a === 'escape') this.escape();
        else if (this.phase === 'active') this.setTool(a);
      },
    });
    document.addEventListener('visibilitychange', this.onVisibility);
    // read-only inspection hook for automated browser tests (no mutation possible through it)
    (window as unknown as { __pd?: unknown }).__pd = {
      phase: () => this.phase,
      accounting: () => (this.sim ? { ...this.sim.getAccounting(), remainingFraction: this.sim.getRemainingFraction() } : null),
      head: () => ({ ...this.motion.pose }),
      area: () => (this.area ? { ...this.area } : null),
    };
  }

  // ───────────────────────────── setup ─────────────────────────────

  attachRig(rig: VacuumRig) {
    const old = this.rig;
    if (old) {
      this.deps.scene.remove(old.root);
      if (old.dock) this.deps.scene.remove(old.dock);
      old.dispose();
    }
    this.rig = rig;
    this.deps.scene.add(rig.root);
    if (rig.dock) {
      // the dock never moves: fixed at its home position, oriented like the docked vacuum
      rig.dock.position.set(DOCK.x, 0, DOCK.z);
      rig.dock.rotation.set(0, HERO.yaw + Math.PI, 0);
      this.deps.scene.add(rig.dock);
    }
    if (!this.sim) this.buildSimulation();
    this.applyRig(0);
    this.deps.invalidate();
  }

  private buildSimulation() {
    const { w, h } = this.viewport;
    this.area = playAreaFor(w / h);
    this.sim = new DirtSimulation({ area: this.area, nozzle: this.rig!.meta.nozzle, quality: this.tier, seed: 1251 });
    this.dirt = new DirtRenderer(this.sim, { quality: this.tier });
    this.deps.scene.add(this.dirt.group);
  }

  /** Rebuild simulation if the aspect class changed while nothing is on the floor (hero only). */
  private maybeRebuildSimulation() {
    if (!this.sim || this.phase !== 'hero') return;
    const next = playAreaFor(this.viewport.w / this.viewport.h);
    if (next === this.area) return;
    this.deps.scene.remove(this.dirt.group);
    this.dirt.dispose();
    this.buildSimulation();
  }

  setStartButton(el: HTMLElement | null) {
    this.startButton = el;
    this.layoutStartButton();
  }

  resize(w: number, h: number) {
    this.viewport = { w, h };
    this.maybeRebuildSimulation();
    const aspect = w / h;
    const insets = this.insets();
    this.heroCam = this.director.heroPose(aspect, h, { top: insets.top, bottom: 24 });
    if (this.area) this.activeCam = this.director.activePose(this.area, aspect, h, insets);
    if (this.phase === 'hero' || this.phase === 'loading') this.director.set(this.heroCam);
    else if (this.phase === 'active' && !this.timeline) this.director.set(this.activeCam);
    else if (this.phase === 'inspect') this.applyInspectCamera();
    this.layoutStartButton();
    this.deps.invalidate();
  }

  private insets(): ViewInsets {
    const mobile = this.viewport.w < 700;
    return { top: mobile ? 56 : 64, bottom: mobile ? 92 : 96 };
  }

  getPhase() {
    return this.phase;
  }

  private setPhase(p: ExperienceState) {
    this.phase = p;
    useUI.getState().set({ phase: p });
    this.deps.invalidate();
  }

  /** Called once the rig is attached and the first frame can be shown. */
  enterHero() {
    this.motion.reset(DOCK.x, DOCK.z, HERO.yaw);
    this.motion.steeringEnabled = false;
    this.pitchBase = 0;
    this.dynWeight = 0;
    this.power = 0;
    this.raise = PRODUCT.dockedTilt;
    this.reveal = 0;
    this.floor.reveal = 0;
    this.floor.preload('oak');
    this.studio.setFocus(new THREE.Vector3(DOCK.x, 0.55, DOCK.z), 0.9);
    this.setPhase('hero');
    this.resize(this.viewport.w, this.viewport.h);
  }

  // ───────────────────────────── transitions ─────────────────────────────

  start() {
    if (this.phase !== 'hero' || !this.rig) return;
    this.setPhase('starting');
    const ui = useUI.getState();
    ui.set({ controlsVisible: false, allClear: false, tool: 'clean', drawerOpen: false });
    this.audio.click();
    void this.floor.setSurface(ui.surface, true);
    this.floor.setRevealCenter(DOCK.x, DOCK.z + 0.6);
    this.studio.setFocus(new THREE.Vector3(0, 0.15, -0.1), 0.95);

    const fromCam = clonePose(this.director.current);
    const toCam = this.activeCam;
    const reduced = ui.reducedMotion;

    if (reduced) {
      // stable arrival with a short fade, no sweeping move and no demo pass
      const tl = new Timeline(0.6, () => this.finishIntro());
      tl.tween(0, 0.25, (k) => setFade(k), linear)
        .cue(0.25, () => {
          this.director.set(toCam);
          this.power = 1;
          this.pitchBase = ACTIVE.pitch;
          this.motion.pose.yaw = ACTIVE.yaw;
          this.reveal = 1;
          this.sim.addIntroPatch(this.introPatchPose());
        })
        .tween(0.3, 0.6, (k) => setFade(1 - k), linear);
      this.timeline = tl;
      return;
    }

    const [p0, p1] = INTRO.power;
    const [i0, i1] = INTRO.incline;
    const [c0, c1] = INTRO.camera;
    const [f0, f1] = INTRO.floor;
    const [d0, d1] = INTRO.demo;
    const startYaw = this.motion.pose.yaw;
    const tl = new Timeline(INTRO.total, () => this.finishIntro());
    tl.tween(p0, p1, (k) => (this.power = k), easeOutCubic)
      .tween(i0, i1, (k) => {
        this.pitchBase = lerp(0, ACTIVE.pitch, k);
        this.motion.pose.yaw = lerpAngle(startYaw, ACTIVE.yaw, k);
      })
      .tween(c0, c1, (k) => this.director.lerp(fromCam, toCam, k), easeInOutCubic)
      .tween(f0, f1, (k) => (this.reveal = k), easeInOutSine)
      .cue(INTRO.patchAt, () => this.sim.addIntroPatch(this.introPatchPose()))
      .tween(d0, d1, (k) => this.demoTarget(k), linear, () => {
        this.demoStart = { x: this.motion.pose.x, z: this.motion.pose.z, yaw: this.motion.pose.yaw };
        this.demoPickup = true;
        this.motion.steeringEnabled = true;
      })
      .cue(INTRO.controls, () => useUI.getState().set({ controlsVisible: true }));
    this.timeline = tl;
  }

  private demoStart: HeadPose = { x: 0, z: 0, yaw: 0 };

  /** A virtual head pose short of the patch so addIntroPatch (15–35 cm ahead) lands inside the play area. */
  private introPatchPose(): HeadPose {
    const yaw = ACTIVE.yaw;
    const d = INTRO.patchDistance - 0.25;
    return { x: DOCK.x - Math.sin(yaw) * d, z: DOCK.z - Math.cos(yaw) * d, yaw };
  }

  /** Scripted pass: forward through part of the patch then ease back slightly — same controller + sim. */
  private demoTarget(k: number) {
    const s = this.demoStart;
    const fx = -Math.sin(s.yaw);
    const fz = -Math.cos(s.yaw);
    const rx = -fz;
    const rz = fx;
    // forward through one side of the patch (leaving the rest), then ease back slightly
    // out of the dock and through one side of the patch, then ease back slightly
    const reach = INTRO.patchDistance + 0.12;
    const fwd = k < 0.75 ? easeInOutSine(k / 0.75) * reach : reach - easeInOutSine((k - 0.75) / 0.25) * 0.1;
    const side = easeInOutSine(Math.min(1, k / 0.4)) * 0.15;
    // not clamped while leaving the dock (the dock sits outside the play area); clamp once inside
    const raw = { x: s.x + fx * fwd + rx * side, z: s.z + fz * fwd + rz * side };
    const t = raw.z < this.area.minZ ? raw : clampToArea(raw, 0.14, this.area);
    this.motion.target.x = t.x;
    this.motion.target.z = t.z;
    // the head rolls forward off the dock base plate
    this.raise = PRODUCT.dockedTilt * (1 - easeInOutSine(Math.min(1, k / 0.25)));
    if (k >= 1) this.demoPickup = false;
  }

  skipIntro() {
    if (this.phase !== 'starting' || !this.timeline) return;
    const tl = this.timeline;
    // settle the head where it is now; no snap of the camera beyond the target pose
    this.demoPickup = false;
    tl.finish();
    this.motion.target.x = this.motion.pose.x;
    this.motion.target.z = this.motion.pose.z;
  }

  private finishIntro() {
    this.timeline = null;
    this.raise = 0;
    this.demoPickup = false;
    this.power = 1;
    this.pitchBase = ACTIVE.pitch;
    this.dynWeight = 1;
    this.reveal = 1;
    this.motion.steeringEnabled = true;
    this.motion.target.x = this.motion.pose.x;
    this.motion.target.z = this.motion.pose.z;
    this.director.set(this.activeCam);
    setFade(0);
    useUI.getState().set({ controlsVisible: true });
    this.setPhase('active');
  }

  back() {
    if (this.phase === 'hero' || this.phase === 'returning' || this.phase === 'loading') return;
    this.input.end();
    this.timeline?.cancel();
    this.timeline = null;
    this.strokeActive = false;
    this.pickupActive = false;
    this.demoPickup = false;
    this.parked = false;
    this.savedPose = null;
    useUI.getState().set({ controlsVisible: false, drawerOpen: false, strokeActive: false, allClear: false, detecting: false, tool: 'clean' });
    this.setPhase('returning');
    const fromCam = clonePose(this.director.current);
    const toCam = this.heroCam;
    const from = { ...this.motion.pose };
    const fromPitch = this.pitchBase + this.pitchDyn;
    const fromPower = this.power;
    const fromReveal = this.reveal;
    this.dynWeight = 0;
    this.motion.steeringEnabled = false;
    const reduced = useUI.getState().reducedMotion;
    const T = reduced ? 0.6 : RETURN.total;
    const tl = new Timeline(T, () => {
      this.timeline = null;
      this.audio.stopMotor();
      this.enterHero();
    });
    tl.tween(0, T * 0.4, (k) => (this.power = fromPower * (1 - k)), linear)
      .cue(T * 0.15, () => this.sim.clearFloor())
      .tween(0, T * 0.7, (k) => (this.reveal = fromReveal * (1 - k)), easeInOutSine)
      .tween(0, T, (k) => {
        this.motion.reset(lerp(from.x, DOCK.x, k), lerp(from.z, DOCK.z, k), lerpAngle(from.yaw, HERO.yaw, k));
        this.pitchBase = lerp(fromPitch, 0, k);
        this.raise = PRODUCT.dockedTilt * easeInOutSine(Math.max(0, (k - 0.75) / 0.25));
        this.pitchDyn = 0;
        this.rollDyn *= 1 - k;
        this.fold = 0;
      })
      .tween(0, T, (k) => this.director.lerp(fromCam, toCam, k), easeInOutCubic);
    this.timeline = tl;
    this.studio.setFocus(new THREE.Vector3(DOCK.x, 0.55, DOCK.z), 0.9);
  }

  inspect() {
    if (this.phase !== 'active') return;
    this.input.end();
    useUI.getState().set({ drawerOpen: false });
    this.savedPose = { ...this.motion.pose };
    const head = this.motion.pose;
    this.inspectBase.set(head.x, 0, head.z);
    const camOff = this.director.current.pos.clone().sub(this.inspectBase);
    this.inspectOrbit = { theta: Math.atan2(camOff.x, camOff.z), phi: 1.28, radius: 2.5 };
    const fromCam = clonePose(this.director.current);
    const fromPitch = this.pitchBase;
    this.setPhase('inspect');
    this.dynWeight = 0;
    const tl = new Timeline(1.1, () => (this.timeline = null));
    tl.tween(0, 1.1, (k) => {
      this.pitchBase = lerp(fromPitch, 0, k);
      const to = this.director.inspectPose(this.inspectBase, this.inspectOrbit.theta, this.inspectOrbit.phi, this.inspectOrbit.radius);
      this.director.lerp(fromCam, to, k);
    });
    this.timeline = tl;
    this.studio.setFocus(new THREE.Vector3(head.x, 0.5, head.z), 0.9);
  }

  /** Small preset for inspection close-ups. */
  inspectPreset(which: 'full' | 'head' | 'bin') {
    if (this.phase !== 'inspect') return;
    const fromCam = clonePose(this.director.current);
    const o = this.inspectOrbit;
    if (which === 'full') Object.assign(o, { phi: 1.28, radius: 2.5 });
    if (which === 'head') Object.assign(o, { phi: 1.1, radius: 0.75 });
    if (which === 'bin') Object.assign(o, { phi: 1.45, radius: 1.0 });
    this.inspectFocus = which === 'head' ? 0.06 : which === 'bin' ? 0.97 : 0.58;
    const to = this.director.inspectPose(this.inspectBase, o.theta, o.phi, o.radius, this.inspectFocus);
    this.timeline?.cancel();
    const tl = new Timeline(0.8, () => (this.timeline = null));
    tl.tween(0, 0.8, (k) => this.director.lerp(fromCam, to, k));
    this.timeline = tl;
  }

  private inspectFocus = 0.58;

  private applyInspectCamera() {
    const o = this.inspectOrbit;
    this.director.set(this.director.inspectPose(this.inspectBase, o.theta, o.phi, o.radius, this.inspectFocus));
  }

  exitInspect() {
    if (this.phase !== 'inspect') return;
    const fromCam = clonePose(this.director.current);
    this.timeline?.cancel();
    const tl = new Timeline(1.0, () => {
      this.timeline = null;
      this.dynWeight = 1;
      this.director.set(this.activeCam);
      this.setPhase('active');
    });
    tl.tween(0, 1.0, (k) => {
      this.pitchBase = lerp(0, ACTIVE.pitch, k);
      this.director.lerp(fromCam, this.activeCam, k);
    });
    this.timeline = tl;
    if (this.savedPose) this.motion.target = { x: this.savedPose.x, z: this.savedPose.z, active: false };
    this.studio.setFocus(new THREE.Vector3(this.motion.pose.x, 0.15, this.motion.pose.z - 0.1), 0.95);
  }

  private escape() {
    const ui = useUI.getState();
    if (ui.drawerOpen) {
      ui.set({ drawerOpen: false });
      return;
    }
    if (this.phase === 'inspect') this.exitInspect();
    else if (this.phase === 'starting') this.skipIntro();
  }

  private orbit(dx: number, dy: number) {
    if (this.phase !== 'inspect' || this.timeline) return;
    const o = this.inspectOrbit;
    o.theta -= dx * 0.006;
    o.phi = THREE.MathUtils.clamp(o.phi - dy * 0.005, 0.55, 1.52);
    this.applyInspectCamera();
  }

  private zoom(f: number) {
    if (this.phase !== 'inspect' || this.timeline) return;
    const o = this.inspectOrbit;
    o.radius = THREE.MathUtils.clamp(o.radius * f, 0.6, 3.2);
    this.applyInspectCamera();
  }

  // ───────────────────────────── tools ─────────────────────────────

  setTool(tool: ActiveTool) {
    const ui = useUI.getState();
    if (ui.tool === tool && !(tool === 'add' && !ui.drawerOpen)) return;
    this.input.end();
    if (tool === 'add') {
      // pause pickup and park the head just outside the placement zone
      this.pickupActive = false;
      this.parked = true;
      const a = this.area;
      // just beyond the far edge: a mostly-reverse move keeps yaw, and the wand trails out of frame
      this.motion.target = { x: this.motion.pose.x * 0.5 + (a.minX + a.maxX) * 0.25, z: a.minZ - 0.16, active: false };
      ui.set({ tool, drawerOpen: true });
    } else {
      this.parked = false;
      ui.set({ tool, drawerOpen: false });
    }
  }

  setSurface(s: SurfaceKind) {
    useUI.getState().set({ surface: s });
    void this.floor.setSurface(s);
    this.sim?.setSurface(s);
    this.dirt?.setSurface(s);
  }

  makeMess() {
    if (this.phase !== 'active') return;
    const added = this.sim.addPreset(Math.floor(Math.random() * 1e9));
    this.afterAdd(added);
  }

  clearFloor() {
    this.sim.clearFloor();
    useUI.getState().set({ allClear: false, budgetFull: false });
  }

  /** Day/night lighting. Studio owns the look; this only routes the request and keeps the UI state. */
  setNight(on: boolean) {
    useUI.getState().set({ night: on });
    this.studio.setMode(on ? 'night' : 'day');
    this.deps.invalidate();
  }

  async setSound(on: boolean) {
    useUI.getState().set({ sound: on });
    if (on) await this.audio.enable();
    else this.audio.disable();
  }

  private afterAdd(added: number) {
    const ui = useUI.getState();
    const patch: Partial<typeof ui> = {};
    if (added > 0 && ui.allClear) patch.allClear = false;
    const kinds = ui.dirtKind === 'mixed' ? (['dust', 'hair', 'pet', 'crumbs'] as const) : [ui.dirtKind];
    const full = kinds.some((k) => this.sim.isFull(k));
    if (full !== ui.budgetFull) patch.budgetFull = full;
    if (Object.keys(patch).length) ui.set(patch);
  }

  // ───────────────────────────── input → target ─────────────────────────────

  private floorHit(cx: number, cy: number, out: { x: number; z: number }) {
    const rect = this.deps.stage.getBoundingClientRect();
    this.ndc.set(((cx - rect.left) / rect.width) * 2 - 1, -((cy - rect.top) / rect.height) * 2 + 1);
    this.ray.setFromCamera(this.ndc, this.deps.camera);
    const p = this.ray.ray.intersectPlane(this.plane, this.v3);
    if (!p) return false;
    out.x = p.x;
    out.z = p.z;
    return true;
  }

  private beginClean(hit: { x: number; z: number }) {
    if (this.parked) this.parked = false;
    const pose = this.motion.pose;
    const ox = pose.x - hit.x;
    const oz = pose.z - hit.z;
    // grabbing the head itself keeps the exact offset; a press elsewhere glides the head under the pointer
    this.decayOffset = Math.hypot(ox, oz) > MOTION.grabRadius;
    this.grabOffset = { x: ox, z: oz };
    this.strokeActive = true;
    this.pickupActive = true;
    this.setTarget(hit);
    useUI.getState().set({ strokeActive: true });
  }

  private moveClean(hit: { x: number; z: number }) {
    if (!this.strokeActive) return;
    this.setTarget(hit);
  }

  private setTarget(hit: { x: number; z: number }) {
    this.lastHit.x = hit.x;
    this.lastHit.z = hit.z;
    const t = clampToArea({ x: hit.x + this.grabOffset.x, z: hit.z + this.grabOffset.z }, 0.12, this.area);
    this.motion.target.x = t.x;
    this.motion.target.z = t.z;
    this.motion.target.active = true;
  }

  private endClean() {
    this.strokeActive = false;
    this.pickupActive = false;
    this.motion.target.active = false;
    // settle safely: stop at the current pose plus a short glide
    this.motion.target.x = this.motion.pose.x + this.motion.vx * 0.06;
    this.motion.target.z = this.motion.pose.z + this.motion.vz * 0.06;
    useUI.getState().set({ strokeActive: false });
  }

  private addPoint(hit: { x: number; z: number }, first: boolean) {
    const ui = useUI.getState();
    const a = this.area;
    if (hit.x < a.minX || hit.x > a.maxX || hit.z < a.minZ || hit.z > a.maxZ) {
      this.lastAdd = { x: hit.x, z: hit.z, t: this.time };
      return;
    }
    let added: number;
    if (first) added = this.sim.addScatter(ui.dirtKind, ui.density, hit.x, hit.z);
    else {
      const dt = Math.min(0.1, this.time - this.lastAdd.t);
      added = this.sim.addStroke(ui.dirtKind, ui.density, this.lastAdd.x, this.lastAdd.z, hit.x, hit.z, dt);
    }
    this.lastAdd = { x: hit.x, z: hit.z, t: this.time };
    this.afterAdd(added);
  }

  // ───────────────────────────── frame ─────────────────────────────

  update(rawDt: number) {
    if (this.disposed || !this.rig) return;
    // never apply a large accumulated delta (tab switches, hitches)
    const dt = Math.min(rawDt, 1 / 20);
    this.time += dt;
    this.timeline?.advance(dt);

    const live = this.phase === 'starting' || this.phase === 'active' || this.phase === 'returning';
    if (this.phase === 'active' && useUI.getState().tool === 'clean') this.keyboardDrive(dt);
    if (this.strokeActive && this.decayOffset) {
      const f = Math.exp(-dt / MOTION.offsetDecay);
      this.grabOffset.x *= f;
      this.grabOffset.z *= f;
      this.setTarget(this.lastHit);
    }

    const pickup = (this.pickupActive || this.demoPickup) && this.phase !== 'inspect' && this.power > 0.5;
    if (live && this.phase !== 'returning') {
      this.motion.update(dt, (prev, next, h) => this.sim.step(h, prev, next, pickup));
    }

    // wand dynamics: push/pull and lateral lean with damped response
    const targetPitchDyn = THREE.MathUtils.clamp(-this.motion.forwardSpeed * 0.07, -0.08, 0.08) * this.dynWeight;
    const targetRoll = THREE.MathUtils.clamp(this.motion.lateral * 0.1, -0.1, 0.1) * this.dynWeight;
    const k = 1 - Math.exp(-dt * 6);
    this.pitchDyn += (targetPitchDyn - this.pitchDyn) * k;
    this.rollDyn += (targetRoll - this.rollDyn) * k;

    const density = this.phase === 'active' || this.phase === 'starting' ? this.sim.getLocalDensity(this.motion.pose) : 0;
    this.applyRig(dt, density, pickup);
    this.updateRing(dt, pickup, density);
    this.floor.reveal = this.reveal;
    this.floor.update(dt);
    this.dirt.sync(this.time);

    if (this.phase === 'active' || this.phase === 'starting') {
      this.studio.setFocus(this.v3.set(this.motion.pose.x, 0.15, this.motion.pose.z - 0.1), 0.95);
    }

    // audio + pickup feedback
    const events = this.sim.drainPickups();
    if (this.audio.isEnabled) {
      for (const e of events) this.audio.pickup(e.kind, e.mass);
      this.audio.update(this.power, pickup, density, this.motion.speed);
    }

    if (this.phase === 'active' && this.time - this.lastAllClearCheck > 0.25) {
      this.lastAllClearCheck = this.time;
      this.updateStatus(pickup, density);
    }

    if (live || this.timeline || this.floor.animating || this.phase === 'inspect') this.deps.invalidate();
  }

  private keyboardDrive(dt: number) {
    const keys = this.input.keys;
    if (this.input.keyboardActive) {
      if (!this.motion.target.active) {
        this.motion.target.x = this.motion.pose.x;
        this.motion.target.z = this.motion.pose.z;
      }
      const s = MOTION.keyboardSpeed * dt;
      const t = clampToArea(
        {
          x: this.motion.target.x + ((keys.right ? 1 : 0) - (keys.left ? 1 : 0)) * s,
          z: this.motion.target.z + ((keys.down ? 1 : 0) - (keys.up ? 1 : 0)) * s,
        },
        0.12,
        this.area,
      );
      this.motion.target.x = t.x;
      this.motion.target.z = t.z;
      this.motion.target.active = true;
      this.parked = false;
    } else if (!this.strokeActive && this.motion.target.active) {
      this.motion.target.active = false;
    }
    if (!this.strokeActive) this.pickupActive = keys.space;
  }

  private ringState: 'white' | 'purple' | 'lightPurple' = 'white';
  private ringHold = 0;

  /** Mirrors the product's detect ring: purple over heavy dirt, light purple briefly while it clears, else white. */
  private updateRing(dt: number, pickup: boolean, density: number) {
    let next: typeof this.ringState = 'white';
    if (pickup && density > 0.12) {
      next = 'purple';
      this.ringHold = 0.9;
    } else if (this.ringHold > 0) {
      this.ringHold -= dt;
      next = 'lightPurple';
    }
    if (next !== this.ringState) {
      this.ringState = next;
      this.rig?.setRing(next);
    }
  }

  private updateStatus(pickup: boolean, density: number) {
    const ui = useUI.getState();
    const acc = this.sim.getAccounting();
    const clear = acc.added > 0 && this.sim.getRemainingFraction() < ALL_CLEAR_TOLERANCE;
    const detecting = pickup && density > 0.04;
    const patch: Partial<typeof ui> = {};
    if (clear !== ui.allClear) patch.allClear = clear;
    if (detecting !== ui.detecting) patch.detecting = detecting;
    if (Object.keys(patch).length) ui.set(patch);
  }

  private applyRig(dt: number, density = 0, pickup = false) {
    const rig = this.rig!;
    const p = this.motion.pose;
    rig.applyPose({
      x: p.x,
      z: p.z,
      yaw: p.yaw,
      pitch: this.pitchBase + this.pitchDyn,
      roll: this.rollDyn,
      fold: this.fold,
      dockTilt: this.raise,
    });
    rig.spinRollers(dt, this.power * (0.75 + (pickup ? 0.2 : 0) + density * 0.35));
    rig.setPower(this.power);
    const acc = this.sim ? this.sim.getAccounting() : null;
    rig.setBinFill(acc ? Math.min(0.55, acc.collected / 400) : 0);

    // contact shadow + headlight follow the actual floorhead
    const cs = this.contactShadow;
    cs.position.set(p.x, 0.0004, p.z);
    cs.rotation.set(-Math.PI / 2, 0, p.yaw + Math.PI);
  }

  /** Project the PowerControlAnchor and place the Start control to its right, clamped on-screen. */
  layoutStartButton() {
    const el = this.startButton;
    if (!el || !this.rig || !this.heroCam) return;
    const cam = new THREE.PerspectiveCamera(this.heroCam.fov, this.viewport.w / this.viewport.h, 0.05, 50);
    cam.position.copy(this.heroCam.pos);
    cam.lookAt(this.heroCam.target);
    cam.updateMatrixWorld();
    // evaluate in hero pose
    this.rig.applyPose({ x: DOCK.x, z: DOCK.z, yaw: HERO.yaw, pitch: 0, roll: 0, fold: 0, dockTilt: PRODUCT.dockedTilt });
    const anchor = this.rig.anchorWorld('PowerControlAnchor', new THREE.Vector3()).project(cam);
    const box = new THREE.Box3().setFromObject(this.rig.nodes.MotorAssembly);
    let right = -1;
    const c = new THREE.Vector3();
    for (let i = 0; i < 8; i++) {
      c.set(i & 1 ? box.max.x : box.min.x, i & 2 ? box.max.y : box.min.y, i & 4 ? box.max.z : box.min.z).project(cam);
      right = Math.max(right, c.x);
    }
    const { w, h } = this.viewport;
    const size = 64;
    let x = ((right + 1) / 2) * w + (w < 700 ? 18 : 36);
    let y = ((1 - anchor.y) / 2) * h - size / 2;
    x = Math.min(w - size - 16, Math.max(16, x));
    y = Math.min(h - size - 120, Math.max(80, y));
    el.style.setProperty('--sx', `${Math.round(x)}px`);
    el.style.setProperty('--sy', `${Math.round(y)}px`);
    if (this.phase !== 'hero' && this.phase !== 'loading') this.applyRig(0);
  }

  dispose() {
    this.disposed = true;
    this.timeline?.cancel();
    this.input.dispose();
    this.audio.dispose();
    document.removeEventListener('visibilitychange', this.onVisibility);
    if (this.rig) {
      this.deps.scene.remove(this.rig.root);
      if (this.rig.dock) this.deps.scene.remove(this.rig.dock);
      this.rig.dispose();
    }
    if (this.dirt) {
      this.deps.scene.remove(this.dirt.group);
      this.dirt.dispose();
    }
    this.deps.scene.remove(this.floor.mesh, this.contactShadow);
    this.floor.dispose();
    this.studio.dispose();
    (this.contactShadow.material as THREE.MeshBasicMaterial).map?.dispose();
    (this.contactShadow.material as THREE.Material).dispose();
    this.contactShadow.geometry.dispose();
  }
}

function makeContactShadow() {
  const c = document.createElement('canvas');
  c.width = c.height = 128;
  const g = c.getContext('2d')!;
  const grad = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  grad.addColorStop(0, 'rgba(0,0,0,0.55)');
  grad.addColorStop(0.5, 'rgba(0,0,0,0.28)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 128, 128);
  const tex = new THREE.CanvasTexture(c);
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(0.36, 0.3),
    new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 0.5, toneMapped: false }),
  );
  m.position.z = -0.02;
  m.renderOrder = 1;
  return m;
}

function blockedByUI(cx: number, cy: number) {
  const els = document.querySelectorAll<HTMLElement>('[data-ui-block]');
  for (const el of els) {
    if (el.dataset.hidden === 'true') continue;
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    if (cx >= r.left - 6 && cx <= r.right + 6 && cy >= r.top - 6 && cy <= r.bottom + 6) return true;
  }
  return false;
}

function setFade(k: number) {
  const el = document.getElementById('scene-fade');
  if (el) el.style.opacity = String(k);
}
