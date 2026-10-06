/**
 * three.js view of the authoritative DirtSimulation. Reads sim state only (never owns mess state).
 *
 *   const dirt = new DirtRenderer(sim, { quality });
 *   scene.add(dirt.group);           // keep the group at identity transform (world-space geometry)
 *   each frame after sim.step():  dirt.sync(time)
 *   dirt.setSurface('oak'|'stone'|'carpet'); dirt.setQuality('high'|'balanced'); dirt.dispose();
 *
 * Layers: dust decal (y≈0.0006, RGBA8 DataTexture R=density G=tone, dirty-row uploads, procedural grain
 * shader on MeshStandardMaterial so it receives scene light + shadows), long-hair ribbons, pet-hair
 * fiber ribbons, crumbs (6 InstancedMeshes from a procedural library), motes (Points).
 */
import * as THREE from 'three';
import type { QualityTier, SurfaceKind } from '../../contracts/types';
import { CRUMB_UNDER_SHELL, DirtSimulation } from '../DirtSimulation';
import { MAX_CLUMPS, MAX_CRUMBS, MAX_FIBERS_PER_CLUMP, MAX_MOTES, MAX_STRANDS, MAX_STRAND_POINTS } from '../constants';
import { CRUMB_SHAPE_COUNT, makeCrumbGeometry } from './crumbGeometry';
import { RibbonBuffers, makeRibbonMaterial, type RibbonUniforms } from './ribbonMaterial';
import { hash2 } from '../rng';

export interface DirtRendererOptions {
  quality: QualityTier;
}

const DUST_Y = 0.0006;
const HAIR_Y = 0.0005;
const PET_Y = 0.0007;

const toLin = (c: number) => Math.pow(c, 2.2);

interface SurfaceTuning {
  dustContrast: number;
  dustSoft: number;
  /** Linear-RGB colour the dust film is pushed toward and how far (carpet: lighter grey dulling). */
  dustTint: [number, number, number];
  dustTintMix: number;
  /** Extra fine-grain contrast in the film alpha. */
  dustGrain: number;
  crumbSink: number;
  hairY: number;
  hairWidthMul: number;
  hairShade: number;
  hairAlpha: number;
  petWidthMul: number;
  minPx: number;
}

const SURFACE_TUNING: Record<SurfaceKind, SurfaceTuning> = {
  oak: { dustContrast: 1, dustSoft: 0, dustTint: [0, 0, 0], dustTintMix: 0, dustGrain: 0, crumbSink: 0, hairY: 0, hairWidthMul: 1, hairShade: 1, hairAlpha: 0.95, petWidthMul: 1, minPx: 1 },
  stone: { dustContrast: 1, dustSoft: 0, dustTint: [0, 0, 0], dustTintMix: 0, dustGrain: 0, crumbSink: 0, hairY: 0, hairWidthMul: 1, hairShade: 1, hairAlpha: 0.95, petWidthMul: 1, minPx: 1 },
  // carpet: dust reads as a lighter, greyer dulling of the beige pile (with coarse grain), crumbs sit a
  // touch lower; hair sits on top of the pile — wider, darker and opaque so it keeps its contrast.
  carpet: {
    dustContrast: 1,
    dustSoft: 0.25,
    dustTint: [0.55, 0.55, 0.54],
    dustTintMix: 0.68,
    dustGrain: 0.35,
    crumbSink: 0.18,
    hairY: 0.0012,
    hairWidthMul: 1.9,
    hairShade: 0.5,
    hairAlpha: 1,
    petWidthMul: 1.35,
    minPx: 1.4,
  },
};

export class DirtRenderer {
  readonly group = new THREE.Group();
  private quality: QualityTier;
  private surface: SurfaceKind = 'oak';

