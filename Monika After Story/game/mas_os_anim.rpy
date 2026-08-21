# MAS OS motion. Two open styles, picked in Settings:
#   rise — slide up (default)
#   zoom — fade in, grow toward the player, unblur

define mas_os_trans = Dissolve(0.22)
define mas_os_trans_long = Dissolve(0.38)

transform mas_os_page:
    on show:
        alpha 0.0
        yoffset 16
        easein 0.28 alpha 1.0 yoffset 0
    on hide:
        easeout 0.14 alpha 0.0 yoffset 8

transform mas_os_page_zoom:
    transform_anchor True
    on show:
        alpha 0.0
        zoom 0.88
        blur 12
        easein 0.32 alpha 1.0 zoom 1.0 blur 0
    on hide:
        easeout 0.16 alpha 0.0 zoom 0.94 blur 6

transform mas_os_pop(delay=0.0):
    alpha 0.0
    yoffset 14
    pause delay
    easein 0.28 alpha 1.0 yoffset 0

transform mas_os_pop_zoom(delay=0.0):
    transform_anchor True
    subpixel True
    alpha 0.0
    zoom 0.90
    blur 8
    pause delay
    easein 0.30 alpha 1.0 zoom 1.0 blur 0

transform mas_os_btn:
    on idle:
        easein 0.12 yoffset 0
    on hover:
        easein 0.12 yoffset -3
    on selected_idle:
        easein 0.12 yoffset 0
    on selected_hover:
        easein 0.12 yoffset -3

transform mas_os_tile_in(delay=0.0):
    alpha 0.0
    yoffset 18
    pause delay
    easein 0.30 alpha 1.0 yoffset 0
    on idle:
        easein 0.12 yoffset 0
    on hover:
        easein 0.12 yoffset -4
    on selected_idle:
        easein 0.12 yoffset 0
    on selected_hover:
        easein 0.12 yoffset -4

transform mas_os_tile_zoom(delay=0.0):
    transform_anchor True
    subpixel True
    alpha 0.0
    zoom 0.90
    blur 5
    pause delay
    easein 0.30 alpha 1.0 zoom 1.0 blur 0
    on idle:
        easein 0.12 zoom 1.0
    on hover:
        easein 0.12 zoom 1.04
    on selected_idle:
        easein 0.12 zoom 1.0
    on selected_hover:
        easein 0.12 zoom 1.04

transform mas_os_launch_in:
    alpha 0.0
    yoffset 12
    pause 0.05
    easein 0.32 alpha 1.0 yoffset 0
    on idle:
        easein 0.12 yoffset 0
    on hover:
        easein 0.12 yoffset -5

transform mas_os_launch_zoom:
    transform_anchor True
    subpixel True
    alpha 0.0
    zoom 0.88
    blur 10
    pause 0.05
    easein 0.32 alpha 1.0 zoom 1.0 blur 0
    on idle:
        easein 0.12 zoom 1.0
    on hover:
        easein 0.12 zoom 1.04

transform mas_os_dim:
    on show:
        alpha 0.0
        easein 0.18 alpha 1.0
    on hide:
        easeout 0.12 alpha 0.0

transform mas_os_modal:
    on show:
        alpha 0.0
        yoffset 16
        easein 0.22 alpha 1.0 yoffset 0
    on hide:
        easeout 0.14 alpha 0.0 yoffset 10

transform mas_os_modal_zoom:
    transform_anchor True
    subpixel True
    on show:
        alpha 0.0
        zoom 0.84
        blur 16
        easein 0.28 alpha 1.0 zoom 1.0 blur 0
    on hide:
        easeout 0.16 alpha 0.0 zoom 0.90 blur 8


# Launch MAS — button flies in, dim, logo, looping bar.
transform mas_os_launch_dim:
    alpha 0.0
    ease 0.85 alpha 0.88
    ease 0.35 alpha 0.96

transform mas_os_launch_fly:
    subpixel True
    xpos 56
    ypos 150
    zoom 1.0
    alpha 1.0
    easein 0.72 xpos 430 ypos 286 zoom 1.10
    pause 0.12
    easeout 0.28 alpha 0.0 zoom 1.22

