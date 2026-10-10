# VR roadmap: OpenXR / Meta Quest (audit only, no VR work started)

Status: 2026-10-10. This is a desk audit of the code and docs as they are. No XR code, plugin or export setting was added or run, and nothing here was tested on a headset (the dev container has none). Facts about the game come from the files named in each row. Statements about Godot's and Meta's XR behaviour are from general knowledge of Godot 4 and Quest and must be re-checked against the 4.7 and current Meta docs before work starts. Numbers marked "est." are estimates.

## Verdict

- The **puzzles, saves, hints, localization, item data and models** are ready for VR as they are. That is the bulk of the game's value.
- The **camera, input and HUD** are phone-only (a tweened view-stack camera, finger gestures in screen pixels, a screen-space `CanvasLayer`). They must be replaced, not adapted.
- The hardest part is **comfort and performance**, not code: the camera moves, glides, zooms and flashbacks are all things VR forbids, and the stereo frame rate (72 to 90 Hz) asks about 2 to 3.5x the pixels per second of a phone at 60 fps (est.).
- A first playable ("walk the Chapter 1 lab with a hand ray") is a small project. A shippable Quest game with all chapters is a large one.

## What carries over as is

| Area | Where | Why it carries over |
|---|---|---|
| Puzzle logic | `game/src/core/room_logic.gd`; `game/src/rooms/{lab7,archive,underground}/*_logic.gd` (3,236 lines) | Pure `RefCounted`, no scene access (checked: no `Node`, `get_tree`, `Input` or autoload use). Every player intent is a method that returns events. The headless solvers and fuzz tests in `game/tests/` keep proving it, whatever the front end is |
| Hints | `*_hints.gd` | Evaluate goals against logic state only |
| Items | `game/src/core/item_db.gd`, `item_dress.gd` | Data tables |
| Saves | `SaveSystem`, `GameState` | Versioned JSON of ids and numbers, language-independent, atomic writes. VR adds only settings keys (comfort options) |
| Localization | `game/localization/strings.csv`, `Loc`, `tr()` | Text is already keyed and EN/RU/UZ. World-space panels need new fit tests, not new strings |
| Models | 107 GLBs, 69 MB (`game/assets/models`) | Built in metres: the camera's eye height is 1.45 m and focus views sit 0.26 to 0.5 m from props, so they are close to real scale. Textures are ASTC-capable (`import_etc2_astc=true`), which Quest supports |
| Audio | `AudioManager`, 12 MB | Buses and 3D players carry over. Positional audio matters more in VR, so spatialization is a tuning task |
| Room "visuals" | `*_visuals.gd`, `apply_state()` | They rebuild the scene from logic state, so a different rig can show the same state |
| Hotspot data | `RoomBase`: `hotspot_view()`, `deeper_views()`, `in_reach()`, `use_target()`, `resolve()`, the tap colliders (`StaticBody3D` with `part` / `hotspot` meta) | They do not depend on the screen once a ray exists. Only `raycast(screen)` and `_on_tap(screen)` take screen coordinates |
| QA | solvers, `tap_map`, `view_probe`, perf logs in `playthrough.gd` | The logic-level parts are reusable. The renderer-level parts (Xvfb, lavapipe) cannot run an XR session |

## What must change

