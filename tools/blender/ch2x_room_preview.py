"""QA renders of the Chapter 2 expansion rooms: imports the exported room GLB plus its props at the suggested placements,
re-applies the preview materials (textured) and renders the views listed below with the room's own light recipe.

    blender -b --factory-startup -P tools/blender/ch2x_room_preview.py -- room=pump [--shots=pump,manifold] [--res=800x540]
Output: $MR_QA_DIR/ch2x/prev_<room>_<shot>.png (convert to docs/previews/ch2_expansion/*.jpg with tools/blender/ch2x_pack_previews.py).
Placements here are SUGGESTIONS for the scene agent (docs/models/ch2_exp.md lists them).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import C, G  # noqa: E402

ARGS = M.main_guard()
ORANGE, AMBER, COLD, RED, DAYLIGHT, GREEN = "FFA050", "FFC27A", "BFE0FF", "FF2A1A", "FFE2B8", "BFE8C0"

# model placements: (glb, (x, y, z), yaw)
ROOMS = {
    "pump": {
        "models": [("room_pump", (0, 0, 0), 0), ("boiler", (0, 0, -1.75), 0), ("manifold_plate", (3.5, 0, 1.35), -90),
                   ("pipe_run", (-3.5, 0, 1.05), 90), ("book_lift_cage", (-4.40, 0, -1.50), 90), ("mallet", (1.60, 0.885, 2.58), 20)],
        "lights": [("work", "POINT", (0.5, 2.28, 0.2), 260, ORANGE, 0.06), ("boiler", "POINT", (0.0, 0.75, -0.50), 90, "FF7030", 0.1),
                   ("fill", "POINT", (-1.5, 2.6, 1.0), 40, COLD, 0.2), ("fill2", "POINT", (1.5, 2.8, -1.5), 30, "FFB878", 0.2)],
        "shots": {"pump": ((-1.7, 1.75, 2.7), (0.4, 1.1, -1.5), 64), "manifold": ((0.6, 1.5, 0.7), (3.5, 1.25, 1.35), 58),
                  "boiler": ((0.4, 1.45, 1.2), (0.0, 1.0, -1.75), 58), "lift_door": ((2.6, 1.7, 1.6), (-4.0, 1.1, -1.5), 62),
                  "pipes": ((-0.4, 1.5, 1.4), (-3.5, 1.1, 1.05), 60)},
    },
}


def retex():
    """Swap the plain imported materials for the textured preview materials of mrlib (same slot names)."""
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            base = m.name.split(".")[0]
            if base.startswith("M_"):
                o.data.materials[i] = M.material(base)


def main():
    room = next((a.split("=", 1)[1] for a in ARGS if a.startswith("room=")), "pump")
    res = (800, 540)
    for a in ARGS:
        if a.startswith("--res="):
            w, h = a[6:].split("x")
            res = (int(w), int(h))
    sel = C.args_shots(ARGS)
    spec = ROOMS[room]
    X.begin()
    for glb, pos, yaw in spec["models"]:
        C.qa_import(C.model_glb(glb), pos, yaw)
    retex()
    C.qa_begin(samples=24)
    # glow materials as emissive in the preview
    for n, col, st in (("M_Emissive_Warm", "FFB46B", 6.0), ("M_Emissive_Red", "FF3B2F", 6.0), ("M_Emissive_Table", "FFF1D0", 5.0),
                       ("M_Emissive_Safelight", "FF1A0E", 5.0), ("M_Emissive_Lumen", "CFF6FF", 5.0)):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Emission Color"].default_value = M.hex_rgba(col)
            b.inputs["Emission Strength"].default_value = st
    for tag, (cam, tgt, vfov) in spec["shots"].items():
        if not C.want(tag, sel):
            continue
        for nm, kind, pos, en, col, rad in spec["lights"]:
            C.qa_light(nm, kind, pos, en, col, radius=rad)
        C.shoot(f"prev_{room}_{tag}", cam, tgt, vfov=vfov, res=res, samples=24, world=0.05)
        C.qa_clear()


main()
