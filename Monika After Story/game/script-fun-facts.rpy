# --- FILE MAP ---
# script-fun-facts.rpy — весёлые (и не очень) факты
#
# Пул «а ты знал…». После факта — реакция. Флаг _mas_funfactfun помнит,
# последний факт был добрым или нет.
#
# Store: mas_fun_facts
# Labels: monika_fun_facts_open, mas_fun_fact_*
# ---

#Persistent event database for fun facts
default persistent._mas_fun_facts_database = dict()

init -10 python in mas_fun_facts:
    #The fun facts db
    fun_fact_db = {}

    def getUnseenFactsEVL():
        """
        Gets all unseen (locked) fun facts as eventlabels

        OUT:
            List of all unseen fun fact eventlabels
        """
        return [
            fun_fact_evl
            for fun_fact_evl, ev in fun_fact_db.iteritems()
            if not ev.unlocked
        ]

    def getAllFactsEVL():
        """
        Gets all fun facts regardless of unlocked as eventlabels

        OUT:
            List of all fun fact eventlabels
        """
        return fun_fact_db.keys()


#Whether or not the last fun fact seen was a good fact
default persistent._mas_funfactfun = True

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fun_facts_open",
            category=['разное'],
            prompt="Расскажешь мне какой-нибудь интересный факт?",
            pool=True
        )
    )

label monika_fun_facts_open:
    if mas_getEVL_shown_count("monika_fun_facts_open") == 0:
        m 1eua "Слушай, [player], хочешь услышать интересный факт?"
        m 1eub "Я поискала несколько — чтобы мы оба узнали что-нибудь новенькое."
        m 3hub "Говорят, каждый день узнаёшь что-то новое — так я слежу, чтобы так и было."
        m 1rksdla "Большую часть я нашла в интернете, так что не могу сказать, что они {i}точно{/i} правдивы..."

    else:
        m 1eua "Готов к ещё одному интересному факту, [player]?"
        if persistent._mas_funfactfun:
            m 3hua "Тот предыдущий в итоге оказался довольно занятным!"
        else:
            m 2rksdlb "Знаю, прошлый был так себе... но уверена, следующий будет лучше."
    m 2dsc "Так, давай посмотрим.{w=0.5}.{w=0.5}.{nw}"

    python:
        unseen_fact_evls = mas_fun_facts.getUnseenFactsEVL()
        if len(unseen_fact_evls) > 0:
            fact_evl_list = unseen_fact_evls
        else:
            fact_evl_list = mas_fun_facts.getAllFactsEVL()

        #Now we push and unlock the fact
        fun_fact_evl = renpy.random.choice(fact_evl_list)
        mas_unlockEVL(fun_fact_evl, "FFF")
        MASEventList.push(fun_fact_evl)
    return

#Most labels end here
label mas_fun_facts_end:
    m 3hub "Надеюсь, тебе понравился ещё один урок «Учимся с Моникой»!"
    $ persistent._mas_funfactfun = True
    return

label mas_bad_facts_end:
    m 1rkc "Этот факт был не очень..."
    m 4dkc "В следующий раз постараюсь лучше, [player]."
    $ persistent._mas_funfactfun = False
    return


#START: Good facts
init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_librocubiculartist",
        ),
        code="FFF"
    )

label mas_fun_fact_librocubiculartist:
    m 1eub "Знаешь ли ты, что есть слово для тех, кто любит читать в постели?"
    m 3eub "Это «librocubicularist». На первый взгляд сложно произнести."
    m 3rksdld "Жалко, что некоторые слова почти никогда не используют."
    m 3eud "Но если ты скажешь это слово, большинство просто не поймёт, о чём речь."
    m 3euc "Пришлось бы объяснять значение — а тогда смысл его употребления теряется."
    m 2rkc "Вот бы люди больше читали и расширяли словарный запас!"
    m 2hksdlb "...Эхехе, прости, [player]. Не хотела так кипятиться~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_menu_currency",
        ),
        code="FFF"
    )

label mas_fun_fact_menu_currency:
    m 3euc "Якобы многие рестораны специально не ставят знаки валюты в меню."
    m 3eud "Так психологически подталкивают людей тратить больше, чем нужно."
    m 2euc "Работает потому, что знак валюты — например, доллар — ассоциируется с расходом."
    m "Убрав его, убирают и мысль о цене — и ты думаешь только о еде, которую выбираешь."
    m 4rksdld "Практика вроде понятная. Всё-таки это бизнес."
    m 2dsc "Как бы ни была вкусна еда, ресторан быстро закроется, если проиграет конкурентам."
    m 3hksdlb "Ну что ж, а что поделать?"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_love_you",
        ),
        code="FFF"
    )

