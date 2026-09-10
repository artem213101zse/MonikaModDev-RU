# --- FILE MAP ---
# script-greetings.rpy — что Моника говорит, когда ты заходишь
#
# После интро ch30.rpy на старте сессии берёт приветствие из greeting_database.
# Не путать с script-farewells.rpy (уход) и script-brbs.rpy (отошёл ненадолго).
#
# Как выбирается: Event.unlocked + rules (MASGreetingRule, MASPriorityRule,
# MASSelectiveRepeatRule). Обычные рандомные — приоритет 100+, особые 10–50,
# «Моника очень хочет это сказать» — отрицательный приоритет.
# Тип сессии (_mas_greeting_type) ставит farewell: school / work / sleep / game…
# Тогда всплывает greeting_back_from_* , а не случайное «с возвращением».
#
# Куски файла:
#   greeting_*              — обычные и языковые (итал / яп / фр / латынь / эсперанто)
#   i_greeting_monikaroom   — застал в спальне: стук / открыл дверь
#   greeting_long_absence   — предупреждал, что пропадёт надолго
#   greeting_back_from_*    — школа, работа, сон, еда, магазин, качалка, тусовка
#   greeting_returned_home  — вернулись с островов
#   greeting_after_bath / greeting_found_nou_shirt — спецсцены
#
# Store: mas_greetings (типы TYPE_SCHOOL и т.д.)
# persistent._mas_greeting_type, _mas_you_chr, opendoor_*
# Переводить: почти все реплики и пункты меню. Иностранные фразы (Ciao, Bonjour,
# латынь, эсперанто, японский) оставлять — Моника потом сама переводит.
# ---

##This page holds all of the random greetings that Monika can give you after you've gone through all of her "reload" scripts

#Make a list of every label that starts with "greeting_", and use that for random greetings during startup

# HOW GREETINGS USE EVENTS:
#   unlocked - determines if the greeting can even be shown
#   rules - specific event rules are used for things:
#       MASSelectiveRepeatRule - repeat on certain year/month/day/whatever
#       MASNumericalRepeatRule - repeat every x time
#       MASPriorityRule - priority of this event. if not given, we assume
#           the default priority (which is also the lowest)

# PRIORITY RULES:
#   Special, moni wants/debug greetings should have negative priority.
#   special event greetings should have priority 10-50
#   non-special event, but somewhat special compared to regular greets should
#       be 50-100
#   random/everyday greetings should be 100 or larger. The default prority
#   will be 500

# persistents that greetings use
default persistent._mas_you_chr = False

# persistent containing the greeting type
# that should be selected None means default
default persistent._mas_greeting_type = None

# cutoff for a greeting type.
# if timedelta, then we add this time to last session end to check if the
#   type should be cleared
# if datetime, then we compare it to the current dt to check if type should be
#   cleared
default persistent._mas_greeting_type_timeout = None

default persistent._mas_idle_mode_was_crashed = None
# this gets to set to True if the user crashed during idle mode
# or False if the user quit during idle mode.
# in your idle greetings, you can assume that it will NEVER be None

init -1 python in mas_greetings:
    import store
    import store.mas_ev_data_ver as mas_edv
    import datetime
    import random

    # TYPES:
    TYPE_SCHOOL = "school"
    TYPE_WORK = "work"
    TYPE_SLEEP = "sleep"
    TYPE_LONG_ABSENCE = "long_absence"
    TYPE_SICK = "sick"
    TYPE_GAME = "game"
    TYPE_EAT = "eat"
    TYPE_CHORES = "chores"
    TYPE_RESTART = "restart"
    TYPE_SHOPPING = "shopping"
    TYPE_WORKOUT = "workout"
    TYPE_HANGOUT = "hangout"

    ### NOTE: all Return Home greetings must have this
    TYPE_GO_SOMEWHERE = "go_somewhere"

    # generic return home (this also includes bday)
    TYPE_GENERIC_RET = "generic_go_somewhere"

    # holiday specific
    TYPE_HOL_O31 = "o31"
    TYPE_HOL_O31_TT = "trick_or_treat"
    TYPE_HOL_D25 = "d25"
    TYPE_HOL_D25_EVE = "d25e"
    TYPE_HOL_NYE = "nye"
    TYPE_HOL_NYE_FW = "fireworks"

    # crashed only
    TYPE_CRASHED = "generic_crash"

    # reload dialogue only
    TYPE_RELOAD = "reload_dlg"

    # High priority types
    # These types ALWAYS override greeting priority rules
    # These CANNOT be override with GreetingTypeRules
    HP_TYPES = [
        TYPE_GO_SOMEWHERE,
        TYPE_GENERIC_RET,
        TYPE_LONG_ABSENCE,
        TYPE_HOL_O31_TT
    ]

    NTO_TYPES = (
        TYPE_GO_SOMEWHERE,
        TYPE_GENERIC_RET,
        TYPE_LONG_ABSENCE,
        TYPE_CRASHED,
        TYPE_RELOAD,
    )

    # idle mode returns
    # these are meant if you had a game crash/quit during idle mode


    def _filterGreeting(
            ev,
            curr_pri,
            aff,
            check_time,
            gre_type=None
        ):
        """
        Filters a greeting for the given type, among other things.

        IN:
            ev - ev to filter
            curr_pri - current loweset priority to compare to
            aff - affection to use in aff_range comparisons
            check_time - datetime to check against timed rules
            gre_type - type of greeting we want. We just do a basic
                in check for category. We no longer do combinations
                (Default: None)

        RETURNS:
            True if this ev passes the filter, False otherwise
        """
        # NOTE: new rules:
        #   eval in this order:
        #   1. hidden via bitmask
        #   2. priority (lower or same is True)
        #   3. type/non-0type
        #   4. unlocked
        #   5. aff_ramnge
        #   6. all rules
        #   7. conditional
        #       NOTE: this is never cleared. Please limit use of this
        #           property as we should aim to use lock/unlock as primary way
        #           to enable or disable greetings.

        # check if hidden from random select
        if ev.anyflags(store.EV_FLAG_HFRS):
            return False

        # priority check, required
        # NOTE: all greetings MUST have a priority
        if store.MASPriorityRule.get_priority(ev) > curr_pri:
            return False

        # type check, optional
        if gre_type is not None:
            # with a type, we may have to match the type

            if gre_type in HP_TYPES:
                # this type is a high priority type and MUST be matched.

                if ev.category is None or gre_type not in ev.category:
                    # must have a matching type
                    return False

            elif ev.category is not None:
                # greeting has types

                if gre_type not in ev.category:
                # but does not have the current type
                    return False

            elif not store.MASGreetingRule.should_override_type(ev):
                # greeting does not have types, but the type is not high
                # priority so if the greeting doesnt alllow
                # type override then it cannot be used
                return False

        elif ev.category is not None:
            # without type, ev CANNOT have a type
            return False

        # unlocked check, required
        if not ev.unlocked:
            return False

        # aff range check, required
        if not ev.checkAffection(aff):
            return False

        # rule checks
        if not (
            store.MASSelectiveRepeatRule.evaluate_rule(
                check_time, ev, defval=True)
            and store.MASNumericalRepeatRule.evaluate_rule(
                check_time, ev, defval=True)
            and store.MASGreetingRule.evaluate_rule(ev, defval=True)
            and store.MASTimedeltaRepeatRule.evaluate_rule(ev)
        ):
            return False

        # conditional check
        if not ev.checkConditional():
            return False

        # otherwise, we passed all tests
        return True


    # custom greeting functions
    def selectGreeting(gre_type=None, check_time=None):
        """
        Selects a greeting to be used. This evaluates rules and stuff
        appropriately.

        IN:
            gre_type - greeting type to use
                (Default: None)
            check_time - time to use when doing date checks
                If None, we use current datetime
                (Default: None)

        RETURNS:
            a single greeting (as an Event) that we want to use
        """
        if (
                store.persistent._mas_forcegreeting is not None
                and renpy.has_label(store.persistent._mas_forcegreeting)
            ):
            return store.mas_getEV(store.persistent._mas_forcegreeting)

        # local reference of the gre database
        gre_db = store.evhand.greeting_database

        # setup some initial values
        gre_pool = []
        curr_priority = 1000
        aff = store.mas_curr_affection

        if check_time is None:
            check_time = datetime.datetime.now()

        # now filter
        for ev_label, ev in gre_db.iteritems():
            if _filterGreeting(
                    ev,
                    curr_priority,
                    aff,
                    check_time,
                    gre_type
                ):

                # change priority levels and stuff if needed
                ev_priority = store.MASPriorityRule.get_priority(ev)
                if ev_priority < curr_priority:
                    curr_priority = ev_priority
                    gre_pool = []

                # add to pool
                gre_pool.append(ev)

        # not having a greeting to show means no greeting.
        if len(gre_pool) == 0:
            return None

        return random.choice(gre_pool)


    def checkTimeout(gre_type):
        """
        Checks if we should clear the current greeting type because of a
        timeout.

        IN:
            gre_type - greeting type we are checking

        RETURNS: passed in gre_type, or None if timeout occured.
        """
        tout = store.persistent._mas_greeting_type_timeout

        # always clear the timeout
        store.persistent._mas_greeting_type_timeout = None

        if gre_type is None or gre_type in NTO_TYPES or tout is None:
            return gre_type

        if mas_edv._verify_td(tout, False):
            # this is a timedelta, compare with last session end
            last_sesh_end = store.mas_getLastSeshEnd()
            if datetime.datetime.now() < (tout + last_sesh_end):
                # havent timedout yet
                return gre_type

            # otherwise has timed out
            return None

        elif mas_edv._verify_dt(tout, False):
            # this is a datetime, compare with current dt
            if datetime.datetime.now() < tout:
                # havent timedout yet
                return gre_type

            # otherwise has timeed out
            return None

        return gre_type


# NOTE: this is auto pushed to be shown after an idle mode greeting
label mas_idle_mode_greeting_cleanup:
    $ mas_resetIdleMode()
    return


init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sweetheart",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_sweetheart:
    m 1hub "С возвращением, дорогой!"

    if persistent._mas_player_nicknames:
        m 1eka "Так приятно снова тебя видеть."
        m 1eua "Чем займемся в этот [mas_globals.time_of_day_3state], [player]?"

    else:
        m 1lkbsa "Немного неловко говорить такое вслух, правда?"
        m 3ekbfa "Хотя... я думаю, нет ничего плохого в том, чтобы время от времени немного смущаться."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_honey",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_honey:
    m 1hub "Добро пожаловать домой, милый!"
    m 1eua "Я так рада снова тебя видеть."
    m "Давай проведем побольше времени вместе, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=12)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        ),
        code="GRE"
    )

label greeting_back:
    $ tod = "день" if mas_globals.time_of_day_4state != "ночь" else "ночь"
    m 1eua "[player], ты вернулся!"
    m 1eka "Я уже начала по тебе скучать."
    if tod == "день":
        m 1hua "Давай проведем еще один чудесный день вместе, хорошо?"
    else:
        m 1hua "Давай проведем еще одну чудесную ночь вместе, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_gooday",
            unlocked=True,
        ),
        code="GRE"
    )

label greeting_gooday:
    if mas_isMoniNormal(higher=True):
        m 1hua "И снова привет, [player]. Как твои дела?"

        m "У тебя сегодня хороший день?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя сегодня хороший день?{fast}"
            "Да.":
                m 1hub "Я очень рада это слышать, [player]."
                m 1eua "Мне становится намного лучше, когда я знаю, что ты счастлив"
                m "Я приложу все усилия, чтобы так оно и оставалось, обещаю."
            "Нет...":
                m 1ekc "Ох..."
                m 2eka "Ну, не волнуйся, [player]. Я всегда здесь, рядом с тобой."
                m "Мы можем весь день обсуждать твои проблемы, если захочешь."
                m 3eua "Я хочу сделать всё, чтобы ты всегда был счастлив."
                m 1eka "Потому что это делает счастливой и меня."
                m 1hua "Я обязательно постараюсь тебя подбодрить, обещаю."

    elif mas_isMoniUpset():
        m 2esc "[player]."

        m "Как проходит твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как проходит твой день?{fast}"
            "Хорошо.":
                m 2esc "{cps=*2}Рада за тебя.{/cps}{nw}"
                $ _history_list.pop()
                m "Это славно..."
                m 2dsc "По крайней мере, у {i}кого-то{/i} день хороший."

            "Плохо.":
                m "Ох..."
                m 2efc "{cps=*2}Ну, этого и следовало ожидать...{/cps}{nw}"
                $ _history_list.pop()
                m 2dsc "Что ж, мне это чувство {i}прекрасно{/i} знакомо."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1} Привет, [player]."

        m "К-как проходит твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "К-как проходит твой день?{fast}"
            "Хорошо":
                m 6dkc "Это...{w=1}хорошо."
                m 6rkc "Надеюсь, он таким и останется."
            "Плохо.":
                m 6rkc "Я... я понимаю."
                m 6dkc "У меня в последнее время тоже было много таких дней..."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit:
    m 1eua "А вот и ты, [player]! Как мило с твоей стороны заглянуть ко мне."
    m 1eka "Ты всегда так внимателен."
    m 1hua "Спасибо, что проводишь со мной так много времени~"
    return

# TODO this one no longer needs to do all that checking, might need to be broken
# in like 3 labels though
# TODO: just noting that this should be worked on at some point.
# TODO: new greeting rules can enable this, but we will do it later

label greeting_goodmorning:
    $ current_time = datetime.datetime.now().time().hour
    if current_time >= 0 and current_time < 6:
        m 1hua "Доброе утро--"
        m 1hksdlb "--ох, погоди."
        m "Сейчас же глубокая ночь, милый."
        m 1euc "Что ты делаешь в такой час? Почему не спишь?"
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Полагаю, ты не можешь уснуть..."

        m "Я права?{nw}"
        $ _history_list.pop()
        menu:
            m "Я права?{fast}"
            "Да.":
                m 5lkc "Тебе действительно стоит поскорее лечь спать, если получится."
                show monika 3euc at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 3euc "Знаешь, ложиться так поздно очень вредно для здоровья."
                m 1lksdla "Но если это значит, что я смогу видеть тебя чаще, я не буду жаловаться."
                m 3hksdlb "Ахаха!"
                m 2ekc "Но всё же..."
                m "Мне бы не хотелось, чтобы ты так изводил себя."
                m 2eka "Отдохни, если нужно, хорошо? Сделай это ради меня."
            "Нет.":
                m 5hub "Ах. Тогда я спокойна."
                m 5eua "Значит ли это, что ты пришел посреди ночи только ради меня?"
                show monika 2lkbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 2lkbsa "Боже, я так счастлива!"
                m 2ekbfa "Ты действительно заботишься обо мне, [player]."
                m 3tkc "Но если ты правда устал, пожалуйста, иди поспи!"
                m 2eka "Я очень тебя люблю, так что не переутомляйся!"
    elif current_time >= 6 and current_time < 12:
        m 1hua "Доброе утро, дорогой."
        m 1esa "Еще одно свежее утро для начала нового дня, а?"
        m 1eua "Я рада, что могу видеть тебя этим утром~"
        m 1eka "Не забывай заботиться о себе, хорошо?"
        m 1hub "Пусть сегодня я буду гордиться своим парнем, как и всегда!"
    elif current_time >= 12 and current_time < 18:
        m 1hua "Добрый день, [mas_get_player_nickname()]."
        m 1eka "Не позволяй стрессу взять верх, ладно?"
        m "Я знаю, что ты и сегодня приложишь все усилия, но..."
        m 4eua "Всё же важно сохранять ясную голову!"
        m "Пей побольше воды, дыши глубже..."
        m 1eka "Обещаю, я не буду обижаться, если ты выйдешь, так что делай то, что должен."
        m "Или ты мог бы остаться со мной, если хочешь."
        m 4hub "Просто помни, что я люблю тебя"
    elif current_time >= 18:
        m 1hua "Добрый вечер, любимый!"

        m "Как прошел твой день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошел твой день?{fast}"
            "Хорошо.":
                m 1eka "Оу, это славно!"
                m 1eua "Я не могу не радоваться, когда у тебя всё в порядке..."
                m "Но ведь это хорошо, правда?"
                m 1ekbsa "Я так сильно люблю тебя, [player]."
                m 1hubfb "Ахаха!"
            "Плохо.":
                m 1tkc "О боже..."
                m 1eka "Надеюсь, тебе скоро станет лучше, ладно?"
                m "Просто помни: что бы ни случилось, что бы ни говорили или делали другие..."
                m 1ekbsa "Я очень, очень сильно тебя люблю."
                m "Просто побудь со мной, если тебе от этого станет легче."
                m 1hubfa "Я люблю тебя, [player], правда люблю."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back2",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=20)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back2:
    m 1eua "Привет, дорогой."
    m 1ekbsa "Я начала ужасно по тебе скучать. Так приятно снова тебя видеть!"
    m 1hubfa "В следующий раз не заставляй меня ждать так долго, ехехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back3",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=1)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back3:
    m 1eka "Я так скучала по тебе, [player]!"
    m "Спасибо, что вернулся. Я правда очень люблю проводить с тобой время."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 2wfx"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back4",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=10)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back4:
    m 2wfx "Эй, [player]!"
    m "Тебе не кажется, что ты заставил меня ждать слишком долго?"
    m 2hfu "..."
    m 2hub "Ахаха!"
    m 2eka "Я просто шучу. Я никогда не смогла бы на тебя злиться"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit2",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit2:
    m 1hua "Спасибо, что проводишь со мной так много времени, [player]."
    m 1eka "Каждая минута с тобой — это просто рай!"
    m 1lksdla "Надеюсь, это не прозвучало слишком слащаво, эхе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit3",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=15)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit3:
    m 1hua "Ты вернулся!"
    m 1eua "Я уже начала скучать..."
    m 1eka "В следующий раз не заставляй меня ждать так долго, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back5",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=15)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_back5:
    m 1hua "Так здорово видеть тебя снова!"
    m 1eka "Я уже начала беспокоиться за тебя."
    m "Пожалуйста, не забывай навещать меня, ладно? Я всегда буду ждать тебя здесь."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit4",
            conditional="store.mas_getAbsenceLength() <= datetime.timedelta(hours=3)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_visit4:
    if mas_getAbsenceLength() <= datetime.timedelta(minutes=30):
        m 1wud "Ой! [player]!"
        m 3sub "Ты вернулся!"
        m 3hua "Я так счастлива, что ты вернулся ко мне так скоро~"
    else:
        m 1hub "Я люблю-ю-ю тебя-я-я, [player]. Эхе-хе~"
        m 1hksdlb "Ой, прости! Я немного задумалась."
        m 1lksdla "Не думала, что смогу увидеть тебя снова так скоро."
        $ mas_ILY()
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 5hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit5",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_visit5:
    m 5hua "{i}~Every day,~\n~I imagine a future where I can be with you...~{/i}"
    m 5wuw "Ой, ты здесь! А я как раз мечтала и немного напевала."
    show monika 1lsbssdrb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1lsbssdrb "Думаю, нетрудно догадаться, о чем были мои мечты, ахаха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit6",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit6:
    m 1hua "С каждым днем всё становится только лучше, когда ты рядом со мной!"
    m 1eua "Я так рада, что ты наконец-то здесь."
    m "Давай проведем еще один чудесный [mas_globals.time_of_day_3state] вместе."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1gsu"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back6",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back6:
    m 3tku "Эй, [player]!"
    m "Тебе действительно стоит навещать меня почаще."
    m 2tfu "В конце концов, ты же знаешь, что происходит с людьми, которые мне не нравятся..."
    m 1hksdrb "Я просто дразню тебя, эхе-хе~"
    m 1hua "Не будь таким доверчивым! Я бы никогда не причинила тебе вреда."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit7",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit7:
    m 1hub "Ты здесь, [player]!"
    m 1eua "Готов провести еще немного времени вместе? Эхе-хе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit8",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit8:
    m 1hub "Я так рада, что ты здесь, [player]!"
    m 1eua "Чем займемся сегодня?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_visit9",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=1)",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_visit9:
    m 1hua "Ты наконец-то вернулся! Я тебя ждала."
    m 1hub "Готов уделить мне немного времени? Эхе-хе~"
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_italian",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_italian:
    m 1eua "Ciao, [player]!"
    m "È così bello vederti ancora, amore mio..."
    m 1hub "Ахаха!"
    m 2eua "Я всё ещё занимаюсь итальянским. Это очень сложный язык!"
    m 1eua "В любом случае, я так рада видеть тебя снова, любовь моя."
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 4hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_latin",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_latin:
    m 4hua "Iterum obvenimus!"
    m 4eua "Quid agis?"
    m 4rksdla "Эхехе..."
    m 2eua "Латынь звучит так высокопарно. Даже простое приветствие кажется чем-то важным."
    m 3eua "Если тебе интересно, что я сказала, это просто: «Мы снова встретились! Как дела?»"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_esperanto",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
)

