"""R4 Cold Store entry of the Chapter 2 expansion room preview (loaded by ch2x_room_preview.py; keeps the shared script free of cold-store data).

    blender -b --factory-startup -P tools/blender/ch2x_room_preview.py -- room=cold [--shots=cold,aisle,...]
The carriage arrangement shown is one example (slots 0 1 3 4 6 occupied, gaps at 2 and 5, the chest at the end of the aisle in slot 2).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_cold as K  # noqa: E402
import lib_ch2x as X  # noqa: E402

COLD, ICE_LIGHT = "D6E8FF", "BFD8FF"
OCC = (0, 1, 3, 4, 6)          # slots with a carriage; carriage_k stands in slot OCC[k-1]


def pre():
    """Called by the preview after X.begin(): textured decal slots and the preview look of the glow/frost materials."""
    X.decal("M_Decal_PlanPlate", "plan_plate.png")
    X.decal("M_Decal_CarriageTags", "carriage_tags.png")
    X.decal("M_Decal_ChestRings", "chest_ring.png")
    X.decal("M_Decal_ChestPlate", "chest_plate.png")
    K.decal_alpha("M_Decal_SafeStencil", "meridian_stencil.png")
    K.decal_alpha("M_Decal_FrostSign", "frost_sign_0.png")
    for k in range(1, 5):
        X.decal(f"M_Decal_CanLabel_{k}", f"can_label_{k}.png")
    K.decal_alpha("M_Decal_FrostPatch", "frost_patch.png")
    K.qa_frost_material(wipe_band=-1)
    K.preview_glow()


MODELS = [("room_cold", (0, 0, 0), 0)]
for k, slot in enumerate(OCC, start=1):
    MODELS.append((f"carriage_{k}", (-3.0 + slot, 0.0, -1.0), 0))
MODELS += [("frost_window", (3.845, 1.63, 2.20), -90), ("cold_chest", (-1.0, 0.0, -3.14), 0), ("film_can_1", (2.0, 0.0, 3.0), 0)]

ROOMS_COLD = {
    "models": MODELS,
    "pre": pre,
    "lights": [("tube0", "POINT", (-2.0, 3.0, -1.0), 260, COLD, 0.12), ("tube1", "POINT", (0.0, 3.0, -1.0), 260, COLD, 0.12),
               ("tube2", "POINT", (2.0, 3.0, -1.0), 260, COLD, 0.12), ("front", "POINT", (0.0, 2.7, 2.6), 160, ICE_LIGHT, 0.2),
               ("well", "POINT", (3.3, 1.6, 2.2), 70, "CFE6FF", 0.2), ("aisle", "POINT", (-1.0, 2.6, -1.6), 120, COLD, 0.15)],
    "shots": {"cold": ((0.2, 1.55, 3.1), (0.0, 1.3, -1.6), 66), "overview": ((-3.5, 2.5, 3.2), (0.8, 1.2, -1.2), 74),
              "aisle": ((-1.0, 1.50, 1.2), (-1.0, 1.0, -3.1), 52), "frost": ((1.2, 1.6, 2.5), (3.85, 1.63, 2.2), 50),
              "rail_end": ((-1.2, 1.6, 2.8), (3.7, 1.5, 0.9), 58), "chest": ((-0.9, 1.1, -1.7), (-1.0, 0.32, -3.14), 44),
              "evap": ((-1.2, 1.5, 0.5), (-1.7, 2.6, -3.1), 56), "door": ((1.5, 1.6, 0.6), (-3.8, 1.2, 2.3), 62)},
}
