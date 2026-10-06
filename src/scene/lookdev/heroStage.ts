import * as THREE from 'three';
import { DOCK } from '../../config/tuning';
import type { QualityTier } from '../../contracts/types';

/**
 * Hero "launch stage": a dark graded stage floor, an inset podium under the docked product (top flush with the floor
 * at y≈0 so the floorhead and dock rest on it exactly as on the floor), a chamfered metal rim with a thin warm LED
 * line, a domed backdrop with a soft radial glow for depth, three restrained light beams (additive gradient cones, no
 * volumetrics) and three real spot lights (overhead key with soft shadow, two back rims).
 *
 * setAmount(s, reveal): s = 1 full stage, 0 gone. The stage floor dissolves with the *same* radial mask as Floor.ts'
 * reveal (centre DOCK + 0.6 m toward the viewer, radius reveal × 7 m, 1.2 m feather) so the oak spreads out of the stage.
 * Light count is constant for the scene's life (intensity 0 when hidden) — no program recompiles on Start/Back.
 */

const CENTER = new THREE.Vector3(DOCK.x + 0.05, 0, DOCK.z + 0.1);
/** Stage horizon colour (linear). Studio uses the same value for fog so floor and backdrop meet without a line. */
export const STAGE_HORIZON = new THREE.Color(0x0f1012);
const R = 0.46; // podium top radius (m): dock base + docked floorhead with margin
const REVEAL_C = new THREE.Vector2(DOCK.x, DOCK.z + 0.6);

const fadeVert = /* glsl */ `
varying vec3 vWorld;
varying vec3 vN;
varying vec3 vView;
varying vec2 vUv;
#include <common>
#include <fog_pars_vertex>
void main() {
  vUv = uv;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorld = wp.xyz;
  vN = normalize(mat3(modelMatrix) * normal);
  vView = normalize(cameraPosition - wp.xyz);
  vec4 mvPosition = viewMatrix * wp;
  gl_Position = projectionMatrix * mvPosition;
  #include <fog_vertex>
}`;

/** Additive soft light beam: brightest near the (off-frame) source, soft edges from the view angle. */
function beamMaterial(color: THREE.Color) {
  return new THREE.ShaderMaterial({
    uniforms: { uColor: { value: color }, uK: { value: 0 } },
    vertexShader: fadeVert,
    fragmentShader: /* glsl */ `
uniform vec3 uColor; uniform float uK;
varying vec3 vN; varying vec3 vView; varying vec2 vUv;
void main() {
  float edge = pow(abs(dot(normalize(vN), normalize(vView))), 2.2);
  // uv.y: 1 at the apex (top), 0 at the base (floor)
  float along = smoothstep(0.0, 0.55, vUv.y) * (0.35 + 0.65 * vUv.y);
  gl_FragColor = vec4(uColor * edge * along * uK, 1.0);
}`,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    side: THREE.FrontSide,
    toneMapped: false,
  });
}

export class HeroStage {
  readonly group = new THREE.Group();
  readonly key: THREE.SpotLight;
  readonly rimL: THREE.SpotLight;
  readonly rimR: THREE.SpotLight;
  private floorMat: THREE.MeshStandardMaterial;
  private floorU = { uReveal: { value: 0 }, uFade: { value: 1 } };
  private topMat: THREE.MeshPhysicalMaterial;
  private rimMat: THREE.MeshStandardMaterial;
  private ledMat: THREE.MeshBasicMaterial;
  private spillMat: THREE.ShaderMaterial;
  private backMat: THREE.ShaderMaterial;
  private beams: THREE.ShaderMaterial[] = [];
  private visual = new THREE.Group();
  private disposables: { dispose(): void }[] = [];
  private s = -1;

