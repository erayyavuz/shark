# Shark PowerDetect — interactive 3D concept

An independent, client-side product playground built around a reconstructed 3D model of the
**Shark PowerDetect Clean & Empty IP3251 (Turkish IP3251EUT)**, including its auto-empty dock. The visitor sees the product
docked in a studio composition, presses **Start**, and the stick leaves the dock onto a playable floor where they make a mess
and guide the vacuum over it.

**Live:** https://shark-powerdetect.try2.app/

> **Unofficial fan concept.** Not affiliated with, sponsored or endorsed by SharkNinja. "Shark", "PowerDetect", "DuoClean" and the
> product markings shown on the 3D model are trademarks of SharkNinja Operating LLC and are used here only to depict the product.
> The 3D model is an independent procedural reconstruction (no manufacturer CAD). No backend, accounts, purchase flow or runtime AI services.
> Reference photographs, manuals and video frames used during modelling are copyrighted by their owners and are not included in this repository.

## Requirements

- Node 22+ and npm
- Optional, only for rebuilding the 3D asset: Blender 5.2 (`/Applications/Blender.app` or set `BLENDER_BIN`)
- Optional, only for regenerating floor textures: Python 3 with numpy + Pillow

## Commands

```bash
npm install
npm run dev              # local dev server (prints its URL, e.g. http://127.0.0.1:5173/)
npm run build            # typecheck + production build into dist/
npm run preview          # serve dist/ locally
npm run typecheck
npm run test             # vitest: simulation, motion, timeline
npm run test:e2e         # playwright: browser flows (Chromium + WebKit; builds + previews automatically)
npm run assets:build     # rebuild GLBs from scripts/blender/v3 (needs Blender + Python Pillow)
npm run assets:validate  # check node names, hierarchy, contact anchors, budgets
npm run qa:capture       # regenerate the evidence/ screenshots
python3 scripts/textures/make_floors.py   # regenerate floor textures
```

The shipped `public/models/*.glb` let the site run without Blender installed.

## Controls

| Action | Mouse / touch | Keyboard |
|---|---|---|
| Start | Start button right of the product | Tab to it, Enter / Space |
| Clean | Drag on the floor; the head follows with realistic speed limits. Grab the head to keep its offset, or press elsewhere and it glides under your pointer. | Focus the floor (Tab), arrows move, hold Space to vacuum |
| Add dirt | Add dirt → pick Dust / Hair / Pet hair / Crumbs / Mixed and Light / Medium / Heavy; tap scatters, drag paints | A |
| Back to cleaning | Clean | C |
| Make a mess / Clear floor | Toolbar (mobile: Floor drawer for Clear floor) | Tab + Enter |
| Floor | Oak / Stone / Carpet (keeps the mess) | Tab + Enter |
| Inspect | Eye icon; drag to orbit, wheel / pinch to zoom; Full / Head / Bin presets; Done | Esc exits |
| Sound | Speaker icon (off by default; synthesized) | |
| Night | Moon / sun icon (hero top-right and in the view controls): dark room lit by the product's own LEDs (white headlights, violet rear LEDs, screen ring) | |
| Back | Arrow icon: returns to the product view and clears the session mess | |

Debug counters: append `?debug` to the URL (development aid, not part of the experience).
Other dev flags: `?proxy` (primitive stand-in rig), `?model=high`, `?nowebgl` (forces the fallback), `?post=off|noao|nobloom`.

Note: `npm run test:e2e` reuses a server already listening on :4173 — rebuild/restart `npm run preview` first so it tests the current build.

## Project layout

| Path | Contents |
|---|---|
| `src/app` | Experience orchestrator (state machine, single loop), zustand UI store, timeline, perf governor |
| `src/contracts` | Shared types, coordinate + rig contracts (meters, Y-up, head-local +Z = front) |
| `src/scene` | Studio lighting, floor shader, camera director, lookdev (materials, floor surfaces) |
| `src/product` | GLB loading (with truthful byte progress), rig adapter, dev proxy |
| `src/simulation` | Dust field, hair strands, pet-hair clumps, crumbs, swept pickup, accounting, renderers |
| `src/interaction` | Pointer/keyboard mapping, damped motion controller |
| `src/ui` | Overlay UI, icons, styles |
| `src/audio` | Single managed Web Audio graph |
| `scripts/blender/v3` | Current asset (IP3251): `PARTS_CONTRACT.md`, `params.py` (interfaces), `parts/{floorhead,wand,handheld,dock}.py`, `materials.py` + `decals.json`, `assemble.py`, `preview.py`. Earlier targets: `v2/` (IA3246GN Sagewood), `build_powerdetect.py` (v1 IP1251) |
| `assets/source` | Editable `powerdetect-v3.blend`, textures (`textures/v3/`, decal atlas) |
| `assets/references` | Reference photos (reference only, not shipped) + manifest + contact sheet |
| `assets/reference-comparison` | Reference vs render comparison sheets |
| `evidence/` | QA screenshots and reports |

See `PRODUCT_REFERENCE_IP3251.md` and `TECHNICAL_REFERENCE_IP3251.md` for what is observed vs inferred on the model, `DECISIONS.md` for settled choices,
`QA_REPORT.md` for measured results and `ASSET_CREDITS.md` for asset provenance.

## Hosting later

`npm run build` produces a static `dist/` folder (no server code). Serve it from any static host at the site root.
