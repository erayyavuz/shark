"""
Reference-view renders of assets/source/powerdetect.blend + labeled side-by-side comparisons.

  Blender -b --factory-startup -P scripts/blender/render_reference_views.py -- [--samples 48] [--views front,side,...]
      renders assets/reference-comparison/render_<view>.png, then runs
  python3 scripts/blender/render_reference_views.py --compose
      builds assets/reference-comparison/compare_<view>.png (reference | render, labeled) with PIL.

Rendering uses Cycles (GPU Metal when available) with a pale studio sweep, broad key, fill and rim light.
Cameras approximate the reference viewpoints (long lenses for the near-orthographic V2/V7 views);
perspective mismatch is not treated as a geometry error.
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "reference-comparison")
REF = os.path.join(ROOT, "assets", "references")

# view -> (reference file, crop box in reference pixels or None, label)
PAIRS = {
    "front": ("V7.png", (760, 80, 1300, 2000), "V7 official front (IP1251EUT)"),
    "folded_side": ("V2.jpg", (600, 150, 2050, 2900), "V2 folded side (IP1251UKT)"),
    "threequarter_R": ("V1.jpg", (0, 330, 1350, 1700), "V1 front 3/4 (MultiFlex bent)"),
    "threequarter_L": ("V8.png", None, "V8 front (UKT) - 3/4 L has no exact ref"),
    "side": ("V2.jpg", (600, 2300, 2050, 2900), "V2 floorhead side (crop)"),
    "rear": ("V2.jpg", (600, 1500, 2050, 2400), "V2 handle loop (no direct rear ref)"),
    "head_close": ("V5.png", (965, 0, 2000, 780), "V5 head close-up (advertising rings ignored)"),
    "head_top": ("V5.png", (0, 770, 965, 1380), "V5 head top view"),
    "bin_close": ("V4.png", (640, 380, 1290, 1200), "V4 handheld close-up"),
    "cleaning": ("V6.png", (380, 280, 2000, 1380), "V6 in use (MultiFlex ~90 deg)"),
}


def blender_main():
    import bpy
    from mathutils import Vector, Euler

    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 48
    views = argv[argv.index("--views") + 1].split(",") if "--views" in argv else list(PAIRS.keys())
    blend = os.path.join(ROOT, "assets", "source", "powerdetect.blend")
    bpy.ops.wm.open_mainfile(filepath=blend)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.samples = samples
    cy.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        cy.device = "GPU"
    except Exception as e:  # CPU fallback
        print("[render] GPU unavailable:", e)
    cy.max_bounces = 8
    cy.transmission_bounces = 8
    sc.view_settings.view_transform = "Khronos PBR Neutral"
    sc.view_settings.exposure = 0.0
    sc.render.film_transparent = False

    # world: pale studio
    world = bpy.data.worlds.new("Studio")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.80, 0.79, 0.77, 1)
    bg.inputs["Strength"].default_value = 0.30

    # floor sweep
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "StudioFloor"
    fm = bpy.data.materials.new("Floor")
    fm.use_nodes = True
    b = fm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.72, 0.71, 0.69, 1)
    b.inputs["Roughness"].default_value = 0.55
    floor.data.materials.append(fm)

    def area(name, loc, rot, size, energy, color=(1, 1, 1)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size = size
        ld.energy = energy
        ld.color = color
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = loc
        d = Vector((0, 0, 0.55)) - Vector(loc)
        ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        return ob

    area("Key", (-1.6, -1.8, 2.2), None, 2.2, 190)
    area("Fill", (2.0, -1.2, 1.0), None, 2.5, 55)
    area("Rim", (0.6, 2.2, 1.9), None, 1.6, 120)
    area("Top", (0, 0, 3.2), None, 2.0, 45)

    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam

    for o in bpy.data.objects:
        if o.name.startswith("DustbinContents"):
            o.hide_render = True  # fill is driven at runtime; keep the bin empty for identity comparisons
    neck = bpy.data.objects["NeckPivot"]
    flex = bpy.data.objects["FlexPivot"]

    def look(loc, target, lens, res=(900, 1400), ortho=None):
        cam.location = loc
        d = Vector(target) - Vector(loc)
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        if ortho:
            cam_d.type = "ORTHO"
            cam_d.ortho_scale = ortho
        else:
            cam_d.type = "PERSP"
            cam_d.lens = lens
        cam_d.clip_start = 0.01
        cam_d.clip_end = 50
        sc.render.resolution_x, sc.render.resolution_y = res
        sc.render.resolution_percentage = 100

    def pose(pitch=0.0, fold=0.0):
        # Blender rot about +X moves +Z toward -Y (front). Lean back => negative.
        neck.rotation_euler = Euler((-math.radians(pitch), 0, 0))
        flex.rotation_euler = Euler((math.radians(fold), 0, 0))
        bpy.context.view_layer.update()

    def sph(az, el, dist, tz):
        # az measured from front (-Y) toward +X
        a, e = math.radians(az), math.radians(el)
        return (dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), tz + dist * math.sin(e))

    V = {
        "front": lambda: (pose(), look(sph(0, 2, 9.0, 0.58), (0, -0.05, 0.58), 0, ortho=1.30, res=(760, 1300))),
        "folded_side": lambda: (pose(0, 178), look((6.0, -0.05, 0.42), (0, -0.05, 0.42), 0, ortho=0.80, res=(1000, 1400))),
        "threequarter_R": lambda: (pose(), look(sph(38, 12, 2.2, 0.55), (0, -0.07, 0.57), 50, res=(900, 1300))),
        "threequarter_L": lambda: (pose(), look(sph(-38, 12, 2.2, 0.55), (0, -0.07, 0.57), 50, res=(900, 1300))),
        "side": lambda: (pose(), look((6.0, 0.125, 0.58), (0, 0.125, 0.58), 0, ortho=1.24, res=(760, 1300))),
        "rear": lambda: (pose(), look(sph(180, 6, 6.0, 0.58), (0, 0.10, 0.58), 0, ortho=1.30, res=(760, 1300))),
        "head_close": lambda: (pose(), look(sph(-28, 14, 0.75, 0.03), (0.0, -0.01, 0.05), 50, res=(1200, 900))),
        "head_top": lambda: (pose(), look((0.0, -0.03, 1.4), (0.0, -0.03, 0.0), 0, ortho=0.36, res=(1200, 900))),
        "bin_close": lambda: (pose(), look(sph(25, 8, 1.1, 0.95), (0, 0.10, 0.96), 60, res=(900, 1200))),
        "cleaning": lambda: (pose(45, 0), look(sph(-50, 28, 3.0, 0.30), (0, 0.15, 0.34), 50, res=(1400, 1000))),
    }
    os.makedirs(OUT, exist_ok=True)
    for name in views:
        V[name]()
        sc.render.filepath = os.path.join(OUT, f"render_{name}.png")
        bpy.ops.render.render(write_still=True)
        print("[render]", name)
    pose()


def compose():
    from PIL import Image, ImageDraw, ImageFont

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
    except Exception:
        font = ImageFont.load_default()
    H = 1100
    for view, (ref, crop, label) in PAIRS.items():
        rp = os.path.join(OUT, f"render_{view}.png")
        if not os.path.exists(rp):
            continue
        r = Image.open(os.path.join(REF, ref)).convert("RGBA")
        bgc = Image.new("RGBA", r.size, (255, 255, 255, 255))
        r = Image.alpha_composite(bgc, r).convert("RGB")
        if crop:
            r = r.crop(crop)
        m = Image.open(rp).convert("RGB")
        r = r.resize((int(r.width * H / r.height), H))
        m = m.resize((int(m.width * H / m.height), H))
        W = r.width + m.width + 30
        out = Image.new("RGB", (W, H + 70), (245, 245, 243))
        out.paste(r, (10, 64))
        out.paste(m, (r.width + 20, 64))
        d = ImageDraw.Draw(out)
        d.text((14, 12), "REFERENCE: " + label, fill=(30, 30, 30), font=font)
        d.text((r.width + 24, 32 if r.width < 600 else 12), "RENDER: " + view + " (procedural model)", fill=(90, 40, 130), font=font)
        out.save(os.path.join(OUT, f"compare_{view}.png"))
        print("[compose]", view)


if __name__ == "__main__":
    if "--compose" in sys.argv:
        compose()
    else:
        blender_main()
