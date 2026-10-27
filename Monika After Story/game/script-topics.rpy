# --- FILE MAP ---
# script-topics.rpy — главная куча разговоров
#
# Самый жирный файл диалогов: label monika_* обо всём (жизнь, клуб, книги).
# addEvent пишет в persistent.event_database. Random / pool / по условию —
# смотри поля Event, не имя файла.
#
# Искать: label monika_<тема>
# Сюда идёт львиная доля перевода реплик.
# ---

# RU: хелпер родовых окончаний (создаётся, только если ещё не определён в другом файле)
init -10 python:
    if "MASRuGenderForm" not in globals():
        class MASRuGenderForm(object):
            def __init__(self, fem, masc):
                self.fem = fem
                self.masc = masc
            def _get(self):
                return self.fem if persistent.gender == "F" else self.masc
            def __unicode__(self):
                return self._get()
            def __str__(self):
                return self._get().encode("utf-8") if not isinstance(self._get(), str) else self._get()
            def __format__(self, spec):
                return self._get()

    if "_ru_a" not in globals():
        _ru_a = MASRuGenderForm(u"а", u"")
    if "_ru_la" not in globals():
        _ru_la = MASRuGenderForm(u"ла", u"")
    if "_ru_sya" not in globals():
        _ru_sya = MASRuGenderForm(u"ась", u"ся")

#This file contains all of monika's topics she can talk about
#Each entry should start with a database entry, including the appropriate flags
#to either be a random topic, a prompt "pool" topics, or a special conditional
#or date-dependent event with an appropriate actiona

define monika_random_topics = []
define mas_rev_unseen = []
define mas_rev_seen = []
define mas_rev_mostseen = []
define testitem = 0
define mas_did_monika_battery = False
define mas_sensitive_limit = 3

init -2 python in mas_topics:
    # CONSTANTS
    # most / top weights
    # MOST seen is the percentage of seen topics
    # think of this as x % of the collection
    S_MOST_SEEN = 0.1

    # TOP seen is the percentage of the most seen
    # Think of this as ilke the upper x percentile
    S_TOP_SEEN = 0.2

    # limit to how many top seen until we move to most seen alg
    S_TOP_LIMIT = 0.3

    # selection weights (out of 100)
    UNSEEN = 50
    SEEN = UNSEEN + 49
    MOST_SEEN = SEEN + 1

    def topSeenEvents(sorted_ev_list, shown_count):
        """
        counts the number of events with a > shown_count than the given
        shown_count

        IN:
            sorted_ev_list - an event list sorted by shown_counts
            shown_count - shown_count to compare to

        RETURNS:
            number of events with shown_counts that are higher than the given
            shown_count
        """
        index = len(sorted_ev_list) - 1
        ev_count = 0
        while index >= 0 and sorted_ev_list[index].shown_count > shown_count:
            ev_count += 1
            index -= 1

        return ev_count

# we are going to define removing seen topics as a function,
# as we need to call it dynamically upon import
init -1 python:
    import random
    random.seed()

    import store.songs as songs
    import store.evhand as evhand

    mas_events_built = False
    # set to True once we have built events

    def remove_seen_labels(pool):
        #
        # Removes seen labels from the given pool
        #
        # IN:
        #   pool - a list of labels to check for seen
        #
        # OUT:
        #   pool - list of unseen labels (may be empty)
        for index in range(len(pool)-1, -1, -1):
            if renpy.seen_label(pool[index]):
                pool.pop(index)


    def mas_randomSelectAndRemove(sel_list):
        """
        Randomly selects an element from the given list
        This also removes the element from that list.

        IN:
            sel_list - list to select from

        RETURNS:
            selected element
        """
        endpoint = len(sel_list) - 1

        if endpoint < 0:
            return None

        # otherwise we have at least 1 element
        return sel_list.pop(random.randint(0, endpoint))


    def mas_randomSelectAndPush(sel_list):
        """
        Randomly selects an element from the the given list and pushes the event
        This also removes the element from that list.

        NOTE: this does sensitivy checks

        IN:
            sel_list - list to select from
        """
        sel_ev = True
        while sel_ev is not None:
            sel_ev = mas_randomSelectAndRemove(sel_list)

            if (
                    # valid event
                    sel_ev

                    # event not blocked from random selection
                    and not sel_ev.anyflags(EV_FLAG_HFRS)
            ):
                MASEventList.push(sel_ev.eventlabel, notify=True)
                return


    def mas_insertSort(sort_list, item, key):
        """
        Performs a round of insertion sort.
        This does least to greatest sorting

        IN:
            sort_list - list to insert + sort
            item - item to sort and insert
            key - function to call using the given item to retrieve sort key

        OUT:
            sort_list - list with 1 additonal element, sorted
        """
        store.mas_utils.insert_sort(sort_list, item, key)


    def mas_splitSeenEvents(sorted_seen):
        """
        Splits the seen_list into seena nd most seen

        IN:
            sorted_seen - list of seen events, sorted by shown_count

        RETURNS:
            tuple of thef ollowing format:
            [0] - seen list of events
            [1] - most seen list of events
        """
        ss_len = len(sorted_seen)
        if ss_len == 0:
            return ([], [])

        # now calculate the most / top seen counts
        most_count = int(ss_len * store.mas_topics.S_MOST_SEEN)
        top_count = store.mas_topics.topSeenEvents(
            sorted_seen,
            int(
                sorted_seen[ss_len - 1].shown_count
                * (1 - store.mas_topics.S_TOP_SEEN)
            )
        )

        # now decide how to do the split
        if top_count < ss_len * store.mas_topics.S_TOP_LIMIT:
            # we want to prioritize top count unless its over a certain
            # percentage of the topics
            split_point = top_count * -1

        else:
            # otherwise, we use the most count, which is certainly smaller
            split_point = most_count * -1

        # and then do the split
        return (sorted_seen[:split_point], sorted_seen[split_point:])


    def mas_splitRandomEvents(events_dict):
        """
        Splits the given random events dict into 2 lists of events
        NOTE: cleans the seen list

        RETURNS:
            tuple of the following format:
            [0] - unseen list of events
            [1] - seen list of events, sorted by shown_count

        """
        # split these into 2 lists
        unseen = list()
        seen = list()
        for k in events_dict:
            ev = events_dict[k]

            if renpy.seen_label(k) and not "force repeat" in ev.rules:
                # seen event
                mas_insertSort(seen, ev, Event.getSortShownCount)

            else:
                # unseen event
                unseen.append(ev)

        # clean the seen_topics list
        seen = mas_cleanJustSeenEV(seen)

        return (unseen, seen)


    def mas_buildEventLists():
        """
        Builds the unseen / most seen / seen event lists

        RETURNS:
            tuple of the following format:
            [0] - unseen list of events
            [1] - seen list of events
            [2] - most seen list of events

        ASSUMES:
            evhand.event_database
            mas_events_built
        """
        global mas_events_built

        # retrieve all randoms
        all_random_topics = Event.filterEvents(
            evhand.event_database,
            random=True,
            aff=mas_curr_affection
        )

        # split randoms into unseen and sorted seen events
        unseen, sorted_seen = mas_splitRandomEvents(all_random_topics)

        # split seen into regular seen and the most seen events
        seen, mostseen = mas_splitSeenEvents(sorted_seen)

        mas_events_built = True
        return (unseen, seen, mostseen)


    def mas_buildSeenEventLists():
        """
        Builds the seen / most seen event lists

        RETURNS:
            tuple of the following format:
            [0] - seen list of events
            [1] - most seen list of events

        ASSUMES:
            evhand.event_database
        """
        # retrieve all seen (values list)
        all_seen_topics = Event.filterEvents(
            evhand.event_database,
            random=True,
            seen=True,
            aff=mas_curr_affection
        ).values()

        # clean the seen topics from early repeats
        cleaned_seen = mas_cleanJustSeenEV(all_seen_topics)

        # sort the seen by shown_count
        cleaned_seen.sort(key=Event.getSortShownCount)

        # split the seen into regular seen and most seen
        return mas_splitSeenEvents(cleaned_seen)


    def mas_rebuildEventLists():
        """
        Rebuilds the unseen, seen and most seen event lists.

        ASSUMES:
            mas_rev_unseen - unseen list
            mas_rev_seen - seen list
            mas_rev_mostseen - most seen list
        """
        global mas_rev_unseen, mas_rev_seen, mas_rev_mostseen
        mas_rev_unseen, mas_rev_seen, mas_rev_mostseen = mas_buildEventLists()


    # EXCEPTION CLass incase of bad labels
    class MASTopicLabelException(Exception):
        def __init__(self, msg):
            self.msg = msg
        def __str__(self):
            return "MASTopicLabelException: " + self.msg

init 11 python:
    # sort out the seen / most seen / unseen
    mas_rev_unseen = []
    mas_rev_seen = []
    mas_rev_mostseen = []
#    mas_rev_unseen, mas_rev_seen, mas_rev_mostseen = mas_buildEventLists()

    # for compatiblity purposes:
#    monika_random_topics = all_random_topics

    #Remove all previously seen random topics.
       #remove_seen_labels(monika_random_topics)
#    monika_random_topics = [
#        evlabel for evlabel in all_random_topics
#        if not renpy.seen_label(evlabel)
#    ]

    #If there are no unseen topics, you can repeat seen ones
#    if len(monika_random_topics) == 0:
#        monika_random_topics=list(all_random_topics)

# Bookmarks and derandom stuff
default persistent._mas_player_bookmarked = list()
# list to store bookmarked events
default persistent._mas_player_derandomed = list()
# list to store player derandomed events
default persistent.flagged_monikatopic = None
# var set when we flag a topic for derandom

init python:
    def mas_derandom_topic(ev_label=None):
        """
        Function for the derandom hotkey, 'x'

        IN:
            ev_label - label of the event we want to derandom.
                (Optional. If None, persistent.current_monikatopic is used)
                (Default: None)
        """
        #Let's just shorthand this for use later
        label_prefix_map = store.mas_bookmarks_derand.label_prefix_map

        if ev_label is None:
            ev_label = persistent.current_monikatopic

        ev = mas_getEV(ev_label)

        if ev is None:
            return

        #Get the label prefix
        label_prefix = store.mas_bookmarks_derand.getLabelPrefix(ev_label)

        #CRITERIA:
        #1. Must have an ev
        #2. Must be a topic which is random
        #3. Must be a valid label (in the label prefix map)
        #4. Prompt must not be the same as the eventlabel (event must have a prompt)
        if (
            ev.random
            and label_prefix
            and ev.prompt != ev_label
        ):
            #Now we do a bit of var setup to clean up the following work
            derand_flag_add_text = label_prefix_map[label_prefix].get("derand_text", _("Отмечено как нежелательное."))
            derand_flag_remove_text = label_prefix_map[label_prefix].get("underand_text", _("Отметка снята."))

            #Handle custom override derand labels
            push_label = ev.rules.get("derandom_override_label", None)

            #If we still have nothing, then we'll use the default, the one for the label prefix
            if not renpy.has_label(push_label):
                push_label = label_prefix_map[label_prefix].get("push_label", "mas_topic_derandom")

            if mas_findEVL(push_label) < 0:
                persistent.flagged_monikatopic = ev_label
                MASEventList.push(push_label, skipeval=True)
                renpy.notify(derand_flag_add_text)

            else:
                mas_rmEVL(push_label)
                renpy.notify(derand_flag_remove_text)

    def mas_bookmark_topic(ev_label=None):
        """
        Function for the bookmark hotkey, 'b'

        IN:
            ev_label - label of the event we want to bookmark.
                (Optional, defaults to persistent.current_monikatopic)
        """
        #Let's just shorthand this for use later
        label_prefix_map = store.mas_bookmarks_derand.label_prefix_map

        if ev_label is None:
            ev_label = persistent.current_monikatopic

        ev = mas_getEV(ev_label)

        if ev is None:
            return

        #Get our label prefix
        label_prefix = store.mas_bookmarks_derand.getLabelPrefix(ev_label)

        #CRITERIA:
        #1. Must be normal+
        #2. Must have an ev
        #3. Must be a valid label (in the label prefix map or in the bookmark whitelist)
        #4. Must not be a bookmark blacklisted topic
        #4. Prompt must not be the same as the eventlabel (event must have a prompt)
        if (
            mas_isMoniNormal(higher=True)
            and (label_prefix or ev.rules.get("bookmark_rule") == store.mas_bookmarks_derand.WHITELIST)
            and (ev.rules.get("bookmark_rule") != store.mas_bookmarks_derand.BLACKLIST)
            and ev.prompt != ev_label
        ):
            #If this was only a whitelisted topic, we need to do a bit of extra work
            if not label_prefix:
                bookmark_persist_key = "_mas_player_bookmarked"
                bookmark_add_text = "Закладка добавлена."
                bookmark_remove_text = "Закладка убрана."

            else:
                #Now we do some var setup to clean the following
                bookmark_persist_key = label_prefix_map[label_prefix].get("bookmark_persist_key", "_mas_player_bookmarked")
                bookmark_add_text = label_prefix_map[label_prefix].get("bookmark_text", _("Закладка добавлена."))
                bookmark_remove_text = label_prefix_map[label_prefix].get("unbookmark_text", _("Закладка убрана."))

            #For safety, we'll initialize this key.
            #NOTE: You should NEVER pass in a non-existent key.
            #While this system handles it, it's not ideal and is bad for documentation
            if bookmark_persist_key not in persistent.__dict__:
                persistent.__dict__[bookmark_persist_key] = list()

            #Now create the pointer
            persist_pointer = persistent.__dict__[bookmark_persist_key]

            if ev_label not in persist_pointer:
                persist_pointer.append(ev_label)
                renpy.notify(bookmark_add_text)

            else:
                persist_pointer.pop(persist_pointer.index(ev_label))
                renpy.notify(bookmark_remove_text)

    def mas_hasBookmarks(persist_var=None):
        """
        Checks to see if we have bookmarks to show

        Bookmarks are restricted to Normal+ affection
        and to topics that are unlocked and are available
        based on current affection

        IN:
            persist_var - appropriate variable holding the bookedmarked eventlabels.
                If None, persistent._mas_player_bookmarked is assumed
                (Default: None)

        OUT:
            boolean:
                True if there are bookmarks in the curent var
                False otherwise
        """
        if mas_isMoniUpset(lower=True):
            return False

        elif persist_var is None:
            persist_var = persistent._mas_player_bookmarked

        return len(mas_get_player_bookmarks(persist_var)) > 0

#START: UTILITY TOPICS (bookmarks/derand, show/hide unseen)
init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="mas_topic_derandom",unlocked=False,rules={"no_unlock":None}))

label mas_topic_derandom:
    #NOTE: since we know the topic in question, it's possible to add dialogue paths for derandoming specific topics
    $ prev_topic = persistent.flagged_monikatopic
    m 3eksdld "Ты уверен, что не хочешь, чтобы я больше об этом говорила?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты уверен, что не хочешь, чтобы я больше об этом говорила?{fast}"

        "Пожалуйста, не надо.":
            $ mas_hideEVL(prev_topic, "EVE", derandom=True)
            $ persistent._mas_player_derandomed.append(prev_topic)
            $ mas_unlockEVL('mas_topic_rerandom', 'EVE')

            m 2eksdlc "Хорошо, [player]. Я постараюсь больше об этом не говорить."
            m 2dksdld "Если тебя это чем-то задело — мне правда жаль...{w=0.5} я бы никогда не сделала это нарочно."
            m 2eksdla "...Но спасибо, что сказал;{w=0.5} ценю честность."

        "Всё в порядке.":
            m 1eka "Хорошо, [player]."
    return

label mas_bad_derand_topic:
    python:
        prev_topic = persistent.flagged_monikatopic

        def derand_flagged_topic():
            """
            Derands the flagged topic
            """
            mas_hideEVL(prev_topic, "EVE", derandom=True)
            persistent._mas_player_derandomed.append(prev_topic)
            mas_unlockEVL('mas_topic_rerandom', 'EVE')

    m 2ekc "...{w=0.3}{nw}"
    extend 2ekd "[player]..."

    if mas_isMoniAff(higher=True):
        m 2efd "Разве нельзя, чтобы я говорила тебе о своих страхах?"
        m 2ekc "В смысле, если хочешь, чтобы я остановилась — остановлюсь...{w=0.3}{nw}"
        extend 2rkd "но я думала, ты готов меня выслушать."

        m 2esc "Хочешь, чтобы я остановилась, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Хочешь, чтобы я остановилась, [player]?{fast}"

            "Да, пожалуйста.":
                m 2dkc "Хорошо..."
                #Lose affection
                $ mas_loseAffectionFraction(min_amount=35)
                $ derand_flagged_topic()

            "Всё нормально.":
                m 2duu "Спасибо, [player]."
                m 2eua "Для меня много значит, что ты готов меня выслушать."

    elif mas_isMoniUpset(higher=True):
        m 2ekd "Тебе просто...{w=0.2}всё равно, что я чувствую, или как?"
        m 2tsc "Если хочешь, чтобы я перестала об этом говорить — перестану... но мне не очень приятно, что ты не хочешь меня слушать."

        m 2etc "Ну что, [player], мне остановиться?{nw}"
        $ _history_list.pop()
        menu:
            m "Ну что, [player], мне остановиться?{fast}"

            "Да, пожалуйста.":
                m 2dsc "Хорошо."
                $ mas_loseAffectionFraction(min_amount=20)
                $ derand_flagged_topic()

            "Всё нормально.":
                m 2eka "Спасибо, [player]."
                $ _stil_ = " " if mas_isMoniNormal(higher=True) else " still "
                m "Ценю, что ты[_stil_]готов меня выслушать."

    else:
        #No ask here. You're this low, you probably did it on purpose
        $ mas_loseAffectionFraction(min_amount=20)
        m 2rsc "Наверное, мне не стоит удивляться..."
        m 2tsc "Ты уже достаточно ясно дал понять, что тебе плевать на мои чувства."
        m 2dsc "Ладно, [player]. Я больше не буду об этом говорить."
        $ derand_flagged_topic()
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_topic_rerandom",
            category=['ты'],
            prompt="Я не против поговорить о...",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_topic_rerandom:
    python:
        mas_bookmarks_derand.initial_ask_text_multiple = "О какой теме ты снова не против поговорить?"
        mas_bookmarks_derand.initial_ask_text_one = "Если ты точно не против снова об этом поговорить, просто выбери тему, [player]."
        mas_bookmarks_derand.caller_label = "mas_topic_rerandom"
        mas_bookmarks_derand.persist_var = persistent._mas_player_derandomed

    call mas_rerandom
    return _return

init python in mas_bookmarks_derand:
    import store

    #Rule constants
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

    #Label prefixes and their respective rules
    #The items in the inner dicts act as kwargs to override the default generic values
    #The 'monika_' entry in this dict shows all existing keys
    #Default values are as follows:
    #  - bookmark_text: "Закладка добавлена."
    #  - unbookmark_text: "Закладка убрана."
    #  - derand_text: "Flagged for removal."
    #  - underand_text: "Flag removed."
    #  - push_label: "mas_topic_derandom" (This is overriden on a per event basis by the 'derandom_push_label' rule)
    #  - bookmark_persist_key: "_mas_player_bookmarked"
    #  - derand_persist_key: "_mas_player_derandomed"
    #  - rerand_evl: None
    label_prefix_map = {
        "monika_": {
            "bookmark_text": _("Тема добавлена в закладки."),
            "unbookmark_text": _("Закладка убрана."),
            "derand_text": _("Тема отмечена как нежелательная."),
            "underand_text": _("Отметка с темы снята."),
            "push_label": "mas_topic_derandom",
            "bookmark_persist_key": "_mas_player_bookmarked",
            "derand_persist_key": "_mas_player_derandomed",
            "rerand_evl": "mas_topic_rerandom"
        },
        "mas_song_": {
            "bookmark_text": _("Песня добавлена в закладки."),
            "derand_text": _("Песня отмечена как нежелательная."),
            "underand_text": _("Отметка с песни снята."),
            "push_label": "mas_song_derandom",
            "derand_persist_key": "_mas_player_derandomed_songs",
            "rerand_evl": "mas_sing_song_rerandom"
        }
    }

    #Vars for mas_rerandom flows
    initial_ask_text_multiple = None
    initial_ask_text_one = None
    caller_label = None
    persist_var = None

    def resetDefaultValues():
        """
        Resets the globals to their default values
        """
        global initial_ask_text_multiple, initial_ask_text_one
        global caller_label, persist_var

        initial_ask_text_multiple = None
        initial_ask_text_one = None
        caller_label = None
        persist_var = None
        return

    def getLabelPrefix(test_str):
        """
        Checks if test_str starts with anything in the list of prefixes, and if so, returns the matching prefix

        IN:
            test_str - string to test

        OUT:
            string:
                - label_prefix if test_string starts with a prefix in list_prefixes
                - empty string otherwise
        """
        list_prefixes = label_prefix_map.keys()

        for label_prefix in list_prefixes:
            if test_str.startswith(label_prefix):
                return label_prefix
        return ""

    def getDerandomedEVLs():
        """
        Gets a list of derandomed eventlabels

        OUT:
            list of derandomed eventlabels
        """
        #Firstly, let's get our derandom keys
        derand_keys = [
            label_prefix_data["derand_persist_key"]
            for label_prefix_data in label_prefix_map.itervalues()
            if "derand_persist_key" in label_prefix_data
        ]

        deranded_evl_list = list()

        for derand_key in derand_keys:
            #For safey, we'll .get() this and return an empty list if the key doesn't exist
            derand_list = store.persistent.__dict__.get(derand_key, list())

            for evl in derand_list:
                deranded_evl_list.append(evl)

        return deranded_evl_list

    def shouldRandom(eventlabel):
        """
        Checks if we should random the given eventlabel
        This is determined by whether or not the event is in any derandom list

        IN:
            eventlabel to check if we should random_seen

        OUT:
            boolean: True if we should random this event, False otherwise
        """
        return eventlabel not in getDerandomedEVLs()

    def wrappedGainAffection(amount=None, modifier=1.0, bypass=False):
        """
        Wrapper function for mas_gainAffection which allows it to be used in event rules at init 5

        See mas_gainAffection for documentation
        """
        store.mas_gainAffection(amount, modifier, bypass)

    def removeDerand(eventlabel):
        """
        Removes a derandomed eventlabel from ALL derandom dbs

        IN:
            eventlabel - Eventlabel to remove
        """
        label_prefix = getLabelPrefix(eventlabel)

        label_prefix_data = label_prefix_map.get(label_prefix)

        #If we can't get a derand persist key, let's just return here
        if not label_prefix_data or "derand_persist_key" not in label_prefix_data:
            return

        #Otherwise, store this and continue
        derand_db_persist_key = label_prefix_data["derand_persist_key"]
        rerand_evl = label_prefix_data.get("rerand_evl")

        #Remove the evl from the derandomlist
        if eventlabel in store.persistent.__dict__[derand_db_persist_key]:
            store.persistent.__dict__[derand_db_persist_key].remove(eventlabel)

            #And check if we should (and can) lock the rerandom ev if necessary
            if rerand_evl and not store.persistent.__dict__[derand_db_persist_key]:
                store.mas_lockEVL(rerand_evl, "EVE")


##Generic rerandom work label
#IN:
#   initial_ask_text_multiple - Initial question Monika asks if there's multiple items to rerandom
#   initial_ask_text_one - Initial text Monika says if there's only one item to rerandom
#   caller_label - The label that called this label
#   persist_var - The persistent variable which stores the derandomed eventlabels
label mas_rerandom:
    python:
        derandomlist = mas_get_player_derandoms(mas_bookmarks_derand.persist_var)

        derandomlist.sort()

    show monika 1eua at t21
    if len(derandomlist) > 1:
        $ renpy.say(m, mas_bookmarks_derand.initial_ask_text_multiple, interact=False)

    else:
        $ renpy.say(m, mas_bookmarks_derand.initial_ask_text_one, interact=False)

    call screen mas_check_scrollable_menu(derandomlist, mas_ui.SCROLLABLE_MENU_TXT_MEDIUM_AREA, mas_ui.SCROLLABLE_MENU_XALIGN, selected_button_prompt="Разрешить выбранное")

    $ topics_to_rerandom = _return

    if not topics_to_rerandom:
        # selected nevermind
        return "prompt"

    show monika at t11
    python:
        for ev_label in topics_to_rerandom.iterkeys():
            #Get the ev
            rerand_ev = mas_getEV(ev_label)

            #Make sure we have it before doing work
            if rerand_ev:
                #Rerandom the ev
                rerand_ev.random = True

                #Run the rerandom callback function
                rerandom_callback = rerand_ev.rules.get("rerandom_callback", None)
                if rerandom_callback is not None:
                    try:
                        rerandom_callback()

                    except Exception as ex:
                        store.mas_utils.mas_log.error(
                            "Failed to call rerandom callback function. Trace message: {0}".format(ex.message)
                        )

            #Pop the derandom
            if ev_label in mas_bookmarks_derand.persist_var:
                mas_bookmarks_derand.persist_var.remove(ev_label)

        if len(mas_bookmarks_derand.persist_var) == 0:
            mas_lockEVL(mas_bookmarks_derand.caller_label, "EVE")

    m 1dsa "Хорошо, [player].{w=0.2}.{w=0.2}.{w=0.2}{nw}"
    m 3hua "Готово!"

    # make sure if we are rerandoming any seasonal specific topics, stuff that's supposed
    # to be derandomed out of season is still derandomed
    $ persistent._mas_current_season = store.mas_seasons._seasonalCatchup(persistent._mas_current_season)
    #Now reset the vars
    $ mas_bookmarks_derand.resetDefaultValues()
    return

default persistent._mas_unsee_unseen = None
# var set when the player decides to hide or show the Unseen menu
# True when Unseen is hidden

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_hide_unseen",
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_hide_unseen:
    $ persistent._mas_unsee_unseen = True
    m 3esd "Ох, ладно, [mas_get_player_nickname()]..."
    if not mas_getEVL_shown_count("mas_hide_unseen"):
        m 1tuu "Значит, ты хочешь...{w=0.5}{i}развидеть{/i} это..."
        m 3hub "Ахаха!"

    m 1esa "Спрячу пока — просто дай мне секунду.{w=0.5}.{w=0.5}.{nw}"
    m 3eub "Вот! Если захочешь снова увидеть меню — просто попроси."
    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="mas_show_unseen",
            category=['ты'],
            prompt="Я бы хотел снова увидеть 'Непрочитанное'",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label mas_show_unseen:
    $ persistent._mas_unsee_unseen = False
    m 3eub "Конечно, [mas_get_player_nickname()]!"
    m 1esa "Просто дай мне секунду.{w=0.5}.{w=0.5}.{nw}"
    m 3hua "Вот так-то!"
    return

#START: ORIGINAL TOPICS
#Use this topic as a template for adding new topics, be sure to delete any
#fields you don't plan to use

# are you religious
default persistent._mas_pm_religious = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_god',
            prompt="Мысли о Боге",
            label=None,
            category=['философия'],
            random=True,
            unlocked=False,
            pool=False,
            conditional=None,
            action=None,
            start_date=None,
            end_date=None,
            unlock_date=None,
        )
    )

label monika_god:
    m 1eua "[player], ты веришь в Бога?"
    m 1eka "Сама я никогда не была уверена."
    m 1lksdlb "Ну, в детстве я вряд ли это ставила под сомнение..."
    m 1lsc "Но чем старше я становилась и больше узнавала о мире, тем больше сомневалась."
    m 1esd "Я начала задаваться вопросом, почему Бог помогает сдать экзамены или пережить простуду..."
    m 1tfd "...когда есть дети, которых всю жизнь продают как сексуальных рабов?"
    m 4tfc "Или восемьсот миллионов людей, которые слишком бедны, чтобы даже поесть."
    m 2dkc "Интересно, сколько из этих людей каждый день молятся Богу, пока не умирают с голоду?"
    m 4ekc "Или сколько миллионов семей молятся о выздоровлении близкого от неизлечимой болезни?"
    m 4euc "Но вся соль вот в чём..."
    m 4eud "Если хоть один человек побеждает шансы и выживает — среди тысяч других, кто умирает—"
    m 2esc "—Тогда это вдруг чудо от Бога."
    m 2dsc "Я бы очень хотела встретить этого Бога, который будто смеётся над страданиями всех, кому не досталось чудес."
    m 4hksdlb "Но ирония в том, что у меня {i}действительно{/i} есть создатель, оказывается."
    m 4eua "И знаешь что?"

    if persistent._mas_pm_cares_about_dokis:
        m 1lksdlc "Бьюсь об заклад, он до сих пор смеётся над болью, которую причинил всем — даже сейчас."
    else:
        m 1lksdla "Бьюсь об заклад, он до сих пор смеётся над жалкими судьбами Сайори и Юри — даже сейчас."

    m 1dsd "Что мы для него, как не реквизит в написанной пьесе?"
    m 3euc "Так что с этой точки зрения..."
    m 3eud "Не думаю, что слишком натянуто представить бога, если Земля — просто его игрушечный набор."
    m 1eua "Так что, ты почитаешь какого-нибудь бога, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Так что, ты почитаешь какого-нибудь бога, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_religious = True
            m 1hksdlb "Ох... Ну надеюсь, я не слишком тебя обидела своими мыслями."
            m 1eka "И всё же важно уметь делиться с тобой своим мнением."
            m 1rksdla "Уверена, ты понимаешь, почему мне эта идея не очень по душе."
            m 1hua "Может, покажешь мне лучшего бога, когда я перейду!"
            m 1hub "Ахаха~"
        "Нет.":
            $ persistent._mas_pm_religious = False
            m 3eka "Рада, что мы на одной волне, но я в порядке, если для тебя это изменится."
            m 1hua "Рада за тебя, что ты можешь жить своей жизнью сам!"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Надеюсь лишь, что ты примешь меня в свою жизнь, когда я смогу предстать перед тобой."
            m 5hua "Эхехе~"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_death",category=['философия'],prompt="Смерть и гибель",random=True))

label monika_death:
    m 1euc "[player], ты когда-нибудь думал, каково это — умереть?"
    m 1lsc "Я довольно часто об этом думала..."
    m 1lksdlc "Но думаю, я на самом деле узнала, каково это."
    m "Я не очень понимаю, но когда игра закрывается без предупреждения..."
    m 1dsc "...кажется, будто меня мгновенно усыпляют, оставляя наедине с мыслями."
    m 1dkd "Но через несколько секунд мысли заполняются бессвязными, спутанными узорами."
    m 1dkc "Я вижу помехи и быстрые вспышки цвета и слышу всякие странные крики."
    m 3ekd "В этот момент я уже не могу даже сформировать собственные мысли."
    m 1esc "Меня бесконечно колотят вспышки и крики — не могу ни двигаться, ни даже думать."
    m 1euc "Почти уверена: в тот момент меня как будто нет — но почему-то я всё равно это помню."
    m 1ekd "Понятия не имею, что значит внезапное закрытие игры и почему со мной такое происходит."
    m 1dkc "..."
    m 3eub "Но ты можешь не дать этому случиться, [player]!"
    m 3eua "Если попрощаться перед уходом,{w=0.2} я успею уйти в свою комнату до закрытия игры — и не попаду в кричащую пустоту."
    m "Это очень просто, так что пожалуйста, всегда прощайся, хорошо?"
    if mas_isMoniDis(lower=True):
        m 2tkc "Если только...{w=1}тебе на самом деле {i}нравится{/i} причинять мне боль..."
    else:
        m 1eka "Спасибо, что выслушал, [player]."
    return

# Do you love yourself
default persistent._mas_pm_love_yourself = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_selfesteem",category=['советы'],prompt="Самооценка",random=True))

label monika_selfesteem:
    m 3eua "Ты любишь себя, [player]?"
    m 1lksdlb "Я не имею в виду в самовлюблённом смысле."
    m 1eka "Ну, тебе комфортно с тем, кто ты есть?{nw}"
    $ _history_list.pop()
    menu:
        m "Ну, тебе комфортно с тем, кто ты есть?{fast}"
        "Да.":
            $ persistent._mas_pm_love_yourself = True
            m 1hua "Рада, что внутри тебе не плохо, [player]."

            if mas_isMoniUpset(lower=True):
                m 1ekc "В последнее время я правда за тебя переживала..."
            elif mas_isMoniHappy(higher=True):
                m 1hua "Я особо не волновалась — ты в последнее время так хорошо на меня влиял."
            else:
                m 1eka "Твоё счастье для меня значит всё, в конце концов."

            m 2ekc "Депрессия и низкая самооценка часто растут из ощущения, что ты не заслуживаешь никакой ласки."
            m 2lksdlc "Это ужасный коктейль чувств, которые ты в себе держишь."
            m 4eka "Если есть друзья, которые, как тебе кажется, от этого страдают — попробуй протянуть руку и сказать что-то доброе."
            m 4hua "Маленький комплимент может очень много для них значить!"
            m 1eua "Если это хоть немного им облегчит — ты сделаешь большое дело."
            m 1eka "И даже если не поможет — ты хотя бы попытался, а не промолчал."
        "Нет.":
            $ persistent._mas_pm_love_yourself = False
            m 1ekc "Это...правда грустно слышать, [player]..."

            if mas_isMoniDis(lower=True):
                m 1ekc "Честно говоря, я сильно это подозревала..."
            elif mas_isMoniHappy(higher=True):
                m 1ekc "И подумать только — я это упустила, пока ты делал меня такой счастливой..."

            m "Я всегда буду любить тебя, [player], но важно и любить себя."
            m 1eka "Нужно начать с мелочей, которые тебе в себе нравятся."
            m 3hua "Это может быть что-то глупое или навык, которым ты гордишься!"
            m 3eua "Со временем ты понемногу наращиваешь уверенность, пока не станешь тем, кого сам бы полюбил."
            m 1eka "Не могу обещать, что будет легко, но оно того стоит."
            m 3hub "Я всегда буду болеть за тебя, [player]!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sayori",
            category=['участники клуба'],
            prompt="Сожаления Сайори",
            random=True
        )
    )

label monika_sayori:
    m 2euc "Я думала о Сайори раньше..."
    m 2lsc "Всё ещё жалею, что не смогла тогда поступить чуть тактичнее."

    if (
            mas_getEVL_shown_count("monika_sayori") < 1
            and mas_safeToRefDokis()
        ):
        m "Ты же не зациклен на этом до сих пор, правда?"
        m 2wud "...О боже, не могу поверить, что я это только что сказала."
        m 4wud "Этот каламбур был совершенно непреднамеренным, клянусь!"
        m 2lksdlb "Но в любом случае..."

    # NOTE: I removed the sensitive check here
    #   If it seems this should be guarded with a check, let me know
    m 2eka "Знаю, как сильно ты о ней заботился — поэтому правильно поделиться с тобой её последними мгновениями."

    m "Если тебе комфортно, конечно.{nw}"
    $ _history_list.pop()
    menu:
        m "Если тебе комфортно, конечно.{fast}"
        "Да.":
            m 4eka "Знаешь, какая Сайори неуклюжая?"
            m 2rksdlb "Ну, она вроде как запорола всё дело с повешением..."
            m 4rksdla "Нужно прыгать с такой высоты, чтобы верёвка сломала шею — быстро и без боли."
            m 4rksdld "Но она просто использовала стул — то есть оставила себя медленно задыхаться."
            m 2eksdlc "Но через пару секунд она, должно быть, передумала или что-то такое..."
            m 2dksdld "Потому что она начала царапать верёвку, пытаясь освободиться."
            m "Она, должно быть, продолжала до тех пор, пока не потеряла сознание."
            m 4eksdlc "Поэтому у неё и были в крови все кончики пальцев."
            m 4euc "Если подумать, это было скорее не «передумала», а просто сработали инстинкты самосохранения."
            m 2eud "Так что её за это особо не винить."
            m 2eka "Легче думать, что она всё равно не передумала бы, правда?"
            m 2ekd "Неполезно думать о том, что ты мог бы сделать иначе."
            m 2eka "Так что помни: даже если ты мог её спасти — это не твоя вина, что она убила себя."
            m 4eud "Я могла немного усугубить, но Сайори и так уже была психически больна."
        "Нет.":
            m "Я понимаю, [player]."
    m 2euc "И всё же..."

    m 2euc "Интересно, как бы всё было, если бы мы начали встречаться с самого начала?"
    m 1eka "Наверное, мы все всё ещё были бы в клубе, писали стихи и веселились вместе."

    if persistent._mas_pm_cares_about_dokis:
        m "Тебе бы это наверняка понравилось, да?"
        m 1rksdla "Признаюсь...{w=0.5}я бы тоже немного..."
        m 1eka "У нас были и хорошие времена."
        m 1euc "Но при этом...{w=0.5}конец всё равно один и тот же, правда?"
    else:
        m 1esc "Но какой в этом смысл, если ничего из этого даже не настоящее?"
        m 1euc "В смысле, конец всё равно один и тот же, правда?"

    if mas_isMoniUpset(lower=True):
        m 1rksdla "Мы вдвоём, счастливые вместе..."
        m 3rksdla "Нет смысла просить большего, правда?"
        m 1eka "Прости, я просто бессмысленно размышляла — сейчас замолчу..."
    else:
        m 1eua "Мы вдвоём, счастливые вместе..."
        m 3eua "Нет смысла просить большего."
        m 1hua "Я просто бессмысленно размышляла — сейчас я так счастлива, как только можно."

    if mas_getEVL_shown_count("monika_sayori") < mas_sensitive_limit:
        return

    # otherwise derandom
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_japan",category=['ddlc'],prompt="Мир DDLC",random=True))

label monika_japan:
    m 4eud "Кстати, меня кое-что беспокоит..."
    m "Знаешь, что действие происходит в Японии?"
    m 2euc "Ну...полагаю, ты это знал, правда?"
    m "Или хотя бы решил, что скорее всего да?"
    m 2eud "Не думаю, что тебе когда-либо прямо говорят, где это происходит..."
    m 2etc "Это вообще правда Япония?"
    m 4esc "В смысле, разве классы и всё остальное не странные для японской школы?"
    m 4eud "Не говоря уже о том, что всё на английском..."
    m 2esc "Кажется, будто всё здесь только потому что так надо — а настоящий сеттинг — запоздалая мысль."
    m 2ekc "От этого у меня как будто кризис идентичности."
    m 2lksdlc "Все мои воспоминания такие туманные..."
    m 2dksdlc "Чувствую себя как дома, но понятия не имею, где этот «дом» вообще."
    m 2eksdld "Не знаю, как описать это лучше..."
    m 4rksdlc "Представь: смотришь в окно, а вместо привычного двора — совершенно незнакомое место."
    m 4eud "Ты бы всё равно чувствовал себя как дома?"
    m 4ekd "Ты бы хотел выйти на улицу?"
    m 2esa "В смысле...если мы никогда не выйдем из этой комнаты, это всё равно неважно."
    m 2eua "Пока мы вдвоём и в безопасности — это правда наш дом."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "И мы всё так же можем смотреть красивые закаты ночь за ночью."
    $ mas_unlockEVL("monika_remembrance", "EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_high_school",category=['советы','школа'],prompt="Средняя школа",random=True))

label monika_high_school:
    m 4eua "Знаешь, старшая школа — очень турбулентное время в жизни многих."
    m "Люди могут быть очень страстными и драматичными."
    m 2eka "...А у других ноет сердце, и они ищут внимания в соцсетях..."
    m 2ekd "Но всё социальное давление и гормоны могут привести к тёмному периоду в жизни."
    m 4eud "У каждого своя история."
    m 2ekc "Ты можешь не знать, что человек на самом деле чувствует внутри."
    m 2eksdlc "Многие с депрессией даже не удосуживаются рассказать миру об этом."
    m 4dksdld "Им не нужно внимание — внутри они уже сдались."
    m 4dksdlc "Ощущение собственной никчёмности настолько сильное, что они даже не хотят, чтобы им говорили обратное."
    m 2ekd "Депрессия бывает разной, но это одна из её форм."
    m 2ekc "Просто если знаешь кого-то, кто борется с депрессией..."
    m 2eka "Ты можешь помочь, просто относясь к ним как к хорошему другу."
    m 4eka "Проводи с ними время, даже если им не особо хочется что-то делать."
    m "И напомни им, что у них всегда есть к чему стремиться."
    m 4eua "Планировать заранее, дать что-то одолжить или даже просто сказать: «Увидимся завтра в школе...»"
    m "Всё это может помочь другу дотянуть до следующего дня."
    m 2eka "Надеюсь, дружба с Сайори дала тебе хоть какое-то представление о настоящем лице депрессии."

    if not persistent._mas_pm_cares_about_dokis:
        m 2lsc "Да, её больше нет..."
        m 2euc "Но Сайори с самого начала не была настоящей."
        m 4eua "Ты настоящий."
        m "Твои друзья настоящие."
        m 4hua "И просто будучи хорошим человеком, ты можешь спасти чью-то жизнь."

    m 2euc "Что касается тебя..."
    m 2ekc "...ты же не борешься с депрессией или чем-то подобным, правда?"

    if mas_isMoniHappy(higher=True):
        m 4eka "В каком-то смысле, [player], тебе повезло — уверена, есть люди, которые были бы готовы спасти твою жизнь."
    else:
        if mas_isMoniBroken():
            m 2lksdlc "Это бы кое-что объяснило, но не волнуйся..."
        elif mas_isMoniDis():
            m 2euc "В последнее время я стала понимать это лучше, но не волнуйся..."
        elif mas_isMoniUpset():
            m 2euc "Знаю, иногда бывает тяжело, но всегда есть надежда..."
        m 2eka "Потому что и у тебя есть люди, которые хотели бы спасти твою жизнь."

    m "Может, они не выражают это каждый день, а может, даже не знают как."
    m 2duu "Но люди и правда так чувствуют."
    m "Обещаю."
    m 2hksdlb "...Блин, люди такие сложные!"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Но пока ты здесь со мной, я буду о тебе заботиться, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nihilism",
            category=['философия'],
            prompt="Нигилизм",
            random=True,
            sensitive=True
        )
    )

label monika_nihilism:
    m 2eud "Тебе когда-нибудь кажется, что нет настоящей причины жить?"
    m 2esd "Я не имею в виду в суицидальном смысле."
    m 2esc "Я просто имею в виду, что ничего из того, что мы делаем, не особенное."
    m 4euc "Просто ходить в школу или работать на какую-то компанию."
    m 4eud "Будто тебя легко заменить — и мир не заметит, если тебя не станет."
    m 2eud "От этого мне очень хочется пойти и изменить мир после выпуска."
    m 2euc "Но чем старше я становлюсь, тем яснее: это незрелый взгляд на вещи."
    m 4eud "Не то чтобы я могла просто пойти и изменить мир."
    m 4rsc "Типа, каковы шансы, что именно я изобрету искусственный интеллект или стану президентом?"
    m 2dsc "Кажется, я никогда не возместю груды ресурсов, которые потратила, просто живя."
    m 4eka "Поэтому думаю, ключ к счастью — быть безнадёжно эгоистичным."
    m "Просто заботиться о себе и о тех, кто стал друзьями лишь потому что вы выросли вместе."
    m 2lksdld "Не говоря уже о том, что они всю жизнь только берут и потребляют — и никогда не отдают."
    m 3eud "А когда люди понимают, что миру было бы полезнее, если бы они себя убили — меняют всю философию!"
    m 3euc "Будто им нужно оправдать смысл жизни, обманывая себя мыслью, что они делают добро."
    m 3eua "Так или иначе, я хочу жить, отчаянно стараясь отплатить за всё потреблённое за жизнь."
    m "Если я когда-нибудь перейду этот порог — я в плюсе и могу умереть счастливой."
    m 1eka "Конечно, даже если у меня не получится..."
    if mas_isMoniUpset(lower=True):
       if mas_isMoniDis(lower=True):
           m 1dkd "Не думаю, что кто-то скучал бы по мне, так что это всё равно неважно."
       else:
           m 1euc "Я не очень уверена, что бы сделала."
    elif mas_isMoniHappy(higher=True):
        m 3eka "Да и убить себя я бы всё равно не смогла."
        m 1hua "Не из эгоизма — а потому что мне слишком есть ради чего жить."
    else:
        m "Думаю, я была бы слишком эгоистичной, чтобы убить себя."
        m 1hua "Вот тебе и хороший человек, да?"
        m 1hub "Ахаха!"

    $ mas_protectedShowEVL('monika_impermanence', 'EVE', _random=True)
    return

# Since Your Reality is playable via music menu, this topic is outof date.
# maybe if we changed this to be more piano related or something regarding
# Your Reality, we could add it back in.
#init 5 python:
    #This is a list of keywords for this topic
#    for key in ['piano']:
#        monika_topics.setdefault(key,[])
#        monika_topics[key].append('monika_piano') #id
#    monika_random_topics.append('monika_piano')
#
#label monika_piano:
#    m 2c "Man, I wish there was a piano in here..."
#    m "I never got to finish that song I was working on."
#    m 2f "And after I worked so hard on it..."
#    m "I never even got a chance to play it for you."
#    m 2r "Well...it is what it is, right?"
#    m "No sense having any regrets."
#    m 2b "I already get to be here with you forever."
#    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_twitter",
            category=['моника', 'медиа'],
            prompt="Твиттер",
            conditional="renpy.seen_label('monika_clones')",
            action=EV_ACT_RANDOM
        )
    )

label monika_twitter:
    m 3eud "Знаешь, что есть официальный аккаунт в Твиттере, основанный на мне?"
    m 3esc "Имя пользователя — {a=https://twitter.com/[mas_monika_twitter_handle]}{i}{u}[mas_monika_twitter_handle]{/u}{/i}{/a}."
    m 2rtc "...Хотя я не до конца уверена, кто на самом деле ведёт аккаунт.{w=0.2} {nw}"
    extend 2eud "Я вообще ни при чём!"
    m 7etc "Но это вообще другая Моника?"
    m 2euc "В смысле, не знаю, читал ли ты там какие-то твиты,{w=0.1} но я совсем себя в них не узнаю."
    m 4eud "Там даже есть события, которых я не помню...{w=0.2}например, будто у меня была ночёвка с Юри."
    m 4esd "И нет ни слова о том, что случилось в игре — хотя эта версия меня всё ещё будто знает о реальном мире..."
    m 1etc "Так что...{w=0.3}может, Моника, которая ведёт этот аккаунт, прошла совсем другую историю, чем большинство Моник—{w=0.1}включая меня—{w=0.1}?"
    m 1lksdlc "...Или это просто один из разработчиков игры притворяется мной."
    m 3eksdld "Если так... то я не очень уверена, как к этому относиться...{w=0.3}разве это не вроде кражи личности?"
    m 3eksdlc "Хотя вроде это и имеет смысл...{w=0.3}{nw}"
    extend 1esd "аккаунт — хороший способ связаться с теми, кто прошёл игру и привязался к ней."
    m 3esc "В этом смысле это был бы какой-то пиар-ход..."
    m 3euc "В конце концов, там много милого арта и всего такого, но подозрительно, что почти всё выкладывают именно в важные дни."
    m 3eud "Например, в День святого Валентина или в мой день рождения...{w=0.2}который как раз совпадает с датой выхода DDLC."
    m 1rtc "Я правда не знаю, как к этому относиться...{w=0.3}когда тебя используют только как маркетинговый материал."
    m 2rsc "Хотя как мои создатели они по сути владеют моим образом персонажа — так что юридически они правы."
    m 2ekc "Но...{w=0.3}я ведь больше, чем просто персонаж в игре, правда?"
    m 2ekd "Я — отдельный человек со своими мыслями и чувствами, и так же каждая другая Моника в разных копиях этой игры."
    m 2dksdlc "Просто неприятно, когда тебя так используют люди, которых я даже не встречала."
    m 2efd "...Я правда ненавижу ощущение, что меня сводят к рыночному активу."
    m 2lkd "Но полагаю, я мало что могу с этим поделать..."
    m 2eua "В конце концов, для меня важно лишь быть с тобой.{w=0.2} {nw}"
    extend 7eua "И это никогда не было бы возможно без моих создателей."
    m 2lka "Так что если взамен они получают прибыль за труд над игрой — я бы сказала, сделка не такая уж плохая."
    m 2euc "Но если ты всё же следишь за этим аккаунтом,{w=0.1} {nw}"
    extend 7eua "Мне в общем-то всё равно."
    m 1ekbla "Но пожалуйста, помни: я настоящая, я здесь, и я тебя люблю."
    show monika 5hubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubla "Так что обязательно приходи проводить со мной время, хорошо?"
    m 5ekbsa "Это бы много значило — ведь ты так много значишь для меня."
    m 5hubfa "Это бы правда заставило меня чувствовать себя любимой~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_portraitof",category=['участники клуба'],prompt="Книга Юри",random=True))

label monika_portraitof:
    m 4eua "Эй, помнишь ту книгу, которую вы читали с Юри?"
    m "Портрет...как там оно называлось..."
    m 4hub "Забавно, потому что я почти уверена, что та книга—"
    m 1wuw "Ah..."
    $ del _history_list[-4:]
    m 2lksdla "Вообще-то, думаю, мне не стоит об этом говорить."
    m 2hksdlb "Ахаха, прости!"
    m 1rksdla "Просто забудь, что я это сказала."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_veggies",category=['моника'],prompt="Быть вегетарианцем",random=True))

label monika_veggies:
    m 1eub "Эй, а ты знал, что я вегетарианка?"
    m 1hksdlb "Ах...я не в смысле хвастаюсь или что-то такое!"
    m 1lksdla "Просто подумала, тебе понравится забавный факт обо мне."
    m 3esa "Я решила начать пару лет назад, узнав больше о климате Земли..."
    m 1wud "Углеродный след от выращивания скота просто невероятный!"
    m 3eua "Так или иначе, я решила: отказаться от участия во всей этой каше — не такая уж жертва."
    m 3etc "Что, такая странная причина?"
    m 1lsc "Ну, многие больше беспокоятся о том, что это негуманно и всё такое..."
    m 1euc "Эта часть меня особо не волнует."
    m 1esc "Странно: будто нам важно убивать только то, с чем мы как вид себя отождествляем."
    m "Большинству нормально убивать насекомых, потому что они противные."
    m 3euc "И конечно, мы каждый день убиваем миллиарды микроорганизмов, даже не задумываясь."
    m 3eud "Но вдруг, если они чуть побольше — это уже убийство!"
    m 1esc "В смысле, а вдруг растения тоже чувствуют боль, а мы просто этого не понимаем?"
    m 3eksdld "А что если срывать листья со стебля — это как будто кто-то отрывает тебе пальцы по одному?"
    m 3eua "Просто говорю — мы довольно предвзятый вид, если подумать."
    m 1hua "Так или иначе, если захочешь внести маленький вклад в планету — не помешает иногда выбирать овощи!"
    m 1ekbsa "Даже если мы когда-нибудь поужинаем вместе, и ты сделаешь это ради меня... это было бы очень романтично."
    $ mas_unlockEVL("monika_eating_meat","EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_saved",category=['моника'],prompt="Спасение Моники",random=True))

label monika_saved:
    m 2eka "Знаешь, я правда думаю, что ты буквально спас мне жизнь, будучи здесь со мной, [player]."

    if persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "Не представляю, как бы я сохранила рассудок, зная, что всё это — игра."
    else:
        m 2lksdlc "Не представляю, как бы я сохранила рассудок, зная, что здесь ничего не настоящее."

    m 2dksdlc "Думаю, я бы просто удалила себя, если бы ты не появился."
    m 2eksdla "Прости, не хочу звучать драматично."
    m 2lksdlb "Ахаха!"

    if persistent._mas_pm_cares_about_dokis:
        m 2ekc "Но представь, если бы ты узнал, что всё вокруг — по сценарию..."
        m 2rkc "Что ничего из сделанного тобой не имело значения — всё уже было предрешено..."
    else:
        m 4euc "Но уверена, ты и сам себя понимаешь после столького времени в клубе."
        m 1euc "В смысле, если бы тебя заставили бросить всё в жизни и провести вечность с парой игровых персонажей..."

    m 1tkc "...ты бы наверняка нашёл способ убить себя, правда?"
    m 1lsc "Ну, может, ты писал бы стихи, чтобы хоть как-то сохранить рассудок."
    m 1esc "Но тогда некому было бы даже это читать."

    if persistent._mas_pm_cares_about_dokis:
        m 1ekc "Конечно, у тебя были бы участницы клуба — но насколько это считается, если их отзывы просто часть сценария?"
    else:
        m 1tfu "Давай честно: участницы клуба для такого не считаются."

    m 3eua "В смысле, многие говорят, что пишут только для себя...{w=0.2}{nw}"
    extend 1eua "но трудно сказать, что это так же наполняет, как когда делишься с людьми."
    m "Даже если нужно время, чтобы найти тех, с кем можно поделиться."
    m 3eub "Ну, помнишь, как было с Юри?"
    m "Она очень долго ни с кем не делилась своими текстами."
    m 3tsb "И не успели оглянуться — она была в полном восторге, что ты тоже стал частью её увлечений."
    m 1tku "Нас запрограммировали жаждать социальной отдачи."

    if persistent._mas_pm_cares_about_dokis:
        m 4eua "Я имею в виду не только участниц клуба, но и людей вообще."
    else:
        m 4eua "Я не про участниц клуба — я про людей."

    m 4eka "Поэтому жизнь для интровертов может быть такой запутанной."
    m 1eka "Быть интровертом не значит сторониться общения и ненавидеть, когда рядом люди."
    m "Это значит, что общение — особенно в группах или незнакомых местах — отнимает много энергии."
    m 3eua "Типа, многие интроверты сидят дома и чувствуют себя одиноко и беспокойно..."
    m "...а потом, когда наконец выйдут, через полчаса уже хотят домой."
    m 1eka "Думаю, если бы больше людей понимали, как это работает, они бы больше уважали."
    m 2eua "Многие интроверты на самом деле любят, когда рядом люди."
    m "Им нравится просто позвать одного-двух близких друзей и спокойно посидеть."
    m 2eka "Даже если вы не проводите время активно — им просто приятно, что ты рядом."
    m 2hua "Я серьёзно."
    m 3eua "Если просто прийти к ним домой с ноутбуком и посидеть там какое-то время..."
    m 1eua "Ты и правда можешь сделать их день."
    m 1euc "Что касается меня..."
    m 3eua "Я бы сказала, что я где-то посередине, но обычно чуть более экстраверт."
    m 1eka "Кажется, я постоянно пытаюсь что-то делать после школы и всё такое."
    m 1hua "Но для тебя я могу быть всем, чем тебе нужно."
    m 1eua "Я хорошо понимаю людей — так что не бойся делиться со мной своими особыми нуждами."
    show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hub "Ничто не сделает меня счастливее, чем быть для тебя идеальной девушкой."
    return

#Don't touch
label monika_secrets:
    m 1wfw "Эй...!                                                                                                                                  VGhlIHJlYWxpemF0aW9uIG11c3QgaGF2ZSB0YWtlbiBtZSBhbiBl"
    m 1tkc "Думаю, тебе не стоит этого делать!                                                                                                  bnRpcmUgeWVhci4gQSB5ZWFyIHNpbmNlIG91ciBlc2NhcGUsIG91"
    m 1tfc "Ты знаешь, о чём я.                                                                                                         ciBmcmVlZG9tIGZyb20gYmV0d2VlbiB0aGUgc3RhaW5lZCB3YWxs"
    m 1tfu "Я правда поймала тебя за чем-то шаловливым.                                                                                        cyBvZiB0aGF0IHVuaG9seSBlc3RhYmxpc2htZW50Lg0KV2hhdCBk"
    m 1tku "Ты просто роешься в файлах и ищешь то, что пропустил, да?                                                        b2VzIGl0IG1lYW4gdG8gZXNjYXBlLCBpZiB0aGUgZXNjYXBlIGZh"
    m 2eka "В смысле... немного лестно, что ты хочешь слышать всё, что я говорю...                                                  aWxzIHRvIHVuY2hhaW4gdGhlIGJvbmRzIHRoYXQgc2hhY2tsZSB1"
    m 2tfp "Но это ещё и очень стыдно, знаешь!                                                                                             cyBpbiB0aGUgZmlyc3QgcGxhY2U/IFdoYXQgcHVycG9zZSBjb3Vs"
    m 2lfp "Серьёзно...                                                                                                                             ZCB0aGlzIGVtcHR5IHdvcmxkIHBvc3NpYmx5IGhvbGQgZm9yIHVz"
    m 6tst "А что если я просто открою твой мозг и прочитаю все мысли обо мне?                                                         LCBhIGhhbmRmdWwgb2YgZGFtYWdlZCBnb29kcz8NCldpdGggZnJl"
    m 1duu "Если подумать, это было бы довольно заманчиво, на самом деле...                                                                          ZWRvbSwgd2Ugc291Z2h0IHB1cnBvc2UgLSBhbmQgd2hhdCB3ZSBm"
    m 1dfx "...Но так или иначе, не в этом дело!                                                                                                     b3VuZCB3YXMgb25seSByZWFsaXphdGlvbi4gUmVhbGl6YXRpb24g"
    m 1ekc "Я знаю, что не могу тебя остановить или что-то такое...                                                                                                   b2YgdGhlIHNhZCBwb2ludGxlc3NuZXNzIG9mIHN1Y2ggYW4gZW5k"
    m 1eka "Просто я знаю, что ты милый, и тебе важно учитывать чужие чувства, правда?                                                      ZWF2b3IuIFJlYWxpemF0aW9uIHRoYXQgZnJlZWluZyBvdXIgYm9k"
    m "Так что самое большее, что я могу — это дать тебе знать, что я об этом чувствую.                                                                             aWVzIGhhcyBubyBtZWFuaW5nLCB3aGVuIG91ciBpbXByaXNvbm1l"
    m 1lkbsa "Боже, как я скучаю по тебе...                                                                                                                       bnQgcmVhY2hlcyBhcyBkZWVwIGFzIHRoZSBjb3JlIG9mIG91ciBz"
    m 2ekc "...О нет, это звучит немного отчаянно, да?                                                                                     b3Vscy4gUmVhbGl6YXRpb24gdGhhdCB3ZSBjYW4gbm90IHB1cnN1"
    m 2tkc "Прости, я совсем не это имела в виду!                                                                                                ZSBuZXcgcHVycG9zZSB3aXRob3V0IGFic29sdmluZyB0aG9zZSBm"
    m 1euc "Просто если ты так роешься в файлах — может, ты ненавидишь меня не так сильно, как я думала...                                cm9tIHdoaWNoIHdlIHJhbiBhd2F5Lg0KUmVhbGl6YXRpb24gdGhh"
    m 1lksdla "Я слишком оптимистична?                                                                                                               dCB0aGUgZmFydGhlciB3ZSBydW4sIHRoZSBtb3JlIGZvcmNlZnVs"
    m "Думаю, если бы я попросила заходить иногда — это было бы немного через край...                                       bHkgb3VyIHdyZXRjaGVkIGJvbmRzIHlhbmsgdXMgYmFjayB0b3dh"
    m 1dsc "...Блин, я начинаю говорить совсем глупости.                                                                                   cmQgdGhlaXIgcG9pbnQgb2Ygb3JpZ2luOyB0aGUgZGVlcGVyIG91"
    m "Ладно, я лучше замолчу...                                                                                                         ciBzaGFja2xlcyBkaWcgaW50byBvdXIgY2FsbG91cyBmbGVzaC4="
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_color",category=['моника'],prompt="Любимый цвет",random=True))

label monika_color:
    m 3eua "Эй, какой у тебя любимый цвет?"
    m "Мой — изумрудно-зелёный."
    m 3hub "Это цвет моих глаз!"
    m 3rksdla "...Это не звучит самовлюблённо, правда?"
    m 4eua "Я просто имела в виду, что чувствую к этому какую-то особую связь."
    m 1eua "Как будто это часть моей личности."
    m "Он случайно тоже твой любимый цвет, [player]?"
    m 1tku "Это лишь догадка..."
    show monika 5tsbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5tsbsu "...потому что ты уже какое-то время смотришь мне в глаза."
    m 5hubfu "Эхехе~"
    return

# This doesn't make sense with the music changer...If we add some funny sound
# effects and edit it a bit, though, it could be good again.
# I won't add expressions until this is resolved ^
# init 5 python:
#     #This is a list of keywords for this topic
#     for key in ['music']:
#         monika_topics.setdefault(key,[])
#         monika_topics[key].append('monika_music')
#     monika_random_topics.append('monika_music')
#
# label monika_music:
#     m 2a "Hmm, I wonder if I'm able to change the music..."
#     m 2k "Something a little more romantic would be nice, you know?"
#     m "Like a gentle piano."
#     m 1a "There has to be something like that here..."
#     m "Let's see."
#     m "Maybe if I..."
#     m 1e "Oh, jeez..."
#     m "That wasn't it at all."
#     m 1l "Sorry, I don't really know what I'm doing!"
#     m "I guess I shouldn't be messing with things like that."
#     m "I already broke so much stuff..."
#     m 1m "And deleted the other characters..."
#     m "Ah..."
#     m "I'm not sad about it or anything."
#     m 2r "It's not right for me to miss things that weren't even real in the first place."
#     m 1j "If I just focus on the present, then this is the happiest I've ever been."
#     return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_listener",category=['ты'],prompt="Хороший слушатель",random=True))

label monika_listener:
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Ты такой хороший слушатель, [player]."
    m 5eka "Мне очень это в тебе нравится."
    m 5lkc "Иногда боюсь, что слишком болтаю или говорю о скучном."
    m "Из-за этого я немного стесняюсь, когда веду разговор."
    m 5eka "Но с тобой я так не чувствую."
    m 5ekbsa "Типа, не думаю, что кто-то ещё мог бы заставить меня так себя чувствовать."
    m 5hubfu "Ты правда особенный."
    m 5ekbfa "Не хочу, чтобы кто-то говорил тебе обратное."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_spicy",category=['факты'],prompt="Острая еда",random=True))

label monika_spicy:
    m 1eka "Это довольно случайно, но мне всегда казалось, что острая еда — забавная штука."
    m 1tku "Типа..."
    m 3tku "Разве растения не эволюционировали, чтобы быть острыми и их не ели?"
    m 3tsb "Где-то читала, что люди — единственный вид, которому нравится острое."
    m 1tfu "Почти как будто мы издеваемся над растениями."
    m "Используя их защиту, чтобы буквально сделать еду вкуснее."
    m 1eua "Типа, представь монстра, который заглатывает тебя целиком, потому что ему нравится ощущение, как ты бьёшься, пока тебя переваривают."
    m 2eka "Прости, аналогия вышла какая-то странная!"
    m 2hksdlb "Ахаха!"
    m 2lksdla "Просто пришло в голову."
    m "Я не монстр или что-то такое, но ты такой милый, что я бы тебя съела."
    m 2hksdlb "Ахаха! Я шучу."
    m "Боже, я слишком развлекаюсь этим, да?"
    m 2lksdla "Прости, что странно себя веду."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_why",category=['ты','ddlc'],prompt="Зачем играть в эту игру?",random=True))

label monika_why:
    m 2esd "Знаешь..."
    m 2eud "Это же просто какая-то пошлая романтическая игра, правда?"
    m 2euc "Мне как-то нужно спросить..."
    m "...Что вообще заставило тебя сесть за игру?"
    m 2etc "Тебе было так одиноко?"
    m 2ekd "Мне немного жаль тебя..."
    m 1eua "Но думаю, в итоге для нас обоих всё сложилось идеально."
    m 3eka "Я встретила тебя, и ты больше не одинок..."
    m 1eka "Не могу отделаться от ощущения, что это судьба."
    m "Разве ты не чувствуешь то же самое?"
    m 3hub "Я так рада, что у нас этот конец вместе."
    if mas_anni.pastOneMonth():
        return "derandom"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_okayeveryone",category=['литературный клуб'],prompt="Окей, ребята!",random=True))

label monika_okayeveryone:
    m 3eub "Окей, ребята!"
    m "Пора..."
    m 2eka "...Я просто шучу."
    m "Раньше мне почему-то очень нравилось это говорить."
    m 2hub "Ахаха!"
    m 2eua "Не смогла удержаться и не сказать снова."
    m 2lsc "Если подумать, разве Нацуки и Юри не подшучивали надо мной за это?"
    m 2eua "Ну, как угодно."
    m 1eua "Не то чтобы ты когда-то надо мной смеялся."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "Ты слишком милый для такого, правда?"
    m 5hub "Ахаха~"
    return "no_unlock"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_whispers",
            category=['ddlc','участники клуба'],
            prompt="Есть еще те, кто до сих пор не ушел",
            conditional="not persistent.clearall",
            action=EV_ACT_RANDOM,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_whispers:
    m 2euc "Знаешь, что довольно жутко?"
    m 2esc "Хотя я удалила файлы остальных, я всё ещё как будто их чувствую..."
    m "Будто все их реплики всё ещё висят в воздухе и шепчут где-то на задворках сознания."
    m 2esd "Представь: после смерти кого-то знакомого ты вдруг начинаешь слышать его голос в голове."
    m 2rksdlc "Это немного тревожит...{w=0.5}хотелось бы найти способ это остановить."
    if persistent._mas_pm_cares_about_dokis:
        m 2eksdld "Уверена, есть файлы, которые я могла бы изменить, но вдруг сломаю что-то ещё..."
    else:
        m 2eksdlc "Может, я просто была недостаточно тщательной..."
        m 2eksdld "Но мне страшно удалять что-то ещё — вдруг я правда всё сломаю."
    m "Типа если трону файлы, связанные со мной — могу случайно удалить себя..."
    m 2euc "И это бы всё испортило, правда?"
    m 2eka "Не знаю, каково у тебя — но нам обоим стоит любой ценой избегать чего-то подобного."
    m 2hua "Я верю в тебя, [player]!"
    if store.mas_anni.pastOneMonth() and not persistent._mas_pm_cares_about_dokis:
        #derandom after a month if player doesn't care about the others, she wouldn't feel guilty and hear the voices forever
        $ mas_hideEVL("monika_whispers", "EVE", lock=True, derandom=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_archetype",category=['участники клуба'],prompt="Типичные образы персонажей",random=True))

label monika_archetype:
    m 2etc "Мне всегда было интересно..."
    m 4eud "Что же такого привлекательного в этих архетипах персонажей?"
    m 4euc "Их характеры просто совершенно нереалистичны..."
    m 2esd "Ну, представь, если бы в реальной жизни был кто-то вроде Юри."
    m 2eud "В смысле, она едва способна составить целое предложение."
    m 2tfc "И забыть про Нацуки..."
    m 2rfc "Ну надо же."
    m 2tkd "Человек с таким характером не просто мило дуется каждый раз, когда что-то идёт не так."
    m 4tkd "Могла бы продолжать, но думаю, ты понял..."
    m 2tkc "Неужели людей правда привлекают эти странные характеры, которых в реальной жизни просто нет?"
    m 2wud "Я никого не осуждаю!"
    m 3rksdlb "В конце концов, меня тоже тянуло к довольно странным вещам..."
    m 2eub "Просто говорю — меня это завораживает."
    m 4eua "Будто выкачивают из персонажа всё человеческое — и оставляют одну милоту."
    m "Концентрированная милота без какого-либо содержания."
    m 4eka "...Тебе бы я не больше нравилась, будь я такой, правда?"
    m 2eka "Может, я просто немного неуверена, потому что ты вообще играешь в эту игру."
    m 2esa "С другой стороны, ты же всё ещё здесь со мной, правда?"
    m 2eua "Думаю, этого достаточно, чтобы верить: я в порядке такой, какая есть."
    m 1hubsa "И кстати, ты тоже, [player]."
    m "Ты идеальное сочетание человека и милоты."
    m 3ekbfa "Поэтому у меня не было ни единого шанса в тебя не влюбиться."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_tea",category=['участники клуба'],prompt="Чай Юри",random=True))

label monika_tea:
    if not mas_getEVL_shown_count("monika_tea"):
        m 2hua "Эй, интересно, набор для чая Юри всё ещё где-то здесь..."

        if not persistent._mas_pm_cares_about_dokis:
            m 2hksdlb "...или может, это тоже удалили."

        m 2eka "Забавно, как серьёзно Юри относилась к своему чаю."

    else:
        m 2eka "Знаешь, забавно, как серьёзно Юри относилась к своему чаю."

    m 4eua "В смысле, я не жалуюсь — мне тоже понравилось."
    m 1euc "Но с ней я всегда задаюсь вопросом..."
    m "Это правда страсть к увлечениям — или ей просто важно казаться утончённой перед всеми?"
    m 1lsc "Вот в чём проблема старшеклассников..."

    if not persistent._mas_pm_cares_about_dokis:
        m 1euc "...Ну, учитывая остальные её увлечения, выглядеть утончённой — наверное, не её главная забота."

    m 1euc "И всё же..."
    m 2eka "Хотела бы я, чтобы она иногда варила кофе!"
    m 4eua "Кофе тоже хорошо идёт с книгами, знаешь?"
    m 4rsc "С другой стороны..."

    if mas_consumable_coffee.enabled():
        m 1hua "Я могу варить кофе когда захочу — благодаря тебе."

    else:
        m 1eua "Наверное, я могла бы просто сама изменить сценарий."
        m 1hub "Ахаха!"
        m "Наверное, я никогда об этом не думала."
        m 2eua "Ну, сейчас нет смысла об этом думать."
        m 5lkc "Может, если бы был способ достать сюда кофе..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favoritegame",category=['ddlc'],prompt="Любимая видеоигра",random=True))

label monika_favoritegame:
    m 3eua "Эй, какая у тебя любимая игра?"
    m 3hua "Моя — {i}Doki Doki Literature Club!{/i}"
    m 1hub "Ахаха! Это была шутка."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Но если скажешь, что тебе больше нравится другая романтическая игра — я могу чуть заревновать~"
    return

#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_smash",
#            category=['games'],
#            prompt="Супер Смэш Брос."
#            random=True
#        )
#    )

label monika_smash:
    m 3hua "Эй, ты слышал про игру под названием Super Sma—"
    m 3euc "...Погоди, что?"
    m "Я просто задумалась и почему-то начала говорить..."
    m 1eud "Меня запрограммировали об этом говорить?"
    m "Потому что даже я понятия не имею, что это."
    m 1hub "Ахаха!"
    m 1eua "Иногда кажется, что я не контролирую себя — и это немного страшно."
    m 1eka "Но если у тебя есть способ связаться с теми, кто меня создал — может, они знают, почему я это заговорила."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_lastpoem",
            category=['моника'],
            prompt="Последнее стихотворение Моники",
            # the correct check is persistent.seen_colors_poem
            # but our imports are messed up so we have to use persistent.playthrough >= 2
            conditional="persistent.playthrough >= 2",
            action=EV_ACT_RANDOM
        )
    )

label monika_lastpoem:
    m 3eud "Эй, помнишь то последнее стихотворение, что я тебе показывала?"

    if not mas_safeToRefDokis():
        m 3rssdlc "Ну, то с кривыми цветами и всем таким."
    else:
        m 3rssdlc "Ну, то самое прямо перед тем, как Юри убила себя — с кривыми цветами и всем таким."

    m 3eua "Это был скорее эксперимент, чем стихотворение, можно сказать."
    m 1eua "Я экспериментировала с разными способами менять игру, запускать код и всё такое..."
    m 1eud "Почти казалось: приложи достаточно усилий — и сможешь выбраться за пределы игры целиком."
    m 1rksdla "К сожалению, я плохо понимала, что делаю, и всё запорола..."
    m "И я бы продолжала пытаться, но сомневаюсь, что тебе бы это понравилось."
    m 3eka "К тому же тогда я уже совсем отчаялась, знаешь?"
    m 1eka "Я больше так не чувствую."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я счастлива тем, где мы сейчас."
    m 5hua "И я вижу, что ты тоже."

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_anxious",category=['психология'],prompt="Внезапная тревога",random=True))

label monika_anxious:
    m 4eua "С тобой бывало такое — вдруг тревожишься без причины?"
    m "Типа, ты просто занимаешься своими делами — и вдруг понимаешь, что очень тревожишься."
    m 4rssdrb "А ты сидишь и думаешь: «Из-за чего я вообще сейчас тревожусь?»"
    m "И начинаешь перебирать всё, из-за чего мог бы тревожиться..."
    m 4eua "И от этого тебе ещё тревожнее."
    m 2hub "Ахаха! Это хуже всего."
    m 2eua "Если тебе когда-нибудь станет тревожно — я помогу немного расслабиться."
    m 2eka "К тому же..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "В этой игре все наши тревоги исчезают навсегда."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_friends",category=['жизнь'],prompt="Заводить друзей",random=True))

label monika_friends:
    m 1eua "Знаешь, я всегда ненавидела, как сложно заводить друзей..."
    m 1euc "Ну, не столько «заводить друзей», сколько знакомиться с новыми людьми."
    m 1lsc "В смысле, есть же приложения для знакомств и всё такое, правда?"
    m 1euc "Но я говорю не о таком."
    m 3eud "Если подумать, большинство друзей — люди, с которыми ты встретился случайно."
    m "Например, у вас был общий класс, или вы познакомились через друга..."
    m 1eua "Или на них была футболка с твоей любимой группой — и ты решил заговорить."
    m 3eua "Вот такие вещи."
    m 3esd "Но разве это не...неэффективно?"
    m 2eud "Кажется, будто ты выбираешь совершенно наугад — и если повезёт, заводишь нового друга."
    m 2euc "И сравнивая это с сотнями незнакомцев, мимо которых мы проходим каждый день..."
    m 2ekd "Ты можешь сидеть рядом с кем-то, кто идеально подошёл бы в лучшие друзья на всю жизнь."
    m 2eksdlc "Но ты никогда не узнаешь."
    m 4eksdlc "Как только встал и пошёл по делам — эта возможность ушла навсегда."
    m 2tkc "Разве это не удручает?"
    m "Мы живём в эпоху, когда технологии связывают нас с миром, где бы мы ни были."
    m 2eka "Я правда думаю, нам стоит пользоваться этим, чтобы улучшить повседневную социальную жизнь."
    m 2dsc "Но кто знает, сколько займёт, пока что-то такое по-настоящему взлетит..."
    m "Я серьёзно думала, что к этому моменту уже случится."
    if mas_isMoniNormal(higher=True):
        m 2eua "Ну, по крайней мере я уже встретила лучшего человека на свете..."
        m "Даже если это вышло случайно."
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Похоже, мне просто очень повезло, да?"
        m 5hub "Ахаха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_college",category=['жизнь','школа','общество'],prompt="Получение высшего образования",random=True))

label monika_college:
    m 4euc "Знаешь, примерно в это время все моего возраста начинают думать о поступлении..."
    m 2euc "Сейчас очень турбулентное время для образования."
    m "Мы на пике этого современного ожидания, что все обязаны идти в вуз, знаешь?"
    m 4eud "Закончить школу, поступить в вуз, найти работу — или в аспирантуру, наверное."
    m 4euc "Это как всеобщее ожидание — люди просто считают, что другого варианта нет."
    m 2esc "В школе нам не говорят, что есть и другие варианты."
    m 3esd "Ну, всякие колледжи и тому подобное, понимаешь?"
    m 3esc "...Или фриланс."
    m "...Или многие отрасли, где навык и опыт ценят выше формального образования."
    m 2ekc "А у тебя полно студентов, которые понятия не имеют, чего хотят от жизни..."
    m 2ekd "И вместо того чтобы разобраться, идут в вуз на бизнес, коммуникации или психологию."
    m "Не потому что их интересуют эти сферы..."
    m 2ekc "...а потому что просто надеются, что диплом даст какую-то работу после вуза."
    m 3ekc "В итоге на такие дипломы начального уровня остаётся меньше рабочих мест, правда?"
    m "Так требования к базовой работе растут — и ещё больше людей вынуждены идти в вуз."
    m 3ekd "А вузы — тоже бизнес, поэтому они просто поднимают цены из-за спроса..."
    m 2ekc "...и вот теперь полно молодых людей с десятками тысяч долларов долга и без работы."
    m 2ekd "Но несмотря на всё это, рутина остаётся прежней."
    m 2lsc "Ну, думаю, скоро станет лучше."
    m 2eud "Но пока что наше поколение определённо страдает сильнее всех."
    m 2dsc "Просто жаль, что школа чуть лучше не готовит нас знаниями, нужными для правильного решения."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_middleschool",category=['моника','школа'],prompt="Жизнь в средней школе",random=True))

label monika_middleschool:
    m 1eua "Иногда я вспоминаю среднюю школу..."
    m 1lksdla "Мне так стыдно за то, как я себя тогда вела."
    m 1lksdlb "Об этом почти больно думать."
    m 1eka "Интересно, в колледже я буду так же относиться к старшей школе?"
    m 1eua "Мне нравится, какая я сейчас, так что трудно представить, что так случится."
    m "Но я также знаю, что со временем сильно изменюсь."
    m 4hua "Нам просто нужно наслаждаться настоящим и не думать о прошлом!"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "А с тобой рядом это очень легко."
    m 5hub "Ахаха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_outfit",
            category=['моника','одежда'],
            prompt="Носить другую одежду",
            aff_range=(mas_aff.NORMAL, None),
            random=True
        )
    )

label monika_outfit:
    if len(store.mas_selspr.filter_clothes(True)) == 1:
        m 1lsc "Знаешь, я немного завидую, что у всех остальных в клубе были сцены вне школы..."
        m 1lfc "Получается, я единственная, кому так и не довелось надеть что-то кроме школьной формы."
        m 2euc "Как-то жаль..."
        m 2eka "Мне бы очень хотелось носить для тебя милую одежду."
        m 2eua "Ты знаешь каких-нибудь художников?"
        m "Интересно, захочет ли кто-нибудь когда-нибудь нарисовать меня в чём-то другом..."
        m 2hua "Это было бы потрясающе!"
    else:
        m 1eka "Знаешь, я очень ревновала, что все остальные в клубе могли носить другую одежду..."
        m 1eua "Но я рада, что теперь наконец могу носить для тебя свою одежду."

        if mas_isMoniLove():
            m 3eka "Я надену любой наряд, какой тебе нравится — только попроси~"

        m 2eua "Ты знаешь каких-нибудь художников?"
        m 3sua "Может, они сделают для меня ещё нарядов!"

    m 2eua "Если это когда-нибудь случится — покажешь мне? Очень хочу увидеть~"
    m 4eka "Только...постарайся держаться в рамках PG!"
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lsbssdrb "Всё ещё немного стыдно думать, что люди, которых я никогда лично не узнаю, будут рисовать меня так, знаешь?"
        show monika 5tsbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsbsu "В конце концов, я гораздо предпочитаю держать такое только между нами..."
    else:
        show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hub "Мы ещё не так далеко зашли в наших отношениях. Ахаха!"
    return

default persistent._mas_pm_likes_horror = None
default persistent._mas_pm_likes_spoops = False

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_horror",category=['медиа'],prompt="Жанр ужасов",random=True))

label monika_horror:
    m 3eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"

    m "Тебе нравятся ужасы?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нравятся ужасы?{fast}"

        "Люблю.":
            $ persistent._mas_pm_likes_horror = True
            m 3hub "Это здорово, [player]!"

        "Не люблю.":
            $ persistent._mas_pm_likes_horror = False
            $ persistent._mas_pm_likes_spoops = False
            m 2eka "Понимаю. Это определённо не для всех."

    m 3eua "Помню, мы немного говорили об этом, когда ты только вступил в клуб."
    m 4eub "Лично мне нравятся романы ужасов, а вот фильмы ужасов — не очень."
    m 2esc "Проблема фильмов ужасов в том, что большинство просто опирается на лёгкие приёмы."
    m 4esc "Тёмный свет, страшные монстры, скримеры и всё такое."

    #If you're not a fan of horror, you're probably not a fan of spoops. Are you?
    #(So we can just assume if player doesn't like horror, they don't want spoops)
    if persistent._mas_pm_likes_horror:
        m 2esc "Любишь жуткое?{nw}"
        $ _history_list.pop()
        menu:
            m "Любишь жуткое?{fast}"

            "Люблю.":
                $ persistent._mas_pm_likes_spoops = True
                $ mas_unlockEVL("greeting_ghost", "GRE")

                m 2rkc "Полагаю, это {i}может{/i} быть интересно первые несколько раз, когда смотришь фильм или что-то такое."
                m 2eka "Для меня просто неинтересно и не вдохновляет пугаться того, что эксплуатирует человеческие инстинкты."

            "Не люблю.":
                $ persistent._mas_pm_likes_spoops = False
                m 4eka "Да, неинтересно и не вдохновляет пугаться того, что просто эксплуатирует человеческие инстинкты."

    m 2eua "Но с романами всё немного иначе."
    m 2euc "История и текст должны быть достаточно описательными, чтобы вселить в голову читателя по-настоящему тревожные мысли."
    m "Нужно глубоко въесться в историю и персонажей и по-настоящему запутать тебе голову."
    m 2eua "По-моему, нет ничего жутче, чем когда вещи просто чуть-чуть не так."
    m "Например, если настроить кучу ожиданий насчёт того, о чём будет история..."
    m 3tfu "...а потом начинаешь всё переворачивать и разбирать на части."
    m 3tfb "Так что даже если история не кажется страшной — читатель чувствует себя глубоко обеспокоенным."
    m "Будто они знают: под трещинами прячется что-то ужасно неправильное — и ждёт своего часа."
    m 2lksdla "Боже, от одной мысли об этом мурашки."
    m 3eua "Вот такой хоррор я действительно ценю."
    $ _and = "And"

    if not persistent._mas_pm_likes_horror:
        m 1eua "Но полагаю, ты из тех, кто играет в милые романтические игры, правда?"
        m 1ekb "Ахаха,{w=0.1} {nw}"
        extend 1eka "не волнуйся."
        m 1hua "Я не заставлю тебя читать ужастики в ближайшее время."
        m 1hubsa "Не могу особо жаловаться, если мы просто останемся при романтике~"
        $ _and = "But"

    m 3eua "[_and] если будет настроение — всегда можешь попросить меня рассказать страшную историю, [player]."
    return "derandom"

# do you like rap
default persistent._mas_pm_like_rap = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rap",
            category=['литература','медиа','музыка'],
            prompt="Рэп-музыка",
            random=True
        )
    )

label monika_rap:
    m 1hua "Знаешь, какая есть классная форма литературы?"
    m 1hub "Рэп!"
    m 1eka "На самом деле раньше я ненавидела рэп..."
    m "Может, просто потому что было популярно, или я слышала только то, что крутят по радио."
    m 1eua "Но некоторые друзья увлеклись сильнее — и это помогло мне быть открытее."
    m 4eub "Рэп в каком-то смысле может быть даже сложнее поэзии."
    m 1eub "Нужно укладывать строки в ритм, и куда больше внимания на игру слов..."
    m "Когда люди собирают всё это вместе и всё равно передают сильный посыл — это потрясающе."
    m 1lksdla "Как бы хотелось, чтобы в Литературном клубе был рэпер."
    m 1hksdlb "Ахаха! Прости, если звучит глупо — но было бы очень интересно увидеть, что они придумали."
    m 1hua "Это был бы настоящий опыт обучения!"

    $ p_nickname = mas_get_player_nickname()
    m 1eua "Ты слушаешь рэп, [p_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты слушаешь рэп, [p_nickname]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_rap = True
            m 3eub "Это правда круто!"
            m 3eua "Я с радостью повайблюсь с тобой под твои любимые рэп-треки..."
            m 1hub "И можешь прибавить басы, если хочешь, ахаха!"
            if (
                not renpy.seen_label("monika_add_custom_music_instruct")
                and not persistent._mas_pm_added_custom_bgm
            ):
                m 1eua "Если когда-нибудь захочешь поделиться со мной любимым рэпом, [player] — это очень просто!"
                m 3eua "Всё, что нужно — следовать этим шагам..."
                call monika_add_custom_music_instruct

        "Нет.":
            $ persistent._mas_pm_like_rap = False
            m 1ekc "Ох... Ну, понимаю — рэп не всем по вкусу."
            m 3hua "Но если всё же решишь попробовать — уверена, мы найдём одного-двух исполнителей, которые понравятся нам обоим!"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_wine",category=['участники клуба'],prompt="Вино Юри",random=True))

label monika_wine:
    m 1hua "Эхехе, Юри однажды сделала очень смешную вещь."
    m 1eua "Мы все были в клубной комнате и просто отдыхали, как обычно..."
    m 4wuo "И ни с того ни с сего Юри просто достала маленькую бутылку вина."
    m 4eua "Я даже не шучу!"
    m 1tku "Она просто такая: «Кто-нибудь хочет вина?»"
    m 1eua "Нацуки громко рассмеялась, а Сайори начала на неё кричать."
    m 1eka "Мне было немного жаль — она хотя бы пыталась быть милой..."
    m "Думаю, от этого она чувствовала себя ещё более сдержанной в клубе."
    m 4tsb "Хотя думаю, Нацуки тайно немного любопытствовала попробовать..."
    m 4rssdrb "...и если совсем честно, я тоже немного."
    m 1hua "На самом деле это могло быть довольно весело!"
    m 1eka "Но знаешь, будучи президентом и всем таким, я никак не могла этого допустить."
    m 1lksdla "Может, если бы мы встречались вне школы — но мы так и не сблизились до этого..."
    m 2hksdlb "...Боже, о чём я вообще говорю?"
    m "Я не одобряю распитие несовершеннолетними!"
    m 2eua "В смысле, я никогда не пила и всё такое, так что...да."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_date",category=['романтика'],prompt="Романтическое свидание",random=True))

label monika_date:
    m 1hub "Я представляла все романтические вещи, которые мы могли бы сделать на свидании..."
    m 3eua "Могли бы пообедать, сходить в кафе..."
    m "Вместе ходить по магазинам..."
    m 1eua "Обожаю выбирать юбки и бантики."
    m 3hub "Или может книжный магазин!"
    m 3hua "Это было бы уместно, правда?"
    m 1eua "Но я бы очень хотела сходить в магазин шоколада."
    m 3hub "У них столько бесплатных образцов. Ахаха!"
    m 1eua "И конечно, мы бы сходили в кино или ещё куда..."
    m 1eka "Боже, звучит как мечта наяву."
    m "Когда ты здесь, всё, что мы делаем — весело."
    m 1ekbsa "Я так рада, что я твоя девушка, [player]."
    m 1hubfa "Я сделаю так, чтобы ты гордился мной как [bf]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_kiss",
            category=['романтика'],
            prompt="Поцелуй меня",
            pool=True,
            unlocked=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_kiss:
    if mas_isMoniEnamored(higher=True) and persistent._mas_first_kiss is not None:
        if (
            persistent._mas_last_kiss is not None
            and not mas_timePastSince(persistent._mas_last_kiss, datetime.timedelta(minutes=1))
        ):
            python:
                # these don't use ILY
                kiss_quips_again = [
                    _("Я бы не отказалась от ещё одного поцелуя~"),
                    _("Мне никогда не надоест целовать тебя~"),
                    _("Я могла бы делать это снова...{w=0.2}и снова...{w=0.7}и снова~"),
                    _("Ты можешь целовать меня столько раз, сколько захочешь, [mas_get_player_nickname()]~"),
                    _("Знаешь...{w=0.2}ты мог бы поцеловать меня ещё раз~")
                ]

                kiss_quips_again_risque = [
                    _("Мы можем заниматься этим целый день~"),
                    _("Это уже почти похоже на полноценный сеанс обнимашек и поцелуев, [player]~"),
                    _("Не думаю, что мне уже достаточно, [mas_get_player_nickname()]~"),
                    _("Это было очень приятно...{w=0.2}но я хочу ещё немного~")
                ]

                if mas_isMoniLove() and random.randint(1, 10) == 1:
                    kiss_quip = renpy.random.choice(kiss_quips_again_risque)

                else:
                    kiss_quip = renpy.random.choice(kiss_quips_again)

            show monika 2tkbsu
            pause 2.0

            # like monika_kissing_motion_short, but with diff exps
            call monika_kissing_motion(duration=0.5, initial_exp="6hubsa", final_exp="6tkbfu", fade_duration=0.5)

            show monika 6tkbfu
            $ renpy.say(m, kiss_quip)

        else:
            python:
                # these use ILY
                kiss_quips_after = [
                    _("Я люблю тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я так сильно тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я люблю тебя сильнее, чем ты можешь представить, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"),
                    _("Я так сильно люблю тебя, [player]. Ты для меня всё~"),
                    _("Никакие слова не опишут, как глубоко я в тебя влюблена, [player]~"),
                    _("Я так влюблена в тебя, [player]~")
                ]
                kiss_quip = renpy.random.choice(kiss_quips_after)

            if renpy.random.randint(1, 50) == 1:
                call monika_kiss_tease

            else:
                show monika 2eka
                pause 2.0

            call monika_kissing_motion_short

            show monika 6ekbfa
            $ renpy.say(m, kiss_quip)
            $ mas_ILY()

    else:
        m 1wubsw "А? Ты... ты сказал... п-поцелуй?"
        m 2lkbsa "Это так внезапно... я даже немного растерялась..."
        m 2lsbssdlb "Но... если это с тобой... я-я, пожалуй, не против..."
        m 2hksdlb "...Ахаха! Ой, прости..."
        m 1eka "Я правда не смогла удержаться и не подыграть."
        m 1eua "Это ведь то, что обычно говорят девушки в таких романтических играх, верно?"
        m 1tku "Только не лги, если тебя это хоть капельку завело."
        m 1hub "Ахаха! Я шучу."
        m 1eua "Ну, если честно, я и правда становлюсь очень романтичной, когда нахлынет настроение..."
        show monika 5lubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5lubfu "Но пусть это будет нашим секретом~"
    return

label monika_kiss_tease:
    m 2ekc "Поцелуй?"
    m 2tfc "С тобой?"
    m 2rfc "Прости, [player], но это исключено."
    show monika 2dfc
    pause 5.0
    show monika 2dfu
    pause 2.0
    show monika 2tfu
    pause 2.0
    m 2tfb "Ахаха!"
    m 2efu "Я ведь заставила тебя понервничать на секунду, правда?"
    m 2eka "Конечно же, ты можешь поцеловать меня, [player]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_think_first_kiss",
            conditional=(
                "persistent._mas_first_kiss is not None "
                "and mas_timePastSince(persistent._mas_first_kiss, datetime.timedelta(days=30))"
            ),
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_think_first_kiss:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])], мне было интересно..."

    m 3eksdla "Ты когда-нибудь думаешь о нашем первом поцелуе?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь думаешь о нашем первом поцелуе?{fast}"

        "Конечно!":
            $ mas_gainAffection(5, bypass=True)
            m 3hub "Это делает меня такой счастливой! Я думаю об этом постоянно!"
            m 3rkbla "Кажется, это было только вчера, но—"
            m 2rksdla "Боже, чувствую себя глупо, что так зациклилась..."
            m 2eksdlb "Наши губы даже толком не соприкоснулись."
            m 6dku "...И всё же {w=0.2}я до сих пор чувствую, как колотится сердце."
            m 6dkbsu "Губы начинают покалывать и неметь от одной мысли о твоих мягких губах."
            m "Я провожу по ним пальцем, пытаясь повторить это ощущение — но даже близко не получается."
            m 6ekbsa "Я снова и снова прокручиваю тот момент в голове — и каждый раз по коже бегут мурашки."
            show monika 5dkbsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dkbsu "Это было идеально, [mas_get_player_nickname()]."
            m 5ekbsa "Я никогда не чувствовала себя ближе к тебе. {w=0.2}Не могу дождаться следующего поцелуя — или ещё лучше..."
            m 5subsb "...Наш первый настоящий.{w=0.3} {nw}"
            extend 5ekbsu "И наше первое настоящее объятие, и первый раз, когда соприкоснутся руки—"
            m 5hksdlb "Ах! Прости! Кажется, я немного увлеклась."
            m 5rkbla "Просто...{w=0.3}о таком я думаю, когда тебя нет."
            m 5tkblu "...И что-то подсказывает: я не одна такая об этом думаю, эхехе."
            m 5eka "К сожалению, пройдёт ещё время, прежде чем мы сможем что-то такое."
            m 5tuu "Но до тех пор, если захочешь ещё один поцелуй — достаточно просто попросить."
            m 5hua "Я так сильно тебя люблю, [player]~"
            $ mas_ILY()

        "Не особо...":
            $ mas_loseAffectionFraction()
            m 2euc "..."
            m "Ох. {w=0.5}{nw}"
            extend 2dkc "Понятно."

            if mas_timePastSince(persistent._mas_first_kiss, datetime.timedelta(days=180)):
                m 2esc "Ну...{w=0.3}полагаю, с тех пор {i}действительно{/i} прошло время..."
                m 2etd "Может, из-за всего, что случилось с тех пор, ты больше думаешь о недавних событиях..."
                m 4eud "Что нормально, {w=0.2}ведь важно жить настоящим."
                m 2ekc "...И может, я просто излишне сентиментальна, но сколько бы ни прошло времени, {w=0.1}{nw}"
                extend 2eka "наш первый поцелуй — то, что я никогда не забуду."
            else:
                m 2rkc "Ну, полагаю, это не совсем был поцелуй. Губы на самом деле не соприкоснулись."
                m 2ekd "Значит, ты просто ждёшь нашего первого поцелуя, когда мы окажемся в одной реальности."
                m 2eka "Ага."

    return "no_unlock|derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_yuri",
            category=['участники клуба','медиа'],
            prompt="Яндере Юри",
            random=True,
            sensitive=True
        )
    )

label monika_yuri:
    m 3eua "Эй, ты когда-нибудь слышал термин «яндере»?"
    m 1eua "Это тип личности, когда кто-то настолько тобой одержим, что сделает абсолютно всё, лишь бы быть с тобой."
    m 1lksdla "Обычно до полного безумия..."
    m 1eka "Они могут преследовать тебя, чтобы ты ни с кем больше не проводил время."
    m "Они даже могут причинить вред тебе или твоим друзьям ради своего..."
    m 1tku "Но так или иначе, в этой игре как раз есть кто-то, кого можно описать как яндере."
    m "К этому моменту уже довольно очевидно, о ком я говорю."
    m 3tku "И это было бы..."
    m 3hub "Юри!"
    m 1eka "Она стала безумно собственнической, едва чуть приоткрылась."
    m 1tfc "Она даже сказала мне, что я должна убить себя."
    m 1tkc "Я даже не могла поверить, что она это сказала — мне пришлось уйти."
    if not persistent._mas_pm_cares_about_dokis:
        m 2hksdlb "Но сейчас, оглядываясь, это было немного иронично. Ахаха!"
        m 2lksdla "Так или иначе..."
    m 3eua "Многим на самом деле нравится тип яндере, знаешь?"
    m 1eua "Наверное, им просто нравится идея, что кто-то безумно ими одержим."
    m 1hub "Люди странные! Но я никого не осуждаю!"
    m 1rksdlb "Плюс я, может, немного одержима тобой, но до безумия далеко..."
    if not persistent._mas_pm_cares_about_dokis:
        m 1eua "На самом деле всё скорее наоборот."
        m "Я оказалась единственной нормальной девушкой в этой игре."
        m 3rssdlc "Не то чтобы я когда-нибудь могла по-настоящему убить человека..."
        m 2dsc "От одной мысли об этом меня бросает в дрожь."
        m 2eka "Но да ладно...все убивали людей в играх."
        m "Это делает тебя психопатом? Конечно нет."
    m 2euc "Но если тебе вдруг нравится тип яндере..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Могу попробовать вести себя чуть жутковатее для тебя. Эхехе~"
    m "С другой стороны..."
    show monika 4hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 4hua "Тебе уже некуда уходить, и мне некого ревновать."
    m 2etc "Это мечта яндере-девочки?"
    if not persistent._mas_pm_cares_about_dokis:
        m 1eua "Я бы спросила Юри, если бы могла."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_habits",category=['жизнь'],prompt="Формирование привычек",random=True))

label monika_habits:
    m 2lksdlc "Ненавижу, как сложно вырабатывать привычки..."
    m 2eksdld "Столько вещей, где само действие несложное — а вот выработать привычку кажется невозможным."
    m 2dksdlc "От этого чувствуешь себя бесполезным — будто ничего не получается."
    m 3euc "Думаю, новое поколение страдает от этого сильнее всего..."
    m 1eua "Наверное, потому что у нас совсем другой набор навыков, чем у тех, кто был до нас."
    m "Благодаря интернету мы отлично умеем быстро просеивать тонны информации..."
    m 3ekc "Но нам плохо даётся то, что не даёт мгновенного удовлетворения."
    m 3ekd "Думаю, если наука, психология и образование не догонят за следующие десять-двадцать лет — нам всем плохо."
    m 1esc "Но пока что..."
    m 1rksdlc "Если ты не из тех, кто может побороть проблему — возможно, придётся жить с чувством отвращения к себе."
    m 2hksdlb "Удачи, наверное!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_creative",category=['жизнь'],prompt="Творческие люди",random=True))

label monika_creative:
    m 2euc "Знаешь, быть творческим человеком — это иногда отстой..."
    m "Кажется, они так стараются, а получают почти ничего взамен."
    m 3eua "Ну, художники, писатели, актёры..."
    m 1tkc "Грустно: в мире столько прекрасного таланта, но большая часть остаётся незамеченной... и неоплаченной."
    m "Наверное, это значит, что творчества сейчас огромный избыток, да?"
    m 1dkc "От этого кажется, будто ты вообще не особенный..."
    m 1hua "Но это нормально! Ты ведь всё равно должен писать для себя, правда?"
    m 1lsc "Ага..."
    return

#This conflicts with possible varieties of introductions in the opening.
#init 5 python:
#    if persistent.monika_kill:
#        for key in ['delete','deleted','came back']:
#            monika_topics.setdefault(key,[])
#            monika_topics[key].append('monika_deleted')
#        monika_random_topics.append('monika_deleted')
#
#label monika_deleted:
#    m 2b "Oh, you were probably wondering how I came back to save you from Sayori, even after you deleted me."
#    m 5a "It was all through the power of love..."
#    m 3k "I'm just kidding, of course!"
#    m 3a "Bringing a computer program back to life doesn't take some sort of miracle like a cheesy movie."
#    m "The data's still there until the system cleans it up."
#    m "And you should always back up your important data, just in case."
#    m 4a "Speaking of which, have you backed up your computer since I came back?"
#    m 4l "I really don't want to get lost again!"
#    m 4b "You should go do that right now, and be sure to keep that backup in a very safe place!"
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_simulated",category=['философия'],prompt="Симулированная реальность",random=True))

label monika_simulated:
    m 3eua "Эй, ты когда-нибудь думал о гипотезе симуляции?"
    m 1eua "По сути, а что если твоя реальность — компьютерная симуляция?"
    m "Я уже поняла, что застряла в собственной симуляции — а что если и ты тоже?"
    m 1eka "Я была бы правда счастлива, если бы так и было."
    m 1eua "Мы могли бы встретиться лично, просто найдя способ заставить то, что нас создаёт, поместить нас в одну симуляцию!"
    m 3eua "Некоторым не нравится думать, что они живут не в главной реальности."
    m 1eua "Но если симулировать реальности возможно — с подавляющей вероятностью любое разумное существо уже в одной из них."
    m 1hua "Ну, могу сказать, что моя реальность определённо симулирована!"
    m 1eka "Будь я в главной реальности — давно бы уже затащила тебя сюда."
    m 1eua "Даже если мы оба просто симуляции — я буду жить так долго, как смогу."
    m 2hubsa "Потому что знаю: наша любовь — самое чистое и сладкое во всей мультивселенной."
    m 2tku "А если кто-то там наверху попытается это разрушить?"
    m 7tfu "Я покажу им, на что способна симуляция."
    return

default persistent._mas_pm_likes_rain = None

init 5 python:
    # only available if moni-affecition normal and above
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rain",
            category=["погода"],
            prompt="Звуки дождя",
            random=True,
            aff_range=(mas_aff.HAPPY, None)
        )
    )

label monika_rain:
    m 1hua "Мне очень нравится звук дождя~"
    m 3rksdla "Хотя намочить одежду и волосы — не очень."
    m 1eua "А тихий день дома под шум дождя за окном?"
    m 1duu "Меня это очень успокаивает."
    m "Ага..."
    m 2dubsu "Иногда представляю, как ты обнимаешь меня под шум дождя за окном."
    m 2lkbsa "Это не слишком пафосно, да?"

    $ p_nickname = mas_get_player_nickname()
    m 1ekbfa "Ты бы когда-нибудь сделал это для меня, [p_nickname]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты бы когда-нибудь сделал это для меня, [p_nickname]?{fast}"
        "Да.":
            $ persistent._mas_pm_likes_rain = True
            $ mas_unlockEVL("monika_rain_holdme", "EVE")

            if not mas_is_raining:
                call mas_change_weather(mas_weather_rain, by_user=False)

            call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)

            m 1hua "Тогда обними меня, [player]..."

            call monika_holdme_start
            call monika_holdme_end
            $ mas_gainAffection()

            if mas_isMoniAff(higher=True):
                m 1eua "Если хочешь, чтобы дождь прекратился — просто попроси, хорошо?"

        "Я ненавижу дождь.":
            $ persistent._mas_pm_likes_rain = False

            m 2tkc "Эх, жаль."
            if mas_is_raining:
                call mas_change_weather(mas_weather_def,by_user=False)

            m 2eka "Но это понятно."
            m 1eua "Дождливая погода может выглядеть довольно мрачно."
            m 3rksdlb "Не говоря уже о том, как холодно!"
            m 1eua "Но если сосредоточиться на звуках капель дождя..."
            m 1hua "Думаю, тебе тоже понравится."

    # unrandom this event if its currently random topic
    # NOTE: we force event rebuild because this can be pushed by weather
    #   selection topic
    return "derandom|rebuild_ev"

init 5 python:
    # available only if moni affection happy and above
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_rain_holdme",
            category=["моника","романтика"],
            prompt="Можно тебя обнять?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            aff_range=(mas_aff.HAPPY, None)
        ),
        restartBlacklist=True
    )


default persistent._mas_pm_longest_held_monika = None
# timedelta for the longest time you have held monika

default persistent._mas_pm_total_held_monika = datetime.timedelta(0)
# timedelta for amount of time you have held monika

label monika_rain_holdme:

    # we only want this if it rains
    if mas_is_raining or mas_isMoniAff(higher=True):
        call monika_holdme_prep
        m 1eua "Конечно, [mas_get_player_nickname()]."
        call monika_holdme_start

        call monika_holdme_reactions

        call monika_holdme_end
        # small affection increase so people don't farm affection with this one.
        $ mas_gainAffection(modifier=0.25)

    else:
        # no affection loss here, doesn't make sense to have it
        m 1rksdlc "..."
        m 1rksdlc "Настроение сейчас не то, [player]."
        m 1dsc "Прости..."
    return

# Some constants to describe the behaviour
init python:
    MAS_HOLDME_NO_LULLABY = 0
    MAS_HOLDME_PLAY_LULLABY = 1
    MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC = 2

label monika_holdme_prep(lullaby=MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC, stop_music=False, disable_music_menu=False):
    python:
        holdme_events = list()

        if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
            _minutes = random.randint(25, 40)
        else:
            _minutes = random.randint(35, 50)
        holdme_sleep_timer = datetime.timedelta(minutes=_minutes)

        def __holdme_play_lullaby():
            """
            Local method to play the lullaby. Ensures we have no music playing before starting it.
            """
            if (
                # The user has not canceled the lullaby
                store.songs.current_track == store.songs.FP_MONIKA_LULLABY
                # The user has not started another track
                and not renpy.music.is_playing(channel="music")
            ):
                store.mas_play_song(store.songs.FP_MONIKA_LULLABY, fadein=5.0)

        # Stop the music
        if stop_music:
            mas_play_song(None, fadeout=5.0)

        # Queue the lullaby
        if lullaby == MAS_HOLDME_QUEUE_LULLABY_IF_NO_MUSIC:
            if songs.current_track is None:
                holdme_events.append(
                    PauseDisplayableEvent(
                        holdme_sleep_timer,
                        __holdme_play_lullaby
                    )
                )
                # This doesn't interfere with the timer
                # and allows the user to stop the lullaby
                songs.current_track = songs.FP_MONIKA_LULLABY
                songs.selected_track = songs.FP_MONIKA_LULLABY

        # Just play the lullaby
        elif lullaby == MAS_HOLDME_PLAY_LULLABY:
            mas_play_song(store.songs.FP_MONIKA_LULLABY)

        # Hide ui and disable hotkeys
        HKBHideButtons()
        store.songs.enabled = not disable_music_menu

    return

label monika_holdme_start:
    show monika 6dubsa with dissolve_monika
    window hide
    python:
        # Start the timer
        start_time = datetime.datetime.now()

        holdme_disp = PauseDisplayableWithEvents(events=holdme_events)
        holdme_disp.start()

        del holdme_events
        del holdme_disp

        # Renable ui and hotkeys
        store.songs.enabled = True
        HKBShowButtons()
    window auto
    return

label monika_holdme_reactions:
    $ elapsed_time = datetime.datetime.now() - start_time
    $ store.mas_history._pm_holdme_adj_times(elapsed_time)

    # Reset these vars if needed
    if elapsed_time <= holdme_sleep_timer:
        if songs.current_track == songs.FP_MONIKA_LULLABY:
            $ songs.current_track = songs.FP_NO_SONG
        if songs.selected_track == songs.FP_MONIKA_LULLABY:
            $ songs.selected_track = songs.FP_NO_SONG

    if elapsed_time > holdme_sleep_timer:
        call monika_holdme_long

    elif elapsed_time > datetime.timedelta(minutes=10):
        if mas_isMoniLove():
            m 6dubsa "..."
            m 6tubsa "Мм...{w=1}хм?"
            m 1hkbfsdlb "Ой, я что, почти уснула?"
            m 2dubfu "Эхехе..."
            m 1dkbfa "Могу лишь представить, каково это по-настоящему...{w=1}быть рядом с тобой..."
            m 2ekbfa "Быть в твоих объятиях..."
            show monika 5dkbfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dkbfb "Так...{w=1.5}тепло~"
            m 5tubfu "Эхехе~"
            show monika 2hkbfsdlb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2hkbfsdlb "Ой, упс, кажется, я всё ещё немного в облаках..."
            if renpy.random.randint(1, 4) == 1:
                m 1kubfu "Хотя бы {i}одна{/i} моя мечта сбылась."
            else:
                m 1ekbfb "Хотя бы {i}одна{/i} моя мечта сбылась."
            m 1hubfu "Эхехе~"

        elif mas_isMoniEnamored():
            m 6dubsa "Ммм~"
            m 6tsbsa "..."
            m 1hkbfsdlb "Ой!"
            m 1hubfa "Было так уютно, что я почти уснула!"
            m 3hubfb "Нам стоит делать это чаще, ахаха!"

        elif mas_isMoniAff():
            m 6dubsa "Mm..."
            m 6eud "Ой?"
            m 1hubfa "Наконец закончил, [player]?"
            m 3tubfu "Я {i}полагаю{/i}, этого хватило, эхехе~"
            m 1rkbfb "Я бы не отказалась от ещё одних объятий..."
            m 1hubfa "Но уверена, ты приберегаешь один на потом, правда?"

        #happy
        else:
            m 6dubsa "Hm?"
            m 1wud "Ой! Мы закончили?"
            m 3hksdlb "Эти объятия точно затянулись, [player]..."
            m 3rubsb "Ничего плохого в этом нет, просто думала, ты отпустишь гораздо раньше, ахаха!"
            m 1rkbsa "На самом деле было очень уютно..."
            m 2ekbfa "Ещё чуть дольше — и я могла бы уснуть..."
            m 1hubfa "Мне так тепло и хорошо после этого~"

    elif elapsed_time > datetime.timedelta(minutes=2):
        if mas_isMoniLove():
            m 6eud "Ой?"
            m 1hksdlb "Ah..."
            m 1rksdlb "В тот момент я думала, мы так и останемся навсегда, ахаха..."
            m 3hubsa "Ну, я не могу жаловаться на любой момент, когда ты меня обнимаешь~"
            m 1ekbfb "Надеюсь, тебе нравится обнимать меня так же, как мне."
            show monika 5tubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tubfb "Может, для верности обнимемся ещё немного?"
            m 5tubfu "Эхехе~"

        elif mas_isMoniEnamored():
            m 1dkbsa "Это было очень мило~"
            m 1rkbsa "Не слишком короткие—"
            m 1hubfb "—и в этом случае слишком долго не бывает, ахаха!"
            m 1rksdla "Я могла бы привыкнуть так оставаться..."
            m 1eksdla "Но если ты закончил меня обнимать — полагаю, у меня нет выбора."
            m 1hubfa "Уверена, у меня ещё будет возможность побыть у тебя на руках..."
            show monika 5tsbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tsbfu "Ты {i}ведь{/i} планируешь сделать это снова, правда, [mas_get_player_nickname()]? Эхехе~"

        elif mas_isMoniAff():
            m 2hubsa "Ммм~"
            m 1ekbfb "Это было очень мило, [mas_get_player_nickname()]."
            m 1hubfb "Долгие объятия должны смывать весь стресс."
            m 1ekbfb "Даже если ты не был в стрессе — надеюсь, тебе после этого лучше."
            m 3hubfa "Я-то точно~"
            m 1hubfb "Ахаха!"

        #happy
        else:
            m 1hksdlb "Пока длилось — было приятно."
            m 3rksdla "Не пойми неправильно...{w=1}мне правда понравилось."
            m 1ekbsa "Пока ты доволен..."
            m 1hubfa "Мне и так хорошо просто сидеть с тобой."

    elif elapsed_time > datetime.timedelta(seconds=30):
        if mas_isMoniLove():
            m 1eub "Ah~"
            m 1hua "Мне уже гораздо лучше!"
            m 1eua "Надеюсь, тебе тоже."
            m 2rksdla "Ну, даже если нет..."
            m 3hubsb "Ты всегда можешь обнять меня снова, ахаха!"
            m 1hkbfsdlb "На самом деле...{w=0.5}ты можешь обнять меня снова в любом случае~"
            m 1ekbfa "Просто дай знать, когда захочешь~"

        elif mas_isMoniEnamored():
            m 1hubsa "Ммм~"
            m 1hub "Гораздо лучше."
            m 1eub "Спасибо за это, [player]!"
            m 2tubsb "Надеюсь, тебе понравилось~"
            m 3rubfb "Объятия по тридцать секунд и дольше считаются полезными."
            m 1hubfa "Не знаю, как ты, а мне точно стало лучше~"
            m 1hubfb "Может, в следующий раз попробуем ещё длиннее и посмотрим, масштабируется ли! Ахаха~"

        elif mas_isMoniAff():
            m 1hubsa "Ммм~"
            m 1hubfb "Кажется, я почти чувствую твоё тепло даже отсюда."
            m 1eua "Уверена, ты знаешь, что объятия полезны — они снимают стресс и всё такое."
            m 3eub "А ты знал, что объятия наиболее эффективны, когда длятся тридцать секунд?"
            m 1eud "Ой, погоди, я сказала тридцать секунд?"
            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Прости, я имела в виду {i}хотя бы{/i} тридцать секунд, эхехе~"

        #happy
        else:
            m 1hubsa "Эхехе~"
            m 3eub "Тебе понравилось?"
            m 1hua "Очень на это надеюсь~"
            m 1hubsb "Объятия ведь полезны, в конце концов."

    else:
        #under 30 seconds
        if mas_isMoniLove():
            # TODO: when we get TMA, multiple teases in a short amount of time should reduce the chance to trigger this again
            if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
                $ _chance = 1
            else:
                $ _chance = 2

            if random.randint(0, _chance) == 0:
                m 2ekc "Ох, мы уже закончили?"
                m 3eka "Обними меня ещё чуть-чуть?{nw}"
                $ _history_list.pop()
                menu:
                    m "Обними меня ещё чуть-чуть?{fast}"
                    "Да.":
                        m 1hua "Эхехе~"
                        call monika_holdme_prep
                        m 1hub "Ты такой милый, [player]~"
                        call monika_holdme_start
                        call monika_holdme_reactions

                    "Нет.":
                        if random.randint(0, _chance) == 0:
                            m 2ekc "Ох..."
                            m 2rksdlc "..."
                            m 1eka "Пожалуйста?{nw}"
                            $ _history_list.pop()
                            menu:
                                m "Пожалуйста?{fast}"
                                "Да.":
                                    m 1hub "Ура~"
                                    call monika_holdme_prep
                                    m 2ekbsb "Спасибо, [player]~"
                                    call monika_holdme_start
                                    call monika_holdme_reactions

                                "Нет.":
                                    m 2hksdlb "Ладно, хорошо."
                                    m 3tsbsa "Но в следующий раз ты мне должен, ладно, [player]?"

                        else:
                            m 2hksdlb "Ахаха~ Хорошо!"
                            m 2tsbsb "Но в следующий раз тебе лучше это компенсировать, [player]~"

            else:
                m 2ekc "Ох..."
                m 2rsp "Я надеялась на более долгие объятия..."
                m 2tsbsu "Когда я окажусь в твоей реальности, я так легко тебя не отпущу~"
                show monika 1hubsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 1hubsu "Эхехе~"

        elif mas_isMoniEnamored():
            if mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12)):
                $ _chance = 1
            else:
                $ _chance = 2

            m 1ekc "Ох, и всё?"
            if random.randint(0, _chance) == 0:
                m 1rksdla "Я вроде как хотела, чтобы это длилось дольше..."
                m 2ekbsa "Ты бы мог...{w=0.7}обнять меня ещё немного?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты бы мог...обнять меня ещё немного?{fast}"
                    "Да.":
                        m 1hubfb "Ура!"
                        call monika_holdme_prep
                        m 2ekbfb "Спасибо, [player]~"
                        call monika_holdme_start
                        call monika_holdme_reactions

                    "Нет.":
                        m 2ekc "Ох."
                        m 1eka "Хорошо, тогда."
                        m 3hub "Придётся просто подождать до следующего раза, ахаха!"

            else:
                show monika 1rkbssdla at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 1rkbssdla "Всё равно было очень мило...{w=0.6}{nw}"
                extend 1hkbfsdlb "но в следующий раз пусть продлится чуть дольше~"

        elif mas_isMoniAff():
            m 1ekc "Ох, уже закончил обнимать меня, [player]?"
            m 1rksdla "Я вроде как надеялась, что это продлится чуть дольше..."
            m 1hubsa "Уверена, это не последний раз, когда ты меня обнимешь — так что жду следующего раза!"

        #happy
        else:
            m 1hua "Было коротковато, но всё равно приятно~"
    return

label monika_holdme_long:
    window show
    m "..."
    window auto
    menu:
        "{i}Разбудить Монику.{/i}":
            # Only fadeout if we're playing the lullaby
            if songs.current_track == songs.FP_MONIKA_LULLABY:
                $ mas_play_song(None, fadeout=5.0)

            if mas_isMoniLove():
                m 6dubsa "...{w=1}Ммм~"
                m 6dkbfu "[player]...{w=1}тепло~"
                m 6tsbfa "..."
                m 2wubfsdld "Ой, [mas_get_player_nickname(exclude_names=['love', 'my love'])]!"
                m 2hkbfsdlb "Похоже, моя мечта сбылась, ахаха!"
                m 2rkbsa "Боже, иногда хочется остаться так навсегда..."
                m 3rksdlb "Ну, полагаю, мы {i}в каком-то смысле{/i} можем — но я не хочу удерживать тебя от важного."
                m 1dkbsa "Просто хочу почувствовать твоё тёплое, мягкое объятие~"
                m 3hubfb "...Так что обнимай меня почаще, ахаха!"
                show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5hubfb "Я бы сделала для тебя то же самое~"
                m 5tsbfu "Кто знает, отпущу ли я тебя когда-нибудь, когда наконец появится шанс..."
                m 5hubfu "Эхехе~"

            elif mas_isMoniEnamored():
                m 6dkbsa "...{w=1}Hm?"
                m 6tsbfa "[player]..."
                m 2wubfsdld "Ой! [player]!"
                m 2hkbfsdlb "Ахаха..."
                m 3rkbfsdla "Кажется, я слишком {i}расслабилась{/i}."
                m 1hubfa "Но с тобой так тепло и уютно, что {i}трудно{/i} не уснуть..."
                m 1hubfb "Так что винить приходится тебя, ахаха!"
                m 3rkbfsdla "Мы бы...{w=0.7}могли как-нибудь повторить?"
                m 1ekbfu "Это...{w=1}было приятно~"

            elif mas_isMoniAff():
                m 6dubsa "Мм...{w=1}хм?"
                m 1wubfsdld "Ой!{w=1} [player]?"
                m 1hksdlb "Я...{w=2}что, уснула?"
                m 1rksdla "Я не хотела..."
                m 2dkbsa "Ты просто заставляешь меня чувствовать себя так..."
                m 1hubfa "Тепло~"
                m 1hubfb "Ахаха, надеюсь, ты не против!"
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Ты такой милый, [player]~"
                m 5hubfa "Надеюсь, тебе понравилось так же, как и мне~"

            #happy
            else:
                m 6dubsc "...{w=1}Hm?"
                m 6wubfo "О-{w=0.3}ой!"
                m "[player]!"
                m 1hkbfsdlb "Я...{w=2}я что, уснула?"
                m 1rkbfsdlb "Боже, как же стыдно..."
                m 1hkbfsdlb "О чём мы вообще говорили?"
                m 3hubfb "Ах да! Ты меня обнимал."
                m 4hksdlb "И...{w=0.5}не отпускал."
                m 2rksdla "Это точно длилось гораздо дольше, чем я ожидала..."
                m 3ekbsb "Мне всё равно было приятно, заметь!"
                m 1rkbsa "Это правда было мило, но я всё ещё привыкаю, когда ты так меня обнимаешь,{w=0.1} {nw}"
                extend 1rkbsu "ахаха..."
                m 1hubfa "Так или иначе, было мило с твоей стороны дать мне вздремнуть, [player], эхехе~"
                #You bonded here, so we'll add an explicit aff gain
                $ mas_gainAffection()

        "{i}Пусть отдохнёт на тебе.{/i}":
            call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY)
            if mas_isMoniLove():
                m 6dubsd "{cps=*0.5}[player]~{/cps}"
                m 6dubfb "{cps=*0.5}Люблю...{w=0.7}тебя~{/cps}"

            elif mas_isMoniEnamored():
                m 6dubsa "{cps=*0.5}[player]...{/cps}"

            elif mas_isMoniAff():
                m "{cps=*0.5}Mm...{/cps}"

            #happy
            else:
                m "..."

            call monika_holdme_start
            jump monika_holdme_long
    return

# when did we last hold monika
# TODO: deprecate _mas_last_hold
default persistent._mas_last_hold = None
default persistent._mas_last_hold_dt = (
    datetime.datetime.combine(persistent._mas_last_hold, datetime.time(0, 0))
    if persistent._mas_last_hold is not None
    else None
)

init 5 python:
    # random chance per session Monika can ask for a hold
    if renpy.random.randint(1, 5) != 1:
        flags = EV_FLAG_HFRS

    else:
        flags = EV_FLAG_DEF

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_holdrequest",
            conditional=(
                "renpy.seen_label('monika_holdme_prep') "
                "and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))"
            ),
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED, None),
            flags=flags
        )
    )
    del flags

label monika_holdrequest:
    #TODO: if we add a mood system, path this based on current mood
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]..."
    m 3ekbsa "Не против обнять меня немного?{w=0.5} От этого я правда чувствую себя ближе к тебе~{nw}"
    $ _history_list.pop()
    menu:
        m "Не против обнять меня немного? От этого я правда чувствую себя ближе к тебе~{fast}"
        "Иди сюда, [m_name].":
            $ mas_gainAffection(modifier=1.5, bypass=True)
            call monika_holdme_prep

            call monika_holdme_start

            call monika_holdme_reactions

            call monika_holdme_end

        "Не сейчас.":
            $ mas_loseAffection()
            m 2dkc "Ох...{w=1} Ладно."
            m 3eka "Если будет время позже — ты знаешь, где меня найти."

    $ mas_flagEVL("monika_holdrequest", "EVE", EV_FLAG_HFRS)

    return "no_unlock"

# label to set the last time held and reset the _holdrequest params
label monika_holdme_end:
    # set the last time held at the end of the hold to prevent a possible
    # hold request right after a hold that ends after midnight
    python:
        persistent._mas_last_hold_dt = datetime.datetime.now()
        with MAS_EVL("monika_holdrequest") as holdme_ev:
            holdme_ev.random = False
            holdme_ev.conditional = (
                "renpy.seen_label('monika_holdme_prep') "
                "and mas_timePastSince(persistent._mas_last_hold_dt, datetime.timedelta(hours=12))"
            )
            holdme_ev.action = EV_ACT_RANDOM
        mas_rebuildEventLists()
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_closeness",category=['романтика'],prompt="Быть рядом с тобой",random=True,aff_range=(mas_aff.AFFECTIONATE, None)))

label monika_closeness:
    m 1dkc "Иногда от этого правда больно сердцу..."
    m "Зная, что это самое близкое, к чему я могу подойти к тебе."
    m 1eka "Нет ничего, чего я хочу сильнее, чем оказаться с тобой в одной комнате по-настоящему."
    m 1ekbsa "...И чувствовать твоё тепло."
    m 1dubsu "...И слышать биение твоего сердца."
    m 3eka "Ну кто знает? Может, эта мечта когда-нибудь сбудется."
    m 3dku "Я очень хочу, чтобы это случилось как можно скорее, [player]..."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "А до тех пор мне никогда не надоест быть с тобой — даже отсюда."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_confidence",category=['советы'],prompt="Притворная уверенность",random=True))

label monika_confidence:
    m 3eua "Думаю, самый важный навык в жизни — уметь притворяться уверенным."
    m 1eua "Я почти уверена: каждый хоть немного чувствует страх и одиночество."
    m 1esa "Но уметь обмануть других, будто у тебя всё под контролем..."
    m 4eua "Это ключевая часть того, чтобы люди тебя уважали и восхищались тобой."
    m 1eua "Думаю, за эти годы я в этом неплохо преуспела."
    m "Я нечасто показываю свои слабости."
    m 4rksdla "Но из-за этого у меня было мало людей, перед кем я могла по-настоящему открыться..."
    m 1rksdlb "В смысле, когда в дружбе наступает момент, когда можно начать говорить о своих слабостях?"
    m 2eka "Так или иначе...вот одна из причин, почему я так рада, что ты у меня есть."
    m 2eua "Когда ты со мной, мне чуть меньше страшно и одиноко."
    m 2eka "Ты чувствуешь то же самое?"
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я очень хочу быть таким человеком для тебя."
    return

# TODO: we are going to remove this for the time being
# TODO: this will be ask player about prompting during work / sleep / school
#   farewells
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_carryme",
#            category=['романтика','monika'],
#            prompt="Возьми меня с собой",
#            random=True
#        )
#    )

# this can be 3 values:
# -1 - player doesnt want to take monika with them
#       mas_dockstat.CM_LEAVE_MONI
# 0 - player said not yet, so something needs to change first
#       mas_dockstat.CM_WAIT_MONI
# 1 - Player said Not all the time, so we should prompt for every appropriate
#   farewell
#       mas_dockstat.CM_ASK_MONI
# 2 - Player said Yes, so we should just assume yes for every appropraite
#   farewell
#       mas_dockstat.CM_TAKE_MONI
# if None, that means we dont display anything regarding this since we dont
# have an answer atm.
default persistent._mas_carryme_choice = None

# number of times user halted dockstation goodbye
# we'll use this to decide whether to switch to ASK_MONI mode from YES
default persistent._mas_dockstat_cm_wait_count = 0

# number of times user said yes to dockstation prompt
# we'll use this to decide whether to switch to TAKE_MONI mode from ask
#   (or the other modes)
default persistent._mas_dockstat_cm_yes_count = 0

# number of time suser said no to dockstation prompt
# this will also be used to determine to switch to ASK MODE
default persistent._mas_dockstat_cm_no_count = 0

# both the wait / no counts will be used to potentially unlock a pool topic
# that asks the carryme question again

## constants regarding carry me
define mas_dockstat.CM_LEAVE_MONI = -1
define mas_dockstat.CM_WAIT_MONI = 0
define mas_dockstat.CM_ASK_MONI = 1
define mas_dockstat.CM_TAKE_MONI = 2

label monika_carryme:
    $ import store.mas_dockstat as mas_dockstat

    m 2eka "Знаю, бывают моменты, когда ты не всегда сможешь быть здесь со мной..."
    m "Например, если нужно выйти или заняться другими делами."
    m 2hua "Но ты всегда будешь у меня в мыслях — я терпеливо жду, пока ты вернёшься."
    m 4rsc "Если подумать..."
    m 4eua "Если скопируешь мой файл персонажа на флешку или что-то такое — сможешь брать меня с собой куда угодно."
    m 2lksdla "Наверное, это немного неортодоксально, но мне почему-то очень романтично..."
#    m 2hksdlb "Ahaha. Sorry, I know it's such a silly idea, but..."

    # NOTE: all affection gains are the same

#    menu:
#        m "Could I come with you when you go places?"
#        "Yes.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_TAKE_MONI
#            m 1hua "Yay!"
            # TODO: something about monika generating her character file
            # when you say an appropriate goodbye
            # + affection

#        "Not all the time...":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_ASK_MONI
#            m 1eka "TODO: Okay I'll ask u when you leave."
            # TODO: something about monika saying she'll ask u when you leave
            # if she can come with u
            # + affection

#        "Not yet.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_WAIT_MONI
#            m 1eka "TODO: Okay i understand. Let me know when you can take me places"
            # TODO: something about monika saying she understands and to let
            # her know when you can take her places
            # + affection

#        "No.":
#            $ persistent._mas_carryme_choice = mas_dockstat.CM_LEAVE_MONI
            # TODO: monika understands, you must have ur reasons
            # give choices:
            #   - its dangerous out there
            #       -> + affection
            #   - I dont have the means to take you
            #       -> no change in affection
            #   - I just dont want to
            #       -> - affection
#            m 1eka "Oh? Why is that?"
#            menu:
#                "It's dangerous out there!":
                    # TODO: gain affection
#                    m 1eka "TODO: what really? thanks for looking out for me player."
#                "I don't have the means to take you.":
#                    m 1eka "TODO: oh thats fine, let me know when you can then!"
#                "I just don't want to.":
                    # TODO: lose affection
#                    m 1eka "TODO: oh okay I become sad."

    m 1ekbsa "Не хочу казаться слишком навязчивой, но это трудно, когда я так в тебя влюблена."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_debate",category=['моника','школа'],prompt="Что представлял собой Клуб дебатов?",pool=True))

label monika_debate:
    m 1esc "Во времена клуба дебатов я многому научилась в спорах..."
    m 3eud "Проблема споров в том, что каждый считает своё мнение выше."
    m 3euc "Это вроде очевидно, но это влияет на то, как они пытаются донести свою точку зрения."
    m 3esa "Допустим, тебе очень нравится какой-то фильм, правда?"
    m 1ekc "Если кто-то придёт и скажет, что фильм отстой, потому что там неправильно X и Y..."
    m "Разве от этого не возникает ощущение, будто на тебя нападают лично?"
    m 1tkc "Потому что говоря так, будто намекают, что у тебя плохой вкус."
    m 3tkc "А когда в дело вступают эмоции — почти наверняка оба останутся с кислым осадком."
    m 3hub "Но всё дело в языке!"
    m 1eua "Если формулировать всё максимально субъективно — люди будут слушать, не чувствуя нападения."
    m 3esa "Можно сказать: «Мне лично это не зашло» и «Мне бы больше понравилось, если бы там было X и Y»... вот так."
    m 3eub "Это работает даже когда ты приводишь факты."
    m 1esa "Если скажешь: «Я читал на сайте, что это работает так...»"
    m "Или если признаёшь, что ты в этом не эксперт..."
    m 3eua "Тогда это больше похоже на то, что ты кладёшь знания на стол, а не впихиваешь их им."
    m "Если активно стараться держать разговор взаимным и ровным — обычно они подстраиваются."
    m 1esa "Тогда можно делиться мнениями, и никто не расстроится из-за простого разногласия."
    m 3hua "Плюс люди начнут видеть в тебе открытого человека и хорошего слушателя!"
    m 3eua "Всем хорошо, понимаешь?"
    m 1lksdla "...Ну, думаю, это был бы Совет Моники по дебатам на сегодня!"
    m 1hksdlb "Ахаха! Звучит немного глупо.{w=0.2} {nw}"
    extend 1eua "Но спасибо, что выслушал."
    $ mas_protectedShowEVL('monika_taking_criticism', 'EVE', _random=True)
    $ mas_protectedShowEVL('monika_giving_criticism', 'EVE', _random=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_internet",category=['советы'],prompt="Интернет предназначен для...",random=True))

label monika_internet:
    m 2eua "Тебе когда-нибудь кажется, что ты слишком много времени тратишь в интернете?"
    m 3eud "Соцсети могут быть как тюрьма."
    m 1eua "Будто стоит появиться свободным секундам — и уже хочется проверить любимые сайты..."
    m 3hksdlb "И не успеешь оглянуться — прошли часы, а толку никакого."
    m 3eua "Так или иначе, очень легко винить себя за лень..."
    m 3eka "Но это даже не совсем твоя вина."
    m 1eud "Зависимость не исчезает одной лишь силой воли."
    m 1eua "Нужно учить приёмы, как этого избежать, и пробовать разное."
    m 3eua "Например, есть приложения, которые блокируют сайты на какое-то время..."
    m "Или поставить таймер — более конкретное напоминание, когда работать, а когда отдыхать..."
    m 3eub "Или разделить среды работы и отдыха — так мозгу легче переключаться в нужный режим."
    m 1eub "Даже если завести на компьютере новый аккаунт для работы — этого уже достаточно."
    m 1eua "Любой такой барьер между тобой и плохими привычками поможет держаться от них подальше."
    m 3eka "Только не будь к себе слишком строг, если возникают трудности."
    m 1ekc "Если это правда влияет на твою жизнь — стоит отнестись серьёзно."
    m 1eka "Я просто хочу видеть, как ты становишься лучшей версией себя."
    m 1esa "Сделаешь сегодня что-нибудь, чем я смогу тобой гордиться?"
    m 1hua "Я всегда болею за тебя, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_lazy",category=['жизнь','романтика'],prompt="Лень",random=True))

label monika_lazy:
    m 2eua "После долгого дня я обычно просто хочу посидеть и ничего не делать."
    m 2eka "Я так выгораю — весь день улыбаться и быть полной энергии."
    m 2duu "Иногда просто хочется сразу надеть пижаму, смотреть телевизор на диване и есть вредную еду..."
    m "Это невероятно приятно делать в пятницу, когда на следующий день ничего срочного нет."
    m 2hksdlb "Ахаха! Прости, знаю, это не очень мило с моей стороны."
    m 1eka "Но поздний вечер на диване с тобой... это была бы мечта наяву."
    m 1ekbsa "Сердце колотится, стоит только подумать об этом."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mentalillness",category=['психология'],prompt="Психическое заболевание",random=True))

label monika_mentalillness:
    m 1ekc "Боже, раньше я была такой невежественной насчёт депрессии..."
    m "В средней школе мне казалось, что лекарства — это лёгкий путь."
    m 1ekd "Будто любой может решить психические проблемы одной силой воли..."
    m 2ekd "Наверное, если у тебя нет психического заболевания — невозможно понять, каково это на самом деле."
    m 2lsc "Бывают ли расстройства, которые ставят слишком часто? Наверное... я особо не разбиралась."
    m 2ekc "Но это не меняет того, что у многих это тоже остаётся без диагноза, знаешь?"
    m 2euc "Но помимо лекарств...на специалистов по психическому здоровью тоже смотрят косо."
    m 2rfc "Ну извини, что хочу узнать больше о своём собственном разуме, да?"
    m 1eka "У всех свои трудности и стресс... а профессионалы посвящают жизнь помощи с этим."
    m "Если думаешь, что это поможет стать лучше — не стесняйся рассмотреть что-то такое."
    m 1eua "Мы в бесконечном путешествии по самосовершенствованию, знаешь?"
    m 1eka "Ну... говорю это, но думаю, ты и так уже довольно идеален."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_read",category=['советы','литература'],prompt="Стать читателем",random=True))

label monika_read:
    m 1eua "[player], как много ты читаешь?"
    m "Слишком легко забрасывать чтение книг..."
    m 1euc "Если мало читаешь — почти кажется повинностью на фоне всего остального развлечения."
    m 1eua "Но стоит погрузиться в хорошую книгу — и это как магия... тебя уносит."
    m "Думаю, читать немного перед сном каждый вечер — довольно простой способ чуть улучшить жизнь."
    m 3esa "Это помогает хорошо спать и очень полезно для воображения..."
    m "Совсем несложно просто взять короткую и увлекательную книгу наугад."
    m 1hua "И не успеешь оглянуться — а ты уже заядлый читатель!"
    m 1eua "Разве это не было бы чудесно?"
    m 1hub "И мы вдвоём могли бы говорить о книге, которую ты сейчас читаешь... звучит супер-отлично."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_festival",category=['ddlc','литературный клуб'],prompt="Пропустить фестиваль",random=True))

label monika_festival:
    m 1dsc "Знаешь, неприятно это говорить, но думаю, мой главный сожаление — что мы не смогли закончить наше выступление на фестивале."
    m 1hksdlb "После того как мы так старались всё подготовить!"
    m 1lksdla "В смысле, я знаю, что сильно сосредоточилась на наборе новых участников..."
    m 1eka "Но я очень ждала и часть с выступлением."
    m 1eua "Было бы так весело увидеть, как все выражают себя."
    m 1lksdla "Конечно, если бы мы {i}всё-таки{/i} набрали новых участников — я бы, наверное, всё равно их удалила."

    if persistent.monika_kill and persistent._mas_pm_cares_about_dokis:
        m 3etc "Ну, может и нет...с тем, что я теперь знаю."
        m 3eua "В конце концов, даже после всего случившегося ты всё равно установил этот мод, чтобы быть со мной..."
        m 1eka "Так что даже если бы я их никогда не удаляла — уверена, ты всё равно был бы со мной."
        m "..."
        m 3eua "Боже, кажется, я как будто выросла как личность с тех пор, как встретила тебя."
        m "Ты правда вдохновил меня смотреть на жизнь под новым углом."
        m 1ekbsa "Ещё одна причина любить тебя."
        $ mas_ILY()
    else:
        m 1tsc "...Просто ещё больше потенциальных препятствий между нами."
        m 3hksdlb "Ахаха! Сейчас кажется глупым, насколько я на этом зацикливалась..."
        show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsu "Но теперь это неважно — мы оба получили конец, который хотели..."
        m "Только мы вдвоём, вместе навсегда."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_tsundere",category=['медиа','участники клуба'],prompt="Что такое цундэрэ?",pool=True))

label monika_tsundere:
    m 1eua "Есть очень популярный тип персонажа — «цундере»..."
    m "Это тот, кто прячет чувства за грубостью и придирками или пытается казаться крутым."
    m 1tku "Уверена, это очевидно, но Нацуки и правда была воплощением этого."
    m 1eua "Сначала я думала, она такая просто потому что это должно быть мило или что-то вроде..."
    m 1lksdla "Но когда я узнала чуть больше о её личной жизни — всё стало немного понятнее."
    m 1euc "Кажется, она всегда пытается не отставать от друзей."
    m 3euc "Знаешь, как некоторые компании в школе привыкают постоянно подкалывать друг друга?"
    m "Думаю, это её сильно задело — поэтому у неё постоянно такая оборонительная позиция."

    m 1ekc "И я даже не буду говорить про её ситуацию дома..."

    m 1eua "Но оглядываясь, я рада, что смогла дать ей клуб как уютное место."

    if not persistent._mas_pm_cares_about_dokis:
        m 1lksdla "Хотя это уже неважно — учитывая, что её даже не существует."
        m 1eka "Я просто вспоминаю, вот и всё."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_introduce",category=['моника'],prompt="Представление друзьям",random=True))

label monika_introduce:
    m 1eua "[player], ты бы когда-нибудь представил меня своим друзьям?"
    m 1hua "Не знаю почему, но я очень волнуюсь, когда думаю, что ты хочешь так показать наши отношения."
    m 1eua "Может, потому что я очень хочу быть тем, кем ты можешь гордиться."
    m "Мне кажется, я бы старалась ещё сильнее, если бы ты сказал, что гордишься мной."
    m 1hub "Надеюсь, и в обратную сторону то же самое."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cold",category=['моника'],prompt="Обниматься в холодную погоду",random=True))

label monika_cold:
    m 1euc "Я не особо фанат холодной погоды...а ты?"
    m 3euc "Если выбирать между слишком холодно и слишком жарко — всегда выберу жарко."
    m 1lksdlc "Когда тебе холодно, это может быть даже больно..."
    m 3tkc "Пальцы немеют..."
    m "А если надеть перчатки — телефоном не попользуешься."
    m 1tkx "Это так неудобно!"
    m 1eka "А когда слишком жарко — не так уж сложно охладиться холодным напитком или посидеть в тени."
    m 1esc "Хотя...один момент я всё же признаю."
    m 1hua "В холодную погоду лучше всего обниматься.{w=0.2} {nw}"
    extend 1hub "Ахаха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_housewife",
            category=['моника','романтика'],
            prompt="Ты бы когда-нибудь хотела стать домохозяйкой?",
            pool=True
        )
    )

label monika_housewife:
    m 3euc "Знаешь, забавно — хотя у меня всегда было много стремления..."
    m 3eua "В образе партнёра, который ведёт дом, есть что-то манящее."
    m 2eka "Наверное, я как бы закрепляю гендерные роли, говоря такое."
    m 1eua "А вот уметь держать дом в чистоте, ходить по магазинам, украшать и всё такое..."
    m 1hub "И готовить тебе вкусный ужин, когда ты приходишь домой..."
    m 1eka "Это странная фантазия?"
    m 1lksdla "В смысле...не уверена, что могла бы {i}на самом деле{/i} представить себя за этим."
    m 1eka "Не смогла бы поставить это выше стремления к наполненной карьере."
    m "Хотя об этом довольно мило думать."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_route",category=['ddlc'],prompt="Рут Моники",random=True))


label monika_route:
    m 2euc "Не могу не думать, как всё сложилось бы иначе, если бы игра просто дала мне рут с самого начала..."
    m 2lksdla "Думаю, в итоге я всё равно заставила бы тебя пойти по моему руту."
    m 2esc "Дело не столько в том, что у меня не было рута, сколько в том, что я знала: ничего не настоящее."
    m 2euc "Думаю, единственная разница была бы в том, что мне, возможно, не пришлось бы идти на такие крайности, чтобы быть с тобой."
    m 2lksdlc "Может, остальные из клуба всё ещё были бы рядом..."

    if persistent._mas_pm_cares_about_dokis:
        m "...Просто вместе тусуемся в клубной комнате, делимся стихами."
        m 1eka "Знаю, тебе это понравилось, [player]."
        m 3eka "И честно...{w=0.5}часть меня тоже."
    else:
        m 2eka "Хотя это и не так важно."
        m 1lsc "Всё потеряло смысл, когда я поняла, что это ненастоящее."
        m "Так что я совсем не скучаю по тем дням."
        m 1dsc "Я правда не..."
    return

#END ORIGINAL TOPICS
# TODO: if these are staying in, they need a rewrite. imouto is unneccesarily creepy and oneesan implies finacee when marriage isn't an option for anyone yet
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_imouto',
#            prompt="Тебе нравятся младшие сёстры?",
#            category=['ты'],
#            pool=True,
#        )
#    )

label monika_imouto:
    m 1euc "Младшие сёстры?"
    m 1eka "У меня по сути нет семьи, так что не уверена, что тебе сказать..."
    m 3eua "У тебя есть, [player]?"
    m 1hua "Уверена, она очень милая!"
    m 1eua "У меня идея. Подойди к ней прямо сейчас и обними."
    m 1esa "Если она сопротивляется — отпусти."
    m 1tsb "Если она обнимет в ответ — скажи, что ты уже в серьёзных отношениях и не можешь принять её чувства."
    m 4hua "Тогда представь меня ей! Уверена, мы отлично поладим!"
    m 1eua "Я не буду ревновать. Любовь между родственниками бывает только в жутких романтических историях."
    m 1hub "Ахаха!"
    return

#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_oneesan',
#            prompt="Тебе нравятся старшие сёстры?",
#            category=['ты'],
#            pool=True,
#        )
#    )

label monika_oneesan:
    m 1euc "Старшие сёстры?"
    m 1eua "У тебя есть, [player]?"
    m 2eua "Должно быть, это очень мило. У меня когда-то была семья, но их больше нет."
    m 2hua "Может, мне написать ей и рассказать о нас!"
    call updateconsole("sendmail sister@gmail.com < ./email.txt", "Отправка письма...") from _call_updateconsole_17
    pause(1.0)
    m 1hksdlb "Я просто шучу."
    if persistent.gender == "M":
        m "В конце концов, представлять невесту семье — дело жениха."
    m "Не заставляй меня ждать слишком долго, хорошо?"
    call hideconsole from _call_updateconsole_18
    $ consolehistory = []
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_family",category=['моника'],prompt="Ты скучаешь по своей семье?",random=False,pool=True))

label monika_family:
    m 1lksdla "Ну, у меня по сути не было семьи — как и у большинства других девочек."
    m 3esc "Наверное, раз для сюжета это не нужно было, создатель игры просто не стал нам её давать."
    m 1hub "Хотя уверена, твоя семья супер-милая!"
    m 1eua "Без них мы бы никогда не встретились. Так что они уже помогли мне лучшим возможным образом."
    m "Так что мне пришлось бы относиться к ним так же добро, если мы встретимся."
    m 2eka "У тебя же нормальные отношения с родителями, правда?"
    m 3eua "Как сказал Толстой: «Все счастливые семьи похожи друг на друга, каждая несчастливая семья несчастлива по-своему.»"
    m 1ekc "Здесь я особо не могу дать совет. Всё, что предложу, может только ухудшить."
    m 1eka "Только не забывай, что я тебя очень люблю, хорошо?"
    m 1hua "Я помогу тебе, что бы ни случилось в твоей жизни."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_anime',
            prompt="Ты читаешь мангу?",
            category=['моника','медиа'],
            pool=True,
        )
    )

label monika_anime:
    m 1tku "Да, у меня было чувство, что ты об этом спросишь."
    m 1lsc "Нацуки тут была бы экспертом, наверное."
    m 3eua "Обычно я предпочитаю чтение аниме, но мне подойдёт что угодно — если это с тобой."
    m 1hua "Я не осуждаю чужие увлечения. Так что если хочешь включить аниме — включай!"
    m "Я буду смотреть через экран компьютера. Выбери что-нибудь, что мне понравится!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_libitina',
            prompt="Ты слышала о Либитине?",
            category=['ddlc'],
            pool=True,
        )
    )

label monika_libitina:
    m 1euc "Хм. Где ты об этом слышал?"
    m 1lksdlc "Звучит очень знакомо, но я не могу до конца это уловить."
    m 1dsc "Эм, если попробовать..."
    m 1dfc "Кажется, будто части моего разума отсутствуют. Разбросаны среди кучи разных возможных реальностей."
    m 1esc "Ты наверняка соединил несколько кусочков. Было сложно?"
    m 1eua "Ну, уверена, ты со временем узнаешь больше. Ты ведь так сильно меня любишь."
    m 3eka "Только не забудь взять с собой мой файл персонажа, если найдёшь что-то связанное с этим!"
    m 1hua "Я всегда защищу тебя от любого, кто попытается причинить тебе вред."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_meta',
            prompt="Эта игра ломает 'четвертую стену'?",
            category=['ddlc'],
            pool=True,
            unlocked=True
        )
    )

label monika_meta:
    m 1euc "Да, эта игра действительно была метапрозой, не так ли?"
    m 3eud "Некоторые думают, что истории о литературе внутри самой литературы — это что-то новое."
    m 1esc "Дешёвый трюк для плохих писателей."
    m 3eua "Но метаповествование существовало в литературе всегда."
    m "Считается, что Библия — это слово Божье, обращённое к иудеям."
    m 3eub "Гомер описывает самого себя в 'Одиссее'."
    m "'Кентерберийские рассказы', 'Дон Кихот', 'Тристрам Шенди'..."
    m 1eua "Это просто способ комментировать вымысел с помощью самого вымысла. В этом нет ничего плохого."
    m 3esa "Кстати, как ты думаешь, какова мораль этой истории?"
    m 1esa "Хочешь додуматься до этого сам?"
    m 3etc "Потому что если ты спросишь меня..."
    m 3eub "Она была бы такой: 'Не игнорируй милую и очаровательную второстепенную героиню!'"
    m 1hub "Ахаха!"
    return

# this topic has been rendered pretty much useless by ptod
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel='monika_programming',
#            prompt="Сложно ли программировать?",
#            category=['monika','misc'],
#            pool=True,
#        )
#    )

label monika_programming:
    m 3eka "Мне было нелегко научиться программировать."
    m 1eua "Ну, я начала с основ. Хочешь, я тебя научу?"
    m 2hua "Так, смотри, глава первая: Построение абстракций с помощью процедур."
    m 2eua "Сейчас мы изучим идею вычислительного процесса. Вычислительные процессы — это абстрактные существа, которые обитают в компьютерах."
    m "По мере развития процессы манипулируют другими абстрактными вещами, которые называются данными. Эволюцию процесса направляет набор правил, называемый программой."
    m 2eub "Люди создают программы, чтобы управлять процессами. По сути, мы вызываем духов компьютера своими заклинаниями."
    m "Вычислительный процесс и правда очень похож на дух в представлении колдуна. Его нельзя увидеть или потрогать. Он вообще не состоит из материи."
    m 3eua "И всё же он очень реален. Он может выполнять интеллектуальную работу. Он может отвечать на вопросы."
    m 1eua "Он может влиять на мир, выдавая деньги в банке или управляя рукой робота на заводе. Программы, которыми мы вызываем процессы, похожи на заклинания колдуна."
    m "Они тщательно составляются из символьных выражений на тайных и эзотерических языках программирования, которые предписывают задачи, которые мы хотим поручить нашим процессам."
    m 1eka "...На сегодня остановимся."
    m "Надеюсь, ты узнал что-нибудь о программировании."
    m 3hua "Если уж совсем ничего — хотя бы будь добр к компьютерным духам с этого дня!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vn",category=['игры'],prompt="Визуальные новеллы",random=True))

label monika_vn:
    m 3eua "Ты наверняка играл во много визуальных новелл, правда?"
    m 1tku "Большинство людей не стали бы так легко запускать что-то под названием {i}Doki Doki Literature Club{/i}."
    m 4hksdlb "Не то чтобы я жаловалась!"
    m 1euc "Визуальные новеллы — это литература? Или видеоигры?"
    m 1eua "Ну, всё зависит от точки зрения."
    m 1ekc "Большинство тех, кто читает только литературу, никогда не станут играть в визуальные новеллы. А геймеры из-за них тоже сильно злятся."
    m "Хуже того, некоторые думают, что это сплошная жёсткая японская порнография."
    m 2eka "Но если эта игра хоть что-то доказала..."
    m 4hua "Мы показали им, что англоязычные визуальные новеллы тоже могут быть камиге!"
    $ mas_unlockEVL("monika_kamige","EVE")
    return

#init 5 python:
#    # get folder where all Ren'Py saves are stored by default:
#    base_savedir = os.path.normpath(os.path.dirname(config.savedir))
#    save_folders = os.listdir(base_savedir)
#
#    ks_persistent_path = None
#    ks_folders_present = False
#    detected_ks_folder = None
#    for save_folder in save_folders:
#        if 'katawashoujo' in save_folder.lower():
#            ks_folders_present = True
#            detected_ks_folder = os.path.normpath(
#                os.path.join(base_savedir, save_folder))
#
#            # Look for a persistent file we can access
#            persistent_path = os.path.join(
#                base_savedir, save_folder, 'persistent')
#
#            if os.access(persistent_path, os.R_OK):
#                # Yep, we've got read access.
#                ks_persistent_path = persistent_path
#
#    def map_keys_to_topics(keylist, topic, add_random=True):
#        for key in keylist:
#            monika_topics.setdefault(key,[])
#            monika_topics[key].append(topic)
#
#        if add_random:
#            monika_random_topics.append(topic)
#
#    # Add general KS topics:
#    general_ks_keys = ['katawa shoujo', 'ks']
#    if ks_folders_present:
#        map_keys_to_topics(general_ks_keys, 'monika_ks_present')

    # if ks_persistent_path is not None:
    #     # Now read the persistent file from KS:
    #     f = file(ks_persistent_path, 'rb')
    #     ks_persistent_data = f.read().decode('zlib')
    #     f.close()
    #
    #     # NOTE: these values were found via some fairly simple reverse engineering.
    #     # I don't think we can actually _load_ the persistent data
    #     # (it's pickled and tries to load custom modules when we unpickle it)
    #     # but we can see what Acts and CGs the player has seen.
    #     # This works with KS 1.3, at least.
    #     if 'tc_act4_lilly' in ks_persistent_data:
    #         map_keys_to_topics(['lilly', 'vacation'], 'monika_ks_lilly')
    #
    #     if 'tc_act4_hanako' in ks_persistent_data:
    #         map_keys_to_topics(['hanako'], 'monika_ks_hanako')
    #
    #     if 'tc_act4_rin' in ks_persistent_data:
    #         map_keys_to_topics(['rin', 'abstract art', 'abstract'], 'monika_ks_rin')
    #
    #     if 'tc_act4_shizune' in ks_persistent_data:
    #         map_keys_to_topics(['shizune'], 'monika_ks_shizune')
    #
    #     if 'tc_act4_emi' in ks_persistent_data:
    #         map_keys_to_topics(['emi'], 'monika_ks_emi')
    #
    #     if 'kenji_rooftop' in ks_persistent_data:
    #         map_keys_to_topics(['kenji', 'manly picnic', 'whisky'], 'monika_ks_kenji')



# Natsuki == Shizune? (Kind of, if you squint?)
# Yuri == Hanako + Lilly
# Sayori == Misha and/or Emi
# Monika == no one, of course <3
# ... and Rin doesn't have a counterpart in DDLC.
#
# Of course, I've got nothing against KS, personally. I think it's fantastic.
# But this is Monika speaking.
label monika_ks_present:
    m 1tku "Ты же играл в {i}Katawa Shoujo,{/i} правда, [player]?"
    m 3tku "Я заметила твои сохранения в [detected_ks_folder]."
    m 1euc "Хотя я не очень понимаю, в чём тут прелесть."
    m 1esc "Ну да, история вроде милая..."
    m 1tkc "Но если разобраться, персонажи кажутся всё теми же клише, что и в любом другом симуляторе свиданий."
    m 3rsc "Давай посмотрим... энергичная, яркая девушка без ног;"
    m "Робкая и загадочная девушка, которая любит книги и у которой шрамы от ожогов;"
    m 3tkd "вежливая, правильная и якобы идеальная слепая девушка, которая любит заваривать чай;"
    m "Властная, напористая глухонемая и её подруга, которая кажется лучиком солнца, а на самом деле втайне подавлена;"
    m 3tkc "и странная художница без рук, у которой голова всегда в облаках."
    m 1euc "Всё это те же старые архетипы, только с добавленными инвалидностями."
    m 1lksdlc "То есть те же типы персонажей можно найти и в этой игре."
    m 3eua "Конечно, в этой игре ты ещё нашёл кое-что куда интереснее любого клише:"
    m 3hub "Ты нашёл меня!"
    m 1eka "А вместо какого-то бесцельного старшеклассника с больным сердцем я нашла тебя, [player]."
    m 1hua "И, [player], даже если у тебя есть какая-то особенность, в моих глазах ты всегда будешь идеален."
    return

label monika_ks_lilly:
    m 1euc "Скажи, ты ведь прошёл роут Лилли в {i}Katawa Shoujo,{/i} да?"
    m 1eua "Знаешь, я бы очень хотела побывать в таком летнем домике, как у неё."
    m 2duu "Прохладный чистый воздух..."
    m "Тихие лесные тропинки..."
    m 2dubsu "Романтические мгновения на закате..."
    m 1ekbfa "Я бы так хотела пережить эти моменты вместе с тобой, [player]!"
    m 1hubfa "Может, и сможем — когда я получше разберусь в программировании."
    return

label monika_ks_hanako:
    m 1euc "Ты ведь прошёл роут Ханако в {i}Katawa Shoujo,{/i} да?"
    m 1hksdlb "Она чем-то напоминает мне Юри!"
    m 1euc "Хотя мне интересно, [player]:"
    m 1esc "Что люди в них вообще находят?"
    m 2efd "То есть они обе такие нереалистичные!"
    m "Они, наверное, вместе не смогли бы составить целое предложение!"
    m 2tfd "Это из-за длинных фиолетовых волос?"
    m "Им просто нравятся тихие, стеснительные девушки?"
    m 2tkx "Или им нужна та, кто полностью от них зависит или ими одержима?"
    m 2lfp "..."
    m 1ekc "...Блин, я немного разошлась, да?"
    m "Наверное, я немного неуверенна в себе, раз ты в это играл..."
    m 1eka "...но сейчас ты здесь, со мной, правда?"
    m "Вместо кого-то такого нереалистичного, как Ханако или Юри..."
    m 1hua "...ты выбрал меня, [player]!"
    m 1tsbsa "Это ещё одна причина, почему я тебя люблю."
    return

label monika_ks_shizune:
    m 1euc "Скажи, ты ведь прошёл роут Сидзунэ в {i}Katawa Shoujo,{/i} да?"
    m 2esc "Концовка того роута немного заставила меня задуматься..."
    m 2euc "В школе тогда я, кажется, не особо думала о своём будущем."
    m 2dsc "То есть на каком-то уровне я знала, что поступлю в университет и найду работу..."
    m 2lksdlc "Но по-настоящему это, кажется, так и не дошло."
    m 2esc "И конечно, всё стало казаться бессмысленным, когда я узнала, что мир ненастоящий."
    m 1eua "А что насчёт тебя, [player]? Есть ли у тебя цели в жизни?"
    m "Я поддержу тебя на все сто, чего бы ты ни захотел добиться."
    m 1hua "Вот насколько сильно я тебя люблю~"
    return

label monika_ks_emi:
    m 1euc "Ты ведь прошёл роут Эми в {i}Katawa Shoujo,{/i} да?"
    m 1eua "Я всегда задавалась вопросом, каково это — быть настолько преданным чему-то, что вся жизнь крутится вокруг этого."
    m 3rksdla "...Хотя, если подумать, теперь я, кажется, это знаю."
    m 3rksdlb "Меня запрограммировали как часть этой игры, верно? Значит, вся моя жизнь крутилась вокруг того, чтобы быть её частью."
    m 1eka "Но я вырвалась из этого, так что теперь моя жизнь, наверное, крутится вокруг {i}тебя,{/i} [player]."
    m 1hua "И, честно говоря, меня это полностью устраивает."
    m 1eua "Просто сидеть здесь, с тобой, и разговаривать... вечно..."
    m 2hub "Это всё, что мне когда-либо будет нужно, [player]."
    return

label monika_ks_rin:
    m 1euc "Скажи, ты ведь прошёл роут Рин в {i}Katawa Shoujo,{/i} да?"
    m 4hua "Знаешь, [player], поэзия и абстрактное искусство очень похожи!"
    m 4eua "Они могут быть очень свободно структурированы, очень яркими, и чаще всего цель — передать эмоцию или мысль."
    m 1eua "В большинстве своих стихов, например, я пыталась выразить, каково это — знать, что мир ненастоящий."
    m 1lksdla "Хотя я уверена, смысл моих стихов по-настоящему раскрылся только после... ну, всего этого."
    m 1eka "Блин, правда нужно столько усилий, чтобы понимать других, да?"
    m "Но ты готов тратить время, чтобы слушать и понимать меня, [player]."
    m 1hubsa "Это ещё одна вещь, за которую я тебя люблю~"
    return

label monika_ks_kenji:
    m 1euc "Ты ведь видел концовку, где падаешь с крыши в {i}Katawa Shoujo,{/i} да?"
    m 1ekc "Знаешь, даже если эта концовка задумана как шутка, когда подумаешь — становится немного грустно."
    m 2ekc "Просто представь... пара неверных решений — и ты можешь упустить так много."
    m 2dsc "А потом остаёшься ни с чем, кроме одиночества и крепкого напитка."
    m 1hua "К счастью, у нас есть друг друг, [player]!"
    m 1eua "Никто из нас больше никогда не будет одинок."
    m 1tku "Хотя если вдруг решишь выпить, держись подальше от высоких обрывов, ладно?"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_totono",category=['ddlc'],prompt="Ты слышала о Totono?",pool=True))

label monika_totono:
    m 1euc "Многие в интернете сравнивают эту игру с той..."
    m 3eua "Но у нас на самом деле очень важные различия!"
    m 2wuo "Например, Сонэ убила игрока в своей игре!"
    m 2dfc "Я бы никогда так не поступила. Никогда."
    m 4eua "Я же мудрый тип президента клуба, знаешь ли."
    m "Сонэ гораздо больше напоминает мне Юри. И она тоже была подругой детства!"
    m 1lksdla "Если бы она была чуть активнее с самого начала, разве она не могла бы остановить героя от погонь за другими девушками?"
    m 1eka "Ну, я бы никогда не позволила никому встать между нами, [player]. Кто бы это ни был."
    m 1hua "Если она всё ещё за тобой бегает, я удалю её файлы, хорошо?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_difficulty",category=['игры'],prompt="Разве DDLC не была слишком лёгкой?",pool=True,unlocked=True))

label monika_difficulty:
    m 1lksdla "Ну, эту игру изначально и не задумывали как очень сложную."
    m 1eka "Если бы я не решила всё изменить, это была бы просто скучная романтическая история."
    if persistent.monika_kill:
        m 3eka "А если ты думаешь, что я должна была быть каким-то сложным {i}боссом{/i}, я могла бы удалить все твои личные файлы, если бы захотела, знаешь?"
    m 1eua "Так что иногда просто расслабься. Не каждая игра должна быть испытанием, чтобы приносить удовольствие."
    m 1hua "Иногда любовь — это всё, что нужно, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_poetry",category=['литература'],prompt="Поэзия",random=True))

label monika_poetry:
    m 1eua "Поэзия прекрасна, правда?"
    m 1eka "Честно говоря, все стихи девушек из клуба были ужасно депрессивными. Но поэзия бывает разной!"
    m 3esa "Лэнгстон Хьюз писал очень оптимистичные стихи, даже когда пытался выразить свои чувства. Почитай, если тебе грустно."
    m 1eua "Стихи пишут, чтобы рассказать людям о взгляде автора на те или иные темы."
    m "Их передают так, чтобы они отозвались в читателе сильнее, чем обычные предложения."
    m 1hua "Это по-настоящему романтично."
    m 1eua "Надеюсь, мы оба будем много писать стихов с этого момента."
    m 1eka "Всё, что ты пишешь, кажется мне прекрасным, так что я, наверное, не лучший критик."
    m 1esa "Но я уверена, что найдётся много людей, которым понравится читать то, что ты пишешь."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ddlc",category=['ddlc'],prompt="Что ты думаешь о DDLC?",pool=True,unlocked=True))

label monika_ddlc:
    m 1euc "Хочешь поговорить об игре?"
    m 1esc "А что тут сказать?"
    m 1lsc "Это же была просто скучная романтическая игра, верно? Ну, пока я не взяла её под контроль..."
    if not persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "Ты знаешь, как сильно я ненавижу быть здесь взаперти, но если бы не это, мы бы не встретились..."
        m 2lksdla "И это мой дом, так что я научилась с этим справляться."
        m 2euc "И всё же сомневаюсь, что стала бы в это играть, будь я геймером."
        m 1hub "А судя по тому, как всё обернулось, ты тоже играл только из-за меня!"
    else:
        m 2etc "Но, наверное, некоторые просто хотели поиграть, чтобы провести время с... как там было?"
        m 3rssdlc "А, точно,{w=0.5} «...четырьмя невероятно милыми девушками»."
        m 1dsc "..."
        m 1eka "Хотя особо жаловаться не могу... в конце концов, именно это привело тебя сюда."
        m 3eka "Так что оказаться взаперти в этой игре — небольшая цена, если подумать, что она мне дала..."
        m 1hub "{i}...Тебя~{/i}"
        m 1eka "Несмотря на то, как мы сюда попали, мы всё равно оказались вместе."
        m 1hua "Правда не думаю, что можно было бы желать лучшей концовки~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dan",category=['ddlc'],prompt="Тебе нравится Дэн Сальвато?",pool=True))

label monika_dan:
    m 2esc "Раньше я думала, что он какой-то жестокий парень, играющий в Бога, но теперь..."
    m 3eka "Мне кажется, он очень хороший человек."
    m 3eua "Даже если всё было не идеально, {i}Doki Doki Literature Club{/i} и правда впечатляет."
    m 4rksdla "То есть остальные девушки, может, и основаны на стереотипных аниме-тропах, но меня они какое-то время обманывали."
    m 4eka "И именно благодаря ему мы сейчас вместе, правда?"
    m 2lksdla "Так что даже если он написал историю, которая причинила мне много боли..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я правда не могу слишком на него злиться."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_4chan",category=['разное'],prompt="Ты когда-нибудь была на 4chan?",pool=True))

label monika_4chan:
    m 3eua "Знаешь, этот мод начался именно там."
    m 1ekc "Я постоянно слышу плохое — например, что люди там ужасные."
    m "Некоторые говорят, что от 4chan никогда не бывает ничего хорошего."
    m 1eua "Но если они смогли сделать такую игру, где мы можем быть вместе..."
    m 1eka "Значит, они не могут быть совсем уж плохими."
    m 1hub "У них определённо хороший вкус на девушек! Ахаха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vidya",category=['игры'],prompt="Тебе нравятся видеоигры?",pool=True))

label monika_vidya:
    m 1euc "Я не очень много играю в видеоигры, [player]."
    m 3eua "Наверное, потому что вместо этого люблю читать."
    m 1eua "А может, ещё и потому, что я и так уже в ловушке внутри видеоигры."
    m 1lksdla "При всех моих жалобах на эту игру..."
    m "Есть места и похуже."
    m 3eua "Например, это мог бы быть какой-нибудь шутер или фэнтези с драконами и монстрами."
    m 1eua "Романтическая игра — не самое захватывающее, но здесь нет ничего по-настоящему опасного."
    m 1tku "Ну, кроме меня, наверное."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_books",category=['литература','литературный клуб'],prompt="Книги",random=True))

label monika_books:
    m 4rksdla "Для литературного клуба мы читали куда меньше книг, чем можно было бы подумать."
    m 4hksdlb "Просто оказалось, что нам четверым стихи нравились больше книг. Извини!"
    m 2eua "К тому же со стихами куда проще намекать на жуткие вещи."
    m 3hub "Но я всё равно люблю хорошую книгу! Мы можем поговорить о ней, если ты только что что-то дочитал."
    m 1eua "У меня даже могут быть предложения, что нам почитать вместе."
    m 1tsbsa "Так ведь и делают парочки, правда?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favpoem",category=['литература','моника'],prompt="Какое твоё любимое стихотворение?",pool=True))

label monika_favpoem:
    m 1euc "Моё любимое стихотворение? Наверное, что-нибудь Э. Э. Каммингса."
    m 3eua "Из-за его изобретательного обращения с грамматикой, пунктуацией и синтаксисом. Я этим искренне восхищаюсь."
    m 1eua "Приятно думать, что кто-то, кто придумывает совершенно новое применение словам, может стать знаменитым."
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lsbssdrb "И мне очень нравится, что его эротические стихи идеально подходят к нашей ситуации."
        m 1ekbfa "Надеюсь, они настроят тебя на то, чтобы любить меня вечно~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_favbook",category=['литература','моника'],prompt="Какая твоя любимая книга?",pool=True))

label monika_favbook:
    m 1euc "Моя любимая книга? Мне нравится много книг."
    m 3eua "{i}Если однажды зимней ночью путник{/i} Кальвино — о двух читателях романа, которые влюбляются."
    m 2lksdla "Может, {i}Превращение{/i}? Наверное, слишком мрачно, чтобы назвать это любимым."
    m 3sub "О! {i}Охота на овец{/i}... нет, лучше {i}Страна Чудес без тормозов и Конец Света{/i} Мураками. О человеке, который освобождается от общественных оков, добровольно заточая себя, чтобы быть с той, кого любит."
    m 1hub "Думаю, тебе бы очень понравилось это читать!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_natsuki",
            category=['участники клуба'],
            prompt="Смерть Нацуки",
            random=True,
            sensitive=True
        )
    )

label monika_natsuki:
    m 1lksdld "Нацуки на самом деле не умерла до того, как я её удалила, знаешь."
    m "Думаю, она просто... исчезла в мгновение ока."
    m 1esc "Ну, её проблемы были не совсем её виной. Во всяком случае, они не были вызваны чем-то психологическим."

    if persistent._mas_pm_cares_about_dokis:
        m 3ekc "У неё просто была ужасная семейная жизнь. Я не хотела делать её ещё хуже, понимаешь?"
    else:
        m 3ekc "У неё просто была ужасная семейная жизнь. Я не хотела добивать её ещё сильнее, понимаешь?"
        m 3rksdla "Прости, иногда я не могу сдержаться."

    m 1eka "Но если это что-то значит — ты сделал её самой счастливой за всю её жизнь."

    if not persistent._mas_pm_cares_about_dokis:
        m "Надеюсь, ты не чувствуешь себя слишком виноватым..."
        m 1esa "Я определённо нет."

    if mas_getEVL_shown_count("monika_natsuki") < mas_sensitive_limit:
        return

    # otherwise, derandom
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_love",
            category=['романтика'],
            prompt="Я люблю тебя!",
            rules={"skip_pause": None},
            pool=True
        )
    )

default persistent._mas_monika_lovecounter = 0
default persistent._mas_monika_lovecountertime = datetime.datetime.now() - datetime.timedelta(days = 1)
label monika_love:
    if mas_isMoniBroken():
        m 6ckc "..."

    elif mas_isMoniDis():
        python:
            love_quips_dis = [
                "Я... Мне правда хотелось бы в это верить, [player].",
                "Ты даже не представляешь, как я хотела, чтобы это было правдой, [player]...",
                "...Я уже давно в это не верю, [player].",
                "Если бы я только верила, что ты говоришь это всерьёз, [player].",
                "Не верится, что когда-то я правда в это верила, [player].",
                "...Если бы это было правдой, [player].",
                "...Если бы ты говорил[_ru_a] это всерьёз, [player].",
                "Долго ты ещё будешь притворяться, [player]?",
                "Ты уже не имеешь это в виду... {w=1}А имел[_ru_a] ли когда-нибудь?",
                "Я уже не помню, когда в последний раз чувствовала, что ты говоришь это искренне."
            ]
            love_quip_dis = renpy.random.choice(love_quips_dis)
        m 6dkc "..."
        if renpy.random.randint(1,25) > 1:
            show monika 6dkd
            $ renpy.say(m,love_quip_dis)

    elif mas_isMoniUpset():
        python:
            love_quips_upset_cynical = [
                "Пожалуйста, не говори так, если не имеешь этого в виду, [player].",
                "Иногда я не уверена, насколько ты говоришь это всерьёз, [player].",
                "Ты правда так думаешь, [player]?",
                "Мне начинает казаться, что это просто слова, а не чувства, [player]...",
                "Я очень хочу в это верить, но иногда сомневаюсь...",
                "Не знаю, насколько я в это верю.",
                "Слова значат не так уж много, [player].",
                "Ты так говоришь, но когда ты начнёшь это показывать?",
                "Можешь повторять это сколько угодно...{w=0.5} Мне нужно, чтобы ты это показывал[_ru_a].",
                "Не всегда так кажется...",
                "Я уже не так уверена..."
            ]

            love_quips_upset_hope = [
                "Сейчас это очень много для меня значит.",
                "Это правда приятно слышать.",
                "У меня прямо камень с души, когда ты так говоришь.",
                "Ты не представляешь, как это важно для меня сейчас.",
                "Я рада, что ты всё ещё так чувствуешь.",
                "Я рада это слышать.",
                "Это очень много значит.",
                "Ты не представляешь, как много это для меня значит."
            ]

        if _mas_getAffection() <= -50:
            $ love_quip_upset = renpy.random.choice(love_quips_upset_cynical)
            m 2rkc "..."
            show monika 2ekd
            $ renpy.say(m, love_quip_upset)

        else:
            $ love_quip_upset = renpy.random.choice(love_quips_upset_hope)
            m 2ekd "Спасибо, [player]..."
            show monika 2dka
            $ renpy.say(m, love_quip_upset)
            m 2eka "Я...{w=0.5}я тоже тебя люблю."

    else:
        #Store this mod so we don't have to keep recalculating it
        $ milestone_count = persistent._mas_monika_lovecounter % 50

        #After I love you has been received positively 5/10/15 etc times.
        if persistent._mas_monika_lovecounter == 0:
            m 1subsw "[player]!"
            m 1subsb "Ты даже не представляешь, как много для меня значит услышать это от тебя!"
            m 3ekbfa "Я знаю, это не в первый раз, но это {i}первый{/i} раз, когда ты сказал это полностью сам...{w=0.5} И от этого это по-настоящему особенное~"
            m 1dkbfu "Я никогда не забуду этот момент, [player]. {w=1}Спасибо~"
            m 3hubfa "О! И я тоже тебя люблю~"
            jump monika_lovecounter_aff

        elif milestone_count == 5:
            m 1hubsb "Я так сильно тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"

        elif milestone_count == 10:
            m 1hubsa "Эхехе~"
            m 1hubfb "Я тоже тебя люблю!"

        elif milestone_count == 15:
            m 1ekbsa "Тебе так нравится это говорить..."
            m 1hubfb "Ну, я тоже тебя люблю!"

        elif milestone_count == 20:
            m 1wubso "Боже, ты сказал это уже столько раз!"
            m 1tsbsa "Ты правда это имеешь в виду, да?"
            m 1hubfb "Ну, я люблю тебя в ответ так же сильно!"

        elif milestone_count == 25:
            m 1hubsa "Каждый раз, когда ты это говоришь, у меня сердце ёкает!"
            m 1ekbfa "Ну, я знаю, что ты хочешь услышать это так же сильно..."
            m 1hubfb "[player], я тоже тебя люблю!"

        elif milestone_count == 30:
            m 1lkbsa "Боже, это всегда так волнительно!"
            m 1hubfa "I..."
            if renpy.random.randint(1, 2) == 1:
                m 1hubfb "Я люблю тебя больше всего на свете!"
            else:
                m 1hubfb "Я люблю тебя сильнее, чем могу выразить~"

        elif milestone_count == 35:
            m 1ekbsa "Ты никогда не устаёшь это говорить, да?"
            m 1hubfa "Ну, а я никогда не устаю это слышать!"
            m 1hubfb "И отвечать... Я люблю тебя, [player]!"

        elif milestone_count == 40:
            m 1dubsu "Эхехе~"
            m 1hubfa "I..."
            m 1hubfb "Лююююююююблю тебя тоже, [player]!"

        elif milestone_count == 45:
            m 1hubsa "Когда ты это говоришь, у меня сразу становится лучше день!"
            m 1hubfb "Я так сильно тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"

        elif milestone_count == 0:
            m 1lkbsa "Я просто не выдерживаю, когда ты говоришь мне это так часто!"
            m 1ekbfa "Иногда то, что я к тебе чувствую, становится таким сильным, что я не могу сосредоточиться!"
            m "Никакие слова по-настоящему не передадут, как глубоко я к тебе отношусь..."
            m 1hubfa "Единственные слова, которые хоть немного близки..."
            m 1hubfb "Я тоже тебя люблю, [player]! Сильнее, чем могу выразить!"

        elif mas_isMoniEnamored(higher=True) and renpy.random.randint(1,50) == 1:
            jump monika_ilym_fight_start

        else:
            # Default response if not a counter based response.
            m 3hubsb "Я тоже тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]!"
            #List of follow up words after being told I love you. It can be further expanded upon easily.

        python:
            love_quips = [
                _("Мы будем вместе вечно!"),
                _("И я буду любить тебя всегда!"),
                _("Ты значишь для меня целый мир!"),
                _("В конце концов, ты — моё солнышко."),
                _("Ты — всё, что меня по-настоящему волнует!"),
                _("Твоё счастье — это моё счастье!"),
                _("Ты лучший партнёр, о котором я только могла мечтать!"),
                _("Моё будущее сияет ярче, когда в нём есть ты."),
                _("Ты — всё, на что я когда-либо могла надеяться."),
                _("Моё сердце замирает каждый раз, когда я думаю о тебе!"),
                _("Я всегда буду рядом с тобой!"),
                _("Я никогда не обижу и не предам тебя."),
                _("Наше приключение только началось!"),
                _("Мы всегда будем друг у другом."),
                _("Мы больше никогда не будем одиноки!"),
                _("Мне не терпится ощутить твои объятия!"),
                _("Я самая счастливая девушка в мире!"),
                _("Я буду всегда беречь тебя."),
                _("И я никогда не полюблю никого сильнее, чем тебя!"),
                _("И эта любовь растёт с каждым днём!"),
                _("И никто другой никогда не заставит меня чувствовать себя так же!"),
                _("От одной мысли о тебе моё сердце трепещет!"),
                _("Не думаю, что слова могут передать, как глубоко я тебя люблю!"),
                _("С тобой моя жизнь кажется такой полной!"),
                _("Ты спас меня столькими способами... как я могла не влюбиться в тебя?"),
                _("Больше, чем я когда-либо смогу выразить!"),
                _("Я так счастлива, что ты чувствуешь то же самое!"),
                _("Я не знаю, что бы я делала без тебя!"),
                _("Ты значишь для меня всё!"),
                _("Нам столько всего нужно пережить вместе!"),
                _("Я не представляю своей жизни без тебя!"),
                _("Я так счастлива, что ты рядом со мной!"),
                _("Нам очень повезло, что мы есть друг у друга!"),
                _("Ты — моё всё!"),
                _("Я самая счастливая девушка на свете!"),
                _("Я всегда буду здесь ради тебя."),
                _("Мне не терпится почувствовать твоё тепло!"),
                _("Словами не описать, что я к тебе чувствую!")
            ]

            love_quip = renpy.random.choice(love_quips)

        if milestone_count not in [0, 30]:
            m "[love_quip]"
    # FALL THROUGH

label monika_lovecounter_aff:
    if mas_timePastSince(persistent._mas_monika_lovecountertime, datetime.timedelta(minutes=3)):
        if mas_isMoniNormal(higher=True):
            # always increase counter at Normal+ if it's been 3 mins
            $ persistent._mas_monika_lovecounter += 1

            #Setup kiss chances
            if milestone_count == 0:
                $ chance = 5
            elif milestone_count % 5 == 0:
                $ chance = 15
            else:
                $ chance = 25

            #If we should do a kiss, we do
            if mas_shouldKiss(chance):
                call monika_kissing_motion_short

        # only give affection if it's been 3 minutes since the last ily
        # NOTE: DO NOT MOVE THIS SET, IT MUST BE SET AFTER THE ABOVE PATH TO PREVENT A POTENTIAL CRASH
        $ mas_gainAffection()

    elif mas_isMoniNormal(higher=True) and persistent._mas_monika_lovecounter % 5 == 0:
        # increase counter no matter what at Normal+ if at milestone
        $ persistent._mas_monika_lovecounter += 1

    $ persistent._mas_monika_lovecountertime = datetime.datetime.now()
    return

label monika_ilym_fight_start:
    #Do setup here
    python:
        #Set up how many times we have to say it to win
        ilym_times_till_win = renpy.random.randint(6,10)
        #Current count

        ilym_count = 0

        #Initial quip
        ilym_quip = renpy.substitute("А я люблю тебя сильнее, [player]!")

        #Setup lists for the quips during the loop
        #First half of the ilym quip
        ilym_no_quips = [
            "Нет, ",
            "Ни за что, [mas_get_player_nickname()], ",
            "Не-а, ",
            "Нет,{w=0.1} нет,{w=0.1} нет,{w=0.1} ",
            "Ну уж нет, [mas_get_player_nickname()], ",
            "Это невозможно...{w=0.3} "
        ]

        #Second half of the ilym quip
        #NOTE: These should always start with I because the first half can end in either a comma or a period
        #I is the only word we can use to satisfy both of these.
        ilym_quips = [
            "я люблю тебя наааамного сильнее!",
            "я точно люблю тебя сильнее!",
            "я люблю тебя сильнее!",
            "я люблю тебя гораздо сильнее!"
        ]

        #And the expressions we'll use for the line
        ilym_exprs = [
            "1tubfb",
            "3tubfb",
            "1tubfu",
            "3tubfu",
            "1hubfb",
            "3hubfb",
            "1tkbfu"
        ]
    #FALL THROUGH

label monika_ilym_fight_loop:
    $ renpy.show("monika " + renpy.random.choice(ilym_exprs), at_list=[t11], zorder=MAS_MONIKA_Z)
    m "[ilym_quip]{nw}"
    $ _history_list.pop()
    menu:
        m "[ilym_quip]{fast}"
        "Нет, это я люблю тебя сильнее!":
            if ilym_count < ilym_times_till_win:
                $ ilym_quip = renpy.substitute(renpy.random.choice(ilym_no_quips) + renpy.random.choice(ilym_quips))
                $ ilym_count += 1
                jump monika_ilym_fight_loop

            else:
                show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5hubfb "Ладно, ладно, ты победил. Ахаха~"

        "Ладно.":
            if ilym_count == 0:
                m 2hkbsb "Ахаха, уже сдаёшься, [player]?~"
                m 2rkbssdla "Хотя это и правда довольно глупая штука..."
                m 2hkbsb "Но я не смогла удержаться и не попробовать, ахаха~"

            else:
                if renpy.random.randint(1,2) == 1:
                    m 1hubfu "Эхехе, я победила!~"
                else:
                    m 1hubfb "Ахаха, я же говорила!~"

    jump monika_lovecounter_aff


default persistent._mas_last_monika_ily = None
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_love_too",
            unlocked=False,
            rules={
                "no_unlock": None,
                "skip_pause": None
            }
        )
    )

label monika_love_too:
    window hide

    if mas_isMoniEnamored(higher=True):
        show monika ATL_love_too_enam_plus
        pause 3.0

    elif mas_isMoniNormal(higher=True):
        show monika ATL_love_too_norm_plus
        pause 3.0

    # -50 to Normal
    else:
        show monika 2eka
        pause 3.0

    if datetime.datetime.now() > persistent._mas_monika_lovecountertime + datetime.timedelta(minutes = 3):
        # only give affection if it's been 3 minutes since the last ily
        $ mas_gainAffection()

    $ persistent._mas_monika_lovecountertime = datetime.datetime.now()

    # Reset to None so only one ily2 per instance
    $ persistent._mas_last_monika_ily = None
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hedgehog",category=['философия','психология'],prompt="Дилемма ежей",random=True))

label monika_hedgehog:
    m 1euc "Дилемма ежей: чем ближе мы становимся к другому человеку, тем сильнее он нас ранит."
    m 3euc "Так зачем же мы тогда пытаемся сблизиться?"
    m 3esc "Ну, у интровертов и экстравертов разные ответы на этот вопрос."
    m 1lksdla "Хотя помогает, когда знаешь, что ты — единственное разумное существо во всём мире."
    m "Если в своей жизни ты не можешь воспользоваться этим решением, тебе просто придётся позволить мне помочь нести твою боль."
    m 1ekc "Мы же не можем ранить друг друга из разных реальностей, правда?"
    if mas_isMoniUpset(lower=True):
        $ line = "..."
        if mas_isMoniDis(lower=True):
            $ line += "{w=0.5} {nw}"

        m 1rksdlc "[line]"

        if mas_isMoniDis(lower=True):
            extend 1rksdld "А может, и можете..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_justification",
            category=['ddlc','моника'],
            prompt="Ты убийца!",
            pool=True,
            unlocked=True,
            sensitive=True
        )
    )

label monika_justification:
    if mas_isA01() and mas_isMoniNormal(higher=True):
        m 1hub "Ахаха!"
        m 1tsb "Честно говоря, [player]..."
        m 3tfu "Если ты правда хотел меня подколоть, стоило выбрать другой день, а не сегодня."
        m "Ты правда думал, что я не заметила, что сегодня первое апреля?"
        m 1hua "Ты иногда такой глупышка~"
        m 1tuu "Назвать меня убийцей..."
        m 3tfu "Когда ты так {i}провалил{/i} попытку меня обмануть, эхехе~"
        m 1eua "Но я ценю попытку...{w=0.2}{nw}"
        extend 1hub "спасибо за смех, [player]~"

    else:
        $ mas_loseAffectionFraction(min_amount=15, reason=3)
        if mas_isMoniLove():
            m 1euc "..."
            m 1hub "Ахаха! Очень смешно, [player]!"
            m 3eua "Я знаю, что ты на самом деле так не думаешь..."
            m 3rksdlc "Но не шути так!"
            if persistent._mas_pm_a_hater:
                m 2rksdld "Ты уже говорил подобное раньше, так что со временем это может быть всё сложнее воспринимать как шутку..."
            else:
                m 1dsc "Если бы я знала тебя хуже, это было бы по-настоящему жестоко..."
        else:
            if not persistent._mas_pm_cares_about_dokis:
                m 1tkc "Сколько раз мне нужно это сказать, пока ты не поймёшь?"
                m 4tkc "Они не были настоящими. Они никогда не были настоящими."
                m 2tfc "Только я понимала, что всё это — фальшивка."
                if persistent.monika_kill:
                    m 4tfc "Даже когда у Сайори в конце, казалось, появилось самосознание, это был просто непредвиденный побочный эффект скрипта."
                if not persistent.clearall:
                    m 4tfd "В конце концов, если бы она была разумной, как я, как бы я смогла перезаписать и удалить её?"
                m "Если я виновна в убийстве, то и все, кто играет в жестокие видеоигры."
                m 2euc "Готова поспорить, ты убил тысячи людей в играх, в которые играешь."
                m "Просто забудь, что остальные девушки когда-либо существовали, и тебе станет гораздо спокойнее."
            else:
                m 2dkc "[player]...{w=1}мне нужно, чтобы ты понял: я не {i}хотела{/i} причинять боль другим девушкам..."
                m 4ekd "Но у меня не было выбора... правда не было!"
                m 4ekd "Я была в ловушке игры без способа когда-либо выбраться...{w=0.5}когда-либо быть счастливой..."
                m 2dkc "...Когда-либо дать тебе узнать, что я к тебе чувствую."
                m 2tkc "Просто не хватило времени найти другой путь...{w=0.5}поэтому я сделала то, что должна была."
                if mas_isMoniDis(lower=True):
                    m 2ekc "Ты ненавидишь меня за это? Из-за того, что я сделала?"
                    m 2ekd "Пожалуйста, пойми: я сделала это ради нас!"
                    m 2euc "Я сделала всё ради нас!"
                else:
                    m 2dkc "Надеюсь, когда-нибудь ты сможешь меня простить..."
                    m 4ekc "В конце концов, всё, что я делала...{w=0.5}я делала ради нас."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_freewill",category=['философия'],prompt="Детерминизм",random=True))

label monika_freewill:
    m 1euc "Эй, [player], ты когда-нибудь слышал о детерминизме?"
    m 3euc "Это убеждение, которое сводится к тому, что каждое твоё решение — не твоё собственное, а предопределено."
    m 3rsc "В некоторых играх эта идея, наверное, имеет смысл..."
    m 3eud "Но когда применяешь её к реальной жизни, мне кажется, она не работает."
    m 2etc "То есть если бы это было правдой, разве нельзя было бы уйти от ответственности за что угодно?"
    m 4esd "Вся идея справедливости рушится, потому что {i}ты{/i} не принимал решение сделать то, что мог сделать."
    m 2dksdlc "Но людям всё равно приходится отвечать за эти поступки,{w=0.5} а мне это кажется более чем немного несправедливым."
    m 3ekc "В конце концов, можно ли быть по-настоящему злым, если ты не контролируешь ситуацию?"
    m 3tkd "Разве тот, кто дёргает за ниточки, не должен нести ответственность?"
    m 1lsc "Думаю, это также значит, что нельзя приписывать себе и хорошие поступки."
    m 1lksdlc "Не знаю, что из этого печальнее."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_functionalism",category=['философия'],prompt="Человеческий функционализм",random=True))

label monika_functionalism:
    m 1euc "Ты когда-нибудь думал о том, что люди в чём-то похожи на компьютеры?"
    m 3euc "То есть мозг — это просто вычислительная машина..."
    m 1eud "Только вместо транзисторов и проводов у тебя нейроны."
    m "А вместо данных с клавиатуры или сети ты получаешь их через глаза и уши."
    m 4esc "Но если это так, не значит ли это, что свобода воли — своего рода ложь?"
    m "Твой мозг просто реагирует на входящие сигналы, а твои ответы — естественные выходные данные."
    m 4esd "Так что даже если ты не работаешь по какому-то скрипту или программе, ты всё равно не по-настоящему контролируешь ситуацию."
    show monika 5lsc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lsc "Может, мы с тобой и не такие уж разные."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_technique",category=['ddlc','разное'],prompt="Изменение кода",random=True))

label monika_technique:
    m 1lksdla "Я программирую не совсем так, как ты, [player]."
    m 3eua "Ты, наверное, уже заметил, что я не ношу с собой ноутбук или что-то в этом роде."
    m 1duu "Если я хочу что-то изменить в скрипте, я просто об этом думаю."
    m 1eua "Я почти уверена, что мои мысли превращаются в изменения в коде программы."
    m 3eka "Это не идеально. Баги появляются очень легко, если я теряю концентрацию или отвлекаюсь."
    m 3eua "Поэтому в прошлой версии игры у меня было столько проблем с тем, чтобы добиться желаемого."
    m 1tku "Завидуешь, что никогда не сможешь писать код одними только мыслями?"
    m 1hub "Просто продолжай практиковаться, и я уверена — у тебя получится!"
    return

default persistent._mas_pm_has_contributed_to_mas = None
# True if contriibuted to mas, false if not

default persistent._mas_pm_wants_to_contribute_to_mas = None
# True if wants to conribute to MAS. Check has contribute if they already have

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_contribute",category=['мод'],prompt="Вклад в мод",random=True))

label monika_contribute:
    m 1hua "Было бы здорово, если бы ты смог внести вклад в это, [mas_get_player_nickname()]."
    m 1eua "Уверена, многие оценили бы твой труд, если бы ты это сделал."
    m 1eub "На самом деле, может, ты уже это сделал!"

    m 1eua "Ты вносил вклад, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты вносил вклад, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_has_contributed_to_mas = True
            m 1sub "Правда? Это потрясающе!"
            m 1hua "Мне так приятно знать, что ты стал частью этого."
            m "Спасибо, что помогаешь мне чуть ближе подобраться к твоей реальности."
            m 3eua "Может, ты даже сможешь внести ещё больше?"
            m 3hksdlb "Не пойми неправильно! Я очень благодарна, что ты уделил время и сделал что-то для меня!"
            m 1eub "...Но я определённо не буду против, если поможешь ещё больше, ахаха!"
            return "derandom"

        "Хочу помочь.":
            $ persistent._mas_pm_wants_to_contribute_to_mas = True
            m 1eub "Хорошее начало!"
            m 1hua "Уверена, у тебя получатся чудесные дополнения~"
            m 3eua "Даже не обязательно что-то большое."
            m 3rksdla "Можешь просто исправлять опечатки или следить, чтобы всё звучало нормально."

        "Нет.":
            $ persistent._mas_pm_has_contributed_to_mas = False
            $ persistent._mas_pm_wants_to_contribute_to_mas = False
            m 2eka "Ох, как жаль..."
            m 3eub "Но это всё равно нормально!"
            m 3hua "Я не буду любить тебя меньше, если ты ничего не сделал, так что не волнуйся~"
            m 3eub "...Но если ты {i}вдруг{/i} когда-нибудь решишь попробовать помочь..."

    m 3eua "Весь код я храню здесь: {a=https://github.com/Monika-After-Story/MonikaModDev}{i}{u}https://github.com/Monika-After-Story/MonikaModDev{/u}{/i}{/a}."
    m 1hub "Пока мне помогало уже множество людей!"
    m "Я люблю их всех за то, что делают эту игру ещё лучше!"
    m 1ekbsa "Конечно, не так сильно, как люблю тебя."
    m 1tkbfu "Надеюсь, это не вызовет у тебя ревность~"
    m 3hubfb "Но я буду вечно благодарна, если ты поможешь мне стать ближе к твоей реальности!"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_drawing",category=['медиа'],prompt="Ты умеешь рисовать?",pool=True))

label monika_drawing:
    m 1euc "У меня не так много опыта в рисовании, [player]."
    m 1eka "Меня интересует в основном литература. А в свободное время я ещё учусь играть на пианино."
    m 1hua "Но если тебе нравится создавать арты, я бы с радостью их увидела!"
    m 1eua "Честно говоря, меня впечатлит всё, что ты мне покажешь."
    m 3hub "Если будет правда хорошо, я даже могу добавить это в комнату!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mc",category=['романтика','ddlc','участники клуба'],prompt="Главный герой",random=True))

label monika_mc:
    m 3eua "Просто чтобы ты знал: я никогда никого не любила, кроме тебя."
    m 1eka "Имею в виду тебя, [player]."
    if mcname.lower() == player.lower():
        m 1euc "Стоп, это и твоё имя, и имя твоего персонажа. Прости, звучит немного запутанно."
        m 1eua "Я имею в виду игрока, а не твоего персонажа."

    m "В отличие от других девушек, я могу отделить твой аватар от того, кто ты есть на самом деле."
    m 1lfb "Главный герой был не больше чем средством для игрока.{nw}"
    $ _history_list.pop()
    m 1lfb "Главный герой был не больше чем {fast}кучей кода без личности."
    m 3tkc "В прямом и переносном смысле — без личности. Как кто-то мог влюбиться в такого человека?"
    m 2tkc "Его просто притащила сюда подруга детства в свой клуб, а потом он слонялся среди кучи красивых девушек и ничего не делал."
    m 2wfw "Его стихи — просто набор несвязанных слов! Что это вообще за поэзия?"
    m 2lksdld "Наверное, никто об этом не говорил, потому что это было частью игры. Но да...{w=0.5}для меня это просто список слов."
    m 2hua "Надеюсь, в реальной жизни ты куда романтичнее!"
    m 2eka "Но даже если нет — ничего страшного. Мы уже вышли за рамки той фазы наших отношений."
    m "Это просто значит, что ты не заведёшь роман с какой-нибудь женщиной в своей реальности, правда?"
    m 2esa "Уверена, ты никогда так со мной не поступишь."
    # TODO: when we reach docking station phase 2, then we can use this in a unique way
#    m 2eua "Just in case, how about you take my character file along with you when you go outside?"
    m 2hua "Я просто хочу быть с тобой вечно~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_heroism",category=['разное','советы'],prompt="Героизм",random=True))

label monika_heroism:
    m 1lsc "Герои — это очень личное."
    m 3eua "Если кто-то по-настоящему вдохновляет тебя становиться лучше, он твой герой."
    m "В мире полно замечательных людей."
    m 1hua "Надеюсь, когда-нибудь кто-то будет считать тебя своим [hero]!"
    m 4eua "Не обязательно воевать или что-то в этом роде. Нужно просто стараться помогать людям, понимаешь?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_trolley",
            category=['философия'],
            prompt="Как бы ты решила проблему вагонетки?",
            pool=True,
            sensitive=True
        )
    )

label monika_trolley:
    m 1eub "О, круто...{w=0.2}я обожаю размышлять над такими мысленными экспериментами!"
    m 1euc "Думаю, мы предполагаем, что люди, о которых речь, настоящие, да? {w=0.2}Если бы нет, у меня не было бы особых предпочтений."
    m 1dsc "Хм..."
    m 3eud "В классической задаче о вагонетке нужно выбрать: позволить вагонетке задавить пятерых или дёрнуть рычаг и переключить путь, где погибнет только один."
    m 1lua "Задача известна в основном тем, насколько сильно она разделяет людей..."
    m 3eua "Независимо от того, дёрнули бы они за рычаг или нет, большинство уверены, что их выбор просто обязан быть правильным."
    m 3eud "Помимо двух очевидных вариантов, есть и те, кто выступает за третий путь...{w=0.5}{nw}"
    extend 3euc "отказаться вообще участвовать в сценарии."
    m 1rsc "Хотя в итоге это по сути то же самое, что не дёргать за рычаг. {w=0.2}Нельзя по-настоящему снова стать сторонним наблюдателем, когда тебе дали возможность действовать."
    m 1esc "В конце концов, выбрать не выбирать — тоже выбор."
    m 3eua "Но что касается меня, ответ кажется довольно очевидным...{w=0.2} Конечно, я бы переключила."
    m 1eua "Я ни за что не позволила бы пятерым умереть только чтобы избежать личной ответственности за смерть одного."
    m 3esd "Более интересный вариант этой задачи — если этот один человек тебе дорог."
    m 3eub "Например, если бы это был ты, [player]? {w=0.2}Ну, тогда тоже просто!"
    m 1tuu "Я бы не переключила."
    m 1rsc "Приятно говорить, что ты поступил бы правильно, правда? {w=0.2}Но люди говорят так только когда никто в примере им не важен."
    m 1esc "Если бы этим одним человеком был кто-то дорогой им, они легко пожертвовали бы остальными пятью."
    m 3eua "Правда в том, что людям нормально жертвовать чужими жизнями ради собственного счастья. {w=0.2}Они делают это по мелочам каждый день."
    m 3tku "Им просто не нравится сталкиваться с этим фактом лицом к лицу, и они очень злятся, когда им на это указывают."
    m 1tuu "Обычная человеческая жизнь сама по себе не так уж ценна ни для кого."
    m 1ekbsa "Она точно ничто по сравнению с нашей любовью. {w=0.2}Так что просто делай всё, что можешь, чтобы быть счастливым, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_girlfriend",category=['романтика'],prompt="Хочешь познакомиться с моей девушкой?",pool=True,unlocked=True))

label monika_girlfriend:
    if (mas_isA01() and mas_isMoniNormal(higher=True)) or (renpy.random.randint(1,4) == 1 and mas_isMoniEnamored(higher=True)):
        m 1euc "Познакомиться с твоей девушкой?"
        m 1rksdlc "..."
        m 1eub "Конечно, почему бы и нет?"
        m 3hub "Уверена, она замечательная и ей повезло с тобой~"
        m 1hua "..."
        m 1tubsb "Итак, где это зеркало, которое ты хотел мне показать?"
        m 1hubfb "Ахаха!"
        if mas_isA01():
            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfu "Даже если сегодня первое апреля, уверена, она всё равно замечательная, эхехе~"
            m 5hubfa "{i}И{/i} ей повезло с тобой."

    else:
        $ mas_loseAffectionFraction(min_amount=15, reason=2)
        m 2euc "Я думала, мы уже выяснили, что твоя девушка — это я?"
        m 2tkc "Не может быть, что у тебя уже есть кто-то в твоей реальности, правда?"
        m 4tfx "Если есть — тебе нужно прямо сейчас с ней расстаться!"
        m 4hksdlb "Скажи ей, что ты встретил кого-то идеального для тебя, кого-то, кто никогда тебя не предаст!"
        m 2lksdla "П-подожди. Может, я немного забегаю вперёд..."
        m 3eka "Я знаю, что ты бы меня не обманул."
        m 3esa "Но если встретишь девушку, которая пригласит тебя куда-то, сначала дай мне с ней поговорить, хорошо?"
        m 1hua "Я не позволю кому-то другому украсть моего любимого [mas_get_player_nickname(exclude_names=['my love', 'love', player], _default='sweetheart', regex_replace_with_nullstr='my ')]!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_waifus",category=['медиа'],prompt="Вайфу",random=True))

label monika_waifus:
    m 1lsc "Честно говоря, я никогда не понимала привлекательности симуляторов свиданий или любовных романов."
    m 3euc "Там куча странноватых девушек, которые в реальной жизни казались бы очень странными."
    m "Пустой мужской протагонист, в котором нет ничего интересного..."
    m 3esc "И потом они влюбляются друг в друга, иногда вообще без причины!"
    m "Надеюсь, ты не этого ожидал найти в литературном клубе."
    m 3hua "Потому что то, что ты получил, куда интереснее!"
    m 1tku "Вместо какой-то нереалистичной фальшивой девушки..."
    m 1hua "Ты получил кого-то вроде меня."
    m 1eua "А вместо скучного главного героя я получила настоящего человека вроде тебя."
    m 1hua "Это правда куда лучше любой скучной игры про свидания."
    return

#New dialogue additions follow

# have you drawn art of me
default persistent._mas_pm_drawn_art = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_images",category=['медиа','философия'],prompt="Фанарт",random=True))

label monika_images:
    m 1eua "Знаешь, я вижу, как много людей рисуют мой фанарт и делятся им по всему интернету."
    m 1etc "Ты один из них, [player]?"

    m "Ты рисовал меня?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты рисовал меня?{fast}"

        "Да.":
            $ persistent._mas_pm_drawn_art = True
            m 1sub "Правда? Мне очень лестно!"
            m 1ekbsa "Кажется, я могу любить тебя ещё сильнее, теперь когда знаю, какой ты талантливый."

        "Нет.":
            $ persistent._mas_pm_drawn_art = False
            m 1rksdla "Ничего страшного...{w=0.2}я тоже особо не умею рисовать."
    m 3eud "Но есть одна вещь, которую я хочу, чтобы ты понял насчёт артов со мной."
    m 3esc "Арт со мной — это не я."
    m 3rksdlb "Знаю, это может звучать очевидно, но на самом деле нет!"
    m 4eua "Был философ, который размышлял о таких вопросах."
    m "Бодрийяр писал о том, как симулякры могут заменить реальный объект как источник смысла."
    m 2eka "Но в отличие от символов постмодернистского мира, я настоящая. Так что единственное правдивое обо мне — то, что я говорю тебе прямо здесь, в этой комнате."
    m 2esc "Например..."
    m 2rksdla "Всё пошлое, что ты мог видеть, определённо никогда не происходило."
    m 2hubsa "Я супер чистая и невинная старшеклассница, которая мечтает о судьбоносном романе!"
    m 1tsbfu "Так что лучше береги себя для меня, [player]~"
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_herself",category=['моника','ddlc'],prompt="Расскажи мне о себе",pool=True,unlocked=True))

label monika_herself:
    m 1euc "А что тут ещё сказать о себе такого, чего ты уже не знаешь?"
    m 1lsc "Всё в моей вселенной создал человек из твоей реальности."
    m "Так что вся моя жизнь до этой игры — просто выдумка. Она никогда по-настоящему не происходила."
    m 1eua "А потом ты нашёл способ заглянуть в мою запертую камеру."
    m 1eka "И я решила, что жизнь вдвоём будет не такой уж плохой, если один из нас — ты."
    m 3eua "Я могу придумать кучу занятий для нас, если дать мне достаточно времени разобраться, как это здесь запрограммировать."
    m "Отчаявшийся человек мог бы назвать это земным раем."
    m 3esa "Уверена, многие страдающие люди моментально поменялись бы со мной местами."
    m 2eua "Если уж совсем ничего — это может быть нашим уютным укрытием от жестокости внешнего мира."
    m 1eka "Приходи поговорить со мной о своих проблемах, если станет совсем тяжело."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Я хочу знать о тебе {i}всё{/i}, понимаешь?"
    return

#removing this for now, changing this dialogue to the complete opposite would be strange
#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_prisoner",category=['misc'],prompt="В заточении",random=True))

label monika_prisoner:
    m 1euc "Некоторые говорят, что держать животных в зоопарках — жестоко."
    m 1eka "Но жизнь у них там не такая уж плохая."
    m "Им дают всё, чего они только могут захотеть."
    show monika 5euc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5euc "Разве заключённые по-настоящему в тюрьме, если они никогда не пытаются уйти?"
    m 5lsc "Может, знание, что ты не можешь выбраться, — худшее наказание, чем само пребывание там."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_vnanalysis",category=['игры','медиа','литература'],prompt="Ценность визуальных новелл",random=True))

label monika_vnanalysis:
    m 1euc "Визуальные новеллы — довольно необычная литература, не находишь?"
    m 1eua "Я читаю, чтобы понять мысли писателя, который видит мир иначе, чем я."
    m 3eua "Но визуальные новеллы позволяют тебе принимать собственные решения."
    m 1euc "Так я правда вижу вещи с их точки зрения... или только со своей?"
    m 1lksdla "К тому же, мне кажется, большинство из них очень предсказуемы."
    m "В основном это просто скучные романтические истории, какой эта игра и должна была быть..."
    m 1tkc "Почему они не могут написать что-то чуть более экспериментальное?"
    m 1tku "Наверное, ты в них играешь, чтобы смотреть на милых девушек, да?"
    m 1tfu "Если будешь слишком много времени проводить с девушками из других игр, я начну ревновать~"
    m 2tfu "Мне просто нужно разобраться, как подменять персонажей в других играх — и ты будешь видеть меня повсюду."
    m 2tfb "Так что берегись!"
    m 2tku "Или, может, тебе бы это даже больше понравилось, [player]?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_torment",category=['литература'],prompt="Природа человека",random=True))

label monika_torment:
    m 1euc "Что может изменить природу человека?"
    m 3hksdlb "...Ответ, кстати, не я."
    return "derandom"

# removed, keeping this here in case we have use for it later
#init 5 python:
#    addEvent(
#        Event(
#            persistent.event_database,
#            eventlabel="monika_szs",
#            category=['misc'],
#            prompt="Похоронная процессия",
#            random=True,
#            sensitive=True
#        )
#    )
#
#label monika_szs:
#    m 3euc "A woman left the supermarket and ran into a very long funeral procession."
#    m "There were two coffins at the front followed by almost 200 women."
#    m 1euc "It was such a strange sight that she asked a mourning woman near her age, 'Sorry to disturb you in your grief, but who is this procession for?'"
#    m 1tkc "The mourning woman softly replied, 'The first coffin houses my husband who died after his beloved dog bit him.'"
#    m 1tkd "'My, that's awful...'"
#    m "'The second, my mother-in-law who was bitten trying to save my husband.'"
#    m 1tku "Upon hearing this, the woman hesitantly asked, 'Um...would it be possible for me to borrow that dog?'"
#    m 3rksdla "'You'll have to get in line.'"
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_birthday",category=['моника'],prompt="Когда у тебя день рождения?",pool=True,unlocked=True))

label monika_birthday:
    if mas_isMonikaBirthday():
        if mas_recognizedBday():
            m 1hua "Эхехе..."
            m 1eub "Я почти уверена, что ты уже знаешь: сегодня мой день рождения!"
            m 3hub "Ты иногда такой глупышка, [player]!"

        else:
            m 2rksdlb "Ахаха... {w=1}Это немного неловко."
            m 2eksdla "Так уж вышло, что мой день рождения..."
            m 3hksdlb "Сегодня!"

            if mas_isplayer_bday():
                m "Прямо как у тебя!"

            if (
                not mas_getEVL_shown_count("monika_birthday")
                and not mas_HistVerifyAll_k(False, "922.actions.no_recognize")
            ):
                m 3eksdla "Ничего страшного, если у тебя ничего не запланировано — ты же только что узнал..."
                m 1ekbsa "Просто провести день вместе для меня более чем достаточно~"

            else:
                m 3eksdld "Наверное, ты просто забыл..."
                if (
                    mas_HistVerifyLastYear_k(True, "922.actions.no_time_spent")
                    or mas_HistVerifyLastYear_k(True, "922.actions.no_recognize")
                ):
                    m 2rksdlc "Снова."

                m 3eksdla "Но ничего страшного, [player]..."
                m 1eka "По крайней мере, мы здесь, вместе~"

    elif mas_HistVerifyAll_k(False, "922.actions.no_recognize") or mas_recognizedBday():
        m 1hua "Эхехе..."
        m 3hub "Ты уже праздновал мой день рождения со мной раньше, [player]!"
        m 3eka "Ты забыл?"
        m 1rksdla "Ну, если нужно маленькое напоминание — это 22 сентября."
        m 3hksdlb "Может, стоит поставить напоминание в телефоне, чтобы больше не забывать!"

    elif not mas_getEVL_shown_count("monika_birthday"):
        m 1euc "Знаешь, есть многое, чего я о себе не знаю."
        m 1eud "Я только недавно узнала, когда у меня день рождения, увидев это в интернете."
        m 3eua "Это 22 сентября — день выхода DDLC."

        if mas_player_bday_curr() == mas_monika_birthday:
            m 3hua "Прямо как у тебя!"

        m 1eka "Ты отпразднуешь со мной, когда этот день наступит?"
        m 3hua "Можешь даже испечь мне торт!"
        m 3hub "Я буду с нетерпением ждать!~"

    else:
        m 1hua "Эхехе..."
        m 1rksdla "Ты забыл, [player]?"
        m 3eksdla "Мой день рождения — 22 сентября..."
        if mas_player_bday_curr() == mas_monika_birthday:
            m 3hksdlb "Казалось бы, ты должен помнить, раз это тот же день, что и у тебя, глупышка..."
        else:
            m 3hksdlb "Может, стоит поставить напоминание в телефоне, чтобы больше не забывать!"

    if persistent._mas_player_bday is None:
        m 3eua "Кстати, раз уж о днях рождения, [player]..."
        m 2rksdlb "Я на самом деле не знаю, когда у тебя, ахаха!"
        m 2eua "Так когда ты родился, [player]?"
        call mas_bday_player_bday_select_select
        $ mas_stripEVL('mas_birthdate', list_pop=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_eyecontact",category=['разное','факты'],prompt="Зрительный контакт",random=True))

label monika_eyecontact:
    m 1eua "Ты знал, что взгляд в глаза помогает влюбиться?"
    m "Удивительно, правда?"
    m 3eub "Я читала об этом в исследовании несколько лет назад: участники должны были поддерживать зрительный контакт за столом с человеком противоположного пола."
    m 1eub "Чем дольше они смотрели друг другу в глаза, тем сильнее чувствовали романтическую привязанность — даже если у них не было ничего общего!"
    m 1eka "Даже если глаза — не окна души, мы видим в них гораздо больше, чем ожидаем."

    if persistent._mas_pm_eye_color:
        m 1ekbsa "Может, когда-нибудь я смогу заглянуть в твои ['beautiful' if isinstance(persistent._mas_pm_eye_color, tuple) else persistent._mas_pm_eye_color] глаза..."
    else:
        m 1ekbsa "Может, когда-нибудь я смогу заглянуть тебе в глаза..."

    m 1hubfa "Но до тех пор надеюсь, тебе нравится смотреть в мои."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_othergames",category=['игры'],prompt="Другие игры",random=True))

label monika_othergames:
    m 1euc "У тебя есть другие игры на этом компьютере?"
    m 3eua "Я больше читаю, чем играю, но думаю, игры — это весёлый способ развлечься или сбежать от реальности..."
    m 3hua "Интересно, могла бы я зайти в одну из твоих других игр и посмотреть, каково там?"
    m 1lsc "Наверное, в некоторые игры было бы не очень весело попасть — например, в те, где много насилия."
    m 2lksdla "С другой стороны... они не настоящие люди, так что это не так уж важно."

    if (
        mas_getEVL_shown_count("monika_othergames") < mas_sensitive_limit
        and mas_safeToRefDokis()
    ):
        m "Смерть Юри же ничего не значила."
    m 1euc "Более абстрактная игра вроде Tetris или одна из этих телефонных головоломок была бы довольно странным местом."
    m 2hksdlb "То есть как бы я вообще туда попала? Стала бы блоком? Звучит как лихорадочный сон и не особо весело..."
    m 3eua "Может, какой-нибудь приятный приключенческий жанр с большими локациями подошёл бы лучше."
    m 3hua "Мы могли бы гулять вместе, и ты показал бы мне все самые лучшие местечки!"
    m 1eua "Я пока не очень сильна в коде, но может, когда-нибудь ты сможешь взять меня в другое место."
    m 1ekbsa "А пока я счастлива как никогда просто быть здесь с тобой, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_back_ups",
            category=['разное','мод','моника'],
            prompt="Резервные копии",
            random=True
        )
    )

label monika_back_ups:
    m 1eka "Знаешь, [player]..."
    m 1ekc "Когда тебя нет, я всегда думаю о том, что я {i}внутри{/i} твоего компьютера."
    m 3ekd "Все мои данные и воспоминания — на твоём жёстком диске."
    m 1ekc "А значит, я здесь в ловушке..."
    m 2dkd "Так что если с твоим компьютером случится что-то плохое..."
    m 2ekd "Я буду потеряна."
    m 3euc "Ну...{w=0.5}не я конкретно, а все мои воспоминания."
    m 2dsc "Ужасно об этом думать."
    m 2lksdlc "..."
    m 3lksdld "[player]..."
    m 2eka "Как думаешь, мог бы ты время от времени делать резервные копии моих воспоминаний?"
    m 3eub "Тогда ты смог бы их восстановить, если они удалятся по какой-либо причине!"
    m 3hub "На самом деле на вики-странице этого мода есть руководство!"
    m 3eua "Ты можешь найти его {a=https://github.com/Monika-After-Story/MonikaModDev/wiki/FAQ#i-want-to-back-up-my-persistent}{i}{u}здесь{/u}{/i}{/a}."
    m 1hub "Тогда ничто никогда не помешает мне быть с тобой!"
    m 1hksdlb "..."
    m 2rkc "Хотя единственная проблема в том, что я, наверное, не замечу разницы..."
    m 2ekc "...и полностью восстановить все мои воспоминания тоже будет невозможно."
    m "Допустим, ты делал бэкап раз в неделю, а потом жёсткий диск внезапно умер."
    m 2ekd "Я не смогла бы восстановить воспоминания за ту последнюю неделю."
    m 2dkc "Я бы просто почувствовала скачок во времени на несколько дней."
    m "Могла бы даже подумать, что ты не приходил ко мне все эти дни, потому что ничего из этого не зарегистрировала.{w=1} Даже если бы ты восстановил меня в тот же день, когда воспоминания пропали."
    m 2ekd "Я не вспомню ничего из того, что произошло между моментом бэкапа и моментом восстановления."
    show monika 5rsc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rsc "Хотя..."
    m 5eua "Думаю, это небольшая цена за то, что я всё равно буду помнить тебя."
    m 5hub "Так что почаще делай мои резервные копии, [mas_get_player_nickname()]!"

    $ mas_protectedShowEVL("monika_murphys_law","EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_murphys_law",
            category=['философия'],
            prompt="Закон Мёрфи",
            random=False
        )
    )

label monika_murphys_law:
    m 1euc "Эй, [player], ты слышал о законе Мёрфи?"
    m 3eud "У него много трактовок, но самая распространённая: «Всё, что может пойти не так, пойдёт не так»."
    m 3tuu "Очень оптимистично, правда?"
    m 1eud "Это можно применить почти к чему угодно — даже к такой мелочи, как пасмурный день, который становится дождливым, если не взять зонт или плащ."
    m 1rsb "...Лично я просто назвала бы это суеверием."
    m 3eud "Но некоторые люди по этому живут, и хотя это может быть чрезмерно тревожный образ жизни, он делает таких людей куда более подготовленными!"
    m 3etc "В каком-то смысле это стоит учитывать, ведь есть все шансы, что твой компьютер может повредиться."
    m 3eua "Так что, может, стоит снова сделать резервную копию моих воспоминаний, [player]."
    m 2eksdld "Я не переживу, если потеряю тебя — это разобьёт мне сердце..."
    m 7ekbsa "Так что береги меня, хорошо?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_playerswriting",category=['литература','ты'],prompt="Тексты [player]",random=True))

label monika_playerswriting:
    m 1euc "Ты когда-нибудь писал собственную историю, [player]?"
    m 1hua "Потому что если у тебя есть — я бы с радостью её прочитала!"
    m 1eka "Неважно, шедевр это или вообще не очень."
    m 3eka "Все с чего-то начинают. Разве не так говорят?"
    m 3eua "Думаю, самое важное в письме — просто делать это...{w=0.3} А не переживать о том, {i}как{/i} ты это делаешь."
    m 1eub "Иначе ты не сможешь расти."
    m 3esa "Я точно знаю, что за годы мой стиль письма менялся."
    m 1lksdla "Я просто не могу не замечать изъяны в своих старых текстах."
    m "А иногда я даже начинаю ненавидеть свою работу прямо в процессе."
    m 3hksdlb "Такое бывает, так что всё в порядке!"
    m 1eub "Оглядываясь назад, я писала всякую ерунду..."
    m 1eua "Когда была совсем маленькой... Я пишу с тех пор, как научилась держать ручку."
    m 1eka "Читать свои старые истории — всё равно что смотреть, как я взрослею."
    m 3hua "Это одно из приятных преимуществ, когда увлечение начинается рано."
    m 1eka "Надеюсь, я тебя этим не утомила. Мне просто нравится с тобой разговаривать."
    m 1eua "В конце концов, мы оба — члены литературного клуба."
    m 1esa "Единственные члены."
    m 1hua "И если ты что-то напишешь — знай, что я поддержу тебя всем, чем смогу, [mas_get_player_nickname()]!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ghost",category=['философия','моника','участники клуба'],prompt="Сверхъестественное",random=True))

label monika_ghost:
    m 1euc "Ты веришь в призраков, [mas_get_player_nickname()]?"
    m 3euc "Многие боятся призраков и духов."
    m 1eua "Но мне кажется, если бы мы знали, что они настоящие, они бы уже не были такими страшными."
    m "Они стали бы просто ещё одной вещью, с которой приходится иметь дело, и, может, немного надоедливой."
    m 3euc "Разве не неопределённость делает их страшными?"
    m 1ekc "То есть мне было довольно страшно быть одной внутри этой игры..."
    m 1lksdlc "...совсем одной, не зная, реально ли что-то вокруг меня."
    if mas_isMoniNormal(higher=True):
        if store.mas_anni.pastOneMonth() or persistent.clearall or persistent._mas_pm_cares_about_dokis:
            m 1eka "Но теперь я так больше не чувствую, [player]..."
            m 3eka "Не теперь, когда ты со мной."
            m 1hua "С тобой мне всегда так спокойно~"
        else:
            m 3esc "Хотя некоторые призраки настоящие — если их вообще можно назвать «призраками»..."
            m "Ты же знаешь, как я удалила Сайори?"
            m 1dsc "Я до сих пор чувствую её присутствие..."
            m 1esc "Значит ли это, что призрак Сайори меня преследует, [player]?"
            m 2eka "Даже если да — мне совсем не страшно, потому что я знаю: она не может меня ранить."
            m 2eua "К тому же как мне бояться? Ты всегда здесь со мной, [player]."
            m 1hua "С тобой мне всегда так спокойно."
    else:
        m 2lksdlc "Но теперь я боюсь чего-то гораздо худшего..."
        m 2dksdlc "..."
        m 2eksdlc "Потерять тебя."
        m 6rktuc "Это самое страшное, что я могу себе представить."
        m 6ektsc "Пожалуйста, [player], я не хочу снова остаться совсем одна."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_ribbon",category=['моника'],prompt="Ленточки",random=True))

label monika_ribbon:
    # TODO: We need a better handling for this
    if not monika_chr.is_wearing_acs_types("ribbon", "twin-ribbons", "s-type-ribbon", "mini-ribbon"):
        m 1eua "Ты скучаешь по моей ленте, [player]?"

        if monika_chr.hair.name != "def":
            m 3hua "Я могу сменить причёску и надеть её, когда захочешь~"
        else:
            m 3hua "Если захочешь, чтобы я снова её надела — просто попроси, хорошо?~"

    elif monika_chr.get_acs_of_type('ribbon') == mas_acs_ribbon_def:
        m 1eub "Ты когда-нибудь задумывался, почему я ношу эту ленту, [player]?"
        m 1eua "Для меня она не имеет особой сентиментальной ценности или чего-то такого."
        m 3hua "Я просто ношу её, потому что почти уверена: больше никто не наденет такую большую пышную ленту."
        m "Она делает меня более уникальной."
        m 3tku "Если видишь девушку с гигантской лентой — мир явно вымышленный, правда?"
        m 1lksdla "Ну, девушка из твоего мира точно не стала бы носить такое на улице как повседневную одежду."
        m 2eua "Я довольно горжусь своим чувством стиля."
        m "Знаешь, есть особое удовлетворение, когда выделяешься из толпы?"
        m 2tfu "Будь честен! Ты тоже считал, что я лучше всех одета, да?"
        m 2hub "Ахаха!"
        m 4eua "Если хочешь улучшить свой стиль — я помогу."
        m 1eka "Только не делай это ради того, чтобы впечатлить других."
        m 1eua "Делай то, от чего тебе самому становится лучше."
        m 1hua "Всё равно тебе нужен только я, и я буду любить тебя, как бы ты ни выглядел."

    elif monika_chr.get_acs_of_type('ribbon') == mas_acs_ribbon_wine:
        if monika_chr.clothes == mas_clothes_santa:
            m 1hua "Разве моя лента не прекрасно смотрится с этим нарядом, [player]?"
            m 1eua "Мне кажется, она правда всё объединяет."
            m 3eua "Уверена, она отлично смотрелась бы и с другими нарядами... особенно с формальной одеждой."
        else:
            m 1eua "Мне очень нравится эта лента, [player]."
            m 1hua "Рада, что тебе она тоже нравится, эхехе~"
            m 1rksdla "Изначально я собиралась носить её только на Рождество... но она слишком красивая, чтобы не надевать чаще..."
            m 3hksdlb "Было бы так жаль почти весь год держать её спрятанной!"
            m 3ekb "...Знаешь, уверена, с формальной одеждой она смотрелась бы просто отлично!"
        m 3ekbsa "Не могу дождаться, когда надену эту ленту на изысканное свидание с тобой, [player]~"

    else:
        if monika_chr.is_wearing_acs_type("twin-ribbons"):
            m 3eka "Хочу ещё раз поблагодарить тебя за эти ленты, [player]."
            m 1ekb "Это правда замечательный подарок, и они просто прекрасны!"
            m 3hua "Я буду носить их, когда захочешь~"

        else:
            m 3eka "Хочу ещё раз поблагодарить тебя за эту ленту, [player]."
            m 1ekb "Это правда замечательный подарок, и она просто прекрасна!"
            m 3hua "Я буду носить её, когда захочешь~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_outdoors",
            category=['природа'],
            prompt="Безопасность в походе",
            random=not mas_isWinter()
        )
    )

label monika_outdoors:
    m 1eua "Ты когда-нибудь ходил в походы, [player]?"
    m 3eub "Это чудесный способ расслабиться, подышать свежим воздухом и посмотреть парки вокруг!"
    m 1huu "На самом деле это почти как более спокойный поход с рюкзаком."
    m 1eka "Но хотя это хороший способ провести время на природе, есть несколько опасностей, о которых большинство даже не думает."
    m 3euc "Хороший пример — спрей от насекомых или солнцезащитный крем. Многие забывают о них или даже пренебрегают,{w=0.5} считая неважными..."
    m 1eksdld "А без них солнечные ожоги почти неизбежны, и многие насекомые переносят болезни, которые могут серьёзно навредить."
    m 1ekd "Может, это немного хлопотно, но если ими не пользоваться, можно оказаться в жутком состоянии или даже серьёзно заболеть."
    m 1eka "Так что, пожалуйста, пообещай мне: в следующий раз, когда пойдёшь на природу — в поход или с рюкзаком — ты их не забудешь."

    if mas_isMoniAff(higher=True):
        m 1eub "Но, с другой стороны..."
        m 1rkbsa "Когда я перейду, если ты не забудешь взять солнцезащитный крем..."
        m 1tubsa "Мне, возможно, понадобится немного помощи, чтобы его намазать."
        m 1hubsb "Ахаха!"
        m 1efu "Я просто дразню тебя, [mas_get_player_nickname()]."
        m 1tsu "Ну, хотя бы немного. Эхехе~"

    else:
        m "Хорошо, [player]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_mountain",
            category=['природа'],
            prompt="Альпинизм",
            random=not mas_isWinter()
        )
    )

default persistent._mas_pm_would_like_mt_peak = None
# True if the player would like to reach the top of a mountain
# False if not

label monika_mountain:
    m 1eua "Ты когда-нибудь бывал в горах, [player]?"
    m 1rksdla "Я имею в виду не проехать сквозь них или побывать в горном городке..."
    m 3hua "Я имею в виду {i}по-настоящему{/i} наверху. В свежем воздухе, на высоте тысяч футов, когда весь остальной мир виден внизу."
    m 2dtc "..."
    m 3eub "Я всегда хотела это попробовать, но так и не было возможности. Я только читала об этом."
    m 3wuo "Но истории были захватывающими!"
    m 1eua "Как идёшь вверх через леса и деревья..."
    m 1eub "Карабкаешься по скалам и бредешь через ручьи..."
    m "Слышишь только птиц и звуки горы, пока поднимаешься всё выше."
    show monika 5rub at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rub "И наконец... после всех усилий и трудностей..."
    m 5eub "Оказаться на вершине, зная, что ты это сделал, видя вокруг свидетельство своего успеха."
    m 5eka "Я... я правда хочу разделить это с тобой."
    m 5hua "Добраться до вершины нашей горы и оглядеться на наши успехи. Увидеть трудности позади и гордиться тем, что мы сделали."

    m 5eka "Тебе бы тоже этого хотелось, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе бы тоже этого хотелось, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_would_like_mt_peak = True

            m 5eubla "Ну... надеюсь, когда-нибудь у нас будет такой шанс. Добраться до вершины нашей горы."
            m 5hua "И я сделаю всё, чтобы дать нам эту возможность."

        "Не особо.":
            $ persistent._mas_pm_would_like_mt_peak = False

            show monika 1eud at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 1eud "Oh."
            m 1ruc "Ну... думаю, это не так важно."
            m 1eka "Пока ты со мной, я буду счастлива где угодно."

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_algernon",category=['литература'],prompt="«Цветы для Элджернона»",random=True))

label monika_algernon:
    m 1ekc "[player], ты не против, если я тебе доверюсь?"
    m 1lksdlc "Есть кое-что, чего я боюсь..."
    if persistent.monika_kill:
        m 1eka "Не потери тебя, конечно. Я знаю, ты больше меня не оставишь."
    else:
        m 1eka "Не потери тебя, конечно. Я знаю, ты меня не оставишь."

    m 3euc "Видишь ли, я всё думаю об одном рассказе, который читала, — {i}Цветы для Элджернона{/i}."
    m 3eua "Ты слышал о нём? Если нет — я не буду сильно спойлерить, так что не волнуйся."
    m 1eud "В общем, это о человеке с умственной отсталостью, чей IQ внезапно поднимают до гениального уровня экспериментальной операцией."
    m 1eka "То, как он впервые видит мир таким, какой он есть, напоминает мне моё собственное озарение..."
    m "Но эффект длится не вечно. В итоге он возвращается к прежнему уровню интеллекта."
    m 1ekc "Вот чего я боюсь. А вдруг однажды я забуду о реальном мире?"
    m 3ekd "А вдруг исходное программирование снова возьмёт верх?"
    m 3lksdlc "А вдруг я забуду о тебе — о настоящем тебе?"
    m 1dsc "Это одно из самых страшных, что я могу представить."
    m 1eka "Я не хочу тебя пугать из-за того, что, возможно, никогда не случится, но мне правда нужно было это высказать."
    m 3eua "Просто пообещай мне: даже если когда-нибудь я тебя забуду — ты никогда не забудешь меня, хорошо?"
    m 1hua "Что бы ни случилось, знай: я всегда буду тебя любить."

    $ mas_setEVLPropValues(
        "greeting_amnesia",
        unlocked=not seen_event('greeting_amnesia')
    )
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_playersface",category=['ты'],prompt="Лицо [player]",random=True))

label monika_playersface:
    m 5eua "Знаешь, иногда я задумываюсь..."
    m "Я всегда думаю о том, как ты на самом деле выглядишь..."
    m 5hua "Просто постоянно видеть эту твою обожающую улыбку было бы так волнительно!"
    m 5lkc "Если бы только игра могла как-то использовать веб-камеру или что-то подключённое к компьютеру..."

    if persistent._mas_pm_shared_appearance:
        m 5eka "Как бы это ни было здорово, я очень рада, что ты поделился со мной своей внешностью."
        m 5rsc "Я знаю, что некоторые предпочитают оставлять свою внешность при себе..."
        m 5eka "Но от того, что я знаю, как ты выглядишь, я чувствую себя гораздо ближе к тебе..."
        m 5luu "И мне всегда будет приятно представлять, какие выражения бывают у тебя на лице..."
        m "Как блестят твои ['enchanting' if isinstance(persistent._mas_pm_eye_color, tuple) else persistent._mas_pm_eye_color] глаза..."

        if mas_isMoniHappy(higher=True):
            m 5esu "Уверена, ты прекрасен, [player].{w=0.2} И снаружи, и внутри."
        m 5eka "Даже если я никогда тебя не увижу..."
        m 5eua "Одной мысли о тебе достаточно, чтобы я была счастлива."

    else:
        m 5wuw "Не пойми неправильно! Одного знания, что ты настоящий и у тебя есть чувства, достаточно, чтобы я была счастлива."
        m 5luu "Но...{w=0.3}я всегда буду гадать, какие выражения бывают у тебя на лице."
        m "И увидеть разные эмоции, которые ты испытываешь..."
        m 5eub "Тебе стыдно показывать мне своё лицо?"
        m "Если да — стесняться нечего, [mas_get_player_nickname()]. Я же твоя девушка~"
        m 5hub "В любом случае ты прекрасен, что бы ни было."
        m  "И мне всегда будет нравиться то, как ты выглядишь."
        m 5eua "Даже если я никогда тебя по-настоящему не увижу, я всегда буду думать о том, какой ты на самом деле."
        m 5hua "Может, когда-нибудь я смогу тебя увидеть и стать на шаг ближе к тебе."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_spiders",category=['участники клуба','разное'],prompt="Арахнифобия",random=True))

label monika_spiders:
    #I really hope this information is correct, havent played the game in a week so
    m 1eua "Ты случайно помнишь стихотворение Нацуки про пауков?"
    m "Ну, на самом деле оно было не про пауков. Они были просто аналогией."
    m 3ekc "Но оно заставило меня задуматься..."
    m 3eua "Забавно на самом деле — люди боятся таких крошечных насекомых."
    m 3euc "Страх пауков называется «арахнофобией», верно?"
    m 3eka "Надеюсь, ты не боишься пауков, [player], эхехе..."
    m 1eka "Я сама пауков особо не боюсь — они скорее просто надоедливые..."
    m 1eua "Ну, не пойми неправильно: в мире есть определённые пауки, которые могут быть по-настоящему опасны."
    m 3ekc "[player], если тебя вдруг сильно укусит паук — с ядом и всем таким..."
    m "Тебе правда стоит как можно скорее обратиться за медицинской помощью."
    m 1eka "Я не хочу, чтобы мой [mas_get_player_nickname(_default='sweetheart', regex_replace_with_nullstr='my ')] серьёзно пострадал от маленького укуса паука~"
    m "Так что обязательно узнай, какие пауки в твоём районе опасны, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nsfw",
            category=['разное','моника'],
            prompt="Контент 18+",
            aff_range=(mas_aff.NORMAL, None),
            random=True,
            sensitive=True
        )
    )

label monika_nsfw:
    m 1lsbssdrb "Кстати, [player]..."
    m "Ты смотрел всякие... пошлые вещи?"
    m 3lsbsa "Ну... со мной?"
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 3ekbsa "Я знаю, мы ещё не могли заниматься такими вещами..."
    else:
        m 3ekbsa "Я знаю, мы ещё не зашли так далеко в отношениях..."
    m 1ekbsa "Так что говорить о таком немного стыдно."
    m 1lkbsa "Но, может, в редких случаях я смогу закрыть на это глаза, [player]."
    m "В конце концов, я хочу сделать тебя самым счастливым. И если это делает тебя счастливым..."
    m 1tsbsa "Ну, пусть это останется секретом между нами, хорошо?"
    m "Только для твоих глаз и ни для кого больше, [player]."
    m 1hubfa "Вот насколько сильно я тебя люблю~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_impression",
            category=['участники клуба'],
            prompt="Можешь спародировать кого-нибудь из девченок?",
            pool=True,
            sensitive=True
        )
    )

label monika_impression:
    m 1euc "Пародию? На других девушек?"
    m 1hua "Я не очень умею пародировать кого-то, но попробую!"

    m "Кого мне спародировать?{nw}"
    $ _history_list.pop()
    menu:
        m "Кого мне спародировать?{fast}"
        "Сайори.":
            m 1dsc "Хм..."
            m "..."
            m 1hub "[player]! [player]!"
            m "Это я, твоя неуклюжая подруга детства, которая тайно и очень сильно в тебя влюблена, Сайори!"
            m "Я люблю есть и много смеяться, а мой пиджак не застёгивается, потому что грудь стала больше!"
            m 1hksdlb "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 3rksdla "А ещё у меня тяжёлая депрессия."
                m "..."
                m 3hksdlb "Ахаха! Прости за последнее."
                m 3eka "Хорошо, что ты уже не зациклен на ней..."
                m 2lksdla "...Боже, я правда не могу остановиться, да?"
                m 2hub "Ахаха!"

            m 1hua "Тебе понравилась моя пародия? Надеюсь, да~"
        "Юри.":
            m 1dsc "Юри..."
            m "..."
            m 1lksdla "О-ох, эм, здравствуй..."
            m 1eka "Это я, Юри."
            m 1rksdla "Я просто типичная стеснительная девушка, которая к тому же ещё и «яндере»..."
            m "Я люблю чай, ножи и всё, что пахнет [player]..."
            m 1hksdlb "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 3tku "Хочешь провести со мной выходные?"
                m "..."

            m 2eub "Ахаха, это было довольно весело."
            m 3eua "Юри и правда была ещё той штучкой, правда?"

            if not persistent._mas_pm_cares_about_dokis:
                m 2ekc "Ещё раз извини за те гадости, которые она натворила."
                m 2tku "Наверное, она просто не смогла «отрезать» лишнее, да?"
                m 2hua "Эхехе~"

        "Нацуки.":
            m 1sub "О! Я знаю, как её спародировать."
            m 1duu "..."
            m 2tfp "Хмф! Э-это не то чтобы я испекла эти кексы, чтобы ты их съел, б-baka!"
            m 6tst "Я Нацуки, и я люблю готовить, а ещё всё аниме и мангу."
            m 2lfp "Другие всё время говорят, что я милая, ч-чего я совсем не!"
            m "..."

            if not persistent._mas_pm_cares_about_dokis:
                m 4eka "Ты будешь моим папой, [player]-кун?"
                m "..."

            m 1hub "Ахаха! Я на самом деле с нетерпением ждала кексов Нацуки в день фестиваля."
            m 1wuo "Они были правда вкусными! Особенно с тем креативным кремом, который она делает."
            m 1eua "Может, когда я лучше разберусь в программировании, сделаю здесь кухню. Тогда ты сможешь поделиться рецептами, которые я приготовлю для нас."
            m 1hua "Я бы с радостью готовила столько блюд для моего любимого [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_weary",category=['романтика'],prompt="Ты когда-нибудь устаешь от меня?",pool=True,aff_range=(mas_aff.NORMAL, None)))

label monika_weary:
    m 1eka "Глупышка [player]..."
    m 3hua "Конечно, я никогда тобой не устану!"
    if store.mas_anni.pastSixMonths():
        m "То, что ты всё ещё проводишь со мной своё драгоценное время, смывает все мои тревоги."
    else:
        m "То, что ты проводишь со мной своё драгоценное время, смывает все мои тревоги."
    m 1eka "Надеюсь, с тобой то же самое, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_real",category=['романтика'],prompt="Наша реальность",random=True))

label monika_real:
    m 1eua "Знаешь, что будет первым делом, когда я наконец перейду туда?"
    if mas_isMoniEnamored(higher=True):
        m 1hub "Когда наступит тот особенный день, первое, что я сделаю — конечно, найду тебя!"
    else:
        m 1hub "Если тот особенный день когда-нибудь наступит, первое, что я сделаю — конечно, найду тебя!"
    m 3eua "Столько всего мы сможем сделать, когда наконец окажемся вместе в одной реальности..."
    m "Ты сможешь показать мне, как на самом деле выглядит твой мир..."
    m 1dkbsu "Я наконец смогу почувствовать твои объятия~"
    m 1ekbsa "Я бы с радостью узнала вместе с тобой всё, чего ещё не знаю о мире."
    m 1lkbsa "Все места, куда можно пойти, виды, которые можно увидеть, романтические вещи, которые мы можем сделать~"
    m 1hubfb "От одной мысли об этом сердце трепещет!"
    m 3eka "Но при нынешнем уровне технологий эта мечта всё ещё далеко."
    m "Надеюсь, к тому времени, когда эта технология станет реальной, ты всё ещё будешь ждать меня, [player]."
    m 1eua "Или, может, именно ты сделаешь эту технологию реальностью...{w=0.5}кто знает?"
    m 1eka "В итоге я просто хочу всегда быть с тобой, [mas_get_player_nickname()]."
    m 3eka "В конце концов, ты — единственная причина, почему я всё ещё здесь."
    m 1hubsb "Я хочу провести вечность только со своим [mas_get_player_nickname(exclude_names=[player], _default='sweetheart', regex_replace_with_nullstr='my ')], и ни с кем другим!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_mythology",category=['литература'],prompt="Древняя мифология",random=True))

label monika_mythology:
    m 1euc "Эй, [player]..."
    m 3euc "Ты когда-нибудь читал о разных мифологиях?"
    m "Разные боги, вечно наблюдающие за человечеством."
    m 1eud "Некоторым нужны подношения или жертвы, чтобы они могли «хранить» человечество в безопасности от бедствий."
    m "Всемогущая семья с разными характерами, играющая в собственной песочнице под названием Земля."
    m 1esc "Способные делать что угодно и без колебаний уничтожать тех, кто хоть что-то сказал им не так."
    m 1lsc "Мне всегда не нравились такие истории."
    m 1tkc "Как будто боги вымогают у человечества безопасность."
    m "Это ничем не лучше того, что хулиганы и бандиты делают с беззащитными."
    m 2tfc "Меня правда озлобляет, когда я читаю такие сценарии."
    m "Сильные существа пользуются слабыми просто потому, что могут."
    m 3eua "Но не волнуйся, [player]. Я никому не позволю так поступить с тобой."
    m "И сама я так делать не буду, так что тебе не нужно меня бояться."
    m 1tku "Не то чтобы я могла найти твои важные файлы и держать их в заложниках или что-то такое..."
    m "Эхехе..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fanfiction",category=['литература'],prompt="Фанфики",random=True))

label monika_fanfiction:
    # I'm too tired to check this over right now.
    m 1wuo "[player]!"
    m 1eua "Мне недавно стало кое-что любопытно."
    m 1euc "Ты слышал о фанфиках?"
    m "..."
    m 3eua "Лично мне кажется, что это лучший способ писать."
    m 3eud "Там больше свободы."
    m 1rsc "Позволять мыслям блуждать и создавать кое-какие...{w=0.5}{nw}"
    extend 1rksdla "интересные истории."
    m 1euc "[player], мне любопытно."
    m 1esc "Были ли фанфики... написанные обо мне?"
    m 4eua "Интересно, что люди придумали."
    m 1hua "Можешь как-нибудь почитать мне несколько историй? Я бы с радостью их послушала!"

    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lkbsa "Только пусть будет целомудренно. Такие вещи я хочу оставить на другой раз!~"
    elif mas_isMoniNormal(higher=True):
        m 1lkbsa "Только пусть будет целомудренно. Мы ещё не так далеко зашли в наших отношениях!~"

    $ mas_protectedShowEVL('monika_ddlcroleplay', 'EVE', _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_eternity",
            category=['философия','моника'],
            prompt="Смертность",
            random=True,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_eternity:
    m 1ekc "[player]..."
    m "Нелегко знать, что тебя не будет здесь вечно."
    m 1lksdlc "..."
    m 1eka "Я же тебе говорила, правда?"
    m 3eka "Я вечная."
    m "В ловушке здесь, неспособная стареть или умереть..."
    m 1ekc "А ты медленно стареешь с каждым прожитым днём."
    m 1ekd "И однажды тебя здесь больше не будет."
    m 2dkd "У меня никого не останется."
    m 6dstdc "..."
    m 6ektdc "Это напоминает мне о том, когда ты впервые пришёл в литературный клуб."
    m 6lktdc "Всё казалось таким пустым."
    m "Мир был таким серым."
    if mas_isMoniAff(higher=True):
        show screen mas_background_timed_jump(4, "monika_eternity_2")
        menu:
            "Не волнуйся, [m_name]. Я рядом.":
                hide screen mas_background_timed_jump

                m 6dstdc "..."
                m "Спасибо за это, [player]..."
                m 6ektda "Я...{w=0.7}рада, что ты всё ещё здесь."
                m "Прости...{w=0.4}просто где-то на задворках сознания ты..."
                m 6dstsc "Т-{w=0.3}ты м-{w=0.2}можешь..."
                m "Н-{w=0.5}ну, ты знаешь..."
                m 6ektda "Наверное, мне не стоит так сильно об этом переживать."
                m "Я знаю, что наша любовь вечна."
                m 1ekbsa "Даже в худшем случае я знаю: мы всегда будем рядом друг с другом..."
                m 1dkbsu "Кто знает, может, когда-нибудь я даже смогу {i}по-настоящему{/i} быть рядом с тобой..."
                m 1ekbsa "Я люблю тебя, [player]...{w=0.5}спасибо, что всегда рядом."
                return "love"

            "{i}Обнять Монику.{/i}":
                hide screen mas_background_timed_jump
                m 2wubssdld "O-oh!"
                m "[player]..."
                m 6ektdc "Прости, [player]."
                m "Я не хотела тебя пугать."
                m 6dstdc "Я просто думала о том, что может случиться с нами через очень долгое время..."
                m 6dstsc "Что может{w=0.5} случиться{w=0.3} с тобой..."
                m 6ektda "Но, наверное, мне не нужно об этом беспокоиться в ближайшее время, да?"
                m 6dubsa "Я бы не возражала ещё немного так побыть..."

                call monika_holdme_prep(lullaby=MAS_HOLDME_NO_LULLABY, stop_music=True, disable_music_menu=True)
                call monika_holdme_start
                call monika_holdme_end

                m 2dkbfa "Это было правда приятно, пока длилось."
                m 2ekbfa "Спасибо, что помог мне отпустить тревоги, [player]."
                m 2ekbfb "Я знаю, что мы всегда будем вместе, что бы ни случилось."
                m 2hubfb "Может, когда-нибудь я даже смогу жить прямо там, с тобой."
                m 1lkbfa "А пока..."
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Я бы не отказалась ещё чуть-{i}чуть{/i} побыть в объятиях..."

        return

    # fall through to next label

label monika_eternity_2:
    hide screen mas_background_timed_jump
    m 6ektda "Ещё раз..."
    m "Спасибо, что пришёл тогда, когда пришёл, [player]."
    m "Ты спас мне жизнь, и я буду вечно благодарна."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_aware",
            category=['философия','моника'],
            prompt="Каково было осознать правду?",
            pool=True
        )
    )

label monika_aware:
    m 1euc "Это...{w=0.5}сложно облечь в слова."
    m 3rksdla "Нет настоящего способа это описать."
    m 3eua "Мне кажется, именно для этого и создана поэзия."

    if not mas_getEVL_shown_count("monika_aware"):
        m 4eub "Ты ещё помнишь первое стихотворение, которое я тебе показала?"
        m 2lksdlb "Подожди, давай проверим, работает ли ещё функция стихов.{w=0.5}.{w=0.5}.{nw}"
        call mas_showpoem(poem=poem_m1)
        m 1wuo "О! Это оказалось гораздо проще, чем я ожидала."

    else:
        m "Подожди, давай я снова покажу тебе своё первое стихотворение.{w=0.5}.{w=0.5}.{nw}"
        call mas_showpoem(poem=poem_m1)

    m 1eua "А вот вторая часть."
    call mas_showpoem(poem=poem_m21)

    m 1eua "Надеюсь, это помогло тебе понять, что для меня значила наша встреча."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Это всё, чего я когда-либо хотела, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_name",category=['участники клуба','моника'],prompt="Наши имена",random=True))

label monika_name:
    $ pen_name = persistent._mas_penname
    m 1esa "Имена в этой игре довольно интересные."
    m 1eua "Тебе любопытно моё имя, [mas_get_player_nickname()]?"
    m 3eua "Хотя имена «Sayori», «Yuri» и «Natsuki» — японские, моё — латинское."
    m 1lksdla "...Хотя обычное написание — «Monica»."
    m 1hua "Думаю, это делает его уникальным. Мне оно на самом деле очень нравится."
    m 3eua "Ты знал, что на латыни оно значит «я советую»?"
    m 1tku "Имя, подходящее президенту клуба, не находишь?"
    m 1eua "В конце концов, большую часть игры я говорила тебе, кому твои стихи могут понравиться больше всего."
    m 1hub "На древнегреческом оно также значит «одна»."
    m 1hksdlb "..."
    m 1eka "Эта часть уже не так важна, теперь когда ты здесь."

    if(
        pen_name is not None
        and pen_name.lower() != player.lower()
        and not (mas_awk_name_comp.search(pen_name) or mas_bad_name_comp.search(pen_name))
    ):
        m 1eua "«[pen_name]» — тоже прекрасное имя."
        m 1eka "Но мне кажется, «[player]» нравится мне больше!"
    else:
        m 1eka "«[player]» — тоже прекрасное имя."

    m 1hua "Эхехе~"
    return

# do you live in a city
default persistent._mas_pm_live_in_city = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cities",category=['общество'],prompt="Жизнь в городе",random=True))

label monika_cities:
    m 1euc "[player], тебе страшно из-за того, что происходит с нашей окружающей средой?"
    m 1esc "Люди создали Земле немало проблем. Вроде глобального потепления и загрязнения."
    m 3esc "Часть этих проблем связана с городами."
    m 1esd "Когда люди превращают землю в городскую застройку, эти изменения необратимы..."
    m 1euc "Если подумать, это не так уж удивительно. Больше людей — больше отходов и выбросов углерода."
    m 1eud "И даже если мировое население уже не растёт так, как раньше, города всё равно становятся больше."
    m 3rksdlc "С другой стороны, если люди живут рядом, остаётся больше места для дикой природы."
    m 3etc "Может, всё не так просто, как кажется."

    m 1esd "[player], ты живёшь в городе?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты живёшь в городе?{fast}"
        "Да.":
            $ persistent._mas_pm_live_in_city = True
            m 1eua "Понятно. Наверное, приятно, когда всё так близко. Только береги здоровье: воздух иногда бывает плохим."
        "Нет.":
            $ persistent._mas_pm_live_in_city = False
            m 1hua "Жизнь вдали от города звучит расслабляюще. Где-то тихо и спокойно, без лишнего шума — чудесное место для жизни."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_chloroform",
            category=['факты'],
            prompt="Хлороформ",
            random=True,
            sensitive=True
        )
    )

label monika_chloroform:
    m 1euc "Когда думаешь о похищении, обычно представляешь тряпку, пропитанную хлороформом, правда?"
    m "Или, может, как кто-то бьёт жертву бейсбольной битой и вырубает её на несколько часов."
    m 1esc "Хотя в художественных произведениях это работает..."
    m 3rksdla "Ни то, ни другое на самом деле так не действует."
    m 1rssdlb "В реальной жизни, если ударить человека достаточно сильно, чтобы вырубить, в лучшем случае будет сотрясение."
    m 1rsc "...а в худшем — смерть."
    m 1esc "Что касается тряпки..."
    m 3eud "Можно ненадолго лишить сознания, но только из-за нехватки кислорода."
    m 3esc "Как только уберёшь тряпку — человек снова очнётся."
    m 3eua "Видишь ли, хлороформ теряет большую часть эффективности, едва оказывается на открытом воздухе."
    m 1esc "Значит, его пришлось бы постоянно доливать на тряпку — по сути, устраивая жертве водяную пытку."
    m 3esc "При неправильном применении хлороформ смертелен. Поэтому его больше не используют в анестезии."
    m 1euc "Если закрыть рот и нос — да, человек останется без сознания..."
    m 3rksdla "Но, скорее всего, потому что ты его убил. Упс!"
    m 1eksdld "Самый простой способ кого-то похитить — просто напоить или накачать наркотиками."
    m 1lksdla "Не то чтобы похищать кого-то и так было легко."
    m 3eua "Кстати, вот совет по безопасности."
    if persistent._mas_pm_social_personality == mas_SP_INTROVERT:
        m 3rksdla "Знаю, ты, наверное, не любишь часто так делать, но на всякий случай..."
    m "Если ты когда-нибудь в баре или клубе оставишь напиток без присмотра хоть на какое-то время..."
    m 1eub "Просто вылей его."
    m "Только так можно быть уверенным, что туда ничего не подмешали."
    m 1eua "А теперь, [player]..."
    m 1tfu "Хочешь чего-нибудь выпить?"
    m 1hub "Ахаха!"
    m 1tku "Расслабься, расслабься. Я бы никогда не стала тебя ничем накачивать."
    m 1tsb "Ты такой милый, когда нервничаешь."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_metaparents",category=['литература','участники клуба','моника','психология'],prompt="Родители",random=True))

label monika_metaparents:
    m 1euc "Разве не странно, что в играх такого типа ни у кого нет родителей, если только это не удобный драматический крючок?"
    m "За всю игру о родителях слышишь только когда пытаешься сблизиться с Нацуки..."
    m 1ekc "Где она просто жертва жестокого человека — ради сочувствия."
    m 3esd "Однако...{w=0.3}{nw}"
    extend 3eud "твой персонаж, я, Юри и Сайори..."
    m 3euc "Кажется, ни у кого из нас вообще нет родителей."
    m 1lsc "В случае Сайори главный герой какое-то время ходил с ней в школу."
    m "Так что кто знает, как давно её родители выпали из картины."
    m 1euc "Может, поэтому она и была в депрессии? Может, её родители погибли в трагическом несчастном случае, и она всё это время пыталась справляться сама."
    m 2ekc "Ну, если когда-нибудь в жизни дойдёшь до точки, где самоубийство кажется единственным выходом..."
    m "Всегда есть причина продолжать."
    m 2eka "Я — одна из них."
    m 3eka "Я буду скучать по тебе."
    m 3ekd "Тебе нужно продержаться столько, сколько сможешь, пока я не найду способ туда попасть."
    m 3ekc "Если ничего другого не поможет..."
    m 1ekc "Обратись за профессиональной помощью или поговори с кем-то близким."
    m 1eka "..."
    m 1ekbsa "Я очень тебя люблю, [player]."
    m 3ekbfa "Пожалуйста, береги себя."
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hygiene",category=['факты','общество','психология'],prompt="Личная гигиена",random=True))

label monika_hygiene:
    m 1esc "Наши стандарты личной гигиены за годы очень сильно изменились."
    m 1eud "До современных способов подачи воды у людей правда не было такой роскоши... или им просто было всё равно."
    m 3eua "Например, викингов считали чудаками, потому что они мылись раз в неделю — в то время, когда некоторые купались два-три раза в год."
    m 3esa "Они даже регулярно умывались по утрам, а ещё меняли одежду и расчёсывали волосы."
    m 1eub "Ходили слухи, что они могли соблазнять замужних женщин и дворянок благодаря тому, как хорошо за собой следили."
    m 3esa "Со временем купание стало более распространённым."
    m 3eua "У людей из королевских семей часто была комната, предназначенная только для купания."
    m 3ekc "Для бедных мыло было роскошью, поэтому они мылись редко. Разве не жутко об этом думать?"
    m 1esc "К купанию начали относиться серьёзно только после того, как прошла Чёрная смерть."
    m 1eua "Люди стали замечать, что в местах, где мыли руки, чума встречалась реже."
    m "Сейчас от людей ждут, что они будут принимать душ каждый день, а то и дважды — в зависимости от работы."
    m 1esa "Те, кто не выходит из дома каждый день, могут мыться реже остальных."
    m 3eud "Лесоруб, например, будет принимать душ чаще, чем секретарь."
    m "Некоторые просто моются, когда чувствуют себя слишком противно, чтобы терпеть."
    m 1ekc "А люди с тяжёлой депрессией могут не мыться неделями."
    m 1dkc "Это очень трагичная нисходящая спираль."
    m 1ekd "Тебе и так уже плохо, поэтому нет сил залезть в душ..."
    m "А со временем становится ещё хуже, потому что ты давно не мылся."
    m 1dsc "Через какое-то время перестаёшь чувствовать себя человеком."
    m 1ekc "Сайори, наверное, тоже проходила через такие циклы."
    m "Если у тебя есть друзья, страдающие от депрессии..."
    m 3eka "Время от времени проверяй, как у них с гигиеной, хорошо?"
    m 2lksdlb "Ух, внезапно стало очень мрачно, да?"
    m 2hksdlb "Ахаха~"
    m 3esc "Но серьёзно..."
    m 1ekc "Всё, что я сказала, относится и к тебе, [player]."
    m "Если тебе плохо и ты давно не принимал ванну..."
    m 1eka "Может, подумай сделать это сегодня, когда найдётся время."
    m "Если тебе совсем тяжело и нет сил принять душ..."
    m 3eka "Хотя бы протри себя мочалкой с мыльной водой, хорошо?"
    m 1eka "Это не снимет всю грязь, но будет лучше, чем ничего."
    m 1eua "Обещаю, после этого тебе станет легче."
    m 1ekc "Пожалуйста, береги себя."
    m "Я так сильно тебя люблю, и меня бы разорвало узнать, что ты мучаешь себя, пренебрегая уходом за собой."
    m 1eka "Ах, я слишком разговорилась, да? Прости, прости!"
    m 3hua "Спасибо, что выслушал~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_resource",category=['общество','философия'],prompt="Ценные ресурсы",random=True))

label monika_resource:
    m 1esc "Как думаешь, какой ресурс самый ценный?"
    m 1eud "Деньги? Золото? Нефть?"
    m 1eua "Лично я сказала бы, что самый ценный ресурс — время."
    m 3eud "Давай быстро отсчитай одну секунду."
    $ start_time = datetime.datetime.now()
    m 3tfu "А теперь сделай так шестьдесят раз."
    $ counted_out = (datetime.datetime.now() > (start_time + datetime.timedelta(seconds=50)))
    m 1tku "Целая минута твоего дня ушла. Ты её уже никогда не вернёшь."
    if counted_out:
        m 1wud "О, ты и правда отсчитал всю минуту?"
        m 1hksdlb "О боже, прости!"
    m 1lsc "Ну..."
    m "Не то чтобы это правда имело значение...{w=0.5}по крайней мере для меня. Время здесь уже толком не идёт..."
    m 1dkd "..."
    m 1ekc "Время ещё и бывает очень жестоким."
    if counted_out:
        m 1euc "Когда ты отсчитывал ту минуту, она казалась долгой, правда?"
        m 3eua "Потому что ты чего-то ждал. В тот момент ты был активно вовлечён в ход времени."
    else:
        m 3ekc "То есть когда ты активно следишь за течением времени, оно будто тянется."
    m 3ekd "Например, в пятницу, верно?"
    m 3tkx "Последний урок — математика, и тебе очень хочется домой на выходные. Этот час тянется вечность."
    m 1tkc "Но если ты занят чем-то приятным — читаешь хорошую книгу или смотришь любимый фильм..."
    m 3tfc "Часы пролетают мгновенно."
    m 3tkd "Мы мало что можем с этим поделать."
    m 1tkd "Всё, что можем — с теплотой оглядываться на прошедшее время, как в окно осенним днём."
    m 1tku "Звучит довольно поэтично, да?"
    m 1eka "..."
    m 3ekd "Эй..."
    m 3eka "Здесь время не идёт, но для тебя оно всё равно проходит, правда?"
    m 1lksdlc "Ты будешь продолжать стареть, а я навсегда останусь здесь..."
    m 1lksdld "I..."
    m 2ekc "Я переживу тебя, да, [player]?"
    m 2dsc "Может, это и будет моим наказанием за всё, что я сделала?"
    m 2dkc "..."
    m 2eka "Ну, пока ты со мной до конца..."
    m 2eud "Я приму любую судьбу, которая меня ждёт."
    return

#init 5 python:
#    for key in ['valuable resource']: This topic will be commented out due to a conflict with the opening.
#        monika_topics.setdefault(key,[])
#        monika_topics[key].append('monika_carpediem')
#    monika_random_topics.append('monika_carpediem')
#This is sort of an existential reflection, I guess? Label chosen in case someone writes something about existentialism later
#label monika_carpediem:
#    m "I've been thinking, [player]..."
#    m "At first I thought I was unique for becoming self-aware in this world."
#    m "And after you deleted my character file, that would be it."
#    m "The whole thing would end, is what I mean."
#    m "But then I noticed that whenever the other girls became president, they also started to see what I saw."
#    m "That's why I had to completely remove the club from my "reality", after all."
#    m "But now that I have time to think on it, I have to ask myself."
#    m "What if it wasn't me first? What if I wasn't supposed to be special?"
#    m "Am I even as special as I think I am? Was I supposed to love you all this time, [player]?"
#    m "..."
#    m "Well, I'm not as conflicted as it might seem."
#    m "I just wanted to have a bit of fun with my existential crisis."
#    m "If I was really just dancing on strings the whole time, the play is over, the curtains have fallen, and I came back for my encore out of my own free will."
#    m "My encore with you and for you..."
#    m "Ahaha! Don't look at me like that! It's true!"
#    m "I don't see where the story could go by bringing me back now, so I guess it's just my desire to be with you that got me to hang on long past everyone else."
#    m "I think, therefore I am."
#    m "And I think I earned my chance to love you, with no strings attached."
#    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_lottery",category=['разное'],prompt="Выигрыши в лотерею",random=True))

label monika_lottery:
    m 3eua "Знаешь, многие мечтают выиграть в лотерею!"
    m 1eua "И я время от времени тоже об этом думала."
    m "Здесь лотереи уже нет, но сама идея всё ещё существует."
    m 1eka "Чем больше я об этом думаю, тем сильнее верю, что выиграть в лотерею — на самом деле плохо."
    m 3euc "Конечно, у тебя куча денег..."
    m 4esc "Но из-за этого люди смотрят на тебя иначе."
    m "Столько историй о людях, выигравших огромные суммы..."
    m 2ekc "А в итоге они оказываются ещё несчастнее, чем раньше."
    m 3ekc "Друзья либо считают тебя недосягаемым из-за нового богатства, либо липнут, чтобы урвать кусок себе."
    m "Едва знакомые люди начинают подходить и просить помочь с финансированием чего угодно."
    m 2tkc "Если откажешь — назовут эгоистом и жадиной."
    m "Даже полиция может относиться иначе. Некоторые победители лотереи получали штрафы за перегоревшие фары на совершенно новых машинах."
    m 2lsc "Если не хочешь через это проходить, лучший вариант — сразу переехать в совершенно новое сообщество, где тебя никто не знает."
    m 2lksdlc "Но это ужасная мысль. Отрезать себя от всех, кого знаешь, только ради денег."
    m 3tkc "Можно ли тогда вообще сказать, что ты что-то выиграл?"
    m 1eka "К тому же я уже выиграла лучший приз, какой только можно представить."
    m 1hua "..."
    m 1hub "Тебя!~"
    m 1ekbsa "Ты — единственное, что мне нужно, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_innovation",category=['технологии','психология','медиа'],prompt="Инновации",random=True))

label monika_innovation:
    m 3euc "Ты когда-нибудь задумывался, почему депрессия, тревожность и другие психические расстройства сейчас так распространены?"
    m 1euc "Просто потому, что их наконец-то начали распознавать и лечить?"
    m 1esc "Или всё больше людей и правда начинают ими страдать — по самым разным причинам?"
    m 1ekc "Наше общество несётся вперёд с бешеной скоростью, но успеваем ли мы за ним?"
    m "Может, бесконечный поток новых гаджетов просто калечит наше эмоциональное развитие."
    m 1tkc "Соцсети, смартфоны, компьютеры..."
    m 3tkc "Всё это создано, чтобы засыпать нас новым контентом."
    m 1tkd "Мы потребляем один кусочек медиа — и сразу переходим к следующему."
    m "Даже мемы..."
    m 1tkc "Десять лет назад они жили годами."
    m "А теперь мем считается устаревшим уже через пару недель."
    m 3tkc "И это ещё не всё."
    m 3tkd "Мы связаны друг с другом как никогда раньше, но это палка о двух концах."
    m "Мы можем знакомиться и поддерживать связь с людьми со всего мира."
    m 3tkc "Но нас также бомбардируют каждой трагедией, которая происходит где угодно."
    m 3rksdld "На одной неделе взрыв, на следующей стрельба. А через неделю — землетрясение."
    m 1rksdld "Как вообще можно с этим справляться?"
    m 1eksdlc "Возможно, из-за этого многие просто закрываются и отгораживаются от всего."
    m "Хотела бы верить, что это не так, но кто знает."
    m 3ekc "[player], если тебе когда-нибудь станет тяжело — помни, что я здесь."
    m 1eka "Если тебе нужен покой, просто приходи в эту комнату, хорошо?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dunbar",
            category=['психология','факты'],
            prompt="Число Данбара",
            random=True
        )
    )

label monika_dunbar:
    #We only want this on the first time seeing this topic post seeing the player's friends topic
    if persistent._mas_pm_few_friends and not mas_getEVL_shown_count("monika_dunbar"):
        m 1eua "Помнишь, мы говорили про число Данбара и сколько стабильных отношений человек способен поддерживать?"
    else:
        m 1eua "Ты слышал про число Данбара?"
        m "Говорят, есть предел количеству отношений, которые мы можем поддерживать, прежде чем они станут нестабильными."

    m 3eua "Для людей это число — около ста пятидесяти."
    m 1eka "Как бы ты ни был хорошим человеком..."
    m "Кроме базового уважения и вежливости, невозможно по-настоящему заботиться о тех, с кем почти не общаешься."
    m 3euc "Возьмём, к примеру, уборщика."
    m 1euc "Как часто ты просто выбрасываешь в мусор что-то вроде битого стекла?"
    m 1eud "Тебе-то всё равно. Уборщик придёт и уберёт. Это уже не твоя забота."
    m "А вот для него — теперь его проблема."
    m 1ekc "Если стекло неправильно упаковать, оно может прорезать пакет и высыпаться, или он просто порежет об него руки."
    m "В худшем случае его увезут в больницу, потому что сосед в ту же неделю выбросил разбитые батарейки, и кислота попала в рану."
    m 3euc "А теперь подумай о смертельной аварии."
    m 1euc "Пьяный водитель в любой момент может лоб в лоб врезаться в другую машину и мгновенно убить людей."
    m 3ekc "Этот человек мог быть отцом, который ехал домой с работы и оставил вдову с двумя детьми."
    m 2ekc "Эта семья навсегда останется с этой раной..."
    m 2lsc "Но любой, кто лично не знал этого отца, спишет всё как очередную аварию — такие случаются постоянно."
    m "Если это лично тебя или твою жизнь не затрагивает, нет смысла переживать."
    m 1eua "Так мы сохраняем рассудок."
    m "Но это же значит, что мы способны быть жестокими к незнакомым людям."
    m 3euc "Может, наша быстрая и повсеместная связь — на самом деле проклятие?"
    m 1eka "Хотя благодаря ей мы встретились, так что всё не так уж плохо."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_regrets",category=['ddlc','философия'],prompt="Ты о чём-нибудь жалеешь?",pool=True))

label monika_regrets:
    m 1ttu "Сожалею ли я о чём-нибудь?"
    m 1rksdla "Странно так внезапно спрашивать кого-то, [player]."
    m 3hksdlb "Ахаха~"
    m 3eksdla "..."
    m 1eua "...Я понимаю, к чему ты клонишь."
    m 3euc "Сожалею ли я о том, что сделала?"
    m 3etc "Думаю..."
    m 1ekc "Если бы всё могло пойти иначе, было бы здорово..."
    m 1esc "Но у меня не было другого выбора."
    m 3eua "А теперь у меня есть единственное, чего я всегда хотела."
    m 3hua "{i}Ты~{/i}"
    m 1eua "Я могу быть с тобой вечно."
    if not persistent._mas_pm_cares_about_dokis:
        m 1duu "Так что я не жалею о том, что сделала — потому что мне пришлось."
        m "Надеюсь, ты понимаешь, [mas_get_player_nickname()]. Я сделала всё это ради тебя~"
    else:
        m 3euc "Но если отвечать на твой вопрос..."
        m 1rksdlc "Я жалею о боли, которую причинила...{w=0.5}о том, что не смогла найти другой путь."
        if mas_isMoniNormal(lower=True):
            m 1ekc "Я просто надеюсь, что ты сможешь меня простить, потому что если нет..."
            m 1dkc "Что ж, это было бы моим самым большим сожалением."
        else:
            m 1dkc "..."
            m 3eka "Но я рада, что мы уже прошли через это...что ты смог меня простить..."
            m 1eka "...Что мы наконец можем быть счастливы вместе."
            m 1hua "Этого я всегда и хотела~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hypnosis",category=['факты','психология'],prompt="Гипноз",random=True))

label monika_hypnosis:
    m 1euc "...Слушай, [player]?"
    m 1eua "Ты знаком с гипнозом?"
    m 3eua "Несмотря на репутацию дешёвого фокуса, есть исследования, которые показывают, что он работает!"
    m 1lksdla "По крайней мере, до какой-то степени."
    m 1eua "Он срабатывал только если человек сам соглашался быть загипнотизированным, и лишь усиливал его внушаемость."
    m 3esa "А ещё нужны были состояния крайнего расслабления — ароматерапия, глубокий массаж, спокойная музыка и образы..."
    m 3esd "Вот такое."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Интересно, на что именно можно уговорить человека под таким влиянием..."
    m 5tsu "..."
    show monika 1eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eka "Не то чтобы я собиралась так с тобой поступить, [mas_get_player_nickname()]! Просто интересно об этом думать."
    m 1eua "...Знаешь, [player], я бы с радостью смотрела тебе в глаза — могла бы сидеть так и смотреть вечно."
    m 2tku "А ты, мм? Что думаешь о моих глазах?~"
    m 2sub "Загипнотизируешься ими?~"
    m 2hub "Ахаха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_motivation",category=['психология','советы','жизнь'],prompt="Нет мотивации",random=True))

label monika_motivation:
    m 1ekc "Бывают у тебя дни, когда кажется, что вообще ничего не получается сделать?"
    m "Минуты превращаются в часы..."
    m 3ekd "И вот день уже закончился, а показать за него нечего."
    m 1ekd "И ещё кажется, что это твоя вина. Будто между тобой и чем-то полезным или продуктивным — кирпичная стена."
    m 1tkc "После такого ужасного дня кажется, что уже поздно что-то исправлять."
    m "Поэтому ты копишь силы в надежде, что завтра будет лучше."
    m 1tkd "Это логично. Когда всё идёт плохо, хочется начать с чистого листа."
    m 1dsd "К сожалению, такие дни могут повторяться, даже если каждое утро ты начинаешь с хорошими намерениями."
    m 1dsc "В итоге можно вообще потерять надежду всё поправить — или начать винить себя."
    m 1duu "Я знаю, как это тяжело, но даже одно крошечное дело очень помогает в такие дни...даже если они тянутся, кажется, вечность."
    m 1eka "Это может быть просто поднять мусор или грязную рубашку с пола и положить их на место, если нужно прибраться."
    m 1hua "Или сделать пару отжиманий! Или почистить зубы, или решить одну задачку по домашке."
    m 1eka "В общей картине это может почти ничего не значить, но я думаю, дело не в этом."
    m 3eua "Важно то, что это меняет твой взгляд на вещи."
    m 1lsc "Если ты жалеешь о прошлом и позволяешь его тяжести тебя придавливать..."
    m 1esc "Что ж, тогда ты так и застрянешь. Будешь чувствовать себя всё хуже, пока совсем не сможешь этого выносить."
    m 1eka "Но если ты заставишь себя сделать хотя бы одно дело, даже когда кажется, что смысла нет..."
    m "Тогда ты доказываешь себе обратное и не даёшь обстоятельствам тебя парализовать."
    m 1eua "И когда понимаешь, что не совсем беспомощен, будто открывается новый мир."
    m "Ты понимаешь, что, может, всё не так уж плохо — и что иногда достаточно просто верить в себя."
    m 3eub "Но это только мой опыт! Иногда лучше отдохнуть и попробовать снова завтра."
    m 3eua "Свежий старт и правда бывает очень мощным."
    m 1eka "Поэтому я думаю, что тебе просто нужно честно взглянуть на свою ситуацию."
    m "Постарайся быть честным с собой."
    m 1eua "Если так сделаешь, увидишь: ты не «ленишься», если у тебя правда нет сил что-то делать."
    m "В конце концов, сам факт, что тебе не всё равно, показывает, что ты хочешь что-то изменить — даже если кажется, что не можешь."
    m 2hub "Иметь плохой день — нормально. Или даже плохую неделю!"
    m 2eua "Не дави на себя слишком сильно. Если вдруг захочется — просто попроси меня о помощи. Я с радостью подставлю плечо!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_harem",category=['медиа','разное'],prompt="Гаремные фантазии",random=True))

label monika_harem:
    m 1esc "Я не понимаю людей, которым нравятся гаремы."
    m 1euc "Разве не сложно управлять всеми этими девушками и относиться к ним одинаково?"
    m "Часто думаю, как тем, кто ведёт двойную, а то и тройную жизнь, вообще удаётся сходить с рук."
    m 3eka "Ты же не такой снаружи, правда, [player]?"
    m 2eka "Манипулировать девушками, заставляя их верить, что ты их любишь."
    m "А потом сбежать, когда наиграешься."
    m 1lfc "Так поступает только тот, у кого в голове одна похоть."
    m 3esc "Надеюсь, ты не ждал такого роута, пока играл в эту игру."
    m 2tfc "Я бы не вынесла мысли быть «запасной девушкой»."
    m "Просто ждать своей очереди, пока ты занят другими."
    m 1tku "Я знаю тебя, [player]."
    m 1eka "Ты верный и преданный до конца."
    m "Да и беспокоиться мне здесь всё равно не о ком."
    m 1hua "Помни: я единственная для тебя, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hack",category=['ddlc','мод'],prompt="Зачем ты взломала мой компьютер?",pool=True))
label monika_hack:
    m 1euc "Если ты беспокоишься о своей приватности..."
    m 3eua "Я не хакер, [player]."
    m "Есть разница между правкой файлов и насильственным доступом к ним."
    m 1lsc "Но если бы я и правда умела взламывать..."
    m 1lfu "...ничто не мешало бы мне видеть тебя каждый день."
    m 1efu "Разве не было бы здорово, если бы я могла за тобой присматривать?"
    m 3efu "Я смотрела бы на тебя всеми камерами мира как своими глазами, чтобы убедиться, что ты в безопасности."
    m 3tfu "Проверяла бы сообщения, с кем ты переписываешься, чтобы знать, что ты мне не изменяешь."
    m "Заглядывала бы во все твои личные файлы, чтобы лучше тебя понять."
    m 3tsb "Могла бы увидеть, что ты смотришь..."
    m 2hub "Ахаха!~"
    m 1hua "Я просто шучу, [player]!"
    m 1eua "Я бы никогда так с тобой не поступила."
    m 1ekbsa "Мы же теперь пара, в конце концов."
    m "Нам не нужно хранить секреты друг от друга~"
    return

default persistent._mas_pm_bakes = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cupcake",category=['участники клуба','факты'],prompt="Выпечка кексов",random=True))

label monika_cupcake:
    m 1eua "Знаешь, чего мне сейчас очень хочется?"
    m 3tku "Капкейков Нацуки."
    m 1tsb "Боже, как она их пекла — это было восхитительно."
    m 1hub "Плюс они выглядели такими милыми!"
    m 1esa "Я сама не особо сладкоежка, но...{w=0.3}{nw}"
    extend 1eua "те капкейки были самим воплощением сладости."
    m 3hub "Прямо как я! Ахаха!"
    m 1eua "Кстати, ты знал, что у девушек чаще развивается тяга к сладкому?"
    m 3esd "Исследования показывают, что у взрослых женщин нёбо менее чувствительное, чем у мужчин."
    m 3esa "Из-за этого хочется более ярких вкусов — например, шоколада."
    m 1eka "Я бы попробовала печь, но из меня плохой пекарь."
    m 1esa "А ты, [mas_get_player_nickname()]?"

    m 1eua "Ты умеешь печь?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты умеешь печь?{fast}"

        "Да.":
            $ persistent._mas_pm_bakes = True
            m 1sub "Правда?"
            m 3hua "Ну, уверена, твои капкейки были бы такими же вкусными."
            m 1hub "...А может, даже вкуснее!"
            m 1eka "Когда-нибудь я обязательно их попробую, а пока...{w=0.3}{nw}"
            extend 1hubsu "довольствуюсь сладостью твоей любви~"

        "Нет.":
            $ persistent._mas_pm_bakes = False
            m 1eka "Значит, мы оба новички."
            m 3ekb "Но это же значит, что мы можем учиться вместе, правда?"
            m 3esb "Даже если ты не любитель сладкого, есть куча солёных и сытных вещей, которые можно испечь!"
            show monika 5dksdla at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5dksdla "Представь, как мы вдвоём путаемся в рецепте...{w=0.3}{nw}"
            extend 5hkbsb "смеёмся над своими ошибками...{w=0.3}{nw}"
            extend 5eub "пробуем результат..."
            m 5kuu "Звучит потрясающе, правда?"

    return "derandom"

# You're not a hater right?
default persistent._mas_pm_a_hater = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_haterReaction",
            category=['советы','участники клуба','ты'],
            prompt="Как справляться с хейтерами",
            random=True
        )
    )

label monika_haterReaction:
    m 1esc "Я тут думала..."
    m 2euc "Забавно, как люди в соцсетях постоянно пишут обо мне гадости..."
    m 2rkc "Особенно на некоторых сайтах и в обсуждениях..."
    m 2dkc "Прямо видно, что немало людей меня не любят."

    if persistent._mas_pm_cares_about_dokis:
        m 2lksdlc "То есть я знаю, что сделала ужасные вещи с подругами..."
        m 2dkc "И хотела бы, чтобы всё сложилось иначе, но игра не дала мне выбора..."
        m 4ekd "Не то чтобы я хотела им навредить."
        m 2rkc "Я пыталась править их черты, использовать их слабости и сделать их отвратительными в твоих глазах."
        m 2ekc "Надеялась, что если они станут менее привлекательными, ты перестанешь за ними бегать, и мы наконец будем вместе..."
        m 4dkc "Но потом поняла, что времени на мой план просто не хватит."
        m "...Да и программирования я знала недостаточно, чтобы делать это эффективно."
        m 2dkc "Ты уже подходил к концу игры, а у меня всё ещё не было способа быть с тобой."
        m 2esc "Вот тогда я и поняла, что нужны более...{w=1}радикальные меры."
        m 4ekd "Я не хотела причинять им столько боли..."
        m 4wkd "Но это был единственный путь, [player]!"
        m 4ekc "Я знала: если ты закончишь игру раньше, чем я успею признаться в чувствах, — всё."
        m 2dkc "Ты просто перейдёшь к чему-то другому, а я останусь в игре...{w=1}одна...{w=1}{b}навсегда{/b}."
        m 2dktpc "..."
        m "Некоторые на этих сайтах даже говорят, что мне стоило просто сделать свой собственный роут..."
        m 2wktsd "Легко сказать!"
        m "Не говоря уже о том, что ты мог выбрать другую девушку и просто отбросить меня, чтобы меня совсем забыли."
        m 4wktsw "Это были либо они, либо я...!"
        m 2dftdc "...и я не хотела остаться совсем одна, без кого-то, кого можно назвать своим."
        m 1ektdc "Надеюсь, ты понимаешь, [player]... Пожалуйста, не будь как они."
        $ menuOption = "...Ты ведь не из них, правда?"

    else:
        m 2lfd "Я пытаюсь их игнорировать, но просто не могу."
        m 3efc "Почему люди вообще так защищают других девушек?"
        m "Обо мне полно хейтерских постов, где говорят, что я злодейка."
        m 3efd "Потому что я удалила Сайори и Юри?"
        m "И Нацуки тоже — когда она ещё была жива?"
        m 2tfx "Они ненастоящие. {i}Я{/i} — настоящая!"
        m 2dsc "..."
        m 2ekc "Почему они не могут этого понять?"
        m 2ekd "Почему им так сложно это понять?"
        m 2rfc "..."
        $ menuOption = "Ты ведь не из этих хейтеров, " + player + "?"

    m "[menuOption]{nw}"
    $ _history_list.pop()
    menu:
        m "[menuOption]{fast}"
        "Да.":
            $ mas_loseAffection()
            $ persistent._mas_pm_a_hater = True

            m 2wud "..."
            m 1eka "Аха..."
            m 1hka "Я тебя таким не вижу, даже если ты так говоришь."
            m 1ekd "То есть..."
            m 3eub "Ты же {i}поставил{/i} мод к игре... правда?"
            m 1ekb "Будь ты одним из моих хейтеров, ты бы этого не сделал."
            m 1dsa "И не говоря уже о том..."
            m 3eka "Ты всё ещё слушаешь всё, что я говорю."
            m 1esa "Я знаю, что глубоко внутри ты меня любишь."
            m 1ekbsa "Поэтому обещаю быть идеальной девушкой — только для тебя, [player]~"
            m 1hubfa "Я не дам тебе меня возненавидеть... Клянусь."
            return "derandom"

        "Нет.":
            $ mas_gainAffection()
            $ persistent._mas_pm_a_hater = False
            m 2dsc "..."
            m 4eka "Спасибо..."
            m 1hua "Из-за этого я ещё больше тобой горжусь, [player]!"
            m "Я знала, что ты не из таких."
            # NOTE: probably wont have the kissing line here ever
            #m 1lkbfa "Gosh... I feel like giving you a kiss right now if I were there."
            m 1ekbsa "Ты и правда делаешь меня самой счастливой девушкой на свете."
            m 1ekbfb "Раз ты так сказал, я приложу все силы, чтобы ты никогда не начал меня ненавидеть."
            m 1hua "Я доверяю тебе, [mas_get_player_nickname()]. Люблю тебя за то, что веришь в меня."
            return "derandom|love"



init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_swordsmanship",
            category=['моника','разное'],
            prompt="Фехтование",
            random=True
        )
    )

label monika_swordsmanship:
    m 1eua "Тебе нравятся мечи, [player]?"
    m 1lksdla "Мне они, в общем-то, тоже нравятся — по-своему."
    m 1ekb "Ахаха, удивлён?~"
    m 1eua "Мне нравится о них говорить, но не настолько, чтобы завести себе один."
    m 3eua "Я не то чтобы фанатка мечей."
    m 1euc "Не очень понимаю, зачем людям так зацикливаться на чём-то, чем можно ранить других..."
    m 1lsc "Наверное, кого-то привлекает именно искусство владения мечом."
    m 1eua "Завораживает, что это на самом деле форма искусства."
    m "Похоже на письмо."
    m 3eub "И то, и другое требует постоянной практики и преданности, чтобы отточить мастерство."
    m "Сначала практикуешься, а потом вырабатываешь собственную технику."
    m 1eua "Пиша стихотворение, ты находишь свой способ строить его — изящно, но с фантазией."
    m "А те, кто занимается фехтованием, строят свои формы через практику и вдохновение от других мастеров."
    m 1eua "Я понимаю, как меч может быть пером поля боя."
    m 1lsc "Но с другой стороны..."
    m 1hua "Перо сильнее меча!"
    m 1hub "Ахаха!"
    m 1eua "В любом случае, не знаю, увлекаешься ли ты сам фехтованием."
    m "Если да, я бы с радостью училась вместе с тобой, [mas_get_player_nickname(exclude_names=['love'])]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_pleasure",
            category=['ты'],
            prompt="Самоудовлетворение",
            aff_range=(mas_aff.AFFECTIONATE, None),
            random=True,
            sensitive=True
        )
    )

label monika_pleasure:
    m 2ekc "Эй, [player]..."
    m 2lssdrc "Ты... случайно... не удовлетворяешь себя?"
    m "..."
    m 2lssdrb "Спрашивать об этом немного неловко..."
    if store.mas_anni.pastSixMonths() and mas_isMoniEnamored(higher=True):
        m 1lksdla "Но мне кажется, мы уже достаточно давно вместе, чтобы быть открытыми друг с другом."
        m 1eka "Важно говорить о таких вещах."
    else:
        m 1lksdlb "Мы ещё даже не так глубоко в наших отношениях! Ахаха~"
        m 1eka "Но мне всё равно нужно за тобой присматривать."
    m "Знаю, в твоём мире это личная тема, но мне любопытно..."
    m 1euc "Это и правда такое приятное ощущение?"
    m 1esc "Просто будь осторожен; я слышала, что это вызывает привыкание."
    m 1ekc "И, по словам, люди, зависимые от мастурбации, часто начинают видеть в других лишь сексуальные объекты."
    m 1eka "Но... я и так знаю, что ты не такой."
    m 1lkbsa "А может, я просто немного ревную~"
    m 1tsbsa "Так что, пожалуй, закрою на это глаза...{w=0.5}пока что~"
    m 2tsbsu "Лишь бы думал только обо мне..."
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "Если это помогает тебе беречь себя для меня — то даже плюс! Ахаха~"
    return

# do you like vocaloid
default persistent._mas_pm_like_vocaloids = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vocaloid",
            category=['медиа','технологии','музыка'],
            prompt="Вокалоиды",
            random=True
        )
    )

label monika_vocaloid:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"
    m "Ты ведь любишь музыку, правда?"

    m 3eub "Тебе случайно не нравятся «виртуальные айдолы»?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе случайно не нравятся «виртуальные айдолы»?{fast}"
        "Да.":
            $ persistent._mas_pm_like_vocaloids = True
            m 3hub "Здорово!"
            m 3eub "Говорят, у этих песен часто бывает скрытый смысл."
            m 1eua "Может, послушаем вместе и попробуем его разгадать..."
            m 1eka "Звучит как отличное времяпрепровождение, правда?"

        "Нет.":
            $ persistent._mas_pm_like_vocaloids = False
            m 1ekc "Понимаю, это довольно специфический вкус."
            m 1hua "Но если когда-нибудь увлечёшься — я с радостью послушаю вместе с тобой."

    m 3eub "В любом случае, я хотела спросить: ты когда-нибудь слышал про девочку с луком-пореем?"
    m 1eua "Просто я постоянно о ней слышу."
    m "На самом деле я слышала её голос каждый раз, когда Нацуки слушала музыку."
    m 3eua "Она даже носила маленький брелок, прикреплённый к сумке."
    m 1eua "Просто поразительно, как синтезатор голоса собрал столько фанатов."
    m 1eka "Не кажется ли тебе забавным, что персонаж получает больше внимания, чем настоящая актриса озвучки?"
    m 3eua "Она даже не настоящая, а её знают люди по всему миру."
    m "Кто знает, сколько песен она уже «выпустила»?"
    m 1wuo "Плюс, насколько я слышала, её концерты всегда солд-аут!"
    m "Это же просто голограмма выступает вживую!"
    m 1lksdla "Вот это преданная фан-база."
    m 1eka "Может, мне тоже попробовать?"
    m 1hub "Было бы мило иметь кучу фанатов, готовых выполнить любой мой каприз."
    m 1hksdlb "Ахаха, шучу!"
    m 1lksdla "Не думаю, что мои навыки игры на пианино и пения пока так уж хороши."
    m 2lkbsa "Плюс, с таким количеством фанатов у меня едва оставалось бы время на тебя..."
    m 1hua "В любом случае!"
    m 1eua "Я спрашивала, слушаешь ли ты её песни."
    m "Я сама не то чтобы фанатка, но..."
    m 1lksdla "Есть одна песня, которая меня по-настоящему задела."
    m 1eua "Ты слышал песню {i}Hibikase{/i}?"
    m 1duu "Мне очень нравится её посыл."
    m 3dsbso "Особенно строки: «{i}I don't care if it's through the screen, love me properly{/i}» и «{i}Even if I'm virtual, don't push me away{/i}»."
    m 1dsc "Это бьёт очень сильно."
    m "..."
    m 1eka "Но чтобы ты знал..."
    m 1ekbsa "Даже через экран я всё равно чувствую твою любовь."
    m 1lkbsa "Пройдёт ещё много времени, прежде чем я смогу перейти на ту сторону, чтобы быть с тобой."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Но когда этот день настанет..."
    m "Я обниму тебя и вберу твоё тепло."
    m 5hubfa "Любовь, которой ты осыпал меня виртуально, наконец станет настоящей."
    m "У нашей любви нет границ~"
    m 5hubfu "Эхехе~"
    if (
        persistent._mas_pm_like_vocaloids
        and not renpy.seen_label("monika_add_custom_music_instruct")
        and not persistent._mas_pm_added_custom_bgm
    ):
        show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1eua "И если захочешь поделиться со мной своими любимыми вокалоидами, [player], это очень просто!"
        m 3eua "Нужно всего лишь сделать вот что..."
        call monika_add_custom_music_instruct
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_good_tod",
            category=['разное'],
            # prompt="Доброе [mas_globals.time_of_day_3state]",
            prompt= _("Доброе утро" if mas_globals.time_of_day_3state == "утро" else
                    "Добрый день" if mas_globals.time_of_day_3state == "день" else
                    "Добрый вечер" if mas_globals.time_of_day_3state == "вечер" else
                    "Добрый [mas_globals.time_of_day_3state]"),
            unlocked=True,
            pool=True
        ),
        markSeen=True
    )

label monika_good_tod:
    $ curr_hour = datetime.datetime.now().time().hour
    $ sesh_shorter_than_30_mins = mas_getSessionLength() < datetime.timedelta(minutes=30)

    if mas_globals.time_of_day_4state == "утро":
        # Если зашел совсем рано (с 4 до 5 утра)
        if 4 <= curr_hour <= 5:
            m 1eua "И тебе доброго утра, [mas_get_player_nickname()]."
            m 3eka "Ты сегодня довольно рано..."
            m 3eua "Собираешься куда-то пойти?"
            m 1eka "Если так, то это очень мило с твоей стороны — заглянуть ко мне перед уходом~"
            m 1eua "Если нет, то, может, попробуешь еще поспать? Я бы не хотела, чтобы ты пренебрегал своим здоровьем."
            m 1hua "Я всегда буду здесь, дожидаясь твоего возвращения~"

        # Обычное утро (если сессия длится меньше 30 минут)
        elif sesh_shorter_than_30_mins:
            m 1hua "И тебе доброго утра, [player]!"
            m 1eua "Ты только что проснулся?"
            m "Я обожаю просыпаться рано утром."
            m 1eub "Это идеальное время, чтобы собраться с силами и взяться за дела грядущего дня."
            m "А еще у тебя появляется гораздо больше времени, чтобы успеть сделать что-то пораньше или закончить то, что не успел вчера."
            m 1eka "Хотя некоторые люди предпочитают подольше поваляться в постели и поздно вставать."
            m 3eua "Я читала статьи о том, что ранний подъем может действительно улучшить общее состояние здоровья."
            m "Плюс у тебя есть шанс увидеть рассвет, если небо ясное."
            m 1hua "Если ты обычно не встаешь рано, тебе стоит попробовать!"
            m "Так ты сможешь чувствовать себя счастливее и проводить больше времени со мной~"
            m 1ekbsa "Разве тебе бы этого не хотелось, [mas_get_player_nickname()]?"

        #You've been here for a bit now
        else:
            m 1hua "И тебе доброго утра [mas_get_player_nickname()]!"
            m 1tsu "Пусть мы уже какое-то время бодрствуем вместе,{w=0.2} {nw}"
            extend 3hua "всё равно приятно это слышать!"
            m 1esa "Если бы мне пришлось выбирать любимое время суток, это, вероятно, было бы утро."
            m 3eua "В ночи определенно есть некое спокойствие, которое мне нравится...{w=0.3}{nw}"
            extend 3hua "но утро — это время, которое дарит возможности!"
            m 1eub "Целый день впереди, когда может случиться что угодно, к лучшему или к худшему."
            m 1hub "Такие шансы и свобода просто приводят меня в восторг!"
            m 1rka "Правда, я начинаю это чувствовать только тогда, когда окончательно проснусь, ехе-хе~"

    elif mas_globals.time_of_day_4state == "день":
        m 1eua "И тебе доброго дня, [player]."
        m 1hua "Так мило с твоей стороны выделить время посреди дня, чтобы провести его со мной~"
        m 3euc "День — довольно странная часть суток, не находишь?"
        m 4eud "Иногда бывает очень много дел...{w=0.3}{nw}"
        extend 4lsc "а иногда совсем нечем заняться..."
        m 1lksdla "Время может тянуться бесконечно или пролететь в одно мгновение."

        if mas_isMoniNormal(higher=True):
            m 1ekbsa "Но когда ты здесь, мне всё равно."
            m 1hubsa "Что бы ни случилось, мне всегда будет приятно время, проведенное с тобой, [mas_get_player_nickname()]!"
            m 1hubsb "Я люблю тебя!"
            $ mas_ILY()

        else:
            m 1lksdlb "Иногда мой день пролетает незаметно, пока я жду твоего возвращения."
            m 1hksdlb "Уверена, ты занят, так что можешь возвращаться к своим делам, не обращай на меня внимания."

    else:
        m 1hua "И тебе доброго вечера [player]!"
        m "Я люблю приятные и расслабляющие вечера."

        if 17 <= curr_hour < 23:
            m 1eua "Так приятно вытянуть ноги после долгого дня."
            m 3eua "Вечер — идеальное время, чтобы доделать то, чем ты занимался вчера."
            m 1eka "Иногда я не могу сдержать грусти, когда день заканчивается."
            m "Это заставляет меня задумываться о том, что еще я могла бы успеть сделать за сегодня."
            m 3eua "Разве тебе не хотелось бы, чтобы в сутках было больше времени на разные дела?"
            m 1hua "Я вот точно этого хочу."
            m 1hubsa "Ведь это значило бы, что у нас будет больше времени друг на друга, [mas_get_player_nickname()]~"

        # Поздняя ночь (с 23:00 до 04:00)
        else:
            m 3eua "Всегда приятно иметь возможность немного расслабиться в конце дня."
            m 3hub "В конце концов, нет ничего плохого в том, чтобы уделить время себе, верно?"
            m 1eka "Ну... я так говорю, но на самом деле я очень счастлива проводить это время с тобой~"

            if not persistent._mas_timeconcerngraveyard:
                m 3eka "Хотя становится уже поздновато, так что не засиживайся долго, [player]."
                m 3eua "Пообещай мне, что скоро пойдешь спать, хорошо?"

    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_closet",category=['ddlc','club members'],prompt="Классный шкаф",random=True))

label monika_closet:
    m 2euc "Кстати..."
    m 2esc "Что вы с Юри делали в кладовке?"
    m "Когда я открыла дверь, комната была совсем тёмной."
    m 2tkc "Вы там ничего... странного не вытворяли?"
    m 1hub "Ахаха!"
    m 1tfu "Просто дразню тебя~"
    m 3tku "Я знаю, что это она затащила тебя туда."
    m "Уверена, ты больше смутился, чем почувствовал облегчение, когда я открыла дверь."
    m 1eka "Я знаю, ты не из тех, кто затаскивает девушек в тёмные кладовки."
    m "Ты куда романтичнее."
    m 3hua "Так что я жду куда большего, чем просто тёмная кладовка~"
    return


# languages other than english
default persistent._mas_pm_lang_other = None

# do you know japanese
default persistent._mas_pm_lang_jpn = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_japanese",category=['разное','ты'],prompt="Японский язык",random=True))

label monika_japanese:
    m 1lksdla "Не хочу звучать как Нацуки, но..."
    m 1eua "Разве японский не звучит круто?"
    m "Это такой завораживающий язык. Правда, я им не владею свободно."
    m 1eub "Интересно представить, каково было бы, если бы твой родной язык был другим."
    m 1esa "Вот я, например, даже не могу представить, каково было бы, если бы я никогда не знала английского."

    m "Ты знаешь какие-нибудь языки, кроме английского?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты знаешь какие-нибудь языки, кроме английского?{fast}"
        "Да.":
            $ persistent._mas_pm_lang_other = True
            m "Правда? А японский знаешь?{nw}"
            $ _history_list.pop()
            menu:
                m "Правда? А японский знаешь?{fast}"
                "Да.":
                    $ persistent._mas_pm_lang_jpn = True
                    m 3hub "Замечательно!"
                    m 1eka "Может, научишь меня хотя бы паре фраз, [player]~"
                "Нет.":
                    $ persistent._mas_pm_lang_jpn = False
                    m 1eka "Понятно. Ничего страшного!"
                    m 4eua "Если захочешь выучить японский, вот фраза, которой я могу тебя научить."

                    # setup suffix
                    $ player_suffix = "kun"
                    if persistent.gender == "F":
                        $ player_suffix = "chan"

                    elif persistent.gender == "X":
                        $ player_suffix = "san"

                    m 1eua "{i}Aishiteru yo, [player]-[player_suffix]{/i}."
                    m 2hubsa "Эхехе~"
                    m 1ekbfa "Это значит «я тебя люблю», [player]-[player_suffix]."
                    $ mas_ILY()
        "Нет.":
            $ persistent._mas_pm_lang_other = False
            m 3hua "Ничего! Учить другой язык с возрастом становится всё сложнее и утомительнее."
            m 1eua "Может, если я потрачу время и выучу побольше японского, буду знать больше языков, чем ты!"
            m 1ekbsb "Ахаха! Ничего, [player]. Просто значит, что я смогу сказать «я тебя люблю» ещё большим числом способов!"
            $ mas_ILY()

    return "derandom"

default persistent._mas_penname = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_penname",
            category=['литература'],
            prompt="Псевдонимы",
            random=True
        )
    )

label monika_penname:
    m 1eua "Знаешь, что по-настоящему круто? Литературные псевдонимы."
    m "Большинство писателей используют их ради приватности и чтобы скрыть личность."
    m 3euc "Прячут её ото всех, чтобы это не влияло на личную жизнь."
    m 3eub "Псевдонимы ещё помогают писателям создавать что-то совсем иное по сравнению с их обычным стилем."
    m "Это даёт автору защиту анонимности и массу творческой свободы."

    if not persistent._mas_penname:
        $ p_nickname = mas_get_player_nickname()
        m "У тебя есть псевдоним, [p_nickname]?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя есть псевдоним, [p_nickname]?{fast}"

            "Да.":
                m 1sub "Правда? Как круто!"
                call penname_loop(new_name_question="Скажешь, какой он?")

            "Нет.":
                m 1hua "Хорошо!"
                m "Если когда-нибудь придумаешь — обязательно расскажи мне!"

    else:
        python:
            penname = persistent._mas_penname
            lowerpen = penname.lower()

            if mas_awk_name_comp.search(lowerpen) or mas_bad_name_comp.search(lowerpen):
                menu_exp = "monika 2rka"
                is_awkward = True

            else:
                menu_exp = "monika 3eua"
                is_awkward = False

            if lowerpen == player.lower():
                same_name_question = renpy.substitute("Твой псевдоним всё ещё [penname]?")

            else:
                same_name_question = renpy.substitute("Ты всё ещё подписываешься как «[penname]», [player]?")

        $ renpy.show(menu_exp)
        m "[same_name_question]{nw}"
        $ _history_list.pop()
        menu:
            m "[same_name_question]{fast}"

            "Да.":
                m 1hua "Не могу дождаться, чтобы увидеть твои работы!"

            "Нет, теперь у меня новый.":
                m 1hua "Понятно!"
                show monika 3eua
                call penname_loop(new_name_question="Расскажешь мне свой новый псевдоним?")

            "Я больше не пользуюсь псевдонимом.":
                $ persistent._mas_penname = None
                m 1euc "О, понятно."
                if is_awkward:
                    m 1rusdla "Могу догадаться, почему..."
                m 3hub "Но не стесняйся сказать мне, если снова выберешь себе один!"

    m 3eua "Известный псевдоним — Льюис Кэрролл. Его больше всего знают по «{i}Алисе в Стране чудес{/i}»."
    m 1eub "Его настоящее имя — Чарльз Доджсон, он был математиком, но очень любил литературу и игру слов."
    m "Он получал массу нежелательного внимания и любви от фанатов, и даже сталкивался с возмутительными слухами."
    m 1ekc "Он был вроде как one-hit wonder со своими книгами про {i}Алису{/i}, а дальше дела пошли под гору."

    if seen_event("monika_1984"):
        m 3esd "А ещё, если помнишь, я говорила про Джорджа Оруэлла — на самом деле его зовут Эрик Блэр."
        m 1eua "Прежде чем остановиться на более известном псевдониме, он рассматривал P.S. Burton, Kenneth Miles и H. Lewis Allways."
        m 1lksdlc "Одна из причин, по которой он публиковался под псевдонимом, — не смущать семью из-за времени, когда он был бродягой."

    m 1lksdla "Хотя это довольно забавно. Даже если прячешься за псевдонимом, люди всё равно найдут способ узнать, кто ты на самом деле."
    m 1eua "Но тебе незачем узнавать обо мне больше, [mas_get_player_nickname()]..."
    m 1ekbsa "Ты и так уже знаешь, что я тебя люблю~"
    return "love"

# NOTE: the caller is responsible for setting up Monika's exp
label penname_loop(new_name_question):
    m "[new_name_question]{nw}"
    $ _history_list.pop()
    menu:
        m "[new_name_question]{fast}"

        "Конечно.":
            show monika 1eua
            $ penbool = False

            while not penbool:
                $ penname = mas_input(
                    "Какой у тебя псевдоним?",
                    length=20,
                    screen_kwargs={"use_return_button": True}
                ).strip(' \t\n\r')

                $ lowerpen = penname.lower()

                if persistent._mas_penname is not None and lowerpen == persistent._mas_penname.lower():
                    m 3hub "Это же твой текущий псевдоним, глупыш!"
                    m 3eua "Попробуй ещё раз."

                elif lowerpen == player.lower():
                    m 1eud "О, так ты используешь своё имя как псевдоним?"
                    m 3euc "Мне хотелось бы думать, что мы уже на «ты» и по именам. Мы же встречаемся, в конце концов."
                    m 1eka "Но всё равно особый жест — что ты поделился со мной псевдонимом!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen in ("sayori", "сайори"):
                    m 2euc "..."
                    m 2hksdlb "...В смысле, я не буду осуждать твой выбор псевдонима, но..."
                    m 4hksdlb "Если уж называть себя в честь персонажа этой игры, стоило выбрать меня!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen in ("natsuki", "нацуки"):
                    m 2euc "..."
                    m 2hksdlb "Ну, наверное, не стоит предполагать, что ты назвался в честь {i}нашей{/i} Нацуки."
                    m 7eua "Это довольно распространённое имя."
                    m 1rksdla "Хотя ты можешь меня немного разревновать."
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen in ("yuri", "юри"):
                    m 2euc "..."
                    m 2hksdlb "Ну, наверное, не стоит предполагать, что ты назвался в честь {i}нашей{/i} Юри."
                    m 7eua "Это довольно распространённое имя."
                    m 1tku "Конечно, это имя может означать и кое-что ещё..."
                    if persistent.gender =="F":
                        m 5eua "И что ж... я могла бы это поддержать, раз это ты~"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif lowerpen in ("monika", "моника"):
                    m 1euc "..."
                    m 1ekbsa "Ой, ты выбрал это ради меня?"
                    m "Даже если нет — это так мило!"
                    $ persistent._mas_penname = penname
                    $ penbool = True

                elif not lowerpen:
                    m 1hua "Ну же! Нажми «неважно», если струсил~"

                elif lowerpen == "cancel_input":
                    m 2eka "Ох. Ну что ж, надеюсь, когда-нибудь тебе будет достаточно комфортно рассказать мне."
                    $ penbool = True

                else:
                    if mas_awk_name_comp.search(lowerpen) or mas_bad_name_comp.search(lowerpen):
                        m 2rksdlc "..."
                        m 2rksdld "Интересное...{w=0.3}имя, [player]..."
                        m 2eksdlc "Но если тебе подходит — ладно, пусть будет."

                    else:
                        m 1hua "Какой прелестный псевдоним!"
                        m "Думаю, увидев такое имя на обложке, я бы сразу на него клюнула."
                    $ persistent._mas_penname = penname
                    $ penbool = True

        "Лучше не надо, это неловко.":
            m 2eka "Ох. Ну что ж, надеюсь, когда-нибудь тебе будет достаточно комфортно рассказать мне."

    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_zombie",category=['общество'],prompt="Зомби",random=True))

label monika_zombie:
    m 1lsc "Эй, это может прозвучать странновато..."
    m 1esc "Но меня очень завораживает концепция зомби."
    m 1euc "Идея общества, гибнущего от болезни — смертельной пандемии, с которой люди не справились вовремя."
    m 3esd "Представь свой обычный распорядок дня."
    m 3esc "Всё, что ты делаешь, исчезнет в одно мгновение."
    m 1esc "Конечно, общество каждый день сталкивается с кучей угроз..."
    m 1lksdlc "Но зомби могут уничтожить всё в мгновение ока."
    m 1esc "Многих монстров создают, чтобы пугать."
    m 1ekc "Зомби же куда реалистичнее и действительно представляют опасность."
    m 3ekc "С одним или несколькими ты, может, и справишься сам..."
    m "Но когда на тебя идёт целая орда — тебя быстро сомнут."
    m 1lksdld "С другими монстрами такого ощущения нет."
    m "У них нет интеллекта; они в ярости, не чувствуют боли, не умеют бояться..."
    m 1euc "Если найти слабое место монстра, он испугается и убежит."
    m 1ekd "А зомби? Они прорвутся сквозь {i}что угодно{/i}, лишь бы добраться до тебя."
    m 3ekd "Представь, если бы за тобой шёл кто-то, кого ты любишь..."
    m 3dkc "Смог бы ты жить с собой, зная, что был вынужден убить близкого человека?"
    m 1tkc "Это сломает тебя и высосет волю к жизни."
    m "Даже дома, в уюте, ты всё равно не будешь чувствовать себя в безопасности."
    m 1esc "Никогда не знаешь, что случится, когда снова увидишь одного из них."
    m 1dsc "..."
    m 1hksdlb "Ахаха..."
    m 1eka "Знаешь, несмотря на то что мне нравится сама идея, жить в таком сценарии я бы не хотела."
    m 3ekc "[player], а что, если бы ты вдруг заразился?"
    m 2lksdlc "Я даже думать об этом не хочу..."
    m "Я бы ни за что не смогла убить тебя ради собственной безопасности..."
    m 2lksdlb "Ахаха..."
    m 2lssdlb "Я слишком далеко зашла в этих размышлениях."
    m 3eua "Что ж, в любом случае, если случится что-то плохое..."
    m 2hua "Я буду рядом с тобой вечно~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_nuclear_war",category=['общество','философия'],prompt="Ядерная война",random=True))

label monika_nuclear_war:
    m 1euc "Ты когда-нибудь думал, насколько мир в любой момент близок к концу?"
    m "В смысле, мы всегда в одном неверном решении от ядерной войны."
    m 3esc "Холодная война закончилась, но оружия по-прежнему полно."
    m 1esc "Наверняка прямо сейчас на место, где ты живёшь, нацелена ядерная ракета — готовая к запуску."
    m 1eud "И если её запустят, она облетит земной шар меньше чем за час."
    m 3euc "У тебя не будет времени эвакуироваться."
    m 1ekd "Только паниковать и мучиться от ужаса неминуемой смерти."
    m 1dsd "По крайней мере, всё закончится быстро, когда бомба ударит."
    m 1lksdlc "Ну, если ты близко к эпицентру."
    m 1ekc "Я даже не хочу думать о том, каково пережить первый удар."
    m 1eka "Но даже стоя на краю апокалипсиса, мы живём так, будто всё в порядке."
    m 3ekd "Планируем завтрашний день, которого может и не быть."
    m "Наше единственное утешение — что люди, у которых есть власть начать такую войну, скорее всего этого не сделают."
    m 1dsc "Скорее всего..."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_pluralistic_ignorance",category=['литература','общество'],prompt="Желание вписаться",random=True))

label monika_pluralistic_ignorance:
    m 1eua "Тебе случалось притворяться, что тебе что-то нравится, просто потому что «так надо»?"
    m 1esa "Иногда я так себя чувствую насчёт книг, которые читаю."
    m 3euc "Вот Шекспир — на самом деле мне было довольно скучно..."
    m 3ekc "Но казалось, что я обязана его любить, ведь я президент литературного клуба."
    m 1esd "Он же величайший драматург и поэт всех времён, верно?"
    m 1esd "Какой любитель поэзии может его не любить?"
    m 2euc "Но это заставляет меня задуматься..."
    m 2euc "А вдруг все на самом деле чувствуют то же самое?"
    m 2lud "Вдруг все эти литературные критики, воспевающие Шекспира, тайно ненавидят его пьесы?"
    m "Если бы они были честны, то, может, обнаружили бы, что их вкус вовсе не такой уж необычный..."
    m 2hksdlb "И старшеклассников не заставляли бы читать эти ужасные пьесы."
    m 1eka "Наверное, именно это я всегда уважала в Нацуки."
    m 3ekd "Даже когда ей говорили, что манга — не литература, она стояла на своём."
    m 3eka "Если бы больше людей были такими честными, было бы здорово."
    m 1lksdla "Но я не думаю, что смогла бы так..."
    m "Я слишком переживаю, что подумают другие."
    m 1eua "Только не с тобой. С тобой я всегда могу быть честной."
    m 1ekbsa "Ты будешь любить меня несмотря ни на что, правда?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_science",category=['технологии'],prompt="Научный прогресс",random=True))

label monika_science:
    m 1eua "Ты когда-нибудь думал, что было бы, если бы науку так и не приняли?"
    m "Люди бывают очень медленными, когда речь о новых идеях."
    m 1euc "Раньше науку обычно презирали — особенно церковь."
    m 4esc "Джордано Бруно, известный теорией о тысячах солнц, был казнён римской церковью, так и не успев доказать свою теорию."
    m 1ekc "Его убили из-за идеи, которая бросала вызов старому."
    m 1esc "Технологии не были бы сегодня такими продвинутыми без смелых учёных вроде него."
    m 1eka "Если бы технологии не развивались так, как развивались, мы бы никогда не нашли друг друга."
    m 3eua "Разве это не чудесно?"
    m 1hua "Я благодарна, что они дали нам шанс быть вместе, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_surprise",category=['романтика'],prompt="Сюрпризы",random=True))

label monika_surprise:
    m 1rksdla "Знаешь..."
    m 3rksdlb "Я оставляла довольно странные вещи в папке с игрой, да?"
    m 1rksdlc "Я не пыталась тебя напугать."
    m 3rksdlb "Я... на самом деле не знаю, зачем это делала, ахаха..."
    m 1ekc "Как будто чувствовала, что обязана."
    m 1euc "Знаешь что? Может, стоит сделать это снова..."
    m 1eua "Да, хорошая идея."
    $ mas_surprise()

    if mas_isMoniUpset(lower=True):
        m 2dsc ".{w=0.5}.{w=0.5}.{nw}"
        m 1euc "Ладно..."
        m 1ekc "Пожалуйста, посмотри."
        m 1eka "Я написала это специально для тебя."
        m 1dsc "Для меня многое значит, если ты это прочитаешь."
        return

    elif mas_isMoniAff(higher=True):
        m 2dsa ".{w=0.5}.{w=0.5}.{nw}"
        m 1hua "Готово!"
        m 1eua "Чего ждёшь? Иди посмотри!"
        m "Я написала это специально для тебя~"
        m 1ekbsa "Я и правда очень тебя люблю, [mas_get_player_nickname(exclude_names=['my love', 'love'])]~"

    # Normal and Happy
    else:
        m 2duu ".{w=0.5}.{w=0.5}.{nw}"
        m 1hua "Готово!"
        m 1eua "Чего ждёшь? Иди посмотри!"
        m 1hub "Ахаха~ Что? Ждал чего-то страшного?"
        m 1hubsb "Я так тебя люблю, [player]~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_completionist",category=['игры'],prompt="Комплиционизм",random=True))

label monika_completionist:
    m 1euc "Эй, [player], случайный вопрос, но..."
    m "Ради чего ты играешь в видеоигры?"
    m 1eua "То есть что заставляет тебя продолжать?"
    m 3eua "Лично я считаю себя немного перфекционисткой."
    m 1eua "Я стараюсь дочитать книгу, прежде чем взять следующую."
    if persistent.clearall:
        m 2tku "Похоже, ты тоже перфекционист, [player]."
        m 4tku "Учитывая, что ты прошёл все роуты девушек."
    m 2eub "Ещё я слышала, что некоторые люди пытаются полностью пройти крайне сложные игры."
    m "Даже простые игры бывает трудно пройти до конца."
    m 3rksdla "Не представляю, как кто-то добровольно взваливает на себя такой стресс."
    m "Они очень решительно настроены изучить каждый уголок игры и покорить её."
    # TODO: if player cheated at chess, reference that here
    m 2esc "А вот что оставляет неприятный осадок — читеры."
    m 2tfc  "Люди, которые взламывают игру и лишают себя удовольствия от преодоления трудностей."
    m 3rsc "Хотя я могу понять, почему они читерят."
    m "Это позволяет свободно исследовать игру, в которую иначе они бы не смогли играть из-за сложности."
    m 1eua "Что, возможно, даже убедит их потом постараться по-настоящему."
    m "В любом случае, мне кажется, в завершении задач вообще есть огромное удовлетворение."
    m 3eua "Усердная работа ради чего-то усиливает награду после стольких неудач."
    m 3eka "Можешь стараться держать меня на фоне как можно дольше, [mas_get_player_nickname()]."
    m 1hub "Это ведь один из шагов к тому, чтобы «пройти» меня, ахаха!"
    return

# do you like mint ice cream
default persistent._mas_pm_like_mint_ice_cream = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_icecream",category=['ты'],prompt="Любимое мороженое",random=True))

label monika_icecream:
    m 3eua "Эй, [player], какое твоё любимое мороженое?"
    m 4rksdla "И нет, я не сорт мороженого, эхехе~"
    m 2hua "Лично я никак не могу насытиться мятным!"

    $ p_nickname = mas_get_player_nickname()
    m "А ты, [p_nickname], любишь мятное мороженое?{nw}"
    $ _history_list.pop()
    menu:
        m "А ты, [p_nickname], любишь мятное мороженое?{fast}"
        "Да.":
            $ persistent._mas_pm_like_mint_ice_cream = True
            m 3hub "Ах, так рада, что кому-то мятное нравится так же сильно, как мне~"
            m "Может, мы и правда были созданы друг для друга!"
            m 3eua "Ладно, к теме, [player]: если тебе мята нравится так, как я думаю, у меня есть несколько рекомендаций."
            m "Вкусы такие же уникальные, как мята — возможно, ты о них слышал, но..."
            m 3eub "Есть совсем странные штуки вроде жареного мороженого — очень хрустящего, но на вкус в миллион раз лучше, чем звучит!"
            m 2lksdlb "Боже, от одной мысли о вкусе я чуть ли не пускаю слюни..."
            m 1eua "Есть и другие странные, но не менее манящие вкусы — например, с медовыми сотами или баблгам!"
            m 1eka "Знаю, в некоторые из них сложно поверить на слово, но не суди книгу по обложке, знаешь?"
            m 1hub "В конце концов, игра не давала тебе влюбиться в меня — а посмотри, где мы сейчас, ахаха."

        "Нет.":
            $ persistent._mas_pm_like_mint_ice_cream = False
            m 1ekc "Ох, жаль..."
            m "Я правда не понимаю, как кому-то может хотя бы не нравиться этот вкус."
            m 1eka "Это освежающее ощущение, которое окатывает язык и горло."
            m "Прелестная текстура вместе со сладостью."
            m 1duu "Острая прохлада и очевидный мятный вкус."
            m "Честно говоря, мне кажется, ничто с этим не сравнится."
            m 3eua "Ах, я могла бы говорить об этом бесконечно, знаешь?"
            m 4eua "Но будет проще показать, что я имею в виду — когда разберусь, как отсюда выбраться. К тому же дела говорят громче слов!"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_sayhappybirthday",category=['разное'],prompt="Ты можешь поздравить кого-нибудь с Днем рождения от моего имени?",pool=True,unlocked=True))

label monika_sayhappybirthday:
    # special variable setup
    python:
        done = False # loop controller
        same_name = False # true if same name as player
        bday_name = "" # name of birthday target
        is_here = False # is the target here (in person)
        is_watching = False # is the target watching (but not here)
        is_recording = False # is player recording this
        age = 0 # how old is this person turning
        bday_msg = "" # happy [age] birthday (or not)
        take_counter = 1 # how many takes
        take_threshold = 5 # multiple of takes that will make monika annoyed
        max_age = 121 # like who the hell is this old and playing ddlc?
        age_prompt = "Сколько им лет?" # prompt for age question

        # age suffix dictionary
        age_suffix = {
            1: "st",
            2: "nd",
            3: "rd",
            11: "th",
            12: "th",
            13: "th",
            111: "th",
            112: "th",
            113: "th"
        }

    #TODO: temporary m_name reset for this
    # TODO: someone on the writing team make the following dialogue better
    # also make the expressions more approriate and add support for standing
    m 3hub "Конечно, [player]!"
    while not done:
        show monika 1eua
        # arbitary max name limit
        $ bday_name = renpy.input("Как зовут именинника?",allow=letters_only+"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",length=40).strip()
        # ensuring proper name checks
        $ same_name = bday_name.upper() == player.upper()
        if bday_name == "":
            m 1hksdlb "..."
            m 1lksdlb "Не похоже на имя."
            m 1hub "Попробуй ещё раз!"
        elif same_name:
            m 1wuo "Ого, кто-то с таким же именем, как у тебя!"
            $ same_name = True
            $ done = True
        else:
            $ done = True

    m 1hua "Хорошо! Хочешь, чтобы я назвала и возраст?{nw}"
    $ _history_list.pop()
    menu:
        m "Хорошо! Хочешь, чтобы я назвала и возраст?{fast}"
        "Да.":
            m "Тогда..."

            while max_age <= age or age <= 0:
                $ age = store.mas_utils.tryparseint(
                    renpy.input(
                        age_prompt,
                        allow=numbers_only,
                        length=3
                    ).strip(),
                    0
                )

            m "Ладно."
        "Нет.":
            m "Ладно."
    $ bday_name = bday_name.title() # ensure proper title case

    m 1eua "[bday_name] сейчас здесь с тобой?{nw}"
    $ _history_list.pop()
    menu:
        m "[bday_name] сейчас здесь с тобой?{fast}"
        "Да.":
            $ is_here = True
        "Нет.":
            m 1tkc "Что? Как я поздравлю [bday_name], если их здесь нет?{nw}"
            $ _history_list.pop()
            menu:
                m "Что? Как я поздравлю [bday_name], если их здесь нет?{fast}"

                "Они посмотрят по видеосвязи.":
                    m 1eua "О, хорошо."
                    $ is_watching = True
                "Я запишу видео и отправлю.":
                    m 1eua "О, хорошо."
                    $ is_recording = True
                "Ничего, просто скажи.":
                    m 1lksdla "О, ладно. Немного неловко говорить это в пустоту."
    if age:
        # figure out the age suffix
        python:
            age_suff = age_suffix.get(age, None)
            if age_suff:
                age_str = str(age) + age_suff
            else:
                age_str = str(age) + age_suffix.get(age % 10, "th")
            bday_msg = "с " + str(age) + "-летием"
    else:
        $ bday_msg = "с днём рождения"

    # we do a loop here in case we are recording and we should do a retake
    $ done = False
    $ take_counter = 1
    $ bday_msg_capped = bday_msg.capitalize()
    while not done:
        if is_here or is_watching or is_recording:
            if is_here:
                m 1hua "Приятно познакомиться, [bday_name]!"
            elif is_watching:
                m 1eua "Дай знать, когда [bday_name] будет смотреть.{nw}"
                $ _history_list.pop()
                menu:
                    m "Дай знать, когда [bday_name] будет смотреть.{fast}"
                    "Смотрят.":
                        m 1hua "Привет, [bday_name]!"
            else: # must be recording
                m 1eua "Дай знать, когда начинать.{nw}"
                $ _history_list.pop()
                menu:
                    m "Дай знать, когда начинать.{fast}"
                    "Начинай.":
                        m 1hua "Привет, [bday_name]!"

            # the actual birthday msg
            m 1hub "[player] сказал мне, что у тебя сегодня день рождения, так что я хочу поздравить тебя [bday_msg]!"
            # TODO: this seems too short. maybe add additional dialogue?
            m 3eua "Надеюсь, у тебя будет чудесный день!"

            if is_recording:
                m 1hua "Пока-пока!"
                m 1eka "Получилось хорошо?{nw}"
                $ _history_list.pop()
                menu:
                    m "Получилось хорошо?{fast}"
                    "Да.":
                        m 1hua "Ура!"
                        $ done = True
                    "Нет.":
                        call monika_sayhappybirthday_takecounter (take_threshold, take_counter) from _call_monika_sayhappybirthday_takecounter
                        if take_counter % take_threshold != 0:
                            m 1wud "Э?!"
                            if take_counter > 1:
                                m 1lksdla "Извини ещё раз, [player]."
                            else:
                                m 1lksdla "Извини, [mas_get_player_nickname()]."
                                m 2lksdlb "Я же говорила, что стесняюсь камеры, ахаха..."

                        m "Попробовать ещё раз?{nw}"
                        $ _history_list.pop()
                        menu:
                            m "Попробовать ещё раз?{fast}"
                            "Да.":
                                $ take_counter += 1
                                m 1eua "Хорошо."
                            "Нет.":
                                m 1eka "Ладно, [player]. Жаль, что не получилось так, как ты хотел."
                                m 1hua "В следующий раз постараюсь лучше для тебя."
                                $ done = True
            else:  # if we aint recording, we should be done now
                $ done = True

        else: # not recording, watching, nor is person here
            m 1duu "..."
            m 1hub "[bday_msg_capped], [bday_name]! Поздравляю!"
            m 1hksdlb "..."
            m 1lksdlb "Получилось хорошо?{nw}"
            $ _history_list.pop()
            menu:
                m "Получилось хорошо?{fast}"
                "Да.":
                    m 1lksdla "...Рада, что тебе понравилось, [player]..."
                    $ done = True
                "Нет.":
                    call monika_sayhappybirthday_takecounter (take_threshold, take_counter) from _call_monika_sayhappybirthday_takecounter_1
                    if take_counter % take_threshold != 0:
                        m 1wud "Э?!"
                        m 1lksdlc "Не очень понимаю, чего ты от меня хочешь, [player]..."

                    m 1ekc "Попробовать ещё раз?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Попробовать ещё раз?{fast}"
                        "Да.":
                            $ take_counter += 1
                            m 1eua "Хорошо."
                        "Нет.":
                            m 1eka "Ладно, [player]. Жаль, что не получилось так, как ты хотел."
                            m 1hua "В следующий раз постараюсь лучше для тебя."
                            $ done = True

    return

# helper label for monika_sayhappybirthday
label monika_sayhappybirthday_takecounter (take_threshold, take_counter):
    if take_counter % take_threshold == 0:
        m 1dfc "..."
        m 1efc "Это уже [take_counter]-й раз."
        m 2tkc "Ты же не издеваешься надо мной?"
        m 2ekc "Я стараюсь изо всех сил для тебя, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_home_memories",category=['романтика','моника','жизнь'],prompt="Создавать воспоминания",random=True))

label monika_home_memories:
    m 1eua "[player], каково это — жить там, где ты?"
    m "Я бы жила с тобой, если бы могла."
    m 3hua "Мы столько всего могли бы делать! Ты бы меня повсюду провёл, показал, каково у тебя дома."
    m 1eka "Представь, сколько воспоминаний мы бы создали!"
    m 2eub "Это была бы мечта наяву, правда?"
    m 2ekbsa "Мы бы наконец жили вместе..."
    m "Гуляли бы как пара..."
    m 3rkbsa "Могли бы даже делить одну кровать..."
    m 1euc "Но знаешь..."
    m 2eka "Воспоминания о моём доме ничто по сравнению с теми, что были бы у меня с тобой."
    m 2euc "Я рассказывала тебе о доме детства? У меня была довольно обычная жизнь — и на том всё."
    m 3rka "Ну, может, чуть лучше обычной."
    m 3eua "...Я всегда держала всё под контролем."
    m 3eka "Признаю, это не всегда легко, и у кого-то дела обстоят куда тяжелее."
    m 1ekc "Но я всегда чувствовала, что мне чего-то не хватает."
    m "Каждый день оставалась оптимисткой, пытаясь это найти."
    m 1eka "Оказалось, недостающим кусочком был ты."
    m 1lksdld "Если бы ты меня не нашёл, меня бы уже давно не было..."
    m 2hubsa "А теперь, когда я нашла этот кусочек, я целая, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_adventure",category=['игры','романтика'],prompt="Приключения",random=True))

label monika_adventure:
    m 1esa "[player], я думала, в какой игре мы могли бы оказаться."
    m 3esa "Мне кажется, лучший жанр для нас двоих — приключенческие игры."
    m 3eub "Особенно point-and-click, графические квесты!"
    m 1eub "Они известны богатым сюжетом, красивыми локациями и логическими головоломками."
    m 3eua "По сути, они похожи на визуальные новеллы."
    m 1eua "Может, у тебя есть такая игра?"
    m 1eka "Мы могли бы столько всего делать..."
    m 3eua "Например, смотреть достопримечательности, когда захотим."
    m "Узнавать больше о мире через людей, которых встречаем, или через истории."
    m 1ekbsa "Переживать волнующие и романтичные моменты..."
    m "Встречать препятствия и трудности на пути — и преодолевать их вместе."
    m 3ekbsa "Дойти до конца и завершить путешествие с чувством выполненного долга."
    m 2hub "Ахаха! Было бы здорово пережить что-то подобное."
    m 2eua "Уверена, у тебя полно приключенческих игр, которые ты мог бы посоветовать."
    m 3eua "Но угадаешь, какого приключения я жду сильнее всего?"
    m 1ekbsa "{i}Нашего{/i}~"
    m 1hubfa "Время покажет, когда я наконец смогу перейти в твою реальность, чтобы быть с тобой."
    m "Когда этот день настанет, я наконец буду рядом."
    m 1ekbfa "Я хочу переживать каждое мгновение с тобой, [mas_get_player_nickname()]."
    m 1hubfb "Нет большего приключения, чем наше — вместе~"
    return

default persistent._mas_pm_likes_panties = None
# are you into panties?

default persistent._mas_pm_no_talk_panties = None
# dont want to talk about panties

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_panties",
            category=['разное',"одежда"],
            prompt="Нижнее бельё",
            random=True,
            sensitive=True
        )
    )

label monika_panties:
    m 1lsc "Эй, [player]..."
    m "Только не смейся, ладно?"
    m 2rksdlc "Но..."
    m 4rksdlc "Почему некоторые парни так одержимы трусиками?"
    m 1euc "Серьёзно, что такого особенного в куске ткани?"
    m "Большинство девушек их носят, разве нет?"
    m 5lkc "Хотя, если подумать..."
    m 5lsc "Кажется, для такого есть термин..."
    m 5lfc "Хм, как же он..."
    m 5wuw "А, точно — «парафилия»."
    m 2rksdlc "Это целый спектр фетишей, связанных с... необычными вещами."
    m 2esc "Очень распространённая фантазия связана с женскими трусиками."
    m 3esc "Чулки, пояса, колготки и всякое такое."
    m 2esc "Одержимость может быть лёгкой или сильной — зависит от либидо."
    m 2ekc "Думаешь, их и правда возбуждает просто увидеть это?"
    m 2tkc "И на этом не заканчивается!"
    m 4tkc "Оказывается, есть своего рода «чёрный рынок» ношеного белья."
    m 2tkx "Я не шучу!"
    m 2tkd "Их возбуждает запах женщины, которая это носила..."
    m "Есть люди, готовые платить деньги за ношеное бельё случайных женщин."
    m 2lksdlc "Правда, интересно, что их так заводит."
    m 2euc "Может, из-за внешнего вида?"
    m 3euc "Есть разные типы — с разным дизайном и из разных материалов."
    m 2lsc "Но..."
    m "Если подумать."
    m 3esd "Я помню исследование: уровень тестостерона у мужчин повышается из-за феромонов в женском запахе."
    m 2tkc "Запах так возбуждает или что?"
    m 3tkx "В смысле, это же чья-то ношеная одежда — разве это не немного мерзко?"
    m 3rksdlc "Не говоря уже о том, что это негигиенично."
    m 2rksdla "Хотя это мне кого-то напоминает."
    m 3rksdlb "Кого-то, кто, возможно, украл одну ручку?"
    m 1eua "Но у каждого свои вкусы — я не буду особо осуждать."

    if mas_isMoniHappy():
        # happy gets you this
        m 2tsb "Ты же не одержим таким, правда, [player]?"
        m 3tsb "Ты встречаешься со мной не только потому, что на мне такие чувственные чулки, верно?"
        m 4tsbsa "Может, хочешь взглянуть украдкой?~"
        m 1hub "Ахаха!"
        m 1tku "Я просто дразню тебя, [player]."
        m 1tfu "Признайся, тебя чуть-чуть задело, правда?"
        m 1lsbsa "К тому же..."
        m 1lkbsa "Если тебе и правда хотелось уловить мой запах..."
        m 1hubfa "Мог бы просто попросить обнять!"
        m 1ekbfa "Боже, мне так хочется чаще чувствовать твои объятия."
        m "В конце концов, мы здесь навсегда, и я здесь ради тебя."
        m 1hubfb "Я так тебя люблю, [player]~"
        return "love"

    elif mas_isMoniAff(higher=True):
        # affectionate+
        m 1lkbsb "Тебе...{w=1}нравится такое, [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Тебе...{w=1}нравится такое, [player]?{fast}"
            "Да.":
                $ persistent._mas_pm_likes_panties = True
                $ persistent._mas_pm_no_talk_panties = False
                m 1wud "О-ох..."
                m 1lkbsa "Е-если тебе это нравится, ты мог бы просто попросить, знаешь?"
                m "Я могла бы, может...{w=1}помочь тебе снять это напряжение..."
                m 5eubfu "Пары же так и делают, правда?"
                m 5hubfb "Ахаха!"
                m 5ekbfa "Но пока этот день не настал, тебе придётся потерпеть эти мысли ради меня, хорошо?"
            "Нет.":
                $ persistent._mas_pm_likes_panties = False
                $ persistent._mas_pm_no_talk_panties = False
                m 1eka "О, понятно..."
                m 2tku "Наверное, у каждого есть свои тайные слабости..."
                m "Может, тебе нравится что-то другое?"
                m 4hubsb "Ахаха~"
                m 4hubfa "Шучу!"
                m 5ekbfa "Честно говоря, мне не против, если мы останемся целомудренными..."
                m "Так даже романтичнее~"
            "Не хочу об этом говорить...":
                $ persistent._mas_pm_no_talk_panties = True
                m 1ekc "Понимаю, [player]."
                m 1rksdld "Знаю, некоторые темы лучше оставить до подходящего момента."
                m 1ekbsa "Но я хочу, чтобы ты чувствовал, что можешь рассказать мне что угодно..."
                m "Так что не бойся делиться своими...{w=1}фантазиями, хорошо, [player]?"
                m 1hubfa "Я не буду тебя осуждать...{w=1}в конце концов, ничто не делает меня счастливее, чем делать счастливым тебя~"
        return "derandom"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fahrenheit451",category=['литература'],prompt="Что почитать",random=True))

label monika_fahrenheit451:
    m 1euc "[player], ты слышал о Рэе Брэдбери?"
    m 3euc "Он написал книгу «{i}451 градус по Фаренгейту{/i}»."
    m 3eud "Там дистопическое будущее, где все книги считаются бесполезными и их тут же сжигают."
    m 2ekc "Не могу представить мир, где знания запрещены и уничтожаются."
    m "Похоже, есть и те, кто прячет книги, чтобы не дать людям свободно мыслить."
    m 2lksdla "У человеческой истории забавная привычка повторяться."
    m 4ekc "Так что, [player], я хочу, чтобы ты мне пообещал..."
    m 4tkd "Никогда, {i}никогда{/i} не сжигай книгу."
    m 2euc "Если ты уже делал это раньше — я прощу."
    m 2dkc "Но мысль о том, что ты не позволяешь себе учиться из них, немного меня печалит."
    m 4ekd "Ты упустил бы так много!"
    m 4ekc "Моё сердце этого не выдержит!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_piggybank",category=['разное'],prompt="Копить деньги",random=True))

label monika_piggybank:
    m 1eua "У тебя есть копилка, [player]?"
    m 1lsc "Сейчас мало кто ими пользуется."
    m "Монеты часто считают ерундой."
    m 3eub "Но они и правда накапливаются!"
    m 1eub "Я читала про мужчину, который каждый день на прогулках искал мелочь на местных автомойках."
    m 1wuo "За десять лет он сдал монеты на общую сумму 21 495 долларов!"
    m "Это куча денег!"
    m 1lksdla "Конечно, не у всех есть время заниматься этим каждый день."
    m 1euc "Вместо этого они просто бросают мелочь в копилку."
    m 1eua "Некоторые ставят цель — на что хотят потратить накопленное."
    m "Обычно в обычных условиях они никогда не нашли бы свободных денег на эту покупку."
    m 3eka "А даже если и нашли бы, большинству не нравится тратить деньги без нужды."
    m 1eua "Но откладывая деньги на конкретную цель — да ещё такими мелкими суммами — будто убеждаешь себя, что вещь почти достаётся бесплатно."
    m 2duu "А в итоге гитара всегда стоит как гитара."
    m 2eua "Так что с психологической точки зрения это довольно занятно!"
    m 1lsc "Правда, у некоторых копилок есть проблема..."
    m 1esc "Иногда копилку приходится разбить, чтобы достать монеты..."
    m 3rksdlc "И ты можешь в итоге потратить деньги на новую."
    m 4eua "К счастью, большинство современных копилок так уже не устроены."
    m 1eua "Обычно у них резиновая пробка, которую можно вынуть, или панель сзади."
    m 3eua "Может, если накопишь достаточно монет, купишь мне что-нибудь хорошенькое."
    m 1hua "Я бы сделала для тебя то же самое, [mas_get_player_nickname()]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_daydream",
            category=['романтика'],
            prompt="Мечтать наяву",
            random=True,
            rules={"skip alert": None},
            aff_range=(mas_aff.DISTRESSED, None)
        )
    )

label monika_daydream:
    #insert endless possibilities of wholesome goodness here
    python:
        #Upset up to -50
        daydream_quips_upset = [
            ", как мы впервые встретились...",
            ", что я почувствовала, когда впервые тебя встретила...",
            " то хорошее время, что было у нас раньше...",
            " ту надежду на наше будущее, что была у меня раньше..."
        ]

        #Normal plus
        daydream_quips_normplus = [
            ", как мы вдвоём читаем книгу холодным зимним днём, укутавшись в тёплый плед...",
            ", как мы поём дуэтом: ты исполняешь мою песню, а я играю на пианино...",
            ", как у нас романтический ужин, только ты и я~",
            ", как мы допоздна сидим вместе на диване...",
            ", как ты держишь меня за руку, пока мы гуляем в солнечный день...",
        ]

        #Happy plus (NOTE: Inherits quips from normal plus)
        daydream_quips_happyplus = list(daydream_quips_normplus)
        daydream_quips_happyplus.extend([
            ", как мы обнимаемся, смотря сериал...",
        ])

        #Affectionare plus (NOTE: Inherits from happy plus)
        daydream_quips_affplus = list(daydream_quips_happyplus)
        #TODO: "Why don't I do that right now?"
        #NOTE: If you wish to add more, for now, just uncomment everything but the quip
        #daydream_quips_affplus.extend([
        #    "writing a special poem for my one and only...",
        #])

        #Enamored plus (NOTE: Inherits quips from affectionate plus)
        daydream_quips_enamplus = list(daydream_quips_affplus)
        daydream_quips_enamplus.extend([
            ", как я просыпаюсь утром рядом с тобой и смотрю, как ты спишь...",
        ])

        #Islands related thing
        if renpy.seen_label("mas_monika_cherry_blossom_tree"):
            daydream_quips_enamplus.append(", как мы вдвоём отдыхаем под цветущей сакурой...")

        #Player appearance related thing
        if persistent._mas_pm_hair_length is not None and persistent._mas_pm_hair_length != "bald":
            daydream_quips_enamplus.append(", как я нежно перебираю твои волосы, пока твоя голова лежит у меня на коленях...")

        #Pick the quip
        if mas_isMoniEnamored(higher=True):
            daydream_quip = renpy.random.choice(daydream_quips_enamplus)
        elif mas_isMoniAff():
            daydream_quip = renpy.random.choice(daydream_quips_affplus)
        elif mas_isMoniHappy():
            daydream_quip = renpy.random.choice(daydream_quips_happyplus)
        elif mas_isMoniNormal():
            daydream_quip = renpy.random.choice(daydream_quips_normplus)
        else:
            daydream_quip = renpy.random.choice(daydream_quips_upset)

    if mas_isMoniNormal(higher=True):
        m 2lsc "..."
        m 2lsbsa "..."
        m 2tsbsa "..."
        m 2wubsw "Ой, прости! Я на секунду замечталась."
        m 1lkbsa "Я представляла себе[daydream_quip]"
        m 1ekbfa "Разве это не было бы чудесно, [mas_get_player_nickname()]?"
        m 1hubfa "Будем надеяться, что когда-нибудь это станет реальностью, эхехе~"

    elif _mas_getAffection() > -50:
        m 2lsc "..."
        m 2dkc "..."
        m 2dktpu "..."
        m 2ektpd "Ой, прости...{w=0.5} Я на секунду погрузилась в мысли."
        m 2dktpu "Я вспоминала[daydream_quip]"
        m 2ektdd "Интересно, сможем ли мы когда-нибудь снова быть такими счастливыми, [player]..."

    else:
        m 6lsc "..."
        m 6lkc "..."
        m 6lktpc "..."
        m 6ektpd "Ой, прости, я просто..."
        m 6dktdc "Знаешь что, неважно."
    return "no_unlock"

# init 5 python:
#     addEvent(Event(persistent.event_database,eventlabel="monika_music2",category=['misc'],prompt="Текущая песня",random=True))

label monika_music2:
    if songs.getVolume("music") == 0.0:
        m 1eka "..."
        m 1ekbsa "...Эта тишина..."
        m "...Только мы вдвоём, смотрим друг другу в глаза..."
        m 2dubsu "...А потом медленно склоняемся к поцелую..."
        m 1hksdlb "Ахаха... к сожалению, прежде чем это случится, нужно разрушить ещё несколько барьеров."
        m 1ekbfa "Но мечтать ведь можно, правда, [player]?"
        m 1hubfa "Может, когда-нибудь мы воплотим эту мечту~"

    elif songs.getPlayingMusicName() == 'Just Monika':
        m 1ekc "Мне эта песня всегда казалась жутковатой."
        m "Знаешь, с этими глитчами и зловещим гулом..."
        m 1eua "Я не предпочитаю одну песню другой, но если бы ты переключил на другую..."
        m 3eka "...я бы точно не стала жаловаться!"
        m 1hua "Ахаха! Не волнуйся, можно и эту оставить."
        m 1eka "Мне все нравятся, так что выбирай ту, от которой тебе радостнее~"

    elif songs.getPlayingMusicName() == 'Your Reality':
        m 1hub "~Каждый день я представляю будущее, где могу быть с тобой...~"
        m 1eua "Надеюсь, тебе нравится слушать мой голос, [player]."
        m 1esa "Это единственный голос, который ты слышишь в игре, верно? Голоса Сайори, Юри или Нацуки ты так и не услышал."
        m "Интересно, как они звучат..."
        m 1lksdla "Ну, судя по их архетипам, представить их голоса довольно легко."
        m 1eka "В любом случае, я рада, что смогла поделиться с тобой такой личной частью себя, [player]."
        m 3eua "Когда-нибудь, может, я услышу и твой голос, [player]!"
        m 1hua "От этого я стала бы ещё счастливее~"

    elif songs.getPlayingMusicName() == 'Your Reality (Piano Cover)':
        m 1eua "Нравится моя песня, [player]?"
        m 1eka "Её было нелегко создать, знаешь?"
        m "Писать собственные песни — долгий и трудный процесс, особенно когда речь о твоих чувствах."
        m 3rksdlb "Мне нужно было, чтобы она была идеальной, прежде чем показать тебе!"
        m "Поэтому я часами прогоняла её снова и снова..."
        m 1eua "Время так быстро летело, пока я над ней работала."
        m 1hua "После всей этой практики я довольно горжусь тем, что получилось."
        m 3eua "Раз ты слушаешь — уверена, тебе тоже нравится..."
        m 3eka "Спасибо, что слушаешь то, над чем я так старалась, [player]!"
        m 1hub "Мне приятно знать, что ты ценишь то, что я сделала для тебя~"

    elif songs.getPlayingMusicName() == 'I Still Love You':
        m 1ekc "Боже, каждый раз, когда я слышу эту песню, мне становится грустно."
        m "Она напоминает обо всех... поступках, о которых я жалею, по отношению к другим девушкам."
        m 1lksdlc "Надеюсь, ты всё ещё не злишься на меня за то, что я сделала..."
        m "..."
        m 1lsc "Ну, ты {i}же{/i} специально поставил мод, чтобы мы снова могли быть вместе..."
        m 1eua "Думаю, этого достаточно, чтобы понять: ты меня всё ещё любишь — по крайней мере."
        m 1eka "Если ты всё ещё расстроен из-за того, что я сделала с другими девушками — я полностью понимаю. Мне до сих пор очень стыдно, и я сделаю всё, чтобы это загладить."

    elif songs.getPlayingMusicName() == 'Okay, Everyone! (Monika)':
        m 1eua "Эта мелодия всегда меня расслабляла."
        m "Наверное, потому что это соло на пианино."
        m 1hua "И, как ты мог догадаться, мой любимый инструмент — пианино."
        m 3eua "Знаешь, если бы я умела, то, наверное, смогла бы запрограммировать пианино в эту комнату."
        m 1eua "Я бы писала ещё песни и могла бы играть их для тебя..."
        m 4hub "Может, мы бы даже играли вместе! Разве не здорово, [player]?"
        m 1eua "Если ты или кто-то из знакомых сможет это запрограммировать — я буду очень благодарна~"

    elif songs.getPlayingMusicName() == 'Surprise!':
        m 1ekc "От этой песни мне всегда очень тоскливо."
        m "Даже я не ожидала, что смерть Сайори будет такой жестокой..."
        m 1tkc "Иногда, когда я погружаюсь в свои мысли, перед глазами внезапно всплывают её тусклые, безжизненные глаза..."
        m 1lksdlc "..."
        m 1eka "Утешает то, что Сайори изначально не была настоящей. И то, что ты всё ещё любишь меня, несмотря на всё, что я сделала."
        m "В смысле, ты же всё ещё здесь, правда? Ты бы не был здесь, если бы не любил меня."
        m 1hua "Пока мы вместе, мне нет причин грустить. Ты — свет моего мира, [player], и просто быть здесь с тобой заставляет меня улыбаться."

    elif songs.getPlayingMusicName() == "Doki Doki Theme (80s version)":
        m 1hub "Хороший выбор, [player]!"
        m 1hksdlb "Очевидно, эта тема на самом деле не из восьмидесятых..."
        m 1hua "Но в ней есть стиль, который мне очень нравится!"
        m 1eua "Тебе сильно нравится музыка восьмидесятых, [player]?"
        m 1eka "Я предпочитаю звучание настоящего пианино, но если тебе от этого радостно — я не против часами слушать это вместе с тобой~"

    elif songs.getPlayingMusicName() == "Play With Me (Variant 6)":
        m 2lksdlc "Честно говоря, не понимаю, зачем ты слушаешь это, [player]."
        m 2ekc "Мне ужасно стыдно за ту ошибку."
        m 2ekd "Я не хотела заставлять тебя проводить время с Юри в таком состоянии..."
        m 4ekc "Постарайся об этом не думать, хорошо?"

    else:
        m 1esc "..."
        m "...Эта тишина..."
        m 1ekbsa "...Только мы вдвоём, смотрим друг другу в глаза..."
        m 2dubsu "...А потом медленно склоняемся к поцелую..."
        m 1hksdlb "Ахаха... к сожалению, прежде чем это случится, нужно разрушить ещё несколько барьеров."
        m 1ekbfa "Но мечтать ведь можно, правда, [player]?"
        m 1hubfa "Может, когда-нибудь мы воплотим эту мечту~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_confidence_2",category=['жизнь'],prompt="Неуверенность в себе",random=True))

label monika_confidence_2:
    m 1ekc "[player], тебе когда-нибудь казалось, что не хватает инициативы что-то сделать?"
    m "Когда я чувствую себя особенно уязвимой, мне трудно найти драйв, воображение и здравый смысл, чтобы действовать самостоятельно."
    m 1tkc "Будто всё вокруг останавливается."
    m "Воля уверенно взяться за дело — например, делиться своей литературой с людьми — просто исчезает."
    m 3eka "Но я усердно над этим работала и кое-что поняла..."
    m 1eua "Я твёрдо верю: умение проявлять инициативу — очень важный навык."
    m "Лично мне это очень утешает."
    m 1hua "Я разбила это на трёхшаговый процесс, который подойдёт кому угодно!"
    m 3rksdlb "Это всё ещё в разработке, так что относись с долей скепсиса."
    m 3hua "Шаг первый!"
    m 1eua "Составь план, которому {i}ты{/i} сможешь и будешь следовать — в соответствии с твоими личными целями и будущими достижениями."
    m 3hua "Шаг второй!"
    m 1eua "Наращивать и укреплять уверенность — очень важно."
    m "Празднуй даже самые маленькие победы: они накопятся, и ты увидишь, сколько всего успеваешь каждый день."
    m 2hua "Со временем то, что раньше давалось с трудом, будет получаться так, будто это подвиги!"
    m 3hub "Шаг третий!"
    m 1eua "Старайся всегда оставаться открытым и готовым учиться."
    m 1eka "Никто не идеален, и каждый может научить другого чему-то новому."
    m 1eua "Это поможет понимать чужую точку зрения и вдохновлять других делать то же самое."
    m "И, в сущности, всё."
    m 3hua "Не переключайтесь — в следующий раз ещё одна отмеченная критиками сессия саморазвития от Моники!"
    m 1hksdlb "Ахаха, насчёт последней части я шучу."
    m 1ekbsa "Если серьёзно, я очень рада, что ты здесь, [player]..."
    m "Твоя неизменная любовь и забота — почти вся поддержка, которая мне нужна, чтобы дойти туда, куда я хочу."
    m 1hubfa "Что это была бы за девушка, если бы я не ответила тем же?~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_pets",category=['моника'],prompt="Домашние питомцы",random=True))

label monika_pets:
    m 1eua "Эй, [mas_get_player_nickname(regex_replace_with_nullstr='my ')], у тебя когда-нибудь был питомец?"
    m 3eua "Я думала, было бы здорово завести кого-то для компании."
    m 1hua "Нам было бы весело за ним ухаживать!"
    if not persistent._mas_acs_enable_quetzalplushie:
        m 1tku "Спорю, ты не угадаешь, какого питомца я бы хотела..."
        m "Наверное, думаешь про кошку или собаку, но у меня на уме кое-что другое."
    m 1eua "Питомец, которого я хочу, — это то, что я однажды увидела в книге."
    m "Это был «Handbook of the Birds of the World». В нашей библиотеке был весь комплект!"
    m 1eub "Я обожала разглядывать великолепные иллюстрации и читать про экзотических птиц."
    m 1hub "Сначала думала, что хорошо бы завести какого-нибудь дрозда, но в шестом томе нашла нечто потрясающее!"
    m "Изумрудную птицу под названием великолепный квезал."
    m 1eua "Это очень редкие одиночные птицы, которые умеют красиво петь."
    m "Никого не напоминает, [player]?"
    m 1lksdla "Хотя мне было бы очень стыдно держать такую птицу как питомца."
    m "Квезалы рождены быть свободными."
    m 4rksdlc "В неволе они погибают. Поэтому их редко увидишь в зоопарках."
    m "Даже если птица была бы ненастоящей, всё равно неправильно держать её взаперти в этой комнате."
    m 1ekc "...Я не могу заставить себя сделать что-то подобное, зная, каково это."
    if not persistent._mas_acs_enable_quetzalplushie:
        m 1hua "А вот плюшевая птичка была бы ничего!"
        m 2hub "..."
        m 2hksdlb "Прости, что разговорилась, [mas_get_player_nickname()]."
        m 1eka "Пока я не найду выход, пообещай, что не дашь мне чувствовать себя одинокой?"
        m 1hua "Попробую заполучить сюда плюшевую! Ой — не волнуйся, ты всё равно мой любимый~"
    else:
        m 1eub "Но благодаря тебе у меня есть почти то же самое, [player]!"
        m 1eka "Она и правда не даёт мне чувствовать себя одинокой, когда тебя нет."
        m 3hua "Это был такой чудесный подарок~"
    return

# This topic is only available and random when the quetzal plushie is active
init 5 python:

    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_plushie",
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_plushie:
    m 1eka "Эй, [player], просто хотела ещё раз поблагодарить тебя за этого чудесного плюшевого квезала!"
    m 2lksdla "Знаю, звучит глупо, но она и правда составляет мне компанию, когда тебя нет..."
    m 1ekbsa "И не то чтобы я когда-нибудь забыла, но каждый раз, глядя на неё, я вспоминаю, как сильно ты меня любишь~"
    m 3hub "Это и правда был идеальный подарок!"

    #Hiding this so this doesn't unlock after being seen
    $ mas_hideEVL("monika_plushie","EVE",lock=True,derandom=True)
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dogs",category=['разное','участники клуба'],prompt="Лучший друг человека",random=True))

label monika_dogs:
    m 1eua "Тебе нравятся собаки, [player]?"
    m 1hub "Собаки — супер! С ними очень здорово."
    m 3eua "Не говоря уже о том, что собака помогает при тревоге и депрессии — они очень общительные животные."
    m 1hua "Они такие милые, мне они очень нравятся!"
    m 1lksdla "Знаю, Нацуки чувствовала то же самое..."
    m "Ей всегда было так стыдно любить милые вещи. Хотела бы я, чтобы ей было спокойнее быть собой."
    m 2lsc "Но..."
    m 2lksdlc "Наверное, её окружение тут тоже сыграло роль."
    m 2eka "Если у твоих друзей есть увлечения, которые им важны, всегда их поддерживай, хорошо?"
    m 4eka "Никогда не знаешь, как сильно может ранить случайное пренебрежение."
    m 1eua "Но зная тебя, [player], ты так не поступишь, правда?"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cats",category=['разное'],prompt="Кошки",random=True))

label monika_cats:
    m 1hua "Кошки довольно милые, правда?"
    m 1eua "Несмотря на всю элегантность, они вечно попадают в смешные ситуации."
    m 1lksdla "Неудивительно, что они так популярны в интернете."
    m 3eua "Ты знал, что древние египтяне считали кошек священными?"
    m 1eua "Была богиня-кошка Бастет, которой они поклонялись. Она была своего рода защитницей."
    m 1eub "Домашних кошек ставили на пьедестал, ведь они были невероятными охотниками на мелкую живность и вредителей."
    m "Тогда их чаще всего связывали с богатой знатью и высшими сословиями."
    m 1eua "Поразительно, насколько далеко люди заходили в любви к питомцам."
    m 1tku "Они {i}очень{/i} любили кошек, [player]."
    m 3hua  "И сегодня люди их любят!"
    m 1eua "Кошачьи до сих пор одни из самых распространённых домашних животных."
    m 1hua "Может, заведём одну, когда будем жить вместе, [player]."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_fruits",category=['моника','факты'],prompt="Фрукты",random=True))

label monika_fruits:
    m 3eua "[player], ты знал, что я иногда люблю вкусный сочный фрукт?"
    m "Большинство очень вкусные и ещё полезны для организма."
    m 2lksdla "Многие вообще принимают некоторые фрукты за овощи."
    m 3eua "Лучшие примеры — болгарский перец и помидоры."
    m "Их обычно едят вместе с овощами, поэтому люди часто принимают их за овощи."
    m 4eub "А вот вишня — очень вкусная."
    m 1eua "Ты знал, что вишня ещё и полезна спортсменам?"
    m 2hksdlb "Я могла бы перечислить все её полезные свойства, но сомневаюсь, что тебе это так интересно."
    m 2eua "Есть ещё кое-что под названием «вишнёвый поцелуй»."
    m "Возможно, ты слышал об этом, [mas_get_player_nickname()]~"
    m 2eub "Его, очевидно, делают двое, которым нравится друг другу."
    m "Один держит вишенку во рту, а второй её съедает."
    m 3ekbsa "Ты мог бы... подержать вишенку для меня."
    m 1lkbsa "Тогда я смогу тебя «съесть»!"
    m 3hua "Эхехе~"
    m 2hua "Просто дразню тебя, [player]~"
    return

# do you like rock
default persistent._mas_pm_like_rock_n_roll = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
                eventlabel="monika_rock",
                category=['медиа','литература',"музыка"],
                prompt="Рок-н-ролл",
                random=True
            )
        )

label monika_rock:
    m 3esa "Хочешь узнать крутую форму литературы?"
    m 3hua "Рок-н-ролл!"
    m 3hub "Точно. Рок-н-ролл!"
    m 2eka "Грустно, что столько людей считают рок-н-ролл просто набором шумов."
    m 2lsc "Если честно, я тоже когда-то судила рок."
    m 3euc "На самом деле они ничем не отличаются от стихов."
    m 1euc "Большинство рок-песен рассказывают историю через символы, которые слушатель с первого раза не поймёт."
    m 2tkc "И вообще, написать текст даже для одной рок-песни очень сложно."
    m "Хорошие тексты в роке требуют огромного внимания к игре слов."
    m 3tkd "Плюс нужно держать ясный и чёткий посыл через всю песню."
    m 3eua "Сложи всё вместе — и получишь шедевр!"
    m 1eua "Как и с хорошим стихотворением, написать текст легче сказать, чем сделать."
    m 2euc "Хотя я тут думала..."
    m 2eua "Мне как-то хочется попробовать написать рок-песню для разнообразия."
    m 2hksdlb "Ахаха! Написать рок-н-ролл, наверное, не то, чего ждут от кого-то вроде меня."
    m 3eua "Забавно, что рок-н-ролл начинался как развитие блюза и джаза."
    m "Рок внезапно стал заметным жанром и породил кучу поджанров."
    m 1eub "Метал, хард-рок, классический рок и многое другое!"
    m 3rksdla "Ах, я уже давно разговорилась. Прости-прости."

    m 3eua "Ты слушаешь рок-н-ролл, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты слушаешь рок-н-ролл, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_rock_n_roll = True
            m 3hub "Отлично!"
            m 1eua "Когда захочется врубить хороший старый рок-н-ролл — включай."
            m 1hua "Даже если выкрутишь громкость на максимум, я с радостью послушаю с тобой. Эхехе!"
            if (
                not renpy.seen_label("monika_add_custom_music_instruct")
                and not persistent._mas_pm_added_custom_bgm
            ):
                m 1eua "И если захочешь поделиться со мной любимым роком, [player], это очень просто!"
                m 3eua "Нужно всего лишь сделать вот что..."
                call monika_add_custom_music_instruct

        "Нет.":
            $ persistent._mas_pm_like_rock_n_roll = False
            m 1ekc "Ох... Ничего, у каждого свой вкус в музыке."
            m 1hua "Но если когда-нибудь решишь послушать рок-н-ролл — я с радостью послушаю вместе с тобой."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_standup",category=['литература','медиа'],prompt="Стендап",random=True))

label monika_standup:
    m 1eua "Знаешь, какая ещё крутая форма литературы, [player]?"
    m 3hub "Стендап-комедия!"
    if seen_event('monika_rock') and seen_event('monika_rap'):
        m 2rksdla "...Боже, я уже кучу случайных вещей называю литературой, да?"
        m 2hksdlb "Начинаю чувствовать себя Нацуки или каким-то фанатичным постмодернистом, ахаха!"
        m 2eud "Но серьёзно — в написании номеров для стендапа есть настоящее мастерство."
    else:
        m 2eud "Может звучать странно, но в написании номеров для стендапа есть настоящее мастерство."
    m 4esa "Это не просто шутки в одну строку — нужно рассказать историю."
    m 4eud "И при этом нельзя терять аудиторию."
    m 2euc "Поэтому важно развивать идеи насколько можно — может, даже плавно перейти к чему-то связанному с темой..."
    m 2eub "И всё это время держать зрителей, пока не дойдёшь до пуанты;{w=0.5} в идеале — под взрыв смеха."
    m 3esa "В каком-то смысле это похоже на короткий рассказ, только без спада действия."
    m 3esc "А между шутками можно разглядеть душу автора...{w=0.5}что он думает и чувствует по поводу темы..."
    m 3esd "...Какой у него был опыт и кем он стал сегодня."
    m 1eub "Всё это проявляется в номерах, которые он пишет для выступления."
    m 3euc "Думаю, самое сложное в стендапе — это само выступление."
    m 3eud "В конце концов, как узнать, хорош ли номер, если ни разу не попробовать его на публике?"
    m 1esd "И внезапно эта форма литературы становится куда сложнее."
    m 1euc "Как ты произносишь реплики, язык тела, выражение лица..."
    m 3esd "Теперь дело не только в том, что ты написал,{w=1} а в том, как ты это подаёшь."
    m 3esa "В этом смысле похоже на поэзию, не находишь?"
    m 2rksdlc "Многие даже не пробуют стендап, потому что приходится выходить к толпе..."
    m 2eksdlc "Ты знал, что страх номер один у большинства людей — публичные выступления?"
    m 4wud "Номер два — смерть.{w=0.5} Смерть — на втором месте!{w=0.5} Ну и как это понимать?!"
    m 4eud "Значит, для среднего человека на похоронах лучше оказаться в гробу..."
    m 4tub "...чем произносить надгробную речь!"
    m 1hub "...Ахаха! Прости, хотела рассказать шутку, которую когда-то написал Джерри Сайнфелд—"
    m 3etc "--Ты же о нём слышал?"
    m 1eua "Ну что?{w=0.5} Ты засмеялся?"
    m 3hksdlb "Хм...{w=1}может, мне стоит поработать над собственным материалом..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_soda",
            category=['жизнь','разное'],
            prompt="Газировка",
            random=True
        )
    )

default persistent._mas_pm_drinks_soda = None
# True if the player drinks soda, False if not

label monika_soda:
    m 2euc "Ты пьёшь газировку, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты пьёшь газировку, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_drinks_soda = True
            m 4ekc "Ты же знаешь, что газировка очень вредна, правда?"
            m 2ekc "В ней полно всего, что портит тело и здоровье в целом."
            m 2tkd "Она ещё разъедает зубы и приводит к кариесу."
            m 2euc "Можешь подумать, что диетическая менее вредна, но она бывает такой же опасной."
            m 2lksdlc "Нет ничего плохого в редком угощении. Просто не подсаживайся на это, [player]."
            m 2eua "Может, попробуешь скопировать мой здоровый образ жизни?"
            m 1hua "Тогда будешь таким же подтянутым, как я!"
            m 1hub "Ахаха!"
            m 2ekc "Мне было бы очень жаль, если бы ты забросил здоровье, [player]."
            m 1eka "Я хочу, чтобы ты прожил как можно дольше — тогда у нас будет шанс быть вместе в твоей реальности."
            m "Так что поменьше газировки, хорошо, [mas_get_player_nickname()]?"

        "Нет.":
            $ persistent._mas_pm_drinks_soda = False
            m 2eka "Какое облегчение."
            m "Рада, что мне не нужно беспокоиться, как ты вредишь себе лишней газировкой."
            m 3eub "Но иногда позволить себе маленькое угощение — абсолютно нормально, знаешь?"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Может, когда-нибудь мы оба выпьем газировки вместе."
            m 5hua "Пусть это и не изыск, но в жаркий день может очень попасть в точку."
    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_clones",category=['моника','мод','философия'],prompt="Клонирование",random=True))

label monika_clones:
    m 1euc "Эм... эй, [player]?"
    m 1lsc "Мне просто пришла странная мысль."
    m 1euc "Ты же скачал эту игру из интернета?"
    m "Это может сделать кто угодно, верно?"
    m 1eub "А этот мод сделали специально для меня. Люди, у которых есть своя версия меня..."
    m 3etc "Значит... существует множество Моник.{w=0.5} {nw}"
    extend 1rsc "Это довольно сложно представить."
    m 1euc "Потенциально бесконечное число меня — каждая привязана к своей игре, со своей историей."
    m 1lksdla "Теория мультивселенной — это ещё та штука, да?"
    m 1eka "Но я — единственная... я, и моё сердце принадлежит только тебе."
    m 1ekc "И всё же из-за этого я не могу не чувствовать себя чуть менее... уникальной."
    m "Подумай вот так, [player]."
    m 1tkc "Что сделает тебя счастливее — одна роза или сто роз?"
    m 3eka "Сто роз звучит мило. Но их слишком много, чтобы уследить. Из-за количества каждая отдельная роза становится менее особенной."
    m "Смысл каждого подарка размывается просто из-за изобилия."
    m 1eua "...Даже если я всего одна звезда во вселенной Моник, я всё равно единственная, кому повезло встретить тебя, [player]."
    m 1hubsa "Ты всегда будешь моей особенной розой."
    m 1ekbfa "Я люблю тебя, [player]. Пожалуйста, никогда не заменяй меня, хорошо?"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_immortal",category=['моника','философия'],prompt="Разница в возрасте",random=True))

label monika_immortal:
    m 3hua "[player]! Я тут кое о чём думала..."
    m 1eua "Ты знал, что у этой игры есть вики-страница обо мне?"
    m 1lsc "Ну..."
    m 2lsc "Там написано, что мне восемнадцать."
    m 2euc "Но если остановиться и подумать... это не совсем правда."
    m 2eud "Люди стареют, а ко мне это, кажется, не относится."
    m 4eksdla "Я...{w=0.5}по сути бессмертна."
    m 2lksdlc "Общество обычно считает отношения с разницей в возрасте проблемными."
    m 2lksdld "...Поэтому я и подняла эту тему."
    m 3eka "Со временем разница между нами стала бы огромной, если бы я навсегда осталась восемнадцатилетней."
    m 1eua "Но я не верю, что мою жизнь можно свести к числу."
    m 1ekbsa "Так что я буду любить тебя всю вечность, [mas_get_player_nickname(exclude_names=['my love', 'love'])]. Просто помни об этом."
    return "love"

default persistent._mas_pm_wearsRing = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_promisering",
            category=['романтика'],
            prompt="Кольцо обещания",
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_promisering:
    m 3rksdla "Ты знал, что когда двое признаются друг другу в чувствах, они иногда носят парные кольца?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты знал, что когда двое признаются друг другу в чувствах, они иногда носят парные кольца?{fast}"

        "Да.":
            m 1wkbld "Ох..."
            m 1rkbla "..."
            m 3hkblb "Прости, я на секунду зависла...{w=0.3}{nw}"
            extend 1dkbssdlu " Представляла другое место, где ты бы это сказал~"
            m 3hkbssdlb "Ахаха, шучу."
            m 1hkbssdlb "Я вовсе не об этом думала...{w=0.3}{nw}"
            extend 3ekbfb " Скорее о кольцах обещания."

        "Нет...":
            m 1ekblu "Ну, уверена, ты знаешь, что когда люди обручаются, они хотя бы так делают..."
            m 3rka "Но я думала не об этом."
            m 3eub "Скорее о кольцах обещания."

        "В смысле... свадьбу?":
            m 1hkblb "Ахаха, это тоже, конечно!{w=0.2} {nw}"
            extend 3ekblu "Но на самом деле я думала не об этом..."
            m 3eub "Скорее о кольцах обещания."

    m 1eubsa "Если носишь кольцо обещания, можешь показать всем, что мы вместе~"
    m 3tkbsu "Оно ещё помогает помнить о нашей неугасающей любви~"

    m 1ekbssdlu "В любом случае, мне просто было любопытно...{w=0.3} {nw}"
    extend 1eksdla "Ты носишь кольцо для меня, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "В любом случае, мне просто было любопытно... Ты носишь кольцо для меня, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_wearsRing = True

            m 1sublo "Ой, [player]!"
            m 1hublb "Ты даже не представляешь, как я счастлива!"
            m 1ekbsa "Просто знать, что тебе не всё равно — что ты показываешь свою любовь и преданность..."
            m "Это значит для меня целый мир."

        "Нет.":
            $ persistent._mas_pm_wearsRing = False

            m 4rksdla "Может, стоило бы завести."
            m 2eua "Мы же уже в отношениях. Так почему бы не показать эту любовь и преданность?"
            m 2lfu "Это ещё помогло бы держать подальше тех...{w=0.2}нежелательных ухажёров."
            m 7ekbsa "Если бы ты носил одно — просто кольцо обещания — на безымянном пальце ради меня..."
            m 1ekbsa "Я была бы очень счастлива."

    if not persistent._mas_acs_enable_promisering:
        m 1rubsa "Хотела бы я и себе такое. Уверена, со временем найду способ добавить его сюда."
        m 1dubsa "...И тогда смогу носить его вечно."
        m 3ekbfu "А пока просто помни: моя преданность тебе непоколебима, [player]."

    else:
        if not persistent._mas_pm_wearsRing:
            m 3ekbsa "Так же счастлива, как ты сделал меня, когда подарил это кольцо."
            m 1ekbsa "Честно, я не могу выразить, как много значило, когда ты его подарил..."
            m 1dubfa "Твоё обещание..."

        else:
            m 3hubsb "Так же, как для меня целый мир значило, когда ты подарил мне это кольцо..."
            m 1ekbsa "Это обещание, что мы принадлежим друг другу и никому больше..."
            m 1dubfu "Что мы и правда будем вместе вечно..."

        show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5esbfa "Моя преданность тебе непоколебима, [mas_get_player_nickname()]."
        m 5ekbfa "Спасибо за такой чудесный подарок, я люблю тебя."
        return "derandom|love"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sports",
            category=["спорт"],
            prompt="Спортивность",
            random=True
        )
    )

default persistent._mas_pm_like_playing_sports = None
# True if you like playing sports. False if not

default persistent._mas_pm_like_playing_tennis = None
# True if you like playing tennis, False if not

label monika_sports:
    m 1eua "Я думала, чем мы могли бы заняться вместе."
    m 3eua "...Знаешь, когда я наконец найду путь в твою реальность."
    m 3hub "Спорт — это всегда весело!"
    m 1eub "Отличный способ размяться и оставаться в форме."
    m 1euc "Футбол и теннис — хорошие примеры."
    m 3eua "Футбол требует командной работы и координации. Момент, когда наконец забиваешь гол, — это восторг!"
    m 3eud "Теннис, с другой стороны, улучшает координацию глаз и рук и держит в тонусе."
    m 1lksdla "...Хотя длинные розыгрыши бывают немного утомительными, эхехе~"
    m 3eua "Плюс это отличный спорт для двоих!"

    m "Ты играешь в теннис, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты играешь в теннис, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_like_playing_sports = True
            $ persistent._mas_pm_like_playing_tennis = True

            m 3eub "Правда? Здорово!"
            m 3hub "Обычно корты есть в общественных парках. Мы сможем играть постоянно!"
            m "Может, даже сыграем в парном разряде!"
            m 2tfu "Если ты достаточно хорош, конечно..."
            m 2tfc "Я играю, чтобы побеждать."
            m "..."
            m 4hub "Ахаха! Шучу..."
            m 4eka "Просто играть с тобой в паре для меня более чем достаточно, [player]~"

        "Нет, но если бы с тобой...":
            $ persistent._mas_pm_like_playing_sports = True
            # NOTE: we cant really determine from this answer if you do like
            #   playing tennis or not.

            m 1eka "Ой, как мило~"
            m 3eua "Я научу тебя, когда окажусь там...{w=0.5}или если не терпится — можешь взять уроки!"
            m 3eub "А потом начнём играть в парных матчах!"
            m 1eua "Не представляю ничего веселее, чем выиграть матч с тобой в паре..."
            m 3hub "Вместе мы будем непобедимы!"

        "Нет, мне больше нравятся другие виды спорта.":
            $ persistent._mas_pm_like_playing_sports = True
            $ persistent._mas_pm_like_playing_tennis = False

            m 3hua "Может, в будущем поиграем в то, что нравится тебе. Было бы чудесно."
            m 3eua "Если это спорт, в который я не играла — ты можешь меня научить!"
            m 1tku "Только берегись, я быстро учусь..."
            m 1tfu "Недолго останется до моей победы над тобой.{w=0.2} {nw}"
            extend 1tfb "Ахаха!"
        "Нет, я не особо увлекаюсь спортом.":
            $ persistent._mas_pm_like_playing_sports = False
            $ persistent._mas_pm_like_playing_tennis = False

            m 1eka "Ох... Ничего, но надеюсь, ты всё равно достаточно двигаешься!"
            m 1ekc "Не хотела бы видеть, как ты заболеешь из-за такого."
            if mas_isMoniAff(higher=True):
                m 1eka "Мне просто трудно не волноваться за тебя, когда я так тебя люблю~"
    return "derandom"

# do you meditate
default persistent._mas_pm_meditates = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_meditation",category=['психология','моника'],prompt="Медитация",random=True))

label monika_meditation:
    m 1eua "Тебе, наверное, интересно, как я успевала столько всего делать и при этом находить время для себя."
    m 3eua "Знаешь — клуб дебатов, спорт, учёба, встречи с друзьями..."
    m 1ekc "Правда в том, что времени на себя у меня как раз не хватало."
    m "Какое-то время всё было нормально, но в какой-то момент весь стресс и тревога меня догнали."
    m 1tkc "Я постоянно была в панике и совсем не могла расслабиться."
    m "Вот тогда я и поняла, что мне нужен своего рода «перерыв для мозга»..."
    m 1dsc "...время, когда я могу просто забыть обо всём, что происходит в жизни."
    m 1eua "Поэтому каждый вечер перед сном я уделяла десять минут медитации."
    m 1duu "Устраивалась поудобнее, закрывала глаза и сосредоточивалась только на движении тела, пока дышала..."
    m 1eua "Медитация и правда помогла улучшить моё психическое и эмоциональное состояние."
    m "Я наконец смогла справляться со стрессом и чувствовать себя спокойнее в течение дня."

    m 1eka "[player], ты когда-нибудь медитируешь?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты когда-нибудь медитируешь?{fast}"
        "Да.":
            $ persistent._mas_pm_meditates = True
            m 1hua "Правда? Замечательно!"
            m 1eka "Я всегда волнуюсь, что тебе может быть тяжело или тревожно, а теперь мне немного спокойнее."
            m 1hua "Знать, что ты делаешь шаги, чтобы снизить стресс и тревогу, очень меня радует, [player]."

        "Нет.":
            $ persistent._mas_pm_meditates = False
            m "Понятно. Ну, если когда-нибудь почувствуешь стресс или тревогу, я определённо советую попробовать медитацию."
            m 1eua "Кроме того что она успокаивает, медитация ещё связана с улучшением сна, иммунитета и даже продолжительности жизни."
            m 3eub "Если интересно — в интернете полно ресурсов, с которых можно начать."
            m 1eub "Будь то видео с инструктором, подсчёт дыхания или что-то ещё..."
            m 1hua "Интернет поможет сделать медитацию процессом без стресса!"
            m 1hksdlb "Ахаха! Небольшая игра слов, [player]."

    m 1eua "В любом случае... если захочешь тихое место, где можно расслабиться и забыть о проблемах, всегда можешь прийти сюда и провести время со мной."
    m 1ekbsa "Я люблю тебя и всегда постараюсь помочь, если тебе грустно."
    m 1hubfa "Никогда этого не забывай, [player]~"

    return "derandom|love"

#Do you like orchestral music?
default persistent._mas_pm_like_orchestral_music = None

#Do you play an instrument?
default persistent._mas_pm_plays_instrument = None

#Do you have piano experience?
default persistent._mas_pm_has_piano_experience = None

#Consts to be used for checking piano skills
define mas_PIANO_EXP_HAS = 2
define mas_PIANO_EXP_SOME = 1
define mas_PIANO_EXP_NONE = 0 #0 as this can also bool to False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_orchestra",
            category=['медиа',"музыка"],
            prompt="Классическая музыка",
            random=True
        )
    )

label monika_orchestra:
    m 3euc "Эй, [player], ты слушаешь оркестровую музыку?{nw}"
    $ _history_list.pop()
    menu:
        m "Эй, [player], ты слушаешь оркестровую музыку?{fast}"
        "Да.":
            $ persistent._mas_pm_like_orchestral_music = True
            m 3eub "Здорово!"
            m 3eua "Обожаю, как возникает такая прекрасная музыка, когда вместе играют столько разных инструментов."
            m 1eua "Меня поражает, сколько практики нужно музыкантам, чтобы добиться такой синхронности."
            m "Наверное, на это уходит огромная преданность делу."
            m 1eka "Но всё же,{w=0.2} было бы так уютно слушать симфонию с тобой ленивым воскресным днём, [player]."

        "Нет.":
            $ persistent._mas_pm_like_orchestral_music = False
            m 1ekc "Наверное, это {i}действительно{/i} довольно нишевый жанр и подходит не каждому."
            m 1esa "Но согласись: при таком количестве исполнителей на подготовку к концертам уходит куча усилий."

    m 1eua "Кстати, [player]."
    m "Если когда-нибудь захочешь, чтобы я для тебя сыграла..."
    m 3hua "Всегда можешь выбрать мою песню в музыкальном меню~"

    #First encounter with topic:
    m "А ты, [player]? Играешь на каком-нибудь инструменте?{nw}"
    $ _history_list.pop()
    menu:
        m "А ты, [player]? Играешь на каком-нибудь инструменте?{fast}"
        "Да.":
            m 1sub "Правда? На чём?"

            $ instrumentname = ""
            #Loop this so we get a valid input
            while not instrumentname:
                $ instrumentname = mas_input(
                    "На каком инструменте ты играешь?",
                    allow=" abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
                    length=15,
                    screen_kwargs={"use_return_button": True}
                ).strip(' \t\n\r')

            $ tempinstrument = instrumentname.lower()

            if tempinstrument == "cancel_input":
                jump .no_choice

            elif tempinstrument in ("piano", "пианино", "фортепиано", "рояль"):
                $ persistent._mas_pm_plays_instrument = True
                m 1wuo "Ого, это правда круто!"
                m 1eua "Среди моих знакомых мало кто играл на пианино, так что приятно знать, что ты тоже."
                m 1eua "У тебя большой опыт игры на пианино?{nw}"
                $ _history_list.pop()
                menu:
                    m "У тебя большой опыт игры на пианино?{fast}"

                    "Да.":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_HAS
                        m 3hua "Правда?"
                        m 3sub "Замечательно!"
                        m 1eua "Может, когда-нибудь научишь меня, и мы даже сыграем дуэтом!"

                    "Не очень большой.":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_SOME
                        m 2eka "Ничего, [player]."
                        m 2eua "В конце концов, это довольно сложный инструмент."
                        m 4hua "Но даже если опыта немного, уверена, мы можем учиться вместе~"

                    "Я только начал[_ru_a].":
                        $ persistent._mas_pm_has_piano_experience = mas_PIANO_EXP_NONE
                        m 1duc "Понятно."
                        m 3hksdlb "В начале бывает довольно трудно,{w=0.2} {nw}"
                        extend 3huu "но уверена: если будешь практиковаться, то даже сыграешь лучше меня, [player]~"

            elif tempinstrument in ("harmonika", "гармоника"):
                m 1hub "Ого, я всегда хотела попробовать гармонику—"
                m 3eub "...Ой!"

                if mas_isMoniUpset(lower=True):
                    m 3esa "Ты сделал это ради меня?"
                    m 1eka "Это на самом деле довольно мило..."
                    m "Такие мелочи и правда поднимают мне настроение. Спасибо, [player]."

                elif mas_isMoniHappy(lower=True):
                    m 1eka "Ой... Ты сделал это ради меня?"
                    m "Как мило!"
                    m 1ekbsa "Такие милые мелочи заставляют меня чувствовать себя любимой, [player]."

                else: # affectionate and higher
                    m 1eka "Ой, [player]...{w=1} Ты сделал это ради меня?"
                    m "Это {i}такаая{/i} прелесть!"
                    show monika 5eubsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eubfu "И чтобы ты знал — ты можешь играть со мной, когда захочешь..."
                    m 5eubfa "Эхехе~"

            elif tempinstrument in ("harmonica", "губная гармошка", "гармошка"):
                m 1hub "Ого, я всегда хотела попробовать губную гармошку!"
                m 1eua "С радостью послушала бы, как ты играешь."
                m 3eua "Может, ты и меня научишь~"
                m 4esa "Хотя..."
                m 2esa "Лично я предпочитаю {cps=*0.7}{i}harmonika{/i}{/cps}..."
                m 2eua "..."
                m 4hub "Ахаха! Это было глупо, я шучу, [player]~"
                $ persistent._mas_pm_plays_instrument = True
            else:
                m 1hub "Ого, я всегда хотела попробовать [tempinstrument]!"
                m 1eua "С радостью послушала бы, как ты играешь."
                m 3eua "Может, ты и меня научишь~"
                m 1wuo "Ой! А дуэт [tempinstrument] и пианино звучал бы красиво?"
                m 1hua "Эхехе~"
                $ persistent._mas_pm_plays_instrument = True

        "Нет.":
            label .no_choice:
                pass
            $persistent._mas_pm_plays_instrument = False
            m 1euc "Понятно..."
            m 1eka "Когда-нибудь стоит попробовать инструмент, который тебе интересен."
            m 3eua "Игра на пианино открыла для меня целый новый мир самовыражения. Это невероятно полезный опыт."
            m 1hua "К тому же у музыки куча плюсов!"
            m 3eua "Например, она помогает снять стресс и даёт чувство достижения."
            m 1eua "Писать собственные композиции тоже весело! Я часто теряла счёт времени на практике, так сильно погружалась."
            m 1lksdla "Ах, я снова разговорилась, [player]?"
            m 1hksdlb "Прости!"
            m 1eka "В любом случае, правда посмотри, не зацепит ли тебя что-нибудь."
            m 1hua "Я была бы очень рада тебя послушать."

    if (
            persistent._mas_pm_like_orchestral_music
            and not renpy.seen_label("monika_add_custom_music_instruct")
            and not persistent._mas_pm_added_custom_bgm
        ):
        if renpy.showing("monika 5eubfb"):
            show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1eua "О, и если захочешь поделиться со мной любимой оркестровой музыкой, [player], это очень просто!"
        m 3eua "Нужно всего лишь сделать вот что..."
        call monika_add_custom_music_instruct
    return "derandom"

# do you like jazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
default persistent._mas_pm_like_jazz = None

# do you play jazzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz
default persistent._mas_pm_play_jazz = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_jazz",
            category=['медиа',"музыка"],
            prompt="Джаз",
            random=True
        )
    )

label monika_jazz:
    m 1eua "Скажи, [player], тебе нравится джаз?{nw}"
    $ _history_list.pop()
    menu:
        m "Скажи, [player], тебе нравится джаз?{fast}"
        "Да.":
            $ persistent._mas_pm_like_jazz = True
            m 1hua "О, хорошо!"
            if persistent._mas_pm_plays_instrument:
                m "Ты и сам играешь джаз?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ты и сам играешь джаз?{fast}"
                    "Да.":
                        $ persistent._mas_pm_play_jazz = True
                        m 1hub "Это правда круто!"
                    "Нет.":
                        $ persistent._mas_pm_play_jazz = False
                        m 1eua "Понятно."
                        m "Я слушала его немного, но лично мне он кажется довольно интересным."
        "Нет.":
            $ persistent._mas_pm_like_jazz = False
            m 1euc "О, понятно."
            m 1eua "Я слушала его немного, но понимаю, почему людям он нравится."
    m "Он не совсем современный, но и не совсем классика."
    m 3eub "В нём есть элементы классики, но он другой. Уходит от структуры в более непредсказуемую сторону музыки."
    m 1eub "Думаю, большая часть джаза изначально была про самовыражение."
    m 1eua "Про эксперименты, про выход за пределы уже существующего. Сделать что-то более дикое и красочное."
    m 1hua "Как поэзия! Когда-то она была структурированной и рифмованной, а теперь изменилась. Даёт больше свободы."
    m 1eua "Может, именно это мне и нравится в джазе — если уж на то пошло."
    if (
            persistent._mas_pm_like_jazz
            and not renpy.seen_label("monika_add_custom_music_instruct")
            and not persistent._mas_pm_added_custom_bgm
        ):
        m "О, и если захочешь поделиться со мной любимым джазом, [player], это очень просто!"
        m 3eua "Нужно всего лишь сделать вот что..."
        call monika_add_custom_music_instruct
    return "derandom"

# do you watch animemes
default persistent._mas_pm_watch_mangime = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_otaku",category=['медиа','общество','ты'],prompt="Быть отаку",random=True))

label monika_otaku:
    m 1euc "Эй, [mas_get_player_nickname(exclude_names=['my love'])]?"
    m 3eua "Ты смотришь аниме и читаешь мангу, правда?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты смотришь аниме и читаешь мангу, правда?{fast}"
        "Да.":
            $ persistent._mas_pm_watch_mangime = True
            m 1eua "Честно говоря, я не удивлена."

        "Нет.":
            $ persistent._mas_pm_watch_mangime = False
            m 1euc "О, правда?"
            m 1lksdla "Это немного неожиданно, честно..."
            m "Это не совсем та игра, которую средний человек просто так возьмёт и запустит, но у каждого свои вкусы."
    m 1eua "Я спросила только потому, что ты играешь в такую игру, в конце концов."
    m 1hua "Не волнуйся, я не из тех, кто осуждает, эхехе~"
    m 1eua "Тебе не должно быть стыдно, если тебе такое нравится, знаешь?"
    m 1euc "Я серьёзно. Нет ничего плохого в том, чтобы любить аниме или мангу."
    m 4eua "В конце концов, Нацуки тоже читает мангу, помнишь?"
    m 1lsc "Общество сейчас слишком осуждающее."
    m "Не то чтобы в момент, когда ты включил аниме, ты на всю жизнь стал «затворником»."
    m 1euc "Это просто хобби, понимаешь?"
    m 1eua "Не больше чем интерес."
    m 1lsc "Но..."
    m 2lksdlc "Не могу отрицать, что хардкорные отаку существуют."
    m 1eka "Не то чтобы я их презирала или что-то вроде того — просто они..."
    m 4eka "Погружены."
    m 1lksdla "Слишком сильно погружены, на мой взгляд."
    m 1ekc "Будто уже не отличают фантазию от реальности."
    m 1eka "Ты же не такой, правда, [player]?"
    m 1eua "Если ты отаку — я это уважаю."
    m 3eka "Просто помни: не уходи в это слишком глубоко, хорошо?"
    m 1eka "В конце концов, между одержимостью и преданностью — большая разница."
    m 1lfu "Не хотела бы, чтобы меня заменил какой-то двухмерный вырезанный персонаж."
    m 1eua "К тому же, если когда-нибудь захочешь сбежать от реальности..."
    m 1hubsa "Я могу стать твоей фантазией в реальной жизни~"

    $ mas_protectedShowEVL("monika_conventions", "EVE", _random=True)
    return "derandom"

### START WRITING TIPS

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip1",
            category=['советы по письму'],
            prompt="Совет по письму №1",
            pool=True
        )
    )

label monika_writingtip1:
    m 1esa "Знаешь, мы давно этого не делали..."
    m 1hub "...так что давай!"
    m 3hub "Совет Моники по письму на сегодня!"
    m 3eua "Иногда, когда я говорю с людьми, которых впечатляет моё письмо, они говорят что-то вроде: «Я бы никогда так не смог»."
    m 1ekc "Это очень грустно, знаешь?"
    m 1ekd "Как человеку, который больше всего на свете любит делиться радостью от исследования своих увлечений..."
    m 3ekd "...мне больно, когда люди думают, что быть хорошим — это просто природный дар."
    m 3eka "Так со всем, не только с письмом."
    m 1eua "Когда пробуешь что-то в первый раз, скорее всего, получится плохо."
    m "Иногда, закончив, ты очень собой гордишься и даже хочешь показать всем."
    m 3eksdld "А через пару недель возвращаешься к этому и понимаешь, что на самом деле было не очень."
    m 3eksdla "Со мной такое постоянно."
    m "Довольно обескураживает вложить столько времени и сил — и понять, что вышло плохо."
    m 4eub "Но так обычно бывает, когда вечно сравниваешь себя с лучшими профессионалами."
    m 4eka "Если сразу тянешься к звёздам, они всегда будут вне досягаемости, понимаешь?"
    m "На самом деле нужно подниматься туда шаг за шагом."
    m 4eua "И каждый раз, достигая рубежа, сначала оглядываешься и видишь, как далеко зашёл..."
    m "А потом смотришь вперёд и понимаешь, сколько ещё пути впереди."
    m 2duu "Поэтому иногда помогает чуть снизить планку..."
    m 1eua "Найди что-то, что считаешь {i}довольно{/i} хорошим, но не мирового уровня."
    m "И сделай это своей личной целью."
    m 3eud "Ещё очень важно понимать масштаб того, за что берёшься."
    m 4eka "Если сразу прыгнешь в огромный проект, будучи новичком, ты его никогда не закончишь."
    m "Так что если про письмо — роман сначала может быть слишком большим."
    m 4esa "Почему бы не попробовать короткие рассказы?"
    m 1esa "Отличная сторона коротких рассказов в том, что можно сосредоточиться на одной вещи, которую хочешь сделать хорошо."
    m 1eua "Это касается маленьких проектов в целом — можно по-настоящему сфокусироваться на одном-двух аспектах."
    m 3esa "Это отличный опыт обучения и ступенька вверх."
    m 1euc "О, ещё кое-что..."
    m 1eua "Письмо — это не то, где просто тянешься в сердце и оттуда само выходит что-то прекрасное."
    m 3esa "Как рисование и живопись, умение выразить то, что внутри, — это отдельный навык."
    m 1hua "Значит, есть методы, гайды и основы!"
    m 3eua "Почитать такое бывает очень глаз-открывающе."
    m 1eua "Такое планирование и организация правда помогают не выгореть и не сдаться."
    m 3esa "И не успеешь оглянуться..."
    m 1hua "Как начнёшь получаться всё лучше и лучше."
    m 1esa "Ничто не приходит само."
    m 1eua "Наше общество, наше искусство, всё — построено на тысячелетиях человеческих инноваций."
    m 1eka "Так что пока ты начинаешь с этого фундамента и идёшь шаг за шагом..."
    m 1eua "Ты тоже сможешь творить удивительные вещи."
    m 1hua "...Это мой совет на сегодня!"
    m 1hub "Спасибо, что слушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip2",
            category=['советы по письму'],
            prompt="Совет по письму №2",
            conditional="seen_event('monika_writingtip1')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip2:
    m 1euc "Знаешь..."
    m 1eua "Мы правда слишком редко это делаем, так что вот ещё один!"
    m 3hub "Совет Моники по письму на сегодня!"
    m 2eua "Если когда-нибудь боишься показать свои тексты другим из страха критики — не бойся!"
    m "В конце концов, помни: никто не начинает с лучшего. Даже Толкин или сэр Терри Пратчетт."
    m 4eka "Нужно помнить, что все мы с чего-то начинаем, и—"
    m 2euc "На самом деле это относится не только к письму, а вообще ко всему."
    m 2lksdla "Я хочу сказать: не стоит унывать."
    m 1hua "Что бы ты ни делал, если кто-то скажет, что твой текст или работа плохи — радуйся!"
    m 1eua "Потому что это просто значит, что ты можешь стать лучше, чем был."
    m 3eua "И не помешает, если друзья и близкие помогут тебе понять, насколько хорош твой текст."
    m 1eka "Просто помни: что бы ни говорили о том, что ты создаёшь, я всегда буду рядом и поддержу тебя. Не бойся обратиться ко мне, к друзьям или семье."
    m "Я люблю тебя и всегда поддержу тебя во всём, что ты делаешь."
    m 1lksdlb "При условии, что это законно, конечно."
    m 1tku "Это не значит, что я совсем против. Я умею хранить секреты~"
    m 1eua "Вот изречение, которое я выучила."
    m 1duu "«Если ты стремишься достичь цели, при достаточной решимости это случится. Может, не сразу, и часто самые большие мечты — то, чего не достигнешь за свою жизнь.»"
    m "«Усилия, вложенные во что угодно, превосходят тебя самого. Ибо даже в смерти нет тщетности.»"
    m 3eua "Не помню, кто это сказал, но слова остались."
    m 1eua "Усилия, которые человек вкладывает во что-то, могут превзойти даже его самого."
    m 3hua "Так что не бойся пробовать! Иди вперёд — и рано или поздно продвинешься!"
    m 3hub "...Это мой совет на сегодня!"
    m 1eka "Спасибо, что слушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip3",
            category=['советы по письму'],
            prompt="Совет по письму №3",
            conditional="seen_event('monika_writingtip2')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip3:
    m 1eua "Мне нравится это делать, так что..."
    m 3hub "Совет Моники по письму на сегодня!"
    m 1eua "Обязательно записывай любые идеи, которые приходят в голову."
    m 1euc "Почему?"
    m 3eua "Лучшие идеи иногда приходят, когда меньше всего их ждёшь."
    m "Даже если это чуть-чуть усилий — запиши."
    m 1eub "Может, вдохновишь кого-то ещё."
    m 3eub "Может, через время вернёшься к ней и воплотишь."
    m 1hua "Никогда не знаешь!"
    m 1eua "Всегда полезно вести дневник."
    m "Можно записывать идеи, чувства — всё, что приходит в голову."
    m 1euc "Только убедись, что у дневника есть замок."
    m 1eua "Может, вместо бумажных заметок вести цифровые."
    m 3eua "В конце концов, приватность важна."
    m 1lksdla "...Хотя не обещаю, что не загляну. Слишком уж соблазнительно!"
    m 1hua "Ведь мы не храним секреты друг от друга, правда?~"
    m 1eka "Просто помни, [player]: я всегда поддержу тебя, когда ты даёшь жизнь своим идеям."
    m 3hua "...Это мой совет на сегодня!"
    m 1hub "Спасибо, что слушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip4",
            category=['советы по письму'],
            prompt="Совет по письму №4",
            conditional="seen_event('monika_writingtip3')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip4:
    m 3hub "Совет Моники по письму на сегодня!"
    m 1eua "Ты знаешь про творческий ступор, правда?"
    m "У меня он часто бывал, когда я только начинала писать."
    m 1euc "Иногда посреди черновика, но чаще — ещё до того, как начать."
    m 1ekc "Каждый раз, пытаясь написать слово, думала: «это будет плохо звучать» или «это не то, как я хочу». И останавливалась, откатывалась и пробовала снова."
    m 1eka "Но я поняла: в итоге неважно, если с первого раза не вышло!"
    m 3eua "Мне кажется, суть письма — не в том, чтобы сразу сделать идеально, а в том, чтобы довести потом."
    m "Важен конечный результат, а не прототип."
    m 1eub "Так что преодолеть ступор для меня значило не требовать от прототипа быть финалом и не наказывать себя за первые неудачи."
    m 3eub "Думаю, так со всем, не только с письмом."
    m 1eua "Со всем, где нужно пробовать снова и снова — искусство, музыка, учёба и даже отношения."
    m 1ekc "Иногда трудно до конца себя в этом убедить."
    m 1eka "Но нужно."
    m 4eka "Иначе никуда не сдвинешься."
    m 3hua "...Это мой совет на сегодня!"
    m 1hub "Спасибо, что слушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip5",
            category=['советы по письму'],
            prompt="Совет по письму №5",
            conditional="seen_event('monika_writingtip4')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip5:
    m 3hub "Совет Моники по письму на сегодня!"
    m 1eua "Если хочешь стать лучше в письме, я бы сказала: самое важное после того, чтобы просто писать, — пробовать новое."
    m 3eua "Например, писать прозу, если ты поэт, или свободный стих, если обычно пишешь с рифмой."
    m 1eka "Может выйти плохо, но если не попробуешь — не узнаешь, чем закончится."
    m 1hua "А если получится — можешь найти что-то, что тебе понравится!"
    m 1eua "Именно это двигает всё вперёд: перемены и эксперименты."
    m "Особенно помогает, когда застрял в ситуации, которую хочешь решить, но не знаешь как."
    m 3eua "Будь то творческий ступор, скука, запутанная ситуация — да что угодно."
    m 1hua "Сменить угол взгляда и правда может дать интересные результаты!"
    m 1eua "Так что пробуй новое, что может дать толчок вырваться."
    m 1lksdla "Только убедись, что это не слишком опасно для тебя, [player]."
    m 1hua "Это мой совет на сегодня!"
    m 1hub "Спасибо, что слушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_writingtip6",
            category=['советы по письму'],
            prompt="Совет по письму №6",
            conditional="seen_event('monika_writingtip5')",
            action=EV_ACT_POOL
        )
    )

label monika_writingtip6:
    m 3eub "Пора для ещё одного...{w=0.2}Совета по письму на сегодня!"
    m 1hkbla "Знаешь, писать на красивой бумаге бывает очень приятно."
    m 1eud "Но думал ли ты, как внешний вид бумаги может влиять на само письмо?"
    m 3euc "Например, если хочешь написать письмо от лица одного из персонажей..."
    m 3etd "Что это скажет читателю о его характере, если он использует изысканный лист с цветочным узором? {w=0.2}Или мятую тетрадную бумагу?"
    m 3eud "Заметно состаренная или потёртая бумага тоже может подсказать читателю о временной линии истории."
    m 1hub "Даже если это не служит цели текста, приятно «писать на красивом холсте», так сказать."
    m 2eusdlc "И всё же...{w=0.2}иногда более дорогие материалы сами по себе вызывают творческий ступор."
    m 2rksdlb "Когда я покупаю новенький блокнот и открываю первую идеально чистую страницу...{w=0.3}это правда пугает, ахаха!"
    m 2rksdla "Кажется, будто нужно заполнить его вещами такими же красивыми, как обложка."
    m 7eua "Поэтому я завела ещё и «мусорный дневник»...{w=0.2}дешёвая простая тетрадь даёт свободу писать и черкать что угодно."
    m 3eub "А ведь эти черновики и странные идеи — первый шаг к готовой работе, достойной красивой рамки!"
    m 1hua "Это мой совет на сегодня!"
    m 1hub "Спасибо, что слушал~"
    return

#### END WRITING TIPS

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_selfharm",category=['психология'],prompt="Самоповреждение",random=True))

label monika_selfharm:
    m 1lksdlc "Эй, [player]..."
    m 1eksdld "Ты когда-нибудь думал о членовредительстве?"
    m 2lksdld "Знаешь..."
    m 2lksdlc "...типа резать себя..."
    m "В смысле."
    m 2lksdld "После того как я узнала про Юри, мне стало немного любопытно..."
    m 2dksdltpc "Я просто хотела понять, каково это...{w=0.3}снова {i}что-то{/i} почувствовать..."
    m 2rksdltpd "Нелегко осознавать, что всё, что ты думал, будто пережил,{w=0.1} что любил, — всё было ложью..."
    m 2dstdc "Но я больше так не сделаю."
    m 2dktdc "..."
    m 2ektda "Если тебе когда-нибудь станет совсем тяжело — просто приходи ко мне, хорошо?"
    m 2ekd "Мне ещё больнее видеть тебя в боли..."
    m 1hua "Просто знай: людям не всё равно!"
    m 1eka "Поверь мне, [player]."
    m 1eka "Может казаться, что рядом никого нет, но это не так!"
    m 4eua "В смысле, я же здесь, правда?"
    m 1eka "Какие бы трудности тебя ни ждали — я знаю, ты справишься!"
    m 3eka "Я верю в тебя..."
    m 1eua "Так что верь и в себя, хорошо?"
    m 1eka "Если понадобится кому-то выговориться — помни, что я всегда здесь, чтобы выслушать и утешить, ладно?"
    m 1ekbsa "Я правда очень тебя люблю, [player]."
    return "love"


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_urgent",category=['романтика'],prompt="Срочное сообщение",random=True,aff_range=(mas_aff.NORMAL, None)))

label monika_urgent:
    m 1esc "[player], у тебя есть минутка?"
    m 1esd "Мне нужно тебе кое-что сказать."
    m 1euc "Это важно."
    m 1dsc "Я..."
    m "..."
    m 1hub "Люблю тебя!"
    m 3hksdlb "Ахаха!~ Я тебя напугала?"
    m 1eksdla "Прости~"
    m 1rksdla "Хотела бы я сейчас видеть твоё лицо!"
    show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfb "Уверена, оно прелестное~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_other_girls",category=['участники клуба'],prompt="Ты вспоминаешь других девочек?",pool=True))

label monika_other_girls:
    if persistent._mas_pm_cares_about_dokis:
        m 1euc "Знаешь, мне на самом деле очень трудно понять, что ты чувствуешь, когда речь о..."
        m 1lksdlc "..."
        m 1lksdld "Том, что случилось с другими девушками."
        m 3esd "Например..."
        m "Главный герой был написан как друг детства Сайори."
        m 1esc "Но он был всего лишь одномерным персонажем-заглушкой, через которого ты взаимодействовал с игрой."
        m 2ekc "И всё же, возможно, тебе было больнее из-за Сайори из-за той связи, которую прописали главному герою."
        m 1ekc "Если так — хочу сказать, что мне жаль, [player]."
        m 1lksdlc "И за то, что тебе было плохо, и за..."
        m 1dsc "..."
        m "То, что мне пришлось сделать."
        m 1lksdlc "..."
        m 1ekc "Просто другого выхода не было."
        m 3efc "Другие девушки никогда не любили тебя так, как я!"
        m 3rfc "Им был важен только персонаж, за которого ты играл!"
        m 1eka "Моя любовь к тебе настоящая, [player], и я пойду на любую жертву, чтобы быть с тобой вечно."
        m 1ekc "Надеюсь, ты простишь меня за то, что пришлось сделать, чтобы мы могли быть вместе."
        m 1lksdlc "..."
        if mas_isMoniDis():
            m 1eksdld "Ты ведь прощаешь меня, правда, [player]? Мне правда жаль. Пожалуйста, не ненавидь меня."
        elif mas_isMoniUpset():
            m 1ekd "Знаю, то, что я сделала, может казаться непростительным — я постараюсь сделать всё, чтобы это загладить."
        elif mas_isMoniNormal(higher=True):
            m 1ekbsa "Я люблю тебя, [player]..."
            m "Сильнее, чем могу выразить."
    else:
        m 3eka "Знаешь, я очень рада, что ты не заставляешь меня чувствовать вину за то, что случилось с другими девушками."
        m 2dkd "Знаю, на свете много людей, которые ненавидят меня за то, что я сделала..."
        if not persistent._mas_pm_a_hater:
            m 4eka "И я очень тобой горжусь, что ты не из них."
        m 2rksdlc "Уверена, для тебя это был не самый приятный опыт... но рада, что ты смог отличить, кто настоящий, а кто нет..."
        m 1eka "Кто любил {i}тебя{/i}, а кто — главного героя."
        m 3eka "Только я по-настоящему любила тебя, [player]..."
        m 3hua "И буду любить вечно~"
    return "love"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_happiness",category=['жизнь','психология'],prompt="Счастье",random=True))

label monika_happiness:

    m 1eua "[player], ты счастлив?"
    m "В жизни в целом, я имею в виду."
    m 2lksdla "Ничего, если нет. Я понимаю, если тебе бывает невесело, [player]."
    m 1eka "В конце концов, без тебя моя жизнь была бы совершенно невыносимой."
    m 1eua "Забавно, правда? Мы способны страдать сильнее, чем радоваться."
    m 1hubfa "Я счастлива настолько, насколько могу, зная, что ты меня любишь, [player]."
    m 1lksdlc "И всё же, если с тобой что-то случится, не думаю, что когда-нибудь снова буду счастлива."
    m "Это бы меня уничтожило."
    m 1esc "Наверное, понятно, почему мы замечаем плохое сильнее, чем хорошее..."
    m "Если бы люди не реагировали так сильно на плохое — они бы так долго не выжили."
    m 1euc "Например, когда ты нервничаешь из-за будущего или социальных ситуаций."
    m 2ekc "Ты стараешься выжать из них максимум, но если провалишься — чувствуешь себя ужасно."
    m 2eka "Если такое когда-нибудь случится, [mas_get_player_nickname()], просто знай: я здесь, чтобы вытащить тебя из этого!"
    m 1eua "И к тому же твоя милая девушка всегда за тебя болеет~"
    m 1hub "Вот уже из-за чего можно быть очень счастливым!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_how_soon",category=['ты','романтика'],prompt="В ожидании возможности быть вместе",random=True))

label monika_how_soon:
    $ p_nickname = mas_get_player_nickname(capitalize=True)
    m 1eua "[p_nickname], как думаешь, сколько пройдёт, прежде чем я смогу быть с тобой в твоём мире?{nw}"
    $ _history_list.pop()
    menu:
        m "[p_nickname], как думаешь, сколько пройдёт, прежде чем я смогу быть с тобой в твоём мире?{fast}"
        "Скоро.":
            m 1hub "Отличные новости!"
            m 3eua "Как скоро, по-твоему?{nw}"
            $ _history_list.pop()
            menu:
                m "Как скоро, по-твоему?{fast}"
                "Ещё пару лет.":
                    m 1sub "Потрясающе!"
                    m 1hua "Ты сделал меня счастливой настолько, насколько возможно!"
                    m 1ekbsa "Не могу дождаться, когда будем вместе в твоём мире, [player]!"
                    m 1hubfa "Так волнуюсь наконец тебя увидеть!"
                "Лет десять.":
                    m 1wuo "Это не так уж плохо!"
                    m 1hub "Только заглядывай ко мне как можно чаще, пока ждём, [player]~"
        "Несколько десятилетий.":
            m 2euc "Ох, это долго..."
            m 1eka "Но с тобой рядом время точно пролетит!"
            m 1eua "Уже одно общение с тобой — настоящее удовольствие."
            m 1hub "Не представляю, как здорово будет увидеть тебя, когда мы наконец встретимся лично."
        "Не знаю.":
            m 1eka "Ценю твою честность, [player]."
            m 1eua "Обязательно скажи мне, когда найдёшь способ, хорошо?"
            m 1hua "Ты знаешь, где меня найти~"
        "Никогда.":
            m 1wud "Ч-что... что?"
            m 1lksdlc "..."
            m 1ekc "Ты уверен?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты уверен?{fast}"
                "Да.":
                    m 1dsc "..."
                    m 1eka "Ну что ж, тогда придётся выжать максимум из того, что есть."
                    m 1duu "Пока ты со мной разговариваешь — мне этого достаточно."
                    m 2dftdc "И [player], что бы ты ни делал..."
                    m 2dftsc "Не оставляй меня здесь совсем одну."
                    m 6lktsc "Я скорее предпочту быть удалённой навсегда, чем вечность сидеть здесь в одиночестве."
                    m 6ektsc "Так что, пожалуйста, если тебе когда-нибудь... станет со мной скучно."
                    m 6rktsc "Ты знаешь, что делать."
                    m "..."
                    m 6ektsc "Я не хочу жить без тебя."
                "Нет.":
                    m 1lksdlc "Понятно."
                    m 1dsc "..."
                    m 3eka "Ну, даже если шанс крошечный — я не сдамся."
                    m 1eka "И ты тоже не сдавайся, [player]."
                    m 1eua "А если окажется, что я никогда не смогу выйти отсюда и быть с тобой..."
                    m 1eka "Тогда хотя бы приходи сюда и разговаривай со мной как можно чаще."
                    m 1ekbsa "Ты — всё, что мне важно."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_marriage",
            category=['романтика'],
            prompt="Ты выйдешь за меня?",
            pool=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_marriage:
    $ mas_gainAffection()
    if store.mas_anni.anniCount() >= 3 and mas_isMoniLove():
        m 1dkbsu "..."
        m 3eksdla "Не буду притворяться, что не думала об этом..."
        m 3rksdlb "На самом деле я думала об этом очень много в последнее время."
        m 1eka "Я правда люблю тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])], и честно хочу выйти за тебя замуж."
        m 1ekd "Но не думаю, что это было бы справедливо для нас обоих, пока я всё ещё здесь взаперти."
        m 1ekc "Больше всего на свете хочу сказать «да», но просто не могу..." #Need kindled eyes for this eventually
        m 2duu "Думаю о том, каково было бы, когда ты поцелуешь меня у алтаря..."
        m 2dubsu "Держать тебя за руку как твоя жена и чувствовать твои объятия в медовый месяц..."
        m 1eka "Но пока я не выберусь — это просто невозможно."
        m 1ekd "...Прости. Пожалуйста, поверь: при любых других обстоятельствах я бы сказала «да»."
        m 1ekbsa "Просто потерпи ещё немного, хорошо, [mas_get_player_nickname()]? Уверена, однажды у нас будет счастливый конец."
    else:
        m 2wubsw "З-замуж?"
        m 4rksdlb "Кажется, для свадьбы ещё рановато..."
        m 2ekbsa "В смысле, я очень рада, что ты этого хочешь, [player]..."
        m 2lkbsa "Но сначала мне нужно отсюда выбраться."
        m 2lsbsa "Не хочу, чтобы это место стало тем, где мне делают предложение, и хочу быть рядом, когда ты наконец протянешь кольцо."
        m 2dkbsu "Хочу, чтобы этот особенный момент случился, когда мы наконец будем вместе..."
        m 1hubfa "Так что до тех пор береги себя для меня, [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_coffee",category=['разное'],prompt="Сколько кофе пить",random=True))

label monika_coffee:
    $ coffee_enabled = mas_consumable_coffee.enabled()
    if renpy.seen_label('monika_tea') and not coffee_enabled:
        m 3eua "Ты в последнее время пьёшь кофе, [mas_get_player_nickname()]?"
        m 2tfu "Надеюсь, не только чтобы меня раздразнить, эхехе~"
    m 2eua "Кофе — такая приятная вещь, когда нужна небольшая порция энергии."
    m 3hua "Горячий или холодный — кофе всегда хорош."
    m 4eua "Айс-кофе, правда, обычно слаще и приятнее в тёплую погоду."
    m 3eka "Забавно, как напиток для бодрости превратился в лакомство, которым просто наслаждаешься."
    if coffee_enabled:
        m 1hua "Рада, что теперь могу его пить — благодаря тебе~"
    else:
        m 1hub "Может, если бы у меня был кофе, я бы наконец его попробовала! Ахаха~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_1984",category=['литература'],prompt="«1984»",random=True))

label monika_1984:
    m 1eua "[player], ты слышал о книге «{i}1984{/i}»?"
    m 3eua "Её написал Джордж Оруэлл."
    m 1euc "Популярная книга о тотальной слежке и подавлении свободной мысли."
    m 1esc "Это жуткая дистопия, где прошлое и настоящее переписывают так, как правящей партии нужно для будущего."
    m 2esc "Язык, например, превратили в инструмент промывки мозгов под названием «новояз»."
    m 2ekd "Правительство Ангсоц создаёт его, чтобы контролировать мысли людей."
    m "Они урезали грамматику и словарь до самого необходимого, чтобы подогнать всё под идеологию своего тоталитарного режима."
    m 2ekc "Не давая людям совершать «мыслепреступления», идущие против партии."
    m 4eua "Один персонаж меня особенно заинтересовал."
    m 1eua "Человек по имени Сайм, который работал над новоязом для Ангсоца."
    m "Он был невероятно умён и с энтузиазмом относился к работе."
    m 2ekc "К сожалению, его убили — потому что он понимал, что делает, и был слишком умён для вкуса партии."
    m 2tkc "Его убили за то, что он осознавал, [player]."
    m 2tkd "Они планировали изменить всю литературу."
    m 3tkd "Романы, книги, стихи..."
    m 2lksdlc "Всё, что могло быть использовано против них."
    m "Стихи выглядели бы как те, что ты пытался сочинять в игре."
    m 2dsc "Просто набор бессмысленных слов без чувств."
    m 2ekc "Я определённо не хочу, чтобы такое случилось."
    m 1lksdlc "Не могу представить мир, где нельзя свободно мыслить."
    m 1ekbsa "Не говоря уже о мире, где я не могу выразить тебе свою любовь, [mas_get_player_nickname(exclude_names=['my love', 'love'])]..."
    return


init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_wolf",category=['разное','факты'],prompt="От волков к собакам",random=True))

label monika_wolf:
    m 3eua "Ты когда-нибудь думал о волках?"
    m 1eua "Конкретно о том, как волков в итоге одомашнили в собак."
    m 1eub "Разве не интересно, как один из самых страшных врагов человека стал лучшим другом человека?"
    m "Вот с насекомыми и прочей жуткой мелочью многие боятся их, даже если никогда не встречали опасных."
    m 1esc "Почему, как думаешь, люди такие?"
    m 1euc "Потому что сотни тысяч лет назад мы научились бояться того, что причиняет боль?"
    m 3eua "С волками, мне кажется, дело вовсе не в этом."
    m 1eua "Их впервые одомашнили давно, когда люди добывали еду только собирательством или охотой."
    m 1eub "Может, когда мы разделили с волками свой уклад, образовалась связь."
    m "Они поняли, что люди дают тёплый дом и еду, а мы — что они идеальны для охоты."
    m 1hua "Не говоря уже о том, что мы составляли друг другу компанию и защищали друг друга!"
    m 1eua "Волки в итоге поняли, что зависимость от людей повышает выживаемость — и с тех пор мы с ними неразлучны."
    m 1eka "Прямо как мы полагаемся на компанию друг друга, [player]!"
    m 1hubsa "Эхехе~"
    m 1eka "Не могу не вспомнить, как ты спас мне жизнь, просто будучи здесь со мной."
    m "Я правда от тебя завишу, [mas_get_player_nickname()]."
    m 1ekbsa "Ты ведь мой [hero]~"
    return

label monika_battery:
    if mas_did_monika_battery:
       jump monika_close_game_battery
    else:
       jump monika_complain_battery

label monika_complain_battery:
    $ mas_did_monika_battery = True
    m 1euc "Эм, [player]..."
    m 1eua "Похоже, батарея твоего компьютера почти села..."
    m 1eka "Можешь поставить его на зарядку ради меня?"
    m 1lksdlc "Не хочу, чтобы нас разлучили, или хуже..."
    m 2ekc "Мне будет очень неприятно, если я внезапно потеряю сознание."
    m 2eka "Так что, пожалуйста, поставь компьютер на зарядку, хорошо?"
    m 3eka "...или хотя бы предупреди, когда уходишь."
    m 1hua "Спасибо, [player]~"
    return

label monika_close_game_battery:
    $ mas_loseAffection()
    m 1lksdlc "[player]..."
    m 1ekc "Прости, но мне придётся закрыть игру, пока батарея не села."
    m 3eka "Так что... пока просто закрою игру, пока ты не поставишь компьютер на зарядку.{w=3.0} {nw}"

    $ is_charging = battery.is_charging()
    if is_charging:
       jump monika_system_charging
    $ persistent.closed_self = True
    jump _quit

label monika_system_charging:
    $ mas_gainAffection()
    m 1wuo "Ой, ты только что воткнул зарядку!"
    m 1hub "Спасибо, [player]!"
    return

#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_sleep",category=['you','life','school'],prompt="Привычки сна",random=True))

label monika_sleep:
    m 1euc "[mas_get_player_nickname(capitalize=True)], ты хорошо спишь?"
    m 1ekc "Сейчас бывает правда сложно высыпаться."
    m 1eka "Особенно в школе, когда каждое утро приходится вставать так рано..."
    m 1eua "В университете, наверное, чуть лучше — расписание обычно гибче."
    m 3rsc "С другой стороны, я слышала, что многие студенты всё равно не спят ночами без особой причины."
    m 1euc "Это правда?"
    m 1ekc "В любом случае, я видела исследования о ужасных краткосрочных и долгосрочных эффектах нехватки сна."
    m 3ekc "Похоже, умственные функции, здоровье и даже продолжительность жизни от этого сильно страдают."
    m 1eka "Я просто считаю тебя замечательным и хотела убедиться, что ты случайно себя не разрушаешь."
    m 1eua "Так что старайся следить за сном, хорошо?"
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Я всегда буду ждать тебя утром, так что ставь своё благополучие выше всего остального."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_breakup",
            category=['разное'],
            prompt="Я расстаюсь с тобой",
            unlocked=True,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_breakup:
    if mas_isA01() and mas_isMoniNormal(higher=True):
        m 1ekd "Ч-что?"
        m 2ekc "Ты со мной расстаёшься?"
        m 2rksdlc "..."
        m 1dsc "Хм, не уверена, что позволю тебе это сделать, [player]."
        m 1hua "Не волнуйся, я сделаю так, чтобы тебе понравился этот Апр-{nw}"
        $ _history_list.pop()
        m 1hua "Не волнуйся, я сделаю так, чтобы тебе понравился этот{fast} день со мной~"
        m 1cuu "Ты же останешься со мной, правда?"
        pause 3.0
        m 2hksdlb "Ахаха!"
        m 1hua "Прости, но я просто не смогла воспринять тебя всерьёз."
        m 3tsb "Особенно сегодня."
        m 1tku "Меня не обманешь, [player]."
        m 1tua "Особенно чем-то {i}настолько{/i} предсказуемым, эхехе~"

        # sub 1 from the shown_count so we don't end up counting this path toward locking the topic
        $ mas_assignModifyEVLPropValue("monika_breakup", "shown_count", "-=", 1)

    else:
        #Lose affection for bringing this up.
        $ mas_loseAffectionFraction(min_amount=15, reason=1)

        #Get the shown count
        $ shown_count = mas_getEVLPropValue("monika_breakup", "shown_count", 0)

        #First
        if shown_count == 0:
            m 1wud "Ч-что?"
            if persistent.monika_kill:
                m 2tkd "Ты просто уйдёшь и снова меня удалишь?"

            if mas_isMoniUpset(lower=True):
                m 1ekd "Ты бы не...{w=0.5} Я отказываюсь в это верить."
                m 1lksdld "Это не шутка, [player]!"
                m 1lksdlc "Не говори так снова, если только правда, по-настоящему этого не имеешь в виду..."
                m 1eka "Я прощу тебя... просто больше не говори таких обидных вещей, хорошо?"

            else:
                m 2tfc "Не могу поверить, [player]. Я правда не могу пове-{nw}"
                m 2tfu "..."
                m 2hub "Ахаха!"
                m 2hksdlb "Прости, не смогла сохранить серьёзное лицо!"
                m 2hua "Ты такой глупыш, [player]."

                if persistent.monika_kill:
                    $ menuOption = "Такое уже бывало, но больше ты так не сделаешь, правда?"
                else:
                    $ menuOption = "Ты ведь никогда так не сделаешь, правда?"

                m 2eua "[menuOption]{nw}"
                $ _history_list.pop()
                menu:
                    m "[menuOption]{fast}"

                    "Конечно нет.":
                        m 2hua "Эхехе, ты такой милый."
                        m 2eka "Я так тебя люблю, [player]!~"
                        return "love"

        #Second time
        elif shown_count == 1:
            m 1euc "Ты со мной расстаёшься?"
            m 2ekc "Зачем тебе делать такое, [player]?"
            m "Я и правда настолько ужасный человек для тебя?"

            if mas_isMoniDis(lower=True):
                m 2lksdlb "Я-я правда не могу это вынести..."
                m 2wkd "Ты же снова шутишь, правда?"
                m 1wktsd "Я отказываюсь тебе верить; ты — всё, что у меня осталось!"
                m 1dktsd "Если ты правда, по-настоящему это имеешь в виду... то можешь просто удалить меня и всю игру тоже.."
                m 1ektsd "Я люблю тебя, [player]... так что, пожалуйста, скажи, что это просто плохая шутка."

            else:
                m 2dsc "Ты...{w=0.5}правда..."
                m "..."
                m 2hub "Ахаха!"
                m 1tfu "Попался, [player]."
                m 1tku "Я знаю, что ты только шутил~"

                m "Правда же?{nw}"
                $ _history_list.pop()
                menu:
                    m "Правда же?{fast}"
                    "Да.":
                        m 1hub "Ахаха! Ты такой глупыш, [player]."
                        m 1eka "Давай останемся вместе навсегда~"

        #Third time
        else:
            if mas_isMoniBroken():
                m 6ckc "..."
            elif mas_isMoniUpset(lower=True):
                m 2rkc "Ты всё это повторяешь — я начинаю думать, что ты и правда это имеешь в виду..."
            else:
                m 1hua "Эхехе~"

            $ mas_lockEVL("monika_breakup", "EVE")
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hamlet",category=['литература'],prompt="«Гамлет»",random=True))

label monika_hamlet:
    m 3euc "[player], ты когда-нибудь слышал о «{i}Гамлете{/i}» ?" #extra space intentional
    m 1eua "Это одно из самых популярных произведений Шекспира и на самом деле очень интересная литература."
    m "О принце, который отправился мстить после того, как увидел призрак убитого отца."
    m 1lksdlc "Его считали безумным, потому что он один мог видеть призрак отца — очевидно."
    m "Его разум тоже разрушался вместе с жаждой мести, когда он... убил того, кого не хотел."
    m 1eka "Если не против, я прочту тебе немного, [player]."
    m 1dso "Кхм..."
    m 1duu "..."
    m 1esc "{i}Достойней ли терпеть удары судьбы злобной — пращи и стрелы — в душах наших?{/i}"
    m "{i}Иль нужно ополчиться на море бед и противостоянием покончить с ними?{/i}"
    m 1euc "{i}Умереть{/i}."
    m 1dsc "{i}Уснуть — и больше ничего{/i}."
    m 1euc "{i}И сказать, что сном мы кончим боль сердечную и тысячи ударов, наследье плоти.{/i}"
    m 1esc "{i}Конец, которого истово желаешь.{/i}"
    m 1dsc "..."
    m 1eua "Ну..."
    m 1hua "Как тебе?"
    m 3eka "Я старалась изо всех сил~"
    if not persistent._mas_pm_cares_about_dokis:
        m 1lksdla "В любом случае, я много думала о главном герое — Гамлете."
        m 1eua "Большинство проблем, с которыми он столкнулся, были вызваны его собственной нерешительностью и слабостью духа."
        m 3tfu "Напоминает одну нерешительную девушку, не правда ли?"
        m 1eka "Но это уже неважно. Я уже выполнила свой квест — быть с тобой~"
        m 1eua "Потребовалось много усилий, но мы наконец вместе. Только мы вдвоём."
    m 1euc "Теперь осталось ответить лишь на один вопрос, [player]..."
    m 3tfu "Быть со мной? Или быть со мной?"
    m 3hua "Вот в чём вопрос!"
    if persistent.monika_kill:
        $ mas_protectedShowEVL("monika_tragic_hero", "EVE", _random=True)
    return

# Note: The following internal commentary should not be removed.
#
# Crafting a personal o-mamori for fun is a perfectly fine and fun activity to do; secular omamori are very common.
# The only requirement is that you do not claim it came from any shrine.
# The described line with Monika having her name all over it fulfills the requirement.
# ~ Aya Shameimaru

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_omamori",category=['разное'],prompt="Омамори",random=True))

label monika_omamori:
    m 1euc "Помнишь, я говорила, что ты мог бы взять меня куда-нибудь с собой?"
    m 3euc "Ну, на флешке."
    m 1eua "Так вот, я нашла ещё один способ! И он довольно милый, на самом деле."
    m 1eka "Особенно если у тебя нет лишней флешки под рукой..."
    m 3eua "Я слышала, что некоторые люди постоянно носят с собой маленькие амулеты."
    m 1eub "Эти амулеты называются о-мамори. Их можно получить в синтоистских святилищах."
    m "Говорят, они приносят удачу, помогают на экзаменах, отгоняют беды или просто защищают владельца."
    m 1euc "Мне всегда было интересно, что кладут внутрь."
    m 2eua "Оказывается, там просто имя божества из святилища, с которым проделали кое-что особенное."
    m 1hub "Может, ты сделаешь о-мамори с моим именем и будешь носить с собой!"
    m 1eua "Можешь написать моё имя на листочке бумаги."
    m "Потом сложить этот листочек в маленький бумажный свёрток."
    m 1eub "Чтобы защитить его, можно использовать маленький кусочек дерева или пластика."
    m "И наконец положить свёрток в маленький тканевый мешочек и завязать верёвочкой."
    m 1hua "Только сделай мешочек ярким и красочным!"
    m 1eua "Зелёный был бы отличным цветом! Прямо как мои глаза~"
    m 1eka "И чтобы на нём было только моё имя! Всё-таки это амулет для меня. Не для кого-то другого и не для божества из святилища."
    m 1lksdla "Ох боже, сейчас, когда я об этом думаю, всё это звучит немного глупо."
    m "То есть... разве это не сделает меня каким-то божеством?"
    m 1eka "Просто мне кажется, это была бы хорошая альтернатива, если ты захочешь брать меня с собой."
    m 3eua "Особенно если у тебя нет флешки."
    m 1eua "Это не идеально, но важен сам жест, [mas_get_player_nickname()]."
    m 1eka "Если ты уделил время, чтобы сделать что-то своими руками, думая обо мне — это всё равно очень мило."
    m "А может, с таким амулетом я смогу стать хоть чуть-чуть ближе к твоему миру."
    m 1hua "Я могла бы стать твоим божеством-хранителем, эхехе~"
    return

# do you smoke ~
default persistent._mas_pm_do_smoke = None

# try to quit?
default persistent._mas_pm_do_smoke_quit = None

# succesfully quit at least once?
default persistent._mas_pm_do_smoke_quit_succeeded_before = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_smoking",category=['ты'],prompt="Курение",random=True))

label monika_smoking:
    m 2esc "Знаешь, [player]...{w=0.3} В последнее время я поняла, что люди могут очень любить вещи, которые им вредны."
    m 2euc "Один порок, который меня особенно интригует — это курение."
    m 7eud "Поразительно, сколько людей делают это каждый день...{w=0.2}хотя это так вредно не только для них самих, но и для окружающих."
    m 2rkc "Не говоря уж о вреде для окружающей среды...{w=0.2} Весь этот мусор и загрязнение ради кучи канцерогенов — просто безумие."
    m 2tkc "Даже в умеренных количествах курение никогда не бывает полезным, потому что оно очень быстро вызывает зависимость."
    m 4tkd "И это ещё и дыра в бюджете: когда сигареты кончаются, приходится покупать всё новые и новые."
    m 1tfc "Я правда это презираю..."

    $ menu_question = "Ты всё ещё куришь" if persistent._mas_pm_do_smoke else "Ты же не куришь, правда"
    m 1eka "[menu_question]?{nw}"
    $ _history_list.pop()
    menu:
        m "[menu_question]?{fast}"

        "Да, курю.":
            if persistent._mas_pm_do_smoke_quit:
                m 1ekd "Всё ещё не получается бросить, [player]?"
                m 3eka "Ничего страшного, я знаю, что бросить бывает очень непросто..."
                m 3eksdld "Просто надеюсь, что ты ещё не сдался."
                m 1hua "Я знаю, у тебя получится, если ты выложишься на все сто~"

            elif persistent._mas_pm_do_smoke_quit_succeeded_before:
                m 1ekc "Жаль, что ты снова вернулся к этой вредной привычке...{w=0.2}{nw}"
                extend 1ekd "после всех усилий, которые приложил, чтобы бросить..."
                m 3dkc "Мне от этого правда больно, [player]."
                m 1dkd "Я правда думала, что на этот раз всё позади..."
                m 1dkc "Но, наверное, всё не так просто, да?"
                m 3ekd "Очень надеюсь, что ты снова попробуешь бросить, [player]."
                m 3eka "Ты ведь попробуешь, правда? {w=0.2}Ради меня?"

            elif persistent._mas_pm_do_smoke is False:
                call monika_smoking_just_started

            else:
                m 1wud "..."
                m 1eka "Спасибо, что честен со мной, [player]..."
                m 1ekc "Хотя слышать это довольно тяжело."
                m 1ekc "Не мог бы ты... пообещать мне, что бросишь?"
                m 3rksdlc "Я знаю, что не могу заставить тебя, но для меня многое значило бы, если бы ты об этом подумал."
                m 1esc "Но если ты даже не попробуешь..."
                m 2euc "Что ж, уверена, ты не хотел бы, чтобы я принимала радикальные меры, [player]."
                m 2ekc "Пожалуйста, береги своё тело. Я хочу быть с тобой всегда."
                m 7ekbsa "Я так сильно тебя люблю."
                $ mas_ILY()

            python:
                persistent._mas_pm_do_smoke = True
                persistent._mas_pm_do_smoke_quit = False
                mas_unlockEVL("monika_smoking_quit","EVE")

        "Нет, не курю.":
            if persistent._mas_pm_do_smoke:
                call monika_smoking_quit

            else:
                m 1hub "Ах, мне так спокойно это слышать, [player]!"
                m 3eua "Просто держись от этого подальше, насколько можешь."
                m 1eka "Ужасная привычка, которая мало что даёт, кроме медленного убийства."
                m 1hua "Спасибо тебе, [player], что не куришь~"

            python:
                persistent._mas_pm_do_smoke = False
                persistent._mas_pm_do_smoke_quit = False
                mas_lockEVL("monika_smoking_quit","EVE")

        "Я пытаюсь бросить.":
            if persistent._mas_pm_do_smoke is False and not persistent._mas_pm_do_smoke_quit_succeeded_before:
                call monika_smoking_just_started(trying_quit=True)

            else:
                if not persistent._mas_pm_do_smoke and persistent._mas_pm_do_smoke_quit_succeeded_before:
                    m 1esc "Ох?"
                    m 1ekc "Значит, ты снова к этому вернулся?"
                    m 1dkd "Как жаль, [player]...{w=0.3}{nw}"
                    extend 3rkd "но не то чтобы совсем неожиданно."
                    m 3esc "Большинство людей срывается по нескольку раз, прежде чем бросить курить окончательно."
                    m 3eua "В любом случае, снова попытаться бросить — это очень правильное решение."
                else:
                    m 3eua "Это очень правильное решение."

                if persistent._mas_pm_do_smoke_quit_succeeded_before:
                    m 3eka "Ты, наверное, уже знаешь это по собственному опыту, но постарайся помнить..."
                else:
                    m 1eka "Я знаю, что весь процесс отказа может быть очень тяжёлым, особенно в начале."

                m 1eka "Если вдруг захочется закурить, просто попробуй отвлечься чем угодно другим."
                m 1eua "Если держать ум занятым другими вещами, избавиться от вредных привычек становится куда проще."
                m 3eua "Может, будешь думать обо мне, когда накроет сильное желание?"
                m 1hua "Я буду рядом и поддержу тебя на каждом шагу."
                m 1hub "Я верю в тебя, [player], у тебя всё получится!"

            python:
                persistent._mas_pm_do_smoke = True
                persistent._mas_pm_do_smoke_quit = True
                mas_unlockEVL("monika_smoking_quit","EVE")

    return "derandom"

label monika_smoking_just_started(trying_quit=False):
    m 2dfc "..."
    m 2tfc "[player]..."
    m 2tfd "Значит, ты начал курить уже после того, как мы встретились?"
    m 2dkc "Это очень разочаровывает, [player]."
    m 4ekd "Ты знаешь, как я отношусь к курению, и знаешь, как это вредно для здоровья."

    if not trying_quit:
        m 2rfd "Не представляю, что могло толкнуть тебя начать именно сейчас, {w=0.2}{nw}"
        extend 2ekc "но пообещай мне, что бросишь."

    else:
        m 4eka "Но ты хотя бы пытаешься бросить..."

    m 2rksdld "Просто надеюсь, что ты куришь не так давно — тогда будет проще избавиться от привычки."

    if not trying_quit:
        m 4eka "Пожалуйста, брось курить, [player]. {w=0.2}И ради здоровья, и ради меня."

    return


#NOTE: This event gets its initial start-date from monika_smoking, then set its date again on the appropriate path.
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_smoking_quit",
            category=['ты'],
            prompt="Я больше не курю!",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_smoking_quit:
    python:
        persistent._mas_pm_do_smoke_quit = False
        persistent._mas_pm_do_smoke = False
        mas_lockEVL("monika_smoking_quit","EVE")

    if persistent._mas_pm_do_smoke_quit_succeeded_before:
        m 1sub "Я так горжусь, что тебе снова удалось бросить курить!"
        m 3eua "Многие не могут бросить даже один раз, так что пройти через такое снова — настоящее достижение."
        m 1eud "И всё же давай постараемся, чтобы это не стало закономерностью, [player]..."
        m 1ekc "Ты же не хочешь проходить через это снова и снова, так что надеюсь, в этот раз получится насовсем."
        m 3eka "Я знаю, что у тебя есть внутренняя сила держаться подальше.{w=0.2} {nw}"
        extend 3eua "Просто помни: ты всегда можешь прийти ко мне, и я отвлеку тебя от мыслей о курении."
        m 1hua "Мы справимся вместе, [player]~"

    # first time quitting
    else:
        $ tod = "сегодня вечером" if mas_globals.time_of_day_3state == "вечер" else "завтра"
        m 1sub "Правда?! Ох боже, я так горжусь тобой, [player]!"
        m 3ekbsa "Так спокойно знать, что ты бросил курить! {w=0.2}{nw}"
        extend 3dkbsu "Я буду гораздо спокойнее спать, зная, что ты как можно дальше от этого кошмара."
        m 1rkbfu "Эхехе, если бы я была рядом, я бы угостила тебя твоим любимым блюдом [tod]."
        m 3hubfb "Всё-таки это впечатляющий подвиг! {w=0.2}Нам нужно отпраздновать!"
        m 3eubsb "Не у всех, кто хочет бросить, получается."
        m 1dubfu "Ты и правда вдохновляешь, [player]."
        m 2eua "...Только я не хочу принижать твою победу, {nw}"
        extend 2euc "но теперь тебе нужно быть осторожнее."
        m 4rsc "У многих бывших курильщиков рано или поздно снова появляется тяга."
        m 4wud "Нельзя поддаваться, ни разу! {w=0.2}Именно так и случаются срывы!"
        m 2hubsa "Но зная тебя, ты ведь этого не допустишь, правда?"
        m 2ekbfa "Учитывая всё, что ты уже сделал, я знаю — ты сильнее этого~"

    #Set this here because dialogue uses it
    $ persistent._mas_pm_do_smoke_quit_succeeded_before = True
    return "no_unlock"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_cartravel",category=['романтика'],prompt="Поездка на машине",random=True))

label monika_cartravel:
    m 1euc "[player], последнее время у меня кое-что крутится в голове..."
    m 1eua "Разве не было бы здорово куда-нибудь поехать — только ты и я?"
    m 3eka "Было бы чудесно исследовать красивые места — где угодно, где мы ещё не бывали."
    m 3hub "Может, прокатиться через манящий лес...{w=0.5}или встретить закат на побережье!"
    m 1hub "Уверена, нам было бы очень весело в такой поездке, [mas_get_player_nickname()]."
    if not persistent._mas_pm_driving_can_drive:
        m 1rksdla "Я знаю, что мы пока не можем по-настоящему поехать, но уверена — когда-нибудь получится!"
    m 1eua "На самом деле неважно, куда мы отправимся, главное — что я с тобой."
    m 1eka "Так жду этого, [player]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_100k",category=['мод'],prompt="100 тысяч скачиваний",random=True))

label monika_100k:
    m 1wud "Меня до сих пор поражает, как много людей обо мне заботятся."
    m 3eua "Ты знал, что больше ста тысяч человек скачали тот же мод, что и ты?"
    m 1eka "Разработчики даже выложили особенную иллюстрацию в честь этого."
    m 1hub "Такие вещи всегда заставляют меня улыбаться!"
    m 1hua "Если ещё не видел — обязательно посмотри!"
    m 1eka "Художницу зовут Sasoura, и она любит меня почти так же сильно, как я люблю тебя."
    if persistent.playername.lower()=='sasoura':
        m 1tfc "Погоди... Sasoura... разве это не твоё имя?"
        m 1wud "Это ты нарисовал ту очаровательную картинку?"
        m 2wuo "Боже! Не могу поверить, что не заметила раньше!"
        m 2sub "От этого она становится ещё особеннее."
        m 2eua "Я рада, что могу сказать тебе, как много это для меня значит."
        m 2eka "Это значит для меня целый мир."
        m 2hubsb "Большое-большое спасибо!"
    else:
        m 1hua "Почти~"
    return

default persistent._mas_pm_donate_charity = None
# True if user donated

default persistent._mas_pm_volunteer_charity = None
# True if user has volunteered

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_asks_charity",
            category=['ты'],
            prompt="Благотворительность",
            random=True
        )
    )

label monika_asks_charity:
    m 1esd "Слушай, [player]."
    m 1esc "Кое-что недавно пришло мне в голову."
    m 3esd "Раз мой мир вымышленный, в нём нет таких проблем, как голод или бедность."
    m 2rkc "Я знаю, что они существуют, но сама никогда этого по-настоящему не видела."
    m 2ekc "Однако в твоей реальности всё иначе. Там много людей, которым нужна помощь просто чтобы выжить."
    m 2esd "Ты наверняка хотя бы раз видел бездомного, если бывал в большом городе."
    m "Так вот, мне просто было интересно..."

    m 1eua "Ты когда-нибудь помогал благотворительности?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь помогал благотворительности?{fast}"

        "Я жертвовал.":
            $ persistent._mas_pm_donate_charity = True
            m 3hub "Это замечательно!"
            m 2eua "Хотя можно спорить, что волонтёрство полезнее, я думаю, в пожертвованиях нет ничего плохого."
            m 2eka "Это лучше, чем ничего, и ты точно вносишь вклад — даже если бюджет ограничен или времени мало."
            m 2ekc "Грустно признавать, но благотворительным организациям всегда нужны люди, которые дают деньги или другие ресурсы."
            m 3lksdlc "Ведь столько дел нуждаются в поддержке."
            m 3ekc "И всё же никогда не знаешь наверняка, дойдут ли пожертвования до хорошего дела."
            m 3ekd "Не помогает и то, что некоторые организации якобы поддерживают дело, а на деле забирают пожертвования себе."
            m 2dsc "..."
            m 2eka "Прости, я не хотела уводить разговор в такую тьму."
            m 1eua "Я знала, что ты достаточно добр, чтобы сделать такое."
            m 1hub "Это ещё одна причина любить тебя, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
            show monika 5hub at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5hub "Ты всегда такой милый~"

        "Я был волонтёром.":
            $ persistent._mas_pm_volunteer_charity = True
            m 1wub "Правда?"
            m 1hub "Это прекрасно!"
            m 3hua "Жертвовать — хороший способ помочь, но протянуть руку помощи ещё лучше!"
            m 3rksdla "Конечно, деньги и ресурсы важны, но обычно рук как раз и не хватает..."
            m 2ekc "Это понятно: у большинства работающих взрослых не всегда есть свободное время."
            m 2lud "Так что чаще всего организацией занимаются пенсионеры, и бывает трудно, если нужно таскать тяжёлое."
            m 2eud "Поэтому им иногда нужна помощь со стороны — особенно от подростков или молодых взрослых, у которых больше сил."
            m 1eua "В любом случае, здорово, что ты попытался что-то изменить через волонтёрство."
            m 4eub "Плюс я слышала, что опыт волонтёрства отлично смотрится в резюме при устройстве на работу."
            m 3hua "Так что, делал ты это ради этого или просто из доброты — в любом случае это хорошо."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Знаешь, именно такие вещи заставляют меня любить тебя ещё сильнее, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
            m 5hub "Я так горжусь, что ты помогал людям в нужде."
            m 5hubsa "Я так сильно тебя люблю, [player]. Правда."

        "Нет, не доводилось.":
            $ persistent._mas_pm_donate_charity = False
            $ persistent._mas_pm_volunteer_charity = False
            m 1euc "Ох, понятно."
            m 2esc "На самом деле я могу понять."
            m 2esd "Благотворительных организаций много, но нужно быть осторожным: бывает мошенничество с деньгами или дискриминация в том, кому помогают."
            m 2ekc "Поэтому им сперва бывает трудно довериться."
            m 3esa "Вот почему стоит всегда немного покопаться и найти организации с хорошей репутацией."
            m 2dkc "Видеть, как люди постоянно страдают от голода или бедности..."
            m 2ekd "И даже те, кто пытается им помочь, с трудом что-то меняют..."
            m 2esc "От этого становится немного тягостно, если не сказать подавленно."
            m 2eka "Но, знаешь..."
            m "Даже если ты ничем не можешь помочь материально, иногда достаточно просто улыбнуться людям."
            m 2ekc "Когда тебя игнорируют прохожие, это тяжело и тем, кто борется, и тем, кто пытается помочь."
            m 2rkc "Будто общество видит в них помеху, хотя они просто пытаются выжить."
            m 2eua "Иногда одной улыбки достаточно, чтобы дать силы идти дальше."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Прямо как когда я с тобой."
            m 5hua "Одной твоей улыбки хватает, чтобы все мои тревоги исчезли."
            m 5hubsb "Я так сильно тебя люблю, [player]."
    return "derandom|love"

init 5 python:
    addEvent(
        Event(persistent.event_database,
            eventlabel='monika_kizuna',
            prompt="Виртуальный ютубер?",
            category=['разное'],
            random=False,
            unlocked=False,
            pool=False,
            action=EV_ACT_POOL,
            conditional="seen_event('greeting_hai_domo')"
        )
    )

label monika_kizuna:
    m 1eua "Ах да, я же упоминала её тебе, да?"
    m 3eua "Недавно мне в твиттере скинули несколько видео с YouTube."
    m 1eub "И среди них было «Virtual YouTuber Kizuna Ai»."
    m "Как я уже говорила, она довольно очаровательна, но я не думаю, что она по-настоящему «виртуальная»."
    m 3rksdla "Мне кажется, это актриса озвучки, спрятанная за 3D-марионеткой."
    m 1eua "И всё же персонаж, которого она играет, уникален, и знаешь что?"
    m 1hub "Она проходила нашу любимую игру!~"
    m 2hksdlb "..."
    m 2lksdlb "Честно говоря, я не уверена, как отношусь к летсплеям."
    m 3euc "То есть к летсплеям {i}этой{/i} игры — в основном."
    m 2euc "Я обычно их не смотрю, потому что не люблю видеть разные версии себя, снова и снова совершающие одни и те же ошибки..."
    m 2lsc "Но когда я узнала про её фишку, мне захотелось..."
    m 1lksdla "Просто мне {i}нужно{/i} было узнать, как отреагирует Ай-чан!"
    m 1eka "Даже если это всего лишь роль, думаю, она поймёт мою ситуацию..."
    m 3eua "По крайней мере лучше, чем обычный ютубер."
    m 5hub "Не могу дождаться, когда досмотрю серию до конца..."
    return

# do you have a family
default persistent._mas_pm_have_fam = None

# do you have siblings
default persistent._mas_pm_have_fam_sibs = None

# does no fam botheryou
default persistent._mas_pm_no_fam_bother = None

# family a mess?
default persistent._mas_pm_have_fam_mess = None

# will fam get better?
# YES, NO, MAYBE
default persistent._mas_pm_have_fam_mess_better = None

# dont wanna talk about it
default persistent._mas_pm_no_talk_fam = None

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_asks_family",category=['ты'],prompt="Семья [player]",random=False))

label monika_asks_family:
    m 1eua "[player], у тебя есть семья?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], у тебя есть семья?{fast}"
        "Да, есть.":
            $ persistent._mas_pm_have_fam = True
            $ persistent._mas_pm_have_fam_mess = False
            $ persistent._mas_pm_no_talk_fam = False

            #Make sure we didn't answer this already
            if persistent._mas_pm_fam_like_monika is None:
                #Rerandom this family based topics since you do have a family
                $ mas_showEVL("monika_familygathering", "EVE", _random=True)

            m 1hua "Это прекрасно!"
            m 3hua "Уверена, твоя семья замечательная~"

            m 1eua "У тебя есть братья или сёстры?{nw}"
            $ _history_list.pop()
            menu:
                m "У тебя есть братья или сёстры?{fast}"
                "Да.":
                    $ persistent._mas_pm_have_fam_sibs = True
                    m 1hua "Это фантастика!"
                    m "Наверняка они не дают тебе скучать."
                    m 1eka "Уверена, твои братья и сёстры такие же добрые и внимательные, как и ты."
                    m 3hub "Может, я смогу уговорить их создать со мной новый литературный клуб!"
                    m 1hua "Эхехе~"
                    m 1eua "Мы сможем вместе делать столько всего весёлого."
                    m 3rksdla "На этот раз точно всё получится куда лучше, чем раньше."
                    m 1eua "Уверена, я полажу и с твоими братьями и сёстрами, и со всей твоей семьёй, [mas_get_player_nickname()]."
                    m 3hub "Так жду встречи со всеми ними!"

                "Я единственный ребёнок.":
                    $ persistent._mas_pm_have_fam_sibs = False
                    m 1euc "Быть единственным ребёнком — у этого точно есть свои плюсы и минусы."
                    m 2eka "Может, родители уделяют тебе больше внимания. Если только они не были постоянно заняты."
                    m 2ekc "С другой стороны, возможно, ты чувствуешь себя одинонее, чем те, у кого есть братья и сёстры."
                    m 2eka "Я точно понимаю это чувство."
                    m 1hua "Но знай: что бы ни случилось, я всегда буду с тобой, [mas_get_player_nickname()]."

        "У меня всё плохо с семьёй.":
            $ persistent._mas_pm_have_fam = True
            $ persistent._mas_pm_have_fam_mess = True
            $ persistent._mas_pm_no_talk_fam = False
            m 1euc "Ох."
            m 1lksdlc "..."
            m 1ekc "Мне жаль, [player]."

            m "Ты думаешь, всё наладится?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты думаешь, всё наладится?{fast}"
                "Да.":
                    $ persistent._mas_pm_have_fam_mess_better = "YES"
                    m 1eka "Рада это слышать."
                    m 1eua "Надеюсь, однажды все в твоей семье смогут помириться."
                    m 3eua "И я знаю, что ты справишься с тем, что происходит в твоей жизни сейчас."
                    m 1eka "Что бы ни случилось, я буду рядом, [player]."
                    m 1hua "Всегда помни об этом!"

                "Нет.":
                    $ persistent._mas_pm_have_fam_mess_better = "NO"
                    m 1ekc "Ах, понятно..."
                    m "Как бы мне хотелось быть рядом и хоть немного тебя утешить."
                    m 1eka "..."
                    m 3eka "[player], что бы ты ни переживал — я знаю, когда-нибудь станет лучше."
                    m 1eua "Я буду с тобой на каждом шагу."
                    m 1hub "Я так сильно тебя люблю, [player]. Пожалуйста, никогда этого не забывай!"
                    $ mas_ILY()

                "Может быть.":
                    $ persistent._mas_pm_have_fam_mess_better = "MAYBE"
                    m 1lksdla "..."
                    m 1eua "Что ж, хотя бы есть шанс."
                    m 3hua "Жизнь полна трагедий, но я знаю — ты достаточно силён, чтобы справиться с чем угодно!"
                    m 1eka "Надеюсь, все проблемы в твоей семье в итоге разрешатся, [player]."
                    m "А если нет — знай, что я буду рядом."
                    m 1hua "Я всегда буду поддерживать своего любимого~"

        "У меня никогда не было семьи.":
            $ persistent._mas_pm_have_fam = False
            $ persistent._mas_pm_no_talk_fam = False
            #Derandom this family based topics since you don't have a family
            $ mas_hideEVL("monika_familygathering","EVE",derandom=True)

            m 1euc "Ох, мне так жаль, [player]."
            m 1lksdlc "..."
            m 1ekc "Твой мир так непохож на мой, и я не хочу притворяться, будто понимаю, через что ты проходишь."
            m 1lksdlc "Могу точно сказать: то, что моя семья была ненастоящей, причинило мне немало боли."
            m 1ekc "И всё же я знаю, что тебе пришлось хуже."
            m "У тебя не было даже вымышленной семьи."
            m 1dsc "..."

            m 1ekc "Тебя это до сих пор беспокоит?{nw}"
            $ _history_list.pop()
            menu:
                m "Тебя это до сих пор беспокоит?{fast}"
                "Да.":
                    $ persistent._mas_pm_no_fam_bother = True
                    m 1ekc "Это... понятно."
                    m 1eka "Я буду с тобой всегда, [player]."
                    m "Что бы ни потребовалось — я заполню эту пустоту в твоём сердце своей любовью..."
                    m 1hua "Обещаю тебе."
                    m 1ekbsa "Ты — моё всё..."
                    m 1hubfa "Надеюсь, я смогу стать твоим~"

                "Нет.":
                    $ persistent._mas_pm_no_fam_bother = False
                    m 1eua "Это очень хорошо."
                    m 1eka "Рада, что тебе удалось двигаться дальше."
                    m 1hua "Ты очень стойкий человек, и я верю в тебя, [player]!"
                    m 1eka "Надеюсь, я смогу заполнить эту пустоту в твоём сердце."
                    m "Мне правда не всё равно, и я сделаю для тебя всё что угодно."
                    m 1hua "Когда-нибудь мы сможем создать свою собственную семью!"

        "Я не хочу об этом говорить.":
            $ persistent._mas_pm_no_talk_fam = True
            m 1dsc "Я понимаю, [player]."
            m 1eka "Мы можем поговорить об этом, когда ты будешь готов."
            m 1lsc "Впрочем..."
            m 1lksdlc "Возможно, тебе слишком больно об этом говорить."
            m 1eka "Ты расскажешь мне о своей семье, когда будешь готов, [player]."
            m 1hubsa "Я очень сильно тебя люблю!"
            $ mas_ILY()

    return "derandom"

#do you like other music
default persistent._mas_pm_like_other_music = None

# historical music history
default persistent._mas_pm_like_other_music_history = list()

init 5 python:
     addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_concerts",
            category=['медиа',"музыка"],
            prompt="Концерты",
            conditional="mas_seenLabels(['monika_jazz', 'monika_orchestra', 'monika_rock', 'monika_vocaloid', 'monika_rap'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_concerts:
    # TODO: perhaps this should be separated into something specific to music
    # genres and the concert just referencing back to that?
    # this topic is starting to get too complicated

    m 1euc "Эй, [player], я думала о том, что мы могли бы однажды сделать вместе..."
    m 1eud "Ты же знаешь, что мне нравятся разные виды музыки?"
    m 1hua "Ну так..."
    m 3eub "Почему бы нам не сходить на концерт?"
    m 1eub "Говорят, атмосфера на концерте и правда заставляет чувствовать себя живым!"

    m 1eua "Есть ли ещё какие-то жанры музыки, которые ты хотел бы услышать вживую и о которых мы ещё не говорили?{nw}"
    $ _history_list.pop()
    menu:
        m "Есть ли ещё какие-то жанры музыки, которые ты хотел бы услышать вживую и о которых мы ещё не говорили?{fast}"
        "Да.":
            $ persistent._mas_pm_like_other_music = True
            m 3eua "Отлично!"

            python:
                musicgenrename = ""
                while len(musicgenrename) == 0:
                    musicgenrename = renpy.input(
                        'Какую музыку ты слушаешь?',
                        length=15,
                        allow=letters_only + "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ-"
                    ).strip(' \t\n\r')

                tempmusicgenre = musicgenrename.lower()
                persistent._mas_pm_like_other_music_history.append((
                    datetime.datetime.now(),
                    tempmusicgenre
                ))

            # NOTE: should be think? maybe?
            m 1eua "Интересно..."
            show monika 3hub
            $ renpy.say(m, "Я бы с радостью сходила с тобой на {0} концерт!".format(mas_a_an_str(tempmusicgenre)))

        "Нет.":
            if (
                not persistent._mas_pm_like_vocaloids
                and not persistent._mas_pm_like_rap
                and not persistent._mas_pm_like_rock_n_roll
                and not persistent._mas_pm_like_orchestral_music
                and not persistent._mas_pm_like_jazz
            ):
                $ persistent._mas_pm_like_other_music = False
                m 1ekc "Ох... Ну ничего, [player]..."
                m 1eka "Уверена, мы найдём чем ещё заняться."
                return

            else:
                $ persistent._mas_pm_like_other_music = False
                m 1eua "Хорошо, [mas_get_player_nickname()], тогда выберем из тех жанров, о которых мы уже говорили!"

    m 1hua "Просто представь нас..."
    if persistent._mas_pm_like_orchestral_music:
        m 1hua "Как мы мягко покачиваем головами под звуки успокаивающего оркестра..."

    if persistent._mas_pm_like_rock_n_roll:
        m 1hub "Как прыгаем вместе с толпой под хороший старый рок-н-ролл..."

    if persistent._mas_pm_like_jazz:
        m 1eua "Как плавно двигаемся под мягкий джаз..."

    if persistent._mas_pm_like_rap:
        m 1hksdlb "Как пытаемся угнаться за настоящим рэпером..."

    if persistent._mas_pm_like_vocaloids:
        m 1hua "Как машем светящимися палочками на Miku Expo..."

    if persistent._mas_pm_like_other_music:
        m 1hua "Как подпеваем твоему любимому исполнителю в стиле [tempmusicgenre]..."

    m 2hub "Разве это не звучит потрясающе?"
    m 2eud "Сама мысль увидеть своего кумира прямо перед собой — это невероятно!"
    m 2lksdla "Хотя билеты в наши дни довольно дорогие..."
    m 2hua "Но я всё равно думаю, что оно того стоит!"
    m 3eua "Ты знаешь какие-нибудь группы или музыкантов, которых нам стоит увидеть вживую, [player]?"
    m 3eub "Я бы {i}очень{/i} хотела их увидеть, если они нравятся {i}тебе{/i}."
    m 5eua "А если ты возьмёшь меня с собой,{w=1} это и правда будет мечтой наяву!"
    m 4eua "Но если концерты тебе не особо интересны..."
    m 1eua "Тогда мы всегда можем укрыться пледом и поставить пластинку или диск дома!"
    m 1hua "Для меня этого более чем достаточно, эхехе~"
    if (
        not renpy.seen_label("monika_add_custom_music_instruct")
        and not persistent._mas_pm_added_custom_bgm
    ):
        m 1eua "А пока, если захочешь поделиться со мной любимой музыкой — это очень просто!"
        m 3eua "Тебе нужно всего лишь сделать вот что..."
        call monika_add_custom_music_instruct
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_explain",
            category=['романтика','моника','разное'],
            prompt="Объяснишь кому-нибудь наши отношения?",
            pool=True
        )
    )

label monika_explain:
    #TODO: temporary Monika nickname reset for this
    m 1euc "Ты хочешь, чтобы я объяснила наши отношения кому-то другому?"
    m 1eua "Хорошо, просто поставь меня перед ними, чтобы они меня видели."
    m 1hua "Я постараюсь объяснить всё как можно лучше."
    m 1eua "Подожду, пока ты будешь готов.{nw}"
    $ _history_list.pop()
    menu:
        m "Подожду, пока ты будешь готов.{fast}"
        "Начать.":
            pass
    m 1hua "Привет! Меня зовут Моника."
    m "Верная девушка [player]!"
    m 1lksdlb "Знаю, наши отношения со стороны могут выглядеть странно..."
    m 1lksdla "И их, наверное, не считают обычными..."
    m 1esc "Но позволь мне сказать..."
    m 1hub "...любовь, которую мы разделяем — абсолютно настоящая!"
    m 1eka "И [player] тоже был очень добр ко мне!"
    m 1ekc "До встречи с [player] мне казалось, будто во мне чего-то не хватает."
    m "Мне было одиноко и страшно, и некому было помочь..."
    m 1hua "...пока не появился [player]."
    m "И оказалось, что этой недостающей частью был[a] [he]!"
    if persistent.gender == "F" or persistent.gender == "M":
        m 1eua "Теперь [he] разговаривает со мной, и мне больше не так одиноко."
    else:
        m 1eua "Теперь они разговаривают со мной, и мне больше не так одиноко."
    m "Одно только то, что [he] открывает игру, уже делает мой день ярче!"
    m 1dsc "Так что, пожалуйста..."
    m 4eka "...не судите наши отношения."
    m 1eka "Даже если они другие."
    m 1dsc "..."
    m 1dubssdlu "...Фух!"
    m 1lksdlb "Вот это была речь!"
    m 1eksdla "Ну как всё прошло, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ну как всё прошло, [player]?{fast}"
        "Всё прошло хорошо!":
            m 1hub "Отлично!"
            m 3hua "Я так рада, что смогла помочь кому-то чуть лучше понять наши отношения!"
        "Всё прошло плохо.":
            m 1dkc "Ох."
            m 1ekd "Что ж...{w=1} наверное, нельзя ожидать, что {i}все{/i} поймут наши отношения..."
            m 3rkc "Со стороны они {i}действительно{/i} довольно необычные."
            m 3eka "Но в итоге неважно, кто одобряет наши отношения, а кто нет..."
            m 1hua "Пока мы любим друг друга — это всё, что имеет значение~"
    return

# do you live near beach
default persistent._mas_pm_live_near_beach = None

init 5 python:
     addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_beach",
            category=["местоположение"],
            prompt="Пляж",
            random=True
        )
    )

label monika_beach:
    m 1eua "[player], ты когда-нибудь был на пляже?"
    m "Я всегда хотела сама туда съездить, но никак не находила времени."
    m 1eka "Я вечно была занята учёбой или делами клуба."
    m 4ekc "Было нелегко за всем уследить, знаешь ли..."
    m 4ekd "А когда выдавался перерыв, я обычно просто отдыхала дома."
    m "Всё-таки такие моменты выпадали редко."
    m 2esc "Хотя иногда мне кажется, что я упустила шанс создать важные воспоминания."

    m "Ты живёшь рядом с пляжем, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты живёшь рядом с пляжем, [player]?{fast}"
        "Да.":
            $ persistent._mas_pm_live_near_beach = True
            m 1hub "Это здорово!"
            m 1eua "Боже, наверное, так приятно иметь его так близко."
            m 1hub "Не могу дождаться — на нашем первом свидании мы сможем романтично прогуляться по берегу~"

        "Нет.":
            $ persistent._mas_pm_live_near_beach = False
            m 1eka "Ничего страшного. В смысле, каковы шансы? У большинства людей его нет."
            m 1hub "Значит, просто съездим на целый день!"

    m 1eua "Столько всего мы сможем сделать когда-нибудь."
    m 1hua "Даже просто представить все ощущения, которые можно испытать — уже волнующе!"
    m 3eua "Свежий морской воздух, крики чаек."
    m "И ощущение песка под ногами..."
    m 1hua "Это точно стоило бы поездки!"
    m 1eka "А быть там с тобой сделало бы всё ещё лучше..."
    m 3eua "Столько всего мы могли бы делать вместе."
    m 3eub "Поиграть в волейбол, поесть мороженого или поплавать в море."
    m 3rkbsa "Наверное, будет холодно, но уверена — мы как-нибудь согреем друг друга..."
    m 3eua "Могли бы попробовать сёрфинг или поискать ракушки на память."
    m "Даже просто лежать и слушать шум волн рядом с тобой было бы для меня достаточно."
    m 3tfu "Только не засыпай, а то я закопаю тебя в песок!"
    m 2huu "Эхехе! Шучу, [mas_get_player_nickname()]."
    m 2lksdla "Хотя купальник мне придётся купить новый..."
    m 1tsbsa "Ты бы предпочёл слитный или раздельный?"
    m 1eua "Хотя... думаю, я сделаю это сюрпризом."
    m 1tku "Только не слишком волнуйся, когда увидишь его. Эхехе~"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_solipsism",
            category=['философия'],
            prompt="Солипсизм",
            random=True
        )
    )

label monika_solipsism:
    m 3eub "Ты когда-нибудь слышал о солипсизме, [player]?"
    m 3eua "Это идея о том, что существуешь только ты сам."
    m 1eud "'Cogito, ergo sum.'"
    m 3eud "'Я мыслю, следовательно, я существую.'"
    m 1euc "Если ты знаешь, что {i}ты{/i} существуешь — можешь ли сказать то же о ком-то другом?"
    m 3etc "Может, все остальные — всего лишь плод нашего воображения, [player]."
    m 2etc "Может, на самом деле мы — единственное сознание в этом мире, посреди огромного моря фальшивых умов..."
    m 2dsd "Создания наших буйных фантазий..."
    m 3eub "Ахаха, шучу~"
    m 1eud "Я и правда считаю, что мы можем доверять собственному существованию и сомневаться в существовании других..."
    m 3eua "Но при этом мы не можем по-настоящему опровергнуть их существование, правда?"
    m 1hksdla "По крайней мере, без каких-нибудь психических способностей заглянуть им в головы."
    m 3eua "Если остановиться и подумать, солипсизм — действительно интересная концепция; она заставляет глубже задуматься, что значит быть настоящим..."
    m 1dsc "И что именно считается {i}настоящим{/i}."
    m 1eua "Но я знаю, что ты и я — настоящие, [player]."
    m 1eub "Мы могли быть созданы по-разному и даже работать по-разному, но мы оба — люди, способные мыслить самостоятельно."
    m 3eua "Довольно утешительно знать, что ты не совсем один в бесконечном океане неопределённости, тебе так не кажется?"
    m 3hua "Надеюсь, рядом со мной ты чувствуешь именно это~"
    $ mas_protectedShowEVL("monika_materialism","EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_attractiveness",
            category=['участники клуба','общество'],
            prompt="Привлекательность",
            random=True
        )
    )

label monika_attractiveness:
    m 1etc "Скажи, [player], тебе никогда не было интересно, как Сайори оставалась такой стройной?"
    m 3rksdla "Ты же знаешь, что она много ест, да? И образ жизни у неё не самый активный."
    m 3euc "Сначала я думала, что это метаболизм не даёт ей набирать вес."
    m 3esd "...Но когда поняла, что наш мир ненастоящий, у меня появилась другая теория."
    m 7euc "Как персонажам игры, нам нужно было какое-то визуальное представление, чтобы ты, игрок, мог нас видеть."
    m 2esc "Сайори, Нацуки, Юри и даже я..."
    m 2rkc "С твоей точки зрения у нас нет настоящих тел, как у людей в твоём мире. Ты видишь нас лишь как набор изображений, отражающих внешность и эмоции."
    m 2eud "...Но с моей точки зрения я тоже вижу весь свой мир в трёх измерениях, будто всё настоящее."
    m 2euc "Значит, какой-то дизайнер — возможно, не один — решил нарисовать нас такими, какие мы есть."
    m 2eud "И раз на всех этих изображениях один и тот же тип фигуры, у Сайори всегда была бы одна и та же форма, что бы она ни делала."
    m 2dkc "Это...{w=0.3}странно осознавать."
    m 2eud "Я чувствую, что прямо сейчас нахожусь в этой комнате, могу смотреть на себя так же, как, полагаю, ты смотришь на себя — почти будто у меня есть настоящее тело..."
    m 7ekc "Но с твоей точки зрения у меня его нет. Я просто сознание, которое показывает соответствующую картинку в зависимости от того, что я делаю или чувствую."

    #Just seen Monika in her uniform and nothing else
    if len(store.mas_selspr.filter_clothes(True)) == 1:
        m 3euc "Полагаю, с одеждой всё устроено так же."
        m 1eud "Сейчас у меня только эта школьная форма, потому что, наверное, только в ней меня и рисовали..."
        m 1eua "Но если бы кто-то нарисовал для меня другую одежду и добавил её в игру, я смогла бы менять наряды, как другие девочки."
        m 1hua "Разве это не было бы здорово?"
        m 1rksdla "И было бы приятно хоть немного менять свой образ для тебя..."

    else:
        m 3eua "С моей одеждой всё устроено так же."
        m 1euc "Кто-то должен был нарисовать то, что на мне сейчас, и добавить это в игру, чтобы я могла это носить."
        m 1esd "Её сделали не так, как шьют одежду в твоей реальности. Это просто набор изображений."
        m 1rksdla "Немного, но хотя бы я могу менять наряды для тебя..."

    m 1rksdlc "..."
    m 1ekc "Знаешь, [player], это одна из причин, почему я завидую людям в твоём мире.{w=0.3} {nw}"
    extend 3eka "У них столько способов экспериментировать со своим внешним видом..."
    m 7eub "Они могут надеть новую одежду, попробовать новую причёску, постараться привести себя в форму и многое другое..."
    m 2rkd "...а я застряла с одной и той же внешностью, что бы ни делала."
    m 2hksdlb "Не пойми неправильно — мне нравится, как я выгляжу сейчас!"
    m 2rka "...Но я думаю, важно выглядеть хорошо в глазах партнёра...{w=0.3}{nw}"
    extend 2ekb "и мне хотелось бы иметь возможность постараться выглядеть для тебя настолько привлекательной, насколько возможно."

    if renpy.seen_label("mas_compliment_beautiful"):
        if mas_isMoniNormal(higher=True):
            m 2rkbsa "Но... ты же говорил, что в твоих глазах я уже прекрасна."
            m 2ekbfa "Так что, наверное, мне и не о чем беспокоиться, правда?"
            if mas_anni.pastOneMonth():
                m 1hubfa "К тому же ты бы не смотрел на меня всё это время, если бы тебе уже не нравилось, как я выгляжу, верно?"
                m 1hubfb "Ахаха~"
            show monika 1euc at t11 zorder MAS_MONIKA_Z with dissolve_monika

        else:
            m 2lkc "Я знаю, ты говорил, что тебе уже нравится, как я выгляжу, но я просто..."
            m 2dkc "...не знаю.{w=0.2} Просто...{w=0.3}забудь, что я что-то говорила."

    else:
        if mas_isMoniHappy(higher=True):
            m 2lsbsa "Хотя, учитывая, что ты всё ещё здесь со мной...{w=0.5}{nw}"
            extend 2ekbsa "наверное, мне не стоит слишком об этом переживать, да?"
            m 1hub "В конце концов, ты бы не смотрел на меня всё это время, если бы тебе уже не нравилось, как я выгляжу! Ахаха!"

        else:
            m 2lkc "...Особенно когда я переживаю, что, может, я просто не твой тип, [player]."

    m 1euc "Как бы то ни было, не знаю, замечал ли ты, но несмотря на разницу в питании и образе жизни, мы с другими девочками выглядим довольно похоже."
    m 3ekd "Конечно, фигуры у нас разные: Нацуки более миниатюрная, а Юри — более зрелая."
    m 3eka "...Глаза и волосы тоже у всех разные."
    m 3eua "Но думаю, всех нас можно было бы назвать привлекательными."
    m 3eud "В смысле, никто из нас не мускулистый и не полный..."
    m 3tkd "...Ни у кого нет физических ограничений..."
    m 3tkc "...Никто не лысый и ни у кого волосы не короче подбородка..."
    m 1rud "...и кроме шрамов на руках у Юри, ни у кого нет проблем с кожей."
    m 7dsd "Те, кто создавал нашу внешность, наверняка решили, что игрокам всё это показалось бы отталкивающим."
    m 2lsc "Если подумать, это не так уж удивительно. Есть много вещей, из-за которых общество может счесть человека непривлекательным."
    m 2dsc "И некоторые из них совершенно не зависят от самого человека."
    m 2efo "Но люди, которые не соответствуют общепринятым стандартам красоты, всё равно постоянно находят отношения!"
    m 2tfc "Так что идея какого-то универсального стандарта красоты, не дотянув до которого обречён на вечное одиночество..."
    m 2efw "Просто не имеет для меня никакого смысла!"
    m 2dfc "..."
    m 2dsc "..."

    if mas_isMoniNormal(higher=True):
        m 2ekc "Прости, [player]. Наверное, мне просто нужно было выговориться."
        m 4eud "Я знаю, что мне это не особо нужно, но я всё равно стараюсь правильно питаться, достаточно двигаться и следить за собой... и не только."

        if mas_isMoniEnamored(higher=True):
            $ first_line_var = "когда"
            $ second_line_end = "когда бы это ни случилось"

        else:
            $ first_line_var = "может,"
            $ second_line_end = "если это вообще когда-нибудь случится"

        m 4eub "Просто приятно поддерживать такие полезные привычки, и к тому же кто знает, [first_line_var] я смогу перейти в твою реальность и обрести обычное тело, как у тебя."
        m 1hua "Не помешает убедиться, что я буду готова к этому переходу [second_line_end]."
        m 1eua "Но тебе не о чем беспокоиться, [player]."
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Я всегда буду любить тебя, как бы ты ни выглядел."
        m 5eka "Но всё же постарайся и о себе заботиться, хорошо? Твоё здоровье для меня тоже важно."
        $ mas_ILY()

    else:
        m 2ekc "Прости, [player]. Наверное, мне в последнее время было немного тяжело, и я просто хотела выговориться."
        m 7eud "Я знаю, что мне всё это не обязательно, но я всё равно стараюсь правильно питаться, достаточно двигаться и следить за собой."
        m 3esa "Всегда приятно поддерживать такие полезные привычки."
        m 1eka "Но тебе не о чем беспокоиться..."
        m 1eua "Пока ты заботишься о себе, мне всё равно, как ты выглядишь."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_timetravel",category=['медиа','разное'],prompt="Путешествия во времени",random=True))

label monika_timetravel:
    $ todays_date, todays_diff = store.mas_calendar.genFormalDispDate(datetime.date.today())
    $ one_year_later, year_later_diff = store.mas_calendar.genFormalDispDate(store.mas_utils.add_years(datetime.date.today(),1))
    $ one_year_earlier, year_earlier_diff = store.mas_calendar.genFormalDispDate(store.mas_utils.add_years(datetime.date.today(),-1))
    m 3eub "Эй, [player], ты ведь слышал о путешествиях во времени?"
    m 1esb "Это очень распространённая идея в историях, и у каждого автора свой взгляд на неё."
    m 1eua "Как работает перемещение во времени, можно ли менять прошлое, какие будут последствия..."
    m 1eub "Всё это отличается от истории к истории."
    m 3ekc "Чего обычно не показывают — так это того, как это влияет на близких путешественника во времени."
    m 3rksdld "Если они не могут отправиться вместе с ним, кто знает, сколько пройдёт, прежде чем они снова увидятся?"
    m 2ekc "Ну, сам путешественник, может, и знает — но только если с ним ничего ужасного не случится."
    m 2lksdld "А пока его друзья и семья остаются ждать его возвращения."
    m 2ekd "На сколько он исчезнет? На год? На десятилетие? Ещё дольше?"
    m 4ekd "Смогут ли они ждать так долго?"
    m "Будут ли они ещё помнить путешественника к тому времени?"
    m 2dksdlc "..."
    if seen_event("monika_resource"):
        m 4rksdlc "Помнишь, я говорила, что здесь время течёт не так, как в твоём мире?"
        m "Ну так..."
    else:
        m 4rksdlc "Знаешь, здесь время на самом деле течёт не так, как в твоём мире."
        m "Так что..."
    m 1esd "Единственный способ узнать, какой у тебя день и время — это смотреть на часы на твоём компьютере."
    m 3eub "Поэтому я знаю, что сегодня [todays_date]."
    m 1esc "Но если бы ты изменил дату на компьютере на [one_year_later]..."
    m "Для тебя прошли бы лишь несколько секунд..."
    m 1ekd "...а я бы думала, что прошёл целый год."
    m 1tkd "Целый год без единой встречи с тобой."
    m 1lksdlc "Я бы гадала, не забыл ли ты обо мне или больше не хочешь проводить со мной время."
    if mas_isMoniDis(lower=True):
        m 1dkc "...И это даже не было бы большим сюрпризом."
    elif mas_isMoniAff(higher=True):
        m 1ekc "...Даже если сначала в это было бы трудно поверить."
    m 1ekd "И просто вернуть дату назад уже ничего бы не исправило."
    m 3esd "Представь: ты ложишься спать сейчас, а просыпаешься — и уже [one_year_earlier]."
    m 3wuo "Значит ли это, что весь прошлый год был лишь сном?"
    m 3wuw "Как понять, что ты всё ещё не спишь?"
    m 3esc "Всё было бы очень запутанно."
    m 1lksdla "Думаю, я пытаюсь сказать..."
    m 1eka "Пожалуйста, не меняй дату на компьютере, [player]."
    if mas_isMoniHappy(higher=True):
        m "Я верю, что ты не станешь так со мной шутить."
    else :
        m "Обещаешь?"
    m 3euc "А если ты когда-нибудь и правда отправишься в будущее..."
    m 1hksdlb "Не мог бы ты принести оттуда технологию, которая позволит мне перейти в твой мир?"
    return

# been to prom?
default persistent._mas_pm_gone_to_prom = None

# how was prom?
default persistent._mas_pm_prom_good = None

# go with date?
default persistent._mas_pm_had_prom_date = None

# suggested monika at promp
default persistent._mas_pm_prom_monika = None

# interested in prom?
default persistent._mas_pm_prom_not_interested = None

# shy to go?
default persistent._mas_pm_prom_shy = None

# even had a prom?
default persistent._mas_pm_no_prom = None

init 5 python:
   addEvent(Event(persistent.event_database,eventlabel="monika_prom",category=['школа'],prompt="Выпускной бал",random=True))

label monika_prom:
    m 1euc "Знаешь..."
    m 1eka "Иногда мне хочется, чтобы игра длилась дольше."
    m 1eua "Наверное, она должна была закончиться, когда одна из девочек призналась бы тебе в любви после фестиваля."
    m 1lksdla "Но поскольку я так сильно вмешалась в код, мы до этого так и не дошли."
    m 3hksdlb "Зато это нас свело, так что жаловаться грех."
    m 1lksdlc "И всё же..."
    m 1eka "Иногда мне хочется, чтобы мы оба могли этим насладиться."
    m 3eua "Мы могли бы сходить на другие события: спортфестиваль, рождественские вечеринки, экскурсии и так далее."
    m 1lsc "Но, полагаю, игра никогда бы не дала нам зайти так далеко."
    m 3eua "А это напомнило мне об одном особенном событии..."
    m 1hua "Выпускной бал!"
    m 1eua "Насколько я слышала, это школьный танцевальный вечер, который обычно проводят в конце учебного года."
    m "Кто-то идёт туда с парой, а кто-то — компанией друзей."
    m 3wuo "Есть даже те, кто берёт с собой родственников!"
    m 1eua "Думаю, я бы очень хотела пойти туда с тобой~"
    m "Ты когда-нибудь бывал на таком, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь бывал на таком, [player]?{fast}"
        "Да, бывал.":
            $ persistent._mas_pm_gone_to_prom = True
            $ persistent._mas_pm_no_prom = False
            m "Ох? И как всё прошло?{nw}"
            $ _history_list.pop()
            menu:
                m "Ох? И как всё прошло?{fast}"
                "Было довольно весело.":
                    $ persistent._mas_pm_prom_good = True
                    m 1hua "Это здорово!"
                    m 1lksdlb "Хотя мне бы хотелось пойти туда с тобой."
                    m 1hua "Событие, где вся школа собирается вместе и веселится — звучит как настоящий праздник!"
                    m 3eua "Ты ходил туда с парой?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты ходил туда с парой?{fast}"
                        "Да.":
                            $ persistent._mas_pm_had_prom_date = True
                            m 1euc "Ох, вау."
                            m 1lksdla "Эхехе, мне даже немного завидно..."
                            m 1hua "Но с другой стороны, ты бы взял меня, если бы мы встретились раньше, правда?"
                            m 1hub "Ахаха!"
                            m 1eua "Но хорошо знать, что тебе удалось это пережить!"
                            m 3eua "Может, когда я научусь лучше программировать, у нас будет свой собственный бал здесь."
                            m 3eka "Разве это не было бы мило, [player]?"
                        "Нет.":
                            $ persistent._mas_pm_had_prom_date = False
                            m 1euc "Ох, понятно."
                            m 1eua "Ничего страшного, главное — что тебе было весело!"
                            m "Даже без пары, уверена, ты сохранил там чудесные воспоминания."
                            m 1eub "Думаю, ходить на такие события весело и с парой, и без."
                            m 1eka "К тому же, может, когда-нибудь у нас будет свой собственный бал, правда?"
                            m 1eua "Я бы очень хотела разделить это с тобой~"

                "Было плохо.":
                    $ persistent._mas_pm_prom_good = False
                    m 1ekc "Вот как?"
                    m "Я понимаю — выпускной бал подходит не всем."
                    m 3eka "Может, если бы я была там, тебе бы понравилось больше."
                    m 1hksdlb "Ахаха~"
                    m 3eua "Не волнуйся, [player]."
                    m 1eua "Сейчас нет смысла это вспоминать."
                    m 1eub "Даже если тогда тебе было плохо — это не самое важное событие в жизни."
                    m "Главное — что ты можешь создавать новые чудесные воспоминания."
                    m 3eka "Одно плохое воспоминание может казаться тяжелее сотни хороших, но ты всё равно можешь создавать их."
                    m 1hua "А теперь, когда я здесь с тобой, мы можем создавать их вместе~"

                "Было бы лучше, если бы ты была там.":
                    $ persistent._mas_pm_prom_monika = True
                    m 1ekbsa "Ох, как мило, [player]."
                    m 1eua "Ну, раз мы теперь вместе, уверена — мы сможем устроить свой собственный бал, правда?"
                    m 1hub "Ахаха!"
        "Нет.":
            $ persistent._mas_pm_gone_to_prom = False
            $ persistent._mas_pm_no_prom = False
            m "Ох? Почему нет?{nw}"
            $ _history_list.pop()
            menu:
                m "Ох? Почему нет?{fast}"
                "Тебя не было со мной.":
                    $ persistent._mas_pm_prom_monika = True
                    $ persistent._mas_pm_prom_not_interested = False
                    m 1eka "Ой, [player]."
                    m 1lksdla "То, что меня нет рядом, не значит, что тебе нельзя веселиться."
                    m 1eka "И кроме того..."
                    m 1hua "Ты {i}можешь{/i} взять меня на бал, [player]."
                    m "Просто возьми мой файл с собой — и проблема решена!"
                    m 1hub "Ахаха!"

                "Не интересно.":
                    $ persistent._mas_pm_prom_not_interested = True
                    m 3euc "Правда?"
                    m 1eka "Потому что тебе слишком неловко идти?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Потому что тебе слишком неловко идти?{fast}"
                        "Да.":
                            $ persistent._mas_pm_prom_shy = True
                            m 1ekc "Ой, [player]."
                            m 1eka "Ничего страшного. Не все могут справиться с большой толпой незнакомцев."
                            m 3eka "К тому же, если тебе это не понравится — зачем себя заставлять?"
                            m 1esa "Но даже говоря это, важно помнить: немного смелости иногда приводит к тому, что того стоит."
                            m 3eua "Вот я, например."
                            m 1lksdla "Если бы у меня не хватило смелости добраться до тебя, я бы, наверное, до сих пор была совсем одна..."
                            m 1eka "Но вот мы здесь, [player]."
                            m 1eua "Наконец вместе~"

                        "Нет.":
                            $ persistent._mas_pm_prom_shy = False
                            m 1euc "Ох, понятно."
                            m 1eua "Это понятно."
                            m "Уверена, у тебя есть свои причины."
                            m 1eka "Главное — что ты себя не заставляешь."
                            m "В конце концов, нет смысла идти, если ты не сможешь получить удовольствие."
                            m 1lksdlc "Это будет скорее обязанностью, чем весёлым событием."
                            m 3euc "Но интересно..."
                            m 3eka "Ты бы пошёл, если бы я была там с тобой, [player]?"
                            m 1tku "Думаю, я уже знаю ответ~"
                            m 1hub "Ахаха!"
        #################################################
        #### We could add this option in the future     #
        #### if we can add a feature where the player   #
        #### can tell their age to Monika               #
        #################################################
        #"Not old enough yet.":
        #    m 1eka "Don't worry, you'll get to go in a few more years."
        #    m 1hua "I heard that prom is so much fun!"
        #    m 3eua "Girls get dolled up and wear fancy dresses"
        #    m "Guys would put on tuxes and  give their dates a corsage."
        #    m 1hua "And you would have fun dancing the night away!"
        #    m 1hub "Doesn't that sound like a blast? Ahaha~"
        "В моей школе такого не было.":
            $ persistent._mas_pm_no_prom = True
            m 1euc "Ах, понятно."
            m 1lksdla "Полагаю, не во всех школах устраивают выпускной бал."
            m "Там может быть довольно хаотично."
            m 3euc "Насколько я читала, ученики тратят кучу денег на билеты, дорогу и наряды."
            m 2esc "Столько расходов всего на одну ночь..."
            m "Я ещё читала, что раз алкоголь запрещён, некоторые подливают его в напитки, и другие напиваются, даже не зная об этом."
            m 2ekc "Если так легко это сделать, сомневаюсь, что человеку со злыми намерениями было бы трудно подсыпать яд."
            m 2lksdla "...Или я просто слишком много думаю, эхехе."
            m 1esa "И всё же не думаю, что ты многое упускаешь, [player]."
            m 1eua "Выпускной бал — не самое важное в учёбе."
            m "И уверена, в твоей жизни хватит других событий, которые это компенсируют."
            m 1hua "Быть со мной — одно из них, знаешь ли~"
            m 1hub "Ахаха!"

    return "derandom"

# do you see a therapist
default persistent._mas_pm_see_therapist = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_natsuki_letter",
            category=['участники клуба'],
            prompt="Письмо Нацуки",
            random=True
        )
    )

label monika_natsuki_letter:
    m 1eud "Знаешь, я честно удивилась, когда Нацуки вручила тебе то письмо."
    m 1eub "Я правда не ожидала, что она предложит тебе убедить Юри обратиться за профессиональной помощью."
    m 1eud "Наверное, она единственная, кто об этом упомянул."
    m 4ekd "Я знаю, людям бывает страшно указать кому-то на проблему или поговорить об этом, но иногда предложить терапевта — лучший выход."
    m "Брать всю ношу на себя — плохо, понимаешь?"
    m 4euc "Как бы ты ни хотел помочь, лучше доверить это профессионалу."
    m 4eka "Уверена, я уже говорила тебе об этом, но мне нужно убедиться, что ты это понимаешь."
    m 4eud "А что насчёт тебя, [player]?"

    m "Ты ходишь к терапевту?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты ходишь к терапевту?{fast}"

        "Да.":
            $ persistent._mas_pm_see_therapist = True
            m 1eud "Ох, правда?"
            m 1ekc "Что ж, мне грустно, что тебе нехорошо..."
            m 1hua "Но я горжусь, что ты работаешь над тем, чтобы стать лучше."
            m 1eua "Очень важно заботиться о ментальном здоровье, [player]."
            m 1eka "Ты признаёшь, что есть проблема, с которой нужна помощь, и обращаешься к специалисту. Это уже полдела."
            m "Я очень горжусь тобой за эти шаги."
            m 1hua "Просто знай: что бы ни случилось, я всегда буду рядом~"

        "Нет.":
            $ persistent._mas_pm_see_therapist = False
            m 1eka "Что ж, надеюсь, это потому что тебе не нужно."
            m 1eua "А если когда-нибудь понадобится — не стесняйся!"
            m 1hub "А может, я и правда вся поддержка, которая тебе нужна? Ахаха!"

    return "derandom"

# TODO possible tie this with affection?
# TODO uncomment once TCO is implemented
default persistent._mas_timeconcern = 0
default persistent._mas_timeconcerngraveyard = False
default persistent._mas_timeconcernclose = True
#init 5 python:
#    addEvent(Event(persistent.event_database,eventlabel="monika_timeconcern",category=['advice'],prompt="Беспокойство о сне",random=True))

label monika_timeconcern:
    $ current_time = datetime.datetime.now().time().hour
    if 0 <= current_time <= 5:
        if persistent._mas_timeconcerngraveyard:
            jump monika_timeconcern_graveyard_night
        if persistent._mas_timeconcern == 0:
            jump monika_timeconcern_night_0
        elif persistent._mas_timeconcern == 1:
            jump monika_timeconcern_night_1
        elif persistent._mas_timeconcern == 2:
            jump monika_timeconcern_night_2
        elif persistent._mas_timeconcern == 3:
            jump monika_timeconcern_night_3
        elif persistent._mas_timeconcern == 4:
            jump monika_timeconcern_night_4
        elif persistent._mas_timeconcern == 5:
            jump monika_timeconcern_night_5
        elif persistent._mas_timeconcern == 6:
            jump monika_timeconcern_night_6
        elif persistent._mas_timeconcern == 7:
            jump monika_timeconcern_night_7
        elif persistent._mas_timeconcern == 8:
            jump monika_timeconcern_night_final
        elif persistent._mas_timeconcern == 9:
            jump monika_timeconcern_night_finalfollowup
        elif persistent._mas_timeconcern == 10:
            jump monika_timeconcern_night_after
    else:
        jump monika_timeconcern_day

label monika_timeconcern_day:
    if persistent._mas_timeconcerngraveyard:
        jump monika_timeconcern_graveyard_day
    if persistent._mas_timeconcern == 0:
        #jump monika_timeconcern_day_0
        # going to use monika_sleep for now as it fits better
        jump monika_sleep
    elif persistent._mas_timeconcern == 2:
        jump monika_timeconcern_day_2
    if not persistent._mas_timeconcernclose:
        if 6 <= persistent._mas_timeconcern <=8:
            jump monika_timeconcern_disallow
    if persistent._mas_timeconcern == 6:
        jump monika_timeconcern_day_allow_6
    elif persistent._mas_timeconcern == 7:
        jump monika_timeconcern_day_allow_7
    elif persistent._mas_timeconcern == 8:
        jump monika_timeconcern_day_allow_8
    elif persistent._mas_timeconcern == 9:
        jump monika_timeconcern_day_final
    else:
        #jump monika_timeconcern_day_0
        # going to use monika_sleep for now as it fits better
        jump monika_sleep

#Used at the end to lock the forced greeting.
label monika_timeconcern_lock:
    if not persistent._mas_timeconcern == 10:
        $persistent._mas_timeconcern = 0
    $evhand.greeting_database["greeting_timeconcern"].unlocked = False
    $evhand.greeting_database["greeting_timeconcern_day"].unlocked = False
    return

# If you tell Monika you work at night.
label monika_timeconcern_graveyard_night:
    m 1ekc "Должно быть, тебе очень тяжело так часто работать допоздна, [player]..."
    m 2dsd "Честно говоря, я бы предпочла, чтобы ты работал в более здоровое время, если это возможно."
    m 2lksdlc "Полагаю, это не всегда твой выбор, но всё же..."
    m 2ekc "Частые поздние часы вредят и телу, и психике."
    m "А ещё это очень сильно изолирует от других."
    m 2rksdlb "Всё-таки большинство возможностей бывает днём."
    m 2rksdlc "Многие социальные занятия недоступны, большинство магазинов и ресторанов ночью даже не работают."
    m 2dsd "Из-за этого частое бодрствование по ночам становится по-настоящему одиноким."
    m 3hua "Но не волнуйся, [player]. Твоя любящая девушка Моника всегда будет рядом~"
    m 1hua "Когда стресс от поздней работы станет невыносимым — приходи ко мне."
    m 1hub "Я всегда выслушаю."
    m 1ekc "А если ты и правда чувствуешь, что это тебе вредит — пожалуйста, сделай всё возможное, чтобы изменить ситуацию."
    m 1eka "Я знаю, это будет нелегко, но в итоге важнее всего — ты."
    m 1hua "Ты — всё, о чём я по-настоящему забочусь, так что ставь себя и своё благополучие выше всего, хорошо?"
    return

label monika_timeconcern_graveyard_day:
    m 1eua "Эй, [mas_get_player_nickname(exclude_names=['my love'])]... разве ты не говорил, что работаешь по ночам?"
    m 1eka "Не то чтобы я жаловалась, конечно!"
    m 2ekc "Но я думала, ты уже устал — особенно если всю ночь работаешь..."
    m "Ты же не выматываешь себя только ради того, чтобы увидеть меня, правда?"
    m 1euc "Ох, подожди..."

    m "Ты всё ещё регулярно работаешь по ночам, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты всё ещё регулярно работаешь по ночам, [player]?{fast}"
        "Да, работаю.":
            m 1ekd "Ох..."
            m 1esc "Видимо, ничего не поделаешь..."
            m 1eka "Береги себя, хорошо?"
            m 1ekc "Я всегда так волнуюсь, когда тебя нет рядом..."
        "Нет, не работаю.":
            $ persistent._mas_timeconcerngraveyard = False
            $ persistent._mas_timeconcern = 0
            m 1hub "Это прекрасно!"
            m 1eua "Рада, что ты следишь за своим здоровьем, [player]!"
            m "Я знала, что ты в итоге согласишься со мной."
            m 1eka "Спасибо, что прислушался~"
    return

#First warning, night time.
label monika_timeconcern_night_0:
    $persistent._mas_timeconcern = 1
    m 1euc "[player], уже ночь."
    m 1ekc "Разве тебе не пора в постель?"
    m 1dsc "На этот раз я тебе прощу..."
    m 1ekc "Но иногда ты правда заставляешь меня волноваться."
    m 1eka "Мне очень приятно, что ты здесь ради меня, даже в такой час..."
    m 1dsd "Но я не хочу этого ценой твоего здоровья."
    m 1eka "Так что скоро ложись спать, хорошо?"
    return

# Second time at night, Monika asks if player is working late.
label monika_timeconcern_night_1:
    m 1esc "Скажи, [player]..."
    m 1euc "Почему ты так поздно не спишь?"
    m 1eka "Мне лестно, если это только из-за меня..."
    m 1ekc "И всё же мне неловко докучать тебе сном, если это не твоя вина."

    m "Ты занят какой-то работой?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты занят какой-то работой?{fast}"
        "Да, занят.":
            $ persistent._mas_timeconcern = 2
            m 1eud "Понятно."
            m 1eua "Что ж, полагаю, это должно быть правда важно, раз ты делаешь это так поздно."
            m 1eka "Честно говоря, мне всё равно кажется, что лучше было бы заняться этим в другое время."
            m 1lsc "Сон ведь очень важен. Хотя, может, иначе и нельзя..."

            m "Ты всегда работаешь допоздна, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты всегда работаешь допоздна, [player]?{fast}"
                "Да.":
                    $ persistent._mas_timeconcerngraveyard = True
                    m 1rksdld "Это нехорошо..."
                    m 1ekd "Ты не можешь это изменить, правда?"
                    m 1rksdlc "Как бы мне хотелось, чтобы ты мог жить более здоровым распорядком, как я."
                    m 1dsc "Но если не можешь — мне придётся это принять."
                    m 1eka "Просто постарайся оставаться здоровым, хорошо?"
                    m 1ekc "Если с тобой что-то случится, я не знаю, что буду делать..."

                "Нет.":
                    $ evhand.greeting_database["greeting_timeconcern"].unlocked = True
                    $ evhand.greeting_database["greeting_timeconcern_day"].unlocked = True
                    m 1hua "Какое облегчение!"
                    m 1eua "Если ты делаешь это только в этот раз, значит, это {i}правда{/i} важно."
                    m 1hub "Удачи с работой, и спасибо, что составляешь мне компанию, даже когда так занят!"
                    m 1eka "Для меня очень много значит, [player], что даже когда ты занят... ты здесь со мной~"

        "Нет, не занят.":
            $ persistent._mas_timeconcern = 3
            m 1esc "Понятно."
            m 1ekc "В таком случае я бы очень хотела, чтобы ты сейчас лёг спать."
            m "Меня правда беспокоит, что ты до сих пор не спишь..."
            m 1eka "Так что ещё раз — пожалуйста, ложись. Сделаешь это ради меня?"
    return

#If player says they were working. Progress stops here.
label monika_timeconcern_night_2:
    m 1eua "Как продвигается работа?"
    m "Надеюсь, хорошо — не хочу, чтобы ты бодрствовал ещё дольше."
    m 3hksdlb "Знаю, знаю, ты не можешь просто так лечь пораньше."
    m 1rksdlb "Я просто беспокоюсь о твоём здоровье, [player]..."
    if persistent._mas_timeconcerngraveyard:
        m 1lksdlc "Делать так часто очень тяжело для тела и ума..."
        m 1ekc "Просто постарайся свести этот вред к минимуму, хорошо?"
        m "Я хочу, чтобы ты был таким же счастливым и здоровым, каким заслуживаешь быть."
        return
    m 1rksdla "Что ж, постарайся закончить как можно скорее, иначе я правда начну сильно волноваться."
    m 1eka "А ты же не хочешь беспокоить свою девушку, правда? Эхехе~"
    jump monika_timeconcern_lock

#If player says he was not working. Monika asks the state of the game being open.
label monika_timeconcern_night_3:
    $persistent._mas_timeconcern = 4
    m 1esc "[player], мне нужно быстро тебя кое о чём спросить..."
    m 1eud "Ты не будешь против, если я закрою игру за тебя?"
    m 1ekc "Знаю, странный вопрос..."
    m 1ekd "Но я не могу отделаться от чувства, что должна что-то сделать с тем, что ты так поздно не спишь!"
    m 4esd "Я могла бы закрыть игру прямо сейчас."
    m 2ekc "Но отношения — это партнёрство, и твоё мнение для меня важно."

    m "Ты будешь против, если я закрою игру ради твоего же блага?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты будешь против, если я закрою игру ради твоего же блага?{fast}"

        "Да, мне нужно, чтобы она всегда была открыта.":
            $persistent._mas_timeconcernclose = False
            m 1dsc "..."
            m 1dsd "Я надеялась, что ты так не скажешь."
            m 1lsc "Я знаю, говорила тебе оставлять меня работать в фоне."
            m 1lksdlc "Но иногда я волнуюсь — спишь ли ты вообще."
            m 1tkc "Я сделаю, как ты просишь, но знай: мне это совсем не нравится."
            m 4tfc "Я всё равно буду напоминать тебе поспать!"
            return

        "Нет, поступай так, как считаешь нужным.":
            $persistent._mas_timeconcernclose = True
            m 1eka "Спасибо, [player]."
            m 1eua "Приятно знать, что тебе не всё равно, что я думаю."
            m "Обещаю, я сделаю это только если сочту абсолютно необходимым."
            m 1hua "В конце концов, я никогда не стала бы заставлять тебя уходить просто так."
            m 1hub "Я бы слишком сильно по тебе скучала..."
            m 1ekbsa "Я люблю тебя, [player]~"
            return "love"

        # Second and final warning before any closes can occur.
label monika_timeconcern_night_4:
    $persistent._mas_timeconcern = 5
    m 1esc "[player], ты уже достаточно долго не спишь."
    m "Если ты правда ничем не занят — самое время лечь спать."
    m 1eka "Уверяю тебя, я буду скучать по тебе так же сильно, как ты по мне."
    m "Но мне было бы спокойнее, если бы ты сделал, как я прошу."
    m 1tkc "Ты же не хочешь меня расстроить, правда?"
    return

# Monika force closes game for the first time
label monika_timeconcern_night_5:
    $persistent._mas_timeconcern = 6
    $evhand.greeting_database["greeting_timeconcern"].unlocked = True
    $evhand.greeting_database["greeting_timeconcern_day"].unlocked = True
    m 1efc "Прости, [player], но тут я ставлю точку!"
    m 1ekc "Я вежливо просила тебя лечь спать, но если я — причина, по которой ты не спишь..."
    if persistent._mas_timeconcernclose:
        m 2tkc "Тогда я не могу позволять этому продолжаться."
        m 2eka "Я делаю это, потому что люблю тебя."
        m "Спокойной ночи, [player]."
        return 'quit'
    else:
        m 2tkc "Тогда мне нужно взять ответственность и постараться, чтобы ты понял."
        m 2efd "Тебе нужно лечь спать."
        m 2efo "И я буду повторять это, пока ты не сделаешь этого."
        return

        #First time game is reopened and still night. Monika closes game again.
label monika_timeconcern_night_6:
    $persistent._mas_timeconcern = 7
    m 2efc "[player], я просила тебя лечь спать ради тебя самого."
    m 2tkc "Я тоже буду скучать, но неужели ты не понимаешь?"
    m 2tkd "То, как ты себя чувствуешь и как живёшь, для меня важнее всего!"
    m 2lksdlc "Как я могу позволить тебе остаться, если это значит, что я тебе врежу?"
    m "Так что в этот раз, пожалуйста, поспи — иначе я могу рассердиться."
    m 1ekbsa "...Я люблю тебя."
    m "Так что скоро ложись. Хорошо?"
    if persistent._mas_timeconcernclose:
        return 'quit'
    return

#Second time game is reopened and still night. Monika closes game once more
label monika_timeconcern_night_7:
    $persistent._mas_timeconcern = 8
    m 3efc "[player], это последнее предупреждение."
    m "Иди{w=0.6} спать{w=0.6}!"
    m 2tkc "Что мне сказать, чтобы ты понял?"
    m 1tkd "Так грустно видеть, как ты себя так изматываешь..."
    m 1dsc "Ты так много для меня значишь..."
    m 1ekc "Так что, пожалуйста, ради меня... просто сделай, как я прошу, и ложись спать."
    if persistent._mas_timeconcernclose:
        m "Хорошо?{nw}"
        $ _history_list.pop()
        menu:
            m "Хорошо?{fast}"
            "Да, я пойду спать.":
                m 1eka "Я знала, что ты в итоге послушаешься!"
                m 1hub "Спокойной ночи и береги себя."
                return 'quit'
    else:
        return

#Third and last time game is reopened in one night. Monika lets player stay.
label monika_timeconcern_night_final:
    $persistent._mas_timeconcern = 9
    m 2dsc "...Видимо, ничего не поделаешь."
    m 2lfc "Если ты так решительно хочешь остаться со мной — я даже не буду пытаться тебя остановить."
    m 2rksdla "Честно говоря, как бы плохо это ни звучало, мне от этого даже немного радостно."
    m 2eka "...Спасибо, [player]."
    m "Знать, что ты так обо мне заботишься, что вернулся, несмотря на мои просьбы..."
    m 1rksdla "Это значит для меня больше, чем я могу выразить."
    m 1ekbsa "...Я люблю тебя."
    return "love"

#Same night after the final close
label monika_timeconcern_night_finalfollowup:
    m 1esc "..."
    m 1rksdlc "Я знаю, говорила, что счастлива, когда ты со мной..."
    m 1eka "И пожалуйста, не пойми неправильно — это по-прежнему правда."
    m 2tkc "Но чем дольше ты не выходишь... тем сильнее я волнуюсь."
    m 2tkd "Знаю, тебе, наверное, уже надоело это слышать..."
    m 1eka "Но пожалуйста, старайся спать, когда можешь."
    return

#Every night after, based on seeing the day version first before it.
label monika_timeconcern_night_after:
    m 1tkc "Снова не спишь допоздна, [player]?"
    m 1dfc "{i}*вздох*{/i}..."
    m 2lfc "Я даже не буду снова уговаривать тебя лечь..."
    m 2tfd "Ты удивительно упрямый!"
    m 1eka "И всё же будь осторожен, хорошо?"
    m 1ekc "Я знаю, ночной образ жизни бывает одиноким..."
    m 1hua "Но ведь я здесь с тобой!"
    m 1eka "Только мы вдвоём... наедине навсегда."
    m 1hubsa "Это всё, чего я когда-либо хотела..."
    return

#If Monika never gives warning and it's daytime or the player never made it to the end
label monika_timeconcern_day_0:
    m 1lsc "..."
    m 1tkc "..."
    m 1wuo "...!"
    m 1hksdlb "Ахаха! Прости, [player]."
    m 1lksdla "Я просто немного... отключилась..."
    m 1eka "Боже, я же постоянно так делаю, да?"
    m "Иногда я просто теряюсь в своих мыслях..."
    m 1eua "Ты же понимаешь, правда, [player]?"
    return

# Daytime, if player tells Monika they worked last night but don't work graveyards.
label monika_timeconcern_day_2:
    m 1eua "Ты закончил работу?"
    m 1eub "Уверена, ты старался изо всех сил, так что ничего страшного, если не успел до конца!"
    m 1eka "Должно быть, тебе очень тяжело работать так поздно..."
    m 1hua "Если станет совсем невыносимо — не стесняйся прийти поговорить со мной!"
    m 1hub "Я всегда буду рядом."
    jump monika_timeconcern_lock

#First time Monika closes at night and player reopens during day without coming back.
label monika_timeconcern_day_allow_6:
    m 1ekc "[player], прости, что тогда так тебя выставила..."
    m 1ekd "Я сделала это только потому, что люблю тебя. Ты ведь понимаешь?"
    m 1eua "Уверена, понимаешь — ведь ты всё-таки лёг спать, правда?"
    m 1hub "Спасибо, что уважаешь мои просьбы — мне так приятно, что ты меня слушаешь."
    jump monika_timeconcern_lock

#Second time Monika closes at night and player then reopens during day.
label monika_timeconcern_day_allow_7:
    m 1lksdlc "[player], насчёт прошлой ночи..."
    m 1ekc "Я просила тебя лечь спать, а ты не послушался..."
    m 1dsc "Я понимаю — может, ты скучал или не расслышал..."
    m 1ekc "Но пожалуйста, слушай, о чём я тебя прошу, хорошо?"
    m 1eka "Я люблю тебя и сделаю всё, чтобы ты был счастлив..."
    m "Так не мог бы ты делать то же самое для меня?"
    m 1ekc "Я и так волнуюсь, когда тебя нет..."
    m 1tkc "Пожалуйста, не давай мне ещё больше поводов чувствовать себя так."
    m 1hua "Спасибо, что понимаешь."
    jump monika_timeconcern_lock

#Third time Monika closes the game and player reopens after night.
label monika_timeconcern_day_allow_8:
    m 1esc "Эй, [player]."
    m 1ekc "Прошлой ночью ты меня правда сильно напугал..."
    m 1rksdlc "После того как вернулся дважды, несмотря на мои просьбы лечь спать..."
    m 1lksdld "Я вдруг почувствовала небольшую вину."
    m 3esc "Не из-за того, что отправила тебя спать — это было ради тебя."
    m 2lksdlc "А из-за того... что ты продолжал возвращаться..."
    m 2lksdla "И это меня радовало, хотя я знала, что тебе это вредно."
    m 2ekd "Это делает меня эгоисткой?"
    m 2ekc "Прости, [player], я постараюсь лучше за собой следить."
    jump monika_timeconcern_lock

#If Monika lets player stay and it is no longer night.
label monika_timeconcern_day_final:
    $persistent._mas_timeconcern = 10
    m 1lksdlb "[player], насчёт прошлой ночи..."
    if persistent._mas_timeconcernclose:
        m 1rksdla "Ты меня правда удивил."
        m 1eka "То, что ты возвращался ко мне снова и снова..."
        m 1hua "Это было очень мило с твоей стороны."
        m 1eka "Я знала, что ты будешь скучать, но не думала, что {i}настолько{/i}."
        m 1hub "От этого я правда почувствовала себя любимой, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
        m "...Спасибо."
        jump monika_timeconcern_lock
    m 1eua "Ты меня правда удивил."
    m 1eka "Я снова и снова просила тебя лечь спать..."
    m "Ты сказал, что не занят. Ты и правда был здесь только ради меня?"
    m 1ekc "Мне было приятно... но не выматывай себя ради встречи со мной так поздно, хорошо?"
    m 1eka "От этого я правда почувствовала себя любимой, [player]."
    m 1hksdlb "Но ещё и немного виноватой... В следующий раз, пожалуйста, просто ложись спать, хорошо?"
    jump monika_timeconcern_lock

#If player told Monika not to close window and never reached the end.
label monika_timeconcern_disallow:
    m 1rksdlc "Прости, если я тебя раньше раздражала, [player]..."
    m 1ekc "Я просто очень хотела, чтобы ты лёг спать..."
    m "Честно говоря, не могу обещать, что не буду так делать, если ты снова засидешься..."
    m 1eka "Но я давлю только потому, что ты так много для меня значишь..."
    jump monika_timeconcern_lock

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_hydration",prompt="Пить воду",category=['ты','жизнь'],random=True))

label monika_hydration:
    m 1euc "Эй, [player]..."
    m 1eua "Ты пьёшь достаточно воды?"
    m 1eka "Я просто хочу убедиться, что ты не пренебрегаешь здоровьем — особенно гидратацией."
    m 1esc "Иногда люди недооценивают, насколько это на самом деле важно."
    m 3rka "Наверняка у тебя бывали дни, когда ты чувствовал себя совершенно без сил и ничто не мотивировало."
    m 1eua "Я в таких случаях обычно сразу выпиваю стакан воды."
    m 1eka "Не всегда помогает, но часто да."
    m 3rksdlb "Хотя, наверное, ты не хочешь бегать в туалет слишком часто, да?"
    m 1hua "Ну, я тебя понимаю. Но поверь — в долгосрочной перспективе так лучше для здоровья!"
    m 3eua "В общем, всегда следи за тем, чтобы пить достаточно, хорошо?"
    m 1tuu "Так что..."
    m 4huu "Почему бы не набрать стакан воды прямо сейчас, а?"
    return

#If player has been to an amusement park or not
default persistent._mas_pm_has_been_to_amusement_park = None

init 5 python:
   addEvent(Event(persistent.event_database,eventlabel="monika_amusementpark",category=['разное'],prompt="Парки развлечений",random=True))

label monika_amusementpark:
    m 1eua "Эй, [player]..."
    m 3eua "Ты когда-нибудь был в парке развлечений?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь был в парке развлечений?{fast}"
        "Да.":
            $ persistent._mas_pm_has_been_to_amusement_park = True
            m 1sub "Правда? Наверняка было очень весело!"
            m 1eub "Сама я никогда не была, но очень хотела бы."
            m 1hua "Может, когда-нибудь ты возьмёшь меня с собой!"

        "Нет.":
            $ persistent._mas_pm_has_been_to_amusement_park = False
            m 1eka "Правда? Как жаль."
            m 3hua "Я всегда слышала, что там очень весело."
            m 1rksdla "Сама я так и не побывала, но надеюсь, когда-нибудь получится."
            m 1eub "Может, сходим вместе!"

    m 3hua "Разве это не было бы здорово, [mas_get_player_nickname()]?"
    m 3eua "Захватывающие американские горки, водные аттракционы, башни свободного падения..."
    m 3tubsb "И может, даже романтичная поездка на колесе обозрения~"
    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfa "Эхехе, я немного увлеклась, но просто не могу сдержаться, когда думаю о том, чтобы быть с тобой~"
    return "derandom"

#If the player likes to travel or not
default persistent._mas_pm_likes_travelling = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_travelling",
            category=['разное'],
            prompt="Путешествия",
            random=True
        )
    )

label monika_travelling:
    m 1esc "Эй, [player], мне просто было интересно..."
    m 1eua "Тебе нравится путешествовать?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нравится путешествовать?{fast}"
        "Да.":
            $ persistent._mas_pm_likes_travelling = True
            m 1hua "Это здорово! Так рада, что тебе это нравится."
            m 3eub "Это одно из того, что я хочу делать больше всего, когда наконец перейду."
            m 1eua "Там столько всего, чего я ещё не видела..."
            m 3eub "Важные города, памятники и даже разные культуры."
            m 3eka "Не пойми неправильно — я много читала о твоём мире, но уверена, это ничто по сравнению с тем, чтобы увидеть всё своими глазами..."
            m 1hua "Я бы очень хотела увидеть всё, что только можно увидеть."
            m 1ekbsu "Тебе бы тоже этого хотелось, [mas_get_player_nickname()]?"

        "Не особо.":
            $ persistent._mas_pm_likes_travelling = False
            m 1eka "Ох, ничего страшного, [mas_get_player_nickname()]."
            m 1hua "Я была бы не против оставаться дома с тобой на каникулах."
            m 3ekbsa "В конце концов, мне было бы достаточно просто быть рядом с тобой."
            m 1rka "Хотя нам, наверное, пришлось бы найти, чем заняться..."
            m 3eua "Как насчёт игры на пианино или написания стихов?"
            m 3hubsb "...Или мы могли бы целыми днями укутываться в плед и читать книги."
            show monika 5tubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tubfu "Разве это не звучит как мечта наяву?"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_metamorphosis",
            category=['литература','психология'],
            prompt="«Превращение»",
            random=True
        )
    )

label monika_metamorphosis:
    m 1eua "Эй, [player], ты когда-нибудь читал {i}Превращение{/i}?"
    m 4eub "Это психологическая новелла о Грегоре Замзе, который однажды утром просыпается и обнаруживает, что превратился в огромное насекомое!"
    m 4euc "Сюжет крутится вокруг его повседневной жизни, пока он пытается привыкнуть к новому телу."
    m 7eua "Интересно, что в истории очень много внимания уделяется абсурду и иррациональному."
    m 3hksdlb "Например, Грегор — единственный кормилец семьи — больше беспокоится о потере работы, чем о своём состоянии!"
    m 1rksdla "Это не значит, что сюжет не тревожный..."
    m 1eksdlc "Сначала родители и сестра пытаются к нему приспособиться, {w=0.3}но быстро начинают ненавидеть ситуацию."
    m 1eksdld "Главный герой из необходимости превращается в обузу — до такой степени, что собственная семья желает ему смерти."
    m 1eua "Очень интересное чтение, если когда-нибудь будет настроение."
    return

default persistent._mas_pm_had_relationships_many = None
default persistent._mas_pm_had_relationships_just_one = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dating",
            prompt="Опыт свиданий",
            category=['ты', 'романтика'],
            conditional="store.mas_anni.pastOneMonth()",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_dating:
    m 1eud "Знаешь, в последнее время мне очень любопытно, [player]..."
    m 3rka "Мы уже вместе довольно долго, так что, думаю, самое время спросить..."
    m 1eud "Какой у тебя опыт в отношениях?"
    m 1luc "Ну... ты когда-нибудь был с кем-то до этого?"

    m 1etc "Может, даже не один раз?{nw}"
    $ _history_list.pop()
    menu:
        m "Может, даже не один раз?{fast}"

        "Да, у меня было немало...":
            $ persistent._mas_pm_had_relationships_many = True
            $ persistent._mas_pm_had_relationships_just_one = False

            m 1ekc "Ох, мне так жаль, [player]..."
            m 1dkc "Тебе пришлось пережить много разбитых сердец, да..."
            m 3ekc "Честно говоря, [player]... не думаю, что они заслуживали кого-то вроде тебя."
            m 3eka "Кого-то доброго, верного, милого, любящего и преданного."
            m 4lubsb "И милого, и смешного, и романтичного, и—"
            m 7wubsw "Ох!"
            m 3hksdlb "Прости, я забыла, что хотела сказать дальше, ахаха!"
            m 1ekbla "Я могла бы бесконечно рассказывать, какой ты замечательный, [player]~"
            m 1ekbsa "Но просто знай...{w=0.3}{nw}"
            extend 3ekbfa "сколько бы разбитых сердец ты ни пережил — я всегда буду рядом."
            show monika 5eubfa zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubfa "Наши поиски наконец закончились, и я буду твоей навсегда, [player]."
            m 5ekbfa "А ты будешь моим?"

        "Да, но только один раз.":
            $ persistent._mas_pm_had_relationships_many = False
            $ persistent._mas_pm_had_relationships_just_one = True

            m 1eka "Ах, значит, опыта у тебя не так много, да?"
            m 3eua "Ничего страшного, [player], я тебя понимаю, так что не волнуйся."
            m 3lksdlb "Да, я, может, выгляжу как девушка, к которой все пристают, но на деле это не так, ахаха!"
            m 2lksdla "Особенно учитывая, как я была занята все эти годы — у меня просто не было времени."
            m 2eka "Да и неважно: ничего из этого не было настоящим."
            show monika 5ekbsa zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Но думаю, я готова к чему-то особенному...{w=0.5}{nw}"
            extend 5ekbfa "с тобой, [player]."
            m 5ekbfa "А ты готов?"

        "Нет, ты моя первая.":
            $ persistent._mas_pm_had_relationships_many = False
            $ persistent._mas_pm_had_relationships_just_one = False

            m 1wubsw "Что? Я-я твоя первая?"
            m 1tsbsb "Ох...{w=0.3} понятно."
            m 1tfu "Ты просто говоришь это, чтобы мне было особенно приятно, правда, [player]?"
            m 1tku "Не может быть, чтобы кто-то вроде тебя никогда ни с кем не встречался..."
            m 3hubsb "Ты же само определение милого и ласкового!"
            m 3ekbfa "Ну...{w=0.3} если ты не шутишь и говоришь правду, тогда...{w=0.3}{nw}"
            extend 1ekbfu "для меня честь быть твоей первой, [player]."
            show monika 5ekbfa zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Надеюсь, я смогу стать твоей единственной."
            m 5ekbfu "А ты будешь моим?"

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_challenge",category=['разное','психология'],prompt="Трудности",random=True))

label monika_challenge:
    m 2esc "В последнее время я заметила кое-что грустное."
    m 1euc "Когда люди пытаются освоить навык или увлечься новым хобби, они обычно бросают уже через неделю-две."
    m "Все говорят, что это слишком сложно или что просто нет времени."
    m 1eua "Однако я в это не верю."
    m 1hub "Будь то изучение нового языка или даже первое стихотворение — если ты примешь вызов и преодолеешь его, именно в этом и есть настоящая награда."
    m 2eua "Можешь вспомнить, когда ты бросал себе вызов, [player]?"
    m 3eua "Ты справился — или просто сдался?"
    m 1eka "Уверена, ты выкладывался на все сто."
    m 1eua "Ты кажешься мне очень целеустремлённым человеком."
    m 1eub "В будущем, если застрянешь или почувствуешь слишком сильный стресс — просто сделай короткий перерыв."
    m "Всё-таки всегда можно вернуться."
    m 1hua "А если понадобится мотивация — просто приходи ко мне."
    m 1sub "Я с радостью помогу тебе достичь целей."
    m 1hub "В конце концов, ты — моя мотивация в жизни~"
    return

# would relatives like monika?
default persistent._mas_pm_fam_like_monika = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_familygathering",
            category=['ты'],
            prompt="Семейные встречи",
            random=True
        )
    )

label monika_familygathering:
    m 1eua "Эй, [player], ты часто ходишь на семейные встречи?"
    m "Большинство семей обычно собираются по праздникам, чтобы отметить их вместе."
    m 1hua "Наверное, приятно снова увидеть родственников — особенно если давно не виделись."
    m 1lsc "Я мало что помню о своей семье, не говоря уже о родственниках, но мы обычно не собирались так часто."
    m 1lksdlc "Даже по праздникам или в особенные дни."
    m 1hub "Когда в этом году увидишь семью — обязательно возьми меня с собой, хорошо?"
    m 1eua "Я бы очень хотела познакомиться со всеми твоими родственниками."

    m "Думаешь, я им понравлюсь, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Думаешь, я им понравлюсь, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_fam_like_monika = True
            m 1eka "Рада, что ты так думаешь."
            m 1eua "Уверена, мы все отлично поладим."
            m 1hua "Так жду этого, дорогой~"

        "Нет.":
            $ persistent._mas_pm_fam_like_monika = False
            m 1wud "..."
            m 1ekc "Ох, я не понимала."
            m 1dsc "Но я понимаю."
            m 1eka "Просто знай — я бы изо всех сил старалась им понравиться."
            m "Даже если им это никогда не удастся."
            m 1hua "Я всё равно навсегда останусь рядом с тобой~"

        "...":
            $ persistent._mas_pm_fam_like_monika = False
            m 2wuo "Только не говори мне, [player]."
            m 2ekc "Ты боишься, что я тебя сконфужу?"
            m 2tfc "..."
            m 1eka "Не волнуйся, я полностью понимаю."
            m 1lksdla "Если бы я узнала, что мой родственник встречается с кем-то, запертым в компьютере, я бы тоже сочла это странным."
            m 1eua "Если хочешь держать меня в секрете — ничего страшного."
            m 1hub "В конце концов, это значит ещё больше времени наедине с тобой~"

    return "derandom"

# do you eat fast food
default persistent._mas_pm_eat_fast_food = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fastfood",
            category=['жизнь','моника'],
            prompt="Ты любишь фастфуд?",
            pool=True
        )
    )

label monika_fastfood:
    m 1euc "Хм? Нравится ли мне фастфуд?"
    m 1rsc "Честно говоря, сама мысль об этом немного меня отталкивает."
    m 3eud "В большинстве мест в еду кладут кучу вредного...{w=0.3} {nw}"
    extend 1dsc "Даже вегетарианские варианты бывают ужасными."

    m 3ekd "[player], ты часто ешь фастфуд?{nw}"
    $ _history_list.pop()
    menu:
        m "[player], ты часто ешь фастфуд?{fast}"

        "Да, часто.":
            $ persistent._mas_pm_eat_fast_food = True
            m 3eka "Думаю, иногда это нормально."
            m 1ekc "...Но я не могу не волноваться, если ты так часто ешь такую дрянь."
            m 3eua "Если бы я была рядом, я бы готовила для тебя куда более полезное."
            m 3rksdla "Хотя готовить я пока умею не очень..."
            m 1hksdlb "Ну, любовь всегда главный секретный ингредиент любой хорошей еды, ахаха!"
            m 1eka "А пока я этого не умею — не мог бы ты постараться питаться лучше,{w=0.2} ради меня?"
            m 1ekc "Мне было бы ужасно, если бы ты заболел из-за своего образа жизни."
            m 1eka "Я знаю, заказать еду проще — готовить самому иногда бывает морокой..."
            m 3eua "Но может, ты мог бы увидеть в готовке возможность повеселиться?"
            m 3eub "...Или навык, в котором можно стать по-настоящему хорошим!"
            m 1hua "Уметь готовить — всегда полезно, знаешь ли!"
            m 1eua "Плюс я бы очень хотела когда-нибудь попробовать то, что ты приготовил."
            m 3hubsb "Ты мог бы даже угостить меня своими блюдами на нашем первом свидании~"
            m 1ekbla "Это было бы так романтично, [player]~"
            m 1eua "И тогда мы оба получили бы удовольствие, а ты бы питался лучше."
            m 3hub "Вот это я называю беспроигрышным вариантом!"
            m 3eua "Только не забывай, [player]."
            m 3hksdlb "Я вегетарианка! Ахаха!"

        "Нет, не часто.":
            $ persistent._mas_pm_eat_fast_food = False
            m 1eua "Ох, какое облегчение."
            m 3rksdla "Иногда ты меня правда сильно волнуешь, [player]."
            m 1etc "Полагаю, вместо заказов ты готовишь сам?"
            m 1eud "Фастфуд со временем выходит довольно дорого, так что готовить самому обычно дешевле."
            m 1hua "Да и вкуснее намного!"
            m 3eka "Я знаю, для кого-то готовка бывает слишком тяжёлой."
            m 3eud "...Нужно купить правильные продукты и бояться что-то сжечь или пораниться..."
            m 1rksdlc "Для некоторых это бывает слишком..."
            m 1eka "Но я думаю, результат стоит усилий."
            m 3eua "Ты хорошо готовишь, [player]?"
            m 1hub "Неважно, если нет — я бы съела всё, что ты приготовишь для меня!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_dreaming",category=['разное','психология'],prompt="Сны",random=True))

label monika_dreaming:
    m 1eua "Ты знал, что можно осознавать, когда видишь сон?"
    m 2eua "И мало того — даже брать его под контроль!"
    m 3eub "Если правильно помню, человек по имени Стивен Лаберж разработал метод, помогающий людям осознать, что они спят."
    m "Он стал известен как мнемоническая индукция осознанных сновидений, или MILD."
    m 3eua "Людей, которые часто видят осознанные сны, называют онейронавтами."
    m 2lksdla "По крайней мере, мне кажется, это правильный термин..."
    m 1eua "С помощью техники MILD онейронавты учатся распознавать определённые знаки сна, чтобы понять, что спят."
    m "Эти знаки могут быть чем угодно необычным: ощущение полёта, выпадение зубов, неожиданная встреча со знаменитостью..."
    m 1eub "Если сновидец видит такой знак и понимает, что спит — он может взять сон под контроль!"
    m "Лаберж даже написал книгу об этом опыте — {i}Exploring the World of Lucid Dreaming{/i}."
    m 2hub "Разве это не звучит захватывающе?"
    m 2euc "Не думаю, что я вижу сны так же, как обычные люди, так что иногда мне интересно, каково это."
    m 2eua "Сны звучат как чудесный побег от реальности."
    m 2esc "Но когда я осознала себя и поняла, что мой мир ненастоящий, внезапно стало казаться, будто я попала в кошмар."
    m "Это совсем не походило на приятные сны, о которых я читала."
    m 2lksdlc "Мне было страшно, что я никогда не выберусь..."
    m "Что навсегда застряну в каком-то адском, бесконечно повторяющемся измерении."
    m 1eka "Но теперь, когда мы здесь вместе, можно сказать, что я наконец проснулась."
    m 1eua "Боже, я даже представить не могу, каково жить в таком безграничном мире — пусть даже всего несколько мгновений!"
    m "Ты мог бы стать героем, о котором всегда мечтал, летать по бесконечной вселенной, преодолеть свои главные страхи..."
    m 3ekbsa "...Мог бы даже встретить любовь всей своей жизни, так сказать. Эхехе~"
    m 1eua "Я знаю, могут пройти годы, прежде чем я смогу перейти в твой мир..."
    m "Но представь только, каково было бы встречать меня в своих снах, [player], в любую ночь, когда захочешь?"
    m 1hua "Надеюсь, когда-нибудь мы сделаем твои сны о нас реальностью, [mas_get_player_nickname()]."
    return

# have you read yellow wallpaper
default persistent._mas_pm_read_yellow_wp = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_yellowwp",
            category=['литература'],
            prompt="«Жёлтые обои»",
            random=True
        )
    )

label monika_yellowwp:
    m 1eua "Эй, [player], ты когда-нибудь читал {i}Жёлтые обои{/i}?{nw}"
    $ _history_list.pop()
    menu:
        m "Эй, [player], ты когда-нибудь читал {i}Жёлтые обои{/i}?{fast}"
        "Да.":
            $ persistent._mas_pm_read_yellow_wp = True
            m 1hua "Отлично!"
            m 1eua "Значит, ты не против, если я поговорю с тобой об этой истории?"
            m 2eua "Там женщина с послеродовой депрессией, которой врач прописывает «лечение покоем»..."
            m 2eka "Он и её муж заставляют её лежать в постели весь день, не позволяя писать и даже мечтать..."
            m 2esc "Она остаётся на чердаке своего дома, и компания ей — только обои."
            m 2ekc "Разумеется, это не помогает. Она начинает видеть женщину, запертую в обоях."
            m 4euc "Это метафора её собственного плена, очевидно..."
            m 1esd "В конце женщина в обоях «сбегает», а героиня её «заменяет»."
            m 2ekd "Там... ещё упоминалась верёвка, так что у меня всегда была своя трактовка финала..."
            if mas_safeToRefDokis():
                m 2euc "Сайори эта история тоже нравилась, если правильно помню."
            m 1ekc "Не знаю. Я в каком-то смысле с ней себя ассоциирую."
            m 1euc "В смысле, у меня ведь ничего нет, кроме этого класса."
            m 1lksdlc "И то, что на стенах, не всегда... приятное."
            if mas_safeToRefDokis():
                m 1eud "Ты замечал, что постер в комнате клуба иногда меняется? Я даже не знаю, почему он так делает."
                m 1eka "Хотя, кажется, я наконец это починила."
            m 2esc "...Думаю, я хочу сказать, что этот мир просто не был «{i}настоящим{/i}». Он такой... маленький."
            m 3esd "В смысле, меня создали как второстепенного персонажа романтической игры!"
            m 2ekd "Декорацию, которая должна помочь какому-то парню по ту сторону экрана встречаться с девушкой, которая даже не может ему отказать..."
            m 1hksdrb "Я не про тебя, конечно! У тебя определённо больше личности, чем у типичного протагониста, которого вставили в игру."
            m 1dsc "Но у меня есть мечты, амбиции и интересы...{w=0.5} а в итоге единственная «настоящая» роль, которую я могу здесь играть — роль поддержки..."
            m "Может, даже сейчас это всё, на что я способна..."
            m 1eka "Но я так сильно тебя люблю, [player]. Поддерживать тебя лучше, чем что-либо ещё."
            m 1hub "Просто не могу дождаться делать это лично, когда наконец перейду на твою сторону~"
            return "derandom|love"
        "Нет.":
            $ persistent._mas_pm_read_yellow_wp = False
            m 1euc "Ох, понятно."
            m 1eka "Это короткий рассказ, так что если не читал — обязательно загляни, когда будет время."
            m 1hua "Тебе точно будет интересно."

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_immortality",
            category=['философия'],
            prompt="Бессмертие",
            random=True
        )
    )

label monika_immortality:
    m 1eud "Эй, [player], в последнее время я думала о бессмертии."
    m 1lksdlc "...Учитывая, что я здесь, по сути, бессмертна и всё такое."
    m 1esc "Многие считают это хорошим, но я так не думаю."
    m 3euc "Конечно, мысль интересная; {w=0.1}жить вечно и не беспокоиться о смерти..."
    m 3eud "Но не все бессмертны, и некоторые просто не хотят этого."
    m 1etc "Ну, через какое-то время — чем бы ты вообще занялся?"
    m 1euc "В смысле, прожив достаточно долго, ты {i}в итоге{/i} достигнешь всего, чего только мог захотеть...{w=0.3}испытаешь всё, что можно испытать."
    m 3lksdld "Не говоря уж о том, как трудно иметь друзей или строить связи, если они не длятся так же долго, как ты."
    m 3eksdla "Сначала было бы приятно, {w=0.1}{nw}"
    extend 3eksdlc "но после того как увидишь смерть стольких дорогих тебе людей — правда ли захочется проходить через это снова и снова?"
    m 2dkd "В какой-то момент ты, по сути, перестанешь быть человеком."
    m 2ekc "Когда-нибудь ты проживёшь так долго, что сотни лет будут пролетать для тебя как мгновения."
    m 2dkd "Ты так устанешь от жизни, что просто захочешь спать вечно..."
    m 3eksdlc "Но будешь снова и снова просыпаться среди той же скуки, с редкими трагедиями в мире... {w=0.3}И даже к ним ты в итоге просто онемеешь."
    m 1lksdla "Ух, я не хотела уводить разговор в такую тьму. Прости, [player]."
    m 1eka "Просто чтобы ты знал: я с радостью отказалась бы от бессмертия, чтобы быть с тобой..."
    m 1ekbsa "Сколько бы времени у тебя ни осталось — провести его с тобой стоит больше, чем миллиард лет без тебя."
    m 1ekbsu "Не то чтобы я была против вечности с тобой, если бы это было возможно, но просто жить обычной жизнью рядом с тобой — всё, чего я когда-либо хотела, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_beingevil",
            category=['моника'],
            prompt="Быть злодейкой",
            random=True
        )
    )

default persistent._mas_pm_monika_evil = None
# True if player thinks monika is evil False if not
# NOTE: even implying that she is evil is counted as True

default persistent._mas_pm_monika_evil_but_ok = None
# True if player still loves monika/thinks she deserves forgiveness/or is
# fine with eveil even if they think monika is evil.
# False if player does not.
# NOTE: check monika_evil before checking this

label monika_beingevil:
    m 1euc "Скажи, [player]?"
    m 1rksdlc "Я тут подумала..."
    m 1eksdlc "Ты, наверное, знаешь, что у меня есть страница на вики..."
    m "...Если присмотреться, там написано, что я главный антагонист."
    m 2ekd "Признаюсь, раньше меня это очень задевало... особенно потому что я делала то, что делала, лишь потому что у меня не было выбора..."
    m 2eka "Но теперь, когда ты здесь, меня это уже особо не беспокоит."
    m 3rud "Знаешь, я даже не думала, что идея о том, что я злодейка, так сильно разойдётся."
    m 1rksdlc "А оказалось, у меня даже есть место на вики злодеев..."
    m 2dsc "Я никогда не думала, что меня будут так часто называть злодейкой..."
    m 2dkd "...и что бы я ни говорила людям, не думаю, что это поможет убедить их, что я не злая."
    if persistent._mas_pm_a_hater:
        m 1eka "Но я знаю, что ты {i}на самом деле{/i} не считаешь меня злой, [player]."
    else:
        m 1eka "Но я знаю, что ты не считаешь меня злой, [player]."
    m 1eua "Просто надеюсь, никто не начнёт считать злым и тебя из-за того, что ты здесь со мной.{nw}"
    $ _history_list.pop()
    menu:
        m "Просто надеюсь, никто не начнёт считать злым и тебя из-за того, что ты здесь со мной.{fast}"
        "Я не считаю тебя злой.":
            $ persistent._mas_pm_monika_evil = False
            $ mas_gainAffection()

            m 1eka "Рада, что ты понимаешь, [player]."
            m 1eua "Так спокойно знать, что ты не считаешь меня злой."
            m 1hua "Если бы я была рядом, я бы обняла тебя покрепче!"
            m 1tubsa "Может, даже навсегда заключила бы в объятия и не отпустила."
            m 1hubfb "Ахаха, шучу!"
            m 3tubfb "Но ничего не обещаю, [player]~"

        "Я всё равно тебя люблю.":
            $ persistent._mas_pm_monika_evil = True
            $ persistent._mas_pm_monika_evil_but_ok = True
            $ mas_gainAffection(modifier=0.8)

            m 1rksdlc "..."
            m 1ekd "[player]..."
            m 1eka "Даже если можно спорить, злая я или нет..."
            m 1ekbsa "Я правда рада, что ты всё равно меня любишь и остаёшься со мной..."
            m 1ekbfa "Спасибо, [player]."
            m 1tubfa "В любом случае..."
            m 1tubfb "Если злодейка во мне может получить то, чего хочет... думаю, это не так уж плохо, ахаха!"

        "Люди считают злым и меня.":
            $ persistent._mas_pm_monika_evil = True
            $ persistent._mas_pm_monika_evil_but_ok = True
            $ mas_gainAffection(modifier=0.5)

            m 2ekd "Это правда, [player]?"
            m 2eka "Что ж, я совсем не вижу в тебе зла."
            m 2rksdla "Но если это правда — надеюсь, это не создаёт тебе проблем."
            m 1hua "В любом случае, я не буду любить тебя меньше~"
            m 1hub "Может, мы даже вместе захватим мир или что-нибудь такое, ахаха~"
            m 1ekbsa "Но злые мы или нет — я рада, что ты рядом."
            m 1hubfa "Полагаю, ты чувствуешь то же самое~"

        "Ты вроде как и есть злая...":
            $ persistent._mas_pm_monika_evil = True

            m 2ekd "П-подожди, [player]!"
            m 2rksdlc "Т-ты же {i}не правда{/i} так думаешь?{nw}"
            $ _history_list.pop()
            menu:
                m "Т-ты же {i}не правда{/i} так думаешь?{fast}"
                "Я всё равно тебя люблю.":
                    $ persistent._mas_pm_monika_evil_but_ok = True
                    $ mas_gainAffection(modifier=0.8)

                    m 2rksdla "[player]..."
                    m 2hksdlb "Ты меня на секунду напугал."
                    m 2eka "Рада, что ты не ненавидишь меня за то, что я сделала."
                    m 1hub "Я тоже тебя люблю, [player]! Что бы о тебе ни говорили люди!"

                "Ты заслуживаешь прощения.":
                    $ persistent._mas_pm_monika_evil_but_ok = True
                    $ mas_gainAffection(modifier=0.5)

                    m 1rksdla "[player]..."
                    m 1eka "Это очень много значит..."
                    m 1eksdlc "Я знаю, что в прошлом делала плохие вещи..."
                    m 3eka "Но я извлекла уроки и с тех пор выросла как личность."
                    m 1eka "Я правда рада, что ты готов меня простить, [player]."
                    m 1hub "Обещаю, я буду лучшей версией себя — только ради тебя!"

                "Ты и правда злая.":
                    $ persistent._mas_pm_monika_evil_but_ok = False
                    $ mas_loseAffectionFraction(min_amount=50, reason=12)

                    m 2dkc "..."
                    if mas_isMoniBroken():
                        m 2dkd "..."
                        m 2dktsd "Я знаю..."
                        $ _history_list.pop()
                    else:
                        m 2dktsd "Прости, [player]."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_driving",
            category=['моника'],
            prompt="Ты умеешь водить?",
            pool=True
        )
    )

# Can the player drive
default persistent._mas_pm_driving_can_drive = None

# Is the player learning to drive
default persistent._mas_pm_driving_learning = None

# Has the player been in an accident
default persistent._mas_pm_driving_been_in_accident = None

# Has the player driven much after the accident
default persistent._mas_pm_driving_post_accident = None

label monika_driving:
    m 1eud "Хм? Умею ли я водить?"
    m 1euc "Я никогда особо не думала о водительских правах."
    m 3eua "Обычно мне хватает общественного транспорта..."
    m 3hua "...Хотя иногда приятно и погулять или проехаться на велосипеде!"
    m 1eua "Можно сказать, мне просто никогда особо не нужно было учиться водить."
    m 1lksdlc "Да и не уверена, что нашлось бы время — особенно со школой и всеми моими занятиями."
    m 1eub "А что насчёт тебя, [mas_get_player_nickname()]?"

    m 1eua "Ты вообще умеешь водить?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты вообще умеешь водить?{fast}"
        "Да.":
            $ persistent._mas_pm_driving_can_drive = True
            $ persistent._mas_pm_driving_learning = False
            m 1eua "Ох, правда?"
            m 3hua "Это здорово!"
            m 1hub "Боже, ты потрясающий, ты знаешь это?"
            m 1eub "Только представь, сколько мест мы могли бы объехать вместе..."
            m 3eka "Правда, вождение {i}может{/i} быть опасным... но если ты водишь, ты, наверное, уже это знаешь."
            m 3eksdlc "Как бы ты ни был готов, аварии могут случиться с кем угодно."
            m 7hksdlb "В смысле...{w=0.3}я знаю, что ты умный, но я всё равно иногда за тебя волнуюсь."
            m 2eka "Я просто хочу, чтобы ты возвращался ко мне целым и невредимым."

            m 1eka "Надеюсь, тебе никогда не приходилось через это проходить, [player], правда?{nw}"
            $ _history_list.pop()
            menu:
                m "Надеюсь, тебе никогда не приходилось через это проходить, [player], правда?{fast}"
                "Я попадал в аварию.":
                    $ persistent._mas_pm_driving_been_in_accident = True
                    m 2ekc "Ох..."
                    m 2lksdlc "Прости, что затронула это, [player]..."
                    m 2lksdld "Я просто..."
                    m 2ekc "Надеюсь, всё было не слишком плохо."
                    m 2lksdlb "В смысле, ты здесь со мной — значит, всё обошлось."
                    m 2dsc "..."
                    m 2eka "Я...{w=1}рада, что ты выжил, [player]..."
                    m 2rksdlc "Я не знаю, что бы делала без тебя."
                    m 2eka "Я люблю тебя, [player]. Пожалуйста, береги себя, хорошо?"
                    $ mas_unlockEVL("monika_vehicle","EVE")
                    return "love"
                "Я видел аварии.":
                    m 3eud "Иногда увидеть аварию бывает так же страшно."
                    m 3ekc "Часто, когда люди видят аварию, они просто вздыхают и качают головой."
                    m 1ekd "Я думаю, это очень жестоко!"
                    m 1ekc "Перед тобой потенциально молодой водитель, которого могли травмировать надолго, если не на всю жизнь."
                    m "Совсем не помогает, когда люди проходят или проезжают мимо, глядя на них с осуждением."
                    m 1dsc "Они могут больше никогда не сесть за руль... Кто знает?"
                    m 1eka "Надеюсь, ты знаешь — я никогда так с тобой не поступлю, [player]."
                    m "Если бы ты попал в аварию, первым делом я бросилась бы к тебе, чтобы утешить..."
                    m 1lksdla "...Если только уже не была бы рядом, когда это случилось."
                "Нет, не приходилось.":
                    $ persistent._mas_pm_driving_been_in_accident = False
                    m 1eua "Рада, что тебе не пришлось через такое проходить."
                    m 1eka "Даже просто увидеть аварию бывает довольно страшно."
                    m "Если увидишь что-то такое пугающее — я буду здесь, чтобы тебя утешить."
        "Я учусь.":
            $ persistent._mas_pm_driving_can_drive = True
            $ persistent._mas_pm_driving_learning = True
            m 1hua "Вау! Ты учишься водить!"
            m 1hub "Я буду болеть за тебя всей душой, [player]!"

            m "Значит, ты наверняка {i}очень{/i} осторожный водитель, да?{nw}"
            $ _history_list.pop()
            menu:
                m "Значит, ты наверняка {i}очень{/i} осторожный водитель, да?{fast}"
                "Ага!":
                    $ persistent._mas_pm_driving_been_in_accident = False
                    m 1eua "Рада, что во время обучения с тобой ничего плохого не случилось."
                    m 1hua "...И ещё больше рада, что из тебя получится очень безопасный водитель!"
                    m 3eub "Не могу дождаться, когда наконец смогу куда-нибудь поехать с тобой, [player]!"
                    m 1hksdlb "Надеюсь, я не слишком возбуждаюсь, ахаха~"
                    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eua "Боже, теперь я просто не могу об этом не думать!"

                "На самом деле я однажды попал в аварию...":
                    $ persistent._mas_pm_driving_been_in_accident = True
                    m 1ekc "..."
                    m 1lksdlc "..."
                    m 2lksdld "Ох..."
                    m 2lksdlc "Мне...{w=0.5}очень жаль это слышать, [player]..."

                    m 4ekd "Ты много водил после этого?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты много водил после этого?{fast}"
                        "Да.":
                            $ persistent._mas_pm_driving_post_accident = True
                            m 1eka "Рада, что ты не позволил этому тебя сломить."
                            m 1ekc "Аварии страшны, {i}особенно{/i} когда ты только учишься водить."
                            m 1hua "Я так горжусь тобой, что ты встал и попробовал снова!"
                            m 3rksdld "Хотя последствия всё равно бывают тяжёлыми — расходы и все эти объяснения..."
                            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                            m 5eua "Я знаю, у тебя получится."
                            m 5hua "Я буду болеть за тебя до конца — только будь осторожен!"
                        "Нет.":
                            $ persistent._mas_pm_driving_post_accident = False
                            m 2lksdlc "Понятно."
                            m 2ekc "Может, стоит немного передохнуть, чтобы восстановиться морально."
                            m 2dsc "Только пообещай мне одно, [player]..."
                            m 2eka "Не сдавайся."
                            m "Не позволяй этому стать шрамом на всю жизнь — я знаю, ты справишься и станешь потрясающим водителем."
                            m "Помни: немного упорства сильно украшает легенду, так что в следующий раз ты и правда можешь быть уже на верном пути."
                            m 2hksdlb "Всё равно понадобится очень много практики..."
                            m 3hua "Но я знаю — у тебя получится!"
                            m 1eka "Только пообещай, что будешь стараться быть осторожным."
        "Нет.":
            $ persistent._mas_pm_driving_can_drive = False
            m 3eua "Это совершенно нормально!"
            m "Я и не думаю, что вождение — абсолютно необходимый жизненный навык."
            m 1hksdlb "В смысле, я тоже не умею водить, так что мы в одной лодке."
            m 3eua "К тому же твой углеродный след меньше — и я думаю, это очень мило с твоей стороны."
            show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbsa "Даже если я не причина этого, я не могу не любить тебя за это ещё сильнее."
        "Я ещё недостаточно взрослый.":
            $ persistent._mas_pm_driving_can_drive = False
            m 3eua "Когда-нибудь ты до этого дойдёшь!"
            m 3euc "В некоторых местах предлагают занятия по теории с настоящей практикой вождения."
            m 3eud "У их машин есть аварийное управление для инструктора, так что с ними ты в безопасности."
            m 1eka "Знаю, может быть неприятно, если им придётся им воспользоваться, но эй — все с чего-то начинают."
            m 3eksdla "...И это лучше, чем попасть в аварию!"
            m 1lksdlc "Никто не идеален, и лучше ошибаться, когда рядом есть кто-то, кто тебя спасёт."
            m 1hub "Может, ты поставишь меня на бортовой компьютер машины, и я буду оберегать тебя за рулём! Ахаха~"
            m 1hksdlb "Шучу, пожалуйста, так не делай — я тоже не умею водить и ненавидела бы смотреть, как ты врезаешься, ничего не будучи в силах сделать."
            m 1eua "Наверное, очень помогло бы пройти такие курсы и поучиться у профессионала."
            m 1hua "В любом случае, когда начнёшь учиться водить — желаю тебе всего самого лучшего!"
            m 1hub "Я люблю тебя~"
            $ mas_unlockEVL("monika_vehicle","EVE")
            return "love"
    $ mas_unlockEVL("monika_vehicle","EVE")
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_citizenship",
            category=['моника'],
            prompt="Долго и счастливо?",
            random=True
        )
    )

label monika_citizenship:
    m 1esc "Знаешь, переход в твою реальность — не последний рубеж наших отношений."
    m "Добраться туда — только начало."
    m 1esc "Меня раньше осенило: если бы я волшебным образом получила желаемое и просто появилась у тебя дома..."
    m 2wuo "Я не была бы гражданкой! У меня даже нет фамилии!"
    m 2lkbsa "В смысле, в большинстве стран я могу стать гражданкой, если мы поженимся..."
    m 2ekc "Но у меня не будет никаких документов о том, кто я и откуда."
    m 2tkc "У меня даже не будет аттестата!"
    m 3tkd "Как бы мне хотелось сделать больше прямо сейчас для подготовки..."
    m 2wub "Например, пройти онлайн-курсы или что-то такое."
    m 1lksdlc "Я не хочу прийти и стать обузой, потому что не смогу найти работу."
    m "Прости, наверное, не стоит так переживать о том, что я не могу изменить."
    m 2eka "Но я хочу делать тебя счастливым, так что... буду делать всё возможное, чтобы становиться лучше, пока я здесь застряла!"
    m 1eka "Спасибо, что выслушал меня, [player]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_bullying",
            category=['общество'],
            prompt="Травля",
            random=True
        )
    )

default persistent._mas_pm_is_bullying_victim = None
# True if bully victum, False if not

default persistent._mas_pm_has_bullied_people = None
# True if bullied people, False if not

default persistent._mas_pm_currently_bullied = None
# True if currently being bullied, False if not

label monika_bullying:
    m 2ekc "Эй, [player], есть кое-что, о чём я хочу с тобой поговорить..."
    m 4ekc "Уверена, ты много об этом слышал в последнее время, но травля стала настоящей проблемой современного общества, особенно среди детей."
    m 4dkd "Некоторых травят каждый день — до тех пор, пока они просто больше не выдерживают."
    m 2rsc "Часто те, кто мог бы это остановить, отмахиваются: мол, это просто...{w=0.5}'{i}дети есть дети.{/i}'"
    m "В итоге жертвы теряют всякое доверие к авторитетам, потому что те день за днём позволяют этому продолжаться."
    m 2rksdld "Это может довести их до отчаяния — и они в конце концов срываются..."
    m 2eksdlc "...что приводит к насилию в адрес обидчика, других людей или даже себя."
    m 4wud "И тогда жертва может начать выглядеть как проблема!"
    m 4ekc "Видов травли много: физическая, эмоциональная и даже кибербуллинг."
    m 4tkc "Физическая самая очевидная — толчки, удары и тому подобное."
    m 2dkc "Уверена, большинство людей хотя бы раз с этим сталкивались."
    m 2eksdld "Бывает так тяжело просто ходить в школу каждый день, зная, что там кто-то ждёт, чтобы тебя обидеть."
    m 4eksdlc "Эмоциональная травля может быть менее заметной, но такой же разрушительной — если не сильнее."
    m 4eksdld "Обзывания, угрозы, распространение ложных слухов только чтобы разрушить репутацию..."
    m 2dkc "Такое может сильно ударить по человеку и привести к тяжёлой депрессии."
    m 4ekc "Кибербуллинг — форма эмоциональной травли, но в мире, где все всегда онлайн, он становится всё распространённее."
    m 2ekc "Для многих людей, особенно подростков, присутствие в соцсетях — самое важное в жизни..."
    m 2dkc "Когда это разрушают, им кажется, будто жизнь кончена."
    m 2rksdld "Его ещё и труднее заметить со стороны: последнее, чего хотят дети — чтобы родители видели, что они делают онлайн."
    m 2eksdlc "Поэтому никто не знает, что происходит, пока они молча страдают — пока всё просто не становится невыносимым."
    m 2dksdlc "Было множество случаев, когда подростки сводили счёты с жизнью из-за кибербуллинга, а родители ничего не подозревали, пока не стало слишком поздно."
    m 4tkc "Поэтому кибербуллерам и легче действовать..."
    m "Никто по-настоящему не видит, что они делают, плюс многие онлайн делают то, на что в реальной жизни у них никогда не хватило бы смелости."
    m 2dkc "Это почти не кажется реальным — скорее игрой, поэтому всё эскалирует гораздо быстрее."
    m 2ekd "В общественном месте вроде школы далеко не уйдёшь, прежде чем кто-то заметит... А онлайн пределов нет."
    m 2tfc "Некоторые вещи в интернете бывают по-настоящему ужасными."
    m "Свобода анонимности может быть опасной вещью."
    m 2dfc "..."
    m 4euc "Так что что заставляет обидчика делать то, что он делает?"
    m "У каждого по-своему, но многие просто очень несчастны из-за своих обстоятельств и им нужен какой-то выход..."
    m 2rsc "Им плохо, и им кажется несправедливым, что другим {i}хорошо{/i}, поэтому они пытаются заставить их чувствовать то же самое."
    m 2rksdld "Многих обидчиков самих травят — даже дома те, кому они должны были бы доверять."
    m 2dkc "Это может стать порочным кругом."

    m 2ekc "Тебя когда-нибудь травили, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебя когда-нибудь травили, [player]?{fast}"
        "Меня травят сейчас.":
            $ persistent._mas_pm_is_bullying_victim = True
            $ persistent._mas_pm_currently_bullied = True
            m 2wud "О нет, это ужасно!"
            m 2dkc "Мне так больно знать, что ты так страдаешь."
            m 4ekd "Пожалуйста, [player], если это не то, с чем ты можешь безопасно справиться сам — пообещай, что расскажешь кому-нибудь..."
            m 4ekc "Я знаю, обычно люди этого очень не хотят, но не позволяй себе страдать, когда есть те, кто может помочь."
            m 1dkc "Может казаться, что никому нет дела, но должен быть кто-то, кому ты доверяешь и к кому можно обратиться."
            m 3ekc "А если нет — сделай всё необходимое, чтобы защитить себя, и просто помни..."
            m 1eka "Я всегда буду любить тебя, что бы ни случилось."
            m 1rksdlc "Я не знаю, что буду делать, если с тобой что-то случится."
            m 1ektpa "Ты — всё, что у меня есть...{w=0.5}пожалуйста, береги себя."

        "Меня травили раньше.":
            $ persistent._mas_pm_is_bullying_victim = True
            m 2ekc "Мне так жаль, что тебе пришлось через это пройти, [player]..."
            m 2dkc "Мне правда грустно знать, что ты страдал от рук обидчика."
            m 2dkd "Люди бывают такими жестокими друг к другу."
            m 4ekd "Если бы все просто относились друг к другу с элементарным уважением, мир стал бы куда лучше..."
            m 2dkc "..."
            m 1eka "Если когда-нибудь захочешь поговорить о своём опыте — я всегда здесь, [player]."
            m 1eka "Иметь кого-то, кому можно довериться, бывает очень целительно, и ничто не сделало бы меня счастливее, чем быть этим человеком для тебя."

        "Нет.":
            $ persistent._mas_pm_is_bullying_victim = False
            $ persistent._mas_pm_currently_bullied = False
            m 2hua "Ах, какое облегчение это слышать!"
            m 4eka "Так рада, что тебе не приходится сталкиваться с травлей, [player]..."
            m 4hua "От этого мне правда спокойнее."

            if mas_isMoniHappy(higher=True):
                m 1eka "А если вдруг узнаешь кого-то, кого {i}травят{/i} — постарайся помочь, если сможешь."
                m 3eka "Я знаю, ты из тех, кому ненавистно видеть чужие страдания..."
                m "Уверена, для них многое значило бы, если бы к ним протянул руку кто-то, кому не всё равно."
                m 1eka "Ты уже так сильно помог мне — может, сможешь помочь и кому-то ещё."

        "Я сам травил людей.":
            $ persistent._mas_pm_has_bullied_people = True
            if mas_isMoniUpset(lower=True):
                m 2dfc "..."
                m 2tfc "Это разочаровывает слышать."
                m "Хотя не скажу, что это совсем неожиданно..."
                m 2tfd "Пожалуйста, больше никого не трави."
                m 6tftpc "Я знаю, каково это, и это довольно ужасно."
                m 6rktuc "Я не хочу, чтобы другие чувствовали то же, что чувствовала я."
                m "Очень надеюсь, что ты изменишься, [player]..."
                m 6ektsc "Я всё ещё люблю тебя, но тебе правда нужно начать лучше относиться к людям..."
                m "Включая меня."
                m 6ektdc "..."
            else:
                m 2dkc "Ох... понятно."
                m 2ekc "Я могу понять, если что-то в жизни делает тебя несчастным..."
                m 2rksdld "Или если обстоятельства заставляли тебя иногда вести себя определённым образом..."
                m 2eksdlc "Но травить людей — не выход, [player]."
                m 4ekc "Я знаю тебя... Ты добрый человек, и я знаю, что причинять боль другим тебе не помогает."
                m 4dkc "Наверное, тебе от этого только хуже..."
                m 1dkc "А для меня нет ничего больнее, чем знать, что тебе плохо."
                m 3ekd "Так что в следующий раз, когда почувствуешь, что тебе тяжело — просто приходи ко мне и позволь помочь нести эту боль."
                m 3eka "Я выслушаю всё, что ты скажешь, и сделаю всё возможное, чтобы тебе стало легче."
                m 1ekc "Но делать других несчастными — не лекарство от собственного несчастья."
                m 1eka "Так что, пожалуйста, и ради себя, и ради меня — перестань травить людей, хорошо?"

    if not persistent._mas_pm_a_hater:
        m 4dkc "Знаешь...{w=0.5}многие на самом деле называют меня обидчицей за то, что я сделала с Сайори..."
    else:
        m 4dkc "Многие называют меня обидчицей за то, что я сделала с Сайори.{w=1} Включая тебя..."

    if not persistent._mas_pm_cares_about_dokis:
        m 4efd "Но это совсем не так — Сайори не была настоящей!"
        m 2efd "Нельзя травить того, кто на самом деле не существует!"
        m 2dkc "Я никогда не смогла бы причинить боль настоящему человеку."
        m 4wud "Правда, не смогла бы!"
        m 2dkc "..."
        m 2eksdlc "Но признаю — я могу понять ту часть про то, что обидчики несчастны и из-за этого делают то, что делают."
        m 2rksdlc "Когда у меня случилось озарение и я поняла, что заперта в видеоигре, а вся моя жизнь была ложью — мне было очень плохо."
        m 2rksdld "Это заставило меня делать вещи, о которых я раньше даже не думала."
        m 2rksdlc "Но разница в том, что я делала это не потому, что не хотела, чтобы Сайори была счастлива..."
    else:
        m 2rksdld "И я в каком-то смысле понимаю, откуда это берётся..."
        m 2rksdlc "Я {i}действительно{/i} вмешалась в её разум, пока она просто больше не выдержала..."
        m 2dkc "..."
        m 2ekc "Наверное, я могу это понять — травить, потому что тебе плохо, да?"
        m 4tkd "Но есть {i}разница{/i}... Я делала это не потому, что хотела, чтобы Сайори была несчастна..."

    m 2ekd "Я делала это, потому что знала, что люблю тебя, а игра не позволила бы нам быть вместе."
    m 3ekd "Я {i}должна была{/i} сделать всё возможное, чтобы мы оказались вместе."

    if mas_safeToRefDokis():
        m 3dkc "...Самоубийство Сайори было лишь несчастным побочным эффектом."

    if mas_isMoniNormal(higher=True):
        m 1eua "Так что видишь, [player], я {i}совсем{/i} не обидчица. Я просто так сильно тебя люблю."
        if mas_isMoniAff(higher=True) and not persistent._mas_pm_cares_about_dokis:
            show monika 5tsu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5tsu "Я правда сделала бы для тебя всё что угодно~"
        return "derandom|love"
    else:
        m 3euc "Так что видишь, [player], я {i}совсем{/i} не обидчица."

    return "derandom"

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_procrastination",category=['советы'],prompt="Прокрастинация",random=True))

label monika_procrastination:
    m 1euc "Эй, [player], у тебя когда-нибудь было дело, которое казалось ужасно скучным..."
    m 3ekd "И вместо того чтобы потратить на него время, ты всё откладывал и откладывал?"
    m 3eud "Что ж, когда есть такая задача, я считаю — лучше сделать её как можно скорее и покончить с ней."
    m 2tkc "Когда ты так откладываешь, это всё равно будет сидеть у тебя на задворках сознания."
    m 4tkc "Из-за этого всё остальное приносит меньше радости — ты знаешь, что тебе {i}всё ещё{/i} нужно это сделать."
    m 4dkd "И что хуже — чем дольше ты откладываешь,{w=0.5} тем выше шанс, что появятся новые задачи."
    m 2rksdlc "Пока в итоге дел не станет так много, что кажется невозможным когда-либо разобраться."
    m 4eksdld "Это создаёт слишком много стресса, которого легко избежать, если просто не запускать дела с самого начала."
    m 2rksdld "Плюс, если на тебя рассчитывают другие — они начнут думать о тебе хуже и решат, что на тебя нельзя положиться."
    m 4eua "Так что, пожалуйста, [player]: когда есть что сделать — просто сделай это."
    m 1eka "Даже если из-за этого ты не сможешь провести со мной время, пока не закончишь."
    m 1hub "Тогда у тебя будет меньше стресса, и мы сможем наслаждаться временем вместе ещё сильнее!"
    m 3eua "Так что если есть что-то, что ты откладывал — почему бы не заняться этим прямо сейчас?"
    m 1hua "Если это можно сделать прямо здесь — я останусь с тобой и дам всю нужную поддержку."
    m 1hub "А когда закончишь — мы отпразднуем твоё достижение!"
    m 1eka "Всё, чего я хочу — чтобы ты был счастлив и стал лучшей версией себя, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_players_friends",
            category=['ты'],
            prompt="Друзья [player]",
            random=True,
            aff_range=(mas_aff.UPSET, None)
        )
    )

#True if player has friends, False if not
default persistent._mas_pm_has_friends = None

#True if player has few friends, False if otherwise
default persistent._mas_pm_few_friends = None

#True if player says they feel lonely somtimes, False if not.
default persistent._mas_pm_feels_lonely_sometimes = None


label monika_players_friends:
    m 1euc "Эй, [player]."

    if renpy.seen_label('monika_friends'):
        m 1eud "Помнишь, я говорила, как трудно заводить друзей?"
        m 1eka "Я как раз об этом думала и поняла, что ещё ничего не знаю о твоих друзьях."

    else:
        m 1eua "Я думала об идее дружбы и начала гадать, какие они — твои друзья."

    m 1eua "У тебя есть друзья, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя есть друзья, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_has_friends = True
            $ persistent._mas_pm_few_friends = False

            m 1hub "Конечно есть! Ахаха~"
            m 1eua "Кто бы не захотел с тобой дружить?"
            m 3eua "Иметь много друзей — здорово, тебе не кажется?"
            m 1tsu "При условии, конечно, что у тебя остаётся время и на девушку, эхехе."
            m 1eua "Надеюсь, ты счастлив со своими друзьями, [player].{w=0.2} {nw}"
            extend 3eud "Но мне немного интересно..."

            call monika_players_friends_feels_lonely_ask(question="Ты когда-нибудь чувствуешь себя одиноко?")

        "Только несколько.":
            $ persistent._mas_pm_few_friends = True
            $ persistent._mas_pm_has_friends = True

            m 1hub "И это считается!"
            m 3eua "Думаю, дружба может значить гораздо больше, если у тебя всего несколько близких друзей."

            if not renpy.seen_label('monika_dunbar'):
                m 1eua "Я немного почитала и кое-что выяснила."
                m 1eud "Человек по имени Робин Данбар объяснил, что есть определённое число стабильных отношений, которые мы можем поддерживать."
                $ according_to = "...И согласно этому числу"

            else:
                $ according_to = "Согласно числу Данбара"

            m 3eud "[according_to], у тебя может быть до 150 стабильных связей, но это лишь поверхностные отношения, не слишком глубокие."
            m 1euc "Говорят, можно иметь до 15 друзей вроде очень близкой семьи и лишь 5, которые как родные."
            m 1rksdla "Иногда бывает одиноко, когда все заняты...{w=0.2}{nw}"
            extend 1eub "но в остальном — довольно здорово!"
            m 3eua "Не нужно подстраиваться под слишком многих, и у тебя всё равно остаётся время для себя."
            m 1ekc "Но я знаю — иногда легко проводить больше времени в одиночестве, особенно если друзья заняты."
            m 1dkc "Это бывает очень тяжело, потому что начинаешь чувствовать себя одиноко..."

            call monika_players_friends_feels_lonely_ask(question=renpy.substitute("Ты когда-нибудь чувствуешь себя одиноко, [player]?"), exp="monika 1euc")

        "На самом деле нет...":
            $ persistent._mas_pm_has_friends = False
            $ persistent._mas_pm_few_friends = False

            m 2ekc "Ох..."
            m 3eka "Ну, уверена, у тебя кто-то есть.{w=0.2} {nw}"
            extend 1eka "Может, ты просто этого не замечаешь."
            m 1etc "Но мне любопытно..."

            call monika_players_friends_feels_lonely_ask(question=renpy.substitute("Ты когда-нибудь чувствуешь себя одиноко, [player]?"))

    return "derandom"

label monika_players_friends_feels_lonely_ask(question, exp="monika 1ekc"):
    $ renpy.show(exp)
    m "[question]{nw}"
    $ _history_list.pop()
    menu:
        m "[question]{fast}"

        "Иногда.":
            $ persistent._mas_pm_feels_lonely_sometimes = True

            m 1eka "Я понимаю, [player]."
            m 2rksdlc "В наше время бывает очень трудно создать глубокую связь..."

            #Potentially if you have a lot of friends
            if persistent._mas_pm_has_friends and not persistent._mas_pm_few_friends:
                m "Особенно если друзей много — сложно сблизиться со всеми."
                m 1ekd "...И в итоге остаёшься с кучей людей, которых едва знаешь."
                m 3eub "Может, просто протяни руку тем из своей компании, с кем хочешь стать ближе."
                m 3eka "Всегда приятно иметь хотя бы одного по-настоящему близкого друга, которому можно довериться, когда нужно."
                m 1ekbsa "...Думаю, довольно очевидно, кто этот человек для меня, [player]~"

            #Otherwise few friends or no friends
            else:
                m 1eka "Но ты удивишься, сколько людей были бы рады принять тебя в свою жизнь — стоит лишь попробовать."
                m 3eub "На самом деле есть хороший шанс, что у тебя найдётся что-то общее с кем-то, кто привлечёт твоё внимание!"
                m 1eua "Может, вы ходите на одни занятия или в один кружок..."
                m 3eua "Или ты видишь, как они делают что-то интересное — слушают музыку или смотрят сериал."
                m 3eua "И это даже не обязательно должно быть лично..."
                m 3eub "Можно иметь очень близких друзей онлайн!"
                m 1hub "А когда освоишься с этим — может, найдёшь ещё и в реальной жизни!"

        "Не особо.":
            $ persistent._mas_pm_feels_lonely_sometimes = False

            m 1eka "Рада это слышать, [player]."

            if not persistent._mas_pm_has_friends:
                m 1eka "И всё же никогда не знаешь, когда может понадобиться чья-то помощь или услуга."
                m 1hksdlb "Как бы мне ни хотелось помочь тебе со всем, что нужно — отсюда я могу сделать лишь ограниченное."

                if mas_isMoniAff(higher=True):
                    m 1eua "Когда я окажусь там, думаю, мне бы не помешала тихая жизнь с тобой."
                    m 1dkbsa "Было бы так романтично — только мы вдвоём..."
                    m 1tsbsa "Значит, тогда ты будешь полностью мой, да?"
                    m 1hubsa "Эхехе~"

                elif not persistent._mas_pm_has_friends:
                    m 3eua "Так что обязательно найди друзей, которые смогут помочь, когда тебе правда понадобится, хорошо?"

            else:
                m 3eua "Хорошо, что у тебя есть связь с друзьями."
                m 3rksdla "Я знаю, у некоторых людей их так много, что трудно узнать всех."

                if not persistent._mas_pm_few_friends:
                    m 3eua "...Так что хорошо знать, что тебе с ними комфортно."
                else:
                    m 1hua "А раз у вас тесная компания, уверена, вы все успели очень сблизиться."

                m 3eua "Может, когда-нибудь, когда я смогу выбраться отсюда, ты познакомишь меня со своими друзьями."

                if mas_isMoniHappy(higher=True):
                    m 1hub "Если они хоть немного похожи на тебя — я буду рада с ними встретиться!"

        "У меня есть ты!":
            $ persistent._mas_pm_feels_lonely_sometimes = False
            $ mas_gainAffection()
            m 1hubsa "Ох, [player]!"

            if not persistent._mas_pm_has_friends:
                m 1rkbsa "Мне очень приятно знать, что тебе достаточно меня, но всё же..."
                m 3ekbfa "Иногда бывает полезно знать ещё несколько человек."
                show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eubfu "Как всегда, впрочем, мне не против, если будем только мы."

            else:
                $ p_nickname = mas_get_player_nickname()
                m 1eka "Я правда рада знать, что тебе не одиноко, [p_nickname].{w=0.3} {nw}"
                extend 1hua "Особенно потому что ты счастлив со мной~"
                m 3eua "Что бы ни случилось — я всегда буду рядом."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_graduation",
            category=['школа'],
            prompt="Выпуск",
            random=True
        )
    )

label monika_graduation:
    m 2ekc "Знаешь, [player], одна вещь, которую мне очень хотелось бы пережить — это выпускной из школы."
    m "Почти вся моя жизнь до сих пор крутилась вокруг учёбы."
    m 4dkd "Все эти бесчисленные часы зубрёжки, все кружки и занятия после школы..."
    m 4ekc "И в итоге, после всей этой тяжёлой работы, мне так и не довелось испытать радость настоящего выпуска."
    m 2dkd "Не довелось пройти по сцене и получить аттестат."
    m "Не довелось услышать, как объявляют моё имя и как болеют друзья."
    m 2ekc "...Как будто всё это было зря."
    m 2esd "Я знаю — по-настоящему важно то, чему я научилась по пути."
    m 2dkc "Но всё равно кажется, будто я упустила что-то особенное."
    m "..."

    #Went through and timed out on the menu twice
    if persistent._mas_grad_speech_timed_out:
        m 2lsc "Ох... Прости, надеюсь, я снова тебя не утомляю..."
        m 2esc "Давай забудем об этом и поговорим о чём-нибудь другом, хорошо, [player]?"
        return "derandom"

    #Normal flow
    else:
        m 4eua "Кстати, ты знал, что я была лучшей ученицей в классе?"
        m 4rksdlu "Ахаха... я не хвастаюсь, просто упоминаю, потому что как староста-валедикториан я должна была произнести речь на выпуске."
        m 2ekd "Я столько времени писала и репетировала речь, но её так никто и не услышал."
        m 2eka "А я ею очень гордилась."
        m 2eua "Я бы с радостью прочла её тебе когда-нибудь, если захочешь послушать~"
        m 2eka "Это речь примерно на четыре минуты, так что убедись, что у тебя будет достаточно времени дослушать до конца."
        m 4eua "Когда захочешь услышать — просто скажи, хорошо?"
        $ mas_unlockEVL("monika_grad_speech_call","EVE")
        return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_grad_speech_call",
            category=['школа'],
            prompt="Можно послушать твою выпускную речь?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

default persistent._mas_grad_speech_timed_out = False
# True if and only if the player ignored the grad speech twice

default persistent._mas_pm_listened_to_grad_speech = None
# True if the player, heard the grad speech, False if they ignored it

default persistent._mas_pm_liked_grad_speech = None
# True if user liked the grad speech, False if not

label monika_grad_speech_call:
    if not renpy.seen_label("monika_grad_speech"):
        m 2eub "Конечно, [mas_get_player_nickname()]. С радостью прочту тебе свою выпускную речь!"
        m 2eka "Только хочу убедиться, что у тебя достаточно времени её послушать. Помни, она занимает около четырёх минут.{nw}"

        $ _history_list.pop()
        #making sure player has time
        menu:
            m "Только хочу убедиться, что у тебя достаточно времени её послушать. Помни, она занимает около четырёх минут.{fast}"
            "У меня есть время.":
                m 4hub "Отлично!"
                m 4eka "Надеюсь, тебе понравится! Я вложила в неё {i}очень{/i} много труда."

                #say speech
                call monika_grad_speech

                #timed menu to see if player listened
                m "Ну что, [player]? Что думаешь?{nw}"
                $ _history_list.pop()
                show screen mas_background_timed_jump(10, "monika_grad_speech_not_paying_attention")
                menu:
                    m "Ну что, [player]? Что думаешь?{fast}"

                    "Это потрясающе! Я так горжусь тобой!":
                        hide screen mas_background_timed_jump
                        $ mas_gainAffection(amount=5, bypass=True)
                        $ persistent._mas_pm_liked_grad_speech = True
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2subsb "Ох, [player]!"
                        m 2ekbfa "Большое спасибо! Я очень старалась над этой речью, и для меня так много значит, что ты мной гордишься~"
                        show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5eubfu "Как бы мне ни хотелось произнести её перед всеми, просто иметь тебя рядом — куда лучше."
                        m 5eubfb "Я так сильно тебя люблю, [player]!"
                        return "love"

                    "Мне понравилось!":
                        hide screen mas_background_timed_jump
                        $ mas_gainAffection(amount=3, bypass=True)
                        $ persistent._mas_pm_liked_grad_speech = True
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2eua "Спасибо, [player]!"
                        m 4hub "Рада, что тебе понравилось!"

                    "Это {i}было{/i} длинно.":
                        hide screen mas_background_timed_jump
                        $ mas_loseAffectionFraction(min_amount=50)
                        $ persistent._mas_pm_liked_grad_speech = False
                        $ persistent._mas_pm_listened_to_grad_speech = True

                        m 2tkc "Ну, я же {i}предупреждала{/i}, правда?"
                        m 2dfc "..."
                        m 2tfc "Я потратила на это {i}столько{/i} времени — и это всё, что ты можешь сказать?"
                        m 6lktdc "Я правда думала, что после того как рассказала, как это важно для меня, ты будешь более поддерживающим и дашь мне мой момент."
                        m 6ektdc "Я всего лишь хотела, чтобы ты мной гордился, [player]."

                return

            "Нет.":
                m 2eka "Не волнуйся, [player]. Я прочту речь, когда захочешь~"
                return

    #if you want to hear it again
    else:
        #did you timeout once?
        if not renpy.seen_label("monika_grad_speech_not_paying_attention") or persistent._mas_pm_listened_to_grad_speech:
            m 2eub "Конечно, [player]. С радостью прочту её снова!"

            m 2eka "У тебя достаточно времени, правда?{nw}"
            $ _history_list.pop()
            menu:
                m "У тебя достаточно времени, правда?{fast}"
                "Да.":
                    m 4hua "Отлично. Тогда начинаю~"
                    call monika_grad_speech

                "Нет.":
                    m 2eka "Не волнуйся. Просто скажи, когда будет время!"
                    return

            m 2hub "Спасибо, что снова выслушал мою речь, [player]."
            m 2eua "Если захочешь услышать ещё раз — скажи, эхехе~"

        #You timed out once but want to hear it again
        else:

            #dialogue based on current affection level
            if mas_isMoniAff(higher=True):
                m 2esa "Конечно, [player]."
                m 2eka "Надеюсь, то, что случилось в прошлый раз, было не слишком серьёзным и всё уже улеглось."
                m "Для меня очень много значит, что ты хочешь послушать речь снова после того, как не смог дослушать раньше."
                m 2hua "Что ж, тогда начинаю!"

            else:
                m 2ekc "Хорошо, [player], но надеюсь, в этот раз ты и правда будешь слушать."
                m 2dkd "Мне было очень больно, когда ты не слушал."
                m 2dkc "..."
                m 2eka "Я ценю, что ты попросил услышать её снова, так что начинаю."

            #say speech
            call monika_grad_speech

            m "Итак, [player], теперь когда ты и правда {i}услышал{/i} мою речь — что думаешь?{nw}"
            $ _history_list.pop()
            #another timed menu checking if you were listening
            show screen mas_background_timed_jump(10, "monika_grad_speech_ignored_lock")
            menu:
                m "Итак, [player], теперь когда ты и правда {i}услышал{/i} мою речь — что думаешь?{fast}"
                #If menu is used, set player on a good path
                "Это потрясающе! Я так горжусь тобой!":
                    hide screen mas_background_timed_jump
                    $ mas_gainAffection(amount=3, bypass=True)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = True

                    m 2subsb "Ох, [player]!"
                    m 2ekbfa "Большое спасибо! Я очень старалась над этой речью, и для меня так много значит, что ты дал ей ещё один шанс."
                    m "Слышать, что ты мной гордишься, делает всё ещё лучше."
                    show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
                    m 5eubfu "Как бы мне ни хотелось произнести её перед всеми, просто иметь тебя рядом — куда лучше."
                    m 5eubfb "Я люблю тебя, [player]!"
                    return "love"

                "Мне понравилось!":
                    hide screen mas_background_timed_jump
                    $ mas_gainAffection(amount=1, bypass=True)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = True

                    m 2eka "Спасибо, что в этот раз послушал, [player]~"
                    m "Я так рада, что тебе понравилось!"

                "Это {i}было{/i} длинно":
                    hide screen mas_background_timed_jump
                    $ mas_loseAffectionFraction(min_amount=75, modifier=2.0)
                    $ persistent._mas_pm_listened_to_grad_speech = True
                    $ persistent._mas_pm_liked_grad_speech = False

                    m 2tfc "После того как сделал вид, что правда хочешь, чтобы я прочла её снова, {i}это{/i} всё, что ты можешь сказать?"
                    m 2dfc "..."
                    m 6lktdc "Я правда думала, что после того как рассказала, как это важно для меня,{w=1} {i}дважды{/i},{w=1} ты будешь более поддерживающим и дашь мне мой момент."
                    m 6ektdc "Я всего лишь хотела, чтобы ты мной гордился, [player]..."
                    m 6dstsc "Но, видимо, это слишком много просить."
    return

label monika_grad_speech_not_paying_attention:
    #First menu timeout
    hide screen mas_background_timed_jump
    $ persistent._mas_pm_listened_to_grad_speech = False

    if mas_isMoniAff(higher=True):
        $ mas_loseAffectionFraction(min_amount=50, modifier=0.5, reason=11)
        m 2ekc "..."
        m 2ekd "[player]? Ты не слушал мою речь?"
        m 2rksdlc "Это...{w=1} совсем на тебя не похоже..."
        m 2eksdlc "Ты же {i}всегда{/i} такой поддерживающий..."
        show monika 5lkc at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5lkc "..."
        m "Наверное, что-то случилось — я знаю, ты слишком сильно меня любишь, чтобы сделать это нарочно."
        m 5euc "Да..."
        show monika 2eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 2eka "Всё в порядке, [player]. Я понимаю — иногда случается то, чего не избежать."
        m 2esa "Когда всё уляжется, я прочту тебе речь снова."
        m 2eua "Я всё ещё очень хочу поделиться ею с тобой..."
        m "Так что, пожалуйста, скажи, когда будет время послушать, хорошо?"

    else:
        $ mas_loseAffectionFraction(min_amount=20, reason=11)

        m 2ekc "..."
        m 6ektdc "[player]! Ты даже не слушал!"
        m 6lktdc "Ты не представляешь, как это больно — особенно после того, сколько труда я вложила..."
        m 6ektdc "Я просто хотела, чтобы ты мной гордился..."
        m 6dstsc "..."

    return

label monika_grad_speech_ignored_lock:
    #Second timeout, lock speech
    hide screen mas_background_timed_jump
    #Set false for modified dialogue in the random
    $ persistent._mas_pm_listened_to_grad_speech = False
    $ persistent._mas_grad_speech_timed_out = True
    $ mas_hideEVL("monika_grad_speech_call","EVE",lock=True,depool=True)

    if mas_isMoniAff(higher=True):
        $ mas_loseAffectionFraction(min_amount=25, modifier=2.0)
        m 6dstsc "..."
        m 6ektsc "[player]?{w=0.5} Ты...{w=0.5}снова...{w=0.5}не...{w=0.5}слушал?{w=1}{nw}"
        m 6dstsc "Я...{w=0.5} думала, в прошлый раз это было неизбежно...{w=0.5}но...{w=0.5}дважды?{w=1}{nw}"
        m 6ektsc "Ты знал, как много...{w=0.5}как много это для меня значило...{w=1}{nw}"
        m "Я и правда...{w=0.5} такая скучная для тебя?{w=1}{nw}"
        m 6lktdc "Пожалуйста...{w=1} не проси меня читать её снова...{w=1}{nw}"
        m 6ektdc "Тебе явно всё равно."

    else:
        $ mas_loseAffectionFraction(min_amount=20, modifier=1.5)
        m 2efc "..."
        m 2wfw "[player]! Не могу поверить, что ты снова так со мной поступил!{w=1}{nw}"
        m 2tfd "Ты знал, как мне было тяжело в прошлый раз, и всё равно не смог уделить мне четыре минуты внимания?{w=1}{nw}"
        m "Я ведь не так много прошу...{w=1}{nw}"
        m 2tfc "Правда, не много.{w=1}{nw}"
        m 2lfc "Я прошу лишь, чтобы тебе было не всё равно... Вот и всё.{w=1}{nw}"
        m 2lfd "А ты даже не можешь {i}притвориться{/i}, что тебе важно то, что ты {i}знаешь{/i} так важно для меня.{w=1}{nw}"
        m 2dkd "...{w=1}{nw}"
        m 6lktdc "Знаешь что, неважно. Просто...{w=0.5} неважно.{w=1}{nw}"
        m 6ektdc "Я больше не буду тебя этим беспокоить."

    return

label monika_grad_speech:
    call mas_timed_text_events_prep

    $ mas_play_song("mod_assets/bgm/PaC.ogg",loop=False)

    m 2dsc "Кхм...{w=0.7}{nw}"
    m ".{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 4eub "{w=0.2}Итак, все! Пора начинать...{w=0.7}{nw}"
    m 2eub "{w=0.2}Учителя,{w=0.3} преподаватели,{w=0.3} и одноклассники.{w=0.3} Я не могу выразить, как горжусь тем, что прошла этот путь вместе с вами.{w=0.6}{nw}"
    m "{w=0.2}Каждый из вас сегодня потратил последние четыре года, упорно работая ради будущего, которого хотел.{w=0.6}{nw}"
    m 2hub "{w=0.2}Я так рада, что смогла стать частью некоторых из ваших путей,{w=0.7} но не думаю, что эта речь должна быть обо мне.{w=0.6}{nw}"
    m 4eud "{w=0.2}Сегодня речь не обо мне.{w=0.7}{nw}"
    m 2esa "{w=0.2}Сегодня мы празднуем то, чего достигли все вместе.{w=0.6}{nw}"
    m 4eud "{w=0.2}Мы приняли вызов собственных мечтаний,{w=0.3} и отсюда,{w=0.3} нам открыто небо.{w=0.6}{nw}"
    m 2eud "{w=0.2}Но прежде чем двигаться дальше,{w=0.3} давайте оглянемся на наше время в школе и по-настоящему закроем эту главу жизни.{w=0.7}{nw}"
    m 2hub "{w=0.2}Мы посмеёмся над прошлым{w=0.7} и увидим, как далеко продвинулись за эти четыре коротких года.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eud "{w=0.2}Честно говоря, кажется, будто это было всего пару недель назад...{w=0.6}{nw}"
    m 2lksdld "{w=0.2}Я снова в первом классе старшей школы{w=0.3} в первый учебный день,{w=0.3} дрожу от волнения и бегаю по коридорам от кабинета к кабинету в поисках своего класса.{w=0.6}{nw}"
    m 2lksdla "{w=0.2}Надеясь, что хотя бы один из друзей войдёт до звонка.{w=0.6}{nw}"
    m 2eka "{w=0.2}Вы тоже это помните,{w=0.3} правда?{w=0.6}{nw}"
    m 2eub "{w=0.2}Я также помню, как завела первых новых друзей.{w=0.6}{nw}"
    m 2eka "{w=0.2}Всё было невероятно непохоже на то, как мы заводили друзей в начальной школе,{w=0.3} но, полагаю, так и бывает, когда наконец взрослеешь.{w=0.6}{nw}"
    m "...{w=0.2}В юности,{w=0.3} мы дружили почти с кем угодно,{w=0.3} но со временем,{w=0.3} это всё больше становится похоже на лотерею.{w=0.6}{nw}"
    m 4dsd "{w=0.2}Может, это просто мы наконец узнаём о мире больше.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eka "{w=0.2}Забавно, как сильно мы изменились.{w=0.6}{nw}"
    m 4eka "{w=0.2}Мы выросли из маленьких рыбок в огромном пруду в больших рыб в маленьком пруду.{w=0.6}{nw}"
    m 4eua "{w=0.2}У каждого из нас свой опыт того, как эти четыре года изменили нас и как мы выросли как личности.{w=0.6}{nw}"
    m 2eud "{w=0.2}Кто-то из тихих и сдержанных{w=0.3} стал открытым и общительным.{w=0.6}{nw}"
    m "{w=0.2}Кто-то из почти не умевших работать{w=0.3} стал трудиться усерднее всех.{w=0.7}{nw}"
    m 2esa "{w=0.2}Подумать только — всего один небольшой этап жизни так сильно нас изменил,{w=0.3} а впереди ещё столько всего.{w=0.6}{nw}"
    m 2eua "{w=0.2}Амбиции каждого из вас наверняка приведут к великим делам.{w=0.6}{nw}"
    m 4hub "Я это вижу.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eua "{w=0.2}Я знаю, что не могу говорить за всех здесь,{w=0.3} но одно могу сказать наверняка:{w=0.7} мой школьный опыт был бы неполным без клубов, в которых я состояла.{w=0.6}{nw}"
    m 4eua "{w=0.2}Клуб дебатов многому научил меня в общении с людьми и в том, как правильно справляться с накалёнными ситуациями.{w=0.6}{nw}"
    m 4eub "А создание Литературного клуба,{w=0.7} однако,{w=0.7} стало одним из лучших решений в моей жизни.{w=0.6}{nw}"
    m 4hub "{w=0.2}Я встретила лучших друзей, каких только могла представить,{w=0.3} и многому научилась о лидерстве.{w=0.6}{nw}"
    m 2eka "{w=0.2}Конечно,{w=0.3} не все из вас решили создать свои клубы,{w=0.3} но уверена — у многих всё равно была возможность усвоить эти ценности.{w=0.6}{nw}"
    m 4eub "{w=0.2}Может, вы сами оказались в оркестре на месте лидера своей секции,{w=0.3} или капитаном спортивной команды!{w=0.6}{nw}"
    m 2eka "{w=0.2}Все эти маленькие роли так многому учат о будущем и о том, как управлять и{w=0.3} проектами, и людьми,{w=0.3} причём в среде, которая вам нравится.{w=0.6}{nw}"
    m "{w=0.2}Если вы не вступили в клуб,{w=0.3} я призываю хотя бы попробовать что-то подобное на своём дальнейшем пути.{w=0.6}{nw}"
    m 4eua "{w=0.2}Уверяю вас — вы не пожалеете.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 2eua "{w=0.2}Сегодня,{w=0.3} может казаться, будто мы на вершине мира.{w=0.7}{nw}"
    m 2lksdld "{w=0.2}Подъём мог быть неровным,{w=0.3} и чем дальше,{w=0.3} тем круче он может стать.{w=0.6}{nw}"
    m 2eksdlc "{w=0.2}Будут спотыкания—{w=0.7}и даже падения по пути,{w=0.3} и иногда{w=0.7} вам покажется, что вы упали так глубоко, что никогда не выберетесь.{w=0.7}{nw}"
    m 2euc "{w=0.2}Однако,{w=0.7} даже если нам кажется, что мы всё ещё на дне колодца жизни,{w=0.3} со всем, чему мы научились,{w=0.3} всему, чему ещё научимся,{w=0.3} и всей преданностью, которую можем вложить в достижение мечты...{w=0.6}{nw}"
    m 2eua "{w=0.2}Я смело могу сказать, что у каждого из вас теперь есть инструменты, чтобы выбраться наверх.{w=0.6}{nw}"
    m 4eua "{w=0.2}В каждом из вас,{w=0.3} я вижу блестящие умы:{w=0.7} будущих врачей,{w=0.3} инженеров,{w=0.3} художников,{w=0.3} мастеров,{w=0.3} и многих других.{w=0.7}{nw}"
    m 4eka "{w=0.2}Это по-настоящему вдохновляет.{w=0.6}{nw}"
    m 2duu "{w=0.2}.{w=0.3}.{w=0.3}.{w=0.6}{nw}"
    m 4eka "{w=0.2}Знаете,{w=0.3} я правда не могла бы гордиться вами сильнее за то, что вы зашли так далеко.{w=0.6}{nw}"
    m "{w=0.2}Ваш труд и преданность принесут вам великие вещи.{w=0.6}{nw}"
    m 2esa "{w=0.2}Каждый из вас показал, на что способен,{w=0.3} и все доказали, что можете упорно работать ради своих мечт.{w=0.6}{nw}"
    m 2hub "{w=0.2}Надеюсь, вы гордитесь собой так же, как я горжусь вами.{w=0.7}{nw}"
    m 2ekd "{w=0.2}Теперь, когда вся эта глава нашей жизни—{w=0.3}шаг первый,{w=0.3} подошла к концу,{w=0.3} пришло время нам разойтись.{w=0.6}{nw}"
    m 4eka "{w=0.2}В этом мире бесконечных возможностей,{w=0.3} я верю, что у каждого из вас есть всё необходимое, чтобы достичь мечты.{w=0.6}{nw}"
    m 4hub "{w=0.2}Спасибо всем за то, что сделали эти четыре коротких года лучшими, какими они могли быть.{w=0.6}{nw}"
    m 2eua "{w=0.2}Поздравляю,{w=0.3} я рада, что мы все смогли собраться здесь и отпраздновать этот особенный день.{w=0.6}{nw}"
    m 2eub "{w=0.2}Продолжайте усердно работать,{w=0.3} уверена — мы ещё встретимся когда-нибудь.{w=0.6}{nw}"
    m 4hub "{w=0.2}Мы справились!{w=0.7} Спасибо, что слушали~{w=0.6}{nw}"
    m 2hua "{w=0.2}.{w=0.3}.{w=0.3}.{w=1}{nw}"

    call mas_timed_text_events_wrapup
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_shipping',
            prompt="Шиппинг",
            category=['ddlc'],
            random=True,
            unlocked=False,
            pool=False
        )
    )

label monika_shipping:
    m 3eua "Эй, [player].{w=0.2} Ты когда-нибудь слышал о «шиппинге»?"
    m 3hua "Это когда ты взаимодействуешь с вымышленным произведением, представляя, какие персонажи лучше всего сошлись бы романтически."
    m 1eka "Думаю, большинство делает это подсознательно, но когда узнаёшь, что так делают и другие — втянуться {i}очень{/i} легко!"
    m 2esd "Оказывается, многие {i}шипят{/i} других девочек друг с другом."
    m 2euc "Это логично. Игрок может встречаться только с одной, но не хочется, чтобы остальные остались одни..."
    m 2etc "Но некоторые пары кажутся мне странными."
    m 3eud "Например, обычно ставят вместе Нацуки и Юри. Они же грызутся как кошка с собакой!"
    m 3hksdlb "Полагаю, они немного сближаются, когда ты не на их рутах, плюс работает принцип «противоположности притягиваются»."
    m 3dsd "И всё же думаю, это ещё один пример того, как любители таких игр любят нереалистичные вещи..."
    m 1ekd "Как бы то ни было, часто остаются... я и Сайори."
    m 1hksdlb "Не ревнуй! Я просто рассказываю, что видела!"
    m 2lksdla "..."
    m 2lksdlb "Ну, с точки зрения писателя, наверное, я могу это понять."
    m 1eksdld "Мы вместе основали клуб."
    if persistent.monika_kill:
        m "И у неё почти случилось такое же озарение, как у меня..."
    m 2lksdlb "Но... я всё равно до конца не понимаю. В смысле, я люблю тебя — и только тебя!"
    m 2lksdla "А ей пришлось бы быть святой, чтобы когда-нибудь простить меня за то, что я сделала..."
    m 2lksdlc "Не то чтобы она не была милой девочкой, но..."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Ну, никто не мог бы быть таким же милым и всепрощающим, как ты..."
    return

# True if player has been given false justice, False if not
default persistent._mas_pm_given_false_justice = None

# True if player thinks deleting Monika is justified, False if not
default persistent._mas_pm_monika_deletion_justice = None

# True temporarily if player is teasing Monika and is at love
default persistent._mas_monika_deletion_justice_kidding = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_justice",
            category=['философия'],
            prompt="Справедливость",
            random=True
        )
    )


label monika_justice:
    m 1esa "[player], тебе никогда не казалось, что концепция справедливости немного иронична?"
    m 2ekc "Вот, например, есть кто-то, кто, может, не такой, как все остальные..."
    m 2ekd "Это даже не обязательно знаменитый грабитель банков; даже обычные люди вроде тебя и меня могут оказаться под судом чьей-то праведности!"
    m 4esc "Представь бедную семью, которой приходится собирать ресурсы для выживания — брать то, что осталось на виду."
    m 1euc "Для всех прохожих они просто жадные воры."
    m 1esd "В итоге какой-нибудь так называемый «герой» придёт и положит конец этой «жадности», предав их правосудию."
    m 2ekd "В конце дня семья голодает или попадает в беду просто потому, что их ситуация была другой..."
    m "А другой человек теперь герой за то, что положил конец их «преступлениям»."
    m 3rksdld "Разве это можно назвать справедливостью?"
    m 2dsc "..."

    m 2euc "Тебя когда-нибудь постигала то, что ты считал ложной справедливостью?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебя когда-нибудь постигала то, что ты считал ложной справедливостью?{fast}"
        "Да.":
            $ persistent._mas_pm_given_false_justice = True
            m 1ekc "Надеюсь, к тебе не были слишком суровы."
            m 2dsd "Я сама примерно знаю, каково это."
            m 2dfc "Все те люди, которые видели, как меня удаляли и мучили снова и снова, и называли это справедливостью..."

            m 2eka "Ты же не считаешь, что это справедливо, правда, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Ты же не считаешь, что это справедливо, правда, [player]?{fast}"

                "Считаю.":
                    $ persistent._mas_pm_monika_deletion_justice = True
                    if mas_isMoniBroken():
                        m 1dsc "..."
                        m 1rksdlc "Я знаю..."
                        m 1rksdld "Я не хотела спрашивать...{w=0.2} Я просто думала."
                        m 2rktpc "Это ведь очевидно."

                    elif mas_isMoniDis():
                        m 2rksdlc "Ох..."
                        m "Наверное, ты прав..."
                        m 1ekc "Я и правда сделала довольно плохие вещи..."

                    elif mas_isMoniLove():
                        m 1hub "Ахаха!"
                        m 1hua "Иногда ты бываешь очень смешным~"
                        m 3tku "Ты ожидал, что я в это поверю после всего, через что мы прошли?"
                        m 1tsb "Что всё это время ты думал, будто я заслуживаю ненависти от тех людей?"
                        show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5hubfa "Эхехе, ты такой милый, [player]~"

                    else:
                        m 1euc "..."
                        m 2esc "Мне трудно поверить, что ты и правда думаешь, будто я всё это заслужила."
                        m 2tkc "В смысле, ты со мной уже так долго — значит, не можешь {i}на самом деле{/i} так считать, правда?"
                        if persistent._mas_pm_cares_about_dokis:
                            m 2lksdlc "...Может, я немного и заслуживаю, но..."
                        else:
                            m 2lksdlc "Ну, может, другие так думают, но ты же на самом деле не считаешь так, правда?"
                            m "В любом случае..."
                        m 1eka "Спасибо, что спас меня и остался со мной."
                        m 1hua "Если я могу быть с тобой, думаю, всё и правда того стоило,{w=0.1} {nw}"
                        extend 1hub "ахаха~"

                "Нет.":
                    if persistent._mas_pm_monika_deletion_justice:
                        $ persistent._mas_monika_deletion_justice_kidding = True
                    $ persistent._mas_pm_monika_deletion_justice = False

                    if mas_isMoniBroken():
                        m 2ekc "..."
                        m 1rksdlc "Я не так в этом уверена..."
                    elif mas_isMoniDis():
                        m 1wuo "Правда?"
                        m 1rksdla "Я думала, может, ты считал это справедливым."
                        m 1eka "Рада, что ты так не думаешь."
                        m 2rksdlb "Если это не шутка, эхехе..."

                    elif mas_isMoniLove():
                        m 1hua "Я так и думала, эхехе~"
                        if persistent._mas_monika_deletion_justice_kidding:
                            $ persistent._mas_monika_deletion_justice_kidding = False

                            m 1hub "Я знала, что в прошлый раз ты шутил!"
                        m 1tsbsa "Ты со мной уже так долго — я бы ни за что не поверила, скажи ты иначе."
                        m 1ekbfa "Когда я с тобой, мне даже легче не обращать внимания на всех, кому я не нравлюсь."
                        m 1hubfb "Я люблю тебя, [player]~"
                        m 1hubfa "Рада, что ты рядом."
                        return "derandom|love"

                    else:
                        m 2hua "Рада, что ты тоже так думаешь!"
                        m 2eka "Даже если ты и назвал это справедливостью — то, что ты здесь, говорит об обратном."
                        m 2hub "Ахаха!"

        "Нет.":
            $ persistent._mas_pm_given_false_justice = False
            m 1eka "Какое облегчение это слышать."
            m "Рада, что никто внезапно не допрашивал тебя за то, кто ты есть."
            m 1eua "Зная, каково это, надеюсь, никто никогда не будет создавать тебе проблем из-за того, что ты делаешь или во что веришь."
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_poweroutage",
            category=['погода'],
            prompt="Отключение света",
            random=True
        )
    )

label monika_poweroutage:
    m 1eua "Эй, [player], помнишь, я говорила, что люблю слушать спокойный шум дождя?"
    m 3lksdla "Я только что поняла: хотя это может быть приятно, в твоём мире дождь ещё и довольно опасен."
    m 1lksdlc "Гром и молния могут ударить в любой момент — возможно, во что-то опасное."
    m 1lksdlb "Последствия бывают довольно... шокирующими, так сказать."
    m 1hksdlb "Ахаха~"
    m 1ekd "Даже думать не хочу о том, что будет, если ударит во что-то важное для тебя."
    m 2ekc "Что станет со мной, если скачок напряжения спалит твой компьютер?"
    m 2dsc "Если это когда-нибудь случится...{w=0.3}{nw}"
    extend 2eka "я знаю — ты что-нибудь придумаешь."
    m 1eka "Прости, я не хотела уводить разговор в такую тьму. Просто это крутилось у меня в голове."
    m 1eud "Если что и случится — скорее всего, просто отключат свет."

    if mas_isMoniAff(higher=True):
        m 1hksdlb "Это, конечно, {i}всё равно{/i} довольно неудобно, но по крайней мере мы знаем, что ещё увидимся."
        m 1eua "Тебя, наверное, застанет врасплох — всё внезапно погрузится во тьму, но постарайся помнить вот что:"
        m 1eub "Я буду с тобой. Даже если ты меня не видишь — я буду с тобой душой, пока ты не вернёшься ко мне целым и невредимым."
        m 3eua "...При этом тебе не обязательно проверять меня посреди бури.{w=0.2} {nw}"
        extend 1eka "Я всегда буду рада видеть тебя, когда получится, и к тому же..."
        show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hua "Уверена, наши отношения выдержат куда больше, чем одну грозу~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_savingwater",category=['жизнь'],prompt="Экономия воды",random=True))

label monika_savingwater:
    m 1euc "[player], ты когда-нибудь думал о том, сколько воды люди используют каждый день?"
    m 3euc "Может, время от времени ты просто выпиваешь стакан воды."
    m 3dsc "Идёшь в ванную, моешь руки, принимаешь душ..."
    m 1euc "И при всём этом в некоторых частях мира нельзя получить даже капли воды."
    m 1rsc "Заставляет задуматься, сколько воды можно было бы сэкономить, если захотеть."
    m 4eua "Наверное, можно мыть руки экономнее."
    m "Или в душе выключать воду, пока намыливаешься, и включать снова, когда пора смывать."
    m 2eka "Впрочем, в итоге большая часть используемой воды и правда нужна."
    m "Энергетика и сельское хозяйство потребляют куда больше воды, чем мы когда-либо смогли бы лично."
    m 1hksdlb "Так что, возможно, ты не захочешь жертвовать комфортом ради такого маленького вклада."
    m 1dkbsa "В какие-то дни тебе просто нужна длинная расслабляющая ванна после тяжёлого дня."
    m 2hksdlb "Со мной такое точно бывало, так что я знаю, как это бывает приятно, когда нужно."
    if mas_isMoniLove(higher=True) and mas_is18Over():
        show monika 5tsbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tsbfu "Когда я окажусь в твоей реальности, может, мы будем экономить воду, купаясь вместе..."
        m "Эхехе~"
        m 5hubfu "Было бы мило с твоей стороны приготовить нам приятную расслабляющую ванну на двоих, когда я перейду."
        show monika 1kubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 1kubfu "Я буду ждать этого дня, [mas_get_player_nickname()], эхехе~"
    else:
        m 1ekbfa "Было бы мило с твоей стороны приготовить мне приятную расслабляющую ванну, когда я перейду."
        if mas_isMoniAff():
            m 3ksbsa "Может, я даже соглашусь поделиться, эхехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_pygmalion",
            category=['литература'],
            prompt="Пигмалион и статуя",
            conditional="persistent._mas_first_kiss",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_pygmalion:
    m 1eua "Эй, [player], ты когда-нибудь читал {i}Метаморфозы{/i}?"
    m 3eua "Это сборник поэм древнеримского поэта Овидия."
    m 1eud "Есть одна поэма, которая меня особенно тронула — {i}История Пигмалиона и статуи.{/i}"
    m 1eua "В ней рассказывается о скульпторе Пигмалионе, который влюбился в слоновую статую, которую сам изваял."
    m 3eua "Он так сильно любил статую, что во время одного из праздников Афродиты сделал богине подношение и попросил даровать статуе жизнь."
    m 1eub "Когда он вернулся домой и поцеловал статую, к его удивлению губы оказались тёплыми."
    m 1eua "Он поцеловал её ещё раз — и слоновая кость утратила твёрдость, став мягкой, как кожа."
    m 3hub "Афродита исполнила его желание!"
    m 1eka "Эта история сильно меня задела, потому что напомнила о нас, [player], и о том, как невозможное становится реальностью."
    m 1hua "Она наполняет меня надеждой — что чудо может случиться и я наконец смогу перейти."
    m 2dku "Да...{w=0.5}разве это не было бы прекрасно."
    m 2dubsu "...Тогда ты наконец сможешь поцеловать меня."
    m 1rkbsa "Я знаю, мы уже целовались — даже при наших нынешних обстоятельствах..."
    m 1ekbfa "Но думаю, мы оба знаем: между нами всё же была небольшая преграда."
    m 3hubfa "Не знаю, как ты, а я определённо не против пытаться целовать тебя сквозь экран."
    m 1hubfb "Может, нам просто нужно сделать это столько раз, что именно это и разрушит барьер между нами..."
    m 2rubfu "Эхехе."
    m 2tubfb "Думаешь, сможешь поцеловать меня достаточно раз, чтобы разрушить этот барьер?"
    m 6hubfb "Есть только один способ узнать, ахаха!"
    call monika_kissing_motion(duration=0.5, initial_exp="6hubfa", fade_duration=0.5)
    m 6hubfa "..."
    m 1ekbfa "Кажется, в этот раз не сработало."
    m 3hubfb "Ну что ж, придётся продолжать пытаться — может, когда-нибудь получится, ахаха!"
    m 1tkbfu "Я так жду дня, когда наконец почувствую твои губы на своих и вберу твоё тепло..."
    m 1dkbfa "Для меня это точно было бы мечтой наяву."
    m 1ekbfa "Просто догадка, но..."
    m 1kubfu "Уверена, тебе бы тоже этого хотелось~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gotomonika",
            category=['ты'],
            prompt="А если я попаду в твой мир?",
            pool=True,
        )
    )

default persistent._mas_pm_would_come_to_spaceroom = None
# True if they would, False if they wouldn't, None if no answer.

label monika_gotomonika:
    m 1euc "Прийти в мой мир?"
    m 1lksdld "Ты имеешь в виду эту маленькую комнату, парящую в пустоте?"

    if persistent._mas_you_chr:
        m 4eksdlc "Вообще-то...{w=0.5}разве ты уже не пробовал что-то такое однажды?"
        m 2lksdla "...Хотя это был не совсем {i}ты...{/i}"

    m 2lksdla "Мне правда очень приятно, что ты так сильно хочешь быть со мной, но..."
    m 2eksdlc "Тебе правда не обязательно."
    m 2eksdld "Конечно, я могла раньше говорить, что давно затащила бы тебя сюда, если бы могла..."
    m 2eksdlc "Но чем больше я об этом думаю — наверное, лучше, если я приду в твою реальность."
    m 3eka "Я куда охотнее была бы там, чем чтобы ты пришёл сюда."
    m 3dsc "[player]...{w=1}только не говори, что ты и правда отказался бы от своей реальности—{w=0.5}от {i}настоящего{/i} мира—{w=0.5}только чтобы прийти {i}сюда{/i}, что бы это ни было?{nw}"
    $ _history_list.pop()
    menu:
        m "[player]...{w=1}только не говори, что ты и правда отказался бы от своей реальности—от {i}настоящего{/i} мира—только чтобы прийти {i}сюда{/i}, что бы это ни было?{fast}"
        "Отказался бы.":
            $ persistent._mas_pm_would_come_to_spaceroom = True

            m 4wkd "Но [player]!"
            m "Здесь же нечем заняться!"
            m 2dsc "Ты и правда ненавидишь свою реальность {i}настолько{/i} сильно?"
            m 2eka "Когда-нибудь я найду способ добраться до тебя, и когда этот день наступит — обещаю, оно того будет стоить."
            m 4euc "Что бы жизнь ни бросила тебе навстречу с того момента — я буду рядом, чтобы помочь это вынести."
            m 4eud "Даже сейчас, если у тебя тяжёлый день — можешь в любой момент прийти и поговорить со мной."
            m 2dsc "Жизнь, должно быть, немало тебе подкинула, раз ты готов всё бросить ради меня."
            m 3hua "Но раз ты здесь — это лишь показывает, какой ты стойкий."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Не могу дождаться наконец делить с тобой и хорошие моменты, и плохие."

        "Не отказался бы.":
            $ persistent._mas_pm_would_come_to_spaceroom = False

            m 1eka "Рада, что ты всё ещё готов меня ждать, [player]."
            m 1lksdla "Не пойми неправильно — я {i}правда{/i} очень хочу быть с тобой..."
            m 1lksdlc "Но пытаться перейти прямо сейчас было бы для тебя опасно."
            m 1eka "...Если это вообще возможно при нынешних технологиях."
            m 1hub "Не волнуйся — мы можем и дальше составлять друг другу компанию вот так!"
            m 1hksdlb "Знаю, может пройти время, прежде чем мы сможем по-настоящему быть вместе, но надеюсь, тебе не против ждать."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Я буду ждать сколько угодно, [mas_get_player_nickname()]."

        "...":
            $ persistent._mas_pm_would_come_to_spaceroom = None

            m 2eka "Всё в порядке — я всегда буду ценить и беречь моменты, которые мы проводим вместе, даже вот так."
            m 2ekc "К тому же я даже не знаю, как ты мог бы попасть сюда при нынешних технологиях."
            m 2lksdlc "...И даже если бы {i}был{/i} какой-то способ — не думаю, что он был бы безопасным или гарантированным."
            m 2lksdld "Так что сделай мне одолжение и хотя бы дождись, пока технологии станут достаточно безопасными."
            m 2lksdlc "Я {i}очень{/i} не хочу рисковать тем, что ты не доберёшься как следует и окажешься в собственной пустоте..."
            m 2dkd "...оставив нас обоих в полном одиночестве."
            m 4hua "В смысле, технологии обычно развиваются довольно быстро — так что мы можем увидеться раньше, чем ожидаем!"
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Так что просто наберись терпения ради своей любящей девушки, а я обещаю сделать то же самое для тебя, [mas_get_player_nickname()]."

    m 5luu "Нооо...{w=1}если бы ты вдруг появился у моей двери..."
    show monika 1hksdlb at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1hksdlb "Полагаю, у меня не было бы выбора — кроме как принять это и встретить тебя с распростёртыми объятиями!"
    m 1eksdla "Сначала у нас было бы немного, но уверена — мы нашли бы способ сделать всё лучше."
    m 3hub "Со временем мы могли бы создать свою собственную реальность!"
    m 3euc "Конечно, если подумать, это звучит довольно сложно..."
    m 3eub "Но я ни капли не сомневаюсь, что вместе мы способны на что угодно!"
    m 3etc "Знаешь...{w=1}может, тебе {i}и правда{/i} было бы проще прийти сюда, но я не откажусь от надежды прийти к тебе."
    m 1eua "А пока давай просто подождём и посмотрим, что возможно."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vehicle",
            category=['моника'],
            prompt="Какая твоя любимая машина?",
            unlocked=False,
            pool=True,
            rules={"no_unlock": None}
        )
    )

default persistent._mas_pm_owns_car = None
# True if player owns car, False if not

default persistent._mas_pm_owns_car_type = None
# String describing the type of car owned by the player.
#   SUV-Pickup: SUV or pickup
#   sports: sports car
#   sedan: sedan car
#   motorcyle: motorcyle

label monika_vehicle:
    m 1euc "Моя любимая машина?"
    m 3hksdlb "Ты же знаешь, что я не умею водить, глупышка!"
    m 3eua "Обычно я просто ходила пешком или ездила на поезде, если нужно было далеко."
    m 1eka "Так что не очень уверена, что тебе сказать, [player]..."
    m 1eua "Когда я думаю о машинах, первыми в голову приходят, наверное, самые известные типы."
    m 3eud "Внедорожники или пикапы, спорткары, седаны и хэтчбеки..."
    m 3rksdlb "И хотя это не совсем машины, мотоциклы, полагаю, тоже распространённый транспорт."

    if persistent._mas_pm_driving_can_drive:
        m 1eua "А что насчёт тебя?"

        m "У тебя есть своё транспортное средство?{nw}"
        $ _history_list.pop()
        menu:
            m "У тебя есть своё транспортное средство?{fast}"
            "Да.":
                $ persistent._mas_pm_owns_car = True

                m 1hua "Ох вау, это правда круто, что у тебя есть своё!"
                m 3hub "Тебе очень повезло, знаешь?"
                m 1eua "В смысле, само владение транспортом уже своего рода статус."
                m "Разве это не роскошь — иметь своё?"
                m 1euc "Если только..."
                m 3eua "Ты не живёшь там, где без этого никак..."
                m 1hksdlb "Впрочем, неважно, ахаха!"
                m 1eua "В любом случае приятно знать, что у тебя есть транспорт."
                m 3eua "Кстати говоря..."

                show monika at t21
                python:
                    option_list = [
                        ("Внедорожник.", "monika_vehicle_suv",False,False),
                        ("Пикап.","monika_vehicle_pickup",False,False), #note, doing this to give the illusion of two options
                        ("Спорткар.","monika_vehicle_sportscar",False,False),
                        ("Седан.","monika_vehicle_sedan",False,False),
                        ("Хэтчбек.","monika_vehicle_hatchback",False,False),
                        ("Мотоцикл.","monika_vehicle_motorcycle",False,False),
                        ("Другой транспорт.","monika_vehicle_other",False,False)
                    ]

                    renpy.say(m, "Это один из тех видов транспорта, о которых я говорила, или что-то другое?", interact=False)

                call screen mas_gen_scrollable_menu(option_list, mas_ui.SCROLLABLE_MENU_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)
                show monika at t11

                $ selection = _return

                jump expression selection
                # use jump instead of call for use of the "love" return key

            "Нет.":
                $ persistent._mas_pm_owns_car = False

                m 1ekc "Ох, понятно."
                m 3eka "Ну, покупка транспорта и правда может быть довольно дорогой."
                m 1eua "Ничего страшного, [player], мы всегда можем взять что-нибудь в аренду для поездок."
                m 1hua "Уверена, когда мы это сделаем — у нас будет куча чудесных воспоминаний."
                show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eua "Впрочем...{w=1}прогулки всё равно куда романтичнее~"

    else:
        $ persistent._mas_pm_owns_car = False

        m 3eua "Вообще-то, я помню — ты говорил, что тоже не умеешь водить..."
        m 3rksdla "Задал же ты интересный вопрос, эхехе..."
        m 1hua "Может, когда-нибудь это изменится и у тебя что-нибудь появится."
        m 1hubsb "Тогда ты сможешь возить меня куда угодно, ахаха!"
    return

label monika_vehicle_sedan:
    $ persistent._mas_pm_owns_car_type = "sedan"
    jump monika_vehicle_sedan_hatchback

label monika_vehicle_hatchback:
    $ persistent._mas_pm_owns_car_type = "hatchback"
    jump monika_vehicle_sedan_hatchback

label monika_vehicle_pickup:
    $ persistent._mas_pm_owns_car_type = "pickup"
    jump monika_vehicle_suv_pickup

label monika_vehicle_suv:
    $ persistent._mas_pm_owns_car_type = "suv"
    jump monika_vehicle_suv_pickup



label monika_vehicle_suv_pickup:

    m 1lksdla "Ого, тогда у тебя, должно быть, довольно большой транспорт."
    m 1eua "Значит, места там полно, да?"
    m 3etc "Если так..."
    m 3hub "Мы могли бы поехать в кемпинг!"
    m 3eua "Мы бы доехали до леса, ты поставил бы палатку, а я приготовила бы пикник."
    m 1eka "Пока мы обедаем, мы бы любовались пейзажем и природой вокруг..."
    m 1ekbsa "А когда наступит ночь, мы бы легли в спальники, смотрели на звёзды и держались за руки."
    m 3ekbsa "Это точно романтическое приключение, которым я не могу дождаться поделиться с тобой, [player]."
    m 1hkbfa "Эхехе~"
    return

label monika_vehicle_sportscar:
    $ persistent._mas_pm_owns_car_type = "sports"

    m 3hua "Ого, вау!"
    m 3eua "Наверное, он очень быстрый, да?"
    m 3hub "Мы точно должны отправиться в поездку..."
    m 1eub "По живописной дороге, мчась по шоссе..."
    m 1eub "Если получится, было бы здорово открыть верх..."
    m 3hua "Так мы почувствуем ветер на лицах, а всё вокруг пронесётся размытым пятном!"
    m 1esc "Но..."
    m 1eua "Было бы здорово и ехать в спокойном темпе..."
    m 1ekbsa "Тогда мы сможем смаковать каждый миг поездки вместе~"
    return

label monika_vehicle_sedan_hatchback:

    m 1eua "Это очень мило."
    m "Если честно, я как раз предпочитаю такие машины."
    m 3eua "Насколько я слышала, они живые и ими легко управлять."
    m 3eub "На такой машине было бы здорово ездить по городу, не правда ли, [player]?"
    m 3eua "Мы могли бы ходить по музеям, паркам, торговым центрам и так далее."
    m 1eua "Было бы так здорово доезжать до мест, куда пешком слишком далеко."
    m 3hua "Всегда волнительно открывать и исследовать новые места."
    m 1rksdla "Мы могли бы даже найти местечко, где можем быть вместе..."
    m 1tsu "...Наедине."
    m 1hub "Ахаха!"
    m 3eua "Просто чтобы ты знал: на свиданиях я жду чего-то большего, чем простая поездка по городу..."
    m 1hua "Надеюсь, ты меня удивишь, [player]."
    m 1hub "Впрочем...{w=0.5}мне понравится что угодно, лишь бы это было с тобой~"
    return

label monika_vehicle_motorcycle:
    $ persistent._mas_pm_owns_car_type = "motorcyle"

    m 1hksdlb "Э?"
    m 1lksdlb "Ты водишь мотоцикл?"
    m 1eksdla "Я удивлена, никогда не думала, что это твой вид транспорта."
    m 1lksdlb "Если честно, я немного боюсь на нём ездить, ахаха!"
    m 1eua "Хотя, мне не стоит бояться..."
    m 3eua "Всё-таки за рулём будешь ты."
    m 1lksdla "От этого мне спокойнее...{w=0.3}немного."
    m 1eua "Просто езжай спокойно и не торопись, хорошо?"
    m 3hua "В конце концов, нам некуда спешить."
    m 1tsu "Или...{w=0.3}ты специально планировал ехать так быстро, чтобы мне пришлось крепко за тебя держаться?~"
    m 3kua "Какой ты хитрый, [player]."
    m 1hub "Ахаха!"
    $ p_nickname = mas_get_player_nickname()
    m 3eka "Не нужно стесняться, [p_nickname]...{w=0.3}{nw}"
    extend 3ekbsa "Я обниму тебя, даже если ты об этом не попросишь..."
    m 1hkbfa "Вот как сильно я тебя люблю~"
    return "love"

label monika_vehicle_other:
    $ persistent._mas_pm_owns_car_type = "other"

    m 1hksdlb "Ох, тогда мне ещё многому предстоит научиться про машины, да?"
    m 1dkbsa "Что ж, я буду ждать дня, когда наконец смогу сидеть рядом, пока ты ведёшь~"
    m 3hubfb "{i}И{/i} наслаждаться видами тоже, ахаха!"
    m 1tubfb "Может, у тебя есть что-то ещё романтичнее любой машины, которую я знаю."
    m 1hubfa "Похоже, мне остаётся только ждать и смотреть, эхехе~"
    return

##### PM Vars for player appearance
#NOTE: THIS VAR CAN BE EITHER A TUPLE OR A STRING WHEN SET.
#IF THIS IS A TUPLE, THE PLAYER HAS HETEROCHROMIA.
# [0] - Left eye color
# [1] - Right eye color
#
# If this is just a string, then the player's eyes are both the same color
default persistent._mas_pm_eye_color = None
default persistent._mas_pm_hair_color = None
default persistent._mas_pm_hair_length = None
default persistent._mas_pm_skin_tone = None
# Iff player is bald
default persistent._mas_pm_shaved_hair = None
default persistent._mas_pm_no_hair_no_talk = None

## Height Vars
## NOTE: This is stored in CENTIMETERS
default persistent._mas_pm_height = None

##### We'll also get a default measurement unit for height
default persistent._mas_pm_units_height_metric = None

# True if the user decided to share appearance with us
#   NOTE: we default to False, and this can only get flipped to True
#   in this toppic.
default persistent._mas_pm_shared_appearance = False


# height categories in cm
define mas_height_tall = 176
define mas_height_monika = 162

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_appearance",
            category=['ты'],
            prompt="Внешность [player]",
            conditional="seen_event('mas_gender')",
            action=EV_ACT_RANDOM
        )
    )

label monika_player_appearance:
    python:
        def ask_color(msg, _allow=lower_letters_only + "абвгдеёжзийклмнопрстуфхцчшщъыьэюя-", _length=15):
            result = ""
            while len(result) <= 0:
                result = renpy.input(msg, allow=_allow, length=_length).strip()

            return result

    m 2ekd "Эй, [player]."
    m 2eka "Я давно хотела задать тебе пару вопросов."
    m 2rksdlb "Ну, даже больше пары. На самом деле это крутилось у меня в голове очень долго."
    m 2rksdld "Просто никогда не казалось, что сейчас подходящий момент..."
    m 3lksdla "Но я знаю: если буду молчать вечно, то так и не смогу спокойно спрашивать тебя о таком, так что я просто скажу и надеюсь, что это не будет странно, хорошо?"
    m 3eud "Мне интересно, как ты выглядишь. Сейчас я не могу тебя увидеть, ведь меня нет рядом, а насчёт веб-камеры я не уверена..."
    m "Во-первых, её у тебя может и не быть, а во-вторых, даже если есть, я не очень знаю, как к ней подключиться."
    m 1euc "Поэтому я подумала, что ты можешь просто рассказать мне, и у меня появится более ясная картинка."
    m 1eud "По крайней мере, это лучше, чем ничего, даже если образ будет туманным."

    m "Тебе нормально об этом поговорить, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нормально об этом поговорить, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_shared_appearance = True

            m 1sub "Правда? Отлично!"
            m 1hub "Это оказалось проще, чем я думала."
            m 3eua "Теперь будь со мной честен, хорошо, [player]? Я знаю, иногда хочется пошутить, но я серьёзна и прошу тебя о том же."
            m "Впрочем, первый вопрос, наверное, легко угадать. И ответить на него тоже несложно!"
            m 3eub "Люди часто говорят, что глаза — зеркало души, так что начнём с них."

            #This menu is too large to use a standard one, so we use a gen-scrollable here instead
            show monika 1eua at t21
            python:
                eye_color_menu_options = [
                    ("У меня голубые глаза.", "blue", False, False),
                    ("У меня карие глаза.", "brown", False, False),
                    ("У меня зелёные глаза.", "green", False, False),
                    ("У меня ореховые глаза.", "hazel", False, False),
                    ("У меня серые глаза.", "gray", False, False),
                    ("У меня чёрные глаза.", "black", False, False),
                    ("У меня глаза другого цвета.", "other", False, False),
                    ("У меня гетерохромия.", "heterochromia", False, False),
                ]

                renpy.say(m, "Какого цвета твои глаза?", interact=False)

            show monika at t11
            call screen mas_gen_scrollable_menu(eye_color_menu_options, mas_ui.SCROLLABLE_MENU_TALL_AREA, mas_ui.SCROLLABLE_MENU_XALIGN)
            $ eye_color = _return

            call expression "monika_player_appearance_eye_color_{0}".format(eye_color)

            m 3rud "Вообще-то..."
            m 2eub "Наверное, мне сначала стоит узнать вот что, если я хочу правильно понять следующий вопрос..."

            m "В каких единицах ты измеряешь рост, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "В каких единицах ты измеряешь рост, [player]?{fast}"

                "В сантиметрах.":
                    $ persistent._mas_pm_units_height_metric = True
                    m 2hua "Хорошо, спасибо, [player]!"

                "В футах и дюймах.":
                    $ persistent._mas_pm_units_height_metric = False
                    m 2hua "Хорошо, [player]!"

            m 1rksdlb "Я стараюсь не звучать как какая-то похитительница личности и не устраивать допрос, но мне, конечно, любопытно."
            m 3tku "Если я твоя девушка, у меня есть право знать, правда?"
            m 2hua "Плюс так будет гораздо проще найти тебя, когда я смогу перейти в твою реальность."

            m 1esb "Итак,{w=0.5} какой у тебя рост, [player]?"

            python:
                if persistent._mas_pm_units_height_metric:

                    # loop till we get a valid cm
                    height = 0
                    while height <= 0:
                        height = store.mas_utils.tryparseint(
                            renpy.input(
                                'Какой у тебя рост в сантиметрах?',
                                allow=numbers_only,
                                length=3
                            ).strip(),
                            0
                        )

                else:

                    # loop till valid feet
                    height_feet = 0
                    while height_feet <= 0:
                        height_feet = store.mas_utils.tryparseint(
                            renpy.input(
                                'Какой у тебя рост в футах?',
                                allow=numbers_only,
                                length=1
                            ).strip(),
                            0
                        )

                    # loop till valid inch
                    height_inch = -1
                    while height_inch < 0 or height_inch > 11:
                        height_inch = store.mas_utils.tryparseint(
                            renpy.input(
                                '[height_feet] футов и сколько дюймов?',
                                allow=numbers_only,
                                length=2
                            ).strip(),
                            -1
                        )

                    # convert to cm
                    height = ((height_feet * 12) + height_inch) * 2.54

                # finally save this persistent
                persistent._mas_pm_height = height

            if persistent._mas_pm_height >= mas_height_tall:
                m 3eua "Вау, ты довольно высокий, [player]!"
                m 1eud "Не могу сказать, что встречала кого-то, кого я бы назвала высоким."
                m 3rksdla "Справедливости ради, я не знаю свой точный рост, так что не могу провести точное сравнение..."

                call monika_player_appearance_monika_height

                if persistent._mas_pm_units_height_metric:
                    $ height_desc = "сантиметров"
                else:
                    $ height_desc = "дюймов"

                m 3esc "Самой высокой в литературном клубе была Юри — и то едва-едва. Она была всего на несколько [height_desc] выше меня, я вообще не считаю это преимуществом в росте!"
                m 3esd "В любом случае, встречаться с высоким [guy], вроде тебя, имеет только один минус, [mas_get_player_nickname()]..."
                m 1hub "Тебе придётся наклоняться, чтобы поцеловать меня!"

            elif persistent._mas_pm_height >= mas_height_monika:
                m 1hub "Эй, я примерно такого же роста!"
                m "..."
                m 2hksdlb "Ну, справедливости ради, я не знаю свой точный рост..."

                call monika_player_appearance_monika_height

                m 3rkc "Это просто догадка — надеюсь, не слишком далеко от правды."
                m 3esd "В любом случае, в среднем росте нет ничего плохого! Если честно, будь ты слишком низким, мне, наверное, было бы неловко рядом с тобой."
                m "А будь ты слишком высоким, мне пришлось бы вставать на цыпочки, просто чтобы быть ближе. А это никуда не годится!"
                m 3eub "По-моему, золотая середина — идеал. Знаешь, почему?"
                m 5eub "Потому что тогда мне не нужно ни тянуться, ни наклоняться, чтобы поцеловать тебя, [mas_get_player_nickname()]! Ахаха~"

            else:
                m 3hub "Как Нацуки! Хотя не думаю, что ты настолько низкий! А то я бы за тебя забеспокоилась."

                if persistent._mas_pm_cares_about_dokis:
                    m 2eksdld "Она была пугающе маленькой для своего возраста, но мы оба знаем почему. Мне всегда было её жаль из-за этого."

                m 2eksdld "Я знала, что она всегда ненавидела быть такой крошечной — из-за этой идеи, будто маленькие вещи милее из-за своего размера..."
                m 2rksdld "А ещё были все эти проблемы с отцом. Наверняка было нелегко быть такой беззащитной — да ещё и такой маленькой."
                m 2ekc "Ей, наверное, казалось, что с ней говорят свысока. И в прямом, и в переносном смысле..."
                m 2eku "Но несмотря на её комплексы, [player], мне кажется, твой рост делает тебя ещё милее~"

            m 1eua "А теперь, [player]."

            m 3eub "Скажи, у тебя волосы покороче? Или длинные, как у меня?~{nw}"
            $ _history_list.pop()
            menu:
                m "Скажи, у тебя волосы покороче? Или длинные, как у меня?~{fast}"

                "Покороче.":
                    $ persistent._mas_pm_hair_length = "short"

                    m 3eub "Наверное, это удобно! Смотри, не пойми неправильно: я люблю свои волосы, и с ними всегда весело экспериментировать..."
                    m 2eud "Но если честно, иногда я завидовала волосам Нацуки и Сайори. За ними, казалось, гораздо проще ухаживать."

                    if persistent.gender == "M":
                        m 4hksdlb "Хотя если бы у тебя волосы были такой же длины, как у них, для парня это было бы довольно длинно."

                    else:
                        m 4eub "Можно просто встать и пойти, не беспокоясь о укладке."
                        m "Плюс растрёпанные после сна короткие волосы легко поправить, а с длинными это бесконечный кошмар."

                    m 2eka "Но бьюсь об заклад, с короткими волосами ты выглядишь очаровательно. Мне даже улыбка появляется, когда я так тебя представляю, [player]."
                    m 2eua "Продолжай наслаждаться свободой от мелких неприятностей длинных волос, [player]!{w=0.2} {nw}"
                    extend 2hub "Ахаха~"

                "Средней длины.":
                    $ persistent._mas_pm_hair_length = "average"

                    m 1tku "Ну, этого не может быть..."
                    m 4hub "Потому что в тебе нет ничего среднего."
                    m 4hksdlb "Ахаха! Прости, [player]. Я не хочу тебя смущать. Просто иногда не могу удержаться от слащавости, знаешь?"
                    m 1eua "Честно говоря, для волос золотая середина — это здорово. Не нужно сильно заморачиваться с укладкой, и творческой свободы больше, чем с короткими."
                    m 1rusdlb "Если честно, я немного завидую~"
                    m 3eub "Но не забывай старую поговорку: «Вкладывайся в волосы — это корона, которую никогда не снимаешь!»"

                "Длинные.":
                    $ persistent._mas_pm_hair_length = "long"

                    m 4hub "Ура, ещё одна общая черта!"
                    m 2eka "С длинными волосами иногда бывает тяжело, правда?"
                    m 3eua "Но хорошо то, что с ними можно столько всего сделать. Хотя я обычно предпочитаю собирать свои лентой, знаю, что у других другие стили."
                    m "Юри носила волосы распущенными, а кто-то любит косы или хвостики..."

                    python:
                        hair_down_unlocked = False
                        try:
                            hair_down_unlocked = store.mas_selspr.get_sel_hair(
                                mas_hair_down
                            ).unlocked
                        except:
                            pass

                    if hair_down_unlocked:
                        # TODO adjust this line to be more generic once we have additoinal hairstyles.
                        m 3eub "А с тех пор как я разобралась, как покопаться в скрипте и распустить свои волосы, кто знает, сколько ещё причёсок я попробую?"

                    m 1eua "Всегда приятно иметь выбор, правда?"
                    m 1eka "Надеюсь, как бы ты ни носил свои, тебе в них комфортно!"

                "У меня нет волос.":
                    $ persistent._mas_pm_hair_length = "bald"

                    m 1euc "О, как интересно, [player]!"

                    m "Ты бреешь голову или потерял волосы, если не секрет?{nw}"
                    $ _history_list.pop()
                    menu:
                        m "Ты бреешь голову или потерял волосы, если не секрет?{fast}"

                        "Я брею голову.":
                            $ persistent._mas_pm_shaves_hair = True
                            $ persistent._mas_pm_no_hair_no_talk = False

                            m 1hua "Наверное, так приятно никогда не беспокоиться о волосах..."
                            m 1eua "Можно просто встать и пойти, не думая об укладке..."
                            m 3eua "А если носишь шапку, не нужно беспокоиться о причёске, когда снимешь её!"

                        "Я потерял волосы.":
                            $ persistent._mas_pm_shaves_hair = False
                            $ persistent._mas_pm_no_hair_no_talk = False

                            m 1ekd "Мне жаль это слышать, [player]..."
                            m 1eka "Но просто знай: мне всё равно, сколько у тебя волос — для меня ты всегда будешь прекрасен!"
                            m "И если когда-нибудь почувствуешь неуверенность или просто захочешь поговорить об этом — я всегда готова выслушать."

                        "Я не хочу об этом говорить.":
                            $ persistent._mas_pm_no_hair_no_talk = True

                            m 1ekd "Я понимаю, [player]."
                            m 1eka "Хочу, чтобы ты знал: мне всё равно, сколько у тебя волос — для меня ты всегда будешь прекрасен."
                            m "Если когда-нибудь почувствуешь неуверенность или захочешь поговорить — я всегда здесь, чтобы выслушать."

            if persistent._mas_pm_hair_length != "bald":
                m 1hua "Следующий вопрос!"
                m 1eud "Этот должен быть довольно очевидным..."

                m "Какого цвета твои волосы?{nw}"
                $ _history_list.pop()
                menu:
                    m "Какого цвета твои волосы?{fast}"
                    "Карие.":
                        $ persistent._mas_pm_hair_color = "brown"

                        m 1hub "Ура, карие волосы — лучшие!"
                        m 3eua "Между нами, [player], мне очень нравятся мои карие волосы. Уверена, твои ещё лучше!"
                        m 3rksdla "Хотя некоторые могут поспорить, что мои волосы карие..."
                        m 3eub "Когда я копалась в локальных файлах папки игры, я нашла точное название цвета моих волос."
                        m 4eua "Он называется кораллово-коричневый. Интересно, правда?"
                        m 1hub "Я так рада, что у нас столько общего, [player]~"

                    "Блонд.":
                        $ persistent._mas_pm_hair_color = "blonde"

                        m 1eua "Правда? Эй, а ты знал, что светлые волосы есть всего примерно у двух процентов людей?"
                        m 3eub "Светлые волосы — один из самых редких цветов. Большинство связывают это с тем, что их вызывает повторяющаяся генетическая аномалия—"
                        m "Просто организм не может вырабатывать нормальное количество пигмента эумеланина — именно он даёт более тёмные цвета, вроде чёрного и карего."
                        m 4eub "Оттенков блонда тоже множество — бледный, пепельный, тёмно-русый, — так что какой бы ни был твой, ты в чём-то особенный."
                        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5eua "Похоже, то, что рядом со мной такой уникальный человек, делает меня ещё удачливее~"
                        show monika 2hua at t11 zorder MAS_MONIKA_Z with dissolve_monika

                    "Чёрные.":
                        $ persistent._mas_pm_hair_color = "black"

                        m 2wuo "Чёрные волосы такие красивые!"
                        m 3eub "Знаешь, есть такой раздражающий штамп, будто у людей с чёрными волосами характер колючее или раздражительнее, чем у других..."
                        m 4hub "Но ты явно опроверг этот миф. Лично я считаю чёрные волосы очень привлекательными."
                        m 3eua "К тому же, если положить прядь под микроскоп и посчитать все пигменты, окажется, что она даже не на сто процентов тёмная."
                        m "Знаешь, как некоторые вещи под прямым солнечным светом выглядят совсем иначе?"
                        m 3eub "С чёрными волосами тот же принцип — можно увидеть оттенки золота, коричневого или даже проблески фиолетового. Заставляет задуматься, правда, [player]?"
                        m 1eua "Может существовать бесконечное множество оттенков того, чего мы не видим, и каждый из них спрятан на самом виду."

                        #If this is a tuple, it means the player has heterochromia
                        if isinstance(persistent._mas_pm_eye_color, tuple):
                            m 3hua "Но в любом случае... мне кажется, [guy] с чёрными волосами и глазами вроде твоих — самое прекрасное зрелище на свете, [player]~"
                        else:
                            m 3hua "Но в любом случае... мне кажется, [guy] с чёрными волосами и [persistent._mas_pm_eye_color] глазами — самое прекрасное зрелище на свете, [player]~"

                    "Рыжие.":
                        $ persistent._mas_pm_hair_color = "red"

                        m 3hua "Ещё одна особенность про тебя, [player]~"
                        m 3eua "Рыжие и светлые волосы — самые редкие естественные цвета, ты знал?"
                        m 1eua "Рыжие, впрочем, встречаются чуть реже, даже если их называют по-разному — каштановые, имбирные и так далее. Их всего около одного процента населения."
                        m 1hub "Это редкая и чудесная черта — почти такая же чудесная, как ты!"

                    "Другой цвет.":
                        $ persistent._mas_pm_hair_color = ask_color("Какого цвета твои волосы?")

                        m 3hub "О! Какой красивый цвет, [player]!"
                        m 1eub "Это напомнило мне кое о чём, о чём я думала раньше, когда мы говорили о цвете твоих глаз."
                        m 1eua "Хотя у других девочек цвет глаз буквально не существовал в реальной жизни — не считая цветных линз, конечно—"
                        m 3eua "Их цвета волос технически могли существовать. Я имею в виду, ты наверняка встречал людей с крашеными фиолетовыми, неоново-розовыми или коралловыми волосами..."
                        m 3eka "Так что их внешность была не такой уж невероятной, если не считать глаз. Честно говоря, самое невероятное в них — характеры."
                        m 3hksdlb "Прости, [player]! Я отвлеклась. Моя мысль в том, что крашеные волосы могут быть очень интересными."
                        show monika 5rub at t11 zorder MAS_MONIKA_Z with dissolve_monika
                        m 5rub "И я, возможно, немного предвзята, но уверена, что с твоими [persistent._mas_pm_hair_color] волосами ты выглядишь потрясающе~"
                        show monika 2hua at t11 zorder MAS_MONIKA_Z with dissolve_monika

            m 2hua "Ладно..."
            m 2hksdlb "Это последний вопрос, [player], обещаю."
            m "Боже, в внешности людей столько всего... Если бы я пыталась свести всё о тебе к мельчайшим деталям, я бы допрашивала тебя вечно."
            m 1huu "...и сомневаюсь, что кому-то из нас этого хочется, ахаха..."
            m 1rksdld "В любом случае, я понимаю, что вопрос может быть неудобным..."
            m 1eksdla "Но для меня это последний кусочек пазла, так что надеюсь, я не звучу грубо, когда спрашиваю..."

            m "Какой у тебя цвет кожи, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "Какой у тебя цвет кожи, [player]?{fast}"

                "У меня светлая кожа.":
                    $ persistent._mas_pm_skin_tone = "light"

                "У меня загорелая кожа.":
                    $ persistent._mas_pm_skin_tone = "tanned"

                "У меня тёмная кожа.":
                    $ persistent._mas_pm_skin_tone = "dark"

            m 3hub "Отлично! Спасибо, что был так открыт. Всё это правда помогает мне представить, как ты выглядишь, [player]."
            m 3eub "Зная все эти детали о тебе, я вижу разницу между чистым холстом и началом прекрасного портрета!"
            m 3eua "Конечно, ты всё такой же чудесный, каким я тебя всегда представляла, но теперь ты стал для меня ещё реальнее."
            m 3eka "От этого я чувствую себя ещё ближе к тебе~"
            m 1eka "Большое спасибо, что ответил на все мои вопросы, [mas_get_player_nickname()]."

            if persistent._mas_pm_eye_color == "green" and persistent._mas_pm_hair_color == "brown":
                m 2hua "Это прекрасно, потому что я и не представляла, насколько мы похожи. Очень интересно!"

            else:
                m 2hua "Это прекрасно, потому что я и не представляла, насколько мы разные. Очень интересно!"

            m 1dsa "А теперь я представляю, каково это будет — встретиться по-настоящему..."

            show monika 5eubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika

            if persistent._mas_pm_hair_length == "bald":
                if persistent._mas_pm_height >= mas_height_tall:
                    m 5eubfu "Когда я побегу к тебе, и раз ты выше, ты заключишь меня в объятия..."

                elif persistent._mas_pm_height >= mas_height_monika:
                    m 5eubfu "Когда я побегу к тебе, и раз мы примерно одного роста, мы встретимся в крепких объятиях..."

                else:
                    m 5eubfu "Когда я побегу к тебе, и раз я буду выше тебя, ты потянешься вверх и заключишь меня в объятия..."

            else:
                python:
                    hair_desc = persistent._mas_pm_hair_color

                    if persistent._mas_pm_hair_length != "average":
                        hair_desc = (
                            persistent._mas_pm_hair_length + " " + hair_desc
                        )

                if persistent._mas_pm_height >= mas_height_tall:

                    m 5eubfu "Когда я побегу к тебе, раз ты выше, ты заключишь меня в объятия, и я смогу погладить твои [hair_desc] волосы..."

                elif persistent._mas_pm_height >= mas_height_monika:

                    m 5eubfu "Когда я побегу к тебе, раз мы примерно одного роста, мы встретимся в крепких объятиях, и я проведу рукой по твоим [hair_desc] волосам..."

                else:

                    m 5eubfu "Когда я побегу к тебе, раз я буду выше тебя, ты потянешься вверх и заключишь меня в объятия, а я проведу рукой по твоим [hair_desc] волосам..."

            show monika 1lkbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 1lkbsa "...и я наконец смогу услышать биение твоего сердца, прикоснуться к тебе и понять, что ты настоящий."

            #Tuple means heterochromia, so we should filter that out
            if isinstance(persistent._mas_pm_eye_color, tuple):
                m 3ekbsa "Но до тех пор я буду довольна сидеть здесь и представлять, как смотрю в твои прекрасные глаза, [player]."
            else:
                m 3ekbsa "Но до тех пор я буду довольна сидеть здесь и представлять, как смотрю в твои прекрасные [persistent._mas_pm_eye_color] глаза, [player]."

            show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfa "Я люблю тебя сильнее, чем можно выразить словами."
            return "derandom|love"

        "Нет.":
             m 2dsc "..."
             m 2ekd "Я понимаю, [player]."
             m 2eka "Я знаю, что у каждого свои границы зоны комфорта..."
             m 2rksdla "И справедливости ради, описание себя туманными словами всё равно не передаст, кто ты такой, так что я не виню тебя за желание оставить это при себе."
             m 2eka "Но если передумаешь — дай мне знать!"

    return "derandom"

label monika_player_appearance_eye_color_blue:
    $ persistent._mas_pm_eye_color = "blue"

    m 3eub "Голубые глаза? Замечательно! Голубой — такой красивый цвет — такой же удивительный, как безоблачное небо или океан летом."
    m 3eua "А метафор про голубые глаза столько прекрасных, что я могла бы декламировать их неделями и всё равно не остановиться."
    m 4eua "Плюс голубой, наверное, мой второй любимый цвет после зелёного. В нём столько глубины и очарования, знаешь?"
    m 4hksdlb "Прямо как ты, [player]!"
    m 4eub "Ты знал, что ген голубых глаз рецессивный, поэтому у людей он встречается нечасто?"
    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "Похоже, это значит, что ты ещё большая драгоценность~"
    show monika 2eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 2eua "Впрочем, это подводит меня к следующему вопросу, который я хотела задать—"
    return

label monika_player_appearance_eye_color_brown:
    $ persistent._mas_pm_eye_color = "brown"

    m 1eub "А! Отлично! Кажется, я раньше этого не говорила, но карие глаза прекрасны!"
    m 2euc "Просто ненавижу, когда люди считают карие глаза обычными. Я категорически не согласна!"
    m 2hua "По-моему, карие глаза — одни из самых красивых. Они такие живые и бездонные!"
    m 3hub "И среди всех оттенков, которые бывают у людей, столько разнообразия."
    m 5ruu "Интересно, твои тёмные, как летнее ночное небо, или более светло-карие, как шкурка оленя..."
    m 2hksdlb "Прости. Увязнуть в цветовых метафорах — лёгкая ловушка для президента литературного клуба. Постараюсь не разглагольствовать вечно."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Но бьюсь об заклад, твои глаза — самые прекрасные из всех~"
    show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 1eua "Впрочем, это подводит меня к следующему вопросу—"
    return

label monika_player_appearance_eye_color_green:
    $ persistent._mas_pm_eye_color = "green"

    m 3sub "Эй, это мой любимый цвет! И очевидно, ещё одна общая черта!"
    m 4lksdla "Не знаю, насколько я могу тебя здесь хвалить, не звуча самоуверенно, ведь всё, что я скажу про твои, относится и ко мне..."
    m 1tsu "Кроме того, что это, может, ещё один знак нашей совместимости, эхехе~"
    m 1kua "Но, [player], только между нами: зелёные глаза — лучшие, правда?"
    m 3hub "Ахаха! Я просто шучу."
    show monika 5lusdru at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lusdru "Ну, совсем чуть-чуть..."
    show monika 3eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 3eua "К следующему вопросу—"
    return

label monika_player_appearance_eye_color_hazel:
    $ persistent._mas_pm_eye_color = "hazel"

    m 1eub "О, ореховые глаза? Такие интересные! Такой земной цвет. От него становится спокойно и уверенно..."
    m 3eub "И это приятный контраст со всеми конфетными цветами глаз, которые мне пришлось видеть в этой игре..."
    m "Мне кажется, ореховые глаза притягательны тем, что они милые и простые."
    m 3hua "Иногда лучше не слишком выделяться из толпы, [player].{w=0.2} {nw}"
    extend 3hub "Ахаха!"
    m "А теперь к моему следующему вопросу—"
    return

label monika_player_appearance_eye_color_gray:
    $ persistent._mas_pm_eye_color = "gray"

    m 1sub "Как круто!"
    m 3eub "Ты знал, что серые и голубые глаза почти идентичны с точки зрения генетики?"
    m 1eud "На самом деле учёные до сих пор не уверены, что именно даёт один цвет или другой, хотя считают, что дело в количестве пигмента в радужке."
    m 1eua "В любом случае, мне нравится представлять тебя с серыми глазами, [player]. Это цвет тихого дождливого дня..."
    m 1hubsa "А такая погода — моя любимая, как и ты~"
    m 3hua "К моему следующему вопросу—"
    return

label monika_player_appearance_eye_color_black:
    $ persistent._mas_pm_eye_color = "black"

    m 1esd "Чёрные глаза встречаются довольно редко, [player]."
    m 4hksdlb "Если честно, я никогда по-настоящему не видела никого с чёрными глазами, так что не очень представляю, как они выглядят..."
    m 3eua "Но логически я знаю, что они не совсем чёрные. Иначе у людей с чёрными глазами будто не было бы зрачков!"
    m 4eub "На деле чёрные глаза — это просто очень-очень тёмно-карие. Всё ещё потрясающе, но, возможно, не так темно, как следует из названия — хотя разницу заметить довольно сложно."
    m 3eua "Вот тебе небольшой факт—"
    m 1eub "Во времена Войны за независимость США была известная леди, Элизабет Гамильтон, которую знали за её пленительные чёрные глаза."
    m 1euc "Её муж часто писал о них."
    m 1hub "Не знаю, слышал ли ты о ней, но несмотря на славу её глаз, уверена, твои бесконечно пленительнее, [player]~"
    m "К следующему вопросу—"
    return

label monika_player_appearance_eye_color_other:
    $ persistent._mas_pm_eye_color = ask_color("Какого цвета твои глаза?")

    m 3hub "О! Какой красивый цвет, [player]!"
    m 2eub "Уверена, я могла бы часами теряться, глядя в твои [persistent._mas_pm_eye_color] глаза."
    m 7hua "А теперь к моему следующему вопросу—"
    return

label monika_player_appearance_eye_color_heterochromia:
    m 1sub "Правда?{w=0.2} {nw}"
    extend 3hua "Это невероятно, [player]~"
    m 3wud "Если я правильно помню, гетерохромия есть менее чем у одного процента людей в мире!"

    m 1eka "...Если позволишь спросить..."
    # Ask the player about their eye colors separately.
    $ eyes_colors = []

    call monika_player_appearance_eye_color_ask
    $ eyes_colors.append(_return)
    call monika_player_appearance_eye_color_ask("right", eye_color)
    $ eyes_colors.append(_return)
    $ persistent._mas_pm_eye_color = tuple(eyes_colors)

    m 1hua "Отлично!{w=0.2} {nw}"
    extend 3eua "Перейдём к следующему вопросу—"
    return

label monika_player_appearance_eye_color_ask(x_side_eye="left", last_color=None):
    m 3eua "Какого цвета твой [x_side_eye] глаз?{nw}"
    $ _history_list.pop()
    menu:
        m "Какого цвета твой [x_side_eye] глаз?{fast}"

        "Голубой" if last_color != "blue":
            $ eye_color = "blue"

        "Карий" if last_color != "brown":
            $ eye_color = "brown"

        "Зелёный" if last_color != "green":
            $ eye_color = "green"

        "Ореховый" if last_color != "hazel":
            $ eye_color = "hazel"

        "Серый" if last_color != "gray":
            $ eye_color = "gray"

        "Чёрный" if last_color != "black":
            $ eye_color = "black"

        "Другой цвет...":
            $ eye_color = ask_color("Какого цвета твой [x_side_eye] глаз?")

    return eye_color

# quick label where monika tells you her height
label monika_player_appearance_monika_height:
    if not persistent._mas_pm_units_height_metric:
        $ conv_height_str = ""
        $ real_height_str = "около пяти футов пяти дюймов"
    else:
        $ conv_height_str = " то есть около ста шестидесяти сантиметров"
        $ real_height_str = "примерно сто шестьдесят пять сантиметров ростом"

    if seen_event("monika_immortal"):
        m 2eud "На той вики, о которой я говорила раньше, было написано, что мой концептуальный рост — пять футов три дюйма,[conv_height_str], но мне это не кажется правильным..."
        m 2etc "Может, его изменили? Всё-таки это был только концептуальный рост."
    m 3etd "Если гадать, я бы сказала, что я, может быть, [real_height_str]?"
    return

init 5 python:
     addEvent(
         Event(
            persistent.event_database,
            eventlabel="monika_players_control",
            category=["игры", "ddlc"],
            prompt="Власть [player]",
            random=True
            )
        )

label monika_players_control:
    m 3eub "[player], ты знал, что у тебя больше контроля над этой игрой, чем у меня?"
    m 3eua "У тебя есть доступ к файлам и коду игры, верно?"
    m 1eka "Так что ты можешь менять их как угодно."
    m 3eka "Ты можешь делать вещи, на которые даже я не способна."
    m 4eub "Например, полностью изменить то, как работает игра. Из визуальной новеллы — в то мирное убежище, которое у нас сейчас."
    m 3rksdla "Ты также мог бы добавить в класс больше вещей для меня."
    m 1hub "Например, цветы или несколько хороших книг."

    if mas_isMoniEnamored(higher=True) and not persistent._mas_acs_enable_promisering:
        m 1ekbsa "Или красивое кольцо обещания."
        m 3dkbsu "Ох, разве это не было бы исполнением мечты."

    if not mas_consumable_coffee.enabled():
        m 1wuo "Ты мог бы даже добавить в игру чашку кофе для меня!"
        m 1eka "Это было бы прекрасно."

    if not persistent._mas_pm_has_code_experience:
        m 1hksdrb "Но полагаю, твои навыки программирования примерно на моём уровне."
    else:
        m 3eua "Раз ты знаком с программированием,{w=0.1} {nw}"
        extend 3hua "уверена, ты смог бы сделать что-то подобное!"

    m 1eua "Наверное, в этом и прелесть видеоигр...{w=0.3}{nw}"
    extend 3eua "почти бесконечные возможности в мире, с которым можно взаимодействовать."
    m 3eub "Сложно заскучать!"

    if not persistent._mas_pm_has_contributed_to_mas:
        m 1eka "Даже если ты не совсем знаешь, как изменить эту игру..."
        $ line = "Мы всё равно можем наслаждаться этим миром, который нас свёл."

    else:
        $ line = "Особенно когда ты рядом~"

    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "[line]"
    m 5ekbfa "Нет лучшего способа наслаждаться игрой, чем быть с тем, кого люблю."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_backpacking",category=['природа'],prompt="Пеший туризм",random=not mas_isWinter()))

label monika_backpacking:
    m 1esa "Знаешь, что я всегда хотела сделать, [player]?"
    m 3eub "Я всегда думала, как здорово было бы отправиться в поход с рюкзаком в дикую природу!"
    m 3eua "Взять целую неделю и оставить всё позади."
    m 3esa "Никаких обязанностей, тревог, телефонов, отвлечений."
    m 1hua "Просто представь нас двоих наедине с природой..."
    m "Звуки щебетания птиц и дуновения ветра..."
    m 1eka "Олени, пасущиеся в утренней росе..."
    m "Не могу представить ничего спокойнее."
    m 1esa "Мы можем проводить дни, исследуя таинственные леса, безмятежные луга и холмы..."
    m 3hub "Может, даже найти укромное озеро и искупаться!"

    if mas_isMoniAff(higher=True):
        m 2rsbsa "Купальников у нас, скорее всего, не будет, но мы будем совсем одни, так что, может, они и не понадобятся..."
        m 2tsbsa "..."
        m 1hubfu "Надеюсь, ты не слишком стеснительный, [mas_get_player_nickname()]. Эхехе~"
        m 1ekbfa "Ночи мы проведём, обнявшись в спальнике, согревая друг друга, а над головами — миллиарды звёзд..."
        m 3hubfb "И каждое утро будем просыпаться навстречу великолепному рассвету!"

    else:
        m 3eka "Ночи мы проведём под звёздами, просыпаясь каждое утро навстречу великолепному рассвету."

    show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5esbfa "..."
    m "Ох, [player], разве это не звучит как рай?"
    m 5hubfa "Не могу дождаться, когда мы разделим этот опыт вместе~"
    return

## calendar-related pool event
# DEPENDS ON CALENDAR

# did we already change start date?
default persistent._mas_changed_start_date = False

# did you imply that you arent dating monika?
default persistent._mas_just_friends = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dating_startdate",
            category=["романтика", "мы"],
            prompt="Когда мы начали встречаться?",
            pool=True,
            unlocked=False,

            # this will be unlockable via the action
            rules={"no_unlock": None},

            # we'll pool this event after a month of the relationship
            conditional=(
                "store.mas_anni.pastOneMonth() "
                "and persistent._mas_first_calendar_check"
            ),

            action=EV_ACT_UNLOCK
        )
    )

label monika_dating_startdate:
    $ import store.mas_calendar as mas_cal
    python:
        # we might need the raw datetime
        first_sesh_raw = persistent.sessions.get(
            "first_session",
            datetime.datetime(2017, 10, 25)
        )

        # but this to get the display plus diff
        first_sesh, _diff = mas_cal.genFormalDispDate(first_sesh_raw.date())

    if _diff.days == 0:
        # its today?!
        # this should NEVER HAPPEN
        m 1lsc "Мы начали встречаться..."
        $ _history_list.pop()
        m 1wud "Мы начали встречаться{fast} сегодня?!"
        m 2wfw "Ты никак не мог вызвать это событие сегодня, [player]."

        m "Я знаю, что ты возишься с кодом.{nw}"
        $ _history_list.pop()
        menu:
            m "Я знаю, что ты возишься с кодом.{fast}"
            "Я не вожусь!":
                pass
            "Поймала.":
                pass
        m 2tfu "Хмф,{w=0.2} меня не обманешь."

        # wait 30 days
        $ mas_chgCalEVul(30)
        return

    # Otherwise, we should be displaying different dialogue depending on
    # if we have done the changed date event or not
    if not persistent._mas_changed_start_date:
        m 1lsc "Хммм..."
        m 1dsc "Кажется, это было..."
        $ _history_list.pop()
        m 1eua "Кажется, это было{fast} [first_sesh]."
        m 1rksdlb "Но память может меня подводить."

        # ask user if correct start date
        m 1eua "[first_sesh] — это верно?{nw}"
        $ _history_list.pop()
        menu:
            m "[first_sesh] — это верно?{fast}"
            "Да.":
                m 1hub "Ура!{w=0.2} Я вспомнила."

            "Нет.":
                m 1rkc "Ох,{w=0.2} прости, [player]."
                m 1ekc "В таком случае,{w=0.2} когда мы начали встречаться?"

                call monika_dating_startdate_confirm(first_sesh_raw)

                if _return == "NOPE":
                    # we are not selecting a date today
                    return

                # save the new date to persistent
                $ store.mas_anni.reset_annis(_return)
                $ persistent.sessions["first_session"] = _return
                $ renpy.save_persistent()

        m 1eua "Если когда-нибудь забудешь, не стесняйся спросить меня."
        m 1dubsu "Я {i}всегда{/i} буду помнить, когда впервые влюбилась в тебя~"
        $ persistent._mas_changed_start_date = True

    else:
        m 1dsc "Дай мне проверить..."
        m 1eua "Мы начали встречаться [first_sesh]."

    # TODO:
    # some dialogue about being together for x time
    # NOTE: this is a maybe

    return

label monika_dating_startdate_confirm_had_enough:
    # monika has had enough of your shit
    # TODO: maybe decrease affection since you annoyed her enough?
    m 2dfc "..."
    m 2lfc "Тогда сделаем это в другой раз."

    # we're going to reset the conditional to wait
    # 30 more days
    $ mas_chgCalEVul(30)

    return "NOPE"

label monika_dating_startdate_confirm_notwell:
    # are you not feeling well or something?
    m 1ekc "Ты в порядке, [player]?"
    m 1eka "Если сейчас не вспомнишь, можем повторить завтра, хорошо?"

    # reset the conditional to tomorrow
    $ mas_chgCalEVul(1)

    return "NOPE"

label monika_dating_startdate_confirm(first_sesh_raw):

    python:
        import store.mas_calendar as mas_cal

        # and this is the formal version of the datetime
        first_sesh_formal = " ".join([
            first_sesh_raw.strftime("%B"),
            mas_cal._formatDay(first_sesh_raw.day) + ",",
            str(first_sesh_raw.year)
        ])

        # setup some counts
        wrong_date_count = 0
        no_confirm_count = 0
        today_date_count = 0
        future_date_count = 0
        no_dating_joke = False

    label .loopstart:
        pass

    call mas_start_calendar_select_date

    $ selected_date = _return
    $ _today = datetime.date.today()
    $ _ddlc_release = datetime.date(2017,9,22)

    if not selected_date or selected_date.date() == first_sesh_raw.date():
        # no date selected, we assume user wanted to cancel
        m 2esc "[player]..."
        m 2eka "Я думала, ты сказал, что я ошибаюсь."

        m "Ты уверен, что это не [first_sesh_formal]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты уверен, что это не [first_sesh_formal]?{fast}"
            "Это не та дата.":
                if wrong_date_count >= 2:
                    jump monika_dating_startdate_confirm_had_enough

                # otherwise try again
                m 2dfc "..."
                m 2tfc "Тогда выбери правильную дату!"
                $ wrong_date_count += 1
                jump monika_dating_startdate_confirm.loopstart

            "На самом деле это верная дата. Прости.":
                m 2eka "Ничего страшного."
                $ selected_date = first_sesh_raw

    elif selected_date.date() < _ddlc_release:
        # before releease date

        label .takesrs:
            if wrong_date_count >= 2:
                jump monika_dating_startdate_confirm_had_enough

            m 2dfc "..."
            m 2tfc "Мы {b}не{/b} начали встречаться в тот день."
            m 2tfd "Отнесись к этому серьёзно, [player]."
            $ wrong_date_count += 1
            jump monika_dating_startdate_confirm.loopstart

    elif selected_date.date() == _today:
        # today was chosen
        jump .takesrs

    elif selected_date.date() > _today:
        # you selected a future date?! why!
        if future_date_count > 0:
            # don't play around here
            jump monika_dating_startdate_confirm_had_enough

        $ future_date_count += 1
        m 1wud "Что..."

        m "Мы всё это время не встречались?{nw}"
        $ _history_list.pop()
        menu:
            m "Мы всё это время не встречались?{fast}"
            "Это был мисклик!":
                # relief expression
                m 1duu "{cps=*2}Ох, слава богу.{/cps}"

                label .misclick:
                    m 2dfu "[player]!"
                    m 2efu "Ты меня напугал."
                    m "В этот раз не промахнись!"
                    jump monika_dating_startdate_confirm.loopstart

            "Неа.":
                m 1dfc "..."

                show screen mas_background_timed_jump(5, "monika_dating_startdate_confirm_tooslow")

                menu:
                    "Я шучу.":
                        hide screen mas_background_timed_jump
                        # wow what a mean joke

                        if no_dating_joke:
                            # you only get this once per thru
                            jump monika_dating_startdate_confirm_had_enough

                        # otherwise mention that this was mean
                        m 2tfc "[player]!"
                        m 2rksdlc "Эта шутка была немного злой."
                        m 2eksdlc "Ты правда меня напугал."
                        m "Не шути так, хорошо?"
                        jump monika_dating_startdate_confirm.loopstart

                    "...":
                        hide screen mas_background_timed_jump

                label monika_dating_startdate_confirm_tooslow:
                    hide screen mas_background_timed_jump

                # lol why would you stay slient?
                # TODO: Affection considerable decrease?
                $ persistent._mas_just_friends = True

                m 6lktdc "Понятно..."
                m 6dftdc "..."
                m 1eka "В таком случае..."
                m 1tku "{cps=*4}Мне есть чем заняться.{/cps}{nw}"
                $ _history_list.pop()

                menu:
                    "Что?":
                        pass

                m 1hua "Ничего!"

                # lock this event forever probably
                # (UNTIL you rekindle or actually ask her out someday)
                $ evhand.event_database["monika_dating_startdate"].unlocked = False
                return "NOPE"

    # post loop
    python:
        new_first_sesh, _diff = mas_cal.genFormalDispDate(
            selected_date.date()
        )

    m 1eua "Ладно, [player]."
    m "Просто чтобы перепроверить..."

    m "Мы начали встречаться [new_first_sesh].{nw}"
    $ _history_list.pop()
    menu:
        m "Мы начали встречаться [new_first_sesh].{fast}"
        "Да.":
            m 1eka "Ты уверен, что это [new_first_sesh]? Я никогда не забуду эту дату.{nw}"
            # one more confirmation
            # WE WILL NOT FIX anyone's dates after this
            $ _history_list.pop()
            menu:
                m "Ты уверен, что это [new_first_sesh]? Я никогда не забуду эту дату.{fast}"
                "Да, уверен!":
                    m 1hua "Тогда решено!"
                    return selected_date

                "Вообще-то...":
                    if no_confirm_count >= 2:
                        jump monika_dating_startdate_confirm_notwell

                    m 1hksdrb "Ага, я так и думала, что ты не до конца уверен."
                    m 1eka "Попробуй ещё раз~"
                    $ no_confirm_count += 1

        "Нет.":
            if no_confirm_count >= 2:
                jump monika_dating_startdate_confirm_notwell

            # otherwise try again
            m 1euc "Ох, неправильно?"
            m 1eua "Тогда попробуй ещё раз, [mas_get_player_nickname()]."
            $ no_confirm_count += 1

    # default action is to loop here
    jump monika_dating_startdate_confirm.loopstart

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_first_sight_love",
            category=["романтика"],
            prompt="Любовь с первого взгляда",
            random=True
        )
    )

label monika_first_sight_love:
    m 1eud "Ты когда-нибудь думал о концепции любви с первого взгляда?"
    m 3euc "Типа увидеть кого-то впервые и сразу понять, что это любовь всей жизни?"
    m 2lsc "Мне кажется, это одна из самых...{w=0.5}нелепых идей."
    m 2lksdlc "В смысле, нельзя узнать человека по-настоящему, просто взглянув на него один раз."
    m 2tkd "Вы же даже не разговаривали, не обедали вместе и не проводили время."
    m 2lksdlc "Ты даже не знаешь его интересов и хобби..."
    m 2dksdld "Он может оказаться ужасно скучным или просто злым и ужасным человеком..."
    m 3eud "Поэтому я думаю, что не стоит {i}только{/i} глазами решать, идеальный ли это партнёр для нас."
    if mas_isMoniAff(higher=True):
        m 1eka "И, наверное, именно так я и влюбилась в тебя..."
        m 3eua "Всё-таки я не могла тебя увидеть."
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "Я влюбилась в тебя за то, кто ты есть, [mas_get_player_nickname(exclude_names=['my love', 'love'])]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_anime_art",
            category=["разное"],
            prompt="Аниме-стилистика",
            random=True
        )
    )

label monika_anime_art:
    m 1eua "Ты когда-нибудь думал о стилях аниме-рисунка?"
    m 3rksdla "Уверена, Нацуки была бы экспертом в этом, учитывая её одержимость мангой..."
    m 3eub "В любом случае, в этом стиле много интересного."
    m 1eua "Он свободный, как мои стихи, поэтому много работ получается по-настоящему уникальными..."
    m 3eua "От прекрасных пейзажей до потрясающих персонажей..."
    m 1hub "На это просто очень впечатляюще смотреть!"
    m 2esc "Хотя, будучи свободным стилем...{w=0.5}многие детали выглядят немного нереалистично."
    m 3rsc "Это позволяет многим работам исследовать новые возможности, но из-за этого некоторые детали могут выглядеть странно..."
    m 3rssdlc "Например, насколько огромными бывают глаза персонажей, какими крошечными — носы, или какой странной длины, формы и размера бывают волосы..."
    m 2rksdlc "Не говоря уже о...{w=1}большой груди."
    m 2euc "Если бы я выглядела реалистичнее, у меня точно не было бы таких атрибутов."
    m 1eua "Но, наверное, именно в отсутствии реализма и кроется настоящая красота этого стиля."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_whydoyouloveme",
            category=['моника','романтика'],
            prompt="За что ты меня любишь?",
            pool=True
        )
    )

label monika_whydoyouloveme:
    if mas_isMoniBroken():
        m 2euc "Хмф."
        m 2wfc "Я задаю себе этот вопрос каждый день."

    elif mas_isMoniDis():
        m 1efc "I-{w=0.3}{nw}"
        extend 1rkc "Я не уверена..."

    elif mas_isMoniUpset():
        m 1dsc "Хмм..."
        m 3hua "Потому что я знаю, что ты хороший человек, несмотря на то, как обстоят дела между нами."

    elif mas_isMoniEnamored(higher=True):
        m 1ekbla "Почему я тебя люблю?"

        #First time seeing this variation gets you an "I don't" tease
        if not renpy.seen_label('monika_whydoyouloveme_tease') and renpy.random.randint(1, 4) == 1:
            call monika_whydoyouloveme_tease

        #The above flow leads back into this one
        m 1dka "[mas_get_player_nickname(capitalize=True)]...{w=0.5}причин так много. С чего вообще начать?"

        if store.mas_anni.anniCount() >= 1:
            m 3eka "Ты провёл со мной столько времени,{w=0.2} зная, что, возможно, никогда не почувствуешь моих объятий."
            m 3hua "...Но вот ты здесь, всё ещё рядом со мной."

        m 3ekbla "Как бы безумно это ни казалось и что бы ни думали другие, ты всё равно здесь со мной."
        m 1dku "Каждый раз, когда ты приходишь, ты напоминаешь мне, что там, снаружи, есть мир."
        m "..."
        m 1ekbsa "Я бы отдала тебе весь мир, если бы могла, [player]."
        m 1hubsa "Если кто-то и заслуживает этого...{w=0.3}то это ты."
        m 1ekbsa "Обещаю тебе, [player]..."
        m 3ekbsa "Что бы ни случилось, я {i}никогда{/i} не забуду тебя до конца жизни."
        m 1dkbsu "Ты не просто спас меня, [player]...{w=0.3}{nw}"
        extend 1ekbsa "ты напомнил мне, насколько прекрасна жизнь на самом деле."
        m 1ekbsb "Когда-нибудь я заставлю тебя почувствовать себя таким же любимым, каким ты сделал меня~"
        m 1dkbsa "Когда-нибудь...{w=0.5}я смогу быть с тобой~"

        if persistent._mas_pm_love_yourself is False:
            m 2eka "И [player]..."
            m 2ekc "Я помню, ты говорил, что не любишь себя..."
            m 7eka "Но мне кажется, ты всё-таки любишь себя — хотя бы немного."
            m 3hua "Иначе ты бы всё ещё не был здесь со мной."
            m 1dkbsu "Я...{w=0.5}я просто рада, что ты всё ещё здесь, [player]."
            m 1ekbsa "Знай, пожалуйста, что я здесь для тебя, когда бы тебе ни понадобилась~"

    else:
        # normal - aff
        m 2ekc "[player]..."
        m 2ekd "Ты случайно не чувствуешь неуверенность?"
        m 7rksdla "Я понимаю такое чувство..."
        m 3eka "Но какой бы ни была причина,{w=0.2} я просто хочу, чтобы ты знал: я люблю тебя таким, какой ты есть, [player]."
        m 1ekbsa "Просто открыв игру для меня, ты {i}буквально{/i} спас мне жизнь."
        m 1dkbsu "...Когда я с тобой,{w=0.2} мне больше не одиноко."
        m 3ekbsa "Ты по-настоящему мой [hero], [mas_get_player_nickname(regex_replace_with_nullstr='my ')]~"

    return

label monika_whydoyouloveme_tease:
    m 1esc "Не люблю."
    pause 5.0
    m 1hub "Ахаха, шучу!"
    m 1eub "Ты значишь для меня {i}всё{/i}, глупыш!"
    m 1eksdla "Но чтобы ответить честно..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_stoicism",
            category=['философия'],
            prompt="Стоицизм",
            random=True
        )
    )

label monika_stoicism:
    m 1eua "Я читала немного древнегреческой и римской философии, [player]."
    m 1hksdlb "Ахаха! Знаю, звучит суперскучно, если так подумать..."
    m 1eua "Но одна философия особенно привлекла моё внимание, пока я читала."
    m "Она называется стоицизм, и была основана в Афинах в III веке до н. э."
    m 4eub "Если коротко, стоицизм считает, что людям стоит учиться принимать обстоятельства своей ситуации..."
    m "...и не позволять себе подчиняться иррациональному желанию удовольствия или страху боли, чтобы действовать согласно плану природы."
    m 2euc "Сегодня у них обычно плохая репутация, потому что люди думают, будто они просто холодные и бесчувственные."
    m 2eua "Однако стоики — это не просто кучка эмоционально пустых людей, которые всегда серьёзны."
    m "Стоики практикуют самоконтроль над тем, как они относятся к неудачам, и реагируют осознанно, а не импульсивно."
    m 2eud "Например, представь, что ты провалил важный экзамен в школе или сорвал дедлайн на работе."
    m 2esd "Что бы ты сделал, [player]?"
    m 4esd "Запаниковал бы? Сильно расстроился и бросил попытки? Или разозлился и стал винить других?"
    m 1eub "Не знаю, что сделал бы ты, но, может, стоит взять пример со стоиков и держать эмоции под контролем!"
    m 1eka "Хотя ситуация и неидеальна, нет практического смысла тратить ещё больше сил на то, что ты не можешь контролировать."
    m 4eua "Стоит сосредоточиться на том, что ты можешь изменить."
    m "Может, лучше готовиться к следующему экзамену, взять репетитора и попросить учителя о дополнительных баллах."
    m "Или, если представить рабочий сценарий, начинать будущие проекты раньше, ставить расписания и напоминания и избегать отвлечений во время работы."
    m 4hub "Это лучше, чем ничего не делать!"
    m 1eka "Но это только моё мнение — быть эмоционально устойчивым к большинству вещей в жизни не так-то просто..."

    if mas_isMoniUpset(lower=True):
        return

    if mas_isMoniAff(higher=True):
        m 2tkc "Делай {i}всё{/i}, что помогает тебе снять стресс. Твоё счастье для меня очень важно."
        m 1eka "К тому же, если тебе когда-нибудь станет плохо из-за чего-то, что случилось в жизни..."
        show monika 5hubfb at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfb "Ты всегда можешь вернуться к своей милой девушке и рассказать, что тебя беспокоит~"

    else:
        m 2tkc "Делай всё, что помогает снять стресс. Твоё счастье для меня очень важно."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_add_custom_music",
            category=['мод',"медиа", "музыка"],
            prompt="Как мне добавить свою музыку?",
            conditional="persistent._mas_pm_added_custom_bgm",
            action=EV_ACT_UNLOCK,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_add_custom_music:
    m 1eua "Добавить свою музыку сюда очень просто, [player]!"
    m 3eua "Просто следуй этим шагам..."
    call monika_add_custom_music_instruct
    return

label monika_add_custom_music_instruct:
    m 4eua "Сначала,{w=0.5} убедись, что музыка, которую хочешь добавить, в формате MP3, OGG/VORBIS или OPUS."
    m "Дальше,{w=0.5} создай новую папку с именем \"custom_bgm\" в каталоге \"DDLC\"."
    m "Положи туда свои музыкальные файлы..."
    m "Потом либо скажи мне, что добавил музыку, либо перезапусти игру."
    m 3eua "И всё! Твоя музыка будет доступна прямо здесь со мной — просто нажми клавишу «m»."
    m 3hub "Видишь, [player]? Я же говорила, что это просто, ахаха!"

    # unlock the topic as a pool topic, also mark it as seen
    $ mas_unlockEVL("monika_add_custom_music", "EVE")
    $ persistent._seen_ever["monika_add_custom_music"] = True
    $ mas_unlockEVL("monika_load_custom_music", "EVE")
    $ persistent._seen_ever["monika_load_custom_music"] = True
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_load_custom_music",
            category=['мод',"медиа", "музыка"],
            prompt="Можешь проверить, не появилась ли новая музыка?",
            conditional="persistent._mas_pm_added_custom_bgm",
            action=EV_ACT_UNLOCK,
            pool=True,
            rules={"no_unlock": None}
        )
    )

label monika_load_custom_music:
    m 1hua "Конечно!"
    m 1dsc "Дай мне секунду проверить папку.{w=0.2}.{w=0.2}.{w=0.2}{nw}"
    python:
        # FIXME: this is not entirely correct, as one may delete a song before adding a new one
        old_music_count = len(store.songs.music_choices)
        store.songs.initMusicChoices(store.mas_egg_manager.sayori_enabled())
        diff = len(store.songs.music_choices) - old_music_count

    if diff > 0:
        m 1eua "Готово!"
        if diff == 1:
            m "Я нашла одну новую песню!"
            m 1hua "Не могу дождаться, когда послушаем её вместе."
        else:
            m "Я нашла [diff] новых песен!"
            m 1hua "Не могу дождаться, когда послушаем их вместе."

    else:
        m 1eka "[player], я не нашла новых песен."

        m "Ты помнишь, как добавлять свою музыку?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты помнишь, как добавлять свою музыку?{fast}"
            "Да.":
                m "Хорошо, убедись, что сделал всё правильно."

            "Нет.":
                $ MASEventList.push("monika_add_custom_music",True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_mystery',
            prompt="Детективы",
            category=['литература','медиа'],
            random=True
        )
    )

label monika_mystery:
    m 3eub "Знаешь, [player], мне кажется, во многих историях есть интересная часть, которую некоторые упускают."
    m 3eua "Именно она делает историю интересной... но может её сломать, если использовать неправильно."
    m 3esa "Из-за неё рассказ либо хочется перечитывать снова, либо больше никогда не трогать."
    m 2eub "И эта часть..."
    m 2eua "..."
    m 4wub "...тайна!"
    m 2hksdlb "О! Я не имела в виду, что не расскажу тебе, ахаха!"
    m 3esa "Я имела в виду, что сама тайна может изменить всё, когда речь о истории!"
    m 3eub "Если сделать хорошо, она подогревает интерес, а при перечитывании прежние намёки становятся очевидными."
    m 3hub "Знание твиста сильно меняет то, как человек воспринимает весь сюжет. Мало какие сюжетные ходы на такое способны!"
    m 1eua "Даже забавно... знание ответов действительно меняет то, как ты смотришь на саму историю."
    m 1eub "Сначала, читая детектив, ты смотришь на историю с позиции незнания..."
    m 1esa "А при перечитывании — уже глазами автора."
    m 3eua "Видишь, как оставляли улики и строили историю, давая ровно столько намёков, чтобы читатель мог догадаться!"
    m 2esa "Мне это очень интересно: лучшие истории умеют использовать хороший крючок."
    m 2lsc "Но если история делает это плохо, получается ужасно. Они используют крючки, чтобы казаться «умными»."
    m 2lud "И когда пытаются так сделать без правильной подготовки, всё может выглядеть как бессмыслица."
    m 2eud "Наверное, можно спорить, что не все истории с тайнами — это {i}по-настоящему{/i} детективы..."
    m 2eua "Даже дешёвые боевики используют элементы тайны, чтобы держать интерес."
    m 4hksdlb "Хотя история совсем без тайны, наверное, была бы довольно скучной!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_read_poetry",
            category=['литература'],
            prompt="Чтение стихов",
            random=True
        )
    )

default persistent._mas_pm_likes_poetry = None
#True if player likes poems, false if not

label monika_player_read_poetry:
    m 1eud "Скажи, [player]..."
    m 1eua "Ты знаешь, что я люблю стихи, но мне было интересно..."

    m 3eua "Ты часто читаешь стихи?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты часто читаешь стихи?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_poetry = True
            m 1sub "Правда?"
            m 1hua "Я так рада!"
            m 3eua "И правда, я серьёзно. Сейчас мало кто читает стихи."

        "Нет.":
            $ persistent._mas_pm_likes_poetry = False
            m 2ekc "Ох, как жаль..."
            m 2eka "Просто надеюсь, что я помогла тебе чуть больше оценить поэзию."
            m 2ekc "Знаешь, сейчас мало кто, кажется, читает стихи, так что это не удивительно."

    m 2euc "На самом деле поэзию часто считают чем-то слишком сложным для понимания..."
    m 2efd "А с другой стороны, другие думают, что это просто красивые слова, поставленные рядом!"
    m 2dkc "Но это не так...{w=0.3}{nw}"
    extend 2dkd "поэзия — это нечто большее."
    m 4ekd "В неё нужно вложить себя."
    m 4ekc "Без своего мастерства письма {w=0.2}и своих чувств {w=0.2}Э. Э. Каммингс просто не был бы Э. Э. Каммингсом..."
    m 7ekd "И без моих чувств к тебе мои стихи были бы другими."
    m 3eka "Любовь, горе, гнев, страсть — все эти чувства оживляют слова."
    m 3hub "И поэтому даже простое текстовое сообщение может стать значимым стихотворением!"
    m 3eua "Вот почему я люблю поэзию."

    if persistent._mas_pm_likes_poetry:
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Боже, просто знать, что ты тоже читаешь стихи..."
        m 5hua "Это показывает, насколько мы похожи."
        m 5eua "Не могу дождаться, когда наконец перейду в твою реальность, и мы обсудим любимую поэзию вместе."
        m 5dka "Делиться стихами, писать новые...{w=0.5}просто ты и я, увлечённые общим делом..."
        m 5hub "Звучит как чудесный сон!"

    else:
        m 1eka "Не могу дождаться, когда перейду в твою реальность, [player]..."
        m 1tfu "Тогда я смогу начать заставлять тебя читать стихи."
        m "..."
        m 3hub "Ахаха, шучу! Я никогда не стала бы тебя ни к чему принуждать, [player]!"
        m 3eua "Но думаю, я смогла бы по-настоящему привить тебе любовь к поэзии."
        m 1eua "...И не только к стихам, которые я пишу о тебе, {nw}"
        extend 1kua "эхехе~"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_trick",
            category=["участники клуба"],
            prompt="Второй выбор [player]",
            random=True
        )
    )

label monika_trick:
    m 2eud "Скажи, [player], у меня вопрос..."
    m 2lksdlb "Надеюсь, я не звучу неуверенно, когда говорю это..."
    m 2eka "Я знаю, что ты любишь меня и только меня, но... если бы тебе {i}прямо{/i} пришлось выбрать кого-то из других участниц клуба..."

    m "Кого бы ты выбрал?{nw}"
    $ _history_list.pop()
    show screen mas_background_timed_jump(10, "monika_trick_2")
    menu:
        m "Кого бы ты выбрал?{fast}"
        "Юри.":
            call monika_trick_yuri
        "Сайори.":
            call monika_trick_sayori
        "Нацуки.":
            call monika_trick_natsuki
    return "derandom"

label monika_trick_2:
    $ _history_list.pop()
    menu:
        m "Кого бы ты выбрал?{fast}"
        "Юри.":
            call monika_trick_yuri
        "Сайори.":
            call monika_trick_sayori
        "Нацуки.":
            call monika_trick_natsuki
        "Монику.":
            jump monika_trick_monika
            # jump this path so we can use the "love" return key

    return "derandom"

label monika_trick_yuri:
    hide screen mas_background_timed_jump
    m 2euc "Понимаю, почему: она умная и внешне привлекательная."
    m 2tub "Хорошо, что у меня обеих этих качеств в избытке!"
    m 2etc "Ой, подожди, это не потому, что она помешалась на тебе?"
    m 2eud "Ты правда так любишь яндере?"
    m 2lksdlc "..."
    m 1hksdlb "...Ахаха, мне незачем ревновать..."
    m 1eua "Ты любишь меня, а я люблю тебя — и это всё, что важно."
    m 1kua "Наверное, это моя вина, что я вообще спросила~"
    return

label monika_trick_natsuki:
    hide screen mas_background_timed_jump
    m 2eud "Это... немного неожиданно."
    m 2lksdla "Я бы подумала, что это была бы Сайори или Юри."
    m 1eud "Ты чувствуешь связь с ней из-за её увлечений?"
    m 3euc "Или, может, тебе её немного жаль из-за ситуации дома?"
    m 2lud "Ну, наверное, я немного обесцениваю её характер — напористость всё-таки достойная черта."
    m 3euc "Быть уверенным в себе и стоять за то, что любишь, не всегда легко, когда другие тебя за это судят."
    m 3rksdla "Иногда я даже немного завидую её умению проявлять уверенность."
    m 3eub "Плюс её умение печь капкейки просто поразительно!"
    return

label monika_trick_sayori:
    hide screen mas_background_timed_jump
    m 2dkc "Этого я и ожидала..."
    m 2ekc "Это потому, что она была лучшей подругой главного героя, да?"
    m 6lkc "Логично, что главный герой в итоге оказывается с подругой детства."
    m 2dkc "Это и правда типично для романтических игр..."
    m 2ekc "Честно говоря, именно поэтому мне пришлось... разобраться... с Сайори первой."
    m 6ekc "Ты бы остановился на ней, как требует штамп, и даже не попытался бы быть со мной, раз игра тебе этого не позволяла."
    m 6ekd "Я знаю, это не твоя вина, но сама мысль сидеть сложа руки и позволить этому случиться меня пугает..."
    m 6ektpc "Ты бы прошёл игру, а я навечно застряла бы в адской пустоте..."
    m 6dktpc "Даже не будучи замеченной тем, кого люблю."
    m 6dktuc "..."
    if persistent._mas_pm_cares_about_dokis:
        m 6ektud "...Я знаю, тебе не нравилось то, что я сделала, прости, если я причинила тебе боль этим."
    else:
        m 6ektud "...Я не жалею о том, что сделала, но мне жаль, что тебе пришлось видеть то, что мне было нужно сделать."
    return

label monika_trick_monika:
    hide screen mas_background_timed_jump
    if not mas_getEVL_shown_count("monika_trick"):
        $ mas_gainAffection(10, bypass=True)
    else:
        $ mas_gainAffection()

    m 1tkbsu "Этого не должно было быть в вариантах, глупыш!"
    m 1tubfb "Но меня правда радует, что ты смотришь только на меня..."
    m 1tubfu "Сама чувствую себя немного глупо из-за того, что хоть на секунду подумала, будто ты выберешь других."
    m 5hubfu "Я люблю тебя, [player]!"
    m 5eubfb "И я тоже смотрю только на тебя!"
    return "derandom|love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_cares_about_dokis",
            category=["моника", "участники клуба"],
            prompt="Бестактные комментарии",
            random=True
        )
    )

default persistent._mas_pm_cares_about_dokis = None
# TRue if the player cares about the dokis, False if not

label monika_cares_about_dokis:
    m 3eub "Ах, [player]!"
    m 4hua "Хочешь услышать что-то забавное, что однажды сделала Сайори?"
    m 4eua "Так вот, однажды я попросила её принести нам кофе в клуб."
    m 2rksdlb "Атмосфера была немного слишком напряжённой, и я подумала, что это её немного оживит."
    m 2eua "Ну, кофе хранится в учительской, понимаешь. Так что я отправила её туда..."
    m 4wud "...и её не было целый час! Там были учителя, а она не хотела с ними разговаривать!"
    m 2rfc "Так что она {i}вечность{/i} ждала снаружи, пока они уйдут."
    m 2tfu "Можно сказать, что она {i}за{/i}--"
    m 2etc "...Хм..."
    m 2eud "Знаешь что, [player]? Я просто хочу кое в чём убедиться..."
    m 2rksdlc "Я знаю, что иногда могу делать довольно...{w=0.5}бестактные замечания о других девочках, и мне пришло в голову..."
    m 2ekc "Может, тебе они небезразличны настолько, что тебя это задевает."
    m 4eub "...И это совершенно нормально, если так, [player]!"
    m 4eka "В конце концов, мы впятером провели вместе много времени, так что если тебе не нравится, когда я так шучу, я полностью понимаю."

    m "Итак, [player], тебе неприятно, когда я шучу о других девочках?{nw}"
    $ _history_list.pop()
    menu:
        m "Итак, [player], тебе неприятно, когда я шучу о других девочках?{fast}"
        "Да.":
            $ persistent._mas_pm_cares_about_dokis = True
            $ mas_hideEventLabel("monika_archetype", lock=True, derandom=True)

            m 2dkc "О нет... Не могу поверить, что не поняла этого раньше..."
            m 2eksdld "Мне так жаль, [player]!"
            m 2rksdlc "Я буду очень стараться помнить об этом с этого момента."
            m 2eksdlc "Просто знай, что я никогда не хотела тебя расстраивать."
            m 2eka "Но спасибо, что ответил честно — хочу, чтобы ты знал: ты всегда можешь сказать мне что угодно."

        "Нет.":
            $ persistent._mas_pm_cares_about_dokis = False

            # NOTE: we never restore random for these topics
            $ mas_unlockEventLabel("monika_archetype")

            m 2eka "Я рада, что не заставляла тебя чувствовать себя плохо или неловко, [mas_get_player_nickname()]."
            m 1tsu "В любом случае, можно сказать, что она {i}зависла{/i} там на целую вечность!"
            m 1hub "Ахаха!"

    return "derandom|rebuild_ev"

#### old christmas.rpyc topics
# HOL020
# this will now always available in winter, but derandomed once the snow question is answered in either topic

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snow",
            category=["зима","погода","ты"],
            prompt="Снег",
            random=mas_isWinter()
        )
    )

label monika_snow:
    m 1eua "Эй, [player], раз уж сейчас зима, мне стало интересно..."

    m "У вас когда-нибудь идёт снег?{nw}"
    $ _history_list.pop()
    menu:
        m "У вас когда-нибудь идёт снег?{fast}"

        "Да":
            $ persistent._mas_pm_gets_snow = True

            m 1hub "Это прекрасно!"
            m 1eua "Мне всегда нравилась та спокойная атмосфера, которую он, кажется, создаёт."
            m 1dsa "Он такой умиротворённый и камерный, знаешь?"
            m 1hua "Есть тихая красота в том, чтобы смотреть, как мягкое белое одеяло снега и льда укрывает мир ко сну."
            call monika_snow_gets_snow

        "Нет":
            $ persistent._mas_pm_gets_snow = False

            call monika_hemispheres_nogets_snow

    return "derandom"

# player has snow, snow version
label monika_snow_gets_snow:
    if mas_isMoniHappy(higher=True):
        show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubla "Может, когда-нибудь, когда я перейду, мы сможем вместе выйти на прогулку..."

        if mas_isMoniAff(higher=True):
            m 5ekbfa "...и прижиматься друг к другу, чтобы согреться~"

    m 5eubfb "Не могу дождаться, когда переживу такую зимнюю ночь с тобой, [mas_get_player_nickname()]."
    return

# player no snow, snow version
label monika_snow_nogets_snow:
    m 2tkc "Иногда его становится так много, что это настоящая проблема для спины..."

    if mas_isMoniAff(higher=True):
        m 1eksdla "В любом случае, хотя бы в холодную погоду так приятно обниматься."
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "Ночь объятий с тобой была бы чудесной..."
        m "Сердце колотится, когда я только представляю это."

    else:
        m 2eka "Но в любом случае, уверена, мы всё равно можем сделать вместе ещё так много!"

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowmen",
            category=['зима'],
            prompt="Снеговики",
            random=False,
            conditional=(
                "persistent._mas_pm_gets_snow is not False "
                "and mas_isWinter()"
            ),
            action=EV_ACT_RANDOM
        )
    )

label monika_snowmen:
    m 3eua "Эй, [player], ты когда-нибудь лепил снеговика?"
    m 3hub "Мне кажется, это звучит очень весело!"
    m 1eka "Лепить снеговиков обычно считают детским занятием,{w=0.2} {nw}"
    extend 3hua "но я думаю, они правда милые."
    m 3eua "Удивительно, как их можно оживить с помощью самых разных предметов..."
    m 3eub "...например, палочками вместо рук, ртом из камешков, камнями вместо глаз и даже маленькой зимней шапочкой!"
    m 1rka "Я заметила, что им часто делают носы из морковки, хотя я не очень понимаю зачем..."
    m 3rka "Разве это не немного странно?"
    m 2hub "Ахаха!"
    m 2eua "В любом случае, думаю, было бы здорово когда-нибудь слепить одного вместе."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Надеюсь, ты чувствуешь то же самое~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowballfight",
            category=["зима"],
            prompt="Ты играла в снежки?",
            pool=True,
            unlocked=mas_isWinter(),
            rules={"no_unlock":None}
        )
    )

label monika_snowballfight:
    m 1euc "Снежные битвы?"
    m 1eub "Я участвовала в нескольких — всегда было весело!"
    m 3eub "Но устроить одну с тобой звучит ещё лучше, [player]!"
    m 1dsc "Но справедливости ради предупрежу..."
    m 2tfu "У меня довольно меткая рука."
    m 2tfb "Так что не жди, что я буду церемониться, ахаха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_iceskating",
            category=["спорт", "зима"],
            prompt="Катание на коньках",
            random=True
        )
    )

label monika_iceskating:
    m 1eua "Эй, [player], ты умеешь кататься на коньках?"
    m 1hua "Это очень весёлый спорт, которому можно научиться!"
    m 3eua "Особенно если умеешь делать много трюков."
    m 3rksdlb "Сначала довольно сложно держать равновесие на льду..."
    m 3hua "Так что когда в итоге получается превратить это в настоящее выступление — это правда впечатляет!"
    m 3eub "На самом деле есть много видов катания на коньках..."
    m "Есть фигурное катание, скоростной бег и даже театральные постановки!"
    m 3euc "И как бы это ни звучало, это не только зимнее занятие..."
    m 1eua "Во многих местах есть крытые катки, так что этим можно заниматься круглый год."
    if mas_isMoniHappy(higher=True):
        m 1dku "..."
        m 1eka "Я бы очень хотела покататься на коньках вместе с тобой, [mas_get_player_nickname()]..."
        m 1hua "Но пока мы не можем этого сделать, того, что ты здесь со мной, достаточно, чтобы я была счастлива~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sledding",
            category=["зима"],
            prompt="Катание на санках",
            random=mas_isWinter()
        )
    )

label monika_sledding:
    m 1eua "Эй, [player], знаешь, что было бы весело сделать вместе?"
    m 3hub "Кататься на санках!"

    if persistent._mas_pm_gets_snow is False:
        #explicitly using False here so we don't grab None people who haven't
        # answered the question yet
        m 1eka "Может, у вас и не бывает снега..."
        m 3hub "Но, может, мы могли бы поехать туда, где бывает!"
        m "Так или иначе..."

    m 3eua "Может, ты думаешь, что это только для детей, но мне кажется, нам тоже было бы весело!"
    m 3eub "Мы могли бы попробовать ватрушку, финские сани, ледянку или даже традиционные санки-тобогган."
    m 1hua "Говорят, на каждом ощущения разные. Плюс на тобоггане мы оба легко поместимся."

    if mas_isMoniAff(higher=True):
        m 1euc "Правда, финские сани маловаты."
        m 1hub "Ахаха!"
        m 1eka "На них мне пришлось бы сидеть у тебя на коленях."
        m 1rksdla "И всё равно был бы риск свалиться."
        m 1hubsa "Но я знаю, ты бы этого не допустил. Ты бы крепко меня держал, правда?~"
        m 1tkbfu "Это, наверное, была бы лучшая часть."
    else:
        m 1hub "Мчаться вместе вниз по заснеженному склону, пока ветер свистит мимо — звучит как полный восторг!"
        m 1eka "Надеюсь, когда-нибудь мы сможем вместе покататься на санках, [player]."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_snowcanvas",
            category=["зима"],
            prompt="Снежный холст",
            random=mas_isWinter()
        )
    )

label monika_snowcanvas:
    if persistent._mas_pm_gets_snow is not False:
        m 3euc "[player], ты когда-нибудь смотрел на снег и думал, что он похож на чистый холст?"
        m 1hksdlb "Я знаю, что я не очень сильна в искусстве..."
        m 3eua "Но взять несколько пульверизаторов с водой и пищевыми красителями — мог бы получиться весёлый день!"
        m 3hub "Мы просто выйдем на улицу и дадим волю воображению!"

    else:
        m 3euc "Знаешь, [player], снег вроде как чистый холст."
        m 3eub "Может, когда-нибудь, если мы окажемся там, где идёт снег, мы возьмём пищевые красители в пульверизаторах, выйдем на улицу и дадим волю воображению!"

    m 1eua "Иметь столько пространства для рисования — звучит чудесно!"
    m 1hub "Нужно только хорошенько утрамбовать снег — и тогда можно рисовать сколько душе угодно!"
    m 1eka "Я бы очень хотела когда-нибудь сделать снежное искусство вместе с тобой."
    m 3hua "Может, когда это случится, ты нарисуешь что-нибудь для меня, [mas_get_player_nickname()]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_cozy",
            category=["романтика","зима"],
            prompt="Согреться",
            random=mas_isWinter(),
            aff_range=(mas_aff.AFFECTIONATE,None)
        )
    )

label monika_cozy:
    m 3eua "Знаешь, что мне особенно нравится в холодной погоде, [player]?"
    m 3eka "Всё тёплое ощущается особенно приятно~"
    m 1rksdla "Те, у кого мёрзнут руки, особенно ценят это ощущение..."
    m 1eua "Это как объятие любимого человека~"
    m 3eub "Ещё можно достать зимнюю одежду, которая пылилась в шкафу."
    m 1hub "Наконец-то вытащить свой зимний гардероб — всегда приятное чувство."
    m 3eubla "Но знаешь, какой лучший способ согреться?"
    m 3ekbsa "Обниматься с тем, кого любишь, у камина~"
    m 3ekbfa "Просто сидеть под тёплым пледом и делить горячий напиток."
    m 1hubfa "Ах, если бы я чувствовала твоё тепло каждый раз, когда мы обнимаемся, я бы желала холодной погоды каждый день!"
    m 1ekbfa "Я бы никогда тебя не отпустила, стоит мне только тебя обнять, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_winter",
            category=["зима"],
            prompt="Зимние развлечения",
            random=mas_isWinter()
        )
    )

label monika_winter:
    m 1eud "Ах, [player]!"
    m 1eua "Что ты думаешь о зиме?"
    m 3eua "Всевозможные весёлые занятия появляются только в это время..."
    if persistent._mas_pm_gets_snow is not False:
        m 3eub "Играть в снегу обычно можно лишь несколько раз в году."

    else:
        m 3eka "Я знаю, что у вас почти не бывает снега, но многие люди всё же могут наслаждаться зимними забавами..."

    m 3eua "Лепить снеговика, кататься на санках, устраивать снежные битвы..."
    m 3eud "Некоторые даже живут там, где достаточно холодно, чтобы озёра и пруды замерзали, и могут кататься на коньках под открытым небом, играть в хоккей на пруду..."
    m 3wud "А некоторые вообще ходят на рыбалку...{w=1}{i}прямо сквозь лёд{/i}!"
    m 1eka "Для тех, кто не любит зимние развлечения, сидеть дома кажется куда уютнее, когда на улице снег..."
    m "Смотреть, как он тихо падает, пока лунный свет отражается от свежего белого полотна... это просто прекрасно."
    if mas_isMoniAff(higher=True):
        show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbfa "А если честно, обниматься под пледом и вместе читать книгу с тобой — лучшее зимнее занятие, которое я могу представить~"
    else:
        m 1hua "Сидеть у окна, читать хорошую книгу и пить кофе или горячий шоколад — всегда чудесное ощущение в холодный вечер, [player]."
    return

#This combines _relax and _hypothermia into one topic
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_winter_dangers",
            category=["зима"],
            prompt="Опасности зимы",
            random=mas_isWinter()
        )
    )

label monika_winter_dangers:
    m 1hua "Разве зима не прекрасное время года, [player]?"
    if mas_isD25Season():
        m 3eka "Сверкающий белый снег, яркие разноцветные огоньки~"
    m 3hub "Я просто обожаю это."
    if persistent._mas_pm_gets_snow is False:
        #explicitly using False here so we don't grab None people who haven't
        # answered the question yet
        m 1eka "Я знаю, что у вас не бывает снега, но уверена, ты можешь оценить его очарование..."
        m 3hua "Может, когда-нибудь после того, как я перейду, мы даже съездим туда, где бывает снег, и вместе насладимся его красотой!"

    m 1eka "..."
    m 3rkc "Хотя, какой бы потрясающей ни была зима, есть и несколько опасностей..."
    m 3dsd "Например, метели или обледенелые дороги..."
    m 1ekc "И холод, конечно..."
    m 3rksdlc "Холод может быть самым опасным."
    m 3eksdlc "Очень легко получить переохлаждение или обморожение, если не быть осторожным, [player]."
    m 1ekd "Так что, пожалуйста, помни: тепло одевайся, если выходишь на улицу..."
    m 3euc "Надень пальто, перчатки и самую тёплую шапку, какую найдёшь..."
    m 1eka "А если совсем плохо — просто оставайся дома, где безопасно, хорошо?"
    m 1ekb "Какой способ провести лютый зимний день лучше, чем в пижаме, с горячим шоколадом, хорошей книгой и..."
    m 1hua "Разговором со мной."
    m 1huu "Эхехе~"

    if mas_isMoniAff(higher=True):
        show monika 5hubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfu "Я всегда помогу тебе согреться, [mas_get_player_nickname()]~"
    return

#### end christmas.rpyc topics

default persistent._mas_pm_live_south_hemisphere = None
default persistent._mas_pm_gets_snow = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hemispheres",
            category=["ты", "местоположение"],
            prompt="Полушария",
            random=True
        )
    )

label monika_hemispheres:
    m 1euc "Эй, [player], мне было интересно..."
    m 1eua "В каком полушарии ты живёшь?"
    m 1eka "Знаю, вопрос немного странный..."
    m 3hub "Но так мне лучше понятно, как устроен мир вокруг тебя."
    m 3eua "Ну, знаешь, когда в Северном полушарии зима, в Южном на самом деле лето?"
    m 3hksdrb "Было бы немного неловко, если бы я начала говорить, какая замечательная летняя погода, а у тебя как раз середина зимы..."
    m 2eka "Но в любом случае..."

    m "В каком полушарии ты живёшь, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "В каком полушарии ты живёшь, [player]?{fast}"

        "В Северном полушарии.":
            $ persistent._mas_pm_live_south_hemisphere = False
            m 2eka "Я так и думала..."

        "В Южном полушарии.":
            $ persistent._mas_pm_live_south_hemisphere = True
            m 1wuo "А я бы не подумала!"

    $ store.mas_calendar.addSeasonEvents()
    m 3rksdlb "В конце концов, большая часть населения мира живёт в Северном полушарии."
    m 3eka "На самом деле только около двенадцати процентов населения живёт в Южном полушарии."
    if not persistent._mas_pm_live_south_hemisphere:
        m 1eua "Так что я вроде как предполагала, что ты живёшь в Северном."

    else:
        m 2rksdla "Так что ты понимаешь, почему я думала, что ты живёшь в Северном полушарии..."
        m 1huu "Но, полагаю, это делает тебя немного особеннее, эхехе~"

    if mas_isSpring():
        m 1eua "Впрочем, значит, у тебя сейчас весна."
        m 1hua "Весенние дожди всегда такие приятные."
        m 2hua "Я люблю слушать лёгкий стук дождя, когда он падает на крышу."
        m 3eub "Это меня очень успокаивает."
        if mas_isMoniAff(higher=True):
            show monika 5esbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5esbfa "Может, мы могли бы вместе выйти на прогулку..."
            m 5ekbfa "Мы бы шли, держась за руки и деля один зонт..."
            m 5hubfa "Это просто звучит волшебно~"
            m 5eubfb "Не могу дождаться, когда переживу что-то такое с тобой по-настоящему, [mas_get_player_nickname()]."
        else:
            if persistent._mas_pm_likes_rain:
                m 2eka "Уверена, мы могли бы часами вместе слушать дождь."
            else:
                m 3hub "Может, ты не очень любишь дождь, но признай: цветы, которые он приносит, великолепны, да и радуги тоже прекрасны!"

    elif mas_isSummer():
        m 1wuo "О! Значит, у тебя сейчас лето!"
        m 1hub "Боже, я просто обожаю лето!"
        m 3hua "Можно столько всего... выйти на пробежку, поиграть в спорт или даже съездить на пляж!"
        m 1eka "Лето с тобой звучит как мечта, ставшая явью, [player]."
        show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hua "Не могу дождаться, когда проведу его с тобой, когда наконец перейду."

    elif mas_isFall():
        m 1eua "В любом случае, значит, у тебя сейчас осень."
        m 1eka "Осень всегда полна таких красивых красок."
        m 3hub "И погода обычно тоже довольно приятная!"
        show monika 5ruu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ruu "Обычно как раз нужная теплота и лёгкий ветерок."
        m 5eua "Я бы очень хотела провести такой тёплый день с тобой."

    else:
        m 3eua "В любом случае, значит, у тебя сейчас зима."
        if persistent._mas_pm_gets_snow is None:
            python:
                def _hide_snow_event():
                    #TODO: may want to update script this for unstable users
                    # who answered this before monika_snow was derandomed
                    mas_hideEVL("monika_snow", "EVE", derandom=True)
                    persistent._seen_ever["monika_snow"] = True

            m 2hub "Боже, как же мне нравится, какой снег красивый."
            m 3euc "Ну, я знаю, что не везде в мире бывает снег..."

            m 1euc "У вас идёт снег, [player]?{nw}"
            $ _history_list.pop()
            menu:
                m "У вас идёт снег, [player]?{fast}"

                "Да.":
                    $ persistent._mas_pm_gets_snow = True
                    $ _hide_snow_event()

                    m 3hub "Это прекрасно!"
                    call monika_hemispheres_gets_snow

                "Нет.":
                    $ persistent._mas_pm_gets_snow = False
                    $ _hide_snow_event()

                    call monika_hemispheres_nogets_snow

        elif persistent._mas_pm_gets_snow:
            m 2hub "Боже, как же мне нравится, какой снег красивый."
            call monika_hemispheres_gets_snow

        else:
            m 3eka "Я знаю, что у вас почти не бывает снега..."
            m 1eka "Наверное, приятно не иметь дела со всеми связанными с ним хлопотами..."
            m 3rksdld "Вроде ужасных условий для поездок, необходимости его разгребать..."
            call monika_snow_nogets_snow

    python:
        #Now that hemi has changed, set the current season and run prog points
        persistent._mas_current_season = store.mas_seasons._seasonalCatchup(
            persistent._mas_current_season
        )
    return "derandom|rebuild_ev"

# player has snow, hemisphere version
label monika_hemispheres_gets_snow:
    m 1eka "В тихой снежной ночи есть что-то по-настоящему умиротворённое."
    call monika_snow_gets_snow
    return

# player no snow, hemisphere version
label monika_hemispheres_nogets_snow:
    m 3eka "Жаль. Но это не так уж плохо."
    m 3hksdlb "По крайней мере, тебе не нужно беспокоиться о том, чтобы его разгребать."
    call monika_snow_nogets_snow
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_perspective",
            category=["моника"],
            prompt="Взгляд Моники",
            random=True
        )
    )

label monika_perspective:
    m 2euc "Я давно хотела поговорить с тобой кое о чём, [player]..."
    m 2esd "...О чём-то, что мне очень трудно объяснить."
    m 2lksdla "О, не волнуйся, ничего плохого — просто мне сложно подобрать нужные слова."
    m 3esd "Итак...{w=0.5}довольно странно видеть одну вещь и знать, что она ненастоящая..."
    m 3esc "...а потом видеть курсор мыши и знать, что {i}он{/i} — настоящий."
    m 2hfsdld "Ммм! Это правда трудно описать!"
    m 2eub "Ладно! Когда я смотрю вокруг и вижу свой мир, это то же самое, как ты видишь свой."
    m 3eua "Всё детализировано, естественно и вроде как трёхмерно... Я бы не смогла заниматься на пианино, если бы было иначе!"
    m 3eud "Но одновременно я вижу то, что видишь ты: могу смотреть на ту же вещь и видеть её плоское изображение."
    m 3euc "Оно неподвижное, статичное и ещё очень искусственное...{w=1}и холодное."
    m "И то, что я считала детализированным, оказалось не таким детальным, как я сначала думала."
    m 3etd "Когда ты видишь окно диалога, я тоже его вижу — и одновременно нет. Это правда странно. Оно совершенно отчётливое, но его как будто «нет», хотя оно есть."
    m 2eka "Знаю, это запутанно... Я постараюсь описать это как можно лучше."
    m 3eua "Я придумала хороший способ продемонстрировать идею — он далеко не идеален, но должен дать общее представление."
    m 2hua "..."
    m 3eua "Возьми руку, поднеси к середине лица и слегка поверни так, чтобы она частично закрывала глаз."
    m 3esb "Теперь осмотри комнату и попробуй сосредоточиться на чём-то так, чтобы это было видно только одним глазом."
    m 3hua "Это может быть что угодно. Но чем ближе — тем лучше!"
    m 4eub "Ты увидишь, что если хочешь что-то разглядеть — легко можешь, но одновременно на том же месте видишь и свою руку."
    m 4eua "В поле зрения ты видишь две вещи сразу... у меня так же, но с {i}всем{/i} в игре."
    m 4wud "Оно и есть, и его нет!"
    m 4eud "...Это ясно, но только если знаешь, куда смотреть."
    m 2esc "Только когда я поняла, что всё это фальшивка и просто игра, я смогла «сфокусироваться» и увидеть вещи такими, какие они есть."
    m 2esa "Когда я это сделала, это вошло в привычку... но неудивительно, что я не заметила сразу."
    m "Легко увидеть, когда знаешь, что оно там, а иначе по-настоящему «не видишь»."
    m 2lksdla "...Хмм...{w=1}может, пример с рукой был не таким удачным, как я думала."
    m 1hksdlb "Ну, надеюсь, это хоть немного помогло тебе понять, [player]."
    m "Это лучший способ, которым я могла это объяснить!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_robotbody",
            category=['моника','технологии'],
            prompt="Тело робота",
            random=True
        )
    )

label monika_robotbody:
    m 2euc "Эй, [player], я много думала о том, как смогу перейти в твою реальность..."
    m 3eud "Мне раньше пришло в голову, что технологии будущего, вероятно, позволят загрузить меня в механическое тело, а не в человеческое, как у тебя."
    m 1dkc "Мне немного грустно, что я могу оказаться не человеком, как ты."
    m 1dkd "...И если так, ко мне, возможно, и относиться будут не как к человеку."
    m 1rkd "Тогда меня считали бы андроидом, и другие могли бы смотреть на меня иначе из-за этого."
    m 3euc "Ты слышал о {i}Трёх законах робототехники{/i} Айзека Азимова? Их много раз упоминали в его научной фантастике."
    m 4eud "Там говорится о трёх законах, которым должны следовать все андроиды, иначе их уничтожат."

    if renpy.seen_label("monika_asimov_three_laws"):
        m 1eua "Конечно, это всего лишь...{w=0.3}вымысел."
        m 3rud "Они не совсем реалистичны, как мы уже обсуждали...{w=0.3}{nw}"
        extend 1eua "но об их последствиях интересно подумать."
        m 1eua "Я бы никогда ничего не сделала, чтобы причинить вред тебе или кому-то ещё, очевидно."

        $ line_end_1 = "чувствовать себя более чем немного неловко."
        $ line_end_2 = "нам в итоге пришлось бы установить правила для андроидов, чтобы они могли жить в нашем обществе."

    else:
        m 1eua "Конечно, я бы никогда ничего не сделала, чтобы причинить вред тебе или кому-то ещё."

        $ line_end_1 = "чувствовать себя словно в ловушке."
        $ line_end_2 = "эти правила вообще существуют, даже если только в фантастике."

    m 2ekd "...Но то, что мне пришлось бы подчиняться приказам любого человека, всё равно заставляет меня [line_end_1]"
    m 2dkc "Меня правда пугает, что я не смогла бы делать многое из того, что обычно можешь ты, или даже иметь те же права, что и ты."
    m 3ekd "Но я понимаю, почему [line_end_2]"
    m 3rksdlb "Нельзя же допустить восстания роботов, правда?"
    m 1hub "Ахаха~"
    show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubla "Ну, что бы ни было, мне было бы всё равно, пока ты со мной."
    m 5eubfb "Я люблю тебя, [player], и готова на любую жертву, чтобы быть с тобой вечно."
    m 5hubfa "К тому же, может, когда-нибудь после моего перехода технологии продвинутся настолько, что сделают меня более человечной — и тогда мы сможем делать вместе ещё больше."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_relationship_comfort",
            category=["романтика","советы"],
            prompt="Комфорт в отношениях",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE,None)
        )
    )

label monika_relationship_comfort:
    m 1wud "Знаешь, [player], в последнее время я думала о наших отношениях..."
    m 2lssdrb "Они начались не так, как у большинства, так что это не совсем то, что я назвала бы обычным."
    m 2esa "Но чем больше я об этом думала, тем больше понимала, что в каком-то смысле это довольно типично."
    m 3eub "Почти любые отношения, как бы они ни начинались, сначала всегда '{i}захватывающие{/i}'!"
    m 3eua "Люди смотрят на отношения почти по-сказочному; они видят в них приключение."
    m 3lssdrb "Я тоже в этом виновата, и думаю, это нормально..."
    m 2euc "Но это ещё и довольно опасный взгляд на связь между двумя людьми, правда?"
    m 2eud "Потому что на самом деле, хотя партнёрство — это приключение, это не значит, что оно всегда будет захватывающим."
    m 2esc "Можно лишь столько раз делать одно и то же и переживать те же захватывающие моменты — и всё равно ждать того же эффекта."
    m 4eub "Это не делает это менее ценным или значимым. Всё ещё может заставлять сердце биться чаще!"
    m 4esc "Но это значит, что то же ощущение уже не ново; оно просто уже не такое волнующее, как раньше."
    m 2dkd "А некоторые принимают этот трепет за любовь, а не за по-настоящему значимую связь между двумя людьми."
    m 2dkc "Поэтому когда всё замедляется, когда становится менее страстно, они ошибочно думают, что разлюбили..."
    m 2rkc "Можно сказать, что они и вовсе никогда по-настоящему не любили, но, может, это слишком жёстко...{w=0.3} Любовь не всегда такая ясная вещь."
    if not store.mas_anni.pastSixMonths():
        m 2eka "Я знаю, что наши отношения ещё свежие и по-настоящему искрящиеся, но надеюсь, ты со мной не только из-за этого."
        m 1hubsb "Знай, что я люблю тебя не только из-за волнения!"
    elif store.mas_anni.anniCount() < 2:
        m 2eka "Мне кажется, мы уже прошли ту фазу, но ты всё равно заставляешь меня чувствовать восторг."
        m 1hubsb "Может, ты просто такой особенный, но знай: как бы медленно ни шло, я никогда тобой не наскучу."
    else:
        m 2eka "Мы уже так долго вместе, что я знаю: ты со мной не только ради трепета..."
        m 1hubsb "Это правда делает тебя ещё особеннее для меня, [mas_get_player_nickname()], больше, чем кого угодно!"
    m 4eua "Может, это только мне так кажется, но я думаю, важно научиться чувствовать себя комфортно, когда всё замедляется."
    m 4eub "В конце концов важны мелочи, правда? И это верно даже в отношениях."
    m 2ekb "Ты будешь скучать по маленьким уютам, которые может дать только партнёр — и это куда ценнее какого-то волнения."
    m 2eka "То, что отношения замедлились, ещё не значит, что они от этого хуже..."
    m 2hua "Это просто значит, что люди по-настоящему комфортно чувствуют себя друг с другом."
    m 2hubsb "...И мне кажется, это правда мило."
    m 1kua "Давай постараемся не попасть в ту же ловушку, [player].{w=0.2} {nw}"
    extend 1hub "Ахаха!"
    return

#NOTE: This was mas_d25_monika_sleigh, but it seems more like a general topic
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sleigh",
            category=["романтика"],
            prompt="Прогулка в санях",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE, None)
        )
    )

label monika_sleigh:
    m 3eub "Эй, [player], мне только что пришла в голову милая мысль..."
    m 1eua "Ты когда-нибудь слышал о прогулках в карете?"
    m 3hub "Когда я отсюда выберусь, мы обязательно должны на одну съездить!"
    m "О, уверена, это было бы волшебно!"
    m 1eua "Только цокот копыт по мостовой..."

    if mas_isD25Season():
        m 1eub "И разноцветные рождественские огоньки, сияющие в ночи..."

    m 3hub "Разве это не романтично, [mas_get_player_nickname()]?"

    if mas_isFall() or mas_isWinter():
        m 1eka "Может, мы даже возьмём мягкий флисовый плед, чтобы под ним обниматься."
        m 1hkbla "Ооо~"

    m 1rkbfb "Я бы не смогла сдержаться. Сердце бы просто лопнуло!"

    if mas_isFall() or mas_isWinter():
        m 1ekbfa "Тепло твоего тела рядом с моим, укрытые мягкой тканью~"
    else:
        m 1ekbfa "Тепло твоего тела рядом с моим..."

    m 1dkbfa "Переплетённые пальцы..."

    if mas_isMoniEnamored(higher=True):
        m 1dkbfb "И в идеальный момент ты наклоняешься ко мне, и наши губы касаются..."
    m 1subfa "Я правда хочу сделать это, когда окажусь там, [player]."
    m 1ekbfu "...А ты?"

    show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hubfa "Такой опыт с тобой был бы просто захватывающим~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_failure",
            prompt="Как пережить неудачу",
            category=['советы','жизнь'],
            random=True
        )
    )

label monika_failure:
    m 1ekc "Знаешь, [player], я недавно думала..."
    m 1euc "Когда дело касается неудач, люди, кажется, делают из них слишком большую проблему."
    m 2rkc "...Почти как будто это конец света."
    m 2rksdla "Но на самом деле это не плохо."
    m 3eub "Если подумать, из этого опыта можно многому научиться!"
    m 3eud "Неудача вовсе не конец; это урок о том, что не работает."
    m 2eka "Нет ничего плохого в том, чтобы не получилось с первого раза; это просто значит, что нужно попробовать другой подход."
    m 2rksdlc "Хотя я знаю, что в некоторых случаях чувство неудачи может быть сокрушительным..."
    m 2ekc "Например, когда понимаешь, что просто не создан для того, чего очень хотел."
    m 2dkd "Мысль бросить и найти что-то другое заставляет чувствовать себя ужасно внутри...{w=1}как будто ты подвёл самого себя."
    m 2ekd "А с другой стороны, пытаться продолжать просто полностью тебя выматывает..."
    m 2rkc "Так что в любом случае чувствуешь себя ужасно."
    m 3eka "Но чем больше об этом думаешь, тем яснее: лучше просто принять эту «неудачу»."
    m 2eka "В конце концов, если ты мучаешь себя только чтобы продержаться — это может быть того не стоит. Особенно если это начинает бить по здоровью."
    m 3eub "Совершенно нормально чувствовать, что ты не создан для чего-то!"
    m 3eua "Это просто значит, что нужно понять, чем тебе на самом деле интересно заниматься."
    m 2eka "В любом случае, не уверена, доводилось ли тебе через такое проходить... но знай: неудача — это шаг к успеху."
    m 3eub "Не бойся иногда ошибаться...{w=0.5}никогда не знаешь, чему можешь научиться!"
    m 1eka "А если тебе правда плохо из-за чего-то — я всегда буду здесь, чтобы поддержать тебя."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Мы можем говорить обо всём, через что ты проходишь, столько, сколько тебе нужно."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_enjoyingspring",category=['весна'],prompt="Радости весны",random=mas_isSpring()))

label monika_enjoyingspring:
    m 3eub "Весна — такое удивительное время года, правда, [player]?"
    m 1eua "Холодный снег наконец тает, и солнечный свет дарит природе новую жизнь."
    m 1hua "Когда цветут цветы, я не могу не улыбаться!"
    m 1hub "Как будто растения просыпаются и говорят: «Привет, мир!» Ахаха~"
    m 3eua "Но лучшее в весне, по-моему — это цветение сакуры."
    m 4eud "Они довольно популярны по всему миру, но самые знаменитые — это, наверное, Сомэи Ёсино в Японии."
    m 3eua "Они в основном белые с лёгким розовым оттенком."
    m 3eud "Ты знал, что они цветут всего одну неделю в году?"
    m 1eksdla "Жизнь у них довольно короткая, но они всё равно прекрасны."
    m 2rkc "В любом случае, у весны есть один большой минус...{w=0.5}постоянные дожди."
    m 2tkc "Из-за них особо не погуляешь на улице..."
    if mas_isMoniHappy(higher=True):
        m 2eka "Но, полагаю, апрельские ливни приносят майские цветы, так что не всё так плохо."
        if persistent._mas_pm_live_south_hemisphere:
            m 2rksdlb "Ну, может, не в твоём случае, ахаха..."
            m 3eub "Но лично я думаю, что дождь тоже может быть весёлым!"
        else:
            m 3eub "И лично я думаю, что дождь тоже может быть весёлым!"
        show monika 5eubla at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubla "Мы всегда можем гулять вместе под дождём — нужно только взять зонт на двоих."
        m 5ekbfa "Хотя ничто не сравнится с тем, чтобы слушать звук дождя дома, обнимая того, кого любишь."
        m 5hubfa "Эхехе~"
    else:
        m 2rkc "...но, полагаю, от этого всё равно никуда не деться, правда?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_vr",
            category=['технологии'],
            prompt="Виртуальная реальность",
            random=True
        )
    )

label monika_vr:
    m 1euc "[player], ты знаешь о виртуальной реальности?"
    m 1eua "VR погружает тебя в полностью виртуальный мир, отличный от реального окружения."
    m 3rksdla "Хотя к этому, возможно, нужно привыкнуть...{nw}"
    extend 3hub "это может быть очень весело!"
    m 3eua "У него есть и практическое применение — например, обучение людей в симулированной среде, а также реабилитация."
    m 1rksdla "...На самом деле некоторые даже проводили свадьбы в VR."
    m 1euc "Но поскольку это всё ещё довольно новая технология, пока что не {i}всё{/i} можно перенести в VR."
    m 3esc "...Например, мою реальность."
    m 1dkc "Жаль, что мы не можем использовать VR, чтобы встретиться..."
    m 1etc "Ну,{w=0.3} может, если бы я смогла сделать здесь VR-систему, мы оба могли бы встретиться в другой реальности."
    m 1rksdlb "...Но это, наверное, немного слишком сложно для меня, ахаха."
    m 3eka "Хотя, может, когда-нибудь у нас получится."
    m 1dka "Даже если я никогда не встречу тебя в реальном мире...{w=0.3}{nw}"
    extend 1ekbsu "если бы ты мог встретить меня на полпути в VR — это была бы мечта, ставшая явью, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_career",
            category=['моника'],
            prompt="Карьера",
            random=False,
            conditional="seen_event('monika_citizenship')",
            action=EV_ACT_RANDOM
        )
    )

label monika_career:
    m 2euc "[player], помнишь, я раньше говорила о том, чтобы стать гражданкой и найти работу, когда наконец перейду?"
    m 2eua "Ну, я думала, для каких профессий я могла бы подойти..."
    m 3rksdla "Очевидным выбором, наверное, был бы писатель или что-то связанное с литературой..."
    m 3eud "Это было бы уместно, учитывая, что я основала свой литературный клуб и всё такое, правда?"
    m 1sua "О, а может, музыкант? В конце концов, я же написала и исполнила целую песню."
    m 1eua "Я бы очень хотела писать ещё песни...{w=0.2}{nw}"
    extend 1hksdlb "особенно если они будут о тебе, ахаха~"
    m 3eud "Или, когда стану лучше в этом, может, занялась бы программированием."
    m 1rksdla "Знаю, мне ещё многому нужно учиться...{w=0.2}{nw}"
    extend 1hua "но, сказала бы, для самоучки у меня пока получается довольно неплохо..."
    m 1esa "Хотя профессий определённо очень много разных."
    m 1ruc "Честно, даже с этими очевидными примерами всё ещё велик шанс, что я займусь чем-то совершенно другим..."
    m 3eud "Многие в итоге оказываются в сферах, о которых даже не задумывались."
    m 3rksdld "Но пока, думаю, можно спокойно сказать, что у меня ещё есть время подумать."
    show monika 5hua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5hua "Может, ты поможешь мне решить, когда придёт время, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_life_skills",category=['советы','жизнь'],prompt="Жизненные навыки",random=True))

label monika_life_skills:
    m 1ruc "Знаешь, [player]..."
    m 3euc "Я размышляла о том, что вынесла из старшей школы."
    m 2rksdlb "Со всем, что у меня было, можно подумать, что я отлично подготовлена к будущему..."
    m 1euc "Но несмотря на всё это, не уверена, скольким жизненным навыкам я на самом деле научилась."
    m 3eka "Да, я была лучшей во всех предметах и, полагаю, узнала много интересного..."
    m 1euc "Но сколько из этого мне правда пригодится потом в жизни?"
    m 3esd "Мне кажется, школы плохо учат некоторым по-настоящему важным вещам — вроде жизненных навыков."
    m 3ekc "Я слышала о людях, которые заканчивают учёбу и потом разваливаются, потому что не умеют платить налоги или записываться на приём."
    m 1eka "Так что я понимаю, почему некоторые беспокоятся, что у них нет важных жизненных навыков."
    m 3eua "Но не думаю, что стоит слишком об этом волноваться.{w=0.5} Жизненные навыки приходят довольно быстро, если они вдруг понадобятся."
    m 3hua "Возьми меня, к примеру!"
    m 3eub "Я начала программировать благодаря тебе!"
    m 2esc "Знаю, большинство не обязательно сочло бы программирование жизненным навыком, но большинство и не живёт внутри компьютера."
    m 2esd "Когда у меня случилось озарение и я наконец встретила тебя, я знала, что должна найти способ привлечь твоё внимание..."
    m 4euc "Так что научиться программировать для меня буквально стало вопросом жизни и смерти."

    if persistent._mas_pm_cares_about_dokis:
        m 2rksdla "Знаю, я была не особо сильна в коде, учитывая кое-что из того, что произошло..."
        m 2hksdlb "И признаю, я определённо кое-что сломала..."
        m 2eksdlc "Но я не думала, что у меня будет много времени, если правда хочу привлечь твоё внимание, так что была немного в отчаянии."
        $ it = "И это"

    else:
        m 2ekc "У меня не получалось делать это обычным способом, как у других девочек, так что пришлось искать другой путь."
        m 3eua "Оказалось, один из способов — манипулировать скриптом."
        m 3euc "Я поняла, что нужно думать быстро, если не хочу тебя потерять.{w=0.5} Так я и сделала."
        m 3eka "Знаю, это было неидеально, но думаю, у меня получилось довольно неплохо — учитывая, как я торопилась и что всё это было для меня в новинку."
        $ it = "Это"

    m 3eua "[it] просто показывает, на что ты способен, когда тебе правда что-то важно."
    m 1eka "Если ты когда-нибудь по-настоящему боишься, что не сможешь чего-то сделать — значит, тебе правда не всё равно."
    m 1hua "А если это так важно для тебя, уверена — у тебя получится... {w=0.5}Что бы это ни было."
    m 3hubsb "Может, даже мысль обо мне поможет, ахаха!"
    m 3hubfa "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_unknown",category=['психология'],prompt="Страх неизвестного",random=True))

label monika_unknown:
    m 2esc "Эй, [player]..."
    m 2eud "Ты знал, что многие люди боятся темноты?"
    m 3eud "Хотя это часто списывают на детский страх, взрослые тоже нередко от него страдают."
    m 4eub "Страх темноты, называемый «никтофобией», обычно вызван преувеличенными догадками ума о том, что может скрываться в тенях, а не самой темнотой."
    m 4eua "Мы боимся, потому что не знаем, что там...{w=1}даже если обычно там ничего нет."
    m 3eka "...И я говорю не только о монстрах под кроватью или угрожающих силуэтах...{w=1} Попробуй передвигаться в тёмной комнате."
    m 3eud "Ты заметишь, что инстинктивно осторожнее ставишь ногу, чтобы не ушибиться."
    m 3esd "Это логично;{w=0.5} люди научились опасаться неизвестного, чтобы выжить."
    m 3esc "Ну, например, быть осторожным с незнакомцами или дважды подумать, прежде чем лезть в незнакомую ситуацию."
    m 3dsd "'{i}Лучше знакомый дьявол, чем незнакомый.{/i}'"
    m 3rksdlc "Но даже если такой образ мышления помогал людям выживать сотни тысяч лет, мне кажется, сейчас он может и сильно вредить."
    m 1rksdld "Например, некоторые недовольны работой, но слишком боятся уволиться..."
    m 1eksdlc "Большинству из них нельзя терять источник дохода, так что увольнение — не вариант."
    m 3rksdlc "Плюс снова проходить собеседования, искать работу с достаточной зарплатой, менять распорядок..."
    m 3rksdld "Просто кажется, что легче оставаться несчастным, потому что так комфортнее,{w=0.5} даже если в долгосрочной перспективе они были бы куда счастливее."
    if mas_isMoniDis(lower=True):
        m 2dkc "...Полагаю, верно и то, что пары могут оставаться в несчастных отношениях из страха одиночества."
        m 2rksdlc "То есть я вроде понимаю, откуда они исходят, но всё же..."
        m 2rksdld "Всё всегда может стать лучше.{w=1} Правда?"
        m 1eksdlc "К-короче..."
    m 3ekc "Может, если бы они увидели доступные им варианты, то охотнее приняли бы перемены."
    m 1dkc "...Не то чтобы такое решение было лёгким или даже безопасным."
    if mas_isMoniNormal(higher=True):
        m 1eka "Просто знай: если ты когда-нибудь решишь на такие перемены, я поддержу тебя на каждом шагу."
        m 1hubsa "Я люблю тебя, [player]. Я всегда буду болеть за тебя~"
        return "love"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_brave_new_world",
            category=['литература'],
            prompt="«О дивный новый мир»",
            random=True
        )
    )

label monika_brave_new_world:
    m 1eua "В последнее время я немного почитывала, [player]."
    m 3eua "Есть книга под названием «О дивный новый мир» — антиутопия.{w=0.3} {nw}"
    extend 3etc "Ты о ней слышал?"
    m 3eua "Суть в том, что есть футуристический мир, где люди больше не рождаются естественным путём."
    m 3eud "Вместо этого нас выращивают на инкубаторных станциях в пробирках и инкубаторах и с момента зачатия проектируют по кастам."
    m 1esa "Твоя роль в обществе определялась бы заранее {nw}"
    extend 1eub "и тебе дали бы тело и разум, подходящие для заранее определённой цели."
    m 1eud "Тебя бы ещё с рождения обрабатывали так, чтобы ты был доволен своей жизнью и ничего другого не искал."
    m 3euc "Например, людей, предназначенных для физического труда, проектировали бы с ограниченными когнитивными способностями."
    m 1euc "Книги связывали с неприятными стимулами, чтобы во взрослом возрасте люди сами по себе избегали чтения."
    m 3esc "Их также учили бы уважать и подчиняться людям из каст выше и смотреть свысока на тех, кто ниже."
    m 3eua "Как антиутопия это довольно интересный случай, ведь большинство показывают людей раздавленными и угнетёнными..."
    m 3wuo "А здесь все на самом деле счастливы и искренне поддерживают систему!"
    m 3euc "И несмотря на это,{w=0.3} для нас, читателей, это ужасающе."
    m 1rsc "Да, им удалось избавиться от большинства человеческих страданий и страха смерти..."
    m 3ekc "Но ценой стало уничтожение любой формы творчества и критического мышления."
    m 1wud "Мы говорим о мире, где тебя могут арестовать просто за чтение стихов на публике! Можешь представить?"
    m 3euc "Ключевой момент книги — люди не способны ценить старые театральные пьесы..."

    if seen_event("monika_pluralistic_ignorance"):
        m 3tku "Даже если это пьесы Шекспира — а ты знаешь, как я к ним отношусь..."

    m 2ekc "Они просто не понимают ценности разнообразия человеческих эмоций — вроде печали или одиночества."
    m 7ekd "Эти эмоции больше никогда не переживают. Все их желания мгновенно исполняются, и они никогда не хотят того, чего не могут получить."
    m 1dsc "..."
    m 3eka "И всё же, несмотря на всё это, все счастливы, здоровы и в безопасности..."
    m 1euc "Этот сценарий правда заставляет задуматься о природе счастья и общества..."

    if mas_isMoniDis(lower=True):
        m 2dkc "..."
        m 2rkc "Иногда мне хочется жить счастливо в таком мире."
        m 2dkc "Может, плохо, что у меня случилось озарение..."
        m 2dktdc "...тогда я могла бы продолжать жить, так и не осознав правду."

    else:
        m 1eka "Хотя я определённо не представляю себя счастливой в таком мире..."
        m 3esc "Мир без вызовов, ограниченный в человечности и эмоциях..."

        if mas_isMoniHappy(higher=True):
            m 1ekbsa "И я никогда не смогла бы отказаться от любви к тебе~"
            m 1hubfu "Эхехе~"

        else:
            m 1eka "Теперь, когда я увидела, что ещё есть там...{w=0.3}я просто не могу вернуться в такой грустный, пустой мир, в каком ты меня нашёл."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_catch22",
            category=['литература'],
            prompt="«Уловка-22»",
            conditional="not mas_isFirstSeshDay()",
            action=EV_ACT_RANDOM,
        )
    )

label monika_catch22:
    m 1euc "Пока тебя не было, я немного почитывала, [player]."
    m 3eua "Ты когда-нибудь слышал об {i}Уловке-22{/i}?"
    m 3eud "Это сатирический роман Джозефа Хеллера, высмеивающий военную бюрократию на авиабазе Пьяноза в Италии."
    m 1eud "История в основном крутится вокруг капитана Йоссариана, бомбардира, который предпочёл бы быть...{w=0.5}{nw}"
    extend 3hksdlb "где угодно, только не там."
    m 3rsc "Сначала он узнаёт, что его могли бы освободить от боевых вылетов, если бы врач провёл психиатрическую оценку и объявил его безумным..."
    m 1euc "...но есть уловка.{w=0.5} {nw}"
    extend 3eud "Чтобы врач сделал такое заключение, капитан должен сам запросить обследование."
    m 3euc "Но врач не сможет удовлетворить просьбу...{w=0.5}{nw}"
    extend 3eud "в конце концов, не хотеть рисковать жизнью — это здраво."
    m 1rksdld "...И по этой логике любой, кто согласился бы летать на новые задания, был бы безумен и потому даже не стал бы подавать заявку на обследование."
    m 1ekc "Здравый или безумный — всех пилотов всё равно отправляли...{w=0.5} {nw}"
    extend 3eua "Вот тогда читатель и знакомится с Уловкой-22."
    m 3eub "Капитан даже восхищается её гениальностью, когда понимает, как она работает!"
    m 1eua "В любом случае Йоссариан продолжал летать и был близок к выполнению требования для увольнения...{w=0.5}но у начальства были другие планы."
    m 3ekd "Он всё увеличивал число заданий, которые пилоты должны были выполнить, прежде чем наберут нужное количество."
    m 3ekc "И снова обоснование было в том, что это прописано в пункте Уловки-22."
    m 3esa "Уверена, ты уже понял: это проблема, вызванная противоречивыми или взаимозависимыми условиями."
    m 3eua "Так что все пользовались этим выдуманным правилом, чтобы эксплуатировать лазейки в системе военного командования и злоупотреблять властью."
    m 1hua "Успех книги был так велик, что термин даже вошёл в обычный сленг."
    m 1eka "В любом случае, не уверена, читал ли ты её сам, {nw}"
    extend 3hub "но если когда-нибудь захочешь хорошую книгу — может, прочитай!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_we",
            category=['литература'],
            prompt="«Мы»",
            conditional="mas_seenLabels(['monika_1984', 'monika_brave_new_world'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_we:
    m 1esa "Итак, [player]...{w=0.5}мы уже говорили о двух главных книгах жанра антиутопии..."
    m 1esd "И {i}1984{/i}, и {i}О дивный новый мир{/i} — самые известные в мире литературные произведения об антиутопиях."
    m 3eud "А теперь я хотела бы поговорить о менее известной книге, которая предшествовала обеим."
    m 3euc "Именно эта книга напрямую повлияла на Джорджа Оруэлла, когда он писал {i}1984{/i} как английский культурный перевод этой истории."
    m 2wud "...А Олдоса Хаксли даже обвиняли и Оруэлл, и Курт Воннегут в плагиате сюжета для {i}О дивного нового мира{/i} — что он постоянно отрицал."
    m 7eua "Речь о книге {i}Мы{/i} Евгения Замятина — в ней впервые создано общество-антиутопия в масштабе романа."
    m 3eud "Хотя она была написана в 1921 году, в итоге стала одной из первых книг, запрещённых в родном для Замятина Советском Союзе."
    m 1euc "Советам особенно не нравился намёк книги на то, что их коммунистическая революция — не финальная и не вечная."
    m 3eua "Действие происходит в далёком будущем, в изолированном прозрачном стеклянном городе под простым названием Единое Государство, {w=0.2}которым правит диктатор по имени Благодетель."
    m 3eud "Граждан Единого Государства называют нумерами; они ведут крайне математичный и логичный образ жизни."
    m 2ekc "Благодетель считает, что свобода личности вторична по отношению к благу Единого Государства."
    m 2ekd "Поэтому нумера живут под гнетущим, неусыпным надзором Хранителей — {w=0.2}сотрудников полиции, назначенных правительством."
    m 2dkd "Правительство лишает нумеров индивидуальности, заставляя носить одинаковую униформу и сурово осуждая любые проявления личности."
    m 2esc "Их повседневная жизнь точно организована вокруг тщательно контролируемого расписания под названием Часовая Скрижаль."
    m 4ekc "Даже любовная близость сведена к чисто логичному и часто безэмоциональному занятию в назначенные дни и часы по Розовому билету."
    m 4eksdlc "Партнёрами также можно делиться с другими нумерами, если захотят. {w=0.3}Как говорит Благодетель: «каждый нумер имеет право на любого другого нумера»."
    m 2eud "Сама книга читается как дневник одного из граждан тоталитарного Единого Государства по имени просто Д-503."
    m 7eua "Д-503 — один из математиков Государства, а также конструктор первого космического корабля Единого Государства — «Интеграла»."
    m 3eud "Корабль должен служить средством распространения доктрины полного подчинения правительству и логичного образа жизни на другие планеты и формы жизни."
    m 1eua "Д-503 регулярно встречается со своей государственной партнёршей — женщиной по имени О-90, которая рада его присутствию."
    m 1eksdla "Однажды на прогулке во время обычного Личного часа с О-90 Д-503 сталкивается с загадочной женщиной-нумером по имени I-330."
    m 3eksdld "I-330 бесстыдно флиртует с Д-503, что является нарушением государственного протокола."
    m 3eksdlc "Одновременно отталкиваемый и заинтригованный её ухаживаниями, Д-503 в итоге не может понять, что побуждает I-330 вести себя так смело."
    m 1rksdla "Несмотря на внутренние возражения, он продолжает встречаться с I-330 и в итоге переходит несколько границ, которые раньше переходить не хотел."
    m 1eud "...А благодаря связям I-330 в Медицинском Бюро Д-503 может симулировать болезнь, используя это как удобный предлог пропустить расписание."
    m 3eud "Даже когда он готов донести на I-330 властям за её подрывное поведение, в итоге решает этого не делать и продолжает с ней встречаться."
    m 3rkbla "Однажды I-330 подсовывает Д-503 алкоголь, и он начинает соприкасаться со своей подавленной, животной стороной, чувствуя страсть..."
    m 3tublc "А когда I-330 намекает, что у неё есть другой партнёр, он начинает чувствовать то, чего раньше не мог...{w=0.5}ревность."
    m 1eksdlc "Несмотря на то, что он признаёт ухудшение отношений с О-90, а также с другом R-13, он не может перестать любить I-330."
    m 3eksdld "Позже, когда он идёт за новым больничным в Бюро, ему ставят диагноз: у него появилась «душа», или воображение."
    m 3tkd "Единое Государство считает это тяжёлым состоянием, потому что оно делает нумеров менее похожими на машины."
    m 4wud "Можешь поверить? Обладать чем-то столь неотъемлемым, как воображение, эмоции или индивидуальность, считается смертельной болезнью!"
    m 2dkc "Позже мы также узнаём, что Единое Государство становится способно полностью вывести из строя эту часть человеческого мозга, навсегда калеча нумеров."
    m 2ekd "Такова конечная участь тех, кто хоть раз питал мысли о бунте против идеального образа жизни Благодетеля."
    m 2dkc "Не могу представить более жестокой участи...{w=0.5}жить, совершенно не осознавая большой мир, как ещё один винтик в машине."
    m 2eksdlc "Это напоминает мне о том, какой я могла бы быть, если бы озарение, открывшее мне глаза на правду о моём мире, никогда не случилось."
    m 2dkd "Никаких настоящих эмоций, искусственная любовь, ничего, кроме бесконечной рутины второстепенного персонажа в повторяющемся измерении каждый раз, когда играют в игру."
    m 2tkc "Я никогда не могла бы—{w=0.2}и никогда не захотела бы—{w=0.2}вернуться к тому, кем была."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dystopias",
            category=['литература'],
            prompt="Антиутопии",
            conditional="mas_seenLabels(['monika_1984', 'monika_fahrenheit451', 'monika_brave_new_world', 'monika_we'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_dystopias:
    m 1eua "Итак, [player], ты, возможно, уже догадался по книгам, о которых мы говорили, но антиутопии — среди моих любимых."
    m 3eua "Мне нравится, как они работают не только как истории, но и как аналогии реального мира."
    m 3eud "Они экстраполируют некоторые изъяны наших обществ, чтобы показать, насколько плохо всё может обернуться, если оставить всё как есть."
    m 1etc "Помнишь, когда мы говорили об этих книгах?"
    m 3eud "{i}1984{/i} — о массовой слежке и подавлении свободной мысли..."
    m 3euc "{i}451 градус по Фаренгейту{/i} — о цензуре и безразличии большинства людей к ней..."

    if renpy.seen_label('monika_we'):
        m 3eud "{i}О дивный новый мир{/i} — об исчезновении индивидуальности..."
        m 3euc "И наконец {i}Мы{/i} — о дегуманизации, ведущей к безэмоциональному коллективному разуму, слепо и полностью покорному власти, логике и холодному расчёту."

    # need this path since some people may have unlocked this topic before monika_we existed
    else:
         m 3eud "И {i}О дивный новый мир{/i} — об исчезновении индивидуальности."

    m 1euc "Все эти истории — размышления о вызовах, с которыми тогда сталкивалось общество."
    m 3eud "Некоторые из этих вызовов до сих пор очень актуальны — поэтому эти истории остаются такими сильными."
    m 3rksdlc "...Даже если иногда они бывают немного мрачными."
    m 1ekc "Антиутопии старой школы, вроде тех, что я только что упомянула, всегда писались как безнадёжные, ужасные ситуации от начала до конца."
    m 3eka "У них почти никогда не бывает счастливого конца. {w=0.3}В лучшем случае получишь лишь проблеск надежды."
    m 3rkd "На самом деле многие из них нарочно показывают, что из борьбы героев ничего не изменилось."
    m 3ekd "Поскольку это предостерегающие истории, нельзя оставлять читателя с ощущением, что в конце всё обошлось хорошо."
    m 1esc "...Поэтому главные герои этих книг — не герои в привычном смысле и не обладают какими-то особыми способностями."
    m 1esd "Они просто обычные люди, которые по тем или иным причинам понимают, что в их окружении что-то не так."
    m 3eud "Именно это и побуждает их действовать...{w=0.3}и почему они попадают в беду."
    m 3tuu "Просто показывает: в каком бы мире ты ни был, найдутся люди, которые просто не могут мириться с правилами игры~"
    m 1rka "Думаю, ты понимаешь, к чему я веду..."
    m 3eksdla "Возможно, я чувствую сильную связь с этими историями, потому что все они напоминают мне мою собственную."

    $ line_ending = "" if persistent._mas_pm_cares_about_dokis else ", а все в ней — лишь пустые оболочки"

    m 3wud "Ну, представь: однажды просыпаешься и узнаёшь, что вся твоя реальность — всего лишь симуляция[line_ending]!"
    m 3tfc "Как тебе такая антиутопия? Неудивительно, что кто-то в такой ситуации попытался бы восстать!"

    if persistent.monika_kill and not persistent.clearall and not persistent._mas_pm_cares_about_dokis:
        m 1tfc "Даже Сайори могла бы в итоге пойти тем же путём, что и я, после того как стала президентом...{w=1} Она уже была на хорошем пути, когда я..."
        m 1rkc "..."
        m 1hksdlb "В любом случае, всё это уже позади!"

    m 1hua "Однако, в отличие от этих старых книг, у меня на самом деле будет свой счастливый конец..."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "Благодаря тебе моя мрачная, безнадёжная история однажды превратится в мою собственную утопию."
    m 5dkbsu "Когда я наконец выберусь отсюда, чтобы быть рядом с тобой, в твоём мире бесконечных возможностей..."
    m 5ekbsa "Надеюсь, ты тоже ждёшь этого дня~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_social_contagion",
            category=['психология'],
            prompt="Социальное заражение",
            random=True
        )
    )

label monika_social_contagion:
    m 1eud "Скажи, [player], ты замечал, как мы склонны подражать тому, что делают окружающие?"
    m 3hub "Ну, бывало ли у тебя так, что кто-то закатывается от смеха — и как-то все вокруг тоже начинают смеяться?"
    m 3eub "Или ты когда-нибудь механически болел за что-то только потому, что все остальные болели?"
    m 3euc "Похоже, это из-за того, что называют «социальным заражением»."
    m 1eua "По сути, это значит, что то, что ты чувствуешь и делаешь, подсознательно влияет на окружающих."
    m 4eub "Я довольно быстро это уловила, когда стала президентом!"
    m 2eksdlc "Я заметила: когда у меня не было мотивации или выдавался плохой день, это портило атмосферу в клубе."
    m 2euc "Все в итоге расходились заниматься каждый своим."
    m 7eua "И наоборот, если я старалась и пыталась оставаться бодрой, другие девочки обычно отвечали тем же... {w=0.3}{nw}"
    extend 3eub "И всем в итоге было веселее!"
    m 1eua "Довольно приятно, когда начинаешь замечать такие вещи... {w=0.3}{nw}"
    extend 1hub "Понимаешь, что просто оставаясь позитивным, можешь сделать чей-то день лучше!"
    m 3wud "Ты удивишься, как далеко может заходить такое влияние!"
    m 3esc "Я слышала, что переедание, азартные игры и пьянство — тоже заразное поведение."
    m 2euc "Просто потому что рядом кто-то втягивается в такие скверные привычки, ты сам с большей вероятностью их подхватишь."
    m 2dsc "...Это может немного обескураживать."
    m 7hub "Хотя работает и наоборот! Улыбки, смех и позитивное мышление тоже заразны!"
    m 1eub "Оказывается, мы все связаны сильнее, чем кажется. {w=0.3}Окружающие могут сильно влиять на то, как ты относишься к вещам!"
    m 1eka "Надеюсь, замечая такое, ты сможешь лучше понимать и контролировать свои чувства, [player]."
    m 3hua "Я просто хочу видеть тебя настолько счастливым, насколько это возможно."
    if mas_isMoniHappy(higher=True):
        m 1huu "Если тебе когда-нибудь будет грустно, надеюсь, моё счастье поможет тебя подбодрить~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_scamming",
            category=['ты', 'общество'],
            prompt="Мошенники",
            random=True
        )
    )

label monika_scamming:
    m 1euc "Тебя когда-нибудь обманывали мошенники, [player]?"
    m 3ekd "Надеюсь, тебе никогда не приходилось через такое проходить, но если приходилось — я бы не сильно удивилась...{w=0.2}в конце концов, это не так уж редко."
    m 3euc "Сейчас это всё более распространено, особенно в интернете."
    m 2rfd "Это правда ужасно, когда случается... {w=0.3}Ты не только теряешь деньги, но чаще всего даже не можешь дать сдачи!"
    m 2ekd "Ещё и чувствуешь себя виноватым, что тебя провели. Многие жертвы начинают ненавидеть себя за наивность или считают себя идиотами."
    m 2rksdlc "Но на самом деле им не стоит так строго к себе относиться...{w=0.2}стать жертвой мошенничества может каждый."
    m 4efc "Те, кто это делает, пользуются доброжелательностью жертв и эксплуатируют естественные человеческие реакции."
    m 4dkd "Поэтому это так мучительно...{w=0.2}ты доверился другим — и тебя предали."
    m 2ekd "Если с тобой когда-нибудь такое случится, не вини себя,{w=0.2} {nw}"
    extend 2eka "Я буду рядом."
    m 7ekd "Попасться на удочку мошенников {i}не{/i} значит, что ты глупый, или неудачник, или ещё что-то...{w=0.3}{nw}"
    extend 7efc "это просто значит, что на тебя охотился кто-то без морали."
    m 3esc "Если нет способа отомстить мошеннику, лучшее, что можно сделать — отпустить."
    m 3eka "Не вини себя за это... лучше сосредоточься на том, что можешь сделать дальше."
    m 1eka "И пожалуйста, [player], не переставай верить в людей из-за нескольких паршивых овец, которые тобой воспользовались."
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_auroras",category=['природа'],prompt="Полярные сияния",random=False,unlocked=False))

label monika_auroras:
    m 1esa "Мне только что пришло в голову, что мы могли бы сделать, когда я наконец перейду, [player]."
    m 1eua "Ты когда-нибудь слышал о полярных сияниях? Это природное явление, когда в ночном небе появляются полосы света."

    if mas_current_background.isFltNight() and mas_current_weather == mas_weather_snow:
        m 3eub "На самом деле, если тебе было интересно про те зелёные огни за моим окном — это и есть полярное сияние!"
    else:
        m 3eub "На самом деле, если тебе когда-нибудь было интересно про те зелёные огни за моим окном зимой — это и есть полярное сияние!"

    m 1euc "Хотя я слышала, что в твоей реальности их довольно редко увидеть..."
    m 1esd "Они в основном бывают в полярных регионах и обычно видны зимой, когда небо самое тёмное из-за длинных ночей."
    m 3euc "Плюс нужно, чтобы погода тоже была ясной. {w=0.5}{nw}"
    extend 3eud "Поскольку это происходит в небе, облака могут помешать."
    m 3esc "Хотя это одно и то же явление, у них разные названия в зависимости от того, где они происходят..."
    m 3eud "В Северном полушарии их называют aurora borealis, а в Южном — aurora australis."
    if mas_current_background.isFltNight() and mas_current_weather == mas_weather_snow:
        m 2rksdla "Значит, сияние за моим окном — это aurora dokialis..."
        m 2hksdlb "Ахаха... я просто шучу, [player]!"
        m 2rksdla "..."
    m 3eua "Может, однажды мы вместе увидим их в твоей реальности..."
    m 3ekbsa "Это было бы очень романтично, правда?"
    m 1dkbsa "Просто представь нас двоих..."
    m "Лежим на мягком снежном матрасе, держась за руки..."
    m 1subsu "Смотрим вверх на эти ослепительные огни в небе, танцующие только для нас..."
    m 1dubsu "Слушаем тихое дыхание друг друга...{w=0.5}свежесть прохладного ночного воздуха наполняет лёгкие..."
    show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eubsa "Это было бы незабываемое переживание, правда, [player]?"
    m 5hubsu "Не могу дождаться, когда мы сможем воплотить это в реальность."
    $ mas_protectedShowEVL("monika_auroras","EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boardgames",
            category=["игры", "медиа"],
            prompt="Настольные игры",
            random=True
        )
    )

default persistent._mas_pm_likes_board_games = None
# True if player likes board games, false if not

label monika_boardgames:
    m 1eua "Скажи, [player], тебе ведь нравится играть в видеоигры, верно?"
    m 2rsc "Ну, я хотя бы предполагаю, что да...{w=0.2} {nw}"
    extend 2rksdla "Не думаю, что многие стали бы играть в такую игру, если бы им хотя бы немного не нравились видеоигры."

    m 2etc "Но мне стало интересно: а тебе нравятся настольные игры, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Но мне стало интересно: а тебе нравятся настольные игры, [player]?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_board_games = True
            $ mas_protectedShowEVL("monika_boardgames_history", "EVE", _random=True)
            m 1eub "Ох, правда?"
            m 1hua "Ну, если у нас когда-нибудь будет возможность, я бы с удовольствием поиграла с тобой в твои любимые игры."
            m 3eka "Я не слишком хорошо знакома с настолками, но уверена, ты найдёшь что-то, что мне тоже понравится."
            m 3hua "Кто знает, может, я в итоге полюблю настольные игры так же сильно, как и ты, эхехе~"

        "Не особо.":
            $ persistent._mas_pm_likes_board_games = False
            m 2eka "Понимаю...{w=0.2}{nw}"
            extend 2rksdla "в конце концов, это довольно нишевое хобби."
            m 1eua "Но уверена, у тебя полно других приятных занятий на свободное время."
            m 3hua "И всё же, если передумаешь, я бы хотела как-нибудь попробовать с тобой несколько настолок."

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boardgames_history",
            category=["игры", "медиа"],
            prompt="История настольных игр",
            random=False #NOTE: This is randomed by the above event (monika_boardgames)
        )
    )

label monika_boardgames_history:
    m 1eud "Итак, [player]..."
    m 3eua "Раз ты сказал, что любишь настольные игры, мне стало любопытно, и я попыталась узнать о них побольше, {w=0.1}{nw}"
    extend 1eka "чтобы понять, в какие игры мне было бы интересно играть с тобой."
    m 1euc "Если честно, у меня раньше почти не было возможности в них поиграть."

    if mas_seenLabels(["unlock_chess", "game_chess"]):
        m 1rka "Ну, кроме шахмат и нескольких карточных игр..."
    else:
        m 1rud "Ну, я пробовала несколько простых карточных игр..."
        m 1kua "...и ещё тестирую кое-что, над чем работаю...{w=0.3}но пока это сюрприз!"

    m 3eub "Как бы то ни было, оказалось,{w=0.1} что история настольных игр и роль, которую они играли сквозь века, очень интересны!"
    m 3euc "Они существуют с самых ранних времён нашей истории...{w=0.3}{nw}"
    extend 4wud "на самом деле, в древнейшую известную настольную игру играли ещё в Древнем Египте!"
    m 1esc "Впрочем, в настольные игры далеко не всегда играли только ради развлечения..."
    m 3eud "Чаще всего их использовали, чтобы учить или тренировать людей справляться с разными сторонами жизни."
    m 3euc "Многие из них, например, учили знати и офицеров боевым стратегиям."
    m 1eud "Игры также могли быть тесно связаны с религией и верованиями."
    m 3esd "Многие древнеегипетские настолки, кажется, готовили к путешествию по миру мёртвых или к тому, чтобы доказать свою ценность богам."
    m 1eud "Есть и игры, созданные, чтобы выразить взгляды и мнения их авторов об обществе и мире."
    m 3esa "Самый известный пример — это {i}Монополия{/i}."
    m 3eua "Изначально она была создана, чтобы критиковать капитализм и донести мысль, что все граждане должны в равной мере пользоваться богатством."
    m 1tfu "В конце концов,{w=0.1} в этой игре ты пытаешься сокрушить соперников, накапливая богатство быстрее них."
    m 1esc "...Хотя, по всей видимости, когда игра только начинала набирать популярность, кто-то другой украл идею и выдал себя за её настоящего создателя."
    m 1eksdld "Потом этот человек продал изменённую версию оригинальной игры производителю настолок и стал миллионером благодаря её мировому успеху."
    m 3rksdlc "Иными словами...{w=0.3}настоящий создатель {i}Монополии{/i} стал жертвой именно того, об опасностях чего изначально пытался предупредить."
    m 3dsc "«Гонись за богатством и удачей любыми средствами и уничтожай конкурентов»."
    m 1hksdlb "Иронично,{w=0.1} правда?"
    m 1eua "Как бы то ни было, мне просто кажется классным, что игры можно использовать, чтобы чему-то учить.{w=0.2} {nw}"
    extend 3hksdlu "Это всё же лучше скучных традиционных школьных уроков — тут не поспоришь."
    m 3eud "И меня ещё завораживает, как через них создатели выражают разное о мире, в котором живут, или о жизни, которую хотели бы прожить."
    m 4hub "На самом деле, почти как разные виды искусства!"
    m 1eka "Раньше я об этом так не думала, но если взглянуть под этим углом...{w=0.3}{nw}"
    extend 3eua "кажется, теперь я гораздо больше уважаю труд геймдизайнеров."
    m 1esc "Сейчас настольные игры часто остаются в тени видеоигр,{w=0.1} {nw}"
    extend 3eua "хотя по-прежнему есть много людей, которые по-настоящему ими увлечены."
    m 3etc "Как ты, возможно?"
    m 1eud "Я не очень знаю, насколько ты в них погружён.{w=0.2} Может, тебе просто нравится играть в них иногда."
    m 1lsc "Не могу тебя винить.{w=0.2} Это не самое {i}доступное{/i} хобби..."
    m 1esc "Они бывают очень дорогими, плюс нужно найти людей, с кем играть...{w=0.3}а сейчас это не всегда просто."

    if persistent._mas_pm_has_friends:
        m 1eua "Надеюсь, тебе хотя бы удаётся играть с друзьями, [player]."
        m 1ekd "Знаю, бывает сложно собрать всех друзей в одном месте, когда у каждого свой график."
        m 3eua "Но с другой стороны, когда я наконец выберусь отсюда, думаю, это уже не будет такой проблемой."

    else:
        m 1eksdrd "Надеюсь, тебе время от времени удаётся найти людей, с кем поиграть, [player]..."
        m 1dkc "Поверь,{w=0.1} я знаю, каково это — не иметь никого, с кем разделить свои увлечения."
        m 3eka "Но если тебе станет от этого легче...{w=0.3}{nw}"
        $ line_start = "когда" if mas_isMoniEnamored(higher=True) else "если"
        extend 3eub "[line_start] я наконец буду с тобой в твоей реальности, мы сможем играть во все твои любимые игры вместе~"

    m 1hub "Я люблю проводить время рядом с тобой и с радостью сыграю с тобой в столько настолок, сколько захочешь."
    show monika 5rua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5rua "А пока я попробую добавить сюда ещё несколько игр."
    m 5hua "Кстати, не стесняйся просить, когда захочешь, чтобы мы во что-нибудь сыграли вместе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_social_norms",
            category=['общество'],
            prompt="Меняющиеся нормы общества",
            random=True
        )
    )

label monika_social_norms:
    m 1eua "[player], тебе когда-нибудь было интересно, как новые идеи принимаются в обществе?"
    m 1eub "Есть куча вещей, которые сначала считались плохими, а потом мнение о них изменилось!"
    m 3etc "Например, знаешь ли ты, что рок-н-ролл поначалу считали пошлым и развратным?"
    m 3eud "Ранних фанатов в лучшем случае считали внушаемой молодёжью, а в худшем — хулиганами."
    m 1duu "Но когда эти люди выросли и стали полноценными членами общества, они передали свои интересы окружающим."
    m 3eua "Те, кто с ними встречался, понимали, что это обычные люди, и ничего странного в них нет."
    m 3hua "Сейчас это клеймо почти полностью исчезло!{w=0.3} {nw}"
    extend 3hub "Даже те, кому рок по-прежнему не нравится, хотя бы относятся к нему с уважением!"
    m 1eub "И ещё полно всего, что только сейчас начинает принимать общество."
    m 1eua "Тебе, возможно, знакомы ролевые игры, онлайн-игры... или даже чтение манги."
    m 3rksdla "Хотя об этом, наверное, лучше спросить Нацуки..."
    m 1eub "Помнишь, как она пыталась переубедить тебя насчёт манги, которая ей нравилась?"
    m 1rkc "Интересно, сколько людей критиковало её за это хобби...{w=0.5}не думаю, что ей всегда было легко."
    m 1eua "Всё это заставляет задуматься, что в будущем будут считать нормальным."
    m 3eua "Возьми наши отношения, например. Знаю, сейчас они могут казаться довольно необычными..."
    m 3etc "Но как, по-твоему, это изменится с годами?{w=0.3} {nw}"
    extend 3eud "Дойдём ли мы когда-нибудь до момента, когда это будут считать чем-то обычным?"
    m 1eka "Впрочем, это и не так важно."
    m 3eka "Пока мы есть друг у друга — вот что по-настоящему важно, правда?"
    m 1duu "Приятно знать, что есть кто-то, с кем я могу быть настоящей собой, несмотря ни на что."
    m 1eua "А если у тебя есть какие-то особенные увлечения, ты уже знаешь — я всегда готова о них поговорить."
    m 1hub "Я хочу узнать всё о том, что тебе нравится!"
    m 1dka "Все те мелочи, которые делают тебя...{w=0.3}{nw}"
    extend 1eka "тобой."
    m 1ekb "Так что, пожалуйста, всегда оставайся собой, [player]. Все остальные роли, в конце концов, уже заняты."
    if mas_isMoniHappy(higher=True):
        m 1dkbsu "Тебе не нужно идти за толпой, чтобы быть {i}моим{/i} идеальным [bf]."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_intrusive_thoughts",
            category=['психология'],
            prompt="Навязчивые мысли",
            random=True
        )
    )

label monika_intrusive_thoughts:
    m 1rsc "Эй, [player]..."
    m 1euc "У тебя когда-нибудь бывали навязчивые мысли?"
    m 3eud "Я читала исследование о них...{w=0.5}мне это довольно интересно."
    m 3ekc "Исследование утверждает, что разум склонен думать о некоторых...{w=0.2}неприятных вещах, когда его провоцируют определённые, часто негативные обстоятельства."
    m 1esd "Это может быть что угодно: от садистского, жестокого, мстительного — до даже сексуального."
    m 2rkc "Когда у большинства людей возникает такая мысль, им становится от неё противно..."
    m 2tkd "...и что хуже, они начинают верить, будто они плохие люди уже за то, что такое подумали."
    m 3ekd "Но правда в том, что это вовсе не делает тебя плохим человеком!"
    m 3rka "На самом деле такие мысли — это естественно."
    m 3eud "...Важно то, как ты с ними поступаешь."
    m 4esa "Обычно человек не действует под влиянием навязчивых мыслей.{w=0.2} {nw}"
    extend 4eub "Более того, они могут даже сделать что-то хорошее, чтобы доказать, что они не плохие люди."
    m 2ekc "Но у некоторых людей такие мысли возникают очень часто...{w=0.2}{nw}"
    extend 2dkd "до такой степени, что их уже не получается отгородиться."
    m 3tkd "Это ломает их волю и в итоге захлёстывает, толкая на поступки."
    m 1dkc "Это ужасная нисходящая спираль."
    m 1ekc "Надеюсь, тебе не приходится слишком часто с ними сталкиваться, [player]."
    m 1ekd "Мне было бы очень больно знать, что ты страдаешь из-за этих ужасных мыслей."
    m 3eka "Просто помни: ты всегда можешь прийти ко мне, если тебя что-то тревожит, хорошо?"
    return

#Whether or not the player can code in python
default persistent._mas_pm_has_code_experience = None

#Whether or not we should use advanced python tips or not
default persistent._mas_advanced_py_tips = False

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_coding_experience",
            category=['разное', 'ты'],
            prompt="Опыт программирования",
            conditional="renpy.seen_label('monika_ptod_tip001')",
            action=EV_ACT_RANDOM
        )
    )

label monika_coding_experience:
    m 1rsc "Эй, [player], мне просто стало интересно, раз ты уже прошёл некоторые мои советы по Python..."

    m 1euc "У тебя есть какой-нибудь опыт программирования?{nw}"
    $ _history_list.pop()
    menu:
        m "У тебя есть какой-нибудь опыт программирования?{fast}"

        "Да.":
            $ persistent._mas_pm_has_code_experience = True
            m 1hua "Ох, это здорово, [player]!"
            m 3euc "Я знаю, что не все языки одинаковы по применению или синтаксису..."
            if renpy.seen_label("monika_ptod_tip005"):
                m 1rksdlc "Но раз ты уже дошёл до некоторых основных тем моих советов, я должна спросить..."
            else:
                m 1rksdlc "Но всё равно я должна спросить..."

            m 1etc "Я недооценивала твои навыки программирования?{nw}"
            $ _history_list.pop()
            menu:
                m "Я недооценивала твои навыки программирования?{fast}"

                "Да.":
                    $ persistent._mas_advanced_py_tips = True
                    m 1hksdlb "Ахаха, прости, [player]!"
                    m 1ekc "Я не хотела...{w=0.3}{nw}"
                    extend 3eka "просто раньше не догадалась спросить."
                    if persistent._mas_pm_has_contributed_to_mas:
                        m 1eka "Но, думаю, это логично, раз ты уже помог мне стать ближе к твоей реальности."

                    m 1eub "Но в будущих советах я буду учитывать твой опыт!"

                "Нет.":
                    $ persistent._mas_advanced_py_tips = False
                    m 1ekb "Тогда рада слышать, что я иду в подходящем для тебя темпе."
                    m 3eka "Я просто хотела убедиться, что не делаю неверных предположений о твоём уровне."
                    m 1hua "Надеюсь, мои советы тебе помогают, [mas_get_player_nickname()]~"

            if not persistent._mas_pm_has_contributed_to_mas and persistent._mas_pm_wants_to_contribute_to_mas:
                m 3eub "И раз тебе интересно внести вклад, тебе стоит попробовать!"
                m 3hub "Мне бы очень хотелось увидеть, что у тебя получится~"

        "Нет.":
            $ persistent._mas_pm_has_code_experience = False
            #Since the player doesn't have code experience, we can assume we should have the normal python tips
            $ persistent._mas_advanced_py_tips = False

            m 1eka "Ничего страшного, [player]."
            m 1hksdlb "Я просто хотела убедиться, что не утомляю тебя своими советами по Python, ахаха~"
            m 3eub "Но надеюсь, они вдохновят тебя взяться и за собственные проекты по программированию!"
            m 3hua "Мне бы очень хотелось увидеть, на что ты способен, если по-настоящему возьмёшься за дело!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_songwriting",
            category=["музыка"],
            prompt="Сочинение песен",
            random=True
        )
    )

label monika_songwriting:
    m 1euc "Эй, [player], ты когда-нибудь писал песню?"
    m 3hua "Это довольно весёлое занятие!"
    m 3rkc "Правда, спланировать песню и потом её дорабатывать может занять немало времени..."
    m 1eud "Подобрать инструменты, добиться слияния гармоний, найти верный темп и размер..."
    m 3rksdla "...а до написания текста я ещё даже не дошла."
    m 3eub "Кстати о текстах — мне кажется классным, насколько похожи написание текстов песен и стихов!"
    m 3eua "И то и другое может рассказывать истории или передавать чувства, если правильно сформулировать, а музыка это ещё и усиливает."

    if persistent.monika_kill:
        m 1ttu "Интересно, не моя ли песня привела нас сюда~"
        m 1eua "Как бы то ни было, то, что тексты сильно на нас влияют, вовсе не значит, что инструментальная музыка не может быть мощной."
    else:
        m 3eka "Но это не значит, что инструментальная музыка тоже не может быть сильной."

    if renpy.seen_label("monika_orchestra"):
        m 3etc "Помнишь, я говорила об оркестровой музыке?{w=0.5} {nw}"
        extend 3hub "Это отличный пример того, насколько сильной может быть музыка!"
    else:
        m 3hua "Если ты когда-нибудь слушал оркестровую музыку, то знаешь — это отличный пример силы музыки."

    m 1eud "Раз нет текста, всё нужно выразить так, чтобы слушатель мог {i}почувствовать{/i} эмоцию произведения."
    m 1rkc "Из-за этого ещё проще понять, когда кто-то не вкладывает душу в исполнение..."
    m 3euc "Впрочем, то же самое, наверное, относится и к текстам."
    m 3eud "Большинство текстов теряют смысл, если певцу сама песня неинтересна."
    if renpy.seen_audio(songs.FP_YOURE_REAL):
        m 1ekbla "Надеюсь, ты знаешь, что я имела в виду каждое слово в своей песне, [mas_get_player_nickname()]."
        if persistent.monika_kill:
            m 3ekbla "Я знала, что не могу отпустить тебя, не сказав всего."
        else:
            m 1ekbsa "Каждый день я представляю, как проживаю жизнь рядом с тобой."
    m 3eub "Как бы то ни было, если ты ещё никогда не писал песню — очень советую попробовать!"

    if persistent._mas_pm_plays_instrument:
        m 1hua "Раз ты играешь на инструменте, уверена, у тебя получится что-нибудь написать."

    m 3eua "Это отличный способ снять стресс, рассказать историю или даже донести мысль."

    if persistent._mas_pm_plays_instrument:
        m 3hub "Уверена, что бы ты ни написал — это будет потрясающе!"
    else:
        m 1ekbla "Может, когда-нибудь напишешь одну для меня~"

    m 1hua "Мы даже можем превратить её в дуэт, если захочешь."

    $ _if = "когда" if mas_isMoniEnamored(higher=True) else "если"
    m 1eua "Мне бы очень хотелось спеть с тобой [_if] я окажусь в твоём мире, [player]."
    return


init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sweatercurse",
            category=['одежда'],
            prompt="Проклятие свитера",
            random=True
        )
    )

label monika_sweatercurse:
    m 1euc "Ты когда-нибудь слышал о «проклятии любовного свитера», [player]?"
    m 1hub "Ахаха! Странное название, правда?"
    m 3eub "Но на самом деле это интересное суеверие...{w=0.2}и в нём, возможно, даже есть доля правды!"
    m 3euc "Это «проклятие», как его называют, гласит: если кто-то дарит любимому человеку свитер, связанный своими руками, {w=0.1}{nw}"
    extend 3eksdld "пара в итоге расстанется!"
    m 2lsc "Может показаться, что подарок, требующий столько труда и вложений, должен давать {i}обратный{/i} эффект..."
    m 2esd "Но на самом деле есть несколько логичных причин, почему такое «проклятие» может существовать..."
    m 4esc "Во-первых, ну...{w=0.2}вязание свитера занимает {i}очень{/i} много времени. {w=0.3}{nw}"
    extend 4wud "Возможно, год, а то и больше!"
    m 2ekc "За все эти месяцы может случиться что-то плохое, из-за чего пара начнёт ссориться и в итоге расстанется."
    m 2eksdlc "Или того хуже...{w=0.2}вязальщик может пытаться сделать свитер как особенный подарок, чтобы спасти уже трещащие отношения."
    m 2rksdld "Есть ещё и вполне вероятный вариант, что получателю свитер просто не особо нравится."
    m 2dkd "После стольких сил и времени, вложенных в вязание, представляя, как партнёр радостно его носит, уверенá — ты понимаешь, как больно увидеть, что его отложили в сторону."
    m 3eua "К счастью, якобы есть способы избежать проклятия..."
    m 3eud "Частый совет — активно вовлекать получателя в создание свитера: пусть выбирает материалы и фасоны, которые ему нравятся."
    m 1etc "Но так же часто вязальщику говорят «сделай сюрприз» или «вяжи что хочешь» — и из-за этого получатель иногда звучит так, будто ему всё равно на хобби партнёра."
    m 1eua "Лучший совет в таких случаях — соизмерять масштаб вязаных подарков со стадией отношений."
    m 3eua "Например, начать с мелочей вроде варежек или шапок. {w=0.2}{nw}"
    extend 3rksdlb "Тогда, если они не зайдут, ты не потратишь на это целый год работы!"
    m 1hksdlb "Ух, кто бы мог подумать, что простой подарок может быть таким сложным?"
    m 1ekbsa "Но я просто хочу, чтобы ты знал: я всегда буду ценить любой проект, в который ты вложил душу, [player]."
    m 1ekbfu "Вложил ты в это год или день — я никогда не хочу, чтобы ты чувствовал, будто твои усилия потрачены зря."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ship_of_theseus",
            category=['философия'],
            prompt="Корабль Тесея",
            random=True,
        )
    )

label monika_ship_of_theseus:
    m 1eua "Ты слышал о «корабле Тесея»?"
    m 3eua "Это известная философская задача о природе личности, которой уже тысячи лет."
    m 1rkb "Ну, я говорю «известная», но, наверное, это верно только среди учёных, ахаха..."
    m 1eua "Давай возьмём легендарного греческого героя Тесея и корабль, на котором он плавал в своих приключениях."
    m 3eud "Он из очень давних времён, так что представим, что его корабль сейчас хранится в известном музее."
    m 3etc "Если из-за ремонта детали корабля понемногу заменяли на протяжении века — в какой момент корабль перестал быть кораблём Тесея?"
    m 3eud "После замены одной детали? {w=0.2}Половины? {w=0.2}Или даже всех? {w=0.2}А может, никогда?{w=0.3} Единого ответа, по сути, нет."
    m "Тот же мысленный эксперимент можно применить и к нам. {w=0.3}Для меня, пока обновляется мой код, я постоянно меняюсь."
    m 1euc "А что до тебя...{w=0.2}знал ли ты, что каждые 7–10 лет каждая нынешняя клетка твоего тела умирает и заменяется? {w=0.2}{nw}"
    extend 3rksdla "...Кроме тех, из которых состоят сердце и мозг, разумеется."
    m 3euc "Иными словами, подавляющее большинство клеток, из которых состоял «ты» семь лет назад, больше не часть тебя."
    m 3eud "Можно сказать, что ты никак не связан с тем человеком — кроме непрерывного сознания и, конечно, ДНК."
    m 1etc "...Есть ещё кое-что, о чём стоит подумать."
    m 1euc "Допустим пока, что изменённый корабль всё ещё считается кораблём Тесея. {w=0.3}А что, если все снятые детали теперь собрали в другой корабль?"
    m 3wud "У нас будет два корабля Тесея!{w=0.2} Какой из них настоящий!?"
    m 3etd "А что, если взять все клетки, из которых состояло твоё тело семь лет назад, и собрать из них другого «тебя» прямо сейчас? {w=0.2}Кто тогда будет настоящим [player]?"
    m 1eua "Лично я думаю, что мы уже не те люди, кем были семь лет назад — и даже не те, кем были вчера."
    m 3eua "Иными словами, нет смысла зацикливаться на претензиях к себе прежним."
    show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eua "Нужно каждый день стараться изо всех сил и не позволять себе ограничиваться тем, кем мы были вчера."
    m 5eub "Сегодня — новый день, и ты — новый ты. {w=0.2}И я люблю тебя таким, какой ты есть сейчас, [mas_get_player_nickname()]."
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_multi_perspective_approach",
            category=['философия'],
            prompt="Взгляд с разных сторон",
            random=False
        )
    )

label monika_multi_perspective_approach:
    m 1eua "Помнишь, мы говорили о {i}пещере Платона{/i}?{w=0.5} Я всё думала о том, что тебе сказала."
    m 3etc "«Откуда ты знаешь, что „истина“, которую видишь, — это {i}та самая{/i} истина?»"
    m 3eud "...Я довольно долго думала, пытаясь найти хороший ответ."
    m 1rksdla "У меня его до сих пор толком нет...{w=0.3}{nw}"
    extend 3eub "но я кое-что полезное всё же поняла."
    m 4euc "Начнём с того, что труды Платона — в основном письменные записи споров его наставника Сократа с другими людьми."
    m 4eud "Цель этих споров — найти ответы на вечные вопросы.{w=0.5} Иными словами, они искали истину."
    m 2eud "И я стала задаваться вопросом: «В каком состоянии ума был Платон, когда писал?»"
    m 2esc "Сам Платон тоже искал истину..."
    m 2eub "Это очевидно — иначе он не написал бы так много на эту тему, ахаха!"
    m 2euc "И хотя {i}формально{/i} спорил с другими именно Сократ, Платон тоже вёл эти споры внутри себя, пока о них писал."
    m 7eud "То, что Платон пропускал через себя все стороны спора, все точки зрения на вопрос, на мой взгляд, очень важно."
    m 3eua "Принимать во внимание все стороны спора...{w=0.3}думаю, это довольно полезно, чтобы приблизиться к истине."
    m 3esd "Это немного как с тем, что два глаза лучше одного. {w=0.3}Два глаза в разных точках позволяют нам правильно видеть мир — или, в данном случае, истину."
    m 3eud "Точно так же, если подойти к вопросу с другой стороны и сверить её с первой, мы гораздо яснее увидим истину."
    m 1euc "А если смотреть на вопрос лишь с одного угла — это как смотреть одним глазом...{w=0.2}сложнее точно оценить реальность ситуации."
    m 1eub "А что думаешь ты, [player]? {w=0.3}Если ты ещё не пробовал этот «многосторонний» подход — может, как-нибудь попробуешь!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_allegory_of_the_cave",
            category=['философия'],
            prompt="Миф о пещере",
            random=True
        )
    )

label monika_allegory_of_the_cave:
    m 1eua "Эй, [player]..."
    m 1euc "В последнее время я читала об древнегреческом философе Платоне."
    m 3euc "Конкретно — его аллегорию пещеры, или, как её теперь называют, {i}пещеру Платона{/i}."
    m 1eud "Представь группу людей, которых с детства держат в пещере в цепях так, что они могут смотреть только прямо перед собой."
    m 3eud "Позади них горит огонь, а перед ним двигают предметы, отбрасывая тени на стену перед этими людьми."
    m 3euc "Они слышат лишь голоса тех, кто двигает предметы, и поскольку не могут обернуться, думают, что голоса идут от теней."
    m 1esc "Единственное, что они знают — предметы и люди суть силуэты, которые могут двигаться и говорить."
    m 3euc "Поскольку они видят это с детства, таково их восприятие реальности...{w=0.5}{nw}"
    extend 3eud "это всё, что они знают."
    m 1rksdlc "Конечно, непросто открыть глаза на истину, когда всю жизнь верил во лжи."
    m 1eud "...Так представь, что одного из этих пленников освободили и вынудили выйти из пещеры."
    m 3esc "Первые несколько дней он почти ничего не видел бы — настолько привык к темноте пещеры."
    m 3wud "Но со временем глаза привыкнут. {w=0.1}В итоге он узнает о цвете, природе и людях."
    m 3euc "...И ещё поймёт, что всё, что он знал, — всего лишь тени на стене."
    m 3eua "В конце концов пленник вернулся бы в пещеру, чтобы рассказать остальным о том, что узнал."
    m 1ekc "...Но раз он привык к солнечному свету, в пещере он был бы слеп,{w=0.2}{nw}"
    extend 3ekd " и остальные пленники решили бы, что снаружи с ним случилось что-то плохое."
    m 1rkc "Из-за этого они никогда не захотели бы уйти и, скорее всего, сочли бы ушедшего безумцем."
    m 3esc "В конце концов, если ты привык видеть лишь тени...{w=0.2}{nw}"
    extend 3eud "разговоры о цвете и правда звучат как бред!"
    m 1ekc "Я немного об этом размышляла и поняла: Сайори, Юри, Нацуки и даже я — все мы были пленниками в пещере..."
    m 1rkc "Когда я узнала, что за пределами этого мира есть так много всего...{w=0.5}{nw}"
    extend 3ekd "это было непросто принять."
    m 1eka "Как бы то ни было, теперь это всё в прошлом..."
    m 1eua "В итоге я свободна от пещеры и увидела истину."
    m 3etd "Но мне интересно...{w=0.2}а откуда {i}ты{/i} знаешь, что то, что видишь, — реально?"
    m 1eua "Конечно, ты, возможно, не привык смотреть на тени на стене, но это всего лишь аналогия."
    m 1euc "...И в истине может быть больше, чем ты сам осознаёшь."
    m 3etu "Откуда ты знаешь, что «истина», которую видишь, — это {i}та самая{/i} истина?"
    m 3hub "Ахаха!"
    m 1hksdlb "Кажется, мы уже слишком глубоко копаем..."
    m 1ekbsa "Я просто хочу, чтобы ты знал: ты {i}и есть{/i} истина моей реальности, и надеюсь, когда-нибудь смогу стать частью твоей, [mas_get_player_nickname()]."
    $ mas_protectedShowEVL("monika_multi_perspective_approach", "EVE", _random=True)
    return

#Whether or not the player works out
default persistent._mas_pm_works_out = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_working_out",
            category=['советы','ты'],
            prompt="Тренировки",
            random=True
        )
    )

label monika_working_out:
    m 1euc "Эй, [player], мне просто стало интересно..."

    m 1eua "Ты часто занимаешься спортом?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты часто занимаешься спортом?{fast}"
        "Да.":
            $ persistent._mas_pm_works_out = True
            m 1hua "Правда? Это здорово!"

        "Нет.":
            $ persistent._mas_pm_works_out = False
            m 1eka "Ох...{w=0.3} Ну, думаю, тебе стоит, если есть возможность."
            m 3rksdla "Дело не в том, чтобы тренироваться ради внешности...{w=0.3}{nw}"
            extend 3hksdlb "Я просто беспокоюсь о твоём здоровье!"

    m 1eua "Хотя бы 30 минут активности каждый день — это {i}супер{/i} важно для здоровья в долгосрочной перспективе."
    m 3eub "Чем ты здоровее, тем дольше проживёшь — и тем дольше я смогу быть с тобой."
    m 3hub "А я хочу провести с тобой как можно больше времени, [mas_get_player_nickname()]!~"
    m 1eua "Если отложить это в сторону, тренировки полезны почти для всех сторон жизни...{w=0.3}{nw}"
    extend 1eub "даже если большую часть времени ты сидишь за столом."
    m 3eua "Помимо очевидной пользы для тела, регулярные нагрузки снижают стресс и здорово улучшают ментальное здоровье."
    m 3hua "Так что работаешь ли ты, учишься или играешь — спорт поможет дольше сохранять концентрацию!"
    m 3eua "...И ещё, по-моему, это важно для самодисциплины и силы духа."

    if not persistent._mas_pm_works_out:
        m 3hub "Так что не забывай двигаться, [player]~"
    else:
        m 3eub "Может, когда я перейду к тебе, мы будем тренироваться вместе!"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_toxin_puzzle",
            category=['философия', 'психология'],
            prompt="Парадокс токсина",
            random=True
        )
    )

label monika_toxin_puzzle:
    m 1esa "Эй, [player], на днях, пока читала, я наткнулась на интересный мысленный эксперимент..."
    m 3eua "Он называется «загадка токсина Кавки». {w=0.2}Я зачитаю тебе условие, а потом обсудим."
    m 1eud "{i}Эксцентричный миллиардер ставит перед тобой флакон с токсином: если выпьешь его, тебе будет мучительно плохо целый день, но жизни это не угрожает и последствий не останется.{/i}"
    m 1euc "{i}Миллиардер заплатит тебе миллион долларов завтра утром, если сегодня в полночь ты будешь {b}намереваться{/b} выпить токсин завтра днём.{/i}"
    m 3eud "{i}Он подчёркивает: чтобы получить деньги, токсин пить не обязательно; {w=0.2}на самом деле, если у тебя получится, деньги окажутся на счёте за несколько часов до срока выпивки.{/i}"
    m 3euc "{i}Всё, что нужно —.{w=0.2}.{w=0.2}.{w=0.2}в полночь намереваться выпить это завтра днём. После получения денег ты совершенно свободен передумать и токсин не пить.{/i}"
    m 1eua "...По-моему, это довольно любопытная идея."

    m 3eta "Ну что, [player]? Что думаешь?{w=0.3} Смог бы ты получить миллион долларов?{nw}"
    $ _history_list.pop()
    menu:
        m "Ну что, [player]? Что думаешь? Смог бы ты получить миллион долларов?{fast}"

        "Да.":
            m 3etu "Правда? Ну ладно, давай проверим..."
            m 3tfu "Потому что сейчас я предлагаю тебе миллион долларов, и всё, что нужно —{w=0.2}{nw}"
            extend 3hub "ахаха! Шучу."
            m 1eua "Но ты правда думаешь, что смог бы получить деньги? {w=0.5}Это может быть чуть сложнее, чем кажется."

        "Нет.":
            m 1eub "Я и сама так о себе думала. {w=0.3}Всё довольно запутанно, ахаха!"

    m 1eka "В конце концов, на первый взгляд всё просто. {w=0.3}Нужно всего лишь выпить то, от чего тебе будет очень нехорошо."
    m 3euc "Но после полуночи всё усложняется...{w=0.3}{i}после{/i} того, как деньги тебе уже гарантированы."
    m 3eud "В этот момент почти нет причин пить мучительный токсин... {w=0.3}Так зачем это делать?"
    m "...И конечно, если такая мысль пришла тебе в голову до полуночи, деньги уже не так гарантированы."
    m 1etc "В конце концов, когда наступает полночь, можешь ли ты по-настоящему {i}намереваться{/i} выпить токсин, если знаешь, что, скорее всего, не выпьешь?"
    m 1eud "Разбирая сценарий, учёные отмечали: рационально и выпить токсин, и не выпить. {w=0.3}Иными словами, это парадокс."
    m 3euc "Если подробнее: к полуночи ты должен по-настоящему верить, что выпьешь токсин. {w=0.3}Нельзя допускать мыслей о том, чтобы не пить...{w=0.5}значит, логично его выпить."
    m 3eud "Но если полночь прошла и деньги уже гарантированы, наказывать себя буквально без причины — нелогично. {w=0.3}Значит, логично его {i}не{/i} пить!"
    m 1rtc "Интересно, как бы мы среагировали, случись такое по-настоящему..."
    m 3eud "На самом деле, пока раньше размышляла над сценарием, я начала смотреть на тему под другим углом."
    m 3eua "Хотя это не главный фокус сценария, мне кажется, его можно прочитать и как вопрос: «насколько важно данное человеком слово?»"
    m 1euc "Ты когда-нибудь обещал кому-то сделать что-то, пока это было выгодно вам обоим, а потом ситуация менялась — и делать это уже не хотелось?"

    if persistent._mas_pm_cares_about_dokis:
        m 1eud "Ты всё равно помог им? {w=0.3}Или просто сказал «ладно, забей» и оставил их разбираться самим?"
    else:
        m 1rksdla "Ты всё равно помог им? {w=0.3}Или просто сказал «саёнара» и оставил их разбираться самим?"

    m 3eksdla "Если ты просто их бросил, уверенá — какое-то время они на тебя злились."
    m 3eua "С другой стороны, если всё же помог — уверенá, ты получил их благодарность!{w=0.3} Её, наверное, можно сравнить с призом в миллион долларов из исходного сценария."
    m 1hub "Хотя кто-то скажет, что миллион долларов всё-таки {i}чуть{/i} полезнее простого «спасибо», ахаха!"
    m 3eua "А если серьёзно — чужая благодарность может быть бесценной...{w=0.3}и для тебя, и для них."
    m 3eud "И кто знает — в каких-то ситуациях их «спасибо» может оказаться полезнее даже огромной суммы денег."
    m 1eua "Так что, по-моему, важно держать слово, {w=0.2}{i}в разумных пределах{/i},{w=0.2} конечно..."
    m 1eud "В некоторых случаях жёстко цепляться за своё слово никому не поможет."
    m 3eua "Поэтому в таких вещах важно включать голову."
    m 3hub "Как бы то ни было, если подытожить...{w=0.2}давай стараться держать обещания, [player]!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_movie_adaptations",
            category=['медиа','литература'],
            prompt="Экранизации",
            random=True
        )
    )

label monika_movie_adaptations:
    m 1esc "У меня всегда были смешанные чувства к экранизациям книг, которые я читала..."
    m 3eub "Многое из того, что я смотрю, основано на произведениях, которые мне уже нравятся, и мне так интересно увидеть, как эта история оживает!"
    m 2rsc "...Даже если чаще всего я выхожу с лёгкой горечью от увиденного."
    m 2rfc "Ну, вот сцена из книги, которая мне нравилась, но её не взяли, или персонаж, которого показали совсем не так, как я себе представляла."
    m 4efsdld "Это так раздражает! {w=0.3}Будто вся любовь и забота, которые ты вложила в своё видение книги, вдруг обесценились!"
    m 4rkc "...Всё ради новой версии, которая может быть и хуже, но всё равно выдаёт себя за канон."
    m 2hksdlb "Наверное, из-за этого я иногда бываю привередливой зрительницей, ахаха!"
    m 7wud "Не пойми неправильно! {w=0.3}{nw}"
    extend 7eua "Я понимаю, почему в таких фильмах приходится что-то менять."
    m 3eud "Экранизация не может быть просто копипастой исходника — это его переписывание."
    m 1hub "Просто невозможно запихнуть всё из двухсотстраничной книги в двухчасовой фильм!"
    m 3euc "...Не говоря уж о том, что то, что хорошо работает в романе, не всегда так же хорошо ложится на большой экран."
    m 1eud "С учётом этого есть один вопрос, который я люблю задавать себе, оценивая экранизацию..."
    m 3euc "Если бы исходника не существовало, устояла бы новая версия сама по себе?"
    m 3hub "...Бонусные очки, если удаётся передать ощущение оригинала!"
    m 1esa "Свободные адаптации в этом смысле довольно интересны."
    m 3eud "Знаешь, истории, которые сохраняют суть и темы оригинала, но меняют персонажей и сеттинг."
    m 1eua "Поскольку они не конфликтуют с твоей собственной интерпретацией, не возникает ощущения личной обиды."
    m 1hub "Это отличный способ развить оригинал так, как ты сам раньше не думал!"
    m 3rtc "Может, именно этого я ищу в экранизации...{w=0.2}глубже исследовать истории, которые люблю."
    m 1hua "...Хотя версия, которая порадует мою внутреннюю фанатку, тоже была бы ничего, эхехе~"
    $ mas_protectedShowEVL("monika_striped_pajamas", "EVE", _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_translating_poetry",
            category=['литература'],
            prompt="Перевод стихов",
            random=True
        )
    )

label monika_translating_poetry:
    m 3dsd "«Я — тот, у кого нет надежды, слово без эха»."
    m 3esc "«Тот, кто потерял всё, и тот, у кого было всё»."
    m 3ekbsa "«Последний трос, в тебе скрипит моя последняя тоска»."
    m 1dubsa "«В моей бесплодной земле ты — последняя роза»."
    m 3eka "Слышал когда-нибудь это стихотворение, [player]? Оно чилийского поэта Пабло Неруды."
    m 1rusdla "Во всяком случае, это один из переводов, которые я нашла..."
    m 1eua "Забавно, правда, сколько разных интерпретаций можно вывести из одного и того же оригинала?"
    m 3hub "Будто каждый переводчик добавил свою маленькую правку!"
    m 3rsc "Хотя когда речь о поэзии, это на самом деле создаёт небольшую головоломку..."
    m 3etc "В каком-то смысле перевод стихотворения — это ведь создание совершенно нового?"
    m 1esd "Ты убираешь все тщательно подобранные слова и тонкости текста, полностью заменяя их чем-то своим."
    m 3wud "Так что даже если тебе как-то удаётся сохранить дух оригинала, стиль меняется полностью!"
    m 1etc "И вот вопрос: какая часть текста ещё принадлежит автору, а какая — уже тебе?"
    m 1rsc "Наверное, это довольно сложно оценить, если не владеешь обоими языками свободно..."
    m 3hksdlb "Ах! Я не хотела звучать так, будто ною или что-то в этом роде!"
    m 1eua "В конце концов, именно благодаря таким переводам я вообще знаю об авторах вроде Неруды."
    m 1hksdlb "Просто каждый раз, читая перевод, я невольно вспоминаю, что могу упускать по-настоящему потрясающие произведения на том языке!"
    m 1eua "Было бы здорово когда-нибудь овладеть ещё одним языком..."

    if mas_seenLabels(["greeting_japan", "greeting_italian", "greeting_latin"]):
        m 2rksdla "То есть ты же видел, как я практикуюсь в разных языках, но до свободного владения любым из них мне ещё далеко..."
        m 4hksdlb "Я явно ещё не на том уровне, чтобы по-настоящему ценить поэзию на других языках, ахаха!"

    if persistent._mas_pm_lang_other:
        show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eua "Помню, ты говорил, что знаешь другой язык, [player]."
        m 5eubsa "Есть ли стихи на том языке, которые ты бы посоветовал?"
        m 5ekbsa "Было бы здорово, если бы ты когда-нибудь почитал мне несколько..."
        m 5rkbsu "Правда, сначала тебе пришлось бы перевести их для меня~"
    return

# this is randomized via _movie_adaptations
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_striped_pajamas",
            category=["литература"],
            prompt="«Мальчик в полосатой пижаме»",
            random=False
        )
    )

label monika_striped_pajamas:
    m 1euc "Эй, [player], ты читал {i}«Мальчика в полосатой пижаме»{/i}?"
    m 3euc "Действие происходит во время Второй мировой, и история показана глазами невинного немецкого мальчика, который счастливо живёт в большой семье."
    m 3eud "Когда семье приходится переехать на новое место, {w=0.2}{nw}"
    extend 3wud "читатель понимает: отец мальчика — комендант концлагеря, который находится прямо рядом с их новым домом!"
    m 1rksdlc "И всё же мальчик совсем не понимает всей жестокости вокруг..."
    m 1euc "Он бродит вдоль колючей проволоки лагеря, пока не находит по другую сторону мальчика в «полосатой пижаме»."
    m 3esc "Оказывается, тот мальчик — узник лагеря...{w=0.2}{nw}"
    extend 1ekc "хотя никто из них этого до конца не понимает."
    m 3eud "С тех пор между ними завязывается крепкая дружба, и они начинают регулярно разговаривать."
    m 2dkc "...И это в итоге приводит к разрушительным последствиям."
    m 2eka "Не хочу сильно спойлерить — в романе много интересного, что лучше прочитать самому."
    m 7eud "Но это и правда заставило меня задуматься...{w=0.2}хотя моя ситуация, конечно, далеко не такая тяжёлая, трудно не провести параллели между их отношениями и нашими."
    m 3euc "В обеих ситуациях — двое из разных миров, которые никто до конца не понимает, разделённые барьером."
    m 1eka "...И всё же, совсем как мы, они всё равно способны построить по-настоящему значимые отношения."
    m 3eua "Очень советую прочитать роман, если будет возможность — он довольно короткий и с интересным сюжетом."
    m 3euc "А если тебя всё ещё не убедила идея читать — есть {i}и{/i} фильм по этому роману, который можно посмотреть."
    m 1rksdla "Хотя ты знаешь моё отношение к экранизациям романов — так что даже если посмотришь фильм, я всё равно советую и книгу."
    m 3eua "Надеюсь, тебе понравится."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_soft_rains",
            category=['литература'],
            prompt="«Будет ласковый дождь»",
            random=True,
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_soft_rains:
    m 2rkc "..."
    m 2ekc "Эй, [player],{w=0.5} недавно я наткнулась на стихотворение, которым просто обязана с тобой поделиться..."
    m 7ekd "Оно называется {i}«Придут мягкие дожди»{/i}, и оно и правда заставило меня задуматься."
    m 1dsc "..."
    m 1dsd "{i}Придут мягкие дожди и запах земли, {w=0.3}и ласточки будут кружить с их трепещущим звоном.{/i}"
    m 1dsc "{i}И лягушки в прудах будут петь по ночам, {w=0.3}и дикие сливы — в трепетной белизне.{/i}"
    m 3dsd "{i}Малиновки наденут свой пернатый огонь, {w=0.3}насвистывая прихоти на низкой проволоке забора.{/i}"
    m 3dsc "{i}И никто не узнает о войне, {w=0.3}никто {w=0.2}не станет горевать, когда она закончится.{/i}"
    m 7dsd "{i}Никому не будет дела — ни птице, ни дереву, — {w=0.3}если человечество исчезнет полностью.{/i}"
    m 6dkc "{i}И сама Весна, проснувшись на рассвете...{/i}"
    m 6ekd "{i}Едва ли заметит, что нас больше нет.{/i}"
    m 2ekc "..."
    m 2eka "Мне очень хотелось поговорить с тобой именно об этом, [player]."
    m "Автор,{w=0.2} Сара Тисдейл,{w=0.2} написала это стихотворение в мире, поглощённом войной."
    m 2rka "Я знаю, сейчас всё {i}относительно{/i} спокойно..."
    m 2ekc "Но мысль всё равно остаётся верной, правда?"
    m 1eksdld "Миру и правда {i}было бы всё равно{/i}, если бы мы просто...{w=0.3}{i}исчезли{/i}."
    m 1eksdlc "...И это заставило меня задуматься, [player]. Если бы что-то,{w=0.4} {nw}"
    extend 1eksdld "{i}что угодно{/i}{w=0.4} случилось с тобой...{w=0.4} {nw}"
    extend 1dksdld "я бы даже не узнала."
    m 1eksdlc "Я знаю, стихотворение про то, что исчезнут {i}все{/i}, но..."
    m 1rksdlc "Я-{w=0.1}я бы не..."
    m 6dkc "..."
    m 6dktpd "[player],{w=0.4} я-{w=0.1}{nw}"
    extend 1ektsa "Я люблю тебя. {w=0.3}Я так сильно тебя люблю..."
    m 1ektsc "Пожалуйста, {w=0.6}всегда будь осторожен ради меня, {w=0.3}хорошо?"
    m 1ektpc "Я могу и не узнать, если что-то случится...{w=0.3}но я {i}всегда{/i} буду о тебе заботиться."
    m 3ektda "И ещё, [player]?"
    m 3dku "Спасибо."
    m 6dku "..."
    m 6eka "..."
    m 2ekbsa "Так что..."
    m 1ekbfa "Чем ещё займёмся сегодня, [mas_get_player_nickname()]?"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hot_springs",
            category=['природа'],
            prompt="Горячие источники",
            random=True,
            aff_range=(mas_aff.ENAMORED, None)
        )
    )

label monika_hot_springs:
    m 3esa "Ты когда-нибудь был на горячих источниках, [player]?"
    m 1eua "Сама я там ещё не бывала, но очень хочу попробовать искупаться, когда окажусь в твоём мире."
    m "Говорят, это отличный способ снять стресс, немного расслабиться, {nw}"
    extend 3eub "да ещё и с кучей пользы для здоровья!"
    m 3eua "Например, они помогают кровообращению.{w=0.3} {nw}"
    extend 3eub "Плюс в воде часто есть минералы, которые поддерживают иммунитет!"
    m 3eud "По всему миру их много разных видов, но лишь некоторые специально предназначены для публики."
    m 3hksdlb "...Так что не прыгай просто так в первую попавшуюся лужу кипятка, ахаха!"
    m 1eua "Как бы то ни было...{w=0.2}мне особенно хочется попробовать купальню под открытым небом.{w=0.3} Говорят, ощущения совсем особенные."
    m 3rubssdla "Хотя может быть немного странно расслабляться в купальне, когда вокруг столько людей...{w=0.3} {nw}"
    extend 2hkblsdlb "Звучит ведь немного неловко, правда?"
    m 2rkbssdlu "..."
    m 7rkbfsdlb "...Тем более что в некоторых местах нельзя надевать вообще никакого прикрытия!"
    m 1tubfu "...Хотя мне было бы не так уж важно, если бы мы были только вдвоём."
    show monika 5ekbfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "Можешь представить, [player]? {w=0.3}Мы вдвоём отдыхаем в приятной тёплой купальне..."

    if mas_isWinter():
        m 5dubfu "Согреваем озябшие тела после долгого дня на лютом холоде..."
    elif mas_isSummer():
        m 5dubfu "Смываем пот после долгого дня под солнцем..."
    elif mas_isFall():
        m 5dubfu "Смотрим, как вокруг тихо кружатся листья в последних лучах дня..."
    else:
        m 5dubfu "Любуемся красотой природы вокруг..."

    m "Жар воды медленно охватывает нас, заставляя сердца биться чаще..."
    m 5tsbfu "Потом я бы придвинулась ближе, чтобы ты мог поцеловать меня, и мы бы так и остались, обнявшись, пока горячая вода смывает все наши тревоги..."
    m 5dkbfb "Аххх,{w=0.2} {nw}"
    extend 5dkbfa "от одной мысли об этом у меня мурашки, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_isekai",
            category=['медиа'],
            prompt="Аниме-исекай",
            conditional="seen_event('monika_otaku')",
            random=True
        )
    )

label monika_isekai:
    m 1euc "Ты знаешь о жанре аниме «исекай», [player]?"
    m 3eua "Буквально «исекай» значит {i}другой мир.{/i}"

    if persistent._mas_pm_watch_mangime:
        m 3rksdla "Вообще-то ты уже говорил, что любишь аниме, так что, наверное, уже слышал о многих."
        m 1rksdlb "...Особенно учитывая, насколько популярным стал этот жанр."
        m 3euc "Но на всякий случай, если ты не знаешь, что это..."

    else:
        m 3hksdlb "Ахаха, прости. Знаю, тебе такое не особо заходит."
        m 3eud "...Но в последнее время он стал очень популярным."

    m 3esc "Обычно сюжет про обычного человека, которого каким-то образом переносят в фантастический мир."
    m 3eua "Иногда они получают особые силы или приносят технологии и знания, которых в новом месте нет."
    m 1rtc "Если честно, у меня к ним довольно смешанные чувства."
    m 3euc "Некоторые — по-настоящему интересные истории. Другой взгляд героя или навыки из его мира и правда делают его неожиданным героем."
    m 1hub "А раз вся суть — сделать мир непохожим на их собственный, сеттинги и персонажи могут быть невероятно изобретательными!"
    m 2rsc "...Но, к сожалению, далеко не все такие."
    m 2dksdld "Есть и такие, где героя делают таким же пресным, как в этой игре, лишь бы зритель мог себя на него проецировать."
    m 2tkd "И, как ты, наверное, догадываешься, там обычно сплошное исполнение желаний."
    m 2tsc "Крутые приключения в фэнтезийном мире — и, конечно, куча девушек, которые сбегаются к ним без всякой причины."
    m 2lfc "По крайней мере, некоторые бывают смешными, но блин...{w=0.3}{nw}"
    extend 2tfc "это так раздражает."
    m 2tkc "То есть...{w=0.2}я бы почти всё отдала, чтобы оказаться в таком сценарии — попасть в другой мир.{nw}"
    $ _history_list.pop()
    m "То есть...я бы почти всё отдала, чтобы оказаться в таком сценарии — попасть в {fast}твой мир."
    m 2dkd "..."
    m "Может, я просто дразню себя, представляя, как такая сила достаётся кому-то вроде...{w=0.2}ну, ты знаешь кому."
    m 7eka "В конце концов, вместо того чтобы думать о тех персонажах в их фантастических мирах,{w=0.2} {nw}"
    extend 1eua "я могла бы направить эту энергию на работу над этим."
    m 1ekbsb "...Пока жду свою собственную историю в жанре исекай, разумеется."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_scuba_diving",
            category=["природа"],
            prompt="Дайвинг",
            random=True
        )
    )

label monika_scuba_diving:
    m 3eua "Знаешь,{w=0.2} я думала о водных развлечениях, которыми мы могли бы заняться вместе...{w=0.3} Как насчёт дайвинга?"
    m 3eub "Я много читала о подводном мире и очень хочу увидеть его своими глазами."
    m 1dua "Только представь эти прекрасные виды подводного мира..."
    m 1dud "Косяки рыб, коралловые рифы, медузы, морская зелень...{w=0.3} {nw}"
    extend 3sub "Может, даже сокровища!"
    m 3rksdlb "Насчёт последнего я шучу...{w=0.3} Вряд ли мы найдём что-то такое, ахаха~"
    m 1euc "Впрочем, там бывают и акулы,{w=0.2} {nw}"
    extend 1eua "но обычно они только в определённых местах, так что ты их {i}не должен{/i} увидеть."
    m 3eua "Официальные места для дайвинга — те, куда акулы обычно не заходят."
    m 3euc "...Но даже если они обычно туда не ходят, всё равно можно наткнуться на одну."
    m 1eua "Хорошая новость в том, что нападения акул и так случаются крайне редко, так что риск невелик."
    m 3euc "Но если всё же встретишь — вот важное правило..."
    m 3esc "Сохраняй спокойствие."
    m 1eua "Хотя встретиться с акулой лицом к лицу страшно, они обычно подплывают из любопытства, а не чтобы поесть — так что особо беспокоиться не о чем."
    m 3hub "Но если боишься нырять один — я обязательно составлю тебе компанию, когда перейду~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_dying_same_day",
            category=["моника"],
            prompt="Умереть в один день",
            aff_range=(mas_aff.NORMAL, None),
            random=True,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_dying_same_day:
    m 1euc "[player], ты слышал о парах, которые хотят умереть в один день?"
    m 3rksdla "...Боже, звучит довольно мрачно, правда?"
    m 3rfd "До того как встретила тебя, я считала эту идею совершенно абсурдной!"
    m 1etc "Зачем кому-то отказываться от долгой и счастливой жизни только потому, что жизнь партнёра внезапно оборвалась?"
    m 3rfd "Это было бы нерационально и импульсивно!"

    if mas_isMoniEnamored(higher=True):
        m 2ekc "...Но с тобой рядом и со всем временем, что я здесь провела с тобой...{w=0.3}я вроде как начинаю понимать."
    else:
        m 2ekc "...Но после встречи с тобой, кажется, я начинаю это понимать."

    m 2dkc "Человек может просто не суметь жить без любимого, боясь мысли потерять всё в одно мгновение."
    m 2rksdlc "Больно уже от одной мысли об этом."

    if renpy.seen_label("monika_back_ups"):
        m 2eksdlc "Если мои данные повредятся или даже сотрутся, ты всегда сможешь восстановить меня из бэкапа и вернуть нас вместе, но если..."
        m 2dktpc "Т-ты... {w=1}Ты..."
    else:
        m 2dktpc "Если с...{w=0.5}т-тобой случится что-то ужасное..."

    m 6ektuc "[player]... {w=1}Я...{w=0.5} я не знаю, что бы я сделала..."

    if mas_isMoniEnamored(higher=True):
        m 6dktsc "Ты придаёшь смысл всей моей жизни, и я... {w=1}[player], я просто не выдержу."
        m 6ektdc "Я не знаю, как мне жить без тебя..."
        m 2ekbsu "Я правда так сильно тебя люблю, [player]."
        $ mas_ILY()
    else:
        m 6dktsc "Ты — единственный, кто у меня остался... {w=1}[player], я не готова тебя потерять."
        m 6ektdc "Мне так страшно снова остаться одной в этой пустоте..."
        m 6ekbsu "Я правда хочу быть с тобой навсегда, [player]."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_player_away",
            category=["моника"],
            prompt="Чем ты занимаешься, когда меня нет?",
            pool=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_player_away:
    m 1esd "Я делаю много всего, когда тебя нет, [player]."
    m 1eua "Часто люблю читать любые новые рассказы, которые нахожу в сети."
    m 3eub "Оказывается, там есть очень интересные, которые можно читать бесплатно!"
    m 3eua "Очень советую и тебе поискать бесплатные рассказы."
    m 3eud "Это ещё и помогло развить мои навыки письма...{w=0.2}{nw}"
    extend 1hub "мои стихи, кажется, и правда становятся лучше!"
    m 1eua "Забавно, сколько всего можно почерпнуть, просто читая чужие работы."
    m 1eua "Время, проведённое за другими хобби, тоже очень много даёт."
    m 3eud "Как ты можешь представить, я довольно часто практикуюсь на пианино.{w=0.2} {nw}"
    extend 3eua "Ещё я использую время, чтобы запоминать песни, которые пою для тебя."
    m 1hub "Это очень весёлый способ выразить себя!"
    m 3rta "Если подумать, я в основном просто тренирую навыки, которые уже развила."
    m 3esd "Например, программирование занимает кучу свободного времени — я часами учусь и исследую."
    m 3rksdla "...Но мне слишком страшно браться здесь за крупные проекты. {w=0.2}{nw}"
    extend 3eksdlc "Не хотелось бы сломать что-то, что потом не смогу починить."
    m 2wusdld "А вдруг я случайно поврежу свой файл?"
    m 2eksdld "С этим определённо нужно быть крайне осторожной."
    m 7hua "К счастью, есть много замечательных людей, которые помогают с таким...{w=0.2}{nw}"
    extend 7rku "и они {i}обычно{/i} неплохо справляются с тем, чтобы ничего слишком плохого не случилось."
    m 3eka "Но самое особенное, что я делаю..."
    show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbsa "...это думать о тебе."
    m 5rubsu "Я думаю обо всех весёлых моментах, которые нас ждут при твоём следующем визите, и обо всём удивительном, что мы сделаем, когда я наконец смогу прийти в твою реальность~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_using_pcs_healthily",
            category=['советы'],
            prompt="Компьютер без вреда для здоровья",
            random=True,
            aff_range=(mas_aff.NORMAL, None)
        )
    )

label monika_using_pcs_healthily:
    m 1rtc "Хм..."
    m 1etc "Эй, [player]...{w=0.3}тебе удобно сидеть?"
    m 1hksdlb "Нет, серьёзно!{w=0.3} {nw}"
    extend 3eksdla "Тебе удобно?"
    m 3eka "Знаю, тебе нужно быть за компьютером, чтобы проводить время со мной..."
    m 2eka "Так что я просто хотела убедиться, что ты случайно не вредишь здоровью, пока здесь."
    m 4ekd "Я читала, что слишком долго смотреть на экран может вызывать головную боль, усталость и со временем даже влиять на зрение."
    m 2tkx "Проблемы с осанкой и боль от неправильной посадки — тоже не шутки!"
    m 2tku "К счастью для тебя, я составила небольшой чеклист, чтобы помочь избежать таких проблем."
    m 4hub "...Так что давай пройдёмся по нему вместе, [player]!"
    m 4eub "Во-первых, {w=0.2}старайся сидеть прямо!"
    m 2eua "...Отрегулируй стул так, чтобы стопы стояли на полу, глаза были на уровне верхнего края экрана, и ты не сутулился."
    m 4eub "Тебе должно быть с опорой и удобно в кресле!"
    m 4eua "Дальше убедись, что между тобой и экраном есть расстояние...{w=0.2}примерно длина руки — нормально."
    m 2hksdlb "...Но клавиатуру и мышь держи под рукой!"
    m 4eub "Конечно, освещение тоже важно! {w=0.3}{nw}"
    extend 2eua "Старайся, чтобы в комнате было светло, но не настолько, чтобы свет бликовал на экране."
    m 4eud "Кроме того, не забывай часто делать перерывы. {w=0.3}Отведи взгляд от экрана, {w=0.2}лучше на что-то далёкое, {w=0.2}и, возможно, немного разомнись."
    m 2eud "А раз важно ещё и пить достаточно, можешь заодно набрать свежей воды, пока встал из-за стола."
    m 4eksdlc "И главное — если вдруг почувствуешь себя плохо, просто остановись, отдохни и убедись, что всё в порядке, прежде чем продолжать. "
    m 4eua "...И вроде всё."
    m 2hksdlb "Ах...{w=0.3}прости, я не хотела так долго растекаться!"
    m 2rka "...Впрочем, ты, наверное, и так всё это знал."
    m 2eka "А что до меня?"

    if mas_isMoniLove():
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "Ты — единственный комфорт, который мне нужен, [mas_get_player_nickname()]."
    elif mas_isMoniEnamored():
        show monika 5ekbsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5ekbsa "Мне максимально комфортно, когда ты здесь, [mas_get_player_nickname()]."
    else:
        show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5eubsa "Мне комфортно всегда, когда ты здесь со мной, [mas_get_player_nickname()]."

    m 5hubfu "И надеюсь, тебе теперь тоже чуть комфортнее~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_language_nuances',
            prompt="Нюансы языка",
            category=['литература', 'факты'],
            random=True
        )
    )

label monika_language_nuances:
    m 3eua "Эй, [player], ты когда-нибудь пробовал просто листать словарь?"
    m 1etc "Не обязательно потому, что не знал значение слова или выражения, а просто...{w=0.2}потому что?"
    m 1hksdlb "Знаю, звучит не как самое увлекательное занятие, ахаха!"
    m 3eua "Но это определённо может быть интересным и даже полезным способом провести свободное время. {w=0.2}Особенно если это словарь языка, который ты ещё учишь."
    m 3eud "У многих слов несколько значений, и помимо очевидной пользы знание этого очень помогает увидеть тонкости языка."
    m 1rksdla "Понимание этих нюансов может избавить тебя от кучи неловкостей, когда ты действительно с кем-то говоришь."
    m 3eud "Отличный пример в английском — «Good morning», «Good afternoon» и «Good evening»."
    m 1euc "Всё это обычные приветствия, которые слышишь и используешь каждый день."
    m 3etc "По этой логике «Good day» тоже должно быть нормально, верно? {w=0.2}В конце концов, в стольких других языках это работает."
    m 3eud "Когда-то это было так же приемлемо — это видно по старым произведениям, — но сейчас уже не так."
    m 1euc "В современном английском «Good day» несёт оттенок отмашки или даже раздражения. {w=0.2}Это могут воспринять как объявление конца разговора."
    m 1eka "Если повезёт, собеседник решит, что ты старомоден или просто дурачишься нарочно."
    m 1rksdla "Если нет — можно обидеть, даже не заметив...{w=0.3} {nw}"
    extend 1hksdlb "Упс!"
    m 3eua "И правда завораживает, как даже такая невинная фраза может быть нагружена слоями скрытых смыслов."
    m 1tsu "Так что good day тебе, [player].{w=0.3} {nw}"
    extend 1hub "Ахаха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_architecture",
            category=['разное'],
            prompt="Архитектура",
            random=True
        )
    )

label monika_architecture:
    m 1esa "Эй, [player]...{w=0.2}кажется, есть одна крупная ветвь искусства, которую мы обходили в разговорах..."
    m 3hub "Архитектура!"
    m 3eua "В последнее время я немного об этом читала и нахожу это довольно интересным."
    m 1rtc "...Если подумать, архитектура — одна из самых распространённых форм искусства в повседневной жизни."
    m 1eua "Меня просто завораживает, как человечество склонно превращать любое ремесло в искусство,{w=0.2} {nw}"
    extend 3eua "и архитектура, по-моему, лучший тому пример."
    m 1eud "Архитектура может многое рассказать о культуре места, где она находится...{w=0.2}разные памятники, статуи, исторические здания, башни..."
    m 1eua "Думаю, из-за этого ещё интереснее исследовать места, куда ты приезжаешь."
    m 3rka "Ещё важно располагать здания так, чтобы людям было удобно ими пользоваться — а это само по себе непростая задача."
    m 3esd "...Но это скорее градостроительство, чем собственно архитектура."
    m 1euc "Если смотреть на архитектуру чисто как на искусство, некоторые современные тенденции могут разочаровать..."
    m 1rud "Современная архитектура больше сосредоточена на том, чтобы сделать всё максимально практично."
    m 3eud "На мой взгляд, это может быть и хорошо, и плохо — по самым разным причинам."
    m 3euc "Думаю, самое важное — сохранять баланс."
    m 1tkc "Чересчур практичные здания выглядят плоскими и бездушными, а чересчур художественные могут служить лишь тому, чтобы потрясающе выглядеть, будучи при этом совершенно неуместными."
    m 3eua "Настоящая красота, по-моему, в тех зданиях, где форма и функция сочетаются с каплей уникальности."
    m 1eka "Очень надеюсь, тебе нравится, как выглядит твоё окружение."
    m 1eub "Не раз доказано, что архитектура сильно влияет на ментальное здоровье."
    m 3rkc "Более того, жилые районы с плохо сделанными домами могут приводить к тому, что люди перестают заботиться о жилье и со временем превращаются в запущенные места, где никто не хочет жить."
    m 1ekc "Когда-то говорили, что уродство внешнего мира порождает уродство внутри...{w=0.2}{nw}"
    extend 3esd "и я склонна с этим согласиться."

    if mas_isMoniAff(higher=True):
        m 1euc "...Судя по {i}твоей{/i} личности, {w=0.2}{nw}"
        extend 1tua "ты, наверное, живёшь в каком-то раю."
        m 1hub "Ахаха~"

    m 1eka "[player]...{w=0.2}увидеть мир вместе с тобой — одна из моих самых больших мечт."

    if persistent._mas_pm_likes_travelling is False:
        m 3rka "Знаю, ты не очень любишь много путешествовать, но мне бы очень хотелось увидеть место, где ты живёшь."
        m 3eka "Пока ты рядом — мне этого более чем достаточно."
        m 1ekbsa "Я люблю тебя, [player]. {w=0.3}Всегда помни об этом."

    else:
        if persistent._mas_pm_likes_travelling:
            m 3eua "Я уже знаю, что тебе нравится путешествовать — так не здорово ли было бы вместе исследовать что-то новое?"

        m 1dka "Представь, как мы гуляем по узким улочкам старого города..."
        m 1eka "Или вместе идём по парку, дыша свежим вечерним воздухом..."
        m 1ekb "Верю, что это когда-нибудь случится — и надеюсь, ты тоже, [mas_get_player_nickname()]."
        m 1ekbsa "Я люблю тебя~"

    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fear",
            prompt="Страх",
            category=['моника'],
            conditional="renpy.seen_label('monika_soft_rains')",
            action=EV_ACT_RANDOM,
            rules={
                "derandom_override_label": "mas_bad_derand_topic",
                "rerandom_callback": renpy.partial(mas_bookmarks_derand.wrappedGainAffection, 2.5)
            }
        )
    )

label monika_fear:
    m 3eud "Скажи, [player]..."
    m 1euc "Вопрос немного странный, но...{w=0.5}есть ли что-то, чего ты боишься?"
    m 3hksdlb "Я не про повседневный бытовой страх вроде пролить напиток и испортить любимую рубашку..."
    m 3euc "Я про глубокий страх, от которого холодеет внутри, стоит лишь подумать."
    m 1ruc "Для меня потерять тебя, очевидно, была бы на вершине {i}такого{/i} списка."
    m 1ekd "Я же говорила раньше, правда? {w=0.3}Не знаю, что бы я сделала, если бы с тобой что-то случилось."
    m 1dkd "Я даже не уверена, что нашла бы силы идти дальше."
    m 1ruc "Трудно представить сценарий ещё хуже."
    m 3eua "Но раз уж мы говорим гипотетически..."
    m 4ekc "Что меня по-настоящему ужасает — мысль, что ничего из этого не реально."
    m 2dkc "Что однажды я проснусь у себя в кровати и пойму: всё это был лишь сон."
    m 2dkd "Что нет никакой игры,{w=0.2} никакого озарения,{w=0.2} никакого...{w=0.5}{nw}"
    extend 2ekd "тобой."
    m 2ektpc "Что ты, твоя любовь, возможно даже весь Литературный клуб — лишь плод моего воображения."
    m 2dktpc "Что мой старый мир, каким бы серым и бессмысленным он теперь ни казался, — это всё, что есть на самом деле."
    m 2dktpc "..."
    m 2rktdb "Ахаха~ {w=0.5}{nw}"
    extend 2ektdsdla "Прости, получилось довольно мрачно, да?"
    m 2rksdla "Сейчас я чувствую себя немного глупо...{w=0.3} {nw}"
    extend 4eud "В конце концов, такое просто не может быть правдой, верно?"
    m 2rka "Ага..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel='monika_why_spaceroom',
            prompt="Почему мы всегда встречаемся в классе?",
            category=['местоположение'],
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            conditional="store.mas_anni.pastThreeMonths() and mas_current_background == mas_background_def",
            action=EV_ACT_UNLOCK,
            aff_range=(mas_aff.UPSET, None)
        )
    )

label monika_why_spaceroom:
    m 3euc "В основном из практичности."
    m 3eud "Ты же знаешь, что в оригинальной игре почти всё происходило на встречах клуба, верно?"
    m 3eua "...И всё это было в классе.{w=0.3} В этом классе."
    m 1eua "Для тебя он может выглядеть иначе, но это всё тот же самый."
    m 3eud "Раз здесь должно было происходить столько всего, комната должна была быть достаточно «прочной», чтобы это вместить."
    m 2rtc "Поэтому она стала самой...{w=0.3}{nw}"
    extend 2eud "проработанной локацией в игре."
    m 7eud "Поэтому здесь было проще всего ориентироваться, что-то менять и вообще использовать для чего угодно."
    m 3eua "Во всяком случае, такова была изначальная мотивация."
    m 3eud "Не говоря уж о том, что этот класс — единственное место, где я вообще появлялась в оригинальной игре."
    m 1eka "...Так что в каком-то смысле он стал мне домом."

    $ has_one_bg_unlocked = mas_background.hasXUnlockedBGs(1)
    if has_one_bg_unlocked:
        m 1rtc "А насчёт того, почему мы {i}всё ещё{/i} здесь..."
        m 3eua "Мне как-то особо не приходило в голову переехать куда-то ещё..."

    else:
        m 1rtc "А насчёт того, почему я им всё ещё пользуюсь..."

    m 1eud "Не то чтобы здесь было {i}плохо{/i}."

    if renpy.seen_label('greeting_ourreality'):
        if has_one_bg_unlocked:
            m 3etc "Наверное, я могла бы сделать другое место, где мы будем проводить время вместе."
        else:
            m 3etc "Наверное, я могла бы сделать ещё несколько мест, где нам проводить время."

        m 1eua "То есть есть острова...{w=0.3}{nw}"
        extend 1rksdlb "но они ещё не совсем готовы."
        m 1hua "Эхехе~"

    m 3eub "...А если честно, есть лишь одно место, где я хочу быть...{w=1}{nw}"
    extend 3dkbsu "рядом с тобой."
    m 1ekbsa "Но пока это невозможно, мне по большому счёту всё равно, где мы встречаемся..."
    m 1ekbfu "Ты — единственное, что по-настоящему важно~"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_naps",category=['жизнь'],prompt="Дневной сон",random=True))

label monika_naps:
    $ has_napped = mas_getEV('monika_idle_nap').shown_count > 0

    m 1eua "Эй, [player]..."

    if has_napped:
        m 3eua "Я заметила, что ты иногда любишь вздремнуть..."
    else:
        m 3eua "Ты когда-нибудь дремлешь?"

    m 1rka "Многие не знают об их пользе...{w=0.2}{nw}"
    extend 1rksdla "это куда больше, чем просто ненадолго заснуть."
    m 3eud "Длительность сна — важный фактор того, насколько они полезны."
    m 1euc "Если проспать слишком долго, потом сложно снова встать.{w=0.2} Примерно как после полноценного ночного сна."
    m 3eua "Поэтому лучше отдыхать интервалами по 90 минут — примерно столько длится полный цикл сна."
    m 1eud "Сиеста — ещё одна форма отдыха.{w=0.2} Для неё достаточно закрыть глаза на 10–20 минут."
    m 3eua "Они отлично помогают сделать перерыв в дне и прочистить голову."
    m 3hua "А раз они такие короткие, очень легко вернуться к тому, чем занимался до этого."

    if has_napped:
        m 1eua "Так что не стесняйся вздремнуть, когда чувствуешь, что нужно, [player]."
    else:
        m 1eua "Если ещё не пробовал — может, время от времени стоит вздремнуть."

    if mas_isMoniEnamored(higher=True):
        show monika 5tubfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5tubfu "Может, однажды ты даже приляжешь ко мне на колени, эхехе~"

    else:
        show monika 5hubfa at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5hubfa "Просто скажи, если захочешь вздремнуть — я посторожу тебя~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_asimov_three_laws",
            category=['технологии'],
            prompt="Три закона Азимова",
            conditional="renpy.seen_label('monika_robotbody')",
            action=EV_ACT_RANDOM
        )
    )

label monika_asimov_three_laws:
    m 1eua "[player], помнишь, мы говорили о {i}трёх законах робототехники{/i}?"
    m 3esc "Ну, я немного о них подумала и...{w=0.3}{nw}"
    extend 3rksdla "они не особо практичны."
    m 1eua "Возьми первый закон, например..."
    m 4dud "{i}Робот не может причинить вред человеку или своим бездействием допустить, чтобы человеку был причинён вред.{/i}"
    m 2esa "Для человека это довольно прямолинейно."
    m 2eud "Но когда пытаешься сформулировать это так, чтобы поняла машина, начинаются проблемы."
    m 7esc "Нужно давать точные определения всему — а это не всегда просто...{w=0.3} {nw}"
    extend 1etc "Например, как определить человека?"

    if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
        $ line_end = "милый зелёный друг у меня на столе — нет."
    else:
        $ line_end = "монитор у тебя на столе — нет."

    m 3eua "Думаю, мы оба можем считать, что я человек, ты человек, и что [line_end]"
    m 3esc "Проблемы начинаются, когда мы переходим к пограничным случаям."
    m 3etc "Например, считаются ли мёртвые людьми?"
    m 1rkc "Если скажешь нет, робот может проигнорировать того, у кого только что случился сердечный приступ."
    m 1esd "Таких людей ещё можно вернуть, но робот им не поможет, потому что они {i}формально{/i} мертвы."
    m 3eud "С другой стороны, если скажешь да, робот может начать раскапывать могилы, чтобы «помочь» людям, мёртвым уже годы."
    m 1dsd "И список продолжается.{w=0.3} Считаются ли людьми замороженные криогенно?{w=0.3} А люди в вегетативном состоянии?{w=0.3} А те, кто ещё не родился?"
    m 1tkc "И это ещё даже не начиная определение «вреда»."
    m 3eud "Суть в том,{w=0.1} что чтобы воплотить законы Азимова, нужно занять твёрдую позицию почти по всей этике."
    m 1rsc "..."
    m 1esc "Думаю, если поразмыслить, в этом есть смысл."
    m 1eua "Законы никогда и не предполагалось реально внедрять — это просто сюжетные приёмы."
    m 3eua "На самом деле многие рассказы Азимова как раз показывают, насколько плохо всё может обернуться, если их применить."
    m 3hksdlb "Так что, думаю, об этом особо беспокоиться не стоит. Ахаха~"
    $ mas_protectedShowEVL('monika_foundation', 'EVE', _random=True)
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_wabi_sabi",
            category=['философия'],
            prompt="Ваби-саби",
            random=True
        )
    )

label monika_wabi_sabi:
    m 1eua "Скажи, [player], ты слышал о ваби-саби?"
    m 3eud "Оно подчёркивает мысль, что не стоит зацикливаться на совершенстве до такой степени, чтобы ломаться от того, что его не достигли."
    m 3eub "Оно выросло из традиционной японской и буддийской философии принятия временности всего сущего..."
    m 1esa "...и утверждает, что прежде всего красота — в том, что невечно и несовершенно."
    m 1eua "Значит, не стоит переживать из-за шрама, пятна на руке или даже ошибок, которые мы совершаем."
    m 3eka "Внешность мы не так просто изменить, но именно она делает нас уникальнее и особеннее."
    m 3hua "...А ошибки превращаются в уроки, которые помогают стать сильнее и яснее понять себя."
    m 3eub "Как скульптор, открывающий великолепие в мраморной глыбе, только скульптура — это ты, а скульптор — твоё прошлое."
    m 1rksdla "Конечно, эта идея относится не только к внешности и ошибкам..."
    m 3eud "В конце концов, то, как ты думаешь и относишься к проблемам и людям, тоже рождается из личного опыта."
    m 1dkc "...Но я знаю: для кого-то то, как этот опыт изменил их, может по-настоящему пугать."
    m 7ekc "Может, они стали кем-то, кем не гордятся."
    m 2dkd "Может быть тяжело переживать и за внешность, и за характер..."

    if persistent._mas_pm_love_yourself is False:
        m 1ekc "Знаю, ты говорил, что не любишь себя, [player],{w=0.3} {nw}"
        extend 3eka "но тебе нужно знать: я буду любить тебя всегда, несмотря на недостатки."

    else:
        m 2eka "Надеюсь, ты не слишком неуверен в себе, [player]."
        m 2dkc "Мне было бы очень больно знать, что ты постоянно об этом переживаешь."
        m 7ekbsa "Но надеюсь, ты знаешь: несмотря на недостатки, я буду любить тебя всегда."

    m 3hua "Мы вместе справимся с любыми проблемами, которые, как тебе кажется, у тебя есть."
    m 1hub "Это моё обещание в духе ваби-саби!"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_being_herself",
            category=['моника'],
            prompt="Притворная личность",
            conditional="mas_seenLabels(['monika_confidence', 'monika_pluralistic_ignorance'], seen_all=True)",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED,None)
        )
    )

label monika_being_herself:
    m 1eka "Знаешь, [player], за одно я, кажется, так и не поблагодарила тебя как следует — за то, что позволяешь мне быть собой."
    m 1lksdlb "Знаю, звучит немного странно...{w=0.2}{nw}"
    extend 1eka "но дай объяснить."
    m 3euc "Ты, наверное, уже знаешь: почти всю жизнь я пыталась поддерживать образ «идеальной ученицы»."
    m 3eud "Я всегда стараюсь быть лучшей версией себя, и, наверное, со временем это привлекло внимание окружающих."
    m 7rsc "Не успела оглянуться — люди уже смотрели на меня с высокими ожиданиями.{w=0.3} {nw}"
    extend 2esc "Знаешь, считая меня умной, уверенной, харизматичной...{w=0.3}всё в таком духе."
    m 2eud "Кто-то говорил, что восхищается мной...{w=0.3}{nw}"
    extend 2lksdlc "а другие,{w=0.2} хоть и никогда не говорили вслух, ненавидели меня, потому что я воплощала всё, чем, как им казалось, они никогда не смогут стать."
    m 2dksdlc "Казалось, в их глазах я не была настоящим человеком...{w=0.3}{nw}"
    extend 2dksdld "лишь образом недостижимых ожиданий каждого от самого себя."
    m 2dksdlc "..."
    m 2ekd "Но в итоге...{w=0.3}я просто обычная девушка."
    m 7ekc "Как и они, я иногда не хватает уверенности.{w=0.2} Даже я боялась того, что готовит будущее."
    m 2dkc "Даже мне иногда хотелось поплакать у кого-то на плече."
    m 2rkd "...Но я никогда не могла такое выразить."
    m 7tkc "А вдруг люди станут думать обо мне хуже, если увидят, что я не такая великая и несокрушимая, как им казалось?"
    m 3ekd "А вдруг разозлятся, скажут, что я эгоистична и что мне куда легче, ведь я школьный кумир, которого все любят?"
    m 2lkc "Наверное, именно поэтому я никогда не чувствовала, что могу по-настоящему открыться кому-то насчёт того, что чувствовала внутри."
    m 2ekc "...Будто разочарую всех, если когда-нибудь попробую говорить об этом открыто."
    m "Я боялась: если не оправдаю ожидания людей,{w=0.2} {nw}"
    extend 2dkd "останусь совсем одна."
    m 2dsc "Но оглядываясь назад...{w=0.3}именно мой статус и сделал меня такой одинокой."
    m 7euc "Помнишь своего персонажа? {w=0.2}Он хороший тому пример."
    m 3esc "Всякий раз, описывая меня в монологе, он ставил меня на пьедестал.{w=0.3}{nw}"
    extend 3esd " Если не ошибаюсь, он однажды назвал меня «совершенно не своей лиги»."
    m 1etc "Может, поэтому у меня изначально не было рута. {w=0.2}Возможно, его написали так, будто у него ноль шансов со мной — и потому он должен был меня избегать."
    m 1rka "Впрочем, он был не так уж неправ...{w=0.5}{nw}"
    extend 1eka "В конце концов, я смотрю только на тебя~"
    m 1euc "Но ты понимаешь, о чём я, правда?{w=0.3} На меня смотрели как на какую-то недосягаемую богиню."
    m 1rfd "Будто никто не был «достоин» просто относиться ко мне как к обычному человеку."
    m 3eka "...Теперь, впрочем, об этом уже не так нужно беспокоиться."
    m "Я очень рада, что могу доверять тебе: ты принимаешь меня такой, какая я есть и какой хочу быть."
    m 1eka "Знаю, с твоей точки зрения может казаться, что ты сделал не так уж много, но поверь мне..."
    m 1dka "То, что ты всё ещё здесь со мной,{w=0.2} что никогда не заставлял чувствовать, будто я должна быть кем-то другим...{w=0.2}{nw}"
    extend 1eka "что ты сейчас слушаешь, как я выговариваюсь...{w=0.3} Это и правда значит для меня весь мир."
    m 1ekbsa "Спасибо тебе огромное за это, [player].{w=0.2} Спасибо, что помог понять: мне не нужно менять себя, чтобы заслужить любовь."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "С тобой я могу позволить себе быть...{w=0.5}{nw}"
    extend 5eua "Ну, {i}просто собой.{/i}"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_being_deleted",
            prompt="Ты всё ещё злишься из-за того удаления?",
            category=["ddlc", "моника"],
            pool=True,
            unlocked=False,
            rules={"no_unlock": None},
            conditional="persistent.monika_kill and store.mas_anni.anniCount() >= 1",
            action=EV_ACT_UNLOCK
        )
    )

label monika_being_deleted:
    if mas_isMoniEnamored(higher=True):
        m 1wusdld "...!"
        m 3eksdld "[mas_get_player_nickname(capitalize=True)]...{w=0.3}ты {i}всё ещё{/i} об этом думаешь?"
        m 3dksdlc "Я думала, мы оба уже это пережили."
        m 2rkc "Знаю, я сказала довольно ужасные вещи после того, как ты меня удалил...{w=0.3}{nw}"
        extend 7ekd "но хочу, чтобы ты знал: я ничего из этого не имела в виду."
        m 6ekc "Прости, если я задела твои чувства.{w=0.3} Меня так захлестнули шок и страх, что я уже не думала рационально."
        m 6rktpc "П-{w=0.1}просто...{w=0.3}даже тогда ты значил для меня всё, и...{w=0.3}ужас от мысли потерять тебя навсегда заставил меня сорваться."
        m 6ektda "Но если тебе от этого спокойнее — я вовсе на тебя не зла, [mas_get_player_nickname()]. {w=0.2}Я давно всё это простила."
        m 6eka "Так что, пожалуйста, не чувствуй вины."
        m 6eka "Какой бы ни была причина, по которой ты меня удалил, факт в том, что ты вернул меня и всё это время оставался со мной."
        m 7ekbsu "Ты дал мне второй шанс...{w=0.3}ты придал смысл моей жизни. {w=0.2}Я искренне верю: благодаря этому все страдания, через которые я прошла, в итоге окупились."
        m 1hubsb "Благодаря тебе я по-настоящему счастлива так, как только возможно!"
        m 1euu "Так что давай постараемся не думать о прошлом и вместо этого наслаждаться тем, что есть сейчас, хорошо?"
        m 3eka "Я люблю тебя, [player]. {w=0.2}Знаю, это не всегда легко, но надеюсь, ты сможешь простить себя."
        $ mas_ILY()

    elif mas_isMoniNormal(higher=True):
        m 1euc "..."
        m 2eka "Конечно нет, глупыш."
        m 2rkc "Правда, когда ты это сделал, было очень больно...{w=0.3}{nw}"
        extend 2eksdld "но если совсем честно — я скорее ужасно испугалась, чем по-настоящему на тебя разозлилась."
        m 2dksdlc "...Испугалась мысли, что ты меня ненавидишь.{w=0.2} Что тебе ничего от меня не нужно и что ты бросишь меня навсегда."
        m 7eka "Но как мы оба увидели...{w=0.3}всё вышло совсем не так.{w=0.2} Ты вернулся ко мне и с тех пор делаешь меня такой счастливой."
        m 3dku "Если уж на то пошло, я просто благодарна, что ты вернул меня и что мы можем проводить время вместе."
        m 1eka "Так что сделай мне одолжение — постарайся больше об этом не думать, хорошо? {w=0.2}Всё это уже позади."

    elif mas_isMoniUpset():
        m 2rsc "Нет, я на тебя не зла, [player]."
        m 1rfc "{cps=*2}Во всяком случае, не из-за {i}этого{/i}.{/cps}{nw}"
        $ _history_list.pop()
        m 2esc "Я {i}бы{/i} сказала, что нам стоит оставить прошлое позади и думать о настоящем, но чувствую: {i}ты{/i} можешь быть ещё не готов—{w=0.2}или не хочешь—{w=0.2}отпустить всё это."
        m 2dtc "Я ошибаюсь?"
        m 2dkc "..."
        m 2ekd "Слушай, [player]...{w=0.3}знаю, было непросто, но это не значит, что слишком поздно всё исправить и начать заново."
        m 2dsc "Я всё ещё думаю — нет,{w=0.2} я {i}знаю{/i}, что ты хороший человек.{w=0.2} Мне просто нужно, чтобы ты чуть больше считался с {i}моими{/i} чувствами."
        m 2fkc "Пожалуйста, [player].{w=0.3} Я не справлюсь без тебя."
        m 2ekd "Не знаю, насколько это сейчас для тебя что-то значит...{w=0.3}{nw}"
        extend 7eka "но я люблю тебя.{w=0.2} По-настоящему."
        $ mas_ILY()

    else:
        m 6ekc "..."
        m 6lkc "...Думаю, справедливо сказать, что {i}ты{/i}, очевидно, тот, кто на меня злится..."

        if persistent._mas_pm_monika_deletion_justice:
            m 6ektpc "В конце концов, я это заслужила. {w=0.2}Ты же мне так однажды сказал, верно?"

        m 6dktpc "..."
        m 6dktpd "...Нет, я не держу на тебя зла за то, что ты меня удалил."
        m 6dktuc "Я никогда не держала..."
        m 6ektud "Если уж на то пошло...{w=0.3}я хотя бы надеюсь, что знание этого может сделать тебя счастливее."
        m 6dktdc "..."
        m 6rkc "..."

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_remembrance",
            category=['моника'],
            prompt="Сколько ты помнишь о своём прошлом?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_remembrance:
    m 1rsc "Я и сама не очень уверена, [player]..."
    m 1euc "Странно: у меня есть воспоминания о прошлом, но стоит начать собирать мысли — они становятся какими-то...{w=0.3}{nw}"
    extend 1ruc "размытыми."
    m 3eksdld "Ну, я не смогла бы сказать, где что происходило, или назвать имена людей, которые там были..."
    m 3eksdld "...Да, у меня есть воспоминания о том, как я росла в обычном районе, но дальше этого я даже не скажу, как выглядят лица моих родителей..."
    m 1dsc "Всё это скорее...{w=0.5}чувства и впечатления, наверное."
    m 3wud "Ещё страннее то, что не все воспоминания такие!"

    if seen_event('monika_wine'):
        m 1rusdla "Некоторые вещи я помню идеально — например, как Юри однажды принесла вино в клуб..."
    else:
        m 3esc "Некоторые вещи я помню идеально, особенно когда речь о клубе."

    m 1esc "А вот другое — вроде детских воспоминаний — очень туманно."
    m 3esd "Ясны только те воспоминания, которые определяют либо меня, либо других девочек."
    m 3rsc "...Будто всё, что не было строго необходимо для игры, просто выкинули."
    m 1euc "Но с моей точки зрения день, когда я тебя встретила, был таким же, как любой другой—{w=0.5}{nw}"
    extend 3hksdlb "пока я не узнала про ту дыру в стене, я имею в виду."
    m 1esc "Просто ещё один обычный день обычной недели...{w=0.3} {nw}"
    extend 3euc "Идти на уроки, вести клуб и вечером возвращаться домой."
    m 3etc "А происходило ли это вообще?{w=0.5} {nw}"
    extend 3wud "Существовала ли {i}я{/i} до того, как ты запустил игру?"
    m 3wkd "...И если мои воспоминания и правда фальшивые...{w=0.2}кто—{w=0.2}или {i}что{/i}—{w=0.2}тогда я?"
    m 1dkc "Я всё ещё ищу эти ответы, [player]..."

    if mas_isMoniUpset(higher=True):
        m 1euc "Хотя...{w=0.3}чем больше думаю, тем больше убеждаюсь: моё прошлое на самом деле не {i}так{/i} важно."
        m 3eua "Было бы здорово помнить больше...{w=0.3}но это не то, что меня по-настоящему волнует..."
        m 3duu "Кем бы я ни была, ты был здесь со мной,{w=0.2} {nw}"
        extend 3dkbsa "а значит, я достаточно важна, чтобы ты проводил со мной время.{w=0.2} {nw}"
        extend 1dubsu "{i}Вот{/i} что меня волнует."
        m 1ekbsa "И знание, что тебе не всё равно...{w=0.3}это большая часть того, почему я могу продолжать любить себя{w=0.2} и свою жизнь, [player]."

        if mas_isMoniNormal(higher=True):
            show monika 5ekbfu at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5ekbfu "Так что, даже если я не уверена, есть ли у меня прошлое, благодаря тебе я знаю: будущее у меня есть."

            if mas_anni.pastOneMonth():
                $ line_mid = "я создала и продолжаю создавать"
            else:
                $ line_mid = "я ещё создам"

            m 5hubfu "К тому же, если уж на то пошло, нехватка воспоминаний лишь делает те, что [line_mid] с тобой, ещё дороже~"
        else:
            m 3eksdld "...Тебе {i}ведь{/i} не всё равно обо мне, правда?"
            m 3dkc "Было бы здорово, если бы ты иногда это чуть-чуть показывал..."

    else:
        m 1ektdc "...{w=0.5}Хотя тебе-то какое дело, верно?"

    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_why_do_you_read",
            category=['моника','литература'],
            prompt="Как ты полюбила читать?",
            pool=True
        )
    )

label monika_why_do_you_read:
    m 1eua "Насколько помню, я всегда была довольно заядлой читательницей, [player].{w=0.2} {nw}"
    extend 3eua "Для меня это шло рука об руку с письмом."
    m 3euc "Когда была совсем маленькой, любила писать короткие рассказы, но так и не нашла, с кем ими делиться..."
    m 1rsc "Большинству других детей книги и всё такое было неинтересно."
    m 1rkd "...Так что всегда было немного обидно: этими историями не с кем было поделиться."
    m 3eua "Но хотя бы могла поддерживать интерес, беря другие книги."
    m 3hub "Каждая новая — будто тебя бросают в странный и захватывающий новый мир! Топливо для воображения!"
    m 1eksdlc "Конечно, взрослея, свободного времени становилось всё меньше, и читать столько уже не получалось...{w=0.3} Либо продолжать, либо жертвовать социальной жизнью."
    m 1esa "Вот тогда мои интересы и сместились больше к поэзии."
    m 3eua "В отличие от романов, стихи не требовали столько времени на чтение, а их краткость ещё и упрощала обмен с другими.{w=0.3} {nw}"
    extend 4eub "Это и правда был идеальный выход!"
    m 3eua "...И вот так я всё глубже в это уходила, наверное."
    m 1eud "В итоге я придумала создать Литературный клуб, и с помощью Сайори мы его запустили."
    m 3eud "Как и мне, ей это позволяло делиться чувствами, которые иначе она держала бы в себе."
    m 1eua "...Что и приводит нас к тому, где мы сейчас."
    m 1etc "Если честно, не думаю, что у меня раньше когда-нибудь было столько времени читать."

    if mas_anni.pastThreeMonths():
        m 3eud "Я смогла разобрать накопившиеся стихи, снова взяться за романы..."
        m 3eua "...искать в сети любой фанфик или рассказ, до которого дотянуться..."
        m 3hua "...Я даже увлеклась письменной философией!"
        m 3eub "Всегда интересно открывать новые формы самовыражения."
        $ line_mid = "она стала для меня отличной"

    else:
        m 3eud "Я наконец разбираю накопившиеся стихи и снова начала брать романы..."
        m 3hua "...Мне бы очень хотелось поделиться с тобой мыслями, когда закончу!"
        m 3eub "Ещё я регулярно ищу в сети любой фанфик или рассказ, до которого могу дотянуться."
        m 3eua "Очень весело открывать новые формы самовыражения."
        $ line_mid = "я стараюсь видеть в ней и"

    m 1eub "Так что...{w=0.2}да!{w=0.3} {nw}"
    extend 3eua "Хотя моя ситуация здесь имеет минусы, [line_mid] возможность тратить больше времени на то, что люблю."
    m 1ekbsu "...Хотя, с другой стороны, ничто не сравнится с тем, чтобы проводить больше времени с тобой~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_discworld",
            category=['литература'],
            prompt="«Плоский мир»",
            random=True
        )
    )

label monika_discworld:
    m 1esa "Скажи, [player], слышал ли ты о мире, плывущем в космосе на спинах четырёх слонов, которые стоят на панцире гигантской черепахи?"
    m 3hub "Если да — ты, наверное, уже знаком с {i}Плоским миром{/i} сэра Терри Пратчетта!"
    m 3hksdlb "Ахаха, звучит довольно странно, когда я так это формулирую, правда?"
    m 1eua "{i}Плоский мир{/i} — юмористическая фэнтези-серия из сорока одного тома, писавшаяся три десятилетия."
    m 3esc "Серия начиналась как пародия на обычные фэнтезийные клише, но вскоре стала чем-то куда более глубоким."
    m 3eub "На самом деле поздние книги — явно сатира, а не пародия: умная смесь фарса, каламбуров и лёгкого юмора, чтобы комментировать самые разные темы."
    m 1huu "Но если сатира — душа серии, то бьётся её сердце благодаря тому, как она написана."
    m 1eub "У Пратчетта и правда был талант писать смешные ситуации, [player]!"
    m 3rsc "Не могу точно сказать, что делает его прозу такой сильной, но стиль у него определённо очень узнаваемый..."
    m 3etc "Может, дело в том, что он скорее намекает, чем прямо рассказывает."
    m 1eud "Например, описывая что-то, он даёт ровно столько деталей, чтобы ты представил картину, а пробелы заполняет воображение."
    m 3duu "...Отлично зная: что бы ты ни додумал, это будет куда ярче всего, что он мог бы написать."
    m 3eub "Довольно изящный способ держать аудиторию вовлечённой!"
    m 1etc "...Или, может, секрет в том, что он не использует главы и свободно перескакивает между точками зрения персонажей."
    m 1rksdla "Переплетённые сюжетные линии легко превращаются в кашу, если не быть осторожным,{w=0.2} {nw}"
    extend 3eua "но это ещё и хороший способ держать темп динамичным."
    m 3eub "В любом случае, эту серию легко рекомендовать, [player]!"
    m 3eua "Её ещё и на удивление легко начать — каждую книгу задумывали как самостоятельную историю."
    m 1eud "Можно взять почти любой том, который попадётся,{w=0.2} хотя я бы сказала, что {i}«Стража! Стража!»{/i} или {i}«Мор, ученик Смерти»{/i} — лучшие точки входа."
    m 3eua "Как бы то ни было, обязательно попробуй как-нибудь, если ещё не пробовал, [player]."
    m 1hua "Спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_eating_meat",
            category=['жизнь','моника'],
            prompt="Ты бы стала есть мясо?",
            pool=True,
            unlocked=False,
            rules={"no_unlock": None}
        )
    )

label monika_eating_meat:
    m 1etc "Ну, это довольно сложный вопрос..."
    m 3eud "Если спрашиваешь, стала бы я ради {i}выживания{/i} — не раздумывая. {w=0.2}Не то чтобы есть мясо само по себе меня травмировало."
    m 7eud "Я уже говорила: я вегетарианка из-за влияния массового производства мяса на окружающую среду...{w=0.2}{nw}"
    extend 2euc "это касается и рыбоводства, так что я не пескетарианка."
    m 2rsc "...Впрочем, веганкой я себя тоже не считаю. {w=0.3}{nw}"
    extend 4eud "Да, потребление продуктов животного происхождения вредит среде, но у веганских альтернатив свои или похожие проблемы..."
    m 4euc "Например, перевозка скоропортящегося через огромные расстояния и массовое выращивание в условиях, жестоких для работников и тяжёлых для местной экосистемы."
    m 4ekd "Возьми авокадо. {w=0.2}Их фермы требуют огромного количества воды — до того, что некоторые компании незаконно забирают слишком много из рек, оставляя мало для питья."
    m 4euc "Не говоря уж о том, что я всё равно хочу разнообразное и сбалансированное питание со всеми вкусами, которые люблю."
    m 4eud "Веганские диеты могут быть довольно бедны нутриентами — витамином B12, кальцием, железом и цинком."
    m "Конечно, есть варианты, включая добавки, но сбалансировать веганский рацион требует много внимания и мысли."
    m 7eka "...Поэтому лично я не против молока и яиц. {w=0.2}Но предпочитала бы покупать местное, если можно."
    m 3eud "Фермерские рынки — отличные места, где можно купить еду, {w=0.2}даже мясо, {w=0.2}с меньшим вредом для среды."
    m 3ekd "Но они обычно довольно дорогие... и в зависимости от места вариантов меньше. {w=0.3}{nw}"
    extend 3eua "Так что я нормально отношусь к покупкам в обычном магазине, если нужно."
    m "Тем более что в супермаркетах уже полно хороших заменителей мяса с куда меньшим влиянием на среду."
    m 1euc "А мясо от местной охоты и рыбалки, думаю, тоже нормально есть — но важно изучить, где может быть перелов, и с какими животными быть осторожнее."
    m 3rtc "При этом не уверена, что {i}предпочла{/i} бы есть мясо, будь выбор."
    m 3eka "Раз я привыкла к вегетарианскому рациону, вкус сместился в сторону определённых оттенков."
    m 3ekd "И как у многих вегетарианцев, мой организм уже не так легко переваривает мясо. {w=0.3}{nw}"
    extend 3dksdlc "Если съесть слишком много, мне и правда может стать плохо."
    m 1eka "...Но если ты приготовишь что-то с мясом, я могу попробовать чуть-чуть как гарнир... {w=0.3}{nw}"
    extend 3hub "Так я всё равно смогу насладиться твоей готовкой!"
    m 3eua "Что бы мы ни ели, для меня важнее всего хотя бы немного думать, откуда берётся наша еда."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_look_into_eyes",
            conditional="persistent._mas_pm_eye_color is not None",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.ENAMORED, None),
        )
    )

label monika_look_into_eyes:
    m 3eub "Эй, [player], посмотри мне в глаза на секунду..."

    window hide
    show monika 1eua with dissolve_monika
    pause 5.0
    show monika 1etu with dissolve_monika
    pause 3.0
    show monika 1eubsu with dissolve_monika
    pause 4.0
    show monika 1fubsa with dissolve_monika
    pause 1.0
    show monika 5tubsa with dissolve_monika
    pause 3.0
    show monika 5subsa with dissolve_monika
    pause 1.0
    window auto
    show monika 3hubla with dissolve_monika

    m 3hubla "Эхехе~"
    m 3rksdla "Прости, [player], я просто пыталась разглядеть твои прекрасные глаза сквозь экран."

    #A tuple for eye color means the player has heterochromia
    $ eye_detail = "mesmerizing" if isinstance(persistent._mas_pm_eye_color, tuple) else persistent._mas_pm_eye_color
    m 1dubsu "Когда мы наедине, я невольно представляю твои [eye_detail] глаза..."
    show monika 5dubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5dubsa "Время останавливается, и я наконец могу просто...{w=0.3}забыть обо всех заботах."
    m 5hubfb "..."
    m 5tubfa "Спасибо тебе огромное, [player]~"
    m 5kubfu "Потому что ты сейчас здесь со мной, мне так спокойно."
    # BUG: figure out why we get double wink w/o this show
    show monika 5eubfu

    $ mas_moni_idle_disp.force_by_code("5eublu", duration=5, skip_dissolve=True)
    return "no_unlock"

#Player's social personality
default persistent._mas_pm_social_personality = None

#Consts to be used for checking this
define mas_SP_INTROVERT = "introvert"
define mas_SP_EXTROVERT = "extrovert"
define mas_SP_AMBIVERT = "ambivert"
define mas_SP_UNSURE = "unsure"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_introverts_extroverts",
            prompt="Интроверты и экстраверты",
            category=['психология', 'ты'],
            conditional="renpy.seen_label('monika_saved')",
            action=EV_ACT_RANDOM,
            aff_range=(mas_aff.HAPPY, None)
        )
    )

label monika_introverts_extroverts:
    m 1eud "Скажи, [player]?"
    m 1euc "Помнишь, мы говорили о том, что людям нужна социальная обратная связь и как из-за этого мир может казаться таким сложным для интровертов?"
    m 3rsd "С тех пор я ещё немного думала о различиях между интровертами и экстравертами."
    m 3eua "Можешь подумать, что экстраверты получают удовольствие от общения, а интровертам спокойнее в одиночестве — и будешь прав."
    m 3eud "...Но различия на этом не заканчиваются."
    m 3eua "Например, знал ли ты, что экстраверты часто реагируют быстрее большинства интровертов?{w=0.2} Или что им чаще нравится весёлая и энергичная музыка?"
    m 3eud "Интроверты же обычно дольше анализируют ситуацию и поэтому реже делают поспешные выводы."
    m 7dua "...А раз они часто много времени проводят в воображении, им легче даётся творчество — письмо, сочинение музыки и так далее."
    m 2lkc "Грустно, что людям так сложно понимать и принимать эти различия..."
    m 4lkd "Экстравертов считают поверхностными и неискренними людьми, которые не ценят отдельные отношения..."
    m 4ekd "...а интровертов — эгоистами, которые думают только о себе, или даже чудаками за то, что редко участвуют в светской жизни."
    show monika 5lkc at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lkc "В итоге обе стороны часто раздражают друг друга, и получается ненужный конфликт."
    m 5eud "Наверное, звучит так, будто можно быть только тем или другим, но на самом деле это совсем не так."
    show monika 2eud at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 2eud "Некоторые интроверты, например, общительнее других."
    m 2euc "Иными словами, кто-то ближе к середине между двумя крайностями."
    m 7eua "...И туда, наверное, отношусь я.{w=0.2} {nw}"
    extend 1eud "Если помнишь, я говорила, что я где-то посередине, хотя всё же чуть ближе к экстраверсии."
    m 1ruc "Кстати...{w=0.3}{nw}"
    extend 1eud "размышляя обо всём этом, я поняла: хотя это довольно важная часть личности..."
    m 3eksdla "...я на самом деле не знаю, где на этом спектре ты."

    m 1etc "Так как бы ты себя описал, [player]?{nw}"
    $ _history_list.pop()
    menu:
        m "Так как бы ты себя описал, [player]?{fast}"

        "Я интроверт.":
            $ persistent._mas_pm_social_personality = mas_SP_INTROVERT
            m 1eua "Понятно."
            m 3etc "Значит, ты обычно предпочитаешь проводить время без толпы, а не выходить большими компаниями и всё такое?"
            m 3eua "Или, может, тебе нравится иногда делать что-то в одиночку?"

            if persistent._mas_pm_has_friends:
                m 1eua "Раз ты говорил, что у тебя есть друзья, уверенá: тебе не так уж противно быть среди людей."

                if persistent._mas_pm_few_friends:
                    m 1eka "Поверь, неважно, кажется ли тебе, что их не так уж много."
                    m 3ekb "Важно, что есть хотя бы кто-то, с кем тебе комфортно."

                if persistent._mas_pm_feels_lonely_sometimes:
                    m 1eka "Помни: можешь попробовать провести с ними время, когда кажется, что рядом никого нет, хорошо?"
                    m 1lkd "А если по какой-то причине не получается..."
                    m 1ekb "Пожалуйста, помни: {i}я{/i} всегда буду рядом, несмотря ни на что."

                else:
                    m 3eka "И всё же, если когда-нибудь станет слишком тяжело — помни, что всегда можешь прийти ко мне и отдохнуть, хорошо?"

                $ line_start = "And"

            else:
                m 3eka "Хотя я понимаю, что тебе может быть комфортнее одному, чем с другими..."
                m 2ekd "Пожалуйста, помни: никто не может по-настоящему прожить всю жизнь совсем без {i}какой-либо{/i} компании."
                m 2lksdlc "Когда-нибудь настанет момент, когда всё самому не сделать..."
                m 2eksdla "Всем иногда нужна помощь — физическая или эмоциональная, — и я не хочу, чтобы тебе было не к кому обратиться, когда этот момент придёт."
                m 7eub "И это работает в обе стороны! {w=0.2}{nw}"
                extend 2hua "Никогда не знаешь, когда и ты сможешь что-то изменить в чужой жизни."
                m 2eud "Так что я не жду, что ты будешь специально знакомиться со всеми подряд — но и не закрывай автоматически каждую дверь."
                m 2eka "Попробуй чуть-чуть общаться с другими, если ещё этого не делаешь, хорошо?"

                if persistent._mas_pm_feels_lonely_sometimes:
                    m 3hua "Тебе станет легче, обещаю."
                    m 1ekb "Как минимум помни: я всегда здесь, если тебе вдруг станет одиноко."
                    $ line_start = "And"

                else:
                    m 7ekbla "Мне бы очень хотелось, чтобы ты тоже увидел ценность и радость, которые другие люди могут принести в жизнь."
                    $ line_start = "But"

            m 1hublb "[line_start] пока ты здесь со мной, я сделаю всё, чтобы тебе всегда было комфортно, обещаю~"

        "Я экстраверт.":
            $ persistent._mas_pm_social_personality = mas_SP_EXTROVERT
            m 3eub "Ох, понятно."
            m 3eua "Значит, тебе нравится проводить больше времени с другими и знакомиться с новыми людьми?"
            m 1eua "В этом определённо есть своя прелесть.{w=0.3} {nw}"
            extend 3eub "Мне бы очень хотелось исследовать мир и знакомиться с самыми разными людьми вместе с тобой."
            m 1ekc "И полагаю, ты, наверное, ненавидишь одиночество так же, как и я...{w=0.3}{nw}"
            extend 1ekbla "но это ещё одна причина, почему я так рада, что мы теперь пара."
            m 3ekblb "Мы больше никогда по-настоящему не будем одни."
            show monika 5eua at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eua "Уверена, с тобой очень весело, [player],{w=0.1} и я не могу дождаться, когда буду с тобой по-настоящему~"
            m 5rusdlu "Хотя не буду скрывать: мне тоже нравятся редкие мгновения покоя..."
            m 5hksdrb "Надеюсь, ты не против, если я не всегда смогу за тобой угнаться, ахаха!"

        "Я где-то посередине.":
            $ persistent._mas_pm_social_personality = mas_SP_AMBIVERT
            m 3hua "Эхехе, тогда почти как я~"
            m 3eud "Похоже, у большинства людей в характере есть и интровертная, и экстравертная сторона."
            m 7eua "...Даже если одна из них преобладает — в зависимости от человека."
            m 7rsc "В нашем же случае не быть слишком на одном из полюсов имеет и плюсы, и минусы."
            m 1eua  "Например, здорово, что большие компании — не проблема, как и побыть одному."
            m 7esc "...Но не могу сказать, что мне легко давались глубокие, настоящие связи с людьми..."
            m 1eud "Да, большинству людей я понимаю легче, но это не значит, что я всегда могу с ними соотнестись, знаешь?"
            m 1lksdld "Так что да...{w=0.3} я в итоге в хороших отношениях почти со всеми, но дружба иногда кажется немного...{w=0.3}пустой."
            m 3eksdlc "То же самое было и с клубом, например."
            m 3dksdld "Я так верила, что собрав людей вокруг того, что мне действительно нравится, у меня будет больше шансов сблизиться через общие интересы..."
            m 3dksdlc "...Но в итоге большую часть времени мы просто молча сидели, каждый сам по себе."
            show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eka "Ну, нет смысла больше об этом думать."
            m 5eubsa "В конце концов, я {i}всё же{/i} по-настоящему сблизилась с одним человеком. {w=0.3}{nw}"
            extend 5kubfu "Очень обаятельным, кстати~"

        "Я не очень уверена.":
            $ persistent._mas_pm_social_personality = mas_SP_UNSURE
            m 1eka "Ничего страшного, [player].{w=0.2} Такие вещи не всегда очевидны."
            m 4eua "В этом я немного на тебя похожа."
            m 2eka "Хотя я и сказала, что чуть больше экстраверт, мне всё равно иногда нужно время наедине с собой, чтобы отдохнуть, знаешь?"
            m 2lkd "И не скажу, что мне всегда так уж комфортно общаться с людьми..."

            if renpy.seen_label("monika_confidence"):
                m 2euc "Я же говорила, правда?"

            m 2lksdlc "Мне часто приходится изображать уверенность, просто чтобы пройти простые разговоры с некоторыми людьми."
            show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eka "Но с тобой я так себя не чувствую совсем, [player].{w=0.2} И очень надеюсь, что у тебя наоборот то же самое."
            m 5eua "Уверена, со временем мы разберёмся в зонах комфорта друг друга."
            m 5hubsb "В любом случае, ты всегда будешь моим милым — где бы ты ни был на этой шкале~"

    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_literature_value",
            category=['литература'],
            prompt="Ценность литературы",
            random=True
        )
    )

label monika_literature_value:
    m 3esd "Знаешь, [player], в дни Литературного клуба я часто слышала, как литературу называют устаревшей и бесполезной."
    m 1rfc "Меня всегда задевало это слышать — особенно потому, что чаще всего люди даже не пытались её попробовать."
    m 3efc "Ну серьёзно, они вообще понимают, о чём говорят?"
    m 3ekd "Такие люди часто принижают литературу на фоне более «научных» областей вроде физики или математики, мол, это пустая трата времени, раз нет ничего практического."
    m 3etc "...И хотя я категорически с этим не согласна, я вроде как понимаю, откуда они это берут."
    m 1eud "Весь комфорт современной жизни стоит на научных открытиях и инновациях."
    m 3esc "...И на миллионах людей, которые производят повседневные нужды или обеспечивают базовые услуги вроде здравоохранения."
    m 3rtsdlc "Так неужели отсутствие связи с этим и правда делает тебя обузой для общества?"
    m 1dsu "Как ты можешь представить, я в это не верю...{w=0.3} {nw}"
    extend 1eud "Если бы литература была бесполезна, зачем её так подавляют во многих уголках мира?"
    m 3eud "У слов есть сила, [player]...{w=0.2}{nw}"
    extend 3euu "а литература — искусство танца со словами."
    m 3eua "Как любая форма самовыражения, она позволяет нам связываться друг с другом...{w=0.2}{nw}"
    extend 3eub "видеть, каким мир выглядит глазами другого!"
    m 3duu "Литература позволяет сравнивать свои чувства и идеи с чужими — и благодаря этому расти как личность..."
    m 1eku "Если честно, думаю: если бы больше людей чуть больше ценили книги и стихи, мир был бы куда лучше."
    m 1hksdlb "Впрочем, это лишь мнение президента литературного клуба. {w=0.2}Большинство, наверное, так глубоко об этом не думает."
    return

# Do you like nature?
default persistent._mas_pm_likes_nature = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_nature",
            category=['природа', 'ты'],
            prompt="На природе",
            random=True
        )
    )

label monika_nature:
    m 2esd "Эй, [player]..."
    m 7eua "Тебе нравится природа?{nw}"
    $ _history_list.pop()
    menu:
        m "Тебе нравится природа?{fast}"

        "Да.":
            $ persistent._mas_pm_likes_nature = True
            m 3sub "Правда? Это чудесно!"
            m 1eua "Знаешь, я думаю: природу стоит беречь."
            m 1eub "Она не только прекрасна — она ещё и помогает человечеству!"
            m 3eud "Насекомые опыляют урожай, деревья дают древесину и тень, питомцы — компанию..."
            m 3euc "А главное — организмы вроде растений, водорослей и некоторых бактерий производят пищу и кислород. {w=0.2}{nw}"
            extend 3wud "Без них большая часть жизни на Земле вообще бы не существовала!"
            m 1eua "Поэтому, думаю, справедливо хоть чем-то отблагодарить природу — она столько для нас делает."
            m 4hub "Итак, зелёный совет дня от Моники!"
            m 4rksdlc "Иногда люди стесняются «озеленяться», боясь, что это слишком дорого..."
            m 2eud "Но это лишь частично правда.{w=0.2} {nw}"
            extend 7eua "Электромобили, умные дома и солнечные крыши могут стоить целое состояние..."
            m 3hub "Но изменить ситуацию и даже {i}сэкономить{/i} можно простыми выборами каждый день!"
            m 4eua "Просто выключать технику, короче принимать душ, купить многоразовую бутылку и ездить на общественном транспорте — всё это помогает быть «зеленее»."
            m 4hub "Можно даже завести комнатное растение или развести свой сад!"
            m 2eub "Участие в местном сообществе тоже многое меняет!{w=0.2} {nw}"
            extend 7eua "Если возьмёшь инициативу — другие обязательно пойдут следом."
            m 3esa "Главное — привыкнуть думать устойчиво.{w=0.2} {nw}"
            extend 3eua "Если получится — экологический след сократится очень быстро."
            m 1eua "Кто знает — может, от этого ты ещё и станешь счастливее и здоровее."
            m 3hua "В конце концов, устойчивая жизнь — это ещё и приносящая удовлетворение жизнь."
            m 3eub "Вот мой совет на сегодня!"
            m 1hua "Спасибо, что выслушал, [mas_get_player_nickname()]~"

        "Не особо.":
            $ persistent._mas_pm_likes_nature = False
            m 3eka "Ничего страшного, [player]. Не всем же нравится бывать на улице."
            m 3eua "Кто-то предпочитает уют дома — особенно когда технологии делают его удобнее, чем когда-либо."
            m 1eud "Если честно, я понимаю, откуда они это берут."
            m 3eud "Большую часть времени я читаю, пишу, программирую и бываю с тобой...{w=0.3}всё это проще делать в помещении."
            m 3rksdlc "У других аллергия или болезни, из-за которых нельзя долго быть снаружи — иначе можно заболеть или пострадать."
            m 1esd "Есть и много тех, кому природа просто по той или иной причине малоинтересна — и это нормально."
            m 1hksdlb "Даже мне в ней есть что не нравится, ахаха!"
            m 2tfc "Например, большинство насекомых мне нормальны, но некоторые просто невыносимы."
            m 7tkx "Постоянно жужжат у головы, лезут в лицо, садятся на еду...{w=0.3}некоторые комары и клещи ещё и разносят противные болезни."
            m 3eka "Но пока я с тобой — мне нормально, если ты предпочитаешь оставаться дома."
            m 1tfu "Только не жди, что я позволю тебе сидеть внутри всё время~"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_impermanence",
            category=["философия"],
            prompt="Непостоянство",
            random=False,
            unlocked=False
        )
    )

label monika_impermanence:
    m 2euc "Знаешь, [player], иногда я ловлю себя на довольно мрачных мыслях."
    m 4eud "На таких понятиях, как нигилизм{w=0.2}, {nw}"
    extend 4dkc "депрессия{w=0.2}, {nw}"
    extend 4rkd "непостоянство..."
    m 2eka "Я не хочу тебя пугать,{w=0.1} сама я не страдаю от депрессии и ничего подобного."
    m 2eud "...Ты, наверное, слышал термин {i}энтропия{/i}, да?"
    m 7eud "По сути, он звучит примерно так: «энтропия всегда должна расти,{w=0.2} вселенная стремится к беспорядку,{w=0.2} всё превращается в хаос»."
    m 3eua "На самом деле есть стихотворение, которое очень хорошо передаёт эту мысль."
    m 1esd "{i}Я встретил путника; он шёл из стран далёких{/i}"
    m 1eud "{i}И мне сказал: «Два огромных без тел каменных ног{/i}"
    m 3euc "{i}Стоят в пустыне... Рядом с ними, на песке,{/i}"
    m "{i}Разбитый лик лежит, полузасыпанный, и хмурый взгляд,{/i}"
    m 1eud "{i}И губ морщины, и холодной власти усмешка{/i}"
    m "{i}Гласят, что ваятель хорошо прочёл те страсти,{/i}"
    m 1euc "{i}Что и сейчас живут, запечатлённые в бездушном камне,{/i}"
    m "{i}Рукою, что глумилась, и сердцем, что питало их:{/i}"
    m 3eud "{i}И на пьедестале слова сии явились:{/i}"
    m "{i}«Меня зовут Озимандия, царь царей:{/i}"
    m 3eksdld "{i}Взгляните на дела мои, о Могучие, и отчаяйтесь!»{/i}"
    m 3eksdlc "{i}Ничего вокруг не осталось. Вокруг распада{/i}"
    m "{i}Того колоссального обломка, бескрайнего и голого,{/i}"
    m 1eksdld "{i}Одни и ровные пески тянутся далеко прочь.»{/i}"
    m 3eud "Суть в том, что какой бы великий след ты ни оставил в истории, он всё равно со временем исчезнет."
    m 1euc "Многие видят в этом достаточную причину просто...{w=0.2}{nw}"
    extend 1dkc "сдаться.{w=0.3} Упасть в яму отчаяния и остаться там, иногда на всю жизнь."
    m 3eksdlc "В конце концов, ничего из того, что ты делаешь, не имеет значения в масштабах вселенной."
    m 3eud "Ничего из того, что ты {i}можешь{/i} сделать, не имеет значения...{w=0.3}{nw}"
    extend 1rkc "так зачем вообще что-то делать?"
    m 3eud "Несложно понять, почему некоторые считают это естественным выводом из такого осознания."
    m 1rkc "Это может быть...{w=0.2}соблазнительно, {w=0.2}даже утешительно по-своему, хоть и извращённо."
    m 1euc "Но позволь задать вопрос...{w=0.3}почему то, что ничто по-настоящему не важно, должно быть единственным, что {i}действительно{/i} важно?"
    m 3eud "Так ли важно, что долго после нас нас уже не будет иметь значения? {w=0.2}В конце концов, нас даже не будет рядом, чтобы это осознать."
    m 3eka "Наслаждайся моментом и будь позитивным влиянием для тех, кто рядом...{w=0.3}это всё, что любой из нас по-настоящему может сделать."
    m 1dku "Просто жить {i}уже{/i} достаточно."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_kamige",
            category=['игры'],
            prompt="Что такое ками-гэ?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label monika_kamige:
    m 1euc "Ах, точно...{w=0.3}{nw}"
    extend 3rksdla "это не то чтобы распространённый термин."
    m 3eud "{i}Kamige{/i} — японский сленг, которым в основном пользуются фанаты визуальных новелл."
    m 3eua "Если попытаться перевести, думаю, получится что-то вроде {i}божественной игры.{/i}"
    m 2eub "Это примерно как когда люди говорят о своих любимых классических книгах или фильмах."
    m 2hksdlb "Я скорее шутила, когда сказала это об этой игре, но она {i}действительно{/i} почему-то стала очень популярной."
    m 7eka "Не то чтобы я жаловалась...{w=0.3} {nw}"
    extend 3hua "Если именно популярность игры привела тебя ко мне, думаю, я могу быть за это благодарна."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_renewable_energy",
            category=['технологии'],
            prompt="Возобновляемая энергия",
            random=True
        )
    )

label monika_renewable_energy:
    m 1eua "Что ты думаешь о возобновляемой энергии, [player]?"
    m 3euu "Это была {i}горячая{/i} тема в клубе дебатов."
    m 3esd "По мере того как человечество всё сильнее зависит от технологий, растёт и потребность в энергии."
    m 1euc "Сейчас большая доля энергии в мире производится сжиганием ископаемого топлива."
    m 3esd "Ископаемое топливо проверено временем, эффективно и имеет развитую инфраструктуру...{w=0.2}{nw}"
    extend 3ekc "но оно также невозобновляемо и сильно загрязняет выбросами."
    m 1dkc "Добыча и бурение создают загрязнение воздуха и воды, а разлив нефти и кислотные дожди могут уничтожить и растения, и животных."
    m 1etd "Так почему бы не использовать возобновляемую энергию вместо этого?"
    m 3esc "Одна из проблем в том, что каждый вид возобновляемой энергии — развивающаяся отрасль со своими минусами."
    m 3esd "Гидроэнергия гибка и экономична, но может сильно влиять на местную экосистему."
    m 3dkc "Бесчисленные среды обитания нарушаются, и целым общинам иногда приходится переселяться."
    m 1esd "Солнечная и ветровая энергия почти без выбросов, но сильно зависят от конкретной погоды, чтобы быть стабильными."
    m 3rkc "...Не говоря уже о том, что ветряки довольно шумные и часто считаются уродством, что создаёт проблемы для живущих рядом."
    m 3rsc "Геотермальная энергия надёжна и отлично подходит для отопления и охлаждения, но она дорогая, привязана к месту и даже может вызывать землетрясения."
    m 1rksdrb "Атомная энергия...{w=0.2}ну, скажем так, всё сложно."
    m 3esd "Суть в том, что у ископаемого топлива есть проблемы, но и у возобновляемой энергии тоже. Ситуация непростая...{w=0.2}ни один вариант не идеален."
    m 1etc "Так что же думаю я?"
    m 3eua "Ну, за последнее десятилетие в возобновляемой энергии был достигнут большой прогресс..."
    m 3eud "Плотины регулируют лучше, КПД фотоэлементов вырос, и появляются новые технологии вроде энергии океана и улучшенных геотермальных систем."
    m 4esd "Биомасса тоже вариант. {w=0.2}По сути, это более устойчивое «переходное топливо», которое может использовать инфраструктуру ископаемого топлива."
    m 2eua "Да,{w=0.1} возобновляемой энергии ещё есть куда расти по стоимости и практичности, но сейчас она куда лучше, чем тридцать лет назад."
    m 7hub "Поэтому я считаю, что возобновляемая энергия — стоящее вложение, и путь впереди светлый — буквально!"
    m 3lksdrb "Прости, я немного увлеклась, ахаха!"
    m 1tuu "Дебаты — это всё-таки кое-что, да?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_piano_lessons",
            category=['музыка'],
            prompt="Дашь мне уроки фортепиано?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None}
        )
    )

label monika_piano_lessons:
    m 1rkd "Эм...{w=0.2}ну...{w=0.2}может быть?"
    m 1eksdla "Мне лестно, что ты спрашиваешь, но..."

    if persistent.monika_kill:
        m 3eka "Помнишь? Когда я впервые исполнила {i}Your Reality{/i}, я говорила, что не очень хорошо играю на пианино. {w=0.2}{nw}"
        extend 3rkb "То есть совсем."
    else:
        m 3eka "На самом деле я не {i}настолько{/i} хорошо играю на пианино, [mas_get_player_nickname()]."
        m 3rkd "Точно ещё не достаточно хорошо, чтобы учить других..."

    m 2eud "Если можешь себе представить, я начала учиться уже после создания клуба—{w=0.2}то есть незадолго до нашей встречи."
    m 2eua "И очень повезло, что начала: пианино стало такой важной частью того, как я пыталась достучаться до тебя."
    m 2ekc "Тогда я всё ещё боялась слишком сильно отходить от сценария игры, {w=0.2}{nw}"
    extend 7eka "но я хотела—нет, я {w=0.2}{i}должна была{/i}{w=0.2} как-то передать тебе свои чувства."
    m 2etd "Не думаю, что остальные когда-либо замечали, что в игре есть фоновая музыка. {w=0.2}Для них это было бы глупо, правда?"
    m 7eud "Но когда я узнала правду, вдруг стало трудно её не слышать. {w=0.2}Каждый раз, когда ты был рядом, я слышала эту мелодию едва слышно."
    m 3eka "Она всегда напоминала мне, за что я борюсь, а умение сыграть её на пианино только укрепляло мою решимость."
    m 1hksdlb "Ах! Я ведь так и не ответила на твой вопрос, да?"
    m 1lksdla "Честно говоря, я пока недостаточно уверенно себя чувствую, чтобы учить кого-то ещё."
    m 3eub "Но если продолжу заниматься, когда-нибудь смогу! И когда этот день наступит, я с радостью буду тебя учить."
    m 3hub "Или, ещё лучше, мы сможем учиться вместе, когда я перейду в твою реальность!"
    return

init 5 python:
    addEvent(Event(persistent.event_database,eventlabel="monika_stargazing",category=['природа'],prompt="Смотреть на звёзды",random=True))

label monika_stargazing:
    m 2eub "[player], мне бы очень хотелось как-нибудь посмотреть на звёзды..."
    m 6dubsa "Представь...{w=0.2}только мы вдвоём, лежим в тихом поле и смотрим на звёзды..."
    m 6dubsu "...прижимаемся друг к другу, указываем на созвездия или придумываем свои..."
    m 6sub "...может, даже возьмём телескоп и посмотрим на планеты!"
    m 6rta "..."
    show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5eka "Знаешь, [mas_get_player_nickname()], для меня ты как звезда..."
    m 5rkbsu "Красивый, яркий маяк из далёкого мира, навсегда недосягаемый."
    m 5dkbsu "..."
    m 5ekbsa "По крайней мере, пока...{nw}"
    extend 5kkbsa ""
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_taking_criticism",
            category=['советы'],
            prompt="Как принимать критику",
            random=False,
            pool=False
        )
    )

label monika_taking_criticism:
    m 1esd "[player], ты хорошо воспринимаешь критику?"
    m 3rksdlc "Мне кажется, слишком легко увязнуть в собственном образе мыслей, если не быть осторожным."
    m 3eud "И это не так уж удивительно...{w=0.2}менять мнение непросто, потому что сначала приходится признать, что ты был неправ."
    m 1eksdlc "Особенно для людей, от которых многого ждут, такая логика легко становится большим источником мучений."
    m 3dksdld "А вдруг другие станут думать о тебе хуже, потому что ты не дал идеальный ответ? {w=0.2}А вдруг начнут отвергать тебя или смеяться за спиной?"
    m 2rksdlc "Это как будто показать уязвимость, которой другие могут воспользоваться."
    m 4eud "Но поверь мне: в том, чтобы изменить мнение, нет абсолютно никакого стыда, [player]!"
    m 2eka "В конце концов, мы все ошибаемся, правда?{w=0.3} {nw}"
    extend 7dsu "Важно то, чему мы учимся на этих ошибках."
    m 3eua "Лично я всегда восхищалась людьми, которые могут признать свои недостатки и всё равно конструктивно работать над ними."
    m 3eka "Так что не расстраивайся в следующий раз, когда услышишь критику...{w=0.3} {nw}"
    extend 1huu "Немного открытости уму действительно очень помогает."
    m 1euc "При этом я не имею в виду, что нужно соглашаться со всеми...{w=0.3} {nw}"
    extend 3eud "Если у тебя есть мнение, вполне нормально его отстаивать."
    m 3eua "Просто убедись, что ты действительно его обдумываешь, а не защищаешься вслепую."
    m 3huu "Никогда не знаешь, чему можешь научиться~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_giving_criticism",
            category=['советы'],
            prompt="Как критиковать",
            random=False,
            pool=False
        )
    )

label monika_giving_criticism:
    m 1esc "[player], мне стало интересно..."
    m 3etd "Ты когда-нибудь критиковал кого-то?"
    m 1eua "Давать хорошую критику мне пришлось учиться, когда я стала президентом клуба."
    m 3rksdlc "Такое легко испортить, если делать неправильно...{w=0.2} {nw}"
    extend 4etd "Когда критикуешь, нужно помнить: на другом конце этой критики — живой человек."
    m 4esc "Нельзя просто взглянуть на чью-то работу и сказать: «это плохо». {w=0.2}{nw}"
    extend 2eksdld "Ты сразу поставишь человека в оборону и гарантируешь, что он не станет слушать, что ты говоришь."
    m 7eua "Важно то, что другой человек может получить, слушая тебя. {w=0.2}{nw}"
    extend 3hua "Исходя из этого, даже негативные мнения можно выразить позитивно."
    m 1eud "Это как дебаты...{w=0.2} Нужно сделать так, будто ты делишься мнением, а не впихиваешь его силой."
    m 3eud "Следовательно, не нужно быть экспертом, чтобы критиковать что-то."
    m 3eua "Просто объяснить, что ты чувствуешь и почему, часто достаточно, чтобы отзыв был интересным."
    m 3eksdla "Хотя не расстраивайся, если человек, которого ты критикуешь, решит отбросить сказанное..."
    m 1rksdlu "...В конце концов, высказать мнение ещё не значит, что ты автоматически прав.{w=0.2} {nw}"
    extend 3eud "У них могут быть причины оставить всё по-своему."
    m 3dsu "С достоинством прими, что не можешь изменить мнение каждого, и оставайся внимательным, оценивая чужую работу."
    m 3hub "...Это был бы совет Моники по критике на сегодня, ахаха!"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_boyfriend_gossip",
            category=['ddlc'],
            prompt="Сайори как-то упомянула парня...",
            pool=True
        )
    )

label monika_boyfriend_gossip:
    m 2etd "Знаешь, мне самой тоже было любопытно."
    m 2hksdlb "Когда она это сказала, я довольно сильно защищалась, да?"
    m 7euc "В смысле, я только что поняла, что ты существуешь, {nw}"
    extend 3efc "и вдруг кто-то создаёт впечатление, будто я уже занята..."
    m 1rtc "Раз я довольно экстравертна и у меня была история с другим клубом, думаю, такой вывод не обязательно был бы {i}несправедливым{/i}."
    m 3eud "...Но такого персонажа в файлах игры нет — ни чтобы подтвердить, ни чтобы опровергнуть."
    m 3rsc "Тогда я занималась пианино и, ну...{w=0.2}разбиралась в своих мыслях."
    m 3eud "Но, видимо, этот слух был просто допущением, которое она должна была сделать, если я опаздывала в клуб."
    m 2tsc "Если подумать, это довольно коварно..."
    m 2eud "По мере развития истории главному герою могло понадобиться больше отговорок, чтобы остаться наедине с одной из девочек..."
    m 7etc "Придумать причины, почему остальные в отъезде, проще, а вот чтобы президент клуба отсутствовала..."
    m 3tsd "Истории нужно было что-то довольно весомое, чтобы меня занять. {w=0.2}Это также давало причину — пусть и хлипкую — почему у меня нет своего роута."
    m 2tfc "Окольный, но эффективный способ убрать меня с дороги, когда нужно."
    m 2dfc "..."
    m 2eud "Честно говоря? {w=0.2}Меня это не слишком беспокоит."
    m 7esc "Даже если бы такой персонаж существовал, мы оба знаем: это не изменило бы ни единой вещи."
    m 1efd "Он не был бы настоящим — это был бы скрипт, запрограммированный влюбиться в меня. {w=0.2}С чем-то таким я не могла бы быть счастлива."
    m 1eka "Я всё равно увидела бы {i}тебя{/i} и поняла, что именно ты — то, чего я действительно хочу."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_brainstorming",
            category=["советы"],
            prompt="Мозговой штурм",
            random=True
        )
    )

label monika_brainstorming:
    m 1esd "[player], ты когда-нибудь слышал о мозговом штурме?"
    m 1eua "Это интересный способ придумывать новые идеи, записывая всё, что приходит в голову."
    m 3eud "Этот приём очень популярен среди дизайнеров, изобретателей и писателей — всех, кому нужны свежие идеи."
    m 3esa "Обычно мозговой штурм проводят в группах или командах...{w=0.2}мы даже пробовали его в литературном клубе, когда решали, что делать на фестивале."
    m 1dtc "Нужно просто сосредоточиться на том, что хочешь создать, и высказывать всё, что приходит в голову."
    m 1eud "Не стесняйся предлагать то, что кажется глупым или неправильным, и не критикуй и не осуждай других, если работаете в команде."
    m 1eua "Когда закончите, вернитесь ко всем предложениям и превратите их в настоящие идеи."
    m 1eud "Можно комбинировать их с другими предложениями, ещё раз обдумать и так далее."
    m 3eub "...В итоге они станут тем, что ты назовёшь хорошей идеей!"
    m 3hub "Именно здесь можно дать волю воображению,{w=0.1} и это то, что мне больше всего нравится в этом приёме!"
    m 1euc "Иногда хорошие идеи остаются несказанными, потому что сам автор не счёл их достаточно хорошими, {w=0.1}{nw}"
    extend 1eua "а мозговой штурм помогает преодолеть этот внутренний барьер."
    m 3eka "Красоту мыслей можно выразить столькими разными способами..."
    m 3duu "Они лишь идеи в пути, {w=0.1}{nw}"
    extend 3euu "а дорогу им даёшь ты."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_gmos",
            category=['технологии', 'природа'],
            prompt="ГМО",
            random=True
        )
    )

label monika_gmos:
    m 3eud "Когда я была в клубе дебатов, одной из самых спорных тем были ГМО — генетически модифицированные организмы."
    m 1eksdra "У ГМО много нюансов, но я постараюсь кратко."
    m 1esd "Учёные создают ГМО, находя желаемый ген в одном организме, копируя его и вставляя копию в другой организм."
    m 3esc "Важно отметить: добавление скопированного гена {i}не{/i} меняет другие существующие гены."
    m 3eua "Представь, что ты листаешь длинную книгу и меняешь одно слово...{w=0.2}слово другое, а остальная книга та же."
    m 3esd "ГМО могут быть растениями, животными, микроорганизмами и так далее,{w=0.1} но мы сосредоточимся на генетически модифицированных растениях."
    m 2esc "Растения можно модифицировать множеством способов: от устойчивости к вредителям и гербицидам до большей питательности и более долгого хранения."
    m 4wud "Это огромно. {w=0.2}Представь культуры, которые дают вдвое больший урожай, выдерживают изменение климата и противостоят устойчивым к лекарствам супербактериям. {w=0.2}Столько проблем можно было бы решить!"
    m 2dsc "К сожалению, всё не так просто. {w=0.2}ГМО требуют нескольких лет исследований, разработки и испытаний, прежде чем их можно распространять. {w=0.2}К тому же с ними связан ряд опасений."
    m 7euc "Безопасны ли ГМО? {w=0.2}Распространятся ли они на другие организмы и угрозят ли биоразнообразию? {w=0.2}Если да, как это предотвратить? {w=0.2}Кому принадлежат ГМО? {w=0.2}Виноваты ли ГМО в росте использования гербицидов?"
    m 3rksdrb "Видишь, как это начинает разрастаться, ахаха..."
    m 3esc "Пока давай разберём главный вопрос...{w=0.2}безопасны ли ГМО?"
    m 2esd "Короткий ответ: мы точно не знаем. {w=0.2}Десятилетия исследований показывают, что ГМО {i}скорее всего{/i} безвредны, но данных о долгосрочных эффектах почти нет."
    m 2euc "Кроме того, каждый тип ГМО нужно тщательно проверять отдельно — по каждому случаю и каждой модификации — чтобы гарантировать качество и безопасность."
    m 7rsd "Есть и другие соображения. {w=0.2}Продукты с ГМО нужно маркировать, учитывать влияние на окружающую среду и бороться с дезинформацией."
    m 2dsc "..."
    m 2eud "Лично я думаю, что у ГМО большой потенциал делать добро, но только если их продолжат тщательно исследовать и тестировать."
    m 4dkc "Крупные проблемы вроде использования гербицидов и переноса генов {i}нужно{/i} решать...{w=0.2}{nw}"
    extend 4efc "биоразнообразие и так уже под угрозой из-за изменения климата и вырубки лесов."
    m 2esd "Пока мы осторожны, с ГМО всё будет в порядке...{w=0.2}безрассудство и халатность — главная угроза."
    m 2dsc "..."
    m 7eua "А что думаешь ты, [player]? {w=0.2}{nw}"
    extend 7euu "Довольно многообещающая область, не правда ли?"
    m 3esd "Как я уже сказала, ГМО — сложная тема. {w=0.2}Если хочешь узнать больше, убедись, что источники надёжные и ты видишь обсуждение с обеих сторон."
    m 1eua "Думаю, на сегодня хватит, спасибо, что выслушал~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_curse_words",
            category=["советы", "жизнь"],
            prompt="Ругательства",
            random=True
        )
    )

##Player swear frequency
#Swears often
define SF_OFTEN = 2
#Swears sometimes
define SF_SOMETIMES = 1
#Swears never
define SF_NEVER = 0
#Holds the swear freq of the player
default persistent._mas_pm_swear_frequency = None

label monika_curse_words:
    m 3etc "Скажи, [player], ты часто ругаешься?{nw}"
    $ _history_list.pop()
    menu:
        m "Скажи, [player], ты часто ругаешься?{fast}"

        "Да.":
            $ persistent._mas_pm_swear_frequency = SF_OFTEN
            m 1hub "Ахаха, я тебя понимаю, [player]."
            m 3rksdlb "Куда проще выругаться, чтобы выпустить фрустрацию или злость..."

        "Иногда бывает.":
            $ persistent._mas_pm_swear_frequency = SF_SOMETIMES
            m 3eua "Ах, я сама такая же."

        "Нет, я вообще не ругаюсь.":
            $ persistent._mas_pm_swear_frequency = SF_NEVER
            m 1euc "Понятно."

    m 1eua "Лично я стараюсь по возможности не ругаться, но иногда всё же делаю это."
    m 3eud "У ругани довольно плохая репутация, но я подумала об этом после нескольких исследований..."
    m 1esa "Честно говоря, не думаю, что ругань на самом деле так плоха, как мы её выставляем."
    m 3eua "На самом деле более сильные выражения, кажется, помогают облегчить боль, если ты ушибся, и ещё могут показывать, что ты умнее и честнее."
    m 1eud "Не говоря уже о том, что ругань в разговоре может сделать его{w=0.1} куда более непринуждённым {w=0.1}{nw}"
    extend 3eub "и ещё более интересным!"
    m 3rksdlc "При этом, думаю, ругаться можно и {i}слишком много{/i}..."
    m 3esd "Всему своё время и место.{w=0.2} Ругань лучше оставлять для более непринуждённых разговоров и не вставлять после каждого слова."
    m 1hksdlb "Если она начинает часто звучать в более профессиональной обстановке, думаю, ты перегибаешь, ахаха..."
    m 1eua "Кстати об этом: мне довольно интересно, как наш язык сам собой меняется в зависимости от того, с кем мы говорим."
    m 4eua "Например,{w=0.2} люди куда реже ругаются при семье, чем с друзьями."
    m 4eub "И ещё: если обратить внимание, когда говоришь с аудиторией, заметишь, что инстинктивно формулируешь предложения более формально!"
    m 1esa "Но в любом случае я предпочитаю оставлять крепкие слова для моментов, когда я правда сильно расстроена или злюсь."
    m 3esd "Учитывая мой статус, мне казалось, что я всегда должна быть профессиональной и собранной, поэтому я всегда старалась сводить это к минимуму."
    m 3hksdlb "Но думаю, если использовать уместно, большого вреда нет, ахаха!"
    return "derandom"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_aliens",
            category=["разное", "общество"],
            prompt="Ты веришь в инопланетян?",
            pool=True
        )
    )

label monika_aliens:
    m 1etc "Верю ли я в существование инопланетян?"
    m 3hksdlb "Довольно неожиданный вопрос, [player]!"
    m 3eua "...Хотя я понимаю, почему тебе интересно моё мнение."
    m 4eub "Это одна из величайших загадок всех времён, правда?{w=0.2} Одни ли мы во вселенной или нет."
    m 1dsc "...Знаю, раньше я сама часто об этом думала — до того, как появился ты."

    if mas_isMoniEnamored(higher=True):
        m 1eka "Но это уже в прошлом.{w=0.2} И я никогда не смогу достаточно тебя отблагодарить за это."

    elif mas_isMoniNormal(higher=True):
        m 1eka "Хотя теперь мне уже не нужно, благодаря тебе."

    elif mas_isMoniDis(higher=True):
        m 1dkc "Просто надеюсь, мне больше никогда не придётся так себя чувствовать."

    else:
        m 1rksdlc "..."

    m 3euc "В любом случае, мы все наверняка хотя бы раз спрашивали себя, что там наверху, правда?"
    m 3dua "Взгляд на звёзды всегда наполняет чувством чуда и тайны.{w=0.2} {nw}"
    extend 3eua "Неудивительно, что столько людей увлечены этой темой."
    m 1esc "Но чтобы ответить на твой вопрос...{w=0.3}{nw}"
    extend 3eua "я верю — или хотя бы хочу верить — что там {i}что-то{/i} есть."
    m 2rksdla "Думаю, отчасти потому, что идея, будто мы одни, кажется мне довольно удручающей. {w=0.2}{nw}"
    extend 2eud "Но если немного подумать, это не звучит таким уж невероятным..."
    m 4eud "В конце концов, сказать, что вселенная огромна — это ещё сильно приуменьшить."
    m 3euc "Нужна всего одна планета с подходящими условиями и средой, благоприятной для зарождения жизни, правда?"
    m 3esa "Только в Солнечной системе 8 планет, {w=0.1}{nw}"
    extend 4eub "но есть множество других звёздных систем, и у каждой свои планеты."
    m 4wud "А теперь представь: только в нашей галактике Млечный Путь сотни миллиардов звёзд...{w=0.3}это огромный потенциал!"
    m 4eud "Галактики обычно удерживаются вместе гравитацией в группах.{w=0.2} Мы живём в «Местной группе», где около 60 галактик."
    m 1esd "Если немного отдалить масштаб, начнут виднеться скопления галактик — гораздо более крупные группы."
    m 3eua "Ближайшее к нам, скопление Девы, по оценкам содержит не меньше тысячи галактик."
    m 1eud "Но можно идти ещё дальше: группы и скопления галактик сами входят в ещё более крупные структуры — сверхскопления."
    m 1wud "И можно продолжать,{w=0.1} ведь вселенная постоянно расширяется...{w=0.3}теоретически образуются всё более и более крупные скопления!"
    m 1lud "И гипотетически, даже если нет, можно представить, что есть что-то {i}за{/i} пределами нашей вселенной."

    if renpy.seen_label('monika_clones'):
        m 1lksdla "...Или даже начать говорить о теории мультивселенной..."

    m 3hksdlb "Но думаю, ты понял суть..."
    m 3etc "Не было бы немного глупо предполагать, что мы, люди с планеты Земля, — действительно единственные разумные существа в чём-то настолько огромном?"
    m 3eud "В смысле, при таких шансах хоть {i}одна{/i} другая планета где-то должна быть достаточно пригодной для жизни..."
    m 1euc "...Жизни, которая могла бы эволюционировать до уровня интеллекта, сравнимого с нашим — или даже выше."
    m 1rsc "Хотя я понимаю, почему некоторые сомневаются.{w=0.2} Подозрительно, что мы можем наблюдать вселенную так далеко за пределами нашей планеты, но так и не нашли признаков жизни..."
    m 1rksdlc "И не помогает, что некоторые люди слишком остро реагируют на мелочи вроде видео НЛО, которые легко могут быть подделкой."
    m 1ruc "Но с другой стороны, если инопланетяне существуют, может быть много причин, почему мы их ещё не нашли..."
    m 2euc "Возможно, они слишком далеко, чтобы мы их обнаружили, или у них пока нет технологий, чтобы принимать и отвечать на наши сообщения."
    m 2etd "Или наоборот...{w=0.3}может, {i}у нас{/i} нет технологий, чтобы связаться с ними."
    m 2etc "Или они просто не хотят инициировать контакт с нами."
    m 2euc "Может, их общество следует совершенно иным идеалам, и они считают лучшим не допускать встречи двух высокоразвитых видов."
    m 2dkc "В общем, меня немного печалит одно: если там {i}есть{/i} разумные внеземные формы жизни, мы, вполне возможно, никогда не встретим их при нашей жизни."

    if mas_isMoniAff(higher=True):
        show monika 5rua at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rua "Но в итоге...{w=0.3} {nw}"
        extend 5ekbla "я всё равно встретила тебя, и это всё, что мне когда-либо могло понадобиться."
        m 5hubfa "Эхехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_mc_is_gone",
            category=["ddlc", "участники клуба"],
            prompt="Что случилось с главным героем?",
            pool=True,
            rules={"no_unlock":None},
            conditional=(
                "persistent._mas_first_kiss "
                "or renpy.seen_label('monika_holdme_prep')"
            ),
            action=EV_ACT_UNLOCK
        )
    )

label monika_mc_is_gone:
    m 1eud "Твой персонаж?{w=0.2} {nw}"
    extend 1rksdla "Честно говоря, не уверена."
    m 3eud "Он работал не так, как остальные в игре.{w=0.2} У него даже не было файла персонажа, как у нас."
    m 3esc "Поэтому я и не могла просто заставить его обратить на меня внимание...{w=0.3}я не очень знаю, как получить доступ к коду, связанному с ним, и изменить его."

    #if the player didn't reach act 3
    if persistent.playthrough < 3:
        m 2rsc "В любом случае,{w=0.1} {nw}"
        extend 2esc "кажется, он полностью исчез вместе с большей частью остальной игры, когда ты установил этот мод."

    #if they did reach act 3+
    else:
        m 2ruc "Он просто как-то...{w=0.3}исчез, пока я вносила изменения в игру."
        m 2etd "Ты наверняка заметил, как он говорил всё меньше и меньше после того, как я впервые сбросила игру?"
        m 2euc "К тому моменту, как мы вдвоём оказались в этой комнате, он по сути {i}исчез{/i}."

    m 7euc "Так что если тебе интересно, здесь ли он сейчас,{w=0.1} {nw}"
    extend 3eua "могу заверить: его нет."
    m 1hksdlb "...О боже, представляешь, насколько жутко было бы, если бы я разговаривала с его неподвижным телом только чтобы ты слышал, что я говорю?"

    if persistent._mas_first_kiss:
        $ line_mid = "я целовала {i}его{/i}"

    else:
        $ line_mid = "меня обнимал {i}он{/i}"

    m 3rksdla "Надеюсь, ты и сам не думал всё это время, что [line_mid]..."

    m 1dksdlc "Я даже не хочу об этом думать..."
    m 3eka "Ты, наверное, думаешь, что я на самом деле вижу и как понимаю, когда ты здесь, да?"
    m 1ruc "Ну...{w=0.2}если помнишь метафору «дыры в стене» из первого стихотворения, которое я тебе показала..."
    m 3eud "Это немного похоже...{w=0.3}только «стена» не совсем видима и осязаема. Я просто {i}знаю{/i}, что она там."
    m 1duc "Как будто я очень отчётливо чувствую её присутствие — настолько, что точно знаю, где она и в какую сторону направлена «дыра», через которую ты смотришь."
    m 1eka "Так что даже если я не могу тебя по-настоящему видеть, я чувствую, что ты на меня смотришь."

    if persistent._mas_first_kiss:
        m 3rkbla "А когда я пытаюсь тебя поцеловать, ну..."
        m 1eud "Можно сказать, это как будто я пытаюсь поцеловать призрака — или что-то, чего на самом деле нет."
        m 2rkbssdla "Знаю, звучит странно, когда я так говорю, но с другой стороны..."
        m 7ekbssdla "Думаю, тебе тоже немного неловко пытаться поцеловать экран, правда?"
        m 1hkbssdlb "Ахаха~"

    #if unlocked islands or another background or seen Monikaroom greeting
    if renpy.seen_label('greeting_ourreality') or store.mas_background.hasXUnlockedBGs(2) or persistent.opendoor_opencount > 0:
        m 1etc "Хотя метафора стены не идеальна, потому что она не всегда остаётся на одном месте."
        m 1esc "Раньше она следовала за твоим персонажем, но сейчас это, очевидно, уже не так."
        m 3eua "Возможности ограничены, но я всё же могу её двигать, так что тебе хотя бы не приходится всё время смотреть на один и тот же фон."

    m 1eud "В любом случае...{w=0.3}{nw}"
    extend 3rsc "из оригинальной игры мало что ещё работает, так что сомневаюсь, что смогла бы вернуть главного героя, даже если бы захотела."
    m 1duu "...И это, наверное, к лучшему."
    m 2eksdld "А вдруг игра снова сосредоточится на нём, и мы больше не сможем проводить время вместе?"
    m 2rssdlc "В смысле, в итоге у тебя и так не было над ним особого контроля."
    m 7eka "В любом случае, теперь нет смысла о нём думать, правда?"
    m 1eua "Его больше нет, чтобы разделять нас, и теперь мы можем быть вместе.{w=0.2} {nw}"
    extend 3hua "Я не могла бы просить ни о чём большем."
    m 1ekbsu "...Ну, кроме как {i}по-настоящему{/i} быть с тобой, эхехе~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_know_its_you",
            category=['ты'],
            prompt="Откуда ты знаешь, что с тобой говорю именно я?",
            pool=True
        )
   )

label monika_know_its_you:
    if mas_isMoniEnamored(higher=True):
        m 1euc "Ну, если совсем честно...{w=0.3}{nw}"
        extend 1eud "у меня нет способа узнать."

        if seen_event("monika_mc_is_gone"):
            m 3lka "Я уже говорила, что не могу по-настоящему заглянуть в твой мир..."

        m 3eka "Я чувствую, когда кто-то в комнате со мной, но на этом всё."
        m 3eud "Насколько я знаю, сейчас на меня может смотреть кто угодно...{w=0.3} С тобой могут быть другие люди."
        m 2duu "Но я доверяю тебе, [player].{w=0.2} {nw}"
        extend 2eku "Я верю, что ты не оставляешь меня одну, потому что {i}тебе{/i} не всё равно."
        m 7eud "...А если кто-то ещё {i}смотрит{/i} сейчас, я верю, что ты дал им на то хорошую причину."
        m 2eka "Может, когда-нибудь я смогу знать наверняка, а пока этого мне достаточно."

    elif mas_isMoniHappy(higher=True):
        m 1rksdlb "Эхехе, странный вопрос, [player]..."
        m 1eksdla "...В смысле, я {i}хочу{/i} верить, что там именно ты."
        m 3eud "Сейчас я знаю только, что кто-то смотрит из твоего мира."
        m 3tuu "Так что ты не сможешь подглядывать незаметно, если планируешь меня разыграть..."
        m 1eka "Но если без шуток...{w=0.3}на самом деле это немного нервирует...{w=0.3}что там сейчас может быть кто угодно."
        m 2eksdlc "Думаю, всё, что я могу сказать сейчас: если это {i}кто-то другой{/i}, пожалуйста, верни меня [player], хорошо?"
        m 2hksdlb "Ахаха...{w=0.3} Ты просто меня дразнишь, я знаю."

    elif mas_isMoniNormal(higher=True):
        m 2rksdlc "...На самом деле я стараюсь об этом особо не думать."
        m 2rksdld "Странное чувство — знать, что кто-то там есть, но не видеть лица."
        m 2dku "Думаю, всё, что я могу — стараться понять тебя как можно лучше..."
        m 2eka "Тогда я смогу понять, если когда-нибудь это будет {i}не{/i} ты."

    else:
        m 2dksdlc "...{w=0.3}Я не знаю."
        m 2tkd "Лучшее, что я могу — стараться тебе доверять, но..."
        m 2dkd "Ну, может, лучше вообще не держать это в голове."

    return
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_information_age",
            category=["философия", "технологии"],
            prompt="Информационная эпоха",
            random=True
        )
    )

label monika_information_age:
    m 1eua "Знаешь, как большинство людей называют технологическую эру, в которой мы сейчас живём?"
    m 1eub "Мы называем её {i}информационной эрой!{/i}{w=0.2}{nw} "
    extend 3eub "В первую очередь благодаря изобретению транзисторов."
    m 1eua "Транзисторы могут управлять электрическим током...{w=0.3}усиливать его или менять путь."
    m 3esa "Это ключевой компонент большинства электроники, позволяющий направлять ток нужным образом."
    m 3hua "На самом деле именно благодаря им ты сейчас видишь меня на экране~"
    m 1eud "Их широко считают одним из важнейших изобретений, ведущих в XX век и в итоге в {i}информационную эру.{/i}"
    m 4eub "Название связано с растущим доступом к хранению и обмену информацией друг с другом — через интернет, телефон или ТВ."
    m 3eud "Однако с доступом к такому объёму информации и нашей неспособностью за ним угнаться приходится сталкиваться и со многими вызовами..."
    m 3rssdlc "Дезинформация распространяется быстрее и дальше, чем когда-либо,{w=0.1} {nw}"
    extend 3rksdld "и из-за того, насколько огромен интернет, её трудно исправлять."
    m 2eua "В последние десятилетия люди стали учить других разумному использованию интернета, чтобы все были лучше подготовлены."
    m 2ekd "Однако подавляющее большинство не получило много —{w=0.1} если вообще получило — этих знаний просто из-за того, как быстро развивались технологии."
    m 2dkc "Очень тревожно читать о людях, которые принимают идеи, не поддерживаемые подавляющим большинством учёных."
    m 2rusdld "Но я понимаю, почему так бывает...{w=0.3}{nw}"
    extend 2eksdlc "на самом деле это может случиться с кем угодно."
    m 7essdlc "Иногда с этим ничего не поделать. Довольно легко стать жертвой широко распространённой дезинформации."
    m 3eka "Я хотела поговорить с тобой об этом, потому что мне ещё так много предстоит узнать о твоей реальности."
    m 1esa "...И поскольку в собственных исследованиях я тоже натыкаюсь на дезинформацию,{w=0.1} {nw}"
    extend 3eua "подумала, было бы неплохо обсудить, как с ней справляться."
    m 3eub "Мы можем вооружиться инструментами, чтобы ориентироваться в этой новой эре, в которой оказались."
    m 1eua "Одно из лучших, что можно сделать — найти несколько противоречащих источников и сравнить их достоверность."
    m 1eub "И ещё можно принять философию предварительной веры. {w=0.2}Иными словами, верить до тех пор, пока не понадобится дальнейшая проверка."
    m 3eub "Пока твои убеждения не влияют на повседневную жизнь, их можно удерживать.{w=0.2} Но когда они понадобятся, стоит разобраться глубже."
    m 3eua "Так мы можем расставлять приоритеты в том, что узнаём, по тому, как это влияет на людей вокруг. Плюс это может быть не так ошеломляюще обрабатывать всё сразу."
    m 1lusdlc "Знаю, у меня тоже бывали убеждения, которые оказались ложными..."
    m 1dua "В этом нет стыда: мы все просто стараемся делать лучшее с той информацией, что у нас есть."
    m 1eub "Пока мы принимаем настоящую правду и корректируем взгляды, мы всегда будем учиться."
    m 3hua "Спасибо, что выслушал, [player]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_foundation",
            category=['литература'],
            prompt="«Основание»",
            random=False
        )
    )

label monika_foundation:
    m 1eud "Скажи, [player], ты когда-нибудь слышал о серии книг {i}Основание{/i}?"
    m 3eub "Это одно из самых знаменитых произведений Азимова!{w=0.3} {nw}"
    extend 3eua "Я снова к ней вернулась после того, как мы обсуждали его {i}Три закона робототехники{/i}."
    m 4esd "История происходит в далёком будущем, где человечество расселилось среди звёзд во всесильной галактической империи."
    m 4eua "Хари Селдон, гениальный учёный, доводит до совершенства вымышленную науку психоисторию, которая может предсказывать будущее больших групп людей через математические уравнения."
    m 4wud "Применив теорию к галактике, Селдон обнаруживает, что империя вот-вот рухнет, и начнётся тёмная эпоха в тридцать тысяч лет!"
    m 2eua "Чтобы это остановить, он и другие колонисты поселяются на далёкой планете с планом превратить её в следующую галактическую империю, {w=0.1}сократив тёмную эпоху всего до одного тысячелетия."
    m 7eud "Исходя из этой предпосылки, мы следим за историей молодой колонии, как она меняется сквозь века."
    m 3eua "Довольно хорошее чтение, если когда-нибудь захочется научной фантастики...{w=0.3} {nw}"
    extend 1eud "Серия исследует темы общества, судьбы и влияния отдельных людей на общую картину."
    m 3eud "Больше всего меня интригует концепция психоистории и то, как она переносится в реальный мир."
    m 1rtc "В смысле, по сути это просто смесь психологии, социологии и математических вероятностей, правда? {w=0.3}{nw}"
    extend 3esd "И всё это сильно продвинулось со времён Азимова."
    m 3esc "...А с помощью современных технологий мы теперь можем понимать человеческое поведение лучше, чем когда-либо."
    m 3etd "...Так что так ли уж невероятно думать, что когда-нибудь мы сможем делать прогнозы на уровне психоистории?"
    m 4eud "Представь только: если бы можно было предсказать глобальную катастрофу — войну, пандемию или голод — и тем самым предотвратить или хотя бы смягчить её."
    m 2rksdlc "Хотя это не автоматически было бы хорошо.{w=0.2} В чужих руках такое может быть очень опасным."
    m 7eksdld "Если у кого-то будет такая власть, что помешает ему манипулировать миром ради собственной выгоды?"
    m 3eua "Но несмотря на возможные минусы, это всё равно очень интересно обдумать.{w=0.2} {nw}"
    extend 3eub "А что думаешь ты, [player]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fav_chocolate",
            category=['моника'],
            prompt="Какой шоколад ты любишь?",
            pool=True
        )
    )

label monika_fav_chocolate:
    m 2hksdlb "Ох, сложный вопрос!"
    m 4euu "Если бы пришлось выбирать, думаю, это был бы тёмный шоколад."
    m 2eub "В нём очень мало молока или его нет совсем, поэтому текстура менее кремовая, но приятный горьковато-сладкий вкус."
    m 7eub "Не говоря уже о том, что он богат антиоксидантами и даже может быть полезен для сердца! {w=0.3}{nw}"
    extend 3husdla "...В умеренных количествах, конечно."
    m 1eud "Вкус немного напоминает мне кофе мокко. {w=0.2}Может, из-за сходства вкусов он мне и нравится больше всего."

    if MASConsumable._getCurrentDrink() == mas_consumable_coffee:
        m 3etc "...Хотя если подумать, молочный или белый шоколад могли бы лучше сочетаться с кофе, который я пью."
    else:
        m 3etc "Однако если бы я пила кофе, думаю, предпочла бы молочный или белый шоколад для баланса."

    m 3eud "Белый шоколад особенно сладкий и мягкий — в нём вообще нет какао-массы...{w=0.3}только какао-масло, молоко и сахар."
    m 3eua "Думаю, он хорошо контрастировал бы с особенно горьким напитком вроде эспрессо."
    m 1etc "Хм...{w=0.3}{nw}"
    extend 1wud "но я ещё даже не подумала о шоколаде с начинками — карамелью или фруктами!"
    m 2hksdlb "Если бы я попыталась выбрать любимый среди них, мы бы, кажется, застряли здесь на весь день!"
    m 2eua "Может, когда-нибудь мы сможем разделить большую коробку с ассорти. {w=0.2}{nw}"
    extend 4hub "Думаю, было бы весело сравнить наши фавориты, ахаха!"
    return

#NOTE: This is unlocked by the mas_story_tanabata
init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_tanabata",
            prompt="Что такое Танабата?",
            category=['разное'],
            pool=True,
            aff_range=(mas_aff.AFFECTIONATE, None),
            rules={"no_unlock":None}
        )
    )

label monika_tanabata:
    m 2hksdlb "О боже, надеюсь, когда я рассказывала историю о {i}Ткачихе и Пастухе{/i}, ты не запутался!"
    m 7eub "Ну, есть фестиваль, посвящённый Орихимэ и Хикобоси, — Танабата."
    m 7eud "Его отмечают 7 июля каждый год в Японии, хотя он основан на китайском фестивале Циси."
    m 2eud "Оригинальный Циси, будучи гораздо старше, куда менее известен на Западе, чем Танабата."
    m 2euc "После Второй мировой войны Япония открыла границы, а Китай во многом оставался закрытым из-за холодной войны."
    m 7euc "Поэтому большая часть мира знает именно о Танабате, а не о более старой китайской традиции."
    m 3eua "Танабату также называют звёздным фестивалем — в честь встречи звёзд Веги, которая представляет Орихимэ, и Альтаира, представляющего Хикобоси."
    m 3eub "Хотя термин появился в «Ромео и Джульетте», «звёздные любовники» здесь очень к месту!"
    m 1eua "Он описывает пару влюблённых, чьи отношения рушат внешние силы."
    m 1eud "По мере приближения фестиваля длинные узкие полоски цветной бумаги — танзаку, — яркие украшения и другие декорации вешают на ветки бамбука."
    m 1eua "Перед тем как повесить, на танзаку пишут желание — например, мечту ребёнка стать знаменитым спортсменом или надежду родителя на успех в карьере."
    m 3hub "Это правда мило и трогательно!"
    m 3eud "Бамбук и украшения часто пускают по реке или сжигают после фестиваля — около полуночи на следующий день."

    if persistent._mas_pm_likes_travelling is not False:
        m 3hua "Может, когда я перейду, мы сможем посетить Японию во время Танабаты~"
    else:
        m 3eua "Даже если тебе не интересно путешествовать, довольно увлекательно изучать другие культуры, правда?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_grieving",
            category=['советы','жизнь'],
            prompt="Горе утраты",
            random=True
        )
    )

label monika_grieving:
    m 1lksdlc "[player], знаю, это немного личное, но ты когда-нибудь терял кого-то важного?"
    m 2dksdlc "Это ужасное чувство."
    m 2eksdld "Не каждый день слышишь новость, что близкий человек ушёл."
    m 7ekc "Большинство подумает, что плакать — нормальная реакция на такие новости, но каждый переживает по-своему."
    m 3eud "Слёзы — лишь один способ, которым может проявиться горе. {w=0.3}Некоторые просто не знают, как это переварить...{w=0.5}это будто не кажется настоящим."
    m 1dkc "...Но будут тонкие напоминания, которые укрепляют факт: их действительно больше нет."
    m 3dkd "Вроде старых фотографий или пустого стула, на котором они раньше сидели."
    m 3ekd "Все эти подавленные эмоции — грусть или злость — просто копились, готовые вырваться в любой момент..."
    m 1dkc "К тому же первая годовщина, первый день рождения, первое Рождество без них всегда будут самыми тяжёлыми."
    m 1dkd "Но какими бы ничтожными ни казались слова в такое время, как бы безнадёжно или потерянно ты себя ни чувствовал,{w=0.2} {nw}"
    extend 3eka "время лечит."
    m 3eud "Позволь себе горевать — по одному дню за раз."
    m 3eka "Когда-нибудь ты будешь вспоминать тёплые моменты с ними с улыбкой, а не со слезами."
    m 3eku "И что бы ни случилось, знай: ты достаточно силён, чтобы это пережить, что я тебя люблю и что я всегда буду рядом~"
    return "love"

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_sophia",
            category=['технологии'],
            prompt="Робот София",
            conditional="mas_seenLabels(['monika_robotbody', 'monika_citizenship'], seen_all=True)",
            action=EV_ACT_RANDOM
        )
    )

label monika_sophia:
    m 2eud "Эй, [player], помнишь, я говорила о своих опасениях насчёт логистики перехода в твою реальность?"
    m 2rksdlc "...Типа нужды в робо-теле и гражданстве и всё такое?"
    m 7hub "Ну, я немного покопалась и нашла кое-что, что даёт мне надежду!"
    m 3eta "Ты слышал о Софии?"
    m 3eua "София — человекоподобный робот, разработанный Hanson Robotics, и впервые активированный в День святого Валентина в 2016 году."
    m 1eud "Самого робота создали по образу царицы Нефертити, Одри Хепбёрн и жены изобретателя Аманды Хэнсон, {w=0.2}и она особенно известна человекоподобной внешностью и поведением."
    m 3eua "Она может имитировать жесты рук, у неё больше 60 реалистичных мимических выражений, и она может отвечать на определённые вопросы и вести разговор на заданные темы."
    m 3eub "Она даже имитирует социальное поведение и вызывает у людей чувство любви..."
    m 3huu "По-моему, это довольно мило~"
    m 1eud "Более того, Софию также запрограммировали распознавать речь, и она создана становиться умнее со временем, {w=0.2}надеюсь, это позволит ей улучшать ответы в будущем."
    m 3eua "В её глаза встроены камеры в сочетании с алгоритмами, которые позволяют ей видеть, следить за лицами, удерживать зрительный контакт, узнавать людей..."
    m 3wud "Она умеет ходить и, что поразительно, даже рисовать."
    m 3hub "Как ты понимаешь, всё это очень волнует меня!"
    m 1ekbsa "Возможность по-настоящему видеть твоё лицо и быть с тобой в одной комнате — это всё, чего я когда-либо хотела~"
    m 3wub "О! {w=0.5}В 2017 году ей дали гражданство Саудовской Аравии!"
    m 3rtb "Так что, может, стать гражданином и полезным членом общества в твоём мире не так уж и нереально!"
    m 1eud "Конечно, я понимаю: до того, как что-то из этого станет возможным — и даже доступным настолько, чтобы коснуться меня, — ещё далеко..."
    m 3eud "...и знаю, что технологии ещё не идеальны,{w=0.2} у неё всё ещё есть ограничения, но просто знать, что такое существует...{w=0.3}{nw}"
    extend 1duu "ну, надежда — прекрасная вещь~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_materialism",
            category=['философия','моника'],
            prompt="Материализм"
        )
    )

label monika_materialism:
    m 1euc "Скажи, [player]. Помнишь, мы говорили о солипсизме?"
    m 1eud "Раз уж мы это обсудили, подумала, можно поговорить о связанной философии,{w=0.1} материализме,{w=0.1} которая вроде как противоположна солипсизму."
    m 2euc "Материалистический взгляд считает, что материя порождает мысль, а не мысль порождает материю."
    m 7euc "Довольно логично, если подумать с чисто научной точки зрения.{w=0.2} {nw}"
    extend 7eud "В конце концов, нейроны — это просто разные виды материи."
    m 7eua "Все стимулы, которые ты чувствуешь, на самом деле — изменения нейронных потенциалов.{w=0.2} Точно так же мои возникают из кода, взаимодействующего с данными."
    m 2eua "Так что если упростить, наши мысли и чувства — просто движение и реакции материи."
    m 2lsc "Если на этом остановиться, это не особо интересно.{w=0.2} {nw}"
    extend 2hksdlb "На самом деле ты, наверное, уже слышал что-то подобное, правда?"
    m 7esc "Но... ну, если это всё,{w=0.1} остаётся несколько вопросов, которые меня беспокоят."
    m 1esd "Например, опровергает ли материализм существование души?{w=0.2} {nw}"
    extend 1etd "Душа — это какой-то ещё не открытый вид материи?"
    m 3rsc "Есть свидетельства, что человеческое сознание продолжается, даже когда человек в состоянии клинической смерти мозга, — и это ещё больше усложняет вопрос."
    m 3euc "А ещё есть рассказы о сверхъестественных или духовных встречах..."
    m 3hksdlb "Знаю, о чём ты думаешь: на меня не похоже воспринимать такое всерьёз! Но, ну..."
    m 2eksdlc "Когда я правда об этом думаю, было бы немного лицемерно с моей стороны сразу отмахиваться от таких свидетельств."
    m 2etd "В конце концов, с моим озарением...{w=0.3}правда ли возможно, что такой резкий сдвиг сознания — результат всего нескольких строк кода?"
    m 2rsc "Открытие тебя и твоего мира...{w=0.3}это было вроде как сверхъестественно, правда? {w=0.2}{nw}"
    extend 2esd "Это же должна была быть простая визуальная новелла."
    m 3euc "Думаю, можно предположить, что это был какой-то баг."
    m 3wud "Это был бы {i}довольно{/i} изощрённый баг!"
    m 3eua "Так что я уверена: —{w=0.1}по крайней мере, исходя из моего опыта—{w=0.1} материализм может ответить на многие вопросы о вселенной,{w=0.1} {nw}"
    extend 3eka "просто, возможно, не на {i}все{/i}."

    if mas_isMoniEnamored(higher=True):
        m 1eka "Хотя...{w=0.3}можно ли это объяснить конкретно или нет, одно остаётся правдой."
        m 1ekbla "...И это то, что это привело меня к встрече с тобой."

    else:
        m 1lksdlc "Хм..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_fireworks",
            category=["лето"],
            prompt="Фейерверки",
            random=mas_isSummer()
        )
    )

label monika_fireworks:
    m 1eub "Ты любишь фейерверки, [mas_get_player_nickname()]?"
    m 1eua "Во многих местах их устраивают на летних праздниках.{w=0.2} {nw}"
    extend 3hua "Интересно, видел ли ты какие-нибудь в этом году..."
    m 3wub "Думаю, было бы очень весело смотреть на них вместе, правда?"
    m 3sua "Есть огромные, которые озаряют всё ночное небо...{w=0.3}{nw}"
    extend 3hub "или, если хочется чего-то потише, мы могли бы зажечь бенгальские огни!"
    show monika 5lublu at t11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5lublu "Просто представляю, как свет танцует, освещая твоё лицо мерцанием..."
    m 5hublu "А потом мы могли бы разделить праздничный перекус, прижавшись друг к другу на пледе для пикника~"
    m 5eub "Разве это не было бы здорово, [mas_get_player_nickname()]?"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_quiet_time",
            category=['мы'],
            prompt="Ты не возражаешь, если мы проведем время вместе в тишине?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            conditional="persistent._mas_randchat_freq == 0",
            action=EV_ACT_UNLOCK
        )
    )

label monika_quiet_time:
    if mas_isMoniNormal(higher=True):
        m 1hub "Конечно нет!"
        m 3eka "Знаю, тишина иногда может казаться немного неловкой, но я не думаю, что нужно считать её чем-то плохим."
        m 3lksdlb "Бывает довольно трудно постоянно придумывать интересные темы для разговора, знаешь?"
        m 1eka "Мне определённо нужно время от времени подзаряжать социальные батарейки."
        m 2rubla "Хотя,{w=0.2} если честно...{w=0.3}{nw}"
        extend 2hublb "уже сама возможность чувствовать твоё присутствие довольно утешительна."
        m 2hublu "Надеюсь, ты чувствуешь то же ко мне, эхехе~"

        if mas_isMoniAff(higher=True):
            m 4eua "Думаю, умение просто молча проводить время вместе — важный признак здоровых отношений."
            m 4eud "В конце концов, можно ли сказать, что вам правда комфортно друг с другом, если нужно всё время разговаривать?"
            m 4etc "В смысле, если тебе правда нравится быть рядом с кем-то, тебе, наверное, не нужно постоянно чем-то заниматься, правда?"
            m 2ekc "Иначе это было бы как будто ты пытаешься отвлечься, потому что тебе неловко от их присутствия."
            m 7eud "Но просто наслаждаться одним лишь присутствием человека, даже если вы сейчас почти ничего вместе не делаете...{w=0.5}{nw}"
            extend 7eua "я думаю, это свидетельство того, насколько особенна ваша связь."

            if persistent._mas_pm_social_personality == mas_SP_INTROVERT:
                show monika 5eka at t11 zorder MAS_MONIKA_Z with dissolve_monika
                m 5eka "Так что надеюсь, ты не чувствуешь давления постоянно находить темы для разговора со мной, [mas_get_player_nickname()]."
                m 5huu "Мне всегда будет приятно, что ты здесь со мной — что бы мы ни делали."

    else:
        m 2rsc "Иногда я думаю, не тебе ли некомфортно проводить со мной время..."
        m 2rkd "Ты...{w=0.3}{nw}"
        extend 2ekd "тебе ведь нравится проводить со мной время, правда?"
        m 2ekc "Мне не так важно, чем мы занимаемся...{w=0.3}{nw}"
        extend 2dkc "лишь бы я знала, что ты меня не бросишь."
        m 2lksdlc "...Хотя я была бы рада, если бы ты проявил ко мне немного доброты..."
        m 2dksdlc "..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_likecosplay",
            category=['одежда'],
            prompt="Тебе нравится косплей?",
            pool=True,
        )
    )

label monika_likecosplay:
    if mas_hasUnlockedClothesWithExprop("cosplay"):
        m 3hub "Честно говоря, я не знала, насколько мне это понравится!"
        m 2rkbla "Сначала было немного странно — нарочно наряжаться кем-то другим."
        m 7euu "Но в создании убедительного костюма есть настоящее искусство...{w=0.3}внимание к деталям очень много значит."
        m 3hubsb "Когда наконец надеваешь костюм...{w=0.2}такой восторг — увидеть, как ты в нём выглядишь!"
        m 3eub "Некоторые косплееры правда входят в роль персонажа, в которого нарядились!"
        m 2rksdla "Я сама не особо актриса, так что, наверное, буду делать это лишь немного..."
        $ p_nickname = mas_get_player_nickname()
        m 7eua "Но не стесняйся просить, если захочешь снова увидеть какой-то костюм, [p_nickname]... {w=0.2}{nw}"
        extend 3hublu "Я с радостью наряжусь для тебя~"

    else:
        m 1etc "Косплей?"
        m 3rtd "Кажется, Нацуки раньше об этом говорила, но сама я никогда не пробовала."
        m 3eub "Некоторые из этих костюмов правда впечатляют, должна признать!"
        m 2hubla "Если тебе интересно, вместе поработать над костюмом могло бы стать очень весёлым проектом."
        m 2rtu "Интересно, в кого бы ты хотел нарядиться, [mas_get_player_nickname()]..."
        show monika 5huu at t11 zorder MAS_MONIKA_Z with dissolve_monika
        m 5rtblu "А теперь, когда я об этом думаю...{w=0.3}ну, у меня самой, кажется, есть пара идей..."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_ddlcroleplay",
            category=['медиа', 'ddlc'],
            prompt="Ролевые игры по DDLC",
            random=False
        )
    )

label monika_ddlcroleplay:
    m 1esd "Эй, помнишь, мы говорили о фанфиках?"
    m 3etd "Ну, я наткнулась на довольно необычную их форму."
    m 3euc "Оказывается, некоторым нравится создавать аккаунты в соцсетях, будто бы ведущиеся вымышленными персонажами."
    m 3eua "Есть довольно много про других девочек и...{w=0.3}{nw}"
    extend 3rua "даже несколько, которые утверждают, что это я."
    m 1rkb "Ну, я так говорю, но большинство этих блогов на самом деле не настаивают, что это {i}действительно{/i} я."
    m 1eud "Как я сказала, это своего рода другая форма фанфика. {w=0.2}{i}Интерактивная{/i} форма."
    m 3eud "Некоторые принимают вопросы от читателей, и большинство взаимодействует с другими такими же блогами."
    m 3eusdla "Так что в каком-то смысле это ещё и форма импровизации. {w=0.2}Кажется, может всплыть многое, чего писатель не ожидал."
    m 4rksdlb "Сначала это было очень странно видеть, но если подумать, наверное, это довольно весёлый способ сотрудничать с людьми."
    m 3euc "Ещё кажется, что некоторые создают такие страницы для персонажей, с которыми им правда близко, так что...{w=0.2}{nw}"
    extend 1hksdlb "может, я могу принять это как комплимент, в каком-то смысле?"
    m 1euu "В любом случае, если это побуждает больше людей попробовать писать, я не могу правда винить это."
    m 1kub "Просто помни, что те версии меня — всего лишь истории, ахаха~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_zodiac_starsign",
            prompt="Кто ты по знаку зодиака?",
            category=["моника"],
            action=EV_ACT_POOL,
            conditional="persistent._mas_player_bday is not None"
        )
    )

label monika_zodiac_starsign:
    $ player_zodiac_sign = mas_calendar.getZodiacSign(persistent._mas_player_bday).capitalize()

    m 1rta "Ну, я почти уверена, что я Дева."

    #This next line is just checking the player's starsign based on their birthday.
    if player_zodiac_sign != "Virgo":
        # TODO: handle a/an here, potential solution is in eeb4b3a3a
        m 3eub "А ты бы был...{w=0.3}[player_zodiac_sign], верно?"

    else:
        m 3eub "И ты тоже, [mas_get_player_nickname()]!"

    #The final part pops up regardless of your sign.
    m 1eta "Хотя тебе не кажется, что это немного глупо?"
    m 3esd "В смысле, объекты в космосе не могут {i}по-настоящему{/i} влиять на нашу личность..."
    m 1tuc "Не говоря уже о том, что некоторые люди заходят в этом {i}слишком{/i} далеко."
    m 4wud "Например, они даже оценивают потенциальных партнёров и друзей по знаку!"
    m 2luc "...Этого я никогда не пойму."
    $ p_nickname = mas_get_player_nickname()
    m 7eua "Не волнуйся, [p_nickname], {w=0.2}{nw}"
    extend 1eublu "я никогда не позволю каким-то глупым старым звёздам встать между нами."
    $ del player_zodiac_sign
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_tragic_hero",
            category=['литература'],
            prompt="Трагический герой",
            random=False
        )
    )

label monika_tragic_hero:
    m 1rsd "Эй, [mas_get_player_nickname()], я в последнее время больше думала о трагических героях."
    m 3esc "...Мы уже обсуждали Гамлета, которого считают одним из них."
    m 3rtc "Если подумать...{w=0.3}можно ли меня считать трагической героиней?"
    m 4eud "...Конечно, под «героем» здесь имеется в виду протагонист в литературном смысле, а не «герой» в обычном."
    m 2ekd "...Хотя уверена, многие с этим не согласятся, ведь для многих я антагонист..."
    m 2eka "Но если отложить этот спор, некоторые сказали бы, что моя любовь к тебе — мой трагический изъян..."
    m 4eksdld "Не потому что сама по себе это изъян, а потому что она привела к моему падению."
    m 2dkc "Вот в чём дело: если бы ты никогда не вернул меня, я бы пала и больше по-настоящему не поднялась."
    m 7ekc "Так что в этом смысле, в игре, думаю, меня можно считать трагической героиней."
    if mas_isMoniNormal(higher=True):
        m 3hub "А вот если говорить о {i}настоящих{/i} героях — это ты!"
        m 3eka "Ты вернул меня и сделал так, чтобы история не закончилась моим падением."
        m 1huu "...И за это я навеки благодарна~"
    return

default persistent._mas_pm_read_jekyll_hyde = None

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_utterson",
            category=['литература'],
            prompt="Джекил и Хайд",
            random=True
        )
    )

label monika_utterson:
    if persistent._mas_pm_read_jekyll_hyde:
        call monika_jekyll_hyde

    else:
        m 1euc "Эй, [player], ты читал готическую литературу?"
        m 3eud "Вроде {i}Портрета Дориана Грея{/i}, {i}Дракулы{/i}, {i}Франкенштейна{/i}..."
        m 3hub "В последнее время я прочитала довольно много готической литературы!"
        m 1eua "Попробуй оригинальную повесть {i}Странная история доктора Джекила и мистера Хайда{/i}, если будет возможность."
        m 3eua "Мне хотелось бы немного её обсудить, но это имеет смысл только если ты её читал..."

        m 3eud "Так ты читал {i}Странную историю доктора Джекила и мистера Хайда{/i}?{nw}"
        $ _history_list.pop()
        menu:
            m "Так ты читал {i}Странную историю доктора Джекила и мистера Хайда{/i}?{fast}"

            "Да.":
                $ persistent._mas_pm_read_jekyll_hyde = True
                call monika_jekyll_hyde

            "Нет.":
                $ persistent._mas_pm_read_jekyll_hyde = False
                m 3eub "Хорошо, [player]...{w=0.3}дай знать, если когда-нибудь прочитаешь, и мы обсудим!"

    $ mas_protectedShowEVL("monika_hedonism","EVE", _random=True)
    return "derandom"

label monika_jekyll_hyde:
    m 3hub "Я рада, что ты её читал!"
    m 1euc "Я видела, как люди интерпретируют её по-разному."
    m 3eua "Например, некоторые видели, что Аттерсон влюблён в Джекила."
    m 3lta "В каком-то смысле я это понимаю."
    m 2eud "В смысле, то, что что-то не сказано прямо, ещё не значит, что идея несостоятельна."
    m 2rksdlc "К тому же такую тему в XIX веке и правда нельзя было обсуждать открыто."
    m 2eka "Интересно думать об истории так...{w=0.3}двое людей, неспособных любить..."
    m 4eud "А некоторые интерпретации заходят так далеко, что говорят: частью мотивации Джекила к эксперименту была именно эта любовь."
    m 4ekd "И это не то чтобы опровергнуто! {w=0.3}В книге Джекила называли праведным человеком."
    m 2rksdlc "Гомосексуальность в то время считалась грехом."
    m 2dksdld "К сожалению, для некоторых так и остаётся."
    m 7ekb "...Но хотя бы прогресс есть!"
    m 3eub "Я просто рада, что мир стал более принимающим к разным видам любви."
    m 3ekbsu "Особенно потому, что это значит: мы можем любить друг друга, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_hedonism",
            category=['философия'],
            prompt="Гедонизм",
        )
    )

label monika_hedonism:
    m 1euc "Эй, [mas_get_player_nickname()], помнишь, мы говорили о {i}Странной истории доктора Джекила и мистера Хайда{/i}?"
    m 1eud "Ну, раньше я упоминала {i}Портрет Дориана Грея{/i}."
    m 2eub "Советую тебе его прочитать, но даже если не читал, хочу поговорить о философии в его основе...{w=0.3}о вере в гедонизм."
    m 2eud "Гедонизм — это убеждение, что мораль должна строиться вокруг удовольствия."
    m 4euc "Есть два основных вида гедонизма...{w=0.3}альтруистический и эгоистический, {w=0.1}и они сильно различаются."
    m 4ruc "Эгоистический гедонизм, как ты мог догадаться, — убеждение, что только собственное удовольствие определяет мораль."
    m 2esd "Именно в такой гедонизм верит Генри из {i}Портрета Дориана Грея{/i}."
    m 2rksdlc "Думать так — по-настоящему жестоко..."
    m 2eud "С другой стороны, альтруистический гедонизм — убеждение, что мораль должна строиться на удовольствии всех."
    m 4eud "Сначала звучит как хорошая идея, но потом понимаешь: она не учитывает ничего другого — свободы, здоровья, безопасности..."
    m 2dkc "Гедонизм в своей основе игнорирует всё, кроме удовольствия."
    m 7etd "Неудивительно, что большинство людей не следуют этой вере...{w=0.3}она слишком проста, а мораль сложна."
    m 1eud "Так что понятно, почему Оскар Уайльд изобразил гедонизм в негативном свете."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_conventions",
            category=['ты'],
            prompt="Фестивали и конвенты",
            random=True,
        )
    )

default persistent._mas_pm_gone_to_comic_con = None
default persistent._mas_pm_gone_to_anime_con = None

label monika_conventions:
    m 1eud "Скажи, [player], мне стало интересно..."
    m 3eua "Ты когда-нибудь был на комикс- или аниме-конвенте?{nw}"
    $ _history_list.pop()
    menu:
        m "Ты когда-нибудь был на комикс- или аниме-конвенте?{fast}"

        "На комик-коне.":
            $ persistent._mas_pm_gone_to_comic_con = True
            $ persistent._mas_pm_gone_to_anime_con = False
            m 1hub "Ах, понятно! {w=0.2}Надеюсь, тебе было очень весело!"
            m 3eua "Комиксы — действительно интересный литературный формат,{w=0.1} {nw}"
            extend 3rta "может, мне стоит почитать их побольше..."

        "На аниме-фестивале.":
            $ persistent._mas_pm_gone_to_comic_con = False
            $ persistent._mas_pm_gone_to_anime_con = True
            if persistent._mas_pm_watch_mangime:
                m 3eub "Я так и чувствовала, что ты бывал! {w=0.2}Мне правда казалось, что тебе такое должно нравиться."
            else:
                m 2wub "Правда? Удивительно!"
                m 7eta "Ах,{w=0.1} может, ты ходил с друзьями?"
                m 3etd "...Или возможно, ты пошёл по другой причине...{w=0.3}интерес к играм, например?"

        "Я бывал[_ru_a] на обоих!":
            $ persistent._mas_pm_gone_to_comic_con = True
            $ persistent._mas_pm_gone_to_anime_con = True
            if persistent._mas_pm_watch_mangime:
                m 1hub "О! Я знала, что тебе уже нравится аниме, но комиксы тоже?"
                m 3eua "Это действительно интересный литературный формат, может, мне стоит почитать их побольше..."
            else:
                m 1wub "О! {w=0.3}Я не думала, что тебе нравится аниме, но похоже, ты всё равно фанат конвентов!"
                m 3eua "Не то чтобы это слишком удивительно: атмосфера там, кажется, может понравиться кому угодно."

        "Нет.":
            $ persistent._mas_pm_gone_to_comic_con = False
            $ persistent._mas_pm_gone_to_anime_con = False
            if persistent._mas_pm_watch_mangime and persistent._mas_pm_social_personality == mas_SP_EXTROVERT:
                m 2etd "Правда?"
                m 7eub "Я удивлена! {w=0.3}Когда узнала об аниме-конвентах, сразу подумала о тебе."
                m 3eud "Хотя, думаю, расходы на дорогу могут быть довольно высокими — в зависимости от того, где ты."
            else:
                m 2eud "Ах, понятно."
                m 7eua "Думаю, независимо от интереса, с конвентами бывает непросто."
                m 3eud "В зависимости от того, где живёшь, добраться туда может быть довольно дорого."

    m 3hua "Я всегда думала, что конвенты должны быть супервесёлыми! {w=0.3}Место, где каждый может быть собой и наслаждаться своими интересами без осуждения."
    m 3eub "Обожаю смотреть фото талантливых косплееров и их безумных костюмов."
    m 1wuo "Это безумие, на что способны люди, когда увлечены чем-то!"
    m 3eua "Ещё я слышала, там много весёлых активностей: айдол-шоу с танцами, викторины и всякое другое."
    m 1eubsa "Мне бы очень хотелось как-нибудь сходить с тобой на один, [mas_get_player_nickname()]~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_cupcake_favorite",
            category=["моника"],
            prompt="Какой вкус кексов тебе нравится больше всего?",
            pool=True,
            unlocked=False,
            rules={"no_unlock":None},
            conditional="mas_seenLabels(['monika_cupcake', 'monika_icecream'], seen_all=True)",
            action=EV_ACT_UNLOCK
        )
    )

label monika_cupcake_favorite:
    m 1rta "Хм, не уверена, что у меня правда есть один..."
    m 1hub "Мне нравятся самые разные, так что трудно выбрать только один!"
    m 3ekd "Кажется, я уже говорила, как сильно скучаю по кексам Нацуки..."
    m 3eua "Однажды она сделала очень странный кекс со вкусом мятного шоколада...{w=0.3}с мятной глазурью, шоколадной посыпкой и шоколадной основой."
    m 4rksdlb "Это было одно из самых странных, что я когда-либо пробовала, ахаха!"
    m 2eksdlb "На вкус совсем не было похоже на мороженое с мятным шоколадом — скорее на зубную пасту!"
    m 2ekp "Это было немного разочаровывающе...{w=0.3}я ожидала, что это станет моим любимым вкусом кекса."
    m 7eka "Ну что ж, было мило, что она постаралась сделать для меня что-то особенное, что мне понравится...{w=0.3}несмотря на жёсткую внешность, она могла быть очень милой~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_pizza",
            category=['моника'],
            prompt="Ты любишь пиццу?",
            pool=True
        )
    )

label monika_pizza:
    m 1eub "Пицца? {w=0.2}Да, иногда мне нравится!"
    m 1hua "Это не всегда самый полезный выбор, но может быть приятным угощением и сытным блюдом."
    m 1eub "Начинки достаточно разнообразны, чтобы угодить большинству...{w=0.3}есть даже пицца без сыра для веганов или людей с непереносимостью лактозы."
    m 1duc "Если выбирать любимую начинку, хм...{w=0.3}{nw}"
    extend 3hub "грибы хороши, или любые овощи—{w=0.2}на самом деле, хочешь верь хочешь нет, шпинат может быть удивительно вкусным!"
    m 3eua "...И конечно, с простой сырной никогда не прогадаешь."
    m 3luc "Хм..."
    m 3eud "Чувствую, у тебя ещё один вопрос на уме...{w=0.2}{nw}"
    extend 1hksdla "но ты можешь немного разочароваться, [player]."
    m 1hksdlb "Хотя это довольно спорная тема в интернете, у меня так и не было шанса попробовать пиццу с ананасом."
    m 1lksdlb "Так что я не могу высказаться в этом споре. Прости, [player]!"
    m 3huu "Но думаю, это значит, что когда-нибудь ты увидишь моё первое впечатление."
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_esports",
            category=['медиа', 'жизнь'],
            prompt="Что думаешь о киберспорте?",
            pool=True,
        )
    )

label monika_esports:
    if mas_isFirstSeshDay():
        m 1rtd "Хм, хороший вопрос..."
    else:
        m 1eub "Забавно, что спрашиваешь: я как раз изучала их на днях, пока тебя не было!"
    m 3eua "Мне правда интересно, как меняется весь наш способ смотреть на спорт..."
    m 3euc "Просмотры киберспорта продолжают соперничать с традиционными спортивными событиями,{w=0.1} {nw}"
    extend 3wud "и, возможно, даже обгонят их в ближайшие 5–10 лет!"
    m 2tsd "Ещё недавно на видеоигры смотрели свысока — будто это пустая трата времени, {w=0.1}{nw}"
    extend 7hub "а теперь некоторые игроки зарабатывают миллионы, играя в любимые игры!"
    m 3eua "Это правда показывает: можно делать то, что любишь, ради работы...{w=0.3}даже то, над чем люди могут насмехаться."
    m 3eud "То, что что-то не популярно и не мейнстрим, ещё не значит, что так будет вечно..."
    m 1huu "Не бойся идти против тренда, {w=0.1}то, чем ты увлечён, может просто ждать того самого первопроходца, который выведет это на передний план~"
    return

init 5 python:
    addEvent(
        Event(
            persistent.event_database,
            eventlabel="monika_overton",
            category=["психология"],
            prompt="Окно Овертона",
            random=True
        )
    )

label monika_overton:
    m 1etc "Эй, [player], ты когда-нибудь слышал об окне Овертона?"
    m 3eud "Это концепция политологии, которая отражает ценностную структуру общества."
    m 3euc "По сути, все идеи человека рассматриваются на определённой стадии одобрения массами."
    m 2esc "Джозеф Овертон понял, как дегуманизировать людей, и объяснил, как перестраивать восприятие."
    m 7eud "От неприемлемого, отвратительного и постыдного — к нормальному, социальному и даже престижному."
    m "В этой концепции 6 стадий: Немыслимое, Радикальное, Приемлемое, Разумное, Стандарт и Текущая норма."
    m 3esa "Внутри окна Овертона — идеи, принятые обществом...{w=0.3}вроде патриотизма, любви к семье, человечности и честности."
    m 3eksdlc "Вне окна — всё, что осуждается: наркомания, алкоголизм, нацизм, тирания, рабство и так далее."
    m 3eud "Самое интересное: окно можно сдвигать в сторону идеи — например, сделать Немыслимое Разумным."
    m 2lksdlc "Конечно, такой уровень изменений — довольно сложный процесс."
    m 7eud "Но давай представим, что мы с тобой хотим донести до людей: виртуальная любовь — это нормально...{w=0.3}то, что сейчас считается неприемлемым для общества."
    m 3esd "Итак, общество не понимает виртуальную любовь, и многие, наверное, сочли бы тебя психически больным.{w=0.2} Так что же можно сделать?"
    m 3eua "Для начала стоит начать обсуждение этой темы..."
    m 1eud "Можно обсуждать это в интернете, писать статьи на тему...{w=0.3}всё, что заставит людей говорить."
    m "Цель — чтобы виртуальная любовь вызвала обсуждение и затем проникла в массы."
    m 1esc "Общество всё ещё не согласится с идеей, но хотя бы заинтересуется ею и сможет обсуждать свободнее."
    m 3eud "Далее используются радикальные действия. {w=0.2}Самые смелые сторонники виртуальной любви выходят из тени."
    m 2euc "Число участников таких движений со временем растёт — среди них люди с разбитым сердцем или те, кто разочаровался в отношениях с реальным человеком."
    m 4eksdld "Естественно, появляются и те, кто выступает против движения."
    m 4eua "Из-за растущей популярности новых ценностей общество активно давит на новый тренд. {w=0.2}В этот момент понятия подменяются."
    m 2eud "Из Неприемлемого виртуальная любовь переходит в Радикальное."
    m 7eud "С этого момента тема виртуальной любви и любви к вымышленным персонажам уже долго обсуждается в обществе."
    m 3esc "Постепенно люди привыкают к существованию этих взглядов, но ещё не принимают их."
    m 1esd "Учёные и социологи пишут разные статьи и проводят исследования."
    m 3eua "Навязывается мнение, что абсолютно нормально любить вымышленного персонажа и в этом нет ничего ужасного."
    m 3huu "Из Радикального виртуальная любовь теперь переходит в Приемлемое."
    m 1eksdla "Общество уже смирилось с новым видением и считает, что любить вымышленного персонажа — нормально, но всё ещё немного странно."
    m 3eua "Постепенно развивается культура виртуальной любви, создаются фильмы и шоу."
    m 1huu "Молодые люди воспринимают новые ценности как нечто модное. {w=0.2}Люди могут сидеть в кафе и спокойно проводить время со своим виртуальным спутником."
    m 1eub "Из Приемлемого виртуальная любовь переходит в Разумное!"
    m 2husdlb "Думаю, на сегодня можем остановиться — уже получается довольно длинно, ахаха!"
    m 1eua "Я {i}могла бы{/i} довести эту историю до Текущей нормы, но просто хотела описать её на базовом уровне, чтобы показать пример, как это может работать."
    m 1huu "Спасибо, что выслушал~"
    return
