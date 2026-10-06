# Product Reference: Shark PowerDetect IP1251EUT

Version 1.0 (2026-10-04). Owner: reference-director. Reference images are in `assets/references/` and listed in `assets/references/manifest.json`, which records the URL, retrieval date, sha256, what each image shows and usage notes. The labeled contact sheet is `assets/references/contact-sheet.jpg`. **All reference images are SharkNinja material. Use them for reconstruction only. Do not redistribute them or ship them in the app.**

## 1. Chosen SKU

**IP1251EUT** is a cordless stick vacuum with a PowerDetect DuoClean Detect floorhead, MultiFLEX wand and no auto-empty dock. This is the working assumption from brief §2.

- Shopify product JSON for P1 (`/products/shark-powerdetect-clean-empty-mor-siyah.json`) has the tag `IP1251EUT`. Its gallery contains exactly V1–V6. The "clean-empty" text in the URL is legacy. The page text does not mention a dock.
- **V7 is SharkNinja's own `IP1251EUT_01` image.** It is a straight front view of the EUT on a transparent background, found through the public Cloudinary tag listing. It is the **primary scale reference**.
- The manual for P2 (`IP3251_1.pdf`, a Turkish manual covering the IP1000 and IP3000 series) is the source for M1–M4. The IP1000 sections apply to this SKU.

## 2. Reference IDs

| ID | Shows | Main use |
|---|---|---|
| V1 | Assembled 3/4 view from front-left, MultiFlex partly bent, accessories | Colour relationships, decals, buttons. **Its purple is desaturated and is an outlier.** |
| V2 | IP1251UKT folded to about 180°, standing alone, near-orthographic side view | Lengths along the axis (cross-check), handle and battery loop, rear wheels, head side cap, fore-aft depths |
| V3 | Top-down lifestyle shot of the head on oak | Head top face, purple strip, neck |
| V4 | Three handheld close-ups | End cap and control screen, vent, bands, ribbed bin ring |
| V5 | Head close-ups. The rings and badge are advertising. | Roller chevrons, LED windows, label plate. The bottom-left quadrant gives the head depth/width ratio. |
| V6 | MultiFlex at about 90° in use | Handle loop, battery panel, front spine, fold direction |
| **V7** | **Official EUT front view, upright** | **Primary lengths along the axis and lateral widths. Purple colour.** |
| V8 | UKT front view with tools | Confirms that EUT and UKT look the same from the front |
| V9 | UKT head, low 3/4 view. The review panel and rings are advertising. | Side cap, turquoise button, LED window |
| M1–M4 | Manual pages 5, 11, 17 and 12 | Assembly and lock tabs, control screen, sensor locations, MultiFLEX latch and fold |

## 3. Scale method (traceable)

- **V7, front view:** the alpha bounding box runs from y 121 to 1947 = 1826 px, which corresponds to 1.158 m (P1 H). This gives **k₇ = 0.634 mm/px** at the wand plane. The head front is closer to the camera, so it is about 8% larger in the image: 447 px wide, compared with 415 px predicted from k₇. Head-plane measurements therefore use **0.263 m / 447 px = 0.588 mm/px**.
- **V2, side view, folded:** floor (bottom of rear wheel) y 2648 → hinge pivot (centre of purple disc) y 310 = 2338 px. Hinge pivot → end of end cap y 2189 = 1879 px. The sum is 4217 px, which corresponds to 1.158 m, so **k₂ = 0.2747 mm/px**. This assumes the MultiFLEX fold is a pure rotation about the pivot.
- **Cross-check:** V7 and V2 agree within 1–3 mm on the purple wand (0.298 / 0.299) and the end cap (0.053 / 0.053). Floor → hinge pivot is 0.664 m in V7 and 0.642 m in V2, a 3% difference.
- **Head depth:** V5 bottom-left is near-orthographic top-down. The main body runs from front edge x 650 to rear edge x 318 = 332 px. Half the width runs from the neck centreline y 1200 to the side edge y 870 = 330 px, so the full width is 660 px. Ratio 0.503 × 0.263 = 0.132 m.
- **Overall depth from P1 (D 0.393 m):** this runs from the head front to the rear of the handle. It is used only as a constraint, not as the depth of the head.

Status key: **observed** = measured directly in a matched view. **inferred** = estimated or derived, with no direct view. **conflicting** = sources disagree, and the choice and reason are given.

## 4. Proportions table

Upright pose: wand vertical, floor y = 0. Lengths are along the wand/handheld axis, from the bottom up. Values are in metres.

