# Chapter 2 group D2: inventory items (measured results)

Models: `leyla_badge`, `index_card`, `request_card`, `file_folder`, `locker_key`, `pocket_receiver`,
`tape_reel`, `film_reel`, `lumen_crystal`, `glass_slide`, `key_strand`, `key_leyla`.
Scripts: `tools/blender/models/<name>.py`, shared helpers in `tools/blender/lib_ch2_items.py`, build list
`tools/blender/build_lists/ch2_items.txt`. Contract: `docs/models/ch2.md` §0 and §6 "Items", item rules in
`docs/models/devices.md` "Inventory items".

```
blender -b --factory-startup -P tools/blender/models/<name>.py [-- --no-render]
blender -b --factory-startup -P tools/blender/models/items_lineup_ch2.py      # QA only, exports nothing
```

Every script runs the same pipeline as the Chapter 1 items (`lib_ch2_items.item_main`): build, finalize
(box UVs, smoothing), set the decal UVs, move the **centre of mass** (uniform density over the closed
shells; paper sheets and decals carry no mass) to the origin, export `game/assets/models/<name>.glb`, then
print the size, bottom and tris in Godot axes, check the required part names (own objects, identity
rotation), and run a **back-face check** (14 orthographic views with a red back-face override; Godot culls
back faces): every item shows 0.00–0.03 % red. `check_glb_names.py` passes on all twelve GLBs, and every
material slot used exists in `game/assets/materials/`.

All coordinates are **Godot, model-local, metres**. The root mesh node is at identity, so scene origin =
node origin = centre of mass. To rest an item on a surface at height h, put its origin at **h − bottom**.

**Flat items** lie flat, hero face up (+Y), their top edge toward **−Z**. `ItemDB.view_tilt` (70° about +X)
then shows them upright to the inspect camera; the QA `_2` renders use exactly that view.
**Standing items** present their hero face to **+Z** with no tilt.

## Summary

| File | Tris | Size (Godot x × y × z) | Natural pose (identity) | Bottom (y) | Notes |
|---|---|---|---|---|---|
| `leyla_badge.glb` | 2,006 | 0.0900 × 0.0055 × 0.1005 | Flat, face up, clip toward −Z | −0.0006 | Printed card 0.086 × 0.054 centred (−0.0008, +0.0002, +0.0139); clip and cord stub beyond its top edge |
| `index_card.glb` | 192 | 0.1250 × 0.0003 × 0.0750 | Flat, face up, notched edge toward −Z | −0.0001 | Card centre (−0.0002, 0, −0.0006). **Notches at 1, 3, 4, 7** |
| `request_card.glb` | 520 | 0.1250 × 0.0004 × 0.0750 | Flat, face up, punch row toward −Z | −0.0002 | Card centre (−0.0001, 0, +0.0007); clipped corner top-left |
| `file_folder.glb` | 1,928 | 0.2540 × 0.0051 × 0.3205 | Flat, front cover up, top toward −Z, spine at −X | −0.0011 | Cover 0.240 × 0.320 centred (0, 0, −0.0002); tab to x = +0.133 |
| `locker_key.glb` | 2,253 | 0.0306 × 0.0034 × 0.0893 | Flat, tag toward −Z, blade toward +Z | −0.0016 | Key + split ring + brass tag "9" |
| `pocket_receiver.glb` | 2,292 | 0.0829 × 0.1738 × 0.0327 | Upright, face +Z, strap loop and antenna up | −0.0606 | Body 0.075 × 0.120 × 0.030 centred (−0.0004, −0.0006, −0.0001) |
| `tape_reel.glb` | 2,382 | 0.1270 × 0.0104 × 0.1270 | Flat, label side up | −0.0052 | Reel axis = the origin's Y axis; label top at y = +0.0052 |
| `film_reel.glb` | 2,486 | 0.1800 × 0.1800 × 0.0206 | On its rim, face +Z (axis along Z) | −0.0900 | Origin = reel centre |
| `lumen_crystal.glb` | 2,234 | 0.0545 × 0.0607 × 0.0072 | On its rim, face +Z, grip tab up | −0.0276 | Disc centre (0, −0.0003, −0.0005); face plane z = +0.0026 |
| `glass_slide.glb` | 258 | 0.0822 × 0.0028 × 0.0822 | Flat, front up, top toward −Z | −0.0014 | Image plane y = 0 |
| `key_strand.glb` | 1,854 | 0.0430 × 0.0105 × 0.1400 | Flat, bow toward −Z, bit toward +Z sticking out to +X | −0.0053 | Eye hole centre (−0.0014, 0, −0.0683), Ø 4.4 mm |
| `key_leyla.glb` | 1,854 | 0.0270 × 0.0072 × 0.1100 | Flat, bow toward −Z, bit toward +Z sticking out to +X | −0.0036 | Bow centre (−0.0009, 0, −0.0283), bow bottom z = −0.0123 |

