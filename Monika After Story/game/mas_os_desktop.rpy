# MAS OS desktop layout — extras/Windows look (DDLC Plus style).
# cards layout stays the default; this is selected in Settings → Оформление.

init -5 python in mas_os:
    import store
    import datetime

    LAYOUTS = (
        ("cards", "Плитки", "Текущий вид: крупные кнопки и карточки слева, сетка справа."),
        ("desktop", "Рабочий стол", "Как extras в DDLC Plus: значки на обоях, панель задач, окна."),
    )

    start_open = False
    TASKBAR_Y = 676
    TASKBAR_H = 44
    WIN_X0 = 24
    WIN_Y0 = 16
    WIN_W = 1232
    WIN_H = 652
    WIN_TITLE = 34

    WM_APPS = (
        ("events", "События", "events"),
        ("docs", "Документация", "docs"),
        ("gifts", "Подарки", "gifts"),
        ("files", "Файлы", "files"),
        ("browser", "Браузер", "browser"),
        ("data", "Данные", "data"),
        ("settings", "Настройки", "settings"),
        ("submods", "Сабмоды", "submods"),
        ("store", "Склад", "updates"),
        ("player", "Плеер", "sound"),
        ("about", "О системе", "about"),
        ("logs", "Логи", "logs"),
        ("setup", "Установщик", "boot"),
    )

    wm_apps = []
    wm_minimized = []
    wm_geom = {}
    wm_focus = None
    _wm_embed_depth = 0
    fm_sub = None

    def layout_id():
        lid = getattr(store.persistent, "_mas_os_layout", "cards") or "cards"
        for row in LAYOUTS:
            if row[0] == lid:
                return lid
        return "cards"

    def layout_desktop():
        return layout_id() == "desktop"

    def set_layout(lid):
        global start_open
        ids = [row[0] for row in LAYOUTS]
        if lid not in ids:
            lid = "cards"
        store.persistent._mas_os_layout = lid
        start_open = False
        wm_close_all()
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        return None

    def set_start_open(value):
        global start_open
        start_open = bool(value)
        return None

    def toggle_start():
        global start_open
        start_open = not start_open
        return None

    def desk_clock():
        try:
            return datetime.datetime.now().strftime("%H:%M")
        except Exception:
            return ""

    def desk_date():
        try:
            return datetime.datetime.now().strftime("%d.%m.%Y")
        except Exception:
            return ""

    def desk_icons():
        ev_label = events_button_label()
        ev_badge = unread_event_count() > 0
        return (
            (ev_label, "events", "events", "#C94A7A", ev_badge),
            ("Документация", "docs", "docs", "#7A4A9A", False),
            ("Подарки", "gifts", "gifts", "#E85A9A", False),
            ("Файлы", "files", "files", "#5A6A9A", False),
            ("Браузер", "browser", "browser", "#4A8AAA", False),
            ("Данные", "data", "data", "#8A6A4A", False),
            ("Настройки", "settings", "settings", "#6A6A7A", False),
            ("Сабмоды", "submods", "submods", "#4A8A6A", False),
            ("Склад", "store", "store", "#4A8AAA", False),
            ("Плеер", "player", "player", "#8A6A4A", False),
            ("О системе", "about", "about", "#7A4A9A", False),
            ("Логи", "logs", "logs", "#8A6A4A", False),
        )

    def launch_action():
        if launch_anim_on():
            return store.Show("mas_os_launch_anim")
        return store.Return("launch")

    def wm_meta(app_id):
        for aid, title, icon in WM_APPS:
            if aid == app_id:
                return (aid, title, icon)
        return (app_id, app_id, "about")

    def wm_is_open(app_id):
        return app_id in wm_apps

    def wm_is_min(app_id):
        return app_id in wm_minimized

    def wm_is_focus(app_id):
        return wm_focus == app_id and app_id not in wm_minimized

    def wm_visible():
        out = []
        for aid in wm_apps:
            if aid not in wm_minimized:
                out.append(aid)
        return out

    def wm_embedded():
        return _wm_embed_depth > 0

    def wm_begin_embed():
        global _wm_embed_depth
        _wm_embed_depth += 1
        return None

    def wm_end_embed():
        global _wm_embed_depth
        if _wm_embed_depth > 0:
            _wm_embed_depth -= 1
        return None

    def wm_pos(app_id):
        pos = wm_geom.get(app_id)
        if pos:
            return pos
        n = 0
        if app_id in wm_apps:
            n = wm_apps.index(app_id)
        return (WIN_X0 + 20 * (n % 4), WIN_Y0 + 16 * (n % 4))

    def wm_open(app_id, reset_fm=True):
        global start_open, wm_focus, fm_sub
        start_open = False
        if app_id == "files":
            try:
                if reset_fm or not fm_cwd:
                    fm_open()
            except Exception:
                pass
            if app_id not in wm_apps:
                fm_sub = None
        if app_id not in wm_apps:
            n = len(wm_apps)
            wm_apps.append(app_id)
            wm_geom[app_id] = (
                WIN_X0 + 20 * (n % 4),
                WIN_Y0 + 16 * (n % 4),
            )
        if app_id in wm_minimized:
            wm_minimized.remove(app_id)
        if app_id in wm_apps:
            wm_apps.remove(app_id)
            wm_apps.append(app_id)
        wm_focus = app_id
        return None

    def wm_close(app_id):
        global wm_focus, fm_sub
        if app_id in wm_apps:
            wm_apps.remove(app_id)
        if app_id in wm_minimized:
            wm_minimized.remove(app_id)
        if app_id in wm_geom:
            wm_geom.pop(app_id, None)
        if app_id == "files":
            fm_sub = None
        if wm_focus == app_id:
            wm_focus = None
            vis = wm_visible()
            if vis:
                wm_focus = vis[-1]
        return None

    def wm_close_focused():
        if wm_focus:
            return wm_close(wm_focus)
        return None

    def wm_close_or_nested():
        global fm_sub
        if wm_focus == "files" and fm_sub:
            if fm_sub == "edit":
                fm_sub = "view"
            else:
                fm_sub = None
            return None
        return wm_close_focused()

    def wm_minimize(app_id):
        global wm_focus
        if app_id not in wm_apps:
            return None
        if app_id not in wm_minimized:
            wm_minimized.append(app_id)
        if wm_focus == app_id:
            wm_focus = None
            vis = wm_visible()
            if vis:
                wm_focus = vis[-1]
        return None

    def wm_focus_app(app_id):
        global wm_focus, start_open
        start_open = False
        if app_id not in wm_apps:
            return wm_open(app_id)
        if app_id in wm_minimized:
            wm_minimized.remove(app_id)
        if app_id in wm_apps:
            wm_apps.remove(app_id)
            wm_apps.append(app_id)
        wm_focus = app_id
        return None

    def wm_taskbar_click(app_id):
        if app_id not in wm_apps:
            return wm_open(app_id)
        if app_id in wm_minimized:
            return wm_focus_app(app_id)
        if wm_focus == app_id:
            return wm_minimize(app_id)
        return wm_focus_app(app_id)

    def wm_close_all():
        global wm_focus, fm_sub
        wm_apps[:] = []
        wm_minimized[:] = []
        wm_geom.clear()
        wm_focus = None
        fm_sub = None
        return None

    def wm_esc():
        global start_open
        if start_open:
            start_open = False
            return None
        if wm_focus and wm_focus not in wm_minimized:
            return wm_close_or_nested()
        return None

    def fm_embed_go(page):
        global fm_sub
        if page == "edit":
            try:
                if fm_begin_edit():
                    fm_sub = "edit"
            except Exception:
                pass
            return None
        fm_sub = page
        return None


