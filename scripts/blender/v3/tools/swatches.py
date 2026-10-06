"""Blender -b --factory-startup -P scripts/blender/v3/tools/swatches.py -- [--samples 48] [--out path.png]
Material swatch render (sphere + cylinder per material + decal atlas card) under the preview.py studio."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = os.path.dirname(HERE)
sys.path.insert(0, V2)
import bpy  # noqa: E402
import lib  # noqa: E402
import materials  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d  # noqa: E731
bpy.ops.wm.read_factory_settings(use_empty=True)
materials.make_materials("high")
out = arg("--out", os.path.join(V2, "..", "..", "..", "assets", "reference-comparison", "v3", "materials", "swatches.png"))
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
names = materials.swatch_scene(os.path.abspath(out), samples=int(arg("--samples", "48")), light_scale=float(arg("--light", "1.0")), world=float(arg("--world")) if arg("--world") else None)
print("[swatches]", out, names)
