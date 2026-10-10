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
| 2026-10-10 (owner feedback) | Panel 7 and the poster fitted to the HUD's free area, bag HUD, notebook page 4 icons, safe hints, shadow / radio-hatch reframes, story caption waits outside Panel 7 | seed 4242: all steps ✓, 5/5 shards, `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`; seed 1337: all steps ✓, `taps through 3D scene: 101, logic fallbacks (missing models/placeholders): 0`; both `taps under a HUD control: 0 (window 1920x1080)` | seed 777 leave: all steps ✓, `taps through the 3D scene: 94, logic fallbacks: 0`; seed 777 take: all steps ✓, `taps through the 3D scene: 86, logic fallbacks: 0`; both `taps under a HUD control: 0 (window 1920x1080)` |
| 2026-10-10 (engagement pass, `docs/ENGAGEMENT.md`) | Ch1: bookcase reveal staging, the corridor beyond the door, the second-mirror milestone, the corridor postmark epilogue, resume at the ending. Ch2: the reel reveal, the cliffhanger and the Chapter 3 card, the vault's answer, blank-crystal feedback, the whisper secret, resume at the ending | seed 4242: all steps ✓, 5/5 shards, `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`; seed 1337: all steps ✓, `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`; both `taps under a HUD control: 0 (window 1920x1080)` | seed 777 leave (Leyla's key): all steps ✓ including the cliffhanger, `taps through the 3D scene: 94, logic fallbacks: 0`; seed 777 take (Strand's key): all ✓, `taps through the 3D scene: 86, logic fallbacks: 0`; both `taps under a HUD control: 0 (window 1920x1080)` |

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

<!-- hud-check-ch1 -->
### Owner feedback from an Android phone (2026-10-10): Panel 7, the HUD, the safe code chain
| Problem | Effect on a player | Fix |
|---|---|---|
| Panel 7 close-up: the four icons above the lamps were cut off by the title and the main lever with its "1" plate sat under the inventory | Taps on the lever hit inventory slots; the icons that the notebook refers to could not be read | The close-up is **fitted** to the area the HUD leaves free (`RoomCamera.fit_rect` with `hud_free_rect`, refitted when the screen or the text size changes), so the whole plate, icons to lever, shows at 16:9, 19.5:9, 20:9 and 4:3 (`docs/previews/quality/ch1_panel7_framing_{phone61,tablet10}_before_after.jpg`, `ch1_panel7_powered_before_after.jpg`). Each switch bay and the lever have a finger-sized tap area; the lamp icons are 2.7 cm on the plate. The story caption that follows the power-on ("a faint red glow around the bookcase") sat over the icons for 4.5 s, so it now waits until the player leaves the panel |
| Nothing checked that a control is clear of the HUD: the solver's taps go straight to the room, so earlier runs passed while a phone player could not reach the lever | A defect only a human on a phone could find | `tap_map --hud-check` (see below) and a counter in both playthroughs: taps whose point lies under a HUD control. **0 in every run** |
| Notebook page 4 named LOCK, LIGHT, ARRAY and VENT in words only; the Uzbek "Panjara" for ARRAY reads like a grille, which is what VENT is | The word-to-lamp link depended on the translation | The page draws the panel's four icons next to the words in all three languages (`{panel_lock}` … tokens, one additive helper `_ink_icons` in `hud.gd`), `docs/previews/quality/ch1_notebook_p4_icons_en_ru_uz.jpg` |
| The safe chain (UV page symbols → Strand's *Tabula Resonantiarum* poster → dots → digits): hint 1 of "safe" talked about the page, the UV page never said where to look, the poster close-up had its header under a two-line title and its bottom under the prompt, and the ink read at 2.1:1 through the glass | The most likely place for a stuck player: they had four symbols and no pointer | Hint 1 names the poster on the safe's wall, hint 2 says each symbol's dots are one digit (none is 0); the UV page line reads "Count them on his Table of Resonances"; the poster view is fitted whole between title and prompt, its caption is one line, and its glass is hidden in that view (ink contrast **2.1 → 4.3:1** measured on the render). The reader keeps the long title. `docs/previews/quality/ch1_poster_before_after.jpg`; the poster's cells next to the UV page art for all 10 symbols: `ch1_poster_vs_uv_glyphs.jpg` (dot counts and shapes match; `test_safe_chain.gd` also compares the poster generator's table with the logic's and checks 200 seeds) |
| Hints at levels 1 and 2 did not always name the object to go to | A stuck player was told what to do but not where | All 26 Ch1 goals re-read: the notebook's desk, the drawer wheels and the flip clock, Strand's gear box left of the desk, combining the cell with the lamp from the bag, the UV lamp for the page, the desk's keyhole, Panel 7's lever, the icons over the lamps, the radio's hatch, the bookcase's encyclopedia, the samples on the bench (EN/RU/UZ) |
| `--hud-check` run at 19.5:9 and 4:3 found controls too close to the screen edge | Sculpture knobs 1–4 mm from the bottom edge in the shadow view; the radio's tuning knob 1.4 mm in the radio-hatch view | The shadow view is aimed lower; the radio-hatch camera is 18 cm further back |

#### HUD check (`tap_map --hud-check`)
Every interactive part of a view (`IA_*`, `Item_*`, `Shard_*`, `Echo_*`) must have its tap point on screen, outside every rectangle `HUD.blocked_rects()` reports (the four corner buttons; the bag tray when it is out) and at least 6 mm from the screen edge, with the message and prompt banners up as they are while a player works a mechanism with an item in hand. Two exceptions, both reported: a control the view can only *focus* (its tap moves the camera to the object's own view, `RoomBase.in_reach`) is checked in that view, not here; and a control with under 40 % of itself on screen that peeks in at the edge is scenery. A control under a banner is a warning, because banners take no input. Screens: `phone61` 2340×1080 at 400 dpi with a camera cut-out (19.5:9), `phone20` 20:9, `phone55` 1920×1080 (16:9), `tablet10` 2048×1536 (4:3).

| Run | Result line, as printed |
|---|---|
| Ch1, 36 views, start state, 19.5:9 | `hud-check (phone61): 93 controls in 36 views, 0 failures, 13 banner warnings (80 focus-only controls and 0 slivers not checked)` |
| Ch1, 36 views, start state, 4:3 | `hud-check (tablet10): 90 controls in 36 views, 0 failures, 6 banner warnings (59 focus-only controls and 0 slivers not checked)` |
| Ch1, 10 darkroom views, bookcase open (`--until=shelf_open`), 19.5:9 / 4:3 | `hud-check (phone61): 9 controls in 10 views, 0 failures, 7 banner warnings (28 focus-only controls and 0 slivers not checked)` / `hud-check (tablet10): 9 controls in 10 views, 0 failures, 2 banner warnings (21 focus-only controls and 0 slivers not checked)` |
| Ch1, 13 views with the beam on (`--until=beam_on`), 19.5:9 / 4:3 | `hud-check (phone61): 35 controls in 13 views, 0 failures, 12 banner warnings (13 focus-only controls and 0 slivers not checked)` / `hud-check (tablet10): 31 controls in 13 views, 0 failures, 4 banner warnings (9 focus-only controls and 0 slivers not checked)` |
| Ch1 views changed in this pass (panel, poster, shadow, radio_hatch, safe), 20:9 / 16:9 | `hud-check (phone20): 26 controls in 5 views, 0 failures, 2 banner warnings (0 focus-only controls and 0 slivers not checked)` / `hud-check (phone55): 26 controls in 5 views, 0 failures, 2 banner warnings (0 focus-only controls and 0 slivers not checked)` |

Before the check learned which controls a view can work, the first full run printed `hud-check (phone61): 173 controls in 36 views, 24 failures` and `hud-check (tablet10): 149 controls in 36 views, 7 failures`; all but the shadow and radio-hatch cases were controls seen at the edge of someone else's close-up.

<!-- hud-check-ch1 -->

### Engagement pass (2026-10-10): reveals, the hand-off to Chapter 2, resuming at the end
`docs/ENGAGEMENT.md` has the minute-by-minute curve and the reasoning.

| Problem | Effect on a player | Fix |
|---|---|---|
| The bookcase reveal (P9 → the darkroom), the chapter's midpoint, was a message line and a door sound | The hidden room opened without light or air: told, not shown | As the case swings, the darkroom's red safelight flares through the gap (0.7 → 4.2 → back, reaching 1.6 m further for a moment), a breath of dust rolls into the lab, a low tone sounds and a caption reads *"[A cold draught breathes out from behind the shelves]"* (`_stage_bookcase_reveal`) |
| The door opened onto the flat fog colour | The final image of 40 minutes was an empty rectangle, and nothing pointed on to Chapter 2 | A 9 m institute corridor beyond the door, built only when it opens: linoleum, green dado, three enamel pendants, and double doors under a lit **RECORDS ARCHIVE B** sign (it translates). The lamps flicker on one by one toward the sign: *"[Beyond the door, the corridor lamps wake one by one]"* |
| The epilogue said *"On the train home…"* and Chapter 2 then opens *"Beyond Laboratory 7…"* | The free chapters contradicted each other at their seam | `epi1.postmark`: *"Under the corridor lamp you unfold the parcel's wrapper again. The postmark reads: 14 XI 1979."* |
| The mirror stretch (P12) gave no sign of progress until the door opened | Eight clicks per stand with nothing new to see | The first time mirror A sends the beam on to mirror B: a bright tick and *"[The beam leaps to the second mirror]"*, once (`_beam_progress`). No rule changed |
| Continue after the ending loaded a finished room: quitting on the chapter card left an open door, nothing to tap and no card. Quitting during the ending left the door open and the lens choice never offered | Stranded at the free-to-free hand-off, with only Pause → Main menu → Chapters as a way out | A finished save opens on the chapter card (its Play button starts Chapter 2) over the lit corridor; a save made between the door and the choice offers the choice again (`_resume_completed`, `_resume_choice`). `qa/transition_check.tscn` on the code before this pass printed `✗ Continue at the open door offers the choice again` and `✗ a finished Lab 7 opens on the chapter card (not an empty room)` |

Checks (2026-10-10, after the changes):
- `qa/playthrough.tscn --seed=4242`: all 15 steps ✓, 5/5 shards, `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`, `taps under a HUD control: 0 (window 1920x1080)`; `--seed=1337`: all ✓ (safe 6803, books VII-III-IX), `taps through 3D scene: 100, logic fallbacks (missing models/placeholders): 0`, `taps under a HUD control: 0 (window 1920x1080)`. After these runs the red flare was made stronger and the corridor sign larger; these are presentation only, with no tap target or camera view changed, and are shown in the reveal shots below.
- `qa/ch1_reveal_shots.tscn` (new; the bookcase at 0.3 / 0.9 / 1.8 s and the ending through the corridor), on the code before and after: `docs/previews/engagement/ch1_bookcase_reveal_before_after.jpg`, `ch1_door_corridor_before_after.jpg`, `ch1_epilogue_card_before_after.jpg`.
- `tap_map --chapter=ch1 --until=shelf_open --views=bookshelf,darkroom,door,lock --hud-check --screen=phone61`: `hud-check (phone61): 4 controls in 4 views, 0 failures, 3 banner warnings (9 focus-only controls and 0 slivers not checked)`.
- `qa/transition_check.tscn` (new, headless, seed 4242): Continue at the open door, Continue on the finished chapter, Play into Chapter 2 with the Chapter 1 choices, a midway save and Continue in Chapter 2: `transition checks failed: 0`. The same checks on the code before this pass (seed 0): 6 failed.

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
| No puzzle part hidden behind another in its view | AUTOMATED TESTED (tap maps) + VISUALLY VERIFIED | 27 start-state views and 13 views at the darkroom stage (`--until=shelf_open`), 2026-10-10 (`docs/previews/quality/ch1_tap_map_puzzles.jpg`): every puzzle control is green (reachable at ≥ 3 of 5×5 sample points). The only red marks are parts hidden by design: the compartment and keyhole inside the shut desk, the gears under the open lid, the keypad behind the open safe door, the rings seen edge-on from the chalkboard, the valve socket under the closed hatch |
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
7. **The ending.** Can testers say why they are going to the archive (the 1998 clipping on the evidence wall)? Do they notice the corridor and its sign before choosing?

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

<!-- hud-check-ch2 -->
### HUD check (2026-10-10)
`tap_map --hud-check` (rules in the Chapter 1 section) on every Chapter 2 view:

| Run | Result line, as printed |
|---|---|
| 34 views, start state, 19.5:9 | `hud-check (phone61): 122 controls in 34 views, 0 failures, 30 banner warnings (202 focus-only controls and 3 slivers not checked)` |
| 34 views, start state, 4:3 | `hud-check (tablet10): 119 controls in 34 views, 0 failures, 24 banner warnings (121 focus-only controls and 0 slivers not checked)` |
| 12 booth views with the booth open (`--until=booth_open`), 19.5:9 / 4:3 | `hud-check (phone61): 27 controls in 12 views, 0 failures, 7 banner warnings (73 focus-only controls and 0 slivers not checked)` / `hud-check (tablet10): 27 controls in 12 views, 0 failures, 2 banner warnings (36 focus-only controls and 1 slivers not checked)` |
| 8 vault views with the vault unlocked (`--until=vault_unlocked`), 19.5:9 / 4:3 | `hud-check (phone61): 16 controls in 8 views, 0 failures, 2 banner warnings (26 focus-only controls and 1 slivers not checked)` / `hud-check (tablet10): 16 controls in 8 views, 0 failures, 7 banner warnings (7 focus-only controls and 0 slivers not checked)` |

<!-- hud-check-ch2 -->

### Engagement pass (2026-10-10): the purchase moment, the 42nd figure, feedback and a secret
Chapters 1 and 2 are free, so the end of this chapter is where a player decides to buy. `docs/ENGAGEMENT.md` has the curve and the reasoning; the cliffhanger is `game/src/rooms/archive/archive_teaser.gd`.

| Problem | Effect on a player | Fix |
|---|---|---|
| Straight after the key choice came the statistics card: *"To be continued…"* and Main Menu | The purchase moment showed nothing new and left no question open | **The cliffhanger.** The key comes off its hook. A lift motor wakes under the vault (shake, stuttering bulb, falling dust). A glimpse down the freight-lift shaft: eight lamps wake storey by storey, the cage climbs, the light of Level −2 breathes at the bottom, the transformer hum rises. On black: *"Somewhere below, a recorder clicks on"*, Leyla's 1998 voice captioned over a tape-head trace (the words are from Chapter 3's recorder), then a second voice under the hiss: *"Leyla?… Who is that with you?"* Then the **Chapter 3 card** (below) and the usual chapter card. A tap shortens every beat; the card waits for the player |
| The twist, the 42nd silhouette, was one 7.5 s caption over a screen a quarter of the view wide | Easy to miss the chapter's reveal | The reel close-up, *"…Forty-one silhouettes in the light."*; then a reveal tone and a haptic pulse: the frame dims around the figure at the right edge, a cold halo grows around her (`vault_reel.gdshader`), the camera leans in, *"And a forty-second, at the edge of the frame. Leyla, 1998."* The choice opens over a cradle view framed high, clear of the dialog |
| After a crystal is recorded, nothing pointed to the vault; the leave path then has six more device steps | The longest stretch of busywork, with the next goal across the hall | The vault answers: a far clunk, that port's light pipe on the vault door flares, *"[Across the hall, the vault door answers with a dull clunk]"* (once per image) |
| A blank crystal that recorded nothing just sat in the socket; P11b's rule (film lamp off) was never said | A wrong idea and a dead tap looked the same | It says why: the screen is dark / the picture is blurred / two images overlap / *"It waits for one sharp image, alone on the screen."* Switching the slide lamp on over the running film: *"The slide's light and the film's light cross on the screen."* No answer is spoken |
| Nothing off the main path rewarded curiosity except the echoes | — | **Secret "Forty-Two":** with all three reels found, select the receiver at the shut vault door: the needle twitches once more and a far voice counts *"…forty… forty-one… forty-two"* (achievement `forty_two`; no puzzle depends on it) |
| Continue after the end loaded a finished Archive (or an open vault whose choice was never made) with nothing to do | Stranded | A finished save opens on the Chapter 3 card; a save between the vault and the choice offers the two keys again. Before this pass `qa/transition_check.tscn` printed `✗ Continue at the open vault offers the two keys again` and `✗ a finished Archive opens on a card (not an empty room)` |

**The Chapter 3 card's hand-off** (`ArchiveTeaser.card_state()`; `purchase_panel.gd` is not touched):

| State | When | The card shows |
|---|---|---|
| `unlock` | Chapter 3 released, not owned, the store open | *"Chapters 3 and 4 finish the story. One purchase unlocks both; no ads, ever."*, **Continue the story** (opens `PurchasePanel.open()` over the card), a quiet **Not now**. A completed purchase closes the card; the chapter card then offers Play |
| `soon` | Chapter 3 not released, or no store (`REAL_PAYMENTS_ENABLED = false` in a release build) | *"Chapters 3 and 4 are on their way. Your key and your choices are saved for them."*, **Continue** |
| `play` | Chapter 3 owned, or a tester build | **Continue** (the chapter card offers Play) |

Checks (2026-10-10, after the changes):
- `qa/playthrough_ch2.tscn --lens=leave --seed=777`: P1–P12, P11b, `✓ Finale: leyla_key → chapter complete`, `✓ Cliffhanger: lift shaft, recorder, Chapter 3 card (soon)`, `✓ Chapter 3 card → chapter card`, `taps through the 3D scene: 94, logic fallbacks: 0`, `taps under a HUD control: 0 (window 1920x1080)`. `--lens=take --seed=777`: the same with `strand_key`, `taps through the 3D scene: 86, logic fallbacks: 0`, `taps under a HUD control: 0 (window 1920x1080)`. Before this pass, the same leave run printed `taps through the 3D scene: 94, logic fallbacks: 0` and ended on the statistics card. The playthrough now plays Strand's key on the take path and Leyla's on the leave path, and presses the Chapter 3 card's button. After the leave run, the finale close-ups lost their title plate. After both runs, the shaft camera moved toward the middle of the shaft. Neither change touches a tap target; the final framing is in the teaser shots.
- `qa/teaser_shots.tscn` (new; the solver plays to the unlocked vault, then the real scene runs the whisper, the finale, the cliffhanger and the card in its three store states): rendered on the leave path (Leyla's key) and on the take path (Strand's key, seed 31337), `teaser checks failed: 0` both times. Measured: the shaft view `draw calls 52, primitives 7554` with the HUD.
- `tap_map --chapter=ch2 --until=vault_open --views=vault,vault_inside,vault_reel,vault_cradle --hud-check --screen=phone61`: `hud-check (phone61): 1 controls in 4 views, 0 failures, 1 banner warnings (10 focus-only controls and 0 slivers not checked)`. Its frames showed the view title covering the top of the key cradle at phone text size, so the finale close-ups have no title now.
- `qa/transition_check.tscn` (headless): Continue at the open vault and on the finished chapter, see the Chapter 1 section.
- Previews: `docs/previews/engagement/ch2_*.jpg`.

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
| No puzzle part hidden behind another in its view | AUTOMATED TESTED (tap maps) + VISUALLY VERIFIED | 30 views with the booth open and drawer 04 / divider 1– pulled (2026-10-10, `docs/previews/quality/ch2_tap_map_puzzles.jpg`): every puzzle control is green in the view where it is used. The red marks are parts hidden by the state: locker 8 behind the open locker 9 door, the dial and the lockers behind the open booth door, far-off drawers seen from the booth. The dial holes and punch keys were re-framed to ~7 mm on a phone and checked by the feedback audit |
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
6. **Pacing.** Is the stretch from the booth to the vault too long without a hint of progress? (Since the engagement pass the vault answers each recording.)
7. **The cliffhanger and the Chapter 3 card.** Do testers watch it through or tap past it? Does the card feel like an invitation or a sales pitch? Does anyone find the receiver's whisper at the vault?

---

## Chapter 3 — The Underground Facility (Level −2)

### Tools
| Check | Command | What it does |
|---|---|---|
| Solver playthrough | `tools/qa_run.sh -- res://qa/playthrough_ch3.tscn -- --out=<dir> --key=strand` (and `--key=leyla`, `--seed=N`, `--lens=take`, `--secret`) | `UndergroundSolver` decides each move on a copy of the game (`qa/ch3_plan.gd` records it); the playthrough walks there through the open ways (lift passages, blast doors, the shutter tunnel) and taps the part through the room's raycast. After the first wing it saves, frees the scene and rebuilds it from the save (the menu's Continue). Every fallback is reported with what the tap hit; fallbacks for models not built yet are listed per puzzle. Exit 0 = no failed step and no fallback |
| Quick logic-flow run | `godot --headless --path game res://qa/playthrough_ch3.tscn -- --out=<dir> --quick --key=leyla` | The same taps without a renderer (the headless window is set to 16:9 so the views frame as on a phone); 4 to 7 minutes depending on the machine load. A fallback caused by a part that is missing from a model that *is* built is reported as a wiring bug (only models listed in `missing_models` count as "not built yet") |
| Tap map / perf | `tools/qa_run.sh --stall=1500 -- res://qa/tap_map.tscn -- --chapter=ch3 --until=<state key> --views=desk,drum_east [--perf --breakdown] [--cam=name:x,y,z:tx,ty,tz:fov]` | Marks every tappable part in a view, or (`--perf`) logs draw calls and primitives and saves a clean PNG per view. `--until` runs the solver to a state: `case_open` (Choir, hall not started), `crystal_grown` (seal still closed), `camp_open`, `gallery_awake` (the Array asleep), `array_awake` (finale). `--perf` prints nothing until the end, so pass `--stall=1500` or the watchdog kills the run after 180 s; `--cam` tries a camera before it goes into `underground_data.gd` |
| Logic tests | `tools/run_tests.sh` | Puzzle rules, both wing orders, both lens paths, the secret, 60-seed variants, the no-softlock fuzz |
| Mid-wing Continue | `godot --headless --path game res://qa/playthrough_ch3.tscn -- --out=<dir> --quick --key=strand --seed=23 --reload-every=3` | Quits and presses Continue every 3rd step; the rebuilt scene must show the same state and the same tappable parts (see Release-candidate QA) |
| Logic sweep | `godot --headless --path game res://qa/playthrough_ch3.tscn -- --out=<dir> --logic-sweep --sweep-seeds=75` | 300 games of solver actions mixed with random takes / returns, a save round trip after every action, a completion check from every 4th state; about 1 minute |

### What the 3D QA found and fixed (2026-10-10)
| Problem | Effect on a player | Fix |
|---|---|---|
| The lift zone had only the cage lamp | From the lift, the lobby beyond the open gate was a black hole; the way out could not be seen | Two unshadowed omnis over the passage mouths (group L) |
| `desk`, `switch_room`, `choir_s` and `nursery_w` culled the lobby while framing a passage mouth | The opening showed the fogged background as a flat teal slab | Those views draw group L too (the lobby is 27 draw calls) |
| The eyepiece rim's vertex colours were read as linear | Every port view was framed by a bright beige disc instead of a dark brass rim | `vertex_color_is_srgb` on the rim material |
| Camera fill of 0.9 on dark steel | The east drum lock's symbols were nearly black | Fill 1.5 in the close-ups that must be read (drum locks, cabinets, case, cam drum, log, drawer, socket, recorder, plate) |
| The drums sit 5 cm behind a shrouded plate with dark-steel symbols on brass; no room light reached them | The drum lock read as a nearly black panel even with the stronger fill | A small warm omni in front of each lock (range 1.1, unshadowed) and cream enamel symbol surfaces (albedo 0.94/0.9/0.8, emission 0.3): the four symbols read clearly at default brightness |
| Cabinet fronts lit only by the ceiling work lamps | The switch cabinets and the plate were dim from the desk view | An unshadowed 80° wash spot over the three cabinet fronts (energy 1.6, range 4.5) |
| Array rings: near-white albedo and emission 1.2 while awake (above the 1.1 glow threshold) | The sleeping Array bloomed white through the glass floor | Dormant rings: grey-blue glass, emission 0.15 asleep, 0.55 awake (under the threshold), 2.2 when the Array answers; `array_up` 1.0 / 2.0 / 3.0 with the state |
| `Item_chamber` could not be tapped: the seed in the autoclave was replaced by the grown crystal, but the old node was only queued for freeing, so the new one was renamed `Item_chamber2` | A player could not take the crystal out of the autoclave (found by the quick run: 1 fallback on both paths) | `_held_item` removes the old node from the tree before it frees it; the playthrough now reports a part missing from a built model as a real fallback |
| The 41 rising lights were visible in the Gallery from the first minute (`_rising.visible` is rewritten by zone culling on every view change) | White balls floated over the glass floor and the room before the Array answered | `set_present` (the presence flag culling respects), `present` false until `array_awake` |
| The key spot's cone ends short of the console (z 2.6) and the memorial arc (z -3.9) | Dials and figures read dark (model agent's note) | `console_lamp` (omni 1.5, range 3.6) and `memorial_lamp` (omni 2.0, range 5.5), unshadowed, group G; the console and the wall read clearly in `console`, `strand_plate`, `cradle`, `memorial`, `socket_42` |
| The choir rack and the tube bench are black enamel on a dark wall | Hooks, slots and the bench places vanished in `rack`, `rack_close`, `bench` | `rack_wash`, an unshadowed 85 degree spot over both (1.5, range 5.5) |
| Step globes at the shader's default emission 2.6; console lamp jewels at 2.5 | Lit globes were white blobs with a halo, the jewels white dots under the HUD buttons | Globes 1.05 (warm opal), jewels 1.5 in amber and cyan; no strong bloom left in the Choir |
| The `recorder` camera sat 25 degrees above the table, behind the scope; the two keys were dark Bakelite on dark leather | The play and rewind keys read as brown squares, their pictograms were slivers | Ivory piano-key material on both keys; the camera moved to (5.3, 1.38, -2.2), fov 34, looking over the scope's top at the keys and still showing the scope's screen. The key glyphs are readable in the render |
| `camp` view drew only group K | The open shutter showed a flat teal portal card | `camp` adds the Gallery when `shutter_open` |
| Seal receptors: cream symbols on a yellow rim or a white centre, glossy 0.25 under the prism lamp | The white centre and the yellow rim lost their symbols; a hot spot on the middle disc | Symbols are dark engravings, roughness 0.6, centre emission 1.0 |
| The answering Array's rings at emission 2.2 on near-white glass, the 41 memorial crystals at 2.8, the secret socket ring at 2.4 | Flat white rings and crystals (symbols clipped), a strong bloom in the finale | Rings: cyan albedo, emission 1.5; crystals 1.7; socket ring 1.5 |
| Drum lock lamp at y 1.55, energy 1.3 | The top window of the lock was hot and its symbol washed out | Lamp at y 1.4, energy 1.0 (see Status for the check) |
| `meter_case` at the 1.5 close-up fill | The letter beside the case was flat white | Fill 1.15 for that view |
| A tap right after a cinematic or a camera move is dropped (`RoomBase._on_tap` while `cam.transitioning`) | QA only: the autoclave door after the growth and the second port-rim tap fell back | The playthrough waits for the camera, as a finger would |
| The headless window is square | QA only: the master knob and the port rims fell outside the frame | The headless run sets a 16:9 window |

