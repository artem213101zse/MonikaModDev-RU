# MAS OS fake browser — emulates desktop window reactions on Android.
#
# Скриншоты сайтов (прокрутка в правой панели):
#   game/mod_assets/mas_os/browser/<id>.png
# id совпадает с SITES[].id: youtube.png, wikipedia.png, twitter.png, ...
# Ширина 790 px, высота любая (лучше 1600–2400), PNG, без прозрачности.
# Если файла нет — показывается текстовая заглушка. Как сделать свои:
# см. game/mod_assets/mas_os/browser/КАК_ВСТАВИТЬ_СКРИНЫ.txt

init -5 python in mas_os:
    import random
    import store

    toast_title = "Моника"
    toast_body = ""
    current_site = None

    BROWSER_SHOT = "mod_assets/mas_os/browser/{0}.png"

    LOREM = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod "
        "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, "
        "quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.\n\n"
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu "
        "fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum.\n\n"
        "Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac "
        "turpis egestas. Vestibulum tortor quam, feugiat vitae, ultricies eget, tempor sit "
        "amet, ante. Donec eu libero sit amet quam egestas semper.\n\n"
        "Aenean ultricies mi vitae est. Mauris placerat eleifend leo. Quisque sit amet est "
        "et sapien ullamcorper pharetra. Vestibulum erat wisi, condimentum sed, commodo "
        "vitae, ornare sit amet, wisi.\n\n"
        "Aenean fermentum, elit eget tincidunt condimentum, eros ipsum rutrum orci, "
        "sagittis tempus lacus enim ac dui. Donec non enim in turpis pulvinar facilisis. "
        "Ut felis. Praesent dapibus, neque id cursus faucibus, tortor neque egestas augue.\n\n"
        "Etiam ultricies nisi vel augue. Curabitur ullamcorper ultricies nisi. Nam eget dui. "
        "Etiam rhoncus. Maecenas tempus, tellus eget condimentum rhoncus, sem quam semper "
        "libero, sit amet adipiscing sem neque sed ipsum.\n\n"
        "Nam quam nunc, blandit vel, luctus pulvinar, hendrerit id, lorem. Maecenas nec "
        "odio et ante tincidunt tempus. Donec vitae sapien ut libero venenatis faucibus. "
        "Nullam quis ante. Etiam sit amet orci eget eros faucibus tincidunt.\n\n"
        "Duis leo. Sed fringilla mauris sit amet nibh. Donec sodales sagittis magna. Sed "
        "consequat, leo eget bibendum sodales, augue velit cursus nunc, quis gravida magna "
        "mi a libero. Fusce vulputate eleifend sapien.\n\n"
        "Vestibulum purus quam, scelerisque ut, mollis sed, nonummy id, metus. Nullam "
        "accumsan lorem in dui. Cras ultricies mi eu turpis hendrerit fringilla. Vestibulum "
        "ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae.\n\n"
        "In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum "
        "felis eu pede mollis pretium. Integer tincidunt. Cras dapibus. Vivamus elementum "
        "semper nisi. Aenean vulputate eleifend tellus."
    )

    # Quips copied from script-windowreacts.rpy (mas_wrs_*).
    SITES = [
        {
            "id": "pinterest",
            "name": "Pinterest",
            "url": "https://www.pinterest.com/",
            "quips": [
                "Что-то новенькое сегодня, [player]?",
                "Нашёл что-нибудь интересное, [player]?",
                "Увидел что-нибудь, что тебе нравится?",
            ],
        },
        {
            "id": "duolingo",
            "name": "Duolingo",
            "url": "https://www.duolingo.com/",
            "quips": [
                "Учишь новые способы сказать «я люблю тебя», [player]?",
                "Учишь новый язык, [player]?",
                "Какой язык учишь, [player]?",
            ],
        },
        {
            "id": "wikipedia",
            "name": "Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Doki_Doki_Literature_Club",
            "heading": "Doki Doki Literature Club - Wikipedia",
            "quips": [
                "Узнаёшь что-то новое, [player]?",
                "Решил немного покопаться, [player]?",
                "«Doki Doki Literature Club»...\nЗвучит интересно, [player].",
            ],
        },
        {
            "id": "virtualpiano",
            "name": "Virtual Piano",
            "url": "https://www.virtualpiano.net/",
            "quips": [
                "Ой, ты собираешься сыграть для меня?\nКакой ты милый~",
                "Сыграй что-нибудь для меня, [player]!",
            ],
        },
        {
            "id": "youtube",
            "name": "YouTube",
            "url": "https://www.youtube.com/",
            "quips": [
                "Что смотришь, [mas_get_player_nickname()]?",
                "Смотришь что-нибудь интересное, [mas_get_player_nickname()]?",
            ],
        },
        {
            "id": "r34m",
            "name": "Rule34 · Monika",
            "url": "https://rule34.xxx/index.php?page=post&s=list&tags=monika",
            "quips": [
                "Эй, [player]... на что это ты смотришь?",
            ],
        },
        {
            "id": "monikamoddev",
            "name": "GitHub · MonikaModDev",
            "url": "https://github.com/Monika-After-Story/MonikaModDev",
            "quips": [
                "Ой, ты делаешь что-то для меня?\nКакой ты милый~",
                "Собираешься помочь мне стать ближе к твоей реальности?\nКакой ты милый, [player]~",
            ],
        },
        {
            "id": "twitter",
            "name": "Twitter",
            "url": "https://twitter.com/",
            "quips": [
                "Увидел что-нибудь, чем хочешь поделиться со мной, [player]?",
                "Есть что-нибудь интересное рассказать, [player]?",
            ],
        },
        {
            "id": "4chan",
            "name": "4chan",
            "url": "https://boards.4chan.org/",
            "quips": [
                "Так вот где всё началось, да?\nЭто... действительно нечто.",
                "Надеюсь, ты не проведёшь весь день в спорах с другими анонами, [player].",
                "Слышала, тут есть треды про Литературный клуб.\nПередай им от меня привет~",
                "Буду поглядывать, какие доски ты открываешь, вдруг появятся идеи, ахаха!",
            ],
        },
        {
            "id": "pixiv",
            "name": "pixiv",
            "url": "https://www.pixiv.net/",
            "quips": [
                "Интересно, рисовали ли меня...\nНе поищешь?\nТолько давай без пошлостей, хорошо?~",
                "Довольно интересное место... столько умелых людей выкладывают свои работы.",
            ],
        },
        {
            "id": "reddit",
            "name": "Reddit",
            "url": "https://www.reddit.com/",
            "quips": [
                "Нашёл хорошие посты, [player]?",
                "Сидишь на Reddit? Только не проведи весь день за мемами, хорошо?",
                "Интересно, есть ли сабреддиты обо мне...\nАхаха, шучу, [player].",
            ],
        },
        {
            "id": "mal",
            "name": "MyAnimeList",
            "url": "https://myanimelist.net/",
            "quips": [
                "Может, когда-нибудь посмотрим аниме вместе, [player]~",
            ],
        },
        {
            "id": "deviantart",
            "name": "DeviantArt",
            "url": "https://www.deviantart.com/",
            "quips": [
                "Здесь столько таланта!",
                "Когда-нибудь хотела бы научиться рисовать...",
            ],
        },
        {
            "id": "netflix",
            "name": "Netflix",
            "url": "https://www.netflix.com/",
            "quips": [
                "С удовольствием посмотрела бы с тобой романтику, [player]!",
                "Что смотрим сегодня, [player]?",
                "Что собираешься смотреть, [player]?",
            ],
        },
        {
            "id": "twitch",
            "name": "Twitch",
            "url": "https://www.twitch.tv/",
            "quips": [
                "Смотришь стрим, [player]?",
                "Не против, если я посмотрю с тобой?",
                "Что смотрим сегодня, [player]?",
            ],
        },
        {
            "id": "docs",
            "name": "Google Docs",
            "url": "https://docs.google.com/",
            "quips": [
                "Пишешь историю?",
                "Конспектируешь, [player]?",
                "Пишешь стихотворение?",
                "Пишешь любовное письмо?~",
            ],
        },
        {
            "id": "crunchyroll",
            "name": "Crunchyroll",
            "url": "https://www.crunchyroll.com/",
            "quips": [
                "Какое аниме смотрим сегодня, [player]?",
                "Смотришь аниме, [player]?",
                "Не могу дождаться, когда посмотрим аниме вместе!~",
            ],
        },
    ]

    def site_by_id(site_id):
        for site in SITES:
            if site["id"] == site_id:
                return site
        return None

    def current_site_data():
        return site_by_id(current_site)

    def site_shot(site_id):
        path = BROWSER_SHOT.format(site_id)
        if store.renpy.loadable(path):
            return path
        return None

    def _moni_name():
        return store.m_name or getattr(store.persistent, "_mas_monika_nickname", None) or "Моника"

    def _extra_quips(site):
        extras = []
        sid = site["id"]
        if sid == "virtualpiano":
            try:
                if store.mas_isGameUnlocked("piano"):
                    extras.append("Похоже, тебе нужно пианино побольше?\nАхаха~")
            except Exception:
                pass
        elif sid == "twitter":
            try:
                line = store.renpy.substitute(
                    "Я люблю тебя, [mas_get_player_nickname(exclude_names=['love', 'my love'])]."
                )
                extras.append(
                    "280 символов? Мне хватит {0}...\n{1}".format(len(line), line)
                )
            except Exception:
                extras.append("280 символов? Мне хватит нескольких...\nЯ люблю тебя.")
        elif sid == "pixiv":
            drawn = getattr(store.persistent, "_mas_pm_drawn_art", None)
            if drawn is None or drawn:
                extras.append(
                    "Довольно интересное место... столько умелых людей выкладывают свои работы.\nТы среди них, [player]?"
                )
            if drawn:
                extras.extend([
                    "Пришёл выложить свой рисунок меня, [player]?",
                    "Выкладываешь то, что нарисовал меня?",
                ])
        elif sid == "mal":
            if getattr(store.persistent, "_mas_pm_watch_mangime", None) is None:
                extras.append("Значит, тебе нравятся аниме и манга, [player]?")
        elif sid == "crunchyroll":
            if getattr(store.persistent, "_mas_pm_watch_mangime", None) is False:
                return [
                    "О! Значит, тебе нравится аниме, [player]?",
                    "Приятно видеть, что ты расширяешь кругозор.",
                    "Хм, интересно, что тебя зацепило?",
                ]
        return extras

    def quips_for(site):
        extras = _extra_quips(site)
        if site["id"] == "crunchyroll" and extras:
            return extras
        return list(site["quips"]) + extras

    def show_toast(title, body):
        global toast_title, toast_body
        toast_title = title
        toast_body = body
        # Тост на экране и запись в центр уведомлений рабочего стола.
        try:
            notify_add(title, body, source="browser")
        except Exception:
            pass
        if store.renpy.get_screen("mas_os_toast"):
            store.renpy.hide_screen("mas_os_toast")
        store.renpy.show_screen("mas_os_toast")
        if getattr(store.persistent, "_mas_notification_sounds", True):
            try:
                store.renpy.play("mod_assets/sounds/effects/notif.wav", channel="sound")
            except Exception:
                pass

    def visit_site(site_id):
        global current_site
        site = site_by_id(site_id)
        if site is None:
            return
        current_site = site_id
        quips = quips_for(site)
        try:
            body = store.renpy.substitute(random.choice(quips))
        except Exception:
            body = random.choice(quips)
        show_toast(_moni_name(), body)


