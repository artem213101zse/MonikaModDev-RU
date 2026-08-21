# MAS OS file manager — browse/create/edit/delete under the game and save dirs.

init -5 python in mas_os:
    import os
    import shutil
    import store

    TEXT_EXTS = set([
        ".txt", ".log", ".json", ".rpy", ".md", ".csv", ".gift", ".xml",
        ".html", ".css", ".ini", ".cfg", ".mcal", ".py", ".json5",
    ])
    EDIT_MAX = 12000
    VIEW_BYTES = 48000
    VIEW_MAX_LINES = 240
    VIEW_CHUNK = 40
    VIEW_WRAP = 160
    EDIT_MAX_LINES = 400

    fm_cwd = ""
    fm_status = ""
    fm_name = ""
    fm_prompt_kind = "file"
    fm_edit_path = ""
    fm_edit_buf = ""
    fm_edit_view = ""
    fm_edit_name = ""
    fm_can_save = True
    fm_truncated = False
    fm_edit_lines = []
    fm_edit_index = -1
    fm_line_buf = ""
    fm_typing = False

    def _abs(path):
        return _norm(os.path.abspath(path))

    def fm_roots():
        roots = [_abs(game_dir())]
        sd = save_dir()
        if sd:
            sd = _abs(sd)
            if sd not in roots:
                roots.append(sd)
        return roots

    def fm_in_sandbox(path):
        path = _abs(path)
        if not path:
            return False
        path_l = path.lower()
        for root in fm_roots():
            if path == root or path.startswith(root + "/"):
                return True
            root_l = (root or "").lower()
            if path_l == root_l or path_l.startswith(root_l + "/"):
                return True
        return False

    def fm_is_root(path=None):
        path = _abs(path or fm_cwd)
        return path in fm_roots()

    def fm_rel(path=None):
        path = _abs(path or fm_cwd)
        gd = _abs(game_dir())
        if path == gd or path.startswith(gd + "/"):
            rel = path[len(gd):].lstrip("/")
            return rel if rel else _("игра")
        sd = _abs(save_dir()) if save_dir() else ""
        if sd and (path == sd or path.startswith(sd + "/")):
            rel = path[len(sd):].lstrip("/")
            return ("saves/" + rel) if rel else _("сохранения")
        return path

    def fm_open(path=None):
        global fm_cwd, fm_status
        target = _abs(path or game_dir())
        if not fm_in_sandbox(target):
            fm_status = "Путь вне папки игры."
            return False
        if not os.path.isdir(target):
            fm_status = "Папка не найдена."
            return False
        fm_cwd = target
        fm_status = ""
        return True

    def fm_go_parent():
        if fm_is_root():
            return False
        parent = _abs(os.path.dirname(fm_cwd))
        return fm_open(parent)

    def fm_jump(kind):
        global fm_status
        mapping = {
            "game": game_dir(),
            "characters": characters_dir(),
            "log": log_dir(),
            "submods": submods_dir(),
            "saves": save_dir(),
        }
        path = mapping.get(kind)
        if not path:
            fm_status = "Папка не задана."
            return False
        if kind in ("characters", "log", "submods") and not os.path.isdir(path):
            try:
                os.makedirs(path)
            except Exception:
                pass
        return fm_open(path)

    def _fmt_size(n):
        try:
            n = int(n)
        except Exception:
            return "?"
        if n < 1024:
            return "{0} B".format(n)
        if n < 1024 * 1024:
            return "{0:.1f} KB".format(n / 1024.0)
        return "{0:.1f} MB".format(n / (1024.0 * 1024.0))

    def fm_is_text(name):
        ext = os.path.splitext(name)[1].lower()
        return ext in TEXT_EXTS or ext == ""

    def fm_icon_for(name, is_dir):
        if is_dir:
            return "files"
        ext = os.path.splitext(name or "")[1].lower()
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
            return "gallery"
        if ext in (".mp3", ".ogg", ".wav", ".opus", ".flac"):
            return "sound"
        if ext in (".ttf", ".otf"):
            return "font"
        if ext in (".zip", ".rpa", ".rpyc"):
            return "data"
        if ext == ".gift":
            return "gifts"
        if ext in (".rpy", ".py"):
            return "submods"
        if fm_is_text(name):
            return "file-text"
        return "file-text"

    def fm_list():
        cwd = fm_cwd or game_dir()
        items = []
        try:
            names = os.listdir(cwd)
        except Exception as err:
            return [{
                "name": "..",
                "dir": True,
                "label": _(".. (вверх)"),
                "meta": "",
                "path": cwd,
                "icon": "folder-up",
                "ipath": icon_path("folder-up"),
            }]

        for name in names:
            path = os.path.join(cwd, name)
            is_dir = os.path.isdir(path)
            meta = ""
            if not is_dir:
                try:
                    meta = _fmt_size(os.path.getsize(path))
                except Exception:
                    meta = "?"
            ui_name = name.replace("[", "[[").replace("{", "{{")
            iname = fm_icon_for(name, is_dir)
            items.append({
                "name": name,
                "dir": is_dir,
                "path": _abs(path),
                "meta": meta,
                "icon": iname,
                "ipath": icon_path(iname),
                "label": ui_name,
            })
        items.sort(key=lambda row: (not row["dir"], row["name"].lower()))
        return items

    def fm_enter(name):
        global fm_status
        path = _abs(os.path.join(fm_cwd, name))
        if not fm_in_sandbox(path):
            fm_status = "Путь вне папки игры."
            return None
        if os.path.isdir(path):
            fm_open(path)
            return None
        if fm_is_text(name):
            if fm_prepare_named(name):
                return "view"
            return None
        fm_status = "Бинарный файл ({0}). Можно удалить, но не открыть.".format(name)
        return None

    def fm_prepare_named(name):
        global fm_status, fm_edit_path
        if not fm_is_text(name):
            fm_status = "Бинарный файл ({0}). Можно удалить, но не открыть.".format(name)
            fm_edit_path = ""
            return False
        return fm_prepare_view(_abs(os.path.join(fm_cwd, name)), name)

    def _escape_view(text):
        return (text or "").replace("{", "{{").replace("[", "[[")

    def _wrap_view_lines(text, max_len=VIEW_WRAP, max_lines=VIEW_MAX_LINES):
        out = []
        cut = False
        for raw in (text or "").split("\n"):
            if not raw:
                out.append("")
            else:
                i = 0
                length = len(raw)
                while i < length:
                    out.append(raw[i:i + max_len])
                    i += max_len
                    if len(out) >= max_lines:
                        cut = True
                        break
            if len(out) >= max_lines:
                cut = True
                break
        if cut:
            out = out[:max_lines]
            out.append("...")
        return out

    def fm_prepare_view(path, name):
        global fm_edit_path, fm_edit_buf, fm_edit_view, fm_edit_name
        global fm_can_save, fm_status, fm_truncated, fm_edit_lines
        global fm_edit_index, fm_line_buf, fm_typing
        path = _abs(path)
        if not fm_in_sandbox(path) or not os.path.isfile(path):
            fm_status = "Файл не найден."
            return False
        try:
            with open(path, "rb") as handle:
                data = handle.read(VIEW_BYTES + 1)
        except Exception as err:
            fm_status = "Не прочитать: {0}".format(err)
            return False

        over_view = len(data) > VIEW_BYTES
        if over_view:
            data = data[:VIEW_BYTES]
        text = None
        for enc in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
            try:
                text = data.decode(enc)
                break
            except Exception:
                continue
        if text is None:
            fm_status = "Не похоже на текст."
            return False
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        nlines = text.count("\n") + 1
        fm_edit_path = path
        fm_edit_name = name
        fm_truncated = over_view or nlines > VIEW_MAX_LINES
        fm_can_save = (not over_view) and (len(data) <= EDIT_MAX) and (nlines <= EDIT_MAX_LINES)
        fm_edit_buf = text if fm_can_save else ""
        fm_edit_view = _escape_view("\n".join(_wrap_view_lines(text)))
        fm_edit_lines = []
        fm_edit_index = -1
        fm_line_buf = ""
        fm_typing = False
        fm_status = ""
        return True

    def fm_view_chunks():
        lines = (fm_edit_view or "").split("\n")
        chunks = []
        i = 0
        while i < len(lines):
            chunks.append("\n".join(lines[i:i + VIEW_CHUNK]))
            i += VIEW_CHUNK
        return chunks or [""]

    def fm_edit_chunks():
        return fm_view_chunks()

    def fm_line_label(idx):
        raw = ""
        if 0 <= idx < len(fm_edit_lines):
            raw = fm_edit_lines[idx] or ""
        shown = raw.replace("[", "[[").replace("{", "{{")
        if len(shown) > 90:
            shown = shown[:90] + "..."
        if not shown:
            shown = " "
        return "{0:>4}  {1}".format(idx + 1, shown)

    def start_fm_typing():
        global fm_typing
        fm_typing = True
        iv = getattr(store.mas_os, "fm_line_iv", None)
        if iv is not None:
            iv.default = True

    def stop_fm_typing():
        global fm_typing
        fm_typing = False
        iv = getattr(store.mas_os, "fm_line_iv", None)
        if iv is not None:
            iv.default = False

    def fm_begin_edit():
        global fm_edit_lines, fm_edit_index, fm_line_buf, fm_typing, fm_status
        if not fm_can_save:
            fm_status = "Этот файл слишком большой, чтобы править его здесь."
            return False
        text = fm_edit_buf if fm_edit_buf is not None else ""
        fm_edit_lines = text.split("\n")
        if not fm_edit_lines:
            fm_edit_lines = [""]
        fm_edit_index = -1
        fm_line_buf = ""
        fm_typing = False
        fm_status = ""
        return True

    def fm_select_line(idx):
        global fm_edit_index, fm_line_buf
        stop_fm_typing()
        if 0 <= idx < len(fm_edit_lines):
            fm_edit_index = idx
            fm_line_buf = fm_edit_lines[idx]

    def fm_apply_line():
        global fm_edit_lines, fm_status
        if 0 <= fm_edit_index < len(fm_edit_lines):
            fm_edit_lines[fm_edit_index] = fm_line_buf or ""
        stop_fm_typing()
        fm_status = ""
        return True

    def fm_insert_line():
        global fm_edit_lines, fm_edit_index, fm_line_buf, fm_status
        fm_apply_line()
        if len(fm_edit_lines) >= EDIT_MAX_LINES:
            fm_status = "Слишком много строк."
            return False
        at = fm_edit_index + 1 if fm_edit_index >= 0 else len(fm_edit_lines)
        fm_edit_lines.insert(at, "")
        fm_edit_index = at
        fm_line_buf = ""
        return True

    def fm_delete_line():
        global fm_edit_lines, fm_edit_index, fm_line_buf
        if not fm_edit_lines:
            fm_edit_lines = [""]
            fm_edit_index = 0
            fm_line_buf = ""
            return True
        if len(fm_edit_lines) == 1:
            fm_edit_lines[0] = ""
            fm_edit_index = 0
            fm_line_buf = ""
            return True
        idx = fm_edit_index if fm_edit_index >= 0 else (len(fm_edit_lines) - 1)
        if idx < 0 or idx >= len(fm_edit_lines):
            idx = len(fm_edit_lines) - 1
        fm_edit_lines.pop(idx)
        fm_edit_index = min(idx, len(fm_edit_lines) - 1)
        fm_line_buf = fm_edit_lines[fm_edit_index]
        stop_fm_typing()
        return True

    def fm_save_edit():
        global fm_status, fm_edit_view, fm_edit_buf
        if not fm_can_save:
            fm_status = "Файл слишком большой для правки здесь."
            return False
        fm_apply_line()
        path = fm_edit_path
        if not path or not fm_in_sandbox(path):
            fm_status = "Нельзя сохранить сюда."
            return False
        text = "\n".join(fm_edit_lines)
        try:
            with open(path, "wb") as handle:
                handle.write(text.replace("\r\n", "\n").encode("utf-8"))
            fm_edit_buf = text
            fm_edit_view = _escape_view("\n".join(_wrap_view_lines(text)))
            fm_status = "Сохранено: {0}".format(os.path.basename(path))
            return True
        except Exception as err:
            fm_status = "Ошибка записи: {0}".format(err)
            return False

    def fm_valid_name(raw, as_file=False):
        name = (raw or "").strip()
        if not name or name in (".", ".."):
            return None
        if "/" in name or "\\" in name or ":" in name:
            return None
        if as_file and "." not in name:
            name = name + ".txt"
        return name

    def fm_begin_create(kind):
        global fm_prompt_kind, fm_name, fm_status
        fm_prompt_kind = kind
        fm_name = ""
        fm_status = ""
        store.renpy.show_screen("mas_os_fm_prompt")

    def fm_confirm_create():
        global fm_status
        as_file = fm_prompt_kind == "file"
        name = fm_valid_name(fm_name, as_file=as_file)
        store.renpy.hide_screen("mas_os_fm_prompt")
        if not name:
            fm_status = "Имя не подходит."
            return False
        path = _abs(os.path.join(fm_cwd, name))
        if not fm_in_sandbox(path):
            fm_status = "Путь вне папки игры."
            return False
        if os.path.exists(path):
            fm_status = "Уже есть: {0}".format(name)
            return False
        try:
            if as_file:
                with open(path, "wb") as handle:
                    handle.write(b"")
                fm_status = "Создан файл {0}".format(name)
            else:
                os.makedirs(path)
                fm_status = "Создана папка {0}".format(name)
            return True
        except Exception as err:
            fm_status = "Не создать: {0}".format(err)
            return False

    def fm_delete(name):
        global fm_status
        path = _abs(os.path.join(fm_cwd, name))
        if fm_is_root(path) or not fm_in_sandbox(path):
            fm_status = "Это корень, удалять нельзя."
            return False
        if not os.path.exists(path):
            fm_status = "Уже нет."
            return False
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                fm_status = "Папка удалена: {0}".format(name)
            else:
                os.remove(path)
                fm_status = "Файл удалён: {0}".format(name)
            return True
        except Exception as err:
            fm_status = "Не удалить: {0}".format(err)
            return False


