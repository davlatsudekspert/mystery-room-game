# App Store metadata: MYSTERY ROOM (EN / RU)

App Store Connect record **"Mystery Room: Lost Institute"** (Apple ID `6820786933`, bundle `com.mysteryroom.forgotteninstitute`, primary locale `en-US`; see `docs/release/IOS_TESTFLIGHT.md`).
- **English (U.S.)** is the primary localization.
- **Russian** has to be added: App Store Connect → the app → the language menu → Add Language → Russian.
- App Store Connect has **no Uzbek** localization, so the texts say the game is fully playable in Uzbek. The build's `uz.lproj` puts Uzbek in the product page's Languages row.

Limits are from Apple's App Store Connect Help (see `../README.md`, sources A2–A3):
- name 2–30 characters; subtitle ≤ 30 characters;
- promotional text ≤ 170 characters; description ≤ 4,000 characters;
- keywords ≤ 100 **bytes**, each keyword longer than two characters, no words from the app name.

Russian letters take 2 bytes each in UTF-8, so the RU keyword list is short on purpose. The counts below were measured by `tools/store/make_store_graphics.py --check-text`.

**Description structure (owner's request, 2026-10-09):** the same as on Play.
1. A short letter from Leyla to the player.
2. A separator line.
3. One sentence on the business model.
4. Five feature bullets.

The full rationale, the Uzbek version and the fact check are in `../google_play/LISTING.md`.

Payments are off in store builds, which show Chapter 2 as "coming soon". So the business-model sentence says the purchase is **planned and not on sale yet** and gives no price. The texts describe only what the build does (App Review Guideline 2.3). Promotional text, keywords and subtitle carry no price wording (Guideline 2.3.7).

---

## English (U.S.)

### Name (28 / 30)
```text
Mystery Room: Lost Institute
```

### Subtitle (24 / 30)
```text
A 3D escape-room mystery
```
Alternative (29 / 30): `Escape room of light & shadow`

### Promotional text (139 / 170)
```text
Every clock in the Meridian Institute stopped at 03:17. Step into Laboratory 7, bring back the power and find out what the light remembers.
```

### Keywords (96 / 100 bytes)
```text
escape,puzzle,adventure,riddle,detective,quest,clues,logic,laboratory,secret,offline,story,brain
```

### Description (≤ 4,000)
```text
If this reaches you, the Institute has kept its silence long enough.
Every clock in the building stopped at 03:17, and forty-one of us never came home.
I hid what I could: in drawers, in ink that only one lamp can show, in plain sight.
Search slowly. Nothing in that room is there by chance.
The light remembers. Ask it gently.
Laboratory 7. Please finish what I could not. — L.

◆ ——— ◆

Chapters 1 and 2 are free to play in full. One purchase that unlocks the rest of the investigation, Chapters 3 and 4, is planned and not on sale yet.

• Realistic 3D rooms from 1979: walnut panels, brass mechanisms and a darkroom glowing red
• One-finger touch controls: tap to look closer, drag to turn a dial or sweep a lamp
• Most puzzle answers change with every new game, so no walkthrough can solve it for you
• Fully playable in English, Russian and Uzbek
• No ads and no data collected. Works offline
```

---

## Russian

### Name (30 / 30)
```text
Mystery Room: Забытый институт
```

### Subtitle (22 / 30)
```text
Головоломка-побег в 3D
```

### Promotional text (124 / 170)
```text
Все часы в институте «Меридиан» остановились в 03:17. Войдите в Лабораторию 7, верните питание и узнайте, что запомнил свет.
```

### Keywords (88 / 100 bytes)
```text
побег,квест,загадки,детектив,логика,тайна,ключи
```
`docs/release/IOS_TESTFLIGHT.md` proposed a longer list (86 characters). It is about 160 bytes in UTF-8, which is over Apple's 100-byte limit. Use this one.

### Description (≤ 4,000)
```text
Если это дошло до тебя, институт молчал достаточно долго.
Все часы в здании остановились в 03:17, и сорок один из нас так и не вернулся домой.
Я спрятала всё, что смогла: в ящиках, в чернилах, которые видны лишь под одной лампой, на самом виду.
Ищи не спеша. В той комнате ничего не лежит случайно.
Свет помнит. Спроси его бережно.
Лаборатория 7. Пожалуйста, закончи то, что не смогла я. — Л.

◆ ——— ◆

Главы 1 и 2 бесплатны целиком. Одна покупка, открывающая остальное расследование — главы 3 и 4, — запланирована и пока не продаётся.

• Реалистичные 3D-комнаты 1979 года: ореховые панели, латунные механизмы и фотолаборатория в красном свете
• Управление одним пальцем: нажмите, чтобы рассмотреть, проведите, чтобы повернуть ручку или посветить лампой
• Большинство ответов меняется в каждой новой игре: прохождение из интернета за вас её не решит
• Полностью на английском, русском и узбекском
• Без рекламы и без сбора данных. Работает без интернета
```

---

## Other App Information fields
| Field | Value | Who |
|---|---|---|
| Primary category | Games → **Puzzle** | — |
| Secondary category | Games → **Adventure** | — |
| Privacy Policy URL | `https://sites.google.com/view/mysteryroom-privacy` | — |
| Support URL (required) | Must lead to real contact information. Suggestion: add a "Contact" line with the support e-mail to the same Google Site, then use that URL | **Owner** |
| Marketing URL | Optional; leave empty | — |
| Copyright (required) | `2026 <owner's legal name or studio name>` (Apple adds the © sign) | **Owner** |
| Version | `1.0` (the record's current version) | — |

## App Privacy: "Data Not Collected"
App Store Connect → the app → **App Privacy** → Get Started → "Do you or your third-party partners collect data from this app?" → **No, we do not collect data from this app** → Save → **Publish**. The product page then shows **"Data Not Collected"**.

Why this is true for the current build:
- No accounts, ads, analytics, crash-upload or third-party SDKs.
- The game makes no network requests; progress and settings stay on the device (`user://`).
- The privacy-policy link opens the system browser, outside the app.

Apple: "You are not responsible for disclosing data collected by Apple" (App privacy details, source A5). Purchases through StoreKit therefore do not change the answer by themselves. **Re-answer before release** if a later build adds server-side receipt validation, analytics, crash reporting or any network call that sends data off the device.

## Age rating: suggested answers (App Information → Age Ratings → Set Up Age Ratings)
Apple's 2025+ questionnaire covers in-app controls, capabilities and content frequency (source A4). Suggested answers for Chapters 1–2:

| Section | Item | Answer | Why |
|---|---|---|---|
| In-App Controls | Parental Controls | No | — |
| In-App Controls | Age Assurance | No | — |
| Capabilities | Unrestricted Web Access | No | The privacy link opens Safari; there is no in-app browser |
| Capabilities | User-Generated Content | No | — |
| Capabilities | Social Media | No | — |
| Capabilities | Messaging and Chat | No | — |
| Capabilities | Advertising | No | No ads |
| Mature Themes | Profanity or Crude Humor | None | — |
| Mature Themes | **Horror/Fear Themes** | **Infrequent** | Dark rooms, an unexplained disappearance, translucent "echo" figures of the missing staff. No gore, no jump scares |
| Mature Themes | Alcohol, Tobacco, or Drug Use or References | None | Lab vials and darkroom chemicals only |
| Medical or Wellness | Medical or Treatment Information | None | — |
| Medical or Wellness | Health or Wellness Topics | None | — |
| Sexuality or Nudity | Mature or Suggestive Themes | None | (Answering "Infrequent" for the disappearance plot gives the same 9+) |
| Sexuality or Nudity | Sexual Content or Nudity | None | — |
| Sexuality or Nudity | Graphic Sexual Content and Nudity | None | — |
| Violence | Cartoon or Fantasy Violence | None | — |
| Violence | Realistic Violence | None | — |
| Violence | Prolonged Graphic or Sadistic Realistic Violence | None | — |
| Violence | Guns or Other Weapons | None | — |
| Chance-Based Activities | Gambling | No | — |
| Chance-Based Activities | Simulated Gambling | None | — |
| Chance-Based Activities | Contests | None | — |
| Chance-Based Activities | Loot Boxes | No | The planned unlock is one fixed purchase, not a random reward |
| Age Categories and Override | — | Not Applicable | Not a Kids-category app |

**Expected result: 9+.** Apple's table puts "Infrequent horror or fear themes" at 9+, and nothing else raises it. This matches the Google Play IARC answers (fear: yes, mild) in `../PLAY_VA_APPSTORE_QOLLANMA.txt` §1.4. Review the answers again before Chapters 3–4 ship.

## Export compliance
Answered in the binary (`ITSAppUsesNonExemptEncryption = false`). If asked anyway: "None of the algorithms mentioned above".
