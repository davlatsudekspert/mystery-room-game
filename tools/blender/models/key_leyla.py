"""key_leyla.glb — Leyla's key (vault key cradle, right hook): opens the crystal-growth vaults (Ch3 route).

A slender 110 mm key of dark blued steel (M_Steel_Dark): an oval bow (27 x 32 mm, 3 mm plate, rounded
edges) pierced right through with **Leyla's sign** — a crescent opening to the right with three dots in
a vertical row inside its opening (proportions taken from glyph_sign.png, sign height 20.5 mm) — a turned
collar, a thin round shank (Ø 4.5 mm) with a domed tip and a small flag bit with one ward and a
chamfered corner.
A small hanging eye (Ø 7.2 mm, hole Ø 3.4 mm) crowns the bow, as on Strand's key, for the vault cradle hook.
Lies flat (broad faces Godot +-Y, hero face up), the bow toward Godot -Z (the top in the inspect view),
the bit toward +Z sticking out to +X. Origin at the centre of mass.
    blender -b --factory-startup -P tools/blender/models/key_leyla.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402

NAME = "key_leyla"
MAT = "M_Steel_Dark"
T = 0.0030            # bow plate
BY = 0.0234           # bow centre (Blender y; +Y = Godot -Z)
RX, RY = 0.0135, 0.0160
EYE_Y, EYE_R, EYE_HOLE = BY + RY + 0.0020, 0.0036, 0.0017     # hanging eye on top of the bow
TOP = EYE_Y + EYE_R                                           # eye top; the tip is at TOP - 0.110
SIGN_H = 0.0205       # crescent height (glyph_sign.png: 410 px of 512)
PX = SIGN_H / 410.0   # metres per glyph pixel


def gp(px, py):
    """glyph_sign.png pixel -> bow coordinates (image y down, centre 256)."""
    return ((px - 256.0) * PX, BY + (256.0 - py) * PX)


def crescent(min_w=0.0008, n_out=26, n_in=20):
    """Crescent hole opening to the right: outer circle minus an inner circle shifted right; the cusps
    are cut where the crescent gets thinner than min_w (a pierced cusp would close up)."""
    c1x, c1y = gp(293.0, 255.5)
    r1 = 205.0 * PX
    c2x, c2y = gp(337.5, 255.5)
    r2 = 179.5 * PX
    # outer arc angle where the crescent width (radial gap between the circles) falls to min_w
    lo, hi = math.pi / 2 * 0.2, math.pi       # search the upper half
    a_cut = None
    for i in range(400):
        a = lo + (hi - lo) * i / 399
        px, py = c1x + r1 * math.cos(a), c1y + r1 * math.sin(a)
        if math.hypot(px - c2x, py - c2y) - r2 > min_w:
            a_cut = a
            break
    pts = []
    for i in range(n_out):                         # outer arc, top -> left -> bottom (CCW)
        a = a_cut + (2 * math.pi - 2 * a_cut) * i / (n_out - 1)
        pts.append((c1x + r1 * math.cos(a), c1y + r1 * math.sin(a)))
    # inner arc back, bottom -> left -> top, between the matching points on the inner circle
    bx, by = pts[-1]
    tx, ty = pts[0]
    b0 = math.atan2(by - c2y, bx - c2x) % (2 * math.pi)      # ~310 deg: below the opening
    b1 = math.atan2(ty - c2y, tx - c2x) % (2 * math.pi)      # ~50 deg: decreasing through 180 deg
    for i in range(n_in):
        a = b0 + (b1 - b0) * i / (n_in - 1)
        pts.append((c2x + r2 * math.cos(a), c2y + r2 * math.sin(a)))
    return pts


def dots():
    out = []
    for py in (171.5, 255.5, 339.5):
        cx, cy = gp(315.5, py)
        out.append(L.circle(22.0 * PX, 12, cx=cx, cy=cy))
    return out


def build():
    bow_out = [(RX * math.cos(t), BY + RY * math.sin(t)) for t in (math.tau * i / 48 for i in range(48))]
    bow_out = C.union_circle(bow_out, 0.0, EYE_Y, EYE_R, n=12)
    eye = L.circle(EYE_HOLE, 10, cx=0.0, cy=EYE_Y)
    bow = L.curve_solid(NAME, [bow_out, eye, crescent()] + dots(), T, bevel=0.0005, bevel_res=1, mat=MAT)
    bow.location = (0, 0, -T / 2)
    M.apply_transform(bow)
    # turned collar + slender shank with a domed tip (from inside the bow down to the tip at y = -0.065)
    y_top = BY - RY + 0.0015
    tip = y_top - (TOP - 0.110)
    prof = [(0.0030, 0.0), (0.0036, 0.0016), (0.0036, 0.0030), (0.0027, 0.0042), (0.0033, 0.0056),
            (0.0033, 0.0068), (0.00225, 0.0080), (0.00225, tip - 0.0018), (0.0017, tip - 0.0006), (0.0, tip)]
    shank = C.key_shank("shank", prof, y_top, MAT, segments=12)
    # small flag bit with two wards (toward +X)
    yt = TOP - 0.110
    y0, y1, xr, xo = yt + 0.0050, yt + 0.0205, 0.0015, 0.0120
    bit_pts = [(xr, y0), (xo, y0), (xo, y0 + 0.0040), (xo - 0.0042, y0 + 0.0040), (xo - 0.0042, y0 + 0.0068),
               (xo, y0 + 0.0068), (xo, y1 - 0.0030), (xo - 0.0025, y1), (xr, y1)]
    bit = L.curve_solid("bit", [bit_pts], 0.0025, bevel=0.0003, bevel_res=0, mat=MAT)
    bit.location = (0, 0, -0.00125)
    M.apply_transform(bit)
    rest = M.join([shank, bit], "key_shaft")
    M.set_parent(rest, bow)
    return [bow]


def main():
    C.item_main(NAME, build, shots=[
        ("", (0.05, -0.12, 0.14), (0.0, 0.004, 0.0), 50),
        ("_2", C.inspect_cam(0.24), (0.0, -0.008, 0.0), 50),
    ])


if __name__ == "__main__":
    main()