### Set dressing: Leyla's camp, the crystal shutter wall, the memorial niche (art pass, 2026-10-10)
The newly integrated areas read as empty tiled boxes (`61_memorial_wall`, `62_leyla_camp`, `65_crystal_shutter`, `docs/previews/ch3/`). They are now dressed with three original models (`tools/blender/models/ch3_dress_{camp,corridor,memorial}.py`, shared helper `ch3_dress_lib.py`, build list `build_lists/ch3_dress.txt`), one original grime atlas (`ch3_dress_textures.py` -> `game/assets/textures/dress/ch3_grime.png`, material `M_Dress_Grime`) and two of the CC0 props already in `docs/CC0_PROPS.md`. Every model is built in world coordinates, is one mesh with a surface per material, has **no colliders** (no tap can reach it) and casts **no shadows**.

| Area | Added |
|---|---|
| Leyla's camp (`ch3_dress_camp`, 3.7k tris) | a plank crate beside the cot's head used as a table, with a **tin storm lantern (the camp's key light: a warm omni with a slow 5 % flicker; the bare bulb is now a weak fill)**, three stacked notebooks, an open notebook, a pencil, a tin mug and (CC0) a `seadogs_compass`; a worn brick-brown wool blanket on the sleeping bag with one edge hanging over the cot rail; a paraffin heater with a glowing mica window; a spare battery pack with clamp leads beside the table's cable run; survey maps, a floor plan, a tuning chart, a notebook page and a photo pinned over the tiles with **red cord tied between the tacks** (the cords also tie the blank sheets of `leyla_camp`); grime on the north, south and east walls and the floor |
| Crystal shutter wall (`ch3_dress_corridor`, 2.8k tris) | a painted pipe along the west wall with clamps and a flanged valve with a red wheel, turning up through the roof; a conduit along the north wall with clips, a junction box and a drop to a switch box; a crimson **fire bucket** with sand on a hook under its flame pictogram; (CC0) an `old_gas_mask` on a hook; a **dusty hand cart** with a canvas-covered load and a cable coil; original language-neutral stencils (hazard bolt, flame, flow chevrons, valve glyph) and **one weathered hazard stripe at the shutter's foot, dirtied over** (the only tape in the room); missing tiles aligned to the 0.15 m tile grid, cracks, damp, rust drips, streaks, baseboard and ceiling-line grime |
| Memorial gallery (`ch3_dress_memorial`, 3.9k tris) | the flat marbled wall becomes a **framed niche**: a dark plaster field (`M_Dress_Plaster_Dark`) between two stone pilasters, a cornice and a dark stone plinth, ending short of the shutter tunnel mouth; a carved **inscription band** of abstract strokes and diamonds (no letters); a stone offering ledge with **five candles and a posy of dried flowers in a tin** that Leyla left (soot above them, a small warm omni of 0.5); a worn walnut bench with iron frames facing the wall; streaks and damp on the plaster; the memorial lamp is now a soft 72 degree cone, so the band and the 41 crystals are lit and the niche falls off into the dark |

Wiring (`underground_data.gd` `DRESS` / `DRESS_CC0`, `underground_room.gd` `_build_dressing`): the camp and the shutter wall use a new culling group **J**, drawn only in the camp's own views (`camp`, `shutter`, `recorder`; `groups_for` adds J to every view that has K as a base group). The Nursery views that only look through the camp door (`nursery`, `nursery_w`, `seal`, `prisms`) never draw it: they sit at 147 / 141 / 86 / 125 draw calls and are unchanged. The memorial niche is group G. The two CC0 props are merged by `ModelUtil.merge_static` into one mesh. Flames use `M_Dress_Flame` (emission 0.95, below the environment's glow threshold of 1.1), so a phone shows a warm point and no bloom halo. `--no-dress` (a user argument of the scene) builds the room without any of it: the "before" shots below come from it.

