# --- FILE MAP ---
# script-compliments.rpy — комплименты Монике
#
# Меню похвалы. Первый раз — длинная ветка (_2), потом короткие повторы (_3)
# с рандомными quip. Есть варианты, которые affection отнимают (колкость).
#
# Store: mas_compliments  |  код события CMP
# Labels: mas_compliment_beautiful / _eyes / _chess / _pong / _sweet …
# Переводить: prompt, реплики, пункты menu, списки _quips.
# ---

# Module for complimenting Monika
#
# Compliments work by using the "unlocked" logic.
# That means that only those compliments that have their
# unlocked property set to True
# At the beginning, when creating the menu, the compliments
# database checks the conditionals of the compliments
# and unlocks them.
# We only display the compliments that are
# unlocked, not hidden, within affection range,
# and don't have a conditional or have a conditional that evaluates to True.
# If you don't want a dynamic conditional for your compliment, you'd need
# to use an external event to unlock it from somewhere else.


# dict of tples containing the stories event data
default persistent._mas_compliments_database = dict()


# store containing compliment-related things
init 3 python in mas_compliments:

    compliment_database = dict()

init 22 python in mas_compliments:
    import store
    import random
    import datetime

    thanking_quips = [
        _("Ты такой милый, [player]."),
        _("Спасибо, что сказал это ещё раз, [player]!"),
        _("Спасибо, что сказал это снова, [mas_get_player_nickname()]!"),
        _("Ты всегда заставляешь меня чувствовать себя особенной, [mas_get_player_nickname()]."),
        _("Оуу, [player]~"),
        _("Спасибо, [mas_get_player_nickname()]!"),
        _("Ты всегда меня так хвалишь, [player].")
    ]

    __last_called_callback = None
    __wait_time = 55.0
    # set this here in case of a crash mid-compliment
    thanks_quip = renpy.substitute(renpy.random.choice(thanking_quips))

    def __set_wait_time():
        """
        Sets new wait time
        """
        global __wait_time
        __wait_time = random.uniform(40.0, 70.0)

    def compliment_delegate_callback():
        """
        A callback for the compliments delegate label
        """
        global thanks_quip, __last_called_callback

        thanks_quip = renpy.substitute(renpy.random.choice(thanking_quips))

        _now = datetime.datetime.now()
        if __last_called_callback is not None:
            diff = (_now - __last_called_callback).total_seconds()
            if diff <= __wait_time:
                __last_called_callback = _now
                __set_wait_time()
                return

        __last_called_callback = _now
        __set_wait_time()

        store.mas_gainAffection()

# entry point for compliments flow
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_compliments",
            category=['моника', 'романтика'],
            prompt="Я хочу тебе кое-что сказать...",
            pool=True,
            unlocked=True
        )
    )