  constructor(private scene: THREE.Scene, tier: QualityTier) {
    this.group.name = 'HeroStage';

    // ── stage floor: deep charcoal satin, dissolving with the oak reveal mask ──
    this.floorMat = new THREE.MeshStandardMaterial({ color: 0x17181b, roughness: 0.42, metalness: 0, transparent: true });
    this.floorMat.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, this.floorU);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vStageXZ;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvStageXZ = (modelMatrix * vec4(transformed, 1.0)).xz;');
      sh.fragmentShader = sh.fragmentShader
        .replace(
          '#include <common>',
          `#include <common>
varying vec2 vStageXZ;
uniform float uReveal, uFade;`,
        )
        .replace(
          '#include <dithering_fragment>',
          `#include <dithering_fragment>
{
  float d = length(vStageXZ - vec2(${REVEAL_C.x.toFixed(3)}, ${REVEAL_C.y.toFixed(3)}));
  float r = uReveal * 7.0;
  float m = uReveal >= 0.999 ? 1.0 : smoothstep(r, r - 1.2, d) * smoothstep(0.0, 0.15, uReveal);
  gl_FragColor.a *= (1.0 - m) * uFade;
}`,
        );
    };
    const floor = new THREE.Mesh(new THREE.CircleGeometry(12, 96), this.floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(CENTER.x, 0.0006, CENTER.z);
    floor.receiveShadow = true;
    floor.renderOrder = 0;
    this.visual.add(floor);

    // ── podium top: inset satin stone disc, flush with the floor ──
    this.topMat = new THREE.MeshPhysicalMaterial({
      color: 0x1f2023,
      roughness: 0.45,
      metalness: 0,
      clearcoat: 0.35,
      clearcoatRoughness: 0.22,
      transparent: true,
    });
    const top = new THREE.Mesh(new THREE.CircleGeometry(R, 96), this.topMat);
    top.rotation.x = -Math.PI / 2;
    top.position.set(CENTER.x, 0.0011, CENTER.z);
    top.receiveShadow = true;
    top.renderOrder = 1;
    this.visual.add(top);

    // ── chamfered rim (6 mm high, outside the product footprint) ──
    const prof = [
      new THREE.Vector2(R - 0.002, 0.0),
      new THREE.Vector2(R - 0.002, 0.0045),
      new THREE.Vector2(R + 0.004, 0.006),
      new THREE.Vector2(R + 0.016, 0.006),
      new THREE.Vector2(R + 0.026, 0.0025),
      new THREE.Vector2(R + 0.028, 0.0),
    ];
    // satin anodised bezel: a mostly-dielectric finish so it catches the key as a fine light line instead of mirroring
    // the dark dome
    this.rimMat = new THREE.MeshStandardMaterial({ color: 0x75787e, metalness: 0.35, roughness: 0.36, transparent: true });
    const rim = new THREE.Mesh(new THREE.LatheGeometry(prof, 128), this.rimMat);
    rim.position.copy(CENTER);
    rim.castShadow = false;
    rim.receiveShadow = true;
    this.visual.add(rim);

    // ── LED line at the foot of the rim + faint floor spill ──
    this.ledMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1, 0.86, 0.7), transparent: true, toneMapped: false });
    const led = new THREE.Mesh(new THREE.TorusGeometry(R + 0.029, 0.0008, 6, 192), this.ledMat);
    led.rotation.x = -Math.PI / 2;
    led.position.set(CENTER.x, 0.0012, CENTER.z);
    this.visual.add(led);

    this.spillMat = new THREE.ShaderMaterial({
      uniforms: { uK: { value: 0 }, uColor: { value: new THREE.Color(1, 0.8, 0.6) } },
      vertexShader: fadeVert,
      fragmentShader: /* glsl */ `
uniform float uK; uniform vec3 uColor; varying vec2 vUv;
void main() {
  float r = length(vUv - 0.5) * 2.0;         // 0 centre … 1 edge of the quad
  float inner = ${((R + 0.029) / (R + 0.2)).toFixed(4)};
  float t = (r - inner) / (1.0 - inner);
  float a = r < inner ? 0.0 : exp(-t * 9.0) * (1.0 - smoothstep(0.85, 1.0, r));
  gl_FragColor = vec4(uColor * a * uK, 1.0);
}`,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const spill = new THREE.Mesh(new THREE.PlaneGeometry((R + 0.2) * 2, (R + 0.2) * 2), this.spillMat);
    spill.rotation.x = -Math.PI / 2;
    spill.position.set(CENTER.x, 0.0014, CENTER.z);
    spill.renderOrder = 2;
    this.visual.add(spill);

    // ── backdrop dome: graded charcoal with a soft cool-neutral glow behind the product ──
    this.backMat = new THREE.ShaderMaterial({
      uniforms: { uK: { value: 0 }, uHorizon: { value: STAGE_HORIZON } },
      vertexShader: fadeVert,
      fragmentShader: /* glsl */ `
uniform float uK; uniform vec3 uHorizon; varying vec3 vWorld;
void main() {
  vec3 d = normalize(vWorld - vec3(${CENTER.x.toFixed(3)}, 0.0, ${CENTER.z.toFixed(3)}));
  // exactly the fog colour at the horizon, falling to near-black overhead
  vec3 base = mix(uHorizon, uHorizon * 0.35, smoothstep(0.02, 0.6, d.y));
  // soft haze glow behind the product, lifted off the horizon so the floor line stays seamless
  vec2 g = vec2(d.x * 1.6, d.y - 0.2);
  float glow = exp(-dot(g, g) * 9.0) * smoothstep(0.0, 0.12, d.y) * step(d.z, 0.0);
  gl_FragColor = vec4(base + vec3(0.013, 0.0135, 0.016) * glow, uK);
}`,
      side: THREE.BackSide,
      transparent: true,
      depthWrite: false,
      fog: false,
    });
    const dome = new THREE.Mesh(new THREE.SphereGeometry(14, 48, 24), this.backMat);
    dome.position.set(CENTER.x, 0, CENTER.z);
    dome.renderOrder = -2;
    dome.frustumCulled = false;
    this.visual.add(dome);

    // ── beams: centre key + two back rims, apexes off-frame ──
    const mkBeam = (from: THREE.Vector3, to: THREE.Vector3, radius: number, color: THREE.Color) => {
      const len = from.distanceTo(to);
      const g = new THREE.ConeGeometry(radius, len, 48, 1, true);
      // cone apex at +y: move so apex sits at origin, then orient apex→floor along -Y local
      g.translate(0, -len / 2, 0);
      const m = beamMaterial(color);
      this.beams.push(m);
      const mesh = new THREE.Mesh(g, m);
      mesh.position.copy(from);
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, -1, 0), to.clone().sub(from).normalize());
      mesh.renderOrder = 4;
      mesh.frustumCulled = false;
      this.visual.add(mesh);
    };
    const keyFrom = new THREE.Vector3(CENTER.x + 0.35, 3.4, CENTER.z + 0.35);
    const keyTo = CENTER.clone();
    mkBeam(keyFrom, keyTo, 0.5, new THREE.Color(0.075, 0.072, 0.066));
    const rlFrom = new THREE.Vector3(CENTER.x - 1.7, 3.2, CENTER.z - 1.6);
    const rrFrom = new THREE.Vector3(CENTER.x + 1.8, 3.2, CENTER.z - 1.5);
    mkBeam(rlFrom, new THREE.Vector3(CENTER.x - 0.35, 0, CENTER.z - 0.3), 0.42, new THREE.Color(0.05, 0.054, 0.064));
    mkBeam(rrFrom, new THREE.Vector3(CENTER.x + 0.4, 0, CENTER.z - 0.25), 0.42, new THREE.Color(0.05, 0.054, 0.064));

    // ── real lights ──
    this.key = new THREE.SpotLight(0xfff3e6, 0, 7, 0.16, 1, 2);
    this.key.position.copy(keyFrom);
    this.key.target.position.set(CENTER.x, 0.35, CENTER.z);
    this.key.castShadow = true;
    const ms = tier === 'high' ? 1024 : 512;
    this.key.shadow.mapSize.set(ms, ms);
    this.key.shadow.camera.near = 1.5;
    this.key.shadow.camera.far = 5;
    this.key.shadow.bias = -0.0004;
    this.key.shadow.normalBias = 0.01;
    this.key.shadow.radius = 5;
    this.rimL = new THREE.SpotLight(0xdde6ff, 0, 7, 0.32, 0.8, 2);
    this.rimL.position.copy(rlFrom);
    this.rimL.target.position.set(CENTER.x, 0.7, CENTER.z);
    this.rimR = new THREE.SpotLight(0xe8eeff, 0, 7, 0.32, 0.8, 2);
    this.rimR.position.copy(rrFrom);
    this.rimR.target.position.set(CENTER.x, 0.8, CENTER.z);
    this.group.add(this.key, this.key.target, this.rimL, this.rimL.target, this.rimR, this.rimR.target, this.visual);

    this.visual.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) this.disposables.push(m.geometry);
    });
    this.disposables.push(this.floorMat, this.topMat, this.rimMat, this.ledMat, this.spillMat, this.backMat, ...this.beams);
    scene.add(this.group);
    this.setAmount(1, 0);
  }

  /** s: stage presence 0..1 (already eased by the caller); reveal: Floor reveal 0..1 (drives the floor dissolve). */
  setAmount(s: number, reveal: number) {
    this.floorU.uReveal.value = reveal;
    // the dark floor dissolves through the reveal mask and fades in lock-step with the backdrop and fog, so the
    // horizon never separates and the floor is never re-lit as a grey disc mid-transition
    this.floorU.uFade.value = 1 - Math.pow(1 - s, 3);
    if (s === this.s) return;
    this.s = s;
    const vis = s > 0.001;
    this.visual.visible = vis;
    // podium fades a little later than the beams/backdrop so the product never looks like it is floating
    const podium = THREE.MathUtils.smoothstep(s, 0.05, 0.6);
    this.topMat.opacity = podium;
    this.rimMat.opacity = podium;
    this.topMat.depthWrite = podium > 0.99;
    this.rimMat.depthWrite = podium > 0.99;
    this.ledMat.color.setRGB(1, 0.86, 0.7).multiplyScalar(2.4);
    this.ledMat.opacity = podium;
    this.spillMat.uniforms.uK.value = 0.22 * podium;
    this.backMat.uniforms.uK.value = 1 - Math.pow(1 - s, 3);
    for (const b of this.beams) b.uniforms.uK.value = s * s;
    this.key.intensity = 24 * s;
    this.rimL.intensity = 30 * s;
    this.rimR.intensity = 26 * s;
    this.key.shadow.autoUpdate = vis;
    if (!vis) this.key.shadow.needsUpdate = false;
  }

  get amount() {
    return Math.max(0, this.s);
  }

  dispose() {
    this.scene.remove(this.group);
    for (const d of this.disposables) d.dispose();
    this.key.shadow.map?.dispose();
  }
}
