# -*- coding: utf-8 -*-
# --- FILE MAP ---
# zz_affhearts.rpy — сердечки по бокам, когда растёт привязанность
#
# Как лайки на стриме: всплывают слева и справа и улетают вверх.
# Срабатывает из mas_affection._grant_aff, если очки реально добавились.
# Стили: stream / columns / burst / sparkle / soft / fireworks
# Текущий стиль: persistent._mas_affhearts_style (пока stream).
# Превью всех стилей — MAS OS → Настройки → Персонализация → Привязанность.
#
# Store: mas_affhearts
# Рисуется Displayable на слое overlay (не screen) — поверх всего
# и сама снимается, когда частицы доиграли.
# Ассеты: mod_assets/affhearts/
# ---

default persistent._mas_affhearts_style = "stream"


init -2 python in mas_affhearts:
    import random
    import time
    import store

    WIDTH = 1280
    HEIGHT = 720

    COOLDOWN = 1.25

    STYLE_STREAM = "stream"
    STYLE_COLUMNS = "columns"
    STYLE_BURST = "burst"
    STYLE_SPARKLE = "sparkle"
    STYLE_SOFT = "soft"
    STYLE_FIREWORKS = "fireworks"
    STYLE_RAIN = "rain"
    STYLE_FOUNTAIN = "fountain"
    STYLE_ORBIT = "orbit"
    STYLE_OFF = "off"

    STYLES = [
        STYLE_OFF,
        STYLE_STREAM,
        STYLE_COLUMNS,
        STYLE_BURST,
        STYLE_SPARKLE,
        STYLE_SOFT,
        STYLE_FIREWORKS,
        STYLE_RAIN,
        STYLE_FOUNTAIN,
        STYLE_ORBIT,
    ]

    STYLE_ROWS = (
        (STYLE_OFF, u"Выключено", u"Сердечки не появляются. Привязанность всё равно растёт."),
        (STYLE_STREAM, u"Лайки как на стриме", u"Сердечки всплывают с боков и улетают вверх."),
        (STYLE_COLUMNS, u"Колонны по бокам", u"Две вертикальные колонны сердечек по краям."),
        (STYLE_BURST, u"Взрыв из углов", u"Вылетают из нижних углов к центру."),
        (STYLE_SPARKLE, u"Искры и сердечки", u"Мелкие искры вместе с сердцами."),
        (STYLE_SOFT, u"Мягкие большие", u"Крупные полупрозрачные сердца."),
        (STYLE_FIREWORKS, u"Фейерверк по бокам", u"Вспышки по бокам экрана."),
        (STYLE_RAIN, u"Дождь сердец", u"Падают сверху вниз по всему экрану."),
        (STYLE_FOUNTAIN, u"Фонтан", u"Вылетают снизу из центра вверх."),
        (STYLE_ORBIT, u"Орбита", u"Кружатся вокруг Моники слева и справа."),
    )

    def current_style():
        sid = getattr(store.persistent, "_mas_affhearts_style", None) or STYLE_STREAM
        if sid not in STYLES:
            return STYLE_STREAM
        return sid

    def set_style(sid):
        if sid not in STYLES:
            sid = STYLE_STREAM
        store.persistent._mas_affhearts_style = sid
        try:
            store.renpy.save_persistent()
        except Exception:
            pass
        return None

    def preview(sid=None):
        if sid is None:
            sid = current_style()
        set_style(sid)
        if sid == STYLE_OFF:
            return None
        play(style=sid, amount=10.0, force=True)
        return None

    HEARTS = [
        "mod_assets/affhearts/heart_pink.png",
        "mod_assets/affhearts/heart_hot.png",
        "mod_assets/affhearts/heart_white.png",
        "mod_assets/affhearts/heart_lav.png",
        "mod_assets/affhearts/heart_gold.png",
    ]
    SOFT = "mod_assets/affhearts/heart_soft.png"
    SPARK = "mod_assets/affhearts/sparkle.png"

    particles = []
    duration = 3.8
    _last_play = 0.0

    class Particle(object):
        def __init__(self, img, x0, y0, x1, y1, delay, dur, rot, z0, z1, a0):
            self.img = img
            self.x0 = x0
            self.y0 = y0
            self.x1 = x1
            self.y1 = y1
            self.delay = delay
            self.dur = dur
            self.rot = rot
            self.z0 = z0
            self.z1 = z1
            self.a0 = a0


    def _count(amount, lo, hi):
        try:
            a = float(amount)
        except Exception:
            a = 1.0
        t = max(0.0, min(a / 12.0, 1.0))
        return int(lo + (hi - lo) * t)


    def _pick_heart(gold_ok=True):
        pool = list(HEARTS)
        if not gold_ok:
            pool = [p for p in pool if "gold" not in p]
        return random.choice(pool)


    def _build_stream(n):
        out = []
        for side in (0, 1):
            for i in range(n):
                if side == 0:
                    x0 = random.uniform(24, 108)
                    x1 = x0 + random.uniform(-36, 48)
                else:
                    x0 = random.uniform(1172, 1256)
                    x1 = x0 + random.uniform(-48, 36)
                y0 = random.uniform(640, 760)
                y1 = random.uniform(-60, 140)
                delay = random.uniform(0.0, 1.15)
                dur = random.uniform(2.15, 3.15)
                rot = random.uniform(-28, 28)
                z0 = random.uniform(0.42, 0.78)
                z1 = z0 + random.uniform(0.04, 0.18)
                img = SPARK if random.random() < 0.12 else _pick_heart()
                a0 = 0.92 if img != SPARK else 1.0
                out.append(Particle(img, x0, y0, x1, y1, delay, dur, rot, z0, z1, a0))
        return out


    def _build_columns(n):
        out = []
        for side in (0, 1):
            for i in range(n):
                if side == 0:
                    x0 = random.uniform(36, 92)
                else:
                    x0 = random.uniform(1188, 1244)
                x1 = x0 + random.uniform(-18, 18)
                y0 = random.uniform(520, 740)
                y1 = y0 - random.uniform(380, 640)
                delay = (i / float(max(n, 1))) * 0.9 + random.uniform(0.0, 0.12)
                dur = random.uniform(2.4, 3.4)
                rot = random.uniform(-12, 12)
                z0 = random.uniform(0.38, 0.7)
                z1 = z0
                out.append(Particle(_pick_heart(), x0, y0, x1, y1, delay, dur, rot, z0, z1, 0.9))
        return out


    def _build_burst(n):
        out = []
        corners = ((48, 705), (1232, 705))
        for cx, cy in corners:
            for i in range(n):
                inward = 1 if cx < 640 else -1
                x1 = cx + inward * random.uniform(40, 260)
                y1 = cy - random.uniform(280, 720)
                delay = random.uniform(0.0, 0.45)
                dur = random.uniform(1.8, 2.8)
                rot = random.uniform(-70, 70)
                z0 = random.uniform(0.35, 0.72)
                z1 = z0 + random.uniform(0.1, 0.28)
                img = SPARK if random.random() < 0.18 else _pick_heart()
                out.append(Particle(img, cx, cy, x1, y1, delay, dur, rot, z0, z1, 0.95))
        return out


    def _build_sparkle(n):
        out = []
        for side in (0, 1):
            for i in range(n):
                if side == 0:
                    x0 = random.uniform(16, 130)
                    x1 = x0 + random.uniform(-50, 70)
                else:
                    x0 = random.uniform(1150, 1264)
                    x1 = x0 + random.uniform(-70, 50)
                y0 = random.uniform(580, 750)
                y1 = random.uniform(-80, 180)
                delay = random.uniform(0.0, 1.0)
                dur = random.uniform(1.35, 2.25)
                rot = random.uniform(-50, 50)
                z0 = random.uniform(0.28, 0.62)
                z1 = z0 + random.uniform(0.05, 0.22)
                img = SPARK if random.random() < 0.45 else _pick_heart()
                out.append(Particle(img, x0, y0, x1, y1, delay, dur, rot, z0, z1, 1.0))
        return out


    def _build_soft(n):
        out = []
        for side in (0, 1):
            for i in range(n):
                if side == 0:
                    x0 = random.uniform(20, 150)
                    x1 = x0 + random.uniform(-20, 40)
                else:
                    x0 = random.uniform(1130, 1260)
                    x1 = x0 + random.uniform(-40, 20)
                y0 = random.uniform(620, 740)
                y1 = random.uniform(40, 220)
                delay = random.uniform(0.0, 0.9)
                dur = random.uniform(3.1, 4.2)
                rot = random.uniform(-16, 16)
                z0 = random.uniform(0.7, 1.15)
                z1 = z0 + random.uniform(0.08, 0.22)
                out.append(Particle(SOFT, x0, y0, x1, y1, delay, dur, rot, z0, z1, 0.62))
        return out


    def _build_fireworks(n):
        out = []
        origins = ((70, 430), (1210, 430), (70, 620), (1210, 620))
        per = max(3, n / 2)
        for ox, oy in origins:
            for i in range(per):
                ang_push = random.uniform(-140, 140)
                x1 = ox + ang_push
                y1 = oy - random.uniform(180, 520)
                delay = random.uniform(0.0, 0.55)
                dur = random.uniform(1.7, 2.7)
                rot = random.uniform(-90, 90)
                z0 = random.uniform(0.32, 0.75)
                z1 = z0 * random.uniform(0.85, 1.25)
                if random.random() < 0.28:
                    img = SPARK
                elif random.random() < 0.22:
                    img = "mod_assets/affhearts/heart_gold.png"
                else:
                    img = _pick_heart()
                out.append(Particle(img, ox, oy, x1, y1, delay, dur, rot, z0, z1, 0.95))
        return out


    def _build_rain(n):
        out = []
        for i in range(n + 6):
            x0 = random.uniform(40, 1240)
            x1 = x0 + random.uniform(-40, 40)
            y0 = random.uniform(-80, 40)
            y1 = random.uniform(640, 820)
            delay = random.uniform(0.0, 0.9)
            dur = random.uniform(1.8, 2.8)
            rot = random.uniform(-50, 50)
            z0 = random.uniform(0.35, 0.7)
            z1 = z0 * random.uniform(0.9, 1.2)
            img = SPARK if random.random() < 0.18 else _pick_heart()
            out.append(Particle(img, x0, y0, x1, y1, delay, dur, rot, z0, z1, 0.9))
        return out

    def _build_fountain(n):
        out = []
        for i in range(n + 4):
            x0 = random.uniform(600, 680)
            y0 = 730
            x1 = x0 + random.uniform(-280, 280)
            y1 = random.uniform(80, 320)
            delay = random.uniform(0.0, 0.7)
            dur = random.uniform(1.9, 2.9)
            rot = random.uniform(-70, 70)
            z0 = random.uniform(0.4, 0.8)
            z1 = z0 * random.uniform(0.8, 1.15)
            out.append(Particle(_pick_heart(), x0, y0, x1, y1, delay, dur, rot, z0, z1, 0.94))
        return out

    def _build_orbit(n):
        out = []
        for side in (0, 1):
            cx = 220 if side == 0 else 1060
            cy = 360
            for i in range(max(4, n / 2)):
                ang = random.uniform(0, 6.28)
                rad = random.uniform(70, 160)
                x0 = cx + rad * 0.2
                y0 = cy
                x1 = cx + rad
                y1 = cy + random.uniform(-120, 120)
                delay = random.uniform(0.0, 0.5)
                dur = random.uniform(2.0, 3.2)
                rot = random.uniform(-40, 40)
                z0 = random.uniform(0.4, 0.72)
                z1 = z0
                out.append(Particle(_pick_heart(), x0, y0, x1, y1, delay, dur, rot, z0, z1, 0.9))
        return out

    def _build(style, amount):
        if style == STYLE_OFF:
            return []
        if style == STYLE_COLUMNS:
            return _build_columns(_count(amount, 10, 16))
        if style == STYLE_BURST:
            return _build_burst(_count(amount, 8, 14))
        if style == STYLE_SPARKLE:
            return _build_sparkle(_count(amount, 14, 22))
        if style == STYLE_SOFT:
            return _build_soft(_count(amount, 5, 8))
        if style == STYLE_FIREWORKS:
            return _build_fireworks(_count(amount, 6, 10))
        if style == STYLE_RAIN:
            return _build_rain(_count(amount, 12, 20))
        if style == STYLE_FOUNTAIN:
            return _build_fountain(_count(amount, 10, 16))
        if style == STYLE_ORBIT:
            return _build_orbit(_count(amount, 10, 16))
        return _build_stream(_count(amount, 9, 16))


    def play(style=None, amount=6.0, force=False):
        """
        RUNTIME. Shows the side-heart overlay.

        IN:
            style - one of STYLES, or None to use persistent
            amount - affection gained, scales particle count
            force - ignore cooldown (debug preview)
        """
        global particles, duration, _last_play

        now = time.time()
        if not force and (now - _last_play) < COOLDOWN:
            return

        if style is None:
            style = current_style()
        if style not in STYLES:
            style = STYLE_STREAM
        if style == STYLE_OFF:
            return

        particles = _build(style, amount)
        duration = 4.2
        _last_play = now
        store.mas_affhearts_show()


