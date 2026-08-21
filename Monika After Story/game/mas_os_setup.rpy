# MAS OS first-run installer. Also reopen from Settings → Система.

init -5 python in mas_os:
    import os
    import store

    setup_step = 0
    setup_from = "boot"
    SETUP_LAST = 5

    SETUP_TITLES = (
        "Приветствие",
        "Файлы DDLC",
        "Внешний вид",
        "Шрифт и движение",
        "Запуск",
        "Готово",
    )

    DDLC_PACKS = (
        ("audio", "audio.rpa", "bgm/m1.ogg"),
        ("images", "images.rpa", "gui/menu_art_m.png"),
        ("scripts", "scripts.rpa", "gui/menu_bg.png"),
        ("fonts", "fonts.rpa", "gui/font/Aller_Rg.ttf"),
    )

    DDLC_URLS = (
        ("Скачать DDLC бесплатно", "https://ddlc.moe"),
        ("Steam", "https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/"),
    )

    def setup_title():
        if 0 <= setup_step < len(SETUP_TITLES):
            return SETUP_TITLES[setup_step]
        return "Установка"

    def setup_next():
        global setup_step
        if setup_step < SETUP_LAST:
            setup_step += 1
        return None

    def setup_back():
        global setup_step
        if setup_step > 0:
            setup_step -= 1
        return None

    def setup_goto(step):
        global setup_step
        if 0 <= step <= SETUP_LAST:
            setup_step = step
        return None

    def setup_finish():
        store.persistent._mas_os_setup_done = True
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        return "done"

    def setup_skip():
        return setup_finish()

    def setup_recheck():
        return None

    def _pack_file_ok(path):
        try:
            return os.path.isfile(path) and os.path.getsize(path) > 2048
        except Exception:
            return False

    def ddlc_packs():
        gamed = os.path.join(game_dir(), "game")
        try:
            archives = list(getattr(store.config, "archives", None) or [])
        except Exception:
            archives = []
        rows = []
        for key, rpa, marker in DDLC_PACKS:
            path = os.path.join(gamed, rpa)
            on_disk = _pack_file_ok(path)
            in_arc = key in archives
            loadable = False
            try:
                loadable = bool(store.renpy.loadable(marker))
            except Exception:
                loadable = False
            ok = on_disk or in_arc or loadable
            if on_disk:
                how = "файл на диске"
            elif in_arc:
                how = "архив подключён"
            elif loadable:
                how = "ресурсы распакованы"
            else:
                how = "не найден"
            rows.append({
                "key": key,
                "rpa": rpa,
                "ok": ok,
                "how": how,
            })
        return rows

    def ddlc_all_ok():
        rows = ddlc_packs()
        if not rows:
            return False
        for row in rows:
            if not row["ok"]:
                return False
        return True

    def ddlc_missing():
        return [row["rpa"] for row in ddlc_packs() if not row["ok"]]

    def set_font_all(fid):
        for slot, _cap, _hint, _key, _def in FONT_SLOTS:
            set_font(fid, slot)
        return None


label mas_os_setup:
    python:
        store.mas_os.enter_shell()
        store.mas_os.setup_step = 0
        if store.mas_os.setup_from not in ("settings", "boot"):
            store.mas_os.setup_from = "boot"
    $ quick_menu = False
    $ _confirm_quit = False
    $ config.allow_skipping = False
    window hide
    call screen mas_os_setup
    $ _setup_came = store.mas_os.setup_from
    $ store.mas_os.setup_from = "boot"
    if _setup_came == "settings":
        jump mas_os_settings
    return