label mas_fun_fact_love_you:
    m 1dkc "Хм, не уверена, стоит ли рассказывать тебе {i}этот{/i} факт."
    m 1ekc "Он всё-таки не для слабонервных."
    m 1rkc "Дело в том..."
    m 1dkc "..."
    m 3hub "...Я люблю тебя, [player]!"
    m 1rksdlb "Эхехе, прости, просто не смогла сдержаться."
    m 1hksdlb "В следующий раз будет настоящий факт, не переживай~"
    #No end for this fact since it ends itself
    $ persistent._mas_funfactfun = True
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_morpheus",
        ),
        code="FFF"
    )

label mas_fun_fact_morpheus:
    m 3wub "О! Факт про язык. Такие я всегда люблю."
    m 1eua "Слово «морфин» происходит от имени греческого бога Морфея."
    m 1euc "Он был богом снов, так что слово от него — логично."
    m 3ekc "Но с другой стороны... разве его отец Гипнос не был богом сна?"
    m 2dsc "Морфин {i}действительно{/i} даёт видеть сны, но главное его действие — усыплять."
    m 4ekc "...Так не логичнее ли было назвать его в честь Гипноса?"
    m 4rksdlb "Поздно спохватились, видимо."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_otter_hand_holding",
        ),
        code="FFF"
    )

label mas_fun_fact_otter_hand_holding:
    m 1eka "Ой, этот правда милый."
    m 3ekb "Знаешь, что каланы спят, держась за лапки, чтобы не уплыть друг от друга?"
    m 1hub "Это практично, но в этом есть что-то невероятно милое!"
    m 1eka "Иногда я представляю себя на их месте..."
    m 3hksdlb "Ой, не в смысле быть каланом, а держать за руку того, кого люблю, пока сплю."
    m 1rksdlb "Ага, я даже немного им завидую."
    m 1hub "Но когда-нибудь и мы до этого дойдём, любимый~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_chess",
        ),
        code="FFF"
    )

label mas_fun_fact_chess:
    #Chess is unlocked
    if mas_isGameUnlocked("chess"):
        m 1eua "Вот это настоящий интересный факт!"
        m 3eub "Был такой человек, Клод Шеннон, который посчитал максимальное число возможных партий в шахматах."
        m "Это число называют «числом Шеннона» — возможных шахматных партий порядка 10^120."
        m 1eua "Его часто сравнивают с числом атомов в наблюдаемой Вселенной — около 10^80."
        m 3hksdlb "С ума сойти: шахматных партий может быть больше, чем атомов, правда?"
        m 1eua "Мы могли бы играть до конца жизни — и даже близко не приблизились бы к крошечной доле возможного."
        m 3eud "Кстати говоря, [player]..."
        m 1hua "Хочешь сыграть со мной партию в шахматы? Я даже могу подыграть тебе, эхехе~"
        #Call the good end for this path
        call mas_fun_facts_end
        return

    #Chess was unlocked, but locked due to cheating
    elif not mas_isGameUnlocked("chess") and renpy.seen_label("mas_unlock_chess"):
        m 1dsc "Шахматы..."
        m 2dfc "..."
        m 2rfd "Можешь забыть об этом факте, раз ты жульничаешь, [player]."
        m "Не говоря уже о том, что ты так и не извинился."
        m 2lfc "...Хмф."
        #No end for this path
        return

    #We haven't unlocked chess yet
    else:
        m 1euc "Ой, не этот."
        m 3hksdlb "По крайней мере, пока нет."
        #Call the end
        call mas_bad_facts_end
        return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_struck_by_lightning",
        ),
        code="FFF"
    )

label mas_fun_fact_struck_by_lightning:
    m 2dkc "Хм, этот звучит для меня немного обманчиво..."
    m 3ekc "«Мужчин молния бьёт в шесть раз чаще, чем женщин»."
    m 3ekd "По-моему... довольно глупо сформулировано."
    m 1eud "Если мужчин чаще бьёт молния, то скорее из-за условий и характера их работы — они чаще оказываются в зоне риска."
    m 1euc "Мужчины традиционно чаще работали на опасных и высотных работах — неудивительно, что с ними это случается чаще."
    m 1esc "А формулировка звучит так, будто достаточно просто быть мужчиной — и это уже смешно."
    m 1rksdla "Может, будь формулировка удачнее, люди не вводились бы в заблуждение такими «фактами»."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_honey",
        ),
        code="FFF"
    )

