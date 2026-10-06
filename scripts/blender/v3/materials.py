"""
Material library for the v3 (IP3251 / IP3251EUT, TR 'mor-siyah': gunmetal + purple, bronze wand, white dock) build.
Owned by the materials agent.

make_materials(tier) populates lib.MATS with every name in PARTS_CONTRACT.md (+ M_RollerFront, agreed with the lead).
Principled BSDF only, glTF-exportable node graphs:
  Image(ORM, Non-Color) -> Separate Color -> G: Roughness; Metallic = constant factor (glTF: factor x ORM.B)
  Image(normal, Non-Color) -> Normal Map(strength) -> Normal             (exported as normalTexture + scale)
  Image(decal atlas, sRGB) -> Base Color, Alpha                          (exported as baseColorTexture, BLEND)
  fabric: Sheen Weight/Tint/Roughness (KHR_materials_sheen) + fibre normal
Textures live in assets/source/textures/v3/ (tools/build_textures.py, tools/build_decals.py); run build_textures.py again
after changing a roughness in COLOURS (ORM tiles are per roughness).

Colour sources: see the comment above each COLOURS entry (U = user frames = truth, R = official cl-eut-01 render).

Helpers for modelers:
  DECALS                       -> slots from decals.json
  decal_uv(slot, s, t)         -> Blender UV inside the slot's ink box (s, t in 0..1, t = glyph up)
  ensure_uvs(objects, tile)    -> box-projected UVs for meshes that have none (assembler calls before export)
  M_RollerFront UVs            -> U = around the roller (0..1 = 360 deg), V = along the axis (0 = -x end, 1 = +x end)
"""
import json
import math
import os

import bpy
import lib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(ROOT, "assets", "source", "textures", "v3")

try:
    with open(os.path.join(HERE, "decals.json")) as _f:
        DECALS = json.load(_f)["slots"]
except Exception:  # noqa: BLE001
    DECALS = {}


def decal_uv(slot, s, t, rect="ink"):
    u0, v0, u1, v1 = DECALS[slot][rect]
    return (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)


def _srgb2lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _lin(hexcol):
    return (*[_srgb2lin(c) for c in _hex(hexcol)], 1.0)


