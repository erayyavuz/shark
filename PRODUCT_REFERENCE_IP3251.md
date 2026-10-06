# PRODUCT REFERENCE — Shark PowerDetect Clean & Empty IP3251 (TR: IP3251EUT)

Owner: reference-director · **v2 (2026-10-05)**. Supersedes the IA3246GN pack for the current target. `PRODUCT_REFERENCE.md` (IP1251) and `PRODUCT_REFERENCE_IA3246GN.md` are left as they are.

**Image pack:** `assets/references/ip3251/`

| Folder or file | Contents |
|---|---|
| `user/` | The user's 6 video frames. **These decide the colourway.** |
| `raw/` | 78 official and spare-part stills |
| `frames/` | 116 video frames and crops |
| `sheets/` | 5 labelled contact sheets |
| `manifest.json` | 205 entries, each with url, date, sha256, colourway, what it shows, and a "reference only" usage note. Its `notes` block lists the videos watched and the method. |

**Usage: reference only.** The images are SharkNinja, retailer and video-creator copyright. Never ship these files or textures derived from them.

`TECHNICAL_REFERENCE_IP3251.md` (technical agent) covers the manuals, part numbers, EUIPO designs, battery and screen-state logic, and dock dimensions from drawings. That material is cross-referenced here, not repeated.

**Status codes**

| Code | Meaning |
|---|---|
| **U** | Seen in the user's frames |
| **O** | Seen in official or third-party IP3251 imagery |
| **O\*** | Seen only on the IP1251 sibling (same stick hardware) |
| **I** | Inferred |
| **C** | Sources conflict. The choice made and the reason are given. |

**Reference IDs** are file stems, for example `tr-ip3251eut-01`, `cl-eut-01`, `vid-UDDjkrKD7Mk-t0156.0` (video ID plus time in seconds) and `user-video-1663`. Video URL: `https://www.youtube.com/watch?v=<id>&t=<s>`.

---

## 0. Identity

| Item | Finding | Status |
|---|---|---|
| TR retail page | `sharkninja.com.tr/products/shark-powerdetect-clean-empty-sarjli-dikey-supurge-gold-ip3251eut`: tag **IP3251EUT**, "PowerDetect Clean&Empty Auto-Empty Sistemli Pet Başlıklı", 17 images (`tr-ip3251eut-01…17`). | O |
| The slug the user named | `/products/shark-powerdetect-clean-empty-mor-siyah` is tagged **IP1251EUT** (purple wand, no dock). It only *links* the shared IP1000/IP3000 manual `IP3251_1.pdf`. Its 6 images are saved as `tr-morsiyah-ip1251-*` and are **not** the IP3251 colourway. | O (C with the slug name) |
| Sibling listings | All show the same geometry and colours. 3D viewer asset `IP3251UKT_3D` exists but has no licence and was not downloaded. | O |
| — UK IP3251UKT | Cloudinary `cl-ukt-01`, `cl-ukt-gallery_02…15` | |
| — US IP3251 | `cl-na-01…12` | |
| — EU | front render `cl-eut-01` | |
| — PDP modules | `pdp-*` | |
| Stick hardware | Identical to IP1251 (IP1000 series). The geometry in `PRODUCT_REFERENCE.md` §4 still applies. Only colours and the wand finish differ. | O (technical §0) |
| User unit | `user-video-1663…1668`: same SKU, TR retail. | U |

## 1. Official dimensions and scale

| Quantity | Value | Source |
|---|---|---|
| Docked system H × W × D | **1177 × 263 × 472 mm**. W = floorhead width; D = head front → base-plate rear. | UK PDP spec table "26.29 L × 47.19 W × 117.7 H cm". US gives 10.24 × 18.5 × 46.46 in (= 1180 H). |
| Stick alone | 1158 × 263 × 393 mm, 3.71 kg | TR / technical §4.1 |
| Weight, stick + dock | 8.4 kg | UK |

### Front-ortho stations (`cl-eut-01`)

Method:
- Alpha bbox runs y 121–1951 = 1830 px. Setting that to 1177 mm gives **1.555 px/mm** at the wand plane.
- Perspective magnifies the floorhead front by about 10 % (it measures 286–290 mm; the real width is 263 mm).
- The dock is about 3 % small (it sits behind the stick).

| Height above floor (mm) | Width (mm) | Part |
|---|---|---|
| 1177–1130 | 82 → 89 | Purple fluted end cap. Its top face is the round screen, pointing up when docked. |
| 1130–1115 | 89–91 | Champagne "POWERDETECT" label plate band |
| 1115–1055 | 91 | Gunmetal motor body with slot vents (both sides) |
| 1055–1045 | 91 | Brushed-silver "Shark" frame top |
| 1045–1015 | 91 | Purple ring at the bin top |
| 1015–905 | 91 | Clear bin with silver cyclone shroud; silver frame on both sides |
| **≈ 900–830** | **120** | **Dock cradle cup** (graphite) gripping the bin base |
| 830–590 | 70 | Graphite dock post behind. Upper wand coupling and MultiFLEX hinge in front: purple discs at ≈ 760–790, release button ≈ 710. |
| 590–540 | 70–77 | Top of the champagne wand |
| **≈ 525** | 204–208 | **Top of the white dock tower** |
| 525–≈235 | 204–208 (≈ 200 real) | White tower front. "POWERDETECT" badge at its upper-right front corner. |
| ≈ 235–15 | 213 | Graphite lower body ("plinth") |
| 15–0 | — | Graphite base plate |
| 100–0 | 282–290 (263 real) | DuoClean Detect floorhead |

### Side-photo cross-check (`vid-JCGXMfx8SG8-t0020.3`, a near-side real photo)

Scale is set by the IP1251 wand tube, 298 mm = 450 px, giving 0.662 mm/px. Measured at that scale:
- floor → tower top ≈ **500 mm**
- graphite lower body ≈ **180 mm** tall
- tower depth ≈ **195 mm**
- base plate depth ≈ **310 mm** (some perspective)

**Dock size: conflicting (C).**
- `TECHNICAL_REFERENCE_IP3251.md` §4.2 gives tower ≈ 170 W × 155 D × 390 H and cradle top ≈ 850 (EUIPO orthographic, anchored at an assumed 850 mm cradle top).
- The official render and the side photo agree with each other on tower ≈ **200 W × ≈195 D × 500–525 H** and cradle top ≈ **890–900**.

**Recommendation:** use 200 × 195 × 510 and cradle top 890. The bin base must sit inside the cup. The stick's handheld bottom is at 0.812 m plus the plate thickness, and the cup wraps about 70 mm of bin. EUIPO drawings are design-registration views, not to scale.

---

## 2. HANDHELD

**Best references:**
- Colour: `crop-user1663-handheld` (U, colour truth)
- Screen ON: `user-video-1668` (U), `vid-UDDjkrKD7Mk-t0156/0159`, `vid-ph7l7p4JMsA-t0664/0680`, `vid-wuXUwo0Itxg-t0445`, `crop-tr01-handheld-screen-inset`
- Cap, plate and vents: `vid-UDDjkrKD7Mk-t0006/0231/0234`
- Side and grip: `vid-UDDjkrKD7Mk-t0012/0165/0168`, `vid-JCGXMfx8SG8-t0072.5`
- Bin: `tr-part-cyclone-toz-haznesi-ip3251eut-1`, `cl-na-04`
- Battery: `tr-part-batarya-ip3251-serisi-1`
- Front ortho: `crop-cl-eut-01-handheld-front`

