# Quality report

Scores are on a 10-point scale and come only from evidence: real Godot screenshots, automated 3D playthroughs, tests, and performance numbers. **No human player has played the game yet.** Fun, clarity and the emotional impact are therefore *estimates* until playtesters report. A 10 is never given without a real player's or a real device's confirmation.

All screenshots and frame counts come from the software renderer in the dev container (lavapipe under Xvfb, no GPU). Colours and timing on phones will differ.

## How each criterion is judged
| # | Criterion | Evidence used | What a higher score needs |
|---|---|---|---|
| 1 | 3D graphics and atmosphere | Real Godot screenshots (`docs/previews/`) | Phone screenshots and device lighting checks |
| 2 | Original puzzles | Design docs, logic tests, solver and real-tap playthroughs | Playtesters solving them without hints at the intended pace |
| 3 | Story and emotional impact | Text beats, the WOW-moment list, screenshots | Player feedback |
| 4 | Mobile controls | Tap maps (`qa/tap_map.tscn`), playthrough fallbacks | Real-finger tests on phones |
| 5 | Text readability and UX | UI screenshots at phone sizes, the layout-fit test | Device checks at 50 % brightness |
| 6 | Sound and animation | Rendered audio checked by measurement; animated sequences in screenshots | Listening on phone speakers and headphones |
| 7 | FPS and performance | Draw calls and primitives per view (software renderer) | FPS measured on a mid-range Android phone |
| 8 | Error-free play | Tests, no-softlock fuzz, real-tap playthroughs on several seeds | A human run without blockers |
| 9 | EN/RU/UZ quality | The string validator, font coverage, localized decals, screenshots | Native-speaker review |
| 10 | Commercial readiness | Store setup, signing, privacy, `docs/BUSINESS_STRATEGY.md` | A store-approved internal test build |

## Chapter 1 — The Locked Laboratory (2026-10-09)
| # | Score | Evidence | Main gap |
|---|---|---|---|
| 1 | 7.5 | Lab and darkroom screenshots. The unpowered lab is now readable (`docs/previews/ch1_dark_state_before_after.jpg`) | Some props are plain; there are no phone captures |
| 2 | 8 | 12 linked puzzles. Real-tap playthrough: 13/13 steps, 0 fallbacks. Per-game variant answers for the gear box, safe cipher and beacon | Unproven with players |
| 3 | 7 | Intro, flashback, the echo turning toward you, the 1979 postmark | Unproven with players |
| 4 | 7 | Player review: all objects reachable; drawer/mirror aiming issues were test artefacts | No real-finger test yet |
| 5 | 6 | The owner reports small text on phones. A UI audit with auto text scaling is in progress | Being fixed |
| 6 | 7 | 40+ synthesized sounds and a music cue | Not heard on a device |
| 7 | 6 | ~94–99 draw calls, ~175–183k primitives (target 150k) | No FPS measured on a phone |
| 8 | 8 | Tests (87 tests, 7216 checks), a 300-seed fuzz and 60-seed variant tests pass | No human run |
| 9 | 8 | All text through tr(), with RU/UZ checked by screenshots | No native-speaker review |
| 10 | 6 | Play Console app created, declarations mostly done, privacy policy live, upload key ready | No AAB in internal testing yet |

