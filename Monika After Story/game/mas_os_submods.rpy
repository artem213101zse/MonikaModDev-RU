# -*- coding: utf-8 -*-
# MAS OS — submod manager: disk list, catalog JSON, overlay/submod install, safe mode.

default persistent._mas_os_catalog_url = "https://raw.githubusercontent.com/artem213101zse/mas-os-submods/main/index.json"
default persistent._mas_os_sm_installs = []

init -5 python in mas_os:
    import os
    import re
    import json
    import threading
    import store
    try:
        import time
    except Exception:
        time = None

    try:
        import zipfile
    except Exception:
        zipfile = None

    try:
        import shutil
    except Exception:
        shutil = None

    SM_ZIP_MAX = 96 * 1024 * 1024
    SM_JSON_MAX = 512 * 1024
    SM_FILE_MAX = 24 * 1024 * 1024
    SM_TOTAL_MAX = 140 * 1024 * 1024
    SM_FILES_MAX = 4000

    CATALOG_DEFAULT = (
        "https://raw.githubusercontent.com/artem213101zse/mas-os-submods/main/index.json"
    )

    sm_status = ""
    sm_log = []
    sm_busy = False
    sm_tab = "installed"
    sm_catalog = None
    sm_cat_name = ""
    sm_cat_updated = ""
    sm_url_typing = False
    sm_direct_typing = False
    sm_direct = ""
    sm_need_reboot = False

    def catalog_url():
        url = getattr(store.persistent, "_mas_os_catalog_url", None) or CATALOG_DEFAULT
        url = unicode(url).strip()
        if not url:
            return CATALOG_DEFAULT
        return url

    def set_catalog_url(url):
        url = (url or "").strip()
        if not url:
            url = CATALOG_DEFAULT
        store.persistent._mas_os_catalog_url = url
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        return None

    def set_sm_tab(tab):
        global sm_tab
        if tab in ("installed", "catalog", "safe"):
            sm_tab = tab
        return None

    def start_sm_url_typing():
        global sm_url_typing
        sm_url_typing = True
        iv = getattr(store.mas_os, "sm_url_iv", None)
        if iv is not None:
            iv.default = True
        return None

    def stop_sm_url_typing():
        global sm_url_typing
        sm_url_typing = False
        iv = getattr(store.mas_os, "sm_url_iv", None)
        if iv is not None:
            iv.default = False
        return None

    def start_sm_direct_typing():
        global sm_direct_typing
        sm_direct_typing = True
        iv = getattr(store.mas_os, "sm_direct_iv", None)
        if iv is not None:
            iv.default = True
        return None

    def stop_sm_direct_typing():
        global sm_direct_typing
        sm_direct_typing = False
        iv = getattr(store.mas_os, "sm_direct_iv", None)
        if iv is not None:
            iv.default = False
        return None

    def disabled_dir():
        return os.path.join(game_dir(), "Submods_disabled")

    def _sm_off_paths():
        paths = [
            os.path.join(game_dir(), "mas_os_submods_off.txt"),
            os.path.join(game_dir(), "game", "mas_os_submods_off.txt"),
        ]
        try:
            if user_data_is_documents():
                root = user_data_root()
                if root:
                    paths.append(os.path.join(root, "_mas", "flags", "submods_off.txt"))
        except Exception:
            pass
        return paths

    def sm_off_names():
        names = set()
        for path in _sm_off_paths():
            if not path or not os.path.isfile(path):
                continue
            try:
                handle = open(path, "r")
                try:
                    for line in handle:
                        name = (line or "").strip()
                        if not name or name.startswith("#"):
                            continue
                        names.add(name.replace("\\", "/").split("/")[-1].lower())
                finally:
                    handle.close()
            except Exception:
                pass
        return names

    def _write_sm_off(names):
        body = "\n".join(sorted(names))
        if body:
            body += "\n"
        data = body.encode("utf-8")
        for path in _sm_off_paths():
            parent = os.path.dirname(path)
            if parent and not os.path.isdir(parent):
                try:
                    os.makedirs(parent)
                except Exception:
                    continue
            try:
                handle = open(path, "wb")
                handle.write(data)
                handle.close()
            except Exception:
                pass
        return None

    def _restore_parked_submods():
        src = disabled_dir()
        dst = submods_dir()
        if not os.path.isdir(src):
            return
        _move_merge(src, dst)

    def safe_flag_path(sticky=False):
        name = "mas_os_safe_mode_on" if sticky else "mas_os_safe_mode"
        return os.path.join(game_dir(), name)

    def safe_mode_sticky():
        return os.path.isfile(safe_flag_path(True))

    def safe_mode_pending():
        return os.path.isfile(safe_flag_path(False))

    def request_safe_mode(sticky=False):
        global sm_status, sm_need_reboot
        path = safe_flag_path(False)
        try:
            with open(path, "w") as handle:
                handle.write("1\n")
        except Exception as err:
            sm_status = "Не удалось записать флаг: {0}".format(err)
            return None
        if sticky:
            try:
                with open(safe_flag_path(True), "w") as handle:
                    handle.write("1\n")
            except Exception:
                pass
        sm_status = "В следующий запуск скрипты Submods не загрузятся. Папки на месте. Нажми Перезагрузка."
        sm_need_reboot = True
        return None

    def clear_safe_mode():
        global sm_status, sm_need_reboot
        for sticky in (True, False):
            path = safe_flag_path(sticky)
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        sm_status = "Безопасный режим снят. Папки на месте, скрипты снова грузятся. Нужен перезапуск."
        sm_need_reboot = True
        return None

    def _move_merge(src, dst):
        if not os.path.isdir(src):
            return
        if not os.path.exists(dst):
            parent = os.path.dirname(dst)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            os.rename(src, dst)
            return
        if not os.path.isdir(dst):
            return
        for name in os.listdir(src):
            s = os.path.join(src, name)
            d = os.path.join(dst, name)
            if os.path.exists(d):
                base, ext = os.path.splitext(name)
                n = 2
                while os.path.exists(d):
                    d = os.path.join(dst, "{0}_{1}{2}".format(base, n, ext))
                    n += 1
            os.rename(s, d)
        try:
            os.rmdir(src)
        except Exception:
            pass

    def _list_folders(path):
        if not path or not os.path.isdir(path):
            return []
        try:
            names = os.listdir(path)
        except Exception:
            return []
        out = []
        for name in names:
            if name.startswith("."):
                continue
            full = os.path.join(path, name)
            if os.path.isdir(full) or name.lower().endswith(".rpy"):
                out.append(name)
        out.sort(key=lambda n: n.lower())
        return out

    def sm_loaded_map():
        out = {}
        smap = getattr(store.mas_submod_utils, "submod_map", {}) or {}
        for sm in smap.itervalues():
            out[sm.name] = sm
        return out

    def sm_installed_rows():
        loaded = sm_loaded_map()
        active = _list_folders(submods_dir())
        off = sm_off_names()
        rows = []
        seen = set()
        for sm in loaded.itervalues():
            folder = _guess_folder(sm.name, active)
            rows.append({
                "key": sm.name,
                "title": sm.name,
                "version": sm.version,
                "author": sm.author,
                "desc": sm.description or "",
                "state": "loaded",
                "folder": folder,
                "place": "active",
            })
            if folder:
                seen.add(folder.lower())
        for name in active:
            if name.lower() in seen:
                continue
            if name.lower() in off:
                rows.append({
                    "key": "off:" + name,
                    "title": name,
                    "version": "",
                    "author": "",
                    "desc": "Выключен: папка на месте, скрипты не грузятся.",
                    "state": "disabled",
                    "folder": name,
                    "place": "active",
                })
                seen.add(name.lower())
                continue
            rows.append({
                "key": "disk:" + name,
                "title": name,
                "version": "",
                "author": "",
                "desc": "Папка на диске, но MAS её не зарегистрировал (нет Submod(...) или ошибка init).",
                "state": "orphan",
                "folder": name,
                "place": "active",
            })
        rows.sort(key=lambda r: (r["state"] != "loaded", r["title"].lower()))
        return rows

    def _guess_folder(name, folders):
        if not name:
            return None
        want = name.lower().replace(" ", "")
        for folder in folders:
            key = folder.lower().replace(" ", "").replace("_", "")
            if key == want or folder.lower() == name.lower():
                return folder
        return None

    def sm_disable(folder):
        global sm_status, sm_need_reboot
        if not folder:
            return None
        name = os.path.basename(folder)
        names = sm_off_names()
        names.add(name.lower())
        _write_sm_off(names)
        sm_status = "«{0}» выключен, папка на месте. Нужен перезапуск.".format(folder)
        sm_need_reboot = True
        return None

    def sm_enable(folder):
        global sm_status, sm_need_reboot
        if not folder:
            return None
        name = os.path.basename(folder).lower()
        names = sm_off_names()
        if name in names:
            names.remove(name)
        _write_sm_off(names)
        sm_status = "«{0}» включён. Нужен перезапуск.".format(folder)
        sm_need_reboot = True
        return None

    def sm_open_bios_uninstall():
        global sm_status
        if getattr(store.renpy, "android", False):
            open_bios("library")
            return None
        sm_status = "Снятие пака — в BIOS, на ПК удали папку из game/Submods."
        return None

    def sm_delete(folder, place="active"):
        global sm_status, sm_need_reboot
        if getattr(store.renpy, "android", False):
            return sm_open_bios_uninstall()
        if not folder:
            return None
        name = os.path.basename(folder)
        msg = _uninstall_manifest(_manifest_id_for_folder(name))
        root = submods_dir() if place != "disabled" else disabled_dir()
        path = os.path.join(root, name)
        leftover = False
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    if shutil is None:
                        raise Exception("shutil нет")
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                leftover = True
            except Exception as err:
                if not msg:
                    sm_status = "Не удалось удалить: {0}".format(err)
                    return None
        _forget_install(name)
        if msg:
            sm_status = msg
        elif leftover:
            sm_status = "Удалено: {0}. Если были файлы в mod_assets — проверь Склад / файлы.".format(folder)
        else:
            sm_status = "Уже удалено."
        sm_need_reboot = True
        return None

    def _forget_install(name):
        recs = list(getattr(store.persistent, "_mas_os_sm_installs", None) or [])
        keep = []
        for rec in recs:
            if (rec.get("name") or "").lower() == (name or "").lower():
                continue
            keep.append(rec)
        store.persistent._mas_os_sm_installs = keep
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def _record_install(name, layout, paths, sid="", added=None, replaced=None):
        recs = list(getattr(store.persistent, "_mas_os_sm_installs", None) or [])
        recs.insert(0, {
            "name": name,
            "layout": layout,
            "id": sid,
            "paths": list(paths)[:400],
            "added": list(added or [])[:400],
            "replaced": list(replaced or [])[:400],
        })
        store.persistent._mas_os_sm_installs = recs[:40]
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def _sm_sideload_root():
        try:
            if user_data_is_documents():
                root = user_data_root()
                if root:
                    return _norm(root)
        except Exception:
            pass
        return game_dir()

    def _sm_system_root():
        try:
            if user_data_is_documents():
                root = user_data_root()
                if root:
                    return os.path.join(root, "_mas", "submods")
        except Exception:
            pass
        return _sm_sideload_root()

    def _sm_manifest_dir():
        if user_data_is_documents():
            return os.path.join(_sm_system_root(), "installed")
        return os.path.join(_sm_sideload_root(), "submods_installed")

    def _sm_backup_root():
        if user_data_is_documents():
            return os.path.join(_sm_system_root(), "backups")
        return os.path.join(_sm_sideload_root(), "submod_backups")

    def _sm_vanilla_root():
        if user_data_is_documents():
            return os.path.join(_sm_system_root(), "vanilla")
        return os.path.join(_sm_sideload_root(), "submod_vanilla")

    def _sm_payload_root():
        if user_data_is_documents():
            return os.path.join(_sm_system_root(), "payloads")
        return os.path.join(_sm_sideload_root(), "submod_payloads")

    def _sm_vanilla_file(kind, rel):
        return os.path.join(_sm_vanilla_root(), kind, rel.replace("/", os.sep))

    def _sm_payload_file(sid, kind, rel):
        return os.path.join(_sm_payload_root(), sid, kind, rel.replace("/", os.sep))

    def _sm_iter_manifests(except_id=None):
        dirn = _sm_manifest_dir()
        if not os.path.isdir(dirn):
            return
        try:
            names = os.listdir(dirn)
        except Exception:
            return
        for name in names:
            if not name.endswith(".json"):
                continue
            oid = name[:-5]
            if except_id and oid == except_id:
                continue
            path = os.path.join(dirn, name)
            try:
                man = _sm_read_json(path)
            except Exception:
                continue
            man["_id"] = man.get("id") or oid
            man["_mtime"] = os.path.getmtime(path)
            yield man

    def _sm_safe_id(name):
        text = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "submod").lower())
        return (text[:40] or "submod")

    def _sm_write_json(path, obj):
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        raw = json.dumps(obj, ensure_ascii=True)
        if isinstance(raw, unicode):
            raw = raw.encode("utf-8")
        handle = open(path, "wb")
        try:
            handle.write(raw)
        finally:
            handle.close()

    def _sm_read_json(path):
        handle = open(path, "rb")
        try:
            raw = handle.read()
        finally:
            handle.close()
        return json.loads(raw)

    def _sm_copy_file(src, dst):
        folder = os.path.dirname(dst)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        if shutil is not None:
            shutil.copy2(src, dst)
            return
        data = open(src, "rb").read()
        out = open(dst, "wb")
        try:
            out.write(data)
        finally:
            out.close()

    def _sm_prune_empty(path, stop):
        cursor = path
        stop_n = _norm(stop) if stop else ""
        while cursor:
            if not os.path.isdir(cursor):
                break
            if stop_n and _norm(cursor) == stop_n:
                break
            try:
                kids = os.listdir(cursor)
            except Exception:
                break
            if kids:
                break
            parent = os.path.dirname(cursor)
            try:
                os.rmdir(cursor)
            except Exception:
                break
            cursor = parent

    def _sm_classify(rels):
        sub = 0
        sprite = 0
        asset = 0
        rpy_n = 0
        gift_n = 0
        for rel in rels or []:
            low = (rel or "").replace("\\", "/").lower()
            leaf = low.split("/")[-1]
            if (
                leaf.endswith((".rpy", ".rpym"))
                or "/submods/" in low
                or low.startswith("submods/")
            ):
                sub += 4
                if leaf.endswith((".rpy", ".rpym")):
                    rpy_n += 1
            if (
                "mod_assets/monika/" in low
                or "/monika/j/" in low
                or "/monika/c/" in low
                or "/monika/a/" in low
                or "/monika/h/" in low
                or "/monika/f/" in low
                or "/hair/" in low
                or "/clothes/" in low
                or "/acs/" in low
                or leaf.startswith(("hair-", "acs-", "clothes-"))
            ):
                sprite += 3
            if leaf.endswith(".json"):
                sprite += 2
            if leaf.endswith(".gift"):
                gift_n += 1
                sprite += 2
            mapped = _KNOWN_ASSETS.get(leaf)
            if mapped:
                asset += 5
            elif leaf.endswith((".png", ".jpg", ".jpeg", ".webp", ".ogg", ".mp3", ".wav")):
                asset += 1
        if sub > 0:
            if rpy_n <= 2 and sprite >= 8:
                return "spritepack"
            return "submod"
        if gift_n and sprite >= 2:
            return "spritepack"
        if sprite >= 3 and sprite >= asset:
            return "spritepack"
        if asset > 0:
            return "assetpack"
        return "submod"

    def _sm_looks_sprite(rels):
        json = False
        art = False
        gift = False
        for rel in rels or []:
            low = (rel or "").replace("\\", "/").lower()
            if (
                "mod_assets/monika/j/" in low
                or "/monika/j/" in low
                or "mod_assets/monika/c/" in low
                or "mod_assets/monika/a/" in low
                or "mod_assets/monika/h/" in low
            ):
                return True
            if low.endswith(".json"):
                json = True
            if low.endswith((".png", ".jpg", ".jpeg", ".webp")):
                art = True
            leaf = low.split("/")[-1]
            if leaf.endswith(".gift") or ("." not in leaf and leaf):
                gift = True
        return json and (art or gift)

    def _sm_looks_submod(rels):
        for rel in rels or []:
            low = (rel or "").replace("\\", "/").lower()
            if "/submods/" in low or low.startswith("submods/") or low.endswith(".rpy") or low.endswith(".rpym"):
                return True
        return False

    _KNOWN_ASSETS = {
        "pong.png": "mod_assets/games/pong/pong.png",
        "pong_field.png": "mod_assets/games/pong/pong_field.png",
        "pong_ball.png": "mod_assets/games/pong/pong_ball.png",
        "chess_board.png": "mod_assets/games/chess/chess_board.png",
        "piano.png": "mod_assets/games/piano/piano.png",
        "board.png": "mod_assets/games/piano/board.png",
    }

    def _sm_looks_asset(rels):
        art = 0
        for rel in rels or []:
            leaf = (rel or "").replace("\\", "/").split("/")[-1].lower()
            if leaf.endswith((".rpy", ".rpym", ".json")):
                return False
            if leaf.endswith((".png", ".jpg", ".jpeg", ".webp", ".ogg", ".mp3", ".wav")):
                art += 1
        return art > 0

    def _sm_map_asset(rel):
        r = (rel or "").replace("\\", "/").lstrip("/")
        leaf = r.split("/")[-1]
        mapped = _KNOWN_ASSETS.get(leaf.lower())
        if mapped:
            return mapped
        low = r.lower()
        if low.startswith(("mod_assets/", "gui/", "images/")):
            return r
        if leaf.lower().startswith("hm_") and leaf.lower().endswith(".png"):
            return "mod_assets/games/hangman/" + leaf
        root = writable_gamedir() or os.path.join(game_dir(), "game")
        hits = []
        try:
            for dirpath, _dirnames, filenames in os.walk(root):
                for name in filenames:
                    if name.lower() == leaf.lower():
                        full = os.path.join(dirpath, name)
                        rel_out = os.path.relpath(full, root).replace("\\", "/")
                        hits.append(rel_out)
                        if len(hits) > 1:
                            break
                if len(hits) > 1:
                    break
        except Exception:
            hits = []
        if len(hits) == 1:
            return hits[0]
        return None

    def _sm_peel_markers(rel):
        r = (rel or "").replace("\\", "/").lstrip("/")
        low = r.lower()
        markers = (
            "/game/submods/", "/game/mod_assets/", "/game/python-packages/",
            "/game/gui/",
            "game/submods/", "game/mod_assets/", "game/python-packages/",
            "game/gui/",
            "/submods/", "/mod_assets/", "/python-packages/",
            "/characters/", "characters/",
            "/custom_bgm/", "/chess_games/", "/piano_songs/",
        )
        for m in markers:
            if m.startswith("/"):
                idx = low.find(m)
                if idx >= 0:
                    return r[idx + 1:]
            elif low.startswith(m):
                return r
        return r

    def _sm_dest_for(rel, pack, as_sprite=False, as_asset=False):
        r = _sm_peel_markers(rel)
        low = r.lower()
        if low.startswith("game/"):
            r = r[5:]
            low = r.lower()
        if not r:
            return None, None
        for top in ("characters/", "custom_bgm/", "chess_games/", "piano_songs/", "saves/"):
            if low.startswith(top):
                return "docs", r
        if low.startswith("submods/"):
            rest = r.split("/", 1)
            if len(rest) < 2 or not rest[1]:
                return None, None
            return "game", "Submods/" + rest[1]
        if (
            low.startswith("mod_assets/")
            or low.startswith("python-packages/")
            or low.startswith("gui/")
        ):
            return "game", r
        if as_sprite:
            if low.startswith(("j/", "a/", "c/", "h/", "f/", "t/")):
                return "game", "mod_assets/monika/" + r
            if low.endswith(".json"):
                return "game", "mod_assets/monika/j/" + r.split("/")[-1]
            leaf = r.split("/")[-1]
            if leaf.lower().endswith(".gift") or ("." not in leaf):
                return "docs", "characters/" + leaf
            if leaf.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                return "game", "mod_assets/monika/" + r
            return "game", "mod_assets/monika/" + pack + "/" + r
        if as_asset:
            mapped = _sm_map_asset(r)
            if mapped:
                return "game", mapped
            return None, None
        return "game", "Submods/" + pack + "/" + r

    def _sm_dest_file(kind, rel):
        if kind == "docs":
            base = _sm_sideload_root()
        else:
            base = writable_gamedir() or os.path.join(game_dir(), "game")
        return os.path.normpath(os.path.join(base, rel.replace("/", os.sep)))

    def _sm_inside(root, target):
        root_l = os.path.normpath(root).replace("\\", "/").lower()
        target_l = os.path.normpath(target).replace("\\", "/").lower()
        return target_l == root_l or target_l.startswith(root_l + "/")

    def _parse_dest_key(key):
        text = key or ""
        if ":" in text:
            kind, rel = text.split(":", 1)
            return kind, rel
        return "game", text

    def _manifest_id_for_folder(folder):
        sid = _sm_safe_id(folder)
        path = os.path.join(_sm_manifest_dir(), sid + ".json")
        if os.path.isfile(path):
            return sid
        dirn = _sm_manifest_dir()
        if not os.path.isdir(dirn):
            return sid
        want = (folder or "").lower()
        try:
            names = os.listdir(dirn)
        except Exception:
            return sid
        for name in names:
            if not name.endswith(".json"):
                continue
            try:
                man = _sm_read_json(os.path.join(dirn, name))
            except Exception:
                continue
            pack = unicode(man.get("pack") or "").lower()
            if pack == want:
                return name[:-5]
        return sid

    def _uninstall_manifest(sid):
        if not sid:
            return ""
        man_file = os.path.join(_sm_manifest_dir(), sid + ".json")
        if not os.path.isfile(man_file):
            return ""
        try:
            man = _sm_read_json(man_file)
        except Exception as err:
            return "Манифест не прочитан: {0}".format(err)
        backup_dir = os.path.join(_sm_backup_root(), sid)
        payload_dir = os.path.join(_sm_payload_root(), sid)
        deleted = 0
        restored = 0
        keys = list(man.get("added") or []) + list(man.get("replaced") or [])
        seen = {}
        for key in keys:
            if key in seen:
                continue
            seen[key] = True
            kind, rel = _parse_dest_key(key)
            target = _sm_dest_file(kind, rel)
            other_pay = None
            best_at = -1
            for other in _sm_iter_manifests(sid):
                owned = list(other.get("added") or []) + list(other.get("replaced") or [])
                if key not in owned:
                    continue
                cand = _sm_payload_file(other.get("_id") or "", kind, rel)
                if not os.path.isfile(cand):
                    continue
                at = other.get("installedAt") or other.get("_mtime") or 0
                try:
                    at = float(at)
                except Exception:
                    at = 0
                if other_pay is None or at >= best_at:
                    other_pay = cand
                    best_at = at
            if other_pay and os.path.isfile(other_pay):
                try:
                    _sm_copy_file(other_pay, target)
                    restored += 1
                except Exception:
                    pass
                continue
            vanilla = _sm_vanilla_file(kind, rel)
            if os.path.isfile(vanilla):
                try:
                    _sm_copy_file(vanilla, target)
                    restored += 1
                except Exception:
                    pass
                continue
            if os.path.isfile(target):
                try:
                    os.remove(target)
                    deleted += 1
                except Exception:
                    pass
            try:
                parent = os.path.dirname(target)
                name = os.path.basename(target)
                if name.endswith(".rpy") or name.endswith(".rpym"):
                    twin = os.path.join(parent, name + "c")
                    if os.path.isfile(twin):
                        os.remove(twin)
                        deleted += 1
            except Exception:
                pass
            stop = _sm_sideload_root() if kind == "docs" else (
                writable_gamedir() or os.path.join(game_dir(), "game")
            )
            _sm_prune_empty(os.path.dirname(target), stop)
        packs = {}
        man_pack = man.get("pack") or sid
        if man_pack:
            packs[man_pack] = True
        for key in keys:
            kind, rel = _parse_dest_key(key)
            if kind != "game":
                continue
            low = (rel or "").replace("\\", "/").lower()
            if not low.startswith("submods/"):
                continue
            rest = rel.replace("\\", "/")[len("Submods/"):] if rel.replace("\\", "/").lower().startswith("submods/") else ""
            pack = rest.split("/")[0] if rest else ""
            if pack:
                packs[pack] = True
        root = writable_gamedir() or os.path.join(game_dir(), "game")
        for pack in packs:
            owned = False
            prefix = "game:Submods/" + pack
            for other in _sm_iter_manifests(sid):
                owned_keys = list(other.get("added") or []) + list(other.get("replaced") or [])
                for ok in owned_keys:
                    if ok == prefix or ok.startswith(prefix + "/") or ok.lower().startswith(prefix.lower() + "/"):
                        owned = True
                        break
                if owned:
                    break
            if owned:
                continue
            folder = os.path.join(root, "Submods", pack)
            if shutil is not None and os.path.isdir(folder):
                try:
                    shutil.rmtree(folder)
                except Exception:
                    pass
        if shutil is not None:
            for folder in (backup_dir, payload_dir):
                if os.path.isdir(folder):
                    try:
                        shutil.rmtree(folder)
                    except Exception:
                        pass
        try:
            os.remove(man_file)
        except Exception:
            pass
        return "Сабмод «{0}» снят: удалено {1}, возвращено {2}.".format(
            man.get("pack") or sid, deleted, restored
        )

    def sm_log_clear():
        global sm_log, sm_status
        sm_log = []
        sm_status = ""

    def sm_log_line(msg):
        global sm_log, sm_status
        text = unicode(msg)
        sm_status = text
        safe = text.replace("{", "{{").replace("[", "[[")
        sm_log.append(safe)
        if len(sm_log) > 120:
            sm_log = sm_log[-120:]

    def _github_zip(url):
        url = (url or "").strip()
        m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
        if m:
            return "https://github.com/{0}/{1}/archive/refs/heads/main.zip".format(
                m.group(1), m.group(2)
            )
        m = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/?$",
            url,
        )
        if m:
            return "https://github.com/{0}/{1}/archive/refs/heads/{2}.zip".format(
                m.group(1), m.group(2), m.group(3)
            )
        return url

    def _install_candidates(url):
        """
        GitHub /releases/download/ 302s to a signed CDN URL.
        Keep the original first; if that body is HTML, try tag archives.
        """
        url = (url or "").strip()
        out = []
        seen = set()

        def _add(item):
            item = (item or "").strip()
            if not item or item in seen:
                return
            seen.add(item)
            out.append(item)

        rewritten = _github_zip(url)
        rewritten = _rewrite_url(rewritten) or rewritten
        _add(rewritten)
        m = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/releases/download/([^/]+)/(.+)$",
            url.split("#")[0],
        )
        if m:
            owner, repo, tag, _fname = m.group(1), m.group(2), m.group(3), m.group(4)
            _add("https://github.com/{0}/{1}/archive/refs/tags/{2}.zip".format(
                owner, repo, tag
            ))
            _add("https://codeload.github.com/{0}/{1}/zip/refs/tags/{2}".format(
                owner, repo, tag
            ))
            _add("https://github.com/{0}/{1}/archive/{2}.zip".format(owner, repo, tag))
        m = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/releases/tag/([^/]+)/?$",
            url.split("#")[0],
        )
        if m:
            owner, repo, tag = m.group(1), m.group(2), m.group(3)
            _add("https://github.com/{0}/{1}/archive/refs/tags/{2}.zip".format(
                owner, repo, tag
            ))
            _add("https://codeload.github.com/{0}/{1}/zip/refs/tags/{2}".format(
                owner, repo, tag
            ))
        return out

    def _zip_prefix(paths):
        if not paths:
            return ""
        tops = []
        for p in paths:
            part = p.split("/")[0]
            if part and part not in tops:
                tops.append(part)
        if len(tops) != 1:
            return ""
        top = tops[0]
        if top.lower() in (
            "game", "submods", "mod_assets", "python-packages", "gui",
            "characters", "custom_bgm", "chess_games", "piano_songs", "saves",
        ):
            return ""
        return top + "/"

    def _classify_paths(rels):
        overlay = False
        sub_root = False
        for p in rels:
            pl = p.lower()
            if (
                pl.startswith("game/submods/")
                or pl.startswith("game/mod_assets/")
                or pl.startswith("game/python-packages/")
            ):
                overlay = True
            if pl.startswith("submods/"):
                sub_root = True
        if overlay:
            return "overlay"
        if sub_root:
            return "submods_root"
        return "loose"

    def _overlay_ok(rel):
        pl = rel.replace("\\", "/").lower()
        if pl.startswith("game/"):
            rest = pl[5:]
        else:
            rest = pl
        for allow in ("submods/", "mod_assets/", "python-packages/"):
            if rest.startswith(allow):
                return True
        return False

    def _peel_zip_rel(name):
        """
        Extra Plus etc. wrap files in 'ExtraPlus 1.1.1 - MAS 12.6 and above/game/...'.
        Return a path starting at game/, submods/, mod_assets/ or python-packages/.
        """
        pl = (name or "").replace("\\", "/").lstrip("/")
        if not pl:
            return ""
        low = pl.lower()
        for marker in (
            "/game/submods/",
            "/game/mod_assets/",
            "/game/python-packages/",
            "/game/gui/",
        ):
            idx = low.find(marker)
            if idx >= 0:
                return pl[idx + 1:]
        for marker in (
            "game/submods/",
            "game/mod_assets/",
            "game/python-packages/",
            "game/gui/",
        ):
            if low.startswith(marker):
                return pl
        for marker in ("/submods/", "/mod_assets/", "/python-packages/"):
            idx = low.find(marker)
            if idx >= 0:
                return pl[idx + 1:]
        for marker in ("submods/", "mod_assets/", "python-packages/"):
            if low.startswith(marker):
                return pl
        return pl

    def _zip_payload(data):
        if not data:
            return data
        if data[:2] == "PK":
            return data
        if data[:3] == "\xef\xbb\xbf" and data[3:5] == "PK":
            return data[3:]
        idx = data.find("PK\x03\x04")
        if idx > 0 and idx < 2048:
            return data[idx:]
        return data

    def install_submod_zip(data, display_name="submod.zip", kind_hint="auto", log=None):
        """
        Inspect a zip and install as overlay (game/ merge) or Submods pack.
        RETURNS: (ok, message, written_paths)
        """
        def _log(msg):
            if log:
                try:
                    log(msg)
                except Exception:
                    pass

        if zipfile is None and struct is None:
            return False, "zip не поддерживается", []
        data = _zip_payload(data)
        _log("открываю zip: {0}, {1}".format(display_name, _magic_desc(data)))
        try:
            members = _zip_list_members(data, log=_log)
        except Exception as err:
            msg = "это не zip: {0} ({1})".format(err, _magic_desc(data))
            _log(msg)
            return False, msg, []
        infos = []
        total = 0
        for name, raw in members:
            name = name.replace("\\", "/").lstrip("/")
            if not name or name.endswith("/"):
                continue
            if ".." in name.split("/"):
                return False, "в архиве путь с .. — отказ", []
            size = len(raw or "")
            if size > SM_FILE_MAX:
                return False, "файл в архиве больше {0} МБ: {1}".format(
                    SM_FILE_MAX / (1024 * 1024), name
                )
            total += size
            if total > SM_TOTAL_MAX:
                return False, "архив слишком большой в распаковке", []
            infos.append((name, raw))
            if len(infos) > SM_FILES_MAX:
                return False, "слишком много файлов в архиве", []
        if not infos:
            return False, "архив пустой", []
        peeled = []
        for name, raw in infos:
            rel = _peel_zip_rel(name)
            if not rel:
                rel = name.replace("\\", "/").lstrip("/")
            peeled.append((rel, raw, name))
        rels = [r for r, _raw, _orig in peeled if r]
        prefix = _zip_prefix(rels)
        if prefix:
            new_rels = []
            new_peeled = []
            for rel, raw, orig in peeled:
                if rel.startswith(prefix):
                    rel = rel[len(prefix):]
                if not rel:
                    continue
                new_rels.append(rel)
                new_peeled.append((rel, raw, orig))
            rels = new_rels
            peeled = new_peeled
        layout = _classify_paths(rels)
        if kind_hint == "overlay" and layout == "loose":
            layout = "overlay"
        _log("в архиве {0} файлов, префикс «{1}», раскладка {2}".format(
            len(peeled), prefix.rstrip("/") if prefix else "нет", layout
        ))
        sample = rels[:8]
        for rel in sample:
            _log("  в архиве: {0}".format(rel))
        if len(rels) > 8:
            _log("  … ещё {0} путей".format(len(rels) - 8))
        root = os.path.normpath((writable_gamedir() or os.path.join(game_dir(), "game")).replace("/", os.sep))
        pack = os.path.splitext(os.path.basename(display_name or "submod"))[0]
        pack = re.sub(r"(?i)-(main|master)$", "", pack)
        pack = re.sub(r"[^A-Za-z0-9._\-]+", "_", pack)[:40] or "submod"
        if prefix:
            pref = re.sub(r"(?i)-(main|master)$", "", prefix.rstrip("/"))
            pref = re.sub(r"[^A-Za-z0-9._\-]+", "_", pref)[:40]
            if pref:
                pack = pref
        sid = _sm_safe_id(pack)
        guessed = _sm_classify(rels)
        as_sprite = guessed == "spritepack"
        as_asset = guessed == "assetpack"
        _log("тип пака: {0}".format(guessed))
        if kind_hint == "spritepack":
            as_sprite = True
            as_asset = False
        elif kind_hint == "assetpack":
            as_sprite = False
            as_asset = True
        old = _uninstall_manifest(sid)
        if old:
            _log(old)
        _log("пишем в game={0}".format(root))
        written = []
        added = []
        replaced = []
        skipped = 0
        count = 0
        dest_folders = []
        for rel, raw, _orig in peeled:
            if not rel:
                continue
            low = rel.replace("\\", "/").lower()
            if (
                low.startswith("__macosx/")
                or "/__macosx/" in low
                or low.endswith(".ds_store")
                or "/.git/" in low
                or low.startswith(".git/")
            ):
                skipped += 1
                continue
            kind, dest_rel = _sm_dest_for(rel, pack, as_sprite, as_asset)
            if not kind or not dest_rel:
                skipped += 1
                continue
            target = _sm_dest_file(kind, dest_rel)
            base = _sm_sideload_root() if kind == "docs" else root
            if not _sm_inside(base, target):
                skipped += 1
                continue
            folder = os.path.dirname(target)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            key = kind + ":" + dest_rel
            if os.path.isfile(target):
                vanilla = _sm_vanilla_file(kind, dest_rel)
                owned = False
                for other in _sm_iter_manifests(sid):
                    owned_keys = list(other.get("added") or []) + list(other.get("replaced") or [])
                    if key in owned_keys:
                        owned = True
                        break
                if not os.path.isfile(vanilla) and not owned:
                    _sm_copy_file(target, vanilla)
                bak = os.path.join(_sm_backup_root(), sid, kind, dest_rel.replace("/", os.sep))
                if not os.path.isfile(bak):
                    _sm_copy_file(target, bak)
                replaced.append(key)
            else:
                added.append(key)
            handle = open(target, "wb")
            try:
                handle.write(raw)
            finally:
                handle.close()
            try:
                _sm_copy_file(target, _sm_payload_file(sid, kind, dest_rel))
            except Exception:
                pass
            count += 1
            written.append(target)
            top = dest_rel.split("/")[0]
            if top and top not in dest_folders:
                dest_folders.append(top)
            if count <= 20:
                _log("  + {0}".format(target))
            elif count == 21:
                _log("  … остальные файлы пишу без построчного вывода")
        if count <= 0:
            _log("ни одного разрешённого файла (нужны Submods / mod_assets / python-packages / рескин)")
            return False, "ни одного разрешённого файла (нужны Submods / mod_assets / python-packages / рескин картинок)", []
        extra = ""
        if skipped:
            extra = " Пропущено {0} файлов вне разрешённых папок.".format(skipped)
            _log("пропущено {0} файлов".format(skipped))
        man = {
            "id": sid,
            "name": display_name,
            "pack": pack,
            "added": added,
            "replaced": replaced,
            "files": count,
            "installedAt": int(time.time() * 1000) if time else 0,
            "kind": "spritepack" if as_sprite else ("assetpack" if as_asset else "submod"),
        }
        try:
            _sm_write_json(os.path.join(_sm_manifest_dir(), sid + ".json"), man)
        except Exception as err:
            _log("манифест не записался: {0}".format(err))
        _record_install(display_name, layout, written, sid, added, replaced)
        _inventory_add("submod", [os.path.basename(p) for p in written[:8]])
        where = (", ".join(dest_folders[:6]) if dest_folders else "game")
        msg = "Установлено {0} файлов ({1}) → {2}. Новых {3}, заменено (бекап) {4}.{5} Перезапусти оболочку.".format(
            count, layout, where, len(added), len(replaced), extra
        )
        _log(msg)
        return True, msg, written

    def _parse_catalog(raw):
        try:
            data = json.loads(raw)
        except Exception:
            return None, "индекс не JSON"
        if not isinstance(data, dict):
            return None, "корень индекса должен быть объектом"
        items = data.get("items") or data.get("submods")
        if not isinstance(items, list):
            return None, "нет списка items"
        out = []
        for row in items:
            if not isinstance(row, dict):
                continue
            sid = unicode(row.get("id") or "").strip()
            name = unicode(row.get("name") or sid).strip()
            url = unicode(row.get("url") or "").strip()
            if not sid or not url:
                continue
            if not (url.startswith("http://") or url.startswith("https://")):
                continue
            kind = unicode(row.get("kind") or "auto").strip().lower()
            if kind not in ("auto", "overlay", "submod"):
                kind = "auto"
            out.append({
                "id": sid[:64],
                "name": name[:80],
                "author": unicode(row.get("author") or "")[:60],
                "version": unicode(row.get("version") or "")[:20],
                "description": unicode(row.get("description") or "")[:400],
                "mas": unicode(row.get("mas") or "")[:20],
                "url": url[:500],
                "kind": kind,
                "notes": unicode(row.get("notes") or "")[:240],
            })
        meta = {
            "name": unicode(data.get("name") or "Каталог")[:80],
            "updated": unicode(data.get("updated") or "")[:32],
            "items": out,
        }
        return meta, None

    def fetch_catalog():
        global sm_busy, sm_status, sm_catalog, sm_cat_name, sm_cat_updated
        if sm_busy:
            return None
        sm_busy = True
        sm_status = "Загружаю индекс…"
        worker = threading.Thread(target=_catalog_worker)
        worker.daemon = True
        worker.start()
        return None

    def _catalog_worker():
        global sm_busy, sm_status, sm_catalog, sm_cat_name, sm_cat_updated
        try:
            url = _rewrite_url(catalog_url())
            pack = _http_get(url, max_bytes=SM_JSON_MAX)
            if not pack:
                raise Exception("пустой ответ")
            raw = pack[0]
            if raw.lstrip()[:1] not in ("{", "["):
                raise Exception("это не JSON (проверь raw-ссылку, не github.com/blob)")
            meta, err = _parse_catalog(raw)
            if err:
                raise Exception(err)
            sm_catalog = meta.get("items") or []
            sm_cat_name = meta.get("name") or ""
            sm_cat_updated = meta.get("updated") or ""
            sm_status = "Индекс: {0} ({1} шт.)".format(
                sm_cat_name or "каталог",
                len(sm_catalog),
            )
        except Exception as err:
            sm_catalog = []
            sm_status = "Индекс не открылся: {0}. Репозиторий можно создать позже — пока ставь по прямой ссылке.".format(err)
        sm_busy = False

    def start_sm_install(url, kind_hint="auto"):
        global sm_busy, sm_status
        if getattr(store.renpy, "android", False):
            sm_status = "На телефоне паки ставит BIOS → Контент."
            open_bios("content")
            return None
        if sm_busy:
            return None
        url = (url or "").strip()
        if not url:
            sm_status = "Нет ссылки."
            return None
        sm_log_clear()
        sm_busy = True
        sm_status = "Скачиваю сабмод…"
        sm_log_line("Старт установки…")
        worker = threading.Thread(target=_sm_install_worker, args=(url, kind_hint))
        worker.daemon = True
        worker.start()
        return None

    def start_direct_install():
        stop_sm_direct_typing()
        return start_sm_install(sm_direct, "auto")

    def _sm_install_worker(url, kind_hint):
        global sm_busy, sm_status, sm_need_reboot
        try:
            sm_log_line("1. Исходная ссылка:")
            sm_log_line("   {0}".format(url))
            sm_log_line("   kind_hint={0}".format(kind_hint))
            candidates = _install_candidates(url)
            if "yadi.sk" in (url or "") or "disk.yandex." in (url or ""):
                sm_log_line("2. Яндекс.Диск: спрашиваю прямой href")
                href = _yandex_direct(url)
                if not href:
                    raise Exception("Яндекс.Диск не отдал файл")
                sm_log_line("   href={0}".format(href[:220]))
                candidates = [href] + [c for c in candidates if c != href]
            sm_log_line("2. Варианты URL ({0}):".format(len(candidates)))
            for i, cand in enumerate(candidates):
                sm_log_line("   [{0}] {1}".format(i + 1, cand[:220]))

            last_err = None
            used = set()
            idx = 0
            while idx < len(candidates):
                cand = candidates[idx]
                idx += 1
                if cand in used:
                    continue
                used.add(cand)
                sm_log_line("3. Скачиваю вариант {0}/{1}".format(len(used), max(len(candidates), len(used))))
                try:
                    pack = _http_get(cand, max_bytes=SM_ZIP_MAX, log=sm_log_line)
                except Exception as err:
                    last_err = err
                    sm_log_line("   скачивание не вышло: {0}".format(err))
                    continue
                if not pack:
                    last_err = Exception("пустой ответ")
                    sm_log_line("   пустой ответ")
                    continue
                data, header_name, _meta = pack
                if not data:
                    last_err = Exception("пустой файл")
                    sm_log_line("   тело пустое")
                    continue

                if _looks_like_html(data):
                    sm_log_line("   это HTML/XML, не архив")
                    extracted = _html_direct_url(data)
                    if extracted and extracted not in used:
                        sm_log_line("   в странице есть прямая ссылка, добавляю в очередь")
                        sm_log_line("   {0}".format(extracted[:220]))
                        candidates.append(extracted)
                    last_err = Exception("пришла страница, не zip")
                    continue

                name = dl_guess_name(cand, header_name)
                ext = os.path.splitext(name)[1].lower()
                sm_log_line("4. Имя файла: {0}  расширение: {1}".format(name, ext or "нет"))
                sm_log_line("   {0}".format(_magic_desc(data)))

                is_zip = ext == ".zip" or _looks_like_zip(data)
                if ext == ".rpy" and not is_zip:
                    folder = submods_dir()
                    sm_log_line("5. Это .rpy → {0}".format(folder))
                    if not os.path.isdir(folder):
                        os.makedirs(folder)
                        sm_log_line("   создал папку Submods")
                    path = os.path.join(folder, os.path.basename(name))
                    with open(path, "wb") as handle:
                        handle.write(data)
                    _record_install(name, "loose", [path])
                    sm_need_reboot = True
                    sm_log_line("Готово: положен {0}".format(path))
                    sm_status = "Положен {0} в Submods. Перезапусти оболочку.".format(name)
                    sm_busy = False
                    return

                if is_zip:
                    sm_log_line("5. Распаковка zip")
                    ok, msg, paths = install_submod_zip(
                        data, name, kind_hint, log=sm_log_line
                    )
                    if ok:
                        sm_need_reboot = True
                        if paths:
                            sm_log_line("первый путь: {0}".format(paths[0]))
                            sm_log_line("последний путь: {0}".format(paths[-1]))
                        sm_status = msg
                        sm_busy = False
                        return
                    last_err = Exception(msg)
                    sm_log_line("   zip не принят, пробую следующий URL")
                    continue

                last_err = Exception("нужен .zip или .rpy, пришло {0}".format(ext or "без расширения"))
                sm_log_line("   {0}".format(last_err))

            if last_err:
                raise last_err
            raise Exception("не удалось скачать ни по одному URL")
        except Exception as err:
            sm_log_line("ОШИБКА: {0}".format(err))
            sm_status = "Установка не вышла: {0}".format(err)
        sm_busy = False