Draw calls per view (`tap_map --perf`, HUD included, 19.5:9, same state before -> after; limit 150):

| State | Views |
|---|---|
| `camp_open` (shutter closed) | camp 83 -> 86, shutter 77 -> 80, recorder 82 -> 85, **nursery 147 -> 147, nursery_w 141 -> 141, seal 86 -> 86, prisms 125 -> 125** |
| `shutter_open` | camp 117 -> 121, shutter 121 -> 125, gallery 89 -> 90, gallery_w 92 -> 93, finale 112 -> 113 |
| `array_awake` (worst case) | camp 121 -> 125, shutter 129 -> 133, memorial 70 -> 71, socket_42 70 -> 71, finale 120 -> 121, console 98 -> 99 |

`choir_s` (145) is untouched: no dressing is drawn in the Choir Hall. The count is per mesh instance (the dressing is 1 to 3 meshes per view); the real surface count of one dressing mesh is 8 to 12 (one per material), triangles 2.8k to 3.9k per model, +6k primitives in the camp views.

Checks run on the final state (2026-10-10):
- `cd game && godot --headless res://qa/check_scripts.tscn`: `checked 96 scripts, 0 broken`; `python3 tools/blender/check_glb_names.py`: `checked 150 GLB files, 0 with reserved names`; `tools/run_tests.sh`: `163 tests, 25416 checks, 0 failures`.
- `tap_map --chapter=ch3 --hud-check --screen=phone61`, 55 views, `camp_open`: `hud-check (phone61): 161 controls in 55 views, 7 failures, 35 banner warnings (280 focus-only controls and 6 slivers not checked)`; 12 views of the camp, shutter, recorder, gallery, memorial, socket, console and finale at `array_awake`: `hud-check (phone61): 30 controls in 12 views, 0 failures, 5 banner warnings (64 focus-only controls and 1 slivers not checked)`. The camp, shutter, recorder, memorial, socket_42 and gallery views list **no** unreachable or off-screen control. The 7 failures of the 55-view run are all pre-existing and outside the dressed areas (`rack` bench 1 and 2, `rack_close` hammer, the four prism-bench knobs in `prisms`: 1.5 to 5 mm from the screen edge, minimum 6); a run of those views with `--no-dress` gives the same 7. **Fixed in the release-candidate QA below.**
- `godot --headless --path game res://qa/playthrough_ch3.tscn -- --quick --key=strand`: `taps through the 3D scene: 102, logic fallbacks: 0`, exit 0; `--key=leyla`: `taps through the 3D scene: 100, logic fallbacks: 0`, exit 0.

