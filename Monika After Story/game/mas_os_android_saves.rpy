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
            return "нужен доступ ко всем файлам"
        return "папка приложения"

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

    def data_locked():
        """Documents picked, all-files not granted — file ops stay grey."""
        if not android_saves_available():
            return False
        return bool(android_saves_wait_permission())


screen mas_os_saves_picker(in_setup=False):
    $ st = store.mas_os.android_saves_status()
    $ path = st.get("path") or "Documents/Monika_after_story"
    $ wait = store.mas_os.android_saves_wait_permission()
    $ folder = store.mas_os.saves_folder_display()
    $ wide = 1080 if in_setup else 700
    $ android = st.get("android")
    $ using_docs = st.get("using") == "documents" and st.get("active")
    $ choice = getattr(store.persistent, "_mas_os_android_saves", "ask") or "ask"

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

            text _("Копировать, подменять и удалять файлы — в «Данные» и «Файлы». Текущий persistent изнутри игры не трогаем: подставить другой файл можно только через файловый менеджер, затем перезапуск оболочки."):
                style "mas_os_hint"
                xsize wide

        elif wait:
            if st.get("allowed"):
                text _("Разрешение получено"):
                    style "mas_os_subtitle"

                text _("Доступ ко всем файлам есть. Нажми «Продолжить» — игра подхватит старые сейвы в Documents и перезапустится."):
                    style "mas_os_body"
                    xsize wide

                textbutton _("Продолжить"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize wide
                    action MASOSFn(store.mas_os.android_saves_finish_documents)
            else:
                text _("Нужен доступ к файлам"):
                    style "mas_os_subtitle"

                text _("Чтобы сейвы в Documents переживали переустановку, Android требует «доступ ко всем файлам». Без него игра останется в папке приложения и не будет трогать старые слоты."):
                    style "mas_os_body"
                    xsize wide

                text _("Нажми кнопку ниже. В списке найди это приложение и включи доступ. Потом вернись сюда — проверка идёт сама, либо нажми «Проверить»."):
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

            if in_setup:
                textbutton _("Оставить папку приложения"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize wide
                    action Function(store.mas_os.android_saves_choose_app)
            else:
                textbutton _("Отмена, папка приложения"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize wide
                    action [Function(store.mas_os.android_saves_choose_app), Return("app")]

        elif using_docs:
            text _("Сейвы в Documents"):
                style "mas_os_subtitle"

            text path:
                style "mas_os_hint"
                xsize wide
                substitute False

            text _("Папка видна в файловом менеджере телефона. Старые слоты подхватываются после переустановки, пока выдан доступ ко всем файлам."):
                style "mas_os_body"
                xsize wide

            textbutton _("Вернуть папку приложения"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize wide
                action Function(store.mas_os.android_saves_choose_app)

        else:
            text _("Где хранить сохранения"):
                style "mas_os_subtitle"

            text _("«В Documents» кладёт сейвы в:\n[path]\nПапка видна в файловом менеджере. На Android 11+ система попросит доступ ко всем файлам — без него после переустановки старые сейвы не подхватятся. Это не сбор данных."):
                style "mas_os_hint"
                xsize wide
                substitute True

            text _("«Папка приложения» — скрытая папка, как у стокового Ren'Py. После удаления приложения эти сейвы пропадут."):
                style "mas_os_hint"
                xsize wide

            textbutton _("Сохранять в Documents"):
                style "mas_os_button"
                text_style "mas_os_button_text"
                xsize wide
                action Function(store.mas_os.android_saves_choose_documents)

            if in_setup:
                textbutton _("Папка приложения"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize wide
                    action Function(store.mas_os.android_saves_choose_app)
            else:
                textbutton _("Оставить как обычно"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize wide
                    action [Function(store.mas_os.android_saves_choose_app), Return("app")]

            if choice == "app":
                text _("Выбрана папка приложения. Можно идти дальше."):
                    style "mas_os_body"
                    xsize wide


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

        use mas_os_saves_picker(in_setup=False)


screen mas_os_android_saves_row():
    $ st = store.mas_os.android_saves_status()
    $ mode = store.mas_os.android_saves_mode_label()
    $ android = st.get("android")

    text _("Сохранения"):
        style "mas_os_subtitle"

    text _("Сейчас: [mode]"):
        style "mas_os_body"
        substitute True

    if android:
        text _("Documents переживает переустановку только с разрешением «доступ ко всем файлам»."):
            style "mas_os_hint"

        textbutton _("Сохранять в Documents"):
            style "mas_os_button"
            text_style "mas_os_button_text"
            xsize 760
            action Show("mas_os_android_saves")

        if store.mas_os.android_saves_wait_permission():
            textbutton _("Открыть настройки разрешения"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 760
                action Function(store.mas_os.android_saves_open_settings)

        textbutton _("Оставить папку приложения"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 760
            action Function(store.mas_os.android_saves_choose_app)
    else:
        text _("На ПК сейвы уже в видимой папке. Подмена файлов — через «Данные» и «Файлы»."):
            style "mas_os_hint"