# name: (base sRGB, roughness, metallic, finish, notes)
# finish: "plastic" (satin grain ORM + micro normal), "brushed" (streak ORM + groove normal), "fabric" (fuzzy microfibre:
# sheen + fibre normal, no ORM), None (flat factors)
# Samples: U = user frames (user/user-video-166x, colour truth), R = official renders (raw/cl-eut-01 front, alpha-masked),
# T = tr-ip3251eut-* photography.  "lit / median / shade" = 80th pct / median / 20th pct of class-selected pixels.
COLOURS = {
    # browser r1: handheld read lighter than U1663 (#64636a median, p20 #504f54) under the app light -> #636367.
    # U1663 motor body #67676c (lit #77767b), dock post #58595e; R motor #64625d / lit #77756f. Satin metallic-flake paint look.
    "M_Gunmetal": ("#636367", 0.42, 0.2, "plastic", "main gunmetal body plastic (motor body, wand ends, dock post, cradle)"),
    # round 2: #47484c -> plinth/white ratio 0.24 vs cl-eut-01 0.37 (#494743 / #c7c6c6) -> #505155.
    # lead 2026-10-05 (user rejection): TR colour = 'Koyu Gri'; user head body 1663 neck #3b3c40, 1667 #2d292e, front lip
    # #393c41..#494f54 -> M_Charcoal #36373b (head/handle); dock keeps the lighter graphite as M_DockGraphite.
    # lead ref v2 dock graphite #47484c; round 1 #3e3e42 rendered the dock post #201f23 vs U1663 post #58595e.
    # U1667 head body #2a262b, lower collar #39393d; U1668 handle near-black; R dock lower band #494743 (lit)
    "M_Charcoal": ("#45464a", 0.50, 0.0, "plastic", "TR 'Koyu Gri' dark charcoal: head body, neck, collars, handle frame, battery"),
    # dock post / plinth / base plate (kept lighter than the head: U1663 base plate #4d4f52, cl-eut-01 plinth #494743)
    "M_DockGraphite": ("#4c4d51", 0.46, 0.0, "plastic", "dock graphite: post, cradle, plinth, base plate [added]"),
    # lead ref v2 proposals (2026-10-05): purple #4a2f86, gunmetal #6a6a6e, dock white #e6e9eb, dock graphite #47484c,
    # mint roller #4fcdb8, wand bronze-gold #a68d64 -> blended with the samples below (user frames = truth).
    # U1663 cap: lit #6148ab / median #3d2675 / shade #240d44 (several flutes, 67k px); left flank #4e3880; bin ring #4e3a7b lit;
    # U1664 hinge/side caps #442caf (LED-tinted, excluded); R cap #3f2859 -> lit #613d85 (render grade more magenta).
    # round 2: #4d3288 metal 0.45 rendered #3b1a73 vs U #3d2675 (too blue-saturated) -> greyer base, metal 0.32.
    # Strong lit/shade contrast + crisp highlight => metallic-look satin paint (metal 0.45).
    "M_Purple": ("#4f3786", 0.30, 0.32, "plastic", "satin metallic-look purple: ribbed cap, bin ring, hinge discs, neck disc, side caps"),
    # round 5: #a8916c rendered #624f2c (b/r 0.45, olive-gold, over-saturated by the metallic env) -> #ab9c84:
    # goldener hue than r4 (g/r 0.91) with b/r 0.77 so it renders between U (#5d4b41) and R champagne (#aaa18b).
    # round 4 (lead + wand agent): #a99282 read reddish brown -> bronze-gold #a8916c (less red; lead ref #a68d64).
    # round 1 (Cycles studio): #a68c6c rendered #5b4627 (too yellow, wood-like) vs U #5d4b41 -> pinker, less saturated.
    # U1667 wand (lit room) median #4e3d31 lit #5f4f44; U1663 #5d4b41; floor in the same frame #9a9795 -> F0 ~ px / 0.6 =
    # #9e8371. R/T render champagne #aaa18b..#bcb39a (hi #eee2c3). Blend toward the user truth: bronze-champagne.
    "M_Bronze": ("#ab9c84", 0.34, 0.8, "brushed", "anodized bronze/champagne wand tube (brushed along the tube)"),
    # round 3: #c4b896 metal 0.65 read dark gold (env-dominated); U label is ~1.3-1.5x the body -> lighter, less metal.
    # U1663 label #86816d lit #a7a497; R label lit #eee2c3, mid #bcb39a. Lighter + yellower than the wand.
    "M_Champagne": ("#d2c9aa", 0.32, 0.45, "brushed", "champagne POWERDETECT label plate band / dock badge"),
    # U1663 bin frame #a1a7ac lit #c3cbd1, lower #808286 / lit #bac1c4; R frame lit #e9e9eb
    "M_SilverBrush": ("#b8bdc1", 0.30, 1.0, "brushed", "brushed silver bin frame / Shark band / trims"),
    "M_Chrome": ("#d3d5d8", 0.18, 1.0, None, "bright metal: cyclone mesh shroud, screws, contacts"),
    # U1663 rear brushroll core (through window): median #59999c lit #71b9bb shade #35686b; U1667 #558782 (behind cover).
    # Fabric: sheen gives the soft grazing bloom seen on the roller edge.
    "M_Turquoise": ("#56c2b4", 0.85, 0.0, "fabric", "mint/turquoise soft roller fabric + turquoise accents"),
    # U1663 chevron strip pale yellow-tan through the cover (#aeb99d, mint-tinted) -> de-tinted pale straw yellow
    "M_RollerFibre": ("#d4cb98", 0.9, 0.0, "fabric", "yellow/tan chevron-V bristle-fibre strips on the rear brushroll"),
    # U1663 dock canister #e4edf8 (clipped highlights, cool), R #c7c6c6 (shaded side). Satin white ABS.
    "M_White": ("#e7e9eb", 0.34, 0.0, "plastic", "dock canister / tower, satin white"),
    # lead: matte light-grey printed badge plates (duoclean DETECT plate on the head cover) — a metal here hot-spotted
    "M_LabelGrey": ("#aeb1b4", 0.5, 0.0, "plastic", "matte light-grey label plate"),
    "M_Rubber": ("#19191b", 0.74, 0.0, "plastic", "matte black soft-touch: grip, wheels, seals (U1668 grip #161318)"),
    "M_Bristle": ("#18181a", 0.78, 0.0, None, "black brush strip / bristles"),
    "M_Screen": ("#060708", 0.05, 0.0, None, "glossy black screen glass / dock dial lens / bin-full window"),
    "M_Hose": ("#2a2a2e", 0.55, 0.0, None, "flex hose"),
    "M_Dust": ("#7c7064", 0.95, 0.0, None, "debris in the bin"),
}

