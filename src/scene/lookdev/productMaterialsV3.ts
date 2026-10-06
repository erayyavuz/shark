import * as THREE from 'three';

export type RingState = 'white' | 'purple' | 'lightPurple';

export interface ProductMaterialSet {
  /** 0..1 power-on level: floorhead headlights (white) + violet accent LEDs and the handheld screen ring. */
  setLed(k: number): void;
  /** Handheld screen LED ring colour (DETECT: white = low debris, light purple = clearing, purple = heavy debris). */
  setRing(state: RingState): void;
  setBinFill(node: THREE.Object3D, k: number): void;
  /** Dock "dust bin full" light window (M_DockDisplay, atlas-textured icons). Optional extra over the v2 API. */
  setDockBinFull?(on: boolean): void;
  dispose(): void;
}

/**
 * Runtime material tuning for the v3 GLB (IP3251 / IP3251EUT: gunmetal + purple, bronze wand, white dock).
 * scripts/blender/v3/materials.py is the source of truth for colours / roughness.
 *
 * v3 ORM tiles are generated per material roughness (mean G = authored roughness), so glTF roughnessFactor 1 is
 * already correct: no roughness rescale here (unlike v2), only env-map gain and special materials.
 *
 * LED contract (read by scene/lookdev/productLights.ts): every M_LED* material carries `userData.ledLevel` (0..1) and
 * `userData.ledRole`: 'headlight' (M_LED, cool white front corners) | 'accent' (M_LEDAccent, violet rear corners +
 * strip behind the roller window) | 'ring' (M_LEDRing, handheld screen).
 */
const ENV: Record<string, number> = {
  M_Gunmetal: 1.0,
  M_Charcoal: 0.8,
  M_DockGraphite: 0.9,
  M_Purple: 1.25,
  M_Bronze: 1.6,
  M_Champagne: 1.5,
  M_SilverBrush: 1.6,
  M_Chrome: 1.8,
  M_White: 0.9,
  M_Rubber: 0.45,
  M_Bristle: 0.5,
  M_Hose: 0.8,
  M_Screen: 1.4,
  M_Turquoise: 0.6,
  M_RollerFibre: 0.6,
  M_RollerFront: 0.2,
};

/** soft roller fabrics: sheen (KHR_materials_sheen is exported; this only fills it in if a loader dropped it) */
const FABRIC: Record<string, { sheen: number; tint: number; rough: number; roughness?: number }> = {
  M_Turquoise: { sheen: 0.45, tint: 0xd8fff6, rough: 0.5 },
  M_RollerFibre: { sheen: 0.45, tint: 0xfff4d0, rough: 0.5 },
  // black microfibre pile: a dim neutral sheen only (a white sheen washed it to mid grey in the browser, r1)
  M_RollerFront: { sheen: 0.22, tint: 0x5a5a5a, rough: 0.6, roughness: 1.0 },
};

/**
 * Fresnel opacity for thin clear plastics (no transmission pass): alpha rises toward grazing angles so the shell's
 * edges, thickness and silhouette read like real polycarbonate, while face-on stays see-through. Reflections are
 * also scaled by alpha under normal blending, so this is what makes the env/clearcoat highlights visible at all.
 */
function addFresnelAlpha(m: THREE.MeshPhysicalMaterial, edgeAlpha: number, power: number) {
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uEdgeAlpha = { value: edgeAlpha };
    shader.uniforms.uEdgePow = { value: power };
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uEdgeAlpha;\nuniform float uEdgePow;')
      .replace(
        '#include <normal_fragment_maps>',
        `#include <normal_fragment_maps>
        {
          float ndv = abs(dot(normalize(normal), normalize(vViewPosition)));
          float fr = pow(1.0 - ndv, uEdgePow);
          diffuseColor.a = mix(diffuseColor.a, uEdgeAlpha, fr);
        }`,
      );
  };
  m.customProgramCacheKey = () => `fresnelAlpha:${edgeAlpha}:${power}`;
}

