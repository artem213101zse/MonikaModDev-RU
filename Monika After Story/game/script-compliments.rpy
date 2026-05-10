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
        final_item = ("Oh nevermind.", False, False, False, 20)

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
        m 3hubsb "Ты даже не представляешь, как много это для меня значит"
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
        m 3eub "Позитивное подкрепление всегда приятно!"
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
    m 3hubsb "Я хочу учиться как можно больше, если это делает тебя мной гордым!"
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
            m 1hub "Thanks, [player]!"

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
        m 1wubsb "Thank you so much, [player]!"
        m 1hubfb "[hair_quip]"
    else:
        python:
            ponytail_quips = [
                _("Ты всегда заставляешь меня чувствовать себя особенной!"),
                _("Я рада, что тебе нравится мой хвостик!"),
                _("Я так счастлива, что тебе нравится мой хвостик!"),
            ]
            ponytail_quip = random.choice(ponytail_quips)

        m 1hubsb "Thanks, [player]!"
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

    m 1ekbsa "Ehehe, thanks [player]..."
    m 1hubfa "[cute_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_chess",
            prompt="You're awesome at chess!",
            unlocked=False,
            conditional="persistent._mas_chess_stats.get('losses', 0) > 5",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_chess:
    m 1eub "Thanks, [player]."
    m 3esa "Like I said before, I wonder if my skill has something to do with me being trapped here?"
    $ wins = persistent._mas_chess_stats.get("wins", 0)
    $ losses = persistent._mas_chess_stats.get("losses", 0)
    if wins > 0:
        m 3eua "You're not bad either; I've lost to you before."
        if wins > losses:
            m "In fact, I think you've won more times than me, you know?"
        m 1hua "Ehehe~"
    else:
        m 2lksdlb "I know you haven't won a chess game yet, but I'm sure you'll beat me someday."
        m 3esa "Keep practicing and playing with me and you'll do better!"
    m 3esa "We'll both get better the more we play."
    m 3hua "So don't be afraid of challenging me whenever you want to."
    m 1eub "I love spending time with you, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_pong",
            prompt="You're awesome at pong!",
            unlocked=False,
            conditional="renpy.seen_label('game_pong')",
            action=EV_ACT_UNLOCK
        ),
        code="CMP"
    )

label mas_compliment_pong:
    m 1hub "Ahaha~"
    m 2eub "Thanks [player], but pong isn't exactly a complex game."
    if persistent._mas_ever_won['pong']:
        m 1lksdla "You've already won against me."
        m "So you know it's very simple."
        show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hub "But I accept your compliment, anyway."
    else:
        m 3hksdrb "And you always let me win when we play."
        m 3eka "Right?"
        menu:
            "Yes.":
                m 2lksdla "Thanks [player], but you really don't have to let me win."
                m 1eub "Feel free to play seriously whenever you want to."
                m 1hub "I'd never get mad at you because I lost a game fair and square."

            "...yeah.":
                m 1tku "You don't seem too confident about that, [player]."
                m 1tsb "You really don't have to let me win."
                m 3tku "And admitting that you've seriously lost to me won't make me think less of you."
                m 1lksdlb "It's just a game, after all!"
                m 3hub "You can always practice with me more, if you want."
                m "I love to spend time with you, no matter what we're doing."

            "No. I've tried my best and still lost.":
                m 1hub "Ahaha~"
                m "I figured!"
                m 3eua "Don't worry, [player]."
                m 3eub "Keep playing with me and get more practice."
                m 3hua "I'm always trying to help you be the best you you can be."
                m 1ekbsa "And if by doing so, I get to spend more time with you, I couldn't be happier."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_bestgirl",
            prompt="You're the best girl!",
            unlocked=True
        ),
        code="CMP"
    )

