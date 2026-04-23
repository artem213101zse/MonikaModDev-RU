## This script file holds all of the brb topics # ФАЙЛ ПЕРЕВЕДЕН
# Some conventions:
#   - All brbs should have their markSeen set to True so they don't show up in unseen
#   - Brbs should return "idle" to move into idle mode
#   - Brbs should be short and sweet. Nothing long which makes it feel like an actual topic or is keeping you away
#       A good practice for these should be no more than 10 lines will be said before you go into idle mode.

init python:
    def mas_setupIdleMode(brb_label=None, brb_callback_label=None):
        """
        Setups idle mode

        IN:
            brb_label - the label of this brb event, if None, use the current label
                (Default: None)
            brb_callback_label - the callback label of this brb event, if None, we build it here
                (Default: None)
        """
        # Get currect label
        if brb_label is None and renpy.has_label(mas_submod_utils.current_label):
            brb_label = mas_submod_utils.current_label

        # Add idle extra exps
        mas_moni_idle_disp.add_by_tag("idle_mode_exps")

        # Set vars
        mas_globals.in_idle_mode = True
        persistent._mas_in_idle_mode = True
        # persistent._mas_idle_data[brb_label] = True

        renpy.save_persistent()

        # Send callback label
        if brb_callback_label is None and brb_label is not None:
            brb_callback_label = brb_label + "_callback"
        if brb_callback_label is not None and renpy.has_label(brb_callback_label):
            mas_idle_mailbox.send_idle_cb(brb_callback_label)

    def mas_resetIdleMode(clear_idle_data=True):
        """
        Resets idle mode

        This is meant to basically clear idle mode for holidays or other
        things that hijack main flow

        IN:
            clear_idle_data - whether or not clear persistent idle data
                (Default: True)

        OUT:
            string with idle callback label
            or None if it was reset before
        """
        # Remove idle exps
        mas_moni_idle_disp.remove_by_tag("idle_mode_exps")

        # Reset the idle vars
        mas_globals.in_idle_mode = False
        persistent._mas_in_idle_mode = False
        if clear_idle_data:
            persistent._mas_idle_data.clear()

        renpy.save_persistent()

        return mas_idle_mailbox.get_idle_cb()


