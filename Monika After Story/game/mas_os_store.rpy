# MAS OS — Склад: download player content by URL (GitHub / Drive / Yandex / direct).
# Named "Склад" in the UI: a box for files Android cannot copy by hand.

default persistent._mas_os_dl_history = []
default persistent._mas_os_dl_files = []

init -5 python in mas_os:
    import os
    import re
    import json
    import threading
    import store

    try:
        import urllib2
        import urllib
    except Exception:
        urllib2 = None
        urllib = None

    try:
        import urlparse
    except Exception:
        urlparse = None

    try:
        import ssl as _ssl
    except Exception:
        _ssl = None

    try:
        import zipfile
    except Exception:
        zipfile = None

    try:
        import zlib
    except Exception:
        zlib = None

    DL_MAX = 32 * 1024 * 1024
    DL_TIMEOUT = 90
    DL_UA = (
        "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    )

    dl_url = ""
    dl_kind = "wallpaper"
    dl_status = ""
    dl_typing = False
    dl_busy = False
    dl_last_name = ""
    dl_from = "home"

    DL_KINDS = [
        ("wallpaper", "Обои", "wallpaper", (".png", ".jpg", ".jpeg")),
        ("font", "Шрифты", "font", (".ttf", ".otf")),
        ("music", "Музыка", "sound", (".mp3", ".ogg", ".opus")),
        ("submod", "Сабмоды", "submods", (".rpy", ".zip")),
        ("gift", "Подарки", "gifts", (".gift", ".txt")),
        ("textbox", "Текстбокс", "textbox", (".png",)),
        ("other", "Другое", "save", (".png", ".jpg", ".jpeg", ".ttf", ".otf", ".ogg", ".mp3", ".rpy", ".json", ".zip", ".txt")),
    ]

    def dl_kind_row(kind=None):
        kind = kind or dl_kind
        for row in DL_KINDS:
            if row[0] == kind:
                return row
        return DL_KINDS[0]

    def set_dl_kind(kind):
        global dl_kind
        dl_kind = kind or "wallpaper"

    def open_store(kind, back="home"):
        global dl_from
        set_dl_kind(kind)
        dl_from = back or "home"
        stop_dl_typing()
        return None

    def _dl_protected_names(kind):
        names = set()
        if kind == "wallpaper":
            names.update(("splash.png", "menu.png"))
        elif kind == "font":
            for _fid, _title, path in getattr(store.mas_os, "FONT_PACKS", ()) or ():
                names.add(os.path.basename(path).lower())
            names.update((
                "sourcehansansk-regular.otf",
                "sourcehansanssc-regular.otf",
                "mplus-2p-regular.ttf",
                "mplus-1mn-medium.ttf",
            ))
        elif kind == "textbox":
            for _tid, _title, path in getattr(store.mas_os, "TEXTBOX_COLORS", ()) or ():
                names.add(os.path.basename(path).lower())
            names.update((
                "textbox.png",
                "textbox_d.png",
                "textbox_monika.png",
                "textbox_monika_d.png",
            ))
        return names

    def dl_is_protected(kind, name):
        base = os.path.basename(name or "").lower()
        if not base or base in (".", ".."):
            return True
        return base in _dl_protected_names(kind)

    def _inventory_add(kind, names):
        files = list(getattr(store.persistent, "_mas_os_dl_files", None) or [])
        have = set()
        for rec in files:
            have.add((rec.get("kind"), (rec.get("name") or "").lower()))
        for name in names:
            base = os.path.basename(name or "")
            if not base or dl_is_protected(kind, base):
                continue
            key = (kind, base.lower())
            if key in have:
                continue
            files.insert(0, {"kind": kind, "name": base})
            have.add(key)
        store.persistent._mas_os_dl_files = files[:80]
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def _inventory_remove(kind, name):
        base = os.path.basename(name or "").lower()
        files = []
        for rec in (getattr(store.persistent, "_mas_os_dl_files", None) or []):
            if rec.get("kind") == kind and (rec.get("name") or "").lower() == base:
                continue
            files.append(rec)
        store.persistent._mas_os_dl_files = files
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def _dl_safe_join(folder, name):
        folder = os.path.normpath(folder)
        path = os.path.normpath(os.path.join(folder, os.path.basename(name or "")))
        prefix = folder
        if not prefix.endswith(os.sep):
            prefix = prefix + os.sep
        if path != folder and not path.startswith(prefix):
            return None
        return path

    def dl_list_files(kind=None):
        """
        Player-owned files for this Склад tab. Built-in game assets are skipped.
        """
        kind = kind or dl_kind
        folder = _dl_folder(kind)
        found = {}

        def consider(name):
            base = os.path.basename(name or "")
            if not base or base.startswith("."):
                return
            if dl_is_protected(kind, base):
                return
            path = _dl_safe_join(folder, base)
            if not path or not os.path.exists(path):
                return
            ext = os.path.splitext(base)[1].lower()
            if kind == "gift" and ext not in (".gift",):
                return
            if kind == "music" and ext not in (".mp3", ".ogg", ".opus"):
                return
            if kind == "wallpaper" and ext not in (".png", ".jpg", ".jpeg"):
                return
            if kind == "font" and ext not in (".ttf", ".otf"):
                return
            if kind == "textbox" and ext not in (".png",):
                return
            found[base.lower()] = {
                "kind": kind,
                "name": base,
                "path": path,
                "isdir": os.path.isdir(path),
            }

        scan = kind != "textbox"
        if scan and os.path.isdir(folder):
            try:
                listed = os.listdir(folder)
            except Exception:
                listed = []
            for name in listed:
                consider(name)

        for rec in (getattr(store.persistent, "_mas_os_dl_files", None) or []):
            if rec.get("kind") == kind:
                consider(rec.get("name"))

        rows = list(found.values())
        rows.sort(key=lambda row: row["name"].lower())
        return rows

    def _after_dl_delete(kind, name):
        if kind == "wallpaper":
            if wallpaper_id() == name:
                try:
                    if asset_exists(WP_REL + "/splash.png"):
                        set_wallpaper("splash.png")
                    else:
                        set_wallpaper("solid")
                except Exception:
                    set_wallpaper("solid")
        elif kind == "music":
            try:
                player_rescan()
            except Exception:
                pass
            try:
                cur = player_current_path() or ""
                if name and name in cur:
                    player_stop()
            except Exception:
                pass
        elif kind == "textbox":
            try:
                cur = os.path.basename(textbox_dark_path() or "").lower()
                if cur == (name or "").lower():
                    set_textbox("pink")
            except Exception:
                pass

    def dl_delete(kind, name):
        global dl_status
        if dl_is_protected(kind, name):
            dl_status = "Это файл игры, его нельзя удалить."
            return None
        folder = _dl_folder(kind)
        path = _dl_safe_join(folder, name)
        if not path:
            dl_status = "Некорректный путь."
            return None
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)
            else:
                _inventory_remove(kind, name)
                dl_status = "Файла уже нет: {0}".format(name)
                return None
        except Exception as err:
            dl_status = "Не удалось удалить: {0}".format(err)
            return None
        _inventory_remove(kind, name)
        _after_dl_delete(kind, name)
        dl_status = "Удалено: {0}".format(name)
        return None

    def dl_delete_prompt(name):
        return "Удалить «{0}» со склада? Файлы игры не удаляются.".format(name)

    def start_dl_typing():
        global dl_typing
        dl_typing = True
        iv = getattr(store.mas_os, "dl_iv", None)
        if iv is not None:
            iv.default = True

    def stop_dl_typing():
        global dl_typing
        dl_typing = False
        iv = getattr(store.mas_os, "dl_iv", None)
        if iv is not None:
            iv.default = False

    def _dl_folder(kind):
        based = game_dir()
        root = writable_gamedir()
        mapping = {
            "wallpaper": os.path.join(root, "mod_assets", "mas_os", "wallpapers"),
            "font": os.path.join(root, "mod_assets", "font"),
            "music": os.path.join(based, "custom_bgm"),
            "submod": os.path.join(root, "Submods"),
            "gift": os.path.join(based, "characters"),
            "textbox": os.path.join(root, "gui"),
            "other": os.path.join(root, "mod_assets", "mas_os", "import"),
        }
        return mapping.get(kind) or mapping["other"]

    def _safe_filename(name):
        name = os.path.basename(name or "").strip()
        name = name.split("?")[0].split("#")[0]
        name = re.sub(r"[^A-Za-z0-9._\- ]+", "_", name)
        name = name.strip(" ._")
        if not name or name in (".", ".."):
            return None
        return name[:80]

    def _rewrite_url(url):
        url = (url or "").strip()
        if not url:
            return None
        if url.startswith("github.com/"):
            url = "https://" + url
        m = re.match(
            r"https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.*)$",
            url,
        )
        if m:
            return "https://raw.githubusercontent.com/{0}/{1}/{2}/{3}".format(
                m.group(1), m.group(2), m.group(3), m.group(4)
            )
        m = re.search(r"drive\.google\.com/file/d/([^/]+)", url)
        if m:
            return "https://drive.google.com/uc?export=download&id=" + m.group(1)
        if "drive.google.com" in url:
            m = re.search(r"[?&]id=([A-Za-z0-9_-]+)", url)
            if m:
                return "https://drive.google.com/uc?export=download&id=" + m.group(1)
        if "dropbox.com" in url:
            if "dl=0" in url:
                return url.replace("dl=0", "dl=1")
            if "dl=" not in url:
                sep = "&" if "?" in url else "?"
                return url + sep + "dl=1"
            return url
        return url

    def _yandex_direct(url):
        if urllib2 is None or urllib is None:
            return None
        api = (
            "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key="
            + urllib.quote(url.encode("utf-8"), safe="")
        )
        pack = _http_get(api)
        if not pack:
            return None
        try:
            data = json.loads(pack[0])
        except Exception:
            return None
        return data.get("href")

    class _MASOSNoRedirect(urllib2.HTTPRedirectHandler if urllib2 is not None else object):
        """
        Do not auto-follow. GitHub release assets 302 to a signed
        objects.githubusercontent.com URL; Python 2 urllib2 unquotes
        %2F in X-Amz-Signature and the CDN returns XML/HTML, not the zip.
        """
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def _hdr(meta, name):
        if meta is None:
            return ""
        try:
            if hasattr(meta, "getheader"):
                val = meta.getheader(name)
            else:
                val = meta.get(name)
        except Exception:
            val = None
        if val is None:
            try:
                val = meta.get(name.lower())
            except Exception:
                val = None
        if val is None:
            return ""
        if isinstance(val, (list, tuple)):
            val = val[0] if val else ""
        return str(val)

    def _magic_desc(data):
        if not data:
            return "пусто"
        raw = data[:16]
        hx = " ".join(["%02x" % ord(c) for c in raw[:12]])
        ascii_s = "".join([
            (c if 32 <= ord(c) < 127 else ".")
            for c in raw[:16]
        ])
        return "magic hex[{0}] ascii[{1}] {2} байт".format(hx, ascii_s, len(data))

    def _looks_like_html(data):
        if not data:
            return False
        head = data[:512].lstrip().lower()
        if head.startswith("<!") or head.startswith("<html") or head.startswith("<head"):
            return True
        if "<html" in head[:240] or "<body" in head[:240]:
            return True
        if head.startswith("<?xml") and "<error" in head:
            return True
        return False

    def _looks_like_zip(data):
        if not data:
            return False
        if data[:2] == "PK":
            return True
        if data[:3] == "\xef\xbb\xbf" and data[3:5] == "PK":
            return True
        return False

    def _maybe_gunzip(data, log=None):
        if not data or zlib is None:
            return data
        if data[:2] != "\x1f\x8b":
            return data
        try:
            out = zlib.decompress(data, 16 + zlib.MAX_WBITS)
        except Exception as err:
            if log:
                log("  gzip не распаковался: {0}".format(err))
            return data
        if log:
            log("  распаковал gzip → {0} байт".format(len(out)))
        return out

    def _html_direct_url(data):
        if not data:
            return None
        text = data[:12000]
        m = re.search(r"https://objects\.githubusercontent\.com/[^\"'\s<>]+", text)
        if m:
            return m.group(0).replace("&amp;", "&")
        m = re.search(
            r'http-equiv=["\']refresh["\'][^>]*content=["\'][^;]*;\s*url=([^"\']+)',
            text,
            re.I,
        )
        if m:
            return m.group(1).replace("&amp;", "&")
        m = re.search(
            r'href=["\'](https://github\.com/[^"\']+/releases/download/[^"\']+)["\']',
            text,
        )
        if m:
            return m.group(1).replace("&amp;", "&")
        return None

    def _join_url(base, loc):
        loc = (loc or "").strip()
        if not loc:
            return None
        loc = loc.replace("&amp;", "&")
        if loc.startswith("http://") or loc.startswith("https://"):
            return loc
        if urlparse is not None:
            try:
                return urlparse.urljoin(base, loc)
            except Exception:
                pass
        return None

    def _cd_filename(meta):
        cd = _hdr(meta, "Content-Disposition")
        if not cd:
            return None
        m = re.search(r"filename\*=(?:UTF-8''|utf-8'')([^;]+)", cd)
        if m:
            raw = m.group(1).strip().strip('"')
            try:
                if urllib is not None:
                    raw = urllib.unquote(raw)
            except Exception:
                pass
            return raw
        m = re.search(r'filename="?([^";]+)"?', cd)
        if m:
            return m.group(1).strip()
        return None

    def _build_opener():
        handlers = []
        if urllib2 is not None:
            handlers.append(_MASOSNoRedirect())
        if _ssl is not None and urllib2 is not None:
            try:
                ctx = _ssl._create_unverified_context()
                handlers.append(urllib2.HTTPSHandler(context=ctx))
            except Exception:
                pass
        if urllib2 is None:
            return None
        try:
            return urllib2.build_opener(*handlers)
        except Exception:
            return urllib2.build_opener()

    def _open_once(opener, req, timeout):
        try:
            return opener.open(req, timeout=timeout)
        except TypeError:
            return opener.open(req)
        except urllib2.HTTPError:
            raise

    def _http_get(url, max_bytes=DL_MAX, log=None):
        if urllib2 is None:
            return None

        def _log(msg):
            if log:
                try:
                    log(msg)
                except Exception:
                    pass

        current = (url or "").strip()
        if not current:
            raise Exception("пустая ссылка")
        opener = _build_opener()
        if opener is None:
            raise Exception("сеть недоступна")
        seen = set()
        hops = 0
        last_err = None
        while hops < 8:
            hops += 1
            key = current[:500]
            if key in seen:
                raise Exception("цикл редиректов: {0}".format(current[:160]))
            seen.add(key)
            _log("HTTP GET [{0}] {1}".format(hops, current[:220]))
            req = urllib2.Request(current)
            req.add_header("User-Agent", DL_UA)
            req.add_header("Accept", "application/octet-stream, application/zip, */*")
            req.add_header("Accept-Language", "en-US,en;q=0.8")
            resp = None
            try:
                resp = _open_once(opener, req, DL_TIMEOUT)
            except urllib2.HTTPError as err:
                loc = ""
                try:
                    loc = _hdr(err.hdrs, "Location")
                except Exception:
                    loc = ""
                code = getattr(err, "code", 0)
                _log("  HTTP {0} {1}".format(code, getattr(err, "msg", "") or ""))
                if code in (301, 302, 303, 307, 308) and loc:
                    nxt = _join_url(current, loc)
                    _log("  Location: {0}".format((nxt or loc)[:220]))
                    if nxt:
                        current = nxt
                        last_err = err
                        continue
                body = ""
                try:
                    body = err.read(4096)
                except Exception:
                    body = ""
                try:
                    err.close()
                except Exception:
                    pass
                if body:
                    _log("  тело ошибки: {0}".format(_magic_desc(body)))
                    extracted = _html_direct_url(body)
                    if extracted and extracted not in seen:
                        _log("  в HTML ошибке есть прямая ссылка, пробую")
                        current = extracted
                        last_err = err
                        continue
                raise Exception("HTTP {0}: {1}".format(code, getattr(err, "msg", None) or err))
            except Exception as err:
                loc = ""
                hdrs = getattr(err, "hdrs", None) or getattr(err, "headers", None)
                code = getattr(err, "code", None)
                if hdrs is not None:
                    loc = _hdr(hdrs, "Location")
                if code in (301, 302, 303, 307, 308) and loc:
                    nxt = _join_url(current, loc)
                    _log("  HTTP {0} Location: {1}".format(code, (nxt or loc)[:220]))
                    if nxt:
                        current = nxt
                        last_err = err
                        continue
                last_err = err
                _log("  сбой соединения: {0}".format(err))
                raise

            code = getattr(resp, "code", None) or getattr(resp, "status", None) or 200
            meta = resp.info() if hasattr(resp, "info") else None
            ctype = _hdr(meta, "Content-Type")
            clen = _hdr(meta, "Content-Length")
            enc = _hdr(meta, "Content-Encoding")
            loc = _hdr(meta, "Location")
            final = ""
            try:
                final = resp.geturl() or ""
            except Exception:
                final = ""
            _log("  статус {0}  Content-Type={1}  Length={2}  Encoding={3}".format(
                code, ctype or "?", clen or "?", enc or "-"
            ))
            if final and final != current:
                _log("  geturl: {0}".format(final[:220]))

            if code in (301, 302, 303, 307, 308):
                nxt = _join_url(current, loc) or _join_url(final, loc)
                try:
                    resp.close()
                except Exception:
                    pass
                if not nxt:
                    raise Exception("редирект {0} без Location".format(code))
                _log("  Location: {0}".format(nxt[:220]))
                current = nxt
                continue

            length = 0
            try:
                length = int(clen or 0)
            except Exception:
                length = 0
            if length > max_bytes:
                try:
                    resp.close()
                except Exception:
                    pass
                raise Exception("файл больше {0} МБ (сервер сказал {1} байт)".format(
                    max_bytes / (1024 * 1024), length
                ))

            chunks = []
            total = 0
            try:
                while True:
                    piece = resp.read(64 * 1024)
                    if not piece:
                        break
                    total += len(piece)
                    if total > max_bytes:
                        raise Exception("файл больше {0} МБ".format(max_bytes / (1024 * 1024)))
                    chunks.append(piece)
                    if log and length and total > 0 and total % (512 * 1024) < 64 * 1024:
                        _log("  скачано {0}/{1} байт".format(total, length))
            finally:
                try:
                    resp.close()
                except Exception:
                    pass

            data = "".join(chunks)
            if enc.lower() == "gzip" or data[:2] == "\x1f\x8b":
                data = _maybe_gunzip(data, log=_log)
            _log("  скачано {0}".format(_magic_desc(data)))
            name = _cd_filename(meta)
            if name:
                _log("  Content-Disposition имя: {0}".format(name))
            return data, name, meta

        if last_err:
            raise last_err
        raise Exception("слишком много редиректов")

    def dl_guess_name(url, header_name=None):
        name = _safe_filename(header_name) if header_name else None
        if name:
            return name
        path = url.split("?")[0].rstrip("/")
        return _safe_filename(path.split("/")[-1]) or "download.bin"

    def _append_history(kind, name, ok, detail):
        hist = getattr(store.persistent, "_mas_os_dl_history", None)
        if hist is None:
            hist = []
        hist.insert(0, {
            "kind": kind,
            "name": name,
            "ok": ok,
            "detail": detail,
        })
        store.persistent._mas_os_dl_history = hist[:12]
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def dl_history():
        return getattr(store.persistent, "_mas_os_dl_history", None) or []

    def _zip_top_names(data):
        if zipfile is None:
            return []
        import StringIO
        tops = []
        seen = set()
        try:
            zf = zipfile.ZipFile(StringIO.StringIO(data))
            for info in zf.infolist():
                name = info.filename.replace("\\", "/").lstrip("/")
                if not name or ".." in name.split("/"):
                    continue
                top = name.split("/")[0]
                key = top.lower()
                if top and key not in seen:
                    seen.add(key)
                    tops.append(top)
        except Exception:
            return []
        return tops

    def _extract_zip(data, dest):
        if zipfile is None:
            raise Exception("zip не поддерживается")
        import StringIO
        zf = zipfile.ZipFile(StringIO.StringIO(data))
        dest = os.path.normpath(dest)
        count = 0
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.endswith("/") or ".." in name.split("/"):
                continue
            target = os.path.normpath(os.path.join(dest, name))
            if not target.startswith(dest):
                continue
            folder = os.path.dirname(target)
            if folder and not os.path.isdir(folder):
                os.makedirs(folder)
            if info.file_size:
                with open(target, "wb") as handle:
                    handle.write(zf.read(info))
                count += 1
        return count

    def _download_worker(url, kind):
        global dl_busy, dl_status, dl_last_name
        try:
            raw = _rewrite_url(url)
            if not raw:
                raise Exception("вставь ссылку http(s)")
            if raw.startswith("http://") is False and raw.startswith("https://") is False:
                raise Exception("только http или https")
            if "yadi.sk" in raw or "disk.yandex." in raw:
                href = _yandex_direct(raw)
                if not href:
                    raise Exception("Яндекс.Диск не отдал файл. Ссылка должна быть публичной.")
                raw = href
            data, header_name, meta = _http_get(raw)
            if not data:
                raise Exception("пустой ответ")
            head = data[:200].lstrip().lower()
            if head.startswith("<!doctype") or head.startswith("<html"):
                raise Exception(
                    "пришла веб-страница, не файл. Для Google Drive: доступ «все у кого есть ссылка», файл не огромный."
                )
            name = dl_guess_name(raw, header_name)
            row = dl_kind_row(kind)
            ext = os.path.splitext(name)[1].lower()
            if ext not in row[3]:
                raise Exception("для «{0}» нужен файл {1}, а пришёл {2}".format(
                    row[1], ", ".join(row[3]), ext or "без расширения"
                ))
            folder = _dl_folder(kind)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            if kind == "submod" and ext == ".zip":
                installer = getattr(store.mas_os, "install_submod_zip", None)
                if installer is not None:
                    ok, msg, _paths = installer(data, name, "auto")
                    dl_last_name = name
                    dl_status = msg
                    _append_history(kind, name, ok, dl_status)
                    if not ok:
                        raise Exception(msg)
                else:
                    n = _extract_zip(data, folder)
                    tops = _zip_top_names(data)
                    _inventory_add(kind, tops or [name])
                    dl_last_name = name
                    dl_status = "Распаковано {0} файлов в Submods. Перезапусти игру.".format(n)
                    _append_history(kind, name, True, dl_status)
            else:
                if dl_is_protected(kind, name):
                    raise Exception(
                        "«{0}» — файл игры, его нельзя перезаписать со склада.".format(name)
                    )
                path = os.path.join(folder, name)
                with open(path, "wb") as handle:
                    handle.write(data)
                _inventory_add(kind, [name])
                dl_last_name = name
                extra = ""
                if kind in ("submod", "font", "music"):
                    extra = " Перезапусти игру, чтобы подхватилось."
                elif kind == "wallpaper":
                    extra = " Обои появятся в настройках оформления."
                elif kind == "textbox":
                    extra = " Если имя textbox_d_цвет.png — подхватим как цвет бокса позже."
                dl_status = "Готово: {0}{1}".format(name, extra)
                _append_history(kind, name, True, dl_status)
        except Exception as err:
            dl_status = "Не вышло: {0}".format(err)
            _append_history(kind, url[:48], False, dl_status)
        dl_busy = False

    def start_download():
        global dl_busy, dl_status
        if dl_busy:
            return
        url = (dl_url or "").strip()
        if not url:
            dl_status = "Сначала вставь ссылку."
            return
        if urllib2 is None:
            dl_status = "Сеть недоступна в этой сборке."
            return
        stop_dl_typing()
        dl_busy = True
        dl_status = "Скачиваю…"
        worker = threading.Thread(target=_download_worker, args=(url, dl_kind))
        worker.daemon = True
        worker.start()


