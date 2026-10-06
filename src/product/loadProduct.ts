import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { QualityTier } from '../contracts/types';
import type { RigMeta } from './VacuumRig';

export interface LoadedProduct {
  scene: THREE.Object3D;
  meta: Partial<RigMeta> | null;
}

/** Fetch with truthful byte progress (total only when the server reports Content-Length). */
async function fetchWithProgress(url: string, onProgress: (loaded: number, total: number | null) => void, signal?: AbortSignal) {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  const lenHeader = res.headers.get('content-length');
  const total = lenHeader && !res.headers.get('content-encoding') ? Number(lenHeader) : null;
  if (!res.body) {
    const buf = await res.arrayBuffer();
    onProgress(buf.byteLength, total);
    return buf;
  }
  const reader = res.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    loaded += value.byteLength;
    onProgress(loaded, total);
  }
  const out = new Uint8Array(loaded);
  let o = 0;
  for (const c of chunks) {
    out.set(c, o);
    o += c.byteLength;
  }
  return out.buffer;
}

export async function loadProduct(
  tier: QualityTier,
  onProgress: (loaded: number, total: number | null) => void,
  signal?: AbortSignal,
): Promise<LoadedProduct> {
  const base = import.meta.env.BASE_URL;
  const [buf, meta] = await Promise.all([
    fetchWithProgress(`${base}models/powerdetect-${tier}.glb`, onProgress, signal),
    fetch(`${base}models/rig.json`, { signal })
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null),
  ]);
  const loader = new GLTFLoader();
  loader.setMeshoptDecoder(MeshoptDecoder);
  const gltf = await loader.parseAsync(buf, base);
  return { scene: gltf.scene, meta: meta ? normalizeMeta(meta) : null };
}

function normalizeMeta(raw: Record<string, unknown>): Partial<RigMeta> {
  const out: Partial<RigMeta> = {};
  const n = raw.nozzle as RigMeta['nozzle'] | undefined;
  if (n && typeof n.intakeWidth === 'number') out.nozzle = n;
  if (typeof raw.rollerFrontRadius === 'number') out.rollerFrontRadius = raw.rollerFrontRadius;
  if (typeof raw.rollerRearRadius === 'number') out.rollerRearRadius = raw.rollerRearRadius;
  return out;
}