Previews at phone aspect (2340 x 1080 renders, stored 1560 x 720), `docs/previews/ch3/dress_<view>_before.jpg` / `_after.jpg`: `dress_camp` (`camp_open`), `dress_shutter` (`camp_open`), `dress_recorder` (`camp_open`), `dress_shutter_open` (`shutter_open`: the tunnel to the dressed Gallery), `dress_gallery` (`shutter_open`), `dress_memorial` and `dress_socket42` (`array_awake`). Cycles checks of the models: `qa/blender/ch3/dress_camp*.png`, `dress_corridor*.png`, `dress_memorial*.png`.

Rebuild: `python3 tools/blender/models/ch3_dress_textures.py` (atlas and the five `M_Dress_*` materials), then `tools/blender/build_all.sh` (the three scripts are in `build_lists/ch3_dress.txt`), then `godot --headless --path game --import`.

### Release-candidate QA (2026-10-10)
Scope: the HUD check at 19.5:9 and 4:3 (and 20:9, 16:9), rendered playthroughs of both Chapter 2 key paths, seed variants, save/reload in the middle of each wing, odd take / return orders, every hint at levels 1 and 2, and what a phone player would trip on. `released` stays `false`: the verdict is at the end.

#### HUD check
The 7 failures of the set-dressing run were pre-existing and were **not** HUD overlaps: the controls sat 1.4 to 5 mm inside the screen edge (minimum 6 mm). The first 4:3 run of this chapter found 2 more, the 16:9 and 20:9 runs 4 more, and the start state 1 more. All are fixed by moving cameras (`underground_data.gd` `VIEWS`); no tap point had to move.

