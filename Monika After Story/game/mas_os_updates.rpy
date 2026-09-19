# -*- coding: utf-8 -*-
# --- FILE MAP ---
# mas_os_updates.rpy — проверка обновлений порта из MAS OS
#
# Не путать с updater.rpy: тот смотрит официальный MAS с S3.
# Здесь только этот порт. Сравниваем config.port_version с файлом.
# config.version остаётся версией MAS.
#
# Источники:
#   GitHub version.txt / version_test.txt — игроки и тестовый канал
#   game/mod_assets/mas_os/update_preview/version.txt — локальный тест окна
#
# Два канала, каждый смотрит свой файл:
#   основной              → version.txt
#   дополнительный (тест) → version_test.txt
# Пока правишь тестовый файл, игроки на основном ничего не видят.
# Канал переключается в Debug → Обновления.
#
# Тихая проверка при входе в оболочку. Ручная — Настройки → Система.
# Экраны: mas_os_update_checking / available / current / error.
#
# Формат version.txt:
#   # комментарии только ДО номера версии
#   0.2.0
#   title: необязательный заголовок окна
#   ticker: текст бегущей строки в лобби
#   banner: текст всплывающей плашки
#
#   ## Что нового
#   - пункт
#   **жирный**, *курсив*, ~~зачёркнутый~~, `код`
#   {size=22}крупнее{/size}  {color=#FF8AC4}цвет{/color}
#   {font=riffic}заголовочный шрифт{/font}
# ---

default persistent._mas_os_update_channel = "stable"
default persistent._mas_os_skipped_versions = {}

