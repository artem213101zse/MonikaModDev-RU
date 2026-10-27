# Подарки MAS — где искать и полный список

## Почему в `git diff` не видно «весь список»

Перевод менял **реплики Моники**, а не имена файлов. Строки вроде `"coffee"`, `"blackribbon"` в `addReaction(...)` — это **ключи** (имя файла без `.gift`). Они специально остаются латиницей: так игра находит `characters/coffee.gift`.

Полный каталог для игрока уже есть в коде MAS OS:

- `mas_os_gifts.rpy` → словари `GIFT_TITLES` / `GIFT_HINTS` / `GIFT_IMG`
- Реакции и регистрация stock-подарков → `zz_reactions.rpy` (`addReaction`)
- Напитки после подарка → `zz_consumables.rpy`
- Спрайтпаки (одежда/ACS из JSON) → `zz_spritejsons.rpy` + `mod_assets/**/*.json` (поле `giftname`)

## Как работает подарок

1. Создаёшь пустой файл `characters/<имя>.gift` (или через склад MAS OS).
2. При заходе/приветствии `mas_filereacts` сканирует `characters/`.
3. Если имя есть в `filereact_map` (из `addReaction`) — очередь специальной реплики.
4. Если имя есть в JSON спрайтпака — разблокировка спрайта + общая/спец. реакция.
5. Иначе — общая реакция «неизвестный подарок».
6. Файл `.gift` потом удаляется; affection с дневным лимитом.

## Stock-подарки (вшитые реакции в `zz_reactions.rpy`)

| Файл `.gift` | Название (RU) | Label реакции | Заметка |
|---|---|---|---|
| `coffee.gift` | Кофе | `mas_reaction_gift_coffee` | Кофе. Напиток; можно дарить повторно, пока не заполнится запас. |
| `hotchocolate.gift` | Горячий шоколад | `mas_reaction_hotchocolate` | Горячий шоколад. Напиток, особенно к холодному сезону. |
| `justmonikathermos.gift` | Термос | `mas_reaction_gift_thermos_mug` | Термос Just Monika. Аксессуар на стол. |
| `quetzalplushie.gift` | Кетцаль | `mas_reaction_quetzal_plush` | Плюшевый кетцаль. Один раз; любимый «питомец». |
| `promisering.gift` | Кольцо | `mas_reaction_promisering` | Кольцо-обещание. Принимает только с привязанности «Влюблённая» и выше. |
| `cupcake.gift` | Капкейк | `mas_reaction_cupcake` | Капкейк. Нейтральный подарок, можно дарить в любой день. |
| `candy.gift` | Конфеты | `mas_reaction_candy` | Конфеты. В коде реакция на Хэллоуин; в другой сезон может пройти как обычный подарок. |
| `candycorn.gift` | Candy corn | `mas_reaction_candycorn` | Кукурузные конфеты. Плохой подарок — Моника не любит. |
| `fudge.gift` | Фадж | `mas_reaction_fudge` | Шоколадный фадж. |
| `christmascookies.gift` | Печенье | `mas_reaction_christmascookies` | Рождественское печенье. Сезон D25; иначе может быть обычной реакцией. |
| `candycane.gift` | Трость | `mas_reaction_candycane` | Карамельная трость. Сезон D25. |
| `roses.gift` | Розы | `mas_reaction_gift_roses` | Розы. Хорошо на свидание / 14 февраля. |
| `chocolates.gift` | Шоколад | `mas_reaction_gift_chocolates` | Коробка шоколадных конфет. |
| `noudeck.gift` | Колода NOU | `mas_reaction_gift_noudeck` | Колода карт NOU. Открывает мини-игру, если ещё не открыта. |
| `blackribbon.gift` | Чёрная лента | `mas_reaction_blackribbon` | Чёрная лента для волос. |
| `blueribbon.gift` | Синяя лента | `mas_reaction_blueribbon` | Синяя лента. |
| `darkpurpleribbon.gift` | Тёмно-фиолетовая | `mas_reaction_darkpurpleribbon` | Тёмно-фиолетовая лента. |
| `emeraldribbon.gift` | Изумрудная лента | `mas_reaction_emeraldribbon` | Изумрудная лента. |
| `grayribbon.gift` | Серая лента | `mas_reaction_grayribbon` | Серая лента. |
| `greenribbon.gift` | Зелёная лента | `mas_reaction_greenribbon` | Зелёная лента. |
| `lightpurpleribbon.gift` | Светло-фиолетовая | `mas_reaction_lightpurpleribbon` | Светло-фиолетовая лента. |
| `peachribbon.gift` | Персиковая лента | `mas_reaction_peachribbon` | Персиковая лента. |
| `pinkribbon.gift` | Розовая лента | `mas_reaction_pinkribbon` | Розовая лента. |
| `platinumribbon.gift` | Платиновая лента | `mas_reaction_platinumribbon` | Платиновая лента. |
| `redribbon.gift` | Красная лента | `mas_reaction_redribbon` | Красная лента. |
| `rubyribbon.gift` | Рубиновая лента | `mas_reaction_rubyribbon` | Рубиновая лента. |
| `sapphireribbon.gift` | Сапфировая лента | `mas_reaction_sapphireribbon` | Сапфировая лента. |
| `silverribbon.gift` | Серебряная лента | `mas_reaction_silverribbon` | Серебряная лента. |
| `tealribbon.gift` | Бирюзовая лента | `mas_reaction_tealribbon` | Бирюзовая лента. |
| `yellowribbon.gift` | Жёлтая лента | `mas_reaction_yellowribbon` | Жёлтая лента. |

