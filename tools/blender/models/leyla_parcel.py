"""leyla_parcel.glb — Leyla's parcel, addressed to Laboratory 7 (Chapter 4, group H; secret S1, locker 17 -> the post station).

A parcel wrapped in brown kraft paper, 0.20 x 0.12 x 0.08 m: soft rounded corners, an overlapping paper seam along the top, the envelope folds on both ends, tied with cream twine in two
loops that cross in a bow knot on the top (two loops and two tails), and a cream tag hanging on a short string from the knot, lying on the top face with the Chapter 2 laboratory flask
and the number 7 in ink (the address of the post dial: the flask and the number wheel's 7). No words. Lies flat on its large face (Blender +Z up = Godot +Y); the long side along X.
Origin at the centre of mass. Slots: M_Cardboard (paper), M_Paper (twine and tag), M_Bakelite (ink): three (the documented exception of "<= 2 materials"; 3 surfaces).
    blender -b --factory-startup -P tools/blender/models/leyla_parcel.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402
import lib_ch4_items as H  # noqa: E402  (sets the QA output folder to qa/blender/ch4)
import lib_ch4_fgh as F  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "leyla_parcel"
KRAFT, TWINE, INK = "M_Cardboard", "M_Paper", "M_Bakelite"
LX, LY, LZ = 0.20, 0.12, 0.08
KNOT = (0.004, 0.0)


def prism_yz(bm, pts_zy, x0, x1):
    F.prism_yz(bm, pts_zy, x0, x1)


def kraft():
    parts = []
    body = M.box("parcel", (LX, LY, LZ), loc=(0.0, 0.0, LZ / 2.0), mat=KRAFT, bevel=0.0065, segments=2)
    parts.append(body)
    # the overlapping seam along the top: a slightly turned strip with a folded edge
    seam = [(-0.0985, -0.016), (0.0985, -0.0185), (0.0985, 0.0245), (-0.0985, 0.0270)]
    parts.append(G.plate_xy("seam", [seam], 0.0012, LZ, KRAFT, bevel=0.0003))
    # the envelope folds on both ends: two side triangles and a bottom trapezoid, stacked 0.8 mm apart
    bm = bmesh.new()
    for sx in (-1, 1):
        base = sx * LX / 2.0
        step = 0.0008 * sx
        prism_yz(bm, [(0.006, -0.0545), (0.074, -0.0545), (0.040, -0.002)], base, base + step)
        prism_yz(bm, [(0.006, 0.0545), (0.074, 0.0545), (0.040, 0.002)], base + step, base + 2 * step)
        prism_yz(bm, [(0.006, -0.0545), (0.006, 0.0545), (0.036, 0.016), (0.036, -0.016)], base + 2 * step, base + 3 * step)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    me = bpy.data.meshes.new("folds")
    bm.to_mesh(me)
    bm.free()
    folds = bpy.data.objects.new("folds", me)
    bpy.context.scene.collection.objects.link(folds)
    M.assign(folds, KRAFT)
    parts.append(folds)
    return parts


def rect_loop(plane, c, hx, hz, off=0.0016):
    """A closed rectangular path round the parcel in the XZ plane (y = c) or the YZ plane (x = c)."""
    z0, z1 = -off, LZ + off
    if plane == "xz":
        return [(-hx - off, c, z0), (hx + off, c, z0), (hx + off, c, z1), (-hx - off, c, z1)]
    return [(c, -hz - off, z0), (c, hz + off, z0), (c, hz + off, z1), (c, -hz - off, z1)]


def twine_parts():
    out = []
    out.append(A.tube("loop1", rect_loop("xz", KNOT[1], LX / 2.0, LY / 2.0), 0.0017, sides=6, fillet=0.012, fillet_segs=3, mat=TWINE, closed=True))
    out.append(A.tube("loop2", rect_loop("yz", KNOT[0], LX / 2.0, LY / 2.0), 0.0017, sides=6, fillet=0.010, fillet_segs=3, mat=TWINE, closed=True))
    kx, ky, kz = KNOT[0], KNOT[1], LZ + 0.0030
    # the bow: two loops (flattened tori) and a centre knot, two tails
    for sgn in (-1, 1):
        lp = M.torus(f"bowloop{sgn}", 0.0085, 0.0016, loc=(kx + sgn * 0.0100, ky + sgn * 0.0020, kz + 0.0012), major_seg=14, minor_seg=5, mat=TWINE)
        lp.scale = (1.0, 0.62, 0.55)
        lp.rotation_euler = (0.0, 0.0, math.radians(sgn * 18.0))
        M.apply_transform(lp)
        out.append(lp)
    out.append(M.sphere("knot", 0.0042, loc=(kx, ky, kz + 0.0010), segments=10, rings=6, mat=TWINE))
    out.append(A.tube("tail1", [(kx, ky, kz + 0.0006), (kx + 0.012, ky - 0.010, kz - 0.0008), (kx + 0.026, ky - 0.014, LZ + 0.0016)], 0.0014, sides=5, mat=TWINE))
    out.append(A.tube("tail2", [(kx, ky, kz + 0.0006), (kx - 0.010, ky + 0.012, kz - 0.0008), (kx - 0.019, ky + 0.027, LZ + 0.0016)], 0.0014, sides=5, mat=TWINE))
    return out


def tag_parts():
    """The tag on the top face, in the world, plus its ink; the string from the knot to the tag's hole."""
    tx, ty, tz = 0.048, -0.020, LZ + 0.0015
    ang = math.radians(-14.0)
    w, h = 0.052, 0.034
    outline = [(-w / 2, h / 2 - 0.006), (-w / 2 + 0.006, h / 2), (w / 2, h / 2), (w / 2, -h / 2), (-w / 2, -h / 2)]
    hole = list(reversed(L.circle(0.0024, 10, cx=-w / 2 + 0.0075, cy=h / 2 - 0.0075)))
    rot = Matrix.Translation((tx, ty, tz)) @ Matrix.Rotation(ang, 4, "Z")
    tag = G.plate_xy("tag", [outline, hole], 0.0014, 0.0, TWINE, bevel=0.0002)
    tag.data.transform(rot)
    # a ring of string through the hole, back to the knot
    hx, hy, _hz = rot @ Vector((-w / 2 + 0.0075, h / 2 - 0.0075, 0.0007))
    kx, ky, kz = KNOT[0], KNOT[1], LZ + 0.0030
    string = A.tube("tagstring", [(kx, ky, kz), (kx + 0.012, ky - 0.006, LZ + 0.0016), (hx, hy, tz + 0.0010)], 0.0010, sides=5, mat=TWINE)
    ink = []
    flask = L.flat_shape("flask", F.picto_loops("flask", 0.0215), mat=INK)
    flask.data.transform(rot @ Matrix.Translation((-0.0105, -0.0020, 0.0014 + 0.0003)))
    ink.append(flask)
    seven = D.hand("seven", "7", 0.0230, ratio=0.8, mat=INK)
    seven.data.transform(rot @ Matrix.Translation((0.0115, -0.0020, 0.0014 + 0.0003)))
    ink.append(seven)
    rule = L.flat_shape("rule", [[(-0.0220, -0.0120), (0.0220, -0.0118), (0.0220, -0.0128), (-0.0220, -0.0130)]], mat=INK)
    rule.data.transform(rot @ Matrix.Translation((0.0, 0.0, 0.0014 + 0.0003)))
    ink.append(rule)
    return [tag, string], ink


def build():
    kr = kraft()
    root = M.join(kr, NAME)
    tw = twine_parts()
    tg, ink = tag_parts()
    twine = M.join(tw + tg, "twine")
    inkobj = M.join(ink, "ink")
    M.set_parent(twine, root)
    M.set_parent(inkobj, root)
    return root


def main():
    G.item_main(NAME, build, post=lambda: D.resmooth(bpy.data.objects[NAME], 38.0), required=("twine", "ink"), budget=2600, surf_budget=3, mat_budget=3, shots=[
        ("", (0.16, -0.22, 0.20), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.34), (0.0, -0.002, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