| Area | Today | In VR | Work |
|---|---|---|---|
| **Camera** | `RoomCamera` (`game/src/interaction/room_camera.gd`): a stack of views, yaw 360 and pitch -38..32 deg, pinch FOV 32..72, tweened moves of 0.55 to 0.9 s along an arc, a swipe that glides on, a handheld sway in focus views | The headset owns the camera pose and the FOV. The game may move only the rig (`XROrigin3D`), never the head. Zoom, glide, sway and tweened moves must go | Keep the idea of views, as **stations**: reuse each view's `pos` as a standing or seated anchor and `target` as the direction to face. A focus view becomes "step to this station" (blink teleport) or "lean in", and small props are grabbed and held to inspect. Provide the same `view_changed` signal from an XR adapter so the HUD, hints and `view_changed_hook` keep working |
| **Selecting things** | `TouchInput`: tap, drag, pinch, two-finger tap in screen pixels; `RoomBase.raycast(screen)` picks the smallest part within 0.18 m behind the first hit (`DEPTH_WINDOW_M`) | `XRController3D` (or hand tracking) with trigger, grip and a ray from the controller pose. Back = a button, not a two-finger tap | `raycast(origin, dir)` plus a thin screen wrapper for phones. Hover highlight, haptics (replaces `Input.vibrate_handheld`), snapping and larger targets for ray jitter. Small controls (drawer wheels, radio knob) were already flagged for real-finger tests in `QUALITY_REPORT.md` |
| **Gestures with pixels** | Knobs and dials: `drag_part_started` / `drag_part(rel: Vector2)` in `archive_room.gd` and `underground_room.gd`. The UV lamp is aimed by a screen position (`_uv_aim`, `project_ray_normal` in `lab7_room.gd`) | Twist or grab-and-turn with the hand; the lamp is a tracked held object | New interaction per puzzle control (about a dozen types). The logic calls stay the same |
| **HUD** | `hud.gd`: a `CanvasLayer` (layer 10) of `Control`s anchored to the screen with safe-area insets, millimetre touch targets (`UITheme`), banners, a left inventory column, overlays (documents, notebook, inspect, hints, pause, intro, finale) | A screen-space layer is not shown in XR, and head-locked UI is uncomfortable | Render the same `Control` trees into `SubViewport`s on quads in the world (or composition layers for sharp text, if the 4.7 OpenXR plugin supports them on Quest). Inventory on the wrist or a belt, banners and subtitles as lazy-follow world UI, documents as held papers. Re-run the layout tests (`test_layout.gd`) for the new panel sizes at EN/RU/UZ (RU is about 30 % longer) |
| **Fades and loading** | `SceneManager` fades with a 2D layer; scene build is slow on the CPU renderer (about 6 s in QA) | The compositor must keep running; a frozen frame in a headset is a comfort problem | Fade with a head-attached quad, load asynchronously, show a lightweight lobby |
| **Scripted camera moments** | Intro, the 1979 flashback, the bookcase reveal camera, the echo turning toward you (`DEVELOPMENT_STATUS.md`) | The player's head cannot be steered | Re-stage as world events (light, sound, props moving) with the player free to look away; check each |
| **Renderer** | `mobile` (Vulkan/Metal), `msaa_3d=1` (2x), glow, fog, tone mapping and adjustments in `make_environment`; a ReflectionProbe, decals, dust particles; per-room lights with 2 or 3 shadow casters; no baked lighting. No shader reads the screen or depth texture (checked), which is good for XR | Quest runs Android, so the same `mobile` renderer can be used with OpenXR (`Viewport.use_xr`, multiview). Moving to Compatibility stays a fallback (the project already has `fallback_to_opengl3` and a web preset on it) | Enable OpenXR in the Android export (the preset has `xr_features/xr_mode=0` today) and the Meta vendor plugin; budget MSAA (2x to 4x), foveated rendering, drop or bake glow and extra shadows. `CrashGuard` safe levels 1 to 3 (no MSAA; no positional shadows, probes or particles; no decals, glow or sun shadow) are a ready-made quality ladder |
| **Performance budgets** | `ARCHITECTURE.md`: 30 fps minimum, 60 fps target; 150 draw calls, 150k visible triangles, 2 shadow lights, 200 MB texture memory per view. Measured: Ch1 lab 94 to 99 draws and about 175 to 183k primitives (over budget), Ch2 hall 144 draws and about 86k primitives (`QUALITY_REPORT.md`). No FPS has been measured on any phone yet | 72 to 90 Hz means 13.9 to 11.1 ms per frame; rendering is done for two eyes | See below |
| **Comfort** | Forced camera moves everywhere (see Camera) | No forced camera motion at all | Teleport with a short blink, or station hops; snap turn (30 to 45 deg) by default, smooth turn optional; seated and standing modes with a height offset (the rooms assume a 1.45 m eye); an optional vignette; no head bob or sway; stable horizon; keep Settings entries `look_sensitivity`, `invert_look` and `reduce_motion` only for the flat version |
| **Store and billing** | `Premium` providers: Mock, Google Play, App Store. `REAL_PAYMENTS_ENABLED = false` | Quest uses the Meta store and its own entitlement check | A new provider behind the existing interface; privacy, age rating and store rules for the platform |

### What the 150 draw-call budget means in VR

