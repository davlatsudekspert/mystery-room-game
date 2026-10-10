"""MYSTERY ROOM — Chapter 4 inventory items (group H): helpers on top of lib_ch3_items / lib_ch2_items (never edits them).
Contract: docs/models/ch4.md section 9; results: docs/models/ch4_h.md.

Conventions are the item pipeline's (Blender, Z up; Godot = Blender (x, z, -y)): flat items lie in the XY plane, hero face up (Blender +Z = Godot +Y), the top edge toward Blender +Y
(Godot -Z); standing items face Blender -Y (Godot +Z). The origin is the centre of mass (the pipeline moves it). QA renders go to qa/blender/ch4/ (Cycles, <= 32 samples).

  tower_key(n)      the four tower keys: a crenellated brass bow with the Roman numeral I..IV in relief, a turned neck, a round shank and a steel bit with n-dependent code cuts
  ink_flat          zero-thickness ink shapes (M_Bakelite) on paper
"""
from __future__ import annotations

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402
import lib_ch4_numerals as N  # noqa: E402

ROOT = M.ROOT
G.QA_SUB = "ch4"
C.QA_SUB = "ch4"
TAU = 2.0 * math.pi
BRASS, BRASS_P, STEEL, PAPER, BAKE = "M_Brass_Aged", "M_Brass_Polished", "M_Steel_Dark", "M_Paper", "M_Bakelite"


# ====================================================================== tower keys
BOW_W, BOW_H = 0.036, 0.046
KEY_LEN = 0.098
SHANK_R = 0.0060
CODES = {1: "010000", 2: "010100", 3: "101010", 4: "110101"}


def _crenellated():
    hw = BOW_W / 2.0
    mer = 0.0065
    pts = [(-hw + 0.0, -BOW_H + 0.010), (-hw + 0.010, -BOW_H), (hw - 0.010, -BOW_H), (hw, -BOW_H + 0.010), (hw, 0.0), (0.0095, 0.0), (0.0095, -mer), (0.00425, -mer), (0.00425, 0.0),
           (-0.00425, 0.0), (-0.00425, -mer), (-0.0095, -mer), (-0.0095, 0.0), (-hw, 0.0)]
    return pts


def tower_key(n: int, name: str):
    bow_loop = _crenellated()
    eye = list(reversed(L.circle(0.0019, 12, cy=-0.0145)))
    bow = G.plate_xy(name, [bow_loop, eye], 0.0032, -0.0016, BRASS, bevel=0.0006)
    # the numeral plaque (a raised rounded plate) and the numeral on it
    plaque = G.plate_xy("plaque", [L.rounded_rect(0.0285, 0.0195, 0.003, 3, 0.0, -0.0318)], 0.0007, 0.0016, BRASS, bevel=0.0002)
    num = N.roman_obj("num", n, 0.0120, 0.0010, BRASS, loc=(0.0, -0.0318, 0.0023), bevel=0.0002)
    # a thin brass band between the merlons and the plaque
    band = G.plate_xy("band", [[(-0.0145, -0.0085), (0.0145, -0.0085), (0.0145, -0.0100), (-0.0145, -0.0100)]], 0.0006, 0.0016, BRASS, bevel=0.0001)
    # neck, collar, shank (turned), along -Y
    yb = -BOW_H
    tip = -KEY_LEN
    r = SHANK_R
    neck = 0.0040
    coll = 0.0032
    prof = [(0.0, -0.0030), (0.0042, -0.0030), (0.0047, 0.0), (0.0047, neck - 0.0008), (0.0062, neck), (0.0076, neck + 0.0006), (0.0076, neck + coll - 0.0006), (0.0068, neck + coll),
            (r, neck + coll + 0.0004), (r, -tip + yb - 0.0018), (r - 0.0014, -tip + yb), (0.0, -tip + yb)]
    shank = D.revolve("shank", prof, direction=(0, -1, 0), loc=(0, yb, 0), segments=14, mat=BRASS, up_hint=(0, 0, 1))
    # the bit: six slots along the last 22 mm of the shank, the code cuts of tower n
    b0, b1 = tip + 0.0022, tip + 0.0245
    xo = r + 0.0070
    code = CODES[n]
    slot = (b1 - b0) / 6.0
    pts = [(r - 0.0015, b0)]
    for k, ch in enumerate(code):
        xr = xo - (0.0034 if ch == "1" else 0.0)
        pts += [(xr, b0 + slot * k), (xr, b0 + slot * (k + 1))]
    pts += [(r - 0.0015, b1)]
    # simplify: drop collinear / duplicate points
    clean = []
    for p in pts:
        if not clean or abs(clean[-1][0] - p[0]) + abs(clean[-1][1] - p[1]) > 1e-7:
            clean.append(p)
    bit = G.plate_xy("key_bit", [clean], 0.0026, -0.0013, STEEL, bevel=0.0003)
    root = M.join([bow, plaque, num, band, shank], name)
    M.set_parent(bit, root)
    return root


def tower_key_item(n: int) -> None:
    name = f"tower_key_{n}"

    def build():
        tower_key(n, name)

    def post():
        D.resmooth(bpy.data.objects[name], 32.0)

    G.item_main(name, build, post=post, required=("key_bit",), budget=1200, shots=[
        ("", (0.07, -0.14, 0.15), (0.0, 0.0, 0.0), 50),
        ("_2", C.inspect_cam(0.20), (0.0, -0.002, 0.0), 50),
    ])
