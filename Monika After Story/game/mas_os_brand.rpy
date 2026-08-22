# Kurokawa GDS branding: logo slots, powered-by, rainbow OS button frame.
# Drop final PNGs into game/mod_assets/mas_os/brand/ (see PROMPTS.txt).
# Current PNGs are geometric stubs — overwrite in place, names stay the same.

default persistent._mas_os_boot_splash = "logo"

init -5 python in mas_os:
    import store

    BRAND_ROOT = "mod_assets/mas_os/brand/"
    POWERED_BY = "powered by kurokawa gds"
    STUDIO = "Kurokawa GDS"
    STUDIO_LONG = "Kurokawa Game Dev Studio"

    BOOT_SPLASH = (
        ("logo", "Логотип студии", "Знак Kurokawa, радуга, powered by, потом рабочий стол."),
        ("wordmark", "Надпись", "Знак + kurokawa gds крупно, потом рабочий стол."),
        ("minimal", "Минимальная", "Короткий fade, только MAS OS."),
        ("off", "Выкл", "Сразу рабочий стол, без заставки."),
    )

    boot_preview = False
    boot_preview_mode = None

    def brand_path(name):
        if not name:
            return None
        if "." not in name:
            name = name + ".png"
        path = BRAND_ROOT + name
        try:
            if store.renpy.loadable(path):
                return path
        except Exception:
            pass
        return None

    def logo_path(kind="logo"):
        if kind == "wordmark":
            return brand_path("logo_wordmark.png") or brand_path("logo.png")
        if kind == "boot":
            return brand_path("boot_logo.png") or brand_path("logo_wordmark.png") or brand_path("logo.png")
        return brand_path("logo.png")

    def os_btn_idle():
        return brand_path("os_btn_idle.png") or TALK_IDLE

    def os_btn_hover():
        return brand_path("os_btn_hover.png") or TALK_HOVER

    def os_btn_size():
        custom = brand_path("os_btn_idle.png")
        if custom:
            try:
                w, h = store.renpy.image_size(custom)
                if w and h:
                    z = min(180.0 / float(w), 52.0 / float(h))
                    return (max(120, int(w * z)), max(36, int(h * z)))
            except Exception:
                pass
            return (180, 52)
        return TALK_SIZE

    def os_btn_disp(hover=False):
        path = os_btn_hover() if hover else os_btn_idle()
        w, h = os_btn_size()
        try:
            return store.renpy.display.im.Scale(path, int(w), int(h))
        except Exception:
            try:
                return store.im.Scale(path, int(w), int(h))
            except Exception:
                return path

    def os_btn_label_color():
        if brand_path("os_btn_idle.png"):
            return "#FFF6FB"
        return "#000000"

    def os_btn_label_size():
        _w, h = os_btn_size()
        if h >= 48:
            return 16
        return 14

    def boot_splash_saved():
        sid = getattr(store.persistent, "_mas_os_boot_splash", "logo") or "logo"
        for row in BOOT_SPLASH:
            if row[0] == sid:
                return sid
        return "logo"

    def boot_splash_id():
        if boot_preview_mode:
            return boot_preview_mode
        return boot_splash_saved()

    def boot_splash_on():
        if boot_preview:
            return True
        return boot_splash_id() != "off"

    def set_boot_splash(sid):
        ids = [row[0] for row in BOOT_SPLASH]
        if sid not in ids:
            sid = "logo"
        store.persistent._mas_os_boot_splash = sid
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        return None

    def start_boot_preview(mode):
        global boot_preview, boot_preview_mode
        ids = [row[0] for row in BOOT_SPLASH]
        if mode not in ids:
            mode = "logo"
        boot_preview = True
        boot_preview_mode = mode
        return None

    def end_boot_preview():
        global boot_preview, boot_preview_mode
        boot_preview = False
        boot_preview_mode = None
        return None

    def finish_boot_anim():
        if boot_preview:
            try:
                store.renpy.hide_screen("mas_os_boot_anim")
            except Exception:
                pass
            end_boot_preview()
            return None
        return "boot_done"

    def return_to_shell_action():
        if flag("_mas_os_return_confirm", True):
            return store.Show(
                screen="mas_os_confirm",
                message=RETURN_CONFIRM,
                yes_action=store.Function(return_to_shell),
                no_action=store.Hide("mas_os_confirm"),
            )
        return store.Function(return_to_shell)


