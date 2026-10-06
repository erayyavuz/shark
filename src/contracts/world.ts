/**
 * World / coordinate contract — owned by the lead. Do not change without updating DECISIONS.md.
 *
 * Units: meters. Runtime is Y-up (three.js / glTF). The floor is the XZ plane at Y = 0.
 * Vacuum-local forward: the floorhead's front edge (front roller, headlights) faces local +Z.
 * Blender authoring is Z-up with forward = Blender -Y; the glTF exporter's +Y-up conversion maps
 * Blender (x, y, z) -> glTF (x, z, -y), so Blender -Y forward becomes glTF +Z forward.
 *
 * Head yaw: rotation about world +Y. yaw = 0 means the head's front faces world -Z
 * (i.e. away from the default camera, which sits on +Z looking toward -Z).
 * Implementation: VacuumRoot.rotation.y = yaw + Math.PI so local +Z maps to world -Z when yaw = 0.
 */

export interface Vec2 {
  x: number;
  z: number;
}

/** Playable rectangle on the floor (world XZ). The decorative floor plane is larger. */
export interface PlayArea {
  minX: number;
  maxX: number;
  minZ: number;
  maxZ: number;
}

export const PLAY_AREA: PlayArea = { minX: -0.7, maxX: 0.7, minZ: -0.5, maxZ: 0.5 };

export const playWidth = (a: PlayArea = PLAY_AREA) => a.maxX - a.minX;
export const playDepth = (a: PlayArea = PLAY_AREA) => a.maxZ - a.minZ;

/** World XZ -> normalized field coordinates u,v in [0,1]. u grows with +X, v grows with +Z. */
export function worldToField(p: Vec2, a: PlayArea = PLAY_AREA): { u: number; v: number } {
  return { u: (p.x - a.minX) / (a.maxX - a.minX), v: (p.z - a.minZ) / (a.maxZ - a.minZ) };
}

export function fieldToWorld(u: number, v: number, a: PlayArea = PLAY_AREA): Vec2 {
  return { x: a.minX + u * (a.maxX - a.minX), z: a.minZ + v * (a.maxZ - a.minZ) };
}

export function clampToArea(p: Vec2, margin = 0, a: PlayArea = PLAY_AREA): Vec2 {
  return {
    x: Math.min(a.maxX - margin, Math.max(a.minX + margin, p.x)),
    z: Math.min(a.maxZ - margin, Math.max(a.minZ + margin, p.z)),
  };
}

/** Head-local -> world on the floor. Local +Z = head front. */
export function headLocalToWorld(pose: HeadPose, lx: number, lz: number): Vec2 {
  // forward(world) = (sin(yaw+π), cos(yaw+π)) = (−sin yaw, −cos yaw).
  const c = Math.cos(pose.yaw + Math.PI);
  const s = Math.sin(pose.yaw + Math.PI);
  // three.js rotation about Y by angle t maps local (x, z) -> (x·cos t + z·sin t, −x·sin t + z·cos t)
  return { x: pose.x + lx * c + lz * s, z: pose.z - lx * s + lz * c };
}

/** World -> head-local (inverse of headLocalToWorld). */
export function worldToHeadLocal(pose: HeadPose, wx: number, wz: number): { lx: number; lz: number } {
  const dx = wx - pose.x;
  const dz = wz - pose.z;
  const c = Math.cos(pose.yaw + Math.PI);
  const s = Math.sin(pose.yaw + Math.PI);
  return { lx: dx * c - dz * s, lz: dx * s + dz * c };
}

/** The actual, simulated floorhead pose (never the raw cursor). x,z is the VacuumRoot floor origin. */
export interface HeadPose {
  x: number;
  z: number;
  yaw: number;
}

/** Where input wants the head to go; fed into the damped motion controller. */
export interface InputTarget {
  x: number;
  z: number;
  active: boolean;
}
