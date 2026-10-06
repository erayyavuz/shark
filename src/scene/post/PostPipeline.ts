import * as THREE from 'three';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { FullScreenQuad } from 'three/examples/jsm/postprocessing/Pass.js';
import type { QualityTier } from '../../contracts/types';

/**
 * Hand-driven post chain (no EffectComposer: no buffer ping-pong parity to track when passes toggle).
 *
 *   scene ──► sceneRT (HalfFloat HDR, MSAA, depth texture)
 *              ├─► GTAO (high tier; normals reconstructed from the resolved depth, no extra scene pass) ─► aoTex
 *              └─► bloom high-pass + mip blur (only HDR values above threshold: LEDs, screen ring, hot light pools)
 *   final quad: scene × AO (+ bloom) → exposure → Khronos PBR Neutral tone map → gentle grade → sRGB → dither
 *
 * Quality: high = MSAA 4, full-res GTAO, bloom from full-res mips; balanced = MSAA 2 (falls back to 0 if unsupported),
 * no AO, half-resolution bloom chain.
 */

const BLUR_X = new THREE.Vector2(1, 0);
const BLUR_Y = new THREE.Vector2(0, 1);

/** UnrealBloomPass without the final additive blend back onto its input; we composite in the output shader. */
class BloomOnly extends UnrealBloomPass {
  get texture(): THREE.Texture {
    return (this as unknown as { renderTargetsHorizontal: THREE.WebGLRenderTarget[] }).renderTargetsHorizontal[0].texture;
  }
  renderBloom(renderer: THREE.WebGLRenderer, input: THREE.WebGLRenderTarget) {
    const self = this as unknown as {
      renderTargetBright: THREE.WebGLRenderTarget;
      renderTargetsHorizontal: THREE.WebGLRenderTarget[];
      renderTargetsVertical: THREE.WebGLRenderTarget[];
      separableBlurMaterials: THREE.ShaderMaterial[];
      nMips: number;
      compositeMaterial: THREE.ShaderMaterial;
      highPassUniforms: Record<string, THREE.IUniform>;
      materialHighPassFilter: THREE.ShaderMaterial;
      bloomTintColors: THREE.Vector3[];
      _fsQuad: FullScreenQuad;
    };
    const q = self._fsQuad;
    const oldAuto = renderer.autoClear;
    renderer.autoClear = false;
    renderer.setClearColor(0x000000, 0);
    self.highPassUniforms.tDiffuse.value = input.texture;
    self.highPassUniforms.luminosityThreshold.value = this.threshold;
    q.material = self.materialHighPassFilter;
    renderer.setRenderTarget(self.renderTargetBright);
    renderer.clear();
    q.render(renderer);
    let inp = self.renderTargetBright;
    for (let i = 0; i < self.nMips; i++) {
      const m = self.separableBlurMaterials[i];
      q.material = m;
      m.uniforms.colorTexture.value = inp.texture;
      m.uniforms.direction.value = BLUR_X;
      renderer.setRenderTarget(self.renderTargetsHorizontal[i]);
      renderer.clear();
      q.render(renderer);
      m.uniforms.colorTexture.value = self.renderTargetsHorizontal[i].texture;
      m.uniforms.direction.value = BLUR_Y;
      renderer.setRenderTarget(self.renderTargetsVertical[i]);
      renderer.clear();
      q.render(renderer);
      inp = self.renderTargetsVertical[i];
    }
    q.material = self.compositeMaterial;
    self.compositeMaterial.uniforms.bloomStrength.value = this.strength;
    self.compositeMaterial.uniforms.bloomRadius.value = this.radius;
    self.compositeMaterial.uniforms.bloomTintColors.value = self.bloomTintColors;
    renderer.setRenderTarget(self.renderTargetsHorizontal[0]);
    renderer.clear();
    q.render(renderer);
    renderer.autoClear = oldAuto;
  }
}