init -4 python in mas_os:
    import os
    import re
    import time
    import threading
    import store

    UPDATE_REPO = "https://github.com/artem213101zse/MonikaModDev-RU"
    UPDATE_BRANCH = "renpy-7-port"
    UPDATE_CHANNEL_ORDER = ("stable", "test")
    UPDATE_CHANNELS = {
        "stable": {
            "label": u"Основной",
            "file": "version.txt",
        },
        "test": {
            "label": u"Дополнительный (тест)",
            "file": "version_test.txt",
        },
    }

    UPDATE_LOCAL_REL = os.path.join(
        "mod_assets", "mas_os", "update_preview", "version.txt"
    )

    upd_checking = False
    upd_silent = True
    upd_cancelled = False
    upd_available = False
    upd_remote = ""
    upd_notes = ""
    upd_news_title = ""
    upd_news_blocks = []
    upd_ticker_text = ""
    upd_banner_text = ""
    upd_error = ""
    upd_need_ui = None
    upd_prompted = False
    upd_local_cache = ""
    upd_source = "remote"

    NEWS_TEST_TICKER = (
        u"Ваш порт устарел. Обновите его до последней версии. "
        u"Спасибо за понимание и постоянную поддержку!"
    )
    NEWS_TEST_BANNER = (
        u"Выпущена новая версия порта. Для продолжения **открой** новости "
        u"и **обнови** сборку."
    )

    news_ticker_force = False
    news_ticker_t0 = None
    news_banner_pending = False
    news_game_checked = False
    _news_banner_now = u""

    UPD_FETCH_MAX = 96 * 1024
    _UPD_TAG_NAMES = (
        "size", "color", "font", "b", "i", "u", "s", "a", "alpha", "outline", "f",
        "vspace", "space",
    )
    _UPD_TAG_RE = re.compile(
        ur"\{(/?)(size|color|font|b|i|u|s|a|alpha|outline|f|vspace|space)(?:=([^}]*))?\}",
        re.IGNORECASE | re.UNICODE,
    )

    def upd_mas_version():
        ver = getattr(store.config, "version", None) or ""
        try:
            return unicode(ver).strip()
        except Exception:
            return str(ver).strip()

    def upd_local_version():
        ver = getattr(store.config, "port_version", None)
        if not ver:
            ver = getattr(store.config, "version", None) or ""
        try:
            return unicode(ver).strip()
        except Exception:
            return str(ver).strip()

    def upd_is_local():
        return upd_source == "local"

    def upd_local_file_path():
        gamed = getattr(store.renpy.config, "gamedir", None) or ""
        based = getattr(store.renpy.config, "basedir", None) or ""
        names = [
            os.path.join(gamed, UPDATE_LOCAL_REL) if gamed else None,
            os.path.join(based, "update_preview", "version.txt") if based else None,
        ]
        for path in names:
            if path and os.path.isfile(path):
                return path
        if gamed:
            return os.path.join(gamed, UPDATE_LOCAL_REL)
        return UPDATE_LOCAL_REL

    def upd_channel_id():
        cid = getattr(store.persistent, "_mas_os_update_channel", None) or "stable"
        if cid not in UPDATE_CHANNELS:
            return "stable"
        return cid

    def upd_channel_meta():
        return UPDATE_CHANNELS.get(upd_channel_id()) or UPDATE_CHANNELS["stable"]

    def upd_channel_label():
        return upd_channel_meta().get("label") or u"Основной"

    def upd_channel_file():
        return upd_channel_meta().get("file") or "version.txt"

    def upd_channel_url():
        name = upd_channel_file()
        base = (
            "https://raw.githubusercontent.com/artem213101zse/"
            "MonikaModDev-RU/{0}/{1}"
        ).format(UPDATE_BRANCH, name)
        return base + "?t=" + str(int(time.time()))

    def upd_has_update():
        if not upd_available:
            return False
        remote = (upd_remote or "").strip()
        if not remote:
            return False
        return remote != upd_local_version()

    def upd_status_line():
        local = upd_local_version()
        mas = upd_mas_version()
        ch = upd_channel_label()
        fn = upd_channel_file()
        if upd_has_update():
            return u"Порт {0} (MAS {1}). На канале «{2}» ({3}) доступна {4}.".format(
                local, mas, ch, fn, upd_remote
            )
        return u"Порт {0} (MAS {1}). Канал «{2}» читает {3}.".format(
            local, mas, ch, fn
        )

    def upd_checking_line():
        if upd_is_local():
            return u"Читаю локальный файл, GitHub не трогается."
        return u"Читаю {0} на канале «{1}».".format(
            upd_channel_file(), upd_channel_label()
        )

    def upd_error_hint():
        if upd_is_local():
            return (
                u"Локальный файл не прочитался. "
                u"Положи version.txt в game/mod_assets/mas_os/update_preview/."
            )
        return (
            u"Файл {0} с GitHub не прочитался. "
            u"Сеть, файл ещё не залит, или сырой URL недоступен."
        ).format(upd_channel_file())

    def upd_skipped_map():
        blob = getattr(store.persistent, "_mas_os_skipped_versions", None)
        if not isinstance(blob, dict):
            return {}
        return blob

    def upd_skipped():
        return upd_skipped_map().get(upd_channel_id())

    def upd_set_channel(cid):
        global upd_available, upd_remote, upd_notes, upd_error
        global upd_need_ui, upd_prompted, upd_news_title, upd_news_blocks
        global upd_ticker_text, upd_banner_text
        if cid not in UPDATE_CHANNELS:
            cid = "stable"
        store.persistent._mas_os_update_channel = cid
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        upd_available = False
        upd_remote = ""
        upd_notes = ""
        upd_news_title = ""
        upd_news_blocks = []
        upd_ticker_text = ""
        upd_banner_text = ""
        upd_error = ""
        upd_need_ui = None
        upd_prompted = False
        return None

    def upd_skip():
        global upd_available
        remote = (upd_remote or "").strip()
        if remote:
            blob = dict(upd_skipped_map())
            blob[upd_channel_id()] = remote
            store.persistent._mas_os_skipped_versions = blob
            try:
                store.renpy.save_persistent()
            except Exception:
                pass
        upd_available = False
        try:
            store.renpy.hide_screen("mas_os_update_available")
        except Exception:
            pass
        return None

    def upd_clear_skip():
        blob = dict(upd_skipped_map())
        if upd_channel_id() in blob:
            del blob[upd_channel_id()]
            store.persistent._mas_os_skipped_versions = blob
            try:
                store.renpy.save_persistent()
            except Exception:
                pass
        return None

    def upd_later():
        try:
            store.renpy.hide_screen("mas_os_update_available")
        except Exception:
            pass
        return None

    def upd_open_repo():
        try:
            open_site(UPDATE_REPO)
        except Exception:
            pass
        try:
            store.renpy.hide_screen("mas_os_update_available")
        except Exception:
            pass
        return None

    def upd_hide_error():
        try:
            store.renpy.hide_screen("mas_os_update_error")
        except Exception:
            pass
        return None

    def upd_hide_current():
        try:
            store.renpy.hide_screen("mas_os_update_current")
        except Exception:
            pass
        return None

    def upd_show_available():
        try:
            store.renpy.show_screen("mas_os_update_available")
        except Exception:
            pass
        return None

    def upd_cancel():
        global upd_cancelled, upd_silent
        upd_cancelled = True
        upd_silent = True
        try:
            store.renpy.hide_screen("mas_os_update_checking")
        except Exception:
            pass
        return None

    def upd_can_show_prompt():
        try:
            if store.renpy.get_screen("mas_os_boot_anim"):
                return False
            if store.renpy.get_screen("mas_os_launch_anim"):
                return False
            if store.renpy.get_screen("mas_os_generating"):
                return False
        except Exception:
            pass
        return True

    def upd_news_rows():
        return list(upd_news_blocks or [])

    def news_ticker_message():
        if news_ticker_force:
            return upd_ticker_text or NEWS_TEST_TICKER
        if not upd_has_update():
            return u""
        if upd_ticker_text:
            return upd_ticker_text
        remote = upd_remote or u""
        local = upd_local_version()
        return (
            u"Доступна версия {0} порта. Сейчас стоит {1}. "
            u"Нажми, чтобы открыть новости. Спасибо, что ты с нами."
        ).format(remote, local)

    def news_ticker_on():
        return bool(news_ticker_message())

    def news_ticker_x():
        return 16

    def news_ticker_y():
        if layout_desktop():
            return 12
        return 90

    def news_ticker_game_on():
        if not news_ticker_on():
            return False
        if not game_entered:
            return False
        try:
            if store.renpy.get_screen("mas_os_home"):
                return False
            if store.renpy.get_screen("mas_os_home_cards"):
                return False
            if store.renpy.get_screen("talk_choice"):
                return False
            if store.renpy.get_screen("mas_extramenu_area"):
                return False
            if store.renpy.get_screen("mas_os_news_ticker_overlay"):
                return False
        except Exception:
            pass
        return True

    def news_on_game_enter():
        global news_game_checked
        if news_game_checked or upd_available or upd_checking:
            return None
        news_game_checked = True
        if upd_remote:
            return None
        return upd_on_enter()

    def news_banner_message():
        if upd_banner_text:
            return upd_banner_text
        remote = upd_remote or u""
        if remote:
            return (
                u"Выпущена новая версия порта {0}. "
                u"**Открой** новости и **обнови** сборку."
            ).format(remote)
        return NEWS_TEST_BANNER

    def news_banner_markup(text):
        text = unicode(text or "")
        text = text.replace(u"{", u"{{")
        text = re.sub(
            ur"\*\*(.+?)\*\*",
            ur"{color=#6FCF97}{b}\1{/b}{/color}",
            text,
        )
        return text

    def news_can_show_banner():
        try:
            if store.renpy.get_screen("mas_os_update_available"):
                return False
            if store.renpy.get_screen("mas_os_update_checking"):
                return False
            if store.renpy.get_screen("mas_os_boot_anim"):
                return False
            if store.renpy.get_screen("mas_os_launch_anim"):
                return False
            if store.renpy.get_screen("mas_os_generating"):
                return False
        except Exception:
            pass
        return True

    def news_show_banner(message=None):
        global _news_banner_now
        if message:
            _news_banner_now = news_banner_markup(message)
        else:
            _news_banner_now = news_banner_markup(news_banner_message())
        try:
            store.renpy.show_screen("mas_os_news_banner")
        except Exception:
            pass
        return None

    def news_hide_banner():
        try:
            store.renpy.hide_screen("mas_os_news_banner")
        except Exception:
            pass
        return None

    def news_maybe_banner():
        global news_banner_pending
        if not news_banner_pending:
            return None
        if not news_can_show_banner():
            return None
        news_banner_pending = False
        return news_show_banner()

    def news_hide_ticker_overlay():
        global news_ticker_force
        news_ticker_force = False
        try:
            store.renpy.hide_screen("mas_os_news_ticker_overlay")
        except Exception:
            pass
        return None

    def news_test_ticker():
        global news_ticker_force, news_ticker_t0, upd_ticker_text
        news_ticker_force = True
        news_ticker_t0 = time.time()
        if not upd_ticker_text:
            upd_ticker_text = NEWS_TEST_TICKER
        try:
            store.renpy.show_screen("mas_os_news_ticker_overlay")
        except Exception:
            pass
        return None

    def news_test_banner():
        return news_show_banner(NEWS_TEST_BANNER)

    def news_test_both():
        news_test_ticker()
        return news_show_banner(NEWS_TEST_BANNER)

    def news_banner_click():
        news_hide_banner()
        if upd_has_update() or news_ticker_force:
            return upd_show_available()
        return None

    def _upd_decode(data):
        if data is None:
            return u""
        if isinstance(data, unicode):
            text = data
        else:
            try:
                text = data.decode("utf-8")
            except Exception:
                try:
                    text = data.decode("cp1251")
                except Exception:
                    text = unicode(data)
        if text and text[0] == u"\ufeff":
            text = text[1:]
        return text.replace(u"\r\n", u"\n").replace(u"\r", u"\n")

    def _upd_font_path(name):
        name = (name or "").strip().strip("\"'")
        if not name:
            return None
        low = name.lower()
        packs = []
        try:
            packs = all_font_packs()
        except Exception:
            try:
                packs = list(FONT_PACKS)
            except Exception:
                packs = []
        for fid, title, path in packs:
            if unicode(fid).lower() == low:
                return path
            if unicode(title).lower() == low:
                return path
            base = os.path.splitext(os.path.basename(path))[0].lower()
            if base == low:
                return path
        if (
            "/" in name
            or "\\" in name
            or low.endswith(".ttf")
            or low.endswith(".otf")
        ):
            return name
        return None

    def _upd_rewrite_tags(text):
        def _repl(m):
            slash = m.group(1) or ""
            name = (m.group(2) or "").lower()
            arg = m.group(3)
            if name == "f":
                name = "font"
            if name == "font" and arg and not slash:
                path = _upd_font_path(arg)
                if path:
                    arg = path
            if slash:
                return u"{/" + name + u"}"
            if arg is not None:
                return u"{" + name + u"=" + unicode(arg) + u"}"
            return u"{" + name + u"}"

        return _UPD_TAG_RE.sub(_repl, text)

    def _upd_protect(text):
        chunks = []

        def _keep(m):
            chunks.append(m.group(0))
            return u"\x01MD{0}\x01".format(len(chunks) - 1)

        text = _UPD_TAG_RE.sub(_keep, text)
        return text, chunks

    def _upd_restore(text, chunks):
        i = 0
        while i < len(chunks):
            text = text.replace(u"\x01MD{0}\x01".format(i), chunks[i])
            i += 1
        return text

    def _upd_md_inline(text):
        if not text:
            return u""
        text = unicode(text)
        text, saved = _upd_protect(text)

        codes = []

        def _code(m):
            codes.append(m.group(1))
            return u"\x01CD{0}\x01".format(len(codes) - 1)

        text = re.sub(ur"`([^`]+)`", _code, text)
        text = text.replace(u"{", u"{{")
        text = re.sub(
            ur"\[([^\]]+)\]\(([^)]+)\)",
            ur"{a=\2}\1{/a}",
            text,
        )
        text = re.sub(ur"\*\*\*(.+?)\*\*\*", ur"{b}{i}\1{/i}{/b}", text)
        text = re.sub(ur"\*\*(.+?)\*\*", ur"{b}\1{/b}", text)
        text = re.sub(ur"__(.+?)__", ur"{b}\1{/b}", text)
        text = re.sub(ur"~~(.+?)~~", ur"{s}\1{/s}", text)
        text = re.sub(
            ur"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            ur"{i}\1{/i}",
            text,
        )
        text = re.sub(
            ur"(?<![A-Za-z0-9_])_([^_]+)_(?![A-Za-z0-9_])",
            ur"{i}\1{/i}",
            text,
        )
        text = _upd_restore(text, saved)
        i = 0
        while i < len(codes):
            snippet = codes[i].replace(u"{", u"{{")
            tagged = u"{color=#C989A8}" + snippet + u"{/color}"
            text = text.replace(u"\x01CD{0}\x01".format(i), tagged)
            i += 1
        return _upd_rewrite_tags(text)

    def _upd_is_version_token(token):
        if not token:
            return False
        return re.match(r"^[0-9A-Za-z][0-9A-Za-z._+-]*$", token) is not None

    def _upd_version_from_line(line):
        s = (line or "").strip()
        if not s:
            return None
        low = s.lower()
        for prefix in (u"version:", u"версия:", u"ver:"):
            if low.startswith(prefix):
                s = s.split(u":", 1)[1].strip()
                break
        if not s or s.startswith(u"#"):
            return None
        token = s.split()[0]
        if _upd_is_version_token(token):
            return token
        return None

    def _upd_meta_field(line, prefixes):
        s = (line or "").strip()
        low = s.lower()
        for prefix in prefixes:
            if low.startswith(prefix):
                return s.split(u":", 1)[1].strip()
        return None

    def _upd_block_start(stripped):
        if not stripped:
            return True
        if stripped in (u"---", u"***", u"___"):
            return True
        if stripped.startswith(u"#"):
            return True
        if stripped.startswith(u"> "):
            return True
        if re.match(ur"^[-*+] ", stripped):
            return True
        if re.match(ur"^\d+\.\s+", stripped):
            return True
        return False

    def _upd_md_blocks(body):
        rows = []
        if not body:
            return rows
        lines = unicode(body).replace(u"\r\n", u"\n").replace(u"\r", u"\n").split(u"\n")
        i = 0
        n = len(lines)
        while i < n:
            raw = lines[i].rstrip()
            stripped = raw.strip()
            if not stripped:
                if rows and rows[-1].get("kind") != "space":
                    rows.append({"kind": "space"})
                i += 1
                continue
            if stripped in (u"---", u"***", u"___"):
                rows.append({"kind": "hr"})
                i += 1
                continue
            if stripped.startswith(u"### "):
                rows.append({"kind": "h3", "text": _upd_md_inline(stripped[4:])})
                i += 1
                continue
            if stripped.startswith(u"## "):
                rows.append({"kind": "h2", "text": _upd_md_inline(stripped[3:])})
                i += 1
                continue
            if stripped.startswith(u"# "):
                rows.append({"kind": "h1", "text": _upd_md_inline(stripped[2:])})
                i += 1
                continue
            if stripped.startswith(u">"):
                quote = []
                while i < n:
                    q = lines[i].rstrip()
                    qs = q.strip()
                    if not qs.startswith(u">"):
                        break
                    piece = qs[1:]
                    if piece.startswith(u" "):
                        piece = piece[1:]
                    quote.append(piece)
                    i += 1
                rows.append({"kind": "quote", "text": _upd_md_inline(u" ".join(quote))})
                continue
            m_ul = re.match(ur"^[-*+] (.+)$", stripped)
            if m_ul:
                rows.append({
                    "kind": "li",
                    "mark": u"•",
                    "text": _upd_md_inline(m_ul.group(1)),
                })
                i += 1
                continue
            m_ol = re.match(ur"^(\d+)\.\s+(.+)$", stripped)
            if m_ol:
                rows.append({
                    "kind": "li",
                    "mark": m_ol.group(1) + u".",
                    "text": _upd_md_inline(m_ol.group(2)),
                })
                i += 1
                continue
            para = [stripped]
            i += 1
            while i < n:
                nxt = lines[i].rstrip()
                ns = nxt.strip()
                if not ns or _upd_block_start(ns):
                    break
                para.append(ns)
                i += 1
            rows.append({"kind": "p", "text": _upd_md_inline(u" ".join(para))})
        if rows and rows[0].get("kind") == "space":
            rows = rows[1:]
        if rows and rows[-1].get("kind") == "space":
            rows = rows[:-1]
        return rows

    def _upd_plain_notes(blocks):
        bits = []
        for blk in blocks:
            kind = blk.get("kind")
            if kind in ("p", "li", "h2", "h3", "quote"):
                raw = blk.get("text") or u""
                raw = _UPD_TAG_RE.sub(u"", raw)
                raw = raw.replace(u"{{", u"{")
                if raw:
                    bits.append(raw)
            if len(bits) >= 3:
                break
        return u" ".join(bits).strip()

    def _upd_parse(data):
        text = _upd_decode(data)
        version = u""
        title = u""
        ticker = u""
        banner = u""
        body_lines = []
        seen_version = False
        for raw in text.split(u"\n"):
            line = raw.rstrip()
            stripped = line.strip()
            if not seen_version:
                if not stripped or stripped.startswith(u"#"):
                    continue
                ver = _upd_version_from_line(stripped)
                if ver:
                    version = ver
                    seen_version = True
                continue
            if not body_lines:
                meta = _upd_meta_field(stripped, (u"title:", u"заголовок:"))
                if meta is not None:
                    title = meta
                    continue
                meta = _upd_meta_field(stripped, (u"ticker:", u"бегущая:", u"строка:"))
                if meta is not None:
                    ticker = meta
                    continue
                meta = _upd_meta_field(stripped, (u"banner:", u"баннер:"))
                if meta is not None:
                    banner = meta
                    continue
            body_lines.append(line)
        body = u"\n".join(body_lines).strip()
        blocks = _upd_md_blocks(body)
        if not title:
            for blk in blocks:
                if blk.get("kind") == "h1":
                    title = _UPD_TAG_RE.sub(u"", blk.get("text") or u"")
                    title = title.replace(u"{{", u"{").strip()
                    break
        notes = _upd_plain_notes(blocks)
        return version, notes, blocks, title, ticker, banner

    def _upd_fetch(url):
        opener = None
        try:
            opener = _build_opener()
        except Exception:
            opener = None
        if opener is None:
            if urllib2 is None:
                raise Exception("сеть недоступна")
            opener = urllib2.build_opener()
        req = urllib2.Request(url)
        ua = "MAS-OS-Updater"
        try:
            ua = DL_UA
        except Exception:
            pass
        req.add_header("User-Agent", ua)
        req.add_header("Accept", "text/plain, */*")
        req.add_header("Cache-Control", "no-cache")
        resp = None
        try:
            try:
                resp = opener.open(req, timeout=8)
            except TypeError:
                resp = opener.open(req)
            data = resp.read(UPD_FETCH_MAX)
        finally:
            if resp is not None:
                try:
                    resp.close()
                except Exception:
                    pass
        if not data:
            raise Exception("пустой ответ")
        head = data[:80].lstrip().lower()
        if (
            head.startswith("<html")
            or head.startswith("<!doctype")
            or head.startswith("<head")
        ):
            raise Exception("вместо версии пришла HTML-страница")
        return data

    def _upd_worker():
        global upd_checking, upd_available, upd_remote, upd_notes
        global upd_error, upd_need_ui, upd_local_cache
        global upd_news_title, upd_news_blocks
        global upd_ticker_text, upd_banner_text, news_banner_pending
        result_ui = None
        try:
            if upd_cancelled:
                return
            local = upd_local_version()
            upd_local_cache = local
            if upd_source == "local":
                path = upd_local_file_path()
                if not path or not os.path.isfile(path):
                    raise Exception("нет файла {0}".format(UPDATE_LOCAL_REL))
                handle = open(path, "rb")
                try:
                    data = handle.read(UPD_FETCH_MAX)
                finally:
                    handle.close()
            else:
                data = _upd_fetch(upd_channel_url())
            if upd_cancelled:
                return
            parsed = _upd_parse(data)
            remote = parsed[0]
            notes = parsed[1]
            blocks = parsed[2]
            title = parsed[3]
            ticker = parsed[4]
            banner = parsed[5]
            if not remote:
                raise Exception("в файле нет номера версии")
            upd_remote = remote
            upd_notes = notes
            upd_news_blocks = blocks
            upd_news_title = title or u""
            upd_ticker_text = ticker or u""
            upd_banner_text = banner or u""
            if remote != local:
                skipped = (upd_source != "local") and (upd_skipped() == remote)
                if upd_silent and skipped:
                    upd_available = False
                    result_ui = None
                else:
                    upd_available = True
                    result_ui = "available"
                    if upd_silent:
                        news_banner_pending = True
            else:
                upd_available = False
                result_ui = None if upd_silent else "current"
        except Exception as err:
            if upd_cancelled:
                return
            try:
                upd_error = unicode(err)
            except Exception:
                upd_error = str(err)
            upd_available = False
            result_ui = None if upd_silent else "error"
        finally:
            if not upd_cancelled:
                upd_need_ui = result_ui
            upd_checking = False

    def upd_start(silent=True, source="remote"):
        global upd_checking, upd_silent, upd_cancelled, upd_error
        global upd_need_ui, upd_notes, upd_source
        global upd_news_title, upd_news_blocks
        global upd_ticker_text, upd_banner_text
        if source not in ("remote", "local"):
            source = "remote"
        if upd_checking:
            if not silent:
                try:
                    store.renpy.show_screen("mas_os_update_checking")
                except Exception:
                    pass
            return None
        upd_source = source
        upd_silent = bool(silent)
        upd_cancelled = False
        upd_error = ""
        upd_notes = ""
        upd_news_title = ""
        upd_news_blocks = []
        upd_ticker_text = ""
        upd_banner_text = ""
        upd_need_ui = None
        upd_checking = True
        if not silent:
            try:
                store.renpy.show_screen("mas_os_update_checking")
            except Exception:
                pass
        worker = threading.Thread(target=_upd_worker)
        worker.daemon = True
        worker.start()
        return None

    def upd_manual():
        return upd_start(False, "remote")

    def upd_local_test():
        return upd_start(False, "local")

    def upd_retry():
        src = "local" if upd_is_local() else "remote"
        try:
            store.renpy.hide_screen("mas_os_update_error")
        except Exception:
            pass
        return upd_start(False, src)

    def upd_on_enter():
        global upd_prompted, upd_need_ui, upd_cancelled, news_game_checked
        upd_prompted = False
        upd_need_ui = None
        upd_cancelled = False
        news_game_checked = True
        return upd_start(True)

    def upd_tick():
        global upd_need_ui, upd_prompted, news_banner_pending
        if upd_checking:
            return None
        try:
            if store.renpy.get_screen("mas_os_update_checking"):
                store.renpy.hide_screen("mas_os_update_checking")
        except Exception:
            pass
        need = upd_need_ui
        if need == "available" and not upd_can_show_prompt():
            news_maybe_banner()
            return None
        if need:
            upd_need_ui = None
            if need == "available":
                upd_prompted = True
                if upd_source != "local":
                    try:
                        notify_add(
                            u"Обновление порта",
                            u"Доступна версия {0}".format(upd_remote or ""),
                            source="updates",
                        )
                    except Exception:
                        pass
                in_room = False
                try:
                    in_room = bool(game_entered) and not store.renpy.get_screen("mas_os_home")
                except Exception:
                    in_room = bool(game_entered)
                if in_room:
                    news_banner_pending = True
                else:
                    try:
                        store.renpy.show_screen("mas_os_update_available")
                    except Exception:
                        pass
            elif need == "current":
                try:
                    store.renpy.show_screen("mas_os_update_current")
                except Exception:
                    pass
            elif need == "error":
                try:
                    store.renpy.show_screen("mas_os_update_error")
                except Exception:
                    pass
        news_maybe_banner()
        return None

    def _news_rgba(hexcol, alpha):
        s = (hexcol or "#000000").strip().lstrip("#")
        try:
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            return (r, g, b, int(max(0, min(255, alpha))))
        except Exception:
            return (0, 0, 0, int(alpha))


