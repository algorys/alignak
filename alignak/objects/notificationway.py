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
#     Hartmut Goebel, h.goebel@goebel-consult.de
#     Guillaume Bour, guillaume@bour.cc
#     Gerhard Lausser, gerhard.lausser@consol.de
#     Grégory Starck, g.starck@gmail.com
#     Frédéric Pégé, frederic.pege@gmail.com
#     Sebastien Coavoux, s.coavoux@free.fr
#     Thibault Cohen, titilambert@gmail.com
#     Jean Gabes, naparuba@gmail.com
#     Christophe Simon, geektophe@gmail.com
#     Romain Forlot, rforlot@yahoo.com

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
"""This module provides NotificationWay and NotificationWays classes that
implements way of sending notifications. Basically used for parsing.

"""
from alignak.objects.item import Item, Items

from alignak.property import BoolProp, IntegerProp, StringProp, ListProp
from alignak.log import logger

_special_properties = ('service_notification_commands', 'host_notification_commands',
                       'service_notification_period', 'host_notification_period')


class NotificationWay(Item):
    """NotificationWay class is used to implement way of sending notifications (command, periods..)

    """
    id = 1  # zero is always special in database, so we do not take risk here
    my_type = 'notificationway'

    properties = Item.properties.copy()
    properties.update({
        'notificationway_name':
            StringProp(fill_brok=['full_status']),
        'host_notifications_enabled':
            BoolProp(default=True, fill_brok=['full_status']),
        'service_notifications_enabled':
            BoolProp(default=True, fill_brok=['full_status']),
        'host_notification_period':
            StringProp(fill_brok=['full_status']),
        'service_notification_period':
            StringProp(fill_brok=['full_status']),
        'host_notification_options':
            ListProp(default=[''], fill_brok=['full_status'], split_on_coma=True),
        'service_notification_options':
            ListProp(default=[''], fill_brok=['full_status'], split_on_coma=True),
        'host_notification_commands':
            ListProp(fill_brok=['full_status']),
        'service_notification_commands':
            ListProp(fill_brok=['full_status']),
        'min_business_impact':
            IntegerProp(default=0, fill_brok=['full_status']),
    })

    running_properties = Item.running_properties.copy()

    # This tab is used to transform old parameters name into new ones
    # so from Nagios2 format, to Nagios3 ones.
    # Or Alignak deprecated names like criticity
    old_properties = {
        'min_criticity': 'min_business_impact',
    }

    macros = {}

    def get_name(self):
        """Accessor to notificationway_name attribute

        :return: notificationway name
        :rtype: str
        """
        return self.notificationway_name

    def want_service_notification(self, t, state, type, business_impact, cmd=None):
        """Check if notification options match the state of the service
        Notification is NOT wanted in ONE of the following case::

        * service notifications are disabled
        * cmd is not in service_notification_commands
        * business_impact < self.min_business_impact
        * service_notification_period is not valid
        * state does not match service_notification_options for problem, recovery and flapping
        * state does not match host_notification_options for downtime

        :param t: time we want to notify the contact (usually now)
        :type t: int
        :param state: host or service state ("WARNING", "CRITICAL" ..)
        :type state: str
        :param type: type of notification ("PROBLEM", "RECOVERY" ..)
        :type type: str
        :param business_impact: impact of this service
        :type business_impact: int
        :param cmd: command launched to notify the contact
        :type cmd: str
        :return: True if no condition is matched, otherwise False
        :rtype: bool
        TODO: Simplify function
        """
        if not self.service_notifications_enabled:
            return False

        # Maybe the command we ask for are not for us, but for another notification ways
        # on the same contact. If so, bail out
        if cmd and cmd not in self.service_notification_commands:
            return False

        # If the business_impact is not high enough, we bail out
        if business_impact < self.min_business_impact:
            return False

        b = self.service_notification_period.is_time_valid(t)
        if 'n' in self.service_notification_options:
            return False
        t = {'WARNING': 'w', 'UNKNOWN': 'u', 'CRITICAL': 'c',
             'RECOVERY': 'r', 'FLAPPING': 'f', 'DOWNTIME': 's'}
        if type == 'PROBLEM':
            if state in t:
                return b and t[state] in self.service_notification_options
        elif type == 'RECOVERY':
            if type in t:
                return b and t[type] in self.service_notification_options
        elif type == 'ACKNOWLEDGEMENT':
            return b
        elif type in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return b and 'f' in self.service_notification_options
        elif type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED'):
            # No notification when a downtime was cancelled. Is that true??
            # According to the documentation we need to look at _host_ options
            return b and 's' in self.host_notification_options

        return False

    def want_host_notification(self, t, state, type, business_impact, cmd=None):
        """Check if notification options match the state of the host
        Notification is NOT wanted in ONE of the following case::

        * host notifications are disabled
        * cmd is not in host_notification_commands
        * business_impact < self.min_business_impact
        * host_notification_period is not valid
        * state does not match host_notification_options for problem, recovery, flapping and dt


        :param t: time we want to notify the contact (usually now)
        :type t: int
        :param state: host or service state ("WARNING", "CRITICAL" ..)
        :type state: str
        :param type: type of notification ("PROBLEM", "RECOVERY" ..)
        :type type: str
        :param business_impact: impact of this service
        :type business_impact: int
        :param cmd: command launched to notify the contact
        :type cmd: str
        :return: True if no condition is matched, otherwise False
        :rtype: bool
        TODO: Simplify function
        """
        if not self.host_notifications_enabled:
            return False

        # If the business_impact is not high enough, we bail out
        if business_impact < self.min_business_impact:
            return False

        # Maybe the command we ask for are not for us, but for another notification ways
        # on the same contact. If so, bail out
        if cmd and cmd not in self.host_notification_commands:
            return False

        b = self.host_notification_period.is_time_valid(t)
        if 'n' in self.host_notification_options:
            return False
        t = {'DOWN': 'd', 'UNREACHABLE': 'u', 'RECOVERY': 'r',
             'FLAPPING': 'f', 'DOWNTIME': 's'}
        if type == 'PROBLEM':
            if state in t:
                return b and t[state] in self.host_notification_options
        elif type == 'RECOVERY':
            if type in t:
                return b and t[type] in self.host_notification_options
        elif type == 'ACKNOWLEDGEMENT':
            return b
        elif type in ('FLAPPINGSTART', 'FLAPPINGSTOP', 'FLAPPINGDISABLED'):
            return b and 'f' in self.host_notification_options
        elif type in ('DOWNTIMESTART', 'DOWNTIMEEND', 'DOWNTIMECANCELLED'):
            return b and 's' in self.host_notification_options

        return False

    def get_notification_commands(self, type):
        """Get notification commands for object type

        :param type: object type (host or service)
        :type type: str
        :return: command list
        :rtype: list[alignak.objects.command.Command]
        """
        # service_notification_commands for service
        notif_commands_prop = type + '_notification_commands'
        notif_commands = getattr(self, notif_commands_prop)
        return notif_commands

    def is_correct(self):
        """Check if this host configuration is correct ::

        * All required parameter are specified
        * Go through all configuration warnings and errors that could have been raised earlier

        :return: True if the configuration is correct, otherwise False
        :rtype: bool
        """
        state = True
        cls = self.__class__

        # Raised all previously saw errors like unknown commands or timeperiods
        if self.configuration_errors != []:
            state = False
            for err in self.configuration_errors:
                logger.error("[item::%s] %s", self.get_name(), err)

        # A null notif way is a notif way that will do nothing (service = n, hot =n)
        is_null_notifway = False
        if (hasattr(self, 'service_notification_options') and
                self.service_notification_options == ['n']):
            if (hasattr(self, 'host_notification_options') and
                    self.host_notification_options == ['n']):
                is_null_notifway = True
                return True

        for prop, entry in cls.properties.items():
            if prop not in _special_properties:
                if not hasattr(self, prop) and entry.required:
                    logger.warning("[notificationway::%s] %s property not set",
                                   self.get_name(), prop)
                    state = False  # Bad boy...

        # Ok now we manage special cases...
        # Service part
        if not hasattr(self, 'service_notification_commands'):
            logger.warning("[notificationway::%s] do not have any "
                           "service_notification_commands defined", self.get_name())
            state = False
        else:
            for cmd in self.service_notification_commands:
                if cmd is None:
                    logger.warning("[notificationway::%s] a "
                                   "service_notification_command is missing", self.get_name())
                    state = False
                if not cmd.is_valid():
                    logger.warning("[notificationway::%s] a "
                                   "service_notification_command is invalid", self.get_name())
                    state = False

        if getattr(self, 'service_notification_period', None) is None:
            logger.warning("[notificationway::%s] the "
                           "service_notification_period is invalid", self.get_name())
            state = False

        # Now host part
        if not hasattr(self, 'host_notification_commands'):
            logger.warning("[notificationway::%s] do not have any "
                           "host_notification_commands defined", self.get_name())
            state = False
        else:
            for cmd in self.host_notification_commands:
                if cmd is None:
                    logger.warning("[notificationway::%s] a "
                                   "host_notification_command is missing", self.get_name())
                    state = False
                if not cmd.is_valid():
                    logger.warning("[notificationway::%s] a host_notification_command "
                                   "is invalid (%s)", cmd.get_name(), str(cmd.__dict__))
                    state = False

        if getattr(self, 'host_notification_period', None) is None:
            logger.warning("[notificationway::%s] the host_notification_period "
                           "is invalid", self.get_name())
            state = False

        return state


