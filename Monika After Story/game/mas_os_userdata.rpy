# -*- coding: utf-8 -*-
# MAS OS — live user-data folders (characters, custom_bgm, chess, piano).
#
# Layout v3 (PC basedir and Android Documents/Monika_after_story):
#   saves, characters, custom_bgm, chess_games, piano_songs, game
#   log/                 journals (same place as stock MAS on PC)
#   mas_os/{обои, шрифты, текстбоксы, неопределено}
#   mas_bios/{archives, backups, flags, submods, paths.json}
# Internal filesDir is Python/BIOS only.

init -8 python in mas_os:
    import json
    import os
    import re
    import shutil
    import store

    LAYOUT_VERSION = 3
    SYSTEM_DIRNAME = "mas_bios"
    LEGACY_SYSTEM_DIRNAME = "_mas"
    MAS_OS_DIRNAME = u"mas_os"
    MAS_OS_WALLPAPERS = u"обои"
    MAS_OS_FONTS = u"шрифты"
    MAS_OS_TEXTBOXES = u"текстбоксы"
    MAS_OS_UNKNOWN = u"неопределено"

    USER_DATA_FOLDERS = (
        "characters",
        "custom_bgm",
        "chess_games",
        "piano_songs",
    )

    MAS_OS_SUBFOLDERS = (
        MAS_OS_WALLPAPERS,
        MAS_OS_FONTS,
        MAS_OS_TEXTBOXES,
        MAS_OS_UNKNOWN,
    )

    USER_DATA_README = (
        u"MAS OS — ваши данные\n"
        u"====================\n\n"
        u"Положите файл в нужную папку. Игра подхватит его "
        u"(музыку — после входа в MAS OS или перезапуска).\n"
        u"Android: это Documents/Monika_after_story, не папка приложения.\n"
        u"ПК: это папка рядом с DDLC.exe.\n\n"
        u"saves/          сейвы и persistent (Android)\n"
        u"characters/     подарки .gift, oki doki, imsorry, файл Моники\n"
        u"custom_bgm/     своя музыка: ogg, opus, mp3\n"
        u"chess_games/    сохранённые партии шахмат (.pgn)\n"
        u"piano_songs/    свои ноты пианино (.json)\n"
        u"game/           распакованный DDLC, сабмоды, спрайтпаки\n"
        u"log/            журналы игры и BIOS\n"
        u"mas_os/         обои, шрифты и текстбоксы MAS OS\n"
        u"  обои/         картинки фона оболочки (png/jpg)\n"
        u"  шрифты/       свои ttf/otf\n"
        u"  текстбоксы/   свои png; каждый цвет — в своей подпапке\n"
        u"  неопределено/ сюда игра кладёт файлы, которые не поняла\n"
        u"mas_bios/       служебное (архивы, бэкапы, установщик)\n"
        u"                  сюда руками класть ничего не нужно\n\n"
        u"Если бросить файл прямо в mas_os/, игра сама разложит его "
        u"по папкам при запуске.\n"
        u"Сабмоды ставятся в game/Submods. Zip качаются в mas_bios/archives.\n"
    )

    MAS_OS_FOLDER_README = (
        u"MAS OS — пользовательские файлы оболочки\n"
        u"========================================\n\n"
        u"Сюда копируйте обои, шрифты и текстбоксы через проводник.\n"
        u"Лучше сразу во вложенные папки:\n"
        u"  обои/         png, jpg, jpeg\n"
        u"  шрифты/       ttf, otf\n"
        u"  текстбоксы/   png (свои варианты в корне, каждый цвет — в своей папке)\n\n"
        u"Файл, брошенный прямо сюда, игра разложит сама.\n"
        u"Непонятные файлы попадут в «неопределено» — оболочка их не читает.\n"
        u"Не кладите сюда .rpy — скрипты из этой папки не запускаются.\n"
    )

    _user_data_applied = False

    def user_data_root():
        """
        Folder the player can actually open.
        Documents when that mode is active; otherwise MAS basedir
        (PC game folder, or Android app files — same layout as RG).
        """
        try:
            st = android_saves_status()
        except Exception:
            st = {}
        if st.get("using") == "documents" and st.get("path"):
            return _norm(st.get("path"))
        return _norm(store.renpy.config.basedir)

    def user_data_dir(name):
        root = user_data_root()
        if not root:
            return ""
        return _norm(os.path.join(root, name))

    def user_data_is_documents():
        try:
            st = android_saves_status()
        except Exception:
            st = {}
        return bool(st.get("using") == "documents" and st.get("path"))

    def system_root():
        root = user_data_root()
        if not root:
            return ""
        return _norm(os.path.join(root, SYSTEM_DIRNAME))

    def archives_dir():
        return _norm(os.path.join(system_root() or "", "archives"))

    def backups_dir():
        return _norm(os.path.join(system_root() or "", "backups"))

    def flags_dir():
        return _norm(os.path.join(system_root() or "", "flags"))

    def mas_os_root():
        root = user_data_root()
        if not root:
            return ""
        return _norm(os.path.join(root, MAS_OS_DIRNAME))

    def mas_os_sub(name):
        base = mas_os_root()
        if not base or not name:
            return ""
        return _norm(os.path.join(base, name))

    def mas_os_wallpapers_dir():
        return mas_os_sub(MAS_OS_WALLPAPERS)

    def mas_os_fonts_dir():
        return mas_os_sub(MAS_OS_FONTS)

    def mas_os_textboxes_dir():
        return mas_os_sub(MAS_OS_TEXTBOXES)

    def mas_os_unknown_dir():
        return mas_os_sub(MAS_OS_UNKNOWN)

    def _fs_name(name):
        if name is None:
            return u""
        try:
            if isinstance(name, unicode):
                return name
        except NameError:
            return name
        for enc in ("utf-8", "mbcs", "cp1251"):
            try:
                return name.decode(enc)
            except Exception:
                pass
        try:
            return unicode(name, "utf-8", "replace")
        except Exception:
            return name

    def drop_path_hint(rel):
        """
        Player-facing folder hint. Android Documents vs PC basedir.
        rel is a path under the user-data root, with / separators.
        """
        rel = (rel or "").replace("\\", "/").strip("/")
        if user_data_is_documents() or getattr(store.renpy, "android", False):
            if rel:
                return "Documents/Monika_after_story/" + rel
            return "Documents/Monika_after_story"
        if rel:
            return rel + u"  (папка игры, рядом с DDLC.exe)"
        return u"папка игры, рядом с DDLC.exe"

    def _ensure_dir(path):
        if not path:
            return False
        try:
            if not os.path.isdir(path):
                os.makedirs(path)
            return True
        except Exception:
            return False

    def _copy_newer(src, dst):
        if not src or not dst or not os.path.isfile(src):
            return False
        try:
            if os.path.isfile(dst):
                if os.path.getmtime(src) <= (os.path.getmtime(dst) + 1.0):
                    if os.path.getsize(src) == os.path.getsize(dst):
                        return False
            parent = os.path.dirname(dst)
            if parent:
                _ensure_dir(parent)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False

    def _merge_dir(src, dst):
        """Copy files from src into dst. Newer (or missing) wins. Returns count."""
        n = 0
        if not src or not os.path.isdir(src):
            return 0
        _ensure_dir(dst)
        try:
            names = os.listdir(src)
        except Exception:
            return 0
        for name in names:
            if name in (".", ".."):
                continue
            s = os.path.join(src, name)
            d = os.path.join(dst, name)
            try:
                if os.path.isdir(s):
                    n += _merge_dir(s, d)
                elif os.path.isfile(s):
                    if _copy_newer(s, d):
                        n += 1
            except Exception:
                pass
        return n

    def _write_text_file(path, body):
        if not path or os.path.isfile(path):
            return
        try:
            parent = os.path.dirname(path)
            if parent:
                _ensure_dir(parent)
            data = body
            try:
                if isinstance(data, unicode):
                    data = data.encode("utf-8")
            except NameError:
                pass
            handle = open(path, "wb")
            handle.write(data)
            handle.close()
        except Exception:
            pass

    def _write_readme(root):
        _write_text_file(os.path.join(root, "README_MAS_OS.txt"), USER_DATA_README)
        _write_text_file(
            os.path.join(mas_os_root() or "", "README.txt"),
            MAS_OS_FOLDER_README,
        )

    def _touch_nomedia(path):
        if not path:
            return
        _ensure_dir(path)
        marker = os.path.join(path, ".nomedia")
        if os.path.isfile(marker):
            return
        try:
            handle = open(marker, "wb")
            handle.close()
        except Exception:
            pass

    def ensure_user_data_tree():
        """Create the live folders. Safe to call often. Lazy on engine dirs."""
        root = user_data_root()
        if not root:
            return False
        _ensure_dir(root)
        for name in USER_DATA_FOLDERS:
            _ensure_dir(os.path.join(root, name))
        _ensure_dir(os.path.join(root, "log"))
        _ensure_dir(system_root())
        for name in ("archives", "backups", "flags", "submods"):
            _ensure_dir(os.path.join(system_root(), name))
        _ensure_mas_os_tree()
        if getattr(store.renpy, "android", False) and user_data_is_documents():
            for name in ("saves", "game"):
                _ensure_dir(os.path.join(root, name))
            _touch_nomedia(root)
            _touch_nomedia(system_root())
            _touch_nomedia(mas_os_root())
            for name in USER_DATA_FOLDERS + ("saves", "game", "log"):
                _touch_nomedia(os.path.join(root, name))
            for name in MAS_OS_SUBFOLDERS:
                _touch_nomedia(mas_os_sub(name))
        elif getattr(store.renpy, "android", False):
            _touch_nomedia(root)
            for name in USER_DATA_FOLDERS:
                _touch_nomedia(os.path.join(root, name))
            _touch_nomedia(mas_os_root())
            for name in MAS_OS_SUBFOLDERS:
                _touch_nomedia(mas_os_sub(name))
        _write_readme(root)
        return True

    def _ensure_mas_os_tree():
        root = mas_os_root()
        if not root:
            return False
        _ensure_dir(root)
        for name in MAS_OS_SUBFOLDERS:
            _ensure_dir(mas_os_sub(name))
        return True

    def _migrate_basedir_into_root(root):
        """First Documents use: copy app-folder user data so nothing vanishes."""
        based = _norm(store.renpy.config.basedir)
        if not based or _norm(root) == based:
            return
        for name in USER_DATA_FOLDERS:
            src = os.path.join(based, name)
            dst = os.path.join(root, name)
            if not os.path.isdir(src):
                continue
            # Always merge; skip if dest already has more recent copies.
            _merge_dir(src, dst)
        dest_log = os.path.join(root, "log")
        for name in ("traceback.txt", "log.txt", "masrun"):
            _copy_newer(os.path.join(based, name), os.path.join(dest_log, name))

    def _same_path(a, b):
        return _norm(a) == _norm(b) and bool(a)

    def _is_meta_name(name):
        low = _fs_name(name).lower()
        return low in (
            ".nomedia",
            "readme.txt",
            "readme_mas_os.txt",
            "paths.json",
        )

    def _move_one_file(src, dst):
        if not src or not os.path.isfile(src) or _same_path(src, dst):
            return
        if os.path.isfile(dst):
            try:
                os.remove(src)
            except Exception:
                pass
            return
        parent = os.path.dirname(dst)
        if parent:
            _ensure_dir(parent)
        try:
            shutil.move(src, dst)
        except Exception:
            if _copy_newer(src, dst):
                try:
                    os.remove(src)
                except Exception:
                    pass

    def _move_dir_contents(src, dst):
        if not src or not os.path.isdir(src) or _same_path(src, dst):
            return
        _ensure_dir(dst)
        try:
            names = os.listdir(src)
        except Exception:
            return
        for name in names:
            if name in (".", ".."):
                continue
            s = os.path.join(src, name)
            d = os.path.join(dst, name)
            try:
                if os.path.isdir(s):
                    _move_dir_contents(s, d)
                elif os.path.isfile(s):
                    _move_one_file(s, d)
            except Exception:
                pass
        _delete_if_empty(src)

    def _delete_if_empty(path):
        if not path or not os.path.isdir(path):
            return
        try:
            names = os.listdir(path)
        except Exception:
            return
        leftovers = []
        for name in names:
            if name in (".", ".."):
                continue
            if _is_meta_name(name) and os.path.isfile(os.path.join(path, name)):
                continue
            leftovers.append(name)
        if leftovers:
            return
        for name in names:
            fp = os.path.join(path, name)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass
        try:
            os.rmdir(path)
        except Exception:
            pass

    def _migrate_system_dirname(root):
        """_mas → mas_bios. Idempotent."""
        if not root:
            return
        old = os.path.join(root, LEGACY_SYSTEM_DIRNAME)
        new = os.path.join(root, SYSTEM_DIRNAME)
        if os.path.isdir(old) and not _same_path(old, new):
            _move_dir_contents(old, new)
            _delete_if_empty(old)

    def _migrate_log_to_root(root):
        """Keep log/ next to the game, never inside mas_bios."""
        if not root:
            return
        dest = os.path.join(root, "log")
        _ensure_dir(dest)
        for src in (
            os.path.join(root, SYSTEM_DIRNAME, "log"),
            os.path.join(root, LEGACY_SYSTEM_DIRNAME, "log"),
        ):
            if os.path.isdir(src) and not _same_path(src, dest):
                _move_dir_contents(src, dest)
        _move_one_file(os.path.join(root, "launcher.log"), os.path.join(dest, "launcher.log"))
        _move_one_file(os.path.join(root, "traceback.txt"), os.path.join(dest, "traceback.txt"))

    def _migrate_documents_layout(root):
        """Old v1 Documents tree → mas_bios (except log, which stays at root)."""
        if not root or not user_data_is_documents():
            return
        mas = os.path.join(root, SYSTEM_DIRNAME)
        _ensure_dir(mas)
        arch = os.path.join(mas, "archives")
        sm = os.path.join(mas, "submods")
        pairs = (
            (os.path.join(root, "incoming"), arch),
            (os.path.join(root, "archives"), arch),
            (os.path.join(root, "backups"), os.path.join(mas, "backups")),
            (os.path.join(root, "flags"), os.path.join(mas, "flags")),
            (os.path.join(root, "submods_installed"), os.path.join(sm, "installed")),
            (os.path.join(root, "submod_vanilla"), os.path.join(sm, "vanilla")),
            (os.path.join(root, "submod_payloads"), os.path.join(sm, "payloads")),
            (os.path.join(root, "submod_backups"), os.path.join(sm, "backups")),
            (os.path.join(root, "Transfer"), arch),
        )
        for src, dst in pairs:
            _move_dir_contents(src, dst)
        flags = os.path.join(mas, "flags")
        _move_one_file(
            os.path.join(root, ".mas_force_monika_home"),
            os.path.join(flags, ".mas_force_monika_home"),
        )
        _move_one_file(
            os.path.join(root, "mas_os_safe_mode"),
            os.path.join(flags, "mas_os_safe_mode"),
        )
        _migrate_log_to_root(root)

    def _legacy_mas_os_sub_map():
        return {
            u"wallpapers": MAS_OS_WALLPAPERS,
            u"wallpaper": MAS_OS_WALLPAPERS,
            u"fonts": MAS_OS_FONTS,
            u"font": MAS_OS_FONTS,
            u"textboxes": MAS_OS_TEXTBOXES,
            u"textbox": MAS_OS_TEXTBOXES,
            u"unknown": MAS_OS_UNKNOWN,
            u"unknown_content": MAS_OS_UNKNOWN,
            u"неопределенный контент": MAS_OS_UNKNOWN,
            u"неопределённый контент": MAS_OS_UNKNOWN,
        }

    def _classify_mas_os_dump(name):
        key = _fs_name(name)
        low = key.lower()
        if _is_meta_name(low):
            return None
        _root, ext = os.path.splitext(low)
        stem = os.path.splitext(key)[0].lower()
        if ext in (".ttf", ".otf", ".ttc", ".woff", ".woff2"):
            return MAS_OS_FONTS
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"):
            if (
                stem.startswith("textbox")
                or stem.startswith("tb_")
                or stem.startswith("namebox")
                or stem.startswith("gui_textbox")
            ):
                return MAS_OS_TEXTBOXES
            return MAS_OS_WALLPAPERS
        return MAS_OS_UNKNOWN

    def _sort_mas_os_dumps(root=None):
        """
        Files dropped in mas_os/ (not in a subfolder) go to обои / шрифты /
        текстбоксы / неопределено so Ren'Py never sees stray .rpy here.
        неопределено is never scanned afterwards.
        """
        base = mas_os_root()
        if root:
            base = _norm(os.path.join(root, MAS_OS_DIRNAME))
        if not base or not os.path.isdir(base):
            return
        _ensure_mas_os_tree()
        legacy = _legacy_mas_os_sub_map()
        known = set([_fs_name(n).lower() for n in MAS_OS_SUBFOLDERS])
        try:
            names = os.listdir(base)
        except Exception:
            return
        for name in names:
            if name in (".", ".."):
                continue
            src = os.path.join(base, name)
            key = _fs_name(name)
            low = key.lower()
            if _is_meta_name(low):
                continue
            try:
                is_dir = os.path.isdir(src)
            except Exception:
                continue
            if is_dir:
                dest_name = legacy.get(low)
                if dest_name and dest_name.lower() != low:
                    _move_dir_contents(src, mas_os_sub(dest_name))
                elif low not in known:
                    _move_dir_contents(src, os.path.join(mas_os_unknown_dir(), name))
                    _delete_if_empty(src)
                continue
            dest_kind = _classify_mas_os_dump(name)
            if not dest_kind:
                continue
            _move_one_file(src, os.path.join(mas_os_sub(dest_kind), name))
        _migrate_textbox_color_folders()

    def _migrate_textbox_color_folders():
        """tb_{hex}_{strength}_{src}.png pile → текстбоксы/{HEX}/tb_{strength}_{src}.png"""
        folder = mas_os_textboxes_dir()
        if not folder or not os.path.isdir(folder):
            return
        try:
            names = os.listdir(folder)
        except Exception:
            return
        pat = re.compile(r"^tb_([0-9A-Fa-f]{3,8})_(\d+)_(.+)\.png$")
        for name in names:
            src = os.path.join(folder, name)
            try:
                if not os.path.isfile(src):
                    continue
            except Exception:
                continue
            match = pat.match(name)
            if not match:
                continue
            hexc = match.group(1).upper()
            dest_dir = os.path.join(folder, hexc)
            _ensure_dir(dest_dir)
            new_name = "tb_{0}_{1}.png".format(match.group(2), match.group(3))
            _move_one_file(src, os.path.join(dest_dir, new_name))

    def _migrate_mas_os_assets(root=None):
        """Copy player wallpapers/fonts/tints out of game/ into mas_os/."""
        _ensure_mas_os_tree()
        bundled_wp = set([
            "splash.png", "menu.png",
            "wall1.jpg", "wall2.jpg", "wall3.jpg", "wall4.jpg",
            "black-background-with-wavy-lines_52683-76524.jpg",
        ])
        skip_font_prefix = (
            "sourcehansans", "mplus-2p", "mplus-1mn", "orig_m1",
            "aller", "riffic", "halogen", "m1_fixed", "shantell", "greatvibes",
        )
        skip_font_exact = set([
            "aller_rg.ttf", "rifficfree-bold.ttf", "halogen.ttf",
            "m1_fixed.ttf", "greatvibes-regular.ttf",
        ])
        try:
            gamed = writable_gamedir()
        except Exception:
            gamed = None
        if gamed:
            old_wp = os.path.join(gamed, "mod_assets", "mas_os", "wallpapers")
            dest_wp = mas_os_wallpapers_dir()
            if os.path.isdir(old_wp) and not _same_path(old_wp, dest_wp):
                try:
                    names = os.listdir(old_wp)
                except Exception:
                    names = []
                for name in names:
                    if name in (".", "..") or _is_meta_name(name):
                        continue
                    if _fs_name(name).lower() in bundled_wp:
                        continue
                    src = os.path.join(old_wp, name)
                    if os.path.isfile(src):
                        dest = os.path.join(dest_wp, name)
                        if user_data_is_documents():
                            _move_one_file(src, dest)
                        else:
                            _copy_newer(src, dest)
            old_font = os.path.join(gamed, "mod_assets", "font")
            dest_font = mas_os_fonts_dir()
            if os.path.isdir(old_font) and not _same_path(old_font, dest_font):
                try:
                    names = os.listdir(old_font)
                except Exception:
                    names = []
                for name in names:
                    if name in (".", "..") or _is_meta_name(name):
                        continue
                    low = _fs_name(name).lower()
                    ext = os.path.splitext(low)[1]
                    if ext not in (".ttf", ".otf"):
                        continue
                    if low in skip_font_exact:
                        continue
                    if any(low.startswith(p) for p in skip_font_prefix):
                        continue
                    src = os.path.join(old_font, name)
                    if os.path.isfile(src):
                        _copy_newer(src, os.path.join(dest_font, name))
            old_tint = os.path.join(gamed, "cache", "mas_os_tint")
            dest_tb = mas_os_textboxes_dir()
            if os.path.isdir(old_tint) and not _same_path(old_tint, dest_tb):
                _move_dir_contents(old_tint, dest_tb)
        try:
            saved = getattr(store.renpy.config, "savedir", None)
        except Exception:
            saved = None
        if saved:
            old_saved = os.path.join(saved, "mas_os_tint")
            dest_tb = mas_os_textboxes_dir()
            if os.path.isdir(old_saved) and not _same_path(old_saved, dest_tb):
                _move_dir_contents(old_saved, dest_tb)

    def _write_paths_json(root):
        if not root:
            return
        mas = os.path.join(root, SYSTEM_DIRNAME)
        blob = {
            "layout": LAYOUT_VERSION,
            "root": _norm(root),
            "saves": _norm(os.path.join(root, "saves")),
            "characters": _norm(os.path.join(root, "characters")),
            "custom_bgm": _norm(os.path.join(root, "custom_bgm")),
            "chess_games": _norm(os.path.join(root, "chess_games")),
            "piano_songs": _norm(os.path.join(root, "piano_songs")),
            "game": _norm(os.path.join(root, "game")),
            "log": _norm(os.path.join(root, "log")),
            "mas_os": _norm(os.path.join(root, MAS_OS_DIRNAME)),
            "wallpapers": _norm(mas_os_wallpapers_dir()),
            "fonts": _norm(mas_os_fonts_dir()),
            "textboxes": _norm(mas_os_textboxes_dir()),
            "unknown": _norm(mas_os_unknown_dir()),
            "system": _norm(mas),
            "archives": _norm(os.path.join(mas, "archives")),
            "backups": _norm(os.path.join(mas, "backups")),
            "flags": _norm(os.path.join(mas, "flags")),
            "submods": _norm(os.path.join(mas, "submods")),
        }
        path = os.path.join(mas, "paths.json")
        _ensure_dir(mas)
        try:
            handle = open(path, "wb")
            handle.write(json.dumps(blob, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8"))
            handle.close()
        except Exception:
            pass
        based = _norm(store.renpy.config.basedir)
        if based and based != _norm(root):
            try:
                handle = open(os.path.join(based, "mas_paths.json"), "wb")
                handle.write(json.dumps(blob, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8"))
                handle.close()
            except Exception:
                pass

    def _drop_basedir_mirrors(root):
        """Stop copying gifts/music into filesDir so they cannot resurrect."""
        based = _norm(store.renpy.config.basedir)
        if not based or not root or _same_path(based, root):
            return
        for name in ("custom_bgm", "characters"):
            src = os.path.join(root, name)
            dst = os.path.join(based, name)
            if _same_path(src, dst):
                continue
            if not os.path.isdir(src):
                continue
            if not os.path.isdir(dst):
                continue
            try:
                shutil.rmtree(dst)
            except Exception:
                pass

    def _mirror_music_for_engine(root):
        """Legacy no-op. Documents is the only copy of custom_bgm."""
        return

    def _mirror_folder_for_engine(root, name):
        """Legacy no-op. Documents is canonical; basedir is not a mirror."""
        return

    def _ensure_mbase_file():
        """Android APK has mbase in assets, not as a real file. Dockstat needs a path."""
        if not getattr(store.renpy, "android", False):
            return
        dests = [
            os.path.join(_norm(store.renpy.config.basedir), "game", "mod_assets", "monika", "mbase"),
        ]
        root = user_data_root()
        if root:
            dests.append(os.path.join(root, "game", "mod_assets", "monika", "mbase"))
        data = None
        for dest in dests:
            if os.path.isfile(dest) and os.path.getsize(dest) > 0:
                continue
            if data is None:
                try:
                    handle = store.renpy.file("mod_assets/monika/mbase")
                    data = handle.read()
                    handle.close()
                except Exception:
                    try:
                        import renpy.loader as _loader
                        handle = _loader.load("mod_assets/monika/mbase")
                        data = handle.read()
                        handle.close()
                    except Exception:
                        return
            parent = os.path.dirname(dest)
            _ensure_dir(parent)
            try:
                out = open(dest, "wb")
                out.write(data)
                out.close()
            except Exception:
                pass

    def _snapshot_logs(root):
        based_log = os.path.join(_norm(store.renpy.config.basedir), "log")
        dest_log = os.path.join(root, "log")
        if _norm(based_log) == _norm(dest_log):
            return
        _merge_dir(based_log, dest_log)
        _copy_newer(
            os.path.join(_norm(store.renpy.config.basedir), "traceback.txt"),
            os.path.join(dest_log, "traceback.txt"),
        )

    def _retarget_mas_paths(root):
        """Point MAS os-path constants at the live user tree."""
        def folder(name):
            path = os.path.normcase(_norm(os.path.join(root, name)) + "/")
            _ensure_dir(path.rstrip("/\\"))
            return path

        chars = folder("characters")
        chess = folder("chess_games")
        piano = folder("piano_songs")
        bgm = folder("custom_bgm")

        try:
            store.MASDockingStation.DEF_STATION_PATH = chars
        except Exception:
            pass
        ds = getattr(store, "mas_docking_station", None)
        if ds is not None:
            try:
                ds.station = chars
                ds.enabled = os.path.isdir(chars.rstrip("/\\"))
            except Exception:
                pass

        try:
            store.mas_chess.CHESS_SAVE_PATH = chess
        except Exception:
            pass

        try:
            store.mas_piano_keys.pnml_basedir = piano
            store.mas_piano_keys.no_pnml_basedir = False
        except Exception:
            pass

        try:
            skip_bgm = False
            try:
                skip_bgm = safe_boot_active()
            except Exception:
                skip_bgm = False
            if skip_bgm:
                hidden = os.path.join(root, "_mas_os_safe_hidden_bgm").replace("\\", "/")
                if not hidden.endswith("/"):
                    hidden += "/"
                store.songs.custom_music_dir = hidden
                store.songs.custom_music_reldir = ""
            else:
                live = bgm.replace("\\", "/")
                if not live.endswith("/"):
                    live += "/"
                store.songs.custom_music_dir = live
                if user_data_is_documents():
                    # ../custom_bgm is filesDir. Play by filename: custom_bgm
                    # is on searchpath, and file_open_callback restores
                    # /storage/... paths that Ren'Py stripped.
                    store.songs.custom_music_reldir = ""
        except Exception:
            pass

    def _rescan_custom_content():
        try:
            sayori = False
            egg = getattr(store, "mas_egg_manager", None)
            if egg is not None and hasattr(egg, "sayori_enabled"):
                sayori = bool(egg.sayori_enabled())
            store.songs.initMusicChoices(sayori)
        except Exception:
            pass
        try:
            store.mas_piano_keys.addCustomSongs()
        except Exception:
            pass

    def user_file_present(filename):
        """mas_utils.is_file_present, but user folders follow user_data_root."""
        if not filename:
            return False
        if not filename.startswith("/"):
            filename = "/" + filename
        root = user_data_root() or store.renpy.config.basedir
        prefixes = (
            "/characters",
            "/custom_bgm",
            "/chess_games",
            "/piano_songs",
            "/log",
        )
        use_user = False
        for pfx in prefixes:
            if filename == pfx or filename.startswith(pfx + "/"):
                use_user = True
                break
        if filename == "/log" or filename.startswith("/log/"):
            base = user_data_dir("log")
            rest = filename[4:]
            filepath = os.path.normcase((base or "") + rest)
        else:
            base = root if use_user else store.renpy.config.basedir
            filepath = os.path.normcase((base or "") + filename)
        try:
            return os.access(filepath, os.F_OK)
        except Exception:
            return False

    _user_loader_installed = False

    def _safe_hidden_user_fs(path):
        try:
            if not safe_boot_active():
                return False
        except Exception:
            return False
        low = (path or "").replace("\\", "/").lower()
        if "/mod_assets/monika/" in low:
            return False
        if "/custom_bgm/" in low or low.endswith("/custom_bgm"):
            return True
        if "/mas_os/" in low or "/custom_wallpaper" in low:
            return True
        if "/game/submods" in low or "/python-packages" in low:
            return True
        if "/mod_assets/" in low:
            return True
        return False

    def _allowed_user_fs(path):
        path = _norm(path)
        if not path:
            return False
        if _safe_hidden_user_fs(path):
            return False
        roots = []
        try:
            root = user_data_root()
            if root:
                roots.append(_norm(root))
        except Exception:
            pass
        try:
            based = _norm(store.renpy.config.basedir)
            if based:
                roots.append(based)
        except Exception:
            pass
        for base in roots:
            if not base:
                continue
            if path == base or path.startswith(base.rstrip("/") + "/"):
                return True
        return False

    def _restore_user_fs(name):
        """
        Ren'Py loader lstrip('/') on Android, so
        /storage/emulated/0/Documents/... becomes storage/emulated/0/...
        and is looked up inside game/. Put the slash back and only
        allow files under the player tree.
        """
        if not name:
            return None
        try:
            name = name.replace("\\", "/")
        except Exception:
            pass
        candidates = [name]
        if not name.startswith("/"):
            low = name.lower()
            if (
                low.startswith("storage/")
                or low.startswith("sdcard/")
                or low.startswith("mnt/")
                or low.startswith("data/")
            ):
                candidates.append("/" + name)
        for cand in candidates:
            try:
                if os.path.isfile(cand) and _allowed_user_fs(cand):
                    return cand
            except Exception:
                pass
        return None

    def _user_file_open(name):
        path = _restore_user_fs(name)
        if not path:
            return None
        try:
            return open(path, "rb")
        except Exception:
            return None

    def _user_file_loadable(name):
        return _restore_user_fs(name) is not None

    def _user_asset_search_dirs():
        try:
            if safe_boot_active():
                return []
        except Exception:
            pass
        dirs = []
        for getter in (
            custom_bgm_dir,
            mas_os_wallpapers_dir,
            mas_os_fonts_dir,
            mas_os_textboxes_dir,
        ):
            try:
                path = getter()
            except Exception:
                path = None
            if path:
                dirs.append(_norm(path))
        try:
            tb = mas_os_textboxes_dir()
        except Exception:
            tb = None
        if tb and os.path.isdir(tb):
            try:
                names = os.listdir(tb)
            except Exception:
                names = []
            for name in names:
                sub = os.path.join(tb, name)
                try:
                    if os.path.isdir(sub):
                        dirs.append(_norm(sub))
                except Exception:
                    pass
        return dirs

    def _register_user_asset_searchpath():
        """
        Append player folders after script load so images/audio resolve
        by filename. Do not add mas_os root or неопределено.
        """
        try:
            if safe_boot_active():
                return
        except Exception:
            pass
        try:
            sp = store.renpy.config.searchpath
        except Exception:
            return
        if sp is None:
            return
        for path in _user_asset_search_dirs():
            if not path or not os.path.isdir(path):
                continue
            if path in sp:
                continue
            try:
                sp.append(path)
            except Exception:
                pass

    def _install_user_file_loader():
        """Let Ren'Py open Documents/mas_os files that are not under gamedir."""
        global _user_loader_installed
        _register_user_asset_searchpath()
        if _user_loader_installed:
            return
        try:
            prev_open = store.renpy.config.file_open_callback
            prev_loadable = store.renpy.config.loadable_callback
        except Exception:
            return

        def open_cb(name):
            rv = _user_file_open(name)
            if rv is not None:
                return rv
            if prev_open:
                return prev_open(name)
            return None

        def loadable_cb(name):
            if _user_file_loadable(name):
                return True
            if prev_loadable:
                return prev_loadable(name)
            return False

        store.renpy.config.file_open_callback = open_cb
        store.renpy.config.loadable_callback = loadable_cb
        _user_loader_installed = True

    def apply_user_data_tree():
        """
        Create folders, migrate old Documents layout, retarget MAS.
        Documents is the only copy of gifts and music. Idempotent.
        """
        global _user_data_applied
        root = user_data_root()
        if not root:
            return False
        ensure_user_data_tree()
        _install_user_file_loader()
        _migrate_system_dirname(root)
        _migrate_log_to_root(root)
        if not user_data_is_documents():
            mas = system_root()
            for name in ("archives", "backups", "flags"):
                src = os.path.join(root, name)
                dst = os.path.join(mas, name)
                if os.path.isdir(src) and not _same_path(src, dst):
                    _move_dir_contents(src, dst)
        based = _norm(store.renpy.config.basedir)
        if _norm(root) != based:
            _migrate_basedir_into_root(root)
            _migrate_documents_layout(root)
            _snapshot_logs(root)
            _drop_basedir_mirrors(root)
        _migrate_mas_os_assets(root)
        _sort_mas_os_dumps(root)
        _migrate_textbox_color_folders()
        _write_paths_json(root)
        _retarget_mas_paths(root)
        _register_user_asset_searchpath()
        _ensure_mbase_file()
        _rescan_custom_content()
        _user_data_applied = True
        return True


init 11 python:
    try:
        store.mas_os.apply_user_data_tree()
    except Exception:
        pass
    try:
        _orig_ifp = store.mas_utils.is_file_present

        def _mas_os_is_file_present(filename):
            try:
                return store.mas_os.user_file_present(filename)
            except Exception:
                return _orig_ifp(filename)

        store.mas_utils.is_file_present = _mas_os_is_file_present
    except Exception:
        pass
