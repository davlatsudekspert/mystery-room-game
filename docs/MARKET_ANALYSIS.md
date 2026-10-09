# Market Analysis — MYSTERY ROOM: The Forgotten Institute

_Research date: 2026-10-09. Companion to [`BUSINESS_STRATEGY.md`](BUSINESS_STRATEGY.md), which holds the comparable premium titles, store fees, taxes, payouts, the launch plan and the payment checklist. This document goes deeper on the mass-market escape games, compares five revenue models, and turns the findings into product actions._

## Qisqacha mazmun (oʻzbekcha)
- **Raqobatchilar:**
  - **Bepul, reklamali oʻyinlar:** Adventure Escape Mysteries, Escape game: 50 rooms, 100 Doors. Ularning yuklab olishlari koʻp (Google Play-da 5M+ dan 10M+ gacha), lekin reklama, vaqt cheklovi, pullik maslahat va “taxmin qilinadigan kodlar” haqida shikoyatlar koʻp.
  - **Premium oʻyinlar:** The Room, Rusty Lake. Ularning bahosi yuqori, lekin oʻyin qisqa, The Room esa App Store-da faqat ingliz tilida.
- **Bizning hisob:** reklamasiz premium oʻyinlarning Google Play-dagi oʻrtacha bahosi **4.76**, reklamali bepul oʻyinlarniki **4.54**. Bu bogʻliqlik, sabab emas.
- **Daromad modellari:** 10k, 100k va 1M yuklab olish uchun beshta model solishtirildi. Barcha kiritilgan qiymatlar alohida koʻrsatilgan. Reklama narxi (eCPM) Oʻzbekiston va MDH uchun ishonchli manbada topilmadi, shuning uchun u taxmin.
- **Tavsiya:** **1-bob bepul + 2–4-boblar bitta xarid ($4.99), reklamasiz.** Bu oʻyin atmosferasiga, doʻkondagi “reklama yoʻq” vaʼdasiga va maxfiylik siyosatiga mos keladi. Hech narsa yoqilmaydi: egasi qaror qilmaguncha reklama SDK ham, toʻlov ham yoʻq.
- **Mahsulot boʻyicha harakatlar:** telefonda unumdorlik, matn hajmi, kuchli 1-bob yakuni, bepul uch bosqichli maslahat, keyingi tillar (avval ES, PT-BR, DE, FR, soʻng TR, keyin JA/KO/ZH) va boblarni chiqarish rejasi.

---

## 0. Labels used for numbers
| Label | Meaning |
|---|---|
| **[O] Official** | Read from a store listing or official help page on 2026-10-09 (source tag such as [G21] or [R1]) |
| **[E] Third-party estimate** | A vendor or tracker benchmark; the tracker is always named |
| **[C] Calculation / assumption** | Mine. Shown separately and never mixed into official figures |

**No paid tracker (Sensor Tower, AppMagic, data.ai) was accessed.** So there are no third-party download or revenue estimates for individual competitors in this document. The only revenue figures for competitors are those the developers themselves published (see `BUSINESS_STRATEGY.md` §2b).

---

## 1. Competitors, deeper

### 1.1 Official store facts (accessed 2026-10-09)
- **Ratings and counts** are exact values from the listing data: the structured data on Google Play, and Apple's iTunes Lookup API [A0] for the App Store. The store pages display them rounded.
- **Install ranges** exist on Google Play only.
- **“IAP per item”** is the range Google Play shows.

