"""key_square.glb — the square isolator key of Strand's trapped-key interlock (Chapter 3 W1 / W1b).

A Castell-style brass interlock key, 85 mm long: a flat 3 mm brass bow 34 mm across shaped as the square symbol
(lib_ch3_symbols, corners rounded) with the same symbol embossed on its face and a Ø 3.2 mm hanging hole near
its top, a turned neck and collar, a round brass shank Ø 12 mm and a flat dark-steel bit with two code cuts.
One blank, four bows (key_diamond, key_triangle, key_circle, key_square): the silhouette is the cue.
Parts: `key_square` (root: bow, emboss, shank; M_Brass_Aged), `key_bit` (M_Steel_Dark).
Lies flat, hero face up (Godot +Y), bow toward Godot -Z, blade toward +Z. Origin at the centre of mass.
Builder: lib_ch3_items.castell_key / key_item.
    blender -b --factory-startup -P tools/blender/models/key_square.py [-- --no-render]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lib_ch3_items as G  # noqa: E402

if __name__ == "__main__":
    G.key_item("square")
