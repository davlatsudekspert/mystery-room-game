# Gameplay QA

How each chapter has been checked. The five status levels are never mixed:

| Level | Meaning |
|---|---|
| **IMPLEMENTED** | The code or asset exists. |
| **INTEGRATED** | It is wired into the real game scene and reachable by a player. |
| **AUTOMATED TESTED** | A script exercised it and checked the result: logic tests, or real raycast taps through the 3D scene. |
| **VISUALLY VERIFIED** | Someone looked at real Godot screenshots of it (not Blender renders). |
| **HUMAN TESTED** | A person played it on a device. |

**Nothing is HUMAN TESTED yet.** No physical phone has run the game. Automated play proves the chapter can be finished and does not break; it does not prove the chapter is fun or clear. Only playtesters can tell us that.

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
| Locked drawer message | AUTOMATED TESTED (logic) | The review tapped the middle of the drawer, which is where the code wheels sit, so it turned a wheel instead of pulling. The message exists in code (`msg.drawer_locked` + sound). The review now pulls the drawer by the side of its front |
| Hints, 3 levels | AUTOMATED TESTED (3D UI) | Level 1 → 2 → 3, the button disables at level 3, Back closes the panel |
| Save, quit, continue | AUTOMATED TESTED | The continued state equals the saved state, and the intro does not replay |
| Language switch mid-game (EN → RU → UZ) | AUTOMATED TESTED + VISUALLY VERIFIED | View titles and the pause menu change at once; screenshots checked |
| Finale choice cannot be dismissed with Back | AUTOMATED TESTED | |
| Dark (unpowered) lab readability | VISUALLY VERIFIED | Before the fix the south-west and south views were almost black (mean brightness 2–3 of 255). A cool moonlight bounce and a higher dark ambient raised them to 18–23 while the power-on change stays dramatic. See `docs/previews/ch1_dark_state_before_after.jpg`. A brightness slider in Settings covers dim phone screens |
| Main menu with the logo (EN/RU/UZ) | VISUALLY VERIFIED | `docs/previews/ui/main_menu_logo_en_ru_uz.jpg`; the logo subtitle is translated in each language |
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

### Status
| Area | Level | Evidence |
|---|---|---|
| Puzzle logic P1–P12 + both Chapter 1 lens paths | AUTOMATED TESTED (logic) | `test_archive_puzzles.gd`, `test_archive_no_softlock.gd` and the archive solver run in `tools/run_tests.sh` |
| Room scene (`archive.tscn`: views, every interaction, film, canister and vault sequences) | IMPLEMENTED | Scripts parse (`qa/check_scripts.tscn`: 0 broken) |
| 3D models (41) | IMPLEMENTED, partly | `docs/models/CH2_MANIFEST.md`: 19 ready, 1 slightly over budget, 21 still being built |
| Audio (42 sounds, ambience, 2 music cues) | IMPLEMENTED | Rendered and imported in Godot; loop flags confirmed on the 4 looping effects. Checked by measurement and spectrogram only, not by ear |
| 3D playthrough, both lens paths (`qa/playthrough_ch2.tscn --lens=take` / `--lens=leave`) | not yet run | Waits for the remaining models |

The estimated duration is 30–40 minutes for a first-time player. That is the design target, not a measurement.

The real-scene results, the screenshots and the list of things that need human testing will be added here once the 3D playthrough runs.
