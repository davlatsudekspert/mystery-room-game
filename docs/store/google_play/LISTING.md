# Google Play store listing: MYSTERY ROOM (EN / RU, plus UZ for later)

Play Console → **Grow users → Store presence → Main store listing** (Russian: «Основная страница в Google Play»).
- Default language: **English (United States) – en-US**.
- Translation: **Russian – ru-RU** (Translations → Manage translations → Add your own translation text).
- Play has **no Uzbek** listing language [P3], so the EN and RU texts say the game is fully playable in Uzbek. The UZ text at the end is kept for the game's own pages or a future store language.

**Description structure (owner's request, 2026-10-09):**
1. a short letter from Leyla to the player, in our own words;
2. a separator line;
3. one plain sentence on the business model;
4. five feature bullets.

The owner sent another game's App Store page as a structural reference only. No text, art or badges were taken from it.

**Payments are still off** (`REAL_PAYMENTS_ENABLED = false`). Since 2026-10-10 Chapters 1 and 2 are free (owner decision); Chapters 3–4, which the purchase unlocks, are not released yet. The business-model sentence therefore says the purchase is **planned and not on sale yet**, with no price.

Limits are from the Play Console Help (`../README.md`, sources P1–P4): app name ≤ 30 characters, short description ≤ 80, full description ≤ 4,000. The counts below were measured by `tools/store/make_store_graphics.py --check-text`.
- The separator `◆ ——— ◆` is a single line. Play's special-character rule targets the title, icon and developer name [P4].
- If Play's review ever objects, replace the separator with an empty line.

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

## Uzbek (not a Play listing language; kept for later)

### Toʻliq tavsif (≤ 4,000)
```text
Agar bu xat sizga yetib kelgan boʻlsa, institut yetarlicha uzoq jim turdi.
Binodagi barcha soatlar 03:17 da toʻxtadi va oramizdan qirq bir kishi uyiga qaytmadi.
Qoʻlimdan kelganini yashirdim: tortmalarga, faqat bitta chiroq koʻrsatadigan siyohga, koʻz oldidagi joylarga.
Shoshilmay qidiring. U xonada hech narsa tasodifan turmaydi.
Yorugʻlik eslaydi. Undan ehtiyotkorlik bilan soʻrang.
7-laboratoriya. Iltimos, men tugata olmagan ishni tugating. — L.

◆ ——— ◆

1- va 2-boblar toʻliq bepul. Tergovning qolgan qismini, yaʼni 3- va 4-boblarni ochadigan bitta xarid rejalashtirilgan, hozircha sotuvda yoʻq.

• 1979-yildagi realistik 3D xonalar: yongʻoq panellar, jez mexanizmlar va qizil nurli fotolaboratoriya
• Bir barmoq bilan boshqaruv: yaqindan koʻrish uchun bosing, dastakni burash yoki chiroq bilan yoritish uchun suring
• Aksariyat jumboqlarning javobi har yangi oʻyinda oʻzgaradi, internetdagi yechim uni siz uchun yechib bermaydi
• Ingliz, rus va oʻzbek tillarida toʻliq
• Reklama yoʻq, hech qanday maʼlumot toʻplanmaydi. Internetsiz ishlaydi
```

---

## When real payments are switched on (not before)
Replace only the business-model sentence. Do this after the purchase works in the store build and the IARC questionnaire says "purchases: yes" (`docs/BUSINESS_STRATEGY.md` §9):
- EN: `Chapters 1 and 2 are free to play in full. One purchase unlocks the rest of the investigation, Chapters 3 and 4.`
- RU: `Главы 1 и 2 бесплатны целиком. Одна покупка открывает остальное расследование — главы 3 и 4.`
- UZ: `1- va 2-boblar toʻliq bepul. Bitta xarid tergovning qolgan qismini, yaʼni 3- va 4-boblarni ochadi.`

## Fact check of the bullets
| Claim | Where it is true |
|---|---|
| One-finger controls | Every action is a tap or a one-finger drag. Pinch-to-zoom and two-finger back are optional; the on-screen back button does the same (input setup in `game/src/rooms/room_base.gd` and `lab7_room.gd`; back button in `game/src/ui/hud.gd`) |
| Answers change every game | `docs/VARIANTS.md`: on for players. Story anchors (03:17, 41 staff) stay fixed, hence "most" |
| No data collected, offline | No `INTERNET` permission in the APK/AAB; no analytics or ads (`docs/release/GOOGLE_PLAY_TESTING.md` §5) |
| Three languages | `game/localization/strings.csv` (en, ru, uz) |

## Other listing fields (unchanged from `PLAY_VA_APPSTORE_QOLLANMA.txt` §1.5)
- App or game: **Game**. Category: **Puzzle**. Tags: Puzzle, Escape room, Mystery, Adventure (those that exist in the list).
- Contact email: **the owner's support email** (to be filled by the owner).
- Privacy policy: `https://sites.google.com/view/mysteryroom-privacy`.
