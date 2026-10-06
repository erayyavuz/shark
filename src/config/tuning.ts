/** Art-direction + motion tuning. All magic numbers for camera/motion live here. */
export const PALETTE = {
  studio: '#EAE9E6',
  text: '#242526',
  muted: '#696B6D',
  accent: '#9A6142',
} as const;

/** Home position of the Clean & Empty dock (world floor coords). The vacuum rests docked here in the hero view;
 * the play area lies in front of it (toward the viewer). */
export const DOCK = { x: 0, z: -0.66 };

export const HERO = {
  /** Yaw for the hero presentation: front faces the camera (+Z) turned slightly for depth. */
  yaw: Math.PI - 0.42,
  /** Fraction of usable viewport height the product should occupy. */
  heightFraction: 0.78,
  fov: 26,
  /** Camera elevation (m) relative to product center and small downward look. */
  cameraHeight: 0.66,
  lookAtHeight: 0.575,
  /** Horizontal camera offset (m) so the product sits left of center leaving room for Start on the right. */
  lateralShift: 0.07,
};

export const ACTIVE = {
  /** Resting yaw in active play: head front angled toward the viewer, wand trailing back-right. */
  yaw: Math.PI + 0.55,
  yawRange: 1.05,
  pitch: 0.92,
  fov: 36,
  /** Downward viewing angle (radians from horizontal). */
  elevation: 0.98,
  azimuth: 0.0,
};

export const MOTION = {
  stiffness: 70,
  damping: 15,
  maxAccel: 9,
  maxSpeed: 1.5,
  /** yaw follow rate per m/s of speed */
  steer: 5.5,
  maxYawRate: 3.2,
  /** pointer within this distance (m) of the intake center grabs the head with a preserved offset */
  grabRadius: 0.16,
  /** time constant (s) for gliding the head under a pointer that started elsewhere */
  offsetDecay: 0.3,
  touchOffsetPx: 56,
  keyboardSpeed: 0.55,
  fixedStep: 1 / 120,
  maxCatchUpSteps: 8,
};

export const INTRO = {
  total: 3.4,
  power: [0, 0.35],
  incline: [0.3, 1.6],
  camera: [0.15, 2.35],
  floor: [0.55, 1.9],
  patchAt: 1.25,
  /** distance (m) from the dock along the head front where the intro patch is centred */
  patchDistance: 0.52,
  demo: [1.9, 3.15],
  controls: 3.05,
};

export const RETURN = { total: 1.8 };
