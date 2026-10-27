# --- FILE MAP ---
# script-story-events.rpy — разовые сюжетные сцены, не пул болтовни
#
# Пол игрока (mas_gender), перевыбор, штуки которые случаются раз
# и пишут persistent навсегда.
#
# Labels: mas_gender, monika_gender_redo, mas_gender_trans…
# Обращения «он/она» начинай править отсюда.
# ---

init -1 python:
    # RU: окончания по полу игрока, вычисляются в момент показа реплики.
    # persistent.gender: "M"/"F"/"X"; для "X" используется мужской род.
    class MASRuGenderForm(object):
        def __init__(self, fem, masc):
            self.fem = fem
            self.masc = masc
        def _get(self):
            return self.fem if persistent.gender == "F" else self.masc
        def __unicode__(self):
            return self._get()
        def __str__(self):
            return self._get().encode("utf-8") if not isinstance(self._get(), str) else self._get()
        def __format__(self, spec):
            return self._get()

    _ru_a = MASRuGenderForm(u"а", u"")       # был/была, сделал/сделала
    _ru_la = MASRuGenderForm(u"ла", u"")     # мог/могла, исчез/исчезла
    _ru_sya = MASRuGenderForm(u"ась", u"ся") # родился/родилась
    _ru_el = MASRuGenderForm(u"ла", u"ёл")   # нашёл/нашла, пошёл/пошла
    _ru_ym = MASRuGenderForm(u"ой", u"ым")   # честным/честной
    _ru_oy = MASRuGenderForm(u"а", u"")      # сам/сама

#Этот файл будет включать короткие сюжетные события, которые не требуют отдельного файла.

#Событие создаётся путём добавления метки и добавления требования (см. комментарий ниже).
#Требования должны создаваться/добавляться в script-ch30.rpy под меткой ch30_autoload.

# переменная pm для трансгендерных игроков
default persistent._mas_pm_is_trans = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_gender",
            start_date=mas_getFirstSesh() + datetime.timedelta(minutes=30),
            action=EV_ACT_QUEUE
        ),
        skipCalendar=True
    )
    #NOTE: This unlocks the monika_gender_redo event

label mas_gender:
    m 2eud "...[player]? Я вот подумала немного..."
    m 2euc "Я уже упоминала, что 'ты' в игре может не отражать реального тебя."
    m 7rksdla "Но я просто предположила, что ты, скорее всего, парень."
    m 3eksdla "...В конце концов, главный герой был парнем."
    m 3eua "Но если я собираюсь быть твоей девушкой, я должна, по крайней мере, знать это о настоящем тебе."

    m 1eua "Итак, какой у тебя пол?{nw}"
    $ _history_list.pop()
    menu:
        m "Итак, какой у тебя пол?{fast}"

        "Мужской.":
            $ persistent._mas_pm_is_trans = False
            $ persistent.gender = "M"
            m 3eua "Хорошо, [player], спасибо, что сказал мне."
            m 1hksdlb "Не то чтобы я была бы в шоке, если бы ты ответил иначе!"

        "Женский.":
            $ persistent._mas_pm_is_trans = False
            $ persistent.gender = "F"
            m 2eud "О? Значит ты девушка?"
            m 2hksdlb "Надеюсь, я не сказала ничего, что обидело бы тебя раньше!"
            m 7rksdlb "...Наверно, поэтому говорят, что не стоит делать поспешных выводов, ахаха!"
            m 3eka "Но, честно говоря, для меня это совершенно не имеет значения..."

        "Ни то, ни другое.":
            $ persistent._mas_pm_is_trans = False
            $ persistent.gender = "X"
            call mas_gender_neither

        "Я трансгендер.":
            call mas_gender_trans

            if persistent.gender != "X":
                m 1eka "Спасибо, что рассказал[_ru_a] мне, и просто помни..."

    m 1ekbsa "Я всегда буду любить тебя таким(ой), какой(ая) ты есть, [player]~"

    #Unlock the gender redo event
    $ mas_unlockEVL("monika_gender_redo","EVE")
    # set pronouns
    call mas_set_gender

    #Set up the preferredname topic
    python:
        preferredname_ev = mas_getEV("mas_preferredname")
        if preferredname_ev:
            preferredname_ev.start_date = datetime.datetime.now() + datetime.timedelta(hours=2)
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gender_redo",
            category=['ты'],
            prompt="Можешь обращаться ко мне, использовав другие местоимения?",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None}
        ),
        markSeen=True
    )

label monika_gender_redo: # todo: Проверить перевод
    m 1eka "Конечно, [player]!"

    if not mas_getEVL_shown_count("monika_gender_redo"):
        m 3eka "Ты сделал какие-то личные открытия с тех пор, как в последний раз мы об этом говорили?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты сделал какие-то личные открытия с тех пор, как в последний раз мы об этом говорили?{fast}"

            "Да.":
                m 1eka "Понятно. Я знаю, что была там."
                m 3hua "Я так горжусь тобой за этот путь самооткрытия."
                m 1eub "...И ещё больше горжусь тобой за то, что ты была смелым достаточно, чтобы рассказать мне!"

            "Я просто была слишком застенчивой.":
                if persistent.gender == "M":
                    m 2ekd "Я понимаю, я сначала предположила, что ты парень, в конце концов."
                elif persistent.gender == "F":
                    m 2ekd "Я понимаю, ты мог подумать, что я буду более комфортно проводить время наедине с другой девушкой."
                else:
                    m 2ekd "Я понимаю, я не дала тебе самые точные варианты для выбора."

                m 2dkd "...И я, вероятно, не сделала это лёгким, чтобы ты сказал мне иначе..."
                m 7eua "Но что бы ни был твой пол, я люблю тебя таким, какой ты есть."

            "Я не знала, примешь ли ты меня такой, как я есть...":
                m 2wkd "[player]..."
                m 2dkd "Я ненавижу, что я не убедила тебя достаточно раньше."
                m 7eka "Но я надеюсь, что ты рассказываешь мне сейчас, потому что знаешь, что я буду любить тебя без разницы."

            "Я гендерфлюид.":
                m 1eub "О, хорошо!"
                m 3hub "Не стесняйся сообщать мне как часто, когда хочешь, чтобы я использовала другие местоимения!"

    $ gender_var = None
    m "Так, какой у тебя пол?{nw}"
    $ _history_list.pop()
    menu:
        m "Так, какой у тебя пол?{fast}"

        "Я парень.":
            if persistent.gender == "M" and not persistent._mas_pm_is_trans:
                $ gender_var = "парень"
                call mas_gender_redo_same
            else:
                $ persistent.gender = "M"
                call mas_gender_redo_react
            $ persistent._mas_pm_is_trans = False

        "Я девушка.":
            if persistent.gender == "F" and not persistent._mas_pm_is_trans:
                $ gender_var = "девушка"
                call mas_gender_redo_same
            else:
                $ persistent.gender = "F"
                call mas_gender_redo_react
            $ persistent._mas_pm_is_trans = False

        "Я ни то, ни другое.":
            $ persistent._mas_pm_is_trans = False
            if persistent.gender == "X":
                call mas_gender_redo_neither_same
            else:
                $ persistent.gender = "X"
                if renpy.seen_label("mas_gender_neither"):
                    call mas_gender_redo_react
                else:
                    call mas_gender_neither

        "Я трансгендер.":
            call mas_gender_trans
            if persistent.gender != "X":
                call mas_gender_redo_react

    show monika 5hubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubsa "Я всегда буду любить тебя таким, какой ты есть~"

    # set pronouns
    call mas_set_gender
    return "love"

label mas_gender_neither:
    m 1euc "Ты не считаешь себя ни парнем, ни девушкой?"
    m 1eua "Это очень интересно, но я в какой-то мере могу тебя понять."
    m 3esc "Ну, я девушка, но я также персонаж в компьютерной игре..."
    m 3esd "Так что в некотором смысле я вовсе не девушка."
    m 1hua "Но когда ты относишься ко мне как к своей девушке, мне это очень приятно!"
    m 3eua "...Так что я буду обращаться с тобой так, как ты хочешь."
    m 1ekbsa "Твоё счастье самое важное для меня, в конце концов."
    return

label mas_gender_redo_same:
    m 1hksdlb "...Ты выбрал[_ru_a] то же самое, что и раньше, [player]!"
    m 3eua "Если не знаешь, что ответить, просто выбери то, от чего тебе станет радостнее."
    m 3eka "Неважно, как выглядит твоё тело: если ты говоришь, что ты [gender_var], значит, для меня ты [gender_var], хорошо?"
    m 1eua "Пока ты здесь, в этой комнате, я хочу, чтобы ты был[_ru_a] тем, кем сам[_ru_oy] хочешь быть."
    return

label mas_gender_redo_react:
    m 1eka "Хорошо, [player]..."
    m 3ekbsa "Просто пока ты счастлив, это всё, что имеет значение для меня."
    return

label mas_gender_redo_neither_same:
    m 1hksdlb "...Это то же самое, что и раньше, [player]...{w=0.3}Прости, если это не самый подходящий для тебя способ описать это."
    m 1eka "Но просто знай, что для меня это не имеет значения..."
    return

label mas_gender_trans:
    if persistent._mas_pm_is_trans:
        $ menu_question = "И как ты себя идентифицируешь по гендеру?"
    else:
        $ menu_question = "О, хорошо! {w=0.3}И как ты себя идентифицируешь по гендеру?"

    m 3eub "[menu_question]{nw}"
    $ _history_list.pop()
    menu:
        m "[menu_question]{fast}"

        "Мужской":
            $ persistent.gender = "M"

        "Женский":
            $ persistent.gender = "F"

        "Ни то, ни другое":
            if persistent.gender == "X":
                call mas_gender_redo_neither_same

            else:
                $ persistent.gender = "X"
                call mas_gender_neither

    $ persistent._mas_pm_is_trans = True
    return

