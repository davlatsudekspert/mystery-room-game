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
| 4 | 7.5 | Tap maps found and fixed covered cards and dividers, a blocked hatch, an unreadable diagram and a too-low projector view | No real-finger test yet |
| 5 | 6 | As for Chapter 1 (UI audit in progress) | Being fixed |
| 6 | 7 | 42 sounds, an ambience and 2 music cues, checked by measurement and spectrogram | Not heard on a device |
| 7 | 5.5 | Hall view: 216 draw calls and ~161k primitives after the first optimisation pass (was 222 / 239k) | Further reduction; FPS on a phone |
| 8 | 8 | Tests pass; real-tap playthroughs pass on both paths and on a variant seed (in progress) | No human run |
| 9 | 8 | Localized decals (badge, cards, rules, labels) in EN/RU/UZ | No native-speaker review |
| 10 | 5 | Not yet released in the chapter list (`released: false`) | Finish the player review, then release |

## Fixes found by QA in this round (see `docs/GAMEPLAY_QA.md`)
- Chapter 2 crash on every "use item" tap: `ItemDB.is_tool` clashed with Godot's `Script.is_tool()`.
- The projector beam rendered as a floor-to-ceiling slab.
- The vault overlay turned the sign the wrong way.
- The dial holes became untappable (a regression), caught by the tap map before release.
- The catalogue's tiny card tabs, covered dividers and a section hidden in the carcass.
- The compressor diagram was unreadable.
- A locker door blocked the floor hatch.
- English words were baked into decals.
