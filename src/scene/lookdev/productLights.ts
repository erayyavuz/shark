import * as THREE from 'three';

/**
 * Real light cast by the floorhead LEDs (the product's "dirt reveal" lighting).
 *
 * IP3251 (DuoClean Detect): WHITE headlights at the front corners and VIOLET LEDs at the rear corners beside the
 * wheels (+ a thin violet strip behind the roller window). The GLB exports anchors `LightFrontL/R` and `LightRearL/R`
 * under `FloorHead`; each gets a low SpotLight whose colour comes from the LED material with the matching
 * `userData.ledRole` ('headlight' | 'accent'), set by productMaterialsV3. Older models without anchors fall back to
 * left/right clustering of the `HeadLights` meshes (front spots only).
 *
 * The light count is fixed for the lifetime of the scene (lights sit at intensity 0 without a rig) so swapping the
 * product model never triggers a program recompile. Power follows the LED materials' `userData.ledLevel`.
 */
interface Anchor {
  pos: THREE.Object3D;
  tgt: THREE.Object3D;
  /** owned helper objects we created (removed on release); GLB anchors are not owned */
  owned: boolean;
  role: 'headlight' | 'accent';
}

// Photometric: the LEDs sit a few cm above the floor, so illuminance falls off very steeply (E = I cosθ / d²).
const FRONT_CD = 0.05;
const REAR_CD = 0.04;
const WASH_CD = 0.035;
const WHITE = new THREE.Color(0xeef4ff);
const VIOLET = new THREE.Color(0x7a4cff);

export class ProductLights {
  readonly group = new THREE.Group();
  private spots: THREE.SpotLight[] = [];
  private wash: THREE.SpotLight;
  private head: THREE.Object3D | null = null;
  private ledMats: THREE.MeshStandardMaterial[] = [];
  private anchors: Anchor[] = [];
  private washAnchor: Anchor | null = null;
  private v = new THREE.Vector3();
  private cFront = new THREE.Color();
  private cRear = new THREE.Color();
  /** 0 day … 1 night: spots stay physically the same; this only feeds glow/emissive boost at night */
  night = 0;

  constructor(private scene: THREE.Scene, highTier: boolean) {
    for (let i = 0; i < 4; i++) {
      const s = new THREE.SpotLight(0xffffff, 0, 0.4, THREE.MathUtils.degToRad(76), 1, 2);
      s.castShadow = false;
      this.spots.push(s);
      this.group.add(s, s.target);
    }
    this.wash = new THREE.SpotLight(0xffffff, 0, 0.8, THREE.MathUtils.degToRad(50), 1, 2);
    // high tier: the centre wash casts a short shadow so crumbs and hair throw low raking shadows (the reveal effect)
    if (highTier) {
      this.wash.castShadow = true;
      this.wash.shadow.mapSize.set(512, 512);
      this.wash.shadow.camera.near = 0.01;
      this.wash.shadow.camera.far = 1.0;
      this.wash.shadow.bias = -0.0008;
      this.wash.shadow.normalBias = 0.002;
      this.wash.shadow.radius = 2;
    }
    this.group.add(this.wash, this.wash.target);
    this.group.name = 'ProductLights';
    scene.add(this.group);
  }

  private isAttached(o: THREE.Object3D) {
    let p: THREE.Object3D | null = o;
    while (p) {
      if (p === this.scene) return true;
      p = p.parent;
    }
    return false;
  }

