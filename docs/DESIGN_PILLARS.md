# Design Pillars, Competitive Analysis & Signature Mechanics

## 1. What the best games in the genre do well, and where they fall short
This is analysis of design qualities only. We copy no story, puzzle, art, audio or IP.

| Game (genre reference) | Strengths to learn from | Weaknesses we can beat |
|---|---|---|
| **The Room** series | Tactile close-up mechanisms, superb sound and haptics, nested boxes and "one more layer" reveals, camera feels physical | Story is thin and vague. Puzzles are often "find the hidden latch". Little player agency. The special lens reveals hidden objects in the present |
| **Rusty Lake / Cube Escape** | Strong surreal narrative across many small games, memorable characters, cross-game lore, short sessions, WOW twists | 2D point-and-click. Logic sometimes leaps ("moon logic"). Low production fidelity limits immersion |
| **The House of Da Vinci** | 3D Renaissance mechanisms, clear goals, a device that shows **past events** | Pacing is uneven. Hint fatigue. The past-vision device is the central gimmick, **so we deliberately avoid a "look into the past" lens** |
| **Generic mobile escape rooms** | Low friction, quick wins | Asset-store look, random codes, unfair hidden pixels, ads and energy walls |

**Our quality bar:**
- tactile 3D mechanisms on the level of The Room
- a narrative pull on the level of Rusty Lake
- clearer fairness than both: every answer comes from evidence, with a three-level hint ladder
- a premium, ad-free business model

## 2. Signature mechanics (original to MYSTERY ROOM)
Each mechanic grows out of the fiction (the **Lumen**: light remembers) and scales across chapters.

| # | Mechanic | What the player does | Ch1 implementation | Fun | Original | Mobile UX | Feasible | Perf | Extensible |
|---|---|---|---|---|---|---|---|---|---|
| **M1** | **Light Memory (record → replay)** | A Lumen crystal **records the light pattern that falls on it**, such as a shadow, a glyph or a coloured flash. The projector later **replays** it elsewhere as a *light key* | In the darkroom, form the Institute emblem with the shadow sculpture, with the crystal seated in the emblem socket, to record it. Then project the recorded emblem onto the door's ground-glass light lock | ★★★★★ | ★★★★★ | ★★★★ | ★★★★ | ★★★★ | ★★★★★ |
| **M2** | **Live Lumen beam engineering** | Tune the beam's spectrum by deduction (colour rings), then route it live in 3D with mirrors. The beam **carries** the recorded image | Rings follow "heaviest first" (vial densities). Two mirrors, one recovered from the darkroom, guide the emblem across the lab to the door | ★★★★ | ★★★★ | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ (prisms, filters, splitters, timed light in Ch3–4) |
| **M3** | **Instrument layers: one room, several hidden layers** | Leyla's toolkit reveals different hidden layers of the *same* room. The player learns to scan the room with different senses | **UV** shows ink, the **radio** finds Strand's beacon (audio and magic eye), **circuits** distribute power, and **Lumen** carries memory | ★★★★ | ★★★ (the combination is new) | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ (Ch2 portable receiver, Ch3 Geiger/resonance meter) |
| **M4** | **Consequences across rooms and chapters** | Actions in one space change another, and choices persist | Restoring the ARRAY line makes a **red darkroom glow leak around the bookcase**, a diegetic hint to the secret room. The finale choice (take or leave the lens) and the 5 Lumen shards are saved for Chapter 2 and later endings | ★★★★ | ★★★★ | ★★★★★ | ★★★★★ | ★★★★★ | ★★★★★ |

**Rejected ideas:**
- A handheld "past-vision lens" was rejected because it is too close to existing games.
- Timed or real-time pressure puzzles were rejected because they are hostile on mobile.
- Pixel-hunt collectibles without a tool were rejected because they are unfair. The shards are visible under UV, which is a skill players already have.

## 3. WOW moments in Chapter 1, roughly every 3–5 minutes
| Minute (approx.) | Moment | Built with |
|---|---|---|
| 0:00 | The door slams, the maglock clicks red, and you are alone in moonlight with dust in the beam | Camera shake, sound, volumetric-looking light cards |
| 3–5 | First UV sweep: invisible handwriting blooms on the "blank" page | UV reveal shader, shimmer sound |
| 8–10 | **Power returns**: relays clack one by one, lamps warm up, the projector starts humming, and a **red glow appears around the bookcase edges** | Light tweening, emissive lamps, sound sequence |
| 12–14 | The radio's static resolves into Strand's beacon, and the magic-eye glows green with each pulse | Audio crossfade by dial distance |
| 15–17 | **The bookcase swings open** into a hidden red-lit darkroom with 41 staff photographs on Leyla's evidence wall | Animated hinge, red safelight, reveal camera |
| 18–21 | Real-time shadow: turning the brass sculpture until its shadow becomes the Institute emblem. The crystal flares as it **records** it | Real shadow-casting spot light, crystal glow |
| 24–28 | The **Lumen beam** fires. You steer it with mirrors and it paints the emblem onto the door, which opens. For three seconds **the whole lab flashes back to 1979**: warm light, Leyla writing at the desk. **She turns her head toward you.** | Beam meshes, projector texture, environment swap, echo figure |
| End | Choice: take or leave the lens. The epilogue card reveals that **your parcel was postmarked 14 Nov 1979** | Narrative UI |

## 4. Pacing & difficulty curve (Chapter 1)
Difficulty runs from 1 (trivial) to 5 (hard). Mechanics are introduced one per beat: observation, then mechanism, then combine, then hidden layer, then deduction, then signals, then space, then light.

| Act | Puzzles | Difficulty |
|---|---|---|
| Act A — Darkness | Drawer, gear box, lamp | 1–2 |
| Act B — Hidden ink | Cipher and safe, desk compartment | 2–3 |
| Act C — Power and signals | Circuits, radio repair, tuning | 3 |
| Act D — Secrets | Encyclopedia door, shadow lock and recording | 3–4 |
| Act E — Light | Projector tuning, mirror path, finale | 4 |

## 5. Hooks into later chapters
- **Ch2 "The Missing Scientist":** the evidence wall shows Leyla came back long after 1979 (newspaper dates from 1998). Who sent the 1979-postmarked parcel?
- **Ch3 "The Underground Facility":** Strand's beacon source is triangulated below the Institute.
- **Ch4 "The Experiment":** running the Array in reverse. The ending is determined by lens, shards and the choices made in Ch2–3.