transform mas_os_launch_logo_in:
    subpixel True
    alpha 0.0
    zoom 0.84
    yoffset 22
    pause 0.58
    easein 0.42 alpha 1.0 zoom 1.0 yoffset 0
    pause 1.78
    alpha 0.0

transform mas_os_launch_bar_in:
    alpha 0.0
    pause 0.78
    ease 0.28 alpha 1.0
    pause 1.72
    alpha 0.0

transform mas_os_indet_run:
    xoffset -150
    linear 1.15 xoffset 400
    repeat

transform mas_os_indet_run2:
    xoffset -220
    pause 0.38
    linear 1.35 xoffset 400
    repeat

transform mas_os_cut_at(t=2.88):
    alpha 0.0
    pause t
    alpha 1.0

transform mas_os_bloom_wash:
    alpha 0.0
    ease 0.7 alpha 0.92
    ease 0.45 alpha 1.0

transform mas_os_bloom_title:
    subpixel True
    alpha 0.0
    zoom 0.92
    yoffset 10
    pause 0.45
    easein 0.4 alpha 1.0 zoom 1.0 yoffset 0
    pause 1.15
    ease 0.25 alpha 0.0 zoom 1.08

transform mas_os_glitch_shake:
    xoffset 0
    pause 0.07
    xoffset 12
    pause 0.04
    xoffset -9
    pause 0.05
    xoffset 4
    pause 0.03
    xoffset 0
    pause 0.11
    xoffset -14
    pause 0.04
    xoffset 8
    pause 0.03
    xoffset 0
    repeat

transform mas_os_glitch_logo:
    subpixel True
    alpha 0.0
    pause 0.2
    alpha 1.0
    pause 0.06
    alpha 0.0
    pause 0.08
    alpha 1.0
    xoffset 0
    pause 0.12
    xoffset 10
    pause 0.05
    xoffset -16
    alpha 0.7
    pause 0.04
    xoffset 0
    alpha 1.0
    pause 0.55
    alpha 0.0
    pause 0.1
    alpha 1.0
    pause 0.7
    alpha 0.0

transform mas_os_scanline:
    alpha 0.0
    pause 0.15
    alpha 0.35
    pause 0.04
    alpha 0.0
    pause 0.22
    alpha 0.5
    pause 0.03
    alpha 0.0
    pause 0.4
    alpha 0.4
    pause 0.05
    alpha 0.0
    repeat

transform mas_os_iris_zoom:
    subpixel True
    xalign 0.5
    yalign 0.5
    zoom 1.0
    alpha 1.0
    ease 1.15 zoom 2.6 alpha 0.0

transform mas_os_iris_btn:
    subpixel True
    xpos 56
    ypos 150
    zoom 1.0
    alpha 1.0
    ease 1.05 xpos 430 ypos 300 zoom 0.18 alpha 0.0

transform mas_os_iris_vignette:
    alpha 0.0
    ease 0.35 alpha 0.55
    ease 0.8 alpha 1.0

transform mas_os_off_dim:
    alpha 0.0
    ease 0.28 alpha 1.0


screen mas_os_launch_end(hold=3.0):
    default can_skip = False

    timer 0.55 action SetScreenVariable("can_skip", True)
    timer hold action Function(store.mas_os.finish_launch_anim)

    button:
        xpos 0
        ypos 0
        xysize (1280, 720)
        background None
        sensitive can_skip
        action Function(store.mas_os.finish_launch_anim)

    key "dismiss" action If(can_skip, Function(store.mas_os.finish_launch_anim), NullAction())
    key "K_RETURN" action If(can_skip, Function(store.mas_os.finish_launch_anim), NullAction())
    key "K_ESCAPE" action If(can_skip, Function(store.mas_os.finish_launch_anim), NullAction())
    key "K_AC_BACK" action If(can_skip, Function(store.mas_os.finish_launch_anim), NullAction())


screen mas_os_launch_btn_face():
    $ _ic = store.mas_os.icon_path("launch")

    hbox:
        xalign 0.5
        yalign 0.5
        spacing 12

        if _ic:
            add store.mas_os.fit_image(_ic, 40, 40):
                yalign 0.5
        else:
            frame:
                xysize (40, 40)
                background Solid("#FF8AC4")
                yalign 0.5

                text ">":
                    style "mas_os_glyph"
                    size 22
                    xalign 0.5
                    yalign 0.5

        text _("Запустить MAS"):
            style "mas_os_launch_text"
            yalign 0.5