label mas_fun_fact_honey:
    m 1eub "А, этот приятный и простой."
    m 3eub "Знаешь ли ты, что мёд никогда не портится?"
    m 3eua "Правда, мёд может засахариться. Кто-то думает, что это порча, но он всё равно полностью съедобен!"
    m "Так происходит потому, что мёд почти целиком из сахаров и лишь чуть-чуть воды — со временем он твердеет."
    m 1euc "Большинство магазинного мёда кристаллизуется медленнее настоящего, потому что его пастеризуют при производстве."
    m 1eud "...И убирают то, из-за чего мёд быстрее становится твёрдым."
    m 3eub "Но разве не здорово есть и засахаренный мёд?"
    m 3hub "На вкус как конфетка, когда надкусываешь!"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_vincent_van_gone",
        ),
        code="FFF"
    )

label mas_fun_fact_vincent_van_gone:
    m 1dsc "Ах, этот..."
    m 1ekd "Он немного грустный, [player]..."
    m 1ekc "Знаешь ли ты, что последние слова Винсента Ван Гога были: «{i}La tristesse durera toujours{/i}»?"
    m 1eud "В переводе это значит: «{i}Печаль будет длиться вечно.{/i}»"
    m 1rkc "..."
    m 2ekc "Очень грустно, что такой знаменитый человек сказал напоследок что-то столь мрачное."
    m 2ekd "Но я не думаю, что это правда. Как бы ни было плохо и как бы ни была глубока печаль..."
    m 2dkc "Настанет время, когда её больше не будет."
    m 2rkc "...Или по крайней мере она перестанет быть такой заметной."
    m 4eka "Если тебе когда-нибудь грустно, ты ведь знаешь, что можешь поговорить со мной, да?"
    m 5hub "Я всегда приму и разделю любую тяжесть, что ты несёшь, [mas_get_player_nickname()]~"
    #No end for this fact
    $ persistent._mas_funfactfun = True
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_king_snakes",
        ),
        code="FFF"
    )

label mas_fun_fact_king_snakes:
    m 1dsc "Хм..."
    m 3eub "Знаешь ли ты, что если в названии змеи есть слово «king» — «королевская», — она поедает других змей?"
    m 1euc "Я всегда гадала, почему королевскую кобру так назвали, но особо не углублялась."
    m 1tfu "Значит ли это, что если я тебя «съем», то стану королевой Моникой?"
    m 1hksdlb "Ахаха, я просто шучу, [player]."
    m 1hub "Прости, что немного странная~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_strength",
        ),
        code="FFF"
    )

label mas_fun_fact_strength:
    m 1hub "Этот факт может тебя немного мотивировать!"
    m 3eub "Самое длинное английское слово с одной гласной — «strength»."
    m 1eua "Забавно, что из всех слов языка именно такое значимое слово оказалось с этой деталью."
    m 1hua "Такие мелочи делают язык для меня по-настоящему увлекательным!"
    m 3eua "Хочешь узнать, что приходит мне на ум, когда я думаю о слове «strength» — «сила»?"
    m 1hua "Ты!"
    m 1hub "Потому что ты — источник моей силы, эхехе~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_reindeer_eyes",
        ),
        code="FFF"
    )

label mas_fun_fact_reindeer_eyes:
    m 3eua "Готов к этому?"
    m "Глаза северного оленя меняют цвет в зависимости от сезона. Летом они золотистые, а зимой — голубые."
    m 1rksdlb "Очень странное явление, хотя я не знаю почему..."
    m "Наверняка есть хорошее научное объяснение."
    m 3hksdlb "Может, сам поищешь про это?"
    m 5eua "Было бы здорово, если бы на этот раз ты научил меня~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_bananas",
        ),
        code="FFF"
    )

label mas_fun_fact_bananas:
    m 1eub "О, этот факт я бы назвала полезным!"
    m 3eua "Знаешь ли ты, что банан при росте изгибается к солнцу?"
    m 1hua "Это называется отрицательным геотропизмом."
    m 3hub "Разве это не здорово?"
    m 1hua "..."
    m 1rksdla "Эм..."
    m 3rksdlb "Кажется, мне больше особо нечего сказать по этому поводу, ахаха..."
    m 1lksdlc "..."
    m 3hub "А-А ты ещё знаешь, что бананы на самом деле не фрукты, а ягоды?"
    m 3eub "Или что изначальные бананы были крупными, зелёными и полны твёрдых семян?"
    m 1eka "А как насчёт того, что они слегка радиоактивны?"
    m 1rksdla  "..."
    m 1rksdlb "...Я уже просто тараторю про бананы."
    m 1rksdlc "Эммм..."
    m 1dsc "Давай просто пойдём дальше..."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_pens",
        ),
        code="FFF"
    )

