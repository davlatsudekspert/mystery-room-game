# CC0 Dressing Props (Poly Haven) — Laboratory 7

Secondary **dressing** props that raise realism around the procedurally modelled hero and interactive objects. None of them is interactive or puzzle-critical. All are Poly Haven models under **CC0 1.0**; the licence register is `docs/ASSET_LICENSES.md`.

- **Files:** `game/assets/models/cc0/<id>/<id>.glb`. Each is a single binary glTF with its 1K JPG textures embedded (albedo, OpenGL normal, ARM = AO/roughness/metal).
- **Rebuild:** `python3 tools/models_cc0/fetch_cc0_models.py [--only <id> ...] [--qa]`. It re-downloads, re-converts and, with `--qa`, re-renders the contact sheet.
- **QA contact sheet:** `qa/cc0_props_contact_sheet.jpg`. Cycles CPU, 32 spp, 512 px per prop in a neutral grey studio, plus two lines of props at real scale on checker floors.

## Props

All values are in **Godot axes** (Y up, metres). The bounding box is **W (X) × H (Y) × D (Z)**. Placement coordinates refer to `docs/ROOM_LAYOUT.md` and are suggestions only; the lead places and rotates the models in Godot.

| id | bbox W × H × D (m) | tris (source → final) | .glb MB | Suggested placement in Lab 7 |
|---|---|---|---|---|
| `vintage_microscope` | 0.106 × 0.400 × 0.182 | 20,631 → **5,998** | 1.91 | Lab bench top, in the free span between the vial rack and the radio, ~(−0.35, 0.92, 2.30). `lab_bench.glb` lists a microscope, so this one can replace it |
| `vintage_spacecraft_instrument` | 0.410 × 0.270 × 0.204 | 13,279 → **6,000** | 2.72 | A shelf of the worn metal rack, or the top of the filing cabinet. Keep it away from the radio |
| `retro_multimeter` | 0.216 × 0.279 × 0.203 | 8,948 → **3,997** | 1.28 | Floor or a crate under Panel 7, ~(2.70, 0, −1.30), with the leads toward the panel. Alternatively a shelf of the metal rack |
| `book_encyclopedia_set_01` | 0.551 × 0.237 × 0.163 | 67,282 → **5,979** | 1.02 | A shelf of the metal rack, or the top of the filing cabinet. **Not** the bookshelf door (see cautions) |
| `magnifying_glass_01` | 0.132 × 0.027 × 0.272 | 7,240 → **2,500** | 0.36 | Desk top, east of the notebook, ~(0.00, 0.78, −1.95) |
| `round_spectacles` | 0.158 × 0.046 × 0.149 | 11,810 → **2,500** | 1.81 | Desk top, beside the notebook (not on it), ~(−0.05, 0.78, −2.10) |
| `seadogs_compass` | 0.081 × 0.087 × 0.150 | 11,645 → **4,997** | 2.52 | Bookshelf (not the clear spot on shelf 3), or the window sill |
| `tea_set_01` | 0.387 × 0.165 × 0.268 | 40,296 (19,180 kept) → **3,998** | 1.44 | Desk east end, ~(0.10, 0.78, −2.25). This is the story's "cup of tea, dried to a ring". The teapot is its own node and can be moved apart |
| `vintage_electric_kettle` | 0.321 × 0.305 × 0.248 | 14,838 → **3,999** | 2.13 | Stone window sill (north wall, x 0.95–2.05, y ≈ 1.45), or beside the radiator |
| `vintage_wooden_drawer_01` | 0.858 × 0.545 × 0.457 | 5,184 → **5,184** | 0.76 | North wall, between the filing cabinet and the desk, ~(−1.85, 0, −2.27), facing +Z |
| `metal_stool_02` | 0.448 × 0.458 × 0.473 | 6,532 → **6,532** | 2.54 | In front of the lab bench, ~(0.15, 0, 1.60). The seat is 0.46 m high, so it reads as "pushed aside". It stays below the Lumen beam (y 1.15) |
| `worn_metal_rack` | 0.915 × 1.900 × 0.600 | 6,372 → **6,372** | 2.01 | East wall, south of the door, centre ~(2.70, 0, 1.95), facing −X. Check clearance to the wall safe and mirror A |
| `old_gas_mask` | 0.212 × 1.126 × 0.309 | 18,900 → **3,999** | 1.89 | A free hook on the coat rack at (2.6, 0, −2.15). **Origin is the hook point (top)**; the hose hangs 1.13 m below it |
| `marble_bust_01` | 0.272 × 0.515 × 0.300 | 17,456 → **4,000** | 0.59 | Top of the filing cabinet (−2.6, top, −2.2) |

