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
| Dark (unpowered) lab readability | VISUALLY VERIFIED | Before the fix the south-west and south views were almost black (mean brightness 2–3 of 255). A cool moonlight bounce and a higher dark ambient raised them to 18–23 while the power-on change stays dramatic. See `docs/previews/ch1_dark_state_before_after.jpg`. A brightness slider in Settings covers dim phone screens |
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
