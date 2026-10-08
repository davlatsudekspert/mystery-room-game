# Development Plan

| Phase | Scope | Exit criteria (verified, not assumed) |
|---|---|---|
| 0 | Environment audit, architecture, story, art direction, puzzle graph | Docs committed; toolchain installed and version-checked |
| 1 | Godot project, autoloads, Lab 7 pure logic, test runner | `tools/run_tests.sh` green, including full-solution and no-softlock fuzz |
| 2 | Blender procedural models, CC0 textures, fonts, original audio | GLBs import without errors; license register complete; render screenshots reviewed |
| 3 | Interactive room: camera, interactions, inventory, inspect, combine, all 7 puzzles | Scripted runtime playthrough in the real scene reaches `door_open`; screenshots of each puzzle |
| 4 | Visual polish, animation, lighting states, sound, full UI | Screenshot review pass; no placeholder geometry in the final scene |
| 5 | EN/RU/UZ localization, layout checks, broader tests | Key coverage 100%; overflow checks pass at text scale 1.3 |
| 6 | Android: SDK, export preset, debug APK (+AAB via Gradle) | APK builds and passes `apksigner verify`; on-device test needs the owner's phone |
| 7 | iOS: export preset, safe areas, Xcode notes | Preset committed; build **not verifiable** without macOS (stated) |
| 8 | Store assets, monetization abstraction, release checklist | Checklist + screenshots + listing texts in 3 languages |
