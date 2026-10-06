// Visual QA evidence capture (brief §14.3 / §14.4).
//   npm run qa:capture                      (uses the running dev server at http://127.0.0.1:5180/)
//   QA_URL=http://127.0.0.1:4173/ npm run qa:capture     (e.g. against `npm run preview`)
//   QA_ONLY=core|viewports|perf|video        (optional: run one section)
// Determinism: Math.random is replaced by a seeded PRNG before page scripts run (the simulation
// itself is seeded with 1251), and every action uses fixed coordinates/timings.
import { chromium, webkit } from 'playwright';
import { mkdir, rename, writeFile, rm } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const BASE = (process.env.QA_URL ?? 'http://127.0.0.1:5180/').replace(/\/?$/, '/');
const OUT = path.resolve('evidence');
const ONLY = process.env.QA_ONLY ?? 'all';
const CHROME_ARGS = ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'];

const VIEWPORTS = [
  { name: '1440x900', width: 1440, height: 900, touch: false },
  { name: '1920x1080', width: 1920, height: 1080, touch: false },
  { name: '390x844', width: 390, height: 844, touch: true },
  { name: '430x932', width: 430, height: 932, touch: true },
  { name: '740x360', width: 740, height: 360, touch: true },
];

const SEED_SCRIPT = `(() => {
  let s = 0x2545f491;
  Math.random = () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
})();`;

const log = [];
const note = (m) => {
  log.push(m);
  console.log(m);
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function newPage(browser, vp, extra = {}) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    deviceScaleFactor: 1,
    hasTouch: !!vp.touch,
    ...extra,
  });
  await ctx.addInitScript(SEED_SCRIPT);
  const page = await ctx.newPage();
  page.__logs = [];
  page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && page.__logs.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => page.__logs.push(`[pageerror] ${e.message}`));
  return { ctx, page };
}

const pd = (page, fn) => page.evaluate((f) => window.__pd?.[f]?.() ?? null, fn);

async function waitPhase(page, p, timeout = 20000) {
  await page.waitForFunction((ph) => document.querySelector('.overlay')?.classList.contains(`phase-${ph}`), p, { timeout });
}

async function gotoHero(page, query = '', settle = 1500) {
  await page.goto(BASE + query);
  await page.waitForSelector('.start', { state: 'visible', timeout: 60000 });
  await waitPhase(page, 'hero');
  await sleep(settle);
}

async function tap(page, sel, touch) {
  if (touch) await page.locator(sel).first().tap();
  else await page.locator(sel).first().click();
}

async function toActive(page, { touch = false, query = '' } = {}) {
  await gotoHero(page, query);
  await tap(page, '.start', touch);
  try {
    await page.locator('.skip').waitFor({ state: 'visible', timeout: 4000 });
    await tap(page, '.skip', touch);
  } catch {
    /* reduced motion has no skip */
  }
  await waitPhase(page, 'active');
  await page.waitForFunction(() => !document.querySelector('.dock')?.classList.contains('is-hidden'), null, { timeout: 10000 });
  await sleep(500);
}

/** Pointer stream on the stage. Mouse uses real input; touch uses PointerEvents (pointerType touch). */
async function stroke(page, pts, dur, { touch = false, hold = false, shots = [] } = {}) {
  const n = Math.max(2, Math.round(dur / 16));
  const at = (i) => {
    const t = (i / n) * (pts.length - 1);
    const a = Math.min(pts.length - 2, Math.floor(t));
    const k = t - a;
    return [pts[a][0] + (pts[a + 1][0] - pts[a][0]) * k, pts[a][1] + (pts[a + 1][1] - pts[a][1]) * k];
  };
  const shotAt = new Map(shots.map((s) => [Math.round(s.at * n), s.path]));
  const tev = (type, x, y) =>
    page.evaluate(
      ([type, x, y]) =>
        document.querySelector('.stage').dispatchEvent(new PointerEvent(type, { pointerId: 11, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 })),
      [type, x, y],
    );
  if (touch) await tev('pointerdown', pts[0][0], pts[0][1]);
  else {
    await page.mouse.move(pts[0][0], pts[0][1]);
    await page.mouse.down();
  }
  for (let i = 1; i <= n; i++) {
    const [x, y] = at(i);
    if (touch) await tev('pointermove', x, y);
    else await page.mouse.move(x, y);
    await sleep(16);
    if (shotAt.has(i)) await page.screenshot({ path: shotAt.get(i) });
  }
  if (!hold) {
    if (touch) await tev('pointerup', pts[pts.length - 1][0], pts[pts.length - 1][1]);
    else await page.mouse.up();
  }
}

