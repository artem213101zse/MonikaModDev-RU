# -*- coding: utf-8 -*-
# --- FILE MAP ---
# zz_debugmenu.rpy — кнопка Debug в комнате (не MAS OS)
#
# Включается константой MAS_DEBUG_MENU в definitions.rpy.
# На релизе поставь False — кнопки не будет.
# Отсюда запускаются мини-игры и разблокируется контент так, будто
# Моника уже «открыла» его (пианино, шахматы, виселица, NOU, острова…).
#
# Labels: mas_debug_menu, mas_debug_games, mas_debug_unlocks,
#         mas_debug_progress, mas_debug_islands, mas_debug_hearts,
#         mas_debug_room, mas_debug_scenes, mas_debug_weather, mas_debug_bg
# Кнопка: zz_hotkey_buttons.rpy (справа внизу). Хоткей: Shift+D.
# ---

init python:
    import store
    import datetime

    def mas_debug_open():
        """RUNTIME ONLY. Opens the in-game debug menu."""
        if not MAS_DEBUG_MENU:
            return
        renpy.jump("mas_debug_menu")


    def mas_debug_mark_ev_seen(evlabel):
        """Marks an event as already shown so ch30 resets keep it unlocked."""
        ev = mas_getEV(evlabel)
        if ev is None:
            return False
        if ev.shown_count < 1:
            ev.shown_count = 1
        ev.unlocked = True
        ev.last_seen = datetime.datetime.now()
        return True


    def mas_debug_mark_label_seen(label):
        """Marks a raw label as seen (needed for NOU gift check)."""
        se = getattr(persistent, "_seen_ever", None)
        if se is None:
            return
        try:
            se[label] = True
        except Exception:
            try:
                se.add(label)
            except Exception:
                pass


    def mas_debug_unlock_game(gamename, unlock_evl=None):
        """
        Unlocks a minigame as if Monika already introduced it.
        Survives the ch30 games() reset.
        """
        mas_unlockGame(gamename)
        if unlock_evl:
            mas_debug_mark_ev_seen(unlock_evl)
        if gamename.lower() == "nou":
            mas_debug_mark_label_seen("mas_reaction_gift_noudeck")
        if gamename.lower() == "chess":
            persistent._mas_chess_timed_disable = None
        return mas_isGameUnlocked(gamename) or (
            mas_games.getGameEVByPrompt(gamename) is not None
            and mas_games.getGameEVByPrompt(gamename).unlocked
        )


    def mas_debug_unlock_all_games():
        mas_debug_unlock_game("pong")
        mas_debug_unlock_game("chess", "mas_unlock_chess")
        mas_debug_unlock_game("hangman", "mas_unlock_hangman")
        mas_debug_unlock_game("piano", "mas_unlock_piano")
        mas_debug_unlock_game("nou")


    def mas_debug_game_state(gamename):
        ev = mas_games.getGameEVByPrompt(gamename)
        if ev is None:
            return "?"
        if ev.unlocked:
            return u"открыто"
        return u"закрыто"


    def mas_debug_esc(text):
        """Ren'Py treats [name] in buttons as interpolation. Escape it."""
        if text is None:
            return ""
        if not isinstance(text, unicode):
            try:
                text = text.decode("utf-8")
            except Exception:
                text = unicode(text)
        return text.replace(u"[", u"[[")


    def mas_debug_set_aff(value):
        """Sets affection. Uses the developer setter, falls back to grant."""
        value = float(value)
        store.mas_affection._set_aff(value, "DEBUG")
        cur = store.mas_affection._get_aff()
        if abs(cur - value) > 1.0:
            if value > cur:
                mas_gainAffection(value - cur, bypass=True)
        mas_updateAffectionExp()
        return store.mas_affection._get_aff()


    def mas_debug_add_xp_levels(levels):
        store.mas_xp._grant_xp(store.mas_xp.XP_LVL_RATE * int(levels))
        return store.mas_xp.level()


    def mas_debug_unlock_islands():
        """Unlocks islands and all progress sprites."""
        aff = store.mas_affection._get_aff()
        if aff < store.mas_affection.AFF_ENAMORED_MIN:
            mas_debug_set_aff(store.mas_affection.AFF_ENAMORED_MIN + 50)
        store.mas_island_event.start_progression()
        if persistent._mas_islands_start_lvl is None:
            persistent._mas_islands_start_lvl = store.mas_xp.level()
        persistent._mas_islands_progress = store.mas_island_event.MAX_PROGRESS_LOVE
        unlocks = persistent._mas_islands_unlocks
        if unlocks:
            for key in list(unlocks.keys()):
                unlocks[key] = True
        mas_unlockEVL("mas_monika_islands", "EVE")


    def mas_debug_unlock_songs():
        count = 0
        for ev in store.mas_songs.song_db.itervalues():
            if not ev.unlocked:
                ev.unlocked = True
                count += 1
        store.mas_songs.checkRandSongDelegate()
        store.mas_songs.checkSongAnalysisDelegate()
        return count


    def mas_debug_unlock_stories():
        count = 0
        for ev in store.mas_stories.story_database.itervalues():
            if not ev.unlocked:
                ev.unlocked = True
                count += 1
        return count


    def mas_debug_unlock_pool_topics():
        count = 0
        for ev in store.evhand.event_database.itervalues():
            if ev.pool and "no_unlock" not in ev.rules and not ev.unlocked:
                mas_unlockEvent(ev)
                ev.unlock_date = datetime.datetime.now()
                count += 1
        return count


    def mas_debug_unlock_backgrounds():
        count = 0
        for bg_id in store.mas_background.BACKGROUND_MAP.keys():
            if not store.mas_background.isBackgroundUnlocked(bg_id):
                store.mas_background.unlockBackground(bg_id)
                count += 1
        return count


    def mas_debug_unlock_weather():
        count = 0
        for mw_id, mw_obj in store.mas_weather.WEATHER_MAP.iteritems():
            if not mw_obj.unlocked:
                mw_obj.unlocked = True
                count += 1
        store.mas_weather.saveMWData()
        return count


    def mas_debug_unlock_sprites():
        count = 0
        maps = (
            store.mas_selspr.ACS_SEL_MAP,
            store.mas_selspr.HAIR_SEL_MAP,
            store.mas_selspr.CLOTH_SEL_MAP,
        )
        for sel_map in maps:
            for sel in sel_map.itervalues():
                if not sel.unlocked:
                    sel.unlocked = True
                    count += 1
        for key in store.mas_selspr.PROMPT_MAP:
            store.mas_selspr.unlock_prompt(key)
        store.mas_selspr.save_selectables()
        return count


    def mas_debug_status_line():
        aff = store.mas_affection._get_aff()
        lvl = store.mas_xp.level()
        return u"aff {0:.0f}  |  lvl {1}  |  piano {2}  chess {3}  hangman {4}  nou {5}".format(
            aff,
            lvl,
            mas_debug_game_state("piano"),
            mas_debug_game_state("chess"),
            mas_debug_game_state("hangman"),
            mas_debug_game_state("nou"),
        )


    def mas_debug_items(pairs, first=None):
        """Sorted (prompt, value) rows for mas_gen_scrollable_menu."""
        rows = []
        if first:
            for prompt, value in first:
                rows.append((mas_debug_esc(prompt), value, False, False))
        pairs = sorted(list(pairs), key=lambda item: item[0].lower())
        for prompt, value in pairs:
            rows.append((mas_debug_esc(prompt), value, False, False))
        return rows


    def mas_debug_push_and_leave(evl):
        """Queue an event then return to ch30 so it actually runs."""
        MASEventList.push(evl, skipeval=True)
        renpy.jump("mas_debug_menu_close")


