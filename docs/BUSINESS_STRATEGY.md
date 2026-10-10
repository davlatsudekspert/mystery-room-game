# Business Strategy — MYSTERY ROOM: The Forgotten Institute

_Draft for the owner. Research date: 2026-10-09. Companion document: [`MARKET_ANALYSIS.md`](MARKET_ANALYSIS.md) (deeper competitor review, revenue models compared, product actions). Technical monetization notes: [`MONETIZATION.md`](MONETIZATION.md)._

## Qisqacha mazmun (oʻzbekcha)
- **Model (egasining qarori, 2026-10-10; Monument Valley 3 uslubida):** 1- va 2-boblar bepul. 3–4-boblar bitta xarid (`full_game`, $4.99, doʻkonlarning mintaqaviy narxlari) bilan ochiladi. Reklama yoʻq, internetsiz ishlaydi, EN/RU/UZ. Haqiqiy toʻlovlar hali oʻchiq (`REAL_PAYMENTS_ENABLED = false`).
- **Raqobatchilar:** The Room, The House of Da Vinci, Rusty Lake, Monument Valley, Agent A. Monument Valley 3 aynan bizning modelni ishlatadi: dastlabki 2 bob bepul, toʻliq oʻyin bitta xarid, App Store-da $5.99.
- **Doʻkon komissiyasi:** yiliga birinchi $1 mln daromad uchun ikkala doʻkonda 15%. Buning uchun Apple Small Business Program va Google Play 15% tier dasturlariga yozilish shart.
- **Soliqlar:** Yevropa, AQSh va boshqa koʻp davlatlarda QQS yoki sales tax-ni doʻkonning oʻzi undiradi va toʻlaydi. Lekin **Oʻzbekistondagi xaridorlarga** sotuvda Oʻzbekistonda yashovchi dasturchi QQSni oʻzi hisoblashi va toʻlashi kerak (Google va Apple qoidalari). Bu yerda soliq boʻyicha maslahat berilmaydi: 3.5-boʻlimdagi savollarni mahalliy soliq maslahatchisi bilan aniqlang.
- **Pul olish:** Google Oʻzbekistonga USD-da bank oʻtkazmasi (wire) bilan toʻlaydi, eng kam miqdor $100. Apple uchun eng kam miqdor $40.
- **Rossiya:** Google Play-da 2022-yildan beri xarid toʻxtatilgan. Apple-da 2026-yil 1-apreldan telefon hisobi orqali toʻlov yoʻq. Rus tilidagi oʻyinchilarning katta qismi xarid qila olmasligi mumkin.
- **Daromad (taxminiy hisob):** 100 000 oʻyinchi × 2% × $4.99 ≈ **$6 200**, 1 000 000 × 2% ≈ **$73 500** daromad soligʻidan oldin. Barcha taxminlar 4-boʻlimda yozilgan.
- **$0 marketing:** ASO, haqiqiy oʻyindan treyler, press-kit, Reddit, Discord, TikTok, YouTube, Telegram, bepul festivallar (DevGAMM Awards, GDWC).
- **Test:** avval 5–8 kishi bilan “ovoz chiqarib oʻylash” sessiyalari, soʻng yopiq test (yangi shaxsiy Google hisoblari uchun kamida 12 tester, 14 kun), keyin 100–1000 oʻyinchi.
- **Analitika:** hozirgi maxfiylik siyosati “maʼlumot toʻplanmaydi” deydi. Har qanday analitika uchun siyosatni yangilash, rozilik oynasi va doʻkon anketalarini oʻzgartirish kerak.
- Haqiqiy toʻlovlarni yoqishdan oldin 9-boʻlimdagi roʻyxatni toʻliq bajaring.

---

