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

    def data_make_backup():
        global data_status
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        try:
            store.__mas__memoryBackup()
            data_status = "Бэкап persistent и календаря создан."
            return True
        except Exception as err:
            data_status = "Бэкап не удался: {0}".format(err)
            return False

    def data_restore():
        global data_status
        row = data_selected_row()
        if row is None:
            data_status = "Нечего загружать."
            return False
        if row["is_current"]:
            data_status = "Это уже текущий persistent."
            return False
        if not row["ok"]:
            data_status = "Этот файл повреждён, загружать нельзя."
            return False
        folder = _save_folder()
        src = row["path"]
        dst = os.path.join(folder, "persistent")
        try:
            try:
                store.__mas__memoryBackup()
            except Exception:
                if os.path.isfile(dst):
                    shutil.copy2(dst, os.path.join(folder, "persistent_osprev.bak"))
            shutil.copy2(src, dst)
            cal = row.get("cal")
            if cal:
                cal_src = os.path.join(folder, cal)
                cal_dst = os.path.join(folder, "db.mcal")
                if os.path.isfile(cal_src):
                    shutil.copy2(cal_src, cal_dst)
            data_status = "Подставлено. Перезапуск..."
            reboot_shell()
            return True
        except Exception as err:
            data_status = "Не загрузить: {0}".format(err)
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
        row = data_selected_row()
        if row is None or not os.path.isfile(row["path"]):
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

    def data_delete_bak():
        global data_status, data_selected
        row = data_selected_row()
        if row is None:
            data_status = "Нечего удалять."
            return False
        if row["is_current"] or row["name"] == "persistent":
            data_status = "Текущий persistent удалять нельзя."
            return False
        try:
            os.remove(row["path"])
            cal = row.get("cal")
            if cal:
                cal_path = os.path.join(_save_folder(), cal)
                if os.path.isfile(cal_path):
                    os.remove(cal_path)
            data_selected = "persistent"
            data_status = "Удалено: {0}".format(row["name"])
            return True
        except Exception as err:
            data_status = "Не удалить: {0}".format(err)
            return False

    def list_import_zips():
        found = []
        seen = set()
        for folder in (os.path.join(game_dir(), "mas_os_export"), characters_dir()):
            if not folder or not os.path.isdir(folder):
                continue
            try:
                names = os.listdir(folder)
            except Exception:
                names = []
            for name in sorted(names):
                if not name.lower().endswith(".zip"):
                    continue
                if name in seen:
                    continue
                seen.add(name)
                found.append({
                    "name": name,
                    "path": os.path.join(folder, name),
                })
        return found

    def data_import_zip(path):
        global data_status
        if not path or not os.path.isfile(path):
            data_status = "ZIP не найден."
            return False
        folder = _save_folder()
        try:
            zf = zipfile.ZipFile(path, "r")
        except Exception as err:
            data_status = "Не открыть ZIP: {0}".format(err)
            return False
        try:
            names = zf.namelist()
            per_name = None
            for n in names:
                base = os.path.basename(n)
                if base == "persistent" or (base.startswith("persistent") and (base.endswith(".bak") or base == "persistent_unstable")):
                    per_name = n
                    break
            if per_name is None:
                data_status = "В архиве нет persistent."
                return False
            try:
                store.__mas__memoryBackup()
            except Exception:
                pass
            payload = zf.read(per_name)
            dst = os.path.join(folder, "persistent")
            handle = open(dst, "wb")
            try:
                handle.write(payload)
            finally:
                handle.close()
            for n in names:
                base = os.path.basename(n)
                if base == "db.mcal" or (base.startswith("db.mcal") and base.endswith(".bak")):
                    cal_data = zf.read(n)
                    cal_dst = os.path.join(folder, "db.mcal")
                    handle = open(cal_dst, "wb")
                    try:
                        handle.write(cal_data)
                    finally:
                        handle.close()
                    break
        except Exception as err:
            data_status = "Импорт не удался: {0}".format(err)
            return False
        finally:
            zf.close()
        data_status = "ZIP импортирован. Перезапуск..."
        reboot_shell()
        return True


