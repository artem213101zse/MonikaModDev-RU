# -*- coding: utf-8 -*-
# Машинные настройки MAS OS и смена persistent после рестарта.
# Prefs лежат рядом с сейвами (не внутри persistent), чтобы смена слота
# не откатывала тему, шрифты и TOS.

init -20 python in mas_os:
    import os
    import json
    import shutil
    import datetime
    import sys
    import store

    # Имена файлов в папке сейвов. Их читает и патч SDK до persistent.init().
    PREFS_FILE = "mas_os_prefs.json"
    NOTIFY_FILE = "mas_os_notify.json"
    SLOT_FLAG = ".mas_os_next_slot"
    FROM_SLOT_FLAG = ".mas_os_prefs_from_slot"

    # Ключи оболочки, которые живут «на устройстве», не у конкретной Моники.
    PREFS_KEYS = (
        "_mas_os_boot",
        "_mas_os_motion",
        "_mas_os_launch_anim",
        "_mas_os_sfx",
        "_mas_os_stagger",
        "_mas_os_talk_btn",
        "_mas_os_menu_btn",
        "_mas_os_aff_widget",
        "_mas_os_music_widget",
        "_mas_os_music_autoplay",
        "_mas_os_music_loop",
        "_mas_os_music_shuffle",
        "_mas_os_return_confirm",
        "_mas_os_quit_confirm",
        "_mas_os_textbox",
        "_mas_os_tb_tint_on",
        "_mas_os_tb_tint",
        "_mas_os_tb_strength",
        "_mas_os_ui_match",
        "_mas_os_font",
        "_mas_os_font_menu",
        "_mas_os_font_ui",
        "_mas_os_font_notes",
        "_mas_os_wallpaper",
        "_mas_os_wp_dim",
        "_mas_os_theme",
        "_mas_os_layout",
        "_mas_os_setup_done",
        "_mas_os_tos_agreed",
        "_mas_os_android_saves",
        "_mas_os_intro_skip",
        "_mas_os_boot_splash",
        "_mas_os_catalog_url",
    )

    notify_open = False
    notify_items = []
    data_prefs_from_slot = False

    def _prefs_dir():
        try:
            folder = save_dir()
        except Exception:
            folder = getattr(store.renpy.config, "savedir", None)
        return folder or ""

    def _prefs_path():
        folder = _prefs_dir()
        if not folder:
            return None
        return os.path.join(folder, PREFS_FILE)

    def _notify_path():
        folder = _prefs_dir()
        if not folder:
            return None
        return os.path.join(folder, NOTIFY_FILE)

    def _json_write(path, payload):
        if not path:
            return False
        folder = os.path.dirname(path)
        try:
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
        except Exception:
            pass
        try:
            raw = json.dumps(payload, ensure_ascii=True, indent=2)
            handle = open(path, "wb")
            try:
                handle.write(raw)
            finally:
                handle.close()
            return True
        except Exception:
            return False

    def _json_read(path, fallback):
        if not path or not os.path.isfile(path):
            return fallback
        try:
            handle = open(path, "rb")
            try:
                raw = handle.read()
            finally:
                handle.close()
            data = json.loads(raw)
            if data is None:
                return fallback
            return data
        except Exception:
            return fallback

    def prefs_save():
        """Снимок текущих настроек OS на диск (не в persistent)."""
        persistent = store.persistent
        blob = {}
        for key in PREFS_KEYS:
            try:
                blob[key] = getattr(persistent, key)
            except Exception:
                pass
        return _json_write(_prefs_path(), blob)

    def prefs_overlay():
        """Наложить машинные prefs на уже загруженный persistent."""
        blob = _json_read(_prefs_path(), None)
        if not isinstance(blob, dict):
            return False
        persistent = store.persistent
        for key in PREFS_KEYS:
            if key not in blob:
                continue
            try:
                setattr(persistent, key, blob[key])
            except Exception:
                pass
        return True

    def prefs_boot():
        """
        Старт после загрузки слота.
        Флаг from_slot: взять вид OS из этого сейва и запомнить.
        Иначе: вернуть машинный вид поверх слота.
        """
        folder = _prefs_dir()
        from_slot = False
        if folder:
            flag = os.path.join(folder, FROM_SLOT_FLAG)
            if os.path.isfile(flag):
                from_slot = True
                try:
                    os.unlink(flag)
                except Exception:
                    pass
        if from_slot:
            prefs_save()
        else:
            prefs_overlay()
        notify_load()
        return None

    def os_persist():
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        prefs_save()

    def _cal_name(per_name):
        if per_name == "persistent":
            return "db.mcal"
        if per_name == "persistent_unstable":
            return None
        if per_name.startswith("persistent") and per_name.endswith(".bak"):
            mid = per_name[len("persistent"):-len(".bak")]
            return "db.mcal" + mid + ".bak"
        return None

    def _safe_slot_name(name):
        name = os.path.basename(name or "")
        if not name or name in (".", ".."):
            return None
        if "/" in name or "\\" in name or ":" in name:
            return None
        return name

    def slot_copy_now(name):
        """Запасной путь без патча SDK: копируем файл сами, потом рестарт."""
        name = _safe_slot_name(name)
        folder = _prefs_dir()
        if not name or not folder:
            return False
        src = os.path.join(folder, name)
        dst = os.path.join(folder, "persistent")
        if not os.path.isfile(src):
            return False
        try:
            if os.path.abspath(src) != os.path.abspath(dst) and os.path.isfile(dst):
                shutil.copy2(dst, os.path.join(folder, "persistent_osprev.bak"))
            if os.path.abspath(src) != os.path.abspath(dst):
                shutil.copy2(src, dst)
            cal = _cal_name(name)
            if cal:
                cal_src = os.path.join(folder, cal)
                cal_dst = os.path.join(folder, "db.mcal")
                if os.path.isfile(cal_src):
                    shutil.copy2(cal_src, cal_dst)
            return True
        except Exception:
            return False

    def schedule_persistent_slot(name, prefs_from_slot=False):
        """
        Выбранный persistent применится после utter_restart.
        Патч SDK копирует файл до persistent.init(); без патча копируем здесь.
        """
        global data_status
        name = _safe_slot_name(name)
        folder = _prefs_dir()
        if not name or not folder:
            data_status = "Нечего загружать."
            return False
        src = os.path.join(folder, name)
        if not os.path.isfile(src):
            data_status = "Файл не найден."
            return False
        if name == "persistent":
            data_status = "Это уже текущий persistent."
            return False
        if not prefs_from_slot:
            prefs_save()
        try:
            handle = open(os.path.join(folder, SLOT_FLAG), "wb")
            try:
                handle.write(name)
            finally:
                handle.close()
        except Exception as err:
            data_status = "Не записать флаг слота: {0}".format(err)
            return False
        if prefs_from_slot:
            try:
                open(os.path.join(folder, FROM_SLOT_FLAG), "wb").close()
            except Exception:
                pass
        main = sys.modules.get("__main__")
        if not (main and hasattr(main, "mas_os_boot_prepare")):
            if not slot_copy_now(name):
                data_status = "Не скопировать persistent."
                return False
            try:
                os.unlink(os.path.join(folder, SLOT_FLAG))
            except Exception:
                pass
        data_status = "Слот назначен. Перезапуск..."
        reboot_shell()
        return True

    def notify_load():
        global notify_items
        data = _json_read(_notify_path(), [])
        if not isinstance(data, list):
            data = []
        notify_items = data[-40:]
        return None

    def notify_save():
        return _json_write(_notify_path(), notify_items[-40:])

    def notify_add(title, body, source="browser"):
        global notify_items
        try:
            stamp = datetime.datetime.now().strftime("%d.%m %H:%M")
        except Exception:
            stamp = ""
        notify_items.append({
            "title": unicode(title or "Моника"),
            "body": unicode(body or ""),
            "time": stamp,
            "source": unicode(source or "browser"),
        })
        notify_items = notify_items[-40:]
        notify_save()
        return None

    def notify_clear():
        global notify_items
        notify_items = []
        notify_save()
        return None

    def notify_count():
        return len(notify_items)

    def toggle_notify():
        global notify_open, start_open
        notify_open = not notify_open
        start_open = False
        return None

    def set_notify_open(value):
        global notify_open
        notify_open = bool(value)
        return None

    def toggle_prefs_from_slot():
        global data_prefs_from_slot
        data_prefs_from_slot = not data_prefs_from_slot
        return None


init -19 python in mas_os:
    # Сразу после persistent: вернуть машинный вид OS (или запомнить вид слота).
    try:
        prefs_boot()
    except Exception:
        pass