## Chapter 2 — The Missing Scientist (2026-10-09)
| # | Score | Evidence | Main gap |
|---|---|---|---|
| 1 | 8 | Archive, booth, film and vault screenshots (`docs/previews/ch2/`) | The film's on-screen image is a little dim; no phone captures |
| 2 | 8.5 | 12 puzzles + P11b on two Ch1 paths; 0 fallbacks on both (86 and 78 taps). Variant answers for the valves, punch card, tape clicks/dial, splice order, focus and vault overlay | Unproven with players |
| 3 | 7.5 | The voice diary, the 1979 film, Leyla's echo, the 42nd silhouette, the key choice | Unproven with players |
| 4 | 8 | Tap maps and the first-time-player review found and fixed: covered cards and dividers, a blocked hatch, an unreadable diagram, a too-low projector view, and the catalogue that could not be reached from the hall (now a hanging sign and walking) | No real-finger test yet |
| 5 | 6 | As for Chapter 1 (UI audit in progress) | Being fixed |
| 6 | 7 | 42 sounds, an ambience and 2 music cues, checked by measurement and spectrogram | Not heard on a device |
| 8 | 6 | Hall view: **144 draw calls, ~86k primitives** (was 198 / 126k; budget 150 / 150k). The `tap_map --breakdown` QA tool found that the floating dust, as a moving shadow caster, made the spot light redraw its shadow map every frame: 30 draw calls. Dust no longer casts shadows (Ch1 and the menu gain too). Shelf contents and the book row now draw as one mesh each (`ModelUtil.merge_static`). Stacks view 106, desk 67 | FPS on a phone |
| 8 | 8 | Tests pass; real-tap playthroughs pass on both paths and on a variant seed (in progress) | No human run |
| 9 | 8 | Localized decals (badge, cards, rules, labels) in EN/RU/UZ | No native-speaker review |
| 10 | 6 | Released in the chapter list (paid bundle; tester builds open it). Player review: 1 small UI issue left | Real payments and store review |

## 2026-10-10 update: 3D light and player-QA pass (Chapters 1 and 2)
Only the criteria that moved. Evidence: the same seed played before and after through the real scene (Ch1 seed 4242, Ch2 seed 777 leave path), frame statistics (mean luminance and the share of pixels clipped to white), tap maps, and the new headless feedback audit (`qa/feedback_audit.tscn`). Before/after pairs: `docs/previews/quality/`.

| # | Chapter | Score | Evidence | Main gap |
|---|---|---|---|---|
| 1 | Ch1 | 7.5 → **8** | Glow 0.6/0.05/1.1 → 0.4/0/1.35 and emissives 3.5–4.0 → 2.2–2.6: the panel's jewel lamps, bulbs and the projector lens no longer bloom into white discs; the dark lab is unchanged (mean 37.8 → 37.5); the powered lab keeps its pendant-and-shadow mood (`ch1_lab_powered_before_after.jpg`, `ch1_panel_before_after.jpg`) | The beam is still a bright tube at energy 1.05 (3.1 % clipped); the regression run at 0.75 is pending. Software renderer only, no phone captures |
| 1 | Ch2 | 8 → **8.5** | Splicer light box 11.8 % → 0.1 % clipped; the film view's white haze is gone and the picture is the brightest thing (`ch2_film_before_after.jpg`); hall pendants no longer blots | The dial close-up still clips 15 % on the polished brass plate (a satin override is in the next run); the slide field clipped 21 % (shader fix pending its run) |
| 4 | Ch1 | 7 → **7.5** | Feedback audit: 48 taps in 9 puzzle states, 0 silent. Tap maps of 27 views: every puzzle part green; the only red/orange marks are parts hidden by design (a closed compartment, rings seen edge-on). Panel 7's lever and lamps clear the HUD. Drawer wheels and safe keys grew from ~4–5 mm to ~8 mm on a 6" phone (two-state close-ups). Radiator and sculpture got tap areas | No real-finger test; darkroom-stage tap maps pending |
| 4 | Ch2 | 8 → **8.5** | Feedback audit: 40 taps in 6 states, 0 silent (no pressure, no card, no reel, locked, emptied, unlocked). Dial holes and punch keys ~7 mm on a phone (were ~5) | Full tap map of 30 views pending in the render queue; no real-finger test |
| 6 | both | 7 → **7.5** | Every tap now has an audible answer (a tick for solved wheels, a rattle for locked doors, a soft tap for scenery), from the existing synthesized set | Not heard on a device |
| 7 | Ch1 | 6 | Measured in this pass: 130 draw calls (dark) / 136 (powered), 112–117k primitives, under the 150k primitive target; the draw-call count rose with the HUD redesign's inventory column | FPS on a phone |
| 7 | Ch2 | 6 → **5.5** | Hall view 166 draw calls (budget 150; it was 144 before the aisle sign and the HUD column), ~86k primitives | A `--perf --breakdown` run is queued to name the extra draws |
| 8 | both | 8 | Ch1 seed 4242: 100 taps, 0 fallbacks before and after; Ch2 seed 777 leave: 94 taps, 0 fallbacks before and after. 102 tests pass on main plus these changes | More seeds and both player reviews are queued behind other agents' renders |

