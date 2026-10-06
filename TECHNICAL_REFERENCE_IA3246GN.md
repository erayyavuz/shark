# TECHNICAL REFERENCE — Shark PowerDetect Speed Clean & Empty, Luxe Collection, Sagewood (IA3246GN)

Owner: technical-research agent. Status: **v2 (2026-10-05)** — v2 adds the US owner's guide (S0), RTINGS measurements, US-design search result. Companion to `PRODUCT_REFERENCE_IA3246GN.md` (photos, owned by reference-director).
All files are under `assets/references/ia3246/technical/` (see `manifest.json` there: url, date, sha256, description, licence = reference only).
Nothing here is CAD-exact. Every number below carries a source and a confidence level.

Platform note: IA3246GN is a US colour/finish SKU of the **IA3000 series** (IA3240 / IA3241 / IA3242 / IA3243 / IA3246BL/BR/GN/IV share one owner's guide). The stick is also sold without the dock as the **IA1000 series** (IA1241). EU/UK/AU equivalents: IA3241EUT, IA3241UKT, IA3241ANZ. Geometry is the same platform; finish/colour differs.

---

## 1. Sources

| # | File (under `assets/references/ia3246/technical/`) | Origin | What it gives | Confidence it applies to IA3246GN |
|---|---|---|---|---|
| **S0** | **`manuals/IA1000_IA3000_US_owners_guide_EN_IA3246GN.pdf`** (+ `manual_pages/us_og_p-01..13.png`, 200 dpi spreads, `us_og_contact_sheet.png`) | US owner's guide "POWERDETECT Speed Clean & Empty Cordless Vacuum IA1000/IA3000 Series" (doc IA3241_IB_MP_Mv2), listed for IA3246GN on manualsfile.com | **Primary manual for this SKU.** Same drawings as S1 minus the UK odour dial. Names dock **XDCKIA3000NO**, battery **XIABTR540US**. Quiet mode = slider (right = on). | **High** |
| S1 | `manuals/IA3000UK_series_owners_guide_EN_IA3241UKT.pdf` (+ renders `manual_pages/ia3000uk_og_p-01..15.png`, 200 dpi, each PNG = a 2-page spread) | Official SharkNinja owner's guide "Clean & Empty PowerDetect Speed Cordless Vacuum IA3000 Series", UK English, created 2025-11-18. Mirror: `s3-eu-west-1.amazonaws.com/media.markselectrical.co.uk/manuals/IA3241UKT.pdf` | All line drawings: assembly, UI screen, LEDs, dock, filters, nozzle underside, sensors, accessories, error table | **High** for stick/handheld/nozzle/UI. **Medium** for dock (UK dock has an anti-odour dial on top; US marketing photos do not show it — see §6.4) |
| S2 | `manuals/IA3000UK_series_quick_start_guide_EN.pdf` (+ `manual_pages/ia3000uk_qsg_p-1/2.png`) | `sharkclean.ie/cdn/shop/files/IA3000UK_Series_QSG_MP_Mv4_LR_1.pdf` | Assembly overview, mode explanation, LED colours (Edge Detect / Floor Detect / Dirt Reveal), battery part number + rating | High |
| S3 | `manuals/IA3000_series_owners_guide_DE_EU.pdf` | `gzhls.at/...c47520d03ce8.pdf` (Geizhals mirror, EU multilingual edition, German pages) | Same drawings as S1 (cross-check) | High |
| S4 | `manuals/IA1000UK_series_owners_guide_EN_IA1241UKT.pdf` | Marks Electrical mirror | Same stick without dock (cross-check) | High for stick |
| S5 | sharkninja.com IA3246GN page (saved HTML in session scratchpad `ia.html`, not redistributed) | official US spec tab | Overall dims, weights, path width, bin capacity, runtime, charge time, wattage | High (official) |
| S6 | sharkninja.co.uk IA3241UKT product page + XIABTR540EU battery page | official UK spec tab | Metric dims, hand-vac weight, path width in cm, battery pack dims | High (official; battery dims probably packaging-level) |
| S7 | thegoodguys.com.au IA3241ANZ spec tab | AU retailer | H/W/D in mm, weight, box dims | Medium-high |
| S9 | RTINGS IA3241 review (rtings.com/vacuum/reviews/shark/powerdetect-speed-clean-empty-ia3241), read in browser | Lab measurements: weights, storing dims, wand reach, bin volume, runtime | High (measured, same platform) |
| S8 | EUIPO registered designs `designs/EUIPO_015094303-000{1..4}/`, `designs/EUIPO_015094332-000{1,2}/` (7 views each, 2550×3301 JPG) | `euipo.europa.eu/copla/design/data/<number>` (public register) | Orthographic + perspective line drawings of a 2024-09 SharkNinja stick / handheld / nozzle / dock family | **Low** for stick/handheld/nozzle (sibling product, see §3), **Medium** for dock layout only |

Not obtained (gaps, see §8): US design patents for this exact product (Google Patents rate-limited this session; the US applications 29/961,464 and 29/961,466 are probably unpublished/pending), spare-part dimensions for brushroll / wand / filters.

---

## 2. Extracted manual drawings — which views they provide

All paths relative to `assets/references/ia3246/technical/manual_pages/`. "p" numbers are printed page numbers. The UK guide (S1, `ia3000uk_og_*`) is listed in detail below; the **US guide (S0, `us_og_*`) has the same drawings** in this order: p-03 assembly (dock side elevation + 3/4, handheld/wand/nozzle side), p-04 battery LEDs + UI + battery side view + dock contacts + **hand-vac release button close-ups**, p-05 battery removal + UI (POWER/MODE) + upright lock + clean-indicator ring, p-06 above-floor + MultiFLEX bend/fold + dock bin removal, p-07 dock use + quiet slider + bin window + HEPA, p-08 dock filters + nozzle underside + sensors + IA3000 dust cup, p-09 blockages + error table, p-10 accessories. Prefer `us_og_*` where both exist.

| PNG | Printed pages | Views useful for modelling |
|---|---|---|
| `ia3000uk_og_p-01.png` | cover | Whole system on dock, 3/4 front line art (proportions of stick vs dock). |
| `ia3000uk_og_p-04.png` | p6 **ASSEMBLY** | **Best exploded set.** Handheld (left side elevation): vertical body/bin at front, horizontal top bar, closed loop handle at rear-top, battery grip below handle, vent slot array at top-front, release button. Flexology wand (side): straight tube, hinge knuckle with round pivot cap + unlock button ~ upper third, lower collar with release button. Floor nozzle (side): round side cap with concentric disc, rear wheel, neck yoke with two-axis swivel. Dock (side): rectangular tower body, slot window on side, lower plinth, flat base plate, charging post slides into front slot, odour cartridge on top, wall adapter. Dock 3/4: oval/rounded floor plate extending forward, accessory peg on base (front-right), crevice tool clipped to post. |
| `ia3000uk_og_p-05.png` | p8-9 | Top of dock: anti-odour dial (circular, flip-up loop handle, "+/-" arc scale, padlock icon, triangle index marks), cartridge geometry (cylindrical can, bayonet ring). **UK feature — verify for US**. |
| `ia3000uk_og_p-06.png` | p10-11 | **UI screen front view** (rounded "D"/shield-shaped black screen) + battery pack side view (long rounded capsule, release latch at top end, small oval LED window at the rear end); battery sliding out of handle grip; dock charging contacts close-up (cradle cup at top of post). |
| `ia3000uk_og_p-07.png` | p12-13 | **UI screen large** (icons positions), POWER / MODE buttons, upright-lock pose, DIRT REVEAL light cone from right front corner of nozzle, FLOOR DETECT (top view of nozzle on wood→carpet), EDGE DETECT (top view of nozzle side). |
| `ia3000uk_og_p-08.png` | p14-15 | MultiFlex/Flexology: bend angle (~90° fold), unlock button close-up (pill-shaped slider on rear of hinge, with 3 small square marks above), storage fold pose, handheld↔wand release button close-up (oval button with round dot), accessory insertion. |
| `ia3000uk_og_p-09.png` | p16-17 | Dock in use (3/4), **Quiet-mode switch** on top of charging post (rectangular slide switch, crescent-moon icon), **dust-bin window** (vertical slot with a fill-line tick on the side of the dock bin), removing dock bin (top handle, rear face with ribs/latches), bottom-door release button on bin side. |
| `ia3000uk_og_p-10.png` | p18-19 | Handheld dust-cup removal (button, pulls downward), post-motor filter cartridge with pull tab at rear of motor; dock filter door at the rear base (hatched grille panel with round button), pre-motor filter + post-motor filter stack, exhaust foam filter (rounded-triangle foam) under the dock bin with fan visible. |
| `ia3000uk_og_p-11.png` | p20-21 | **Nozzle underside (best bottom view)**, **Dirt-Detect sensor in handheld inlet (front 3/4 of handheld bottom/inlet)**, **Edge-Detect sensor on nozzle side cap**, **Floor-Detect sensor on underside**. |
| `ia3000uk_og_p-12.png` | p22-23 | Blockage views (handheld 3/4, wand ends, nozzle underside, charging post top, dock top); **labelled UI diagram** (LED ring, ECO, DETECT, BOOST, F0) and **LED error table**. |
| `ia3000uk_og_p-13.png` | p24 | Accessory line art A–N (crevice, duster crevice, flexible crevice, anti-allergen brush, multi-surface, motorised hand tool, wide upholstery, car kit, battery, pre-motor filter (round puck), post-motor HEPA (pleated cylinder), dock post-motor filter (rectangular grid), dock exhaust foam (rounded triangle), battery charging sleeve). |
| `ia3000uk_qsg_p-1.png` | QSG | Assembly, POWER / MODE, modes graphic (Clean Floor = low, Medium dirt, Heavy dirt), Additional Detect Technology panel (Edge Detect, Floor Detect, Dirt Reveal), dock charging and emptying. |
| `ia3000uk_og_contact_sheet.png` | all | overview |

---

## 3. Registered designs (EUIPO) — what was found and how well it matches

Search: Google Patents (`assignee=SharkNinja, type=DESIGN, priority ≥ 2022-06`, terms vacuum/cleaner/nozzle/docking/station/wand/battery/floor; 922 records, list in session scratchpad) → candidate families checked on the EUIPO register (which serves the actual drawings).

| Design | Product indication | Priority | Visual comparison with IA3246 hero `ia_01.jpg` / Amazon photos / S1 | Verdict |
|---|---|---|---|---|
| **015094303-0001** (stick, 7 views: L, R, front, rear, top, bottom, persp.) | Vacuum cleaners (part of) | US 29/961,464, 2024-09-05 | In-line handheld with ribbed ring + loop handle, MultiFlex-style knuckle under the handheld, slim wand. **But** floor nozzle has teardrop side caps with an LED band; IA3246's TurboPro Detect has D-shaped side caps with a round metallic disc + small oval edge sensor (see `raw/amz-oatstone-ia3246iv-main…jpg`, S1 p21 Fig 2). Ribbed ring sits at the very top on the design; on IA3246 it sits *below* the "Shark" badge band. | **Sibling / not the IA3246.** Low (≈20%). Useful only for general proportions of a SharkNinja 2024-25 stick. |
| 015094303-0002 / -0003 (handheld) | Vacuum cleaners (part of) | same | Pistol/loop layout similar to the S1 handheld side drawing, but ring position, perforation band and handle details differ. | Low (≈20–30%) |
| 015094303-0004 (nozzle) | Vacuum cleaner heads | same | Teardrop side caps — **does not match**. | Low (≈10%) |
| **015094332-0001 / -0002** (dock "holder", 7 views) | Holders for handheld vacuum cleaners (part of) | US 29/961,466, 2024-09-05 | Same architecture as the IA3000 dock: vertical charging post with cup cradle at top, rectangular tower with arched lower front, flat base plate with accessory peg; claimed part = the cradle (solid lines), rest dashed. Base plate is rectangular in the design vs rounded/oval plate in S1 p6 and photos. | **Medium (≈50%)** for dock topology & cradle; do not copy base outline. |
| 015044754-0001 (dock), 015044922-0001 (handheld), 015045103/015045106 (2023-06) | — | US 29/895,33x, 2023-06 | Earlier PowerDetect IP-series dock (ribbed base) and handhelds. | Not this product |
| 015120297-0001…0006 (2025-04) | floor-cleaning machine + dock | US 29/998,645 | Wet/dry floor cleaner. | Not this product |

US designs (Google Patents in browser, assignee SharkNinja, type DESIGN, priority ≥ 2023-10): only 21 granted, none for this product; USD1124550S1 (US 29/895,800, 2023-06) = the EU 015045103 handheld-with-hose family, USD1105672S1 (2023-08) = upright family. The US applications behind the 2024-09 family (29/961,464 stick, 29/961,466 dock holder) were not yet granted/published. (patentimages.storage.googleapis.com is blocked from this sandbox, so no US sheets downloaded.)

**Conclusion:** no design registration found that is unambiguously the IA3246 stick or TurboPro Detect nozzle. The **owner's manual drawings (S1) are the authoritative line art**; combine with the reference-director's photos. Design files kept for the dock topology and as a sibling comparison only.

---

## 4. Consolidated dimension table (mm)

Conventions: H = vertical, W = left-right (across the cleaning path), D/L = front-back. "Photo-derived" = measured on the official front render `ia_01.jpg` (2070 px square, near-orthographic, head plane ≈ 0.61 mm/px if head W = 260 mm; handheld plane ≈ 0.62–0.64 mm/px). Perspective makes photo-derived numbers ±5–8 %.

### 4.1 Official / retailer numbers

| Item | Value | Source | Confidence |
|---|---|---|---|
| System (stick in dock) H × W × L | **1140 × 260 × 375** (44.88 × 10.24 × 14.76 in) | S5 sharkninja.com IA3246GN | High (official) |
| Same, UK | 1140 × 260.1 × 374.9 | S6 IA3241UKT | High |
| Same, AU | 1145 × 260 × 355 | S7 IA3241ANZ | Medium-high |
| Same, **measured** (stored on dock) | **1138 × 261 × 382** (44.80 × 10.28 × 15.04 in) | S9 RTINGS | High (measured) |
| Stick weight measured | 3.25 kg (7.16 lb); weight in hand 1.50 kg | S9 | High |
| Wand reach measured | min 0.39 m, max 0.99 m (RTINGS "wand length" = reach of handheld+wand configuration, not tube length) | S9 | Medium (definition) |
| Dirt compartment measured | 2.30 L (dock) | S9 | High |
| Battery life measured | 14 min (BOOST, floor) – 74 min (ECO, no tool); recharge 255 min | S9 | High |
| Cleaning path width | **211** (8.3 in; UK 21.08 cm) | S5, S6 | High |
| Total system weight (stick + dock) | 6.44 kg (14.2 lb) | S5, S6 | High |
| Stick weight ("lightweight at 7 lb") | ≈ 3.2 kg (AU 3.2 kg; US "at 7 lbs") | S5 marketing, S7 | High |
| Hand-vac weight | 1.59 kg (3.5 lb) | S5, S6 | High |
| Hand-vac dust cup | 0.47 L (US "0.5 qt") | S6, S5 | High |
| Dock dust bin | 2 L, "up to 45 days" | S5 compare table, S1 p17 | High |
| Battery | XIABTR540US (US) / XIABTR540EU, 18 V, 3750 mAh, 67.5 Wh, Li-ion | S2 QSG, S6 | High |
| Battery pack L × W × H | 136.9 × 84.1 × 65 (listing; likely packaging) | S6 | **Low** for the bare pack |
| Runtime / charge | up to 60 min (ECO, non-motorised tool); full charge ≈ 6 h (UK page 5 h) | S1 p10, S5, S6 | High |
| Motor | 350 W body motor, 115 W nozzle, 18 V | S1 p2 | High |
| Dock evacuation cycle | 15 s | S1 p16 | High |
| Box (AU) | 700 × 340 × 290, 9 kg | S7 | Medium |

### 4.2 Component dimensions (derived — use as modelling targets, refine against photos)

| Component | Dimension | How derived | Confidence |
|---|---|---|---|
| Floor nozzle overall width | **≈ 255–262** | Official W = 260 is the widest element (head ≈ dock base); hero: head 427 px vs path window ≈ 345 px → 211 × 427/345 ≈ 261 | Medium-high |
| Nozzle brush window (clear cover opening) | ≈ 211 wide | = cleaning path | Medium-high |
| Nozzle front height (floor → top of clear cover) | ≈ 55–62 | hero 1790→1880 px ≈ 90 px × 0.61 | Medium |
| Nozzle depth (front lip → rear wheel back) | ≈ 120–135 | AU D 355 / US L 375 is dock-base driven; side drawing S1 p6 ratio W:D of nozzle ≈ 2:1 | Low-medium |
| Side cap (D-shape) height × depth | ≈ 55 × 60, round disc Ø ≈ 35 | photo `amz-oatstone…main` relative to head height | Low-medium |
| Brushroll diameter | ≈ 45–50 (copper roll, chevron fins) | S1 p21 underside ratio to nozzle width | Low |
| Stick overall height (floor → top of handheld, not docked) | **≈ 1080–1110** | hero 112→1880 px = 1768 px × 0.61–0.63 | Medium |
| Handheld body (bin section) width | ≈ 88–92 | hero 968→1108 px = 140 px × 0.63 | Medium |
| Handheld top cap → bottom of bin | ≈ 290 | hero 112→565 px ≈ 453 px × 0.63 | Medium |
| Copper cyclone ring band height | ≈ 22–26 | hero ≈ 245–285 px | Medium |
| Wand visible tube width (front) | ≈ 32–34 | hero copper tube 1013→1063 px = 50 px × 0.64 | Medium |
| MultiFlex hinge centre height (stick upright) | ≈ 610–630 above floor (hero hinge ≈ 880 px; floor ≈ 1880 px; 1000 px × 0.62) | hero | Medium-low |
| Wand overall (handheld socket → nozzle neck) | ≈ 700–740 | hero 565→1720 px ≈ 1155 px × 0.62 | Medium-low |
| Dock tower width (front) | ≈ 165–175 | hero 905→1170 px = 265 px × 0.63 (tower is behind stick → real size slightly larger) | Medium-low |
| Dock tower body H (excluding post) | ≈ 470–490 | hero 1015→1775 px ≈ 760 px × 0.63 | Low-medium |
| Dock base plate | ≈ 260 W × 355–375 D | official W/L of system (base plate sets footprint) | Medium |
| Dock bin capacity | 2 L | official | High |

---

## 5. Controls, lights and indicators (from S1 / S2)

### 5.1 Handheld UI screen (rear face of handheld, facing the user)
Shape: a rounded black "shield/D" panel, wider at the top, flat-ish bottom, with a glossy black face. Layout (S1 p12-13, p23 labelled):
- **LED ring** — a thin illuminated arc following the outer edge of the screen (top and both sides). Colours: **white** = no heavy debris / normal; **deep purple** = heavy debris detected, suction boosted; **light purple** = debris being removed; **flashing purple** = nozzle clog/stall (error).
- **DETECT icon** — top centre, concentric-circles (target) icon; lit when DETECT mode active.
- **ECO icon** — upper left, leaf in circle.
- **BOOST icon** — upper right, swirl/turbine in circle.
- Centre: water-drop icon below DETECT (unlabelled in the table; likely odour/fragrance or dirt indicator — treat as a dim icon).
- **Battery bar** — a horizontal white light bar across the middle (gradient length = charge: full / half / low (blinking) / none).
- **Battery/charge icon** (battery with bolt) under the bar, and a small **"F0"** icon to its right (fault code).
- Two touch/press buttons at the bottom edge, separated by a vertical split: **POWER** (left, ⏻ symbol) and **MODE** (right, fan symbol). They are grey segments forming the bottom of the screen.
- Modes cycle ECO → DETECT → BOOST.

### 5.2 Battery pack LED
Small oval LED window on the battery end: pulses **yellow** 0–75 % charge, pulses **green** 75–100 %, **white** = fully charged, then turns off. Charging lights blink when correctly docked.

### 5.3 Floor nozzle lights (TurboPro Detect)
- **Dirt Reveal / Reveal Technology headlight**: a light at the **front right corner** of the nozzle (side cap front face) casting a low, angled **blue** light across hard floors (S1 p13 "On hard floors ONLY"; US copy "precisely angled blue light"). Photos also show a column of small dot-matrix lights on the front edge of the side cap (verify count in photos).
- **Edge Detect sensor**: small oval window on the outer face of the side cap, behind/next to the round disc (S1 p21 Fig 2).
- **Floor Detect sensor**: small round sensor on the underside, rear-left of the brush chamber near the neck (S1 p21 Fig 3).
- **Dirt Detect sensor**: inside the handheld inlet (acoustic/optical ring around the airway, S1 p21 Fig 1).
- Error table mentions "Headlight LEDs" (Edge-detect error lights F0 + ring + headlight).

### 5.4 Dock indicators / controls
- **Quiet Mode** slide switch on top of the charging post (crescent-moon icon) — dock-and-charge without auto-evacuation.
- **Dust-bin window**: vertical slot on the dock bin side with a fill line.
- Dock bin: carry handle on top, side **bottom-release button**.
- Filter door at the rear bottom of the dock with a press button at its bottom.
- (UK) **Anti-odour dial** on top of the dock beside the post: circular, flip-up loop handle, teal alignment arrows, "+/−" intensity arc, padlock symbol. **Not visible in US photos** — default: omit for IA3246GN unless reference-director's photos show it.
- No status LEDs on the dock are documented in the manual (charging status is shown on the handheld).

---

## 6. Subsystem notes (details visible in drawings: holes, vents, seams, buttons, counts)

### 6.1 Floor nozzle (TurboPro Detect) — S1 p6, p13, p20-23; photos
- Top: clear polycarbonate dome cover over the full brush chamber, black frame around it, "TURBOPRO DETECT" text front-left on the cover, front bumper/comb lip with small transparent teeth/combs along the bottom front edge (underside shows ~10 small hook/comb features along the front edge, S1 p20/21).
- Brushroll: copper/orange roll with **chevron (V) fin pattern** pointing to the centre (self-cleaning comb), visible through cover (S1 p20 shows the chevron converging at centre).
- Underside (S1 p20, p21 Fig 3): rear squeegee strip held by **3 quarter-turn screws** (left, centre (larger, in the neck intake), right); 2 tall rear wheels flanking the neck; floor-detect sensor dot left of the neck; small front rollers/bumps row.
- Side caps: dark grey D-shape, **round metallic disc** (finish colour: copper on Sagewood) with an **oval edge-sensor window** behind it; right cap carries the headlight at its lower front corner.
- Neck: grey yoke with "Shark" logo on the top deck plate, dark ribbed flexible hose visible inside the neck, two-axis swivel; **nozzle release button** at the rear/bottom of the wand collar (pedal-like).
- Two rear wheels (diam ≈ 30–35 mm est.) at the neck sides.

### 6.2 Handheld — S1 p6, p10, p12, p18, p21
- Front elevation (hero): sage top cap (rounded, slightly domed) → dark textured/fabric-look band with white "Shark" wordmark → "POWERDETECT SPEED" text strip → **ribbed copper cyclone ring (≈ 50–60 vertical ribs visible across the front half; count from photo)** → clear bin window showing the inner cyclone shroud/mesh and a vertical inlet duct → sage lower collar with front latch button.
- Side (S1 p6): vertical body; top horizontal bar with an array of **vent slots** (≈ 10–12 parallel slots) at the front-top; closed **loop handle** at rear-top; **battery pack** forms the lower rear grip, slides up into the handle compartment (release latch at the bottom/front of pack).
- Rear: UI screen (§5.1) at the rear end of the top bar, facing the user.
- Dust-cup release button on the side; dust cup slides downward to remove (S1 p18); post-motor filter cartridge pulled out by a tab at the rear of the motor housing.
- Inlet (bottom, S1 p21 Fig 1): round inlet with the dirt-detect sensor, rectangular bin door below, latch tab, electrical contact pins for wand.

### 6.3 Wand + MultiFlex (Flexology) hinge — S1 p6, p14-15
- Copper anodised aluminium tube, dark grey moulded ends; vertical "POWERDETECTSPEED" print on the front of the tube (hero).
- Top collar: oval release button with a round dot (front), clicks into handheld.
- Hinge ≈ upper third: dark grey knuckle with **round pivot cap** on the side, copper accent band at the knuckle (hero), **unlock button on the rear** (pill-shaped slider, three small square marks above it). Folds forward ≈ 90°+ to lie the handheld against the wand for storage / under-furniture.
- Lower collar: dark grey, oval release button (front), round copper disc badge on the front of the nozzle neck connector (hero, ~Ø 30 mm).
- Electrical contacts run through the wand (headlights depend on the connection).

### 6.4 Auto-empty dock — S1 p6, p11, p16-19, p22; S8 015094332
- Parts: **dock base plate** (rounded/oval floor plate extending forward under the nozzle, with a raised **accessory peg** at the front-right corner), **dock body/tower** (rounded-rectangle section; lower plinth darker colour with an arched front recess; upper removable **dock dust bin** with vertical window), **charging post** (separate part, slides into a slot at the front of the dock until it clicks; latch on its back), **cradle** cup at the top of the post (receives the handheld bottom; charging contacts inside), **quiet-mode switch** on top of the post.
- Rear base: filter door (hatched grille) with a round button; inside: dock post-motor filter (rectangular grid) + exhaust foam filter (rounded triangle) under the bin, fan visible.
- Power: external wall adapter → cord plugs into the dock base side.
- Dock bin: top carry handle, bottom flap door, side release button.
- US vs UK: UK adds the anti-odour cartridge dial on the dock top. **Confirmed by the US guide (S0): no odour dial in the US IA3000** (assembly steps 1-5 only, crevice tool stored on a mount on the dock). US photos (`raw/sn-IA3000_Series_5050_Auto-Empty.jpg`) show a plain dock top with a small control near the post — **model the US variant**.
- US dock part number XDCKIA3000NO. Quiet mode: slider on top of the charging post, slide right = Quiet on.

---

## 7. How to use this file
1. Model to the official envelope first: system 1140 H × 260 W × ~370 D; nozzle ≈ 260 W, path 211.
2. Use `manual_pages/ia3000uk_og_p-04.png` (side elevations) and `p-11.png` (underside) as blueprint underlays; scale them to the dimensions in §4 (manual drawings are not to scale between parts).
3. Use the reference-director's photo set for colours, finishes and the exact rib/dot counts.
4. Do not use the EUIPO stick/nozzle drawings as blueprints (sibling product).

## 8. Gaps / next steps
- Exact US design patents (US 29/961,464 & 29/961,466 likely pending; also any 2025 filings) — retry Google Patents / USPTO ppubs once rate limit clears.
- Part dimensions (brushroll length/Ø, wand length/OD, HEPA filter Ø×H, pre-motor foam Ø, dock filters) — no spare-part listing with measurements found yet.
- Utility patents with dimensioned figures (edge detect / dirt reveal / dock evacuation) not pursued — Google Patents rate-limited; low value vs the manual drawings.
- Dot-matrix light count on the nozzle side cap and copper ring rib count: take from the reference-director's close-up photos.
