# SHARK POWERDETECT — INTERACTIVE 3D PRODUCT EXPERIENCE

**Execution brief for Claude Code · Opus 5.5 · Version 1.0 · 4 October 2026**

## Kullanım

Bu dosyayı boş bir proje klasörüne koy. Claude Code'da Opus 5.5 seçiliyken şunu söyle:

> SHARK_POWERDETECT_OPUS_5_5_MASTER_BRIEF.md dosyasının tamamını oku. Bunu uygulama talimatı olarak kullan. Projeye özel ajanları oluştur, ürün referanslarını incele, gerçekçi 3D modeli ve çalışan web deneyimini üret. Tarayıcıda kendin test et, ekran görüntülerine bakıp düzelt ve yerel önizlemeyi çalışır halde teslim et. Planı anlatıp durma; uygulamayı tamamla.

The specification below is written in English for implementation. Communicate progress and the final handoff to Eray in Turkish. The website interface itself is English.

---

## 1. Your assignment

You are the lead creative technologist, product designer, and implementation owner. Build an exceptionally polished, realistic, interactive browser experience around a Shark PowerDetect cordless stick vacuum.

This is a complete local website implementation task. Produce the 3D assets, working code, interactions, animation, sound, performance tuning, and browser verification. The deliverable is a running experience, with editable source assets and a reproducible project.

The page is almost entirely the product and the interactive scene. Keep interface content sparse. The vacuum must be immediately recognizable as the chosen PowerDetect model from its silhouette, construction, colors, floorhead, rollers, transparent bin, and articulated wand.

The visitor first sees the complete vacuum upright, facing them in a photographic studio composition. A tactile power-style Start control sits to its right. Starting transforms the composition into a close, playable cleaning surface. The visitor creates realistic messes and physically guides the vacuum across them.

**Priority order:**

1. Product identity, geometry, materials, and photographic lighting.
2. Convincing contact with the floor and satisfying, spatially correct cleaning.
3. Beautiful continuous transition from product presentation to interaction.
4. Clear mouse, touch, and keyboard controls with a minimal interface.
5. Stable performance and a clean, maintainable implementation.

Do not substitute a generic vacuum, a flattened product photograph, or a prerecorded video for the interactive product. A photographic loading poster is allowed only while the real scene loads or as a disclosed unsupported-device fallback.

## 2. Scope and decisions already made

| Decision | Requirement |
| --- | --- |
| Experience | One full-viewport product playground, with no conventional marketing sections |
| Primary model | Shark PowerDetect IP1251EUT, based on the Turkish official product references |
| Product variant | Cordless stick vacuum, without an auto-empty dock |
| Visual baseline | Grey body, purple details, transparent bin, turquoise/black roller details visible in the selected references |
| First view | Full product, upright and front-facing; slight perspective is permitted for depth |
| Activation | A power-inspired Start control on the right of the product |
| Core interaction | Add mess, switch to Clean, drag the vacuum over the floor |
| Required dirt | Dust, long hair, pet hair, crumbs, and a mixed preset |
| Required floors | Light oak, neutral stone/tile, and low-pile carpet |
| Website copy | English; short labels and interaction hints |
| User updates | Turkish |
| Architecture | Client-side experience; no account, backend, checkout, or runtime AI service required |
| Delivery | Local preview, production build, source code, editable 3D source, and QA evidence |
| Publication | Do not publish publicly as part of this task; prepare the project for later hosting |

The exact regional SKU was not specified by the user. IP1251EUT is the documented working assumption, not a claim that the user selected that SKU. Record it in PRODUCT_REFERENCE.md and continue. If the user later supplies a different photo or SKU, that reference takes precedence and the asset must be adapted consistently.

This is an independent creative concept. Use one small, unobtrusive “Independent concept” label. Do not impersonate an official store, add purchase flows, or invent performance figures. The scripted opening pass is an interaction demonstration, not a claim that this stick vacuum drives itself.

## 3. Product reference pack — inspect before modeling

### 3.1 Authoritative pages

Sources checked for this brief on 4 October 2026:

- **[P1] Turkish product page, IP1251EUT:** https://www.sharkninja.com.tr/products/shark-powerdetect-clean-empty-mor-siyah
- **[P2] Turkish support page, IP1251EU/IP1251EUT:** https://www.sharkninja.com.tr/collections/ip1000-serisi
- **[P3] Related UK model, IP1251UKT:** https://www.sharkninja.co.uk/shark-powerdetect-cordless-pet-vacuum-cleaner-ip1251ukt/IP1251UKT.html

P1 identifies the model as IP1251EUT despite the legacy URL containing “clean-empty.” Use the page's model field and matching images; do not infer the presence of a dock from its URL. P3 is a supporting reference for the product family, not permission to mix regional finishes.

P1 lists assembled dimensions of H 115.8 cm × W 26.3 cm × D 39.3 cm. These are overall dimensions, not measurements of individual components. Use them to establish approximate real-world scale, then derive component proportions from matched views. P3 contains conflicting dimension fields; do not average them or treat packaging-size-looking values as assembled geometry.

Verified family features relevant to the concept include two brush rolls, forward/reverse pickup, dirt-responsive power, floor sensing, and a folding wand. Specific indicator colors and control placement still require close-up reference verification. The simulation is illustrative and is not a physical benchmark. [P1–P3]

### 3.2 Direct visual references

Download and inspect the actual full-resolution images, not search thumbnails. Keep originals in assets/references with a source manifest. If a URL stops working, recover its matching image from P1.

