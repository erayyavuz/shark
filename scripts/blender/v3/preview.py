"""
Standard-view renders of one v3 part (or the full product) for reference comparison. Lead-owned.

  Blender -b --factory-startup -P scripts/blender/v3/preview.py -- --part floorhead|wand|handheld|dock|all
          [--tier high] [--samples 32] [--views front,back,left,right,top,bottom,q_l,q_r,q_l_low,q_r_high]
          [--res 1200] [--engine cycles|eevee] [--out <dir>] [--light 0.15]

Output: assets/reference-comparison/v3/<part>/<view>.png
Orthographic views (front/back/left/right/top/bottom) use the same scale per part so they can be overlaid with
patent drawings / near-orthographic product photos. 3/4 views use a 70 mm lens.
'front' looks at the product front (camera on +fwd); 'left' = camera on the product's left (-x).
"""
import bpy
import math
import os
import sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import assemble  # noqa: E402
import lib  # noqa: E402

VIEWS = {
    # name: (direction from target to camera in product coords (x, up, fwd), ortho?)
    "front": ((0, 0, 1), True),
    "back": ((0, 0, -1), True),
    "left": ((-1, 0, 0), True),
    "right": ((1, 0, 0), True),
    "top": ((0, 1, 0.0001), True),
    "bottom": ((0, -1, 0.0001), True),
    "q_l": ((-0.75, 0.35, 0.85), False),
    "q_r": ((0.75, 0.35, 0.85), False),
    "q_l_low": ((-0.8, 0.12, 0.7), False),
    "q_r_high": ((0.6, 0.9, 0.7), False),
    "q_back_l": ((-0.7, 0.4, -0.8), False),
}


def setup_scene(samples, engine, light=0.15):
    sc = bpy.context.scene
    if engine == "eevee":
        sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items} else "BLENDER_EEVEE"
    else:
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
        except Exception as e:
            print("[preview] GPU unavailable:", e)
        cy.max_bounces = 8
        cy.transmission_bounces = 8
    sc.view_settings.view_transform = "Khronos PBR Neutral"
    world = bpy.data.worlds.new("Studio")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.82, 0.81, 0.79, 1)
    bg.inputs["Strength"].default_value = 2.0 * light  # metals mostly reflect the world; calibrated vs hero copper (materials agent)
    return sc


def add_lights(sc, center, size, light=0.15):
    def area(name, d, energy, sz):
        ld = bpy.data.lights.new(name, "AREA")
        ld.size = sz * size
        ld.energy = energy * size * size * light
        ob = bpy.data.objects.new(name, ld)
        sc.collection.objects.link(ob)
        ob.location = center + Vector(d).normalized() * size * 2.6
        ob.rotation_euler = (center - ob.location).to_track_quat("-Z", "Y").to_euler()

    # Blender-space directions (x, y=-fwd, z=up)
    area("Key", (-1.0, -1.3, 1.4), 520, 1.6)
    area("Fill", (1.3, -0.9, 0.5), 160, 1.8)
    area("Rim", (0.5, 1.4, 1.1), 330, 1.2)
    area("Top", (0, 0, 1), 140, 1.4)
    area("Under", (0, -0.6, -1), 40, 1.6)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
    part = arg("--part", "all")
    tier = arg("--tier", "high")
    samples = int(arg("--samples", "32"))
    res = int(arg("--res", "1200"))
    engine = arg("--engine", "cycles")
    # calibrated by the materials agent: at 0.15 an 18% grey card renders ~sRGB 120-130 and Sagewood albedos match the hero
    light = float(arg("--light", "0.15"))
    views = arg("--views", ",".join(VIEWS)).split(",")
    out_dir = arg("--out", os.path.join(ROOT, "assets", "reference-comparison", "v3", part))
    os.makedirs(out_dir, exist_ok=True)
    parts = assemble.PART_NAMES if part == "all" else [part]
    outs = assemble.build_all(tier, parts)
    if part == "all":
        assemble.rig(outs)
    bpy.context.view_layer.update()
    mats = assemble.materials
    if hasattr(mats, "ensure_uvs"):
        mats.ensure_uvs([o for o in bpy.context.scene.objects if o.type == "MESH"])
    for o in bpy.data.objects:
        if o.name.startswith("DustbinContents"):
            o.hide_render = True
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
    if not meshes:
        print("[preview] nothing to render")
        return
    mn, mx = lib.world_bbox(meshes)
    center = (mn + mx) / 2
    size = max((mx - mn).length, 0.05)
    sc = setup_scene(samples, engine, light)
    add_lights(sc, center, size, light)
    cam_d = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam_d.clip_start = 0.001
    cam_d.clip_end = 100
    ext = mx - mn
    for v in views:
        if v not in VIEWS:
            continue
        d, ortho = VIEWS[v]
        db = Vector((d[0], -d[2], d[1])).normalized()  # product -> Blender
        cam.location = center + db * size * 3
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        if ortho:
            cam_d.type = "ORTHO"
            if v in ("front", "back"):
                w, h = ext.x, ext.z
            elif v in ("left", "right"):
                w, h = ext.y, ext.z
            else:
                w, h = ext.x, ext.y
            cam_d.ortho_scale = max(w, h) * 1.08
            ar = max(0.25, min(4.0, (w + 1e-4) / (h + 1e-4)))
        else:
            cam_d.type = "PERSP"
            cam_d.lens = 70
            cam.location = center + db * size * 2.25
            ar = 1.0
        sc.render.resolution_x = int(res * min(1.0, ar)) if ar < 1 else res
        sc.render.resolution_y = res if ar < 1 else int(res / ar)
        sc.render.filepath = os.path.join(out_dir, f"{v}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[preview] {v} -> {sc.render.filepath}")


if __name__ == "__main__":
    main()
