# Engagement review: Chapters 1 and 2

**Date:** 2026-10-10. **Why now:** Chapters 1 and 2 are free, and the US$4.99 purchase unlocks Chapters 3 and 4. The end of Chapter 2 is where a player decides to buy. The owner's brief: the first two chapters must pull the player in, and their ending must leave the player wanting more.

**Method.** I played both chapters the way a first-time fan of *The Room* would. My sources:
- the rendered solver playthroughs (`qa/playthrough.tscn` with seed 4242, `qa/playthrough_ch2.tscn` with seed 777 on the leave path) and their screenshots, both from before and after this pass;
- the design documents (`docs/STORY.md`, `docs/PUZZLE_DESIGN.md`, `docs/CHAPTER2_DESIGN.md`);
- the code: every caption, message, sound and camera move that a solved step triggers.

**What this review is not.** Minutes are a first-time-player **estimate**. They come from the puzzle count and the length of the documents and cinematics; the solver's own times (about 3 and 4 minutes) tell us nothing about humans. No one has played either chapter on a phone yet (`docs/GAMEPLAY_QA.md`). Treat the curves as hypotheses for the first playtest to confirm or break.

**Scale.** Curiosity is rated 1–5:
- 1: nothing new; the player is doing chores.
- 3: something to work out.
- 5: "I have to see what happens next".

The type column uses these labels:
- **hook**: a question is planted;
- **aha**: a deduction lands;
- **reveal**: something hidden opens;
- **wow**: a set piece;
- **dead**: more than 2–3 minutes with nothing new seen or learned.

---

## Chapter 1: The Locked Laboratory

Estimated length: 35–60 minutes. The table uses the middle of that range.