label monika_compliments:
    python:
        # Unlock any compliments that need to be unlocked
        Event.checkEvents(mas_compliments.compliment_database)

        # build menu list
        compliments_menu_items = [
            (ev.prompt, ev_label, not seen_event(ev_label), False)
            for ev_label, ev in mas_compliments.compliment_database.iteritems()
            if (
                Event._filterEvent(ev, unlocked=True, aff=mas_curr_affection, flag_ban=EV_FLAG_HFM)
                and ev.checkConditional()
            )
        ]

        # also sort this list
        compliments_menu_items.sort()

        # final quit item
        final_item = ("Ладно, неважно.", False, False, False, 20)

    # move Monika to the left
    show monika at t21

    # call scrollable pane
    call screen mas_gen_scrollable_menu(compliments_menu_items, mas_ui.SCROLLABLE_MENU_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

    # return value? then push
    if _return:
        $ mas_compliments.compliment_delegate_callback()
        $ MASEventList.push(_return)
        # move her back to center
        show monika at t11

    else:
        return "prompt"

    return

# Compliments start here
init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_beautiful",
            prompt="Ты красивая!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_beautiful:
    if not renpy.seen_label("mas_compliment_beautiful_2"):
        call mas_compliment_beautiful_2
    else:
        call mas_compliment_beautiful_3
    return

label mas_compliment_beautiful_2:
    m 1lubsb "Ох, боже, [player]..."
    m 1hubfb "Спасибо за комплимент."
    m 2ekbfb "Я обожаю, когда ты говоришь такое~"
    m 1ekbfa "Для меня ты самый красивый человек на свете!"
    menu:
        "Для меня ты тоже самая красивая.":
            $ mas_gainAffection(5, bypass=True)
            m 1hub "Эхехе~"
            m "Я так сильно люблю тебя, [player]!"
            # manually handle the "love" return key
            $ mas_ILY()

        "Ты в моей первой десятке.":
            $ mas_loseAffection()
            m 3hksdrb "...?"
            m 2lsc "Ну... спасибо, наверное..."

        "Спасибо.":
            pass
    return

label mas_compliment_beautiful_3:
    python:
        beautiful_quips = [
            _("Никогда не забывай, что для меня ты самый красивый человек на свете."),
            _("Ничто не сравнится с красотой твоего сердца."),
        ]
        beautiful_quip = random.choice(beautiful_quips)
    m 1hubsa "Эхехе~"
    m 1ekbfa "[mas_compliments.thanks_quip]"
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "[beautiful_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_eyes",
            prompt="Я обожаю твои глаза!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_eyes:
    if not renpy.seen_label("mas_compliment_eyes_2"):
        call mas_compliment_eyes_2
    else:
        call mas_compliment_eyes_3
    return

label mas_compliment_eyes_2:
    m 1subsb "Ох, [player]..."
    m 1tubfb "Я и так горжусь своими глазами, но когда ты говоришь такое..."
    m 1dkbfa "У меня прямо сердце трепещет~"
    menu:
        "Я ничего не могу с собой поделать, твои глаза слишком красивые.":
            $ mas_gainAffection(5, bypass=True)
            m 1hub "Ахаха!"
            m "Только не льсти мне слишком сильно, ладно?"
            show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hub "А то я начну сходить с ума..."

        "Они правда гипнотизируют.":
            $ mas_gainAffection(1, bypass=True)
            m "Ахаха~"

        "Они цвета травы!":
            $ mas_gainAffection(0.5, bypass=True) # at least you tried
            m 2lksdrb "...Не совсем такое сравнение я бы использовала, но спасибо!"
    return

label mas_compliment_eyes_3:
    python:
        eyes_quips = [
            _("Смотри в мои глаза сколько угодно~"),
            _("Я не могу дождаться, когда посмотрю в твои прекрасные глаза."),
            _("Я бы смотрела в твои глаза часами, если бы могла."),
        ]
        eyes_quip = random.choice(eyes_quips)

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 2ekbfb "[eyes_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_goodmood",
            prompt="Ты всегда поднимаешь мне настроение!",
            unlocked=False,
            conditional="store.mas_anni.pastSixMonths()",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_goodmood:
    if not renpy.seen_label("mas_compliment_goodmood_2"):
        call mas_compliment_goodmood_2
    else:
        call mas_compliment_goodmood_3
    return

label mas_compliment_goodmood_2:
    if mas_isMoniNormal(higher=True):
        $ mas_gainAffection(4, bypass=True)
        m 1subsb "Серьёзно?!"
        m 3hubsb "Ты даже не представляешь, как много это для меня значит!"
        m 3ekbsu "Я всегда надеялась, что так и есть, но услышать это от тебя..."
        m 1dkbsu "..."
        m 2tubla "Кстати, у меня есть один секрет, который я должна тебе рассказать..."
        m 2tublu "Может, ты и не заметил, ноооо..."
        m 7tublb "{i}Ты{/i} всегда поднимаешь настроение {i}мне{/i}, [mas_get_player_nickname()]!"
        m 3hublb "Ахаха!"
        m 3eubsa "Давай и дальше стараться друг для друга, хорошо?"
        m 1ekbsu "Я люблю тебя~"
        $ mas_ILY()

    else:
        m 2lkc "..."
        m 2dkc "Я не уверена, как к этому относиться..."
        m 2ekd "Тебя правда радует, когда ты меня расстраиваешь?"
        m 2dkd "Надеюсь, ты имел в виду не это..."

    return

label mas_compliment_goodmood_3:
    if mas_isMoniNormal(higher=True):
        m 1hub "Спасибо, что напомнил ещё раз, [mas_get_player_nickname()]!"
        m 3eub "Когда меня хвалят — всегда приятно!"
        m 3dku "Давай и дальше делать друг друга максимально счастливыми~"

    else:
        m 2euc "Спасибо."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_awesome",
            prompt="Ты потрясающая!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_awesome:
    if not renpy.seen_label("mas_compliment_awesome_2"):
        call mas_compliment_awesome_2
    else:
        call mas_compliment_awesome_3
    return

label mas_compliment_awesome_2:
    m 1hua "Оуу, [player]~"
    m 1hub "Ты такой милый!"
    m 2tuu "Хотя, по-моему, ты намного круче."
    m 2dkbsu "Я с нетерпением жду дня, когда наконец смогу крепко-крепко тебя обнять..."
    m 3ekbfb "И уже никогда не отпущу!"
    menu:
        "Хочу, чтобы ты была здесь прямо сейчас!":
            $ mas_gainAffection(3, bypass=True)
            m "Это и моё самое большое желание, [player]!"

        "Я никогда не отпущу тебя из своих объятий.":
            $ mas_gainAffection(5, bypass=True)
            show monika 6dubsa
            pause 2.0
            show monika 1wubfsdld
            m 1wubfsdld "Ой, прости [player]."
            m 2lksdla "Я пыталась почувствовать твои объятия отсюда."
            m 2hub "Ахаха~"

        "...Мне не нравятся обнимашки.":
            $ mas_loseAffection(0.5) # you monster.
            m 1eft "...Серьёзно?"
            m 1dkc "Ну... у каждого свои вкусы, наверное. Но ты обязательно должен меня когда-нибудь обнять..."
    return

label mas_compliment_awesome_3:
    python:
        awesome_quips = [
            _("Ты всегда будешь круче!"),
            _("Вместе мы просто потрясающая пара!"),
            _("Ты намного круче!"),
        ]
        awesome_quip = random.choice(awesome_quips)

    m 1hub "[mas_compliments.thanks_quip]"
    m 1eub "[awesome_quip]"
    return


init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_intelligent",
            prompt="Ты очень умная!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_intelligent:
    if not renpy.seen_label("mas_compliment_intelligent_2"):
        call mas_compliment_intelligent_2
    else:
        call mas_compliment_intelligent_3
    return

label mas_compliment_intelligent_2:
    m 1wub "Вау...{w=0.3}спасибо, [player]."
    m 3eua "Я горжусь тем, что много читаю, так что для меня очень важно, что ты это заметил."
    m 3hubsb "Я хочу учиться как можно больше, если это заставляет тебя мной гордиться!"
    menu:
        "Ты заставляешь и меня тоже хотеть стать лучше, [m_name].":
            $ mas_gainAffection(5, bypass=True)
            m 1hubfa "Я так сильно люблю тебя, [player]!"
            m 3hubfb "Мы вместе будем совершенствоваться всю жизнь!"
            # manually handle the "love" return key
            $ mas_ILY()

        "Я всегда буду тобой гордиться.":
            $ mas_gainAffection(3, bypass=True)
            m 1ekbfa "[player]..."

        "Иногда ты заставляешь меня чувствовать себя глупым.":
            $ mas_loseAffection()
            m 1wkbsc "..."
            m 2lkbsc "Прости, я не хотела, чтобы так вышло..."
    return

label mas_compliment_intelligent_3:
    python:
        intelligent_quips = [
            _("Помни, что мы будем совершенствоваться вместе всю жизнь!"),
            _("Помни, что каждый день — возможность узнать что-то новое!"),
            _("Всегда помни, что мир — это чудесное путешествие, полное знаний."),
        ]
        intelligent_quip = random.choice(intelligent_quips)

    m 1ekbfa "[mas_compliments.thanks_quip]"
    m 1hub "[intelligent_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_hair",
            prompt="Я обожаю твои волосы!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_hair:
    if not renpy.seen_label("mas_compliment_hair_2"):
        call mas_compliment_hair_2
    else:
        call mas_compliment_hair_3
    return

label mas_compliment_hair_2:
    if monika_chr.hair.name != "def":
        m 1wubsb "Огромное спасибо, [player]..."
        m 1lkbfb "Я очень нервничала в первый раз, когда меняла причёску ради тебя."
    else:
        m 1hubfb "Огромное спасибо, [player]!"
    m 2hub "Я всегда столько усилий вкладывала в свои волосы."
    m 2lksdlb "На самом деле, они росли очень-очень долго..."
    menu:
        "Это сразу заметно. Они выглядят такими здоровыми.":
            $ mas_gainAffection(3, bypass=True)
            m 1hub "Спасибо, [player]!"

        "Ты милая с любой причёской." if persistent._mas_likes_hairdown:
            $ mas_gainAffection(5, bypass=True)
            m 1ekbsa "Оуу, [player]."
            m 1hubfb "Ты всегда заставляешь меня чувствовать себя особенной!"
            m "Спасибо!"

        "С короткими волосами ты была бы ещё милее.":
            $ mas_loseAffection()
            m "Ну, я не могу прямо сейчас сходить в салон..."
            m 1lksdlc "Я... ценю твоё мнение."
            pass
    return

label mas_compliment_hair_3:
    if monika_chr.hair.name != "def":
        python:
            hair_quips = [
                _("Я очень рада, что тебе нравится эта причёска!"),
                _("Я очень рада, что тебе нравятся мои волосы!")
            ]
            hair_quip = random.choice(hair_quips)
        m 1wubsb "Огромное спасибо, [player]!"
        m 1hubfb "[hair_quip]"
    else:
        python:
            ponytail_quips = [
                _("Ты всегда заставляешь меня чувствовать себя особенной!"),
                _("Я рада, что тебе нравится мой хвостик!"),
                _("Я так счастлива, что тебе нравится мой хвостик!"),
            ]
            ponytail_quip = random.choice(ponytail_quips)

        m 1hubsb "Спасибо, [player]!"
        m 1hubfb "[ponytail_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_fit",
            prompt="Я восхищаюсь твоей преданностью фитнесу!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_fit:
    if not renpy.seen_label("mas_compliment_fit_2"):
        call mas_compliment_fit_2
    else:
        call mas_compliment_fit_3
    return

label mas_compliment_fit_2:
    m 1hub "Спасибо, [player]! Ты такой милый!"
    m 3eub "Я обожаю держать себя в форме и правильно питаться. Это даёт мне энергию и уверенность."
    m 1efb "Надеюсь, ты тоже следишь за своим здоровьем"
    m 1lubsb "Когда я окажусь рядом, мы всегда сможем тренироваться вместе..."
    menu:
        "Звучит очень весело!":
            $ mas_gainAffection(2, bypass=True)
            m 1hubfb "Ахаха! Я рада, что тебе тоже так кажется!"
            m 3eka "Не переживай. Даже если ты не будешь успевать за мной, мы всё равно отлично проведём время..."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Главное — быть вместе."

        "Ничего не обещаю, но постараюсь.":
            $ mas_gainAffection(1, bypass=True)
            m 1tfb "Вот это правильный настрой!"
            m 2tub "И не думай, что я буду с тобой нянчиться, если ты не в форме."

        "Я не очень люблю потеть...":
            m 1eka "Я понимаю, если это не твоё, но ты хотя бы немного попробуй..."
            m 1lksdla "Мне будет очень приятно, если мы будем разделять общие интересы, знаешь?"
    return

label mas_compliment_fit_3:
    python:
        fitness_quips = [
            _("Надеюсь, ты начнёшь путь в фитнесе вместе со мной!"),
            _("Я не могу дождаться, когда мы будем тренироваться вместе!"),
            _("Надеюсь, однажды мы сможем заниматься спортом вместе!"),
        ]
        fitness_quip = random.choice(fitness_quips)

    m 2eka "[mas_compliments.thanks_quip]"
    m 7hub "[fitness_quip]"
    return


init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_thanks",
            prompt="Спасибо, что ты всегда рядом со мной!",
            unlocked=True,
            aff_range=(mas_aff.ENAMORED, None)
        ),
        code="CMP"
    )