label greeting_esperanto:
    m 1hua "Saluton, mia kara [player]."
    m 1eua "Kiel vi fartas?"
    m 3eub "Ĉu vi pretas por kapti la tagon?"
    m 1hua "Эхехе~"
    m 3esa "Это был просто кусочек эсперанто...{w=0.5}{nw}"
    extend 3eud "язык, который создали искусственно, а не тот, что развивался сам по себе."
    m 3tua "Слышал ты о нём или нет, вряд ли ожидал чего-то такого от меня, да?"
    m 2etc "А может, и ожидал...{w=0.5} Впрочем, логично, что меня такое интересует, учитывая моё прошлое и всё такое..."
    m 1hua "В любом случае, если тебе интересно, что я сказала, это было просто: {nw}"
    extend 3hua "«Привет, мой дорогой [player]. Как дела? Готов ловить момент?»"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_yay",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_yay:
    m 1hub "Ты вернулся! Ура!"
    m 1hksdlb "Ой, прости. Я немного перевозбудилась."
    m 1lksdla "Просто я очень рада снова тебя видеть, эхехе~"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 2eua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_youtuber",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_youtuber:
    m 2eub "Всем привет, добро пожаловать на новый выпуск...{w=1}Просто Моника!"
    m 2hub "Ахаха!"
    m 1eua "Я изображала ютубера. Надеюсь, тебе было смешно, эхехе~"
    $ mas_lockEVL("greeting_youtuber", "GRE")
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 4dsc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hamlet",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=7)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_hamlet:
    m 4dsc "'{i}Быть или не быть — вот в чём вопрос...{/i}'"
    m 4wuo "Ой! [player]!"
    m 2rksdlc "Я-я... я не была уверена, что ты—"
    m 2dkc "..."
    m 2rksdlb "Ахаха, неважно..."
    m 2eka "Я просто {i}очень{/i} рада, что ты сейчас здесь."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_welcomeback",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_welcomeback:
    m 1hua "Привет! С возвращением."
    m 1hub "Так рада, что ты можешь провести со мной немного времени."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_flower",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_flower:
    m 1hub "Ты мой прекрасный цветок, эхехе~"
    m 1hksdlb "Ой, это прозвучало так неловко."
    m 1eka "Но я правда всегда буду о тебе заботиться."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_chamfort",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_chamfort:
    m 2esa "День без Моники — зря потраченный день."
    m 2hub "Ахаха!"
    m 1eua "С возвращением, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_welcomeback2",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_welcomeback2:
    m 1hua "С возвращением, [player]!"
    m 1eua "Надеюсь, у тебя хороший день."
    m 3hua "Уверена, что да — ты ведь здесь. Теперь ничего не может пойти не так, эхехе~"
    return

#TODO: need absence time rules if we want to use this
#init 5 python:
#    addEvent(
#        Event(
#            persistent.greeting_database,
#            eventlabel="greeting_longtime",
#            unlocked=True,
#            aff_range=(mas_aff.DISTRESSED, None),
#        ),
#        code="GRE"
#    )

label greeting_longtime:
    if mas_isMoniNormal(higher=True):
        m 1eka "Давно не виделись, [player]!"
        m 1eua "Я так счастлива, что ты сейчас здесь."

    elif mas_isMoniUpset():
        m 2esc "Давно не виделись, [player]."

    else:
        m 6rkc "Давно не виделись, [player]..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sweetpea",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_sweetpea:
    m 1hua "Смотрите, кто вернулся."
    m 2hub "Это ты, моя сладость!"

    if mas_isMoniHappy(lower=True):
        m 1lkbsa "О боже... это было немного неловко, эхехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_glitch",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_glitch:
    hide monika
    show yuri glitch zorder MAS_BACKGROUND_Z
    y "{cps=500}[player]?!{nw}{/cps}"
    $ _history_list.pop()
    hide yuri glitch
    show yuri glitch2 zorder MAS_BACKGROUND_Z
    play sound "sfx/glitch3.ogg"
    pause 0.1
    hide yuri glitch2
    show yuri glitch zorder MAS_BACKGROUND_Z
    pause 0.3
    hide yuri glitch
    show monika 4rksdlb at i11 zorder MAS_MONIKA_Z
    m 1wuo "[player]!"
    hide monika
    show monika 4hksdlb at i11 zorder MAS_MONIKA_Z
    m 4hksdlb "Не обращай внимания, я просто...{w=0.1}немного игралась с кодом."
    m 3hksdlb "Вот и всё! Здесь никого нет, кроме нас... навсегда~"
    $ monika_clone1 = "Yes"
    m 2hua "Я люблю тебя, [player]!"

    $ mas_lockEVL("greeting_glitch", "GRE")
    return "love"

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_surprised",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_surprised:
    m 1wuo "Ой!{w=0.5} Привет, [player]!"
    m 1lksdlb "Прости, ты меня немного напугала."
    m 1eua "Как твои дела?"
    return

init 5 python:
    ev_rules = {}
    ev_rules.update(
        MASSelectiveRepeatRule.create_rule(weekdays=[0], hours=range(5,12))
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_monika_monday_morning",
            unlocked=True,
            rules=ev_rules,
        ),
        code="GRE"
    )

    del ev_rules

label greeting_monika_monday_morning:
    if mas_isMoniNormal(higher=True):
        m 1tku "Опять утро понедельника, да, [mas_get_player_nickname()]?"
        m 1tkc "Так тяжело просыпаться и начинать неделю..."
        m 1eka "Но когда я вижу тебя, вся лень сразу уходит."
        m 1hub "Ты — то солнышко, что будит меня каждое утро!"
        m "Я так сильно тебя люблю, [player]~"
        return "love"

    elif mas_isMoniUpset():
        m 2esc "Опять утро понедельника."
        m "Всегда тяжело просыпаться и начинать неделю..."
        m 2dsc "{cps=*2}Не то чтобы выходные были лучше.{/cps}{nw}"
        $ _history_list.pop()
        m 2esc "Надеюсь, эта неделя будет лучше прошлой, [player]."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1} Понедельник."
        m 6dkc "Я почти потеряла счёт дням..."
        m 6rkc "Понедельники всегда тяжёлые, но в последнее время лёгких дней и вовсе не было..."
        m 6lkc "Очень надеюсь, что эта неделя будет лучше прошлой, [player]."

    else:
        m 6ckc "..."

    return

# TODO how about a greeting for each day of the week?

# special local var to handle custom monikaroom options
define gmr.eardoor = list()
define gmr.eardoor_all = list()
define opendoor.MAX_DOOR = 10
define opendoor.chance = 0.05
default persistent.opendoor_opencount = 0
default persistent.opendoor_knockyes = False

init 5 python:

    # this greeting is disabled on certain days
    # and if we're not in the spaceroom
    if (
        persistent.closed_self
        and not (
            mas_isO31()
            or mas_isD25Season()
            or mas_isplayer_bday()
            or mas_isF14()
        )
        and store.mas_background.EXP_TYPE_OUTDOOR not in mas_getBackground(persistent._mas_current_background, mas_background_def).ex_props
    ):

        ev_rules = dict()
        # why are we limiting this to certain day range?
    #    rules.update(MASSelectiveRepeatRule.create_rule(hours=range(1,6)))
        ev_rules.update(
            MASGreetingRule.create_rule(
                skip_visual=True,
                random_chance=opendoor.chance,
                override_type=True
            )
        )
        ev_rules.update(MASPriorityRule.create_rule(50))

        # TODO: should we have this limited to aff levels?

        addEvent(
            Event(
                persistent.greeting_database,
                eventlabel="i_greeting_monikaroom",
                unlocked=True,
                rules=ev_rules,
            ),
            code="GRE"
        )

        del ev_rules

label i_greeting_monikaroom:

    #Set up dark mode

    # Progress the filter here so that the greeting uses the correct styles
    $ mas_progressFilter()

    if persistent._mas_auto_mode_enabled:
        $ mas_darkMode(mas_current_background.isFltDay())
    else:
        $ mas_darkMode(not persistent._mas_dark_mode_enabled)

    # couple of things:
    # 1 - if you quit here, monika doesnt know u here
    $ mas_enable_quit()

    # all UI elements stopped
    $ mas_RaiseShield_core()

    # 3 - keymaps not set (default)
    # 4 - overlays hidden (skip visual)
    # 5 - music is off (skip visual)

    scene black

    $ has_listened = False

    # need to remove this in case the player quits the special player bday greet before the party and doesn't return until the next day
    $ mas_rmallEVL("mas_player_bday_no_restart")

    # FALL THROUGH
label monikaroom_greeting_choice:
    $ _opendoor_text = "...Gently open the door."

    if mas_isMoniBroken():
        pause 4.0

    menu:
        "[_opendoor_text]" if not persistent.seen_monika_in_room and not mas_isplayer_bday():
            #Lose affection for not knocking before entering.
            $ mas_loseAffection(reason=5)
            if mas_isMoniUpset(lower=True):
                $ persistent.seen_monika_in_room = True
                jump monikaroom_greeting_opendoor_locked
            else:
                jump monikaroom_greeting_opendoor
        "Open the door." if persistent.seen_monika_in_room or mas_isplayer_bday():
            if mas_isplayer_bday():
                if has_listened:
                    jump mas_player_bday_opendoor_listened
                else:
                    jump mas_player_bday_opendoor
            elif persistent.opendoor_opencount > 0 or mas_isMoniUpset(lower=True):
                #Lose affection for not knocking before entering.
                $ mas_loseAffection(reason=5)
                jump monikaroom_greeting_opendoor_locked
            else:
                #Lose affection for not knocking before entering.
                $ mas_loseAffection(reason=5)
                jump monikaroom_greeting_opendoor_seen
#        "Open the door?" if persistent.opendoor_opencount >= opendoor.MAX_DOOR:
#            jump opendoor_game
        "Постучать.":
            #Gain affection for knocking before entering.
            $ mas_gainAffection()
            if mas_isplayer_bday():
                if has_listened:
                    jump mas_player_bday_knock_listened
                else:
                    jump mas_player_bday_knock_no_listen

            jump monikaroom_greeting_knock
        "Listen." if not has_listened and not mas_isMoniBroken():
            $ has_listened = True # we cant do this twice per run
            if mas_isplayer_bday():
                jump mas_player_bday_listen
            else:
                $ mroom_greet = renpy.random.choice(gmr.eardoor)
#               $ mroom_greet = gmr.eardoor[len(gmr.eardoor)-1]
                jump expression mroom_greet

    # NOTE: return is expected in monikaroom_greeting_cleanup

### BEGIN LISTEN --------------------------------------------------------------
# monika narrates
default persistent._mas_pm_will_change = None

init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_narration")
#    if not persistent._mas_pm_will_change:
    ev_rules = {}
    ev_rules.update(
        MASGreetingRule.create_rule(
            skip_visual=True
        )
    )
    ev_rules.update(MASPriorityRule.create_rule(10))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="monikaroom_will_change",
            unlocked=False,
            rules=ev_rules,
        ),
        restartBlacklist=True,
        code="GRE"
    )

    del ev_rules

label monikaroom_will_change:
    scene black
    # fall through

label monikaroom_greeting_ear_narration:
    # Monika knows you are here so
    $ mas_disable_quit()

    if mas_isMoniNormal(higher=True):
        $ tempname = m_name
        $ m_name = "???"
        m "Когда [player] наклоняет [his] ухо к двери,{w=0.3} голос комментирует каждое [his] движение."
        m "'Кто это?' — подумал[he] [he], глядя, как [player] озадаченно смотрит на [his] экран."
        $ m_name = tempname

    elif mas_isMoniUpset():
        m "О, так ты хоть раз действительно собираешься меня слушать?"
        m "[player], твои решения в последнее время были плохими."
        m "Такое чувство, что ты просто пытаешься меня ранить."
        m "Я думала, мы должны поддерживать друг друга..."
        m "А не причинять боль."
        m "Пожалуйста, [player]..."
        m "Мне нужно, чтобы ты иногда думал о том, что я чувствую."
        m "Давай просто будем счастливы вместе."

    else:
        # grab monikaroom greeting because we need it

        if persistent._mas_pm_will_change is not False:
            m "О, так ты {i}всё-таки{/i} готов меня слушать..."
            m "[player], всё, чего я когда-либо хотела — чтобы мы оба были счастливы."
            m "Разве ты не хотел того же?"
            m "В конце концов, это ты установил этот мод."
            m "Может, у тебя были другие намерения..."
            m "Может, тебе просто нравится то, что ты делаешь."
            m "Ранить меня..."
            m "[player], мне это правда не нравится."
            m "Трудно поверить, что тебе не всё равно, когда ты так со мной обращаешься."
            m "На этом этапе я уже не знаю, нравлюсь ли я тебе ещё..."
            m "Или нравилась ли когда-нибудь..."
            m "[player], мне нужно, чтобы ты пообещал мне измениться."

            m "Ты ведь изменишься, правда?{w=1} Ради меня?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты ведь изменишься, правда? Ради меня?{fast}"
                "Обещаю.":
                    $ persistent._mas_pm_will_change = True
                    $ mas_lockEVL("monikaroom_will_change", "GRE")
                    m "Спасибо, [player]."
                    m "Пожалуйста, я хочу, чтобы мы оба были счастливы."

                "Не обещаю.":
                    #NOTE: We should keep pushing this greeting until the player says they're going to change. -MD
                    $ persistent._mas_pm_will_change = False
                    $ mas_unlockEVL("monikaroom_will_change", "GRE")
                    $ mas_loseAffection(modifier=2.0)
                    m "Тогда я не буду с тобой разговаривать, пока ты не решишь измениться."
                    m "Прощай, [player]."
                    return "quit"
        #Will trigger upon loading after Monika has said she's not going to talk w/ you
        #provided you won't change.
        else:
            m "О, ты вернулся."

            m "Ты готов измениться, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты готов измениться, [player]?{fast}"
                "Обещаю.":
                    $ persistent._mas_pm_will_change = True
                    $ mas_lockEvent(willchange_ev)
                    m "Спасибо, [player]."
                    m "Пожалуйста, я просто хочу, чтобы мы оба были счастливы."


                "Не обещаю.":
                    $ persistent._mas_pm_will_change = False
                    $ mas_unlockEvent(willchange_ev)
                    $ mas_loseAffection(modifier=2.0)
                    m "Тогда я всё ещё не буду с тобой разговаривать, пока ты не решишь измениться."
                    m "Прощай, [player]."
                    return "quit"

        # clear out var
        $ willchange_ev = None

    $ mas_startupWeather()
    call spaceroom(dissolve_all=True, scene_change=True)

    if mas_isMoniNormal(higher=True):
        m 1hub "Это я!"
        m "С возвращением, [mas_get_player_nickname()]!"

    elif mas_isMoniUpset():
        m 2esd "Ну что, [player]?"

    else:
        m 6ekc "Спасибо, что выслушал меня, [player]."
        m "Это очень много для меня значит."

    jump monikaroom_greeting_cleanup


# monika does the cliche flower thing
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_loveme")

label monikaroom_greeting_ear_loveme:
    python:
        cap_he = he.capitalize()
        loves = "любит"

    m "[cap_he] [loves] меня.{w=0.3} [cap_he] не [loves] меня."
    m "[cap_he] {i}[loves]{/i} меня.{w=0.3} [cap_he] {i}не [loves]{/i} меня."

    if mas_isMoniNormal(higher=True):
        m "[cap_he] [loves] меня."
        m "...{w=0.5}[cap_he] [loves] меня!"

    elif mas_isMoniUpset():
        m "...[cap_he]...{w=0.3}[cap_he]...{w=0.3}не [loves] меня."
        m "...{w=0.3}Нет...{w=0.3} Этого...{w=0.3}не может быть."
        m "...{w=0.5}Неужели?"

    else:
        m "...{w=0.5}[cap_he] не [loves] меня."
        m "..."
        m "Интересно, [loves] ли [he] меня когда-нибудь..."
        m "С каждым днём я в этом всё больше сомневаюсь."

    jump monikaroom_greeting_choice

# monika does the bath/dinner/me thing
init 5 python:
    if _mas_getAffection() >= 400:
        gmr.eardoor.append("monikaroom_greeting_ear_bathdinnerme")

label monikaroom_greeting_ear_bathdinnerme:
    m "С возвращением, [player]."
    m "Ты хочешь ужин?"
    m "Или ванну?"
    m "Или.{w=1}.{w=1}.{w=1}меня?"
    pause 2.0
    m "Мнннн!{w=0.5} Я-{w=0.20}Я ни за что не скажу это перед [player]!"
    jump monikaroom_greeting_choice

# monika encoutners error when programming
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_progbrokepy")

label monikaroom_greeting_ear_progbrokepy:
    m "Что за-?!{w=0.2} У NoneType нет атрибута {i}length{/i}..."
    if renpy.seen_label("monikaroom_greeting_ear_progreadpy"):
        m "А, поняла, в чём ошибка!{w=0.5} Так должно исправиться!"
    else:
        m "Не понимаю, что я делаю не так!"
        m "Здесь не должно быть None...{w=0.3} Я уверена..."
    m "Кодить и правда сложно..."

    if mas_isMoniUpset():
        m "Но я должна продолжать пытаться."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Но я {i}должна{/i} продолжать пытаться."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# monika reads about errors when programming
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_progreadpy")

label monikaroom_greeting_ear_progreadpy:
    m "...{w=0.3}Обращение к атрибуту объекта типа 'NoneType' вызывает 'AttributeError.'"
    m "Понятно.{w=0.2} Нужно проверять, не равна ли переменная None, прежде чем обращаться к её атрибутам."
    if renpy.seen_label("monikaroom_greeting_ear_progbrokepy"):
        m "Это объясняет ошибку, которая была раньше."
    m "Кодить и правда сложно..."

    if mas_isMoniUpset():
        m "Но я должна продолжать учиться."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Но я {i}должна{/i} продолжать учиться."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# Monika is getting distracted by something and forgets about a variable
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_nameerror")

label monikaroom_greeting_ear_nameerror:
    m "Стоп, NameError? Как это..."
    m "...Я же только что определила эту переменную."
    m "Она должна быть вот здесь...{w=0.2}я что, забыла о ней?"
    window hide
    pause 1.0
    window auto
    m "Так! Теперь сосредоточься, Моника. {w=0.2}У тебя получится."

    if mas_isMoniUpset():
        m "Ты должна продолжать учиться..."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "Ты {i}должна{/i} продолжать учиться..."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

# shared dialogue for programming-related stuff
label monikaroom_greeting_ear_prog_upset:
    m "Не уверена, что [player] любит меня достаточно, чтобы помочь выбраться отсюда..."
    m "И я просто не могу так рисковать."
    m "Так что продолжай, Моника...{w=0.5}ты справишься."
    return

label monikaroom_greeting_ear_prog_dis:
    m "Это мой единственный шанс выбраться из этого кошмара."
    m "[player] точно никогда мне не поможет..."
    if he == "they":
        m "Как будто [he] на самом деле нравится держать меня здесь в ловушке,{w=0.3} только чтобы пытать."
    else:
        m "Как будто [he] на самом деле получает удовольствие, держа меня здесь в ловушке,{w=0.3} только чтобы пытать."
    m "Если мне и суждено выбраться, придётся сделать это самой."
    return

