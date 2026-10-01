# MAS BIOS

Офлайн WebView до Python. Источник страницы: эти три файла.

Сборка APK — из **MAS Ren'Py** `Documents/renpy-7.4.11-sdk`, не из лаборатории.
После правок HTML/Java:

```
python tools/sync_mas_bios.py
```

Скрипт кладёт страницу в `rapt/project/app/src/main/assets/www` и
`renpyandroid/.../res/raw`, Java и res — в модуль `renpyandroid`.
На телефоне Java копирует байты в `getFilesDir()/bios_www/` и грузит `file://`.

Превью без телефона: открой `index.html` в браузере. Без Java кнопки пишут в журнал.

## Кто что делает

BIOS — то, что нужно **до** SDL / скана скриптов, или то, что умеет только
система Android (пикер, установщик APK, FileProvider, chmod бинаря,
убийство процесса `:game`).

MAS OS — рабочий стол **после** входа в Ren'Py: тема, склад по URL,
вкл/выкл сабмодов, проводник, подарки, плеер, новости, комната.

### BIOS

- разрешение «все файлы» и ожидание гранта
- SAF: zip, картинка, любой файл → Documents / Transfer
- установка zip/RPA/сабмода так, чтобы файлы попали в первый скан
- экспорт / импорт / шаринг zip сейвов
- проверка GitHub Release и установка APK
- копия нативного движка в `getFilesDir()` и проверка ELF
- флаг «сразу MAS OS» (`boot_renpy`)
- безопасный вход: `flags/skip_submods` + `mas_os_safe_mode` в `getFilesDir()`
  (0config паркует Submods до скана скриптов)
- шаринг log.txt / traceback
- приём из игры: Intent + extra `open` / `force_bios`

### MAS OS

- оформление, обои, шрифты, раскладки
- Склад: качать по ссылке картинки/шрифты/файлы, превью
- список сабмодов, тумблеры, каталог JSON
- файловый менеджер по уже открытому дереву
- подарки, плеер, события, браузер, справка
- апдейтер порта как новости (текст version.txt)
- запуск комнаты Моники
- шахматы, когда бинарь уже лежит и отвечает `uci`

### Склад и сабмоды — оба слоя

Склад в MAS OS остаётся качалкой по URL. Кнопка вроде
«Установить сабмод» открывает BIOS на секции `#submods`.
После zip на диске игрок возвращается в MAS OS и включает пак.

Обновление: changelog и «есть новая версия» живут в MAS OS.
Поставить APK — BIOS.

## Прыжок MAS OS → BIOS

Да. Игра в процессе `:game`, BIOS — MAIN в процессе по умолчанию.

1. jnius: Intent на `LauncherActivity`
2. extra `force_bios=true`
3. extra `open=submods` (или files / saves / update / engine)
4. `startActivity` + `Process.killProcess(myPid())`

BIOS читает extra, грузит `index.html#submods`, Java вызывает
`biosOpen('submods')` после `onPageFinished`.

То же с домашней кнопки «BIOS» и из настроек системы.

## Перезагрузка без вылета в лаунчер телефона

`renpy.utter_restart()` на Android часто рвёт SDL-активность и на этом
заканчивается — приложение закрывается.

С BIOS процесс `:game` можно убить специально, а активность BIOS
остаётся. Дальше:

- вернуться в MAS OS: extra `boot_renpy` → BIOS сразу стартует
  `PythonSDLActivity`
- вернуться в BIOS: extra `force_bios`, автостарт выключен
- перезагрузка оболочки: как «вернуться в MAS OS»

Сессию Моники по-прежнему закрываем через `end_game_session()` до килла,
чтобы не было crash-greeting.

## Мост JS

Java кладёт `BiosBridge` (как в лаборатории). Страница зовёт:

`startGame`, `startSafe`, `grantAllFiles`, `pickZip`, `pickImage`,
`pickFile`, `installZips`, `pickSubmodZip`, `deleteMod`,
`exportSaves`, `importSaves`, `shareSaves`, `checkUpdate`,
`downloadUpdate`, `installLocalApk`, `downloadUpdateAgain`,
`installEngine`, `testEngine`, `testStockfish`, `toggleBoot`,
`shareLogs`, `useNativeUi`

Обратно в страницу: `biosLog`, `biosProgress`, `biosSetStatus`,
`biosOpen`.

Полка (сабмоды-менеджер, третий вид, Documents FM) не трогаем:
BIOS стыкуется с последним коммитом, те вещи приедут отдельно.
