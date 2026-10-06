# QA Report — Shark PowerDetect interactive experience

Author: visual-qa-engineer agent. Date of runs: 2026-10-04/05 (local time). This report covers only what was actually run; anything not run is marked **NOT TESTED**.

## 1. Environment

| Item | Value |
|---|---|
| Hardware | Apple MacBook, Apple M2, 8 GB RAM |
| OS | macOS 27.0.1 (build 26A434) |
| Node | v22.16.0 |
| Playwright | 1.63.0 |
| Chromium (Playwright build) | 153.0.8010.12, headless, launch args `--use-angle=metal --enable-gpu --ignore-gpu-blocklist`; WebGL renderer reported: `ANGLE (Apple, ANGLE Metal Renderer: Apple M2)` |
| WebKit (Playwright build) | 26.6, headless; WebGL renderer reported: `Apple GPU` |
| Device pixel ratio | 1 in every run (deviceScaleFactor 1). Retina/DPR 2–3 rendering was **NOT TESTED**. |
| App under test | e2e: production build served by `vite preview` on :4173 (playwright.config.ts). Evidence capture: dev server http://127.0.0.1:5180/. |
| Assets | `public/models/powerdetect-balanced.glb` (1,287,464 B) and `powerdetect-high.glb` (1,667,716 B), both timestamped 2026-10-04 23:44. The product-modeler was changing GLBs in parallel; final captures and final e2e run used these files. |

Real devices: **no real iPhone, iPad or Android device was tested.** All "mobile" results are desktop browser emulation (viewport + `hasTouch`) and are not mobile performance evidence. Firefox **NOT TESTED** (not installed / not in scope).

## 2. What was run

1. `npx playwright test` — 22 tests × 2 projects (Chromium, WebKit) = **44 passed, 0 failed** (6.1 min, final full run). After that run the "fast stroke" step was changed to keep the pointer down after the flick, and the two affected tests were re-run: 4/4 passed.
2. `npm run qa:capture` (`scripts/qa-capture.mjs`) — full run, no section errors. Output in `evidence/`.
3. One-off load measurement (scratch script, not part of qa:capture) against `vite preview` with Chromium CDP throttling → `evidence/load.jsonl`.
4. Every PNG listed in §5 below was opened and inspected (individually or in side-by-side Chromium/WebKit sheets). The video was inspected as a 12-frame contact sheet (1 frame / 3 s).

The read-only test hook `window.__pd` (phase / accounting / head / area), added by the lead during this run, is used for all accounting assertions.

## 3. §14.2 browser interaction checks

