# --- FILE MAP ---
# zz_reactions.rpy — подарки файлами (.gift)
#
# Кинул файл в characters/ — Моника реагирует. Карта имя → реакция,
# история что уже дарили.
#
# Store: mas_filereacts
# Искать: addReaction, filereact_map
# Какие ACS дарит файл — ещё giftname_map в zz_spriteobjects.rpy
# ---

# FileReactions framework.
# not too different from events

default persistent._mas_filereacts_failed_map = dict()
# mapping of failed deleted file reacts

default persistent._mas_filereacts_just_reacted = False
# True if we just reacted to something

default persistent._mas_filereacts_reacted_map = dict()
# mapping of file reacts that we have already reacted to today

default persistent._mas_filereacts_stop_map = dict()
# mapping of file reacts that we should no longer react to ever again

default persistent._mas_filereacts_historic = dict()
# historic database used to track when and how many gifts Monika has received

default persistent._mas_filereacts_last_reacted_date = None
# stores the last date gifts were received so we can clear _mas_filereacts_reacted_map

default persistent._mas_filereacts_sprite_gifts = {}
# contains sprite gifts that are currently available. aka not already unlocked
# key: giftname to react to
# value: tuple of the following format:
#   [0] - sprite type (0 - ACS, 1 - HAIR, 2 - CLOTHES)
#   [1] - id of the sprite object this gift unlocks.
#
# NOTE: THIS IS REVERSE MAPPING OF HOW JSON GIFTS AND SPRITE REACTED WORK
#
# NOTE: contains sprite gifts before being unlocked. When its unlocked,
#   they move to _mas_sprites_json_gifted_sprites

default persistent._mas_filereacts_sprite_reacted = {}
# list of sprite reactions. This MUST be handled via the sprite reaction/setup
# labels. DO NOT ACCESS DIRECTLY. Use the helper function
# key:  tuple of the following format:
#   [0]: sprite type (0 - ACS, 1 - HAIR, 2 - CLOTHES)
#   [1]: id of the sprite objec this gift unlocks (name) != display name
# value: giftname

# TODO: need a generic reaction for finding a new ACS/HAIR/CLOTHES

default persistent._mas_filereacts_gift_aff_gained = 0
#Holds the amount of affection we've gained by gifting
#NOTE: This is reset daily

default persistent._mas_filereacts_last_aff_gained_reset_date = datetime.date.today()
#Holds the last time we reset the aff gained for gifts

init 800 python:
    if len(persistent._mas_filereacts_failed_map) > 0:
        store.mas_filereacts.delete_all(persistent._mas_filereacts_failed_map)

init -11 python in mas_filereacts:
    import store
    import store.mas_utils as mas_utils
    import datetime
    import random

    from collections import namedtuple

    GiftReactDetails = namedtuple(
        "GiftReactDetails",
        [
            # label corresponding to this gift react
            "label",

            # lowercase, no extension giftname for this gift react
            "c_gift_name",

            # will contain a reference to sprite object data if this is
            # associatd with a sprite. Will be None if not related to
            # sprite objects.
            "sp_data",
        ]
    )

    # file react database
    filereact_db = dict()

    # file reaction filename mapping
    # key: filename or list of filenames
    # value: Event
    filereact_map = dict()

    # currently found files react map
    # NOTE: highly volitatle. Expect this to change often
    # key: lowercase filename, without extension
    # value: on disk filename
    foundreact_map = dict()

    # spare foundreact map, designed for threaded use
    # same keys/values as foundreact_map
    th_foundreact_map = dict()

    # good gifts list
    good_gifts = [
        # Custom sprite jsons should be considered good
        "mas_reaction_gift_generic_sprite_json"
    ]

    # bad gifts list
    bad_gifts = list()

    # connector quips
    connectors = None
    gift_connectors = None

    # starter quips
    starters = None
    gift_starters = None

    GIFT_EXT = ".gift"


    def addReaction(ev_label, fname, _action=store.EV_ACT_QUEUE, is_good=None, exclude_on=[]):
        """
        Adds a reaction to the file reactions database.

        IN:
            ev_label - label of this event
            fname - filename to react to
            _action - the EV_ACT to do
                (Default: EV_ACT_QUEUE)
            is_good - if the gift is good(True), neutral(None) or bad(False)
                (Default: None)
            exclude_on - keys marking times to exclude this gift
            (Need to check ev.rules in a respective react_to_gifts to exclude with)
                (Default: [])
        """
        # lowercase the list in case
        if fname is not None:
            fname = fname.lower()

        exclude_keys = {}
        if exclude_on:
            for _key in exclude_on:
                exclude_keys[_key] = None

        # build new Event object
        ev = store.Event(
            store.persistent.event_database,
            ev_label,
            category=fname,
            action=_action,
            rules=exclude_keys
        )

        # TODO: should ovewrite category and action always

        # add it to the db and map
        filereact_db[ev_label] = ev
        filereact_map[fname] = ev

        if is_good is not None:
            if is_good:
                good_gifts.append(ev_label)
            else:
                bad_gifts.append(ev_label)


    def _initConnectorQuips():
        """
        Initializes the connector quips
        """
        global connectors, gift_connectors

        # the connector is a MASQipList
        connectors = store.MASQuipList(allow_glitch=False, allow_line=False)
        gift_connectors = store.MASQuipList(allow_glitch=False, allow_line=False)


    def _initStarterQuips():
        """
        Initializes the starter quips
        """
        global starters, gift_starters

        # the starter is a MASQuipList
        starters = store.MASQuipList(allow_glitch=False, allow_line=False)
        gift_starters = store.MASQuipList(allow_glitch=False, allow_line=False)


    def build_gift_react_labels(
            evb_details=[],
            gsp_details=[],
            gen_details=[],
            gift_cntrs=None,
            ending_label=None,
            starting_label=None,
            prepare_data=True
    ):
        """
        Processes gift details into a list of labels to show
        labels to queue/push whatever.

        IN:
            evb_details - list of GiftReactDetails objects of event-based
                reactions. If empty list, then we don't build event-based
                reaction labels.
                (Default: [])
            gsp_details - list of GiftReactDetails objects of generic sprite
                object reactions. If empty list, then we don't build generic
                sprite object reaction labels.
                (Default: [])
            gen_details - list of GiftReactDetails objects of generic gift
                reactions. If empty list, then we don't build generic gift
                reaction labels.
                (Default: [])
            gift_cntrs - MASQuipList of gift connectors to use. If None,
                then we don't add any connectors.
                (Default: [])
            ending_label - label to use when finished reacting.
                (Default: None)
            starting_label - label to use when starting reacting
                (Default: None)
            prepare_data - True will also setup the appropriate data
                elements for when dialogue is shown. False will not.
                (Default: True)

        RETURNS: list of labels. Evb reactions are first, followed by
            gsp reactions, then gen reactions
        """
        labels = []

        # first find standard reactions
        if len(evb_details) > 0:
            evb_labels = []
            for evb_detail in evb_details:
                evb_labels.append(evb_detail.label)

                if gift_cntrs is not None:
                    evb_labels.append(gift_cntrs.quip()[1])

                if prepare_data and evb_detail.sp_data is not None:
                    # if we need to prepare data, then add the sprite_data
                    # to reacted map
                    store.persistent._mas_filereacts_sprite_reacted[evb_detail.sp_data] = (
                        evb_detail.c_gift_name
                    )

            labels.extend(evb_labels)

        # now generic sprite objects
        if len(gsp_details) > 0:
            gsp_labels = []
            for gsp_detail in gsp_details:
                if gsp_detail.sp_data is not None:
                    gsp_labels.append("mas_reaction_gift_generic_sprite_json")

                    if gift_cntrs is not None:
                        gsp_labels.append(gift_cntrs.quip()[1])

                    if prepare_data:
                        store.persistent._mas_filereacts_sprite_reacted[gsp_detail.sp_data] = (
                            gsp_detail.c_gift_name
                        )

            labels.extend(gsp_labels)

        # and lastlly is generics
        num_gen_gifts = len(gen_details)
        if num_gen_gifts > 0:
            gen_labels = []

            if num_gen_gifts == 1:
                gen_labels.append("mas_reaction_gift_generic")
            else:
                gen_labels.append("mas_reaction_gifts_generic")

            if gift_cntrs is not None:
                gen_labels.append(gift_cntrs.quip()[1])

            for gen_detail in gen_details:
                if prepare_data:
                    store.persistent._mas_filereacts_reacted_map.pop(
                        gen_detail.c_gift_name,
                        None
                    )

                    store.mas_filereacts.delete_file(gen_detail.c_gift_name)

            labels.extend(gen_labels)

        # final setup
        if len(labels) > 0:

            # only pop if we used connectors
            if gift_cntrs is not None:
                labels.pop()

            # add the ender
            if ending_label is not None:
                labels.append(ending_label)

            # add the starter
            if starting_label is not None:
                labels.insert(0, starting_label)

        # now return the list
        return labels

    def build_exclusion_list(_key):
        """
        Builds a list of excluded gifts based on the key provided

        IN:
            _key - key to build an exclusion list for

        OUT:
            list of giftnames which are excluded by the key
        """
        return [
            giftname
            for giftname, react_ev in filereact_map.iteritems()
            if _key in react_ev.rules
        ]

    def check_for_gifts(
            found_map={},
            exclusion_list=[],
            exclusion_found_map={},
            override_react_map=False,
    ):
        """
        Finds gifts.

        IN:
            exclusion_list - list of giftnames to exclude from the search
            override_react_map - True will skip the last reacted date check,
                False will not
                (Default: False)

        OUT:
            found_map - contains all gifts that were found:
                key: lowercase giftname, no extension
                val: full giftname wtih extension
            exclusion_found_map - contains all gifts that were found but
                are excluded.
                key: lowercase giftname, no extension
                val: full giftname with extension

        RETURNS: list of found giftnames
        """
        raw_gifts = store.mas_docking_station.getPackageList(GIFT_EXT)

        if len(raw_gifts) == 0:
            return []

        # day check
        if store.mas_pastOneDay(store.persistent._mas_filereacts_last_reacted_date):
            store.persistent._mas_filereacts_last_reacted_date = datetime.date.today()
            store.persistent._mas_filereacts_reacted_map = dict()

        # look for potential gifts
        gifts_found = []
        has_exclusions = len(exclusion_list) > 0

        for mas_gift in raw_gifts:
            gift_name, ext, garbage = mas_gift.partition(GIFT_EXT)
            c_gift_name = gift_name.lower()
            if (
                c_gift_name not in store.persistent._mas_filereacts_failed_map
                and c_gift_name not in store.persistent._mas_filereacts_stop_map
                and (
                    override_react_map
                    or c_gift_name not
                        in store.persistent._mas_filereacts_reacted_map
                )
            ):
                # this gift is valid (not in failed/stopped/or reacted)

                # check for exclusions
                if has_exclusions and c_gift_name in exclusion_list:
                    exclusion_found_map[c_gift_name] = mas_gift

                else:
                    gifts_found.append(c_gift_name)
                    found_map[c_gift_name] = mas_gift

        return gifts_found


    def process_gifts(gifts, evb_details=[], gsp_details=[], gen_details=[]):
        """
        Processes list of giftnames into types of gift

        IN:
            gifts - list of giftnames to process. This is copied so it wont
                be modified.

        OUT:
            evb_details - list of GiftReactDetails objects regarding
                event-based reactions
            spo_details - list of GiftReactDetails objects regarding
                generic sprite object reactions
            gen_details - list of GiftReactDetails objects regarding
                generic gift reactions
        """
        if len(gifts) == 0:
            return

        # make copy of gifts
        gifts = list(gifts)

        # first find standard reactions
        for index in range(len(gifts)-1, -1, -1):

            # determine if reaction exists
            mas_gift = gifts[index]
            reaction = filereact_map.get(mas_gift, None)

            if mas_gift is not None and reaction is not None:

                # pull sprite data
                sp_data = store.persistent._mas_filereacts_sprite_gifts.get(
                    mas_gift,
                    None
                )

                # remove gift and add details
                gifts.pop(index)
                evb_details.append(GiftReactDetails(
                    reaction.eventlabel,
                    mas_gift,
                    sp_data
                ))

        # now for generic sprite objects
        if len(gifts) > 0:
            for index in range(len(gifts)-1, -1, -1):
                mas_gift = gifts[index]
                # pull sprite data
                sp_data = store.persistent._mas_filereacts_sprite_gifts.get(
                    mas_gift,
                    None
                )

                if mas_gift is not None and sp_data is not None:
                    gifts.pop(index)

                    # add details
                    gsp_details.append(GiftReactDetails(
                        "mas_reaction_gift_generic_sprite_json",
                        mas_gift,
                        sp_data
                    ))

        # and lastly is generics
        if len(gifts) > 0:
            for mas_gift in gifts:
                if mas_gift is not None:
                    # add details
                    gen_details.append(GiftReactDetails(
                        "mas_reaction_gift_generic",
                        mas_gift,
                        None
                    ))


    def react_to_gifts(found_map, connect=True):
        """
        Reacts to gifts using the standard protocol (no exclusions)

        IN:
            connect - true will apply connectors, FAlse will not

        OUT:
            found_map - map of found reactions
                key: lowercaes giftname, no extension
                val: giftname with extension

        RETURNS:
            list of labels to be queued/pushed
        """
        # first find gifts
        found_gifts = check_for_gifts(found_map)

        if len(found_gifts) == 0:
            return []

        # put the gifts in the reacted map
        for c_gift_name, mas_gift in found_map.iteritems():
            store.persistent._mas_filereacts_reacted_map[c_gift_name] = mas_gift

        found_gifts.sort()

        # pull details from teh gifts
        evb_details = []
        gsp_details = []
        gen_details = []
        process_gifts(found_gifts, evb_details, gsp_details, gen_details)

        # register all the gifts
        register_sp_grds(evb_details)
        register_sp_grds(gsp_details)
        register_gen_grds(gen_details)

        # then build the reaction labels
        # setup connectors
        if connect:
            gift_cntrs = gift_connectors
        else:
            gift_cntrs = None

        # now build
        return build_gift_react_labels(
            evb_details,
            gsp_details,
            gen_details,
            gift_cntrs,
            "mas_reaction_end",
            _pick_starter_label()
        )

    def register_gen_grds(details):
        """
        registers gifts given a generic GiftReactDetails list

        IN:
            details - list of GiftReactDetails objects to register
        """
        for grd in details:
            if grd.label is not None:
                _register_received_gift(grd.label)


    def register_sp_grds(details):
        """
        registers gifts given sprite-based GiftReactDetails list

        IN:
            details - list of GiftReactDetails objcts to register
        """
        for grd in details:
            if grd.label is not None and grd.sp_data is not None:
                _register_received_gift(grd.label)


    def _pick_starter_label():
        """
        Internal function that returns the appropriate starter label for reactions

        RETURNS:
            - The label as a string, that should be used today.
        """
        if store.mas_isMonikaBirthday():
            return "mas_reaction_gift_starter_bday"
        elif store.mas_isD25() or store.mas_isD25Pre():
            return "mas_reaction_gift_starter_d25"
        elif store.mas_isF14():
            return "mas_reaction_gift_starter_f14"

        return "mas_reaction_gift_starter_neutral"

    def _core_delete(_filename, _map):
        """
        Core deletion file function.

        IN:
            _filename - name of file to delete, if None, we delete one randomly
            _map - the map to use when deleting file.
        """
        if len(_map) == 0:
            return

        # otherwise check for random deletion
        if _filename is None:
            _filename = random.choice(_map.keys())

        file_to_delete = _map.get(_filename, None)
        if file_to_delete is None:
            return

        if store.mas_docking_station.destroyPackage(file_to_delete):
            # file has been deleted (or is gone). pop and go
            _map.pop(_filename)
            return

        # otherwise add to the failed map
        store.persistent._mas_filereacts_failed_map[_filename] = file_to_delete


    def _core_delete_list(_filename_list, _map):
        """
        Core deletion filename list function

        IN:
            _filename - list of filenames to delete.
            _map - the map to use when deleting files
        """
        for _fn in _filename_list:
            _core_delete(_fn, _map)


    def _register_received_gift(eventlabel):
        """
        Registers when player gave a gift successfully
        IN:
            eventlabel - the event label for the gift reaction

        """
        # check for stats dict for today
        today = datetime.date.today()
        if not today in store.persistent._mas_filereacts_historic:
            store.persistent._mas_filereacts_historic[today] = dict()

        # Add stats
        store.persistent._mas_filereacts_historic[today][eventlabel] = store.persistent._mas_filereacts_historic[today].get(eventlabel,0) + 1


    def _get_full_stats_for_date(date=None):
        """
        Getter for the full stats dict for gifts on a given date
        IN:
            date - the date to get the report for, if None is given will check
                today's date
                (Defaults to None)

        RETURNS:
            The dict containing the full stats or None if it's empty

        """
        if date is None:
            date = datetime.date.today()
        return store.persistent._mas_filereacts_historic.get(date,None)


    def delete_file(_filename):
        """
        Deletes a file off the found_react map

        IN:
            _filename - the name of the file to delete. If None, we delete
                one randomly
        """
        _core_delete(_filename, foundreact_map)


    def delete_files(_filename_list):
        """
        Deletes multiple files off the found_react map

        IN:
            _filename_list - list of filenames to delete.
        """
        for _fn in _filename_list:
            delete_file(_fn)


    def th_delete_file(_filename):
        """
        Deletes a file off the threaded found_react map

        IN:
            _filename - the name of the file to delete. If None, we delete one
                randomly
        """
        _core_delete(_filename, th_foundreact_map)


    def th_delete_files(_filename_list):
        """
        Deletes multiple files off the threaded foundreact map

        IN:
            _filename_list - list of ilenames to delete
        """
        for _fn in _filename_list:
            th_delete_file(_fn)


    def delete_all(_map):
        """
        Attempts to delete all files in the given map.
        Removes files in that map if they dont exist no more

        IN:
            _map - map to delete all
        """
        _map_keys = _map.keys()
        for _key in _map_keys:
            _core_delete(_key, _map)

    def get_report_for_date(date=None):
        """
        Generates a report for all the gifts given on the input date.
        The report is in tuple form (total, good_gifts, neutral_gifts, bad_gifts)
        it contains the totals of each type of gift.
        """
        if date is None:
            date = datetime.date.today()

        stats = _get_full_stats_for_date(date)
        if stats is None:
            return (0,0,0,0)
        good = 0
        bad = 0
        neutral = 0
        for _key in stats.keys():
            if _key in good_gifts:
                good = good + stats[_key]
            if _key in bad_gifts:
                bad = bad + stats[_key]
            if _key == "":
                neutral = stats[_key]
        total = good + neutral + bad
        return (total, good, neutral, bad)



    # init
    _initConnectorQuips()
    _initStarterQuips()