class NotificationWays(Items):
    """NotificationWays manage a list of NotificationWay objects, used for parsing configuration

    """
    name_property = "notificationway_name"
    inner_class = NotificationWay

    def linkify(self, timeperiods, commands):
        """Create link between objects::

         * notificationways -> timeperiods
         * notificationways -> commands

        :param timeperiods: timeperiods to link
        :type timeperiods: alignak.objects.timeperiod.Timeperiods
        :param commands: commands to link
        :type commands: alignak.objects.command.Commands
        :return: None
        """
        self.linkify_with_timeperiods(timeperiods, 'service_notification_period')
        self.linkify_with_timeperiods(timeperiods, 'host_notification_period')
        self.linkify_command_list_with_commands(commands, 'service_notification_commands')
        self.linkify_command_list_with_commands(commands, 'host_notification_commands')

    def new_inner_member(self, name=None, params={}):
        """Create new instance of NotificationWay with given name and parameters
        and add it to the item list

        :param name: notification way name
        :type name: str
        :param params: notification wat parameters
        :type params: dict
        :return: None
        """
        if name is None:
            name = NotificationWay.id
        params['notificationway_name'] = name
        # print "Asking a new inner notificationway from name %s with params %s" % (name, params)
        nw = NotificationWay(params)
        self.add_item(nw)