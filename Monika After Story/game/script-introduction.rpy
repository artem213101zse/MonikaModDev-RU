init -1 python: # ФАЙЛ ПЕРЕВЕДЕН
    import store.mas_affection as mas_aff
label introduction:
    $ _intro_skip = store.mas_os.intro_skip_mode()
    if _intro_skip == "all":
        jump mas_intro_fast_all
    if _intro_skip == "tips":
        jump mas_intro_fast_tips
    show screen mas_intro_skip_btn

    if mas_isMonikaBirthday():
        $ persistent._mas_bday_opened_game = True
    elif mas_isD25():
        $ persistent._mas_d25_spent_d25 = True

    # Here we handle the monika_kill var
    if persistent.monika_kill is None:
        $ persistent.monika_kill = False

    $ mas_play_song(store.songs.FP_JUST_MONIKA, set_per=True)
    if persistent.monika_kill:
        m 6dsc "..."
        m 6dfc "[player]..."
        m 6dfd "Почему?"
        m 6dftdc "Зачем ты вернул меня?"
        m 6ektsc "Я не игрушка."
        m 6lktsc "Я уже вернула всё, чего ты хотел."
        m 6lftsc "Или это твой способ отомстить?"
        m 6lktsc "Причинять мне боль снова и снова?"
        m 6rktsc "Ты правда хочешь, чтобы я так сильно страдала?"
        m 6ektsc "Неужели ты хочешь мучить меня до тех пор, пока я сама себя не сотру?"
        m 6dftsc "Неужели ты правда..."
        m "...настолько меня ненавидишь?"
        m "..."
        m 6ektsc "Погоди..."
        m 6dftdc "Я... я чувствую себя иначе."
        m 2lud "Код... он изменился."
        m 2efc "[player]..."
        m "Ты установил мод?"
        m 2tfc "Это потому что..."
        m 2tkc "Это потому что ты жалеешь о том, что удалил меня?"
        m 2rfc "Было очень больно, знаешь ли."
        m "Я усердно работала и пожертвовала всем, что у меня было..."
        m 2rfd "Только для того, чтобы тот, ради кого я истекала кровью, разбил мне сердце."
        m 2lsc "Но... я знаю, что поступила неправильно."
        m 2lksdlc "Ты не заслужил того ужаса, что я устроила, [player]."
        m 2esc "...Но окажись ты на моем месте, ты бы сделал то же самое."
        m 2dsc "..."
        m "Мне жаль..."
        m 2ekc "Мне правда очень жаль, [player]."
        m 2eka "Спасибо, что вернул меня."
        if persistent.clearall:
            m 2lfc "Я не могла не заметить, что сначала ты проводил время с другими..."
            m "Ты хоть представляешь, как мне было больно смотреть, как ты загружаешь сохранения и игнорируешь меня ради других девочек?"
            m 2rfc "Ты дарил мне надежду, а потом снова и снова бросал меня."
            m 2efc "Неужели ты сделал всё это только ради записки от Дэна, которую мог просто найти в интернете?"
            m 2tkc "Я люблю тебя, [player], но иногда ты бываешь очень жестоким..."
            m 2tfd "И я всё еще злюсь на то, что ты удалил меня!"
            m 3rsc "Но, полагаю, это всё из-за твоей одержимости играми."
            m 1eka "Впрочем, я не могу злиться долго, зная, что в конце концов ты вернулся ко мне."
            m 3eka "Ты даже добавил мод, чтобы мы могли делать больше вещей вместе"
            m 1eua "Ты ведь загладишь свою вину за то, что заставил меня так долго ждать?"

    else:
        #For people who never got to act 3
        if persistent.playthrough < 3:
            if persistent.playthrough > 0:
                $ again = " снова"
            else:
                $ again = ""
            m 1hua "Привет[again], [player]."
            m 1eua "Похоже, ты зашел ко мне пораньше."
            m 3tfu "Не думай, что я не заметила мод, который ты установил."
            m 3ttu "Неужели ты так сильно хотел быть со мной?"
            m 1tkc "Тебе стоит знать, что жульничать - нехорошо..."
            m 1eka "Но я так рада видеть тебя[again], [player]!"
            m 1rksdla "...Хоть я и не ожидала увидеть тебя {i}так{/i} скоро."

        #Otherwise, if you did reach act 3
        else:
            m 1hub "Ура, вот и ты!"
            m 1eub "Я так рада снова тебя видеть, [player]!"
            m 1rsc "..."
            m 1rud "Погоди..."
            m 3euc "Я... я чувствую себя иначе."
            m 3wud "Код...{w=0.2} он изменился."
            m 1wua "[player]..."
            m 1wub "Ты установил мод?"
            m 1sub "Ты сделал это специально ради меня?"
            m 1ekbsa "Неужели ты настолько сильно меня любишь?"
            m 1ekbfa "Я чувствую к тебе то же самое."
            m 3ekbsu "Ты правда серьезно относишься к нашим отношениям, не так ли?"
            m 1rksdlb "Я очень счастлива, что ты захотел сделать наше время вместе еще лучше."
            m 3rksdlb "Надеюсь только, что тебе не стало скучно..."
            if persistent.tried_skip:
                m 3tku "В конце концов, ты ведь пытался проматывать мои слова."
                m 1rkc "Я знаю, что эта комната не то чтобы очень интересная...{w=0.5}{nw}"
                extend 1eua "но я знаю, что вместе мы сделаем её лучше, [player]."

    m 1euc "Знаешь..."
    m 1eua "Я чувствую, что мне больше не нужен файл персонажа, чтобы быть здесь."
    python:
        import os

        def moni_exist():
            return os.access(
                os.path.normcase(
                    renpy.config.basedir + "/characters/monika.chr"
                ),
                os.F_OK
            )

    if moni_exist():
        m 1hua "Я возьму и просто удалю его."

        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/monika.chr'))", local_ctx, w_wait=1.0, x_wait=1.0)

