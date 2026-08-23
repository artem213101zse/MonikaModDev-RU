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

    GIFT_TITLES = {
        "coffee": "Кофе",
        "hotchocolate": "Горячий шоколад",
        "justmonikathermos": "Термос",
        "quetzalplushie": "Кетцаль",
        "promisering": "Кольцо",
        "cupcake": "Капкейк",
        "candy": "Конфеты",
        "candycorn": "Candy corn",
        "fudge": "Фадж",
        "christmascookies": "Печенье",
        "candycane": "Трость",
        "roses": "Розы",
        "chocolates": "Шоколад",
        "noudeck": "Колода NOU",
        "blackribbon": "Чёрная лента",
        "blueribbon": "Синяя лента",
        "darkpurpleribbon": "Тёмно-фиолетовая",
        "emeraldribbon": "Изумрудная лента",
        "grayribbon": "Серая лента",
        "greenribbon": "Зелёная лента",
        "lightpurpleribbon": "Светло-фиолетовая",
        "peachribbon": "Персиковая лента",
        "pinkribbon": "Розовая лента",
        "platinumribbon": "Платиновая лента",
        "redribbon": "Красная лента",
        "rubyribbon": "Рубиновая лента",
        "sapphireribbon": "Сапфировая лента",
        "silverribbon": "Серебряная лента",
        "tealribbon": "Бирюзовая лента",
        "yellowribbon": "Жёлтая лента",
    }

    GIFT_IMG = {
        "coffee": "mod_assets/monika/a/mug/0.png",
        "hotchocolate": "mod_assets/monika/a/hotchoc_mug/0.png",
        "justmonikathermos": "mod_assets/monika/a/thermos_mug/0.png",
        "quetzalplushie": "mod_assets/monika/a/quetzalplushie/0.png",
        "promisering": "mod_assets/monika/a/promisering/2-10.png",
        "candy": "mod_assets/monika/a/desk_candy_jack_half/0.png",
        "candycorn": "mod_assets/monika/a/desk_candy_jack_brim/0.png",
        "fudge": "mod_assets/monika/a/heartchoc/0.png",
        "christmascookies": "mod_assets/monika/a/christmas_cookies/0.png",
        "candycane": "mod_assets/monika/a/candycane/0.png",
        "roses": "mod_assets/monika/a/roses/0.png",
        "chocolates": "mod_assets/monika/a/heartchoc/0.png",
        "noudeck": "mod_assets/games/nou/cards/back.png",
        "blackribbon": "mod_assets/thumbs/acs-ribbon_black.png",
        "blueribbon": "mod_assets/thumbs/acs-ribbon_blue.png",
        "darkpurpleribbon": "mod_assets/thumbs/acs-ribbon_dark_purple.png",
        "emeraldribbon": "mod_assets/thumbs/acs-ribbon_emerald.png",
        "grayribbon": "mod_assets/thumbs/acs-ribbon_gray.png",
        "greenribbon": "mod_assets/thumbs/acs-ribbon_green.png",
        "lightpurpleribbon": "mod_assets/thumbs/acs-ribbon_light_purple.png",
        "peachribbon": "mod_assets/thumbs/acs-ribbon_peach.png",
        "pinkribbon": "mod_assets/thumbs/acs-ribbon_pink.png",
        "platinumribbon": "mod_assets/thumbs/acs-ribbon_platinum.png",
        "redribbon": "mod_assets/thumbs/acs-ribbon_red.png",
        "rubyribbon": "mod_assets/thumbs/acs-ribbon_ruby.png",
        "sapphireribbon": "mod_assets/thumbs/acs-ribbon_sapphire.png",
        "silverribbon": "mod_assets/thumbs/acs-ribbon_silver.png",
        "tealribbon": "mod_assets/thumbs/acs-ribbon_teal.png",
        "yellowribbon": "mod_assets/thumbs/acs-ribbon_yellow.png",
    }

    GIFT_UNKNOWN_IMG = "mod_assets/thumbs/unknown.png"

    def _gift_loadable(path):
        if not path:
            return False
        try:
            return bool(store.renpy.loadable(path))
        except Exception:
            return False

    def _gift_sel_thumb(sp_type, sp_name):
        selspr = getattr(store, "mas_selspr", None)
        if selspr is None:
            return None
        mapping = {
            0: getattr(selspr, "ACS_SEL_MAP", {}),
            1: getattr(selspr, "HAIR_SEL_MAP", {}),
            2: getattr(selspr, "CLOTH_SEL_MAP", {}),
        }.get(sp_type)
        if not mapping:
            return None
        sel = mapping.get(sp_name)
        if sel is None:
            return None
        try:
            path = sel._build_thumbstr()
        except Exception:
            return None
        if _gift_loadable(path):
            return path
        return None

    def gift_image(stem):
        stem = (stem or "").lower()
        path = GIFT_IMG.get(stem)
        if _gift_loadable(path):
            return path
        info = None
        try:
            info = getattr(store.mas_sprites_json, "giftname_map", {}).get(stem)
        except Exception:
            info = None
        if info:
            path = _gift_sel_thumb(info[0], info[1])
            if path:
                return path
            sp_name = info[1]
            for fname in ("0.png", "0-0.png", "1.png", "2-10.png", "5.png"):
                cand = "mod_assets/monika/a/{0}/{1}".format(sp_name, fname)
                if _gift_loadable(cand):
                    return cand
            if info[0] == 1:
                cand = "mod_assets/thumbs/hair-{0}.png".format(sp_name)
                if _gift_loadable(cand):
                    return cand
            if info[0] == 2:
                cand = "mod_assets/thumbs/clothes-{0}.png".format(sp_name)
                if _gift_loadable(cand):
                    return cand
        for cand in (
            "mod_assets/thumbs/acs-{0}.png".format(stem),
            "mod_assets/monika/a/{0}/0.png".format(stem),
            "mod_assets/thumbs/{0}.png".format(stem),
        ):
            if _gift_loadable(cand):
                return cand
        if _gift_loadable(GIFT_UNKNOWN_IMG):
            return GIFT_UNKNOWN_IMG
        return None

    def gift_title(stem):
        stem = (stem or "").lower()
        title = GIFT_TITLES.get(stem)
        if title:
            return title
        info = None
        try:
            info = getattr(store.mas_sprites_json, "giftname_map", {}).get(stem)
        except Exception:
            info = None
        if info:
            selspr = getattr(store, "mas_selspr", None)
            mapping = None
            if selspr is not None:
                mapping = {
                    0: getattr(selspr, "ACS_SEL_MAP", {}),
                    1: getattr(selspr, "HAIR_SEL_MAP", {}),
                    2: getattr(selspr, "CLOTH_SEL_MAP", {}),
                }.get(info[0])
            sel = mapping.get(info[1]) if mapping else None
            if sel is not None:
                return sel.display_name
            return info[1].replace("_", " ")
        return stem

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
                "title": gift_title(fname),
                "hint": GIFT_HINTS[fname],
                "img": gift_image(fname),
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
                "title": gift_title(fname),
                "hint": hint,
                "img": gift_image(fname),
                "source": "json",
            })

        return rows

    def matched_gifts():
        q = normalize_gift_stem(gift_input)
        rows = gift_catalog()
        if not q:
            return rows
        hits = []
        for row in rows:
            blob = " ".join((
                row.get("stem") or "",
                (row.get("title") or "").lower(),
                (row.get("hint") or "").lower(),
            ))
            if q in blob:
                hits.append(row)
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

    def clear_gift_input():
        global gift_input, gift_status
        gift_input = ""
        gift_status = ""
        stop_gift_typing()
        return None

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
    call screen mas_os_gifts with mas_os_trans
    if _return == "store":
        jump mas_os_store
    jump mas_os_home


