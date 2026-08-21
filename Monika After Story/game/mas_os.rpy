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

# "rise" — windows slide up (current)
# "zoom" — windows fade in, grow, and unblur
default persistent._mas_os_motion = "rise"
# logo / bloom / glitch / iris / off
default persistent._mas_os_launch_anim = "logo"
default persistent._mas_os_sfx = True
default persistent._mas_os_stagger = True
default persistent._mas_os_talk_btn = True
default persistent._mas_os_menu_btn = True
default persistent._mas_os_aff_widget = True
default persistent._mas_os_music_widget = True
default persistent._mas_os_music_autoplay = False
default persistent._mas_os_music_loop = "one"
default persistent._mas_os_music_shuffle = False
default persistent._mas_os_return_confirm = True
default persistent._mas_os_quit_confirm = True
default persistent._mas_os_textbox = "pink"
default persistent._mas_os_font = "aller"
default persistent._mas_os_font_menu = "riffic"
default persistent._mas_os_font_ui = "halogen"
default persistent._mas_os_font_notes = "m1"
default persistent._mas_os_wallpaper = "splash.png"
default persistent._mas_os_wp_dim = True
default persistent._mas_os_theme = "dark"
default persistent._mas_os_setup_done = False
# off — полное вступление; tips — без болтовни, подсказки t/m/p остаются; all — только служебный код
default persistent._mas_os_intro_skip = "off"

