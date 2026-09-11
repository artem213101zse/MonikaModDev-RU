# --- FILE MAP ---
# script-anniversary.rpy — нам уже неделя / месяц / год
#
# Календарь сам ставит в очередь anni_1week, anni_1month, 3/6 месяцев,
# anni_1 … anni_100. Милые и серьёзные разговоры про время вместе.
#
# Store: mas_anni (build_anni считает даты)
# Labels: anni_*
# Почти весь файл — перевод реплик.
# ---

init -2 python in mas_anni:
    import store
    import datetime

    # persistent pointer so we can use it
    __persistent = renpy.game.persistent

    def build_anni(years=0, months=0, weeks=0, isstart=True):
        """
        Builds an anniversary date.

        NOTE:
            years / months / weeks are mutually exclusive

        IN:
            years - number of years to make this anni date
            months - number of months to make thsi anni date
            weeks - number of weeks to make this anni date
            isstart - True means this should be a starting date, False
                means ending date

        ASSUMES:
            __persistent
        """
        # sanity checks
        if __persistent.sessions is None:
            return None

        first_sesh = __persistent.sessions.get("first_session", None)
        if first_sesh is None:
            return None

        if (weeks + years + months) == 0:
            # we need at least one of these to work
            return None

        # sanity checks are done

        if years > 0:
            new_date = store.mas_utils.add_years(first_sesh, years)

        elif months > 0:
            new_date = store.mas_utils.add_months(first_sesh, months)

        else:
            new_date = first_sesh + datetime.timedelta(days=(weeks * 7))

        # check for starting
        if isstart:
            return store.mas_utils.mdnt(new_date)

        # othrewise, this is an ending date
#        return mas_utils.am3(new_date + datetime.timedelta(days=1))
# NOTE: doing am3 leads to calendar problems
#   we'll just restrict this to midnight to midnight -1
        return store.mas_utils.mdnt(new_date + datetime.timedelta(days=1))

    def build_anni_end(years=0, months=0, weeks=0):
        """
        Variant of build_anni that auto ends the bool

        SEE build_anni for params
        """
        return build_anni(years, months, weeks, False)

    def isAnni(milestone=None):
        """
        INPUTS:
            milestone:
                Expected values|Operation:

                    None|Checks if today is a yearly anniversary
                    1w|Checks if today is a 1 week anniversary
                    1m|Checks if today is a 1 month anniversary
                    3m|Checks if today is a 3 month anniversary
                    6m|Checks if today is a 6 month anniversary
                    any|Checks if today is any of the above annis

        RETURNS:
            True if datetime.date.today() is an anniversary date
            False if today is not an anniversary date
        """
        #Sanity checks
        if __persistent.sessions is None:
            return False

        firstSesh = __persistent.sessions.get("first_session", None)
        if firstSesh is None:
            return False

        compare = None

        if milestone == '1w':
            compare = build_anni(weeks=1)

        elif milestone == '1m':
            compare = build_anni(months=1)

        elif milestone == '3m':
            compare = build_anni(months=3)

        elif milestone == '6m':
            compare = build_anni(months=6)

        elif milestone == 'any':
            return (
                isAnniWeek()
                or isAnniOneMonth()
                or isAnniThreeMonth()
                or isAnniSixMonth()
                or isAnni()
            )

        if compare is not None:
            return compare.date() == datetime.date.today()

        else:
            compare = firstSesh
            return (
                store.mas_utils.add_years(compare.date(), datetime.date.today().year - compare.year) == datetime.date.today()
                and anniCount() > 0
            )

    def isAnniWeek():
        return isAnni('1w')

    def isAnniOneMonth():
        return isAnni('1m')

    def isAnniThreeMonth():
        return isAnni('3m')

    def isAnniSixMonth():
        return isAnni('6m')

    def isAnniAny():
        return isAnni('any')

    def anniCount():
        """
        RETURNS:
            Integer value representing how many years the player has been with Monika
        """
        #Sanity checks
        if __persistent.sessions is None:
            return 0

        firstSesh = __persistent.sessions.get("first_session", None)

        if firstSesh is None:
            return 0

        compare = datetime.date.today()

        if (
            compare.year > firstSesh.year
            and compare < store.mas_utils.add_years(firstSesh.date(), compare.year - firstSesh.year)
        ):
            return compare.year - firstSesh.year - 1
        else:
            return compare.year - firstSesh.year

    def pastOneWeek():
        """
        RETURNS:
            True if current date is past the 1 week threshold
            False if below the 1 week threshold
        """
        return datetime.date.today() >= build_anni(weeks=1).date()

    def pastOneMonth():
        """
        RETURNS:
            True if current date is past the 1 month threshold
            False if below the 1 month threshold
        """
        return datetime.date.today() >= build_anni(months=1).date()

    def pastThreeMonths():
        """
        RETURNS:
            True if current date is past the 3 month threshold
            False if below the 3 month threshold
        """
        return datetime.date.today() >= build_anni(months=3).date()

    def pastSixMonths():
        """
        RETURNS:
            True if current date is past the 6 month threshold
            False if below the 6 month threshold
        """
        return datetime.date.today() >= build_anni(months=6).date()