const P = (page, fx, fy) => {
  const s = page.viewportSize();
  return [Math.round(s.width * fx), Math.round(s.height * fy)];
};

async function addDirt(page, kind, density, taps, trail, touch = false) {
  await tap(page, '.tools button:has-text("Add dirt")', touch);
  await page.waitForSelector('.drawer');
  await page.getByRole('radio', { name: kind, exact: true }).click();
  await page.locator('.seg[aria-label=Density] button', { hasText: density }).click();
  await sleep(1200); // head parks outside the placement zone
  for (const [x, y] of taps) {
    await page.mouse.click(x, y);
    await sleep(60);
  }
  if (trail) await stroke(page, trail, 700);
  await tap(page, '.tools button:has-text("Clean")', touch);
  await sleep(1400);
}

/** Calibrate: press-and-hold at a screen point on a clean floor so the head settles under it; returns head world pos. */
async function calibrate(page, pt) {
  await stroke(page, [pt, pt], 1400);
  await sleep(400);
  return pd(page, 'head');
}

/** Drive the head with stage-focused arrow keys (no Space → no pickup) to a world position. */
async function driveHead(page, target) {
  await page.focus('.stage');
  for (let i = 0; i < 80; i++) {
    const h = await pd(page, 'head');
    const dx = target.x - h.x;
    const dz = target.z - h.z;
    if (Math.hypot(dx, dz) < 0.03) break;
    const keys = [];
    if (Math.abs(dx) > 0.02) keys.push(dx > 0 ? 'ArrowRight' : 'ArrowLeft');
    if (Math.abs(dz) > 0.02) keys.push(dz > 0 ? 'ArrowDown' : 'ArrowUp');
    for (const k of keys) await page.keyboard.down(k);
    await sleep(Math.min(250, Math.max(40, (Math.max(Math.abs(dx), Math.abs(dz)) / 0.55) * 1000 * 0.6)));
    for (const k of keys) await page.keyboard.up(k);
  }
  await sleep(700);
  await page.evaluate(() => document.activeElement?.blur());
}

async function clearFloor(page) {
  await page.locator('.tb-btn', { hasText: 'Clear floor' }).click();
  await sleep(200);
}

async function shot(page, name) {
  const p = path.join(OUT, name);
  await page.screenshot({ path: p });
  note(`  saved ${name}`);
  return p;
}

