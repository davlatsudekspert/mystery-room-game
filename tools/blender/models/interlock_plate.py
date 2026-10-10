"""interlock_plate.glb — the trapped-key interlock rule plate above switch cabinet II (W1 / W1b).
Contract: docs/models/ch3.md §5 interlock_plate (+ §12 interlock_plate.png); results: docs/models/ch3_c.md.

Wall-mounted on the south wall at (-8.3, 0, 4.0), yaw 180. Origin = the wall plane at floor level, front +Z.

  interlock_plate (static)  a dark steel picture frame (outer 0.99 x 0.54) with a backing tray, four slotted screws
                            and two wall lugs (M_Steel_Dark).
  plate_image               the 0.90 x 0.45 enamel plate, a quad centred (0, 2.30, 0.015) facing +Z, UV 0..1
                            (u -> +X, v -> +Y), M_Decal_InterlockPlate (group A's interlock_plate.png, no words).

    blender -b --factory-startup -P tools/blender/models/interlock_plate.py [-- --no-render] [--shots=1,2]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch3_bc as B  # noqa: E402

NAME = "interlock_plate"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 600, 2, 2
STEEL, DECAL = B.STEEL, "M_Decal_InterlockPlate"
CY, W, H, ZQ = 2.30, 0.90, 0.45, 0.015
BORDER, Z_FACE = 0.045, 0.026


def frame():
    p = []
    x0, x1 = -W / 2 - BORDER, W / 2 + BORDER
    y0, y1 = CY - H / 2 - BORDER, CY + H / 2 + BORDER
    # backing tray behind the enamel (its face just behind the quad)
    p.append(B.gbox("back", (-W / 2 - 0.004, CY - H / 2 - 0.004, 0.0), (W / 2 + 0.004, CY + H / 2 + 0.004, ZQ - 0.0015),
                    STEEL, 0.0))
    # four frame bars, a raised bead on the inner edge holding the plate
    p += [B.gbox("fb", (x0, y0, 0.0), (x1, y0 + BORDER, Z_FACE), STEEL, 0.005, 1),
          B.gbox("ft", (x0, y1 - BORDER, 0.0), (x1, y1, Z_FACE), STEEL, 0.005, 1),
          B.gbox("fl", (x0, y0 + BORDER - 0.001, 0.0), (x0 + BORDER, y1 - BORDER + 0.001, Z_FACE), STEEL, 0.005, 1),
          B.gbox("fr", (x1 - BORDER, y0 + BORDER - 0.001, 0.0), (x1, y1 - BORDER + 0.001, Z_FACE), STEEL, 0.005, 1)]
    for (a, b) in (((-W / 2 - 0.008, CY - H / 2 - 0.008), (W / 2 + 0.008, CY - H / 2)),
                   ((-W / 2 - 0.008, CY + H / 2), (W / 2 + 0.008, CY + H / 2 + 0.008)),
                   ((-W / 2 - 0.008, CY - H / 2), (-W / 2, CY + H / 2)),
                   ((W / 2, CY - H / 2), (W / 2 + 0.008, CY + H / 2))):
        p.append(B.gbox("bead", (a[0], a[1], ZQ - 0.002), (b[0], b[1], ZQ + 0.006), STEEL, 0.0))
    # slotted screws in the corners, wall lugs top and bottom
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.append(B.rivet("scr", 0.0085, (sx * (W / 2 + BORDER / 2), CY + sy * (H / 2 + BORDER / 2), Z_FACE),
                             segs=6))
    for sy in (-1, 1):
        yy = y1 if sy > 0 else y0
        p.append(B.gbox("lug", (-0.05, yy - 0.01 if sy > 0 else yy - 0.03, 0.0), (0.05, yy + 0.03 if sy > 0 else yy + 0.01,
                                                                                   0.006), STEEL, 0.0))
        p.append(B.rivet("lrv", 0.008, (0.0, yy + sy * 0.014, 0.006), segs=6))
    return B.part(NAME, p)


def image():
    q = B.K.quad("plate_image", (0.0, CY, ZQ), (1, 0, 0), (0, 1, 0), W, H, DECAL)
    return B.part("plate_image", [q], pivot=(0.0, CY, ZQ))


def build():
    M.reset_scene()
    B.ensure_materials()
    fr = frame()
    im = image()
    B.K.to_blender()
    A.finalize_uv()          # box UVs skip M_Decal_* faces: the quad keeps its 0..1 UVs
    return dict(frame=fr, image=im)


def check_uv(obj):
    """The quad's UV corners in Godot terms: u grows toward +X, v toward +Y."""
    me = obj.data
    uv = me.uv_layers.active.data
    pts = []
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = B.V.C_INV @ (obj.matrix_world @ me.vertices[me.loops[li].vertex_index].co)
            pts.append((round(co.x, 3), round(co.y, 3), tuple(round(c, 3) for c in uv[li].uv)))
    ok = all(((u > 0.5) == (x > 0)) and ((v > 0.5) == (y > CY)) for (x, y, (u, v)) in pts)
    print(f"{B.TAG} plate_image UV corners (godot x, y, uv): {pts} -> {'OK' if ok else 'MIRRORED'}")
    return [] if ok else ["plate_image UV mirrored"]


def verify(path, parts):
    req = [NAME, "plate_image"]
    errs = B.verify(path, req, identity=req, expect={"plate_image": (0.0, CY, ZQ)}, parents={n: None for n in req},
                    tris=TRI_BUDGET, surf=SURF_BUDGET, mats=MAT_BUDGET)
    errs += check_uv(parts["image"])
    lo, hi = B.V.mesh_bounds_godot([parts["frame"]])
    print(f"{B.TAG} frame bounds min {tuple(round(c, 3) for c in lo)} max {tuple(round(c, 3) for c in hi)}")
    return errs


def qa(parts, args):
    B.qa_begin()
    B.hall()
    B.place([parts["frame"], parts["image"]], (-8.3, 0.0, 4.0), 180.0, name="qa_plate")
    for tag, name, cam, tgt, fov in (("1", NAME, (-8.3, 2.05, 2.6), (-8.3, 2.3, 3.97), 40),          # interlock_plate
                                     ("2", NAME + "_2", (-7.55, 2.2, 3.35), (-8.25, 2.3, 3.98), 46)):  # oblique close-up
        if B.want(args, tag):
            B.choir_lights(cam, fill=12.0)
            B.shoot(name, cam, tgt, fov)


def main():
    args = M.main_guard()
    parts = build()
    B.K.report(NAME)
    path = B.export(NAME)
    errs = verify(path, parts)
    B.finish(errs, NAME)
    if "--no-render" in args:
        return
    qa(parts, args)


main()
