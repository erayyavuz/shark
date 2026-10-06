# TECHNICAL REFERENCE — Shark PowerDetect Clean & Empty IP3251 (TR "mor-siyah" / UK IP3251UKT / EU IP3251EUT / AU IP3251)

Owner: technical-research agent. Status: **v1.1 (2026-10-05)**. v1.1 adds the dock scaled from the EUIPO orthographics. This file covers manuals, drawings, registered designs and dimensions. Photos and video are owned by the reference-director.
All files are under `assets/references/ip3251/technical/`. The `manifest.json` there lists the URL, date, sha256 and description for each file. Licence: **reference only**.
Nothing here is CAD-exact. Every number below has a source and a confidence level.

**Platform.** The IP3251 is the **IP3000 series**: an IP1000-series stick plus an auto-empty dock (XDCKIP3000). The stick, wand and floorhead are the **same hardware as the IP1251** (IP1000 series). The TR, UK and EU manuals cover both series in one booklet. The TR product page lists the stick spec as **115.8 × 26.3 × 39.3 cm, 3.71 kg**, which is identical to IP1251EUT. The existing measurements in `PRODUCT_REFERENCE.md` (IP1251EUT, V7 and V2 photos) therefore **apply to the IP3251 stick directly**. Only the colour differs: the user's unit has a bronze/champagne wand where the IP1251EUT wand is purple.

**User colourway** (frames `assets/references/ip3251/user/user-video-1663..1668.jpg`):
- Handheld body: gunmetal/grey.
- Top cap: purple, vertically ribbed, ending in a round black screen with a purple LED ring. The cap is fluted aluminium-look and sits just above the vent grille.
- Badge: silver "POWERDETECT" (champagne label), with "Shark" on a brushed-silver collar above the clear bin.
- Bin: clear, with a purple ring at the top of the bin window.
- Wand and hinge: bronze wand, grey MultiFLEX hinge with purple pivot caps.
- Floorhead: dark grey with a turquoise soft roller, a turquoise/teal "DETECT" printed strip, and violet/purple floor LEDs at the front corners.
- Dock: white tower, dark-grey post and base plate. The round black thing on top is the odour dial, described in §5.4.

---

## 1. Sources

| # | File (under `technical/`) | Origin | What it gives | Applies to IP3251? |
|---|---|---|---|---|
| **S1** | `manuals/IP3251_TR_owners_manual.pdf` + `manual_pages/tr_og_p-01..24.png` (200 dpi, single pages), `tr_og_contact_sheet.png` | sharkninja.com.tr product page link `cdn.shopify.com/.../IP3251_1.pdf` (doc IP1000_IP3000Series_IB_MP_Mv12, 2024-11-22) | **Primary.** Turkish market manual. All line drawings: assembly, dock, odour dial, UI screen, battery, MultiFLEX, dock use/quiet/bin-full, bin emptying, filters, nozzle maintenance, sensors, blockages, error table, accessories | **High** (this market) |
| S2 | `manuals/IP3000UK_owners_guide_EN_IP3251UKT.pdf` + `manual_pages/uk_og_p-01..15.png` (spreads) | Marks Electrical mirror `.../manuals/IP3251UKT.pdf` (2024-07-29) | The same drawings in English, with labels. Specs: 21.6 V, body motor 380 W, nozzle 120 W. Battery XBATR640EU 21.6 V 3750 mAh 81 Wh. Dock XDCKIP3000UK. **The UI screen drawing is a different variant** (see §5.1) | High |
| S3 | `manuals/US_IP3000_QSG_homedepot.pdf` + `manual_pages/us_qsg_p-01/02.png` | Home Depot CDN (2024-06-17) | **Colour** graphics: DETECT colours (white → light purple → purple), the nozzle's purple floor-light bars, edge detect, quiet switch, bin emptying | High |
| S4 | `manuals/IP3251EUT_owners_guide_PL_multi_mediaexpert.pdf` + `manual_pages/eu_pl_og_*` | Media Expert PL (2024-11-19) | EU edition, used as a cross-check | High |
| S5 | `manuals/IP1000UK_owners_guide_EN_IP1251UKT.pdf` + `manual_pages/uk_ip1000_og_*` | Marks Electrical | The same stick without the dock | High for the stick |
| S6 | sharkninja.com.tr IP3251 page (session scratchpad `tr.html`, not redistributed) | official TR | Colour "Koyu Gri". 3.71 kg. 115.8 × 26.3 × 39.3 cm. 380 W. Bin 0.7 L. DuoClean Detect = **two rollers**. 70 min | High (stick) |
| S7 | sharkninja.co.uk `IP3251UKT.html` | official UK | **System 117.7 H × 26.29 × 47.19 cm**, stick 3.71 kg, "with dock 8.4 kg", colour "White / Java Grey", charge 6 h, 70 min | High |
| S8 | sharkninja.com.au IP3251 page | official AU | With dock 117.5 H × 26 W × 45.5 D, 8.4 kg. Stick 115 H × 26 W × 38 D, 3.6 kg. 0.7 L + 2 L AED | High |
| S9 | euronics.co.uk / atlanticelectrics.co.uk IP3251UKT | UK retailers | 1177 × 263 × 472 mm, 4.36 kg (?), box 785 × 472 × 327 mm, 13.7 kg | Medium |
| S10 | ShopJimmy spare parts | US parts reseller | Part numbers only (no dimensions): dock XDCKIP3000, wand 555CH3251, handheld XPODIP3251, dust cup 546CH3251 | Medium |
| S11 | EUIPO RCDs in `designs/EUIPO_<number>/view0N.jpg` + `_sheet.png` (see §3) | public register | Line drawings with 7 views each | dock **high**, others low |
| S12 | `PRODUCT_REFERENCE.md` §4 (IP1251EUT photo measurements, earlier run) | project | The stick, wand and head proportions table | High (shared hardware) |

