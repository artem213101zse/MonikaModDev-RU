# MAS OS — Settings (category sidebar) and About (link cards).

init -5 python in mas_os:
    import store

    SET_CATS = [
        ("boot", "Запуск", "boot", "#C94A7A"),
        ("look", "Оформление", "appearance", "#7A4A9A"),
        ("iface", "Интерфейс", "interface", "#4A8AAA"),
        ("sound", "Звук", "sound", "#8A6A4A"),
        ("sys", "Система", "system", "#6A6A7A"),
    ]

    ABOUT_LINKS = [
        {
            "title": "Репозиторий порта",
            "hint": "MonikaModDev-RU",
            "url": "https://github.com/artem213101zse/MonikaModDev-RU",
            "icon": "github-port",
            "hue": "#C94A7A",
        },
        {
            "title": "MAS на GitHub",
            "hint": "официальный мод",
            "url": "https://github.com/Monika-After-Story/MonikaModDev",
            "icon": "mas-official",
            "hue": "#FF8AC4",
        },
        {
            "title": "Ren'Py",
            "hint": "движок игры",
            "url": "https://www.renpy.org/",
            "icon": "renpy",
            "hue": "#4A8AAA",
        },
        {
            "title": "DDLC",
            "hint": "оригинал Team Salvato",
            "url": "https://ddlc.moe",
            "icon": "ddlc",
            "hue": "#8A4A7A",
        },
        {
            "title": "Team Salvato",
            "hint": "авторы DDLC",
            "url": "https://teamsalvato.com",
            "icon": "team-salvato",
            "hue": "#8A6A4A",
        },
    ]

    def open_site(url):
        if not url:
            return False
        try:
            store.renpy.run(store.OpenURL(url))
            return True
        except Exception:
            pass
        try:
            import webbrowser
            webbrowser.open(url)
            return True
        except Exception:
            return False


screen mas_os_font_slot(slot, caption, hint):
    $ f_cur = store.mas_os.font_id(slot)
    $ packs = store.mas_os.font_picker_rows()
    $ f_rows = (len(packs) + 1) // 2
    if f_rows < 1:
        $ f_rows = 1

    vbox:
        spacing 6
        xfill True

        text caption:
            style "mas_os_subtitle"

        text hint:
            style "mas_os_hint"

        grid 2 f_rows:
            spacing 8
            xsize 760

            for fid, ftitle, fpath, preview in packs:
                button:
                    style "mas_os_side_btn"
                    xsize 370
                    ysize 52
                    selected (fid == f_cur)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action Function(store.mas_os.set_font, fid, slot)

                    text ftitle:
                        font preview
                        size 16
                        color store.mas_os.theme_color("body")
                        outlines []
                        xoffset 12
                        yalign 0.5
                        substitute False

            if len(packs) % 2:
                null


