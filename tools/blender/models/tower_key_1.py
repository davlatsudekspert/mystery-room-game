"""tower_key_1.glb — the brass key of mirror tower I (Chapter 4, group H; puzzle P6, `tower_key_1` opens `gate_1`).

A Castell-style key, 98 mm long: a flat 3.2 mm brass bow 36 mm wide shaped like a crenellated tower (three merlons, a hanging eye), a raised numeral plaque carrying the Roman numeral
I in 1 mm relief (12 mm high, the same glyphs as the tower's numeral plate), a turned neck and collar, a round brass shank O 12 mm and a flat dark-steel bit whose
1 code cut differs from the other three keys. Parts: `tower_key_1` (root: bow, plaque, numeral, shank; M_Brass_Aged), `key_bit` (M_Steel_Dark).
Lies flat, hero face up (Godot +Y), the bow toward Godot -Z, the blade toward +Z. Origin at the centre of mass.
Builder: lib_ch4_items.tower_key.
    blender -b --factory-startup -P tools/blender/models/tower_key_1.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lib_ch4_items as H  # noqa: E402

if __name__ == "__main__":
    H.tower_key_item(1)
