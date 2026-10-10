# Localization review — EN / RU / UZ

**Date:** 2026-10-10. **Scope:** every string in `tools/localization/strings_core.py`, `strings_ch1.py`,
`strings_hints.py`, `strings_ch2.py` and `strings_ch3.py` (671 keys × 3 languages, hints included).
`game/localization/strings.csv` is regenerated from these sources with `python3 tools/localization/build_csv.py`.
The fixed terms are in `docs/GLOSSARY.md`.

## Method
1. Read `docs/PUZZLE_DESIGN.md`, `CHAPTER2_DESIGN.md`, `CHAPTER3_DESIGN.md`, `VARIANTS.md` and `STORY.md` first,
   so that no edit could touch a code, an order, a position or a symbol. Level-3 hints keep their placeholders.
2. Automated scan of all 2013 values: Uzbek apostrophes (only ʻ U+02BB in oʻ/gʻ, ʼ U+02BC as tutuq belgisi,
   no ASCII `'`, no backtick), Cyrillic in UZ, ё consistency in RU (word list), straight `"` quotes,
   American spellings in EN, placeholder counts per language. The scan found RU ё and UZ apostrophes already
   consistent; it found nine EN strings with straight quotes.
3. Manual read of each key in the three languages for meaning, tone, terminology and fit (lengths compared with EN;
   `test_layout.gd` checks the buttons and `msg.*` lines at 1.3 text scale).
4. Font coverage: every character used is in Noto Sans (the UI font and the fallback of the display fonts).

## Result
- **74 keys changed, 79 values:** EN 9, RU 20, UZ 50.
- **Classes of fixes**
  - *Terminology collisions removed:* RU «батарея» (radiator vs battery) → «радиатор»; RU/UZ «решётка»/«panjara» for the vent
    grille (the Array is «Решётка»/«Panjara») → «вентиляционная решётка»/«shamollatish panjarasi»; UZ «daftar» for the ledger
    (the notebook is «daftar») → «hisob daftari»; RU «карта» for the request card → «бланк», as in its item names.
  - *Wrong or calqued words:* RU «кристальные хранилища»/«кристальное окно» (кристальный = crystal-clear) → «хранилища кристаллов»,
    «кристаллическое»; UZ «doka» (gauze) for the chalkboard → «doska»; UZ «lagan» (platter) for the station tray → «tokcha»;
    UZ «murvat» kept for knobs but «richag» → «dastak» for levers (one word everywhere); UZ «Strandning tishli qutichasi»
    → «tishli gʻildirakli qutichasi»; UZ «Bolalar rasmi» → «Bola chizgan rasm»; UZ «yurak yozuvi» → «kardiogrammasi».
  - *One term per concept:* UZ socket «uya»/«uyacha» → «uyacha»; UZ badge «nishon»/«guvohnoma» → «guvohnoma»;
    UZ progress «natijalar»/«jarayon» → «oʻyin» (Oʻyin saqlandi, Saqlangan oʻyin); RU «зал Решётки» → «Зал Решётки».
  - *Grammar and naturalness:* RU «Оставить её ей» → «Оставить ей»; RU «Сведите пальцы, чтобы приблизить» (pinching zooms out)
    → «Разведите пальцы…»; RU notebook p. 8 «знаком института, несомым светом Люмена» → «для знака института, принесённого
    светом Люмена»; RU/UZ notebook p. 3 (Strand gave *one of* his boxes); UZ intro «tugata olmagan ishni tugating» →
    «…oxiriga yetkazing»; UZ «sekin gʻuvillaydi» → «mayin gʻuvillaydi»; UZ «Lampa… qizib ketdi» (overheated) → «qizib, … nur sochdi».
  - *Typography:* EN quotes unified to “ ” (nine strings had straight quotes); RU keeps « » and —; UZ keeps « ».
  - *Hint names what the player sees:* RU «Сначала поверните рубильник» → «переключите изолятор» (the Chapter 3 term);
    UZ tape hint «Play»ni bosing → «ijro tugmasini bosing» (the deck key carries no printed text).