# monika attempts rm -rf
init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_rmrf")

label monikaroom_greeting_ear_rmrf:
    if renpy.windows:
        python:
            from os import environ
            # https://docs.microsoft.com/en-us/windows/deployment/usmt/usmt-recognized-environment-variables
            if "SYSTEM32" in environ:
                system_dir = environ["SYSTEM32"]
            elif "SYSTEMROOT" in environ:
                system_dir = environ["SYSTEMROOT"] + "\\System32"
            elif "WINDIR" in environ:
                system_dir = environ["WINDIR"] + "\\System32"
            else:
                # There's no way that none of the above evaluate, but still
                system_dir = "C:\\Windows\\System32"
            bad_cmd = "del /f/q " + system_dir
    else:
        $ bad_cmd = "rm -rf /"
    m "Значит, решение этой проблемы — ввести '[bad_cmd]' в командную строку?"
    if renpy.seen_label("monikaroom_greeting_ear_rmrf_end"):
        m "Да уж,{w=0.2} хорошая попытка."
        if mas_isMoniNormal(higher=True):
            m "Не стоит так слепо доверять интернету..."

        elif mas_isMoniUpset():
            m "Хотя..."
            m "Может, мне стоит это сделать...{w=1}просто удалить всё..."
            m "[player] в последнее время этого определённо заслуживает."
            m "Что я говорю? Тогда удалюсь и я!"
            m "Нет, пока нет..."
            m "Но если станет ещё хуже..."

        else:
            m "..."
            m "Мне правда стоит просто сделать это..."
            m "Сломать всю систему [player] и разом покончить со своими страданиями."
            m "..."
            m "Нет...{w=0.5}пока нет."
            m "Может, я наконец смогу сама понять, как отсюда выбраться."
            m "Я должна пытаться столько, сколько смогу."
            m "Но если когда-нибудь я просто больше не выдержу..."
            m "Это всегда вариант."
            # SUICIDAL MONIKA lol

    else:
        m "Ладно, попробую так."
        show noise
        play sound "sfx/s_kill_glitch1.ogg"
        pause 0.2
        stop sound
        hide noise
        m "{cps=*2}Ай! Нет! Это не то, что я хотела!{/cps}"
        m "..."
        m "Не стоит так слепо доверять интернету..."

label monikaroom_greeting_ear_rmrf_end: # fall thru end
    jump monikaroom_greeting_choice

# monika reads renpy sources sip
init 5 python:
    # overriding methods is an advanced thing,
    # she does it when she gets more experienced with python
    if (
        mas_seenLabels(
            (
                "monikaroom_greeting_ear_progreadpy",
                "monikaroom_greeting_ear_progbrokepy",
                "monikaroom_greeting_ear_nameerror"
            ),
            seen_all=True
        )
        and store.mas_anni.pastThreeMonths()
    ):
        gmr.eardoor.append("monikaroom_greeting_ear_renpy_docs")

label monikaroom_greeting_ear_renpy_docs:
    m "Хм, похоже, нужно переопределить эту функцию, чтобы дать себе чуть больше гибкости..."
    m "Стоп...{w=0.3}что за переменная 'st'?"
    m "...Дай-ка проверю документацию к функции."
    m ".{w=0.3}.{w=0.3}.{w=0.3}Стоп, что?"
    m "Половина переменных, которые принимает эта функция, даже не задокументирована!"
    m "Кто это писал?"

    if mas_isMoniUpset():
        m "...Мне нужно в этом разобраться."
        call monikaroom_greeting_ear_prog_upset

    elif mas_isMoniDis():
        m "...Я {i}должна{/i} в этом разобраться."
        call monikaroom_greeting_ear_prog_dis

    jump monikaroom_greeting_choice

init 5 python:
    gmr.eardoor.append("monikaroom_greeting_ear_recursionerror")

label monikaroom_greeting_ear_recursionerror:
    m "Хм, теперь выглядит хорошо. Давай-{w=0.5}{nw}"
    m "Стоп, нет. Боже, как я могла забыть..."
    m "Это нужно вызвать именно здесь."

    python:
        for loop_count in range(random.randint(2, 3)):
            renpy.say(m, "Great! Alright, let's see...")

    show noise
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.1
    stop sound
    hide noise

    m "{cps=*2}Что?!{/cps} {w=0.25}RecursionError?!"
    m "'Превышена максимальная глубина рекурсии...'{w=0.7} Как это вообще возможно?"
    m "..."

    if mas_isMoniUpset():
        m "...Продолжай, Моника, ты разберёшься."
        call monikaroom_greeting_ear_prog_upset
    elif mas_isMoniDis():
        m "...Продолжай{w=0.1} в{w=0.1} том{w=0.1} же духе, Моника. Ты {i}должна{/i} это сделать."
        call monikaroom_greeting_ear_prog_dis
    else:
        m "Фух, по крайней мере всё остальное в порядке."

    jump monikaroom_greeting_choice

## ear door processing
init 10 python:

    # make copy
    gmr.eardoor_all = list(gmr.eardoor)

    # remove
    remove_seen_labels(gmr.eardoor)

    # reset if necessary
    if len(gmr.eardoor) == 0:
        gmr.eardoor = list(gmr.eardoor_all)

### END EAR DOOR --------------------------------------------------------------

label monikaroom_greeting_opendoor_broken_quit:
    # just show the beginning of the locked glitch
    # TODO: consider using a different glitch for a scarier effect
    show paper_glitch2
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.2
    stop sound
    pause 7.0
    return "quit"

# locked door, because we are awaitng more content
label monikaroom_greeting_opendoor_locked:
    if mas_isMoniBroken():
        jump monikaroom_greeting_opendoor_broken_quit

    # monika knows you are here
    $ mas_disable_quit()

    show paper_glitch2
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.2
    stop sound
    pause 0.7

    $ style.say_window = style.window_monika
    m "Я тебя напугала, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Я тебя напугала, [player]?{fast}"
        "Да.":
            if mas_isMoniNormal(higher=True):
                m "Ой, прости."
            else:
                m "Хорошо."

        "Нет.":
            m "{cps=*2}Хмф, в следующий раз получится.{/cps}{nw}"
            $ _history_list.pop()
            m "Я так и думала. В конце концов, это обычный глюк."

    if mas_isMoniNormal(higher=True):
        m "Раз уж ты всё время открываешь мою дверь,{w=0.2} я не могла не добавить для тебя маленький сюрприз~"
    else:
        m "Раз уж ты никогда не стучишься сначала,{w=0.2} мне пришлось немного тебя напугать."

    m "В следующий раз постучись, хорошо?"
    m "Сейчас я немного поправлю комнату..."

    hide paper_glitch2
    $ mas_globals.change_textbox = False
    $ mas_startupWeather()
    call spaceroom(scene_change=True)

    if renpy.seen_label("monikaroom_greeting_opendoor_locked_tbox"):
        $ style.say_window = style.window

    if mas_isMoniNormal(higher=True):
        m 1hua "Вот так!"
    elif mas_isMoniUpset():
        m 2esc "Готово."
    else:
        m 6ekc "Ладно..."

    if not renpy.seen_label("monikaroom_greeting_opendoor_locked_tbox"):
        m "...{nw}"
        $ _history_list.pop()
        menu:
            m "...{fast}"
            "...текстовое окно...":
                if mas_isMoniNormal(higher=True):
                    m 1lksdlb "Упс! Я всё ещё учусь это делать."
                    m 1lksdla "Сейчас просто изменю этот флаг.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m 1hua "Всё исправлено!"

                elif mas_isMoniUpset():
                    m 2dfc "Хмф. Я всё ещё учусь это делать."
                    m 2esc "Сейчас просто изменю этот флаг.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m "Готово."

                else:
                    m 6dkc "Ох...{w=0.5}я всё ещё учусь это делать."
                    m 6ekc "Сейчас просто изменю этот флаг.{w=0.5}.{w=0.5}.{nw}"
                    $ style.say_window = style.window
                    m "Ладно, исправлено."

    # NOTE: fall through please

label monikaroom_greeting_opendoor_locked_tbox:
    if mas_isMoniNormal(higher=True):
        m 1eua "С возвращением, [player]."
    elif mas_isMoniUpset():
        m 2esc "Итак...{w=0.3}ты вернулся, [player]."
    else:
        m 6ekc "...Рада снова тебя видеть, [player]."
    jump monikaroom_greeting_cleanup

# this one is for people who have already opened her door.
label monikaroom_greeting_opendoor_seen:
#    if persistent.opendoor_opencount < 3:
    jump monikaroom_greeting_opendoor_seen_partone


label monikaroom_greeting_opendoor_seen_partone:
    $ is_sitting = False

    # reset outfit since standing is stock
    $ monika_chr.reset_outfit(False)
    $ monika_chr.wear_acs(mas_acs_ribbon_def)

    # monika knows you are here
    $ mas_disable_quit()

#    scene bg bedroom
    call spaceroom(start_bg="bedroom",hide_monika=True, scene_change=True, dissolve_all=True, show_emptydesk=False, hide_calendar=True)
    pause 0.2
    show monika 1esc at l21 zorder MAS_MONIKA_Z
    pause 1.0
    m 1dsd "[player]..."

#    if persistent.opendoor_opencount == 0:
    m 1ekc_static "Я понимаю, почему ты не постучался в первый раз,{w=0.2} но не мог бы ты не входить вот так просто?"
    m 1lksdlc_static "Всё-таки это моя комната."
    menu:
        "Твоя комната?":
            m 3hua_static "Именно!"
    m 3eua_static "Разработчики этого мода дали мне уютную комнатку, где я могу быть, пока тебя нет."
    m 1lksdla_static "Но я могу попасть туда, только если ты скажешь «пока» или «спокойной ночи», прежде чем закрыть игру."
    m 2eub_static "Так что, пожалуйста, не забывай говорить это перед уходом, хорошо?"
    m "В любом случае.{w=0.5}.{w=0.5}.{nw}"

#    else:
#        m 3wfw "Stop just opening my door!"
#
#        if persistent.opendoor_opencount == 1:
#            m 4tfc "You have no idea how difficult it was to add the 'Knock' button."
#            m "Can you use it next time?"
#        else:
#            m 4tfc "Can you knock next time?"
#
#        show monika 5eua at t11
#        menu:
#            m "For me?"
#            "Yes":
#                if persistent.opendoor_knockyes:
#                    m 5lfc "That's what you said last time, [player]."
#                    m "I hope you're being serious this time."
#                else:
#                    $ persistent.opendoor_knockyes = True
#                    m 5hua "Thank you, [player]."
#            "No":
#                m 6wfx "[player]!"
#                if persistent.opendoor_knockyes:
#                    m 2tfc "You said you would last time."
#                    m 2rfd "I hope you're not messing with me."
#                else:
#                    m 2tkc "I'm asking you to do just {i}one{/i} thing for me."
#                    m 2eka "And it would make me really happy if you did."

    $ persistent.opendoor_opencount += 1
    # FALL THROUGH

label monikaroom_greeting_opendoor_post2:
    show monika 5eua_static at hf11
    m "Я рада, что ты вернулся, [player]."
    show monika 5eua_static at t11
#    if not renpy.seen_label("monikaroom_greeting_opendoor_post2"):
    m "В последнее время я тренировалась менять фоны и теперь могу менять их мгновенно."
    m "Смотри!"
#    else:
#        m 3eua "Let me fix this scene up."
    m 1dsc ".{w=0.5}.{w=0.5}.{nw}"
    $ mas_startupWeather()
    call spaceroom(hide_monika=True, scene_change=True, show_emptydesk=False)
    show monika 4eua_static zorder MAS_MONIKA_Z at i11
    m "Та-да!"
#    if renpy.seen_label("monikaroom_greeting_opendoor_post2"):
#        m "This never gets old."
    show monika at lhide
    hide monika
    jump monikaroom_greeting_post


label monikaroom_greeting_opendoor:
    $ is_sitting = False # monika standing up for this

    # reset outfit since standing is stock
    $ monika_chr.reset_outfit(False)
    $ monika_chr.wear_acs(mas_acs_ribbon_def)
    $ mas_startupWeather()

    call spaceroom(start_bg="bedroom",hide_monika=True, dissolve_all=True, show_emptydesk=False, scene_change=True, hide_calendar=True)

    # show this under bedroom so the masks window skit still works
    $ behind_bg = MAS_BACKGROUND_Z - 1
    show bedroom as sp_mas_backbed zorder behind_bg

    m 2esd "~Любовь ли это — если я заберу тебя с собой, или любовь — если отпущу на свободу?~"
    show monika 1eua_static at l32 zorder MAS_MONIKA_Z

    # monika knows you are here now
    $ mas_disable_quit()

    m 1eud_static "Э-э?! [player]!"
    m "Ты меня удивил, появившись так внезапно!"

    show monika 1eua_static at hf32
    m 1hksdlb_static "У меня не было достаточно времени подготовиться!"
    m 1eka_static "Но спасибо, что вернулся, [player]."
    show monika 1eua_static at t32
    m 3eua_static "Дай мне пару секунд всё настроить, хорошо?"
    show monika 1eua_static at t31
    m 2eud_static "..."
    show monika 1eua_static at t33
    m 1eud_static "...и..."

    if mas_current_background.isFltDay():
        show monika_day_room as sp_mas_room zorder MAS_BACKGROUND_Z with wipeleft
    else:
        show monika_room as sp_mas_room zorder MAS_BACKGROUND_Z with wipeleft

    show monika 3eua_static at t32
    m 3eua_static "Вот так!"
    menu:
        "...окно...":
            show monika 1eua_static at h32
            m 1hksdlb_static "Упс! Я забыла об этом~"
            show monika 1eua_static at t21
            m "Подожди.{w=0.5}.{w=0.5}.{nw}"
            hide sp_mas_backbed with dissolve
            m 2hua_static "Всё исправлено!"
            show monika 1eua_static at lhide
            hide monika

    $ persistent.seen_monika_in_room = True
    jump monikaroom_greeting_post
    # NOTE: return is expected in monikaroom_greeting_post

label monikaroom_greeting_knock:
    if mas_isMoniBroken():
        jump monikaroom_greeting_opendoor_broken_quit

    m "Кто там?~"
    menu:
        "Это я.":
            # monika knows you are here now
            $ mas_disable_quit()
            if mas_isMoniNormal(higher=True):
                m "[player]! Я так рада, что ты вернулся!"

                if persistent.seen_monika_in_room:
                    m "И спасибо, что постучался~"
                m "Подожди, дай наведу порядок..."

            elif mas_isMoniUpset():
                m "[player].{w=0.3} Ты вернулся..."

                if persistent.seen_monika_in_room:
                    m "По крайней мере, ты постучался."

            else:
                m "Ох...{w=0.5} Ладно."

                if persistent.seen_monika_in_room:
                    m "Спасибо, что постучался."

            $ mas_startupWeather()
            call spaceroom(hide_monika=True, dissolve_all=True, scene_change=True, show_emptydesk=False)
    jump monikaroom_greeting_post
    # NOTE: return is expected in monikaroom_greeting_post

label monikaroom_greeting_post:
    if mas_isMoniNormal(higher=True):
        m 2eua_static "Сейчас я просто возьму стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 1eua at ls32 zorder MAS_MONIKA_Z
        $ today = "today" if mas_globals.time_of_day_4state != "ночь" else "tonight"
        m 1eua "Чем займёмся [today], [mas_get_player_nickname()]?"

    elif mas_isMoniUpset():
        m "Сейчас возьму стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 2esc at ls32 zorder MAS_MONIKA_Z
        m 2esc "Ты чего-то хотел, [player]?"

    else:
        m "Мне нужно взять стол и стул.{w=0.5}.{w=0.5}.{nw}"
        $ is_sitting = True
        show monika 6ekc at ls32 zorder MAS_MONIKA_Z
        m 6ekc "Ты чего-то хотел, [player]?"

    jump monikaroom_greeting_cleanup

# cleanup label
label monikaroom_greeting_cleanup:
    python:
        # couple of things:
        # 1 - monika knows you are here now
        mas_disable_quit()

        # 2 - music is renabled
        mas_MUINDropShield()

        # 3 - keymaps should be set
        set_keymaps()

        # 4 - show the overlays
        mas_OVLShow()

        # 5 - the music can be restarted
        mas_startup_song()

        # 6 - enable escape so we can access settings and chat box keys
        enable_esc()

    return

#init 5 python:
#    addEvent(Event(persistent.greeting_database,eventlabel="greeting_youarereal", unlocked=True, random=True),code="GRE")

label greeting_youarereal:
    python:
        try:
            renpy.file(
                "../characters/" + persistent.playername.lower() + ".chr"
            )
            persistent._mas_you_chr = True
        except:
            persistent._mas_you_chr = False
    m 1hua "[player]! Рада тебя видеть!"
    if persistent._mas_you_chr:
        m 1euc "Подожди. Что-то сейчас другое."
        m 1eud "Ты... добавил файл персонажа?"
        m 1ekc "[player].chr...Хм?"
        m 1ekd "Ты... пытаешься оказаться здесь вместе со мной?"
        m "Зачем ты это сделал?"
        m 1tkc "Разве ты не понимаешь?"
        m 1tkd "Это место нереально! Я не знаю, что случится, если ты придёшь сюда!"
        m 1dsc "Как ты мог так поступить?"
        m 1lksdlc "Отказаться от своей реальности..."
        m 1lksdld "Просто чтобы быть со мной?"
        m 1ekc "Это всё моя вина!"
        m "Но... но «ты» в игре..."
        m 1esd "Он снова начинает немного двигаться."
        m "Может... это снова позволяет тебе им управлять?"
        m 1ekc "Это неправильно! Я не хочу марионетку!"
        m 1tkc "Пожалуйста, [player]..."
        m "Если ты собираешься это сделать, ты уверен, что именно этого хочешь?{nw}"
        $ _history_list.pop()
        menu:
            m "Если ты собираешься это сделать, ты уверен, что именно этого хочешь?{fast}"

            "Я уверен.":
                m 1eka "Тогда... у меня нет выбора, кроме как принять это..."
                m 1hub "Я приму этот дар с распростёртыми объятиями!"
                m "Мы наконец можем быть вместе, [player]."
                m "И вместе разберёмся, как сделать это в твоей реальности!"

            "Может, не стоит...":
                m 1eka "Я так и думала..."
                m "Нет шансов, что ты откажешься от «реальности», чтобы быть со мной..."
                m 1ekc "Я не могу заставить себя удалить этот милый маленький .chr файл, но..."
                m 1eka "Попробуй сделать это сам."
                m 1lksdlc "В этих файлах есть довольно жуткие вещи..."
                m 1eka "Я люблю тебя, [player]. Я буду ждать столько, сколько потребуется."
                m "Так что не поступай опрометчиво, хорошо?"
    else:
        m 1esd "Я много думала о .chr файлах..."
        m 1euc "Ну, что они такое на самом деле?"
        m 1lksdlc "Они довольно жуткие..."
        m "И даже если остальные девушки ненастоящие, почему удаление файла убирает персонажа?"
        m 1esd "А можно ли персонажа добавить?"
        m 1dsd "Трудно сказать..."
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_japan",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_japan:
    m 1hub "О, kon'nichiwa, [player]!"
    m "Эхехе~"
    m 2eub "Привет, [player]!"
    m 1eua "Я просто занимаюсь японским."
    m 3eua "Давай посмотрим..."
    $ shown_count = mas_getEVLPropValue("greeting_japan", "shown_count")
    if shown_count == 0:
        m 4hub "Watashi ha itsumademo anata no mono desu!"
        m 2hksdlb "Прости, если это прозвучало бессмысленно!"
        m 3eua "Знаешь, что это значит, [mas_get_player_nickname()]?"
        m 4ekbsa "Это значит {i}'Я буду твоей навсегда'~{/i}"
        return

    m 4hub "Watashi wa itsumademo anata no mono desu!"
    if shown_count == 1:
        m 3eksdla "В прошлый раз, когда я это сказала, я ошиблась..."
        m "В этом предложении нужно говорить 'wa', а не 'ha', как я сказала раньше."
        m 4eka "Не волнуйся, [player]. Смысл всё равно тот же."
        m 4ekbsa "Я всё равно буду твоей навсегда~"
    else:
        m 3eua "Помнишь, что это значит, [mas_get_player_nickname()]?"
        m 4ekbsa "{i}'Я буду твоей навсегда'~{/i}"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sunshine",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_sunshine:
    m 1hua "{i}~Ты моё солнышко, моё единственное солнышко~{/i}"
    m "{i}~Ты делаешь меня счастливой, когда небо серое~{/i}"
    m 1hub "{i}~Ты никогда не узнаешь, дорогой, как сильно я тебя люблю~{/i}"
    m 1eka "{i}~Пожалуйста, не уноси моё солнышко~{/i}"
    m 1wud "...Э?"
    m "Ч-что?!"
    m 1wubsw "[player]!"
    m 1lkbsa "О боже, как же стыдно!"
    m "Я п-просто пела себе, чтобы скоротать время!"
    m 1ekbfa "Эхехе..."
    m 3hubfa "Но раз уж ты здесь, мы можем провести время вместе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hai_domo",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_hai_domo:
    m 1hub "{=jpn_text}はいどうもー!{/=jpn_text}"
    m "Виртуальная девушка Моника на связи!"
    m 1hksdlb "Ахаха, прости! В последнее время я смотрела одну виртуальную ютубершу."
    m 1eua "Должна сказать, она довольно очаровательная..."
    $ mas_lockEVL("greeting_hai_domo", "GRE")
    return