The official sharkninja.co.uk spare-part pages all use placeholder dimensions ("2.01 cm × 2.01 × 2.01, 2 kg"). They are useless for sizing.

---

## 2. Drawings index (best views first)

"p" = PNG page number. `tr_og` pages are single A5 pages. `uk_og` pages are 2-page spreads.

| PNG | Content | Use for modelling |
|---|---|---|
| **`tr_og_p-04.png`** | IP3000 ASSEMBLY (TR) | **Best exploded set.** Handheld side elevation: motor cylinder with ribbed cap at front-top, vent grid, clear bin below, **closed loop handle** with the battery as the lower bar, round power-jack dot. MultiFLEX wand side view (hinge knuckle with round pivot at the upper third, latch). Floor nozzle side view (teardrop/"lozenge" side cap with round end disc, small oval edge sensor, large rear wheel). **Dock side elevation**: charging post (separate, with cradle head and quiet slider), tower with a top that slopes down toward the rear, odour cartridge, lower plinth with rear louvred filter door + round button, flat base plate, wall adapter. Dock 3/4 view: cradle cup, accessory clip, base plate with the post-mounted crevice tool peg. |
| **`tr_og_p-14.png`** | Using the auto-empty dock | Close-up of the cradle charging contacts (2 square pads). **Dock top close-up: quiet-mode slider** (fan icon ← slider → moon icon) in a recess at the top of the post/tower junction. **Stick docked, 3/4 view** (proportions of stick vs dock). **DUST BIN FULL indicator** (black pill-shaped light panel with dust-bin icon + moon icon) on the dock top. |
| **`tr_og_p-08.png`** | Battery UI | **Round screen front view, TR variant** (see §5.1), battery pack side view (long bar, dot LED at the rear end), screen battery states (full / half / low (blinking) / empty). |
| **`tr_og_p-19.png`** | Troubleshooting | **Labelled screen** (LED ring, ECO, DETECT, BOOST, FO icon) + error table. |
| `tr_og_p-11.png` | Controls | Power button on the screen, **mode trigger** under the grip, upright pose, nozzle top view with clean indicator, **Edge indicator** (light cone off the side). |
| `tr_og_p-12.png` | Above-floor + MultiFLEX | Hand-vac release button (oval with circle), MultiFLEX bend (~70–80° forward) and **fold-for-storage pose** (handheld hangs alongside the wand, head on the floor). |
| `tr_og_p-09.png` | Charging | **Cradle top view with contacts**, stick on dock 3/4 view, hand-vac/wand release buttons, IP1000 jack. |
| `tr_og_p-05.png`, `tr_og_p-06.png`, `uk_og_p-05.png` | Odour dial | **Dial top view**: circular, flip-up loop handle, "ODOR NEUTRALIZER TECHNOLOGY" text (UK: hexagon logo + "ANTI-ODOUR TECHNOLOGY"), lock icon, "+"/"–" intensity arc with wedge bars, triangle index, teal alignment arrows. Cartridge = short cylinder with a bayonet. |
| `tr_og_p-13.png` | Emptying | **Dock bin removed**: rear face of the bin (ribbed latch grid, round port), post + cradle standing on the base with the tower bin cavity. **Bin emptying**: rectangular bin, top handle/release, bottom flap opens. Hand-vac emptying. |
| `tr_og_p-15.png` | HEPA filters (IP1000 / IP3000) | Handheld side elevations (best **handheld side views**, with vent slot array, cap ribs, loop handle, power jack), dust-cup removal, post-motor filter pull tab. |
| `tr_og_p-16.png` | Dock filter + nozzle care | **Dock rear lower filter door** (vertical louvres, round button), filter cassette + frame; exhaust foam (rounded triangle) over a fan under the bin; **nozzle side cap** (lozenge with round end disc and oval sensor); underside with **4 squeegee screws + 2 quarter-turn locks**, soft roller removal. |
| `tr_og_p-17.png`, `uk_og_p-11.png` | Sensors | Dirt Detect inside the handheld inlet (Fig. 1). **Light Detect sensor = small round window on the nozzle top deck, left of the neck** (Fig. 2). **Edge Detect = oval window on the side cap** (Fig. 3). Floor Detect on the underside, right of the neck (UK Fig. 4). Dust-cup removal. |
| `tr_og_p-18.png` | Blockages | Underside/top of the nozzle (front roller, chevron V of the rear brushroll, 2 rear wheels, neck), dock post release, dock top. |
| `uk_og_p-07.png` | Controls, UK | Screen variant B, mode trigger, **Light Detect beams from both front corners**, Floor Detect, Edge indicator, clean indicator. |
| `us_qsg_p-01.png` | QSG colour | DETECT colour ramp; nozzle with **purple light bars at the bottom front corners**; quiet switch; dock emptying. |
| `tr_og_p-20.png` | Accessories A–N | Crevice, duster crevice, flexi crevice, anti-allergen brush, multi-surface pet tool, motorised tool, upholstery tool, battery, dock post-motor filter, pre-motor filter, HEPA, dock foam, 1- and 2-slot accessory clips. |