- The budget is measured at hand-authored views. Root views already allow a 360 degree look, so the hall number is a fair proxy; but focus views may be cheaper partly because `view_changed_hook` (per-view lighting and visibility culling) hides or relights the rest. In room-scale the player can look at everything from many places, so the budget must hold for the **worst viewpoint over all stations and all yaws**, not per authored view. Extend `tap_map --breakdown` and the perf log to sweep stations.
- With multiview the scene is submitted once and drawn for both eyes: draw calls stay about the same, but vertex and pixel work doubles. The CPU time per frame shrinks to 11 to 14 ms. Meta's guidance for Quest is often quoted in the low hundreds of draw calls and about 0.75 to 1 M triangles for a Quest 2 class headset (to be checked), so 150 calls is the right order, but the Chapter 1 lab (about 180k primitives, with stereo doubling the vertex load) is over what it should be. Treat 100 to 150 calls and about 100k visible triangles as a starting hypothesis and measure.
- Pixels are the bigger change: a 2400x1080 phone at 60 fps is about 155 Mpx/s, and a Quest 2 at default per-eye resolution (about 1440x1584) at 72 Hz is about 330 Mpx/s (est.), a Quest 3 at 90 Hz about 530 Mpx/s (est.). The headset GPU is stronger than the budget phone the project targets (Adreno 610 / Mali-G57), but it has to push 2 to 3.5 times as many pixels, at a frame rate that must never drop. `PerfGuard`'s render-scale ladder (100 % down to 60 %) is a useful idea, but dynamic resolution in VR needs care.
- Dynamic shadows, glow, decals and the reflection probe cost fill rate. Baked lighting (`LightmapGI` works on the mobile renderer) and occlusion culling would help most and are unused today.

## Risks

1. **No hardware, no XR runtime here.** Nothing can be verified in this container: it has no headset, and Xvfb with lavapipe cannot run an OpenXR session. The owner needs a Quest, and a way to test without one (a runtime simulator on a PC) has to be chosen. Keep the XR layer thin and the logic-level QA as the safety net.
2. **Performance is unmeasured even on phones.** `QUALITY_REPORT.md` scores performance 6 with no FPS on a device; the iOS reports in `docs/TESTING_ON_DEVICE.md` (a black screen after New Game, crashes in builds 5 and 6, probably first-run shader compilation on Metal) show that shader and load hitches are a real risk on mobile GPUs. In a headset a hitch is a comfort problem, so shaders must be warmed up before play.
3. **Comfort and scripted moments.** Every forced camera move and cutscene is a rewrite, and the chapters are still growing.
4. **Content seen from everywhere at 1:1.** Props were authored for a handful of views: backs, undersides and gaps, texture resolution per degree, decal-faked details, fake bounce lights. A room-scale player will see all of them. Needs a visibility audit.
5. **Duplicated code before unification.** `room_base.gd` says Chapter 1's `Lab7Room` "keeps its own copy" of the camera and input code, so there are two code paths to port. Merge them first.
6. **Interaction precision.** Taps were tuned for fingers; a hand ray at 1 to 2 m jitters. Small parts need larger or snapped targets and hover feedback.
7. **Plugins, licence and store.** XR addons (the Meta vendor plugin, XR Tools if used) must match Godot 4.7.2 and be recorded in `docs/ASSET_LICENSES.md`; a Meta developer account and the store review add lead time. Billing stays off until validated.

## Roadmap and rough effort

One developer, full time, with AI assistance, no surprises. Ranges are rough and cumulative risk is high; widen them if hardware access is limited.

| Phase | Content | Effort |
|---|---|---|
| **0. Prepare** (also helps phones) | Decide seated or room-scale first. Merge `Lab7Room` into `RoomBase`. Make `raycast` take a ray and `drag_part` a neutral delta. Split "view" (a place) from "camera tween". Measure real FPS on a phone for a baseline. Get a Quest | 1 to 2 weeks |
| **1. XR boot and rig** | OpenXR in the Android export, `XROrigin3D` rig, stations from the views, blink teleport, snap turn, seated and standing height, controller ray, haptics; the Chapter 1 lab walkable with no UI | 2 to 3 weeks |
| **2. Interaction and world UI** | Pointer on the shared `resolve` code, hover, grab and inspect, knob, wheel and lamp gestures, HUD to world space (wrist inventory, banners, documents, hints, pause), lobby and menus, async loading and head fades | 3 to 5 weeks |
| **3. Rendering and performance** | Stereo budgets, baked lighting, fewer dynamic shadows, drop or bake glow, occlusion and LODs, texture budget, foveation, shader warm-up, hold 72 Hz (90 where possible) on Quest 2 and 3 | 3 to 6 weeks, iterative |
| **4. Content and comfort pass** | Re-stage cutscenes, audit back-geometry and scale, spatial audio, comfort options and tutorial, XR playthrough QA per chapter (about 1 to 2 weeks each) | 3 to 6 weeks for the current three chapters |
| **5. Store and polish** | Meta store provider and entitlements, privacy and age rating, device testing, fixes | 2 to 4 weeks |

**Total about 14 to 26 weeks** for a shippable Quest build of the current chapters; a first playable (the lab walkable with a hand ray) after phases 0 and 1, in about 3 to 5 weeks.
