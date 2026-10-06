import { expect, test, type Page } from '@playwright/test';
import { acct, attachLogs, close, drag, head, toActive, vp, waitPhase, watchConsole } from './helpers';

async function selectTool(page: Page, name: 'Clean' | 'Add dirt') {
  await page.click(`.tools button:has-text("${name}")`);
  await page.waitForTimeout(250);
}

async function clearFloor(page: Page) {
  await page.click('.tb-btn:has-text("Clear floor")');
  await page.waitForTimeout(200);
}

test.describe('dirt + cleaning (accounting via window.__pd)', () => {
  test('each dirt type can be placed by tap and drag; Add dirt never cleans', async ({ page }, info) => {
    const log = watchConsole(page);
    await toActive(page);
    await clearFloor(page);
    let a = (await acct(page))!;
    expect(a.added).toBe(0);
    expect(a.remaining).toBe(0);
    await selectTool(page, 'Add dirt');
    await expect(page.locator('.drawer')).toBeVisible();
    await page.waitForTimeout(1200); // head parks outside the placement zone
    const kinds = ['Dust', 'Hair', 'Pet hair', 'Crumbs', 'Mixed'];
    for (let i = 0; i < kinds.length; i++) {
      const kindBtn = page.getByRole('radio', { name: kinds[i], exact: true });
      await kindBtn.click();
      await expect(kindBtn).toHaveAttribute('aria-checked', 'true');
      const before = (await acct(page))!;
      // tap
      const [tx, ty] = vp(page, 0.25 + i * 0.12, 0.42);
      await page.mouse.click(tx, ty);
      await page.waitForTimeout(150);
      const tapped = (await acct(page))!;
      expect(tapped.added, `${kinds[i]} tap adds mass`).toBeGreaterThan(before.added);
      // drag trail
      await drag(page, [vp(page, 0.25 + i * 0.12, 0.5), vp(page, 0.3 + i * 0.12, 0.65)], 500);
      await page.waitForTimeout(150);
      const dragged = (await acct(page))!;
      expect(dragged.added, `${kinds[i]} drag adds mass`).toBeGreaterThan(tapped.added);
      expect(dragged.collected, 'Add dirt never collects').toBeCloseTo(before.collected, 6);
    }
    // densities
    for (const d of ['Light', 'Medium', 'Heavy']) {
      await page.click(`.seg[aria-label=Density] button:has-text("${d}")`);
      await expect(page.locator(`.seg[aria-label=Density] button:has-text("${d}")`)).toHaveAttribute('aria-checked', 'true');
    }
    a = (await acct(page))!;
    expect(a.collected).toBe(0);
    expect(close(a.added, a.collected + a.remaining)).toBe(true);
    await page.screenshot({ path: info.outputPath('dirt-all-kinds.png') });
    await attachLogs(info, log);
    expect(log.errors).toEqual([]);
  });

  test('slow, fast, diagonal, curving and reverse clean strokes reduce remaining mess; invariant holds', async ({ page }, info) => {
    await toActive(page);
    await clearFloor(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(300);
    await selectTool(page, 'Clean');
    const strokes: [string, [number, number][], number][] = [
      ['slow', [vp(page, 0.3, 0.5), vp(page, 0.7, 0.5)], 2500],
      ['fast', [vp(page, 0.7, 0.6), vp(page, 0.3, 0.6)], 350],
      ['reverse', [vp(page, 0.5, 0.75), vp(page, 0.5, 0.3), vp(page, 0.5, 0.75)], 2000],
      ['diagonal', [vp(page, 0.3, 0.35), vp(page, 0.7, 0.72)], 1500],
      ['curve', [vp(page, 0.3, 0.7), vp(page, 0.45, 0.4), vp(page, 0.6, 0.65), vp(page, 0.72, 0.38)], 2000],
    ];
    const rows: string[] = [];
    let prev = (await acct(page))!;
    const start = prev;
    expect(prev.remaining).toBeGreaterThan(0);
    for (const [name, pts, dur] of strokes) {
      if (name === 'fast') {
        // fast pointer flick, then keep the button down so the speed-limited head can follow the path
        await drag(page, pts, dur, { release: false });
        await page.waitForTimeout(900);
        await page.mouse.up();
      } else await drag(page, pts, dur);
      await page.waitForTimeout(600);
      const now = (await acct(page))!;
      rows.push(`${name}: remaining ${prev.remaining.toFixed(2)} -> ${now.remaining.toFixed(2)} (collected +${(now.collected - prev.collected).toFixed(2)})`);
      expect(now.remaining, `${name} stroke`).toBeLessThanOrEqual(prev.remaining + 1e-6);
      expect(now.added).toBeCloseTo(prev.added, 6);
      expect(close(now.added, now.collected + now.remaining, 1e-3), 'mass invariant').toBe(true);
      prev = now;
    }
    await info.attach('strokes', { body: rows.join('\n'), contentType: 'text/plain' });
    expect(prev.remaining).toBeLessThan(start.remaining * 0.9);
    // idle frames do not collect
    const idle0 = (await acct(page))!;
    await page.waitForTimeout(1500);
    const idle1 = (await acct(page))!;
    expect(idle1.collected).toBeCloseTo(idle0.collected, 6);
  });

  test('stroke moves the nozzle (head follows the pointer, not a cursor eraser)', async ({ page }) => {
    await toActive(page);
    const h0 = (await head(page))!;
    await drag(page, [vp(page, 0.35, 0.5), vp(page, 0.65, 0.5)], 1500);
    await page.waitForTimeout(500);
    const h1 = (await head(page))!;
    expect(Math.hypot(h1.x - h0.x, h1.z - h0.z)).toBeGreaterThan(0.05);
  });

  test('tool isolation: toolbar clicks never move the head or clean; drag starting on toolbar does nothing', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(1500);
    const a0 = (await acct(page))!;
    const h0 = (await head(page))!;
    // click every non-mess toolbar control except floors-change-dirt? (floors preserve dirt, so include them)
    for (const sel of ['.tools button:has-text("Clean")', '.floors button:has-text("Stone")', '.floors button:has-text("Oak")']) {
      await page.click(sel);
      await page.waitForTimeout(300);
    }
    const a1 = (await acct(page))!;
    const h1 = (await head(page))!;
    expect(a1.collected).toBeCloseTo(a0.collected, 6);
    expect(a1.added).toBeCloseTo(a0.added, 6);
    expect(Math.hypot(h1.x - h0.x, h1.z - h0.z)).toBeLessThan(0.01);
    // press on the toolbar, drag into the stage
    const tb = (await page.locator('.toolbar').boundingBox())!;
    await drag(page, [[tb.x + tb.width / 2, tb.y + tb.height / 2], vp(page, 0.4, 0.4), vp(page, 0.6, 0.5)], 800);
    await page.waitForTimeout(500);
    const a2 = (await acct(page))!;
    const h2 = (await head(page))!;
    expect(a2.collected).toBeCloseTo(a1.collected, 6);
    expect(Math.hypot(h2.x - h1.x, h2.z - h1.z)).toBeLessThan(0.01);
    // rapid tool switching: no ghost placement or cleanup
    for (let i = 0; i < 6; i++) {
      await page.keyboard.press(i % 2 ? 'c' : 'a');
      await page.waitForTimeout(60);
    }
    await page.keyboard.press('c');
    await page.waitForTimeout(800);
    const a3 = (await acct(page))!;
    expect(a3.added).toBeCloseTo(a2.added, 6);
    expect(a3.collected).toBeCloseTo(a2.collected, 6);
    // Add dirt drag across a mess never cleans
    await page.keyboard.press('a');
    await page.waitForTimeout(800);
    await drag(page, [vp(page, 0.3, 0.5), vp(page, 0.7, 0.5)], 1000);
    const a4 = (await acct(page))!;
    expect(a4.collected).toBeCloseTo(a3.collected, 6);
    expect(a4.added).toBeGreaterThan(a3.added);
  });

  test('floor switching keeps dirt and accounting', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(800);
    const a0 = (await acct(page))!;
    for (const f of ['Stone', 'Carpet', 'Oak']) {
      await page.click(`.floors button:has-text("${f}")`);
      await expect(page.locator(`.floors button:has-text("${f}")`)).toHaveAttribute('aria-checked', 'true');
      await page.waitForTimeout(800);
      const a = (await acct(page))!;
      expect(a.added).toBeCloseTo(a0.added, 6);
      expect(a.remaining).toBeCloseTo(a0.remaining, 6);
    }
  });

  test('Clear floor resets accounting; All clear shows after cleaning everything', async ({ page }) => {
    await toActive(page);
    await clearFloor(page);
    const z = (await acct(page))!;
    expect([z.added, z.collected, z.remaining]).toEqual([0, 0, 0]);
    // small dust patch then sweep until clear
    await selectTool(page, 'Add dirt');
    await page.getByRole('radio', { name: 'Dust', exact: true }).click();
    await page.click('.seg[aria-label=Density] button:has-text("Light")');
    await page.waitForTimeout(1000);
    await page.mouse.click(...vp(page, 0.5, 0.5));
    await selectTool(page, 'Clean');
    for (let i = 0; i < 6; i++) {
      const y = 0.42 + (i % 3) * 0.08;
      await drag(page, [vp(page, 0.35, y), vp(page, 0.65, y), vp(page, 0.35, y)], 1600);
      await page.waitForTimeout(400);
      if (await page.locator('.clear-msg').isVisible()) break;
    }
    const a = (await acct(page))!;
    await expect(page.locator('.clear-msg')).toBeVisible({ timeout: 3000 });
    expect(a.remainingFraction).toBeLessThan(0.005);
    await page.click('.clear-msg button');
    await expect(page.locator('.clear-msg')).toHaveCount(0);
    expect((await acct(page))!.remaining).toBeGreaterThan(0);
  });

  test('window blur and pointercancel end a stroke mid-drag', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(500);
    for (const kind of ['blur', 'pointercancel'] as const) {
      await page.evaluate(() => {
        (window as any).__lastPid = undefined;
        document.querySelector('.stage')!.addEventListener('pointerdown', (e) => ((window as any).__lastPid = (e as PointerEvent).pointerId), { once: true });
      });
      await drag(page, [vp(page, 0.35, 0.55), vp(page, 0.5, 0.55)], 500, { release: false });
      await expect(page.locator('.overlay')).toHaveClass(/is-stroking/);
      if (kind === 'blur') await page.evaluate(() => window.dispatchEvent(new Event('blur')));
      else
        await page.evaluate(() => {
          const pid = (window as any).__lastPid ?? 1;
          document.querySelector('.stage')!.dispatchEvent(new PointerEvent('pointercancel', { pointerId: pid, bubbles: true, pointerType: 'mouse' }));
        });
      await expect(page.locator('.overlay'), `${kind} ends stroke`).not.toHaveClass(/is-stroking/, { timeout: 2000 });
      await page.waitForTimeout(400);
      const a0 = (await acct(page))!;
      const h0 = (await head(page))!;
      // keep moving with the button still held: must not clean or steer
      for (let i = 0; i < 20; i++) await page.mouse.move(...vp(page, 0.5 + i * 0.01, 0.5));
      await page.waitForTimeout(400);
      const a1 = (await acct(page))!;
      const h1 = (await head(page))!;
      expect(a1.collected, `${kind}: no pickup after cancel`).toBeCloseTo(a0.collected, 6);
      expect(Math.hypot(h1.x - h0.x, h1.z - h0.z)).toBeLessThan(0.02);
      await page.mouse.up();
      await waitPhase(page, 'active');
    }
  });

  test('keyboard: stage focus + arrows move the head, Space vacuums', async ({ page }) => {
    await toActive(page);
    await page.click('.tb-btn:has-text("Make a mess")');
    await page.waitForTimeout(400);
    await page.focus('.stage');
    const h0 = (await head(page))!;
    const a0 = (await acct(page))!;
    await page.keyboard.down('Space');
    await page.keyboard.down('ArrowLeft');
    await page.waitForTimeout(900);
    await page.keyboard.up('ArrowLeft');
    await page.keyboard.down('ArrowUp');
    await page.waitForTimeout(700);
    await page.keyboard.up('ArrowUp');
    await page.keyboard.up('Space');
    await page.waitForTimeout(400);
    const h1 = (await head(page))!;
    const a1 = (await acct(page))!;
    expect(Math.hypot(h1.x - h0.x, h1.z - h0.z)).toBeGreaterThan(0.1);
    expect(a1.collected).toBeGreaterThanOrEqual(a0.collected);
  });
});
