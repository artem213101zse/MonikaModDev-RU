# MAS OS — Settings (category sidebar) and About (link cards).

init python:
    class MASOSTintBarValue(BarValue):
        def __init__(self, channel):
            self.channel = channel

        def get_adjustment(self):
            if self.channel == 3:
                return ui.adjustment(
                    value=store.mas_os.tb_strength(),
                    range=100,
                    changed=store.mas_os.set_tb_strength,
                    step=1,
                )
            rgb = store.mas_os.tb_rgb()
            ch = self.channel

            def _changed(value, channel=ch):
                store.mas_os.set_tb_rgb_channel(channel, value)

            return ui.adjustment(
                value=rgb[ch] if ch in (0, 1, 2) else 0,
                range=255,
                changed=_changed,
                step=1,
            )


screen mas_os_rgb_bar(caption, channel, shown, rng):
    vbox:
        spacing 4
        xfill True

        hbox:
            xfill True

            text caption:
                style "mas_os_hint"

            text "{0}".format(shown):
                style "mas_os_hint"
                xalign 1.0

        bar:
            value MASOSTintBarValue(channel)
            xsize 760
            ysize 20
            style "mas_os_bar"


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
            "logo": "mod_assets/mas_os/about/github.png",
            "icon": "github-port",
            "hue": "#C94A7A",
        },
        {
            "title": "Monika After Story",
            "hint": "официальный мод",
            "url": "https://github.com/Monika-After-Story/MonikaModDev",
            "logo": "mod_assets/mas_os/about/mas.png",
            "icon": "mas-official",
            "hue": "#FF8AC4",
        },
        {
            "title": "Ren'Py",
            "hint": "движок игры",
            "url": "https://www.renpy.org/",
            "logo": "mod_assets/mas_os/about/renpy.png",
            "icon": "renpy",
            "hue": "#4A8AAA",
        },
        {
            "title": "DDLC",
            "hint": "оригинал Team Salvato",
            "url": "https://ddlc.moe",
            "logo": "mod_assets/mas_os/about/ddlc.png",
            "icon": "ddlc",
            "hue": "#8A4A7A",
        },
        {
            "title": "Team Salvato",
            "hint": "авторы DDLC",
            "url": "https://teamsalvato.com",
            "logo": "mod_assets/mas_os/about/salvato.png",
            "icon": "team-salvato",
            "hue": "#8A6A4A",
        },
    ]

    def about_image(path):
        if not path:
            return None
        try:
            opened = asset_open_path(path)
            if opened:
                return opened
        except Exception:
            pass
        try:
            if store.renpy.loadable(path):
                return path
        except Exception:
            pass
        return None

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
    $ logo = store.mas_os.about_image(item.get("logo"))
    $ ic = store.mas_os.icon_path(item.get("icon"))
    $ shown = logo or ic

    button:
        style "mas_os_link_card"
        at store.mas_os.t_tile(delay)
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()
        action Function(store.mas_os.open_site, item["url"])

        vbox:
            spacing 0

            frame:
                xysize (224, 108)
                background Solid(store.mas_os.theme_color("panel2"))
                clipping True

                if shown:
                    add store.mas_os.fit_image(shown, 200, 96):
                        xalign 0.5
                        yalign 0.5
                else:
                    text _("нет картинки"):
                        style "mas_os_hint"
                        xalign 0.5
                        yalign 0.5

            frame:
                xsize 224
                ysize 52
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


screen mas_os_about_bullet(caption, hue="#FF8AC4"):
    hbox:
        spacing 8
        xfill True

        frame:
            xysize (8, 8)
            yoffset 6
            background Solid(hue)

        text caption:
            style "mas_os_hint"
            size 14
            xsize 680
            substitute False


