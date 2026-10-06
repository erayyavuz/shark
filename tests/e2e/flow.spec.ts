import { expect, test } from '@playwright/test';
import { acct, attachLogs, gotoHero, head, phase, toActive, waitPhase, watchConsole } from './helpers';

test.describe('load + state transitions', () => {
  test('fresh load shows hero with the real GLB (no proxy) and no console errors', async ({ page }, info) => {
    const log = watchConsole(page);
    const glbs: { url: string; status: number; local: boolean }[] = [];
    const external: string[] = [];
    page.on('response', (r) => {
      const u = new URL(r.url());
      if (u.pathname.endsWith('.glb')) glbs.push({ url: u.pathname, status: r.status(), local: u.hostname === '127.0.0.1' || u.hostname === 'localhost' });
      if (!['127.0.0.1', 'localhost'].includes(u.hostname) && !u.protocol.startsWith('data') && !u.protocol.startsWith('blob')) external.push(r.url());
    });
    await gotoHero(page);
    expect(page.url()).not.toContain('proxy');
    const balanced = glbs.find((g) => g.url.endsWith('/models/powerdetect-balanced.glb'));
    expect(balanced, 'balanced GLB requested').toBeTruthy();
    expect(balanced!.status).toBe(200);
    expect(glbs.every((g) => g.local)).toBe(true);
    expect(external, 'runtime assets resolve locally').toEqual([]);
    await expect(page.locator('.start')).toBeVisible();
    await expect(page.locator('.start')).toHaveAccessibleName('Start');
    const box = await page.locator('.start').boundingBox();
    expect(box!.width).toBeGreaterThanOrEqual(44);
    expect(box!.height).toBeGreaterThanOrEqual(44);
    await expect(page.locator('.brand-name')).toHaveText(/^Shark PowerDetect/);
    await expect(page.locator('.concept-label')).toBeVisible();
    // canvas is not blank: the hero screenshot has real tonal variation
    const shot = await page.screenshot();
    expect(shot.byteLength).toBeGreaterThan(30_000);
    expect(await phase(page)).toBe('hero');
    await page.waitForTimeout(3000); // allow background high-model swap to happen
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });

  test('Start by mouse runs the full intro to active (no skip)', async ({ page }, info) => {
    const log = watchConsole(page);
    await gotoHero(page);
    await page.click('.start');
    await waitPhase(page, 'starting', 5000);
    await expect(page.locator('.skip')).toBeVisible();
    const t0 = Date.now();
    await waitPhase(page, 'active', 15_000);
    const dur = Date.now() - t0;
    info.annotations.push({ type: 'intro-duration-ms', description: String(dur) });
    // the demo pass picks up part of the intro patch but leaves some mess (§5.3)
    const a = (await acct(page))!;
    expect(a.added).toBeGreaterThan(0);
    expect(a.collected).toBeGreaterThan(0);
    expect(a.remaining).toBeGreaterThan(0);
    await expect(page.locator('.tools button').first()).toBeVisible();
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });

  test('Start by keyboard (Tab to Start + Enter)', async ({ page, browserName }, info) => {
    const log = watchConsole(page);
    await gotoHero(page);
    let focused = false;
    for (let i = 0; i < 12 && !focused; i++) {
      await page.keyboard.press('Tab');
      focused = await page.evaluate(() => document.activeElement?.classList.contains('start') ?? false);
    }
    if (!focused && browserName === 'webkit') {
      // Safari's default only tabs to form fields; Option+Tab reaches every control (platform behaviour)
      info.annotations.push({ type: 'webkit', description: 'Tab alone did not reach Start; used Option(Alt)+Tab' });
      await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur());
      for (let i = 0; i < 12 && !focused; i++) {
        await page.keyboard.press('Alt+Tab');
        focused = await page.evaluate(() => document.activeElement?.classList.contains('start') ?? false);
      }
    }
    expect(focused, 'Start reachable with Tab').toBe(true);
    await page.keyboard.press('Enter');
    await waitPhase(page, 'starting', 5000);
    await waitPhase(page, 'active', 15_000);
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });

  test('Skip intro reaches active quickly', async ({ page }) => {
    await gotoHero(page);
    await page.click('.start');
    await page.locator('.skip').waitFor({ state: 'visible' });
    await page.waitForTimeout(700);
    const t0 = Date.now();
    await page.click('.skip');
    await waitPhase(page, 'active', 3000);
    expect(Date.now() - t0).toBeLessThan(3000);
    expect(await page.locator('.skip').count()).toBe(0);
  });

  test('double-clicking Start does not spawn duplicate intro', async ({ page, browser }) => {
    // reference: single Start on a fresh page (same deterministic seed)
    const ref = await browser.newPage({ viewport: page.viewportSize()! });
    await gotoHero(ref);
    await ref.click('.start');
    await waitPhase(ref, 'active', 15_000);
    const single = (await acct(ref))!;
    await ref.close();
    await gotoHero(page);
    await page.locator('.start').dblclick();
    await waitPhase(page, 'starting', 5000);
    await waitPhase(page, 'active', 15_000);
    const a = (await acct(page))!;
    // a duplicated timeline would add a second intro patch
    expect(a.added).toBeLessThan(single.added * 1.25);
  });

  test('inspect + Done returns to active with the same mess; Back returns to hero and clears', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(300);
    const before = (await acct(page))!;
    const h0 = (await head(page))!;
    await page.click('[aria-label="Inspect product"]');
    await waitPhase(page, 'inspect', 5000);
    for (const p of ['Head', 'Bin', 'Full']) {
      await page.click(`.utility .pill:has-text("${p}")`);
      await page.waitForTimeout(900);
    }
    // orbit by drag; must not clean
    const s = page.viewportSize()!;
    await page.mouse.move(s.width / 2, s.height / 2);
    await page.mouse.down();
    await page.mouse.move(s.width / 2 + 200, s.height / 2 + 30, { steps: 20 });
    await page.mouse.up();
    const mid = (await acct(page))!;
    expect(mid.collected).toBeCloseTo(before.collected, 4);
    await page.click('.utility .pill:has-text("Done")');
    await waitPhase(page, 'active', 5000);
    await page.waitForTimeout(500);
    const after = (await acct(page))!;
    const h1 = (await head(page))!;
    expect(after.added).toBeCloseTo(before.added, 4);
    expect(after.remaining).toBeCloseTo(before.remaining, 4);
    expect(Math.hypot(h1.x - h0.x, h1.z - h0.z)).toBeLessThan(0.05);
    // Escape exits inspect too
    await page.click('[aria-label="Inspect product"]');
    await waitPhase(page, 'inspect', 5000);
    await page.waitForTimeout(1200);
    await page.keyboard.press('Escape');
    await waitPhase(page, 'active', 5000);
    // Back
    await page.click('[aria-label="Back to product"]');
    await waitPhase(page, 'returning', 3000);
    await waitPhase(page, 'hero', 10_000);
    await expect(page.locator('.start')).toBeVisible();
    const cleared = (await acct(page))!;
    expect(cleared.remaining).toBe(0);
  });

  test('sound toggle is off initially and toggles', async ({ page }, info) => {
    const log = watchConsole(page);
    await toActive(page);
    const btn = page.locator('[aria-label^="Sound"]');
    await expect(btn).toHaveAttribute('aria-pressed', 'false');
    await btn.click();
    await expect(page.locator('[aria-label^="Sound"]')).toHaveAttribute('aria-pressed', 'true');
    await page.locator('[aria-label^="Sound"]').click();
    await expect(page.locator('[aria-label^="Sound"]')).toHaveAttribute('aria-pressed', 'false');
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });
});
