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

Payments are off in store builds, which show Chapter 2 as "coming soon". The texts describe only what the build does (App Review Guideline 2.3). Promotional text, keywords and subtitle carry no price wording (Guideline 2.3.7).

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
On 14 November 1979 every clock in the Meridian Institute stopped at 03:17, and forty-one scientists were never seen again.

Decades later, a parcel arrives for you: an old lab badge and a single line. "Laboratory 7. Please finish what I could not."

Step into Laboratory 7, a hand-crafted 3D room frozen at the moment everyone vanished. Search the desk, read the notes, bring back the power and tune the old radio. Somewhere in this room, the light is still waiting.

• Hand-crafted 3D rooms full of tactile brass mechanisms
• Fair, logical puzzles with no random guessing
• A three-step hint system for when you are stuck
• Most puzzle answers change with every new game, so you solve it yourself, not from a walkthrough
• Signature Lumen mechanics: record light in a crystal, project it as a key and steer a living beam with mirrors
• UV ink, radio beacons, electrical circuits, shadows and hidden rooms
• An original story told through objects, handwriting and light
• Choices that carry into the next chapters
• Fully playable in English, Russian and Uzbek
• Works offline. No ads, no energy, no subscriptions, no account

Chapter 1, "The Locked Laboratory", is free to play from start to finish. More chapters are coming.
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
14 ноября 1979 года все часы в институте «Меридиан» остановились в 03:17, и сорок один учёный бесследно исчез.

Спустя десятилетия вам приходит посылка: старый пропуск лаборатории и одна строка: «Лаборатория 7. Пожалуйста, закончи то, что не смогла я».

Войдите в Лабораторию 7 — 3D-комнату, застывшую в момент исчезновения. Обыщите стол, прочитайте записи, верните питание и настройте старое радио. Где-то здесь свет всё ещё ждёт.

• Атмосферные 3D-комнаты с латунными механизмами, которые приятно трогать
• Честные логичные головоломки без случайного угадывания
• Трёхступенчатые подсказки, если вы застряли
• Большинство ответов меняется в каждой новой игре: решение не списать из прохождения
• Фирменные механики Люмена: запишите свет в кристалл, спроецируйте его как ключ и управляйте живым лучом с помощью зеркал
• Невидимые чернила, радиомаяки, электрические цепи, тени и тайные комнаты
• Оригинальная история, рассказанная через предметы, почерк и свет
• Решения, которые влияют на следующие главы
• Полностью на английском, русском и узбекском
• Работает без интернета. Без рекламы, энергии, подписок и аккаунтов

Глава 1 «Запертая лаборатория» бесплатна целиком. Новые главы уже в работе.
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
