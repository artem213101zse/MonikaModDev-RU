## This splash screen is the first thing that Renpy will show the player
##
## Before load, check to be sure that the archive files were found.
## If not, display an error message and quit.

# Проверка наличия архивов игры. Но на андроид архивы не работают, так что отключаем эту проверку
# init -100 python:
#     #Check for each archive needed
#     for archive in ['audio','images','scripts','fonts']:
#         if not archive in config.archives:
#             #If one is missing, throw an error and chlose
#             renpy.error("Архивы игры DDLC не найдены в папке /game. Проверьте установку и попробуйте снова.")



## First, a disclaimer declaring this is a mod is shown, then there is a
## check for the original DDLC assets in the install folder. If those are
## not found, the player is directed to the developer's site to download.
##
init python:
    menu_trans_time = 1
    #The default splash message, originally shown in Act 1 and Act 4
    splash_message_default = _("Эта игра является неофициальной фанатской работой, не связанной с Team Salvato.")
    splash_messages = [
    _("Пожалуйста, поддержите Doki Doki Literature Club & Team Salvato."),
    _("Ты мой солнечный свет,\nМой единственный свет"),
    _("Я скучала по тебе."),
    _("Поиграй со мной"),
    _("Это всего лишь игра... по большей части."),
    _("Эта игра не предназначена для детей\nи лиц с неустойчивой психикой?"),
    _("sdfasdklfgsdfgsgoinrfoenlvbd"),
    _("null"),
    _("Я отправила крошек в ад."),
    _("За это умер Проект М."),
    _("Это была лишь от части твоя вина."),
    _("Эта игра не предназначена для детей\nи для неуравновешенных психов.")
#    "Не забудьте сделать копию файла персонажа Моники."
    ]

image splash_warning = ParameterizedText(style="splash_text", xalign=0.5, yalign=0.5)

##Here's where you can change the logo file to whatever you want
image menu_logo:
    "mod_assets/menu_new.png"
    subpixel True
    xcenter 240
    ycenter 120
    zoom 0.60
    menu_logo_move

#Removed rendering below of other char imgs in main menu

image menu_bg:
    topleft
    "gui/menu_bg.png"
    menu_bg_move

image game_menu_bg:
    topleft
    "gui/menu_bg.png"
    menu_bg_loop

image menu_fade:
    "white"
    menu_fadeout

image menu_art_m:
    subpixel True
    "gui/menu_art_m.png"
    xcenter 1000
    ycenter 640
    zoom 1.00
    menu_art_move(1.00, 1000, 1.00)

image menu_art_m_ghost:
    subpixel True
    "gui/menu_art_m_ghost.png"
    xcenter 1000
    ycenter 640
    zoom 1.00
    menu_art_move(1.00, 1000, 1.00)

image menu_nav:
    "gui/overlay/main_menu.png"
    menu_nav_move

image menu_particles:
    2.481
    xpos 224
    ypos 104
    ParticleBurst("gui/menu_particle.png", explodeTime=0, numParticles=20, particleTime=2.0, particleXSpeed=6, particleYSpeed=4).sm
    particle_fadeout

transform particle_fadeout:
    easeout 1.5 alpha 0

transform menu_bg_move:
    subpixel True
    topleft
    parallel:
        xoffset 0 yoffset 0
        linear 3.0 xoffset -100 yoffset -100
        repeat
    parallel:
        ypos 0
        time 0.65
        ease_cubic 2.5 ypos -500

transform menu_bg_loop:
    subpixel True
    topleft
    parallel:
        xoffset 0 yoffset 0
        linear 3.0 xoffset -100 yoffset -100
        repeat

transform menu_logo_move:
    subpixel True
    yoffset -300
    time 1.925
    easein_bounce 1.5 yoffset 0

transform menu_nav_move:
    subpixel True
    xoffset -500
    time 1.5
    easein_quint 1 xoffset 0

transform menu_fadeout:
    easeout 0.75 alpha 0
    time 2.481
    alpha 0.4
    linear 0.5 alpha 0

transform menu_art_move(z, x, z2):
    subpixel True
    yoffset 0 + (1200 * z)
    xoffset (740 - x) * z * 0.5
    zoom z2 * 0.75
    time 1.0
    parallel:
        ease 1.75 yoffset 0
    parallel:
        pause 0.75
        ease 1.5 zoom z2 xoffset 0

image intro:
    truecenter
    "white"
    0.5
    "bg/splash.png" with Dissolve(0.5, alpha=True)
    2.5
    "white" with Dissolve(0.5, alpha=True)
    0.5

image warning:
    truecenter
    "white"
    "splash_warning" with Dissolve(0.5, alpha=True)
    2.5
    "white" with Dissolve(0.5, alpha=True)
    0.5

image tos = "bg/warning.png"
image tos2 = "bg/warning2.png"