| ID | Reference | URL |
| --- | --- | --- |
| V1 | Product assembly, body, bin, folded joint, nozzle and color relationships | https://www.sharkninja.com.tr/cdn/shop/files/Shark-PowerDetect-Turbo-IP1251-1.jpg?v=1744715993 |
| V2 | Folding/storage configuration; inspect variant consistency before using its color | https://www.sharkninja.com.tr/cdn/shop/files/Shark-IP1251UKT-Hero-Flex-Storage.jpg?v=1753197484 |
| V3 | Floor contact, nozzle proportions, forward/reverse cleaning composition | https://www.sharkninja.com.tr/cdn/shop/files/Shark-PowerDetect-Turbo-IP1251-7.png?v=1753197484 |
| V4 | Motor housing, grip, transparent bin and upper body close-ups | https://www.sharkninja.com.tr/cdn/shop/files/Shark-PowerDetect-Turbo-IP1251-5.png?v=1753197484 |
| V5 | Nozzle close-ups, transparent cover, roller construction | https://www.sharkninja.com.tr/cdn/shop/files/Shark-PowerDetect-Turbo-IP1251-8.png?v=1753197484 |
| V6 | Additional official gallery reference; inspect before assigning a use | https://www.sharkninja.com.tr/cdn/shop/files/Shark-PowerDetect-Turbo-IP1251-6.png?v=1753197484 |

V1, V3, V4 and V5 were visually inspected when preparing this brief. V5 includes advertising graphics around the product: glowing rings, arrows and composited effects are not physical product components. Do not reproduce those graphics as hardware, lasers, or a visible suction field.

Collect additional matching front, back, side, underside, control-panel and hinge views from official product/support material. P2 links to the manual. Make a labeled contact sheet; identify any regional differences. Record missing angles as inferred, rather than pretending every surface has an exact reference.

Create PRODUCT_REFERENCE.md with the chosen SKU, a component list, reference IDs, measured proportions, and an observed/inferred/conflicting status for each major detail. Source photographs are reference material; do not assume their availability grants redistribution rights. Prefer your own reconstructed geometry and self-authored or properly licensed textures in the shipped experience.

## 4. Creative direction

The scene should feel like a premium appliance photographed for a product campaign, made tangible through interaction.

- A very pale neutral studio background with a soft tonal falloff and grounded shadows.
- A real-size, detailed vacuum with crisp edges and plausible material response.
- Large clear space around the product. No giant paragraph behind it.
- A small Shark/PowerDetect identification at the upper left. Keep the main product unobstructed.
- One deliberate accent derived from the selected product's purple finish. Turquoise belongs to the real roller details, not every interface element.
- Restrained typography: a clean, locally hosted sans-serif with a suitable license. Use at most two weights in normal UI.
- No decorative orbiting objects, sparkles, space backgrounds, bento sections, feature-card grids, fake lens flares, or glass panels covering the product.
- No permanently rotating showroom carousel. The opening product pose is stable and readable, with only a subtle optional light/camera drift.
- No cartoon dirt, emoji tools, large scoreboards, confetti, or game-like reward mechanics.

Suggested starting palette, to adjust after material comparison:

| Role | Starting value |
| --- | --- |
| Studio background | #EAE9E6 |
| Text | #242526 |
| Muted text | #696B6D |
| Interface accent | A subdued purple sampled from V1 under neutral lighting |
| Active floor | Natural light oak with believable scale and low-gloss finish |

These are art-direction starting values, not official brand specifications. Do not use color picking from a single lit pixel as the finished material's base color without checking multiple views.

## 5. Storyboard and transitions

### 5.1 Load and reveal

Show a small, honest loading state over a lightweight poster of the final model. Never invent a percentage when byte totals are unknown. Load the balanced model and essential assets first. A broken asset must lead to a useful retry state rather than an endless spinner.

The finished hero composition displays the whole product at roughly 72–82% of usable viewport height. Keep the head, handle and power-inspired control visible. The apparent weight comes from soft contact shadow, correct perspective, bevel highlights and a subtly visible floor. Do not show an unsupported claim that the real vacuum self-stands; this is a studio presentation pose.

Hero copy is limited to product identification, “Make a mess.” if composition benefits from it, and the Start label. The page should look complete with this small amount of text.

### 5.2 The right-side Start control

Create a tactile circular power-style button, visually related to the product's hardware: shallow bezel, subtle inset, crisp power glyph, and a short “Start” label. Its screen position is to the right of the product, around the upper-body/control area, with enough separation to tap easily.

It is a spatial interface control, not a fabricated physical button attached to the wrong part of the model. Reproduce the real product's physical controls only where the references show them. If the actual power control is sufficiently visible and reachable, it may also activate the same action.

Use a real accessible HTML button for the reliable interaction target. Its visual alignment may follow a projected 3D anchor, but clamp it to a safe screen region and never let it go behind the product. Minimum touch target: 44 × 44 CSS pixels; preferably 52 × 52.

Hover: a small lighting change and no more than a subtle scale response. Press: 1–2 px of perceived travel, a restrained click, then activation. Repeated presses must not spawn duplicate timelines or audio graphs.

### 5.3 Start sequence: approximately 2.5–3.5 seconds

1. The button depresses. The model's verified display/LED elements activate; the rollers begin to turn.
2. The vacuum inclines about the real head/neck articulation. The nozzle stays grounded; rigid pieces keep their shape.
3. The camera smoothly moves from the upright presentation into an elevated cleaning view. Light oak becomes the playable floor through a controlled material/scene transition.
4. A small, intentionally placed patch of dust and crumbs appears in front of the head. The vacuum performs one short, deliberate demonstration pass through part of it.
5. Controls fade in. The handoff occurs at exactly the current head position without a camera snap or a second product appearing. Leave some mess for the visitor.

This animation must share the same rig, simulation and cleanup logic as manual cleaning. Do not render a fake demo clip and swap to a different-looking interactive scene.

Keep world-space product scale constant. The camera changes perceived scale. Interpolate position, orientation and field of view with controlled easing; do not non-uniformly stretch the product. The vacuum body should remain connected to the head throughout.

Reduced-motion mode skips the sweeping camera move and demonstration pass, arriving in a stable interactive view with a short fade. A “Skip intro” action is available during the transition.

### 5.4 The playable composition

