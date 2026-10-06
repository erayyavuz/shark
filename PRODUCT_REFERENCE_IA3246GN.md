# PRODUCT REFERENCE — Shark PowerDetect Speed Clean & Empty, Luxe Collection, Sagewood (IA3246GN)

Owner: reference-director · v2 (2026-10-05) · supersedes nothing (old `PRODUCT_REFERENCE.md` = IP1251EUT, kept untouched).
Image pack: `assets/references/ia3246/` → `raw/` (113 stills), `video/` (13 official mp4), `frames/` (245 extracted frames), `sheets/` (5 labelled contact sheets), `manifest.json` (URL, date, sha256, colourway, what it shows for every file).
**Usage: reference only. SharkNinja / Amazon / RTINGS copyright. Never ship these files or derived textures in the app.**
Technical data (manual, patents, part numbers) is covered by `TECHNICAL_REFERENCE_IA3246GN.md` (other agent) — not duplicated here.

Status vocabulary: **O** = observed in a Sagewood image · **O*** = observed on a sibling colourway (same geometry, colour differs) · **I** = inferred · **C** = conflicting sources.
Reference IDs = file stem in `assets/references/ia3246/raw|frames` (e.g. `snuk-gn-01`, `rt-ia3241-build-quality`, `vid-luxemoe-f082`).

---

## 0. Identity, colourways, what is and is not Sagewood

| Item | Finding | Status |
|---|---|---|
| Product family | IA3241 (Ice Blue, non-Luxe), IA3246 Luxe = GN Sagewood / BL Harbor Slate / BR Walnut / IV Oatstone; UK IA3246UKTGN etc. One geometry, finishes differ. | O (official Cloudinary tag lists) |
| Sagewood-only images available | `snuk-gn-01` (UK front render, cleanest), `sn-gn-hero` (US front render), `snuk-gal`/`sn-gal1` (real-world lifestyle photo, side), `vid-luxemoe-f001…f010` (docked in green room), `vid-luxemoe-f100…f114` (lineup, far left), `vid-luxecolors-*` last segment, `vid-5050colors-*` last segment. | O |
| Amazon B0GTC1N9RV | As fetched it resolves to **IA3241 Ice Blue**; its variation set is Frosted Sage / Walnut / Ice Blue / Oatstone / Harbor Slate. **No Sagewood on Amazon.** "Frosted Sage" = **IA3243 Speed Plus** (different SKU: silver wand, black head, FurFins tool) — do NOT use for Sagewood colour. | C (user said B0GTC1N9RV = Sagewood) |
| Wand finish per colourway | Sagewood = copper; Oatstone = champagne gold; Walnut = copper/bronze; Harbor Slate = silver; Ice Blue IA3241 = steel-blue. | O |
| Floorhead roll colour | Luxe (all 4) = copper/terracotta matte; IA3241 = bright orange. Real photos of the underside exist only for IA3241 (orange). | O / O* |
| Head chassis colour | Sagewood renders: very dark green-charcoal; Sagewood photo `snuk-gal`: near-black. Neck plate on Luxe = body colour family (dark sage on GN). | O, slight C (render vs photo) |

## 1. Official / measured dimensions

| Quantity | Value | Source |
|---|---|---|
| Docked, H x W x D | 44.88 in H x 10.24 in W x 14.76 in L = **1140 x 260 x 375 mm** | sharkninja.com IA3246GN specs (saved PDP HTML) + Amazon "Item Dimensions" (same) |
| Docked, measured | **113.8 cm H x 26.1 cm W x 38.2 cm D** | RTINGS lab (IA3241) |
| UK callout | 114 cm H, 37.5 cm L | `snuk-gal5` |
| US callout | 44.9" H, 14.8" L | `sn-gal5` |
| Weight listed | 14.2 lb (6.44 kg) — stick + dock | sharkninja.com, Amazon |
| Stick weight | 7 lb (official "lightweight at 7 lbs"); RTINGS 3.25 kg (7.16 lb) | official / RTINGS |
| Handheld weight | 3.5 lb official; RTINGS "in hand" 1.50 kg | official / RTINGS |
| Cleaning path | 8.3 in = 211 mm (≈ brushroll visible length, see §2) | official |
| Dust cup | 0.5 qt (0.47 L); dock+cup total RTINGS 2.30 L; dock "2L Auto-Empty Dock, up to 45 days" | official / RTINGS / `snuk-3241ukt-12` |
| W = floorhead width | 260 mm (spec) / 261 mm (RTINGS) | I (high confidence: front-view head width matches) |
| L = head front bumper → dock rear | 375–382 mm | I (callout bar in `sn-gal5`/`snuk-gal5` spans head front → dock rear) |