init python:
    import colorsys
    import math

    class MASOSRainbowBorder(renpy.Displayable):
        """
        Animated rainbow rounded-rect / capsule stroke.
        """
        def __init__(self, tw=194, th=66, thickness=3, speed=0.30, radius=None, **kwargs):
            super(MASOSRainbowBorder, self).__init__(**kwargs)
            self.tw = int(tw)
            self.th = int(th)
            self.thickness = max(2, int(thickness))
            self.speed = float(speed)
            if radius is None:
                radius = self.th // 2
            self.radius = max(8, min(int(radius), self.tw // 2, self.th // 2))

        def _rgba(self, hue0, frac, alpha=255):
            h = (hue0 + frac) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, 0.88, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255), int(alpha))

        def render(self, width, height, st, at):
            tw = self.tw or int(width) or 194
            th = self.th or int(height) or 66
            rv = renpy.Render(tw, th)
            canvas = rv.canvas()
            t = self.thickness
            rad = self.radius
            hue0 = (st * self.speed) % 1.0

            def stroke_h(y, x0, x1, phase):
                y = max(0, min(th - t, int(y)))
                x = int(x0)
                end = int(x1)
                step = 3
                while x < end:
                    chunk = min(step, end - x)
                    frac = (phase + float(x) / float(max(tw, 1))) % 1.0
                    canvas.rect(self._rgba(hue0, frac), (x, y, chunk, t))
                    glow_y = y - 1 if y > 0 else y
                    canvas.rect(self._rgba(hue0, frac, 90), (x, glow_y, chunk, 1))
                    x += chunk

            def stroke_v(x, y0, y1, phase):
                x = max(0, min(tw - t, int(x)))
                y = int(y0)
                end = int(y1)
                step = 3
                while y < end:
                    chunk = min(step, end - y)
                    frac = (phase + float(y) / float(max(th, 1))) % 1.0
                    canvas.rect(self._rgba(hue0, frac), (x, y, t, chunk))
                    glow_x = x - 1 if x > 0 else x
                    canvas.rect(self._rgba(hue0, frac, 90), (glow_x, y, 1, chunk))
                    y += chunk

            # Straight edges, inset so corners own the arcs.
            stroke_h(0, rad, tw - rad, 0.00)
            stroke_h(th - t, rad, tw - rad, 0.50)
            stroke_v(0, rad, th - rad, 0.25)
            stroke_v(tw - t, rad, th - rad, 0.75)

            # Quarter-circle corners. Angles: TL π..π/2, TR π/2..0, BR 0..-π/2, BL -π/2..-π
            segs = max(10, int(rad * 1.2))
            corners = (
                (rad, rad, math.pi, math.pi * 0.5, 0.00),
                (tw - rad, rad, math.pi * 0.5, 0.0, 0.25),
                (tw - rad, th - rad, 0.0, -math.pi * 0.5, 0.50),
                (rad, th - rad, -math.pi * 0.5, -math.pi, 0.75),
            )
            for cx, cy, a0, a1, phase in corners:
                i = 0
                while i <= segs:
                    u = float(i) / float(segs)
                    ang = a0 + (a1 - a0) * u
                    # Outer radius through inner radius for thickness.
                    k = 0
                    while k < t:
                        rr = float(rad) - 0.5 - float(k)
                        px = int(cx + math.cos(ang) * rr)
                        py = int(cy - math.sin(ang) * rr)
                        if px < 0:
                            px = 0
                        elif px > tw - 2:
                            px = tw - 2
                        if py < 0:
                            py = 0
                        elif py > th - 2:
                            py = th - 2
                        canvas.rect(self._rgba(hue0, phase + u * 0.12, 255), (px, py, 2, 2))
                        k += 1
                    i += 1

            renpy.redraw(self, 0.05)
            return rv


    class MASOSHueBlob(renpy.Displayable):
        """Soft concentric hue wash behind the boot logo."""
        def __init__(self, size=380, **kwargs):
            super(MASOSHueBlob, self).__init__(**kwargs)
            self.size = int(size)

        def render(self, width, height, st, at):
            s = self.size
            rv = renpy.Render(s, s)
            canvas = rv.canvas()
            hue = (st * 0.18) % 1.0
            steps = 10
            i = 0
            while i < steps:
                pad = int(float(i) * s / float(2 * steps))
                t = 1.0 - (float(i) / float(steps))
                r, g, b = colorsys.hsv_to_rgb((hue + 0.08 * i) % 1.0, 0.78, 1.0)
                a = int(70 * t)
                w = max(2, s - pad * 2)
                canvas.rect(
                    (int(r * 255), int(g * 255), int(b * 255), a),
                    (pad, pad, w, w),
                )
                i += 1
            renpy.redraw(self, 0.06)
            return rv