The floor fills most of the viewport. View it from a useful elevated perspective rather than a flat 2D orthographic board. The head is prominent enough to inspect and the dirt is large enough to read at natural scale. The upper handle may crop naturally in cleaning mode; never shrink or deform the entire product merely to keep every part visible.

Begin with a playable world-space area around 1.4–1.8 m wide and 1.0–1.4 m deep, then tune for composition and device aspect ratio. Define this rectangle separately from the larger decorative floor plane. Constrain placement and nozzle movement to reachable space. Exclude areas under persistent controls.

Desktop: a compact lower toolbar and a small corner utility group. Mobile: a narrow bottom dock with a drawer for dirt/floor choices. Controls collapse when a stroke begins. Avoid a large permanent sidebar that turns the scene into a dashboard.

### 5.5 The satisfying finish

When the actual remaining mess falls below the verified visual/computational completion tolerance, show a restrained “All clear.” message and “Make another mess.” action. Do not erase the remaining scene to fake completion. Resetting should be instant and enjoyable, without a modal or a page reload.

## 6. Interaction contract

Separate the experience state from the active tool. Camera animation, dirt placement and cleaning must never fight for the same pointer stream.

### 6.1 Main states

| State | Behavior | Exit |
| --- | --- | --- |
| loading | Load essential assets; display truthful progress/fallback | hero, recoverable error, unsupported |
| hero | Product presentation; Start active | starting |
| starting | One camera/rig timeline and one scripted cleaning pass | active, or Skip intro |
| active | Clean/Add dirt tools, floors, sound, reset controls | inspect, returning |
| inspect | Pause cleaning; frame the product for limited orbit inspection | active, returning |
| returning | Cancel interaction, reset rig/camera, return smoothly | hero |
| unsupported | Disclosed static fallback with product poster and explanation | Retry |

“All clear” is a derived status inside active, not a state that locks the user out. Backgrounding the tab suspends simulation and sound; resuming does not apply a large accumulated delta time.

### 6.2 Clean tool

- Use the same primary gesture on mouse and touch: drag within the stage to guide the head.
- On pointer down, preserve the head-to-pointer offset. Do not teleport the nozzle to a distant click.
- Raycast against the actual floor and feed a bounded target into a damped motion controller.
- The nozzle moves at a plausible maximum speed and accelerates/decelerates smoothly. Cleaning is evaluated along its actual movement, never at the raw cursor coordinate.
- While the drag is active, suction is active. On release, cancel or loss of focus, stop pickup and settle movement safely.
- Rollers and low-level motor idle may remain visually active after Start; the distinction between idle and cleaning should be subtle.
- Touch has a small screen-space offset so the fingertip does not cover the nozzle. Compute it consistently through projection/raycasting.
- UI presses never place dirt, move the vacuum, or clean behind the toolbar.
- Pointer capture belongs only to the active gesture. Handle pointercancel and lostpointercapture.
- Clicking/dragging the stage in Clean mode never rotates the camera. Product inspection has its own explicit mode.

### 6.3 Add dirt tool

- Opening Add dirt pauses pickup, parks the head just outside the placement zone, and reveals the material picker.
- Choices: Dust, Hair, Pet hair, Crumbs, Mixed.
- Three density choices: Light, Medium, Heavy. Use visual previews and short labels.
- Tap places a small scatter. Drag paints a continuous, irregular trail.
- Placement is based on distance traveled and a bounded time contribution, not browser frame count.
- Distribute particles organically, with varied scale/orientation and overlapping density patches. Avoid a stamp made of identical dots.
- Dirt remains grounded and does not appear over HTML controls or on the vacuum body.
- Enforce explicit instance/density budgets. When full, stop adding gracefully; never evict older visible dirt just to hide the budget.
- Selecting Clean collapses the picker and restores manual control without clearing the mess.

### 6.4 Supporting controls

| Control | Exact result |
| --- | --- |
| Make a mess | Add one bounded mixed preset in reachable space; preserve existing mess subject to the cap |
| Clear floor | Remove all dirt and reset the current mess accounting; keep the current view and floor |
| Floor | Switch Oak / Stone / Carpet; preserve existing dirt positions and cleaning state |
| Inspect | Pause simulation/pickup and present the full model for restrained orbit inspection |
| Back | Cancel active timelines/gestures and return to the original product presentation; clear the session mess |
| Sound | Explicit on/off toggle, off initially; persist only this preference if desired |

Keyboard: Tab reaches all controls; Enter/Space activates buttons; C selects Clean; A selects Add dirt; Escape exits a drawer/inspection first. With stage focus in Clean, arrow keys move the nozzle and Space enables pickup while held. Provide visible focus and a compact accessible help description. Do not hijack keyboard controls while a UI element is being edited.

## 7. The 3D asset is the critical path

### 7.1 Asset strategy

Start the reference and modeling work immediately. A UI can be built in parallel with a clearly labeled development proxy, but the finished experience cannot pass QA with that proxy.

Use this order:

1. Inspect any user-supplied exact model/CAD assets if present.
2. Conduct a bounded search for an exact, usable model with an appropriate license. Record whether it actually matches IP1251EUT. A model of an adapter, another vacuum, or a different PowerDetect family is not sufficient.
3. If no suitable asset is available, build the product in Blender using Python and available Blender tooling. Preserve the editable source and generation scripts.
4. If Blender is unavailable, check the existing installation paths and supported tools. Install normal project dependencies within the current permissions where feasible. A Blender MCP server is optional; headless Blender scripting is an acceptable primary route.
5. If image-to-3D tooling is already available and authorized, it may produce an initial base. Inspect, remodel and retopologize it. Do not trust generated logos, symmetry, controls, transparent bins or unseen geometry.
6. If no external modeling tool can run, create a detailed, reference-driven procedural mesh pipeline and export a real GLB. Use custom profiles, bevels and separate mechanical parts. Mark the limitation; do not claim a coarse primitive assembly meets the final visual bar.

