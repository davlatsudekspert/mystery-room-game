"""notebook.glb — Dr. Leyla Rahimova's leather-bound lab notebook (desk prop + inventory item).

Leather boards with a blind-tooled border, rounded leather spine with three raised bands, a cream page
block with a concave fore-edge, a black elastic closure band, brass corner protectors, a red ribbon
bookmark trailing from the tail, a handwritten paper label ("Laboratory 7 / L. Rahimova 1979") and a
loose folded note peeking out of the head. 0.170 x 0.230 x 0.024 m. Lies flat (cover up = Blender +Z),
spine on the left (-X), head (top edge) toward +Y. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/notebook.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_arch as A  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "notebook"
W, HH, TT = 0.170, 0.230, 0.024
BT = 0.0026              # board thickness
XS = -W / 2              # spine side


def corner_cap(x, y, sx, sy, z0):
    leg = 0.016
    pts = [(x, y), (x - sx * leg, y), (x, y - sy * leg)]
    if sx * sy < 0:
        pts = pts[::-1]
    cap = L.curve_solid("corner", [pts], BT + 0.0010, bevel=0.0005, mat="M_Brass_Aged")
    cap.location = (0, 0, z0 - 0.0005)
    return cap


def build():
    parts = []
    # boards
    for z0 in (0.0, TT - BT):
        b = L.curve_solid("board", [L.rrect4(W - 0.004, HH, radii=(0.005, 0.005, 0.0, 0.0), n=4, cx=0.002)], BT,
                          bevel=0.0009, bevel_res=1, mat="M_Leather")
        b.location = (0, 0, z0)
        parts.append(b)
    # rounded spine (C section extruded along Y) + three raised bands
    def spine_section(bulge, thick):
        out, inn = [], []
        for i in range(9):
            t = -math.pi / 2 + math.pi * i / 8
            out.append((XS + 0.0015 - bulge * math.cos(t), TT / 2 + (TT / 2) * math.sin(t)))
            inn.append((XS + 0.0015 - (bulge - thick) * math.cos(t), TT / 2 + (TT / 2 - thick) * math.sin(t)))
        return out[::-1] + inn
    sp = L.curve_solid("spine", [spine_section(0.0062, 0.0026)], HH, bevel=0.0006, mat="M_Leather")
    L.to_front(sp, y_back=HH / 2)
    parts.append(sp)
    for yb in (-0.070, 0.0, 0.070):
        band = L.curve_solid("hub", [spine_section(0.0074, 0.0040)], 0.0055, bevel=0.0012, bevel_res=0,
                             mat="M_Leather")
        L.to_front(band, y_back=yb + 0.00275)
        parts.append(band)
    # page block with a concave fore-edge
    fx = W / 2 - 0.0028
    sec = [(XS + 0.002, BT + 0.0002), (fx - 0.0004, BT + 0.0002), (fx, BT + 0.003), (fx - 0.0012, TT / 2),
           (fx, TT - BT - 0.003), (fx - 0.0004, TT - BT - 0.0002), (XS + 0.002, TT - BT - 0.0002)]
    pages = L.curve_solid("pages", [sec], HH - 0.006, bevel=0.0004, mat="M_Paper")
    L.to_front(pages, y_back=(HH - 0.006) / 2)
    parts.append(pages)
    # blind-tooled border + paper label with handwriting on the front cover
    zt = TT + 0.00004
    parts.append(L.flat_shape("tooling", L.outline_ring(W - 0.022, HH - 0.020, 0.004, 0.0008, 3), mat="M_Bakelite",
                              loc=(0.003, 0.0, zt)))
    lab = L.curve_solid("label", [L.rounded_rect(0.086, 0.044, 0.003, 3)], 0.0003, bevel=0.0, mat="M_Paper")
    lab.location = (0.006, 0.052, TT)
    parts.append(lab)
    parts.append(L.flat_shape("label_line", L.outline_ring(0.080, 0.038, 0.002, 0.0005, 3), mat="M_Bakelite",
                              loc=(0.006, 0.052, TT + 0.00034)))
    parts.append(D.hand("hand1", "Laboratory 7", 0.0105, mat="M_Bakelite",
                        loc=(0.006, 0.0575, TT + 0.00036)))
    parts.append(D.hand("hand2", "L. Rahimova · 1979", 0.0072, mat="M_Bakelite",
                        loc=(0.006, 0.0430, TT + 0.00036)))
    # brass corner protectors (fore-edge corners, both boards)
    for sy in (-1, 1):
        for z0 in (0.0, TT - BT):
            parts.append(corner_cap(W / 2 + 0.0005, sy * (HH / 2 + 0.0005), 1, sy, z0))
    # elastic closure band (closed loop around the boards, near the fore-edge)
    bx = W / 2 - 0.022
    rr = 0.0035
    y0, y1, z0, z1 = -HH / 2 - 0.0002, HH / 2 + 0.0002, -0.0002, TT + 0.0002
    path = []
    for (cy, cz, a0) in ((y1 - rr, z0 + rr, -90.0), (y1 - rr, z1 - rr, 0.0), (y0 + rr, z1 - rr, 90.0),
                         (y0 + rr, z0 + rr, 180.0)):
        for i in range(4):
            a = math.radians(a0 + 90.0 * i / 3)
            path.append((bx, cy + rr * math.cos(a), cz + rr * math.sin(a)))
    band = A.sweep("elastic", [(-0.0012, -0.0033), (0.0, -0.0033), (0.0, 0.0033), (-0.0012, 0.0033)], path,
                   up=(1, 0, 0), closed=True, mat="M_Rubber")
    parts.append(band)
    # ribbon bookmark out of the tail, lying on the table with a V-cut end
    rib_path = [(-0.020, -HH / 2 + 0.010, TT - BT - 0.0010), (-0.020, -HH / 2 - 0.004, TT - BT - 0.0016),
                (-0.020, -HH / 2 - 0.010, 0.012), (-0.020, -HH / 2 - 0.014, 0.0035), (-0.020, -HH / 2 - 0.020, 0.0006),
                (-0.020, -HH / 2 - 0.030, 0.0004)]
    rib = A.sweep("ribbon", [(-0.00025, -0.0030), (0.00025, -0.0030), (0.00025, 0.0030), (-0.00025, 0.0030)],
                  rib_path, up=(1, 0, 0), mat="M_String_Red")
    parts.append(rib)
    notch = L.flat_shape("ribbon_end", [[(-0.0030, 0.0), (0.0030, 0.0), (0.0030, -0.006), (0.0, -0.0025),
                                         (-0.0030, -0.006)]], mat="M_String_Red",
                         loc=(-0.020, -HH / 2 - 0.030, 0.00065))
    parts.append(notch)
    # loose folded note peeking out of the head
    note = L.curve_solid("note", [[(-0.030, 0.0), (0.024, 0.0), (0.026, 0.019), (-0.028, 0.017)]], 0.0004,
                         bevel=0.0, mat="M_Paper")
    note.data.transform(Matrix.Rotation(math.radians(-4.0), 4, "Z"))
    note.location = (0.020, HH / 2 - 0.006, TT / 2 + 0.003)
    parts.append(note)
    return [M.join(parts, NAME)]


def main():
    D.item_main(NAME, build, shots=[
        ("", (0.16, -0.30, 0.26), (0.0, 0.0, 0.0), 45),
        ("_2", (-0.26, 0.12, 0.10), (-0.03, 0.0, 0.0), 45),
    ])


if __name__ == "__main__":
    main()