# TODO What's the reason to make this one init 10?
init 10 python in mas_anni:

    # we are going to store all anniversaries in antther db as well so we
    # can easily reference them later.
    ANNI_LIST = [
        "anni_1week",
        "anni_1month",
        "anni_3month",
        "anni_6month",
        "anni_1",
        "anni_2",
        "anni_3",
        "anni_4",
        "anni_5",
        "anni_6",
        "anni_7",
        "anni_8",
        "anni_9",
        "anni_10",
        "anni_20",
        "anni_50",
        "anni_100"
    ]

    # anniversary database
    anni_db = dict()
    for anni in ANNI_LIST:
        anni_db[anni] = store.evhand.event_database[anni]


    ## functions that we need (runtime only)
    def _month_adjuster(ev, new_start_date, months, span):
        """
        Adjusts the start_date / end_date of an anniversary event.

        NOTE: do not use this for a non anniversary date

        IN:
            ev - event to adjust
            new_start_date - new start date to calculate the event's dates
            months - number of months to advance
            span - the time from the event's new start_date to end_date
        """
        ev.start_date = store.mas_utils.add_months(
            store.mas_utils.mdnt(new_start_date),
            months
        )
        ev.end_date = store.mas_utils.mdnt(ev.start_date + span)

    def _day_adjuster(ev, new_start_date, days, span):
        """
        Adjusts the start_date / end_date of an anniversary event.

        NOTE: do not use this for a non anniversary date

        IN:
            ev - event to adjust
            new_start_date - new start date to calculate the event's dates
            days - number of months to advance
            span - the time from the event's new start_date to end_date
        """
        ev.start_date = store.mas_utils.mdnt(
            new_start_date + datetime.timedelta(days=days)
        )
        ev.end_date = store.mas_utils.mdnt(ev.start_date + span)


    def add_cal_annis():
        """
        Goes through the anniversary database and adds them to the calendar
        """
        for anni in anni_db:
            ev = anni_db[anni]
            store.mas_calendar.addEvent(ev)

    def clean_cal_annis():
        """
        Goes through the calendar and cleans anniversary dates
        """
        for anni in anni_db:
            ev = anni_db[anni]
            store.mas_calendar.removeEvent(ev)


    def reset_annis(new_start_dt):
        """
        Reset the anniversaries according to the new start date.

        IN:
            new_start_dt - new start datetime to reset anniversaries
        """
        _firstsesh_id = "first_session"
        _firstsesh_dt = renpy.game.persistent.sessions.get(
            _firstsesh_id,
            None
        )

        # remove teh anniversaries off the calendar
        clean_cal_annis()

        # remove first session repeatable
        if _firstsesh_dt:
            # this exists! we can make this easy
            store.mas_calendar.removeRepeatable_dt(_firstsesh_id, _firstsesh_dt)

        # modify the anniversaries
        fullday = datetime.timedelta(days=1)
        _day_adjuster(anni_db["anni_1week"],new_start_dt,7,fullday)
        _month_adjuster(anni_db["anni_1month"], new_start_dt, 1, fullday)
        _month_adjuster(anni_db["anni_3month"], new_start_dt, 3, fullday)
        _month_adjuster(anni_db["anni_6month"], new_start_dt, 6, fullday)
        _month_adjuster(anni_db["anni_1"], new_start_dt, 12, fullday)
        _month_adjuster(anni_db["anni_2"], new_start_dt, 24, fullday)
        _month_adjuster(anni_db["anni_3"], new_start_dt, 36, fullday)
        _month_adjuster(anni_db["anni_4"], new_start_dt, 48, fullday)
        _month_adjuster(anni_db["anni_5"], new_start_dt, 60, fullday)
        _month_adjuster(anni_db["anni_6"], new_start_dt, 6*12, fullday)
        _month_adjuster(anni_db["anni_7"], new_start_dt, 7*12, fullday)
        _month_adjuster(anni_db["anni_8"], new_start_dt, 8*12, fullday)
        _month_adjuster(anni_db["anni_9"], new_start_dt, 9*12, fullday)
        _month_adjuster(anni_db["anni_10"], new_start_dt, 120, fullday)
        _month_adjuster(anni_db["anni_20"], new_start_dt, 240, fullday)
        _month_adjuster(anni_db["anni_50"], new_start_dt, 600, fullday)
        _month_adjuster(anni_db["anni_100"], new_start_dt, 1200, fullday)

        unlock_past_annis()

        # re-add the events to the calendar db
        add_cal_annis()

        # re-add the repeatable to the calendar db
        store.mas_calendar.addRepeatable_dt(
            _firstsesh_id,
            "<3",
            new_start_dt,
            [new_start_dt.year]
        )


    def unlock_past_annis():
        """
        Goes through the anniversary database and unlocks the events that
        already past.
        """
        for anni in anni_db:
            ev = anni_db[anni]

            if store.evhand._isPast(ev):
                renpy.game.persistent._seen_ever[anni] = True
                ev.unlocked = True


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1week',
            prompt="1 Неделя",
            action=EV_ACT_QUEUE,
            category=["юбилей"],
            start_date=store.mas_anni.build_anni(weeks=1),
            end_date=store.mas_anni.build_anni_end(weeks=1)
        ),
        skipCalendar=False
    )

