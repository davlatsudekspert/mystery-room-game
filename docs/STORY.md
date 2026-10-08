# MYSTERY ROOM — The Forgotten Institute
## Story Bible (original work)

> All names, places, events and the "Lumen" concept are original to this project.

### Premise (one line)
A sealed Soviet-era-styled research institute in a mountain valley went silent on a single November night in 1979. Decades later you unlock its doors and discover that its scientists never left — they were *kept*.

### Setting
**The Meridian Institute of Resonant Physics** (RU: Институт резонансной физики «Меридиан»; UZ: «Meridian» rezonans fizikasi instituti).
Founded 1958 in a remote valley. Brick-and-stone halls, walnut-panelled laboratories, brass instruments, humming transformer rooms. Officially closed on **14 November 1979** after a "ventilation accident". Every record was sealed. Every clock in the building stopped at **03:17**.

### Core mystery concept — the Lumen Array
Director **Professor Emil Strand** believed light passing through a perfectly grown crystal leaves an imprint — a *light memory* — that can be replayed. His great machine, the **Lumen Array**, could replay a few seconds of the past as a ghostly projection.
What Strand hid: at full resonance the Array does not just replay light. It **keeps** it — and anything standing in its beam.

### Characters (discovered, never "talked to")
| Character | Role | How the player meets them |
|---|---|---|
| **Prof. Emil Strand** | Founder, director, dying of illness, desperate to "preserve" his colleagues | Letters, chalkboard, his gear-box gifts, the Array itself |
| **Dr. Leyla Rahimova** | Senior researcher, Laboratory 7. The only one who understood the danger. She escaped the Night of Silence because Lab 7 was shielded | Her notebook, UV ink, hidden compartments — she hid the Array's key parts and left a trail only a careful person could follow |
| **The Visitor (player)** | Unnamed. Receives Leyla's old lab badge in a parcel with one line: *"Laboratory 7. Please finish what I could not."* | You |

### Tone
Quiet, curious, melancholic, never gory. Wonder first, dread second. The story is told through objects, handwriting, light and sound — minimal text, no dialogue trees.

### Chapter structure (data-driven; more chapters can be appended in `game/src/core/chapters.gd`)
| # | Chapter | Location | Story beat | Access |
|---|---|---|---|---|
| 1 | **The Locked Laboratory** | Laboratory 7 + Leyla's hidden darkroom | You are locked in Lab 7. You learn about the Night of Silence, restore power, follow Strand's beacon to Leyla's darkroom, and wake the Array for a moment. A light-echo of Leyla appears, and **looks at you** | **Free** |
| 2 | The Missing Scientist | Records archive + Leyla's apartment wing | Where did Leyla go after 1979? Her letters stop in 1998. The parcel you received was postmarked **14 November 1979** | Premium (planned) |
| 3 | The Underground Facility | Transformer halls, crystal-growth vaults | The Array's true scale. The 41 staff silhouettes in the light. Strand's illness | Premium (planned) |
| 4 | The Experiment | The Array Hall | Re-run the Night of Silence in reverse. The ending depends on choices from Chapters 1–3 (lens, shards, who you trusted) | Premium (planned) |

### Fair twists (foreshadowed)
1. **The parcel** that brought you here carries a 1979 postmark. It appears on the intro card and is mentioned in the Chapter 1 epilogue. Leyla could not have sent it in the present day. Someone, or something, inside the light did.
2. **The echo is not a recording.** Recorded light cannot react. Leyla's echo turns toward the player, which proves the Array keeps people, not just images. This is foreshadowed by notebook p.1: "It is not replaying the light. It is keeping it."
3. **Strand was not a villain.** His letters show he tried to save his dying colleagues, and himself. This is revealed gradually across the chapters.

### Player choices that carry forward
| Choice | Recorded as | Consequences |
|---|---|---|
| Ch1 finale: **take** the crystal lens / **leave** it in the projector | `choices.ch1_lens` | Chapter 2 opening differs: the lens can sense echoes, or Leyla's echo guides you once |
| Ch1 optional: all **5 Lumen shards** found | `choices.ch1_shards = 5` | Secret epilogue line; contributes to the "true ending" in Chapter 4 |

### Chapter 1 — "The Locked Laboratory" (detailed)
**Opening (≤ 20 seconds, skippable):** black screen, sound of rain and a heavy key. Text card: *"Meridian Institute. Sealed since 14 November 1979."* The door of Lab 7 swings open; you step in; the door slams; a maglock clicks; a red lamp glows. Only the moon and a flickering desk lamp light the room.

**Environmental storytelling in the room**
- A stopped **flip clock** on the desk: 03:17.
- A chalkboard with Strand's handwriting: half-erased equations and the words *"light remembers"*.
- A poster: **Strand's Table of Resonances** — ten symbols, each with a number of dots.
- Three sample **vials** on the lab bench, labelled only with densities.
- The **Lumen Projector** — a small brass sibling of the great Array — aimed at the door.
- A coat still on the hook. A cup of tea, dried to a ring. A child's drawing pinned near the desk (Leyla's daughter).

**Leyla's notebook (key text, kept short)**
1. *12 Nov 1979.* "Strand wants full resonance on Thursday. The crystal readings are wrong. It is not replaying the light. It is keeping it."
2. *14 Nov 1979.* "Every clock in the building stopped at the same moment. I set the lock of my desk drawer to that moment so that I will never forget it."
3. "Strand gave each of us one of his gear boxes. 'Turn one wheel and its neighbour follows — like people,' he said. I keep the cell for my lamp inside mine."
4. "Panel 7: LOCK, LIGHT and ARRAY must be live. The VENT line must stay dead — or the dust from the Array Hall will reach us."
5. *(blank — UV ink)* "The safe answers in Strand's symbols:" + four symbols.
6. "I took the handle of the main breaker and hid it where only my lamp can show the way."
7. "If someone reads this: the Array must wake once more to open the door. Tune it exactly as Strand wrote — or it will keep you too."
8. "Strand's beacon still calls on his old band, three numbers over and over. My encyclopedia remembers them."
9. *(darkroom note)* "The Institute's mark — only light and shadow may draw it."

**Strand's letter (found in the safe):** "Leyla — the light opens any door when the three rings sing with the three samples, the heaviest first. Do not be afraid of it. — E.S."

**Mid-chapter reveal:** Strand's beacon still broadcasts on the 41 m band. Its pulses open Leyla's hidden darkroom behind the bookcase. Inside are her evidence wall (photos of the 41 staff, newspaper clippings about the "ventilation accident") and the shadow lock that protects Strand's mirror.

**Ending of Chapter 1:**
1. The tuned Lumen beam, guided by the two mirrors, strikes the door's photocell. The maglock releases and the door swings open.
2. For three seconds a translucent figure of light sits at the desk, writing. It is Leyla, 1979. Then she **turns to look at the player**.
3. Choice: *Take the crystal lens* / *Leave it for her*.
4. Text card: *"The Array is listening again."*
5. Chapter complete. The epilogue line varies with the choice and with the shards found.

### Ending of the full game (for future chapters)
Strand, dying, tried to "save" his colleagues by recording them into the great crystal on the Night of Silence. Leyla spent her life hiding the Array's parts so nobody would wake it carelessly — and looking for a way to undo it. The Visitor completes her work: the Array is tuned *in reverse*, the 41 echoes leave the crystal as light, and the Institute is no longer forgotten.

### Localization notes
- Names stay the same in all languages (Leyla Rahimova / Лейла Рахимова / Leyla Rahimova).
- All puzzle-critical information is **language-neutral**: digits, symbols, colours, dot counts, density numbers. Translations never change a solution.