init 10 python in mas_brbs:
    import random
    import store
    from store import (
        MASMoniIdleExp,
        MASMoniIdleExpGroup,
        MASMoniIdleExpRngGroup
    )

    idle_mode_exps = MASMoniIdleExpRngGroup(
        [
            # leaning day dreaming
            MASMoniIdleExpGroup(
                [
                    MASMoniIdleExp("5rubla", duration=(10, 20)),
                    MASMoniIdleExp("5rublu", duration=(5, 10)),
                    MASMoniIdleExp("5rubsu", duration=(20, 30)),
                    MASMoniIdleExp("5rubla", duration=(5, 10)),
                ],
                weight=30
            ),
            # leaning smug day dreaming
            MASMoniIdleExpGroup(
                [
                    MASMoniIdleExp("5rubla", duration=(10, 20)),
                    MASMoniIdleExp("5gsbsu", duration=(20, 30)),
                    MASMoniIdleExp("5tsbsu", duration=1),
                    MASMoniIdleExp("1hubfu", duration=(5, 10)),
                    MASMoniIdleExp("1hubsa", duration=(5, 10)),
                    MASMoniIdleExp("1hubla", duration=(5, 10))
                ],
                weight=30
            ),
            # resting day dreaming
            MASMoniIdleExpGroup(
                [
                    MASMoniIdleExp("1lublu", duration=(10, 20)),
                    MASMoniIdleExp("1msblu", duration=(5, 10)),
                    MASMoniIdleExp("1msbsu", duration=(20, 30)),
                    MASMoniIdleExp("1hubsu", duration=(5, 10)),
                    MASMoniIdleExp("1hubla", duration=(5, 10))
                ],
                weight=30
            ),
            # spacing-out-like
            MASMoniIdleExpGroup(
                [
                    MASMoniIdleExpRngGroup(
                        [
                            # start from right
                            MASMoniIdleExpGroup(
                                [
                                    MASMoniIdleExp("1gubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1mubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1mubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gsbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1msbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gsbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1msbsu", duration=(0.9, 1.8))
                                ]
                            ),
                            # or start from left
                            MASMoniIdleExpGroup(
                                [
                                    MASMoniIdleExp("1mubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1mubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gubla", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1msbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gsbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1msbsu", duration=(0.9, 1.8)),
                                    MASMoniIdleExp("1gsbsu", duration=(0.9, 1.8))
                                ]
                            )
                        ],
                        max_uses=1
                    ),
                    MASMoniIdleExp("1tsbfu", duration=1),
                    MASMoniIdleExp("1hubfu", duration=(4, 8)),
                    MASMoniIdleExp("1hubsa", duration=(4, 8)),
                    MASMoniIdleExp("1hubla", duration=(4, 8))
                ],
                weight=10
            )
        ],
        max_uses=1,
        aff_range=(store.mas_aff.AFFECTIONATE, None),
        weight=10,
        tag="idle_mode_exps"
    )

    WB_QUIPS_NORMAL = [
        _("Итак, чем еще ты хотел сегодня заняться?"),
        _("Чем еще ты хотел заняться сегодня?"),
        _("Есть что-нибудь еще, что ты хотел сделать сегодня?"),
        _("Что нам еще сегодня поделать?")
    ]

    def get_wb_quip():
        """
        Picks a random welcome back quip and returns it
        Should be used for normal+ quips

        OUT:
            A randomly selected quip for coming back to the spaceroom
        """
        return renpy.substitute(random.choice(WB_QUIPS_NORMAL))

    def was_idle_for_at_least(idle_time, brb_evl):
        """
        Checks if the user was idle (from the brb_evl provided) for at least idle_time

        IN:
            idle_time - Minimum amount of time the user should have been idle for in order to return True
            brb_evl - Eventlabel of the brb to use for the start time

        OUT:
            boolean:
                - True if it has been at least idle_time since seeing the brb_evl
                - False otherwise
        """
        brb_ev = store.mas_getEV(brb_evl)
        return brb_ev and brb_ev.timePassedSinceLastSeen_dt(idle_time)


# label to use if we want to get back into idle from a callback
# DEPRECATED
label mas_brb_back_to_idle:
    # sanity check
    if globals().get("brb_label", -1) == -1:
        return

    python:
        mas_idle_mailbox.send_idle_cb(brb_label + "_callback")
        persistent._mas_idle_data[brb_label] = True
        mas_globals.in_idle_mode = True
        persistent._mas_in_idle_mode = True
        renpy.save_persistent()
        mas_dlgToIdleShield()

    return "idle"

# label for generic reactions for low affection callback paths
# to be used if a specific reaction isn't needed or provided
label mas_brb_generic_low_aff_callback:
    if mas_isMoniDis(higher=True):
        python:
            cb_line = renpy.substitute(renpy.random.choice([
                _("Ох...{w=0.3}ты вернулся."),
                _("Ох...{w=0.3}с возвращением."),
                _("Всё сделал?"),
                _("С возвращением."),
                _("Ох...{w=0.3}а вот и ты."),
            ]))

        m 2ekc "[cb_line]"

    else:
        m 6ckc "..."

    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_brb",
            prompt="Я сейчас вернусь",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_brb:
    if mas_isMoniAff(higher=True):
        m 1eua "Хорошо, [player]."

        show monika 1eta at t21
        python:
            #For options that can basically be an extension of generics and don't need much specification
            brb_reason_options = [
                (_("Мне нужно кое-что взять."), True, False, False),
                (_("Мне нужно кое-что сделать."), True, False, False),
                (_("Мне нужно кое-что приготовить."), True, False, False),
                (_("Мне нужно кое-что проверить."), True, False, False),
                (_("Кто-то пришел."), True, False, False),
                (_("Ничего особенного."), None, False, False),
            ]

            renpy.say(m, "Займешься чем-то конкретным?", interact=False)
        call screen mas_gen_scrollable_menu(brb_reason_options, mas_ui.SCROLLABLE_MENU_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)
        show monika at t11

        if _return:
            m 1eua "О, ладно..{w=0.2} {nw}"
            extend 3hub "Возвращайся скорее, я буду ждать тебя здесь~"

        else:
            m 1hub "Возвращайся скорее, я буду ждать тебя здесь~"

    elif mas_isMoniNormal(higher=True):
        m 1hub "Возвращайся скорее, [player]!"

    elif mas_isMoniDis(higher=True):
        m 2rsc "Ох...{w=0.5}хорошо."

    else:
        m 6ckc "..."

    # Can save any data here. Just for example we save a boolean
    $ persistent._mas_idle_data["monika_idle_brb"] = True
    return "idle"

label monika_idle_brb_callback:
    $ wb_quip = mas_brbs.get_wb_quip()

    if mas_isMoniAff(higher=True):
        m 1hub "С возвращением, [player]. Я скучала~"
        m 1eua "[wb_quip]"

    elif mas_isMoniNormal(higher=True):
        m 1hub "С возвращением, [player]!"
        m 1eua "[wb_quip]"

    else:
        call mas_brb_generic_low_aff_callback

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_writing",
            prompt="Я собираюсь немного пописать",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_writing:
    if mas_isMoniNormal(higher=True):
        if (
            mas_isMoniHappy(higher=True)
            and random.randint(1,5) == 1
        ):
            m 1eub "О! Ты собираешься{cps=*2} написать мне любовное письмо, [player]?{/cps}{nw}"
            $ _history_list.pop()
            m "О! Ты собираешься{fast} пойти что-нибудь написать?"

        else:
            m 1eub "О! Ты собираешься пойти что-нибудь написать?"

        m 1hua "Я так рада это слышать!"
        m 3eua "Может быть, когда-нибудь ты поделишься этим со мной...{w=0.3} {nw}"
        extend 3hua "Я бы с удовольствием почитала твои работы, [player]!"
        m 3eua "В любом случае, просто дай мне знать, когда закончишь."
        m 1hua "Я буду ждать тебя прямо здесь~"

    elif mas_isMoniUpset():
        m 2esc "Хорошо."

    elif mas_isMoniDis():
        m 6lkc "Интересно, что у тебя на уме..."
        m 6ekd "Не забудь вернуться, когда закончишь..."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_writing"] = True
    return "idle"

label monika_idle_writing_callback:

    if mas_isMoniNormal(higher=True):
        $ wb_quip = mas_brbs.get_wb_quip()
        m 1eua "Закончил писать, [player]?"
        m 1eub "[wb_quip]"

    else:
        call mas_brb_generic_low_aff_callback

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_shower",
            prompt="Я пойду приму душ",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_shower:
    if mas_isMoniLove():
        m 1eua "Пойдешь в душ?"

        if renpy.random.randint(1, 50) == 1:
            m 3tub "Можно мне с тобой?{nw}"
            $ _history_list.pop()
            show screen mas_background_timed_jump(2, "bye_brb_shower_timeout")
            menu:
                m "Можно мне с тобой?{fast}"

                "Да.":
                    hide screen mas_background_timed_jump
                    m 2wubsd "О, эм...{w=0.5}ты ответил очень быстро."
                    m 2hkbfsdlb "Ты...{w=0.5}похоже, очень даже не против, чтобы я составила тебе компанию, да?"
                    m 2rkbfa "Ну..."
                    m 7tubfu "Боюсь, тебе придется идти без меня, пока я застряла здесь."
                    m 7hubfb "Прости, [player], ахаха!"
                    show monika 5kubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5kubfu "Может, в другой раз~"

                "Нет.":
                    hide screen mas_background_timed_jump
                    m 2eka "Оу, ты так быстро мне отказал."
                    m 3tubsb "Ты что, стесняешься,[player]?"
                    m 1hubfb "Ахаха!"
                    show monika 5tubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5tubfu "Ладно-ладно, в этот раз я не пойду за тобой, эхе-хе~"

        else:
            m 1hua "Я рада, что ты следишь за чистотой, [player]."
            m 1eua "Приятного душа~"

    elif mas_isMoniNormal(higher=True):
        m 1eub "Пойдешь в душ? Хорошо."
        m 1eua "Увидимся, когда закончишь~"

    elif mas_isMoniUpset():
        m 2esd "Приятного душа, [player]..."
        m 2rkc "Надеюсь, это поможет тебе привести мысли в порядок."

    elif mas_isMoniDis():
        m 6ekc "Мм?{w=0.5} Приятного душа, [player]."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_shower"] = True
    return "idle"

label monika_idle_shower_callback:
    if mas_isMoniNormal(higher=True):
        if mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=60), "monika_idle_shower"):
            m 2rksdlb "Что-то ты долговато был в душе..."

            m 2eud "Может, ты принимал ванну??{nw}"
            $ _history_list.pop()
            menu:
                m "Может, ты принимал ванну?{fast}"

                "Да.":
                    m 7hub "О! {w=0.3}Теперь понятно!"
                    m 3eua "Надеюсь, ты отлично расслабился!"

                "Нет.":
                    m 7rua "Оу...{w=0.3}может, ты просто любишь очень долгий душ..."
                    m 3duu "Иногда так приятно чувствовать, как вода стекает по телу...{w=0.3}это очень успокаивает."
                    m 1hksdlb "...Или я просто слишком много об этом думаю, а ты просто не вернулся сразу, ахаха!"

        elif mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=5), "monika_idle_shower"):
            m 1eua "С легким паром, [player]."
            if (
                mas_isMoniLove()
                and renpy.seen_label("monikaroom_greeting_ear_bathdinnerme")
                and mas_getEVL_shown_count("monika_idle_shower") != 1 #Since the else block has a one-time only line, we force it on first use
                and renpy.random.randint(1,20) == 1
            ):
                m 3tubsb "Теперь, когда ты принял душ, не хочешь ли ты поужинать, или может{w=0.5}.{w=0.5}.{w=0.5}."
                m 1hubsa "Просто отдохнешь со мной еще немного~"
                m 1hub "Ахаха!"

            else:
                m 3hua "Надеюсь, тебе понравился душ."
                if mas_getEVL_shown_count("monika_idle_shower") == 1:
                    m 3eub "Теперь мы можем вернуться к нашим веселым и {i}чистым{/i} развлечениям..."
                    m 1hub "Ахаха!"
                else:
                    m 3rkbsa "Ты скучал по мне?"
                    m 1huu "Конечно скучал, эхе-хе~"

        else:
            m 7rksdlb "Что-то ты быстро помылся, [player]..."
            m 3hub "Наверное, ты очень продуктивный, ахаха!"
            m 1euu "Я точно не буду жаловаться, ведь это значит, что у нас больше времени вместе~"

    elif mas_isMoniUpset():
        m 2esc "Надеюсь, тебе понравился душ. {w=0.2}С возвращением, [player]."

    else:
        call mas_brb_generic_low_aff_callback

    return