init python:
    import time
    import store

    class MASOSNewsTicker(renpy.Displayable):
        def __init__(self, width=430, height=30, **kwargs):
            super(MASOSNewsTicker, self).__init__(**kwargs)
            self.width = int(width)
            self.height = int(height)

        def _text(self, msg, alpha=1.0):
            child = Text(
                msg,
                size=14,
                color="#FFE6F3",
                outlines=[],
                font=gui.default_font,
                layout="nobreak",
                substitute=False,
            )
            if alpha < 0.999:
                child = Transform(child, alpha=alpha)
            return child

        def _state(self):
            osstore = store.mas_os
            msg = osstore.news_ticker_message()
            if not msg:
                return None
            now = time.time()
            if osstore.news_ticker_t0 is None:
                osstore.news_ticker_t0 = now
            tr = self._text(msg).render(16384, 64, 0, 0)
            tw, th = tr.get_size()
            clip_w = max(80, self.width - 40)
            x_start = 0
            x_end = min(0, int(clip_w) - int(tw))
            speed = 72.0
            fade_in = 0.32
            hold_start = 0.40
            hold_end = 0.95
            fade_out = 0.38
            pause = 0.55
            travel = float(x_start - x_end)
            if travel > 2:
                scroll_t = max(0.8, travel / speed)
            else:
                scroll_t = 0.0
                hold_end = 1.35
            cycle = fade_in + hold_start + scroll_t + hold_end + fade_out + pause
            t = (now - osstore.news_ticker_t0) % cycle
            xoff = x_start
            alpha = 1.0
            if t < fade_in:
                alpha = t / fade_in
                xoff = x_start
            elif t < fade_in + hold_start:
                alpha = 1.0
                xoff = x_start
            elif t < fade_in + hold_start + scroll_t:
                alpha = 1.0
                if scroll_t > 0:
                    p = (t - fade_in - hold_start) / scroll_t
                    xoff = x_start + (x_end - x_start) * p
                else:
                    xoff = x_start
            elif t < fade_in + hold_start + scroll_t + hold_end:
                alpha = 1.0
                xoff = x_end
            elif t < fade_in + hold_start + scroll_t + hold_end + fade_out:
                alpha = 1.0 - (
                    (t - fade_in - hold_start - scroll_t - hold_end) / fade_out
                )
                xoff = x_end
            else:
                alpha = 0.0
                xoff = x_start
            if alpha < 0:
                alpha = 0.0
            if alpha > 1:
                alpha = 1.0
            return {
                "msg": msg,
                "tw": int(tw),
                "th": int(th),
                "clip_w": int(clip_w),
                "alpha": alpha,
                "xoff": int(xoff),
            }

        def render(self, width, height, st, at):
            w = self.width
            h = self.height
            rv = renpy.Render(w, h)
            osstore = store.mas_os
            stt = self._state()
            if stt is None:
                renpy.redraw(self, 0.2)
                return rv

            canvas = rv.canvas()
            canvas.rect(
                osstore._news_rgba(osstore.theme_color("panel"), 220),
                (0, 0, w, h),
            )
            canvas.rect(
                osstore._news_rgba(osstore.theme_color("accent"), 255),
                (0, 0, 3, h),
            )
            ip = osstore.icon_path("megaphone")
            if ip:
                try:
                    ic = Transform(Image(ip), xysize=(20, 20))
                    ir = ic.render(20, 20, st, at)
                    rv.blit(ir, (8, int((h - 20) / 2)))
                except Exception:
                    pass

            clip_w = stt["clip_w"]
            xoff = stt["xoff"]
            tw = stt["tw"]
            th = stt["th"]
            alpha = stt["alpha"]
            if alpha > 0.02 and tw > 0:
                if xoff >= 0:
                    src_x = 0
                    dst_x = xoff
                    vis_w = min(clip_w - dst_x, tw)
                else:
                    src_x = -xoff
                    dst_x = 0
                    vis_w = min(clip_w, tw - src_x)
                vis_w = int(max(0, vis_w))
                vis_h = int(min(h, max(1, th)))
                src_x = int(max(0, src_x))
                dst_x = int(max(0, dst_x))
                if vis_w > 1 and src_x < tw:
                    full = Transform(
                        self._text(stt["msg"]),
                        alpha=alpha,
                    ).render(16384, 64, st, at)
                    fw, fh = full.get_size()
                    vis_w = min(vis_w, max(0, int(fw) - src_x))
                    vis_h = min(vis_h, max(1, int(fh)))
                    if vis_w > 1:
                        try:
                            piece = full.subsurface((src_x, 0, vis_w, vis_h))
                        except Exception:
                            piece = None
                        if piece is not None:
                            ty = int((h - vis_h) / 2)
                            rv.blit(piece, (32 + dst_x, ty))

            renpy.redraw(self, 0.03)
            return rv

        def event(self, ev, x, y, st):
            try:
                import pygame
            except Exception:
                return None
            if getattr(ev, "type", None) != pygame.MOUSEBUTTONUP:
                return None
            if getattr(ev, "button", 0) != 1:
                return None
            if x < 0 or y < 0 or x >= self.width or y >= self.height:
                return None
            if self._state() is None:
                return None
            try:
                store.mas_os.upd_show_available()
            except Exception:
                pass
            return True

    if "mas_os_news_ticker_game" not in config.overlay_screens:
        config.overlay_screens.append("mas_os_news_ticker_game")


