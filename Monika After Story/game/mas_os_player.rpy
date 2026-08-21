# MAS OS — audio player. Uses the MAS songs store (music_choices / custom_bgm),
# not a second library. Widget on home, full screen, volume in Settings.

init -5 python in mas_os:
    import random
    import store

    player_paused = True

    def player_loop_mode():
        mode = getattr(store.persistent, "_mas_os_music_loop", "one")
        if mode in ("one", "all", "off"):
            return mode
        return "one"

    def set_music_loop(mode):
        if mode not in ("one", "all", "off"):
            return
        store.persistent._mas_os_music_loop = mode
        try:
            store.renpy.save_persistent()
        except Exception:
            pass

    def _song_file(path):
        if not path:
            return path
        try:
            b = path.find(">")
        except Exception:
            return path
        if b >= 0:
            return path[b + 1:]
        return path

    def player_tracks():
        songs = getattr(store, "songs", None)
        if songs is None:
            return []
        choices = getattr(songs, "music_choices", None) or []
        out = []
        for row in choices:
            if not row or len(row) < 2:
                continue
            name, path = row[0], row[1]
            if not path:
                continue
            out.append((name, path))
        return out

    def player_current_path():
        p = None
        try:
            p = store.renpy.music.get_playing(channel="music")
        except Exception:
            p = None
        if p:
            return p
        songs = getattr(store, "songs", None)
        if songs is not None:
            p = getattr(songs, "current_track", None)
            if p:
                return p
        return getattr(store.persistent, "current_track", None)

    def player_index():
        cur = _song_file(player_current_path())
        if not cur:
            return -1
        tracks = player_tracks()
        for i, (_name, path) in enumerate(tracks):
            if _song_file(path) == cur:
                return i
        return -1

    def player_title():
        try:
            name = store.songs.getPlayingMusicName()
            if name:
                return name
        except Exception:
            pass
        idx = player_index()
        tracks = player_tracks()
        if 0 <= idx < len(tracks):
            return tracks[idx][0]
        cur = player_current_path()
        if not cur:
            return "Тишина"
        cur_f = _song_file(cur)
        for name, path in tracks:
            if path == cur or _song_file(path) == cur_f:
                return name
        return "Музыка"

    def player_is_playing():
        if player_paused:
            return False
        try:
            if store.renpy.music.get_pause(channel="music"):
                return False
        except Exception:
            pass
        try:
            return bool(store.renpy.music.is_playing(channel="music"))
        except Exception:
            return False

    def player_volume():
        try:
            return float(store.songs.getUserVolume("music"))
        except Exception:
            return 0.0

    def player_volume_pct():
        try:
            return int(round(player_volume() * 100))
        except Exception:
            return 0

    def mixer_pct(channel):
        try:
            return int(round(float(store.songs.getUserVolume(channel)) * 100))
        except Exception:
            return 0

    def player_music_muted():
        try:
            return bool(store.renpy.game.preferences.mute.get("music", False))
        except Exception:
            return False

    def player_all_muted():
        try:
            mute = store.renpy.game.preferences.mute
            if not mute:
                return False
            for v in mute.itervalues():
                if not v:
                    return False
            return True
        except Exception:
            return False

    def player_set_music_mute(value):
        try:
            store.renpy.game.preferences.mute["music"] = bool(value)
        except Exception:
            pass
        return None

    def player_set_all_mute(value):
        try:
            mute = store.renpy.game.preferences.mute
            for k in list(mute.keys()):
                mute[k] = bool(value)
        except Exception:
            pass
        return None

    def player_unmute_music():
        mute = None
        try:
            mute = store.renpy.game.preferences.mute
        except Exception:
            return None
        for key in ("music", "main"):
            try:
                mute[key] = False
            except Exception:
                pass
        return None

    def player_vol_bump(up=True):
        try:
            if up:
                player_unmute_music()
            store.songs.adjustVolume(channel="music", up=up)
        except Exception:
            pass
        return None

    def player_status_line():
        if player_all_muted():
            return "всё выкл"
        if player_music_muted() or player_volume() <= 0.0:
            return "без звука"
        if player_is_playing():
            n = len(player_tracks())
            extra = []
            if flag("_mas_os_music_shuffle", False):
                extra.append("перемешка")
            mode = player_loop_mode()
            if mode == "one":
                extra.append("повтор")
            elif mode == "all":
                extra.append("список")
            bits = "играет"
            if extra:
                bits = bits + " · " + " · ".join(extra)
            if n:
                bits = bits + " · {0} тр.".format(n)
            return bits
        if player_paused and player_current_path():
            return "пауза"
        return "остановлено"

    def player_play(path=None):
        global player_paused
        tracks = player_tracks()
        if path is None:
            if player_paused:
                paused = False
                playing = None
                try:
                    playing = store.renpy.music.get_playing(channel="music")
                    paused = bool(store.renpy.music.get_pause(channel="music"))
                except Exception:
                    paused = False
                    playing = None
                if playing and paused:
                    try:
                        store.renpy.music.set_pause(False, channel="music")
                    except Exception:
                        pass
                    player_paused = False
                    return None
            path = player_current_path()
            if not path and tracks:
                path = tracks[0][1]
        if not path:
            return None
        mode = player_loop_mode()
        loop_one = (mode == "one")
        player_paused = False
        try:
            store.mas_play_song(
                path,
                fadein=0.35,
                loop=loop_one,
                set_per=True,
                fadeout=0.25,
            )
        except Exception:
            try:
                store.renpy.music.play(
                    path,
                    channel="music",
                    loop=loop_one,
                    fadein=0.35,
                    fadeout=0.25,
                )
            except Exception:
                player_paused = True
                return None
        if mode == "all":
            _queue_rest(path)
        return None

    def _queue_rest(current):
        tracks = player_tracks()
        if len(tracks) < 2:
            return
        cur_f = _song_file(current)
        start = 0
        for i, (_name, path) in enumerate(tracks):
            if _song_file(path) == cur_f:
                start = i
                break
        rest = list(tracks[start + 1:] + tracks[:start])
        if flag("_mas_os_music_shuffle", False):
            random.shuffle(rest)
        for _name, path in rest:
            try:
                store.renpy.music.queue(path, channel="music", loop=False)
            except Exception:
                pass

    def player_pause():
        global player_paused
        player_paused = True
        try:
            store.renpy.music.set_pause(True, channel="music")
        except Exception:
            try:
                store.renpy.music.stop(channel="music", fadeout=0.2)
            except Exception:
                pass
        return None

    def player_toggle():
        if player_is_playing():
            return player_pause()
        return player_play(None)

    def player_stop():
        global player_paused
        player_paused = True
        try:
            store.mas_play_song(None, fadeout=0.25, set_per=True)
        except Exception:
            try:
                store.renpy.music.stop(channel="music", fadeout=0.25)
            except Exception:
                pass
        return None

    def player_next():
        tracks = player_tracks()
        if not tracks:
            return None
        if flag("_mas_os_music_shuffle", False) and len(tracks) > 1:
            cur = _song_file(player_current_path())
            nxt = tracks[random.randint(0, len(tracks) - 1)][1]
            tries = 0
            while _song_file(nxt) == cur and tries < 8:
                nxt = tracks[random.randint(0, len(tracks) - 1)][1]
                tries += 1
            return player_play(nxt)
        idx = player_index()
        if idx < 0:
            return player_play(tracks[0][1])
        nxt = (idx + 1) % len(tracks)
        return player_play(tracks[nxt][1])

    def player_prev():
        tracks = player_tracks()
        if not tracks:
            return None
        idx = player_index()
        if idx < 0:
            return player_play(tracks[0][1])
        prv = (idx - 1) % len(tracks)
        return player_play(tracks[prv][1])

    def player_rescan():
        songs = getattr(store, "songs", None)
        if songs is None:
            return None
        sayori = False
        try:
            sayori = store.mas_egg_manager.sayori_enabled()
        except Exception:
            pass
        try:
            songs.initMusicChoices(sayori)
        except Exception:
            pass
        return None

    def player_on_enter():
        global player_paused
        try:
            player_rescan()
        except Exception:
            pass
        if flag("_mas_os_music_autoplay", False):
            player_paused = False
            started = False
            try:
                store.mas_startup_song()
                started = bool(store.renpy.music.is_playing(channel="music"))
            except Exception:
                started = False
            if not started:
                player_play(None)
            else:
                player_paused = False
                try:
                    store.renpy.music.set_pause(False, channel="music")
                except Exception:
                    pass
        else:
            player_paused = True
            try:
                store.renpy.music.stop(channel="music", fadeout=0.4)
            except Exception:
                pass
        return None

    def player_count_line():
        n = len(player_tracks())
        if n == 0:
            return "Треков пока нет. Скачай ogg/mp3/opus через Склад или положи в custom_bgm."
        return "Плейлист MAS · {0} треков (встроенные + custom_bgm)".format(n)