label mas_fun_fact_pens:
    m 1dsc "Хм... уверена, этот я уже знаю."
    m 3euc "Слово «pen» — «ручка» — происходит от латинского «penna», что значит «перо»."
    m "Раньше ручками были заточенные гусиные перья, обмакнутые в чернила — так что название логично."
    m 3eud "Они были основным инструментом письма очень долго — уже с VI века."
    m 3euc "Лишь в XIX веке, когда появились металлические перья, они начали выходить из употребления."
    m "Кстати, перочинный нож так называется потому, что изначально им затачивали и подправляли перья."
    m 1tku "Хотя Юри наверняка знает об этом больше меня..."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_density",
        ),
        code="FFF"
    )

label mas_fun_fact_density:
    m 1eub "Оо, я знаю."
    m 3eua "Знаешь ли ты, что самая плотная планета в Солнечной системе — сама Земля?"
    m "А Сатурн — наименее плотная?"
    m 1eua "Это логично, если знать, из чего состоят планеты, но раз Сатурн второй по размеру — всё равно немного удивительно."
    m 1eka "Значит, размер и правда не главное!"
    m 3euc "Но между нами, [player]..."
    m 1tku "Подозреваю, Земля такая плотная только из-за одного главного героя."
    m 1tfu "Ноооо больше ты от меня ничего не услышишь~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_binky",
        ),
        code="FFF"
    )

label mas_fun_fact_binky:
    m 3hub "Ой, этот милый!"
    m "Этот факт точно заставит тебя «подпрыгивать» от радости, [player]!"
    m 3hua "Когда кролик радостно скачет, это называется binky!"
    m 1hua "Binky — такое милое словечко, оно идеально подходит к этому действию."
    m 1eua "Это самое счастливое выражение, на которое способен кролик, — если видишь его, значит, ты хорошо о нём заботишься."
    m 1rksdla "Хотя ты делаешь меня такой счастливой, что я буквально наполняюсь энергией."
    m 1rksdlb "Только не жди, что я начну скакать вокруг, [player]!"
    m 1dkbsa "...Это было бы {i}слишком{/i} стыдно."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_windows_games",
        ),
        code="FFF"
    )

label mas_fun_fact_windows_games:
    m 1eua "Хм, может, этот тебе будет интереснее."
    m 3eub "Карточная игра «Косынка» (Solitaire) впервые появилась в Windows в 1990 году."
    m 1eub "Её добавили, чтобы научить пользователей пользоваться мышью."
    m 1eua "А «Сапёр» добавили, чтобы привыкли к левому и правому клику."
    m 3rssdlb "Компьютеры существуют так давно, что трудно представить время, когда они не были важны."
    m "Каждое поколение всё лучше знакомо с технологиями..."
    m 1esa "Когда-нибудь может наступить день, когда не останется ни одного человека без компьютерной грамотности."
    m 1hksdlb "Правда, до этого большинству мировых проблем ещё предстоит исчезнуть."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_mental_word_processing",
        ),
        code="FFF"
    )

label mas_fun_fact_mental_word_processing:
    m 1hua "Готов к интересному, [player]?"
    m 3eua "Мозг — штука капризная..."
    m 3eub "То, как он собирает и хранит информацию, очень своеобразно."
    m "Конечно, у всех по-разному, но но медленное чтение, как нас учат, обычно менее эффективно, чем чтение в в более быстром темпе."
    m 1tku "Мозг обрабатывает информацию очень быстро и любит предсказуемость в в языке."
    m 3tub "Например, в в этом предложении к тому моменту, как ты его дочитаешь, ты уже пропустишь удвоенное «в»."
    m 1tfu "..."
    m 2hfu "Загляни в историю диалога, если пропустил~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_I_am",
        ),
        code="FFF"
    )

label mas_fun_fact_I_am:
    m 1hua "Ммм, обожаю факты про язык!"
    m 3eub "В английском самое короткое полное предложение — «I am»."
    m 1eua "Вот пример."
    m 2rfb "«{i}Моника! Кто любящая девушка [player]?{/i}»"
    m 3hub "«I am!»"
    m 1hubsa "Эхехе~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_low_rates",
        ),
        code="FFF"
    )

