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
#     Thibault Cohen, titilambert@gmail.com
#     Jean Gabes, naparuba@gmail.com
#     Zoran Zaric, zz@zoranzaric.de

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

"""
 This class is an application that launches actions like
 notifications or event handlers
 The reactionner listens to the Arbiter for the configuration sent through
 the given port as first argument.
 The configuration sent by the arbiter specifies from which schedulers the
 will take actions.
 When the reactionner is already launched and has its own conf, it keeps
 on listening the arbiter (one a timeout)
 In case the arbiter has a new conf to send, the reactionner forget its old
 schedulers (and the associated actions) and take the new ones instead.
"""

from alignak.daemons.reactionnerdaemon import Reactionner
from alignak.util import parse_daemon_args


def main():
    """Parse args and run main daemon function

    :return: None
    """
    args = parse_daemon_args()
    daemon = Reactionner(debug=args.debug_file is not None, **args.__dict__)
    daemon.main()


if __name__ == '__main__':
    main()
