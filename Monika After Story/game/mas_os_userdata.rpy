# -*- coding: utf-8 -*-
# MAS OS — live user-data folders (characters, custom_bgm, chess, piano).
#
# Android Documents layout v2 (canonical, no basedir mirrors):
#   Documents/Monika_after_story/
#     saves, characters, custom_bgm, chess_games, piano_songs, game
#     _mas/{archives, backups, log, flags, submods, paths.json}
# PC stays basedir next to DDLC.exe. Internal filesDir is Python/BIOS only.

init -8 python in mas_os:
    import json
    import os
    import shutil
    import store

    LAYOUT_VERSION = 2
    SYSTEM_DIRNAME = "_mas"

    USER_DATA_FOLDERS = (
        "characters",
        "custom_bgm",
        "chess_games",
        "piano_songs",
    )

    USER_DATA_README = (
        "MAS OS — ваши данные\n"
        "====================\n\n"
        "Положите файл в нужную папку. Игра подхватит его "
        "(музыку — после входа в MAS OS или перезапуска).\n"
        "Android: это Documents/Monika_after_story, не папка приложения.\n\n"
        "saves/          сейвы и persistent\n"
        "characters/     подарки .gift, oki doki, imsorry, файл Моники\n"
        "custom_bgm/     своя музыка: ogg, opus, mp3\n"
        "chess_games/    сохранённые партии шахмат (.pgn)\n"
        "piano_songs/    свои ноты пианино (.json)\n"
        "game/           распакованный DDLC, сабмоды, спрайтпаки\n"
        "_mas/           служебное (архивы, логи, бэкапы, установщик)\n"
        "                  сюда руками класть ничего не нужно\n\n"
        "Сабмоды ставятся в game/Submods. Zip качаются в _mas/archives.\n"
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
        if name == "log" and user_data_is_documents():
            return _norm(os.path.join(root, SYSTEM_DIRNAME, "log"))
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
        if user_data_is_documents():
            return _norm(os.path.join(root, SYSTEM_DIRNAME))
        return root

    def archives_dir():
        if user_data_is_documents():
            return _norm(os.path.join(system_root(), "archives"))
        return _norm(os.path.join(user_data_root() or "", "archives"))

    def backups_dir():
        if user_data_is_documents():
            return _norm(os.path.join(system_root(), "backups"))
        return _norm(os.path.join(user_data_root() or "", "backups"))

    def flags_dir():
        if user_data_is_documents():
            return _norm(os.path.join(system_root(), "flags"))
        return _norm(os.path.join(user_data_root() or "", "flags"))

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

    def _write_readme(root):
        path = os.path.join(root, "README_MAS_OS.txt")
        try:
            if os.path.isfile(path):
                return
            handle = open(path, "wb")
            handle.write(USER_DATA_README.encode("utf-8"))
            handle.close()
        except Exception:
            pass

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
        if getattr(store.renpy, "android", False) and user_data_is_documents():
            for name in ("saves", "game"):
                _ensure_dir(os.path.join(root, name))
            _ensure_dir(system_root())
            _touch_nomedia(root)
            _touch_nomedia(system_root())
            for name in USER_DATA_FOLDERS + ("saves", "game"):
                _touch_nomedia(os.path.join(root, name))
        elif getattr(store.renpy, "android", False):
            _touch_nomedia(root)
            for name in USER_DATA_FOLDERS:
                _touch_nomedia(os.path.join(root, name))
        _write_readme(root)
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
        dest_log = os.path.join(root, SYSTEM_DIRNAME, "log")
        for name in ("traceback.txt", "log.txt", "masrun"):
            _copy_newer(os.path.join(based, name), os.path.join(dest_log, name))

    def _same_path(a, b):
        return _norm(a) == _norm(b) and bool(a)

    def _is_meta_name(name):
        return name in (".nomedia", "README.txt", "README_MAS_OS.txt")

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

    def _migrate_documents_layout(root):
        """Old v1 Documents tree → v2 (_mas). Idempotent."""
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
            (os.path.join(root, "log"), os.path.join(mas, "log")),
            (os.path.join(root, "flags"), os.path.join(mas, "flags")),
            (os.path.join(root, "submods_installed"), os.path.join(sm, "installed")),
            (os.path.join(root, "submod_vanilla"), os.path.join(sm, "vanilla")),
            (os.path.join(root, "submod_payloads"), os.path.join(sm, "payloads")),
            (os.path.join(root, "submod_backups"), os.path.join(sm, "backups")),
            (os.path.join(root, "Transfer"), arch),
        )
        for src, dst in pairs:
            _move_dir_contents(src, dst)
        logd = os.path.join(mas, "log")
        flags = os.path.join(mas, "flags")
        _move_one_file(os.path.join(root, "launcher.log"), os.path.join(logd, "launcher.log"))
        _move_one_file(os.path.join(root, "traceback.txt"), os.path.join(logd, "traceback.txt"))
        _move_one_file(
            os.path.join(root, ".mas_force_monika_home"),
            os.path.join(flags, ".mas_force_monika_home"),
        )
        _move_one_file(
            os.path.join(root, "mas_os_safe_mode"),
            os.path.join(flags, "mas_os_safe_mode"),
        )

    def _write_paths_json(root):
        if not root or not user_data_is_documents():
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
            "system": _norm(mas),
            "archives": _norm(os.path.join(mas, "archives")),
            "backups": _norm(os.path.join(mas, "backups")),
            "log": _norm(os.path.join(mas, "log")),
            "flags": _norm(os.path.join(mas, "flags")),
            "submods": _norm(os.path.join(mas, "submods")),
        }
        path = os.path.join(mas, "paths.json")
        _ensure_dir(mas)
        try:
            handle = open(path, "wb")
            handle.write(json.dumps(blob, indent=2, sort_keys=True).encode("utf-8"))
            handle.close()
        except Exception:
            pass
        based = _norm(store.renpy.config.basedir)
        if based and based != _norm(root):
            try:
                handle = open(os.path.join(based, "mas_paths.json"), "wb")
                handle.write(json.dumps(blob, indent=2, sort_keys=True).encode("utf-8"))
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
        dest_log = os.path.join(root, SYSTEM_DIRNAME, "log")
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
            live = bgm.replace("\\", "/")
            if not live.endswith("/"):
                live += "/"
            store.songs.custom_music_dir = live
            if user_data_is_documents():
                # ../custom_bgm resolves to filesDir, not Documents.
                store.songs.custom_music_reldir = live
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
        based = _norm(store.renpy.config.basedir)
        if _norm(root) != based:
            _migrate_basedir_into_root(root)
            _migrate_documents_layout(root)
            _snapshot_logs(root)
            _write_paths_json(root)
            _retarget_mas_paths(root)
            _drop_basedir_mirrors(root)
        else:
            _retarget_mas_paths(root)
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