screen mas_os_launch_indet():
    frame:
        xalign 0.5
        ypos 528
        xsize 380
        ysize 12
        background Solid("#2A1018")
        clipping True
        at mas_os_launch_bar_in

        add Solid("#FF5BA2"):
            xysize (128, 12)
            at mas_os_indet_run

        add Solid("#FFD7EC"):
            xysize (56, 12)
            at mas_os_indet_run2


screen mas_os_launch_logo_seq():
    add Solid("#000000") at mas_os_launch_dim

    button:
        style "mas_os_launch"
        at mas_os_launch_fly
        action NullAction()

        use mas_os_launch_btn_face

    $ _logo = store.mas_os.launch_logo_path()
    if _logo:
        add store.mas_os.fit_image(_logo, 560, 240) at mas_os_launch_logo_in:
            xalign 0.5
            yalign 0.42
    else:
        text _("Doki Doki Literature Club"):
            style "mas_os_title"
            xalign 0.5
            yalign 0.42
            text_align 0.5
            at mas_os_launch_logo_in

    use mas_os_launch_indet

    add Solid("#000000") at mas_os_cut_at(2.88)

    use mas_os_launch_end(3.05)


screen mas_os_launch_bloom_seq():
    add Solid("#FFB7D8") at mas_os_bloom_wash

    $ _logo = store.mas_os.launch_logo_path()
    if _logo:
        add store.mas_os.fit_image(_logo, 520, 220) at mas_os_bloom_title:
            xalign 0.5
            yalign 0.40
    else:
        text _("Just Monika"):
            style "mas_os_title"
            size 48
            color "#7A2850"
            xalign 0.5
            yalign 0.42
            at mas_os_bloom_title

    text _("Monika After Story"):
        style "mas_os_subtitle"
        xalign 0.5
        ypos 430
        at mas_os_bloom_title

    add Solid("#FFFFFF") at mas_os_cut_at(2.18)

    use mas_os_launch_end(2.45)


screen mas_os_launch_glitch_seq():
    $ _logo = store.mas_os.launch_logo_path()

    add Solid("#000000C8")

    add Solid("#FF2D7A"):
        xsize 1280
        ysize 18
        ypos 120
        at mas_os_scanline

    add Solid("#3EC7FF"):
        xsize 1280
        ysize 10
        ypos 340
        at mas_os_scanline

    add Solid("#FFFFFF"):
        xsize 1280
        ysize 6
        ypos 510
        at mas_os_scanline

    if _logo:
        add store.mas_os.fit_image(_logo, 540, 230) at mas_os_glitch_logo:
            xalign 0.5
            yalign 0.42
            xoffset 0
    else:
        text _("Just Monika"):
            style "mas_os_title"
            xalign 0.5
            yalign 0.45
            at mas_os_glitch_logo

    add Solid("#000000") at mas_os_cut_at(1.82)

    use mas_os_launch_end(2.05)


screen mas_os_launch_iris_seq():
    add store.mas_os.wallpaper_disp() at mas_os_iris_zoom

    add Solid("#000000") at mas_os_iris_vignette

    button:
        style "mas_os_launch"
        at mas_os_iris_btn
        action NullAction()

        use mas_os_launch_btn_face

    add Solid("#000000") at mas_os_cut_at(1.52)

    use mas_os_launch_end(1.85)


screen mas_os_launch_off_seq():
    add Solid("#000000") at mas_os_off_dim

    use mas_os_launch_end(0.55)


screen mas_os_launch_anim():
    modal True
    zorder 500

    $ mode = store.mas_os.launch_anim_id()

    if mode == "bloom":
        use mas_os_launch_bloom_seq
    elif mode == "glitch":
        use mas_os_launch_glitch_seq
    elif mode == "iris":
        use mas_os_launch_iris_seq
    elif mode == "off":
        use mas_os_launch_off_seq
    else:
        use mas_os_launch_logo_seq