| # | Check | Result | How / evidence |
|---|---|---|---|
| 1 | Fresh load, real asset, hero | **PASS** (Chromium, WebKit) | `flow.spec` test 1: `/models/powerdetect-balanced.glb` → 200 from 127.0.0.1, no `?proxy`, no non-local requests, Start ≥44×44 px, phase `hero`, no console errors. `hero-desktop.png`, `hero-mobile.png`, `viewports/hero-*`. |
| 2 | Start by mouse and keyboard; inspect transition | **PASS** | Mouse: full intro reached `active` in 3318 ms (Chromium) / 3823 ms (WebKit), wall clock incl. 120 ms press delay. Keyboard: Tab → Start → Enter works in Chromium; in WebKit plain Tab does not reach buttons (Safari default), Option+Tab does — platform behaviour, not an app defect. Transition frames: `start-transition-early/mid/end.png` (0.7 s / 1.7 s / 3.0 s). Double-click on Start does not add a second intro patch. |
| 3 | Each dirt category, tap + drag | **PASS** (center region) | Dust, Hair, Pet hair, Crumbs, Mixed × tap and drag all increase `added`; `collected` stays 0 in Add dirt. Densities selectable. Placement near reachable *boundaries* was **not** specifically tested. |
| 4 | Slow / fast / diagonal / curving / reverse strokes | **PASS** | Each stroke never increases `remaining`; `added` unchanged; `added ≈ collected + remaining` (rel. 1e‑3) after every stroke. Example (Chromium): slow −72.8, fast(+hold) −14.6, reverse −13.9, diagonal −6.5, curve −4.9 mass units. Visual: `dust-before/midstroke/after.png` show a clean band exactly along the head path with an untouched strip beside it. |
| 5 | Drag onto UI, pointer cancel, leave/re-enter window | **PARTIAL PASS** | Press on toolbar then drag into stage: no head move, no pickup. Synthetic `pointercancel` and window `blur` mid-stroke end the stroke (`is-stroking` removed) and later moves with button held neither clean nor steer. A stroke that *starts on the stage and passes over the toolbar* was **NOT TESTED**. Real OS window switching **NOT TESTED** (synthetic blur only). |
| 6 | Rapid tool switching | **PASS** | 7 alternating A/C key presses: no change in `added`/`collected`; Add-dirt drag across a mess never collects. |
| 7 | Floors with existing dirt | **PASS** | Oak→Stone→Carpet→Oak: `added`/`remaining` identical; `oak-active.png`, `stone-active.png`, `carpet-active.png` show identical dirt positions. Ground contact looks correct on all three; readability on carpet is poor (D3). |
| 8 | Inspect and return | **PASS** | Presets Full/Head/Bin, orbit drag (no pickup), Done and Esc both return to `active`; mess and head pose unchanged (<5 cm). |
| 9 | Sound toggle; hide/show tab | **PARTIAL** | Sound is off initially and toggles (aria-pressed). Actual audio output **NOT TESTED** (headless). Hidden tab was simulated by overriding `document.hidden` + dispatching `visibilitychange`: no pickup jump. A real backgrounded tab (rAF throttling) **NOT TESTED**. |
| 10 | Clear/add repeatedly; 10× Back/Start | **PASS** | Clear floor → accounting 0/0/0. 10 cycles (Start, Skip, Make a mess, Clear, Make a mess, Back) with `?debug`: `geo 37, tex 11, calls 61` in every cycle in both engines — no growth. |
| 11 | Asset failure, reduced motion, no WebGL | **PASS** | Aborted GLB → `error` phase with message + Retry; un-route + Retry → hero → Start works. 404 GLB → error (no endless spinner). `?nowebgl` → disclosed static fallback + Retry, no canvas. Reduced motion: `active` in ~0.7–0.8 s, intro patch present, `collected = 0` (no demo pass). `fallback-*.png`, `reduced-motion.png`. |
| 12 | Local assets; no scene/shader/console errors | **PASS** | No non-local requests. Console errors: none in any normal-flow test in either engine. Only warning: `THREE.Clock: This module has been deprecated. Please use THREE.Timer instead.` (every load). The asset-failure tests log the expected fetch error (`TypeError: Failed to fetch` / `Load failed`). |

Additional checks run: keyboard drive (stage focus + arrows moves head ≥10 cm, Space pickup); touch-pointer stroke on a 390×844 emulated viewport cleans; all mobile dock buttons inside viewport and ≥40 px tall; "All clear." appears below 0.5 % remaining and "Make another mess." adds mess without a reload.

## 4. §14.3 viewports

Captured hero + active (after Make a mess) at 1440×900, 1920×1080, 390×844, 430×932, 740×360 in **both** Chromium and WebKit (`evidence/viewports/`, 20 files). Chromium and WebKit renders are visually equivalent at every viewport (compared side by side). Start button stays right of the product and on-screen at all five sizes; mobile dock fits every width. Safe-area insets and dynamic viewport height were **NOT TESTED** (no notch emulation).

## 5. §14.4 evidence (all in `evidence/`, all opened)

