# -*- coding: utf-8 -*-
# Replay of the original DDLC credits (names, pictures, Your Reality).
# Does not set autoload and does not quit the game. «Назад» returns to MAS OS.

init python:
    class MASOSCredits(Action):
        def __call__(self):
            store.renpy.jump("mas_os_orig_credits")

    def credit_img(n):
        kind = "_locked"
        flags = getattr(store.persistent, "clear", None)
        try:
            if flags and (n - 1) < len(flags) and flags[n - 1]:
                kind = ""
        except Exception:
            kind = "_locked"
        if getattr(store.persistent, "clearall", None):
            kind = "_clearall"
        return "mas_os_ccg{0}{1}".format(n, kind)


image mas_os_credits_logo:
    "gui/logo.png"
    truecenter
    zoom 0.6 alpha 0 subpixel True
    linear 2.0 alpha 1
    4.5
    linear 2.0 alpha 0

image mas_os_credits_ts:
    "images/bg/splash-white.png"
    xalign 0.5 yalign 0.6
    zoom 0.65 alpha 0 subpixel True
    linear 2.0 alpha 1
    4.5
    linear 2.0 alpha 0

style mas_os_credits_header:
    font "gui/font/RifficFree-Bold.ttf"
    color "#ffaae6"
    size 36
    text_align 0.5
    outlines []

style mas_os_credits_text:
    font "gui/font/Halogen.ttf"
    color "#fff"
    size 36
    text_align 0.5
    outlines []

image mas_os_credits_header = ParameterizedText(style="mas_os_credits_header", ypos=-40)
image mas_os_credits_text = ParameterizedText(style="mas_os_credits_text", ypos=40)

transform mas_os_cr_scroll:
    subpixel True
    yoffset 740
    linear 15 yoffset -380

transform mas_os_cr_text:
    anchor (0.5, 0.5) subpixel True
    yoffset 920
    linear 15 yoffset -200

transform mas_os_cr_right:
    xalign 0.9
    mas_os_cr_scroll

transform mas_os_cr_left:
    xalign 0.1
    mas_os_cr_scroll

transform mas_os_cr_text_right:
    xpos 960
    mas_os_cr_text

transform mas_os_cr_text_left:
    xpos 320
    mas_os_cr_text

init python:
    def _ccg(n, kind):
        return "images/cg/credits/{0}{1}.png".format(n, "b" if kind == "b" else "")

init:
    python:
        for _n in range(1, 11):
            renpy.image(
                "mas_os_ccg{0}".format(_n),
                im.Scale("images/cg/credits/{0}.png".format(_n), 640, 360),
            )
            renpy.image(
                "mas_os_ccg{0}_locked".format(_n),
                im.Scale("images/cg/credits/{0}b.png".format(_n), 640, 360),
            )
            renpy.image(
                "mas_os_ccg{0}_clearall".format(_n),
                im.Scale("images/cg/credits/{0}.png".format(_n), 640, 360),
            )


screen mas_os_credits_back():
    zorder 300

    textbutton _("Назад"):
        style "mas_os_nav_btn"
        text_style "mas_os_nav_btn_text"
        xpos 48
        ypos 640
        action Jump("mas_os_credits_done")

    key "K_ESCAPE" action Jump("mas_os_credits_done")
    key "K_AC_BACK" action Jump("mas_os_credits_done")


label mas_os_orig_credits:
    window hide
    $ quick_menu = False
    scene black
    show screen mas_os_credits_back
    play music "<from 50.0>bgm/credits.ogg" noloop

    show mas_os_credits_logo
    $ renpy.pause(8.0, hard=True)
    hide mas_os_credits_logo

    show expression credit_img(1) at mas_os_cr_right as credits_image_1
    show mas_os_credits_header "Concept & Game Design" at mas_os_cr_text_left as credits_header_1
    show mas_os_credits_text "Dan Salvato" at mas_os_cr_text_left as credits_text_1
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(2) at mas_os_cr_left as credits_image_2
    show mas_os_credits_header "Character Art" at mas_os_cr_text_right as credits_header_2
    show mas_os_credits_text "Satchely" at mas_os_cr_text_right as credits_text_2
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(3) at mas_os_cr_right as credits_image_1
    show mas_os_credits_header "Background Art" at mas_os_cr_text_left as credits_header_1
    show mas_os_credits_text "Velinquent" at mas_os_cr_text_left as credits_text_1
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(4) at mas_os_cr_left as credits_image_2
    show mas_os_credits_header "Writing" at mas_os_cr_text_right as credits_header_2
    show mas_os_credits_text "Dan Salvato" at mas_os_cr_text_right as credits_text_2
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(5) at mas_os_cr_right as credits_image_1
    show mas_os_credits_header "Music" at mas_os_cr_text_left as credits_header_1
    show mas_os_credits_text "Dan Salvato" at mas_os_cr_text_left as credits_text_1
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(6) at mas_os_cr_left as credits_image_2
    show mas_os_credits_header "Vocals" at mas_os_cr_text_right as credits_header_2
    show mas_os_credits_text "Jillian Ashcraft" at mas_os_cr_text_right as credits_text_2
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(7) at mas_os_cr_right as credits_image_1
    show mas_os_credits_header "Special Thanks" at mas_os_cr_text_left as credits_header_1
    show mas_os_credits_text "Masha Gutin\nKagefumi" at mas_os_cr_text_left as credits_text_1
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(8) at mas_os_cr_left as credits_image_2
    show mas_os_credits_header "Special Thanks" at mas_os_cr_text_right as credits_header_2
    show mas_os_credits_text "David Evelyn\nCorey Shin" at mas_os_cr_text_right as credits_text_2
    $ renpy.pause(9.0, hard=True)

    show expression credit_img(9) at mas_os_cr_right as credits_image_1
    show mas_os_credits_header "Special Thanks" at mas_os_cr_text_left as credits_header_1
    show mas_os_credits_text "Alecia Bardachino\nMatt Naples" at mas_os_cr_text_left as credits_text_1
    $ renpy.pause(8.0, hard=True)

    show expression credit_img(10) at mas_os_cr_left as credits_image_2
    show mas_os_credits_header "Special Thanks" at mas_os_cr_text_right as credits_header_2
    show mas_os_credits_text "Monika\n[player]" at mas_os_cr_text_right as credits_text_2
    $ renpy.pause(9.0, hard=True)

    scene black
    show mas_os_credits_ts
    show mas_os_credits_text "made with love by":
        zoom 0.75 xalign 0.5 yalign 0.25 alpha 0 subpixel True
        linear 2.0 alpha 1
        4.5
        linear 2.0 alpha 0
    $ renpy.pause(9.0, hard=True)

    jump mas_os_credits_done


label mas_os_credits_done:
    stop music fadeout 0.8
    scene black
    hide screen mas_os_credits_back
    $ quick_menu = False
    if store.mas_os.layout_desktop():
        jump mas_os_home
    jump mas_os_about
