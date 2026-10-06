import * as THREE from 'three';

/**
 * Floor-lying ribbon material for hair and pet fibers (lit by the scene like any MeshStandardMaterial).
 *
 * Geometry attributes:
 *   position  ribbon centre-line point (world space; the mesh must stay at identity transform)
 *   aOffset   vec2 world-XZ half-width vector perpendicular to the strand
 *   aSide     −1 / +1 (which edge)
 *   aAlpha    per-vertex opacity (tip taper)
 *   color     linear RGB
 *   normal    (0, 1, 0)
 *
 * Shimmer suppression: in the vertex shader the projected ribbon width is measured in pixels; when it
 * is below uMinPx the ribbon is widened to uMinPx and its alpha reduced by the same factor, so a
 * sub-pixel hair keeps constant coverage instead of flickering. Edges are soft (alpha across).
 */
export interface RibbonUniforms {
  uResolution: { value: THREE.Vector2 };
  uMinPx: { value: number };
}

export function makeRibbonMaterial(uniforms: RibbonUniforms, roughness: number): THREE.MeshStandardMaterial {
  const m = new THREE.MeshStandardMaterial({
    vertexColors: true,
    roughness,
    metalness: 0,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -6,
  });
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uResolution = uniforms.uResolution;
    shader.uniforms.uMinPx = uniforms.uMinPx;
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        `#include <common>
attribute vec2 aOffset;
attribute float aSide;
attribute float aAlpha;
uniform vec2 uResolution;
uniform float uMinPx;
varying float vRibbonFade;
varying float vAcross;`,
      )
      .replace(
        '#include <begin_vertex>',
        `vec3 transformed = vec3( position );
{
  vec3 off = vec3( aOffset.x, 0.0, aOffset.y );
  vec4 c0 = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
  vec4 c1 = projectionMatrix * modelViewMatrix * vec4( position + off, 1.0 );
  vec2 dpx = ( c1.xy / c1.w - c0.xy / c0.w ) * 0.5 * uResolution;
  float wpx = 2.0 * length( dpx );
  float k = max( 1.0, uMinPx / max( wpx, 1e-4 ) );
  transformed += off * aSide * k;
  vRibbonFade = aAlpha / k;
  vAcross = aSide;
}`,
      );
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
varying float vRibbonFade;
varying float vAcross;`,
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
diffuseColor.a *= vRibbonFade * ( 1.0 - smoothstep( 0.35, 1.0, abs( vAcross ) ) * 0.85 );`,
      );
  };
  m.customProgramCacheKey = () => 'dirt-ribbon-v1';
  return m;
}

/** Growable-free ribbon buffer: fixed capacity, rewritten in place each update. */
export class RibbonBuffers {
  readonly geometry = new THREE.BufferGeometry();
  readonly pos: Float32Array;
  readonly off: Float32Array;
  readonly side: Float32Array;
  readonly alpha: Float32Array;
  readonly col: Float32Array;
  readonly index: Uint32Array;
  vCount = 0;
  iCount = 0;
  private readonly posAttr: THREE.BufferAttribute;
  private readonly offAttr: THREE.BufferAttribute;
  private readonly alphaAttr: THREE.BufferAttribute;
  private readonly colAttr: THREE.BufferAttribute;
  private readonly indexAttr: THREE.BufferAttribute;

  constructor(readonly maxVerts: number) {
    this.pos = new Float32Array(maxVerts * 3);
    this.off = new Float32Array(maxVerts * 2);
    this.side = new Float32Array(maxVerts);
    this.alpha = new Float32Array(maxVerts);
    this.col = new Float32Array(maxVerts * 3);
    this.index = new Uint32Array(maxVerts * 3);
    const nrm = new Float32Array(maxVerts * 3);
    for (let i = 0; i < maxVerts; i++) {
      nrm[i * 3 + 1] = 1;
      this.side[i] = i & 1 ? 1 : -1;
    }
    this.posAttr = new THREE.BufferAttribute(this.pos, 3).setUsage(THREE.DynamicDrawUsage);
    this.offAttr = new THREE.BufferAttribute(this.off, 2).setUsage(THREE.DynamicDrawUsage);
    this.alphaAttr = new THREE.BufferAttribute(this.alpha, 1).setUsage(THREE.DynamicDrawUsage);
    this.colAttr = new THREE.BufferAttribute(this.col, 3).setUsage(THREE.DynamicDrawUsage);
    this.indexAttr = new THREE.BufferAttribute(this.index, 1).setUsage(THREE.DynamicDrawUsage);
    this.geometry.setAttribute('position', this.posAttr);
    this.geometry.setAttribute('aOffset', this.offAttr);
    this.geometry.setAttribute('aSide', new THREE.BufferAttribute(this.side, 1));
    this.geometry.setAttribute('aAlpha', this.alphaAttr);
    this.geometry.setAttribute('color', this.colAttr);
    this.geometry.setAttribute('normal', new THREE.BufferAttribute(nrm, 3));
    this.geometry.setIndex(this.indexAttr);
    this.geometry.setDrawRange(0, 0);
  }

  begin(): void {
    this.vCount = 0;
    this.iCount = 0;
  }

  /** Append one ribbon vertex pair. `connect` joins it to the previous pair with a quad. */
  pushPair(x: number, y: number, z: number, ox: number, oz: number, r: number, g: number, b: number, a: number, connect: boolean): boolean {
    if (this.vCount + 2 > this.maxVerts) return false;
    const v = this.vCount;
    for (let k = 0; k < 2; k++) {
      const i = v + k;
      this.pos[i * 3] = x;
      this.pos[i * 3 + 1] = y;
      this.pos[i * 3 + 2] = z;
      this.off[i * 2] = ox;
      this.off[i * 2 + 1] = oz;
      this.alpha[i] = a;
      this.col[i * 3] = r;
      this.col[i * 3 + 1] = g;
      this.col[i * 3 + 2] = b;
    }
    if (connect && v >= 2) {
      const ix = this.index;
      let n = this.iCount;
      ix[n++] = v - 2;
      ix[n++] = v - 1;
      ix[n++] = v;
      ix[n++] = v - 1;
      ix[n++] = v + 1;
      ix[n++] = v;
      this.iCount = n;
    }
    this.vCount = v + 2;
    return true;
  }

  commit(): void {
    this.posAttr.clearUpdateRanges();
    this.posAttr.addUpdateRange(0, this.vCount * 3);
    this.offAttr.clearUpdateRanges();
    this.offAttr.addUpdateRange(0, this.vCount * 2);
    this.alphaAttr.clearUpdateRanges();
    this.alphaAttr.addUpdateRange(0, this.vCount);
    this.colAttr.clearUpdateRanges();
    this.colAttr.addUpdateRange(0, this.vCount * 3);
    this.indexAttr.clearUpdateRanges();
    this.indexAttr.addUpdateRange(0, this.iCount);
    this.posAttr.needsUpdate = true;
    this.offAttr.needsUpdate = true;
    this.alphaAttr.needsUpdate = true;
    this.colAttr.needsUpdate = true;
    this.indexAttr.needsUpdate = true;
    this.geometry.setDrawRange(0, this.iCount);
  }

  dispose(): void {
    this.geometry.dispose();
  }
}
