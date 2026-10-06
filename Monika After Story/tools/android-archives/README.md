# Android RPA packs

Сборка:

```
python tools/make_android_archives.py
```

Получаются `images.rpa` и `audio.rpa` плюс `.sha256`. Их нет в git.

Залей оба `.rpa` и оба `.sha256` в GitHub Release репозитория
`artem213101zse/MonikaModDev-RU` с теми же именами. BIOS качает
`releases/latest/download/images.rpa`.

Без релиза можно скопировать файлы в телефон:
`Documents/Monika_after_story/archives/`
и в BIOS нажать «Поставить с диска».