**Inspect rotation:** `Basis(Vector3.RIGHT, deg_to_rad(70))` for every flat item above, i.e. all except
`pocket_receiver`, `film_reel` and `lumen_crystal`. `ItemDB.FLAT` already lists the badge, both cards, the
file, the slide, both keys and the locker key. **It does not list the tape reels** (`tape_1996`,
`tape_1997`, `tape_1998`): the contract has the reel lying face up (`deck_reel_mount`, `grille_reel_mount`:
"identity → reel face +Y"), so without the tilt the inspect view and the icon show the reel edge-on. Add the
three tape ids to `FLAT` (see "Notes for the game code").

---

## leyla_badge.glb (2,006 tris)

**Shape:** the printed card is ID-1 size, 86 × 54 mm, 0.76 mm thick, sealed in a clear laminate pouch
(`M_Glass`, 2 mm border, 10 mm margin above the card with a strap slot). A clear vinyl strap
(`M_Glass_Frosted`) with a chrome snap runs through the slot to a nickel alligator clip (`M_Chrome`); a
frayed stub of the old red lanyard cord (`M_String_Red`) is knotted through the clip's hinge.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `leyla_badge` (root) | (0, 0, 0) | Card edge (`M_Paper`) |
| `badge_face` | (−0.0008, +0.0002, +0.0139) | The printed front, 86 × 54 mm with r 3.2 mm corners, at the card top (y = +0.0002). **UV 0..1 over the 86 × 54 rectangle**, u left → right, v bottom → top as seen from above with the clip away from the viewer (−Z = top). Slot `M_Decal_Badge` (`badge.png`, 860 × 540; its 2.7 mm transparent corners fall outside the mesh) |
| `badge_clip` | same | Laminate, strap, snap, clip, cord (static) |

---

## index_card.glb (192 tris) — puzzle-critical