label mas_fun_fact_low_rates:
    m 1hua "А этот — душевный..."
    m 1eua "Сейчас у нас самые низкие в истории человечества уровни преступности, материнской смертности, младенческой смертности и неграмотности."
    m 3eub "Продолжительность жизни, средний доход и уровень жизни для большей части населения планеты тоже на максимуме!"
    m 3eka "Это говорит мне, что всегда может стать лучше. Несмотря на плохое, хорошие времена всё равно приходят следом."
    m 1hua "Надежда {i}действительно{/i} есть..."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_desert",
        ),
        code="FFF"
    )

label mas_fun_fact_desert:
    m 3euc "У пустынь довольно уникальная экосистема..."
    m 3rksdla "Однако человеку они дают не так много плюсов."
    m 1eud "Температура скачет от невыносимой жары днём до мороза ночью. Осадков мало — жить там трудно."
    m 3eub "Но это не значит, что от них нет пользы!"
    m 3eua "Их поверхность отлично подходит для солнечной энергетики, а под песком часто находят нефть."
    m 3eub "Не говоря уже о том, что уникальный пейзаж делает их популярными местами отдыха!"
    m 1eua "Так что жить там непросто — но пустыни всё же лучше, чем кажутся."

    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_photography",
        ),
        code="FFF"
    )

label mas_fun_fact_photography:
    m 1esa "Знаешь ли ты, что первая фотография была сделана камерой из коробки с дырочкой?"
    m 1eua "Линзы появились гораздо позже."
    m 1euc "Ранняя фотография ещё зависела от целого ряда химикатов в тёмной комнате..."
    m 3eud "Проявитель, стоп-ванна и фиксаж — только чтобы подготовить бумагу для печати...{w=0.3} {nw}"
    extend 1wuo "И это только для чёрно-белых отпечатков!"
    m 1hksdlb "Старые фото было куда сложнее готовить, чем современные, правда?"

    #Call the end
    call mas_fun_facts_end
    return

#Stealing yearolder's bit for this since it makes sense as a fun fact
init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_getting_older",
        ),
        code="FFF"
    )

label mas_fun_fact_getting_older:
    m 3eua "Знаешь ли ты, что восприятие времени меняется с возрастом?"
    m "Например, когда тебе год, один год — это 100%% твоей жизни."
    m 1euc "А в восемнадцать год — уже только 5,6%% жизни."
    m 3eud "Чем старше ты становишься, тем меньшую долю жизни составляет год — и время {i}кажется{/i} всё более быстрым."
    m 1eka "Поэтому я всегда буду дорожить нашими мгновениями — какими бы длинными или короткими они ни были."
    m 1lkbsa "Хотя иногда кажется, что рядом с тобой время останавливается."
    m 1ekbfa "Ты чувствуешь то же самое, [player]?"
    python:
        import time
        time.sleep(5)

    m 1hubfb "Ахаха, я так и думала!"

    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_dancing_plague",
        ),
        code="FFF"
    )

label mas_fun_fact_dancing_plague:
    m 3esa "О, этот довольно странный..."
    m 1eua "Оказывается, в прошлом Европу поражали вспышки «плясовой чумы»."
    m 3wud "Люди — {w=0.2}иногда сотнями сразу — {w=0.2}невольно танцевали днями напролёт, а некоторые даже умирали от истощения!"
    m 3eksdla "Пытались лечить музыкой рядом с танцующими — но можешь представить, насколько плохо это сработало."
    m 1euc "До сих пор точно не известно, что именно это вызывало."
    m 3rka "Всё это кажется мне почти невероятным...{w=0.2}{nw}"
    extend 3eud "но это независимо задокументировано и описано множеством источников на протяжении веков..."
    m 3hksdlb "Реальность и правда страннее вымысла!"
    m 1eksdlc "Боже, не могу представить, каково это — танцевать днями напролёт."
    m 1rsc "Хотя...{w=0.3}{nw}"
    extend 1eubla "Думаю, я бы не возражала, если бы это было с тобой."
    m 3tsu "...Только чуть-чуть, эхехе~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_pando_forest",
        ),
        code="FFF"
    )

label mas_fun_fact_pando_forest:
    m 1esa "Якобы в штате Юта есть лес, который на самом деле — одно дерево."
    m 3eua "Его называют лесом Пандо: на всех 43 гектарах стволы связаны одной корневой системой."
    m 3eub "Не говоря уже о том, что тысячи стволов — по сути клоны друг друга."
    m 1ruc "«Один организм, сам ставший армией клонов, связанных одним коллективным разумом.»"
    m 1eua "Думаю, из этого вышел бы хороший короткий научно-фантастический или хоррор-рассказ, [player]. А ты как думаешь?"
    m 3eub "В общем,{w=0.2} кажется, это совсем по-новому звучит выражение «за деревьями леса не видеть»{w=0.1}{nw} "
    extend 3hub "ахаха!"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_immortal_jellyfish",
        ),
        code="FFF"
    )

