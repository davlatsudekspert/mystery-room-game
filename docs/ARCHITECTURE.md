# Technical Architecture

## Engine
- **Godot 4.7.2 stable**, GDScript with static typing.
- **Renderer:**
  - `mobile` (Vulkan/Metal) on Android and iOS, with automatic fallback to `gl_compatibility` on devices without good Vulkan support.
  - `gl_compatibility` for the web demo build.
- **Orientation:** landscape (`sensor_landscape`). See `UI_UX.md` for the portrait vs landscape decision.

## Repository layout
```
mystery-room-game/
├── CLAUDE.md                 # rules for AI-assisted sessions (isolation, tools)
├── DEVELOPMENT_STATUS.md     # verified status per phase
├── NEXT_STEPS.md
├── docs/                     # design + technical docs
├── tools/                    # offline content pipeline (never shipped)
│   ├── setup_env.sh          # installs Godot/Blender/templates in a fresh container
│   ├── blender/              # procedural modelling scripts -> game/assets/models/*.glb
│   ├── textures/             # texture fetch (CC0) + procedural texture generation
│   ├── audio/                # procedural audio synthesis -> game/assets/audio/*.ogg
│   ├── fonts/                # font fetch + coverage checks
│   ├── ui/                   # SVG sources for logo/icons -> PNG via Inkscape
│   ├── run_tests.sh          # headless automated tests
│   └── blender/check_glb_names.py  # rejects node names Godot treats as import hints
└── game/                     # Godot project root
    ├── project.godot
    ├── assets/{models,textures,materials,fonts,audio,ui}
    ├── localization/strings.csv
    ├── src/
    │   ├── autoload/         # global singletons
    │   ├── core/             # pure logic (no nodes): items, room logic, hints, save
    │   ├── rooms/lab7/       # chapter 1 scene + bindings
    │   ├── interaction/      # camera, raycast, interactables, focus views
    │   ├── ui/               # menus, HUD, inventory, inspect, notebook, dialogs
    │   └── fx/               # shaders (UV reveal, dust, lumen)
    └── tests/                # headless test suites
```

## Layering
```
UI (Control scenes)   3D Room scene (Node3D)
        \                 /
         \   signals     /
          ▼             ▼
     GameState (autoload) ── SaveSystem (JSON, user://)
          │
          ▼
     RoomLogic (pure RefCounted, deterministic, fully unit-tested)
```
- **RoomLogic** (`src/core/room_logic.gd` base, `src/rooms/lab7/lab7_logic.gd`) holds the whole puzzle state as plain data.
  - Every player intent is a method (`set_drawer_wheel`, `press_gear`, `combine`, `use_item_on`, `toggle_switch`…).
  - Each method returns an `ActionResult` with `events` (strings such as `"drawer_opened"`, `"item_added:uv_lamp"`).
  - It has no scene-tree access, so the tests can play the entire chapter headlessly in milliseconds.
- **Room scene** listens to `GameState.events` and plays the corresponding animation, sound and VFX. Visual state is always rebuilt from the logic state (`apply_state()`), so loading a save restores the exact visuals.
- **Interactables** (`src/interaction/interactable.gd`) are `Area3D`/`StaticBody3D` with an `action_id`. On tap, the room script maps `action_id` to a RoomLogic call, or to a camera focus change.

## Autoloads
| Autoload | Responsibility |
|---|---|
| `Settings` | Language, volumes, text scale, haptics, invert-look; persisted in `user://settings.cfg` |
| `Loc` | Language detection (`OS.get_locale_language()`), EN fallback, switching, font selection per language |
| `GameState` | Current chapter, RoomLogic instance, inventory facade, event bus, autosave (debounced) |
| `SaveSystem` | Versioned JSON saves (`user://save_v1.json`), atomic write via a temp file and rename, migration hook |
| `AudioManager` | Buses Master/Music/Ambience/SFX/UI, crossfading music, pooled 3D/2D SFX players |
| `SceneManager` | Fade transitions, loading screen, back-stack for menus |
| `Hints` | Evaluates hint goals against the RoomLogic state; returns a 3-level ladder |
| `Premium` | Entitlements (`full_game`), purchase/restore via a provider interface (Mock / Google Play / App Store) |

## Inventory & items
- `ItemDB` (`src/core/item_db.gd`) is a static table of `id → {name_key, desc_key, model, icon, inspectable}`.
- `Inventory` is part of the RoomLogic state. It holds an ordered list of ids plus the selected id.
- Combination recipes are data: `[["uv_lamp_empty","battery_cell"] → "uv_lamp"]`, and order does not matter.