screen mas_os_setup():
    modal True
    zorder 200

    $ step = store.mas_os.setup_step
    $ title = store.mas_os.setup_title()
    $ last = store.mas_os.SETUP_LAST
    $ packs = store.mas_os.ddlc_packs() if step == 1 else []
    $ files_ok = store.mas_os.ddlc_all_ok()
    $ from_settings = store.mas_os.setup_from == "settings"

    use mas_os_bg

    text _("Установка MAS OS") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text title:
        style "mas_os_subtitle"
        xpos 48
        ypos 58

    hbox:
        xpos 48
        ypos 88
        spacing 8

        for i in range(last + 1):
            frame:
                xysize (18, 8)
                background Solid(store.mas_os.theme_color("accent") if i == step else store.mas_os.theme_color("btn"))

    frame at store.mas_os.t_pop(0.06):
        style "mas_os_panel"
        xpos 48
        ypos 110
        xysize (1184, 500)
        padding (24, 18)

        viewport:
            xysize (1136, 464)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 1100

                if step == 0:
                    text _("Добро пожаловать"):
                        style "mas_os_subtitle"

                    text _("Это оболочка порта до запуска комнаты Моники. Сейчас проверим файлы оригинальной DDLC и выставим внешний вид."):
                        style "mas_os_body"
                        xsize 1080

                    text _("Модификация содержит спойлеры. Её стоит ставить после прохождения оригинальной Doki Doki Literature Club."):
                        style "mas_os_hint"
                        xsize 1080

                    text _("Позже мастер можно открыть снова: Настройки → Система."):
                        style "mas_os_hint"

                    textbutton _("Пропустить настройку"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 280
                        action Function(store.mas_os.setup_skip)

                elif step == 1:
                    text _("Архивы оригинальной DDLC"):
                        style "mas_os_subtitle"

                    text _("Нужны audio.rpa, images.rpa, scripts.rpa и fonts.rpa в папке game. На Android они часто уже внутри приложения — тогда строка будет зелёной."):
                        style "mas_os_hint"
                        xsize 1080

                    for row in packs:
                        frame:
                            style "mas_os_panel"
                            background Solid(store.mas_os.theme_color("panel2"))
                            xsize 1080
                            padding (12, 10)

                            hbox:
                                spacing 12
                                yalign 0.5

                                frame:
                                    xysize (12, 12)
                                    background Solid("#3DFF9A" if row["ok"] else "#FF3B5C")
                                    yalign 0.5

                                text row["rpa"]:
                                    style "mas_os_body"
                                    yalign 0.5
                                    min_width 180
                                    substitute False

                                text row["how"]:
                                    style "mas_os_hint"
                                    yalign 0.5
                                    substitute False

                    if files_ok:
                        text _("Все ресурсы на месте. Можно идти дальше."):
                            style "mas_os_body"
                    else:
                        text _("Чего-то не хватает. Скачай DDLC с официального сайта и скопируй четыре .rpa в папку game этого мода, затем нажми «Проверить снова»."):
                            style "mas_os_body"
                            xsize 1080

                    hbox:
                        spacing 12

                        for cap, url in store.mas_os.DDLC_URLS:
                            textbutton cap:
                                style "mas_os_nav_btn"
                                text_style "mas_os_nav_btn_text"
                                xsize 320
                                action Function(store.mas_os.open_site, url)

                    textbutton _("Проверить снова"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 240
                        action Function(store.mas_os.setup_recheck)

                elif step == 2:
                    text _("Тема, обои и текстбокс. Это можно сменить в любой момент в настройках."):
                        style "mas_os_hint"

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 1080
                        padding (16, 12)
                        use mas_os_theme_toggle(width=1040)

                    use mas_os_onoff(
                        _("Затемнение поверх обоев"),
                        _("Текст лучше читается на ярких картинках."),
                        "_mas_os_wp_dim",
                    )

                    text _("Обои"):
                        style "mas_os_subtitle"

                    $ wp_cur = store.mas_os.wallpaper_id()
                    $ wp_pack = store.mas_os.wallpaper_grid_cells()
                    $ wp_nrows = wp_pack[1]
                    $ wp_cells = wp_pack[2]
                    grid 2 wp_nrows:
                        spacing 8
                        xsize 1080

                        for cell in wp_cells:
                            if cell:
                                button:
                                    style "mas_os_side_btn"
                                    xsize 530
                                    ysize 80
                                    selected (cell[0] == wp_cur)
                                    action Function(store.mas_os.set_wallpaper, cell[0])

                                    hbox:
                                        spacing 10
                                        yalign 0.5
                                        xoffset 8

                                        if cell[2]:
                                            add store.mas_os.fit_image(cell[2], 160, 56):
                                                yalign 0.5
                                        else:
                                            frame:
                                                xysize (160, 56)
                                                background Solid(store.mas_os.theme_color("bg"))
                                                yalign 0.5

                                        text cell[1]:
                                            style "mas_os_side_btn_text"
                                            yalign 0.5
                                            substitute False
                            else:
                                null

                    text _("Цвет текстбокса"):
                        style "mas_os_subtitle"

                    $ tb_cur = store.mas_os.textbox_id()
                    grid 2 2:
                        spacing 8
                        xsize 1080

                        for tid, ttitle, tpath in store.mas_os.TEXTBOX_COLORS:
                            button:
                                style "mas_os_side_btn"
                                xsize 530
                                ysize 80
                                selected (tid == tb_cur)
                                action Function(store.mas_os.set_textbox, tid)

                                hbox:
                                    spacing 10
                                    yalign 0.5
                                    xoffset 8

                                    add store.mas_os.fit_image(tpath, 210, 52):
                                        yalign 0.5

                                    text ttitle:
                                        style "mas_os_side_btn_text"
                                        yalign 0.5

                elif step == 3:
                    text _("Основной шрифт диалога. Остальные слоты (меню, UI, записки) — в настройках оформления."):
                        style "mas_os_hint"
                        xsize 1080

                    $ f_cur = store.mas_os.font_id("dialogue")
                    grid 2 4:
                        spacing 8
                        xsize 1080

                        for fid, ftitle, fpath in store.mas_os.FONT_PACKS:
                            button:
                                style "mas_os_side_btn"
                                xsize 530
                                ysize 52
                                selected (fid == f_cur)
                                action Function(store.mas_os.set_font, fid, "dialogue")

                                text ftitle:
                                    font fpath
                                    size 16
                                    color store.mas_os.theme_color("body")
                                    outlines []
                                    xoffset 12
                                    yalign 0.5
                                    substitute False

                        null

                    textbutton _("Применить этот шрифт ко всем слотам"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 420
                        action Function(store.mas_os.set_font_all, f_cur)

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 1080
                        padding (16, 12)
                        use mas_os_motion_toggle(width=1040)

                    text _("Анимация «Запустить MAS»"):
                        style "mas_os_subtitle"

                    $ launch_cur = store.mas_os.launch_anim_id()
                    vbox:
                        spacing 6

                        for aid, atitle, ahint in store.mas_os.LAUNCH_ANIMS:
                            button:
                                style "mas_os_side_btn"
                                xsize 1080
                                ysize 64
                                selected (aid == launch_cur)
                                action Function(store.mas_os.set_launch_anim, aid)

                                vbox:
                                    spacing 2
                                    yalign 0.5
                                    xoffset 12

                                    text atitle:
                                        style "mas_os_side_btn_text"
                                        substitute False

                                    text ahint:
                                        style "mas_os_hint"
                                        size 13
                                        xsize 1040
                                        substitute False

                elif step == 4:
                    text _("Как открывать порт и что показать на главной."):
                        style "mas_os_hint"

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 1080
                        padding (16, 12)
                        use mas_os_boot_toggle(width=1040)

                    use mas_os_onoff(
                        _("Звуки кнопок MAS OS"),
                        _("Щелчки при наведении и нажатии."),
                        "_mas_os_sfx",
                    )

                    use mas_os_onoff(
                        _("Виджет привязанности"),
                        _("Карточка Моники на главной."),
                        "_mas_os_aff_widget",
                    )

                    use mas_os_onoff(
                        _("Виджет плеера"),
                        _("Музыка на главной."),
                        "_mas_os_music_widget",
                    )

                    use mas_os_onoff(
                        _("Спрашивать перед выключением"),
                        _("Окно «да/нет» на Выключение."),
                        "_mas_os_quit_confirm",
                    )

                    text _("Первое вступление Моники"):
                        style "mas_os_subtitle"

                    text _("Новичку — «Не пропускать». Если уже ставил мод — «Только подсказки». CTRL в комнате всё равно выключен, поэтому это единственный безопасный пропуск."):
                        style "mas_os_hint"
                        xsize 1080

                    use mas_os_intro_skip_picker(width=1080)

                else:
                    text _("MAS OS готов"):
                        style "mas_os_subtitle"

                    if files_ok:
                        text _("Файлы DDLC на месте, оформление сохранено. Дальше откроется оболочка — оттуда можно запустить комнату Моники."):
                            style "mas_os_body"
                            xsize 1080
                    else:
                        text _("Оформление сохранено, но архивы DDLC всё ещё неполные. Игра может не запуститься, пока не скопируешь .rpa в папку game."):
                            style "mas_os_body"
                            xsize 1080

                    text _("Повторить мастер: Настройки → Система → Установщик MAS OS.\nСбросить внешний вид: там же, «Сбросить настройки»."):
                        style "mas_os_hint"
                        xsize 1080

    hbox:
        xpos 48
        ypos 640
        spacing 12

        if step > 0:
            textbutton _("Назад"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                action Function(store.mas_os.setup_back)
        elif from_settings:
            textbutton _("Закрыть"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                action Return("settings")

        if step < last:
            textbutton _("Далее"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                action Function(store.mas_os.setup_next)
        else:
            textbutton _("Готово"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                action Function(store.mas_os.setup_finish)

    if step == 0:
        key "K_ESCAPE" action If(from_settings, Return("settings"), Function(store.mas_os.setup_skip))
        key "K_AC_BACK" action If(from_settings, Return("settings"), Function(store.mas_os.setup_skip))
    elif step > 0:
        key "K_ESCAPE" action Function(store.mas_os.setup_back)
        key "K_AC_BACK" action Function(store.mas_os.setup_back)