- **Puzzle texts:** no answer, code, order or position was changed in any language.

## Changed keys (old → new)

### core (12 values)

| Key | Lang | Old | New |
|---|---|---|---|
| `ui.quit_confirm` | uz | Oʻyindan chiqasizmi? Natijalar saqlangan. | Oʻyindan chiqasizmi? Hammasi saqlangan. |
| `ui.new_game_confirm` | uz | Yangi oʻyin boshlansinmi? Joriy natijalar oʻchib ketadi. | Yangi oʻyin boshlansinmi? Joriy oʻyin oʻchib ketadi. |
| `ui.look_sensitivity` | uz | Qarash sezgirligi | Kamera sezgirligi |
| `ui.delete_save` | uz | Natijalarni oʻchirish | Saqlangan oʻyinni oʻchirish |
| `ui.delete_save_confirm` | uz | Barcha saqlangan natijalar oʻchirilsinmi? Buni qaytarib boʻlmaydi. | Saqlangan oʻyin butunlay oʻchirilsinmi? Buni qaytarib boʻlmaydi. |
| `ui.saved` | uz | Jarayon saqlandi | Oʻyin saqlandi |
| `ui.save_failed` | uz | Jarayonni saqlab boʻlmadi | Oʻyinni saqlab boʻlmadi |
| `ui.choice_prompt` | uz | Billur linza proyektorda sekin gʻuvillaydi. Leylaning nuri soʻnmoqda. | Billur linza proyektorda mayin gʻuvillaydi. Leylaning nuri soʻnmoqda. |
| `ui.leave_lens` | ru | Оставить её ей | Оставить ей |
| `tut.zoom` | ru | Сведите пальцы, чтобы приблизить. | Разведите пальцы, чтобы приблизить. |
| `tut.zoom` | uz | Yaqinlashtirish uchun ikki barmoq bilan torting. | Yaqinlashtirish uchun ikki barmoqni kering. |
| `intro.2` | uz | Sizga posilka keldi. Ichida — eski laboratoriya guvohnomasi va bir qator yozuv:<br>«7-laboratoriya. Iltimos, men tugata olmagan ishni tugating». | Sizga posilka keldi. Ichida — eski laboratoriya guvohnomasi va bir qator yozuv:<br>«7-laboratoriya. Iltimos, men tugata olmagan ishni oxiriga yetkazing». |

### ch1 (26 values)

