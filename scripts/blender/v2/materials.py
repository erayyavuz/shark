"""
Material library for the v2 (IA3246GN Sagewood) build. Owned by the materials agent.

make_materials(tier) populates lib.MATS with every name in PARTS_CONTRACT.md (+ M_SilverBrush, M_PlateGrey, M_LEDRing).
Principled BSDF only, glTF-exportable node graphs:
  Image(ORM, Non-Color) -> Separate Color -> G: Roughness; Metallic = constant factor (glTF: factor x ORM.B)
  Image(normal, Non-Color) -> Normal Map(strength) -> Normal             (exported as normalTexture + scale)
  Image(decal atlas, sRGB) -> Base Color, Alpha                          (exported as baseColorTexture, BLEND)
Textures live in assets/source/textures/v2/ (built by tools/build_textures.py and tools/build_decals.py) and are packed
into the GLB by the exporter.

Colour sources (sRGB, Sagewood only): official hero raw/sn-gn-hero.png (region medians, key-green excluded),
raw/sn-gal1.jpg (Sagewood handheld in use), LuxeColors video Sagewood frame, sharkninja.com swatch #757971.
See the table in COLOURS below; each value notes its samples.

Helpers for modelers:
  DECALS                       -> slots from decals.json
  decal_uv(slot, s, t)         -> Blender UV inside the slot's ink box (s, t in 0..1, t = glyph up)
  ensure_uvs(objects, tile)    -> box-projected UVs for meshes that have none (assembler calls before export)
"""
import json
import math
import os

import bpy
import lib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
TEX = os.path.join(ROOT, "assets", "source", "textures", "v2")

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
# finish: "plastic" (satin grain ORM + micro normal), "brushed" (streak ORM + groove normal), None (flat factors)
COLOURS = {
    # hero dock front (lit flat face) #8b8d83, cap top #696d65, gal1 handheld top #798078, site swatch #757971.
    # reference-director 3-source median #7d8073. Final = blend; Cycles studio (light 0.15) front flat ~ hero.
    "M_Sage": ("#7e8176", 0.46, 0.0, "plastic", "Sagewood satin body"),
    # hero dock plinth #53574f, head body rear #50544c, ref-director #53574e
    "M_SageDeep": ("#585c53", 0.50, 0.0, "plastic", "darker sage trims: dock plinth, head chassis"),
    # hero upper wand / handle neck dark parts #464b48..#5d615b (lit side), ref-director couplings #3e433f
    "M_Graphite": ("#414643", 0.42, 0.0, "plastic", "near-black green-grey: upper wand, knuckles, latches"),
    # hero copper wand #c19881 (soft lit), gal1 #a5684b (warm room), ref-director #b07c5e. Anodized, brushed along V.
    "M_Copper": ("#c39a82", 0.38, 0.6, "brushed", "anodized copper wand + neck disc: dyed oxide over aluminium -> part dielectric (metal 0.6)"),
    # hero cyclone shroud ribs #ac856f (dark grooves + bright ribs)
    "M_CopperSatin": ("#bc9178", 0.36, 0.7, "brushed", "copper-tone metallised plastic: cyclone shroud, hinge plates"),
    # brushroll: ref-director Luxe brushroll #8a5a44; hero behind window #72503e
    "M_CopperBrush": ("#8b5a43", 0.55, 0.2, None, "brushroll copper fins/sleeve"),
    "M_Chrome": ("#d3d5d8", 0.24, 1.0, None, "bright metal: screws, cyclone mesh shroud (hero reads satin light grey)"),
    # hero band behind POWERDETECTSPEED #8b8f8d (brushed, reads bright at grazing)
    "M_SilverBrush": ("#b4b8b7", 0.32, 1.0, "brushed", "brushed silver band / satin metal trims [added]"),
    # hero Shark plate #7c807f (brushed grey, slightly darker than the band)
    "M_PlateGrey": ("#8a8e8d", 0.36, 0.75, "brushed", "brushed grey Shark plate on the handheld [added]"),
    "M_Rubber": ("#1d1e1f", 0.85, 0.0, "plastic", "wheels, seals, grips"),
    "M_Bristle": ("#18181a", 0.78, 0.0, None, "black brush strip"),
    "M_Screen": ("#060708", 0.05, 0.0, None, "glossy black UI screen glass"),
    "M_Hose": ("#1b1c1d", 0.55, 0.0, None, "flex hose"),
    "M_Dust": ("#7c7064", 0.95, 0.0, None, "debris in the bin"),
}

