"""core_crystal.glb — the Core of the Array: a double-terminated crystal on a brass pedestal (Chapter 4, group D; the hero of
the climax). Contract: docs/models/ch4.md section 6 core_crystal; results: docs/models/ch4_d.md.

ISLAND FRAME: the model is placed at (0, 2.5, 0); origin = the island centre on the platform top; the crystal centre is
(0, 1.6, 0) = world (0, 4.1, 0). Three mesh objects, one surface each:
  core_pedestal  M_Brass_Aged     r 0.55, 1.10 high: stepped foot, waist r 0.40, flared collar, a top plate and a socket cup
                                  holding the crystal's lower point, six setting claws
  core_shell     M_Crystal        the hexagonal crystal: prism r 0.24, 0.50 high, rhombic terminations, 1.20 high in all
                                  (y 1.00 .. 2.20); translucent (the code may raise its emission)
  core_light     M_Emissive_Lumen the inner core of the crystal: a smaller faceted gem inside the shell (the code drives its
                                  emission; core_glow's OmniLight sits at core_center)
  core_center    empty at (0, 1.6, 0)
The 41 + 1 light sprites are NOT in the file: the code builds a MultiMesh orbiting core_center at r 0.75 in three inclined bands
(sprite size 0.07), see docs/models/ch4_d.md for the QA layout used in the renders.

    blender -b --factory-startup -P tools/blender/models/core_crystal.py [-- --no-render] [--shots=1,2,...]
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
from lib_ch4 import K, D, BRASS, CRYSTAL, LUMEN, STEEL  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

NAME = "core_crystal"
TRI_BUDGET, SURF_BUDGET, MAT_BUDGET = 3000, 3, 3
CENTER = (0.0, 1.6, 0.0)
R_SHELL, H_BODY, H_TIP = 0.24, 0.50, 0.35          # 0.50 + 2 x 0.35 = 1.20 high


def pedestal():
    prof = [(0.0, 0.0), (0.55, 0.0), (0.55, 0.05), (0.51, 0.08), (0.51, 0.115), (0.45, 0.135), (0.45, 0.17), (0.40, 0.21),
            (0.40, 0.84), (0.43, 0.87), (0.43, 0.90), (0.50, 0.95), (0.50, 0.985), (0.55, 1.01), (0.55, 1.07), (0.31, 1.07),
            (0.31, 1.10), (0.27, 1.125), (0.215, 1.10), (0.14, 1.02), (0.0, 0.99)]
    parts = [K.glathe("pedestal", prof, base=(0, 0, 0), axis=(0, 1, 0), segments=36, mat=BRASS, smooth=60.0)]
    # eight rivets on the collar and a machined band
    for i in range(12):
        a = math.radians(30.0 * i)
        parts.append(K.rivet("rv", 0.016, (0.502 * math.sin(a), 0.92, 0.502 * math.cos(a)),
                             normal=(math.sin(a), 0.0, math.cos(a)), mat=BRASS, segs=5))
    # six setting claws: up from the cup rim, then in over the crystal's shoulder
    for i in range(6):
        a = math.radians(60.0 * i + 30.0)
        d = Vector((math.sin(a), 0.0, math.cos(a)))
        p0 = d * 0.285 + Vector((0, 1.11, 0))
        p1 = d * 0.285 + Vector((0, 1.30, 0))
        p2 = d * 0.250 + Vector((0, 1.395, 0))
        parts.append(D.rod("claw", tuple(p0), tuple(p1), 0.011, segs=5, mat=BRASS))
        parts.append(D.rod("claw", tuple(p1), tuple(p2), 0.011, segs=5, mat=BRASS))
    return parts


def build():
    M.reset_scene()
    C.ensure_materials()
    ped = K.part("core_pedestal", pedestal(), pivot=(0.0, 0.0, 0.0))
    shell = X.gem2("shell_mesh", CENTER, R_SHELL, H_BODY, H_TIP, CRYSTAL, shoulder=0.52, shoulder_at=0.5, twist=30.0)
    shell = K.part("core_shell", [shell], pivot=CENTER)
    core = X.gem2("core_mesh", CENTER, 0.105, 0.36, 0.30, LUMEN, shoulder=0.5, shoulder_at=0.55, twist=30.0)
    core = K.part("core_light", [core], pivot=CENTER)
    K.empty("core_center", CENTER)
    K.to_blender()
    C.finalize()
    return dict(pedestal=ped, shell=shell, core=core)


def verify(path):
    req = ["core_pedestal", "core_shell", "core_light", "core_center"]
    ident = [r for r in req if r != "core_center"]
    expect = {"core_pedestal": (0.0, 0.0, 0.0), "core_shell": CENTER, "core_light": CENTER, "core_center": CENTER}
    errs = C.verify(path, required=req, identity=ident, expect=expect, tri_budget=TRI_BUDGET, surf_budget=SURF_BUDGET,
                    mat_budget=MAT_BUDGET)
    for n in ("core_pedestal", "core_shell", "core_light"):
        lo, hi = C.bounds([n])
        print(f"{C.TAG} {n} bounds {lo} .. {hi} tris {K.mesh_tris(bpy.data.objects[n])}")
    return errs


# ====================================================================== QA
def qa(args, parts):
    X.qa_env(extra=[("bridge", (0, 0, 0), 0.0), ("catwalk", (0, 0, 0), 0.0), ("shell_lift4", (0, 0, 0), 0.0),
                    ("ring_rails", (0, 0, 0), 0.0), ("array_rings", (0, 0, 0), 0.0)])
    X.qa_reliquary(skip=(NAME,), sprites=True)
    X.qa_place_island([parts["pedestal"], parts["shell"], parts["core"], bpy.data.objects["core_center"]])
    parts["core"].visible_shadow = False
    S = int(os.environ.get("MR_S", "24"))
    RES = (int(os.environ.get("MR_W", "960")), int(os.environ.get("MR_H", "640")))

    def lit(cam, fill, ambient):
        C.lights(cam, fill=fill, ambient=ambient, bridge_lamp=False)
    if C.want(args, "1"):          # the core closeup (cage and glass hidden): crystal, light sprites, pedestal, cradle
        X.vis("qa_cage_", False)
        X.vis("qa_glass_tower_", False)
        cam, tgt, fov = (0.0, 4.7, 2.5), (0.0, 4.0, 0.0), 52
        lit(cam, 40.0, 0.2)
        C.shoot(NAME, cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "2"):          # a low closeup of the pedestal and the setting claws
        cam, tgt, fov = (1.3, 3.75, 1.6), (0.0, 3.75, 0.0), 46
        lit(cam, 30.0, 0.15)
        C.shoot(NAME + "_2", cam, tgt, fov, samples=S, res=RES)
    if C.want(args, "3"):          # the island view with the cage and the glass case round it
        X.vis("qa_cage_", True)
        X.vis("qa_glass_tower_", True)
        cam, tgt, fov = C.view("island")
        lit(cam, 40.0, 0.2)
        C.shoot(NAME + "_3", cam, tgt, fov, samples=S, res=RES)

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