| Key | Lang | Old | New |
|---|---|---|---|
| `item.notebook.desc` | uz | Leyla Rahimovaning qoʻli bilan yozilgan laboratoriya jurnali. Bir sahifasi gʻalati darajada boʻm-boʻsh. | Leyla Rahimovaning qoʻli bilan yozilgan laboratoriya jurnali. Bir sahifasi negadir boʻm-boʻsh. |
| `item.uv_lamp_empty.desc` | ru | Фонарь с фиолетовым стеклом. Отсек для батареи пуст. | Лампа с фиолетовым стеклом. Отсек для батареи пуст. |
| `item.mirror_item.desc` | uz | Jez gardishli, mahkamlash qoziqchali koʻzgu. Koʻzgu tirgagiga mos keladi. | Orqasida oʻrnatish qoziqchasi boʻlgan jez gardishli koʻzgu. Koʻzgu tirgagiga mos keladi. |
| `doc.notebook.p3` | ru | Странд подарил каждому из нас свою шкатулку с шестернями.<br>«Поверни одно колесо — и сосед последует за ним, как люди», — сказал он.<br><br>В своей я храню батарею для лампы. | Странд подарил каждому из нас одну из своих шкатулок с шестернями.<br>«Поверни одно колесо — и сосед последует за ним, как люди», — сказал он.<br><br>В своей я храню батарею для лампы. |
| `doc.notebook.p3` | uz | Strand har birimizga oʻzining tishli gʻildirakli qutichasidan sovgʻa qilgan.<br>«Bitta gʻildirakni bursang, qoʻshnisi ham ergashadi — xuddi odamlardek», degandi u.<br><br>Men oʻzimnikida chirogʻim batareyasini saqlayman. | Strand har birimizga oʻzining tishli gʻildirakli qutichalaridan bittasini sovgʻa qilgan.<br>«Bitta gʻildirakni bursang, qoʻshnisi ham ergashadi — xuddi odamlardek», degandi u.<br><br>Men oʻzimnikida chirogʻim batareyasini saqlayman. |
| `doc.notebook.p8` | ru | Если кто-то читает это: Решётка должна проснуться ещё раз, чтобы открыть дверь.<br><br>Глаз двери откроется только перед знаком института, несомым светом Люмена.<br><br>Настрой её точно так, как писал Странд, — иначе она удержит и тебя. | Если кто-то читает это: Решётка должна проснуться ещё раз, чтобы открыть дверь.<br><br>Глаз двери открывается только для знака института, принесённого светом Люмена.<br><br>Настрой её точно так, как писал Странд, — иначе она удержит и тебя. |
| `obj.gearbox` | uz | Strandning tishli qutichasi | Strandning tishli gʻildirakli qutichasi |
| `obj.chalkboard` | uz | Strandning dokasi | Strandning doskasi |
| `obj.drawing` | uz | Bolalar rasmi: institut, quyosh, oq xalatli ayol | Bola chizgan rasm: institut, quyosh, oq xalatli ayol |
| `obj.emblem` | uz | Markazida uyasi bor institut belgisi | Markazida uyachasi bor institut belgisi |
| `obj.radiator` | ru | Холодная чугунная батарея | Холодный чугунный радиатор |
| `obj.radiator` | uz | Sovuq choʻyan batareya | Sovuq choʻyan radiator |
| `msg.main_locked` | uz | Asosiy richag mahkamlangan. | Asosiy dastak mahkamlangan. |
| `msg.radio_needs_valve` | uz | Qopqoq ostida lampa uchun boʻsh uya bor. | Qopqoq ostida lampa uchun boʻsh uyacha bor. |
| `msg.valve_installed` | uz | Lampa toʻq sariq rangda qizib ketdi. | Lampa qizib, toʻq sariq nur sochdi. |
| `msg.lens_in_socket` | uz | Linza uyaga aynan mos tushdi. | Linza uyachaga aynan mos tushdi. |
| `msg.projector_no_lens` | uz | Linza uyasi boʻsh. | Linza uyachasi boʻsh. |
| `hint.handle.3` | uz | Uzgich dastasini tanlang va 7-paneldagi asosiy richagga bosing. | Uzgich dastasini tanlang va 7-paneldagi asosiy dastakka bosing. |
| `hint.circuits.3` | uz | Faqat I, II va III ulagichlarni koʻtaring, soʻng asosiy richagni koʻtaring. | Faqat I, II va III ulagichlarni koʻtaring, soʻng asosiy dastakni koʻtaring. |
| `hint.tune.1` | uz | Strand mayogʻining toʻlqinini dokasida qoldirgan. | Strand mayogʻining toʻlqinini doskasida qoldirgan. |
| `hint.tune.2` | uz | Dokada λ = 41 m deb yozilgan. Radio shkalasi ham metrlarda belgilangan. | Doskada λ = 41 m deb yozilgan. Radio shkalasi ham metrlarda belgilangan. |
| `hint.record.2` | uz | Belgi markazidagi uyaga billur linza mos keladi. | Belgi markazidagi uyachaga billur linza mos keladi. |
| `hint.record.3` | uz | Soya belgini hosil qilib turganda billur linzani uyaga qoʻying. | Soya belgini hosil qilib turganda billur linzani uyachaga qoʻying. |
| `hint.retrieve_lens.3` | uz | Linzani qaytarib olish uchun uyaga bosing. | Linzani qaytarib olish uchun uyachaga bosing. |
| `hint.lens.1` | uz | Proyektor uyasi boʻsh. | Proyektor uyachasi boʻsh. |
| `hint.projector.3` | uz | Halqalarni toʻq qizil, kobalt, yashilga qoʻying — soʻng richagni torting. | Halqalarni toʻq qizil, kobalt, yashilga qoʻying — soʻng dastakni torting. |

