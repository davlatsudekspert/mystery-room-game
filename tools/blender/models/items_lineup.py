"""QA only: renders qa/blender/items_lineup.png with every inventory item side by side (no export).

Builds each item with its own script's build() (same geometry as the exported .glb), drops it on a
table at its natural resting pose and frames all of them with one camera.
    blender -b --factory-startup -P tools/blender/models/items_lineup.py
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

LAYOUT = {     # name: (x, y, yaw deg, tilt about X deg)
    "notebook": (-0.25, 0.13, 10.0, 0.0),
    "letter": (-0.03, 0.15, -6.0, 0.0),
    "mirror_item": (0.21, 0.16, 0.0, -72.0),      # reclined on its back for the shot
    "breaker_handle": (-0.22, -0.12, 10.0, 0.0),
    "crystal_lens": (-0.08, -0.10, 14.0, 0.0),
    "radio_valve": (0.02, -0.12, 0.0, 0.0),
    "battery_cell": (0.10, -0.11, 0.0, 0.0),
    "brass_key": (0.19, -0.15, -24.0, 0.0),
    "uv_lamp": (0.34, -0.07, -38.0, 0.0),
}


def load(name):
    spec = importlib.util.spec_from_file_location(f"item_{name}", os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    M.reset_scene()
    D.ensure_materials()
    groups = []
    for name, (x, y, yaw, tilt) in LAYOUT.items():
        mod = load(name)
        before = set(bpy.context.scene.objects)
        mod.build()
        new = [o for o in bpy.context.scene.objects if o not in before]
        groups.append((name, mod, new, x, y, yaw, tilt))
    M.finalize()
    for name, mod, new, x, y, yaw, tilt in groups:
        if hasattr(mod, "post"):
            mod.post()
        meshes = [o for o in new if o.type == "MESH"]
        com = D.centre_of_mass(meshes)
        grp = M.empty("QA_grp_" + name, loc=tuple(com))
        for o in new:
            if o.parent is None:
                M.set_parent(o, grp)
        grp.location = (x, y, 0.0)
        grp.rotation_euler = (math.radians(tilt), 0.0, math.radians(yaw))
        M.refresh()
        lo, _ = D.bounds(meshes)
        grp.location.z -= lo.z
    D.qa_tweak()
    D.shot("items_lineup", (0.05, -0.80, 0.60), (0.05, 0.02, 0.03), lens=43, samples=32, res=(960, 600))


if __name__ == "__main__":
    main()