label mas_os_browser:
    $ store.mas_os.current_site = None
    call screen mas_os_browser with mas_os_trans
    $ store.renpy.hide_screen("mas_os_toast")
    jump mas_os_home


transform mas_os_toast_slide:
    xoffset 420
    alpha 0.0
    easein 0.38 xoffset 0 alpha 1.0
    pause 4.0
    easeout 0.32 xoffset 420 alpha 0.0


screen mas_os_toast():
    zorder 400

    timer 5.0 action Hide("mas_os_toast")

    frame:
        style "mas_os_toast_frame"
        at mas_os_toast_slide
        xalign 1.0
        yalign 1.0
        xoffset -24
        yoffset -56
        xsize 380
        padding (0, 0)

        hbox:
            add Solid("#FF5BA2") xsize 6 ysize 118
            vbox:
                xsize 368
                spacing 4
                xoffset 14
                yoffset 12

                text store.mas_os.toast_title:
                    style "mas_os_toast_title"

                text store.mas_os.toast_body:
                    style "mas_os_toast_body"


screen mas_os_browser():
    if not store.mas_os.wm_embedded():
        modal True
        zorder 200

    $ site = store.mas_os.current_site_data()
    $ shot = store.mas_os.site_shot(site["id"]) if site else None
    $ heading = (site.get("heading") or site["name"]) if site else _("Браузер")
    $ page_body = (site.get("intro") or store.mas_os.LOREM) if site else ""
    $ embedded = store.mas_os.wm_embedded()
    $ page_top = 70
    $ page_h = 628 if embedded else 558

    use mas_os_bg

    text _("Браузер") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    viewport:
        xpos 48
        ypos page_top
        xysize (340, page_h)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 6

            for item in store.mas_os.SITES:
                button:
                    style "mas_os_side_btn"
                    ysize 74
                    selected (store.mas_os.current_site == item["id"])
                    action Function(store.mas_os.visit_site, item["id"])
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    vbox:
                        spacing 2
                        yalign 0.5
                        xoffset 14
                        xsize 280

                        text item["name"]:
                            style "mas_os_side_btn_text"
                            size 16
                            substitute False

                        text item["url"]:
                            style "mas_os_hint"
                            size 12
                            xsize 280
                            substitute False

    frame:
        style "mas_os_panel"
        xpos 410
        ypos page_top
        xysize (822, page_h)
        padding (0, 0)

        viewport:
            xysize (822, page_h)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 12
                xsize 790
                null height 8

                if site is None:
                    text _("Выбери сайт слева.\n\nМоника пришлёт уведомление справа снизу, как в Windows 10. Это замена реакций на активное окно — на Android система не видит другие приложения."):
                        style "mas_os_body"
                        xsize 760
                        xpos 16
                else:
                    if shot:
                        add store.mas_os.fit_image(shot, 790) xpos 16
                    else:
                        text heading:
                            style "mas_os_subtitle"
                            xpos 16

                        text page_body:
                            style "mas_os_body"
                            size 16
                            xsize 760
                            xpos 16

                null height 24

    if not store.mas_os.wm_embedded():
        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            xpos 48
            ypos 640
            action Return("back")

        key "K_ESCAPE" action Return("back")
        key "K_AC_BACK" action Return("back")


style mas_os_toast_frame is default:
    background Solid("#1B1B1B")

style mas_os_toast_title is default:
    font gui.default_font
    size 16
    color "#FFFFFF"
    outlines []

style mas_os_toast_body is default:
    font gui.default_font
    size 15
    color "#DDDDDD"
    outlines []
    layout "subtitle"
