"""key_strand.glb — Strand's key (vault key cradle, left hook): opens the Array Hall (Ch3 route).

A large ornate 140 mm key of aged brass. The round bow (Ø 43 mm over its eight scallops, 4 mm plate,
rounded edges) is open: inside its frame stands **Strand's mark** as openwork — a ring (Ø 14 / 19.6 mm)
crossed by a vertical meridian bar (2.1 mm) that runs from the top of the frame to the bottom; the four
openings around them are pierced right through. The worn high points of the mark are polished
(M_Brass_Polished). A hanging eye (Ø 9.6 mm, hole Ø 4.4 mm) crowns the bow; an engraved line follows
the frame. Below: a turned collar of beads, a round shank (Ø 7.2 mm) with a mid ring and a domed tip,
and a stepped bit with three wards.
Lies flat (broad faces Godot +-Y, hero face up), the bow toward Godot -Z (the top in the inspect view),
the bit toward +Z sticking out to +X. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/key_strand.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "key_strand"
MAT = "M_Brass_Aged"
T = 0.0040            # bow plate
BY = 0.0405           # bow centre (Blender y; +Y = Godot -Z)
R0, RA = 0.0203, 0.0012          # scallop radius and amplitude (8 lobes)
RO = 0.0160                      # frame opening
RING_IN, RING_OUT = 0.0070, 0.0098
BAR = 0.0021
EYE_Y, EYE_R, EYE_HOLE = BY + 0.0250, 0.0048, 0.0022
TOP = EYE_Y + EYE_R              # eye top (Blender y); the tip is at TOP - 0.140


def openings():
    """The four pierced openings around the mark (left/right outside the ring, left/right inside it)."""
    h = BAR / 2
    loops = []
    for sx in (-1, 1):
        # outside the ring: frame arc, down the bar, ring outer arc back up, up the bar
        t0 = math.asin(h / RO)
        u0 = math.asin(h / RING_OUT)
        pts = []
        n = 16
        for i in range(n):
            a = (math.pi / 2 + t0) + (math.pi - 2 * t0) * i / (n - 1)          # 90 -> 270 deg on the left
            pts.append((RO * math.cos(a), BY + RO * math.sin(a)))
        for i in range(n - 6):
            a = (3 * math.pi / 2 - u0) - (math.pi - 2 * u0) * i / (n - 7)        # 270 -> 90 deg on the ring
            pts.append((RING_OUT * math.cos(a), BY + RING_OUT * math.sin(a)))
        if sx > 0:
            pts = [(-x, y) for (x, y) in pts]
        loops.append(pts)
        # inside the ring: a half disc beside the bar
        w0 = math.asin(h / RING_IN)
        pts = []
        m = 9
        for i in range(m):
            a = (math.pi / 2 + w0) + (math.pi - 2 * w0) * i / (m - 1)
            pts.append((RING_IN * math.cos(a), BY + RING_IN * math.sin(a)))
        if sx > 0:
            pts = [(-x, y) for (x, y) in pts]
        loops.append(pts)
    return loops


def bow_outline():
    pts = []
    n = 64
    for i in range(n):
        t = math.tau * i / n
        r = R0 + RA * math.cos(8 * t)
        pts.append((r * math.cos(t), BY + r * math.sin(t)))
    return C.union_circle(pts, 0.0, EYE_Y, EYE_R, n=14)


def build():
    loops = [bow_outline(), L.circle(EYE_HOLE, 10, cx=0.0, cy=EYE_Y)] + openings()
    bow = L.curve_solid(NAME, loops, T, bevel=0.0007, bevel_res=0, mat=MAT)
    bow.location = (0, 0, -T / 2)
    M.apply_transform(bow)
    # polish the worn top faces of the mark (ring + meridian bar), both sides
    pol = M.add_slot(bow, "M_Brass_Polished")
    for p in bow.data.polygons:
        c = p.center
        r = math.hypot(c.x, c.y - BY)
        on_ring = RING_IN - 0.0004 < r < RING_OUT + 0.0004
        on_bar = abs(c.x) < BAR / 2 + 0.0004 and r < RO
        if abs(p.normal.z) > 0.6 and (on_ring or on_bar):
            p.material_index = pol
    # engraved line along the frame (front face)
    line = L.flat_shape("engrave", L.circle_line((RO + R0 - RA) / 2 + 0.0002, 0.00045, n=40, cy=BY),
                        mat="M_Bakelite", loc=(0, 0, T / 2 + 0.00004))
    M.apply_transform(line)
    # turned collar (beads) + shank with a mid ring + domed tip
    y_top = BY - R0 + 0.0020
    tip = y_top - (TOP - 0.140)
    prof = [(0.0034, 0.0), (0.0047, 0.0012), (0.0054, 0.0028), (0.0047, 0.0044), (0.0040, 0.0053),
            (0.0049, 0.0064), (0.0049, 0.0078), (0.0040, 0.0088), (0.0036, 0.0100),
            (0.0036, 0.0440), (0.0042, 0.0452), (0.0042, 0.0480), (0.0036, 0.0492),
            (0.0036, tip - 0.0022), (0.0027, tip - 0.0008), (0.0, tip)]
    shank = C.key_shank("shank", prof, y_top, MAT, segments=14)
    # stepped bit with three wards (toward +X)
    yt = TOP - 0.140
    y0, y1, xr, xo = yt + 0.0045, yt + 0.0240, 0.0025, 0.0190
    bit_pts = [(xr, y0), (xo, y0), (xo, y0 + 0.0030), (xo - 0.0060, y0 + 0.0030), (xo - 0.0060, y0 + 0.0056),
               (xo, y0 + 0.0056), (xo, y0 + 0.0102), (xo - 0.0095, y0 + 0.0102), (xo - 0.0095, y0 + 0.0128),
               (xo, y0 + 0.0128), (xo, y1 - 0.0040), (xo - 0.0045, y1 - 0.0040), (xo - 0.0045, y1), (xr, y1)]
    bit = L.curve_solid("bit", [bit_pts], 0.0042, bevel=0.0004, bevel_res=0, mat=MAT)
    bit.location = (0, 0, -0.0021)
    M.apply_transform(bit)
    rest = M.join([line, shank, bit], "key_shaft")
    M.set_parent(rest, bow)
    return [bow]


def main():
    C.item_main(NAME, build, shots=[
        ("", (0.06, -0.15, 0.17), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.30), (0.0, -0.004, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