screen mas_os_player_widget(width=420, height=132, ypos=386):
    $ _mus_ic = store.mas_os.icon_path("sound")
    $ _title = store.mas_os.player_title()
    $ _status = store.mas_os.player_status_line()
    $ _playing = store.mas_os.player_is_playing()
    $ _vol = store.mas_os.player_volume_pct()

    frame at store.mas_os.t_pop(0.12):
        style "mas_os_panel"
        xpos 56
        ypos ypos
        xsize width
        ysize height
        padding (16, 10)

        vbox:
            spacing 4
            xfill True

            hbox:
                spacing 8

                if _mus_ic:
                    add store.mas_os.fit_image(_mus_ic, 22, 22):
                        yalign 0.5

                button:
                    style "mas_os_link"
                    yalign 0.5
                    action Return("player")
                    hover_sound store.mas_os.os_hover()
                    activate_sound store.mas_os.os_activate()

                    text _title:
                        style "mas_os_body"
                        xsize 250
                        substitute False

                textbutton _("список"):
                    style "mas_os_player_mini"
                    text_style "mas_os_player_mini_text"
                    yalign 0.5
                    action Return("player")

            text _status:
                style "mas_os_hint"
                substitute False

            bar:
                value AudioPositionValue(channel="music", update_interval=0.35)
                xsize (width - 36)
                ysize 10
                style "mas_os_bar"

            hbox:
                spacing 6

                textbutton _("<<"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    action Function(store.mas_os.player_prev)

                if _playing:
                    textbutton _("||"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        selected True
                        action Function(store.mas_os.player_pause)
                else:
                    textbutton _(">"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        action Function(store.mas_os.player_toggle)

                textbutton _(">>"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    action Function(store.mas_os.player_next)

                textbutton _("−"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    action Function(store.mas_os.player_vol_bump, False)

                text "{0}%".format(_vol):
                    style "mas_os_hint"
                    yalign 0.5
                    min_width 52
                    text_align 0.5
                    substitute False

                textbutton _("+"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    action Function(store.mas_os.player_vol_bump, True)


screen mas_os_loop_toggle(width=720):
    $ mode = store.mas_os.player_loop_mode()
    $ third = int((width - 16) / 3)

    vbox:
        spacing 6
        xfill True

        text _("Повтор"):
            style "mas_os_hint"

        frame:
            style "mas_os_toggle_track"
            xsize width
            ysize 52
            padding (4, 4)

            hbox:
                spacing 4

                textbutton _("Трек"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize third
                    selected (mode == "one")
                    at mas_os_btn
                    action Function(store.mas_os.set_music_loop, "one")

                textbutton _("Список"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize third
                    selected (mode == "all")
                    at mas_os_btn
                    action Function(store.mas_os.set_music_loop, "all")

                textbutton _("Выкл"):
                    style "mas_os_toggle_opt"
                    text_style "mas_os_toggle_opt_text"
                    xsize third
                    selected (mode == "off")
                    at mas_os_btn
                    action Function(store.mas_os.set_music_loop, "off")


screen mas_os_pref_onoff(caption, hint, is_on, on_action, off_action):
    frame:
        style "mas_os_panel"
        xsize 760
        padding (16, 12)

        hbox:
            spacing 12
            xfill True

            vbox:
                xsize 470
                spacing 4

                text caption:
                    style "mas_os_subtitle"

                text hint:
                    style "mas_os_hint"

            frame:
                style "mas_os_toggle_track"
                xsize 236
                ysize 44
                padding (4, 4)
                yalign 0.5

                hbox:
                    spacing 4

                    textbutton _("Вкл"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 110
                        selected is_on
                        action on_action

                    textbutton _("Выкл"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 110
                        selected (not is_on)
                        action off_action


screen mas_os_vol_row(caption, hint, pref, channel=None):
    $ pct = store.mas_os.mixer_pct(channel) if channel else None

    frame:
        style "mas_os_panel"
        background Solid(store.mas_os.theme_color("panel2"))
        xsize 760
        padding (16, 12)

        vbox:
            spacing 8
            xfill True

            hbox:
                xfill True

                text caption:
                    style "mas_os_subtitle"

                if pct is not None:
                    text "{0}%".format(pct):
                        style "mas_os_hint"
                        xalign 1.0

            text hint:
                style "mas_os_hint"

            bar:
                value Preference(pref)
                xsize 720
                ysize 22
                style "mas_os_bar"


screen mas_os_player():
    modal True
    zorder 200

    $ tracks = store.mas_os.player_tracks()
    $ title = store.mas_os.player_title()
    $ status = store.mas_os.player_status_line()
    $ playing = store.mas_os.player_is_playing()
    $ vol = store.mas_os.player_volume_pct()
    $ cur_i = store.mas_os.player_index()
    $ _mus_ic = store.mas_os.icon_path("sound")
    $ count_line = store.mas_os.player_count_line()
    $ muted = store.mas_os.player_music_muted()

    use mas_os_bg

    text _("Плеер") at store.mas_os.t_pop(0.0):
        style "mas_os_title"
        xpos 48
        ypos 16

    text count_line at store.mas_os.t_pop(0.04):
        style "mas_os_hint"
        xpos 48
        ypos 58
        substitute False

    frame at store.mas_os.t_pop(0.06):
        style "mas_os_panel"
        xpos 48
        ypos 96
        xysize (520, 520)
        padding (20, 16)

        vbox:
            spacing 10
            xfill True

            hbox:
                spacing 10

                if _mus_ic:
                    add store.mas_os.fit_image(_mus_ic, 40, 40):
                        yalign 0.5

                vbox:
                    spacing 2

                    text _("Сейчас"):
                        style "mas_os_hint"

                    text title:
                        style "mas_os_stat_state"
                        color store.mas_os.theme_color("subtitle")
                        xsize 420
                        substitute False

            text status:
                style "mas_os_body"
                substitute False

            bar:
                value AudioPositionValue(channel="music", update_interval=0.3)
                xsize 470
                ysize 14
                style "mas_os_bar"

            hbox:
                spacing 8
                xalign 0.5

                textbutton _("<< пред"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 110
                    action Function(store.mas_os.player_prev)

                if playing:
                    textbutton _("Пауза"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        xsize 110
                        selected True
                        action Function(store.mas_os.player_pause)
                else:
                    textbutton _("Играть"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        xsize 110
                        action Function(store.mas_os.player_toggle)

                textbutton _("след >>"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 110
                    action Function(store.mas_os.player_next)

            hbox:
                spacing 8
                xalign 0.5

                textbutton _("Стоп"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 110
                    action Function(store.mas_os.player_stop)

                if muted:
                    textbutton _("Звук"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        xsize 110
                        action Function(store.mas_os.player_set_music_mute, False)
                else:
                    textbutton _("Без звука"):
                        style "mas_os_player_btn"
                        text_style "mas_os_player_btn_text"
                        xsize 110
                        selected True
                        action Function(store.mas_os.player_set_music_mute, True)

                textbutton _("Обновить"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 110
                    action Function(store.mas_os.player_rescan)

            text _("Громкость музыки"):
                style "mas_os_hint"

            hbox:
                spacing 8

                textbutton _("−"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 52
                    action Function(store.mas_os.player_vol_bump, False)

                bar:
                    value Preference("music volume")
                    xsize 330
                    ysize 22
                    yalign 0.5
                    style "mas_os_bar"

                textbutton _("+"):
                    style "mas_os_player_btn"
                    text_style "mas_os_player_btn_text"
                    xsize 52
                    action Function(store.mas_os.player_vol_bump, True)

            text "{0}%".format(vol):
                style "mas_os_hint"
                xalign 0.5

            frame:
                style "mas_os_panel"
                background Solid(store.mas_os.theme_color("panel2"))
                padding (12, 8)
                xfill True
                use mas_os_loop_toggle(width=454)

            frame:
                style "mas_os_toggle_track"
                xsize 454
                ysize 44
                padding (4, 4)

                hbox:
                    spacing 4

                    textbutton _("По порядку"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 218
                        selected (not store.mas_os.flag("_mas_os_music_shuffle", False))
                        action Function(store.mas_os.set_flag, "_mas_os_music_shuffle", False)

                    textbutton _("Перемешать"):
                        style "mas_os_toggle_opt"
                        text_style "mas_os_toggle_opt_text"
                        xsize 218
                        selected store.mas_os.flag("_mas_os_music_shuffle", False)
                        action Function(store.mas_os.set_flag, "_mas_os_music_shuffle", True)

    frame at store.mas_os.t_pop(0.08):
        style "mas_os_panel"
        xpos 588
        ypos 96
        xysize (644, 520)
        padding (12, 12)

        viewport:
            xysize (616, 492)
            draggable True
            mousewheel True
            scrollbars "vertical"

            vbox:
                spacing 6
                xsize 590

                if tracks:
                    for i, (name, path) in enumerate(tracks):
                        $ sel = (i == cur_i)
                        button:
                            style "mas_os_side_btn"
                            xsize 590
                            ysize 56
                            selected sel
                            hover_sound store.mas_os.os_hover()
                            activate_sound store.mas_os.os_activate()
                            action Function(store.mas_os.player_play, path)

                            hbox:
                                spacing 10
                                yalign 0.5
                                xoffset 10

                                text "{0:02d}".format(i + 1):
                                    style "mas_os_hint"
                                    yalign 0.5
                                    min_width 28

                                text name:
                                    style "mas_os_side_btn_text"
                                    yalign 0.5
                                    xsize 500
                                    substitute False
                else:
                    text _("Плейлист пуст. Склад → музыка, или файлы в custom_bgm."):
                        style "mas_os_hint"

    hbox:
        xpos 48
        ypos 640
        spacing 12

        textbutton _("Назад"):
            style "mas_os_nav_btn"
            text_style "mas_os_nav_btn_text"
            at mas_os_btn
            action Return("back")

        use mas_os_store_link("music", "player", 420)

    key "K_ESCAPE" action Return("back")
    key "K_AC_BACK" action Return("back")


style mas_os_bar is slider:
    ysize 14
    left_bar Solid("#C94A7A")
    right_bar Solid("#2A1018")
    thumb Solid("#FFE6F3")
    thumb_offset 0
    left_gutter 0
    right_gutter 0

style mas_os_player_btn is default:
    xsize 56
    ysize 44
    padding (6, 4)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    selected_background Solid("#C94A7A")
    selected_hover_background Solid("#E05A8A")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_player_btn_text is generic_button_text_dark:
    size 16
    text_align 0.5
    xalign 0.5
    yalign 0.5
    layout "subtitle"
    idle_color "#FFE6F3"
    hover_color "#FFFFFF"
    selected_color "#FFFFFF"

style mas_os_player_mini is default:
    xsize 88
    ysize 32
    padding (6, 2)
    idle_background Solid("#3A1524")
    hover_background Solid("#6A2442")
    hover_sound gui.hover_sound
    activate_sound gui.activate_sound

style mas_os_player_mini_text is generic_button_text_dark:
    size 14
    text_align 0.5
    xalign 0.5
    yalign 0.5
    layout "subtitle"
    idle_color "#FFD7EC"
    hover_color "#FFFFFF"