const RING: Record<RingState, THREE.Color> = {
  white: new THREE.Color(0xf2f4ff),
  // user frame 1668 lit ring #4936e8..#4b37f1, lead ref ~#6a3cff
  purple: new THREE.Color(0x5f3cff),
  lightPurple: new THREE.Color(0xc29cff),
};

function prefixLookup<T>(table: Record<string, T>, name: string): T | undefined {
  let best: string | undefined;
  for (const k of Object.keys(table)) if (name.startsWith(k) && (!best || k.length > best.length)) best = k;
  return best ? table[best] : undefined;
}

export function applyProductMaterials(roots: THREE.Object3D[]): ProductMaterialSet {
  const leds: { mat: THREE.MeshStandardMaterial; gain: number }[] = [];
  const rings: THREE.MeshStandardMaterial[] = [];
  const dockDisplays: THREE.MeshStandardMaterial[] = [];
  const created: THREE.Material[] = [];
  const cache = new Map<THREE.Material, THREE.Material>();
  let ledK = 0;
  let ringGain = 1.6;

  /**
   * Thin clear plastics without a transmission pass: a mostly transparent physical surface whose own (lit) colour
   * acts as the tint, plus clearcoat-grade reflections. Double-sided -> see-through factor (1 - opacity)^2.
   */
  const clearFrom = (src: THREE.MeshStandardMaterial, kind: 'bin' | 'cover') => {
    const bin = kind === 'bin';
    const m = new THREE.MeshPhysicalMaterial({
      name: src.name,
      // cover: smoky polycarbonate -- a DARK tint so it darkens what is behind it (a light tint added a grey veil that
      // washed the black roller out, browser r1); visibility comes from fresnel alpha + env/clearcoat reflections.
      // bin: cool water-clear
      color: new THREE.Color(bin ? 0x4a5257 : 0x1e2226),
      metalness: 0,
      roughness: 0.03,
      transparent: true,
      opacity: bin ? 0.12 : 0.26,
      ior: 1.58,
      specularIntensity: 1,
      clearcoat: 1,
      clearcoatRoughness: 0.02,
      envMapIntensity: bin ? 1.7 : 1.1,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    addFresnelAlpha(m, bin ? 0.6 : 0.8, bin ? 3.0 : 2.5);
    // glass blend: background x (1 - alpha) + full reflected light (normal blending would scale the env/clearcoat
    // highlights by alpha too, which is why the cover vanished). The tint's own lit diffuse is small (dark colour).
    m.blending = THREE.CustomBlending;
    m.blendEquation = THREE.AddEquation;
    m.blendSrc = THREE.OneFactor;
    m.blendDst = THREE.OneMinusSrcAlphaFactor;
    created.push(m);
    return m;
  };

  const fabricFrom = (src: THREE.MeshStandardMaterial, f: { sheen: number; tint: number; rough: number; roughness?: number }) => {
    // always enforce the runtime sheen (the GLB's exported sheen is tuned for Cycles and washes out in three)
    let m = src as THREE.MeshPhysicalMaterial;
    if (!m.isMeshPhysicalMaterial) {
      m = new THREE.MeshPhysicalMaterial();
      THREE.MeshStandardMaterial.prototype.copy.call(m, src);
      created.push(m);
    }
    m.sheen = f.sheen;
    m.sheenColor = new THREE.Color(f.tint);
    m.sheenColorMap = null;
    m.sheenRoughness = f.rough;
    if (f.roughness !== undefined) {
      m.roughness = f.roughness;
      m.roughnessMap = null;
    }
    m.needsUpdate = true;
    return m;
  };

  for (const root of roots) root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
    const next = mats.map((mat) => {
      if (cache.has(mat)) return cache.get(mat)!;
      const std = mat as THREE.MeshStandardMaterial;
      const name = std.name || '';
      let out: THREE.Material = std;
      if (name.startsWith('M_ClearBin')) out = clearFrom(std, 'bin');
      else if (name.startsWith('M_ClearCover')) out = clearFrom(std, 'cover');
      else if (name.startsWith('M_LED')) {
        // authored emissive hue is kept (white headlights, violet accents); runtime drives intensity
        if (std.emissive.getHex() === 0) std.emissive = new THREE.Color(0xf4f8ff);
        std.emissiveIntensity = 0;
        std.toneMapped = true;
        std.userData.ledLevel = 0;
        if (name.startsWith('M_LEDRing')) {
          std.emissive.copy(RING.white);
          std.userData.ledRole = 'ring';
          rings.push(std);
        } else if (name.startsWith('M_LEDAccent')) {
          std.userData.ledRole = 'accent';
          leds.push({ mat: std, gain: 2.6 });
        } else {
          std.userData.ledRole = 'headlight';
          leds.push({ mat: std, gain: 2.4 });
        }
      } else if (name.startsWith('M_DockDisplay')) {
        // icon glyphs come from the decal atlas (emissiveMap + alpha); window body is M_Screen geometry behind it
        if (std.emissive.getHex() === 0) std.emissive = new THREE.Color(0xf4f6ff);
        std.emissiveIntensity = 0;
        std.transparent = true;
        std.depthWrite = false;
        std.alphaTest = 0.02;
        std.polygonOffset = true;
        std.polygonOffsetFactor = -2;
        std.polygonOffsetUnits = -2;
        dockDisplays.push(std);
      } else if (name.startsWith('M_Decal')) {
        // printed ink on plates 0.2-0.3 mm above the surface: no z-fight, no depth write, crisp alpha edge
        std.transparent = true;
        std.depthWrite = false;
        std.alphaTest = 0.02;
        std.polygonOffset = true;
        std.polygonOffsetFactor = -2;
        std.polygonOffsetUnits = -2;
        std.side = THREE.FrontSide;
        std.envMapIntensity = 0.8;
        if (std.map) std.map.anisotropy = 8;
      } else if (std.isMeshStandardMaterial) {
        const fab = prefixLookup(FABRIC, name);
        if (fab) out = fabricFrom(std, fab);
        const s = out as THREE.MeshStandardMaterial;
        s.envMapIntensity = prefixLookup(ENV, name) ?? 1.0;
        if (s.normalMap) s.normalMap.anisotropy = 4;
        if (s.map) s.map.anisotropy = 8;
      }
      cache.set(mat, out);
      return out;
    });
    mesh.material = Array.isArray(mesh.material) ? next : next[0];
    const first = next[0];
    if (first.transparent) {
      mesh.castShadow = false;
      const n = first.name;
      mesh.renderOrder = n.startsWith('M_Decal') || n.startsWith('M_DockDisplay') ? 3 : 2;
    }
  });

  return {
    setLed(k) {
      ledK = k;
      for (const l of leds) {
        l.mat.emissiveIntensity = l.gain * k;
        // read by scene/lookdev/productLights (real light cast by the head LEDs follows this level)
        l.mat.userData.ledLevel = k;
      }
      for (const m of rings) {
        m.emissiveIntensity = ringGain * k;
        m.userData.ledLevel = k;
      }
    },
    setRing(state) {
      ringGain = state === 'white' ? 1.6 : 2.2;
      for (const m of rings) {
        m.emissive.copy(RING[state]);
        m.emissiveIntensity = ringGain * ledK;
      }
    },
    setBinFill(node, k) {
      node.visible = k > 0.01;
      node.scale.y = Math.max(0.001, k);
    },
    setDockBinFull(on) {
      for (const m of dockDisplays) m.emissiveIntensity = on ? 1.8 : 0;
    },
    dispose() {
      for (const m of created) m.dispose();
    },
  };
}