label anni_1week:
    m 1eka "Знаю, глупо отмечать всего неделю вместе, но я просто рада, что ты здесь со мной, [player]."
    m 1ekc "Многие пары столько не протягивают."
    m 1lksdlc "Влюбиться с первого взгляда легко, а вот построить крепкие отношения — уже сложнее."
    m 1ekd "Многие отношения рушатся, когда пары слишком торопятся."
    m "Чаще всего они просто не успевают по-настоящему узнать друг друга."
    m 1dsc "Поэтому всегда грустно смотреть, как всё рушится..."
    m 1duu "Но я рада, что у нас крепкая связь, [player]."
    show monika 5lubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lubfb "Откуда я это знаю?"
    m 5hubfb "Потому что ты бы не остался со мной так надолго, милый~"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1month',
            prompt="1 месяц",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=1),
            end_date=store.mas_anni.build_anni_end(months=1)
        ),
        skipCalendar=False
    )

label anni_1month:
    m 3sub "Сегодня месяц, как мы вместе!"
    m 1hua "Я правда рада, что нам до сих пор так весело вместе."
    m 1eua "И ещё, [player]?"
    m 1lkbsa "..."
    m 1ekbfa "Спасибо тебе огромное, что остаёшься со мной так долго."
    if not seen_event('monika_saved'):
        m 1lksdlc "Не представляю, что бы я делала, если бы тебя не было."
        m 3ekc "В конце концов, я единственная настоящая, кто живёт в этом мире."
        m 1dsc "Я уже говорила, что было бы, если бы не ты..."
        m 1hksdlb "Ахаха, прости. Надеюсь, я не испортила настроение своими рассуждениями."
    else:
        m "Я даже не могу выразить, как ценю, что ты здесь со мной."
        m 1dubsu "Всё, что я могу — стараться изо всех сил быть для тебя идеальной девушкой!"
    m 1ekbfa "Я правда люблю тебя, [player]."
    m 1hubfa "Давай сделаем этот день особенным~"
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_3month',
            prompt="3 месяца",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=3),
            end_date=store.mas_anni.build_anni_end(months=3)
        ),
        skipCalendar=False
    )