**Shape:** a cream catalogue card, 125 × 75 mm, 0.3 mm card stock, corners r 1.5 mm. Its top edge carries
**8 edge positions**, left → right = positions 1..8, position k centred at **u = (k − 0.5) / 8**
(x = −0.0625 + (k − 0.5) × 0.015625 from the card centre). **V-notches** (8.4 mm wide at the edge, 10 mm
deep, 0.6 mm flat at the tip, the same numbers as the decal builder's `NOTCH_W_PX` / `NOTCH_D_PX`) are cut
right through the card at **positions 1, 3, 4 and 7**; 2, 5, 6 and 8 are plain: pattern **1 0 1 1 0 0 1 0**
(`C.PUNCH_CODE`, = `ItemDress.PUNCH_CODE`). A Ø 6 mm catalogue-rod hole is punched at the bottom centre,
5.2 mm above the bottom edge, exactly where `index_card.png` draws it (transparent there too).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `index_card` (root) | (0, 0, 0) | Card body (`M_Paper`), notched and holed, its top cap replaced by the face |
| `card_face` | (−0.0002, +0.0002, −0.0006) | The printed face with the same notches and hole. **UV 0..1 over the full 125 × 75 rectangle** (u left → right, v bottom → top, top edge = notched edge at −Z). Slot `M_Decal_IndexCard` (alpha scissor). QA: the printed circles 1, 3, 4, 7 sit exactly in the notch tips |

---

## request_card.glb (520 tris)

**Shape:** a buff request card, 125 × 75 × 0.3 mm, corners r 1.5 mm, its **top-left corner clipped 4.5 mm**
(45°), as drawn in `request_card.png` (`REQ_CLIP_PX = 45`).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `request_card` (root) | (0, 0, 0) | Card body (`M_Paper`) |
| `card_face` | (−0.0001, +0.0002, +0.0007) | Printed face, **UV 0..1 over the full 125 × 75 rectangle** (u left → right, v bottom → top, the punch row at the top = −Z). Slot `M_Decal_RequestCard` |
| `hole_0` … `hole_7` | x = −0.0548, −0.0391, −0.0235, −0.0079, +0.0077, +0.0234, +0.0390, +0.0546; y = −0.0001; z = −0.0276 | Dark discs (`M_Rubber`), Ø 5.0 mm, a closed 0.4 mm puck from just under the card to just over its face, centred on the printed punch circles (u = (i + 0.5) / 8, 9.2 mm below the top edge). Own objects, identity. **All eight are visible in the GLB**; `ItemDress` hides the unpunched ones (all hidden for `blank_card`) |

---

## file_folder.glb (1,928 tris)

**Shape:** a closed manila personnel folder, 240 × 320 mm: two 0.6 mm card covers (`M_Cardboard`) joined
by a rounded spine fold on the left, three loose sheets inside (one sticks out 2 mm at the right edge, one
1.5 mm at the bottom), an index tab on the back cover sticking out 13 mm from the right edge near the top
(x 0.120 → 0.133, z −0.122 … −0.070 from the cover centre), linen-reinforced (`M_Linen`) with a white label
typed **0417** (3D, `M_Bakelite`), and a string-and-button closure: a brown fibre washer (`M_Leather`) with a
brass rivet at (+0.103, z +0.004), a cotton string (`M_Linen`) wound 1½ turns round it, its tail running
over the right edge.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `file_folder` (root) | (0, 0, 0) | Back cover with the tab |
| `folder_face` | (0, −0.0011, −0.0002) | Printed front cover at y = +0.0013, **UV 0..1 over the full 240 × 320 rectangle** (u left → right, v bottom → top, top = −Z). Slot `M_Decal_FileCover` (`file_cover.png` 1200 × 1600, same 3 : 4 aspect). The button sits at u ≈ 0.93, v ≈ 0.51, clear of the printed stamp |
| `folder_body` | same | Front cover edge, sheets, spine, tab, label, closure (static) |

---

## locker_key.glb (2,253 tris)

**Shape:** a nickel-plated locker key (`M_Chrome`), 50 mm: round bow Ø 21 mm (2 mm plate) with a Ø 5.6 mm
ring hole, a flat blade with four bitting cuts, a milled groove (dark strip) and a pointed tip. A blackened
split ring (`M_Steel_Dark`, Ø 19 mm) joins it to a round **aged-brass tag** (Ø 30 mm, 1.2 mm) stamped with
a big **9**: 3D, the numeral is sunk 0.4 mm into the tag and its floor darkened (`M_Bakelite`), 17 mm high,
inside a stamped border ring broken at the hole. The tag lies on the far side of the ring, so in the inspect
view the **9 reads upright** at the top and the key hangs below it. Key and tag rest on the ring wire where
they cross it (tilted 1.6° / 2.4°).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `locker_key` (root) | (0, 0, 0) | The key |
| `key_ring_tag` | (−0.0003, −0.0015, −0.0037) | Ring, tag, numeral, groove (static) |

---

## pocket_receiver.glb (2,292 tris)

**Shape:** a dark Bakelite pocket receiver, body 75 × 120 × 30 mm with rounded edges. Front, top to bottom:
a chrome-bezelled meter window (54 × 32 mm) with a cream face, a scale arc, **5 bar marks of rising length**
(bars 1–3 black, 4–5 red) and a rest dot; the black `needle` under a glass; a small chrome name plate with
the Institute's mark; a chrome-framed speaker grille, six chrome bars over grille cloth. Right side: the
knurled cream `tuning_knob` thumbwheel (Ø 21 mm, red index dot) protruding 7 mm. Left side: an earphone
socket. Back: battery door line and a coin-slot screw. Top: a telescopic chrome antenna (three sections, ball
tip, leaning 10° out to +X; tip at y ≈ +0.113) and a leather wrist-strap loop in a chrome keeper at the
centre.

| Part | Pivot (Godot) | Axis | Rest → active |
|---|---|---|---|
| `needle` | (−0.0004, +0.0174, +0.0154) | local **+Z** | Identity points at **12 o'clock** (+Y), 22 mm long. The code rotates it by **(40° − 16° × bars)**, bars 0..5: +40° (bars 0) = the rest dot at the left, bar k at 40 − 16k = +24, +8, −8, −24, −40°. Positive = counter-clockwise as the player sees the face. QA `_2` (bars 0) and `_3` (bars 4) check it |
| `tuning_knob` | (+0.0336, +0.0234, +0.0014) | local **+Z** | Own object (cosmetic); a thumbwheel whose axis faces the viewer, so it turns about +Z like a dial |
| `receiver_details` | (−0.0004, −0.0006, −0.0001) | — | static (meter, plate, grille, antenna, strap, socket) |

**Hanging:** the strap loop's inner apex (where a hook carries it) is at **(−0.0044, +0.0952, −0.0001)**.
`lockers.py` already places `receiver_mount` from this point.

---

## tape_reel.glb (2,382 tris)

**Shape:** a glossy black plastic 5-inch reel (`M_Lacquer_Black`, Ø 127 mm): two 1.2 mm flanges with a
stiffening rim and three kidney windows, a 54 mm hub, a keyed spindle hole (Ø 8 mm + three keyways at 90°,
210°, 330°), wound with brown ¼-inch tape (`M_Tape`) to Ø 104 mm, the tape end held by a strip of splicing
tape. 10.4 mm thick.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `tape_reel` (root) | (0, 0, 0) | Bottom flange |
| `label` | (0, −0.0047, 0) | Round paper hub label on the **top** flange (y = +0.0052): outer Ø 51 mm, spindle hole Ø 9 mm. **UV 0..1 over its bounding square** (u left → right, v bottom → top seen from above, the reel's 'top' toward −Z). Default slot **`M_Decal_TapeLabel_1996`**; `ItemDress` swaps in 1997 / 1998. The decal's transparent spindle hole and keyways (alpha scissor) line up with the mesh hole and the reel's keyways |
| `reel_body` | same | Top flange, rims, hub, tape pack (static) |

Spindle: the hole is on the origin's Y axis; the reel's lowest point is 0.0052 below the origin, so on a
platter at height h the origin goes to h + 0.0052 (used by `tape_deck`, `vent_grille`, `stacks_shelving`).

---

## film_reel.glb (2,486 tris)

**Shape:** a 7-inch (Ø 180 mm) pressed-steel 16 mm reel (`M_Chrome`): two 0.8 mm flanges, each cut into three
straight 12 mm spokes by three windows, an embossed stiffening ring and hub boss on each outer face, a steel
hub drum (`M_Steel_Dark`, Ø 50 mm) with the **square 8 mm drive hole and its keyway** right through
(keyway toward +Y at rest), wound with amber film (`M_Film`) to Ø 144 mm; the film end is held by white
splicing tape. 20.6 mm across the flanges.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `film_reel` (root) | (0, 0, 0) = reel centre | Front flange (the +Z face) |
| `reel_body` | same | Back flange, ribs, hub, film pack, tape (static) |

The axis is local **Z**. `film_projector.feed_reel_mount` turns it −90° about Y so the reel plane is YZ;
`film_splicer.splicer_reel_mount` uses identity (face +Z).

---

## lumen_crystal.glb (2,234 tris)

**Shape:** a clear crystal disc (`M_Crystal`), Ø 50 mm, 6 mm thick, with a flat polished front and a shallow
12-facet rose-cut back, in a thin turned brass bezel (`M_Brass_Aged`, Ø 54.5 mm, 7.2 mm deep, two fine
grooves round the band) with front and back lips. Eight engraved index dots ring the front lip (every 45°,
the 12 o'clock one a short bar) so a rotation reads at a glance. A small brass grip tab with a Ø 2.8 mm hole
stands up at 12 o'clock (top at y = +0.0331).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `lumen_crystal` (root) | (0, 0, 0) | The crystal disc |
| `crystal_face` | (0, −0.0003, −0.0005) = disc centre | Own front disc, **radius 23.2 mm** (the visible face inside the lip), at z = +0.0026, facing +Z. **UV 0..1 over its bounding square** (u left → right, v bottom → top seen from the front). Slot `M_Crystal`; `ItemDress.glyph` overrides it with the glowing image (QA `_3` shows `glyph_sign.png` on it) |
| `crystal_bezel` | same | Bezel, index dots, grip tab (static) |

Lying face up (lens case, rotated −90° about X) its lowest point is 0.0041 below the origin (`lens_case`
uses this). Standing (sockets, ports) its rim bottom is 0.0276 below the origin, the face plane 0.0026 in
front of it.

---

## glass_slide.glb (258 tris)

**Shape:** a 3¼-inch lantern slide, 82 × 82 mm: a 2.6 mm glass sandwich (`M_Glass`) bound on all four edges
with black passe-partout tape (`M_Rubber`, 2.8 mm over each face; its inner wall is removed so nothing shows
through the glass).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `glass_slide` (root) | (0, 0, 0) | Glass |
| `slide_image` | (0, −0.0013, 0) | The image plane inside the sandwich (y = 0), the **full 82 × 82 mm, UV 0..1** (u left → right, v bottom → top seen from the front, top = −Z). Slot `M_Decal_SlideMark` (alpha blend): `slide_mark.png` carries the black card mask with the round window, the mark and the ✦ corner spot (bottom-left) |
| `slide_mount` | same | Binding tape (static) |

`slide_projector.slide_gate_mount` stands it up facing +Z and the code turns it about local +Z in 90° steps;
the mark is symmetric under 180°, so 2 of the 4 positions put the meridian upright.

---

## key_strand.glb (1,854 tris)

**Shape:** a large ornate aged-brass key, 140 mm. The round bow (Ø 43 mm over its eight scallops, 4 mm plate,
chamfered) is **open: Strand's mark stands inside it as openwork** — a ring (Ø 14 / 19.6 mm) crossed by a
vertical meridian bar (2.1 mm) that runs from the top of the frame to the bottom; the four openings around
them are pierced through. The faces of the mark are polished (`M_Brass_Polished`). A hanging eye
(Ø 9.6 mm, hole Ø 4.4 mm) crowns the bow; an engraved line follows the frame. Below: turned collar beads, a
round shank (Ø 7.2 mm) with a mid ring and a domed tip, and a stepped bit with three wards (+X).

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `key_strand` (root) | (0, 0, 0) | Bow (with the mark) |
| `key_shaft` | (−0.0014, 0, −0.0028) | Collar, shank, bit, engraved line (static) |

**Hanging on the vault cradle:** with the mount basis `Basis(Vector3.RIGHT, PI / 2)` the key hangs bow up,
face +Z; the eye hole centre is then **(−0.0014, +0.0683, 0)** from the mount and the eye top
+0.0731 (`vault_interior.py` uses these numbers).

---

## key_leyla.glb (1,854 tris)

**Shape:** a slender 110 mm key of dark blued steel (`M_Steel_Dark`): an oval bow (27 × 32 mm, 3 mm plate,
rounded edges) **pierced right through with Leyla's sign** — a crescent opening to the right with three dots
in a vertical row inside its opening, proportions taken from `glyph_sign.png` (sign height 20.5 mm, dots
Ø 1.8 mm; the crescent's cusps are cut where it narrows below 0.8 mm so the piercing stays open) — a turned
collar, a thin shank (Ø 4.5 mm) with a domed tip and a small flag bit with one ward and a chamfered corner.

| Part | Node origin (Godot) | Notes |
|---|---|---|
| `key_leyla` (root) | (0, 0, 0) | Bow with the sign |
| `key_shaft` | (−0.0009, 0, +0.0007) | Collar, shank, bit (static) |

**Hanging on the vault cradle** (mount basis `Basis(Vector3.RIGHT, PI / 2)`): bow centre (−0.0009, +0.0283)
from the mount, bow half-width 0.0135, half-height 0.016, bow bottom +0.0123, top +0.0443. The vault cradle
carries it on two rest pins under the bow's shoulders (`vault_interior.py`, `LEYLA_BOW`).

---

## QA renders (`qa/blender/ch2/`)

| Model | Renders |
|---|---|
| leyla_badge | `item_leyla_badge.png` (hero), `_2` (inspect view: 70° tilt) |
| index_card | `item_index_card.png` (hero: notches over printed circles 1, 3, 4, 7), `_2` (inspect) |
| request_card | `item_request_card.png` (hero, all holes), `_2` (inspect, solved pattern 1 0 1 1 0 0 1 0) |
| file_folder | `item_file_folder.png` (hero), `_2` (inspect), `_3` (closure, tab and spine close-up) |
| locker_key | `item_locker_key.png` (hero), `_2` (inspect: the 9 upright) |
| pocket_receiver | `item_pocket_receiver.png` (hero), `_2` (meter, bars 0), `_3` (meter, bars 4), `_4` (back 3/4: antenna, strap, wheel, door screw) |
| tape_reel | `item_tape_reel.png` (hero with the 1996 label), `_2` (inspect view) |
| film_reel | `item_film_reel.png` (hero), `_2` (edge view: flanges, film pack) |
| lumen_crystal | `item_lumen_crystal.png` (hero), `_2` (back: rose-cut), `_3` (recorded: Leyla's sign glowing on `crystal_face`) |
| glass_slide | `item_glass_slide.png` (hero), `_2` (inspect) |
| key_strand | `item_key_strand.png` (hero), `_2` (inspect: the mark upright) |
| key_leyla | `item_key_leyla.png` (hero), `_2` (inspect: the sign opening right) |
| all | `items_ch2.png`: every item at its natural pose on a walnut table (request card punched, one crystal recorded) |

## Deviations from the contract and choices

- **Overall sizes include attachments.** The contract sizes are kept for the main bodies: the badge card
  0.086 × 0.054 (overall 0.090 × 0.1005 with the laminate, strap and clip), the file 0.24 × 0.32 (overall
  0.254 with the side tab and spine), the receiver body 0.075 × 0.12 × 0.03 (overall 0.083 × 0.174 × 0.033
  with the wheel, antenna and strap), the crystal disc Ø 0.050 × 6 mm (overall 0.0545 × 0.0607 × 0.0072 with
  the bezel and tab).
- **Strand's mark in `key_strand` is openwork** (the ring and meridian are the metal left standing in the
  open bow). Cutting a ring plus a meridian *as holes* would free the inner disc, so "pierced" is read as
  pierced openwork. Leyla's sign in `key_leyla` *is* cut as holes. `key_strand` has a hanging eye for the
  cradle hook; `key_leyla` has none (the cradle rests it on pins).
- **`index_card` has a catalogue-rod hole** (bottom centre), because `index_card.png` draws one.
- **`glass_slide` has no separate card mask:** `slide_mark.png` already paints the black mount with its round
  window, so a 3D mask would hide the decal's ✦ corner spot. The card mount is therefore the decal; the tape
  edges are 3D.
- **`tuning_knob` turns about local +Z** (the contract only names it).
- `pocket_receiver` meter: bar marks sit exactly on the needle angles for bars 1..5 (24, 8, −8, −24, −40°);
  bars 0 = the rest dot at +40°.

## Notes for the game code

- `ItemDB.FLAT`: add **`tape_1996`, `tape_1997`, `tape_1998`** (the reel lies face up; without the 70° tilt
  the icon and inspect view show its edge). Every other item already matches: flat = badge, both cards,
  file, slide, both keys, locker key; standing = receiver, film reel, crystals.
- `ItemDress` names all exist: `label` (tape_reel), `crystal_face` (lumen_crystal), `hole_0..7`
  (request_card, all visible by default).
- `M_Decal_Badge`, `M_Decal_RequestCard` and `M_Decal_FileCover` are opaque, and their meshes are cut to the
  printed shape, so no transparent decal pixel is ever on screen. `M_Decal_IndexCard` and
  `M_Decal_TapeLabel_*` use alpha scissor; their holes are also cut in the meshes.