| Game (developer) | Google Play [O] | App Store (US) [O] | Monetisation [O] | Src |
|---|---|---|---|---|
| **Adventure Escape Mysteries** (Haiku Games) | ✔ · 10M+ · 4.64 (213,474) | ✔ · 4.76 (21,850) | Free; **contains ads**; IAP $0.99–$34.99 per item. On iOS: star packs and key packs, $0.99–$34.99. A review describes waiting for keys or watching ads to speed it up [A20] | G21, A20 |
| **Escape game: 50 rooms 1** (BusColdApp) | ✔ · 10M+ · 4.44 (960,464) | Not found on the US App Store by title or developer search (absence not proven) | Free; **contains ads**; IAP $0.99–$4.99 per item; “Humanized hints” | G22 |
| Escape game: 50 rooms 2 | ✔ · 10M+ · 4.46 (264,113) | Not found | Free; ads; IAP $0.99–$14.99 | G23 |
| Escape game: 50 rooms 3 | ✔ · 5M+ · 4.54 (148,650) | Not found | Free; ads; IAP $0.99–$4.99 | G24 |
| (A different series: “Room Escape: 50 rooms I”, Shenzhen Zhonglian) | — | ✔ · 4.53 (98,571) | Free | A23 |
| **100 Doors Challenge** (Play: Pixel Tale Games; iOS: Vladimir Poriadnikov; same title, link between publishers not verified) | ✔ · 10M+ · 4.70 (203,394) | ✔ · 4.58 (2,138) | Free; **contains ads**; IAP $1.49–$8.49 (Play); coin packs $0.99–$3.99 (iOS) | G25, A21 |
| Puzzle 100 Doors – Room escape (Pixel Tale Games) | ✔ · 5M+ · 4.36 (69,639) | — | Free; **contains ads**; no IAP shown | G26 |
| **100 Doors – Escape from Prison** (Peaksel) | ✔ · 10M+ · 4.49 (279,415) | ✔ · 4.50 (2,853) | Free; **contains ads**; IAP $0.99–$99.99 per item (Play). On iOS: coin packs to $19.99 and “Buy Battle Pass $9.99” | G27, A22 |
| Escape from School – 100 Doors (Peaksel) | ✔ · 10M+ · 4.23 (136,911) | — | Free; **contains ads**; IAP $0.99–$49.99 | G28 |
| **The Room 1–4** (Fireproof) | ✔ · 500K+ to 1M+ each · 4.80–4.90 | ✔ · 4.81–4.94 | **Paid**, $0.99 / $1.99 / $3.99 / $4.99; no ads | G1–G4, A1–A4 |
| **Cube Escape Collection** (Rusty Lake) | ✔ · 5M+ · 4.64 (64,030) | ✔ · 4.91 (6,700) | Free; **contains ads** (Play); “Unlock Premium $2.99” | G9, A8 |
| **Rusty Lake** paid games (Hotel, Roots, Paradise, Servant of the Lake) | ✔ · 10K+ to 500K+ · 4.60–4.94 | ✔ · 4.76–4.95 | **Paid**, $1.99–$4.99; free “Lite” versions exist | G11–G15, A10–A13 |

### 1.2 Third-party estimates
None. Per-title downloads or revenue would need a paid tracker, which was not used. I do not present any such numbers.

### 1.3 My calculations from the official data [C]
| Calculation | Result | Caveat |
|---|---|---|
| Mean Google Play rating of the **14 premium, no-ads titles** in `BUSINESS_STRATEGY.md` §2a: The Room 1–4, The House of Da Vinci 1–3, Rusty Lake Hotel/Roots/Paradise/Servant, Monument Valley 1–2, Agent A | **4.76** (median 4.80; lowest 4.39) | Correlation, not cause. Paid games attract self-selected fans |
| Mean Google Play rating of the **12 free, ad-supported titles** in both documents: Adventure Escape Mysteries, 50 rooms 1–3, the four 100 Doors titles, Tiny Room Stories, Doors: Awakening, Cube Escape Collection, Cube Escape: Seasons | **4.54** (median 4.58; highest 4.71) | Same caveat |
| Languages on the App Store listings of 13 comparable games [A0] | After English, the most common are FR, DE, JA, PT, RU, ES (10 of 13 each), IT (9), and KO, TR, ZH (8). **None lists Uzbek.** The Room, The Room: Old Sins and Adventure Escape Mysteries list **English only** | Listing metadata, not translation quality |
| Install floors on Google Play | Ad-supported escape games: 5M+ to 10M+. Premium mystery games: 10K+ to 1M+ (Monument Valley 5M+) | The ranges say nothing about revenue |

### 1.4 Style, praise, complaints and what we can beat
- **Visual style** is described from each listing's screenshots and description.
- **Praise and complaints** come from the reviews each store page shows at the top. That is a small, store-selected sample.

