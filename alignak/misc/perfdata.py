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
#     Sebastien Coavoux, s.coavoux@free.fr
#     aviau, alexandre.viau@savoirfairelinux.com
#     Nicolas Dupeux, nicolas@dupeux.net
#     Grégory Starck, g.starck@gmail.com
#     Jean-Claude Computing, jeanclaude.computing@gmail.com
#     Thibault Cohen, titilambert@gmail.com
#     Jean Gabes, naparuba@gmail.com
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
"""
This module provide classes to handle performance data from monitoring plugin output
"""
import re
from alignak.util import to_best_int_float

perfdata_split_pattern = re.compile(r'([^=]+=\S+)')
# TODO: Improve this regex to not match strings like this:
# 'metric=45+e-456.56unit;50;80;0;45+-e45e-'
metric_pattern = \
    re.compile(
        r'^([^=]+)=([\d\.\-\+eE]+)([\w\/%]*)'
        r';?([\d\.\-\+eE:~@]+)?;?([\d\.\-\+eE:~@]+)?;?([\d\.\-\+eE]+)?;?([\d\.\-\+eE]+)?;?\s*'
    )


def guess_int_or_float(val):
    """Wrapper for Util.to_best_int_float
    Basically cast into float or int and compare value
    If they are equal then there is no coma so return integer

    :param val: value to cast
    :return: value casted into int, float or None
    :rtype: int | float | NoneType
    """
    try:
        return to_best_int_float(val)
    except Exception, exp:
        return None


class Metric:
    """
    Class providing a small abstraction for one metric of a Perfdatas class
    """
    def __init__(self, s):
        self.name = self.value = self.uom = \
            self.warning = self.critical = self.min = self.max = None
        s = s.strip()
        # print "Analysis string", s
        r = metric_pattern.match(s)
        if r:
            # Get the name but remove all ' in it
            self.name = r.group(1).replace("'", "")
            self.value = guess_int_or_float(r.group(2))
            self.uom = r.group(3)
            self.warning = guess_int_or_float(r.group(4))
            self.critical = guess_int_or_float(r.group(5))
            self.min = guess_int_or_float(r.group(6))
            self.max = guess_int_or_float(r.group(7))
            # print 'Name', self.name
            # print "Value", self.value
            # print "Res", r
            # print r.groups()
            if self.uom == '%':
                self.min = 0
                self.max = 100

    def __str__(self):
        s = "%s=%s%s" % (self.name, self.value, self.uom)
        if self.warning:
            s = s + ";%s" % (self.warning)
        if self.critical:
            s = s + ";%s" % (self.critical)
        return s


class PerfDatas:
    """
    Class providing performance data extracted from a check output
    """
    def __init__(self, s):
        s = s or ''
        elts = perfdata_split_pattern.findall(s)
        elts = [e for e in elts if e != '']
        self.metrics = {}
        for e in elts:
            m = Metric(e)
            if m.name is not None:
                self.metrics[m.name] = m

    def __iter__(self):
        return self.metrics.itervalues()

    def __len__(self):
        return len(self.metrics)

    def __getitem__(self, key):
        return self.metrics[key]

    def __contains__(self, key):
        return key in self.metrics