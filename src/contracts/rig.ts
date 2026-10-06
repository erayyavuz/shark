/**
 * Rig contract — node names in public/models/powerdetect-*.glb. Units meters, Y-up, local +Z = head front.
 * Hierarchy (locked):
 *
 * VacuumRoot                      origin on the floor (y=0) at the center of the floorhead's intake footprint
 *                                 (midway between the roller contact lines, centered in X). NeckPivot sits behind it at local −Z.
 *  └ FloorHead                    floor-contact assembly; never tilts with the wand
 *     ├ RollerFront               rotates about its local X axis (soft DuoClean front roller)
 *     ├ RollerRear                rotates about its local X axis (bristle brushroll, underneath)
 *     ├ HeadLights                emissive LED meshes at the front corners (verified in V5)
 *     ├ IntakeFront / IntakeRear  empties at roller centers on the floor plane (y≈0)
 *     ├ FloorContactAnchors       empty; children Contact_* are points that must sit at y≈0
 *     └ NeckPivot                 at the neck joint axis. Leaning the wand back (toward local −Z, away from the head front)
 *        │                        is rotation.x = −pitch (three.js right-hand rule). rotation.z = sideways lean. Rest: wand vertical.
 *        └ LowerWand              neck connector + purple wand
 *           └ FlexPivot           MultiFlex fold joint at top of the purple wand; rotation.x folds (rest 0)
 *              └ UpperWand        short grey section between fold joint and bin
 *                 └ MotorAssembly bin + cyclone + motor + filter cap + handle + battery
 *                    ├ DustbinShell     transparent bin shell (separate material)
 *                    ├ DustbinContents  optional fill visualization (scale.y drives fill, rest hidden-ish)
 *                    └ PowerControlAnchor empty: reference point for the hero Start UI projection
 */
export const RIG_NODES = [
  'VacuumRoot',
  'FloorHead',
  'NeckPivot',
  'LowerWand',
  'FlexPivot',
  'UpperWand',
  'MotorAssembly',
  'DustbinShell',
  'DustbinContents',
  'RollerFront',
  'RollerRear',
  'HeadLights',
  'PowerControlAnchor',
  'IntakeFront',
  'IntakeRear',
  'FloorContactAnchors',
] as const;

export type RigNodeName = (typeof RIG_NODES)[number];

/** Pickup/contact geometry in FloorHead-local meters (measured from the finished mesh; see assets/manifest.json). */
export interface NozzleGeometry {
  /** Usable intake width across X (inside the side caps). */
  intakeWidth: number;
  /** Local Z range of the intake/contact footprint under the head [rear, front]. */
  intakeZMin: number;
  intakeZMax: number;
  /** Outer shell footprint for occlusion/no-pass checks. */
  shellWidth: number;
  shellZMin: number;
  shellZMax: number;
}