// ─────────────────────────── core evidence (Chromium 1440×900 unless noted) ───────────────────────────
async function core(browser) {
  note('core evidence (chromium)');
  const D = VIEWPORTS[0];
  const summary = { errors: [] };
  const section = async (name, fn) => {
    try {
      await fn();
    } catch (e) {
      note(`  SECTION FAILED ${name}: ${String(e).split('\n')[0]}`);
      summary.errors.push({ section: name, error: String(e).slice(0, 400) });
    }
  };

  // hero desktop + mobile
  await section('hero desktop + mobile', async () => {
    const { ctx, page } = await newPage(browser, D);
    await gotoHero(page, '', 5000); // allow the background high-model swap
    await shot(page, 'hero-desktop.png');
    summary.heroConsole = page.__logs.slice();
    await ctx.close();
    const m = await newPage(browser, VIEWPORTS[2]);
    await gotoHero(m.page, '', 2500);
    await shot(m.page, 'hero-mobile.png');
    await m.ctx.close();
  });

  // start transition (full intro, no skip)
  await section('start transition', async () => {
    const { ctx, page } = await newPage(browser, D);
    await gotoHero(page, '', 5000);
    const t0 = Date.now();
    await page.locator('.start').click();
    const times = {};
    for (const [name, ms] of [
      ['start-transition-early.png', 700],
      ['start-transition-mid.png', 1700],
      ['start-transition-end.png', 3000],
    ]) {
      await sleep(Math.max(0, t0 + ms - Date.now()));
      times[name] = Date.now() - t0;
      await shot(page, name);
    }
    await waitPhase(page, 'active');
    times.activeAt = Date.now() - t0;
    summary.startTransitionTimesMs = times;
    await sleep(600);
    await shot(page, 'active-after-intro.png');
    await ctx.close();
  });

  // dust before / midstroke / after
  await section('dust before / midstroke / after', async () => {
    const { ctx, page } = await newPage(browser, D);
    await toActive(page);
    await clearFloor(page);
    const home = await calibrate(page, P(page, 0.28, 0.52));
    await clearFloor(page);
    const taps = [];
    for (let i = 0; i < 7; i++) taps.push(P(page, 0.4 + i * 0.03, 0.5 + ((i % 3) - 1) * 0.04));
    await addDirt(page, 'Dust', 'Heavy', taps, [P(page, 0.38, 0.55), P(page, 0.62, 0.47)]);
    await driveHead(page, home);
    const a0 = await pd(page, 'accounting');
    await shot(page, 'dust-before.png');
    await stroke(page, [P(page, 0.28, 0.52), P(page, 0.7, 0.52)], 3000, { hold: true, shots: [{ at: 0.62, path: path.join(OUT, 'dust-midstroke.png') }] });
    await page.mouse.up();
    note('  saved dust-midstroke.png');
    await sleep(900);
    await shot(page, 'dust-after.png');
    summary.dust = { before: a0, after: await pd(page, 'accounting') };
    await ctx.close();
  });

  // hair capture sequence (partial strand ingestion)
  await section('hair capture sequence', async () => {
    const { ctx, page } = await newPage(browser, D);
    await toActive(page);
    await clearFloor(page);
    const home = await calibrate(page, P(page, 0.28, 0.5));
    await clearFloor(page);
    const taps = [P(page, 0.45, 0.5), P(page, 0.5, 0.52), P(page, 0.55, 0.49), P(page, 0.5, 0.46)];
    await addDirt(page, 'Hair', 'Heavy', taps, [P(page, 0.44, 0.47), P(page, 0.56, 0.53)]);
    await driveHead(page, home);
    const a0 = await pd(page, 'accounting');
    await shot(page, 'hair-before.png');
    await stroke(page, [P(page, 0.28, 0.5), P(page, 0.72, 0.5)], 4000, {
      shots: [0.3, 0.42, 0.54, 0.66].map((at, i) => ({ at, path: path.join(OUT, `hair-capture-sequence-${i + 1}.png`) })),
    });
    note('  saved hair-capture-sequence-1..4.png');
    await sleep(800);
    await shot(page, 'hair-after.png');
    summary.hair = { before: a0, after: await pd(page, 'accounting') };
    await ctx.close();
  });

  // crumbs mid pickup
  await section('crumbs mid pickup', async () => {
    const { ctx, page } = await newPage(browser, D);
    await toActive(page);
    await clearFloor(page);
    const home = await calibrate(page, P(page, 0.28, 0.5));
    await clearFloor(page);
    const taps = [];
    for (let i = 0; i < 6; i++) taps.push(P(page, 0.42 + i * 0.03, 0.5 + ((i % 2) - 0.5) * 0.06));
    await addDirt(page, 'Crumbs', 'Heavy', taps, [P(page, 0.43, 0.53), P(page, 0.57, 0.47)]);
    await driveHead(page, home);
    const a0 = await pd(page, 'accounting');
    await shot(page, 'crumbs-before.png');
    await stroke(page, [P(page, 0.28, 0.5), P(page, 0.72, 0.5)], 3600, { shots: [{ at: 0.24, path: path.join(OUT, 'crumbs-mid-pickup.png') }, { at: 0.32, path: path.join(OUT, 'crumbs-mid-pickup-2.png') }] });
    note('  saved crumbs-mid-pickup.png');
    await sleep(800);
    summary.crumbs = { before: a0, after: await pd(page, 'accounting') };
    await ctx.close();
  });

  // floors with existing dirt
  await section('floors with existing dirt', async () => {
    const { ctx, page } = await newPage(browser, D);
    await toActive(page);
    await clearFloor(page);
    await page.locator('.tb-btn', { hasText: 'Make a mess' }).click();
    await sleep(600);
    await shot(page, 'oak-active.png');
    const before = await pd(page, 'accounting');
    for (const f of ['Stone', 'Carpet']) {
      await page.locator('.floors button', { hasText: f }).click();
      await sleep(1800);
      await shot(page, `${f.toLowerCase()}-active.png`);
    }
    summary.floors = { before, after: await pd(page, 'accounting') };
    await ctx.close();
  });

  // product inspection views (reduced motion → head at origin with ACTIVE.yaw, so theta math is exact)
  await section('product inspection views', async () => {
    const { ctx, page } = await newPage(browser, D, { reducedMotion: 'reduce' });
    await toActive(page);
    await clearFloor(page);
    const h = await pd(page, 'head');
    await page.locator('[aria-label="Inspect product"]').click();
    await waitPhase(page, 'inspect');
    await sleep(1500);
    // current theta ≈ atan2(camOff.x, camOff.z); product front faces world angle yaw+π
    const front = h.yaw + Math.PI;
    const s = page.viewportSize();
    let theta = null;
    const orbitTo = async (target) => {
      // orbit: theta -= dx * 0.006 ; drag in small chunks
      const dx = -(target - theta) / 0.006;
      const steps = Math.max(2, Math.round(Math.abs(dx) / 8));
      await page.mouse.move(s.width / 2, s.height / 2);
      await page.mouse.down();
      for (let i = 1; i <= steps; i++) await page.mouse.move(s.width / 2 + (dx * i) / steps, s.height / 2);
      await page.mouse.up();
      theta = target;
      await sleep(500);
    };
    // estimate starting theta: active camera sits at azimuth 0 relative to the area center (+Z side)
    theta = Math.atan2(0 - h.x, 1 - h.z);
    await page.locator('.utility .pill', { hasText: 'Full' }).click();
    await sleep(1200);
    const views = [
      ['product-front.png', front],
      ['product-three-quarter.png', front + Math.PI / 4],
      ['product-side.png', front + Math.PI / 2],
      ['product-back.png', front + Math.PI],
    ];
    for (const [name, t] of views) {
      await orbitTo(t);
      await shot(page, name);
    }
    await orbitTo(front + Math.PI / 5);
    await page.locator('.utility .pill', { hasText: 'Head' }).click();
    await sleep(1300);
    await shot(page, 'head-closeup.png');
    await page.locator('.utility .pill', { hasText: 'Bin' }).click();
    await sleep(1300);
    await shot(page, 'bin-closeup.png');
    summary.inspect = { head: h, frontTheta: front };
    await page.locator('.utility .pill', { hasText: 'Done' }).click();
    await waitPhase(page, 'active');
    await ctx.close();
  });

  // reduced motion arrival
  await section('reduced motion arrival', async () => {
    const { ctx, page } = await newPage(browser, D, { reducedMotion: 'reduce' });
    await gotoHero(page, '', 3000);
    const t0 = Date.now();
    await page.locator('.start').click();
    await waitPhase(page, 'active');
    summary.reducedMotionActiveMs = Date.now() - t0;
    await sleep(500);
    await shot(page, 'reduced-motion.png');
    summary.reducedMotionAccounting = await pd(page, 'accounting');
    await ctx.close();
  });

  // mobile controls (390×844, touch)
  await section('mobile controls', async () => {
    const M = VIEWPORTS[2];
    const { ctx, page } = await newPage(browser, M);
    await toActive(page, { touch: true });
    await page.locator('.tb-btn', { hasText: 'Make a mess' }).tap();
    await sleep(500);
    await shot(page, 'mobile-controls.png');
    await page.locator('.tools button', { hasText: 'Add dirt' }).tap();
    await sleep(900);
    await shot(page, 'mobile-dirt-drawer.png');
    await page.locator('.tools button', { hasText: 'Clean' }).tap();
    await page.locator('.tb-btn', { hasText: 'Floor' }).tap();
    await sleep(500);
    await shot(page, 'mobile-floor-drawer.png');
    await page.locator('.tb-btn', { hasText: 'Floor' }).tap();
    await sleep(300);
    await stroke(page, [P(page, 0.2, 0.5), P(page, 0.8, 0.5)], 1600, { touch: true, hold: true, shots: [{ at: 0.6, path: path.join(OUT, 'mobile-midstroke.png') }] });
    await page.evaluate(() => document.querySelector('.stage').dispatchEvent(new PointerEvent('pointerup', { pointerId: 11, pointerType: 'touch', bubbles: true })));
    note('  saved mobile-midstroke.png');
    await ctx.close();
  });

  // fallbacks
  await section('fallbacks', async () => {
    const { ctx, page } = await newPage(browser, D);
    await page.goto(BASE + '?nowebgl');
    await waitPhase(page, 'unsupported');
    await sleep(500);
    await shot(page, 'fallback-nowebgl.png');
    await page.route('**/models/powerdetect-*.glb', (r) => r.abort('failed'));
    await page.goto(BASE);
    await waitPhase(page, 'error', 30000);
    await sleep(400);
    await shot(page, 'fallback-asset-error.png');
    await ctx.close();
  });
  return summary;
}

