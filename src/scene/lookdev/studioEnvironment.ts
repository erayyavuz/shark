import * as THREE from 'three';

/**
 * Self-authored HDR environments rendered into PMREM (no downloaded HDRI):
 *
 * DAY  — a photographic product studio: pale gradient sweep, one large overhead-left key softbox, a broad overhead
 *        diffusion panel, two tall strip boxes behind left/right for edge highlights, a dim front-right fill card and
 *        a warm-grey floor bounce. Glossy plastics, the copper wand and the clear bin pick up readable, shaped
 *        reflections instead of RoomEnvironment's generic box room.
 * NIGHT — a dark living room: deep blue-grey walls, a cool moonlit window to the left-back and one small warm practical
 *        (lamp) far right. Very little energy overall; the product's own lights do the work.
 *
 * Emissive values above 1 are intentional (linear HDR; PMREM renders without tone mapping).
 */

function gradientSphere(top: THREE.Color, horizon: THREE.Color, bottom: THREE.Color) {
  const geo = new THREE.SphereGeometry(20, 48, 24);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: { uTop: { value: top }, uHor: { value: horizon }, uBot: { value: bottom } },
    vertexShader: `varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 uTop, uHor, uBot; varying vec3 vDir;
void main(){
  float y = vDir.y;
  vec3 c = y > 0.0 ? mix(uHor, uTop, pow(smoothstep(0.0, 1.0, y), 0.7)) : mix(uHor, uBot, smoothstep(0.0, 0.35, -y));
  gl_FragColor = vec4(c, 1.0);
}`,
  });
  return new THREE.Mesh(geo, mat);
}

/** Rectangular emitter with a soft (feathered) edge, like a diffused softbox face. */
function softbox(w: number, h: number, color: THREE.Color, edge = 0.18) {
  const mat = new THREE.ShaderMaterial({
    side: THREE.DoubleSide,
    depthWrite: false,
    transparent: true,
    blending: THREE.AdditiveBlending,
    uniforms: { uColor: { value: color }, uEdge: { value: edge } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
    fragmentShader: `uniform vec3 uColor; uniform float uEdge; varying vec2 vUv;
void main(){
  vec2 d = min(vUv, 1.0 - vUv);
  float m = smoothstep(0.0, uEdge, d.x) * smoothstep(0.0, uEdge, d.y);
  // slight centre hot-spot like a real diffuser
  float hot = 1.0 + 0.25 * (1.0 - length(vUv - 0.5) * 1.6);
  gl_FragColor = vec4(uColor * m * hot, 1.0);
}`,
  });
  return new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
}

function place(m: THREE.Object3D, pos: [number, number, number], target: [number, number, number] = [0, 0.5, 0]) {
  m.position.set(...pos);
  m.lookAt(new THREE.Vector3(...target));
  return m;
}

const c = (r: number, g: number, b: number, k = 1) => new THREE.Color(r * k, g * k, b * k);

export function buildDayEnvScene() {
  const s = new THREE.Scene();
  s.add(gradientSphere(c(0.82, 0.82, 0.83), c(0.7, 0.69, 0.68), c(0.36, 0.34, 0.32)));
  // key: big overhead-left-front softbox (matches the shadow-casting key direction)
  s.add(place(softbox(3.4, 2.4, c(1, 0.97, 0.93, 7.5)), [-4.2, 5.2, 1.8]));
  // overhead diffusion panel (top light, broad soft sheen on upper surfaces)
  s.add(place(softbox(4.5, 4.5, c(1, 1, 1, 2.2), 0.3), [0.4, 7.5, -0.6]));
  // strip lights behind left and right: long vertical edge highlights on the wand, bin and cap
  s.add(place(softbox(0.7, 5.2, c(0.95, 0.97, 1.0, 9)), [4.6, 2.4, -4.2]));
  s.add(place(softbox(0.6, 4.6, c(1, 0.98, 0.96, 6)), [-5.0, 2.2, -3.4]));
  // restrained front-right fill card
  s.add(place(softbox(3.0, 2.2, c(1, 1, 1, 1.1), 0.35), [5.2, 1.8, 4.2]));
  // floor bounce (warm grey card under the product)
  s.add(place(softbox(8, 8, c(0.62, 0.6, 0.57, 0.55), 0.45), [0, -2.5, 0], [0, 0, 0]));
  return s;
}

export function buildNightEnvScene() {
  const s = new THREE.Scene();
  s.add(gradientSphere(c(0.06, 0.066, 0.078), c(0.045, 0.049, 0.057), c(0.024, 0.025, 0.028)));
  // moonlit window, left-back, with mullions (two panes)
  const win = new THREE.Group();
  const paneL = softbox(1.2, 2.6, c(0.5, 0.58, 0.74, 1.7), 0.06);
  const paneR = softbox(1.2, 2.6, c(0.5, 0.58, 0.74, 1.7), 0.06);
  paneL.position.x = -0.66;
  paneR.position.x = 0.66;
  win.add(paneL, paneR);
  s.add(place(win, [-6.5, 2.6, -3.2]));
  // dim warm practical (table lamp) far right-back
  s.add(place(softbox(0.6, 0.5, c(1.0, 0.66, 0.4, 2.0), 0.4), [6.5, 1.3, -2.8]));
  return s;
}

export function bakeEnv(renderer: THREE.WebGLRenderer, scene: THREE.Scene) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(scene, 0.02, 0.1, 30);
  pmrem.dispose();
  scene.traverse((o) => {
    const m = o as THREE.Mesh;
    if (m.isMesh) {
      m.geometry.dispose();
      (m.material as THREE.Material).dispose();
    }
  });
  return rt.texture;
}
