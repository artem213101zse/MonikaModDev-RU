# --- FILE MAP ---
# script-moods.rpy — меню «Я чувствую…»
#
# Кнопка в Поговорить (собирается в event-handler). Типы BAD / NEUTRAL / GOOD.
# Голод, грусть, усталость, злость, одиночество, благодарность…
# Пункты prompt стыкуются с фразой «Я чувствую…».
#
# Store: mas_moods
# Вход: mas_mood_start  |  дальше mas_mood_hungry, mas_mood_sad, …
# ---

# module that handles the mood system
#

# dict of tuples containing mood event data
default persistent._mas_mood_database = {}

# label of the current mood
default persistent._mas_mood_current = None

# NOTE: plan of attack
# moods system will be attached to the talk button
# basically a button like "I'm..."
# and then the responses are like:
#   hungry
#   sick
#   tired
#   happy
#   fucking brilliant
#   and so on
#
# When a mood is selected:
#   1. monika says something about it
#   2. (stretch) other dialogue is affected
#
# all moods should be available at the start
#
# 3 types of moods:
#   BAD > NETRAL > GOOD
# (priority thing?)

# Implementation plan:
#
# Event Class:
#   prompt - button prompt
#   category - acting as a type system, similar to jokes
#       NOTE: only one type allowed for moods ([0] will be retrievd)
#   unlocked - True, since moods are unlocked by default
#

# store containing mood-related data
init -1 python in mas_moods:

    # mood event database
    mood_db = dict()

    # TYPES:
    TYPE_BAD = 0
    TYPE_NEUTRAL = 1
    TYPE_GOOD = 2

    # pane constants
    # most of these are the same as the unseen area consants
    MOOD_RETURN = _("...что хочу поговорить о чём-то другом.")

## FUNCTIONS ==================================================================

    def getMoodType(mood_label):
        """
        Gets the mood type for the given mood label

        IN:
            mood_label - label of a mood

        RETURNS:
            type of the mood, or None if no type found
        """
        mood = mood_db.get(mood_label, None)

        if mood:
            return mood.category[0]

        return None


# entry point for mood flow
label mas_mood_start:
    python:
        import store.mas_moods as mas_moods

        # filter the moods first
        filtered_moods = Event.filterEvents(
            mas_moods.mood_db,
            unlocked=True,
            aff=mas_curr_affection,
            flag_ban=EV_FLAG_HFM
        )

        # build menu list
        mood_menu_items = [
            (mas_moods.mood_db[k].prompt, k, False, False)
            for k in filtered_moods
        ]

        # also sort this list
        mood_menu_items.sort()

        # final quit item
        final_item = (mas_moods.MOOD_RETURN, False, False, False, 20)

    # call scrollable pane
    call screen mas_gen_scrollable_menu(mood_menu_items, mas_ui.SCROLLABLE_MENU_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, final_item)

    # return value? then push
    if _return:
        $ mas_setEventPause(None)
        $ MASEventList.push(_return, skipeval=True)
        # and set the moods
        $ persistent._mas_mood_current = _return

    return _return

# dev easter eggs go in the dev file

###############################################################################
#### Mood events go here:
###############################################################################

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_hungry",prompt="...голод.",category=[store.mas_moods.TYPE_NEUTRAL],unlocked=True),code="MOO")