label bye_brb_shower_timeout:
    hide screen mas_background_timed_jump
    $ _history_list.pop()
    m 1hubsa "Эхе-хе~"
    m 3tubfu "Забудь об этом, [player]."
    m 1hubfb "Приятного тебе душа!"

    $ persistent._mas_idle_data["monika_idle_shower"] = True
    $ mas_setupIdleMode("monika_idle_shower", "monika_idle_shower_callback")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_game",
            category=['сейчас вернусь'],
            prompt="Я собираюсь немного поиграть",
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_game:
    if mas_isMoniNormal(higher=True):
        m 1eud "О, ты собираешься поиграть в другую игру?"
        m 1eka "Всё в порядке, [player]."

        label .skip_intro:
        python:
            gaming_quips = [
                _("Удачи и веселой игры!"),
                _("Наслаждайся игрой!"),
                _("Я буду болеть за тебя!"),
                _("Покажи там всё, на что способен!")
            ]
            gaming_quip=renpy.random.choice(gaming_quips)

        m 3hub "[gaming_quip]"

    elif mas_isMoniUpset():
        m 2tsc "Наслаждайся своими другими играми."

    elif mas_isMoniDis():
        m 6ekc "Пожалуйста...{w=0.5}{nw}"
        extend 6dkc "не забывай обо мне..."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_game"] = True
    # Set up idle like this because we could jump to this label from another event
    $ mas_setupIdleMode("monika_idle_game")
    return