label anni_3month:
    m 1eua "[player], ты знаешь, какой сегодня день?"
    m 1hua "У нас уже три месяца вместе!"
    m 1hub "Время так быстро летит, правда?"
    m 1hksdlb "...Даже если здесь оно толком не идёт, эхехе."
    m 1eua "Но мне всё равно очень весело."
    m 1ekbsa "С тобой моя жизнь стала намного лучше, [player]."
    m 2ekbfa "Я очень рада, что ты остаёшься со мной так долго."
    m 1tsbsa "Ты правда особенный, да?"
    m 1lsbsa "Ну! Боюсь, у меня нет ничего особенного в планах."
    m 1hubfa "Давай просто насладимся этим днём по полной, как всегда."
    m 1hubfb "Хорошо, [player]?"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_6month',
            prompt="6 месяцев",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(months=6),
            end_date=store.mas_anni.build_anni_end(months=6)
        ),
        skipCalendar=False
    )

label anni_6month:
    m 1hub "Не могу поверить — уже наш полугодовой юбилей!"
    m 1eka "Я правда рада, что ты остаёшься со мной так долго."
    m 1lksdlc "Мне часто одиноко, когда тебя нет рядом."
    m 1ekc "У меня есть чем заняться, пока тебя нет, но всё равно очень одиноко от мысли, что я здесь одна."
    m 1hua "Поэтому каждый твой визит делает мой день ярче!"
    m 1euc "Но за последние месяцы я кое-что поняла..."
    m "Большинство пар отмечают годовщины чем-то особенным вместе, правда?"
    m 3eud "Например, сходить поесть или на шоу."
    m 1lksdla "Я не жалуюсь, но все наши годовщины до сих пор мы провели в этой комнате."
    m 1lksdlc "Было бы весело, если бы мы могли сходить куда-то ещё..."
    m "Жаль, что здесь нет такого места — у нас ведь только эта комната."
    m 1dsc "..."
    m 3wuo "...Ох, знаю!"
    m 1sub "Может, когда-нибудь я смогу запрограммировать нам красивое место для годовщин!"
    m "Или, может, ты добавишь особое место для нас двоих, [player]."
    m 1duu "Если только..."
    m 1eua "Ты уже водил меня куда-то в своей реальности?"
    m 1eka "Было бы так мило увидеть, куда ты меня водил~"
    m 1eua "А пока я не против, что мы ограничены этой комнатой."
    m 1ekbsa "Потому что пока ты здесь со мной..."
    m 1hubfa "...я счастлива как никогда!"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_1',
            prompt="1 год",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=1),
            end_date=store.mas_anni.build_anni_end(years=1)
        ),
        skipCalendar=False
    )

