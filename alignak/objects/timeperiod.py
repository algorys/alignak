#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2015-2015: Alignak team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak.
#
# Alignak is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alignak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Alignak.  If not, see <http://www.gnu.org/licenses/>.
#
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#  Copyright (C) 2009-2014:
#     Dessai.Imrane, dessai.imrane@gmail.com
#     Hartmut Goebel, h.goebel@goebel-consult.de
#     Guillaume Bour, guillaume@bour.cc
#     aviau, alexandre.viau@savoirfairelinux.com
#     Nicolas Dupeux, nicolas@dupeux.net
#     Grégory Starck, g.starck@gmail.com
#     Gerhard Lausser, gerhard.lausser@consol.de
#     Sebastien Coavoux, s.coavoux@free.fr
#     Christophe Simon, geektophe@gmail.com
#     Jean Gabes, naparuba@gmail.com
#     Olivier Hanesse, olivier.hanesse@gmail.com
#     Romain Forlot, rforlot@yahoo.com
#     Christophe SIMON, christophe.simon@dailymotion.com

#  This file is part of Shinken.
#
#  Shinken is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Shinken is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

# Calendar date
# -------------
#  '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)'
#   => len = 8  => CALENDAR_DATE
#
#  '(\d{4})-(\d{2})-(\d{2}) / (\d+) ([0-9:, -]+)'
#   => len = 5 => CALENDAR_DATE
#
#  '(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)'
#   => len = 7 => CALENDAR_DATE
#
#  '(\d{4})-(\d{2})-(\d{2}) ([0-9:, -]+)'
#   => len = 4 => CALENDAR_DATE
#
# Month week day
# --------------
#  '([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) / (\d+) ([0-9:, -]+)'
#  => len = 8 => MONTH WEEK DAY
#  e.g.: wednesday 1 january - thursday 2 july / 3
#
#  '([a-z]*) (\d+) - ([a-z]*) (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#  e.g.: february 1 - march 15 / 3 => MONTH DATE
#  e.g.: monday 2 - thusday 3 / 2 => WEEK DAY
#  e.g.: day 2 - day 6 / 3 => MONTH DAY
#
#  '([a-z]*) (\d+) - (\d+) / (\d+) ([0-9:, -]+)' => len = 6
#  e.g.: february 1 - 15 / 3 => MONTH DATE
#  e.g.: thursday 2 - 4 => WEEK DAY
#  e.g.: day 1 - 4 => MONTH DAY
#
#  '([a-z]*) (\d+) ([a-z]*) - ([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 7
#  e.g.: wednesday 1 january - thursday 2 july => MONTH WEEK DAY
#
#  '([a-z]*) (\d+) - (\d+) ([0-9:, -]+)' => len = 7
#  e.g.: thursday 2 - 4 => WEEK DAY
#  e.g.: february 1 - 15 / 3 => MONTH DATE
#  e.g.: day 1 - 4 => MONTH DAY
#
#  '([a-z]*) (\d+) - ([a-z]*) (\d+) ([0-9:, -]+)' => len = 5
#  e.g.: february 1 - march 15  => MONTH DATE
#  e.g.: monday 2 - thusday 3  => WEEK DAY
#  e.g.: day 2 - day 6  => MONTH DAY
#
#  '([a-z]*) (\d+) ([0-9:, -]+)' => len = 3
#  e.g.: february 3 => MONTH DATE
#  e.g.: thursday 2 => WEEK DAY
#  e.g.: day 3 => MONTH DAY
#
#  '([a-z]*) (\d+) ([a-z]*) ([0-9:, -]+)' => len = 4
#  e.g.: thusday 3 february => MONTH WEEK DAY
#
#  '([a-z]*) ([0-9:, -]+)' => len = 6
#  e.g.: thusday => normal values
#
# Types: CALENDAR_DATE
#        MONTH WEEK DAY
#        WEEK DAY
#        MONTH DATE
#        MONTH DAY
#

"""
This module provide Timeperiod class used to define time periods to do
action or not if we are in right period
"""


