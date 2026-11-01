"""wipe_cloth.glb — the soft cloth of the Cold Store frost window (hands layer item; N5 wipe reveal).

Chapter 2 expansion (docs/CHAPTER2_EXPANSION.md §8 N5, §12). A square of faded flannel, folded in three: three layers with soft wavy edges, a blue
stitched hem on the top fold, two woven stripes and a loose thread. 0.15 x 0.11 x 0.020, lying flat (front face = +Y up).

Model space (Godot): origin at the centre of mass (0, 0, 0). Nodes:
  wipe_cloth        the cloth (single object, identity)
  grip_mount        empty at the top fold centre (0, 0.0165, 0): where the glove pinches it (hands layer)

    blender -b --factory-startup -P tools/blender/models/wipe_cloth.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_arch as A  # noqa: E402
import lib_ch2x as X  # noqa: E402
import lib_ch2x_cell as Q  # noqa: E402
from lib_ch2x import G, GV, gbox, gcyl, part, mount  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "wipe_cloth"
BUDGET = 1500
ARGS = M.main_guard()
CLOTH = "M_Linen"


def layer(name, x0, x1, z0, z1, y, ph, thick=0.0062, mat=CLOTH):
    xs = [x0 + (x1 - x0) * i / 12 for i in range(13)]

    def sec(x):
        n = 7
        pts = []
        for j in range(n):
            z = z0 + (z1 - z0) * j / (n - 1)
            e = min(j, n - 1 - j) / 2.0                                   # rolled-down edges
            ye = y - 0.0030 * max(0.0, 1.0 - e) + 0.0007 * math.sin(x * 55 + j * 1.7 + ph) + 0.0005 * math.sin(z * 70 + ph)
            pts.append((z, ye))
        return pts
    return Q.drape(name, xs, sec, thick=thick, mat=mat)


def build():
    X.begin()
    o = []
    o.append(layer("l0", -0.075, 0.075, -0.055, 0.055, -0.0075, 0.0))
    o.append(layer("l1", -0.071, 0.077, -0.052, 0.052, 0.0000, 1.3))
    o.append(layer("l2", -0.077, 0.071, -0.050, 0.054, 0.0076, 2.4))
    # blue stitched hem along the front edge of the top fold
    for i in range(14):
        x = -0.062 + i * 0.0095
        o.append(gbox(f"hem{i}", (x, 0.0148, 0.043), (x + 0.0055, 0.0158, 0.0455), "M_Enamel_Cobalt", bevel=0.0))
    for k, z in enumerate((0.029, 0.020)):                              # two woven flannel border stripes
        o.append(gbox(f"stripe{k}", (-0.070, 0.0145, z), (0.066, 0.0153, z + 0.0035), "M_Enamel_Cobalt", bevel=0.0))
    o.append(gcyl("thread", 0.0012, 0.020, (-0.070, 0.0, 0.040), axis="x", verts=4, mat="M_Enamel_Cobalt", bevel=0.0))
    X.top(o)
    cl = part("wipe_cloth", o, (0, 0, 0))
    mount("grip_mount", (0.0, 0.0165, 0.0))
    return cl


if __name__ == "__main__":
    build()
    errs = X.finish(NAME, ["wipe_cloth", "grip_mount"], ["wipe_cloth"], BUDGET, {"wipe_cloth": (0, 0, 0)}, show=["wipe_cloth"], wood=False)
    if X.want_render(ARGS):
        X.qa_props(NAME, [("", (0.12, 0.17, 0.22), (0.0, 0.0, 0.0), 28)], floor=True, world=0.2)