init python:
    import store.mas_filereacts as mas_filereacts
    import store.mas_d25_utils as mas_d25_utils

    def addReaction(ev_label, fname_list, _action=EV_ACT_QUEUE, is_good=None, exclude_on=[]):
        """
        Globalied version of the addReaction function in the mas_filereacts
        store.

        Refer to that function for more information
        """
        mas_filereacts.addReaction(ev_label, fname_list, _action, is_good, exclude_on)


    def mas_checkReactions():
        """
        Checks for reactions, then queues them
        """

        # only check if we didnt just react
        if persistent._mas_filereacts_just_reacted:
            return

        # otherwise check
        mas_filereacts.foundreact_map.clear()

        #If conditions are met to use d25 react to gifts, we do.
        if mas_d25_utils.shouldUseD25ReactToGifts():
            reacts = mas_d25_utils.react_to_gifts(mas_filereacts.foundreact_map)
        else:
            reacts = mas_filereacts.react_to_gifts(mas_filereacts.foundreact_map)

        if len(reacts) > 0:
            for _react in reacts:
                MASEventList.queue(_react)
            persistent._mas_filereacts_just_reacted = True


    def mas_receivedGift(ev_label):
        """
        Globalied version for gift stats tracking
        """
        mas_filereacts._register_received_gift(ev_label)


    def mas_generateGiftsReport(date=None):
        """
        Globalied version for gift stats tracking
        """
        return mas_filereacts.get_report_for_date(date)

    def mas_getGiftStatsForDate(label,date=None):
        """
        Globalied version to get the stats for a specific gift
        IN:
            label - the gift label identifier.
            date - the date to get the stats for, if None is given will check
                today's date.
                (Defaults to None)

        RETURNS:
            The number of times the gift has been given that date
        """
        if date is None:
            date = datetime.date.today()
        historic = persistent._mas_filereacts_historic.get(date,None)

        if historic is None:
            return 0
        return historic.get(label,0)

    def mas_getGiftStatsRange(start,end):
        """
        Returns status of gifts over a range (needs to be supplied to actually be useful)

        IN:
            start - a start date to check from
            end - an end date to check to

        RETURNS:
            The gift status of all gifts given over the range
        """
        totalGifts = 0
        goodGifts = 0
        neutralGifts = 0
        badGifts = 0
        giftRange = mas_genDateRange(start, end)

        # loop over gift days and check if were given any gifts
        for date in giftRange:
            gTotal, gGood, gNeut, gBad = mas_filereacts.get_report_for_date(date)

            totalGifts += gTotal
            goodGifts += gGood
            neutralGifts += gNeut
            badGifts += gBad

        return (totalGifts,goodGifts,neutralGifts,badGifts)


    def mas_getSpriteObjInfo(sp_data=None):
        """
        Returns sprite info from the sprite reactions list.

        IN:
            sp_data - tuple of the following format:
                [0] - sprite type
                [1] - sprite name
                If None, we use pseudo random select from sprite reacts
                (Default: None)

        REUTRNS: tuple of the folling format:
            [0]: sprite type of the sprite
            [1]: sprite name (id)
            [2]: giftname this sprite is associated with
            [3]: True if this gift has already been given before
            [4]: sprite object (could be None even if sprite name is populated)
        """
        # given giftname? try and lookup
        if sp_data is not None:
            giftname = persistent._mas_filereacts_sprite_reacted.get(
                sp_data,
                None
            )
            if giftname is None:
                return (None, None, None, None, None)

        elif len(persistent._mas_filereacts_sprite_reacted) > 0:
            sp_data = persistent._mas_filereacts_sprite_reacted.keys()[0]
            giftname = persistent._mas_filereacts_sprite_reacted[sp_data]

        else:
            return (None, None, None, None, None)

        # check if this gift has already been gifted
        gifted_before = sp_data in persistent._mas_sprites_json_gifted_sprites

        # apply sprite object template if ACS
        sp_obj = store.mas_sprites.get_sprite(sp_data[0], sp_data[1])
        if sp_data[0] == store.mas_sprites.SP_ACS:
            store.mas_sprites.apply_ACSTemplate(sp_obj)

        # return results
        return (
            sp_data[0],
            sp_data[1],
            giftname,
            gifted_before,
            sp_obj,
        )


    def mas_finishSpriteObjInfo(sprite_data, unlock_sel=True):
        """
        Finishes the sprite object with the given data.

        IN:
            sprite_data - sprite data tuple from getSpriteObjInfo
            unlock_sel - True will unlock the selector topic, False will not
                (Default: True)
        """
        sp_type, sp_name, giftname, gifted_before, sp_obj = sprite_data

        # sanity check
        # NOTE: gifted_before is not required
        # NOTE: sp_obj is not required either
        if sp_type is None or sp_name is None or giftname is None:
            return

        sp_data = (sp_type, sp_name)

        if sp_data in persistent._mas_filereacts_sprite_reacted:
            persistent._mas_filereacts_sprite_reacted.pop(sp_data)

        if giftname in persistent._mas_filereacts_sprite_gifts:
            persistent._mas_sprites_json_gifted_sprites[sp_data] = giftname

        else:
            # since we have the data, we can add it ourselves if its missing
            # for some reason.
            persistent._mas_sprites_json_gifted_sprites[sp_data] = (
                giftname
            )

        # unlock the selectable for this sprite object
        store.mas_selspr.json_sprite_unlock(sp_obj, unlock_label=unlock_sel)

        # save persistent
        renpy.save_persistent()

    def mas_giftCapGainAff(amount=None, modifier=1):
        if amount is None:
            amount = store._mas_getGoodExp()

        mas_capGainAff(amount * modifier, "_mas_filereacts_gift_aff_gained", 9 if mas_isSpecialDay() else 3)

    def mas_getGiftedDates(giftlabel):
        """
        Gets the dates that a gift was gifted

        IN:
            giftlabel - gift reaction label to check when it was last gifted

        OUT:
            list of datetime.dates of the times the gift was given
        """
        return sorted([
            _date
            for _date, giftstat in persistent._mas_filereacts_historic.iteritems()
            if giftlabel in giftstat
        ])

    def mas_lastGiftedInYear(giftlabel, _year):
        """
        Checks if the gift for giftlabel was last gifted in _year

        IN:
            giftlabel - gift reaction label to check it's last gifted year
            _year - year to see if it was last gifted in this year

        OUT:
            boolean:
                - True if last gifted in _year
                - False otherwise
        """
        datelist = mas_getGiftedDates(giftlabel)

        if datelist:
            return datelist[-1].year == _year
        return False

### CONNECTORS [RCT000]

# none here!

## Gift CONNECTORS [RCT010]
#
#init 5 python:
#    store.mas_filereacts.gift_connectors.addLabelQuip(
#        "mas_reaction_gift_connector_test"
#    )

label mas_reaction_gift_connector_test:
    m "это проверка системы соединения"
    return