# LED / emissive: (base sRGB, emission sRGB, strength, notes)
EMISSIVE = {
    # Reveal head light: core reads icy white-blue (#cde4ef in LuxeMOE), spill is saturated blue (#304378) -> blue LED
    "M_LED": ("#e9eef2", "#8cbcff", 1.0, "Reveal headlight lens (blue-white LED)"),
    # hero head light-pipe (unlit) #85b9e5, lit = saturated blue
    "M_LEDAccent": ("#85b9e5", "#3c8dff", 1.0, "Reveal blue light pipe / blue indicators"),
    # UI screen ring + light bar: white normally; deep/light purple when debris detected (guide p.7)
    "M_LEDRing": ("#d9dadb", "#f2f4ff", 1.0, "UI screen LED ring + light bar [added]"),
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


def _finish(nt, b, finish, normal_strength):
    orm = _img("plastic_orm.jpg" if finish == "plastic" else "brushed_orm.jpg")
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
            # ORM texture carries absolute roughness (plastic ~0.46, brushed ~0.30); per-material offsets are applied
            # at runtime (productMaterials.ts multiplies roughness) — keep authored factor for non-glTF previews.
            _finish(nt, b, finish, 0.35 if finish == "plastic" else 0.25)
            m["roughnessTarget"] = rough
        if name == "M_Screen":
            b.inputs["Coat Weight"].default_value = 1.0
            b.inputs["Coat Roughness"].default_value = 0.03

    # clear bin: water-clear PC/ABS-clear, faint blue-grey body tint (hero bin reads cool grey against the sage)
    m, nt, b = _new("M_ClearBin")
    b.inputs["Base Color"].default_value = _lin("#eef3f5")
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    _thin_clear(nt, b, "#eef3f5")
    # brushroll window: light neutral-grey smoke. Refs (hero, sn-gal2, laa-01) show the copper roll bright through it;
    # hero roll behind the window #72503e vs exposed brushroll #8a5a44 -> ~0.75 per face (two faces) -> #c6c7c8
    m, nt, b = _new("M_ClearSmoke")
    b.inputs["Base Color"].default_value = _lin("#c6c7c8")
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.49
    _thin_clear(nt, b, "#c6c7c8")

    for name, (base, emis, strength, _n) in EMISSIVE.items():
        m, nt, b = _new(name)
        b.inputs["Base Color"].default_value = _lin(base)
        b.inputs["Roughness"].default_value = 0.3
        b.inputs["Emission Color"].default_value = _lin(emis)
        b.inputs["Emission Strength"].default_value = strength

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


TEXTURED = tuple(n for n, v in COLOURS.items() if v[3])


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
    names = list(COLOURS) + ["M_ClearBin", "M_ClearSmoke"] + list(EMISSIVE) + ["M_Decal", "CAL_Grey18", "CAL_White90"]
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
        pl.scale = (0.4, 0.2, 1)
        pl.data.materials.append(lib.MATS["M_Copper"])
        objs.append(pl)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0.225, 0.0595, 0.16), rotation=(math.pi / 2, 0, 0))
        dc = bpy.context.object
        dc.scale = (0.4, 0.2, 1)
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
    cam.location = center + Vector((0, -1, 0.25)).normalized() * size * 3
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.resolution_x = res
    sc.render.resolution_y = int(res * ((mx - mn).z + 0.03) / ((mx - mn).x) * 1.1)
    sc.render.film_transparent = False
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    return names
