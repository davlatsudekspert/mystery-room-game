# Art Direction Guide — MYSTERY ROOM: The Forgotten Institute

## Pillars
1. **Scientific romance, not horror.** A 1950s–70s research institute built with pride: walnut, brass, enamel, glass and stone. Abandoned, but never gory.
2. **Light is the protagonist.** The Lumen concept means that every scene is composed around a few motivated light sources:
   - cold moonlight
   - one warm practical lamp
   - violet UV
   - the cyan-white "Lumen" glow
3. **Tactile mechanisms.** Every interactive object should look satisfying to touch: knurled brass knobs, chunky toggles, engraved scales, enamel labels.
4. **Dust and time.** Surfaces show wear: rubbed edges, dust on top faces, paper yellowing, verdigris in the crevices of brass.
5. **Restraint.** We avoid a cluttered "asset store" look. Each prop has a reason to be there and tells a piece of the story.

## Palette

| Token | Hex | Use |
|---|---|---|
| `ink` | `#0E0F12` | Deepest shadows, UI background |
| `shadow_teal` | `#13201F` | Shadow tint, fog colour |
| `walnut` | `#3B2416` | Primary wood |
| `mahogany` | `#5A2E1B` | Desk, door |
| `brass` | `#B08D57` | Mechanisms (aged) |
| `brass_hi` | `#E3C27A` | Brass highlights, UI accent hover |
| `verdigris` | `#4E7F6E` | Patina, success state |
| `enamel_cream` | `#E8DFC8` | Labels, dials |
| `paper` | `#D9CBB0` | Notebook, posters |
| `ink_brown` | `#2B2118` | Handwriting |
| `lamp_warm` | `#FFB46B` | Practical lights, about 2700 K |
| `moon_cold` | `#7FA7D9` | Window key light |
| `uv_violet` | `#7B4DFF` | UV beam |
| `uv_ink` | `#9CFFD8` | Fluorescent ink |
| `lumen` | `#CFF6FF` | Array and crystal glow |
| `danger` | `#B5523B` | Maglock lamp, error |

**Value structure:** 70% of the frame sits in dark values (`ink` to `walnut`). The midtones are wood and brass. Highlights are reserved for interactable brass edges, paper and light sources, so the eye naturally finds clues.

## Lighting recipe (mobile-safe)
- **Before power is restored:**
  - Moonlight is a DirectionalLight with soft shadows through the window bars.
  - One flickering OmniLight in the desk lamp.
  - A red maglock lamp.
  - Fog uses `shadow_teal` at low density.
- **After power is restored:**
  - Two warm ceiling pendants come on.
  - The panel lamps glow.
  - The projector emits `lumen`.
  - Tween the exposure from 0.8 to 1.0 over 2 seconds.
- **ReflectionProbe:** one, low update, so brass picks up the room.
- **Environment:**
  - ACES/AgX tonemap
  - subtle glow on emissives only
  - slight vignette and grain in the UI layer
  - no SSAO, SSR or volumetrics (unsupported on Mobile and Compatibility renderers)
- **Fake AO:** baked into textures and vertex colour where helpful. Contact shadows come from real shadow-casting lights, at most 2 casting lights at once.

## Materials
Most materials are PBR built from **CC0 scanned textures** (ambientCG, Poly Haven) at 1K. A few are procedural from `tools/textures/`. All materials live in `game/assets/materials/*.tres` and are assigned by Blender material slot name.

| Slot name | Look |
|---|---|
| `M_Wood_Walnut` | Dark walnut, semi-gloss, roughness 0.45 |
| `M_Wood_Floor` | Worn parquet or planks, dusty, roughness 0.6 |
| `M_Brass_Aged` | Metallic 1, roughness 0.35, brown-gold albedo, darker crevices |
| `M_Steel_Painted` | Green-grey enamel (safe, panel), chipped edges |
| `M_Plaster_Wall` | Off-white aged plaster, upper walls |
| `M_Wood_Panel` | Wainscoting, lower walls |
| `M_Stone` | Window sill, floor trim |
| `M_Glass` | Vials and lamp glass, transparent, high gloss |
| `M_Leather` | Notebook cover, chair |
| `M_Paper` | Documents, with emission 0 |
| `M_Enamel_Cream` | Dials and labels |
| `M_Emissive_*` | Lamps, indicators, Lumen glow |

## Modelling rules (Blender)
- Bevel **every** hard edge, using 2 segments for hero props and 1 for background props. Bevels are what make procedural props look premium instead of looking like primitives.
- Scale is 1 unit = 1 m. The room is about 6 × 5 m, with a ceiling height of 3.4 m.
- Triangle budget:
  - hero props ≤ 6k tris
  - background props ≤ 2k
  - room shell ≤ 10k
  - whole scene ≤ 150k
- Textures are 1K, with 2K only for the floor and walls. Use ETC2/ASTC compression (Godot VRAM compressed).
- Interactive parts are separate objects, named `IA_<id>` (for example `IA_drawer_wheel_0`), so Godot can attach behaviour to them.
- Pivots sit where things rotate: hinges, wheel axles, lever bases.

## UI style
- **Fonts:**
  - Display: *Cormorant Garamond* (SemiBold/Bold), engraved-plaque feel
  - UI and body: *Noto Sans*, highly legible, with full Cyrillic and Uzbek ʻ ʼ support
  - Handwriting (notebook): *Caveat*, with Noto Sans fallback
- **Panels:**
  - `ink` at 88% opacity
  - 1 px `brass` hairline border
  - 10 px corner radius
  - soft drop shadow
- **Buttons:**
  - minimum touch target 56 × 56 dp
  - brass outline
  - fills `brass` on press
  - text and icons in `enamel_cream`
- **Motion:** 180–250 ms ease-out for UI, and 500–700 ms cubic ease-in-out for the camera. Never bounce.
- **Icons:** simple line icons in the brass hairline style (hint lamp, gear, back arrow, bag).

## Logo
"MYSTERY ROOM" in Cormorant Garamond Bold with wide tracking, above a thin brass rule and the subtitle "THE FORGOTTEN INSTITUTE" in small caps. Behind it sits a circular "lens" emblem: a crystal ring with a single meridian line.

## What to avoid
- Pure black (#000) or pure white (#FFF) surfaces
- Saturated primary colours, except in the deliberate vial and ring colours
- Cartoon proportions
- Untextured primitives
- Glossy plastic on brass
