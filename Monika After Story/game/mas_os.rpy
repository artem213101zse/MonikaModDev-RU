# MAS OS
# Pre-game shell for the Android/port build (DDLC Plus extras-style).
# Must run before splash session/affection startup so visiting the shell
# is not a MAS session and does not trigger crash/reload greetings.
#
# This is a PORT FEATURE, not a submod:
#   - submods init inside the game, after persistent and splash logic
#   - the shell has to work even when submods or persistent are broken
#   - installing submods is something the shell itself will manage

default persistent._mas_os_reopen = False

# "always" — MAS OS on every cold start (Android-friendly default)
# "skip"   — straight into MAS unless the player asked to return to the shell
default persistent._mas_os_boot = "always"

init -10 python in mas_os:
    import os
    import store
    import renpy

    VERSION = "0.1.0-proto"
    game_entered = False

    _active_doc = None
    _active_event = None
    _active_log = None
    gift_input = ""
    gift_status = ""

    ROADMAP = (
        "Сделано:\n"
        "• оболочка до сессии (Моника не обижается на выход из OS)\n"
        "• пропуск OS при запуске\n"
        "• события из календаря на стене\n"
        "• фейковый браузер и тосты реакций на окна\n"
        "• виджет привязанности\n"
        "• подарки в characters и просмотр логов\n\n"
        "Доделать заглушки:\n"
        "• файлы: копировать / удалять / поделиться\n"
        "• данные: экспорт, импорт, бэкап persistent\n"
        "• сабмоды: установка с устройства + перезапуск\n"
        "• настройки: апдейтер порта, обои OS, шрифт, текстбокс\n\n"
        "Дальше по пользе для Android:\n"
        "• спрайтпаки (json + png) до запуска игры\n"
        "• безопасный режим, если сабмод валит init\n"
        "• кастомная музыка и piano_songs\n"
        "• док-станция / monika.chr\n"
        "• API-ключи и часовой пояс\n"
        "• рендер и масштаб UI до старта\n"
        "• календарь на месяц в OS\n"
        "• FAQ порта в документации\n"
        "• картинки на плитки главного меню\n\n"
        "Не тащить в OS: разговоры, extras, мини-игры — это комната Моники."
    )

    # In-game talk-menu button. Swap these two paths when custom art is ready.
    TALK_IDLE = "mod_assets/hkb_idle_background.png"
    TALK_HOVER = "mod_assets/hkb_hover_background.png"
    TALK_SIZE = (120, 35)
    TALK_LABEL = "MAS OS"

    RETURN_CONFIRM = (
        "Вернуться в MAS OS?\n"
        "Сессия с Моникой завершится, приложение не закроется.\n"
        "Она не будет думать, что вы ушли без прощания."
    )

    def can_show():
        """
        True if the pre-game shell should run on this boot.
        """
        if getattr(store.persistent, "_mas_os_reopen", False):
            store.persistent._mas_os_reopen = False
            return True

        if game_entered:
            return False

        if bool(getattr(store, "_restart", False)):
            return False

        return getattr(store.persistent, "_mas_os_boot", "always") != "skip"

    def boot_opens_shell():
        return getattr(store.persistent, "_mas_os_boot", "always") != "skip"

    def set_boot(mode):
        """
        "always" — open MAS OS on cold start.
        "skip"   — go straight into MAS unless the player asked to return.
        """
        if mode not in ("always", "skip"):
            return
        store.persistent._mas_os_boot = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def toggle_boot():
        if boot_opens_shell():
            set_boot("skip")
        else:
            set_boot("always")

    AFF_STATE_NAMES = {
        store.mas_affection.BROKEN: "Разбитая",
        store.mas_affection.DISTRESSED: "Страдающая",
        store.mas_affection.UPSET: "Расстроенная",
        store.mas_affection.NORMAL: "Обычная",
        store.mas_affection.HAPPY: "Счастливая",
        store.mas_affection.AFFECTIONATE: "Привязанная",
        store.mas_affection.ENAMORED: "Влюблённая",
        store.mas_affection.LOVE: "Любовь",
    }

    AFF_STATE_COLORS = {
        store.mas_affection.BROKEN: "#9A8A90",
        store.mas_affection.DISTRESSED: "#C989A8",
        store.mas_affection.UPSET: "#E8A0B8",
        store.mas_affection.NORMAL: "#FFD7EC",
        store.mas_affection.HAPPY: "#FFE6F3",
        store.mas_affection.AFFECTIONATE: "#FFB7D8",
        store.mas_affection.ENAMORED: "#FF8AC4",
        store.mas_affection.LOVE: "#FF5BA2",
    }

    def _aff_state_from_value(val):
        aff = store.mas_affection
        if val <= aff.AFF_BROKEN_MIN:
            return aff.BROKEN
        if val <= aff.AFF_DISTRESSED_MIN:
            return aff.DISTRESSED
        if val <= aff.AFF_UPSET_MIN:
            return aff.UPSET
        if val < aff.AFF_HAPPY_MIN:
            return aff.NORMAL
        if val < aff.AFF_AFFECTIONATE_MIN:
            return aff.HAPPY
        if val < aff.AFF_ENAMORED_MIN:
            return aff.AFFECTIONATE
        if val < aff.AFF_LOVE_MIN:
            return aff.ENAMORED
        return aff.LOVE

    def _fmt_aff(val):
        try:
            val = float(val)
        except Exception:
            return "—"
        if abs(val - round(val)) < 0.05:
            return str(int(round(val)))
        return "{0:.1f}".format(val)

    def aff_snapshot():
        """
        Read-only affection for the home widget.
        Loads saved aff without absence decay or programming points.
        """
        try:
            store._mas_AffLoad()
        except Exception:
            pass

        try:
            val = store._mas_getAffection()
        except Exception:
            val = 0.0

        state = _aff_state_from_value(val)
        return {
            "value": val,
            "value_s": _fmt_aff(val),
            "state": state,
            "state_s": AFF_STATE_NAMES.get(state, "Обычная"),
            "color": AFF_STATE_COLORS.get(state, "#FFD7EC"),
        }

    def next_event_line():
        try:
            rows = upcoming_events()
        except Exception:
            rows = []
        if not rows:
            return "Ближайших событий нет"
        row = rows[0]
        if row["days"] <= 0:
            return "Сегодня: {0}".format(row["title"])
        return "{0} · {1}".format(row["title"], row["when"])

    def enter_shell():
        """
        Puts the runtime into a non-session UI state.
        Does not touch closed_self / sessions / affection totals.
        """
        store.quick_menu = False
        store._confirm_quit = False
        store._dismiss_pause = True
        renpy.config.allow_skipping = False
        try:
            store.renpy.block_rollback()
        except Exception:
            pass
        try:
            store._mas_AffLoad()
        except Exception:
            pass

    def mark_game_entered():
        """
        Call only when the player explicitly launches MAS from the shell.
        """
        global game_entered
        game_entered = True

    def _quit(relaunch=False):
        """
        Named stores import the renpy package, not renpy.exports.
        """
        store.renpy.quit(relaunch=relaunch, status=0, save=True)

    def request_quit():
        """
        Leave the app from the shell without starting a MAS session.
        label quit is still invoked by Ren'Py; it must no-op while
        game_entered is False.
        """
        _quit(relaunch=False)

    def end_game_session():
        """
        Same teardown as label quit: playtime, calendar, affection, sprites.
        Does not exit the process. Used before utter_restart into MAS OS.
        """
        persistent = store.persistent
        dt = store.datetime

        try:
            store.mas_calendar.saveCalendarDatabase(store.CustomEncoder)
        except Exception:
            pass

        try:
            persistent.sessions["last_session_end"] = dt.datetime.now()
            today_time = (
                persistent.sessions["last_session_end"]
                - persistent.sessions["current_session_start"]
            )
            new_time = today_time + persistent.sessions["total_playtime"]
            if dt.timedelta(0) < new_time <= store.mas_maxPlaytime():
                persistent.sessions["total_playtime"] = new_time
            store.mas_dockstat.setMoniSize(persistent.sessions["total_playtime"])
        except Exception:
            pass

        try:
            store.mas_selspr.save_selectables()
        except Exception:
            pass

        try:
            store.monika_chr.save()
        except Exception:
            pass

        try:
            store.mas_weather.saveMWData()
        except Exception:
            pass

        try:
            store.mas_background.saveMBGData()
        except Exception:
            pass

        try:
            store.mas_o31_event.removeImages()
        except Exception:
            pass

        try:
            store.mas_runDelayedActions(store.MAS_FC_END)
            store.mas_delact.saveDelayedActionMap()
        except Exception:
            pass

        try:
            store._mas_AffSave()
        except Exception:
            pass

        try:
            if not persistent._mas_dockstat_going_to_leave:
                store.mas_utils.trydel(
                    store.mas_docking_station._trackPackage("monika")
                )
        except Exception:
            pass

        try:
            store.mas_sprites._clear_caches()
        except Exception:
            pass

        try:
            store.mas_xp.grant()
        except Exception:
            pass

        try:
            store.mas_logging.logging.shutdown()
        except Exception:
            pass

    def reboot_shell():
        """
        Restart the process in-engine back into MAS OS.
        quit(relaunch=True) often just closes a Windows/Android build.
        """
        store.persistent._mas_os_reopen = True
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        store.renpy.utter_restart()

    def return_to_shell():
        """
        End the current MAS session cleanly and restart in-engine into MAS OS.

        closed_self=True and _mas_game_crashed left True → next MAS launch
        is a normal greeting, not crash/reload scold.
        Application stays open (same as Перезагрузка in the shell).
        """
        store.persistent.closed_self = True
        store.persistent._mas_game_crashed = True
        try:
            end_game_session()
        except Exception:
            try:
                store._mas_AffSave()
            except Exception:
                pass
        reboot_shell()

    def platform_name():
        if getattr(renpy, "android", False):
            return "Android"
        if getattr(renpy, "ios", False):
            return "iOS"
        if getattr(renpy, "windows", False):
            return "Windows"
        if getattr(renpy, "macintosh", False):
            return "macOS"
        if getattr(renpy, "linux", False):
            return "Linux"
        return "Unknown"

    def is_touch():
        # renpy.variant lives on renpy.exports, not the renpy package
        # imported into this store. config.variants is always available.
        variants = getattr(renpy.config, "variants", None) or ()
        return bool(
            getattr(renpy, "android", False)
            or getattr(renpy, "ios", False)
            or getattr(renpy, "mobile", False)
            or "mobile" in variants
            or "touch" in variants
        )

    def _norm(path):
        if not path:
            return ""
        return os.path.normpath(path).replace("\\", "/")

    def game_dir():
        return _norm(renpy.config.basedir)

    def save_dir():
        return _norm(renpy.config.savedir)

    def persistent_path():
        return _norm(os.path.join(renpy.config.savedir, "persistent"))

    def characters_dir():
        return _norm(os.path.join(renpy.config.basedir, "characters"))

    def submods_dir():
        return _norm(os.path.join(renpy.config.basedir, "game", "Submods"))

    def log_dir():
        return _norm(os.path.join(renpy.config.basedir, "log"))

    def list_dir_names(path, limit=24):
        """
        Best-effort directory listing. Returns (exists, names, truncated).
        """
        if not path or not os.path.isdir(path):
            return False, [], False

        try:
            names = sorted(os.listdir(path))
        except Exception:
            return True, [], False

        truncated = len(names) > limit
        return True, names[:limit], truncated

    def submod_rows():
        rows = []
        submod_map = getattr(store.mas_submod_utils, "submod_map", {})
        for sm in submod_map.itervalues():
            rows.append((sm.name, sm.version, sm.author))
        rows.sort(key=lambda row: row[0].lower())
        return rows

