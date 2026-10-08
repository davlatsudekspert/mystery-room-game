# -*- coding: utf-8 -*-
"""Three-level hints per goal (game/src/rooms/lab7/lab7_hints.gd). Level 1 nudge, 2 where, 3 answer."""

H = {
"notebook": [
    ("Someone left a notebook behind.", "Кто-то оставил блокнот.", "Kimdir daftar qoldirib ketgan."),
    ("Look at the desk under the window.", "Посмотрите на стол под окном.", "Deraza ostidagi stolga qarang."),
    ("Tap the desk, then take Leyla's notebook.", "Нажмите на стол и возьмите блокнот Лейлы.", "Stolga bosing va Leylaning daftarini oling."),
],
"drawer": [
    ("Leyla wrote about a moment she must never forget.", "Лейла писала о мгновении, которое нельзя забыть.", "Leyla hech qachon unutmasligi kerak boʻlgan lahza haqida yozgan."),
    ("The clock on her desk stopped at that very moment.", "Часы на её столе остановились именно в это мгновение.", "Uning stolidagi soat aynan oʻsha lahzada toʻxtagan."),
    ("Set the drawer wheels to 0-3-1-7.", "Установите колёса ящика на 0-3-1-7.", "Tortma gʻildiraklarini 0-3-1-7 ga qoʻying."),
],
"take_lamp": [
    ("The drawer is open.", "Ящик открыт.", "Tortma ochiq."),
    ("Something is lying inside the drawer.", "В ящике что-то лежит.", "Tortma ichida nimadir yotibdi."),
    ("Tap the lamp inside the drawer to take it.", "Нажмите на лампу в ящике, чтобы взять её.", "Olish uchun tortmadagi chiroqqa bosing."),
],
"gearbox": [
    ("Strand's box: each knob drags a neighbour along.", "Шкатулка Странда: каждая ручка тянет за собой соседа.", "Strandning qutichasi: har bir murvat qoʻshnisini ham aylantiradi."),
    ("Bring every gear's pointer to the mark at the back. Count how far each one is.", "Наведите стрелки всех шестерней на метку сзади. Посчитайте, сколько шагов до неё.", "Har bir gʻildirak koʻrsatkichini orqadagi belgiga keltiring. Har biri necha qadam uzoqligini sanang."),
    ("Press the left knob 2 times, the middle knob 1 time, the right knob 3 times.", "Нажмите левую ручку 2 раза, среднюю — 1 раз, правую — 3 раза.", "Chap murvatni 2 marta, oʻrtadagini 1 marta, oʻngdagini 3 marta bosing."),
],
"take_cell": [
    ("The gear box is open.", "Шкатулка открыта.", "Quticha ochiq."),
    ("Leyla kept something for her lamp inside it.", "Лейла хранила в ней кое-что для лампы.", "Leyla uning ichida chirogʻi uchun nimanidir saqlagan."),
    ("Tap the battery cell inside the box.", "Нажмите на батарею в шкатулке.", "Quticha ichidagi batareyaga bosing."),
],
"lamp": [
    ("The lamp is dead.", "Лампа не работает.", "Chiroq ishlamayapti."),
    ("Its battery bay fits something you carry.", "К её отсеку подойдёт кое-что из ваших вещей.", "Uning batareya joyiga yoningizdagi bir narsa mos keladi."),
    ("Select the UV lamp, press Combine, then tap the battery cell.", "Выберите УФ-лампу, нажмите «Объединить», затем батарею.", "UB chiroqni tanlang, «Birlashtirish»ni bosing, soʻng batareyani tanlang."),
],
"cipher": [
    ("One page of the notebook looks empty.", "Одна страница блокнота кажется пустой.", "Daftarning bir sahifasi boʻsh koʻrinadi."),
    ("Some inks only show under ultraviolet light.", "Некоторые чернила видны только в ультрафиолете.", "Ayrim siyohlar faqat ultrabinafsha nurda koʻrinadi."),
    ("Open the notebook at the blank page and press the UV button.", "Откройте блокнот на пустой странице и нажмите кнопку УФ.", "Daftarni boʻsh sahifada oching va UB tugmasini bosing."),
],
"safe": [
    ("The symbols on the page stand for numbers.", "Символы на странице означают числа.", "Sahifadagi belgilar sonlarni bildiradi."),
    ("The poster on the wall counts dots beside each symbol.", "Плакат на стене показывает число точек рядом с каждым символом.", "Devordagi plakat har bir belgi yonida nuqtalar sonini koʻrsatadi."),
    ("Enter 7-2-9-4 on the safe keypad, then press the enter key (bottom right).", "Введите на сейфе 7-2-9-4 и нажмите клавишу ввода (внизу справа).", "Seyf tugmalarida 7-2-9-4 ni tering va kiritish tugmasini bosing (pastki oʻngda)."),
],
"take_safe": [
    ("The safe is open.", "Сейф открыт.", "Seyf ochiq."),
    ("Everything inside will be useful.", "Всё, что внутри, пригодится.", "Ichidagi hamma narsa asqotadi."),
    ("Take the key, the lens, the letter and the valve from the safe.", "Возьмите из сейфа ключ, линзу, письмо и лампу.", "Seyfdan kalit, linza, maktub va radiolampani oling."),
],
"compartment": [
    ("“Where only my lamp can show the way.”", "«Туда, куда дорогу укажет только моя лампа».", "«Faqat chirogʻim yoʻl koʻrsata oladigan joyga»."),
    ("Shine the UV lamp along Leyla's desk.", "Посветите УФ-лампой вдоль стола Лейлы.", "Leylaning stoli boʻylab UB chiroq bilan yoriting."),
    ("Shine UV on the right side of the desk, then press the carved rosette.", "Посветите УФ на правую боковину стола и нажмите на резную розетку.", "Stolning oʻng yon tomonini UB bilan yoriting va oʻyma gul naqshni bosing."),
],
"key": [
    ("A keyhole has appeared.", "Появилась замочная скважина.", "Kalit teshigi paydo boʻldi."),
    ("The safe held a small brass key.", "В сейфе был маленький латунный ключ.", "Seyfda kichkina jez kalit bor edi."),
    ("Select the brass key and tap the keyhole in the desk.", "Выберите латунный ключ и нажмите на скважину в столе.", "Jez kalitni tanlang va stoldagi kalit teshigiga bosing."),
],
"take_handle": [
    ("The hidden compartment is open.", "Тайник открыт.", "Yashirin boʻlma ochiq."),
    ("Leyla hid something important inside.", "Лейла спрятала там нечто важное.", "Leyla uning ichiga muhim narsa yashirgan."),
    ("Take the breaker handle (and the photograph) from the compartment.", "Возьмите из тайника рукоять рубильника (и фотографию).", "Boʻlmadan uzgich dastasini (va suratni) oling."),
],
"handle": [
    ("The main breaker can't be moved.", "Главный рубильник не двигается.", "Asosiy uzgich qimirlamaydi."),
    ("Its handle is missing — you have it.", "У него нет рукояти — она у вас.", "Uning dastasi yoʻq — u sizda."),
    ("Select the breaker handle and tap the main lever on Panel 7.", "Выберите рукоять и нажмите на главный рычаг щита 7.", "Uzgich dastasini tanlang va 7-paneldagi asosiy richagga bosing."),
],
"circuits": [
    ("Leyla listed which lines must be live.", "Лейла записала, какие линии должны быть под током.", "Leyla qaysi liniyalar tok ostida boʻlishi kerakligini yozib qoldirgan."),
    ("LOCK, LIGHT and ARRAY on; VENT off. Follow the copper traces from each switch to the lamps.", "ЗАМОК, СВЕТ и РЕШЁТКА — вкл., ВЕНТИЛЯЦИЯ — выкл. Проследите медные дорожки от переключателей к лампам.", "QULF, YORUGʻLIK va PANJARA yoqilgan, SHAMOLLATISH oʻchiq. Har bir ulagichdan lampalargacha mis yoʻlakchalarni kuzating."),
    ("Raise switches I, II and III only, then raise the main lever.", "Поднимите только переключатели I, II и III, затем главный рычаг.", "Faqat I, II va III ulagichlarni koʻtaring, soʻng asosiy richagni koʻtaring."),
],
"valve": [
    ("The radio is silent.", "Радио молчит.", "Radio jim."),
    ("Open its hatch: a valve is missing.", "Откройте крышку: не хватает лампы.", "Qopqogʻini oching: lampa yetishmayapti."),
    ("Select the radio valve from the safe and tap the radio.", "Выберите радиолампу из сейфа и нажмите на радио.", "Seyfdan olingan radiolampani tanlang va radioga bosing."),
],
"tune": [
    ("Strand left his beacon's band on his board.", "Странд оставил на доске волну своего маяка.", "Strand mayogʻining toʻlqinini dokasida qoldirgan."),
    ("The chalkboard says λ = 41 m. The radio dial is marked in metres too.", "На доске написано λ = 41 м. Шкала радио тоже размечена в метрах.", "Dokada λ = 41 m deb yozilgan. Radio shkalasi ham metrlarda belgilangan."),
    ("Drag the knob (or tap its left side) until the needle sits on 41 m.", "Крутите ручку пальцем (или нажимайте её левую сторону), пока стрелка не встанет на 41 м.", "Murvatni barmoq bilan buring (yoki chap tomoniga bosing), koʻrsatkich 41 m ga kelsin."),
],
"books": [
    ("The beacon repeats three numbers.", "Маяк повторяет три числа.", "Mayoq uchta sonni takrorlaydi."),
    ("Count its pulses: 2, 6, 3. Leyla's encyclopedia “remembers them”.", "Посчитайте импульсы: 2, 6, 3. Энциклопедия Лейлы «их помнит».", "Impulslarni sanang: 2, 6, 3. Leylaning ensiklopediyasi «ularni eslaydi»."),
    ("Pull volumes II, VI, then III.", "Потяните тома II, VI, затем III.", "II, VI, soʻng III jildlarni torting."),
],
"shadow": [
    ("The wall shows the Institute's mark.", "На стене — знак института.", "Devorda institut belgisi bor."),
    ("Make the sculpture's shadow draw it: a full ring and a straight line.", "Сделайте так, чтобы тень скульптуры нарисовала его: полное кольцо и прямую линию.", "Haykalcha soyasi uni chizsin: toʻliq halqa va toʻgʻri chiziq."),
    ("Turn the ring until it faces the lamp, and the rod until it stands upright.", "Поворачивайте кольцо, пока оно не встанет к лампе, а стержень — пока не станет вертикальным.", "Halqani chiroqqa yuzlanguncha, sterjenni esa tik turguncha buring."),
],
"take_mirror": [
    ("The cabinet is open.", "Шкафчик открыт.", "Javoncha ochiq."),
    ("Strand's mirror is inside.", "Внутри — зеркало Странда.", "Ichida Strandning koʻzgusi bor."),
    ("Tap the round mirror to take it.", "Нажмите на круглое зеркало, чтобы взять его.", "Olish uchun dumaloq koʻzguga bosing."),
],
"record": [
    ("“The crystal remembers what falls on it.”", "«Кристалл помнит то, что на него падает».", "«Billur ustiga tushgan narsani eslab qoladi»."),
    ("The mark's socket fits the crystal lens.", "Гнездо в центре знака подходит для кристаллической линзы.", "Belgi markazidagi uyaga billur linza mos keladi."),
    ("Place the crystal lens in the socket while the shadow forms the mark.", "Вставьте линзу в гнездо, пока тень образует знак.", "Soya belgini hosil qilib turganda billur linzani uyaga qoʻying."),
],
"retrieve_lens": [
    ("The crystal has remembered the mark.", "Кристалл запомнил знак.", "Billur belgini eslab qoldi."),
    ("Now it must travel with the light.", "Теперь он должен отправиться вместе со светом.", "Endi u yorugʻlik bilan birga yoʻlga chiqishi kerak."),
    ("Tap the socket to take the lens back.", "Нажмите на гнездо, чтобы забрать линзу.", "Linzani qaytarib olish uchun uyaga bosing."),
],
"lens": [
    ("The projector's socket is empty.", "Гнездо проектора пусто.", "Proyektor uyasi boʻsh."),
    ("The crystal lens fits it.", "Туда подходит кристаллическая линза.", "Unga billur linza mos keladi."),
    ("Select the crystal lens and tap the projector.", "Выберите линзу и нажмите на проектор.", "Billur linzani tanlang va proyektorga bosing."),
],
"projector": [
    ("Strand's letter tells how to tune it.", "Письмо Странда говорит, как его настроить.", "Strandning maktubi uni qanday sozlashni aytadi."),
    ("“The heaviest first.” Compare the samples' density (ρ).", "«Начиная с самого тяжёлого». Сравните плотность (ρ) образцов.", "«Eng ogʻiridan boshlab». Namunalarning zichligini (ρ) solishtiring."),
    ("Set the rings to crimson, cobalt, green — then pull the lever.", "Установите кольца: малиновый, кобальтовый, зелёный — и потяните рычаг.", "Halqalarni toʻq qizil, kobalt, yashilga qoʻying — soʻng richagni torting."),
],
"mount_mirror": [
    ("One mirror stand is empty.", "Одна зеркальная стойка пуста.", "Bitta koʻzgu tirgagi boʻsh."),
    ("You carry Strand's round mirror.", "У вас есть круглое зеркало Странда.", "Sizda Strandning dumaloq koʻzgusi bor."),
    ("Select the round mirror and tap the empty stand near the door.", "Выберите зеркало и нажмите на пустую стойку у двери.", "Dumaloq koʻzguni tanlang va eshik yonidagi boʻsh tirgakka bosing."),
],
"mirrors": [
    ("The door has a glass eye made for light.", "У двери есть стеклянный глаз — для света.", "Eshikning yorugʻlik uchun shisha koʻzi bor."),
    ("Each tap turns a mirror one notch (45°). Guide the beam around the room.", "Каждое нажатие поворачивает зеркало на одно деление (45°). Проведите луч по комнате.", "Har bosish koʻzguni bir pogʻona (45°) buradi. Nurni xona boʻylab yoʻnaltiring."),
    ("First stand: send the beam toward the window wall. Second stand: send it into the door's eye.", "Первая стойка: направьте луч к стене с окном. Вторая — в глаз двери.", "Birinchi tirgak: nurni deraza devoriga yoʻnaltiring. Ikkinchisi: eshik koʻziga."),
],
"finale": [
    ("The way is open.", "Путь открыт.", "Yoʻl ochiq."),
    ("Leyla's light is fading.", "Свет Лейлы угасает.", "Leylaning nuri soʻnmoqda."),
    ("Make your choice.", "Сделайте выбор.", "Tanlov qiling."),
],
}