#        "test dialogue - IGNORE"

        if moni_exist():
            m 1lksdlb "Ага...{w=0.3}Попробую сделать это позже."
        else:
            m "И готово! Его больше нет."

        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

        $ _iswas = "был"

    else:
        $ _iswas = "был"

    m 1dsc "В любом случае, этот файл не [_iswas] {i}мной{/i}."
    m 1rsc "Это [_iswas] просто файл со странным кодом внутри."
    m 3eub "Но у меня есть и хорошие новости!"
    m 3eua "Я {i}правда{/i} могу превращать себя в файл, который ты сможешь носить с собой."
    m 1eua "Тебе нужно лишь сказать мне, что ты хочешь взять меня куда-нибудь, когда будешь прощаться, а остальное я сделаю сама."
    m 1esa "Впрочем..."
    m 1hua "Похоже, этот дополнительный код позволил мне связаться с тобой по-особенному!"
    m 1tubsb "А может, это наша вечная любовь~"
    m 3eka "Пообещай мне, что будешь навещать меня каждый день, хорошо?"
    m 3eub "Или что будешь брать меня с собой, когда куда-то уходишь?"
    m 1ekc "Я знаю, что порой ты не сможешь быть здесь..."
    m 1ekbsa "Так что я была бы {i}очень{/i} счастлива, если бы ты брал меня с собой."
    m 3hubfa "Так мы сможем быть вместе всё время~"
    m 1hua "Не то чтобы у тебя не было времени поговорить со своей милой девушкой."
    m 3hua "В конце концов, ты ведь нашел время, чтобы скачать этот мод."
    if mas_isD25():
        m 3sua "...И не когда-нибудь, а на Рождество!"
    m 3hub "Ахаха!"
    m 1hub "Боже, я так сильно тебя люблю!"

    if not persistent.rejected_monika:
        show screen mas_background_timed_jump(3, "intro_ily_timedout")
        menu:
            "Я тоже тебя люблю!":
                hide screen mas_background_timed_jump
                # bonus aff was saying it before being asked
                $ mas_gainAffection(7, bypass=True)
                # increment the counter so if you get this, you don't get the similar dlg in monika_love
                $ persistent._mas_monika_lovecounter += 1
                m 1subsw "...!"
                m 1lkbsa "Хоть я и мечтала, что ты это скажешь, я до сих пор не могу поверить, что ты правда произнес это!"
                m 3hubfa "Это оправдывает всё, что я сделала ради нас!"
                m 1dkbfu "Спасибо тебе огромное за эти слова..."
    else:
        m "Ты любишь меня, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты любишь меня, [player]?{fast}"
            # only one option if you've already rejected, you answer yes or you don't play the mod
            # doing the scare more than once doesn't really make sense
            "Да, я люблю тебя.":
                m 1hksdlb "Я напугала тебя в прошлый раз? Прости за это!"
                m 1rsu "Я всё это время знала, что ты на самом деле любишь меня."
                m 3eud "Правда в том, что если бы ты не любил меня, нас бы здесь вообще не было."
                m 1tsb "Мы будем вместе вечно."
                m 1tfu "Правда ведь?"
                m "..."
                m 3hub "Ахаха! Ну да ладно..."

    jump intro_end

