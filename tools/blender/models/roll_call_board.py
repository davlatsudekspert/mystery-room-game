"""roll_call_board.glb — the staff roll-call board of the Reading Gallery (R5, puzzle N8; "a closed library on a Sunday").

NOT the Chapter 4 `roll_board.glb` (that one is the Watch Room's 42-hook board); this is the Gallery's own six-hook board.
A dark-oak frame with a green baize field, a brass header plate with six pips, six brass hooks (an upturned tip, a pin plate and
that hook's number as 1..6 brass pips under it), six cream portrait tags hanging on them, and a clue-slip rail: six brass clips
along the baize below (the clue slips are drawn by code onto quads placed at `slip_mount_k`).

Model space (Godot): origin on the floor under the board centre, the board hangs on the wall behind it (back at z = 0), the face
looks +Z. Board 2.50 w x 1.36 h (x +-1.25, y 0.90 .. 2.26). Wall placements: north wall as is; west wall: yaw +90.
Parts (origin at the pivot, identity rotation at rest):
  roll_board_body   frame, baize, header, hooks, pips, slip rail
  IA_tag_0..5       portrait tags. Pivot = the hole centre of the tag as it hangs on hook k at rest (tag k on hook k):
                    (-1.00 + 0.40 k, 1.85, 0.056). Moving a tag to hook j = translate by ((j - k) * 0.40, 0, 0). Tag 0.30 x 0.225 x 0.012.
                    The portrait is a quad on the tag with slot M_Decal_RollTags (3 x 2 atlas, cell k = tag k at rest, UV set per tag)
  empties           hook_0..5 (-1.00 + 0.40 k, 1.85, 0.056), slip_mount_0..5 (-1.00 + 0.40 k, 1.30, 0.034) (slip centre, 0.30 x 0.20),
                    light_origin_board (0, 2.1, 0.9)
    blender -b --factory-startup -P tools/blender/models/roll_call_board.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_upper as U  # noqa: E402
from lib_ch2x import G, gbox, gcyl, glathe, gquad, gpoly, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "roll_call_board"
BUDGET = 5000
ARGS = M.main_guard()
OAK, BRASS = "M_Wood_Mahogany", "M_Brass_Aged"
BW, BY0, BY1 = 2.50, 0.90, 2.26
HY = 1.85                       # hook height
XK = [-1.0 + 0.4 * k for k in range(6)]


def tag_outline(w, h, r, seg=4):
    return A.rounded_rect(w, h, r, seg)


def build():
    X.begin()
    b = []
    # frame: oak, with a rounded outer moulding; baize field
    b.append(gbox("frame_l", (-BW / 2, BY0, 0.0), (-BW / 2 + 0.10, BY1, 0.045), OAK, bevel=0.01, seg=2))
    b.append(gbox("frame_r", (BW / 2 - 0.10, BY0, 0.0), (BW / 2, BY1, 0.045), OAK, bevel=0.01, seg=2))
    b.append(gbox("frame_b", (-BW / 2, BY0, 0.0), (BW / 2, BY0 + 0.10, 0.045), OAK, bevel=0.01, seg=2))
    b.append(gbox("frame_t", (-BW / 2, BY1 - 0.10, 0.0), (BW / 2, BY1, 0.045), OAK, bevel=0.01, seg=2))
    b.append(gbox("baize", (-BW / 2 + 0.10, BY0 + 0.10, 0.0), (BW / 2 - 0.10, BY1 - 0.10, 0.018), "M_Felt", bevel=0.0))
    b.append(gbox("inner_bead", (-BW / 2 + 0.10, BY0 + 0.10, 0.018), (BW / 2 - 0.10, BY1 - 0.10, 0.026), BRASS, bevel=0.0))
    b.append(gbox("baize2", (-BW / 2 + 0.115, BY0 + 0.115, 0.018), (BW / 2 - 0.115, BY1 - 0.115, 0.027), "M_Felt", bevel=0.0))
    # pediment with the header plate and six pips (the six hooks)
    b.append(gbox("ped", (-0.75, BY1, 0.0), (0.75, BY1 + 0.11, 0.05), OAK, bevel=0.012, seg=2))
    b.append(gbox("ped_cap", (-0.80, BY1 + 0.11, 0.0), (0.80, BY1 + 0.15, 0.06), OAK, bevel=0.01))
    b.append(gbox("header", (-0.52, BY1 + 0.025, 0.05), (0.52, BY1 + 0.095, 0.058), BRASS, bevel=0.003))
    for k in range(6):
        b.append(gcyl(f"hpip{k}", 0.012, 0.004, (-0.40 + 0.16 * k, BY1 + 0.06, 0.058), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    # hooks: pin plate + pin + upturned tip + numbered pips under each hook
    for k, x in enumerate(XK):
        b.append(gbox(f"hplate{k}", (x - 0.03, HY - 0.035, 0.026), (x + 0.03, HY + 0.035, 0.034), BRASS, bevel=0.003))
        b.append(gcyl(f"hpin{k}", 0.0065, 0.058, (x, HY, 0.030), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
        b.append(gcyl(f"htip{k}", 0.0065, 0.022, (x, HY, 0.084), axis="y", verts=8, mat="M_Brass_Polished", bevel=0.0))
        for j in range(k + 1):
            b.append(gcyl(f"num{k}_{j}", 0.0075, 0.004, (x - 0.0125 * k + 0.025 * j, HY + 0.095, 0.027), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    # a hanging rail under the hooks to catch a dropped tag + clue rail with six clips
    b.append(gbox("tag_ledge", (-1.10, 1.50, 0.028), (1.10, 1.525, 0.06), BRASS, bevel=0.003))
    b.append(gbox("slip_rail", (-1.12, 1.17, 0.027), (1.12, 1.19, 0.052), BRASS, bevel=0.002))
    for k, x in enumerate(XK):
        b.append(gbox(f"clip{k}", (x - 0.03, 1.40, 0.028), (x + 0.03, 1.425, 0.044), BRASS, bevel=0.002))
        b.append(gcyl(f"clip_pin{k}", 0.006, 0.016, (x, 1.41, 0.028), axis="z", verts=6, mat="M_Brass_Polished", bevel=0.0))
        b.append(gbox(f"slot{k}", (x - 0.155, 1.185, 0.027), (x + 0.155, 1.195, 0.034), "M_Lacquer_Black", bevel=0.0))
    # brass corner studs and bottom shelf for a lamp
    for sx in (-1, 1):
        for sy in (BY0 + 0.05, BY1 - 0.05):
            b.append(gcyl(f"stud{sx}{sy}", 0.014, 0.012, (sx * (BW / 2 - 0.05), sy, 0.045), axis="z", verts=8, mat="M_Brass_Polished", bevel=0.0))
    b.append(gbox("shelf", (-0.95, 0.88, 0.0), (0.95, 0.92, 0.20), OAK, bevel=0.006))
    for sx in (-1, 1):
        b.append(gbox(f"bracket{sx}", (sx * 0.85 - 0.015, 0.74, 0.0), (sx * 0.85 + 0.015, 0.88, 0.16), OAK, bevel=0.004))
    X.top(b, 4)
    body = part("roll_call_board_body", b, (0, 0, 0))

    # six tags: rounded card with a brass eyelet, portrait quad from the atlas
    tags = []
    for k, x in enumerate(XK):
        w, h = 0.30, 0.225
        mtx = X.C.gframe((x, HY - 0.012 - h / 2, 0.050), (1, 0, 0), (0, 1, 0))
        o = [gpoly(f"card{k}", tag_outline(w, h, 0.03), 0.012, mtx, mat="M_Enamel_Cream", bevel=0.0012)]
        o.append(gcyl(f"eye{k}", 0.014, 0.014, (x, HY, 0.049), axis="z", verts=12, mat=BRASS, bevel=0.0))
        row, col = divmod(k, 3)
        u0, u1 = col / 3.0, (col + 1) / 3.0
        v0, v1 = 1.0 - (row + 1) / 2.0, 1.0 - row / 2.0
        X.decal("M_Decal_RollTags", "roll_tags.png")
        q = gquad(f"photo{k}", (x, HY - 0.012 - h / 2 - 0.004, 0.0625), (1, 0, 0), (0, 1, 0), w - 0.02, h - 0.045, "M_Decal_RollTags",
                  uv=(u0, v0, u1, v1))
        o.append(q)
        tags.append(part(f"IA_tag_{k}", o, (x, HY, 0.056)))
    for k, x in enumerate(XK):
        mount(f"hook_{k}", (x, HY, 0.056))
        mount(f"slip_mount_{k}", (x, 1.30, 0.034))
    mount("light_origin_board", (0.0, 2.1, 0.9))
    return body, tags


if __name__ == "__main__":
    build()
    req = ["roll_call_board_body"] + [f"IA_tag_{k}" for k in range(6)] + [f"hook_{k}" for k in range(6)] + [f"slip_mount_{k}" for k in range(6)] + ["light_origin_board"]
    exp = {f"IA_tag_{k}": (XK[k], HY, 0.056) for k in range(6)}
    errs = X.finish(NAME, req, [f"IA_tag_{k}" for k in range(6)], BUDGET, exp, show=["roll_call_board_body", "IA_tag_0"])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 1.7, 2.9), (0.0, 1.55, 0.0), 40), ("_close", (-0.4, 1.8, 1.0), (-0.4, 1.7, 0.0), 40)], floor=False, world=0.25)