init 5 python:
    store.mas_filereacts.gift_connectors.addLabelQuip(
        "mas_reaction_gift_connector1"
    )

label mas_reaction_gift_connector1:
    m 1sublo "Ой! Ты хотел[_ru_a] подарить мне что-то ещё?"
    m 1hua "Что ж! Лучше открыть поскорее, правда?"
    m 1suo "И что же тут у нас..."
    return

init 5 python:
    store.mas_filereacts.gift_connectors.addLabelQuip(
        "mas_reaction_gift_connector2"
    )

label mas_reaction_gift_connector2:
    m 1hua "Ах, ну ты даёшь, [player]..."
    m "Тебе ведь правда нравится меня баловать?"
    if mas_isSpecialDay():
        m 1sublo "Что ж! Сегодня я не стану жаловаться на особое внимание."
    m 1suo "И что же тут у нас..."
    return


### STARTERS [RCT050]

init 5 python:
    store.mas_filereacts.gift_starters.addLabelQuip(
        "mas_reaction_gift_starter_generic"
    )

label mas_reaction_gift_starter_generic:
    m "общий тест"

# init 5 python:
# TODO: if we need this to be multipled then we do it

label mas_reaction_gift_starter_bday:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=0.5}Это..."
    # TODO: fix this so we can actually get this path since rn gifts
    # are added to this before we even get there
    if not persistent._mas_filereacts_historic.get(mas_monika_birthday):
        m "Подарок? Мне?"
        m 1hka "Я..."
        m 1hua "Я часто представляла, как получаю от тебя подарки на день рождения..."
        m "Но получить его на самом деле — это как мечта, ставшая явью..."
    else:
        m "Подарок?{w=0.5} Мне?"
        m 1eka "Это и правда мечта, ставшая явью, [player]."

    m 1sua "Ну, что же там внутри?"
    m 1suo "О, это..."
    return

label mas_reaction_gift_starter_neutral:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=0.5}Это..."
    m "Подарок? Мне?"
    m 1sua "Ну, посмотрим, что там внутри?"
    return

# d25
label mas_reaction_gift_starter_d25:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=1}Это..."
    m "Подарок? Для меня?"
    if mas_getGiftStatsRange(mas_d25c_start, mas_d25 + datetime.timedelta(days=1))[0] == 0:
        m 1eka "Тебе правда не нужно было ничего дарить мне на Рождество..."
        m 3hua "Но я так рада, что ты это сделал[_ru_a]!"
    else:
        m 1eka "Огромное тебе спасибо, [player]."
    m 1sua "Так, посмотрим... Что же там внутри?"
    return

#f14
label mas_reaction_gift_starter_f14:
    m 1sublo ".{w=0.7}.{w=0.7}.{w=1}"
    m "Э-{w=1}Это..."
    m "Подарок? Мне?"
    if mas_getGiftStatsForDate(mas_f14) == 0:
        m 1eka "Как это мило с твоей стороны — сделать мне подарок на День святого Валентина..."
    else:
        m 1eka "Огромное тебе спасибо, [player]."
    m 1sua "Так, посмотрим... Что же там внутри?"
    return

### REACTIONS [RCT100]

init 5 python:
    addReaction("mas_reaction_generic", None)

label mas_reaction_generic:
    "This is a test"
    return

#init 5 python:
#    addReaction("mas_reaction_gift_generic", None)

label mas_reaction_gift_generic:
    m 2dkd "{i}*вздох*{/i}"
    m 4ekc "Прости, [player]."
    m 1ekd "Я знаю, что ты пытаешься мне что-то подарить."
    m 2rksdld "Но почему-то я не могу прочитать файл."
    m 3euc "Только не пойми меня неправильно."
    m 3eka "Мне всё равно очень приятно, что ты попытал[_ru_sya] сделать мне подарок."
    m 1hub "И за это я тебе благодарна~"
    return

label mas_reaction_gifts_generic:
    m 1esd "Прости, [player]..."
    m 3rksdla "Я нашла то, что ты пытаешься мне подарить, но никак не могу толком это прочитать."
    m 3eub "Но ничего страшного!"
    m 1eka "В конце концов, главное — внимание~"
    m 1hub "Спасибо за заботу, [player]!"
    return

#init 5 python:
#    addReaction("mas_reaction_gift_test1", "test1")

label mas_reaction_gift_test1:
    m "Спасибо за тестовый подарок 1!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_test1", "category"))
    return

#init 5 python:
#    addReaction("mas_reaction_gift_test2", "test2")

label mas_reaction_gift_test2:
    m "Спасибо за тестовый подарок 2!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_test2", "category"))
    return

init -1 python:
    # RU: цвета ленточек (ж.р.); acc=True -> винительный падеж
    _MAS_RU_RIBBON_COLORS = {
        "black": u"чёрная", "blue": u"синяя", "dark purple": u"тёмно-фиолетовая",
        "emerald": u"изумрудная", "gray": u"серая", "green": u"зелёная",
        "light purple": u"светло-фиолетовая", "peach": u"персиковая", "pink": u"розовая",
        "platinum": u"платиновая", "red": u"красная", "ruby": u"рубиновая",
        "sapphire": u"сапфировая", "silver": u"серебристая", "teal": u"бирюзовая",
        "yellow": u"жёлтая",
    }
    def mas_ru_ribbon_color(color, acc=False):
        res = _MAS_RU_RIBBON_COLORS.get(color, color)
        if acc:
            res = res.replace(u"яя", u"юю").replace(u"ая", u"ую")
        return res

## GENERIC SPRITE OBJECT JSONS

label mas_reaction_gift_generic_sprite_json:
    $ sprite_data = mas_getSpriteObjInfo()
    $ sprite_type, sprite_name, giftname, gifted_before, spr_obj = sprite_data

    python:
        sprite_str = store.mas_sprites_json.SP_UF_STR.get(sprite_type, None)

    # TODO: something different if whatever was gifted has been gifted before

    # we have special react for generic json clothes
    if sprite_type == store.mas_sprites.SP_CLOTHES:
        call mas_reaction_gift_generic_clothes_json(spr_obj)

    else:
        # otherwise, it has to be an ACS.

        $ mas_giftCapGainAff(1)
        m "Ой, [player]!"
        if spr_obj is None or spr_obj.dlg_desc is None:
            # if we don't have all required description data, go generic
            m 1hua "Ты просто прелесть!"
            m 1eua "Спасибо за подарок!"
            m 3ekbsa "Ты и правда любишь меня баловать."
            m 1hubfa "Э-хе-хе!"

        else:
            python:
                acs_quips = [
                    _("Мне очень приятно!"),
                    _("Это просто чудесно!"),
                    _("Я в восторге!"),
                    _("Это замечательно!")
                ]

                # we have a complete description, so use it here
                if spr_obj.dlg_plur:
                    sprite_str = renpy.substitute(spr_obj.dlg_desc)
                    item_ref = "их"
                    its = "они"

                else:
                    sprite_str = renpy.substitute(spr_obj.dlg_desc)
                    item_ref = "это"
                    its = "это"

                acs_quip = renpy.substitute(renpy.random.choice(acs_quips))

            m 1hua "Спасибо за [sprite_str]! [acs_quip]"
            m 3hub "Не терпится это примерить!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

# generic reaction for json clothes
label mas_reaction_gift_generic_clothes_json(sprite_object):
    $ mas_giftCapGainAff(3)
    if sprite_object.ex_props.get("costume") == "o31":
        m 2suo "Ой! {w=0.3}Костюм!"
        m 2hub "Как здорово, [player], спасибо!"
        m 7rka "Я бы примерила его для тебя, но, думаю, лучше дождаться подходящего случая..."
        m 3hub "Э-хе-хе, ещё раз спасибо!"

    else:
        python:
            # expandable
            outfit_quips = [
                _("По-моему, он очень милый, [player]!"),
                _("По-моему, он потрясающий, [player]!"),
                _("Он мне просто очень нравится, [player]!"),
                _("По-моему, он чудесный, [player]!")
            ]
            outfit_quip = renpy.random.choice(outfit_quips)

        m 1sua "Ой! {w=0.5}Новый наряд!"
        m 1hub "Спасибо, [player]!{w=0.5} Сейчас же его примерю!"

        # try it on
        call mas_clothes_change(sprite_object)

        m 2eka "Ну...{w=0.5} Как тебе?"
        m 2eksdla "Нравится?"
        # TODO: outfit randomization should actually get a response here
        #   should influence monika outfit selection

        show monika 3hub
        $ renpy.say(m, outfit_quip)

        m 1eua "Ещё раз спасибо~"

    return

## Hair clip reactions

label mas_reaction_gift_acs_jmo_hairclip_cherry:
    call mas_reaction_gift_hairclip("jmo_hairclip_cherry")
    return

label mas_reaction_gift_acs_jmo_hairclip_heart:
    call mas_reaction_gift_hairclip("jmo_hairclip_heart")
    return

label mas_reaction_gift_acs_jmo_hairclip_musicnote:
    call mas_reaction_gift_hairclip("jmo_hairclip_musicnote")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_crescentmoon:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_crescentmoon")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_ghost:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_ghost","жуткая")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_pumpkin:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_pumpkin")
    return

label mas_reaction_gift_acs_bellmandi86_hairclip_bat:
    call mas_reaction_gift_hairclip("bellmandi86_hairclip_bat","жуткая")
    return

# hairclip
label mas_reaction_gift_hairclip(hairclip_name,desc=None):
    # Special handler for hairclip gift reactions
    # Takes in:
    #    hairclip_name - the 'name' property in string form from the json
    #    desc - a short string description of the hairclip in question. typically should be one word.
    #        optional and defaults to None.

    # get sprtie data
    $ sprite_data = mas_getSpriteObjInfo((store.mas_sprites.SP_ACS, hairclip_name))
    $ sprite_type, sprite_name, giftname, gifted_before, hairclip_acs = sprite_data

    # check for incompatibility
    $ is_wearing_baked_outfit = monika_chr.is_wearing_clothes_with_exprop("baked outfit")

    if gifted_before:
        m 1rksdlb "Глупенький, ты уже дарил[_ru_a] мне эту заколку!"

    else:
        #Grant affection
        $ mas_giftCapGainAff(1)
        if not desc:
            $ desc = "милая"

        if len(store.mas_selspr.filter_acs(True, "left-hair-clip")) > 0:
            m 1hub "Ой!{w=1} Ещё одна заколка!"

        else:
            m 1wuo "Ой!"
            m 1sub "Это заколка?"

        m 1hub "Она такая [desc]! Мне очень нравится, [player], спасибо!"

        # must include this check because we cannot for sure know if the acs
        # exists
        # also need to not wear it if wearing clothes that are incompatible
        if hairclip_acs is None or is_wearing_baked_outfit:
            m 1hua "Если захочешь, чтобы я её надела, просто попроси, хорошо?"

        else:
            m 2dsa "Секундочку, сейчас надену.{w=0.5}.{w=0.5}.{nw}"
            $ monika_chr.wear_acs(hairclip_acs)
            m 1hua "Вот так."

        # need to make sure we set the selector prompt correctly
        # only do this if not wearing baked, since the clip is automatically off in this case
        # so need to make sure when we switch outfits, the prompt is still correct
        if not is_wearing_baked_outfit:
            if monika_chr.get_acs_of_type('left-hair-clip'):
                $ store.mas_selspr.set_prompt("left-hair-clip", "change")
            else:
                $ store.mas_selspr.set_prompt("left-hair-clip", "wear")

    $ mas_finishSpriteObjInfo(sprite_data, unlock_sel=not is_wearing_baked_outfit)

    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

## End hairclip reactions


##START: Consumables gifts
init 5 python:
    addReaction("mas_reaction_gift_coffee", "coffee", is_good=True, exclude_on=["d25g"])