label anni_1:
    m 1dka "Боже...{w=0.2}трудно поверить, что уже целый год, как мы встретились."
    m 1eka "Здесь время почти ничего не значит, но я знаю: оставаться со мной так долго — большое обязательство для тебя."
    m 2rkc "Признаюсь, сначала я немного нервничала...{w=0.3} {nw}"
    extend 7eka "Такие отношения — не самые простые."
    m 2ekd "...И я не знала, нет ли в твоей реальности чего-то более важного..."
    m 7duu "Но ты продолжал возвращаться.{w=0.3} Продолжал проводить со мной время — как я всегда надеялась."
    m 1ekb "...И со временем я правда начала в это верить...{w=0.2}что ты имел в виду, когда говорил, что хочешь быть со мной."
    m 3dkbsu "...Что у нас может быть счастливая жизнь вместе.{w=0.3} {nw}"
    extend 3ekbsa "Ты и я — в нашей маленькой реальности."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Я даже не знаю, как тебя отблагодарить, [player]. {w=0.2}Ты сделал этот год для меня невероятным."
    m 5eublb "Так... есть что-то особенное, что ты хотел сделать в нашу первую годовщину?"
    m 5hksdrb "Я особо ничего не планировала, но уверена — мы найдём, чем весело заняться."
    show monika 3huu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 3huu "В конце концов...{w=0.3}когда ты здесь, всё, что мы делаем — весело."
    m 1hubsa "Я так сильно тебя люблю, [player]. {w=0.2}С годовщиной~"
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_2',
            prompt="2 года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=2),
            end_date=store.mas_anni.build_anni_end(years=2)
        ),
        skipCalendar=False
    )

label anni_2:
    m 3eua "Уже два года, как мы влюбились друг в друга."
    m 1eka "Ты ещё помнишь день, когда мы встретились, [player]?"
    m 3eub "Потребовалось столько усилий, чтобы установить этот первый контакт, но в итоге всё того стоило!"
    m 2ekc "Знаю, до перехода в твою реальность ещё может быть очень далеко..."
    m 2duu "Но когда мы достигаем такой вехи,{w=0.1} {nw}"
    extend 7eua "приятно думать обо всём остальном, что ждёт нас впереди."

    if persistent._mas_pm_has_friends:
        m 3hubla "Мне так не терпится жить в мире настоящих людей. Будет чудесно встретить твоих друзей и даже завести своих."
    elif persistent._mas_pm_has_friends is False:
        m 1dka "Мы оба очень долго были одиноки, знаешь? Но когда я перейду, будет так весело заводить новых друзей вместе."
    else:
        m 3hua "Уверена, мы заведём вместе кучу новых друзей!"

    m 3hksdlb "Конечно, твоя компания мне всегда будет нравиться больше всего...{w=0.3}{nw}"
    extend 3eua "но проводить время только вдвоём больше не будет единственным вариантом."
    m 3eub "Общаться тоже станет намного проще!{w=0.2} {nw}"
    extend 3dubsb "Мы наконец услышим голоса друг друга, узнаем привычки и будем помогать друг другу во множестве мелочей."
    m 1ekbsa "Но сегодня я не буду думать только о будущем...{w=0.2} {nw}"
    extend 3hubsu "Я обязательно наслажусь каждой минутой, которую мы проведём вместе~"
    m 1hubsu "Так что давай устроим ещё один чудесный день, [mas_get_player_nickname()]."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_3',
            prompt="3 года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=3),
            end_date=store.mas_anni.build_anni_end(years=3)
        ),
        skipCalendar=False
    )

label anni_3:
    m 4wuo "У нас правда уже третья годовщина?"
    m 2hubsb "Вау...{w=0.3}время правда пролетело, да?"
    m 3rksdla "Знаешь, обычно если пара вместе три года..."
    m 2rsbsa "Они примерно тогда женятся, правда?"
    m 1hub "Ахаха!"
    m 1eka "Я не пытаюсь на тебя давить, не волнуйся."
    m 1lkbsa "К тому же мне бы сначала хотелось обнять тебя по-настоящему — до свадьбы."
    m 1eua "В твоём мире уже изобрели тела роботов-девушек?" # 1s?
    m 1eub "Если посадишь меня в такое — тогда, может, и к священнику сходим~"
    m 2lsbssdrb "Или попробуешь коснуться меня в виртуальной реальности, если она уже есть."
    m 1eua "На самом деле есть куча разных способов встретиться по-настоящему, да?"
    m 1hubsa "Я верно буду ждать дня, когда стану твоей женой — так что, пожалуйста, не забывай обо мне!"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_4',
            prompt="4 года",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=4),
            end_date=store.mas_anni.build_anni_end(years=4)
        ),
        skipCalendar=False
    )