screen mas_os_onoff(caption, hint, flag_name, default=True):
    $ on = store.mas_os.flag(flag_name, default)

    frame:
        style "mas_os_panel"
        xsize 760
        padding (16, 12)

        hbox:
            spacing 12
            xfill True

            vbox:
                xsize 470
                spacing 4

                text caption:
                    style "mas_os_subtitle"

                text hint:
                    style "mas_os_hint"

            frame:
                style "mas_os_toggle_track"
                xsize 236
                ysize 44
                padding (4, 4)
                yalign 0.5

                hbox:
                    spacing 4

                    textbutton _("Вкл"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 110
                        selected on
                        action Function(store.mas_os.set_flag, flag_name, True)

                    textbutton _("Выкл"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 110
                        selected (not on)
                        action Function(store.mas_os.set_flag, flag_name, False)


screen mas_os_link_card(item, delay=0.08):
    $ ic = store.mas_os.icon_path(item.get("icon"))
    $ shown = store.mas_os.doc_image_path(item.get("image")) if not ic else None

    button:
        style "mas_os_link_card"
        at store.mas_os.t_tile(delay)
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()
        action Function(store.mas_os.open_site, item["url"])

        vbox:
            spacing 0

            frame:
                xysize (220, 96)
                background Solid(store.mas_os.theme_color("panel2"))
                clipping True

                if ic:
                    add store.mas_os.fit_image(ic, 88, 88):
                        xalign 0.5
                        yalign 0.5
                elif shown:
                    add store.mas_os.fit_image(shown, 220, 96):
                        xalign 0.5
                        yalign 0.5
                else:
                    text _("нет картинки"):
                        style "mas_os_hint"
                        xalign 0.5
                        yalign 0.5

            frame:
                xsize 220
                ysize 56
                background Solid(item.get("hue") or "#C94A7A")
                padding (8, 6)

                vbox:
                    spacing 0
                    xfill True

                    text item["title"]:
                        style "mas_os_link_card_title"
                        substitute False

                    text item.get("hint") or "":
                        style "mas_os_link_card_hint"
                        substitute False


screen mas_os_settings():
    modal True
    zorder 200

    $ cat = store.mas_os.settings_cat or "boot"

    use mas_os_bg

    text _("Настройки") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text _("Слева разделы, справа параметры. То, что уже работает в оболочке.") at store.mas_os.t_pop(0.04):
        style "mas_os_hint"
        xpos 48
        ypos 58

    viewport:
        xpos 48
        ypos 100
        xysize (340, 510)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 8

            for cat_id, title, icname, hue in store.mas_os.SET_CATS:
                button:
                    style "mas_os_side_btn"
                    selected (cat == cat_id)
                    action Function(store.mas_os.set_settings_cat, cat_id)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    hbox:
                        spacing 10
                        yalign 0.5
                        xoffset 8

                        if store.mas_os.icon_path(icname):
                            add store.mas_os.fit_image(store.mas_os.icon_path(icname), 32, 32):
                                yalign 0.5
                        else:
                            frame:
                                xysize (32, 32)
                                background Solid(hue)
                                yalign 0.5

                                text icname:
                                    style "mas_os_glyph"
                                    xalign 0.5
                                    yalign 0.5

                        text title:
                            style "mas_os_side_btn_text"
                            yalign 0.5

    frame at store.mas_os.t_pop(0.06):
        style "mas_os_panel"
        xpos 410
        ypos 100
        xysize (822, 510)
        padding (20, 16)

        viewport:
            xysize (782, 478)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 760

                if cat == "boot":
                    text _("Запуск"):
                        style "mas_os_subtitle"

                    text _("Что открывать при холодном старте и как выходить из комнаты Моники."):
                        style "mas_os_hint"

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        padding (16, 12)
                        use mas_os_boot_toggle(width=720)

                    use mas_os_onoff(
                        _("Спрашивать перед возвратом в OS"),
                        _("Если выкл — кнопка MAS OS сразу завершает сессию без окна «да/нет»."),
                        "_mas_os_return_confirm",
                    )

                    use mas_os_onoff(
                        _("Спрашивать перед выключением"),
                        _("Подтверждение на главной, когда жмёшь «Выключение» или назад."),
                        "_mas_os_quit_confirm",
                    )

                    text _("Первое вступление Моники"):
                        style "mas_os_subtitle"

                    text _("При первом заходе в комнату CTRL не работает. Новичку лучше оставить полное вступление: там про разговор, музыку и игры. Если уже видел — можно сократить. Служебный код (удаление monika.chr, флаги) не пропускается."):
                        style "mas_os_hint"

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        padding (16, 12)
                        use mas_os_intro_skip_picker(width=720)

                    text _("Анимация запуска MAS"):
                        style "mas_os_subtitle"

                    text _("Играется при «Запустить MAS». «Тест» показывает ролик и возвращает сюда, игру не трогает."):
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
                                    xsize 604
                                    ysize 76
                                    selected (aid == launch_cur)
                                    hover_sound store.mas_os.os_hover()
                                    activate_sound store.mas_os.os_activate()
                                    action Function(store.mas_os.set_launch_anim, aid)

                                    vbox:
                                        spacing 2
                                        yalign 0.5
                                        xoffset 12
                                        xsize 560

                                        text atitle:
                                            style "mas_os_side_btn_text"
                                            substitute False

                                        text ahint:
                                            style "mas_os_hint"
                                            size 13
                                            xsize 540
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

                elif cat == "look":
                    text _("Оформление"):
                        style "mas_os_subtitle"

                    text _("Тема оболочки, анимации, обои, текстбокс и шрифты."):
                        style "mas_os_hint"

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        padding (16, 12)
                        use mas_os_theme_toggle(width=720)

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        padding (16, 12)
                        use mas_os_motion_toggle(width=720)

                    use mas_os_onoff(
                        _("Каскад появления"),
                        _("Плитки выезжают по очереди. Выкл — всё сразу."),
                        "_mas_os_stagger",
                    )

                    text _("Обои MAS OS"):
                        style "mas_os_subtitle"

                    text _("Картинки из папки game/mod_assets/mas_os/wallpapers. PNG или JPG. На Android файлы из APK и скачанные со Склада подхватываются с диска автоматически."):
                        style "mas_os_hint"

                    use mas_os_onoff(
                        _("Затемнение поверх обоев"),
                        _("Чтобы розовый текст оставался читаемым."),
                        "_mas_os_wp_dim",
                    )

                    $ wp_cur = store.mas_os.wallpaper_id()
                    $ wp_pack = store.mas_os.wallpaper_grid_cells()
                    $ wp_nrows = wp_pack[1]
                    $ wp_cells = wp_pack[2]
                    grid 2 wp_nrows:
                        spacing 10
                        xsize 760

                        for cell in wp_cells:
                            if cell:
                                button:
                                    style "mas_os_side_btn"
                                    xsize 370
                                    ysize 92
                                    selected (cell[0] == wp_cur)
                                    hover_sound store.mas_os.os_hover()
                                    activate_sound store.mas_os.os_activate()
                                    action Function(store.mas_os.set_wallpaper, cell[0])

                                    hbox:
                                        spacing 10
                                        yalign 0.5
                                        xoffset 10

                                        if cell[2]:
                                            add store.mas_os.fit_image(cell[2], 210, 56):
                                                yalign 0.5
                                        else:
                                            frame:
                                                xysize (210, 56)
                                                background Solid(store.mas_os.theme_color("bg"))
                                                yalign 0.5

                                        text cell[1]:
                                            style "mas_os_side_btn_text"
                                            yalign 0.5
                                            xsize 120
                                            substitute False
                            else:
                                null

                    use mas_os_store_link("wallpaper", "settings")

                    text _("Цвет текстбокса"):
                        style "mas_os_subtitle"

                    text _("Меняется и в оболочке, и у Моники. Светлая тема пока без отдельных файлов."):
                        style "mas_os_hint"

                    $ tb_cur = store.mas_os.textbox_id()
                    grid 2 2:
                        spacing 10
                        xsize 760

                        for tid, ttitle, tpath in store.mas_os.TEXTBOX_COLORS:
                            button:
                                style "mas_os_side_btn"
                                xsize 370
                                ysize 92
                                selected (tid == tb_cur)
                                hover_sound store.mas_os.os_hover()
                                activate_sound store.mas_os.os_activate()
                                action Function(store.mas_os.set_textbox, tid)

                                hbox:
                                    spacing 10
                                    yalign 0.5
                                    xoffset 10

                                    add store.mas_os.fit_image(tpath, 210, 56):
                                        yalign 0.5

                                    text ttitle:
                                        style "mas_os_side_btn_text"
                                        yalign 0.5

                    use mas_os_store_link("textbox", "settings")

                    text _("Шрифты"):
                        style "mas_os_subtitle"

                    text _("Каждый слот отдельно. Свои ttf/otf — через Склад, потом перезапуск."):
                        style "mas_os_hint"

                    for slot, caption, hint, persist_key, def_id in store.mas_os.FONT_SLOTS:
                        use mas_os_font_slot(slot, caption, hint)

                    use mas_os_store_link("font", "settings")

                elif cat == "iface":
                    text _("Интерфейс"):
                        style "mas_os_subtitle"

                    text _("Что показывать на главной и внутри игры."):
                        style "mas_os_hint"

                    use mas_os_onoff(
                        _("Кнопка MAS OS в «Эй, Моника…»"),
                        _("Картинка-кнопка слева сверху на экране разговора."),
                        "_mas_os_talk_btn",
                    )

                    use mas_os_onoff(
                        _("Пункт MAS OS в игровом меню"),
                        _("В паузе рядом с настройками."),
                        "_mas_os_menu_btn",
                    )

                    use mas_os_onoff(
                        _("Виджет привязанности на главной"),
                        _("Карточка «Моника» слева. На саму привязанность не влияет."),
                        "_mas_os_aff_widget",
                    )

                    use mas_os_onoff(
                        _("Виджет плеера на главной"),
                        _("Карточка с треком, паузой и громкостью. Полный список — плитка «Плеер»."),
                        "_mas_os_music_widget",
                    )

                elif cat == "sound":
                    text _("Звук"):
                        style "mas_os_subtitle"

                    text _("Громкость общая с игрой: что выставишь здесь, то будет и у Моники."):
                        style "mas_os_hint"

                    use mas_os_vol_row(
                        _("Музыка"),
                        _("Плеер MAS OS и фон в комнате."),
                        "music volume",
                        "music",
                    )

                    use mas_os_vol_row(
                        _("Звуки"),
                        _("Клики меню, UI. Не путать со щелчками оболочки ниже."),
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
                        _("Тишина без сброса ползунка. Плеер продолжает крутить трек."),
                        store.mas_os.player_music_muted(),
                        Function(store.mas_os.player_set_music_mute, True),
                        Function(store.mas_os.player_set_music_mute, False),
                    )

                    use mas_os_pref_onoff(
                        _("Выключить весь звук"),
                        _("Все микшеры сразу. То же, что «Без звука» в настройках игры."),
                        store.mas_os.player_all_muted(),
                        Function(store.mas_os.player_set_all_mute, True),
                        Function(store.mas_os.player_set_all_mute, False),
                    )

                    use mas_os_onoff(
                        _("Звуки кнопок MAS OS"),
                        _("Наведение и нажатие плиток, карточек и тумблеров."),
                        "_mas_os_sfx",
                    )

                    use mas_os_onoff(
                        _("Играть музыку в оболочке"),
                        _("При входе в MAS OS сразу продолжает последний трек. Иначе тишина, пока не нажмёшь play."),
                        "_mas_os_music_autoplay",
                        False,
                    )

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        padding (16, 12)
                        use mas_os_loop_toggle(width=720)

                    use mas_os_onoff(
                        _("Перемешать"),
                        _("Кнопки вперёд/назад и автосмена списка берут случайный трек."),
                        "_mas_os_music_shuffle",
                        False,
                    )

                    use mas_os_ibutton(_("Открыть плеер"), Return("player"), "Au", "#8A6A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="sound")

                    use mas_os_store_link("music", "settings")

                    use mas_os_ibutton(_("Обновить плейлист"), Function(store.mas_os.player_rescan), "R", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="reboot")

                    text _("Треки те же, что в музыкальном меню MAS: встроенные + папка custom_bgm. Новое с Склада подхватится после «Обновить плейлист»."):
                        style "mas_os_hint"

                else:
                    text _("Система"):
                        style "mas_os_subtitle"

                    text _("Обновления порта и служебное. Версия — в «О системе»."):
                        style "mas_os_hint"

                    text _("Каталог сабмодов — JSON-индекс. Ссылку меняют в разделе «Сабмоды» → Каталог. Пример схемы: game/mod_assets/mas_os/catalog_example.json."):
                        style "mas_os_hint"

                    use mas_os_ibutton(_("Установщик MAS OS"), Return("setup"), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="boot")

                    use mas_os_ibutton(_("Сбросить настройки MAS OS"), Show("mas_os_confirm", message=_("Сбросить оформление, звук и поведение оболочки к заводским?\nСкачанные файлы и прочитанные события не трогаем."), yes_action=[Function(store.mas_os.reset_os_settings), Hide("mas_os_confirm")], no_action=Hide("mas_os_confirm")), "R", "#8A3A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="reboot")

                    use mas_os_ibutton(_("Проверить обновления порта"), Show("mas_os_notice", message=_("Проверка обновлений порта появится позже.\nСюда можно будет вставить уже готовую реализацию.")), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="updates")

                    text _("Оболочка не считает посещение комнаты, пока не нажато «Запустить MAS»."):
                        style "mas_os_hint"

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        at mas_os_btn
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_about():
    modal True
    zorder 200

    $ plat = store.mas_os.platform_name()
    $ touch = _("да") if store.mas_os.is_touch() else _("нет")
    $ rver = renpy.version()
    $ osver = store.mas_os.VERSION
    $ links = store.mas_os.ABOUT_LINKS

    use mas_os_bg

    text _("О системе") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text _("MAS OS [osver]  ·  [config.name] [config.version]  ·  [rver]") at store.mas_os.t_pop(0.04):
        style "mas_os_hint"
        xpos 48
        ypos 58

    hbox at store.mas_os.t_pop(0.08):
        xpos 48
        ypos 96
        spacing 12

        for i in range(len(links)):
            use mas_os_link_card(links[i], delay=0.06 + 0.04 * i)

    frame at store.mas_os.t_pop(0.16):
        style "mas_os_panel"
        xpos 48
        ypos 330
        xysize (1184, 280)
        padding (20, 14)

        hbox:
            spacing 24

            vbox:
                xsize 360
                spacing 8

                text _("Сборка"):
                    style "mas_os_subtitle"

                text _("Платформа: [plat]"):
                    style "mas_os_body"

                text _("Сенсорный ввод: [touch]"):
                    style "mas_os_body"

                text _("Картинки на кнопках — заглушки из игры. Позже заменишь своими."):
                    style "mas_os_hint"

                textbutton _("Открыть логи"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 200
                    action Return("logs")

            viewport:
                xysize (760, 248)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 8
                    xsize 730

                    text _("План порта"):
                        style "mas_os_subtitle"

                    text store.mas_os.ROADMAP:
                        style "mas_os_hint"
                        xsize 720
                        substitute False

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        at mas_os_btn
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


style mas_os_link_card is default:
    xsize 220
    ysize 152
    padding (0, 0)
    idle_background Solid("#1E0C14")
    hover_background Solid("#3A1524")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_link_card_title is default:
    font gui.default_font
    size 15
    color "#FFF0F7"
    outlines []

style mas_os_link_card_hint is default:
    font gui.default_font
    size 12
    color "#FFD7EC"
    outlines []