| # | Component | Chosen | V7 (front) | V2 (side) | Status |
|---|---|---|---|---|---|
| 1 | Floor → neck joint disc centre | **0.112** | 0.112 (disc facing front, 1770 px) | 0.094 (disc seen from the side) | conflicting. The two views show different landmarks on a 2-axis neck. The pitch axis is probably lower, about 0.09–0.10. |
| 2 | Neck joint → bottom of purple wand | **0.171** | 0.171 | 0.160 | observed |
| 2a | of which the grey bottom cuff of the wand (lock-tab slot, 1505–1530 px) | 0.020 | 0.020 | 0.017 (dark knob) | observed |
| 2b | of which the floorhead neck connector (grey, oval release button centred 0.079 above the disc) | 0.151 | 0.151 | ~0.143 | observed |
| 3 | **Purple wand (lower rigid tube)** | **0.298** | 0.298 | 0.299 | observed |
| 4 | Top of purple → MultiFLEX pivot (grey taper, wand-side half of the hinge) | **0.082** | 0.082 | 0.087 | observed |
| 5 | MultiFLEX pivot → bottom of handheld (upper grey wand, dark-grey oval release button centred 0.032 below the handheld) | **0.149** | 0.149 | 0.163 | observed |
| 6 | Handheld bin zone: grey base + clear bin + purple ring | **0.216** | 0.216 | 0.206 | observed |
| 6a | of which the grey bin base / handheld socket | 0.035 | 0.035 | — | observed (V7) |
| 6b | of which the silver cyclone-shroud band, seen through the bin | 0.050 | 0.050 | — | observed |
| 6c | of which the clear bin window (visible part) | 0.100 | 0.100 | — | observed |
| 6d | of which the purple ribbed ring at the top of the bin | 0.030 | 0.030 | (short purple segment only) | observed in V1/V4/V7. In V2 only the part near the front frame shows, so the ring may be partial or recessed (inferred). |
| 7 | Motor / vent section, including the silver "Shark" band at its base | **0.076** | 0.076 | 0.095 (V2 boundary includes the ring zone) | observed |
| 8 | Purple ribbed end cap (round control screen on its end face) | **0.053** | 0.053 | 0.053 | observed |
| | **Sum** | **1.157** | | | |

### Cross-sections and other dimensions

| Component | Chosen (m) | Source | Status |
|---|---|---|---|
| End cap diameter | 0.090 | V7 lateral 0.088 (139 px). V2 fore-aft about 0.09–0.10, partly hidden by the grip. | observed |
| Round control screen on end face (dark disc) diameter | ~0.060 | V4 left, about 0.65–0.7 × cap diameter | inferred |
| Motor / handheld body width (lateral) | 0.090 | V7 141–147 px | observed |
| Handheld body depth: bin rear wall → front frame (fore-aft) | 0.104 | V2 y 1500: 1232–1611 px | observed |
| Clear bin diameter | 0.090 (+ rear lid latch protruding about 0.025) | V7 width, V2 depth minus spine | observed / inferred |
| Front frame ("spine") along bin + motor, front side, light-grey window strip | 0.034 deep | V2 1497–1621 px | observed |
| Motor/bin axis offset behind wand axis | ~0.035 | V2 fold geometry, V6 | inferred |
| Bottom of handheld / socket width | 0.046 | V7 73 px | observed |
| Upper wand width (lateral) | 0.045, or 0.051 at the release-button bulge | V7 71 / 81 px | observed |
| MultiFLEX hinge housing width (lateral) / with purple pivot caps | 0.051 / 0.063 | V7 81 / 99 px | observed |
| MultiFLEX pivot cap (purple disc) diameter | 0.023 | V2 85 px | observed |
| MultiFLEX pivot location | on the **front** (+Z) face of the wand top, about 0.025 in front of the wand axis. The fold closes toward the front: in storage the handheld hangs above the head (V2). The release latch is on the **rear** of the wand (M4, V2). | V2, V6, M4 | observed |
| Purple wand cross-section, lateral × fore-aft | **0.035 × 0.046**. Rounded rectangle with soft facets ("hex" look in V1). | V7 55 px. V2 186 px gives 0.051, M1 drawing gives 0.039. | lateral observed. Fore-aft conflicting: mean chosen. |
| Taper from purple wand to hinge | 0.036 → 0.045 over about 0.05 | V7 | observed |
| Lower cuff / neck connector width | 0.036 → 0.046 | V7 57 → 72 px | observed |
| Neck yoke width above head | 0.048 | V7 75 px, V5 | observed |
| **Floorhead width** (outer, including side caps) | **0.263** | P1 | observed (published) |
| Floorhead main-body depth (front bumper → rear body edge) | **0.132** | V5 ratio | observed (ratio) |
| Floorhead footprint depth including neck and rear wheels | ~0.185 | V5, V2 | inferred |
| Floorhead height (front, to top of clear cover) | **0.076** | V7 front face 130 px × 0.588 | observed (±0.005) |
| Front soft roller (black, turquoise chevrons): visible length / diameter | 0.200 / ~0.055 | V7 340 px × 0.588; diameter from head height | length observed, diameter inferred |
| Rear bristle brushroll (underneath) diameter | ~0.040 | no underside view | inferred |
| Rear wheels (2, grey tyre with radial-line face, dark hub), diameter / width | 0.047 / ~0.020 | V2 172 px | diameter observed (±10%), width inferred |
| Wand axis → head front | ~0.150 | P1 D 0.393 − handle extent 0.208 − axis offset 0.035 | inferred |
| Handle loop: rear extent from motor axis to outer rear end | 0.208 | V2 757 px (axis x 1450 → 693) | observed |
| Handle loop: outer height at the rear end | 0.162 | V2 590 px | observed |
| Battery (lower bar of loop, light-grey "Shark" panel): length × thickness | 0.152 × 0.040 | V2 | observed |
| Grip (upper bar, purple mode trigger next to the motor): thickness | ~0.028 | V2 | observed (±15%) |
| Battery bar attachment, below top of cap | 0.107–0.148 | V2 | observed |
| Grip / trigger attachment, below top of cap | 0.035–0.050 | V2 | observed |
| Handle rise toward the rear (relative to the line perpendicular to the motor axis) | ~20° (range 10–30°) | V2 bars, V6 | inferred |

