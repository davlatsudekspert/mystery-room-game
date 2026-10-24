# Fresh-player QA, Chapters 1-2 (2026-10-24)

Report only: no game code changed. Screenshots were rendered at 1280x720 (playthrough scenes) and 2400x1080 (tap_map, `--screen=phone20`). Playthrough shots are 16:9, not 20:9, so phone framing was judged only from the tap_map shots I opened (`station`, `splicer`).

## Commands run and results
| Command | Result |
|---|---|
| `git pull origin main`, `tools/setup_env.sh`, `godot --headless --path game --import` | up to date; toolchain ready (Godot 4.7.2, Blender 5.2.2); import ran |
| `tools/run_tests.sh` | 246 tests, 30474 checks, 0 failures (exit 0); leaked-ObjectDB / resource warnings at exit only |
| `tools/qa_run.sh -- res://qa/playthrough.tscn -- --lang=en --seed=7731` | exit 0 (Ch1 EN) |
| same, `--lang=ru --seed=4419 --hold=notebook` | exit 0 (Ch1 RU) |
| same, `--lang=uz --seed=9052` | exit 0 (Ch1 UZ) |
| same, `--lang=en --seed=2288 --store` | exit 0 (Ch1 store) |
| `playthrough_ch2.tscn` `--lang=en --seed=6143` / `--lang=ru --seed=3907` / `--lang=uz --seed=8216` / `--lang=en --seed=5570 --store` | all exit 0 |
| `tap_map.tscn -- --chapter=ch1 --views=all --hud-check --screen=phone20` | exit 0: 93 controls, 36 views, 0 failures, 8 banner warnings |
| same, `--chapter=ch2` | exit 0: 122 controls, 37 views, 0 failures, 27 banner warnings |

Playthrough reports: Ch1 97 taps, 0 logic fallbacks, 3 continue checks failed 0. Ch2 85 taps, 0 fallbacks, 3 continue checks failed 0.
I opened about 50 of the ~170 screenshots (key views per run, not all). Seeds differ per run, so puzzle content differs, which is expected.

## Findings
No blockers found. Every test and run passed.

| # | Sev | Where | Finding |
|---|---|---|---|
| 1 | annoying | Ch2 tap_map phone20, `station`, `splicer` (HUD warnings: 27 in Ch2, 8 in Ch1) | With an item in hand, the "Nothing happens." and "Tap where to use: ..." banners sit over the play area. In `splicer` the prompt covers the scissors and pen, and the message covers the front of the slot row. In `station` the title banner covers the small icons at the top of the tube panel. The tool counts these as warnings, not failures. |
| 2 | annoying | Ch2, all languages, `14_receiver_grille` | Three stacked bottom banners (item card, 2-line description, "Tap where to use") crowd the lower fifth of the screen. The item description is long. In RU and UZ it wraps to two lines. |
| 3 | annoying | Ch1/Ch2, `03_drawer_closeup_locked` (Ch1) and the `Pinch to zoom.` caption (Ch2: `03_catalogue`, `21_dial`, `36_vault_closed`) | A tutorial-style caption shows in the same strip as the scene caption. The pinch hint appears on views where nothing needs zooming, and it overlaps the title strip. |
| 4 | annoying | Ch2, EN, `33_echo_stacks` | Two prompts disagree: the card says "Crystal: Strand's mark", the prompt says "Tap where to use: Crystal: Leyla's sign". It may be two different items, but it reads as a mismatch. The ghost figures on the right overlap each other. |
| 5 | annoying | Ch1/Ch2, notebook overlay (`08_notebook_uv_page`, all languages) | The overlay covers only part of the caption below it. Half-hidden caption text shows under the page ("Hidden ink blooms...", "UV ..."). The bag and pause buttons are dimmed but still visible. |
| 6 | annoying | Ch1 RU `--hold=notebook`, `17_panel_power_restored` | The caption "Блокнот Лейлы сюда не подходит" lands over the panel's top lamp icons and hides them. That is expected for a held-item tap, but it covers the puzzle's key icons. |
| 7 | cosmetic | Ch1, all languages, `37_finale_choice` | The bracketed sound caption (`[Beyond the door, the corridor lamps wake one by one]`) is low contrast and sits right under the title banner. The corridor sign text is unreadable at this size. |
| 8 | cosmetic | Ch2 `30_socket_recorded` | The "Projection screen" view shows a mostly empty wall with a tiny socket. The title does not match what is framed. |
| 9 | cosmetic | Ch2 `41_finale_choice` | The key-choice view has a black blob at bottom left and clutter around the dialog. The dialog is readable. |
| 10 | cosmetic | Ch1 `29_vials_densities`, `27_shadow_misaligned` | An unexplained black plate sits above the vials, and a dark block hangs at the top of the corkboard. The "Lumen shard 5/5" toast is very faint. |
| 11 | cosmetic | Ch2 RU/UZ `49_chapter_complete` | The stat labels wrap: "Головоломок / решено" and "Saqlangan aks- / sadolar" (hyphen split). The values below them are misaligned against the other columns. |
| 12 | cosmetic | Ch2 `07_punch_keys` | The card text ("REQUEST - ARCHIVE B", field labels) is unreadable at phone size. The punch keys are legible. |
| 13 | cosmetic | Ch2 `49_chapter_complete`, all languages | The end card says "To be continued" with only Main Menu, but DEVELOPMENT_STATUS.md says Ch3 is open to testers. The same card also says "Chapters 3 and 4 are on their way". Ch1's card offers "Play". Likely intended for the store build, but it may confuse testers. |
| 14 | info | `--store` runs | The Ch1 and Ch2 store runs looked identical to the non-store runs in the shots I opened. I did not check the purchase panel (not reached in these runs). |

## Language check
- No untranslated English found in the RU/UZ screenshots I opened. These are intentional Latin or English texts: "TABULA RESONANTIARUM", "LUX MEMINIT", and the "ENCYCLOPEDIA" spines.
- The UZ text uses the Latin script with proper o' / g' marks.

## Not covered
- Real 20:9 playthrough shots (only the tap_map phone20 shots).
- Audio and timing: whether captions vanish too fast cannot be judged from still screenshots.
- Purchase panel, settings, and main menu.