init -10 python in mas_os:
    import os
    import store
    import renpy

    VERSION = "0.1.0-proto"
    game_entered = False

    _active_doc = None
    _active_event = None
    settings_cat = "boot"
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

    OS_DEFAULTS = (
        ("_mas_os_boot", "always"),
        ("_mas_os_motion", "rise"),
        ("_mas_os_launch_anim", "logo"),
        ("_mas_os_sfx", True),
        ("_mas_os_stagger", True),
        ("_mas_os_talk_btn", True),
        ("_mas_os_menu_btn", True),
        ("_mas_os_aff_widget", True),
        ("_mas_os_music_widget", True),
        ("_mas_os_music_autoplay", False),
        ("_mas_os_music_loop", "one"),
        ("_mas_os_music_shuffle", False),
        ("_mas_os_return_confirm", True),
        ("_mas_os_quit_confirm", True),
        ("_mas_os_textbox", "pink"),
        ("_mas_os_font", "aller"),
        ("_mas_os_font_menu", "riffic"),
        ("_mas_os_font_ui", "halogen"),
        ("_mas_os_font_notes", "m1"),
        ("_mas_os_wallpaper", "splash.png"),
        ("_mas_os_wp_dim", True),
        ("_mas_os_theme", "dark"),
        ("_mas_os_intro_skip", "off"),
    )

    def reset_os_settings():
        persistent = store.persistent
        for key, value in OS_DEFAULTS:
            setattr(persistent, key, value)
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        try:
            apply_theme()
        except Exception:
            pass
        try:
            apply_font()
        except Exception:
            pass
        try:
            apply_textbox()
        except Exception:
            pass
        return None

    INTRO_SKIP_MODES = (
        (
            "off",
            "Не пропускать",
            "Полное вступление. Для первого знакомства: Моника объяснит мод сама.",
        ),
        (
            "tips",
            "Только подсказки",
            "Без длинной болтовни. Останется как открыть разговор, музыку, игры и закладки.",
        ),
        (
            "all",
            "Всё вступление",
            "Только служебный код (файл персонажа, флаги). Подсказки потом могут всплыть в разговоре.",
        ),
    )

    def intro_skip_mode():
        mode = getattr(store.persistent, "_mas_os_intro_skip", "off") or "off"
        if mode in ("off", "tips", "all"):
            return mode
        return "off"

    def set_intro_skip(mode):
        if mode not in ("off", "tips", "all"):
            mode = "off"
        store.persistent._mas_os_intro_skip = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def needs_setup():
        if getattr(store.persistent, "_mas_os_setup_done", False):
            return False
        sessions = getattr(store.persistent, "sessions", None) or {}
        try:
            total = int(sessions.get("total_sessions", 0) or 0)
        except Exception:
            total = 0
        if total > 0:
            store.persistent._mas_os_setup_done = True
            try:
                store.renpy.save_persistent()
            except Exception:
                pass
            return False
        return True

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

    def motion_zoom():
        return getattr(store.persistent, "_mas_os_motion", "rise") == "zoom"

    def set_motion(mode):
        if mode not in ("rise", "zoom"):
            return
        store.persistent._mas_os_motion = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    LAUNCH_ANIMS = (
        (
            "logo",
            "Логотип",
            "Кнопка выезжает в центр, экран темнеет, появляется логотип DDLC и бесконечная полоска.",
        ),
        (
            "bloom",
            "Вспышка",
            "Розовый свет заливает оболочку, вспыхивает название, потом комната.",
        ),
        (
            "glitch",
            "Глитч",
            "Помехи и дёрганый логотип, как в оригинальном DDLC. Резкий обрыв.",
        ),
        (
            "iris",
            "Схлопывание",
            "Оболочка втягивается в кнопку запуска и гаснет.",
        ),
        (
            "off",
            "Без анимации",
            "Короткое затемнение, сразу игра.",
        ),
    )

    launch_preview = False
    launch_preview_mode = None
    _settings_no_trans = False

    def launch_anim_id():
        if launch_preview_mode:
            return launch_preview_mode
        mode = getattr(store.persistent, "_mas_os_launch_anim", "logo") or "logo"
        for row in LAUNCH_ANIMS:
            if row[0] == mode:
                return mode
        return "logo"

    def launch_anim_on():
        return launch_anim_id() != "off"

    def set_launch_anim(mode):
        ids = [row[0] for row in LAUNCH_ANIMS]
        if mode not in ids:
            mode = "logo"
        store.persistent._mas_os_launch_anim = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def start_launch_preview(mode):
        global launch_preview, launch_preview_mode
        ids = [row[0] for row in LAUNCH_ANIMS]
        if mode not in ids:
            mode = "logo"
        launch_preview = True
        launch_preview_mode = mode
        return None

    def end_launch_preview():
        global launch_preview, launch_preview_mode
        launch_preview = False
        launch_preview_mode = None
        return None

    def finish_launch_anim():
        if launch_preview:
            return "preview"
        return "launch"

    def launch_logo_path():
        for path in ("mod_assets/menu_new.png", "bg/splash.png"):
            try:
                if store.renpy.loadable(path):
                    return path
            except Exception:
                pass
        return None

    def flag(name, default=True):
        return bool(getattr(store.persistent, name, default))

    def set_flag(name, value):
        setattr(store.persistent, name, bool(value))
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def set_settings_cat(cat_id):
        global settings_cat
        settings_cat = cat_id or "boot"

    def os_hover():
        if flag("_mas_os_sfx", True):
            return store.gui.hover_sound
        return None

    def os_activate():
        if flag("_mas_os_sfx", True):
            return store.gui.activate_sound
        return None

    ICON_ROOT = "mod_assets/mas_os/icons/"

    TEXTBOX_COLORS = (
        ("pink", "Розовый", "gui/textbox_d.png"),
        ("blue", "Синий", "gui/textbox_d_blue.png"),
        ("purple", "Фиолетовый", "gui/textbox_d_purple.png"),
        ("green", "Зелёный", "gui/textbox_d_green.png"),
    )

    def textbox_id():
        color = getattr(store.persistent, "_mas_os_textbox", "pink") or "pink"
        for tid, title, path in TEXTBOX_COLORS:
            if tid == color:
                return color
        return "pink"

    def textbox_dark_path():
        color = textbox_id()
        if color == "pink":
            path = "gui/textbox_d.png"
        else:
            path = "gui/textbox_d_{0}.png".format(color)
        try:
            if store.renpy.loadable(path):
                return path
        except Exception:
            pass
        return "gui/textbox_d.png"

    def apply_textbox():
        """
        Point dark-mode say window at the chosen PNG.
        Light mode keeps the stock textbox.png (no extra variants yet).
        """
        dark = textbox_dark_path()
        try:
            store.style.window_dark.background = store.Image(
                dark, xalign=0.5, yalign=1.0
            )
        except Exception:
            pass
        monika = dark.replace("textbox_d", "textbox_monika_d")
        try:
            if not store.renpy.loadable(monika):
                monika = "gui/textbox_monika_d.png"
            store.style.window_monika_dark.background = store.Image(
                monika, xalign=0.5, yalign=1.0
            )
        except Exception:
            pass
        try:
            store.style.rebuild()
        except Exception:
            pass

    def set_textbox(color):
        ids = [row[0] for row in TEXTBOX_COLORS]
        if color not in ids:
            color = "pink"
        store.persistent._mas_os_textbox = color
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        apply_textbox()

    FONT_PACKS = (
        ("aller", "Обычный (Aller)", "gui/font/Aller_Rg.ttf"),
        ("riffic", "Заголовки (Riffic)", "gui/font/RifficFree-Bold.ttf"),
        ("halogen", "UI (Halogen)", "gui/font/Halogen.ttf"),
        ("m1", "Записки (m1)", "mod_assets/font/m1_fixed.ttf"),
        (
            "shantell",
            "Shantell Sans",
            "mod_assets/font/ShantellSans-VariableFont_BNCE,INFM,SPAC,wght.ttf",
        ),
        (
            "shantell_italic",
            "Shantell Sans курсив",
            "mod_assets/font/ShantellSans-Italic-VariableFont_BNCE,INFM,SPAC,wght.ttf",
        ),
        (
            "greatvibes",
            "Great Vibes",
            "mod_assets/font/GreatVibes-Regular.ttf",
        ),
    )

    FONT_SLOTS = (
        ("dialogue", "Реплики Моники", "Текст в текстбоксе и MAS OS.", "_mas_os_font", "aller"),
        ("menu", "Меню и заголовки", "Пауза, «Настройки», пункты навигации.", "_mas_os_font_menu", "riffic"),
        ("ui", "Кнопки и мелкий UI", "Галочки в настройках игры, поэмы, hangman.", "_mas_os_font_ui", "halogen"),
        ("notes", "Записки календаря", "Заметки на днях и стихи Моники.", "_mas_os_font_notes", "m1"),
    )

    _FONT_STYLES = {
        "dialogue": (
            "default", "normal", "say_dialogue", "gui_text",
            "button_text", "button_text_dark",
            "choice_button_text", "choice_button_text_dark",
            "talk_choice_button_text", "talk_choice_button_text_dark",
            "label_text", "label_text_dark",
            "mas_os_title", "mas_os_subtitle", "mas_os_hint", "mas_os_body",
            "mas_os_stat_state", "mas_os_launch_text", "mas_os_tile_text",
            "mas_os_side_btn_text", "mas_os_nav_btn_text", "mas_os_button_text",
            "mas_os_toggle_opt_text", "mas_os_link_card_title",
            "mas_os_link_card_hint",
        ),
        "menu": (
            "navigation_button_text", "navigation_button_text_dark",
            "game_menu_label_text", "game_menu_label_text_dark",
            "pref_label_text", "pref_label_text_dark",
        ),
        "ui": (
            "poemgame_text", "poemgame_text_dark",
            "radio_button_text", "radio_button_text_dark",
            "check_button_text", "check_button_text_dark",
            "generic_fancy_check_button_text",
            "generic_fancy_check_button_text_dark",
            "generic_fancy_check_button_disabled_text",
            "chibika_note_text",
            "hangman_text",
        ),
        "notes": (
            "mas_monika_poem_text",
        ),
    }

    _font_prev = {
        "dialogue": None,
        "menu": "gui/font/RifficFree-Bold.ttf",
        "ui": "gui/font/Halogen.ttf",
        "notes": "mod_assets/font/m1_fixed.ttf",
    }

    def font_id(slot="dialogue"):
        default = "aller"
        persist_key = "_mas_os_font"
        for sid, title, hint, key, def_id in FONT_SLOTS:
            if sid == slot:
                default = def_id
                persist_key = key
                break
        fid = getattr(store.persistent, persist_key, default) or default
        for row in FONT_PACKS:
            if row[0] == fid:
                return fid
        return default

    def font_latin_path(slot="dialogue"):
        fid = font_id(slot)
        for row in FONT_PACKS:
            if row[0] == fid:
                path = row[2]
                try:
                    if store.renpy.loadable(path):
                        return path
                except Exception:
                    pass
        return "gui/font/Aller_Rg.ttf"

    def _fontgroup(latin_path):
        return (
            store.FontGroup()
            .add("mod_assets/font/SourceHanSansK-Regular.otf", 0xac00, 0xd7a3)
            .add("mod_assets/font/SourceHanSansSC-Regular.otf", 0x4e00, 0x9faf)
            .add("mod_assets/font/mplus-2p-regular.ttf", 0x3000, 0x4dff)
            .add(latin_path, 0x0000, 0xffff)
        )

    def _set_styles_font(names, font_obj):
        for name in names:
            st = getattr(store.style, name, None)
            if st is None:
                continue
            try:
                st.font = font_obj
            except Exception:
                pass

    def _retarget_font(old_font, new_font):
        if old_font is None:
            return
        styles = getattr(store.renpy.style, "styles", None) or {}
        for key in list(styles.keys()):
            name = key[0] if key else None
            if not name:
                continue
            st = getattr(store.style, name, None)
            if st is None:
                continue
            try:
                cur = st.font
            except Exception:
                continue
            if cur is old_font or cur == old_font:
                try:
                    st.font = new_font
                except Exception:
                    pass

    _COMPACT_STYLES = (
        "hkb_button_text", "hkb_button_text_dark",
        "mas_os_talk_btn_text",
        "quick_button_text", "quick_button_text_dark",
        "generic_button_text_base",
        "generic_button_text_light", "generic_button_text_dark",
    )

    def apply_font():
        """
        Apply all font slots. CJK fallbacks stay in the FontGroup.
        Tight in-game buttons (hkb 120×35, quick menu) keep a latin-only
        font: FontGroup CJK metrics overflow those boxes on phones.
        """
        dlg_path = font_latin_path("dialogue")
        mobile = False
        try:
            mobile = is_touch()
        except Exception:
            mobile = False
        if mobile and "variable" in (dlg_path or "").lower():
            dlg_path = "gui/font/Aller_Rg.ttf"
        try:
            dlg_fg = _fontgroup(dlg_path)
        except Exception:
            return

        compact_font = dlg_path
        if mobile and "variable" in (compact_font or "").lower():
            compact_font = "gui/font/Aller_Rg.ttf"

        old_dlg = _font_prev.get("dialogue")
        if old_dlg is None:
            old_dlg = store.gui.default_font
        _retarget_font(old_dlg, dlg_fg)
        store.gui.default_font = dlg_fg
        store.gui.interface_font = dlg_fg
        store.gui.button_text_font = compact_font
        store.gui.choice_button_text_font = dlg_fg
        _set_styles_font(_FONT_STYLES["dialogue"], dlg_fg)
        _set_styles_font(_COMPACT_STYLES, compact_font)
        for name, size in (
            ("hkb_button_text", 16),
            ("hkb_button_text_dark", 16),
            ("mas_os_talk_btn_text", 14),
        ):
            st = getattr(store.style, name, None)
            if st is None:
                continue
            try:
                st.size = size
                st.align = (0.5, 0.5)
            except Exception:
                pass
        if mobile:
            for name, size in (
                ("hkb_button_text", 15),
                ("hkb_button_text_dark", 15),
                ("mas_os_talk_btn_text", 13),
                ("quick_button_text", 13),
                ("quick_button_text_dark", 13),
                ("generic_button_text_base", 16),
                ("generic_button_text_light", 16),
                ("generic_button_text_dark", 16),
            ):
                st = getattr(store.style, name, None)
                if st is None:
                    continue
                try:
                    st.size = size
                    st.align = (0.5, 0.5)
                    st.text_align = 0.5
                except Exception:
                    pass
            for name in ("hkb_button", "hkb_button_dark"):
                st = getattr(store.style, name, None)
                if st is None:
                    continue
                try:
                    st.xysize = (168, 48)
                    st.padding = (6, 8, 6, 8)
                except Exception:
                    pass
            try:
                if getattr(store.gui, "text_size", 24) > 24:
                    store.gui.text_size = 22
            except Exception:
                pass
        _font_prev["dialogue"] = dlg_fg

        menu_path = font_latin_path("menu")
        try:
            menu_fg = _fontgroup(menu_path)
        except Exception:
            menu_fg = dlg_fg
        _retarget_font(_font_prev.get("menu"), menu_fg)
        _set_styles_font(_FONT_STYLES["menu"], menu_fg)
        _font_prev["menu"] = menu_fg

        ui_path = font_latin_path("ui")
        try:
            ui_fg = _fontgroup(ui_path)
        except Exception:
            ui_fg = dlg_fg
        _retarget_font(_font_prev.get("ui"), ui_fg)
        _set_styles_font(_FONT_STYLES["ui"], ui_fg)
        _font_prev["ui"] = ui_fg

        notes_path = font_latin_path("notes")
        _retarget_font(_font_prev.get("notes"), notes_path)
        _set_styles_font(_FONT_STYLES["notes"], notes_path)
        _font_prev["notes"] = notes_path
        try:
            store.MASCalendar.NOTE_FONT = notes_path
        except Exception:
            pass

        try:
            store.style.rebuild()
        except Exception:
            pass

    def set_font(fid, slot="dialogue"):
        ids = [row[0] for row in FONT_PACKS]
        persist_key = "_mas_os_font"
        default = "aller"
        for sid, title, hint, key, def_id in FONT_SLOTS:
            if sid == slot:
                persist_key = key
                default = def_id
                break
        if fid not in ids:
            fid = default
        setattr(store.persistent, persist_key, fid)
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        apply_font()

    def icon_path(name):
        if not name:
            return None
        path = ICON_ROOT + name + ".png"
        try:
            if store.renpy.loadable(path):
                return path
        except Exception:
            pass
        return None

    WP_REL = "mod_assets/mas_os/wallpapers"
    WP_EXTS = (".png", ".jpg", ".jpeg")

    def wallpaper_dir():
        return os.path.join(game_dir(), "game", "mod_assets", "mas_os", "wallpapers")

    def list_wallpapers():
        rows = [("solid", "Сплошной цвет", None)]
        folder = wallpaper_dir()
        if not os.path.isdir(folder):
            return rows
        try:
            names = sorted(os.listdir(folder))
        except Exception:
            return rows
        for name in names:
            ext = os.path.splitext(name)[1].lower()
            if ext not in WP_EXTS:
                continue
            rel = WP_REL + "/" + name
            try:
                if not store.renpy.loadable(rel):
                    continue
            except Exception:
                continue
            title = os.path.splitext(name)[0].replace("_", " ").replace("-", " ")
            rows.append((name, title, rel))
        return rows

    def wallpaper_grid_cells(cols=2):
        items = list_wallpapers()
        cells = list(items)
        while len(cells) % cols:
            cells.append(None)
        nrows = max(1, len(cells) // cols)
        return cols, nrows, cells

    def wallpaper_id():
        wid = getattr(store.persistent, "_mas_os_wallpaper", "splash.png")
        if not wid or wid == "solid":
            return "solid"
        rel = WP_REL + "/" + wid
        try:
            if store.renpy.loadable(rel):
                return wid
        except Exception:
            pass
        return "solid"

    def wallpaper_rel():
        wid = wallpaper_id()
        if wid == "solid":
            return None
        return WP_REL + "/" + wid

    def wallpaper_disp():
        rel = wallpaper_rel()
        if not rel:
            return store.Solid(theme_color("bg"))
        try:
            iw, ih = store.renpy.image_size(rel)
            if iw and ih:
                z = max(1280.0 / float(iw), 720.0 / float(ih))
                return store.Transform(rel, zoom=z)
        except Exception:
            pass
        return rel

    def set_wallpaper(wid):
        store.persistent._mas_os_wallpaper = wid or "solid"
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    THEME_DARK = {
        "bg": "#14070d",
        "bg_dim": "#14070dA6",
        "panel": "#1E0C14",
        "panel2": "#2A1018",
        "btn": "#3A1524",
        "btn_hover": "#6A2442",
        "btn_sel": "#8A3060",
        "btn_sel_hover": "#A03C70",
        "launch": "#7A2850",
        "launch_hover": "#C94A7A",
        "accent": "#C94A7A",
        "accent_hover": "#E05A8A",
        "title": "#FFE6F3",
        "subtitle": "#FF9AC8",
        "hint": "#C989A8",
        "body": "#FFD7EC",
        "btn_text": "#FFE6F3",
        "btn_text_hover": "#FFFFFF",
        "selected_text": "#FFFFFF",
        "insensitive": "#8C6B7A",
        "input": "#FFF0F7",
        "log": "#E8D0DC",
        "link_card": "#1E0C14",
        "link_card_hover": "#3A1524",
    }

    THEME_LIGHT = {
        "bg": "#FFF4F8",
        "bg_dim": "#FFF4F8B8",
        "panel": "#FFFFFF",
        "panel2": "#FFE8F1",
        "btn": "#FFD4E6",
        "btn_hover": "#FFB7D8",
        "btn_sel": "#FF8AC4",
        "btn_sel_hover": "#FF5BA2",
        "launch": "#FF8AC4",
        "launch_hover": "#FF5BA2",
        "accent": "#E85A9A",
        "accent_hover": "#FF7AB8",
        "title": "#7A2850",
        "subtitle": "#C94A7A",
        "hint": "#A05078",
        "body": "#5A2038",
        "btn_text": "#5A2038",
        "btn_text_hover": "#3A1024",
        "selected_text": "#FFFFFF",
        "insensitive": "#C989A8",
        "input": "#5A2038",
        "log": "#5A2038",
        "link_card": "#FFFFFF",
        "link_card_hover": "#FFE6F0",
    }

    def theme_light():
        return getattr(store.persistent, "_mas_os_theme", "dark") == "light"

    def theme_color(key):
        pal = THEME_LIGHT if theme_light() else THEME_DARK
        if key in pal:
            return pal[key]
        return THEME_DARK.get(key, "#14070d")

    def apply_theme():
        c = theme_color
        st = store.style
        Solid = store.Solid
        try:
            st.mas_os_title.color = c("title")
            st.mas_os_subtitle.color = c("subtitle")
            st.mas_os_hint.color = c("hint")
            st.mas_os_body.color = c("body")
            st.mas_os_link_text.idle_color = c("hint")
            st.mas_os_link_text.hover_color = c("title")
            st.mas_os_toggle_track.background = Solid(c("panel2"))
            st.mas_os_toggle_opt.idle_background = Solid(c("btn"))
            st.mas_os_toggle_opt.hover_background = Solid(c("btn_hover"))
            st.mas_os_toggle_opt.selected_background = Solid(c("accent"))
            st.mas_os_toggle_opt.selected_hover_background = Solid(c("accent_hover"))
            st.mas_os_toggle_opt_text.idle_color = c("hint")
            st.mas_os_toggle_opt_text.hover_color = c("title")
            st.mas_os_toggle_opt_text.selected_color = c("selected_text")
            st.mas_os_gift_field.idle_background = Solid(c("panel2"))
            st.mas_os_gift_field.hover_background = Solid(c("btn"))
            st.mas_os_cat_btn.idle_background = Solid(c("btn"))
            st.mas_os_cat_btn.hover_background = Solid(c("btn_hover"))
            st.mas_os_cat_btn.selected_background = Solid(c("accent"))
            st.mas_os_cat_btn.selected_hover_background = Solid(c("accent_hover"))
            st.mas_os_cat_btn_text.idle_color = c("hint")
            st.mas_os_cat_btn_text.hover_color = c("title")
            st.mas_os_cat_btn_text.selected_color = c("selected_text")
            st.mas_os_panel.background = Solid(c("panel"))
            st.mas_os_launch.idle_background = Solid(c("launch"))
            st.mas_os_launch.hover_background = Solid(c("launch_hover"))
            st.mas_os_launch_text.idle_color = c("selected_text")
            st.mas_os_launch_text.hover_color = "#FFFFFF"
            st.mas_os_tile.idle_background = Solid(c("btn"))
            st.mas_os_tile.hover_background = Solid(c("btn_hover"))
            st.mas_os_tile_text.idle_color = c("btn_text")
            st.mas_os_tile_text.hover_color = c("btn_text_hover")
            st.mas_os_side_btn.idle_background = Solid(c("btn"))
            st.mas_os_side_btn.hover_background = Solid(c("btn_hover"))
            st.mas_os_side_btn.selected_background = Solid(c("btn_sel"))
            st.mas_os_side_btn.selected_hover_background = Solid(c("btn_sel_hover"))
            st.mas_os_side_btn_text.idle_color = c("body")
            st.mas_os_side_btn_text.hover_color = c("btn_text_hover")
            st.mas_os_side_btn_text.selected_color = c("selected_text")
            st.mas_os_nav_btn.idle_background = Solid(c("btn"))
            st.mas_os_nav_btn.hover_background = Solid(c("btn_hover"))
            st.mas_os_nav_btn_text.idle_color = c("btn_text")
            st.mas_os_nav_btn_text.hover_color = c("btn_text_hover")
            st.mas_os_button.idle_background = Solid(c("btn"))
            st.mas_os_button.hover_background = Solid(c("btn_hover"))
            st.mas_os_button.insensitive_background = Solid(c("panel2"))
            st.mas_os_button_text.idle_color = c("btn_text")
            st.mas_os_button_text.hover_color = c("btn_text_hover")
            st.mas_os_button_text.insensitive_color = c("insensitive")
        except Exception:
            pass
        try:
            st.mas_os_bar.left_bar = Solid(c("accent"))
            st.mas_os_bar.right_bar = Solid(c("panel2"))
            st.mas_os_bar.thumb = Solid(c("title"))
            st.mas_os_player_btn.idle_background = Solid(c("btn"))
            st.mas_os_player_btn.hover_background = Solid(c("btn_hover"))
            st.mas_os_player_btn.selected_background = Solid(c("accent"))
            st.mas_os_player_btn.selected_hover_background = Solid(c("accent_hover"))
            st.mas_os_player_btn_text.idle_color = c("btn_text")
            st.mas_os_player_btn_text.hover_color = c("btn_text_hover")
            st.mas_os_player_btn_text.selected_color = c("selected_text")
            st.mas_os_player_mini.idle_background = Solid(c("btn"))
            st.mas_os_player_mini.hover_background = Solid(c("btn_hover"))
            st.mas_os_player_mini_text.idle_color = c("body")
            st.mas_os_player_mini_text.hover_color = c("btn_text_hover")
        except Exception:
            pass
        try:
            st.mas_os_log_text.color = c("log")
        except Exception:
            pass
        try:
            st.mas_os_link_card.idle_background = Solid(c("link_card"))
            st.mas_os_link_card.hover_background = Solid(c("link_card_hover"))
            st.mas_os_link_card_title.color = c("selected_text")
            st.mas_os_link_card_hint.color = c("body")
        except Exception:
            pass
        try:
            store.style.rebuild()
        except Exception:
            pass

    def set_theme(mode):
        if mode not in ("dark", "light"):
            return
        store.persistent._mas_os_theme = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        apply_theme()

    def _motion_delay(delay):
        if not flag("_mas_os_stagger", True):
            return 0.0
        return delay

    def t_pop(delay=0.0):
        delay = _motion_delay(delay)
        if motion_zoom():
            return store.mas_os_pop_zoom(delay)
        return store.mas_os_pop(delay)

    def t_page():
        if motion_zoom():
            return store.mas_os_page_zoom
        return store.mas_os_page

    def t_tile(delay=0.0):
        delay = _motion_delay(delay)
        if motion_zoom():
            return store.mas_os_tile_zoom(delay)
        return store.mas_os_tile_in(delay)

    def t_launch():
        if motion_zoom():
            return store.mas_os_launch_zoom
        return store.mas_os_launch_in

    def t_modal():
        if motion_zoom():
            return store.mas_os_modal_zoom
        return store.mas_os_modal

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
        try:
            apply_font()
        except Exception:
            pass
        try:
            apply_textbox()
        except Exception:
            pass
        try:
            apply_theme()
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
    $ store.mas_os.player_on_enter()
    $ quick_menu = False
    $ _confirm_quit = False
    $ config.allow_skipping = False
    window hide

    jump mas_os_home


label mas_os_home:
    call screen mas_os_home with mas_os_trans

    if _return == "launch":
        hide screen mas_os_launch_anim
        scene black
        $ store.mas_os.mark_game_entered()
        return

    if _return == "preview":
        hide screen mas_os_launch_anim
        $ store.mas_os.end_launch_preview()
        jump mas_os_home

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

    elif _return == "store":
        $ store.mas_os.dl_from = "home"
        jump mas_os_store

    elif _return == "logs":
        jump mas_os_logs

    elif _return == "player":
        jump mas_os_player

    jump mas_os_home


label mas_os_quit:
    python:
        store.mas_os.request_quit()
    return


label mas_os_settings:
    if store.mas_os._settings_no_trans:
        $ store.mas_os._settings_no_trans = False
        call screen mas_os_settings
    else:
        call screen mas_os_settings with mas_os_trans
    if _return == "preview":
        hide screen mas_os_launch_anim
        $ store.mas_os.end_launch_preview()
        $ store.mas_os._settings_no_trans = True
        jump mas_os_settings
    if _return == "player":
        jump mas_os_player
    if _return == "store":
        jump mas_os_store
    if _return == "setup":
        $ store.mas_os.setup_from = "settings"
        jump mas_os_setup
    jump mas_os_home


label mas_os_player:
    call screen mas_os_player with mas_os_trans
    if _return == "store":
        jump mas_os_store
    jump mas_os_home


label mas_os_files:
    $ store.mas_os.fm_open()
    jump mas_os_files_loop

label mas_os_files_loop:
    call screen mas_os_files with mas_os_trans
    if _return == "view":
        jump mas_os_fm_view_loop
    if _return == "gifts":
        jump mas_os_gifts
    if _return == "logs":
        jump mas_os_logs
    jump mas_os_home


label mas_os_fm_view_loop:
    call screen mas_os_fm_view with mas_os_trans
    if _return == "edit":
        if store.mas_os.fm_begin_edit():
            call screen mas_os_fm_edit with mas_os_trans
        jump mas_os_fm_view_loop
    jump mas_os_files_loop


label mas_os_submods:
    call screen mas_os_submods with mas_os_trans
    if _return == "store":
        jump mas_os_store
    jump mas_os_home


label mas_os_about:
    call screen mas_os_about with mas_os_trans
    if _return == "logs":
        jump mas_os_logs
    jump mas_os_home


screen mas_intro_skip_btn():
    zorder 90

    textbutton _("Пропустить"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 1040
        ypos 12
        action Jump("mas_intro_safe_skip")
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()


screen mas_os_intro_skip_picker(width=760):
    $ mode = store.mas_os.intro_skip_mode()

    vbox:
        spacing 8
        xfill True

        for mid, mtitle, mhint in store.mas_os.INTRO_SKIP_MODES:
            button:
                style "mas_os_side_btn"
                xsize width
                ysize 72
                selected (mid == mode)
                hover_sound store.mas_os.os_hover()
                activate_sound store.mas_os.os_activate()
                action Function(store.mas_os.set_intro_skip, mid)

                vbox:
                    spacing 2
                    yalign 0.5
                    xoffset 12
                    xsize (width - 24)

                    text mtitle:
                        style "mas_os_side_btn_text"
                        substitute False

                    text mhint:
                        style "mas_os_hint"
                        size 13
                        xsize (width - 40)
                        substitute False


screen mas_os_confirm(message, yes_action, no_action):
    # Dedicated confirm: the stock confirm screen is wired to Monika's quit scold.
    modal True
    zorder 300

    style_prefix "confirm"

    add Solid("#000000B2") at mas_os_dim

    frame at store.mas_os.t_modal():
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

                textbutton _("Да"):
                    at mas_os_btn
                    action yes_action
                textbutton _("Нет"):
                    at mas_os_btn
                    action no_action


screen mas_os_bg():
    add store.mas_os.wallpaper_disp():
        xalign 0.5
        yalign 0.5
    if store.mas_os.flag("_mas_os_wp_dim", True):
        add Solid(store.mas_os.theme_color("bg_dim"))


screen mas_os_frame(title, subtitle=None):
    modal True
    zorder 200

    use mas_os_bg

    vbox at store.mas_os.t_pop(0.0):
        xpos 40
        ypos 28
        xsize 1200
        spacing 4

        text title:
            style "mas_os_title"

        if subtitle:
            text subtitle:
                style "mas_os_subtitle"

    fixed at store.mas_os.t_page():
        transclude

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_notice(message):
    modal True
    zorder 310

    add Solid("#000000B2") at mas_os_dim

    frame at store.mas_os.t_modal():
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
                    at mas_os_btn
                    action Function(store.mas_os.set_boot, "always")

                textbutton _("Игра"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (not shell_on)
                    at mas_os_btn
                    action Function(store.mas_os.set_boot, "skip")


screen mas_os_motion_toggle(width=388):
    $ zoom_on = store.mas_os.motion_zoom()
    $ half = int((width - 12) / 2)

    vbox:
        spacing 6
        xfill True

        text _("Появление окон"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("Снизу вверх"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (not zoom_on)
                    at mas_os_btn
                    action Function(store.mas_os.set_motion, "rise")

                textbutton _("Приближение"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected zoom_on
                    at mas_os_btn
                    action Function(store.mas_os.set_motion, "zoom")


screen mas_os_theme_toggle(width=388):
    $ light_on = store.mas_os.theme_light()
    $ half = int((width - 12) / 2)

    vbox:
        spacing 6
        xfill True

        text _("Тема MAS OS"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("Тёмная"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected (not light_on)
                    at mas_os_btn
                    action Function(store.mas_os.set_theme, "dark")

                textbutton _("Светлая"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected light_on
                    at mas_os_btn
                    action Function(store.mas_os.set_theme, "light")


screen mas_os_ibutton(caption, act, glyph, hue, bstyle="mas_os_tile", tstyle="mas_os_tile_text", align_center=True, delay=0, icon=None, badge=False):
    $ ipath = store.mas_os.icon_path(icon)

    button:
        style bstyle
        at store.mas_os.t_tile(delay)
        action act
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()

        hbox:
            spacing 10
            if align_center:
                xalign 0.5
            yalign 0.5
            xoffset (0 if align_center else 12)

            if ipath:
                add store.mas_os.fit_image(ipath, 32, 32):
                    yalign 0.5
            else:
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

        if badge:
            frame:
                xysize (12, 12)
                background Solid("#FF3B5C")
                xalign 1.0
                yalign 0.0
                xoffset -8
                yoffset 6


screen mas_os_home():
    modal True
    zorder 200

    $ snap = store.mas_os.aff_snapshot()
    $ ev_line = store.mas_os.next_event_line()
    $ ev_label = store.mas_os.events_button_label()
    $ ev_badge = store.mas_os.unread_event_count() > 0
    $ _aff_state = snap["state_s"]
    $ _aff_val = snap["value_s"]
    $ _aff_color = snap["color"]
    $ _launch_ic = store.mas_os.icon_path("launch")
    $ _aff_ic = store.mas_os.icon_path("affection")

    use mas_os_bg

    vbox at store.mas_os.t_pop(0.0):
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
        at store.mas_os.t_launch()
        xpos 56
        ypos 150
        default_focus True
        action If(
            store.mas_os.launch_anim_on(),
            Show("mas_os_launch_anim"),
            Return("launch"),
        )
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()

        hbox:
            xalign 0.5
            yalign 0.5
            spacing 12

            if _launch_ic:
                add store.mas_os.fit_image(_launch_ic, 40, 40):
                    yalign 0.5
            else:
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

    $ _aff_on = store.mas_os.flag("_mas_os_aff_widget", True)
    $ _mus_on = store.mas_os.flag("_mas_os_music_widget", True)
    $ _aff_y = 268 if _mus_on else 280
    $ _aff_h = 110 if _mus_on else 150
    $ _mus_y = 386 if _aff_on else 280
    $ _mus_h = 136 if _aff_on else 150
    $ _boot_y = 526 if (_aff_on and _mus_on) else 440

    if _aff_on:
        frame at store.mas_os.t_pop(0.10):
            style "mas_os_panel"
            xpos 56
            ypos _aff_y
            xsize 420
            ysize _aff_h
            padding (20, 12)

            vbox:
                spacing 4
                xfill True

                hbox:
                    spacing 8

                    if _aff_ic:
                        add store.mas_os.fit_image(_aff_ic, 22, 22):
                            yalign 0.5

                    text _("Моника"):
                        style "mas_os_hint"
                        yalign 0.5

                text _aff_state:
                    style "mas_os_stat_state"
                    color _aff_color

                text _("Привязанность: [_aff_val]"):
                    style "mas_os_body"

                if not _mus_on:
                    text ev_line:
                        style "mas_os_hint"

    if _mus_on:
        use mas_os_player_widget(width=420, height=_mus_h, ypos=_mus_y)

    frame at store.mas_os.t_pop(0.14):
        style "mas_os_panel"
        xpos 56
        ypos _boot_y
        xsize 420
        ysize 102
        padding (16, 10)

        use mas_os_boot_toggle

    grid 2 5:
        xpos 520
        ypos 140
        spacing 12

        use mas_os_ibutton(ev_label, Return("events"), "Сб", "#C94A7A", delay=0.08, icon="events", badge=ev_badge)
        use mas_os_ibutton(_("Документация"), Return("docs"), "Дк", "#7A4A9A", delay=0.11, icon="docs")
        use mas_os_ibutton(_("Подарки"), Return("gifts"), "Пд", "#E85A9A", delay=0.14, icon="gifts")
        use mas_os_ibutton(_("Файлы"), Return("files"), "Фл", "#5A6A9A", delay=0.17, icon="files")
        use mas_os_ibutton(_("Браузер"), Return("browser"), "Бр", "#4A8AAA", delay=0.20, icon="browser")
        use mas_os_ibutton(_("Данные"), Return("data"), "Дн", "#8A6A4A", delay=0.23, icon="data")
        use mas_os_ibutton(_("Настройки"), Return("settings"), "Нс", "#6A6A7A", delay=0.26, icon="settings")
        use mas_os_ibutton(_("Сабмоды"), Return("submods"), "См", "#4A8A6A", delay=0.29, icon="submods")
        use mas_os_ibutton(_("Склад"), Return("store"), "Ск", "#4A8AAA", delay=0.32, icon="updates")
        use mas_os_ibutton(_("Плеер"), Return("player"), "Au", "#8A6A4A", delay=0.35, icon="sound")

    hbox:
        xpos 56
        ypos 640
        spacing 12

        use mas_os_ibutton(_("О системе"), Return("about"), "i", "#7A4A9A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True, delay=0.32, icon="about")
        use mas_os_ibutton(_("Логи"), Return("logs"), "Lg", "#8A6A4A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True, delay=0.35, icon="logs")
        use mas_os_ibutton(_("Перезагрузка"), Function(store.mas_os.reboot_shell), "R", "#4A8AAA", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True, delay=0.38, icon="reboot")
        if store.mas_os.flag("_mas_os_quit_confirm", True):
            use mas_os_ibutton(_("Выключение"), Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm")), "X", "#8A3A4A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True, delay=0.41, icon="shutdown")
        else:
            use mas_os_ibutton(_("Выключение"), Function(store.mas_os.request_quit), "X", "#8A3A4A", bstyle="mas_os_nav_btn", tstyle="mas_os_nav_btn_text", align_center=True, delay=0.41, icon="shutdown")

    if store.mas_os.flag("_mas_os_quit_confirm", True):
        key "K_ESCAPE" action Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm"))
        key "K_AC_BACK" action Show("mas_os_confirm", message=_("Выключить MAS OS?"), yes_action=Function(store.mas_os.request_quit), no_action=Hide("mas_os_confirm"))
    else:
        key "K_ESCAPE" action Function(store.mas_os.request_quit)
        key "K_AC_BACK" action Function(store.mas_os.request_quit)


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

style mas_os_talk_btn_text:
    variant "small"
    size 13
    align (0.5, 0.5)
    text_align 0.5
    layout "subtitle"

style mas_os_talk_btn_text:
    variant "touch"
    size 13
    align (0.5, 0.5)
    text_align 0.5
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
