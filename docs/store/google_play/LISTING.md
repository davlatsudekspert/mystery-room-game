# Google Play store listing: MYSTERY ROOM (EN / RU)

Play Console → **Grow users → Store presence → Main store listing** (Russian: «Основная страница в Google Play»).
- Default language: **English (United States) – en-US**.
- Translation: **Russian – ru-RU** (Translations → Manage translations → Add your own translation text).
- Play has **no Uzbek** listing language, so the EN and RU texts say the game is fully playable in Uzbek.

Payments are still off (`REAL_PAYMENTS_ENABLED = false`), and store builds show Chapter 2 as locked ("coming soon"). The texts therefore only say what the build does today: **Chapter 1 is free, more chapters are coming**. They make no purchase promise and no price claim.

Limits are from the Play Console Help (see `../README.md`, sources P1–P3): app name ≤ 30 characters, short description ≤ 80, full description ≤ 4,000. The counts below were measured by `tools/store/make_store_graphics.py --check-text`.

---

## English (United States) – en-US

### App name (28 / 30)
```text
Mystery Room: Lost Institute
```

### Short description (65 / 80)
```text
A 3D mystery escape room. Light remembers. Find out what it kept.
```

### Full description (≤ 4,000)
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

## Russian – ru-RU

### Название (30 / 30)
```text
Mystery Room: Забытый институт
```

### Краткое описание (60 / 80)
```text
3D-головоломка-побег. Свет помнит. Узнайте, что он сохранил.
```

### Полное описание (≤ 4 000)
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

## When real payments are switched on (not before)
Replace the last paragraph only after the purchase works in the store build and the IARC questionnaire says "purchases: yes" (`docs/BUSINESS_STRATEGY.md` §9):
- EN: `Chapter 1, "The Locked Laboratory", is free to play from start to finish. One optional purchase unlocks the next chapters.`
- RU: `Глава 1 «Запертая лаборатория» бесплатна целиком. Одна необязательная покупка открывает следующие главы.`

## Other listing fields (unchanged from `PLAY_VA_APPSTORE_QOLLANMA.txt` §1.5)
- App or game: **Game**. Category: **Puzzle**. Tags: Puzzle, Escape room, Mystery, Adventure (those that exist in the list).
- Contact email: **the owner's support email** (to be filled by the owner).
- Privacy policy: `https://sites.google.com/view/mysteryroom-privacy`.
