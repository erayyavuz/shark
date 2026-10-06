"""Blender -b --factory-startup -P scripts/blender/v2/tools/lookdev_render.py -- <preview.py args> [--world 0.3]
preview.py with an optional absolute world strength override (to test env brightness for metals / clear parts)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import preview  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
W = float(argv[argv.index("--world") + 1]) if "--world" in argv else None
_orig = preview.setup_scene


def _setup(*a, **k):
    sc = _orig(*a, **k)
    if W is not None:
        sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = W
    return sc


preview.setup_scene = _setup
preview.main()