| Min | What the player sees and does | Curiosity | Type |
|---|---|---|---|
| 0–1 | Rain, a key, *"Sealed since 14 November 1979"*. The parcel line: *"Please finish what I could not"*. The door slams, the maglock clicks, a red lamp | 5 | hook |
| 1–4 | Dark lab by moonlight. The notebook, p.1: *"It is not replaying the light. It is keeping it."* The clock stopped at 03:17, the poster, the chalkboard, the coat, the cold tea | 4 | hook |
| 4–6 | **P1 drawer 0317.** The clock and notebook p.2 give the code. The drawer slides open on a UV lamp with no battery | 4 | aha |
| 6–9 | **P2 gear box** (each knob turns two gears) gives the battery cell. **P3** puts the cell in the lamp | 3 | — |
| 9–11 | The UV lamp on the blank page: *"Hidden ink blooms"*. Four of Strand's symbols. A glowing mark appears on the side of the desk | 5 | reveal |
| 11–15 | The symbols read through the poster's dot counts open **P4, the safe**. Four things come out at once: the brass key, the crystal lens, Strand's sealed letter and a radio valve | 4 | aha |
| 15–18 | **P5 desk compartment** (rosette, keyhole, key) holds the breaker handle and Leyla's photograph *"For Mira"* | 3 | reveal (small) |
| 18–23 | **P6 Panel 7** (logic; another agent's area) restores power. The pendants stutter on, the transformer hums, red light seeps around the bookcase | 5 | wow |
| 23–27 | The valve goes in, **P7–P8** tune to 41 m, the beacon's pulses cut through the static, and every lamp in the lab stutters: *the Array answers* | 5 | wow |
| 27–29 | **P9 encyclopedia**: the bookcase swings | 4 → **5** | reveal |
| 29–34 | The darkroom: the evidence wall (41 photographs, the 1979 and 1998 clippings) and **P10 shadow lock**. The cabinet opens; the emblem is recorded in the crystal | 4 | aha |
| 34–37 | **P11 projector**: Strand's letter and the vial densities tune the rings. A clean Lumen beam | 4 | wow |
| 37–42 | **P12 mirrors**: two stands, eight clicks each, the beam traced live | 3 | **dead risk** |
| 42–44 | The door's eye blazes and the room flashes back to 1979. Leyla's echo at the desk turns to look at you. Take or leave the lens | 5 | wow + twist |
| 44 | The door opens… **onto a flat fog-coloured slab** (before this pass); the chapter card | 2 → **4** | — |

Optional throughout: five Lumen shards under UV.

### Where Chapter 1 sags
1. **The bookcase opening (min 27), the chapter's midpoint reveal, was told rather than shown.** It had a message line and a door sound, and the camera stepped back. No light came from the hidden room and nothing happened in the air. *Fixed.*
2. **The final image was empty.** The door opened onto the fog colour (`docs/previews/playthrough/` frame 34): the player's reward for 40 minutes was a blank rectangle, and nothing pointed on to Chapter 2. *Fixed.*
3. **The epilogue contradicted the next chapter.** *"On the train home you look at the parcel again"* is followed at once by Chapter 2: *"Beyond Laboratory 7, a corridor leads to Records Archive B."* Now that both chapters are free and are played back to back, this is the seam players cross. *Fixed.*
4. **Continue after the ending stranded the player.** Quit on the chapter card, choose Continue, and the game loaded a finished Lab 7: door open, nothing to tap, no card, no way to Chapter 2 except Pause, Main menu, Chapters. Shown by `qa/transition_check.tscn` on the code before this pass: `✗ a finished Lab 7 opens on the chapter card (not an empty room)`. *Fixed.*
5. **The mirror stretch (min 37–42) risks being trial and error.** Each click turns a mirror 45°, and only one of eight positions is right per stand. The live beam is good feedback, but nothing new is seen while the player clicks. *Not changed:* the puzzle is fair as designed, and the hint H16 says which way to aim. If testers stall here, the cheapest lever is a soft tick when the beam reaches the second stand (`beam_path` event).
6. **The gear box (min 6–9) is the one puzzle with no story payload.** It is short and teaches the "neighbour follows" idea. *Not changed.*
7. **The evidence wall carries the 1998 clipping that sets up Chapter 2,** but reading it is optional (a document). *Not changed:* Chapter 2's intro restates the premise. A playtest should ask whether testers can say why they are going to the archive.
8. **Panel 7 and the first three minutes** belong to other agents (Panel 7 variants; the menu, intro and first-run prompts). They are rated here for the curve only.

---

## Chapter 2: The Missing Scientist

Estimated length: 30–40 minutes. Free since 2026-10-10.

| Min | What the player sees and does | Curiosity | Type |
|---|---|---|---|
| 0–1 | The fire shutter crashes down; emergency lamps flicker aisle by aisle. *"Her file must be somewhere in this archive"* | 5 | hook |
| 1–4 | The hall, the vault door with its glass disc, the screen, the booth. The aisle sign leads to the **P1 card catalogue**: badge 0417 → drawer 04, divider 1–, card 17 | 4 | aha |
| 4–7 | **P2 compressor**: two gauges, three valves, a piping plate. It wheezes to life | 3 | aha (small) |
| 7–9 | **P3 punch**: copy eight notches. **P4 tube**: the chart says the book. The canister **shoots across the ceiling** and thumps back heavier, with Leyla's 1998 letter and the key to locker 9 | 3 → 5 | wow |
| 9–14 | **P5 locker 9** gives the receiver. **P6 hunt** by needle and beeps: the grille swings, the ledger is hollow, the hatch lifts | 4 | reveal ×3 |
| 14–18 | **P7 tape deck at 4.75**: Leyla's voice diary, 1996–98 (*"Forty-one names. Strand did not lose them. He kept them."*). Clicks 2, 8, 5 | 5 | story peak |
| 18–20 | **P8 rotary dial** opens the booth | 4 | aha |
| 20–25 | **P9 splice by shadow** (dawn → noon). **P10**: the hall dims and **a 1979 film plays on the big screen**: 41 people, then Leyla draws her sign. With 5/5 shards, Strand's secret reel follows. On the leave path, Leyla's echo walks to the slide cabinet | 5 | wow |
| 25–31 | **P11** records the sign at the screen socket. On the leave path, **P11b**: drawer, slide, gate, rotate, film lamp off, second crystal | 3 → 2 | **dead risk** |
| 31–34 | **P12 dual light lock**: two crystals, two collars, the zoom → the bolts cascade, three turns of the wheel, the 1.9 m door swings | 5 | wow |
| 34–36 | The vault reel: 41 silhouettes and **a 42nd at the edge: Leyla, 1998** | 4 → **5** | twist |
| 36 | Two keys. Choose | 4 | choice |
| 36+ | *Before:* the chapter card at once (*"To be continued…"*, Main Menu). *Now:* the cliffhanger (below) | 2 → **5** | — |

### Where Chapter 2 sags
1. **The purchase moment was a statistics card.** Straight after the key choice came time, puzzles, hints and *"To be continued…"* (`docs/previews/ch2/39_chapter_complete.jpg`). Nothing new was seen and no question was left open beyond one epilogue line. This is the screen where the player decides to pay. *Fixed: the cliffhanger.*
2. **The chapter's twist was a caption over a small screen.** The 42nd silhouette, Leyla in 1998, stands at the edge of a frame that filled about a quarter of the vault view, and a 7.5 s caption read over it (`docs/previews/ch2/36_vault_opening.jpg`). Nothing in light, sound or camera said "look here". *Fixed.*
3. **After a crystal is recorded, nothing points to the vault (min 25–31).** The flash and *"It keeps her sign now"* close the step, but the next goal is across the hall. On the leave path the player then does six more device operations with no story beat. This is the chapter's longest stretch of busywork. *Fixed in part:* the vault now answers each recording. P11b itself is unchanged.
4. **Wrong tries in P11 were silent.** A blank crystal seated while the picture is blurred, the screen dark, the wrong frame showing, or the film and slide lamps both on just sat there. The player could not tell "wrong idea" from "this does nothing". P11b's hidden rule (the film lamp must be off) was also never said out loud. *Fixed:* each case now says why the crystal stays clear, without giving the answer.
5. **The P3 punch is copying.** Eight keys from the index card. It is short, and the canister flight that follows is the reward. *Not changed.*
6. **Nothing rewarded curiosity outside the main path, apart from the echoes.** *Fixed: one secret added* (below).
7. **Continue after the ending stranded the player here too:** a finished Archive with nothing to tap. *Fixed:* it opens on the Chapter 3 card.

---

## What changed (this pass)

### Chapter 2: the cliffhanger at the purchase moment
`game/src/rooms/archive/archive_teaser.gd` (new), `archive_room.gd`, `archive_visuals.gd`. Every line is in EN, RU and UZ (`tools/localization/strings_ch2.py`).

1. **The reel, staged (about 11 s).**
   - The camera comes close to Leyla's pull-down screen. Caption: *"The Array Hall, 1979. Forty-one silhouettes in the light."*
   - Then the sting: a low reveal tone, the projector charging and a haptic pulse. The frame dims around the figure at its right edge and a cold halo grows around her (`vault_reel.gdshader`). The camera leans in toward her: *"And a forty-second, at the edge of the frame. Leyla, 1998."*
   - The camera then settles on the key cradle and the choice opens.
2. **The key comes off its hook** toward the player, with the key-lift sound; the clamp drops on the other key.
3. **The floor answers.** A lift motor wakes under the vault: the view shakes, the caged bulb stutters, dust falls from the ceiling. Caption: *"[Under the floor, something old and heavy wakes: a lift motor]"*.
4. **A glimpse down the freight-lift shaft** (STORY.md: the vault key opens the old freight lift to Level −2).
   - We cut to the landing sill and look down 30 m of concrete shaft. Its eight caged lamps wake one storey at a time, each with a relay click.
   - The cage rises from the dark with its work lamp. At the bottom, the cold light of Level −2 breathes, and the ambience becomes the transformer hum.
   - Captions: *"[Floor by floor, the lamps of the lift shaft wake]"*, *"[Far below: the hum of the transformer halls]"*.
   - The shaft is built from primitives and the shared materials (about 30 draw calls) only for this shot, and is freed afterwards.
5. **The recorder, on black.**
   - *"Somewhere below, a recorder clicks on."* (the canonical epilogue line), with a deck click and tape hiss.
   - Then Leyla's 1998 voice, captioned line by line. The words are taken from Chapter 3's recorder text (`doc3.recorder`), so the teaser and Chapter 3 agree: *"If you hear this, the lift still works." "The Choir and the Nursery must sing together, or the Array stays deaf." "I am going down to them."*
   - Then, **the bigger mystery:** *"[Under the hiss, a second voice. An old man's. Very close.]"* and *"Leyla?… Who is that with you?"* That is Strand, kept in the light, noticing someone. It is consistent with STORY.md's twist 2 (the Array keeps people, and they react) and with Chapter 3's finale, where Strand and Leyla wait in the light.
6. **The Chapter 3 card.** It shows *Chapter 3 · The Underground Facility*, a rule, and one line for the wing the chosen key opens:
   - Strand's key: the Choir Hall, the transformers, the singing tubes and the office where he kept his last secret;
   - Leyla's key: the Nursery, the crystal vaults, her last camp, and a recorder that is still turning.

   Then one calm hand-off, chosen by `ArchiveTeaser.card_state()`:

   | State | When | The card shows |
   |---|---|---|
   | `unlock` | Chapter 3 is released, not owned, and the store is open | *"Chapters 3 and 4 finish the story. One purchase unlocks both; no ads, ever."*, then **Continue the story**, which opens the store agent's `PurchasePanel.open()`, and a quiet **Not now** text button. If the purchase succeeds, the card closes by itself and the chapter card that follows offers Play |
   | `soon` | Chapter 3 is not released yet, or there is no store (`REAL_PAYMENTS_ENABLED = false` in a release build) | *"Chapters 3 and 4 are on their way. Your key and your choices are saved for them."* and **Continue** |
   | `play` | Chapter 3 is owned, or this is a tester build | **Continue** |

   **Continue** or **Not now** leads to the HUD's usual chapter card (time, puzzles, echoes, Chapter 3, Main menu). The card never times out and never pops anything up on its own. Back is swallowed, as on the finale choice. `purchase_panel.gd` is not touched.
7. **Skippable.** A tap shortens each beat of the shaft and the recorder (about 45 s in all, unskipped). The card always waits for the player.
8. **A finished save opens on the card.** Continue after the chapter ended shows the vault and the Chapter 3 card again.

### Chapter 2: clarity, rewards and a secret
- **The vault answers a recording.** About a second after a crystal records the sign (or Strand's mark), a far clunk sounds across the hall, the matching port's light pipe on the vault door flares, and a caption reads: *"[Across the hall, the vault door answers with a dull clunk]"*. The next goal announces itself, and the step gets a second payoff. This happens once per image.
- **Why the crystal stays clear.** A blank crystal that records nothing now says why: the screen is dark, the picture is blurred, two images overlap, or it waits for one sharp image alone on the screen. The slide lamp switched on over the running film says the two lights cross on the screen. These turn P11 and P11b's hidden rules into feedback without giving the answer.
- **Secret: "Forty-Two".** Once all three reels are found, select Leyla's receiver at the shut vault door. The needle twitches one last time and, under the static, a far voice counts *"…forty… forty-one… forty-two"*. This foreshadows the reel's twist before it is seen. It unlocks the achievement `forty_two` and touches no puzzle.

### Chapter 1
`game/src/rooms/lab7/lab7_room.gd` (new functions at the end of the file, plus three call sites: one line in `_ready`, one in `shelf_opened` and one in `_play_ending`), `lab7_logic.gd` (`epilogue_keys` only), `tools/localization/strings_ch1.py`.
- **The bookcase reveal is shown.** As the case swings:
  - the darkroom's red safelight flares through the gap (0.7 → 2.6 → back);
  - a breath of dust rolls out into the lab;
  - a low tone sounds and a caption reads: *"[A cold draught breathes out from behind the shelves]"*.
- **Beyond the door, a corridor.** The door now opens onto a 9 m institute corridor: linoleum, green dado, plaster and three enamel pendants. At its far end are double doors under a lit enamel sign, **RECORDS ARCHIVE B** (it translates with the language), and an amber emergency lamp. As the door swings, the lamps flicker on one by one toward the sign: *"[Beyond the door, the corridor lamps wake one by one]"*. The chapter card now sits over a lit corridor that leads to Chapter 2. It is built only when the door opens.
- **The epilogue agrees with Chapter 2:** *"Under the corridor lamp you unfold the parcel's wrapper again. The postmark reads: 14 XI 1979."* This is the new key `epi1.postmark`; the old `epi.postmark` stays in `strings_core.py`, unused, because that file is shared.
- **A finished save opens on the chapter card,** with its Play button for Chapter 2, over the open door and the lit corridor.

### Not changed, on purpose
- **Puzzle answers and difficulty are unchanged.** No logic rule changed. Every variant (docs/VARIANTS.md) still comes from the seed; the new messages describe the state and never speak an answer.
- **Other agents' areas** were not touched: the intro and first-run prompts, Panel 7, the HUD (`game/src/ui/*`), `purchase_panel.gd`, `chapters.gd` and `premium.gd`.

---

## Verification

<!-- filled in from the runs below -->

---

## For the owner's judgment
1. **Strand's line on the tape** (*"Leyla?… Who is that with you?"*) is new canon. It fits STORY.md and Chapter 3's finale, but it commits the story to Strand being aware inside the light. Keep it, or end the tape on Leyla's *"I am going down to them"*?
2. **The voice is a murmur.** The tape uses the existing synthesized murmur (`tape_voice`) with captions, as Chapter 2's diary does. A recorded Leyla (and Strand) in EN, RU and UZ would lift the cliffhanger more than any visual change. That needs a voice actor or a licensed TTS.
3. **The hand-off wording.** *"Continue the story"* and *"Not now"* on the card, and the line *"One purchase unlocks both; no ads, ever."* (true per `docs/MONETIZATION.md`). Should the price appear on the card itself, or only in the purchase screen, as now?
4. **Length of the cliffhanger.** About 45 s unskipped, plus 11 s for the reel. A tap shortens every beat; first-time players should probably see it whole.
5. **Playtest questions.** Do players find the whisper secret? Do they look at the vault after the clunk? Do they stall on the mirrors? Can they say why they go to the archive?
