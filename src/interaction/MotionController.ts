import type { HeadPose, InputTarget } from '../contracts/world';
import { ACTIVE, MOTION } from '../config/tuning';

const wrap = (a: number) => {
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
};

/**
 * Damped, speed/acceleration-limited floorhead motion. Input only sets a target;
 * cleaning is evaluated along the pose this controller produces.
 *
 * Steering behaves like a caster: yaw turns toward the travel direction at a rate proportional
 * to speed. Reverse strokes (moving against the head front) steer toward −velocity, so the
 * appliance never spins 180°. Yaw is constrained around ACTIVE.yaw so the wand stays away from the viewer.
 */
export class MotionController {
  pose: HeadPose = { x: 0, z: 0, yaw: ACTIVE.yaw };
  prev: HeadPose = { x: 0, z: 0, yaw: ACTIVE.yaw };
  vx = 0;
  vz = 0;
  /** smoothed signed forward speed (m/s, + = toward head front) and lateral accel, for wand dynamics */
  forwardSpeed = 0;
  lateral = 0;
  target: InputTarget = { x: 0, z: 0, active: false };
  yawCenter = ACTIVE.yaw;
  yawRange = ACTIVE.yawRange;
  steeringEnabled = true;
  private acc = 0;

  reset(x: number, z: number, yaw: number) {
    this.pose = { x, z, yaw };
    this.prev = { ...this.pose };
    this.vx = this.vz = 0;
    this.forwardSpeed = 0;
    this.lateral = 0;
    this.target = { x, z, active: false };
    this.acc = 0;
  }

  get speed() {
    return Math.hypot(this.vx, this.vz);
  }

  /**
   * Advance with fixed steps. `onStep(prev, next)` runs per fixed step so the simulation sees
   * the exact swept path. Returns the number of steps taken.
   */
  update(dt: number, onStep?: (prev: HeadPose, next: HeadPose, h: number) => void): number {
    const h = MOTION.fixedStep;
    this.acc = Math.min(this.acc + dt, h * MOTION.maxCatchUpSteps);
    let n = 0;
    while (this.acc >= h) {
      this.acc -= h;
      this.prev.x = this.pose.x;
      this.prev.z = this.pose.z;
      this.prev.yaw = this.pose.yaw;
      this.stepOnce(h);
      onStep?.(this.prev, this.pose, h);
      n++;
    }
    return n;
  }

  private stepOnce(h: number) {
    const dx = this.target.x - this.pose.x;
    const dz = this.target.z - this.pose.z;
    let ax = MOTION.stiffness * dx - MOTION.damping * this.vx;
    let az = MOTION.stiffness * dz - MOTION.damping * this.vz;
    const am = Math.hypot(ax, az);
    if (am > MOTION.maxAccel) {
      ax *= MOTION.maxAccel / am;
      az *= MOTION.maxAccel / am;
    }
    this.vx += ax * h;
    this.vz += az * h;
    const sp = Math.hypot(this.vx, this.vz);
    if (sp > MOTION.maxSpeed) {
      this.vx *= MOTION.maxSpeed / sp;
      this.vz *= MOTION.maxSpeed / sp;
    }
    // settle: kill tiny residual drift
    if (sp < 0.002 && Math.hypot(dx, dz) < 0.0008) {
      this.vx = this.vz = 0;
    }
    this.pose.x += this.vx * h;
    this.pose.z += this.vz * h;

    // head forward in world: (−sin yaw, −cos yaw)
    const fx = -Math.sin(this.pose.yaw);
    const fz = -Math.cos(this.pose.yaw);
    const rx = -fz; // right-hand lateral in floor plane
    const rz = fx;
    const fwd = this.vx * fx + this.vz * fz;
    const lat = this.vx * rx + this.vz * rz;
    const k = 1 - Math.exp(-h * 10);
    this.forwardSpeed += (fwd - this.forwardSpeed) * k;
    this.lateral += (lat - this.lateral) * k;

    const speed = Math.hypot(this.vx, this.vz);
    if (this.steeringEnabled && speed > 0.03) {
      // reverse strokes steer toward the opposite of travel direction
      const dirx = fwd >= 0 ? this.vx : -this.vx;
      const dirz = fwd >= 0 ? this.vz : -this.vz;
      const desired = Math.atan2(-dirx, -dirz);
      // only lateral component steers; pure push/pull keeps yaw
      const diff = wrap(desired - this.pose.yaw);
      let rate = diff * MOTION.steer * Math.min(1, speed / 0.6) * Math.min(1, Math.abs(lat) / (speed + 1e-6) + 0.15);
      rate = Math.max(-MOTION.maxYawRate, Math.min(MOTION.maxYawRate, rate));
      let yaw = this.pose.yaw + rate * h;
      const off = wrap(yaw - this.yawCenter);
      const lim = this.yawRange;
      if (off > lim) yaw = this.yawCenter + lim;
      else if (off < -lim) yaw = this.yawCenter - lim;
      this.pose.yaw = yaw;
    }
  }
}
