# v3 parts contract — Shark PowerDetect Clean & Empty IP3251 (TR 'mor-siyah': gunmetal + purple, bronze wand, white dock)

Lead-owned. Part agents read this before writing code. Changes to anything in this file or `params.py` go through the lead.

## Files and ownership

| File | Owner | Purpose |
|---|---|---|
| `lib.py` | lead | geometry helpers (mk, lathe, loft_up, sweep, extrude, rrect, fillet, catmull, bevel, empty, set_parent, ...) |
| `params.py` | lead | **interface** dimensions only (pivots, axes, interface planes, overall size, dock placement) |
| `materials.py` | materials agent | `make_materials(tier) -> None` fills `lib.MATS` with the names below; textures/decals |
| `parts/floorhead.py` | floorhead agent | DuoClean Detect floorhead: turquoise soft front roller (RollerFront), rear brushroll (RollerRear), clear cover, violet LEDs, wheels, neck up to `WAND_SOCKET_UP` |
| `parts/wand.py` | wand agent | everything from `WAND_SOCKET_UP` up to `HANDHELD_BOTTOM_UP`: lower collar + nozzle-release button, bronze wand tube, MultiFLEX hinge (purple discs), upper wand |
| `parts/handheld.py` | handheld agent | handheld from `HANDHELD_BOTTOM` up: bin, cyclone, motor, cap, display, handle, battery, trigger |
| `parts/dock.py` | dock agent | Clean & Empty base: white tower + round display, dark base plate, charging post + cradle cup |
| `assemble.py` | lead | calls parts, builds rig hierarchy, exports GLBs + rig.json |
| `preview.py` | lead | renders one part (or all) from standard views for comparison |

Each part file may keep its own private dimension constants at the top (a local ledger with source/status comments).
Never edit another agent's file. Shared needs → message the lead.

## Coordinates

Product coords `(x, up, fwd)` meters. Floor `up = 0`. `x` = product right when looking at the front.
`fwd` = toward the floorhead front. Origin = centre of the floorhead intake footprint (VacuumRoot).
Use `lib.V(x, up, fwd)` to get Blender vectors (Blender Z-up, front = -Y). Build everything in the **upright,
docked rest pose** (wand vertical, fold straight). The dock is built in the same frame, around that docked pose.

## Part API

```python
def build(ctx) -> dict
```
`ctx = {"tier": "high"|"balanced", "P": params module, "lib": lib module}`. Materials are already created
(`lib.MATS`); pass material **names** to helpers. Return:

```python
{
  "groups": {"FloorHead": [...], "LowerWand": [...], "UpperWand": [...], "MotorAssembly": [...], "Dock": [...]},  # only your groups
  "special": {  # separately animated / runtime-addressed meshes (floorhead / handheld agents)
     "RollerFront": obj, "RollerRear": obj,       # floorhead: spin axis = product X through the object origin
     "HeadLights": [objs],                         # floorhead: emissive LED meshes (joined by assembler)
     "DustbinShell": obj, "DustbinContents": obj,  # handheld: origin of contents at bin floor; runtime scales Y
     "Display": [objs],                            # handheld: emissive display/indicator meshes (optional)
     "DockLights": [objs],                         # dock: emissive indicator meshes (optional)
  },
  "anchors": {"PowerControlAnchor": (x,up,fwd), "IntakeFront": ..., "IntakeRear": ...},
  "contacts": {"Contact_*": (x, 0, fwd)},          # floorhead
  "nozzle": {"intakeWidth":..,"intakeZMin":..,"intakeZMax":..},  # floorhead, head-local fwd values
  "notes": "free text"
}
```

Group meaning (all meshes in product coords; the assembler re-parents preserving world transforms):
- `FloorHead`: never tilts. `LowerWand`: rotates about `NECK_PIVOT`. `UpperWand`: rotates about `FOLD_PIVOT`.
  `MotorAssembly`: rigid with UpperWand (child). `Dock`: separate top-level `DockRoot`, never moves.

## Material names (fixed)

`M_Gunmetal` (main grey/gunmetal body plastic), `M_Charcoal` (near-black/dark-grey plastic: handle, battery, collars, head body),
`M_Purple` (purple ribbed cap, bin ring, hinge discs, accents), `M_Bronze` (bronze/champagne anodized metal wand),
`M_Champagne` (champagne 'POWERDETECT' label plate), `M_SilverBrush` (brushed silver bin frame / trims),
`M_ClearBin` (clear bin), `M_ClearCover` (head clear cover), `M_Chrome` (cyclone mesh, screws),
`M_Turquoise` (soft roller fabric / turquoise accents), `M_RollerFibre` (yellow fibre stripe if separate), `M_White` (dock tower),
`M_Rubber`, `M_Bristle`, `M_Hose`, `M_Screen` (glossy black screen glass), `M_LED` (floorhead WHITE front headlights, emissive), `M_LEDAccent` (VIOLET rear-corner LEDs + strip behind the roller window, emissive),
`M_LEDRing` (handheld screen ring, emissive purple/white), `M_DockDisplay` (dock round display icons, emissive),
`M_Decal` (marking atlas, alpha), `M_Dust`.
If you need another, ask the lead (the materials agent adds it).

## Quality bar

Real silhouettes from profiles/lofts/sweeps; bevels on every hard edge that catches light (0.4–2 mm);
modelled holes, vents, grilles, seams (0.4–0.8 mm gaps), screws, buttons, lights where visible in references.
Budgets: whole product high ≤ 260k tris, balanced ≤ 110k tris (dock included). Use `lib.D` detail values so the
balanced tier is automatically lighter. No n-gon artifacts: check shading in renders.

## Verify your part

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/blender/v3/preview.py -- --part <name> [--tier high]
```
writes `assets/reference-comparison/v2/<part>/<view>.png` (front, back, left, right, top, bottom, 3/4 L/R, close-ups).
Open them with the Read tool and compare against the references side by side (make PIL comparison sheets).

## Decals (markings)

The materials agent publishes `scripts/blender/v3/decals.json` + `assets/source/textures/v3/decal_atlas.png`
(expected slots: "Shark" (bin frame, neck plate), "POWERDETECT" (champagne plate), "duoclean DETECT" (head cover plate),
screen icons, dock display icons). Decal plates = separate thin meshes with `M_Decal`, 0.2–0.3 mm off the surface,
UVs via `materials.decal_uv(slot, s, t)`. `materials.ensure_uvs()` box-projects UVs for meshes without UVs.

## Lights (runtime)

Every emissive mesh must use `M_LED` (head violet LEDs), `M_LEDRing` (screen ring) or `M_DockDisplay` (dock display) so the
app can drive them. The floorhead also returns anchors `LightFrontL`, `LightFrontR`, `LightRearL`, `LightRearR` (where the
violet LEDs sit, pointing at the floor) — the app attaches real SpotLights there for the night mode.