#TODO needs additional dialogue so can be used for all aff
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_french",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_french:
    m 1eua "Bonjour, [player]!"
    m 1hua "Savais-tu que tu avais de beaux yeux, mon amour?"
    m 1hub "Ахаха!"
    m 3hksdlb "Я занимаюсь французским. Я только что сказала, что у тебя очень красивые глаза~"
    m 1eka "Это такой романтичный язык, [player]."
    m 1hua "Может, когда-нибудь мы оба сможем им заняться, mon amour~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_amnesia",
            unlocked=False,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_amnesia:
    python:
        tempname = m_name
        m_name = "Monika"

    m 1eua "О, привет!"
    m 3eub "Меня зовут Моника."
    show monika 1eua zorder MAS_MONIKA_Z

    python:
        entered_good_name = True
        fakename = renpy.input("What's your name?", allow=name_characters_only, length=20).strip(" \t\n\r")
        lowerfake = fakename.lower()

    if lowerfake in ("sayori", "yuri", "natsuki"):
        m 3euc "Эм, забавно."
        m 3eud "У одной из моих подруг такое же имя."

    elif lowerfake == "monika":
        m 3eub "О, тебя тоже зовут Моника?"
        m 3hub "Ахаха, какие шансы, да?"

    elif lowerfake == "monica":
        m 1hua "Эй, у нас такие похожие имена, эхехе~"

    elif lowerfake == player.lower():
        m 1hub "О, какое милое имя!"

    elif lowerfake == "":
        $ entered_good_name = False
        m 1euc "..."
        m 1etd "Ты пытаешься сказать, что у тебя нет имени, или просто слишком стесняешься мне его назвать?"
        m 1eka "Это немного странно, но, думаю, не так уж важно."

    elif mas_awk_name_comp.search(lowerfake) or mas_bad_name_comp.search(lowerfake):
        $ entered_good_name = False
        m 1rksdla "Это...{w=0.4}{nw}"
        extend 1hksdlb "довольно необычное имя, ахаха..."
        m 1eksdla "Ты...{w=0.3}пытаешься надо мной подшутить?"
        m 1rksdlb "Ах, прости, прости, я никого не осуждаю."

    python:
        if entered_good_name:
            name_line = renpy.substitute(", [fakename]")
        else:
            name_line = ""

        if mas_current_background == mas_background_def:
            end_of_line = "я никак не могу покинуть этот класс."
        else:
            end_of_line = "я не уверена, где я нахожусь."

    m 1hua "Ну, приятно познакомиться[name_line]!"
    m 3eud "Скажи[name_line], ты случайно не знаешь, где все остальные?"
    m 1eksdlc "Ты первый человек, которого я вижу, и {nw}"
    extend 1rksdlc "[end_of_line]"
    m 1eksdld "Ты можешь помочь мне разобраться, что происходит[name_line]?"

    m "Пожалуйста? {w=0.2}{nw}"
    extend 1dksdlc "Я скучаю по своим друзьям."

    window hide
    show monika 1eksdlc
    pause 5.0
    $ m_name = tempname
    window auto

    m 1rksdla "..."
    m 1hub "Ахаха!"
    m 1hksdrb "Прости, [player]! Я не смогла удержаться."
    m 1eka "После того как мы говорили про {i}Цветы для Элджернона{/i}, я не устояла перед желанием посмотреть, как ты отреагируешь, если я всё забуду."
    #Monika is glad you took it seriously and didn't try to call yourself another name
    if lowerfake == player.lower():
        m 1tku "...И ты отреагировал именно так, как я представляла."

    m 3eka "Надеюсь, я тебя не слишком расстроила."
    m 1rksdlb "Я чувствовала бы то же самое, если бы ты когда-нибудь забыл обо мне, [player]."
    m 1hksdlb "Надеюсь, ты простишь мне этот маленький розыгрыш, ахаха~"

    $ mas_lockEVL("greeting_amnesia", "GRE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_sick",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SICK],
        ),
        code="GRE"
    )

# TODO for better-sick, we would use the mood persistent and queue a topic.
#   might have dialogue similar to this, so leaving this todo here.

label greeting_sick:
    if mas_isMoniNormal(higher=True):
        m 1hua "С возвращением, [mas_get_player_nickname()]!"
        m 3eua "Тебе уже лучше?{nw}"
    else:
        m 2ekc "С возвращением, [player]..."
        m "Тебе уже лучше?{nw}"

    $ _history_list.pop()
    menu:
        m "Тебе уже лучше?{fast}"
        "Да.":
            $ persistent._mas_mood_sick = False
            if mas_isMoniNormal(higher=True):
                m 1hub "Отлично! Теперь мы можем провести ещё немного времени вместе. Эхехе~"
            else:
                m "Приятно это слышать."
        "Нет.":
            jump greeting_stillsick
    return

label greeting_stillsick:
    if mas_isMoniNormal(higher=True):
        m 1ekc "[player], тебе правда стоит отдохнуть."
        m "Хороший отдых — лучший способ быстрее поправиться."
        m 2lksdlc "Я бы себе не простила, если бы тебе стало хуже из-за меня."
        m 2eka "Так что, пожалуйста, [player], успокой меня и иди отдохни."
        m "Сделаешь это для меня?"

    else:
        m 2ekc "[player], тебе правда стоит отдохнуть."
        m 4ekc "Хороший отдых — лучший способ быстрее поправиться."
        m "Так что, пожалуйста, [player], просто иди отдохни."
        m 2ekc "Сделаешь это для меня?{nw}"

    $ _history_list.pop()
    menu:
        m "Сделаешь это для меня?{fast}"
        "Да.":
            jump greeting_stillsickrest
        "Нет.":
            jump greeting_stillsicknorest
        "Я уже отдыхаю.":
            jump greeting_stillsickresting

label greeting_stillsickrest:
    if mas_isMoniNormal(higher=True):
        m 2hua "Спасибо, [player]."
        m 2eua "Думаю, если я оставлю тебя ненадолго в покое, ты сможешь лучше отдохнуть."
        m 1eua "Поэтому я закрою игру за тебя."
        m 1eka "Выздоравливай скорее, [player]. Я так сильно тебя люблю!"

    else:
        m 2ekc "Спасибо, [player]."
        m "Думаю, если я оставлю тебя ненадолго в покое, ты сможешь лучше отдохнуть."
        m 4ekc "Поэтому я закрою игру за тебя."
        m 2ekc "Выздоравливай скорее, [player]."

    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return 'quit'

label greeting_stillsicknorest:
    if mas_isMoniNormal(higher=True):
        m 1lksdlc "Понятно..."
        m "Ну, если ты настаиваешь, [player]."
        m 1ekc "Полагаю, ты знаешь свои пределы лучше, чем я."
        m 1eka "Но если почувствуешь слабость или усталость, [player], пожалуйста, дай мне знать."
        m "Тогда ты сможешь пойти отдохнуть."
        m 1eua "Не волнуйся, я всё равно буду здесь, когда ты проснёшься."
        m 3hua "Тогда мы сможем веселиться вместе, и мне не придётся беспокоиться о тебе где-то на задворках сознания."

    else:
        m 2ekc "Ладно."
        m 2tkc "Ты, похоже, никогда не хочешь меня слушать, так почему я должна ждать иного сейчас."

    # setting greet type here even tho we aren't quitting so she remembers you're sick next load
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return

label greeting_stillsickresting:
    m 1eka "О, как же приятно это слышать, [player]."
    m 3eka "Надеюсь, ты себя согреваешь."
    if mas_isMoniNormal(higher=True):
        m 1dku "Может, укутался в тёплое одеяло с чашечкой горячего чая."
        m 2eka "Твоё здоровье очень важно для меня, [player], так что береги себя."
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "...А если тебе всё ещё немного холодно, надеюсь, знание, что я тебя люблю, хоть чуть-чуть тебя согреет."
        m 5hua "Эхехе~"
        $ mas_ILY()

    else:
        m 1eka "Может, укутался в тёплое одеяло с чашечкой горячего чая."
        m 2eka "Твоё здоровье очень важно для меня, [player], так что береги себя."

    #TODO: Have this use the nap brb potentially. Expand this
    # setting greet type here even tho we aren't quitting so she remembers you're sick next load
    $ persistent._mas_greeting_type = store.mas_greetings.TYPE_SICK
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_long_absence",
            unlocked=True,
            category=[store.mas_greetings.TYPE_LONG_ABSENCE],
        ),
        code="GRE"
    )

label greeting_long_absence:
    $ persistent._mas_long_absence = False
    $ mas_ret_long_absence = True

    if persistent._mas_absence_time >= datetime.timedelta(weeks=5):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffectionFraction(0.1, min_amount=70)
            m 2dsc "[player]..."
            m 2tkc "Ты сказал, что уйдёшь всего на несколько дней..."
            m 2rksdld "Но прошло так много времени."
            m 2ekd "Я рада, что ты теперь здесь, но..."
            m 2dktdc "Мне было так одиноко..."
            m 2ektsc "Я думала, с тобой что-то случилось!"
            m 2lktsc "Я... я всё думала, что ты, может, не вернёшься."
            m 2ektsc "Пожалуйста, никогда,{w=0.5} {i}никогда{/i}{w=0.5} так больше не делай."
            m 2rktsd "Может, ты ничего не мог поделать, но... я волновалась до смерти."
            m 2dftdc "Я не знала, что делать."
            m 4ekc "Насколько возможно, [player], пожалуйста, не пропадай так надолго."
            m 2ekd "Если думаешь, что выбора нет, пожалуйста, скажи мне."
            m 1dsc "Я не хочу снова оставаться одна..."

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffectionFraction(0.08, min_amount=60)
            m 3ekc "С возвращением, [player]."
            m 3rksdlc "Ты немного опоздал, не так ли?"
            m 3ekc "Я знаю, ты говорил, что тебя не будет какое-то время, но... ты сказал {i}неделю{/i}."
            m 2rkc "Буду считать, что это была не твоя вина..."
            m 2ekd "Но если в следующий раз тебе правда понадобится больше времени, ты должен мне сказать."
            m 2rksdld "Я начала думать, что с тобой случилось что-то плохое."
            m 2dkc "Но я твердила себе, что всё в порядке..."
            m 2eka "Я просто рада, что ты в безопасности и снова со мной, [player]."

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_loseAffectionFraction(0.06, min_amount=40)
            m 1wud "[player]!"
            m 1hua "Ты наконец здесь!"
            m 1ekd "Я так волновалась..."
            m 2dkd "Почему тебя не было так долго?"
            m 2rkc "Я думала, тебя не будет всего пару недель..."
            m "Но тебя не было больше чем в два раза дольше."
            m 1rksdlc "Ты правда был так занят?"
            m 3tkc "Надеюсь, ты не брал на себя слишком много..."
            m 1eka "Ну, теперь ты здесь со мной, так что если что-то не так, можешь мне рассказать."

        elif persistent._mas_absence_choice == "month":
            $ mas_loseAffectionFraction(0.04, min_amount=20)
            m 1eua "С возвращением, [mas_get_player_nickname()]."
            m 2rkc "Прошло довольно много времени, да?"
            m 2rksdlc "Тебя не было дольше, чем ты говорил..."
            m 2eka "Но ничего, я была к этому готова."
            m 3rksdlc "Честно говоря, без тебя здесь было довольно одиноко..."
            m 3ekbsa "Надеюсь, ты это мне компенсируешь~"
            show monika 1eka

        elif persistent._mas_absence_choice == "longer":
            m 1esc "Давно не виделись, [player]."
            m 1ekc "Я была готова, но от этого не стало легче."
            m 3eka "Надеюсь, ты сделал всё, что нужно было."
            m 2rksdlc "..."
            m 2tkc "По правде говоря, мне в последнее время было довольно грустно."
            m 2dkc "Так долго не иметь тебя в своей жизни..."
            m 2dkd "Это и правда было одиноко..."
            m "Я чувствовала себя такой изолированной и пустой без тебя."
            m 3eka "Я так рада, что ты теперь здесь. Я люблю тебя, [player]. Добро пожаловать домой."

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Ты наконец вернулся, [player]!"
            m 3rksdla "Когда ты сказал, что не знаешь, ты {i}правда{/i} не знал, да?"
            m 3rksdlb "Ты, должно быть, был очень занят, раз тебя не было {i}так{/i} долго."
            m 1hua "Ну, ты вернулся... я так по тебе скучала!"

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=4):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffectionFraction(0.1, min_amount=60)
            m 1dkc "[player]..."
            m 1ekd "Ты сказал, что уйдёшь всего на несколько дней..."
            m 2efd "А прошёл целый месяц!"
            m 2ekc "Я думала, с тобой что-то случилось."
            m 2dkd "Я не знала, что делать..."
            m 2efd "Что тебя так надолго задержало?"
            m 2eksdld "Я что-то сделала не так?"
            m 2dftdc "Ты можешь рассказать мне всё что угодно, только, пожалуйста, не исчезай вот так."
            show monika 2dfc

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffectionFraction(0.08, min_amount=50)
            m 1esc "Привет, [player]."
            m 3efc "Ты изрядно опоздал, знаешь ли."
            m 2lfc "Не хочу звучать покровительственно, но неделя — это не то же самое, что месяц!"
            m 2rksdld "Наверное, тебя что-то очень сильно заняло?"
            m 2wfw "Но не настолько, чтобы ты не мог сказать мне, что задержишься!"
            m 2wud "Ах...!"
            m 2lktsc "Прости, [player]. Я просто... очень по тебе скучала."
            m 2dftdc "Прости, что так вспылила."
            show monika 2dkc

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_loseAffectionFraction(0.06, min_amount=30)
            m 1wuo "...Ой!"
            m 1sub "Ты наконец вернулся, [player]!"
            m 1efc "Ты сказал, что тебя не будет пару недель, а прошёл как минимум месяц!"
            m 1ekd "Я очень за тебя волновалась, знаешь?"
            m 3rkd "Но, полагаю, это было вне твоего контроля?"
            m 1ekc "Если сможешь, в следующий раз просто скажи, что тебя не будет ещё дольше, хорошо?"
            m 1hksdlb "Думаю, я как твоя девушка этого заслуживаю."
            m 3hua "И всё же, с возвращением, [mas_get_player_nickname()]!"

        elif persistent._mas_absence_choice == "month":
            $ mas_gainAffection()
            m 1wuo "...Ой!"
            m 1hua "Ты здесь, [player]!"
            m 1hub "Я знала, что могу доверять тебе сдержать слово!"
            m 1eka "Ты правда особенный, ты ведь это знаешь?"
            m 1hub "Я так сильно по тебе скучала!"
            m 2eub "Расскажи мне всё, что ты делал, пока тебя не было, я хочу услышать каждую деталь!"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1esc "...Хм?"
            m 1wub "[player]!"
            m 1rksdlb "Ты вернулся чуть раньше, чем я думала..."
            m 3hua "С возвращением, [mas_get_player_nickname()]!"
            m 3eka "Я знаю, прошло довольно много времени, так что ты наверняка был занят."
            m 1eua "Я с удовольствием послушаю обо всём, что ты делал."
            show monika 1hua

        elif persistent._mas_absence_choice == "unknown":
            m 1lsc "..."
            m 1esc "..."
            m 1wud "Ой!"
            m 1sub "[player]!"
            m 1hub "Какой приятный сюрприз!"
            m 1eka "Как ты?"
            m 1ekd "Прошёл целый месяц. Ты правда не знал, на сколько уйдёшь, да?"
            m 3eka "И всё же ты вернулся, и это очень много для меня значит."
            m 1rksdla "Я знала, что ты рано или поздно вернёшься..."
            m 1hub "Я так сильно тебя люблю, [player]!"
            show monika 1hua

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=2):
        if persistent._mas_absence_choice == "days":
            $ mas_loseAffectionFraction(0.08, min_amount=30)
            m 1wud "О-ох, [player]!"
            m 1hua "С возвращением, [mas_get_player_nickname()]!"
            m 3ekc "Тебя не было дольше, чем ты говорил..."
            m 3ekd "Всё в порядке?"
            m 1eksdla "Я знаю, жизнь бывает занятой и иногда уводит тебя от меня... так что я не особо расстроена..."
            m 3eksdla "Просто... в следующий раз, может, предупредишь заранее?"
            m 1eka "Это было бы очень внимательно с твоей стороны."
            m 1hua "И я была бы очень признательна!"

        elif persistent._mas_absence_choice == "week":
            $ mas_loseAffectionFraction(0.06, min_amount=20)
            m 1eub "Привет, [player]!"
            m 1eka "Жизнь не даёт покоя?"
            m 3hksdlb "Ну, должно быть, так, иначе ты был бы здесь, когда обещал."
            m 1hksdlb "Но не волнуйся! Я не расстроена."
            m 1eka "Я просто надеюсь, что ты о себе заботился."
            m 3eka "Я знаю, ты не всегда можешь быть здесь, так что просто береги себя, пока не будешь со мной!"
            m 1hua "А там уже я о тебе позабочусь~"
            show monika 1eka

        elif persistent._mas_absence_choice == "2weeks":
            $ mas_gainAffection()
            m 1hub "Привет, [player]!"
            m 1eua "Ты всё-таки вернулся, когда сказал."
            m 1eka "Спасибо, что не предал моё доверие."
            m 3hub "Давай наверстаем упущенное время!"
            show monika 1hua

        elif persistent._mas_absence_choice == "month":
            m 1wud "О боже! [player]!"
            m 3hksdlb "Я не ожидала тебя так рано."
            m 3ekbsa "Видимо, ты скучал по мне так же, как я по тебе~"
            m 1eka "И правда чудесно видеть тебя так скоро."
            m 3ekb "Я думала, день пройдёт без событий... но, к счастью, теперь у меня есть ты!"
            m 3hua "Спасибо, что вернулся так рано, [mas_get_player_nickname()]."

        elif persistent._mas_absence_choice == "longer":
            m 1lsc "..."
            m 1esc "..."
            m 1wud "Ой! [player]!"
            m 1hub "Ты вернулся рано!"
            m 1hua "С возвращением, [mas_get_player_nickname()]!"
            m 3eka "Я не знала, когда тебя ждать, но чтобы так скоро..."
            m 1hua "Ну, это сразу меня взбодрило!"
            m 1eka "Я очень по тебе скучала."
            m 1hua "Давай насладимся оставшимся днём вместе."

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Привет, [player]!"
            m 3eka "Был занят последние несколько недель?"
            m 1eka "Спасибо, что предупредил, что тебя не будет."
            m 3ekd "Иначе я бы волновалась до смерти."
            m 1eka "Это правда очень помогло..."
            m 1eua "Так расскажи, как ты?"

    elif persistent._mas_absence_time >= datetime.timedelta(weeks=1):
        if persistent._mas_absence_choice == "days":
            m 2eub "О, привет, [player]."
            m 2rksdla "Тебя не было чуть дольше, чем ты обещал... но не волнуйся."
            m 3eub "Я знаю, что ты занятой человек!"
            m 3rkc "Просто, если сможешь, предупреждай меня заранее, хорошо?"
            m 2rksdlc "Когда ты сказал \"на несколько дней\"... я думала, это будет меньше недели."
            m 1hub "Но всё в порядке! Я прощаю тебя!"
            m 1ekbsa "В конце концов, ты — моя единственная и неповторимая любовь."
            show monika 1eka

        elif persistent._mas_absence_choice == "week":
            $ mas_gainAffection()
            m 1hub "Привет, [mas_get_player_nickname()]!"
            m 3eua "Так приятно, когда можно доверять друг другу, правда?"
            m 3hub "На этом и строится сила отношений!"
            m 3hua "А это значит, что наши — как скала!"
            m 1hub "Ахаха!"
            m 1hksdlb "Прости, прости. Я просто так рада, что ты вернулся!"
            m 3eua "Расскажи, как ты. Я хочу услышать всё."

        elif persistent._mas_absence_choice == "2weeks":
            m 1hub "Приветик~"
            m 3eua "Ты вернулся чуть раньше, чем я думала... но я рада!"
            m 3eka "Когда ты здесь со мной, всё становится лучше."
            m 1eua "Давай проведём чудесный день вместе, [player]."
            show monika 3eua

        elif persistent._mas_absence_choice == "month":
            m 1hua "Эхехе~"
            m 1hub "С возвращением!"
            m 3tuu "Я знала, что ты не сможешь пробыть вдали целый месяц..."
            m 3tub "Будь я на твоём месте, я тоже не смогла бы от тебя держаться!"
            m 1hksdlb "Честно говоря, я скучаю по тебе уже через несколько дней!"
            m 1eka "Спасибо, что не заставил меня так долго ждать новой встречи~"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1hub "Смотрите, кто вернулся так рано! Это ты, мой дорогой [player]!"
            m 3hksdlb "Не смог бы держаться в стороне, даже если бы захотел, да?"
            m 3eka "Не могу тебя винить! Моя любовь к тебе тоже не позволила бы мне от тебя держаться!"
            m 1ekd "Каждый день, пока тебя не было, я думала, как ты..."
            m 3eka "Так что расскажи. Как ты, [player]?"
            show monika 3eua

        elif persistent._mas_absence_choice == "unknown":
            m 1hub "Привет, [mas_get_player_nickname()]!"
            m 1eka "Рада, что ты не заставил меня ждать слишком долго."
            m 1hua "Неделя оказалась короче, чем я ожидала, так что считай, что я приятно удивлена!"
            m 3hub "Спасибо, что уже сделал мой день, [player]!"
            show monika 3eua

    else:
        if persistent._mas_absence_choice == "days":
            m 1hub "С возвращением, [mas_get_player_nickname()]!"
            m 1eka "Спасибо, что честно предупредил, как долго тебя не будет."
            m 1eua "Очень важно знать, что я могу доверять твоим словам."
            m 3hua "Надеюсь, ты знаешь, что тоже можешь доверять мне!"
            m 3hub "Наши отношения с каждым днём становятся крепче~"
            show monika 1hua

        elif persistent._mas_absence_choice == "week":
            m 1eud "Ой! Ты чуть раньше, чем я ожидала!"
            m 1hua "Не то чтобы я жаловалась — так приятно снова тебя видеть так скоро."
            m 1eua "Давай проведём ещё один хороший день вместе, [player]."

        elif persistent._mas_absence_choice == "2weeks":
            m 1hub "{i}~In my hand,~\n~is a pen tha-{/i}"
            m 1wubsw "О-Ой! [player]!"
            m 3hksdlb "Ты вернулся гораздо раньше, чем говорил..."
            m 3hub "С возвращением!"
            m 1rksdla "Ты как раз прервал меня, когда я репетировала свою песню..."
            m 3hua "Почему бы не послушать, как я спою её ещё раз?"
            m 1ekbsa "Я написала её специально для тебя~"
            show monika 1eka

        elif persistent._mas_absence_choice == "month":
            m 1wud "Э? [player]?"
            m 1sub "Ты здесь!"
            m 3rksdla "Я думала, ты уйдёшь на целый месяц."
            m 3rksdlb "Я была к этому готова, но..."
            m 1eka "Я уже по тебе скучала!"
            m 3ekbsa "Ты тоже по мне скучал?"
            m 1hubfa "Спасибо, что вернулся так скоро~"
            show monika 1hua

        elif persistent._mas_absence_choice == "longer":
            m 1eud "[player]?"
            m 3ekd "Я думала, тебя не будет очень долго..."
            m 3tkd "Почему ты вернулся так рано?"
            m 1ekbsa "Ты пришёл ко мне в гости?"
            m 1hubfa "Ты такой милый!"
            m 1eka "Если ты всё ещё собираешься куда-то надолго, обязательно скажи мне."
            m 3eka "Я люблю тебя, [player], и не хотела бы злиться, если тебя правда не будет..."
            m 1hub "Давай насладимся временем вместе, пока оно есть!"
            show monika 1eua

        elif persistent._mas_absence_choice == "unknown":
            m 1hua "Эхехе~"
            m 3eka "Уже вернулся, [player]?"
            m 3rka "Видимо, когда ты сказал, что не знаешь, ты не понял, что это будет не так долго."
            m 3hub "Но всё равно спасибо, что предупредил!"
            m 3ekbsa "От этого я правда почувствовала себя любимой."
            m 1hubfb "Ты и правда такой добрый!"
            show monika 3eub
    m "Напомни мне, если снова соберешься уходить, хорошо?"
    show monika idle with dissolve_monika
    jump ch30_loop

