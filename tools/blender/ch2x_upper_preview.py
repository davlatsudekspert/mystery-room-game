"""QA renders of the UPPER FLOOR rooms of the Chapter 2 expansion (R5 Reading Gallery, R6 Plate Room, R7 Director's Office).

Same idea as ch2x_room_preview.py (kept separate so parallel artists do not collide): imports the exported room GLB plus its props at
the suggested placements, re-applies the textured preview materials and renders the views below with the room's own light recipe.

    blender -b --factory-startup -P tools/blender/ch2x_upper_preview.py -- room=gallery [--shots=gallery,balcony] [--res=800x540] [--samples=20]
Output: $MR_QA_DIR/ch2x/prev_<room>_<shot>.png (convert with tools/blender/ch2x_pack_previews.py <dir> prev_).
Placements here are the SUGGESTIONS for the scene agent (docs/models/ch2_exp.md lists them).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import C  # noqa: E402

ARGS = M.main_guard()
SEPIA, GREENLAMP, WARM, RED, COOL = "FFD59A", "D6F2A0", "FFC27A", "FF1E10", "BFD8FF"

ROOMS = {
    "gallery": {
        "models": [("room_gallery", (0, 0, 0), 0), ("balcony_rail", (0, 0, 1.6), 0), ("roll_call_board", (-1.0, 0, -3.0), 0),
                   ("pa_horn", (-4.5, 3.35, 0.15), 90), ("stair_wedge", (3.15, 0, 1.0), 0)],
        "lights": [("sun_n1", "AREA", (1.5, 2.2, -3.9), 700, SEPIA, 1.4, (1.5, 0.8, -1.0)),
                   ("sun_n2", "AREA", (3.1, 2.2, -3.9), 700, SEPIA, 1.4, (3.1, 0.6, -0.8)),
                   ("sun_w", "AREA", (-5.3, 2.2, -2.1), 420, SEPIA, 1.4, (-2.0, 0.8, -1.4)),
                   ("hall_day", "AREA", (0.0, 2.6, 4.2), 900, "FFE2B8", 5.0, (0.0, 1.0, 0.0)),
                   ("lamp_a", "POINT", (-2.5, 1.12, -1.02), 14, GREENLAMP, 0.05, None), ("lamp_b", "POINT", (-0.85, 1.12, -1.02), 14, GREENLAMP, 0.05, None),
                   ("lamp_c", "POINT", (-2.5, 1.12, 0.58), 14, GREENLAMP, 0.05, None), ("lamp_d", "POINT", (-0.85, 1.12, 0.58), 14, GREENLAMP, 0.05, None),
                   ("pend_a", "POINT", (-1.6, 2.65, 2.3), 60, WARM, 0.08, None), ("pend_b", "POINT", (1.6, 2.65, 2.3), 60, WARM, 0.08, None),
                   ("fill", "POINT", (0.0, 3.3, -0.5), 120, "FFE0B8", 0.3, None)],
        "shots": {"gallery": ((-4.15, 1.75, -2.3), (1.0, 1.3, 0.7), 66), "balcony": ((0.2, 1.75, 0.9), (0.4, -0.9, 3.0), 72),
                  "board": ((-1.0, 1.7, 0.4), (-1.0, 1.65, -3.0), 52), "counter": ((-0.8, 1.7, 0.2), (-4.5, 1.3, 0.0), 60),
                  "stair": ((0.8, 1.8, -1.8), (3.3, 0.2, 0.9), 66), "horn": ((0.6, 2.2, 0.6), (-4.5, 3.3, 0.15), 55),
                  "east": ((-3.0, 1.7, 0.5), (4.5, 1.3, -1.6), 64)},
    },
    "plate": {
        "models": [("room_plate", (0, 0, 0), 0), ("enlarger", (0.20, 0.90, -2.20), 0)] +
                  [("negative_strip", (-1.62, 0.9016, 0.10 + 0.09 * k), 0) for k in range(4)],
        "lights": [("safe_a", "POINT", (-1.2, 2.55, -0.4), 70, RED, 0.08, None), ("safe_b", "POINT", (1.3, 2.55, 0.9), 70, RED, 0.08, None),
                   ("safe_c", "POINT", (2.7, 2.1, -0.3), 30, RED, 0.08, None), ("enl", "POINT", (0.25, 1.35, -2.0), 6, "FFE0B0", 0.05, None),
                   ("fill", "POINT", (0.0, 2.8, 0.2), 14, "8A93A8", 0.3, None)],
        "shots": {"plate": ((-2.4, 1.7, 2.0), (0.8, 1.2, -0.5), 66), "enlarger": ((1.3, 1.5, -0.5), (0.2, 1.1, -2.2), 56),
                  "trays": ((0.6, 1.5, -1.3), (3.0, 0.9, -0.4), 62), "racks": ((0.5, 1.6, 0.3), (-3.0, 1.3, -1.2), 64),
                  "door": ((1.2, 1.6, -1.2), (-2.2, 1.2, 2.4), 62), "table": ((0.6, 1.7, 1.6), (-1.2, 0.9, 0.2), 56)},
    },
    "office": {
        "models": [("room_office", (0, 0, 0), 0), ("strand_cabinet", (2.67, 0, 0.30), -90), ("tea_set", (-0.55, 0.606, 0.95), 0),
                   ("projector_lamp", (2.67, 1.014, 0.30), 0), ("pass_key", (0.75, 0.768, -1.0), 15)],
        "lights": [("win", "AREA", (0.4, 2.0, -3.3), 900, "DDEBFF", 1.6, (0.4, 0.8, -0.6)), ("desk", "POINT", (-0.05, 1.0, -1.5), 22, GREENLAMP, 0.05, None),
                   ("fill", "POINT", (0.0, 2.8, 0.3), 70, "E8F0FF", 0.3, None), ("fill2", "POINT", (-1.5, 2.2, 1.6), 30, "FFE8C8", 0.3, None)],
        "shots": {"office": ((-2.5, 1.7, 2.0), (0.6, 1.2, -0.6), 64), "cabinet": ((0.5, 1.5, 0.3), (2.8, 1.2, 0.3), 54),
                  "desk": ((0.4, 1.6, 0.9), (0.4, 0.9, -1.6), 56), "tea": ((-1.9, 1.5, -0.3), (-0.55, 0.55, 0.95), 50),
                  "fireplace": ((0.3, 1.6, -0.6), (-0.5, 1.2, 2.4), 60), "door": ((1.3, 1.7, 1.0), (-2.9, 1.2, -1.1), 64)},
    },
}


def retex():
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
    room = next((a.split("=", 1)[1] for a in ARGS if a.startswith("room=")), "gallery")
    res = (800, 540)
    samples = 20
    for a in ARGS:
        if a.startswith("--res="):
            w, h = a[6:].split("x")
            res = (int(w), int(h))
        if a.startswith("--samples="):
            samples = int(a[10:])
    sel = C.args_shots(ARGS)
    spec = ROOMS[room]
    X.begin()
    for glb, pos, yaw in spec["models"]:
        C.qa_import(C.model_glb(glb), pos, yaw)
    retex()
    C.qa_begin(samples=samples)
    for n, col, st in (("M_Emissive_Warm", "FFB46B", 6.0), ("M_Emissive_Red", "FF3B2F", 6.0), ("M_Emissive_Table", "FFE6BE", 7.0),
                       ("M_Emissive_Safelight", "FF1A0E", 5.0), ("M_Emissive_Lumen", "CFF6FF", 5.0)):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Emission Color"].default_value = M.hex_rgba(col)
            b.inputs["Emission Strength"].default_value = st
    for tag, (cam, tgt, vfov) in spec["shots"].items():
        if not C.want(tag, sel):
            continue
        for nm, kind, pos, en, col, rad, target in spec["lights"]:
            lo = C.qa_light(nm, kind, pos, en, col, radius=rad, target=target)
            lo.visible_camera = False
        C.shoot(f"prev_{room}_{tag}", cam, tgt, vfov=vfov, res=res, samples=samples, world=0.05)
        C.qa_clear()


main()