label mas_os_data:
    $ store.mas_os.data_status = ""
    if not store.mas_os.data_selected:
        $ store.mas_os.data_selected = "persistent"
    call screen mas_os_data with mas_os_trans
    jump mas_os_home


screen mas_os_data():
    modal True
    zorder 200

    $ rows = store.mas_os.list_persistents()
    $ sel = store.mas_os.data_selected_row()
    $ zips = store.mas_os.list_import_zips()
    $ status = store.mas_os.data_status
    $ sel_name = sel["name"] if sel else ""
    $ d_nick = ("Моника: " + sel["nick"]) if sel else ""
    $ d_player = ("Игрок: " + sel["player"]) if sel else ""
    $ d_ver = ("Версия: " + sel["version"]) if sel else ""
    $ d_aff = ("Привязанность: " + sel["aff_s"] + "  " + sel["state_s"]) if sel else ""
    $ d_ses = ("Сессии: " + sel["sessions"] + "  /  " + sel["play"]) if sel else ""
    $ d_first = ("Первая: " + sel["first"]) if sel else ""
    $ d_last = ("Последняя: " + sel["last"]) if sel else ""
    $ d_file = ("Файл: " + sel["mtime"] + "  " + sel["size"]) if sel else ""

    use mas_os_bg

    text _("Данные") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 18

    text _("Бэкапы persistent в папке сохранений. Загрузка подменяет текущий файл и перезапускает игру."):
        style "mas_os_hint"
        xpos 48
        ypos 58
        xsize 1180

    viewport:
        xpos 48
        ypos 92
        xysize (760, 430)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 4

            hbox:
                spacing 8
                text _("файл") style "mas_os_hint" xsize 240
                text _("дата") style "mas_os_hint" xsize 150
                text _("игрок") style "mas_os_hint" xsize 140
                text _("привяз.") style "mas_os_hint" xsize 90

            if not rows:
                text _("Persistent не найден."):
                    style "mas_os_body"
            else:
                for row in rows:
                    textbutton "{0}   {1}   {2}   {3}".format(row["name"], row["mtime"], row["player"], row["aff_s"]):
                        style "mas_os_side_btn"
                        text_style "mas_os_side_btn_text"
                        xsize 730
                        ysize 48
                        substitute False
                        selected (row["name"] == sel_name)
                        action Function(store.mas_os.data_select, row["name"])

    frame:
        style "mas_os_panel"
        xpos 828
        ypos 92
        xysize (404, 430)
        padding (16, 14)

        vbox:
            spacing 6
            xfill True

            if sel:
                text sel["name"]:
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

                text d_file:
                    style "mas_os_hint"
                    substitute False
            else:
                text _("Выбери запись слева."):
                    style "mas_os_hint"

    vbox:
        xpos 48
        ypos 532
        spacing 8

        hbox:
            spacing 8

            textbutton _("Создать бэкап"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 200
                action Function(store.mas_os.data_make_backup)

            textbutton _("Загрузить"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 180
                action Show(
                    "mas_os_confirm",
                    message=_("Подставить этот persistent и перезапустить MAS OS? Текущий сначала сохранится в bak."),
                    yes_action=[Function(store.mas_os.data_restore), Hide("mas_os_confirm")],
                    no_action=Hide("mas_os_confirm")
                )

            textbutton _("Экспорт ZIP"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 180
                action Function(store.mas_os.data_export_zip)

            textbutton _("Удалить bak"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 180
                action Show(
                    "mas_os_confirm",
                    message=_("Удалить выбранный bak? Текущий persistent не тронется."),
                    yes_action=[Function(store.mas_os.data_delete_bak), Hide("mas_os_confirm")],
                    no_action=Hide("mas_os_confirm")
                )

        if zips:
            hbox:
                spacing 8

                text _("Импорт ZIP:"):
                    style "mas_os_hint"
                    yalign 0.5

                for zitem in zips[:3]:
                    textbutton zitem["name"]:
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 240
                        substitute False
                        action Show(
                            "mas_os_confirm",
                            message=_("Импортировать архив и перезапустить?"),
                            yes_action=[Function(store.mas_os.data_import_zip, zitem["path"]), Hide("mas_os_confirm")],
                            no_action=Hide("mas_os_confirm")
                        )

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 48
            ypos 612
            xsize 1180
            substitute False

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")
