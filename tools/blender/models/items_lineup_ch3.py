"""QA only: renders qa/blender/ch3/items_ch3.png with every Chapter 3 item side by side (no export).

Builds each item with its own script's build() / post() (the keys with lib_ch3_items.castell_key: the same
geometry as the exported .glb files), drops it on a walnut table at its natural resting pose (the meter, the
fork and the crystals stand, the keys and the ECG strip lie flat) and frames all of them with one camera.
The meter reads 4.
    blender -b --factory-startup -P tools/blender/models/items_lineup_ch3.py
"""
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import bpy  # noqa: E402
import mrlib as M  # noqa: E402
import lib_devices as D  # noqa: E402
import lib_ch2_items as C  # noqa: E402
import lib_ch3_items as G  # noqa: E402

LAYOUT = {     # name: (x, y, yaw deg) on the table (Blender XY, camera at -Y)
    "ecg_strip": (-0.10, 0.15, 3.0),
    "resonance_meter": (0.19, 0.14, -14.0),
    "strand_fork": (0.31, 0.19, 0.0),
    "nursery_crystal": (0.07, 0.13, 8.0),
    "seed_crystal": (0.12, 0.03, 0.0),
    "key_diamond": (-0.24, -0.06, 8.0),
    "key_triangle": (-0.15, -0.07, -4.0),
    "key_circle": (-0.06, -0.06, 6.0),
    "key_square": (0.03, -0.07, -7.0),
}


def load(name):
    spec = importlib.util.spec_from_file_location(f"item_{name}", os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_item(name):
    if name.startswith("key_"):
        root, _info = G.castell_key(name[4:], name)
        M.finalize([root] + list(root.children))
        D.resmooth(root, 32.0)
        return
    mod = load(name)
    mod.build()


def main():
    M.reset_scene()
    G.ensure_materials()
    groups = []
    for name, (x, y, yaw) in LAYOUT.items():
        before = set(bpy.context.scene.objects)
        if name.startswith("key_"):
            build_item(name)
            new = [o for o in bpy.context.scene.objects if o not in before]
        else:
            mod = load(name)
            mod.build()
            new = [o for o in bpy.context.scene.objects if o not in before]
            M.finalize(new)
            if hasattr(mod, "post"):
                mod.post()
            if name == "resonance_meter":
                mod.reading(4)()
        for o in new:
            o.name = f"LU_{name}_{o.name}"
        groups.append((name, new, x, y, yaw))
    for name, new, x, y, yaw in groups:
        meshes = [o for o in new if o.type == "MESH"]
        com = D.centre_of_mass(meshes)
        grp = M.empty("LU_grp_" + name, loc=tuple(com))
        for o in new:
            if o.parent is None:
                M.set_parent(o, grp)
        grp.location = (x, y, 0.0)
        grp.rotation_euler = (0.0, 0.0, math.radians(yaw))
        M.refresh()
        lo, _ = D.bounds(meshes)
        grp.location.z -= lo.z
    top = M.box("LU_table", (0.80, 0.50, 0.03), loc=(0.03, 0.06, -0.015), mat="M_Wood_Walnut", bevel=0.004)
    M.box_uv(top, 1.0)
    D.qa_tweak()
    lights = [((0.6, -1.0, 1.3), 260, "FFE2C0", 1.6), ((-1.2, -0.5, 0.8), 90, "BFD4FF", 2.0),
              ((0.2, 1.3, 1.5), 160, "FFFFFF", 1.2)]
    C.shot("items_ch3", (0.03, -0.50, 0.42), (0.03, 0.06, 0.03), lens=40, floor_z=-0.03, samples=32,
           res=(960, 640), lights=lights)


if __name__ == "__main__":
    main()
