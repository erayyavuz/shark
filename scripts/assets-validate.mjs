#!/usr/bin/env node
/**
 * Validates the product GLBs against the rig contract (src/contracts/rig.ts) and asset budgets.
 * Exits non-zero on any failure.
 *
 * Checks per file (runtime GLBs and their *.uncompressed.glb fallbacks when present):
 *   - every RIG_NODES name exists exactly once, with the locked parent hierarchy
 *   - articulated/root nodes have identity rest rotation and unit scale (runtime overwrites rotation)
 *   - Contact_* anchors under FloorContactAnchors and IntakeFront/IntakeRear sit at world y ~= 0
 *   - RollerFront/RollerRear geometry is centred on the node origin with X as the long (spin) axis
 *   - head front faces +Z (front roller z > rear roller z), wand top is above the head
 *   - triangle counts and file sizes inside budget; required material names present
 *   - public/models/rig.json has the NozzleGeometry fields and sane values
 */
import { readFileSync, existsSync, statSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { MeshoptDecoder } from 'meshoptimizer';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MODELS = join(ROOT, 'public', 'models');
const errors = [];
const warnings = [];
const fail = (m) => errors.push(m);
const warn = (m) => warnings.push(m);

const rigSrc = readFileSync(join(ROOT, 'src', 'contracts', 'rig.ts'), 'utf8');
const RIG_NODES = [...rigSrc.match(/RIG_NODES = \[([\s\S]*?)\]/)[1].matchAll(/'([A-Za-z]+)'/g)].map((m) => m[1]);
const PARENT = {
  FloorHead: 'VacuumRoot',
  RollerFront: 'FloorHead',
  RollerRear: 'FloorHead',
  HeadLights: 'FloorHead',
  IntakeFront: 'FloorHead',
  IntakeRear: 'FloorHead',
  FloorContactAnchors: 'FloorHead',
  NeckPivot: 'FloorHead',
  LowerWand: 'NeckPivot',
  FlexPivot: 'LowerWand',
  UpperWand: 'FlexPivot',
  MotorAssembly: 'UpperWand',
  DustbinShell: 'MotorAssembly',
  DustbinContents: 'MotorAssembly',
  PowerControlAnchor: 'MotorAssembly',
};
const IDENTITY_ROT = ['VacuumRoot', 'FloorHead', 'NeckPivot', 'LowerWand', 'FlexPivot', 'UpperWand', 'MotorAssembly', 'RollerFront', 'RollerRear'];
// v3 (IP3251) core materials; see scripts/blender/v3/PARTS_CONTRACT.md
const REQUIRED_MATERIALS = ['M_Gunmetal', 'M_Charcoal', 'M_Purple', 'M_Bronze', 'M_White', 'M_ClearBin', 'M_ClearCover', 'M_LED', 'M_LEDAccent', 'M_LEDRing'];
const BUDGET = {
  high: { tri: [60_000, 260_000], bytes: 8_000_000 },
  balanced: { tri: [30_000, 110_000], bytes: 4_000_000 },
};

// --- tiny mat4 helpers (column-major, glTF convention)
function compose(t, r, s) {
  const [x, y, z, w] = r;
  const x2 = x + x, y2 = y + y, z2 = z + z;
  const xx = x * x2, xy = x * y2, xz = x * z2, yy = y * y2, yz = y * z2, zz = z * z2, wx = w * x2, wy = w * y2, wz = w * z2;
  return [
    (1 - (yy + zz)) * s[0], (xy + wz) * s[0], (xz - wy) * s[0], 0,
    (xy - wz) * s[1], (1 - (xx + zz)) * s[1], (yz + wx) * s[1], 0,
    (xz + wy) * s[2], (yz - wx) * s[2], (1 - (xx + yy)) * s[2], 0,
    t[0], t[1], t[2], 1,
  ];
}
function mul(a, b) {
  const o = new Array(16).fill(0);
  for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c * 4 + r] += a[k * 4 + r] * b[c * 4 + k];
  return o;
}
const xform = (m, p) => [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12], m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13], m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]];