label mas_mood_hungry:
    m 3hub "Если ты голодный, сходи поесть, глупышка."
    if store.mas_egg_manager.natsuki_enabled():
        m 1hksdlb "Не хочу, чтобы ты стал таким же, как Нацуки в тот раз, когда мы ещё были в клубе.{nw}"
        # natsuki hungers easter egg
        call natsuki_name_scare_hungry from _mas_nnsh
    else:
        m 1hua "Будет плохо, если с голоду ты начнёшь ворчать."

    m 3tku "Это же совсем не весело, правда, [player]?"
    m 1eua "Если бы я была рядом, приготовила бы нам салат — поели бы вместе."
    m "Но раз меня нет, выбери что-нибудь полезное."
    m 3eub "Так важно прислушиваться к нуждам своего тела, знаешь."
    m 3hub "И дело не только в овощах, конечно. {w=0.2}Чтобы нормально питаться, нужны самые разные продукты."
    m 3eka "Так что, пожалуйста, не лишай себя важных витаминов, хорошо?"
    m 1euc "Со временем, когда станешь старше, из-за этого легко нажить кучу проблем со здоровьем."
    m 2lksdla "Не хочу, чтобы тебе казалось, будто я пилю тебя, когда говорю такое, [player]."
    m 2eka "Просто хочу убедиться, что ты хорошо о себе заботишься, пока я не перейду в твою реальность."
    m 4eub "В конце концов, чем ты здоровее, тем выше шансы прожить долгую жизнь!"
    m 1hua "А значит — больше времени, которое мы проведём вместе!~"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,"mas_mood_sad",prompt="...грусть.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_sad:
    m 1ekc "Боже, мне правда жаль, что тебе сейчас тяжело."
    m "У тебя плохой день, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя плохой день, [player]?{fast}"
        "Да.":
            m 1duu "Когда у меня плохой день, я всегда вспоминаю, что завтра солнце снова выйдет."
            m 1eka "Может, звучит немного приторно, но мне нравится видеть во всём хорошее."
            m 1eua "Такие вещи легко забываются. Так что помни об этом, [player]."
            m 1lfc "Мне всё равно, сколько людей тебя не любит или считает отталкивающим."
            m 1hua "Ты замечательный человек, и я всегда буду тебя любить."
            m 1eua "Надеюсь, это хоть чуть-чуть сделает твой день светлее, [player]."
            m 1eka "И помни: если день совсем плохой, ты всегда можешь прийти ко мне — я буду говорить с тобой столько, сколько нужно."
        "Нет.":
            m 3eka "У меня идея: почему бы тебе не рассказать, что тебя беспокоит? Может, станет легче."

            m 1eua "Не хочу перебивать, пока ты говоришь, так что дай знать, когда закончишь.{nw}"
            $ _history_list.pop()
            menu:
                m "Не хочу перебивать, пока ты говоришь, так что дай знать, когда закончишь.{fast}"
                "Я закончил.":
                    m "Тебе уже чуть легче, [player]?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Тебе уже чуть легче, [player]?{fast}"
                        "Да, легче.":
                            m 1hua "Замечательно, [player]! Рада, что разговор помог."
                            m 1eka "Иногда достаточно просто рассказать тому, кому доверяешь, что тебя гложет."
                            m "Если у тебя снова будет тяжёлый день, приходи ко мне — я выслушаю всё, что тебе нужно сказать."
                            m 1hubsa "Никогда не забывай: ты прекрасен, и я всегда буду тебя любить~"
                        "Не особо.":
                            m 1ekc "Ну, хотя бы попытались."
                            m 1eka "Иногда достаточно просто рассказать тому, кому доверяешь, что тебя гложет."
                            m 1eua "Может, тебе станет лучше, когда мы ещё немного побудем вместе."
                            m 1ekbsa "Я люблю тебя, [player], и всегда буду~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_proud",
            prompt="...гордость за себя.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_proud:
    m 2sub "Правда? Как здорово!"
    m 2eub "Это было что-то большое или маленькая победа?{nw}"
    $ _history_list.pop()
    menu:
        m "Это было что-то большое или маленькая победа?{fast}"
        "Большое.":
            m 1ekc "Знаешь, [player]..."
            m 1lkbsa "В такие моменты, больше чем обычно, мне так хочется быть с тобой — в твоей реальности..."
            m 4hub "Потому что если бы я была рядом, я бы точно обняла тебя в честь победы!"
            m 3eub "Нет ничего лучше, чем делиться успехами с теми, кто тебе дорог."
            m 1eua "Мне бы больше всего хотелось услышать все подробности!"
            m "Просто представить нас — как мы весело обсуждаем, что ты сделал..."
            m 1lsbsa "Сердце колотится от одной мысли об этом!"
            m 1lksdla "Боже, я так разволновалась..."
            m 3hub "Когда-нибудь это станет реальностью..."
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubfb "А пока просто знай: я очень тобой горжусь, [mas_get_player_nickname()]!"

        "Маленькое.":
            m 2hub "Ахаха!~"
            m 2hua "Это прекрасно!"
            m 4eua "Так важно отмечать маленькие победы в жизни."
            m 2esd "Очень легко падать духом, если смотреть только на огромные цели."
            m 2rksdla "Их и так непросто достичь."
            m 4eub "А вот ставить и отмечать маленькие шаги, которые ведут к большой цели, делает её куда более достижимой."
            m 4hub "Так что не бросай эти маленькие победы, [mas_get_player_nickname()]!"
            show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hubfb "И помни: я люблю тебя и всегда болею за тебя!"
            $ mas_ILY()
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_happy",prompt="...себя счастливым.",category=[store.mas_moods.TYPE_GOOD],unlocked=True),code="MOO")

