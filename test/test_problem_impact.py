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
#     aviau, alexandre.viau@savoirfairelinux.com
#     Grégory Starck, g.starck@gmail.com
#     Sebastien Coavoux, s.coavoux@free.fr
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

#
# This file is used to test host- and service-downtimes.
#

from alignak_test import *


class TestProblemImpact(AlignakTest):
    def setUp(self):
        self.setup_with_file(['etc/alignak_problem_impact.cfg'])

    def test_problems_impacts(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification

        # First initialize routers 0 and 1
        now = time.time()

        # The problem_impact_state change should be enabled in the configuration
        self.assertEqual(True, self.conf.enable_problem_impacts_states_change)

        host_router_0 = self.sched.hosts.find_by_name("test_router_0")
        host_router_0.checks_in_progress = []
        self.assertEqual(2, host_router_0.business_impact)
        host_router_1 = self.sched.hosts.find_by_name("test_router_1")
        host_router_1.checks_in_progress = []
        self.assertEqual(2, host_router_1.business_impact)

        # Then initialize host under theses routers
        host_0 = self.sched.hosts.find_by_name("test_host_0")
        host_0.checks_in_progress = []
        host_1 = self.sched.hosts.find_by_name("test_host_1")
        host_1.checks_in_progress = []

        all_hosts = [host_router_0, host_router_1, host_0, host_1]
        all_routers = [host_router_0, host_router_1]
        all_servers = [host_0, host_1]

        #--------------------------------------------------------------
        # initialize host states as UP
        #--------------------------------------------------------------
        print "- 4 x UP -------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 0, 'UP'], [host_router_1, 0, 'UP'], [host_0, 0, 'UP'], [host_1, 0, 'UP']], do_sleep=False)

        for h in all_hosts:
            self.assertEqual('UP', h.state)
            self.assertEqual('HARD', h.state_type)

        #--------------------------------------------------------------
        # Now we add some problems to routers
        #--------------------------------------------------------------
        print "- routers get DOWN /SOFT-------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        # Max attempt is at 5, should be soft now
        for h in all_routers:
            self.assertEqual('DOWN', h.state)
            self.assertEqual('SOFT', h.state_type)

        print "- routers get DOWN /HARD-------------------------------------"
        # Now put 4 more checks so we get DOWN/HARD
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)

        # Max attempt is reach, should be HARD now
        for h in all_routers:
            self.assertEqual('DOWN', h.state)
            self.assertEqual('HARD', h.state_type)

        #--------------------------------------------------------------
        # Routers get HARD/DOWN
        # should be problems now!
        #--------------------------------------------------------------
        # Now check in the brok generation too
        host_router_0_brok = host_router_0.get_update_status_brok()
        host_router_0_brok.prepare()
        host_router_1_brok = host_router_1.get_update_status_brok()
        host_router_1_brok.prepare()

        # Should be problems and have sub servers as impacts
        for h in all_routers:
            self.assertEqual(True, h.is_problem)
            # Now routers are problems, they should have take the max
            # business_impact value ofthe impacts, so here 5
            self.assertEqual(5, h.business_impact)
            for s in all_servers:
                self.assertIn(s.uuid, h.impacts)
                self.assertIn(s.uuid,  host_router_0_brok.data['impacts'])
                self.assertIn(s.uuid,  host_router_1_brok.data['impacts'])

        # Should have host notification, but it's not so simple:
        # our contact say: not under 5, and our hosts are 2. But
        # the impacts have huge business_impact, so the hosts gain such business_impact
        self.assert_any_log_match('HOST NOTIFICATION.*;')
        self.show_and_clear_logs()


        # Now impacts should really be .. impacts :)
        for s in all_servers:
            self.assertEqual(True, s.is_impact)
            self.assertEqual('UNREACHABLE', s.state)
            # And check the services are impacted too
            for svc_id in s.services:
                svc = self.sched.services[svc_id]
                print "Service state", svc.state
                self.assertEqual('UNKNOWN', svc.state)
                self.assertIn(svc.uuid,  host_router_0_brok.data['impacts'])
                self.assertIn(svc.uuid,  host_router_1_brok.data['impacts'])
                brk_svc = svc.get_update_status_brok()
                brk_svc.prepare()
                self.assertSetEqual(set([host_router_0.uuid, host_router_1.uuid]), set(brk_svc.data['source_problems']))
            for h in all_routers:
                self.assertIn(h.uuid, s.source_problems)
                brk_hst = s.get_update_status_brok()
                brk_hst.prepare()
                self.assertIn(h.uuid, brk_hst.data['source_problems'])

        #--------------------------------------------------------------
        # One router get UP now
        #--------------------------------------------------------------
        print "- 1 X UP for a router ------------------------------"
        # Ok here the problem/impact propagation is Checked. Now what
        # if one router get back? :)
        self.scheduler_loop(1, [[host_router_0, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assertEqual('UP', host_router_0.state)
        self.assertEqual('HARD', host_router_0.state_type)

        # And should not be a problem any more!
        self.assertEqual(False, host_router_0.is_problem)
        self.assertEqual([], host_router_0.impacts)

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assertEqual(True, s.is_impact)
            self.assertEqual([host_router_1.uuid], s.source_problems)

        #--------------------------------------------------------------
        # The other router get UP :)
        #--------------------------------------------------------------
        print "- 1 X UP for the last router ------------------------------"
        # What is the last router get back? :)
        self.scheduler_loop(1, [[host_router_1, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assertEqual('UP', host_router_1.state)
        self.assertEqual('HARD', host_router_1.state_type)

        # And should not be a problem any more!
        self.assertEqual(False, host_router_1.is_problem)
        self.assertEqual([], host_router_1.impacts)

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assertEqual(False, s.is_impact)
            self.assertEqual('UP', s.state)
            self.assertEqual([], s.source_problems)

        # And our "business_impact" should have failed back to our
        # conf value, so 2
        self.assertEqual(2, host_router_0.business_impact)
        self.assertEqual(2, host_router_1.business_impact)
        # It's done :)

    def test_problems_impacts_with_crit_mod(self):
        self.print_header()
        # retry_interval 2
        # critical notification
        # run loop -> another notification

        # First initialize routers 0 and 1
        now = time.time()

        # The problem_impact_state change should be enabled in the configuration
        self.assertEqual(True, self.conf.enable_problem_impacts_states_change)

        host_router_0 = self.sched.hosts.find_by_name("test_router_0")
        host_router_0.checks_in_progress = []
        self.assertEqual(2, host_router_0.business_impact)
        host_router_1 = self.sched.hosts.find_by_name("test_router_1")
        host_router_1.checks_in_progress = []
        self.assertEqual(2, host_router_1.business_impact)

        # Then initialize host under theses routers
        host_0 = self.sched.hosts.find_by_name("test_host_0")
        host_0.checks_in_progress = []
        host_1 = self.sched.hosts.find_by_name("test_host_1")
        host_1.checks_in_progress = []

        all_hosts = [host_router_0, host_router_1, host_0, host_1]
        all_routers = [host_router_0, host_router_1]
        all_servers = [host_0, host_1]

        # Our crit mod that will allow us to play with on the fly
        # business_impact modulation
        critmod = self.sched.conf.businessimpactmodulations.find_by_name('Raise')
        self.assertIsNot(critmod, None)

        # We lie here, from now we do not want criticities
        for h in all_hosts:
            for s in h.services:
                self.sched.services[s].business_impact = 2

        #--------------------------------------------------------------
        # initialize host states as UP
        #--------------------------------------------------------------
        print "- 4 x UP -------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 0, 'UP'], [host_router_1, 0, 'UP'], [host_0, 0, 'UP'], [host_1, 0, 'UP']], do_sleep=False)

        for h in all_hosts:
            self.assertEqual('UP', h.state)
            self.assertEqual('HARD', h.state_type)

        #--------------------------------------------------------------
        # Now we add some problems to routers
        #--------------------------------------------------------------
        print "- routers get DOWN /SOFT-------------------------------------"
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        # Max attempt is at 5, should be soft now
        for h in all_routers:
            self.assertEqual('DOWN', h.state)
            self.assertEqual('SOFT', h.state_type)

        print "- routers get DOWN /HARD-------------------------------------"
        # Now put 4 more checks so we get DOWN/HARD
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)
        self.scheduler_loop(1, [[host_router_0, 2, 'DOWN'], [host_router_1, 2, 'DOWN']], do_sleep=False)

        # Max attempt is reach, should be HARD now
        for h in all_routers:
            self.assertEqual('DOWN', h.state)
            self.assertEqual('HARD', h.state_type)

        #--------------------------------------------------------------
        # Routers get HARD/DOWN
        # should be problems now!
        #--------------------------------------------------------------
        # Now check in the brok generation too
        host_router_0_brok = host_router_0.get_update_status_brok()
        host_router_0_brok.prepare()
        host_router_1_brok = host_router_1.get_update_status_brok()
        host_router_1_brok.prepare()

        # Should be problems and have sub servers as impacts
        for h in all_routers:
            self.assertEqual(True, h.is_problem)
            # Now routers are problems, they should have take the max
            # business_impact value ofthe impacts, so here 2 because we lower all critcity for our test
            self.assertEqual(2, h.business_impact)
            for s in all_servers:
                self.assertIn(s.uuid, h.impacts)
                self.assertIn(s.uuid, host_router_0_brok.data['impacts'])
                self.assertIn(s.uuid, host_router_1_brok.data['impacts'])

        # Should have host notification, but it's not so simple:
        # our contact say: not under 5, and our hosts are 2. And here
        # the business_impact was still low for our test
        self.assert_no_log_match('HOST NOTIFICATION.*;')
        self.show_and_clear_logs()


        # Now impacts should really be .. impacts :)
        for s in all_servers:
            self.assertEqual(True, s.is_impact)
            self.assertEqual('UNREACHABLE', s.state)
            # And check the services are impacted too
            for svc_id in s.services:
                svc = self.sched.services[svc_id]
                print "Service state", svc.state
                self.assertEqual('UNKNOWN', svc.state)
                self.assertIn(svc.uuid, host_router_0_brok.data['impacts'])
                self.assertIn(svc.uuid, host_router_1_brok.data['impacts'])
                brk_svc = svc.get_update_status_brok()
                brk_svc.prepare()
                self.assertSetEqual(set([host_router_0.uuid, host_router_1.uuid]), set(brk_svc.data['source_problems']))
            for h in all_routers:
                self.assertIn(h.uuid, s.source_problems)
                brk_hst = s.get_update_status_brok()
                brk_hst.prepare()
                self.assertIn(h.uuid, brk_hst.data['source_problems'])


        for h in all_hosts:
            for s_id in h.services:
                s = self.sched.services[s_id]
                s.update_business_impact_value(self.sched.hosts, self.sched.services,
                                               self.sched.timeperiods,
                                               self.sched.businessimpactmodulations)
                self.assertEqual(2, s.business_impact)

        # Now we play with modulation!
        # We put modulation period as None so it will be right all time :)
        critmod.modulation_period = None

        crit_srv = self.sched.services.find_srv_by_name_and_hostname("test_host_1", "test_ok_1")
        self.assertIn(critmod.uuid, crit_srv.business_impact_modulations)

        # Now we set the modulation period as always good, we check that the service
        # really update it's business_impact value
        self.sched.update_business_values()
        # So the service with the modulation should got it's business_impact raised
        self.assertEqual(5, crit_srv.business_impact)
        # And the routers too (problems)
        self.assertEqual(5, host_router_0.business_impact)
        self.assertEqual(5, host_router_1.business_impact)

        #--------------------------------------------------------------
        # One router get UP now
        #--------------------------------------------------------------
        print "- 1 X UP for a router ------------------------------"
        # Ok here the problem/impact propagation is Checked. Now what
        # if one router get back? :)
        self.scheduler_loop(1, [[host_router_0, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assertEqual('UP', host_router_0.state)
        self.assertEqual('HARD', host_router_0.state_type)

        # And should not be a problem any more!
        self.assertEqual(False, host_router_0.is_problem)
        self.assertEqual([], host_router_0.impacts)

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assertEqual(True, s.is_impact)
            self.assertEqual([host_router_1.uuid], s.source_problems)

        #--------------------------------------------------------------
        # The other router get UP :)
        #--------------------------------------------------------------
        print "- 1 X UP for the last router ------------------------------"
        # What is the last router get back? :)
        self.scheduler_loop(1, [[host_router_1, 0, 'UP']], do_sleep=False)

        # should be UP/HARD now
        self.assertEqual('UP', host_router_1.state)
        self.assertEqual('HARD', host_router_1.state_type)

        # And should not be a problem any more!
        self.assertEqual(False, host_router_1.is_problem)
        self.assertEqual([], host_router_1.impacts)

        # And check if it's no more in sources problems of others servers
        for s in all_servers:
            # Still impacted by the other server
            self.assertEqual(False, s.is_impact)
            self.assertEqual('UP', s.state)
            self.assertEqual([], s.source_problems)

        # And our "business_impact" should have failed back to our
        # conf value, so 2
        self.assertEqual(2, host_router_0.business_impact)
        self.assertEqual(2, host_router_1.business_impact)
        # It's done :)



if __name__ == '__main__':
    unittest.main()