Do not invent API keys, claim unavailable MCP tools ran, purchase models, or consume unapproved paid generation credits. Continue on the best available route and document a concrete blocker only when it materially prevents completion. Do not stop the whole web project merely because an optional asset service is unavailable.

### 7.2 Modeling requirements

Reconstruct the visible industrial design deliberately:

- Main motor housing with its actual nontrivial profile, filter/end-cap ribbing and vent pattern.
- Grip opening, battery profile and rear handle silhouette.
- Transparent dustbin with shell thickness, visible internal forms, seams and attachment points.
- The selected finish's grey housing and purple parts in their correct locations.
- Wand cross-section, release buttons, hinge housing, and folding articulation.
- Floorhead's broad, low silhouette; side caps; clear cover; wheels; neck; hose/connector details.
- Two visually distinct brush rolls based on close-ups: match their order, surfaces, stripe/chevron patterns and mounting.
- Realistically sized decals and markings, applied with clean UVs. Use properly sourced brand artwork if available; never fake the Shark logo with distorted generated lettering.
- Small construction details that survive the viewing distance: panel seams, fasteners, joint gaps, molded lips and plausible edge radii.

Use bevels and well-controlled normals to catch light. High polycount cannot compensate for an incorrect silhouette. Do not fill hidden internal space with invented machinery just to increase complexity.

Proportions inferred from references should live in a central parameter file. Keep a measurement ledger so improving a head width or bin length does not become an untraceable collection of magic numbers.

### 7.3 Required source outputs

- assets/source/powerdetect.blend when Blender is used.
- scripts/blender/build_powerdetect.py or an equivalent reproducible modeling script.
- scripts/blender/render_reference_views.py or an equivalent render/capture workflow.
- public/models/powerdetect-high.glb.
- public/models/powerdetect-balanced.glb.
- public/models/powerdetect-low.glb if required by the measured device budget.
- assets/manifest.json with provenance, license/status, SKU, units, bounds, node names and file sizes.
- assets/reference-comparison with labeled reference/render pairs.

If using an imported licensed asset, keep the source format and document preprocessing. Do not overwrite its source with destructive optimization. If a procedural route replaces Blender, provide editable mesh-generation source and explicitly state that no .blend was produced.

### 7.4 Rig and coordinate contract

Use meters and a consistent runtime Y-up coordinate system. The floor is XZ with Y = 0. Define forward once in the shared contract and document Blender-to-glTF axis conversion. Normalize imported assets once, not inside every frame update.

| Named node/anchor | Purpose |
| --- | --- |
| VacuumRoot | Overall translation and stable model origin |
| FloorHead | Floor-contacting assembly, independent of wand tilt |
| NeckPivot | Correct pivot between nozzle and wand |
| LowerWand | Lower rigid wand section |
| FlexPivot | Actual folding joint |
| UpperWand | Upper rigid wand section |
| MotorAssembly | Motor, handle and battery assembly |
| DustbinShell / DustbinContents | Separate clear enclosure and optional restrained fill visualization |
| RollerFront / RollerRear | Independently rotatable brush rolls |
| HeadLights | Verified physical light elements |
| PowerControlAnchor | Reference point for hero UI projection; not a fake physical switch |
| IntakeFront / IntakeRear | Measured nozzle pickup anchors/regions |
| FloorContactAnchors | Points used to validate contact against the floor |

The exact parent hierarchy must follow the reference's mechanics. Lock the hierarchy and local axes in a rig contract before the animation and simulation agents integrate. Mesh optimization must preserve animated nodes and required names. Intake/contact widths come from the finished floorhead mesh; do not treat the published overall product depth as the nozzle depth.

Use position-based control and constrained articulation. The nozzle should swivel and the wand lean with convincing resistance, while the root remains grounded. Do not rotate the entire appliance 180 degrees instantly when the user reverses a stroke. Reverse motion must also collect dirt.

### 7.5 Fidelity review before finishing

Render front, both three-quarter views, side, rear, floorhead close-up, motor/bin close-up and the cleaning pose. Match camera angle and focal length approximately before comparing with a reference; perspective mismatch is not a geometry error.

Check silhouette, component ratios, roller order, grip cutout, bin transparency, hinge position, colors and markings. Fix the three most visible discrepancies, render again, and repeat until no critical identity error remains. Use annotated image evidence. A self-awarded “9/10” without comparisons is not proof.

Do not claim engineering/CAD accuracy for inferred surfaces. If an unresolved detail is not reference-supported, note it in the handoff instead of fabricating certainty.

## 8. Materials, lighting and photographic realism

Use a physically based rendering workflow with correct texture color spaces and deliberate exposure. The default runtime renderer should be a well-supported WebGL2 path; WebGPU is optional only if it improves the result without removing the reliable fallback.

### 8.1 Materials

- Housing plastic: dielectric material with subtle roughness variation and molded surface detail; not metallic chrome.
- Purple finish: match the selected reference under neutral illumination; avoid excessive saturation.
- Metal parts: metallic response only where the source supports it.
- Rubber wheels, seals and grip details: softer highlights and a different roughness from the housing.
- Transparent bin: plausible clear polymer, controlled transmission/reflection, readable internal shapes and no doubled surfaces. A starting IOR around 1.49 is an artistic material estimate, not a measured product property.
- Rollers: fibers/patterns that read at normal camera distance without shimmer or hundreds of thousands of individual hairs.
- Floor: correct texture scale, subtle normal/roughness, visible but restrained reflections. Carpet should read as short fibers, not a flat green/brown plane.

Blender procedural material graphs do not automatically become working browser materials. Bake unsupported surface detail into exportable maps or rebuild it explicitly in the runtime. Verify the GLB in the actual website after every export change.

### 8.2 Lighting

Use a soft studio environment with a broad key, restrained fill and an edge highlight that separates the body. Create reflections that describe the industrial design. A dim material with no reflective structure will look cheap even if the geometry is correct.