init python:
    class MASOSTOSMark(Action):
        def __init__(self, which):
            self.which = which

        def __call__(self):
            store.mas_os.tos_mark(self.which)
            store.renpy.restart_interaction()
            return None

    class MASOSTOSDone(Action):
        def __call__(self):
            if store.mas_os.tos_test:
                store.mas_os.tos_test = False
                store.renpy.hide_screen("mas_os_tos")
                store.renpy.restart_interaction()
                return None
            return True

    class MASOSTOSRefuse(Action):
        def __call__(self):
            store.mas_os.tos_refuse()
            return None


label mas_os_tos_seq:
    python:
        store.mas_os.tos_begin(False)
        quick_menu = False
        _confirm_quit = False
        config.allow_skipping = False
    scene white
    pause 0.5
    scene tos
    with Dissolve(1.0)
    pause 0.4
    call screen mas_os_tos
    scene white
    with Dissolve(1.0)
    return


screen mas_os_tos_agree_btn(cap, agreed, which):
    button:
        xsize 430
        ysize 56
        padding (10, 6)
        background Solid("#2F9A58" if agreed else "#FFD0E4")
        hover_background Solid("#3DB86A" if agreed else "#FFB7D8")
        action MASOSTOSMark(which)
        hover_sound gui.hover_sound
        activate_sound gui.activate_sound

        hbox:
            spacing 12
            xalign 0.5
            yalign 0.5

            frame:
                xysize (28, 28)
                background Solid("#FFFFFF")
                yalign 0.5

                if agreed:
                    text "OK":
                        size 13
                        color "#1A7A3A"
                        bold True
                        xalign 0.5
                        yalign 0.5
                        outlines []

            text cap:
                size 18
                color ("#FFFFFF" if agreed else "#5A2038")
                yalign 0.5
                outlines []
                substitute False


screen mas_os_tos():
    modal True
    zorder 400

    $ phase = store.mas_os.tos_phase
    $ a_mas = store.mas_os.tos_agree_mas
    $ a_os = store.mas_os.tos_agree_os
    $ gname = config.name

    if phase == 2:
        if renpy.loadable("bg/warning2.png"):
            add "tos2"
        else:
            add Solid("#ffffff")
        timer 1.5 action MASOSTOSDone()
    else:
        if renpy.loadable("bg/warning.png"):
            add "tos"
        else:
            add Solid("#14070d")
        add Solid("#000000B3")

        frame:
            xalign 0.5
            yalign 0.5
            xsize 1000
            padding (32, 24)
            background Solid("#FFF8F2")

            vbox:
                xsize 936
                spacing 12

                text _("Условия использования"):
                    style "splash_text"
                    size 26
                    color "#1A1216"
                    xalign 0.5

                text _("Monika After Story"):
                    style "splash_text"
                    size 20
                    color "#7A2850"
                    xalign 0.5

                text _("[gname] — это фанатский мод для Doki Doki Literature Club, никак не связанный с Team Salvato. Рекомендуется проходить его только после завершения оригинальной игры: здесь очень много спойлеров. Для запуска нужны файлы оригинальной DDLC, их можно бесплатно скачать на http://ddlc.moe"):
                    style "splash_text"
                    size 18
                    color "#24181C"
                    xsize 936
                    xalign 0.5
                    text_align 0.5
                    substitute True

                text _("Запуская [gname], вы подтверждаете, что прошли Doki Doki Literature Club до конца и согласны со всеми спойлерами."):
                    style "splash_text"
                    size 18
                    color "#24181C"
                    xsize 936
                    xalign 0.5
                    text_align 0.5
                    substitute True

                text _("MAS OS"):
                    style "splash_text"
                    size 20
                    color "#7A2850"
                    xalign 0.5

                text _("MAS OS — оболочка этого порта, © Kurokawa GDS (Kurokawa Game Dev Studio). Это не продукт Team Salvato и не официальная часть команды Monika After Story. Оболочку можно использовать только в составе этого порта: нельзя копировать MAS OS в чужой мод или сборку, выдавать её за свою работу, снимать логотип и строку «powered by Kurokawa GDS»."):
                    style "splash_text"
                    size 18
                    color "#24181C"
                    xsize 936
                    xalign 0.5
                    text_align 0.5

                text _("Нужны оба согласия. Если одно не принято — игра закроется."):
                    style "splash_text"
                    size 16
                    color "#7A2850"
                    xalign 0.5

                hbox:
                    xalign 0.5
                    spacing 20

                    use mas_os_tos_agree_btn(_("Согласен: мод"), a_mas, "mas")
                    use mas_os_tos_agree_btn(_("Согласен: MAS OS"), a_os, "os")

        if a_mas and a_os:
            timer 0.45 action Function(store.mas_os.tos_advance)

        key "K_ESCAPE" action If(a_mas and a_os, NullAction(), MASOSTOSRefuse())
        key "K_AC_BACK" action If(a_mas and a_os, NullAction(), MASOSTOSRefuse())