### ch2 (28 values)

| Key | Lang | Old | New |
|---|---|---|---|
| `item.leyla_badge.name` | uz | Leylaning laboratoriya nishoni | Leylaning guvohnomasi |
| `item.strand_key.desc` | ru | Тяжёлая латунь со звездой. Он открывает зал Решётки. | Тяжёлая латунь со звездой. Он открывает Зал Решётки. |
| `item.leyla_key.desc` | ru | Простая сталь с полумесяцем. Он открывает кристальные хранилища. | Простая сталь с полумесяцем. Он открывает хранилища кристаллов. |
| `obj2.ledger` | uz | Daftarlar qatori | Hisob daftarlari qatori |
| `msg.c2_card_punched` | ru | Щёлк. Карта пробита. | Щёлк. Бланк пробит. |
| `msg.c2_card_returned` | uz | Kartani laganga qaytardingiz. | Kartani tokchaga qaytardingiz. |
| `msg.c2_canister_loaded` | ru | Карта отправляется в капсулу. | Бланк отправляется в капсулу. |
| `msg.c2_grille` | ru | Решётка открывается: два винта едва держатся. | Вентиляционная решётка открывается: два винта едва держатся. |
| `msg.c2_grille` | uz | Panjara ochildi: ikki vinti boʻshab qolgan ekan. | Shamollatish panjarasi ochildi: ikki vinti boʻshab qolgan ekan. |
| `msg.c2_ledger` | uz | Daftarning ichi kovak ekan. | Hisob daftarining ichi kovak ekan. |
| `msg.c2_projector_empty` | uz | Chiroq ekranga boʻm-boʻsh oq toʻrtburchak tushirdi. Proyektorda plyonka yoʻq. | Chiroq ekranga boʻm-boʻsh oq toʻrtburchak tushirdi. Proyektorda lenta yoʻq. |
| `cap2.goal` | uz | Choʻntagingizda Leylaning xodim nishoni bor. Uning shaxsiy ishi shu arxivning bir joyida boʻlishi kerak. | Choʻntagingizda Leylaning guvohnomasi bor. Uning shaxsiy ishi shu arxivning bir joyida boʻlishi kerak. |
| `doc2.file` | uz | Ishimni ochgan kishiga:<br>1996-yilda qaytib keldim. Institut muhrlangan, ammo arxiv hali nafas olyapti — quvurlar, chiroqlar, seyfxona.<br>Ovozimni qabul qilgichim eshita oladigan joyga yashirdim. Qabul qilgich 9-shkafchada.<br>— L.R. | Shaxsiy ishimni ochgan kishiga:<br>1996-yilda qaytib keldim. Institut muhrlangan, ammo arxiv hali nafas olyapti — quvurlar, chiroqlar, seyfxona.<br>Ovozimni qabul qilgichim eshita oladigan joyga yashirdim. Qabul qilgich 9-shkafchada.<br>— L.R. |
| `film.3` | uz | Qirq bir kishimiz. Butun xodimlar. | Qirq birtamiz. Barcha xodimlar. |
| `film.secret` | en | 13 November 1979. Strand, alone: "If the Array keeps them, I will be with them. Forgive me, Leyla." | 13 November 1979. Strand, alone: “If the Array keeps them, I will be with them. Forgive me, Leyla.” |
| `echo2.stacks` | uz | Ikki olim ochiq daftar ustida jimgina bahslashmoqda. | Ikki olim ochiq hisob daftari ustida jimgina bahslashmoqda. |
| `epi2.strand_key` | ru | Вы берёте ключ Странда. Где-то внизу ждёт зал Решётки. | Вы берёте ключ Странда. Где-то внизу ждёт Зал Решётки. |
| `epi2.leyla_key` | ru | Вы берёте ключ Лейлы. Её путь вниз ведёт через кристальные хранилища. | Вы берёте ключ Лейлы. Её путь вниз ведёт через хранилища кристаллов. |
| `hint.c2_catalogue.1` | uz | Leylaning nishonida raqam bor. Kartoteka gʻarbiy devor yonida, javonlar ortida. | Leylaning guvohnomasida raqam bor. Kartoteka gʻarbiy devor yonida, javonlar ortida. |
| `hint.c2_punch.2` | uz | Stansiya laganidan boʻsh karta oling va kartochkadagi kesiklarni teshgichda takrorlang. | Stansiya tokchasidan boʻsh karta oling va kartochkadagi kesiklarni teshgichda takrorlang. |
| `hint.c2_dispatch.3` | ru | Карту в капсулу, диск на книгу, потяните рычаг. | Бланк в капсулу, диск на книгу, потяните рычаг. |
| `hint.c2_take_file.2` | uz | Stansiyaning qabul laganini oching. | Stansiyaning qabul tokchasini oching. |
| `hint.c2_hunt.3` | ru | Решётка на западной стене, полый гроссбух на стеллаже, люк у читального стола. | Вентиляционная решётка на западной стене, полый гроссбух на стеллаже, люк у читального стола. |
| `hint.c2_hunt.3` | uz | Gʻarbiy devordagi panjara, javondagi kovak daftar, mutolaa stoli yonidagi lyuk. | Gʻarbiy devordagi shamollatish panjarasi, javondagi kovak hisob daftari, mutolaa stoli yonidagi lyuk. |
| `hint.c2_tape.3` | uz | Tezlik 4.75, gʻaltakni magnitofonga qoʻying, «Play»ni bosing. Uchalasi uchun. | Tezlik 4.75, gʻaltakni magnitofonga qoʻying, ijro tugmasini bosing. Uchalasi uchun. |
| `hint.c2_booth.2` | en | "The booth answers to my reels, in the order I made them." Count each reel's clicks. | “The booth answers to my reels, in the order I made them.” Count each reel's clicks. |
| `hint.c2_record_sign.1` | en | "The crystal remembers what falls on it." | “The crystal remembers what falls on it.” |
| `hint.c2_finale.2` | ru | Ключ Странда открывает зал Решётки, ключ Лейлы — кристальные хранилища. | Ключ Странда открывает Зал Решётки, ключ Лейлы — хранилища кристаллов. |