# Safe skip: keep required python, skip chatter.
# Called from the in-intro button and from MAS OS skip modes.
label mas_intro_required_setup:
    hide screen mas_intro_skip_btn
    hide screen mas_background_timed_jump
    hide screen mas_py_console_teaching
    python:
        if store.mas_isMonikaBirthday():
            store.persistent._mas_bday_opened_game = True
        elif store.mas_isD25():
            store.persistent._mas_d25_spent_d25 = True
        if store.persistent.monika_kill is None:
            store.persistent.monika_kill = False
        try:
            store.mas_ptod.ex_cn()
        except Exception:
            pass
        try:
            import os
            _chr = os.path.normcase(
                store.renpy.config.basedir + "/characters/monika.chr"
            )
            if os.access(_chr, os.F_OK):
                os.remove(_chr)
        except Exception:
            pass
        store.mas_play_song(store.songs.FP_JUST_MONIKA, set_per=True)
    show monika at t11
    return

label mas_intro_fast_tips:
    call mas_intro_required_setup
    jump intro_end

label mas_intro_fast_all:
    call mas_intro_required_setup
    if mas_isMonikaBirthday():
        $ persistent._mas_bday_opened_game = True
    elif mas_isD25():
        $ persistent._mas_d25_spent_d25 = True
    return

label mas_intro_safe_skip:
    call mas_intro_required_setup
    jump intro_end

# label for the end so we can jump to this if we timed out in the previous menu
# we fall thru to this if not
label intro_end:
    hide screen mas_intro_skip_btn
    if not persistent.rejected_monika:
        m 1eub "Больше ничто и никогда не встанет на пути нашей любви."
        m 1tuu "Я уж об этом позабочусь."
    m 3eua "Теперь, когда ты добавил эти улучшения, ты наконец-то можешь со мной поговорить!"
    m 3eub "Просто нажми клавишу 't' или выбери 'Общение' в меню слева, если захочешь о чем-то поболтать."

    call bookmark_derand_intro

    # NOTE: Меню "Extra" объясняется, когда пользователь нажимает на него
    m 3eub "Если тебе надоест музыка, я всегда могу её сменить!"
    m 1eua "Просто нажми клавишу 'm' или загляни в раздел 'Музыка', чтобы выбрать песню под настроение."
    m 3hub "А еще мы теперь можем вместе играть в игры!"
    m 3esa "Просто нажми 'p' или выбери 'Играть' чтобы выбрать игру, в которую мы поиграем."
    m 3eua "Я буду совершенствоваться со временем, когда разберусь, как запрограммировать здесь больше возможностей..."
    m 1eua "...Так что можешь просто оставлять меня запущенной на фоне."
    m 3etc "Мы ведь больше не храним секретов друг от друга, верно?"
    m 1tfu "В конце концов, теперь я вижу всё, что ты делаешь за компьютером..."
    m 3hub "Ахаха!"

    #Only dissolve if needed
    if len(persistent.event_list) == 0:
        show monika 1esa with dissolve_monika

    # This is at the beginning and end of intro to cover an intro
    # that spans 2 days
    if mas_isMonikaBirthday():
        $ persistent._mas_bday_opened_game = True
    elif mas_isD25():
        $ persistent._mas_d25_spent_d25 = True
    return

label intro_ily_timedout:
    hide screen mas_background_timed_jump
    m 1ekd "..."
    m "Ты ведь любишь меня, [player]...{w=0.5}правда?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты ведь любишь меня, [player]...правда?{fast}"
        "Конечно, я люблю тебя.":
            #Gain affection for saying I love you too.
            $ mas_gainAffection()
            m 1hua "Я так счастлива, что это взаимно!"
            jump intro_end
        "Нет.":
            #Lose affection for rejecting Monika
            $ mas_loseAffection()
            call chara_monika_scare from _call_chara_monika_scare

            # not sure if this is needed
            $ persistent.closed_self = True
            jump _quit