  // dust
  private dustTex!: THREE.DataTexture;
  private dustData!: Uint8Array;
  private texW = 0;
  private texH = 0;
  private readonly dustMat: THREE.MeshStandardMaterial;
  private readonly dustMesh: THREE.Mesh;
  private readonly dustUniforms = {
    uDust: { value: null as THREE.Texture | null },
    uAreaMin: { value: new THREE.Vector2() },
    uAreaSize: { value: new THREE.Vector2() },
    uContrast: { value: 1 },
    uSoft: { value: 0 },
    uTint: { value: new THREE.Vector3() },
    uTintMix: { value: 0 },
    uGrainBoost: { value: 0 },
  };
  private readonly dirtyRect = new Int32Array(4);
  private readonly pendingRect = new Int32Array([0, 0, -1, -1]);
  private texFresh = true;

  // ribbons
  private readonly ribbonUniforms: RibbonUniforms = { uResolution: { value: new THREE.Vector2(1920, 1080) }, uMinPx: { value: 1.0 } };
  private readonly hairBuf: RibbonBuffers;
  private readonly petBuf: RibbonBuffers;
  private readonly hairMesh: THREE.Mesh;
  private readonly petMesh: THREE.Mesh;
  private readonly hairMat: THREE.MeshStandardMaterial;
  private readonly petMat: THREE.MeshStandardMaterial;
  private hairVersion = -1;
  private petVersion = -1;

  // crumbs
  private readonly crumbMeshes: THREE.InstancedMesh[] = [];
  private readonly crumbMat: THREE.MeshStandardMaterial;
  private crumbVersion = -1;

  // motes
  private readonly motePos = new Float32Array(MAX_MOTES * 3);
  private readonly moteAlpha = new Float32Array(MAX_MOTES);
  private readonly moteGeom = new THREE.BufferGeometry();
  private readonly moteMat: THREE.ShaderMaterial;
  private readonly motes: THREE.Points;

  // scratch
  private readonly m4 = new THREE.Matrix4();
  private readonly q = new THREE.Quaternion();
  private readonly qRoll = new THREE.Quaternion();
  private readonly v3 = new THREE.Vector3();
  private readonly s3 = new THREE.Vector3();
  private readonly axis = new THREE.Vector3();
  private readonly up = new THREE.Vector3(0, 1, 0);
  private readonly color = new THREE.Color();
  private readonly drawSize = new THREE.Vector2();
  private readonly tmpX = new Float32Array(64);
  private readonly tmpZ = new Float32Array(64);
  private readonly shapeCount = new Int32Array(CRUMB_SHAPE_COUNT);