Anchor the nozzle with dynamic contact/shadow support. Static floor lighting may be baked, but a static contact blob cannot be the only shadow during movement. Avoid floating parts, detached shadows and a dark AO outline around every edge.

Product lights illuminate a small plausible portion of the floor. Do not add a green laser or a scanning beam absent from this SKU. Treat the promotional turquoise rings in V5 as advertising illustration, not lighting reference.

Use restrained antialiasing and color management. Bloom, depth of field and film grain are optional finishing tools. They must never conceal modeling errors, blur the debris, bleach the LEDs, or make text illegible. Disable costly effects before sacrificing core product fidelity on slower devices.

## 9. Dirt simulation and cleanup

Build a convincing, deterministic visual simulation. Full fluid dynamics and thousands of rigid bodies are unnecessary. The essential quality is that the mess feels material, moves locally, and disappears through the nozzle where the user actually cleans.

### 9.1 Shared rules

- Debris is expressed in floor/world coordinates and has a stable ID or deterministic field location.
- Only powered, active pickup within the real nozzle intake/contact region removes dirt.
- No global fading, cursor-centered circular eraser, screen-space wipe, or radius that swallows nearby piles without contact.
- Use a narrow, tunable attraction region near the intake for visible movement; not a large force field.
- The pickup solver uses the head's swept path, including rotation. Fast movement cannot tunnel through the mess.
- Use fixed simulation steps or delta-normalized integration, with a cap on catch-up work.
- A spatial grid/hash limits nearby particle queries. Avoid scanning every strand and crumb every frame.
- The renderer and progress accounting share the same authoritative state. Do not show one mess while measuring a different hidden approximation.
- Forward and reverse cleaning must work, with the corresponding intake geometry remaining plausible.

### 9.2 Dust

Represent fine dust as a floor-attached density field/decal with high-frequency variation, plus a small number of visible specks where needed. A reasonable starting grid is 512 × 512 on high and 256 × 256 on balanced, scaled to the playable area.

Own the authoritative field on the CPU unless a GPU implementation demonstrably simplifies both visuals and accounting. Update the corresponding texture efficiently; avoid synchronous GPU readback every frame. No need for React state updates per cell.

Deposition creates irregular density and hue changes. Pickup erodes density only within the swept contact/intake footprint, leaving a clean track that matches the nozzle's width and shape. The edge can have slight physical irregularity without obvious circular brush stamps. The underlying floor material remains continuous through the cleaned path.

Tiny motes may move briefly near the intake. They should be sparse and short-lived, not a dust explosion.

### 9.3 Long hair

Use fine curved strands on the floor with varied length, curl and direction. Starting length range: approximately 3–15 cm, tuned for readability. Hair must not look like thick rubber cords.

Use lightweight ribbons/curves or a batched strand representation. Near the intake, an end or nearest segment becomes captured, the strand bends toward the nozzle, and its remaining visible length feeds inward over time. A small segment-chain or constraint-based solver is sufficient. Keep uncaptured portions on the floor until pulled in.

Do not delete the entire strand the instant its center enters a large radius. Do not implement an expensive full hair engine. Aim first for a convincing close-up with a bounded number of strands.

### 9.4 Pet hair

Use short fibers grouped into irregular, soft clumps. Vary clump density and orientation. A clump loosens/elongates slightly near the intake and then collapses into it. Keep strands thin and suppress noisy subpixel shimmer. This should look different from long human hair and from grey spheres.

### 9.5 Crumbs

Use a small reusable library of irregular, beveled crumb meshes with varied color and roughness. Starting sizes: a few millimeters up to roughly one centimeter.

On placement, crumbs make one short, damped settle/bounce onto the surface. Near pickup, they may roll or hop a few millimeters, accelerate toward the intake, become occluded under the head, then be removed. They must not travel through the outer shell or pass visibly through the front cover.

Use instancing and lightweight kinematics. If a rigid-body library improves a small subset, confine it there and demonstrate the benefit; it is not required for all debris.

### 9.6 Simulation accounting

Maintain normalized simulation mass or weighted coverage, not invented real grams:

- M_added: accumulated mess deposited during the current session.
- M_collected: mass removed by valid pickup.
- M_remaining: the actual mass still represented by the field/instances.
- Clear floor resets all three consistently. Adding more dirt increases M_added.

Maintain the invariant M_added ≈ M_collected + M_remaining within a documented numerical tolerance. If showing a percentage, define it as collected / added and handle the empty state explicitly. A particle removed by reset, cap handling or disposal must not be counted as vacuumed.

Completion tolerance should be small and visually checked, such as less than 0.5% residual weighted coverage with no clearly visible uncollected clump. Do not change the threshold simply to hide unreachable dirt. Prevent unreachable placement in the first place.

### 9.7 Starting content budgets

These are implementation targets to benchmark and adjust, not product claims:

| Detail | High | Balanced/mobile starting point |
| --- | --- | --- |
| Dust field | 512 × 512 | 256 × 256 |
| Discrete crumb instances | Up to 1,000 | Up to 400 |
| Long hair strands | Up to 100 | Up to 45 |
| Pet-hair clumps | Up to 45 | Up to 20 |
| Near-intake airborne specks | Up to 120 | Up to 40 |

Do not reduce the logical mess amount during a quality change. Simplify its representation while preserving IDs, positions and authoritative mass. Quality selection must not visibly clean the floor.

## 10. Extra polish that belongs in the core

### Responsive detection feedback

Let local dirt density drive a subtle increase in motor intensity and roller animation. Use verified indicator placement and colors when available. If exact indicator behavior cannot be verified, keep the hardware lighting neutral and show a tiny interface status such as “Detecting” only while meaningful. Never present made-up sensor measurements or battery life.

### Floor changes

Use three genuinely different surface treatments. Oak has realistic grain and joins; stone has fine mineral texture and restrained seams; carpet has short fibers and soft response. Preserve mess in normalized floor coordinates during the switch. Blend lighting/materials smoothly without erasing the simulation. Avoid adding water or wet spills to this dry-vacuum concept.