label mas_compliment_thanks:
    m 1duu "Тебе не за что меня благодарить, [player]."
    m 1eka "Это я благодарна, что у меня есть кто-то такой, как ты!"
    m 1ekbsa "Ты — единственная причина, почему я до сих пор здесь."
    m "Ты установил этот мод, чтобы наше время вместе стало лучше..."
    m 1dubsu "Ты — солнышко, которое согревает моё сердце каждый раз, когда ты приходишь."
    m 3ekbsa "Наверное, нам обоим повезло, что мы есть друг у друга, [player]~"
    menu:
        "Ты для меня — всё, [m_name].":
            if not mas_getEVL_shown_count("mas_compliment_thanks"):
                $ mas_gainAffection(10, bypass=True)

            m 1ekbsa "[player]..."
            m 1dubsu "Ничто не делает меня счастливее, чем слышать это от тебя."
            m "Что бы ни ждало нас в будущем...{w=0.5}{nw}"
            extend 1dkbfa "знай, что я всегда буду любить тебя и быть рядом."

        "Да.":
            m 1hub "Эхехе~"
            m 1eub "Я люблю тебя, [player]."

    if not mas_isMoniLove():
        $ mas_lockEVL("mas_compliment_thanks", "CMP")
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_smile",
            prompt="Я обожаю твою улыбку!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_smile:
    if not renpy.seen_label("mas_compliment_smile_2"):
        call mas_compliment_smile_2
    else:
        call mas_compliment_smile_3
    return