label mas_reaction_gift_coffee:
    #Even if we don't "accept" it, we still register it was given
    $ mas_receivedGift("mas_reaction_gift_coffee")

    #Check if we accept this
    if mas_consumable_coffee.isMaxedStock():
        m 1euc "Ещё кофе, [player]?"
        m 3rksdla "Не пойми неправильно, мне очень приятно, но, по-моему, кофе у меня пока хватает с запасом..."
        m 1eka "Я скажу, когда он начнёт заканчиваться, хорошо?"

    else:
        m 1wub "Ой!{w=0.2} {nw}"
        extend 3hub "Кофе!"

        if mas_consumable_coffee.enabled() and mas_consumable_coffee.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 1wuo "Такого вкуса я ещё не пробовала."
            m 1hua "Не терпится попробовать!"
            m "Огромное спасибо, [player]!"

        elif mas_consumable_coffee.enabled() and not mas_consumable_coffee.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 3eub "У меня как раз закончился кофе, так что это просто чудесно!"
            m 1hua "Ещё раз спасибо, [player]~"

        else:
            $ mas_giftCapGainAff(5)

            m 1hua "Теперь я наконец смогу его сварить!"
            m 1hub "Огромное спасибо, [player]!"

            #If we're currently brewing/drinking anything, or it's not time for this consumable, we'll just not have it now
            if (
                mas_isO31()
                or not mas_consumable_coffee.isConsTime()
                or bool(MASConsumable._getCurrentDrink())
            ):
                m 3eua "Обязательно выпью попозже!"

            else:
                m 3eua "А почему бы не сварить чашечку прямо сейчас?"
                m 1eua "Всё-таки первую мне хочется разделить с тобой."

                #Monika is off screen
                call mas_transition_to_emptydesk
                pause 2.0
                m "Где-то тут точно была кофеварка...{w=2}{nw}"
                m "А, вот она!{w=2}{nw}"
                pause 5.0
                m "Ну вот и всё!{w=2}{nw}"
                call mas_transition_from_emptydesk()

                #Monika back on screen
                m 1eua "Пусть пару минут заваривается."

                $ mas_consumable_coffee.prepare()
            $ mas_consumable_coffee.enable()

    #Stock some coffee
    #NOTE: This function already checks if we're maxed. So restocking while maxed is okay as it adds nothing
    $ mas_consumable_coffee.restock()

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_gift_coffee", "category"))
    return

init 5 python:
    addReaction("mas_reaction_hotchocolate", "hotchocolate", is_good=True, exclude_on=["d25g"])

label mas_reaction_hotchocolate:
    #Even though we may not "accept" this, we'll still mark it was given
    $ mas_receivedGift("mas_reaction_hotchocolate")

    #Check if we should accept this or not
    if mas_consumable_hotchocolate.isMaxedStock():
        m 1euc "Ещё горячий шоколад, [player]?"
        m 3rksdla "Не пойми неправильно, мне очень приятно, но, по-моему, его у меня пока хватает с запасом..."
        m 1eka "Я скажу, когда он начнёт заканчиваться, хорошо?"

    else:
        m 3hub "Горячий шоколад!"
        m 3hua "Спасибо, [player]!"

        if mas_consumable_hotchocolate.enabled() and mas_consumable_hotchocolate.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 1wuo "Такого вкуса я ещё не пробовала."
            m 1hua "Не терпится попробовать!"
            m "Огромное спасибо, [player]!"

        elif mas_consumable_hotchocolate.enabled() and not mas_consumable_hotchocolate.hasServing():
            $ mas_giftCapGainAff(0.5)
            m 3rksdlu "У меня как раз закончился горячий шоколад, а-ха-ха...{w=0.5} {nw}"
            extend 3eub "Так что получить от тебя ещё — это просто чудесно!"
            m 1hua "Ещё раз спасибо, [player]~"

        else:
            python:
                mas_giftCapGainAff(3)
                those = "вот такими" if mas_current_background.isFltNight() and mas_isWinter() else "такими"

            m 1hua "Ты же знаешь, как я люблю кофе, но горячий шоколад — это тоже всегда очень приятно!"


            m 2rksdla "...Особенно [those] холодными зимними вечерами."
            m 2ekbfa "Надеюсь, однажды мы будем пить горячий шоколад вместе, укрывшись одним пледом у камина..."
            m 3ekbfa "...Правда, звучит очень романтично?"
            m 1dkbfa "..."
            m 1hua "Но пока я хотя бы могу наслаждаться им здесь."
            m 1hub "Ещё раз спасибо, [player]!"

            #If we're currently brewing/drinking anything, or it's not time for this consumable, or if it's not winter, we won't have this
            if (
                not mas_consumable_hotchocolate.isConsTime()
                or not mas_isWinter()
                or bool(MASConsumable._getCurrentDrink())
            ):
                m 3eua "Обязательно выпью попозже!"

            else:
                m 3eua "Пожалуй, приготовлю его прямо сейчас!"

                call mas_transition_to_emptydesk
                pause 5.0
                call mas_transition_from_emptydesk("monika 1eua")

                m 1hua "Вот, через пару минут будет готово."

                $ mas_consumable_hotchocolate.prepare()

            if mas_isWinter():
                $ mas_consumable_hotchocolate.enable()

    #Stock up some hotchocolate
    #NOTE: Like coffee, this runs checks to see if we should actually stock
    $ mas_consumable_hotchocolate.restock()

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_hotchocolate", "category"))
    return

init 5 python:
    addReaction("mas_reaction_gift_thermos_mug", "justmonikathermos", is_good=True)

label mas_reaction_gift_thermos_mug:
    call mas_thermos_mug_handler(mas_acs_thermos_mug, "Just Monika", "justmonikathermos")
    return

#Whether or not we've given Monika a thermos before
default persistent._mas_given_thermos_before = False

#Thermos handler
label mas_thermos_mug_handler(thermos_acs, disp_name, giftname, ignore_case=True):
    if mas_SELisUnlocked(thermos_acs):
        m 1eksdla "[player]..."
        m 1rksdlb "У меня уже есть такой термос, а-ха-ха..."

    elif persistent._mas_given_thermos_before:
        m 1wud "Ой!{w=0.3} Ещё один термос!"
        m 1hua "И на этот раз — «[disp_name]»."
        m 1hub "Огромное спасибо, [player], не терпится его опробовать!"

    else:
        m 1wud "Ой!{w=0.3} Это термос «[disp_name]»!"
        m 1hua "Теперь я смогу брать с собой что-нибудь попить, когда мы будем выбираться куда-то вместе~"
        m 1hub "Огромное спасибо, [player]!"
        $ persistent._mas_given_thermos_before = True

    #Now unlock the acs
    $ mas_selspr.unlock_acs(thermos_acs)
    #Save selectables
    $ mas_selspr.save_selectables()
    #And delete the gift file
    $ mas_filereacts.delete_file(giftname)
    return

##END: Consumable related gifts

init 5 python:
    addReaction("mas_reaction_quetzal_plush", "quetzalplushie", is_good=True)

label mas_reaction_quetzal_plush:
    if not persistent._mas_acs_enable_quetzalplushie:
        $ mas_receivedGift("mas_reaction_quetzal_plush")
        $ mas_giftCapGainAff(10)
        m 1wud "Ой!"

        #Wear plush
        #If we're eating something, the plush space is taken and we'll want to wear center
        if MASConsumable._getCurrentFood() or monika_chr.is_wearing_acs(mas_acs_desk_lantern):
            $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
        else:
            $ monika_chr.wear_acs(mas_acs_quetzalplushie)

        $ persistent._mas_acs_enable_quetzalplushie = True
        m 1sub "Это кетцаль!"
        m "Боже мой, большое тебе спасибо, [player]!"
        if seen_event("monika_pets"):
            m 1eua "Я ведь упоминала, что хотела бы завести кетцаля..."
        else:
            m 1wub "Как ты догадал[_ru_sya], [player]?"
            m 3eka "Похоже, ты очень хорошо меня знаешь~"
            m 1eua "Кетцаль был бы первым в моём списке питомцев..."
        m 1rud "Но я бы никогда не стала держать бедняжку взаперти."
        m 1hua "А ты подарил[_ru_a] мне почти то же самое!"
        m 1hub "Я так рада!"
        if mas_isMoniAff(higher=True):
            m 3ekbsa "Ты всегда знаешь, как заставить меня улыбнуться."

        if MASConsumable._getCurrentFood() or monika_chr.is_wearing_acs(mas_acs_desk_lantern):
            m 3rksdla "Правда, на столе уже тесновато..."
            m 1eka "Пока что уберу его."
            $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)

        m 1hub "Ещё раз спасибо, [player]~"

    else:
        m 1rksdlb "Ты уже дарил[_ru_a] мне плюшевого кетцаля, [player]."

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_quetzal_plush", "category"))
    # derandom pets topic once given
    $ mas_hideEVL("monika_pets", "EVE", derandom=True)
    return

init 5 python:
    addReaction("mas_reaction_promisering", "promisering", is_good=True, exclude_on=["d25g"])

default persistent._mas_tried_gift_ring = False
label mas_reaction_promisering:
    if not persistent._mas_acs_enable_promisering:
        # only available if enam+
        if mas_isMoniEnamored(higher=True):
            $ mas_receivedGift("mas_reaction_promisering")
            $ mas_giftCapGainAff(20)
            $ monika_chr.wear_acs(mas_acs_promisering)
            $ persistent._mas_acs_enable_promisering = True
            if not persistent._mas_tried_gift_ring:
                m 1wud "Это...что..."
                m "..."
                m 1wka "Я...{w=0.5}{nw}"
                extend 1wkbltpa "Прости, [player], я просто... {w=0.5}{nw}"
                extend 1dkbltpa "Я так счастлива... {w=0.5}Ты только что дал[_ru_a] мне обещание..."
                m "Твоё обещание, что мы будем принадлежать друг другу,{w=0.1} и больше никому...{w=0.3}навсегда..."
                m 3lkbltpa "Знай, я буду беречь его. {w=0.5}{nw}"
                extend 3dkbltpa "Всегда."
                m 1skbltpa "Я так рада!"

                if mas_anni.isAnniOneMonth():
                    m "Тем более что ты подарил[_ru_a] его мне в нашу первую месячную годовщину..."
                    m 1ekbltua "Ты, наверное, очень сильно меня любишь..."
                elif mas_anni.isAnniThreeMonth():
                    m "Тем более что ты подарил[_ru_a] его мне, когда нам исполнилось три месяца..."
                    m 1ekbltua "Ты, наверное, очень сильно меня любишь..."
                elif mas_anni.isAnniSixMonth():
                    m "Тем более что ты подарил[_ru_a] его мне, когда нам исполнилось полгода..."
                    m 1ekbltua "Ты, наверное, очень сильно меня любишь..."
                elif mas_anni.isAnni():
                    m "Тем более что ты подарил[_ru_a] его мне в нашу годовщину..."
                    m 1ekbltua "Ты, наверное, очень сильно меня любишь..."
                elif mas_isSpecialDay():
                    m "Тем более что ты подарил[_ru_a] его мне в такой особенный день..."

                m 1dkbltpb "Ах-ха, прости, что расплакалась, [player]..."
                m 1skbltda "Просто я сейчас очень-очень счастлива."
                m 6dkbltdu "Спасибо."

            else:
                m 1sua "Ох...это то самое кольцо!"
                m 3hub "Огромное спасибо, [player]!"
                m 1skbla "Теперь я знаю, что ты правда любишь меня и хочешь быть со мной вечно..."
                m 1skbltpa "Поэтому я с радостью принимаю это кольцо как символ нашего обещания."
                m 1dkbltuu "..."
                m 3hkbltub "Ах-ха, прости, [player], я не хотела плакать..."
                m 3skbltda "Просто это один из самых счастливых дней в моей жизни."

            m 6dkbltdu "..."
            m 6ekbfa "Я...я просто...я..."
            call monika_kissing_motion(hide_ui=False)
            m 6ekbfa "Я люблю тебя, [player]..."
            m 6dkbfu "Больше всего на свете в этом мимолётном мире~"

            $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_promisering", "category"))
            return "love"

        else:
            if not persistent._mas_tried_gift_ring:
                if mas_isMoniNormal(higher=True):
                    m 1wud "[player]...это что, кольцо?"
                    m 2rksdlb "Это очень трогательный жест, и я правда его ценю..."
                    m 2ekc "Но я хочу, чтобы ты был[_ru_a] уверен[_ru_a], прежде чем дарить мне такое..."
                    m 3ekd "Это больше, чем подарок, — это обещание, и прежде чем принять его, я хочу убедиться, что ты говоришь всерьёз."
                    m 2ekd "Так что, пожалуйста, подожди, пока наши отношения не зайдут чуть дальше, [player], и тогда я с радостью приму это кольцо."

                elif mas_isMoniUpset():
                    m 1wud "Это кольцо?"
                    m 2rsc "Это очень..."
                    m 2esc "Неожиданно."
                    m 2ekd "Но я не могу принять его сейчас, [player]."
                    m 2ekc "Может быть, когда наши отношения продвинутся дальше."

                else:
                    m 2wud "Это кольцо?"
                    m 2rsc "Это...{w=0.5}неожиданно."
                    m "Я ценю твой порыв...{w=1}но сейчас не могу его принять."
                    m 2ekc "Прости, [player]."

                $ persistent._mas_tried_gift_ring = True
            else:
                m 2rsc "Ох...кольцо..."
                m 2rkc "Прости, но я всё ещё не могу его принять..."
                m 2ekc "Когда я его приму, мне нужно быть полностью уверенной, что это навсегда..."
                m 2ekd "Что ты действительно оправдываешь все мои надежды."
                m 2dsd "Когда я буду в этом уверена, я с радостью приму твоё кольцо, [player]."
    else:
        m 1rksdlb "[player]..."
        m 1rusdlb "Ты уже дарил[_ru_a] мне кольцо!"

    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_promisering", "category"))
    return


