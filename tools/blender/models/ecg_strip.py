"""ecg_strip.glb — Strand's ECG strip (clipped to his office lamp; the W2 "heart strip" evidence).

A strip of ECG chart paper, 320 x 50 mm, 0.2 mm thick, still slightly curled from the recorder's roll (the
ends lift 12 mm), with a Ø 3 mm clip hole punched at the centre of its top edge (the bracketed edge).
Parts:
- `ecg_strip` (root): the back and the cut edges, M_Paper.
- `strip_face`: the printed face, its own object. **UV 0..1 over the full 320 x 50 rectangle**: u runs along
  the trace from left to right as the strip reads (brackets sun, moon, star), v from the bottom edge (0) to
  the bracketed top edge (1), never mirrored. Slot M_Decal_EcgPaper (the grid, the brackets and the symbols
  of ecg_paper.png); ItemDress puts the trace shader on it (docs/models/ch3.md section 11). The clip hole is
  cut through the face at u = 0.5, v = 0.944 (Ø 3 mm = u 0.4953..0.5047, v 0.914..0.974).
Lies flat, face up (Godot +Y), the bracketed edge toward Godot -Z. Origin at the centre of mass (the strip's
area centroid; paper sheets are weighed by area).
    blender -b --factory-startup -P tools/blender/models/ecg_strip.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bmesh  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402

NAME = "ecg_strip"
W, H, T = 0.320, 0.050, 0.0002
CURL = 0.012                       # lift of each end (z = CURL (2x / W)^2)
HOLE_R, HOLE_Y = 0.0015, H / 2 - 0.0028
Y1 = HOLE_Y - 0.0035                # the row under the hole region
NX = 24                            # segments along the strip (the curl follows them)


def top_face(bm):
    """The printed face at z = T as a structured strip (so it follows the curl): quads between the rows
    y = -H/2, Y1 and H/2 at NX + 1 columns, except the two cells around x = 0 above Y1, which are filled
    around the clip hole. Returns the faces."""
    xs = [-W / 2 + W * i / NX for i in range(NX + 1)]
    ys = (-H / 2, Y1, H / 2)
    grid = [[bm.verts.new((x, y, T)) for x in xs] for y in ys]
    faces = []
    for r in range(2):
        for i in range(NX):
            if r == 1 and i in (NX // 2 - 1, NX // 2):
                continue
            faces.append(bm.faces.new((grid[r][i], grid[r][i + 1], grid[r + 1][i + 1], grid[r + 1][i])))
    i0 = NX // 2 - 1
    ring = [grid[1][i0], grid[1][i0 + 1], grid[1][i0 + 2], grid[2][i0 + 2], grid[2][i0 + 1], grid[2][i0]]
    edges = [bm.edges.get((ring[k], ring[(k + 1) % 6])) or bm.edges.new((ring[k], ring[(k + 1) % 6]))
             for k in range(6)]
    hole = [bm.verts.new((x, y, T)) for (x, y) in L.circle(HOLE_R, 12, cx=0.0, cy=HOLE_Y)]
    edges += [bm.edges.new((hole[k], hole[(k + 1) % 12])) for k in range(12)]
    res = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    faces += [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
    return faces


def build():
    bm = bmesh.new()
    top = top_face(bm)
    # bottom copy at z = 0 and walls along every boundary edge -> one closed slab
    bot = {v: bm.verts.new((v.co.x, v.co.y, 0.0)) for v in list(bm.verts)}
    for f in list(top):
        bm.faces.new([bot[v] for v in reversed(f.verts)])
    for e in [e for e in bm.edges if len(e.link_faces) == 1 and e.verts[0] in bot and e.verts[1] in bot]:
        a, b = e.verts
        bm.faces.new((a, b, bot[b], bot[a]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for v in bm.verts:
        v.co.z += CURL * (2 * v.co.x / W) ** 2
    # split: the printed face (top) becomes its own object
    face_bm = bmesh.new()
    vmap = {}
    top_set = set(top)
    for f in top:
        vs = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = face_bm.verts.new(v.co)
            vs.append(vmap[v])
        nf = face_bm.faces.new(vs)
        if f.normal.z < 0:
            nf.normal_flip()
    bmesh.ops.delete(bm, geom=list(top_set), context="FACES_ONLY")
    me = bpy.data.meshes.new(NAME)
    bm.to_mesh(me)
    bm.free()
    root = bpy.data.objects.new(NAME, me)
    bpy.context.scene.collection.objects.link(root)
    M.assign(root, "M_Paper")
    fm = bpy.data.meshes.new("strip_face")
    face_bm.normal_update()
    face_bm.to_mesh(fm)
    face_bm.free()
    face = bpy.data.objects.new("strip_face", fm)
    bpy.context.scene.collection.objects.link(face)
    M.assign(face, "M_Decal_EcgPaper")
    for p in face.data.polygons:
        if p.normal.z < 0:
            p.flip()
    M.set_parent(face, root)
    return [root]


def post():
    face = bpy.data.objects["strip_face"]
    C.uv_rect_all(face, -W / 2, W / 2, -H / 2, H / 2, axis="Z")
    M.smooth(bpy.data.objects[NAME], 30.0)
    M.smooth(face, 30.0)


COM = [Vector((0, 0, 0))]


def centroid():
    """Area-weighted centroid of the printed face, moved to mid-thickness."""
    face = bpy.data.objects["strip_face"]
    M.refresh()
    acc, area = Vector((0, 0, 0)), 0.0
    for p in face.data.polygons:
        a = p.area
        acc += (face.matrix_world @ p.center) * a
        area += a
    c = acc / area
    COM[0] = Vector((c.x, c.y, c.z - T / 2))
    return COM[0]


def report():
    face = bpy.data.objects["strip_face"]
    flo, fhi = C.godot_bounds([face])
    print(f"[items3] strip_face bounds godot min {tuple(round(c, 4) for c in flo)} max {tuple(round(c, 4) for c in fhi)}")
    G.report_point("clip hole centre (on the face)", point=Vector((0.0, HOLE_Y, T)) - COM[0])


def main():
    C.LIGHTS = C.SOFT
    G.item_main(NAME, build, post=post, required=("strip_face",), budget=400, extra_report=report,
                com_fn=centroid, shots=[
                    ("", (0.10, -0.36, 0.30), (0.0, 0.0, 0.0), 50),
                    ("_2", C.inspect_cam(0.46), (0.0, -0.002, 0.0), 50),
                ])


if __name__ == "__main__":
    main()