**Sheet:** `sheets/sheet-handheld.jpg`

**Geometry:** the IP1251 handheld unchanged (end cap Ø 90 × 53 mm, body 90 W × 104 D, handle loop 208 × 162, battery 152 × 40). See `PRODUCT_REFERENCE.md` §4.

| Feature | Position, shape and size | Colour and finish | Count | Refs | Status |
|---|---|---|---|---|---|
| End cap | Cylinder Ø 90, 53 long, at the rear end. Long **tapered flutes/grooves** run axially and slightly helically. They are widest at the rim and fade toward the body. | **Purple, satin anodised-metal look.** User lit #4b348b, shade #260e41. Render #3f2859. Video lit up to #7d4fd0. | ≈ 20–24 flutes (8 visible per half) | U 1663, `t0006`, `t0234` | U/O (count I ±3) |
| Cap face rim | Outer rim of the end face has **notched "crown" serrations**: small triangular notches every ≈ 22–25°. | Purple | ≈ 14–16 notches | `t0156`, `ph7-t0664`, render inset | O (count I) |
| Thin gloss ring | Narrow (≈ 3 mm) bright **gloss purple band** where the cap meets the body | Gloss violet, near-chrome | 1 | `t0234`, U 1663 | O/U |
| Small cap button | Small round purple button on the cap rim, at the top (in the docked pose), on the grip side | Purple | 1 | U 1663 (top-left of cap) | U. Function I: likely the filter-cap release. Technical §6.1 may confirm. |
| Round screen | Black gloss disc (≈ 60–65 mm) filling the cap face, with a **purple LED ring** inside the rim. Full layout in §6. | Glass #0b0b10 | 1 | §6 | U/O |
| Power button | Rounded-rect/pill button at the bottom of the screen face (grip side). Dark smoked shell with a purple ⏻ icon, lit purple in use. | Dark violet-black; icon purple emissive | 1 | `ph7-t0680`, inset | O |
| Champagne label plate | Wrap-around band, ≈ 15 mm tall, just below the cap. "POWERDETECT" in dark grey ("POWER" bold, "DETECT" light). Its top edge has a shallow V notch at the front. | **Champagne/brushed gold**: render #aaa18b, photo #7c7664 shade | 1 | U 1663, `t0006`, `t0234` | U/O |
| Motor body | ≈ 60 mm long section between the plate and the "Shark" frame | **Gunmetal/titanium grey**, fine satin. User #68676c, render #77756f. | — | U, render | U/O |
| Vent grilles | One recessed panel on each side face (left and right of the screen axis). **Rounded-end slots (stadium), ≈ 2 × 9 mm, in a staggered brick pattern.** | Through-slots, dark inside | ≈ 4–6 slots × 13–14 rows per side | `crop-user1663-handheld`, `t0234` crop, `t0231` | U/O (count ±2) |
| "Shark" frame | Brushed-silver frame wrapping the front of the bin: an arch over the bin top plus two side rails. Large italic "Shark" wordmark at the top front. | Brushed aluminium-look #75777d…#c9ccca. Logo raised, gloss. | 1 | U 1663 | U |
| Purple bin ring | Ring around the bin top, ≈ 30 mm, partly hidden behind the frame | Purple, satin | 1 | U 1663, render | U/O |
| Clear bin | Cylinder Ø 90, with a silver cyclone shroud and mesh visible inside. Bottom-opening flap with a latch. A yellow QR sticker on retail units is a factory label: do not model it. | Clear PC, slight cool tint | 1 | `cl-na-04`, `tr-part-cyclone…` | O |
| Grip loop | Loop behind the motor. The grip is dark charcoal; its frame is gunmetal. "Shark" is printed (light grey) on the outer face of the battery bar. | Grip #2a2a2e soft-touch | 1 | `t0165`, `t0168` | O |
| Mode trigger | Purple trigger under the grip, next to the body | Purple | 1 | `t0168` (pink-purple tab), technical §5.1 | O |
| Battery | Lower loop bar, black/charcoal, with a light-grey "Shark" panel and a round LED dot at the rear end | Charcoal + silver panel | 1 | `tr-part-batarya…` | O |
| Grip blue edge light | A cyan line along the inner grip edge in Teknosa frames. Most likely a reflection of the blue studio curtain, not an LED. | — | — | `t0168`, `t0231` | C → **do not model** |

---

## 3. WAND + MultiFLEX

**Best references:** `crop-cl-eut-01-wand-hinge` (front ortho, decal), `crop-user1663-dock-wand` (U colour), `tr-part-flex-sap-ust-sarj-1` (isolated wand), `crop-tr01-hinge-wand`, `vid-UDDjkrKD7Mk-t0213` (bent, hose), `tr-ip3251eut-12/-16/-17`, `vid-JCGXMfx8SG8-t0020.3` (real side).

**Sheet:** `sheets/sheet-wand-hinge.jpg`

**Geometry:** IP1251 unchanged. Wand tube 298 mm, section 35 × ≈ 46. Hinge pivot ≈ 0.664 m above the floor. Pivot caps Ø 23. Hinge 63 wide with caps.

