#!/usr/bin/env node
/**
 * Asset pipeline: Blender procedural build -> GLB (high + balanced) -> optional Meshopt compression.
 *
 *   node scripts/assets-build.mjs                # build + meshopt-compress (keeps *.uncompressed.glb fallbacks)
 *   node scripts/assets-build.mjs --no-meshopt   # build only, uncompressed GLBs at the runtime paths
 *   node scripts/assets-build.mjs --skip-blender # only (re)compress existing GLBs
 *
 * Runtime note: compressed files use EXT_meshopt_compression (+ KHR_mesh_quantization); the loader must call
 * GLTFLoader.setMeshoptDecoder(MeshoptDecoder) from three/examples/jsm/libs/meshopt_decoder.module.js.
 * The uncompressed fallbacks (public/models/powerdetect-<tier>.uncompressed.glb) load with a plain GLTFLoader.
 * Blender binary: $BLENDER_BIN or /Applications/Blender.app/Contents/MacOS/Blender.
 */
import { spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync, rmSync, statSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const MODELS = join(ROOT, 'public', 'models');
const TIERS = ['high', 'balanced'];
const args = new Set(process.argv.slice(2));
const BLENDER = process.env.BLENDER_BIN || '/Applications/Blender.app/Contents/MacOS/Blender';

function runBlender() {
  if (!existsSync(BLENDER)) {
    console.error(`[assets:build] Blender not found at ${BLENDER} (set BLENDER_BIN).`);
    process.exit(1);
  }
  const script = join(ROOT, 'scripts', 'blender', 'v3', 'assemble.py');
  console.log(`[assets:build] ${BLENDER} -b --factory-startup -P ${script} -- --tier all`);
  const r = spawnSync(BLENDER, ['-b', '--factory-startup', '-P', script, '--', '--tier', 'all'], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  const out = `${r.stdout || ''}${r.stderr || ''}`;
  for (const line of out.split('\n')) if (/\[build\]|Error|Traceback/.test(line)) console.log('  ' + line);
  if (r.status !== 0 || /Traceback/.test(out)) {
    console.error('[assets:build] Blender build failed');
    process.exit(1);
  }
}

// Rig nodes that carry meshes (rollers, lights, bin shell/contents) get their mesh moved onto a child
// "<name>_Mesh" node. Quantization may write a dequantization scale/offset onto mesh nodes; this keeps the
// rig nodes' own TRS (identity rotation, unit scale) free for runtime rotation.x / scale.y.
const RIG_MESH_NODES = ['RollerFront', 'RollerRear', 'HeadLights', 'DustbinShell', 'DustbinContents'];
function splitRigMeshes(doc) {
  for (const node of doc.getRoot().listNodes()) {
    if (!RIG_MESH_NODES.includes(node.getName())) continue;
    const mesh = node.getMesh();
    if (!mesh) continue;
    const child = doc.createNode(`${node.getName()}_Mesh`).setMesh(mesh);
    node.setMesh(null);
    node.addChild(child);
  }
}

// Re-encode textures (PNG ORM -> JPEG, palette-quantized decal atlases, halved resolution on balanced) via Pillow.
function optimizeTextures(doc, tier) {
  const tmp = join(ROOT, 'assets', 'source', '.tex_tmp');
  mkdirSync(tmp, { recursive: true });
  let before = 0;
  let after = 0;
  for (const tex of doc.getRoot().listTextures()) {
    const img = tex.getImage();
    if (!img) continue;
    const name = (tex.getName() || 'tex').replace(/[^A-Za-z0-9_-]/g, '_');
    const inp = join(tmp, `${name}.in`);
    const out = join(tmp, `${name}.out`);
    writeFileSync(inp, img);
    const r = spawnSync('python3', [join(ROOT, 'scripts', 'optimize_texture.py'), inp, out, name, tier], { encoding: 'utf8' });
    if (r.status !== 0) {
      console.warn(`[assets:build] texture ${name} left as is: ${r.stderr.trim().split('\n').pop()}`);
      continue;
    }
    const data = readFileSync(out);
    before += img.byteLength;
    if (data.byteLength < img.byteLength) {
      tex.setImage(new Uint8Array(data)).setMimeType(r.stdout.trim());
      after += data.byteLength;
    } else after += img.byteLength;
  }
  rmSync(tmp, { recursive: true, force: true });
  console.log(`[assets:build] ${tier}: textures ${(before / 1e6).toFixed(2)} MB -> ${(after / 1e6).toFixed(2)} MB`);
}

async function compress() {
  const { NodeIO } = await import('@gltf-transform/core');
  const { ALL_EXTENSIONS } = await import('@gltf-transform/extensions');
  const { meshopt, reorder, prune, dedup } = await import('@gltf-transform/functions');
  const { MeshoptEncoder, MeshoptDecoder } = await import('meshoptimizer');
  await MeshoptEncoder.ready;
  await MeshoptDecoder.ready;
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({
    'meshopt.encoder': MeshoptEncoder,
    'meshopt.decoder': MeshoptDecoder,
  });
  const sizes = {};
  for (const tier of TIERS) {
    const src = join(MODELS, `powerdetect-${tier}.glb`);
    const raw = join(MODELS, `powerdetect-${tier}.uncompressed.glb`);
    // uncompressed fallback, always kept; a fresh Blender build overwrites src, so refresh the fallback from it
    if (!args.has('--skip-blender') || !existsSync(raw)) copyFileSync(src, raw);
    const doc = await io.read(raw);
    splitRigMeshes(doc);
    await io.write(raw, doc); // fallback gets the identical node structure
    // dedup/prune never rename or drop named nodes that carry children or meshes; keepLeaves keeps anchor empties
    optimizeTextures(doc, tier);
    await doc.transform(
      dedup(),
      prune({ keepLeaves: true, keepAttributes: true }),
      reorder({ encoder: MeshoptEncoder }),
      meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
    );
    await io.write(src, doc);
    sizes[tier] = { compressed: statSync(src).size, uncompressed: statSync(raw).size };
    console.log(`[assets:build] ${tier}: ${(sizes[tier].uncompressed / 1e6).toFixed(2)} MB -> ${(sizes[tier].compressed / 1e6).toFixed(2)} MB (meshopt)`);
  }
  return sizes;
}

function updateManifest(sizes) {
  const mpath = join(ROOT, 'assets', 'manifest.json');
  if (!existsSync(mpath)) return;
  const manifest = JSON.parse(readFileSync(mpath, 'utf8'));
  const report = JSON.parse(readFileSync(join(ROOT, 'assets', 'source', 'build_report_v3.json'), 'utf8'));
  manifest.files = manifest.files || {};
  for (const tier of TIERS) {
    const f = `public/models/powerdetect-${tier}.glb`;
    manifest.files[f] = {
      bytes: statSync(join(ROOT, f)).size,
      triangles: report.tiers[tier]?.triangles,
      compression: sizes ? 'EXT_meshopt_compression + KHR_mesh_quantization' : 'none',
      uncompressedFallback: sizes ? `public/models/powerdetect-${tier}.uncompressed.glb` : null,
      uncompressedBytes: sizes ? sizes[tier].uncompressed : statSync(join(ROOT, f)).size,
    };
  }
  manifest.updated = new Date().toISOString();
  writeFileSync(mpath, JSON.stringify(manifest, null, 2) + '\n');
  console.log('[assets:build] manifest updated');
}

if (!args.has('--skip-blender')) runBlender();
let sizes = null;
if (!args.has('--no-meshopt')) {
  try {
    sizes = await compress();
  } catch (e) {
    console.warn('[assets:build] meshopt compression failed, keeping uncompressed GLBs:', e.message);
    for (const tier of TIERS) {
      const raw = join(MODELS, `powerdetect-${tier}.uncompressed.glb`);
      if (existsSync(raw)) copyFileSync(raw, join(MODELS, `powerdetect-${tier}.glb`));
    }
    sizes = null;
  }
}
updateManifest(sizes);
console.log('[assets:build] done');
