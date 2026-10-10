# Store assets: MYSTERY ROOM (Google Play, App Store, TestFlight)

## Qisqacha (oʻzbekcha)
- **Tayyor:**
  - Google Play: belgi (icon), feature graphic (EN va RU), 8 ta telefon skrinshoti (EN va RU). Planshet (7" va 10") uchun ham oʻsha fayllar ishlatiladi.
  - App Store: iPhone 6.9", 6.5", 6.3" va iPad 13" skrinshotlari (EN va RU).
  - EN/RU matnlar: nom, qisqa va toʻliq tavsif, subtitle, promotional text, keywords.
  - App Privacy javobi («Data Not Collected») va yosh reytingi javoblari (natija 9+).
  - TestFlight «Test Information» qoralamasi.
  - Hammasini bir varaqda koʻrish: `store_assets_sheet.jpg`.
- **Sizning soʻrovingiz boʻyicha:**
  - Tavsif Leylaning oʻyinchiga yozgan qisqa xati bilan boshlanadi (EN/RU/UZ).
  - Keyin ajratuvchi chiziq, biznes-model haqida bitta gap («1- va 2-boblar bepul, 3- va 4-boblar uchun bitta xarid rejalashtirilgan, hozircha sotuvda yoʻq») va 5 ta bandli roʻyxat keladi.
  - 1-skrinshot: qorongʻi xonadagi Strandning tishli qutisi (1-bob), pastida oltin chiziqli yozuv bor: «◆ —— Every clock stopped at 03:17 —— ◆» (RU: «Все часы остановились в 03:17»).
- **Skrinshotlar** oʻyinning haqiqiy Godot renderlari (Blender emas). Ular boshqa variant seed bilan olingan, shuning uchun oʻyinchining javoblarini oshkor qilmaydi.
- **Muhim (2026-10-10 dan):** 2-bob endi bepul va doʻkon buildida ochiq. Shuning uchun 2-bobdan olingan 07–08 skrinshotlarni ham yuklash mumkin (01–08). 3–4-boblar chiqmaguncha ulardan skrinshot qoʻymang (Apple 2.3.1, Google Play metadata qoidasi).
- **Sizdan kerak:**
  - support e-mail va Support URL;
  - TestFlight feedback e-mail va App Review kontakt maʼlumotlari;
  - Copyright qatori uchun ism yoki studiya nomi.
- Hech narsa yuklanmadi. Play Console va App Store Connect'ga kirilmadi. Workflow ishga tushirilmadi.

---

## What to upload where
| Store field | File(s) | Notes |
|---|---|---|
| Play → Main store listing → App icon | `google_play/icon_512.png` | 512×512, 32-bit PNG (RGBA, opaque), < 1024 KB [P1] |
| Play → Feature graphic (en-US) | `google_play/feature_graphic_en-US.jpg` | 1024×500 JPEG, no alpha [P1]. Logo kept out of the edge zones |
| Play → Feature graphic (ru-RU translation) | `google_play/feature_graphic_ru-RU.jpg` | Same art, the Russian logo subtitle |
| Play → Phone screenshots (en-US) | `google_play/screenshots/en-US/01…08_*.jpg` | 2560×1440 (16:9) JPEG. Max side ≤ 3840 and ≤ 2× the short side. Three or more 16:9 shots ≥ 1920×1080 make a game eligible for recommendations [P1] |
| Play → 7-inch and 10-inch tablet screenshots | `google_play/tablet_01_gear_box_no_caption.jpg` + `screenshots/en-US/02…08` | Large screens: 1,080–7,680 px, 16:9 landscape, at least 4, and "exclude additional text that is not part of your core app experience" [P1]. Hence the hero without its caption band |
| Play → screenshots (ru-RU translation) | `google_play/screenshots/ru-RU/` | The game UI and the caption in Russian. Without them Play shows the en-US ones |
| Play → texts | `google_play/LISTING.md` | Name, short and full description, EN and RU (and UZ for later), with measured counts [P2] |
| App Store → iPhone 6.9" (Dynamic Island, large) | `app_store/screenshots/iphone_6.9/<locale>/` | 2868×1320 landscape [A1] |
| App Store → iPhone 6.5" (Face ID, large) | `app_store/screenshots/iphone_6.5/<locale>/` | 2688×1242 landscape [A1] |
| App Store → iPhone 6.3" (Dynamic Island, medium) | `app_store/screenshots/iphone_6.3/<locale>/` | 2622×1206 landscape [A1] |
| App Store → iPad 13" | `app_store/screenshots/ipad_13/<locale>/` | 2752×2064 landscape [A1] |
| App Store → texts, App Privacy, age rating | `app_store/METADATA.md` | EN and RU [A2–A5] |
| TestFlight → Test Information | `testflight/TEST_INFORMATION.md` | Beta description, What to Test, review notes [A6–A8] |
| Review | `store_assets_sheet.jpg` | Every image above, small. Chapter 2 shots have an orange frame |