### ch3 (13 values)

| Key | Lang | Old | New |
|---|---|---|---|
| `item.strand_key.desc3` | en | Heavy brass with a star. The tag reads: "For the Choir." | Heavy brass with a star. The tag reads: “For the Choir.” |
| `item.leyla_key.desc3` | en | Plain steel with a crescent. The tag reads: "For the Nursery." | Plain steel with a crescent. The tag reads: “For the Nursery.” |
| `item.ecg_strip.desc` | uz | Strandning yurak yozuvi, 1977. Ruchka bilan uchta qavs: quyosh, oy, yulduz. | Strandning kardiogrammasi, 1977. Ruchka bilan uchta qavs: quyosh, oy, yulduz. |
| `obj3.port` | ru | Кристальное смотровое окно | Кристаллическое смотровое окно |
| `obj3.shutter` | ru | Кристальная заслонка | Кристаллическая заслонка |
| `msg.c3_key_trapped` | ru | Ключ заперт. Сначала поверните рубильник. | Ключ заперт. Сначала переключите изолятор. |
| `cap3.secret` | en | Leyla, 1998, kneels by the wall and lays her hand on the forty-second socket. "Keep a place for me." | Leyla, 1998, kneels by the wall and lays her hand on the forty-second socket. “Keep a place for me.” |
| `intro3.strand_key` | en | The freight lift sinks below the archive. The tag on Strand's key reads: "For the Choir." | The freight lift sinks below the archive. The tag on Strand's key reads: “For the Choir.” |
| `intro3.leyla_key` | en | The freight lift sinks below the archive. The tag on Leyla's key reads: "For the Nursery." | The freight lift sinks below the archive. The tag on Leyla's key reads: “For the Nursery.” |
| `doc3.growth_log` | uz | Oxirgi urugʻ, kesimi. Uchdan bir burilish bilan chizilgan. | Oxirgi urugʻ, kesimi. Uchdan bir aylanma burilgan holda chizilgan. |
| `hint.c3_interlock.1` | uz | Strand uzgichlar xonasi kalitlar bilan ishlaydi. | Strandning uzgichlar xonasi kalitlar bilan ishlaydi. |
| `hint.c3_heart.2` | en | "My heart keeps the count." Look at the strip on his lamp. | “My heart keeps the count.” Look at the strip on his lamp. |
| `hint.c3_startup.2` | ru | Наблюдайте за оператором через все три кристальных окна. Счётчик показывает шаг. | Наблюдайте за оператором через все три кристаллических окна. Счётчик показывает шаг. |

