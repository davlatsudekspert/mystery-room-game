"""locker_key.glb — the small key to staff locker 9 (returned by the pneumatic tube with Leyla's file).

A nickel-plated steel locker key (M_Chrome), 50 mm: a round bow (Ø 21 mm, 2 mm plate) with a Ø 5.6 mm
ring hole, a flat blade with four bitting cuts, a milled groove along it and a
pointed tip. A blackened steel split ring (Ø 19 mm wire ring) joins it to a round aged-brass tag
(Ø 30 mm, 1.2 mm) stamped with a big **9** (17 mm; 3D: the numeral is sunk 0.4 mm into the tag, its
floor darkened) inside a stamped border ring broken at the hole. The 9 reads upright in the inspect
view (the tag lies above the ring, the numeral's top away from the hole). Key and tag rest on the ring
wire where they cross it.
Lies flat (Godot +Y up), the tag toward Godot -Z (the top in the inspect view), the key's blade toward
+Z. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/locker_key.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "locker_key"
C.LIGHTS = C.SOFT
RING_R, WIRE = 0.0095, 0.00065       # split ring: centre-line radius, wire radius
RING_C = (0.0, 0.0)                  # ring centre (Blender xy)
KEY_A = math.radians(-96)            # where the key hangs on the ring (angle around the ring centre)
TAG_A = math.radians(80)             # where the tag hangs
KT = 0.0020                          # key plate
TT, TD = 0.0012, 0.0004              # tag plate, stamp depth
TAG_R = 0.0150
TAG_HOLE_D = 0.0118                  # tag hole centre to tag centre


def key_shape():
    """Key outline in its own frame: ring hole at the origin, the blade pointing down (-Y)."""
    bow_c, bow_r, hw = (0.0, -0.0042), 0.0105, 0.0038       # bow centre / radius, blade half width
    yb = bow_c[1] - math.sqrt(bow_r ** 2 - hw ** 2)        # shoulder line
    blade = [(hw, yb), (hw, yb - 0.0040), (0.0024, yb - 0.0062), (hw, yb - 0.0084),
             (hw, yb - 0.0108), (0.0021, yb - 0.0128), (hw, yb - 0.0150), (hw, yb - 0.0172),
             (0.0026, yb - 0.0190), (hw, yb - 0.0208), (hw, yb - 0.0262), (0.0005, yb - 0.0300),
             (-hw, yb - 0.0262), (-hw, yb)]
    # bow arc from the left shoulder (~250 deg) clockwise over the top to the right shoulder (~-70 deg)
    a_l = math.atan2(yb - bow_c[1], -hw - bow_c[0]) % math.tau
    a_r = math.atan2(yb - bow_c[1], hw - bow_c[0]) % math.tau - math.tau
    n = 36
    angles = [a_l + (a_r - a_l) * i / n for i in range(1, n)]
    arc = [(bow_c[0] + bow_r * math.cos(a), bow_c[1] + bow_r * math.sin(a)) for a in angles]
    outline = list(reversed(blade + arc))
    hole = L.circle(0.0028, 16)
    return outline, hole, yb, bow_c


def build_key():
    outline, hole, yb, bow_c = key_shape()
    key = L.curve_solid(NAME, [outline, hole], KT, bevel=0.0003, bevel_res=0, mat="M_Chrome")
    # milled groove along the blade (dark strip, front face)
    groove = L.flat_shape("groove", [L.rounded_rect(0.0012, 0.0200, 0.0005, 2, cx=-0.0012, cy=yb - 0.0125)],
                          mat="M_Steel_Dark", loc=(0, 0, KT + 0.00003))
    M.apply_transform(groove)
    return [key, groove]


def build_tag():
    """Tag in its own frame: hole at the origin, the tag body below it (-Y), the 9 upright."""
    tc = (0.0, -TAG_HOLE_D)
    disc = L.circle(TAG_R, 32, cx=tc[0], cy=tc[1])
    hole = L.circle(0.0017, 10)
    # the 9 reads upright with the tag lying above the ring (its top away from the hole)
    nine = C.text_loops("9", 0.0240, font=L.FONT_SANS_B, res=2)
    nine = C.move_loops(nine, tc[0], tc[1] - 0.0008, rot=math.pi)
    base = L.curve_solid("tag", [disc, hole], TT - TD, bevel=0.00025, bevel_res=0, mat="M_Brass_Aged")
    top = L.curve_solid("tag_top", [disc, hole] + nine, TD, bevel=0.0001, bevel_res=0, mat="M_Brass_Aged")
    top.location = (0, 0, TT - TD - 0.00002)
    M.apply_transform(top)
    floor = L.flat_shape("tag_nine", nine, mat="M_Bakelite", loc=(0, 0, TT - TD + 0.00002))
    M.apply_transform(floor)
    rb, a0, a1 = TAG_R - 0.0019, math.radians(90 + 24), math.radians(90 + 336)     # broken at the hole
    ring_line = L.arc_pts(rb + 0.00025, a0, a1, 34, cx=tc[0], cy=tc[1]) + \
        list(reversed(L.arc_pts(rb - 0.00025, a0, a1, 34, cx=tc[0], cy=tc[1])))
    border = L.flat_shape("tag_border", [ring_line], mat="M_Bakelite", loc=(0, 0, TT + 0.00003))
    M.apply_transform(border)
    return [base, top, floor, border]


def place(objs, angle, lift, tilt):
    """Hang a part (built with its hole at the origin, body toward -Y) on the ring at `angle`: its hole on
    the ring wire, its body pointing away from the ring centre, resting on the wire (lift) and tilted
    down toward its far end (tilt > 0, radians)."""
    hx = RING_C[0] + RING_R * math.cos(angle)
    hy = RING_C[1] + RING_R * math.sin(angle)
    rot = Matrix.Rotation(angle + math.pi / 2, 4, "Z")          # body (-Y) -> radially outward
    tl = Matrix.Rotation(tilt, 4, (math.cos(angle + math.pi / 2), math.sin(angle + math.pi / 2), 0.0))
    for o in objs:
        o.data.transform(Matrix.Translation((hx, hy, lift)) @ tl @ rot)


def build():
    key_parts = build_key()
    place(key_parts, KEY_A, 2 * WIRE - 0.0002, math.radians(1.6))
    tag_parts = build_tag()
    place(tag_parts, TAG_A, 2 * WIRE - 0.0002, math.radians(2.4))
    key = key_parts[0]
    ring = M.torus("split_ring", RING_R, WIRE, loc=(RING_C[0], RING_C[1], WIRE), major_seg=30, minor_seg=5,
                   mat="M_Steel_Dark")
    M.apply_transform(ring)
    # the split: a second, slightly offset turn over a quarter of the ring
    turn_pts = []
    for k in range(11):                       # the second turn rises over the first in its middle
        a = math.radians(-60 + 8 * k)
        rise = 0.0011 * 0.9 * (1 - abs(a - math.radians(-20)) / math.radians(40)) ** 0.5
        turn_pts.append((RING_C[0] + (RING_R - 0.0004) * math.cos(a), RING_C[1] + (RING_R - 0.0004) * math.sin(a),
                         WIRE + rise))
    turn = L.tube("ring_turn", turn_pts, WIRE * 0.95, mat="M_Steel_Dark", bevel_res=1, res_u=2)
    hard = M.join(key_parts[1:] + tag_parts + [ring, turn], "key_ring_tag")
    M.set_parent(hard, key)
    return [key]


def main():
    C.item_main(NAME, build, shots=[
        ("", (0.04, -0.10, 0.11), (0.0, -0.002, 0.0), 50),
        ("_2", C.inspect_cam(0.21), (0.0, -0.005, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