label mas_os_shell:
    python:
        store.mas_os.enter_shell()

    scene black
    stop music fadeout 0.4
    $ quick_menu = False
    $ _confirm_quit = False
    $ config.allow_skipping = False
    window hide

    jump mas_os_home


label mas_os_home:
    call screen mas_os_home

    if _return == "launch":
        $ store.mas_os.mark_game_entered()
        return

    elif _return == "quit":
        jump mas_os_quit

    elif _return == "events":
        jump mas_os_events

    elif _return == "docs":
        jump mas_os_docs

    elif _return == "files":
        jump mas_os_files

    elif _return == "submods":
        jump mas_os_submods

    elif _return == "data":
        jump mas_os_data

    elif _return == "about":
        jump mas_os_about

    elif _return == "settings":
        jump mas_os_settings

    elif _return == "browser":
        jump mas_os_browser

    elif _return == "gifts":
        jump mas_os_gifts

    elif _return == "logs":
        jump mas_os_logs

    jump mas_os_home


label mas_os_quit:
    python:
        store.mas_os.request_quit()
    return


label mas_os_settings:
    call screen mas_os_settings
    jump mas_os_home


label mas_os_files:
    $ store.mas_os.fm_open()
    jump mas_os_files_loop

label mas_os_files_loop:
    call screen mas_os_files
    if _return == "view":
        jump mas_os_fm_view_loop
    if _return == "gifts":
        jump mas_os_gifts
    if _return == "logs":
        jump mas_os_logs
    jump mas_os_home