---

## 3. Registered designs (EUIPO) — match assessment

Candidates found in the previous run's Google Patents SharkNinja design list (2023-06 priority family). Images were downloaded from the EUIPO register.

| Design | Indication | Priority | Verdict |
|---|---|---|---|
| **015044754-0001** `designs/EUIPO_015044754-0001/` (+ `_sheet.png`), 7 views: front, rear, side, side, 3 × perspective | Docking stations for vacuum cleaners | US 29/895,332, 2023-06-20 (filed EU 2023-12-18) | **MATCH (~85%) — this is the IP3000 dock.** Same topology as the manual: tall separate post with an open cradle cup, a rectangular tower with a flat top carrying a **round dial** and the bin handle recess, a lower plinth with **fine vertical fluting/louvres** all round and a **rear louvred filter door with a round button**, and a flat base plate with a rounded front and a recess in front of the post. Use it as the **dock blueprint** (front, rear and side orthographics). |
| 015044922-0001 | Hand-held vacuum cleaners | US 29/895,331, 2023-06-20 | **Partial (~40%).** Round knurled end cap, round screen with a pill power button, clear bin, vent grilles: all consistent. The handle differs: it is an open L-handle ending in a battery block, whereas the IP3251 has a closed loop with the battery as the lower bar. Treat it as an early or sibling form. Do not use it as a blueprint. |
| 015045103-0001 | Vacuum cleaners | US 29/895,800 | Hand-vac with a wrap-around hose. **Not this product.** |
| 015045106-0001 | Vacuum cleaners (part of) | US 29/895,798 | Slim stick, different head. **Not this product.** |

