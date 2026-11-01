"""pipe_run.glb — the wall pipe network of the Pump Room (puzzle N2 "Pipe routing", mallet tapping).

Chapter 2 expansion, docs/CHAPTER2_EXPANSION.md §8 N2. A superset board: 7 nodes and 9 candidate pipe segments laid out on an
enamel-black wall board 3.00 x 1.80 m. Every variant graph (`v_pipes`, 6 verified graphs) is drawn by SHOWING a subset of the
segments (hide the others). Each segment is a tappable `IA_pipe_<a><b>` (copper pipe with brass unions, wall clips); the
mallet taps it and the code plays the pitch. Every segment carries a child `glow_<a><b>` (emissive warm bands over the pipe)
that the code lights when the flow reaches it.

Nodes (junction boxes, static), letters in the part names:
  s  SOURCE   compressor stub, pictogram: circle with arrow            (-1.30, 0.90)
  a          (-0.45, 1.40)      b (-0.45, 0.40)
  c          ( 0.40, 1.40)      d ( 0.40, 0.40)
  t  TARGET   Cold Store coil, pictogram: zig-zag coil                 ( 1.25, 1.40)
  h  HAZARD   vent to the hall, pictogram: louvres, with a warning lamp ( 1.25, 0.40)
Segments (9): sa sb ab ac bd cd ct dh th   (x, y are model coordinates; the pipe axis is at z = 0.10)

Model space (Godot): front +Z, origin on the wall plane at floor level, x = 0 board centre.
Placement suggestion: west wall of the Pump Room at (-3.5, 0, 1.05), yaw +90.

Parts:
  pipe_board    board, node boxes with pictograms, stubs to the walls (static)
  IA_pipe_<ab>  each segment, origin at the segment midpoint, identity rotation; child glow_<ab> (same origin)
  hazard_lamp_h red caged lamp at node h (M_Emissive_Red), origin at its centre (1.25, 0.60, 0.10)
  target_lamp_t warm lamp at node t (M_Emissive_Warm), origin (1.25, 1.60, 0.10)
    blender -b --factory-startup -P tools/blender/models/pipe_run.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, glathe, part  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "pipe_run"
BUDGET = 11000
ARGS = M.main_guard()
ZP = 0.10
NODES = {"s": (-1.30, 0.90), "a": (-0.45, 1.40), "b": (-0.45, 0.40), "c": (0.40, 1.40), "d": (0.40, 0.40),
         "t": (1.25, 1.40), "h": (1.25, 0.40)}
EDGES = ["sa", "sb", "ab", "ac", "bd", "cd", "ct", "dh", "th"]
NODE_HALF = 0.095
PR = 0.028


JUNCTION = {"sa": (-1.30, 1.40), "sb": (-1.30, 0.40)}      # the source bus (static) feeds both pipes through these boxes
JUNC_HALF = 0.06


def pipe_between(n0, n1, name):
    if name in JUNCTION:
        a, b = Vector(JUNCTION[name] + (0,)), Vector(NODES[n1] + (0,))
        d = (b - a).normalized()
        return tuple(a + d * JUNC_HALF), tuple(b - d * NODE_HALF)
    a, b = Vector(NODES[n0] + (0,)), Vector(NODES[n1] + (0,))
    d = (b - a).normalized()
    p0 = a + d * NODE_HALF
    p1 = b - d * NODE_HALF
    return (p0.x, p0.y, ZP), (p1.x, p1.y, ZP)


def pictogram(node, c):
    """Raised brass pictogram on the front of a node box (language neutral)."""
    x, y = c
    z = 0.075
    o = []
    if node == "s":                    # circle with an arrow
        o.append(M.torus("pic_ring", 0.045, 0.006, loc=G(x, y, z), rot=(math.pi / 2, 0, 0), major_seg=16, minor_seg=4,
                         mat="M_Brass_Polished"))
        o.append(gbox("pic_arrow", (x - 0.03, y - 0.005, z - 0.004), (x + 0.03, y + 0.005, z + 0.004), "M_Brass_Polished"))
        o.append(X.gpoly("pic_head", [(0.0, 0.015), (0.0, -0.015), (0.025, 0.0)], 0.008, A.frame_matrix(G(x + 0.03, y, z - 0.004),
                         Vector((0, 0, 1)) * 0 + G(1, 0, 0), G(0, 1, 0), Vector((0, 0, 0)) + G(0, 0, 1)) if False else X.C.gframe((x + 0.03, y, z - 0.004), (1, 0, 0), (0, 1, 0)),
                         mat="M_Brass_Polished", bevel=0.0))
    elif node == "t":                  # coil: zig-zag
        pts = [(x - 0.05, y - 0.03), (x - 0.03, y + 0.03), (x - 0.01, y - 0.03), (x + 0.01, y + 0.03), (x + 0.03, y - 0.03),
               (x + 0.05, y + 0.03)]
        o.append(X.gtube("pic_zig", [(p[0], p[1], z) for p in pts], 0.0045, sides=5, mat="M_Brass_Polished", caps=True))
    elif node == "h":                  # louvres
        for i in range(4):
            o.append(gbox(f"pic_l{i}", (x - 0.045, y - 0.04 + i * 0.027, z - 0.004), (x + 0.045, y - 0.03 + i * 0.027, z + 0.004),
                          "M_Brass_Polished"))
    return o


def build():
    X.begin()
    board = []
    board.append(gbox("backboard", (-1.50, 0.0, 0.0), (1.50, 1.80, 0.040), "M_Paint_Black", bevel=0.006, seg=2))
    board.append(gbox("frame_t", (-1.52, 1.78, 0.0), (1.52, 1.84, 0.055), "M_Iron_Rust", bevel=0.004))
    board.append(gbox("frame_b", (-1.52, -0.04, 0.0), (1.52, 0.02, 0.055), "M_Iron_Rust", bevel=0.004))
    board.append(gbox("frame_l", (-1.54, -0.04, 0.0), (-1.48, 1.84, 0.055), "M_Iron_Rust", bevel=0.004))
    board.append(gbox("frame_r", (1.48, -0.04, 0.0), (1.54, 1.84, 0.055), "M_Iron_Rust", bevel=0.004))
    # painted guide lines of the superset behind the pipes (so hidden segments leave a faint ghost)
    for e in EDGES:
        p0, p1 = pipe_between(e[0], e[1], e)
        a, b = Vector(p0), Vector(p1)
        w = 0.012
        mn = (min(a.x, b.x) - w, min(a.y, b.y) - w, 0.040)
        mx = (max(a.x, b.x) + w, max(a.y, b.y) + w, 0.043)
        board.append(gbox("ghost" + e, mn, mx, "M_Enamel_Cream", bevel=0.0))
    # node boxes
    for n, (x, y) in NODES.items():
        board.append(gbox("node" + n, (x - NODE_HALF, y - NODE_HALF, 0.040), (x + NODE_HALF, y + NODE_HALF, 0.090), "M_Iron_Rust",
                          bevel=0.007, seg=2))
        board.append(gbox("nodeplate" + n, (x - NODE_HALF + 0.015, y - NODE_HALF + 0.015, 0.090),
                          (x + NODE_HALF - 0.015, y + NODE_HALF - 0.015, 0.098), "M_Steel_Dark", bevel=0.002))
        board += pictogram(n, (x, y)) if n in "sth" else []
        for sx in (-1, 1):
            for sy in (-1, 1):
                board.append(gcyl(f"nb{n}{sx}{sy}", 0.008, 0.008, (x + sx * 0.075, y + sy * 0.075, 0.098), axis="z", verts=6,
                                  mat="M_Brass_Aged", bevel=0.0))
    board.append(gbox("bus_box_a", (-1.30 - JUNC_HALF, 1.40 - JUNC_HALF, 0.040), (-1.30 + JUNC_HALF, 1.40 + JUNC_HALF, 0.085), "M_Iron_Rust", bevel=0.006))
    board.append(gbox("bus_box_b", (-1.30 - JUNC_HALF, 0.40 - JUNC_HALF, 0.040), (-1.30 + JUNC_HALF, 0.40 + JUNC_HALF, 0.085), "M_Iron_Rust", bevel=0.006))
    board.append(X.pipe("bus", [(-1.30, 0.40 + JUNC_HALF, ZP - 0.012), (-1.30, 1.40 - JUNC_HALF, ZP - 0.012)], 0.032,
                        mat="M_Steel_Painted", flange_ends=False))
    # stubs: source from the left edge, coil to the top right, vent to the bottom right
    board.append(X.pipe("stub_s", [(-1.50, 0.90, ZP - 0.012), (-1.30 - NODE_HALF, 0.90, ZP - 0.012)], 0.036, mat="M_Steel_Painted", flange_r=0.055))
    board.append(X.pipe("stub_t", [(1.25 + NODE_HALF, 1.40, ZP), (1.50, 1.40, ZP)], PR, mat="M_Copper", flange_r=0.045))
    board.append(X.pipe("stub_h", [(1.25, 0.40 - NODE_HALF, ZP), (1.25, 0.05, ZP)], 0.034, mat="M_Steel_Dark", flange_r=0.05))
    # source gauge to the left of s and a second one: pressure indication (static look)
    gb, nd = X.gauge("src_gauge", (-1.30, 1.62, 0.060), r=0.07, axis="z")
    board.append(gb)
    nd.name = "needle_src"
    # lamps on stands
    hz = part("hazard_lamp_h", [M.sphere("hz", 0.030, loc=G(1.25, 0.60, ZP), segments=12, rings=6, mat="M_Emissive_Red")],
              (1.25, 0.60, ZP), presmooth=False)
    tg = part("target_lamp_t", [M.sphere("tg", 0.030, loc=G(1.25, 1.60, ZP), segments=12, rings=6, mat="M_Emissive_Warm")],
              (1.25, 1.60, ZP), presmooth=False)
    for nm, y in (("h", 0.60), ("t", 1.60)):
        board.append(gcyl(f"lstem{nm}", 0.012, y - 0.40 - NODE_HALF + 0.03 if nm == "h" else y - 1.40 - NODE_HALF + 0.03,
                          (1.25, (0.40 + NODE_HALF) if nm == "h" else (1.40 + NODE_HALF), ZP), axis="y", verts=8,
                          mat="M_Brass_Aged", bevel=0.0))
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            board.append(gcyl(f"lc{nm}{i}", 0.003, 0.07, (1.25 + math.cos(a) * 0.036, y + math.sin(a) * 0.036 - 0.035, ZP + 0.0)
                              if False else (1.25 + math.cos(a) * 0.036, y - 0.035, ZP + math.sin(a) * 0.036), axis="y", verts=4,
                              mat="M_Steel_Dark", bevel=0.0))
    # wall clips and the segments
    segs = []
    for e in EDGES:
        p0, p1 = pipe_between(e[0], e[1], e)
        a, b = Vector(p0), Vector(p1)
        mid = (a + b) / 2
        objs = [X.pipe(f"seg{e}", [p0, p1], PR, mat="M_Copper", flange_ends=True, flange_r=0.046, flange_t=0.012,
                       flange_mat="M_Brass_Aged", bolts=4, sides=10)]
        # clip band at the midpoint
        d = (b - a).normalized()
        ax = "x" if abs(d.x) > abs(d.y) else "y"
        objs.append(gcyl(f"clip{e}", PR + 0.007, 0.03, (mid.x - (0.015 if ax == "x" else 0), mid.y - (0.015 if ax == "y" else 0), mid.z),
                         axis=ax, verts=12, mat="M_Steel_Dark", bevel=0.0))
        objs.append(gbox(f"clipfoot{e}", (mid.x - 0.016, mid.y - 0.016, 0.043), (mid.x + 0.016, mid.y + 0.016, ZP - PR),
                         "M_Steel_Dark", bevel=0.0))
        ia = part(f"IA_pipe_{e}", objs, (mid.x, mid.y, ZP))
        # glow bands (emissive rings every 0.09 m along the pipe)
        L = (b - a).length
        n = max(2, int(L / 0.10))
        bands = []
        for i in range(n):
            t = (i + 0.5) / n
            c = a + (b - a) * t
            bands.append(gcyl(f"gb{e}{i}", PR + 0.003, 0.018, (c.x - (0.009 if ax == "x" else 0), c.y - (0.009 if ax == "y" else 0), c.z),
                              axis=ax, verts=12, mat="M_Emissive_Warm", bevel=0.0))
        gl = part(f"glow_{e}", bands, (mid.x, mid.y, ZP), presmooth=False)
        gl.parent = ia
        gl.matrix_parent_inverse = ia.matrix_world.inverted()
        segs.append(ia)
    X.top(board)
    part("pipe_board", board, (0, 0, 0))
    return segs


def main():
    segs = build()
    req = ["pipe_board", "hazard_lamp_h", "target_lamp_t", "needle_src"] + [f"IA_pipe_{e}" for e in EDGES] + [f"glow_{e}" for e in EDGES]
    expect = {}
    for e in EDGES:
        p0, p1 = pipe_between(e[0], e[1], e)
        expect[f"IA_pipe_{e}"] = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, ZP)
    errs = X.finish(NAME, req, req[1:], BUDGET, expect, show=req[:6])
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.0, 1.0, 3.6), (0.0, 0.95, 0.0), 50), ("_2", (0.7, 0.95, 1.4), (0.8, 0.95, 0.0), 45)],
                   floor=False, world=0.18)


main()