# LED / emissive: (base sRGB, emission sRGB, strength, notes). Runtime (productMaterialsV3.ts) drives intensity/colour.
EMISSIVE = {
    # lead ref v2: FRONT corner headlights are cool WHITE (U1667 white floor pool on the carpet)
    "M_LED": ("#eef2ff", "#e8eeff", 1.0, "floorhead front-corner headlights (cool white)"),
    # rear-corner LEDs beside the wheels + thin strip behind the roller window: violet. U1664-1666 lit LED pixels median
    # #7d67ec, core #a797f3, floor glow #9082f1; lead ~#7a4cff
    "M_LEDAccent": ("#d9d2ff", "#7a4cff", 1.0, "floorhead rear-corner violet LEDs + violet strip [added per lead]"),
    # U1668 ring median #4936e8 core #4b37f1; lead ref v2 ~#6a3cff -> #5f3cff
    "M_LEDRing": ("#2a1d55", "#5f3cff", 1.0, "handheld screen LED ring (white/pink/purple by DETECT state)"),
    # dock DUST BIN FULL window icons (S1 p14 'TOZ KUTUSU DOLU GOSTERGESI'); textured with the decal atlas (slot dock_binfull)
    "M_DockDisplay": ("#0b0c0d", "#f4f6ff", 0.0, "dock bin-full light (atlas-textured; off by default, runtime lights it)"),
}

_IMG_CACHE = {}


def _img(name, colorspace="Non-Color"):
    path = os.path.join(TEX, name)
    if not os.path.exists(path):
        print(f"[materials] missing texture {path} — run tools/build_textures.py / build_decals.py")
        return None
    key = (path, colorspace)
    if key not in _IMG_CACHE:
        im = bpy.data.images.load(path, check_existing=True)
        im.colorspace_settings.name = colorspace
        _IMG_CACHE[key] = im
    return _IMG_CACHE[key]


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get("Principled BSDF")
    lib.MATS[name] = m
    return m, nt, b


def _tex_node(nt, img, x, y):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    t.location = (x, y)
    t.interpolation = "Linear"
    return t


def _finish(nt, b, finish, normal_strength, rough):
    if finish == "fabric":
        orm = None
        nrm = _img("fabric_normal.jpg")
    else:
        orm = _img(f"orm_{finish}_r{int(round(rough * 100)):02d}.jpg")
        nrm = _img("plastic_normal.jpg" if finish == "plastic" else "brushed_normal.jpg")
    if orm is not None:
        t = _tex_node(nt, orm, -700, 0)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        sep.location = (-400, 0)
        nt.links.new(t.outputs["Color"], sep.inputs["Color"])
        nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
        # metallic stays a constant factor: glTF exports metallicFactor x texture.B (B = 1 brushed / 0 plastic)
    if nrm is not None:
        t = _tex_node(nt, nrm, -700, -320)
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.location = (-400, -320)
        nm.inputs["Strength"].default_value = normal_strength
        nt.links.new(t.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])


def _sheen(b, tint_hex, weight=0.7, rough=0.45):
    """microfibre pile: KHR_materials_sheen-exportable Principled sheen."""
    b.inputs["Sheen Weight"].default_value = weight
    b.inputs["Sheen Roughness"].default_value = rough
    b.inputs["Sheen Tint"].default_value = _lin(tint_hex)


