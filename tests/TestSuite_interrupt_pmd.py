# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


"""
DPDK Test suite.
Test interrupt pmd.
"""

import string
import time

import framework.utils as utils
from framework.test_case import TestCase


class TestInterruptPmd(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.eal_para = self.dut.create_eal_parameters(cores='1S/4C/1T')
        self.coremask = utils.create_mask(cores)

        self.path = self.dut.apps_name["l3fwd-power"]

        self.trafficFlow = {
            "Flow1": [[0, 0, 1], [1, 0, 2]],
            "Flow2": [[0, 0, 0], [0, 1, 1], [0, 2, 2], [0, 3, 3], [0, 4, 4]],
            "Flow3": [[0, 0, 0], [0, 1, 1], [0, 2, 2], [0, 3, 3], [0, 4, 4], [0, 5, 5], [0, 6, 6], [0, 7, 7],
                      [1, 0, 8], [1, 1, 9], [1, 2, 10], [1, 3, 11], [1, 4, 12], [1, 5, 13], [1, 6, 14]],
        }
        # build sample app
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        self.default_driver = self.get_nic_driver()
        test_driver = "vfio-pci"
        if test_driver != self.default_driver:
            self.dut.send_expect("modprobe %s" % test_driver, "#")
        self.set_nic_driver(test_driver)

    def get_nic_driver(self, port_id=0):
        port = self.dut.ports_info[port_id]["port"]
        return port.get_nic_driver()

    def set_nic_driver(self, set_driver='vfio-pci'):
        for i in self.dut_ports:
            port = self.dut.ports_info[i]["port"]
            driver = port.get_nic_driver()
            if driver != set_driver:
                port.bind_driver(driver=set_driver)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_different_queue(self):
        cmd = "%s %s -- -p 0x3 -P --config='(0,0,1),(1,0,2)' "% (self.path, self.eal_para)
        self.dut.send_expect(cmd, "L3FWD_POWER", 60)
        portQueueLcore = self.trafficFlow["Flow1"]
        self.verifier_result(2, 2, portQueueLcore)

        self.dut.kill_all()
        cores = list(range(6))
        eal_para = self.dut.create_eal_parameters(cores=cores)
        cmd = "%s %s -- -p 0x3 -P --config='(0,0,0),(0,1,1),(0,2,2),(0,3,3),(0,4,4)' "% (self.path, eal_para)
        self.dut.send_expect(cmd, "L3FWD_POWER", 120)
        portQueueLcore = self.trafficFlow["Flow2"]
        self.verifier_result(20, 1, portQueueLcore)

        self.dut.kill_all()
        cores = list(range(24))
        eal_para = self.dut.create_eal_parameters(cores=cores)
        cmd = "%s %s -- -p 0x3 -P --config='(0,0,0),(0,1,1),(0,2,2),(0,3,3),\
        (0,4,4),(0,5,5),(0,6,6),(0,7,7),(1,0,8),(1,1,9),(1,2,10),(1,3,11),\
        (1,4,12),(1,5,13),(1,6,14)' "% (self.path, eal_para)

        self.dut.send_expect(cmd, "L3FWD_POWER", 60)
        portQueueLcore = self.trafficFlow["Flow3"]
        self.verifier_result(40, 2, portQueueLcore)

    def verifier_result(self, num, portnum, portQueueLcore):
        self.scapy_send_packet(num, portnum)
        result = self.dut.get_session_output(timeout=5)
        for i in range(len(portQueueLcore)):
            lcorePort = portQueueLcore[i]
            self.verify("FWD_POWER: lcore %d is waked up from rx interrupt on port %d queue %d" %(lcorePort[2],
                lcorePort[0], lcorePort[1]) in result, "Wrong: lcore %d is waked up failed" % lcorePort[2])
            self.verify("L3FWD_POWER: lcore %d sleeps until interrupt triggers" %(
                lcorePort[2]) in result, "Wrong: lcore %d not sleeps until interrupt triggers" % lcorePort[2])

    def scapy_send_packet(self, num, portnum):
        """
        Send a packet to port
        """
        for i in range(len(self.dut_ports[:portnum])):
            for j in range(num):
                txport = self.tester.get_local_port(self.dut_ports[i])
                mac = self.dut.get_mac_address(self.dut_ports[i])
                txItf = self.tester.get_interface(txport)
                self.tester.scapy_append(
                    'sendp([Ether()/IP(dst="198.0.0.%d")/UDP()/Raw(\'X\'*18)], iface="%s")' % (j, txItf))
        self.tester.scapy_execute()

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.set_nic_driver(self.default_driver)