| View | Control | Measured | Cause | Fix |
|---|---|---|---|---|
| `rack` (19.5:9) | `IA_bench_0/1/2`, the bench's three places | 0.4 (sliver), 1.4, 2.9 mm from the bottom edge | the camera looks up at the rack; the bench top is below the eye line | camera 0.9 m east and level: the whole rack and the three places are on screen |
| `rack_close` (19.5:9) | `IA_hammer` | 5.0 mm from the right edge | the hammer stands 1.4 m east of the rack's middle | camera 0.45 m further back, 0.15 m higher |
| `rack_close` (4:3) | `IA_slot_0`, `IA_slot_6` (and `IA_tube_4` after a first try) | 5.1, 5.4 (2.8) mm | the rack is 2.2 m wide | the same move; a 0.2 m shift east had pushed the left tube off the tablet |
| `rack_close` (16:9) | `IA_hammer`, then the bench tubes at the bottom right | 3.3 mm | a wider or lower frame lets the bench peek in | the camera's 0.15 m rise keeps the bench below the frame |
| `prisms` (19.5:9, 4:3) | `IA_p_left/right`, `IA_q_left/right` (apron buttons) | 2.6 mm (phone), 5.5 mm (tablet) from the bottom edge | the apron is below the frame | camera higher and further back, looking down: buttons, prisms and the seal's three receptors sit between the title and the banners |
| `bench` (4:3) | `IA_hammer` | 4.3 mm from the left edge | the hammer is 0.83 m west of the bench's middle | camera 0.2 m west |
| `memorial` (4:3) | `IA_socket_42` | 1.7 mm from the right edge | socket 42 is at x 1.78 | camera 0.25 m east, fov 62 (the arc stays whole on a phone) |
| `grow` (19.5:9, start state) | `IA_peg_2` | 2.8 mm from the right edge | the cam drum's pegs sit at the frame's edge | 0.15 m east, fov 56 (the start lever stays inside on a tablet) |
| `scope` (20:9) | `IA_knob_x`, `IA_knob_y` | 3.9, 4.7 mm from the edges | the knobs beside the scope enter the frame at the edges | fov 40 |
| `switch_room` (16:9) | `IA_passage_w` | under the bag button | the west passage is at the frame's left edge | camera 0.2 m west |