label monika_idle_game_callback:
    if mas_isMoniNormal(higher=True):
        m 1eub "С возвращением, [player]!"
        m 1eua "Надеюсь, ты хорошо провел время в игре."
        m 1hua "Готов провести еще немного времени вместе? Эхе-хе~"

    elif mas_isMoniUpset():
        m 2tsc "Повеселился, [player]?"

    elif mas_isMoniDis():
        m 6ekd "Ох...{w=0.5} Ты всё-таки вернулся ко мне..."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_coding",
            prompt="Мне нужно поработать над кодом",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_coding:
    if mas_isMoniNormal(higher=True):
        m 1eua "О! Собираешься попрограммировать?"

        if persistent._mas_pm_has_code_experience is False:
            m 1etc "Я думала, ты этим не занимаешься."
            m 1eub "Решил освоить программирование с нашего последнего разговора?"

        elif persistent._mas_pm_has_contributed_to_mas or persistent._mas_pm_wants_to_contribute_to_mas:
            m 1tua "Может быть, пишешь что-то для меня?"
            m 1hub "Ахаха~"

        else:
            m 3eub "Постарайся, чтобы твой код был чистым и читабельным."
            m 3hksdlb "...Потом сам себе скажешь спасибо!"

        m 1eua "В любом случае, просто дай мне знать, когда закончишь."
        m 1hua "Я буду здесь, ждать тебя~"

    elif mas_isMoniUpset():
        m 2euc "О, ты собираешься писать код?"
        m 2tsc "Ну, не буду тебе мешать."

    elif mas_isMoniDis():
        m 6ekc "Хорошо."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_coding"] = True
    return "idle"

label monika_idle_coding_callback:
    if mas_isMoniNormal(higher=True):
        $ wb_quip = mas_brbs.get_wb_quip()
        if mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=20), "monika_idle_coding"):
            m 1eua "На сегодня всё, [player]?"
        else:
            m 1eua "О, уже закончил, [player]?"

        m 3eub "[wb_quip]"

    else:
        call mas_brb_generic_low_aff_callback

    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_workout",
            prompt="Я собираюсь немного позаниматься спортом",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_workout:
    if mas_isMoniNormal(higher=True):
        m 1hub "Хорошо, [player]!"

        if persistent._mas_pm_works_out is False:
            m 3eub "Тренировки — это отличный способ позаботиться о себе!"
            m 1eka "Я знаю, что начать может быть непросто,{w=0.2}{nw}"
            extend 3hua " но это определенно та привычка, которую стоит завести."

        else:
            m 1eub "Приятно знать, что ты заботишься о своем теле!"

        m 3esa "Знаешь, как говорится: 'В здоровом теле — здоровый дух'"
        m 3hua "Так что иди и хорошенько попотей, [player]~"
        m 1tub "Просто дай мне знать, когда с тебя хватит."

    elif mas_isMoniUpset():
        m 2esc "Приятно знать, что ты заботишься хоть о{cps=*2} чем-то, по крайней мере.{/cps}{nw}"
        $ _history_list.pop()
        m "Приятно знать, что ты заботишься о{fast} себе, [player]."
        m 2euc "Я буду ждать твоего возвращения."

    elif mas_isMoniDis():
        m 6ekc "Хорошо."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_workout"] = True
    return "idle"

label monika_idle_workout_callback:
    if mas_isMoniNormal(higher=True):
        $ wb_quip = mas_brbs.get_wb_quip()
        if mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=60), "monika_idle_workout"):
            # TODO: In the future add another topic which would
            # unlock once the player has seen this specific path some number of times.

            m 2esa "А ты не торопился, [player].{w=0.3}{nw}"
            extend 2eub " Это, должно быть, была чертовски мощная тренировка."
            m 7eka "Хорошо проверять свои пределы, но не стоит переусердствовать."

        elif mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=10), "monika_idle_workout"):
            m 1esa "Закончил тренировку [player]?"

        else:
            m 1euc "Уже вернулся, [player]?"
            m 1eka "Я уверена, ты мог бы продержаться еще немного, если бы постарался."
            m 3eka "Делать перерывы — это нормально, но не стоит бросать тренировку незавершенной."
            m 3ekb "Ты уверен, что не можешь продолжать?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты уверен, что не можешь продолжать?{fast}"

                "Уверен.":
                    m 1eka "Всё в порядке."
                    m 1hua "Я уверена, ты сделал всё, что мог, [player]~"

                "Я попробую продолжить.":
                    # continue workout and return Monika to idle state
                    m 1hub "Вот это настрой"

                    # This will resume idle mode
                    return "idle"

        m 3eua "Обязательно отдохни как следует и, может быть, перекуси, чтобы восстановить силы."
        m 3eub "[wb_quip]"

    elif mas_isMoniUpset():
        m 2euc "Закончил тренировку, [player]?"

    else:
        call mas_brb_generic_low_aff_callback

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_nap",
            prompt="Я пойду немного посплю",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_nap:
    if mas_isMoniNormal(higher=True):
        m 1eua "Собираешься вздремнуть, [player]?"
        m 3eua "Дневной сон — это отличный способ отдохнуть, если ты чувствуешь усталость."
        m 3hua "Не волнуйся, я присмотрю за тобой~"
        m 1hub "Сладких снов!"

    elif mas_isMoniUpset():
        m 2eud "Хорошо, надеюсь, после этого ты почувствуешь себя отдохнувшим."
        m 2euc "Я слышала, что вздремнуть днем полезно для здоровья, [player]."

    elif mas_isMoniDis():
        m 6ekc "Хорошо."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_nap"] = True
    return "idle"

