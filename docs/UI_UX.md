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

## Main menu (`main_menu.gd`, `menu_item.gd`, `menu_background.gd`, `menu_atmosphere.gdshader`)
The title screen follows the language of premium mystery games such as The Room: one dramatically lit object in a dark scene, and a quiet text menu beside it. The style is ours: warm brass, walnut and the teal of our logo.
- **Hero object:** Prof. Strand's brass gear box (Chapter 1) stands on Leyla's desk, right of the menu column. The camera aims so that the box centre stays at a fixed point in the free space right of the column, whatever the screen's aspect ratio (`MenuBackground.set_frame()`, `KEEP_WIDTH` camera). It drifts slowly around the box on long, unrelated periods (bearing ±7°, height, distance); the horizon stays level. Its three wheels turn at 3°/s, neighbours in opposite directions as meshing wheels do (all three have 12 teeth, so meshing wheels must turn at the same speed). The desk lamp is the single warm key light: an omni above the box with an inverse-square falloff, so the brass top is the brightest thing in the room. It flickers faintly. A cool moonlight from behind gives the rim. The stopped flip clock (03:17) and Leyla's spectacles stay in the frame as story details. The tea set waits just right of the frame, and the drift brings its cup to the edge now and then.
- **Phone GPU budget:** one shadowed omni (the lamp; unshadowed with safe graphics), one unshadowed directional light, the existing dust motes (off with safe graphics), standard materials only. There are no reflection probes, decals, sky or custom 3D shaders. The desk casts no shadow, so the lamp's shadow pass stays small: about 20 draw calls plus 3 in the shadow pass. Without a probe, brass would only reflect the black background, so the menu uses a half-metallic copy of the brass materials (0.35).
- **Atmosphere** (`menu_atmosphere.gdshader`, a 2D canvas shader over the 3D view): a heavy vignette centred on the box and darkening toward the screen edges, a dark gradient behind the menu column for legibility, and a soft warm glow behind the logo. A little dither keeps the dark gradients free of banding.
- **Menu items** (`MenuItem`): Cormorant Garamond in cream, with no box and no border. Each row is a full-width touch target, at least `UITheme.target(78)` tall (9 mm on a phone; down to 7 mm only on a very short screen with large text). Hover or press warms the text to gold and sweeps in a thin gold rule under it, with a small diamond and tail at its left end. The first item is the primary one (Continue, or New Game when there is no save): it is larger and bold, and shows its rule at rest. On phones and tablets there is no Quit item.
- **Logo:** top of the column, up to 700×525 (it shrinks first on short screens with large text, and hides below 150 px). It sits over a soft warm glow.
- **Version line:** small capitals in the display font under the menu, where a title screen puts its copyright line. Tester builds append the renderer, `last stop` and `safe`. Open panels cover it.
- **Entrance:** the scene comes up out of black (0.9 s) while the logo and its glow fade in. Then the items rise 18 px and fade in one after another, 80 ms apart; everything has settled after about 1.1 s. With Settings → Reduce camera motion, everything is simply there, and the camera and lamp hold still (the wheels keep turning).
- **QA:** `qa/ui_screens.tscn` with `--saved` shows Continue, `--mobile` drops Quit as on a phone, `--highlight=N` shows item N pressed, and `--clean` leaves the cutout zones off the screenshots. Previews: `docs/previews/ui/menu_en.jpg`, `menu_ru.jpg`, `menu_uz.jpg` (6.1" phone, 2556×1179 at 460 dpi, notch insets), `menu_tablet_en.jpg` (10" 4:3), `menu_pressed_en.jpg` (Chapters pressed), and `menu_before_after.jpg`. The "before" half of the comparison is the old menu as a desktop build shows it, without a save (no Continue, with Quit), cropped to the same safe area.
