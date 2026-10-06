import * as THREE from 'three';
import { ACTIVE, DOCK, HERO } from '../config/tuning';
import type { PlayArea } from '../contracts/world';
import { PRODUCT } from '../config/product';

export interface CamPose {
  pos: THREE.Vector3;
  target: THREE.Vector3;
  fov: number;
}

export interface ViewInsets {
  /** CSS pixels reserved at the top and bottom of the viewport */
  top: number;
  bottom: number;
}

export const clonePose = (p: CamPose): CamPose => ({ pos: p.pos.clone(), target: p.target.clone(), fov: p.fov });

/**
 * Computes framing for hero / active / inspect, owns the live camera pose and interpolation.
 * Product world scale never changes; only position, orientation and FOV move.
 */
export class CameraDirector {
  readonly current: CamPose = { pos: new THREE.Vector3(0, 0.6, 3), target: new THREE.Vector3(0, 0.55, 0), fov: HERO.fov };
  private probe = new THREE.PerspectiveCamera();
  private v = new THREE.Vector3();

  constructor(private camera: THREE.PerspectiveCamera) {}

  apply() {
    this.camera.position.copy(this.current.pos);
    if (Math.abs(this.camera.fov - this.current.fov) > 1e-4) {
      this.camera.fov = this.current.fov;
      this.camera.updateProjectionMatrix();
    }
    this.camera.lookAt(this.current.target);
  }

  set(p: CamPose) {
    this.current.pos.copy(p.pos);
    this.current.target.copy(p.target);
    this.current.fov = p.fov;
    this.apply();
  }

  lerp(a: CamPose, b: CamPose, k: number) {
    // interpolate around the target (spherical-ish) so the move arcs instead of cutting through the floor
    const ta = this.v.copy(a.target);
    this.current.target.lerpVectors(ta, b.target, k);
    const oa = a.pos.clone().sub(a.target);
    const ob = b.pos.clone().sub(b.target);
    const sa = new THREE.Spherical().setFromVector3(oa);
    const sb = new THREE.Spherical().setFromVector3(ob);
    let dth = sb.theta - sa.theta;
    while (dth > Math.PI) dth -= Math.PI * 2;
    while (dth < -Math.PI) dth += Math.PI * 2;
    const s = new THREE.Spherical(
      sa.radius + (sb.radius - sa.radius) * k,
      sa.phi + (sb.phi - sa.phi) * k,
      sa.theta + dth * k,
    );
    this.current.pos.setFromSpherical(s).add(this.current.target);
    this.current.fov = a.fov + (b.fov - a.fov) * k;
    this.apply();
  }

  /** Hero: whole product upright at ~78% of usable height, offset left on wide screens for the Start control. */
  heroPose(aspect: number, viewportH: number, insets: ViewInsets): CamPose {
    const usable = Math.max(0.5, (viewportH - insets.top - insets.bottom) / viewportH);
    const fov = HERO.fov;
    const h = PRODUCT.overallHeight / (HERO.heightFraction * usable);
    let d = h / (2 * Math.tan(THREE.MathUtils.degToRad(fov / 2)));
    // narrow screens: make sure product + Start control fit horizontally (~0.78 m)
    const hfov = 2 * Math.atan(Math.tan(THREE.MathUtils.degToRad(fov / 2)) * aspect);
    // must fit: the product + Start control, and on the hero stage the podium (Ø ~0.9 m at the dock) with a margin
    const needW = aspect < 0.8 ? 1.06 : 0.8;
    d = Math.max(d, needW / (2 * Math.tan(hfov / 2)));
    const shift = aspect > 1 ? HERO.lateralShift + Math.min(0.12, (aspect - 1) * 0.08) : 0.11;
    // vertical centering within the usable band
    const centerOffset = ((insets.bottom - insets.top) / viewportH) * h * 0.5;
    const target = new THREE.Vector3(DOCK.x + shift, HERO.lookAtHeight - centerOffset, DOCK.z);
    const pos = new THREE.Vector3(DOCK.x + shift, HERO.cameraHeight - centerOffset, DOCK.z + d);
    return { pos, target, fov };
  }

  /**
   * Active: elevated view over the play area; distance solved so the reachable rectangle fits
   * inside the viewport minus UI insets.
   */
  activePose(area: PlayArea, aspect: number, viewportH: number, insets: ViewInsets): CamPose {
    const fov = aspect < 0.8 ? ACTIVE.fov + 6 : ACTIVE.fov;
    const el = aspect < 0.8 ? ACTIVE.elevation + 0.12 : ACTIVE.elevation;
    const cam = this.probe;
    cam.fov = fov;
    cam.aspect = aspect;
    cam.near = 0.05;
    cam.far = 50;
    cam.updateProjectionMatrix();
    const yTop = 1 - (2 * (insets.top + 8)) / viewportH;
    const yBot = -1 + (2 * (insets.bottom + 8)) / viewportH;
    const cx = (area.minX + area.maxX) / 2;
    let tz = (area.minZ + area.maxZ) / 2;
    const corners = [
      new THREE.Vector3(area.minX, 0, area.minZ),
      new THREE.Vector3(area.maxX, 0, area.minZ),
      new THREE.Vector3(area.minX, 0, area.maxZ),
      new THREE.Vector3(area.maxX, 0, area.maxZ),
    ];
    const dir = new THREE.Vector3(Math.sin(ACTIVE.azimuth) * Math.cos(el), Math.sin(el), Math.cos(ACTIVE.azimuth) * Math.cos(el));
    const fits = (d: number, z: number) => {
      const target = new THREE.Vector3(cx, 0, z);
      cam.position.copy(target).addScaledVector(dir, d);
      cam.lookAt(target);
      cam.updateMatrixWorld();
      let minY = 9, maxY = -9, maxX = 0;
      for (const c of corners) {
        const p = this.v.copy(c).project(cam);
        minY = Math.min(minY, p.y);
        maxY = Math.max(maxY, p.y);
        maxX = Math.max(maxX, Math.abs(p.x));
      }
      return { minY, maxY, maxX };
    };
    let hi = 8;
    const want = (yTop + yBot) / 2;
    for (let it = 0; it < 4; it++) {
      let lo = 0.6;
      hi = 8;
      for (let i = 0; i < 30; i++) {
        const mid = (lo + hi) / 2;
        const r = fits(mid, tz);
        if (r.maxX <= 0.95 && r.maxY - r.minY <= yTop - yBot) hi = mid;
        else lo = mid;
      }
      // re-center vertically inside [yBot, yTop]: moving the target toward −Z lowers the area on screen
      let a = tz - 1.5, b = tz + 1.5;
      for (let i = 0; i < 30; i++) {
        const m = (a + b) / 2;
        const r = fits(hi, m);
        if ((r.maxY + r.minY) / 2 > want) b = m;
        else a = m;
      }
      tz = (a + b) / 2;
    }
    const target = new THREE.Vector3(cx, 0, tz);
    const pos = target.clone().addScaledVector(dir, hi);
    return { pos, target, fov };
  }

  /** Inspect: frame the full (upright) product around a floor point, with orbit angles. */
  inspectPose(base: THREE.Vector3, theta: number, phi: number, radius: number, focusHeight = 0.58): CamPose {
    const target = new THREE.Vector3(base.x, focusHeight, base.z);
    const pos = new THREE.Vector3().setFromSpherical(new THREE.Spherical(radius, phi, theta)).add(target);
    return { pos, target, fov: 30 };
  }
}