init python:
    class MASOSDLInputValue(InputValue):
        default = False
        editable = True
        returnable = True

        def get_text(self):
            return store.mas_os.dl_url or ""

        def set_text(self, value):
            store.mas_os.dl_url = value

        def enter(self):
            store.mas_os.stop_dl_typing()
            return None


init 1 python:
    store.mas_os.dl_iv = MASOSDLInputValue()


label mas_os_store:
    $ store.mas_os.stop_dl_typing()
    call screen mas_os_store with mas_os_trans
    if _return == "settings":
        jump mas_os_settings
    if _return == "player":
        jump mas_os_player
    if _return == "gifts":
        jump mas_os_gifts
    if _return == "submods":
        jump mas_os_submods
    jump mas_os_home


screen mas_os_store():
    modal True
    zorder 200

    $ kind = store.mas_os.dl_kind
    $ typing = store.mas_os.dl_typing
    $ typed = store.mas_os.dl_url or ""
    $ status = store.mas_os.dl_status
    $ busy = store.mas_os.dl_busy
    $ hist = store.mas_os.dl_history()
    $ row = store.mas_os.dl_kind_row()
    $ owned = store.mas_os.dl_list_files()
    $ back_to = store.mas_os.dl_from or "home"

    use mas_os_bg

    if busy:
        timer 0.4 repeat True action Function(renpy.restart_interaction)

    text _("Склад") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text _("Скачать файл по прямой ссылке. Для телефона: GitHub raw, Google Drive, Яндекс.Диск, Dropbox.") at store.mas_os.t_pop(0.04):
        style "mas_os_hint"
        xpos 48
        ypos 58
        xsize 1180

    viewport:
        xpos 48
        ypos 100
        xysize (340, 510)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 8

            for kid, title, icname, exts in store.mas_os.DL_KINDS:
                button:
                    style "mas_os_side_btn"
                    selected (kid == kind)
                    action Function(store.mas_os.set_dl_kind, kid)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    hbox:
                        spacing 10
                        yalign 0.5
                        xoffset 8

                        if store.mas_os.icon_path(icname):
                            add store.mas_os.fit_image(store.mas_os.icon_path(icname), 32, 32):
                                yalign 0.5

                        text title:
                            style "mas_os_side_btn_text"
                            yalign 0.5

    frame at store.mas_os.t_pop(0.06):
        style "mas_os_panel"
        xpos 410
        ypos 100
        xysize (822, 510)
        padding (20, 16)

        viewport:
            xysize (782, 478)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 10
                xsize 760

                text row[1]:
                    style "mas_os_subtitle"

                text _("Принимает: {0}. Максимум 32 МБ.").format(", ".join(row[3])):
                    style "mas_os_hint"

                hbox:
                    spacing 8

                    if typing:
                        input:
                            value store.mas_os.dl_iv
                            copypaste True
                            length 4000
                            color store.mas_os.theme_color("input")
                            size 18
                            xsize 400
                            yalign 0.5
                    else:
                        button:
                            style "mas_os_gift_field"
                            xsize 400
                            ysize 44
                            action [
                                Function(store.mas_os.start_dl_typing),
                                store.mas_os.dl_iv.Enable(),
                            ]

                            if typed:
                                text typed:
                                    style "mas_os_body"
                                    size 16
                                    yalign 0.5
                                    substitute False
                            else:
                                text _("Нажми или Вставить"):
                                    style "mas_os_hint"
                                    size 16
                                    yalign 0.5

                    textbutton _("Вставить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        xsize 140
                        action Function(store.mas_os.paste_url_into, "dl")

                    if typing:
                        textbutton _("Готово"):
                            style "mas_os_nav_btn"
                            text_style "mas_os_nav_btn_text"
                            xsize 110
                            action [
                                store.mas_os.dl_iv.Disable(),
                                Function(store.mas_os.stop_dl_typing),
                            ]

                textbutton _("Скачать"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    xsize 220
                    sensitive (not busy)
                    action Function(store.mas_os.start_download)

                if status:
                    text status:
                        style "mas_os_body"
                        xsize 750
                        substitute False

                text _("GitHub: raw.githubusercontent.com/... или страница blob — сами перепишем в raw. Drive/Яндекс — доступ по ссылке."):
                    style "mas_os_hint"
                    xsize 750

                text _("Загруженное"):
                    style "mas_os_subtitle"

                text _("Только свои файлы. Обои splash/menu, шрифты MAS и штатные текстбоксы удалить нельзя."):
                    style "mas_os_hint"
                    xsize 750

                viewport:
                    xysize (750, 150)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 4
                        xsize 726

                        if not owned:
                            text _("Пока ничего своего в этом разделе."):
                                style "mas_os_hint"
                        else:
                            for item in owned:
                                hbox:
                                    spacing 8
                                    xsize 726

                                    text item["name"]:
                                        style "mas_os_body"
                                        size 16
                                        yalign 0.5
                                        xsize 500
                                        substitute False

                                    textbutton _("Удалить"):
                                        style "mas_os_nav_btn"
                                        text_style "mas_os_nav_btn_text"
                                        xsize 140
                                        ysize 36
                                        action Show(
                                            "mas_os_confirm",
                                            message=store.mas_os.dl_delete_prompt(item["name"]),
                                            yes_action=[
                                                Function(store.mas_os.dl_delete, item["kind"], item["name"]),
                                                Hide("mas_os_confirm"),
                                            ],
                                            no_action=Hide("mas_os_confirm"),
                                        )

                text _("Недавние попытки"):
                    style "mas_os_subtitle"

                viewport:
                    xysize (750, 70)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 2
                        xsize 726

                        if not hist:
                            text _("Пока пусто."):
                                style "mas_os_hint"
                        else:
                            for item in hist:
                                $ mark = "OK" if item.get("ok") else "ERR"
                                text "{0}  {1}  —  {2}".format(mark, item.get("kind"), item.get("name")):
                                    style "mas_os_hint"
                                    substitute False

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        at mas_os_btn
        action [
            Function(store.mas_os.stop_dl_typing),
            Return(back_to),
        ]

    key "K_ESCAPE" action [Function(store.mas_os.stop_dl_typing), Return(back_to)]
    key "K_AC_BACK" action If(
        store.mas_os.dl_typing,
        [store.mas_os.dl_iv.Disable(), Function(store.mas_os.stop_dl_typing)],
        [Function(store.mas_os.stop_dl_typing), Return(back_to)],
    )


screen mas_os_store_link(kind, back="home", xsize=760):
    $ ic = store.mas_os.icon_path("updates")

    button:
        style "mas_os_button"
        xsize xsize
        ysize 56
        hover_sound store.mas_os.os_hover()
        activate_sound store.mas_os.os_activate()
        action [
            Function(store.mas_os.open_store, kind, back),
            Return("store"),
        ]

        hbox:
            spacing 10
            yalign 0.5
            xoffset 12

            if ic:
                add store.mas_os.fit_image(ic, 32, 32):
                    yalign 0.5
            else:
                frame:
                    xysize (32, 32)
                    background Solid("#4A8AAA")
                    yalign 0.5

                    text _("Ск"):
                        style "mas_os_glyph"
                        xalign 0.5
                        yalign 0.5

            text _("Загрузить свои через Склад"):
                style "mas_os_button_text"
                yalign 0.5
