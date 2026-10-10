"""QA only: renders every Chapter 4 item (group H) as an inventory icon candidate: qa/blender/ch4/icon_<name>.png at 330 x 330 (the sheet script downsizes to 110 px).

Imports each exported GLB (game/assets/models/<name>.glb, so the real files are checked, not the build functions), frames it the way the inspect / inventory view does (flat items tilted
70 deg about Godot +X and seen from +Z, standing items seen from the front), soft three-point light, no floor.
    blender -b --factory-startup -P tools/blender/models/items_lineup_ch4.py [-- --only=name1,name2]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402
import lib_ch3_a as K  # noqa: E402
import lib_ch4_items as H  # noqa: E402
from mathutils import Vector  # noqa: E402

ITEMS = [("tower_key_1", "flat"), ("tower_key_2", "flat"), ("tower_key_3", "flat"), ("tower_key_4", "flat"), ("strand_log", "flat"), ("pocket_watch", "stand"),
         ("strand_last_letter", "flat"), ("reverse_pawl", "flat"), ("leyla_note_1998", "flat"), ("leyla_parcel", "flat")]
RES = 330


def main():
    args = M.main_guard()
    only = None
    for a in args:
        if a.startswith("--only="):
            only = a.split("=", 1)[1].split(",")
    for name, kind in ITEMS:
        if only and name not in only:
            continue
        M.reset_scene()
        C.ensure_materials()
        holder = K.qa_import(name, (0, 0, 0), 0.0, prefix="it_")
        if holder is None:
            print(f"[items4] {name}: GLB missing")
            continue
        M.refresh()
        pts = []
        for o in bpy.data.objects:
            if o.type == "MESH" and o.name.startswith("it_"):
                pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        centre = (lo + hi) / 2.0
        r = (hi - lo).length / 2.0
        d = 3.0 * r
        if kind == "flat":
            t = math.radians(70.0)
            cam = centre + Vector((0.0, -d * math.cos(t), d * math.sin(t)))
        else:
            cam = centre + Vector((0.0, -d * 0.97, d * 0.22))
        D.qa_tweak()
        C.shot(f"icon_{name}", tuple(cam), tuple(centre), lens=50, floor_z=None, samples=24, res=(RES, RES), lights=C.SOFT)
        print(f"[items4] {name}: icon rendered, bounds {tuple(round(c, 4) for c in lo)} .. {tuple(round(c, 4) for c in hi)}")


main()