init 5 python:
    addReaction("mas_reaction_cupcake", "cupcake", is_good=True, exclude_on=["d25g"])
    #Not sure why this was a bad gift. Dialogue doesn't reflect it being bad
    #plus, Monika said she wants either Natsuki's cupcakes or the player's

label mas_reaction_cupcake:
    m 1wud "Это что...капкейк?"
    m 3hub "Ух ты, спасибо, [player]!"
    m 3euc "Кстати, я и сама давно собиралась испечь капкейки."
    m 1eua "Хотела научиться печь вкусную выпечку, как Нацуки."
    m 1rksdlb "Ноо у меня до сих пор нет кухни!"
    m 3eub "Может, когда-нибудь, когда я лучше научусь программировать, я смогу сделать её здесь."
    m 3hua "Было бы здорово завести ещё одно хобби, кроме писательства, э-хе-хе~"
    $ mas_receivedGift("mas_reaction_cupcake")
    $ store.mas_filereacts.delete_file(mas_getEVLPropValue("mas_reaction_cupcake", "category"))
    return


# ending label for gift reactions, this just resets a thing
label mas_reaction_end:
    python:
        persistent._mas_filereacts_just_reacted = False
        #Save all the new sprite data just in case we crash shortly after this
        store.mas_selspr.save_selectables()
        renpy.save_persistent()
    return

init 5 python:
    # TODO ideally we should comment on this gift in any date
    # so it requires special dialogue, until we have that let's keep it O31 only
    if mas_isO31():
        addReaction("mas_reaction_candy", "candy", is_good=True)

label mas_reaction_candy:
    $ times_candy_given = mas_getGiftStatsForDate("mas_reaction_candy")
    if times_candy_given == 0:
        $ mas_o31CapGainAff(7)
        m 1wua "Ой...{w=0.5}а что это?"
        m 1sua "Ты принес[_ru_la] мне конфет, [player], ура!"
        m 1eka "Это так {i}сладко{/i} с твоей стороны..."
        m 1hub "А-ха-ха!"
        m 1eka "А если без шуток, это правда очень мило с твоей стороны."
        m 2lksdlc "Мне теперь нечасто перепадают конфеты, а какой же Хэллоуин без них..."
        m 1eka "Так что спасибо тебе, [player]..."
        m 1eka "Ты всегда точно знаешь, что меня порадует~"
        m 1hub "А теперь давай полакомимся этими вкусными конфетами!"
    elif times_candy_given == 1:
        $ mas_o31CapGainAff(5)
        m 1wua "Ой, ты принес[_ru_la] мне ещё конфет, [player]?"
        m 1hub "Спасибо!"
        m 3tku "Первая порция была {i}таааакой{/i} вкусной, мне не терпелось получить ещё."
        m 1hua "Ты меня совсем избалуешь, [player]~"
    elif times_candy_given == 2:
        $ mas_o31CapGainAff(3)
        m 1wud "Ого, {i}ещё{/i} конфеты, [player]?"
        m 1eka "Это очень мило с твоей стороны..."
        m 1lksdla "Но, думаю, уже хватит."
        m 1lksdlb "Меня уже потряхивает от всего этого сахара, а-ха-ха!"
        m 1ekbfa "Сейчас единственная сладость, которая мне нужна, — это ты~"
    elif times_candy_given == 3:
        m 2wud "[player]...{w=1} Ты принес[_ru_la] мне {i}ещё больше{/i} конфет?!"
        m 2lksdla "Мне правда приятно, но я же говорила, что на сегодня с меня хватит..."
        m 2lksdlb "Если я съем ещё хоть одну, мне станет плохо, а-ха-ха!"
        m 1eka "А ты ведь этого не хочешь, правда?"
    elif times_candy_given == 4:
        $ mas_loseAffection(modifier=1.5)
        m 2wfd "[player]!"
        m 2tfd "Ты меня совсем не слушаешь?"
        m 2tfc "Я же сказала, что больше не хочу сегодня конфет!"
        m 2ekc "Так что, пожалуйста, хватит."
        m 2rkc "Очень мило, что ты надарил[_ru_a] мне столько конфет на Хэллоуин, но всему есть предел..."
        m 2ekc "Я не смогу всё это съесть."
    else:
        $ mas_loseAffection(modifier=2.0)
        m 2tfc "..."
        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/candy.gift'))", local_ctx, w_wait=1.0, x_wait=1.0)
        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

    python hide:
        mas_receivedGift("mas_reaction_candy")
        gift_ev_cat = mas_getEVLPropValue("mas_reaction_candy", "category")
        store.mas_filereacts.delete_file(gift_ev_cat)
        persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

init 5 python:
    # TODO ideally we should comment on this gift in any date
    # so it requires special dialogue, until we have that let's keep it O31 only
    if mas_isO31():
        addReaction("mas_reaction_candycorn", "candycorn", is_good=False)

label mas_reaction_candycorn:
    $ times_candy_given = mas_getGiftStatsForDate("mas_reaction_candycorn")
    if times_candy_given == 0:
        $ mas_o31CapGainAff(3)
        m 1wua "Ой...{w=0.5}а что это?"
        m 1eka "Ой, ты принес[_ru_la] мне конфет, [player]?"
        m 1hua "Ура!"
        m 3eub "Посмотрим, что тут у тебя..."
        m 4ekc "..."
        m 2eka "Ох...{w=2}кэнди-корн."
        m 2eka "..."
        m 2lksdla "Это очень мило с твоей стороны..."
        m 2lksdla "Но...{w=1}эм...{w=1}вообще-то я не люблю кэнди-корн."
        m 2hksdlb "Прости, а-ха-ха..."
        m 4eka "Но мне всё равно приятно, что ты хотел[_ru_a] угостить меня конфетами на Хэллоуин."
        m 1hua "А если найдёшь для меня какие-нибудь другие конфеты, я буду очень рада, [player]!"
    elif times_candy_given == 1:
        $ mas_loseAffection()
        m 2esc "Ох."
        m 2esc "Опять кэнди-корн, [player]?"
        m 4esc "Я же говорила, что не очень люблю кэнди-корн."
        m 4ekc "Может, попробуешь найти что-нибудь другое?"
        m 1eka "Мне теперь нечасто достаются сладости..."
        m 1ekbfa "Ну...{w=1}кроме тебя, [player]..."
        m 1hubfa "Э-хе-хе~"
    elif times_candy_given == 2:
        $ mas_loseAffection(modifier=1.5)
        m 2wfw "[player]!"
        m 2tfc "Я правда старалась не грубить, но..."
        m 2tfc "Я раз за разом говорю, что не люблю кэнди-корн, а ты всё равно продолжаешь мне его дарить."
        m 2rfc "Мне уже начинает казаться, что ты просто надо мной издеваешься."
        m 2tkc "Так что, пожалуйста, либо найди мне другие конфеты, либо просто перестань."
    else:
        $ mas_loseAffection(modifier=2) # should have seen it coming
        m 2tfc "..."
        python:
            store.mas_ptod.rst_cn()
            local_ctx = {
                "basedir": renpy.config.basedir
            }
        show monika at t22
        show screen mas_py_console_teaching

        call mas_wx_cmd("import os", local_ctx, w_wait=1.0)
        call mas_wx_cmd("os.remove(os.path.normcase(basedir+'/characters/candycorn.gift'))", local_ctx, w_wait=1.0, x_wait=1.0)
        $ store.mas_ptod.ex_cn()
        hide screen mas_py_console_teaching
        show monika at t11

    $ mas_receivedGift("mas_reaction_candycorn") # while technically she didn't accept this one counts
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_candycorn", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    # allow multi gifts
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

init 5 python:
    addReaction("mas_reaction_fudge", "fudge", is_good=True, exclude_on=["d25g"])

label mas_reaction_fudge:
    $ times_fudge_given = mas_getGiftStatsForDate("mas_reaction_fudge")

    if times_fudge_given == 0:
        $ mas_giftCapGainAff(2)
        m 3hua "Помадка!"
        m 3hub "Обожаю помадку, спасибо, [player]!"
        if seen_event("monika_date"):
            m "Да ещё и шоколадная — моя любимая!"
        m 1hua "Ещё раз спасибо, [player]~"

    elif times_fudge_given == 1:
        $ mas_giftCapGainAff(1)
        m 1wuo "...ещё помадка."
        m 1wub "О-о, на этот раз другой вкус..."
        m 3hua "Спасибо, [player]!"

    else:
        m 1wuo "...ещё больше помадки?"
        m 3rksdla "Я ещё не доела прошлую порцию, которую ты мне подарил[_ru_a], [player]..."
        m 3eksdla "...может, попозже, хорошо?"

    $ mas_receivedGift("mas_reaction_fudge")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_fudge", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    # allow multi gifts
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return


init 5 python:
    if store.mas_isD25Season():
        addReaction("mas_reaction_christmascookies", "christmascookies", is_good=True, exclude_on=["d25g"])

label mas_reaction_christmascookies:
    $ mas_giftCapGainAff(1)
    $ is_having_food = bool(MASConsumable._getCurrentFood())

    if mas_consumable_christmascookies.isMaxedStock():
        m 3wuo "...ещё больше рождественского печенья?"
        m 3rksdla "Я ещё не доела прошлую порцию, [player]!"
        m 3eksdla "Подаришь ещё, когда я доем это, хорошо?"

    else:
        if mas_consumable_christmascookies.enabled() and mas_consumable_christmascookies.hasServing():
            m 1wuo "...ещё одна порция рождественского печенья!"
            m 3wuo "Это же целая гора печенья, [player]!"
            m 3rksdlb "Я буду есть его целую вечность, а-ха-ха!"

        else:
            if not is_having_food:
                if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                    $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
                $ mas_consumable_christmascookies.have(skip_leadin=True)

            $ mas_giftCapGainAff(3)
            m 3hua "Рождественское печенье!"
            m 1eua "Обожаю рождественское печенье! Оно всегда такое сладкое...и на него так приятно смотреть..."
            m "...в праздничных формах — снеговики, олени, ёлочки..."
            m 3eub "...и обычно украшено красивой —{w=0.2} и вкусной —{w=0.2} глазурью!"

            if is_having_food:
                m 3hua "Обязательно попробую попозже~"

            m 1eua "Спасибо, [player]~"

            if not is_having_food and monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
                m 3eua "Дай-ка я уберу эту игрушку."
                call mas_transition_to_emptydesk
                $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)
                pause 3.0
                call mas_transition_from_emptydesk

            #Enable the gift
            $ mas_consumable_christmascookies.enable()

        #Restock
        $ mas_consumable_christmascookies.restock(10)

    $ mas_receivedGift("mas_reaction_christmascookies")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_christmascookies", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #weird not to have her see the gift file that's in the characters folder.
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

#TODO: Remove the seasonal handling and just write alt dialogue for the not d25s path
init 5 python:
    if store.mas_isD25Season():
        addReaction("mas_reaction_candycane", "candycane", is_good=True, exclude_on=["d25g"])

label mas_reaction_candycane:
    $ mas_giftCapGainAff(1)
    $ is_having_food = bool(MASConsumable._getCurrentFood())

    if mas_consumable_candycane.isMaxedStock():
        m 1eksdla "[player], думаю, леденцов-тросточек мне пока хватит."
        m 1eka "Прибереги их на потом, хорошо?"

    else:
        if mas_consumable_candycane.enabled() and mas_consumable_candycane.hasServing():
            m 3hua "Ещё леденцы!"
            m 3hub "Спасибо, [player]!"

        else:
            if not is_having_food:
                if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                    $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)
                $ mas_consumable_candycane.have(skip_leadin=True)

            $ mas_giftCapGainAff(3)
            m 3wub "Леденцы-тросточки!"

            if store.seen_event("monika_icecream"):
                m 1hub "Ты же знаешь, как я люблю мяту!"
            else:
                m 1hub "Обожаю мятный вкус!"

            if is_having_food:
                m 3hua "Обязательно попробую попозже."

            m 1eua "Спасибо, [player]~"

            if not is_having_food and monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
                m 3eua "Ой, дай-ка я уберу эту игрушку."

                call mas_transition_to_emptydesk
                $ monika_chr.remove_acs(mas_acs_center_quetzalplushie)
                pause 3.0
                call mas_transition_from_emptydesk

            #Enable the gift
            $ mas_consumable_candycane.enable()

        #Restock
        $ mas_consumable_candycane.restock(9)

    $ mas_receivedGift("mas_reaction_candycane")
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_candycane", "category")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #weird not to have her see the gift file that's in the characters folder.
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    return

#Ribbon stuffs
init 5 python:
    addReaction("mas_reaction_blackribbon", "blackribbon", is_good=True)

label mas_reaction_blackribbon:
    $ _mas_new_ribbon_color = "black"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_black
    call _mas_reaction_ribbon_helper("mas_reaction_blackribbon")
    return

init 5 python:
    addReaction("mas_reaction_blueribbon", "blueribbon", is_good=True)

