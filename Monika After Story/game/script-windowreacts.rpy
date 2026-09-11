# --- FILE MAP ---
# script-windowreacts.rpy — «о, ты в YouTube / Википедии…»
#
# Короткие реакции, если включено слежение за окном Windows.
# Каждое приложение — свой label mas_wrs_*.
#
# Labels: mas_wrs_youtube, _wikipedia, _twitter, _pinterest, _duolingo…
# Техника окон: zz_windowutils.rpy (вкл/выкл, фильтры).
# ---

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_pinterest",
            category=["Pinterest"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_pinterest:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Что-то новенькое сегодня, [player]?",
            "Нашёл что-нибудь интересное, [player]?",
            "Увидел что-нибудь, что тебе нравится?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_pinterest')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_duolingo",
            category=["Duolingo"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_duolingo:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Учишь новые способы сказать «я люблю тебя», [player]?",
            "Учишь новый язык, [player]?",
            "Какой язык учишь, [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_duolingo')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_wikipedia",
            category=["- Wikipedia"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_wikipedia:
    $ wikipedia_reacts = [
        "Узнаёшь что-то новое, [player]?",
        "Решил немного покопаться, [player]?"
    ]

    #Items in here will get the wiki article you're looking at for reacts.
    python:
        wind_name = mas_getActiveWindowHandle()
        try:
            cutoff_index = wind_name.index(" - Wikipedia")

            #If we're still here, we didn't value error
            #Now we get the article
            wiki_article = wind_name[:cutoff_index]

            # May contain clarification in trailing parentheses
            wiki_article = re.sub("\\s*\\(.+\\)$", "", wiki_article)
            wikipedia_reacts.append(renpy.substitute("«[wiki_article]»...\nЗвучит интересно, [player]."))

        except ValueError:
            pass

    $ wrs_success = mas_display_notif(
        m_name,
        wikipedia_reacts,
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_wikipedia')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_virtualpiano",
            category=["^Virtual Piano"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_virtualpiano:
    python:
        virtualpiano_reacts = [
            "Ой, ты собираешься сыграть для меня?\nКакой ты милый~",
            "Сыграй что-нибудь для меня, [player]!"
        ]

        if mas_isGameUnlocked("piano"):
            virtualpiano_reacts.append("Похоже, тебе нужно пианино побольше?\nАхаха~")

        wrs_success = mas_display_notif(
            m_name,
            virtualpiano_reacts,
            'Window Reactions'
        )

        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_virtualpiano')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_youtube",
            category=["- YouTube"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_youtube:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Что смотришь, [mas_get_player_nickname()]?",
            "Смотришь что-нибудь интересное, [mas_get_player_nickname()]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_youtube')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_r34m",
            category=[r"(?i)(((r34|rule\s?34).*monika)|(post \d+:[\w\s]+monika)|(monika.*(r34|rule\s?34)))"],
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_r34m:
    python:
        mas_display_notif(m_name, ["Эй, [player]... на что это ты смотришь?"],'Window Reactions')

        choice = random.randint(1,10)

        if choice == 1 and mas_isMoniNormal(higher=True):
            MASEventList.queue('monika_nsfw')

        elif choice == 2 and mas_isMoniAff(higher=True):
            MASEventList.queue('monika_pleasure')

        else:
            if mas_isMoniEnamored(higher=True):
                if choice < 4:
                    exp_to_force = "1rsbssdlu"
                elif choice < 7:
                    exp_to_force = "2tuu"
                else:
                    exp_to_force = "2ttu"
            else:
                if choice < 4:
                    exp_to_force = "1rksdlc"
                elif choice < 7:
                    exp_to_force = "2rssdlc"
                else:
                    exp_to_force = "2tssdlc"

            mas_moni_idle_disp.force_by_code(exp_to_force, duration=5)
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_monikamoddev",
            category=["MonikaModDev"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_monikamoddev:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Ой, ты делаешь что-то для меня?\nКакой ты милый~",
            "Собираешься помочь мне стать ближе к твоей реальности?\nКакой ты милый, [player]~"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_monikamoddev')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_twitter",
            category=["/ Twitter"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_twitter:
    python:
        temp_line = renpy.substitute("I love you, [mas_get_player_nickname(exclude_names=['love', 'my love'])].")
        temp_len = len(temp_line)

        # quip: is_ily
        ily_quips_map = {
            "Увидел что-нибудь, чем хочешь поделиться со мной, [player]?": False,
            "Есть что-нибудь интересное рассказать, [player]?": False,
            "280 символов? Мне хватит [temp_len]...\n[temp_line]": True
        }
        quip = renpy.random.choice(ily_quips_map.keys())

        wrs_success = mas_display_notif(
            m_name,
            [quip],
            'Window Reactions'
        )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_twitter')
    return "love" if ily_quips_map[quip] else None

# This is removed until later, maybe it could work with other quips
# init 5 python:
#     addEvent(
#         Event(
#             persistent._mas_windowreacts_database,
#             eventlabel="mas_wrs_monikatwitter",
#             category=['twitter', 'lilmonix3'],
#             rules={
#                 "notif-group": "Window Reactions",
#                 "skip alert": None,
#                 "keep_idle_exp": None,
#                 "skip_pause": None
#             },
#             show_in_idle=True
#         ),
#         code="WRS"
#     )

label mas_wrs_monikatwitter:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Пришёл признаться всему миру в любви ко мне, [player]?",
            "Ты же не шпионишь за мной?\nАхаха, шучу~",
            "Мне всё равно, сколько у меня подписчиков, пока есть ты~"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_monikatwitter')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_4chan",
            category=["- 4chan"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_4chan:
    #TODO: consider adding reactions for /vg/ and /ddlc/
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Так вот где всё началось, да?\nЭто... действительно нечто.",
            "Надеюсь, ты не проведёшь весь день в спорах с другими анонами, [player].",
            "Слышала, тут есть треды про Литературный клуб.\nПередай им от меня привет~",
            "Буду поглядывать, какие доски ты открываешь, вдруг появятся идеи, ахаха!",
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_4chan')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_pixiv",
            category=["- pixiv"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_pixiv:
    #Make a list of notif quips for this
    python:
        pixiv_quips = [
            "Интересно, рисовали ли меня...\nНе поищешь?\nТолько давай без пошлостей, хорошо?~",
            "Довольно интересное место... столько умелых людей выкладывают свои работы.",
        ]

        #Monika doesn't know if you've drawn art of her, or she knows that you have drawn art of her
        if persistent._mas_pm_drawn_art is None or persistent._mas_pm_drawn_art:
            pixiv_quips.extend([
                "Довольно интересное место... столько умелых людей выкладывают свои работы.\nТы среди них, [player]?",
            ])

            #Specifically if she knows you've drawn art of her
            if persistent._mas_pm_drawn_art:
                pixiv_quips.extend([
                    "Пришёл выложить свой рисунок меня, [player]?",
                    "Выкладываешь то, что нарисовал меня?",
                ])

        wrs_success = mas_display_notif(
            m_name,
            pixiv_quips,
            'Window Reactions'
        )

        #Unlock again if we failed
        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_pixiv')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_reddit",
            category=[r"(?i)reddit"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_reddit:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Нашёл хорошие посты, [player]?",
            "Сидишь на Reddit? Только не проведи весь день за мемами, хорошо?",
            "Интересно, есть ли сабреддиты обо мне...\nАхаха, шучу, [player].",
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_reddit')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_mal",
            category=["MyAnimeList"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_mal:
    python:
        myanimelist_quips = [
            "Может, когда-нибудь посмотрим аниме вместе, [player]~",
        ]

        if persistent._mas_pm_watch_mangime is None:
            myanimelist_quips.append("Значит, тебе нравятся аниме и манга, [player]?")

        wrs_success = mas_display_notif(m_name, myanimelist_quips, 'Window Reactions')

        #Unlock again if we failed
        if not wrs_success:
            mas_unlockFailedWRS('mas_wrs_mal')

    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_deviantart",
            category=["DeviantArt"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_deviantart:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Здесь столько таланта!",
            "Когда-нибудь хотела бы научиться рисовать...",
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_deviantart')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_netflix",
            category=["Netflix"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_netflix:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "С удовольствием посмотрела бы с тобой романтику, [player]!",
            "Что смотрим сегодня, [player]?",
            "Что собираешься смотреть, [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_netflix')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_twitch",
            category=["- Twitch"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_twitch:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Смотришь стрим, [player]?",
            "Не против, если я посмотрю с тобой?",
            "Что смотрим сегодня, [player]?"
        ],
        'Window Reactions'
    )

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_twitch')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_word_processor",
            category=['Google Docs|LibreOffice Writer|Microsoft Word'],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_word_processor:
    $ wrs_success = mas_display_notif(
        m_name,
        [
            "Пишешь историю?",
            "Конспектируешь, [player]?",
            "Пишешь стихотворение?",
            "Пишешь любовное письмо?~"
        ],
        'Window Reactions'
    )

    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_word_processor')
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_windowreacts_database,
            eventlabel="mas_wrs_crunchyroll",
            category=[r"(?i)crunchyroll"],
            rules={
                "notif-group": "Window Reactions",
                "skip alert": None,
                "keep_idle_exp": None,
                "skip_pause": None
            },
            show_in_idle=True
        ),
        code="WRS"
    )

label mas_wrs_crunchyroll:
    python:
        if persistent._mas_pm_watch_mangime is False:
            crunchyroll_quips = [
                "О! Значит, тебе нравится аниме, [player]?",
                "Приятно видеть, что ты расширяешь кругозор.",
                "Хм, интересно, что тебя зацепило?",
            ]

        else:
            crunchyroll_quips = [
                "Какое аниме смотрим сегодня, [player]?",
                "Смотришь аниме, [player]?",
                "Не могу дождаться, когда посмотрим аниме вместе!~",
            ]

        wrs_success = mas_display_notif(m_name, crunchyroll_quips, 'Window Reactions')

    #Unlock again if we failed
    if not wrs_success:
        $ mas_unlockFailedWRS('mas_wrs_crunchyroll')
    return