hero-desktop, hero-mobile, product-front, product-side, product-back, product-three-quarter, head-closeup, bin-closeup, start-transition-early/mid/end, dust-before/midstroke/after, hair-before, hair-capture-sequence-1..4, hair-after, crumbs-before, crumbs-mid-pickup, crumbs-mid-pickup-2, oak-active, carpet-active, stone-active, mobile-controls, mobile-dirt-drawer, mobile-floor-drawer, mobile-midstroke, reduced-motion, active-after-intro, fallback-nowebgl, fallback-asset-error, viewports/*, interaction.webm (34.4 s, Chromium 1280×720: hero → full intro → add mixed dirt → clean → carpet → clean → inspect → Done → Back), perf.json, capture-summary.json (accounting before/after each capture, transition timings), load.jsonl.

Determinism: `Math.random` is replaced by a seeded xorshift before page scripts (the simulation itself uses seed 1251); all coordinates and timings are fixed. Strokes are real-time, so exact pickup amounts vary run to run (e.g. dust remaining after the stroke was 59 in one run and 100 in another); dirt placement is reproducible.

Hair capture: `hair-capture-sequence-2..4` show strands partly under the intake and partly still on the floor (partial ingestion) — visible. Crumbs: `crumbs-mid-pickup*.png` show crumbs disappearing at the intake edge while the rest stay put.

## 6. Measured performance

`evidence/perf.json`: rAF frame deltas during a continuous ~6 s cleaning stroke over a double "Make a mess", plus the `?debug` line. Headless, DPR 1, M2. rAF is vsync-limited at 60 Hz, so 16.7 ms is the floor.

| Browser | Viewport | p50 | p95 | p99 | max | frames >20 ms | in-app overlay (last sample) |
|---|---|---|---|---|---|---|---|
| Chromium | 1440×900 | 16.7 | 16.8 | 16.8 | 16.8 | 0 | p95 18.1 ms, 61 calls, 227k tris, dpr 1.5 |
| Chromium | 1920×1080 | 16.7 | 16.8 | 16.8 | 16.8 | 0 | p95 18.7 ms, 61 calls, 227k tris, dpr 1.25 |
| Chromium | 390×844 | 16.7 | 16.7 | 16.8 | 16.8 | 0 | p95 18.2 ms, 65 calls, 119k tris |
| Chromium | 430×932 | 16.7 | 16.8 | 16.8 | 16.8 | 0 | p95 18.3 ms, 65 calls, 118k tris |
| Chromium | 740×360 | 16.7 | 16.8 | 16.8 | 16.8 | 0 | p95 18.4 ms, 66 calls, 109k tris |
| WebKit | 1440×900 | 17 | 18 | 19 | 20 | 0 | p95 18.0 ms, 62 calls |
| WebKit | 1920×1080 | 17 | **21** | 29 | 34 | 24 / 446 | p95 21.0 ms |
| WebKit | 390×844 | 17 | 18 | 19 | 19 | 0 | p95 18.0 ms |
| WebKit | 430×932 | 17 | 18 | 18 | 19 | 0 | p95 18.0 ms |
| WebKit | 740×360 | 17 | 18 | 18 | 19 | 0 | p95 18.0 ms |

(WebKit reports rAF timestamps in whole milliseconds.) Desktop target "p95 < 20 ms" met on this machine everywhere except WebKit 1920×1080 (21 ms). Draw calls 61–66 (< 90/150 budgets). Mobile performance on a real mid-range device: **NOT TESTED**.

Load (`evidence/load.jsonl`, production build, Chromium, cache disabled):
- Unthrottled desktop: hero at 581 ms; 3.79 MB transferred total (incl. 1.67 MB background high-model upgrade).
- CDP throttle 10 Mbps down / 5 Mbps up / 40 ms latency: hero at 1.82 s (desktop) / 1.77 s (390×844); 1.71 MB transferred before hero (JS 365 KB + balanced GLB 1.29 MB); total after idle 3.79 MB desktop, 2.12 MB mobile-size viewport. This is DevTools throttling, not a real network.

## 7. Defects

Severity: High = blocks a "finished" claim; Medium = clearly visible quality problem; Low = polish; Info = observation.

| ID | Sev | Owner | Defect | Evidence |
|---|---|---|---|---|
| D1 | Medium | lead / interaction-designer | On portrait mobile, opening Add dirt parks the head off-screen right (`area.maxX + 0.24`), so the motor body and handle lie diagonally across the upper part of the floor and dominate the view while the drawer is open; it stays there after returning to Clean until the next stroke. | `mobile-dirt-drawer.png`, `mobile-floor-drawer.png` |
| D2 | Medium | simulation-engineer (+ lookdev) | Dust deposits from Make a mess / taps render as soft multi-lobed blobs with scalloped edges; on stone and oak several read like paw prints or smoke puffs rather than fine dust. | `stone-active.png`, `oak-active.png`, `dust-before.png` |
| D3 | Medium | lookdev-artist (+ simulation-engineer) | On Carpet the same mess is barely readable: dust and hair almost disappear into the high-frequency carpet texture (compare identical positions on stone). | `carpet-active.png` vs `stone-active.png` |
| D4 | Low | lookdev-artist | Oak texture: the same grain figure visibly repeats across planks in active view; at inspect head distance the wood texture is soft/blurred. | `oak-active.png`, `head-closeup.png` |
| D5 | Low | lead | WebKit 1920×1080 p95 21 ms (target < 20 ms) during a cleaning stroke. | `perf.json` |
| D6 | Low | lead | PerfGovernor raises render DPR above the display DPR (display DPR 1, governor settled at 1.25–1.5): supersampling cost with no benefit on DPR‑1 screens. `initialDpr` caps at `devicePixelRatio`, the governor does not. | `perf.json` debug lines (`dpr 1.25/1.5`) |
| D7 | Low | lead / interaction-designer | HTML labels collide with the scene/UI: "Shark PowerDetect" sits over the vacuum handle in active desktop views; "Independent concept" sits over the vacuum body on mobile active and overlaps the dock edge at 740×360. | `dust-after.png`, `mobile-controls.png`, `viewports/active-740x360-*.png` |
| D8 | Low | lead | Fallback/error state: the notice card covers the floorhead in the poster, and the poster's background rectangle is visibly lighter than the page background. | `fallback-nowebgl.png`, `fallback-asset-error.png` |
| D9 | Low | lead | Inspect "Bin" preset crops the top of the purple filter cap. | `bin-closeup.png` |
| D10 | Low | product-modeler (verify vs references) | Head close-up shows a flat black rectangular bar across the front roller between the turquoise bands; please check against the references. Product-fidelity against reference photos was **not** judged by QA. | `head-closeup.png` |
| D11 | Low | lead | Console warning on every load: `THREE.Clock: This module has been deprecated. Please use THREE.Timer instead.` | e2e console attachments |
| D12 | Info | interaction-designer | Pressing the stage far from the head makes the head glide to the pointer **with suction on**, so it cleans everything on its way (in the first capture attempt it removed a whole hair patch before the intended stroke). This follows the "never teleport" rule, but may surprise users. | first-run observation; the capture script now uses keyboard positioning to avoid it |
| D13 | Info | lead | A quick flick that is released straight away cleans nothing: the head is speed-limited and stops on release. This follows §6.2 by design; noted because a "fast stroke" in the browser only collects if the pointer stays down. | e2e `strokes` attachment (first run: fast = 0 collected) |
| D14 | Info | lead | After the intro demo pass, a probe run read ~38 % of the intro patch still remaining (`remainingFraction` 0.38), but on screen it is a small smear mostly beside or behind the head. "Leave some mess" reads weakly. | `active-after-intro.png`, `start-transition-end.png` |

**§14.5 blocking defects:** none of the listed blocking conditions was clearly observed in these captures. Nozzle contact, connected parts, no duplicate vacuum, no snap, constant scale and no shader errors all held in the inspected frames. D2/D3 come closest ("dust looks like…" / readability). Product silhouette and colorway against the selected references were not assessed by QA (reference-director / product-modeler scope).

## 8. Not tested

Real iOS/Android devices and their performance; Firefox; DPR > 1 rendering; safe-area/notch insets and dynamic viewport height; multi-touch pinch in inspect; real OS window switching and real backgrounded tabs; audible sound output; dirt placement near play-area boundaries; a stroke that starts on the stage and passes over UI controls; screen readers.

## 9. Files

- `tests/e2e/helpers.ts`, `tests/e2e/flow.spec.ts`, `tests/e2e/cleaning.spec.ts`, `tests/e2e/robustness.spec.ts`, `tests/e2e/mobile.spec.ts` (note: `tsconfig.json` includes these files in `npm run build`'s typecheck; they typecheck cleanly).
- `scripts/qa-capture.mjs` (`npm run qa:capture`; `QA_URL` overrides the base URL, `QA_ONLY=core|viewports|perf|video` runs one section).
- `evidence/**`, `QA_REPORT.md`.

## Post-QA fixes (lead, 2026-10-05)

| Defect | Fix | Verification |
|---|---|---|
| Mobile Add dirt: head parked off-screen, body across the floor | Head now parks just beyond the far edge of the play area (mostly reverse move keeps yaw; wand trails out of frame) | 390×844 screenshot inspected |
| Dust read as paw prints / smoke puffs | simulation-engineer: single irregular domain-warped films, stroke-aligned trails | Stone/oak/carpet screenshots inspected by lead |
| Dust and hair nearly invisible on carpet | Per-surface renderer params (lighter dulling dust, wider/darker opaque hair on carpet) | Carpet screenshot inspected by lead |
| Governor rendered above display pixel ratio | Max DPR capped at `window.devicePixelRatio` | code review |
| Labels overlapping dock at 740×360 | "Independent concept" moves under the brand in active/inspect; compact centred dock on short landscape | 740×360 screenshot inspected |
| Fallback notice covering the poster's floorhead | Poster repositioned and edge-feathered into the studio colour | `?nowebgl` screenshot inspected |
| Bin preset cropped the end cap | Bin preset focus/radius adjusted | — |

After these fixes: `npm run typecheck` clean, `npm run test` 25/25, `npm run build` OK, `npm run assets:validate` OK (4 files),
`npm run test:e2e` **44/44 passed** (Chromium 153 + WebKit 26.6, 6.1 min), `npm run qa:capture` re-run (evidence/ regenerated).

Still open (not fixed): oak texture repetition at a distance (low), roller stripes crisper than V5 fibres, MultiFlex/upper-wand mouldings simplified, `THREE.Clock` deprecation warning originates inside @react-three/fiber.

## v2 product (IA3246GN Sagewood + Clean & Empty dock), 2026-10-05

Asset: `scripts/blender/v2` (floorhead / wand / handheld / dock modules + materials, built by 5 parallel agents after 2 research agents).
High 195k tris (2.70 MB meshopt), balanced 107k tris (1.97 MB), height 1.140 m = official docked height. `assets:validate` OK.
Reference comparisons: `assets/reference-comparison/v2/{floorhead,wand,handheld,dock,materials,all}/` (final full-product sheet `all/compare_full_v2.png`).

Re-run after integration: typecheck clean, `npm run test` 25/25, `npm run test:e2e` **44/44** (Chromium 153 + WebKit 26.6), `npm run qa:capture` regenerated `evidence/`.
Measured p95 frame time during a cleaning stroke (Apple M2, headless): Chromium 16.7 ms at all 5 viewports, WebKit 18 ms (one >20 ms frame at 430×932).

Known differences vs the real product (documented by the modelers): bin window reads sage-grey rather than whitish-frosted; copper band slightly browner; MultiFLEX fold stops at ~95° (manual storage fold ~180° not supported); hinge hose smaller than in photos; dock cradle interior, evacuation port and rear inferred (no clear references); underside pockets and some moulded recesses simplified; no Sagewood side/rear/top photos exist, so those surfaces use the identical-geometry IA3241/IA3246 colourways. Not tested: real phones, Firefox, retina pixel ratios.

## v3 product (IP3251, TR) + lighting overhaul + night mode — 2026-10-05

Asset: `scripts/blender/v3` (floorhead / wand / handheld / dock / materials agents, after visual + manual research agents).
High 167k tris (2.93 MB), balanced 101k tris (1.96 MB; textures re-encoded 2.84 → 0.53 MB). `assets:validate` OK (4 files).
Comparisons: `assets/reference-comparison/v3/{floorhead,wand,handheld,dock,materials}/` incl. matched-angle renders vs the user's
frames (`dock/compare_docked.png`, `handheld/compare_user.png`).
Lighting: custom softbox PMREM studio, GTAO (high tier, half-res), selective bloom, HDR MSAA post pipeline; night mode = dark room,
real SpotLights at the floorhead LED anchors (white front, violet rear), screen-ring LED driven by dirt detection.

Checks (on a fresh production build): typecheck clean, `npm run test` 25/25, `npm run test:e2e` **44/44** (Chromium 153 + WebKit 26.6).
An earlier run in this round had 2 failures that came from a stale preview server (old build) — fixed by rebuilding/restarting.
p95 frame time during a cleaning stroke (Apple M2, headless): Chromium 16.7–16.8 ms at all viewports; WebKit 18 ms on mobile sizes,
19–20 ms at 1920×1080 / 1440×900 (9 and 22 frames > 20 ms) — slightly over the 20 ms desktop target in WebKit.

Known differences: overall height ≈2.8% tall (handle tip vs spec, see DECISIONS.md); dock plinth smooth per photos (EUIPO shows fluting);
filter door on the right side; screen icon layout uses manual variant A (official TR photo shows variant B — user close-up needed);
headlight housings simplified (no inner chamfer/amber parts); some underside/yoke details inferred. Not tested: real phones, Firefox, retina DPR.

## v3 rework after user review (2026-10-05, evening)

User rejected the floorhead/handheld as "not identical" (screenshot of the app head vs their frames). Rework:
- Research: +150 close-up frames (89 head, 61 handheld) from ~18 videos incl. the 25-min Turkish unboxing; screen icon layout confirmed from the
  TR unit's shipping film (atlas rebuilt).
- Floorhead rebuilt with camera-solved (OpenCV) 50% overlays against cl-eut-01 front (4 px mean error), pdp DuoCleanDetect 3/4 (6 px), user 1663 (11 px),
  crop-tr01 (22 px): one continuous clear cover, front black/teal brush behind the clear bumper, badge on the cover's front face, 3-chip LED corner
  pockets, violet strip + rear LEDs, dark 'Koyu Gri' body (#45464a), Ø35 neck disc (measured; user's "smaller" request contradicted the photos).
- Handheld: chunky matte-black grip (37×32 mm), charcoal grip neck/flare, 18 broad cap flutes, screen face radius 38.5 mm with measured LED ring,
  MAX line; camera-solved overlays vs user 1663/1668.
- Runtime materials: clear cover/bin blend like glass (reflections not scaled by opacity, grazing-angle opacity), black front roller.
Checks on a fresh build: typecheck clean, unit 25/25, e2e 44/44. Sheets: assets/reference-comparison/v3/{floorhead,handheld}/overlay_*.png.
Open: handle rear-upright width (no straight top/rear photo), body rear vent grid not modelled, roller-V direction ambiguity between sources.