label splashscreen:
    # Init reached splash: crash watchdog can stand down.
    $ store.mas_os.mark_boot_ok()
    # Team Salvato + MAS OS clickwrap before the shell.
    if not persistent._mas_os_tos_agreed:
        call mas_os_tos_seq
    # MAS OS must run BEFORE session/affection startup.
    # Visiting the shell is not a MAS session.
    if store.mas_os.needs_setup():
        call mas_os_setup
    if store.mas_os.android_saves_should_ask():
        call screen mas_os_android_saves
    if store.mas_os.can_show():
        call mas_os_shell

    python:
        _mas_AffStartup()

        persistent.sessions['current_session_start']=datetime.datetime.now()
        persistent.sessions['total_sessions'] = persistent.sessions['total_sessions']+ 1
        store.mas_calendar.loadCalendarDatabase()

        # set zoom
        store.mas_sprites.adjust_zoom()

        # We're about to start, all things should be loaded, we can check event conditionals
        Event.validateConditionals()

    if store.mas_per_check.should_show_chibika_persistent():
        # we have a corrupted per w/ no backups or incompatible per
        call mas_backups_you_have_bad_persistent

    scene white

    if persistent.first_run:
        $ quick_menu = False
        #Optional, load a copy of DDLC save data
        if not persistent._mas_imported_saves:
            call import_ddlc_persistent from _call_import_ddlc_persistent

        $ persistent.first_run = False

#    $ basedir = config.basedir.replace('\\', '/')
#   NOTE: this keeps screwing with my syntax coloring
    python:
        basedir = config.basedir.replace("\\", "/")

        # dump verseion to a firstrun-style file
        with open(basedir + "/game/masrun", "w") as versfile:
            versfile.write(config.name + "|" + config.version + "\n")


    #Check for game updates before loading the game or the splash screen

    #autoload handling
    #Use persistent.autoload if you want to bypass the splashscreen on startup for some reason
    if persistent.autoload and not _restart:
        jump autoload

    $ mas_enable_quit()

    # Start splash logic
    $ config.allow_skipping = False

    # Splash screen
    show white
    $ persistent.ghost_menu = False #Handling for easter egg from DDLC
    $ splash_message = splash_message_default #Default splash message
    $ config.main_menu_music = audio.t1
    $ renpy.music.play(config.main_menu_music)
    show intro with Dissolve(0.5, alpha=True)
    pause 2.5
    hide intro with Dissolve(0.5, alpha=True)
    #You can use random splash messages, as well. By default, they are only shown during certain acts.
    if renpy.random.randint(0, 3) == 0:
        $ splash_message = renpy.random.choice(splash_messages)
    show splash_warning "[splash_message]" with Dissolve(0.5, alpha=True)
    pause 2.0
    hide splash_warning with Dissolve(0.5, alpha=True)
    $ config.allow_skipping = False

    python:
        if persistent._mas_auto_mode_enabled:
            mas_darkMode(mas_current_background.isFltDay())
        else:
            mas_darkMode(not persistent._mas_dark_mode_enabled)
    return

label warningscreen:
    hide intro
    show warning
    pause 3.0

label after_load:
    $ config.allow_skipping = False
    $ _dismiss_pause = config.developer
    $ persistent.ghost_menu = False #Handling for easter egg from DDLC
    $ style.say_dialogue = style.normal
    #Check if the save has been tampered with
    if anticheat != persistent.anticheat:
        stop music
        scene black
        "Не удалось загрузить сохранение."
        "Ты что, пытался жульничать?"
        #Handle however you want, default is to force reset all save data
        $ renpy.utter_restart()
    return


label autoload:
    python:
        # Stuff that's normally done after splash
        if "_old_game_menu_screen" in globals():
            _game_menu_screen = _old_game_menu_screen
            del _old_game_menu_screen
        if "_old_history" in globals():
            _history = _old_history
            del _old_history
        # Open the settings panel in the menu
        _game_menu_screen = "preferences"
        renpy.block_rollback()

        # Fix the game context (normally done when loading save file)
        renpy.context()._menu = False
        renpy.context()._main_menu = False
        main_menu = False
        _in_replay = None

    # explicity remove keymaps we dont want
    $ config.keymap["debug_voicing"] = list()
    $ config.keymap["choose_renderer"] = list()

    # Pop the _splashscreen label which has _confirm_quit as False and other stuff
    $ renpy.pop_call()

    # oh shit we are going to break everything right here
    if persistent._mas_chess_mangle_all:
        jump mas_chess_go_ham_and_delete_everything

    python:
        # okay lets setup monika's clothes
        # monika_chr.change_outfit(
        #     persistent._mas_monika_clothes,
        #     persistent._mas_monika_hair
        # )

        # need to set the monisize correctly
        store.mas_dockstat.setMoniSize(persistent.sessions["total_playtime"])
        # finally lets run actions that needed to be run
        mas_runDelayedActions(MAS_FC_START)
        # Start predict idle sprites
        renpy.start_predict("monika idle")

    #jump expression persistent.autoload
    # NOTE: we should always jump to ch30 instead
    jump ch30_autoload

label before_main_menu:
    $ config.main_menu_music = audio.t1
    return

label quit:
    # Closed MAS OS without launching the game: do not write session,
    # playtime, or affection. Otherwise Monika treats it as a visit.
    if not store.mas_os.game_entered:
        python:
            try:
                store.mas_logging.logging.shutdown()
            except Exception:
                pass
        return

    python:
        store.mas_os.end_game_session()
    return