| Feature | Detail | Colour and finish | Status |
|---|---|---|---|
| Wand tube | Rounded-rect aluminium extrusion | **Champagne-gold / bronze metallic.** Renders read pale champagne (#a49c86 … #b6ad95). Real photos and video read a deeper **bronze-gold** (user video #71635c shade; `JCG-t0020.3` lit ≈ #b08a50 / shade #806340). **Proposed albedo #a68d64**, metallic 1, roughness ≈ 0.35, brushed along the length. | U/O, C (render vs photo: use the photo look) |
| Wand decal | "**Shark POWERDETECT**" in dark grey (#4a4a4a). Vertical on the front face, reading top → bottom. "Shark" bold italic; "POWER" bold, "DETECT" light. Upper half of the tube. | Dark grey print | O (`cl-eut-01`, `tr-part-flex…`, `tr-ip3251eut-16`) |
| Upper coupling + hinge housing | Gunmetal grey (#5a5a5e … #77756f). A dark stadium release button on the front, about 50 mm below the handheld. | Satin | U/O |
| MultiFLEX hinge | 3-knuckle barrel. **Purple discs on both side ends** (≈ Ø 23). A black corrugated hose shows when bent. The latch is at the rear. | Discs purple satin with a spun finish | U/O |
| Lower collar | Gunmetal, with a stadium release button | Gunmetal | U/O |
| Neck disc | Large purple round disc on the neck front (≈ Ø 34), spun/radial finish | Purple | U/O (`cl-eut-01`, U 1663) |

---

## 4. FLOORHEAD — DuoClean Detect

**Best references:**
- Top view, colour: `crop-user1663-floorhead` (U)
- LEDs: `user-video-1664/1665/1666`, white `user-video-1667`
- Front: `crop-cl-eut-01-floorhead-front`, `vid-UDDjkrKD7Mk-t0189/0192`, `vid-cHkhhEh7AuE-t0009` (headlight ON)
- Top deck: `vid-JCGXMfx8SG8-t0176.9` (Shark plate, violet strip, EDGE DETECT print, light sensor)
- Underside: **`vid-wuXUwo0Itxg-t0160`**, `vid-2Ockr0C4Jdw-t0084/0088`
- Side cap: `vid-wuXUwo0Itxg-t0340`, `vid-JCGXMfx8SG8-t0139.2/0171.1`
- Violet glow: `vid-YVHoHgc5bu8-t0013`, `vid-ph7l7p4JMsA-t0256/0520`
- 3/4 render: `crop-tr01-floorhead`

**Sheet:** `sheets/sheet-floorhead.jpg`

**Geometry:** IP1251 unchanged. Width 263, body depth 132, front height 76, rear wheels Ø 47.

| Feature | Position, shape and size | Colour and finish | Count | Refs | Status |
|---|---|---|---|---|---|
| Chassis / top deck | Low box with angular facets | **Gunmetal grey.** Photo #848380 lit, #6a6f71 shade. User video looks darker, about #58595f. | — | `JCG-t0176.9`, U | O/U |
| Clear top cover | Long window over the rear soft roller, the full width between the side caps | Clear PC | 1 | U 1663, `t0189` | U/O |
| **Rear roller (soft)** | Large-diameter soft roller **behind** the front brush, seen through the top cover. **Mint/turquoise plush** with **one golden-yellow fibre strip in a wide V/chevron** (apex at the centre). | Mint #45ceb4 (video); user reads #5fc9c0. Fibre strip #c8b45a. | 1 | U 1663, `wuX-t0160`, `t0189` | U/O |
| **Front brushroll** | At the very front, under the lower clear lip. **Black bristle roll with mint/teal helical fin stripes** (≈ 10–12 visible stripe bands, wound as a double helix). | Black #0c1312; teal fin #2fb59b | 1 | `wuX-t0160`, `tr-part-agiz-yumusak-rulo-1`, `t0189` | O |
| Front lip + comb | Clear lower front lip. Behind the rollers sits a dark grey **saw-tooth comb** (≈ 12 diagonal teeth, Anti Hair Wrap). | Clear / dark grey | 1 | `wuX-t0160` | O |
| "duo clean DETECT" plate | Grey badge on the front of the cover, centre-right. "duo" outline lowercase, "clean" small, "**DETECT**" bold caps. | Light grey plate (#a9aaa8), dark print | 1 | U 1663, `t0189` | U/O |
| Corner windows | Clear/smoked angled corner housings at both front corners, with small amber/silver internal detail (lens + PCB). They emit the **white headlights**. | Smoked clear | 2 | `t0189`, `cHk-t0009` | O |
| Violet light strip | Thin **purple/violet** bar along the rear edge of the roller window, just in front of the neck plate. It reads as a lit lightpipe in `JCG-t0176.9`. | Violet #5a3cff when lit | 1 | `JCG-t0176.9` | O (lit vs unlit: I) |
| Neck plate | Raised trapezoid plate centred on the rear deck, "**Shark**" in large light-grey/white italic | Gunmetal plate; logo #afada9 | 1 | U 1663, `JCG-t0176.9` | U/O |
| Light-Detect sensor | Small round black window on the deck, right of the neck plate (viewed from the front) | Black lens | 1 | `JCG-t0176.9`, technical §5.3 | O |
| Foot pictogram | Small light-grey footprint (shoe) icon on the deck top-right | Light grey print | 1 | `JCG-t0176.9` | O |
| "EDGE DETECT" print | Vertical text on the right side panel front face: "**EDGE** DETECT" | Light grey | 1 (per side: I) | `JCG-t0176.9` | O |
| Side caps | Rounded **teardrop** caps on each end, **purple** satin, inside a gunmetal surround. A **turquoise round button/disc** (≈ Ø 14) sits toward the front. A small dark oval Edge-sensor window sits further back. | Purple #4a2f86; button #3fd1c2 | 2 | `wuX-t0340`, `tr-ip3251eut-16`, `JCG-t0139.2` | O |
| Rear wheels | Behind the body on both sides of the neck. Dark grey tyre with a fine radial-line face and a **silver centre cap**. | #2b2b2b / cap silver | 2 | `JCG-t0020.3`, `t0088` | O |
| Underside | Twin roller bays (see the roller rows above). Two coin-slot screws and a white rating label "Shark Power Nozzle" on the neck underside. | Dark grey | — | `wuX-t0160` | O |
| Corrugated hose | Black hose in the neck yoke | Black | 1 | U 1663 | U/O |

---

## 5. DOCK — Clean & Empty (auto-empty, 2 L)

**Best references:**
- Colour: `crop-user1663-dock-wand` (U)
- Front ortho: `crop-cl-eut-01-dock-front`
- Isolated: **`tr-part-2-0l-aed-eu-fisi-1`** (whole dock, 4472 px), `tr-part-2-0l-aed-toz-haznesi-1-1` (white bin), `tr-part-2-0l-aed-boru-1` (post + cradle), `crop-tr01-dock-empty`
- Top: **`vid-JCGXMfx8SG8-t0011.6`** (indicator pill + POWERDETECT badge), **`vid-ph7l7p4JMsA-t0352`** (top handle, dial, yellow label, cord)
- Cradle: `vid-ph7l7p4JMsA-t0344/0616` (QUIET MODE slider)
- Lower rear grille: `vid-JCGXMfx8SG8-t0098.6/0104.4`
- Tower interior and port: `vid-JCGXMfx8SG8-t0124.7`, `vid-UDDjkrKD7Mk-t0129`
- Side: `vid-JCGXMfx8SG8-t0020.3`

**Sheet:** `sheets/sheet-dock.jpg`

**Architecture.** A graphite **base plate** carries:
- a graphite **lower body** (≈ 180–230 mm tall), topped by
- a **white removable 2 L bin/tower** (to ≈ 500–525 mm);
- a graphite **round-rect post** rising from the front-left of the tower top up to
- the graphite **cradle cup** (top ≈ 890).

The floorhead parks on the plate in front.

| Feature | Detail | Colour and finish | Status |
|---|---|---|---|
| White bin/tower | ≈ 200 W × 195 D (see §1 C). Rounded vertical edges. The front-right corner is chamfered/rounded. The top slopes slightly to the rear. Inside: a round evacuation port with a black gasket (bin rear) and a mating port on the tower front. | **White, satin-gloss** #e0e4e7 (photo), user #e4eef8 | U/O |
| Top carry handle | Recessed grip with a **dark grey rubber handle bar** across the top centre | Dark grey #4a4a4c | O (`ph7-t0352`, `tr-part-…toz-haznesi`) |
| Anti-Odour dial | Round black gloss puck (≈ Ø 55–65) at the **rear-right of the top**. Teal print: hexagon cube logo, "ANTI-ODOUR TECHNOLOGY", padlock / open-lock, "+ ▬▬▬ −" intensity wedges, ▶ index. **Printed, not a display.** | Black #111, teal #1fb5a5 | O. U shows a black disc with green marks. |
| Indicator pill | Black gloss rounded **pill/teardrop** window on the top-left, next to the post. White icons: **bin-with-dust** (bin-full) above a **moon** (quiet mode). | Black; icons white/emissive when active | O (`JCG-t0011.6`, `ph7-t0352`) |
| POWERDETECT badge | Small rectangular champagne-gold plate with "POWERDETECT" in dark text. Upper front-left of the tower (vertical in renders, reading top→bottom), next to the post. | Brushed gold #957c59 (photo) | O |
| Yellow warning label | Yellow triangle/rectangle sticker on the top right (emptying instructions) | Yellow #f2d21a | O (optional) |
| Post | Graphite round-rect column (≈ 55 × 65) from the tower top to the cradle | Graphite #45464a…#585a5e | U/O |
| Cradle cup | Open-front U cup, ≈ 107 W × 115 H, projecting forward. Two charging pads inside. A **yellow "QUIET MODE" label plus slide switch** (fan ← → moon) on its front. | Graphite; yellow label | O |
| Lower body | Graphite box the same footprint as the tower. **Diagonal-slatted filter door** on the right side face (≈ 120 × 160) with a **round twist button** at its bottom. The power cord exits at the lower rear. | Graphite #6d6a68 lit / #45464a; grille slots dark | O (`JCG-t0098.6`) |
| Base plate | Thin (≈ 15 mm) graphite plate with rounded corners, extending forward under the head and slightly beyond the sides of the tower. Two short pegs on the separate accessory plate (`tr-part-2-yuvali-bebek-yuvasi-1`), which is an optional accessory station. | Graphite #424347 | U/O |

**Render colour conflict (C).** Moody renders `tr-ip3251eut-10/-11/-13` and `cl-na-10` show the tower as **dark brown/charcoal with a lit window**. That is an advertising "x-ray" grade. Every real photo and the user's unit show **white**. Use white.

---

## 6. LIGHTS, SCREENS AND EMISSIVES

1. **Handheld round screen** (cap face).
   - **Purple LED ring:** a full circle just inside the cap rim. User #4533d1, video #5016b4. Emissive about **#6a3cff**; in DETECT it changes white → light purple → purple (technical §5.1).
   - **TR/EU retail layout (Variant A)**, seen in the TR and US review units `t0156`, `t0159` and `ph7-t0680`:
     - **DETECT icon** (concentric rings) at the top centre, light cyan-blue #7cc8f0;
     - **horizontal battery bar** across the middle (cyan gradient, length = charge);
     - **battery-with-bolt icon** under the bar while charging;
     - **ECO leaf** in a circle, green #3fbf5a, left of centre when in ECO;
     - BOOST fan icon on the right, **red** (#e04848) when active (see §10.1);
     - **power pill** at the bottom, with a lit purple ⏻.
   - The Vacuum Wars US unit and the official render inset show Variant B: a "[▭]" battery bracket at the top and a leaf · target · fan row. That is a firmware/region difference. **Model Variant A** (agrees with technical §5.1).
   - Screen glass is black, gloss, with an off-state reflection.
2. **Floorhead.**
   - **Two white headlights** at the front corners. Low, wide forward cones; strong cool-white floor spill. Seen in `cHk-t0009`, `ph7-t0256`, `t0192`, U 1667.
   - **Violet/purple under-glow LEDs** at the **rear corners beside the wheels**. They project purple pools on the floor behind and beside the head. Seen in U 1664–1666, `YVH-t0013`, `cHk-t0014` and `ph7-t0520`. Emissive about **#7a4cff**; floor pool #8d6def.
   - The **violet light strip** along the rear edge of the roller window (`JCG-t0176.9`).
   - The violet colour follows the DETECT state (technical §5.3). Do **not** colour the front headlights violet. The user's "violet at the front corners" impression comes from the rear glows seen while the head moves away from the camera (1664–1666).
3. **Battery:** small round LED dot at the rear of the battery bar (yellow / green / white, technical §5.2). Not seen in photos (I).
4. **Dock:**
   - The indicator pill (bin-full and quiet icons) is the only dock light.
   - The anti-odour dial is printed, not lit.
   - No other dock LEDs were seen (O, several angles).

## 7. MARKINGS INVENTORY

| Marking | Where | Style | Ref |
|---|---|---|---|
| "POWERDETECT" | Handheld champagne plate | Dark grey on gold; POWER bold, DETECT light | U 1663 |
| "Shark" | Brushed-silver frame over the bin | Large italic, raised, silver | U 1663 |
| "Shark POWERDETECT" | Wand front, vertical | Dark grey print | `cl-eut-01` |
| "Shark" | Battery bar outer face | Light grey | `t0168` |
| "Shark" | Floorhead neck plate | White/light grey, large italic | U 1663 |
| "duo clean DETECT" | Floorhead front badge | Dark on light grey plate | U 1663 |
| "EDGE DETECT" | Floorhead right side panel, vertical | Light grey | `JCG-t0176.9` |
| Footprint icon | Floorhead deck, top right | Light grey | `JCG-t0176.9` |
| "POWERDETECT" | Dock tower badge | Dark on gold plate | `JCG-t0011.6` |
| Anti-odour dial graphics | Dock top | Teal print | `crop-tr01-dock-display-inset` |
| Bin-full / moon icons | Dock indicator pill | White | `JCG-t0011.6` |
| "QUIET MODE" + fan/moon | Dock cradle front | Yellow label | `ph7-t0344` |

## 8. MATERIALS — proposed base colours

| Material | Base sRGB | Finish |
|---|---|---|
| Purple (cap, bin ring, hinge discs, neck disc, head side caps) | **#4a2f86** | Satin anodised metal look (metallic 0.6, roughness 0.35). Cap base ring is gloss. |
| Gunmetal body (handheld, couplings, head chassis) | **#7f7e7a** (revised from #6a6a6e after neutral-light check, §10.1); head underside #4f4f4f | Satin plastic, roughness 0.45 |
| Brushed silver frame | #b9bcbe | Metallic 1, roughness 0.3, brushed |
| Champagne/bronze wand | **#a68d64** | Metallic 1, roughness 0.35, brushed lengthwise |
| Champagne label plates | #b3a37f | Brushed metallic |
| Dock white | **#e6e9eb** | Satin-gloss plastic, roughness 0.3 |
| Dock graphite (post, cradle, lower body, plate) | **#47484c** | Satin, roughness 0.5 |
| Mint soft roller | **#4fcdb8** | Plush fibre (high roughness, sheen) |
| Roller fibre strip | #c8b45a | Fibre |
| Front brush | black #111 + teal fin #2fb59b | Rubber / bristle |
| Head side-cap button | #3fd1c2 | Gloss |
| Clear parts | Transmission 0.9, IOR 1.58, faint cool tint | Gloss |
| Screen ring emissive | #6a3cff | — |
| Head rear glow emissive | #7a4cff | — |
| Headlights | White 6500 K | — |

## 9. GAPS AND OPEN ITEMS

- **Dock dimensions conflict** with the technical file (390 vs ≈ 510 mm tower). See §1. A tape measure on the user's unit would settle it in a minute.
- Cap flute count, rim notch count and vent slot count are estimated from oblique video (±10–15 %).
- No orthographic rear or top view of the handheld. The underside of the battery and grip comes from video only.
- The function of the small purple button on the cap rim is unconfirmed.
- Retailer galleries were **not fetched**: Amazon .com.tr/.de/.co.uk, Hepsiburada, Trendyol, MediaMarkt TR, Teknosa, Vatan, Argos and Currys. Official and video coverage was judged sufficient.
- Not downloaded:
  - `IP3251UKT_3D` web 3D viewer (no licence);
  - official PDP videos (Cloudinary video tag lists return 404).
- **YouTube:** frames come from 7 videos via yt-dlp 2026.08.19 (latest, no cookies). The Claude-in-Chrome tab could not play video while hidden, so it was closed. Three more downloaded videos were not mined: `5pO1Ofg02HI`, `T9U8rtc6cJk` (25-minute TR unboxing) and `IkFH-pEArs8`. They are the next stop for the dock's rear view and the box contents.
## 10. CLOSE-UP PACK (floorhead + handheld)

**Sheets:** `sheets/floorhead_closeups.jpg` and `sheets/handheld_closeups.jpg`. The numbering matches the tables below.

**Where the frames are:** `assets/references/ip3251/frames/`. Each frame is the sharpest of 7 frames taken within ±0.6 s of the timestamp (edge-variance pick).

**Sources:** the original 7 videos plus 4 newly mined ones:
- `T9U8rtc6cJk`: HKTasarımTamirat, 25-minute TR unboxing (Turkish retail unit)
- `NXMRTS4e6dQ`: Bay Süpürge, TR, vertical 1080×1920, **neutral grey studio light**
- `5pO1Ofg02HI`: Erin Lawrence, US
- `IkFH-pEArs8`: Just A Dad. **Rejected**: it compares IP3251 with IP3253 and the units are not identifiable frame by frame.

**Camera angles** are given relative to the head or handheld: "front" = roller side; "operator view" = high rear 3/4, looking over the handle.

### 10.1 New findings from the close-ups

**Screen icon map (TR unit), confirmed.** The shipping film on the TR unit (`T9U8-t1010`) prints every icon in place, on the round face:
- top: **power pill** in a white rounded square;
- under it: **battery-with-bolt** icon, with a small "FO" to its side;
- a **long horizontal bar** across the middle;
- around the right half of the face, top to bottom: **green ECO leaf** in a circle, large **white DETECT concentric target**, **red BOOST fan** in a circle;
- a **purple ring** following the rim.

The lit screen (`T9U8-t1220`) shows the same placement: green leaf at upper-left in the photo's orientation, power pill at bottom-right. The photo's rotation explains the difference. This is Variant A, agreeing with technical §5.1.
- **Addition to §6:** the BOOST icon is **red**.
- **Off state:** the icons are invisible and the glass is black.

**Front brushroll ratio (neutral light).** Under neutral light (`NXM-t0088`) the front bristle roll reads **about 50 % bright teal (#1ff2d0) and 50 % black**, as broad double-helix bands. It is not mostly black. The official spare render (`tr-part-agiz-yumusak-rulo-1`) shows the same ratio.

**Rear soft roller (neutral light):**
- roller body #59eed1;
- the V fibre strip is pale **yellow-green** (#b9eaad … #c8b45a), a felt/microfibre band about 8 mm wide;
- the V apex is at the centre and points toward the front.

**Head body colour, TR "Koyu Gri" (neutral light, `NXM-t0088/0262`):**
- outer shell and side frame: mid warm grey **#9f9c96 lit / ≈ #7f7e7a albedo**;
- underside plate and comb: darker charcoal **#51504e / #515c5d**;
- wheels: #3c3b3e.

So the shell is mid gunmetal grey, **lighter than near-black**. The user's video frames look darker because they are underexposed. **Revised albedo: shell #7f7e7a, underside #4f4f4f.**

**Underside layout (`NXM-t0088`, `T9U8-t0425/0430`, `wuX-t0160`):**
- the neck yoke carries 2 wheels (Ø 47, dark grey, **silver hubcaps**), a white rating label ("Shark Power Nozzle", CE) and **2 coin-slot screws** either side of the hose port;
- a full-width **saw-tooth comb**: about 11–12 teeth leaning diagonally, dark grey;
- the rear soft-roller bay, then the front brushroll bay;
- small black end bearings.

**Side cap (`NXM-t0262`, `JCG-t0139.2`):**
- the purple teardrop sits in a grey surround;
- the **teal round button is the brushroll release**: pressing it ejects the front brushroll sideways (`T9U8-t1295`);
- the oval edge-sensor window sits behind it.

**Handheld architecture, from the studio side views** (`PmG-t0058` right side, `PmG-t0066` left side, both on a white backdrop; `qXa-t0087`):
- **Clear bin.** A large stepped/trapezoid clear box that fills the front ~55 % of the handheld and hangs below the body line.
  - "MAX" fill line moulded on the side.
  - Its front-bottom corner is angled and carries the bin-door hinge and latch.
  - The cyclone shroud and mesh are visible inside.
- **Top surface.** A flat gunmetal **top surface** runs from the nozzle to the cap. **Its rear third carries a dotted vent grid**, the same staggered slots as the side grilles; the vents wrap from the top onto both sides.
- **Handle loop.** The **front diagonal strut is the battery.** It has a light-grey/silver panel with a vertical "Shark" wordmark and runs from under the bin rear down to the bottom bar. With the battery removed (`PmG-t0058`), the loop is open there.
  - **Correction to §2 / IP1251 note:** the battery is not just "the lower bar".
- **Rear grip strut** (vertical, toward the cap): charcoal soft-touch front face.
  - **Mode trigger:** a **small purple tab on the inside top of the grip**, just under the cap (`qXa-t0087`).
  - A small dark slider mark sits on the grip's rear face.
- **Cap face (screen off, `PmG-t0026`).** Plain black glass. The purple power pill sits at the edge toward the grip. A purple serrated rim (≈ 14–16 notches) surrounds the glass.

**Screen layouts.** US units (Browntown, Alissa Beiler, Vacuum Wars, RTINGS) show Variant B: "[▭]" battery bracket at top, DETECT target centre, power pill. TR and UK units (`T9U8`, `ph7`, `UDD`, Parwaz `wnzn-t0182` film) show Variant A. **Model Variant A.**

**LED placement, consolidated** (`qXa-t0120…0150`, operator view; `MqU-t0022/23`, front low):
- **2 white headlights**, one in each front corner window;
- **2 violet LEDs at the rear corners**, under the side-cap rear, beside the wheels, throwing violet pools on the floor behind and outboard of the head;
- **plus** the thin violet strip at the rear edge of the roller window.

The rear violet and the front white are on together in DETECT.

**Retailer galleries (Argos, Currys, AO, Hepsiburada, Trendyol, Teknosa).** All returned HTTP 403 to non-browser requests. MediaMarkt TR and Vatan returned pages with no IP3251 image URLs. Amazon UK/TR returned stubs. Not pursued: they reuse the official SharkNinja renders already in `raw/`.

### 10.2 Floorhead close-ups
| # | File (frames/) | Shows | Camera angle |
|---|---|---|---|
| 1 | `vid-NXMRTS4e6dQ-t0088.0.jpg` | UNDERSIDE, neutral grey light: rear mint soft roller with yellow V fibre, front teal/black helical brushroll, saw-tooth comb, 2 coin screws, rating label, wheels | underside, straight (head upside-down, neck toward camera top) |
| 2 | `vid-NXMRTS4e6dQ-t0080.0.jpg` | UNDERSIDE both rollers, finger on front brush | underside, ~20 deg from straight |
| 3 | `vid-NXMRTS4e6dQ-t0076.0.jpg` | underside rollers, neck + wheels at top | underside, slightly oblique |
| 4 | `vid-NXMRTS4e6dQ-t0084.0.jpg` | underside, rollers turning | underside oblique |
| 5 | `vid-NXMRTS4e6dQ-t0066.0.jpg` | head held: top cover, mint roller + V, "duo clean DETECT" plate, Shark neck plate, purple side cap + teal button (neutral light) | top-front 3/4 from right, ~45 deg elevation |
| 6 | `vid-NXMRTS4e6dQ-t0062.0.jpg` | head on table, top + neck, neutral light | top-down oblique, from front |
| 7 | `vid-NXMRTS4e6dQ-t0070.0.jpg` | head on table, top + front | top-down ~60 deg, from front |
| 8 | `vid-NXMRTS4e6dQ-t0262.0.jpg` | SIDE CAP close: purple teardrop, teal round button pressed (front roller release), rear wheel, side-cap surround | left side, ~20 deg elevation |
| 9 | `vid-NXMRTS4e6dQ-t0258.0.jpg` | head on table with wand, front 3/4 | front 3/4 high |
| 10 | `vid-NXMRTS4e6dQ-t0232.0.jpg` | head on grey floor, violet rear LEDs + white front light | high 3/4 from front-left |
| 11 | `vid-NXMRTS4e6dQ-t0236.0.jpg` | head on floor, violet glow beside wheels, neutral light | top-down oblique from rear-left |
| 12 | `vid-T9U8rtc6cJk-t0420.0.jpg` | unboxing: underside rollers + neck yoke + Shark plate edge | underside/rear 3/4, hand-held |
| 13 | `vid-T9U8rtc6cJk-t0425.0.jpg` | REAR/UNDERSIDE: neck yoke, wheels, coin screws, comb, rollers | rear-underside oblique |
| 14 | `vid-T9U8rtc6cJk-t0430.0.jpg` | underside: neck, wheel, label, brushroll fins | underside oblique from rear-right |
| 15 | `vid-T9U8rtc6cJk-t0435.0.jpg` | neck + Shark plate + yellow factory label, side | rear 3/4 top from left |
| 16 | `vid-T9U8rtc6cJk-t1100.0.jpg` | head lights ON on laminate, white front pools | high rear 3/4 |
| 17 | `vid-T9U8rtc6cJk-t1140.0.jpg` | violet LEDs ON on rug | high rear 3/4 |
| 18 | `vid-T9U8rtc6cJk-t1190.0.jpg` | white front corner LEDs ON, violet rear glow | high rear 3/4 (operator view) |
| 19 | `vid-T9U8rtc6cJk-t1200.0.jpg` | white + violet LEDs ON | high rear 3/4 (operator view) |
| 20 | `vid-T9U8rtc6cJk-t1295.0.jpg` | front brushroll being pulled out of the side | side/underside, hand-held |
| 21 | `vid-5pO1Ofg02HI-t0035.0.jpg` | FRONT LOW: head under bed, white headlights + violet | front, ~5 deg elevation (floor level) |
| 22 | `vid-5pO1Ofg02HI-t0260.0.jpg` | front 3/4 low on tile, white lights, roller window | front-right 3/4, ~15 deg elevation |
| 23 | `vid-5pO1Ofg02HI-t0265.0.jpg` | front 3/4 low, lights | front-right 3/4, ~15 deg |
| 24 | `vid-5pO1Ofg02HI-t0380.0.jpg` | head top close on rug, purple side cap, LEDs | top-down oblique from front-left |
| 25 | `vid-5pO1Ofg02HI-t0420.0.jpg` | FRONT STRAIGHT close: soft roller + brushroll through cover, corner light windows lit blue-white | front, ~10 deg elevation, very close |
| 26 | `vid-5pO1Ofg02HI-t0425.0.jpg` | front close, finger on soft roller | front close |
| 27 | `vid-5pO1Ofg02HI-t0430.0.jpg` | soft roller fibre V + brush fins macro | front macro |
| 28 | `vid-5pO1Ofg02HI-t0460.0.jpg` | head on tile + wand, violet | high 3/4 rear |
| 29 | `vid-5pO1Ofg02HI-t0480.0.jpg` | TOP-DOWN: Shark neck plate, cover, roller, plate print | top-down ~70 deg from rear |
| 30 | `vid-5pO1Ofg02HI-t0135.0.jpg` | head on armchair fabric, LEDs | oblique |
| 31 | `vid-UDDjkrKD7Mk-t0189.0.jpg` | front straight, cover, both rollers, corner windows | front, ~10 deg elevation |
| 32 | `vid-UDDjkrKD7Mk-t0192.0.jpg` | front close, corner windows | front close |
| 33 | `vid-UDDjkrKD7Mk-t0088.0.jpg` | side cap + wheel + white light | left side, low |
| 34 | `vid-UDDjkrKD7Mk-t0078.0.jpg` | head held upright, front roller removed | front, hand-held |
| 35 | `vid-UDDjkrKD7Mk-t0084.0.jpg` | soft roller macro through cover | front macro |
| 36 | `vid-JCGXMfx8SG8-t0176.9.jpg` | top deck: Shark plate, violet strip, EDGE DETECT print, light sensor, foot icon | top-front, ~40 deg |
| 37 | `vid-JCGXMfx8SG8-t0139.2.jpg` | side cap close (purple teardrop, turquoise button, edge window) | right side, ~10 deg |
| 38 | `vid-JCGXMfx8SG8-t0171.1.jpg` | end cap release, side | side close |
| 39 | `vid-cHkhhEh7AuE-t0009.0.jpg` | white headlight ON, front corner, floor level | front, ~5 deg |
| 40 | `vid-YVHoHgc5bu8-t0013.0.jpg` | violet rear glows, top-down | top-down |
| 41 | `vid-ph7l7p4JMsA-t0256.0.jpg` | dark floor: white front + violet rear | high rear |
| 42 | `vid-ph7l7p4JMsA-t0520.0.jpg` | violet underglow, low angle | side-rear low |
| 43 | `vid-wuXUwo0Itxg-t0160.0.jpg` | underside: mint soft roller + black/teal brush, comb | underside oblique |
| 44 | `vid-wuXUwo0Itxg-t0340.0.jpg` | side profile: purple cap, teal button, wheel | side, ~20 deg |
| 45 | `vid-2Ockr0C4Jdw-t0084.0.jpg` | underside in hand | underside oblique |
| 46 | `vid-PmG6aO3SHhE-t0122.0.jpg` | UNDERSIDE on white backdrop (US unit, studio light): neck yoke, wheels, comb, soft roller V, front brush | underside, ~15 deg |
| 47 | `vid-PmG6aO3SHhE-t0126.0.jpg` | underside, finger on soft roller | underside, ~20 deg |
| 48 | `vid-PmG6aO3SHhE-t0130.0.jpg` | underside 3 | underside, ~20 deg |
| 49 | `vid-PmG6aO3SHhE-t0118.0.jpg` | head held: top cover + Shark plate, white backdrop | top-front, ~50 deg |
| 50 | `vid-PmG6aO3SHhE-t0160.0.jpg` | underside vertical in hand: both rollers + neck, side bearing | underside, rotated 90 deg |
| 51 | `vid-PmG6aO3SHhE-t0164.0.jpg` | underside vertical 2 | underside |
| 52 | `vid-PmG6aO3SHhE-t0196.0.jpg` | MACRO rollers: soft roller V fibre (gold-green felt) + front teal/black helical brush | underside macro |
| 53 | `vid-PmG6aO3SHhE-t0200.0.jpg` | macro rollers 2 | underside macro |
| 54 | `vid-PmG6aO3SHhE-t0202.0.jpg` | macro rollers 3 | underside macro |
| 55 | `vid-JRmJkY-RTeA-t0010.0.jpg` | RTINGS studio: head top/front straight, cover, plate, Shark neck plate | front, ~35 deg elevation |
| 56 | `vid-MqUvnGYlf_o-t0022.0.jpg` | official ad: FRONT STRAIGHT low, both white corner LEDs ON | front, ~5 deg |
| 57 | `vid-MqUvnGYlf_o-t0023.0.jpg` | official ad: front low 2, LEDs ON | front, ~5 deg |
| 58 | `vid-MqUvnGYlf_o-t0025.0.jpg` | official: front 3/4 high on rug, violet strip | front-left 3/4, ~35 deg |
| 59 | `vid-MqUvnGYlf_o-t0034.0.jpg` | official macro: cover + DETECT plate + rollers 3/4 | front-right 3/4, ~25 deg |
| 60 | `vid-MqUvnGYlf_o-t0035.0.jpg` | official macro 2 | front-right 3/4 |
| 61 | `vid-MqUvnGYlf_o-t0047.0.jpg` | official: front straight low, Shark plate, LEDs | front, ~10 deg |
| 62 | `vid-MqUvnGYlf_o-t0048.0.jpg` | official macro: "duo clean DETECT" print on cover, violet strip | front-left, very close |
| 63 | `vid-qXahsvmFo_4-t0003.0.jpg` | head approaching camera, FRONT white headlights both corners ON | front, ~15 deg, far |
| 64 | `vid-qXahsvmFo_4-t0006.0.jpg` | front headlights ON, carpet | front ~15 deg |
| 65 | `vid-qXahsvmFo_4-t0015.0.jpg` | front headlights ON close | front ~15 deg |
| 66 | `vid-qXahsvmFo_4-t0039.0.jpg` | front headlights far | front |
| 67 | `vid-qXahsvmFo_4-t0120.0.jpg` | OPERATOR VIEW: violet LEDs at both REAR corners + white front | high rear, ~50 deg |
| 68 | `vid-qXahsvmFo_4-t0123.0.jpg` | operator view violet 2 | high rear |
| 69 | `vid-qXahsvmFo_4-t0129.0.jpg` | operator view on tile: violet rear + white front pools | high rear |
| 70 | `vid-qXahsvmFo_4-t0141.0.jpg` | operator view violet + white | high rear |
| 71 | `vid-qXahsvmFo_4-t0150.0.jpg` | operator view violet, near wall | high rear |
| 72 | `vid-wnznDooyH-o-t0247.0.jpg` | UK unit on dark carpet: head 3/4 front, white corner light, purple side cap, teal button | front-right 3/4, ~30 deg |
| 73 | `vid-wnznDooyH-o-t0351.0.jpg` | front brushroll removed from side (teal/black helical) | side, hand-held |
| 74 | `vid-wnznDooyH-o-t0364.0.jpg` | UNDERSIDE: both rollers + neck (UK unit) | underside |
| 75 | `vid-wnznDooyH-o-t0390.0.jpg` | underside close: comb, soft roller V | underside close |
| 76 | `vid-wnznDooyH-o-t0403.0.jpg` | underside/neck: label, coin screws, wheels (cool light - plate reads dark slate) | underside oblique |
| 77 | `vid-wnznDooyH-o-t0416.0.jpg` | underside 3/4, roller bay | underside oblique |
| 78 | `vid-wnznDooyH-o-t0845.0.jpg` | head on dark carpet, white LED | front-left 3/4 high |
| 79 | `vid-wnznDooyH-o-t1014.0.jpg` | head side + violet + lit screen in frame | side-top |
| 80 | `vid-wnznDooyH-o-t1144.0.jpg` | head + wand on carpet, side cap | side 3/4 high |
| 81 | `vid-tz8zDNUtIcM-t0996.0.jpg` | underside rollers (grid overlay in source) | underside |
| 82 | `vid-tz8zDNUtIcM-t1008.0.jpg` | MACRO front brush helix teal/black | macro |
| 83 | `vid-tz8zDNUtIcM-t1020.0.jpg` | underside: comb, soft roller V, neck label | underside, ~20 deg |
| 84 | `vid-6_ywPlCctwk-t0014.0.jpg` | Best Buy: head held front-on, cover, brush, Shark plate | front, ~20 deg, studio |
| 85 | `vid-6_ywPlCctwk-t0016.0.jpg` | Best Buy: head front 2 | front, studio |
| 86 | `vid-W_O7EvhuJ3U-t0008.0.jpg` | official IP1251 ad: front low, white corner LEDs, violet strip | front, ~10 deg |
| 87 | `vid-W_O7EvhuJ3U-t0009.0.jpg` | official IP1251 ad: front low 2 | front-left, ~10 deg |
| 88 | `vid-W_O7EvhuJ3U-t0010.0.jpg` | official IP1251 ad: FRONT STRAIGHT low, both white corner LEDs, purple neck disc | front, ~10 deg |
| 89 | `vid-W_O7EvhuJ3U-t0025.0.jpg` | official: head far on floor, front LEDs (text overlay) | front, ~5 deg, far |

### 10.3 Handheld close-ups
| # | File (frames/) | Shows | Camera angle |
|---|---|---|---|
| 1 | `vid-T9U8rtc6cJk-t1010.0.jpg` | SCREEN ICON MAP (TR unit, shipping film): power pill, battery+bolt with "FO", long bar, green ECO leaf, white DETECT target, red BOOST fan, purple ring | cap face, ~30 deg off-axis |
| 2 | `vid-T9U8rtc6cJk-t1005.0.jpg` | screen film + cap flutes + rim, grip | cap face 3/4 from grip side |
| 3 | `vid-T9U8rtc6cJk-t1000.0.jpg` | GRIP TOP + cap side: grip bar, mode trigger tab, purple cap flutes, gloss purple ring | top/side of grip, ~30 deg |
| 4 | `vid-T9U8rtc6cJk-t1220.0.jpg` | SCREEN LIT straight-on: purple ring, green ECO leaf upper-left, power pill bottom-right | cap face ~15 deg off-axis |
| 5 | `vid-T9U8rtc6cJk-t1080.0.jpg` | cap end view, screen off/lit | cap face, oblique |
| 6 | `vid-T9U8rtc6cJk-t0380.0.jpg` | handheld in hand: cap, vents, POWERDETECT plate, yellow sticker | side 3/4 from screen end |
| 7 | `vid-T9U8rtc6cJk-t0384.0.jpg` | cap + screen, hand | cap 3/4 |
| 8 | `vid-T9U8rtc6cJk-t0890.0.jpg` | bin + frame docked, yellow factory sticker | front 3/4 high |
| 9 | `vid-T9U8rtc6cJk-t0900.0.jpg` | HANDHELD SIDE: bin, latch, grip, battery "Shark" silver panel | side, ~10 deg |
| 10 | `vid-T9U8rtc6cJk-t0910.0.jpg` | handheld side, bin empty, battery | side |
| 11 | `vid-T9U8rtc6cJk-t0920.0.jpg` | bin + cyclone side | side |
| 12 | `vid-T9U8rtc6cJk-t0990.0.jpg` | bin/filter area, pre-motor filter | top 3/4 |
| 13 | `vid-T9U8rtc6cJk-t1420.0.jpg` | bin base in dock cradle, QUIET label | front close |
| 14 | `vid-T9U8rtc6cJk-t1450.0.jpg` | docked, cap top | high |
| 15 | `vid-NXMRTS4e6dQ-t0024.0.jpg` | handheld in hand, neutral light: cap, grip | 3/4 from screen end |
| 16 | `vid-NXMRTS4e6dQ-t0028.0.jpg` | bin open, cyclone, neutral light | side 3/4 |
| 17 | `vid-NXMRTS4e6dQ-t0034.0.jpg` | clear bin removed | front |
| 18 | `vid-NXMRTS4e6dQ-t0040.0.jpg` | handheld side, filter, battery | side |
| 19 | `vid-NXMRTS4e6dQ-t0046.0.jpg` | pre-motor filter + handheld | oblique |
| 20 | `vid-NXMRTS4e6dQ-t0268.0.jpg` | handheld + wand in use | oblique |
| 21 | `vid-5pO1Ofg02HI-t0050.0.jpg` | bin in cradle close | front close |
| 22 | `vid-5pO1Ofg02HI-t0120.0.jpg` | handheld out of box | side |
| 23 | `vid-UDDjkrKD7Mk-t0006.0.jpg` | cap + POWERDETECT plate + vents | side, eye level |
| 24 | `vid-UDDjkrKD7Mk-t0156.0.jpg` | screen ECO lit | cap face ~25 deg |
| 25 | `vid-UDDjkrKD7Mk-t0159.0.jpg` | screen DETECT icon + bar + bolt | cap face ~25 deg |
| 26 | `vid-UDDjkrKD7Mk-t0165.0.jpg` | side profile, grip loop | side, ~5 deg |
| 27 | `vid-UDDjkrKD7Mk-t0168.0.jpg` | grip + Shark battery, trigger | side close |
| 28 | `vid-UDDjkrKD7Mk-t0231.0.jpg` | vent grid + bin frame | side close |
| 29 | `vid-UDDjkrKD7Mk-t0234.0.jpg` | cap flutes + slot vents macro | side-top close |
| 30 | `vid-ph7l7p4JMsA-t0680.0.jpg` | screen lit, TR layout | cap face ~10 deg |
| 31 | `vid-ph7l7p4JMsA-t0664.0.jpg` | cap rim notches, ring lit | cap face straight |
| 32 | `vid-wuXUwo0Itxg-t0445.0.jpg` | screen US layout | cap face oblique |
| 33 | `vid-JCGXMfx8SG8-t0072.5.jpg` | grip/battery underside | underside 3/4 |
| 34 | `vid-JCGXMfx8SG8-t0066.7.jpg` | nozzle + bin underside | below |
| 35 | `vid-JCGXMfx8SG8-t0150.8.jpg` | cap removed: motor end interior | cap end |
| 36 | `vid-PmG6aO3SHhE-t0022.0.jpg` | handheld standing on white backdrop: cap, frame, bin (US) | side, eye level |
| 37 | `vid-PmG6aO3SHhE-t0026.0.jpg` | SCREEN straight-on (off) + cap rim notches, grip below | cap face, ~5 deg |
| 38 | `vid-PmG6aO3SHhE-t0030.0.jpg` | screen lit straight-on (US layout) | cap face, ~5 deg |
| 39 | `vid-PmG6aO3SHhE-t0034.0.jpg` | screen lit 2 | cap face |
| 40 | `vid-PmG6aO3SHhE-t0040.0.jpg` | screen lit 3 | cap face |
| 41 | `vid-PmG6aO3SHhE-t0046.0.jpg` | screen + power pill close | cap face |
| 42 | `vid-PmG6aO3SHhE-t0050.0.jpg` | screen lit, DETECT target | cap face |
| 43 | `vid-PmG6aO3SHhE-t0054.0.jpg` | screen lit, DETECT | cap face |
| 44 | `vid-PmG6aO3SHhE-t0058.0.jpg` | HANDHELD RIGHT SIDE (grip side) full: bin, frame, grip loop, battery, studio light | right side, ~10 deg |
| 45 | `vid-PmG6aO3SHhE-t0062.0.jpg` | handheld side, grip loop from below | side-below |
| 46 | `vid-PmG6aO3SHhE-t0066.0.jpg` | HANDHELD LEFT SIDE: bin, Shark frame, battery silver panel, grip | left side, eye level |
| 47 | `vid-PmG6aO3SHhE-t0072.0.jpg` | left side 2, bin latch | left side |
| 48 | `vid-PmG6aO3SHhE-t0076.0.jpg` | bin latch/release with finger | left side close |
| 49 | `vid-JRmJkY-RTeA-t0005.0.jpg` | RTINGS: handheld + grip + vents (IP1251 sibling, purple wand) | side 3/4 |
| 50 | `vid-qXahsvmFo_4-t0087.0.jpg` | grip right side + mode trigger + Shark battery | right side close |
| 51 | `vid-qXahsvmFo_4-t0090.0.jpg` | screen lit straight-on (US): [battery] bracket, DETECT, power pill | cap face straight |
| 52 | `vid-qXahsvmFo_4-t0093.0.jpg` | screen lit straight-on 2 | cap face straight |
| 53 | `vid-wnznDooyH-o-t0182.0.jpg` | UK unit: screen with shipping film (feature labels) + cap | cap face 3/4 |
| 54 | `vid-wnznDooyH-o-t0455.0.jpg` | handheld nozzle end + bin (UK) | front 3/4 |
| 55 | `vid-wnznDooyH-o-t0520.0.jpg` | bin removed, cyclone + filter | top |
| 56 | `vid-wnznDooyH-o-t1170.0.jpg` | stick + handheld on carpet | side high |
| 57 | `vid-tz8zDNUtIcM-t0456.0.jpg` | GRIP close: grip bar, trigger, battery panel | side close |
| 58 | `vid-tz8zDNUtIcM-t1092.0.jpg` | screen lit: battery bar + power pill | cap face oblique |
| 59 | `vid-6_ywPlCctwk-t0019.0.jpg` | Best Buy: handheld side in hands, studio | side |
| 60 | `vid-6_ywPlCctwk-t0038.0.jpg` | bin + frame seated in dock cradle | front, eye level |
| 61 | `vid-6_ywPlCctwk-t0040.0.jpg` | bin in cradle 2 | front |

**Video sources for §10:**

| Video ID | Channel / title | Unit |
|---|---|---|
| T9U8rtc6cJk | HKTasarımTamirat, TR unboxing | TR |
| NXMRTS4e6dQ | Bay Süpürge, TR, neutral studio light | TR |
| 5pO1Ofg02HI | Erin Lawrence | US |
| PmG6aO3SHhE | Browntown "Up-Close Look", white backdrop | US |
| JRmJkY-RTeA | RTINGS | — |
| MqUvnGYlf_o | Electricshop UK, official ad cut | UK |
| qXahsvmFo_4 | Alissa Beiler, IP3251 | US |
| wnznDooyH-o | Parwaz786, IP3251UKT unboxing | UK |
| tz8zDNUtIcM | Smart Home Tested, IP3251UKT | UK |
| 6_ywPlCctwk | Best Buy unboxing | US |
| W_O7EvhuJ3U | Electricshop, official IP1251 ad cut | UK |

Earlier sources (UDD, JCG, cHk, YVH, ph7, wuX, 2Oc) are listed in §0 and in `manifest.json` notes.

Also used: 6_ywPlCctwk (Best Buy unboxing) and W_O7EvhuJ3U (Electricshop, official IP1251 ad cut). vq2upb2s2aw (T3) was downloaded but not reviewed.
