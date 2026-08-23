# MAS OS documentation
#
# How to add a page (see _build_docs at the bottom of the python block):
#   doc_text("id", "cat", "Title", "Body...", tags=["..."], summary="...")
#   doc_gallery("id", "cat", "Title", [("image.png", "caption"), ...], intro="")
#   doc_mixed("id", "cat", "Title", [
#       ("text", "paragraph"),
#       ("image", "image.png", "caption"),
#   ])
#
# Categories: add a tuple to DOC_CATS.
# Screenshots later: put files in game/mod_assets/mas_os/docs/ and point slides at them.

init -8 python in mas_os:
    import store

    _ = getattr(store, "_", lambda s: s)

    # Temporary stand-ins until real screenshots exist.
    DOC_IMG_SPLASH = "bg/splash.png"
    DOC_IMG_MENU = "gui/overlay/main_menu_d.png"
    DOC_IMG_GAME = "gui/overlay/game_menu_d.png"
    DOC_IMG_BOX = "gui/textbox_monika_d.png"
    DOC_IMG_BG = "gui/menu_bg_d.png"
    DOC_IMG_NEW = "mod_assets/menu_new.png"
    DOC_IMG_DESK = "mod_assets/emptydesk.png"

    DOC_CATS = [
        ("os", "MAS OS"),
        ("android", "Android"),
        ("play", "Игра"),
        ("files", "Файлы"),
    ]

    DOC_KIND_SHORT = {
        "text": "Т",
        "gallery": "К",
        "mixed": "ТК",
    }

    DOC_KIND_LABEL = {
        "text": "текст",
        "gallery": "картинки",
        "mixed": "текст + картинки",
    }

    _doc_pages = None
    doc_query = ""
    doc_cat = "all"
    doc_slide = 0
    doc_typing = False

    def doc_text(doc_id, cat, title, body, tags=None, summary=""):
        return {
            "id": doc_id,
            "cat": cat,
            "title": title,
            "kind": "text",
            "body": body or "",
            "tags": list(tags or []),
            "summary": summary or "",
            "slides": [],
            "blocks": [],
        }

    def doc_gallery(doc_id, cat, title, slides, intro="", tags=None, summary=""):
        norm = []
        for item in (slides or []):
            if isinstance(item, dict):
                norm.append({
                    "image": item.get("image", ""),
                    "caption": item.get("caption", ""),
                })
            else:
                img = item[0] if item else ""
                cap = item[1] if len(item) > 1 else ""
                norm.append({"image": img, "caption": cap})
        return {
            "id": doc_id,
            "cat": cat,
            "title": title,
            "kind": "gallery",
            "body": intro or "",
            "tags": list(tags or []),
            "summary": summary or "",
            "slides": norm,
            "blocks": [],
        }

    def doc_mixed(doc_id, cat, title, blocks, tags=None, summary=""):
        norm = []
        for item in (blocks or []):
            if isinstance(item, dict):
                kind = item.get("type") or item.get("kind") or "text"
                if kind == "image":
                    norm.append({
                        "type": "image",
                        "image": item.get("image", ""),
                        "caption": item.get("caption", ""),
                    })
                else:
                    norm.append({
                        "type": "text",
                        "text": item.get("text") or item.get("body") or "",
                    })
            elif item and item[0] == "image":
                cap = item[2] if len(item) > 2 else ""
                norm.append({"type": "image", "image": item[1], "caption": cap})
            elif item:
                norm.append({"type": "text", "text": item[1] if len(item) > 1 else ""})
        return {
            "id": doc_id,
            "cat": cat,
            "title": title,
            "kind": "mixed",
            "body": "",
            "tags": list(tags or []),
            "summary": summary or "",
            "slides": [],
            "blocks": norm,
        }

    def register_doc(page):
        """
        Append a page after the catalog is built. Safe to call from later init.
        """
        pages = docs()
        if not page or not page.get("id"):
            return False
        for existing in pages:
            if existing["id"] == page["id"]:
                pages.remove(existing)
                break
        pages.append(page)
        return True

    def _build_docs():
        # -----------------------------------------------------------------
        # CATALOG — add new articles here.
        # cat must match an id in DOC_CATS (or the page still shows in «Все»).
        # -----------------------------------------------------------------
        return [
            doc_text(
                "what",
                "os",
                _("Что такое MAS OS"),
                _(
                    "MAS OS — оболочка, которая открывается до запуска "
                    "Моники: Эпилог.\n\n"
                    "Пока вы здесь, сессия игры не начинается: Моника не "
                    "считает, что вы к ней заходили, и не обижается, если "
                    "закрыть приложение без прощания.\n\n"
                    "Это фича порта, а не сабмод. Сабмоды подключаются уже "
                    "внутри игры и не могут перехватить загрузку.\n\n"
                    "На главной есть тумблер «При запуске»: MAS OS или сразу "
                    "игра. Выбор запоминается."
                ),
                tags=["оболочка", "сессия", "порт"],
                summary=_("Оболочка до запуска. Сессия не начинается."),
            ),
            doc_gallery(
                "shell_tour",
                "os",
                _("Обход оболочки"),
                [
                    (DOC_IMG_SPLASH, _("Заставка. Позже здесь будет снимок главного экрана MAS OS.")),
                    (DOC_IMG_MENU, _("Главное меню игры. Заглушка: снимок плиток OS ещё не готов.")),
                    (DOC_IMG_GAME, _("Игровое меню. Сюда встанет скрин кнопки возврата в OS.")),
                    (DOC_IMG_BOX, _("Текстбокс Моники. Заглушка для скрина разговора.")),
                ],
                intro=_(
                    "Картиночная статья: листай стрелками. Картинки пока из "
                    "ресурсов игры — заменишь своими скриншотами."
                ),
                tags=["экран", "скриншот", "оболочка"],
                summary=_("Слайды по экранам OS. Пока заглушки."),
            ),
            doc_mixed(
                "android",
                "android",
                _("Для Android"),
                [
                    (
                        "text",
                        _(
                            "На телефоне из MAS сложно достать persistent, логи и "
                            "папку characters. Оболочка как раз для этого."
                        ),
                    ),
                    (
                        "image",
                        DOC_IMG_SPLASH,
                        _("Заставка порта. Позже — скрин MAS OS на телефоне."),
                    ),
                    (
                        "text",
                        _(
                            "Что уже можно сделать, не заходя к Монике:\n\n"
                            "• читать эту документацию\n"
                            "• класть подарки в characters\n"
                            "• смотреть логи и traceback\n"
                            "• копировать persistent через раздел «Данные»\n"
                            "• бродить по папкам в файловом менеджере\n\n"
                            "Клавиатура телефона не должна открываться сама: "
                            "поля ввода появляются после нажатия."
                        ),
                    ),
                    (
                        "image",
                        DOC_IMG_NEW,
                        _("Меню. Заглушка: сюда встанет скрин файлов или подарков."),
                    ),
                ],
                tags=["телефон", "android", "клавиатура"],
                summary=_("Зачем OS на телефоне и что в ней делать."),
            ),
            doc_text(
                "goodbye",
                "play",
                _("Почему важно прощаться"),
                _(
                    "Если закрыть уже запущенную игру крестиком или через "
                    "диспетчер задач, Моника думает, что вы ушли без "
                    "прощания.\n\n"
                    "Выход из MAS OS — не то же самое. Игра ещё не "
                    "стартовала, поэтому прощание не требуется.\n\n"
                    "Когда нажмёте «Запустить MAS», начнётся обычная "
                    "сессия со всеми проверками.\n\n"
                    "Вернуться в OS из комнаты можно через меню или кнопку "
                    "на экране «Эй, Моника…». Тогда сессия закроется "
                    "нормально, без обиды."
                ),
                tags=["прощание", "сессия", "закрыть"],
                summary=_("Выход из OS не равен уходу без прощания."),
            ),
            doc_text(
                "submods",
                "play",
                _("Сабмоды"),
                _(
                    "Сейчас MAS OS только показывает сабмоды, которые уже "
                    "подхватились при загрузке Ren'Py.\n\n"
                    "Установка с устройства появится позже: положить .rpy "
                    "или папку в game/Submods и перезапустить приложение.\n\n"
                    "Сломанный сабмод может уронить загрузку ещё до "
                    "оболочки — это ограничение Ren'Py, не MAS OS."
                ),
                tags=["сабмод", "установка"],
                summary=_("Список загруженных сабмодов. Установка — позже."),
            ),
            doc_mixed(
                "gifts_help",
                "files",
                _("Подарки"),
                [
                    (
                        "text",
                        _(
                            "Раздел «Подарки» пишет файлы в папку characters. "
                            "Моника увидит их только после «Запустить MAS».\n\n"
                            "Имя без пробелов, латиница. Нажми подсказку, "
                            "чтобы подставить имя, затем «Создать .gift»."
                        ),
                    ),
                    (
                        "image",
                        DOC_IMG_DESK,
                        _("Стол. Заглушка: сюда встанет скрин раздела подарков."),
                    ),
                    (
                        "text",
                        _(
                            "Если файл создали случайно — открой колонку "
                            "«Уже в characters» и нажми файл. После "
                            "подтверждения он удалится.\n\n"
                            "Отдельно: oki doki (день рождения Моники) и "
                            "imsorry.txt."
                        ),
                    ),
                ],
                tags=["подарок", "gift", "characters"],
                summary=_("Как класть и убирать .gift без проводника."),
            ),
            doc_gallery(
                "folders",
                "files",
                _("Папки порта"),
                [
                    (DOC_IMG_SPLASH, _("Корень игры. Кнопка «Игра» в файлах.")),
                    (DOC_IMG_MENU, _("characters — подарки и oki doki.")),
                    (DOC_IMG_GAME, _("saves — persistent и .bak.")),
                    (DOC_IMG_BG, _("log — журналы порта и MAS.")),
                    (DOC_IMG_BOX, _("Submods — папка сабмодов внутри game/.")),
                ],
                intro=_(
                    "Быстрые кнопки в файловом менеджере прыгают в эти папки. "
                    "Картинки — заглушки, подписи уже настоящие."
                ),
                tags=["папки", "файлы", "persistent", "characters"],
                summary=_("Куда ведут кнопки Игра / characters / saves."),
            ),
            doc_mixed(
                "writing_docs",
                "os",
                _("Как добавить статью"),
                [
                    (
                        "text",
                        _(
                            "Новые разделы добавляются в game/mas_os_docs.rpy, "
                            "функция _build_docs(). Не надо трогать экран — "
                            "только каталог.\n\n"
                            "Три вида страниц:\n"
                            "• doc_text — только текст\n"
                            "• doc_gallery — картинки с подписями, листать стрелками\n"
                            "• doc_mixed — текст и картинки сверху вниз\n\n"
                            "Категория — id из DOC_CATS. Теги и summary нужны "
                            "для поиска."
                        ),
                    ),
                    (
                        "image",
                        DOC_IMG_SPLASH,
                        _("Заглушка. Свои скрины клади в mod_assets/mas_os/docs/."),
                    ),
                    (
                        "text",
                        _(
                            "Примеры вызовов:\n\n"
                            "doc_text(\"id\", \"os\", \"Заголовок\", \"Текст…\", "
                            "tags=[\"тег\"], summary=\"кратко\")\n\n"
                            "doc_gallery(\"id\", \"os\", \"Заголовок\", "
                            "[(\"mod_assets/mas_os/docs/one.png\", \"Подпись\")])\n\n"
                            "doc_mixed(\"id\", \"os\", \"Заголовок\", ["
                            "(\"text\", \"Абзац\"), "
                            "(\"image\", \"mod_assets/mas_os/docs/one.png\", \"Подпись\")])\n\n"
                            "Из другого файла можно вызвать register_doc(page)."
                        ),
                    ),
                ],
                tags=["документация", "добавить", "скриншот"],
                summary=_("Куда писать новые статьи и как вставлять картинки."),
            ),
        ]

    def docs():
        global _doc_pages
        if _doc_pages is None:
            _doc_pages = _build_docs()
        return _doc_pages

    def doc_by_id(doc_id):
        for item in docs():
            if item.get("id") == doc_id:
                return item
        return None

    def set_active_doc(doc_id):
        global _active_doc, doc_slide
        page = doc_by_id(doc_id)
        if page is not None:
            _active_doc = page
            doc_slide = 0

    def active_doc():
        return _active_doc

    def ensure_active_doc():
        global _active_doc, doc_slide
        if isinstance(_active_doc, dict) and _active_doc.get("id"):
            return
        items = docs()
        _active_doc = items[0] if items else None
        doc_slide = 0

    def set_doc_cat(cat):
        global doc_cat
        doc_cat = cat or "all"

    def clear_doc_query():
        global doc_query
        doc_query = ""
        stop_doc_search()

    def start_doc_search():
        global doc_typing
        doc_typing = True
        iv = getattr(store.mas_os, "doc_iv", None)
        if iv is not None:
            iv.default = True

    def stop_doc_search():
        global doc_typing
        doc_typing = False
        iv = getattr(store.mas_os, "doc_iv", None)
        if iv is not None:
            iv.default = False

    def _doc_blob(page):
        parts = [
            page.get("id") or "",
            page.get("title") or "",
            page.get("summary") or "",
            page.get("body") or "",
            page.get("kind") or "",
            DOC_KIND_LABEL.get(page.get("kind"), ""),
        ]
        for tag in page.get("tags") or []:
            parts.append(tag)
        for slide in page.get("slides") or []:
            parts.append(slide.get("caption") or "")
            parts.append(slide.get("image") or "")
        for block in page.get("blocks") or []:
            parts.append(block.get("text") or "")
            parts.append(block.get("caption") or "")
            parts.append(block.get("image") or "")
        return " ".join(parts).lower()

    def matched_docs():
        q = (doc_query or "").strip().lower()
        cat = doc_cat or "all"
        rows = []
        for page in docs():
            if cat != "all" and page.get("cat") != cat:
                continue
            if q and q not in _doc_blob(page):
                continue
            rows.append(page)
        return rows

    def doc_image_ok(path):
        if not path:
            return False
        try:
            return bool(store.renpy.loadable(path))
        except Exception:
            return False

    def doc_image_path(path):
        if doc_image_ok(path):
            return path
        if doc_image_ok(DOC_IMG_SPLASH):
            return DOC_IMG_SPLASH
        return None

    def fit_image(path, max_w, max_h=None):
        """
        Scale a loadable image to fit a box.
        Transform() in Ren'Py 7.4 does not accept xmaximum/ymaximum.
        zoom is a real transform property.
        """
        if not path:
            return store.Null()
        max_w = max(int(max_w or 0), 1)
        if max_h:
            max_h = max(int(max_h), 1)
        iw = ih = 0
        try:
            iw, ih = store.renpy.image_size(path)
        except Exception:
            iw = ih = 0
        if not iw or not ih:
            return path
        z = float(max_w) / float(iw)
        if max_h:
            z = min(z, float(max_h) / float(ih))
        if z > 1.0:
            z = 1.0
        if z >= 0.995:
            return path
        return store.Transform(path, zoom=z)

    def active_slide():
        page = _active_doc if isinstance(_active_doc, dict) else None
        slides = (page or {}).get("slides") or []
        if not slides:
            return None, 0, 0
        idx = doc_slide % len(slides)
        return slides[idx], idx, len(slides)

    def doc_slide_next():
        global doc_slide
        page = _active_doc if isinstance(_active_doc, dict) else None
        n = len((page or {}).get("slides") or [])
        if n:
            doc_slide = (doc_slide + 1) % n

    def doc_slide_prev():
        global doc_slide
        page = _active_doc if isinstance(_active_doc, dict) else None
        n = len((page or {}).get("slides") or [])
        if n:
            doc_slide = (doc_slide - 1) % n

    def cat_title(cat_id):
        if cat_id == "all":
            return _("Все")
        for cid, title in DOC_CATS:
            if cid == cat_id:
                return title
        return cat_id

    def doc_list_label(page):
        short = DOC_KIND_SHORT.get((page or {}).get("kind"), "?")
        title = (page or {}).get("title") or ""
        return "[{0}] {1}".format(short, title)