// ─────────────────────────── all viewports × browsers ───────────────────────────
async function viewports(engines) {
  const dir = path.join(OUT, 'viewports');
  await mkdir(dir, { recursive: true });
  const rows = [];
  for (const [bname, browser] of engines) {
    for (const vp of VIEWPORTS) {
      note(`viewport ${bname} ${vp.name}`);
      const { ctx, page } = await newPage(browser, vp);
      try {
        await gotoHero(page, '', 3000);
        await page.screenshot({ path: path.join(dir, `hero-${vp.name}-${bname}.png`) });
        const sb = await page.locator('.start').boundingBox();
        await toActive(page, { touch: vp.touch });
        await page.locator('.tb-btn', { hasText: 'Make a mess' }).first().click();
        await sleep(600);
        await page.screenshot({ path: path.join(dir, `active-${vp.name}-${bname}.png`) });
        const dock = await page.locator('.dock').boundingBox();
        rows.push({ browser: bname, viewport: vp.name, startButton: sb, dock, console: page.__logs.slice(0, 20) });
      } catch (e) {
        rows.push({ browser: bname, viewport: vp.name, error: String(e).slice(0, 300), console: page.__logs.slice(0, 20) });
        note(`  FAILED ${e}`);
      }
      await ctx.close();
    }
  }
  return rows;
}