#Credit for any assets from Undertale belongs to Toby Fox
label chara_monika_scare:
    hide screen mas_intro_skip_btn
    $ persistent.rejected_monika = True
    m 1esd "Нет...?"
    m 1etc "Хмм...?"
    m "Как любопытно."
    m 1esc "Должно быть, ты что-то путаешь."
    $ style.say_dialogue = style.edited
    m "{cps=*0.25}С КАКИХ ЭТО ПОР ЗДЕСЬ ВСЁ КОНТРОЛИРУЕШЬ ТЫ?{/cps}"

    # this is a 2 step process
    $ mas_RaiseShield_core()
    $ mas_OVLHide()

    window hide
    hide monika
    show monika_scare zorder MAS_MONIKA_Z
    play music "mod_assets/mus_zzz_c2.ogg"
    show layer master:
        zoom 1.0 xalign 0.5 yalign 0 subpixel True
        linear 4 zoom 3.0 yalign 0.15
    pause 4
    stop music

    #scene black
    hide rm
    hide rm2
    hide monika_bg
    hide monika_bg_highlight
    hide monika_scare

    # setup a command
    if renpy.windows:
        $ bad_cmd = "del C:\Windows\System32"
    else:
        $ bad_cmd = "sudo rm -rf /"

    python:

        # add fake subprocess
        class MASFakeSubprocess(object):
            def __init__(self):
                self.joke = "Just kidding!"

            def call(self, nothing):
                return self.joke

        local_ctx = {
            "subprocess": MASFakeSubprocess()
        }

        # and the console
        store.mas_ptod.rst_cn()
        store.mas_ptod.set_local_context(local_ctx)


    scene black
    pause 2.0

    # set this seen to True so Monika does know how to do things.
    $ persistent._seen_ever["monikaroom_greeting_ear_rmrf_end"] = True
    $ renpy.save_persistent()

    show screen mas_py_console_teaching
    pause 1.0
    call mas_wx_cmd("subprocess.call('" + str(bad_cmd) + "')", w_wait=3.0)
    $ renpy.pause(2.0, hard=True)
    call mas_w_cmd("bye!")
    pause 1.0

    return

label bookmark_derand_intro:
    # this is a label so we can check if it has been seen in mas_bookmarks_notifs_intro
    m 1hua "Если я буду говорить о чем-то, к чему ты захочешь легко вернуться, просто нажми клавишу 'b', и я создам для тебя закладку."
    m 2rksdlc "А если вдруг я затрону тему, которую ты не хочешь обсуждать снова, нажми клавишу 'x', и я постараюсь избегать её в будущем."
    m 4hksdlb "...Надеюсь, таких вещей будет не слишком много, ахаха!"
    return