Not searched this run: US design patents. The US grants for 29/895,331/332 might exist as USD10xxxxx, but patentimages are blocked from the sandbox. No design was found for the stick + DuoClean Detect head as a whole. For those, use the manual drawings plus the IP1251 photo measurements.

---

## 4. Consolidated dimensions (mm)

### 4.1 Official / retailer

| Item | Value | Source | Confidence |
|---|---|---|---|
| **System (stick in dock) H × W × D** | **1177 × 263 × 472** | S7 UK official (117.7 × 26.29 × 47.19), S9 | High |
| Same, AU | 1175 × 260 × 455 | S8 | High |
| **Stick H × W × D** | **1158 × 263 × 393** | S6 TR (= IP1251EUT P1) | High |
| Same, AU | 1150 × 260 × 380 | S8 | High |
| Stick weight | 3.71 kg (AU 3.6 kg) | S6, S7, S8 | High |
| System weight (stick + dock) | 8.4 kg ⇒ dock alone ≈ 4.7 kg | S7, S8 | High |
| Handheld weight | ≈ 2 kg ("almost 2 kg") | testsieger.de review | Medium |
| Handheld length | ≈ 420 (cap end → inlet, excluding handle) | testsieger.de | Medium |
| Handheld dust cup | 0.7 L | S6, S8, S9 | High |
| Dock bin | 2.0 L ("2 L AED") | S8, UK spare "2.0L AED base" | High |
| Battery | XBATR640EU, 21.6 V, 3750 mAh, 81 Wh, Li-ion ("6 × 4.0 Ah"). TR manual prints XBATR640US | S2, UK spare list | High |
| Runtime / charge | up to 70 min (ECO, handheld, no motorised tool) / ≈ 6 h | S1 p8, S7 | High |
| Motor | 380 W body, 120 W nozzle (AU page says "850 W", probably a typo) | S2 p2, S6 | High |
| Dock evacuation | 15 s | S1 p14 | High |
| Power adapter | YLJX2I-T263100 (TR) / -U263100 (UK), i.e. 26.3 V / 1.0 A. Cord 1.2 m | S1 p3 | High |
| Odour cartridge | 17.4 g | S1 p24 | High |
| Shipping box | 785 H × 472 W × 327 D, 13.7 kg | S9 | High |

### 4.2 Component dimensions

Stick, wand and head are inherited from `PRODUCT_REFERENCE.md` §4 (IP1251EUT, same hardware). The dock values are derived from the manual drawings.

