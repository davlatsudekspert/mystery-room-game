# Preview renders (real Godot 4.7.2 renders, Mobile renderer, software Vulkan)

| File | What it shows |
|---|---|
| `player_view_north_*` | Main camera, the player's standing point (0.2, 1.55, 0.25), looking at the desk and the window |
| `main_camera_east_*` | Looking at the exit door, Panel 7, the light lock, the mirror stands and the safe |
| `player_view_west_*` / `player_view_south_*` | Bookcase wall / lab bench and poster wall |
| `desk_closeup_*` | Desk focus view: flip clock 03:17, drawer combination wheels |
| `overview_cutaway_*` | Top-down cut-away of the whole layout (ceiling hidden) |
| `scene_tree.txt` | Node tree plus the list of placed and missing models |

The `_dark` renders show the state before power is restored: moonlight, the desk lamp and the red maglock. The `_powered` renders show the state after Panel 7 is solved.
All models are final Chapter 1 models now; there are no placeholder boxes left.

## `playthrough/`: the automated 3D playthrough (`qa/playthrough.tscn`, 2026-10-08)
Frames from a run that finished Chapter 1 entirely through taps on the real scene: 13/13 steps and 5/5 Lumen shards, 100 taps, 0 logic fallbacks (`playthrough_report.txt`). The highlights are:
- `04_drawer_open_0317`: the drawer lock showing 0317;
- `21_bookcase_open`: the bookcase reveal, filmed from outside the swing arc;
- `26_shadow_emblem_recorded`: Light Memory;
- `30_projector_beam_on`: the Lumen beam;
- `32_finale_echo_1979`: Leyla's light echo at her desk, closed as in 1979;
- `35_chapter_complete`.

## `ui/`: menus and overlays in EN / RU / UZ (`qa/ui_screens.tscn`)
These cover the trilingual language picker, the dimmed settings panel, the main menus, a hint, the pause menu, the inspect view, the notebook, the finale choice and the chapter-complete screen.
`menu_en.jpg` / `menu_ru.jpg` / `menu_uz.jpg` (phone), `menu_tablet_en.jpg`, `menu_pressed_en.jpg` and `menu_before_after.jpg` show the main menu redesign (gear box hero, serif text items; see `docs/UI_UX.md` → Main menu). The older `en_main_menu.jpg` / `uz_main_menu.jpg` / `main_menu_logo_en_ru_uz.jpg` show the previous menu.
`settings_before_after.jpg` and `hud_before_after.jpg` show the 2026-10-10 UI pass (readability presets, the settings panel redesign, the HUD banners and inventory column) against the previous build, both on the owner's iPhone profile (2556×1179 @ 460 dpi, notch insets). `settings_phone_{en,ru,uz}.jpg` and `hud_item_found_{en,ru,uz}.jpg` are the same screens in the three languages at Text size Normal (see `docs/UI_UX.md` → Settings, HUD, Reader).