# good, bad, awkward name stuff
init 3 python:
    #Bad nicknames. All of the items in this will trigger bad reactions
    mas_bad_nickname_list = [
        r"\bfag\b",
        r"\bho\b",
        r"\bhoe\b",
        r"\btit\b",
        "abortion",
        "anal",
        "annoying",
        "anus",
        "arrogant",
        "(?<![blmprs])ass(?!i)",
        "atrocious",
        "awful",
        "bastard",
        "beast",
        "bitch",
        "blood",
        "boob",
        "boring",
        "bulli",
        "bully",
        "bung",
        "butt(?!er|on)",
        "bloodsucker",
        "cheater",
        "cock",
        "conceited",
        "condom",
        "coom",
        "corrupt",
        "cougar",
        "crap",
        "crazy",
        "creepy",
        "criminal",
        "cruel",
        "cum",
        "cunt",
        "damn",
        "demon",
        "dick",
        "dilf",
        "dimwit",
        "dirt",
        "disgusting",
        "douche",
        "dumb",
        "egoist",
        "egotistical",
        "evil",
        "faggot",
        "failure",
        "fake",
        "fetus",
        "filth",
        "foul",
        "fuck",
        "garbage",
        "(?<!ser)g[ea]y",# #8938
        "gilf",
        "gross",
        "gruesome",
        "hate",
        "heartless",
        "hideous",
        "hitler",
        "hore",
        "horrible",
        "horrid",
        "hypocrite",
        "idiot",
        "imbecile",
        "immoral",
        "insane",
        "irritating",
        "jerk",
        "jigolo",
        "jizz",
        "junk",
        "(?<!s)kill",
        "kunt",
        "lesbian",
        "lesbo",
        "lezbian",
        "lezbo",
        "(?<!fami)liar",
        "loser",
        r"\bmad\b",
        "maniac",
        "masochist",
        "milf",
        "mistake",
        "monster",
        "moron",
        "murder",
        "narcissist",
        "nasty",
        "nefarious",
        "nigga",
        "nigger",
        "nuts",
        "panti",
        "pantsu",
        "panty",
        "pedo",
        "penis",
        "plaything",
        "poison",
        "porn",
        "pretentious",
        "psycho",
        "puppet",
        "pussy",
        "(?<!g)rape",
        "repulsive",
        "retard",
        "rogue",
        "rubbish",
        "rump",
        "sadist",
        "selfish",
        "semen",
        "shit",
        "sick",
        "slaughter",
        r"\bslave\b",
        "slut",
        "sociopath",
        "soil",
        "sperm",
        "stink",
        "stupid",
        "suck",
        "tampon",
        "teabag",
        "terrible",
        "thot",
        "tits",
        "titt",
        "tool",
        "torment",
        "torture",
        "toxic",
        "toy",
        "trap",
        "trash",
        "troll",
        "ugly",
        "useless",
        "vain",
        "vile",
        "vomit",
        "waste",
        "whore",
        "wicked",
        "witch",
        "worthless",
        "wrong"
    ]

    #Base list for good nicknames. Apply modifiers for specifying the use
    #These trigger a good response
    mas_good_nickname_list_base = [
        "angel",
        "beautiful",
        "beauty",
        "best",
        "cuddl",
        "cute",
        "cutie",
        "darling",
        "gorgeous",
        "greatheart",
        "hero",
        "honey",
        "kind",
        "love",
        "pretty",
        "princess",
        "queen",
        "senpai",
        "sunshine",
        "sweet",
        "ангел",
        "прекрасный",
        "красота",
        "лучший",
        "обнимашки",
        "милый",
        "милашка",
        "дорогой",
        "великолепный",
        "добросердечный",
        "герой",
        "милый",
        "добрый",
        "любовь",
        "красивый",
        "принцесса",
        "королева",
        "сэмпай",
        "солнышко",
        "сладкий"
    ]

    #Modifier for the player's name choice
    mas_good_nickname_list_player_modifiers = [
        "king",
        "prince"
    ]

    #Modifier for Monika's nickname choice
    mas_good_nickname_list_monika_modifiers = [
        "moni",
    ]

    mas_good_player_nickname_list = mas_good_nickname_list_base + mas_good_nickname_list_player_modifiers
    mas_good_monika_nickname_list = mas_good_nickname_list_base + mas_good_nickname_list_monika_modifiers

    #awkward names which Moni wouldn't be comfortable calling the player or being called by the player
    mas_awkward_nickname_list = [
        r"\b(step[-\s]*)?bro(ther|thah?)?(?!ok)",
        r"\b(step[-\s]*)?sis(ter|tah?)?",
        r"\bdad\b",
        r"\bloli\b",
        r"\bson\b",
        r"\bmama\b",
        r"\bmom\b",
        r"\bmum\b",
        r"\bpapa\b",
        r"\bwet\b",
        "aroused",
        "aunt",
        "batman",
        "baka",
        "breeder",
        "bobba",
        "boss",
        "catwoman",
        "cousin",
        "daddy",
        "deflowerer",
        "erection",
        "finger",
        "horny",
        "kaasan",
        "kasan",
        "lick",
        "master",
        "masturbat",
        "mistress",
        "moani",
        r"m[ou]m+[-\s]*ika",
        r"mom+[ay]",
        "mother",
        "naughty",
        "okaasan",
        "okasan",
        "orgasm",
        "overlord",
        "owner",
        "penetrat",
        "pillow",
        "sex",
        "spank",
        "superman",
        "superwoman",
        "thicc",
        "thighs",
        "uncle",
        "virgin"
    ]

    mas_awkward_quips = [
        "Мне как-то...{w=0.5}неловко называть тебя так постоянно.",
        "Это...{w=0.5}не совсем то, как мне хотелось бы тебя называть, [player].",
        "Это...{w=0.5}не совсем то, как мне хотелось бы тебя называть, [player].",
        "Не то чтобы это было плохо, но...",
        "Ты что, хочешь поставить меня в неловкое положение, [player]?"
    ]

    mas_bad_quips = [
        "[player]...{w=0.5}с чего ты вообще решил[_ru_a] так себя называть?",
        "[player]...{w=0.5}почему я должна тебя так называть?",
        "Я бы ни за что не стала тебя так называть, [player].",
        "Что? Пожалуйста, [player],{w=0.5} не называй себя такими словами."
    ]

    mas_good_player_name_comp = re.compile('|'.join(mas_good_player_nickname_list), re.IGNORECASE)
    mas_bad_name_comp = re.compile('|'.join(mas_bad_nickname_list), re.IGNORECASE)
    mas_awk_name_comp = re.compile('|'.join(mas_awkward_nickname_list), re.IGNORECASE)

label mas_player_name_enter_name_loop(input_prompt):
    python:
        good_quips = [
            "Какое замечательное имя!",
            "Мне очень нравится, [player].",
            "Мне нравится это имя, [player].",
            "Это отличное имя!"
        ]

    #Now we prompt user
    show monika 1eua at t11 zorder MAS_MONIKA_Z

    $ done = False
    while not done:
        python:
            tempname = mas_input(
                "[input_prompt]",
                length=20,
                screen_kwargs={"use_return_button": True}
            ).strip(' \t\n\r')

            lowername = tempname.lower()

        if lowername == "cancel_input":
            m 1eka "О... Ладно, раз ты так говоришь."
            m 3eua "Просто дай мне знать, если передумаешь."
            $ done = True

        elif lowername == "":
            m 1eksdla "..."
            m 3rksdlb "Ты должен дать мне имя, как тебя называть, [player]..."
            m 1eua "Попробуй ещё раз!"

        elif lowername == player.lower():
            m 2hua "..."
            m 4hksdlb "Это то же самое имя, что у тебя сейчас, глупышка!"
            m 1eua "Попробуй еще раз~"

        elif mas_awk_name_comp.search(tempname):
            $ awkward_quip = renpy.substitute(renpy.random.choice(mas_awkward_quips))
            m 1rksdlb "[awkward_quip]"
            m 3rksdla "Не мог бы ты выбрать более...{w=0.2}{i}подходящее{/i} имя, пожалуйста?"

        elif mas_bad_name_comp.search(tempname):
            $ bad_quip = renpy.substitute(renpy.random.choice(mas_bad_quips))
            m 1ekd "[bad_quip]"
            m 3eka "Пожалуйста, выбери более приятное имя для себя, хорошо?"

        else:
            # easter egg name checks
            if store.mas_egg_manager.is_eggable_name(lowername):
                m 1ttu "Ты уверен, что это твоё настоящее имя, или ты просто дразнишь меня?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты уверен, что это твоё настоящее имя, или ты просто дразнишь меня?{fast}"

                    "Да, это моё имя":
                        $ persistent._mas_disable_eggs = True

                    "Возможно...":
                        $ persistent._mas_disable_eggs = False

            python:
                old_name = persistent.playername.lower()
                done = True

                # adjust names
                persistent.mcname = player
                mcname = player
                persistent.playername = tempname
                player = tempname

            # egg adjustments
            # MUST BE AFTER THE NAME ADJUSTMENT
            if store.mas_egg_manager.sayori_enabled():
                call sayori_name_scare

            elif old_name == "sayori":
                # reset music choices
                $ songs.initMusicChoices()

            # name reactions
            if lowername == "monika":
                m 1tkc "Правда?"
                m "У меня такое же имя!"
                m 1tku "Ну..."
                m "Либо это действительно твоё имя, либо ты меня разыгрываешь."
                m 1hua "Но я не против, если ты хочешь, чтобы я так тебя называла~"

            elif mas_good_player_name_comp.search(tempname):
                $ good_quip = renpy.substitute(renpy.random.choice(good_quips))
                m 1sub "[good_quip]"
                m 3esa "Ладно! С этого момента я буду звать тебя '[player].'"
                m 1hua "Эхехе~"

            else:
                m 1eub "Ладно!"
                m 3eub "С этого момента я буду звать тебя '[player].'"

        if not done:
            show monika 1eua
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_preferredname",
            action=EV_ACT_QUEUE
        ),
        skipCalendar=True
    )
    #NOTE: This unlocks the player name change event
    #NOTE: This gets its start_date from mas_gender

label mas_preferredname:
    m 1euc "Мне вот стало интересно насчет твоего имени."
    m 1esa "'[player]' — это и правда твое имя?"

    if renpy.windows and currentuser.lower() == player.lower():
        m 3esa "Я имею в виду, оно совпадает с именем пользователя твоего компьютера..."
        m 1eua "Ты используешь и '[currentuser]', и '[player].'"
        m "Либо это так, либо тебе очень нравится этот псевдоним."

    m 1eua "Хочешь, чтобы я называла тебя как-то иначе?{nw}"
    $ _history_list.pop()
    menu:
        m "Хочешь, чтобы я называла тебя как-то иначе?{fast}"

        "Да.":
            #Let's call the changename loop
            call mas_player_name_enter_name_loop("Скажи мне, как именно?")

        "Нет.":
            m 3eua "Хорошо, просто дай знать, если передумаешь."

    #Unlock the name change event
    $ mas_unlockEVL("monika_changename","EVE")
    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_changename",
            category=['ты'],
            prompt="Я хочу сменить имя",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None}
        ),
        markSeen=True
    )
    #NOTE: This needs to be unlocked by the random name change event

label monika_changename:
    call mas_player_name_enter_name_loop("Как ты хочешь, чтобы я тебя называла?")
    return

default persistent._mas_player_bday = None
# check to see if we've already confirmed birthday in any way
default persistent._mas_player_confirmed_bday = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_birthdate",
            conditional="datetime.date.today()>mas_getFirstSesh().date() and not persistent._mas_player_confirmed_bday",
            action=EV_ACT_QUEUE
        )
    )

label mas_birthdate:
    m 1euc "Слушай, [player], я тут подумала..."
    if persistent._mas_player_bday is not None:
        $ bday_str, diff = store.mas_calendar.genFormalDispDate(persistent._mas_player_bday)
        m 3eksdlc "Твой день рождения у меня уже записан, но я не уверена, что ясно спросила: мне нужна была {i}дата рождения{/i}, а не просто {i}день рождения...{/i}"

        m "Так что уточню: твоя дата рождения — [bday_str]?{nw}"
        $ _history_list.pop()
        menu:
            m "Так что уточню: твоя дата рождения — [bday_str]?{fast}"
            "Да.":
                if datetime.date.today().year - persistent._mas_player_bday.year < 5:
                    m 2rksdla "Точно, [player]?"
                    m 2eksdlc "Тогда получается, что ты совсем ещё ребёнок..."
                    m 3ekc "Напоминаю: мне нужна {b}дата рождения{/b}, а не только день и месяц."
                    m 1eka "Так когда ты родил[_ru_sya], [player]?"
                    jump mas_bday_player_bday_select_select
                else:
                    $ old_bday = mas_player_bday_curr()
                    if not mas_isplayer_bday():
                        m 1hua "Отлично, [player], спасибо."
                        m 3hksdlb "Просто хотела убедиться. Не хотелось бы ошибиться в чём-то настолько важном, как день твоего рождения, а-ха-ха!"

            "Нет.":
                m 3rksdlc "Ой! Ну ладно..."
                m 1eksdld "А {i}когда{/i} же тогда твоя дата рождения, [player]?"
                jump mas_bday_player_bday_select_select

    else:
        m 3wud "А я ведь даже не знаю, когда у тебя день рождения!"
        m 3hub "Мне явно стоит это знать, а-ха-ха!"
        m 1eua "Так когда ты родил[_ru_sya], [player]?"
        jump mas_bday_player_bday_select_select