screen mas_os_update_checking():
    modal True
    zorder 320

    $ _line = store.mas_os.upd_checking_line()

    add Solid("#000000C0")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 640
        ysize 228
        background Solid(store.mas_os.theme_color("panel"))
        padding (28, 24)

        vbox:
            spacing 12
            xfill True

            text _("Проверка обновлений"):
                style "mas_os_title"
                size 28
                xalign 0.5

            text _line:
                style "mas_os_body"
                xalign 0.5
                text_align 0.5
                xsize 560
                substitute False

            frame:
                xalign 0.5
                xsize 480
                ysize 14
                background Solid(store.mas_os.theme_color("panel2"))

                frame:
                    at mas_os_gen_bar_slide
                    xsize 90
                    ysize 14
                    background Solid(store.mas_os.theme_color("accent"))

            textbutton _("Отмена"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xalign 0.5
                action Function(store.mas_os.upd_cancel)

    timer 0.15 repeat True action Function(store.mas_os.upd_tick)
    key "K_ESCAPE" action Function(store.mas_os.upd_cancel)
    key "K_AC_BACK" action Function(store.mas_os.upd_cancel)


screen mas_os_update_available():
    modal True
    zorder 320

    $ _local = store.mas_os.upd_local_version()
    $ _mas = store.mas_os.upd_mas_version()
    $ _remote = store.mas_os.upd_remote or ""
    $ _ch = _("Локальный тест") if store.mas_os.upd_is_local() else store.mas_os.upd_channel_label()
    $ _news_title = store.mas_os.upd_news_title or ""
    $ _rows = store.mas_os.upd_news_rows()

    add Solid("#000000C0")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 1040
        ysize 640
        background Solid(store.mas_os.theme_color("panel"))
        padding (24, 18)

        vbox:
            spacing 10
            xfill True

            hbox:
                xfill True
                spacing 12

                vbox:
                    spacing 2

                    text _("Доступно обновление"):
                        style "mas_os_title"
                        size 30

                    text _("Канал: [_ch]"):
                        style "mas_os_hint"

                null:
                    xfill True

                vbox:
                    spacing 2
                    xsize 420

                    text _("Порт [_local]  →  [_remote]"):
                        style "mas_os_subtitle"
                        xalign 1.0

                    text _("MAS [_mas]"):
                        style "mas_os_hint"
                        xalign 1.0

            if _news_title:
                text _news_title:
                    style "mas_os_subtitle"
                    size 20
                    substitute False

            frame:
                background Solid(store.mas_os.theme_color("panel2"))
                xsize 992
                ysize 430
                padding (14, 10)

                viewport:
                    xysize (964, 410)
                    draggable True
                    mousewheel True
                    scrollbars "vertical"

                    vbox:
                        spacing 8
                        xsize 930

                        if not _rows:
                            text _("Описание обновления не приложили. Новая версия всё равно доступна."):
                                style "mas_os_hint"
                                xsize 900
                        else:
                            for _blk in _rows:
                                if _blk["kind"] == "space":
                                    null height 8
                                elif _blk["kind"] == "hr":
                                    frame:
                                        xsize 900
                                        ysize 2
                                        background Solid(store.mas_os.theme_color("accent"))
                                elif _blk["kind"] == "h1":
                                    text _blk["text"]:
                                        style "mas_os_title"
                                        size 26
                                        xsize 900
                                        substitute False
                                elif _blk["kind"] == "h2":
                                    text _blk["text"]:
                                        style "mas_os_subtitle"
                                        size 22
                                        xsize 900
                                        substitute False
                                elif _blk["kind"] == "h3":
                                    text _blk["text"]:
                                        style "mas_os_subtitle"
                                        size 18
                                        xsize 900
                                        substitute False
                                elif _blk["kind"] == "quote":
                                    hbox:
                                        spacing 10
                                        xsize 900
                                        xfill True

                                        add Solid(store.mas_os.theme_color("accent")):
                                            xsize 4
                                            ysize 28

                                        text _blk["text"]:
                                            style "mas_os_hint"
                                            italic True
                                            size 17
                                            xsize 870
                                            text_align 0.0
                                            xalign 0.0
                                            layout "tex"
                                            substitute False
                                elif _blk["kind"] == "li":
                                    hbox:
                                        spacing 10
                                        xsize 900
                                        xfill True

                                        text _blk.get("mark", "•"):
                                            size 17
                                            color store.mas_os.theme_color("subtitle")
                                            outlines []
                                            xsize 32
                                            text_align 0.0
                                            xalign 0.0
                                            substitute False

                                        text _blk["text"]:
                                            style "mas_os_body"
                                            size 17
                                            xsize 850
                                            text_align 0.0
                                            xalign 0.0
                                            layout "tex"
                                            substitute False
                                else:
                                    text _blk["text"]:
                                        style "mas_os_body"
                                        size 18
                                        xsize 900
                                        text_align 0.0
                                        xalign 0.0
                                        layout "tex"
                                        substitute False

            if store.mas_os.upd_is_local():
                text _("Это локальный превью. GitHub не вызывался, игрокам это не уйдёт."):
                    style "mas_os_hint"
            else:
                text _("Сама игра не качается: открой репозиторий и поставь сборку порта вручную."):
                    style "mas_os_hint"

            hbox:
                spacing 12
                xalign 0.5

                if store.mas_os.upd_is_local():
                    textbutton _("Понятно"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        action Function(store.mas_os.upd_later)
                else:
                    textbutton _("Открыть GitHub"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        action Function(store.mas_os.upd_open_repo)

                    textbutton _("Позже"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        action Function(store.mas_os.upd_later)

                    textbutton _("Пропустить"):
                        style "mas_os_nav_btn"
                        text_style "mas_os_nav_btn_text"
                        action Function(store.mas_os.upd_skip)

    key "K_ESCAPE" action Function(store.mas_os.upd_later)
    key "K_AC_BACK" action Function(store.mas_os.upd_later)


screen mas_os_update_current():
    modal True
    zorder 320

    $ _local = store.mas_os.upd_local_version()
    $ _mas = store.mas_os.upd_mas_version()
    $ _ch = _("локальный файл") if store.mas_os.upd_is_local() else store.mas_os.upd_channel_label()
    $ _fn = store.mas_os.UPDATE_LOCAL_REL if store.mas_os.upd_is_local() else store.mas_os.upd_channel_file()

    add Solid("#000000C0")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 640
        background Solid(store.mas_os.theme_color("panel"))
        padding (28, 24)

        vbox:
            spacing 14
            xfill True

            text _("Порт актуален"):
                style "mas_os_title"
                size 28
                xalign 0.5

            text _("Порт [_local] (MAS [_mas]). Файл [_fn] на канале «[_ch]» совпадает."):
                style "mas_os_body"
                xalign 0.5
                text_align 0.5
                xsize 560

            textbutton _("Понятно"):
                style "mas_os_nav_btn"
                text_style "mas_os_nav_btn_text"
                xalign 0.5
                action Function(store.mas_os.upd_hide_current)

    key "K_ESCAPE" action Function(store.mas_os.upd_hide_current)
    key "K_AC_BACK" action Function(store.mas_os.upd_hide_current)


screen mas_os_update_error():
    modal True
    zorder 320

    $ _err = store.mas_os.upd_error or _("неизвестная ошибка")
    $ _hint = store.mas_os.upd_error_hint()

    add Solid("#000000C0")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 640
        background Solid(store.mas_os.theme_color("panel"))
        padding (28, 24)

        vbox:
            spacing 14
            xfill True

            text _("Не удалось проверить"):
                style "mas_os_title"
                size 28
                xalign 0.5

            text _hint:
                style "mas_os_body"
                xalign 0.5
                text_align 0.5
                xsize 560
                substitute False

            text _err:
                style "mas_os_hint"
                xalign 0.5
                text_align 0.5
                xsize 560
                substitute False

            hbox:
                spacing 12
                xalign 0.5

                textbutton _("Ещё раз"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    action Function(store.mas_os.upd_retry)

                textbutton _("Закрыть"):
                    style "mas_os_nav_btn"
                    text_style "mas_os_nav_btn_text"
                    action Function(store.mas_os.upd_hide_error)

    key "K_ESCAPE" action Function(store.mas_os.upd_hide_error)
    key "K_AC_BACK" action Function(store.mas_os.upd_hide_error)


transform mas_os_banner_in:
    alpha 0.0
    yoffset -14
    ease 0.32 alpha 1.0 yoffset 0


transform mas_os_banner_out:
    ease 0.22 alpha 0.0 yoffset -10


screen mas_os_news_banner():
    modal False
    zorder 325

    $ _msg = store.mas_os._news_banner_now or ""

    if _msg:
        button:
            xalign 0.5
            ypos 70
            xmaximum 740
            background None
            action Function(store.mas_os.news_banner_click)
            at mas_os_banner_in

            frame:
                background Solid("#000000E6")
                padding (22, 14)
                xmaximum 740

                text _msg:
                    style "mas_os_body"
                    size 16
                    text_align 0.5
                    xalign 0.5
                    xmaximum 696
                    substitute False

    timer 4.6 action Function(store.mas_os.news_hide_banner)
    key "K_ESCAPE" action Function(store.mas_os.news_hide_banner)


screen mas_os_news_ticker_overlay():
    modal False
    zorder 350

    add MASOSNewsTicker(width=380, height=30):
        xpos 16
        ypos 12

    textbutton _("Закрыть тест"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 16
        ypos 50
        action Function(store.mas_os.news_hide_ticker_overlay)

    key "K_ESCAPE" action Function(store.mas_os.news_hide_ticker_overlay)
    key "K_AC_BACK" action Function(store.mas_os.news_hide_ticker_overlay)


screen mas_os_news_ticker_game():
    zorder 45

    if store.mas_os.news_ticker_game_on():
        add MASOSNewsTicker(width=360, height=28):
            xpos 14
            ypos 12

    timer 0.5 repeat True action Function(store.mas_os.upd_tick)