label mas_debug_menu:
    $ mas_RaiseShield_core()
    $ mas_HKBRaiseShield()
    jump mas_debug_menu_root


label mas_debug_menu_close:
    $ mas_DropShield_core()
    if store.mas_globals.in_idle_mode:
        $ mas_coreToIdleShield()
    if not renpy.showing("monika idle"):
        show monika idle at t11
    jump ch30_loop


label mas_debug_menu_root:
    python:
        _dbg_items = mas_debug_items(
            [
                (u"Анимации", "hearts"),
                (u"Комната", "room"),
                (u"Контент", "unlocks"),
                (u"Мини-игры", "games"),
                (u"Острова", "islands"),
                (u"Прокачка", "progress"),
                (u"Сцены", "scenes"),
            ],
            first=[(mas_debug_status_line(), "status")],
        )
        _dbg_back = ("Закрыть", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return or _return == "status":
        if not _return:
            jump mas_debug_menu_close
        jump mas_debug_menu_root

    elif _return == "games":
        jump mas_debug_games
    elif _return == "islands":
        jump mas_debug_islands
    elif _return == "unlocks":
        jump mas_debug_unlocks
    elif _return == "progress":
        jump mas_debug_progress
    elif _return == "hearts":
        jump mas_debug_hearts
    elif _return == "room":
        jump mas_debug_room
    elif _return == "scenes":
        jump mas_debug_scenes

    jump mas_debug_menu_root


label mas_debug_menu_close_to_extra:
    $ mas_DropShield_core()
    jump mas_extra_menu


label mas_debug_games:
    python:
        _dbg_items = mas_debug_items([
            (u"Запустить: NOU ({0})".format(mas_debug_game_state("nou")), "run:mas_nou"),
            (u"Запустить: Виселица ({0})".format(mas_debug_game_state("hangman")), "run:mas_hangman"),
            (u"Запустить: Пинг-понг ({0})".format(mas_debug_game_state("pong")), "run:mas_pong"),
            (u"Запустить: Пианино ({0})".format(mas_debug_game_state("piano")), "run:mas_piano"),
            (u"Запустить: Шахматы ({0})".format(mas_debug_game_state("chess")), "run:mas_chess"),
            (u"Открыть NOU (без сцены)", "silent:nou"),
            (u"Открыть виселицу (без сцены)", "silent:hangman"),
            (u"Открыть пианино (без сцены)", "silent:piano"),
            (u"Открыть шахматы (без сцены)", "silent:chess"),
            (u"Разблокировать все игры сразу", "unlock_all"),
            (u"Сцена Моники: виселица", "scene:mas_unlock_hangman"),
            (u"Сцена Моники: пианино", "scene:mas_unlock_piano"),
            (u"Сцена Моники: шахматы", "scene:mas_unlock_chess"),
        ])
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    $ _dbg_choice = _return
    if not _dbg_choice or not isinstance(_dbg_choice, (str, unicode)):
        jump mas_debug_menu_root

    if _dbg_choice.startswith("run:"):
        $ MASEventList.push(_dbg_choice[4:], skipeval=True)
        jump mas_debug_menu_close

    elif _dbg_choice == "unlock_all":
        $ mas_debug_unlock_all_games()
        $ renpy.notify("Все мини-игры открыты")
        jump mas_debug_games

    elif _dbg_choice.startswith("scene:"):
        $ _dbg_arg = _dbg_choice[6:]
        if _dbg_arg == "mas_unlock_chess":
            $ mas_debug_unlock_game("chess", "mas_unlock_chess")
        elif _dbg_arg == "mas_unlock_hangman":
            $ mas_debug_unlock_game("hangman", "mas_unlock_hangman")
        elif _dbg_arg == "mas_unlock_piano":
            $ mas_debug_unlock_game("piano", "mas_unlock_piano")
        $ MASEventList.push(_dbg_arg, skipeval=True)
        jump mas_debug_menu_close

    elif _dbg_choice.startswith("silent:"):
        python:
            _dbg_arg = _dbg_choice[7:]
            _map = {
                "chess": "mas_unlock_chess",
                "hangman": "mas_unlock_hangman",
                "piano": "mas_unlock_piano",
                "nou": None,
            }
            mas_debug_unlock_game(_dbg_arg, _map.get(_dbg_arg))
            renpy.notify(_dbg_arg + ": ok")
        jump mas_debug_games

    jump mas_debug_games


label mas_debug_islands:
    python:
        _isl_on = persistent._mas_islands_start_lvl is not None
        _dbg_items = mas_debug_items(
            [
                (u"Показать острова", "show"),
                (u"Разблокировать острова полностью", "unlock"),
            ],
            first=[(
                u"Острова: {0}  progress {1}".format(
                    u"открыты" if _isl_on else u"закрыты",
                    persistent._mas_islands_progress
                ),
                "status",
            )],
        )
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return or _return == "status":
        if not _return:
            jump mas_debug_menu_root
        jump mas_debug_islands

    elif _return == "unlock":
        $ mas_debug_unlock_islands()
        $ renpy.notify("Острова разблокированы")
        jump mas_debug_islands

    elif _return == "show":
        if persistent._mas_islands_start_lvl is None:
            $ mas_debug_unlock_islands()
        if not mas_canShowIslands(False):
            $ renpy.notify("Острова нельзя показать (нет декода пакета)")
            jump mas_debug_islands
        $ MASEventList.push("mas_monika_islands", skipeval=True)
        jump mas_debug_menu_close

    jump mas_debug_islands


label mas_debug_unlocks:
    python:
        _dbg_items = mas_debug_items([
            (u"Открыть все песни", "songs"),
            (u"Открыть все pool-темы в Поговорить", "pool"),
            (u"Открыть все фоны", "bgs"),
            (u"Открыть все истории", "stories"),
            (u"Открыть всю погоду", "weather"),
            (u"Открыть одежду / волосы / аксессуары", "sprites"),
            (u"Открыть ВСЁ из этого списка", "all"),
        ])
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return:
        jump mas_debug_menu_root

    python:
        _n = 0
        if _return in ("songs", "all"):
            _n += mas_debug_unlock_songs()
        if _return in ("stories", "all"):
            _n += mas_debug_unlock_stories()
        if _return in ("pool", "all"):
            _n += mas_debug_unlock_pool_topics()
        if _return in ("bgs", "all"):
            _n += mas_debug_unlock_backgrounds()
        if _return in ("weather", "all"):
            _n += mas_debug_unlock_weather()
        if _return in ("sprites", "all"):
            _n += mas_debug_unlock_sprites()
        if _return == "all":
            mas_debug_unlock_all_games()
            mas_debug_unlock_islands()
        renpy.notify("Разблокировано: {0}".format(_n))

    jump mas_debug_unlocks


label mas_debug_progress:
    python:
        _aff = store.mas_affection
        _dbg_items = mas_debug_items(
            [
                (u"Affection +10", "aff10"),
                (u"Affection +100", "aff100"),
                (u"Affection -50", "affm50"),
                (u"Уровень: BROKEN (-100)", "affset:{0}".format(int(_aff.AFF_BROKEN_MIN))),
                (u"Уровень: DISTRESSED (-75)", "affset:{0}".format(int(_aff.AFF_DISTRESSED_MIN))),
                (u"Уровень: UPSET (-30)", "affset:{0}".format(int(_aff.AFF_UPSET_MIN))),
                (u"Уровень: NORMAL (0)", "affset:0"),
                (u"Уровень: HAPPY (50)", "affset:{0}".format(int(_aff.AFF_HAPPY_MIN))),
                (u"Уровень: AFFECTIONATE (100)", "affset:{0}".format(int(_aff.AFF_AFFECTIONATE_MIN))),
                (u"Уровень: ENAMORED (400)", "affset:{0}".format(int(_aff.AFF_ENAMORED_MIN))),
                (u"Уровень: LOVE (1000)", "affset:{0}".format(int(_aff.AFF_LOVE_MIN))),
                (u"XP +1 уровень", "xp1"),
                (u"XP +5 уровней", "xp5"),
                (u"XP +12 уровней (порог пианино)", "xp12"),
            ],
            first=[(
                u"Сейчас: aff {0:.0f}  lvl {1}".format(
                    store.mas_affection._get_aff(),
                    store.mas_xp.level()
                ),
                "status",
            )],
        )
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return or _return == "status":
        if not _return:
            jump mas_debug_menu_root
        jump mas_debug_progress

    elif _return == "aff10":
        $ mas_gainAffection(10, bypass=True)
        $ mas_updateAffectionExp()
        $ renpy.notify("aff {0:.0f}".format(store.mas_affection._get_aff()))

    elif _return == "aff100":
        $ mas_gainAffection(100, bypass=True)
        $ mas_updateAffectionExp()
        $ renpy.notify("aff {0:.0f}".format(store.mas_affection._get_aff()))

    elif _return == "affm50":
        $ mas_loseAffection(50)
        $ mas_updateAffectionExp()
        $ renpy.notify("aff {0:.0f}".format(store.mas_affection._get_aff()))

    elif isinstance(_return, (str, unicode)) and _return.startswith("affset:"):
        $ mas_debug_set_aff(float(_return[7:]))
        $ renpy.notify("aff {0:.0f}".format(store.mas_affection._get_aff()))

    elif _return == "xp1":
        $ mas_debug_add_xp_levels(1)
        $ renpy.notify("lvl {0}".format(store.mas_xp.level()))

    elif _return == "xp5":
        $ mas_debug_add_xp_levels(5)
        $ renpy.notify("lvl {0}".format(store.mas_xp.level()))

    elif _return == "xp12":
        $ mas_debug_add_xp_levels(12)
        $ renpy.notify("lvl {0}".format(store.mas_xp.level()))

    jump mas_debug_progress


label mas_debug_hearts:
    python:
        _cur = persistent._mas_affhearts_style or "stream"
        _dbg_items = mas_debug_items(
            [
                (u"Взрыв из углов", "burst"),
                (u"Искры и сердечки", "sparkle"),
                (u"Колонны по бокам", "columns"),
                (u"Лайки как на стриме", "stream"),
                (u"Мягкие большие", "soft"),
                (u"Показать со словами Моники", "dlg"),
                (u"Фейерверк по бокам", "fireworks"),
            ],
            first=[(u"Сейчас выбран: {0}".format(_cur), "status")],
        )
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return or _return == "status":
        if not _return:
            jump mas_debug_menu_root
        jump mas_debug_hearts

    if _return == "dlg":
        jump mas_debug_hearts_dlg

    python:
        _hs = _return
        if _hs in store.mas_affhearts.STYLES:
            persistent._mas_affhearts_style = _hs
            store.mas_affhearts.play(style=_hs, amount=10.0, force=True)

    jump mas_debug_hearts


label mas_debug_hearts_dlg:
    show monika 1hua at t11 zorder MAS_MONIKA_Z
    m 1hua "Смотри внимательно по краям экрана~"
    $ store.mas_affhearts.play(style=persistent._mas_affhearts_style, amount=10.0, force=True)
    pause 3.2
    m 3eua "Это анимация за прибавку привязанности. Ну как, видно?"
    jump mas_debug_hearts


label mas_debug_room:
    python:
        _dbg_items = mas_debug_items([
            (u"Календарь", "calendar"),
            (u"Меню Extra", "extra"),
            (u"Музыка комнаты", "music"),
            (u"Сменить погоду", "weather"),
            (u"Сменить фон", "bg"),
            (u"Тема: день (светлая)", "day"),
            (u"Тема: ночь (тёмная)", "night"),
        ])
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return:
        jump mas_debug_menu_root
    elif _return == "calendar":
        call mas_start_calendar_read_only
        jump mas_debug_room
    elif _return == "music":
        $ select_music()
        jump mas_debug_room
    elif _return == "extra":
        jump mas_debug_menu_close_to_extra
    elif _return == "weather":
        jump mas_debug_weather
    elif _return == "bg":
        jump mas_debug_bg
    elif _return == "day":
        $ mas_darkMode(True)
        $ renpy.notify("день")
        jump mas_debug_menu_close
    elif _return == "night":
        $ mas_darkMode(False)
        $ renpy.notify("ночь")
        jump mas_debug_menu_close
    jump mas_debug_room


label mas_debug_weather:
    python:
        _pairs = []
        for mw in store.mas_weather.WEATHER_MAP.itervalues():
            prompt = getattr(mw, "prompt", None) or getattr(mw, "weather_id", "?")
            _pairs.append((u"Погода: {0}".format(prompt), mw.weather_id))
        _dbg_items = mas_debug_items(_pairs)
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return:
        jump mas_debug_room

    python:
        _mw = store.mas_weather.WEATHER_MAP.get(_return)
        if _mw is not None:
            store.mas_changeWeather(_mw, by_user=True)
            renpy.notify(unicode(_return))
    jump mas_debug_menu_close


label mas_debug_bg:
    python:
        _pairs = []
        for bg_id, bg in store.mas_background.BACKGROUND_MAP.iteritems():
            prompt = getattr(bg, "prompt", None) or bg_id
            _pairs.append((u"Фон: {0}".format(prompt), bg_id))
        _dbg_items = mas_debug_items(_pairs)
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return:
        jump mas_debug_room

    $ _dbg_bg = store.mas_background.BACKGROUND_MAP.get(_return)
    if _dbg_bg is None:
        jump mas_debug_bg
    $ mas_DropShield_core()
    call mas_background_change(_dbg_bg, skip_leadin=True, skip_outro=True, set_persistent=True)
    jump ch30_loop


label mas_debug_scenes:
    python:
        _dbg_items = mas_debug_items([
            (u"Интересный факт", "facts"),
            (u"Кино", "movie"),
            (u"Настроение", "mood"),
        ])
        _dbg_back = ("Назад", False, False, False, 20)

    call screen mas_gen_scrollable_menu(_dbg_items, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, _dbg_back)

    if not _return:
        jump mas_debug_menu_root
    elif _return == "facts":
        $ MASEventList.push("monika_fun_facts_open", skipeval=True)
        jump mas_debug_menu_close
    elif _return == "movie":
        $ MASEventList.push("mas_monikamovie", skipeval=True)
        jump mas_debug_menu_close
    elif _return == "mood":
        $ MASEventList.push("mas_mood_start", skipeval=True)
        jump mas_debug_menu_close
    jump mas_debug_scenes
