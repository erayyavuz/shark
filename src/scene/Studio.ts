import * as THREE from 'three';
import type { QualityTier } from '../contracts/types';
import { bakeEnv, buildDayEnvScene, buildNightEnvScene } from './lookdev/studioEnvironment';
import { ProductLights } from './lookdev/productLights';
import { HeroStage, STAGE_HORIZON } from './lookdev/heroStage';

/**
 * Scene lighting.
 *
 * DAY — photographic product studio: a self-authored softbox environment (PMREM) carries most of the light and all
 * the shaped reflections; one shadow-casting key (tight frustum around the subject, soft PCF) grounds the product,
 * a cool rim separates edges, a faint hemisphere keeps shadow sides from going dead. Seamless pale backdrop via fog.
 *
 * NIGHT — dark room: blue-grey walls, cool moonlight from a window (the key light re-aimed and re-tinted, still
 * casting the only large shadow), a dim warm practical, and the product's own LEDs (ProductLights spots + emissive
 * + bloom) doing the work.
 *
 * setMode() starts a ~0.8 s eased crossfade; update(dt) advances it and returns true while anything animates so the
 * render loop keeps invalidating.
 */

interface Look {
  bg: THREE.Color;
  envI: number;
  keyColor: THREE.Color;
  keyI: number;
  keyDir: THREE.Vector3;
  rimColor: THREE.Color;
  rimI: number;
  hemiSky: THREE.Color;
  hemiGround: THREE.Color;
  hemiI: number;
  practicalI: number;
  fogNear: number;
  fogFar: number;
  exposure: number;
}

const DAY: Look = {
  bg: new THREE.Color(0xe7e6e3),
  envI: 0.62,
  keyColor: new THREE.Color(0xfff4e8),
  // more lateral than frontal: models the round bin/wand and throws a readable grounding shadow to the right-back
  keyI: 2.4,
  keyDir: new THREE.Vector3(-1.15, 1.7, 0.45).normalize(),
  rimColor: new THREE.Color(0xe6eeff),
  rimI: 1.2,
  hemiSky: new THREE.Color(0xf4f6fa),
  hemiGround: new THREE.Color(0xd8d2c8),
  hemiI: 0.07,
  practicalI: 0,
  fogNear: 3.2,
  fogFar: 9,
  exposure: 1.0,
};

const NIGHT: Look = {
  bg: new THREE.Color(0x15181d),
  envI: 0.8,
  // moonlight through a window, left-back: the only large shadow at night and the edge light that keeps the
  // silhouette readable in the hero
  keyColor: new THREE.Color(0xb4c4e0),
  keyI: 0.3,
  keyDir: new THREE.Vector3(-1.1, 1.35, -0.6).normalize(),
  rimColor: new THREE.Color(0x9fb0d0),
  rimI: 0.35,
  hemiSky: new THREE.Color(0x46506a),
  hemiGround: new THREE.Color(0x15171b),
  hemiI: 0.07,
  practicalI: 1.1,
  fogNear: 2.8,
  fogFar: 8.5,
  exposure: 1.1,
};

/** Hero launch stage: the global lights step back so the stage spots (lookdev/heroStage) shape the product. */
const STAGE = {
  bg: STAGE_HORIZON,
  envI: 0.32,
  keyI: 0.22,
  rimI: 0.18,
  hemiI: 0.02,
  fogNear: 2.2,
  fogFar: 7.5,
  exposure: 1.05,
};

const TRANSITION = 0.85;

export class Studio {
  readonly key: THREE.DirectionalLight;
  readonly rim: THREE.DirectionalLight;
  readonly fill: THREE.HemisphereLight;
  readonly practical: THREE.PointLight;
  readonly product: ProductLights;
  readonly stage: HeroStage;
  readonly group = new THREE.Group();
  private envDay: THREE.Texture;
  private envNight: THREE.Texture;
  private focus = new THREE.Vector3();
  private shadowExtent = 0.9;
  private fog: THREE.Fog;
  private bg = new THREE.Color();
  /** 0 = day, 1 = night (eased) */
  private k = 0;
  private from = 0;
  private to = 0;
  private t = 1;
  private keyDir = new THREE.Vector3();
  private led = 0;
  private stageS = 1;
  private reveal = 0;