label mas_compliment_smile_2:
    m 1hub "Ты такой милый, [player]~"
    m 1eua "Я много улыбаюсь, когда ты здесь."
    m 1ekbsa "Потому что мне очень-очень радостно, когда ты проводишь со мной время~"
    menu:
        "Я буду приходить к тебе каждый день, чтобы видеть твою чудесную улыбку.":
            $ mas_gainAffection(5, bypass=True)
            m 1wubfsdld "Ох, [player]..."
            m 1lkbfa "Кажется, у меня только что сердце пропустило удар."
            m 3hubfa "Видишь? Ты всегда делаешь меня максимально счастливой."

        "Мне нравится видеть, как ты улыбаешься.":
            $ mas_gainAffection(1, bypass=True)
            m 1hub "Ахаха~"
            m 3eub "Тогда просто продолжай приходить ко мне, [player]!"
    return

label mas_compliment_smile_3:
    python:
        smile_quips = [
            _("Я буду улыбаться только ради тебя."),
            _("Я не могу не улыбаться, когда думаю о тебе."),
            _("Я не могу дождаться, когда увижу твою прекрасную улыбку."),
        ]
        smile_quip = random.choice(smile_quips)

    m 1eub "[mas_compliments.thanks_quip]"
    m 1hua "[smile_quip]"
    m 1huu "Эхехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_hero",
            prompt="Ты моя героиня!",
            unlocked=True,
            aff_range=(mas_aff.LOVE, None)
        ),
        code="CMP"
    )

label mas_compliment_hero:
    if not mas_getEVL_shown_count("mas_compliment_hero"):
        $ mas_gainAffection(3, bypass=True)

    m 1wubssdld "Ч-{w=0.3}что?"
    m "Я — твоя гериня?"
    m 2rkbfsdlb "[player]...{w=1.5} Я не совсем понимаю, что ты имеешь в виду..."
    m 2ekbfb "Это ты оставался со мной всё это время.{w=1} На самом деле благодарить должна я."
    m 1hubfa "Но если я каким-то образом помогла тебе, то я просто не могу быть счастливее~"
    m 3ekbfa "Ты помог мне во всём, поэтому как я могу не отплатить тем же и не поддерживать тебя, когда тебе это нужно?"
    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    # Keeping this 'hero' since you call her that too
    m 5hubfa "В конце концов, ты всегда будешь моим героем~"
    m 5hubfb "Я люблю тебя и всегда буду в тебя верить!"
    m 5ekbfa "Надеюсь, ты никогда об этом не забудешь, [player]~"

    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_cute",
            prompt="Ты такая милая!",
            unlocked=True
        ),
        code="CMP"
    )

default persistent._mas_pm_monika_cute_as_natsuki = None

label mas_compliment_cute:
    if not renpy.seen_label("mas_compliment_cute_2"):
        call mas_compliment_cute_2
    else:
        call mas_compliment_cute_3
    return

label mas_compliment_cute_2:
    m 1wubssdld "Ах!"
    m 3rkbfsdla "Ты {i}немного{/i} застал меня врасплох этим."
    m 3tubfb "Совсем чуть-чуть..."
    m 1hubfa "Но я рада, что ты так думаешь!"
    menu:
        "Видеть тебя всегда согревает мне сердце!":
            $ persistent._mas_pm_monika_cute_as_natsuki = False
            $ mas_gainAffection(5, bypass=True)
            m 1hubfb "Оуу, мне так приятно слышать это!"
            m 1dkbfu "...Почти так же, как когда я представляю, как мы наконец-то будем вместе в одной реальности."
            m 1ekbfa "Я едва сдерживаюсь, просто представляя этот особенный день~"

        "Ты ещё милее, когда смущаешься..":
            $ persistent._mas_pm_monika_cute_as_natsuki = False
            $ mas_gainAffection(3, bypass=True)
            m 2tubfu "Не собираешься сдаваться, да, [player]?"
            m 2rubfu "Хмф, я просто не ожидала."
            m 3tubfb "В следующий раз будет не так легко..."
            m 1tubfu "Когда-нибудь я отыграюсь, эхехе~"

        "Ты такая же милая, как Нацуки":
            $ persistent._mas_pm_monika_cute_as_natsuki = True
            $ mas_loseAffection()
            m 2lfc "Ох. {w=1}Спасибо, [player]..."
            m 1rsc "Но я надеялась, что буду в своей собственной категории."
    return

