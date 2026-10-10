"""shell_lift4.glb — the Array Hall's south bay (Chapter 4, group A): the lift's lowest landing, a concrete recess in the
hall wall (x +-6, from the circle to the back wall z 18.2, ceiling y 6.2) with a steel portal arch at the mouth, two
ceiling beams, caged lamps, a brass level plate with NO numeral (the unnumbered floor) and Leyla's chalk sign and "1998".
Contract: docs/models/ch4.md section 3 shell_lift4; results: docs/models/ch4_a.md.

Built in WORLD coordinates. The Chapter 3 freight_lift stands in it at (0, 0, 16.4); the bridge deck covers the mouth.

  bay_floor     concrete (x +-6, z from the circle to 18.2)
  bay_walls     concrete: the side walls, the back wall, the ceiling with the shaft opening (x +-1.3, z 15.1 - 17.7) and
                the short dark shaft above it
  bay_frame     steel + brass (two surfaces): the portal arch (lintel along the circle + two jambs), two ceiling beams, wall
                skirting, two caged lamps, rivets; brass level plate with an arrow and no numeral
  leyla_chalk   M_Chalk, flat strokes 2 mm proud on the back wall at (-3.0, 1.5, 18.18) facing -Z: her sign (a crescent
                opening right with three dots) and the digits 1998 under it
  empties       echo_mount_leyla_lift (-3.4, 0, 17.0) yaw 0 (faces the chalk), lift_light (0, 5.8, 16.4)

    blender -b --factory-startup -P tools/blender/models/shell_lift4.py [-- --no-render] [--shots=1,2]
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
from lib_ch4 import K, CONC, STEEL, BRASS, CHALK, R_HALL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "shell_lift4"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 5000, 5, 4
BX, BZ1, CEIL = C.BAY_X, C.BAY_BACK, C.BAY_CEIL
Z0 = math.sqrt(R_HALL ** 2 - BX ** 2)                     # 12.649: where the side walls leave the hall circle
INSIDE = (0.0, 3.0, 15.5)


def mouth(n=24):
    return [(-BX + 2.0 * BX * i / n, math.sqrt(R_HALL ** 2 - (-BX + 2.0 * BX * i / n) ** 2)) for i in range(n + 1)]


def plan_outline():
    return mouth() + [(BX, BZ1), (-BX, BZ1)]


# ====================================================================== concrete
def floor_parts():
    return [K.flat_poly("bay_floor_p", plan_outline(), [], 0.0, CONC, up=True)]


def wall_parts():
    out = []
    out.append(C.arc_strip("side_w", [(-BX, Z0), (-BX, BZ1)], 0.0, CEIL, CONC, inside_pt=INSIDE))
    out.append(C.arc_strip("side_e", [(BX, Z0), (BX, BZ1)], 0.0, CEIL, CONC, inside_pt=INSIDE))
    out.append(C.arc_strip("back", [(-BX, BZ1), (BX, BZ1)], 0.0, CEIL, CONC, inside_pt=INSIDE))
    hole = [(-1.3, 15.1), (1.3, 15.1), (1.3, 17.7), (-1.3, 17.7)]
    out.append(K.flat_poly("bay_ceiling", plan_outline(), [hole], CEIL, CONC, up=False))
    loop = hole + [hole[0]]
    out.append(C.arc_strip("shaft", loop, CEIL, 9.0, CONC, inside_pt=(0.0, 7.5, 16.4)))
    out.append(K.flat_poly("shaft_cap", hole, [], 9.0, CONC, up=False))
    return out


# ====================================================================== steel + brass
def frame_parts():
    st, br = [], []
    # the portal: lintel along the hall circle, two jambs
    lintel = K.revolve("lintel", [(R_HALL + 0.02, 5.7), (R_HALL - 0.22, 5.7), (R_HALL - 0.22, CEIL), (R_HALL + 0.02, CEIL)],
                       C.BAY_PHI[0], C.BAY_PHI[1], 18, STEEL, closed=True)
    st.append(lintel)
    for phi in C.BAY_PHI:
        j = K.gbox("jamb", (-0.28, 0.0, -0.17), (0.28, CEIL, 0.17), STEEL, 0.01)
        C.at_azimuth(j, phi, R_HALL - 0.1)
        st.append(j)
    # two ceiling beams (I-section: web + flanges) framing the shaft opening
    for z in (14.85, 17.85):
        st.append(K.gbox("beam_web", (-BX, 5.74, z - 0.02), (BX, 6.14, z + 0.02), STEEL, 0.0))
        st.append(K.gbox("beam_fl_a", (-BX, 5.70, z - 0.2), (BX, 5.74, z + 0.2), STEEL, 0.0))
        st.append(K.gbox("beam_fl_b", (-BX, 6.14, z - 0.2), (BX, 6.2, z + 0.2), STEEL, 0.0))
        for i in range(-5, 6):                                  # rivets on the lower flange
            st.append(K.rivet("rv", 0.022, (i * 1.05, 5.70, z + 0.1), normal=(0, -1, 0), mat=STEEL, segs=6))
    # skirting angle along the walls
    st.append(K.gbox("skirt_w", (-BX, 0.0, Z0), (-BX + 0.08, 0.16, BZ1), STEEL, 0.004))
    st.append(K.gbox("skirt_e", (BX - 0.08, 0.0, Z0), (BX, 0.16, BZ1), STEEL, 0.004))
    st.append(K.gbox("skirt_b", (-BX, 0.0, BZ1 - 0.08), (BX, 0.16, BZ1), STEEL, 0.004))
    # wall ribs (flat bars) and a horizontal band at y 3.1 - 3.3 round the three walls
    for x in (-5.4, -4.2, -1.8, 1.8, 4.2, 5.4):
        st.append(K.gbox("rib_b", (x - 0.11, 0.16, BZ1 - 0.06), (x + 0.11, CEIL, BZ1), STEEL, 0.004))
    for z in (14.6, 16.4, 17.9):
        st.append(K.gbox("rib_w", (-BX, 0.16, z - 0.11), (-BX + 0.06, CEIL, z + 0.11), STEEL, 0.004))
        st.append(K.gbox("rib_e", (BX - 0.06, 0.16, z - 0.11), (BX, CEIL, z + 0.11), STEEL, 0.004))
    st.append(K.gbox("band_b", (-BX, 3.1, BZ1 - 0.07), (BX, 3.3, BZ1), STEEL, 0.004))
    st.append(K.gbox("band_w", (-BX, 3.1, Z0), (-BX + 0.07, 3.3, BZ1), STEEL, 0.004))
    st.append(K.gbox("band_e", (BX - 0.07, 3.1, Z0), (BX, 3.3, BZ1), STEEL, 0.004))
    # two caged bulkhead lamps on the side walls at y 3.4, z 16.0
    for sx in (-1, 1):
        x0 = sx * BX
        d = -sx
        st.append(K.gbox("lamp_back", (x0 - 0.04 if sx > 0 else x0, 3.22, 15.88), (x0 if sx > 0 else x0 + 0.04, 3.58, 16.12), STEEL, 0.004))
        cage = []
        xi = x0 + d * 0.04
        xo = x0 + d * 0.24
        a, b = sorted((xi, xo))
        for z in (15.9, 16.1):
            for y in (3.24, 3.56):
                cage.append(K.gbox("cb", (a, y - 0.008, z - 0.008), (b, y + 0.008, z + 0.008), STEEL, 0.0))
        for y in (3.24, 3.56):
            cage.append(K.gbox("cr", (xo - 0.008 if sx > 0 else xo, y - 0.008, 15.9), (xo if sx > 0 else xo + 0.008, y + 0.008, 16.1), STEEL, 0.0))
        for z in (15.9, 16.1):
            cage.append(K.gbox("cv", (a, 3.24, z - 0.008), (b, 3.56, z + 0.008), STEEL, 0.0))
        st += cage
        st.append(K.gcyl("bulb", 0.07, 0.0, 0.2, base=(xi, 3.4, 16.0), axis=(d, 0, 0), segments=8, mat=STEEL))
    # brass level plate on the back wall, east of the cage: 0.34 x 0.46, an arrow and NO numeral
    pc = (3.0, 1.55, BZ1 - 0.0)
    plate = K.gbox("lp", (pc[0] - 0.17, pc[1] - 0.23, BZ1 - 0.012), (pc[0] + 0.17, pc[1] + 0.23, BZ1), BRASS, 0.004)
    br.append(plate)
    arrow = [(-0.07, 0.05), (0.07, 0.05), (0.0, -0.07)]                     # a down arrow head (facing -Z, built facing +Z)
    shaft_ = [(-0.02, 0.05), (0.02, 0.05), (0.02, 0.15), (-0.02, 0.15)]
    for loop in (arrow, shaft_):
        o = K.plate("la", [loop], 0.004, z0=0.0, mat=BRASS, bevel=0.0, drop_bottom=True)
        o.data.transform(Matrix.Rotation(math.pi, 4, "Y"))                  # face -Z, still reading upright
        o.data.transform(Matrix.Translation((pc[0], pc[1] - 0.02, BZ1 - 0.012)))
        br.append(o)
    for sx in (-1, 1):
        for sy in (-1, 1):
            br.append(K.rivet("lr", 0.012, (pc[0] + sx * 0.14, pc[1] + sy * 0.19, BZ1 - 0.012), normal=(0, 0, -1), mat=BRASS, segs=8))
    return st, br


# ====================================================================== chalk
def chalk_parts():
    rng = random.Random(1998)
    out = []
    # the sign (crescent + three dots), 0.55 high
    sign = C.S.inlay("sign", "sign", 0.55, depth=0.002, mat=CHALK)
    out.append(sign)
    # the digits 1998, 0.20 high, slightly uneven like chalk, under the sign
    for k, ch in enumerate("1998"):
        d = C.N.digit_obj(f"d{k}", int(ch), 0.20, 0.002, CHALK)
        d.data.transform(Matrix.Rotation(math.radians(rng.uniform(-4, 4)), 4, "Z"))
        d.data.transform(Matrix.Translation((-0.27 + 0.18 * k, -0.43 + rng.uniform(-0.01, 0.01), 0.0)))
        out.append(d)
    # a chalk underline
    out.append(K.gbox("ul", (-0.32, -0.60, 0.0), (0.32, -0.585, 0.002), CHALK, 0.0))
    o = M.join(out, "leyla_chalk")
    # facing -Z on the back wall: turn 180 about Y (the art still reads left to right for a viewer looking south)
    o.data.transform(Matrix.Rotation(math.pi, 4, "Y"))
    o.data.transform(Matrix.Translation((-3.0, 1.5, BZ1 - 0.018)))
    return o


# ====================================================================== build
def build():
    M.reset_scene()
    C.ensure_materials()
    floor = C.merge("bay_floor", floor_parts())
    walls = C.merge("bay_walls", wall_parts())
    st, br = frame_parts()
    frame = C.merge("bay_frame", st + br)
    chalk = chalk_parts()
    K.empty("echo_mount_leyla_lift", (-3.4, 0.0, 17.0))
    K.empty("lift_light", (0.0, 5.8, 16.4))
    K.to_blender()
    C.finalize()
    return dict(floor=floor, walls=walls, frame=frame, chalk=chalk)


def verify(path):
    req = ["bay_floor", "bay_walls", "bay_frame", "leyla_chalk", "echo_mount_leyla_lift", "lift_light"]
    expect = {"echo_mount_leyla_lift": (-3.4, 0.0, 17.0), "lift_light": (0.0, 5.8, 16.4)}
    errs = C.verify(path, required=req, identity=req, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    lo, hi = C.bounds(["bay_floor", "bay_walls", "bay_frame", "leyla_chalk"])
    print(f"{C.TAG} bay bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    C.qa_begin()
    C.qa_floor_nonormal("bay_floor")
    C.qa_hall(shell=True, extra=[("freight_lift", C.LIFT_POS, 0.0)])
    C.qa_floor_nonormal("qa_sh_hall_floor")
    for o in bpy.data.objects:
        if o.name.startswith("qa_sh_oculus_shutter_a"):
            K.pose_slide(o, (-1.7, 0, 0))
        elif o.name.startswith("qa_sh_oculus_shutter_b"):
            K.pose_slide(o, (1.7, 0, 0))
    for o in bpy.data.objects:                 # the cage has arrived: both gates folded open (scale Z 0.15)
        if o.name.startswith("qa_freight_lift_IA_gate_east") or o.name.startswith("qa_freight_lift_IA_gate_west"):
            if o.type == "MESH" and "lock" not in o.name:
                o.scale = (1.0, 0.15, 1.0)
    S = int(os.environ.get("MR_S", "32"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))
    def bay_lights(cam, fill, ambient=0.1):
        C.lights(cam, fill=fill, ambient=ambient, shaft=False, core=False, work=False)
        K.light("bay_lamp_w", "POINT", (-5.55, 3.4, 16.0), 1800.0, "FFC27A", radius=0.1)
        K.light("bay_lamp_e", "POINT", (5.55, 3.4, 16.0), 1800.0, "FFC27A", radius=0.1)
        K.light("lift_light", "POINT", (0.0, 5.8, 16.4), 1200.0, "FFC27A", radius=0.1)
        K.light("core_glow", "POINT", C.CORE_C, 20000.0, "CFF6FF", radius=0.5)
    if C.want(args, "1"):                      # the bay seen from the hall: the portal, the cage, the chalk
        cam, tgt, fov = C.view("bay_hero")
        bay_lights(cam, 60.0, 0.12)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):                      # the chalk
        cam, tgt, fov = C.view("lift_chalk")
        bay_lights(cam, 40.0, 0.1)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):                      # the lift view (R) from the east gate
        cam, tgt, fov = C.view("lift")
        bay_lights(cam, 40.0, 0.1)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)


def main():
    args = M.main_guard()
    parts = build()
    K.report(NAME)
    path = C.export(NAME)
    errs = verify(path)
    print(f"{C.TAG} VERIFY {'FAILED: ' + str(errs) if errs else 'OK'}")
    if "--no-render" in args:
        return
    qa(args, parts)


main()