  constructor(
    private readonly sim: DirtSimulation,
    opts: DirtRendererOptions,
  ) {
    this.quality = opts.quality;
    this.group.name = 'DirtRenderer';
    const a = sim.area;

    // ---------------- dust decal ----------------
    this.dustUniforms.uAreaMin.value.set(a.minX, a.minZ);
    this.dustUniforms.uAreaSize.value.set(a.maxX - a.minX, a.maxZ - a.minZ);
    this.buildDustTexture();
    this.dustMat = new THREE.MeshStandardMaterial({
      roughness: 1,
      metalness: 0,
      transparent: true,
      depthWrite: false,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -4,
    });
    this.dustMat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, this.dustUniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec2 vDustWorld;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvDustWorld = ( modelMatrix * vec4( transformed, 1.0 ) ).xz;');
      shader.fragmentShader = shader.fragmentShader
        .replace(
          '#include <common>',
          `#include <common>
varying vec2 vDustWorld;
uniform sampler2D uDust;
uniform vec2 uAreaMin;
uniform vec2 uAreaSize;
uniform float uContrast;
uniform float uSoft;
uniform vec3 uTint;
uniform float uTintMix;
uniform float uGrainBoost;
float dHash( vec2 p ) { p = fract( p * vec2( 123.34, 456.21 ) ); p += dot( p, p + 45.32 ); return fract( p.x * p.y ); }
float dNoise( vec2 p ) {
  vec2 i = floor( p ); vec2 f = fract( p ); f = f * f * ( 3.0 - 2.0 * f );
  return mix( mix( dHash( i ), dHash( i + vec2( 1.0, 0.0 ) ), f.x ), mix( dHash( i + vec2( 0.0, 1.0 ) ), dHash( i + vec2( 1.0, 1.0 ) ), f.x ), f.y );
}`,
        )
        .replace(
          '#include <map_fragment>',
          `{
  vec2 fuv = ( vDustWorld - uAreaMin ) / uAreaSize;
  vec4 dS = texture2D( uDust, fuv );
  float dens = dS.r;
  float tone = dS.g;
  // fine grain (≈0.4 mm) faded by screen-space derivative to avoid shimmer; mid/low octaves always on
  vec2 pf = vDustWorld * 2500.0;
  float fw = length( fwidth( pf ) );
  float hiFade = 1.0 - smoothstep( 0.5, 1.5, fw );
  float g1 = mix( 0.5, dHash( floor( pf ) ), hiFade );
  float g2 = dNoise( vDustWorld * 650.0 );
  float g3 = dNoise( vDustWorld * 160.0 + 13.0 );
  float grain = g1 * 0.4 + g2 * 0.35 + g3 * 0.25;
  // soft film: optical-depth style coverage, broken up by grain (stronger grain where the film is thin)
  // low-contrast film (soft optical-depth curve, capped) so patches read as a dulling, not ink
  float film = 1.0 - exp( -dens * ( 3.0 - uSoft * 0.8 ) );
  float alpha = clamp( film * ( 0.7 + ( 0.7 + uGrainBoost ) * ( g1 - 0.5 ) + 0.3 * ( g2 - 0.5 ) + 0.2 * ( g3 - 0.5 ) ), 0.0, 1.0 );
  alpha *= smoothstep( 0.004, 0.05, dens );
  // sparse flecks (lint / grit) where dust is present: dark and light ones
  vec2 sp = vDustWorld * 900.0;
  float spFade = 1.0 - smoothstep( 0.6, 1.4, length( fwidth( sp ) ) );
  float hs = dHash( floor( sp ) + 31.7 );
  float presence = smoothstep( 0.04, 0.25, dens );
  float speckD = step( 0.975 - 0.05 * dens, hs ) * presence * spFade;
  float speckL = step( hs, 0.012 + 0.02 * dens ) * presence * spFade;
  // household dust palette (linear): grey-brown film, lighter beige-grey fluff, darker lint
  vec3 cMid = vec3( 0.3, 0.27, 0.235 );
  vec3 cLight = vec3( 0.43, 0.4, 0.355 );
  vec3 cDark = vec3( 0.12, 0.11, 0.1 );
  vec3 col = mix( mix( cMid * 0.72, cMid, smoothstep( 0.0, 0.5, tone ) ), cLight, smoothstep( 0.5, 1.0, tone ) * 0.6 + g2 * 0.15 );
  col *= 0.84 + 0.32 * g1;
  col = mix( col, uTint * ( 0.9 + 0.2 * g1 ), uTintMix );
  col = mix( col, cDark * 0.7, speckD * 0.85 );
  col = mix( col, cLight * 1.25, speckL * 0.8 );
  alpha = max( alpha, max( speckD, speckL ) * 0.9 );
  diffuseColor.rgb = col;
  diffuseColor.a *= clamp( alpha * 0.82 * uContrast, 0.0, 0.85 );
}`,
        );
    };
    this.dustMat.customProgramCacheKey = () => 'dirt-dust-v2';
    const dustGeom = new THREE.PlaneGeometry(a.maxX - a.minX, a.maxZ - a.minZ, 1, 1);
    dustGeom.rotateX(-Math.PI / 2);
    dustGeom.translate((a.minX + a.maxX) / 2, DUST_Y, (a.minZ + a.maxZ) / 2);
    this.dustMesh = new THREE.Mesh(dustGeom, this.dustMat);
    this.dustMesh.name = 'DustDecal';
    this.dustMesh.receiveShadow = true;
    this.dustMesh.renderOrder = 1;
    this.dustMesh.onBeforeRender = () => this.uploadDust();
    this.group.add(this.dustMesh);