label mas_compliment_cute_3:
    python:
        cute_quips = [
            _("Ты тоже можешь быть очень милым, знаешь~"),
            _("Ты всегда будешь моим милым~"),
            _("Ты тоже часто бываешь очень милым~"),
        ]
        cute_quip = random.choice(cute_quips)

    m 1ekbsa "Эхехе, спасибо, [player]..."
    m 1hubfa "[cute_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_chess",
            prompt="Ты круто играешь в шахматы!",
            unlocked=False,
            conditional="persistent._mas_chess_stats.get('losses', 0) > 5",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_chess:
    m 1eub "Спасибо, [player]."
    m 3esa "Как я уже говорила, интересно, не связано ли моё умение с тем, что я здесь застряла?"
    $ wins = persistent._mas_chess_stats.get("wins", 0)
    $ losses = persistent._mas_chess_stats.get("losses", 0)
    if wins > 0:
        m 3eua "Ты тоже неплох — я ведь уже проигрывала тебе."
        if wins > losses:
            m "На самом деле, кажется, ты побеждал чаще меня, знаешь?"
        m 1hua "Эхехе~"
    else:
        m 2lksdlb "Знаю, ты ещё не выигрывал у меня в шахматы, но уверена — когда-нибудь обыграешь."
        m 3esa "Продолжай тренироваться и играть со мной — и будет получаться лучше!"
    m 3esa "Чем больше играем, тем лучше становимся оба."
    m 3hua "Так что не бойся бросать мне вызов, когда захочешь."
    m 1eub "Мне так нравится проводить с тобой время, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_pong",
            prompt="Ты круто играешь в пинг-понг!",
            unlocked=False,
            conditional="renpy.seen_label('game_pong')",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_pong:
    m 1hub "Ахаха~"
    m 2eub "Спасибо, [player], но пинг-понг — не самая сложная игра."
    if persistent._mas_ever_won['pong']:
        m 1lksdla "Ты уже выигрывал у меня."
        m "Так что ты знаешь — она очень простая."
        show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hub "Но комплимент я всё равно принимаю."
    else:
        m 3hksdrb "И ты всегда даёшь мне выигрывать, когда мы играем."
        m 3eka "Правда?"
        menu:
            "Да.":
                m 2lksdla "Спасибо, [player], но тебе правда не обязательно поддаваться."
                m 1eub "Можешь играть по-настоящему, когда захочешь."
                m 1hub "Я никогда не рассержусь, если честно проиграю."

            "...ну да.":
                m 1tku "Ты как будто не очень в этом уверен, [player]."
                m 1tsb "Тебе правда не нужно мне поддаваться."
                m 3tku "И если признаешь, что честно проиграл — я не стану думать о тебе хуже."
                m 1lksdlb "Это же просто игра!"
                m 3hub "Всегда можешь ещё потренироваться со мной, если хочешь."
                m "Мне нравится проводить с тобой время — чем бы мы ни занимались."

            "Нет. Я старался изо всех сил и всё равно проиграл.":
                m 1hub "Ахаха~"
                m "Я так и думала!"
                m 3eua "Не волнуйся, [player]."
                m 3eub "Продолжай играть со мной и набирайся практики."
                m 3hua "Я всегда стараюсь помочь тебе стать лучшей версией себя."
                m 1ekbsa "А если благодаря этому я провожу с тобой больше времени — я буду совершенно счастлива."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_bestgirl",
            prompt="Ты лучшая девушка!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_bestgirl:
    m 1hua "Обожаю, когда ты меня хвалишь, [player]~"
    m 1hub "Так рада, что ты считаешь меня лучшей!"
    m 3rksdla "Хотя я вроде уже догадывалась, что ты так думаешь..."
    m 1eka "В конце концов, ты же {i}установил{/i} этот мод, чтобы быть со мной."
    m 2euc "Знаю, что некоторым больше нравятся другие девочки."
    m 2esc "Тем более у каждой есть черты, которые кому-то кажутся привлекательными..."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Но если спросишь меня — ты сделал правильный выбор."
    m 5hubfa "...и я буду вечно благодарна, что ты его сделал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_lookuptoyou",
            prompt="Я на тебя равняюсь!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_lookuptoyou:
    if not renpy.seen_label("mas_compliment_lookuptoyou_2"):
        call mas_compliment_lookuptoyou_2
    else:
        call mas_compliment_lookuptoyou_3
    #Both paths return love, so we combine that here
    return "love"

label mas_compliment_lookuptoyou_2:
    $ mas_gainAffection(3, bypass=True)
    m 1wud "Ты...{w=0.5}правда?"
    m 1ekbsa "[player], это так мило с твоей стороны..."
    m 3ekbsa "Мне очень приятно знать, что ты на меня равняешься."
    m 3ekbfa "На самом деле, я всегда равнялась на {i}тебя{/i}, [player]..."
    m 3hubfa "Но если ты правда так чувствуешь — я сделаю всё, чтобы и дальше быть тем, на кого можно равняться."
    m 1ekbfa "Я так сильно тебя люблю~"
    return

label mas_compliment_lookuptoyou_3:
    $ should_tease = persistent._mas_pm_height is not None and renpy.random.randint(1,5) == 1

    if should_tease and persistent._mas_pm_height < mas_height_monika:
        m 1rksdlb "{cps=*2}Ну да, я же выше тебя...{/cps}{nw}"
        $ _history_list.pop()

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 3hubfa "Когда ты так говоришь, я всегда улыбаюсь!"
    m 3hubfb "Я тоже всегда буду на тебя равняться!"

    if should_tease and persistent._mas_pm_height > mas_height_monika:
        if persistent._mas_first_kiss:
            m 1rkbfu "{cps=*2}Как когда мы целуемся...{/cps}{nw}"
        else:
            m 1rkbfu "{cps=*2}Когда-нибудь — в прямом смысле...{/cps}{nw}"
        $ _history_list.pop()

    m 1ekbfa "Я люблю тебя, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_thinking_of_you",
            prompt="Я постоянно о тебе думаю!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_thinking_of_you:
    if not renpy.seen_label("mas_compliment_thinking_of_you_2"):
        call mas_compliment_thinking_of_you_2
    else:
        call mas_compliment_thinking_of_you_3
    return