**Global frame for modelers:** metres, Y-up, floor y = 0, product front (head bumper, display faces away) toward +Z, docked unit centred on X = 0.

## 2. Front-view station table (docked, `snuk-gn-01`, near-orthographic)
Scale: floor y=1945 px, top of handheld y=121 px → 1824 px = 1140 mm → **1.600 px/mm** (vertical). Horizontal widths are reliable to ~±3 % above the dock, but the floorhead front is ~4.6 % magnified by perspective (render head 273 mm vs real 261 mm) — scale head widths by 0.955.

| Height above floor (mm) | Silhouette width (mm) | What it is |
|---|---|---|
| 1140 → 1095 | 63 → 87 (rounded dome) | Handheld rear end (display face points up/back; seen from its top side) |
| 1095 → 870 | 87 constant | Handheld cylinder: charcoal "Shark" label panel, metal-look band, copper filter ring, clear bin window |
| 1001 → 870 | central 36 mm see-through | Clear bin window with cyclone/shroud visible inside |
| 866 → 806 | 102–104 | **Dock top cradle** (U-saddle) gripping handheld nose |
| 806 → 765 | 104 → 60 taper | Cradle neck flaring into dock post |
| 765 → 514 | 58–63 | Dark upper wand coupling + MultiFlex hinge + top of copper wand, with sage dock post visible as thin strips both sides |
| ≈ 650 (hinge axis) | hinge knuckle ~62 wide | MultiFlex hinge, copper side caps |
| 510 → 491 | 66 → 164 (radiused shoulder, R ≈ 20) | Top of dock tower |
| 491 → ≈190 | 164 → 171 | Dock canister (upper, body colour) |
| ≈ 195 | thin light ring | Seam ring between canister and plinth |
| ≈190 → 0 | ≈171 (+ foot plate) | Dock plinth (darker) ; foot plate under head |
| 94 → 75 | 196–201 | Floorhead rear wheels / hood seen behind bumper |
| 75 → 0 | 261 (corrected) | Floorhead front (clear cover, bumper) |

Other front-view features (px→mm with 1.6 px/mm, from `sn-gn-hero` scale 1.559): copper wand face width **35 mm**; visible copper wand length above lower coupling ≈ **290 mm** (rest hidden by hinge); copper filter ring band **35 mm** tall; floorhead-neck copper disc **⌀ 34–37 mm**; neck "Shark" plate ≈ 95 mm wide.

## 3. Flat-lay part sizes (RTINGS `rt-ia3241-in-the-box`, top-down; scale = floorhead 261 mm; ±5 %, thick parts read slightly large)
| Part | Size (mm) |
|---|---|
| Handheld (rear end → nozzle tip), without battery | ≈ 368 long, ≈ 240 tall incl. pistol grip |
| Battery pack (slides in front of grip, under body) | ≈ 151 x 82 |
| MultiFlex wand assembly (upper coupling → lower coupling, incl. hinge) | ≈ 640 long |
| Crevice tool | ≈ 354 long |
| Floorhead body depth (front lip → rear of chassis) | ≈ 103–106 ; with neck + rear wheels ≈ 170 |
| Dock canister (removable debris container) | ≈ 181 wide x 337 tall |
| Dock post (lower duct column) | ≈ 74 wide x 433 long incl. ⌀≈28 top spigot |
| Dock cradle piece (top, with yellow "Wait until evacuation completes…" label) | ≈ 160 wide at saddle x 383 long |
| Dock base (plinth + foot plate) | foot plate ≈ 394 long ; plinth ≈ 170–190 tall |

Underside (RTINGS `rt-ia3241-build-quality`, orthographic bottom view, 5.29 px/mm on the 2000-px display): brushroll visible length **≈ 215 mm**, roll ⌀ **≈ 45–50 mm**; rear wheels **⌀ ≈ 48 mm, ≈ 18 mm wide**; front corner rollers ≈ 11–12 mm; coin-lock knobs ⌀ ≈ 14–17 mm; floor-type optical sensor ⌀ ≈ 6 mm.

