# v2 parts contract — Shark PowerDetect Speed Clean & Empty (IA3246GN, Sagewood)

Lead-owned. Part agents read this before writing code. Changes to anything in this file or `params.py` go through the lead.

## Files and ownership

| File | Owner | Purpose |
|---|---|---|
| `lib.py` | lead | geometry helpers (mk, lathe, loft_up, sweep, extrude, rrect, fillet, catmull, bevel, empty, set_parent, ...) |
| `params.py` | lead | **interface** dimensions only (pivots, axes, interface planes, overall size, dock placement) |
| `materials.py` | materials agent | `make_materials(tier) -> None` fills `lib.MATS` with the names below; textures/decals |
| `parts/floorhead.py` | floorhead agent | TurboPro Detect floorhead, brushroll, lights, wheels, neck up to `NECK_PIVOT` |
| `parts/wand.py` | wand agent | everything from `NECK_PIVOT` (exclusive of head neck yoke) up to `HANDHELD_BOTTOM`: lower collar, copper wand, MultiFLEX hinge, upper wand |
| `parts/handheld.py` | handheld agent | handheld from `HANDHELD_BOTTOM` up: bin, cyclone, motor, cap, display, handle, battery, trigger |
| `parts/dock.py` | dock agent | Clean & Empty base, placed around the docked vacuum |
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

`M_Sage` (main sagewood body, satin), `M_SageDeep` (darker sage/graphite-green trims), `M_Graphite` (near-black green-grey
plastic), `M_Copper` (anodized copper metal wand), `M_CopperSatin` (copper-tone plastic/painted accents),
`M_CopperBrush` (brushroll copper bristle/fin surface), `M_ClearBin` (clear bin), `M_ClearSmoke` (smoked clear cover/windows),
`M_Chrome` (bright metal: cyclone shroud/mesh, screws), `M_Rubber`, `M_Bristle`, `M_LED` (white emissive),
`M_LEDAccent` (coloured indicator emissive), `M_Screen` (glossy black display glass), `M_Decal` (logo/marking atlas, alpha),
`M_Hose`, `M_Dust`.
Added by the materials agent: `M_SilverBrush` (brushed silver band / satin metal trims), `M_PlateGrey` (darker brushed-grey
'Shark' plate on the handheld front), `M_LEDRing` (handheld UI-screen LED ring + light bar; runtime switches white/purple).
`M_LED` = icy blue-white headlight emission, `M_LEDAccent` = the blue 'Reveal' light.
If you need another, ask the lead (the materials agent adds it).

## Decals (markings)

Atlas `assets/source/textures/v2/decal_atlas.png`, layout `scripts/blender/v2/decals.json` (Blender UV, origin bottom-left,
`ink` = tight letter box). Decal plates = separate thin meshes with `M_Decal`, 0.2–0.3 mm off the surface, UVs mapped to the
slot's ink rect (use `materials.decal_uv(slot, s, t)` → (u, v) for s,t ∈ 0..1 across the ink box). Slots: `pds_wand_white`
(wand), `pds_band_dark` + `shark_white` + `display_icons` (handheld), `shark_neck` + `turbopro_detect` (floorhead).
`materials.ensure_uvs()` box-projects UVs (50 mm tiles) for meshes without a UV layer; assemble/preview call it.

## Quality bar

Real silhouettes from profiles/lofts/sweeps; bevels on every hard edge that catches light (0.4–2 mm);
modelled holes, vents, grilles, seams (0.4–0.8 mm gaps), screws, buttons, lights where visible in references.
Budgets: whole product high ≤ 260k tris, balanced ≤ 110k tris (dock included). Use `lib.D` detail values so the
balanced tier is automatically lighter. No n-gon artifacts: check shading in renders.

## Verify your part

```
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/blender/v2/preview.py -- --part <name> [--tier high]
```
writes `assets/reference-comparison/v2/<part>/<view>.png` (front, back, left, right, top, bottom, 3/4 L/R, close-ups).
Open them with the Read tool and compare against the references side by side (make PIL comparison sheets).
