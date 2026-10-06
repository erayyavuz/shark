// Captures the hero composition of the real model (UI hidden) as the loading/unsupported poster.
import { chromium } from 'playwright';
const url = process.argv[2] ?? 'http://127.0.0.1:5180/?model=high';
const b = await chromium.launch({ args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 900, height: 1200 }, deviceScaleFactor: 1.5 });
await p.goto(url);
await p.waitForSelector('.start');
await p.waitForTimeout(1500);
await p.addStyleTag({ content: '.overlay{display:none!important}' });
await p.waitForTimeout(300);
await p.screenshot({ path: 'scripts/.poster.png' });
await b.close();