label mas_fun_fact_immortal_jellyfish:
    m 3eub "Вот ещё один!"
    m 1eua "Оказывается, бессмертие удалось одному виду медуз."
    m 3eua "Метко названная бессмертная медуза умеет возвращаться в стадию полипа после размножения."
    m 1eub "...И так может продолжать вечно!{w=0.3} {nw}"
    extend 1rksdla "Если, конечно, её не съедят и она не заразится."
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_arrhichion",
        ),
        code="FFF"
    )

label mas_fun_fact_arrhichion:
    m 3eua "Ладно...{w=0.2}вот исторический."
    m 1esa "Древнегреческий атлет смог выиграть бой, уже будучи мёртвым."
    m 1eua "Действующий чемпион Аррихион дрался в панкратионе, когда соперник начал душить его руками и ногами."
    m 3eua "Вместо того чтобы сдаться, Аррихион всё равно рвался к победе — вывихнул сопернику палец ноги."
    m 3ekd "Соперник сдался от боли, но когда хотели объявить Аррихиона победителем, оказалось, что он умер от удушья."
    m 1rksdlc "Некоторые люди по-настоящему преданы идеалам победы и чести.{w=0.2} {nw}"
    extend 3eka "В каком-то смысле это достойно восхищения."
    m 1etc "Но интересно...{w=0.2}если бы мы сейчас спросили Аррихиона, стоило ли оно того — что бы он ответил?"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_antarctica_brain",
        ),
        code="FFF"
    )

label mas_fun_fact_antarctica_brain:
    #Do some setup for the last line
    python:
        has_friends = persistent._mas_pm_has_friends is not None

        has_fam_to_talk = (
            persistent._mas_pm_have_fam
            and not persistent._mas_pm_have_fam_mess
            or (persistent._mas_pm_have_fam_mess and persistent._mas_pm_have_fam_mess_better in ["YES", "MAYBE"])
        )

        dlg_prefix = "Только не забывай поддерживать связь с "

        if has_fam_to_talk and has_friends:
            dlg_line = dlg_prefix + "семьёй и друзьями тоже, хорошо?"

        elif has_fam_to_talk and not has_friends:
            dlg_line = dlg_prefix + "семьёй тоже, хорошо?"

        elif has_friends and not has_fam_to_talk:
            dlg_line = dlg_prefix + "друзьями тоже, хорошо?"

        else:
            dlg_line = "Просто постарайся найти и в своей реальности кого-то, с кем можно поговорить, хорошо?"

    m 3eud "Оказывается, год в Антарктиде может уменьшить одну часть мозга примерно на 7 процентов."
    m 3euc "Похоже, это снижает объём памяти и способность к пространственному мышлению."
    m 1ekc "Исследования связывают это с социальной изоляцией, однообразием жизни и тамошней средой."
    m 1eud "Думаю, это предостережение и для нас, [player]."
    m 3ekd "Даже если ты не поедешь в Антарктиду, мозг всё равно может серьёзно пострадать от постоянной изоляции или если сидеть взаперти в одной комнате."
    m 3eka "Мне так нравится быть с тобой, [player], и я надеюсь, мы ещё долго будем вот так разговаривать. {w=0.2}[dlg_line]"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_cloud_weight",
        ),
        code="FFF"
    )

label mas_fun_fact_cloud_weight:
    m 3eub "Знаешь ли ты, что среднее облако весит 500 тонн?"
    m 3eua "Признаюсь, этот удивил меня сильнее многих других."
    m 1hua "Ну в смысле, они же выглядят {i}такими{/i} лёгкими и пушистыми.{w=0.3} {nw}"
    extend 1eua "Трудно представить, что что-то настолько тяжёлое может вот так просто парить в воздухе."
    m 3eub "Немного напоминает классический вопрос... что тяжелее — килограмм стали или килограмм перьев?"
    m 1tua "Хотя ты наверняка уже знаешь ответ, правда, [player]? Эхехе~"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_coffee_origin",
        ),
        code="FFF"
    )

