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
- **Type scale (at text scale 1.0):** caption 18, body 22, title 30, display 56. The user text-scale setting multiplies these: 0.9 / 1.0 / 1.15 / 1.3.
- **Touch:** minimum target 56 dp, with 8 dp spacing between targets.
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