init python:
    import datetime

    class MASOSClockText(renpy.Displayable):
        def __init__(self, size=15, color="#FFE6F3", **kwargs):
            super(MASOSClockText, self).__init__(**kwargs)
            self.size = int(size)
            self.color = color

        def render(self, width, height, st, at):
            try:
                now = datetime.datetime.now()
                line = now.strftime("%H:%M") + "\n" + now.strftime("%d.%m.%Y")
            except Exception:
                line = ""
            child = Text(
                line,
                size=self.size,
                color=self.color,
                outlines=[],
                text_align=1.0,
                font=store.gui.default_font,
            )
            cr = child.render(width, height, st, at)
            rv = renpy.Render(int(cr.width), int(cr.height))
            rv.blit(cr, (0, 0))
            renpy.redraw(self, 1.0)
            return rv


init python:
    class MASOSGo(Action):
        """Open an OS app: jump via Return on tiles, window on desktop."""
        def __init__(self, app_id):
            self.app_id = app_id

        def __call__(self):
            if store.mas_os.layout_desktop():
                store.mas_os.wm_open(self.app_id)
                store.renpy.restart_interaction()
                return None
            return self.app_id

    class MASOSBack(Action):
        def __init__(self, dest="back"):
            self.dest = dest

        def __call__(self):
            if store.mas_os.wm_embedded():
                store.mas_os.wm_close_or_nested()
                store.renpy.restart_interaction()
                return None
            return self.dest