def _thin_clear(nt, b, tint_hex, shadow_t=1.0):
    """Cycles-only branch: shadow rays pass through a tinted Transparent BSDF so lit interiors (brushroll, cyclone)
    are not starved by the closed refractive shell (no caustics in Cycles). The glTF exporter reads the ALL-target
    output (plain Principled transmission); Cycles prefers the CYCLES-target output."""
    out_all = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    out_all.target = "ALL"
    lp = nt.nodes.new("ShaderNodeLightPath")
    lp.location = (-200, 400)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.location = (0, 300)
    c = _lin(tint_hex)
    tr.inputs["Color"].default_value = (*[min(1.0, v ** 0.5 * shadow_t) for v in c[:3]], 1.0)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.location = (300, 300)
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(b.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    out_c = nt.nodes.new("ShaderNodeOutputMaterial")
    out_c.target = "CYCLES"
    out_c.location = (550, 300)
    nt.links.new(mix.outputs["Shader"], out_c.inputs["Surface"])
    out_c.is_active_output = False
    out_all.is_active_output = True


def make_materials(tier="high"):
    lib.MATS.clear()
    _IMG_CACHE.clear()
    textured = tier == "high" or tier == "balanced"
    for name, (hexcol, rough, metal, finish, _n) in COLOURS.items():
        m, nt, b = _new(name)
        b.inputs["Base Color"].default_value = _lin(hexcol)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if finish and textured:
            # ORM tile per material roughness (tools/build_textures.py), so glTF roughness = this value +- grain
            _finish(nt, b, finish, {"plastic": 0.35, "brushed": 0.12, "fabric": 0.9}[finish], rough)
            m["roughnessTarget"] = rough
        if finish == "fabric":
            _sheen(b, "#ffffff" if name == "M_Turquoise" else "#fff4d0", 0.6)
        if name == "M_Purple":
            # metallic-look paint: thin clear coat gives the crisp flute highlights seen in U1663 / R
            b.inputs["Coat Weight"].default_value = 0.5
            b.inputs["Coat Roughness"].default_value = 0.12
        if name == "M_Screen":
            b.inputs["Coat Weight"].default_value = 1.0
            b.inputs["Coat Roughness"].default_value = 0.03

    # front soft roller: black microfibre with the two-start turquoise helix (texture U = around, V = along the axis)
    m, nt, b = _new("M_RollerFront")
    b.inputs["Base Color"].default_value = _lin("#151717")
    b.inputs["Roughness"].default_value = 0.92
    img = _img("roller_front_basecolor.jpg", "sRGB")
    if img is not None and textured:
        t = _tex_node(nt, img, -500, 200)
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if textured:
        _finish(nt, b, "fabric", 1.0, 0.92)
    _sheen(b, "#4a4a4a", 0.3, 0.6)   # browser r1: white sheen 0.8 washed the black pile to mid grey

    # clear bin: water-clear PC, faint cool tint (U1663 bin reads neutral-cool over the purple ring / silver frame)
    m, nt, b = _new("M_ClearBin")
    b.inputs["Base Color"].default_value = _lin("#eef3f5")
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    _thin_clear(nt, b, "#eef3f5")
    # floorhead clear cover: water-clear (U1663: mint roller seen nearly unattenuated, #59999c through vs #71b9bb lit)
    m, nt, b = _new("M_ClearCover")
    b.inputs["Base Color"].default_value = _lin("#e9eef0")
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    _thin_clear(nt, b, "#e9eef0")

    for name, (base, emis, strength, _n) in EMISSIVE.items():
        m, nt, b = _new(name)
        b.inputs["Base Color"].default_value = _lin(base)
        b.inputs["Roughness"].default_value = 0.3
        b.inputs["Emission Color"].default_value = _lin(emis)
        b.inputs["Emission Strength"].default_value = strength
        if name == "M_DockDisplay":
            # icon plate: atlas slot dock_binfull -> glyph alpha + emissive colour (glTF emissiveTexture, BLEND)
            img = _img("decal_atlas.png", "sRGB")
            if img is not None:
                t = _tex_node(nt, img, -500, 100)
                img.alpha_mode = "STRAIGHT"
                nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
                nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
                b.inputs["Base Color"].default_value = _lin("#2a2b2c")
            for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                try:
                    setattr(m, attr, val)
                except Exception:  # noqa: BLE001
                    pass

    # marking atlas: printed ink, satin, alpha-blended decal plates
    m, nt, b = _new("M_Decal")
    b.inputs["Roughness"].default_value = 0.42
    img = _img("decal_atlas.png", "sRGB")
    if img is not None:
        t = _tex_node(nt, img, -500, 100)
        img.alpha_mode = "STRAIGHT"
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(t.outputs["Alpha"], b.inputs["Alpha"])
    else:
        b.inputs["Base Color"].default_value = _lin("#eeeeee")
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
        try:
            setattr(m, attr, val)
        except Exception:  # noqa: BLE001
            pass
    try:
        m.use_backface_culling = True
    except Exception:  # noqa: BLE001
        pass


TEXTURED = tuple(n for n, v in COLOURS.items() if v[3]) + ("M_RollerFront",)


def ensure_uvs(objects=None, tile=0.05):
    """Box-project a 'UVMap' (1 texture tile = `tile` m) onto meshes that have no UV layer and use a textured
    material. Side faces get V = world up, so brushed streaks run along vertical parts (the wand) by default."""
    objs = objects if objects is not None else [o for o in bpy.data.objects if o.type == "MESH"]
    n_done = 0
    for ob in objs:
        if ob.type != "MESH":
            continue
        me = ob.data
        if len(me.uv_layers) or not any(s.material and s.material.name.split(".")[0] in TEXTURED for s in ob.material_slots):
            continue
        mw = ob.matrix_world
        nmat = mw.to_3x3().inverted_safe().transposed()
        uvl = me.uv_layers.new(name="UVMap")
        verts = me.vertices
        uv = [0.0] * (len(me.loops) * 2)
        for p in me.polygons:
            n = nmat @ p.normal
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            for li in p.loop_indices:
                co = mw @ verts[me.loops[li].vertex_index].co
                if az >= ax and az >= ay:
                    u, v = co.x, co.y
                elif ax >= ay:
                    u, v = co.y, co.z
                else:
                    u, v = co.x, co.z
                uv[li * 2] = u / tile
                uv[li * 2 + 1] = v / tile
        uvl.data.foreach_set("uv", uv)
        n_done += 1
    print(f"[materials] ensure_uvs: box-projected {n_done} meshes")
    return n_done


def swatch_scene(out_png, samples=48, res=1400, light_scale=1.0, world=None):
    """Render every material on a sphere + a short cylinder under the preview.py studio (for lookdev comparison)."""
    import sys
    sys.path.insert(0, HERE)
    import preview  # noqa: E402
    from mathutils import Vector

    for nm, hx in (("CAL_Grey18", "#767676"), ("CAL_White90", "#f3f3f3")):  # calibration cards (albedo 0.18 / 0.90)
        m, nt, b = _new(nm)
        b.inputs["Base Color"].default_value = _lin(hx)
        b.inputs["Roughness"].default_value = 0.9
    names = list(COLOURS) + ["M_RollerFront", "M_ClearBin", "M_ClearCover"] + list(EMISSIVE) + ["M_Decal", "CAL_Grey18", "CAL_White90"]
    cols = 6
    objs = []
    for i, n in enumerate(names):
        x = (i % cols) * 0.09
        z = -(i // cols) * 0.11
        bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=0.03, location=(x, 0, z + 0.035), calc_uvs=False)
        s = bpy.context.object
        bpy.ops.object.shade_smooth()
        bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.012, depth=0.06, location=(x + 0.028, -0.03, z + 0.03), calc_uvs=False)
        c = bpy.context.object
        bpy.ops.object.shade_smooth()
        for o in (s, c):
            o.data.materials.append(lib.MATS[n])
            objs.append(o)
    if "M_Decal" in lib.MATS:  # show the atlas on a card
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.225, 0.06, 0.16), rotation=(math.pi / 2, 0, 0))
        pl = bpy.context.object
        pl.scale = (0.24, 0.24, 1)
        pl.data.materials.append(lib.MATS["M_Gunmetal"])
        objs.append(pl)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.225, 0.0595, 0.16), rotation=(math.pi / 2, 0, 0))
        dc = bpy.context.object
        dc.scale = (0.24, 0.24, 1)
        dc.data.materials.append(lib.MATS["M_Decal"])
    ensure_uvs(objs, tile=0.05)
    mn, mx = lib.world_bbox(objs)
    center = (mn + mx) / 2
    size = (mx - mn).length
    sc = preview.setup_scene(samples, "cycles")
    preview.add_lights(sc, center, size)
    for o in sc.objects:
        if o.type == "LIGHT":
            o.data.energy *= light_scale
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value *= light_scale
    if world is not None:
        sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = world
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = (mx - mn).x * 1.15
    cam_d.sensor_fit = "HORIZONTAL"
    cam.location = center + Vector((0, -1, 0.25)).normalized() * size * 3
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * ((mx - mn).z + 0.03) / ((mx - mn).x) * 1.1)
    sc.render.film_transparent = False
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    return names