## 0. How to read this document
- **Labels for numbers.** Every external number has a source tag such as [G1] or [R3]. The tags resolve to URLs in [Sources](#sources), all accessed on **2026-10-09**.
  - **Official:** a store listing, store help page or agreement.
  - **Developer-reported / press-reported:** a developer's own statement, or a press article quoting one.
  - **Third-party estimate:** a tracker or vendor benchmark. It is named every time.
  - **Assumption** and **calculation:** mine. They are marked as such.
- **Not advice.** Nothing here is tax, legal or accounting advice. Section 3.5 lists the questions to take to a local tax adviser.
- **Unpublished numbers.** No competitor's revenue or downloads are presented as fact unless the developer published them. Google Play shows only install *ranges* (for example “1M+”).

## 1. The business model at a glance
| Element | Decision | Status |
|---|---|---|
| Chapter 1 “The Locked Laboratory” | Free, full chapter (estimated 35–60 min for a first-time player; an estimate, not a measurement: `docs/GAMEPLAY_QA.md`) | Playable end to end by automated taps; no human test yet |
| Chapters 2–4 | One non-consumable product `full_game`, a one-time purchase | Ch2 in integration, Ch3 designed, Ch4 planned |
| Price | Under consideration: $3.99 / **$4.99** / $6.99 | Owner decides |
| Ads, subscriptions, energy | None | Matches the store listing promise “No ads, no energy, no subscriptions” |
| Connectivity | Offline | Privacy policy: “the game works fully offline and does not send data over the internet” [R32] |
| Languages | EN, RU, UZ | 299 keys for Ch1 |
| Real payments | **Disabled** until store validation | `Premium.REAL_PAYMENTS_ENABLED = false` |

**Closest public precedent:** Monument Valley 3 on the App Store: “Play the first two chapters of Monument Valley 3 for free, then unlock the full game … with a single in-app purchase”. The listed purchase is “Unlock Full Game $5.99” [A16].

**Why the unlock lives inside the same app:** The House of Da Vinci 2 used a separate “Lite” demo app. Its top review on Google Play says: “As a demo, the option to purchase should have simply unlocked the rest of the game. Instead I had to install another, separate game and play the entire demo with forced tutorial all over again” [G7]. One app with an in-app unlock avoids that.

**An alternative to keep in mind:** Google Play offers a free trial for *paid* games: “The trial allows for 60 minutes of full gameplay” [R29]. It applies to paid apps, not to a free app with an in-app unlock, so it would mean a different model on Android. It is noted here only for completeness. See `MARKET_ANALYSIS.md` for the model comparison.

---

## 2. Comparable games

### 2a. Store facts (official listing data, accessed 2026-10-09)
- **Ratings and counts.** Exact values come from the data embedded in each listing: the page's structured data on Google Play, and Apple's iTunes Lookup API [A0] for the App Store, which feeds the same listing. The pages show the same figures rounded; The Room on Google Play shows “4.8” and “290K reviews”.
- **Prices** are US store prices in USD.
- **Install ranges** exist only on Google Play.

| Game (developer) | Model | Google Play: price · rating (count) · installs | App Store (US): price · rating (count) | Src |
|---|---|---|---|---|
| The Room (Fireproof Games) | Paid | $0.99 · 4.80 (289,914) · 1M+ | $0.99 · 4.81 (7,655) | G1, A1 |
| The Room Two | Paid | $1.99 · 4.90 (244,660) · 1M+ | $1.99 · 4.90 (16,674) | G2, A2 |
| The Room Three | Paid | $3.99 · 4.86 (114,056) · 1M+ | $3.99 · 4.94 (33,874) | G3, A3 |
| The Room: Old Sins | Paid | $4.99 · 4.89 (85,977) · 500K+ | $4.99 · 4.94 (35,258) | G4, A4 |
| The House of Da Vinci (Blue Brain Games) | Paid; free “Lite” demos exist | $2.50 · 4.39 (42,202) · 500K+ | $3.99 · 4.78 (25,035) | G5, A5 |
| The House of Da Vinci 2 | Paid | $5.99 · 4.68 (17,934) · 100K+ | $4.99 · 4.83 (11,110) | G6, A6 |
| The House of Da Vinci 2 Lite | Free demo app | Free · 3.61 (1,029) · 100K+ | — | G7 |
| The House of Da Vinci 3 | Paid | $6.99 · 4.69 (8,592) · 100K+ | $5.99 · 4.84 (5,757) | G8, A7 |
| Cube Escape Collection (Rusty Lake) | Free + ads + “Unlock Premium” | Free, contains ads, IAP $2.99 · 4.64 (64,030) · 5M+ | Free, “Unlock Premium $2.99” · 4.91 (6,700) | G9, A8 |
| Cube Escape: Seasons | Free + ads + IAP | Free, contains ads, IAP $0.99 · 4.61 (49,679) · 1M+ | Free · 4.81 (1,420) | G10, A9 |
| Rusty Lake Hotel | Paid | $1.99 · 4.60 (20,581) · 500K+ | $1.99 · 4.77 (1,563) | G11, A10 |
| Rusty Lake: Roots | Paid | $2.99 · 4.67 (16,034) · 100K+ | $2.99 · 4.82 (1,121) | G12, A11 |
| Rusty Lake Paradise | Paid | $2.99 · 4.81 (10,350) · 100K+ | $2.99 · 4.76 (1,777) | G13, A12 |
| Servant of the Lake (2026) | Paid + free “Lite” | $4.99 · 4.94 (8,942) · 10K+ (Lite: free · 4.78 (3,111) · 100K+) | $4.99 · 4.95 (2,181); page shows “Chart #5 Puzzle” | G14, G15, A13 |
| Monument Valley (ustwo games) | Paid + paid expansion | $3.99, IAP $1.99 · 4.86 (268,136) · 5M+ | $3.99 · 4.77 (17,035) | G16, A14 |
| Monument Valley 2 | Paid | $3.99 · 4.89 (85,888) · 1M+ | $3.99 · 4.65 (14,040) | G17, A15 |
| Monument Valley 3 | **Free 2 chapters + one unlock** | Not verified (Play listing not found by me) | Free, “Unlock Full Game $5.99” · 4.85 (4,781) | A16 |
| Agent A: A puzzle in disguise (Yak & Co) | Play: paid. iOS: **free + one unlock** | $5.99 · 4.73 (81,479) · 500K+ | Free, “Agent A full game … all 5 chapters $9.99” · 4.84 (10,669) | G18, A17 |
| Tiny Room Stories: Town Mystery (Kiary Games) | Free + ads + IAP | Free, contains ads, IAP $1.99–$40.99/item · 4.71 (373,551) · 10M+ | Free, contains ads, “Full set $2.99” + key packs · 4.78 (11,282) | G19, A18 |
| Doors: Awakening (Snapbreak) | Free to try + ads + unlock | Free, contains ads, IAP $1.99–$6.99/item · 4.62 (42,920) · 1M+ | Free, “VIP Pack — All Levels & No Ads & Infinite Hints $4.99” · 4.63 (2,447) | G20, A19 |

### 2b. Length, reviews and marketing
- **Length.** HowLongToBeat could not be reached with my tools, and none of these developers states a play time on its store page. Each length below is one reviewer's report on the store page, not a measurement.
- **Praise and complaints** come from the reviews the store page shows at the top on the access date. That is a small, store-selected sample, not a survey.

| Game | Length (one reviewer's report) | Praised | Complained about | Marketing used publicly |
|---|---|---|---|---|
| The Room series | “Very Short Game … for $1 it's okay” [G1] | Atmosphere, sound, fair difficulty; “No ads, nothing required from the player other that a one time purchase” [G2] | Too short (Room 1) [G1] | Launch featuring by Apple: “We made over $100,000 in that first week we were featured” (developer, 2013) [D1]. “This all happened without Fireproof spending any money on marketing or PR or analysts or analytics” (developer, 2014; combined sales of The Room and The Room Two “have hit 5.4 million”) [D2]. Editors' Choice on the App Store [A1] |
| The House of Da Vinci 1–3 | Not stated | Puzzles, story (2 and 3), Renaissance setting [G6][G8] | Finicky touch input: “nothing happen because I'm not touching the exact fraction of a millimeter of my screen” [G5]; camera and zoom; the separate demo app [G7] | Kickstarter: “successfully funded on Kickstarter in late 2016 … over 2.391 adventure game enthusiasts that backed” it (developer text on the listing) [A5]. Free Lite demo apps [G7]. 16 languages on iOS [A0] |
| Rusty Lake / Cube Escape | “each of these seperate stories can be finished in an hour or so” [G9] | Story, strange art and mood, cross-game lore; free entry point | Crashes (Seasons) [G10]; back-and-forth walking (Paradise) [G13]; some puzzles need a walkthrough [G13] | The free Cube Escape games came first to build a community: “6 free to play games with hardly any ads”; launching premium first “never would have had the success” (developers, 2018) [D3]. Official walkthrough videos on their own YouTube channel [D4]. Free “Lite” versions [G15]. 25 languages for the Collection [A0] |
| Monument Valley 1–3 | MV2: “2.5 hours”; MV1: “maybe 5.5 hours” (one reviewer) [G17] | Artistry; “Not trying to squeeze every last dime out of me through micro transactions” [G16] | “Cute, but short and too easy” [G16] | The listing names “Apple Game of the Year 2014” and “Apple Design Award 2014” [A14]. ustwo published its own year-2 figures: about $14.38M revenue and 26.1M downloads, about 80% of them during free promotions (press report of ustwo's post) [D5]. Sales rose when the game appeared in *House of Cards* [D5]. MV3 uses try-before-you-buy [A16] |
| Agent A | “not too short either” [G18] | Intuitive puzzles, music and cut-scenes, no timed events | “Could use a hint button, but there's always a YouTube tutorial” [G18] | Selected as a winner of the PAX Australia 2015 Indie Showcase (developer quote) [D6]. An “episodic tale … spanning five chapters” [G18]. Listing claims a “Google Play Android Excellence award” [G18] and Apple Editors' Choice [A17] |
| Tiny Room Stories | Not stated | 3D rooms you rotate; “easy access no-baiting hints” [G19] | Ad-removal price confusion; hard to resume mid-level [G19] | Released in acts (“I played way back when only act 1 was available”) [G19]; awards listed on the store page (for example a DevGAMM 2019 nomination) [A18] |
| Doors: Awakening | Not stated | Graphics; “no penalties for wrong tries. No time limits” [G20] | Pauses the player's music (audio focus); thin story; weak hints [G20] | “TRY FOR FREE … unlock the full experience” [G20] |

### 2c. What this means for us
1. **Premium, no-ads mystery games rate highest.** The Room, Monument Valley and Servant of the Lake rate 4.8–4.9 on both stores. They earn reviews such as “I love that I can just buy it once” [G2].
2. **“Free start + one unlock” is now used by top-tier studios.** Monument Valley 3 charges $5.99 [A16] and Agent A charges $9.99 on iOS [A17]. Our price range ($3.99–$6.99) is in line.
3. **Short length is the most common complaint about premium titles** [G1][G16]. Chapters 1–3 at an estimated 30–60 min each (estimates and design targets, not measured; Chapter 4 is not designed yet) need clear messaging on the store page, for example “4 chapters”.
4. **Touch precision is a review killer** [G5]. Our tap maps and exact colliders (`docs/GAMEPLAY_QA.md`) address this, but only real-finger tests prove it.
5. **Walkthroughs are part of the genre.** Rusty Lake publishes its own [D4], and players openly rely on YouTube [G18]. See risk R3 in section 8.

---

## 3. Store economics (official sources)

### 3.1 Service fees
| Store | Standard rate | Reduced rate for small developers | Conditions | Src |
|---|---|---|---|---|
| **Apple App Store** | 30% of the price for paid apps and in-app purchases (Schedule 2, §3.4(a)) | **15%** through the App Store Small Business Program | Proceeds of no more than $1M in the previous calendar year *and* the current year, counted across all Associated Developer Accounts. You must enroll: be the Account Holder, accept the Paid Apps agreement, and list associated accounts. “If a participating developer surpasses the 1 million USD threshold in the current calendar year, the standard commission rate will apply to future sales.” | R3, R4 |
| **Google Play**: users in the EEA, UK and US (from 30 Jun 2026) and in Australia and Japan (from 30 Sep 2026) | Above $1M: 20% + 5% billing fee for “new installs”; 25% + 5% for “existing installs”. With the Play Games Level Up program: 15% + 5% and 20% + 5% | **First $1M (USD) of annual earnings: 10% + 5% billing fee**, i.e. 15% in total | A new-install/existing-install split by the date the user first installed. The billing fee applies to purchases through Google Play Billing | R1 |
| **Google Play**: all other markets (including Uzbekistan and Kazakhstan) | 30% on earnings above $1M | **15% for the first $1M** each calendar year | You must enroll in the 15% tier: a payments profile, an Account Group containing all associated accounts, and acceptance of the 15% terms in Play Console. It applies from the enrollment date. After $1M, “the service fee is 30% for all ADAs for the rest of the year” | R1, R2 |

**What this means for us:** every scenario in section 4 stays far below $1M. The highest is $349,500 gross. So the effective fee is **15% on both stores**, *provided both programs are enrolled before the first sale*. Without enrollment, Apple charges 30%.

### 3.2 Refunds
| | Google Play | Apple App Store |
|---|---|---|
| Who decides | Within 48 hours the user can request a refund from Google. “After 48 hours: Contact the developer” [R5]. A paid app can be returned “shortly after first buying it”, only once per app [R5]. Buyers can cancel a paid-app purchase within two hours [R7] | Apple. The user requests it at reportaproblem.apple.com and gets an update within 24–48 hours [R8] |
| Developer action | The developer can refund fully or partly in Play Console order management. “Google will return the service fee to you” [R6] | The developer cannot approve refunds; the decision is Apple's [R8] |
| Effect on payouts | Deducted from the next payout. A negative balance for 48 hours or more is debited from the bank account [R6] | Under Schedule 2, when Apple refunds, “You shall reimburse, or grant Apple a credit for, an amount equal to the price” [R4] |
| Public refund-rate benchmark | **Not found.** Section 4 uses an assumption | **Not found** |

### 3.3 VAT, GST and sales tax handled by the stores
- **Google Play** determines, charges and remits VAT for EU customers “for all developers”. It does the same for GST in Australia, for US sales tax in the listed states, and in many other countries, including Kazakhstan, Georgia and Türkiye [R9]. In the 87 countries it lists (my count), prices are shown **tax-inclusive** [R9].
- **Apple** collects and remits taxes in the regions listed in Exhibit B of Schedule 2. These include the US, the UK, EU states, Kazakhstan, Russia and Uzbekistan [R4].
- **The exception that affects us: sales to customers in Uzbekistan.**
  - Google: “If you're located in Uzbekistan, you're responsible for determining, charging, and remitting Uzbekistan Value Added Tax (VAT) for all Google Play Store paid app and in-app purchases made by customers in Uzbekistan.” For an individual or individual entrepreneur, “Google will apply local VAT on the service fee” [R9].
  - Apple: Uzbekistan is marked “Solely applicable to non-resident Developers. Apple shall not collect and remit taxes for local Developers” [R4].
- **US income-tax withholding.**
  - Apple's agreement requires non-US developers to complete Form W-8BEN (§15.1). Apple withholds when it believes tax is due, and applies treaty rates only with the treaty documentation (§3.7) [R4].
  - The IRS says Uzbekistan is covered by the 1973 US–USSR income-tax treaty [R15]. **Whether any US withholding applies to App Store proceeds, and which treaty article could be claimed, is not verified here.**
  - Google's withholding-tax page lists country rules (Brazil, Egypt, India and others) and nothing for Uzbekistan or for US withholding on app sales [R14]. Confirm in the Play Console payments profile.

### 3.4 Payout requirements
| | Google Play | Apple |
|---|---|---|
| Can an individual in Uzbekistan sell? | Yes. Uzbekistan supports developer *and* merchant registration, with USD as the default currency [R10] | Requires a Paid Apps Agreement, banking information and tax forms [R12]. The owner already has an Apple Developer account (`DEVELOPMENT_STATUS.md`). **Whether a Uzbek bank account is accepted was not verified:** check App Store Connect → Business |
| How paid | Wire transfer in USD. Uzbekistan is on the wire-transfer list [R11] | EFT or direct deposit; Apple prefers low-value transfers to wires [R12] |
| Minimum | **US$100** for USD wire payouts [R7][R11] | **40 USD** for any bank country not in Apple's table; Uzbekistan is not listed [R13] |
| Timing | Orders from a calendar month are paid “around the 15th of the following month” [R7] | “within 45 days of the last day of the fiscal month” [R12] |
| Fees | Bank wire fees “may range from US$0 to US$50 or more” [R11] | “Payments may be subject to bank fees” [R12] |
| Accounts | One-time US$25 registration fee [R31] | US$99 per year [R30] |

### 3.5 Being an individual developer in Uzbekistan: confirm with a local tax adviser
Do not act on this list without professional advice. These are the questions; the stated facts are the public starting points.

| # | Question for the adviser | What public sources say |
|---|---|---|
| 1 | Should I sell as an individual, an individual entrepreneur or an LLC? | Google treats an “Individual or Individual Entrepreneur” differently from a “Business organization” for Uzbek VAT [R9]. PwC: “From 1 January 2026, the fixed PIT regime for individual entrepreneurs was abolished” [T4] |
| 2 | How is my store income taxed? | PwC: residents are taxed on worldwide income, and the standard personal income tax rate is 12% [T4]. Residents with income from outside Uzbekistan must file a return by 1 April of the following year and pay by 1 June [T5] |
| 3 | Do I owe Uzbek VAT on sales to Uzbek players, and must I register? | Both stores say the local developer is responsible (section 3.3). PwC: the VAT rate is 12%; registration is mandatory above a turnover of 12,000 BCU [T6]. The BCU value in USD is not verified here |
| 4 | Can I reclaim or offset the Uzbek VAT Google adds to its service fee? | Google applies it to individuals [R9]. Not verified |
| 5 | Is IT Park residency available to me, and is it worth it? | IT Park's own article (7 Jan 2026) lists benefits for “member companies”: exemption from corporate income tax, VAT, social tax and turnover tax until 1 January 2028, and 7.5% PIT for employees [T7]. **Whether an individual or individual entrepreneur can join could not be verified from a primary source** |
| 6 | Which W-8BEN entries are correct (treaty claim or none)? | Section 3.3 |
| 7 | What bank documents are needed to receive USD wires from Google and transfers from Apple? | Not verified |
| 8 | What records must I keep? | Keep every monthly store earnings report and bank statement (my recommendation) |

---

## 4. Revenue scenarios

### 4.1 Assumptions (all mine unless a source is given)
| # | Input | Value | Basis |
|---|---|---|---|
| A1 | **Players** | People who *start* Chapter 1 in a country where they can pay | This is not downloads, and not monthly active users |
| A2 | **Conversion** | Share of A1 who buy the Chapters 2–4 bundle over the game's life | See 4.4 for benchmarks |
| A3 | **Price** | Consumer price in USD: $3.99, $4.99 or $6.99 | Stores convert to local prices |
| A4 | **Store-collected taxes** | **10% of gross** (blended) | Assumption. In tax-inclusive markets VAT sits inside the price (20% VAT is 16.7% of the price); in the US, sales tax is added on top [R9]. A mix of about 60% tax-inclusive sales gives about 10% |
| A5 | **Store fee** | **15%** of the tax-exclusive price | Requires enrollment in both programs (3.1) |
| A6 | **Refund allowance** | **2%** of proceeds | Assumption. No public refund-rate benchmark was found |
| A7 | **Fixed costs per year** | **$1,300** | Assumption. Apple $99 [R30]; wire and bank fees about $360 (12 × $30, inside Google's $0–$50 range [R11]); Apple bank fees about $360 (assumption); about $500 for a local accountant (assumption, unverified). The Google $25 is already paid |
| A8 | **Marketing cash** | **$0** | The plan in section 5. Owner time is not costed |
| A9 | Order of deductions | Taxes first, then the fee on the tax-exclusive amount, then refunds, then costs | How the stores calculate; columns are shown in the order requested |

**Proceeds per sale (calculation):** $3.99 → **$2.99** · $4.99 → **$3.74** · $6.99 → **$5.24**.
**Break-even (calculation):** about 348 buyers at $4.99 cover the $1,300 fixed costs.

### 4.2 Net before income tax: all combinations (calculation)
| Ch1 players | Conversion | Buyers | Net @ $3.99 | Net @ $4.99 | Net @ $6.99 |
|---|---|---|---|---|---|
| 10,000 | 1% | 100 | −$1,001 | −$926 | −$776 |
| 10,000 | 2% | 200 | −$702 | −$552 | −$252 |
| 10,000 | 3% | 300 | −$403 | −$178 | $272 |
| 10,000 | 5% | 500 | $196 | $571 | $1,320 |
| 100,000 | 1% | 1,000 | $1,691 | $2,441 | $3,940 |
| 100,000 | 2% | 2,000 | $4,683 | $6,182 | $9,181 |
| 100,000 | 3% | 3,000 | $7,674 | $9,923 | $14,421 |
| 100,000 | 5% | 5,000 | $13,657 | $17,405 | $24,902 |
| 500,000 | 1% | 5,000 | $13,657 | $17,405 | $24,902 |
| 500,000 | 2% | 10,000 | $28,613 | $36,110 | $51,104 |
| 500,000 | 3% | 15,000 | $43,570 | $54,815 | $77,306 |
| 500,000 | 5% | 25,000 | $73,483 | $92,225 | $129,710 |
| 1,000,000 | 1% | 10,000 | $28,613 | $36,110 | $51,104 |
| 1,000,000 | 2% | 20,000 | $58,526 | $73,520 | $103,508 |
| 1,000,000 | 3% | 30,000 | $88,439 | $110,930 | $155,912 |
| 1,000,000 | 5% | 50,000 | $148,265 | $185,750 | $260,720 |

### 4.3 Full waterfall at $4.99 (calculation)
| Ch1 players | Conv. | Buyers | Gross | − Store fee (15%) | − Store taxes (10%) | − Refunds (2%) | = Proceeds | − Costs | = Net before income tax |
|---|---|---|---|---|---|---|---|---|---|
| 10,000 | 1% | 100 | $499 | $67 | $50 | $8 | $374 | $1,300 | −$926 |
| 10,000 | 2% | 200 | $998 | $135 | $100 | $15 | $748 | $1,300 | −$552 |
| 10,000 | 3% | 300 | $1,497 | $202 | $150 | $23 | $1,122 | $1,300 | −$178 |
| 10,000 | 5% | 500 | $2,495 | $337 | $250 | $38 | $1,871 | $1,300 | $571 |
| 100,000 | 1% | 1,000 | $4,990 | $674 | $499 | $76 | $3,741 | $1,300 | $2,441 |
| 100,000 | 2% | 2,000 | $9,980 | $1,347 | $998 | $153 | $7,482 | $1,300 | $6,182 |
| 100,000 | 3% | 3,000 | $14,970 | $2,021 | $1,497 | $229 | $11,223 | $1,300 | $9,923 |
| 100,000 | 5% | 5,000 | $24,950 | $3,368 | $2,495 | $382 | $18,705 | $1,300 | $17,405 |
| 500,000 | 1% | 5,000 | $24,950 | $3,368 | $2,495 | $382 | $18,705 | $1,300 | $17,405 |
| 500,000 | 2% | 10,000 | $49,900 | $6,736 | $4,990 | $763 | $37,410 | $1,300 | $36,110 |
| 500,000 | 3% | 15,000 | $74,850 | $10,105 | $7,485 | $1,145 | $56,115 | $1,300 | $54,815 |
| 500,000 | 5% | 25,000 | $124,750 | $16,841 | $12,475 | $1,909 | $93,525 | $1,300 | $92,225 |
| 1,000,000 | 1% | 10,000 | $49,900 | $6,736 | $4,990 | $763 | $37,410 | $1,300 | $36,110 |
| 1,000,000 | 2% | 20,000 | $99,800 | $13,473 | $9,980 | $1,527 | $74,820 | $1,300 | $73,520 |
| 1,000,000 | 3% | 30,000 | $149,700 | $20,210 | $14,970 | $2,290 | $112,230 | $1,300 | $110,930 |
| 1,000,000 | 5% | 50,000 | $249,500 | $33,682 | $24,950 | $3,817 | $187,050 | $1,300 | $185,750 |

### 4.4 Which conversion rates are realistic?
**No reliable industry benchmark for “free first chapter → paid unlock” conversion was found.** The two public data points are:

| Case | Model and price | Reported conversion | Type of source |
|---|---|---|---|
| Gasketball (Mikengreg, 2012) | Free download, one $2.99 unlock | “conversion rate is currently at 0.67%”, about 200,000 downloads | Developer-stated, via NBC News [D8] |
| Super Mario Run (Nintendo, 2017) | Free start, one unlock (C$13.99 equivalent) | “more than five percent of players” paid, 78 million downloads | Press-reported, citing the Wall Street Journal; Nintendo gave revenue of $53M [D7] |

How to read the grid with these:
- **1%: pessimistic.** Plausible for an unknown indie, but Gasketball shows it can be lower (0.67%).
- **2–3%: realistic target.** This holds only if Chapter 1 ends on a strong hook (the echo turning, the 1979 postmark) and the purchase screen is clear. It is an assumption; no benchmark supports it directly.
- **5%: optimistic.** That is the level of a game built on a world-famous brand [D7].

Two structural caveats make the *effective* rate lower:
1. **Russia.** Google Play has paused billing for users in Russia since 10 March 2022, and paid apps cannot be downloaded there [R16]. Apple: “As of April 1, 2026 … payment for Apple subscriptions and digital purchases is no longer available in Russia from mobile phone accounts”; only an existing balance can be spent [R17]. Russian-speaking players *inside Russia* will mostly not be able to pay.
2. **Uzbekistan.** Google's “Paid app availability” list includes Uzbekistan [R18]. That same list still includes Russia, which contradicts R16, so it is not reliable alone. **Whether Uzbek bank cards can pay on Google Play and the App Store was not verified.** Check this with real purchases before launch.

---

## 5. Launch and marketing plan with a $0 budget
Effort figures are my estimates for one person.

### 5.1 Store page optimisation (ASO): 2–3 days, then 1 hour per week
| Field | Limit (official) | Our action |
|---|---|---|
| Name | 30 characters on Play [R25] and on the App Store [R26] | “Mystery Room: Lost Institute” (28 characters; already chosen in `docs/store/`). Keep the full in-game title |
| Play short description | 80 characters [R25] | Existing EN/RU/UZ drafts in `docs/STORE_LISTING.md` fit |
| App Store subtitle | 30 characters [R26] | For example “3D escape room mystery” (22 characters) and its RU/UZ versions |
| App Store keywords | “up to 100 bytes”; “Names of other apps or companies aren't allowed” [R27] | Use genre words (escape room, 3D puzzle, mystery, detective, offline). RU keywords use Cyrillic, which takes 2 bytes per letter in UTF-8, so about 50 letters fit (my calculation). **Never use “The Room” or other titles** |
| Description | 4,000 characters (both stores) [R25][R27] | Lead with “Chapters 1–2 free · one purchase unlocks Chapters 3–4 · no ads · offline · EN/RU/UZ”. Say how many chapters there are, which answers the “too short” complaint (2c) |
| App Store promotional text | 170 characters, editable without a new build [R27] | Use it for launch and chapter news |
| Screenshots and previews | Up to 3 app previews per localization and device size [R27] | Real captures from a phone (the dev container uses a software renderer). Show the WOW beats from `docs/DESIGN_PILLARS.md` §3: power returns, the bookcase swing, the Lumen beam, Leyla's echo |
| Featuring | Apple: nominate in App Store Connect → Featuring → Nominations, at least 3 weeks ahead. “App Launch” is a nomination type; nothing is guaranteed [R28] | Nominate the Ch1 launch and the Ch2 release |

### 5.2 A trailer from real gameplay: 3–5 days
- 30–45 s, landscape, captured on a real phone. Built in this order:
  1. 0–3 s: the door slams.
  2. The UV ink blooms.
  3. Power returns.
  4. The bookcase opens.
  5. The beam paints the emblem.
  6. Leyla turns.
  7. End card: “Chapter 1 free”.
- No fake footage and no UI that is not in the game.
- Make three cuts (EN, RU, UZ captions) from one edit. Reuse it as the app preview, the YouTube video, TikTok/Shorts clips (9:16 crops) and the press-kit video.

### 5.3 Press kit: 1–2 days
- **Where:** one free web page (Google Sites already hosts the privacy policy) or a GitHub Pages site.
- **Contents:**
  - a fact sheet: developer, location, platforms, release date, price model, languages;
  - a 100-word and a 300-word description;
  - 8–10 screenshots;
  - the trailer;
  - the logo and icon;
  - the story hook;
  - contact details.
- **Promo access:** prepare store promo codes for press and creators. Check the current quotas in each console; they are not verified here.

### 5.4 Communities and creators: 4–6 hours per week, ongoing
| Channel | Concrete action | Honest note |
|---|---|---|
| Reddit | Development posts with a GIF of one mechanism (the Lumen beam). Post in subreddits about puzzle and indie games, and in Android and iOS gaming subreddits | Read each subreddit's self-promotion rules first. Pure ads get removed. Expect a few hundred visitors from a good post, not thousands (my estimate) |
| Discord | One small server: #announcements, #hints (spoiler tags), #bugs, #ru, #uz | It is only worth it once there are 50+ players. Moderation takes time |
| TikTok / YouTube Shorts | 1–2 clips per week, 10–20 s each, one “WOW” beat per clip | Free, but slow to build. Consistency matters more than polish |
| YouTube creators (walkthrough culture) | Send a short personal email with a promo code to small and mid-size creators who play mobile escape games. **Publish our own “how it works” guide videos**, as Rusty Lake does [D4] | With per-game variant codes (section 8, R3) a walkthrough teaches the method, not the answers, so creators help discovery without killing the purchase |
| Store reviews | Ask once, after Chapter 1 is completed, never mid-puzzle | Use the platforms' native review prompts |

### 5.5 Uzbek and Russian-speaking communities: 2–3 hours per week
- **The Uzbek language is our edge.** Among the 13 comparable App Store listings I checked, none lists Uzbek (iTunes Lookup data [A0]; calculation).
- **Uzbek channels:** pitch local tech and gaming media, and Telegram channels and groups. Present at universities and IT Park events. Offer a Uzbek-language demo session.
- **Russian-speaking channels:** focus on countries where players *can* pay (for example Kazakhstan [R9]). Remember the Russia billing block (4.4).
- **Native reviewers** of the RU and UZ text can be recruited in the same communities (section 6).

### 5.6 Festivals and showcases with free entry (verified)
| Event | Entry | Fit | Src |
|---|---|---|---|
| DevGAMM Awards | “Submitting your game is free”. PC or mobile. Unreleased, or released after 7 Sep 2025. The 2026 deadline (7 Sep 2026) has **passed**. Showcase participants must buy a ticket | Target the 2027 edition with Ch1 + Ch2 | E1 |
| Game Development World Championship (GDWC) | “No participation or acceptance fees”. Has a mobile category. Games in development need a playable build | Good for a first jury opinion | E2, E3 |
| Pocket Gamer “Big Indie Pitch” (Montréal, 10 Nov 2026) | No pitch fee stated; attendance “FREE (MIGS ticket required)”. Teams of up to 12. Entries close 27 Oct 2026 | In-person only, so travel costs apply. Watch for future online or regional editions | E4 |
| Apple featuring nomination | Free, inside App Store Connect | Every launch and chapter release | R28 |

Not verified, and worth checking: the Google Play Indie Games Festival (country eligibility), Independent Games Festival (fees), regional CIS events.

### 5.7 Timeline (T = public launch of Chapter 1)
| When | Do |
|---|---|
| T − 10 weeks | Test plan waves 0–1 (section 6). Fix what they show |
| T − 8 weeks | Press kit page, trailer v1, store listings in EN/RU/UZ |
| T − 6 weeks | Closed test of 50–300 players (section 6). Start Shorts and TikTok |
| T − 3 weeks | Apple featuring nomination. Creator emails with promo codes. Uzbek media pitch |
| T | Launch on both stores. Reddit development post. Discord opens |
| T + 1 to 4 weeks | Answer every review. Fix the top crash and the top drop-off point. Announce the Chapter 2 date |

---

## 6. Test plan for the first 100–1,000 real players

### 6.1 Recruiting
| Track | Official limits | Use |
|---|---|---|
| Google Play internal testing | Up to 100 testers per app; builds can bypass full review [R20]. Internal-only tracks are exempt from the Data safety section [R23] | Waves 0–1: friends, family, first volunteers |
| Google Play closed testing | Email lists (up to 200 lists of up to 2,000 users each) or Google Groups (no size limit); testers can send private feedback [R20] | Waves 2–3 |
| **Production gate (Play)** | Personal developer accounts created after 13 Nov 2023 must run a closed test with “a minimum of 12 testers who have been opted in continuously for at least 14 days” before applying for production [R19] | Plan at least 15–20 testers as a buffer (my recommendation). Check the owner's account type and creation date |
| TestFlight (iOS) | Up to 100 internal and **10,000 external** testers, by email or public link. The first external build needs Beta App Review. A build can be tested “for up to 90 days”. Testers can send screenshots and crash feedback [R21][R22] | Waves 1–3 on iOS |

**Where to find testers:**
- people the owner knows;
- Uzbek universities and IT Park;
- Telegram groups;
- escape-room and puzzle subreddits (check their rules);
- the Discord server.

Aim for a mix of languages and devices, including at least five low- and mid-range Android phones.

**Waves:**
| Wave | Size | Goal | Gate to the next wave |
|---|---|---|---|
| 0 | 5–8 in person | Think-aloud sessions (6.4) | No blocker in the first 10 minutes |
| 1 | 20–50 | Crashes, devices, brightness, text size | Crash-free on the test devices; text readable |
| 2 | 100–300 | Funnel and stuck points (section 7) | Ch1 completion and drop-off within working targets |
| 3 | up to 1,000 | Purchase intent by price, RU/UZ quality | Decision checklist (section 9) |

### 6.2 What to observe
These come straight from the open questions in `docs/GAMEPLAY_QA.md`:
1. **The first 30 seconds.** Do players understand “drag to look, tap to examine” from the caption alone, and do they find the desk first?
2. **The first drawer:** do testers make the 03:17 → 0317 deduction without hints?
3. **The unpowered lab at 50% screen brightness:** readable, and still moody?
4. **The mirror puzzle:** is the 45° click clear?
5. **Small controls** with a real finger: the drawer wheels and the radio knob.
6. **Dry spells** of more than 5 minutes without progress.
7. **Text size.** The owner already reports small text on phones (`docs/QUALITY_REPORT.md`).
8. **Device performance:** heat, stutter, load time and crashes.
9. **RU/UZ wording** that sounds unnatural.
10. **Reaction to the purchase screen** after Chapter 1.

### 6.3 Short survey (Google Forms, EN/RU/UZ, anonymous, under 3 minutes)
1. Language you played in (EN / RU / UZ).
2. Phone model (optional).
3. How far did you get? (a list of the 12 Ch1 puzzles, plus “Finished Chapter 1”).
4. **Fun:** 1–5.
5. **Clarity:** “I usually knew what to try next”, 1–5.
6. **Where were you stuck longest?** (the puzzle list, plus free text).
7. Hints: “Did the hints help without spoiling?” 1–5.
8. Readability: text size (too small / OK / too large); darkness (too dark / OK).
9. **“Would you buy Chapters 2–4 for $X?”** Definitely / probably / not sure / probably not / definitely not.
   - Give each tester group a different X: $3.99, $4.99 or $6.99.
   - Stated intent usually runs higher than real buying, so read it as a *ranking* of prices, not a forecast.
10. What would make you more likely to buy? (free text).
11. Bugs or anything confusing? (free text).

Do not ask for names, e-mails or phone numbers. Add a one-line privacy note at the top of the form.

### 6.4 How to run think-aloud sessions
1. **Setup:** 45–60 minutes, one player, the player's own phone if possible, a quiet room. Record the screen and voice only after **written consent**.
2. **Script:** “Please play as you would at home and say out loud what you notice, think and try. I can't help you; there are no wrong answers. We are testing the game, not you.”
3. **The facilitator:** stays silent and does not point. If the player is silent for 30 seconds, ask only “What are you thinking now?”. After 5 minutes stuck, suggest the in-game hint button.
4. **Notes template:** per minute, note *what the player tried*, *what they expected*, *what happened*, *emotion* (smile, sigh, “wow”). Record the exact quotes.
5. **Debrief:** 5 minutes. Ask: the best moment, the worst moment, and whether they would pay to continue and at what price.
6. **Synthesis:** after 5–8 sessions, list the problems seen by 2 or more players. Fix those first.

---

## 7. Metrics, measured privacy-first

### 7.1 What to measure
| Metric | Definition | Where it comes from |
|---|---|---|
| Started Ch1 | The intro finished, first control used | Local event log (7.2) |
| First puzzle solved | The drawer (P1) opened | Local event log |
| Ch1 completed | The finale choice made | Local event log |
| Drop-off by puzzle | The furthest puzzle reached by players who stopped | Local summary |
| Session time / total time | Minutes per session; total minutes to finish Ch1 (bucketed) | Local summary |
| Hints used | Count per puzzle and per level (1/2/3) | Local summary |
| Ratings | Store rating and review text | Play Console and App Store Connect (no in-app code needed) |
| Purchase intent | Survey question 9 | Survey (6.3) |
| Purchase conversion | Buyers ÷ Ch1 starters | Buyers from the store sales reports; starters from opt-in summaries or the test waves. A ratio, never per person |

**Working targets** (my assumptions, with no external benchmark):
- at least 85% of starters solve P1;
- at least 50% complete Ch1;
- no single puzzle loses more than 15% of the players who reach it;
- the median Ch1 time is 35–60 min.

### 7.2 How to measure it privacy-first
**Current state, stated clearly:**
- The public privacy policy says: “The game does not collect, store on any server, sell or share any personal information”, and that there are “no advertising, no analytics and no third-party tracking SDKs”. The game “does not send data over the internet” [R32].
- The Play Data safety answer was prepared as “No” collection (`docs/store/PLAY_VA_APPSTORE_QOLLANMA.txt`).

**Any analytics that sends data off the phone requires, before release:**
1. an updated privacy policy;
2. a consent UI;
3. updated Data safety and App Store privacy answers.

**Phase A: the test waves, with zero network**
- The game writes a tiny local summary to `user://`:
  - the furthest puzzle;
  - minutes, in buckets;
  - hints per puzzle and level;
  - the language;
  - the app version.
- No IDs, no device identifiers, no free text.
- A **“Copy my stats”** button in Settings puts a short code on the clipboard. The tester pastes it into the survey (6.3) *if they choose to*.
- The app itself transmits nothing. In my reading of both stores' definitions (below), that keeps the app's answer at “no data collected”. Confirm this when filling the forms. The survey form needs its own privacy note.

**Phase B: after launch, only if needed (opt-in upload)**
- **Off by default.** A clear consent screen in EN/RU/UZ saying what is sent and why. A “View data” button. The choice can be changed in Settings at any time.
- **What is sent:** one anonymous summary per upload, with no install ID and no advertising or device IDs. The data is stored on the phone first and sent only when online *and* opted in.
- **Server:** configure the server not to store IP addresses.
- **No third-party analytics SDK.** That keeps “shared” at “No”.

**What Phase B means for the store forms:**
| | Google Play Data safety | App Store privacy “nutrition label” |
|---|---|---|
| What counts as collection | “‘Collect’ means transmitting data from your app off a user's device”; this includes SDKs [R23] | “transmitting data off the device in a way that allows you … to access it for a period longer than what is necessary to service the transmitted request in real time”. “Data that is processed only on device is not ‘collected’” [R24] |
| Phase A | Nothing transmitted, so nothing collected | Nothing transmitted, so nothing collected |
| Phase B data types | App activity → “App interactions” / “Other actions”; App info and performance → “Diagnostics” (and “Crash logs” if sent) [R23] | “Product Interaction”, “Gameplay Content”, “Performance Data”, “Crash Data” [R24] |
| Optional? | Can be declared “optional” only if all users can opt in or out [R23] | The “optional disclosure” exemption does **not** fit. It requires, among other things, that the user's name is shown in the submission form and that the user provides the data each time [R24]. **So it must be disclosed**, as “not linked to you” only if direct identifiers are stripped and never re-linked |
| Anonymity | The “Anonymous data” exemption applies only to *sharing*, not to collection [R23] | — |

---

## 8. Risks and mitigations
| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 | **Discoverability**: no budget, no brand | Genre leaders rely on featuring and word of mouth [D1][D2]; Rusty Lake built a free-game community first [D3] | Section 5. The free Ch1 *is* the marketing. Apple featuring nominations [R28]; UZ/RU niche (5.5); festivals (5.6); our own walkthrough videos |
| R2 | **Piracy**: Ch2–4 ship inside the same package, so a modified APK could unlock them | `docs/MONETIZATION.md` | Server-side or platform purchase validation with a signed entitlement cache (already planned). Do not spend weeks on anti-piracy; protect the purchase path and move on |
| R3 | **YouTube walkthroughs replace buying** | Players openly use them [G18]; Rusty Lake even posts its own [D4] | Per-game variant answers (`docs/VARIANTS.md`):<br>• Ch1: the gear box, safe cipher and beacon already vary per game (`docs/QUALITY_REPORT.md`, `lab7_logic.gd`). The drawer 03:17 and the shadow emblem are fixed story anchors, so the first answer is public, which is acceptable for a free tutorial puzzle.<br>• Ch2: valves, punch card, tape clicks/dial, splice order, focus and vault vary.<br>• Ch3: designed with variants from the start.<br>Make our own “how it works” videos that never show a final code |
| R4 | **Device performance** | Ch1: ~175–183k primitives against a 150k target. Ch2 hall: 216 draw calls and ~161k primitives against 150/150k. **No FPS measured on a phone**; the debug APK is 123 MB (`DEVELOPMENT_STATUS.md`, `docs/QUALITY_REPORT.md`, `docs/RELEASE_PIPELINE.md`) | The planned LOD and shadow-caster pass. Test on 5+ low and mid-range Android phones in wave 1. PerfGuard resolution scaling. List the minimum devices on the store page |
| R5 | **Localisation quality** | No native-speaker review yet (`docs/QUALITY_REPORT.md`) | Two native reviewers each for RU and UZ in waves 1–2. A glossary of names and terms. Solutions are language-neutral, so translation cannot break a puzzle |
| R6 | **Players who cannot pay** | Russia: Play billing paused, Apple carrier billing ended [R16][R17]. UZ card acceptance unverified | Test real purchases from Uzbekistan and Kazakhstan before launch. Do not forecast revenue from Russia |
| R7 | **Tax and compliance** | Local VAT responsibility for UZ sales [R4][R9] | The section 3.5 questions answered by an adviser *before* payments go live |
| R8 | **“Too short” and “touch too fiddly” reviews** | Common in the genre [G1][G5][G16] | State “4 chapters” on the listing; real-finger tap tests; the brightness and text-size settings |
| R9 | **Production access delayed** | The 12-tester, 14-day rule for new personal Play accounts [R19] | Start the closed test early (6.1) |

---

## 9. Decision checklist before turning on real payments
**Product**
- [ ] Chapter 1 has been HUMAN TESTED by at least 100 players (wave 2) with no blocker. Ch1 completion and drop-off are within the working targets (7.1).
- [ ] At least Chapter 2 is released (`released: true`) and has passed its own player review. Chapters 3–4 have a public, honest schedule: the listing must not promise content that does not exist.
- [ ] Text size and dark-scene readability are fixed and confirmed on real phones.
- [ ] FPS has been measured on at least 3 low and mid-range Android phones and 1 older iPhone.

**Store setup**
- [ ] Enrolled in the Apple Small Business Program [R3] and the Google Play 15% tier [R2].
- [ ] Paid Apps Agreement accepted, Apple banking and tax forms complete [R12]. Google payments profile with a USD-capable bank account [R10][R11].
- [ ] Non-consumable `full_game` created on both stores. Price chosen (decision recorded). Regional prices reviewed.
- [ ] Production access granted on Google Play [R19].

**Tax and legal** (with a local adviser, section 3.5)
- [ ] Legal form chosen: individual, individual entrepreneur or LLC.
- [ ] Uzbek VAT duty on Uzbek sales answered [R4][R9]; registration done if required.
- [ ] W-8BEN completed correctly [R4].
- [ ] A process for keeping monthly records and filing the annual return (1 April) [T5].

**Technology** (`docs/MONETIZATION.md`)
- [ ] GodotGooglePlayBilling and StoreKit 2 providers implemented. Purchase validation and a signed entitlement cache.
- [ ] **Restore purchases** works on a fresh install on both platforms.
- [ ] Tested with Play license testers and Apple Sandbox accounts:
  - purchase;
  - cancel;
  - pending payment;
  - refund (Google [R6]);
  - offline after purchase.
- [ ] At least one real purchase from Uzbekistan on each store (R6).
- [ ] `REAL_PAYMENTS_ENABLED = true` only in the release build that passed all of the above.

**Listing and privacy**
- [ ] The listing says exactly what is free and what is paid: “The first two chapters are free · one purchase unlocks Chapters 3–4”.
- [ ] Privacy policy, Data safety and App privacy answers match the shipped build (section 7). If any analytics ships, all three are updated first.
- [ ] A support contact and a refund FAQ are on the press and support page.

---

## Sources
All sources accessed **2026-10-09**. G = Google Play listing; A = App Store listing; R = official store or authority rules; D = developer or press report; T = third-party; E = event page.

| ID | Source | URL |
|---|---|---|
| G1 | The Room — Google Play | https://play.google.com/store/apps/details?id=com.FireproofStudios.TheRoom |
| G2 | The Room Two — Google Play | https://play.google.com/store/apps/details?id=com.FireproofStudios.TheRoom2 |
| G3 | The Room Three — Google Play | https://play.google.com/store/apps/details?id=com.FireproofStudios.TheRoom3 |
| G4 | The Room: Old Sins — Google Play | https://play.google.com/store/apps/details?id=com.FireproofStudios.TheRoom4 |
| G5 | The House of Da Vinci — Google Play | https://play.google.com/store/apps/details?id=com.bluebraingames.thehouseofdavinci |
| G6 | The House of Da Vinci 2 — Google Play | https://play.google.com/store/apps/details?id=com.bluebraingames.houseofdavinci2 |
| G7 | The House of Da Vinci 2 Lite — Google Play | https://play.google.com/store/apps/details?id=com.bluebraingames.thehouseofdavinci2.demo |
| G8 | The House of Da Vinci 3 — Google Play | https://play.google.com/store/apps/details?id=com.bluebraingames.thehouseofdavinci3 |
| G9 | Cube Escape Collection — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.CubeEscapeCollection |
| G10 | Cube Escape: Seasons — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.CubeEscapeSeasons |
| G11 | Rusty Lake Hotel — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.RustyLakeHotel |
| G12 | Rusty Lake: Roots — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.RustyLakeRoots |
| G13 | Rusty Lake Paradise — Google Play | https://play.google.com/store/apps/details?id=air.com.RustyLake.RustyLakeParadise |
| G14 | Servant of the Lake — Google Play | https://play.google.com/store/apps/details?id=com.RustyLake.ServantOfTheLake |
| G15 | Servant of the Lake Lite — Google Play | https://play.google.com/store/apps/details?id=com.RustyLake.ServantOfTheLakeLite |
| G16 | Monument Valley — Google Play | https://play.google.com/store/apps/details?id=com.ustwo.monumentvalley |
| G17 | Monument Valley 2 — Google Play | https://play.google.com/store/apps/details?id=com.ustwo.monumentvalley2 |
| G18 | Agent A — Google Play | https://play.google.com/store/apps/details?id=co.yakand.agentaapuzzleindisguise |
| G19 | Tiny Room Stories: Town Mystery — Google Play | https://play.google.com/store/apps/details?id=com.kiarygames.tinyroom |
| G20 | Doors: Awakening — Google Play | https://play.google.com/store/apps/details?id=com.snapbreak.doors |
| A0 | Apple iTunes Lookup API (exact rating counts and language lists for the listings below) | https://itunes.apple.com/lookup?id=552039496,1286676015,1062515791,1469235524,6443563379,940006911,1555267021,6748751735,1459520173,1419796608,1583536868,1089890170,1483451514&country=us |
| A1 | The Room — App Store | https://apps.apple.com/us/app/the-room/id552039496 |
| A2 | The Room Two — App Store | https://apps.apple.com/us/app/the-room-two/id667362389 |
| A3 | The Room Three — App Store | https://apps.apple.com/us/app/the-room-three/id918054748 |
| A4 | The Room: Old Sins — App Store | https://apps.apple.com/us/app/the-room-old-sins/id1286676015 |
| A5 | The House of Da Vinci — App Store | https://apps.apple.com/us/app/the-house-of-da-vinci/id1062515791 |
| A6 | The House of Da Vinci 2 — App Store | https://apps.apple.com/us/app/the-house-of-da-vinci-2/id1331393380 |
| A7 | The House of Da Vinci 3 — App Store | https://apps.apple.com/us/app/the-house-of-da-vinci-3/id1469235524 |
| A8 | Cube Escape Collection — App Store | https://apps.apple.com/us/app/cube-escape-collection/id1555267021 |
| A9 | Cube Escape: Seasons — App Store | https://apps.apple.com/us/app/cube-escape-seasons/id979777165 |
| A10 | Rusty Lake Hotel — App Store | https://apps.apple.com/us/app/rusty-lake-hotel/id1059911569 |
| A11 | Rusty Lake: Roots — App Store | https://apps.apple.com/us/app/rusty-lake-roots/id1142016085 |
| A12 | Rusty Lake Paradise — App Store | https://apps.apple.com/us/app/rusty-lake-paradise/id1253855339 |
| A13 | Servant of the Lake — App Store | https://apps.apple.com/us/app/servant-of-the-lake/id6748751735 |
| A14 | Monument Valley — App Store | https://apps.apple.com/us/app/monument-valley/id728293409 |
| A15 | Monument Valley 2 — App Store | https://apps.apple.com/us/app/monument-valley-2/id1187265767 |
| A16 | Monument Valley 3 — App Store | https://apps.apple.com/us/app/monument-valley-3/id6443563379 |
| A17 | Agent A — App Store | https://apps.apple.com/us/app/agent-a-a-puzzle-in-disguise/id940006911 |
| A18 | Tiny Room Story: Town Mystery — App Store | https://apps.apple.com/us/app/tiny-room-story-town-mystery/id1459520173 |
| A19 | Doors: Awakening — App Store | https://apps.apple.com/us/app/doors-awakening/id1483451514 |
| R1 | Google Play — Service fees | https://support.google.com/googleplay/android-developer/answer/112622 |
| R2 | Google Play — 15% service fee tier enrollment | https://support.google.com/googleplay/android-developer/answer/10632485 |
| R3 | Apple — App Store Small Business Program | https://developer.apple.com/app-store/small-business-program/ |
| R4 | Apple Developer Program License Agreement, incl. Schedule 2 (§3.4, §3.7, §6.3, §15.1) and Exhibit B | https://developer.apple.com/support/terms/apple-developer-program-license-agreement/ |
| R5 | Google Play — Apps, games & in-app purchases refund policies | https://support.google.com/googleplay/answer/15574908 |
| R6 | Google Play Console — Refunds | https://support.google.com/googleplay/android-developer/answer/2741495 |
| R7 | Google Play Console — Order processing and payouts | https://support.google.com/googleplay/android-developer/answer/137997 |
| R8 | Apple — Request a refund | https://support.apple.com/en-us/118223 |
| R9 | Google Play Console — Tax rates and VAT | https://support.google.com/googleplay/android-developer/answer/138000 |
| R10 | Google Play Console — Supported locations for developer and merchant registration | https://support.google.com/googleplay/android-developer/answer/9306917 |
| R11 | Google Play Console — Wire transfer payouts | https://support.google.com/googleplay/android-developer/answer/2700656 |
| R12 | App Store Connect — Overview of receiving payments | https://developer.apple.com/help/app-store-connect/getting-paid/overview-of-receiving-payments |
| R13 | App Store Connect — Minimum payment threshold | https://developer.apple.com/help/app-store-connect/reference/minimum-payment-threshold |
| R14 | Google Play Console — Withholding tax | https://support.google.com/googleplay/android-developer/answer/9384608 |
| R15 | IRS — Uzbekistan tax treaty documents | https://www.irs.gov/businesses/international-businesses/uzbekistan-tax-treaty-documents |
| R16 | Google Play Console — Changes to billing for users in Russia and Belarus | https://support.google.com/googleplay/android-developer/answer/11950272 |
| R17 | Apple — Billing for digital purchases in Russia | https://support.apple.com/en-us/126891 |
| R18 | Google Play — Paid app availability | https://support.google.com/googleplay/answer/143779 |
| R19 | Google Play Console — Testing requirements for new personal developer accounts | https://support.google.com/googleplay/android-developer/answer/14151465 |
| R20 | Google Play Console — Set up an open, closed or internal test | https://support.google.com/googleplay/android-developer/answer/9845334 |
| R21 | Apple — TestFlight | https://developer.apple.com/testflight/ |
| R22 | App Store Connect — TestFlight overview | https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview |
| R23 | Google Play Console — Data safety section | https://support.google.com/googleplay/android-developer/answer/10787469 |
| R24 | Apple — App privacy details | https://developer.apple.com/app-store/app-privacy-details/ |
| R25 | Google Play Console — Create and set up your app (listing limits) | https://support.google.com/googleplay/android-developer/answer/9859152 |
| R26 | App Store Connect — App information | https://developer.apple.com/help/app-store-connect/reference/app-information/app-information |
| R27 | App Store Connect — Platform version information | https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information |
| R28 | App Store Connect — Nominate your app for featuring | https://developer.apple.com/help/app-store-connect/manage-featuring-nominations/nominate-your-app-for-featuring |
| R29 | Google Play Console — Free trial for paid games | https://support.google.com/googleplay/android-developer/answer/16923846 |
| R30 | Apple Developer Program (US$99 per year) | https://developer.apple.com/programs/ |
| R31 | Google Play Console — Developer account registration (US$25) | https://support.google.com/googleplay/android-developer/answer/6112435 |
| R32 | MYSTERY ROOM privacy policy (last updated 9 Oct 2026) | https://sites.google.com/view/mysteryroom-privacy |
| D1 | PocketGamer.biz, “Thinking outside the box: the making of The Room”, 2013-06-19 | https://www.pocketgamer.biz/thinking-outside-the-box-the-making-of-the-room/ |
| D2 | PocketGamer.biz, “The Room has sold 5.4 million…”, 2014-03-07 | https://www.pocketgamer.biz/the-room-has-sold-54-million-without-the-databollocks-says-fireproofs-barry-meade/ |
| D3 | itch.io blog, interview with Rusty Lake's creators, 2018-02-06 | https://itch.io/blog/23246/peering-into-the-rusty-lake-an-interview-with-the-series-creators |
| D4 | Rusty Lake YouTube channel (official walkthrough videos) | https://www.youtube.com/@RustyLake/search?query=walkthrough |
| D5 | Gigazine, 2016-05-23, reporting ustwo's “Monument Valley in Numbers: Year 2” (original post: https://medium.com/@ustwogames/monument-valley-in-numbers-year-2-440cf5562fe, not opened by me) | https://gigazine.net/gsc_news/en/20160523-monument-valley-in-numbers-year-2 |
| D6 | Player2, “PAXAUS 2015 Indie Showcase – Agent A”, 2015-10-28 | https://www.player2.net.au/2015/10/paxaus-2015-indie-showcase-agent-a/ |
| D7 | MobileSyrup, 2017-01-31 (citing the Wall Street Journal and Nintendo) | https://mobilesyrup.com/2017/01/31/5-percent-of-super-mario-run-players-have-paid-to-unlock-the-full-game/ |
| D8 | NBC News, 2012-08-16 (Gasketball developers' statement) | https://www.nbcnews.com/tech/tech-news/how-app-200-000-downloads-led-developer-homelessness-flna946720 |
| T4 | PwC Worldwide Tax Summaries — Uzbekistan, taxes on personal income (last reviewed 27 Aug 2026) | https://taxsummaries.pwc.com/republic-of-uzbekistan/individual/taxes-on-personal-income |
| T5 | PwC Worldwide Tax Summaries — Uzbekistan, tax administration (last reviewed 27 Aug 2026) | https://taxsummaries.pwc.com/republic-of-uzbekistan/individual/tax-administration |
| T6 | PwC Worldwide Tax Summaries — Uzbekistan, other taxes (VAT) (last reviewed 27 Aug 2026) | https://taxsummaries.pwc.com/republic-of-uzbekistan/corporate/other-taxes |
| T7 | IT Park Uzbekistan, “Tax incentives for startups and foreign investors…”, 2026-01-07 | https://www.it-park.uz/en/itpark/news/tax-incentives-for-startups-and-foreign-investors-in-uzbekistan-s-it-sector |
| E1 | DevGAMM Awards 2026 — Rules | https://devgamm.com/awards2026/rules/ |
| E2 | GDWC — About | https://thegdwc.com/pages/about.php |
| E3 | GDWC — FAQ | https://thegdwc.com/pages/faq.php |
| E4 | Big Indie Pitch at PG Connects Summit Montréal 2026 | https://www.bigindiepitch.com/event/the-big-indie-pitch-mobilepcconsole-edition-at-pocket-gamer-connects-summit-montreal-2026/ |

## Could not be verified
- Typical play length of every comparable game: HowLongToBeat was not reachable, and the developers do not state lengths. Only single-reviewer reports are quoted.
- The Monument Valley 3 Google Play listing (price and installs).
- A public benchmark for free-chapter → paid-unlock conversion, and for refund rates.
- Whether Uzbek bank cards can pay on Google Play and the App Store.
- Whether Apple accepts a Uzbek bank account for an individual developer.
- Whether any US withholding applies to App Store or Play proceeds for an Uzbekistan resident, and which treaty article applies.
- The USD value of 12,000 BCU (the Uzbek VAT registration threshold).
- Whether an individual or individual entrepreneur can join IT Park.
- Promo-code quotas on both stores.
- Eligibility of Uzbekistan developers for the Google Play Indie Games Festival; IGF fees.
- The bank-fee, accountant-cost, tax-mix (10%) and refund (2%) inputs in section 4. These are assumptions, not data.