init python:
    class MASAffHeartsDisplayable(renpy.Displayable):
        """
        Draws floating hearts itself on the overlay layer.
        Other screens / call screen do not own this, so they cannot eat it.
        """
        def __init__(self, particles):
            super(MASAffHeartsDisplayable, self).__init__()
            self.particles = list(particles)
            self._cache = {}

        def _child(self, img):
            d = self._cache.get(img)
            if d is None:
                d = Image(img)
                self._cache[img] = d
            return d

        def visit(self):
            return [self._child(p.img) for p in self.particles]

        def event(self, ev, x, y, st):
            return None

        def render(self, width, height, st, at):
            w = width or 1280
            h = height or 720
            rv = renpy.Render(w, h)
            alive = False

            for p in self.particles:
                t = st - p.delay
                if t < 0:
                    alive = True
                    continue
                if t >= p.dur:
                    continue
                alive = True

                u = t / float(p.dur)
                if u < 0.0:
                    u = 0.0
                elif u > 1.0:
                    u = 1.0

                ue = 1.0 - (1.0 - u) * (1.0 - u)
                x = p.x0 + (p.x1 - p.x0) * u
                y = p.y0 + (p.y1 - p.y0) * ue
                rot = p.rot * u
                z = p.z0 + (p.z1 - p.z0) * u

                if u < 0.08:
                    a = p.a0 * (u / 0.08)
                elif u > 0.55:
                    a = p.a0 * (1.0 - (u - 0.55) / 0.45)
                else:
                    a = p.a0
                if a < 0.0:
                    a = 0.0
                if a > 1.0:
                    a = 1.0

                child = Transform(
                    self._child(p.img),
                    rotate=rot,
                    zoom=z,
                    alpha=a,
                    subpixel=True
                )
                cr = renpy.render(child, w, h, st, at)
                cw, ch = cr.get_size()
                rv.blit(cr, (int(x - cw / 2.0), int(y - ch / 2.0)))

            if alive:
                renpy.redraw(self, 0)
            else:
                mas_affhearts_hide()

            return rv

    def mas_affhearts_hide():
        """RUNTIME. Removes the overlay displayable."""
        for _lyr in ("front", "overlay", "screens", "master"):
            try:
                renpy.hide("mas_affhearts_disp", layer=_lyr)
            except Exception:
                pass

    def mas_affhearts_show():
        """RUNTIME. Shows hearts on the front layer, above menus and overlays."""
        parts = list(store.mas_affhearts.particles)
        if not parts:
            return
        mas_affhearts_hide()
        renpy.show(
            "mas_affhearts_disp",
            what=MASAffHeartsDisplayable(parts),
            layer="front",
            zorder=250
        )