screen mas_os_gifts():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ stem, preview = store.mas_os.current_gift_preview()
    $ rows = store.mas_os.matched_gifts()
    $ existing, names, cut = store.mas_os.list_character_files(limit=40)
    $ status = store.mas_os.gift_status
    $ typing = store.mas_os.gift_typing
    $ typed = store.mas_os.gift_input or ""

    use mas_os_bg

    text _("Подарки") at store.mas_os.t_pop(0.0):
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
                    color store.mas_os.theme_color("input")
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
                    xsize 470
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

            if typed:
                textbutton _("×"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 44
                    ysize 44
                    action [
                        store.mas_os.gift_iv.Disable(),
                        Function(store.mas_os.clear_gift_input),
                    ]

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
        ypos 196
        xsize 1180

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 48
            ypos 228

    text _("Нажми карточку, чтобы подставить имя"):
        style "mas_os_hint"
        xpos 48
        ypos 254

    vpgrid:
        cols 4
        spacing 8
        xpos 48
        ypos 278
        xysize (760, 344)
        draggable True
        mousewheel True
        scrollbars "vertical"

        for row in rows:
            button:
                style "mas_os_side_btn"
                xsize 178
                ysize 196
                padding (4, 4)
                selected (typed == row["stem"])
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action [
                    store.mas_os.gift_iv.Disable(),
                    Function(store.mas_os.fill_gift, row["stem"]),
                ]

                vbox:
                    spacing 4
                    xfill True

                    frame:
                        xsize 170
                        ysize 118
                        background Solid(store.mas_os.theme_color("panel2"))
                        clipping True

                        if row.get("img"):
                            add store.mas_os.fit_image(row["img"], 166, 114):
                                xalign 0.5
                                yalign 0.5
                        else:
                            text _("?"):
                                style "mas_os_hint"
                                xalign 0.5
                                yalign 0.5

                    text row.get("title") or row["stem"]:
                        style "mas_os_side_btn_text"
                        size 14
                        xoffset 4
                        xsize 160
                        substitute False

                    text "{0}.gift".format(row["stem"]):
                        style "mas_os_hint"
                        size 11
                        xoffset 4
                        xsize 160
                        substitute False

    frame:
        style "mas_os_panel"
        xpos 828
        ypos 254
        xysize (404, 368)
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
                xysize (372, 280)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 4

                    if existing and names:
                        for name in names:
                            $ fimg = store.mas_os.gift_image(store.mas_os.normalize_gift_stem(name))
                            button:
                                style "mas_os_side_btn"
                                xsize 360
                                ysize 56
                                action Show(
                                    "mas_os_confirm",
                                    message=store.mas_os.delete_gift_prompt(name),
                                    yes_action=[
                                        Function(store.mas_os.delete_character_file, name),
                                        Hide("mas_os_confirm"),
                                    ],
                                    no_action=Hide("mas_os_confirm"),
                                )

                                hbox:
                                    spacing 8
                                    yalign 0.5
                                    xoffset 8

                                    if fimg:
                                        add store.mas_os.fit_image(fimg, 40, 40):
                                            yalign 0.5

                                    text name:
                                        style "mas_os_side_btn_text"
                                        size 14
                                        yalign 0.5
                                        xsize 280
                                        substitute False
                        if cut:
                            text _("…и ещё файлы"):
                                style "mas_os_hint"
                    else:
                        text _("Папка пустая."):
                            style "mas_os_hint"

    hbox:
        xpos 48
        ypos 640
        spacing 12

        if not store.mas_os.wm_embedded():
            textbutton _("Назад"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                action [
                    Function(store.mas_os.stop_gift_typing),
                    Return("back"),
                ]

        use mas_os_store_link("gift", "gifts", 420)

    if not store.mas_os.wm_embedded():
        key "K_ESCAPE" action [Function(store.mas_os.stop_gift_typing), Return("back")]
        key "K_AC_BACK" action If(
            store.mas_os.gift_typing,
            [store.mas_os.gift_iv.Disable(), Function(store.mas_os.stop_gift_typing)],
            [Function(store.mas_os.stop_gift_typing), Return("back")],
        )
    key "K_RETURN" action Function(store.mas_os.create_gift_from_input)