## Save format (v1)
```json
{ "version": 1, "chapter": "lab7", "state": { ... RoomLogic.to_dict() ... },
  "stats": {"play_time_s": 734, "hints_used": 2}, "timestamp": 1760000000 }
```
- Only ids and numbers are saved, never translated strings, so saves are language-independent.
- Unknown keys are ignored, and missing keys fall back to defaults. This keeps saves forward-compatible.

## Localization
- Godot `TranslationServer` with `localization/strings.csv` (`keys,en,ru,uz`). The CSV is imported to `.translation` files.
- Keys follow the pattern `area.object.detail` (for example `item.uv_lamp.name`, `nb.page2`, `hint.h4.2`).
- First launch shows a language picker preselected from the device locale. Unsupported locales fall back to EN.
- Uzbek uses Latin with U+02BB (ʻ) for oʻ/gʻ and U+02BC (ʼ) for tutuq belgisi. Fonts were verified to cover these, with Noto Sans as the fallback.
- Russian text runs about 30% longer, so every label uses autowrap and containers that grow. The layout tests check for overflow at text scale 1.3.

## Input
- **Touch:**
  - one-finger drag rotates the view (yaw ±180°, pitch clamp −35°…+30°)
  - pinch zooms (FOV 38°–70°)
  - tap interacts
  - two-finger tap or back button returns from a focus view
- **Mouse** (desktop and web QA): left-drag rotates, wheel zooms, click interacts, right-click or Esc goes back.
- **Tap vs drag:** a gesture counts as a tap if it moves less than 12 dp and lasts less than 350 ms.

## Camera
- One `RoomCamera` with a stack of **views** (`Marker3D` + FOV).
- The root view is free-look from the room centre. Focus views (desk, drawer lock, gear box, safe, panel, projector, poster, clock, bench, door) are entered by tapping their hotspot.
- Transitions are tweened (0.6 s, cubic in-out) along position and quaternion. Input is locked during a transition.

## Premium content access
- `Premium.has_entitlement("full_game")` gates chapters 2–5. Chapter 1 is always free.
- Providers:
  - `MockStoreProvider`: debug builds and tests.
  - `GooglePlayBillingProvider`: activates when the `GodotGooglePlayBilling` plugin singleton exists.
  - `AppStoreProvider`: activates when the iOS StoreKit plugin singleton exists.
- `REAL_PAYMENTS_ENABLED` is **false** until the store products are configured and validated.
- There are no ads, subscriptions or energy systems.

## Testing
- `tools/run_tests.sh` first checks the GLB node names (`tools/blender/check_glb_names.py`), then runs `res://tests/run_all.tscn` headless. It is a scene, so the autoloads exist. The runner is a custom zero-dependency runner and exits non-zero on failure.
- Test suites (`game/tests/`):
  - `test_lab7_puzzles`: each puzzle, wrong inputs, full solution path
  - `test_no_softlock`: 300-seed random-play fuzz, then the scripted solver must still finish
  - `test_save_load`: save/load round-trip through JSON, corrupted data falls back to defaults, saves are language-independent
  - `test_localization`: every key in all 3 languages, placeholders, glyph coverage of the fonts
  - `test_hints`: hint goals advance monotonically to "done" along the solution, and every goal has 3 translated levels
  - `test_settings_premium`: settings persistence, atomic saves with backup, save/continue cycle, premium rules, hint escalation
  - `test_layout`: button and message text fits at text scale 1.3 in EN/RU/UZ
- `game/qa/` holds the runtime QA scenes. They run the real renderer under Xvfb (Vulkan lavapipe).
  - `room_preview.tscn` renders review shots to `docs/previews/`.
  - `playthrough.tscn` plays Chapter 1 by tapping the real 3D parts. It writes screenshots, draw-call and memory stats, and a report. A step that needs a logic fallback counts as a failure. `--from=pN` / `--to=pN` limit the run, and the solver plays the earlier puzzles.
  - `ui_screens.tscn` renders the menus and overlays in EN/RU/UZ.
  - `check_scripts.tscn` load-checks every script.

## Performance budgets (mid-range Android, e.g. Adreno 610 / Mali-G57)
| Budget | Limit |
|---|---|
| Frame time | 30 fps minimum, 60 fps target in focus views |
| Draw calls | ≤ 150 |
| Triangles | ≤ 150k visible |
| Shadow-casting lights | 2 at most |
| Texture memory | ≤ 200 MB |
| APK size | target < 150 MB |