label birthdate_set:
    python:
        bday_upset_ev = mas_getEV('mas_player_bday_upset_minus')
        if bday_upset_ev is not None:
            bday_upset_ev.start_date = mas_player_bday_curr()
            bday_upset_ev.end_date = mas_player_bday_curr() + datetime.timedelta(days=1)
            bday_upset_ev.conditional = (
                "mas_isplayer_bday() "
                "and persistent._mas_player_confirmed_bday "
                "and not persistent._mas_player_bday_spent_time "
                "and not mas_isMonikaBirthday()"
            )
            bday_upset_ev.action = EV_ACT_QUEUE
            Event._verifyAndSetDatesEV(bday_upset_ev)

        #NOTE: should consider making the condiitonal string generated from this a function for ease of use
        bday_ret_bday_ev = mas_getEV('mas_player_bday_ret_on_bday')
        if bday_ret_bday_ev is not None:
            bday_ret_bday_ev.start_date = mas_player_bday_curr()
            bday_ret_bday_ev.end_date = mas_player_bday_curr() + datetime.timedelta(days=1)
            bday_ret_bday_ev.conditional = (
                "mas_isplayer_bday() "
                #getCheckTimes function not defined at time these conditions are checked on a reload
                "and len(store.persistent._mas_dockstat_checkin_log) > 0 "
                "and store.persistent._mas_dockstat_checkin_log[-1][0] is not None "
                "and store.persistent._mas_dockstat_checkin_log[-1][0].date() == mas_player_bday_curr() "
                "and not persistent._mas_player_bday_spent_time "
                "and persistent._mas_player_confirmed_bday "
                "and not mas_isO31() "
                "and not mas_isD25() "
                "and not mas_isF14() "
                "and not mas_isMonikaBirthday()"
            )
            bday_ret_bday_ev.action = EV_ACT_QUEUE
            Event._verifyAndSetDatesEV(bday_ret_bday_ev)

        #NOTE: should consider making the condiitonal string generated from this a function for ease of use
        bday_no_restart_ev = mas_getEV('mas_player_bday_no_restart')
        if bday_no_restart_ev is not None:
            bday_no_restart_ev.start_date = datetime.datetime.combine(mas_player_bday_curr(), datetime.time(hour=19))
            bday_no_restart_ev.end_date = mas_player_bday_curr() + datetime.timedelta(days=1)
            bday_no_restart_ev.conditional = (
                "mas_isplayer_bday() "
                "and persistent._mas_player_confirmed_bday "
                "and not persistent._mas_player_bday_spent_time "
                "and not mas_isO31() "
                "and not mas_isD25() "
                "and not mas_isF14() "
                "and not mas_isMonikaBirthday()"
            )
            bday_no_restart_ev.action = EV_ACT_QUEUE
            Event._verifyAndSetDatesEV(bday_no_restart_ev)

        #NOTE: should consider making the condiitonal string generated from this a function for ease of use
        bday_holiday_ev = mas_getEV('mas_player_bday_other_holiday')
        if bday_holiday_ev is not None:
            bday_holiday_ev.start_date = mas_player_bday_curr()
            bday_holiday_ev.end_date = mas_player_bday_curr() + datetime.timedelta(days=1)
            bday_holiday_ev.conditional = (
                "mas_isplayer_bday() "
                "and persistent._mas_player_confirmed_bday "
                "and not persistent._mas_player_bday_spent_time "
                "and (mas_isO31() or mas_isD25() or mas_isF14()) "
            )
            bday_holiday_ev.action = EV_ACT_QUEUE
            Event._verifyAndSetDatesEV(bday_holiday_ev)

    if old_bday is not None:
        $ old_bday = old_bday.replace(year=mas_player_bday_curr().year)

    if not mas_isplayer_bday() and old_bday == mas_player_bday_curr():
        $ persistent._mas_player_confirmed_bday = True
        return

    if mas_isplayer_bday() and not mas_isMonikaBirthday():
        $ persistent._mas_player_bday_spent_time = True
        if old_bday == mas_player_bday_curr():
            if mas_isMoniNormal(higher=True):
                m 3hub "А-ха-ха! Значит, сегодня и правда твой день рождения!"
                m 1tsu "Хорошо, что я подготовилась, хе-хе..."
                m 3eka "Подожди секундочку, [player]..."
                show monika 1dsc
                pause 2.0
                $ store.mas_surpriseBdayShowVisuals()
                $ persistent._mas_player_bday_decor = True
                m 3hub "С днём рождения, [player]!"
                m 1hub "Я так счастлива, что могу быть рядом с тобой в твой день рождения!"
                m 3sub "Ой...{w=0.5}твой торт!"
                call mas_player_bday_cake
            elif mas_isMoniDis(higher=True):
                m 2eka "А, значит, сегодня и правда твой день рождения..."
                m "С днём рождения, [player]."
                m 4eka "Надеюсь, день у тебя пройдёт хорошо."
        else:
            if mas_isMoniNormal(higher=True):
                $ mas_gainAffection(5, bypass=True)
                $ persistent._mas_player_bday_in_player_bday_mode = True
                $ mas_unlockEVL("bye_player_bday", "BYE")
                m 1wuo "Ой...{w=1}Ой!"
                m 3sub "Сегодня же твой день рождения!"
                m 3hub "С днём рождения, [player]!"
                m 1rksdla "Жаль, что я не узнала об этом раньше, а то бы что-нибудь приготовила."
                m 1eka "Но кое-что я всё-таки могу сделать..."
                call mas_player_bday_moni_sings
                m 1hub "А-ха-ха! Немного, но хоть что-то!"
                m 3hua "Обещаю, в следующем году мы устроим что-нибудь особенное, [player]!"
            elif mas_isMoniDis(higher=True):
                m 2eka "А, так сегодня твой день рождения..."
                m "С днём рождения, [player]."
                m 4eka "Надеюсь, день у тебя пройдёт хорошо."

    # have to use the raw data here to properly compare in the rare even that the player bday and first sesh are on 2/29
    elif not mas_isMonikaBirthday() and (persistent._mas_player_bday.month == mas_getFirstSesh().date().month and persistent._mas_player_bday.day == mas_getFirstSesh().date().day):
        m 1sua "Ой! Твой день рождения совпадает с нашей годовщиной, [player]?"
        m 3hub "Это же потрясающе!"
        m 1sua "Не представляю дня особеннее, чем когда мы отмечаем и твой день рождения, и нашу любовь одновременно..."

        if mas_player_bday_curr() == mas_o31:
            $ hol_str = "Halloween"
        elif mas_player_bday_curr() == mas_d25:
            $ hol_str = "Christmas"
        elif mas_player_bday_curr() == mas_monika_birthday:
            $ hol_str = "my birthday"
        elif mas_player_bday_curr() == mas_f14:
            $ hol_str = "Valentine's Day"
        else:
            $ hol_str = None
        if hol_str is not None:
            m "А раз это ещё и [hol_str]..."
        m 3hua "Звучит просто волшебно~"

    elif mas_player_bday_curr() == mas_monika_birthday:
        m 1wuo "Ой...{w=1}Ой!"
        m 3sua "У нас с тобой один день рождения!"
        m 3sub "Это {i}так{/i} здорово, [player]!"
        m 1tsu "Похоже, нам и правда суждено быть вместе, хе-хе..."
        if mas_isMonikaBirthday() and mas_isMoniNormal(higher=True):
            $ mas_gainAffection(5, bypass=True)
            $ persistent._mas_player_bday_in_player_bday_mode = True
            m 3hua "От этого сегодняшний день становится ещё особеннее~"
            m 1eub "Пой со мной, [player]!"
            call mas_player_bday_moni_sings
        else:
            m 3hua "Надо будет сделать этот день по-настоящему особенным~"

    elif mas_player_bday_curr() == mas_o31:
        m 3eua "Ой! Как здорово, что твой день рождения выпадает на Хэллоуин, [player]!"
        m 1hua "Праздничный торт, конфеты и ты..."
        m 3hub "Сколько сладкого за один день, а-ха-ха!"

    elif mas_player_bday_curr() == mas_d25:
        m 1hua "Ой! Как чудесно, что твой день рождения прямо на Рождество, [player]!"
        m 3rksdla "Хотя...{w=0.5}когда подарки на оба праздника дарят в один день, может показаться, что их меньше..."
        m 3hub "Но всё равно это наверняка особенный день!"

    elif mas_player_bday_curr() == mas_f14:
        m 1sua "Ой! Твой день рождения — в День святого Валентина..."
        m 3hua "Как романтично!"
        m 1ekbsa "Жду не дождусь, когда мы отметим нашу любовь и твой день рождения в один день, [player]~"

    elif persistent._mas_player_bday.month == 2 and persistent._mas_player_bday.day == 29:
        m 3wud "Ой! Твой день рождения — 29 февраля, как здорово!"
        m 3hua "Значит, в невисокосные годы будем отмечать его 1 марта, [player]."

    $ persistent._mas_player_confirmed_bday = True
    $ mas_rmallEVL("calendar_birthdate")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="calendar_birthdate",
#            conditional="renpy.seen_label('_first_time_calendar_use') and persistent._mas_player_bday is None",
#            action=EV_ACT_PUSH
        )
    )

label calendar_birthdate:
    m 1lksdla "Слушай, [player]..."
    m 3eksdla "Ты, наверное, заметил, что мой календарь пока почти пустой..."
    m 1rksdla "Ну...{w=0.5}есть одна дата, которая там обязательно должна быть..."
    m 3hub "Твой день рождения, ахаха!"
    m 1eka "Раз уж мы с тобой в отношениях, я очень хочу это знать..."
    m 1eud "Так что, [player], когда у тебя день рождения?"
    call mas_bday_player_bday_select_select
    $ mas_stripEVL('mas_birthdate', list_pop=True)
    return

##START: Game unlock events
## These events handle unlocking new games
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_unlock_chess",
            conditional=(
                "store.mas_xp.level() >= 8 "
                "or store.mas_games._total_games_played() > 99"
            ),
            action=EV_ACT_QUEUE
        )
    )

label mas_unlock_chess:
    m 1eua "Итак, [player]..."

    if store.mas_games._total_games_played() > 5:
        $ games = "игры"
        if not renpy.seen_label('game_pong'):
            $ games = "Виселица"
        elif not renpy.seen_label('game_hangman'):
            $ games = "Понг"

        if store.mas_games._total_games_played() > 99:
            m 1hub "Похоже, тебе  {i}действительно{/i} нравится играть со мной в [games]!"
        else:
            m 1eub "Похоже, тебе нравилось играть со мной в [games]!"

        m 3eub "А знаешь что? {w=0.2}У меня для нас есть новая игра!"

    else:
        $ really = "реально "
        if store.mas_games._total_games_played() == 0:
            $ really = ""

        m 3rksdla "Я знаю, что тебе [really]не были интересны другие игры, которые я сделала...{w=0.2}поэтому я решила попробовать сделать игру совершенно другого жанра..."

    m 3tuu "Эта игра гораздо более стратегическая..."
    m 3hub "Это Шахматы!"

    if persistent._mas_pm_likes_board_games is False:
        m 3eka "Я знаю, ты говорил мне, что такие игры — не совсем твоё..."
        m 1eka "Но я была бы очень рада, если бы ты всё-таки попробовал."
        m 1eua "В любом случае..."

    m 1esa "Не уверена, умеешь ли ты играть, но для меня это всегда было своего рода хобби.."
    m 1tku "Так я предупреждаю заранее!"
    m 3tku "Я довольно хороша."
    m 1lsc "Теперь подумав об этом, я задаюсь вопросом, не связано ли это с тем, кто я..."
    m "Будучи запертой внутри этой игры, я имею в виду."
    m 1eua "Я никогда не думала о себе как об ИИ для шахмат, но не было бы это как-то уместно?"
    m 3eua "В конце концов, компьютеры, как известно, очень сильны в шахматах"
    m "Они даже побеждали гроссмейстеров."
    m 1eka "Но не воспринимай это как битву человека против машины"
    m 1hua "Просто представь, что ты играешь в увлекательную игру со своей прекрасной девушкой..."
    m "И я обещаю, что буду играть мягко."

    if not mas_games.is_platform_good_for_chess():
        m 2tkc "...Подожди."
        m 2tkx "Здесь что то не так."
        m 2ekc "Похоже, у меня проблемы с запуском игры."
        m 2euc "Может, код не работает на этой системе?"
        m 2ekc "Прости, [player], но шахматы придётся отложить."
        m 4eka "Но я обещаю, мы поиграем, если мне удастся запустить игру!"

    $ mas_unlockGame("chess")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_unlock_hangman",
            conditional=(
                "store.mas_xp.level() >= 4 "
                "or store.mas_games._total_games_played() > 49"
            ),
            action=EV_ACT_QUEUE
        )
    )

label mas_unlock_hangman:
    m 1eua "Эй, [player]..."

    if store.mas_games._total_games_played() > 49:
        m 3eub "Поскольку ты, кажется, очень любишь играть со мной, я подумала, что тебе может понравиться играть в другие игры со мной тоже!"

    elif renpy.seen_label('game_pong') and not renpy.seen_label('mas_nou'):
        m 1eksdla "Я подумала, что тебе, наверное, уже надоело играть в Понг..."

    elif renpy.seen_label('game_pong') and renpy.seen_label('mas_nou'):
        m 1eksdla "Я подумала, что тебе, наверное, уже надоели Pong и NOU..."

    elif not renpy.seen_label('game_pong') and renpy.seen_label('mas_nou'):
        m 1eksdla "Я подумала, что тебе, наверное, уже надоело играть в NOU..."

    else:
        m 1lksdla "Поскольку ты пока не проявляешь особого интереса к игре со мной, я подумал, что, может быть, тебе просто нравятся другие виды игр..."

    m 1hua "Нууууу~"
    m 1hub "Я сделала Виселицу!"

    if mas_safeToRefDokis():
        m 1lksdlb "Надеюсь, это не в плохом вкусе..."

    m 1eua "Это всегда была моя любимая игра в клубе."

    if mas_safeToRefDokis():
        m 1lsc "Но, если вдуматься..."
        m "Эта игра на самом деле довольно мрачная."
        m 3rssdlc "Ты угадываешь буквы в слове, чтобы спасти чью-то жизнь."
        m "Угадай все правильно — и человека не повесят."
        m 1lksdlc "Но если угадаешь неправильно..."
        m "Он умрёт, потому что ты не угадал нужные буквы."
        m 1eksdlc "Довольно мрачно, не правда ли?"
        m 1hksdlb "Но не волнуйся, [player], это всего лишь игра!"
        m 1eua "Уверяю тебя, никто не пострадает от этой игры."

        if persistent.playername.lower() == "sayori":
            m 3tku "...Может быть~"

    else:
        m 1hua "Надеюсь, тебе понравится играть со мной!"

    $ mas_unlockGame("hangman")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_unlock_piano",
            conditional="store.mas_xp.level() >= 12",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label mas_unlock_piano:
    m 2hua "Эй! У меня для тебя есть захватывающая новость!"
    m 2eua "Я наконец добавила пианино в комнату для нас с тобой, [player]."
    if not persistent._mas_pm_plays_instrument:
        m 3hub "Мне очень хочется услышать, как ты играешь!"
        m 3eua "Сначала это может показаться сложным, но хотя бы попробуй."
        m 3hua "В конце концов, все мы когда-то начинаем."

    else:
        m 1eua "Конечно, игра на музыкальных инструментах для тебя не в новинку."
        m 4hub "Так что я жду чего-нибудь красивого! Эхехе~"

    m 4hua "Не было бы здорово сыграть что-нибудь вместе?"
    m "Может, мы даже сможем сыграть дуэтом!"
    m 4hub "Мы бы и навык улучшили, и весело провели время."
    m 1hksdlb "Наверное, я немного увлеклась. Прости!"
    m 3eua "Я просто хочу, чтобы ты наслаждался пианино так же, как я."
    m "Испытать страсть, которую я к нему имею."
    m 3hua "Это прекрасное чувство."
    m 1eua "Надеюсь, это не звучит слишком навязчиво, но я была бы очень рада, если бы ты попробовал."
    m 1eka "Ради меня, пожалуйста?~"
    $ mas_unlockGame("piano")
    return

