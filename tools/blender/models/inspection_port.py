"""inspection_port.glb — the Choir Hall's three crystal inspection ports (×3: port_a, port_b, port_c).
Contract: docs/models/ch3.md §5 inspection_port (+ §1.2 placement, §2 port views); results: docs/models/ch3_c.md.

Origin = the back of the mounting plate (on the wall / post plane), front +Z.
  A (-4.5, 0.85, 2.6) yaw -90 on the east wall; B (-12.0, 4.55, 1.9) yaw 110 on the catwalk post plate;
  C (-8.6, 5.15, 1.9) yaw 180, pitch +60 under the gantry trolley (Basis(UP, yaw) * Basis(RIGHT, pitch)).

  inspection_port (static)  brass porthole: mounting plate Ø0.40 with six slotted screws, barrel Ø0.30 x 0.15 with a
                            base flange and a hoop, the front bezel that holds the lens, a hinge knuckle and a
                            wing-nut dog (one surface, M_Brass_Aged).
  IA_port_ring              the blackened-steel knurled ring round the front (M_Steel_Dark); code: -30° about local
                            +Z per tap (cosmetic). It switches between the port view and its memory view.
  IA_port_lens              the crystal disc Ø0.22 at z = 0.16 (M_Crystal); code: an emission pulse while the 1979
                            loop plays. The lens -> cam.go("port_X").

    blender -b --factory-startup -P tools/blender/models/inspection_port.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "inspection_port"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 2000, 3, 3
BRASS, STEEL, CRYSTAL = B.BRASS, B.STEEL, B.CRYSTAL

PLATE_R, PLATE_T = 0.200, 0.016
BARREL_R, BARREL_Z1 = 0.150, 0.150
RING_RI, RING_RO, RING_Z0, RING_Z1 = 0.142, 0.163, 0.104, 0.146
LENS_R, LENS_Z = 0.110, 0.160
SEG = 24

PORTS = {"a": ((-4.5, 0.85, 2.6), -90.0, 0.0), "b": ((-12.0, 4.55, 1.9), 110.0, 0.0),
         "c": ((-8.6, 5.15, 1.9), 180.0, 60.0)}


# ====================================================================== static brass
def body():
    p = []
    # mounting plate (chamfered front edge) with six slotted screws
    p.append(B.glathe("plate", [(0.0, 0.0), (PLATE_R, 0.0), (PLATE_R, PLATE_T - 0.004), (PLATE_R - 0.004, PLATE_T),
                                (0.0, PLATE_T)], (0, 0, 0), (0, 0, 1), 28, BRASS, smooth=40.0))
    for k in range(6):
        a = math.radians(30 + 60 * k)
        p.append(B.rivet("scr", 0.0085, (0.178 * math.cos(a), 0.178 * math.sin(a), PLATE_T), normal=(0, 0, 1),
                         mat=BRASS, segs=6))
    # barrel: base flange, body with a raised hoop, the ring seat, the front bezel lip that holds the lens
    prof = [(0.168, PLATE_T), (0.168, PLATE_T + 0.010), (BARREL_R, PLATE_T + 0.018), (BARREL_R, 0.062),
            (0.156, 0.066), (BARREL_R, 0.070), (BARREL_R, RING_Z0 - 0.002), (0.140, RING_Z0), (0.140, RING_Z1),
            (0.150, RING_Z1 + 0.002), (0.150, 0.162), (0.132, 0.174), (0.106, 0.172), (0.104, 0.150), (0.0, 0.150)]
    p.append(B.glathe("barrel", prof, (0, 0, 0), (0, 0, 1), SEG, BRASS, smooth=40.0, cap_bottom=False))
    # hinge knuckle (left) and wing-nut dog (right) on the bezel, like a ship's porthole
    p.append(B.gcyl("knuckle", 0.012, -0.022, 0.022, base=(-0.166, 0.0, 0.150), axis=(0, 1, 0), segments=8, mat=BRASS,
                    chamfer=0.002))
    p.append(B.gbox("hleaf", (-0.168, -0.016, 0.142), (-0.140, 0.016, 0.150), BRASS, 0.002))
    p.append(B.gcyl("dogpost", 0.006, 0.0, 0.040, base=(0.150, 0.0, 0.130), axis=(1, 0, 0), segments=8, mat=BRASS))
    p.append(B.gbox("dogbar", (0.160, -0.004, 0.128), (0.178, 0.004, 0.170), BRASS, 0.002))
    wing = B.plate("wing", [A.ccw([(-0.024, 0.003), (-0.006, -0.004), (0.006, -0.004), (0.024, 0.003), (0.020, 0.008),
                                   (-0.020, 0.008)])], 0.004, mat=BRASS, bevel=0.0008)
    wing.data.transform(Matrix.Translation((0.182, 0.0, 0.150)) @ Matrix.Rotation(math.radians(90), 4, "Y") @
                        Matrix.Rotation(math.radians(90), 4, "Z"))
    p.append(wing)
    return B.part(NAME, p)


# ====================================================================== parts
def ring():
    prof = [(RING_RI, RING_Z0), (RING_RO - 0.003, RING_Z0), (RING_RO, RING_Z0 + 0.004, "k"),
            (RING_RO, RING_Z1 - 0.004, "k"), (RING_RO - 0.003, RING_Z1), (RING_RI, RING_Z1)]
    o = B.glathe("ring", prof, (0, 0, 0), (0, 0, 1), 48, STEEL, knurl=0.0022, smooth=25.0, cap_bottom=False,
                 cap_top=False)
    # two grip lugs so the -30° steps read
    lugs = []
    for a in (90.0, 270.0):
        r = math.radians(a)
        lug = B.gbox("lug", (-0.010, -0.006, RING_Z0 + 0.006), (0.010, 0.006, RING_Z1 - 0.006), STEEL, 0.003)
        lug.data.transform(Matrix.Rotation(r - math.pi / 2, 4, "Z") @ Matrix.Translation((0.0, RING_RO + 0.004, 0.0)))
        lugs.append(lug)
    return B.part("IA_port_ring", [o] + lugs, pivot=(0.0, 0.0, (RING_Z0 + RING_Z1) / 2))


def lens():
    prof = [(0.0, 0.151), (LENS_R * 0.6, 0.152), (LENS_R, 0.154), (LENS_R, 0.162), (LENS_R * 0.8, 0.1665),
            (LENS_R * 0.45, 0.1695), (0.0, 0.1705)]
    o = B.glathe("lens", prof, (0, 0, 0), (0, 0, 1), 24, CRYSTAL, smooth=70.0)
    return B.part("IA_port_lens", [o], pivot=(0.0, 0.0, LENS_Z))


# ====================================================================== build / verify
def build():
    M.reset_scene()
    B.ensure_materials()
    st = body()
    rg = ring()
    ln = lens()
    B.K.to_blender()
    A.finalize_uv()
    return dict(body=st, ring=rg, lens=ln)


def verify(path):
    req = [NAME, "IA_port_ring", "IA_port_lens"]
    expect = {"IA_port_ring": (0.0, 0.0, (RING_Z0 + RING_Z1) / 2), "IA_port_lens": (0.0, 0.0, LENS_Z)}
    errs = B.verify(path, req, identity=req, expect=expect, parents={n: None for n in req}, tris=TRI_BUDGET,
                    surf=SURF_BUDGET, mats=MAT_BUDGET)
    lo, hi = B.V.mesh_bounds_godot([o for o in bpy.data.objects if o.type == "MESH"])
    print(f"{B.TAG} bounds min {tuple(round(c, 4) for c in lo)} max {tuple(round(c, 4) for c in hi)}")
    return errs


# ====================================================================== QA
def qa(parts, args):
    B.qa_begin()
    B.hall()
    objs = [parts["body"], parts["ring"], parts["lens"]]
    rest = B.rest_store(objs)
    glow = B.K.glow("qa_lens_glow", "8FE6FF", 0.9)
    # three instances: this scene's objects at A, imported copies at B and C
    root = B.place(objs, *PORTS["a"], name="qa_port_a")
    B.bring(NAME, *PORTS["b"], prefix="qa_pb_")
    B.bring(NAME, *PORTS["c"], prefix="qa_pc_")

    shots = [
        # 1 hero: port A on the east wall, from the hall
        ("1", NAME, (-5.75, 1.25, 1.85), (-4.55, 0.86, 2.6), 40, None),
        # 2 close-up of the ring and the lens (lens pulsing, ring turned one step)
        ("2", NAME + "_2", (-5.02, 0.98, 2.42), (-4.62, 0.85, 2.6), 36, "lit"),
        # 3 port B on the catwalk post, seen from the hall floor
        ("3", NAME + "_3", (-10.0, 1.7, 0.6), (-12.0, 4.5, 1.9), 34, None),
        # 4 port C under the gantry trolley, seen from below
        ("4", NAME + "_4", (-8.0, 2.4, -0.2), (-8.6, 5.1, 1.85), 36, None),
    ]
    for tag, name, cam, tgt, fov, state in shots:
        if not B.want(args, tag):
            continue
        B.rest_apply(objs, rest)
        old = None
        if state == "lit":
            old = B.K.override(parts["lens"], glow)
            B.K.pose_rot(parts["ring"], "z", -30.0)
        B.choir_lights(cam, fill=10.0)
        B.shoot(name, cam, tgt, fov)
        if old is not None:
            B.K.restore(parts["lens"], old)
    return root


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
