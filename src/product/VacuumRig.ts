import * as THREE from 'three';
import { RIG_NODES, type NozzleGeometry, type RigNodeName } from '../contracts/rig';
import { DEFAULT_NOZZLE } from '../config/product';
import { applyProductMaterials, type ProductMaterialSet, type RingState } from '../scene/lookdev/productMaterialsV3';

export interface RigMeta {
  nozzle: NozzleGeometry;
  rollerFrontRadius: number;
  rollerRearRadius: number;
}

export interface RigPose {
  x: number;
  z: number;
  yaw: number;
  /** wand lean back from vertical (rad) */
  pitch: number;
  /** sideways lean (rad) */
  roll: number;
  /** MultiFlex fold (rad), 0 = straight */
  fold: number;
  /** docked nose-down tilt (rad) about the front roller contact line: the rear wheels stand on the dock base plate */
  dockTilt?: number;
}

/**
 * Runtime adapter over the GLB rig. Normalization happens once here; per-frame calls only set
 * transforms on cached nodes.
 */
export class VacuumRig {
  readonly root: THREE.Object3D;
  readonly nodes: Record<RigNodeName, THREE.Object3D>;
  readonly meta: RigMeta;
  readonly isProxy: boolean;
  /** Clean & Empty base (optional `DockRoot` node); static, owned by the scene, never posed. */
  readonly dock: THREE.Object3D | null;
  private materials: ProductMaterialSet;
  private spinFront = 0;
  private spinRear = 0;
  private tmp = new THREE.Vector3();

  constructor(scene: THREE.Object3D, meta: Partial<RigMeta> | null, isProxy = false) {
    this.isProxy = isProxy;
    const found = {} as Record<RigNodeName, THREE.Object3D>;
    const missing: string[] = [];
    for (const name of RIG_NODES) {
      const n = scene.getObjectByName(name);
      if (n) found[name] = n;
      else missing.push(name);
    }
    if (missing.length) throw new Error(`Product rig is missing nodes: ${missing.join(', ')}`);
    this.nodes = found;
    this.root = found.VacuumRoot;
    this.meta = {
      nozzle: meta?.nozzle ?? DEFAULT_NOZZLE,
      rollerFrontRadius: meta?.rollerFrontRadius ?? 0.026,
      rollerRearRadius: meta?.rollerRearRadius ?? 0.02,
    };
    this.root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.castShadow = true;
        m.receiveShadow = true;
      }
    });
    this.dock = scene.getObjectByName('DockRoot') ?? null;
    if (this.dock) {
      this.dock.removeFromParent();
      this.dock.traverse((o) => {
        const m = o as THREE.Mesh;
        if (m.isMesh) {
          m.castShadow = true;
          m.receiveShadow = true;
        }
      });
    }
    this.materials = applyProductMaterials(this.dock ? [this.root, this.dock] : [this.root]);
    // detach from any glTF scene wrapper transforms so VacuumRoot is the world transform owner
    if (this.root.parent) this.root.removeFromParent();
    this.root.matrixAutoUpdate = true;
  }

  applyPose(p: RigPose) {
    const t = p.dockTilt ?? 0;
    const yaw = p.yaw + Math.PI;
    this.root.rotation.set(t, yaw, 0, 'YXZ');
    if (t === 0) {
      this.root.position.set(p.x, 0, p.z);
    } else {
      // keep the front contact line (head-local z = zc on the floor) fixed while the rear lifts
      const zc = this.meta.nozzle.intakeZMax;
      const oy = zc * Math.sin(t);
      const oz = zc * (1 - Math.cos(t));
      this.root.position.set(p.x + Math.sin(yaw) * oz, oy, p.z + Math.cos(yaw) * oz);
    }
    const neck = this.nodes.NeckPivot;
    // the dock tilt belongs to the floorhead only: the neck compensates so the wand stays upright in the cradle
    neck.rotation.set(-p.pitch - t, 0, p.roll, 'YXZ');
    this.nodes.FlexPivot.rotation.x = p.fold;
  }

  /** speed in m/s of floor travel + idle spin; rollers rotate about local X. */
  spinRollers(dt: number, rpmFactor: number) {
    // front soft roller and rear brushroll turn in opposite senses at idle speed scaled by power
    const w = rpmFactor * 26; // rad/s, visual not measured
    this.spinFront += w * dt;
    this.spinRear -= w * 1.15 * dt;
    this.nodes.RollerFront.rotation.x = this.spinFront;
    this.nodes.RollerRear.rotation.x = this.spinRear;
  }

  setPower(k: number) {
    this.materials.setLed(k);
  }

  /** Handheld UI LED ring: white normal, purple heavy dirt, light purple clearing (owner's guide p.7). */
  setRing(state: RingState) {
    this.materials.setRing(state);
  }

  setBinFill(k: number) {
    this.materials.setBinFill(this.nodes.DustbinContents, k);
  }

  anchorWorld(name: RigNodeName, out: THREE.Vector3) {
    this.root.updateWorldMatrix(true, true);
    return this.nodes[name].getWorldPosition(out);
  }

  /** World-space center of the motor assembly (used for inspection framing). */
  productCenter(out: THREE.Vector3) {
    const box = new THREE.Box3().setFromObject(this.root);
    return box.getCenter(out);
  }

  get tmpVec() {
    return this.tmp;
  }

  dispose() {
    for (const r of this.dock ? [this.root, this.dock] : [this.root]) r.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        m.geometry.dispose();
        const mats = Array.isArray(m.material) ? m.material : [m.material];
        for (const mat of mats) {
          for (const v of Object.values(mat)) if (v instanceof THREE.Texture) v.dispose();
          mat.dispose();
        }
      }
    });
    this.materials.dispose();
  }
}