  constructor(private renderer: THREE.WebGLRenderer, private scene: THREE.Scene, tier: QualityTier) {
    this.envDay = bakeEnv(renderer, buildDayEnvScene());
    this.envNight = bakeEnv(renderer, buildNightEnvScene());
    scene.environment = this.envDay;

    scene.background = this.bg;
    this.fog = new THREE.Fog(0xffffff, DAY.fogNear, DAY.fogFar);
    scene.fog = this.fog;

    this.key = new THREE.DirectionalLight(0xffffff, 1);
    this.key.castShadow = true;
    const ms = tier === 'high' ? 2048 : 1024;
    this.key.shadow.mapSize.set(ms, ms);
    this.key.shadow.bias = -0.0003;
    this.key.shadow.normalBias = 0.01;
    // PCF (vogel disk) radius in texels; a tight frustum keeps contact crisp while the penumbra widens with distance
    this.key.shadow.radius = tier === 'high' ? 4 : 3;
    this.group.add(this.key, this.key.target);

    this.rim = new THREE.DirectionalLight(0xffffff, 1);
    this.group.add(this.rim, this.rim.target);

    this.fill = new THREE.HemisphereLight(0xffffff, 0xffffff, 1);
    this.group.add(this.fill);

    // warm practical (table lamp off to the right-back); only on at night
    this.practical = new THREE.PointLight(0xffa860, 0, 9, 2);
    this.practical.position.set(3.2, 1.1, -2.4);
    this.group.add(this.practical);

    scene.add(this.group);
    this.product = new ProductLights(scene, tier === 'high');
    this.stage = new HeroStage(scene, tier);
    this.apply();
    this.setFocus(new THREE.Vector3(0, 0.55, 0), 0.9);
  }

  /** Keep the shadow frustum tight around the subject for crisp contact shadows. */
  setFocus(p: THREE.Vector3, extent: number) {
    this.focus.copy(p);
    this.shadowExtent = extent;
    this.placeLights();
    const cam = this.key.shadow.camera;
    if (cam.right !== extent) {
      cam.left = -extent;
      cam.right = extent;
      cam.top = extent;
      cam.bottom = -extent;
      cam.near = 0.5;
      cam.far = 6;
      cam.updateProjectionMatrix();
    }
  }

  private placeLights() {
    const p = this.focus;
    this.key.position.copy(p).addScaledVector(this.keyDir, 3);
    this.key.target.position.copy(p);
    const rimDir = this.v.set(0.9, 0.8, -1.1).normalize();
    this.rim.position.copy(p).addScaledVector(rimDir, 3);
    this.rim.target.position.copy(p);
  }
  private v = new THREE.Vector3();

  get extent() {
    return this.shadowExtent;
  }

  /** 0 = day … 1 = night, eased (read by the post pipeline for bloom/grade). */
  get nightAmount() {
    return this.k;
  }

  /** Current head-LED power 0..1 (as last seen by update). */
  get ledLevel() {
    return this.led;
  }

  get exposure() {
    return THREE.MathUtils.lerp(THREE.MathUtils.lerp(DAY.exposure, NIGHT.exposure, this.k), STAGE.exposure, this.stageS);
  }

  setMode(mode: 'day' | 'night') {
    const target = mode === 'night' ? 1 : 0;
    if (target === this.to) return;
    this.from = this.k;
    this.to = target;
    this.t = 0;
  }

  /**
   * Hero stage presence, driven by the floor reveal (0 = hero stage, 1 = play floor). Call every frame with the
   * same value Floor.reveal gets; Start (reveal 0→1) dissolves the stage into the floor, Back (1→0) restores it.
   */
  setStage(reveal: number) {
    const s = 1 - THREE.MathUtils.smoothstep(reveal, 0.0, 0.6);
    if (s === this.stageS && reveal === this.reveal) return;
    this.reveal = reveal;
    this.stageS = s;
    this.stage.setAmount(s, reveal);
    this.apply();
  }

  /** 0 = play look … 1 = hero stage (read by the post pipeline). */
  get stageAmount() {
    return this.stageS;
  }