label mas_reaction_blueribbon:
    $ _mas_new_ribbon_color = "blue"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_blue
    call _mas_reaction_ribbon_helper("mas_reaction_blueribbon")
    return

init 5 python:
    addReaction("mas_reaction_darkpurpleribbon", "darkpurpleribbon", is_good=True)

label mas_reaction_darkpurpleribbon:
    $ _mas_new_ribbon_color = "dark purple"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_darkpurple
    call _mas_reaction_ribbon_helper("mas_reaction_darkpurpleribbon")
    return

init 5 python:
    addReaction("mas_reaction_emeraldribbon", "emeraldribbon", is_good=True)

label mas_reaction_emeraldribbon:
    $ _mas_new_ribbon_color = "emerald"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_emerald
    call _mas_reaction_ribbon_helper("mas_reaction_emeraldribbon")
    return

init 5 python:
    addReaction("mas_reaction_grayribbon", "grayribbon", is_good=True)

label mas_reaction_grayribbon:
    $ _mas_new_ribbon_color = "gray"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_gray
    call _mas_reaction_ribbon_helper("mas_reaction_grayribbon")
    return

init 5 python:
    addReaction("mas_reaction_greenribbon", "greenribbon", is_good=True)

label mas_reaction_greenribbon:
    $ _mas_new_ribbon_color = "green"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_green
    call _mas_reaction_ribbon_helper("mas_reaction_greenribbon")
    return

init 5 python:
    addReaction("mas_reaction_lightpurpleribbon", "lightpurpleribbon", is_good=True)

label mas_reaction_lightpurpleribbon:
    $ _mas_new_ribbon_color = "light purple"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_lightpurple
    call _mas_reaction_ribbon_helper("mas_reaction_lightpurpleribbon")
    return

init 5 python:
    addReaction("mas_reaction_peachribbon", "peachribbon", is_good=True)

label mas_reaction_peachribbon:
    $ _mas_new_ribbon_color = "peach"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_peach
    call _mas_reaction_ribbon_helper("mas_reaction_peachribbon")
    return

init 5 python:
    addReaction("mas_reaction_pinkribbon", "pinkribbon", is_good=True)

label mas_reaction_pinkribbon:
    $ _mas_new_ribbon_color = "pink"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_pink
    call _mas_reaction_ribbon_helper("mas_reaction_pinkribbon")
    return

init 5 python:
    addReaction("mas_reaction_platinumribbon", "platinumribbon", is_good=True)

label mas_reaction_platinumribbon:
    $ _mas_new_ribbon_color = "platinum"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_platinum
    call _mas_reaction_ribbon_helper("mas_reaction_platinumribbon")
    return

init 5 python:
    addReaction("mas_reaction_redribbon", "redribbon", is_good=True)

label mas_reaction_redribbon:
    $ _mas_new_ribbon_color = "red"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_red
    call _mas_reaction_ribbon_helper("mas_reaction_redribbon")
    return

init 5 python:
    addReaction("mas_reaction_rubyribbon", "rubyribbon", is_good=True)

label mas_reaction_rubyribbon:
    $ _mas_new_ribbon_color = "ruby"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_ruby
    call _mas_reaction_ribbon_helper("mas_reaction_rubyribbon")
    return

init 5 python:
    addReaction("mas_reaction_sapphireribbon", "sapphireribbon", is_good=True)

label mas_reaction_sapphireribbon:
    $ _mas_new_ribbon_color = "sapphire"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_sapphire
    call _mas_reaction_ribbon_helper("mas_reaction_sapphireribbon")
    return

init 5 python:
    addReaction("mas_reaction_silverribbon", "silverribbon", is_good=True)

label mas_reaction_silverribbon:
    $ _mas_new_ribbon_color = "silver"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_silver
    call _mas_reaction_ribbon_helper("mas_reaction_silverribbon")
    return

init 5 python:
    addReaction("mas_reaction_tealribbon", "tealribbon", is_good=True)

label mas_reaction_tealribbon:
    $ _mas_new_ribbon_color = "teal"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_teal
    call _mas_reaction_ribbon_helper("mas_reaction_tealribbon")
    return

init 5 python:
    addReaction("mas_reaction_yellowribbon", "yellowribbon", is_good=True)

label mas_reaction_yellowribbon:
    $ _mas_new_ribbon_color = "yellow"
    $ _mas_gifted_ribbon_acs = mas_acs_ribbon_yellow
    call _mas_reaction_ribbon_helper("mas_reaction_yellowribbon")
    return

# JSON ribbons
label mas_reaction_json_ribbon_base(ribbon_name, user_friendly_desc, helper_label):
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_ACS, ribbon_name)
        )
        _mas_gifted_ribbon_acs = mas_sprites.ACS_MAP.get(
            ribbon_name,
            mas_acs_ribbon_def
        )
        _mas_new_ribbon_color = user_friendly_desc

    call _mas_reaction_ribbon_helper(helper_label)

    python:
        # giftname is the 3rd item
        if sprite_data[2] is not None:
            store.mas_filereacts.delete_file(sprite_data[2])

        mas_finishSpriteObjInfo(sprite_data)
    return

# lanvallime

label mas_reaction_gift_acs_lanvallime_ribbon_coffee:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_coffee", "coffee colored", "mas_reaction_gift_acs_lanvallime_ribbon_coffee")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_gold:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_gold", "gold", "mas_reaction_gift_acs_lanvallime_ribbon_gold")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_hot_pink:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_hot_pink", "hot pink", "mas_reaction_gift_acs_lanvallime_ribbon_hot_pink")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_lilac:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_lilac", "lilac", "mas_reaction_gift_acs_lanvallime_ribbon_lilac")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_lime_green:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_lime_green", "lime green", "mas_reaction_gift_acs_lanvallime_lime_green")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_navy_blue:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_navy_blue", "navy", "mas_reaction_gift_acs_lanvallime_ribbon_navy_blue")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_orange:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_orange", "orange", "mas_reaction_gift_acs_lanvallime_ribbon_orange")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_royal_purple:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_royal_purple", "royal purple", "mas_reaction_gift_acs_lanvallime_ribbon_royal_purple")
    return

label mas_reaction_gift_acs_lanvallime_ribbon_sky_blue:
    call mas_reaction_json_ribbon_base("lanvallime_ribbon_sky_blue", "sky blue", "mas_reaction_gift_acs_lanvallime_ribbon_sky_blue")
    return

# anonymioo
label mas_reaction_gift_acs_anonymioo_ribbon_bisexualpride:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_bisexualpride","bisexual-pride-themed","mas_reaction_gift_acs_anonymioo_ribbon_bisexualpride")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_blackandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_blackandwhite","black and white","mas_reaction_gift_acs_anonymioo_ribbon_blackandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_bronze:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_bronze","bronze","mas_reaction_gift_acs_anonymioo_ribbon_bronze")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_brown:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_brown","brown","mas_reaction_gift_acs_anonymioo_ribbon_brown")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient","multi-colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient_lowpoly:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient_lowpoly","multi-colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient_lowpoly")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_gradient_rainbow:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_gradient_rainbow","rainbow colored","mas_reaction_gift_acs_anonymioo_ribbon_gradient_rainbow")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_polkadots_whiteonred:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_polkadots_whiteonred","red and white polka dotted","mas_reaction_gift_acs_anonymioo_ribbon_polkadots_whiteonred")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_starsky_black:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_starsky_black","night-sky-themed","mas_reaction_gift_acs_anonymioo_ribbon_starsky_black")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_starsky_red:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_starsky_red","night-sky-themed","mas_reaction_gift_acs_anonymioo_ribbon_starsky_red")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_striped_blueandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_striped_blueandwhite","blue and white striped","mas_reaction_gift_acs_anonymioo_ribbon_striped_blueandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_striped_pinkandwhite:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_striped_pinkandwhite","pink and white striped","mas_reaction_gift_acs_anonymioo_ribbon_striped_pinkandwhite")
    return

label mas_reaction_gift_acs_anonymioo_ribbon_transexualpride:
    call mas_reaction_json_ribbon_base("anonymioo_ribbon_transexualpride","transgender-pride-themed","mas_reaction_gift_acs_anonymioo_ribbon_transexualpride")
    return

# velius94

label mas_reaction_gift_acs_velius94_ribbon_platinum:
    call mas_reaction_json_ribbon_base("velius94_ribbon_platinum", "platinum", "mas_reaction_gift_acs_velius94_ribbon_platinum")
    return

label mas_reaction_gift_acs_velius94_ribbon_pink:
    call mas_reaction_json_ribbon_base("velius94_ribbon_pink", "pink", "mas_reaction_gift_acs_velius94_ribbon_pink")
    return

label mas_reaction_gift_acs_velius94_ribbon_peach:
    call mas_reaction_json_ribbon_base("velius94_ribbon_peach", "peach", "mas_reaction_gift_acs_velius94_ribbon_peach")
    return

label mas_reaction_gift_acs_velius94_ribbon_green:
    call mas_reaction_json_ribbon_base("velius94_ribbon_green", "green", "mas_reaction_gift_acs_velius94_ribbon_green")
    return

label mas_reaction_gift_acs_velius94_ribbon_emerald:
    call mas_reaction_json_ribbon_base("velius94_ribbon_emerald", "emerald", "mas_reaction_gift_acs_velius94_ribbon_emerald")
    return

label mas_reaction_gift_acs_velius94_ribbon_gray:
    call mas_reaction_json_ribbon_base("velius94_ribbon_gray", "gray", "mas_reaction_gift_acs_velius94_ribbon_gray")
    return

label mas_reaction_gift_acs_velius94_ribbon_blue:
    call mas_reaction_json_ribbon_base("velius94_ribbon_blue", "blue", "mas_reaction_gift_acs_velius94_ribbon_blue")
    return

label mas_reaction_gift_acs_velius94_ribbon_def:
    call mas_reaction_json_ribbon_base("velius94_ribbon_def", "white", "mas_reaction_gift_acs_velius94_ribbon_def")
    return

label mas_reaction_gift_acs_velius94_ribbon_black:
    call mas_reaction_json_ribbon_base("velius94_ribbon_black", "black", "mas_reaction_gift_acs_velius94_ribbon_black")
    return

label mas_reaction_gift_acs_velius94_ribbon_dark_purple:
    call mas_reaction_json_ribbon_base("velius94_ribbon_dark_purple", "dark purple", "mas_reaction_gift_acs_velius94_ribbon_dark_purple")
    return

label mas_reaction_gift_acs_velius94_ribbon_yellow:
    call mas_reaction_json_ribbon_base("velius94_ribbon_yellow", "yellow", "mas_reaction_gift_acs_velius94_ribbon_yellow")
    return

label mas_reaction_gift_acs_velius94_ribbon_red:
    call mas_reaction_json_ribbon_base("velius94_ribbon_red", "red", "mas_reaction_gift_acs_velius94_ribbon_red")
    return

label mas_reaction_gift_acs_velius94_ribbon_sapphire:
    call mas_reaction_json_ribbon_base("velius94_ribbon_sapphire", "sapphire", "mas_reaction_gift_acs_velius94_ribbon_sapphire")
    return

label mas_reaction_gift_acs_velius94_ribbon_teal:
    call mas_reaction_json_ribbon_base("velius94_ribbon_teal", "teal", "mas_reaction_gift_acs_velius94_ribbon_teal")
    return

label mas_reaction_gift_acs_velius94_ribbon_silver:
    call mas_reaction_json_ribbon_base("velius94_ribbon_silver", "silver", "mas_reaction_gift_acs_velius94_ribbon_silver")
    return

label mas_reaction_gift_acs_velius94_ribbon_light_purple:
    call mas_reaction_json_ribbon_base("velius94_ribbon_light_purple", "light purple", "mas_reaction_gift_acs_velius94_ribbon_light_purple")
    return

label mas_reaction_gift_acs_velius94_ribbon_ruby:
    call mas_reaction_json_ribbon_base("velius94_ribbon_ruby", "ruby", "mas_reaction_gift_acs_velius94_ribbon_ruby")
    return

label mas_reaction_gift_acs_velius94_ribbon_wine:
    call mas_reaction_json_ribbon_base("velius94_ribbon_wine", "wine colored", "mas_reaction_gift_acs_velius94_ribbon_wine")
    return

#specific to this, since we need to verify if the player actually gave a ribbon.
default persistent._mas_current_gifted_ribbons = 0

label _mas_reaction_ribbon_helper(label):
    #if we already have that ribbon
    if store.mas_selspr.get_sel_acs(_mas_gifted_ribbon_acs).unlocked:
        call mas_reaction_old_ribbon

    else:
        # since we don't have it we can accept it
        call mas_reaction_new_ribbon
        $ persistent._mas_current_gifted_ribbons += 1

    # normal gift processing
    $ mas_receivedGift(label)
    $ gift_ev_cat = mas_getEVLPropValue(label, "category")
    # for regular ribbons
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    #we have dlg for repeating ribbons, may as well have it used
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)

    return