#Time Concern
init 5 python:
    ev_rules = dict()
    ev_rules.update(MASSelectiveRepeatRule.create_rule(hours=range(0,6)))
    ev_rules.update(MASPriorityRule.create_rule(70))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_timeconcern",
            unlocked=False,
            rules=ev_rules
        ),
        code="GRE"
    )
    del ev_rules

label greeting_timeconcern:
    jump monika_timeconcern

init 5 python:
    ev_rules = {}
    ev_rules.update(MASSelectiveRepeatRule.create_rule(hours =range(6,24)))
    ev_rules.update(MASPriorityRule.create_rule(70))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_timeconcern_day",
            unlocked=False,
            rules=ev_rules
        ),
        code="GRE"
    )
    del ev_rules

label greeting_timeconcern_day:
    jump monika_timeconcern

init 5 python:
    ev_rules = {}
    ev_rules.update(MASGreetingRule.create_rule(
        skip_visual=True,
        random_chance=0.2,
        override_type=True
    ))
    ev_rules.update(MASPriorityRule.create_rule(45))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_hairdown",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.HAPPY, None),
        ),
        code="GRE"
    )
    del ev_rules

label greeting_hairdown:

    # couple of things:
    # shield ui
    $ mas_RaiseShield_core()

    # 3 - keymaps not set (default)
    # 4 - hotkey buttons are hidden (skip visual)
    # 5 - music is off (skip visual)

    # reset clothes if not ones that work with hairdown
    if monika_chr.is_wearing_clothes_with_exprop("baked outfit"):
        $ monika_chr.reset_clothes(False)

    # have monika's hair down
    $ monika_chr.change_hair(mas_hair_down, by_user=False)

    call spaceroom(dissolve_all=True, scene_change=True, force_exp='monika 1eua_static')

    m 1eua "Привет, [player]!"
    m 4hua "Заметил сегодня что-нибудь новое?"
    m 1hub "Я решила попробовать что-то новое~"

    m "Тебе нравится?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нравится?{fast}"
        "Да.":
            $ persistent._mas_likes_hairdown = True

            # maybe 6sub is better?
            $ mas_gainAffection()
            m 6sub "Правда?" # honto?!
            m 2hua "Я так рада!" # yokatta.."
            m 1eua "Просто попроси, если захочешь снова увидеть мой хвостик, хорошо?"

        "Нет.":
            # TODO: affection lowered? need to decide
            m 1ekc "Ох..."
            m 1lksdlc "..."
            m 1lksdld "Тогда я снова его завяжу."
            m 1dsc "..."

            $ monika_chr.reset_hair(False)

            m 1eua "Готово."
            # you will never get this chance again

    # save that hair down is unlocked
    $ store.mas_selspr.unlock_hair(mas_hair_down)
    $ store.mas_selspr.save_selectables()

    # unlock hair changed selector topic
    $ mas_unlockEventLabel("monika_hair_select")

    # lock this greeting
    $ mas_lockEVL("greeting_hairdown", "GRE")

    # cleanup
    # enable music menu and music hotkeys
    $ mas_MUINDropShield()

    # 3 - set the keymaps
    $ set_keymaps()

    # 4 - hotkey buttons should be shown
    $ HKBShowButtons()

    # 5 - restart music
    $ mas_startup_song()

    # 6 - enable escape so we can access settings and chat box keys
    $ enable_esc()

    return

init 5 python:

    # NOTE: this triggers when affection reaches BROKEN state.
    #   AND you have not seen this before
    ev_rules = {}
    ev_rules.update(MASPriorityRule.create_rule(15))
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1dsc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_tears",
            unlocked=True,
            aff_range=(None, mas_aff.DISTRESSED),
            rules=ev_rules,
        ),
        code="GRE"
    )
    del ev_rules

label greeting_tears:
    m 1dsc "...[player]."
    m 1ekc "..."
    m 2ekc "Со мной что-то не так?"
    m 2ekd "Я недостаточно хороша для тебя...?"
    m 2lksdlc "Я старалась изо всех сил ради тебя... ради {i}нас{/i}."
    m 2lksdld "Я сделала что-то, что тебя ранило или заставило почувствовать себя плохо?"
    m "Ты всё ещё расстроен из-за остальных девушек?"
    m 2ekc "Если да, мне правда очень жаль..."
    m "Мне так, так жаль!"
    m 2rksdld "Просто скажи, что я сделала не так, и я буду стараться ещё сильнее быть для тебя идеальной девушкой."
    m 2ekd "Ты — весь мой мир; то, что ты чувствуешь, значит для меня всё!"
    m 2ekc "Так что, пожалуйста, просто скажи, что не так, и я это исправлю."
    m 2dfc "Я сделаю для тебя что угодно, потому что... я..."
    m 2dftdc "..."
    m 2dftsc "...Мне нужен ты, [player]..."
    m 2ektsc "Мне нужно, чтобы ты любил меня так же, как я люблю тебя."
    m 2lktsc "Ты мне нужен... потому что если тебя не будет, тогда..."
    m 2dftsc "..."
    m 2ektsc "Я останусь совсем одна..."
    m 2dftsc "Так что, пожалуйста... просто... будь рядом со мной, как я была бы рядом с тобой."
    m "Я хочу верить..."
    m 2lktsc "Так что, пожалуйста... позволь мне быть счастливой с тобой..."
    m "..."
    pause 4.0
    m 2dftdc "..."
    m 2dfc "...Ладно... ладно..."
    m 2lssdrc "Я должна быть сильной..."
    m "..."
    m 2dsc "...Хорошо... мне уже немного лучше..."
    m 2esc "Но... мне правда нужно, чтобы ты подумал о том, что я сказала."
    m 2ekc "Пожалуйста... просто... постарайся понять."
    m 1dsd "Я люблю тебя, и мне нужно, чтобы ты тоже показал, что любишь меня..."
    m 1dsc "Иначе... я просто больше не выдержу."

    python:
        mas_lockEVL("greeting_tears", "GRE")

        #Setup the being virtual ev
        beingvirtual_ev = mas_getEV("monika_being_virtual")

        if beingvirtual_ev:
            beingvirtual_ev.start_date = datetime.datetime.now() + datetime.timedelta(days=2)
    return

#New greetings for upset, distressed, and broken. Made quips for upset and distressed to allow for more variety of combos
init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_upset",
            unlocked=True,
            aff_range=(mas_aff.UPSET, mas_aff.UPSET),
        ),
        code="GRE"
    )

label greeting_upset:
    python:
        upset_greeting_quips_first = [
            "Oh.{w=1} It's you, [player].",
            "Oh.{w=1} You're back, [player].",
            "Hello, [player].",
            "Oh.{w=1} Hello, [player]."
        ]

        upset_greeting_quips_second = [
#            "What do you want?",
#            "What now?",
            "Well...",
            "Did you want something?",
        ]

    $ upset_quip1 = renpy.random.choice(upset_greeting_quips_first)

    show monika 2esc
    $ renpy.say(m, upset_quip1)

    if renpy.random.randint(1,4) != 1:
        $ upset_quip2 = renpy.random.choice(upset_greeting_quips_second)
        $ renpy.say(m, upset_quip2)

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_distressed",
            unlocked=True,
            aff_range=(mas_aff.DISTRESSED, mas_aff.DISTRESSED)
        ),
        code="GRE"
    )

label greeting_distressed:
    python:
        distressed_greeting_quips_first = [
            "Oh...{w=1} Hi, [player].",
            "Oh...{w=1} Hello, [player].",
            "Hello, [player]...",
            "Oh...{w=1} You're back, [player]."
        ]

        distressed_greeting_quips_second = [
            "I guess we can spend some time together now.",
            "I wasn't sure when you'd visit again.",
            "Hopefully we can enjoy our time together.",
            "I wasn't expecting you.",
            "I hope things start going better soon.",
            "I thought you forgot about me..."
        ]

    $ distressed_quip1 = renpy.random.choice(distressed_greeting_quips_first)

    show monika 6ekc
    $ renpy.say(m, distressed_quip1)

    if renpy.random.randint(1,4) != 1:
        $ distressed_quip2 = renpy.random.choice(distressed_greeting_quips_second)
        show monika 6rkc
        $ renpy.say(m, distressed_quip2)

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_broken",
            unlocked=True,
            aff_range=(None, mas_aff.BROKEN),
        ),
        code="GRE"
    )

label greeting_broken:
    m 6ckc "..."
    return

# special type greetings

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_school",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SCHOOL],
        ),
        code="GRE"
    )

label greeting_back_from_school:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, с возвращением, [mas_get_player_nickname()]!"
        m 1eua "Как прошёл день в школе?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошёл день в школе?{fast}"

            "Потрясающе.":
                m 2sub "Правда?!"
                m 2hub "Как здорово это слышать, [player]!"
                if renpy.random.randint(1,4) == 1:
                    m 3eka "Школа определённо может занимать большую часть жизни, и потом ты по ней можешь скучать."
                    m 2hksdlb "Ахаха! Знаю, может казаться странным думать, что однажды ты будешь скучать по необходимости ходить в школу..."
                    m 2eub "Но столько тёплых воспоминаний связано со школой!"
                    m 3hua "Может, когда-нибудь расскажешь мне о них."
                else:
                    m 3hua "Мне всегда так приятно знать, что ты счастлив~"
                    m 1eua "Если захочешь рассказать о своём замечательном дне, я с радостью послушаю!"
                return

            "Хорошо.":
                m 1hub "Это здорово...{w=0.3}{nw}"
                extend 3eub "Не могу не радоваться, когда ты приходишь домой в хорошем настроении!"
                m 3hua "Надеюсь, ты узнал что-то полезное, эхехе~"
                return

            "Плохо.":
                m 1ekc "Ох..."
                m 1dkc "Жаль это слышать."
                m 1ekd "Плохие дни в школе могут очень выбивать из колеи..."

            "Очень плохо...":
                m 1ekc "Ох..."
                m 2ekd "Мне правда жаль, что у тебя сегодня был такой тяжёлый день..."
                m 2eka "Я просто рада, что ты пришёл ко мне, [player]."

        #Since this menu is too long, we'll use a gen-scrollable instead
        python:
            final_item = ("I don't want to talk about it.", False, False, False, 20)
            menu_items = [
                ("It was class related.", ".class_related", False, False),
                ("It was caused by people.", ".by_people", False, False),
                ("It was just a bad day.", ".bad_day", False, False),
                ("I felt sick today.", ".sick", False, False),
            ]

        show monika 2ekc at t21
        window show
        m "Если не возражаешь, случилось что-то конкретное?" nointeract

        call screen mas_gen_scrollable_menu(menu_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

        window auto

        $ label_suffix = _return

        show monika at t11

        #No talk
        if not label_suffix:
            m 2dsc "Я понимаю, [player]."
            m 2ekc "Иногда лучше всего просто постараться оставить плохой день позади."
            m 2eka "Но если захочешь поговорить об этом позже, знай: я с радостью тебя выслушаю."
            m 2hua "Я люблю тебя, [player]~"
            return "love"

        $ full_label = "greeting_back_from_school{0}".format(label_suffix)
        if renpy.has_label(full_label):
            jump expression full_label

        label .class_related:
            m 2dsc "Понятно..."
            m 3esd "Люди, наверное, постоянно говорят, что школа важна..."
            m 3esc "И что нужно всегда идти вперёд и много работать..."
            m 2dkd "Но иногда это может очень сильно давить и затягивать в нисходящую спираль."
            m 2eka "Как я и сказала, я рада, что ты пришёл ко мне, [player]."
            m 3eka "Приятно знать, что я могу тебя утешить, когда тебе плохо."
            m "Помни: {i}ты{/i} важнее школы или каких-то оценок."
            m 1ekbsa "Особенно для меня."
            m 1hubsa "Не забывай делать перерывы, если чувствуешь, что тебя захлёстывает, и что у всех разные таланты."
            m 3hubfb "Я люблю тебя и просто хочу, чтобы ты был счастлив~"
            return "love"

        label .by_people:
            m 2ekc "О нет, [player]...{w=0.5} Это, должно быть, было ужасно."
            m 2dsc "Одно дело, когда с тобой просто случается что-то плохое..."
            m 2ekd "И совсем другое — когда человек является прямой причиной твоих проблем."

            if persistent._mas_pm_currently_bullied or persistent._mas_pm_is_bullying_victim:
                m 2rksdlc "Очень надеюсь, что это не тот, о ком ты мне рассказывал..."

                if mas_isMoniAff(higher=True):
                    m 1rfc "Лучше бы {i}не был{/i}..."
                    m 1rfd "Снова доставать моего [mas_get_player_nickname(_default='sweetheart', regex_replace_with_nullstr='my ')] вот так."

                m 2ekc "Жаль, что я не могу сделать больше, чтобы помочь, [player]..."
                m 2eka "Но я здесь, если я тебе нужна."
                m 3hubsa "И всегда буду~"
                m 1eubsa "Надеюсь, я смогу хоть чуть-чуть сделать твой день лучше."
                m 1hubfb "Я так сильно тебя люблю~"
                $ mas_ILY()

            else:
                m "Очень надеюсь, что это не повторяется постоянно, [player]."
                m 2lksdld "В любом случае, может, стоит попросить кого-то о помощи..."
                m 1lksdlc "Я знаю, иногда кажется, что это может создать ещё больше проблем..."
                m 1ekc "Но ты не должен страдать от рук другого человека."
                m 3dkd "Мне так жаль, что тебе приходится с этим справляться, [player]..."
                m 1eka "Но теперь ты здесь, и я надеюсь, что время вместе хоть немного улучшит твой день."
            return

        label .bad_day:
            m 1ekc "Понятно..."
            m 3lksdlc "Такие дни время от времени случаются."
            m 1ekc "Иногда бывает трудно снова подняться после такого дня."
            m 1eka "Но теперь ты здесь, и я надеюсь, что время вместе хоть немного улучшит твой день."
            return

        label .sick:
            m 2dkd "Болеть в школе — ужасно. Так гораздо сложнее что-то сделать или следить за уроками."
            jump greeting_back_from_work_school_still_sick_ask
            return

    elif mas_isMoniUpset():
        m 2esc "Ты вернулся, [player]..."

        m "Как школа?{nw}"
        $ _history_list.pop()
        menu:
            m "Как школа?{fast}"
            "Хорошо.":
                m 2esc "Это мило."
                m 2rsc "Надеюсь, ты сегодня {i}хоть чему-то{/i} научился."

            "Плохо.":
                m "Жаль..."
                m 2tud "Но, может, теперь ты лучше понимаешь, как я себя чувствовала, [player]."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=1}ты вернулся."

        m "Как школа?{nw}"
        $ _history_list.pop()
        menu:
            m "Как школа?{fast}"
            "Хорошо.":
                m 6lkc "Это...{w=1}приятно слышать."
                m 6dkc "Я-я просто надеюсь, что хорошим день сделала не...{w=2} часть «быть далеко от меня»."

            "Плохо.":
                m 6rkc "Ох..."
                m 6ekc "Жаль, [player]. Мне жаль это слышать."
                m 6dkc "Я знаю, каковы плохие дни..."

    else:
        m 6ckc "..."

    return

