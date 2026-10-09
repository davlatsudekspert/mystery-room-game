"""routing_chart.glb — enamel-framed "PNEUMATIC POST" routing chart under glass (Chapter 2, group B1).

Wall-mounted: origin = floor level, centre of the back face (z = 0); front faces +Z.
Placement: (5.0, 0, -0.35), yaw -90 (front faces world -X). Picture centre at y = 1.75.

  * chart_image: the picture, 0.50 w x 0.70 h, centred at (0, 1.75, 0.02), facing +Z, UV 0..1
    (u left -> right, v bottom -> top), slot M_Decal_RoutingChart (decals/ch2/routing_chart.png, 600 x 840);
  * glass cover (M_Glass) 6 mm in front of it, a dark backing plate, a green enamelled steel frame with a
    chamfered face and brass corner screws, a small brass index plate under the frame.

    blender -b --factory-startup -P tools/blender/models/routing_chart.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2_furniture1 as F  # noqa: E402
from lib_ch2_furniture1 import G, gbox, gquad, gtext  # noqa: E402

NAME = "routing_chart"
BUDGET = 1500
IW, IH, CY, IZ = 0.50, 0.70, 1.75, 0.02
FRAME = "M_Enamel_Green"
FW = 0.042                     # frame face width
FD = 0.034                     # frame depth (wall -> front face)


def build():
    M.reset_scene()
    F.ensure_materials()
    img = F.decal_path("routing_chart.png")
    M.material("M_Decal_RoutingChart", color="E3D9BE", rough=0.3, image=img)
    # chart image (UV 0..1, as seen by the player)
    chart = gquad("chart_image", (0.0, CY, IZ), (1, 0, 0), (0, 1, 0), IW, IH, "M_Decal_RoutingChart")
    # backing plate and glass
    parts = [gbox("backing", (-IW / 2 - 0.012, CY - IH / 2 - 0.012, 0.0), (IW / 2 + 0.012, CY + IH / 2 + 0.012, IZ - 0.0005),
                  "M_Steel_Dark", 0.0)]
    glass = gquad("chart_glass", (0.0, CY, IZ + 0.006), (1, 0, 0), (0, 1, 0), IW + 0.012, IH + 0.012, "M_Glass")
    # frame: a moulded profile swept around the picture (s > 0 = inward, u = out of the wall)
    prof = [(-FW, 0.0), (0.006, 0.0), (0.006, IZ + 0.0085), (0.0, IZ + 0.0085), (-0.004, FD - 0.004),
            (-0.010, FD), (-FW + 0.008, FD), (-FW + 0.002, FD - 0.006), (-FW, FD - 0.012)]
    hw, hh = IW / 2, IH / 2
    path = [G(-hw, CY - hh, 0.0), G(hw, CY - hh, 0.0), G(hw, CY + hh, 0.0), G(-hw, CY + hh, 0.0)]
    frame = A.sweep("frame", prof, path, up=tuple(F.GV((0, 0, 1))), closed=True, mat=FRAME)
    parts.append(frame)
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(F.screw(f"screw{sx}{sy}", 0.0045, (sx * (hw + FW / 2 - 0.004), CY + sy * (hh + FW / 2 - 0.004), FD),
                                 "z", mat="M_Brass_Aged", segs=8))
    # small brass index plate under the frame with the stack code it serves
    py = CY - hh - FW - 0.03
    parts.append(F.gpoly("plate", [A.rounded_rect(0.13, 0.034, 0.005, 2)], 0.0025, (0.0, py, 0.0), (1, 0, 0), (0, 1, 0),
                         mat="M_Brass_Aged", bevel=0.0006, drop_bottom=True))
    parts.append(gtext("plate_txt", "Nº 7", 0.017, (0.0, py, 0.0027), font=F.FONT_SERIF_B, mat="M_Lacquer_Black"))
    for sx in (-1, 1):
        parts.append(F.screw(f"plate_screw{sx}", 0.0025, (sx * 0.054, py, 0.0025), "z", mat="M_Brass_Aged", segs=6))
    F.part("chart_frame", parts)
    F.part("chart_glass", [glass])
    F.finalize_all(wood_grain=False)
    return F.report(NAME)


def verify(path):
    req = ["chart_image"]
    doc = F.glb_json(path)
    # chart_image must keep UV 0..1 (decal): report its UV bounds
    for mesh in doc.get("meshes", []):
        if mesh.get("name") == "chart_image":
            acc = doc["accessors"][mesh["primitives"][0]["attributes"]["TEXCOORD_0"]]
            print(f"{F.TAG}-verify chart_image UV min={acc.get('min')} max={acc.get('max')}")
    return F.verify_glb(path, required=req, identity=req, budget=BUDGET, show=req + ["chart_frame", "chart_glass"])


POS, YAW = (5.0, 0.0, -0.35), -90.0


def main():
    args = M.main_guard()
    build()
    path = F.export(NAME)
    F.check_names(path)
    errs = verify(path)
    if errs:
        print(f"{F.TAG} VERIFY FAILED: {errs}")
    if "--no-render" in args:
        return
    F.qa_begin()
    F.qa_place(POS, YAW)
    F.qa_room()
    F.qa_neighbours([("tube_station", (5.0, 0, -1.4), -90.0), ("compressor_panel", (5.0, 0, 0.8), -90.0)])
    F.qa_room_lights(150.0)
    F.qa_light("fill", "AREA", (3.6, 2.0, -0.2), 40.0, "FFE6CC", radius=1.2, target=(5.0, 1.75, -0.35))
    if F.want("hero", args):
        F.shoot(NAME, (3.7, 1.6, 0.6), (5.0, 1.65, -0.45), vfov=44)
    if F.want("view", args):
        F.shoot(NAME + "_2", (3.9, 1.7, -0.35), (5.0, 1.75, -0.35), vfov=44)


main()
