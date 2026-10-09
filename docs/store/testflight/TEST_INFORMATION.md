# TestFlight "Test Information": draft (EN, optional RU)

Where it goes: App Store Connect → the app → **TestFlight** → Additional → **Test Information** (source A6), and the **What to Test** box that appears when a build is added to a group (source A7).
- Internal testers (App Store Connect users of the team) do not need this page.
- **External testers** do. The first build of a version also goes to TestFlight App Review, which reads this page and the review contact fields.
- `<...>` marks a value the **owner** fills in. Do not invent e-mails or phone numbers.
- Test builds are exported with `beta_unlock`: Chapter 2 opens without a purchase, and real payments stay disabled (`docs/release/IOS_TESTFLIGHT.md`). The texts below say so.

---

## Beta App Description (required)
### English (U.S.)
```text
Mystery Room: Lost Institute is a 3D escape-room mystery for iPhone and iPad, played in landscape.

On 14 November 1979 every clock in the Meridian Institute stopped at 03:17, and forty-one scientists were never seen again. You explore their rooms, solve logical puzzles built from brass mechanisms, light and shadow, and slowly uncover what happened.

This beta contains Chapter 1 "The Locked Laboratory" and Chapter 2 "The Missing Scientist". In test builds Chapter 2 is open without any purchase. There are no purchases, ads, accounts or network features in this build. The game is fully playable in English, Russian and Uzbek.
```

### Russian (optional localization)
```text
Mystery Room: Lost Institute — 3D-головоломка-побег для iPhone и iPad в горизонтальной ориентации.

14 ноября 1979 года все часы в институте «Меридиан» остановились в 03:17, и сорок один учёный бесследно исчез. Вы исследуете их комнаты, решаете логичные головоломки из латунных механизмов, света и тени и постепенно узнаёте, что произошло.

В бета-версии есть Глава 1 «Запертая лаборатория» и Глава 2 «Пропавший учёный». В тестовых сборках Глава 2 открыта без покупки. В этой сборке нет покупок, рекламы, аккаунтов и сетевых функций. Игра полностью доступна на английском, русском и узбекском.
```

## What to Test (per build)
### English (U.S.)
```text
Please play Chapter 1 "The Locked Laboratory" to the end, then Chapter 2 "The Missing Scientist". Then tell us:
1. Where you got stuck, and which hint level (1, 2 or 3) helped.
2. Any text that is cut off, overlaps or is hard to read. Please name the language (English, Russian or Uzbek).
3. Taps that did nothing or opened the wrong object.
4. How smoothly it runs: your iPhone or iPad model and iOS version, and whether the device got hot.
5. Any crash or freeze, and what you did just before it.
To send feedback, take a screenshot in the game, or use the TestFlight app. Thank you for testing!
```

### Russian (optional localization)
```text
Пройдите, пожалуйста, Главу 1 «Запертая лаборатория» до конца, затем Главу 2 «Пропавший учёный». Напишите нам:
1. Где вы застряли и какой уровень подсказки (1, 2 или 3) помог.
2. Обрезанный, наложенный или плохо читаемый текст. Укажите язык (английский, русский или узбекский).
3. Нажатия, которые ничего не сделали или открыли не тот предмет.
4. Насколько плавно идёт игра: модель iPhone или iPad, версия iOS и нагревается ли устройство.
5. Любой вылет или зависание и что вы сделали перед этим.
Чтобы отправить отзыв, сделайте скриншот в игре или используйте приложение TestFlight. Спасибо за помощь!
```

## Other Test Information fields
| Field | Value |
|---|---|
| Feedback Email | `<OWNER: the e-mail testers should write to>`. It is also the reply-to address of the invitation e-mails (source A6) |
| Marketing URL | Optional; leave empty |
| Privacy Policy URL | `https://sites.google.com/view/mysteryroom-privacy` |
| Invitation Experience → App Information | Leave checked. It only shows screenshots and the category after a version is approved for the App Store |

## Beta App Review Information (external testing only)
| Field | Value |
|---|---|
| Contact first and last name | `<OWNER>` |
| Contact phone | `<OWNER>` |
| Contact e-mail | `<OWNER>` |
| Sign-in required | **No** (the game has no accounts) |
| Review notes | see below |

```text
No sign-in is needed and the game works fully offline. This is a test build: Chapter 2 is unlocked without a purchase, and all purchase code is disabled. The game is landscape only. The hint button (light bulb, top right) gives three levels of hints for the current puzzle; level 3 tells the answer. Chapter 1 takes about 30-60 minutes.
```