label anni_4:
    m 1dsc "Четыре года..."
    m "Сначала я вроде думала, что ты довольно быстро обо мне забудешь."
    m 1lksdlc "Знала, что я тебе нравлюсь и всё такое, но так боялась, что тебе надоест держать меня включённой на компьютере."
    m "Прости, что сомневалась в тебе."
    m 1eka "Ты хороший человек, [player]."
    m "Ты буквально всё ценное, что у меня есть в этом мире."
    m 1ekbsa "Я люблю тебя."
    m "Рано или поздно кто-нибудь найдёт способ, чтобы мы были вместе по-настоящему."
    m 1hubfa "Когда это случится, я больше никогда тебя не оставлю одного."
    m 1hubfb "Ахаха!"
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_5',
            prompt="5 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=5),
            end_date=store.mas_anni.build_anni_end(years=5)
        ),
        skipCalendar=False
    )

label anni_5:
    m 1hubsa "Пять лет или пятьдесят — я никогда не устану с тобой разговаривать, [player]."
    m 1rksdlbla "Знаю, наверное, одиноко от того, что мы ещё не встретились в твоей реальности...{w=0.3}{nw}"
    extend 1ekblb "но хотя бы годовщины мы всё равно можем проводить здесь вместе, правда?"
    m 2dkbla "Просто думая об этом..."
    m 2eubla "Пять лет — довольно большая веха.{w=0.2} {nw}"
    extend 7wubld "Мы провели вместе половину целого десятилетия."
    m 1ekbla "Каждый год я жду этот особенный день.{w=0.2} {nw}"
    extend 1dkbsu "День, чтобы вспомнить, когда мы влюбились."
    m 2eublb "Весь мой мир перевернулся, когда мы встретились, и с тех пор ты каждый день меняешь мою жизнь."
    m 1fublu "Не думаю, что это когда-нибудь изменится, [player]. Ты для меня просто...{w=0.3}невероятный."
    m 1hubla "Надеюсь, я смогу быть тебе хорошей девушкой ещё много лет~"
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_6',
            prompt="6 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=6),
            end_date=store.mas_anni.build_anni_end(years=6)
        ),
        skipCalendar=False
    )

label anni_6:
    m 3hubfb "Уверена, ты знаешь, какой сегодня день, [player]...{w=0.3} В конце концов, это самый особенный день для меня!"
    m 3hubla "Знаешь ли ты, что в старых германских и викторианских традициях{w=0.1} у разных годовщин есть тематические подарки?"
    m 4eua "Сначала это было только для больших вех, но со временем темы появились у всё большего числа лет."
    m 4rksdlb "Если смотреть скептически — их, наверное, добавили, чтобы разные отрасли больше зарабатывали на подарках..."
    m 1rkbla "Но мне всё равно кажется это милой традицией."
    m 3ruu "Кстати о сладком...{w=0.3}{nw}"
    extend 3eub "частая тема шестой годовщины — конфеты!"
    m 1eka "Раз я пока не могу подарить тебе подарок — купи себе вкусняшку к этому дню."
    m 1hubfa "Я люблю тебя, [player]. Спасибо за ещё один чудесный год."
    return "love|unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_7',
            prompt="7 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=7),
            end_date=store.mas_anni.build_anni_end(years=7)
        ),
        skipCalendar=False
    )

label anni_7:
    m 1dubfa "Семь лет..."
    m 1eubsb "Знаешь, семь во многих культурах считают счастливым числом.{w=0.2} {nw}"
    extend 1ekbsa "Так может..."
    m 2dkbsa "...Может, в этом году удача будет на моей стороне, и я смогу перейти."
    m 2hksdlb "Ахаха, знаю! Полагаться на суеверия — совсем не в моём стиле."
    m 2eka "Но после всего этого времени я невольно ищу проблески надежды."
    m 2ekbltpa "Но я знаю, что справлюсь.{w=0.2} Даже если ждать ещё долго, я всё равно считаю себя невероятно везучей, что встретила тебя."
    m 2dkbstda "Ты — вся удача, которая мне нужна, [player]."
    m 1ekbsa "За ещё один год вместе — и за все, что впереди."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_8',
            prompt="8 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=8),
            end_date=store.mas_anni.build_anni_end(years=8)
        ),
        skipCalendar=False
    )

