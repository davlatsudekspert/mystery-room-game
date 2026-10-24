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

## Second pass: remaining screenshots

Report only, no game code changed. I re-rendered everything fresh (the earlier folders were not identifiable): Ch1 EN seed 1101, RU 1202, UZ 1303; Ch2 EN 2101, RU 2202, UZ 2303; tap_map phone20 for ch1 (36 views) and ch2 (37 views). Total rendered: 38+38+38+50+49+49 playthrough shots plus 73 tap_map shots.

**Honest count of screenshots actually opened and seen: 54.** I tried to open all ~340, but most `Read` calls on images returned "[media removed: request limit]" instead of the picture. Only these returned a real image, and only they back the visual findings below:
- Ch2 RU playthrough: 18, 19, 22, 23, 24 and 25-49 (30 images).
- Ch1 tap_map phone20: lab, desk, desk_side, drawer, gearbox, under_desk, radiator, coat, poster, safe, panel, chalkboard, radio, radio_hatch, books, bookshelf, bookshelf_top, door, lock, window, clock, darkroom, darkroom_floor, bench (24 images).
- NOT seen (no image came back): all Ch1 EN/RU/UZ playthrough shots, Ch2 EN and UZ playthrough shots, Ch2 RU 01-17, 20, 21, and the other 12 Ch1 tap_map views and all 37 Ch2 tap_map views. Ch1 and Ch2 UZ and Ch1 RU/UZ got no visual check in this pass at all, so the "no untranslated text" claim of pass 1 is not extended by this pass.

Log-based results (not visual): one new test failure. `playthrough` Ch1 EN seed 1101 reported `continue p6: ... state DIFFERS` (exit 1). The same seed run again passed all 3 continue checks, so it is flaky and not reproducible on demand; worth a look in the save/restore code (nothing else failed; 0 logic fallbacks, tap_map 0 failures, Ch1 8 / Ch2 27 banner warnings as before).

### New findings (from images actually seen)
| # | Chapter | Lang | Screenshot | What is wrong | Severity |
|---|---|---|---|---|---|
| 1 | Ch1 | EN (tap_map) | `lab`, `desk`, `drawer`, `radiator`, `safe` | With an item in hand "Nothing happens." (and "Pinch to zoom.") sit over the lower play area on every view; in `door` and `darkroom` the 2-line hint "Only light and shadow..." covers a third of the upper scene (door glass, corkboard). Same family as #1/#3. | annoying |
| 2 | Ch1 | EN | `radio` | Hidden hotspot `radio_hatch` is under the title banner (tool flags it); `valve_socket` target sits low in the dark on `radio_hatch`, hard to find. | annoying |
| 3 | Ch1 | EN | `chalkboard` | The UV projector prop clips into the bottom left and hides the first letter of "LUX MEMINIT"; "TABULA RESONANTIARUM" poster shows only ~30% of the width on a large grey wall, dots small. | cosmetic |
| 4 | Ch1 | EN | `bookshelf`, `books` | Very dark, blocky black book volumes with only roman numerals partly legible; the 9 numbered spines are hard to read at phone size. | annoying |
| 5 | Ch1 | EN | `bookshelf_top` | Shelf top is a plain wood slab filling the screen, the caption sits over the books below; little to see. A thin light sliver shows behind the top edge (back panel gap). | cosmetic |
| 6 | Ch1 | EN | `drawer` | Black untextured plate behind the four brass wheels looks pixelated/noisy (blocky texture). Same noisy blocky texture on `gearbox` lid and `safe` plate. | cosmetic |
| 7 | Ch1 | EN | `window` | Title "Barred window. The valley sleeps under the moon." is very long; the window has no bars, only a plain glass pane, so the text does not match the view. | cosmetic |
| 8 | Ch1 | EN | `door` | Frosted glass shows a stray thick black stroke (a "7") cut off at the top right, "LABORATORY" is half hidden behind the title banner. | cosmetic |
| 9 | Ch1 | EN | `under_desk` | The grey ring and black square plate on the floor are tiny and flat; nothing says this is a search spot. The title strip is missing here (no title). | cosmetic |
| 10 | Ch2 | RU | 18, 19 `deck_tape_*` | Screenshot names lag one step: file 18 ("1997") shows reel 1996, file 19 shows reel 1997; the 1998 reel is never shown. In 18 the click caption "[Щелчки: • • •]" overlays the encyclopedia spines. | cosmetic (tooling) |
| 11 | Ch2 | RU | 17 caption, 27, 39, 43 | "The Array" is translated "Решётка" everywhere, and the ventilation grille is "Вентиляционная решётка"; two different objects share one word, so "Решётка всё ещё гудит под полом" reads as the vent. | annoying |
| 12 | Ch2 | RU | 28 `lens_case_open` | Huge flat black rock-like blobs fill the left 20% and right 20% of the view (untextured film cans); the lens case is small in the middle. | cosmetic |
| 13 | Ch2 | RU | 30 `socket_recorded` | Top 120 px of the frame is a black void band plus a beige strip above the wood trim (camera sees past the wall); tiny socket on an empty green wall; title "Проекционный экран". (Extends #8.) | annoying |
| 14 | Ch2 | RU | 31 `slides_drawer_open` | 6 of 12 slides are near-black, hard to tell apart; a very large red funnel prop fills the right side. | cosmetic |
| 15 | Ch2 | RU | 33 `echo_stacks` | Card says "Кристалл: знак Странда", the prompt says "Нажмите, где использовать: Кристалл: знак Лейлы" (same as #4, now confirmed in RU). Three ghosts overlap at the right edge and clip into the vault door; the sound caption covers the title lamp. | annoying |
| 16 | Ch2 | RU | 34 `echo_catalogue` | The ghost scientist clips into the file cabinet; the "Освобождено эхо: 1 / 3" toast sits over the prompt line. | cosmetic |
| 17 | Ch2 | RU | 36 `vault_closed` | Title "Хранилище архива — двойной световой замок" is so long it runs from the lamp icon to the plaque and covers both; the pinch hint sits right under it. | cosmetic |
| 18 | Ch2 | RU | 40 `vault_reel` | The film image ends hard at x~885 (right 30% shows wall and boxes), with a white sliver top right: camera/plane mismatch at capture. Possibly a mid-move frame; worth checking on a real device. | annoying |
| 19 | Ch2 | RU | 41 `finale_choice` | The key dialog wraps to two lines and sits over foreground props (green cylinder, bag, black blob bottom left, dark disc); readable, cluttered (extends #9). | cosmetic |
| 20 | Ch2 | RU | 44-46 pit | Three round black patches on the shaft walls (top, right, bottom) look like missing decals; 44 and 47 are almost black (very dark, nothing visible). | cosmetic |
| 21 | Ch2 | RU | 43, 48 | Recorder quote and the "Продолжить" button are dim at capture (fade in); a player on a slow device may think the button is disabled. | cosmetic |
| 22 | Ch2 | RU | 49 `chapter_complete` | "Головоломок решено" wraps and the value "12 / 12" sits lower than the other three values (confirms #11 in RU). | cosmetic |

### Verdict
No blockers found in what I could see. The one failure this pass produced is a flaky Ch1 `continue p6` save/restore check; the most confusing items for a player are the card-vs-prompt mismatch (Strand vs Leyla), the stacked bottom banners, the "Решётка" double meaning in RU, and the possibly cut-off vault reel frame. The check is incomplete: 54 of ~340 screenshots were seen, so Ch1 RU/UZ, Ch2 UZ and EN, and the Ch2 tap_map still need a visual pass.
