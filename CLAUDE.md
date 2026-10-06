# Shark PowerDetect — Interactive 3D Product Experience

Master spec: `SHARK_POWERDETECT_OPUS_5_5_MASTER_BRIEF.md` (read it fully before editing). User updates in Turkish; site copy English.

## Priority order
1. Product identity, geometry, materials, photographic lighting
2. Convincing floor contact + spatially correct cleaning
3. Continuous transition hero → interaction
4. Clear mouse/touch/keyboard controls, minimal UI
5. Stable performance, maintainable code

## Settled decisions (see DECISIONS.md)
- SKU (user-selected 2026-10-05, supersedes IP1251EUT): **IA3246GN — Shark PowerDetect Speed Clean & Empty, Luxe Collection, Sagewood** (with auto-empty dock). Sage body, copper wand/accents, clear bin with copper cyclone, TurboPro Detect head with copper brushroll. References: PRODUCT_REFERENCE_IA3246GN.md, TECHNICAL_REFERENCE_IA3246GN.md. User demand: exact ('birebir') realistic replica incl. lights, holes, markings.
- v2 asset pipeline: scripts/blender/v2/ (PARTS_CONTRACT.md, parts/*.py per agent, assemble.py, preview.py).
- Stack: Vite 8 + React 19 + TypeScript 7 + three 0.186 + @react-three/fiber 9 + zustand 5. No drei/GSAP (own small timeline). Vitest + Playwright.
- Asset: procedural Blender 5.2.2 build script (`scripts/blender/build_powerdetect.py`), Blender at `/Applications/Blender.app/Contents/MacOS/Blender` (override with `BLENDER_BIN`).
- Coordinates: meters, Y-up, floor y=0. Contracts in `src/contracts/*` (lead-owned).
- No backend, no runtime AI/paid services, no purchase flow, no invented performance figures. One small “Independent concept” label.

## Agent policy
- Custom agents in `.claude/agents/*.md`, all `model: inherit` (parent session: Opus 5.5).
- Ownership: reference-director → PRODUCT_REFERENCE.md, assets/references; product-modeler → scripts/blender, assets/source, public/models, assets/manifest.json, assets/reference-comparison; simulation-engineer → src/simulation, tests/sim*; lookdev-artist → src/scene/lookdev*, public/textures; interaction-designer → src/interaction, src/ui, src/audio; visual-qa-engineer → evidence/, QA_REPORT.md (reports only).
- Lead owns package.json, lockfile, src/contracts, src/app, root scene, integration.
- Max 3 concurrent workers. One Blender writer, one browser-capture owner at a time.

## Verification
Builds passing is not validation. Every visual change must be checked by real browser screenshots that are opened and inspected. Never claim photorealism / 60 fps everywhere / exact CAD accuracy.