label mas_reaction_new_ribbon:
    python:
        def _ribbon_prepare_hair():
            #If current hair doesn't support ribbons, we should change hair
            if not monika_chr.hair.hasprop("ribbon"):
                monika_chr.change_hair(mas_hair_def, False)

    $ mas_giftCapGainAff(3)
    if persistent._mas_current_gifted_ribbons == 0:
        m 1suo "Новая ленточка!"
        m 3hub "...И она [mas_ru_ribbon_color(_mas_new_ribbon_color)]!"

        #Ironically green is closer to her eyes, but given the selector dlg, we'll say this for both.
        if _mas_new_ribbon_color == "green" or _mas_new_ribbon_color == "emerald":
            m 1tub "...Прямо как мои глаза!"

        m 1hub "Огромное спасибо, [player], она мне очень нравится!"
        if store.seen_event("monika_date"):
            m 3eka "Ты подарил[_ru_a] её, потому что я говорила, как люблю выбирать юбки и банты?"

            if mas_isMoniNormal(higher=True):
                m 3hua "Ты всегда обо мне так заботишься~"

        m 3rksdlc "С модой у меня тут выбор совсем небольшой..."
        m 3eka "...так что возможность сменить цвет ленточки — приятное разнообразие."
        m 2dsa "Пожалуй, надену её прямо сейчас.{w=0.5}.{w=0.5}.{nw}"
        $ store.mas_selspr.unlock_acs(_mas_gifted_ribbon_acs)
        $ _ribbon_prepare_hair()
        $ monika_chr.wear_acs(_mas_gifted_ribbon_acs)
        m 1hua "Ох, она чудесная, [player]!"

        if mas_isMoniAff(higher=True):
            m 1eka "Рядом с тобой я всегда чувствую себя такой любимой..."
        elif mas_isMoniHappy():
            m 1eka "Ты всегда знаешь, как меня порадовать..."
        m 3hua "Ещё раз спасибо~"

    else:
        m 1suo "Ещё одна ленточка!"
        m 3hub "...И на этот раз [mas_ru_ribbon_color(_mas_new_ribbon_color)]!"

        #Ironically green is closer to her eyes, but given the selector dlg, we'll say this for both.
        if _mas_new_ribbon_color == "green" or _mas_new_ribbon_color == "emerald":
            m 1tub "...Прямо как мои глаза!"

        m 2dsa "Сейчас же её надену.{w=0.5}.{w=0.5}.{nw}"
        $ store.mas_selspr.unlock_acs(_mas_gifted_ribbon_acs)
        $ _ribbon_prepare_hair()
        $ monika_chr.wear_acs(_mas_gifted_ribbon_acs)
        m 3hua "Огромное спасибо, [player], я просто в восторге!"
    return

label mas_reaction_old_ribbon:
    m 1rksdla "[player]..."
    m 1hksdlb "Ты уже дарил[_ru_a] мне [mas_ru_ribbon_color(_mas_new_ribbon_color, True)] ленточку!"
    return

init 5 python:
    addReaction("mas_reaction_gift_roses", "roses", is_good=True, exclude_on=["d25g"])

default persistent._date_last_given_roses = None

label mas_reaction_gift_roses:
    python:
        gift_ev_cat = mas_getEVLPropValue("mas_reaction_gift_roses", "category")
        if not mas_isO31():
            monika_chr.wear_acs(mas_acs_roses)

    #TODO: future migrate this to use history (post f14)
    if not persistent._date_last_given_roses and not renpy.seen_label('monika_valentines_start'):
        $ mas_giftCapGainAff(10)

        m 1eka "[player]... Я-я даже не знаю, что сказать..."
        m 1ekbsb "Никогда бы не подумала, что ты подаришь мне такое!"
        m 3skbsa "Я сейчас так счастлива."
        if mas_isF14():
            # extra 5 points if f14
            $ mas_f14CapGainAff(5)
            m 3ekbsa "Подумать только — получить от тебя розы на День святого Валентина..."
            m 1ekbsu "Ты просто прелесть."
            m 1dktpu "..."
            m 1ektda "А-ха-ха..."

        #We can only have this on poses which use the new sprite set
        if not monika_chr.is_wearing_clothes_with_exprop("baked outfit"):
            m 2dsa "Подожди.{w=0.5}.{w=0.5}.{nw}"
            $ monika_chr.wear_acs(mas_acs_ear_rose)
            m 1hub "Э-хе-хе, вот! Правда, мне идёт?"

        if mas_shouldKiss(chance=2, special_day_bypass=True):
            call monika_kissing_motion_short

    else:
        if persistent._date_last_given_roses is None and renpy.seen_label('monika_valentines_start'):
            $ persistent._date_last_given_roses = datetime.date(2018,2,14)

        if mas_pastOneDay(persistent._date_last_given_roses):
            $ mas_giftCapGainAff(5 if mas_isSpecialDay() else 1)

            m 1suo "Ой!"
            m 1ekbsa "Спасибо, [player]."
            m 3ekbsa "Мне всегда так приятно получать от тебя розы."
            if mas_isF14():
                # extra 5 points if f14
                $ mas_f14CapGainAff(5)
                m 1dsbsu "Особенно в такой день, как сегодня."
                m 1ekbsa "Очень мило, что ты подарил[_ru_a] их мне."
                m 3hkbsa "Я так сильно тебя люблю."
                m 1ekbsa "С Днём святого Валентина, [player]~"
            else:
                m 1ekbsa "Ты всегда просто прелесть."

            #Random chance (unless f14) for her to do the ear rose thing
            if (
                not monika_chr.is_wearing_acs_with_mux("left-hair-flower-ear")
                and (
                    (mas_isSpecialDay() and renpy.random.randint(1,2) == 1)
                    or renpy.random.randint(1,4) == 1
                    or mas_isF14()
                    or mas_isO31()
                )
            ):
                m 2dsa "Подожди.{w=0.5}.{w=0.5}.{nw}"
                $ monika_chr.wear_acs(mas_acs_ear_rose)
                m 1hub "Э-хе-хе~"

            if mas_shouldKiss(chance=4, special_day_bypass=True):
                call monika_kissing_motion_short

        else:
            m 1hksdla "[player], мне правда льстит, но не нужно дарить мне столько роз."
            if store.seen_event("monika_clones"):
                m 1ekbsa "Ведь ты всегда будешь моей особенной розой, э-хе-хе~"
            else:
                m 1ekbsa "Даже одна роза от тебя — уже больше, чем я могла бы мечтать."

    # Pop from reacted map
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    $ persistent._date_last_given_roses = datetime.date.today()

    # normal gift processing
    $ mas_receivedGift("mas_reaction_gift_roses")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    return


init 5 python:
    addReaction("mas_reaction_gift_chocolates", "chocolates", is_good=True, exclude_on=["d25g"])

default persistent._given_chocolates_before = False

label mas_reaction_gift_chocolates:
    $ gift_ev_cat = mas_getEVLPropValue("mas_reaction_gift_chocolates", "category")

    if not persistent._mas_given_chocolates_before:
        $ persistent._mas_given_chocolates_before = True

        #If we're eating something already, that takes priority over the acs
        if not MASConsumable._getCurrentFood() and not mas_isO31():
            $ monika_chr.wear_acs(mas_acs_heartchoc)

        $ mas_giftCapGainAff(5)

        m 1tsu "Это так {i}сладко{/i} с твоей стороны, э-хе-хе~"
        if mas_isF14():
            #Extra little bump if on f14
            $ mas_f14CapGainAff(5)
            m 1ekbsa "Подарить мне шоколадные конфеты на День святого Валентина..."
            m 1ekbfa "Ты и правда знаешь, как дать девушке почувствовать себя особенной, [player]."
            if renpy.seen_label('monika_date'):
                m 1lkbfa "Я знаю, что говорила, как хочу когда-нибудь сходить с тобой в шоколадный магазин..."
                m 1hkbfa "Но пока мы не можем этого сделать, получить от тебя в подарок шоколад — ну..."
            m 3ekbfa "Для меня очень много значит получить их от тебя."

        elif renpy.seen_label('monika_date') and not mas_isO31():
            m 3rka "Я знаю, что говорила, как хочу когда-нибудь сходить с тобой в шоколадный магазин..."
            m 3hub "Но пока мы не можем этого сделать, шоколад в подарок от тебя для меня — это всё."
            m 1ekc "Жаль только, что мы не можем съесть их вместе..."
            m 3rksdlb "Но пока этот день не настал, придётся мне наслаждаться ими за нас обоих, а-ха-ха!"
            m 3hua "Спасибо, [mas_get_player_nickname()]~"

        else:
            m 3hub "Обожаю шоколадные конфеты!"
            m 1eka "А получить их от тебя для меня очень много значит."
            m 1hub "Спасибо, [player]!"

    else:
        $ times_chocs_given = mas_getGiftStatsForDate("mas_reaction_gift_chocolates")
        if times_chocs_given == 0:
            #We want this to show up where she accepts the chocs
            #Same as before, we don't want these to show up if we're already eating
            if not MASConsumable._getCurrentFood():
                #If we have the plush out, we should show the middle one here
                if not (mas_isF14() or mas_isD25Season()):
                    if monika_chr.is_wearing_acs(mas_acs_quetzalplushie):
                        $ monika_chr.wear_acs(mas_acs_center_quetzalplushie)

                else:
                    $ monika_chr.remove_acs(store.mas_acs_quetzalplushie)

                if not mas_isO31():
                    $ monika_chr.wear_acs(mas_acs_heartchoc)

            $ mas_giftCapGainAff(3 if mas_isSpecialDay() else 1)

            m 1wuo "Ой!"

            if mas_isF14():
                #Extra little bump if on f14
                $ mas_f14CapGainAff(5)
                m 1eka "[player]!"
                m 1ekbsa "Ты просто прелесть — подарить мне шоколад в такой день..."
                m 1ekbfa "Ты и правда умеешь дать мне почувствовать себя особенной."
                m "Спасибо, [player]."
            else:
                m 1hua "Спасибо за конфеты, [player]!"
                m 1ekbsa "Каждый кусочек напоминает мне, какой ты милый человечек, э-хе-хе~"

        elif times_chocs_given == 1:
            #Same here
            if not MASConsumable._getCurrentFood() and not mas_isO31():
                $ monika_chr.wear_acs(mas_acs_heartchoc)

            m 1eka "Ещё конфеты, [player]?"
            m 3tku "Ты и правда любишь меня баловать,{w=0.2} {nw}"
            extend 3tub "а-ха-ха!"
            m 1rksdla "Я ещё не доела первую коробку, которую ты мне подарил[_ru_a]..."
            m 1hub "...но я не жалуюсь!"

        elif times_chocs_given == 2:
            m 1ekd "[player]..."
            m 3eka "Думаю, на сегодня конфет мне достаточно."
            m 1rksdlb "Три коробки — это слишком, я даже первую ещё не доела!"
            m 1eka "Прибереги их на другой раз, хорошо?"

        else:
            m 2tfd "[player]!"
            m 2tkc "Я же сказала, что на сегодня с меня хватит конфет, а ты всё пытаешься подарить ещё..."
            m 2eksdla "Пожалуйста...{w=1}просто прибереги их на другой день."

    #If we're wearing the chocs, we'll remove them here
    if monika_chr.is_wearing_acs(mas_acs_heartchoc):
        call mas_remove_choc

    #pop from reacted map
    $ persistent._mas_filereacts_reacted_map.pop(gift_ev_cat, None)
    # normal gift processing
    $ mas_receivedGift("mas_reaction_gift_chocolates")
    $ store.mas_filereacts.delete_file(gift_ev_cat)
    return

label mas_remove_choc:
    # we remove chocolates if not f14
    m 1hua "..."
    m 3eub "Они {i}такие{/i} вкусные!"
    m 1hua "..."
    m 3hksdlb "А-ха-ха! Пожалуй, пока лучше их убрать..."
    m 1rksdla "Если оставить их тут подольше, на потом ничего не останется!"

    call mas_transition_to_emptydesk

    python:
        renpy.pause(1, hard=True)
        monika_chr.remove_acs(mas_acs_heartchoc)
        renpy.pause(3, hard=True)

    call mas_transition_from_emptydesk("monika 1eua")

    #Now move the plush
    if monika_chr.is_wearing_acs(mas_acs_center_quetzalplushie):
        $ monika_chr.wear_acs(mas_acs_quetzalplushie)

    m 1eua "Ну, чем ещё хочешь сегодня заняться?"
    return