label mas_os_fm_view_loop:
    call screen mas_os_fm_view
    if _return == "edit":
        if store.mas_os.fm_begin_edit():
            call screen mas_os_fm_edit
        jump mas_os_fm_view_loop
    jump mas_os_files_loop


label mas_os_submods:
    call screen mas_os_submods
    jump mas_os_home


label mas_os_about:
    call screen mas_os_about
    if _return == "logs":
        jump mas_os_logs
    jump mas_os_home


screen mas_os_confirm(message, yes_action, no_action):
    # Dedicated confirm: the stock confirm screen is wired to Monika's quit scold.
    modal True
    zorder 300

    style_prefix "confirm"

    add Solid("#000000B2")

    frame:
        vbox:
            xalign 0.5
            yalign 0.5
            spacing 30

            label _(message):
                style "confirm_prompt"
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 100

                textbutton _("Да") action yes_action
                textbutton _("Нет") action no_action


screen mas_os_frame(title, subtitle=None):
    modal True
    zorder 200

    add Solid("#14070d")

    vbox:
        xpos 40
        ypos 28
        xsize 1200
        spacing 4

        text title:
            style "mas_os_title"

        if subtitle:
            text subtitle:
                style "mas_os_subtitle"

    transclude

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_notice(message):
    modal True
    zorder 310

    add Solid("#000000B2")

    frame:
        style "mas_os_panel"
        xalign 0.5
        yalign 0.5
        xsize 720
        padding (28, 24)

        vbox:
            spacing 20
            xfill True

            text message:
                style "mas_os_body"
                xalign 0.5
                text_align 0.5

            textbutton _("Понятно"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xalign 0.5
                action Hide("mas_os_notice")


screen mas_os_boot_toggle(width=388):
    $ shell_on = store.mas_os.boot_opens_shell()
    $ half = int((width - 12) / 2)

    vbox:
        spacing 6
        xfill True

        text _("При запуске"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("MAS OS"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected shell_on
                    action Function(store.mas_os.set_boot, "always")

                textbutton _("Игра"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (not shell_on)
                    action Function(store.mas_os.set_boot, "skip")


screen mas_os_ibutton(caption, act, glyph, hue, bstyle="mas_os_tile", tstyle="mas_os_tile_text", align_center=True):
    button:
        style bstyle
        action act
        hover_sound gui.hover_sound
        activate_sound gui.activate_sound

        hbox:
            spacing 10
            if align_center:
                xalign 0.5
            yalign 0.5
            xoffset (0 if align_center else 12)

            frame:
                xysize (32, 32)
                background Solid(hue)
                yalign 0.5

                text glyph:
                    style "mas_os_glyph"
                    xalign 0.5
                    yalign 0.5

            text caption:
                style tstyle
                yalign 0.5


screen mas_os_home():
    modal True
    zorder 200

    $ snap = store.mas_os.aff_snapshot()
    $ ev_line = store.mas_os.next_event_line()
    $ ev_label = store.mas_os.events_button_label()
    $ _aff_state = snap["state_s"]
    $ _aff_val = snap["value_s"]
    $ _aff_color = snap["color"]

    add Solid("#14070d")

    vbox:
        xpos 56
        ypos 36
        spacing 4

        text _("MAS OS"):
            style "mas_os_title"

        text _("[config.name]  ·  v[config.version]"):
            style "mas_os_subtitle"

        text _("Оболочка до запуска игры. Сессия не начинается."):
            style "mas_os_hint"

    button:
        style "mas_os_launch"
        xpos 56
        ypos 150
        default_focus True
        action Return("launch")
        hover_sound gui.hover_sound
        activate_sound gui.activate_sound

        hbox:
            xalign 0.5
            yalign 0.5
            spacing 12

            frame:
                xysize (40, 40)
                background Solid("#FF8AC4")
                yalign 0.5

                text ">":
                    style "mas_os_glyph"
                    size 22
                    xalign 0.5
                    yalign 0.5

            text _("Запустить MAS"):
                style "mas_os_launch_text"
                yalign 0.5

    frame:
        style "mas_os_panel"
        xpos 56
        ypos 280
        xsize 420
        ysize 150
        padding (20, 16)

        vbox:
            spacing 6
            xfill True

            text _("Моника"):
                style "mas_os_hint"

            text _aff_state:
                style "mas_os_stat_state"
                color _aff_color

            text _("Привязанность: [_aff_val]"):
                style "mas_os_body"

            text ev_line:
                style "mas_os_hint"

    frame:
        style "mas_os_panel"
        xpos 56
        ypos 440
        xsize 420
        ysize 102
        padding (16, 10)

        use mas_os_boot_toggle

    grid 2 4:
        xpos 520
        ypos 140
        spacing 12

        use mas_os_ibutton(ev_label, Return("events"), "Сб", "#C94A7A")
        use mas_os_ibutton(_("Документация"), Return("docs"), "Дк", "#7A4A9A")
        use mas_os_ibutton(_("Подарки"), Return("gifts"), "Пд", "#E85A9A")
        use mas_os_ibutton(_("Файлы"), Return("files"), "Фл", "#5A6A9A")
        use mas_os_ibutton(_("Браузер"), Return("browser"), "Бр", "#4A8AAA")
        use mas_os_ibutton(_("Данные"), Return("data"), "Дн", "#8A6A4A")
        use mas_os_ibutton(_("Настройки"), Return("settings"), "Нс", "#6A6A7A")
        use mas_os_ibutton(_("Сабмоды"), Return("submods"), "См", "#4A8A6A")

    hbox:
        xpos 56
        ypos 640
        spacing 12

        use mas_os_ibutton(_("О системе"), Return("about"), "i", "#7A4A9A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True)
        use mas_os_ibutton(_("Логи"), Return("logs"), "Lg", "#8A6A4A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True)
        use mas_os_ibutton(_("Перезагрузка"), Function(store.mas_os.reboot_shell), "R", "#4A8AAA", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True)
        use mas_os_ibutton(_("Выключение"), Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm")), "X", "#8A3A4A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True)

    key "K_ESCAPE" action Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm"))
    key "K_AC_BACK" action Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm"))


screen mas_os_settings():
    modal True
    zorder 200

    add Solid("#14070d")

    text _("Настройки"):
        style "mas_os_title"
        xpos 48
        ypos 28

    text _("Пока заглушки. Сюда потом встанут обновления, обои, шрифт и текстбокс."):
        style "mas_os_hint"
        xpos 48
        ypos 74

    vbox:
        xpos 48
        ypos 120
        spacing 12

        use mas_os_ibutton(_("Проверить обновления порта"), Show("mas_os_notice", message=_("Проверка обновлений порта появится позже.\nСюда можно будет вставить уже готовую реализацию.")), "Up", "#4A8AAA", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False)
        use mas_os_ibutton(_("Обои MAS OS"), Show("mas_os_notice", message=_("Смена обоев оболочки появится позже.\nФон пока сплошной цвет.")), "Bg", "#7A4A9A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False)
        use mas_os_ibutton(_("Шрифт игры и OS"), Show("mas_os_notice", message=_("Смена шрифта появится позже.\nБудет отдельно для игры и для оболочки.")), "Aa", "#8A6A4A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False)
        use mas_os_ibutton(_("Цвет текстбокса"), Show("mas_os_notice", message=_("Варианты текстбокса появятся позже.\nИх можно будет нарисовать в Photoshop и подключить сюда.")), "Tx", "#C94A7A", bstyle="mas_os_button", tstyle="mas_os_button_text", align_center=False)

        frame:
            style "mas_os_panel"
            xsize 720
            ysize 102
            padding (16, 10)

            use mas_os_boot_toggle(width=688)

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_submods():
    $ rows = store.mas_os.submod_rows()

    use mas_os_frame(_("Сабмоды"), _("Список того, что уже загрузилось. Установка с устройства — следующий шаг.")):
        viewport:
            xpos 40
            ypos 110
            xysize (1200, 500)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 10
                xsize 1160

                if rows:
                    for name, version, author in rows:
                        text "[name]  v[version]  —  [author]":
                            style "mas_os_body"
                else:
                    text _("Сейчас не загружен ни один сабмод."):
                        style "mas_os_body"

                text _("Установка, удаление и проверка конфликтов будут здесь. Это не сабмод-меню из самой игры: оно доступно до запуска MAS."):
                    style "mas_os_hint"

        textbutton _("Назад"):
            style "mas_os_button"
            text_style "mas_os_button_text"
            xpos 40
            ypos 630
            action Return("back")


screen mas_os_about():
    $ plat = store.mas_os.platform_name()
    $ touch = _("да") if store.mas_os.is_touch() else _("нет")
    $ rver = renpy.version()
    $ osver = store.mas_os.VERSION

    use mas_os_frame(_("О системе")):
        viewport:
            xpos 40
            ypos 100
            xysize (1200, 510)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 1160

                text _("MAS OS [osver]"):
                    style "mas_os_body"

                text _("Игра: [config.name] [config.version]"):
                    style "mas_os_body"

                text _("Движок: [rver]"):
                    style "mas_os_body"

                text _("Платформа: [plat]"):
                    style "mas_os_body"

                text _("Сенсорный ввод: [touch]"):
                    style "mas_os_body"

                text _("План порта (если чат пропадёт — смотри сюда):"):
                    style "mas_os_body"

                text store.mas_os.ROADMAP:
                    style "mas_os_hint"

                textbutton _("Открыть логи"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    action Return("logs")

        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 40
            ypos 640
            action Return("back")


style mas_os_title is default:
    font gui.default_font
    size 40
    color "#FFE6F3"
    outlines []

style mas_os_subtitle is default:
    font gui.default_font
    size 18
    color "#FF9AC8"
    outlines []

style mas_os_hint is default:
    font gui.default_font
    size 16
    color "#C989A8"
    outlines []

style mas_os_glyph is default:
    font gui.default_font
    size 13
    color "#1A0810"
    outlines []
    text_align 0.5

style mas_os_link is default:
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_link_text is mas_os_hint:
    idle_color "#C989A8"
    hover_color "#FFE6F3"
    insensitive_color "#8C6B7A"

style mas_os_toggle_track is default:
    background Solid("#2A1018")

style mas_os_toggle_opt is default:
    ysize 44
    padding (8, 6)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    selected_background Solid("#C94A7A")
    selected_hover_background Solid("#E05A8A")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_toggle_opt_text is generic_button_text_dark:
    size 18
    text_align 0.5
    xalign 0.5
    yalign 0.5
    layout "subtitle"
    idle_color "#C989A8"
    hover_color "#FFE6F3"
    selected_color "#FFFFFF"

style mas_os_gift_field is default:
    padding (12, 8)
    idle_background Solid("#2A1018")
    hover_background Solid("#3A1524")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_cat_btn is default:
    xsize 150
    ysize 36
    padding (8, 4)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    selected_background Solid("#C94A7A")
    selected_hover_background Solid("#E05A8A")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_cat_btn_text is generic_button_text_dark:
    size 16
    text_align 0.5
    xalign 0.5
    yalign 0.5
    layout "subtitle"
    idle_color "#C989A8"
    hover_color "#FFE6F3"
    selected_color "#FFFFFF"

style mas_os_body is default:
    font gui.default_font
    size 20
    color "#FFD7EC"
    outlines []

style mas_os_stat_state is default:
    font gui.default_font
    size 28
    outlines []

style mas_os_panel is default:
    background Solid("#1E0C14")

style mas_os_launch is default:
    xsize 420
    ysize 108
    padding (18, 18)
    idle_background Solid("#7A2850")
    hover_background Solid("#C94A7A")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_launch_text is generic_button_text_dark:
    size 28
    text_align 0.5
    layout "subtitle"
    idle_color "#FFF0F7"
    hover_color "#FFFFFF"

style mas_os_tile is default:
    xsize 340
    ysize 78
    padding (12, 12)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_tile_text is generic_button_text_dark:
    size 22
    text_align 0.5
    layout "subtitle"
    idle_color "#FFE6F3"
    hover_color "#FFFFFF"

style mas_os_side_btn is default:
    xsize 320
    ysize 68
    padding (14, 8)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    selected_background Solid("#8A3060")
    selected_hover_background Solid("#A03C70")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_side_btn_text is generic_button_text_dark:
    size 17
    text_align 0.0
    xalign 0.0
    layout "subtitle"
    idle_color "#FFD7EC"
    hover_color "#FFFFFF"
    selected_color "#FFFFFF"

style mas_os_nav_btn is default:
    xsize 230
    ysize 44
    padding (10, 6)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_nav_btn_text is generic_button_text_dark:
    size 18
    text_align 0.5
    layout "subtitle"
    idle_color "#FFE6F3"
    hover_color "#FFFFFF"

style mas_os_talk_btn:
    background None
    padding (0, 0)
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_talk_btn_text:
    font gui.default_font
    size 14
    color "#000"
    outlines []
    text_align 0.5
    align (0.5, 0.5)
    layout "subtitle"

style mas_os_button is generic_button_dark:
    xsize 720
    ysize 56
    padding (18, 12)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    insensitive_background Solid("#2A121C")

style mas_os_button_text is generic_button_text_dark:
    size 22
    text_align 0.5
    layout "subtitle"
    idle_color "#FFE6F3"
    hover_color "#FFFFFF"
    insensitive_color "#8C6B7A"