screen mas_os_app_nav(dest="back"):
    if not store.mas_os.wm_embedded():
        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 48
            ypos 640
            at mas_os_btn
            action MASOSBack(dest)

        key "K_ESCAPE" action MASOSBack(dest)
        key "K_AC_BACK" action MASOSBack(dest)


screen mas_os_layout_toggle(width=388):
    $ lid = store.mas_os.layout_id()
    $ half = int((width - 12) / 2)

    vbox:
        spacing 6
        xfill True

        text _("Вид оболочки"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("Плитки"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (lid == "cards")
                    at mas_os_btn
                    action Function(store.mas_os.set_layout, "cards")

                textbutton _("Рабочий стол"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (lid == "desktop")
                    at mas_os_btn
                    action Function(store.mas_os.set_layout, "desktop")

        text _("Плитки — как сейчас. Рабочий стол — значки и панель задач, как extras в DDLC Plus."):
            style "mas_os_hint"
            size 13


screen mas_os_desk_icon(caption, act, icon, hue, badge=False, delay=0, xpos=0, ypos=0):
    $ ipath = store.mas_os.icon_path(icon)

    button:
        style "mas_os_desk_icon"
        xpos xpos
        ypos ypos
        at store.mas_os.t_tile(delay)
        action act
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()

        vbox:
            spacing 4
            xalign 0.5
            yalign 0.5
            xsize 100

            if ipath:
                add store.mas_os.fit_image(ipath, 48, 48):
                    xalign 0.5
            else:
                frame:
                    xysize (48, 48)
                    background Solid(hue)
                    xalign 0.5

                    text "•":
                        style "mas_os_glyph"
                        xalign 0.5
                        yalign 0.5

            text caption:
                style "mas_os_desk_icon_text"
                xalign 0.5
                substitute False

        if badge:
            frame:
                xysize (12, 12)
                background Solid("#FF3B5C")
                xalign 1.0
                yalign 0.0
                xoffset -10
                yoffset 4


screen mas_os_wm_body(app_id):
    if app_id == "settings":
        use mas_os_settings
    elif app_id == "about":
        use mas_os_about
    elif app_id == "events":
        use mas_os_events
    elif app_id == "docs":
        use mas_os_docs
    elif app_id == "gifts":
        use mas_os_gifts
    elif app_id == "files":
        if store.mas_os.fm_sub == "edit":
            use mas_os_fm_edit
        elif store.mas_os.fm_sub == "view":
            use mas_os_fm_view
        else:
            use mas_os_files
    elif app_id == "browser":
        use mas_os_browser
    elif app_id == "data":
        use mas_os_data
    elif app_id == "submods":
        use mas_os_submods
    elif app_id == "store":
        use mas_os_store
    elif app_id == "player":
        use mas_os_player
    elif app_id == "logs":
        use mas_os_logs
    elif app_id == "setup":
        use mas_os_setup


screen mas_os_app_window(app_id):
    $ meta = store.mas_os.wm_meta(app_id)
    $ _title = meta[1]
    $ _icon = store.mas_os.icon_path(meta[2])
    $ _pos = store.mas_os.wm_pos(app_id)
    $ _focus = store.mas_os.wm_is_focus(app_id)
    $ _ww = store.mas_os.WIN_W
    $ _wh = store.mas_os.WIN_H
    $ _th = store.mas_os.WIN_TITLE
    $ _bar = store.mas_os.theme_color("accent") if _focus else store.mas_os.theme_color("btn")

    frame:
        style "mas_os_app_win"
        xpos _pos[0]
        ypos _pos[1]
        xysize (_ww, _wh)
        padding (0, 0)

        fixed:
            xysize (_ww, _wh)

            frame:
                background Solid(_bar)
                xpos 0
                ypos 0
                xsize _ww
                ysize _th
                padding (8, 0)

                hbox:
                    spacing 8
                    yalign 0.5
                    xfill True

                    if _icon:
                        add store.mas_os.fit_image(_icon, 18, 18):
                            yalign 0.5

                    text _title:
                        style "mas_os_desk_titlebar_text"
                        size 16
                        yalign 0.5
                        substitute False

                    null:
                        xfill True

                    button:
                        style "mas_os_win_tool"
                        action Function(store.mas_os.wm_minimize, app_id)
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()

                        text "-":
                            style "mas_os_win_tool_text"
                            xalign 0.5
                            yalign 0.5

                    button:
                        style "mas_os_win_tool"
                        action Function(store.mas_os.wm_close, app_id)
                        hover_sound store.mas_os.os_hover()
                        activate_sound store.mas_os.os_activate()

                        text "x":
                            style "mas_os_win_tool_text"
                            xalign 0.5
                            yalign 0.5

            fixed:
                xpos 0
                ypos _th
                xsize _ww
                ysize (_wh - _th)
                clipping True

                $ store.mas_os.wm_begin_embed()
                use mas_os_wm_body(app_id)
                $ store.mas_os.wm_end_embed()

            if not _focus:
                button:
                    xpos 0
                    ypos _th
                    xysize (_ww, _wh - _th)
                    background Solid("#00000028")
                    action Function(store.mas_os.wm_focus_app, app_id)


screen mas_os_desk_window(title, xpos, ypos, xsize, ysize):
    frame:
        style "mas_os_desk_win"
        xpos xpos
        ypos ypos
        xsize xsize
        ysize ysize
        padding (0, 0)

        vbox:
            xfill True
            yfill True

            frame:
                style "mas_os_desk_titlebar"
                background Solid(store.mas_os.theme_color("accent"))
                xfill True
                ysize 32
                padding (10, 4)

                text title:
                    style "mas_os_desk_titlebar_text"
                    yalign 0.5
                    substitute False

            frame:
                background Solid(store.mas_os.theme_color("panel"))
                xfill True
                yfill True
                padding (14, 10)

                transclude


screen mas_os_taskbar():
    $ _launch_ic = store.mas_os.icon_path("launch")
    $ _clock_col = store.mas_os.theme_color("title")

    add Solid(store.mas_os.theme_color("accent")):
        xpos 0
        ypos (store.mas_os.TASKBAR_Y - 2)
        xsize 1280
        ysize 2

    frame:
        style "mas_os_taskbar"
        xpos 0
        ypos store.mas_os.TASKBAR_Y
        xsize 1280
        ysize store.mas_os.TASKBAR_H
        padding (6, 4)

        hbox:
            spacing 6
            yalign 0.5
            xfill True

            button:
                style "mas_os_tb_btn"
                xsize 44
                selected store.mas_os.start_open
                action Function(store.mas_os.toggle_start)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()

                if store.mas_os.logo_path("logo"):
                    add store.mas_os.fit_image(store.mas_os.logo_path("logo"), 28, 28):
                        xalign 0.5
                        yalign 0.5
                else:
                    text "K":
                        style "mas_os_desk_titlebar_text"
                        size 18
                        xalign 0.5
                        yalign 0.5

            button:
                style "mas_os_tb_btn"
                xsize 188
                action store.mas_os.launch_action()
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()

                hbox:
                    spacing 8
                    xalign 0.5
                    yalign 0.5

                    if _launch_ic:
                        add store.mas_os.fit_image(_launch_ic, 22, 22):
                            yalign 0.5

                    text _("Запустить MAS"):
                        style "mas_os_tb_btn_text"
                        yalign 0.5

            null:
                xsize 8

            for _tid in store.mas_os.wm_apps:
                $ _tm = store.mas_os.wm_meta(_tid)
                $ _tic = store.mas_os.icon_path(_tm[2])
                button:
                    style "mas_os_tb_btn"
                    xsize 128
                    selected store.mas_os.wm_is_focus(_tid)
                    action Function(store.mas_os.wm_taskbar_click, _tid)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    hbox:
                        spacing 6
                        yalign 0.5
                        xoffset 6

                        if _tic:
                            add store.mas_os.fit_image(_tic, 18, 18):
                                yalign 0.5

                        text _tm[1]:
                            style "mas_os_tb_btn_text"
                            size 13
                            yalign 0.5
                            substitute False

            null:
                xfill True

            fixed:
                xysize (92, 36)
                yalign 0.5

                add MASOSClockText(size=13, color=_clock_col):
                    xalign 1.0
                    yalign 0.5

            button:
                style "mas_os_tb_btn"
                xsize 40
                action Function(store.mas_os.reboot_shell)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()

                if store.mas_os.icon_path("reboot"):
                    add store.mas_os.fit_image(store.mas_os.icon_path("reboot"), 20, 20):
                        xalign 0.5
                        yalign 0.5

            if store.mas_os.flag("_mas_os_quit_confirm", True):
                button:
                    style "mas_os_tb_btn"
                    xsize 40
                    action Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm"))
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    if store.mas_os.icon_path("shutdown"):
                        add store.mas_os.fit_image(store.mas_os.icon_path("shutdown"), 20, 20):
                            xalign 0.5
                            yalign 0.5
            else:
                button:
                    style "mas_os_tb_btn"
                    xsize 40
                    action Function(store.mas_os.request_quit)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    if store.mas_os.icon_path("shutdown"):
                        add store.mas_os.fit_image(store.mas_os.icon_path("shutdown"), 20, 20):
                            xalign 0.5
                            yalign 0.5


screen mas_os_start_flyout():
    $ _launch_ic = store.mas_os.icon_path("launch")

    button:
        xpos 0
        ypos 0
        xysize (1280, 720)
        background None
        action Function(store.mas_os.set_start_open, False)

    frame:
        style "mas_os_start_menu"
        xpos 6
        ypos 268
        xsize 300
        ysize 400
        padding (0, 0)

        vbox:
            xfill True
            spacing 0

            frame:
                background Solid(store.mas_os.theme_color("accent"))
                xfill True
                padding (14, 12)

                hbox:
                    spacing 12

                    if store.mas_os.logo_path("logo"):
                        add store.mas_os.fit_image(store.mas_os.logo_path("logo"), 40, 40):
                            yalign 0.5

                    vbox:
                        spacing 2
                        yalign 0.5

                        text _("MAS OS"):
                            style "mas_os_desk_titlebar_text"
                            size 18

                        text store.mas_os.POWERED_BY:
                            style "mas_os_powered_text"
                            size 12
                            color "#FFF6FB"
                            substitute False

            button:
                style "mas_os_start_item"
                action [Function(store.mas_os.set_start_open, False), store.mas_os.launch_action()]
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()

                hbox:
                    spacing 10
                    yalign 0.5
                    xoffset 12

                    if _launch_ic:
                        add store.mas_os.fit_image(_launch_ic, 24, 24):
                            yalign 0.5

                    text _("Запустить MAS"):
                        style "mas_os_start_item_text"
                        yalign 0.5

            use mas_os_start_row(_("Настройки"), MASOSGo("settings"), "settings")
            use mas_os_start_row(_("О системе"), MASOSGo("about"), "about")
            use mas_os_start_row(_("Логи"), MASOSGo("logs"), "logs")
            use mas_os_start_row(_("Перезагрузка"), Function(store.mas_os.reboot_shell), "reboot")

            if store.mas_os.flag("_mas_os_quit_confirm", True):
                use mas_os_start_row(_("Выключение"), Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm")), "shutdown")
            else:
                use mas_os_start_row(_("Выключение"), Function(store.mas_os.request_quit), "shutdown")


screen mas_os_start_row(caption, act, icon):
    $ ipath = store.mas_os.icon_path(icon)

    button:
        style "mas_os_start_item"
        action [Function(store.mas_os.set_start_open, False), act]
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()

        hbox:
            spacing 10
            yalign 0.5
            xoffset 12

            if ipath:
                add store.mas_os.fit_image(ipath, 24, 24):
                    yalign 0.5

            text caption:
                style "mas_os_start_item_text"
                yalign 0.5
                substitute False


screen mas_os_home_desktop():
    $ snap = store.mas_os.aff_snapshot()
    $ ev_line = store.mas_os.next_event_line()
    $ icons = store.mas_os.desk_icons()
    $ _aff_state = snap["state_s"]
    $ _aff_val = snap["value_s"]
    $ _aff_color = snap["color"]
    $ _aff_ic = store.mas_os.icon_path("affection")
    $ _aff_on = store.mas_os.flag("_mas_os_aff_widget", True)
    $ _mus_on = store.mas_os.flag("_mas_os_music_widget", True)

    use mas_os_bg(show_brand=False)

    for i in range(len(icons)):
        $ caption, ret, icon, hue, badge = icons[i]
        $ _cx = 28 + (i % 2) * 118
        $ _cy = 20 + (i // 2) * 106
        use mas_os_desk_icon(caption, MASOSGo(ret), icon, hue, badge, delay=0.04 * i, xpos=_cx, ypos=_cy)

    if _aff_on:
        use mas_os_desk_window(_("Моника"), 860, 36, 380, 150):
            vbox:
                spacing 4
                xfill True

                hbox:
                    spacing 8

                    if _aff_ic:
                        add store.mas_os.fit_image(_aff_ic, 22, 22):
                            yalign 0.5

                    text _aff_state:
                        style "mas_os_stat_state"
                        size 22
                        color _aff_color
                        yalign 0.5

                text _("Привязанность: [_aff_val]"):
                    style "mas_os_body"

                text ev_line:
                    style "mas_os_hint"
                    size 14

    if _mus_on:
        $ _mus_y = 200 if _aff_on else 36
        use mas_os_player_widget(width=380, height=150, ypos=_mus_y, xpos=860)

    $ _wins = store.mas_os.wm_visible()
    for _wid in _wins:
        use mas_os_app_window(_wid)

    use mas_os_taskbar

    if store.mas_os.start_open:
        use mas_os_start_flyout


style mas_os_desk_icon is default:
    xsize 108
    ysize 100
    padding (4, 6)
    idle_background Solid("#00000000")
    hover_background Solid("#FFFFFF28")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound


style mas_os_desk_icon_text is default:
    font gui.default_font
    size 13
    color "#FFFFFF"
    outlines [(1, "#000000A0", 0, 0)]
    text_align 0.5
    layout "subtitle"
    xmaximum 100


style mas_os_taskbar is default:
    background Solid("#1A0C12F0")


style mas_os_tb_btn is default:
    ysize 36
    padding (8, 4)
    idle_background Solid("#00000000")
    hover_background Solid("#FFFFFF22")
    selected_background Solid("#FFFFFF33")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound


style mas_os_tb_btn_text is default:
    font gui.default_font
    size 15
    color "#FFE6F3"
    outlines []
    layout "subtitle"


style mas_os_app_win is default:
    background Solid("#14070d")


style mas_os_win_tool is default:
    xsize 32
    ysize 26
    padding (0, 0)
    idle_background Solid("#00000000")
    hover_background Solid("#FFFFFF33")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound


style mas_os_win_tool_text is default:
    font gui.default_font
    size 18
    color "#FFFFFF"
    outlines []
    text_align 0.5


style mas_os_desk_win is default:
    background Solid("#1E0C14")


style mas_os_desk_titlebar is default:
    background Solid("#C94A7A")


style mas_os_desk_titlebar_text is default:
    font gui.default_font
    size 15
    color "#FFFFFF"
    outlines []


style mas_os_start_menu is default:
    background Solid("#1A0C12F5")


style mas_os_start_item is default:
    xfill True
    ysize 48
    padding (8, 6)
    idle_background Solid("#00000000")
    hover_background Solid("#FFFFFF18")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound


style mas_os_start_item_text is default:
    font gui.default_font
    size 16
    color "#FFE6F3"
    outlines []
