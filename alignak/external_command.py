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
#     andrewmcgilvray, a.mcgilvray@gmail.com
#     Guillaume Bour, guillaume@bour.cc
#     Alexandre Viau, alexandre@alexandreviau.net
#     Frédéric MOHIER, frederic.mohier@ipmfrance.com
#     aviau, alexandre.viau@savoirfairelinux.com
#     xkilian, fmikus@acktomic.com
#     Nicolas Dupeux, nicolas@dupeux.net
#     Hartmut Goebel, h.goebel@goebel-consult.de
#     Grégory Starck, g.starck@gmail.com
#     Arthur Gautier, superbaloo@superbaloo.net
#     Sebastien Coavoux, s.coavoux@free.fr
#     Squiz, squiz@squiz.confais.org
#     Olivier Hanesse, olivier.hanesse@gmail.com
#     Jean Gabes, naparuba@gmail.com
#     Zoran Zaric, zz@zoranzaric.de
#     Gerhard Lausser, gerhard.lausser@consol.de

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
"""This module provides ExternalCommand and ExternalCommandManager classes
Used to process command sent by users

"""
import os
import time
import re

from alignak.util import to_int, to_bool, split_semicolon
from alignak.downtime import Downtime
from alignak.contactdowntime import ContactDowntime
from alignak.comment import Comment
from alignak.commandcall import CommandCall
from alignak.log import logger, naglog_result
from alignak.objects.pollerlink import PollerLink
from alignak.eventhandler import EventHandler
from alignak.brok import Brok
from alignak.misc.common import DICT_MODATTR


class ExternalCommand:
    """ExternalCommand class is only an object with a cmd_line attribute.
    All parsing and execution is done in manager

    """
    my_type = 'externalcommand'

    def __init__(self, cmd_line):
        self.cmd_line = cmd_line


