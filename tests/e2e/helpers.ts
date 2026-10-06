import { expect, type Page, type TestInfo } from '@playwright/test';

export interface Accounting {
  added: number;
  collected: number;
  remaining: number;
  remainingFraction: number;
}

/** Collect console errors/warnings + page errors. Warnings are attached, errors asserted by the caller. */
export function watchConsole(page: Page) {
  const errors: string[] = [];
  const warnings: string[] = [];
  page.on('console', (m) => {
    if (m.type() === 'error') errors.push(m.text());
    else if (m.type() === 'warning') warnings.push(m.text());
  });
  page.on('pageerror', (e) => errors.push(`[pageerror] ${e.message}`));
  return { errors, warnings };
}

export async function attachLogs(info: TestInfo, log: { errors: string[]; warnings: string[] }) {
  if (log.warnings.length) await info.attach('console-warnings', { body: [...new Set(log.warnings)].join('\n'), contentType: 'text/plain' });
  if (log.errors.length) await info.attach('console-errors', { body: log.errors.join('\n'), contentType: 'text/plain' });
}

export const phase = (page: Page) => page.evaluate(() => (window as any).__pd?.phase?.() ?? null);
export const acct = (page: Page) => page.evaluate(() => (window as any).__pd?.accounting?.() ?? null) as Promise<Accounting | null>;
export const head = (page: Page) => page.evaluate(() => (window as any).__pd?.head?.() ?? null) as Promise<{ x: number; z: number; yaw: number } | null>;

export async function waitPhase(page: Page, p: string, timeout = 30_000) {
  await expect(page.locator('.overlay')).toHaveClass(new RegExp(`phase-${p}\\b`), { timeout });
}

/** Fresh load to hero. */
export async function gotoHero(page: Page, query = '') {
  await page.goto('/' + query);
  await page.waitForSelector('.start', { state: 'visible', timeout: 60_000 });
  await waitPhase(page, 'hero');
  await page.waitForTimeout(500);
}

/** Hero → active via Skip intro (deterministic, fast). */
export async function toActive(page: Page, query = '', skip = true) {
  await gotoHero(page, query);
  await page.click('.start');
  if (skip) {
    await page.locator('.skip').click({ timeout: 10_000 }).catch(() => undefined);
  }
  await waitPhase(page, 'active', 15_000);
  await expect(page.locator('.dock')).not.toHaveClass(/is-hidden/, { timeout: 10_000 });
  await page.waitForTimeout(400);
}

/** Interpolated mouse drag with real time spacing (ms per step). */
export async function drag(page: Page, pts: [number, number][], durMs = 1000, opts: { release?: boolean } = {}) {
  await page.mouse.move(pts[0][0], pts[0][1]);
  await page.mouse.down();
  const n = Math.max(2, Math.round(durMs / 16));
  for (let i = 1; i <= n; i++) {
    const t = (i / n) * (pts.length - 1);
    const a = Math.min(pts.length - 2, Math.floor(t));
    const k = t - a;
    await page.mouse.move(pts[a][0] + (pts[a + 1][0] - pts[a][0]) * k, pts[a][1] + (pts[a + 1][1] - pts[a][1]) * k);
    await page.waitForTimeout(16);
  }
  if (opts.release !== false) await page.mouse.up();
}

/** Screen-space stage points (fractions of viewport) inside the visible floor, above the dock. */
export function vp(page: Page, fx: number, fy: number): [number, number] {
  const s = page.viewportSize()!;
  return [Math.round(s.width * fx), Math.round(s.height * fy)];
}

export async function debugCounters(page: Page) {
  const t = (await page.locator('.debug').textContent()) ?? '';
  const num = (re: RegExp) => {
    const m = t.match(re);
    return m ? Number(m[1]) : NaN;
  };
  return { raw: t, fps: num(/fps (\d+)/), p95: num(/p95 ([\d.]+)ms/), calls: num(/calls (\d+)/), tris: num(/tris (\d+)k/), geo: num(/geo (\d+)/), tex: num(/tex (\d+)/), dpr: num(/dpr ([\d.]+)/) };
}

export const close = (a: number, b: number, eps = 1e-3) => Math.abs(a - b) <= eps * Math.max(1, Math.abs(a), Math.abs(b));
