# -*- coding: utf-8 -*-
# MAS OS — live user-data folders (characters, custom_bgm, chess, piano, log).
#
# RG Android ports look "synced" because those folders ARE config.basedir:
# Android/data/<pkg>/files/{characters,custom_bgm,chess_games,piano_songs,log,saves}.
# MAS already reads them from basedir. No extra daemon.
#
# When Documents is the save root, basedir stays the app overlay (game/,
# stockfish, submods). User-facing data moves to Documents/Monika_after_story
# so a file manager can drop music or gifts without digging in Android/data.

init -8 python in mas_os:
    import os
    import shutil
    import store

    USER_DATA_FOLDERS = (
        "characters",
        "custom_bgm",
        "chess_games",
        "piano_songs",
        "log",
    )

    USER_DATA_README = (
        "MAS OS — ваши данные\n"
        "====================\n\n"
        "Положите файл в нужную папку. Игра подхватит его "
        "(музыку — после входа в MAS OS или перезапуска).\n\n"
        "characters/     подарки .gift, oki doki, imsorry\n"
        "custom_bgm/     своя музыка: ogg, opus, mp3\n"
        "chess_games/    сохранённые партии шахмат (.pgn)\n"
        "piano_songs/    свои ноты пианино (.json)\n"
        "log/            копии логов\n\n"
        "persistent лежит в этой же папке (или в saves/, если так "
        "настроил движок). Сабмоды — в game/Submods, не здесь.\n"
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

    def ensure_user_data_tree():
        """Create the live folders. Safe to call often."""
        root = user_data_root()
        if not root:
            return False
        _ensure_dir(root)
        for name in USER_DATA_FOLDERS:
            _ensure_dir(os.path.join(root, name))
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
        for name in ("traceback.txt", "log.txt", "masrun"):
            _copy_newer(os.path.join(based, name), os.path.join(root, name))

    def _mirror_music_for_engine(root):
        """
        Ren'Py plays custom_bgm via ../custom_bgm relative to game/.
        Keep a copy next to basedir so the audio loader sees the files.
        Canonical copy for the player is still Documents/custom_bgm.
        """
        based = _norm(store.renpy.config.basedir)
        if not based:
            return
        src = os.path.join(root, "custom_bgm")
        dst = os.path.join(based, "custom_bgm")
        _ensure_dir(src)
        _ensure_dir(dst)
        if _norm(src) == _norm(dst):
            return
        _merge_dir(src, dst)
        # Engine-created nothing here; player files win from Documents.

    def _snapshot_logs(root):
        based_log = os.path.join(_norm(store.renpy.config.basedir), "log")
        dest_log = os.path.join(root, "log")
        if _norm(based_log) == _norm(dest_log):
            return
        _merge_dir(based_log, dest_log)
        _copy_newer(
            os.path.join(_norm(store.renpy.config.basedir), "traceback.txt"),
            os.path.join(root, "traceback.txt"),
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
            # Scan + play: scan the live folder; play still uses ../custom_bgm
            # after the basedir mirror.
            store.songs.custom_music_dir = bgm.replace("\\", "/")
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
        base = root if use_user else store.renpy.config.basedir
        filepath = os.path.normcase((base or "") + filename)
        try:
            return os.access(filepath, os.F_OK)
        except Exception:
            return False

    def apply_user_data_tree():
        """
        Create folders, migrate from the app dir, retarget MAS, mirror music.
        Idempotent.
        """
        global _user_data_applied
        root = user_data_root()
        if not root:
            return False
        ensure_user_data_tree()
        based = _norm(store.renpy.config.basedir)
        if _norm(root) != based:
            _migrate_basedir_into_root(root)
            _mirror_music_for_engine(root)
            _snapshot_logs(root)
        _retarget_mas_paths(root)
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