class ExternalCommandManager:
    """ExternalCommandManager class managed all external command sent to Alignak
    It basically parses arguments and execute the right function

    """

    commands = {
        'CHANGE_CONTACT_MODSATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_MODHATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_MODATTR':
            {'global': True, 'args': ['contact', None]},
        'CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD':
            {'global': True, 'args': ['contact', 'time_period']},
        'ADD_SVC_COMMENT':
            {'global': False, 'args': ['service', 'to_bool', 'author', None]},
        'ADD_HOST_COMMENT':
            {'global': False, 'args': ['host', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM':
            {'global': False, 'args': ['service', 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM':
            {'global': False, 'args': ['host', 'to_int', 'to_bool', 'to_bool', 'author', None]},
        'ACKNOWLEDGE_SVC_PROBLEM_EXPIRE':
            {'global': False, 'args': ['service', 'to_int', 'to_bool',
                                       'to_bool', 'to_int', 'author', None]},
        'ACKNOWLEDGE_HOST_PROBLEM_EXPIRE':
            {'global': False,
             'args': ['host', 'to_int', 'to_bool', 'to_bool', 'to_int', 'author', None]},
        'CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD':
            {'global': True, 'args': ['contact', 'time_period']},
        'CHANGE_CUSTOM_CONTACT_VAR':
            {'global': True, 'args': ['contact', None, None]},
        'CHANGE_CUSTOM_HOST_VAR':
            {'global': False, 'args': ['host', None, None]},
        'CHANGE_CUSTOM_SVC_VAR':
            {'global': False, 'args': ['service', None, None]},
        'CHANGE_GLOBAL_HOST_EVENT_HANDLER':
            {'global': True, 'args': ['command']},
        'CHANGE_GLOBAL_SVC_EVENT_HANDLER':
            {'global': True, 'args': ['command']},
        'CHANGE_HOST_CHECK_COMMAND':
            {'global': False, 'args': ['host', 'command']},
        'CHANGE_HOST_CHECK_TIMEPERIOD':
            {'global': False, 'args': ['host', 'time_period']},
        'CHANGE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host', 'command']},
        'CHANGE_HOST_MODATTR':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_MAX_HOST_CHECK_ATTEMPTS':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_MAX_SVC_CHECK_ATTEMPTS':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_NORMAL_HOST_CHECK_INTERVAL':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_NORMAL_SVC_CHECK_INTERVAL':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_RETRY_HOST_CHECK_INTERVAL':
            {'global': False, 'args': ['host', 'to_int']},
        'CHANGE_RETRY_SVC_CHECK_INTERVAL':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_SVC_CHECK_COMMAND':
            {'global': False, 'args': ['service', 'command']},
        'CHANGE_SVC_CHECK_TIMEPERIOD':
            {'global': False, 'args': ['service', 'time_period']},
        'CHANGE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service', 'command']},
        'CHANGE_SVC_MODATTR':
            {'global': False, 'args': ['service', 'to_int']},
        'CHANGE_SVC_NOTIFICATION_TIMEPERIOD':
            {'global': False, 'args': ['service', 'time_period']},
        'DELAY_HOST_NOTIFICATION':
            {'global': False, 'args': ['host', 'to_int']},
        'DELAY_SVC_NOTIFICATION':
            {'global': False, 'args': ['service', 'to_int']},
        'DEL_ALL_HOST_COMMENTS':
            {'global': False, 'args': ['host']},
        'DEL_ALL_HOST_DOWNTIMES':
            {'global': False, 'args': ['host']},
        'DEL_ALL_SVC_COMMENTS':
            {'global': False, 'args': ['service']},
        'DEL_ALL_SVC_DOWNTIMES':
            {'global': False, 'args': ['service']},
        'DEL_CONTACT_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DEL_HOST_COMMENT':
            {'global': True, 'args': ['to_int']},
        'DEL_HOST_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DEL_SVC_COMMENT':
            {'global': True, 'args': ['to_int']},
        'DEL_SVC_DOWNTIME':
            {'global': True, 'args': ['to_int']},
        'DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST':
            {'global': False, 'args': ['host']},
        'DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'DISABLE_CONTACT_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'DISABLE_CONTACT_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'DISABLE_EVENT_HANDLERS':
            {'global': True, 'args': []},
        'DISABLE_FAILURE_PREDICTION':
            {'global': True, 'args': []},
        'DISABLE_FLAP_DETECTION':
            {'global': True, 'args': []},
        'DISABLE_HOSTGROUP_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOSTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'DISABLE_HOST_AND_CHILD_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_CHECK':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_FLAP_DETECTION':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'DISABLE_HOST_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host']},
        'DISABLE_HOST_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'DISABLE_NOTIFICATIONS':
            {'global': True, 'args': []},
        'DISABLE_PASSIVE_HOST_CHECKS':
            {'global': False, 'args': ['host']},
        'DISABLE_PASSIVE_SVC_CHECKS':
            {'global': False, 'args': ['service']},
        'DISABLE_PERFORMANCE_DATA':
            {'global': True, 'args': []},
        'DISABLE_SERVICEGROUP_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'DISABLE_SERVICE_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'DISABLE_SERVICE_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'DISABLE_SVC_CHECK':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'DISABLE_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['service']},
        'ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST':
            {'global': False, 'args': ['host']},
        'ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact_group']},
        'ENABLE_CONTACT_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'ENABLE_CONTACT_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['contact']},
        'ENABLE_EVENT_HANDLERS':
            {'global': True, 'args': []},
        'ENABLE_FAILURE_PREDICTION':
            {'global': True, 'args': []},
        'ENABLE_FLAP_DETECTION':
            {'global': True, 'args': []},
        'ENABLE_HOSTGROUP_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_SVC_CHECKS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOSTGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['host_group']},
        'ENABLE_HOST_AND_CHILD_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_CHECK':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_FLAP_DETECTION':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'ENABLE_HOST_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host']},
        'ENABLE_HOST_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['host']},
        'ENABLE_NOTIFICATIONS':
            {'global': True, 'args': []},
        'ENABLE_PASSIVE_HOST_CHECKS':
            {'global': False, 'args': ['host']},
        'ENABLE_PASSIVE_SVC_CHECKS':
            {'global': False, 'args': ['service']},
        'ENABLE_PERFORMANCE_DATA':
            {'global': True, 'args': []},
        'ENABLE_SERVICEGROUP_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_CHECKS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS':
            {'global': True, 'args': ['service_group']},
        'ENABLE_SERVICE_FRESHNESS_CHECKS':
            {'global': True, 'args': []},
        'ENABLE_SVC_CHECK':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_FLAP_DETECTION':
            {'global': False, 'args': ['service']},
        'ENABLE_SVC_NOTIFICATIONS':
            {'global': False, 'args': ['service']},
        'PROCESS_FILE':
            {'global': True, 'args': [None, 'to_bool']},
        'PROCESS_HOST_CHECK_RESULT':
            {'global': False, 'args': ['host', 'to_int', None]},
        'PROCESS_HOST_OUTPUT':
            {'global': False, 'args': ['host', None]},
        'PROCESS_SERVICE_CHECK_RESULT':
            {'global': False, 'args': ['service', 'to_int', None]},
        'PROCESS_SERVICE_OUTPUT':
            {'global': False, 'args': ['service', None]},
        'READ_STATE_INFORMATION':
            {'global': True, 'args': []},
        'REMOVE_HOST_ACKNOWLEDGEMENT':
            {'global': False, 'args': ['host']},
        'REMOVE_SVC_ACKNOWLEDGEMENT':
            {'global': False, 'args': ['service']},
        'RESTART_PROGRAM':
            {'global': True, 'internal': True, 'args': []},
        'RELOAD_CONFIG':
            {'global': True, 'internal': True, 'args': []},
        'SAVE_STATE_INFORMATION':
            {'global': True, 'args': []},
        'SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_CONTACT_DOWNTIME':
            {'global': True, 'args': ['contact', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_FORCED_HOST_CHECK':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_FORCED_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_FORCED_SVC_CHECK':
            {'global': False, 'args': ['service', 'to_int']},
        'SCHEDULE_HOSTGROUP_HOST_DOWNTIME':
            {'global': True, 'args': ['host_group', 'to_int', 'to_int',
                                      'to_bool', 'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOSTGROUP_SVC_DOWNTIME':
            {'global': True, 'args': ['host_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_CHECK':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_HOST_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_HOST_SVC_CHECKS':
            {'global': False, 'args': ['host', 'to_int']},
        'SCHEDULE_HOST_SVC_DOWNTIME':
            {'global': False, 'args': ['host', 'to_int', 'to_int', 'to_bool',
                                       'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_HOST_DOWNTIME':
            {'global': True, 'args': ['service_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SERVICEGROUP_SVC_DOWNTIME':
            {'global': True, 'args': ['service_group', 'to_int', 'to_int', 'to_bool',
                                      'to_int', 'to_int', 'author', None]},
        'SCHEDULE_SVC_CHECK':
            {'global': False, 'args': ['service', 'to_int']},
        'SCHEDULE_SVC_DOWNTIME': {'global': False, 'args': ['service', 'to_int', 'to_int',
                                                            'to_bool', 'to_int', 'to_int',
                                                            'author', None]},
        'SEND_CUSTOM_HOST_NOTIFICATION':
            {'global': False, 'args': ['host', 'to_int', 'author', None]},
        'SEND_CUSTOM_SVC_NOTIFICATION':
            {'global': False, 'args': ['service', 'to_int', 'author', None]},
        'SET_HOST_NOTIFICATION_NUMBER':
            {'global': False, 'args': ['host', 'to_int']},
        'SET_SVC_NOTIFICATION_NUMBER':
            {'global': False, 'args': ['service', 'to_int']},
        'SHUTDOWN_PROGRAM':
            {'global': True, 'args': []},
        'START_ACCEPTING_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_ACCEPTING_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': []},
        'START_EXECUTING_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_EXECUTING_SVC_CHECKS':
            {'global': True, 'args': []},
        'START_OBSESSING_OVER_HOST':
            {'global': False, 'args': ['host']},
        'START_OBSESSING_OVER_HOST_CHECKS':
            {'global': True, 'args': []},
        'START_OBSESSING_OVER_SVC':
            {'global': False, 'args': ['service']},
        'START_OBSESSING_OVER_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_ACCEPTING_PASSIVE_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_ACCEPTING_PASSIVE_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_EXECUTING_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_EXECUTING_SVC_CHECKS':
            {'global': True, 'args': []},
        'STOP_OBSESSING_OVER_HOST':
            {'global': False, 'args': ['host']},
        'STOP_OBSESSING_OVER_HOST_CHECKS':
            {'global': True, 'args': []},
        'STOP_OBSESSING_OVER_SVC':
            {'global': False, 'args': ['service']},
        'STOP_OBSESSING_OVER_SVC_CHECKS':
            {'global': True, 'args': []},
        'LAUNCH_SVC_EVENT_HANDLER':
            {'global': False, 'args': ['service']},
        'LAUNCH_HOST_EVENT_HANDLER':
            {'global': False, 'args': ['host']},
        # Now internal calls
        'ADD_SIMPLE_HOST_DEPENDENCY':
            {'global': False, 'args': ['host', 'host']},
        'DEL_HOST_DEPENDENCY':
            {'global': False, 'args': ['host', 'host']},
        'ADD_SIMPLE_POLLER':
            {'global': True, 'internal': True, 'args': [None, None, None, None]},
    }

    def __init__(self, conf, mode):
        self.mode = mode
        if conf:
            self.conf = conf
            self.hosts = conf.hosts
            self.services = conf.services
            self.contacts = conf.contacts
            self.hostgroups = conf.hostgroups
            self.commands = conf.commands
            self.servicegroups = conf.servicegroups
            self.contactgroups = conf.contactgroups
            self.timeperiods = conf.timeperiods
            self.pipe_path = conf.command_file

        self.fifo = None
        self.cmd_fragments = ''
        if self.mode == 'dispatcher':
            self.confs = conf.confs
        # Will change for each command read, so if a command need it,
        # it can get it
        self.current_timestamp = 0

    def load_scheduler(self, scheduler):
        """Setter for scheduler attribute

        :param scheduler: scheduler to set
        :type scheduler: object
        :return: None
        """
        self.sched = scheduler

    def load_arbiter(self, arbiter):
        """Setter for arbiter attribute

        :param arbiter: arbiter to set
        :type arbiter: object
        :return: None
        """
        self.arbiter = arbiter

    def load_receiver(self, receiver):
        """Setter for receiver attribute

        :param receiver: receiver to set
        :type receiver: object
        :return: None
        """
        self.receiver = receiver

    def open(self):
        """Create if necessary and open a pipe
        (Won't work under Windows)

        :return: pipe file descriptor
        :rtype: file
        """
        # At the first open del and create the fifo
        if self.fifo is None:
            if os.path.exists(self.pipe_path):
                os.unlink(self.pipe_path)

            if not os.path.exists(self.pipe_path):
                os.umask(0)
                try:
                    os.mkfifo(self.pipe_path, 0660)
                    open(self.pipe_path, 'w+', os.O_NONBLOCK)
                except OSError, exp:
                    self.error("Pipe creation failed (%s): %s" % (self.pipe_path, str(exp)))
                    return None
        self.fifo = os.open(self.pipe_path, os.O_NONBLOCK)
        return self.fifo

    def get(self):
        """Get external commands from fifo

        :return: external commands
        :rtype: list[alignak.external_command.ExternalCommand]
        """
        buf = os.read(self.fifo, 8096)
        r = []
        fullbuf = len(buf) == 8096 and True or False
        # If the buffer ended with a fragment last time, prepend it here
        buf = self.cmd_fragments + buf
        buflen = len(buf)
        self.cmd_fragments = ''
        if fullbuf and buf[-1] != '\n':
            # The buffer was full but ends with a command fragment
            r.extend([ExternalCommand(s) for s in (buf.split('\n'))[:-1] if s])
            self.cmd_fragments = (buf.split('\n'))[-1]
        elif buflen:
            # The buffer is either half-filled or full with a '\n' at the end.
            r.extend([ExternalCommand(s) for s in buf.split('\n') if s])
        else:
            # The buffer is empty. We "reset" the fifo here. It will be
            # re-opened in the main loop.
            os.close(self.fifo)
        return r

    def resolve_command(self, excmd):
        """Parse command and dispatch it (to sched for example) if necessary
        If the command is not global it will be executed.

        :param excmd: external command to handle
        :type excmd: alignak.external_command.ExternalCommand
        :return: None
        """
        # Maybe the command is invalid. Bailout
        try:
            command = excmd.cmd_line
        except AttributeError, exp:
            logger.debug("resolve_command:: error with command %s: %s", excmd, exp)
            return

        # Strip and get utf8 only strings
        command = command.strip()

        # Only log if we are in the Arbiter
        if self.mode == 'dispatcher' and self.conf.log_external_commands:
            # Fix #1263
            # logger.info('EXTERNAL COMMAND: ' + command.rstrip())
            naglog_result('info', 'EXTERNAL COMMAND: ' + command.rstrip())
        r = self.get_command_and_args(command, excmd)

        # If we are a receiver, bail out here
        if self.mode == 'receiver':
            return

        if r is not None:
            is_global = r['global']
            if not is_global:
                c_name = r['c_name']
                args = r['args']
                logger.debug("Got commands %s %s", c_name, str(args))
                getattr(self, c_name)(*args)
            else:
                command = r['cmd']
                self.dispatch_global_command(command)

    def search_host_and_dispatch(self, host_name, command, extcmd):
        """Try to dispatch a command for a specific host (so specific scheduler)
        because this command is related to a host (change notification interval for example)

        :param host_name: host name to search
        :type host_name: str
        :param command: command line
        :type command: str
        :param extcmd:  external command object (the object will be added to sched commands list)
        :type extcmd: alignak.external_command.ExternalCommand
        :return: None
        """
        logger.debug("Calling search_host_and_dispatch for %s", host_name)
        host_found = False

        # If we are a receiver, just look in the receiver
        if self.mode == 'receiver':
            logger.info("Receiver looking a scheduler for the external command %s %s",
                        host_name, command)
            sched = self.receiver.get_sched_from_hname(host_name)
            if sched:
                host_found = True
                logger.debug("Receiver found a scheduler: %s", sched)
                logger.info("Receiver pushing external command to scheduler %s", sched)
                sched['external_commands'].append(extcmd)
        else:
            for cfg in self.confs.values():
                if cfg.hosts.find_by_name(host_name) is not None:
                    logger.debug("Host %s found in a configuration", host_name)
                    if cfg.is_assigned:
                        host_found = True
                        sched = cfg.assigned_to
                        logger.debug("Sending command to the scheduler %s", sched.get_name())
                        # sched.run_external_command(command)
                        sched.external_commands.append(command)
                        break
                    else:
                        logger.warning("Problem: a configuration is found, but is not assigned!")
        if not host_found:
            if getattr(self, 'receiver',
                       getattr(self, 'arbiter', None)).accept_passive_unknown_check_results:
                b = self.get_unknown_check_result_brok(command)
                getattr(self, 'receiver', getattr(self, 'arbiter', None)).add(b)
            else:
                logger.warning("Passive check result was received for host '%s', "
                               "but the host could not be found!", host_name)

    @staticmethod
    def get_unknown_check_result_brok(cmd_line):
        """Create unknown check result brok and fill it with command data

        :param cmd_line: command line to extract data
        :type cmd_line: str
        :return: unknown check result brok
        :rtype: alignak.objects.brok.Brok
        """

        match = re.match(
            r'^\[([0-9]{10})] PROCESS_(SERVICE)_CHECK_RESULT;'
            r'([^\;]*);([^\;]*);([^\;]*);([^\|]*)(?:\|(.*))?', cmd_line)
        if not match:
            match = re.match(
                r'^\[([0-9]{10})] PROCESS_(HOST)_CHECK_RESULT;'
                r'([^\;]*);([^\;]*);([^\|]*)(?:\|(.*))?', cmd_line)

        if not match:
            return None

        data = {
            'time_stamp': int(match.group(1)),
            'host_name': match.group(3),
        }

        if match.group(2) == 'SERVICE':
            data['service_description'] = match.group(4)
            data['return_code'] = match.group(5)
            data['output'] = match.group(6)
            data['perf_data'] = match.group(7)
        else:
            data['return_code'] = match.group(4)
            data['output'] = match.group(5)
            data['perf_data'] = match.group(6)

        b = Brok('unknown_%s_check_result' % match.group(2).lower(), data)

        return b

    def dispatch_global_command(self, command):
        """Send command to scheduler, it's a global one

        :param command: command to send
        :type command: alignak.external_command.ExternalCommand
        :return: None
        """
        for sched in self.conf.schedulers:
            logger.debug("Sending a command '%s' to scheduler %s", command, sched)
            if sched.alive:
                # sched.run_external_command(command)
                sched.external_commands.append(command)

    def get_command_and_args(self, command, extcmd=None):
        """Parse command and get args

        :param command: command line to parse
        :type command: str
        :param extcmd: external command object (used to dispatch)
        :type extcmd: None | object
        :return: Dict containing command and arg ::

        {'global': False, 'c_name': c_name, 'args': args}

        :rtype: dict | None
        """
        # safe_print("Trying to resolve", command)
        command = command.rstrip()
        elts = split_semicolon(command)  # danger!!! passive checkresults with perfdata
        part1 = elts[0]

        elts2 = part1.split(' ')
        # print "Elts2:", elts2
        if len(elts2) != 2:
            logger.debug("Malformed command '%s'", command)
            return None
        ts = elts2[0]
        # Now we will get the timestamps as [123456]
        if not ts.startswith('[') or not ts.endswith(']'):
            logger.debug("Malformed command '%s'", command)
            return None
        # Ok we remove the [ ]
        ts = ts[1:-1]
        try:  # is an int or not?
            self.current_timestamp = to_int(ts)
        except ValueError:
            logger.debug("Malformed command '%s'", command)
            return None

        # Now get the command
        c_name = elts2[1]

        # safe_print("Get command name", c_name)
        if c_name not in ExternalCommandManager.commands:
            logger.debug("Command '%s' is not recognized, sorry", c_name)
            return None

        # Split again based on the number of args we expect. We cannot split
        # on every ; because this character may appear in the perfdata of
        # passive check results.
        entry = ExternalCommandManager.commands[c_name]

        # Look if the command is purely internal or not
        internal = False
        if 'internal' in entry and entry['internal']:
            internal = True

        numargs = len(entry['args'])
        if numargs and 'service' in entry['args']:
            numargs += 1
        elts = split_semicolon(command, numargs)

        logger.debug("mode= %s, global= %s", self.mode, str(entry['global']))
        if self.mode == 'dispatcher' and entry['global']:
            if not internal:
                logger.debug("Command '%s' is a global one, we resent it to all schedulers", c_name)
                return {'global': True, 'cmd': command}

        # print "Is global?", c_name, entry['global']
        # print "Mode:", self.mode
        # print "This command have arguments:", entry['args'], len(entry['args'])

        args = []
        i = 1
        in_service = False
        tmp_host = ''
        try:
            for elt in elts[1:]:
                logger.debug("Searching for a new arg: %s (%d)", elt, i)
                val = elt.strip()
                if val.endswith('\n'):
                    val = val[:-1]

                logger.debug("For command arg: %s", val)

                if not in_service:
                    type_searched = entry['args'][i - 1]
                    # safe_print("Search for a arg", type_searched)

                    if type_searched == 'host':
                        if self.mode == 'dispatcher' or self.mode == 'receiver':
                            self.search_host_and_dispatch(val, command, extcmd)
                            return None
                        h = self.hosts.find_by_name(val)
                        if h is not None:
                            args.append(h)
                        elif self.conf.accept_passive_unknown_check_results:
                            b = self.get_unknown_check_result_brok(command)
                            self.sched.add_Brok(b)

                    elif type_searched == 'contact':
                        c = self.contacts.find_by_name(val)
                        if c is not None:
                            args.append(c)

                    elif type_searched == 'time_period':
                        t = self.timeperiods.find_by_name(val)
                        if t is not None:
                            args.append(t)

                    elif type_searched == 'to_bool':
                        args.append(to_bool(val))

                    elif type_searched == 'to_int':
                        args.append(to_int(val))

                    elif type_searched in ('author', None):
                        args.append(val)

                    elif type_searched == 'command':
                        c = self.commands.find_by_name(val)
                        if c is not None:
                            # the find will be redone by
                            # the commandCall creation, but != None
                            # is useful so a bad command will be caught
                            args.append(val)

                    elif type_searched == 'host_group':
                        hg = self.hostgroups.find_by_name(val)
                        if hg is not None:
                            args.append(hg)

                    elif type_searched == 'service_group':
                        sg = self.servicegroups.find_by_name(val)
                        if sg is not None:
                            args.append(sg)

                    elif type_searched == 'contact_group':
                        cg = self.contact_groups.find_by_name(val)
                        if cg is not None:
                            args.append(cg)

                    # special case: service are TWO args host;service, so one more loop
                    # to get the two parts
                    elif type_searched == 'service':
                        in_service = True
                        tmp_host = elt.strip()
                        # safe_print("TMP HOST", tmp_host)
                        if tmp_host[-1] == '\n':
                            tmp_host = tmp_host[:-1]
                        if self.mode == 'dispatcher':
                            self.search_host_and_dispatch(tmp_host, command, extcmd)
                            return None

                    i += 1
                else:
                    in_service = False
                    srv_name = elt
                    if srv_name[-1] == '\n':
                        srv_name = srv_name[:-1]
                    # If we are in a receiver, bailout now.
                    if self.mode == 'receiver':
                        self.search_host_and_dispatch(tmp_host, command, extcmd)
                        return None

                    # safe_print("Got service full", tmp_host, srv_name)
                    s = self.services.find_srv_by_name_and_hostname(tmp_host, srv_name)
                    if s is not None:
                        args.append(s)
                    elif self.conf.accept_passive_unknown_check_results:
                        b = self.get_unknown_check_result_brok(command)
                        self.sched.add_Brok(b)
                    else:
                        logger.warning(
                            "A command was received for service '%s' on host '%s', "
                            "but the service could not be found!", srv_name, tmp_host)

        except IndexError:
            logger.debug("Sorry, the arguments are not corrects")
            return None
        # safe_print('Finally got ARGS:', args)
        if len(args) == len(entry['args']):
            # safe_print("OK, we can call the command", c_name, "with", args)
            return {'global': False, 'c_name': c_name, 'args': args}
            # f = getattr(self, c_name)
            # apply(f, args)
        else:
            logger.debug("Sorry, the arguments are not corrects (%s)", str(args))
            return None

    def CHANGE_CONTACT_MODSATTR(self, contact, value):
        """Change contact modified service attribute value
        Format of the line that triggers function call::

        CHANGE_CONTACT_MODSATTR;<contact_name>;<value>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param value: new value to set
        :type value: str
        :return: None
        """
        contact.modified_service_attributes = long(value)

    def CHANGE_CONTACT_MODHATTR(self, contact, value):
        """Change contact modified host attribute value
        Format of the line that triggers function call::

        CHANGE_CONTACT_MODHATTR;<contact_name>;<value>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param value: new value to set
        :type value:str
        :return: None
        """
        contact.modified_host_attributes = long(value)

    def CHANGE_CONTACT_MODATTR(self, contact, value):
        """Change contact modified attribute value
        Format of the line that triggers function call::

        CHANGE_CONTACT_MODATTR;<contact_name>;<value>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param value: new value to set
        :type value: str
        :return: None
        """
        contact.modified_attributes = long(value)

    def CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        """Change contact host notification timeperiod value
        Format of the line that triggers function call::

        CHANGE_CONTACT_HOST_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param notification_timeperiod: timeperiod to set
        :type notification_timeperiod: alignak.objects.timeperiod.Timeperiod
        :return: None
        """
        contact.modified_host_attributes |= DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        contact.host_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    def ADD_SVC_COMMENT(self, service, persistent, author, comment):
        """Add a service comment
        Format of the line that triggers function call::

        ADD_SVC_COMMENT;<host_name>;<service_description>;<persistent>;<author>;<comment>

        :param service: service to add the comment
        :type service: alignak.objects.service.Service
        :param persistent: is comment persistent (for reboot) or not
        :type persistent: bool
        :param author: author name
        :type author: str
        :param comment: text comment
        :type comment: str
        :return: None
        """
        c = Comment(service, persistent, author, comment, 2, 1, 1, False, 0)
        service.add_comment(c)
        self.sched.add(c)

    def ADD_HOST_COMMENT(self, host, persistent, author, comment):
        """Add a host comment
        Format of the line that triggers function call::

        ADD_HOST_COMMENT;<host_name>;<persistent>;<author>;<comment>

        :param host: host to add the comment
        :type host: alignak.objects.host.Host
        :param persistent: is comment persistent (for reboot) or not
        :type persistent: bool
        :param author: author name
        :type author: str
        :param comment: text comment
        :type comment: str
        :return: None
        """
        c = Comment(host, persistent, author, comment, 1, 1, 1, False, 0)
        host.add_comment(c)
        self.sched.add(c)

    def ACKNOWLEDGE_SVC_PROBLEM(self, service, sticky, notify, persistent, author, comment):
        """Acknowledge a service problem
        Format of the line that triggers function call::

        ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;<sticky>;<notify>;<persistent>;
        <author>;<comment>

        :param service: service to acknowledge the problem
        :type service: alignak.objects.service.Service
        :param sticky: acknowledge will be always present is host return in UP state
        :type sticky: integer
        :param notify: if to 1, send a notification
        :type notify: integer
        :param persistent: if 1, keep this acknowledge when Alignak restart
        :type persistent: integer
        :param author: name of the author or the acknowledge
        :type author: str
        :param comment: comment (description) of the acknowledge
        :type comment: str
        :return: None
        """
        service.acknowledge_problem(sticky, notify, persistent, author, comment)

    def ACKNOWLEDGE_HOST_PROBLEM(self, host, sticky, notify, persistent, author, comment):
        """Acknowledge a host problem
        Format of the line that triggers function call::

        ACKNOWLEDGE_HOST_PROBLEM;<host_name>;<sticky>;<notify>;<persistent>;<author>;<comment>

        :param host: host to acknowledge the problem
        :type host: alignak.objects.host.Host
        :param sticky: acknowledge will be always present is host return in UP state
        :type sticky: integer
        :param notify: if to 1, send a notification
        :type notify: integer
        :param persistent: if 1, keep this acknowledge when Alignak restart
        :type persistent: integer
        :param author: name of the author or the acknowledge
        :type author: str
        :param comment: comment (description) of the acknowledge
        :type comment: str
        :return: None
        TODO: add a better ACK management
        """
        host.acknowledge_problem(sticky, notify, persistent, author, comment)

    def ACKNOWLEDGE_SVC_PROBLEM_EXPIRE(self, service, sticky, notify,
                                       persistent, end_time, author, comment):
        """Acknowledge a service problem with expire time for this acknowledgement
        Format of the line that triggers function call::

        ACKNOWLEDGE_SVC_PROBLEM;<host_name>;<service_description>;<sticky>;<notify>;<persistent>;
        <end_time>;<author>;<comment>

        :param service: service to acknowledge the problem
        :type service: alignak.objects.service.Service
        :param sticky: acknowledge will be always present is host return in UP state
        :type sticky: integer
        :param notify: if to 1, send a notification
        :type notify: integer
        :param persistent: if 1, keep this acknowledge when Alignak restart
        :type persistent: integer
        :param end_time: end (timeout) of this acknowledge in seconds(timestamp) (0 to never end)
        :type end_time: int
        :param author: name of the author or the acknowledge
        :type author: str
        :param comment: comment (description) of the acknowledge
        :type comment: str
        :return: None
        """
        service.acknowledge_problem(sticky, notify, persistent, author, comment, end_time=end_time)

    def ACKNOWLEDGE_HOST_PROBLEM_EXPIRE(self, host, sticky, notify,
                                        persistent, end_time, author, comment):
        """Acknowledge a host problem with expire time for this acknowledgement
        Format of the line that triggers function call::

        ACKNOWLEDGE_HOST_PROBLEM;<host_name>;<sticky>;<notify>;<persistent>;<end_time>;
        <author>;<comment>

        :param host: host to acknowledge the problem
        :type host: alignak.objects.host.Host
        :param sticky: acknowledge will be always present is host return in UP state
        :type sticky: integer
        :param notify: if to 1, send a notification
        :type notify: integer
        :param persistent: if 1, keep this acknowledge when Alignak restart
        :type persistent: integer
        :param end_time: end (timeout) of this acknowledge in seconds(timestamp) (0 to never end)
        :type end_time: int
        :param author: name of the author or the acknowledge
        :type author: str
        :param comment: comment (description) of the acknowledge
        :type comment: str
        :return: None
        TODO: add a better ACK management
        """
        host.acknowledge_problem(sticky, notify, persistent, author, comment, end_time=end_time)

    def CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD(self, contact, notification_timeperiod):
        """Change contact service notification timeperiod value
        Format of the line that triggers function call::

        CHANGE_CONTACT_SVC_NOTIFICATION_TIMEPERIOD;<contact_name>;<notification_timeperiod>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param notification_timeperiod: timeperiod to set
        :type notification_timeperiod: alignak.objects.timeperiod.Timeperiod
        :return: None
        """
        contact.modified_service_attributes |= \
            DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        contact.service_notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(contact)

    def CHANGE_CUSTOM_CONTACT_VAR(self, contact, varname, varvalue):
        """Change custom contact variable
        Format of the line that triggers function call::

        CHANGE_CUSTOM_CONTACT_VAR;<contact_name>;<varname>;<varvalue>

        :param contact: contact to edit
        :type contact: alignak.objects.contact.Contact
        :param varname: variable name to change
        :type varname: str
        :param varvalue: variable new value
        :type varvalue: str
        :return: None
        """
        contact.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        contact.customs[varname.upper()] = varvalue

    def CHANGE_CUSTOM_HOST_VAR(self, host, varname, varvalue):
        """Change custom host variable
        Format of the line that triggers function call::

        CHANGE_CUSTOM_HOST_VAR;<host_name>;<varname>;<varvalue>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param varname: variable name to change
        :type varname: str
        :param varvalue: variable new value
        :type varvalue: str
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        host.customs[varname.upper()] = varvalue

    def CHANGE_CUSTOM_SVC_VAR(self, service, varname, varvalue):
        """Change custom service variable
        Format of the line that triggers function call::

        CHANGE_CUSTOM_SVC_VAR;<host_name>;<service_description>;<varname>;<varvalue>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param varname: variable name to change
        :type varvalue: str
        :param varvalue: variable new value
        :type varname: str
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_CUSTOM_VARIABLE"].value
        service.customs[varname.upper()] = varvalue

    def CHANGE_GLOBAL_HOST_EVENT_HANDLER(self, event_handler_command):
        """DOES NOTHING (should change global host event handler)
        Format of the line that triggers function call::

        CHANGE_GLOBAL_HOST_EVENT_HANDLER;<event_handler_command>

        :param event_handler_command: new event handler
        :type event_handler_command:
        :return: None
        TODO: DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        """
        pass

    def CHANGE_GLOBAL_SVC_EVENT_HANDLER(self, event_handler_command):
        """DOES NOTHING (should change global service event handler)
        Format of the line that triggers function call::

        CHANGE_GLOBAL_SVC_EVENT_HANDLER;<event_handler_command>

        :param event_handler_command: new event handler
        :type event_handler_command:
        :return: None
        TODO: DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        """
        pass

    def CHANGE_HOST_CHECK_COMMAND(self, host, check_command):
        """Modify host check command
        Format of the line that triggers function call::

        CHANGE_HOST_CHECK_COMMAND;<host_name>;<check_command>

        :param host: host to modify check command
        :type host: alignak.objects.host.Host
        :param check_command: command line
        :type check_command:
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_COMMAND"].value
        host.check_command = CommandCall(self.commands, check_command, poller_tag=host.poller_tag)
        self.sched.get_and_register_status_brok(host)

    def CHANGE_HOST_CHECK_TIMEPERIOD(self, host, timeperiod):
        """Modify host check timeperiod
        Format of the line that triggers function call::

        CHANGE_HOST_CHECK_TIMEPERIOD;<host_name>;<timeperiod>

        :param host: host to modify check timeperiod
        :type host: alignak.objects.host.Host
        :param timeperiod: timeperiod object
        :type timeperiod: alignak.objects.timeperiod.Timeperiod
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_TIMEPERIOD"].value
        host.check_period = timeperiod
        self.sched.get_and_register_status_brok(host)

    def CHANGE_HOST_EVENT_HANDLER(self, host, event_handler_command):
        """Modify host event handler
        Format of the line that triggers function call::

        CHANGE_HOST_EVENT_HANDLER;<host_name>;<event_handler_command>

        :param host: host to modify event handler
        :type host: alignak.objects.host.Host
        :param event_handler_command: event handler command line
        :type event_handler_command:
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        host.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(host)

    def CHANGE_HOST_MODATTR(self, host, value):
        """Change host modified attributes
        Format of the line that triggers function call::

        CHANGE_HOST_MODATTR;<host_name>;<value>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param value: new value to set
        :type value: str
        :return: None
        """
        host.modified_attributes = long(value)

    def CHANGE_MAX_HOST_CHECK_ATTEMPTS(self, host, check_attempts):
        """Modify max host check attempt
        Format of the line that triggers function call::

        CHANGE_MAX_HOST_CHECK_ATTEMPTS;<host_name>;<check_attempts>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param check_attempts: new value to set
        :type check_attempts: int
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_MAX_CHECK_ATTEMPTS"].value
        host.max_check_attempts = check_attempts
        if host.state_type == 'HARD' and host.state == 'UP' and host.attempt > 1:
            host.attempt = host.max_check_attempts
        self.sched.get_and_register_status_brok(host)

    def CHANGE_MAX_SVC_CHECK_ATTEMPTS(self, service, check_attempts):
        """Modify max service check attempt
        Format of the line that triggers function call::

        CHANGE_MAX_SVC_CHECK_ATTEMPTS;<host_name>;<service_description>;<check_attempts>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param check_attempts: new value to set
        :type check_attempts: int
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_MAX_CHECK_ATTEMPTS"].value
        service.max_check_attempts = check_attempts
        if service.state_type == 'HARD' and service.state == 'OK' and service.attempt > 1:
            service.attempt = service.max_check_attempts
        self.sched.get_and_register_status_brok(service)

    def CHANGE_NORMAL_HOST_CHECK_INTERVAL(self, host, check_interval):
        """Modify host check interval
        Format of the line that triggers function call::

        CHANGE_NORMAL_HOST_CHECK_INTERVAL;<host_name>;<check_interval>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param check_interval: new value to set
        :type check_interval:
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_NORMAL_CHECK_INTERVAL"].value
        old_interval = host.check_interval
        host.check_interval = check_interval
        # If there were no regular checks (interval=0), then schedule
        # a check immediately.
        if old_interval == 0 and host.checks_enabled:
            host.schedule(force=False, force_time=int(time.time()))
        self.sched.get_and_register_status_brok(host)

    def CHANGE_NORMAL_SVC_CHECK_INTERVAL(self, service, check_interval):
        """Modify service check interval
        Format of the line that triggers function call::

        CHANGE_NORMAL_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param check_interval: new value to set
        :type check_interval:
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_NORMAL_CHECK_INTERVAL"].value
        old_interval = service.check_interval
        service.check_interval = check_interval
        # If there were no regular checks (interval=0), then schedule
        # a check immediately.
        if old_interval == 0 and service.checks_enabled:
            service.schedule(force=False, force_time=int(time.time()))
        self.sched.get_and_register_status_brok(service)

    def CHANGE_RETRY_HOST_CHECK_INTERVAL(self, host, check_interval):
        """Modify host retry interval
        Format of the line that triggers function call::

        CHANGE_RETRY_HOST_CHECK_INTERVAL;<host_name>;<check_interval>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param check_interval: new value to set
        :type check_interval:
        :return: None
        """
        host.modified_attributes |= DICT_MODATTR["MODATTR_RETRY_CHECK_INTERVAL"].value
        host.retry_interval = check_interval
        self.sched.get_and_register_status_brok(host)

    def CHANGE_RETRY_SVC_CHECK_INTERVAL(self, service, check_interval):
        """Modify service retry interval
        Format of the line that triggers function call::

        CHANGE_RETRY_SVC_CHECK_INTERVAL;<host_name>;<service_description>;<check_interval>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param check_interval: new value to set
        :type check_interval:
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_RETRY_CHECK_INTERVAL"].value
        service.retry_interval = check_interval
        self.sched.get_and_register_status_brok(service)

    def CHANGE_SVC_CHECK_COMMAND(self, service, check_command):
        """Modify service check command
        Format of the line that triggers function call::

        CHANGE_SVC_CHECK_COMMAND;<host_name>;<service_description>;<check_command>

        :param service: service to modify check command
        :type service: alignak.objects.service.Service
        :param check_command: command line
        :type check_command:
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_COMMAND"].value
        service.check_command = CommandCall(self.commands, check_command,
                                            poller_tag=service.poller_tag)
        self.sched.get_and_register_status_brok(service)

    def CHANGE_SVC_CHECK_TIMEPERIOD(self, service, check_timeperiod):
        """Modify service check timeperiod
        Format of the line that triggers function call::

        CHANGE_SVC_CHECK_TIMEPERIOD;<host_name>;<service_description>;<check_timeperiod>

        :param service: service to modify check timeperiod
        :type service: alignak.objects.service.Service
        :param timeperiod: timeperiod object
        :type timeperiod: alignak.objects.timeperiod.Timeperiod
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_CHECK_TIMEPERIOD"].value
        service.check_period = check_timeperiod
        self.sched.get_and_register_status_brok(service)

    def CHANGE_SVC_EVENT_HANDLER(self, service, event_handler_command):
        """Modify service event handler
        Format of the line that triggers function call::

        CHANGE_SVC_EVENT_HANDLER;<host_name>;<service_description>;<event_handler_command>

        :param service: service to modify event handler
        :type service: alignak.objects.service.Service
        :param event_handler_command: event handler command line
        :type event_handler_command:
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_COMMAND"].value
        service.event_handler = CommandCall(self.commands, event_handler_command)
        self.sched.get_and_register_status_brok(service)

    def CHANGE_SVC_MODATTR(self, service, value):
        """Change service modified attributes
        Format of the line that triggers function call::

        CHANGE_SVC_MODATTR;<host_name>;<service_description>;<value>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param value: new value to set
        :type value: str
        :return: None
        """
        # This is not enough.
        # We need to also change each of the needed attributes.
        previous_value = service.modified_attributes
        future_value = long(value)
        changes = future_value ^ previous_value

        for modattr in [
                "MODATTR_NOTIFICATIONS_ENABLED", "MODATTR_ACTIVE_CHECKS_ENABLED",
                "MODATTR_PASSIVE_CHECKS_ENABLED", "MODATTR_EVENT_HANDLER_ENABLED",
                "MODATTR_FLAP_DETECTION_ENABLED", "MODATTR_PERFORMANCE_DATA_ENABLED",
                "MODATTR_OBSESSIVE_HANDLER_ENABLED", "MODATTR_FRESHNESS_CHECKS_ENABLED"]:
            if changes & DICT_MODATTR[modattr].value:
                logger.info("[CHANGE_SVC_MODATTR] Reset %s", modattr)
                setattr(service, DICT_MODATTR[modattr].attribute, not
                        getattr(service, DICT_MODATTR[modattr].attribute))

        # TODO : Handle not boolean attributes.
        # ["MODATTR_EVENT_HANDLER_COMMAND",
        # "MODATTR_CHECK_COMMAND", "MODATTR_NORMAL_CHECK_INTERVAL",
        # "MODATTR_RETRY_CHECK_INTERVAL",
        # "MODATTR_MAX_CHECK_ATTEMPTS", "MODATTR_FRESHNESS_CHECKS_ENABLED",
        # "MODATTR_CHECK_TIMEPERIOD", "MODATTR_CUSTOM_VARIABLE", "MODATTR_NOTIFICATION_TIMEPERIOD"]

        service.modified_attributes = future_value

        # And we need to push the information to the scheduler.
        self.sched.get_and_register_status_brok(service)

    def CHANGE_SVC_NOTIFICATION_TIMEPERIOD(self, service, notification_timeperiod):
        """Change service notification timeperiod
        Format of the line that triggers function call::

        CHANGE_SVC_NOTIFICATION_TIMEPERIOD;<host_name>;<service_description>;
        <notification_timeperiod>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param notification_timeperiod: timeperiod to set
        :type notification_timeperiod: alignak.objects.timeperiod.Timeperiod
        :return: None
        """
        service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATION_TIMEPERIOD"].value
        service.notification_period = notification_timeperiod
        self.sched.get_and_register_status_brok(service)

    def DELAY_HOST_NOTIFICATION(self, host, notification_time):
        """Modify host first notification delay
        Format of the line that triggers function call::

        DELAY_HOST_NOTIFICATION;<host_name>;<notification_time>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :param notification_time: new value to set
        :type notification_time:
        :return: None
        """
        host.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(host)

    def DELAY_SVC_NOTIFICATION(self, service, notification_time):
        """Modify service first notification delay
        Format of the line that triggers function call::

        DELAY_SVC_NOTIFICATION;<host_name>;<service_description>;<notification_time>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :param notification_time: new value to set
        :type notification_time:
        :return: None
        """
        service.first_notification_delay = notification_time
        self.sched.get_and_register_status_brok(service)

    def DEL_ALL_HOST_COMMENTS(self, host):
        """Delete all host comments
        Format of the line that triggers function call::

        DEL_ALL_HOST_COMMENTS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for c in host.comments:
            self.DEL_HOST_COMMENT(c.id)

    def DEL_ALL_HOST_DOWNTIMES(self, host):
        """Delete all host downtimes
        Format of the line that triggers function call::

        DEL_ALL_HOST_DOWNTIMES;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for dt in host.downtimes:
            self.DEL_HOST_DOWNTIME(dt.id)

    def DEL_ALL_SVC_COMMENTS(self, service):
        """Delete all service comments
        Format of the line that triggers function call::

        DEL_ALL_SVC_COMMENTS;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        for c in service.comments:
            self.DEL_SVC_COMMENT(c.id)

    def DEL_ALL_SVC_DOWNTIMES(self, service):
        """Delete all service downtime
        Format of the line that triggers function call::

        DEL_ALL_SVC_DOWNTIMES;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        for dt in service.downtimes:
            self.DEL_SVC_DOWNTIME(dt.id)

    def DEL_CONTACT_DOWNTIME(self, downtime_id):
        """Delete a contact downtime
        Format of the line that triggers function call::

        DEL_CONTACT_DOWNTIME;<downtime_id>

        :param downtime_id: downtime id to delete
        :type downtime_id: int
        :return: None
        """
        if downtime_id in self.sched.contact_downtimes:
            self.sched.contact_downtimes[downtime_id].cancel()

    def DEL_HOST_COMMENT(self, comment_id):
        """Delete a host comment
        Format of the line that triggers function call::

        DEL_HOST_COMMENT;<comment_id>

        :param comment_id: comment id to delete
        :type comment_id: int
        :return: None
        """
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    def DEL_HOST_DOWNTIME(self, downtime_id):
        """Delete a host downtime
        Format of the line that triggers function call::

        DEL_HOST_DOWNTIME;<downtime_id>

        :param downtime_id: downtime id to delete
        :type downtime_id: int
        :return: None
        """
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    def DEL_SVC_COMMENT(self, comment_id):
        """Delete a service comment
        Format of the line that triggers function call::

        DEL_SVC_COMMENT;<comment_id>

        :param comment_id: comment id to delete
        :type comment_id: int
        :return: None
        """
        if comment_id in self.sched.comments:
            self.sched.comments[comment_id].can_be_deleted = True

    def DEL_SVC_DOWNTIME(self, downtime_id):
        """Delete a service downtime
        Format of the line that triggers function call::

        DEL_SVC_DOWNTIME;<downtime_id>

        :param downtime_id: downtime id to delete
        :type downtime_id: int
        :return: None
        """
        if downtime_id in self.sched.downtimes:
            self.sched.downtimes[downtime_id].cancel()

    def DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        """DOES NOTHING (should disable notification beyond a host)
        Format of the line that triggers function call::

        DISABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        TODO: Implement it
        """
        pass

    def DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        """Disable host notifications for a contactgroup
        Format of the line that triggers function call::

        DISABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>

        :param contactgroup: contactgroup to disable
        :type contactgroup: alignak.objects.contactgroup.Contactgroup
        :return: None
        """
        for contact in contactgroup:
            self.DISABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    def DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        """Disable service notifications for a contactgroup
        Format of the line that triggers function call::

        DISABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>

        :param contactgroup: contactgroup to disable
        :type contactgroup: alignak.objects.contactgroup.Contactgroup
        :return: None
        """
        for contact in contactgroup:
            self.DISABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    def DISABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        """Disable host notifications for a contact
        Format of the line that triggers function call::

        DISABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>

        :param contact: contact to disable
        :type contact: alignak.objects.contact.Contact
        :return: None
        """
        if contact.host_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.host_notifications_enabled = False
            self.sched.get_and_register_status_brok(contact)

    def DISABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        """Disable service notifications for a contact
        Format of the line that triggers function call::

        DISABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>

        :param contact: contact to disable
        :type contact: alignak.objects.contact.Contact
        :return: None
        """
        if contact.service_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.service_notifications_enabled = False
            self.sched.get_and_register_status_brok(contact)

    def DISABLE_EVENT_HANDLERS(self):
        """Disable event handlers (globally)
        Format of the line that triggers function call::

        DISABLE_EVENT_HANDLERS

        :return: None
        """
        if self.conf.enable_event_handlers:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            self.conf.enable_event_handlers = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_FAILURE_PREDICTION(self):
        """Disable failure prediction (globally)
        Format of the line that triggers function call::

        DISABLE_FAILURE_PREDICTION

        :return: None
        """
        if self.conf.enable_failure_prediction:
            self.conf.modified_attributes |= \
                DICT_MODATTR["MODATTR_FAILURE_PREDICTION_ENABLED"].value
            self.conf.enable_failure_prediction = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_FLAP_DETECTION(self):
        """Disable flap detection (globally)
        Format of the line that triggers function call::

        DISABLE_FLAP_DETECTION

        :return: None
        """
        if self.conf.enable_flap_detection:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            self.conf.enable_flap_detection = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()
            # Is need, disable flap state for hosts and services
            for service in self.conf.services:
                if service.is_flapping:
                    service.is_flapping = False
                    service.flapping_changes = []
                    self.sched.get_and_register_status_brok(service)
            for host in self.conf.hosts:
                if host.is_flapping:
                    host.is_flapping = False
                    host.flapping_changes = []
                    self.sched.get_and_register_status_brok(host)

    def DISABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        """Disable host checks for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.DISABLE_HOST_CHECK(host)

    def DISABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        """Disable host notifications for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.DISABLE_HOST_NOTIFICATIONS(host)

    def DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        """Disable host passive checks for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(host)

    def DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        """Disable service passive checks for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_PASSIVE_SVC_CHECKS(service)

    def DISABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        """Disable service checks for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_CHECK(service)

    def DISABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        """Disable service notifications for a hostgroup
        Format of the line that triggers function call::

        DISABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>

        :param hostgroup: hostgroup to disable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.DISABLE_SVC_NOTIFICATIONS(service)

    def DISABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        """DOES NOTHING (Should disable host notifications and its child)
        Format of the line that triggers function call::

        DISABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        pass

    def DISABLE_HOST_CHECK(self, host):
        """Disable checks for a host
        Format of the line that triggers function call::

        DISABLE_HOST_CHECK;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.active_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            host.disable_active_checks()
            self.sched.get_and_register_status_brok(host)

    def DISABLE_HOST_EVENT_HANDLER(self, host):
        """Disable event handlers for a host
        Format of the line that triggers function call::

        DISABLE_HOST_EVENT_HANDLER;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.event_handler_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            host.event_handler_enabled = False
            self.sched.get_and_register_status_brok(host)

    def DISABLE_HOST_FLAP_DETECTION(self, host):
        """Disable flap detection for a host
        Format of the line that triggers function call::

        DISABLE_HOST_FLAP_DETECTION;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.flap_detection_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            host.flap_detection_enabled = False
            # Maybe the host was flapping, if so, stop flapping
            if host.is_flapping:
                host.is_flapping = False
                host.flapping_changes = []
            self.sched.get_and_register_status_brok(host)

    def DISABLE_HOST_FRESHNESS_CHECKS(self):
        """Disable freshness checks (globally)
        Format of the line that triggers function call::

        DISABLE_HOST_FRESHNESS_CHECKS

        :return: None
        """
        if self.conf.check_host_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_host_freshness = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_HOST_NOTIFICATIONS(self, host):
        """Disable notifications for a host
        Format of the line that triggers function call::

        DISABLE_HOST_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.notifications_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            host.notifications_enabled = False
            self.sched.get_and_register_status_brok(host)

    def DISABLE_HOST_SVC_CHECKS(self, host):
        """Disable service checks for a host
        Format of the line that triggers function call::

        DISABLE_HOST_SVC_CHECKS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for s in host.services:
            self.DISABLE_SVC_CHECK(s)

    def DISABLE_HOST_SVC_NOTIFICATIONS(self, host):
        """Disable services notifications for a host
        Format of the line that triggers function call::

        DISABLE_HOST_SVC_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for s in host.services:
            self.DISABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    def DISABLE_NOTIFICATIONS(self):
        """Disable notifications (globally)
        Format of the line that triggers function call::

        DISABLE_NOTIFICATIONS

        :return: None
        """
        if self.conf.enable_notifications:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            self.conf.enable_notifications = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_PASSIVE_HOST_CHECKS(self, host):
        """Disable passive checks for a host
        Format of the line that triggers function call::

        DISABLE_PASSIVE_HOST_CHECKS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.passive_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            host.passive_checks_enabled = False
            self.sched.get_and_register_status_brok(host)

    def DISABLE_PASSIVE_SVC_CHECKS(self, service):
        """Disable passive checks for a service
        Format of the line that triggers function call::

        DISABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.passive_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            service.passive_checks_enabled = False
            self.sched.get_and_register_status_brok(service)

    def DISABLE_PERFORMANCE_DATA(self):
        """Disable performance data processing (globally)
        Format of the line that triggers function call::

        DISABLE_PERFORMANCE_DATA

        :return: None
        """
        if self.conf.process_performance_data:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PERFORMANCE_DATA_ENABLED"].value
            self.conf.process_performance_data = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        """Disable host checks for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_HOST_CHECK(service.host)

    def DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        """Disable host notifications for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_HOST_NOTIFICATIONS(service.host)

    def DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        """Disable passive host checks for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_PASSIVE_HOST_CHECKS(service.host)

    def DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        """Disable passive service checks for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_PASSIVE_SVC_CHECKS(service)

    def DISABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        """Disable service checks for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_SVC_CHECK(service)

    def DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        """Disable service notifications for a servicegroup
        Format of the line that triggers function call::

        DISABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>

        :param servicegroup: servicegroup to disable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.DISABLE_SVC_NOTIFICATIONS(service)

    def DISABLE_SERVICE_FLAP_DETECTION(self, service):
        """Disable flap detection for a service
        Format of the line that triggers function call::

        DISABLE_SERVICE_FLAP_DETECTION;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.flap_detection_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            service.flap_detection_enabled = False
            # Maybe the service was flapping, if so, stop flapping
            if service.is_flapping:
                service.is_flapping = False
                service.flapping_changes = []
            self.sched.get_and_register_status_brok(service)

    def DISABLE_SERVICE_FRESHNESS_CHECKS(self):
        """Disable service freshness checks (globally)
        Format of the line that triggers function call::

        DISABLE_SERVICE_FRESHNESS_CHECKS

        :return: None
        """
        if self.conf.check_service_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_service_freshness = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def DISABLE_SVC_CHECK(self, service):
        """Disable checks for a service
        Format of the line that triggers function call::

        DISABLE_SVC_CHECK;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.active_checks_enabled:
            service.disable_active_checks()
            service.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.sched.get_and_register_status_brok(service)

    def DISABLE_SVC_EVENT_HANDLER(self, service):
        """Disable event handlers for a service
        Format of the line that triggers function call::

        DISABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.event_handler_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            service.event_handler_enabled = False
            self.sched.get_and_register_status_brok(service)

    def DISABLE_SVC_FLAP_DETECTION(self, service):
        """Disable flap detection for a service
        Format of the line that triggers function call::

        DISABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        self.DISABLE_SERVICE_FLAP_DETECTION(service)

    def DISABLE_SVC_NOTIFICATIONS(self, service):
        """Disable notifications for a service
        Format of the line that triggers function call::

        DISABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.notifications_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            service.notifications_enabled = False
            self.sched.get_and_register_status_brok(service)

    def ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST(self, host):
        """DOES NOTHING (should enable notification beyond a host)
        Format of the line that triggers function call::

        ENABLE_ALL_NOTIFICATIONS_BEYOND_HOST;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        TODO: Implement it
        """
        pass

    def ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS(self, contactgroup):
        """Enable host notifications for a contactgroup
        Format of the line that triggers function call::

        ENABLE_CONTACTGROUP_HOST_NOTIFICATIONS;<contactgroup_name>

        :param contactgroup: contactgroup to enable
        :type contactgroup: alignak.objects.contactgroup.Contactgroup
        :return: None
        """
        for contact in contactgroup:
            self.ENABLE_CONTACT_HOST_NOTIFICATIONS(contact)

    def ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS(self, contactgroup):
        """Enable service notifications for a contactgroup
        Format of the line that triggers function call::

        ENABLE_CONTACTGROUP_SVC_NOTIFICATIONS;<contactgroup_name>

        :param contactgroup: contactgroup to enable
        :type contactgroup: alignak.objects.contactgroup.Contactgroup
        :return: None
        """
        for contact in contactgroup:
            self.ENABLE_CONTACT_SVC_NOTIFICATIONS(contact)

    def ENABLE_CONTACT_HOST_NOTIFICATIONS(self, contact):
        """Enable host notifications for a contact
        Format of the line that triggers function call::

        ENABLE_CONTACT_HOST_NOTIFICATIONS;<contact_name>

        :param contact: contact to enable
        :type contact: alignak.objects.contact.Contact
        :return: None
        """
        if not contact.host_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.host_notifications_enabled = True
            self.sched.get_and_register_status_brok(contact)

    def ENABLE_CONTACT_SVC_NOTIFICATIONS(self, contact):
        """Enable service notifications for a contact
        Format of the line that triggers function call::

        DISABLE_CONTACT_SVC_NOTIFICATIONS;<contact_name>

        :param contact: contact to enable
        :type contact: alignak.objects.contact.Contact
        :return: None
        """
        if not contact.service_notifications_enabled:
            contact.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            contact.service_notifications_enabled = True
            self.sched.get_and_register_status_brok(contact)

    def ENABLE_EVENT_HANDLERS(self):
        """Enable event handlers (globally)
        Format of the line that triggers function call::

        ENABLE_EVENT_HANDLERS

        :return: None
        """
        if not self.conf.enable_event_handlers:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            self.conf.enable_event_handlers = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_FAILURE_PREDICTION(self):
        """Enable failure prediction (globally)
        Format of the line that triggers function call::

        ENABLE_FAILURE_PREDICTION

        :return: None
        """
        if not self.conf.enable_failure_prediction:
            self.conf.modified_attributes |= \
                DICT_MODATTR["MODATTR_FAILURE_PREDICTION_ENABLED"].value
            self.conf.enable_failure_prediction = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_FLAP_DETECTION(self):
        """Enable flap detection (globally)
        Format of the line that triggers function call::

        ENABLE_FLAP_DETECTION

        :return: None
        """
        if not self.conf.enable_flap_detection:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            self.conf.enable_flap_detection = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_HOSTGROUP_HOST_CHECKS(self, hostgroup):
        """Enable host checks for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_HOST_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.ENABLE_HOST_CHECK(host)

    def ENABLE_HOSTGROUP_HOST_NOTIFICATIONS(self, hostgroup):
        """Enable host notifications for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_HOST_NOTIFICATIONS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.ENABLE_HOST_NOTIFICATIONS(host)

    def ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS(self, hostgroup):
        """Enable host passive checks for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_PASSIVE_HOST_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(host)

    def ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS(self, hostgroup):
        """Enable service passive checks for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_PASSIVE_SVC_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_PASSIVE_SVC_CHECKS(service)

    def ENABLE_HOSTGROUP_SVC_CHECKS(self, hostgroup):
        """Enable service checks for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_SVC_CHECKS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_CHECK(service)

    def ENABLE_HOSTGROUP_SVC_NOTIFICATIONS(self, hostgroup):
        """Enable service notifications for a hostgroup
        Format of the line that triggers function call::

        ENABLE_HOSTGROUP_SVC_NOTIFICATIONS;<hostgroup_name>

        :param hostgroup: hostgroup to enable
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :return: None
        """
        for host in hostgroup:
            for service in host.services:
                self.ENABLE_SVC_NOTIFICATIONS(service)

    def ENABLE_HOST_AND_CHILD_NOTIFICATIONS(self, host):
        """DOES NOTHING (Should enable host notifications and its child)
        Format of the line that triggers function call::

        ENABLE_HOST_AND_CHILD_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        pass

    def ENABLE_HOST_CHECK(self, host):
        """Enable checks for a host
        Format of the line that triggers function call::

        ENABLE_HOST_CHECK;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.active_checks_enabled:
            host.active_checks_enabled = True
            host.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.sched.get_and_register_status_brok(host)

    def ENABLE_HOST_EVENT_HANDLER(self, host):
        """Enable event handlers for a host
        Format of the line that triggers function call::

        ENABLE_HOST_EVENT_HANDLER;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.event_handler_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            host.event_handler_enabled = True
            self.sched.get_and_register_status_brok(host)

    def ENABLE_HOST_FLAP_DETECTION(self, host):
        """Enable flap detection for a host
        Format of the line that triggers function call::

        ENABLE_HOST_FLAP_DETECTION;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.flap_detection_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            host.flap_detection_enabled = True
            self.sched.get_and_register_status_brok(host)

    def ENABLE_HOST_FRESHNESS_CHECKS(self):
        """Enable freshness checks (globally)
        Format of the line that triggers function call::

        ENABLE_HOST_FRESHNESS_CHECKS

        :return: None
        """
        if not self.conf.check_host_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_host_freshness = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_HOST_NOTIFICATIONS(self, host):
        """Enable notifications for a host
        Format of the line that triggers function call::

        ENABLE_HOST_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.notifications_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            host.notifications_enabled = True
            self.sched.get_and_register_status_brok(host)

    def ENABLE_HOST_SVC_CHECKS(self, host):
        """Enable service checks for a host
        Format of the line that triggers function call::

        ENABLE_HOST_SVC_CHECKS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for s in host.services:
            self.ENABLE_SVC_CHECK(s)

    def ENABLE_HOST_SVC_NOTIFICATIONS(self, host):
        """Enable services notifications for a host
        Format of the line that triggers function call::

        ENABLE_HOST_SVC_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        for s in host.services:
            self.ENABLE_SVC_NOTIFICATIONS(s)
            self.sched.get_and_register_status_brok(s)

    def ENABLE_NOTIFICATIONS(self):
        """Enable notifications (globally)
        Format of the line that triggers function call::

        ENABLE_NOTIFICATIONS

        :return: None
        """
        if not self.conf.enable_notifications:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            self.conf.enable_notifications = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_PASSIVE_HOST_CHECKS(self, host):
        """Enable passive checks for a host
        Format of the line that triggers function call::

        ENABLE_PASSIVE_HOST_CHECKS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.passive_checks_enabled:
            host.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            host.passive_checks_enabled = True
            self.sched.get_and_register_status_brok(host)

    def ENABLE_PASSIVE_SVC_CHECKS(self, service):
        """Enable passive checks for a service
        Format of the line that triggers function call::

        ENABLE_PASSIVE_SVC_CHECKS;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.passive_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            service.passive_checks_enabled = True
            self.sched.get_and_register_status_brok(service)

    def ENABLE_PERFORMANCE_DATA(self):
        """Enable performance data processing (globally)
        Format of the line that triggers function call::

        ENABLE_PERFORMANCE_DATA

        :return: None
        """
        if not self.conf.process_performance_data:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PERFORMANCE_DATA_ENABLED"].value
            self.conf.process_performance_data = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_SERVICEGROUP_HOST_CHECKS(self, servicegroup):
        """Enable host checks for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_HOST_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_HOST_CHECK(service.host)

    def ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS(self, servicegroup):
        """Enable host notifications for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_HOST_NOTIFICATIONS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_HOST_NOTIFICATIONS(service.host)

    def ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS(self, servicegroup):
        """Enable passive host checks for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_PASSIVE_HOST_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_PASSIVE_HOST_CHECKS(service.host)

    def ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS(self, servicegroup):
        """Enable passive service checks for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_PASSIVE_SVC_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_PASSIVE_SVC_CHECKS(service)

    def ENABLE_SERVICEGROUP_SVC_CHECKS(self, servicegroup):
        """Enable service checks for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_SVC_CHECKS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_SVC_CHECK(service)

    def ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS(self, servicegroup):
        """Enable service notifications for a servicegroup
        Format of the line that triggers function call::

        ENABLE_SERVICEGROUP_SVC_NOTIFICATIONS;<servicegroup_name>

        :param servicegroup: servicegroup to enable
        :type servicegroup: alignak.objects.servicegroup.Servicegroup
        :return: None
        """
        for service in servicegroup:
            self.ENABLE_SVC_NOTIFICATIONS(service)

    def ENABLE_SERVICE_FRESHNESS_CHECKS(self):
        """Enable service freshness checks (globally)
        Format of the line that triggers function call::

        ENABLE_SERVICE_FRESHNESS_CHECKS

        :return: None
        """
        if not self.conf.check_service_freshness:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_FRESHNESS_CHECKS_ENABLED"].value
            self.conf.check_service_freshness = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def ENABLE_SVC_CHECK(self, service):
        """Enable checks for a service
        Format of the line that triggers function call::

        ENABLE_SVC_CHECK;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.active_checks_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            service.active_checks_enabled = True
            self.sched.get_and_register_status_brok(service)

    def ENABLE_SVC_EVENT_HANDLER(self, service):
        """Enable event handlers for a service
        Format of the line that triggers function call::

        ENABLE_SVC_EVENT_HANDLER;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.event_handler_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_EVENT_HANDLER_ENABLED"].value
            service.event_handler_enabled = True
            self.sched.get_and_register_status_brok(service)

    def ENABLE_SVC_FLAP_DETECTION(self, service):
        """Enable flap detection for a service
        Format of the line that triggers function call::

        ENABLE_SVC_FLAP_DETECTION;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.flap_detection_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_FLAP_DETECTION_ENABLED"].value
            service.flap_detection_enabled = True
            self.sched.get_and_register_status_brok(service)

    def ENABLE_SVC_NOTIFICATIONS(self, service):
        """Enable notifications for a service
        Format of the line that triggers function call::

        ENABLE_SVC_NOTIFICATIONS;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.notifications_enabled:
            service.modified_attributes |= DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            service.notifications_enabled = True
            self.sched.get_and_register_status_brok(service)

    def PROCESS_FILE(self, file_name, delete):
        """DOES NOTHING (should process a file)
        Format of the line that triggers function call::

        PROCESS_FILE;<file_name>;<delete>

        :param file_name:  file to process
        :type file_name: str
        :param delete: delete after processing
        :type delete:
        :return: None
        """
        pass

    def PROCESS_HOST_CHECK_RESULT(self, host, status_code, plugin_output):
        """Process host check result
        Format of the line that triggers function call::

        PROCESS_HOST_CHECK_RESULT;<host_name>;<status_code>;<plugin_output>

        :param host: host to process check to
        :type host: alignak.objects.host.Host
        :param status_code: exit code of plugin
        :type status_code: int
        :param plugin_output: plugin output
        :type plugin_output: str
        :return: None
        TODO: say that check is PASSIVE
        """
        # raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            naglog_result(
                'info', 'PASSIVE HOST CHECK: %s;%d;%s'
                % (host.get_name().decode('utf8', 'ignore'),
                   status_code, plugin_output.decode('utf8', 'ignore'))
            )
        now = time.time()
        cls = host.__class__
        # If globally disable OR locally, do not launch
        if cls.accept_passive_checks and host.passive_checks_enabled:
            # Maybe the check is just too old, if so, bail out!
            if self.current_timestamp < host.last_chk:
                return

            c = host.launch_check(now, force=True)
            # Should not be possible to not find the check, but if so, don't crash
            if not c:
                logger.error('%s > Passive host check failed. None check launched !?',
                             host.get_full_name())
                return
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the host
            c.exit_status = status_code
            c.get_outputs(plugin_output, host.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = self.current_timestamp  # we are using the external command timestamps
            # Set the corresponding host's check_type to passive=1
            c.set_type_passive()
            self.sched.nb_check_received += 1
            # Ok now this result will be read by scheduler the next loop

    def PROCESS_HOST_OUTPUT(self, host, plugin_output):
        """Process host output
        Format of the line that triggers function call::

        PROCESS_HOST_OUTPUT;<host_name>;<plugin_output>

        :param host: host to process check to
        :type host: alignak.objects.host.Host
        :param plugin_output: plugin output
        :type plugin_output: str
        :return: None
        """
        self.PROCESS_HOST_CHECK_RESULT(host, host.state_id, plugin_output)

    def PROCESS_SERVICE_CHECK_RESULT(self, service, return_code, plugin_output):
        """Process service check result
        Format of the line that triggers function call::

        PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<return_code>;<plugin_output>

        :param service: service to process check to
        :type service: alignak.objects.service.Service
        :param return_code: exit code of plugin
        :type return_code: int
        :param plugin_output: plugin output
        :type plugin_output: str
        :return: None
        """
        # raise a PASSIVE check only if needed
        if self.conf.log_passive_checks:
            naglog_result('info', 'PASSIVE SERVICE CHECK: %s;%s;%d;%s'
                          % (service.host.get_name().decode('utf8', 'ignore'),
                             service.get_name().decode('utf8', 'ignore'),
                             return_code, plugin_output.decode('utf8', 'ignore')))
        now = time.time()
        cls = service.__class__
        # If globally disable OR locally, do not launch
        if cls.accept_passive_checks and service.passive_checks_enabled:
            # Maybe the check is just too old, if so, bail out!
            if self.current_timestamp < service.last_chk:
                return

            c = service.launch_check(now, force=True)
            # Should not be possible to not find the check, but if so, don't crash
            if not c:
                logger.error('%s > Passive service check failed. None check launched !?',
                             service.get_full_name())
                return
            # Now we 'transform the check into a result'
            # So exit_status, output and status is eaten by the service
            c.exit_status = return_code
            c.get_outputs(plugin_output, service.max_plugins_output_length)
            c.status = 'waitconsume'
            c.check_time = self.current_timestamp  # we are using the external command timestamps
            # Set the corresponding service's check_type to passive=1
            c.set_type_passive()
            self.sched.nb_check_received += 1
            # Ok now this result will be reap by scheduler the next loop

    def PROCESS_SERVICE_OUTPUT(self, service, plugin_output):
        """Process service output
        Format of the line that triggers function call::

        PROCESS_SERVICE_CHECK_RESULT;<host_name>;<service_description>;<plugin_output>

        :param service: service to process check to
        :type service: alignak.objects.service.Service
        :param plugin_output: plugin output
        :type plugin_output: str
        :return: None
        """
        self.PROCESS_SERVICE_CHECK_RESULT(service, service.state_id, plugin_output)

    def READ_STATE_INFORMATION(self):
        """DOES NOTHING (What it is supposed to do?)
        Format of the line that triggers function call::

        READ_STATE_INFORMATION

        :return: None
        """
        pass

    def REMOVE_HOST_ACKNOWLEDGEMENT(self, host):
        """Remove an acknowledgment on a host
        Format of the line that triggers function call::

        REMOVE_HOST_ACKNOWLEDGEMENT;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        host.unacknowledge_problem()

    def REMOVE_SVC_ACKNOWLEDGEMENT(self, service):
        """Remove an acknowledgment on a service
        Format of the line that triggers function call::

        REMOVE_SVC_ACKNOWLEDGEMENT;<host_name>;<service_description>

        :param service: service to edit
        :type service: alignak.objects.service.Service
        :return: None
        """
        service.unacknowledge_problem()

    def RESTART_PROGRAM(self):
        """Restart Alignak
        Format of the line that triggers function call::

        RESTART_PROGRAM

        :return: None
        """
        restart_cmd = self.commands.find_by_name('restart-alignak')
        if not restart_cmd:
            logger.error("Cannot restart Alignak : missing command named"
                         " 'restart-alignak'. Please add one")
            return
        restart_cmd_line = restart_cmd.command_line
        logger.warning("RESTART command : %s", restart_cmd_line)

        # Ok get an event handler command that will run in 15min max
        e = EventHandler(restart_cmd_line, timeout=900)
        # Ok now run it
        e.execute()
        # And wait for the command to finish
        while e.status not in ('done', 'timeout'):
            e.check_finished(64000)
        if e.status == 'timeout' or e.exit_status != 0:
            logger.error("Cannot restart Alignak : the 'restart-alignak' command failed with"
                         " the error code '%d' and the text '%s'.", e.exit_status, e.output)
            return
        # Ok here the command succeed, we can now wait our death
        naglog_result('info', "%s" % (e.output))

    def RELOAD_CONFIG(self):
        """Reload Alignak configuration
        Format of the line that triggers function call::

        RELOAD_CONFIG

        :return: None
        """
        reload_cmd = self.commands.find_by_name('reload-alignak')
        if not reload_cmd:
            logger.error("Cannot restart Alignak : missing command"
                         " named 'reload-alignak'. Please add one")
            return
        reload_cmd_line = reload_cmd.command_line
        logger.warning("RELOAD command : %s", reload_cmd_line)

        # Ok get an event handler command that will run in 15min max
        e = EventHandler(reload_cmd_line, timeout=900)
        # Ok now run it
        e.execute()
        # And wait for the command to finish
        while e.status not in ('done', 'timeout'):
            e.check_finished(64000)
        if e.status == 'timeout' or e.exit_status != 0:
            logger.error("Cannot reload Alignak configuration: the 'reload-alignak' command failed"
                         " with the error code '%d' and the text '%s'.", e.exit_status, e.output)
            return
        # Ok here the command succeed, we can now wait our death
        naglog_result('info', "%s" % (e.output))

    def SAVE_STATE_INFORMATION(self):
        """DOES NOTHING (What it is supposed to do?)
        Format of the line that triggers function call::

        SAVE_STATE_INFORMATION

        :return: None
        """
        pass

    def SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME(self, host, start_time, end_time,
                                             fixed, trigger_id, duration, author, comment):
        """DOES NOTHING (Should create host downtime and start it?)
        Format of the line that triggers function call::

        SCHEDULE_AND_PROPAGATE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>

        :return: None
        """
        pass

    def SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME(self, host, start_time, end_time, fixed,
                                                       trigger_id, duration, author, comment):
        """DOES NOTHING (Should create triggered host downtime and start it?)
        Format of the line that triggers function call::

        SCHEDULE_AND_PROPAGATE_TRIGGERED_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;
        <trigger_id>;<duration>;<author>;<comment>

        :return: None
        """
        pass

    def SCHEDULE_CONTACT_DOWNTIME(self, contact, start_time, end_time, author, comment):
        """Schedule contact downtime
        Format of the line that triggers function call::

        SCHEDULE_CONTACT_DOWNTIME;<contact_name>;<start_time>;<end_time>;<author>;<comment>

        :param contact: contact to put in downtime
        :type contact: alignak.objects.contact.Contact
        :param start_time: downtime start time
        :type start_time: int
        :param end_time: downtime end time
        :type end_time: int
        :param author: downtime author
        :type author: str
        :param comment: text comment
        :type comment: str
        :return: None
        """
        dt = ContactDowntime(contact, start_time, end_time, author, comment)
        contact.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(contact)

    def SCHEDULE_FORCED_HOST_CHECK(self, host, check_time):
        """Schedule a forced check on a host
        Format of the line that triggers function call::

        SCHEDULE_FORCED_HOST_CHECK;<host_name>;<check_time>

        :param host: host to check
        :type host: alignak.object.host.Host
        :param check_time: time to check
        :type check_time: int
        :return: None
        """
        host.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    def SCHEDULE_FORCED_HOST_SVC_CHECKS(self, host, check_time):
        """Schedule a forced check on all services of a host
        Format of the line that triggers function call::

        SCHEDULE_FORCED_HOST_SVC_CHECKS;<host_name>;<check_time>

        :param host: host to check
        :type host: alignak.object.host.Host
        :param check_time: time to check
        :type check_time: int
        :return: None
        """
        for s in host.services:
            self.SCHEDULE_FORCED_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    def SCHEDULE_FORCED_SVC_CHECK(self, service, check_time):
        """Schedule a forced check on a service
        Format of the line that triggers function call::

        SCHEDULE_FORCED_SVC_CHECK;<host_name>;<service_description>;<check_time>

        :param service: service to check
        :type service: alignak.object.service.Service
        :param check_time: time to check
        :type check_time: int
        :return: None
        """
        service.schedule(force=True, force_time=check_time)
        self.sched.get_and_register_status_brok(service)

    def SCHEDULE_HOSTGROUP_HOST_DOWNTIME(self, hostgroup, start_time, end_time, fixed,
                                         trigger_id, duration, author, comment):
        """Schedule a downtime for each host of a hostgroup
        Format of the line that triggers function call::

        SCHEDULE_HOSTGROUP_HOST_DOWNTIME;<hostgroup_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>

        :param hostgroup: hostgroup to schedule
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed:
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        for host in hostgroup:
            self.SCHEDULE_HOST_DOWNTIME(host, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment)

    def SCHEDULE_HOSTGROUP_SVC_DOWNTIME(self, hostgroup, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment):
        """Schedule a downtime for each service of each host of a hostgroup
        Format of the line that triggers function call::

        SCHEDULE_HOSTGROUP_SVC_DOWNTIME;;<hostgroup_name>;<start_time>;<end_time>;<fixed>;
        <trigger_id>;<duration>;<author>;<comment>

        :param hostgroup: hostgroup to schedule
        :type hostgroup: alignak.objects.hostgroup.Hostgroup
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed:
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        for host in hostgroup:
            for s in host.services:
                self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                           trigger_id, duration, author, comment)

    def SCHEDULE_HOST_CHECK(self, host, check_time):
        """Schedule a check on a host
        Format of the line that triggers function call::

        SCHEDULE_HOST_CHECK;<host_name>;<check_time>

        :param host: host to check
        :type host: alignak.object.host.Host
        :param check_time: time to check
        :type check_time:
        :return: None
        """
        host.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(host)

    def SCHEDULE_HOST_DOWNTIME(self, host, start_time, end_time, fixed,
                               trigger_id, duration, author, comment):
        """Schedule a host downtime
        Format of the line that triggers function call::

        SCHEDULE_HOST_DOWNTIME;<host_name>;<start_time>;<end_time>;<fixed>;
        <trigger_id>;<duration>;<author>;<comment>

        :param host: host to schedule downtime
        :type host: alignak.object.host.Host
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed: bool
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        dt = Downtime(host, start_time, end_time, fixed, trigger_id, duration, author, comment)
        host.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(host)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)

    def SCHEDULE_HOST_SVC_CHECKS(self, host, check_time):
        """Schedule a check on all services of a host
        Format of the line that triggers function call::

        SCHEDULE_HOST_SVC_CHECKS;<host_name>;<check_time>

        :param host: host to check
        :type host: alignak.object.host.Host
        :param check_time: time to check
        :type check_time:
        :return: None
        """
        for s in host.services:
            self.SCHEDULE_SVC_CHECK(s, check_time)
            self.sched.get_and_register_status_brok(s)

    def SCHEDULE_HOST_SVC_DOWNTIME(self, host, start_time, end_time, fixed,
                                   trigger_id, duration, author, comment):
        """Schedule a service downtime for each service of a host
        Format of the line that triggers function call::

        SCHEDULE_HOST_SVC_DOWNTIME;<host_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>

        :param host: host to schedule downtime
        :type host: alignak.object.host.Host
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed: bool
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        for s in host.services:
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                       trigger_id, duration, author, comment)

    def SCHEDULE_SERVICEGROUP_HOST_DOWNTIME(self, servicegroup, start_time, end_time,
                                            fixed, trigger_id, duration, author, comment):
        """Schedule a host downtime for each host of services in a servicegroup
        Format of the line that triggers function call::

        SCHEDULE_SERVICEGROUP_HOST_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;<fixed>;
        <trigger_id>;<duration>;<author>;<comment>

        :param servicegroup: servicegroup to schedule downtime
        :type servicegroup: alignak.object.servicegroup.Servicegroup
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed: bool
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        for h in [s.host for s in servicegroup.get_services()]:
            self.SCHEDULE_HOST_DOWNTIME(h, start_time, end_time, fixed,
                                        trigger_id, duration, author, comment)

    def SCHEDULE_SERVICEGROUP_SVC_DOWNTIME(self, servicegroup, start_time, end_time,
                                           fixed, trigger_id, duration, author, comment):
        """Schedule a service downtime for each service of a servicegroup
        Format of the line that triggers function call::

        SCHEDULE_SERVICEGROUP_SVC_DOWNTIME;<servicegroup_name>;<start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>

        :param servicegroup: servicegroup to schedule downtime
        :type servicegroup: alignak.object.servicegroup.Servicegroup
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed: bool
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        for s in servicegroup.get_services():
            self.SCHEDULE_SVC_DOWNTIME(s, start_time, end_time, fixed,
                                       trigger_id, duration, author, comment)

    def SCHEDULE_SVC_CHECK(self, service, check_time):
        """Schedule a check on a service
        Format of the line that triggers function call::

        SCHEDULE_SVC_CHECK;<host_name>;<service_description>;<check_time>

        :param service: service to check
        :type service: alignak.object.service.Service
        :param check_time: time to check
        :type check_time:
        :return: None
        """
        service.schedule(force=False, force_time=check_time)
        self.sched.get_and_register_status_brok(service)

    def SCHEDULE_SVC_DOWNTIME(self, service, start_time, end_time, fixed,
                              trigger_id, duration, author, comment):
        """Schedule a service downtime
        Format of the line that triggers function call::

        SCHEDULE_SVC_DOWNTIME;<host_name>;<service_description><start_time>;<end_time>;
        <fixed>;<trigger_id>;<duration>;<author>;<comment>

        :param service: service to check
        :type service: alignak.object.service.Service
        :param start_time: downtime start time
        :type start_time:
        :param end_time: downtime end time
        :type end_time:
        :param fixed: is downtime fixed
        :type fixed: bool
        :param trigger_id: downtime id that triggered this one
        :type trigger_id: int
        :param duration: downtime duration
        :type duration: int
        :param author: downtime author
        :type author: str
        :param comment: downtime comment
        :type comment: str
        :return: None
        """
        dt = Downtime(service, start_time, end_time, fixed, trigger_id, duration, author, comment)
        service.add_downtime(dt)
        self.sched.add(dt)
        self.sched.get_and_register_status_brok(service)
        if trigger_id != 0 and trigger_id in self.sched.downtimes:
            self.sched.downtimes[trigger_id].trigger_me(dt)

    def SEND_CUSTOM_HOST_NOTIFICATION(self, host, options, author, comment):
        """DOES NOTHING (Should send a custom notification)
        Format of the line that triggers function call::

        SEND_CUSTOM_HOST_NOTIFICATION;<host_name>;<options>;<author>;<comment>

        :param host: host to send notif for
        :type host: alignak.object.host.Host
        :param options: notification options
        :type options:
        :param author: notification author
        :type author: str
        :param comment: notification text
        :type comment: str
        :return: None
        """
        pass

    def SEND_CUSTOM_SVC_NOTIFICATION(self, service, options, author, comment):
        """DOES NOTHING (Should send a custom notification)
        Format of the line that triggers function call::

        SEND_CUSTOM_SVC_NOTIFICATION;<host_name>;<service_description>;<options>;<author>;<comment>>

        :param service: service to send notif for
        :type service: alignak.object.service.Service
        :param options: notification options
        :type options:
        :param author: notification author
        :type author: str
        :param comment: notification text
        :type comment: str
        :return: None
        """
        pass

    def SET_HOST_NOTIFICATION_NUMBER(self, host, notification_number):
        """DOES NOTHING (Should set host notification number)
        Format of the line that triggers function call::

        SET_HOST_NOTIFICATION_NUMBER;<host_name>;<notification_number>

        :param host: host to edit
        :type host: alignak.object.host.Host
        :param notification_number: new value to set
        :type notification_number:
        :return: None
        """
        pass

    def SET_SVC_NOTIFICATION_NUMBER(self, service, notification_number):
        """DOES NOTHING (Should set host notification number)
        Format of the line that triggers function call::

        SET_SVC_NOTIFICATION_NUMBER;<host_name>;<service_description>;<notification_number>

        :param service: service to edit
        :type service: alignak.object.service.Service
        :param notification_number: new value to set
        :type notification_number:
        :return: None
        """
        pass

    def SHUTDOWN_PROGRAM(self):
        """DOES NOTHING (Should shutdown Alignak)
        Format of the line that triggers function call::

        SHUTDOWN_PROGRAM

        :return: None
        """
        pass

    def START_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        """Enable passive host check submission (globally)
        Format of the line that triggers function call::

        START_ACCEPTING_PASSIVE_HOST_CHECKS

        :return: None
        """
        if not self.conf.accept_passive_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_host_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def START_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        """Enable passive service check submission (globally)
        Format of the line that triggers function call::

        START_ACCEPTING_PASSIVE_SVC_CHECKS

        :return: None
        """
        if not self.conf.accept_passive_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_service_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def START_EXECUTING_HOST_CHECKS(self):
        """Enable host check execution (globally)
        Format of the line that triggers function call::

        START_EXECUTING_HOST_CHECKS

        :return: None
        """
        if not self.conf.execute_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_host_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def START_EXECUTING_SVC_CHECKS(self):
        """Enable service check execution (globally)
        Format of the line that triggers function call::

        START_EXECUTING_SVC_CHECKS

        :return: None
        """
        if not self.conf.execute_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_service_checks = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def START_OBSESSING_OVER_HOST(self, host):
        """Enable obsessing over host for a host
        Format of the line that triggers function call::

        START_OBSESSING_OVER_HOST;<host_name>

        :param host: host to obsess over
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.obsess_over_host:
            host.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            host.obsess_over_host = True
            self.sched.get_and_register_status_brok(host)

    def START_OBSESSING_OVER_HOST_CHECKS(self):
        """Enable obssessing over host check (globally)
        Format of the line that triggers function call::

        START_OBSESSING_OVER_HOST_CHECKS

        :return: None
        """
        if not self.conf.obsess_over_hosts:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_hosts = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def START_OBSESSING_OVER_SVC(self, service):
        """Enable obssessing over service for a service
        Format of the line that triggers function call::

        START_OBSESSING_OVER_SVC;<host_name>;<service_description>

        :param service: service to obssess over
        :type service: alignak.objects.service.Service
        :return: None
        """
        if not service.obsess_over_service:
            service.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            service.obsess_over_service = True
            self.sched.get_and_register_status_brok(service)

    def START_OBSESSING_OVER_SVC_CHECKS(self):
        """Enable obssessing over service check (globally)
        Format of the line that triggers function call::

        START_OBSESSING_OVER_SVC_CHECKS

        :return: None
        """
        if not self.conf.obsess_over_services:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_services = True
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_ACCEPTING_PASSIVE_HOST_CHECKS(self):
        """Disable passive host check submission (globally)
        Format of the line that triggers function call::

        STOP_ACCEPTING_PASSIVE_HOST_CHECKS

        :return: None
        """
        if self.conf.accept_passive_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_host_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_ACCEPTING_PASSIVE_SVC_CHECKS(self):
        """Disable passive service check submission (globally)
        Format of the line that triggers function call::

        STOP_ACCEPTING_PASSIVE_SVC_CHECKS

        :return: None
        """
        if self.conf.accept_passive_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_PASSIVE_CHECKS_ENABLED"].value
            self.conf.accept_passive_service_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_EXECUTING_HOST_CHECKS(self):
        """Disable host check execution (globally)
        Format of the line that triggers function call::

        STOP_EXECUTING_HOST_CHECKS

        :return: None
        """
        if self.conf.execute_host_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_host_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_EXECUTING_SVC_CHECKS(self):
        """Disable service check execution (globally)
        Format of the line that triggers function call::

        STOP_EXECUTING_SVC_CHECKS

        :return: None
        """
        if self.conf.execute_service_checks:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_ACTIVE_CHECKS_ENABLED"].value
            self.conf.execute_service_checks = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_OBSESSING_OVER_HOST(self, host):
        """Disable obsessing over host for a host
        Format of the line that triggers function call::

        STOP_OBSESSING_OVER_HOST;<host_name>

        :param host: host to obsess over
        :type host: alignak.objects.host.Host
        :return: None
        """
        if host.obsess_over_host:
            host.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            host.obsess_over_host = False
            self.sched.get_and_register_status_brok(host)

    def STOP_OBSESSING_OVER_HOST_CHECKS(self):
        """Disable obssessing over host check (globally)
        Format of the line that triggers function call::

        STOP_OBSESSING_OVER_HOST_CHECKS

        :return: None
        """
        if self.conf.obsess_over_hosts:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_hosts = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def STOP_OBSESSING_OVER_SVC(self, service):
        """Disable obssessing over service for a service
        Format of the line that triggers function call::

        STOP_OBSESSING_OVER_SVC;<host_name>;<service_description>

        :param service: service to obssess over
        :type service: alignak.objects.service.Service
        :return: None
        """
        if service.obsess_over_service:
            service.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            service.obsess_over_service = False
            self.sched.get_and_register_status_brok(service)

    def STOP_OBSESSING_OVER_SVC_CHECKS(self):
        """Disable obssessing over service check (globally)
        Format of the line that triggers function call::

        STOP_OBSESSING_OVER_SVC_CHECKS

        :return: None
        """
        if self.conf.obsess_over_services:
            self.conf.modified_attributes |= DICT_MODATTR["MODATTR_OBSESSIVE_HANDLER_ENABLED"].value
            self.conf.obsess_over_services = False
            self.conf.explode_global_conf()
            self.sched.get_and_register_update_program_status_brok()

    def LAUNCH_SVC_EVENT_HANDLER(self, service):
        """Launch event handler for a service
        Format of the line that triggers function call::

        LAUNCH_SVC_EVENT_HANDLER;<host_name>;<service_description>

        :param service: service to execute the event handler
        :type service: alignak.objects.service.Service
        :return: None
        """
        service.get_event_handlers(externalcmd=True)

    def LAUNCH_HOST_EVENT_HANDLER(self, host):
        """Launch event handler for a service
        Format of the line that triggers function call::

        LAUNCH_HOST_EVENT_HANDLER;<host_name>

        :param host: host to execute the event handler
        :type host: alignak.objects.host.Host
        :return: None
        """
        host.get_event_handlers(externalcmd=True)

    def ADD_SIMPLE_HOST_DEPENDENCY(self, son, father):
        """Add a host dependency between son and father
        Format of the line that triggers function call::

        ADD_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>

        :param son: son of dependency
        :type son: alignak.objects.host.Host
        :param father: father of dependency
        :type father: alignak.objects.host.Host
        :return: None
        """
        if not son.is_linked_with_host(father):
            logger.debug("Doing simple link between %s and %s", son.get_name(), father.get_name())
            # Flag them so the modules will know that a topology change
            # happened
            son.topology_change = True
            father.topology_change = True
            # Now do the work
            # Add a dep link between the son and the father
            son.add_host_act_dependency(father, ['w', 'u', 'd'], None, True)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)

    def DEL_HOST_DEPENDENCY(self, son, father):
        """Delete a host dependency between son and father
        Format of the line that triggers function call::

        DEL_SIMPLE_HOST_DEPENDENCY;<host_name>;<host_name>

        :param son: son of dependency
        :type son: alignak.objects.host.Host
        :param father: father of dependency
        :type father: alignak.objects.host.Host
        :return: None
        """
        if son.is_linked_with_host(father):
            logger.debug("Removing simple link between %s and %s",
                         son.get_name(), father.get_name())
            # Flag them so the modules will know that a topology change
            # happened
            son.topology_change = True
            father.topology_change = True
            # Now do the work
            son.del_host_act_dependency(father)
            self.sched.get_and_register_status_brok(son)
            self.sched.get_and_register_status_brok(father)

    def ADD_SIMPLE_POLLER(self, realm_name, poller_name, address, port):
        """Add a poller
        Format of the line that triggers function call::

        ADD_SIMPLE_POLLER;realm_name;poller_name;address;port

        :param realm_name: realm for the new poller
        :type realm_name: str
        :param poller_name: new poller name
        :type poller_name: str
        :param address: new poller address
        :type address: str
        :param port: new poller port
        :type port: int
        :return: None
        """
        logger.debug("I need to add the poller (%s, %s, %s, %s)",
                     realm_name, poller_name, address, port)

        # First we look for the realm
        r = self.conf.realms.find_by_name(realm_name)
        if r is None:
            logger.debug("Sorry, the realm %s is unknown", realm_name)
            return

        logger.debug("We found the realm: %s", str(r))
        # TODO: backport this in the config class?
        # We create the PollerLink object
        t = {'poller_name': poller_name, 'address': address, 'port': port}
        p = PollerLink(t)
        p.fill_default()
        p.prepare_for_conf()
        parameters = {'max_plugins_output_length': self.conf.max_plugins_output_length}
        p.add_global_conf_parameters(parameters)
        self.arbiter.conf.pollers[p.id] = p
        self.arbiter.dispatcher.elements.append(p)
        self.arbiter.dispatcher.satellites.append(p)
        r.pollers.append(p)
        r.count_pollers()
        r.fill_potential_satellites_by_type('pollers')
        logger.debug("Poller %s added", poller_name)
        logger.debug("Potential %s", str(r.get_potential_satellites_by_type('poller')))


if __name__ == '__main__':

    FIFO_PATH = '/tmp/my_fifo'

    if os.path.exists(FIFO_PATH):
        os.unlink(FIFO_PATH)

    if not os.path.exists(FIFO_PATH):
        os.umask(0)
        os.mkfifo(FIFO_PATH, 0660)
        my_fifo = open(FIFO_PATH, 'w+')
        logger.debug("my_fifo: %s", my_fifo)

    logger.debug(open(FIFO_PATH, 'r').readline())