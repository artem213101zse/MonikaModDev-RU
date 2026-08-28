# Android save-folder choice. Engine helpers live on __main__ (patched SDK).
# Default = app folder. Documents only after All files access is granted.

default persistent._mas_os_android_saves = "ask"

init -5 python in mas_os:
    import os
    import sys
    import store

    def _android_main():
        try:
            return sys.modules.get("__main__")
        except Exception:
            return None

    def android_saves_available():
        main = _android_main()
        return bool(main and getattr(store.renpy, "android", False) and hasattr(main, "mas_android_saves_status"))

    def android_saves_status():
        main = _android_main()
        if main and hasattr(main, "mas_android_saves_status"):
            try:
                return main.mas_android_saves_status()
            except Exception:
                pass
        android = bool(getattr(store.renpy, "android", False))
        return {
            "android": android,
            "wanted": False,
            "allowed": False,
            "active": False,
            "path": None,
            "using": "app",
        }

    def android_saves_should_ask():
        if not android_saves_available():
            return False
        st = android_saves_status()
        if not st.get("android"):
            return False
        if st.get("allowed") and st.get("using") == "documents":
            return False
        choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"
        if choice == "app":
            return False
        return True

    def android_saves_wait_permission():
        # Stay on the wait panel until Documents is actually active.
        # All-files granted is not enough: the engine flag is set only
        # after finish(), and the chooser must not come back in between.
        choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"
        if choice != "documents":
            return False
        st = android_saves_status()
        return not (st.get("using") == "documents" and st.get("active"))

    def android_saves_choose_app():
        store.persistent._mas_os_android_saves = "app"
        try:
            os_persist()
        except Exception:
            try:
                store.renpy.save_persistent()
            except Exception:
                pass
        st = android_saves_status()
        was_docs = st.get("using") == "documents"
        main = _android_main()
        if main and hasattr(main, "mas_android_saves_disable"):
            try:
                main.mas_android_saves_disable()
            except Exception:
                pass
        if was_docs:
            try:
                store.renpy.utter_restart()
            except Exception:
                pass
            return True
        return None

    def android_saves_choose_documents():
        store.persistent._mas_os_android_saves = "documents"
        try:
            os_persist()
        except Exception:
            try:
                store.renpy.save_persistent()
            except Exception:
                pass
        st = android_saves_status()
        if st.get("allowed"):
            if android_saves_finish_documents():
                return True
        android_saves_open_settings()
        return None

    def android_saves_open_settings():
        main = _android_main()
        if main and hasattr(main, "mas_android_open_all_files_settings"):
            try:
                return bool(main.mas_android_open_all_files_settings())
            except Exception:
                pass
        return False

    def android_saves_finish_documents():
        main = _android_main()
        info = {}
        if main and hasattr(main, "mas_android_saves_try_finish"):
            try:
                info = main.mas_android_saves_try_finish() or {}
            except Exception:
                info = {}
        elif main and hasattr(main, "mas_android_saves_enable"):
            try:
                info = main.mas_android_saves_enable() or {}
            except Exception:
                info = {}
        if info.get("restart") and not info.get("need_permission"):
            try:
                store.renpy.utter_restart()
            except Exception:
                pass
            return True
        return False

    def android_saves_poll():
        st = android_saves_status()
        if st.get("allowed"):
            android_saves_finish_documents()
        return None

    def android_saves_mode_label():
        st = android_saves_status()
        if not st.get("android"):
            return saves_folder_display()
        if st.get("using") == "documents" and st.get("allowed"):
            path = st.get("path") or "Documents/Monika_after_story"
            return path
        if (getattr(store.persistent, "_mas_os_android_saves", "ask") == "documents") and not st.get("allowed"):
            return "Documents — нужен доступ ко всем файлам"
        return "папка приложения (риск потери)"

    def saves_folder_display():
        st = android_saves_status()
        if st.get("using") == "documents" and st.get("path"):
            return st.get("path")
        try:
            return store.mas_os.save_dir() or "—"
        except Exception:
            return st.get("path") or "—"

    def android_saves_choice_resolved():
        if not android_saves_available():
            return True
        st = android_saves_status()
        if not st.get("android"):
            return True
        choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"
        if choice == "app":
            return True
        if choice == "documents" and st.get("using") == "documents" and st.get("active"):
            return True
        return False

    def saves_docs_selected():
        choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"
        if choice == "documents":
            return True
        st = android_saves_status()
        return bool(st.get("using") == "documents" and st.get("active"))

    def using_documents():
        st = android_saves_status()
        return bool(st.get("using") == "documents" and st.get("active"))

    def app_folder_risky():
        """True on Android when live user data is still the hidden app folder."""
        if not getattr(store.renpy, "android", False):
            return False
        if using_documents():
            return False
        if android_saves_wait_permission():
            return False
        return True

    def app_folder_warn_title():
        return "Папка приложения — данные легко потерять"

    def app_folder_warn_body():
        return (
            "Сейвы, подарки, музыка и партии лежат в скрытой папке приложения. "
            "Удалил игру, почистил данные или сменил телефон — всё пропадёт. "
            "Documents это переживает и видно в файловом менеджере."
        )

    def data_locked():
        """Documents picked, all-files not granted — file ops stay grey."""
        if not android_saves_available():
            return False
        return bool(android_saves_wait_permission())