async function checkFile(file, tier) {
  const tag = file.replace(ROOT + '/', '');
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
  const doc = await io.read(file);
  const root = doc.getRoot();
  const nodes = root.listNodes();
  const byName = new Map();
  for (const n of nodes) {
    const nm = n.getName();
    if (byName.has(nm) && RIG_NODES.includes(nm)) fail(`${tag}: duplicate rig node ${nm}`);
    byName.set(nm, n);
  }
  const parentOf = new Map();
  for (const n of nodes) for (const c of n.listChildren()) parentOf.set(c, n);
  for (const nm of RIG_NODES) if (!byName.has(nm)) fail(`${tag}: missing rig node ${nm}`);
  for (const [child, par] of Object.entries(PARENT)) {
    const c = byName.get(child);
    if (c && parentOf.get(c)?.getName() !== par) fail(`${tag}: ${child} parent is ${parentOf.get(c)?.getName()}, expected ${par}`);
  }
  for (const nm of IDENTITY_ROT) {
    const n = byName.get(nm);
    if (!n) continue;
    const r = n.getRotation();
    const s = n.getScale();
    if (Math.abs(r[3]) < 0.99999 || Math.hypot(r[0], r[1], r[2]) > 1e-4) fail(`${tag}: ${nm} rest rotation not identity (${r.map((v) => v.toFixed(4))})`);
    if (s.some((v) => Math.abs(v - 1) > 1e-4)) fail(`${tag}: ${nm} scale not 1 (${s})`);
  }
  // world matrices
  const world = new Map();
  const W = (n) => {
    if (world.has(n)) return world.get(n);
    const local = compose(n.getTranslation(), n.getRotation(), n.getScale());
    const p = parentOf.get(n);
    const m = p ? mul(W(p), local) : local;
    world.set(n, m);
    return m;
  };
  const vr = byName.get('VacuumRoot');
  if (vr && vr.getTranslation().some((v) => Math.abs(v) > 1e-6)) fail(`${tag}: VacuumRoot not at origin`);
  const fca = byName.get('FloorContactAnchors');
  const contacts = fca ? fca.listChildren() : [];
  if (contacts.length < 4) fail(`${tag}: FloorContactAnchors has ${contacts.length} children (<4)`);
  for (const c of [...contacts, byName.get('IntakeFront'), byName.get('IntakeRear')].filter(Boolean)) {
    const y = W(c)[13];
    if (Math.abs(y) > 0.002) fail(`${tag}: anchor ${c.getName()} at y=${y.toFixed(4)} (expected ~0)`);
  }
  // geometry: rollers, triangles, materials, lowest vertex
  let tris = 0;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const n of nodes) {
    const mesh = n.getMesh();
    if (!mesh) continue;
    const m = W(n);
    // roller geometry is checked in the roller node's frame (mesh may sit on a *_Mesh child node)
    const rollerNode = ['RollerFront', 'RollerRear'].includes(n.getName()) ? n : ['RollerFront', 'RollerRear'].includes(parentOf.get(n)?.getName()) ? parentOf.get(n) : null;
    const rT = rollerNode ? [W(rollerNode)[12], W(rollerNode)[13], W(rollerNode)[14]] : null;
    let lmin = [Infinity, Infinity, Infinity];
    let lmax = [-Infinity, -Infinity, -Infinity];
    for (const prim of mesh.listPrimitives()) {
      const idx = prim.getIndices();
      const pos = prim.getAttribute('POSITION');
      tris += (idx ? idx.getCount() : pos.getCount()) / 3;
      const el = [];
      for (let i = 0; i < pos.getCount(); i += 3) {
        pos.getElement(i, el);
        const w = xform(m, el);
        if (rT) {
          for (let k = 0; k < 3; k++) {
            lmin[k] = Math.min(lmin[k], w[k] - rT[k]);
            lmax[k] = Math.max(lmax[k], w[k] - rT[k]);
          }
        }
        minY = Math.min(minY, w[1]);
        maxY = Math.max(maxY, w[1]);
      }
    }
    if (rollerNode) {
      const ext = lmax.map((v, k) => v - lmin[k]);
      const ctr = lmax.map((v, k) => (v + lmin[k]) / 2);
            if (!(ext[0] > ext[1] * 2 && ext[0] > ext[2] * 2)) fail(`${tag}: ${rollerNode.getName()} local X is not the long/spin axis (extent ${ext.map((v) => v.toFixed(3))})`);
      if (Math.abs(ctr[1]) > 0.002 || Math.abs(ctr[2]) > 0.002) fail(`${tag}: ${rollerNode.getName()} geometry not centred on its pivot (${ctr.map((v) => v.toFixed(4))})`);
    }
  }
  for (const r of ['RollerFront', 'RollerRear', 'DustbinShell', 'DustbinContents', 'HeadLights']) {
    const n = byName.get(r);
    if (n && !n.getMesh() && !n.listChildren().some((c) => c.getMesh())) fail(`${tag}: ${r} has no mesh`);
  }
  if (minY < -0.0015) fail(`${tag}: geometry penetrates the floor (min y ${minY.toFixed(4)})`);
  if (minY > 0.0025) fail(`${tag}: product floats (min y ${minY.toFixed(4)})`);
  if (Math.abs(maxY - 1.191) > 0.012) warn(`${tag}: overall height ${maxY.toFixed(4)} vs 1.191 (IP3251 stick incl. handle tip; see DECISIONS.md)`);
  const rf = byName.get('RollerFront');
  const rr = byName.get('RollerRear');
  if (rf && rr && !(W(rf)[14] > W(rr)[14])) fail(`${tag}: head front is not +Z (front roller z ${W(rf)[14]} <= rear ${W(rr)[14]})`);
  const mats = new Set(root.listMaterials().map((m) => m.getName()));
  for (const m of REQUIRED_MATERIALS) if (!mats.has(m)) fail(`${tag}: missing material ${m}`);
  const b = BUDGET[tier];
  const bytes = statSync(file).size;
  tris = Math.round(tris);
  if (b && (tris < b.tri[0] || tris > b.tri[1])) fail(`${tag}: ${tris} triangles outside [${b.tri}]`);
  // size budget applies to the shipped (compressed) files; *.uncompressed.glb are offline fallbacks
  if (b && bytes > b.bytes && !file.includes('.uncompressed')) fail(`${tag}: ${bytes} bytes > ${b.bytes}`);
  const ext = root.listExtensionsUsed().map((e) => e.extensionName);
  console.log(`  ${tag}: ${tris} tris, ${(bytes / 1e6).toFixed(2)} MB, ${nodes.length} nodes, ${mats.size} materials, height ${maxY.toFixed(3)} m${ext.length ? ', ext ' + ext.join('+') : ''}`);
}