## 5. Component list

| Component | Description | Refs | Status |
|---|---|---|---|
| End cap | Purple, vertically ribbed, slightly domed. Its end face carries a **dark round control screen** with a power button at the edge nearest the handle, mode icons, a battery bar, and a dirt-indicator light (white → purple when dirt is detected). The `PowerControlAnchor` goes here. | V4, V6, V7, M2 | observed. Exact icon layout from M2 only. |
| Motor section | Warm-grey body with a dotted/slotted vent grille on the front and front-side, and a silver "Shark" band at the base. V4 shows the small "POWERDETECT" wordmark. | V1, V4, V7 | observed |
| Bin | Clear cylinder with an internal silver cyclone shroud and a ribbed purple ring at the top. Grey front frame with a light window strip. Rear lid latch. Bottom-emptying lid (M4/manual p13 flap). | V1, V2, V4, V6, V7 | observed |
| Handle + battery | Closed loop behind the motor. Grip is the upper bar, with a purple mode trigger. The removable battery is the lower bar, with a light-grey "Shark" panel and a round rear end cap/button. | V2, V6, M-p10 | observed |
| Upper wand | Short grey section with a dark-grey oval release button on the front. | V1, V7 | observed |
| MultiFLEX hinge | Grey housing with purple pivot caps on both sides. A black corrugated internal hose shows when folded. Release latch at the rear. | V1, V2, V6, M4 | observed |
| Purple wand | Rounded-rectangle tube. "Shark **POWER**DETECT" reads top-to-bottom on the front face in light grey (V7). V1/V6 show the same wordmark on the side as well. | V1, V3, V6, V7 | observed. Front placement from V7. |
| Neck connector + neck | Grey collar with a light-grey oval release button on the front. Neck joint with a purple/dark disc, black corrugated hose, and yoke onto the head. | V1, V5, V7, V9 | observed. Joint axes inferred (2-axis: lateral pitch + swivel). |
| Floorhead | Low, wide, grey shell. Purple teardrop side caps on both sides; the right cap has a turquoise round button. Grey side slot (edge sensor). Clear top cover over the front roller. "duoclean DETECT" plate. Shark logo on the rear deck. Purple light strip along the rear edge of the roller window (V3, V5). White **LED windows at both front corners**. | V1, V3, V5, V9, M3 | observed |
| Rollers | Front: soft black roller with turquoise chevron/stripe groups, visible through the cover. Rear: bristle brushroll with Anti Hair Wrap comb, underneath and not visible. | V1, V5 | front observed, rear inferred |
| Wheels | 2 rear wheels. Grey radial-texture face, dark hub. | V2, V5 | observed |
| Sensors | Dirt sensor in the air path (handheld inlet). Light sensor on the top rear of the head. Edge sensor on the head side. Do not model them as visible features beyond small windows. | M3 | observed (manual) |

