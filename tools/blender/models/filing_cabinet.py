"""filing_cabinet.glb — 1960s pressed-steel 4-drawer filing cabinet (green-grey enamel), brass card
holders with typed index cards, brass bar pulls, cylinder lock. The third drawer from the
bottom (second from the top) stands 7 cm ajar showing a few staff-record folders.

0.50 w x 1.32 h x 0.60 d (drawer fronts flush at y = -0.30, pulls stand 3 cm proud).
Origin = floor centre. Front faces Blender -Y (Godot +Z). Top is flat at 1.32 (the bust sits on it).
Static (no IA_ parts).

    blender -b --factory-startup -P tools/blender/models/filing_cabinet.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402

NAME = "filing_cabinet"
S, D, B, P = "M_Steel_Painted", "M_Steel_Dark", "M_Brass_Aged", "M_Paper"
HW, BACK, FRONT, H = 0.25, 0.30, -0.288, 1.32
FT = 0.012                      # drawer-front thickness
YF = FRONT - FT                 # drawer-front face (-0.30)
Z0, PITCH, GAP = 0.075, 0.3075, 0.006
AJAR_I, AJAR = 2, 0.07
LABELS = ["S – Z", "M – R", "G – L", "A – F"]    # bottom -> top


def box(name, mn, mx, mat, bevel=0.002, seg=1):
    return A.box_minmax(name, mn, mx, mat=mat, bevel=bevel, segments=seg)


def drawer_z(i):
    z0 = Z0 + i * PITCH
    return z0, z0 + PITCH - GAP


def front_furniture(i, dy):
    """Card holder, card + text, bar pull for drawer i; dy = ajar offset (negative = out)."""
    parts = []
    z0, z1 = drawer_z(i)
    yf = YF + dy
    zc = z1 - 0.075
    # paper index card behind a brass frame
    parts.append(box(f"card{i}", (-0.042, yf - 0.0008, zc - 0.019), (0.042, yf, zc + 0.019), P, 0.0))
    prof = [(0.0, 0.0), (0.0, 0.0018), (0.003, 0.0028), (0.009, 0.0028), (0.0105, 0.0016), (0.0105, 0.0)]
    path = [(-0.05, yf, zc - 0.026), (0.05, yf, zc - 0.026), (0.05, yf, zc + 0.026), (-0.05, yf, zc + 0.026)]
    parts.append(A.sweep(f"card_frame{i}", prof, path, up=(0, -1, 0), closed=True, mat=B))
    for sx in (-0.044, 0.044):
        parts.append(A.screw(f"card_rivet{i}", 0.0022, (sx, yf - 0.0028, zc), (0, -1, 0), B, None, segs=6))
    parts.append(A.text_lowpoly(f"card_text{i}", LABELS[i], 0.024, depth=0.0, resolution=2,
                                loc=(0.0, yf - 0.001, zc - 0.001), rot=(math.pi / 2, 0, 0), mat="M_Bakelite",
                                font_path=A.font_path()))
    # brass bar pull on two posts
    zh = zc - 0.065
    pull = [(-0.065, yf + 0.002, zh), (-0.065, yf - 0.026, zh), (0.065, yf - 0.026, zh), (0.065, yf + 0.002, zh)]
    parts.append(A.tube(f"pull{i}", pull, 0.0062, sides=8, fillet=0.012, fillet_segs=3, mat=B))
    for sx in (-0.065, 0.065):
        parts.append(A.cyl_s(f"pull_rose{i}", 0.012, 0.004, loc=(sx, yf - 0.002, zh), rot=(math.pi / 2, 0, 0),
                                verts=10, mat=B, bevel=0.001, segments=1))
    return parts


def build():
    M.reset_scene()
    A.prepare_materials()
    parts = []
    carcass = M.box("carcass", (2 * HW, BACK - FRONT, H), loc=(0, (BACK + FRONT) / 2, H / 2), mat=S, bevel=0.009,
                    segments=2)
    # recessed toe-kick and the cavity behind the ajar drawer
    M.boolean(carcass, box("cut_kick", (-HW + 0.016, FRONT - 0.05, -0.05), (HW - 0.016, FRONT + 0.035, 0.062), S, 0.0))
    za0, za1 = drawer_z(AJAR_I)
    M.boolean(carcass, box("cut_ajar", (-HW + 0.014, FRONT - 0.05, za0 + 0.006), (HW - 0.014, BACK - 0.03, za1 - 0.006), S, 0.0))
    A.mat_by_face(carcass, lambda c, n, cur: D if (c.y > FRONT + 0.004 and abs(c.x) < HW - 0.005 and
                                                (c.z < 0.063 or za0 < c.z < za1)) else None)
    parts.append(carcass)
    # pressed panel on both sides
    for s in (-1, 1):
        fm = A.frame_matrix((s * HW, 0, 0), (0, s, 0), (0, 0, 1), (s, 0, 0))
        parts.append(A.raised_field(f"side_panel{s}", -0.25, 0.25, 0.12, 1.20, 0.012, 0.003, fm, mat=S))
    # drawer fronts
    for i in range(4):
        z0, z1 = drawer_z(i)
        dy = -AJAR if i == AJAR_I else 0.0
        parts.append(M.box(f"dfront{i}", (2 * HW - 0.024, FT, z1 - z0), loc=(0, FRONT - FT / 2 + dy, (z0 + z1) / 2), mat=S,
                           bevel=0.0045, segments=2))
        parts += front_furniture(i, dy)
    # the ajar drawer's box and a few folders
    z0, z1 = za0, za1
    yb0 = FRONT - AJAR                       # back face of the pulled-out front
    for sx in (-1, 1):
        parts.append(box(f"dside{sx}", (sx * 0.226 - 0.0035, yb0, z0 + 0.016), (sx * 0.226 + 0.0035, 0.22, z1 - 0.045), D, 0.0012))
    parts.append(box("dbottom", (-0.226, yb0, z0 + 0.012), (0.226, 0.22, z0 + 0.018), D, 0.0))
    parts.append(box("dback", (-0.226, 0.214, z0 + 0.016), (0.226, 0.22, z1 - 0.045), D, 0.001))
    parts.append(box("follower", (-0.20, -0.214, z0 + 0.018), (0.20, -0.208, z1 - 0.07), D, 0.001))
    for k, (y, tilt, h) in enumerate(((-0.315, 14, 0.235), (-0.300, 11, 0.232), (-0.282, 9, 0.236), (-0.262, 7, 0.228),
                                      (-0.240, 5, 0.230))):
        f = M.box(f"folder{k}", (0.40, 0.0025, h), mat=P, bevel=0.0008, segments=1)
        f.data.transform(A.Matrix.Translation((0.004 * (k % 2), 0, h / 2)))
        f.data.transform(A.Matrix.Rotation(math.radians(-tilt), 4, "X"))
        f.location = (0.0, y, z0 + 0.018)
        parts.append(f)
        tab_x = -0.14 + 0.07 * k
        t = M.box(f"folder_tab{k}", (0.06, 0.0025, 0.018), mat=P, bevel=0.0006, segments=1)
        t.data.transform(A.Matrix.Translation((tab_x, 0, h + 0.009)))
        t.data.transform(A.Matrix.Rotation(math.radians(-tilt), 4, "X"))
        t.location = (0.0, y, z0 + 0.018)
        parts.append(t)
    # cylinder lock (top right)
    lz = drawer_z(3)[1] - 0.032
    parts.append(A.cyl_s("lock", 0.0115, 0.008, loc=(0.185, YF - 0.004, lz), rot=(math.pi / 2, 0, 0), verts=14, mat=B,
                            bevel=0.0015, segments=1))
    parts.append(box("lock_slot", (0.1835, YF - 0.0085, lz - 0.0055), (0.1865, YF - 0.0075, lz + 0.0055), "M_Bakelite", 0.0))
    A.presmooth(parts)
    body = M.join(parts, "filing_cabinet_body")
    A.finalize_uv()
    print(f"[{NAME}] tris={M.tri_count()}")
    return body


def main():
    args = M.main_guard()
    build()
    A.export_lean(NAME)
    if "--no-render" in args:
        return
    A.render_setup(32, bounces=4)
    M.box("QA_floor", (4, 4, 0.02), loc=(0, 0, -0.01), mat="M_Wood_Floor", bevel=0)
    M.render_preview(NAME, (1.05, -1.75, 1.55), (0.0, 0.0, 0.70), lens=38, res=(760, 960), samples=32,
                     world_strength=0.35, lights=A.STUDIO)
    M.box("QA_floor", (4, 4, 0.02), loc=(0, 0, -0.01), mat="M_Wood_Floor", bevel=0)
    M.render_preview(NAME + "_2", (0.30, -0.95, 1.30), (0.0, -0.30, 0.90), lens=45, res=(900, 700), samples=32,
                     world_strength=0.35, lights=A.STUDIO)


main()
