import * as THREE from 'three';
import type { SurfaceKind } from '../contracts/types';
import { loadSurface, type SurfaceTextures } from './lookdev/floorSurfaces';

/**
 * One large floor plane whose shader blends: studio seamless (hero) -> surface A/B (play).
 * uReveal expands a soft radial mask from uRevealCenter; uMix crossfades between two surfaces,
 * so a floor change never touches the simulation.
 */
export class Floor {
  readonly mesh: THREE.Mesh;
  private mat: THREE.MeshStandardMaterial;
  private uniforms: Record<string, THREE.IUniform>;
  private current: SurfaceKind | null = null;
  private pending: SurfaceKind | null = null;
  private mixAnim: { t: number; dur: number } | null = null;
  private cache = new Map<SurfaceKind, Promise<SurfaceTextures>>();
  private disposed = false;

  constructor() {
    const blank = new THREE.DataTexture(new Uint8Array([128, 128, 255, 255]), 1, 1);
    blank.needsUpdate = true;
    this.uniforms = {
      uMapA: { value: blank },
      uMapB: { value: blank },
      uNorA: { value: blank },
      uNorB: { value: blank },
      uRghA: { value: blank },
      uRghB: { value: blank },
      uScaleA: { value: 1 },
      uScaleB: { value: 1 },
      uNormalStrA: { value: 1 },
      uNormalStrB: { value: 1 },
      uRoughA: { value: new THREE.Vector2(0.5, 0.5) },
      uRoughB: { value: new THREE.Vector2(0.5, 0.5) },
      uTintA: { value: new THREE.Vector3(1, 1, 1) },
      uTintB: { value: new THREE.Vector3(1, 1, 1) },
      uMix: { value: 0 },
      uReveal: { value: 0 },
      uRevealCenter: { value: new THREE.Vector2(0, 0) },
      uStudio: { value: new THREE.Color('#e3e2de') },
    };
    this.mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.9, metalness: 0 });
    this.mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, this.uniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vFloorPos;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvFloorPos = (modelMatrix * vec4(transformed, 1.0)).xz;');
      shader.fragmentShader = shader.fragmentShader
        .replace(
          '#include <common>',
          `#include <common>
varying vec2 vFloorPos;
uniform sampler2D uMapA, uMapB, uNorA, uNorB, uRghA, uRghB;
uniform float uScaleA, uScaleB, uNormalStrA, uNormalStrB, uMix, uReveal;
uniform vec2 uRoughA, uRoughB, uRevealCenter;
uniform vec3 uStudio, uTintA, uTintB;
float floorMask() {
  float d = length(vFloorPos - uRevealCenter);
  float r = uReveal * 7.0;
  return uReveal >= 0.999 ? 1.0 : smoothstep(r, r - 1.2, d) * smoothstep(0.0, 0.15, uReveal);
}`,
        )
        .replace(
          '#include <map_fragment>',
          `vec2 fuvA = vFloorPos / uScaleA;
vec2 fuvB = vFloorPos / uScaleB;
vec3 fcol = mix(texture2D(uMapA, fuvA).rgb * uTintA, texture2D(uMapB, fuvB).rgb * uTintB, uMix);
float fMask = floorMask();
diffuseColor.rgb = mix(uStudio, fcol, fMask);`,
        )
        .replace(
          '#include <roughnessmap_fragment>',
          `float rA = mix(uRoughA.x, uRoughA.y, texture2D(uRghA, fuvA).g);
float rB = mix(uRoughB.x, uRoughB.y, texture2D(uRghB, fuvB).g);
float roughnessFactor = mix(0.92, mix(rA, rB, uMix), fMask);`,
        )
        .replace(
          '#include <normal_fragment_maps>',
          `{
  vec3 nA = texture2D(uNorA, fuvA).xyz * 2.0 - 1.0; nA.xy *= uNormalStrA;
  vec3 nB = texture2D(uNorB, fuvB).xyz * 2.0 - 1.0; nB.xy *= uNormalStrB;
  vec3 nm = normalize(mix(nA, nB, uMix));
  nm.xy *= fMask;
  vec3 T = normalize((viewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
  vec3 B = normalize((viewMatrix * vec4(0.0, 0.0, -1.0, 0.0)).xyz);
  normal = normalize(T * nm.x + B * nm.y + normal * nm.z);
}`,
        );
    };
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(30, 30), this.mat);
    this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.receiveShadow = true;
    this.mesh.name = 'Floor';
    this.mesh.renderOrder = -1;
  }

  private get(kind: SurfaceKind) {
    let p = this.cache.get(kind);
    if (!p) {
      p = loadSurface(kind);
      this.cache.set(kind, p);
    }
    return p;
  }

  /** Preload without displaying (e.g. oak during hero). */
  preload(kind: SurfaceKind) {
    return this.get(kind).then(() => undefined);
  }

  /** Crossfade to a surface. Instant when `instant`. */
  async setSurface(kind: SurfaceKind, instant = false) {
    if (kind === this.current && !this.pending) return;
    this.pending = kind;
    const tex = await this.get(kind);
    if (this.disposed || this.pending !== kind) return;
    this.pending = null;
    const u = this.uniforms;
    if (this.current === null || instant) {
      this.assign('A', tex);
      this.assign('B', tex);
      u.uMix.value = 0;
      this.mixAnim = null;
    } else {
      // bake whatever is visible into A, then fade to B
      if (u.uMix.value > 0.5) this.copyBtoA();
      this.assign('B', tex);
      u.uMix.value = 0;
      this.mixAnim = { t: 0, dur: 0.7 };
    }
    this.current = kind;
  }

  private copyBtoA() {
    const u = this.uniforms;
    u.uMapA.value = u.uMapB.value;
    u.uNorA.value = u.uNorB.value;
    u.uRghA.value = u.uRghB.value;
    u.uScaleA.value = u.uScaleB.value;
    u.uNormalStrA.value = u.uNormalStrB.value;
    (u.uRoughA.value as THREE.Vector2).copy(u.uRoughB.value);
    (u.uTintA.value as THREE.Vector3).copy(u.uTintB.value);
  }

  private assign(slot: 'A' | 'B', t: SurfaceTextures) {
    const u = this.uniforms;
    u[`uMap${slot}`].value = t.map;
    u[`uNor${slot}`].value = t.normal;
    u[`uRgh${slot}`].value = t.rough;
    u[`uScale${slot}`].value = t.tileSize;
    u[`uNormalStr${slot}`].value = t.normalStrength;
    (u[`uRough${slot}`].value as THREE.Vector2).set(t.roughMin, t.roughMax);
    (u[`uTint${slot}`].value as THREE.Vector3).set(...t.tint);
  }

  set reveal(v: number) {
    this.uniforms.uReveal.value = v;
  }
  get reveal() {
    return this.uniforms.uReveal.value;
  }
  setRevealCenter(x: number, z: number) {
    (this.uniforms.uRevealCenter.value as THREE.Vector2).set(x, z);
  }

  get surface() {
    return this.current;
  }

  update(dt: number) {
    if (!this.mixAnim) return;
    this.mixAnim.t += dt;
    const k = Math.min(1, this.mixAnim.t / this.mixAnim.dur);
    this.uniforms.uMix.value = k * k * (3 - 2 * k);
    if (k >= 1) {
      this.copyBtoA();
      this.uniforms.uMix.value = 0;
      this.mixAnim = null;
    }
  }

  get animating() {
    return this.mixAnim !== null;
  }

  dispose() {
    this.disposed = true;
    this.mesh.geometry.dispose();
    this.mat.dispose();
    for (const p of this.cache.values()) p.then((t) => t.dispose()).catch(() => undefined);
  }
}