screen mas_os_saves_toggle(width=700, in_setup=False):
    $ docs_on = store.mas_os.saves_docs_selected()
    $ half = int((width - 12) / 2)
    $ using_docs = store.mas_os.using_documents()
    $ app_on = (not docs_on) and ((getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask") == "app")

    vbox:
        spacing 6
        xfill True

        text _("Где хранить данные"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("Documents"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected docs_on
                    at mas_os_btn
                    action Function(store.mas_os.android_saves_choose_documents)

                textbutton _("Приложение"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize half
                    selected app_on
                    at mas_os_btn
                    if using_docs:
                        action Show(
                            "mas_os_confirm",
                            message=_("Вернуть скрытую папку приложения?\nНовые сейвы, подарки и музыка не переживут удаление игры. Файлы, уже лежащие в Documents, на диске останутся."),
                            yes_action=[
                                Function(store.mas_os.android_saves_choose_app),
                                Hide("mas_os_confirm"),
                            ],
                            no_action=Hide("mas_os_confirm"),
                        )
                    elif in_setup:
                        action Function(store.mas_os.android_saves_choose_app)
                    else:
                        action [
                            Function(store.mas_os.android_saves_choose_app),
                            Return("app"),
                        ]


screen mas_os_saves_picker(in_setup=False):
    $ st = store.mas_os.android_saves_status()
    $ path = st.get("path") or "Documents/Monika_after_story"
    $ wait = store.mas_os.android_saves_wait_permission()
    $ folder = store.mas_os.saves_folder_display()
    $ wide = 1080 if in_setup else 700
    $ android = st.get("android")
    $ using_docs = store.mas_os.using_documents()
    $ choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"
    $ warn_c = store.mas_os.theme_color("warn")
    $ warn_t = store.mas_os.theme_color("warn_title")
    $ warn_b = store.mas_os.theme_color("warn_text")

    if wait:
        timer 0.4 action Function(store.mas_os.android_saves_poll) repeat True

    vbox:
        spacing 12
        xfill True

        if not android:
            text _("Папка сохранений"):
                style "mas_os_subtitle"

            text _("На компьютере разрешение не нужно. Сейвы лежат здесь и остаются после переустановки игры:"):
                style "mas_os_body"
                xsize wide

            text folder:
                style "mas_os_hint"
                xsize wide
                substitute False

            text _("Копировать, подменять и удалять файлы — в «Данные» и «Файлы»."):
                style "mas_os_hint"
                xsize wide

        else:
            use mas_os_saves_toggle(width=wide, in_setup=in_setup)

            text _("Documents — папка видна в файловом менеджере, переживает переустановку. Рекомендуем её."):
                style "mas_os_hint"
                xsize wide

            if wait:
                if st.get("allowed"):
                    text _("Разрешение получено"):
                        style "mas_os_subtitle"

                    text _("Доступ ко всем файлам есть. Нажми «Продолжить» — игра подхватит Documents и перезапустится."):
                        style "mas_os_body"
                        xsize wide

                    textbutton _("Продолжить"):
                        style "mas_os_button"
                        text_style "mas_os_button_text"
                        xsize wide
                        action MASOSFn(store.mas_os.android_saves_finish_documents)
                else:
                    text _("Нужен доступ ко всем файлам"):
                        style "mas_os_subtitle"

                    text _("Android 11+ не пускает в Documents без этого разрешения. Это не сбор данных: без него сейвы останутся в скрытой папке приложения и пропадут при удалении."):
                        style "mas_os_body"
                        xsize wide

                    text _("Открой настройки, найди это приложение и включи доступ. Потом вернись — проверка идёт сама."):
                        style "mas_os_hint"
                        xsize wide

                    textbutton _("Открыть настройки разрешения"):
                        style "mas_os_button"
                        text_style "mas_os_button_text"
                        xsize wide
                        action Function(store.mas_os.android_saves_open_settings)

                    textbutton _("Проверить и продолжить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize wide
                        action MASOSFn(store.mas_os.android_saves_finish_documents)

            elif using_docs:
                text _("Сейвы в Documents"):
                    style "mas_os_subtitle"

                text path:
                    style "mas_os_hint"
                    xsize wide
                    substitute False

                text _("characters, custom_bgm, chess_games и log тоже здесь. Папка переживает переустановку, пока выдан доступ ко всем файлам."):
                    style "mas_os_body"
                    xsize wide

            else:
                frame:
                    background Solid(warn_c)
                    xsize wide
                    padding (14, 12)

                    vbox:
                        spacing 6
                        xfill True

                        text _("Папка приложения — плохой выбор"):
                            style "mas_os_subtitle"
                            color warn_t

                        text _("Скрытая папка Android. Удалил игру, почистил данные или сменил телефон — сейвы, подарки и своя музыка исчезнут. Documents это переживает."):
                            style "mas_os_body"
                            color warn_b
                            xsize (wide - 28)

                if choice == "ask":
                    text _("Выбери сторону тумблера, чтобы идти дальше. Documents — безопасный вариант."):
                        style "mas_os_hint"
                        xsize wide
                else:
                    text _("Можно идти дальше, но лучше переключиться на Documents."):
                        style "mas_os_hint"
                        xsize wide


screen mas_os_app_folder_warn(xpos=48, ypos=16, xsize=820):
    if store.mas_os.app_folder_risky():
        $ warn_c = store.mas_os.theme_color("warn")
        $ warn_t = store.mas_os.theme_color("warn_title")
        $ warn_b = store.mas_os.theme_color("warn_text")

        frame:
            xpos xpos
            ypos ypos
            xsize xsize
            background Solid(warn_c)
            padding (12, 8)

            hbox:
                spacing 10
                yalign 0.5
                xfill True

                vbox:
                    spacing 2
                    xsize (xsize - 220)

                    text _("Папка приложения: данные пропадут при удалении игры"):
                        style "mas_os_subtitle"
                        size 15
                        color warn_t

                    text _("Лучше Documents — сейвы, подарки и музыка переживут переустановку."):
                        style "mas_os_hint"
                        size 13
                        color warn_b
                        xsize (xsize - 228)

                textbutton _("Documents"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize 180
                    yalign 0.5
                    action Function(store.mas_os.android_saves_choose_documents)


screen mas_os_android_saves():
    modal True
    zorder 320

    add Solid("#000000B2")

    frame:
        style "mas_os_panel"
        xalign 0.5
        yalign 0.5
        xsize 760
        padding (28, 24)

        vbox:
            spacing 12
            xfill True

            use mas_os_saves_picker(in_setup=False)

            textbutton _("Закрыть"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 700
                action Return("close")


screen mas_os_android_saves_row():
    $ st = store.mas_os.android_saves_status()
    $ mode = store.mas_os.android_saves_mode_label()
    $ android = st.get("android")
    $ wait = store.mas_os.android_saves_wait_permission()

    text _("Сохранения"):
        style "mas_os_subtitle"

    text _("Сейчас: [mode]"):
        style "mas_os_body"
        substitute True

    if android:
        if wait:
            timer 0.4 action Function(store.mas_os.android_saves_poll) repeat True

        use mas_os_saves_toggle(width=760, in_setup=True)

        if wait:
            text _("Documents выбран, но нет доступа ко всем файлам. Без него игра не сможет писать в эту папку."):
                style "mas_os_hint"

            textbutton _("Открыть настройки разрешения"):
                style "mas_os_button"
                text_style "mas_os_button_text"
                xsize 760
                action Function(store.mas_os.android_saves_open_settings)

            textbutton _("Проверить разрешение"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 760
                action MASOSFn(store.mas_os.android_saves_finish_documents)
        elif store.mas_os.app_folder_risky():
            $ warn_c = store.mas_os.theme_color("warn")
            $ warn_t = store.mas_os.theme_color("warn_title")
            $ warn_b = store.mas_os.theme_color("warn_text")

            frame:
                background Solid(warn_c)
                xsize 760
                padding (14, 10)

                vbox:
                    spacing 4
                    xfill True

                    text _(store.mas_os.app_folder_warn_title()):
                        style "mas_os_subtitle"
                        size 16
                        color warn_t

                    text _(store.mas_os.app_folder_warn_body()):
                        style "mas_os_hint"
                        color warn_b
                        xsize 720
        else:
            text _("Documents переживает переустановку. characters, custom_bgm и log лежат рядом с сейвами."):
                style "mas_os_hint"
    else:
        text _("На ПК сейвы уже в видимой папке. Подмена файлов — через «Данные» и «Файлы»."):
            style "mas_os_hint"