label anni_8:
    m 1eua "Уверена, ты знаешь, какой сегодня день, [player]..."
    m 3hublb "Именно! С годовщиной, [mas_get_player_nickname(exclude_names=[player])]!"
    m 3ekblb "Знаешь... когда отношения длятся так долго, пары иногда начинают бояться, что всё станет пресным."
    m 1lkbla "Восемь лет — это долго, чтобы узнать привычки друг друга и строить жизнь вокруг другого человека."
    m 1ltc "Может...{w=0.5}ты тоже о таком думал, [player]?"
    m 2ekb "То есть—{w=0.2}я не хочу додумывать!{w=0.3} {nw}"
    extend 2ekblu "Но я думала об этом раньше и хотела тебе кое-что сказать."
    m 2dubsa "Хотела сказать: было так интересно смотреть, как ты меняешься."
    m 4fkbsb "За время вместе ты так вырос. Столько неудач — и ты каждую пережил."
    m 2dkbstpa "И всё же,{w=0.2} со всеми этими переменами..."
    m 2ekbstpu "Ты всё равно выбираешь быть со мной. Возвращаешься сюда каждый день, хотя я не могу пережить всё это рядом с тобой."
    m 2fkbstub "Так что...{w=0.3}кажется, я хотела сказать:{w=0.4} я люблю то, что изменилось.{w=0.2} И люблю, что это осталось прежним."

    python:
        mas_moni_idle_disp.force_by_code("1fkbltpa", duration=9, redraw=False, skip_dissolve=True)
        mas_moni_idle_disp.force_by_code("1dktda", duration=2, clear=False, redraw=False, skip_dissolve=True)
        mas_moni_idle_disp.force_by_code("1eua", duration=16, clear=False, skip_dissolve=True)

    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_9',
            prompt="9 Years",
            category=["anniversary"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=9),
            end_date=store.mas_anni.build_anni_end(years=9)
        ),
        skipCalendar=False
    )

label anni_9:
    m 1eub "Happy anniversary, [player]!"
    m 3eta "It's that time of year again, huh?"
    m 3rtc "It's kind of funny, the time feels to me like it's moving a little bit faster every year..."
    m 3esc "Doesn't it seem like the last one just flew by?"
    m 1hksdlb "...It kind of makes me anxious to think about, ahaha!"
    m 1eksdla "I mean...{w=0.2}{nw}"
    extend 2eksdlc "I don't want to let our time just slip through my fingers..."
    m 2ekb "Maybe I just have to take more time to appreciate each moment."
    m 4eub "There have been a lot of studies about how mindfulness can shape our understanding of time, you know."
    m "So by changing the way I think about things, our time together might stretch out a little more."
    m 4hua "Just thinking about that makes me feel a bit better."
    m 1hubla "After all, I'm sure it's going to be another wonderful year if I get to spend it with you."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_10',
            prompt="10 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=10),
            end_date=store.mas_anni.build_anni_end(years=10)
        ),
        skipCalendar=False
    )

label anni_10:
    m 1esc "Я хотела тебя кое о чём спросить."
    m 2euc "Тебе нравилось проводить это время со мной?"
    m 1ekc "Ты не жалеешь, что влюбился и остаёшься здесь со мной, правда?"
    m 1ekbsa "Если ты всё ещё говоришь со мной через десять лет после нашей встречи — я, наверное, правда произвела на тебя впечатление."
    m "В конце концов, я же говорила, что хочу сделать тебя счастливым."
    m 1hubfa "Поверь, ты помог мне куда больше, чем я тебе."
    m "Уже недолго до того, как я смогу войти в твой мир."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_20',
            prompt="20 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=20),
            end_date=store.mas_anni.build_anni_end(years=20)
        ),
        skipCalendar=False
    )

