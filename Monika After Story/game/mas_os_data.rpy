# MAS OS data manager — persistent backups, restore, zip export.

init -5 python in mas_os:
    import os
    import shutil
    import datetime
    import zipfile
    import store

    data_selected = "persistent"
    data_status = ""

    def _save_folder():
        folder = save_dir()
        if folder and not folder.endswith("/") and not folder.endswith("\\"):
            return folder
        return folder

    def _cal_name_for(per_name):
        if per_name == "persistent":
            return "db.mcal"
        if per_name == "persistent_unstable":
            return None
        if per_name.startswith("persistent") and per_name.endswith(".bak"):
            mid = per_name[len("persistent"):-len(".bak")]
            return "db.mcal" + mid + ".bak"
        return None

    def _fmt_dt(value):
        if isinstance(value, datetime.datetime):
            return value.strftime("%d.%m.%Y %H:%M")
        if isinstance(value, datetime.date):
            return value.strftime("%d.%m.%Y")
        return "—"

    def _fmt_mtime(path):
        try:
            return datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%d.%m.%Y %H:%M")
        except Exception:
            return "—"

    def _fmt_play(td):
        try:
            secs = int(td.total_seconds())
        except Exception:
            return "—"
        hours = secs // 3600
        days = hours // 24
        hours = hours % 24
        if days:
            return "{0}д {1}ч".format(days, hours)
        return "{0}ч".format(hours)

    def _aff_from_per(per):
        raw = getattr(per, "_mas_affection_data", None)
        decode = getattr(store.mas_affection, "__decode_data", None)
        if raw is None or decode is None:
            return None
        try:
            unpacked = decode(raw)
        except Exception:
            return None
        if not unpacked:
            return None
        try:
            return float(unpacked[0])
        except Exception:
            return None

    def _meta_from_obj(per, path, name):
        sessions = getattr(per, "sessions", None) or {}
        aff = _aff_from_per(per)
        state_s = ""
        aff_s = "—"
        if aff is not None:
            aff_s = _fmt_aff(aff)
            state_s = AFF_STATE_NAMES.get(_aff_state_from_value(aff), "")
        player = getattr(per, "playername", None) or "—"
        nick = getattr(per, "_mas_monika_nickname", None) or "Моника"
        version = getattr(per, "version_number", None) or "—"
        first = sessions.get("first_session")
        last = sessions.get("last_session_end")
        total = sessions.get("total_sessions")
        play = sessions.get("total_playtime")
        return {
            "ok": True,
            "name": name,
            "path": path,
            "mtime": _fmt_mtime(path),
            "player": unicode(player),
            "nick": unicode(nick),
            "version": unicode(version),
            "aff_s": aff_s,
            "state_s": state_s,
            "sessions": unicode(total) if total is not None else "—",
            "play": _fmt_play(play) if play is not None else "—",
            "first": _fmt_dt(first),
            "last": _fmt_dt(last),
            "is_current": name == "persistent",
            "size": _fm_size(path),
            "cal": _cal_name_for(name),
        }

    def _fm_size(path):
        try:
            n = os.path.getsize(path)
        except Exception:
            return "?"
        if n < 1024:
            return "{0} B".format(n)
        return "{0:.1f} KB".format(n / 1024.0)

    def _meta_broken(path, name, err):
        return {
            "ok": False,
            "name": name,
            "path": path,
            "mtime": _fmt_mtime(path),
            "player": "—",
            "nick": "—",
            "version": "повреждён",
            "aff_s": "—",
            "state_s": "",
            "sessions": "—",
            "play": "—",
            "first": "—",
            "last": "—",
            "is_current": name == "persistent",
            "size": _fm_size(path),
            "cal": _cal_name_for(name),
            "error": unicode(err),
        }

    def list_persistents():
        folder = _save_folder()
        rows = []
        if not folder or not os.path.isdir(folder):
            return rows
        try:
            names = os.listdir(folder)
        except Exception:
            return rows

        def sort_key(name):
            if name == "persistent":
                return (0, 0)
            if name == "persistent_unstable":
                return (2, 0)
            if name.startswith("persistent") and name.endswith(".bak"):
                try:
                    return (1, -int(name[len("persistent"):-len(".bak")]))
                except Exception:
                    return (1, 0)
            return (3, name)

        picked = []
        for name in names:
            if name == "persistent" or name == "persistent_unstable":
                picked.append(name)
            elif name.startswith("persistent") and name.endswith(".bak"):
                picked.append(name)
        picked.sort(key=sort_key)

        for name in picked:
            path = os.path.join(folder, name)
            if name == "persistent":
                snap = aff_snapshot()
                sessions = store.persistent.sessions or {}
                rows.append({
                    "ok": True,
                    "name": name,
                    "path": path,
                    "mtime": _fmt_mtime(path),
                    "player": unicode(getattr(store.persistent, "playername", None) or "—"),
                    "nick": unicode(getattr(store.persistent, "_mas_monika_nickname", None) or "Моника"),
                    "version": unicode(getattr(store.persistent, "version_number", None) or store.config.version),
                    "aff_s": snap["value_s"],
                    "state_s": snap["state_s"],
                    "sessions": unicode(sessions.get("total_sessions", "—")),
                    "play": _fmt_play(sessions.get("total_playtime")) if sessions.get("total_playtime") is not None else "—",
                    "first": _fmt_dt(sessions.get("first_session")),
                    "last": _fmt_dt(sessions.get("last_session_end")),
                    "is_current": True,
                    "size": _fm_size(path),
                    "cal": "db.mcal",
                })
                continue
            try:
                ok, data = store.mas_per_check.tryper(path, get_data=True)
                if not ok:
                    rows.append(_meta_broken(path, name, "не прочитан"))
                else:
                    rows.append(_meta_from_obj(data, path, name))
            except Exception as err:
                rows.append(_meta_broken(path, name, err))
        return rows

    def data_selected_row():
        for row in list_persistents():
            if row["name"] == data_selected:
                return row
        rows = list_persistents()
        return rows[0] if rows else None

    def data_select(name):
        global data_selected, data_status
        data_selected = name
        data_status = ""

    def data_live_meta():
        snap = aff_snapshot()
        sessions = store.persistent.sessions or {}
        path = persistent_path()
        return {
            "ok": True,
            "name": "persistent",
            "path": path,
            "mtime": _fmt_mtime(path) if path and os.path.isfile(path) else "в памяти",
            "player": unicode(getattr(store.persistent, "playername", None) or "—"),
            "nick": unicode(getattr(store.persistent, "_mas_monika_nickname", None) or "Моника"),
            "version": unicode(getattr(store.persistent, "version_number", None) or store.config.version),
            "aff_s": snap["value_s"],
            "state_s": snap["state_s"],
            "sessions": unicode(sessions.get("total_sessions", "—")),
            "play": _fmt_play(sessions.get("total_playtime")) if sessions.get("total_playtime") is not None else "—",
            "first": _fmt_dt(sessions.get("first_session")),
            "last": _fmt_dt(sessions.get("last_session_end")),
            "is_current": True,
            "size": _fm_size(path) if path and os.path.isfile(path) else "—",
            "cal": "db.mcal",
        }

    def data_make_backup():
        global data_status
        if data_locked():
            data_status = "Нет доступа к папке сохранений."
            return False
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        try:
            store.__mas__memoryBackup()
            data_status = "Бэкап persistent и календаря создан. Файл лежит в папке сохранений — открыть его можно в «Файлах»."
            return True
        except Exception as err:
            data_status = "Бэкап не удался: {0}".format(err)
            return False

    def data_promote_path(src):
        """Copy a persistent* file over the live slot, then reboot. File-level only."""
        global data_status
        if data_locked():
            data_status = "Нет доступа к папке сохранений."
            return False
        folder = _save_folder()
        if not src or not os.path.isfile(src) or not folder:
            data_status = "Файл не найден."
            return False
        dst = os.path.join(folder, "persistent")
        try:
            if os.path.abspath(src) == os.path.abspath(dst):
                data_status = "Это уже текущий persistent."
                return False
            try:
                store.__mas__memoryBackup()
            except Exception:
                if os.path.isfile(dst):
                    shutil.copy2(dst, os.path.join(folder, "persistent_osprev.bak"))
            shutil.copy2(src, dst)
            name = os.path.basename(src)
            cal = _cal_name_for(name)
            if cal:
                cal_src = os.path.join(os.path.dirname(src), cal)
                cal_dst = os.path.join(folder, "db.mcal")
                if os.path.isfile(cal_src):
                    shutil.copy2(cal_src, cal_dst)
            data_status = "Файл подставлен. Перезапуск оболочки..."
            reboot_shell()
            return True
        except Exception as err:
            data_status = "Не подставить: {0}".format(err)
            return False

    def _safe_zip_name(text):
        text = unicode(text or "mas").strip() or "mas"
        out = []
        for ch in text:
            if ch.isalnum() or ch in "-_":
                out.append(ch)
            else:
                out.append("_")
        return "".join(out)[:24]

    def data_export_zip():
        global data_status
        if data_locked():
            data_status = "Нет доступа к папке сохранений."
            return False
        row = data_selected_row()
        if row is None or not os.path.isfile(row.get("path") or ""):
            live = persistent_path()
            if live and os.path.isfile(live):
                row = {"path": live, "name": "persistent", "player": getattr(store.persistent, "playername", None) or "mas", "nick": "Моника", "version": "", "aff_s": "", "state_s": "", "sessions": "", "play": "", "first": "", "mtime": ""}
            else:
                data_status = "Нечего экспортировать."
                return False
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_name = "mas_{0}_{1}.zip".format(_safe_zip_name(row.get("player")), stamp)
        folders = []
        export_dir = os.path.join(game_dir(), "mas_os_export")
        char_dir = characters_dir()
        folders.append(export_dir)
        if char_dir:
            folders.append(char_dir)
        info = (
            "MAS OS export\n"
            "file: {0}\n"
            "player: {1}\n"
            "monika: {2}\n"
            "version: {3}\n"
            "affection: {4} {5}\n"
            "sessions: {6}\n"
            "playtime: {7}\n"
            "first: {8}\n"
            "mtime: {9}\n"
        ).format(
            row["name"], row["player"], row["nick"], row["version"],
            row["aff_s"], row["state_s"], row["sessions"], row["play"],
            row["first"], row["mtime"]
        )
        try:
            last_path = None
            for folder in folders:
                if not os.path.isdir(folder):
                    os.makedirs(folder)
                zip_path = os.path.join(folder, zip_name)
                zf = zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED)
                try:
                    zf.write(row["path"], row["name"])
                    cal = row.get("cal")
                    if cal:
                        cal_path = os.path.join(_save_folder(), cal)
                        if os.path.isfile(cal_path):
                            zf.write(cal_path, cal)
                    zf.writestr("mas_os_info.txt", info.encode("utf-8"))
                finally:
                    zf.close()
                last_path = zip_path
            data_status = "ZIP: mas_os_export/ и characters/{0}".format(zip_name)
            return True
        except Exception as err:
            data_status = "Экспорт не удался: {0}".format(err)
            return False

    def data_go_files():
        global fm_keep_cwd
        try:
            fm_jump("saves")
            fm_keep_cwd = True
        except Exception:
            pass
        return "files"