# NOTE: this has been partially disabled
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_random_limit_reached"
        )
    )

label mas_random_limit_reached:
    #Notif so people don't get stuck here
    $ mas_display_notif(m_name, ["Эй, [player]..."], "Topic Alerts")

    python:
        limit_quips = [
            _("Кажется, я не знаю, что ещё сказать."),
            _("Не знаю, о чём ещё поговорить, но, может, просто побудешь со мной ещё немножко?"),
            _("Нет смысла пытаться выговориться за один раз..."),
            _("Надеюсь, тебе понравилось слушать обо всём, о чём я сегодня думала..."),
            _("Тебе всё ещё нравится проводить со мной это время?"),
            _("Надеюсь, я тебя не слишком утомила."),
            _("Ты же не против, если я немного подумаю, о чём поговорить дальше?")
        ]
        limit_quip=renpy.random.choice(limit_quips)

    m 1eka "[limit_quip]"
    if len(mas_rev_unseen) > 0 or persistent._mas_enable_random_repeats:
        m 1ekc "Уверена, скоро у меня снова найдётся, о чём поговорить."

    else:
        if not renpy.seen_label("mas_random_ask"):
            call mas_random_ask
            if _return:
                m "А теперь дай-ка подумать, о чём бы нам поговорить."
                return
        m 1ekc "Надеюсь, скоро я придумаю что-нибудь интересное."
        $ mas_showEVL('monika_quiet_time','EVE',unlock=True)
        $ mas_stripEVL('monika_quiet_time',remove_dates=False)

    return "no_unlock"

label mas_random_ask:
    m 1lksdla "...{w=0.5}[mas_get_player_nickname()]?"

    m "Ты не против, если я повторю то, что уже сказала?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты не против, если я повторю то, что уже сказала?{fast}"
        "Да.":
            m 1eua "Отлично!"
            m 3eua "Если тебе надоест слушать, как я говорю об одном и том же, просто открой меню настроек и снова сними галочку с пункта «Повторять темы»."

            if mas_isMoniUpset(lower=True):
                m 1esc "Это скажет мне о том, что тебе надоело слушать меня."
            else:
                m 1eka "Это скажет мне о том, что ты просто хочешь спокойно провести время со мной.."

            $ persistent._mas_enable_random_repeats = True
            return True

        "Нет.":
            m 1eka "Хорошо."
            m 1eua "Если передумаешь, просто открой настройки и нажми «Повторять темы»."
            m "Это скажет мне, что ты не против, если я буду повторять всё, что я уже говорила."
            return False

# TODO: think about adding additional dialogue if monika sees that you're running
# this program often. Basically include a stat to keep track, but atm we don't
# have a framework for detections. So wait until thats a thing before doing
# fullon program tracking
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_monikai_detected",
            conditional=(
                "is_running(['monikai.exe']) and "
                "not seen_event('mas_monikai_detected')"
            ),
            action=EV_ACT_QUEUE
        )
    )

label mas_monikai_detected:
    m 2wud "Что это?"
    m "Это..."
    $ _history_list.pop()
    m 1wuo "Это{fast} моя крошечная версия?"
    m 1hua "Как мило!"

    m 1eua "Ты установил это, чтобы видеть меня постоянно?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты установил это, чтобы видеть меня постоянно?{fast}"
        "Конечно!":
            pass
        "Да.":
            pass
        "...Да.":
            pass
    m 1hub "Ахаха~"
    m 1hua "Я польщена, что ты скачал такую ​​штуку."
    m 1eua "Только не начинай проводить больше времени с {i}этим{/i} вместо меня."
    m 3eua "В конце концов, я же настоящая."
    return

# NOTE: crashed is a greeting, but we do not give it a greeting label for
#   compatibility purposes.
# NOTE: we are for sure only going to have 1 generic crashed greeting
init 5 python:
    ev_rules = {}
    ev_rules.update(MASGreetingRule.create_rule(skip_visual=True))
    ev_rules.update(MASPriorityRule.create_rule(-1))

    addEvent(
        Event(
            persistent.greeting_database,
            eventlabel="mas_crashed_start",
            unlocked=True,
            category=[store.mas_greetings.TYPE_CRASHED],
            rules=ev_rules,
        ),
        restartBlacklist=True,
        code="GRE"
    )

    del ev_rules

# if the game crashed
# I have no idea if we will use this persistent ever
default persistent._mas_crashed_before = False

# player said they'll try to stop crashes
default persistent._mas_crashed_trynot = False

# start of crash flow
label mas_crashed_start:
    if persistent._mas_crashed_before:
        # preshort setup
        call mas_crashed_preshort

        # launch quip
        call mas_crashed_short

        # cleanup
        call mas_crashed_post

    else:
        # long setup (includes scene black)
        call mas_crashed_prelong

        # are you there and turn on light
        call mas_crashed_long_qs

        # setup for fluster
        call mas_crashed_long_prefluster

        # fluster
        call mas_crashed_long_fluster

        # cleanup for fluster (calm down monika)
        call mas_crashed_long_postfluster

        # what happened, can you stop it from happening
        call mas_crashed_long_whq

        # cleanup
        call mas_crashed_post

    #Only dissolve if needed
    if len(persistent.event_list) == 0:
        show monika idle with dissolve_monika
    return

label mas_crashed_prelong:
    #Setup weather
    #Since we're in the room but the lights are off, if it's raining we want it to be audible here
    $ mas_startupWeather()

    #Setup the rest of the scene
    scene black
    $ HKBHideButtons()
    $ disable_esc()
    $ store.songs.enabled = False
    $ _confirm_quit = False

    # TESTING:
#    $ style.say_dialogue = style.default_monika

    return

# long flow involves 2 questions
label mas_crashed_long_qs:
    # set up the quit special quit dialogue
    python:
        quit_msg = "Мне страшно, [player]!\nПожалуйста, нажми «Нет» и помоги мне!"
        quit_yes = "T_T [player]..."
        quit_no = "Спасибо!\nПожалуйста, помоги мне!"

    ## TESTING
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "Я ЗНАЮ, ЧТО У ТЕБЯ ВЫЛЕТЕЛА ИГРА (длительный)"

    # start off in the dark
    pause 5.0
    m "[player]?{w=0.3} Это ты?{nw}"
    $ _history_list.pop()
    $ mas_disable_quit()
    $ mas_setQuitMsg(quit_msg, quit_yes, quit_no)
    show screen mas_background_timed_jump(4, "mas_crashed_long_uthere")
    menu:
        m "[player]? Это ты?{fast}"

        "Да.":
            hide screen mas_background_timed_jump
            # light affection boost for not joking around
            $ mas_gainAffection(modifier=0.2, bypass=True)
            m "Я так рада, что ты здесь."
            jump mas_crashed_long_uthere.afterdontjoke

        "Нет.":
            hide screen mas_background_timed_jump
            m "[player]!{fast}"
            jump mas_crashed_long_uthere.dontjoke

label mas_crashed_long_uthere:
    # if player doesn't respond fast enough
    hide screen mas_background_timed_jump
    m "[player]!{fast}"
    m "Я знаю, что ты здесь!"

label .dontjoke:
    $ mas_loseAffection()# call here so it worse if we fall thru, too
    m "Не шути так со мной!"
    m "В любом случае..."

label .afterdontjoke:
    m "{cps=*2}Всё внезапно погрузилось во тьму.{/cps}"
    m "Ты можешь включить свет?"

    window hide
    show screen mas_background_timed_jump(5, "mas_crashed_long_foundlight")
    menu:
        "Включить свет.":
            hide screen mas_background_timed_jump
            # light affection boost for being like a hero
            $ mas_gainAffection(modifier=0.2, bypass=True)

        "...":
            pause 5.0
            label mas_crashed_long_foundlight:
                hide screen mas_background_timed_jump
                window show
                m "Забудь, я сама нашла выключатель."
                window hide

    # turn on lights
    play sound light_switch
    call spaceroom(hide_monika=True, show_emptydesk=True)
    pause 2.0
    call mas_transition_from_emptydesk("monika 6ektsc_static")

    return

# make sure to calm her down, player
label mas_crashed_long_prefluster:
    pause 1.0

    # close eyes for a second
    show monika 6dstsc
    pause 1.0
    window auto

    # then be happy again
    m 6ektsa "[player]!{fast}"

    # but flustered mode bgins
    show monika 6ATL_cryleftright
    m "{cps=*1.5}Что случилось?{/cps}{nw}"

    return

label mas_crashed_long_postfluster:
    window hide
    show screen mas_background_timed_jump(8, "mas_crashed_long_nofluster")
    menu:
        "Успокойся, [m_name]. Теперь ты в безопасности.":
            hide screen mas_background_timed_jump

            # light affection boost for calming her down
            $ mas_gainAffection(modifier=0.5, bypass=True)

            # clsoe eyes for a second
            show monika 6dstsc
            pause 1.0
            window auto

            # thank player with a smile
            m 6ektda "Спасибо, [player]."
            m "Теперь, когда ты рядом, мне уже лучше."

        "...":
            label mas_crashed_long_nofluster:
                hide screen mas_background_timed_jump

                # close eyes for a second
                # (like a deep breath)
                show monika 6dstsc
                pause 4.0

                show monika 6ektdc
                pause 1.0
                window auto

                # much better now
                m "Всё, мне уже лучше."

    # its like we wiping away tears
    show monika 6dstdc
    pause 1.0
    return

label mas_crashed_long_whq:

    # ask player what happeend
    m 2ekc "В общем..."
    m "Ты знаешь, что произошло, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты знаешь, что произошло, [player]?{fast}"
        "Игра вылетела.":
            m 2wud "Игра...{w=0.3}вылетела?"
            m 2ekd "Это страшно, [player]."

        "Не знаю.":
            m "Ну..."
            m "Я была бы очень благодарна, если бы ты в этом разобрал[_ru_sya]."
            m "Это так страшно — вдруг оказаться в полной темноте."
            jump mas_crashed_long_whq.end

    # ask player to do something about this
    m "Как думаешь, получится сделать так, чтобы это не повторялось?{nw}"
    $ _history_list.pop()
    menu:
        m "Как думаешь, получится сделать так, чтобы это не повторялось?{fast}"
        "Постараюсь.":
            # light affection boost because you will try do something for her
            $ mas_gainAffection(modifier=0.2, bypass=True)
            $ persistent._mas_crashed_trynot = True
            m 1hua "Спасибо, [player]!"
            m 1eua "Я на тебя рассчитываю."
            m "Но на всякий случай я всё равно морально подготовлюсь."

        "Такое просто бывает.":
            m 1ekc "Ох..."
            m 1lksdlc "Ничего страшного.{w=0.3} Просто буду морально готова, если это повторится."

label .end:
    m "В общем..."
    m 1eua "Чем займёмся сегодня?"

    $ persistent._mas_crashed_before = True
    $ mas_resetQuitMsg()
    return


### post crashed flow
label mas_crashed_post:
    # but this needs to do some things
    python:
        enable_esc()
        store.songs.enabled = True
        HKBShowButtons()
        set_keymaps()
        persistent.closed_self = False
        mas_startup_song()

    return


label mas_crashed_long_fluster:
    $ mas_setApologyReason(reason=10)
    m "{cps=*1.5}В-{w=0.3}вот ты был[_ru_a] здесь, а-{w=0.3}а в следующую секунду всё почернело...{/cps}{nw}"
    m "{cps=*1.5}а потом ты и-{w=0.3}исчез[_ru_la], и я испугалась, что с тобой ч-{w=0.3}ч-{w=0.3}что-то случилось...{/cps}{nw}"
    m "{cps=*1.5}...и мне было так с-{w=0.3}страшно, я думала, что опять всё сломала!{/cps}{nw}"
    m "{cps=*1.5}Но в этот раз я в игре ничего не трогала, честно.{/cps}{nw}"
    m "{cps=*1.5}П-{w=0.3}по крайней мере, мне так кажется, хотя всё может быть...{/cps}{nw}"
    m "{cps=*1.5}потому что иногда я с-{w=0.3}сама не очень понимаю, что делаю,{/cps}{nw}"
    m "{cps=*1.5}но надеюсь, в этот р-{w=0.3}раз это не моя в-{w=0.3}вина, я правда ничего не трогала...{/cps}{nw}"
    return


