import * as THREE from 'three';

/**
 * DEVELOPMENT PROXY ONLY (?proxy=1). Same node names/hierarchy as the real GLB so integration can
 * proceed before the asset exists. Never used by the final experience.
 */
export function buildProxyRig(): THREE.Object3D {
  const grey = new THREE.MeshStandardMaterial({ name: 'M_Housing', color: 0x8d8f91, roughness: 0.45 });
  const purple = new THREE.MeshStandardMaterial({ name: 'M_Purple', color: 0x5b3f8c, roughness: 0.4 });
  const clear = new THREE.MeshStandardMaterial({ name: 'M_ClearBin', color: 0xffffff });
  const led = new THREE.MeshStandardMaterial({ name: 'M_LED', color: 0xffffff });
  const roller = new THREE.MeshStandardMaterial({ name: 'M_RollerFront', color: 0x1b1d1e, roughness: 0.9 });
  const node = (name: string, parent?: THREE.Object3D) => {
    const o = new THREE.Object3D();
    o.name = name;
    parent?.add(o);
    return o;
  };
  const box = (w: number, h: number, d: number, mat: THREE.Material, parent: THREE.Object3D, x = 0, y = 0, z = 0) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
    m.position.set(x, y, z);
    parent.add(m);
    return m;
  };
  const root = node('VacuumRoot');
  const head = node('FloorHead', root);
  box(0.263, 0.07, 0.17, grey, head, 0, 0.04, 0.0);
  const rf = node('RollerFront', head);
  rf.position.set(0, 0.026, 0.05);
  const rfm = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.23, 24), roller);
  rfm.rotation.z = Math.PI / 2;
  rf.add(rfm);
  const rr = node('RollerRear', head);
  rr.position.set(0, 0.02, -0.02);
  const lights = node('HeadLights', head);
  box(0.02, 0.01, 0.005, led, lights, -0.115, 0.03, 0.088);
  box(0.02, 0.01, 0.005, led, lights, 0.115, 0.03, 0.088);
  const intF = node('IntakeFront', head);
  intF.position.set(0, 0, 0.05);
  const intR = node('IntakeRear', head);
  intR.position.set(0, 0, -0.02);
  const contacts = node('FloorContactAnchors', head);
  for (const [x, z] of [[-0.12, 0.08], [0.12, 0.08], [-0.1, -0.11], [0.1, -0.11]]) {
    const c = node('Contact', contacts);
    c.position.set(x, 0, z);
  }
  const neck = node('NeckPivot', head);
  neck.position.set(0, 0.065, -0.09);
  const lower = node('LowerWand', neck);
  box(0.042, 0.55, 0.036, purple, lower, 0, 0.32, 0);
  const flex = node('FlexPivot', lower);
  flex.position.set(0, 0.62, 0);
  const upper = node('UpperWand', flex);
  box(0.05, 0.12, 0.045, grey, upper, 0, 0.06, 0);
  const motor = node('MotorAssembly', upper);
  motor.position.set(0, 0.12, 0);
  const bin = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 0.2, 32), clear);
  bin.name = 'DustbinShell';
  bin.position.y = 0.1;
  motor.add(bin);
  const contents = node('DustbinContents', motor);
  contents.position.y = 0.01;
  const m2 = new THREE.Mesh(new THREE.CylinderGeometry(0.047, 0.047, 0.12, 32), grey);
  m2.position.y = 0.26;
  motor.add(m2);
  const cap = new THREE.Mesh(new THREE.CylinderGeometry(0.047, 0.047, 0.04, 32), purple);
  cap.position.y = 0.34;
  motor.add(cap);
  box(0.035, 0.2, 0.05, grey, motor, 0, 0.18, -0.11);
  const anchor = node('PowerControlAnchor', motor);
  anchor.position.set(0, 0.3, -0.1);
  return root;
}