Lines, state `camp_open`, all 55 views (`tap_map --chapter=ch3 --hud-check`):

| | Before | After |
|---|---|---|
| phone61 (19.5:9, 400 dpi) | `hud-check (phone61): 161 controls in 55 views, 7 failures, 35 banner warnings (280 focus-only controls and 6 slivers not checked)` (the set-dressing run); the three views alone: `hud-check (phone61): 39 controls in 3 views, 7 failures, 0 banner warnings (2 focus-only controls and 1 slivers not checked)` | headless, final cameras: `hud-check (phone61): 164 controls in 55 views, 0 failures, 33 banner warnings (289 focus-only controls and 3 slivers not checked)`; rendered (software Vulkan) run of the same cameras: `hud-check (phone61): 164 controls in 55 views, 0 failures, 34 banner warnings (289 focus-only controls and 3 slivers not checked)`, exit 0 |
| tablet10 (4:3, 264 dpi) | the three views alone, old framing: `hud-check (tablet10): 35 controls in 3 views, 6 failures, 0 banner warnings (2 focus-only controls and 0 slivers not checked)`; all 55 views with the phone fixes in: `hud-check (tablet10): 139 controls in 55 views, 2 failures, 23 banner warnings (262 focus-only controls and 0 slivers not checked)` | headless, final cameras: `hud-check (tablet10): 144 controls in 55 views, 0 failures, 23 banner warnings (262 focus-only controls and 0 slivers not checked)`; rendered run of the same cameras: the same line, exit 0 |

The same 55 views in the other game states, final cameras, headless (the tap map's geometry, raycast and HUD layout do not need a renderer; the same 7 failures reproduce headless on the old cameras, within 0.1 mm of the rendered values): 0 failures in all of them.

| State | phone61 | tablet10 |
|---|---|---|
| start | `167 controls in 55 views, 0 failures, 39 banner warnings (250 focus-only controls and 3 slivers not checked)` | `145 controls, 0 failures, 28 banner warnings` |
| `crystal_grown` (seal closed) | `161 controls, 0 failures, 34 banner warnings` | `141 controls, 0 failures, 24 banner warnings` |
| `camp_open` | `164 controls, 0 failures, 33 banner warnings` | `144 controls, 0 failures, 23 banner warnings` |
| `shutter_open` | `166 controls, 0 failures, 34 banner warnings` | `146 controls, 0 failures, 24 banner warnings` |
| `array_awake` | `166 controls, 0 failures, 34 banner warnings` | `146 controls, 0 failures, 24 banner warnings` |

Also 0 failures: phone20 (20:9) `165 to 169 controls` and phone55 (16:9) `160 to 162 controls` at the start and `camp_open` states, and the ten changed views at text size 1.3 (phone61, tablet10) and 1.15 (phone20, phone55). The banner warnings are transient: the story caption or "Nothing happens." covers a control for 2 to 6 s (cabinet locks, seed-library drawers, drum handles, the remelt button).

#### Playthroughs (`tools/qa_run.sh -- res://qa/playthrough_ch3.tscn -- --out=<dir> --key=<path>`, software Vulkan, 1280 x 720 frames)
Rendered, canonical answers, final cameras and strings (every line as printed):
```
--key=strand   ✓ continue: scene rebuilt from the save (state kept, opens at choir, gate open)
               taps through the 3D scene: 108, logic fallbacks: 0 (0 of them for models not built yet)
               QA_DONE exit=0
--key=leyla    ✓ continue: scene rebuilt from the save (state kept, opens at nursery, gate open)
               taps through the 3D scene: 104, logic fallbacks: 0 (0 of them for models not built yet)
               QA_DONE exit=0
```
Seed variants (headless `--quick`, 16:9 window; the per-game answers differ in every one):
```
--key=strand --seed=5                  taps through the 3D scene: 104, logic fallbacks: 0 ...   continue ✓ (opens at choir)    exit 0
--key=leyla  --seed=9                  taps through the 3D scene: 102, logic fallbacks: 0 ...   continue ✓ (opens at nursery)  exit 0
--key=strand --seed=31 --reload-every=3  (twice)  taps ... 125, fallbacks 0   ✓ reload checks (every 3 steps, 149 tappable parts compared each time): 30, failed: 0
--key=leyla  --seed=47 --reload-every=3           taps ... 146, fallbacks 0   ✓ reload checks (every 3 steps, 149 tappable parts compared each time): 31, failed: 0
--key=strand --seed=23 --reload-every=2           taps ... 135, fallbacks 0   ✓ reload checks ...: 48, failed: 0   (earlier cameras)
--key=leyla  --seed=23 --reload-every=2           taps ... 176, fallbacks 0   ✓ reload checks ...: 49, failed: 0   (earlier cameras)
```
One of the first `--seed=31` runs aborted: after `✓ solved prisms` Godot printed `The caller thread can't call the function propagate_notification() on this node` and died with signal 11 (probably the scene rebuild of a `--reload-every=3` Continue; headless, with three other runs competing for the CPU). The same command twice more ran clean. Not reproduced, not explained: see the open issues.

New options of `playthrough_ch3.gd`:
| Option | What it does |
|---|---|
| `--reload-every=N` | Also quits and presses Continue after every N-th solver step, in the middle of a wing (the original check runs once, after the first wing). The rebuilt scene must hold the same logic state, open at the right hall with the gate open, **and show the same tappable parts** (name, position, orientation of every visible collider in the Choir, the Gallery and the Nursery root views, compared once nothing moves). |
| `--logic-sweep [--sweep-seeds=N]` | No scene. The solver's own player actions, one at a time, interleaved with random takes, returns and uses (the no-softlock test's action set and invariants) for both key paths, both lens paths and a per-game seed; a save round trip after every action; from every 4th state a copy made through the save must still finish the chapter. |
| tap-size scan (always on) | Logs the visible size, as a phone61 player sees it, of every part the playthrough taps and lists those under 9 mm on both sides. |
| per-process save files | The save and profile are `user://qa_ch3_save_<pid>.json`: two runs at once used to load each other's save (a rendered strand run once "continued" into a leyla save: `state DIFFERS, opens at nursery`). |

#### Softlocks: save and reload in the middle of each wing, odd orders
```
--logic-sweep --sweep-seeds=75:  logic sweep: 300 games, 62957 actions, 25594 save round trips, 6444 completion checks from saved states   QA_DONE exit=0
```
300 games = 75 per-game seeds x both key paths x both lens paths. Scene level: the reload checks above, 30 to 49 per run, each one a Continue after every 2nd or 3rd atomic player action, in both wings and in the Gallery, with the same logic state and the same tappable parts before and after. No softlock, no lost item and no scene/state drift found. The 240-run random fuzz of `test_underground_no_softlock.gd` (nonsense actions, end-state round trip) is unchanged and passes.
A timing artefact found on the way, not a bug: right after `pull_drum_handle` the blast door slides for several seconds, so a signature taken at once differed from the rebuilt scene's (the door at rest). The check now waits until two signatures in a row agree.