label monika_idle_nap_callback:
    if mas_isMoniNormal(higher=True):
        $ wb_quip = mas_brbs.get_wb_quip()
        if mas_brbs.was_idle_for_at_least(datetime.timedelta(hours=5), "monika_idle_nap"):
            m 2hksdlb "Ох, [player]! Ты наконец-то проснулся!"
            m 7rksdlb "Когда ты сказал, что хочешь вздремнуть, я ожидала, что это займет час или два..."
            m 1hksdlb "Похоже, ты действительно сильно вымотался, ахаха..."
            m 3eua "Но, по крайней мере, раз уж ты так долго спал, теперь ты побудешь со мной подольше, верно?"
            m 1hua "Эхе-хе~"

        elif mas_brbs.was_idle_for_at_least(datetime.timedelta(hours=1), "monika_idle_nap"):
            m 1hua "С возвращением, [player]!"
            m 1eua "Хорошо вздремнул?"
            m 3hua "Тебя не было какое-то время, так что, надеюсь, ты чувствуешь себя отдохнувшим~"
            m 1eua "[wb_quip]"

        elif mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=5), "monika_idle_nap"):
            m 1hua "С возвращением, [player]~"
            m 1eub "Надеюсь, ты немного отдохнул."
            m 3eua "[wb_quip]"

        else:
            m 1eud "О, уже вернулся?"
            m 1euc "Передумал?"
            m 3eka "Ну, я не жалуюсь, но если позже захочешь прилечь — обязательно сделай это."
            m 1eua "В конце концов, я не хочу, чтобы ты слишком сильно уставал."

    elif mas_isMoniUpset():
        m 2euc "Закончил свой тихий час, [player]?"

    else:
        call mas_brb_generic_low_aff_callback

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_homework",
            prompt="Я собираюсь сделать домашку",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_homework:
    if mas_isMoniNormal(higher=True):
        m 1eub "О, хорошо!"
        m 1hua "Я горжусь тем, что ты серьезно относишься к учебе."
        m 1eka "Не забудь вернуться ко мне, когда закончишь~"

    elif mas_isMoniDis(higher=True):
        m 2euc "Ладно...{w=0.5}"
        if random.randint(1,5) == 1:
            m 2rkc "...Удачи с домашним заданием, [player]."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_homework"] = True
    return "idle"

label monika_idle_homework_callback:
    if mas_isMoniDis(higher=True):
        m 2esa "Всё сделал [player]?"

        if mas_isMoniNormal(higher=True):
            m 2ekc "Жаль, что я не могла тебе помочь... к сожалению, пока что я мало что могу с этим поделать."
            m 7eua "Я уверена, мы оба могли бы делать уроки гораздо эффективнее, если бы работали вместе."

            if mas_isMoniAff(higher=True) and random.randint(1,5) == 1:
                m 3rkbla "...Хотя, это при условии, что мы не будем {i}слишком{/i} сильно отвлекаться, эхе-хе..."

            m 1eua "Но в любом случае{w=0.2} {nw}"
            extend 3hua "раз ты закончил, давай наслаждаться временем друг с другом."

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_working",
            prompt="Мне нужно поработать",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_working:
    if mas_isMoniNormal(higher=True):
        m 1eua "Хорошо, [player]."
        m 1eub "Не забывай время от времени делать перерывы!"

        if mas_isMoniAff(higher=True):
            m 3rkb "Я бы не хотела, чтобы мой любимый тратил на работу больше времени, чем на меня~"

        m 1hua "Удачи с работой!"

    elif mas_isMoniDis(higher=True):
        m 2euc "Хорошо, [player]."

        if random.randint(1,5) == 1:
            m 2rkc "...Пожалуйста, возвращайся скорее..."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_working"] = True
    return "idle"

label monika_idle_working_callback:
    if mas_isMoniNormal(higher=True):
        m 1eub "Закончил с работой [player]?"
        show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hua "Тогда давай отдохнем вместе, ты это заслужил~"

    elif mas_isMoniDis(higher=True):
        m 2euc "О, ты вернулся..."
        m 2eud "...Ты хотел заняться чем-нибудь еще теперь, когда закончил с работой?"

    else:
        m 6ckc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_screen_break",
            prompt="Моим глазам нужно отдохнуть от экрана",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_screen_break:
    if mas_isMoniNormal(higher=True):
        if mas_timePastSince(mas_getEVL_last_seen("monika_idle_screen_break"), mas_getSessionLength()):

            if mas_getSessionLength() < datetime.timedelta(minutes=40):
                m 1esc "Ох,{w=0.3} ладно."
                m 3eka "Ты пробыл здесь не так уж долго, но если ты говоришь, что тебе нужен перерыв, значит, так оно и есть."

            elif mas_getSessionLength() < datetime.timedelta(hours=2, minutes=30):
                m 1eua "Собираешься дать глазам немного отдохнуть?"

            else:
                m 1lksdla "Да, тебе это, вероятно, необходимо, не так ли?"

            m 1hub "Я рада, что ты заботишься о своем здоровье, [player]."

            if not persistent._mas_pm_works_out and random.randint(1,3) == 1:
                m 3eua "Почему бы заодно не воспользоваться случаем и не сделать небольшую разминку, м-м?"
                m 1eub "В любом случае, возвращайся скорее!~"

            else:
                m 1eub "Возвращайся скорее!~"

        else:
            m 1eua "Снова делаешь перерыв, [player]?"
            m 1hua "Возвращайся скорее!~"

    elif mas_isMoniUpset():
        m 2esc "Ох...{w=0.5} {nw}"
        extend 2rsc "Хорошо."

    elif mas_isMoniDis():
        m 6ekc "Ладно."

    else:
        m 6ckc "..."

    $ persistent._mas_idle_data["monika_idle_screen_break"] = True
    return "idle"