`<locale>` is `en-US` or `ru`.

**Which iPhone sizes are required (checked 2026-10-09).** Apple's page [A1] now says:
- "iPhone: At least one screenshot for iPhone with Dynamic Island (medium display)" (6.3");
- "iPad (if your app supports iPadOS): At least one screenshot for iPad 13-inch display";
- for 6.5": "Required if app runs on iPhone and screenshots for iPhone with Dynamic Island (large display) aren't provided".

Smaller sizes are scaled from the larger ones. Upload 6.9" and 6.3", plus 6.5" if App Store Connect asks for it, and iPad 13".

**Chapter 2 shots (07–08).** Since 2026-10-10 Chapter 2 is free, so store builds open it and shots 07–08 may be uploaded. Never show Chapters 3–4 before they ship:
- Apple: "marketing your app in a misleading way, such as by promoting content or services that it does not actually offer … is grounds for removal" (Guideline 2.3.1(a)) [A9].
- Play's metadata policy has the same rule for screenshots [P4].
- **Upload 01–06 now.** These six Chapter 1 shots cover Play's three-shot minimum for recommendations and Apple's one-shot minimum.
- Add 07–08 once Chapter 2 can really be unlocked in the store build.

## How the screenshots were made
- **Real Godot renders.** The QA scenes play the real game through simulated taps (`qa/playthrough.tscn`, `qa/playthrough_ch2.tscn`). They were rendered at each store's native window size through `tools/qa_run.sh`.
  - Seeds: Chapter 1 4242, Chapter 2 777. Every new game draws its own answers (`docs/VARIANTS.md`), so the numbers seen in a shot are not a player's solution.
  - No shot shows a code being entered, either chapter's finale or the Chapter 2 vault interior.
  - The shadow sculpture (06) is shown before it is aligned, because its answer is the same in every game.
  - The one solved state on show (the tuned radio in 04) belongs to seed 4242 only.
- **The real HUD is kept in 02–08** (pause, hint, inventory, view title, captions), in English or Russian, as the player sees it. There are no device frames.
- **01 is the hero frame** (owner's request): Strand's gear box from Chapter 1 in the dark opening scene, our own model.
  - It is a `qa/view_probe.tscn` camera rendered 1.3× larger than the store size and centre-cropped, so the corner HUD buttons fall outside the frame.
  - The caption band (`◆ —— Every clock stopped at 03:17 —— ◆` / `Все часы остановились в 03:17`) is drawn on top in the game's brass colours and Cormorant Garamond. It takes 13 % of the height; Play allows taglines up to 20 % [P1], and Apple allows text overlays (Guideline 2.3.3) [A9].
- **Shapes.**
  - Play: 2560×1440.
  - iPhone: 2868×1320, scaled down by 6–9 % to 6.5" and 6.3", cropping at most 10 px. All three are the same ≈2.17:1 shape, so the HUD layout is identical.
  - iPad: 2752×2064.
- **Feature graphic.** A `qa/view_probe.tscn` frame of the lit Laboratory 7 with the Lumen beam on, plus the owner's logo (`game/assets/ui/logo/logo_en.png` / `logo_ru.png`, made from `docs/brand/logo_source.png`). It uses Chapter 1 art only, for the same reason as above.
- **Rebuild:** run the renders listed in `tools/store/make_store_graphics.py`, then `python3 tools/store/make_store_graphics.py --renders=<dir>`. Check the texts with `--check-text`.

| # | File name | Chapter | Moment |
|---|---|---|---|
| 01 | `01_gear_box` | 1 | Hero: Strand's gear box in the dark, caption band |
| 02 | `02_laboratory` | 1 | Laboratory 7 with the power back on |
| 03 | `03_projector_beam` | 1 | The Lumen projector throws its beam |
| 04 | `04_radio` | 1 | The valve radio picks up a beacon |
| 05 | `05_uv_ink` | 1 | The UV lamp reveals a hidden mark on the desk |
| 06 | `06_shadow_sculpture` | 1 | The shadow sculpture in Leyla's red darkroom, not yet aligned |
| 07 | `07_archive_hall` | 2 | Records Archive B and its vault door |
| 08 | `08_film_projection` | 2 | Strand's film on the archive screen |

## Alt text (Play asks for ≤ 140 characters per graphic)
| File | EN | RU |
|---|---|---|
| feature graphic | Mystery Room logo over a 1970s laboratory where a beam of light crosses the room from a brass projector. | Логотип Mystery Room на фоне лаборатории 1970-х, через которую идёт луч света из латунного проектора. |
| 01 | A wooden box with brass gears and knobs on a dark desk; caption: Every clock stopped at 03:17. | Деревянная шкатулка с латунными шестернями в темноте; подпись: Все часы остановились в 03:17. |
| 02 | A dim 1970s laboratory with a desk, filing cabinet and window, lit by a desk lamp. | Полутёмная лаборатория 1970-х: стол, картотека и окно в свете настольной лампы. |
| 03 | A brass projector on a tripod sends a white beam across the lab. | Латунный проектор на треноге посылает белый луч через лабораторию. |
| 04 | Close-up of an old valve radio with a wavelength dial. | Крупный план старого лампового радио со шкалой волн. |
| 05 | A UV lamp makes a glowing mark appear on the side of a wooden desk. | Ультрафиолетовая лампа проявляет светящийся знак на боку деревянного стола. |
| 06 | A brass ring and rod cast a shadow onto a circle of light in a red darkroom. | Латунные кольцо и стержень отбрасывают тень в световой круг в красной фотолаборатории. |
| 07 | A records archive with shelves, a card catalogue and a large round vault door. | Архив с полками, картотекой и большой круглой дверью хранилища. |
| 08 | A film is projected onto a screen in a dark archive hall. | В тёмном зале архива на экран проецируется фильм. |

## Files
FILE_TABLE

## Needs the owner
- **Support e-mail and Support URL.** Play "Contact email" and App Store "Support URL" must lead to real contact information [A3]. Suggestion: add a contact line to the privacy Google Site.
- **TestFlight Feedback Email** and the **Beta App Review contact** (name, phone, e-mail): `testflight/TEST_INFORMATION.md`.
- **Copyright** line (`2026 <name>`).
- **Russian localization** on App Store Connect (Add Language → Russian) before the RU texts and screenshots can be entered.
- When payments go live, update three things:
  - the business-model sentence of each description (`google_play/LISTING.md` gives the replacement);
  - the IARC answer to "purchases: yes";
  - add screenshots 07–08.

## Sources (all read on 2026-10-09)
| Tag | Official page |
|---|---|
| P1 | Play Console Help — Add preview assets to showcase your app (icon, feature graphic, screenshots, large screens, alt text): https://support.google.com/googleplay/android-developer/answer/9866151 |
| P2 | Play Console Help — Create and set up your app (app name 30, short description 80, full description 4000 characters): https://support.google.com/googleplay/android-developer/answer/9859152 |
| P3 | Play Console Help — Translate and localize your app (listing languages: Russian – ru-RU; no Uzbek): https://support.google.com/googleplay/android-developer/answer/9844778 |
| P4 | Play Console Help — Metadata policy: https://support.google.com/googleplay/android-developer/answer/9898842 |
| A1 | App Store Connect Help — Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications |
| A2 | App Store Connect Help — App information (name 2–30, subtitle ≤ 30): https://developer.apple.com/help/app-store-connect/reference/app-information/app-information |
| A3 | App Store Connect Help — Platform version information (promotional text 170, description 4000, keywords 100 bytes, support URL, copyright): https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information |
| A4 | App Store Connect Help — Age ratings values and definitions: https://developer.apple.com/help/app-store-connect/reference/age-ratings and Set an app age rating: https://developer.apple.com/help/app-store-connect/manage-app-information/set-an-app-age-rating |
| A5 | Apple — App privacy details on the App Store: https://developer.apple.com/app-store/app-privacy-details/ |
| A6 | App Store Connect Help — Provide test information: https://developer.apple.com/help/app-store-connect/test-a-beta-version/provide-test-information |
| A7 | App Store Connect Help — Invite external testers: https://developer.apple.com/help/app-store-connect/test-a-beta-version/invite-external-testers |
| A8 | App Store Connect Help — TestFlight overview: https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview |
| A9 | App Review Guidelines (2.3.1, 2.3.3, 2.3.7): https://developer.apple.com/app-store/review/guidelines/ |
| A10 | App Store Connect Help — App Store localizations (no Uzbek; the Uzbekistan storefront uses English (U.K.)): https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations |

The older 1280×720 set in `graphics/` (from `make_store_graphics.py` of 2026-10-09 morning) is replaced by the folders above.
