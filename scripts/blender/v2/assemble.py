"""
v2 assembler — Shark PowerDetect Speed Clean & Empty (IA3246GN, Sagewood). Lead-owned.

  Blender -b --factory-startup -P scripts/blender/v2/assemble.py -- [--tier all|high|balanced] [--no-export]
         [--parts floorhead,wand,handheld,dock]

Builds every part (scripts/blender/v2/parts/*.py) in the upright docked rest pose, creates the rig hierarchy
required by src/contracts/rig.ts plus a separate DockRoot, and writes:
  assets/source/powerdetect-v2.blend
  public/models/powerdetect-{high,balanced}.glb   (uncompressed; scripts/assets-build.mjs adds meshopt)
  public/models/rig.json
  assets/source/build_report_v2.json
"""
import bpy
import importlib
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import lib  # noqa: E402
import params as P  # noqa: E402
import materials  # noqa: E402

PART_NAMES = ["floorhead", "wand", "handheld", "dock"]
GROUPS = ["FloorHead", "LowerWand", "UpperWand", "MotorAssembly", "Dock"]


def load_part(name):
    mod = importlib.import_module(f"parts.{name}")
    importlib.reload(mod)
    return mod


def build_all(tier, parts):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for m in (lib, P, materials):
        importlib.reload(m)
    lib.set_tier(tier)
    materials.make_materials(tier)
    ctx = {"tier": tier, "P": P, "lib": lib}
    outs = {}
    for name in parts:
        t0 = time.time()
        out = load_part(name).build(ctx) or {}
        outs[name] = out
        print(f"[assemble] part {name}: {sum(len(v) for v in out.get('groups', {}).values())} meshes in {time.time() - t0:.1f}s")
    return outs


def rig(outs):
    E = lib.empty
    pre = {}
    for out in outs.values():
        pre.update(out.get("anchors", {}))
    neck_p = pre.get("NeckPivot", P.NECK_PIVOT)
    fold_p = pre.get("FlexPivot", P.FOLD_PIVOT)
    motor_p = pre.get("MotorAssembly", P.HANDHELD_ORIGIN)
    root = E("VacuumRoot", (0, 0, 0))
    head = E("FloorHead", (0, 0, 0), root)
    neck = E("NeckPivot", neck_p, head)
    lw = E("LowerWand", neck_p, neck)
    flex = E("FlexPivot", fold_p, lw)
    uw = E("UpperWand", fold_p, flex)
    motor = E("MotorAssembly", motor_p, uw)
    dock = E("DockRoot", (0, 0, 0))
    groups = {"FloorHead": head, "LowerWand": lw, "UpperWand": uw, "MotorAssembly": motor, "Dock": dock}
    anchors, contacts, special, nozzle = {}, {}, {}, {}
    for out in outs.values():
        anchors.update(out.get("anchors", {}))
        contacts.update(out.get("contacts", {}))
        special.update(out.get("special", {}))
        nozzle.update(out.get("nozzle", {}))
        for g, objs in out.get("groups", {}).items():
            for o in objs:
                o["grp"] = g
                lib.set_parent(o, groups[g])
    owner = {"PowerControlAnchor": motor, "IntakeFront": head, "IntakeRear": head}
    for nm in ("PowerControlAnchor", "IntakeFront", "IntakeRear"):
        E(nm, anchors.get(nm, (0, 0, 0)), owner[nm])
    fca = E("FloorContactAnchors", (0, 0, 0), head)
    for nm, loc in contacts.items():
        E(nm, loc, fca)
    wrapped = []
    for nm, par in (("RollerFront", head), ("RollerRear", head)):
        ob = special.get(nm)
        if ob is None:
            ob = lib.empty(nm, (0, 0.02, 0), par)  # placeholder so the rig stays valid while parts are missing
        else:
            ob.name = nm
            lib.set_parent(ob, par)
            wrapped.append(ob)
    for nm, par, origin in (("DustbinShell", motor, None), ("DustbinContents", motor, None)):
        ob = special.get(nm)
        if ob is None:
            lib.empty(nm, motor_p, par)
        else:
            ob.name = nm
            lib.set_parent(ob, par)
            wrapped.append(ob)
    for nm, par in (("HeadLights", head), ("Display", motor), ("DockLights", dock)):
        objs = special.get(nm) or []
        if objs:
            j = lib.join_objects(objs, nm)
            lib.set_parent(j, par)
            wrapped.append(j)
        elif nm == "HeadLights":
            lib.empty(nm, (0, 0.03, 0.08), par)
    for ob in wrapped:
        lib.wrap_mesh_in_empty(ob)
    return {"groups": groups, "nozzle": nozzle, "special": special}