---

## 4. FLOORHEAD — TurboPro Detect (modeler A)
Best refs: front `snuk-gn-01` crop (sheet F1), `sn-gal2`/`snuk-gal2` (front close, real-looking render), **underside `rt-ia3241-build-quality`**, right end + LED `amz-harbor-slate-ia3246bl-main-71OzdgVntlL` (sheet F4), left side Sagewood `snuk-gal` (F5), `vid-luxemoe-f082…f098` (front, neck, LED), `vid-luxemoe-f118` (end cap + LED), `sn-IA3000_Series_PowerDetect_Carousel_PDP*` (3/4 top, louvres), flat-lay top `rt-ia3241-in-the-box`. Sheet: `sheets/sheet-floorhead.jpg`.

Overall: 261 W x ≈105 D (body) x ≈60–65 H (I; front-view 70 mm includes top surface in perspective). Box-like bar with rounded end caps; neck yoke in the middle-rear; two large rear wheels behind the bar either side of the neck.

| Feature | Position / shape / size | Colour & finish | Count | Refs | Status |
|---|---|---|---|---|---|
| Clear brushroll cover (front window) | Spans almost full width between end caps, wraps the front-top quadrant; flat-ish front face with soft top radius | Clear PC, very slightly grey/smoke tint, high gloss; edge highlights | 1 | F1, `sn-gal2`, `vid-luxemoe-f086` | O |
| "TURBOPRO DETECT" print | Left part of cover front, lower-middle; "TURBO" regular + "PRO" bold italic + "DETECT" regular, italic sans | White print on clear | 1 | F1, `sn-gal2` | O |
| Front comb / clear lip | Bottom front edge, transparent strip ≈15 mm deep with comb teeth pointing into roll | Clear | **10 teeth**, 4 screw bosses (round, visible through clear) | `rt-…build-quality`, F1 (10 small tabs visible along bottom) | O* |
| Brushroll | ⌀ ≈ 47 mm, length ≈ 215 mm; rubber herringbone fins forming a **V/chevron with apex at centre**, plus one dark bristle strip following the V | Luxe: copper/terracotta matte rubber (#724d3e–#804c3a seen through cover; photo ~#9b6145 lit); bristles near-black brown | fins: 4 chevron fins + 1 bristle row (I from IA3241 underside) | F1, F3, F11 | O / O* |
| End caps L & R | Rounded-rectangle side blocks, dark | Very dark green-charcoal (#3c413d family) satin | 2 | F4, F5 | O |
| Side hub disc | Large round disc on each end-cap outer face (≈ 55–60 % of cap height) | GN: **copper** satin-metallic (photo F5); BL: pale grey | 2 | F5 (Sagewood copper), F4 | O |
| Right-end dot grid | Vertical strip of small round perforations/printed dots at right end, between cover and cap, halftone fading toward top | Dark with light/blue dots | ~3 columns x ~12–14 rows (C: render-dependent) | F1, F4, `sn-gal2` | O |
| Headlight (Reveal) LED | **Single** LED at the **front-right corner, low**, in a small square black housing (~15 x 20 mm) with round lens ⌀≈8 mm; emits blue-white beam angled forward-down across the floor | Lens white/clear; emission blue (≈ #4aa8ff glow, white core) | **1** (right side only) | F1, F4, F6, F8, `vid-luxemoe-f066…f073` | O |
| Blue accent strip | Thin vertical blue edge on the right end beside LED housing | Saturated blue (#2a8fd6 approx), gloss | 1 | F1, `sn-gal2` | O |
| Top hood louvres | Horizontal ribs on top rear hood, left and right of neck | Head colour, satin | ≈ 6–8 ribs per side (I) | F10, F12 | O* |
| Neck yoke + "Shark" plate | Raised trapezoid plate on hood centre, "Shark" logo printed/embossed, ≈95 mm wide | Sagewood: dark sage/charcoal (#60635a); logo light grey | 1 | F1, `sn-gal2` | O |
| Neck swivel with copper disc | Round boss ⌀ ≈ 35 mm on neck front, face = copper with **concentric/radial brushed (spun) finish** | Copper metallic #865d47 (shade) → #c99f88 (lit) | 1 | F1, F2, F8 | O |
| Neck release button | Rounded-rectangle (stadium) button above the copper disc on the lower wand coupling | Body colour, framed by dark outline | 1 | F2, W2 | O |
| Corrugated hose | Short black ribbed hose inside neck/yoke (visible from rear/top and when bent) | Black, semi-gloss | 1 | F4, F12, `snuk-gal` | O |
| Rear wheels | ⌀ ≈48 x 18 mm, behind bar either side of neck; outer face has **radial fine-line pattern** + small silver centre cap | Black rubber; hub dark grey | 2 | F3, F5 (radial pattern) | O |
| Front corner rollers | Small rollers at each front corner underside | Black | 2 | F3 | O* |
| Underside plate | Diagonal chevron ribs across plate behind roll opening; 3 coin-slot twist locks (L, centre, R) for roll access; arrow/lock icons moulded | Black/charcoal ABS matte (#474949) | ribs ≈ 11 (5 + centre + 5) ; locks 3 | F3 | O* |
| Floor-type optical sensor | Small white round window left of neck on underside | White/opal | 1 | F3 | O* |
| Screws visible | Underside around wheel axles + clear lip | Black/silver Phillips | ≈ 4 (axle area) + 4 (lip) | F3 | O* |
| Parting lines | Cover-to-chassis seam along top; end-cap seams vertical; neck plate perimeter | — | — | F1, F4 | O |

## 5. HANDHELD (modeler B)
Best refs: Sagewood front render crop `snuk-gn-01` (H1), Sagewood photo side `snuk-gal` (H2), **rear display `rt-ia3241-controls`** (H3), full side `rt-ia3241-alternative-configuration-1` (H4), side profile `snuk-3241ukt-07` (H6), 3/4 rear `amz-harbor-slate…main` (H12), flat-lay `rt-ia3241-in-the-box` (H11), filters `rt-ia3241-recurring-cost`, video `vid-luxemoe-f035…f039`, `f074…f079`. Sheet: `sheets/sheet-handheld.jpg`.

Architecture (O): a horizontal cylinder (motor + cyclone + filter) along the airflow axis; nozzle/inlet at the front (connects to wand), **round display at the rear end face**; clear bin hangs below the front half of the cylinder; pistol grip loops down-and-back from the rear underside; battery pack slots in vertically in front of the grip under the cylinder. In the dock the unit stands nozzle-down: you see the cylinder's top side with the "Shark" panel, copper ring and bin window facing the viewer; the grip and display face up/rearward toward the dock post.

| Feature | Position / shape / size | Colour & finish | Count | Refs | Status |
|---|---|---|---|---|---|
| Main cylinder shell | ⌀ ≈ 87 mm (front-view width), rounded rear dome | Sagewood satin plastic (#6c6f66 render shade → #77786f; photo #5a5f58 shade) | — | H1, H2 | O |
| Label panel | Rear third of top side, rounded-rect inset, "Shark" white wordmark, fine vertical brushed texture | Dark grey-charcoal metallic-look (#787c7a render) | 1 | H1, H2 | O |
| "POWERDETECTSPEED" band | Below label, light silver band ≈ 10 mm; "POWER" bold + "DETECT" light + "SPEED" bold italic, dark text | Satin silver | 1 | H1 | O |
| Copper filter ring | Ring band ≈ 35 mm tall seen through/around the cylinder: fine vertical ribs (knurl), it is the copper rim of the removable cylindrical pleated filter | Copper metallic, rib knurl: ≈ 60–70 ribs around (I) | 1 | H1, H10, H11 | O |
| Clear bin + cyclone window | Front-top of cylinder transparent (bin), shows grey shroud with mesh dome (perforated cone) and curved inlet duct | Clear PC with slight cool tint; internal parts light grey translucent | 1 | H1, H5 | O |
| Bin (lower) | Clear box below cylinder front, angular stepped sides, black bin-door latch at front-bottom, yellow-green release tab (IA3241) | Clear, slight blue tint (Sagewood photo) | 1 | H2, H5, H6 | O |
| Exhaust grille | Near rear end on each side of cylinder top-rear: parallelogram recessed panel of slots split by one centre bar | Through-slots, dark inside | **2 rows x ≈ 13–15 slots** per side (Sagewood photo shows 2 columns of ≈13) | `snuk-gal` vent crop, `rt-…alternative-configuration-1` | O (count ±2) |
| Ribbed side panel next to bezel | Curved band of ≈ 14 parallel ribs/slots beside display bezel | Body colour | ≈14 | H3 | O* (C: may be same exhaust grille) |
| Rear display | Round face ⌀ ≈ 70 mm (I) black glass, **satin silver bezel ring** ≈ 6 mm | Glass gloss #171815; bezel satin aluminium-look | 1 | H3 | O* |
| Display content (lit) | Top: PowerDetect icon (dot + 3 concentric rings); outer **arc gauge ≈ 240°** (power/suction level); horizontal **battery bar** under centre; **battery+bolt icon** below bar | Emissive light ice-blue (#8ebdd7–#b2d3ec, peak near white) on black | arc 1, icon 1, bar 1 | H3 | O* |
| Buttons | Two soft buttons at the bottom of the display face: **left = power ⏻, right = boost/fan (4-blade) ✣**, trapezoid split pair | Dark grey soft-touch #3c3d37, white icons | 2 | H3 | O* |
| Pistol grip | Loop handle under rear; grip zone wrapped in black rubber/soft-touch; frame body colour | Grip near-black matte; frame sage | 1 | H2, H4 | O |
| Trigger | None — power is the button on display (no trigger seen in any image) | — | 0 | H3, H4 | I |
| Battery pack | Vertical slab in front of grip under cylinder, outer face = recessed dark panel with "Shark" wordmark, ≈151 x 82 | Charcoal panel #3c… with silver/grey "Shark", frame body colour | 1 | H2, H4, H12 | O |
| Wand release button (handheld nose) | Stadium button on top of nozzle neck | Body colour w/ dark outline | 1 | H4, `sn-gn-hero` y≈600 | O |
| Seams | Cylinder longitudinal seam; label-panel perimeter; bin/body parting line; battery perimeter | — | — | H1, H2 | O |
| Charging contacts | Underside of nozzle/bin area, mate in dock cradle | — | ? | — | gap |

## 6. WAND + MultiFLEX HINGE (modeler C)
Best refs: `snuk-gn-01` crops (W1, W2), **Sagewood photo `snuk-gal`** (W3: bent hinge, copper disc, hose), `amz-harbor-slate…main` (W4 bent, 3/4), `snuk-3241ukt-07` (W5 fully folded), flat-lay W6, `vid-luxemoe-f080` (wand decal). Sheet: `sheets/sheet-wand-hinge.jpg`.

Order from top (docked, O): handheld nose → **upper coupling** (dark charcoal, release button) → **MultiFlex hinge** → **copper wand tube** → **lower coupling** (dark charcoal, release button) → floorhead neck (copper disc). Total wand ≈ 640 mm (flat-lay).

| Feature | Position / shape / size | Colour & finish | Count | Refs | Status |
|---|---|---|---|---|---|
| Upper coupling / hinge housing | ≈ 60 mm wide, flattened-oval section, flares where it meets handheld; stadium release button at top | Very dark green-charcoal #404542 satin | 1 + button | W1 | O |
| MultiFlex hinge knuckle | Barrel across the wand ≈ 62 mm wide, 3 visible segments (centre + 2 side), hinge axis ≈ 650 mm above floor when docked; bends wand forward up to ~90° | Charcoal #3c413d; **copper end caps** on both barrel ends | 1 (copper caps 2) | W1, W3 | O |
| Hinge side disc | Round copper disc on the side of the hinge (seen when bent) ⌀ ≈ 20–25 mm, spun finish | Copper metallic (lit #c59886) | 2 (I one each side) | W3, W5 | O |
| Hinge hose | Black corrugated hose exposed at the back of the hinge when bent | Black | 1 | W3, W5 | O |
| Hinge latch | Small dark tab/latch on the rear side of the hinge (locks straight) | Charcoal | 1 | W3, W4 | O |
| Copper wand tube | Rounded-rectangle extrusion, face width 35 mm (depth ≈ 30 mm, I); straight | **Copper anodised-aluminium look, satin/brushed** (render lit #c99f88 / shade #a47b65; photo #a86a4e / #9b6145) | 1 | W1, W2, W3 | O |
| Wand decal | "POWERDETECTSPEED" printed vertically along front face (reads bottom→top when docked: rotated 90° clockwise), "POWER" bold, "DETECT" light, "SPEED" bold italic | White print | 1 | W2, `sn-gn-hero` | O |
| Lower coupling | Charcoal sleeve ≈ 58 mm wide with dark slot (vent/ID slot) at top and stadium release button | Charcoal | 1 + button | W2, `sn-gal2` | O |
| Electrical contacts | Hidden in couplings | — | — | — | gap |

## 7. DOCK — Clean & Empty auto-empty base (modeler D)
Best refs: `snuk-gn-01` (D1, front), **empty dock 3/4 `amz-harbor-slate-ia3246bl-main-71OzdgVntlL` (D2, D3 cradle close)** + same in `amz-oatstone-ia3246iv-main`, `sn-3241laa-01` (D4), **disassembled `rt-ia3241-in-the-box` (D5)**, `sn-IA3000_Series_5050_Auto-Empty` (D6), `snuk-3241ukt-05` (D7), `vid-luxemoe-f082/f083/f084` (plinth arch), `rt-ia3241-design` (rear + cord). Sheet: `sheets/sheet-dock.jpg`.

Architecture (O): heavy round-cornered **plinth + foot plate** (head parks on the plate) → removable **canister** (debris container with internal bag/HEPA, body colour) on top of plinth → a **duct post** rising from the rear of the canister/plinth → **top cradle** (U-saddle) that receives the handheld's bin end; dirt is evacuated from the bin through the cradle and post into the canister (I from parts + yellow label "Wait until evacuation completes…"). The head neck sits in an arched recess on the plinth front.

| Feature | Position / shape / size | Colour & finish | Count | Refs | Status |
|---|---|---|---|---|---|
| Canister / tower | Width ≈ 167–171 mm front view, near-square-to-round "squircle" plan (D2 shows rounded front corners, flatter faces), top at ≈ 505–510 mm, top shoulder radius ≈ 20 mm | Sagewood light sage satin (#8b8d83 lit / #6c6e63 shade; UK #919084) | 1 | D1, D2, D5 | O |
| Side window | Vertical stadium/pill slot on the **right** flank near front, ≈ 128 mm tall x ≈ 10 mm, upper half of canister (fill view) | Smoked translucent, light grey #949896 | 1 | D1, D2 | O |
| Seam ring | Thin light/metallic band between canister and plinth at ≈ 190–200 mm | Light satin (#898a80) | 1 | D1, D2 | O |
| Plinth | Same footprint as canister, ≈ 190 mm tall | Darker sage-charcoal (#53574f) satin | 1 | D1, `vid-luxemoe-f083` | O |
| Front arch recess | Tall round-top ("tombstone") recess on plinth front, receives head neck/lower coupling | Plinth colour, shadowed | 1 | D2 crop, `vid-luxemoe-f083` | O* |
| Foot plate | Thin rounded plate projecting forward under the head, ≈ 394 mm long (flat-lay) incl. under plinth; small upright peg at front-right corner | Plinth colour / dark | 1 (+1 peg) | D2, D5 | O* |
| Duct post | Rises from rear-top of canister, ≈ 70 mm wide rounded-rect section, slight flare into cradle | Body colour (sage) | 1 | D2, D5 | O |
| Top cradle | U-saddle ≈ 104 mm wide x ≈ 60 mm tall at ≈ 806–866 mm above floor; two side wings, **rear wing taller**; small screw boss on inner wall; latch slots on rear wing | Body colour; inside darker | 1 | D3 | O* |
| Evacuation port | Inside cradle floor (mates with bin door) | Black seal (I) | 1 | D5 | I |
| Charging contacts | Inside cradle (I) | — | ? | — | gap |
| Dock LEDs / indicator | None visible in any image (no light on canister/plinth front) | — | 0 | all dock refs | I (gap: rear/top not fully seen) |
| Power cord | Exits rear-bottom of plinth, grey/black, ≈1.5 m | Dark grey | 1 | D5, D10 | O* |
| Warning label | Yellow rectangle with black ! triangle on cradle piece (IA3241 flat-lay); hidden when docked | Yellow | 1 | D5 | O* |
| Rear canister latch | Small rectangular latch/handle recess on canister rear (flat-lay) | Body colour | 1–2 | D5 | O* |

## 8. MATERIALS & COLOUR (materials artist)
Samples are medians over patches (not single pixels), from 3 independent Sagewood sources: US render `sn-gn-hero`, UK render `snuk-gn-01`, real photo `snuk-gal`. Renders are evenly lit (prefer for albedo); the photo is warm-lit (prefer for saturation sanity).

| Material | sRGB hex samples | Proposed base colour | Finish |
|---|---|---|---|
| Sagewood body (handheld, dock canister, post) | render shade #6c6f66 / #72756b / #77786f ; render lit #8b8d83 / #919084 ; photo shade #5a5f58 | **#7d8073** (sage grey-green, low chroma, slight warm-green) | Satin plastic, roughness ≈ 0.45, fine micro-texture |
| Sagewood dark (plinth, head chassis, couplings, hinge) | #53574f (plinth) ; #404542 / #3c413d (couplings, hinge) ; head neck plate #60635a ; photo head chassis near-black #0d0805 | plinth **#53574e**; couplings **#3e433f** | Satin; head chassis darker/more matte |
| Copper (wand, filter ring, discs, hinge caps) | render shade #a47b65, lit #c99f88/#e1a98d ; filter ring #a47b66 ; neck disc #865d47/#91573a ; photo wand #a86a4e/#9b6145, hinge disc #c59886 | **#b07c5e** albedo, metallic 1.0, roughness ≈ 0.30 (wand brushed lengthwise), discs spun/radial anisotropic | Anodised-aluminium look, not mirror |
| Brushroll (Luxe) | through cover #724d3e / #804c3a | **#8a5a44** | Matte rubber, roughness 0.8 |
| Clear parts (bin, roll cover, lip) | — | transmission 0.9, IOR 1.58, tint very slight cool grey (#e8eef0); roll cover slightly smoked | Gloss PC |
| Label panel | #787c7a | **#6f7372** dark metallic grey, brushed | metallic 0.6 |
| Silver text band, display bezel | — | #c9ccca | satin aluminium |
| Display glass | #171815 | black glass | gloss, roughness 0.05 |
| Display glyphs (emissive) | #8ebdd7 – #b2d3ec | **#9fcbe6** emissive | — |
| Headlight | — | white core, blue glow ≈ #4aa8ff | emissive, cone on floor |
| Accent blue strip (head right end) | — | #2a8fd6 (I) | gloss |
| Grip | — | #1c1d1c | soft-touch rubber, roughness 0.85 |
| Black hose, wheels | #464644 (wheel) | #2a2b2a | rubber |
| Site swatch | sharkninja.com colour code for Sagewood = **#757971** | — | matches sampled body tone |

Colour conflicts (C): the LuxeMOE film grades Sagewood noticeably greener/more saturated (olive) than the white-background renders; renders are taken as albedo truth, film as mood only.

## 9. Markings inventory
| Marking | Where | Ref |
|---|---|---|
| "Shark" wordmark (white) | handheld label panel | H1 |
| "POWERDETECTSPEED" (dark on silver) | handheld band | H1 |
| "POWERDETECTSPEED" (white, vertical) | copper wand front | W2 |
| "Shark" (light grey) | floorhead neck plate | F1 |
| "TURBOPRO DETECT" (white italic) | roll cover left | F1 |
| "Shark" (grey) | battery outer panel | H2 |
| "Shark" (embossed) | crevice tool | `sn-gn-hero` |
| Yellow warning label | dock cradle (hidden when docked) | D5 |

## 10. Lights summary
1. Floorhead Reveal LED — 1x, front-right corner, blue-white, beam forward/down (O).
2. Handheld rear display — arc gauge, PowerDetect icon, battery bar, charge icon, ice-blue emissive (O*).
3. Dock — no visible LEDs found (I/gap).
4. No light on the wand/hinge (O).

## 11. Unresolved gaps
- No true side/rear/top orthographic of the Sagewood unit; side/rear geometry comes from IA3241/BL/IV 3/4 renders and RTINGS photos.
- No underside or display photo of a **Luxe** unit (only IA3241 orange/blue) — Luxe display bezel/button colours unconfirmed.
- Dock rear, dock top (cradle floor/evacuation port, charging contacts) not clearly seen.
- Display diameter and handheld depth are inferred (±10 %).
- YouTube unboxing/360 videos not retrievable (yt-dlp bot check; candidate IDs in `manifest.json → not_retrieved`). Best Buy / Target / Walmart / Costco galleries not fetched; IA3241EUT ES gallery (14 images) listed but not downloaded.
- Amazon ASIN conflict (§0).