init python:
    class MASOSDocInputValue(InputValue):
        default = False
        editable = True
        returnable = True

        def get_text(self):
            return store.mas_os.doc_query or ""

        def set_text(self, value):
            store.mas_os.doc_query = value

        def enter(self):
            store.mas_os.stop_doc_search()
            return None


init 1 python:
    store.mas_os.doc_iv = MASOSDocInputValue()


label mas_os_docs:
    $ store.mas_os.stop_doc_search()
    $ store.mas_os.ensure_active_doc()
    call screen mas_os_docs with mas_os_trans
    jump mas_os_home


screen mas_os_doc_image(path, caption=None, max_w=740, max_h=320):
    $ shown = store.mas_os.doc_image_path(path)

    vbox:
        spacing 8
        xfill True

        frame:
            xysize (max_w, max_h)
            background Solid(store.mas_os.theme_color("panel2"))
            xalign 0.5
            clipping True

            if shown:
                add store.mas_os.fit_image(shown, max_w - 12, max_h - 12):
                    xalign 0.5
                    yalign 0.5
            else:
                text _("Нет картинки"):
                    style "mas_os_hint"
                    xalign 0.5
                    yalign 0.5

        if caption:
            text caption:
                style "mas_os_hint"
                xalign 0.5
                text_align 0.5
                xsize max_w
                substitute False