## Каталог MAS OS (`mas_os_gifts.rpy`) — всё, что можно создать из UI

Сюда входят stock-подарки **и** вещи, которые обычно открываются праздниками/affection (платья, бельё, заколки и т.д.). Файл `.gift` с таким именем всё равно можно положить вручную.

| Файл `.gift` | Название | Подсказка |
|---|---|---|
| `coffee.gift` | Кофе | Кофе. Напиток; можно дарить повторно, пока не заполнится запас. |
| `hotchocolate.gift` | Горячий шоколад | Горячий шоколад. Напиток, особенно к холодному сезону. |
| `justmonikathermos.gift` | Термос | Термос Just Monika. Аксессуар на стол. |
| `quetzalplushie.gift` | Кетцаль | Плюшевый кетцаль. Один раз; любимый «питомец». |
| `promisering.gift` | Кольцо | Кольцо-обещание. Принимает только с привязанности «Влюблённая» и выше. |
| `cupcake.gift` | Капкейк | Капкейк. Нейтральный подарок, можно дарить в любой день. |
| `candy.gift` | Конфеты | Конфеты. В коде реакция на Хэллоуин; в другой сезон может пройти как обычный подарок. |
| `candycorn.gift` | Candy corn | Кукурузные конфеты. Плохой подарок — Моника не любит. |
| `fudge.gift` | Фадж | Шоколадный фадж. |
| `christmascookies.gift` | Печенье | Рождественское печенье. Сезон D25; иначе может быть обычной реакцией. |
| `candycane.gift` | Трость | Карамельная трость. Сезон D25. |
| `roses.gift` | Розы | Розы. Хорошо на свидание / 14 февраля. |
| `chocolates.gift` | Шоколад | Коробка шоколадных конфет. |
| `noudeck.gift` | Колода NOU | Колода карт NOU. Открывает мини-игру, если ещё не открыта. |
| `blackribbon.gift` | Чёрная лента | Чёрная лента для волос. |
| `blueribbon.gift` | Синяя лента | Синяя лента. |
| `darkpurpleribbon.gift` | Тёмно-фиолетовая | Тёмно-фиолетовая лента. |
| `emeraldribbon.gift` | Изумрудная лента | Изумрудная лента. |
| `grayribbon.gift` | Серая лента | Серая лента. |
| `greenribbon.gift` | Зелёная лента | Зелёная лента. |
| `lightpurpleribbon.gift` | Светло-фиолетовая | Светло-фиолетовая лента. |
| `peachribbon.gift` | Персиковая лента | Персиковая лента. |
| `pinkribbon.gift` | Розовая лента | Розовая лента. |
| `platinumribbon.gift` | Платиновая лента | Платиновая лента. |
| `redribbon.gift` | Красная лента | Красная лента. |
| `rubyribbon.gift` | Рубиновая лента | Рубиновая лента. |
| `sapphireribbon.gift` | Сапфировая лента | Сапфировая лента. |
| `silverribbon.gift` | Серебряная лента | Серебряная лента. |
| `tealribbon.gift` | Бирюзовая лента | Бирюзовая лента. |
| `yellowribbon.gift` | Жёлтая лента | Жёлтая лента. |
| `blackdress.gift` | Чёрное платье |  |
| `blackpinkdress.gift` | Чёрно-розовое платье |  |
| `marisa.gift` | Костюм Марисы |  |
| `new_years_dress.gift` | Новогоднее платье |  |
| `nou_shirt.gift` | Футболка NOU |  |
| `rin.gift` | Костюм Рин |  |
| `santa.gift` | Костюм Санты |  |
| `santa_lingerie.gift` | Бельё Санты |  |
| `spider_lingerie.gift` | Паучье бельё |  |
| `sundress_white.gift` | Белый сарафан |  |
| `vday_lingerie.gift` | Бельё на 14 февраля |  |
| `blazerless.gift` | Форма без пиджака |  |
| `diamond_necklace_pink.gift` | Розовое колье |  |
| `earrings_diamond_pink.gift` | Розовые серьги |  |
| `grayhearts_hairclip.gift` | Заколка (сердца) |  |
| `holly_hairclip.gift` | Заколка (остролист) |  |
| `marisa_witchhat.gift` | Шляпа ведьмы |  |
| `musicnote_necklace_gold.gift` | Колье-нота |  |
| `pinkdiamonds_hairclip.gift` | Заколка (ромбы) |  |
| `ribbon_wine.gift` | Винная лента |  |
| `ribbon_black_gray.gift` | Чёрно-серая лента |  |
| `ribbon_black_pink.gift` | Чёрно-розовая лента |  |
| `ear_rose.gift` | Роза за ухом |  |
| `flower_crown.gift` | Цветочный венок |  |
| `braided.gift` | Косы |  |
| `down.gift` | Распущенные волосы |  |
| `downtiedstrand.gift` | Хвост с прядью |  |