## 2026-10-10 owner-feedback round: HUD overlap, Panel 7, the safe chain (Chapters 1 and 2)
The owner played Chapter 1 on an Android phone. Evidence: `tap_map --hud-check` at 19.5:9, 20:9, 16:9 and 4:3 (rules and result lines in `docs/GAMEPLAY_QA.md`), both playthroughs on the final code, 151 headless tests, before/after frames in `docs/previews/quality/` (`ch1_panel7_framing_*`, `ch1_panel7_powered_before_after.jpg`, `ch1_poster_before_after.jpg`, `ch1_notebook_p4_icons_en_ru_uz.jpg`, `ch1_poster_vs_uv_glyphs.jpg`).

| # | Chapter | Change | Evidence | Main gap |
|---|---|---|---|---|
| 4 | Ch1 | Panel 7's close-up fits the area the HUD leaves free: the icons, lamps, switches, main lever and its 0 / 1 plate are all on screen and clear of every corner button at the four screen shapes | `--hud-check`: 0 failures in all 36 Ch1 views at 19.5:9 and 4:3 (after reframing the shadow and radio-hatch views); the panel view 0 failures at 20:9 and 16:9 | Not tried with a real finger on the owner's phone |
| 4 | Ch1 | The safe code chain is pointed at from three places: the UV page line, hint 1 and hint 2, and the poster is fitted whole in its close-up with 4.3:1 ink contrast (was 2.1:1) | The poster's 10 cells match the 10 UV glyphs (`ch1_poster_vs_uv_glyphs.jpg`); `test_safe_chain.gd` | The reader's picture is small on a 19.5:9 phone at the largest text size (pinch or double-tap zooms); owned by the UX pass |
| 5 | Ch1 | Notebook page 4 shows the panel's four icons next to LOCK, LIGHT, ARRAY and VENT in EN, RU and UZ | `ch1_notebook_p4_icons_en_ru_uz.jpg` | |
| 4 | Ch2 | Every view checked for HUD overlap at 19.5:9 and 4:3 | Result lines in `docs/GAMEPLAY_QA.md`: 0 failures | The locker view shows slivers of locker 7 and 11 at the screen edge, the vault-ports view a sliver of the wheel (scenery, reported) |
| 8 | both | Ch1 seeds 4242 and 1337, Ch2 seed 777 on both lens paths | 100 / 101 / 94 / 86 taps, 0 logic fallbacks, 0 taps under a HUD control | `Lambda capture at index 0 was freed` is logged once or twice per playthrough (all four runs) when several items fly into the bag at once (`hud.gd` `_fly_to_bag`, the UX pass's code); harmless, but noisy |

## Fixes found by QA in this round (see `docs/GAMEPLAY_QA.md`)
- Chapter 2 crash on every "use item" tap: `ItemDB.is_tool` clashed with Godot's `Script.is_tool()`.
- The projector beam rendered as a floor-to-ceiling slab.
- The vault overlay turned the sign the wrong way.
- The dial holes became untappable (a regression), caught by the tap map before release.
- The catalogue's tiny card tabs, covered dividers and a section hidden in the carcass.
- The compressor diagram was unreadable.
- A locker door blocked the floor hatch.
- English words were baked into decals.

## 2026-10-10 performance: HUD draw calls (all chapters)
The in-game HUD cost about 60 draw calls in every 3D view (Chapter 3's `choir_s` was at 145 of 150, Chapter 4's hall plans about 90 scene calls). Method: `tap_map --perf --hud-breakdown` (new: the view with the HUD shown and hidden; the HUD with the 3D room hidden, so only the 2D canvas draws; the calls each HUD node adds when hidden in turn; every visible HUD node that breaks batching) and `--hud-states` (new: the HUD in the states a player meets). Screen: `--screen=phone61`, 2340x1080 at 400 dpi, text scale 2.54 (a 6.1" phone at Normal). Both columns come from the same scenes; the scene part (HUD hidden) is identical before and after (lab 103, bench 123, hall 147, booth 68, choir_s 89).

### Totals per view
| View | Before: view / HUD adds | After: view / HUD adds | HUD alone, 3D hidden (before → after) |
|---|---|---|---|
| Ch1 `lab` (room view, no Back) | 137 / 34 | 106 / 3 | 35 → 4 |
| Ch1 `bench` (close-up, Back, title) | 180 / 57 | 130 / 7 | 58 → 8 |
| Ch2 `hall` (room view, title, bag count) | 197 / 50 | 154 / 7 | 51 → 8 |
| Ch2 `booth` | 128 / 60 | 76 / 8 | 61 → 9 |
| Ch3 `choir_s` (`--until=case_open`) | 149 / 60 | 97 / 8 | 61 → 9 |

The HUD adds 3 to 8 calls in a normal room view (budget 20; the "HUD alone" column also counts the one call an empty canvas has). `choir_s` in the `case_open` state is 97 of 150 (it was 149); the other `choir_s` states in `GAMEPLAY_QA.md` (worst case 145 with the old HUD) were not re-measured.

### Which HUD nodes cost what (Ch1 `bench`, Ch2 `hall`, Ch3 `choir_s`; before → after)
| Node | Before | After | Why it cost that |
|---|---|---|---|
| Back / Hint / Pause bezel button | 10 / 11 / 8 | 1 / 1 / 1 | disc (1), two antialiased rings (3 each), the icon's antialiased arcs and polylines (3 each) and polygons (1 each); only the plain lines batched |
| Bag button | 15 (18 with items) | 1 (+1 for the count's digits) | the same, plus the count's two discs and the hand ring |
| Title banner | 13 in the per-node pass (its label 2 to 6) | 3 (1 mesh, 2 for the label: outline and fill) | each gradient and rect of the band was a polygon of its own |

### What breaks 2D batching in this engine build (Godot 4.7.2, measured in a scratch scene, 640x360, calls per primitive)
| Drawn with | Calls |
|---|---|
| 5 `draw_rect` in a row / 5 `draw_line` of any width, antialiased or not / 5 `draw_texture_rect` of one texture | 1 in total |
| `draw_circle`, `draw_colored_polygon`, `draw_polygon` with vertex colours | 1 each |
| `draw_arc` or `draw_polyline` antialiased | 3 each (without antialiasing 1) |
| rects alternating with circles (5 each) | 10 (every change of kind starts a call) |
| a rect, a textured rect, a rect | 3 (a texture and the plain white pixel do not batch) |
| two textures alternating (6 rects) | 6 |
| a Label with an outline (`outline_size` 3 or 4) | 1 or 2, depending on whether outline and fill glyphs share an atlas page; the HUD's title label is 2 and 1 without its outline; a two-line message banner is 5 in all (1 mesh + the text) |
| a `StyleBoxFlat` panel, rounded, bordered, with or without a shadow; `clip_contents` | 1 |
| an item with `modulate.a = 0` | 0 (skipped, so a faded banner costs nothing: the HUD is 5 again after a message and a caption have faded) |
| `draw_mesh` with vertex colours, two meshes | 2 |
| a transparent SubViewport used as an atlas | not used: its pixels are stored premultiplied (a (1, .8, .3, .8) disc reads back (.8, .64, .24, .8)), so every item drawing it would need a premultiplied material |

The HUD has no per-button ShaderMaterial, no `clip_contents` outside the tray's scroll box, no shadow `StyleBox` and no `Label` shadow; the cost was the number of separate primitives.

### What changed
- New `game/src/ui/ui_mesh.gd` (`UIMesh`): collects rects, gradients, polygons, discs, antialiased strokes (0.5 px alpha ramp, mitered joins, butt ends) and arcs into one vertex-coloured mesh drawn with one `draw_mesh()`.
- `IconButton._draw`, `UIBanner._draw` and `UIOrnament._draw` build one `UIMesh` each instead of 7 to 18 `draw_*` calls. The count's digits and an item picture in hand stay separate draws (a font atlas and a texture cannot join a mesh): a bezel is 1 call, 2 with the count, 3 with a picture and a count.
- Same shapes, sizes, colours and alpha ramps, same code paths (every `draw_*` call has its `UIMesh` equivalent next to it). Overlays (UV page, notebook, hints, pause) use the same buttons and ornaments; their layout is untouched and their draw calls were not measured.
- QA: `tap_map --hud-breakdown`, `--hud-states`; `game/tests/test_ui_mesh.gd` (geometry of the mesh, every icon in every state, the banner's mesh stays inside the banner).

### Visual check (unchanged look)
`docs/previews/ui/perf/{en,ru,uz}_{normal,xl}_before_after.jpg`: 19.5:9 (the owner's iPhone, 2556x1179), Normal and Extra large; each sheet is the bare HUD, the busiest HUD (title, caption, message, prompt, meter, bag count, item in hand) and a found-item banner, before on the left and after on the right. Pixel difference before/after over the whole frame: mean 0.1 to 1.0 of 765 per pixel, 21 to 750 pixels (of 3.0 million) differ by more than 96; the difference map (x4) shows mostly 3D scene edges and a faint shading of the banner bands, nothing visible at full size.

### HUD in the states a player meets (Ch1 `lab`, 5 items in the bag, `--hud-states`, 3D room hidden so the numbers include the empty canvas's 1 call; before → after)
| State | Calls |
|---|---|
| as it is (3 corner buttons, count) | 38 → 5 |
| + a two-line message | 49 → 10 |
| the found-item banner instead | 58 → 13 |
| + a caption | 67 → 16 |
| + a prompt, item in hand | 72 → 21 |
| + the bag open (tray with 5 slots and the item actions) | 116 → 33 |
| after the message and caption have faded | 38 → 5 |

Main gap: with the tray open each slot still costs 2 (its rounded frame, and its item icon, which is a texture of its own), so a player who leaves the bag open at room views has about 8 + 2 per item + 3 calls; the busiest state of `test_hud_layout` (everything at once) is 33. Merging the slot frames into one mesh layer and packing the item icons into one atlas would make the tray constant; not done, because it changes how slots take taps and `ItemIcons` renders each icon into its own texture. Font outlines cost one call per text line; they stay because the look must not change.

### Checks on the final code
- `tools/run_tests.sh`: `204 tests, 28581 checks, 0 failures (57993 ms)` (36 layout combinations, bag, back, hint and store tests included; `test_ui_mesh` is new). `godot --headless res://qa/check_scripts.tscn`: `checked 118 scripts, 0 broken`.
- `tap_map --chapter=ch1 --hud-check --screen=phone61` on the 36 Chapter 1 views: `hud-check (phone61): 93 controls in 36 views, 0 failures, 13 banner warnings (80 focus-only controls and 0 slivers not checked)`, the same line as before the change.
- Chapter 1 playthrough, seed 4242, on the final code: all steps pass, `Lumen shards 5/5`, `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`, `taps under a HUD control: 0 (window 1920x1080)`.
- Also fixed in this pass: `test_hud_uv.test_the_lamp_strikes_on_the_page` waited a fixed real-time 0.9 s for a 0.63 s tween and failed once at load average 12; it now waits for the light itself (`HudTestRoom.wait_until`, frame by frame, 20 s cap that only a hang reaches), passing 3 of 3 alone and under 8 busy loops.