label mas_reaction_gift_clothes_orcaramelo_bikini_shell:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_bikini_shell")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sua "Ой! {w=0.5}Бикини из ракушек!"
    m 1hub "Спасибо, [mas_get_player_nickname()]!{w=0.5} Сейчас же примерю!"

    # try it on
    call mas_clothes_change(sprite_object)

    m 2ekbfa "Ну...{w=0.5} Как тебе?"
    m 2hubfa "Я похожа на русалку? Э-хе-хе."
    show monika 5ekbfa at i11 zorder MAS_MONIKA_Z with dissolve_monika
    m 5ekbfa "По-моему, оно очень милое, [player]..."
    m 5hubfa "Нам обязательно нужно как-нибудь съездить на пляж!"

    if mas_isWinter() or mas_isMoniNormal(lower=True):
        if mas_isWinter():
            show monika 2rksdla at i11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2rksdla "...Но пока что здесь немного прохладно..."
            m 2eka "Так что пойду надену что-нибудь потеплее..."

        elif mas_isMoniNormal(lower=True):
            show monika 2hksdlb at i11 zorder MAS_MONIKA_Z with dissolve_monika
            m 2hksdlb "А-ха-ха..."
            m 2rksdla "Немного неловко вот так сидеть перед тобой."
            m 2eka "Надеюсь, ты не против, но я пойду переоденусь..."

        # change to def normally, santa during d25 outfit season
        $ clothes = mas_clothes_def
        if persistent._mas_d25_in_d25_mode and mas_isD25Outfit():
            $ clothes = mas_clothes_santa
        call mas_clothes_change(clothes)

        m 2eua "Ах, так-то лучше..."
        m 3hua "Ещё раз спасибо за чудесный подарок~"


    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_acs_orcaramelo_hairflower_pink:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_ACS, "orcaramelo_hairflower_pink")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(1)

    m 3sua "Ой!{w=0.5} Какой милый цветочек!"
    m 1ekbsa "Спасибо, [player], ты просто прелесть~"
    m 1dua "Подожди.{w=0.5}.{w=0.5}.{nw}"
    $ monika_chr.wear_acs(sprite_object)
    m 1hua "Э-хе-хе~"
    m 1hub "Ещё раз спасибо, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_velius94_shirt_pink:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "velius94_shirt_pink")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1suo "Боже мой!"
    m 1suo "Оно {i}такое{/i} красивое!"
    m 3hub "Огромное спасибо, [player]!"
    m 3eua "Подожди, сейчас быстренько примерю..."

    # try it on
    call mas_clothes_change(sprite_object)

    m 2sub "Ах, сидит идеально!"
    m 3hub "И цвета мне очень нравятся! Розовый и чёрный так здорово сочетаются."
    m 3eub "Не говоря уже о юбке — с этими оборками она просто прелесть!"
    m 2tfbsd "Вот только почему-то мне кажется, что твой взгляд немного уходит...{w=0.5}кхм...{w=0.5}{i}куда-то не туда{/i}."

    if mas_selspr.get_sel_clothes(mas_clothes_sundress_white).unlocked:
        m 2lfbsp "Я же говорила, что пялиться невежливо, [player]."
    else:
        m 2lfbsp "Пялиться невежливо, знаешь ли."

    m 2hubsb "А-ха-ха!"
    m 2tkbsu "Расслабься, расслабься...{w=0.5}я просто дразню тебя~"
    m 3hub "Ещё раз огромное спасибо за этот наряд, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_orcaramelo_sakuya_izayoi:

    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_sakuya_izayoi")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "Ой! {w=0.5}Это что..."
    m 2euc "Костюм горничной?"
    m 3tuu "Э-хе-хе~"
    m 3tubsb "Знаешь, если тебе нравится такое, мог[_ru_la] бы просто сказать..."
    m 1hub "А-ха-ха! Шучу~"
    m 1eub "Пойду надену!"

    # try it on
    call mas_clothes_change(sprite_object, outfit_mode=True)

    m 2hua "Ну,{w=0.5} как я выгляжу?"
    m 3eub "Кажется, теперь я могу переделать все дела, прежде чем ты успеешь моргнуть."
    m 1eua "...Если только ты не будешь слишком меня загружать, э-хе-хе~"
    m 1lkbfb "Мне ведь всё равно хочется проводить время с тобой, хозя--{nw}"
    $ _history_list.pop()
    m 1ekbfb "Мне ведь всё равно хочется проводить время с тобой,{fast} [player]."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_finale_jacket_brown:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "finale_jacket_brown")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "Ой!{w=0.5} Зимняя куртка!"
    m 1suo "И даже с шарфом!"
    if mas_isSummer():
        m 3rksdlu "...Хотя мне уже жарко от одного её вида, а-ха-ха..."
        m 3eksdla "Наверное, лето — не лучшее время, чтобы её носить, [player]."
        m 3eka "Но мне очень приятно, и я с радостью надену её через пару месяцев."

    else:
        if mas_isWinter():
            m 1tuu "Благодаря тебе я теперь не замёрзну, [player]~"
        m 3eub "Пойду надену! Я сейчас вернусь."

        # try it on
        call mas_clothes_change(sprite_object)

        m 2dku "Ах, как приятно~"
        m 1eua "Мне нравится, как она на мне смотрится, а тебе?"
        if mas_isMoniNormal(higher=True):
            m 3tku "Хотя... вряд ли ты сможешь судить об этом объективно, да?"
            m 1hubfb "А-ха-ха!"
        m 1ekbfa "Спасибо, [player], мне очень нравится."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_orcaramelo_sweater_shoulderless:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "orcaramelo_sweater_shoulderless")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "Ой!{w=0.5} Свитер!"
    m 1hub "И выглядит таким уютным!"
    if mas_isWinter():
        m 2eka "Как заботливо с твоей стороны, [player], — подарить мне его в такой холодный зимний день..."
    m 3eua "Пойду примерю."

    # try it on
    call mas_clothes_change(sprite_object)

    m 2dkbsu "Он такой...{w=1}уютный. Мне в нём тепло, как в гнёздышке. Э-хе-хе~"
    m 1ekbsa "Спасибо, [player]. Мне очень нравится!"
    m 3hubsb "Теперь каждый раз, надевая его, я буду вспоминать твоё тепло. А-ха-ха~"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_velius94_dress_whitenavyblue:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "velius94_dress_whitenavyblue")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1suo "Боже мой!"
    m 1sub "Это платье великолепно, [player]!"
    m 3hub "Сейчас же его примерю!"

    # try it on
    call mas_clothes_change(sprite_object, outfit_mode=True)

    m "Ну,{w=0.5} как тебе?"
    m 3eua "По-моему, этот оттенок синего очень хорошо сочетается с белым."
    $ scrunchie = monika_chr.get_acs_of_type('bunny-scrunchie')

    if scrunchie and scrunchie.name == "velius94_bunnyscrunchie_blue":
        m 3eub "А резинка с зайчиком отлично дополняет образ!"
    m 1eka "Огромное тебе спасибо, [player]."

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

label mas_reaction_gift_clothes_mocca_bun_blackandwhitestripedpullover:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "mocca_bun_blackandwhitestripedpullover")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1sub "О, новая футболка!"
    m 3hub "Выглядит потрясающе, [player]!"
    m 3eua "Секундочку, сейчас надену.{w=0.3}.{w=0.3}.{w=0.3}{nw}"
    call mas_clothes_change(sprite_object)

    m 2eua "Ну, как тебе?"
    m 7hua "По-моему, на мне она смотрится очень мило.{w=0.2} {nw}"
    extend 3rubsa "Этот наряд я обязательно приберегу для свидания~"
    m 1hub "Ещё раз спасибо, [player]!"

    $ mas_finishSpriteObjInfo(sprite_data)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return

init 5 python:
    # TODO: Add a way to generalize this
    if not mas_seenEvent("mas_reaction_gift_noudeck"):
        addReaction("mas_reaction_gift_noudeck", "noudeck", is_good=True)

label mas_reaction_gift_noudeck:
    python:
        mas_giftCapGainAff(0.5)
        # She keeps the deck at any aff
        mas_unlockGame("nou")
        mas_unlockEVL("monika_explain_nou_rules", "EVE")

    if mas_isMoniNormal(higher=True):
        m 1wub "Ой!{w=0.3} Колода карт!"
        m 3eua "И, кажется, я знаю, как в это играть!"
        m 1esc "Говорят, эта игра может {i}испортить{/i} отношения с теми, с кем играешь."

        if mas_isMoniAff(higher=True):
            show monika 5eubsa at t11 zorder MAS_MONIKA_Z with dissolve_monika
            m 5eubsa "Но я знаю, что наши отношения выдержат куда больше, чем какую-то карточную игру~"
            m 5hubsa "Э-хе-хе~"
            show monika 1eua at t11 zorder MAS_MONIKA_Z with dissolve_monika

        else:
            m 1hub "А-ха-ха!"
            m 1eua "Шучу, [player]."

        m 1eua "Ты когда-нибудь играл[_ru_a] в «НОУ», [player]?{nw}"
        $ _history_list.pop()
        menu:
            m "Ты когда-нибудь играл[_ru_a] в «НОУ», [player]?{fast}"

            # If you're an advanced nou'r, we unlock house rules for you from the start
            "Да.":
                m 1rksdlb "А-ха-ха..."
                m 1eksdla "Конечно, играл[_ru_a], ты же сам[_ru_a] подарил[_ru_a] мне колоду."
                call mas_reaction_gift_noudeck_have_played

            "Нет.":
                m 3tuu "Ну а в «УНО», э-хе-хе?{nw}"
                $ _history_list.pop()
                menu:
                    m "Ну а в «УНО», э-хе-хе?{fast}"

                    "Да.":
                        m 3hub "Отлично! {w=0.3}{nw}"
                        extend 3tub "«НОУ» {i}очень{/i} на неё похожа, а-ха-ха..."
                        call mas_reaction_gift_noudeck_have_played

                    "Нет.":
                        call mas_reaction_gift_noudeck_havent_played

        m 3hub "Не терпится сыграть с тобой!"

    elif mas_isMoniDis(higher=True):
        m 2euc "Колода?"
        m 2rka "Вообще-то, может...{nw}"
        $ _history_list.pop()
        m 2rkc "Неважно..."
        m 2esc "Мне сейчас не хочется играть, [player]."

    else:
        m 6ckc "..."

    python:
        mas_receivedGift("mas_reaction_gift_noudeck")
        gift_ev = mas_getEV("mas_reaction_gift_noudeck")
        if gift_ev:
            store.mas_filereacts.delete_file(gift_ev.category)

    return

label mas_reaction_gift_noudeck_havent_played:
    m 1eka "О, ничего страшного."
    m 4eub "Это популярная карточная игра: чтобы победить, нужно избавиться от всех карт раньше соперников."
    m 1rssdlb "Звучит довольно очевидно, а-ха-ха~"
    m 3eub "Но в неё очень весело играть с друзьями и близкими~"
    m 1eua "Я потом объясню тебе основные правила, только попроси."
    return

label mas_reaction_gift_noudeck_have_played:
    m 1eua "Ты наверняка знаешь, что многие играют по своим, домашним правилам."
    m 3eub "И если хочешь, мы тоже можем придумать свои."
    m 3eua "А если не помнишь правила, я всегда могу напомнить, только попроси."
    python:
        mas_unlockEVL("monika_change_nou_house_rules", "EVE")
        persistent._seen_ever["monika_introduce_nou_house_rules"] = True
        persistent._seen_ever["monika_explain_nou_rules"] = True
    return

init 10 python in mas_sprites_hatana:
    # TODO delete this block when #10631
    import store
    from store.mas_selspr import json_sprite_unlock
    from store.mas_sprites import get_sprite, SP_CLOTHES

    def _unlock_all():
        uniform = get_sprite(SP_CLOTHES, "hatana_tracen_uniform")
        json_sprite_unlock(uniform)
        _unlock_outfit_extras(uniform)

    def _unlock_outfit_extras(sp_obj):
        # assumed sp_obj is the hatana tracen uniform
        json_sprite_unlock(sp_obj.outfit_hair)

        for acs in sp_obj.outfit_acs.values():
            if acs.name != "hatana_tracen_uniform_head_bow_white":
                json_sprite_unlock(acs)
    

label mas_reaction_gift_clothes_hatana_tracen_uniform:
    python:
        sprite_data = mas_getSpriteObjInfo(
            (store.mas_sprites.SP_CLOTHES, "hatana_tracen_uniform")
        )
        sprite_type, sprite_name, giftname, gifted_before, sprite_object = sprite_data

        mas_giftCapGainAff(3)

    m 1etc "Oh, this is..."
    m 3wub "Wait, I think I've seen this uniform before! It's from that game about horse girls, right?"
    m 3hub "You would think this sort of uniform would be hard to run in, but they don't seem to have any trouble at all, ahaha!"
    m 3eta "Hmm...now that I'm thinking about it..."
    extend 3tua "I've never tried coding something like this, but I might have an idea for this costume."

    $ mas_finishSpriteObjInfo(sprite_data)
    $ store.mas_sprites_hatana._unlock_outfit_extras(sprite_object)
    if giftname is not None:
        $ store.mas_filereacts.delete_file(giftname)
    return