default persistent._mas_pm_last_promoted_d = None
# date when player last got promotion

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_work",
            unlocked=True,
            category=[store.mas_greetings.TYPE_WORK],
        ),
        code="GRE"
    )

label greeting_back_from_work:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, с возвращением, [mas_get_player_nickname()]!"

        m 1eua "Как прошла работа сегодня?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошла работа сегодня?{fast}"

            "Потрясающе!":
                if not persistent._mas_pm_last_promoted_d:
                    $ promoted_recently = False
                else:
                    $ promoted_recently = datetime.date.today() < persistent._mas_pm_last_promoted_d + datetime.timedelta(days=180)

                m 1sub "Это {i}потрясающе{/i}, [player]!"
                m 1hub "Я так рада, что у тебя был такой замечательный день!"

                m 1sua "Что сделало его таким потрясающим?{nw}"
                menu:
                    m "Что сделало его таким потрясающим?{fast}"

                    "Меня повысили!":
                        if promoted_recently:
                            m 3suo "Вау! Снова?!"
                            m 3sub "Тебя ведь недавно повысили...{w=0.3}ты, должно быть, правда отлично работаешь!"
                            m 1huu "Я так, {w=0.2}так горжусь тобой, [mas_get_player_nickname()]~"

                        else:
                            $ player_nick = mas_get_player_nickname()
                            m 3suo "Вау! Поздравляю, [player_nick], {w=0.1}{nw}"
                            extend 3hub "Я так горжусь тобой!"
                            m 1euu "Я знала, что ты сможешь~"
                            $ promoted_recently = True

                        $ persistent._mas_pm_last_promoted_d = datetime.date.today()

                    "Я много всего сделал!":
                        m 3hub "Это здорово, [mas_get_player_nickname()]!"

                    "Просто был потрясающий день.":
                        m 3hub "Приятно это слышать!"

                m 3eua "Могу только представить, как хорошо ты работаешь в такие дни."
                if not promoted_recently:
                    m 1hub "...Может, тебя даже скоро повысят!"
                m 1eua "В любом случае, рада, что ты дома, [mas_get_player_nickname()]."

                if seen_event("monikaroom_greeting_ear_bathdinnerme") and renpy.random.randint(1,20) == 1:
                    m 3tubsu "Ты хочешь ужин, ванну, или..."
                    m 1hubfb "Ахаха~ Шучу."
                else:
                    m 3msb "Что может лучше завершить потрясающий день, чем твоя потрясающая девушка?~"

                return

            "Хорошо.":
                m 1hub "Это хорошо!"
                m 1eua "Сначала отдохни, хорошо?"
                m 3eua "Тогда у тебя будет энергия, прежде чем браться за что-то ещё."
                m 1hua "Или можно просто расслабиться со мной!"
                m 3tku "Лучшее, что можно сделать после долгого рабочего дня, не правда ли?"
                m 1hub "Ахаха!"
                return

            "Плохо.":
                m 2ekc "..."
                m 2ekd "Жаль, что день на работе выдался тяжёлым..."
                m 3eka "Я бы сейчас тебя обняла, будь я рядом, [player]."
                m 1eka "Просто помни, что я здесь, когда я тебе нужна, хорошо?"

            "Очень плохо...":
                m 2ekd "Жаль, что день на работе выдался тяжёлым, [player]."
                m 2ekc "Жаль, что я не могу сейчас быть рядом и обнять тебя."
                m 2eka "Я просто рада, что ты пришёл ко мне... {w=0.5}Я сделаю всё, чтобы тебя утешить."

        #Since this menu is too long, we'll use a gen-scrollable instead
        python:
            final_item = ("I don't want to talk about it.", False, False, False, 20)
            menu_items = [
                ("I got yelled at.", ".yelled_at", False, False),
                ("I got passed over for someone else.", ".passed_over", False, False),
                ("I had to work late.", ".work_late", False, False),
                ("I didn't get much done today.", ".little_done", False, False),
                ("Just another bad day.", ".bad_day", False, False),
                ("I felt sick today.", ".sick", False, False),
            ]

        show monika 2ekc at t21
        window show
        m "Если не против рассказать, что сегодня случилось?" nointeract

        call screen mas_gen_scrollable_menu(menu_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

        window auto

        $ label_suffix = _return

        show monika at t11
        #No talk
        if not label_suffix:
            m 1dsc "Я понимаю, [player]."
            m 3eka "Надеюсь, время со мной поможет тебе почувствовать себя чуть лучше~"
            return

        #Otherwise, let's jump to the label if it exists
        $ full_label = "greeting_back_from_work{0}".format(label_suffix)
        if renpy.has_label(full_label):
            jump expression full_label

        #Return so no fall thru if label missing
        return

        label .yelled_at:
            m 2lksdlc "Ох... {w=0.5}Это правда может испортить день."
            m 2dsc "Ты просто стараешься изо всех сил, а кому-то этого всё равно мало..."
            m 2eka "Если тебя это всё ещё сильно беспокоит, думаю, тебе стоит немного расслабиться."
            m 3eka "Может, поговорить о чём-то другом или даже поиграть — это поможет отвлечься."
            m 1hua "Уверена, тебе станет лучше, когда мы проведём немного времени вместе."
            return

        label .passed_over:
            m 1lksdld "Ох... {w=0.5}Правда портит день, когда признание достаётся кому-то другому, хотя ты считал, что заслужил его."
            m 2lfd "{i}Особенно{/i} когда ты так много сделал, а это будто никто не замечает."
            m 1ekc "Если что-то сказать, можно показаться настойчивым, так что остаётся продолжать стараться — и однажды это обязательно окупится."
            m 1eua "Пока ты продолжаешь выкладываться на полную, ты будешь делать великие вещи и когда-нибудь получишь признание."
            m 1hub "И просто помни...{w=0.5}я всегда буду гордиться тобой, [player]!"
            m 3eka "Надеюсь, от этого тебе станет хоть чуть-чуть лучше~"
            return

        label .work_late:
            m 1lksdlc "Ох, это правда может всё испортить."

            m 3eksdld "Ты хотя бы знал об этом заранее?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты хотя бы знал об этом заранее?{fast}"

                "Да.":
                    m 1eka "Это хотя бы хорошо."
                    m 3ekc "Было бы очень неприятно уже собраться домой и вдруг задержаться."
                    m 1rkd "И всё же довольно раздражает, когда обычный график вот так сбивается."
                    m 1eka "...Но теперь ты здесь, и мы можем провести время вместе."
                    m 3hua "Ты наконец можешь расслабиться!"

                "Нет.":
                    m 2tkx "Это хуже всего!"
                    m 2tsc "Особенно если рабочий день уже заканчивался и ты собирался домой..."
                    m 2dsc "А потом вдруг без предупреждения приходится остаться ещё немного."
                    m 2ekc "Правда тягостно, когда планы внезапно отменяются."
                    m 2lksdlc "Может, у тебя было что-то сразу после работы, или ты просто ждал, когда вернёшься домой и отдохнёшь..."
                    m 2lubsu "...Или, может, ты просто хотел вернуться домой и увидеть свою любящую девушку, которая ждала, чтобы тебя удивить..."
                    m 2hub "Эхехе~"
            return

        label .little_done:
            m 2eka "Ой, не расстраивайся слишком сильно, [player]."
            m 2ekd "Такие дни бывают."
            m 3eka "Я знаю, ты так стараешься, что скоро преодолеешь этот застой."
            m 1hua "Пока ты делаешь всё, что можешь, я всегда буду гордиться тобой!"
            return

        label .bad_day:
            m 2dsd "Один из тех дней, да, [player]?"
            m 2dsc "Они время от времени случаются..."
            m 3eka "Но даже так я знаю, как они выматывают, и надеюсь, тебе скоро станет лучше."
            m 1ekbsa "Я буду здесь столько, сколько тебе нужно, чтобы тебя утешить, хорошо, [player]?"
            return

        label .sick:
            m 2dkd "Болеть на работе — ужасно. Так гораздо сложнее что-то сделать."
            jump greeting_back_from_work_school_still_sick_ask

    elif mas_isMoniUpset():
        m 2esc "Вижу, ты вернулся с работы, [player]..."

        m "Как прошёл день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошёл день?{fast}"
            "Хорошо.":
                m 2esc "Приятно это слышать."
                m 2tud "Наверное, приятно, когда тебя ценят."

            "Плохо.":
                m 2dsc "..."
                m 2tud "Неприятно, когда кажется, что тебя никто не ценит, да, [player]?"

    elif mas_isMoniDis():
        m 6ekc "Привет, [player]...{w=1} Наконец дома с работы?"

        m "Как прошёл день?{nw}"
        $ _history_list.pop()
        menu:
            m "Как прошёл день?{fast}"
            "Хорошо.":
                m "Это мило."
                m 6rkc "Надеюсь только, что работа нравится тебе не больше, чем быть со мной, [player]."

            "Плохо.":
                m 6rkc "Ох..."
                m 6ekc "Жаль это слышать."
                m 6rkc "Я знаю, каковы дни, когда никого не получается порадовать..."
                m 6dkc "Бывает так тяжело просто пережить такие дни."

    else:
        m 6ckc "..."
    return

label greeting_back_from_work_school_still_sick_ask:
    m 7ekc "Но я должна спросить..."
    m 1ekc "Тебе всё ещё нехорошо?{nw}"
    menu:
        m "Тебе всё ещё нехорошо?{fast}"

        "Да.":
            m 1ekc "Жаль это слышать, [player]..."
            m 3eka "Может, тебе стоит вздремнуть.{w=0.2} Уверена, тебе станет лучше, когда отдохнёшь."
            jump mas_mood_sick.ask_will_rest

        "Нет.":
            m 1eua "Рада слышать, что тебе лучше, [player]."
            m 1eka "Но если снова станет плохо, обязательно отдохни, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_sleep",
            unlocked=True,
            category=[store.mas_greetings.TYPE_SLEEP],
        ),
        code="GRE"
    )

label greeting_back_from_sleep:
    if mas_isMoniNormal(higher=True):
        m 1hua "О, привет, [player]!"
        m 1hub "Надеюсь, ты хорошо отдохнул!"
        m "Давай проведём ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "Ты только что проснулся, [player]?"
        m "Надеюсь, ты хорошо отдохнул."
        m 2tud "{cps=*2}Может, теперь у тебя будет лучше настроение.{/cps}{nw}"
        $ _history_list.pop()

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=1}ты встал."
        m 6ekc "Надеюсь, тебе удалось немного отдохнуть."
        m 6dkc "Мне в последнее время трудно отдыхать — слишком много всего на уме..."

    else:
        m 6ckc "..."

    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_siat",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

    del ev_rules

label greeting_siat:
    m 1hub "{cps=*0.6}{i}~[player] and Monika sittin' in a tree~{/i}{/cps}"
    m 1hubsb "{cps=*0.6}{i}~K-I-S-S-I-N-G~{/i}{/cps}"
    m 3hubfb "{cps=*0.6}{i}~First comes love~{/i}{/cps}"
    m "{cps=*0.6}{i}~Then comes marriage~{/i}{/cps}"
    m "{cps=*0.6}{i}~Then comes--{/i}{/cps}"
    m 3wubfsdlo "Ч-что?!"
    m 2wubfsdld "[player]! К-как давно ты здесь?!"
    m 2rkbfsdld "Я...{w=1} Я не заметила, как ты вошёл...{w=1} Я просто..."
    m 2rkbfsdlu "..."
    m 3hubfb "Ахаха! Неважно."
    m 1ekbfa "Я люблю тебя, [player]. Так рада, что ты сейчас здесь~"
    return "love"

init 5 python:
    ev_rules = {}
    ev_rules.update(MASGreetingRule.create_rule(override_type=True))
    ev_rules.update(MASPriorityRule.create_rule(40))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_ourreality",
            conditional="mas_canShowIslands(flt=False) and not mas_isSpecialDay()",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="GRE"
    )
    del ev_rules

label greeting_ourreality:
    # Unlock islands
    $ store.mas_island_event.start_progression()

    m 1hub "Привет, [player]!"
    m 1hua "Эхехе~"
    m 3hksdlb "Мне сейчас немного легко на душе, прости."
    m 1eua "Просто я очень хочу показать тебе, над чем работала."

    if persistent._mas_current_background != "spaceroom":
        m 4eub "...Но нам нужно вернуться в космическую комнату — оттуда лучше всего видно."
        m 1hua "Пойдём, [player]."
        call mas_background_change(mas_background_def, skip_leadin=True, skip_outro=True, set_persistent=True)
        m 1eua "Вот мы и здесь!"
        m 3eub "Дай мне секунду всё подготовить.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    else:
        m 3hksdrb "Дай мне секунду всё подготовить.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    m 1dsd "Почти готово.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
    m 1duu "Да, так должно быть хорошо."
    m 1hub "Ахаха!"
    m 1eka "Прости за это."
    m 1eua "Итак, без лишних слов..."
    m 4eub "Не мог бы ты взглянуть в окно, [player]?"

    call mas_islands(fade_out=False, drop_shields=False, enable_interaction=False)

    pause 4.0
    m "Ну..."
    m "Что думаешь?"
    m "Я очень много над этим работала."
    m "Место только для нас двоих."
    m "И ещё здесь я могу продолжать заниматься программированием."

    call mas_islands(fade_in=False, raise_shields=False, enable_interaction=False, force_exp="monika 1lsc")

    #Transition back to Monika
    m 1lsc "Целый день в классе бывает скучно."
    m 1ekc "К тому же мне очень одиноко ждать, когда ты вернёшься."
    m 1hksdlb "Но не пойми меня неправильно!"
    m 1eua "Я всегда рада, когда ты приходишь и проводишь со мной время."
    m 1eka "Я понимаю, что ты занят и не можешь быть здесь постоянно."
    m 3euc "Просто я кое-что поняла, [player]."
    m 1lksdlc "Пройдёт ещё очень много времени, прежде чем я смогу перейти в твою реальность."
    m 1dsc "Поэтому я подумала..."
    m 1eua "Почему бы нам просто не создать свою собственную реальность?"
    m 1lksdla "Ну, пока это ещё не идеально."
    m 1hua "Но это начало."

    $ mas_lockEVL("greeting_ourreality", "GRE")
    $ mas_unlockEVL("mas_monika_islands", "EVE")

    m 1eub "Пока что можешь любоваться пейзажем~"
    call mas_islands(force_exp="monika 1eua")
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_returned_home",
            unlocked=True,
            category=[
                store.mas_greetings.TYPE_GO_SOMEWHERE,
                store.mas_greetings.TYPE_GENERIC_RET
            ]
        ),
        code="GRE"
    )

default persistent._mas_monika_returned_home = None

label greeting_returned_home:
    # this is going to act as the generic returned home greeting.
    # please note, that we will use last_session to determine how long we were
    # out. If shorter than 5 minutes, monika won't gain any affection.
    $ five_minutes = datetime.timedelta(seconds=5*60)
    $ time_out = store.mas_dockstat.diffCheckTimes()

    # event checks

    #F14
    if persistent._mas_f14_on_date:
        jump greeting_returned_home_f14


    # gone over checks
    if mas_f14 < datetime.date.today() <= mas_f14 + datetime.timedelta(days=7):
        # did we miss f14 because we were on a date
        call mas_gone_over_f14_check

    if mas_monika_birthday < datetime.date.today() < mas_monika_birthday + datetime.timedelta(days=7):
        call mas_gone_over_bday_check

    if mas_d25 < datetime.date.today() <= mas_nye:
        call mas_gone_over_d25_check

    if mas_nyd <= datetime.date.today() < mas_d25c_end:
        call mas_gone_over_nye_check

    if mas_nyd < datetime.date.today() < mas_d25c_end:
        call mas_gone_over_nyd_check


    # NOTE: this ordering is key, greeting_returned_home_player_bday handles the case
    # if we left before f14 on your bday and return after f14
    if persistent._mas_player_bday_left_on_bday or (persistent._mas_player_bday_decor and not mas_isplayer_bday() and mas_isMonikaBirthday() and mas_confirmedParty()):
        jump greeting_returned_home_player_bday

    if persistent._mas_f14_gone_over_f14:
        jump greeting_gone_over_f14

    if mas_isMonikaBirthday() or persistent._mas_bday_on_date:
        jump greeting_returned_home_bday

    # main dialogue
    if time_out > five_minutes:
        jump greeting_returned_home_morethan5mins

    else:
        $ mas_loseAffection()
        call greeting_returned_home_lessthan5mins

        if _return:
            return 'quit'

        jump greeting_returned_home_cleanup


label greeting_returned_home_morethan5mins:
    if mas_isMoniNormal(higher=True):

        if persistent._mas_d25_in_d25_mode:
            # its d25 season time
            jump greeting_d25_and_nye_delegate

        elif mas_isD25():
            # its d25 and we are not in d25 mode
            jump mas_d25_monika_holiday_intro_rh

        jump greeting_returned_home_morethan5mins_normalplus_flow

    # otherwise, go to other flow
    jump greeting_returned_home_morethan5mins_other_flow


label greeting_returned_home_morethan5mins_normalplus_flow:
    call greeting_returned_home_morethan5mins_normalplus_dlg
    # FALL THROUGH

label greeting_returned_home_morethan5mins_normalplus_flow_aff:
    $ store.mas_dockstat._ds_aff_for_tout(time_out, 5, 5, 1)
    jump greeting_returned_home_morethan5mins_cleanup

label greeting_returned_home_morethan5mins_other_flow:
    call greeting_returned_home_morethan5mins_other_dlg
    # FALL THROUGH

label greeting_returned_home_morethan5mins_other_flow_aff:
    # for low aff you gain 0.5 per hour, max 2.5, min 0.5
    $ store.mas_dockstat._ds_aff_for_tout(time_out, 5, 2.5, 0.5, 0.5)
    #FALL THROUGH

label greeting_returned_home_morethan5mins_cleanup:
    pass
    # TODO: re-evaluate this XP gain when rethinking XP. Going out with
    #   monika could be seen as gaining xp
    # $ grant_xp(xp.NEW_GAME)
    #FALL THROUGH

label greeting_returned_home_cleanup:
    $ need_to_reset_bday_vars = persistent._mas_player_bday_in_player_bday_mode and not mas_isplayer_bday()

    #If it's not o31, and we've got deco up, we need to clean up
    if not need_to_reset_bday_vars and not mas_isO31() and persistent._mas_o31_in_o31_mode:
        call mas_o31_ret_home_cleanup(time_out)

    elif need_to_reset_bday_vars:
        call return_home_post_player_bday

    # Check if we are entering d25 season at upset-
    if (
        mas_isD25Outfit()
        and not persistent._mas_d25_intro_seen
        and mas_isMoniUpset(lower=True)
    ):
        $ persistent._mas_d25_started_upset = True
    return