init python:
    class MASOSCatUrlInputValue(InputValue):
        default = False
        editable = True
        returnable = True

        def get_text(self):
            return store.mas_os.catalog_url()

        def set_text(self, value):
            store.mas_os.set_catalog_url(value)

        def enter(self):
            store.mas_os.stop_sm_url_typing()
            store.mas_os.fetch_catalog()
            return None

    class MASOSDirectInputValue(InputValue):
        default = False
        editable = True
        returnable = True

        def get_text(self):
            return store.mas_os.sm_direct or ""

        def set_text(self, value):
            store.mas_os.sm_direct = value

        def enter(self):
            store.mas_os.start_direct_install()
            return None


init 1 python:
    store.mas_os.sm_url_iv = MASOSCatUrlInputValue()
    store.mas_os.sm_direct_iv = MASOSDirectInputValue()
    try:
        store.mas_os._restore_parked_submods()
    except Exception:
        pass


screen mas_os_submods():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ tab = store.mas_os.sm_tab
    $ rows = store.mas_os.sm_installed_rows()
    $ cat = store.mas_os.sm_catalog
    $ status = store.mas_os.sm_status
    $ log_lines = store.mas_os.sm_log or []
    $ busy = store.mas_os.sm_busy
    $ sticky = store.mas_os.safe_mode_sticky()
    $ pending = store.mas_os.safe_mode_pending()
    $ need = store.mas_os.sm_need_reboot
    $ url_typing = store.mas_os.sm_url_typing
    $ dir_typing = store.mas_os.sm_direct_typing
    $ cat_url = store.mas_os.catalog_url()
    $ direct = store.mas_os.sm_direct or ""

    use mas_os_bg

    if busy:
        timer 0.4 repeat True action Function(store.mas_os.setup_recheck)

    text _("Сабмоды") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text _("Список и вкл/выкл без переезда папки. На телефоне ставить и снимать паки — BIOS."):
        style "mas_os_hint"
        xpos 48
        ypos 56

    hbox:
        xpos 48
        ypos 88
        spacing 8

        textbutton _("На диске"):
            style "mas_os_cat_btn"
            xsize 180
            selected (tab == "installed")
            action Function(store.mas_os.set_sm_tab, "installed")

        textbutton _("Каталог"):
            style "mas_os_cat_btn"
            xsize 180
            selected (tab == "catalog")
            action [
                Function(store.mas_os.set_sm_tab, "catalog"),
                Function(store.mas_os.fetch_catalog),
            ]

        textbutton _("Безопасный режим"):
            style "mas_os_cat_btn"
            xsize 220
            selected (tab == "safe")
            action Function(store.mas_os.set_sm_tab, "safe")

    if status:
        text status:
            style "mas_os_body"
            xpos 48
            ypos 128
            xsize 1180
            substitute False

    if need:
        textbutton _("Перезагрузить оболочку"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 900
            ypos 84
            xsize 280
            action Function(store.mas_os.reboot_shell)

    $ list_y = 168 if status else 140

    if tab == "installed":
        viewport:
            xpos 48
            ypos list_y
            xysize (1184, 460)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 8
                xsize 1140

                if rows:
                    for row in rows:
                        frame:
                            style "mas_os_panel"
                            background Solid(store.mas_os.theme_color("panel2"))
                            xsize 1140
                            padding (14, 10)

                            hbox:
                                spacing 12
                                xfill True

                                vbox:
                                    xsize 720
                                    spacing 2

                                    hbox:
                                        spacing 8

                                        if row["state"] == "loaded":
                                            frame:
                                                xysize (10, 10)
                                                background Solid("#3DFF9A")
                                                yalign 0.5
                                        elif row["state"] == "disabled":
                                            frame:
                                                xysize (10, 10)
                                                background Solid("#C989A8")
                                                yalign 0.5
                                        else:
                                            frame:
                                                xysize (10, 10)
                                                background Solid("#FFC43A")
                                                yalign 0.5

                                        text row["title"]:
                                            style "mas_os_subtitle"
                                            substitute False

                                    if row["version"] or row["author"]:
                                        text "v{0}  —  {1}".format(row["version"] or "?", row["author"] or "?"):
                                            style "mas_os_hint"
                                            substitute False

                                    text row["desc"]:
                                        style "mas_os_hint"
                                        xsize 700
                                        substitute False

                                hbox:
                                    spacing 6
                                    yalign 0.5

                                    if row["state"] == "disabled":
                                        textbutton _("Вкл"):
                                            style "mas_os_nav_btn"
                                            text_style "mas_os_nav_btn_text"
                                            xsize 100
                                            action Function(store.mas_os.sm_enable, row["folder"])
                                    elif row["folder"]:
                                        textbutton _("Выкл"):
                                            style "mas_os_nav_btn"
                                            text_style "mas_os_nav_btn_text"
                                            xsize 100
                                            action Function(store.mas_os.sm_disable, row["folder"])

                                    if row["folder"]:
                                        if renpy.android:
                                            textbutton _("BIOS"):
                                                style "mas_os_nav_btn"
                                                text_style "mas_os_nav_btn_text"
                                                xsize 120
                                                action Function(store.mas_os.sm_open_bios_uninstall)
                                        else:
                                            textbutton _("Удалить"):
                                                style "mas_os_nav_btn"
                                                text_style "mas_os_nav_btn_text"
                                                xsize 120
                                                action Show(
                                                    "mas_os_confirm",
                                                    message="Удалить «{0}» с диска?".format(row["folder"]),
                                                    yes_action=[
                                                        Function(store.mas_os.sm_delete, row["folder"], row["place"]),
                                                        Hide("mas_os_confirm"),
                                                    ],
                                                    no_action=Hide("mas_os_confirm"),
                                                )
                else:
                    text _("Папка Submods пустая, ничего не загружено."):
                        style "mas_os_hint"

                if renpy.android:
                    textbutton _("Поставить / снять в BIOS"):
                        style "mas_os_button"
                        text_style "mas_os_button_text"
                        xsize 720
                        action Function(store.mas_os.open_bios, "content")
                else:
                    use mas_os_store_link("submod", "submods", 720)

    elif tab == "catalog":
        viewport:
            xpos 48
            ypos list_y
            xysize (1184, 460)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 10
                xsize 1140

                if renpy.android:
                    text _("На телефоне zip ставит BIOS (Контент). Каталог здесь — справочник, кнопка «Ставить» откроет BIOS."):
                        style "mas_os_body"
                        xsize 1140

                    textbutton _("Открыть BIOS → Контент"):
                        style "mas_os_button"
                        text_style "mas_os_button_text"
                        xsize 480
                        action Function(store.mas_os.open_bios, "content")

                text _("Ссылка на index.json (raw GitHub). По умолчанию — репозиторий порта, можно заменить на свой."):
                    style "mas_os_hint"
                    xsize 1140

                hbox:
                    spacing 8

                    if url_typing:
                        input:
                            value store.mas_os.sm_url_iv
                            copypaste True
                            length 4000
                            color store.mas_os.theme_color("input")
                            size 16
                            xsize 640
                            yalign 0.5
                    else:
                        button:
                            style "mas_os_gift_field"
                            xsize 640
                            ysize 40
                            action [
                                Function(store.mas_os.start_sm_url_typing),
                                store.mas_os.sm_url_iv.Enable(),
                            ]

                            text cat_url:
                                style "mas_os_hint"
                                size 14
                                yalign 0.5
                                substitute False

                    textbutton _("Вставить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 140
                        action Function(store.mas_os.paste_url_into, "sm_url")

                    textbutton _("Обновить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 160
                        action [
                            Function(store.mas_os.stop_sm_url_typing),
                            Function(store.mas_os.fetch_catalog),
                        ]

                text _("Прямая ссылка на zip / .rpy / GitHub-репозиторий, если индекса нет или ты знаешь что ставишь."):
                    style "mas_os_hint"

                hbox:
                    spacing 8

                    if dir_typing:
                        input:
                            value store.mas_os.sm_direct_iv
                            copypaste True
                            length 4000
                            color store.mas_os.theme_color("input")
                            size 16
                            xsize 640
                            yalign 0.5
                    else:
                        button:
                            style "mas_os_gift_field"
                            xsize 640
                            ysize 40
                            action [
                                Function(store.mas_os.start_sm_direct_typing),
                                store.mas_os.sm_direct_iv.Enable(),
                            ]

                            if direct:
                                text direct:
                                    style "mas_os_body"
                                    size 15
                                    yalign 0.5
                                    substitute False
                            else:
                                text _("Нажми или Вставить"):
                                    style "mas_os_hint"
                                    size 15
                                    yalign 0.5

                    textbutton _("Вставить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 140
                        action Function(store.mas_os.paste_url_into, "sm_direct")

                    textbutton _("Установить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 180
                        sensitive (not busy)
                        action Function(store.mas_os.start_direct_install)

                if log_lines or busy:
                    frame:
                        style "mas_os_panel"
                        background Solid(store.mas_os.theme_color("panel2"))
                        xsize 1140
                        padding (12, 8)

                        vbox:
                            spacing 3
                            xsize 1110

                            text _("Лог установки — по шагам, URL, пути, magic байты"):
                                style "mas_os_subtitle"

                            if busy:
                                text _("… работаю, лог обновляется …"):
                                    style "mas_os_hint"

                            for line in log_lines:
                                text line:
                                    style "mas_os_hint"
                                    size 13
                                    xsize 1100
                                    substitute False

                if cat:
                    for item in cat:
                        frame:
                            style "mas_os_panel"
                            background Solid(store.mas_os.theme_color("panel2"))
                            xsize 1140
                            padding (14, 10)

                            hbox:
                                spacing 12

                                vbox:
                                    xsize 860
                                    spacing 2

                                    text item["name"]:
                                        style "mas_os_subtitle"
                                        substitute False

                                    text "v{0}  —  {1}  ·  {2}".format(
                                        item.get("version") or "?",
                                        item.get("author") or "?",
                                        item.get("kind") or "auto",
                                    ):
                                        style "mas_os_hint"
                                        substitute False

                                    text item.get("description") or "":
                                        style "mas_os_hint"
                                        xsize 840
                                        substitute False

                                    if item.get("notes"):
                                        text item["notes"]:
                                            style "mas_os_hint"
                                            xsize 840
                                            substitute False

                                textbutton _("Ставить"):
                                    style "mas_os_nav_btn"
                                    text_style "mas_os_nav_btn_text"
                                    xsize 140
                                    yalign 0.5
                                    sensitive (not busy)
                                    action Function(
                                        store.mas_os.start_sm_install,
                                        item["url"],
                                        item.get("kind") or "auto",
                                    )
                else:
                    text _("Индекса пока нет или он не загрузился. Это нормально, пока репозиторий не создан. Пример схемы — game/mod_assets/mas_os/catalog_example.json."):
                        style "mas_os_hint"
                        xsize 1140

    else:
        viewport:
            xpos 48
            ypos list_y
            xysize (1184, 460)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 1140

                text _("Если сабмод валит загрузку, Ren'Py падает до оболочки. Безопасный режим не трогает папки: скрипты Submods просто не грузятся. Выкл на карточке пишет имя в список, папка остаётся. Снимать пак с диска на телефоне — BIOS → Библиотека."):
                    style "mas_os_body"
                    xsize 1140

                if sticky:
                    text _("Сейчас включён постоянный безопасный режим: скрипты Submods не грузятся."):
                        style "mas_os_subtitle"
                elif pending:
                    text _("Флаг на один запуск уже записан. Перезапусти оболочку."):
                        style "mas_os_subtitle"
                else:
                    text _("Сейчас обычный режим: Submods грузятся как всегда."):
                        style "mas_os_hint"

                textbutton _("Следующий запуск без сабмодов"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize 720
                    action Show(
                        "mas_os_confirm",
                        message=_("Записать флаг и перезапустить?\nСкрипты Submods не загрузятся на этот запуск, папки останутся."),
                        yes_action=[
                            Function(store.mas_os.request_safe_mode, False),
                            Hide("mas_os_confirm"),
                            Function(store.mas_os.reboot_shell),
                        ],
                        no_action=Hide("mas_os_confirm"),
                    )

                textbutton _("Держать выключенными, пока не верну"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize 720
                    action Show(
                        "mas_os_confirm",
                        message=_("Постоянный безопасный режим: сабмоды не грузятся, пока не нажмёшь «Вернуть»."),
                        yes_action=[
                            Function(store.mas_os.request_safe_mode, True),
                            Hide("mas_os_confirm"),
                            Function(store.mas_os.reboot_shell),
                        ],
                        no_action=Hide("mas_os_confirm"),
                    )

                textbutton _("Вернуть сабмоды"):
                    style "mas_os_button"
                    text_style "mas_os_button_text"
                    xsize 720
                    action [
                        Function(store.mas_os.clear_safe_mode),
                    ]

                text _("Выкл не переносит папку. Картинки Extra Plus в mod_assets остаются — скрипты уже не грузятся. Полное снятие на телефоне — BIOS."):
                    style "mas_os_hint"
                    xsize 1140

    if not store.mas_os.wm_embedded():
        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 48
            ypos 640
            action [
                Function(store.mas_os.stop_sm_url_typing),
                Function(store.mas_os.stop_sm_direct_typing),
                Return("back"),
            ]

        key "K_ESCAPE" action [
            Function(store.mas_os.stop_sm_url_typing),
            Function(store.mas_os.stop_sm_direct_typing),
            Return("back"),
        ]
        key "K_AC_BACK" action If(
            store.mas_os.sm_url_typing or store.mas_os.sm_direct_typing,
            [
                store.mas_os.sm_url_iv.Disable(),
                store.mas_os.sm_direct_iv.Disable(),
                Function(store.mas_os.stop_sm_url_typing),
                Function(store.mas_os.stop_sm_direct_typing),
            ],
            Return("back"),
        )
