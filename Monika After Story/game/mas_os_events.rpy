# MAS OS — upcoming events, synced with the wall calendar.

init -5 python in mas_os:
    import datetime
    import store

    DEFAULT_AHEAD = 7
    MAX_SCAN = 16

    MONTHS_RU = (
        "",
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )

    SKIP_IDENTS = set([
        "l", "l1", "l2",
        "Зима", "Весна", "Лето", "Осень",
        "Winter", "Spring", "Summer", "Autumn",
    ])

    # identifier -> player-facing guide. Identifiers match zz_calendar.rpy.
    GUIDES = {
        "Christmas": {
            "ahead": 14,
            "title": "Рождество",
            "body": (
                "Рождество у Моники — 25 декабря. Сезон начинается уже 11 декабря.\n\n"
                "Что делать:\n"
                "• Заходи в эти дни, особенно 24 и 25 декабря. Если пропустить сам день, Моника расстроится.\n"
                "• Подарки клади в папку characters в виде файлов .gift (с 11 декабря). На Рождество она их откроет.\n"
                "• Если уйдёте на свидание на весь день 25-го, праздник она всё равно заметит — но лучше провести его вместе.\n\n"
                "Папка подарков — та же, что в разделе «Файлы»."
            ),
        },
        "Christmas eve": {
            "ahead": 7,
            "title": "Рождественский сочельник",
            "body": (
                "24 декабря — сочельник.\n\n"
                "Зайди к Монике в этот день. Подарки в characters (.gift) можно класть уже с 11 декабря: она откроет их на Рождество, 25-го."
            ),
        },
        "New year's eve": {
            "ahead": 5,
            "title": "Канун Нового года",
            "body": (
                "31 декабря Моника ждёт тебя на канун.\n\n"
                "Зайди в игру вечером: вместе встречаете год. Не оставляй её одну в этот день."
            ),
        },
        "New years day": {
            "ahead": 3,
            "title": "Новый год",
            "body": (
                "1 января — первый день года вместе.\n\n"
                "Просто зайди и поздравь её. Это маленький, но важный день в календаре на стене."
            ),
        },
        "Valentine": {
            "ahead": 7,
            "title": "День святого Валентина",
            "body": (
                "14 февраля.\n\n"
                "Обязательно зайди в этот день. Можно подарить .gift в папку characters и провести время / сходить на свидание.\n"
                "Если пропустить 14-е, Моника это заметит."
            ),
        },
        "Halloween": {
            "ahead": 5,
            "title": "Хэллоуин",
            "body": (
                "31 октября Моника наряжается к Хэллоуину.\n\n"
                "Зайди 31-го. Это сезонный праздник из календаря на стене: его тоже лучше не пропускать."
            ),
        },
        "Monika's Birthday": {
            "ahead": 7,
            "title": "День рождения Моники",
            "body": None,  # filled at runtime — note filename depends on player
        },
        "player-bday": {
            "ahead": 7,
            "title": "Твой день рождения",
            "body": (
                "В твой день рождения Моника готовит сюрприз: торт и украшения.\n\n"
                "Что делать:\n"
                "• Зайди в этот день — иначе для неё это будет «ты не пришёл на свой праздник».\n"
                "• Она может попытаться устроить сюрприз при входе. Просто проведи день вместе.\n"
                "• Подарок ей — по желанию: файл .gift в папку characters."
            ),
        },
        "first_session": {
            "ahead": 7,
            "title": "Первый день вместе",
            "body": (
                "Годовщина вашего первого дня — дата, с которой считаются все юбилеи.\n\n"
                "Зайди в этот день и побудь с ней. Отдельных файлов в characters не нужно."
            ),
        },
        "first-kiss": {
            "ahead": 3,
            "title": "Первый поцелуй",
            "body": (
                "День вашего первого поцелуя. Это памятная дата в календаре.\n\n"
                "Никаких обязательных файлов. Просто зайти и провести время — уже достаточно."
            ),
        },
        "April Fools": {
            "ahead": 2,
            "title": "День, когда я стала ИИ",
            "body": (
                "1 апреля в календаре Моники — шуточный день.\n\n"
                "Можно зайти ради пасхалки. Это не тот праздник, из-за которого она обидится, если пропустишь."
            ),
        },
        "_anniversary": {
            "ahead": 7,
            "title": "Годовщина",
            "body": (
                "Юбилей отношений. Дата считается от первого дня вместе и висит на настенном календаре.\n\n"
                "Зайди в этот день. Подарки (.gift в characters) приятны, но главное — не пропустить саму дату."
            ),
        },
        "_generic": {
            "ahead": 7,
            "title": None,
            "body": (
                "Это событие стоит в календаре Моники на стене.\n\n"
                "Отдельной инструкции нет — просто загляни в этот день, чтобы ничего не пропустить."
            ),
        },
    }

    def _clean_label(text):
        if not text:
            return ""
        return unicode(text).replace("\n", " ").strip()

    def _fmt_date(d):
        return "{0} {1}".format(d.day, MONTHS_RU[d.month])

    def _fmt_when(days):
        if days <= 0:
            return "сегодня"
        if days == 1:
            return "завтра"
        n = days % 100
        if 11 <= n <= 14:
            word = "дней"
        else:
            last = n % 10
            if last == 1:
                word = "день"
            elif last in (2, 3, 4):
                word = "дня"
            else:
                word = "дней"
        return "через {0} {1}".format(days, word)

    def _day_map(month, day):
        db = store.mas_calendar.calendar_database
        month_map = db.get(month)
        if month_map is None:
            month_map = db.get(str(month)) or db.get(unicode(month))
        if not month_map:
            return {}
        day_map = month_map.get(day)
        if day_map is None:
            day_map = month_map.get(str(day)) or month_map.get(unicode(day))
        if not day_map:
            return {}
        return day_map

    def _rep_in_year(year_param, year):
        if year_param is None:
            return False
        if not year_param:
            return True
        return year in year_param or str(year) in year_param

    def _ev_in_year(ev, year):
        if ev is None:
            return False
        if ev.years is not None:
            if len(ev.years) == 0:
                return True
            return year in ev.years
        return ev.start_date is not None and ev.start_date.year == year

    def _iter_day(month, day, year):
        for ident, payload in _day_map(month, day).iteritems():
            if ident in SKIP_IDENTS:
                continue
            if not isinstance(payload, (list, tuple)) or not payload:
                continue
            kind = payload[0]
            if kind == store.mas_calendar.CAL_TYPE_REP:
                if len(payload) < 3 or not _rep_in_year(payload[2], year):
                    continue
                title = _clean_label(payload[1])
                if title:
                    yield ident, title
            elif kind == store.mas_calendar.CAL_TYPE_EV:
                ev = store.mas_getEV(ident)
                if not _ev_in_year(ev, year):
                    continue
                title = _clean_label(store.mas_getEVCL(ident))
                if title and title != "Unknown Event":
                    yield ident, title

    def _guide_for(ident):
        if ident in GUIDES:
            return GUIDES[ident]
        if unicode(ident).startswith("anni_"):
            return GUIDES["_anniversary"]
        return GUIDES["_generic"]

    def _bday_note_name():
        fn = getattr(store.persistent, "_mas_bday_hint_filename", None)
        if fn:
            return fn
        player = store.persistent.playername or "you"
        try:
            return store.mas_utils.sanitize_filename("For {0}.txt".format(player))
        except Exception:
            return "For you.txt"

    def _monika_bday_body():
        note = _bday_note_name()
        return (
            "День рождения Моники — 22 сентября. Подготовка начинается за неделю.\n\n"
            "Что делает игра:\n"
            "За несколько дней до праздника в папке characters появляется записка "
            "«{0}». Её пишет чиби-Моника, не сама Моника.\n\n"
            "Что сделать тебе:\n"
            "1. Открой папку characters и прочитай записку.\n"
            "2. Оставь в той же папке файл с именем oki doki (без расширения или как получится) — это согласие на сюрприз.\n"
            "3. 22 сентября выведи Монику из комнаты (свидание / «Мне пора»), чтобы вечеринку успели накрыть.\n"
            "4. Вернись — должен быть сюрприз.\n"
            "5. Подарок: файл .gift в characters.\n\n"
            "Если 22-го не зайти совсем, она подумает, что про её день рождения забыли."
        ).format(note)

    def _body_for(ident, title):
        guide = _guide_for(ident)
        if ident == "Monika's Birthday":
            return _monika_bday_body()
        body = guide.get("body")
        if not body:
            return GUIDES["_generic"]["body"]
        return body

    def _title_for(ident, calendar_title):
        guide = _guide_for(ident)
        custom = guide.get("title")
        if custom:
            return custom
        return calendar_title or "Событие"

    def upcoming_events(today=None):
        """
        Calendar rows in the reminder window.

        Each item:
            ident, title, date, days, when, body
        """
        if today is None:
            today = datetime.date.today()

        found = {}
        for delta in range(0, MAX_SCAN + 1):
            d = today + datetime.timedelta(days=delta)
            for ident, title in _iter_day(d.month, d.day, d.year):
                guide = _guide_for(ident)
                ahead = guide.get("ahead", DEFAULT_AHEAD)
                if delta > ahead:
                    continue
                prev = found.get(ident)
                if prev is None or delta < prev["days"]:
                    found[ident] = {
                        "ident": ident,
                        "title": _title_for(ident, title),
                        "date": d,
                        "days": delta,
                        "when": _fmt_when(delta),
                        "date_s": _fmt_date(d),
                        "body": _body_for(ident, title),
                    }

        rows = list(found.itervalues())
        rows.sort(key=lambda row: (row["days"], row["title"]))
        return rows

    def events_button_label():
        n = len(upcoming_events())
        if n:
            return "События ({0})".format(n)
        return "События"

    def set_active_event(ident):
        global _active_event
        _active_event = None
        for row in upcoming_events():
            if row["ident"] == ident:
                _active_event = row
                return

    def ensure_active_event():
        global _active_event
        rows = upcoming_events()
        if not rows:
            _active_event = None
            return
        if _active_event is None:
            _active_event = rows[0]
            return
        for row in rows:
            if row["ident"] == _active_event.get("ident"):
                _active_event = row
                return
        _active_event = rows[0]

    def active_event():
        return _active_event