const outputShader = {
  vertexShader: /* glsl */ `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
  fragmentShader: /* glsl */ `
precision highp float;
uniform sampler2D tScene, tBloom, tAO;
uniform float uAO, uBloom, uExposure, uSat, uContrast, uVignette, uNight, uSeed;
uniform vec2 uRes;
varying vec2 vUv;

// Khronos PBR Neutral (identical curve to three's NeutralToneMapping)
// The curve's black-level offset subtracts almost the whole min channel from very dark pixels, which turns a dark
// blue-grey room into saturated navy; at night it is scaled down (the only deviation from the reference curve).
vec3 neutral(vec3 color, float offsetScale) {
  const float startCompression = 0.8 - 0.04;
  const float desaturation = 0.15;
  float x = min(color.r, min(color.g, color.b));
  float offset = (x < 0.08 ? x - 6.25 * x * x : 0.04) * offsetScale;
  color -= offset;
  float peak = max(color.r, max(color.g, color.b));
  if (peak < startCompression) return color;
  float d = 1.0 - startCompression;
  float newPeak = 1.0 - d * d / (peak + d - startCompression);
  color *= newPeak / peak;
  float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);
  return mix(color, vec3(newPeak), g);
}
vec3 srgb(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(max(c, 0.0), vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c));
}
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233)) + uSeed) * 43758.5453); }