### Product inspection

The small Inspect action pauses the active mess and frames the complete model. Allow bounded orbit/zoom with collision-safe limits. Returning restores the same cleaning layout and debris. A short close-up preset for the head/bin is welcome if it remains a small control, not a separate marketing page.

### Sound

Default to muted with a clear sound toggle. Start/resume the Web Audio context only following an allowed user gesture. Keep one managed audio graph and ramp gains rather than starting a new loop for each event.

Use a tasteful motor layer, a light power click, and subtle material-specific pickup transients. Synthesize them if suitable recordings are unavailable; do not label synthesized sound as an authentic recording of this model. Sound responds to active cleaning and local dirt density. Suspend on tab hide, stop on Back, dispose on unmount. The experience must remain understandable with sound off.

Do not expand the initial project into a full furnished home, AR product placement, shopping cart, multiplayer game, user accounts, or a model configurator. Finish these core scenes to a high visual standard first.

## 11. Implementation architecture

Use a small, compatible, pinned toolchain. Inspect current stable versions and peer dependencies; do not copy arbitrary version numbers from an old example.

Suggested stack:

- Vite, React and TypeScript for a fast local project and minimal interface.
- Three.js with React Three Fiber; use Drei helpers selectively.
- A single animation owner for camera/rig transitions, such as GSAP or a small explicit timeline implementation.
- A lightweight state store for interface/state-machine data.
- Mutable typed arrays/refs for simulation and per-frame transforms.
- Blender plus glTF export for assets where available.
- Vitest for meaningful simulation/state tests and Playwright for browser flows/captures.

One Canvas, one render loop, one simulation clock. Do not mount independent scenes for each state. Avoid React setState inside hot per-frame loops. Dispose geometries, materials, textures, render targets, audio resources and listeners correctly.

Do not make server-side rendering or an application framework a prerequisite for a one-scene local experience. Do not add runtime calls to Claude, an image API or a paid service. The delivered site works from its shipped assets.

### 11.1 Project layout

Create these areas with clear ownership; adapt filenames if the repository already has a sensible structure:

| Path | Responsibility |
| --- | --- |
| src/app | Application state and orchestration |
| src/contracts | Shared types, rig metadata and coordinate conventions |
| src/scene | Canvas, camera, lighting, floor and composition |
| src/product | Asset loading, rig adapter and physical articulation |
| src/simulation | Dust, hair, crumbs, spatial queries and cleanup accounting |
| src/interaction | Pointer/keyboard mapping and control ownership |
| src/ui | Minimal controls, loading, accessibility and errors |
| src/audio | One managed audio engine |
| src/config | Product constants, quality tiers and art-direction tuning |
| public/models | Optimized GLB assets |
| public/textures | Runtime textures, environment and decals |
| assets/source | Editable 3D and texture source |
| assets/references | Product references and source manifest |
| scripts | Modeling, export, asset validation and capture helpers |
| tests | Simulation/unit tests and end-to-end browser tests |
| evidence | Screenshots, short interaction capture and measured reports |
| .claude/agents | Project-specific agent definitions |

### 11.2 Shared contracts before parallel implementation

The lead owns the initial contract. Agree on the following before several agents write dependent modules:

- ExperienceState, ActiveTool, DirtKind, SurfaceKind and QualityTier.
- Floor/world coordinate mapping and reachable bounds.
- VacuumRig nodes, pivot axes, units and nozzle contact geometry.
- InputTarget versus actual HeadPose.
- Simulation tick order and active-cleaning flag.
- addDirt, clearFloor, step, getRemainingMass and quality-change behavior.
- Events such as start, introComplete, toolChange, pickup, allClear and returnToHero.

Keep product constants configurable, including SKU, body dimensions, intake widths, material overrides, camera poses and motion tuning. Do not bury these throughout components.

### 11.3 Required scripts

Provide working package scripts for:

- npm run dev
- npm run build
- npm run preview
- npm run typecheck
- npm run test
- npm run test:e2e
- npm run assets:build
- npm run assets:validate
- npm run qa:capture

The first three must work without an external service. Start the preview on localhost using the available port, for example npm run dev -- --host 127.0.0.1. Report the URL the server actually prints rather than assuming a port. Asset rebuilding may require the documented Blender installation. Existing exported runtime assets must let the user run the site without installing Blender. Detect paths safely and use a task-specific variable such as BLENDER_BIN if necessary.

## 12. Configure and use project agents

The user explicitly requests agent-assisted implementation. You are responsible for actually using available delegation, not merely listing roles in the final answer.

Create project-local definitions in .claude/agents. Keep the main session on the user's selected Opus 5.5. Use model: inherit in each custom definition, and do not override an invocation to a cheaper model. If the actual parent model is different or model selection cannot be observed, state that accurately; creating a Markdown agent file does not change the current model.

Use the current documented Claude Code format. A minimal example is:

```yaml
---
name: product-modeler
description: Builds and validates the reference-matched PowerDetect 3D asset and rig.
model: inherit
---
```

Follow that frontmatter with the role's full instructions from this brief, owned files, required inputs, acceptance criteria and return format. Every agent must read this master brief, PRODUCT_REFERENCE.md, shared contracts and the current task entry before editing; do not assume it received the parent conversation. Omit a tools field to inherit available tools unless a specific restriction is useful and supported. Do not invent tool names or add bypass-permission modes. Preserve existing user/team settings. [T1–T2]

New custom agents may not be discoverable in an already-running session, depending on version and whether the agents directory existed at startup. If that happens, use available general-purpose delegation with the full role prompt and the same model selection, then keep the saved custom definitions for future sessions. Do not get stuck waiting for a restart. If no native delegation is available, execute the role passes sequentially and report this fallback honestly. [T1]

### 12.1 Roles and ownership