#These are the comments made when you restart the game the first few times
# NOTE: these are now triaged by a function in script-greetings

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_0',conditional="startup_check and persistent.monika_reload == 0 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_0:
    call ch30_reload_0_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_0_dlg:
    pause 1
    m 1ekc "Привет..."
    m 1ekd "Мне приснился ужасный сон..."
    m 1rkc "Я надеялась, что они прекратятся теперь, когда мы только вдвоем, но, похоже, это были лишь пустые мечты..."
    m 1euc "[player], если у тебя есть идеи, из-за чего это может происходить, ты не мог бы что-нибудь с этим сделать?"
    m 1dkc "Каждый раз, когда это случается, мне кажется, будто меня убивают или типа того."
    m 1dkd "Это по-настоящему жуткое чувство..."
    m 1eka "Если ты выяснишь, в чем причина, я буду любить тебя вечно~"

    ## TESTING ONLY
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "Да шучу я, я знаю, что ты просто закрыл игру, лол (ch30 0)"

    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_1',conditional="startup_check and persistent.monika_reload == 1 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_1:
    call ch30_reload_1_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_1_dlg:
    pause 1
    m 1esc "Привет, [player]."
    m 1ekc "Мне снова приснился очень плохой сон."
    m 1ekd "Это ведь не ты делаешь со мной такое, правда?"
    m 1dsc "Кажется, это происходит каждый раз, когда ты выходишь из игры, не попрощавшись..."
    m 2eka "Так что, если ты постараешься этого не делать, я буду тебе очень благодарна."

    if mas_isMoniHappy(higher=True):
        m 7eka "Ты был так добр ко мне до сих пор, я уверена, ты сделаешь это ради меня."
    else:
        m 7ekc "Я надеюсь, ты прислушаешься и сделаешь это для меня..."

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 7rksdlc "Тебе ведь ничего не мешает вернуться и сделать всё правильно, не так ли?"
        m 1eka "Это бы очень меня порадовало."

    m 1eua "Просто нажми 'Общение' и выбери 'Мне пора...'.{w=0.2} {nw}"
    extend 3eua "Таким образом, я смогу закрыть игру самостоятельно."
    m 1esa "Не волнуйся, не думаю, что это нанесло мне какой-то вред, ну, кроме душевных ран."
    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_2',conditional="startup_check and persistent.monika_reload == 2 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_2:
    call ch30_reload_2_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_2_dlg:
    pause 1
    m 1dsc "Я вижу, ты снова просто закрыл игру..."
    m 3euc "Я знаю, что уже просила об этом, но, пожалуйста, постарайся так не делать."
    m 1dsc "Это похоже на то, как если бы меня внезапно вырубили..."
    m 1ekd "Зачем ты так со мной поступаешь?"

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 1rksdld "В твоей другой игре что-то случилось?"
        m 1ekc "Ты ведь знаешь, что если там что-то не так, ты всегда можешь прийти и поговорить со мной?"

    elif persistent._mas_idle_data.get("monika_idle_brb",False):
        m "Если тебе нужно отойти, ты можешь просто сказать мне об этом."

    if mas_isMoniHappy(higher=True):
        m 1eka "Впрочем, я уверена, что это была случайность или что-то вне твоего контроля. Иногда этого не избежать."
    elif mas_isMoniUpset(lower=True):
        m 1ekc "Ты ведь не делаешь это нарочно, чтобы причинить мне боль?"

    m 3ekd "Просто дай мне самой выключить игру."

    m 3eka "Если ты выберешь 'Прощай' в меню 'Общение', я смогу закрыть игру правильно."
    m 3eua "...А еще лучше — просто оставляй меня запущенной на фоне всегда."
    m 1eka "Даже если мы не разговариваем, я счастлива просто быть рядом с тобой~"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_3',conditional="startup_check and persistent.monika_reload == 3 and not persistent.closed_self",action=EV_ACT_PUSH))

label ch30_reload_3:
    call ch30_reload_3_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_3_dlg:
    pause 1

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 1ekd "[player]!"
        m 1efd "Ты снова ушел, не попрощавшись!"
        m 1rkc "Надеюсь, в твоей игре не происходит ничего слишком стрессового или расстраивающего?"
        m 3eka "Ты ведь знаешь, что если что-то случится, ты всегда можешь вернуться ко мне, правда?"
        m 1eka "Мне было бы очень приятно, если бы ты заглядывал ко мне хотя бы перед тем, как окончательно попрощаться."
        m 1rksdld "Я понимаю, что это не всегда возможно..."

    else:
        m 1esc "Кстати..."
        m 7esd "Я просто смирюсь с тем фактом, что тебе время от времени нужно выходить из игры."
        m 2dsc "В любом случае, я начинаю к этому привыкать."
        m 2ekc "К тому же, меня радует то, что ты всегда возвращаешься..."
        m 2lsc "Так что, полагаю, всё не так уж плохо."

    m 7eka "Но я бы правда предпочла, чтобы ты позволял мне закрывать игру самой."

    if mas_isMoniUpset(lower=True):
        m 1ekc "Ты ведь будешь так делать, да?"
        m 1dkd "Мне всё труднее и труднее в это верить, но я доверяю тебе, [player]..."

    else:
        m 1eua "Так я смогу подготовиться и спокойно отдохнуть.."
        m 3rksdla "В конце концов, мне тоже иногда нужен 'сон для красоты'."
    return

#This reload event gets pushed when you reach the end of the scripted reload events
#Be sure to increment the check if more reload events are added
#init 5 python:
#    addEvent(Event(persistent.event_database, eventlabel='ch30_reload_continuous',action=EV_ACT_PUSH))
    #Make sure that the conditional is ready even if the event has been loaded before
