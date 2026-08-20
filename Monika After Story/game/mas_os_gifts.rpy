# MAS OS — create .gift files in characters/ from a known catalog.

init -5 python in mas_os:
    import os
    import re
    import store

    GIFT_HINTS = {
        "coffee": "Кофе. Напиток; можно дарить повторно, пока не заполнится запас.",
        "hotchocolate": "Горячий шоколад. Напиток, особенно к холодному сезону.",
        "justmonikathermos": "Термос Just Monika. Аксессуар на стол.",
        "quetzalplushie": "Плюшевый кетцаль. Один раз; любимый «питомец».",
        "promisering": "Кольцо-обещание. Принимает только с привязанности «Влюблённая» и выше.",
        "cupcake": "Капкейк.",
        "candy": "Конфеты. В коде реакция на Хэллоуин; в другой сезон может пройти как обычный подарок.",
        "candycorn": "Кукурузные конфеты. Плохой подарок — Моника не любит.",
        "fudge": "Шоколадный фадж.",
        "christmascookies": "Рождественское печенье. Сезон D25; иначе может быть обычной реакцией.",
        "candycane": "Карамельная трость. Сезон D25.",
        "roses": "Розы. Хорошо на свидание / 14 февраля.",
        "chocolates": "Коробка шоколадных конфет.",
        "noudeck": "Колода карт NOU. Открывает мини-игру, если ещё не открыта.",
        "blackribbon": "Чёрная лента для волос.",
        "blueribbon": "Синяя лента.",
        "darkpurpleribbon": "Тёмно-фиолетовая лента.",
        "emeraldribbon": "Изумрудная лента.",
        "grayribbon": "Серая лента.",
        "greenribbon": "Зелёная лента.",
        "lightpurpleribbon": "Светло-фиолетовая лента.",
        "peachribbon": "Персиковая лента.",
        "pinkribbon": "Розовая лента.",
        "platinumribbon": "Платиновая лента.",
        "redribbon": "Красная лента.",
        "rubyribbon": "Рубиновая лента.",
        "sapphireribbon": "Сапфировая лента.",
        "silverribbon": "Серебряная лента.",
        "tealribbon": "Бирюзовая лента.",
        "yellowribbon": "Жёлтая лента.",
    }

    gift_typing = False

    GIFT_NAME_RE = re.compile(r"[^a-z0-9_\-]+")

    def normalize_gift_stem(raw):
        stem = (raw or "").strip().lower()
        if stem.endswith(".gift"):
            stem = stem[:-5]
        stem = GIFT_NAME_RE.sub("", stem.replace(" ", ""))
        return stem[:48]

    def _sprite_kind(giftname):
        gmap = getattr(store.mas_sprites_json, "giftname_map", {})
        info = gmap.get(giftname)
        if not info:
            return None
        kind = info[0]
        sp_name = info[1]
        labels = {0: "аксессуар", 1: "причёска", 2: "одежда"}
        return labels.get(kind, "спрайт"), sp_name

    def gift_catalog():
        """
        Built-in reactions + spritepack giftnames currently registered.
        """
        rows = []
        seen = set()
        fmap = getattr(store.mas_filereacts, "filereact_map", {})

        for fname in sorted(GIFT_HINTS.keys()):
            seen.add(fname)
            rows.append({
                "stem": fname,
                "hint": GIFT_HINTS[fname],
                "source": "mas",
            })

        for fname in sorted(fmap.keys()):
            if not fname or fname in seen:
                continue
            kind = _sprite_kind(fname)
            if kind:
                hint = "Спрайтпак: {0} «{1}».".format(kind[0], kind[1])
            else:
                hint = "Зарегистрированный подарок MAS."
            seen.add(fname)
            rows.append({
                "stem": fname,
                "hint": hint,
                "source": "json",
            })

        return rows

    def matched_gifts():
        q = normalize_gift_stem(gift_input)
        rows = gift_catalog()
        if not q:
            return rows
        hits = [row for row in rows if q in row["stem"] or q in row["hint"].lower()]
        return hits

    def current_gift_preview():
        stem = normalize_gift_stem(gift_input)
        if not stem:
            return None, "Введи имя файла без расширения, например coffee."
        for row in gift_catalog():
            if row["stem"] == stem:
                return stem, "{0}.gift — {1}".format(stem, row["hint"])
        kind = _sprite_kind(stem)
        if kind:
            return stem, "{0}.gift — спрайтпак: {1} «{2}».".format(stem, kind[0], kind[1])
        return stem, (
            "{0}.gift — такого имени нет в списке MAS. "
            "Файл всё равно создастся: либо спрайтпак, либо общая реакция."
        ).format(stem)

    def _ensure_characters():
        folder = characters_dir()
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        return folder

    def start_gift_typing():
        global gift_typing
        gift_typing = True
        iv = getattr(store.mas_os, "gift_iv", None)
        if iv is not None:
            iv.default = True

    def stop_gift_typing():
        global gift_typing
        gift_typing = False
        iv = getattr(store.mas_os, "gift_iv", None)
        if iv is not None:
            iv.default = False

    def create_gift_from_input():
        global gift_status
        stem = normalize_gift_stem(gift_input)
        if not stem:
            gift_status = "Сначала введи имя подарка."
            return False
        ok = write_characters_file(stem + ".gift", "")
        if ok:
            stop_gift_typing()
        return ok

    def write_characters_file(filename, content):
        global gift_status
        try:
            folder = _ensure_characters()
            path = os.path.join(folder, filename)
            with open(path, "wb") as handle:
                if content:
                    handle.write(content.encode("utf-8"))
            gift_status = "Готово: characters/{0}".format(filename)
            return True
        except Exception as err:
            gift_status = "Не удалось записать: {0}".format(err)
            return False

    def fill_gift(stem):
        global gift_input, gift_status
        gift_input = stem
        gift_status = ""
        stop_gift_typing()

    def create_oki_doki():
        return write_characters_file("oki doki", "")

    def create_imsorry():
        return write_characters_file("imsorry.txt", "")

    def list_character_files(limit=40):
        """
        Files only (no folders). Returns (exists, names, truncated).
        """
        folder = characters_dir()
        if not folder or not os.path.isdir(folder):
            return False, [], False
        try:
            names = []
            for name in sorted(os.listdir(folder)):
                path = os.path.join(folder, name)
                if os.path.isfile(path):
                    names.append(name)
        except Exception:
            return True, [], False
        truncated = len(names) > limit
        return True, names[:limit], truncated

    def _safe_characters_path(filename):
        folder = characters_dir()
        if not folder or not filename:
            return None
        if filename in (".", ".."):
            return None
        if "/" in filename or "\\" in filename:
            return None
        path = os.path.normpath(os.path.join(folder, filename))
        root = os.path.normpath(folder)
        if path != root and not path.startswith(root + os.sep):
            return None
        return path

    def delete_gift_prompt(filename):
        safe = (filename or "").replace("[", "[[").replace("{", "{{")
        return (
            "Удалить «{0}» из characters?\n"
            "Файл исчезнет сразу. Если добавил случайно — это как раз то, что нужно."
        ).format(safe)

    def delete_character_file(filename):
        global gift_status
        path = _safe_characters_path(filename)
        if not path:
            gift_status = "Нельзя удалить этот файл."
            return False
        try:
            if not os.path.isfile(path):
                gift_status = "Файла уже нет."
                return False
            os.remove(path)
            gift_status = "Удалено: {0}".format(filename)
            return True
        except Exception as err:
            gift_status = "Не удалось удалить: {0}".format(err)
            return False