init python:
    class MASOSAttrInputValue(InputValue):
        def __init__(self, field, default=True, editable=True, returnable=False):
            self.field = field
            self.default = default
            self.editable = editable
            self.returnable = returnable

        def get_text(self):
            return getattr(store.mas_os, self.field, "") or ""

        def set_text(self, value):
            setattr(store.mas_os, self.field, value)

    class MASOSFn(Action):
        """
        Call a store function and keep the current screen.
        Function() returns the callable's value, so True from fm_jump/fm_open
        ends `call screen mas_os_files` and dumps the player back to home.
        """
        def __init__(self, func, *args):
            self.func = func
            self.args = args

        def __call__(self):
            self.func(*self.args)
            renpy.restart_interaction()
            return None

    class MASOSFMOpen(Action):
        def __init__(self, name, is_dir):
            self.name = name
            self.is_dir = is_dir

        def __call__(self):
            if self.is_dir:
                store.mas_os.fm_enter(self.name)
                renpy.restart_interaction()
                return None
            if store.mas_os.fm_prepare_named(self.name):
                return "view"
            renpy.restart_interaction()
            return None


init 1 python:
    store.mas_os.fm_line_iv = MASOSAttrInputValue("fm_line_buf", default=False)


screen mas_os_files():
    modal True
    zorder 200

    $ entries = store.mas_os.fm_list()
    $ cwd_label = store.mas_os.fm_rel()
    $ status = store.mas_os.fm_status
    $ at_root = store.mas_os.fm_is_root()
    $ del_icon = store.mas_os.icon_path("delete")
    $ up_icon = store.mas_os.icon_path("folder-up")

    use mas_os_bg

    text _("Файлы") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text cwd_label:
        style "mas_os_hint"
        xpos 48
        ypos 58
        xsize 1180
        substitute False

    hbox:
        xpos 48
        ypos 86
        spacing 8

        textbutton _("Игра"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 110
            action MASOSFn(store.mas_os.fm_jump, "game")

        textbutton _("characters"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 160
            action MASOSFn(store.mas_os.fm_jump, "characters")

        textbutton _("log"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 90
            action MASOSFn(store.mas_os.fm_jump, "log")

        textbutton _("Submods"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 140
            action MASOSFn(store.mas_os.fm_jump, "submods")

        textbutton _("saves"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 110
            action MASOSFn(store.mas_os.fm_jump, "saves")

        textbutton _("Подарки"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 140
            action Return("gifts")

        textbutton _("Логи"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 100
            action Return("logs")

    hbox:
        xpos 48
        ypos 136
        spacing 8

        button:
            style "mas_os_nav_btn"
            xsize 160
            ysize 44
            sensitive (not at_root)
            action MASOSFn(store.mas_os.fm_go_parent)

            hbox:
                spacing 8
                xalign 0.5
                yalign 0.5

                if up_icon:
                    add store.mas_os.fit_image(up_icon, 22, 22):
                        yalign 0.5
                text _("вверх"):
                    style "mas_os_nav_btn_text"
                    yalign 0.5

        textbutton _("Папка"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 120
            action MASOSFn(store.mas_os.fm_begin_create, "folder")

        textbutton _("txt"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 100
            action MASOSFn(store.mas_os.fm_begin_create, "file")

    viewport:
        xpos 48
        ypos 184
        xysize (1184, 420)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 4

            if not entries:
                text _("Папка пустая."):
                    style "mas_os_hint"
            else:
                for item in entries:
                    hbox:
                        spacing 8

                        button:
                            style "mas_os_side_btn"
                            xsize 980
                            ysize 48
                            padding (8, 6)
                            action MASOSFMOpen(item["name"], item["dir"])

                            hbox:
                                spacing 12
                                yalign 0.5
                                xoffset 8

                                if item["ipath"]:
                                    add store.mas_os.fit_image(item["ipath"], 32, 32):
                                        yalign 0.5
                                else:
                                    frame:
                                        xysize (32, 32)
                                        background Solid("#3A1524")
                                        yalign 0.5

                                text item["label"]:
                                    style "mas_os_side_btn_text"
                                    yalign 0.5
                                    substitute False

                                if item["meta"]:
                                    text item["meta"]:
                                        style "mas_os_hint"
                                        yalign 0.5

                        button:
                            style "mas_os_nav_btn"
                            xsize 48
                            ysize 48
                            action Show(
                                "mas_os_confirm",
                                message="Удалить {0}?".format(item["name"].replace("[", "[[").replace("{", "{{")),
                                yes_action=[MASOSFn(store.mas_os.fm_delete, item["name"]), Hide("mas_os_confirm")],
                                no_action=Hide("mas_os_confirm")
                            )

                            if del_icon:
                                add store.mas_os.fit_image(del_icon, 24, 24):
                                    xalign 0.5
                                    yalign 0.5
                            else:
                                text _("X"):
                                    style "mas_os_nav_btn_text"
                                    xalign 0.5
                                    yalign 0.5

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 48
            ypos 608
            xsize 900

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_fm_prompt():
    modal True
    zorder 320

    add Solid("#000000B2") at mas_os_dim

    frame at store.mas_os.t_modal():
        style "mas_os_panel"
        xalign 0.5
        yalign 0.5
        xsize 640
        padding (24, 20)

        vbox:
            spacing 14
            xfill True

            if store.mas_os.fm_prompt_kind == "folder":
                text _("Имя новой папки"):
                    style "mas_os_subtitle"
                    xalign 0.5
            else:
                text _("Имя txt-файла"):
                    style "mas_os_subtitle"
                    xalign 0.5

            input:
                value MASOSAttrInputValue("fm_name")
                length 40
                copypaste True
                color store.mas_os.theme_color("input")
                size 22
                xalign 0.5

            hbox:
                xalign 0.5
                spacing 16

                textbutton _("Создать"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    action MASOSFn(store.mas_os.fm_confirm_create)

                textbutton _("Отмена"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    action Hide("mas_os_fm_prompt")


screen mas_os_fm_view():
    modal True
    zorder 200

    $ chunks = store.mas_os.fm_view_chunks()
    $ can_save = store.mas_os.fm_can_save
    $ truncated = store.mas_os.fm_truncated
    $ status = store.mas_os.fm_status
    $ fname = store.mas_os.fm_edit_name or _("файл")

    use mas_os_bg

    text fname at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16
        substitute False

    if truncated and not can_save:
        text _("Только чтение. Файл большой — показано начало."):
            style "mas_os_hint"
            xpos 48
            ypos 58
    elif can_save:
        text _("Просмотр. Чтобы изменить — «Править» внизу."):
            style "mas_os_hint"
            xpos 48
            ypos 58
    else:
        text _("Только чтение."):
            style "mas_os_hint"
            xpos 48
            ypos 58

    viewport:
        xpos 48
        ypos 96
        xysize (1184, 520)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 0
            xsize 1140

            for chunk in chunks:
                text chunk:
                    style "mas_os_log_text"
                    xsize 1140
                    substitute False

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 280
            ypos 648
            xsize 700
            substitute False

    hbox:
        xpos 48
        ypos 640
        spacing 12

        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 160
            action Return("back")

        if can_save:
            textbutton _("Править"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xsize 180
                action Return("edit")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


screen mas_os_fm_edit():
    modal True
    zorder 200

    $ lines = store.mas_os.fm_edit_lines
    $ idx = store.mas_os.fm_edit_index
    $ nlines = len(lines)
    $ status = store.mas_os.fm_status
    $ typing = store.mas_os.fm_typing
    $ typed = store.mas_os.fm_line_buf or ""
    $ fname = store.mas_os.fm_edit_name or _("файл")
    $ line_no = (idx + 1) if idx >= 0 else 0
    $ line_hint = _("Строка {0} из {1}. Нажми строку, потом поле ввода.").format(line_no, nlines)

    use mas_os_bg

    text fname at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16
        substitute False

    text line_hint:
        style "mas_os_hint"
        xpos 48
        ypos 58

    viewport:
        xpos 48
        ypos 96
        xysize (1184, 400)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 2
            xsize 1140

            if not lines:
                text _("Файл пустой."):
                    style "mas_os_hint"
            else:
                for i in range(nlines):
                    textbutton store.mas_os.fm_line_label(i):
                        style "mas_os_side_btn"
                        text_style "mas_os_side_btn_text"
                        xsize 1140
                        ysize 36
                        substitute False
                        selected (i == idx)
                        action MASOSFn(store.mas_os.fm_select_line, i)

    frame:
        style "mas_os_panel"
        xpos 48
        ypos 506
        xysize (1184, 114)
        padding (12, 10)

        vbox:
            spacing 8
            xfill True

            if idx < 0:
                text _("Сначала выбери строку в списке."):
                    style "mas_os_hint"
                    yalign 0.5
            else:
                hbox:
                    spacing 8
                    yalign 0.5

                    if typing:
                        input:
                            value store.mas_os.fm_line_iv
                            copypaste True
                            color store.mas_os.theme_color("input")
                            size 18
                            xsize 620
                            yalign 0.5

                        textbutton _("Готово"):
                            style "mas_os_nav_btn"
                            text_style "mas_os_nav_btn_text"
                            xsize 110
                            action [
                                store.mas_os.fm_line_iv.Disable(),
                                MASOSFn(store.mas_os.fm_apply_line),
                            ]
                    else:
                        button:
                            style "mas_os_gift_field"
                            xsize 740
                            ysize 40
                            action [
                                MASOSFn(store.mas_os.start_fm_typing),
                                store.mas_os.fm_line_iv.Enable(),
                            ]

                            if typed:
                                text typed:
                                    style "mas_os_body"
                                    size 16
                                    yalign 0.5
                                    substitute False
                            else:
                                text _("Нажми, чтобы ввести строку"):
                                    style "mas_os_hint"
                                    size 15
                                    yalign 0.5

                    textbutton _("+"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 70
                        action MASOSFn(store.mas_os.fm_insert_line)

                    textbutton _("-"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 70
                        action MASOSFn(store.mas_os.fm_delete_line)

    if status:
        text status:
            style "mas_os_subtitle"
            xpos 420
            ypos 648
            xsize 500
            substitute False

    hbox:
        xpos 48
        ypos 640
        spacing 12

        textbutton _("Сохранить"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 180
            action MASOSFn(store.mas_os.fm_save_edit)

        textbutton _("К просмотру"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xsize 200
            action [
                MASOSFn(store.mas_os.stop_fm_typing),
                Return("back"),
            ]

    key "K_ESCAPE" action [MASOSFn(store.mas_os.stop_fm_typing), Return("back")]
    key "K_AC_BACK" action If(
        store.mas_os.fm_typing,
        [store.mas_os.fm_line_iv.Disable(), MASOSFn(store.mas_os.stop_fm_typing)],
        [MASOSFn(store.mas_os.stop_fm_typing), Return("back")],
    )