// ─────────────────────────── perf during an active cleaning stroke ───────────────────────────
async function perf(engines) {
  const out = { note: 'Frame deltas from requestAnimationFrame during a continuous ~6 s cleaning stroke after Make a mess; debug = ?debug overlay text sampled each 500 ms. Headless browser on the declared machine; not a real mobile device.', runs: [] };
  for (const [bname, browser] of engines) {
    for (const vp of VIEWPORTS) {
      note(`perf ${bname} ${vp.name}`);
      const { ctx, page } = await newPage(browser, vp);
      try {
        await toActive(page, { query: '?debug', touch: vp.touch });
        await page.locator('.tb-btn', { hasText: 'Make a mess' }).first().click();
        await page.locator('.tb-btn', { hasText: 'Make a mess' }).first().click();
        await sleep(2500); // let the PerfGovernor settle
        await page.evaluate(() => {
          const w = window;
          w.__ft = [];
          let last = performance.now();
          const f = (t) => {
            w.__ft.push(+(t - last).toFixed(2));
            last = t;
            if (w.__ftOn) requestAnimationFrame(f);
          };
          w.__ftOn = true;
          requestAnimationFrame(f);
        });
        const debug = [];
        const sampler = setInterval(async () => {
          try {
            debug.push(await page.locator('.debug').textContent());
          } catch {}
        }, 500);
        const pts = [P(page, 0.25, 0.45), P(page, 0.75, 0.45), P(page, 0.75, 0.6), P(page, 0.25, 0.6), P(page, 0.25, 0.45), P(page, 0.75, 0.52)];
        await stroke(page, pts, 6000, { touch: vp.touch });
        clearInterval(sampler);
        const ft = await page.evaluate(() => {
          window.__ftOn = false;
          return window.__ft.slice(5);
        });
        const s = [...ft].sort((a, b) => a - b);
        const q = (p) => s[Math.min(s.length - 1, Math.floor(s.length * p))];
        out.runs.push({
          browser: bname,
          browserVersion: browser.version(),
          viewport: vp.name,
          frames: ft.length,
          meanMs: +(ft.reduce((a, b) => a + b, 0) / ft.length).toFixed(2),
          p50Ms: q(0.5),
          p95Ms: q(0.95),
          p99Ms: q(0.99),
          maxMs: s[s.length - 1],
          over20ms: ft.filter((x) => x > 20).length,
          debug,
          samplesMs: ft,
        });
      } catch (e) {
        out.runs.push({ browser: bname, viewport: vp.name, error: String(e).slice(0, 300) });
      }
      await ctx.close();
    }
  }
  return out;
}