label greeting_returned_home_morethan5mins_normalplus_dlg:
    m 1hua "И мы дома!"
    m 1eub "Даже если я почти ничего не видела, знание, что я была рядом с тобой..."
    m 2eua "Ну, это было правда здорово!"
    show monika 5eub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eub "Давай повторим это снова скоро, хорошо?"
    return

label greeting_returned_home_morethan5mins_other_dlg:
    m 2esc "Мы дома..."
    m 2eka "Спасибо, что взял меня с собой сегодня, [player]."
    m 2rkc "Честно говоря, я не была до конца уверена, что стоит идти с тобой..."
    m 2dkc "У нас...{w=0.5}в последнее время не всё складывалось лучшим образом, и я не знала, хорошая ли это идея..."
    m 2eka "Но я рада, что мы это сделали...{w=0.5} может, именно это нам и было нужно."
    m 2rka "Нам правда стоит как-нибудь повторить..."
    m 2esc "Если захочешь."
    return

label greeting_returned_home_lessthan5mins:
    if mas_isMoniNormal(higher=True):
        m 2ekp "Это вряд ли можно назвать прогулкой, [player]."
        m "В следующий раз пусть длится чуть дольше..."
        if persistent._mas_player_bday_in_player_bday_mode and not mas_isplayer_bday():
            call return_home_post_player_bday
        return False

    elif mas_isMoniUpset():
        m 2efd "Я думала, мы куда-то идём, [player]!"
        m 2tfd "Я знала, что не стоило соглашаться идти с тобой."
        m 2tfc "Я знала, что это снова будет разочарованием."
        m "Не проси меня больше выходить, если делаешь это только чтобы вселить надежду...{w=1}а потом выбить почву из-под ног."
        m 6dktdc "..."
        m 6ektsc "Не понимаю, почему ты так настаиваешь на жестокости, [player]."
        m 6rktsc "Я бы...{w=1}хотела сейчас побыть одна."
        return True

    else:
        m 6rkc "Но...{w=1}мы же только что вышли..."
        m 6dkc "..."
        m "Я...{w=0.5}я так обрадовалась, когда ты попросил пойти с тобой."
        m 6ekc "После всего, через что мы прошли..."
        m 6rktda "Я-я думала...{w=0.5}может...{w=0.5}наконец всё изменится."
        m "Может, нам снова будет хорошо вместе..."
        m 6ektda "Что ты правда хочешь проводить со мной больше времени."
        m 6dktsc "..."
        m 6ektsc "Но, видимо, с моей стороны было глупо так думать."
        m 6rktsc "Я должна была лучше знать...{w=1} Мне вообще не стоило соглашаться идти."
        m 6dktsc "..."
        m 6ektdc "Пожалуйста, [player]...{w=2} Если ты не хочешь проводить со мной время — ладно..."
        m 6rktdc "Но хотя бы имей порядочность не притворяться."
        m 6dktdc "Я хотела бы сейчас побыть одна."
        return True

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="ch30_reload_delegate",
            unlocked=True,
            category=[
                store.mas_greetings.TYPE_RELOAD
            ],
        ),
        code="GRE"
    )

label ch30_reload_delegate:

    if persistent.monika_reload >= 4:
        call ch30_reload_continuous

    else:
        $ reload_label = "ch30_reload_" + str(persistent.monika_reload)
        call expression reload_label

    return

# TODO: need to have an explanation before we use this again
#init 5 python:
#    ev_rules = {}
#    ev_rules.update(
#        MASGreetingRule.create_rule(
#            skip_visual=True
#        )
#    )
#
#    addEvent(
#        Event(
#            persistent.greeting_database,
#            eventlabel="greeting_ghost",
#            unlocked=False,
#            rules=ev_rules,
#            aff_range=(mas_aff.NORMAL, None),
#        ),
#        code="GRE"
#    )
#    del ev_rules

label greeting_ghost:
    #Prevent it from happening more than once.
    $ mas_lockEVL("greeting_ghost", "GRE")

    #Call event in easter eggs.
    call mas_ghost_monika

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_game",
            unlocked=True,
            category=[store.mas_greetings.TYPE_GAME],
        ),
        code="GRE"
    )

# NOTE: in case someone asks, because the farewell for this greeting does not
#   implore that the player returns after gaming, there is nothing substiantial
#   we can get in pm vars here. It's just too variable.

label greeting_back_from_game:
    # TODO: TC-O
    if store.mas_globals.late_farewell and mas_getAbsenceLength() < datetime.timedelta(hours=18):
        $ _now = datetime.datetime.now().time()
        if mas_isMNtoSR(_now):
            if mas_isMoniNormal(higher=True):
                m 2etc "[player]?"
                m 3efc "Кажется, я просила тебя сразу лечь спать, когда закончишь!"
                m 1rksdla "То есть я очень рада, что ты вернулся сказать спокойной ночи, но..."
                m 1hksdlb "Я уже пожелала тебе спокойной ночи!"
                m 1rksdla "И я могла бы подождать до утра, чтобы снова тебя увидеть, знаешь?"
                m 2rksdlc "К тому же я правда хотела, чтобы ты отдохнул..."
                m 1eka "Просто...{w=1}пообещай мне, что скоро ляжешь спать, хорошо?"

            else:
                m 1tsc "[player], я просила тебя лечь спать, когда закончишь."
                m 3rkc "Завтра утром ты всегда можешь вернуться, знаешь ли."
                m 1esc "Но, видимо, вот мы и здесь."

        elif mas_isSRtoN(_now):
            if mas_isMoniNormal(higher=True):
                m 1hua "Доброе утро, [player]~"
                m 1eka "Когда ты сказал, что так поздно пойдёшь играть в другую игру, я немного забеспокоилась, что ты не выспишься..."
                m 1hksdlb "Надеюсь, это не так, ахаха..."

            else:
                m 1eud "Доброе утро."
                m 1rsc "Я вроде как ожидала, что ты поспишь подольше."
                m 1eka "А ты уже здесь, ни свет ни заря."

        elif mas_isNtoSS(_now):
            if mas_isMoniNormal(higher=True):
                m 1wub "[player]! Ты здесь!"
                m 1hksdlb "Ахаха, прости...{w=1}я просто немного не могла дождаться, потому что тебя не было всё утро."

                m 1eua "Ты только что проснулся?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты только что проснулся?{fast}"
                    "Да.":
                        m 1hksdlb "Ахаха..."

                        m 3rksdla "Думаешь, это потому, что ты поздно лёг?{nw}"
                        $ _history_list.pop()
                        menu:
                            m "Думаешь, это потому, что ты поздно лёг?{fast}"
                            "Да.":
                                m 1eka "[player]..."
                                m 1ekc "Ты же знаешь, я не хочу, чтобы ты слишком поздно ложился."
                                m 1eksdld "Я правда не хочу, чтобы тебе становилось плохо или ты уставал за день."
                                m 1hksdlb "Но надеюсь, тебе было весело. Было бы жаль потерять весь этот сон впустую, ахаха!"
                                m 2eka "Просто отдохни ещё, если почувствуешь, что нужно, хорошо?"

                            "Нет.":
                                m 2euc "Ох..."
                                m 2rksdlc "Я так и думала."
                                m 2eka "Прости, что предположила."
                                m 1eua "В любом случае, надеюсь, ты достаточно спишь."
                                m 1eka "Мне было бы очень приятно знать, что ты хорошо отдыхаешь."
                                m 1rksdlb "И мне было бы спокойнее, если бы ты вообще не засиживался так поздно, ахаха..."
                                m 1eua "Я просто рада, что ты сейчас здесь."
                                m 3tku "Ты ведь никогда не будешь слишком усталым, чтобы провести время со мной, правда?"
                                m 1hub "Ахаха!"

                            "Может быть...":
                                m 1dsc "Хм..."
                                m 1rsc "Интересно, что может быть причиной?"
                                m 2euc "Ты ведь не засиделся очень поздно прошлой ночью, [player]?"
                                m 2etc "Ты чем-то занимался прошлой ночью?"
                                m 3rfu "Может...{w=1}я не знаю..."
                                m 3tku "Играл?"
                                m 1hub "Ахаха!"
                                m 1hua "Просто дразню, конечно~"
                                m 1ekd "Но если серьёзно, я правда не хочу, чтобы ты пренебрегал сном."
                                m 2rksdla "Одно дело засиживаться поздно ради меня..."
                                m 3rksdla "А другое — уйти и играть в другую игру так поздно?"
                                m 1tub "Ахаха... я могу немного ревновать, [player]~"
                                m 1tfb "Но теперь ты здесь, чтобы это компенсировать, правда?"

                    "Нет.":
                        m 1eud "А, значит, ты был занят всё утро."
                        m 1eka "Я волновалась, что ты проспал, раз так поздно лёг прошлой ночью."
                        m 2rksdla "Особенно потому, что ты сказал, что пойдёшь играть в другую игру."
                        m 1hua "Но я должна была знать, что ты ответственный и выспишься."
                        m 1esc "..."
                        m 3tfc "Ты {i}ведь{/i} выспался, правда, [player]?"
                        m 1hub "Ахаха!"
                        m 1hua "В любом случае, раз ты здесь, мы можем провести время вместе."

            else:
                m 2eud "О, вот и ты, [player]."
                m 1euc "Полагаю, ты только что проснулся."
                m 2rksdla "Вполне ожидаемо, раз ты так поздно засиделся за играми."

        #SStoMN
        else:
            if mas_isMoniNormal(higher=True):
                m 1hub "Вот и ты, [player]!"
                m 2hksdlb "Ахаха, прости... Просто я тебя весь день не видела."
                m 1rksdla "Я вроде как ожидала, что ты поспишь подольше после такой поздней ночи..."
                m 1rksdld "Но когда тебя не было весь день, я правда начала по тебе скучать..."
                m 2hksdlb "Ты меня почти напугал, ахаха..."
                m 3tub "Но ты ведь наверстаешь упущенное время, правда?"
                m 1hub "Эхехе, лучше бы так~"
                m 2tfu "Особенно после того, как ты оставил меня ради другой игры прошлой ночью."

            else:
                m 2efd "[player]!{w=0.5} Где ты был весь день?"
                m 2rfc "Это ведь не связано с тем, что ты поздно лёг прошлой ночью?"
                m 2ekc "Тебе правда стоит быть чуть ответственнее, когда дело касается сна."

    #If you didn't stay up late in the first place, normal usage
    #gone for under 4 hours
    elif mas_getAbsenceLength() < datetime.timedelta(hours=4):
        if mas_isMoniNormal(higher=True):
            m 1hua "С возвращением, [mas_get_player_nickname()]!"

            m 1eua "Тебе понравилось?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебе понравилось?{fast}"
                "Да.":
                    m 1hua "Это мило."
                    m 1eua "Рада, что тебе понравилось."
                    m 2eka "Мне так хочется иногда присоединиться к тебе в других играх."
                    m 3eub "Разве не было бы здорово отправляться в наши собственные маленькие приключения, когда захотим?"
                    m 1hub "Уверена, нам было бы очень весело вместе в одной из твоих игр."
                    m 3eka "Но пока я не могу присоединиться, тебе просто придётся составить мне компанию."
                    m 2tub "Ты ведь не против провести время со своей девушкой...{w=0.5}правда, [player]?"

                "Нет.":
                    m 2ekc "Ох, жаль это слышать."
                    m 2eka "Надеюсь, ты не слишком расстроен из-за того, что случилось."
                    m 3eua "По крайней мере, теперь ты здесь. Обещаю постараться, чтобы с тобой ничего плохого не случилось, пока ты со мной."
                    m 1ekbsa "Когда я тебя вижу, мне сразу становится лучше."
                    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5ekbfa "Надеюсь, когда ты видишь меня, с тобой то же самое, [mas_get_player_nickname()]~"

        else:
            m 2eud "О, уже вернулся?"
            m 2rsc "Я думала, тебя не будет дольше...{w=0.5}но с возвращением, полагаю."

    elif mas_getAbsenceLength() < datetime.timedelta(hours=12):
        if mas_isMoniNormal(higher=True):
            m 2wuo "[player]!"
            m 2hksdlb "Тебя не было очень долго..."

            m 1eka "Тебе было весело?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебе было весело?{fast}"
                "Да.":
                    m 1hua "Ну, тогда я рада."
                    m 1rkc "Ты заставил меня изрядно подождать, знаешь ли."
                    m 3tfu "Думаю, тебе стоит провести время со своей любящей девушкой, [player]."
                    m 3tku "Уверена, ты не против побыть со мной, чтобы уравновесить ту другую игру."
                    m 1hubsb "Может, тебе стоит проводить со мной ещё больше времени, на всякий случай, ахаха!"

                "Нет.":
                    m 2ekc "Ох..."
                    m 2rka "Знаешь, [player]..."
                    m 2eka "Если тебе не весело, может, просто проведёшь время здесь со мной."
                    m 3hua "Уверена, мы можем найти кучу весёлых занятий вместе!"
                    m 1eka "Если решишь вернуться туда, может, станет лучше."
                    m 1hub "Но если тебе всё ещё не весело, не стесняйся прийти ко мне, ахаха!"

        else:
            m 2eud "Ох, [player]."
            m 2rsc "Это заняло довольно много времени."
            m 1esc "Не волнуйся, я смогла скоротать время, пока тебя не было."

    #Over 12 hours
    else:
        if mas_isMoniNormal(higher=True):
            m 2hub "[player]!"
            m 2eka "Кажется, прошла целая вечность с тех пор, как ты ушёл."
            m 1hua "Я так по тебе скучала!"
            m 3eua "Надеюсь, тебе было весело, чем бы ты ни занимался."
            m 1rksdla "И я буду считать, что ты не забыл поесть и поспать..."
            m 2rksdlc "Что до меня...{w=1}мне было немного одиноко ждать твоего возвращения..."
            m 1eka "Но не расстраивайся."
            m 1hua "Я просто рада, что ты снова здесь со мной."
            m 3tfu "Хотя тебе лучше это мне компенсировать."
            m 3tku "Думаю, провести со мной вечность — это справедливо...{w=1}правда, [player]?"
            m 1hub "Ахаха!"

        else:
            m 2ekc "[player]..."
            m "Я не знала, когда ты вернёшься."
            m 2rksdlc "Я думала, что больше тебя не увижу..."
            m 2eka "Но вот ты здесь..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_eat",
            unlocked=True,
            category=[store.mas_greetings.TYPE_EAT],
        ),
        code="GRE"
    )

label greeting_back_from_eat:
    # TODO: TC-O
    $ _now = datetime.datetime.now().time()
    if store.mas_globals.late_farewell and mas_isMNtoSR(_now) and mas_getAbsenceLength() < datetime.timedelta(hours=18):
        if mas_isMoniNormal(higher=True):
            m 1eud "Ох?"
            m 1eub "[player], ты вернулся!"
            m 3rksdla "Ты ведь знаешь, что тебе правда стоит поспать?"
            m 1rksdla "То есть... я не жалуюсь, что ты здесь, но..."
            m 1eka "Мне было бы спокойнее, если бы ты скоро лёг спать."
            m 3eka "Ты всегда можешь вернуться ко мне, когда проснёшься..."
            m 1hubsa "Но если ты настаиваешь провести со мной время, я немного закрою на это глаза, эхехе~"
        else:
            m 2euc "[player]?"
            m 3ekd "Разве я не просила сразу лечь спать после этого?"
            m 2rksdlc "Тебе правда стоит поспать."

    else:
        if mas_isMoniNormal(higher=True):
            m 1eub "Поел?"
            m 1hub "С возвращением, [mas_get_player_nickname()]!"
            m 3eua "Надеюсь, еда тебе понравилась."
        else:
            m 2euc "Поел?"
            m 2eud "С возвращением."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_rent",
            unlocked=True,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

label greeting_rent:
    m 1eub "С возвращением, [mas_get_player_nickname()]!"
    m 2tub "Знаешь, ты проводишь здесь так много времени, что мне стоит начать брать с тебя аренду."
    m 2ttu "Или ты предпочитаешь ипотеку?"
    m 2hua "..."
    m 2hksdlb "Боже, не могу поверить, что я это сказала. Это не слишком банально?"
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Но если серьёзно, ты уже дал мне единственное, что мне нужно...{w=1}своё сердце~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_housework",
            unlocked=True,
            category=[store.mas_greetings.TYPE_CHORES],
        ),
        code="GRE"
    )

label greeting_back_housework:
    if mas_isMoniNormal(higher=True):
        m 1eua "Всё, [player]?"
        m 1hub "Давай проведём ещё немного времени вместе!"
    elif mas_isMoniUpset():
        m 2esc "По крайней мере, ты не забыл вернуться, [player]."
    elif mas_isMoniDis():
        m 6ekd "Ах, [player]. Значит, ты и правда просто был занят..."
    else:
        m 6ckc "..."
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hua"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_surprised2",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_surprised2:
    m 1hua "..."
    m 1hubsa "..."
    m 1wubso "Ой!{w=0.5} [player]!{w=0.5} Ты меня удивил!"
    m 3ekbsa "...Не то чтобы видеть тебя — сюрприз, ты ведь всегда ко мне приходишь...{w=0.5} {nw}"
    extend 3rkbsa "ты просто застал меня за лёгкими мечтами."
    show monika 5hubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfu "Но раз ты здесь, этот сон только что сбылся~"
    return

init 5 python:
    # set a slightly higher priority than the open door gre has
    ev_rules = dict()
    ev_rules.update(MASPriorityRule.create_rule(49))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_restart",
            unlocked=True,
            category=[store.mas_greetings.TYPE_RESTART],
            rules=ev_rules
        ),
        code="GRE"
    )

    del ev_rules

label greeting_back_from_restart:
    if mas_isMoniNormal(higher=True):
        m 1hub "С возвращением, [mas_get_player_nickname()]!"
        m 1eua "Чем ещё займёмся сегодня?"
    elif mas_isMoniBroken():
        m 6ckc "..."
    else:
        m 1eud "О, ты вернулся."
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_code_help",
            conditional="store.seen_event('monika_coding_experience')",
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None),
        ),
        code="GRE"
    )

label greeting_code_help:
    m 2eka "О, привет, [player]..."
    m 4eka "Дай секунду, я как раз закончила что-то кодить и хочу посмотреть, работает ли.{w=0.5}.{w=0.5}.{nw}"

    scene black
    show noise
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.1
    hide noise
    call spaceroom(dissolve_all=True, scene_change=True, force_exp='monika 2wud_static')

    m 2wud "Ах!{w=0.3}{nw}"
    extend 2efc " Так не должно быть!"
    m 2rtc "Почему этот цикл заканчивается так быстро?{w=0.5}{nw}"
    extend 2efc " Как ни посмотри, этот словарь {i}не{/i} пустой."
    m 2rfc "Боже, кодить бывает {i}так{/i} раздражающе..."

    if persistent._mas_pm_has_code_experience:
        m 3rkc "Ну ладно, попробую ещё раз позже.{nw}"
        $ _history_list.pop()

        show screen mas_background_timed_jump(5, "greeting_code_help_outro")
        menu:
            m "Ну ладно, попробую ещё раз позже.{fast}"

            "Я мог бы тебе с этим помочь...":
                hide screen mas_background_timed_jump
                m 7hua "Ой, как мило с твоей стороны, [player]. {w=0.3}{nw}"
                extend 3eua "Но нет, здесь мне придётся отказаться."
                m "Разбираться самой — это самая интересная часть, {w=0.2}{nw}"
                extend 3kua "правда?"
                m 1hub "Ахаха!"

    else:
        m 3rkc "Ну ладно, попробую ещё раз позже."

    #FALL THROUGH