screen mas_os_settings():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ cat = store.mas_os.settings_cat or "boot"

    use mas_os_bg

    text _("Настройки"):
        style "mas_os_title"
        xpos 48
        ypos 16

    text _("Слева разделы, справа параметры. То, что уже работает в оболочке."):
        style "mas_os_hint"
        xpos 48
        ypos 58

    viewport:
        id "mas_os_settings_cats"
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

    frame:
        style "mas_os_panel"
        xpos 410
        ypos 100
        xysize (822, 510)
        padding (20, 16)

        viewport:
            id "mas_os_settings_body"
            yadjustment store.mas_os.settings_scroll()
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

                    text _("Заставка MAS OS"):
                        style "mas_os_subtitle"

                    text _("Ролик при входе в оболочку. «Тест» показывает его и возвращает сюда. На заглушках уже крутится — свои PNG просто перезапиши."):
                        style "mas_os_hint"

                    use mas_os_boot_splash_picker(width=760)

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

                    text _("Тема оболочки, вид (плитки или рабочий стол), анимации, обои, текстбокс и шрифты."):
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
                        use mas_os_layout_toggle(width=720)

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

                    text _("Готовые картинки или свой цвет ниже — без Photoshop. Меняется у Моники и в оболочке."):
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

                    text _("Свой цвет поверх текстбокса"):
                        style "mas_os_subtitle"

                    text _("Ren'Py красит стандартную картинку по контуру (прозрачность PNG). Photoshop больше не нужен. Кнопки в игре могут взять тот же цвет."):
                        style "mas_os_hint"

                    use mas_os_onoff(
                        _("Включить свой цвет"),
                        _("Наложить выбранный цвет на обычный текстбокс."),
                        "_mas_os_tb_tint_on",
                    )

                    use mas_os_onoff(
                        _("Кнопки и UI в цвет текстбокса"),
                        _("Общение / Экстра / меню выбора / имя в текстбоксе."),
                        "_mas_os_ui_match",
                    )

                    $ tb_hex = store.mas_os.tb_hex()
                    $ tb_str = store.mas_os.tb_strength()
                    $ tb_rgb = store.mas_os.tb_rgb()
                    $ tb_prev = store.mas_os.textbox_preview()

                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 760
                        ysize 92
                        padding (8, 8)
                        clipping True

                        add Transform(tb_prev, zoom=0.55):
                            xalign 0.5
                            yalign 1.0

                    text _("Палитра"):
                        style "mas_os_hint"

                    grid 6 2:
                        spacing 8
                        xsize 760

                        for hexc, title in store.mas_os.TINT_PRESETS:
                            button:
                                style "mas_os_nav_btn"
                                xysize (118, 44)
                                selected (hexc == tb_hex and store.mas_os.tb_tint_on())
                                hover_sound store.mas_os.os_hover()
                                activate_sound store.mas_os.os_activate()
                                action Function(store.mas_os.set_tb_tint, hexc)

                                hbox:
                                    spacing 6
                                    xalign 0.5
                                    yalign 0.5

                                    frame:
                                        xysize (16, 16)
                                        background Solid(hexc)
                                        yalign 0.5

                                    text title:
                                        style "mas_os_nav_btn_text"
                                        size 13
                                        yalign 0.5
                                        substitute False

                    use mas_os_rgb_bar(_("R"), 0, tb_rgb[0], 255)
                    use mas_os_rgb_bar(_("G"), 1, tb_rgb[1], 255)
                    use mas_os_rgb_bar(_("B"), 2, tb_rgb[2], 255)
                    use mas_os_rgb_bar(_("Сила"), 3, tb_str, 100)

                    text _("Текущий цвет {0}  ·  сила {1}%").format(tb_hex, tb_str):
                        style "mas_os_hint"
                        substitute False

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
                        _("Радужная кнопка слева сверху на экране разговора."),
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

                    use mas_os_ibutton(_("Открыть плеер"), MASOSGo("player"), "Au", "#8A6A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="sound")

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

                    use mas_os_android_saves_row

                    use mas_os_ibutton(_("Установщик MAS OS"), MASOSGo("setup"), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="boot")

                    use mas_os_ibutton(_("Сбросить настройки MAS OS"), Show("mas_os_confirm", message=_("Сбросить оформление, звук и поведение оболочки к заводским?\nСкачанные файлы и прочитанные события не трогаем."), yes_action=[Function(store.mas_os.reset_os_settings), Hide("mas_os_confirm")], no_action=Hide("mas_os_confirm")), "R", "#8A3A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="reboot")

                    use mas_os_ibutton(_("Проверить обновления порта"), Show("mas_os_notice", message=_("Проверка обновлений порта появится позже.\nСюда можно будет вставить уже готовую реализацию.")), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False, icon="updates")

                    text _("Оболочка не считает посещение комнаты, пока не нажато «Запустить MAS»."):
                        style "mas_os_hint"

    use mas_os_app_nav


screen mas_os_about():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ plat = store.mas_os.platform_name()
    $ touch = _("да") if store.mas_os.is_touch() else _("нет")
    $ rver = renpy.version()
    $ osver = store.mas_os.VERSION
    $ links = store.mas_os.ABOUT_LINKS
    $ layout_name = _("Рабочий стол") if store.mas_os.layout_desktop() else _("Плитки")
    $ theme_name = _("светлая") if store.mas_os.theme_light() else _("тёмная")

    use mas_os_bg

    frame at store.mas_os.t_pop(0.0):
        style "mas_os_panel"
        xpos 48
        ypos 12
        xysize (1184, 96)
        padding (16, 10)

        hbox:
            spacing 16
            yalign 0.5
            xfill True

            fixed at mas_os_logo_breathe:
                xysize (72, 72)
                use mas_os_logo_mark(max_w=72, max_h=72)

            vbox:
                spacing 2
                yalign 0.5

                text _("О системе"):
                    style "mas_os_title"
                    size 30

                text _("MAS OS [osver]  ·  оболочка порта"):
                    style "mas_os_subtitle"
                    size 16

                use mas_os_powered_line(size=13)

            null:
                xfill True

            vbox:
                spacing 2
                yalign 0.5
                xsize 420

                text _("[config.name]  [config.version]"):
                    style "mas_os_body"
                    size 16
                    xalign 1.0

                text _("[rver]"):
                    style "mas_os_hint"
                    size 13
                    xalign 1.0

                text _("Платформа [plat]  ·  сенсор [touch]"):
                    style "mas_os_hint"
                    size 13
                    xalign 1.0

    hbox at store.mas_os.t_pop(0.06):
        xpos 48
        ypos 118
        spacing 10

        for i in range(len(links)):
            use mas_os_link_card(links[i], delay=0.04 + 0.03 * i)

    hbox at store.mas_os.t_pop(0.12):
        xpos 48
        ypos 286
        spacing 12

        frame:
            style "mas_os_panel"
            xysize (360, 340)
            padding (16, 12)

            vbox:
                spacing 8
                xfill True

                text store.mas_os.STUDIO:
                    style "mas_os_studio_title"
                    substitute False

                text store.mas_os.STUDIO_LONG:
                    style "mas_os_hint"
                    size 13
                    substitute False

                text store.mas_os.ABOUT_BLURB:
                    style "mas_os_hint"
                    size 14
                    xsize 320
                    substitute False

                text _("Сейчас: [layout_name], тема [theme_name]"):
                    style "mas_os_body"
                    size 15

                text store.mas_os.ABOUT_NOTE:
                    style "mas_os_hint"
                    size 13
                    xsize 320
                    substitute False

                textbutton _("Открыть логи"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 200
                    action MASOSGo("logs")

                textbutton _("Тест дисклеймера"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 200
                    action [Function(store.mas_os.tos_begin, True), Show("mas_os_tos")]

        frame:
            style "mas_os_panel"
            xysize (812, 340)
            padding (16, 12)

            viewport:
                id "mas_os_about_plan"
                xysize (776, 312)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 10
                    xsize 750

                    text _("Уже сделано"):
                        style "mas_os_subtitle"

                    for line in store.mas_os.ABOUT_DONE:
                        use mas_os_about_bullet(line, "#FF8AC4")

                    text _("Дальше"):
                        style "mas_os_subtitle"

                    for line in store.mas_os.ABOUT_NEXT:
                        use mas_os_about_bullet(line, "#3DFFF0")

    use mas_os_app_nav


style mas_os_link_card is default:
    xsize 224
    ysize 160
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