transform mas_os_rainbow_pulse:
    alpha 0.78
    ease 1.15 alpha 1.0
    ease 1.15 alpha 0.78
    repeat


transform mas_os_logo_breathe:
    subpixel True
    transform_anchor True
    zoom 1.0
    ease 1.65 zoom 1.07
    ease 1.65 zoom 1.0
    repeat


transform mas_os_boot_aura:
    subpixel True
    transform_anchor True
    alpha 0.0
    zoom 0.72
    pause 0.08
    ease 0.70 alpha 0.55 zoom 1.18
    ease 1.80 alpha 0.18 zoom 1.42


transform mas_os_boot_logo_in:
    subpixel True
    transform_anchor True
    alpha 0.0
    zoom 0.70
    yoffset 18
    pause 0.22
    easein 0.52 alpha 1.0 zoom 1.0 yoffset 0
    pause 1.88
    ease 0.28 alpha 0.0 zoom 1.08


transform mas_os_boot_ring_in:
    alpha 0.0
    pause 0.30
    ease 0.36 alpha 1.0
    pause 1.92
    ease 0.24 alpha 0.0


transform mas_os_boot_in(delay=0.0):
    subpixel True
    alpha 0.0
    yoffset 14
    pause delay
    easein 0.36 alpha 1.0 yoffset 0


transform mas_os_boot_hold(t_out=2.55):
    alpha 1.0
    pause t_out
    ease 0.28 alpha 0.0


transform mas_os_boot_bar_in:
    alpha 0.0
    pause 0.92
    ease 0.24 alpha 1.0
    pause 1.55
    ease 0.22 alpha 0.0


transform mas_os_boot_min_in:
    subpixel True
    transform_anchor True
    alpha 0.0
    zoom 0.90
    yoffset 8
    pause 0.10
    easein 0.32 alpha 1.0 zoom 1.0 yoffset 0
    pause 0.62
    ease 0.22 alpha 0.0 zoom 1.04


transform mas_os_boot_cut:
    alpha 0.0
    pause 2.92
    ease 0.22 alpha 1.0


transform mas_os_boot_cut_wm:
    alpha 0.0
    pause 2.68
    ease 0.22 alpha 1.0


transform mas_os_boot_cut_min:
    alpha 0.0
    pause 1.18
    ease 0.20 alpha 1.0


transform mas_os_boot_off_dim:
    alpha 0.0
    ease 0.22 alpha 1.0


style mas_os_powered_text is default:
    font gui.default_font
    size 13
    color "#FFD56A"
    outlines []


style mas_os_studio_title is default:
    font gui.default_font
    size 20
    color "#FFE6F3"
    outlines []


screen mas_os_powered_line(size=13):
    text store.mas_os.POWERED_BY:
        style "mas_os_powered_text"
        size size
        substitute False


screen mas_os_powered(ypos=698, size=12):
    text store.mas_os.POWERED_BY:
        style "mas_os_powered_text"
        size size
        ypos ypos
        xalign 1.0
        xoffset -24
        substitute False


screen mas_os_logo_mark(kind="logo", max_w=72, max_h=72, xpos=None, ypos=None):
    $ lp = store.mas_os.logo_path(kind)

    if xpos is not None:
        fixed:
            xpos xpos
            ypos ypos
            xysize (max_w, max_h)

            if lp:
                add store.mas_os.fit_image(lp, max_w, max_h):
                    xalign 0.5
                    yalign 0.5
            else:
                frame:
                    xysize (max_w, max_h)
                    background Solid("#3A1524")

                    text "K":
                        style "mas_os_title"
                        size 28
                        xalign 0.5
                        yalign 0.5
                        color "#FF4FA3"
    else:
        fixed:
            xysize (max_w, max_h)

            if lp:
                add store.mas_os.fit_image(lp, max_w, max_h):
                    xalign 0.5
                    yalign 0.5
            else:
                frame:
                    xysize (max_w, max_h)
                    background Solid("#3A1524")

                    text "K":
                        style "mas_os_title"
                        size 28
                        xalign 0.5
                        yalign 0.5
                        color "#FF4FA3"