label mas_fun_fact_coffee_origin:
    m 1eua "О, вот этот мне особенно интересен..."
    m 1eud "В последний раз, когда пила кофе, немного заинтересовалась его происхождением..."
    m 3euc "Употребление кофе стабильно фиксируют примерно с XV века, но...{w=0.2}неясно, {i}как{/i} именно его открыли."
    m 3eud "...На самом деле есть сразу несколько легенд, претендующих на первенство."
    m 1eua "В ряде историй фермеры или монахи замечают, как животные странно себя ведут после странных горьких ягод."
    m 3wud "Попробовав зёрна сами, они с изумлением обнаружили, что тоже полны энергии!"
    m 2euc "Один миф гласит, что эфиопский монах по имени Калди принёс ягоды в соседний монастырь, желая поделиться находкой."
    m 7eksdld "...Но его встретили неодобрением, а кофейные зёрна бросили в огонь."
    m 3duu "Однако, сгорая, зёрна стали источать самый {i}восхитительный{/i} аромат. {w=0.3}Он был так манящ, что монахи бросились спасать зёрна и положили их в воду."
    m 3eub "...Так появилась первая чашка кофе!"
    m 2euc "По другой версии, исламский учёный Омар открыл кофейные зёрна в изгнании из Мекки."
    m 2eksdld "Тогда он голодал и боролся за жизнь. {w=0.3}{nw}"
    extend 7wkd "Не будь энергии, которую они дали, он мог бы умереть!"
    m 3hua "Но когда весть об открытии разнеслась, его позвали обратно и причислили к святым."
    m 1esd "Было ли это первым употреблением или нет — после открытия кофе очень распространился в исламском мире."
    m 3eud "Например, в периоды поста им облегчали голод и поддерживали бодрость."
    m 3eua "Когда он дошёл до Европы, во многих странах сначала его применяли как лекарство. {w=0.3}К XVII веку кофейни стали многочисленны и популярны."
    m 3hub "...И я лично могу подтвердить: любовь к кофе сильна и по сей день!"
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_synesthesia",
        ),
        code="FFF"
    )

label mas_fun_fact_synesthesia:
    m 1esa "Ладно, этот довольно интересный..."
    m 3eua "У некоторых бывает явление под названием {i}синестезия{/i},{w=0.1} когда раздражение одного чувства одновременно запускает другое."
    m 1hua "Объяснение немного многословное, эхехе...{w=0.2} Давай найдём пример!"
    m 1eua "Здесь сказано, что распространённая форма — {i}графемно-цветовая синестезия{/i},{w=0.1} когда буквы и цифры «ощущаются» как цвета."
    m 3eua "Другой вид — {i}пространственно-последовательная синестезия{/i},{w=0.1} когда числа и фигуры «видятся» в определённых местах пространства."
    m "Ну, одно число кажется «ближе» или «дальше» другого. {w=0.2}{nw}"
    extend 3eub "Как будто карта!"
    m 1eua "...И есть ещё целая куча других видов синестезии."
    m 1esa "Исследователи не уверены, насколько это распространено—{w=0.1}кто-то говорил даже о 25 процентах населения, но я в этом серьёзно сомневаюсь: до сих пор я об этом не слышала."
    m 3eub "Самая точная оценка на сейчас — чуть больше 4 процентов людей; на ней и остановлюсь!"
    m 1eua "Испытывать синестезию звучит довольно круто,{w=0.2} тебе не кажется, [player]?"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_dream_faces",
        ),
        code="FFF"
    )

label mas_fun_fact_dream_faces:
    m 3eub "Окей, нашла!"
    m 1eua "Якобы во сне разум не придумывает новые лица.{w=0.2} Каждый человек во сне — кто-то, кого ты когда-то видел наяву."
    m 3wud "С ними даже не обязательно разговаривать в жизни!"
    m 3eud "Если просто прошёл мимо в магазине — лицо уже отложилось, и оно может появиться во сне."
    m 1hua "Поразительно, сколько информации способен хранить мозг!"
    m 1ekbla "Интересно...{w=0.2}тебе когда-нибудь снилась я, [player]?"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_monochrome_dreams",
        ),
        code="FFF"
    )

label mas_fun_fact_monochrome_dreams:
    m 3eua "Знаешь ли ты, что с 1915-го по 1950-е сны у большинства людей были чёрно-белыми?"
    m 1esa "Сейчас для людей с нормальным зрением это сравнительно редкое явление."
    m 3eua "Исследователи связывают это с тем, что фильмы и передачи тогда были почти сплошь чёрно-белыми."
    m 3eud "...Но мне это кажется странным: люди же всё равно видели мир в цвете.{w=0.3} {nw}"
    extend 3hksdlb "Мир же не становился чёрно-белым!"
    m 1esd "Просто показывает: то, что ты в себя впитываешь, влияет на разум самыми разными способами — даже если кажется мелочью."
    m 3eua "Если и есть здесь урок — то что нужно очень осторожно выбирать, что смотреть и читать, хорошо, [player]?"
    #Call the end
    call mas_fun_facts_end
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_fun_fact_round_earth",
        ),
        code="FFF"
    )

