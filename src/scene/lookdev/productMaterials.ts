import * as THREE from 'three';

export type RingState = 'white' | 'purple' | 'lightPurple';

export interface ProductMaterialSet {
  /** 0..1 power-on level: Reveal head light, light pipe and the handheld UI ring/bar. */
  setLed(k: number): void;
  /** Handheld UI LED ring colour (owner's guide: white = normal, deep purple = heavy debris, light purple = clearing). */
  setRing(state: RingState): void;
  setBinFill(node: THREE.Object3D, k: number): void;
  dispose(): void;
}

/**
 * Per-material runtime tuning for the v2 GLB (IA3246GN Sagewood), keyed by material name prefix
 * (scripts/blender/v2/materials.py is the source of truth for colours).
 *
 * glTF sets roughnessFactor = 1 when a metallicRoughness map is present; the shared ORM textures carry an absolute
 * mean roughness (plastic 0.46, brushed metal 0.30), so `rough` here is the factor that restores each finish's
 * authored roughness (three multiplies factor x map.g).
 */
const TUNING: Record<string, { rough?: number; env?: number }> = {
  M_SageDeep: { rough: 0.5 / 0.46, env: 0.9 },
  M_Sage: { rough: 1.0, env: 0.9 },
  M_Graphite: { rough: 0.42 / 0.46, env: 1.0 },
  M_Rubber: { rough: 0.85 / 0.46, env: 0.6 },
  M_CopperSatin: { rough: 0.36 / 0.3, env: 1.5 },
  M_CopperBrush: { env: 1.1 },
  M_Copper: { rough: 0.32 / 0.3, env: 1.6 },
  M_SilverBrush: { rough: 0.32 / 0.3, env: 1.6 },
  M_PlateGrey: { rough: 0.36 / 0.3, env: 1.4 },
  M_Chrome: { env: 1.8 },
  M_Screen: { env: 1.4 },
  M_Bristle: { env: 0.5 },
  M_Hose: { env: 0.8 },
};

const RING: Record<RingState, THREE.Color> = {
  white: new THREE.Color(0xf2f4ff),
  purple: new THREE.Color(0x5a22e0),
  lightPurple: new THREE.Color(0xb59cff),
};

function tuningFor(name: string) {
  // longest prefix wins (M_CopperSatin before M_Copper, M_SageDeep before M_Sage)
  let best: string | undefined;
  for (const k of Object.keys(TUNING)) if (name.startsWith(k) && (!best || k.length > best.length)) best = k;
  return best ? TUNING[best] : undefined;
}

export function applyProductMaterials(roots: THREE.Object3D[]): ProductMaterialSet {
  const leds: { mat: THREE.MeshStandardMaterial; gain: number }[] = [];
  const rings: THREE.MeshStandardMaterial[] = [];
  const created: THREE.Material[] = [];
  const cache = new Map<THREE.Material, THREE.Material>();
  let ledK = 0;
  let ringGain = 1.6;

  /**
   * Thin clear plastics without a transmission pass: a mostly transparent physical surface whose own (lit) colour
   * acts as the tint, plus clearcoat-grade reflections from the room env. Drawn double-sided, so the effective
   * see-through factor is (1 - opacity)^2.
   */
  const clearFrom = (src: THREE.MeshStandardMaterial, kind: 'bin' | 'smoke') => {
    const bin = kind === 'bin';
    const m = new THREE.MeshPhysicalMaterial({
      name: src.name,
      // bin: faint cool frost; smoke: dark neutral grey film (Cycles tint #d6d7d8 per face ~ 0.8 transmittance)
      color: new THREE.Color(bin ? 0xeef3f5 : 0x2b2d2f),
      metalness: 0,
      roughness: bin ? 0.04 : 0.06,
      transparent: true,
      opacity: bin ? 0.09 : 0.2,
      ior: 1.49,
      specularIntensity: 1,
      clearcoat: 1,
      clearcoatRoughness: 0.03,
      envMapIntensity: 1.35,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    created.push(m);
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
      else if (name.startsWith('M_ClearSmoke')) out = clearFrom(std, 'smoke');
      else if (name.startsWith('M_LED')) {
        // authored emissive hue is kept (blue-white Reveal lens, blue light pipe, white ring); runtime drives intensity
        if (std.emissive.getHex() === 0) std.emissive = new THREE.Color(0xf4f8ff);
        std.emissiveIntensity = 0;
        std.toneMapped = true;
        if (name.startsWith('M_LEDRing')) {
          std.emissive.copy(RING.white);
          rings.push(std);
        }
        else leds.push({ mat: std, gain: name.startsWith('M_LEDAccent') ? 2.6 : 2.4 });
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
        const t = tuningFor(name);
        if (t?.rough !== undefined && std.roughnessMap) std.roughness = t.rough;
        std.envMapIntensity = t?.env ?? 1.0;
        if (std.normalMap) std.normalMap.anisotropy = 4;
      }
      cache.set(mat, out);
      return out;
    });
    mesh.material = Array.isArray(mesh.material) ? next : next[0];
    const first = next[0];
    if (first.transparent) {
      mesh.castShadow = false;
      mesh.renderOrder = (first as THREE.Material).name.startsWith('M_Decal') ? 3 : 2;
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
      for (const m of rings) m.emissiveIntensity = ringGain * k;
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
    dispose() {
      for (const m of created) m.dispose();
    },
  };
}