screen mas_os_return_chip(xpos=28, ypos=28):
    $ _w, _h = store.mas_os.os_btn_size()
    $ _pad = 7
    $ _tw = _w + _pad * 2
    $ _th = _h + _pad * 2
    $ _idle = store.mas_os.os_btn_disp(False)
    $ _hover = store.mas_os.os_btn_disp(True)
    $ _act = store.mas_os.return_to_shell_action()
    $ _label = store.mas_os.TALK_LABEL
    $ _col = store.mas_os.os_btn_label_color()
    $ _size = store.mas_os.os_btn_label_size()
    $ _rb = MASOSRainbowBorder(_tw, _th, 3, 0.32, radius=_th // 2)

    fixed:
        xpos xpos
        ypos ypos
        xysize (_tw, _th)

        add _rb:
            xpos 0
            ypos 0
            at mas_os_rainbow_pulse

        button:
            style "mas_os_talk_btn"
            xpos _pad
            ypos _pad
            xysize (_w, _h)
            padding (46, 0, 10, 0)
            idle_background _idle
            hover_background _hover
            selected_background _hover
            action _act

            if _label:
                text _label:
                    style "mas_os_talk_btn_text"
                    color _col
                    size _size


screen mas_os_boot_splash_picker(width=760):
    $ sid = store.mas_os.boot_splash_saved()
    $ _test_ic = store.mas_os.icon_path("view")
    $ _sel_w = int(width - 156)

    vbox:
        spacing 8
        xfill True

        for mid, mtitle, mhint in store.mas_os.BOOT_SPLASH:
            hbox:
                spacing 8

                button:
                    style "mas_os_side_btn"
                    xsize _sel_w
                    ysize 76
                    selected (mid == sid)
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action Function(store.mas_os.set_boot_splash, mid)

                    vbox:
                        spacing 2
                        yalign 0.5
                        xoffset 12
                        xsize (_sel_w - 24)

                        text mtitle:
                            style "mas_os_side_btn_text"
                            substitute False

                        text mhint:
                            style "mas_os_hint"
                            size 13
                            xsize (_sel_w - 40)
                            substitute False

                button:
                    style "mas_os_side_btn"
                    xsize 148
                    ysize 76
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()
                    action [
                        Function(store.mas_os.start_boot_preview, mid),
                        Show("mas_os_boot_anim"),
                    ]

                    hbox:
                        spacing 6
                        xalign 0.5
                        yalign 0.5

                        if _test_ic:
                            add store.mas_os.fit_image(_test_ic, 22, 22):
                                yalign 0.5

                        text _("Тест"):
                            style "mas_os_side_btn_text"
                            yalign 0.5


screen mas_os_boot_end(hold=3.2):
    default can_skip = False

    timer 0.40 action SetScreenVariable("can_skip", True)
    timer hold action Function(store.mas_os.finish_boot_anim)

    button:
        xpos 0
        ypos 0
        xysize (1280, 720)
        background None
        sensitive can_skip
        action Function(store.mas_os.finish_boot_anim)

    key "dismiss" action If(can_skip, Function(store.mas_os.finish_boot_anim), NullAction())
    key "K_RETURN" action If(can_skip, Function(store.mas_os.finish_boot_anim), NullAction())
    key "K_ESCAPE" action If(can_skip, Function(store.mas_os.finish_boot_anim), NullAction())
    key "K_AC_BACK" action If(can_skip, Function(store.mas_os.finish_boot_anim), NullAction())


screen mas_os_boot_bar():
    frame:
        xalign 0.5
        ypos 548
        xsize 320
        ysize 8
        background Solid("#1A0A14")
        clipping True
        at mas_os_boot_bar_in

        add Solid("#FF4FA3"):
            xysize (110, 8)
            at mas_os_indet_run

        add Solid("#3DFFF0"):
            xysize (48, 8)
            at mas_os_indet_run2


screen mas_os_boot_logo_seq():
    $ _lp = store.mas_os.logo_path("boot")
    $ _ring = MASOSRainbowBorder(248, 248, 4, 0.42, radius=52)
    $ _blob = MASOSHueBlob(400)

    add Solid("#050308")

    add _blob at mas_os_boot_aura:
        xalign 0.5
        yalign 0.40

    if _lp:
        add store.mas_os.fit_image(_lp, 300, 300) at mas_os_boot_aura:
            xalign 0.5
            yalign 0.40

    fixed at mas_os_boot_ring_in:
        xalign 0.5
        yalign 0.40
        xysize (248, 248)

        add _ring:
            xpos 0
            ypos 0

    if _lp:
        add store.mas_os.fit_image(_lp, 210, 210) at mas_os_boot_logo_in:
            xalign 0.5
            yalign 0.40
    else:
        text "K":
            style "mas_os_title"
            size 96
            color "#FF4FA3"
            xalign 0.5
            yalign 0.40
            at mas_os_boot_logo_in

    vbox at mas_os_boot_hold(2.55):
        xalign 0.5
        ypos 478
        spacing 4

        text store.mas_os.STUDIO:
            style "mas_os_studio_title"
            size 22
            xalign 0.5
            substitute False
            at mas_os_boot_in(0.72)

        text store.mas_os.POWERED_BY:
            style "mas_os_powered_text"
            size 16
            xalign 0.5
            substitute False
            at mas_os_boot_in(0.92)

    use mas_os_boot_bar

    add Solid("#000000") at mas_os_boot_cut

    use mas_os_boot_end(3.20)


screen mas_os_boot_wordmark_seq():
    $ _wm = store.mas_os.brand_path("logo_wordmark.png")
    $ _lp = store.mas_os.logo_path("logo")
    $ _blob = MASOSHueBlob(340)

    add Solid("#050308")

    add _blob at mas_os_boot_aura:
        xalign 0.5
        yalign 0.40

    if _wm:
        add store.mas_os.fit_image(_wm, 920, 300) at mas_os_boot_logo_in:
            xalign 0.5
            yalign 0.42
    else:
        hbox at mas_os_boot_hold(2.50):
            xalign 0.5
            yalign 0.42
            spacing 28

            if _lp:
                add store.mas_os.fit_image(_lp, 176, 176) at mas_os_boot_in(0.16):
                    yalign 0.5
            else:
                text "K":
                    style "mas_os_title"
                    size 72
                    color "#FF4FA3"
                    yalign 0.5
                    at mas_os_boot_in(0.16)

            vbox:
                spacing 6
                yalign 0.5

                text "kurokawa":
                    style "mas_os_title"
                    size 48
                    color "#FFF6FB"
                    substitute False
                    at mas_os_boot_in(0.38)

                text "GDS":
                    style "mas_os_powered_text"
                    size 28
                    color "#FFD56A"
                    substitute False
                    at mas_os_boot_in(0.54)

                text store.mas_os.POWERED_BY:
                    style "mas_os_powered_text"
                    size 16
                    substitute False
                    at mas_os_boot_in(0.72)

    add Solid("#000000") at mas_os_boot_cut_wm

    use mas_os_boot_end(2.95)


screen mas_os_boot_minimal_seq():
    add Solid("#050308")

    vbox at mas_os_boot_min_in:
        xalign 0.5
        yalign 0.48
        spacing 8

        text _("MAS OS"):
            style "mas_os_title"
            size 40
            xalign 0.5

        text store.mas_os.POWERED_BY:
            style "mas_os_powered_text"
            size 15
            xalign 0.5
            substitute False

    add Solid("#000000") at mas_os_boot_cut_min

    use mas_os_boot_end(1.45)


screen mas_os_boot_off_seq():
    add Solid("#000000") at mas_os_boot_off_dim

    use mas_os_boot_end(0.42)


screen mas_os_boot_anim():
    modal True
    zorder 500

    $ mode = store.mas_os.boot_splash_id()

    if mode == "wordmark":
        use mas_os_boot_wordmark_seq
    elif mode == "minimal":
        use mas_os_boot_minimal_seq
    elif mode == "off":
        use mas_os_boot_off_seq
    else:
        use mas_os_boot_logo_seq