## Спрайтпаки (JSON)

В этой копии `mod_assets` JSON с `giftname` не разобраны / пусто. Смотри `spritepacks/released/**/gifts/*.gift` и JSON спрайтпаков: имя файла без расширения = giftname.

В `spritepacks/` сейчас **135** готовых `.gift` (имена файлов = ключи).


## Готовые `.gift` из `spritepacks/` (имя файла = ключ)

Всего уникальных имён: **135**. Это доп. одежда/ACS из паков; реакция чаще общая JSON-реакция, пока нет спец. label.

| Файл |
---|

```
2bcosplay.gift
8blueribbon.gift
8emeraldribbon.gift
8purpleribbon.gift
8redribbon.gift
8whiteribbon.gift
amdekamberribbon.gift
anchor_necklace.gift
animalcrossing_necklace.gift
bathairclip.gift
beigeturtlenecksweater.gift
bisexualpridethemedribbon.gift
blackandwhiteribbon.gift
blackandwhitestripedpullover.gift
blackbow.gift
blacksilverpiercings.gift
blueandwhitestripedribbon.gift
bluebunnyscrunchie.gift
blueshirt.gift
bluesweatervest.gift
bluetwinribbon.gift
braletteredruffles.gift
bronzeribbon.gift
brownribbon.gift
brownwinterjacket.gift
buttonupflowered.gift
cactus_necklace.gift
cherryhairclip.gift
chokerchainsilver.gift
chokerdaisywhite.gift
chokeremeraldgreen.gift
chokerglitterbeadsilver.gift
chokerribbonred.gift
chokerrufflesred.gift
chokersilkwhite.gift
chokerspikedstar.gift
chokerspiralblack.gift
chokerthreadribbon.gift
coffeeribbon.gift
crescentmoonhairclip.gift
danglyearrings.gift
dressdarkbluesparkle.gift
floweredchoker.gift
gameboygreenribbon.gift
ghosthairclip.gift
goldchain_necklace.gift
goldhoopearrings.gift
goldribbon.gift
gradientribbon.gift
greendress.gift
greenhoodie.gift
greentwinribbon.gift
hatsunemikucosplay.gift
heartchoker.gift
heartcutbikiniblack.gift
heartcutbikinigreen.gift
heartcutbikinipink.gift
heartcutbikinipurple.gift
heartcutbikiniwhite.gift
heartcutbikiniyellow.gift
hearthairclip.gift
hotpinkribbon.gift
lilacribbon.gift
limegreenribbon.gift
lowpolygradientribbon.gift
miniblackribbon.gift
minidarkpinkribbon.gift
minigrayribbon.gift
miniorangeribbon.gift
minipalegreenribbon.gift
minipinkribbon.gift
minipurpleribbon.gift
miniredribbon.gift
miniroyalblueribbon.gift
miniskyblueribbon.gift
miniwhiteribbon.gift
miniyellowribbon.gift
musicnoteearrings.gift
musicnotehairclip.gift
navyblueribbon.gift
orangeribbon.gift
pearlearrings.gift
pinkandwhitestripedribbon.gift
pinkflower.gift
pinkkimono.gift
pinkshirt.gift
pinktwinribbon.gift
pumpkinhairclip.gift
putonahappyfaceshirt.gift
rainbowgradientribbon.gift
resthereshirt.gift
royalpurpleribbon.gift
sakuyaizayoicosplay.gift
shellbikini.gift
shoulderlesssweater.gift
shuchiinacademyuniform.gift
simplechoker.gift
skyblueribbon.gift
sleevelessturtleneckblack.gift
snailshell_necklace.gift
star_necklace.gift
starryblackskyribbon.gift
starryredskyribbon.gift
stypeblackribbon.gift
stypeblueribbon.gift
stypedarkpurpleribbon.gift
stypedefribbon.gift
stypeemeraldribbon.gift
stypegrayribbon.gift
stypegreenribbon.gift
stypelightpurpleribbon.gift
stypepeachribbon.gift
stypepinkribbon.gift
stypeplatinumribbon.gift
styperedribbon.gift
styperubyribbon.gift
stypesapphireribbon.gift
stypesilverribbon.gift
stypetealribbon.gift
stypewineribbon.gift
stypeyellowribbon.gift
sunflower_necklace.gift
supergameboygreenribbon.gift
tanktop.gift
tiedcroptopblack.gift
tiedcroptopwhite.gift
transgenderpridethemedribbon.gift
triforce_necklace.gift
tshirtjurassicpark.gift
tshirtjurassicworld.gift
vcutcrossedstrapstanktopwhite.gift
whiteandnavybluedress.gift
whiteonredpolkadotribbon.gift
wineasymmetricalpullover.gift
yellowtwinribbon.gift
```

## Быстрая проверка перевода

```bash
git diff -- Monika\ After\ Story/game/zz_reactions.rpy
git diff -- Monika\ After\ Story/game/zz_consumables.rpy
# список ключей stock:
rg "addReaction\(" "Monika After Story/game/zz_reactions.rpy"
# каталог названий:
rg "GIFT_TITLES|GIFT_HINTS" "Monika After Story/game/mas_os_gifts.rpy"
```

## Файлы этого прохода

- `zz_reactions.rpy` — реплики на подарки
- `zz_consumables.rpy` — реплики при питье/еде
- `mas_os_gifts.rpy` — **не** переводился сейчас: каталог уже на русском

