# MAS OS fake browser — emulates desktop window reactions on Android.

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
                "Anything new today, [player]?",
                "Anything interesting, [player]?",
                "See anything you like?",
            ],
        },
        {
            "id": "duolingo",
            "name": "Duolingo",
            "url": "https://www.duolingo.com/",
            "quips": [
                "Learning new ways to say 'I love you,' [player]?",
                "Learning a new language, [player]?",
                "What language are you learning, [player]?",
            ],
        },
        {
            "id": "wikipedia",
            "name": "Wikipedia",
            "url": "https://en.wikipedia.org/wiki/Doki_Doki_Literature_Club",
            "heading": "Doki Doki Literature Club - Wikipedia",
            "quips": [
                "Learning something new, [player]?",
                "Doing a bit of research, [player]?",
                "'Doki Doki Literature Club'...\nSeems interesting, [player].",
            ],
        },
        {
            "id": "virtualpiano",
            "name": "Virtual Piano",
            "url": "https://www.virtualpiano.net/",
            "quips": [
                "Awww, are you going to play for me?\nYou're so sweet~",
                "Play something for me, [player]!",
            ],
        },
        {
            "id": "youtube",
            "name": "YouTube",
            "url": "https://www.youtube.com/",
            "quips": [
                "What are you watching, [mas_get_player_nickname()]?",
                "Watching anything interesting, [mas_get_player_nickname()]?",
            ],
        },
        {
            "id": "r34m",
            "name": "Rule34 · Monika",
            "url": "https://rule34.xxx/index.php?page=post&s=list&tags=monika",
            "quips": [
                "Hey, [player]...what are you looking at?",
            ],
        },
        {
            "id": "monikamoddev",
            "name": "GitHub · MonikaModDev",
            "url": "https://github.com/Monika-After-Story/MonikaModDev",
            "quips": [
                "Awww, are you doing something for me?\nYou're so sweet~",
                "Are you going to help me come closer to your reality?\nYou're so sweet, [player]~",
            ],
        },
        {
            "id": "twitter",
            "name": "Twitter",
            "url": "https://twitter.com/",
            "quips": [
                "See anything you want to share with me, [player]?",
                "Anything interesting to share, [player]?",
            ],
        },
        {
            "id": "4chan",
            "name": "4chan",
            "url": "https://boards.4chan.org/",
            "quips": [
                "So this is the place where it all started, huh?\nIt's...really quite something.",
                "I hope you don't end up arguing with other Anons all day long, [player].",
                "I heard there's threads discussing the Literature Club in here.\nTell them I said hi~",
                "I'll be watching the boards you're browsing in case you get any ideas, ahaha!",
            ],
        },
        {
            "id": "pixiv",
            "name": "pixiv",
            "url": "https://www.pixiv.net/",
            "quips": [
                "I wonder if people have drawn art of me...\nMind looking for some?\nBe sure to keep it wholesome though~",
                "This is a pretty interesting place...so many skilled people posting their work.",
            ],
        },
        {
            "id": "reddit",
            "name": "Reddit",
            "url": "https://www.reddit.com/",
            "quips": [
                "Have you found any good posts, [player]?",
                "Browsing Reddit? Just make sure you don't spend all day looking at memes, okay?",
                "Wonder if there are any subreddits dedicated towards me...\nAhaha, just kidding, [player].",
            ],
        },
        {
            "id": "mal",
            "name": "MyAnimeList",
            "url": "https://myanimelist.net/",
            "quips": [
                "Maybe we could watch anime together someday, [player]~",
            ],
        },
        {
            "id": "deviantart",
            "name": "DeviantArt",
            "url": "https://www.deviantart.com/",
            "quips": [
                "There's so much talent here!",
                "I'd love to learn how to draw someday...",
            ],
        },
        {
            "id": "netflix",
            "name": "Netflix",
            "url": "https://www.netflix.com/",
            "quips": [
                "I'd love to watch a romance movie with you [player]!",
                "What are we watching today, [player]?",
                "What are you going to watch [player]?",
            ],
        },
        {
            "id": "twitch",
            "name": "Twitch",
            "url": "https://www.twitch.tv/",
            "quips": [
                "Watching a stream, [player]?",
                "Do you mind if I watch with you?",
                "What are we watching today, [player]?",
            ],
        },
        {
            "id": "docs",
            "name": "Google Docs",
            "url": "https://docs.google.com/",
            "quips": [
                "Writing a story?",
                "Taking notes, [player]?",
                "Writing a poem?",
                "Writing a love letter?~",
            ],
        },
        {
            "id": "crunchyroll",
            "name": "Crunchyroll",
            "url": "https://www.crunchyroll.com/",
            "quips": [
                "What anime are we watching today, [player]?",
                "Watching some anime, [player]?",
                "I can't wait to watch anime with you!~",
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
                    extras.append("I guess you need a bigger piano?\nAhaha~")
            except Exception:
                pass
        elif sid == "twitter":
            try:
                line = store.renpy.substitute(
                    "I love you, [mas_get_player_nickname(exclude_names=['love', 'my love'])]."
                )
                extras.append(
                    "280 characters? I only need {0}...\n{1}".format(len(line), line)
                )
            except Exception:
                extras.append("280 characters? I only need a few...\nI love you.")
        elif sid == "pixiv":
            drawn = getattr(store.persistent, "_mas_pm_drawn_art", None)
            if drawn is None or drawn:
                extras.append(
                    "This is a pretty interesting place...so many skilled people posting their work.\nAre you one of them, [player]?"
                )
            if drawn:
                extras.extend([
                    "Here to post your art of me, [player]?",
                    "Posting something you drew of me?",
                ])
        elif sid == "mal":
            if getattr(store.persistent, "_mas_pm_watch_mangime", None) is None:
                extras.append("So you like anime and manga, [player]?")
        elif sid == "crunchyroll":
            if getattr(store.persistent, "_mas_pm_watch_mangime", None) is False:
                return [
                    "Oh! So you like anime, [player]?",
                    "It's good to see you broadening your horizons.",
                    "Hmm, I wonder what caught your eye?",
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
    call screen mas_os_browser
    $ store.renpy.hide_screen("mas_os_toast")
    jump mas_os_home


transform mas_os_toast_slide:
    xoffset 420
    easein 0.35 xoffset 0
    pause 4.0
    easeout 0.35 xoffset 420


screen mas_os_toast():
    zorder 400

    timer 5.0 action Hide("mas_os_toast")

    frame:
        style "mas_os_toast_frame"
        at mas_os_toast_slide
        xalign 1.0
        yalign 1.0
        xoffset -24
        yoffset -28
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
    modal True
    zorder 200

    $ site = store.mas_os.current_site_data()
    $ shot = store.mas_os.site_shot(site["id"]) if site else None
    $ heading = (site.get("heading") or site["name"]) if site else _("Браузер")
    $ url = site["url"] if site else "mas-os://home"
    $ page_body = (site.get("intro") or store.mas_os.LOREM) if site else ""

    add Solid("#14070d")

    text _("Браузер"):
        style "mas_os_title"
        xpos 48
        ypos 22

    text _("Эмуляция реакций на окна. Скриншоты можно положить в mod_assets/mas_os/browser/."):
        style "mas_os_hint"
        xpos 48
        ypos 66

    viewport:
        xpos 48
        ypos 100
        xysize (340, 510)
        draggable True
        mousewheel True
        scrollbars "vertical"

        vbox:
            spacing 6

            for item in store.mas_os.SITES:
                textbutton item["name"]:
                    style "mas_os_side_btn"
                    text_style "mas_os_side_btn_text"
                    selected (store.mas_os.current_site == item["id"])
                    action Function(store.mas_os.visit_site, item["id"])

    frame:
        style "mas_os_panel"
        xpos 410
        ypos 100
        xysize (822, 510)
        padding (0, 0)

        vbox:
            spacing 0
            xfill True

            frame:
                background Solid("#2A121C")
                xfill True
                padding (14, 8)

                vbox:
                    spacing 4

                    text heading:
                        style "mas_os_subtitle"
                        size 16

                    text url:
                        style "mas_os_hint"
                        size 14

            viewport:
                xysize (822, 454)
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

                        text heading:
                            style "mas_os_subtitle"
                            xpos 16

                        text page_body:
                            style "mas_os_body"
                            size 16
                            xsize 760
                            xpos 16

                    null height 24

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