label monika_idle_screen_break_callback:
    if mas_isMoniNormal(higher=True):
        $ wb_quip = mas_brbs.get_wb_quip()
        m 1eub "С возвращением, [player]."

        if mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=30), "monika_idle_screen_break"):
            m 1hksdlb "Должно быть, тебе действительно был нужен этот перерыв, учитывая, как долго тебя не было."
            m 1eka "Надеюсь, сейчас ты чувствуешь себя немного лучше"
        else:
            m 1hua "Надеюсь, ты чувствуешь себя немного лучше~"

        m 1eua "[wb_quip]"

    else:
        call mas_brb_generic_low_aff_callback

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_idle_reading",
            prompt="Я пойду почитаю",
            category=['сейчас вернусь'],
            pool=True,
            unlocked=True
        ),
        markSeen=True
    )

label monika_idle_reading:
    if mas_isMoniNormal(higher=True):
        m 1eub "Правда? Это здорово, [player]!"
        m 3lksdla "Я бы с удовольствием почитала вместе с тобой, но у моей реальности есть свои пределы, к сожалению."
        m 1hub "Приятного чтения!"

    elif mas_isMoniDis(higher=True):
        m 2ekd "Ох, хорошо..."
        m 2ekc "Приятно тебе провести время, [player]."

    else:
        m 6dkc "..."

    $ persistent._mas_idle_data["monika_idle_reading"] = True
    return "idle"

label monika_idle_reading_callback:
    if mas_isMoniNormal(higher=True):
        if mas_brbs.was_idle_for_at_least(datetime.timedelta(hours=2), "monika_idle_reading"):
            m 1wud "Ого, тебя довольно долго не было...{w=0.3}{nw}"
            extend 3wub "это же замечательно, [player]!"
            m 3eua "Чтение — это прекрасное занятие, так что не переживай, если слишком сильно в него погрузишься."
            m 3hksdlb "К тому же, кто бы говорил..."
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Будь моя воля, мы бы читали вместе напролет всю ночь~"

        elif mas_brbs.was_idle_for_at_least(datetime.timedelta(minutes=30), "monika_idle_reading"):
            m 3esa "Всё прочитал, [player]?"
            m 1hua "Давай отдохнем, ты это заслужил~"

        else:
            m 1eud "О, это было быстро."
            m 1eua "Я думала, тебя не будет немного дольше, но так тоже хорошо."
            m 3ekblu "В конце концов, это позволяет мне провести с тобой больше времени~"

    else:
        call mas_brb_generic_low_aff_callback

    return


