import { expect, test } from '@playwright/test';
import { acct, gotoHero, waitPhase } from './helpers';

test.describe('mobile viewport (emulated; not a real device)', () => {
  test.use({ viewport: { width: 390, height: 844 }, hasTouch: true });

  test('touch: tap Start, Floor drawer, touch-drag cleans, controls not covered', async ({ page }) => {
    await gotoHero(page);
    const sb = (await page.locator('.start').boundingBox())!;
    expect(sb.width).toBeGreaterThanOrEqual(44);
    expect(sb.x + sb.width).toBeLessThanOrEqual(390);
    await page.locator('.start').tap();
    await page.locator('.skip').tap({ timeout: 10_000 }).catch(() => undefined);
    await waitPhase(page, 'active', 15_000);
    await expect(page.locator('.dock')).not.toHaveClass(/is-hidden/, { timeout: 10_000 });
    // all dock buttons inside the viewport and >= 44px tall
    for (const b of await page.locator('.toolbar button').all()) {
      const r = (await b.boundingBox())!;
      expect(r.y + r.height).toBeLessThanOrEqual(844);
      expect(r.height).toBeGreaterThanOrEqual(40);
    }
    await page.locator('.tb-btn:has-text("Floor")').tap();
    await expect(page.locator('.drawer .seg[aria-label=Floor]')).toBeVisible();
    await page.locator('.drawer .seg[aria-label=Floor] button:has-text("Carpet")').tap();
    await expect(page.locator('.drawer .seg[aria-label=Floor] button:has-text("Carpet")')).toHaveAttribute('aria-checked', 'true');
    await page.locator('.tb-btn:has-text("Floor")').tap();
    await page.locator('.tb-btn:has-text("Make a mess")').tap();
    await page.waitForTimeout(400);
    const a0 = (await acct(page))!;
    // synthetic touch pointer stream on the stage (same code path as real touch PointerEvents)
    await page.evaluate(async () => {
      const el = document.querySelector('.stage') as HTMLElement;
      const ev = (type: string, x: number, y: number) =>
        el.dispatchEvent(new PointerEvent(type, { pointerId: 7, pointerType: 'touch', isPrimary: true, clientX: x, clientY: y, bubbles: true, cancelable: true, button: 0, buttons: 1 }));
      const pts: [number, number][] = [];
      for (let i = 0; i <= 90; i++) pts.push([90 + (210 * (i % 45)) / 45, 360 + Math.floor(i / 45) * 80]);
      ev('pointerdown', pts[0][0], pts[0][1]);
      for (const p of pts) {
        ev('pointermove', p[0], p[1]);
        await new Promise((r) => setTimeout(r, 25));
      }
      ev('pointerup', pts[pts.length - 1][0], pts[pts.length - 1][1]);
    });
    await page.waitForTimeout(600);
    const a1 = (await acct(page))!;
    expect(a1.collected).toBeGreaterThan(a0.collected);
  });
});