    // ---------------- hair / pet ribbons ----------------
    // hair: up to (12 segs × 3 subdiv + extra) pairs per strand
    this.hairBuf = new RibbonBuffers(MAX_STRANDS * (MAX_STRAND_POINTS * 3 + 8) * 2);
    this.petBuf = new RibbonBuffers(MAX_CLUMPS * MAX_FIBERS_PER_CLUMP * 4 * 2);
    this.hairMat = makeRibbonMaterial(this.ribbonUniforms, 0.5);
    this.petMat = makeRibbonMaterial(this.ribbonUniforms, 0.75);
    this.hairMesh = new THREE.Mesh(this.hairBuf.geometry, this.hairMat);
    this.petMesh = new THREE.Mesh(this.petBuf.geometry, this.petMat);
    this.hairMesh.name = 'HairRibbons';
    this.petMesh.name = 'PetHairFibers';
    for (const m of [this.hairMesh, this.petMesh]) {
      m.frustumCulled = false;
      m.renderOrder = 2;
      m.onBeforeRender = (renderer) => {
        renderer.getDrawingBufferSize(this.drawSize);
        this.ribbonUniforms.uResolution.value.copy(this.drawSize);
      };
      this.group.add(m);
    }

    // ---------------- crumbs ----------------
    this.crumbMat = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0 });
    this.crumbMat.onBeforeCompile = (shader) => {
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <roughnessmap_fragment>',
        `#include <roughnessmap_fragment>
#if defined( USE_COLOR ) || defined( USE_COLOR_ALPHA )
  // darker, crustier crumbs read slightly glossier; pale crumb interior is matte
  roughnessFactor = clamp( roughnessFactor + ( vColor.g - 0.3 ) * 0.35, 0.55, 0.95 );
#endif`,
      );
    };
    this.crumbMat.customProgramCacheKey = () => 'dirt-crumb-v1';
    const detail = this.quality === 'high' ? 1 : 0;
    for (let s = 0; s < CRUMB_SHAPE_COUNT; s++) {
      const im = new THREE.InstancedMesh(makeCrumbGeometry(s, detail), this.crumbMat, MAX_CRUMBS);
      im.name = `Crumbs_${s}`;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      im.setColorAt(0, this.color.setRGB(1, 1, 1));
      im.instanceColor!.setUsage(THREE.DynamicDrawUsage);
      im.count = 0;
      im.frustumCulled = false;
      im.castShadow = this.quality === 'high';
      im.receiveShadow = true;
      this.crumbMeshes.push(im);
      this.group.add(im);
    }

    // ---------------- motes ----------------
    this.moteGeom.setAttribute('position', new THREE.BufferAttribute(this.motePos, 3).setUsage(THREE.DynamicDrawUsage));
    this.moteGeom.setAttribute('aAlpha', new THREE.BufferAttribute(this.moteAlpha, 1).setUsage(THREE.DynamicDrawUsage));
    this.moteGeom.setDrawRange(0, MAX_MOTES);
    this.moteMat = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: { uViewportH: { value: 1080 }, uSize: { value: 0.0007 }, uColor: { value: new THREE.Color(0.42, 0.38, 0.33) } },
      vertexShader: `
attribute float aAlpha;
uniform float uViewportH;
uniform float uSize;
varying float vA;
void main() {
  vec4 mv = modelViewMatrix * vec4( position, 1.0 );
  gl_Position = projectionMatrix * mv;
  float px = uSize * projectionMatrix[1][1] * 0.5 * uViewportH / max( -mv.z, 1e-3 );
  float k = max( 1.0, 1.5 / max( px, 1e-3 ) );
  gl_PointSize = clamp( px * k, 1.0, 6.0 );
  vA = aAlpha / k;
}`,
      fragmentShader: `
uniform vec3 uColor;
varying float vA;
void main() {
  vec2 c = gl_PointCoord - 0.5;
  float a = vA * ( 1.0 - smoothstep( 0.2, 0.5, length( c ) ) );
  if ( a < 0.01 ) discard;
  gl_FragColor = vec4( uColor, a );
  #include <colorspace_fragment>
}`,
    });
    this.motes = new THREE.Points(this.moteGeom, this.moteMat);
    this.motes.name = 'DustMotes';
    this.motes.frustumCulled = false;
    this.motes.renderOrder = 3;
    this.motes.onBeforeRender = (renderer) => {
      renderer.getDrawingBufferSize(this.drawSize);
      this.moteMat.uniforms.uViewportH.value = this.drawSize.y;
    };
    this.group.add(this.motes);

    this.applySurface();
  }

  // =====================================================================================

  sync(time: number): void {
    this.syncDust();
    if (this.sim.hairVersion !== this.hairVersion) {
      this.hairVersion = this.sim.hairVersion;
      this.buildHair();
    }
    if (this.sim.petVersion !== this.petVersion) {
      this.petVersion = this.sim.petVersion;
      this.buildPet();
    }
    if (this.sim.crumbVersion !== this.crumbVersion) {
      this.crumbVersion = this.sim.crumbVersion;
      this.buildCrumbs();
    }
    this.syncMotes(time);
  }

  setSurface(surface: SurfaceKind): void {
    this.surface = surface;
    this.applySurface();
  }

  setQuality(tier: QualityTier): void {
    if (tier === this.quality) return;
    this.quality = tier;
    const old = this.dustTex;
    this.buildDustTexture();
    old.dispose();
    const detail = tier === 'high' ? 1 : 0;
    for (let s = 0; s < this.crumbMeshes.length; s++) {
      const im = this.crumbMeshes[s];
      const g = im.geometry;
      im.geometry = makeCrumbGeometry(s, detail);
      g.dispose();
      im.castShadow = tier === 'high';
    }
    this.hairVersion = this.petVersion = this.crumbVersion = -1;
  }

  dispose(): void {
    this.group.removeFromParent();
    this.dustTex.dispose();
    this.dustMesh.geometry.dispose();
    this.dustMat.dispose();
    this.hairBuf.dispose();
    this.petBuf.dispose();
    this.hairMat.dispose();
    this.petMat.dispose();
    for (const im of this.crumbMeshes) {
      im.geometry.dispose();
      im.dispose();
    }
    this.crumbMat.dispose();
    this.moteGeom.dispose();
    this.moteMat.dispose();
    this.group.clear();
  }

  // =====================================================================================
  // dust
  // =====================================================================================

  private buildDustTexture(): void {
    const f = this.quality === 'high' ? 1 : 2;
    this.texW = Math.ceil(this.sim.fieldW / f);
    this.texH = Math.ceil(this.sim.fieldH / f);
    this.dustData = new Uint8Array(this.texW * this.texH * 4);
    const t = new THREE.DataTexture(this.dustData, this.texW, this.texH, THREE.RGBAFormat, THREE.UnsignedByteType);
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearFilter;
    t.generateMipmaps = false;
    t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    t.colorSpace = THREE.NoColorSpace;
    this.dustTex = t;
    this.dustUniforms.uDust.value = t;
    this.convertDust(0, 0, this.texW - 1, this.texH - 1);
    t.needsUpdate = true;
    this.texFresh = true;
    // everything was just converted; pending/dirty rects are obsolete
    this.sim.takeDustDirty(this.dirtyRect);
    this.pendingRect[0] = 0;
    this.pendingRect[1] = 0;
    this.pendingRect[2] = -1;
    this.pendingRect[3] = -1;
  }

  /** Convert texel rect [tx0..tx1]×[ty0..ty1] from the authoritative field. */
  private convertDust(tx0: number, ty0: number, tx1: number, ty1: number): void {
    const sim = this.sim;
    const W = sim.fieldW;
    const H = sim.fieldH;
    const d = sim.dust;
    const tone = sim.dustTone;
    const out = this.dustData;
    const f = this.quality === 'high' ? 1 : 2;
    for (let ty = ty0; ty <= ty1; ty++) {
      for (let tx = tx0; tx <= tx1; tx++) {
        let ds = 0;
        let ts = 0;
        let n = 0;
        for (let oy = 0; oy < f; oy++) {
          const j = ty * f + oy;
          if (j >= H) break;
          for (let ox = 0; ox < f; ox++) {
            const i = tx * f + ox;
            if (i >= W) break;
            const k = j * W + i;
            ds += d[k];
            ts += tone[k] * d[k];
            n++;
          }
        }
        const o = (ty * this.texW + tx) * 4;
        const dv = n > 0 ? ds / n : 0;
        out[o] = Math.min(255, Math.round(dv * 255));
        out[o + 1] = ds > 0 ? Math.min(255, Math.round((ts / ds) * 255)) : 0;
        out[o + 2] = 0;
        out[o + 3] = 255;
      }
    }
  }

  /** Collect the sim's dirty cell rect; the upload happens in the decal's onBeforeRender. */
  private syncDust(): void {
    if (!this.sim.takeDustDirty(this.dirtyRect)) return;
    const r = this.dirtyRect;
    const p = this.pendingRect;
    if (p[2] < p[0]) {
      p.set(r);
    } else {
      p[0] = Math.min(p[0], r[0]);
      p[1] = Math.min(p[1], r[1]);
      p[2] = Math.max(p[2], r[2]);
      p[3] = Math.max(p[3], r[3]);
    }
  }

  /**
   * Called right before the decal draws (so ranges are consumed by this upload): converts the pending
   * rect and queues row-wise partial uploads; large rects or a fresh texture get one full upload.
   */
  private uploadDust(): void {
    const p = this.pendingRect;
    if (p[2] < p[0]) return;
    const f = this.quality === 'high' ? 1 : 2;
    const tx0 = Math.floor(p[0] / f);
    const ty0 = Math.floor(p[1] / f);
    const tx1 = Math.min(this.texW - 1, Math.floor(p[2] / f));
    const ty1 = Math.min(this.texH - 1, Math.floor(p[3] / f));
    p[0] = 0;
    p[1] = 0;
    p[2] = -1;
    p[3] = -1;
    this.convertDust(tx0, ty0, tx1, ty1);
    const t = this.dustTex;
    if (this.texFresh || ty1 - ty0 >= 96) {
      t.clearUpdateRanges();
    } else {
      for (let ty = ty0; ty <= ty1; ty++) t.addUpdateRange((ty * this.texW + tx0) * 4, (tx1 - tx0 + 1) * 4);
    }
    this.texFresh = false;
    t.needsUpdate = true;
  }

  // =====================================================================================
  // hair
  // =====================================================================================

  private buildHair(): void {
    const sim = this.sim;
    const buf = this.hairBuf;
    const sub = this.quality === 'high' ? 3 : 2;
    const tun = SURFACE_TUNING[this.surface];
    const y = HAIR_Y + tun.hairY;
    buf.begin();
    for (let s = 0; s < MAX_STRANDS; s++) {
      if (!sim.strandAlive[s]) continue;
      const base = s * MAX_STRAND_POINTS;
      const n = sim.strandN[s];
      const hw = sim.strandWidth[s] * 0.5 * tun.hairWidthMul;
      const r = toLin(sim.strandColor[s * 3]) * tun.hairShade;
      const g = toLin(sim.strandColor[s * 3 + 1]) * tun.hairShade;
      const b = toLin(sim.strandColor[s * 3 + 2]) * tun.hairShade;
      let p = 0;
      while (p < n) {
        if (!sim.strandPointLive[base + p]) {
          p++;
          continue;
        }
        let q = p;
        while (q + 1 < n && sim.strandPointLive[base + q + 1]) q++;
        // piece [p, q]
        let m = 0;
        if (q === p) {
          // lone point: short stub along the original neighbour direction so its mass stays visible
          const nb = p > 0 ? base + p - 1 : base + p + 1;
          const dx = sim.strandPX[nb] - sim.strandPX[base + p];
          const dz = sim.strandPZ[nb] - sim.strandPZ[base + p];
          const d = Math.hypot(dx, dz) || 1;
          this.tmpX[0] = sim.strandPX[base + p];
          this.tmpZ[0] = sim.strandPZ[base + p];
          this.tmpX[1] = this.tmpX[0] + (dx / d) * 0.003;
          this.tmpZ[1] = this.tmpZ[0] + (dz / d) * 0.003;
          m = 2;
        } else {
          for (let k = p; k < q; k++) {
            const i0 = base + Math.max(p, k - 1);
            const i1 = base + k;
            const i2 = base + k + 1;
            const i3 = base + Math.min(q, k + 2);
            for (let t = 0; t < sub; t++) {
              const u = t / sub;
              this.tmpX[m] = catmull(sim.strandPX[i0], sim.strandPX[i1], sim.strandPX[i2], sim.strandPX[i3], u);
              this.tmpZ[m] = catmull(sim.strandPZ[i0], sim.strandPZ[i1], sim.strandPZ[i2], sim.strandPZ[i3], u);
              m++;
            }
          }
          this.tmpX[m] = sim.strandPX[base + q];
          this.tmpZ[m] = sim.strandPZ[base + q];
          m++;
        }
        const isTipStart = p === 0;
        const isTipEnd = q === n - 1;
        for (let k = 0; k < m; k++) {
          const ka = Math.max(0, k - 1);
          const kb = Math.min(m - 1, k + 1);
          let tx = this.tmpX[kb] - this.tmpX[ka];
          let tz = this.tmpZ[kb] - this.tmpZ[ka];
          const tl = Math.hypot(tx, tz) || 1;
          tx /= tl;
          tz /= tl;
          const u = m > 1 ? k / (m - 1) : 0;
          // taper toward free tips; slight tone change along the length
          const taper = Math.min(isTipStart ? Math.min(1, 0.45 + u * 4) : 1, isTipEnd ? Math.min(1, 0.45 + (1 - u) * 4) : 1);
          const shade = 0.88 + 0.24 * u;
          const ww = hw * taper;
          if (!buf.pushPair(this.tmpX[k], y, this.tmpZ[k], -tz * ww, tx * ww, r * shade, g * shade, b * shade, tun.hairAlpha * (0.6 + 0.4 * taper), k > 0)) break;
        }
        p = q + 1;
      }
    }
    buf.commit();
  }

  private buildPet(): void {
    const sim = this.sim;
    const buf = this.petBuf;
    const K = this.quality === 'high' ? 3 : 2;
    const petMul = SURFACE_TUNING[this.surface].petWidthMul;
    const y = PET_Y + SURFACE_TUNING[this.surface].hairY;
    buf.begin();
    const total = MAX_CLUMPS * MAX_FIBERS_PER_CLUMP;
    for (let i = 0; i < total; i++) {
      if (!sim.fibAlive[i]) continue;
      const L = sim.fibLen[i] * sim.fibStretch[i];
      const curl = sim.fibCurl[i] / sim.fibStretch[i];
      const hw = (0.00034 + 0.0001 * hash2(i, 7, 3)) * petMul; // 0.7–0.9 mm full width (wider on carpet)
      const r = toLin(sim.fibColor[i * 3]);
      const g = toLin(sim.fibColor[i * 3 + 1]);
      const b = toLin(sim.fibColor[i * 3 + 2]);
      let x = sim.fibX[i];
      let z = sim.fibZ[i];
      let ang = sim.fibAng[i];
      const ds = L / K;
      // fibers in a clump overlap: tiny height jitter keeps them from z-fighting each other
      const yy = y + hash2(i, 3, 9) * 0.0003;
      for (let k = 0; k <= K; k++) {
        const u = k / K;
        const taper = 1 - 0.55 * u;
        const tx = Math.cos(ang);
        const tz = Math.sin(ang);
        if (!buf.pushPair(x, yy, z, -tz * hw * taper, tx * hw * taper, r, g, b, 0.95 * (1 - 0.4 * u), k > 0)) break;
        ang += curl * ds * 0.5;
        x += Math.cos(ang) * ds;
        z += Math.sin(ang) * ds;
        ang += curl * ds * 0.5;
      }
    }
    buf.commit();
  }

  // =====================================================================================
  // crumbs
  // =====================================================================================

  private buildCrumbs(): void {
    const sim = this.sim;
    const sink = SURFACE_TUNING[this.surface].crumbSink;
    this.shapeCount.fill(0);
    for (let i = 0; i < sim.crumbHigh; i++) {
      if (!sim.crumbAlive[i]) continue;
      // under the outer shell: hidden (occluded), never drawn through the cover
      if (sim.crumbFlags[i] & CRUMB_UNDER_SHELL) continue;
      const shape = sim.crumbShape[i];
      const im = this.crumbMeshes[shape];
      const slot = this.shapeCount[shape]++;
      const s = sim.crumbSize[i];
      const hv = hash2(sim.crumbId[i], 5, 1);
      this.q.setFromAxisAngle(this.up, sim.crumbYaw[i]);
      const roll = sim.crumbRoll[i];
      if (roll !== 0) {
        const d = sim.crumbRollDir[i];
        this.axis.set(Math.sin(d), 0, -Math.cos(d));
        // a partial roll reads as tumbling without lifting the irregular mesh far off the floor
        this.qRoll.setFromAxisAngle(this.axis, roll % (Math.PI * 2) * 0.35);
        this.q.premultiply(this.qRoll);
      }
      this.v3.set(sim.crumbX[i], sim.crumbY[i] - s * sink, sim.crumbZ[i]);
      this.s3.set(s, s * (0.85 + 0.25 * hv), s);
      this.m4.compose(this.v3, this.q, this.s3);
      im.setMatrixAt(slot, this.m4);
      this.color.setRGB(sim.crumbColor[i * 3], sim.crumbColor[i * 3 + 1], sim.crumbColor[i * 3 + 2], THREE.SRGBColorSpace);
      im.setColorAt(slot, this.color);
    }
    for (let sh = 0; sh < this.crumbMeshes.length; sh++) {
      const im = this.crumbMeshes[sh];
      im.count = this.shapeCount[sh];
      im.instanceMatrix.needsUpdate = true;
      if (im.instanceColor) im.instanceColor.needsUpdate = true;
    }
  }

  // =====================================================================================
  // motes / surface
  // =====================================================================================

  private syncMotes(time: number): void {
    const sim = this.sim;
    for (let m = 0; m < MAX_MOTES; m++) {
      if (!sim.moteAlive[m]) {
        this.moteAlpha[m] = 0;
        continue;
      }
      this.motePos[m * 3] = sim.moteX[m];
      this.motePos[m * 3 + 1] = sim.moteY[m];
      this.motePos[m * 3 + 2] = sim.moteZ[m];
      const t = sim.moteLife[m] / sim.moteMaxLife[m];
      // fade in/out; faint flicker as specks tumble through the light
      this.moteAlpha[m] = Math.sin(Math.PI * t) * (0.55 + 0.15 * Math.sin(time * 37 + m * 1.7));
    }
    (this.moteGeom.getAttribute('position') as THREE.BufferAttribute).needsUpdate = true;
    (this.moteGeom.getAttribute('aAlpha') as THREE.BufferAttribute).needsUpdate = true;
    this.motes.visible = sim.moteCount > 0;
  }

  private applySurface(): void {
    const t = SURFACE_TUNING[this.surface];
    this.dustUniforms.uContrast.value = t.dustContrast;
    this.dustUniforms.uSoft.value = t.dustSoft;
    this.dustUniforms.uTint.value.set(t.dustTint[0], t.dustTint[1], t.dustTint[2]);
    this.dustUniforms.uTintMix.value = t.dustTintMix;
    this.dustUniforms.uGrainBoost.value = t.dustGrain;
    this.ribbonUniforms.uMinPx.value = t.minPx;
    this.crumbVersion = this.hairVersion = this.petVersion = -1;
  }
}

function catmull(p0: number, p1: number, p2: number, p3: number, t: number): number {
  const t2 = t * t;
  const t3 = t2 * t;
  return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3);
}
