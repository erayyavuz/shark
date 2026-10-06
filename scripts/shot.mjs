// Dev helper: node scripts/shot.mjs <url> <out.png> [w h] [--steps=json]
// steps: [{"wait":ms}|{"click":"selector"}|{"drag":[[x,y],[x,y],...],"dur":ms}|{"key":"KeyA"}|{"eval":"js"}|{"shot":"path"}]
import { chromium, webkit } from 'playwright';
const [url, out, w = '1440', h = '900', ...rest] = process.argv.slice(2);
const stepsArg = rest.find((r) => r.startsWith('--steps='));
const engine = rest.includes('--webkit') ? webkit : chromium;
const touch = rest.includes('--touch');
const steps = stepsArg ? JSON.parse(stepsArg.slice(8)) : [];
const browser = await engine.launch({ args: engine === chromium ? ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] : [] });
const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1, hasTouch: touch, isMobile: touch && engine === chromium });
const logs = [];
page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && logs.push(`[${m.type()}] ${m.text()}`));
page.on('pageerror', (e) => logs.push(`[pageerror] ${e.message}`));
await page.goto(url);
await page.waitForSelector('.start', { timeout: 60000 }).catch(() => logs.push('no start button'));
await page.waitForTimeout(800);
for (const s of steps) {
  if (s.wait) await page.waitForTimeout(s.wait);
  if (s.click) await page.click(s.click);
  if (s.key) await page.keyboard.press(s.key);
  if (s.down) await page.keyboard.down(s.down);
  if (s.up) await page.keyboard.up(s.up);
  if (s.eval) console.log('eval:', JSON.stringify(await page.evaluate(s.eval)));
  if (s.drag) {
    const pts = s.drag;
    const dur = s.dur ?? 1000;
    await page.mouse.move(pts[0][0], pts[0][1]);
    await page.mouse.down();
    const n = Math.max(2, Math.round(dur / 16));
    for (let i = 1; i <= n; i++) {
      const t = (i / n) * (pts.length - 1);
      const a = Math.min(pts.length - 2, Math.floor(t));
      const k = t - a;
      await page.mouse.move(pts[a][0] + (pts[a + 1][0] - pts[a][0]) * k, pts[a][1] + (pts[a + 1][1] - pts[a][1]) * k);
      await page.waitForTimeout(16);
    }
    if (!s.hold) await page.mouse.up();
  }
  if (s.release) await page.mouse.up();
  if (s.shot) await page.screenshot({ path: s.shot });
}
await page.screenshot({ path: out });
console.log(logs.slice(0, 30).join('\n') || 'no console errors');
await browser.close();