  private bind(head: THREE.Object3D) {
    this.release();
    this.head = head;
    const floorHead = head.parent ?? head;
    floorHead.updateWorldMatrix(true, true);
    const mats = new Set<THREE.MeshStandardMaterial>();
    head.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      for (const mat of Array.isArray(m.material) ? m.material : [m.material]) {
        if ((mat as THREE.MeshStandardMaterial).isMeshStandardMaterial) mats.add(mat as THREE.MeshStandardMaterial);
      }
    });
    this.ledMats = [...mats];

    const mk = (parent: THREE.Object3D, p: THREE.Vector3, t: THREE.Vector3, role: Anchor['role']): Anchor => {
      const pos = new THREE.Object3D();
      const tgt = new THREE.Object3D();
      pos.name = 'LedLightAnchor';
      tgt.name = 'LedLightTarget';
      pos.position.copy(p);
      tgt.position.copy(t);
      parent.add(pos, tgt);
      return { pos, tgt, owned: true, role };
    };

    // v3 GLBs: explicit light anchors on the floorhead (FloorHead-local, +Z = front)
    const named: [string, Anchor['role'], number, number][] = [
      ['LightFrontL', 'headlight', -1, 1],
      ['LightFrontR', 'headlight', 1, 1],
      ['LightRearL', 'accent', -1, -1],
      ['LightRearR', 'accent', 1, -1],
    ];
    let found = 0;
    for (const [name, role, out, dir] of named) {
      const a = floorHead.getObjectByName(name);
      if (!a) continue;
      found++;
      const p = a.position.clone();
      // front: forward and slightly outward; rear: down and outward around the wheels
      const t = dir > 0 ? new THREE.Vector3(p.x + out * 0.06, 0, p.z + 0.12) : new THREE.Vector3(p.x + out * 0.07, 0, p.z - 0.03);
      this.anchors.push(mk(floorHead, p.clone().setY(Math.max(0.012, p.y)), t, role));
    }

    let maxZ = -Infinity;
    let minY = Infinity;
    if (!found) {
      // legacy models: cluster the HeadLights meshes into left/right front spots
      const inv = new THREE.Matrix4().copy(floorHead.matrixWorld).invert();
      const sums = [new THREE.Vector3(), new THREE.Vector3()];
      const counts = [0, 0];
      head.traverse((o) => {
        const m = o as THREE.Mesh;
        if (!m.isMesh) return;
        const pos = m.geometry.getAttribute('position');
        const toLocal = new THREE.Matrix4().multiplyMatrices(inv, m.matrixWorld);
        const step = Math.max(1, Math.floor(pos.count / 400));
        for (let i = 0; i < pos.count; i += step) {
          this.v.fromBufferAttribute(pos, i).applyMatrix4(toLocal);
          const side = this.v.x < 0 ? 0 : 1;
          sums[side].add(this.v);
          counts[side]++;
          minY = Math.min(minY, this.v.y);
          maxZ = Math.max(maxZ, this.v.z);
        }
      });
      const lift = Math.max(0.026, (Number.isFinite(minY) ? minY : 0) + 0.01);
      for (let s = 0; s < 2; s++) {
        if (!counts[s]) continue;
        const c = sums[s].divideScalar(counts[s]);
        const out = s === 0 ? -1 : 1;
        this.anchors.push(mk(floorHead, new THREE.Vector3(c.x, lift, c.z - 0.008), new THREE.Vector3(c.x + out * 0.07, 0, c.z + 0.09), 'headlight'));
      }
    } else {
      for (const a of this.anchors) if (a.role === 'headlight') maxZ = Math.max(maxZ, a.pos.position.z);
    }
    const zf = Number.isFinite(maxZ) ? maxZ : 0.05;
    // just ahead of the shell lip so its raking shadow never clips the head itself
    this.washAnchor = mk(floorHead, new THREE.Vector3(0, 0.04, zf + 0.004), new THREE.Vector3(0, 0, zf + 0.3), 'headlight');
  }

  private release() {
    for (const a of this.anchors) if (a.owned) a.pos.parent?.remove(a.pos, a.tgt);
    if (this.washAnchor) this.washAnchor.pos.parent?.remove(this.washAnchor.pos, this.washAnchor.tgt);
    this.anchors = [];
    this.washAnchor = null;
    this.head = null;
    this.ledMats = [];
  }

  /** emissive hue (unit max channel) of the LED materials with a role, falling back to all LEDs / a default */
  private roleColor(role: 'headlight' | 'accent', out: THREE.Color, fallback: THREE.Color) {
    out.setRGB(0, 0, 0);
    let any = false;
    for (const m of this.ledMats) {
      const r = m.userData.ledRole as string | undefined;
      if (r && r !== role) continue;
      if (!r && role === 'accent') continue;
      out.add(m.emissive);
      any = true;
    }
    if (!any || out.r + out.g + out.b < 1e-4) out.copy(fallback);
    return out.multiplyScalar(1 / Math.max(out.r, out.g, out.b, 1e-4));
  }

  /** Re-binds to the current product automatically (model swaps, proxy rig). */
  update() {
    if (!this.head || !this.isAttached(this.head)) {
      const h = this.scene.getObjectByName('HeadLights');
      if (h && h !== this.head) this.bind(h);
      else if (!h && this.head) this.release();
    }
    let level = 0;
    for (const m of this.ledMats) level = Math.max(level, (m.userData.ledLevel as number | undefined) ?? 0);
    const front = this.roleColor('headlight', this.cFront, WHITE);
    const rear = this.roleColor('accent', this.cRear, VIOLET);

    for (let i = 0; i < this.spots.length; i++) {
      const s = this.spots[i];
      const a = this.anchors[i];
      if (!a || level <= 0.001) {
        s.intensity = 0;
        continue;
      }
      const head = a.role === 'headlight';
      s.color.copy(head ? front : rear);
      s.intensity = (head ? FRONT_CD : REAR_CD) * level;
      s.angle = THREE.MathUtils.degToRad(head ? 76 : 80);
      s.distance = head ? 0.4 : 0.28;
      a.pos.getWorldPosition(s.position);
      a.tgt.getWorldPosition(s.target.position);
      s.target.updateMatrixWorld();
    }
    const w = this.washAnchor;
    if (w && level > 0.001) {
      this.wash.color.copy(front).lerp(new THREE.Color(1, 1, 1), 0.35);
      this.wash.intensity = WASH_CD * level;
      w.pos.getWorldPosition(this.wash.position);
      w.tgt.getWorldPosition(this.wash.target.position);
      this.wash.target.updateMatrixWorld();
    } else this.wash.intensity = 0;
    return level;
  }

  dispose() {
    this.release();
    this.wash.shadow.map?.dispose();
    this.scene.remove(this.group);
  }
}