screen mas_os_docs():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ items = store.mas_os.matched_docs()
    $ doc = store.mas_os.active_doc()
    $ doc = doc if isinstance(doc, dict) else None
    $ doc_id = doc["id"] if doc else None
    $ doc_title = doc["title"] if doc else _("Документация")
    $ doc_kind = (doc or {}).get("kind") or "text"
    $ kind_label = store.mas_os.DOC_KIND_LABEL.get(doc_kind, "")
    $ cat_now = store.mas_os.doc_cat
    $ typing = store.mas_os.doc_typing
    $ typed = store.mas_os.doc_query or ""
    $ slide, slide_i, slide_n = store.mas_os.active_slide()
    $ slide_pos = "{0} / {1}".format(slide_i + 1, slide_n)

    use mas_os_bg

    text _("Документация") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 14

    hbox:
        xpos 48
        ypos 58
        spacing 8

        if typing:
            input:
                value store.mas_os.doc_iv
                length 40
                copypaste True
                color store.mas_os.theme_color("input")
                size 20
                xsize 420
                yalign 0.5

            textbutton _("Готово"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 110
                action [
                    store.mas_os.doc_iv.Disable(),
                    Function(store.mas_os.stop_doc_search),
                ]
        else:
            button:
                style "mas_os_gift_field"
                xsize 420
                ysize 40
                action [
                    Function(store.mas_os.start_doc_search),
                    store.mas_os.doc_iv.Enable(),
                ]

                if typed:
                    text typed:
                        style "mas_os_body"
                        size 18
                        yalign 0.5
                        substitute False
                else:
                    text _("Нажми, чтобы искать"):
                        style "mas_os_hint"
                        size 16
                        yalign 0.5

        if typed:
            textbutton _("Сброс"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 110
                action [
                    store.mas_os.doc_iv.Disable(),
                    Function(store.mas_os.clear_doc_query),
                ]

    hbox:
        xpos 48
        ypos 106
        spacing 8

        textbutton _("Все"):
            style "mas_os_cat_btn"
            text_style "mas_os_cat_btn_text"
            selected (cat_now == "all")
            action Function(store.mas_os.set_doc_cat, "all")

        for cid, ctitle in store.mas_os.DOC_CATS:
            textbutton ctitle:
                style "mas_os_cat_btn"
                text_style "mas_os_cat_btn_text"
                selected (cat_now == cid)
                action Function(store.mas_os.set_doc_cat, cid)

    viewport:
        xpos 48
        ypos 156
        xysize (340, 460)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 6

            if not items:
                text _("Ничего не найдено."):
                    style "mas_os_hint"
            else:
                for page in items:
                    textbutton store.mas_os.doc_list_label(page):
                        style "mas_os_side_btn"
                        text_style "mas_os_side_btn_text"
                        substitute False
                        selected (page["id"] == doc_id)
                        action Function(store.mas_os.set_active_doc, page["id"])

    frame at store.mas_os.t_pop(0.06):
        style "mas_os_panel"
        xpos 410
        ypos 156
        xysize (822, 460)
        padding (20, 16)

        vbox:
            spacing 10
            xfill True

            text doc_title:
                style "mas_os_subtitle"
                substitute False

            text kind_label:
                style "mas_os_hint"

            if doc is None:
                text _("Выбери статью слева."):
                    style "mas_os_body"

            elif doc_kind == "gallery":
                viewport:
                    xysize (774, 360)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 10
                        xsize 750

                        if doc.get("body"):
                            text doc["body"]:
                                style "mas_os_hint"
                                xsize 750
                                substitute False

                        if slide is None:
                            text _("В этой статье ещё нет картинок."):
                                style "mas_os_body"
                        else:
                            use mas_os_doc_image(slide.get("image"), slide.get("caption"), 750, 250)

                            hbox:
                                xalign 0.5
                                spacing 16

                                textbutton _("<"):
                                    style "mas_os_nav_btn"
                                    text_style "mas_os_nav_btn_text"
                                    xsize 70
                                    sensitive (slide_n > 1)
                                    action Function(store.mas_os.doc_slide_prev)

                                text slide_pos:
                                    style "mas_os_body"
                                    yalign 0.5
                                    substitute False

                                textbutton _(">"):
                                    style "mas_os_nav_btn"
                                    text_style "mas_os_nav_btn_text"
                                    xsize 70
                                    sensitive (slide_n > 1)
                                    action Function(store.mas_os.doc_slide_next)

            elif doc_kind == "mixed":
                viewport:
                    xysize (774, 360)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 14
                        xsize 750

                        for block in doc.get("blocks") or []:
                            if block.get("type") == "image":
                                use mas_os_doc_image(block.get("image"), block.get("caption"), 740, 240)
                            else:
                                text block.get("text") or "":
                                    style "mas_os_body"
                                    xsize 740
                                    substitute False

            else:
                viewport:
                    xysize (774, 360)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    text (doc.get("body") or ""):
                        style "mas_os_body"
                        xsize 740
                        substitute False

    if not store.mas_os.wm_embedded():
        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 48
            ypos 640
            action [
                Function(store.mas_os.stop_doc_search),
                Return("back"),
            ]

    if not store.mas_os.wm_embedded():
        key "K_ESCAPE" action [Function(store.mas_os.stop_doc_search), Return("back")]
        key "K_AC_BACK" action If(
            store.mas_os.doc_typing,
            [store.mas_os.doc_iv.Disable(), Function(store.mas_os.stop_doc_search)],
            [Function(store.mas_os.stop_doc_search), Return("back")],
        )
    key "K_LEFT" action Function(store.mas_os.doc_slide_prev)
    key "K_RIGHT" action Function(store.mas_os.doc_slide_next)
    key "K_RETURN" action Function(store.mas_os.stop_doc_search)