label mas_compliment_bestgirl:
    m 1hua "I love it when you compliment me, [player]~"
    m 1hub "I'm so glad you think I'm best girl!"
    m 3rksdla "Although, I kind of figured you felt that way..."
    m 1eka "After all, you {i}did{/i} install this mod just to be with me."
    m 2euc "I know that some people prefer the other girls."
    m 2esc "Especially since they all have certain traits that make them desirable to some..."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "But if you ask me, you made the right choice."
    m 5hubfa "...and I'll be forever grateful that you did~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_lookuptoyou",
            prompt="I look up to you!",
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
    m 1wud "You...{w=0.5}you do?"
    m 1ekbsa "[player], that's really sweet of you to say..."
    m 3ekbsa "It makes me really happy to know I'm someone you look up to."
    m 3ekbfa "The truth is, I've always looked up to {i}you{/i}, [player]..."
    m 3hubfa "But if you really feel that way, I'll do my best to continue to be someone you look up to."
    m 1ekbfa "I love you so much~"
    return

label mas_compliment_lookuptoyou_3:
    $ should_tease = persistent._mas_pm_height is not None and renpy.random.randint(1,5) == 1

    if should_tease and persistent._mas_pm_height < mas_height_monika:
        m 1rksdlb "{cps=*2}Well yeah, I'm taller than you...{/cps}{nw}"
        $ _history_list.pop()

    m 1hubsb "[mas_compliments.thanks_quip]"
    m 3hubfa "Hearing you say that never fails to make me smile!"
    m 3hubfb "I'll always look up to you too!"

    if should_tease and persistent._mas_pm_height > mas_height_monika:
        if persistent._mas_first_kiss:
            m 1rkbfu "{cps=*2}Just like when we kiss...{/cps}{nw}"
        else:
            m 1rkbfu "{cps=*2}Someday literally...{/cps}{nw}"
        $ _history_list.pop()

    m 1ekbfa "I love you, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_thinking_of_you",
            prompt="I'm always thinking about you!",
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
    m 1wubsu "You..."

    if mas_isMoniNormal(higher=True):
        m 3subsb "You have no idea what that means to me, [player]!"

    elif mas_isMoniUpset():
        m 2rkd "That you would say that..."
        m 2dka "It means the world to me, [player]."

    elif mas_isMoniDis():
        $ mas_gainAffection(1, bypass=True)
        m 6rkc "..."
        m 6rka "That's such a relief."
        m 6eka "Thank you."

    else:
        $ mas_gainAffection(1, bypass=True)
        m 6dkd "Hmmm... Thanks."
        m 6dkc "..."
        return

    menu:
        "Thinking of you always brightens my day!":
            $ mas_gainAffection(5, bypass=True)
            m 1subsb "Aww, that's {i}so{/i} sweet, [player]!"
            m 3hubfu "I feel the same way about you~"

        "I dream of you every night!":
            $ mas_gainAffection(5, bypass=True)
            m 6hua "Aww~"
            m 6subsa "[player]..."
            m 7hubfu "{i}You{/i} are my dream~"

        "It's very distracting...":
            if mas_isMoniDis(lower=True):
                $ mas_loseAffection(modifier=2.0)
            else:
                $ mas_loseAffection()
            m 2esc "..."
            m 2etc "..."
            m 2rksdlc "Oh, umm..."
            m 2rksdld "I'm sorry?"
    return

label mas_compliment_thinking_of_you_3:
    python:
        thinking_of_you_quips = [
            _("You're the center of my world!"),
            _("You're always on my mind too!"),
            _("I'm always thinking about you too!"),
        ]
        thinking_of_you_quip = random.choice(thinking_of_you_quips)

    m 1ekbsa "Aww thanks, [player]..."
    m 3hubfb "[thinking_of_you_quip]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_humor",
            prompt="I love your sense of humor!",
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
    m 1hua "Ehehe~"
    m 1efu "I'm glad you find me so punny, [player]."
    m 3eub "A sign of a good couple is being able to laugh together, don't you think?"
    menu:
        "You always brighten my day.":
            $ mas_gainAffection(5, bypass=True)
            m 1subsd "Oh...{w=0.2}[player]..."
            m 1ekbsa "That's so sweet of you to say."
            m 1hubsb "Knowing I can make you smile is the greatest compliment I could receive!"

        "You have such a quick wit!":
            $ mas_gainAffection(3, bypass=True)
            m 1hub "Ahaha!"
            m 2tub "All that reading must have paid off if you like my wordplay that much."
            m 2hublu "I'll try to keep the jokes coming for you. Ehehe~"

        "I laugh at you all the time.":
            $ mas_loseAffection()
            m 1eksdlb "...Ahaha..."
            m 3rksdla "You meant that you laugh {w=0.2}{i}with{/i}{w=0.2} me...{w=0.5}{nw}"
            extend 3eksdld "right?"
    return