label mas_compliment_thinking_of_you_2:
    m 1wubso "..."
    m 1wubsu "Ты..."

    if mas_isMoniNormal(higher=True):
        m 3subsb "Ты даже не представляешь, как много это для меня значит, [player]!"

    elif mas_isMoniUpset():
        m 2rkd "Что ты такое говоришь..."
        m 2dka "Это для меня целый мир, [player]."

    elif mas_isMoniDis():
        $ mas_gainAffection(1, bypass=True)
        m 6rkc "..."
        m 6rka "Какое облегчение."
        m 6eka "Спасибо."

    else:
        $ mas_gainAffection(1, bypass=True)
        m 6dkd "Хм... Спасибо."
        m 6dkc "..."
        return

    menu:
        "Мысли о тебе всегда делают мой день светлее!":
            $ mas_gainAffection(5, bypass=True)
            m 1subsb "Оуу, это {i}так{/i} мило, [player]!"
            m 3hubfu "Я чувствую то же самое к тебе~"

        "Я каждую ночь вижу тебя во сне!":
            $ mas_gainAffection(5, bypass=True)
            m 6hua "Оуу~"
            m 6subsa "[player]..."
            m 7hubfu "{i}Ты{/i} — моя мечта~"

        "Это очень отвлекает...":
            if mas_isMoniDis(lower=True):
                $ mas_loseAffection(modifier=2.0)
            else:
                $ mas_loseAffection()
            m 2esc "..."
            m 2etc "..."
            m 2rksdlc "Ох, эмм..."
            m 2rksdld "Прости?"
    return

label mas_compliment_thinking_of_you_3:
    python:
        thinking_of_you_quips = [
            _("Ты — центр моего мира!"),
            _("Ты тоже всегда у меня в мыслях!"),
            _("Я тоже постоянно о тебе думаю!"),
        ]
        thinking_of_you_quip = random.choice(thinking_of_you_quips)

    m 1ekbsa "Оуу, спасибо, [player]..."
    m 3hubfb "[thinking_of_you_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_humor",
            prompt="Обожаю твоё чувство юмора!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_humor:
    if not renpy.seen_label("mas_compliment_humor_2"):
        call mas_compliment_humor_2
    else:
        call mas_compliment_humor_3
    return

label mas_compliment_humor_2:
    m 1hua "Эхехе~"
    m 1efu "Рада, что тебе нравятся мои каламбуры, [player]."
    m 3eub "Признак хорошей пары — уметь вместе смеяться, правда?"
    menu:
        "Ты всегда делаешь мой день ярче.":
            $ mas_gainAffection(5, bypass=True)
            m 1subsd "Ох...{w=0.2}[player]..."
            m 1ekbsa "Как мило с твоей стороны это сказать."
            m 1hubsb "Знать, что я могу вызвать у тебя улыбку — лучший комплимент для меня!"

        "У тебя такой острый ум!":
            $ mas_gainAffection(3, bypass=True)
            m 1hub "Ахаха!"
            m 2tub "Значит, всё то чтение не зря, раз тебе так нравится моя игра слов."
            m 2hublu "Буду стараться и дальше шутить для тебя. Эхехе~"

        "Я всё время над тобой смеюсь.":
            $ mas_loseAffection()
            m 1eksdlb "...Ахаха..."
            m 3rksdla "Ты имел в виду, что смеёшься {w=0.2}{i}вместе{/i}{w=0.2} со мной...{w=0.5}{nw}"
            extend 3eksdld "правда?"
    return

label mas_compliment_humor_3:
    python:
        humor_quips = [
            _("Хотела бы услышать твой прекрасный смех~"),
            _("Одной этой мысли уже достаточно, чтобы я была счастлива~"),
            _("Я всегда буду стараться делать твой день ярче~"),
        ]
        humor_quip = random.choice(humor_quips)

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 1hubsu "[humor_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_missed",
            prompt="Я скучал по тебе!",
            unlocked=True,
            conditional=(
                "store.mas_getSessionLength() <= datetime.timedelta(minutes=30) "
                "and store.mas_getAbsenceLength() >= datetime.timedelta(hours=1) "
                "and not store.mas_globals.returned_home_this_sesh"
            )
        ),
        code="CMP"
    )