## Deliberately left alone
| Text | Why |
|---|---|
| Every level-3 hint value, `sym.*`, `hint.c3_pos.*`, 0-3-1-7, 41 m, 4.75, 04 / 1– / 17, locker 9, «longest shadow first», «a third of a turn», «smallest first», «left/right» | Puzzle answers and clues must stay language-neutral and identical (`docs/VARIANTS.md`). Only pure wording around them was touched. |
| «Решётка» / «Panjara» for the Array | Established lore name in both languages («решётка»/«panjara» = lattice, the ring array). The collision with the vent grille was solved by qualifying the grille, not by renaming the Array. |
| «Питомник» / «Koʻchatxona» for the Nursery | Keeps the EN pun: crystals are *grown* from seeds there. |
| UZ «murvat» for knob | Natural spoken Uzbek for a turning knob (radio murvati); the dictionary sense «screw» does not confuse here. |
| UZ «shkafcha» for locker | «javon» is already the stacks and cabinets in the same room; «shkafcha» keeps lockers distinct. |
| RU «4.75» with a dot | Matches the number printed on the reel art, which the player must copy onto the speed selector. |
| «Davom etish» / «Продолжить» for both Continue and Resume | Both buttons mean the same action; the EN pair is a stylistic split. |
| EN British spelling (labelled, centred, coloured, metres, catalogue) | It dominates the corpus; no American forms were found. |
| RU «Яснее» / UZ «Aniqroq» on the stronger-hint button | Short, fits the 340 px button in all three languages. |
| RU «Подсказок» as the summary column label | It stands above a bare number (Подсказок / 3). |
| `obj2.sign_catalogue` KARTOTEKA / КАРТОТЕКА | A painted sign in the 3D room; upper case is deliberate. |
| `doc.notebook.p5` empty in all languages | By design: the UV page, filled from `doc.notebook.p5_uv` and the symbols. |

## For the owner to decide
1. **UZ "progress"**: now «Oʻyin saqlandi», «Saqlangan oʻyinni oʻchirish», «Joriy oʻyin oʻchib ketadi» (game saved / delete the saved
   game). If you prefer the literal «jarayon», it is a four-key change in `strings_core.py`.
2. **UZ badge**: «guvohnoma» (ID with a staff number) replaced «nishon» (a pin). Both are heard; pick one and I will align the store texts too.
3. **UZ tray**: «tokcha» replaced «lagan». «Lotok» is the other common choice.
4. **UZ ledger**: «hisob daftari». «Qayd daftari» is the alternative if you prefer "register".
5. **UZ chalkboard**: «doska». «Yozuv taxtasi» is the purer literary form (longer; the hint `tune.2` would grow by 10 characters).
6. **RU vaults**: «хранилища кристаллов» for the crystal vaults; «кристаллические хранилища» if you want "made of crystal".
7. `ui.delete_save` is not yet used by any scene; the UZ label «Saqlangan oʻyinni oʻchirish» (27 characters) should be checked
   when the settings redesign places it.
