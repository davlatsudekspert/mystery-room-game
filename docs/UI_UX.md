# UI / UX Specification

## Orientation decision: **Landscape**
| Criterion | Portrait | Landscape |
|---|---|---|
| Room readability (wide 3D interior, multiple props in view) | Narrow FOV, so the room feels cramped and needs more rotation | ✅ Natural horizontal FOV, which matches the room's composition |
| Close-up puzzles (wheels, keypads, switchboards are wider than tall) | Objects must shrink | ✅ Fill the screen with large touch targets |
| Inventory | Column of 4 slots | ✅ Column on the left, 5 slots visible, scrolls |
| Notebook (two-page spread) | Single page | ✅ Authentic two-page spread |
| One-handed use | ✅ Better | Two thumbs, which is acceptable for a seated puzzle game |
| Genre convention for premium 3D puzzle games | Rare | ✅ Common |

Landscape wins on usability for this content. The game locks to `sensor_landscape`.

## Screen map
```
Splash → (first launch) Language picker → Main menu
Main menu: Continue · New Game · Chapters · Settings · (Restore purchases in Settings)
Game HUD: [◀ Back]        ◆ VIEW TITLE ◆             [💡 Hint]
          [slot]               caption line
          [slot]|  (3D view)
          [slot]|  [👁][⊕] (beside the selected slot)
          [slot]           message / item found banner
                           "Use X on…" prompt          [II Pause]
Overlays: Reader (documents, inscriptions) · Inspect item · Hint · Pause · Settings · Toast · Chapter complete
```

## Design tokens (`game/src/ui/theme_tokens.gd`)
- **Colours:** as in `ART_DIRECTION.md`.
- **Spacing:** 4 / 8 / 12 / 16 / 24 / 32 dp.
- **Radii:** 6 (chips), 10 (panels), 999 (round buttons).
- **Type scale:** design sizes are for a 1920×1080 canvas (body 26, buttons 34 in display small caps, view title 30, reading text 40). `UITheme.size()` scales them for the real screen from its dpi (`UITheme.auto_scale()`, capped at 3.2×): body text reaches a **3.0 mm cap height** (`BODY_CAP_MM`, about 4.2 mm em) at Normal on any phone or tablet (about 2.7× on a 6.1" phone at 460 dpi, 1.6× on a 10" tablet, 1× on a desktop), and nothing the player must read is smaller than **3 mm** em. From body size up to 72 px the boost tapers to half, so titles keep leading body text. Settings → Text size multiplies on top: **Normal 1.0 / Large 1.25 / Extra large 1.5** (`Settings.TEXT_SCALES`; older saves snap to the nearest preset). At Large and Extra large nothing overlaps: panels drop to one column and scroll, segmented controls stack, button rows wrap, and a newer HUD banner fades an older one it would cover.
- **Contrast:** secondary text is `MUTED` b5ab97 (≥ 8:1 on panels). Every line over the 3D scene sits on a dark band or plate at 0.8 alpha (`UIBanner`, `UITheme.caption_plate()` for toasts): cream text ≥ 7:1 and muted text ≥ 4.5:1 even over a white frame.
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

## Settings (`settings_panel.gd`, `ui_segmented.gd`, `ui_switch.gd`, `ui_ornament.gd`)
A dark plate with a hairline gold frame (and a fainter second rule inside it), the title in the display serif over the menu's gold rule with a diamond, and four sections under small-caps headers whose hairline runs to the column's edge: **LANGUAGE** (a segmented control of the native names), **SOUND** (music, sound effects, ambience), **DISPLAY & COMFORT** (text size as a segmented control of the three preset names, each drawn at its own size; brightness; reduce camera motion) and **OTHER** (vibration; simplified graphics with a one-line muted description, `ui.safe_graphics_desc`).
- **Rows:** the label on the left, the control on the right, one touch target tall (`UITheme.target(78)`, 9 mm), hairlines between them. Sliders are thin with a gold fill, a small cream grabber with a brass rim and a percentage readout. Switches (`UISwitch`) are slim pills whose knob slides right and turns the track gold; the state is also written beside them (On / Off), so colour is never the only cue.
- **Columns:** two when the panel is wide enough for two columns of 560 design px (desktop, tablets), one on phones. Only the body scrolls, under soft fades at its top and bottom edges (no scroll bar); the header and the footer never move. When Restore purchases, Privacy policy and Close do not fit on one footer line, the two text links become wrapping rows at the end of the body and only Close stays in the footer.
- **Behaviour kept:** language and text size apply live (the panel rebuilds at the new size and keeps its scroll position), every setting writes through `Settings.set_value()`, and the same panel opens from the pause menu over the 3D room.
- **QA:** `game/tests/test_layout.gd` builds the panel headless on the owner's iPhone (2556×1179, 460 dpi, notch insets), the narrowest 16:9 phone and a 10" tablet, at Normal and Extra large, in EN / RU / UZ: it must stay inside the usable rect, the footer must not overlap the body, every button and slider must be a full touch target and no label may be clipped or stick out. Previews: `docs/previews/ui/settings_before_after.jpg`, `settings_phone_{en,ru,uz}.jpg`.

