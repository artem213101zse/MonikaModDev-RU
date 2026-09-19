# -*- coding: utf-8 -*-
# --- FILE MAP ---
# mas_os_settings_win.rpy — вид настроек как Параметры Windows 10
#
# Старый экран живёт в mas_os_settings.rpy (mas_os_settings_classic).
# Сюда попадаем, если persistent._mas_os_settings_ui == "win10".
# Сначала плитки разделов, внутри — левое меню и содержимое справа.
# «Центр обновления» собирает проверку, новости и тесты.
# ---

screen mas_os_settings_win():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    timer 0.5 repeat True action Function(store.mas_os.upd_tick)

    use mas_os_bg

    if store.mas_os.settings_page == "home":
        use mas_os_settings_win_home
    else:
        use mas_os_settings_win_cat

    if store.mas_os.settings_page == "home":
        use mas_os_app_nav
    else:
        key "K_ESCAPE" action Function(store.mas_os.set_settings_page, "home")
        key "K_AC_BACK" action Function(store.mas_os.set_settings_page, "home")


screen mas_os_settings_win_home():
    $ cats = store.mas_os.SET_WIN_CATS
    $ ncat = len(cats)

    text _("Параметры"):
        style "mas_os_title"
        xpos 48
        ypos 22

    text _("Как в Windows 10: сначала раздел, потом меню слева. Старый вид — в Система → Вид настроек."):
        style "mas_os_hint"
        xpos 48
        ypos 66

    for i in range(ncat):
        $ cat_id, title, hint, icname, hue = cats[i]
        $ _x = 48 + (i % 3) * 390
        $ _y = 118 + (i // 3) * 168
        button:
            style "mas_os_win_tile"
            xpos _x
            ypos _y
            hover_sound store.mas_os.os_hover()
            activate_sound store.mas_os.os_activate()
            action Function(store.mas_os.set_settings_page, cat_id)
            at store.mas_os.t_tile(0.04 * i)

            hbox:
                spacing 16
                yalign 0.5
                xoffset 8

                if store.mas_os.icon_path(icname):
                    add store.mas_os.fit_image(store.mas_os.icon_path(icname), 52, 52):
                        yalign 0.5
                else:
                    frame:
                        xysize (52, 52)
                        background Solid(hue)
                        yalign 0.5

                vbox:
                    spacing 4
                    yalign 0.5
                    xsize 280

                    text title:
                        style "mas_os_win_tile_title"
                        substitute False

                    text hint:
                        style "mas_os_win_tile_hint"
                        substitute False


screen mas_os_settings_win_cat():
    $ page = store.mas_os.settings_page or "look"
    $ sub = store.mas_os.settings_sub or "theme"
    $ subs = store.mas_os.SET_WIN_SUBS.get(page) or []
    $ title = page
    $ icname = "settings"
    $ hue = "#C94A7A"
    for cat_id, ctitle, chint, cic, chue in store.mas_os.SET_WIN_CATS:
        if cat_id == page:
            $ title = ctitle
            $ icname = cic
            $ hue = chue

    button:
        xpos 36
        ypos 16
        xysize (56, 56)
        background None
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()
        action Function(store.mas_os.set_settings_page, "home")

        if store.mas_os.icon_path("back"):
            add store.mas_os.fit_image(store.mas_os.icon_path("back"), 28, 28):
                xalign 0.5
                yalign 0.5
        else:
            text _("‹"):
                style "mas_os_title"
                size 32
                xalign 0.5
                yalign 0.5

    hbox:
        xpos 100
        ypos 22
        spacing 12

        if store.mas_os.icon_path(icname):
            add store.mas_os.fit_image(store.mas_os.icon_path(icname), 36, 36):
                yalign 0.5

        text title:
            style "mas_os_title"
            size 32
            yalign 0.5
            substitute False

    frame:
        xpos 36
        ypos 84
        xysize (268, 548)
        background Solid(store.mas_os.theme_color("panel"))
        padding (8, 10)

        vbox:
            spacing 4

            for sid, slabel in subs:
                button:
                    xsize 252
                    ysize 44
                    background Solid(store.mas_os.theme_color("btn_sel") if sub == sid else "#00000000")
                    hover_background Solid(store.mas_os.theme_color("btn_hover"))
                    padding (10, 8)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action Function(store.mas_os.set_settings_sub, sid)

                    hbox:
                        spacing 8
                        yalign 0.5

                        frame:
                            xysize (4, 22)
                            background Solid(store.mas_os.theme_color("accent") if sub == sid else "#00000000")
                            yalign 0.5

                        text slabel:
                            style "mas_os_body"
                            size 16
                            yalign 0.5
                            color (store.mas_os.theme_color("title") if sub == sid else store.mas_os.theme_color("body"))
                            substitute False

    frame:
        xpos 316
        ypos 84
        xysize (928, 548)
        background Solid(store.mas_os.theme_color("panel"))
        padding (22, 16)

        viewport:
            id "mas_os_win_body"
            yadjustment store.mas_os.settings_scroll()
            xysize (884, 516)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 860

                if page == "look":
                    use mas_os_win_look(sub)
                elif page == "boot":
                    use mas_os_win_boot(sub)
                elif page == "iface":
                    use mas_os_win_iface(sub)
                elif page == "sound":
                    use mas_os_win_sound(sub)
                elif page == "update":
                    use mas_os_win_update(sub)
                else:
                    use mas_os_win_sys(sub)


screen mas_os_win_look(sub):
    if sub == "theme":
        text _("Тема"):
            style "mas_os_subtitle"
            size 26

        text _("Светлая или тёмная оболочка. Меняется сразу, без перезапуска."):
            style "mas_os_hint"

        hbox:
            spacing 16

            button:
                xysize (410, 150)
                background Solid("#1E0C14" if not store.mas_os.theme_light() else store.mas_os.theme_color("btn"))
                hover_background Solid(store.mas_os.theme_color("btn_hover"))
                selected (not store.mas_os.theme_light())
                padding (16, 14)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action Function(store.mas_os.set_theme, "dark")

                vbox:
                    spacing 8

                    frame:
                        xsize 378
                        ysize 72
                        background Solid("#14070d")

                    text _("Тёмная"):
                        style "mas_os_subtitle"
                    text _("Как комната ночью. Розовый текст на тёмном."):
                        style "mas_os_hint"
                        size 14

            button:
                xysize (410, 150)
                background Solid("#FFE8F1" if store.mas_os.theme_light() else store.mas_os.theme_color("btn"))
                hover_background Solid(store.mas_os.theme_color("btn_hover"))
                selected store.mas_os.theme_light()
                padding (16, 14)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action Function(store.mas_os.set_theme, "light")

                vbox:
                    spacing 8

                    frame:
                        xsize 378
                        ysize 72
                        background Solid("#FFF4F8")

                    text _("Светлая"):
                        style "mas_os_subtitle"
                    text _("Дневной вид. Тёмный текст на светлом."):
                        style "mas_os_hint"
                        size 14

        frame:
            style "mas_os_panel"
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (16, 12)
            use mas_os_motion_toggle(width=800)

        use mas_os_onoff(
            _("Каскад появления"),
            _("Плитки выезжают по очереди. Выкл — всё сразу."),
            "_mas_os_stagger",
            True,
            840,
        )

    elif sub == "background":
        text _("Фон"):
            style "mas_os_subtitle"
            size 26

        text _("Картинки из game/mod_assets/mas_os/wallpapers. PNG или JPG."):
            style "mas_os_hint"

        use mas_os_onoff(
            _("Затемнение поверх обоев"),
            _("Чтобы текст оставался читаемым."),
            "_mas_os_wp_dim",
            True,
            840,
        )

        $ wp_cur = store.mas_os.wallpaper_id()
        $ wp_pack = store.mas_os.wallpaper_grid_cells()
        $ wp_nrows = wp_pack[1]
        $ wp_cells = wp_pack[2]
        grid 2 wp_nrows:
            spacing 10
            xsize 840

            for cell in wp_cells:
                if cell:
                    button:
                        style "mas_os_side_btn"
                        xsize 410
                        ysize 100
                        selected (cell[0] == wp_cur)
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()
                        action Function(store.mas_os.open_wp_preview, cell[0], cell[2])

                        hbox:
                            spacing 12
                            yalign 0.5
                            xoffset 10

                            if cell[2]:
                                add store.mas_os.fit_image(cell[2], 240, 72):
                                    yalign 0.5
                            else:
                                frame:
                                    xysize (240, 72)
                                    background Solid(store.mas_os.theme_color("bg"))
                                    yalign 0.5

                            text cell[1]:
                                style "mas_os_side_btn_text"
                                yalign 0.5
                                xsize 130
                                substitute False
                else:
                    null

        use mas_os_store_link("wallpaper", "settings")

    elif sub == "colors":
        text _("Цвета"):
            style "mas_os_subtitle"
            size 26

        text _("Цвет текстбокса и куда его применять: оболочка, игра, календарь, пауза."):
            style "mas_os_hint"

        use mas_os_textbox_color(width=840)

    elif sub == "fonts":
        text _("Шрифты"):
            style "mas_os_subtitle"
            size 26

        text _("Каждый слот отдельно. Свои ttf/otf — через Склад, потом перезапуск."):
            style "mas_os_hint"

        for slot, caption, hint, persist_key, def_id in store.mas_os.FONT_SLOTS:
            use mas_os_font_slot(slot, caption, hint)

        use mas_os_store_link("font", "settings")

    elif sub == "hearts":
        text _("Привязанность"):
            style "mas_os_subtitle"
            size 26

        text _("Сердечки по бокам, когда привязанность растёт. «Тест» показывает стиль, в комнату не заходит."):
            style "mas_os_hint"

        $ heart_cur = store.mas_affhearts.current_style()
        $ _test_ic = store.mas_os.icon_path("view")
        vbox:
            spacing 8

            for hid, htitle, hhint in store.mas_affhearts.STYLE_ROWS:
                hbox:
                    spacing 8

                    button:
                        style "mas_os_side_btn"
                        xsize 680
                        ysize 76
                        selected (hid == heart_cur)
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()
                        action Function(store.mas_affhearts.set_style, hid)

                        vbox:
                            spacing 2
                            yalign 0.5
                            xoffset 12
                            xsize 640

                            text htitle:
                                style "mas_os_side_btn_text"
                                substitute False

                            text hhint:
                                style "mas_os_hint"
                                size 13
                                xsize 620
                                substitute False

                    button:
                        style "mas_os_side_btn"
                        xsize 148
                        ysize 76
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()
                        action Function(store.mas_affhearts.preview, hid)

                        hbox:
                            spacing 6
                            xalign 0.5
                            yalign 0.5

                            if _test_ic:
                                add store.mas_os.fit_image(_test_ic, 22, 22):
                                    yalign 0.5

                            text _("Тест"):
                                style "mas_os_side_btn_text"
                                yalign 0.5

    else:
        text _("Вид оболочки"):
            style "mas_os_subtitle"
            size 26

        text _("Плитки — крупные карточки. Рабочий стол — как extras в DDLC Plus."):
            style "mas_os_hint"

        frame:
            style "mas_os_panel"
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (16, 12)
            use mas_os_layout_toggle(width=800)


screen mas_os_win_boot(sub):
    if sub == "start":
        text _("При запуске"):
            style "mas_os_subtitle"
            size 26

        text _("Что открывать при холодном старте и как выходить из комнаты."):
            style "mas_os_hint"

        frame:
            style "mas_os_panel"
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (16, 12)
            use mas_os_boot_toggle(width=800)

        use mas_os_onoff(
            _("Спрашивать перед возвратом в OS"),
            _("Если выкл — кнопка MAS OS сразу завершает сессию."),
            "_mas_os_return_confirm",
            True,
            840,
        )

        use mas_os_onoff(
            _("Спрашивать перед выключением"),
            _("Подтверждение на главной, когда жмёшь «Выключение»."),
            "_mas_os_quit_confirm",
            True,
            840,
        )

    elif sub == "splash":
        text _("Заставка"):
            style "mas_os_subtitle"
            size 26

        text _("Ролик при входе в оболочку. «Тест» показывает его и возвращает сюда."):
            style "mas_os_hint"

        use mas_os_boot_splash_picker(width=840)

    elif sub == "intro":
        text _("Вступление"):
            style "mas_os_subtitle"
            size 26

        text _("При первом заходе в комнату CTRL не работает. Новичку лучше полное вступление."):
            style "mas_os_hint"

        frame:
            style "mas_os_panel"
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (16, 12)
            use mas_os_intro_skip_picker(width=800)

    else:
        text _("Анимация MAS"):
            style "mas_os_subtitle"
            size 26

        text _("Играется при «Запустить MAS». Тест не заходит в комнату."):
            style "mas_os_hint"

        $ launch_cur = store.mas_os.launch_anim_id()
        $ _test_ic = store.mas_os.icon_path("view")
        vbox:
            spacing 8

            for aid, atitle, ahint in store.mas_os.LAUNCH_ANIMS:
                hbox:
                    spacing 8

                    button:
                        style "mas_os_side_btn"
                        xsize 680
                        ysize 76
                        selected (aid == launch_cur)
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()
                        action Function(store.mas_os.set_launch_anim, aid)

                        vbox:
                            spacing 2
                            yalign 0.5
                            xoffset 12
                            xsize 640

                            text atitle:
                                style "mas_os_side_btn_text"
                                substitute False

                            text ahint:
                                style "mas_os_hint"
                                size 13
                                xsize 620
                                substitute False

                    button:
                        style "mas_os_side_btn"
                        xsize 148
                        ysize 76
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()
                        action [
                            Function(store.mas_os.start_launch_preview, aid),
                            Show("mas_os_launch_anim"),
                        ]

                        hbox:
                            spacing 6
                            xalign 0.5
                            yalign 0.5

                            if _test_ic:
                                add store.mas_os.fit_image(_test_ic, 22, 22):
                                    yalign 0.5

                            text _("Тест"):
                                style "mas_os_side_btn_text"
                                yalign 0.5


screen mas_os_win_iface(sub):
    if sub == "home":
        text _("Главная"):
            style "mas_os_subtitle"
            size 26

        text _("Карточки на домашнем экране оболочки."):
            style "mas_os_hint"

        use mas_os_onoff(
            _("Виджет привязанности на главной"),
            _("Карточка «Моника» слева. На саму привязанность не влияет."),
            "_mas_os_aff_widget",
            True,
            840,
        )

        use mas_os_onoff(
            _("Виджет плеера на главной"),
            _("Карточка с треком, паузой и громкостью."),
            "_mas_os_music_widget",
            True,
            840,
        )
    else:
        text _("В игре"):
            style "mas_os_subtitle"
            size 26

        text _("Что показывать в комнате Моники и в меню паузы."):
            style "mas_os_hint"

        use mas_os_onoff(
            _("Кнопка MAS OS"),
            _("Показывает кнопку возврата в оболочку. Место и стиль — ниже."),
            "_mas_os_talk_btn",
            True,
            840,
        )

        text _("Где показать"):
            style "mas_os_hint"

        vbox:
            spacing 6
            for pid, ptitle, phint in store.mas_os.OSBTN_PLACES:
                button:
                    style "mas_os_side_btn"
                    xsize 840
                    ysize 64
                    selected (store.mas_os.osbtn_place() == pid)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action Function(store.mas_os.set_osbtn_place, pid)

                    vbox:
                        spacing 2
                        yalign 0.5
                        xoffset 12

                        text ptitle:
                            style "mas_os_side_btn_text"
                            substitute False

                        text phint:
                            style "mas_os_hint"
                            size 13
                            substitute False

        text _("Стиль кнопки"):
            style "mas_os_hint"

        grid 2 4:
            spacing 8
            xsize 840

            for sid, stitle, shint in store.mas_os.OSBTN_STYLES:
                button:
                    style "mas_os_side_btn"
                    xsize 410
                    ysize 64
                    selected (store.mas_os.osbtn_style() == sid)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action Function(store.mas_os.set_osbtn_style, sid)

                    vbox:
                        spacing 2
                        yalign 0.5
                        xoffset 12
                        xsize 380

                        text stitle:
                            style "mas_os_side_btn_text"
                            substitute False

                        text shint:
                            style "mas_os_hint"
                            size 12
                            substitute False

        use mas_os_onoff(
            _("Пункт MAS OS в игровом меню"),
            _("В паузе рядом с настройками."),
            "_mas_os_menu_btn",
            True,
            840,
        )

        use mas_os_pref_onoff(
            _("Сенсорное пианино"),
            _("Клавиши внизу экрана. Палец и мышь нажимают ноты, как настоящие клавиши."),
            store.mas_piano_keys.piano_touch_on(),
            Function(store.mas_piano_keys.set_piano_touch, True),
            Function(store.mas_piano_keys.set_piano_touch, False),
        )

        use mas_os_pref_onoff(
            _("Отступы у сенсорного пианино"),
            _("Зазор снизу и щели между клавишами. Выкл — клавиши впритык к краям."),
            store.mas_piano_keys.piano_gaps_on(),
            Function(store.mas_piano_keys.set_piano_gaps, True),
            Function(store.mas_piano_keys.set_piano_gaps, False),
        )


screen mas_os_win_sound(sub):
    if sub == "volume":
        text _("Громкость"):
            style "mas_os_subtitle"
            size 26

        text _("Общая с игрой: что выставишь здесь, то будет и у Моники."):
            style "mas_os_hint"

        use mas_os_vol_row(
            _("Музыка"),
            _("Плеер MAS OS и фон в комнате."),
            "music volume",
            "music",
        )

        use mas_os_vol_row(
            _("Звуки"),
            _("Клики меню, UI."),
            "sound volume",
            "sound",
        )

        use mas_os_vol_row(
            _("Окружение"),
            _("Фоновые шумы комнаты, если канал есть."),
            "mixer amb volume",
            None,
        )

        use mas_os_pref_onoff(
            _("Мьют музыки"),
            _("Тишина без сброса ползунка."),
            store.mas_os.player_music_muted(),
            Function(store.mas_os.player_set_music_mute, True),
            Function(store.mas_os.player_set_music_mute, False),
        )

        use mas_os_pref_onoff(
            _("Выключить весь звук"),
            _("Все микшеры сразу."),
            store.mas_os.player_all_muted(),
            Function(store.mas_os.player_set_all_mute, True),
            Function(store.mas_os.player_set_all_mute, False),
        )

    elif sub == "player":
        text _("Плеер"):
            style "mas_os_subtitle"
            size 26

        use mas_os_onoff(
            _("Играть музыку в оболочке"),
            _("При входе сразу продолжает последний трек."),
            "_mas_os_music_autoplay",
            False,
            840,
        )

        frame:
            style "mas_os_panel"
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (16, 12)
            use mas_os_loop_toggle(width=800)

        use mas_os_onoff(
            _("Перемешать"),
            _("Вперёд/назад и автосмена берут случайный трек."),
            "_mas_os_music_shuffle",
            False,
            840,
        )

        use mas_os_store_link("music", "settings")
        use mas_os_ibutton(_("Обновить плейлист"), Function(store.mas_os.player_rescan), "R", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="reboot")

    else:
        text _("Щелчки"):
            style "mas_os_subtitle"
            size 26

        use mas_os_onoff(
            _("Звуки кнопок MAS OS"),
            _("Наведение и нажатие плиток, карточек и тумблеров."),
            "_mas_os_sfx",
            True,
            840,
        )


screen mas_os_win_update(sub):
    $ _rows = store.mas_os.upd_news_rows()
    $ _local = store.mas_os.upd_local_version()
    $ _mas = store.mas_os.upd_mas_version()
    $ _remote = store.mas_os.upd_remote or ""
    $ _title = store.mas_os.upd_news_title or ""
    $ _ch = store.mas_os.upd_channel_label()
    $ _fn = store.mas_os.upd_channel_file()

    if sub == "status":
        text _("Центр обновления"):
            style "mas_os_subtitle"
            size 26

        text store.mas_os.upd_status_line():
            style "mas_os_hint"
            substitute False

        frame:
            background Solid(store.mas_os.theme_color("panel2"))
            xsize 840
            padding (18, 14)

            vbox:
                spacing 6

                text _("Порт [_local]"):
                    style "mas_os_subtitle"
                    size 22

                text _("MAS [_mas]"):
                    style "mas_os_hint"

                if store.mas_os.upd_has_update():
                    text _("Доступна [_remote]"):
                        style "mas_os_subtitle"
                        color "#6FCF97"
                else:
                    text _("Установлена актуальная сборка порта."):
                        style "mas_os_hint"

                text _("Канал: [_ch]  ·  [_fn]"):
                    style "mas_os_hint"

        use mas_os_ibutton(_("Проверить обновления порта"), Function(store.mas_os.upd_manual), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="updates", badge=store.mas_os.upd_has_update())

        if store.mas_os.upd_has_update():
            use mas_os_ibutton(_("Открыть новости"), Function(store.mas_os.upd_show_available), "N", "#7A4A9A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="docs")

    elif sub == "news":
        text _("Что нового"):
            style "mas_os_subtitle"
            size 26

        if _title:
            text _title:
                style "mas_os_subtitle"
                substitute False

        if not _rows:
            text _("Пока нет текста с сервера. Проверь обновления или открой локальный тест."):
                style "mas_os_hint"
        else:
            frame:
                background Solid(store.mas_os.theme_color("panel2"))
                xsize 840
                padding (16, 12)

                vbox:
                    spacing 8
                    xsize 800

                    for _blk in _rows:
                        if _blk["kind"] == "space":
                            null height 6
                        elif _blk["kind"] == "hr":
                            frame:
                                xsize 800
                                ysize 2
                                background Solid(store.mas_os.theme_color("accent"))
                        elif _blk["kind"] == "h1":
                            text _blk["text"]:
                                style "mas_os_title"
                                size 24
                                xsize 800
                                substitute False
                        elif _blk["kind"] == "h2":
                            text _blk["text"]:
                                style "mas_os_subtitle"
                                size 20
                                xsize 800
                                substitute False
                        elif _blk["kind"] == "h3":
                            text _blk["text"]:
                                style "mas_os_subtitle"
                                size 17
                                xsize 800
                                substitute False
                        elif _blk["kind"] == "li":
                            hbox:
                                spacing 8
                                xsize 800
                                xfill True

                                text _blk.get("mark", "•"):
                                    size 16
                                    color store.mas_os.theme_color("subtitle")
                                    outlines []
                                    xsize 28
                                    text_align 0.0
                                    xalign 0.0
                                    substitute False

                                text _blk["text"]:
                                    style "mas_os_body"
                                    size 16
                                    xsize 750
                                    text_align 0.0
                                    xalign 0.0
                                    layout "tex"
                                    substitute False
                        elif _blk["kind"] == "quote":
                            text _blk["text"]:
                                style "mas_os_hint"
                                italic True
                                size 16
                                xsize 800
                                text_align 0.0
                                xalign 0.0
                                layout "tex"
                                substitute False
                        else:
                            text _blk["text"]:
                                style "mas_os_body"
                                size 16
                                xsize 800
                                text_align 0.0
                                xalign 0.0
                                layout "tex"
                                substitute False

        if store.mas_os.upd_has_update():
            use mas_os_ibutton(_("Открыть окно обновления"), Function(store.mas_os.upd_show_available), "N", "#7A4A9A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="docs")

    else:
        text _("Проверка"):
            style "mas_os_subtitle"
            size 26

        text _("GitHub — для игроков. Локальный файл — чтобы глянуть окно, не трогая сервер."):
            style "mas_os_hint"

        use mas_os_ibutton(_("Проверить обновления порта"), Function(store.mas_os.upd_manual), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="updates", badge=store.mas_os.upd_has_update())
        use mas_os_ibutton(_("Локальный тест окна"), Function(store.mas_os.upd_local_test), "T", "#7A4A9A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="updates")
        use mas_os_ibutton(_("Тест бегущей строки"), Function(store.mas_os.news_test_ticker), "T", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="megaphone")
        use mas_os_ibutton(_("Тест баннера"), Function(store.mas_os.news_test_banner), "T", "#4A8A6A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="notify")
        use mas_os_ibutton(_("Тест строки + баннера"), Function(store.mas_os.news_test_both), "T", "#8A6A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="megaphone")

        text _("Тестовый канал — в Debug → Обновления."):
            style "mas_os_hint"


screen mas_os_win_sys(sub):
    if sub == "general":
        text _("Общие"):
            style "mas_os_subtitle"
            size 26

        use mas_os_android_saves_row

        use mas_os_ibutton(_("Установщик MAS OS"), MASOSGo("setup"), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="boot")

        use mas_os_ibutton(_("Сбросить настройки MAS OS"), Show("mas_os_confirm", message=_("Сбросить оформление, звук и поведение оболочки к заводским?\nСкачанные файлы и прочитанные события не трогаем."), yes_action=[Function(store.mas_os.reset_os_settings), Hide("mas_os_confirm")], no_action=Hide("mas_os_confirm")), "R", "#8A3A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="reboot")

        text _("Оболочка не считает посещение комнаты, пока не нажато «Запустить MAS»."):
            style "mas_os_hint"

    elif sub == "privacy":
        text _("Контент"):
            style "mas_os_subtitle"
            size 26

        use mas_os_onoff(
            _("Скрыть LGBT-контент"),
            _("Скрывает в разговорах варианты пола кроме мужского и женского. Уже записанный в сейве пол не стирается."),
            "_mas_os_hide_lgbt",
            False,
            840,
        )

    else:
        text _("Вид настроек"):
            style "mas_os_subtitle"
            size 26

        text _("Новый вид — плитки как Параметры Windows 10. Классический — старый список слева."):
            style "mas_os_hint"

        hbox:
            spacing 16

            button:
                xysize (400, 130)
                background Solid(store.mas_os.theme_color("btn_sel") if not store.mas_os.settings_ui_classic() else store.mas_os.theme_color("btn"))
                hover_background Solid(store.mas_os.theme_color("btn_hover"))
                padding (16, 14)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action Function(store.mas_os.set_settings_ui, "win10")

                vbox:
                    spacing 6
                    text _("Новый"):
                        style "mas_os_subtitle"
                    text _("Плитки разделов, слева меню как в Персонализации Windows 10."):
                        style "mas_os_hint"
                        size 14

            button:
                xysize (400, 130)
                background Solid(store.mas_os.theme_color("btn_sel") if store.mas_os.settings_ui_classic() else store.mas_os.theme_color("btn"))
                hover_background Solid(store.mas_os.theme_color("btn_hover"))
                padding (16, 14)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action Function(store.mas_os.set_settings_ui, "classic")

                vbox:
                    spacing 6
                    text _("Классический"):
                        style "mas_os_subtitle"
                    text _("Как раньше: категории слева, все опции одним списком справа."):
                        style "mas_os_hint"
                        size 14


style mas_os_win_tile is default:
    xsize 374
    ysize 148
    padding (16, 16)
    idle_background Solid("#1E0C14")
    hover_background Solid("#3A1524")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_win_tile_title is default:
    font gui.default_font
    size 22
    color "#FFE6F3"
    outlines []

style mas_os_win_tile_hint is default:
    font gui.default_font
    size 14
    color "#C989A8"
    outlines []