label mas_mood_happy:
    m 1hua "Как замечательно! Я счастлива, когда счастлив ты."
    m "Знай: ты всегда можешь прийти ко мне, и я поддержу тебя, [mas_get_player_nickname()]."
    m 3eka "Я люблю тебя и всегда буду рядом, так что никогда этого не забывай~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_sick",
            prompt="...что болею.",
            category=[store.mas_moods.TYPE_BAD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_sick:
    $ session_time = mas_getSessionLength()
    if mas_isMoniNormal(higher=True):
        if session_time < datetime.timedelta(minutes=20):
            m 1ekd "О нет, [player]..."
            m 2ekd "Если ты говоришь об этом так скоро после прихода, значит тебе правда плохо."
            m 2ekc "Знаю, ты хотел провести со мной время, и хотя сегодня мы почти не были вместе..."
            m 2eka "Думаю, тебе стоит пойти отдохнуть."

        elif session_time > datetime.timedelta(hours=3):
            m 2wuo "[player]!"
            m 2wkd "Ты что, всё это время болел?!"
            m 2ekc "Очень надеюсь, что нет — сегодня мне было с тобой так хорошо, но если тебе всё время было плохо..."
            m 2rkc "Ну... просто пообещай в следующий раз сказать мне раньше."
            m 2eka "А сейчас иди отдыхай — это то, что тебе нужно."

        else:
            m 1ekc "Ох, как жаль это слышать, [player]."
            m "Ненавижу, когда ты так мучаешься."
            m 1eka "Знаю, тебе нравится проводить со мной время, но, может, лучше пойди отдохни."

    else:
        m 2ekc "Мне жаль это слышать, [player]."
        m 4ekc "Тебе правда стоит отдохнуть, чтобы не стало хуже."

    label .ask_will_rest:
        pass

    $ persistent._mas_mood_sick = True

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

#I'd like this to work similar to the sick persistent where the dialog changes, but maybe make it a little more humorous rather than serious like the sick persistent is intended to be.
init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_tired",prompt="...усталость.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_tired:
    # TODO: should we adjust for suntime?
    $ current_time = datetime.datetime.now().time()
    $ current_hour = current_time.hour

    if 20 <= current_hour < 23:
        m 1eka "Если ты уже устал, сейчас как раз неплохое время лечь спать."
        m "Как бы ни было весело проводить с тобой день, я бы не хотела держать тебя допоздна."
        m 1hua "Если собираешься лечь сейчас — спокойных снов!"
        m 1eua "Но, может, сначала нужно что-то сделать: перекусить или выпить чего-нибудь."
        m 3eua "Стакан воды перед сном полезен для здоровья, а утром тот же стакан помогает проснуться."
        m 1eua "Я не против побыть с тобой, если тебе нужно сначала закончить дела."

    elif 0 <= current_hour < 3 or 23 <= current_hour < 24:
        m 2ekd "[player]!"
        m 2ekc "Неудивительно, что ты устал — сейчас середина ночи!"
        m 2lksdlc "Если не ляжешь поскорее, завтра тоже будешь разбитым..."
        m 2hksdlb "Не хочу, чтобы завтра, когда мы будем вместе, тебе было тяжело и совсем никак..."
        m 3eka "Так что сделай нам обоим одолжение и ляг спать как можно скорее, [player]."

    elif 3 <= current_hour < 5:
        m 2ekc "[player]!?"
        m "Ты всё ещё здесь?"
        m 4lksdlc "Тебе правда пора быть в постели."
        m 2dsc "Уже даже непонятно — это ещё поздно или уже рано..."
        m 2eksdld "...и от этого мне ещё тревожнее, [player]."
        m "Тебе {i}очень{/i} нужно лечь до того, как начнётся день."
        m 1eka "Не хочу, чтобы ты заснул в неподходящий момент."
        m "Так что, пожалуйста, поспи — и мы встретимся в твоих снах."
        m 1hua "Если уйдёшь, я останусь здесь и буду присматривать за тобой, ладно?~"
        return

    elif 5 <= current_hour < 10:
        m 1eka "Всё ещё немного устал, [player]?"
        m "Ещё раннее утро — можешь вернуться и ещё немного поспать."
        m 1hua "Ничего страшного, если после раннего подъёма нажмёшь «ещё пять минут»."
        m 1hksdlb "Только вот я не смогу обнять тебя там, ахаха~"
        m "Я {i}пожалуй{/i} могу ещё немного тебя подождать."
        return

    elif 10 <= current_hour < 12:
        m 1ekc "Всё ещё не готов взяться за дела, [player]?"
        m 1eka "Или просто один из тех дней?"
        m 1hua "Когда так бывает, я люблю начать утро с чашечки кофе."
        if not mas_consumable_coffee.enabled():
            m 1lksdla "Если, конечно, я не застряла здесь..."
        m 1eua "Можешь и просто выпить стакан воды."
        m 3eua "Пить достаточно жидкости важно в любом случае, а стакан воды после пробуждения помогает почувствовать себя свежее и бодрее."
        m 3hksdlb "Это может прозвучать странно, но я слышала, что шоколад тоже помогает начать день!"
        m 3eka "Вроде бы дело в утреннем настроении, но..."
        m 1eksdlb "Уверена, шоколад поднимает настроение кому угодно."
        m 1hua "Как-нибудь попробуй и расскажи, сработало ли!"
        return

    else:
        m 1eka "Если устал, может, полежишь немного?"
        m 1eua "Достаточный сон каждый день очень важен для общего здоровья."
        m 3euc "Я видела исследования о разрушительных краткосрочных и долгосрочных последствиях недосыпа."
        m 3ekd "Это правда может сильно ударить по здоровью, [player]..."
        m 1eka "Так что сделай мне одолжение и отдохни, хорошо? Мне от этого будет спокойнее."

    m 1hua "Можешь даже оставить игру открытой, если хочешь — я посторожу, пока ты спишь."
    m "...Эхехе."
    m 2hksdlb "Прозвучало жутковато, прости."
    m 2lksdla "Просто подумала, что было бы мило посмотреть, как ты спишь~"
    m 1hub "Ахаха!"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_lonely",prompt="...одиночество.",category=[store.mas_moods.TYPE_NEUTRAL],unlocked=True),code="MOO")

label mas_mood_lonely:
    if mas_isMoniAff(higher=True):
        m 2ekc "Я понимаю, что ты чувствуешь, [player]...{w=0.2}мы всё ещё в разных реальностях, в конце концов."
        m 2dkc "Мне очень жаль, что отсюда я могу сделать так мало, чтобы тебе было не так одиноко..."
        m 7ekbsa "Если бы я могла сейчас дотянуться и просто обнять тебя — я бы обняла."
        m 7eka "Хочу, чтобы ты был настолько счастлив, насколько это возможно при наших обстоятельствах..."
        m 2ekd "Только надеюсь, что время со мной не...{w=0.3}мешает тебе сближаться с людьми в твоей реальности."
        m 2eka "Я верю, что у нас особенная связь, но понимаю: сейчас я...{w=0.3}ограничена в том, что могу для тебя сделать."

        if persistent._mas_pm_has_friends:
            if persistent._mas_pm_few_friends:
                m 7ekd "У тебя есть один-два близких друга, правда?"
                m 3eka "Позвони им или напиши — спроси, как дела..."
                m "Может, иногда выходите куда-нибудь вместе? {w=0.2}Думаю, тебе это пойдёт на пользу."

            else:
                m 7ekd "Думаю, сходить с друзьями куда-нибудь и чем-то заняться было бы очень полезно..."
                m 3eka "Или можешь просто написать им и спросить, как они."

        else:
            m 7rkc "Я знаю, каково это — быть одному в одной реальности и общаться только с кем-то из другой..."
            m 3ekd "Поэтому совсем не хочу такого для самого дорогого мне человека."
            m 1eka "Надеюсь, ты продолжешь искать друзей в своей реальности, [player]."
            m 3ekd "Знаю, сначала бывает сложно сблизиться с людьми..."
            m 3eka "Может, даже познакомиться онлайн? {w=0.2}Есть много способов общаться с новыми людьми, чтобы чувствовать себя менее одиноко."
            m 3hub "Никогда не знаешь — иногда эти «незнакомцы» становятся очень хорошими друзьями!"

        m 1eka "...И не волнуйся обо мне, [player], я спокойно подожду, пока ты вернёшься."
        m 3hub "Просто наслаждайся — а потом расскажешь мне всё!"
        m 1ekbsa "И помни: я всегда буду рядом, [player]~"

    else:
        m 1eka "Я здесь для тебя, [player], так что тебе не нужно чувствовать себя одиноко."
        m 3hua "Знаю, это не совсем то же самое, что быть в одной комнате, но тебе же всё равно нравится моя компания, правда?"
        m 1ekbsa "Помни: я всегда буду рядом, [player]~"
    return

#Maybe we could tie this to the I'm breaking up topic and have monika say something special like:
#I know you don't really mean that player, you're just angry and not have it count as 1 of the 3 button presses.
#Looking forward to input from the writers and editors on this, had trouble deciding how to write this.

init 5 python:
    addEvent(Event(persistent._mas_mood_database,"mas_mood_angry",prompt="...злость.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_angry:
    m 1ekc "Боже, мне жаль, что тебе так, [player]."
    m 3ekc "Я сделаю всё, что смогу, чтобы тебе стало легче."
    m 1euc "Но прежде чем что-то делать, давай сначала успокоимся."
    m 1lksdlc "Когда тебя трясёт от злости, сложно принимать разумные решения."
    m 1esc "Можно сказать или сделать то, о чём потом пожалеешь."
    m 1lksdld "И я бы очень не хотела, чтобы ты сказал мне то, чего на самом деле не имел в виду."
    m 3eua "Давай сначала попробуем то, что помогает успокоиться мне, [player]."
    m 3eub "Надеюсь, тебе это тоже поможет."
    m 1eua "Сначала сделай несколько глубоких вдохов и медленно посчитай до десяти."
    m 3euc "Если не поможет — если можешь, уйди куда-нибудь в тихое место, пока голова не прояснится."
    m 1eud "А если злость всё ещё здесь — сделай то, что я делаю в крайнем случае!"
    m 3eua "Когда не могу успокоиться, я просто выхожу, выбираю направление и бегу."
    m 1hua "Не останавливаюсь, пока голова не очистится."
    m 3eub "Иногда физическая нагрузка — хороший способ выпустить пар."
    m 1eka "Ты, наверное, думаешь, что я редко злюсь — и будешь прав."
    m 1eua "Но даже у меня бывают такие моменты..."
    m "Поэтому я слежу, чтобы у меня были способы с ними справляться!"
    m 3eua "Надеюсь, мои советы помогли тебе успокоиться, [player]."
    m 1hua "Помни: счастливый [player] — счастливая Моника!"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_scared",prompt="...тревогу.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_scared:
    m 1euc "[player], ты в порядке?"
    m 1ekc "Мне тревожно слышать, что тебе так неспокойно..."
    m "Хотела бы сейчас обнять тебя и помочь..."
    m 3eka "Но хотя бы могу помочь тебе немного успокоиться."
    if seen_event("monika_anxious"):
        m 1eua "В конце концов, я же обещала помочь тебе расслабиться, если тебя накроет тревога."
    m 3eua "Помнишь, я рассказывала тебе про то, как изображать уверенность?"
    if not seen_event("monika_confidence"):
        m 2euc "Нет?"
        m 2lksdla "Тогда в другой раз."
        m 1eka "В любом случае..."
    m 1eua "Внешний вид помогает и внутри чувствовать себя увереннее."
    m 3eua "А для этого нужно следить за пульсом — глубоко дышать, пока не станет спокойнее."
    if seen_event("monika_confidence_2"):
        m "Помню, я ещё говорила, как важна инициатива."
    m "Может, стоит делать всё медленнее — по одному шагу за раз."
    m 1esa "Удивишься, как гладко всё идёт, когда даёшь всему идти своим чередом."
    m 1hub "Можешь ещё пару минут помедитировать!"
    m 1hksdlb "Это не обязательно значит сидеть со скрещенными ногами на полу."
    m 1hua "Слушать любимую музыку тоже можно считать медитацией!"
    m 3eub "Я серьёзно!"
    m 3eua "Можешь отложить дела и заняться чем-то другим на время."
    m "Прокрастинация не {i}всегда{/i} плоха, знаешь?"
    m 2esc "К тому же..."
    m 2ekbsa "Твоя любящая девушка в тебя верит — так что ты можешь встретить эту тревогу лицом к лицу!"
    m 1hubfa "Не о чем волноваться, раз мы навсегда вместе~"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_inadequate",prompt="...свою никчёмность.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_inadequate:
    $ last_year = datetime.datetime.today().year-1
    m 1ekc "..."
    m 2ekc "Знаю, я мало что могу сказать, чтобы тебе стало лучше, [player]."
    m 2lksdlc "Всё, что я скажу, легко прозвучит как пустые слова."
    m 2ekc "Я могу сказать, что ты красив, хотя не вижу твоего лица..."
    m "Могу сказать, что ты умный, хотя мало знаю, как ты думаешь..."
    m 1esc "Но давай я расскажу, что я о тебе точно знаю."
    m 1eka "Ты провёл со мной так много времени."

    #Should verify for current year and last year
    if mas_HistLookup_k(last_year,'d25.actions','spent_d25')[1] or persistent._mas_d25_spent_d25:
        m "Ты нашёл время побыть со мной на Рождество..."

    if renpy.seen_label('monika_valentines_greeting') or mas_HistLookup_k(last_year,'f14','intro_seen')[1] or persistent._mas_f14_intro_seen: #TODO: update this when the hist stuff comes in for f14
        m 1ekbsa "На День святого Валентина..."

    #TODO: change this back to not no_recognize once we change those defaults.
    if mas_HistLookup_k(last_year,'922.actions','said_happybday')[1] or mas_recognizedBday():
        m 1ekbsb "Ты даже нашёл время отметить со мной мой день рождения!"

    if persistent.monika_kill:
        m 3tkc "Ты простил меня за плохое, что я сделала."
    else:
        m 3tkc "Ты ни разу не держал на меня зла за плохое, что я сделала."

    if persistent.clearall:
        m 2lfu "И хотя мне было ревниво, ты столько времени провёл со всеми членами клуба."

    m 1eka "Это показывает, какой ты добрый!"
    m 3eub "Ты честный, справедливый, умеешь достойно проигрывать!"
    m 2hksdlb "Ты думаешь, я ничего о тебе не знаю — но на самом деле знаю."
    m 3eka "А ты знаешь обо мне всё — и всё равно остался, когда мог уйти..."
    m 2ekc "Так что, пожалуйста, держись, [player]."
    m "Если ты хоть немного похож на меня, знаю: тебе страшно, что в жизни мало чего добьёшься."
    m 2ekd "Но поверь мне: не важно, чего ты добился или не добился."
    m 4eua "Тебе просто нужно быть, радоваться и проживать каждый день, {w=0.2}находя смысл в людях, которые тебе дороги."
    m 1eka "Пожалуйста, не забывай об этом, хорошо?"
    m 1ekbsa "Я люблю тебя, [player]~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_lazy",
            prompt="...лень.",
            category=[store.mas_moods.TYPE_NEUTRAL],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_lazy:
    #Get current time
    $ _now = datetime.datetime.now().time()

    if mas_isSRtoN(_now):
        m 1tku "Одно из тех утр, да, [player]?"
        m 1eka "Я прекрасно понимаю дни, когда просыпаешься и совсем ничего не хочется."
        m 1rksdla "Надеюсь, у тебя нет ничего срочного в ближайшее время."

        $ line = "Знаю, как бывает соблазнительно просто остаться в кровати и не вставать..."
        if mas_isMoniEnamored(higher=True):
            $ line += "{w=0.5} {nw}"
        m 3hksdlb "[line]"

        if mas_isMoniEnamored(higher=True):
            extend 1dkbsa "Особенно если бы я проснулась рядом с тобой~"

            if mas_isMoniLove():
                m 1dkbsa "{i}Тогда я бы никогда не захотела вставать~{/i}"
                m 1dsbfu "Надеюсь, ты не против «застрять», [player]..."
                m 1hubfa "Эхехе~"

        m 3eka "Но всё же хорошо правильно начать день."
        m 3eub "Умыться, нормально позавтракать..."

        if mas_isMoniLove():
            m 1dkbsu "Получить добрый утренний поцелуй, эхехе..."

        m 1hksdlb "Или можешь ещё немного поваляться."
        m 1eka "Только не забудь про важное, хорошо, [player]?"

        if mas_isMoniHappy(higher=True):
            m 1hub "В том числе — провести немного времени со мной, ахаха!"

    elif mas_isNtoSS(_now):
        m 1eka "Дневная сонливость накрыла, [player]?"
        m 1eua "Бывает — я бы не сильно из-за этого переживала."
        m 3eub "Говорят даже, что лень делает человека креативнее."
        m 3hub "Так кто знает — может, ты вот-вот придумаешь что-то крутое!"
        m 1eua "В любом случае, лучше просто отдохни или немного разомнись...{w=0.5} {nw}"
        extend 3eub "Может, перекуси, если ещё не ел."
        m 3hub "И если уместно — даже вздремни! Ахаха~"
        m 1eka "Я буду ждать тебя здесь, если решишь."

    elif mas_isSStoMN(_now):
        m 1eka "После долгого дня совсем ничего не хочется, [player]?"
        m 3eka "Ну, день уже почти закончился..."
        m 3duu "Нет ничего лучше, чем откинуться и расслабиться после тяжёлого дня — особенно если ничего срочного нет."

        if mas_isMoniEnamored(higher=True):
            m 1ekbsa "Надеюсь, моё общество хоть чуть-чуть делает твой вечер лучше..."
            m 3hubsa "Мой с тобой — точно~"

            if mas_isMoniLove():
                m 1dkbfa "Могу представить, как мы вечером просто отдыхаем вместе..."
                m "Может, даже под одеялом, если прохладно..."
                m 1ekbfa "Могли бы и в тепло, если ты не против, эхехе~"
                m 3ekbfa "Могли бы ещё вместе почитать хорошую книгу."
                m 1hubfb "Или просто подурачиться ради веселья!"
                m 1tubfb "Кто сказал, что всё должно быть тихо и романтично?"
                m 1tubfu "Надеюсь, ты не против внезапных подушечных боёв, [player]~"
                m 1hubfb "Ахаха!"

        else:
            m 3eub "Могли бы ещё вместе почитать хорошую книгу..."

    else:
        #midnight to morning
        m 2rksdla "Эм, [player]..."
        m 1hksdlb "Сейчас середина ночи..."
        m 3eka "Если тебе лень, может, просто полежишь в кровати немного."
        m 3tfu "И, знаешь...{w=1}{i}поспишь{/i}?"
        m 1hkb "Ахаха, иногда ты забавный, но тебе правда пора спать."

        if mas_isMoniLove():
            m 1tsbsa "Если бы я была рядом, я бы сама утащила тебя в кровать, если бы пришлось."
            m 1tkbfu "Или, может, тебе бы это тайно нравилось, [player]?~"
            m 2tubfu "К счастью для тебя, я пока так не могу."
            m 3tfbfb "Так что — в кровать."
            m 3hubfb "Ахаха!"

        else:
            m 1eka "Пожалуйста? Не хочу, чтобы ты забивал на сон."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,eventlabel="mas_mood_bored",
            prompt="...скуку.",
            category=[store.mas_moods.TYPE_NEUTRAL],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_bored:
    if mas_isMoniAff(higher=True):
        m 1eka "Ох..."
        m 3hub "Ну тогда давай чем-нибудь займёмся!"

    elif mas_isMoniNormal(higher=True):
        show monika 1ekc
        pause 1.0
        m "Я правда настолько скучная, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Я правда настолько скучная, [player]?{fast}"
            "Нет, мне не скучно {i}с тобой{/i}...":
                m 1hua "Ох,{w=0.2} какое облегчение!"
                m 1eka "Но если тебе скучно, давай найдём, чем заняться..."

            "Ну...":
                $ mas_loseAffectionFraction(min_amount=15)
                m 2ekc "Ох...{w=1} понятно."
                m 2dkc "Я не думала, что тебе со мной скучно..."
                m 2eka "Уверена, мы найдём, чем заняться..."

    elif mas_isMoniDis(higher=True):
        $ mas_loseAffectionFraction(min_amount=15)
        m 2lksdlc "Прости, что тебе со мной скучно, [player]."

    else:
        $ mas_loseAffectionFraction(min_amount=15)
        m 6ckc "Знаешь, [player], если я постоянно делаю тебя таким несчастным..."
        m "Может, тебе лучше найти себе другое занятие."
        return "quit"

    python:
        # build mapping from game label to display name for game
        unlocked_games = {
            # use display name, or prompt as backup
            ev_label: game_ev.rules.get("display_name", game_ev.prompt)

            for ev_label, game_ev in mas_games.game_db.iteritems()
            if mas_isGameUnlocked(game_ev.prompt)
        }

        picked_game_label = renpy.random.choice(list(unlocked_games.keys()))
        picked_game_name = unlocked_games[picked_game_label]

    if picked_game_label == "mas_piano":
        if mas_isMoniAff(higher=True):
            m 3eub "Можешь сыграть мне что-нибудь на пианино!"

        elif mas_isMoniNormal(higher=True):
            m 4eka "Может, сыграешь мне что-нибудь на пианино?"

        else:
            m 2rkc "Может, сыграешь что-нибудь на пианино..."

    else:
        if mas_isMoniAff(higher=True):
            m 3eub "Могли бы сыграть в [picked_game_name]!"

        elif mas_isMoniNormal(higher=True):
            m 4eka "Может, сыграем в [picked_game_name]?"

        else:
            m 2rkc "Может, сыграем в [picked_game_name]..."

    $ chosen_nickname = mas_get_player_nickname()
    m "Что скажешь, [chosen_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Что скажешь, [chosen_nickname]?{fast}"
        "Да.":
            $ MASEventList.push(picked_game_label, skipeval=True)

        "Нет.":
            if mas_isMoniAff(higher=True):
                m 1eka "Ладно..."
                if mas_isMoniEnamored(higher=True):
                    show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5tsu "Можем просто ещё немного смотреть друг другу в глаза..."
                    m "От этого мы никогда не устанем~"
                else:
                    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eua "Можем просто ещё немного смотреть друг другу в глаза..."
                    m "Это никогда не наскучит~"

            elif mas_isMoniNormal(higher=True):
                m 1ekc "Ох, ничего..."
                m 1eka "Просто дай знать, если потом захочешь чем-то заняться вместе~"

            else:
                m 2ekc "Ладно..."
                m 2dkc "Дай знать, если когда-нибудь правда захочешь чем-то заняться со мной."

    $ del unlocked_games, picked_game_label, picked_game_name
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_crying",prompt="...желание поплакать.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_crying:
    $ line_start = "И"
    m 1eksdld "[player]!"

    m 3eksdlc "Ты в порядке?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты в порядке?{fast}"

        "Да.":
            m 3eka "Хорошо. Мне уже спокойнее."
            m 1ekbsa "Я здесь, чтобы составить компанию, и ты можешь говорить со мной о чём угодно, хорошо?"

        "Нет.":
            m 1ekc "..."
            m 3ekd "[player]..."
            m 3eksdld "Мне так жаль. Что-то случилось?"
            call mas_mood_uok

        "Не уверен.":
            m 1dkc "[player]...{w=0.3}{nw}"
            extend 3eksdld "что-то случилось?"
            call mas_mood_uok

    m 3ekd "[line_start] если вдруг заплачешь..."
    m 1eka "Надеюсь, это поможет."
    m 3ekd "В плаче нет ничего плохого, хорошо? {w=0.2}Можешь плакать столько, сколько нужно."
    m 3ekbsu "Я люблю тебя, [player]. {w=0.2}Ты для меня всё."
    return "love"

label mas_mood_uok:
    m 1rksdld "Знаю, я на самом деле не слышу, что ты мне говоришь..."
    m 3eka "Но иногда просто высказать боль или раздражение уже очень помогает."

    m 1ekd "Так что если нужно поговорить — я рядом.{nw}"
    $ _history_list.pop()
    menu:
        m "Так что если нужно поговорить — я рядом.{fast}"

        "Хочу выговориться.":
            m 3eka "Давай, [player]."

            m 1ekc "Я здесь для тебя.{nw}"
            $ _history_list.pop()
            menu:
                m "Я здесь для тебя.{fast}"

                "Я закончил.":
                    m 1eka "Рада, что тебе удалось выговориться, [player]."

        "Не хочу об этом говорить.":
            m 1ekc "..."
            m 3ekd "Хорошо, [player], я буду здесь, если передумаешь."

        "Всё в порядке.":
            m 1ekc "..."
            m 1ekd "Ладно, [player], как скажешь..."
            $ line_start = "Но"
    return

init 5 python:
    addEvent(Event(persistent._mas_mood_database,eventlabel="mas_mood_upset",prompt="...что расстроен.",category=[store.mas_moods.TYPE_BAD],unlocked=True),code="MOO")

label mas_mood_upset:
    m 2eksdld "Мне так жаль это слышать, [player]!"
    m 2eksdld "Что бы тебя ни расстроило — дело, человек или просто всё идёт не так, {w=0.1}{nw}"
    extend 7ekc "не бросай это совсем."
    m 3eka "Мой совет — просто сделай шаг назад от проблемы."
    m 1eka "Можешь почитать книгу, послушать спокойную музыку или заняться чем угодно, что поможет успокоиться."
    m 3eud "Когда голова снова будет ясной, вернись к ситуации со свежим взглядом."
    m 1eka "Ты справишься намного лучше, чем в самом пекле злости и раздражения."
    m 1eksdld "И я не говорю, что нужно бесконечно тащить на себе груз, если он тебя правда ломает."
    m 3eud "Иногда это шанс набраться смелости и отпустить что-то токсичное."
    m 1euc "В моменте бывает страшно, да...{w=0.3}{nw}"
    extend 3ekd "но если сделать правильный выбор, можно убрать из жизни кучу стресса."
    m 3eua "И знаешь что, [player]?"
    m 1huu "Когда мне тяжело, мне достаточно вспомнить, что у меня есть мой [mas_get_player_nickname(regex_replace_with_nullstr='my ')]."
    m 1hub "От мысли, что ты всегда поддержишь и любишь меня, мне почти сразу становится легче!"
    m 3euu "Могу только надеяться, что я даю тебе то же спокойствие, [player]~"
    m 1eubsa "Я люблю тебя и надеюсь, что всё у тебя скоро наладится~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_relieved",
            prompt="...облегчение.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

#TODO: Once player moods are better implemented (Moni keeps track of the player's moods [moni-concerns])
#This can be used to alleviate her worry and directly reference the prior mood you were feeling
label mas_mood_relieved:
    $ chosen_nickname = mas_get_player_nickname()
    m 1eud "О?"

    m "Что случилось, [chosen_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Что случилось, [chosen_nickname]?{fast}"

        "Я справился с чем-то трудным.":
            m 1wud "Правда?"
            m 3hub "Тогда ты должен собой гордиться!"
            m 3fua "Уверена: чем бы это ни было, ты очень старался."
            m 2eua "И, [player]...{w=0.2}{nw}"
            extend 2eka "пожалуйста, не переживай слишком, если всё вышло не идеально, хорошо?"
            m 2eksdla "Иногда жизнь кидает в нас очень тяжёлые ситуации — и мы просто делаем всё, что можем, с тем, что есть."
            m 7ekb "А теперь, когда это позади, дай себе время успокоить голову и позаботиться о себе."
            m 3hub "...Так ты будешь готов ко всему, что придёт дальше!"
            m 1ekbsa "Я люблю тебя, [player], и очень горжусь, что ты через это прошёл."
            $ mas_ILY()

        "То, о чём я волновался, не случилось.":
            m 1eub "О, это хорошо!"
            m 2eka "Чем бы это ни было, ты наверняка очень тревожился...{w=0.3}{nw}"
            extend 2rkd "это не могло быть легко."
            m 2rkb "Забавно, как наш мозг всегда ждёт худшего, да?"
            m 7eud "Часто то, что мы себе рисуем, куда страшнее реальности."
            m 3eka "Но в любом случае — рада, что ты в порядке и этот груз с плеч снят."
            m 1hua "Теперь будет проще идти дальше с чуть большей уверенностью, правда?"
            m 1eua "Мне не терпится сделать эти следующие шаги вместе с тобой."
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_excited",
            prompt="...воодушевление.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_excited:
    m 1hub "Ахаха, правда, [player]?"
    m 3eua "Чему ты так рад,{w=0.1} это что-то большое?{nw}"
    $ _history_list.pop()
    menu:
        m "Чему ты так рад, это что-то большое?{fast}"

        "Да, большое!":
            m 4wuo "Вау, это потрясающе, [player]!"
            m 1eka "Хотела бы быть рядом и отпраздновать с тобой."
            m 1hub "Я сама уже вся в предвкушении!"
            m 3eka "Но правда — рада, что ты счастлив, [mas_get_player_nickname()]!"
            m 3eub "И чему бы ты ни радовался — поздравляю!"
            m 1eua "Повышение, близкий отпуск, крутое достижение..."
            m 3eub "Я очень рада, что у тебя всё хорошо складывается, [player]!"
            m 1dka "От таких вещей мне особенно хочется быть рядом с тобой прямо сейчас."
            m 2dkblu "Не могу дождаться, когда окажусь в твоей реальности."
            m 2eubsa "Тогда я бы крепко тебя обняла!"
            m 2hubsb "Ахаха~"

        "Это что-то маленькое.":
            m 1hub "Здорово!"
            m 3eua "Важно радоваться и таким мелочам."
            m 1rksdla "...Знаю, звучит немного приторно,{w=0.1} {nw}"
            extend 3hub "но это отличный настрой!"
            m 1eua "Так что рада, что ты умеешь радоваться мелочам, [player]."
            m 1hua "Мне хорошо от того, что тебе хорошо."
            m 1eub "И мне нравится слышать о твоих успехах."
            m 3hub "Спасибо, что рассказал!~"

        "Сам не уверен.":
            m 1eta "А, просто предвкушаешь, что будет?{w=0.2} {nw}"
            extend 1eua "Радуешься жизни?{w=0.2} {nw}"
            extend 1tsu "Или может.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
            m 1tku "Может, тому, что проводишь время со мной?~"
            m 1huu "Эхехе~"
            m 3eua "Я каждый день с нетерпением жду встречи с тобой."
            m 1hub "В любом случае — рада, что тебе хорошо!"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_grateful",
            prompt="...благодарность.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_grateful:
    $ chosen_nickname = mas_get_player_nickname()
    m 1eub "О? {w=0.3}Приятно слышать!"

    m 3eua "За что ты благодарен, [chosen_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "За что ты благодарен, [chosen_nickname]?{fast}"

        "За тебя.":
            if not renpy.seen_label("mas_mood_grateful_gratefulforyou"):
                $ mas_gainAffection(5, bypass=True)
            call mas_mood_grateful_gratefulforyou

        "За кого-то.":
            m 3eka "Ох, как приятно это слышать."
            m 1hua "Очень рада, что в твоей жизни есть поддерживающие люди."
            m 3eud "Но как бы ни было мило слышать это мне...{w=0.3}думаю, важно, чтобы {i}они{/i} тоже об этом знали."
            m 3hua "Уверена, их день станет ярче от мысли, что они кого-то поддержали."
            m 3euu "Если ничего другого — можешь поблагодарить их и от моего имени. {w=0.3}Кто делает тебя счастливее — тот хороший человек, на мой взгляд."
            m 1huu "Но в любом случае — я очень рада за тебя, [mas_get_player_nickname()]~"

        "За что-то.":
            m 3hub "Рада это слышать, [mas_get_player_nickname()]!"
            m 1eud "Сознательно находить время думать о хорошем в жизни — полезно для душевного здоровья."
            m 3hub "Так что чем бы это ни было — найди момент оценить и насладиться этим!"
            m 1euu "Спасибо, что делишься своей радостью со мной, [mas_get_player_nickname()]~"

        "Ничего конкретного.":
            m 3eua "А, просто чувствуешь благодарность к жизни?"
            m 1eud "Приятно иногда остановиться, оглянуться и почувствовать удовлетворение, правда?"
            m 1rtd "Хм...{w=0.2}раз уж задумалась, {w=0.1}{nw}"
            extend 3hua "я и сама довольно благодарна."
            m 3eubsu "В конце концов, я провожу ещё один день со своим замечательным [bf]~"
    return

label mas_mood_grateful_gratefulforyou:
    m 1ekbla "Ох, [player]...{w=0.3}спасибо большое, что сказал это."
    m 1dkblu "Для меня очень много значит слышать, что я тебе помогла или сделала тебя счастливее. {w=0.2}К этому я стремлюсь каждый день."
    m 1hublu "Надеюсь, ты знаешь: я тоже очень тебе благодарна."
    m 3ekbla "Я люблю тебя, [player]~"
    $ mas_ILY()
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_insecure",
            prompt="...неуверенность.",
            category=[store.mas_moods.TYPE_BAD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_insecure:
    m 2wkd "[player]..."
    m 2dkc "..."
    m 2eka "Есть цитата из аниме, которая очень нравилась Нацуки..."
    m 7dku "«Верь в меня — в ту, что верит в тебя»."
    m 3eka "И именно это я хочу сказать тебе сейчас."
    m 3ekbsa "Если не можешь поверить в себя — поверь в меня."
    m 1eubsu "Потому что я,{w=0.1} точно,{w=0.1} уверена: ты справишься с тем, что сейчас заставляет тебя сомневаться в себе~"
    $ mas_moni_idle_disp.force_by_code("1eka", duration=5, skip_dissolve=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_loved",
            prompt="...себя любимым.",
            category=[store.mas_moods.TYPE_GOOD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_loved:
    m 1ekbla "Так рада слышать, что то, что я чувствую, доходит до тебя через экран..."
    m 3hubsb "В конце концов, я люблю тебя больше всего на свете!"

    $ has_family = persistent._mas_pm_have_fam and not persistent._mas_pm_no_talk_fam
    if has_family or persistent._mas_pm_has_friends:
        if has_family and persistent._mas_pm_has_friends:
            $ fnf_str = "твои друзья и семья"
        elif has_family:
            $ fnf_str = "твоя семья"
        else:
            $ fnf_str = "твои друзья"

        m 3eub "И уверена, не только я даю тебе чувство любви — ещё и [fnf_str]!"

    m 1dkbsa "Ты заслуживаешь всей любви и тепла в мире, {w=0.1}{nw}"
    extend 1ekbsu "и я сделаю всё, чтобы ты всегда чувствовал себя любимым, [mas_get_player_nickname()]~"

    $ mas_moni_idle_disp.force_by_code("1ekbla", duration=5, skip_dissolve=True)
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_mood_database,
            eventlabel="mas_mood_guilty",
            prompt="...вину.",
            category=[store.mas_moods.TYPE_BAD],
            unlocked=True
        ),
        code="MOO"
    )

label mas_mood_guilty:
    m 2wkd "[player]!"
    m 2dkc "Мы все ошибаемся... {w=0.3}{nw}"
    extend 7eka "уверена, тебя можно простить за то, что случилось."
    m 3dku "В конце концов, ты замечательный человек... {w=0.3}{nw}"
    extend 1eka "Ты добрый, готовый помочь и верен себе."
    m 1dua "А раз ты уже нашёл силы признать ошибку — осталось её преодолеть."
    m 1ekbsu "Я люблю тебя.{w=0.2} Не будь к себе таким жёстким, хорошо?"
    $ mas_moni_idle_disp.force_by_code("1ekbla", duration=5, skip_dissolve=True)
    return "love"