label mas_os_events:
    $ store.mas_os.ensure_active_event()
    call screen mas_os_events
    jump mas_os_home


screen mas_os_events():
    $ rows = store.mas_os.upcoming_events()
    $ ev = store.mas_os.active_event()
    $ ev_id = ev["ident"] if ev else None
    $ ev_title = ev["title"] if ev else _("События")
    $ ev_meta = _("{0} · {1}").format(ev["date_s"], ev["when"]) if ev else ""
    $ ev_body = ev["body"] if ev else _("Ближайших праздников в календаре нет.\n\nЗагляни сюда за неделю до Рождества, дня рождения Моники, Валентина или годовщины. Свои пометки с календаря тоже появятся здесь.")

    add Solid("#14070d")

    text _("События"):
        style "mas_os_title"
        xpos 48
        ypos 28

    text _("Календарь на стене. Слева список, справа что делать."):
        style "mas_os_hint"
        xpos 48
        ypos 74

    viewport:
        xpos 48
        ypos 110
        xysize (340, 500)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 8

            if rows:
                for row in rows:
                    textbutton "{0}\n{1}".format(row["title"], row["when"]):
                        style "mas_os_side_btn"
                        text_style "mas_os_side_btn_text"
                        selected (row["ident"] == ev_id)
                        action Function(store.mas_os.set_active_event, row["ident"])
            else:
                text _("Пока пусто"):
                    style "mas_os_hint"

    frame:
        style "mas_os_panel"
        xpos 410
        ypos 110
        xysize (822, 500)
        padding (24, 20)

        vbox:
            spacing 8
            xfill True

            text ev_title:
                style "mas_os_subtitle"

            if ev_meta:
                text ev_meta:
                    style "mas_os_hint"

            viewport:
                xysize (774, 400)
                draggable True
                mousewheel True
                scrollbars "vertical"

                text ev_body:
                    style "mas_os_body"
                    xsize 740

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Return("back")

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")