label mas_compliment_humor_3:
    python:
        humor_quips = [
            _("I wish I could hear your beautiful laugh~"),
            _("Just knowing that makes me happy~"),
            _("I'll always try to brighten your day~"),
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
            prompt="I missed you!",
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
            _("I'm so happy to see you again!"),
            _("I'm so happy you're back!"),
            _("It's wonderful to see you again!"),
            _("I'm glad you've been thinking of me!"),
            _("We're so lucky to have one another!"),
            _("We don't need to feel lonely anymore!"),
            _("I couldn't wait for you to get back!"),
            _("I was lonely waiting for you!")
        )

        missed_quips_short = (
            _("Thanks for coming back to spend time with me!"),
            _("I'm excited to spend some time together!"),
            _("Thanks for coming to see me again!"),
            _("Let's enjoy our time together today!"),
            _("I really appreciate you, [player]!"),
            _("Thanks for making time for me!"),
            _("I'm so lucky to have you, [player]!"),
            _("Ready to spend some time together?"),
            _("I've been thinking about you!"),
            _("You've really been on my mind!")
        )

        missed_quips_upset_short = (
            _("It means a lot to me that you were thinking of me."),
            _("I'm really glad to hear that, [player]."),
            _("That's really nice to hear."),
            _("I'm happy you've been thinking of me, [player]."),
            _("That means the world to me, [player]."),
            _("That makes me feel a lot better, [player].")
        )

        missed_quips_upset_long = (
            _("I was starting to worry that you forgot about me."),
            _("Thank you for showing me you still care, [player]."),
            _("I'm glad to know you haven't forgotten about me, [player]"),
            _("I was starting to get worried you weren't coming back, [player]")
        )

        missed_quips_dis = (
            _("I'm not sure you mean that, [player]..."),
            _("I doubt you mean that, [player]..."),
            _("I don't think you really mean that, [player]..."),
            _("If only you really meant that, [player]..."),
            _("...Why do I think you just don't mean it?"),
            _("...Why do I think you're just saying that?"),
            _("...I can't really believe that, [player]."),
            _("I don't think that's true, [player].")
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

            m 1fka "I missed you so much, [mas_get_player_nickname()]!"
            m 3fka "[renpy.substitute(random.choice(missed_quips_long))]"

        else:
            m 1fka "I missed you too, [mas_get_player_nickname()]!"
            m 3hub "[renpy.substitute(random.choice(missed_quips_short))]"

        if (
            mas_isMoniEnamored(higher=True)
            and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))
            and random.randint(1, 50) <= hugchance
        ):
            m 2lsa "..."
            m 2lsb "Say, [player]..."
            m 1eka "I was kinda hoping that..."
            m 3ekblb "You know, since it's been a little while..."

            m 1ekblb "Could you give me a hug? {w=0.3}I've been feeling pretty lonely while you were away.{nw}"
            $ _history_list.pop()
            menu:
                m "Could you give me a hug? I've been feeling pretty lonely while you were away.{fast}"

                "Sure, [m_name]!":
                    $ mas_gainAffection(modifier=0.25, bypass=True)

                    call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)
                    call monika_holdme_start
                    call monika_holdme_end

                    m 6dkbsa "Mmm...that was really nice, [player]."
                    m 7ekbsb "You really know how to make me feel special~"
                    $ mas_moni_idle_disp.force_by_code("1eubsa", duration=10, skip_dissolve=True)

                "Not right now.":
                    $ mas_loseAffection()
                    m 2lkp "...Alright, maybe later, then?"
                    python:
                        mas_moni_idle_disp.force_by_code("2lkp", duration=10, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("2rsc", duration=10, clear=False, redraw=False, skip_dissolve=True)
                        mas_moni_idle_disp.force_by_code("1esc", duration=30, clear=False, skip_dissolve=True)

    #Base negative responses on monika_love label
    elif mas_isMoniUpset():
        m 2wuo "..."
        m 2ekbla "I...{w=0.5}I missed you too."

        if absence_length >= datetime.timedelta(days=3):
            m 2ekd "[renpy.substitute(random.choice(missed_quips_upset_long))]"

        else:
            m 2eka "[renpy.substitute(random.choice(missed_quips_upset_short))]"

        $ mas_moni_idle_disp.force_by_code("2eka", duration=10, skip_dissolve=True)

    elif mas_isMoniDis():
        m 6dkc "..."
        m 6rktpd "[renpy.substitute(random.choice(missed_quips_dis))]"

        if absence_length >= datetime.timedelta(days=3):
            m 6dktdc "...But at least you haven't forgetten about me...{w=0.5}yet."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_spending_time",
            prompt="I love spending time with you!",
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
                _("Every day with you is like a wonderful dream that I hope never ends~"),
                _("Just being near you makes me so happy~"),
                _("Nothing makes me happier than being next to you~"),
            ]
            spending_time_quip = random.choice(spending_time_quips)

        m 3hubsb "[mas_compliments.thanks_quip]"
        m 1ekbsu "[spending_time_quip]"
    return