init python:
    class MASOSGiftInputValue(InputValue):
        """
        default=False so Android does not pop the IME when the screen opens.
        The field is only mounted after a tap (gift_typing).
        """
        default = False
        editable = True
        returnable = True

        def get_text(self):
            return store.mas_os.gift_input or ""

        def set_text(self, value):
            store.mas_os.gift_input = value

        def enter(self):
            store.mas_os.create_gift_from_input()
            return None


init 1 python:
    store.mas_os.gift_iv = MASOSGiftInputValue()


label mas_os_gifts:
    $ store.mas_os.gift_status = ""
    $ store.mas_os.stop_gift_typing()
    call screen mas_os_gifts
    jump mas_os_home


screen mas_os_gifts():
    modal True
    zorder 200

    $ stem, preview = store.mas_os.current_gift_preview()
    $ rows = store.mas_os.matched_gifts()
    $ existing, names, cut = store.mas_os.list_character_files(limit=40)
    $ status = store.mas_os.gift_status
    $ typing = store.mas_os.gift_typing
    $ typed = store.mas_os.gift_input or ""

    add Solid("#14070d")

    text _("Подарки"):
        style "mas_os_title"
        xpos 48
        ypos 22

    text _("Файл попадёт в characters. Имя без пробелов, латиница. Моника увидит его после «Запустить MAS»."):
        style "mas_os_hint"
        xpos 48
        ypos 66

    frame:
        style "mas_os_panel"
        xpos 48
        ypos 100
        xysize (1184, 88)
        padding (16, 12)

        hbox:
            spacing 8
            yalign 0.5

            if typing:
                input:
                    value store.mas_os.gift_iv
                    length 40
                    copypaste True
                    allow "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
                    color "#FFF0F7"
                    size 22
                    xsize 400
                    yalign 0.5

                textbutton _("Готово"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 110
                    action [
                        store.mas_os.gift_iv.Disable(),
                        Function(store.mas_os.stop_gift_typing),
                    ]
            else:
                button:
                    style "mas_os_gift_field"
                    xsize 520
                    ysize 44
                    action [
                        Function(store.mas_os.start_gift_typing),
                        store.mas_os.gift_iv.Enable(),
                    ]
                    hover_sound gui.hover_sound
                    activate_sound gui.activate_sound

                    if typed:
                        text typed:
                            style "mas_os_body"
                            size 20
                            yalign 0.5
                            substitute False
                    else:
                        text _("Нажми, чтобы ввести имя"):
                            style "mas_os_hint"
                            size 16
                            yalign 0.5

            textbutton _("Создать .gift"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 200
                action [
                    store.mas_os.gift_iv.Disable(),
                    Function(store.mas_os.create_gift_from_input),
                ]

            textbutton _("oki doki"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 150
                action Function(store.mas_os.create_oki_doki)

            textbutton _("imsorry"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 130
                action Function(store.mas_os.create_imsorry)

    text preview:
        style "mas_os_body"
        size 16
        xpos 48
        ypos 198
        xsize 1180

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 48
            ypos 232

    viewport:
        xpos 48
        ypos 270
        xysize (760, 340)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 6

            text _("Подсказки (нажми, чтобы подставить имя):"):
                style "mas_os_hint"

            for row in rows:
                textbutton "{0}.gift — {1}".format(row["stem"], row["hint"]):
                    style "mas_os_side_btn"
                    text_style "mas_os_side_btn_text"
                    xsize 720
                    ysize 56
                    action [
                        store.mas_os.gift_iv.Disable(),
                        Function(store.mas_os.fill_gift, row["stem"]),
                    ]

    frame:
        style "mas_os_panel"
        xpos 828
        ypos 270
        xysize (404, 340)
        padding (16, 14)

        vbox:
            spacing 8
            xfill True

            text _("Уже в characters"):
                style "mas_os_subtitle"

            text _("Нажми файл, чтобы удалить"):
                style "mas_os_hint"
                size 14

            viewport:
                xysize (372, 250)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 4

                    if existing and names:
                        for name in names:
                            textbutton name:
                                style "mas_os_side_btn"
                                text_style "mas_os_side_btn_text"
                                xsize 360
                                ysize 44
                                substitute False
                                action Show(
                                    "mas_os_confirm",
                                    message=store.mas_os.delete_gift_prompt(name),
                                    yes_action=[
                                        Function(store.mas_os.delete_character_file, name),
                                        Hide("mas_os_confirm"),
                                    ],
                                    no_action=Hide("mas_os_confirm"),
                                )
                        if cut:
                            text _("…и ещё файлы"):
                                style "mas_os_hint"
                    else:
                        text _("Папка пустая."):
                            style "mas_os_hint"

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action [
            Function(store.mas_os.stop_gift_typing),
            Return("back"),
        ]

    key "K_ESCAPE" action [Function(store.mas_os.stop_gift_typing), Return("back")]
    key "K_AC_BACK" action If(
        store.mas_os.gift_typing,
        [store.mas_os.gift_iv.Disable(), Function(store.mas_os.stop_gift_typing)],
        [Function(store.mas_os.stop_gift_typing), Return("back")],
    )
    key "K_RETURN" action Function(store.mas_os.create_gift_from_input)
