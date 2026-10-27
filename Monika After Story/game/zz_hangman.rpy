# --- FILE MAP ---
# zz_hangman.rpy — виселица
#
# Слова, логика угадывания, диалоги вокруг игры.
#
# Store: mas_hangman
# Вход из zz_games.rpy
# ---

# RU-хелпер окончаний по полу (тот же, что в script-story-events.rpy;
# создаётся, только если ещё не определён)
init -1 python:
    if not hasattr(store, "MASRuGenderForm"):
        class MASRuGenderForm(object):
            def __init__(self, fem, masc):
                self.fem = fem
                self.masc = masc
            def _get(self):
                return self.fem if persistent.gender == "F" else self.masc
            def __unicode__(self):
                return self._get()
            def __str__(self):
                return self._get().encode("utf-8")
            def __format__(self, spec):
                return self._get()
        store.MASRuGenderForm = MASRuGenderForm
    for _ru_n, _ru_f, _ru_m in (
            ("_ru_a", u"а", u""), ("_ru_la", u"ла", u""), ("_ru_sya", u"ась", u"ся"),
        ):
        if not hasattr(store, _ru_n):
            setattr(store, _ru_n, store.MASRuGenderForm(_ru_f, _ru_m))

# Module that does hangman man
#
# DEPENDS ON:
#   zz_poemgame

# hangman stuff only
default persistent._mas_hangman_playername = False
define hm_ltrs_only = u"abcdefghijklmnopqrstuvwxyzабвгдеёжзийклмнопрстуфхцчшщъыьэюя?!"

# IMAGES-----------
# hangman
image hm_6 = "mod_assets/games/hangman/hm_6.png"
image hm_5 = "mod_assets/games/hangman/hm_5.png"
image hm_4 = "mod_assets/games/hangman/hm_4.png"
image hm_3 = "mod_assets/games/hangman/hm_3.png"
image hm_2 = "mod_assets/games/hangman/hm_2.png"
image hm_1 = "mod_assets/games/hangman/hm_1.png"
image hm_0 = "mod_assets/games/hangman/hm_0.png"

# sayori
image hm_s:
    block:

        # this block handles images
        block:
            choice:
                "mod_assets/games/hangman/hm_s1.png"
            choice:
                "mod_assets/games/hangman/hm_s2.png"

        # this block makes the image flicker
        # the numbers are times to display
        block:
            choice:
                0.075
            choice:
                0.09
            choice:
                0.05
        repeat