#### Hints at levels 1 and 2
Ch1 and Ch2 name the object to look at; Ch3's level 1 only set the mood ("The desk is dead.") and several level 2 hints said "the plate" or "the wall". Every level 1 and 2 hint of the 12 goals now names an object the player can see, and its place where that is not obvious, with the names of the view captions (`obj3.*`). Strings: `tools/localization/strings_ch3.py` `H` and the 24 rows of `strings.csv` (EN, RU, UZ; level 3 unchanged).

| Goal | Level 1 names | Level 2 names |
|---|---|---|
| `c3_interlock` | the switch room's three cabinets | the interlock plate above them, each lock's key shape |
| `c3_heart` | the meter case in Strand's office | the strip on the lamp in his office |
| `c3_choir` | the tube rack opposite the switch cabinets | the meter, the chalk staircase above the rack |
| `c3_restore` | the control desk, the switch room | the isolators, the interlock plate |
| `c3_startup` | the control desk | the three crystal inspection ports, the counter |
| `c3_seed` | the seed library in the Nursery | Leyla's log on the autoclave, the library |
| `c3_grow` | the autoclave, the growth chart next to it | Leyla's curve on the growth chart, the cam drum's pegs |
| `c3_prisms` | the spectral seal, the prism bench before it | the prisms (tap one to turn it), the three rims of the seal |
| `c3_melody` | the field recorder in Leyla's camp | the recorder's four notes, her crystals, the oscillograph |
| `c3_rings` | the Gallery's glass floor, the blast door | the Array's rings, the door's drum lock |
| `c3_resonance` | Strand's plate on the Gallery console | the Nursery crystal in the console cradle, both knobs, the scope's figure |
| `c3_finale` | the two figures in the Gallery | the 41 memorial crystals |

`tools/run_tests.sh` (hint, localization and layout tests): `204 tests, 28581 checks, 0 failures`.

#### What a phone player would trip on
Measured as a phone61 player sees the parts the playthrough taps (visible size; the collider is that box plus 4 mm, `ModelUtil`): 62 targets, 28 under 9 mm on both sides.

| Finding | Where | Fix or status |
|---|---|---|
| Prisms 5 to 8 mm wide with the turntable, the apron buttons 1.8 mm | `prisms` | **fixed**: a 0.30 m tap cube around each prism (about 10 mm from the new framing): a tap steps the prism and bounces at the ends, a drag turns it; the buttons stay |
| Desk levers 1.6 to 3.3 mm wide (8.8 mm tall), master knob 3.5 x 2.7 mm, the key on the desk hook 1.5 x 2.5 mm | `desk` (overview) | open: the whole desk must stay in one frame to read the plate and the globes; needs a tap-assist radius in `RoomBase.raycast` or a closer view |
| Meter case dials 2.2 to 3.1 x 8.8 mm, cabinet locks 7.1 mm, console knobs 8.2 x 7.6 mm, cam drum pegs 2.9 to 4.3 x 8 mm | `meter_case`, `cabinet_*`, `console`, `cam_drum` | open: the same cause |
| The shutter's four crystals 1.0 to 1.3 mm wide (6 to 8 mm tall) | `shutter` | open |
| Autoclave chamber item 1.8 x 4.6 mm, seed card 2.1 x 3.7 mm, Strand's letters 5.6 x 2.2 mm, the seventh tube 1.8 x 4 mm | `autoclave`, `seed_drawer`, `office`, `rack` | open |
| Ring signs on the glass floor are 3 to 5 mm; the star is a thin sparkle, pale on pale glass | `glass_floor` (the `array_below` model, Blender side) | open: thicken the star, enlarge the signs |
| Dark: the desk's front, the lower left of `rack_close`, the shelf under the bench are near black at default brightness | `desk`, `rack_close`, `bench` | by design (§1.5); the targets themselves are lit |
| The Institute mark (a ring with a meridian bar, `lib_ch3_symbols` `mark`, extruded by `lib_mech.curve_solid`) reads as a thin outline, not a brass band: on the control desk's operator-side face (0.16 m, 4 mm relief) only the right half of the ring's interior has cap faces (mesh check: left 0 %, right 100 %, the ring band 51 % covered); on the Gallery console's plate tab (24 mm, 1.6 mm relief) the whole interior is capped (100 %, band 82 %), a solid disc. Renders: `docs/previews/ch3/bug_mark_control_desk.jpg`, `bug_mark_gallery_console.jpg` (`tap_map --perf --cam=` close-ups) | `desk`, `strand_plate` | open, decoration only: the fix is in the Blender script (build a symbol with holes through `B.plate` with explicit hole loops, as the isolator `m_ring` does); not rebuilt here |
| Bloom: the lit seal receptor (white centre), the drum windows' symbols (white on brass), the card Leyla touches (white rectangle) are the brightest things on screen | `seal`, `drum_*`, `seed_library` | readable, no halo over neighbours; check on a real phone at maximum brightness |

#### Previews (phone aspect, 2340 x 1080 rendered, stored at 1560 x 720, no marks)
`docs/previews/ch3/rc_01_choir_rack.jpg` (`rack`, start), `rc_02_control_desk.jpg` (`desk`, hall running), `rc_03_prism_bench.jpg` (`prisms`, seal closed), `rc_04_leyla_camp.jpg` (`camp`, shutter open), `rc_05_gallery_console.jpg` (`console`, Array awake), `rc_06_finale_gallery.jpg` (`finale`, Array awake). Rendered with `tap_map --perf --screen=phone61`.