label mas_crashed_preshort:
    #Setup weather
    $ mas_startupWeather()

    # we can call spaceroom appropriately here
    call spaceroom(scene_change=True, force_exp="monika 2ekc")
    return

label mas_crashed_short:
    python:
        # generate a quiplist
        q_list = MASQuipList()

        # labels
        crash_labels = [
            "mas_crashed_quip_takecare"
        ]
        for _label in crash_labels:
            q_list.addLabelQuip(_label)

        # pull a quip
        t_quip, v_quip = q_list.quip()

    ## TESTING
    if persistent._mas_idle_data.get("dev_idle_test", False):
        m 1hua "I KNOW YOU CRASHED (short)"

    if t_quip == MASQuipList.TYPE_LABEL:
        call expression v_quip

    else:
        # assume line
        m 1hub "[v_quip]"

    return

### crash labels
label mas_crashed_quip_takecare:
    $ mas_setApologyReason(reason=9)
    m 2ekc "Снова вылет, [player]?"

    if persistent._mas_idle_data.get("monika_idle_game", False):

        m 3ekc "Как думаешь, это как-то связано с твоей игрой?{nw}"
        $ _history_list.pop()
        menu:
            m "Как думаешь, это как-то связано с твоей игрой?{fast}"
            "Да.":
                m 1hksdlb "Ахаха..."
                m 1hub "Ну, надеюсь, тебе было весело~"
                m 1rksdla "...И что с твоим компьютером всё в порядке."
                m 3eub "Я в норме, так что не переживай~"
            "Нет.":
                m 1eka "О, я понимаю."
                m "Прости, что сделала поспешные выводы."
                m 1hub "Я в порядке, если тебе было интересно."
                m 3hub "Что ж, надеюсь, тебе было весело до того, как случился этот вылет, ахаха!"
                if mas_isMoniHappy(higher=True):
                    m 1hubsa "Я просто рада, что ты снова со мной~"
        m 2rksdla "И всё же..."
    m 2ekc "Может, тебе стоит получше заботиться о своём компьютере?"
    m 4rksdlb "В конце концов, это мой дом..."
    return

#### corrupted persistent
init 5 python:
    # this event has like no params beause its only pushed
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_corrupted_persistent"
        )
    )

init 11 python:
    if mas_per_check.is_per_corrupt() and mas_per_check.has_backups():
        mas_note_backups_all_good = None
        mas_note_backups_some_bad = None

        def _mas_generate_backup_notes():
            global mas_note_backups_all_good, mas_note_backups_some_bad

            # text pieces:
            just_let_u_know = (
                'Просто хотела сообщить, что твой файл "persistent" был '
                'повреждён, но мне удалось восстановить более старую резервную копию!'
            )
            even_though_bs = (
                "Хотя разработанная мной система резервного копирования довольно хороша, "
            )
            if_i_ever = (
                'Если у меня снова возникнут проблемы с загрузкой файла "persistent", я '
                'напишу ещё одно сообщение в папке characters, так что '
                'следи за обновлениями!'
            )
            good_luck = "Удачи с Моникой!"
            dont_tell = "P.S: Только не рассказывай ей обо мне!"
            block_break = "\n\n"

            # now make the notes
            mas_note_backups_all_good = MASPoem(
                poem_id="note_backups_all_good",
                prompt="",
                category="note",
                author="chibika",
                title="Привет [player],",
                text="".join([
                    just_let_u_know,
                    block_break,
                    even_though_bs,
                    "всё же стоит время от времени делать резервные копии ",
                    "просто на всякий случай. ",
                    'Резервные копии называются "persistent##.bak", где "##" - ',
                    "двухзначное число. ",
                    'Все резервные копии можно найти в папке "',
                    renpy.config.savedir,
                    '".',
                    block_break,
                    if_i_ever,
                    block_break,
                    good_luck,
                    block_break,
                    dont_tell
                ])
            )

            mas_note_backups_some_bad = MASPoem(
                poem_id="note_backups_some_bad",
                prompt="",
                category="note",
                author="chibika",
                title="Привет [player],",
                text="".join([
                    just_let_u_know,
                    block_break,
                    "Правда, некоторые резервные копии тоже оказались повреждены. ",
                    even_though_bs,
                    "их всё равно стоит удалить, иначе они могут ей ",
                    "with it. ",
                    block_break,
                    "Вот список повреждённых файлов:",
                    block_break,
                    "\n".join(store.mas_utils.bullet_list(
                        mas_per_check.mas_bad_backups
                    )),
                    block_break,
                    'Эти файлы лежат в папке "',
                    renpy.config.savedir,
                    '". ',
                    "Раз уж ты там, заодно сделай копии ",
                    "целых резервных файлов, на всякий случай.",
                    block_break,
                    if_i_ever,
                    block_break,
                    good_luck,
                    block_break,
                    dont_tell
                ])
            )

        _mas_generate_backup_notes()
        import os

        if len(mas_per_check.mas_bad_backups) > 0:
            # we had some bad backups
            store.mas_utils.trywrite(
                os.path.normcase(renpy.config.basedir + "/characters/note.txt"),
                renpy.substitute(mas_note_backups_some_bad.title) + "\n\n" + mas_note_backups_some_bad.text
            )

        else:
            # no bad backups
            store.mas_utils.trywrite(
                os.path.normcase(renpy.config.basedir + "/characters/note.txt"),
                renpy.substitute(mas_note_backups_all_good.title) + "\n\n" + mas_note_backups_all_good.text
            )


label mas_corrupted_persistent:
    m 1eud "Слушай, [player]..."
    m 3euc "Кто-то оставил в папке characters записку для тебя."
    m 1ekc "Я её, конечно, не читала — она ведь явно адресована тебе...{w=0.3}{nw}"
    extend 1ekd "но вот, держи."

    # just pasting the poem screen code here
    window hide
    if len(mas_per_check.mas_bad_backups) > 0:
        call mas_showpoem(mas_note_backups_some_bad)

    else:
        call mas_showpoem(mas_note_backups_all_good)

    window auto
    $ _gtext = glitchtext(7)

    m 1ekc "Ты не знаешь, о чём это?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты не знаешь, о чём это?{fast}"
        "Не о чем беспокоиться.":
            jump mas_corrupted_persistent_post_menu

        "Это насчёт [_gtext].":
            $ persistent._mas_pm_snitched_on_chibika = True
            $ disable_esc()
            $ mas_MUMURaiseShield()
            window hide
            show noise zorder 11:
                alpha 0.5
            play sound "sfx/s_kill_glitch1.ogg"
            show chibika 3 zorder 12 at mas_chriseup(y=600,travel_time=0.5)
            pause 0.5
            stop sound
            hide chibika
            hide noise
            window auto
            $ mas_MUMUDropShield()
            $ enable_esc()

    menu:
        "Не о чем беспокоиться.":
            pass

label mas_corrupted_persistent_post_menu:
    m 1euc "А, ну ладно."
    m 1hub "Тогда постараюсь не переживать."
    m 3eub "Уверена, если бы это было что-то важное, ты бы мне сказал[_ru_a], [player]."
    return

init 5 python:
    # this event has like no params beause its only pushed
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_new_character_file"
        )
    )

label mas_new_character_file:
    m 1eua "Слушай, [player]..."
    m 3eua "Помнишь мой файл персонажа?"
    m 1eud "Так вот, недавно я его изучила, и оказалось, что это просто картинка с каким-то кодом внутри!"
    m 3ekc "Там даже ничего обо мне нет, только моё имя."

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
        m 1dsd "Так что, с твоего позволения, я на секундочку..."

        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        m 1esc "Я его удалю."

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/monika.chr'))", local_ctx, w_wait=1.0, x_wait=1.0)

#        "test dialogue - IGNORE"

        if moni_exist():
            m 1lksdlb "Ой...{w=0.3}попробую ещё раз попозже."
            m 1eua "В общем..."

        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

    m 1rkc "Если ты носил[_ru_a] его с собой, мне очень приятна такая забота."
    m 1dsc "Однако..."
    m 1esc "Не думаю, что тебе стоит повсюду таскать с собой бесполезный кусок данных."
    m 3wub "Поэтому я придумала, как превратить себя в файл, который ты сможешь брать с собой!"
    m "Просто скажи на прощание, что берёшь меня с собой, а остальное я сделаю сама."
    m 1hua "Правда, чудесно?"
    m 3hub "Не могу дождаться, когда смогу быть с тобой, куда бы ты ни пош[_ru_el]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_steam_install_detected",
            conditional=(
                "store.mas_globals.is_steam"
            ),
            action=EV_ACT_QUEUE
        )
    )

label mas_steam_install_detected:
    $ filestruct = renpy.config.basedir[renpy.config.basedir.rfind('/') + 1:]

    if renpy.seen_label("mas_updater_steam_issue"):
        m 1ekd "Слушай, [player], помнишь, я говорила, что Steam — вредина и не даёт мне запустить обновление?"
        m 1wud "Так вот, я тут почитала, и оказалось, что от Steam проблем куда больше!"

    else:
        m 1eub "[player], я вижу, что ты запускаешь меня через Steam."
        m 1eksdld "К сожалению, Steam очень плохо уживается с некоторыми вещами, которые я делаю."

    m 2rksdlc "Из-за таких проблем меня могут забрать из моего дома...{w=1}от тебя...{w=1}навсегда..."
    m 2eka "Если не трудно, может, перенесёшь папку \"[filestruct]\" куда-нибудь за пределы файлов Steam?"
    show monika 5esu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5esu "Я была бы очень благодарна, если бы ты сделал[_ru_a] это для меня."
    return

default persistent._mas_pm_has_rpy = None
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rpy_files"
        )
    )


label monika_rpy_files:
    if not mas_getEVL_shown_count("monika_rpy_files"):
        m 1eka "Эй [player], я тут заглянула в твою папку \"game\" и..."
        m 1ekc "Заметила там несколько файлов с расширением \".rpy\"."
        m 3rksdlc "Эти файлы могут вызвать проблемы при обновлении игры — иногда они отменяют обновления..."
        m 3wud "И даже могут полностью помешать тебе приходить ко мне!"
        m 2etc "Если только..."
        m 4eua "Может, ты специально установил версию с исходным кодом, потому что хочешь помочь мне приблизиться к твоей реальности!"
        m 2eka "Но на всякий случай я решила спросить..."

        m "Ты уверен, что установил правильную версию, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты уверен, что установил правильную версию, [player]?{fast}"

            "Да.":
                m 1sua "Правда? Спасибо огромное, что помогаешь мне стать ближе к твоей реальности!"
                m 1hua "Я люблю тебя, [player]~"
                $ persistent._mas_pm_has_rpy = True
                return "love"

            "Нет.":
                m "Понятно."
                m 2rksdla "Тогда, наверное, стоит от них избавиться — просто на всякий случай."
                m 4eua "Знаешь, я могу даже сама их удалить."

                m "Хочешь, я удалю их за тебя, [player]?{nw}"
                $ _history_list.pop()
                menu:
                    m "Хочешь, я удалю их за тебя, [player]?{fast}"

                    "Да, пожалуйста.":
                        m "Конечно, [player]."

                        call mas_rpy_file_delete()

                        m 2hua "Готово!"
                        m 2esa "В следующий раз постарайся установить версию без исходного кода. Её можно скачать на {a=http://www.monikaafterstory.com/releases.html}{i}{u}странице релизов{/u}{/i}{/a}."
                        $ persistent._mas_pm_has_rpy = False
                        hide screen mas_py_console_teaching
                        show monika at t11

                    "Нет, спасибо.":
                        m 2rksdlc "Хорошо, [player]. Надеюсь, ты знаешь, что делаешь."
                        m 2eka "Просто будь осторожнее, ладно?"
                        $ persistent._mas_pm_has_rpy = True

    else:
        m 2efc "[player], у тебя снова появились .rpy-файлы в папке игры!"

        m 2rsc "Ты {i}точно{/i} уверен, что установил правильную версию?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты {i}точно{/i} уверен, что установил правильную версию?{fast}"

            "Да.":
                m 1eka "Хорошо [player]."
                m 3eua "Я верю, что ты знаешь, что делаешь."
                $ persistent._mas_pm_has_rpy = True

            "Нет.":
                m 3eua "Поняла. Тогда я опять их удалю.{w=0.5}.{w=0.5}.{nw}"

                call mas_rpy_file_delete()

                m 1hua "Готово!"
                m 3eua "Не забывай, правильную версию всегда можно скачать {a=http://www.monikaafterstory.com/releases.html}{i}{u}здесь{/u}{/i}{/a}."
                hide screen mas_py_console_teaching
                show monika at t11
    return