// ─────────────────────────── short recorded interaction ───────────────────────────
async function video(browser) {
  note('video (chromium 1280×720)');
  const vdir = path.join(OUT, '.video-tmp');
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, recordVideo: { dir: vdir, size: { width: 1280, height: 720 } } });
  await ctx.addInitScript(SEED_SCRIPT);
  const page = await ctx.newPage();
  await gotoHero(page, '', 3500);
  await page.locator('.start').click();
  await waitPhase(page, 'active');
  await sleep(600);
  await addDirt(page, 'Mixed', 'Heavy', [P(page, 0.45, 0.5), P(page, 0.55, 0.55)], [P(page, 0.35, 0.6), P(page, 0.65, 0.45)]);
  await stroke(page, [P(page, 0.3, 0.55), P(page, 0.7, 0.5), P(page, 0.35, 0.45), P(page, 0.68, 0.62)], 4500);
  await page.locator('.floors button', { hasText: 'Carpet' }).click();
  await sleep(1200);
  await stroke(page, [P(page, 0.3, 0.5), P(page, 0.7, 0.55)], 2000);
  await page.locator('[aria-label="Inspect product"]').click();
  await sleep(1600);
  await page.locator('.utility .pill', { hasText: 'Done' }).click();
  await sleep(1300);
  await page.locator('[aria-label="Back to product"]').click();
  await waitPhase(page, 'hero');
  await sleep(1200);
  const v = page.video();
  await ctx.close();
  const src = await v.path();
  await rename(src, path.join(OUT, 'interaction.webm'));
  await rm(vdir, { recursive: true, force: true });
  note('  saved interaction.webm');
}

// ─────────────────────────── main ───────────────────────────
await mkdir(OUT, { recursive: true });
const cr = await chromium.launch({ args: CHROME_ARGS });
const wk = await webkit.launch();
const engines = [
  ['chromium', cr],
  ['webkit', wk],
];
const env = { date: new Date().toISOString(), base: BASE, chromium: cr.version(), webkit: wk.version(), node: process.version, platform: `${process.platform} ${process.arch}` };
const result = { env };
try {
  if (ONLY === 'all' || ONLY === 'core') result.core = await core(cr);
  if (ONLY === 'all' || ONLY === 'viewports') result.viewports = await viewports(engines);
  if (ONLY === 'all' || ONLY === 'perf') {
    const p = await perf(engines);
    await writeFile(path.join(OUT, 'perf.json'), JSON.stringify({ env, ...p }, null, 1));
    note('saved perf.json');
    result.perfSummary = p.runs.map(({ samplesMs, debug, ...r }) => ({ ...r, lastDebug: debug?.at(-1) }));
  }
  if (ONLY === 'all' || ONLY === 'video') await video(cr);
} finally {
  await cr.close();
  await wk.close();
}
const summaryPath = path.join(OUT, ONLY === 'all' ? 'capture-summary.json' : `capture-summary-${ONLY}.json`);
await writeFile(summaryPath, JSON.stringify({ ...result, log }, null, 1));
console.log(`done → ${path.relative(process.cwd(), summaryPath)}${existsSync(path.join(OUT, 'interaction.webm')) ? ' (+ interaction.webm)' : ''}`);
