# -*- coding: utf-8 -*-
# --- FILE MAP ---
# mas_os_about_win.rpy — новый вид «О системе»
# Классика осталась в mas_os_settings.rpy (mas_os_about_classic).
# ---

screen mas_os_about_win():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ plat = store.mas_os.platform_name()
    $ rver = renpy.version()
    $ osver = store.mas_os.VERSION
    $ layout_name = _("Рабочий стол") if store.mas_os.layout_desktop() else _("Плитки")
    $ theme_name = _("светлая") if store.mas_os.theme_light() else _("тёмная")
    $ ch = store.mas_os.upd_channel_label()
    $ port = store.mas_os.upd_local_version()
    $ masv = store.mas_os.upd_mas_version()
    $ links = store.mas_os.ABOUT_LINKS

    use mas_os_bg

    text _("О системе"):
        style "mas_os_title"
        xpos 48
        ypos 16

    textbutton _("Классический вид"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 980
        ypos 16
        xsize 252
        action Function(store.mas_os.set_about_ui, "classic")

    frame:
        xpos 48
        ypos 70
        xysize (1184, 110)
        background Solid(store.mas_os.theme_color("panel"))
        padding (18, 12)

        hbox:
            spacing 18
            yalign 0.5

            fixed:
                xysize (80, 80)
                use mas_os_logo_mark(max_w=80, max_h=80)

            vbox:
                spacing 4
                yalign 0.5

                text store.mas_os.STUDIO:
                    style "mas_os_studio_title"
                    size 22
                    substitute False

                text _("MAS OS [osver]  ·  оболочка до комнаты Моники"):
                    style "mas_os_subtitle"
                    size 16

                use mas_os_powered_line(size=13)

            null:
                xfill True

            vbox:
                spacing 4
                yalign 0.5
                xsize 420

                text _("Порт [port]  ·  MAS [masv]"):
                    style "mas_os_body"
                    size 16
                    xalign 1.0

                text _("[rver]"):
                    style "mas_os_hint"
                    size 13
                    xalign 1.0

                text _("[plat]  ·  [layout_name]  ·  тема [theme_name]"):
                    style "mas_os_hint"
                    size 13
                    xalign 1.0

    hbox:
        xpos 48
        ypos 196
        spacing 16

        frame:
            xysize (420, 430)
            background Solid(store.mas_os.theme_color("panel"))
            padding (18, 16)

            vbox:
                spacing 10
                xfill True

                text _("Эта оболочка"):
                    style "mas_os_subtitle"

                text store.mas_os.ABOUT_BLURB:
                    style "mas_os_hint"
                    size 14
                    xsize 380
                    substitute False

                text _("Канал обновлений: [ch]"):
                    style "mas_os_body"
                    size 15

                textbutton _("Проверить обновления"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 360
                    action [
                        Function(store.mas_os.set_settings_page, "update"),
                        MASOSGo("settings"),
                    ]

                textbutton _("Документация"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 360
                    action MASOSGo("docs")

                textbutton _("Логи"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 360
                    action MASOSGo("logs")

                textbutton _("Показать дисклеймер"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 360
                    action [Function(store.mas_os.tos_begin, True), Show("mas_os_tos")]

        frame:
            xysize (748, 430)
            background Solid(store.mas_os.theme_color("panel"))
            padding (18, 16)

            vbox:
                spacing 8
                xfill True

                text _("Ссылки"):
                    style "mas_os_subtitle"

                viewport:
                    xysize (712, 370)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 8
                        xsize 690

                        for item in links:
                            button:
                                xsize 690
                                ysize 64
                                background Solid(store.mas_os.theme_color("btn"))
                                hover_background Solid(store.mas_os.theme_color("btn_hover"))
                                padding (12, 8)
                                hover_sound store.mas_os.os_hover()
                                activate_sound store.mas_os.os_activate()
                                action Function(store.mas_os.open_site, item["url"])

                                hbox:
                                    spacing 12
                                    yalign 0.5

                                    if store.mas_os.icon_path(item.get("icon")):
                                        add store.mas_os.fit_image(store.mas_os.icon_path(item.get("icon")), 36, 36):
                                            yalign 0.5
                                    else:
                                        frame:
                                            xysize (36, 36)
                                            background Solid(item.get("hue") or "#C94A7A")
                                            yalign 0.5

                                    vbox:
                                        spacing 2
                                        yalign 0.5

                                        text item["title"]:
                                            style "mas_os_body"
                                            size 17
                                            substitute False

                                        text item.get("hint") or "":
                                            style "mas_os_hint"
                                            size 13
                                            substitute False

    use mas_os_app_nav