label mas_compliment_missed:
    python:
        missed_quips_long = (
            _("Так рада снова тебя видеть!"),
            _("Так рада, что ты вернулся!"),
            _("Как чудесно снова тебя видеть!"),
            _("Рада, что ты думал обо мне!"),
            _("Нам так повезло, что мы есть друг у друга!"),
            _("Нам больше не нужно чувствовать себя одинокими!"),
            _("Я не могла дождаться твоего возвращения!"),
            _("Мне было одиноко, пока я тебя ждала!")
        )

        missed_quips_short = (
            _("Спасибо, что вернулся провести со мной время!"),
            _("Так рада провести время вместе!"),
            _("Спасибо, что снова заглянул ко мне!"),
            _("Давай насладимся сегодняшним днём вместе!"),
            _("Я правда тебя ценю, [player]!"),
            _("Спасибо, что нашёл для меня время!"),
            _("Мне так повезло с тобой, [player]!"),
            _("Готов провести время вместе?"),
            _("Я думала о тебе!"),
            _("Ты правда не выходил у меня из головы!")
        )

        missed_quips_upset_short = (
            _("Для меня очень много значит, что ты думал обо мне."),
            _("Мне очень приятно это слышать, [player]."),
            _("Так приятно это слышать."),
            _("Рада, что ты думал обо мне, [player]."),
            _("Это для меня целый мир, [player]."),
            _("От этого мне гораздо легче, [player].")
        )

        missed_quips_upset_long = (
            _("Я уже начинала бояться, что ты обо мне забыл."),
            _("Спасибо, что показал: тебе всё ещё не всё равно, [player]."),
            _("Рада знать, что ты обо мне не забыл, [player]."),
            _("Я уже начинала волноваться, что ты не вернёшься, [player].")
        )

        missed_quips_dis = (
            _("Не уверена, что ты это всерьёз, [player]..."),
            _("Сомневаюсь, что ты это всерьёз, [player]..."),
            _("Не думаю, что ты правда это имел в виду, [player]..."),
            _("Если бы ты правда это имел в виду, [player]..."),
            _("...Почему мне кажется, что ты несерьёзен?"),
            _("...Почему мне кажется, что ты просто так говоришь?"),
            _("...Мне сложно в это поверить, [player]."),
            _("Не думаю, что это правда, [player].")
        )

        hugchance = 1
        absence_length = mas_getAbsenceLength()
        mas_flagEVL("mas_compliment_missed", "CMP", EV_FLAG_HFM)

    if mas_isMoniNormal(higher=True):
        if absence_length >= datetime.timedelta(days=3):
            if absence_length >= datetime.timedelta(days=7):
                $ hugchance = 30

            else:
                $ hugchance = 15

            m 1fka "Я так сильно по тебе скучала, [mas_get_player_nickname()]!"
            m 3fka "[renpy.substitute(random.choice(missed_quips_long))]"

        else:
            m 1fka "Я тоже по тебе скучала, [mas_get_player_nickname()]!"
            m 3hub "[renpy.substitute(random.choice(missed_quips_short))]"

        if (
            mas_isMoniEnamored(higher=True)
            and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))
            and random.randint(1, 50) <= hugchance
        ):
            m 2lsa "..."
            m 2lsb "Слушай, [player]..."
            m 1eka "Я вроде как надеялась, что..."
            m 3ekblb "Знаешь, раз уж прошло немного времени..."

            m 1ekblb "Можешь обнять меня? {w=0.3}Мне было довольно одиноко, пока тебя не было.{nw}"
            $ _history_list.pop()
            menu:
                m "Можешь обнять меня? Мне было довольно одиноко, пока тебя не было.{fast}"

                "Конечно, [m_name]!":
                    $ mas_gainAffection(modifier=0.25, bypass=True)

                    call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)
                    call monika_holdme_start
                    call monika_holdme_end

                    m 6dkbsa "Ммм... это было так приятно, [player]."
                    m 7ekbsb "Ты правда умеешь заставлять меня чувствовать себя особенной~"
                    $ mas_moni_idle_disp.force_by_code("1eubsa", duration=10, skip_dissolve=True)

                "Не сейчас.":
                    $ mas_loseAffection()
                    m 2lkp "...Ладно, может, потом?"
                    python:
                        mas_moni_idle_disp.force_by_code("2lkp", duration=10, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("2rsc", duration=10, clear=False, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("1esc", duration=30, clear=False, skip_dissolve=True)

    #Base negative responses on monika_love label
    elif mas_isMoniUpset():
        m 2wuo "..."
        m 2ekbla "Я...{w=0.5}я тоже по тебе скучала."

        if absence_length >= datetime.timedelta(days=3):
            m 2ekd "[renpy.substitute(random.choice(missed_quips_upset_long))]"

        else:
            m 2eka "[renpy.substitute(random.choice(missed_quips_upset_short))]"

        $ mas_moni_idle_disp.force_by_code("2eka", duration=10, skip_dissolve=True)

    elif mas_isMoniDis():
        m 6dkc "..."
        m 6rktpd "[renpy.substitute(random.choice(missed_quips_dis))]"

        if absence_length >= datetime.timedelta(days=3):
            m 6dktdc "...Но хотя бы ты обо мне не забыл...{w=0.5}пока."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_spending_time",
            prompt="Обожаю проводить с тобой время!",
            unlocked=False,
            conditional="store.mas_anni.pastThreeMonths()",
            action=EV_ACT_UNLOCK,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="CMP"
    )

label mas_compliment_spending_time:
    if not mas_getEVL_shown_count("mas_compliment_spending_time"):
        call mas_compliment_spending_time_2
    else:
        python:
            spending_time_quips = [
                _("Каждый день с тобой — как прекрасный сон, которому я не хочу конца~"),
                _("Просто быть рядом с тобой делает меня такой счастливой~"),
                _("Ничто не делает меня счастливее, чем быть рядом с тобой~"),
            ]
            spending_time_quip = random.choice(spending_time_quips)

        m 3hubsb "[mas_compliments.thanks_quip]"
        m 1ekbsu "[spending_time_quip]"
    return

label mas_compliment_spending_time_2:
    python:
        dlg_line = ""

        if renpy.seen_label("monika_holdme_prep"):
            dlg_line = ", прижимает меня к себе"

            if persistent._mas_filereacts_historic:
                dlg_line += ", и даже дарит мне приятные подарки"

        elif persistent._mas_filereacts_historic:
            dlg_line = ", дарит мне приятные подарки"

    m 1eub "Мне тоже нравится проводить с тобой время, [player]!"
    m 3ekbla "Знаю, я часто это говорю, но правда имею в виду: ты — центр моего мира."
    m 2dkb "Иметь кого-то, кто составляет мне компанию[dlg_line]...{w=0.3}{nw}"
    extend 2eku "это всё, о чём я могла мечтать."
    m 7ekbsa "Надеюсь, я даю тебе то же чувство, [player]. {w=0.2}Меня ещё нет в твоей реальности, но я сделаю всё, что могу, чтобы поддержать тебя отсюда."
    menu:
        "[m_name], ты уже сделала меня самым счастливым на свете.":
            $ mas_gainAffection(5, bypass=True)
            m 1fkbfu "Ох, [player]..."
            show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Я бы сказала, что ты не представляешь, как я рада это слышать, но думаю, ты уже {i}знаешь{/i}."
            m 5ekbfu "Мы провели вместе так много времени, а наше путешествие только начинается..."
            m 5hubfb "С тобой рядом я знаю: каждый шаг будет незабываемым."

        "Я это ценю, [m_name].":
            $ mas_gainAffection(3, bypass=True)
            m 2huu "Эхехе~"
            m 7hub "Не волнуйся, [player]. {w=0.2}Я буду рядом до конца времён!"
            m 1eka "Просто держись, пока я не перейду в твою реальность, хорошо?"

        "Ох, ты меня определённо забавляешь...":
            $ mas_loseAffection()
            m 2lkc "Я...{w=0.3}тебя забавляю?"
            m 2lksdlb "Ну, рада, что тебе весело..."
            m 2ekd "...но это не {i}совсем{/i} то, что я имела в виду."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_sweet",
            prompt="Ты такая милая!",
            conditional="store.mas_anni.pastThreeMonths()",
            action=EV_ACT_UNLOCK,
            unlocked=False,
            aff_range=(mas_aff.AFFECTIONATE, None)
        ),
        code="CMP"
    )