| Game | Graphics style | Puzzle style | Praised | Complained about | Weakness we can beat |
|---|---|---|---|---|---|
| Adventure Escape Mysteries | Illustrated 2D scenes with character portraits (screenshot); an episodic collection that includes a chapter tied to the TV show NCIS [G21] | Story chapters, room escapes, mini-games; heavy dialogue | “The stories are captivating and unpredictable” [A20]; variety; the “creepy” chapters [G21] | Key-gated levels: “you have to wait a certain period of time to get ‘keys’” [A20]. A recent chapter was “90% of it is dialogue and the puzzles … extremely easy and very short” [G21]. An account-deletion button placed where a tap deleted the account [G21] | No timers or keys. Story told through objects, not dialogue walls. Tactile 3D. A UI where destructive actions are never next to normal ones |
| Escape game: 50 rooms | Colourful pre-rendered 3D-look single scenes (screenshot) | 50 short self-contained rooms; codes and mechanisms | “very engaging and satisfying” after all 50 rooms [G22] | Unfair codes: “They want you to input codes that you have no way of knowing” [G22]. Exact-spot tapping [G22]. “Essential clues are very small” [G23]. Paid hints: “I won't pay for a consumable item … I would however pay for the ads to be removed” [G23] | Every answer comes from in-world evidence. Free 3-level hints. Exact colliders and tap maps. Text-scale and brightness settings |
| 100 Doors (Challenge, Prison, School) | Realistic pre-rendered rooms, one door per level (screenshots) | Very short levels (“a minute or so” [G25]), item and gesture tricks, coins for hints and skips | Quick levels, variety [G25]; “Not so difficult you feel like you need excessive hints” [G27] | Bugs: an item that “doesn't move at all” after buying a hint [G25]. Ads: “an ad after every level” [G28]; “the ad banner blocks part of the game” [G27]. Trial-and-error codes [G27] | No ads and no coins. Deduction instead of guessing. A no-softlock fuzz and real-tap playthroughs before release (`docs/GAMEPLAY_QA.md`) |
| The Room series | Tactile 3D close-ups of nested boxes (App Store Editors' Choice text [A1]) | Mechanisms, hidden latches, a special lens | Atmosphere, sound, a one-time purchase with no ads [G1][G2] | “Very Short Game” [G1] | A stronger story and choices that carry forward (`docs/STORY.md`). **EN/RU/UZ**: The Room lists English only on iOS [A0]. A clear chapter count |
| Cube Escape / Rusty Lake | Hand-drawn 2D point-and-click, surreal | Inventory puzzles, codes, cross-game lore | Story and mood; free entry [G9] | Crashes (Seasons) [G10]; back-and-forth walking (Paradise) [G13]; reliance on walkthroughs [G13]. The free games contain ads [G9][G10] | 3D presence; fair logic with in-game hints, so a walkthrough is not needed; no ads in the free chapter |

**No copying.** We copy none of these games' code, art, puzzles, story, audio or brand names, including in keywords; Apple's keyword rule forbids other apps' names [R27]. This analysis is about design qualities and business models only, as in `docs/DESIGN_PILLARS.md` §1.

---

## 2. Revenue models compared

### 2.1 The five models
| Model | What the player sees | Who uses it (official evidence) |
|---|---|---|
| **(a)** Ch1 free + paid Ch2–4 | One “Unlock Chapters 2–4” purchase; no ads | Monument Valley 3: 2 chapters free + “Unlock Full Game $5.99” [A16]; Agent A on iOS [A17] |
| **(b)** Rewarded ads for hints | A free game; watch an ad to get a hint | Adventure Escape Mysteries: ads speed up keys [A20] |
| **(c)** Ad-free premium upgrade | A free game with ads; pay once to remove them | Doors: Awakening “Remove Ads $2.99” and “VIP Pack $4.99” [A19]; Tiny Room Stories [A18] |
| **(d)** One-time purchase upfront | Pay before installing | The Room, Rusty Lake paid games, Monument Valley 1–2 [G1–G4][G11–G14][G16][G17] |
| **(e)** Free-to-play + IAP | Free game; buy hint, key or coin packs | 100 Doors titles [G25][G27][G28]; 50 rooms [G22]; Adventure Escape Mysteries [G21] |

### 2.2 Inputs, kept separate
**Downloads are not monthly active users (MAU).**
- The rows below use **downloads** (lifetime installs) because the game is a finite story: revenue is earned per player over their whole play-through, not per month.
- MAU is shown only for context. If downloads arrive evenly over 12 months, new installs per month are 833 / 8,333 / 83,333 for 10k / 100k / 1M downloads [C]. MAU is at least that, plus returning players.
- A third-party retention figure for puzzle games is D7 4.5% and D30 1.2%. Mistplay cites it to GameAnalytics' 2025 benchmarks [E: Mistplay/GameAnalytics, T2]. Our own retention must be measured in the test waves (`BUSINESS_STRATEGY.md` §6–7).

| Input | Conservative | Medium | Optimistic | Label and basis |
|---|---|---|---|---|
| Downloads | 10k / 100k / 1M | same | same | Scenario inputs |
| **Rewarded-video eCPM, US/EU** | $5 | $9 | $15 | [C], anchored on [E]:<br>• Appodeal Q4 2024 (read from charts by Playio): Europe ~$5.1 Android / ~$8.9 iOS; North America ~$9.0 / ~$13.6 [T1].<br>• Tenjin × CAS Q2 2024: US $30.25 Android / $24.39 iOS [T1].<br>• Mistplay: US rewarded average $15.15, period not stated [T2] |
| **Rewarded-video eCPM, CIS/Uzbekistan** | $0.5 | $1.0 | $2.0 | [C]. **No verifiable current figure for Uzbekistan or Kazakhstan.** The latest public Russia figures are 2022 Appodeal data reported by WN Hub: Feb $1.80 Android / $3.05 iOS; Mar $0.75 / $1.45; Jun $1.43 / $1.90 [E: Appodeal via WN Hub, T3] |
| **Rewarded-video eCPM, rest of world** | $1.0 | $1.8 | $3.4 | [C], anchored on Appodeal Latin America ~$1.8 Android / ~$3.4 iOS [E, T1] |
| Audience mix (CIS+UZ / US+EU / rest) | 40 / 30 / 30 % | same | same | [C]: an EN/RU/UZ game with Uzbek-first marketing |
| **Blended eCPM** | **$2.00** | **$3.64** | **$6.32** | [C] |
| Ad views per download, lifetime: (b) hints only | 2 | 5 | 10 | [C] |
| Ad views per download, lifetime: (c) interstitial + rewarded | 5 | 12 | 25 | [C]. 25 means an ad roughly every 5–10 minutes of play |
| Ad-network share | 0% extra | 0% extra | 0% extra | [C]. The benchmark eCPMs are treated as the publisher's share, but the sources do not state whether they are net or gross [T1]. AdMob's share for apps is not published on any help page I found. If the eCPMs are gross, ad revenue is lower |
| (a) Unlock conversion per download, $4.99 | 1% | 2% | 3% | [C]. Public data points: 0.67% (Gasketball, 2012) and >5% (Super Mario Run, 2017) (`BUSINESS_STRATEGY.md` §4.4) |
| (c) Remove-ads conversion, $2.99 | 0.5% | 1% | 2% | [C]; no benchmark found |
| (d) Upfront buyers per 1,000 people reached, $4.99 | 5 | 10 | 20 | [C]; no benchmark found. A paid page converts far fewer visitors than a free one |
| (e) Payer rate × lifetime spend per payer | 0.5% × $3 | 1.5% × $5 | 3% × $8 | [C]; no verified payer-rate benchmark for finite puzzle games was found |
| Store commission | 15% | 15% | 15% | [O]: Apple Small Business Program and Google Play's first-$1M rates [R1][R2][R3] |
| VAT handled by the stores | 10% of gross | 10% | 10% | [C], based on [O] tax-inclusive pricing [R9]. Applies to store purchases only |
| Refunds | 2% | 2% | 2% | [C]; no benchmark found |
| Fixed costs per year | $1,300 | $1,300 | $1,300 | [C]: same as `BUSINESS_STRATEGY.md` §4.1. Ad models also need consent, Data safety and privacy-label work, which costs time rather than cash |

**Formulas [C]:**
- Store purchases are worth price × 0.9 × 0.85 × 0.98 = **74.97% of the gross**.
- Ad revenue = downloads × views × eCPM ÷ 1,000. It does not pass through store billing, so no store fee or store VAT applies.
- In (c), buyers stop seeing ads.

### 2.3 Results: proceeds before fixed costs; in brackets, net after $1,300 fixed costs (before income tax) [C]
| Model | Scenario | 10k downloads | 100k downloads | 1M downloads |
|---|---|---|---|---|
| (a) Ch1 free + $4.99 unlock | Conservative | $374 (−$926) | $3,741 ($2,441) | $37,410 ($36,110) |
| | Medium | $748 (−$552) | $7,482 ($6,182) | $74,820 ($73,520) |
| | Optimistic | $1,122 (−$178) | $11,223 ($9,923) | $112,230 ($110,930) |
| (b) Rewarded ads for hints | Conservative | $40 (−$1,260) | $400 (−$900) | $4,000 ($2,700) |
| | Medium | $182 (−$1,118) | $1,820 ($520) | $18,200 ($16,900) |
| | Optimistic | $632 (−$668) | $6,320 ($5,020) | $63,200 ($61,900) |
| (c) Free with ads + $2.99 remove-ads | Conservative | $212 (−$1,088) | $2,116 ($816) | $21,158 ($19,858) |
| | Medium | $657 (−$643) | $6,566 ($5,266) | $65,659 ($64,359) |
| | Optimistic | $1,997 ($697) | $19,967 ($18,667) | $199,672 ($198,372) |
| (d) $4.99 paid upfront (per people reached) | Conservative | $187 (−$1,113) | $1,871 ($571) | $18,705 ($17,405) |
| | Medium | $374 (−$926) | $3,741 ($2,441) | $37,410 ($36,110) |
| | Optimistic | $748 (−$552) | $7,482 ($6,182) | $74,820 ($73,520) |
| (e) F2P + hint packs | Conservative | $112 (−$1,188) | $1,125 (−$175) | $11,246 ($9,946) |
| | Medium | $562 (−$738) | $5,623 ($4,323) | $56,228 ($54,928) |
| | Optimistic | $1,799 ($499) | $17,993 ($16,693) | $179,928 ($178,628) |

**Per 1,000 downloads [C]:**
| Model | Conservative | Medium | Optimistic |
|---|---|---|---|
| (a) | $37 | $75 | $112 |
| (b) | $4 | $18 | $63 |
| (c) | $21 | $66 | $200 |
| (d) | $19 | $37 | $75 |
| (e) | $11 | $56 | $180 |

**How to read this:**
- Model (a) leads in the conservative and medium cases.
- Models (c) and (e) lead only in their optimistic cases. Those cases need an ad every few minutes or 3% of players buying consumables, which is exactly the behaviour the genre's reviews complain about (1.4).
- All ad figures rest on eCPM assumptions with **no verified data for Uzbekistan or the CIS**.

### 2.4 Player-experience costs and review risk
| Cost | Evidence |
|---|---|
| Ads break the atmosphere of a quiet, melancholic mystery (`docs/STORY.md` “Tone”) | Reviews of ad-supported escape games: “an ad after every level” [G28]; “the ad banner blocks part of the game” [G27] |
| Paid or ad-gated hints feel unfair in a fairness-first design | “I won't pay for a consumable item … I would however pay for the ads to be removed” [G23]; waiting for keys [A20] |
| Lower ratings | Premium no-ads titles average 4.76 vs 4.54 for ad-supported ones on Google Play (1.3) [C]. Correlation only |
| Broken promises | The store listing says “No ads, no energy, no subscriptions” (`docs/STORE_LISTING.md`). The privacy policy says “no advertising, no analytics and no third-party tracking SDKs” and no data is sent over the internet [R32] |
| Privacy and compliance work | An ad SDK transmits data off the device, so it must be declared. “Device or other IDs” (which includes advertising IDs) is a Data safety data type [R23]. The App Store privacy label would change too [R24]. The game would stop being fully offline |
| Revenue fragility | Russia eCPM fell by more than half within a month in 2022 [T3]. Ad income depends on markets we cannot control |

### 2.5 Recommendation
**Model (a): Chapter 1 free and one $4.99 unlock for Chapters 2–4, with no ads and no consumables.** The reasons:
1. **It is the best model in the realistic cases.** In the conservative and medium columns it is ahead of every alternative [C].
2. **It fits the product.** The game is fair, atmospheric and offline, with free hints. Ads and paid hints contradict all four of those qualities.
3. **It protects reviews and word of mouth,** the main free marketing channel for this genre (`BUSINESS_STRATEGY.md` §2b, §5).
4. **It has current, high-profile precedent:** Monument Valley 3 [A16] and Agent A on iOS [A17].
5. **It keeps privacy simple:** no SDKs, no identifiers, and the current privacy answers stay true.

**If (a) underperforms after launch,** test a lower regional price before any ad model. A Google Play paid listing with a 60-minute free trial [R29] is a second option to evaluate. Each change needs the owner's decision.

**Nothing is enabled now.**
- No ad SDK is added.
- Billing stays disabled (`REAL_PAYMENTS_ENABLED = false`).
- The checklist in `BUSINESS_STRATEGY.md` §9 must be completed and the owner must decide first.

---

## 3. How to be better than these competitors: product actions
Each action starts from MYSTERY ROOM's state on 2026-10-09 (`docs/QUALITY_REPORT.md`, `docs/GAMEPLAY_QA.md`, `docs/VARIANTS.md`, the chapter design documents).

### 3.1 Premium visual design
- **Now:** graphics scored 7.5 (Ch1) and 8 (Ch2) on evidence from software-rendered screenshots. Gaps: “Some props are plain; there are no phone captures”, and the Ch2 film image is dim.
- **Actions:**
  1. Capture every key view on a real mid-range Android phone and an iPhone, and fix what differs from the container renders.
  2. Polish the plainest props first, starting with those the player inspects up close.
  3. Keep one lighting language per chapter: moonlight → warm power → red darkroom in Ch1.
  4. Store screenshots only from real device captures.
- **Beats:** the pre-rendered single scenes of the 50 rooms and 100 Doors games (1.4) with a lit, explorable 3D room.

### 3.2 Logical, fun puzzles
- **Now:**
  - Every answer comes from in-world evidence, and solutions are language-neutral.
  - The no-softlock fuzz and real-tap playthroughs pass: Ch1 13/13 steps; Ch2 0 fallbacks on both lens paths.
  - Per-game variants are live for the Ch1 gear box, safe and beacon, and for the Ch2 valves, punch card, tapes and dial, splice, focus and vault.
- **Actions:**
  1. In the test waves, log the time per puzzle and the hint level reached (`BUSINESS_STRATEGY.md` §7).
  2. Redesign any puzzle where more than 15% of players need hint level 3.
  3. Audit every code for “could a player know this?”, which is the top complaint against 50 rooms [G22].
  4. Keep wrong attempts answered with a sound or line, as the player review already checks.
- **Beats:** trial-and-error codes [G27] and pixel hunting [G22].

### 3.3 A strong mystery story
- **Now:** the story is told through objects, handwriting and light, with “fair twists” (the 1979 postmark; the echo that turns). Choices carry forward: the lens, the shards and Leyla's or Strand's key.
- **Actions:**
  1. End Chapter 1 on its strongest beat (the echo turning, then the postmark) *before* the purchase offer.
  2. Show a one-screen “Previously…” card at the start of each chapter.
  3. Keep the notebook as the always-available case file.
  4. Never pad with dialogue, which is the complaint against a recent Adventure Escape Mysteries chapter [G21].
- **Beats:** The Room's thin story (`docs/DESIGN_PILLARS.md`) and dialogue-heavy chapters.

### 3.4 Chapter retention
- **Actions:**
  1. Each chapter ends with a visible hook and a named next location (Archive B → Level −2 → the Array Hall).
  2. Show the chapter list with locked chapters and their names, so players see the whole arc.
  3. Save automatically after every solved puzzle, and make Continue land exactly where the player was. Save and continue are already automated-tested.
  4. Never use timers or energy.
- **Measure:** Ch1 completion, and the share of Ch1 completers who open the chapter list (opt-in summary only, `BUSINESS_STRATEGY.md` §7).

### 3.5 A non-intrusive hint system
- **Now:** free, unlimited hints with a three-level ladder (nudge → where to look → the answer). Level 3 names the player's *own* variant answer. A gentle nudge after a long idle is planned (`docs/GAMEPLAY_QA.md`).
- **Actions:**
  1. Keep hints free and ad-free.
  2. Add the idle nudge as an opt-out setting.
  3. Make level 3 require one extra tap (“Show the answer?”), so it is never seen by accident.
  4. Count hint use per puzzle in the local summary.
- **Beats:** paid hints [G23], coins [A21][A22] and “Hints don't really help you” [G20].

### 3.6 Android and iOS performance
- **Now:**
  - Ch1 has ~175–183k primitives against a 150k target. The Ch2 hall has 216 draw calls and ~161k primitives against 150 / 150k.
  - **No FPS has been measured on a phone.** The debug APK is 123 MB.
  - PerfGuard scales the 3D resolution, and Vulkan falls back to GL.
- **Actions:**
  1. Do the planned LOD and shadow-caster pass until both chapters meet the budget.
  2. Run the `docs/TESTING_ON_DEVICE.md` checklist on at least 3 low- and mid-range Android phones and 1 older iPhone: FPS, heat after 30 minutes, load time, memory.
  3. Offer a “battery saver” setting with lower resolution and fewer shadows.
  4. Consider downloading Ch2–4 assets separately after purchase, to keep the first install small. Check Godot and store support first.
- **Beats:** the glitch and lag complaints against the 100 Doors titles [G25][A22].

### 3.7 Languages: EN/RU/UZ now, then more
- **Now:**
  - 299 Ch1 keys in EN/RU/UZ, checked by a validator and screenshots.
  - Localized decals exist for Ch2.
  - The fonts cover Latin, Latin-1 and Cyrillic only (`docs/FONT_COVERAGE.md`).
  - No native-speaker review yet.
- **First:** native review of RU and UZ (2 reviewers each) before launch. Uzbek is our differentiator: none of the 13 comparable iOS listings has it [A0].
- **Next languages, in this order (my judgement):**

| Order | Languages | Why |
|---|---|---|
| 1 | Spanish, Brazilian Portuguese, German, French | Each is on 10 of 13 comparable listings [A0]. They need only Latin-1, which our fonts already cover, so there is no font work |
| 2 | Turkish | On 8 of 13 [A0]. A Turkic language like Uzbek, so UZ testers may help review it. Google handles VAT for Türkiye [R9]. Needs a font check for Latin Extended-A letters (ğ ş ı İ), which `docs/FONT_COVERAGE.md` does not yet test |
| 3 | Japanese, Korean, Simplified Chinese | JA is on 10 of 13 listings, KO and ZH on 8 [A0]. They need new CJK fonts, layout re-checks and decal variants, so the effort is highest |

- **Rules:** keep every puzzle language-neutral, as now. Every new language needs its own store listing, screenshots and native review.

### 3.8 Chapter release plan (proposal)
| Step | Content | Condition | Store action |
|---|---|---|---|
| 1. Public launch | Ch1 free + **Ch2 available** through the unlock; Ch3–4 shown as “coming” | `BUSINESS_STRATEGY.md` §9 checklist complete; Ch2 has passed human testing | Apple “App Launch” nomination, at least 3 weeks ahead [R28] |
| 2. Ch3 “The Underground Facility” | Free update for owners of the unlock | Ch3 logic, scene, 3D playthrough on both key paths, human test | An “App Enhancements / New Content” nomination [R28]. Promotional text update [R27] |
| 3. Ch4 “The Experiment” | Free update; the endings depend on Ch1–3 choices | Same quality gate | Nomination; press and creator outreach |

- **Timing:** the gap between steps should follow quality, not a calendar. I suggest announcing a date only when a chapter has passed its 3D playthrough.
- **Honesty:** the listing must say clearly which chapters are available today. Selling the unlock before Ch2 exists is not recommended.

---

## Sources
All accessed **2026-10-09**. IDs shared with `BUSINESS_STRATEGY.md` resolve to the same URLs; only the ones used here are listed.

| ID | Source | URL |
|---|---|---|
| G1–G4 | The Room, Two, Three, Old Sins — Google Play | https://play.google.com/store/apps/details?id=com.FireproofStudios.TheRoom (…TheRoom2, …TheRoom3, …TheRoom4) |
| G9 | Cube Escape Collection — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.CubeEscapeCollection |
| G10 | Cube Escape: Seasons — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.CubeEscapeSeasons |
| G11–G13 | Rusty Lake Hotel, Roots, Paradise — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.RustyLakeHotel (…RustyLakeRoots, …RustyLakeParadise) |
| G14–G15 | Servant of the Lake and Lite — Google Play | https://play.google.com/store/apps/details?id=com.RustyLake.ServantOfTheLake (…ServantOfTheLakeLite) |
| G16–G17 | Monument Valley 1–2 — Google Play | https://play.google.com/store/apps/details?id=com.ustwo.monumentvalley (…monumentvalley2) |
| G20 | Doors: Awakening — Google Play | https://play.google.com/store/apps/details?id=com.snapbreak.doors |
| G21 | Adventure Escape Mysteries — Google Play | https://play.google.com/store/apps/details?id=com.haiku.adventure.escape.game.mystery.stories |
| G22 | Escape game: 50 rooms 1 — Google Play | https://play.google.com/store/apps/details?id=com.coldapp.at50rooms1 |
| G23 | Escape game: 50 rooms 2 — Google Play | https://play.google.com/store/apps/details?id=com.coldapp.at50rooms2 |
| G24 | Escape game: 50 rooms 3 — Google Play | https://play.google.com/store/apps/details?id=com.coldapp.at50rooms3 |
| G25 | 100 Doors Challenge — Google Play | https://play.google.com/store/apps/details?id=com.protey.doors_challenge |
| G26 | Puzzle 100 Doors – Room escape — Google Play | https://play.google.com/store/apps/details?id=com.protey.doors_challenge2 |
| G27 | 100 Doors – Escape from Prison — Google Play | https://play.google.com/store/apps/details?id=com.hundred_doors_game.escape_from_prison |
| G28 | Escape from School – 100 Doors — Google Play | https://play.google.com/store/apps/details?id=com.hundred_doors_game.escape_from_school |
| A0 | Apple iTunes Lookup API (rating counts, language lists) | https://itunes.apple.com/lookup?id=552039496,1286676015,1062515791,1469235524,6443563379,940006911,1555267021,6748751735,1459520173,1419796608,1583536868,1089890170,1483451514&country=us |
| A1–A4 | The Room, Two, Three, Old Sins — App Store | https://apps.apple.com/us/app/the-room/id552039496 · /id667362389 · /id918054748 · /id1286676015 |
| A8 | Cube Escape Collection — App Store | https://apps.apple.com/us/app/cube-escape-collection/id1555267021 |
| A10–A13 | Rusty Lake Hotel, Roots, Paradise, Servant of the Lake — App Store | https://apps.apple.com/us/app/rusty-lake-hotel/id1059911569 · /id1142016085 · /id1253855339 · /id6748751735 |
| A16 | Monument Valley 3 — App Store | https://apps.apple.com/us/app/monument-valley-3/id6443563379 |
| A17 | Agent A — App Store | https://apps.apple.com/us/app/agent-a-a-puzzle-in-disguise/id940006911 |
| A18 | Tiny Room Story: Town Mystery — App Store | https://apps.apple.com/us/app/tiny-room-story-town-mystery/id1459520173 |
| A19 | Doors: Awakening — App Store | https://apps.apple.com/us/app/doors-awakening/id1483451514 |
| A20 | Adventure Escape Mysteries — App Store | https://apps.apple.com/us/app/adventure-escape-mysteries/id1419796608 |
| A21 | 100 Doors Challenge — App Store | https://apps.apple.com/us/app/100-doors-challenge/id1089890170 |
| A22 | 100 Doors – Escape from Prison — App Store | https://apps.apple.com/us/app/100-doors-escape-from-prison/id1583536868 |
| A23 | Room Escape: 50 rooms I (Shenzhen Zhonglian) — App Store | https://apps.apple.com/us/app/room-escape-50-rooms-i/id1107507527 |
| R1 | Google Play — Service fees | https://support.google.com/googleplay/android-developer/answer/112622 |
| R2 | Google Play — 15% service fee tier | https://support.google.com/googleplay/android-developer/answer/10632485 |
| R3 | Apple — App Store Small Business Program | https://developer.apple.com/app-store/small-business-program/ |
| R9 | Google Play — Tax rates and VAT | https://support.google.com/googleplay/android-developer/answer/138000 |
| R23 | Google Play — Data safety section | https://support.google.com/googleplay/android-developer/answer/10787469 |
| R24 | Apple — App privacy details | https://developer.apple.com/app-store/app-privacy-details/ |
| R27 | App Store Connect — Platform version information (keywords rule, promotional text) | https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information |
| R28 | App Store Connect — Nominate your app for featuring | https://developer.apple.com/help/app-store-connect/manage-featuring-nominations/nominate-your-app-for-featuring |
| R29 | Google Play — Free trial for paid games | https://support.google.com/googleplay/android-developer/answer/16923846 |
| R32 | MYSTERY ROOM privacy policy | https://sites.google.com/view/mysteryroom-privacy |
| T1 | Playio, “Mobile game eCPM benchmarks 2026” (Appodeal Q4 2024 regional charts; Tenjin × CAS Q2 2024) | https://blog.playio.co/mobile-game-ecpm-benchmarks-2026 |
| T2 | Mistplay, “Rewarded ads stats” (2025-11-11; US rewarded eCPM; GameAnalytics 2025 retention) | https://business.mistplay.com/resources/rewarded-ads-stats/ |
| T3 | WN Hub, 2022-07-11, Appodeal eCPM in Russia | https://wnhub.io/news/marketing/item-20615 |

## Could not be verified
- Rewarded-video eCPM for **Uzbekistan and Kazakhstan** in any recent public source. The CIS values in 2.2 are assumptions.
- Whether the Appodeal, Tenjin and Mistplay eCPMs are net or gross of the ad network's share, and AdMob's revenue share for apps.
- Benchmarks for remove-ads conversion, upfront purchase rate per visitor, and F2P payer rate for finite puzzle games.
- Third-party download or revenue estimates for any competitor (no paid tracker was used).
- Whether “Escape game: 50 rooms” is on the App Store; my searches did not find it.
- Whether Pixel Tale Games (Play) and Vladimir Poriadnikov (iOS) publish the same “100 Doors Challenge”.
- Monument Valley 3's Google Play listing.
- Play lengths of all competitors (HowLongToBeat was not reachable).
