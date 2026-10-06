import { expect, test } from '@playwright/test';
import { acct, attachLogs, debugCounters, gotoHero, toActive, waitPhase, watchConsole } from './helpers';

test.describe('robustness + fallbacks', () => {
  test('10x Start/Back cycles: no monotonic growth of geometries/textures', async ({ page }, info) => {
    test.setTimeout(300_000);
    const log = watchConsole(page);
    await gotoHero(page, '?debug');
    await page.waitForTimeout(4000); // let the background high-model swap settle
    const rows: { i: number; geo: number; tex: number; calls: number }[] = [];
    for (let i = 0; i < 10; i++) {
      await page.click('.start');
      await page.locator('.skip').click({ timeout: 10_000 }).catch(() => undefined);
      await waitPhase(page, 'active', 15_000);
      await page.click('.tb-btn:has-text("Make a mess")');
      await page.click('.tb-btn:has-text("Clear floor")');
      await page.click('.tb-btn:has-text("Make a mess")');
      await page.waitForTimeout(800);
      const c = await debugCounters(page);
      rows.push({ i, geo: c.geo, tex: c.tex, calls: c.calls });
      await page.click('[aria-label="Back to product"]');
      await waitPhase(page, 'hero', 15_000);
      await page.waitForTimeout(600);
    }
    await info.attach('cycles', { body: JSON.stringify(rows, null, 1), contentType: 'application/json' });
    const geo = rows.map((r) => r.geo);
    const tex = rows.map((r) => r.tex);
    // allow warm-up in the first 2 cycles; afterwards no growth
    expect(Math.max(...geo.slice(2)) - geo[2], `geo ${geo.join(',')}`).toBeLessThanOrEqual(2);
    expect(Math.max(...tex.slice(2)) - tex[2], `tex ${tex.join(',')}`).toBeLessThanOrEqual(1);
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });

  test('reduced motion: short fade, no demo pass', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await gotoHero(page);
    await page.click('.start');
    const t0 = Date.now();
    await waitPhase(page, 'active', 5000);
    expect(Date.now() - t0).toBeLessThan(2500);
    const a = (await acct(page))!;
    expect(a.added).toBeGreaterThan(0);
    expect(a.collected, 'no scripted demo pickup').toBe(0);
  });

  test('?nowebgl shows disclosed static fallback with Retry', async ({ page }) => {
    await page.goto('/?nowebgl');
    await waitPhase(page, 'unsupported', 15_000);
    await expect(page.locator('.notice')).toContainText('WebGL');
    await expect(page.locator('.notice button:has-text("Retry")')).toBeVisible();
    expect(await page.locator('canvas').count()).toBe(0);
  });

  test('GLB request aborted -> error + Retry recovers', async ({ page }, info) => {
    const log = watchConsole(page);
    await page.route('**/models/powerdetect-*.glb', (r) => r.abort('failed'));
    await page.goto('/');
    await waitPhase(page, 'error', 30_000);
    await expect(page.locator('.notice')).toContainText(/could not be loaded/i);
    await page.unroute('**/models/powerdetect-*.glb');
    await page.click('.notice button:has-text("Retry")');
    await waitPhase(page, 'hero', 60_000);
    await expect(page.locator('.start')).toBeVisible();
    await page.click('.start');
    await waitPhase(page, 'active', 15_000);
    await attachLogs(info, log);
    // the app logs the load failure once; anything else is unexpected
    const unexpected = log.errors.filter((e) => !/Failed to fetch|Load failed|network|ERR_FAILED|could not|TypeError/i.test(e));
    expect(unexpected).toEqual([]);
  });

  test('GLB 404 -> error state (no endless spinner)', async ({ page }) => {
    await page.route('**/models/powerdetect-balanced.glb', (r) => r.fulfill({ status: 404, body: 'nope' }));
    await page.goto('/');
    await waitPhase(page, 'error', 30_000);
    await expect(page.locator('.notice button:has-text("Retry")')).toBeVisible();
  });

  test('hidden tab does not apply an accumulated simulation jump', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(300);
    const a0 = (await acct(page))!;
    await page.evaluate(() => {
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.waitForTimeout(1500);
    await page.evaluate(() => {
      Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'visible' });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await page.waitForTimeout(500);
    const a1 = (await acct(page))!;
    expect(a1.collected).toBeCloseTo(a0.collected, 6);
    await waitPhase(page, 'active');
  });
});
