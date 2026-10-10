# Gameplay QA

How each chapter has been checked. The five status levels are never mixed:

| Level | Meaning |
|---|---|
| **IMPLEMENTED** | The code or asset exists. |
| **INTEGRATED** | It is wired into the real game scene and reachable by a player. |
| **AUTOMATED TESTED** | A script exercised it and checked the result: logic tests, or real raycast taps through the 3D scene. |
| **VISUALLY VERIFIED** | Someone looked at real Godot screenshots of it (not Blender renders). |
| **HUMAN TESTED** | A person played it on a device. |

**Not HUMAN TESTED yet.**
- The first phone run, on the owner's iPhone with TestFlight build 2 on 2026-10-09, reached the main menu, which works. New Game then crashed while loading Chapter 1 (docs/TESTING_ON_DEVICE.md, "Device reports"). No chapter has been played on a device yet.
- Automated play proves a chapter can be finished and does not break. It does not prove the chapter is fun or clear; only playtesters can tell us that.

**Regression runs** (real 3D scene, solver-driven taps; exit 0 = no failed step and no logic fallback):

| Date | Change under test | Chapter 1 | Chapter 2 |
|---|---|---|---|
| 2026-10-09 | camera feel (smooth follow, glide, arcs), dust without shadows, merged shelf meshes, crash recovery, launch/name fixes | seed 4242: all steps ✓, 100 taps, 0 fallbacks | seed 4096, leave path: all steps ✓, 83 taps, 0 fallbacks |
| 2026-10-10 | light pass (glow, emissives, beam haze, splicer box, camera fill), feedback for every tap, Panel 7 re-framed, radiator and sculpture tap areas, drawer / safe / dial / punch close-ups brought in | seed 4242: all steps ✓, 5/5 shards, 100 taps, 0 fallbacks (before and after the light changes) | seed 777, leave path: all steps ✓, 94 taps, 0 fallbacks (before and after) |

All screenshots come from the software renderer in the dev container (lavapipe, no GPU), so colours and frame rate are only indicative of phones.

---

## Chapter 1 — The Locked Laboratory

### Tools
| Check | Command | What it does |
|---|---|---|
| Logic tests | `tools/run_tests.sh` | Puzzle rules, hints, save/load, localization, layout fit, a 300-seed random-play fuzz for softlocks and lost items |
| Solver playthrough | `qa/playthrough.tscn` | Plays every puzzle by tapping the projected screen point of each part. The tap goes through the same raycast → hotspot → logic path as a finger. A step counts only when the expected state change happens. Any logic fallback is a failure |
| Player review | `qa/player_review.tscn` | Plays like a first-time player: the intro, looking around and tapping everything in the dark, wrong attempts, hints, the documents, a language switch, quit and continue, the finale |
| Lighting probe | `qa/view_probe.tscn --cam=…` | Renders fixed camera angles to compare lighting before and after a change |
| Tap map | `tools/qa_run.sh -- res://qa/tap_map.tscn -- --chapter=ch1 --views=… [--until=shelf_open] [--perf --brightness=0.7]` | Marks every tappable part in a view: green = reachable, orange = small, red = covered, and names what a tap hits instead (works for Chapter 1 since 2026-10-10: the room exposes `raycast`/`resolve` like RoomBase). `--brightness` renders at a Settings slider value |
| Feedback audit | `godot --headless --path game res://qa/feedback_audit.tscn -- --chapter=ch1` | Taps 48 mechanisms and pieces of scenery in their own views, in the puzzle state each belongs to (locked, not yet, solved, emptied), through the real raycast, and checks that each tap answered with a message, caption, sound, camera move, document or state change. Headless: no render slot needed |

