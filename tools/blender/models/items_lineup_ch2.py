"""QA only: renders qa/blender/ch2/items_ch2.png with every Chapter 2 inventory item side by side (no export).

Builds each item with its own script's build() / post() (same geometry as the exported .glb), drops it on
a walnut table at its natural resting pose (the film reel, the receiver and the crystal stand, the rest
lie flat) and frames all of them with one camera. The request card shows the solved punch pattern
(1 0 1 1 0 0 1 0) and one crystal shows a recorded image (Leyla's sign), as ItemDress does in game.
    blender -b --factory-startup -P tools/blender/models/items_lineup_ch2.py
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

LAYOUT = {     # name: (x, y, yaw deg, tilt about X deg) on the table (Blender XY, camera at -Y)
    "file_folder": (-0.34, 0.20, 7.0, 0.0),
    "film_reel": (-0.06, 0.25, 12.0, 0.0),
    "tape_reel": (0.17, 0.22, -10.0, 0.0),
    "pocket_receiver": (0.38, 0.21, -18.0, 0.0),
    "index_card": (-0.31, -0.02, -4.0, 0.0),
    "request_card": (-0.14, 0.03, 9.0, 0.0),
    "leyla_badge": (0.03, 0.02, -8.0, 0.0),
    "lumen_crystal": (0.17, 0.05, 15.0, 0.0),
    "glass_slide": (0.31, 0.00, 6.0, 0.0),
    "key_strand": (-0.20, -0.17, 72.0, 0.0),
    "key_leyla": (0.00, -0.16, 78.0, 0.0),
    "locker_key": (0.18, -0.15, 64.0, 0.0),
}


def load(name):
    spec = importlib.util.spec_from_file_location(f"item_{name}", os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def hook(name, mod):
    """QA dressing (before the objects are renamed)."""
    if name == "request_card":
        for i, bit in enumerate(C.PUNCH_CODE):
            bpy.data.objects[f"hole_{i}"].hide_render = not bit
    if name == "lumen_crystal" and hasattr(mod, "recorded"):
        mod.recorded()


def table():
    mat = bpy.data.materials.get("M_Wood_Walnut") or M.material("M_Wood_Walnut")
    top = M.box("LU_table", (1.30, 0.80, 0.03), loc=(0.02, 0.05, -0.015), mat="M_Wood_Walnut", bevel=0.004)
    M.box_uv(top, 1.0)
    return top, mat


def main():
    M.reset_scene()
    C.ensure_materials()
    groups = []
    for name, (x, y, yaw, tilt) in LAYOUT.items():
        mod = load(name)
        before = set(bpy.context.scene.objects)
        mod.build()
        new = [o for o in bpy.context.scene.objects if o not in before]
        M.finalize(new)
        if hasattr(mod, "post"):
            mod.post()
        hook(name, mod)
        for o in new:                                    # unique names for the next item's lookups
            o.name = f"LU_{name}_{o.name}"
        groups.append((name, new, x, y, yaw, tilt))
    for name, new, x, y, yaw, tilt in groups:
        meshes = [o for o in new if o.type == "MESH"]
        com = D.centre_of_mass(meshes)
        grp = M.empty("LU_grp_" + name, loc=tuple(com))
        for o in new:
            if o.parent is None:
                M.set_parent(o, grp)
        grp.location = (x, y, 0.0)
        grp.rotation_euler = (math.radians(tilt), 0.0, math.radians(yaw))
        M.refresh()
        lo, _ = D.bounds(meshes)
        grp.location.z -= lo.z
    table()
    D.qa_tweak()
    lights = [((0.6, -1.0, 1.3), 260, "FFE2C0", 1.6), ((-1.2, -0.5, 0.8), 90, "BFD4FF", 2.0),
              ((0.2, 1.3, 1.5), 160, "FFFFFF", 1.2)]
    C.shot("items_ch2", (0.02, -0.78, 0.70), (0.02, 0.04, 0.0), lens=40, floor_z=-0.03, samples=32,
           res=(960, 640), lights=lights)


if __name__ == "__main__":
    main()