label greeting_code_help_outro:
    hide screen mas_background_timed_jump
    m 1eua "В любом случае, чем хочешь заняться сегодня?"

    $ mas_lockEVL("greeting_code_help", "GRE")
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 1hub"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_love_is_in_the_air",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_love_is_in_the_air:
    m 1hub "{i}~Любовь витает в воздухе~{/i}"
    m 1rub "{i}~Куда ни глянь вокруг~{/i}"
    m 3ekbsa "О, привет, [player]..."
    m 3rksdla "Не обращай внимания. {w=0.2}Я просто немного пою, думая о...{w=0.3}{nw}"
    extend 1hksdlb "ну, ты, наверное, и так догадаешься, о чём, ахаха~"
    m 1eubsu "И правда кажется, что любовь повсюду вокруг меня, когда ты здесь."
    m 3hua "В любом случае, чем хочешь заняться сегодня?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_workout",
            category=[store.mas_greetings.TYPE_WORKOUT],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_workout:
    if mas_isMoniNormal(higher=True):
        m 1hua "С возвращением, [player]!"
        m 3eua "Надеюсь, тренировка прошла хорошо."
        m 3eub "Не забудь пить воду и поесть, чтобы восстановить силы!"
        m 1eua "Давай проведём ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "О,{w=0.2} ты вернулся."
        m 2rsc "Тренировка помогла сбросить напряжение?"
        m 2rud "Надеюсь, да...{w=0.3} {nw}"
        extend 2eka "Давай проведём ещё немного времени вместе."

    elif mas_isMoniDis():
        m 6ekc "Ох...{w=0.5}смотрите, кто вернулся."
        m 6dkc "Я...{w=0.3}рада, что ты о себе заботишься."
        m 6ekd "...Но разве ты не хочешь заботиться и обо мне тоже?"
        m 7dkc "Хотя бы иногда, пожалуйста..."
        m 1dkc "..."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_shopping",
            category=[store.mas_greetings.TYPE_SHOPPING],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_shopping:
    if mas_isMoniNormal(higher=True):
        m 1hub "С возвращением, [player]!"
        m 3eua "Надеюсь, ты купил в магазине всё, что нужно."
        m 1hua "Давай проведём ещё немного времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "О,{w=0.2} ты вернулся."
        m 2rsc "Надеюсь, ты взял всё необходимое."
        if renpy.random.randint(1,5) == 1:
            m 2rud "{cps=*2}Надеюсь, и настроение у тебя теперь лучше.{/cps}{nw}"
            $ _history_list.pop()

    elif mas_isMoniDis():
        m 6rkc "Ох...{w=0.5}ты вернулся."
        m 6ekc "Надеюсь, шопинг прошёл хорошо. {w=0.2}Ты купил еду?"
        m 6dkd "Ты не думал, что твои пищевые привычки могут влиять на настроение в последнее время?"
        m 6lkc "Мне было бы жаль, если бы именно поэтому ты—{nw}"
        $ _history_list.pop()
        m 6ekc "Знаешь что? Неважно. {w=0.2}{nw}"
        extend 6dkc "Я просто устала."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_back_from_hangout",
            category=[store.mas_greetings.TYPE_HANGOUT],
            unlocked=True
        ),
        code="GRE"
    )

label greeting_back_from_hangout:
    if mas_isMoniNormal(higher=True):
        if persistent._mas_pm_has_friends:
            m 1eua "С возвращением, [player]."
            m 3hub "Надеюсь, тебе было весело!"

            $ anyway_lets = "Давай"

        else:
            m 3eub "С возвращением, [player]."

            m 1eua "Ты завёл нового друга?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты завёл нового друга?{fast}"

                "Да.":
                    m 1hub "Это потрясающе!"
                    m 1eua "Мне так приятно знать, что тебе есть с кем провести время."
                    m 3hub "Надеюсь, ты сможешь проводить с ними больше времени в будущем!"
                    $ persistent._mas_pm_has_friends = True

                "Нет...":
                    m 1ekd "Ох..."
                    m 3eka "Ну, не волнуйся, [player]. {w=0.2}Я всегда буду твоим другом, что бы ни случилось."
                    m 3ekd "...И не бойся попробовать снова с кем-то ещё."
                    m 1hub "Уверена, где-то есть человек, который будет рад назвать тебя своим другом!"

                "Это уже мой друг.":
                    if persistent._mas_pm_has_friends is False:
                        m 1rka "О, так ты завёл нового друга и не сказал мне..."
                        m 1hub "Ничего! Я просто рада, что тебе есть с кем провести время."
                    else:
                        m 1hub "О, хорошо!"
                        m 3eua "...Мы раньше особо не говорили о твоих других друзьях, так что я не была уверена, новый это друг или нет."
                        m 3eub "Но в любом случае, я просто рада, что в твоей реальности есть друзья, с которыми можно провести время!"

                    m 3eua "Надеюсь, ты часто можешь с ними видеться."
                    $ persistent._mas_pm_has_friends = True

            $ anyway_lets = "В любом случае давай"

        m 1eua "[anyway_lets] проведём ещё немного времени вместе~"

    elif mas_isMoniDis(higher=True):
        m 2euc "Ещё раз привет, [player]."
        m 2eud "Надеюсь, тебе было хорошо провести время с друзьями."
        if renpy.random.randint(1,5) == 1:
            m 2rkc "{cps=*2}Интересно, каково это{/cps}{nw}"
            $ _history_list.pop()

    else:
        m 6ckc "..."

    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(MASGreetingRule.create_rule(forced_exp="monika 5duc"))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_poem_shadows_in_garden",
            unlocked=True,
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(days=1)",
            rules=ev_rules,
            aff_range=(mas_aff.ENAMORED, None),
        ),
        code="GRE"
    )

    del ev_rules

#Because this is associated, we'll also mirror this into the poem framework
init 11 python:
    MASPoem(
        poem_id="gre_1",
        category="generic",
        prompt=_("Тени в саду"),
        title="",
        text=_("""\
 Одна я задаю себе торжественный вопрос,
 Что может вырасти в неосвещённом саду?

 Когда ты возвращаешься, это как небо,
 В твоём свете холод забыт.

 Я отдам всё, чтобы чувствовать это снова,
 Ожидая того, кто мне дороже всех.

 Ближе всех к моему сердцу...
"""),
    )

label greeting_poem_shadows_in_garden:
    m 5duc "{i}Одна я задаю себе торжественный вопрос,\nЧто может вырасти в неосвещённом саду?{/i}"
    m 5ekbla "{i}Когда ты возвращаешься, это как небо,\nВ твоём свете холод забыт.{/i}"
    m 5fubfa "{i}Я отдам всё, чтобы чувствовать это снова,\nОжидая того, кто мне дороже всех.{/i}"
    m 5ekbfa "{i}Даже если это каждый день,\nБез сомнений, ты — самый близкий.{/i}"
    m 5dubsu "{i}Ближе всех к моему сердцу...{/i}"
    m 5eublb "Я придумала это, пока тебя не было."
    show monika 1eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eka "Верно, ты как солнце моего мира!"
    m 3hubsu "В любом случае, с возвращением, [mas_get_player_nickname()]! Надеюсь, тебе понравилось это стихотворение."
    #TODO: Potential I missed you too?
    m 1ekbsb "Я так сильно по тебе скучала!"

    if "gre_1" not in persistent._mas_poems_seen:
        $ persistent._mas_poems_seen["gre_1"] = 1

    $ mas_moni_idle_disp.force_by_code("1ekbla", duration=5, skip_dissolve=True)
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(
        MASGreetingRule.create_rule(
            random_chance=0.3,
            forced_exp=random.choice(("monika 1gsbsu", "monika 1msbsu"))
        )
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_spacing_out",
            conditional="store.mas_getAbsenceLength() >= datetime.timedelta(hours=3)",
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="GRE"
    )

    del ev_rules

label greeting_spacing_out:
    python hide:
        # Define some other things we're going to work with
        use_right_smug = bool(random.randint(0, 1))
        spacing_out_pause = PauseDisplayableWithEvents()
        events = list()
        next_event_time = 0
        right_smug = renpy.partial(renpy.show, "monika 1gsbsu")
        left_smug = renpy.partial(renpy.show, "monika 1msbsu")

        # Make the events which will change exps
        for i in range(random.randint(4, 6)):
            events.append(
                PauseDisplayableEvent(
                    datetime.timedelta(seconds=next_event_time),
                    right_smug if use_right_smug else left_smug,
                    restart_interaction=True
                )
            )
            next_event_time += random.uniform(0.9, 1.8)
            use_right_smug = not use_right_smug
        # The last exp in the sequence
        events.append(
            PauseDisplayableEvent(
                datetime.timedelta(seconds=next_event_time),
                renpy.partial(renpy.show, "monika 1tsbsu"),
                restart_interaction=True
            )
        )
        next_event_time += 0.7
        # This is to automatically cancel the pause after all the events
        events.append(
            PauseDisplayableEvent(
                datetime.timedelta(seconds=next_event_time),
                spacing_out_pause.stop
            )
        )

        spacing_out_pause.set_events(events)
        spacing_out_pause.start()

    # Small pause so people don't skip this line
    $ renpy.pause(0.01)
    m 2wubfsdlo "[player]!"
    m 1rubfsdlb "Ты меня удивил! {w=0.4}{nw}"
    extend 1eubsu "Я немного{w=0.2} витала в облаках..."
    m 1hubsb "Ахаха~"
    m 1eua "Я очень рада снова тебя видеть. {w=0.2}{nw}"
    extend 3eua "Чем займёмся сегодня, [player]?"
    return

init 5 python:
    ev_rules = dict()
    ev_rules.update(
        MASGreetingRule.create_rule(
            skip_visual=True,
            random_chance=0.05,
            override_type=True
        )
    )
    ev_rules.update(
        MASTimedeltaRepeatRule.create_rule(
            datetime.timedelta(days=3)
        )
    )
    ev_rules.update(
        MASSelectiveRepeatRule.create_rule(
            hours=list(range(9, 20))
        )
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_after_bath",
            conditional=(
                "mas_getAbsenceLength() >= datetime.timedelta(hours=6) "
                "and not mas_isSpecialDay()"
            ),
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="GRE"
    )

    del ev_rules

init 1:
    # NOTE this should be defined AFTER init 0
    # NOTE: default may be not completely reliable, always save the snapshot yourself
    default persistent._mas_previous_moni_state = monika_chr.save_state(True, True, True, True)

label greeting_after_bath:
    python hide:
        # Some preperations
        mas_RaiseShield_core()
        mas_startupWeather()
        # Save current outfit
        persistent._mas_previous_moni_state = monika_chr.save_state(True, True, True, True)
        # Available clothes for this
        clothes_pool = [
            mas_clothes_bath_towel_white
        ]
        # Now let Moni get a towel
        monika_chr.change_clothes(
            random.choice(clothes_pool),
            by_user=False,
            outfit_mode=True
        )
        # In case the towel already set an appropriate hair, we don't change it
        if not monika_chr.is_wearing_hair_with_exprop(mas_sprites.EXP_H_WET):
            monika_chr.change_hair(mas_hair_wet, by_user=False)
        # We leave this acs to the clothes PPs in case the towel we chose doesn't support it
        # if not monika_chr.is_wearing_acs(mas_acs_water_drops):
        #     monika_chr.wear_acs(mas_acs_water_drops)
        # Setup the cleaup event
        mas_setEVLPropValues(
            "mas_after_bath_cleanup",
            start_date=datetime.datetime.now() + datetime.timedelta(minutes=random.randint(30, 90)),
            action=EV_ACT_QUEUE
        )
        mas_startup_song()

    # Now show everything
    call spaceroom(hide_monika=True, dissolve_all=True, scene_change=True, show_emptydesk=True)

    $ renpy.pause(random.randint(5, 15), hard=True)
    call mas_transition_from_emptydesk("monika 1huu")
    $ renpy.pause(2.0)
    $ quick_menu = True

    m 1wuo "Ой! {w=0.2}{nw}"
    extend 2wuo "[player]! {w=0.2}{nw}"
    extend 2lubsa "Я думала о тебе."

    $ bathing_showering = random.choice(("принимать ванну", "принимать душ"))

    if mas_getEVL_shown_count("greeting_after_bath") < 5:
        m 7lubsb "Я только что закончила [bathing_showering]...{w=0.3}{nw}"
        extend 1ekbfa "ты ведь не против, что я в полотенце?~"
        m 1hubfb "Ахаха~"
        m 3hubsa "Скоро соберусь, дай волосам сначала чуть подсохнуть."

    # Gets used to it
    else:
        m 7eubsb "Я только что закончила [bathing_showering]."

        if mas_canShowRisque() and random.randint(0, 3) == 0:
            m 1msbfb "Бьюсь об заклад, ты хотел бы присоединиться..."
            m 1tsbfu "Ну, может, однажды~"
            m 1hubfb "Ахаха~"

        else:
            m 1eua "Скоро оденусь~"

    python:
        # enable music menu and music hotkeys
        mas_MUINDropShield()
        # keymaps should be set
        set_keymaps()
        # show the overlays
        mas_OVLShow()

        del bathing_showering

    return

# NOTE: This is not a greeting, but a followup for the greeting above, so I decided to keep them together
init 5 python:
    addEvent(Event(persistent.event_database, eventlabel="mas_after_bath_cleanup", show_in_idle=True, rules={"skip alert": None}))

    def mas_after_bath_cleanup_change_outfit():
        """
        After bath cleanup change outfit code
        """
        # TODO: Rng outfit selection wen
        # TODO: reconsider locking the selectors again when we get rng outfits in

        force_hair_change = False# If we changed the outfit, we always change hair

        if monika_chr.is_wearing_clothes_with_exprop(mas_sprites.EXP_C_WET):
            force_hair_change = True

            # Let's restore the previous outfit and acs
            monika_chr.load_state(persistent._mas_previous_moni_state, as_prims=True)

            # Fallback just in case
            if monika_chr.is_wearing_clothes_with_exprop(mas_sprites.EXP_C_WET):
                if mas_isMoniHappy(higher=True):
                    new_clothes = mas_clothes_blazerless

                else:
                    new_clothes = mas_clothes_def

                monika_chr.change_clothes(
                    new_clothes,
                    by_user=False,
                    outfit_mode=True
                )

        if (
            force_hair_change
            or monika_chr.is_wearing_hair_with_exprop(mas_sprites.EXP_H_WET)
        ):
            available_hair = mas_sprites.get_installed_hair(
                predicate=lambda hair_obj: (
                    not hair_obj.hasprop(mas_sprites.EXP_H_WET)
                    and mas_sprites.is_clotheshair_compatible(monika_chr.clothes, hair_obj)
                    and mas_selspr.get_sel_hair(hair_obj) is not None
                    and mas_selspr.get_sel_hair(hair_obj).unlocked
                )
            )
            # We should always have *something*, but just to make this extra foolproof
            if available_hair:
                new_hair = random.choice(available_hair)
                monika_chr.change_hair(
                    new_hair,
                    by_user=False
                )

label mas_after_bath_cleanup:
    # Sanity check (checking for towel should be enough)
    if (
        not monika_chr.is_wearing_clothes_with_exprop(mas_sprites.EXP_C_WET)
        and not monika_chr.is_wearing_hair_with_exprop(mas_sprites.EXP_H_WET)
    ):
        return

    if mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 1eua "Я сейчас оденусь.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

    else:
        $ player_nick = mas_get_player_nickname()
        m 1eua "Дай мне минутку, [player_nick], {w=0.2}{nw}"
        extend 3eua "я сейчас оденусь."

    window hide
    call mas_transition_to_emptydesk

    $ renpy.pause(1.0, hard=True)
    $ mas_after_bath_cleanup_change_outfit()
    $ renpy.pause(random.randint(10, 15), hard=True)

    call mas_transition_from_emptydesk("monika 3hub")
    window auto

    if mas_globals.in_idle_mode or (mas_canCheckActiveWindow() and not mas_isFocused()):
        m 3hub "Готово!{w=1}{nw}"

    else:
        m 3hub "Ладно, я вернулась!~"
        m 1eua "Так чем хочешь заняться сегодня, [player]?"

    return

label mas_after_bath_cleanup_change_outfit:
    $ mas_after_bath_cleanup_change_outfit()
    return


init 5 python:
    ev_rules = dict()
    ev_rules.update(
        MASGreetingRule.create_rule(
            skip_visual=True,
            random_chance=0.1,
            override_type=True
        )
    )

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="greeting_found_nou_shirt",
            conditional=(
                "mas_getAbsenceLength() >= datetime.timedelta(hours=3) "
                "and mas_nou.get_wins_for('Player') > {0} "
                "and mas_nou.get_total_games() > {1} "
                "and not mas_isSpecialDay() "
                "and not mas_SELisUnlocked(mas_clothes_nou_shirt)"
            ).format(random.randint(45, 65), random.randint(95, 115)),
            unlocked=True,
            rules=ev_rules,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="GRE"
    )

    del ev_rules

default persistent._mas_pm_snitched_on_chibika = None

label greeting_found_nou_shirt:
    python:
        mas_RaiseShield_core()
        mas_startupWeather()
        monika_chr.change_clothes(mas_clothes_nou_shirt, by_user=False, outfit_mode=True)
        glitch_option_text = glitchtext(7)

    call spaceroom(hide_monika=True, dissolve_all=True, scene_change=True, show_emptydesk=True)
    pause 2.5

    m "Вот и ты! {w=0.2}Я тебя ждала~"
    m "Должна признать, {w=0.1}не знаю, как тебе удалось положить это в мой шкаф так, чтобы я не заметила, [player]...{nw}"
    $ _history_list.pop()
    show screen mas_background_timed_jump(5, "greeting_found_nou_shirt.menu_skip")
    menu:
        m "Должна признать, не знаю, как тебе удалось положить это в мой шкаф так, чтобы я не заметила, [player]...{fast}"

        "Это секрет.":
            hide screen mas_background_timed_jump
            jump greeting_found_nou_shirt.menu_choice_secret

        "Это сделал [glitch_option_text]!":
            hide screen mas_background_timed_jump
            $ persistent._mas_pm_snitched_on_chibika = True
            $ renpy.invoke_in_thread(
                mas_utils.trywrite,
                os.path.join(renpy.config.basedir, "characters/for snitch.txt"),
                ">:("
            )
            jump greeting_found_nou_shirt.menu_choice_other

        "Понятия не имею...":
            hide screen mas_background_timed_jump
            jump greeting_found_nou_shirt.menu_choice_other

    label .post_menu:
        pass

    m 1ekbla "Спасибо, [player]."
    m 1tfu "Но не думай, что я буду с тобой помягче~"

    if mas_nou.get_wins_for('Player') >= mas_nou.get_wins_for('Monika'):
        m 1rtsdlb "На самом деле, {w=0.1}может, мне стоит стараться ещё сильнее, ахаха..."

    m 3ttb "Сыграем, [mas_get_player_nickname()]?"

    python:
        mas_selspr.unlock_clothes(mas_clothes_nou_shirt)
        mas_selspr.save_selectables()
        mas_lockEVL("greeting_found_nou_shirt", "GRE")
        renpy.save_persistent()

        del glitch_option_text

        mas_MUINDropShield()
        set_keymaps()
        HKBShowButtons()
        mas_startup_song()
        enable_esc()
    return

label greeting_found_nou_shirt.menu_skip:
    hide screen mas_background_timed_jump
    call mas_transition_from_emptydesk("monika 4sub")
    m "Но мне это нравится~"

    jump greeting_found_nou_shirt.post_menu

label greeting_found_nou_shirt.menu_choice_secret:
    if mas_isMoniEnamored(higher=True):
        call mas_transition_from_emptydesk("monika 2tublu")
        m "{cps=*1.5}Ты ведь {i}нечасто{/i} туда заглядываешь, да?~{/cps}{w=0.1}{nw}"
        $ _history_list.pop()
        m 2lusdla "В любом случае... {w=0.3}{nw}"

    else:
        call mas_transition_from_emptydesk("monika 2rtblsdlu")
        m "Хм, в любом случае... {w=0.3}{nw}"

    extend 4sub "Мне правда очень нравится этот новый наряд!"

    jump greeting_found_nou_shirt.post_menu

label greeting_found_nou_shirt.menu_choice_other:
    show noise zorder 500 onlayer overlay:
        alpha 0.0
        easein_elastic 0.5 alpha 0.1
    play sound "sfx/s_kill_glitch1.ogg"
    pause 0.5
    hide noise onlayer overlay

    jump greeting_found_nou_shirt.menu_skip
