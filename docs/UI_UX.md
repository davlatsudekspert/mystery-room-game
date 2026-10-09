# UI / UX Specification

## Orientation decision: **Landscape**
| Criterion | Portrait | Landscape |
|---|---|---|
| Room readability (wide 3D interior, multiple props in view) | Narrow FOV, so the room feels cramped and needs more rotation | ✅ Natural horizontal FOV, which matches the room's composition |
| Close-up puzzles (wheels, keypads, switchboards are wider than tall) | Objects must shrink | ✅ Fill the screen with large touch targets |
| Inventory | Bottom bar, 5 slots visible | ✅ Bottom bar, 8 slots plus action buttons |
| Notebook (two-page spread) | Single page | ✅ Authentic two-page spread |
| One-handed use | ✅ Better | Two thumbs, which is acceptable for a seated puzzle game |
| Genre convention for premium 3D puzzle games | Rare | ✅ Common |

Landscape wins on usability for this content. The game locks to `sensor_landscape`.

## Screen map
```
Splash → (first launch) Language picker → Main menu
Main menu: Continue · New Game · Chapters · Settings · (Restore purchases in Settings)
Game HUD: [≡ Pause]                                    [💡 Hint]
          (3D view)
          [◀ Back]  [ inventory slots ......... ]  [👁 Inspect] [⊕ Combine]
Overlays: Inspect item · Notebook · Hint panel · Pause · Settings · Toast · Chapter complete
```

## Design tokens (`game/src/ui/theme_tokens.gd`)
- **Colours:** as in `ART_DIRECTION.md`.
- **Spacing:** 4 / 8 / 12 / 16 / 24 / 32 dp.
- **Radii:** 6 (chips), 10 (panels), 999 (round buttons).
- **Type scale:** design sizes are for a 1920×1080 canvas (body 26, buttons 28, view title 30). `UITheme.size()` scales them for the real screen from its dpi (`UITheme.auto_scale()`, capped at 1.6×; titles grow less than body text), so body text is about **2.6 mm** tall on a 6.1" phone and nothing is smaller than **2 mm**. Settings → Text size multiplies on top: 0.9 / 1.0 / 1.15 / 1.3.
- **Captions over the 3D scene** sit on a dark plate (`UITheme.caption_plate()`): at least 4.5 : 1 contrast even over a white frame.
- **Safe area:** every screen, panel and toast stays inside the display's safe area (`UITheme.safe_margins()`, re-read after a rotation).
- **Touch:** targets are at least **9 mm** (`UITheme.target()`; inventory slots 8.5 mm, sliders 8 mm), with 8 dp spacing between them. `qa/ui_screens.tscn --device=phone61|phone67|phone55|tablet10` measures every text and target in millimetres and fails on anything clipped, off-screen or under a cutout.
- **Motion:** UI 200 ms ease-out. Camera 600 ms cubic in-out. Toasts 2.2 s.

## Accessibility
- Text scale setting with 4 steps, and live preview.
- All text meets WCAG AA contrast (≥ 4.5:1) against the panel background.
- Colour is never the only cue. Projector rings show the colour plus a distinct pattern notch, and lamps show ON/OFF labels.
- Haptics toggle. Reduced camera motion toggle (cuts the transitions to a fade).
- Subtitles/captions for any sound that carries information (e.g. "Breaker tripped").

## Feedback states
Every tap gets a response within 100 ms:
- a sound
- a highlight pulse
- the camera moving, or a short "nothing happens" line