void main() {
  vec3 col = texture2D(tScene, vUv).rgb;
  if (uAO > 0.0) col *= mix(1.0, texture2D(tAO, vUv).r, uAO);
  if (uBloom > 0.0) col += texture2D(tBloom, vUv).rgb * uBloom;
  col = neutral(col * uExposure, mix(1.0, 0.3, uNight));
  float l = dot(col, vec3(0.2126, 0.7152, 0.0722));
  col = max(mix(vec3(l), col, uSat), 0.0);
  // night: cool the shadows a touch, keep highlights (LED colour) untouched
  col += uNight * vec3(-0.0004, 0.0, 0.0012) * (1.0 - smoothstep(0.0, 0.08, l));
  vec3 s = srgb(clamp(col, 0.0, 1.0));
  // gentle S-curve around mid-grey
  s = mix(s, s * s * (3.0 - 2.0 * s), uContrast);
  vec2 v = vUv - 0.5;
  v.x *= uRes.x / uRes.y;
  s *= 1.0 - uVignette * smoothstep(0.35, 1.05, length(v));
  // triangular dither kills banding in the dark night gradients
  s += (hash(gl_FragCoord.xy) + hash(gl_FragCoord.xy + 17.3) - 1.0) / 255.0;
  gl_FragColor = vec4(s, 1.0);
}`,
};

export interface PostLook {
  exposure: number;
  /** 0 day … 1 night */
  night: number;
}

export class PostPipeline {
  private sceneRT: THREE.WebGLRenderTarget;
  private gtao: GTAOPass | null = null;
  private bloom: BloomOnly;
  private quad: FullScreenQuad;
  private mat: THREE.ShaderMaterial;
  private w = 1;
  private h = 1;
  private seed = 0;
  private tier: QualityTier;

  constructor(private renderer: THREE.WebGLRenderer, private scene: THREE.Scene, private camera: THREE.Camera, tier: QualityTier, private dev: string | null = null) {
    this.tier = tier;
    const gl = renderer.getContext() as WebGL2RenderingContext;
    const hdr = renderer.extensions.has('EXT_color_buffer_float') || renderer.extensions.has('EXT_color_buffer_half_float');
    const maxSamples = (gl.getParameter(gl.MAX_SAMPLES) as number) || 0;
    const samples = Math.min(maxSamples, tier === 'high' ? 4 : 2);
    const depthTexture = new THREE.DepthTexture(1, 1);
    depthTexture.type = THREE.UnsignedIntType;
    this.sceneRT = new THREE.WebGLRenderTarget(1, 1, {
      type: hdr ? THREE.HalfFloatType : THREE.UnsignedByteType,
      samples,
      depthTexture,
      depthBuffer: true,
    });
    this.sceneRT.texture.name = 'PostSceneHDR';

    if (tier === 'high' && dev !== 'noao') this.makeAO();

    this.bloom = new BloomOnly(new THREE.Vector2(1, 1), 0.3, 0.55, 2.0);
    this.mat = new THREE.ShaderMaterial({
      uniforms: {
        tScene: { value: this.sceneRT.texture },
        tBloom: { value: this.bloom.texture },
        tAO: { value: null },
        uAO: { value: 0 },
        uBloom: { value: 1 },
        uExposure: { value: 1 },
        uSat: { value: 1 },
        uContrast: { value: 0 },
        uVignette: { value: 0 },
        uNight: { value: 0 },
        uSeed: { value: 0 },
        uRes: { value: new THREE.Vector2(1, 1) },
      },
      vertexShader: outputShader.vertexShader,
      fragmentShader: outputShader.fragmentShader,
      depthTest: false,
      depthWrite: false,
      toneMapped: false,
    });
    this.quad = new FullScreenQuad(this.mat);
  }

  private makeAO() {
    const g = new GTAOPass(this.scene, this.camera, 1, 1);
    // reuse the scene pass depth: normals are reconstructed from depth, so no second geometry pass is rendered
    g.setGBuffer(this.sceneRT.depthTexture!, undefined as unknown as THREE.Texture);
    g.updateGtaoMaterial({ radius: 0.09, distanceExponent: 1.4, thickness: 0.6, scale: 1.0, samples: 8, distanceFallOff: 1.0 });
    g.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, rings: 2, samples: 8 });
    g.output = GTAOPass.OUTPUT.Off; // we only want gtaoMap; compositing happens in the output shader
    this.gtao = g;
  }

  setTier(tier: QualityTier) {
    if (tier === this.tier) return;
    this.tier = tier;
    if (tier === 'high' && !this.gtao) this.makeAO();
    if (tier !== 'high' && this.gtao) {
      this.gtao.dispose();
      this.gtao = null;
    }
    this.setSize(this.w, this.h);
  }

  /** Drawing-buffer pixel size (CSS size × DPR). */
  setSize(w: number, h: number) {
    w = Math.max(1, Math.floor(w));
    h = Math.max(1, Math.floor(h));
    this.w = w;
    this.h = h;
    this.sceneRT.setSize(w, h);
    if (this.gtao) {
      // half resolution: AO is low-frequency contact darkening; bilinear upsample in the output pass
      this.gtao.setSize(Math.max(1, Math.round(w / 2)), Math.max(1, Math.round(h / 2)));
      // the internal G-buffer target is never rendered (setGBuffer above); keep it tiny
      (this.gtao as unknown as { normalRenderTarget: THREE.WebGLRenderTarget }).normalRenderTarget.setSize(1, 1);
    }
    const bs = this.tier === 'high' ? 1 : 0.5;
    this.bloom.setSize(Math.max(2, Math.round(w * bs)), Math.max(2, Math.round(h * bs)));
    (this.mat.uniforms.uRes.value as THREE.Vector2).set(w, h);
  }

  render(look: PostLook) {
    const r = this.renderer;
    const n = look.night;
    r.setRenderTarget(this.sceneRT);
    r.render(this.scene, this.camera);

    const u = this.mat.uniforms;
    if (this.gtao) {
      this.gtao.render(r, this.sceneRT, this.sceneRT, 0, false);
      u.tAO.value = this.gtao.gtaoMap;
      // AO matters most in the bright studio; at night it would only muddy the LED pools
      u.uAO.value = THREE.MathUtils.lerp(0.85, 0.35, n);
    } else u.uAO.value = 0;

    // day: only true emitters (LEDs, ring) pass; night: lower threshold so the light pools glow softly
    this.bloom.threshold = THREE.MathUtils.lerp(2.8, 0.55, n); // day: high enough that glossy clear-plastic speculars never bloom
    this.bloom.strength = THREE.MathUtils.lerp(0.18, 0.75, n);
    this.bloom.radius = THREE.MathUtils.lerp(0.35, 0.6, n);
    if (this.dev !== 'nobloom') this.bloom.renderBloom(r, this.sceneRT);
    u.uBloom.value = this.dev === 'nobloom' ? 0 : 1;

    u.uExposure.value = look.exposure;
    u.uSat.value = THREE.MathUtils.lerp(0.97, 1.05, n);
    u.uContrast.value = THREE.MathUtils.lerp(0.1, 0.06, n);
    u.uVignette.value = THREE.MathUtils.lerp(0.1, 0.3, n);
    u.uNight.value = n;
    this.seed = (this.seed + 0.618) % 1;
    u.uSeed.value = this.seed;
    r.setRenderTarget(null);
    this.quad.render(r);
  }

  dispose() {
    this.sceneRT.depthTexture?.dispose();
    this.sceneRT.dispose();
    this.gtao?.dispose();
    this.bloom.dispose();
    this.quad.dispose();
    this.mat.dispose();
  }
}