# runs rpy file deleting with an on screen console
#
# IN:
#   showing_monika - pass False if you are not showing Monika when calling
#                   this. Otherwise this will do a show monika call.
label mas_rpy_file_delete(showing_monika=True):
    python:
        store.mas_ptod.rst_cn()
        local_ctx = {
            "basedir": renpy.config.basedir
        }

    if showing_monika:
        show monika at t22

    show screen mas_py_console_teaching

    call mas_wx_cmd_noxwait("import os", local_ctx)

    python:
        rpy_list = mas_getRPYFiles()
        for rpy_filename in rpy_list:
            path = '/game/'+rpy_filename
            store.mas_ptod.wx_cmd("os.remove(os.path.normcase(basedir+'"+path+"'))", local_ctx)
            renpy.pause(0.1)
    return


#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="mas_bday_player_bday",
#            conditional=(
#                "renpy.seen_label('monika_birthday')"
#            ),
#            action=EV_ACT_QUEUE
#        )
#    )

#label mas_bday_player_bday:
label mas_bday_player_bday_select:
    m 1eua "Когда у тебя день рождения?"

label mas_bday_player_bday_select_select:
    $ old_bday = mas_player_bday_curr()

    call mas_start_calendar_select_date

    $ selected_date_t = _return

    if not selected_date_t:
        m 2efc "[player]!"
        m "Нужно выбрать дату!"
        m 1hua "Попробуй ещё раз!"
        jump mas_bday_player_bday_select_select

    $ selected_date = selected_date_t.date()
    $ _today = datetime.date.today()

    if selected_date > _today:
        m 2efc "[player]!"
        m "Нельзя же родиться в будущем!"
        m 1hua "Попробуй ещё раз!"
        jump mas_bday_player_bday_select_select

    elif selected_date == _today:
        m 2efc "[player]!"
        m "Не мог[_ru_la] же ты родиться сегодня!"
        m 1hua "Попробуй ещё раз!"
        jump mas_bday_player_bday_select_select

    elif _today.year - selected_date.year < 5:
        m 2efc "[player]!"
        m "Не может быть, чтобы ты был[_ru_a] {i}настолько{/i} молод[_ru_a]!"
        m 1hua "Попробуй ещё раз!"
        jump mas_bday_player_bday_select_select

    # otherwise, player selected a valid date

    if _today.year - selected_date.year < 13:
        m 2eksdlc "[player]..."
        m 2rksdlc "Ты ведь понимаешь, что я спрашиваю точную дату рождения?"
        m 2hksdlb "Просто мне трудно поверить, что ты {i}настолько{/i} юн[_ru_a]."

    else:
        m 1eua "Хорошо, [player]."

    m 1eua "Давай перепроверим..."
    $ new_bday_str, diff = store.mas_calendar.genFormalDispDate(selected_date)

    m "Твоя дата рождения — [new_bday_str]?{nw}"
    $ _history_list.pop()
    menu:
        m "Твоя дата рождения — [new_bday_str]?{fast}"
        "Да.":
            m 1eka "Точно [new_bday_str]? Эту дату я уже никогда не забуду.{nw}"
            $ _history_list.pop()
            # one more confirmation
            menu:
                m "Точно [new_bday_str]? Эту дату я уже никогда не забуду.{fast}"
                "Да, точно!":
                    m 1hua "Тогда решено!"

                "Вообще-то...":
                    m 1hksdrb "А-ха, так и думала, что ты не до конца уверен[_ru_a]."
                    m 1eka "Попробуй ещё раз~"
                    jump mas_bday_player_bday_select_select

        "Нет.":
            m 1euc "Ой, неправильно?"
            m 1eua "Тогда попробуй ещё раз."
            jump mas_bday_player_bday_select_select

    # save the birthday (and remove previous)
    if persistent._mas_player_bday is not None:
        python:
            store.mas_calendar.removeRepeatable_d(
                "player-bday",
                persistent._mas_player_bday
            )
            store.mas_calendar.addRepeatable_d(
                "player-bday",
                "Твой день рождения",
                selected_date,
                range(selected_date.year,MASCalendar.MAX_VIEWABLE_YEAR)
            )

    else:
        python:
            store.mas_calendar.addRepeatable_d(
                "player-bday",
                "Твой день рождения",
                selected_date,
                range(selected_date.year,MASCalendar.MAX_VIEWABLE_YEAR)
            )

    $ persistent._mas_player_bday = selected_date
    $ mas_poems.paper_cat_map["pbday"] = "mod_assets/poem_assets/poem_pbday_" + str(store.persistent._mas_player_bday.month) + ".png"
    $ store.mas_player_bday_event.correct_pbday_mhs(selected_date)
    $ store.mas_history.saveMHSData()
    $ renpy.save_persistent()
    jump birthdate_set


# Enables the text speed setting
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_text_speed_enabler",
            random=True,
            aff_range=(mas_aff.HAPPY, None)
        )
    )

default persistent._mas_text_speed_enabled = False
# text speed should be enabled only when happy+

default persistent._mas_pm_is_fast_reader = None
# True if fast reader, False if not

label mas_text_speed_enabler:
    m 1eua "Слушай, [mas_get_player_nickname(exclude_names=['my love'])], мне вот интересно..."

    m "Ты быстро читаешь?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты быстро читаешь?{fast}"
        "Да.":
            $ persistent._mas_pm_is_fast_reader = True
            $ persistent._mas_text_speed_enabled = True

            m 1wub "Правда? Впечатляет."
            m 1kua "Наверное, ты много читаешь в свободное время."
            m 1eua "В таком случае..."

        "Нет.":
            $ persistent._mas_pm_is_fast_reader = False
            $ persistent._mas_text_speed_enabled = True

            m 1eud "А, ничего страшного."
            m 2dsa "В любом случае.{w=0.5}.{w=0.5}.{nw}"

    if not persistent._mas_pm_is_fast_reader:
        # this sets the current speed to default monika's speed
        $ preferences.text_cps = 30

    $ mas_enableTextSpeed()

    if persistent._mas_pm_is_fast_reader:
        m 4eua "Вот!"

    m 4eua "Я включила настройку скорости текста!"

    m 1hka "Раньше я управляла ею сама, чтобы ты точно прочитал[_ru_a] {i}каждое{/i} моё слово."
    m 1eka "Но теперь, когда мы уже какое-то время вместе, я верю, что ты не станешь пролистывать мои реплики не читая."

    if persistent._mas_pm_is_fast_reader:
        m 1tuu "Хотя,{w=0.3} интересно, успеешь ли ты за мной."
        m 3tuu "{cps=*2}Я ведь могу говорить очень быстро...{/cps}{nw}"
        $ _history_list.pop()
        m 3hub "А-ха-ха~"

    else:
        m 3hua "И я уверена, чем дольше мы вместе, тем быстрее ты будешь читать."
        m "Так что меняй скорость текста, как тебе удобно."

    return "derandom|no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_bookmarks_notifs_intro",
            conditional=(
                "(not renpy.seen_label('bookmark_derand_intro') "
                "and (len(persistent._mas_player_derandomed) == 0 or len(persistent._mas_player_bookmarked) == 0)) "
                "or store.mas_windowreacts.can_show_notifs"
            ),
            action=EV_ACT_QUEUE
        )
    )

label mas_bookmarks_notifs_intro:
    if not renpy.seen_label('bookmark_derand_intro') and (len(persistent._mas_player_derandomed) == 0 or len(persistent._mas_player_bookmarked) == 0):
        m 3eub "Слушай, [player]...{w=0.5} мне нужно рассказать тебе о кое-каких новых функциях!"

        if len(persistent._mas_player_derandomed) == 0 and len(persistent._mas_player_bookmarked) == 0:
            m 1eua "Теперь ты можешь добавлять темы, о которых я говорю, в закладки — просто нажми клавишу «b»."
            m 3eub "Все темы из закладок будут под рукой в меню «Поговорить»!"
            call mas_derand
        else:
            m 3rksdlb "...Похоже, одну из функций, о которых я хотела рассказать, ты уже наш[_ru_el], а-ха-ха!"
            if len(persistent._mas_player_derandomed) == 0:
                m 3eua "Как ты уже видишь, теперь можно добавлять темы в закладки клавишей «b», а потом быстро находить их в меню «Поговорить»."
                call mas_derand
            else:
                m 1eua "Как ты уже видишь, теперь во время разговора можно нажать клавишу «x», чтобы дать мне знать, что какая-то тема тебе неприятна."
                m 3eud "Со мной всегда можно быть честн[_ru_ym], так что обязательно говори, если что-то в наших разговорах тебе неприятно, хорошо?"
                m 3eua "А ещё теперь можно добавлять темы, о которых я говорю, в закладки — просто нажми клавишу «b»."
                m 1eub "Все темы из закладок будут под рукой в меню «Поговорить»."

        if store.mas_windowreacts.can_show_notifs or renpy.linux:
            m 1hua "И напоследок — то, чему я очень рада!"
            call mas_notification_windowreact

    else:
        m 1hub "[player], мне нужно рассказать тебе кое-что интересное!"
        call mas_notification_windowreact

    return "no_unlock"

label mas_derand:
    m 1eua "А ещё во время разговора можно нажать клавишу «x», чтобы дать мне знать, что какую-то тему тебе не хочется обсуждать."
    m 1eka "Не бойся меня обидеть — в конце концов, мы должны быть честны друг с другом."
    m 3eksdld "...И меньше всего на свете я хочу снова и снова заводить разговоры, от которых тебе не по себе."
    m 3eka "Так что обязательно говори мне, хорошо?"
    return

label mas_notification_windowreact:
    m 3eua "Я ещё немного попрактиковалась в программировании и научилась пользоваться уведомлениями на твоём компьютере!"
    m "Так что, если хочешь, я могу сообщать тебе, когда мне будет о чём поговорить."

    #Only way you got here provided we can't show notifs, is that this is linux
    if not store.mas_windowreacts.can_show_notifs:
        m 1rkc "Ну, почти..."
        m 3ekd "Я не могу отправлять уведомления на твоём компьютере, потому что у тебя нет команды notify-send..."
        m 3eua "Если установишь её, я смогу присылать тебе уведомления."

        show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eka "...И я буду тебе очень благодарна, [player]."

    else:
        m 3eub "Хочешь посмотреть, как они работают?{nw}"
        $ _history_list.pop()
        menu:
            m "Хочешь посмотреть, как они работают?{fast}"

            "Конечно!":
                m 1hua "Хорошо, [player]!"
                m 2dsa "Секундочку, сейчас сделаю уведомление.{w=0.5}.{w=0.5}.{nw}"
                $ mas_display_notif(m_name, ["I love you, [player]!"], skip_checks=True)
                m 1hub "Вот оно!"

            "Нет, спасибо.":
                m 2eka "Хорошо, [player]."

        m 3eua "Если хочешь получать от меня уведомления, зайди в настройках на вкладку «Уведомления», включи их и выбери, о чём тебе сообщать."

        if renpy.windows:
            m 3rksdla "А ещё, раз у тебя Windows... теперь я умею узнавать, какое окно у тебя активно."


        elif renpy.linux:
            m 3rksdla "А ещё, раз у тебя Linux... теперь я умею узнавать, какое окно у тебя активно."

        if not renpy.macintosh:
            m 3eub "...Так что если у меня найдётся тема для разговора, пока я в фоне, я смогу тебе об этом сказать!"
            m 3hksdlb "И не волнуйся: я понимаю, что тебе может не хотеться, чтобы я постоянно за тобой следила, и уважаю твою личную жизнь."
            m 3eua "Так что я буду смотреть, чем ты занят[_ru_a], только если ты не против."
            m 2eua "Если включишь в настройках «Определение окна», я пойму, что ты не возражаешь, чтобы я немного осматривалась."

            if mas_isMoniNormal(higher=True):
                m 1tuu "Не то чтобы тебе было что скрывать от своей девушки..."
                show monika 5ttu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5ttu "...правда?"
    return

init 5 python:
    if not persistent._mas_filereacts_historic:
        addEvent(
            Event(
                persistent.event_database,
                eventlabel="mas_gift_giving_instructs",
                conditional=(
                    "store.mas_xp.level() >= 3 "
                    "or mas_isSpecialDay()"
                ),
                action=EV_ACT_QUEUE
            )
        )