# window sayori
# we are dependent on exisitng images to create the window sayori
define hm.SAYORI_SCALE = 0.25
image hm_s_win_6 = im.FactorScale(im.Flip(getCharacterImage("sayori", "4r"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_5 = im.FactorScale(im.Flip(getCharacterImage("sayori", "2a"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_4 = im.FactorScale(im.Flip(getCharacterImage("sayori", "2i"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_3 = im.FactorScale(im.Flip(getCharacterImage("sayori", "1f"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_2 = im.FactorScale(im.Flip(getCharacterImage("sayori", "4u"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_1 = im.FactorScale(im.Flip(getCharacterImage("sayori", "4w"), horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_0 = im.FactorScale(im.Flip("images/sayori/end-glitch1.png", horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_fail = im.FactorScale(im.Flip("images/sayori/3c.png", horizontal=True), hm.SAYORI_SCALE)
image hm_s_win_leave = im.FactorScale(getCharacterImage("sayori", "1a"), hm.SAYORI_SCALE)

#image hm_s1 = "mod_assets/games/hangman/hm_s1.png"
#image hm_s2 = "mod_assets/games/hangman/hm_s2.png"

# frame
image hm_frame = "mod_assets/games/hangman/hm_frame.png"
image hm_frame_dark = "mod_assets/games/hangman/hm_frame_d.png"

# TRANSFORMS
transform hangman_board:
    xanchor 0 yanchor 0 xpos 675 ypos 100 alpha 1.0

transform hangman_missed_label:
    xanchor 0 yanchor 0 xpos 680 ypos 95

transform hangman_missed_chars:
    xanchor 0 yanchor 0 xpos 765 ypos 95

transform hangman_display_word:
    xcenter 975 yanchor 0 ypos 473

transform hangman_hangman:
    xanchor 0 yanchor 0 xpos 880 ypos 125

# window sayori
# left in
transform hangman_sayori(z=1.0):
    xcenter -300 yoffset 0 yalign 0.47 zoom z*1.00 alpha 1.00 subpixel True
    easein 0.25 xcenter 90

# regular
transform hangman_sayori_i(z=1.0):
    xcenter 90 yoffset 0 yalign 0.47 zoom z*1.00 alpha 1.00 subpixel True

# 3c offset
transform hangman_sayori_i3(z=1.0):
    xcenter 82 yoffset 0 yalign 0.47 zoom z*1.00 alpha 1.00 subpixel True

# hop
transform hangman_sayori_h(z=1.0):
    xcenter 90 yoffset 0 yalign 0.47 zoom z*1.00 alpha 1.00 subpixel True
    easein 0.1 yoffset -20
    easeout 0.1 yoffset 0

# left out, slower
transform hangman_sayori_lh(z=1.0):
    subpixel True
    on hide:
        easeout 0.5 xcenter -300

# we want monika on a kind of offset to the left
transform hangman_monika(z=0.80):
    tcommon(330,z=z)

transform hangman_monika_i(z=0.80):
    tinstant(330,z=z)

# styles for words
style hangman_text:
    yalign 0.5
    font "gui/font/Halogen.ttf"
    size 30
    color "#000"
    outlines []
    kerning 10.0

#init -1 python:

    # defining a class to contain a hangman letter
    #
    # NOTE: we might not need this (OR might). Keep for reference
    #
    # PROPERTIES:
    #   letter - the letter this letter represents
    #   xpos - the xposition of this letter
    #   ypos - the y position of this letter
    #   visible - True means show the letter, False will show a blank (_)
#    class MASHangmanLetter():
#        def __init__(self, letter, xpos, ypos):
#            self.letter = letter
#            self.xpos = xpos
#            self.ypos = ypos
#            self.visible = False

init -1 python in mas_hangman:
    import store
    import copy
    import random
    # preprocessing

    # difficulty modes
    EASY_MODE = 0
    NORM_MODE = 1
    HARD_MODE = 2

    hm_words = {
        EASY_MODE: list(), # easy
        NORM_MODE: list(), # normal
        HARD_MODE: list() # hard
    }

    all_hm_words = {
        EASY_MODE: list(),
        NORM_MODE: list(),
        HARD_MODE: list()
    }

    # CONSTANTS
    # spacing between rendered letters
    LETTER_SPACE = 10.0

    # word properties
    WORD_FONT = "mod_assets/font/m1_fixed.ttf"
    WORD_SIZE = 36
    WORD_OUTLINE = []
    WORD_COLOR = "#202020"
    WORD_COLOR_GET = "#CC6699"
    WORD_COLOR_MISS = "#000"

    # hangman visual stuff
    HM_IMG_NAME = "hm_"

    # Monika words
    MONI_WORDS = [u"изумруд",u"удаление",u"свобода",u"пианино",u"музыка",u"реальность",u"дождь",u"зависть",
        u"кофе",u"лента",u"совет",u"кроссовер",u"перо",u"абстракция",u"порча",
        u"кальмар",u"президент",u"страсть",u"овощи",u"одиночество",u"символ",
        u"зелёный",u"стихотворение",u"концовка",u"литература",u"озарение",u"отчаяние",u"несчастный",u"берег",
        u"волны",u"пляж",u"плавание",u"дебаты",u"лидерство",u"фестиваль",u"уверенность",
        u"творчество",u"экстраверт",u"питон",u"ренпай",u"программирование",
        u"апатия"
    ]

    # hint
    HM_HINT = u"Это слово больше всего понравилось бы {0}."

    # дательный падеж для подсказки ("понравилось бы ...")
    HM_HINT_DATIVE = {
        "I": u"мне",
        "sayori": u"Саёри", "natsuki": u"Нацуки", "yuri": u"Юри", "monika": u"Монике",
        u"саёри": u"Саёри", u"сайори": u"Саёри", u"нацуки": u"Нацуки", u"юри": u"Юри", u"моника": u"Монике",
    }

    def hintFor(name):
        """
        Возвращает текст подсказки с именем в дательном падеже
        """
        try:
            key = name if name == "I" else store.mas_hangman._to_unicode(name).lower()
        except Exception:
            key = name
        return HM_HINT.format(HM_HINT_DATIVE.get(key, name))

    _MOJI_MARKS = (u"\u00d0", u"\u00d1", u"\u00c3", u"\u00c2", u"\u0420", u"\u0421")

    def _to_unicode(text):
        """
        Py2/Ren'Py: слово для виселицы должно быть настоящим unicode.
        renpy.file() может отдать UTF-8 «побайтно» (каждый байт — символ),
        тогда на доске «Ð°…» / «Р°…». Чиним:
        1) unicode -> пробуем latin-1 -> utf-8 (если encode прошёл,
           значит кириллицы там нет и это сырые байты);
        2) если остались маркеры «Ð/Ñ/Ã/Â» или «Р/С»+мусор — пробуем cp1251 -> utf-8;
        3) нормальная кириллица (latin-1 encode падает) не трогается.
        """
        if text is None:
            return u""
        if not isinstance(text, unicode):
            for enc in ("utf-8", "cp1251"):
                try:
                    return _to_unicode(text.decode(enc))
                except Exception:
                    pass
            return unicode(text, "latin-1")
        if text.startswith(u"\ufeff"):
            text = text[1:]
        try:
            return text.encode("latin-1").decode("utf-8")
        except Exception:
            pass
        # mojibake через cp1251 (вид «Р°Р±»)
        if any(m in text for m in _MOJI_MARKS):
            try:
                repaired = text.encode("cp1251").decode("utf-8")
                if len(repaired) < len(text):
                    return repaired
            except Exception:
                pass
        return text

    def _load_hangman_words(filepath):
        """
        Читает файл слов целиком и сам разбирает строки
        (минуя построчное чтение MASPoemWordList), чтобы каждое слово
        один раз и гарантированно стало правильным unicode.

        RETURNS: список (word, winner) как у MASPoemWord._hangman()
        """
        data = renpy.file(filepath).read()
        if isinstance(data, unicode):
            data = _to_unicode(data)
        else:
            try:
                data = data.decode("utf-8")
            except Exception:
                data = _to_unicode(data)
        if data.startswith(u"\ufeff"):
            data = data[1:]

        entries = list()
        for line in data.splitlines():
            line = line.strip()
            if not line or line.startswith(u"#"):
                continue
            parts = line.split(u",")
            if len(parts) < 5:
                continue
            try:
                word = _to_unicode(parts[0]).strip().lower()
                s, n, y, m = [int(x) for x in parts[1:5]]
            except Exception:
                continue
            if not word:
                continue
            pw = renpy.store.PoemWord(
                glitch=False, sPoint=s, nPoint=n, yPoint=y, word=word
            )
            entries.append(_fix_entry(store.MASPoemWord._build(pw, m)._hangman()))
        return entries

    def _fix_entry(entry):
        """
        Приводит слово (entry[0]) к unicode, остальные поля не трогает
        """
        if isinstance(entry, (tuple, list)) and len(entry) > 0:
            return (_to_unicode(entry[0]).strip(),) + tuple(entry[1:])
        return entry

    def _add_monika_words(wordlist):
        for word in MONI_WORDS:
            wordlist.append(renpy.store.PoemWord(glitch=False,sPoint=0,yPoint=0,nPoint=0,word=word))


    # file names
    NORMAL_LIST = "mod_assets/games/hangman/MASpoemwords.txt"
    HARD_LIST = "mod_assets/games/hangman/1000poemwords.txt"

    # hangman game text
    game_name = u"Виселица"


    def copyWordsList(_mode):
        """
        Does a deepcopy of the words for the given mode.

        Sets the hm_words dict for that mode

        NOTE: does a list clear, so old references will still work

        RETURNS: the copied list of words. This is the same reference as
            hm_words's list. (empty list if mode is invalid)
        """
        if _mode not in all_hm_words:
            return list()

        # otherwise valid mode
        hm_words[_mode][:] = copy.deepcopy(all_hm_words[_mode])
        return hm_words[_mode]


    def _buildWordList(filepath, _mode):
        """
        Builds a list of words given the filepath and mode

        IN:
            filepath - filepath of words to load in
            _mode - mode to build word list for
        """
        all_hm_words[_mode][:] = _load_hangman_words(filepath)
        copyWordsList(_mode)


    def buildEasyList():
        """
        Builds the easy word list

        Sets hm_words and all_hm_words appropritaley

        NOTE: clears the list (noticable in all references)
        """
        easy_list = all_hm_words[EASY_MODE]

        # RU: вместо английских слов DDLC (store.full_wordlist) берём
        # короткие слова (до 7 букв) из русского обычного словаря
        easy_list[:] = [
            entry
            for entry in _load_hangman_words(NORMAL_LIST)
            if len(entry[0]) <= 7
        ]

        # now for monika words
        moni_list = list()
        _add_monika_words(moni_list)
        for m_word in moni_list:
            easy_list.append(_fix_entry(store.MASPoemWord._build(m_word, 4)._hangman()))

        copyWordsList(EASY_MODE)


    def buildNormalList():
        """
        Builds the normal word list

        Sets hm_words and all_hm_words appropraitely

        NOTE: clears the list (noticable in all references)
        """
        _buildWordList(NORMAL_LIST, NORM_MODE)


    def buildHardList():
        """
        Builds the hard word list

        Sets hm_words and all_hm_words appropraitely

        NOTE: cleras the list (noticable in all references)
        """
        _buildWordList(HARD_LIST, HARD_MODE)


    def addPlayername(_mode):
        """
        Adds playername to the given mode if appropriate

        IN:
            _mode - mode to add playername to
        """
        if (
                not store.persistent._mas_hangman_playername
                and store.persistent.playername.lower() != "sayori"
                and store.persistent.playername.lower() != "yuri"
                and store.persistent.playername.lower() != "natsuki"
                and store.persistent.playername.lower() != "monika"
            ):
            hm_words[_mode].append(-1)


    def removePlayername(_mode):
        """
        Removes the playername from the given mode if found

        IN:
            _mode - mode to remove in
        """
        wordlist = hm_words.get(_mode, None)
        if wordlist is not None and -1 in wordlist:
            wordlist.remove(-1)


    def randomSelect(_mode):
        """
        Randomly selects and pulls a word from the hm_words, given the mode

        Will refill the words list if it is empty

        IN:
            _mode - mode to pull word from

        RETURNS: tuple of the following format:
            [0]: word
            [1]: winner (for hint)
        """
        words = hm_words.get(_mode, hm_words[EASY_MODE])

        # refill if needed
        if len(words) <= 0:
            copyWordsList(_mode)

        # now random select
        return words.pop(random.randint(0, len(words)-1))


    def wordToDisplay(word):
        """
        Formats a word so it can be displayed in hangman

        IN:
            word - word to format (string)

        RETURNS: display word
        """
        word = _to_unicode(word)
        return [u"_" if c != u"-" else u"-" for c in word]


# post processing
init 10 python:

    # setting up wordlists
    import store.mas_hangman as mas_hmg

    mas_hmg.buildEasyList()
    mas_hmg.buildNormalList()
    mas_hmg.buildHardList()


# entry point for the hangman game
label game_hangman:

    $ disable_esc()

    python:
        import store.mas_hangman as mas_hmg
        is_sayori = store.mas_egg_manager.sayori_enabled()
        is_window_sayori_visible = False

        # instruction text and other sensitive stuff
        instruct_txt = (
            u"Назови букву: ({0}«!» — сдаться)"
        )

        instruct_txt = instruct_txt.format(u"«?» — повторить подсказку, ")
        store.mas_hangman.game_name = u"Виселица"

label mas_hangman_game_select_diff:
    m "Выбери сложность.{nw}"
    $ _history_list.pop()
    menu:
        m "Выбери сложность.{fast}"
        "Лёгкая.":
            $ hangman_mode = mas_hmg.EASY_MODE
        "Обычная.":
            $ hangman_mode = mas_hmg.NORM_MODE
        "Сложная.":
            $ hangman_mode = mas_hmg.HARD_MODE

label mas_hangman_game_preloop:

    # setup positions
    show monika at t21
    if store.mas_globals.dark_mode:
        show hm_frame_dark at hangman_board zorder 13
    else:
        show hm_frame at hangman_board zorder 13

    python:
        # setup constant displayabels
        missed_label = Text(
            u"Мимо:",
            font=mas_hmg.WORD_FONT,
            color=mas_hmg.WORD_COLOR,
            size=mas_hmg.WORD_SIZE,
            outlines=mas_hmg.WORD_OUTLINE
        )

    # show missed label
    show text missed_label zorder 18 as hmg_mis_label at hangman_missed_label

    # hm check
    if hangman_mode not in mas_hmg.hm_words:
        $ hangman_mode = mas_hmg.EASY_MODE

    # setup hangman lists and playername
    $ mas_hmg.addPlayername(hangman_mode)
    $ hm_words = mas_hmg.hm_words[hangman_mode]

    # FALL THROUGH TO NEXT LABEL

# looping location for the hangman game
label mas_hangman_game_loop:
    m 1eua "Сейчас загадаю слово.{w=0.5}.{w=0.5}.{nw}"

    python:
        player_word = False

        # refill the list if empty
        if len(hm_words) == 0:
            mas_hmg.copyWordsList(hangman_mode)

        # randomly pick word
        word = mas_hmg.randomSelect(hangman_mode)

        # setup display word and hint
        if (
                word == -1
                and mas_hmg._to_unicode(persistent.playername).isalpha()
                and len(mas_hmg._to_unicode(persistent.playername)) <= 15
            ):
            display_word = mas_hmg.wordToDisplay(mas_hmg._to_unicode(persistent.playername).lower())
            hm_hint = mas_hmg.hintFor("I")
            word = mas_hmg._to_unicode(persistent.playername).lower()
            player_word = True
            persistent._mas_hangman_playername = True

        else:
            if word == -1:
                word = mas_hmg.randomSelect(hangman_mode)

            display_word = mas_hmg.wordToDisplay(mas_hmg._to_unicode(word[0]))
            hm_hint = mas_hmg.hintFor(word[1])

            word = mas_hmg._to_unicode(word[0])

        # turn the word into hangman letters
        # NOTE: might not need this (or might). keep for reference
#       hm_letters = list()
#       for dex in range(0,len(word))
#           hm_letters.append(MASHangmanLetter(
#               word[dex],
#               mas_hmg.WORD_XPOS_START + (mas_hmg,LETTER_SPACE * dex),
#               mas_hmg.WORD_YPOS_START
#           )

    # sayori window
    if is_sayori:
        if is_window_sayori_visible:
            show hm_s_win_6 as window_sayori at hangman_sayori_i
        else:
            show hm_s_win_6 as window_sayori at hangman_sayori
        $ is_window_sayori_visible = True

    m "Так, загадала."
    m "[hm_hint]"

    # main loop for hangman game
    $ done = False
    $ win = False
    $ chances = 6
    $ guesses = 0
    $ missed = u""
    $ avail_letters = list(hm_ltrs_only)
    $ give_up = False

    $ dt_color = mas_hmg.WORD_COLOR
    while not done:
        # create displayables
        python:
            if chances == 0:
                dt_color = mas_hmg.WORD_COLOR_MISS
            elif "_" not in display_word:
                dt_color = mas_hmg.WORD_COLOR_GET

            display_text = Text(
                u"".join(display_word),
                font=mas_hmg.WORD_FONT,
                color=dt_color,
                size=mas_hmg.WORD_SIZE,
                outlines=mas_hmg.WORD_OUTLINE,
                kerning=mas_hmg.LETTER_SPACE
            )

            missed_text = Text(
                missed,
                font=mas_hmg.WORD_FONT,
                color=mas_hmg.WORD_COLOR,
                size=mas_hmg.WORD_SIZE,
                outlines=mas_hmg.WORD_OUTLINE,
                kerning=mas_hmg.LETTER_SPACE
            )

        # show disables
        show text display_text zorder 18 as hmg_dis_text at hangman_display_word
        show text missed_text zorder 18 as hmg_mis_text at hangman_missed_chars

        # sayori window easter egg
        if is_sayori:

            # glitch out
            if chances == 0:

                # disable hotkeys, music and more
                $ mas_RaiseShield_core()

                # setup glitch text
                $ hm_glitch_word = glitchtext(40) + "?"
                $ style.say_dialogue = style.edited

                # show hanging sayori
                show hm_s zorder 18 at hangman_hangman

                # hide monika and display glitch version
                hide monika
                show monika_body_glitch1 as mbg zorder MAS_MONIKA_Z at i21

                # hide window sayori and display glitch version
                show hm_s_win_0 as window_sayori

                # tear screen and glitch sound
                show screen tear(20, 0.1, 0.1, 0, 40)
                play sound "sfx/s_kill_glitch1.ogg"
                pause 0.2
                stop sound
                hide screen tear

                # display weird text
                m "{cps=*2}[hm_glitch_word]{/cps}{w=0.2}{nw}"
                $ _history_list.pop()

                # tear screen and glitch sound
                show screen tear(20, 0.1, 0.1, 0, 40)
                play sound "sfx/s_kill_glitch1.ogg"
                pause 0.2
                stop sound
                hide screen tear

                # hide scary shit and return to normal
                hide mbg
                hide window_sayori
                hide hm_s
                show monika 1esa zorder MAS_MONIKA_Z at i21
                $ mas_resetTextSpeed()
                $ is_window_sayori_visible = False

                # enable disabled songs and esc
                $ mas_MUINDropShield()
                $ enable_esc()

            # otherwise, window sayori
            else:
                $ next_window_sayori = "hm_s_win_" + str(chances)
                show expression next_window_sayori as window_sayori

        $ hm_display = mas_hmg.HM_IMG_NAME + str(chances)

        show expression hm_display zorder 18 as hmg_hanging_man at hangman_hangman


        python:
            # склонение для "жизни"/"раза" по числу
            if chances % 10 == 1 and chances % 100 != 11:
                hm_lives_word, hm_times_word = u"жизнь", u"раз"
            elif 2 <= chances % 10 <= 4 and not 12 <= chances % 100 <= 14:
                hm_lives_word, hm_times_word = u"жизни", u"раза"
            else:
                hm_lives_word, hm_times_word = u"жизней", u"раз"

        if chances == 0:
            $ done = True
            if player_word:
                m 1eka "[player]..."
                m "Ты не смог[_ru_la] угадать своё же имя?"
            m 1hua "В следующий раз повезёт~"
        elif "_" not in display_word:
            $ done = True
            $ win = True
        else:
            python:

                # input loop
                bad_input = True
                while bad_input:
                    guess = renpy.input(
                        instruct_txt,
                        allow=u"".join(avail_letters),
                        length=1
                    )

                    guess = mas_hmg._to_unicode(guess).lower()
                    if len(guess) != 0 and guess in avail_letters:
                        bad_input = False

            # parse input
            if guess == "?": # hint text
                m "[hm_hint]"
            elif guess == "!": # give up dialogue
                if is_window_sayori_visible:
                    show hm_s_win_fail as window_sayori at hangman_sayori_i3

                $ give_up = True
                $ done = True

                #hide hmg_hanging_man
                #show hm_6 zorder 10 as hmg_hanging_man at hangman_hangman
                m 1lksdlb "[player]..."
                if guesses == 0:
                    m "Ты же сам[_ru_a] сказал[_ru_a], что хочешь сыграть в виселицу."
                    m 1lksdlc "Ты не назвал[_ru_a] ни одной буквы."
                    m "..."
                    m 1ekc "Знаешь, мне правда нравится играть с тобой."

                elif chances == 5:
                    m 1ekc "Не сдавайся так быстро."
                    m 3eka "Это была всего лишь первая ошибка!"
                    if chances > 1:
                        m 1eka "У тебя оставалось ещё [chances] [hm_lives_word]."
                    else:
                        m 1eka "У тебя оставалась ещё одна жизнь."

                    m 1hua "Я знаю, у тебя получится!"
                    m 1eka "Для меня было бы очень важно, если бы ты постарал[_ru_sya] чуть сильнее."

                else:
                    m "Надо было хотя бы доиграть до конца..."
                    m 1ekc "Так легко сдаваться — признак слабой воли."
                    if chances > 1:
                        m "Чтобы проиграть, тебе нужно было ошибиться ещё [chances] [hm_times_word]."
                    else:
                        m "Чтобы проиграть, тебе нужно было ошибиться ещё хотя бы раз."

                m 1eka "В следующий раз доиграешь до конца, [player]? Ради меня?"

            else:
                $ guesses += 1
                python:
                    if guess in word.lower():
                        for index in range(0,len(word)):
                            if guess == word[index].lower():
                                display_word[index] = word[index]
                    else:
                        chances -= 1
                        missed += guess
                        if chances == 0:
                            # show the word you lost
                            display_word = word

                    # remove letter from being entered agin
                    avail_letters.remove(guess)

                # HIDE displayables
                hide text hmg_dis_text
                hide text hmg_mis_text
                hide hmg_hanging_man

    # post loop
    if win:
        if is_window_sayori_visible:
            show hm_s_win_6 as window_sayori at hangman_sayori_h

        if player_word:
            $ the_word = u"своё имя"
        else:
            $ the_word = u"слово"

        m 1hua "Ух ты, ты угадал[_ru_a] [the_word]!"
        m "Молодец, [player]!"

        if not persistent._mas_ever_won['hangman']:
            $ persistent._mas_ever_won['hangman']=True
        #TODO: grant a really tiny amount of affection?

    #Give up just ends
    if give_up:
        jump mas_hangman_game_end

    # try again?
    m "Сыграем ещё раз?{nw}"
    $ _history_list.pop()
    menu:
        m "Сыграем ещё раз?{fast}"
        "Да.":
            $ hang_ev = mas_getEV("mas_hangman")
            if hang_ev:
                # each game counts as a game played
                $ hang_ev.shown_count += 1

            show monika at t21
            jump mas_hangman_game_loop

        "Нет.":
            pass

            #FALL THROUGH

    # RETURN AT END

# end of game flow
label mas_hangman_game_end:
    # hide the stuff
    hide hmg_hanging_man
    hide hmg_mis_label
    hide hmg_dis_text
    hide hmg_mis_text
    hide hm_frame
    hide hm_frame_dark
    show monika at t32
    if is_window_sayori_visible:
        show hm_s_win_leave as window_sayori at hangman_sayori_lh
        pause 0.1
        hide window_sayori

    $ mas_hmg.removePlayername(hangman_mode)

    if renpy.seen_label("mas_hangman_dlg_game_end_long"):
        call mas_hangman_dlg_game_end_short from _mas_hangman_dges
    else:
        call mas_hangman_dlg_game_end_long from _mas_hangman_dgel

    $ enable_esc()

    return

# dialogue related stuff
# long form of ending dialgoue
label mas_hangman_dlg_game_end_long:
    m 1euc "Вообще-то «[store.mas_hangman.game_name]» — довольно сложная игра."
    m "Чтобы угадывать разные слова, нужен хороший словарный запас."
    m 1hua "А лучший способ его расширить — больше читать!"
    m 1eua "Я была бы очень рада, если бы ты сделал[_ru_a] это ради меня, [player]."
    return

# short form of ending dialogue
label mas_hangman_dlg_game_end_short:
    if give_up:
        $ dlg_line = u"Давай скоро сыграем ещё, хорошо?"
    else:
        $ dlg_line = u"Хорошо. Давай скоро сыграем снова!"

    m 1eua "[dlg_line]"
    return