def finalize(ctx):
    for gname, emp in ctx["groups"].items():
        parts = [o for o in emp.children if o.type == "MESH" and o.get("grp") == gname]
        for o in parts:
            lib.apply_modifiers(o)
        if parts:
            j = lib.join_objects(parts, f"{gname}_Body")
            lib.set_origin(j, emp.matrix_world.translation)
    import bmesh

    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            lib.apply_modifiers(o)
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bm.to_mesh(o.data)
            bm.free()


def measure(ctx):
    from mathutils import Vector

    gl = lib.gl
    head = bpy.data.objects["FloorHead"]
    head_meshes = [o for c in head.children if c.name != "NeckPivot" for o in ([c] + list(c.children_recursive)) if o.type == "MESH"]
    hmn, hmx = lib.world_bbox(head_meshes) if head_meshes else (Vector((0, 0, 0)), Vector((0, 0, 0)))
    vac = [o for o in bpy.data.objects["VacuumRoot"].children_recursive if o.type == "MESH"]
    amn, amx = lib.world_bbox(vac)
    dock = [o for o in bpy.data.objects["DockRoot"].children_recursive if o.type == "MESH"]
    nozzle = dict(ctx["nozzle"])
    nozzle.update({"shellWidth": round(hmx.x - hmn.x, 4), "shellZMin": round(-hmx.y, 4), "shellZMax": round(-hmn.y, 4)})
    anchors = {nm: gl(bpy.data.objects[nm].matrix_world.translation) for nm in ("NeckPivot", "FlexPivot", "PowerControlAnchor", "IntakeFront", "IntakeRear", "MotorAssembly", "LowerWand", "UpperWand")}
    out = {
        "product": "Shark PowerDetect Speed Clean & Empty IA3246GN (Sagewood)",
        "units": "meters",
        "upAxis": "+Y",
        "headFront": "+Z (FloorHead local)",
        "nozzle": nozzle,
        "rollerFrontRadius": getattr(P, "BRUSHROLL_R", 0.024),
        "rollerRearRadius": getattr(P, "BRUSHROLL_R", 0.024),
        "neckPivot": anchors["NeckPivot"],
        "flexPivot": anchors["FlexPivot"],
        "powerControlAnchor": anchors["PowerControlAnchor"],
        "anchors": anchors,
        "contacts": {o.name: gl(o.matrix_world.translation) for o in bpy.data.objects["FloorContactAnchors"].children},
        "bounds": {"size": [round(amx.x - amn.x, 4), round(amx.z - amn.z, 4), round(amx.y - amn.y, 4)]},
        "dock": {"present": bool(dock), "node": "DockRoot"},
        "foldAxisSign": 1,
        "pitchConvention": "runtime sets NeckPivot.rotation.x = -pitch; rest rotations identity",
    }
    if dock:
        dmn, dmx = lib.world_bbox(dock)
        out["dock"]["bounds"] = {"min": gl(Vector((dmn.x, dmx.y, dmn.z))), "max": gl(Vector((dmx.x, dmn.y, dmx.z)))}
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    tier = argv[argv.index("--tier") + 1] if "--tier" in argv else "all"
    parts = argv[argv.index("--parts") + 1].split(",") if "--parts" in argv else PART_NAMES
    do_export = "--no-export" not in argv
    tiers = ["high", "balanced"] if tier == "all" else [tier]
    report = {"tiers": {}}
    rigjson = None
    for t in tiers:
        outs = build_all(t, parts)
        ctx = rig(outs)
        bpy.context.view_layer.update()
        if hasattr(materials, "ensure_uvs"):
            materials.ensure_uvs([o for o in bpy.context.scene.objects if o.type == "MESH"])
        if t == "high" or len(tiers) == 1:
            src = os.path.join(ROOT, "assets", "source", "powerdetect-v2.blend")
            os.makedirs(os.path.dirname(src), exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=src, compress=True)
        if not do_export:
            continue
        finalize(ctx)
        bpy.context.view_layer.update()
        total, per = lib.tri_count()
        if rigjson is None:
            rigjson = measure(ctx)
        out = os.path.join(ROOT, "public", "models", f"powerdetect-{t}.glb")
        lib.export_glb(out)
        report["tiers"][t] = {"triangles": total, "perObject": per, "bytes": os.path.getsize(out), "materials": sorted(m.name for m in bpy.data.materials if m.users)}
        print(f"[assemble] {t}: {total} tris -> {out}")
    if do_export and rigjson:
        rigjson["generatedBy"] = "scripts/blender/v2/assemble.py"
        with open(os.path.join(ROOT, "public", "models", "rig.json"), "w") as f:
            json.dump(rigjson, f, indent=2)
        report["rig"] = rigjson
        with open(os.path.join(ROOT, "assets", "source", "build_report_v2.json"), "w") as f:
            json.dump(report, f, indent=2)
    print("[assemble] done")


if __name__ == "__main__":
    main()