**Totals:**
- 14 props, **66,055 tris** if every prop is placed (source total: 229,297 tris)
- **22.97 MB** of `.glb` on disk
- Godot's import also extracts the embedded textures next to each `.glb`, which adds about 19.7 MB of `*_1k.jpg` and `.import` files. That is standard Godot 4 glTF behaviour.

**Budget note:**
- Whole scene: ≤ 150k tris (ART_DIRECTION).
- Hero props: ≤ 6k; small items: ≤ 2.5k (ROOM_LAYOUT).
- Every prop here is ≤ 6.6k, and the desk-top small items are 2.5–5k.
- Placing all 14 costs about 66k tris. Choose the subset the frame needs, as the "Restraint" pillar asks; 6–8 props is about 35–45k.
- Godot generates mesh LODs on import, which cuts the distant cost further.
- Targets are one value per prop in `ASSETS` in the fetch script.

## Chapter 3 placements
Two of these props also dress Leyla's camp in Chapter 3 (placed by `UndergroundData.DRESS_CC0`, merged into one mesh by `ModelUtil.merge_static`, no colliders, no shadows, drawn only in the camp's own views):
- `old_gas_mask` at (4.585, 1.80, −3.40), yaw 90 (its hook point on the camp's west wall, north of the crystal shutter; the hose hangs to y 0.67);
- `seadogs_compass` at (6.09, 0.42, −2.93), yaw 25 (on the crate table beside the storm lantern).

## Orientation, pivots and scale
- **Scale:** real-world metres. Dimensions match Poly Haven's published `dimensions` to within 1 mm. glTF +Y is up.
- **Front:** the authored front faces glTF +Z (Blender −Y), matching the `ROOM_LAYOUT.md` convention.
- **Pivot:** every prop rests on y = 0 (base at the origin height), except `old_gas_mask`. That model is authored hanging, so its origin is its top, the hook point.
- **Source pivots that were fixed:**
  - `vintage_spacecraft_instrument` and `round_spectacles` had their origin at the bounding-box centre. They are now grounded.
- **Baked rotation:**
  - `magnifying_glass_01` was authored standing on its handle. It was rotated to lie flat with the lens up for desk placement.
- **Multi-node props:**
  - `tea_set_01`: `teapot_01`, `teapot_01_lid`, `cup_small_01`, `saucer_circular_04`. The cup is dropped onto its saucer.
  - `vintage_wooden_drawer_01`: the body plus 6 drawer nodes. The drawers can slide in Godot for flavour.
  - `vintage_microscope`: 8 parts.
  - `seadogs_compass`: body, lid and needle.
  - `retro_multimeter`: 7 parts.
  - `book_encyclopedia_set_01`: 20 books.

## Conversion pipeline (`tools/models_cc0/`)
| File | Role |
|---|---|
| `fetch_cc0_models.py` | Orchestrator, Python stdlib only. For each prop it: <ul><li>reads `api.polyhaven.com/info` (authors) and `/files` (glTF 1k list and md5)</li><li>checks that `polyhaven.com/license` and the asset page state CC0</li><li>downloads into a **fresh directory per asset** and verifies md5</li><li>runs Blender headless</li><li>writes `cc0_models_report.json` (tris, bbox, authors, sizes)</li></ul> With `--qa` it also renders and composes the contact sheet with Pillow |
| `convert_gltf_to_glb.py` | Blender script. Steps, in order: <ul><li>import with merged vertices</li><li>optional object subset, moves and drop-onto (tea set)</li><li>Decimate (collapse) to the target; objects under 300 tris are untouched; decimated objects get smooth-by-angle normals (40° default; 50–80° for organic or porcelain shapes); untouched objects keep their authored normals</li><li>optional baked rotation</li><li>pivot normalisation</li><li>glass fix</li><li>GLB export with the JPGs embedded byte-for-byte</li><li>ORM occlusion patch</li></ul> |
| `render_qa.py` | Blender Cycles QA renders: one tile per prop, plus desk-scale and floor-scale lines of props at real scale |
| `cc0_models_report.json` | Machine-readable result of the last run |

**Fixes applied during conversion:**
- **Glass would have rendered opaque in Godot.** The source glass materials are either alpha-BLEND with an RGB JPG as base colour (alpha 1), or `KHR_materials_transmission`, which Godot ignores. Either way the multimeter dial, the instrument's globe and the kettle gauge would have been hidden behind opaque glass. The `*_glass` / `*_lense` materials now use a constant alpha of 0.18 and low roughness. Godot imports them as alpha-blended with a depth pre-pass. The transmission extension is kept for other renderers.
- **Baked AO.** Poly Haven ARM maps pack AO in the R channel, but the source glTF never references it. Each material that uses an ARM map now also points `occlusionTexture` at it, which is standard glTF ORM packing. Godot picks it up as `ao_texture`, which suits ART_DIRECTION's "fake AO baked into textures".
- **Tea set.** The 10-piece set is reduced to teapot + lid and one cup on its saucer, re-laid out compactly. The source lays every piece out in a grid.

**Verification (2026-10-08):**
- **Decimation quality:** A/B Cycles renders, source against output at close range, of the spectacles, compass, microscope, gas mask, multimeter, books, bust and tea set show matching silhouettes. At 3.5k the compass bail ring looked polygonal, so the compass target was raised to 5k.
- **Godot import:** all 14 `.glb` imported in Godot 4.7.2 (`--headless --import`, Mobile renderer, in a throwaway project) with no errors or warnings. A headless check confirmed:
  - mesh counts and tri counts as above
  - the albedo texture present
  - AO enabled on ARM materials
  - glass materials at alpha 0.18 with a transparency mode

## Cautions for level design (fairness and art direction)
- **Encyclopedia puzzle:**
  - The bookshelf door holds the puzzle encyclopedia `IA_book_1..9`: dark green, with Roman numerals.
  - `book_encyclopedia_set_01` is brown with lettered "ENCYCLOPEDIA" spines (A, B, C…).
  - Keep it **off the bookshelf door and away from it**, so players do not try to pull those books.
- **Look-alike devices:**
  - `vintage_spacecraft_instrument` (knobs, counters, a globe) and `retro_multimeter` look operable.
  - Keep them off the radio and Panel 7 interaction spots, and do not give them a tap highlight.
  - Optionally add a one-line flavour inspect text, so players learn they are scenery.
  - The instrument's Cyrillic labels ("ПЕРИОД", "ВИТКИ") fit the Soviet-era setting and carry no puzzle information, so the language-neutral rule holds.
- **Bright materials:**
  - `marble_bust_01` and `tea_set_01` are near-white porcelain and marble, and ART_DIRECTION says to avoid pure white.
  - In-game they will sit in dark values. If they still pop, multiply albedo to about `enamel_cream` (#E8DFC8) with a material override in Godot.
- **Beam path:** keep props out of the Lumen beam path, which runs at y ≈ 1.15 from the projector (−2.3, 1.6) to mirror A (1.6, 1.6), then to mirror B (1.6, 0.12), then to the sensor.

## Not available as CC0 on Poly Haven (to be modelled procedurally)
The following were searched for and have no suitable Poly Haven model:
- coat rack
- globe
- typewriter
- radiator
- rug
- period telephone

`coat_rack` and `radiator` are already in the procedural plan.

**Rejected Poly Haven candidates, with reasons:**
- **Modern look or visible branding:** `desk_lamp_arm_01` (orange modern anglepoise), `wall_clock` (modern, with a brand mark), `Television_01` (brand logo), `modified_thermos` and `plastic_thermos` (brand labels), `Camera_01` (rangefinder with logos), `vintage_stapler` (bright teal office stapler with a label plate, off-palette).
- **Clutter with branded glassware:** `chemistry_set` has 42k tris, and the cylinder and beaker carry maker marks. The vials are hero props anyway.
- **Too ornate or the wrong period:** `vintage_cabinet_01`, `ClassicConsole_01`, gothic furniture, `mid_century_lounge_chair` (recognisable designer piece).
- **Duplicates a hero object:**
  - `standing_chalkboard_01`
  - `filmstrip_projector_8mm` (would compete with the Lumen projector)
  - the clocks: `mantel_clock_01` and `alarm_clock_01` (the stopped flip clock is the story clock; every clock must read 03:17)
  - `vintage_radio_transceiver` (the radio is a puzzle device)
- **Off-theme:**
  - `metal_trash_can` (outdoor)
  - military crates
  - `vintage_suitcase` (travel stickers)
  - `decorative_book_set_01` (modern colourful spines, 112k tris)

## Kenney evaluation (CC0): rejected
- **Packs reviewed:** Kenney **Furniture Kit** (140 models, CC0, https://kenney.nl/assets/furniture-kit) and **Survival Kit** (80 models, CC0, https://kenney.nl/assets/survival-kit). Previews were checked on 2026-10-08.
- **Licence:** fine (CC0).
- **Style:** the kits are flat-shaded, untextured low-poly models with saturated flat colours (red sofas, blue chairs, orange wood) and simplified, toy-like proportions.
- **Conflict with ART_DIRECTION:** that clashes with the "realistic premium" look and with three items on ART_DIRECTION's "What to avoid" list:
  - untextured primitives
  - cartoon proportions
  - saturated primary colours
- **Coat rack:** the Furniture Kit does include a coat stand, the one item Poly Haven lacks. Next to scanned PBR props it would still read as a placeholder, so the coat rack stays procedural.
- **Result:** no Kenney asset is used.