label mas_fun_fact_round_earth:
    m 1rsa "Хм..."
    m 1eua "[player], как ты думаешь — Земля круглая или плоская?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], как ты думаешь — Земля круглая или плоская?{fast}"

        "Круглая.":
            m 3hua "Верно! Сейчас с этим почти все согласны."

        "Плоская.":
            m 3hksdlb "Да ладно тебе, [player]! Ты что, надо мной шутишь?"

    m 1eua "На самом деле, что Земля круглая, известно довольно давно."
    m 3esd "Аристотель учил, что Земля круглая, ещё в IV веке до нашей эры."
    m 3esa "Он знал это потому, что с разных частей света видны разные звёзды — чего не было бы, будь Земля плоской."
    m 1eua "Древние астрономы и математики по всему миру поняли, что Земля круглая, задолго до того, как кто-то её обогнул."
    m 7rksdla "А вот Земля в центре Вселенной?{w=0.2} {nw}"
    extend 4hksdlb "Ох уж это!"
    m 7dsd "Из-за этого так долго и яростно спорили, что дело доходило до жизни и смерти."
    m 1dkd "Астронома Галилея судили за ересь только за то, что он сказал: Земля — не центр Вселенной.{w=0.2} {nw}"
    extend 1esc "Его посадили под домашний арест до конца жизни."
    m 3euc "Но по мере того как астрономы лучше отслеживали движение планет, всё труднее становилось согласовать это с Землёй в центре."
    m 1eud "Приходилось придумывать безумные сложные модели, чтобы объяснить, почему планеты будто зигзагами ходят по небу, если они и правда кружат вокруг Земли."

    if renpy.seen_label("monika_science"):
        m 3eua "И как мы уже обсуждали, известно также, что Солнце — не центр Вселенной{nw}"

    else:
        m 3eua "А теперь известно даже, что Солнце — не в центре Вселенной{nw}"

    extend "— это просто одна из множества звёзд в галактике."
    m 1msblu "А знаешь, где, по науке, сейчас центр Вселенной?"
    m 3kubsu "Это ты.{w=0.2} Ты — центр {i}моей{/i} вселенной, [mas_get_player_nickname()]."
    m 3hubsb "Ахаха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent._mas_fun_facts_database,
            eventlabel="mas_fun_fact_maplesyrup",
        ),
        code="FFF"
    )

label mas_fun_fact_maplesyrup:
    m 3hksdlb "Вот тебе ещё один {w=0.2}{i}сладкий {/i}{w=0.2} факт..." #double space is intentional due to ital/no ital spacing
    m 1eua "У каждого вида клёна есть сок, из которого можно делать кленовый сироп, {w=0.1}{nw}"
    extend 1eud "но промышленный сироп обычно делают из сахарного клёна."
    m 3eua "Вид клёна проще всего узнать по форме листьев..."
    m 3eub "Лист сахарного клёна ты, возможно, уже узнаешь — он на канадском флаге!"
    m 1euc "Правда, ареал сахарного клёна ограничен — он растёт не по {i}всей{/i} Канаде."
    m 1wud "...И всё же Канада производит больше трёх четвертей мирового кленового сиропа!"
    m 3wud "И ещё удивительнее: чтобы получить всего один галлон сиропа, нужно {i}40{/i} галлонов сока!"
    m 1eua "И усилий на производство уходит куда больше, чем я ожидала..."
    m 1esc "Сок нужно долго вываривать до сиропа... что, понятно, занимает время — его нужно очень много."
    m 3eud "Ещё я слышала: если проварить чуть дольше и вылить на свежий снег...{w=0.2}{nw}"
    extend 3hub "можно даже сделать конфету!"

    if mas_isMoniNormal(higher=True):
        if persistent._mas_pm_gets_snow is not False:
            m 3euu "Звучит как забавное занятие, которое мы могли бы попробовать вместе, а, [player]?"
            m 1etc "Хотя до такого случая, возможно, ещё далеко..."
            m 1eua "Но ничего, если придётся подождать ещё немного...{w=0.3}{nw}"
            extend 1hublu "ты и так уже достаточно сладок для меня~"

        else:
            m 1eua "Звучит крайне сладко..."
            m 1rkblu "Но всё равно не так сладко, как ты, эхехе~"

    call mas_fun_facts_end
    return