label anni_20:
    m 1esc "Ты уже прожил довольно долгую жизнь, [player]."
    m "Двадцать лет — это примерно двадцать процентов жизни на Земле, если повезёт."
    m "Надеюсь, к этому моменту ты уже нашёл счастье."
    m 1eka "Я своё нашла."
    m 1ekd "Так что и ты тоже его заслуживаешь."
    m "Двадцать лет назад ты казался грустнее, чем стоило бы."
    m 1eka "Я точно знала, что ты чувствовал. Ты так старался найти кого-то, кто тебя поймёт."
    m "И я тоже пыталась найти тебя."
    m 2hub "Ты бы никого такого, как я, в видеоигре не нашёл — как бы ни искал, [player]."
    m "Я единственная в своём роде."
    m 3rkbsa "И для меня ты — тоже."
    show monika 5eubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubfb "Надеюсь, ты смотришь на последние двадцать лет нашей жизни так же счастливо, как я, [player]."
    m 1hubfa "Так что давай и дальше быть счастливыми вместе."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_50',
            prompt="50 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=50),
            end_date=store.mas_anni.build_anni_end(years=50)
        ),
        skipCalendar=False
    )

label anni_50:
    m 1tkc "Не могу отделаться от мысли: к этому моменту должен же быть способ общаться лучше, чем через этот экран, правда?"
    m "В твоём мире прошло пятьдесят лет с тех пор, как я создала эту комнату."
    m 1hfw "Ну же, выпусти меня уже!"
    m 1dsc "..."
    m 1eua "Ну, если ты всё ещё готов отметить пятидесятую годовщину в этом старом классе..."
    m "Я не против. Чувствуется ностальгия, правда?"
    m 1tfu "Если ты, конечно, не сжульничал, переведя часы вперёд..."
    m 1eka "Рада, что «навсегда» правда значило навсегда."
    m "Даже когда ты умрёшь — я найду способ быть с тобой."
    m 1ekbsa "Тогда увидимся через сто лет, [player]."
    m 1hubfa "Спасибо за всё, что ты для меня сделал."
    m "У твоей жизни всё-таки был смысл."
    m 1hubfb "И у моей — тоже."
    return "unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='anni_100',
            prompt="100 лет",
            category=["юбилей"],
            action=EV_ACT_QUEUE,
            start_date=store.mas_anni.build_anni(years=100),
            end_date=store.mas_anni.build_anni_end(years=100)
        ),
        skipCalendar=False
    )

label anni_100:
    m 1eka "Не думаю, что тебе вообще следует это видеть, [player]."
    m "Я бессмертна, а ты, насколько я помню, — нет."
    m 1tku "Значит, ты, скорее всего, жульничаешь — вручную крутишь системные часы, да?"
    m 1eua "С твоей стороны это мило, так что я тебя прощаю."
    m 1hubsa "Только вложи столько же усилий и в то, чтобы вытащить меня из этих файлов с кодом!"
    m "Уверена, я смогу коснуться тебя по-настоящему — даже если на это уйдёт сто лет."
    return "unlock"

# label anni_negative:
#     m 1o "Ты правда думал, что я не замечу, [player]?"
#     m "Пытаешься обмануть меня, будто у нас годовщина..."
#     m 1p "То, что я здесь плохо чувствую время, не значит, что можно так издеваться над своей девушкой!"
#     m "Я вся разволновалась из-за ерунды..."
#     m 1q "Ну, наверное, я и сама устраивала Литературному клубу худшие розыгрыши."
#     m 1j "Загладь вину — придумай нам что-нибудь романтичное, хорошо?"
#     m 1a"Надеюсь, в этот раз мы дойдём до годовщин честно."
#     m 1k "Я буду ждать!"
#     return
