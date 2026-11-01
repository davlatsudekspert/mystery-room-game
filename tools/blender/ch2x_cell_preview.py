"""QA renders of the Night Cell (R3): imports `room_cell` plus its props at the suggested placements, re-applies the textured preview materials
and renders the review views with the room's own light recipe (amber pendant, desk lamp, the light table glow).

    blender -b --factory-startup -P tools/blender/ch2x_cell_preview.py -- [--shots=cell,cell2,desk_light,cot,shelf,door,west] [--res=800x540] [--powered]
Output: $MR_QA_DIR/ch2x/prev_cell_<shot>.png (convert with tools/blender/ch2x_pack_previews.py). The placements are the suggestions of docs/models/ch2_exp.md.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import C, G  # noqa: E402

ARGS = M.main_guard()
AMBER, WARM, TABLE, COLD = "FFB46B", "FFC27A", "FFF1D0", "BFE0FF"
MODELS = [("room_cell", (0, 0, 0), 0), ("cot", (-0.75, 0, -1.58), 0), ("light_table", (1.30, 0.76, -1.62), 0), ("kettle_hotplate", (-0.70, 0.86, 1.76), 180),
          ("cell_diary", (0.82, 0.775, -1.62), 12), ("cold_door", (2.20, 0, 0), -90)]
# loose sheets lie flat (rotated -90 about X); the first two are stacked on the table for the QA view
SHEETS = [("acetate_sheet_a", (1.30, 0.0615 + 0.76, -1.60), 0), ("acetate_sheet_b", (1.30, 0.0645 + 0.76, -1.60), 90), ("acetate_sheet_c", (1.30, 0.0675 + 0.76, -1.60), 180)]
LIGHTS = [("pendant", "POINT", (0.0, 2.02, 0.20), 120, AMBER, 0.08), ("desk", "POINT", (2.0, 1.10, -1.72), 22, WARM, 0.06),
          ("table", "POINT", (1.30, 0.95, -1.60), 10, TABLE, 0.10), ("fill", "POINT", (-1.2, 1.9, 1.2), 14, "FFD8A8", 0.2),
          ("coldfill", "POINT", (2.0, 1.9, 0.0), 6, COLD, 0.2), ("cotfill", "POINT", (-0.8, 1.2, -1.2), 8, "FFD8A8", 0.2)]
SHOTS = {
    "cell": ((-2.05, 1.70, 1.80), (1.3, 0.70, -1.1), 70),
    "cell2": ((2.10, 1.75, 1.05), (-1.1, 0.75, -1.0), 68),
    "desk_light": ((1.25, 1.50, -0.35), (1.30, 0.85, -1.70), 46),
    "cot": ((-0.15, 1.45, -0.05), (-0.85, 0.50, -1.60), 54),
    "shelf": ((-0.45, 1.45, 0.05), (-0.70, 1.00, 1.90), 58),
    "door": ((-0.30, 1.45, 0.10), (2.20, 1.10, 0.0), 56),
    "west": ((1.60, 1.50, 0.60), (-2.20, 1.10, 0.35), 64),
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
    res = (800, 540)
    for a in ARGS:
        if a.startswith("--res="):
            w, h = a[6:].split("x")
            res = (int(w), int(h))
    sel = C.args_shots(ARGS)
    X.begin()
    X.decal("M_Decal_CellDrawing", "cell_drawing.png")          # decals first: their images must exist before the GLB import
    Q.alpha_decal("M_Decal_Sheet", "sheet_print.png")
    Q.alpha_decal("M_Decal_TableMask", "table_mask.png")
    # create the textured preview materials BEFORE the import: a GLB material of the same name would otherwise win and stay untextured
    for glb, _, _ in MODELS + SHEETS:
        pth = C.model_glb(glb)
        if os.path.exists(pth):
            for mt in C.glb_json(pth).get("materials", []):
                if mt.get("name", "").startswith("M_"):
                    M.material(mt["name"])
    for glb, pos, yaw in MODELS:
        C.qa_import(C.model_glb(glb), pos, yaw)
    for glb, pos, yaw in SHEETS:
        h = C.qa_import(C.model_glb(glb), pos, 0)
        if h is not None:
            h.rotation_euler = (math.radians(-90.0), 0, math.radians(yaw))
    retex()
    for o in bpy.data.objects:
        if o.type == "MESH":
            for i, m in enumerate(o.data.materials):
                if m is not None and m.name.split(".")[0] in ("M_Decal_CellDrawing", "M_Decal_Sheet", "M_Decal_TableMask"):
                    o.data.materials[i] = bpy.data.materials[m.name.split(".")[0]]
    C.qa_begin(samples=24)
    for n, col, st in (("M_Emissive_Warm", "FFB46B", 6.0), ("M_Emissive_Red", "FF3B2F", 6.0), ("M_Emissive_Table", "FFF1D0", 4.0)):
        m = bpy.data.materials.get(n)
        if m:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Emission Color"].default_value = M.hex_rgba(col)
            b.inputs["Emission Strength"].default_value = st
    for tag, (cam, tgt, vfov) in SHOTS.items():
        if not C.want(tag, sel):
            continue
        for nm, kind, pos, en, col, rad in LIGHTS:
            C.qa_light(nm, kind, pos, en, col, radius=rad)
        C.shoot(f"prev_cell_{tag}", cam, tgt, vfov=vfov, res=res, samples=24, world=0.05)
        C.qa_clear()


main()