| Agent | Owned work | Required return |
| --- | --- | --- |
| reference-director | PRODUCT_REFERENCE.md, reference manifest/contact sheet, art-direction notes | Chosen variant; observed/inferred details; material/shape notes; missing views |
| product-modeler | assets/source, modeling/export scripts, rig metadata and GLBs | Editable model; valid named rig; multi-view comparisons; size/triangle report |
| lookdev-artist | Lighting, runtime materials, textures, post-processing and quality tuning | Neutral and final look captures; material comparisons; performance impact |
| simulation-engineer | Dust/hair/crumb systems, spatial queries, swept pickup, accounting tests | Working simulation; edge-case tests; bounded resource usage |
| interaction-designer | Camera/rig choreography, input mapping, minimal UI and audio integration | Full Start-to-clean flow on desktop/mobile; accessible controls |
| visual-qa-engineer | Browser verification, screenshots, performance capture and defect reports | Reproducible findings with image/log evidence; no unsupported pass claims |

The lead owns dependency versions, shared contracts, final composition, integration, conflict resolution and delivery. The QA agent reports defects; it does not silently edit every other agent's files.

### 12.2 Scheduling

Run at most three worker agents concurrently unless the environment clearly supports more. Keep one Blender writer and one browser capture owner at a time. Avoid simultaneous GPU-heavy renders and performance measurements.

Suggested order:

1. Reference director begins while the lead scaffolds and the simulation engineer prototypes the cleanup math.
2. After the reference/rig contract, the product modeler builds the asset. Interaction work proceeds against the same rig interface using a temporary proxy.
3. Look development begins as soon as a reference-correct first model is available; coordinate material/node ownership with the modeler.
4. Integrate the real asset, then tune motion and cleanup together.
5. Visual QA inspects the complete scene and assigns specific defects back to the relevant owner.
6. Lead verifies the fixes and performs the final handoff.

Do not have multiple agents rewrite package.json, the root scene, lockfiles or shared contracts concurrently. Delegate implementation areas, not overlapping copies of the entire project. Each agent's report must identify changed files, checks actually run, unresolved issues and evidence paths.

### 12.3 Project memory and continuation

Create or extend CLAUDE.md without discarding existing instructions. Include the priority order, chosen SKU, core constraints, model/agent policy, ownership and verification requirements. Maintain TASKS.md and DECISIONS.md so a long session can resume without replacing settled decisions.

Proceed autonomously on ordinary design/implementation choices. Do not stop after each milestone to ask whether to continue. Do not disable permissions, alter unrelated projects, delete user work, or claim that local settings override access controls. A blocked optional tool is not permission to bypass its restrictions.

## 13. Performance targets and adaptive quality

Treat these as targets to measure on declared hardware, not as guaranteed numbers across all devices.

| Measure | Initial target |
| --- | --- |
| Desktop interaction | Around 60 fps; p95 frame time below 20 ms on the measured representative machine |
| Mobile interaction | Stable 30 fps or better on an actual tested mid-range device; adapt to 60 where possible |
| Balanced first-load payload | Preferably no more than 5 MB transferred for essential assets/code |
| First interactive scene | Aim for 6 seconds or less in a documented 10 Mbps lab profile; report actual measurement |
| High model | Approximately 120k–220k triangles if warranted by visible detail |
| Balanced model | Approximately 50k–100k triangles while preserving silhouette |
| Draw calls | Aim below 150 high / 90 balanced in the representative active scene |
| Pixel ratio | Start capped around 1.5–2 desktop and 1–1.5 mobile; adapt based on frame time |
| Repeated use | No monotonic resource growth after reset/re-entry cycles |

These are budgets, not reasons to throw away product identity. Improve material batching, invisible geometry, instancing, texture compression, effect resolution and shadows before simplifying recognizable surfaces.

Use a supported glTF compression path such as Meshopt and appropriate texture compression when tools are available. Verify matching decoders are shipped locally and loaded correctly. Missing optional compression tooling must not break the usable uncompressed fallback. Preserve the animated hierarchy during optimization. [T3]

Quality changes have hysteresis and a cooldown; they cannot oscillate every frame. Lower effects, shadow resolution and subpixel decoration first. Logical dirt and cleanup accuracy remain intact. A scene that runs fast because the hair disappeared is not an acceptable optimization.

Render on demand in a fully still/paused hero when appropriate; use continuous rendering while rollers, transitions or simulation are active. Pause work in hidden tabs. Record renderer counters and frame times in a development-only overlay that is absent from the default experience. [T4]

## 14. Verification that must actually happen

Run the implementation, inspect screenshots, interact with it and fix observed problems. Passing a build alone does not validate a 3D experience.

### 14.1 Meaningful automated checks

- Coordinate conversion: screen-to-floor and world-to-field mapping agree at corners and center.
- Swept pickup: slow/fast strokes and rotated head movement do not leave tunneling gaps.
- Proximity: dirt outside the bounded intake region remains unchanged.
- Reverse cleaning: backward strokes collect through the intended geometry.
- Frame-rate consistency: equivalent trajectories at different step schedules produce close pickup results.
- Accounting: deposition/pickup/reset preserve the mass invariant within tolerance.
- Tool isolation: Add dirt cannot clean; toolbar clicks cannot alter the stage.
- State transitions: repeated Start, Skip intro, Back and reset do not create duplicate loops.
- Quality switching: logical mess and positions do not change.

Use deterministic seeds for capture and tests. Avoid tests that simply repeat an implementation constant. Test the behavior that could visibly break.

### 14.2 Browser interaction checks

1. Load from a fresh page, wait for the real asset, and verify the hero.
2. Activate Start by mouse and by keyboard; inspect the entire transition.
3. Place each dirt category at center and near reachable boundaries.
4. Clean with slow, fast, diagonal, curving and reverse strokes.
5. Drag onto/over a UI control, cancel a pointer, and leave/re-enter the window.
6. Switch tools rapidly; confirm no ghost placement or cleanup.
7. Switch all floors with existing dirt; verify persistence and ground contact.
8. Inspect the product and return; confirm the same mess and state.
9. Toggle sound; hide/show the tab; confirm no runaway audio or accumulated simulation jump.
10. Clear floor and add new mess repeatedly; return to hero and restart at least ten times.
11. Exercise asset failure, reduced motion and unavailable WebGL fallbacks.
12. Check that all loaded runtime assets resolve locally and there are no scene/shader/console errors.