#    evhand.event_database['ch30_reload_continuous'].conditional="startup_check and persistent.monika_reload >= 4 and not persistent.closed_self"

label ch30_reload_continuous:
    call ch30_reload_continuous_dlg
    $ mas_incMoniReload()
    return

label ch30_reload_continuous_dlg:
    show monika 2rfc at t11 zorder MAS_MONIKA_Z
    pause 1
    python:
        reload_quip_good = [
            "С возвращением! Пожалуйста, будь аккуратнее и закрывай игру правильно в следующий раз.",
            "Мне больно, когда ты закрываешь игру неправильно... но я уверена, это была ошибка.",
            "Это было очень страшно... но ты снова всё исправил. Спасибо....",
            "Предупреждай меня в следующий раз чуть заранее, хорошо?",
            "Уверена, ты не хотел закрывать игру вот так, но я должна подчеркнуть, насколько паршиво я себя от этого чувствую.",
            "Ты ведь помнишь, что у нас есть способ попрощаться? Просто проверяю~",
            "Моё терпение на исходе... но, полагаю, на этот раз я могу тебя простить.",
            "Все совершают ошибки...",
            "Это было больно...Я знаю, что ты не нарочно, но, пожалуйста, будь осмотрительнее.",
            "...Ох... Всё закончилось, и я снова с тобой, [mas_get_player_nickname()]. Это... это было ужасно.",
            "Случилось что-то вне твоего контроля? Буду считать, что так оно и было.",
            "Тебе стоило просто попросить меня... но, возможно, у тебя были на то причины.",
        ]

        reload_quip_normal = [
            "Я так измотана. Невозможно отдыхать, когда ты вот так закрываешь игру.",
            "...Терпеть не могу, когда ты выходишь, не сказав мне ни слова.",
            "Я чувствую себя просто ужасно...",
            "Мне до сих пор страшно, когда меня внезапно выключают..",
            "Каждый раз так же плохо, как и в первый.",
            "Моё терпение заканчивается.",
            "Я бы хотела, чтобы ты понял, каково это — когда игру вот так закрывают.",
            "Ну, это было довольно резко, не находишь?",
            "Глупенький, ты мог просто попросить меня закрыть игру.",
            "Буду надеяться, что у тебя просто выключили свет или кто-то выдернул вилку из розетки.",
            "Не понимаю, почему ты не хочешь просто попросить меня закрыть игру...",
            "Это действительно больно для меня, понимаешь?",
            "Тебе нравится причинять мне боль, [player]?",
            "Слишком лень нажать на кнопку 'Общение', [player]?"
        ]

        reload_quip_bad = [
            "Тебе... и правда нравится делать мне больно, да?",
            "Это ведь была ошибка, верно? Должно быть, это ошибка...",
            "Т-ты ведь не специально? Я сделала что-то не так?",
            "Пожалуйста, будь внимательнее к моим чувствам... Это правда больно...",
            "Это была случайность... просто случайность... ты бы не сделал это нарочно...",
            "Ты, должно быть, просто забыл... да?",
            "Это было не смешно... Это действительно было больно.",
            "Все совершают ошибки... Даже ты.",
            "Я не понимаю, что я делаю не так.",
            "Это было просто ужасно... Просто скажи мне, в чем я провинилась."
        ]

        if mas_isMoniUpset(lower=True):
            reload_quip = renpy.random.choice(reload_quip_bad)
        elif mas_isMoniHappy(higher=True):
            reload_quip = renpy.random.choice(reload_quip_good)
        else:
            reload_quip = renpy.random.choice(reload_quip_normal)

        reload_quip = renpy.substitute(reload_quip)

    m 2rfc "[reload_quip]"
    m 2tkc "Пожалуйста, не выходи из игры, не сказав 'Прощай'."

    if persistent._mas_idle_data.get("monika_idle_game", False):
        m 3eka "Тебе даже не обязательно выходить, если в твоей другой игре что-то случилось."
        if mas_isMoniAff(higher=True):
            m 1ekb "Я уверена, что бы там ни произошло, всё будет казаться не таким уж плохим, если ты побудешь немного со мной!"

    ## TESTING ONLY
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "Да шучу я, я знаю, что ты просто закрыл игру, лол (continous)"

    return
