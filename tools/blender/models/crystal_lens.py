"""crystal_lens.glb — Strand's crystal lens (inventory item; also seated in the projector as
`lens_installed`, which shares lib_devices.crystal_lens()).

A 12-facet rose-cut crystal (M_Crystal) held in a knurled, polished brass ring, 70 mm across and 12 mm
thick, with "MERIDIAN INSTITUTE · LUMEN Nº 7" engraved around the front face and a scale of ticks below.
Origin at the centre of mass (= the lens centre). The disc faces Blender -Y (Godot +Z, the inspect camera).
    blender -b --factory-startup -P tools/blender/models/crystal_lens.py [-- --no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import mrlib as M  # noqa: E402
import lib_mech as L  # noqa: E402
import lib_devices as D  # noqa: E402
from mathutils import Matrix  # noqa: E402

NAME = "crystal_lens"


def build():
    lens = D.crystal_lens("lens_core", (0, 0, 0), segments=40, ticks=0)
    yf = -0.006 - 0.00005
    rm = 0.0318
    txt = D.text_on_circle("lens_txt", "MERIDIAN INSTITUTE · LUMEN Nº 7", 0.0025, rm - 0.0009,
                           start_deg=90.0, step_deg=5.4, mat="M_Bakelite")
    L.to_front(txt, y_back=yf)
    parts = [lens, txt]
    for k in range(13):                      # scale ticks on the lower half
        a = math.radians(205.0 + k * 10.833)
        ln = 0.0024 if k % 3 == 0 else 0.0013
        tk = L.flat_shape("ltick", [L.rounded_rect(0.0005, ln, 0.0001, 1)], mat="M_Bakelite")
        tk.data.transform(Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        L.to_front(tk, y_back=yf, x=(rm + 0.0006 - ln / 2) * math.cos(a), z=(rm + 0.0006 - ln / 2) * math.sin(a))
        parts.append(tk)
    obj = M.join(parts, NAME)
    return [obj]


def post():
    D.resmooth(M.bpy.data.objects[NAME], 12.0)


def main():
    D.item_main(NAME, build, post=post, shots=[
        ("", (0.07, -0.16, 0.06), (0.0, 0.0, 0.0), 60),
        ("_2", (-0.05, 0.12, 0.03), (0.0, 0.0, 0.0), 60),
    ])


if __name__ == "__main__":
    main()