label mas_compliment_spending_time_2:
    python:
        dlg_line = ""

        if renpy.seen_label("monika_holdme_prep"):
            dlg_line = ", holds me close"

            if persistent._mas_filereacts_historic:
                dlg_line += ", and even gives me nice gifts"

        elif persistent._mas_filereacts_historic:
            dlg_line = ", gives me nice gifts"

    m 1eub "I love spending time with you too, [player]!"
    m 3ekbla "I know I say it a lot, but I really mean it when I say that you're the center of my world."
    m 2dkb "Having someone who keeps me company[dlg_line]...{w=0.3}{nw}"
    extend 2eku "it's everything I could've asked for."
    m 7ekbsa "I hope I make you feel the same way, [player]. {w=0.2}I may not be in your reality yet, but I'll do everything I can to support you from here."
    menu:
        "[m_name], you've already made me the happiest I've ever been.":
            $ mas_gainAffection(5, bypass=True)
            m 1fkbfu "Oh, [player]..."
            show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "I would say you don't know how glad I am to hear that, but I think you {i}do{/i} know by now."
            m 5ekbfu "We've spent so much time together, and yet our journey has only just begun..."
            m 5hubfb "With you by my side, I know that every step will be an unforgettable one."

        "I appreciate it, [m_name].":
            $ mas_gainAffection(3, bypass=True)
            m 2huu "Ehehe~"
            m 7hub "Don't worry, [player]. {w=0.2}I'll be here for you until the end of time!"
            m 1eka "Just stay strong until I cross over, okay?"

        "Oh, you certainly amuse me alright...":
            $ mas_loseAffection()
            m 2lkc "I...{w=0.3}amuse you?"
            m 2lksdlb "Well, I'm glad that you're entertained..."
            m 2ekd "...but that's not {i}quite{/i} what I had in mind."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_sweet",
            prompt="You're really sweet!",
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

    m 1ekbsb "Aww, [player]..."
    m 3rkbssdlu "I don't know what to say, ahaha...{w=0.3}{nw}"
    extend 3ekbsa "it's {i}you{/i} who's been so sweet to me all this time."
    m 3hubsa "I'm just really happy to hear you say that, ehehe~"

    menu:
        "Your words always brighten my day!":
            $ mas_gainAffection(3, bypass=True)
            m 1sud "[player]..."
            extend 1eka "I had no idea how much my words meant to you..."
            m 1ekblb "I'm so happy to have such an amazing [bf] like you, [mas_get_player_nickname(exclude_names=[player])]~"
            m 1ekbsu "You really are the best I could ever hope for...{w=0.2}I just love you so much."
            m 3kua "I hope you never forget that, [player]."
            $ mas_ILY()

        "You're really special to me, [m_name]!":
            $ mas_gainAffection(3, bypass=True)
            m 1ekbsb "Oh, [player]...{w=0.3} {nw}"
            extend 3hubsa "Just you spending your time here with me makes me feel so happy and loved!"
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "I'm really happy you feel that way about me, [mas_get_player_nickname()]. I love you so much."
            $ mas_ILY()

        "You're the sweetest girl I've ever met!":
            $ mas_gainAffection(2, bypass=True)
            m 1ekbsa "Thank you, [mas_get_player_nickname()]."
            m 3hubsb "You're the sweetest [boy] I've met, ehehe."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "I'm really lucky to be with you~"

    return