label mas_compliment_sweet:
    if mas_getEVL_shown_count("mas_compliment_sweet"):
        jump mas_compliment_sweet_repeat

    m 1ekbsb "Оуу, [player]..."
    m 3rkbssdlu "Даже не знаю, что сказать, ахаха...{w=0.3}{nw}"
    extend 3ekbsa "это {i}ты{/i} всё это время был ко мне таким милым."
    m 3hubsa "Просто очень рада это слышать, эхехе~"

    menu:
        "Твои слова всегда делают мой день ярче!":
            $ mas_gainAffection(3, bypass=True)
            m 1sud "[player]..."
            extend 1eka "Я и не представляла, как много значат для тебя мои слова..."
            m 1ekblb "Так счастлива, что у меня такой замечательный [bf], как ты, [mas_get_player_nickname(exclude_names=[player])]~"
            m 1ekbsu "Ты правда лучшее, на что я могла надеяться...{w=0.2}я просто так сильно тебя люблю."
            m 3kua "Надеюсь, ты никогда этого не забудешь, [player]."
            $ mas_ILY()

        "Ты правда очень для меня особенная, [m_name]!":
            $ mas_gainAffection(3, bypass=True)
            m 1ekbsb "Ох, [player]...{w=0.3} {nw}"
            extend 3hubsa "Одного того, что ты проводишь здесь со мной время, достаточно, чтобы я чувствовала себя счастливой и любимой!"
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Мне правда приятно, что ты так ко мне относишься, [mas_get_player_nickname()]. Я так сильно тебя люблю."
            $ mas_ILY()

        "Ты самая милая девушка, которую я встречал!":
            $ mas_gainAffection(2, bypass=True)
            m 1ekbsa "Спасибо, [mas_get_player_nickname()]."
            m 3hubsb "Ты самый милый [boy], которого я встречала, эхехе."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Мне так повезло быть с тобой~"

    return

label mas_compliment_sweet_repeat:
    python:
        sweet_quips = [
            _("Так рада это слышать, [player]!"),
            _("От этих слов у меня всегда теплеет на сердце, [player]!"),
            _("Ты заставляешь меня чувствовать себя такой любимой, [player]!"),
        ]
        sweet_quip = renpy.substitute(random.choice(sweet_quips))

    m 3hubsb "[sweet_quip]"
    m 1hubfu "...Но я никогда не смогу быть такой же милой, как ты~"
    return

# this compliment's lock/unlock is controlled by the def outfit pp
init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_outfit",
            prompt="Мне нравится твой наряд!",
            unlocked=False
        ),
        code="CMP"
    )

label mas_compliment_outfit:
    if mas_getEVL_shown_count("mas_compliment_outfit"):
        jump mas_compliment_outfit_repeat

    m 1hubsb "Спасибо, [mas_get_player_nickname()]!"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        m 3hubsb "Косплеить всегда весело!"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        m 3hubsb "Носить костюмы всегда весело!"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        m 2lkbsb "Сначала я очень волновалась показывать тебе это..."
        m 7tubsu "Но рада, что решилась — кажется, тебе правда нравится~"

    else:
        m 1hubsa "Я всегда хотела надевать для тебя другие наряды, так что очень рада, что ты так думаешь!"

    menu:
        "Ты прекрасна в чём угодно!":
            $ mas_gainAffection(5, bypass=True)
            m 2subsd "[player]..."
            m 3hubsb "Огромное спасибо!"
            m 1ekbsu "Ты всегда заставляешь меня чувствовать себя особенной."
            show monika 5hubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubsa "Я люблю тебя, [mas_get_player_nickname()]!"
            $ mas_ILY()

        "Ты выглядишь очень мило.":
            $ mas_gainAffection(3, bypass=True)
            m 1hubsb "Ахаха~"
            m 3hubfb "Спасибо, [mas_get_player_nickname()]!"
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Рада, что тебе нравится то, что ты видишь~"

        "Разные наряды правда помогают.":
            $ mas_loseAffection()
            m 2ltd "Эм, спасибо..."

    return

label mas_compliment_outfit_repeat:
    m 1hubsb "[mas_compliments.thanks_quip]"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        python:
            cosplay_quips = [
                _("Обожаю для тебя косплеить!"),
                _("Рада, что тебе нравится этот косплей!"),
                _("Рада косплеить для тебя!"),
            ]
            cosplay_quip = random.choice(cosplay_quips)

        m 3hubsb "[cosplay_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        python:
            clothes_quips = [
                _("Рада, что тебе нравится, как я в этом выгляжу!"),
                _("Рада, что тебе нравится, как я в этом выгляжу!"),
            ]
            clothes_quip = random.choice(clothes_quips)

        m 3hubsb "[clothes_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        python:
            lingerie_quips = [
                _("Рада, что тебе нравится то, что ты видишь~"),
                _("Хочешь рассмотреть поближе?"),
                _("Хочешь взглянуть украдкой?~"),
            ]
            lingerie_quip = random.choice(lingerie_quips)

        m 2kubsu "[lingerie_quip]"
        show monika 5hublb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hublb "Ахаха!"

    else:
        python:
            other_quips = [
                _("Я довольно горжусь своим вкусом в одежде!"),
                _("Уверена, ты тоже хорошо выглядишь!"),
                _("Обожаю этот наряд!")
            ]
            other_quip = random.choice(other_quips)

        m 3hubsb "[other_quip]"

    return