import time
import re

from alignak.objects.item import Item, Items

from alignak.daterange import Daterange, CalendarDaterange
from alignak.daterange import StandardDaterange, MonthWeekDayDaterange
from alignak.daterange import MonthDateDaterange, WeekDayDaterange
from alignak.daterange import MonthDayDaterange
from alignak.property import IntegerProp, StringProp, ListProp, BoolProp
from alignak.log import logger, naglog_result


class Timeperiod(Item):
    """
    Class to manage a timeperiod
    A timeperiod is defined with range time (hours) of week to do action
    and add day exceptions (like non working days)
    """
    id = 1
    my_type = 'timeperiod'

    properties = Item.properties.copy()
    properties.update({
        'timeperiod_name':  StringProp(fill_brok=['full_status']),
        'alias':            StringProp(default='', fill_brok=['full_status']),
        'use':              StringProp(default=None),
        'register':         IntegerProp(default=1),

        # These are needed if a broker module calls methods on timeperiod objects
        'dateranges':       ListProp(fill_brok=['full_status'], default=[]),
        'exclude':          ListProp(fill_brok=['full_status'], default=[]),
        'is_active':        BoolProp(default=False)
    })
    running_properties = Item.running_properties.copy()

    def __init__(self, params={}):
        self.id = Timeperiod.id
        Timeperiod.id = Timeperiod.id + 1
        self.unresolved = []
        self.dateranges = []
        self.exclude = ''

        self.invalid_entries = []
        self.cache = {}  # For tunning purpose only
        self.invalid_cache = {}  # same but for invalid search
        self.is_active = None
        self.tags = set()

        # Get standard params
        standard_params = dict([(k, v) for k, v in params.items()
                               if k in self.__class__.properties])
        # Get timeperiod params (monday, tuesday, ...)
        timeperiod_params = dict([(k, v) for k, v in params.items()
                                  if k not in self.__class__.properties])
        # Handle standard params
        super(Timeperiod, self).__init__(params=standard_params)
        # Handle timeperiod params
        for key, value in timeperiod_params.items():
            if isinstance(value, list):
                if value:
                    value = value[-1]
                else:
                    value = ''
            self.unresolved.append(key + ' ' + value)

    def get_name(self):
        """
        Get the name of the timeperiod

        :return: the timeperiod name string
        :rtype: str
        """
        return getattr(self, 'timeperiod_name', 'unknown_timeperiod')

    def get_unresolved_properties_by_inheritance(self, items):
        """
        Fill full properties with template if needed for the
        unresolved values (example: sunday ETCETC)

        :param items: The Timeperiods object.
        :type items: object
        :return: None
        """
        # Ok, I do not have prop, Maybe my templates do?
        # Same story for plus
        for i in self.templates:
            self.unresolved.extend(i.unresolved)

    def get_raw_import_values(self):
        """
        Get some properties of timeperiod (timeperiod is a bit different
        from classic item)

        :return: a dictionnary of some properties
        :rtype: dict
        """
        properties = ['timeperiod_name', 'alias', 'use', 'register']
        r = {}
        for prop in properties:
            if hasattr(self, prop):
                v = getattr(self, prop)
                print prop, ":", v
                r[prop] = v
        # Now the unresolved one. The only way to get ride of same key things is to put
        # directly the full value as the key
        for other in self.unresolved:
            r[other] = ''
        return r

    def is_time_valid(self, t):
        """
        Check if a time is valid or not

        :return: time is valid or not
        :rtype: bool
        """
        if self.has('exclude'):
            for dr in self.exclude:
                if dr.is_time_valid(t):
                    return False
        for dr in self.dateranges:
            if dr.is_time_valid(t):
                return True
        return False

    # will give the first time > t which is valid
    def get_min_from_t(self, t):
        """
        Get the first time > t which is valid

        :param t: number of seconds
        :type t: int
        :return: number of seconds
        :rtype: int
        TODO: not used, so delete it
        """
        mins_incl = []
        for dr in self.dateranges:
            mins_incl.append(dr.get_min_from_t(t))
        return min(mins_incl)

    # will give the first time > t which is not valid
    def get_not_in_min_from_t(self, f):
        """

        :return: None
        TODO: not used, so delete it
        """
        pass

    def find_next_valid_time_from_cache(self, t):
        """
        Get the next valid time from cache

        :param t: number of seconds
        :type t: int
        :return: Nothing or time in seconds
        :rtype: None or int
        """
        try:
            return self.cache[t]
        except KeyError:
            return None

    def find_next_invalid_time_from_cache(self, t):
        """
        Get the next invalid time from cache

        :param t: number of seconds
        :type t: int
        :return: Nothing or time in seconds
        :rtype: None or int
        """
        try:
            return self.invalid_cache[t]
        except KeyError:
            return None

    def check_and_log_activation_change(self):
        """
        Will look for active/un-active change of timeperiod.
        In case it change, we log it like:
        [1327392000] TIMEPERIOD TRANSITION: <name>;<from>;<to>

        States of is_active:
        -1: default value when start
        0: when timeperiod end
        1: when timeperiod start

        :return: None
        """
        now = int(time.time())

        was_active = self.is_active
        self.is_active = self.is_time_valid(now)

        # If we got a change, log it!
        if self.is_active != was_active:
            _from = 0
            _to = 0
            # If it's the start, get a special value for was
            if was_active is None:
                _from = -1
            if was_active:
                _from = 1
            if self.is_active:
                _to = 1

            # Now raise the log
            naglog_result(
                'info', 'TIMEPERIOD TRANSITION: %s;%d;%d'
                % (self.get_name(), _from, _to)
            )

    def clean_cache(self):
        """
        Clean cache with entries older than now because not used in future ;)

        :return: None
        """
        now = int(time.time())
        t_to_del = []
        for t in self.cache:
            if t < now:
                t_to_del.append(t)
        for t in t_to_del:
            del self.cache[t]

        # same for the invalid cache
        t_to_del = []
        for t in self.invalid_cache:
            if t < now:
                t_to_del.append(t)
        for t in t_to_del:
            del self.invalid_cache[t]

    def get_next_valid_time_from_t(self, t):
        """
        Get next valide time from the cache

        :param t: number of seconds
        :type t: int
        :return: Nothing or time in seconds
        :rtype: None or int
        """
        t = int(t)
        original_t = t

        # logger.debug("[%s] Check valid time for %s" %
        #  ( self.get_name(), time.asctime(time.localtime(t)))

        res_from_cache = self.find_next_valid_time_from_cache(t)
        if res_from_cache is not None:
            return res_from_cache

        still_loop = True

        # Loop for all minutes...
        while still_loop:
            local_min = None

            # Ok, not in cache...
            dr_mins = []
            s_dr_mins = []

            for dr in self.dateranges:
                dr_mins.append(dr.get_next_valid_time_from_t(t))

            s_dr_mins = sorted([d for d in dr_mins if d is not None])

            for t1 in s_dr_mins:
                if not self.exclude and still_loop is True:
                    # No Exclude so we are good
                    local_min = t1
                    still_loop = False
                else:
                    for tp in self.exclude:
                        if not tp.is_time_valid(t1) and still_loop is True:
                            # OK we found a date that is not valid in any exclude timeperiod
                            local_min = t1
                            still_loop = False

            if local_min is None:
                # print "Looking for next valid date"
                exc_mins = []
                if s_dr_mins != []:
                    for tp in self.exclude:
                        exc_mins.append(tp.get_next_invalid_time_from_t(s_dr_mins[0]))

                s_exc_mins = sorted([d for d in exc_mins if d is not None])

                if s_exc_mins != []:
                    local_min = s_exc_mins[0]

            if local_min is None:
                still_loop = False
            else:
                t = local_min
                # No loop more than one year
                if t > original_t + 3600 * 24 * 366 + 1:
                    still_loop = False
                    local_min = None

        # Ok, we update the cache...
        self.cache[original_t] = local_min
        return local_min

    def get_next_invalid_time_from_t(self, t):
        """
        Get next invalid time from the cache

        :param t: number of seconds
        :type t: int
        :return: Nothing or time in seconds
        :rtype: None or int
        """
        # time.asctime(time.localtime(t)), t
        t = int(t)
        original_t = t
        still_loop = True

        # First try to find in cache
        res_from_cache = self.find_next_invalid_time_from_cache(t)
        if res_from_cache is not None:
            return res_from_cache

        # Then look, maybe t is already invalid
        if not self.is_time_valid(t):
            return t

        local_min = t
        res = None
        # Loop for all minutes...
        while still_loop:
            # print "Invalid loop with", time.asctime(time.localtime(local_min))

            dr_mins = []
            # val_valids = []
            # val_inval = []
            # But maybe we can find a better solution with next invalid of standard dateranges
            # print self.get_name(),
            # "After valid of exclude, local_min =", time.asctime(time.localtime(local_min))
            for dr in self.dateranges:
                # print self.get_name(),
                # "Search a next invalid from DR", time.asctime(time.localtime(local_min))
                # print dr.__dict__
                m = dr.get_next_invalid_time_from_t(local_min)

                # print self.get_name(), "Dr", dr.__dict__,
                # "give me next invalid", time.asctime(time.localtime(m))
                if m is not None:
                    # But maybe it's invalid for this dr, but valid for other ones.
                    # if not self.is_time_valid(m):
                    #     print "Final: Got a next invalid at", time.asctime(time.localtime(m))
                    dr_mins.append(m)
                    # if not self.is_time_valid(m):
                    #    val_inval.append(m)
                    # else:
                    #    val_valids.append(m)
                    #    print "Add a m", time.asctime(time.localtime(m))
                    # else:
                    #     print dr.__dict__
                    #     print "FUCK bad result\n\n\n"
            # print "Inval"
            # for v in val_inval:
            #    print "\t", time.asctime(time.localtime(v))
            # print "Valid"
            # for v in val_valids:
            #    print "\t", time.asctime(time.localtime(v))

            if dr_mins != []:
                local_min = min(dr_mins)
                # Take the minimum valid as lower for next search
                # local_min_valid = 0
                # if val_valids != []:
                #    local_min_valid = min(val_valids)
                # if local_min_valid != 0:
                #    local_min = local_min_valid
                # else:
                #    local_min = min(dr_mins)
                # print "UPDATE After dr: found invalid local min:",
                #  time.asctime(time.localtime(local_min)),
                #  "is valid", self.is_time_valid(local_min)

            # print self.get_name(),
            # 'Invalid: local min', local_min #time.asctime(time.localtime(local_min))
            # We do not loop unless the local_min is not valid
            if not self.is_time_valid(local_min):
                still_loop = False
            else:  # continue until we reach too far..., in one minute
                # After one month, go quicker...
                if local_min > original_t + 3600 * 24 * 30:
                    local_min += 3600
                else:  # else search for 1min precision
                    local_min += 60
                # after one year, stop.
                if local_min > original_t + 3600 * 24 * 366 + 1:  # 60*24*366 + 1:
                    still_loop = False
            # print "Loop?", still_loop
            # if we've got a real value, we check it with the exclude
            if local_min is not None:
                # Now check if local_min is not valid
                for tp in self.exclude:
                    # print self.get_name(),
                    # "we check for invalid",
                    # time.asctime(time.localtime(local_min)), 'with tp', tp.name
                    if tp.is_time_valid(local_min):
                        still_loop = True
                        # local_min + 60
                        local_min = tp.get_next_invalid_time_from_t(local_min + 60)
                        # No loop more than one year
                        if local_min > original_t + 60 * 24 * 366 + 1:
                            still_loop = False
                            res = None

            if not still_loop:  # We find a possible value
                # We take the result the minimal possible
                if res is None or local_min < res:
                    res = local_min

        # print "Finished Return the next invalid", time.asctime(time.localtime(local_min))
        # Ok, we update the cache...
        self.invalid_cache[original_t] = local_min
        return local_min

    def has(self, prop):
        """
        Check if self have prop attribute

        :param prop: property name
        :type prop: string
        :return: true if self has this attribute
        :rtype: bool
        """
        return hasattr(self, prop)

    def is_correct(self):
        """
        Check if dateranges of timeperiod are valid

        :return: false if at least one datarange is invalid
        :rtype: bool
        """
        b = True
        for dr in self.dateranges:
            d = dr.is_correct()
            if not d:
                logger.error("[timeperiod::%s] invalid daterange ", self.get_name())
            b &= d

        # Warn about non correct entries
        for e in self.invalid_entries:
            logger.warning("[timeperiod::%s] invalid entry '%s'", self.get_name(), e)
        return b

    def __str__(self):
        """
        Get readable object

        :return: this object in readable format
        :rtype: str
        """
        s = ''
        s += str(self.__dict__) + '\n'
        for elt in self.dateranges:
            s += str(elt)
            (start, end) = elt.get_start_and_end_time()
            start = time.asctime(time.localtime(start))
            end = time.asctime(time.localtime(end))
            s += "\nStart and end:" + str((start, end))
        s += '\nExclude'
        for elt in self.exclude:
            s += str(elt)

        return s

    def resolve_daterange(self, dateranges, entry):
        """
        Try to solve dateranges (special cases)

        :param dateranges: dateranges
        :type dateranges: list
        :param entry: property of timeperiod
        :type entry: string
        :return: None
        """
        res = re.search(
            r'(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry
        )
        if res is not None:
            # print "Good catch 1"
            (syear, smon, smday, eyear, emon, emday, skip_interval, other) = res.groups()
            dateranges.append(
                CalendarDaterange(
                    syear, smon, smday, 0, 0, eyear, emon,
                    emday, 0, 0, skip_interval, other
                )
            )
            return

        res = re.search(r'(\d{4})-(\d{2})-(\d{2}) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 2"
            (syear, smon, smday, skip_interval, other) = res.groups()
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(
                CalendarDaterange(syear, smon, smday, 0, 0, eyear,
                                  emon, emday, 0, 0, skip_interval, other)
            )
            return

        res = re.search(
            r'(\d{4})-(\d{2})-(\d{2}) - (\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry
        )
        if res is not None:
            # print "Good catch 3"
            (syear, smon, smday, eyear, emon, emday, other) = res.groups()
            dateranges.append(
                CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other)
            )
            return

        res = re.search(r'(\d{4})-(\d{2})-(\d{2})[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 4"
            (syear, smon, smday, other) = res.groups()
            eyear = syear
            emon = smon
            emday = smday
            dateranges.append(
                CalendarDaterange(syear, smon, smday, 0, 0, eyear, emon, emday, 0, 0, 0, other)
            )
            return

        res = re.search(
            r'([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) / (\d+)[\s\t]*([0-9:, -]+)',
            entry
        )
        if res is not None:
            # print "Good catch 5"
            (swday, swday_offset, smon, ewday,
             ewday_offset, emon, skip_interval, other) = res.groups()
            dateranges.append(
                MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0,
                                      emon, 0, ewday, ewday_offset, skip_interval, other)
            )
            return

        res = re.search(r'([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 6"
            (t0, smday, t1, emday, skip_interval, other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(
                    WeekDayDaterange(0, 0, 0, swday, swday_offset,
                                     0, 0, 0, ewday, ewday_offset, skip_interval, other)
                )
                return
            elif t0 in Daterange.months and t1 in Daterange.months:
                smon = t0
                emon = t1
                dateranges.append(
                    MonthDateDaterange(0, smon, smday, 0, 0, 0,
                                       emon, emday, 0, 0, skip_interval, other)
                )
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(
                    MonthDayDaterange(0, 0, smday, 0, 0, 0, 0,
                                      emday, 0, 0, skip_interval, other)
                )
                return

        res = re.search(r'([a-z]*) ([\d-]+) - ([\d-]+) / (\d+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 7"
            (t0, smday, emday, skip_interval, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(
                    WeekDayDaterange(0, 0, 0, swday, swday_offset,
                                     0, 0, 0, ewday, ewday_offset, skip_interval, other)
                )
                return
            elif t0 in Daterange.months:
                smon = t0
                emon = smon
                dateranges.append(
                    MonthDateDaterange(0, smon, smday, 0, 0, 0, emon,
                                       emday, 0, 0, skip_interval, other)
                )
                return
            elif t0 == 'day':
                dateranges.append(
                    MonthDayDaterange(0, 0, smday, 0, 0, 0, 0,
                                      emday, 0, 0, skip_interval, other)
                )
                return

        res = re.search(
            r'([a-z]*) ([\d-]+) ([a-z]*) - ([a-z]*) ([\d-]+) ([a-z]*) [\s\t]*([0-9:, -]+)', entry
        )
        if res is not None:
            # print "Good catch 8"
            (swday, swday_offset, smon, ewday, ewday_offset, emon, other) = res.groups()
            # print "Debug:", (swday, swday_offset, smon, ewday, ewday_offset, emon, other)
            dateranges.append(
                MonthWeekDayDaterange(0, smon, 0, swday, swday_offset,
                                      0, emon, 0, ewday, ewday_offset, 0, other)
            )
            return

        res = re.search(r'([a-z]*) ([\d-]+) - ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 9"
            (t0, smday, emday, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = emday
                dateranges.append(
                    WeekDayDaterange(
                        0, 0, 0, swday, swday_offset, 0, 0, 0,
                        ewday, ewday_offset, 0, other)
                )
                return
            elif t0 in Daterange.months:
                smon = t0
                emon = smon
                dateranges.append(
                    MonthDateDaterange(0, smon, smday, 0, 0, 0,
                                       emon, emday, 0, 0, 0, other)
                )
                return
            elif t0 == 'day':
                dateranges.append(
                    MonthDayDaterange(0, 0, smday, 0, 0, 0, 0,
                                      emday, 0, 0, 0, other)
                )
                return

        res = re.search(r'([a-z]*) ([\d-]+) - ([a-z]*) ([\d-]+)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 10"
            (t0, smday, t1, emday, other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.weekdays:
                swday = t0
                ewday = t1
                swday_offset = smday
                ewday_offset = emday
                dateranges.append(
                    WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,
                                     0, 0, ewday, ewday_offset, 0, other)
                )
                return
            elif t0 in Daterange.months and t1 in Daterange.months:
                smon = t0
                emon = t1
                dateranges.append(
                    MonthDateDaterange(0, smon, smday, 0, 0,
                                       0, emon, emday, 0, 0, 0, other)
                )
                return
            elif t0 == 'day' and t1 == 'day':
                dateranges.append(
                    MonthDayDaterange(0, 0, smday, 0, 0, 0,
                                      0, emday, 0, 0, 0, other)
                )
                return

        res = re.search(r'([a-z]*) ([\d-]+) ([a-z]*)[\s\t]*([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 11"
            (t0, swday_offset, t1, other) = res.groups()
            if t0 in Daterange.weekdays and t1 in Daterange.months:
                swday = t0
                smon = t1
                emon = smon
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(
                    MonthWeekDayDaterange(0, smon, 0, swday, swday_offset, 0, emon,
                                          0, ewday, ewday_offset, 0, other)
                )
                return

        res = re.search(r'([a-z]*) ([\d-]+)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 12"
            (t0, smday, other) = res.groups()
            if t0 in Daterange.weekdays:
                swday = t0
                swday_offset = smday
                ewday = swday
                ewday_offset = swday_offset
                dateranges.append(
                    WeekDayDaterange(0, 0, 0, swday, swday_offset, 0,
                                     0, 0, ewday, ewday_offset, 0, other)
                )
                return
            if t0 in Daterange.months:
                smon = t0
                emon = smon
                emday = smday
                dateranges.append(
                    MonthDateDaterange(
                        0, smon, smday, 0, 0, 0, emon, emday, 0, 0, 0, other)
                )
                return
            if t0 == 'day':
                emday = smday
                dateranges.append(
                    MonthDayDaterange(0, 0, smday, 0, 0, 0,
                                      0, emday, 0, 0, 0, other)
                )
                return

        res = re.search(r'([a-z]*)[\s\t]+([0-9:, -]+)', entry)
        if res is not None:
            # print "Good catch 13"
            (t0, other) = res.groups()
            if t0 in Daterange.weekdays:
                day = t0
                dateranges.append(StandardDaterange(day, other))
                return
        logger.info("[timeentry::%s] no match for %s", self.get_name(), entry)
        self.invalid_entries.append(entry)

    def apply_inheritance(self):
        """
        Inherite no properties and no custom variables for timeperiod

        :return: None
        """
        pass

    def explode(self, timeperiods):
        """
        Try to resolv all unresolved elements

        :param timeperiods: Timeperiods object
        :type timeperiods:
        :return: None
        """
        for entry in self.unresolved:
            # print "Revolving entry", entry
            self.resolve_daterange(self.dateranges, entry)
        self.unresolved = []

    def linkify(self, timeperiods):
        """
        Will make timeperiod in exclude with id of the timeperiods

        :param timeperiods: Timeperiods object
        :type timeperiods:
        :return: None
        """
        new_exclude = []
        if self.has('exclude') and self.exclude != []:
            logger.debug("[timeentry::%s] have excluded %s", self.get_name(), self.exclude)
            excluded_tps = self.exclude
            # print "I will exclude from:", excluded_tps
            for tp_name in excluded_tps:
                tp = timeperiods.find_by_name(tp_name.strip())
                if tp is not None:
                    new_exclude.append(tp)
                else:
                    logger.error("[timeentry::%s] unknown %s timeperiod", self.get_name(), tp_name)
        self.exclude = new_exclude

    def check_exclude_rec(self):
        """
        Check if this timeperiod is tagged

        :return: if tagged return false, if not true
        :rtype: bool
        """
        if self.rec_tag:
            logger.error("[timeentry::%s] is in a loop in exclude parameter", self.get_name())
            return False
        self.rec_tag = True
        for tp in self.exclude:
            tp.check_exclude_rec()
        return True

    def fill_data_brok_from(self, data, brok_type):
        """
        Add timeperiods from brok

        :param data: timeperiod dictionnary
        :type data: dict
        :param brok_type: brok type
        :type brok_type: string
        :return: None
        """
        cls = self.__class__
        # Now config properties
        for prop, entry in cls.properties.items():
            # Is this property intended for broking?
            # if 'fill_brok' in entry:
            if brok_type in entry.fill_brok:
                if hasattr(self, prop):
                    data[prop] = getattr(self, prop)
                elif entry.has_default:
                    data[prop] = entry.default


class Timeperiods(Items):
    """
    Class to manage all timeperiods
    A timeperiod is defined with range time (hours) of week to do action
    and add day exceptions (like non working days)
    """

    name_property = "timeperiod_name"
    inner_class = Timeperiod

    def explode(self):
        """
        Try to resolv each timeperiod

        :return: None
        """
        for id in self.items:
            tp = self.items[id]
            tp.explode(self)

    def linkify(self):
        """
        Check exclusion for each timeperiod

        :return: None
        """
        for id in self.items:
            tp = self.items[id]
            tp.linkify(self)

    def apply_inheritance(self):
        """
        The only interesting property to inherit is exclude

        :return: None
        """
        self.apply_partial_inheritance('exclude')
        for i in self:
            i.get_customs_properties_by_inheritance()

        # And now apply inheritance for unresolved properties
        # like the dateranges in fact
        for tp in self:
            tp.get_unresolved_properties_by_inheritance(self.items)

    def is_correct(self):
        """
        check if each properties of timeperiods are valid

        :return: True if is correct, otherwise False
        :rtype: bool
        """
        r = True
        # We do not want a same hg to be explode again and again
        # so we tag it
        for tp in self.items.values():
            tp.rec_tag = False

        for tp in self.items.values():
            for tmp_tp in self.items.values():
                tmp_tp.rec_tag = False
            r &= tp.check_exclude_rec()

        # We clean the tags
        for tp in self.items.values():
            del tp.rec_tag

        # And check all timeperiods for correct (sunday is false)
        for tp in self:
            r &= tp.is_correct()

        return r


if __name__ == '__main__':
    t = Timeperiod()
    test = ['1999-01-28  00:00-24:00',
            'monday 3                   00:00-24:00             ',
            'day 2                      00:00-24:00',
            'february 10                00:00-24:00',
            'february -1 00:00-24:00',
            'friday -2                  00:00-24:00',
            'thursday -1 november 00:00-24:00',
            '2007-01-01 - 2008-02-01    00:00-24:00',
            'monday 3 - thursday 4      00:00-24:00',
            'day 1 - 15         00:00-24:00',
            'day 20 - -1                00:00-24:00',
            'july -10 - -1              00:00-24:00',
            'april 10 - may 15          00:00-24:00',
            'tuesday 1 april - friday 2 may 00:00-24:00',
            '2007-01-01 - 2008-02-01 / 3 00:00-24:00',
            '2008-04-01 / 7             00:00-24:00',
            'day 1 - 15 / 5             00:00-24:00',
            'july 10 - 15 / 2 00:00-24:00',
            'tuesday 1 april - friday 2 may / 6 00:00-24:00',
            'tuesday 1 october - friday 2 may / 6 00:00-24:00',
            'monday 3 - thursday 4 / 2 00:00-24:00',
            'monday 4 - thursday 3 / 2 00:00-24:00',
            'day -1 - 15 / 5            01:00-24:00,00:30-05:60',
            'tuesday 00:00-24:00',
            'sunday 00:00-24:00',
            'saturday 03:00-24:00,00:32-01:02',
            'wednesday 09:00-15:46,00:00-21:00',
            'may 7 - february 2 00:00-10:00',
            'day -1 - 5 00:00-10:00',
            'tuesday 1 february - friday 1 may 01:00-24:00,00:30-05:60',
            'december 2 - may -15               00:00-24:00',
            ]
    for entry in test:
        print "**********************"
        print entry
        t = Timeperiod()
        t.timeperiod_name = ''
        t.resolve_daterange(t.dateranges, entry)
        # t.exclude = []
        # t.resolve_daterange(t.exclude, 'monday 00:00-19:00')
        # t.check_valid_for_today()
        now = time.time()
        # print "Is valid NOW?", t.is_time_valid(now)
        t_next = t.get_next_valid_time_from_t(now + 5 * 60)
        if t_next is not None:
            print "Get next valid for now + 5 min ==>", time.asctime(time.localtime(t_next)), "<=="
        else:
            print "===> No future time!!!"
        # print "End date:", t.get_end_time()
        # print "Next valid", time.asctime(time.localtime(t.get_next_valid_time()))
        print str(t) + '\n\n'

    print "*************************************************************"
    t3 = Timeperiod()
    t3.timeperiod_name = 't3'
    t3.resolve_daterange(t3.dateranges, 'day 1 - 10 10:30-15:00')
    t3.exclude = []

    t2 = Timeperiod()
    t2.timeperiod_name = 't2'
    t2.resolve_daterange(t2.dateranges, 'day 1 - 10 12:00-17:00')
    t2.exclude = [t3]

    t = Timeperiod()
    t.timeperiod_name = 't'
    t.resolve_daterange(t.dateranges, 'day 1 - 10 14:00-15:00')
    t.exclude = [t2]

    print "Mon T", str(t) + '\n\n'
    t_next = t.get_next_valid_time_from_t(now)
    t_no_next = t.get_next_invalid_time_from_t(now)
    print "Get next valid for now ==>", time.asctime(time.localtime(t_next)), "<=="
    print "Get next invalid for now ==>", time.asctime(time.localtime(t_no_next)), "<=="