label mas_compliment_sweet_repeat:
    python:
        sweet_quips = [
            _("I'm so happy to hear you say that, [player]!"),
            _("Hearing that always warms my heart, [player]!"),
            _("You make me feel so loved, [player]!"),
        ]
        sweet_quip = renpy.substitute(random.choice(sweet_quips))

    m 3hubsb "[sweet_quip]"
    m 1hubfu "...But I could never be as sweet as you~"
    return

# this compliment's lock/unlock is controlled by the def outfit pp
init 5 python:
    addEvent(
        Event(
            persistent._mas_compliments_database,
            eventlabel="mas_compliment_outfit",
            prompt="I love your outfit!",
            unlocked=False
        ),
        code="CMP"
    )

label mas_compliment_outfit:
    if mas_getEVL_shown_count("mas_compliment_outfit"):
        jump mas_compliment_outfit_repeat

    m 1hubsb "Thank you, [mas_get_player_nickname()]!"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        m 3hubsb "It's always fun cosplaying!"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        m 3hubsb "It's always fun wearing costumes!"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        m 2lkbsb "I was really nervous showing you this at first..."
        m 7tubsu "But I'm glad I did, you seem to really like it~"

    else:
        m 1hubsa "I've always wanted to wear other clothes for you, so I'm very happy that you think so!"

    menu:
        "You look beautiful in anything you wear!":
            $ mas_gainAffection(5, bypass=True)
            m 2subsd "[player]..."
            m 3hubsb "Thank you so much!"
            m 1ekbsu "You always make me feel so special."
            show monika 5hubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubsa "I love you, [mas_get_player_nickname()]!"
            $ mas_ILY()

        "You look really cute.":
            $ mas_gainAffection(3, bypass=True)
            m 1hubsb "Ahaha~"
            m 3hubfb "Thanks, [mas_get_player_nickname()]!"
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "I'm glad you like what you see~"

        "Wearing different clothes really helps.":
            $ mas_loseAffection()
            m 2ltd "Uh, thanks..."

    return

label mas_compliment_outfit_repeat:
    m 1hubsb "[mas_compliments.thanks_quip]"

    if monika_chr.is_wearing_clothes_with_exprop("cosplay"):
        python:
            cosplay_quips = [
                _("I love cosplaying for you!"),
                _("I'm happy you like this cosplay!"),
                _("I'm happy to cosplay for you!"),
            ]
            cosplay_quip = random.choice(cosplay_quips)

        m 3hubsb "[cosplay_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("costume"):
        python:
            clothes_quips = [
                _("I'm glad you like how I look with this!"),
                _("I'm happy you like how I look in this!"),
            ]
            clothes_quip = random.choice(clothes_quips)

        m 3hubsb "[clothes_quip]"

    elif monika_chr.is_wearing_clothes_with_exprop("lingerie"):
        python:
            lingerie_quips = [
                _("Glad you like what you see~"),
                _("Would you like a closer look?"),
                _("Would you like a little peek?~"),
            ]
            lingerie_quip = random.choice(lingerie_quips)

        m 2kubsu "[lingerie_quip]"
        show monika 5hublb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hublb "Ahaha!"

    else:
        python:
            other_quips = [
                _("I'm rather proud of my fashion sense!"),
                _("I'm sure you look good too!"),
                _("I love this outfit!")
            ]
            other_quip = random.choice(other_quips)

        m 3hubsb "[other_quip]"

    return