function checkRigJson() {
  const p = join(MODELS, 'rig.json');
  if (!existsSync(p)) return fail('public/models/rig.json missing');
  const rig = JSON.parse(readFileSync(p, 'utf8'));
  const n = rig.nozzle || {};
  for (const k of ['intakeWidth', 'intakeZMin', 'intakeZMax', 'shellWidth', 'shellZMin', 'shellZMax']) if (typeof n[k] !== 'number') fail(`rig.json nozzle.${k} missing`);
  if (!(n.intakeZMin < 0 && n.intakeZMax > 0 && n.intakeZMin < n.intakeZMax)) fail('rig.json intake Z range does not straddle the origin');
  if (!(n.shellZMin <= n.intakeZMin && n.shellZMax >= n.intakeZMax)) fail('rig.json shell does not contain intake');
  if (!(n.shellZMin > -0.2 && n.shellZMax < 0.12)) fail(`rig.json shell Z range [${n.shellZMin}, ${n.shellZMax}] is not a floorhead footprint`);
  if (!(n.intakeWidth > 0.15 && n.intakeWidth < n.shellWidth && n.shellWidth < 0.28)) fail('rig.json widths implausible');
  for (const k of ['rollerFrontRadius', 'rollerRearRadius']) if (typeof rig[k] !== 'number') fail(`rig.json ${k} missing`);
  for (const k of ['neckPivot', 'flexPivot', 'powerControlAnchor']) if (!Array.isArray(rig[k]) || rig[k].length !== 3) fail(`rig.json ${k} missing`);
  console.log(`  rig.json: nozzle ${JSON.stringify(n)}`);
}

console.log('[assets:validate]');
let checked = 0;
for (const tier of ['high', 'balanced']) {
  for (const f of [`powerdetect-${tier}.glb`, `powerdetect-${tier}.uncompressed.glb`]) {
    const p = join(MODELS, f);
    if (!existsSync(p)) {
      if (!f.includes('uncompressed')) fail(`missing ${f}`);
      continue;
    }
    await checkFile(p, tier);
    checked++;
  }
}
checkRigJson();
for (const w of warnings) console.warn('  WARN ' + w);
if (errors.length) {
  for (const e of errors) console.error('  FAIL ' + e);
  console.error(`[assets:validate] ${errors.length} failure(s)`);
  process.exit(1);
}
console.log(`[assets:validate] OK (${checked} files)`);
