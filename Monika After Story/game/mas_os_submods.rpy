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
        sm_status = "В следующий запуск папка Submods будет отключена. Нажми Перезагрузка."
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
        src = disabled_dir()
        dst = submods_dir()
        if os.path.isdir(src):
            _move_merge(src, dst)
        sm_status = "Безопасный режим снят. Включенные папки возвращены в game/Submods. Нужен перезапуск."
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
        parked = _list_folders(disabled_dir())
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
        for name in parked:
            rows.append({
                "key": "off:" + name,
                "title": name,
                "version": "",
                "author": "",
                "desc": "Выключен: лежит в Submods_disabled рядом с папкой game.",
                "state": "disabled",
                "folder": name,
                "place": "disabled",
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
        src = os.path.join(submods_dir(), os.path.basename(folder))
        dst = os.path.join(disabled_dir(), os.path.basename(folder))
        if not os.path.exists(src):
            sm_status = "Папки уже нет в Submods."
            return None
        try:
            if not os.path.isdir(disabled_dir()):
                os.makedirs(disabled_dir())
            if os.path.exists(dst):
                sm_status = "В выключенных уже есть «{0}».".format(folder)
                return None
            os.rename(src, dst)
        except Exception as err:
            sm_status = "Не удалось выключить: {0}".format(err)
            return None
        sm_status = "«{0}» выключен. Нужен перезапуск.".format(folder)
        sm_need_reboot = True
        return None

    def sm_enable(folder):
        global sm_status, sm_need_reboot
        if not folder:
            return None
        src = os.path.join(disabled_dir(), os.path.basename(folder))
        dst = os.path.join(submods_dir(), os.path.basename(folder))
        if not os.path.exists(src):
            sm_status = "Папки нет среди выключенных."
            return None
        try:
            if not os.path.isdir(submods_dir()):
                os.makedirs(submods_dir())
            if os.path.exists(dst):
                sm_status = "В Submods уже есть «{0}».".format(folder)
                return None
            os.rename(src, dst)
        except Exception as err:
            sm_status = "Не удалось включить: {0}".format(err)
            return None
        sm_status = "«{0}» включён. Нужен перезапуск.".format(folder)
        sm_need_reboot = True
        return None

    def sm_delete(folder, place="active"):
        global sm_status, sm_need_reboot
        if not folder:
            return None
        root = submods_dir() if place != "disabled" else disabled_dir()
        path = os.path.join(root, os.path.basename(folder))
        if not os.path.exists(path):
            sm_status = "Уже удалено."
            return None
        try:
            if os.path.isdir(path):
                if shutil is None:
                    raise Exception("shutil нет")
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as err:
            sm_status = "Не удалось удалить: {0}".format(err)
            return None
        _forget_install(os.path.basename(folder))
        sm_status = "Удалено: {0}. Если были файлы в mod_assets — проверь Склад / файлы.".format(folder)
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

    def _record_install(name, layout, paths):
        recs = list(getattr(store.persistent, "_mas_os_sm_installs", None) or [])
        recs.insert(0, {
            "name": name,
            "layout": layout,
            "paths": list(paths)[:400],
        })
        store.persistent._mas_os_sm_installs = recs[:40]
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

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
        if top.lower() in ("game", "submods", "mod_assets", "python-packages"):
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

        if zipfile is None:
            return False, "zip не поддерживается", []
        import StringIO
        data = _zip_payload(data)
        _log("открываю zip: {0}, {1}".format(display_name, _magic_desc(data)))
        try:
            zf = zipfile.ZipFile(StringIO.StringIO(data))
        except Exception as err:
            msg = "это не zip: {0} ({1})".format(err, _magic_desc(data))
            _log(msg)
            return False, msg, []
        infos = []
        total = 0
        for info in zf.infolist():
            name = info.filename.replace("\\", "/").lstrip("/")
            if not name or name.endswith("/"):
                continue
            if ".." in name.split("/"):
                return False, "в архиве путь с .. — отказ", []
            if info.file_size > SM_FILE_MAX:
                return False, "файл в архиве больше 12 МБ: {0}".format(name), []
            total += info.file_size
            if total > SM_TOTAL_MAX:
                return False, "архив слишком большой в распаковке", []
            infos.append((info, name))
            if len(infos) > SM_FILES_MAX:
                return False, "слишком много файлов в архиве", []
        if not infos:
            return False, "архив пустой", []
        raw_paths = [n for _i, n in infos]
        prefix = _zip_prefix(raw_paths)
        rels = []
        for _info, name in infos:
            rel = name
            if prefix and rel.startswith(prefix):
                rel = rel[len(prefix):]
            if not rel:
                continue
            rels.append(rel)
        layout = _classify_paths(rels)
        if kind_hint == "overlay" and layout == "loose":
            layout = "overlay"
        _log("в архиве {0} файлов, префикс «{1}», раскладка {2}".format(
            len(infos), prefix.rstrip("/") if prefix else "нет", layout
        ))
        sample = rels[:8]
        for rel in sample:
            _log("  в архиве: {0}".format(rel))
        if len(rels) > 8:
            _log("  … ещё {0} путей".format(len(rels) - 8))
        based = game_dir()
        gamed = os.path.join(based, "game")
        _log("basedir={0}".format(based))
        _log("game={0}".format(gamed))
        written = []
        skipped = 0
        count = 0
        for info, name in infos:
            rel = name
            if prefix and rel.startswith(prefix):
                rel = rel[len(prefix):]
            if not rel:
                continue
            if layout == "overlay":
                if not _overlay_ok(rel):
                    skipped += 1
                    continue
                if rel.lower().startswith("game/"):
                    target = os.path.normpath(os.path.join(based, rel))
                else:
                    target = os.path.normpath(os.path.join(gamed, rel))
                root = os.path.normpath(gamed)
            elif layout == "submods_root":
                if not rel.lower().startswith("submods/"):
                    skipped += 1
                    continue
                target = os.path.normpath(os.path.join(gamed, rel))
                root = os.path.normpath(os.path.join(gamed, "Submods"))
            else:
                folder = os.path.splitext(os.path.basename(display_name or "submod"))[0]
                folder = re.sub(r"[^A-Za-z0-9._\-]+", "_", folder)[:40] or "submod"
                target = os.path.normpath(os.path.join(gamed, "Submods", folder, rel))
                root = os.path.normpath(os.path.join(gamed, "Submods"))
            if not target.startswith(os.path.normpath(gamed) + os.sep) and target != os.path.normpath(gamed):
                skipped += 1
                continue
            folder = os.path.dirname(target)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            with open(target, "wb") as handle:
                handle.write(zf.read(info.filename))
            count += 1
            written.append(target)
            if count <= 20:
                _log("  + {0}".format(target))
            elif count == 21:
                _log("  … остальные файлы пишу без построчного вывода")
        if count <= 0:
            _log("ни одного разрешённого файла (нужны Submods / mod_assets / python-packages)")
            return False, "ни одного разрешённого файла (нужны Submods / mod_assets / python-packages)", []
        extra = ""
        if skipped:
            extra = " Пропущено {0} файлов вне разрешённых папок.".format(skipped)
            _log("пропущено {0} файлов вне Submods/mod_assets/python-packages".format(skipped))
        _record_install(display_name, layout, written)
        _inventory_add("submod", [os.path.basename(p) for p in written[:8]])
        msg = "Установлено {0} файлов ({1}).{2} Перезапусти оболочку.".format(
            count, layout, extra
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


screen mas_os_submods():
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

    text _("Каталог по JSON, прямая ссылка, выключение папки. После установки — перезапуск."):
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

                text _("Если сабмод валит загрузку, Ren'Py падает до оболочки. Безопасный режим перед следующим стартом уносит game/Submods в папку Submods_disabled рядом с game (не внутри — иначе .rpy всё равно скомпилируются)."):
                    style "mas_os_body"
                    xsize 1140

                if sticky:
                    text _("Сейчас включён постоянный безопасный режим: каждый запуск паркует Submods."):
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
                        message=_("Записать флаг и перезапустить?\nПапка Submods будет отключена на этот запуск."),
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

                text _("Выкл на карточке сабмода переносит только его папку. Extra Plus при этом оставляет картинки в mod_assets — это нормально, скрипты уже не грузятся. Полное удаление — кнопка Удалить."):
                    style "mas_os_hint"
                    xsize 1140

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