#### Open issues and verdict
Open issues:
1. **Tiny tap targets (the one real risk).** 28 of the 62 parts a playthrough taps are under 9 mm on both sides on a 6.1" phone: the desk's five levers (1.6 to 3.3 mm wide), the master knob, the key on the desk hook, the meter-case dials, the shutter's four crystals, the autoclave chamber item, the seed cards. `RoomBase.raycast` has no finger radius and the colliders are the visible part plus 4 mm. It needs a decision outside this chapter's files: a tap-assist radius in `RoomBase.raycast` (smallest part within N mm of the touch), or closer framings with the controls enlarged. Only the prisms were fixed here.
2. **Glass-floor ring signs** (the code the Gallery's door wants): 3 to 5 mm, the star a thin sparkle on pale glass. A model change in `array_below` (Blender side).
3. **One unexplained crash** in 1 of about 14 headless reload runs (`propagate_notification()` from a non-main thread, signal 11, right after `solved prisms`); the identical command ran clean twice more and no rendered run showed it. If a Continue after the Nursery wing can do this on a device, it is a crash on the load path: a device Continue test mid-wing is worth one run.
4. **Localization pipeline drift:** `tools/localization/build_csv.py` run on this tree writes a `strings.csv` without 62 rows that exist only in the committed CSV (`credits.*`, `licenses.*`, `ui.buy*`, `store.*`, `cap2.*`, ...; another agent's edits of `strings_ch1.py` / `strings_ch2.py` are uncommitted). The 24 hint rows were patched into the CSV in place; do not regenerate it until those land.
5. Audio: the zone tones and the finale music still fall back to Chapter 2 tracks (Status table). Nothing was rendered on a real phone GPU or heard on a real speaker; the tests above are software Vulkan and logic.
6. **Ring-shaped extruded marks** (`mark` on the control desk and the console plate) are half-capped / solid, see the table above; the other `lib_ch3_symbols` kinds with holes (`sign`, `sun`, `moon`) in `array_below`, `blast_door` and the keys were not checked.
7. The human-testing list below still stands (interlock plate pictograms, the 1979 loop, the chalk staircase, prism fans on a phone, ring symbols, the recorder keys, brightness).

Verdict for `released: true`: **ready for a closed-testing release, not yet for the public one.** For: 204 tests with 0 failures, the 300-game sweep and 6 clean reload runs (30 to 49 mid-wing Continues each) with no softlock or drift, both key paths rendered with 102 to 108 taps, 0 fallbacks and Continue passing, seed variants clean, the HUD check at 0 failures on 4 screens and 5 game states, every level 1 and 2 hint naming an object in three languages. Against: open issue 1 (a phone player may not be able to hit the desk levers and the hook key at all, and the first puzzle needs them), open issue 3 (an unexplained crash), and no device run. One phone playtest of the desk, the meter case and the shutter crystals, plus a Continue test, would settle it; if the tap-assist radius lands in `RoomBase`, rerun `playthrough_ch3` and the hud-check once.

### Status
| Area | Level | Evidence |
|---|---|---|
| Logic: 11 puzzles, both wing orders, both lens paths, the secret, per-game variants, softlock fuzz | AUTOMATED TESTED (logic) | `tools/run_tests.sh`: 102 tests, 0 failures |
| Scene: §1.2 layout, the 65 §2 views with captions, §1.4 zone culling and portal cards, §1.5 lights (one shadowed spot per zone), environment, zone room tones, the lift descent intro, `SceneManager.room_ready` / CrashGuard safe levels | INTEGRATED | `game/src/rooms/underground/underground_room.gd`, `underground_data.gd` |
| Hotspot routing of every puzzle to `UndergroundLogic`; visuals rendered from `logic.state`; the nine variant evidence surfaces (§11); kept echoes, the 1979 loop, Leyla's touch, the finale and the secret; hints through `hint_goal()` / `hint_args()` | INTEGRATED | `underground_visuals.gd` |
| Full chapter by real 3D taps, both Chapter 2 key paths | AUTOMATED TESTED (3D taps) | `playthrough_ch3 --quick` on 2026-10-10 with every model built (headless): strand path chapter complete, **102 taps, 0 fallbacks**, exit 0; leyla path **100 taps, 0 fallbacks**, exit 0. History: 63 taps / 45 fallbacks (rendered, groups A, C, G, H only) -> 65 / 37 (after the rack) -> 101 / 1 (all models built; the one fallback was the `Item_chamber2` naming bug, fixed) -> 102 / 0 |
| Continue: save → free the scene → rebuild from the save after the first wing | AUTOMATED TESTED (3D) | Both paths pass: state kept, the scene opens at the wing's hall (strand path: the Choir Hall; leyla path: the Nursery), gate open |
| Tap map of the close-ups (`drum_east`, `cabinet_1`, `desk`, `autoclave`, `cam_drum`, `seed_library`, `lift_w`, `switch_room`, `port_b`, `blast_east`, after the rings) | AUTOMATED TESTED (raycast) | Every control reachable; the only orange/red lines are non-targets: the passage mouth at the switch-room frame edge, the port's own lens and ring from inside the port view, and the autoclave seen far through the open east door |
| Models in the scene | ALL BUILT | Groups A to H: 136 GLBs, every scene model of §1.2 (the room lists a model in `missing_models` only while its GLB is absent; the list is empty), all items and echoes. The quick runs start with `models not built yet: none` |
| Views | VISUALLY VERIFIED (software renderer) | `docs/previews/ch3/60_` to `69_` (the newly modelled areas: gallery console, memorial wall, Leyla's camp, recorder, oscillograph, crystal shutter, prism bench, seal door, Strand's office, meter case) and the refreshed `05_evidence_desk`, `25_evidence_glass_floor`, `26_evidence_drum_east`, rendered by `tap_map --perf` in the states named under Tools. The drum-lock symbols, cabinet fronts and Array rings were re-checked on the real models (see the findings above) |
| Audio | IMPLEMENTED | Tube and crystal tones are synthesized (`underground_tones.gd`); zone tones and the finale music fall back to Chapter 2 tracks until Chapter 3's exist |
| Performance | Under budget (≤ 150 draw calls / 150k primitives) | Every model built; `tap_map --perf` (HUD included), worst case over the states `case_open`, `crystal_grown`, `camp_open`, `gallery_awake`, `array_awake`, 2026-10-10. Draw calls per view: **choir_s 145**, desk 135, nursery 132, nursery_w 123, prisms 123, choir 117, finale 113, seed_library 110, port_b 104, switch_room 97, console 95, rack 91, gallery_w 88, office_door 87, office 85, autoclave 85, gallery 84, camp 83, recorder 83, drum_east 78, bench 74, glass_floor 77, seal 76, shutter 76, cam_drum 76, cabinet_1 75, ecg_lamp 73, meter_case 76, drum_west 72, cradle 71, growth_log 71, memorial 70, socket_42 70, interlock_plate 68, lift 58; primitives 9k to 57k (finale the most). `--breakdown` of the two worst: the scene alone is 85 (choir_s) and 75 (desk) draw calls, **the HUD adds about 60** (UX's). Biggest scene contributors in choir_s: three switch cabinets 9 each, control desk 12, shell 8, meter case 8, office desk 7, strand office 6. No batching was needed: the cabinets' numeral and lock-symbol meshes are shown per state (`_apply_cabinets`) and the dials, levers and lamps animate, so `ModelUtil.merge_static` would save about 3 calls per cabinet at the price of a second set of visibility rules. Re-measure after any HUD growth: choir_s has 5 calls of margin |
| Set dressing (camp, shutter wall, memorial niche) | VISUALLY VERIFIED (software renderer), AUTOMATED | Art pass of 2026-10-10, see "Set dressing" above: 3 models + 1 atlas + 2 CC0 props, no colliders; worst-case draw calls 133 (shutter, `array_awake`); `playthrough_ch3 --quick` 102 / 100 taps, 0 fallbacks; hud-check clean in every dressed view |
| Release-candidate QA (HUD at 4 screens, rendered playthroughs, mid-wing Continue, hints) | AUTOMATED TESTED + VISUALLY VERIFIED | 2026-10-10, see "Release-candidate QA": hud-check 0 failures at phone61 and tablet10 (7 and 2 before), strand and leyla rendered `108` and `104` taps with 0 fallbacks and Continue passing, 30 to 49 mid-wing reloads per run without drift, 300-game logic sweep clean, hints at levels 1 and 2 name their object. Open: 28 of 62 tap targets under 9 mm, one unexplained headless crash |
| Released | — | `chapters.gd`: `released: false` |

### Still needs human testing
1. **The interlock plate.** Do players read the pictograms as "key into the lock face, handle to O, the next key comes free"?
2. **The 1979 loop.** Through three ports, is it clear that the globes count the step and each port shows only some of the levers?
3. **The chalk staircase and the meter.** Is "reading 1 = the longest tube" understood from the staircase alone?
4. **The prism fans.** Is the additive colour on the three rims readable on a phone screen?
5. **The ring symbols.** Outer → inner through the glass floor against the drum order on the door.
6. **The recorder keys.** On a phone, are the two ivory piano keys found at once, and is ◀◀ / ▶ read as rewind / play? (Render: readable at 1280 x 720; a phone screen is smaller.)
7. **Brightness.** The Choir Hall is dark by design (the rack and the transformers stay near black at default brightness); the drum windows' brass frames and the console's lamp jewels are the brightest things on screen. Check both at default and at maximum brightness on an OLED phone.
