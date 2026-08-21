# MAS OS — read log files from /log and the game folder.

init -5 python in mas_os:
    import os
    import store

    LOG_DESC = {
        "mas_log.log": "Основной лог MAS",
        "aff_log.log": "Привязанность",
        "submod_log.log": "Сабмоды",
        "early.log": "Ранний запуск / persistent",
        "spj.log": "JSON спрайтов",
        "pnm.log": "Пианино",
        "bg_flt.log": "Фоны / фильтры",
        "traceback.txt": "Последний краш Ren'Py",
        "log.txt": "Лог движка Ren'Py",
    }

    LOG_TAIL = 24000
    LOG_MAX_LINES = 160
    LOG_CHUNK = 40

    def list_logs():
        rows = []
        seen = set()
        based = game_dir()
        log_dir = os.path.join(based, "log")

        def add_path(path):
            if not path or not os.path.isfile(path):
                return
            name = os.path.basename(path)
            key = os.path.normcase(path)
            if key in seen:
                return
            seen.add(key)
            try:
                size = os.path.getsize(path)
            except Exception:
                size = 0
            rows.append({
                "id": key,
                "name": name,
                "hint": LOG_DESC.get(name, "Лог"),
                "path": path,
                "size": size,
            })

        if os.path.isdir(log_dir):
            try:
                names = sorted(os.listdir(log_dir))
            except Exception:
                names = []
            for name in names:
                low = name.lower()
                if low.endswith(".log") or low.endswith(".txt"):
                    add_path(os.path.join(log_dir, name))

        add_path(os.path.join(based, "traceback.txt"))
        add_path(os.path.join(based, "log.txt"))
        return rows

    def read_log_text(path):
        if not path or not os.path.isfile(path):
            return "Файл не найден."
        try:
            size = os.path.getsize(path)
            with open(path, "rb") as handle:
                if size > LOG_TAIL:
                    handle.seek(size - LOG_TAIL)
                    data = handle.read()
                    truncated = True
                else:
                    data = handle.read()
                    truncated = False
        except Exception as err:
            return "Не удалось прочитать: {0}".format(err)

        text = None
        for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
            try:
                text = data.decode(enc)
                break
            except Exception:
                continue
        if text is None:
            text = data.decode("latin-1", "replace")

        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
        total = len(lines)
        if truncated or total > LOG_MAX_LINES:
            lines = lines[-LOG_MAX_LINES:]
            lines.insert(0, "[конец файла, последние {0} строк из {1}]".format(LOG_MAX_LINES, total))
        text = "\n".join(lines)
        # { } are Ren'Py text tags; [ ] are interpolations.
        return text.replace("{", "{{").replace("[", "[[")

    def log_chunks(text):
        lines = (text or "").split("\n")
        if not lines:
            return [""]
        chunks = []
        i = 0
        while i < len(lines):
            chunks.append("\n".join(lines[i:i + LOG_CHUNK]))
            i += LOG_CHUNK
        return chunks

    def set_active_log(log_id):
        global _active_log
        _active_log = None
        for row in list_logs():
            if row["id"] == log_id:
                row = dict(row)
                try:
                    row["text"] = read_log_text(row["path"])
                except Exception as err:
                    row["text"] = "Не удалось показать лог:\n{0}".format(err).replace("{", "{{").replace("[", "[[")
                _active_log = row
                return

    def ensure_active_log():
        global _active_log
        rows = list_logs()
        if not rows:
            _active_log = None
            return
        if _active_log is None:
            set_active_log(rows[0]["id"])
            return
        current = _active_log.get("id")
        for row in rows:
            if row["id"] == current:
                set_active_log(current)
                return
        set_active_log(rows[0]["id"])

    def active_log():
        return _active_log


label mas_os_logs:
    $ store.mas_os.ensure_active_log()
    call screen mas_os_logs with mas_os_trans
    jump mas_os_home


screen mas_os_logs():
    modal True
    zorder 200

    $ rows = store.mas_os.list_logs()
    $ log = store.mas_os.active_log()
    $ log_id = log["id"] if log else None
    $ log_title = log["name"] if log else _("Логи")
    $ log_hint = log["hint"] if log else ""
    $ log_text = log["text"] if log else _("Логов пока нет.")
    $ log_chunks = store.mas_os.log_chunks(log_text)

    use mas_os_bg

    text _("Логи") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 22

    text _("Читаются файлы из log/ и корень игры. Большие обрезаются с конца."):
        style "mas_os_hint"
        xpos 48
        ypos 66

    viewport:
        xpos 48
        ypos 104
        xysize (340, 506)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 6

            if rows:
                for row in rows:
                    textbutton "{0}\n{1}".format(row["name"], row["hint"]):
                        style "mas_os_side_btn"
                        text_style "mas_os_side_btn_text"
                        selected (row["id"] == log_id)
                        action Function(store.mas_os.set_active_log, row["id"])
            else:
                text _("Файлов лога нет."):
                    style "mas_os_hint"

    frame:
        style "mas_os_panel"
        xpos 410
        ypos 104
        xysize (822, 506)
        padding (18, 14)

        vbox:
            spacing 6
            xfill True

            text log_title:
                style "mas_os_subtitle"

            if log_hint:
                text log_hint:
                    style "mas_os_hint"

            viewport:
                xysize (786, 430)
                draggable True
                mousewheel True
                scrollbars "vertical"

                vbox:
                    spacing 0
                    xsize 750

                    for chunk in log_chunks:
                        text chunk:
                            style "mas_os_log_text"
                            xsize 750
                            substitute False

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


style mas_os_log_text is mas_os_hint:
    font "mod_assets/font/mplus-1mn-medium.ttf"
    size 14
    color "#E8D0DC"
    outlines []