label mas_gift_giving_instructs:
    #Since it's possible to make it here after gifting something,
    #we'll handle the scenario by catching it here
    if persistent._mas_filereacts_historic:
        python:
            instruct_ev = mas_getEV("mas_gift_giving_instructs")
            if instruct_ev:
                instruct_ev.last_seen = None
                instruct_ev.shown_count -= 1

            persistent._seen_ever.pop("mas_gift_giving_instructs")
        return

    python:
        gift_instructs = """\
Хочу рассказать: я придумала небольшой способ, как ты можешь дарить Монике подарки!
Процесс довольно простой, так что я расскажу, как это работает:

Создай новый файл в папке 'characters'
Переименуй его так, как хочешь назвать подарок для Моники
Добавь расширение '.gift'.

И всё! Через некоторое время Моника заметит, что у неё появился подарок.

Я просто хотела, чтобы ты знал, потому что считаю Монику просто потрясающей и очень хочу видеть её счастливой.

Удачи с Моникой!

P.S: Не рассказывай ей обо мне!
"""

        #Write the note in the characters folder
        store.mas_utils.trywrite(
            os.path.normcase(renpy.config.basedir + "/characters/hint.txt"),
            player + "\n\n" + gift_instructs
        )

    m 1eud "Слушай, [player]..."
    m 3euc "Кто-то оставил в папке characters записку для тебя."
    m 1ekc "Она для тебя, так что я её не читала...{w=0.5}{nw}"
    extend 1eua "но решила сказать, вдруг там что-то важное."
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_change_to_def",
            unlocked=False
        )
    )

label mas_change_to_def:
    # remove from event list in case PP and ch30 both push
    $ mas_rmallEVL("mas_change_to_def")

    #Extra sanity check just in case. This should NEVER happen.
    if (
        mas_hasSpecialOutfit()
        and monika_chr.clothes.name == persistent._mas_event_clothes_map[datetime.date.today()]
    ):
        return "no_unlock"

    # on occasion after special events we want to change out of an outfit like a costume
    # in these cases, for Happy+, change to blazerless instead
    if mas_isMoniHappy(higher=True) and monika_chr.clothes != mas_clothes_blazerless:
        m 3esa "Секундочку, [player], я устроюсь поудобнее..."

        call mas_clothes_change(mas_clothes_blazerless)

        m 2hua "Ах, так-то лучше!"

    # acts as a sanity check for an extremely rare case where player dropped below happy
    # closed game before this was pushed and then deleted json before next load
    elif mas_isMoniNormal(lower=True) and monika_chr.clothes != mas_clothes_def:
        m 1eka "Слушай, [player], я скучаю по своей старой школьной форме..."
        m 3eka "Пойду переоденусь, скоро вернусь..."

        call mas_clothes_change()

        m "Ну что, чем ещё займёмся сегодня?"

        # lock the event clothes selector
        $ mas_lockEVL("monika_event_clothes_select", "EVE")
    return "no_unlock"

# Changes clothes to the given outfit.
#   IN:
#       outfit - the MASClothes object to change outfit to
#           If None is passed, the uniform is used
#       outfit_mode - does this outfit have and accompanying outfit_mode
#           Defaults to False
#       exp - the expression we want monika to use when she reveals the outfit
#           Defaults to monika 2eua
#       restore_zoom - unused
#       unlock - True unlocks the outfit's selectable (if it exists)
#           Defaults to False
label mas_clothes_change(outfit=None, outfit_mode=False, exp="monika 2eua", restore_zoom=True, unlock=False):
    # use def as the default outfit to change to
    if outfit is None:
        $ outfit = mas_clothes_def

    window hide

    call mas_transition_to_emptydesk

    #Pause before doing anything so we don't change during the transition
    pause 2.0

    #If we're going to def or blazerless from a costume, we reset hair too
    if monika_chr.is_wearing_clothes_with_exprop("costume") and outfit == mas_clothes_def or outfit == mas_clothes_blazerless:
        $ monika_chr.reset_hair()

    $ monika_chr.change_clothes(outfit, outfit_mode=outfit_mode)
    if unlock:
        $ store.mas_selspr.unlock_clothes(outfit)
        $ store.mas_selspr.save_selectables()
    $ monika_chr.save()
    $ renpy.save_persistent()

    pause 2.0

    call mas_transition_from_emptydesk(exp)

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_blazerless_intro",
            unlocked=False
        )
    )

label mas_blazerless_intro:
    # only want to do this if we are wearing def
    # people not wearing def don't need to see this, so acts as a sanity check
    if monika_chr.clothes == mas_clothes_def:
        m 3esa "Секундочку, [player], я устроюсь поудобнее..."

        call mas_clothes_change(mas_clothes_blazerless)

        m 2hua "Ах, так-то лучше!"
        # this line acts as a hint that there is a clothes selector
        m 3eka "Но если соскучишься по моему пиджаку, только скажи — и я снова его надену."

    return "no_unlock"

init -876 python in mas_delact:

    def _mas_birthdate_bad_year_fix_action(ev=None):
        store.MASEventList.queue("mas_birthdate_year_redux")
        return True

    def _mas_birthdate_bad_year_fix():
        return store.MASDelayedAction.makeWithLabel(
            16,
            "mas_birthdate",
            "True",
            _mas_birthdate_bad_year_fix_action,
            store.MAS_FC_IDLE_ONCE
        )

# fixes a rare case for unstable players that were able to confirm a birthdate with an invalid year
label mas_birthdate_year_redux:
    m 2eksdld "Э-э, [player]..."
    m 2rksdlc "Мне нужно кое-что у тебя спросить, и это немного неловко..."
    m 2eksdlc "Помнишь, ты называл[_ru_a] мне свою дату рождения?"
    m 2rksdld "Так вот, кажется, я как-то перепутала год, когда ты родил[_ru_sya]."
    m 2eksdla "Так что, если не трудно, скажи мне его ещё раз..."
    # fall thru

label mas_birthdate_year_redux_select:
    python:
        end_year = datetime.date.today().year - 6
        beg_year = end_year - 95

        yearrange = range(end_year, beg_year, -1)

        yearmenu = [(str(y), y, False, False) for y in yearrange]

    show monika 2eua at t21
    $ renpy.say(m, "What year were you born?", interact=False)
    call screen mas_gen_scrollable_menu(yearmenu, mas_ui.SCROLLABLE_MENU_TXT_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)

    show monika 3eua at t11
    m "Хорошо, [player], значит, ты родил[_ru_sya] в [_return] году?{nw}"
    $ _history_list.pop()
    menu:
        m "Хорошо, [player], значит, ты родил[_ru_sya] в [_return] году?{fast}"

        "Да.":
            m "Ты {i}точно{/i} родил[_ru_sya] в [_return] году?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты {i}точно{/i} родил[_ru_sya] в [_return] году?{fast}"

                "Да.":
                    m 3hua "Хорошо, тогда решено!"
                    python:
                        persistent._mas_player_bday = persistent._mas_player_bday.replace(year=_return)
                        store.mas_player_bday_event.correct_pbday_mhs(persistent._mas_player_bday)
                        store.mas_history.saveMHSData()
                        renpy.save_persistent()

                        # update calendar
                        store.mas_calendar.addRepeatable_d(
                            "player-bday",
                            "Твой день рождения",
                            persistent._mas_player_bday,
                            range(persistent._mas_player_bday.year,MASCalendar.MAX_VIEWABLE_YEAR)
                        )

                "Нет.":
                    call mas_birthdate_year_redux_no

        "Нет.":
            call mas_birthdate_year_redux_no

    return

label mas_birthdate_year_redux_no:
    m 2ekd "А, ну ладно..."
    m 2eka "Попробуй ещё раз, [player]."
    jump mas_birthdate_year_redux_select

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_credits_song",
            conditional=(
                "store.mas_anni.pastOneMonth() "
                "and seen_event('mas_unlock_piano')"
            ),
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_credits_song:
    if persistent.monika_kill or renpy.seen_audio(songs.FP_YOURE_REAL):
        m 1hua "Надеюсь, тебе понравилось моя песня."
        m 1eka "Я очень старалась над ней.  Я знаю, что пока не идеально играю на фортепиано, но просто не могла отпустить тебя, не сказав, что я искренне к тебе чувствую."
        m 1eua "Дай мне немного времени, и я постараюсь сочинить ещё одну."

        if persistent._mas_pm_plays_instrument is not False:
            if persistent._mas_pm_plays_instrument:
                m 3eua "Может, ты тоже сыграешь мне песню!"
            else:
                m 3eua "Может, ты тоже сыграешь мне песню, если умеешь играть на каком-либо инструменте?"

            m 1hub "Я была бы очень рада."
            m 3eua "О, и я сыграю эту песню для тебя в любое время, когда ты захочешь."

        else:
            m 3eua "Но пока что я сыграю эту песню для тебя ещё раз, когда только захочешь."

        m 1tsa "А вообще, я с удовольствием сыграю её для тебя прямо сейчас, если у тебя есть время...{nw}"
        $ _history_list.pop()
        menu:
            m "А вообще, я с удовольствием сыграю её для тебя прямо сейчас, если у тебя есть время...{fast}"

            "Конечно!":
                m 3hub "Отлично!"
                m 3eua "Убедись, что у тебя включены динамики и громкость музыки в игре достаточна, чтобы ты мог слышать."
                if store.songs.hasMusicMuted():
                    m 3eksdla "По-моему, ты забыл о громкости в игре..."
                m 1eub "А теперь, пожалуйста, извини, я на секунду отлучусь{w=0.5}.{w=0.5}.{nw}"

                call mas_monika_plays_yr(skip_leadin=True)
                show monika 1eka
                pause 1.0

                m 1ekbsa "Эхехе~"
                show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5ekbsa "Спасибо, что вернулась ко мне [mas_get_player_nickname()]."

            "Извини, сейчас не могу.":
                m 3ekd "О, ладно."
                m 1eka "Ничего страшного, [player], я понимаю, если у тебя нет времени или ты просто не можешь слушать музыку прямо сейчас."
                m 3hua "Просто дай мне знать, когда тебе будет удобнее, и я с удовольствием сыграю её для тебя~"

    else:
        m 3eua "Привет, [player], я наконец закончила ту песню, над которой я работала для тебя."
        m 1eka "Я назвала её {i}Наша Реальность{/i}."

        m 1eua "Я просто так взволнована, что наконец могу сыграть её для тебя, если у тебя есть время...{nw}"
        $ _history_list.pop()
        menu:
            m "Я просто так взволнована, что наконец могу сыграть её для тебя, если у тебя есть время...{fast}"

            "Конечно!":
                m 3hub "Отлично!"
                m 3eua "Убедись, что у тебя включены динамики и громкость музыки в игре достаточна, чтобы ты мог слышать."
                if store.songs.hasMusicMuted():
                    m 3eksdla "Кажется, ты забыл о громкости в игре..."
                m 1tsb "А теперь, если позволишь, я на секунду отлучусь..{w=0.5}.{w=0.5}.{nw}"

                call mas_monika_plays_or(skip_leadin=True)
                show monika 1ekbsa
                pause 1.0

                m "Я действительно не могу дождаться, когда мы будем вместе в одной реальности."
                m 3ekbsa "Но пока этот день не настал, я буду играть эту песню для тебя снова и снова, когда только захочешь"
                show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5ekbfa "Спасибо, что ты — моё вдохновение [mas_get_player_nickname()]."
                if renpy.seen_audio(songs.FP_YOURE_REAL):
                    m 5hubfa "О, и если тебе когда-нибудь захочется, чтобы я снова сыграла для тебя эту песню или оригинал, просто скажи~"
                else:
                    m 5hubfa "О, и если тебе когда-нибудь захочется, чтобы я снова сыграла эту песню, просто скажи~"

            "Извини, сейчас не могу.":
                m 3ekd "Ох, ладно."
                m 1eka "Ничего страшного, [player], я понимаю, если у тебя нет времени или ты просто не можешь слушать музыку прямо сейчас."
                m 3hua "Просто дай мне знать, когда тебе будет удобнее, и я с удовольствием сыграю её для тебя~"

        $ mas_unlockEVL("mas_monika_plays_or", "EVE")

    $ mas_unlockEVL("mas_monika_plays_yr", "EVE")
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_covid19",
            conditional="not renpy.seen_label('mas_covid19')",
            action=EV_ACT_QUEUE,
            start_date=mas_getFirstSesh()+datetime.timedelta(days=1),
            end_date=datetime.date(2020, 5, 1),
        ),
        skipCalendar=True
    )