### What the 3D QA found and fixed (2026-10-10, light and feedback pass)
| Problem | Effect on a player | Fix |
|---|---|---|
| Panel 7 close-up framed from 0.88 m: the main lever's handle sat under the bottom HUD bar and the lamps under the title plates | A finger could not reach the main lever in its own view (the solver's taps bypass the HUD, so earlier runs passed) | The camera stands 1.15 m back at fov 54: handle and lamps clear the HUD at both ends (`docs/previews/quality/ch1_panel_before_after.jpg`) |
| The shadow sculpture's ring and rod had no collider | A tap on the sculpture itself fell through to the wall; only its two small knobs reacted | Box tap areas on the ring and the rod; from the shadow view they open the sculpture close-up |
| The radiator was part of the static shell | No way to reach the low radiator view, where a Lumen shard hides between its feet, except a lucky UV sweep from across the room | A tap area on the radiator with its own view and caption |
| 17 taps answered with nothing: the stopped clock, the desk top and its side, the shut gear-box lid, the shut safe door, the panel's lamps, the bench, the coat, the filing cabinet, the window, the door's eye, the projector's empty socket, the sculpture body, emptied containers, solved wheels and keys, the bookcase after it swung open, the projector lever while the beam is on | The player could not tell a wrong idea from a tap that did not register | Each answers with a short line (13 new EN/RU/UZ keys) and/or a sound; emptied containers say "Empty now."; solved wheels and keys tick quietly. Checked by the feedback audit: 48 taps, 0 silent |
| Glow 0.6 / bloom 0.05 / threshold 1.1 with emissives at 3.5–4.0 | The panel's jewel lamps, the pendant bulbs, the projector lens and the beam bloomed into white patches; the radio dial clipped white (8 % of the frame) | Glow 0.4 / 0 / 1.35; lamp glass 2.2, bulbs 2.6, beam energy 0.75 (the shader's 1.6), emblem decal 2.2; the camera fill drops to 0.45 at the radio, poster and lock close-ups, where it clipped the cream dial, the glossy glass and the pale eye |