## HUD (`hud.gd`, `ui_banner.gd`, `icon_button.gd`)
- **Banners** (`UIBanner`): a small-caps serif title between two gold flourishes (a diamond beside the word, a rule running outward and fading), a thin gold rule under it, a subtitle in the body font, on a soft dark band whose ends fade out, with hairlines along its edges. The view title at the top (between Back and Hint) is a title-only banner; captions and tutorial lines are subtitle-only banners under it; messages and the "Use X on…" prompt are subtitle-only banners at the bottom centre. **Item found**: the room's `Found: X` message turns into the item's icon, its name as the title and its one-line description as the subtitle, shown for 4.5 s. One-line texts hug their width; longer ones wrap at the band's maximum width, which keeps clear of the inventory column and the pause button. The caption grows downward and the message upward; when they would meet, the older one fades.
- **Inventory column:** on the left inside the safe area, under the Back button: dark rounded slots (8.5 mm) stacked beside a thin vertical gold rule with small arrow tips, vertically centred in the free span and scrolling when there are more slots than fit. The selected slot has a brass frame and a warm fill; the Inspect and Combine buttons appear beside it, right of the rule. An empty inventory shows one faint slot frame.
- **Buttons:** round bezel buttons drawn in code (a dark translucent disc, a hairline gold ring with a fainter inner ring, the icon in cream): Back top left, Hint top right (its nudge is a small gold dot), Pause bottom right with a roman-numeral **II**. Hit rects are at least 9 mm.
- **Intro:** each card's text in the display serif between two gold rules on black, TAP TO CONTINUE in small caps at the bottom.
- **Dialogs** (`UITheme.dialog()`): the hairline panel, the title over the gold rule, buttons in display small caps with a hairline frame (pressed = a soft brass fill). The pause menu fits a phone screen without scrolling at Normal.
- **QA scripts** keep working through the same names: `_message`, `_caption_line`, `_top_caption`, `_prompt` are the banners' labels, `_inv_box` is the (vertical) box of slot buttons, `_inv_panel` the column, the overlay and intro structure is unchanged.

## Reader (`hud.gd` → `_reader`, `ui_zoom_view.gd`)
Every document and inscription opens full screen: a paper plate filling the safe area above the bottom bar, the title in small caps over a hairline (with the page number at the right for the notebook), then the text in the display serif at reading size (`READ_PX` 40 design px, about 5.8 mm em on a 6.1" phone at Normal; it scrolls when longer) and/or the picture. Pictures (`UIZoomView`) zoom with a pinch, the mouse wheel or a double tap (to 2.5×) and pan with a drag; they are shown exactly as the asset is painted, in the current language where a decal has language variants (`DecalLoc`), so puzzle art reveals nothing more than the wall does.
- Chapter 1: Leyla's notebook (8 pages, the UV page keeps its glowing cipher), Strand's letter, Leyla's photograph (picture and the words on its back), the darkroom note, the evidence board (the eight photographs, a tap enlarges one, and the note), and a second tap on the poster or the chalkboard close-up.
- Chapter 2: the badge and the index cards (localized decals), the personnel file, the three tape transcripts, and a second tap on the routing chart close-up (the chart with its rule under it).
- Chapter 3: Strand's letters, his note and the growth log.
- Close is the round button in the bottom bar; the Android back button closes the reader too. A string: `ui.zoom_hint`.