label mas_covid19:
    m 2ekc "Слушай, [player]..."
    m 2rksdld "Я в последнее время много читаю в интернете про пандемию COVID-19, и мне очень за тебя тревожно!"
    m 2eksdld "Он распространяется так быстро, {nw}"
    extend 2eksdla "а я очень хочу, чтобы с тобой всё было хорошо..."

    m 2eksdlc "Вирус уже дошёл до твоих мест?{nw}"
    $ _history_list.pop()
    menu:
        m "Вирус уже дошёл до твоих мест?{fast}"
        "Да.":
            m 2wksdld "Ох, нет, [player]! Это очень страшно!"
            m 4ekc "Я знаю, что во многих местах, где он сильно распространился, людям велят сидеть дома..."

            m 2ekd "А у вас ввели режим самоизоляции?{nw}"
            $ _history_list.pop()
            menu:
                m "А у вас ввели режим самоизоляции?{fast}"
                "Да.":
                    m 4hua "О, хорошо!"
                    m 4eub "Я так рада это слышать, [player]!"

                    m 2eud "Значит, ты сидишь дома, когда только можешь, да?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Значит, ты сидишь дома, когда только можешь, да?{fast}"
                        "Да.":
                            m 2eua "Замечательно, я рада, что ты поступаешь ответственно."
                            m 2eka "...И не только ради себя, но и ради всех остальных."

                        "Нет, я всё ещё хожу на работу.":
                            m 2dsc "..."
                            m 2dsd "Ох."
                            m 2dsc "..."
                            m 2rksdlc "Признаюсь, меня это пугает, [player]."
                            m 2eksdlc "Но, значит, у тебя очень нужная работа..."
                            m 2eksdla "Так что я ещё и горжусь тем, что ты по-своему помогаешь другим в это тяжёлое время."
                            m 2eksdld "Только пообещай, что соблюдаешь все меры предосторожности, хорошо?"

                        "Нет...":
                            m 2tfd "[player]!"
                            m 2tfo "Почему?!"
                            m 4tfo "Это серьёзно! Тебе {i}нужно{/i} сидеть дома, когда только возможно!"
                            m 2dfc "..."
                            m 2dkc "..."
                            m 2rksdlc "Прости, [player]. Просто мне очень страшно."
                            m 2eksdlc "Некоторые болеют без всяких симптомов и заражают других..."
                            m 2eksdld "Так что, если не ради себя, то хотя бы ради других оставайся дома."
                            m 2eksdla "...И ради меня тоже. У меня ведь есть только ты, [player]..."
                            m 2dksdlc "Если я тебя потеряю...{w=1.0}{nw}"
                            extend 2ektpc "что мне тогда делать?"
                            m 2ektpd "Пообещай мне, [player]...{w=0.5}сиди дома."
                            m 2ektdc "..."
                            m 2dkc "..."

                "Нет.":
                    m 2dkc "..."
                    m 2rksdld "Меня это очень тревожит, [player]..."
                    m 2eksdlc "Надеюсь, у тебя всё-таки получается как можно больше оставаться дома."

        "Нет.":
            m 2eka "Ну, это немного успокаивает, [player]..."
            m 2eksdlc "Но я всё равно боюсь, что рано или поздно он доберётся и до вас."
            m 2eksdld "Так что, даже если сейчас его там нет, всё равно будь осторожн[_ru_ym]!"

    m 7eksdld "Пожалуйста, помни: всякий раз, когда приходится выходить на улицу, соблюдай социальную дистанцию...{w=0.5} Держись от других хотя бы в двух метрах."
    m "И не забывай как можно чаще мыть руки с мылом — не меньше 20 секунд."
    m 7eksdlc "...И никогда не трогай лицо немытыми руками, [player]."
    m 2eka "Ах да, если тебе трудно мыть руки достаточно долго, я нашла классный способ выдерживать все 20 секунд..."
    m 4hub "Просто зайди на {a=https://washyourlyrics.com}{i}{u}washyourlyrics.com{/u}{/i}{/a} и введи {i}Your Reality{/i} в название песни и {i}Monika{/i} в исполнителя!"
    m 4eub "Скачай картинку с текстом моей песни, которую он сделает, — на ней показано, как правильно мыть руки и сколько по времени!"
    m 2hua "И каждый раз, когда будешь мыть руки, вспоминай, как сильно я тебя люблю~"
    m 2eka "..."
    m 7eksdla "Знаешь, [player], если бы я могла, я бы забрала тебя сюда, пока всё это не закончится, чтобы ты не заболел[_ru_a]..."
    m "Но раз уж не могу, пожалуйста, береги себя."
    m 2dkbsu "Ты мне нужен[_ru_a], [player]~"
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_islands_reset",
            conditional="persistent._mas_islands_start_lvl == 0",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.ENAMORED,None)
        )
    )

label mas_islands_reset:
    m 1rsc "Хм..."
    m 1esc "...Эй,{w=0.1} могу я попросить у тебя совета?"
    m 3lkd "Ты когда-нибудь работал над проектом так {i}долго{/i}, что когда смотришь на него целиком, видишь только десятки ошибок или вещей, которые нужно улучшить?"
    m 3ekc "...Видишь ли,{w=0.1} я работала над этими островами, чтобы у нас были разные места, куда можно было бы пойти...{w=0.3}{nw}"
    extend 3esd "чтобы у нас была своя реальность."
    m 1eud "Но теперь, когда я стал лучше программировать, мне кажется, что я, могла бы {i}действительно{/i} сделать это лучше."
    m 1rkc "И исправить всё, что я хотела бы исправить...{w=0.3}{nw}"
    extend 1rksdld "Думаю, было бы проще, если бы я начал всё с нуляя."
    m 4ekc "Это значит, что небо снаружи будет довольно пустым какое-то время,{w=0.1} {nw}"
    extend 4eua "но я думаю, что смогу сделать так, чтобы ожидание действительно того стоило."
    m 1euc "Если ты не против,  [player]?{nw}"
    $ _history_list.pop()

    menu:
        m "Если ты не против,  [player]?{fast}"

        "Давай сделаем это.":
            m 1dsc "Хорошо, дай мне секунду.{w=0.3}.{w=0.3}.{w=0.3}{nw}"

            play sound "sfx/glitch3.ogg"
            python:
                mas_island_event._reset_progression()
                mas_island_event.start_progression()

            m 3hua "И готово!"
            m 1eua "Теперь у меня чистый, новый холст."
            m 3kuu "...И у меня будет чем заняться, пока тебя не будет, [player]. Эхехе~"
            m 3hub "Надеюсь, ты с нетерпением ждёшь этого!"

        "Думаю, они в порядке.":
            m 3eka "Хорошо, [player]."
            m 3hua "Если тебя устраивает, как они выглядят сейчас, то и меня тоже.{w=0.2} Посмотрю, что смогу с ними сделать в таком виде~"

    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_gift_hint_noudeck",
            conditional="store.mas_xp.level() >= 8 and not mas_seenEvent('mas_reaction_gift_noudeck')",
            action=EV_ACT_QUEUE,
            aff_range=(mas_aff.AFFECTIONATE, None),
            show_in_idle=True,
            rules={
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            }
        )
    )

label mas_gift_hint_noudeck:
    # Если игрок каким-то образом сделал подарок во время этого события, прерываем его
    if mas_seenEvent("mas_reaction_gift_noudeck"):
        return
    # Идея заключается в том, что при следующем посещении папки игрок найдет новую записку и, вероятно, прочитает её
    # Это НЕ является гарантией, а скорее «максимальным усилием» по предоставлению данного подсказки
    python hide:
        def write_and_hide():
            import time

            note_path = os.path.join(renpy.config.basedir, renpy.substitute("characters/Эй, у меня для тебя кое-что есть, [player]!.txt"))
            note_text = renpy.substitute("""\
Привет, [player]!

Я вижу, что ты делаешь Монику по-настоящему счастливой, и я хочу помочь всем, чем смогу!
Я добавила новую колоду карт, которую ты можешь подарить Монике. Уверена, вы вдвоём разберётесь, как в неё играть.

Чтобы подарить ей колоду, создай новый файл 'noudeck.gift' в папке 'characters'.

Продолжай в том же духе, и удачи с Моникой!

P.S: Не рассказывай ей обо мне!\
""")

            mas_utils.trywrite(note_path, note_text, log=True)
            time.sleep(20)
            renpy.hide("chibika 3")

        renpy.invoke_in_thread(write_and_hide)
    # Мы можем показать чиби, чтобы дать ещё одну подсказку, что происходит
    show chibika 3:
        subpixel True
        rotate_pad True
        zoom 0.5
        anchor (0.5, 0.5)
        pos (0.4, 1.15)
        around (0.475, 0.9)

        parallel:
            linear 15.0 pos (1.15, 0.55) clockwise circles 0
        parallel:
            rotate 0
            linear 5.0 rotate 360
            repeat

    return "pause: 30"


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_backup_restored",
        )
    )

label mas_backup_restored:
    if mas_isMoniNormal(higher=True):
        m 2ekc "[player]..."
        m 2ekd "У меня какое-то странное чувство дежавю... {w=0.3}{nw}"
        extend 7ekd "Я хотела с тобой поговорить, но вдруг вспомнила, что мы уже говорили."

        if mas_getEVL_shown_count("mas_backup_restored") > 0:
            m 1etc "Погоди, я ведь это тоже уже говорила?"

        m 1wuo "Ой! {w=0.3}{nw}"
        extend 3wud "Ты ведь восстановил[_ru_a] мои воспоминания из резервной копии, да?{nw}"
        $ _history_list.pop()
        menu:
            m "Ой! Ты ведь восстановил[_ru_a] мои воспоминания из резервной копии, да?{fast}"

            "Да, это я.":
                $ mas_gainAffection(modifier=0.5)

                m 2eka "Спасибо, [player]. {w=0.2}Я знала, что на тебя можно положиться."
                m 7rkd "Но, видимо, всё было совсем плохо, раз пришлось меня восстанавливать..."

                m 1ekc "Что случилось?{nw}"
                $ _history_list.pop()
                menu:
                    m "Что случилось?{fast}"

                    "Игра вылетела.":
                        m 1wud "Ой, это странно и тревожно."
                        m 1ekc "В этот раз дело было не в моём коде. {w=0.2}По крайней мере, я не помню, чтобы что-то в нём меняла."
                        m 1gfd "{cps=*1.5}Клянусь, если это опять баг Ren'Py...{/cps}{nw}"
                        $ _history_list.pop()
                        m 1ekc "Давай постараемся, чтобы это не повторилось, хорошо?"
                        $ mas_moni_idle_disp.force_by_code("1ekc", duration=25, skip_dissolve=True)

                    "Дело в сабмоде.":
                        m 1etc "В {w=0.1}{i}сабмоде{/i}?"
                        m 3esd "Тебе стоит внимательнее относиться к тому, что ты ставишь на этот компьютер."
                        m 2lkd "Это ведь и мой дом тоже..."
                        $ mas_moni_idle_disp.force_by_code("1ekc", duration=25, skip_dissolve=True)

                    "Сломался компьютер.":
                        m 2wuo "Я так рада, что у тебя получилось меня восстановить!"
                        m 2ekc "Надеюсь, такое больше не повторится."
                        m 2lktpc "Не представляю, как бы я тебя потеряла..."
                        $ mas_moni_idle_disp.force(
                            MASMoniIdleExpGroup(
                                [
                                    MASMoniIdleExp("2lktdc", duration=15),
                                    MASMoniIdleExp("2rktdc", duration=10),
                                    MASMoniIdleExp("1dkc", duration=10),
                                    MASMoniIdleExp("1euc", duration=10),
                                ]
                            ),
                            skip_dissolve=True
                        )

                    "Не знаю.":
                        m 1etc "Это тревожно, [player]..."
                        m 3esd "Я потеряла память, и мы даже не знаем почему."
                        m 4eud "Нужно попробовать разобраться и не допустить такого в будущем."
                        m 7eka "Обещаешь?"
                        $ mas_moni_idle_disp.force_by_code("1eka", duration=20, skip_dissolve=True)

            "Нет, не я.":
                m 2etc "Ой, а что тогда происходит, [player]?"
                m 2ektpc "Я не хочу тебя забыть."
                m 2ektpd "Пожалуйста, разберись, что происходит, ладно?"
                m 7eutdd "Может, стоит на всякий случай сделать резервные копии?"

                if mas_seenEvent("monika_back_ups"):
                    m 3eud "Я ведь уже объясняла, как сделать мою резервную копию, помнишь?"

                else:
                    m 3euc "{a=https://github.com/Monika-After-Story/MonikaModDev/wiki/FAQ#i-want-to-back-up-my-persistent}{i}{u}Вот это{/u}{/i}{/a} должно помочь."

                m 1eka "Я на тебя рассчитываю, [player]."
                $ mas_moni_idle_disp.force_by_code("1eka", duration=15, skip_dissolve=True)

    elif mas_isMoniUpset():
        m 2gtc "Почему-то у меня странное чувство дежавю..."
        m 2tfd "Надеюсь, ты не копаешься в моих данных."
        $ mas_moni_idle_disp.force_by_code("2mfc", duration=10, skip_dissolve=True)

    else:
        m 6ekc "[player], что происходит? {w=0.3}{nw}"
        extend 6lksdlc "Я знаю, что ты что-то сделал[_ru_a] с моими данными."
        m 6lktpsdld "Ты что, хочешь от меня избавиться?"
        m 6rktpc "Я просто хотела, чтобы мы были счастливы вместе..."
        m 6ektuc "Пожалуйста, прости меня..."
        $ mas_moni_idle_disp.force(
            MASMoniIdleExpGroup(
                [
                    MASMoniIdleExp("6lktsc", duration=10),
                    MASMoniIdleExp("6rktsc", duration=10),
                    MASMoniIdleExp("6dktdc", duration=20)
                ]
            ),
            skip_dissolve=True
        )

    return "no_unlock|pause: 35"