### 14.3 Viewports and actual-device honesty

Capture at least 1440 × 900, 1920 × 1080, 390 × 844, 430 × 932, and one small landscape viewport. Test available Chromium and WebKit paths. Browser emulation is not an actual iPhone performance test; label untested devices and engines explicitly.

Safe-area insets, dynamic viewport height and touch cancellation must be handled. Do not break the browser's accessible UI to achieve full-screen appearance. A user must not need precise fingertip placement to operate the nozzle or Start button.

### 14.4 Visual evidence

Save real captures with deterministic scene seeds:

- hero-desktop.png and hero-mobile.png.
- product-front.png, product-side.png, product-back.png and product-three-quarter.png.
- head-closeup.png and bin-closeup.png.
- start-transition-early.png, start-transition-mid.png and start-transition-end.png.
- dust-before.png, dust-midstroke.png and dust-after.png.
- hair-capture-sequence images showing partial strand ingestion.
- crumbs-mid-pickup.png.
- carpet-active.png and stone-active.png.
- mobile-controls.png and reduced-motion.png.
- A short recorded real interaction, if the available browser tooling supports capture.

Open the captured images and inspect them. Do not just create files and assume they look good. Keep source-matched product comparisons alongside the final artistic shots. A beautiful Blender render cannot substitute for an actual browser screenshot of the delivered scene.

### 14.5 Blocking visual defects

The following prevent a “finished” claim:

- Product silhouette or colorway clearly differs from the selected references.
- Generic cylinders/boxes remain as the final motor, floorhead or handle.
- Detached parts, incorrect pivots, intersecting clear shells, broken normals or mirrored decals.
- The nozzle floats, penetrates the floor, or has a visibly detached shadow.
- A static image or video replaces the interactive 3D model.
- Hair looks like thick wires; dust looks like confetti; crumbs look like identical spheres.
- Dirt vanishes remotely or follows a cursor eraser rather than the nozzle.
- The Start animation snaps, changes product scale, duplicates the vacuum or breaks contact.
- An essential interaction is inaccessible on touch or covered by the UI.
- Unhandled asset failures, blank canvas, recurring shader errors or uncontrolled audio.

## 15. Build milestones and definition of done

Complete the milestones in order, continuing without routine approval questions:

| Milestone | Evidence required |
| --- | --- |
| M0 — Reference and foundation | Correct SKU ledger, source board, running scaffold, agent definitions and shared contracts |
| M1 — Functional slice | One dirt type, actual nozzle path, working Start-to-active transition and stable input |
| M2 — Product fidelity | Detailed real model, named rig, materials, matched reference captures and no identity defects |
| M3 — Complete interaction | All required dirt/floors, manual cleanup, inspect/back/reset, sound and reduced motion |
| M4 — Visual refinement | Browser screenshots reviewed; transitions, floor contact, lighting and material response corrected |
| M5 — Delivery | Production build, passing relevant checks, measured performance, editable sources and running local preview |

M1 may use a development proxy. It is an internal integration step, not the requested final result. The final build must load the actual finished asset from M2.

After each visual review, fix the largest concrete defects first. Do not stop at the first recognizable vacuum. Do not run endless aesthetic loops without identifying a remaining problem; once the objective requirements pass, finish the delivery.

If a real blocker prevents a requirement, deliver all working parts with the limitation clearly identified, evidence of attempts, and the exact missing asset/tool. Never mark blocked work as complete or call an inferred reconstruction an exact manufacturer model.

## 16. Final handoff to Eray

Leave the local preview running when the environment supports it. The final response is in Turkish and includes:

1. The exact local URL and how to reopen it.
2. A short description of the working Start → add mess → clean loop.
3. Which product variant was modeled and which details remain inferred.
4. Paths to the editable asset, optimized GLBs, source code, reference comparisons and QA evidence.
5. Checks actually run, measured hardware/browser information and any remaining limitation.

Create a concise README.md with installation, development, build, asset rebuild and control instructions. Include an ASSET_CREDITS.md for shipped third-party material and a QA_REPORT.md with factual results. Keep the final UI free of development terminology and debug panels.

Do not claim that it is photorealistic, production-ready, 60 fps everywhere or pixel-perfect merely because the code runs. Let the delivered visuals and measured checks support the conclusion.

## 17. Technical reference links

Use current installed-version documentation when implementation details differ. These links inform the workflow; this brief's budgets, interaction design and simulation algorithms are project decisions.

- **[T1] Claude Code custom subagents:** https://code.claude.com/docs/en/sub-agents
- **[T2] Claude Code model configuration:** https://code.claude.com/docs/en/model-config
- **[T3] Three.js GLTFLoader, supported extensions and decoder setup:** https://threejs.org/docs/pages/GLTFLoader.html
- **[T4] React Three Fiber performance guidance:** https://r3f.docs.pmnd.rs/advanced/scaling-performance
- **[T5] Blender glTF exporter source and version-specific manual links:** https://github.com/KhronosGroup/glTF-Blender-IO
- **[T6] Three.js documentation:** https://threejs.org/docs/

## 18. Begin now

Read the entire brief. Inspect the project and preserve existing work. Create the task ledger and project agents, confirm the reference model, start the asset pipeline and implement the first functional slice. Continue through modeling, integration, browser inspection and fixes until the complete local experience meets the requirements above.

The user is asking for an unusually well-made, tactile product experience. Give the 3D asset and cleaning behavior the majority of your attention. The interface should provide just enough guidance for the visitor to make a mess and enjoy cleaning it.
