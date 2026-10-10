"""beam_segment.glb — the light ribbon the code instances (up to five) along the beam's path (Chapter 4, group C).
Contract: docs/models/ch4.md section 5 beam_segment; results: docs/models/ch4_c.md.

ONE mesh object `beam_segment`, one surface (M_Emissive_Lumen), 8 tris: a unit ribbon along +Z from z = 0 to z = 1 made of two
CROSSED quads (a horizontal one and a vertical one, 0.22 wide, both crossing on the axis), each present with both faces so the
ribbon shows from every side with the default back-face culling. UV 0..1: u across the width, v along the length (the code may
swap in a soft-edged shader). Origin = the start of the ribbon. The code sets position = segment start, looks along the segment,
scales Z by its length.

    blender -b --factory-startup -P tools/blender/models/beam_segment.py [-- --no-render] [--shots=1,2,...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_ch4 as C  # noqa: E402
import lib_ch4_cde as X  # noqa: E402
from lib_ch4 import K, LUMEN  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "beam_segment"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 100, 1, 1
W = 0.22


def build():
    M.reset_scene()
    C.ensure_materials()
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    h = W / 2.0
    # (a, b) = the two across-corners of each ribbon (x, y); a ribbon is a quad from z 0 to z 1
    for (ax, ay, bx, by) in ((-h, 0.0, h, 0.0), (0.0, -h, 0.0, h)):
        for side in (0, 1):
            p0, p1 = ((ax, ay), (bx, by)) if side == 0 else ((bx, by), (ax, ay))
            v = [bm.verts.new((p0[0], p0[1], 0.0)), bm.verts.new((p1[0], p1[1], 0.0)),
                 bm.verts.new((p1[0], p1[1], 1.0)), bm.verts.new((p0[0], p0[1], 1.0))]
            f = bm.faces.new(v)
            for lp, (u_, v_) in zip(f.loops, ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))):
                lp[uv].uv = (u_, v_)
    # normals: the horizontal ribbon faces +Y (side 0) / -Y (side 1); the vertical one faces -X / +X (checked below)
    for f in bm.faces:
        f.normal_update()
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    o = K.obj_from_bm(NAME, bm, LUMEN)
    o.data.update()
    K.to_blender()
    return dict(beam=o)


def verify(path):
    errs = C.verify(path, required=[NAME], identity=[NAME], expect={NAME: (0.0, 0.0, 0.0)}, tri_budget=TRI_BUDGET,
                    surf_budget=SURF_BUDGET, mat_budget=MAT_BUDGET)
    lo, hi = C.bounds([NAME])
    print(f"{C.TAG} {NAME} bounds {lo} .. {hi}")
    return errs


# ====================================================================== QA
def qa_instance(a, b, name):
    """A QA copy of the GLB's mesh from Godot point a to Godot point b (scaled along its length)."""
    src = bpy.data.objects[NAME]
    o = src.copy()
    o.data = src.data.copy()
    o.name = name
    bpy.context.scene.collection.objects.link(o)
    va, vb = Vector(a), Vector(b)
    d = vb - va
    # Godot -> Blender via the lib matrix; our mesh runs along Godot +Z
    Cm = K.V.C
    zdir = (Cm @ d).normalized()
    base_z = Cm @ Vector((0, 0, 1))
    rot = base_z.rotation_difference(zdir).to_matrix().to_4x4()
    sc = Matrix.Scale(d.length, 4, base_z)
    o.matrix_world = Matrix.Translation(Cm @ va) @ rot @ sc
    K.override(o, K.glow("qa_beam", "FFF4D0", 6.0))
    o.visible_shadow = False
    M.refresh()
    return o


def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_core()
    parts["beam"].hide_render = True
    # a plausible path: the Sun axis -> tower I (mark 1) -> tower II -> tower III -> tower IV -> up to the Core
    pts = [(-11.8, 1.8, 0.0), (0.0, 1.8, 10.5), (0.0, 1.8, 8.5), (0.0, 1.8, 6.5), (0.0, 1.8, 4.5), (0.0, 4.1, 0.0)]
    # (QA path is only to read the ribbon; the game decides the real folds)
    for i in range(len(pts) - 1):
        qa_instance(pts[i], pts[i + 1], f"qa_beam_{i}")
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=True)
    if C.want(args, "1"):
        cam, tgt, fov = C.view("bridge")
        lit(cam, 70.0, 0.25)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # the ribbon seen end-on and from the side near the Core
        cam, tgt, fov = (3.0, 3.2, 6.0), (0.0, 2.8, 2.5), 56
        lit(cam, 70.0, 0.25)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)


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