### Status
| Area | Level | Evidence |
|---|---|---|
| 12 puzzles + finale choice | AUTOMATED TESTED (3D taps) | Solver playthrough: 13/13 steps, 5/5 Lumen shards, 100 taps, **0 logic fallbacks** |
| Wrong attempts give feedback | AUTOMATED TESTED (3D taps) | Player review: sealed door, wrong safe code (input clears), dead radio, dead projector, main lever without its handle, empty mirror bracket and using the notebook on the door all answer with a message and/or a sound |
| Locked drawer message | AUTOMATED TESTED (3D taps) | Pulling the drawer front answers "Locked. Four brass wheels hold it shut." with a sound. **Fixed:** in the drawer close-up, a tap on the desk around the drawer used to do nothing; it now gives the same answer |
| Hints, 3 levels | AUTOMATED TESTED (3D UI) | Level 1 → 2 → 3, the button disables at level 3, Back closes the panel |
| Save, quit, continue | AUTOMATED TESTED | The continued state equals the saved state, and the intro does not replay |
| Language switch mid-game (EN → RU → UZ) | AUTOMATED TESTED + VISUALLY VERIFIED | View titles and the pause menu change at once; screenshots checked |
| Finale choice cannot be dismissed with Back | AUTOMATED TESTED | |
| Per-game variant answers (safe cipher, gear box, beacon, book order) | AUTOMATED TESTED (logic + 3D taps) + VISUALLY VERIFIED | 60-seed logic tests. Real-scene playthrough with `--seed=4242` on 2026-10-09: safe 1204, books IV-II-VIII, P1–P12, the finale and 5/5 shards, **100 taps, 0 fallbacks**. The UV page shows ◇ ≈ 👁 △, which the poster reads as 1-2-0-4 (`docs/previews/variants/ch1_seed4242_safe_evidence.jpg`). Players get a random seed per game; Continue keeps it (tested) |
| Every object can be reached from the room view | AUTOMATED TESTED (3D taps) | The player review taps the part of each object that is actually visible (raycast samples). **Found and fixed:** the coat rack stood behind Panel 7's open door, so a tap on it opened the panel. It now stands 25 cm further west and is visible between the window and the panel. The mirror stands and the projector are reached through their visible parts. The evidence board is in the darkroom, so it is not visible from the lab |
| Dark (unpowered) lab readability | VISUALLY VERIFIED | Before the fix the south-west and south views were almost black (mean brightness 2–3 of 255). A cool moonlight bounce and a higher dark ambient raised them to 18–23 while the power-on change stays dramatic. See `docs/previews/ch1_dark_state_before_after.jpg`. A brightness slider in Settings covers dim phone screens. The 2026-10-10 glow change left the dark lab as it was (mean 37.8 → 37.5 in the opening view) |
| Light pass (2026-10-10): glow and emissives | VISUALLY VERIFIED + measured | Before/after frames of the same seed-4242 run (`docs/previews/quality/ch1_*_before_after.jpg`): the panel's lamps read as lit glass instead of white discs, the lab's pendant light is unchanged in mood. Clipped pixels in the beam view 3.9 % → 3.1 % at beam energy 1.05; the regression run at 0.75 and the radio dial with the dimmer fill are reported below when they finish |
| Every mechanism answers a tap, in every state | AUTOMATED TESTED (3D taps, headless) | `feedback_audit --chapter=ch1`: 48 taps, 0 silent (2026-10-10), after the drawer and safe close-ups were brought in on their controls |
| No puzzle part hidden behind another in its view | AUTOMATED TESTED (tap maps) + VISUALLY VERIFIED | 27 start-state views and 13 views at the darkroom stage (`--until=shelf_open`), 2026-10-10: every puzzle control is green (reachable at ≥ 3 of 5×5 sample points). The only red marks are parts hidden by design: the compartment and keyhole inside the shut desk, the gears under the open lid, the keypad behind the open safe door, the rings seen edge-on from the chalkboard, the valve socket under the closed hatch |
| Close-ups sized for a finger | VISUALLY VERIFIED | Drawer wheels and safe keys were ~4–5 mm wide on a 6" phone. While shut, the drawer view now frames the four wheels and the safe view the keypad (about 8 mm per control); both step back once opened so the contents are in view. The solver and the feedback audit tap through both framings |
| Main menu with the logo (EN/RU/UZ) | VISUALLY VERIFIED | `docs/previews/ui/menu_en.jpg`, `menu_ru.jpg`, `menu_uz.jpg` (2026-10-09 redesign: gear box hero, serif text items, 0 layout issues in `qa/ui_screens.tscn` on a notched phone and a 10" tablet); the logo subtitle is translated in each language |
| Performance | AUTOMATED (indicative) | 94–99 draw calls, ~175–183k primitives (target 150k), ~6 s scene build on the CPU renderer |

### Estimated duration
- The solver finishes in about 3 minutes, which tells us nothing about humans.
- For a first-time player the estimate is **35–60 minutes**, based on the 12 puzzles, the number of documents and comparable games. This is an estimate, not a measurement.

### Still needs human testing
1. **The first 30 seconds.** Do players understand "drag to look, tap to examine" from the caption alone, and do they find the desk first?
2. **The first drawer.** The clock-to-code link (03:17 → 0317) is the first deduction. Watch whether testers stall; a gentle nudge after a long idle is planned if they do.
3. **Brightness.** Is the unpowered lab readable on a real phone at 50 % screen brightness, and is it still moody?
4. **Mirror puzzle.** Is the one-click 45° turn clear without a tutorial?
5. **Taps on small controls** (drawer wheels, radio knob) with a real finger.
6. **Pacing.** Any stretch longer than 5 minutes without progress or a new discovery.

---

## Chapter 2 — The Missing Scientist (the Archive)

### Tools
| Check | Command | What it does |
|---|---|---|
| Solver playthrough | `tools/qa_run.sh -- res://qa/playthrough_ch2.tscn -- --out=<dir> --lens=take` (and `--lens=leave`) | Plays P1–P12, the finale and the optional echoes by real taps through the room's raycast. It aims where a part is actually visible, like a player. Every logic fallback is reported with what the tap hit instead |
| Tap map | `tools/qa_run.sh -- res://qa/tap_map.tscn -- --chapter=ch2 --views=… [--until=booth_open] [--do=open_cat_drawer:4,…]` | Marks every tappable part in a view: green = reachable, orange = small, red = covered; it names what a tap hits instead |
| Feedback audit | `godot --headless --path game res://qa/feedback_audit.tscn -- --chapter=ch2` | 40 taps on mechanisms and scenery in their own views and states (no pressure, no card, no reel, locked, emptied, unlocked), each checked for an answer (message, caption, sound, camera move, document or state change) |
| Logic tests | `tools/run_tests.sh` | Puzzle rules, both lens paths, the no-softlock fuzz |

### What the 3D QA found and fixed (2026-10-09)
| Problem | Effect on a player | Fix |
|---|---|---|
| `ItemDB.is_tool()` clashed with Godot's `Script.is_tool()` | **Every "use item on …" tap crashed**: card into the punch, card into the canister, key on locker 9, reels on the deck. Chapter 2 could not be finished by tapping | Renamed to `is_tool_item` |
| Catalogue: padded box colliders on cards and dividers | Tapping a card's tab hit a divider in front | Exact colliders for cards and dividers only |
| Catalogue: back sections inside the carcass, small tabs | The cards behind dividers 0–2 could not be seen. Tabs were about 3 mm on a phone | The drawer pulls fully out. Picking a divider moves to a close-up of the raised section, where the tabs are large. The tray view keeps every divider reachable |
| A global "exact collider for thin parts" rule (made during this pass) | The rotary dial's finger holes became untappable (P8 blocked) | Reverted to opt-in. Caught by the tap map before it shipped |
| Compressor piping diagram: polished brass on black | The P2 evidence read as an empty black panel | Satin brass inlay with a faint glow; now legible |
| Projector beam scaled in world axes | The film's WOW moment was hidden by a floor-to-ceiling white slab | The beam now stretches along its own axis |
| Projector view too low | The run lever, focus ring and frame keys were out of frame | The camera now looks at the control side |
| Locker 9 view off-centre; the open locker door covered the floor hatch | The hidden 1998 reel was blocked, and taps went to the locker | Views re-aimed |
| Vault overlay and slide rotation turned counter-clockwise | At the logic's solution the sign did not match the engraving | The shader turns the images clockwise |
| English words baked into decals (badge, cards, rules, tape labels) | RU/UZ players saw English text | EN/RU/UZ variants, swapped at runtime |

### What the 3D QA found and fixed (2026-10-10, light and feedback pass)
| Problem | Effect on a player | Fix |
|---|---|---|
| The splicer's light box at emission 1.1 | A pure white blank (10–12 % of the splicer frame clipped) next to the strips the player must read | Emission 0.4, warm tint: frosted glass with a lamp behind it |
| The film beam haze at energy 0.16 | A quarter of the film view was a white wedge; the picture on the screen was the dimmest thing in the frame | 0.06 and a narrower cone; the picture is the brightest thing again |
| Pendant bulbs and shade linings at 3.0 / 0.55, lamp glass 3.0 everywhere, glow 0.6 / 0.05 / 1.1 | Every pendant in the hall was a white blot | Glow 0.4 / 0 / 1.35, lamp glass 2.2, shade glow 0.35 |
| The screen shader's lit field at 1.25 | The slide view was a clipped white field (21 % of the frame) with no screen weave left | 1.05 |
| 14 taps answered with nothing: the catalogue carcass, the gauges, the chart, the reading table, the stacks, the dial's centre, the dark screen, the empty screen socket, an empty crystal port, the vault door body, locker 9 once emptied, the slide gate and its turn knob without a slide, Eject with no reel, the splicer's light box, emptied grille / ledger / hatch / lens case / receive tray | As in Chapter 1 | Short lines (14 new EN/RU/UZ keys) and sounds; a tap on the vault door in the ports close-up now describes the disc instead of jumping back to the vault view. Checked by the feedback audit: 40 taps, 0 silent |

### Status
| Area | Level | Evidence |
|---|---|---|
| Logic P1–P12, both lens paths, softlock fuzz | AUTOMATED TESTED (logic) | `tools/run_tests.sh` |
| Per-game variant answers (docs/VARIANTS.md) | AUTOMATED TESTED (logic + 3D taps) | 60-seed logic tests: solvable, unique, saved and reproducible. Real-scene playthrough with `--seed=777` on 2026-10-09: valves 4-2-4, punch 10011100, clicks 3-9-8 / dial 398, splice f1 f3 f2 f0, focus 7, vault variant. **94 taps, 0 fallbacks** |
| 41 models in the room, every puzzle interaction | INTEGRATED | `docs/models/CH2_MANIFEST.md` (41/41) |
| Full chapter by real 3D taps, both lens paths | AUTOMATED TESTED (3D taps) | `playthrough_ch2` on 2026-10-09:<br>• leave path: P1–P12, P11b and the finale, **86 taps, 0 logic fallbacks**;<br>• take path: P1–P12 and the finale, **78 taps, 0 logic fallbacks**.<br>Screenshots are in `docs/previews/ch2/`, with phone frames in `docs/previews/ch2/phone/` |
| First-time-player review (`qa/player_review_ch2.tscn`, real touch events through the viewport, 2026-10-09) | AUTOMATED TESTED (3D taps) | First run: 7 real problems. **Fixed:**<br>• the catalogue (P1) was hidden from the hall and no player action led to it → a hanging "CARD CATALOGUE" sign (EN/RU/UZ) and walking to the west aisle;<br>• wrong valve settings were silent → each turn says which gauge is on its mark;<br>• a wrong splice order and the projector lamp without film were silent → messages;<br>• the receiver kept counting a reel already taken;<br>• the open booth could not be entered while holding an item;<br>• the 1996 tape label texture failed to import, so builds lost the 4.75 clue.<br>Second run: 1 ✗ left (the Back button shows during the intro's shutter shot; UI fix in progress). After the intro, a goal line now says where to start |
| Variant seed 31337, take path | AUTOMATED TESTED (3D taps) | Valves 2-3-2, punch 01100101, clicks 1-9-1 / dial 191, splice f2 f0 f3 f1, focus 6: **83 taps, 0 fallbacks** |
| Released | — | `chapters.gd`: `released: true`. Players unlock it with the full-game purchase (real payments still off); tester builds open it through `beta_unlock` |
| Every main view and the booth views | VISUALLY VERIFIED | Tap maps and playthrough screenshots (software renderer) |
| Light pass (2026-10-10): no white patches where the player must read | VISUALLY VERIFIED + measured | Before/after frames of the same seed-777 leave run (`docs/previews/quality/ch2_*_before_after.jpg`). Clipped pixels (luminance ≥ 250) per frame: splicer 11.8 % → 0.1 %, film view haze gone (the picture on the screen is now the brightest thing), hall pendants no longer blots. Unchanged by design: the echo figures (7.9 %, they are made of light) |
| Every mechanism answers a tap, in every state | AUTOMATED TESTED (3D taps, headless) | `feedback_audit --chapter=ch2`: 40 taps, 0 silent (2026-10-10) |
| Audio | IMPLEMENTED | Not listened to on a device |
| Performance | **Over budget (draw calls)** | Hall view: 198 draw calls, ~126k primitives (budget 150 / 150k; it was 222 / 239k). The one shadowed pendant now uses a downward spot cone instead of a dual-paraboloid omni. The other views are 51–171 draw calls |

### Estimated duration
30–40 minutes for a first-time player. This is the design target, not a measurement. The solver needs about 4 minutes.

### Still needs human testing
1. **The catalogue.** Do players read the badge number 0417 as drawer 04 / divider 1– / card 17 without the hints?
2. **The receiver hunt.** Is the bar meter alone enough to find the three reels?
3. **The tape voice and click counts (2, 8, 5).** Are they clear on a phone speaker? The VU needle and caption dots are the visual backup.
4. **The film and recording.** Do players understand that the crystal must sit in the screen socket while only the sharp sign is shown?
5. **The vault overlay.** Is "on its side, smaller" in the engraving clear enough?
6. **Pacing.** Is the stretch from the booth to the vault too long without a hint of progress?

---

## Chapter 3 — The Underground Facility (Level −2)

### Tools
| Check | Command | What it does |
|---|---|---|
| Solver playthrough | `tools/qa_run.sh -- res://qa/playthrough_ch3.tscn -- --out=<dir> --key=strand` (and `--key=leyla`, `--seed=N`, `--lens=take`, `--secret`) | `UndergroundSolver` decides each move on a copy of the game (`qa/ch3_plan.gd` records it); the playthrough walks there through the open ways (lift passages, blast doors, the shutter tunnel) and taps the part through the room's raycast. After the first wing it saves, frees the scene and rebuilds it from the save (the menu's Continue). Every fallback is reported with what the tap hit; fallbacks for models not built yet are listed per puzzle. Exit 0 = no failed step and no fallback |
| Quick logic-flow run | `godot --headless --path game res://qa/playthrough_ch3.tscn -- --out=<dir> --quick --key=leyla` | The same taps without a renderer (the headless window is set to 16:9 so the views frame as on a phone); about 7 minutes |
| Tap map / perf | `tools/qa_run.sh -- res://qa/tap_map.tscn -- --chapter=ch3 --key=strand --until=door_east_open --views=desk,drum_east [--perf --breakdown]` | Marks every tappable part in a view, or logs draw calls, primitives and the per-model breakdown |
| Logic tests | `tools/run_tests.sh` | Puzzle rules, both wing orders, both lens paths, the secret, 60-seed variants, the no-softlock fuzz |

### What the 3D QA found and fixed (2026-10-10)
| Problem | Effect on a player | Fix |
|---|---|---|
| The lift zone had only the cage lamp | From the lift, the lobby beyond the open gate was a black hole; the way out could not be seen | Two unshadowed omnis over the passage mouths (group L) |
| `desk`, `switch_room`, `choir_s` and `nursery_w` culled the lobby while framing a passage mouth | The opening showed the fogged background as a flat teal slab | Those views draw group L too (the lobby is 27 draw calls) |
| The eyepiece rim's vertex colours were read as linear | Every port view was framed by a bright beige disc instead of a dark brass rim | `vertex_color_is_srgb` on the rim material |
| Camera fill of 0.9 on dark steel | The east drum lock's symbols were nearly black | Fill 1.5 in the close-ups that must be read (drum locks, cabinets, case, cam drum, log, drawer, socket, recorder, plate) |
| A tap right after a cinematic or a camera move is dropped (`RoomBase._on_tap` while `cam.transitioning`) | QA only: the autoclave door after the growth and the second port-rim tap fell back | The playthrough waits for the camera, as a finger would |
| The headless window is square | QA only: the master knob and the port rims fell outside the frame | The headless run sets a 16:9 window |

### Status
| Area | Level | Evidence |
|---|---|---|
| Logic: 11 puzzles, both wing orders, both lens paths, the secret, per-game variants, softlock fuzz | AUTOMATED TESTED (logic) | `tools/run_tests.sh`: 102 tests, 0 failures |
| Scene: §1.2 layout, the 65 §2 views with captions, §1.4 zone culling and portal cards, §1.5 lights (one shadowed spot per zone), environment, zone room tones, the lift descent intro, `SceneManager.room_ready` / CrashGuard safe levels | INTEGRATED | `game/src/rooms/underground/underground_room.gd`, `underground_data.gd` |
| Hotspot routing of every puzzle to `UndergroundLogic`; visuals rendered from `logic.state`; the nine variant evidence surfaces (§11); kept echoes, the 1979 loop, Leyla's touch, the finale and the secret; hints through `hint_goal()` / `hint_args()` | INTEGRATED | `underground_visuals.gd` |
| Full chapter by real 3D taps, both Chapter 2 key paths | AUTOMATED TESTED (3D taps) — **waits for models** | `playthrough_ch3` on 2026-10-10 with groups A, C, part of D, G and H built. Rendered strand path: chapter complete, **63 taps, 45 fallbacks** (44 for models not built yet, 1 QA walk since fixed). Quick runs: leyla path 53 taps / 48 fallbacks (44 unbuilt), strand path 57 taps / 44 fallbacks (all unbuilt); after `choir_rack`, `choir_tube` and `transformer` landed, strand path **65 taps / 37 fallbacks, all for unbuilt models** (heart 15, prisms 5, melody 4, resonance 4, choir 3 = the bench tubes, interlock 2, seed 2, restore 1, grow 1) |
| Continue: save → free the scene → rebuild from the save after the first wing | AUTOMATED TESTED (3D) | Both paths: state kept, opens at the wing's hall, gate open |
| Tap map of the close-ups (`drum_east`, `cabinet_1`, `desk`, `autoclave`, `cam_drum`, `seed_library`, `lift_w`, `switch_room`, `port_b`, `blast_east`, after the rings) | AUTOMATED TESTED (raycast) | Every control reachable; the only orange/red lines are non-targets: the passage mouth at the switch-room frame edge, the port's own lens and ring from inside the port view, and the autoclave seen far through the open east door |
| Models in the scene | 14 of 31 built | A (7), C (`switch_cabinet`, `interlock_plate`, `inspection_port`, `control_desk`), D (`autoclave`, `autoclave_dead`, `growth_log`), all items (G) and echoes (H). Waiting: B (7), D (`seed_library`, `growth_chart`, `prism_bench`, `spectral_seal_door`), E (4), F (2). The room spawns a model the moment its GLB is in `game/assets/models/` |
| Views | VISUALLY VERIFIED (software renderer) | The selection in `docs/previews/ch3/` (from the 50 playthrough screenshots and the tap-map shots after the fixes). Still to improve, not blocking: the drum-lock symbols are embossed dark brass in dark windows and stay dim even with the stronger fill (a brighter window face in `blast_door` would help); the sleeping Array's rings are near white at 0.7 emission |
| Audio | IMPLEMENTED | Tube and crystal tones are synthesized (`underground_tones.gd`); zone tones and the finale music fall back to Chapter 2 tracks until Chapter 3's exist |
| Performance | Under budget so far (≤ 150 draw calls / 150k primitives) | Playthrough (strand path, old HUD, before the rack landed), draw calls per view: lift 27–36, choir 52, choir_s 90, desk 86, port_b 66, rack 41, gallery 51, gallery_w 57, glass_floor 51, console 52, finale 64, nursery 54, nursery_w 70, autoclave 54, seed_library 37, prisms 66, camp 37, shutter 67; primitives 4k–43k. Tap map `--perf` after the rings, with the restyled HUD and the choir rack: lift_w 55, choir 91, choir_s 117, desk 119, switch_room 106, port_b 91, nursery_w 104, gallery 72, glass_floor 76, drum_east 72. Biggest single contributors (`--breakdown`): a switch cabinet 18–20, the choir rack 19, the autoclave 13, the control desk 11 (the per-mesh deltas of that run were ±10 noisy because the HUD animated; `_breakdown` now hides the HUD while it measures). Groups B, E and F are not in yet; the Choir views (choir_s, desk) will gain the most and must be re-measured when B lands |
| Released | — | `chapters.gd`: `released: false` |

### Still needs human testing
1. **The interlock plate.** Do players read the pictograms as "key into the lock face, handle to O, the next key comes free"?
2. **The 1979 loop.** Through three ports, is it clear that the globes count the step and each port shows only some of the levers?
3. **The chalk staircase and the meter.** Is "reading 1 = the longest tube" understood from the staircase alone?
4. **The prism fans.** Is the additive colour on the three rims readable on a phone screen?
5. **The ring symbols.** Outer → inner through the glass floor against the drum order on the door.
