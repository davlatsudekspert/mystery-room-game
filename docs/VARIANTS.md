# Per-playthrough puzzle variants (anti-walkthrough)

**Goal.** A player who copies the numbers from a YouTube walkthrough finds that they do not work. Every new game draws its own answers from the in-world evidence; the logic of each puzzle stays the same. Watching a video can still teach *how* a puzzle works, which is fine. Copying the *answer* cannot replace playing.

**Rules.**
- **Story anchors never change.** These are 03:17, 14 November 1979, Leyla's staff number 0417, "41 staff" and the symbols ✦ ☾. They are the lore; changing them would break the story and the other chapters.
- **One seed per game.** It is drawn when a chapter starts, saved with the game, and identical after Continue. The QA solver and the tests read every answer from the logic state, never from constants.
- **Every variant is solvable and unique.** The test suite plays the solver and the no-softlock fuzz over many seeds. Data puzzles also check uniqueness by brute force, as the prism puzzle already does.
- **The evidence is rendered from the state.** Numbers on objects are drawn with Label3D, shader parameters or geometry toggles, or picked from a small set of pre-rendered decal variants. They are never baked into a single fixed image.
- **Hints follow the variant.** Level 3 speaks the player's own answer.

## Chapter 1
| Puzzle | Varies | Evidence → how it is shown | Pool |
|---|---|---|---|
| Drawer (03:17) | — | Story anchor | — |
| Gear box | Which gear wheel takes the battery | Gear tags (Label3D) | 6 |
| Safe 7294 | The 4-digit code from the poster's resonance table | Dot counts per symbol on the poster: a shader parameter or 4 decal variants | ≥ 4 |
| Radio (41 m) | The target wavelength | Chalkboard formula result (Label3D on the board) and the dial scale | 5 |
| Books II-VI-III | The volume order | The notebook's UV page (UI text from the state) | ≥ 6 |
| Shadow emblem | — | The emblem is lore | — |
| Projector rings (vial densities) | The density order | Vial labels (Label3D) | 6 |
| Mirrors | The start rotations | Geometry | 8 × 8 |

## Chapter 2
| Puzzle | Varies | Evidence → how it is shown | Pool |
|---|---|---|---|
| Catalogue 04 / 1– / 17 | — | Leyla's staff number is a story anchor | — |
| Valves 1-2-2 | The green marks on the gauges (P, F) | Gauge mark meshes rotated by code. Only targets with a unique valve solution are used | ≥ 6 |
| Punch pattern | The notches on the index card | The `hole_i` toggles exist on the request card; the index card needs the same toggles | 8–10 patterns |
| Tube destination | — | The chart rule (request card → book) | — |
| Tape clicks 2-8-5 | The click counts per reel | The click sound repeats N times; the caption dots and VU needle follow N | 9³ |
| Booth dial | Follows the clicks | — | — |
| Splice order | Which film strip carries which shadow length | The 4 strip decals are shuffled across the frames | 24 |
| Focus 5 | The sharp mark on the ring | Ring mark (geometry) and the shader's blur centre | 5 |
| Vault lock | The right rotation and zoom | The engraving is drawn by the overlay shader from parameters | 4 × 3 |

## Chapter 3 (built in from the start)
- **Choir staircase:** the 7 heights.
- **Startup:** the lever order.
- **Heart strip:** the peak counts.
- **Seed:** which drawer.
- **Autoclave:** the curve.
- **Prism:** the rims.
- **Melody:** the crystal order.
- **Rings:** the symbols on the drum.
- **Lissajous:** the target ratio.

## Order of work
1. Add the seed to `RoomLogic`, save it with the game, and make the solvers and tests read answers from the state.
2. Chapter 2:
   - tape clicks and dial;
   - splice shuffle;
   - gauge marks;
   - punch notches;
   - focus mark;
   - vault parameters.
3. Chapter 1:
   - safe;
   - books;
   - radio;
   - vials;
   - gear tag.
4. Run the real-scene playthroughs on several seeds for each chapter. Look at the evidence on screen for every variant.