| Component | Value | How | Confidence |
|---|---|---|---|
| Stick stack, floor → top of cap | 1157 total: neck disc 112, neck→wand bottom 171, wand tube 298, wand top → MultiFLEX pivot 82, pivot → handheld bottom 149, bin zone 216, motor/vent 76, purple cap 53 | PRODUCT_REFERENCE §4 | High (observed, shared stick) |
| End cap Ø / round screen Ø | 90 / ~60 | PR §4 | observed / inferred |
| Handheld body width / depth | 90 / 104 | PR §4 | observed |
| Handle rear extent from motor axis / loop height | 208 / 162 | PR §4 | observed |
| Battery bar (lower loop bar) L × thickness | 152 × 40 | PR §4 | observed |
| Wand cross-section | 35 lateral × ~46 fore-aft (rounded rectangle) | PR §4 | lateral observed |
| MultiFLEX pivot cap Ø / hinge width with caps | 23 / 63 | PR §4 | observed |
| **Floorhead width** | **263** | official W | High |
| Floorhead main body depth / with neck + wheels | 132 / ~185 | PR §4 | observed ratio / inferred |
| Floorhead height (front) | 76 ± 5 | PR §4 | observed |
| Front soft roller (turquoise on this colourway): visible length / Ø | ~200 / ~55 | PR §4 | length observed, Ø inferred |
| Rear bristle brushroll Ø | ~40 (chevron V pattern seen in S1 p18 underside) | PR §4 + drawing | inferred |
| Rear wheels (2) Ø / width | 47 / ~20 | PR §4 | observed ±10 % |
| _Dock scale method (v1.1)_ | EUIPO 015044754-0001 front view (view01) and side view (view02) are orthographic: overall height (plate bottom → cradle top) = 508 px. Anchored at cradle top = 850 mm (±30) ⇒ **1.67 mm/px (1.57–1.73)**. Cross-check: the TR p4 side-elevation ratio gives tower ≈ 0.40 m with the same anchor, and the two methods agree within 5 %. | EUIPO + stick stack | Medium |
| Dock total height (plate bottom → top of cradle cup) | **≈ 850** (820–880) | anchor | Medium |
| Dock base plate W × D | **≈ 190 × 250** (front view 114 px, side 150 px). The plate is **narrower than the 263 mm head**, so the head overhangs it at both sides | EUIPO ×1.67 | Medium |
| Dock base plate thickness | ≈ 12–15 | EUIPO | Medium-low |
| Dock tower (white bin housing + plinth) W × D | **≈ 170 × 155** (102 px × 93 px) | EUIPO ×1.67 | Medium |
| Dock tower height, floor → top face | **≈ 390** (370–410). Top face nearly flat in the EUIPO views, slight rearward slope in the TR side drawing | EUIPO 235 px ×1.67; TR p4 | Medium |
| Plinth (dark louvred band) height above the plate | ≈ 140–155 (≈ 0.4 × tower) | EUIPO 93 px incl. plate | Medium |
| Charging post (column) W × D | ≈ 53 × 65 (32 × 40 px), rounded rectangle; rises from the tower's front face, offset to the front so that its front face is roughly flush with the tower front | EUIPO | Medium-low |
| Cradle head W × H × fore-aft | ≈ 107 × 115 × 130 (64 × 70 × 78 px). The cup projects **forward** of the post | EUIPO | Medium-low |
| Post visible above the tower top | ≈ 340 (from the tower top at ≈ 390 to the cradle bottom at ≈ 735) | derived | Medium-low |
| Cradle top above floor | ≈ 850 (the cup wraps the handheld's bottom/socket, at 0.812 m on the stick + ~0.01 plate) | stick stack + S1 p14 3/4 | Medium |
| Odour dial Ø | ≈ 55–65 (about 1/3 of the tower depth) | S1 p4, EUIPO | Low-medium |

---

## 5. Lights, controls and displays

### 5.1 Handheld round screen (end face of the purple cap, facing the user)
A round, glossy black disc with an **LED ring** around its outer edge. On the user's unit the ring glows **purple/violet**; in the drawings the ring arc is brightest at the left and right sides.

There are **two documented icon layouts**:
- **Variant A — TR manual S1 p8 / p11 / p19** (matches the Turkish market):
  - top centre: **DETECT** icon (concentric-circle target, in a white ring);
  - upper left: **ECO** (leaf in a circle); upper right: **BOOST** (swirl/fan in a circle);
  - centre: **water-drop** icon (unlabelled; probably dirt/debris);
  - a horizontal white **battery bar** across the middle (full / half (gradient) / low (blinking, short) / none);
  - below the bar: a **battery-with-bolt** icon and a small **"FO"** text icon to its right;
  - bottom: a **pill-shaped power button** (⏻) with a light outline.
- **Variant B — UK guide S2 p12–13 and US QSG S3**:
  - top: a battery icon inside a bracket frame "[ ▭ ]";
  - middle row: ECO leaf · DETECT target (large) · BOOST swirl;
  - bottom: the power pill.
  - No drop icon and no bar.
- **Recommendation:** model Variant A (TR market). The reference-director's close-up photo should confirm it.

**Ring colours in DETECT** (S2 p13, S3):
- **white** = no heavy debris, low suction;
- **pink / light purple** = debris being cleaned, medium suction;
- **purple** = heavy debris, high suction;
- **flashing purple** = nozzle clog/stall.

The QSG notes that the "Hand Vacuum UI and Nozzle Lights are Synched". Error codes flash the icons at 0.5 s (table in S1 p19).

**Mode selection:** a **trigger on the underside of the grip**, next to the motor body (S1 p11, purple on the user's unit). Modes are ECO → DETECT → BOOST. Power is the on-screen button.

### 5.2 Battery pack
The battery is the lower bar of the handle loop and slides out downward/backward (S1 p10). It has a **small round LED dot** near its rear end:
- pulses yellow at 0–75 %;
- pulses green at 75–100 %;
- white when full, then turns off.

The IP1000 series also has a DC jack hole on the underside of the handle.

### 5.3 Floorhead (DuoClean Detect) lights and sensors
- **Floor lights ("Light Detect"):** headlight emitters at **both front corners**, at the lower front of each side cap. They fire low cones forward and sideways (S2 p13 "LIGHT DETECT"). The QSG and the user frames show **purple/violet light bars at the bottom front corners**, and the colour follows the DETECT ring. The user frames also show white floor illumination on carpet.
- **Light Detect sensor:** small round window on the top deck, left of the neck (S1 p17 Fig. 2).
- **Edge Detect sensor:** small oval window on the outer face of each side cap, between the round end disc and the wheel (S1 p17 Fig. 3).
- **Floor Detect:** round sensor dot on the underside, right of the neck (S2 p21 Fig. 4).
- **Edge indicator:** the headlight on the side where an edge is detected lights up (S1 p11).

### 5.4 Dock
- **The round item on top is the Odour Neutraliser dial, not a screen** (S1 p4–6, S2 p8–9, EUIPO 015044754).
  - Its face carries the "ODOR NEUTRALIZER TECHNOLOGY" text (UK "ANTI-ODOUR" with a hexagon logo), a padlock icon, a "+ / –" wedge-bar intensity arc and a triangle index.
  - It has a **flip-up loop handle** and **teal alignment arrows**.
  - On the user's unit it reads as a black disc with teal/green marks.
  - It has no electronics: the manual documents no dock status display.
- **Dust-bin-full indicator:** a black, rounded, pill-shaped light window on the dock top, near the post. It carries a bin-with-dust icon and a moon icon (quiet mode). It lights when the 2 L bin is full (S1 p14).
- **Quiet-mode slider:** on the cradle head / top of the post. A small rectangular slide switch: fan icon on the left (auto-empty), moon icon on the right (quiet = charge only).
- **Charging contacts:** 2 square pads inside the cradle front (S1 p9 / p14).
- **Dock bin:** a removable white rectangular box with a top handle and release. A side release button opens the bottom flap (S1 p13).
- **Filters:** a rear lower louvred filter door with a round button at its bottom, a post-motor filter cassette, and an exhaust foam (rounded triangle) above the fan under the bin (S1 p16).
- **Base plate:** flat, with a raised accessory peg/clip. The power cord enters at the lower rear of the plinth.

---

## 6. Subsystem notes (counts and shapes from the drawings)

### 6.1 Handheld
- **Layout.** The motor cylinder is coaxial with the bin and the wand.
  - From the top: the ribbed purple cap (vertical flutes, ~20–24 visible around the half-circumference in the TR drawings) with the screen on its end face; then the motor section with **vent grilles** on both sides (perforated dot array of ~6 rows); then a silver collar with the "Shark" logo; then the clear bin with a purple top ring and a front window; then the grey socket at the bottom.
  - The handle is a **closed loop** to the rear. Its upper bar is the grip (with the mode trigger underneath near the body). Its lower bar is the battery, with an oval recess panel. The rear upright joins both bars.
- **Releases.**
  - Dust-cup release: a button at the front-top of the bin (S1 p17 inset); the cup slides out downward.
  - Bin-empty: a button opens the bottom flap.
  - HEPA post-motor filter: pull tab at the side/rear of the motor (S1 p15).
- **Inlet** (S1 p17 Fig. 1): a round airway with the Dirt Detect sensor ring, 4 electrical pins below it, a bin door hinge, and a latch tab.

### 6.2 Wand + MultiFLEX
- Straight tube (bronze on this unit) with grey moulded ends.
- **Top collar:** an oval release button with a round centre dot, on the front.
- **Hinge** at the upper third: a knuckle with a **round pivot cap** on the side (purple on the user unit) and a **latch on the rear** (pill-shaped slider, S1 p12 inset).
- **Bend:** folds forward. In storage pose the handheld hangs down alongside the wand (S1 p12 right).
- **Lower collar:** grey, with an oval release button on the front, clicking onto the head's neck.

### 6.3 Floorhead (DuoClean Detect)
- **Two rollers** (TR page: "iki fırça rulosu"):
  - a **front soft roller** (turquoise, with diagonal/helical stripes in the drawings and a yellow strip in the user frame), removable from the side via a release button on the side cap (S2 p20);
  - a **rear bristle brushroll** with the **chevron V** anti-hair-wrap pattern (S1 p18 / p16 Fig. 3).
- **Side caps:** a "lozenge/teardrop" profile with a round end disc (the roller bearing cap) and a small oval Edge sensor. A large wheel sits behind each cap.
- **Underside:**
  - a rear squeegee plate held by **4 small screws** along the plate;
  - **2 large quarter-turn locks** either side of the neck;
  - **2 rear wheels** flanking the neck duct;
  - the Floor Detect dot.
- **Top deck:**
  - a clear window over the soft roller;
  - a "DETECT" printed strip (turquoise in the user frame) along the front;
  - a "Shark" logo on the neck plate;
  - the Light Detect round window.
- **Neck:** a two-axis swivel with a ribbed flex hose visible.

### 6.4 Dock
Use EUIPO 015044754-0001 front/side/rear views as the blueprint, and S1 p4 / p13 / p14 / p16 for the details.
- **Post:** a separate dark-grey column, which slides over the tower's front stub and cannot be removed once fitted.
- **Cradle head:** an open, U-shaped cup facing the user. Contacts sit inside the front. The quiet slider sits on its rear upper face.
- **Tower:**
  - a white rectangular block with rounded vertical edges;
  - its top slopes slightly down toward the rear and carries the odour dial (front-right) and the bin handle recess;
  - a bin-level window/slot on the side.
- **Plinth:** a dark lower band with **fine vertical louvres all round** and a rear louvred filter door with a round button.
- **Base plate:** dark grey, flat, with rounded corners, extending forward under the floorhead.

---

## 7. How to use this file
1. **Stick.** Reuse the IP1251 geometry from `PRODUCT_REFERENCE.md` §4 unchanged, then apply the IP3251 colourway.
2. **Envelope.** System 1177 H × 263 W × 472 D. The cradle must catch the handheld socket at about 0.81–0.83 m.
3. **Dock shapes.** Model them from EUIPO 015044754-0001 plus `tr_og_p-04/13/14/16`. Use the §4.2 dock table (tower ≈ 170 W × 155 D × 390 H, cradle top ≈ 850, plate ≈ 190 × 250) and calibrate against the reference-director's photos.
4. **Screen.** Use Variant A (TR). LED ring purple; white/pink/purple depending on the state.

## 8. Gaps
- **Dock absolute dimensions**: no official component dimensions exist. v1.1 scales the EUIPO orthographics with a cradle-top anchor of 850 mm (medium confidence, ±5 %). Next step: measure on the official AU side images (`sharkninja.com.au/cdn/shop/files/IP3251-*.webp`, including `IP3251-duoclean-xray.webp` and `IP3251-quite-mode.webp`, which are for the reference-director) or on any straight side photo, using head W = 263 mm as scale.
- **Spare-part dimensions** (soft roller / brushroll length and Ø, wand OD, battery bare size): the official UK spares pages carry placeholder dims, and ShopJimmy gives part numbers only. Not found.
- **Screen variant (A vs B)** on the user's actual unit: needs a close-up photo.
- **US design patents** for 29/895,331/332 were not checked (sandbox blocks patentimages). The EU dock design is enough.
- **Mode-trigger colour, LED-bar count on the nozzle corners and cap flute count:** take them from photos.