## 6. Colour and material notes

Medians are of masked pixels per region, sampled across several views.

| Part | Samples (sRGB median) | Suggested base albedo | Note |
|---|---|---|---|
| Purple (wand, cap, ring, side caps) | V7 #4F326F / #4B2F6A / #523571 · V8 #4C306B · V2 #664188 / #633F84 · V3 #695292 · V4 #695294 · V6 #5E4288 · **V1 #5D4F70 (S 0.14–0.21)** | **#5A3C7E** (H ≈ 268°, S ≈ 0.35, L ≈ 0.36) | V1 is **conflicting**: it is a stylised low-saturation render, so it is excluded. Hue is stable at 261–273° across all views. Satin plastic. The wand is slightly glossier than the cap. |
| Body grey | V7 #7E7B75 / #88867F / #706F69 · V2 #85847F · V1 #787975 · V6 #6F716A | **#7D7B76** warm neutral (H ≈ 45°, S ≈ 0.03) | Matte to satin plastic. The "Shark" band and cyclone shroud are brushed silver. |
| Light grey panels (battery panel, frame window strip) | visual | ~#C9CACB | inferred |
| Turquoise roller stripes / button | V7 #39776D · V2 #3B8379 · V1 #29655C | **#3A7F74** for stripe fibre. Side button is lighter, about #6FD3C6 (V2/V9 visual). | V5 #10877C is advertising-lit: excluded |
| Black parts (roller core, hose, screen) | — | #151617 | Rubber / soft-touch |
| Interface accent (brief §4) | derived from the purple base | #5A3C7E, or a lighter tint #7A5BA3 on the pale background | art direction, not a brand spec |

## 7. Regional differences (EUT vs UKT)

- V7 (EUT) and V8 (UKT) front views are identical in geometry and purple saturation (#4F326F vs #4C306B).
- V2 (UKT, side) does not show the full purple bin ring or the silver band, because the front frame hides them from the side. No hardware difference was found.
- The UK page P3 lists an `IP1251UKT_3D` media asset (a SharkNinja web 3D viewer). It is proprietary and **not licensed for reuse**, so it was not downloaded or used.
- P3 dimension fields conflict, as brief §3.1 says. Only P1 H/W/D are used.

## 8. Licensed 3D model search (bounded, about 10 minutes)

- Web search for "Shark PowerDetect IP1251 3D model" and for sketchfab/cgtrader/turbosquid: **no model of the vacuum was found**. The only hit was a Printables wall-mount accessory, which is not the product.
- Sketchfab API search (`shark powerdetect`, `shark cordless vacuum`, `shark stick vacuum`) returned no usable results.
- SharkNinja's own web 3D asset (`IP1251UKT_3D`) exists but has no reuse licence.
- **Result: no exact, licensed IP1251 model is available.** The procedural Blender route stands (DECISIONS.md).

## 9. Missing views and open issues

- **Underside:** no view of the rear brushroll, the underside of the intake or the wheel axles. These are inferred.
- **Direct rear view:** the handle/battery rear face is seen only in V2 (side) and M-p10 (drawing).
- The neck joint axes are not resolved from photos. The disc centre is 0.112 m (V7) or 0.094 m (V2) above the floor. Use about 0.095–0.10 for the pitch axis and tune by eye against V2/V9.
- Purple wand fore-aft depth is between 0.039 and 0.051. 0.046 is chosen.
- The purple ring at the bin top may be partial or recessed (seen in V2).
- Control-screen icon layout comes only from the M2 line drawing. Show it as a dark disc with a subtle ring; no invented UI.
- V5/V9 advertising rings, glow and arrows, and the V3 triangles, are **not hardware or lighting**.

## 10. Art-direction notes

- Hero pose: front 3/4 view (V1 angle) with the wand **straight**, as in V7, not bent. Use a pale studio background, #EAE9E6.
- Purple appears in only five places: end cap, bin ring, wand, hinge pivot caps, and head side caps (plus the neck disc). Grey dominates. Do not purple-wash.
- Turquoise appears only on the front roller stripes and the side-cap button. Keep turquoise out of the UI.
- Head LEDs: small white corner windows. Their floor spill should be subtle (M2, "corner indicator"). No green laser.