init python:
    class MASOSDataFiles(Action):
        def __call__(self):
            store.mas_os.data_go_files()
            if store.mas_os.layout_desktop():
                store.mas_os.wm_open("files", reset_fm=False)
                store.renpy.restart_interaction()
                return None
            return "files"


label mas_os_data:
    $ store.mas_os.data_status = ""
    if not store.mas_os.data_selected:
        $ store.mas_os.data_selected = "persistent"
    call screen mas_os_data with mas_os_trans
    if _return == "files":
        jump mas_os_files
    jump mas_os_home


screen mas_os_data():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ locked = store.mas_os.data_locked()
    $ live = store.mas_os.data_live_meta()
    $ rows = [] if locked else store.mas_os.list_persistents()
    $ sel = None if locked else store.mas_os.data_selected_row()
    $ status = store.mas_os.data_status
    $ loc = store.mas_os.saves_folder_display()
    $ mode = store.mas_os.android_saves_mode_label()
    $ gray = store.mas_os.theme_color("insensitive")
    $ sel_name = sel["name"] if sel else ""
    $ card = sel if (sel and not sel.get("is_current")) else live
    $ card_title = card["name"] if (card and not card.get("is_current")) else _("Сейчас в памяти")
    $ d_nick = _("Моника: ") + card["nick"]
    $ d_player = _("Игрок: ") + card["player"]
    $ d_ver = _("Версия: ") + card["version"]
    $ d_aff = _("Привязанность: ") + card["aff_s"] + "  " + card["state_s"]
    $ d_ses = _("Сессии: ") + card["sessions"] + "  /  " + card["play"]
    $ d_first = _("Первая: ") + card["first"]
    $ d_last = _("Последняя: ") + card["last"]

    use mas_os_bg

    text _("Данные") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 14

    text _("Сейчас: [mode]"):
        style "mas_os_hint"
        xpos 48
        ypos 52
        xsize 1180
        substitute True

    frame:
        style "mas_os_panel"
        xpos 48
        ypos 82
        xysize (760, 430)
        padding (12, 10)
        background Solid(store.mas_os.theme_color("panel2") if not locked else "#1A1A1A")

        if locked:
            timer 0.5 action MASOSFn(store.mas_os.android_saves_poll) repeat True

            vbox:
                spacing 10
                xfill True

                text _("Папка сохранений недоступна"):
                    style "mas_os_subtitle"
                    color gray

                text _("Выбраны Documents, но нет разрешения «доступ ко всем файлам». Список файлов и операции с диском выключены. Ниже — только текущий persistent из памяти."):
                    style "mas_os_body"
                    color gray
                    xsize 720

                textbutton _("Открыть настройки разрешения"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize 720
                    action Function(store.mas_os.android_saves_open_settings)

                textbutton _("Проверить разрешение"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 720
                    action MASOSFn(store.mas_os.android_saves_finish_documents)

                textbutton _("Вернуть папку приложения"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 720
                    action Function(store.mas_os.android_saves_choose_app)
        else:
            viewport:
                xysize (736, 410)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 4

                    text _("Файлы в папке сохранений (просмотр). Подменить текущий persistent можно только в «Файлах»: копируй bak и «Сделать текущим», затем перезапуск."):
                        style "mas_os_hint"
                        xsize 700

                    if not rows:
                        text _("Файлов persistent не видно."):
                            style "mas_os_body"
                    else:
                        for row in rows:
                            textbutton "{0}   {1}   {2}   {3}".format(row["name"], row["mtime"], row["player"], row["aff_s"]):
                                style "mas_os_side_btn"
                                text_style "mas_os_side_btn_text"
                                xsize 700
                                ysize 48
                                substitute False
                                selected (row["name"] == sel_name)
                                action Function(store.mas_os.data_select, row["name"])

    frame:
        style "mas_os_panel"
        xpos 828
        ypos 82
        xysize (404, 430)
        padding (16, 14)

        vbox:
            spacing 6
            xfill True

            text card_title:
                style "mas_os_subtitle"
                substitute False

            text d_nick:
                style "mas_os_body"
                size 16
                substitute False

            text d_player:
                style "mas_os_body"
                size 16
                substitute False

            text d_ver:
                style "mas_os_body"
                size 16
                substitute False

            text d_aff:
                style "mas_os_body"
                size 16
                substitute False

            text d_ses:
                style "mas_os_body"
                size 16
                substitute False

            text d_first:
                style "mas_os_hint"
                substitute False

            text d_last:
                style "mas_os_hint"
                substitute False

            text loc:
                style "mas_os_hint"
                size 13
                substitute False

            if locked:
                text _("Это снимок из памяти. Файлы на диске не читаем."):
                    style "mas_os_hint"
                    color gray

    vbox:
        xpos 48
        ypos 522
        spacing 8

        hbox:
            spacing 8

            textbutton _("Создать бэкап"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 200
                sensitive (not locked)
                action MASOSFn(store.mas_os.data_make_backup)

            textbutton _("Экспорт ZIP"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 180
                sensitive (not locked)
                action MASOSFn(store.mas_os.data_export_zip)

            textbutton _("Открыть в файлах"):
                style "mas_os_button"
                text_style "mas_os_button_text"
                xsize 220
                sensitive (not locked)
                action MASOSDataFiles()

            textbutton _("Перезапустить оболочку"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 260
                action Show(
                    "mas_os_confirm",
                    message=_("Перезапустить MAS OS? Нужно после подмены persistent в файловом менеджере."),
                    yes_action=[Function(store.mas_os.reboot_shell), Hide("mas_os_confirm")],
                    no_action=Hide("mas_os_confirm")
                )

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 48
            ypos 612
            xsize 1180
            substitute False

    if not store.mas_os.wm_embedded():
        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 48
            ypos 640
            action Return("back")

        key "K_ESCAPE" action Return("back")
        key "K_AC_BACK" action Return("back")