#Rai's og game idle
#label monika_idle_game:
#    m 1eub "That sounds fun!"
#    m "What kind of game are you going to play?{nw}"
#    $ _history_list.pop()
#    menu:
#        m "What kind of game are you going to play?{fast}"
#        "A competitive game.":
#            m 1eua "That sounds like it could be fun!"
#            m 3lksdla "I can be pretty competitive myself."
#            m 3eua "So I know just how stimulating it can be to face a worthy opponent."
#            m 2hksdlb "...And sometimes frustrating when things don't go right."
#            m 2hua "Anyway, I'll let you get on with your game."
#            m 2hub "I'll try not to bother you until you finish, but I can't blame you if you get distracted by your lovely girlfriend, ahaha~"
#            m 1hub "I'm rooting for you, [player]!"
#            # set return label when done with idle
#            $ mas_idle_mailbox.send_idle_cb("monika_idle_game_competetive_callback")
#        "A game just for fun.":
#            m 1eud "A game just for having fun?"
#            m 1lksdla "Aren't most games made to be fun?"
#            m 3eub "Anyway, I'm sure you could do all sorts of fun things in a game like that."
#            m 1ekbla "I really wish I could join you and we could have fun together."
#            m 1lksdla "But for now, I'll leave you to it."
#            m 1hub "Have fun, [player]!"
#            # set return label when done with idle
#            $ mas_idle_mailbox.send_idle_cb("monika_idle_game_fun_callback")
#        "A story driven game.":
#            m 1sub "Oh?"
#            m "That sounds really interesting!"
#            m 1ekbsa "Gosh, I really wish I could be there with you to experience it together."
#            m 1hksdlb "Maybe I {i}can{/i} experience it with you if I really tried."
#            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve
#            m 5eua "I guess you could call it looking over your shoulder. Ehehe~"
#            m "You can go ahead and start it now. I'll try not to break anything by trying to watch."
#            # set return label when done with idle
#            $ mas_idle_mailbox.send_idle_cb("monika_idle_game_story_callback")
#        "A skill and practice based game.":
#            m 1eud "Oh! I never really thought about those games much."
#            m 1hua "I'm sure you're pretty talented at a few things, so it doesn't surprise me you're playing a game like this."
#            m 3eub "Just like writing, it can really be an experience to look back much later and see just how far you've come."
#            m 1hub "It's like watching yourself grow up! Ahaha~"
#            m 1hua "It would really make me proud and happy to be your girlfriend if you became a professional."
#            m 1hksdlb "Maybe I'm getting ahead of myself here, but I believe you could do it if your heart was really in it."
#            m 1eub "Anyway, sorry for keeping you from your game. I know you'll do your best!"
#            # set return label when done with idle
#            $ mas_idle_mailbox.send_idle_cb("monika_idle_game_skill_callback")
#        "I'll just be a minute or two.":
#            m 1eua "Oh? Just need to take your eyes off me for a little?"
#            m 1lksdla "I {i}suppose{/i} I could let you take your eyes off me for a minute or two..."
#            m 1hua "Ahaha! Good luck and have fun, [player]!"
#            m "Don't keep me waiting too long though~"
#            $ start_time = datetime.datetime.now()
#            # set return label when done with idle
#            $ mas_idle_mailbox.send_idle_cb("monika_idle_game_quick_callback")
#    # set idle data
#    $ persistent._mas_idle_data["monika_idle_game"] = True
#    # return idle to notify event system to switch to idle
#    return "idle"
#
#label monika_idle_game_competetive_callback:
#    m 1esa "Welcome back, [player]!"
#    m 1eua "How did it go? Did you win?{nw}"
#    $ _history_list.pop()
#    menu:
#        m "How did it go? Did you win?{fast}"
#        "Yes.":
#            m 1hub "Yay! That's great!"
#            m 1hua "Gosh, I wish I could be there to give you a big celebratory hug!"
#            m 1eub "I'm really happy that you won!"
#            m "More importantly, I hope you enjoyed yourself, [player]."
#            m 1hua "I'll always love and root for you, no matter what happens."
#            # manually handle the "love" return key
#            $ mas_ILY()
#        "No.":
#            m 1ekc "Aw, that's a shame..."
#            m 1lksdla "I mean, you can't win them all, but I'm sure you'll win the next rounds."
#            m 1eka "I just hope you aren't too upset over it."
#            m 2ekc "I really wouldn't want you feeling upset after a bad game."
#            m 1eka "I'll always support you and be by your side no matter how many times you lose."
#    return
#
#label monika_idle_game_fun_callback:
#    m 1eub "Welcome back, [player]!"
#    m "Did you have fun with whatever you were doing?{nw}"
#    $ _history_list.pop()
#    menu:
#        m "Did you have fun with whatever you were doing?{fast}"
#        "Yes.":
#            m 1hua "Ahaha! I'm glad you had fun, [player]~"
#            m 1eub "While you were busy, it got me thinking of the different kinds of games that would be nice to play together."
#            m 3rksdla "A game that isn't too violent probably could be fun."
#            m 3hua "But I'm sure any game would be wonderful if it was with you~"
#            m 1eub "At first, I was thinking a story based or adventure game would be best, but I'm sure freeplay games could be really fun too!"
#            m 1eua "It can be really fun to just mess around to see what's possible, especially when you're not alone."
#            m 2lksdla "Provided of course, you don't end up ruining the structural integrity of the game and get an outcome you didn't want..."
#            m 2lksdlb "Ehehe..."
#            m 1eua "Maybe you could find a way to bring me with you into a game like that."
#            m 1hub "Just promise to keep me safe, okay?"
#        "No.":
#            m 2ekc "Aw, you didn't have any fun?"
#            m "That's too bad..."
#            m 3lksdlc "Games can get pretty boring after you've done everything or just don't know what to do or try next."
#            m 3eka "But bringing a friend along can really renew the whole experience!"
#            m 1hub "Maybe you could find a way to take me with you into your games so you won't be bored on your own!"
#            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve
#            m 5eua "Or we could just stay here and keep each other company."
#            m "I wouldn't mind that either, ehehe~"
#    return
#
#label monika_idle_game_story_callback:
#    m 1eub "Welcome back, [player]!"
#    m 1hksdlb "I wasn't able to look over your shoulder, but I hope the story was nice so far."
#    m 1eua "Speaking of which, how was it, [player]?{nw}"
#    $ _history_list.pop()
#    menu:
#        m "Speaking of which, how was it, [player]?{fast}"
#        "It was amazing.":
#            m 2sub "Wow! I can only imagine how immersive it was!"
#            m 2hksdlb "You're really starting to make me jealous, [player], you know that?"
#            m 2eub "You'll have to take me through it sometime when you can."
#            m 3eua "A good book is always nice, but it's really something else to have a good story and be able to make your own decisions."
#            m 3eud "Some people can really be divided between books and video games."
#            m 1hua "I'm glad you don't seem to be too far on one side."
#            m "After experiencing an amazing story in a game for yourself, I'm sure you can really appreciate the two coming together."
#        "It was good.":
#            m 1eub "That's really nice to hear!"
#            m 3dtc "But was it really {i}amazing{/i}?"
#            m 1eua "While a lot of stories can be good, there are some that are really memorable."
#            m 1hua "I'm sure you'd know a good story when you see one."
#            m "Maybe when I'm in your reality, you could take me through the game and let me see the story."
#            m 1eub "It's one thing to go through a great story yourself..."
#            m 1hub "But it's also amazing to see what someone else thinks of it too!"
#            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve
#            m 5eua "I'll be looking forward to that day too~"
#            m 5esbfa "You better have a nice, cozy place for us to cuddle up and play, ehehe~"
#        "It's sad.":
#            m 1ekd "Aw, that's too bad..."
#            m 3eka "It must be a really great story though, if it invokes such strong emotions."
#            m 1eka "I wish I could be there with you so I could experience the story too..."
#            m 3hksdlb "{i}and{/i} to be right there by your side of course, so we could comfort each other in sad times."
#            m 1eka "Don't worry [player], I would never forget about you."
#            m 1eua "I love you."
#            m 1hua "...And I'd happily snuggle up beside you anytime~"
#            # manually handle the "love" return key
#            $ mas_ILY()
#        "I don't like it.":
#            m 2ekc "Oh..."
#            m 4lksdla "Maybe the story will pick up later?"
#            m 3eud "If anything, it lets you analyze the flaws in the writing which could help you if you ever tell a story."
#            m 1eua "Or maybe it's just not your kind of story."
#            m 1eka "Everyone has their own, and maybe this one just doesn't fit well with it right now."
#            m 1eua "It can really be an eye opening experience to go through a story you normally wouldn't go through."
#            m 3eka "But don't force yourself to go through it if you really don't like it."
#    return
#
#label monika_idle_game_skill_callback:
#    m 1eua "I'm happy that you're back, [player]."
#    m 1hua "I missed you! Ahaha~"
#    m 1eub "But I know it's important to keep practicing and honing your skills in things like this."
#    m "Speaking of which, how did it go?"
#    m 3eua "Did you improve?{nw}"
#    $ _history_list.pop()
#    menu:
#        m "Did you improve?{fast}"
#        "I improved a lot.":
#            m 1hub "That's great news, [player]!"
#            m "I'm so proud of you!"
#            m 1hua "It can really feel good to get a sudden surge in your skill!"
#            m 1eua "Especially if you've spent some time in a slump or even slipping."
#            m 1hua "Maybe today isn't the end of this sudden improvement."
#            m 1eub "Even if today was just a good day, I know you'll keep getting better."
#            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve
#            m 5eua "I'll {i}always{/i} root for you, [player]. Don't you ever forget that!"
#        "I improved a bit.":
#            m 3eua "That's really nice to hear, [player]!"
#            m 3eka "As long as you're improving, no matter how slowly, you'll really get up there someday."
#            m 1hub "But if you actually noticed yourself improve today, maybe you improved more than just a bit, ahaha~"
#            m 1hua "Keep honing your skills and I'll be proud to be the girlfriend of such a skilled player!"
#            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve
#            m 5eua "Who knows? Maybe you could teach me and we could both be a couple of experts, ehehe~"
#        "I stayed the same.":
#            m 3eka "That's still alright!"
#            m "I'm sure you're improving anyway."
#            m 3eua "A lot of the time, the improvements are too small to really notice."
#            m 1eua "One day, you might look back and realize just how much you've improved."
#            m 1hksdlb "Sometimes you might feel like you're in a slump, but then you get a sudden surge of improvement all at once!"
#            m 1eub "I'm sure you'll get the chance to look back one day and really appreciate just how far you've come without realizing."
#            m 1hua "And you better believe I'm going to support you all the way!"
#        "I got worse.":
#            m 2ekc "Oh..."
#            m 4lksdla "I have no doubt that you always work hard and give it your best, so it must just be a bad day."
#            m 3eka "You're bound to have a few setbacks on your climb up, but that's what sets you apart from many others."
#            m 1duu "The fact that you've had more setbacks than some people have even tried. That's what shows your dedication."
#            m 1lksdla "Sometimes, you might even have a couple bad days in a row, but don't let that get you down."
#            m 1hua "With that many setbacks, you're bound to see significant improvement right around the corner!"
#            m "Never give up, [player]. I know you can do it and I'll always believe in you!"
#            m 1eua "Also, do me a favor and take a moment to look back every now and then. You'll be surprised to see just how far you've come."
#    return
#
#label monika_idle_game_quick_callback:
#    $ end_time = datetime.datetime.now()
#    $ elapsed_time = end_time - start_time
#    $ time_threshold = datetime.timedelta(minutes=1)
#    if elapsed_time < time_threshold * 2:
#        m 1hksdlb "Back already?"
#        m "I know you said you would just be a minute or two, but I didn't think it would be {i}that{/i} fast."
#        m 1hub "Did you really miss me that much?"
#        m "Ahaha~"
#        m 1eub "I'm glad you made it back so soon."
#        m 1hua "So what else should we do today, [player]?"
#    elif elapsed_time < time_threshold * 5:
#        m 1hua "Welcome back, [player]!"
#        m 1hksdlb "That was pretty fast."
#        m 1eua "But you did say it wouldn't take too long, so I shouldn't be too surprised."
#        m 1hua "Now we can keep spending time together!"
#    elif elapsed_time < time_threshold * 10:
#        m 1eua "Welcome back, [player]."
#        m 1eka "That took a little longer than I thought, but I don't mind at all."
#        m 1hua "It wasn't that long in all honesty compared to how long it could have been in some games."
#        m "But now we can be together again~"
#    elif elapsed_time < time_threshold * 20:
#        m 1eka "I have to admit that took longer than I thought it would..."
#        m 1eub "But it's not all that bad with all the time you spend with me."
#        m 1eua "I understand some little things in games can take a while for a small thing."
#        m "But maybe if you know it could take a while, you could tell me."
#    elif elapsed_time < time_threshold * 30:
#        m 2lksdla "[player]..."
#        m "It's been almost half an hour already."
#        m "I guess something unexpected happened."
#        m 3lksdla "You wouldn't forget about me, would you?"
#        m 1hua "Ahaha!"
#        m "Just teasing you~"
#        m 1eua "At least you're back now and we can spend more time together."
#    else:
#        m 2lksdla "You {i}sure{/i} took your time with that one huh, [player]?"
#        m "That didn't seem like only a minute or two to me."
#        m 1eka "You can tell me what kind of game it is next time so I have an idea how long it'll take, you know."
#        m 1dsc "Anyway..."
#        m 1eka "I missed you and I'm glad you're finally back, [player]."
#        m "I hope I don't have to wait such a long couple of minutes next time, ehehe."
#    return