  /** Advance transitions + product lights. Returns true while a transition is running. */
  update(dt: number) {
    let animating = false;
    if (this.t < 1) {
      const dur = TRANSITION * Math.abs(this.to - this.from) || TRANSITION;
      this.t = Math.min(1, this.t + dt / dur);
      const e = this.t * this.t * (3 - 2 * this.t);
      this.k = this.from + (this.to - this.from) * e;
      this.apply();
      animating = this.t < 1;
    }
    this.product.stage = this.stageS;
    this.led = this.product.update();
    return animating;
  }

  private apply() {
    const k = this.k;
    const lerpC = (out: THREE.Color, a: THREE.Color, b: THREE.Color) => out.copy(a).lerp(b, k);
    lerpC(this.bg, DAY.bg, NIGHT.bg);
    this.fog.color.copy(this.bg);
    this.fog.near = THREE.MathUtils.lerp(DAY.fogNear, NIGHT.fogNear, k);
    this.fog.far = THREE.MathUtils.lerp(DAY.fogFar, NIGHT.fogFar, k);

    // environment: swap at the midpoint; each side fades through a low point so the swap is not visible
    const nightEnv = k > 0.5;
    this.scene.environment = nightEnv ? this.envNight : this.envDay;
    const sideK = nightEnv ? (k - 0.5) * 2 : 1 - k * 2; // 1 at the pure look, 0 at the swap
    const swapFloor = 0.18;
    this.scene.environmentIntensity = (nightEnv ? NIGHT.envI : DAY.envI) * (swapFloor + (1 - swapFloor) * sideK);

    lerpC(this.key.color, DAY.keyColor, NIGHT.keyColor);
    // intensity eases in log space so the day→night fall-off reads as dimming, not a cut
    this.key.intensity = Math.exp(THREE.MathUtils.lerp(Math.log(DAY.keyI), Math.log(NIGHT.keyI), k));
    this.keyDir.copy(DAY.keyDir).lerp(NIGHT.keyDir, k).normalize();
    lerpC(this.rim.color, DAY.rimColor, NIGHT.rimColor);
    this.rim.intensity = Math.exp(THREE.MathUtils.lerp(Math.log(DAY.rimI), Math.log(NIGHT.rimI), k));
    lerpC(this.fill.color, DAY.hemiSky, NIGHT.hemiSky);
    lerpC(this.fill.groundColor, DAY.hemiGround, NIGHT.hemiGround);
    this.fill.intensity = THREE.MathUtils.lerp(DAY.hemiI, NIGHT.hemiI, k);
    this.practical.intensity = THREE.MathUtils.lerp(DAY.practicalI, NIGHT.practicalI, k);
    this.product.night = k;

    // hero stage overrides the room look
    const s = this.stageS;
    if (s > 0) {
      const L = THREE.MathUtils.lerp;
      // linear-light lerp toward the pale room reads bright very early; hold the dark world, then lift it late
      const sd = 1 - Math.pow(1 - s, 3);
      this.bg.lerp(STAGE.bg, sd);
      this.fog.color.copy(this.bg);
      this.fog.near = L(this.fog.near, STAGE.fogNear, s);
      this.fog.far = L(this.fog.far, STAGE.fogFar, s);
      this.scene.environmentIntensity = L(this.scene.environmentIntensity, STAGE.envI, s);
      this.key.intensity = L(this.key.intensity, STAGE.keyI, s);
      this.rim.intensity = L(this.rim.intensity, STAGE.rimI, s);
      this.fill.intensity = L(this.fill.intensity, STAGE.hemiI, s);
      this.practical.intensity *= 1 - s;
    }
    this.placeLights();
  }

  setShadowQuality(tier: QualityTier) {
    const ms = tier === 'high' ? 2048 : 1024;
    if (this.key.shadow.mapSize.x !== ms) {
      this.key.shadow.mapSize.set(ms, ms);
      this.key.shadow.map?.dispose();
      this.key.shadow.map = null;
    }
  }

  dispose() {
    this.scene.remove(this.group);
    this.product.dispose();
    this.stage.dispose();
    this.envDay.dispose();
    this.envNight.dispose();
    this.key.shadow.map?.dispose();
    this.scene.environment = null;
    this.scene.background = null;
    this.scene.fog = null;
    void this.renderer;
  }
}
