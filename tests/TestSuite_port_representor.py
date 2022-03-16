# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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
Use two representor ports as the control plane to manage the two VFs,
the control plane could change VFs behavior such as change promiscous
mode, stats reset, etc. our statistical data information is
independent on the control plane and data plane.
"""

import re
import time

from framework.dut import Dut
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestPortRepresentor(TestCase):
    def set_up_all(self):
        """
        Prerequisite steps for each test suite.
        """
        self.verify(
            self.nic
            in [
                "fortville_eagle",
                "fortville_spirit",
                "fortville_spirit_single",
                "fortville_25g",
                "carlsville",
                "columbiaville_25g",
                "columbiaville_100g",
            ],
            "NIC Unsupported: " + str(self.nic),
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")

        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()
        self.pmdout_pf = PmdOutput(self.dut)
        self.pmdout_vf0 = PmdOutput(self.dut, self.session_secondary)
        self.pmdout_vf1 = PmdOutput(self.dut, self.session_third)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.tester_mac = self.tester.get_mac(localPort)
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]

        self.unicast_mac = "00:11:22:33:44:55"

        # This is to set up 1pf and 2vfs environment
        # PF is bound to igb_uio, while VF is bound to vfio-pci.
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 2, "igb_uio")
        self.two_vfs_port = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        self.dut.send_expect("modprobe vfio-pci", "#", 3)
        try:
            for port in self.two_vfs_port:
                port.bind_driver(driver="vfio-pci")
        except Exception as e:
            self.destroy_env()
            raise Exception(e)
        self.vfs_pci = self.dut.ports_info[self.dut_ports[0]]["sriov_vfs_pci"]

    def set_up(self):
        """
        Run before each test case.
        """
        self.vf_flag = 1

    def destroy_env(self):
        """
        This is to stop testpmd and destroy 1pf and 2vfs environment.
        """
        if self.vf_flag == 1:
            self.pmdout_vf1.execute_cmd("quit", "#")
            time.sleep(3)
            self.pmdout_vf0.execute_cmd("quit", "#")
            time.sleep(3)
            self.pmdout_pf.execute_cmd("quit", "#")
            time.sleep(3)
        else:
            self.pmdout_pf.execute_cmd("quit", "#")
        self.vf_flag = 0

    def testpmd_pf(self):
        self.pmdout_pf.start_testpmd(
            "Default",
            eal_param="-a %s,representor=0-1" % self.pf_pci,
            param="--port-topology=chained --total-num-mbufs=120000",
        )

    def testpmd_vf0(self):
        self.out_vf0 = self.pmdout_vf0.start_testpmd(
            "Default",
            eal_param="-a %s --file-prefix testpmd-vf0" % self.vfs_pci[0],
            param="--total-num-mbufs=120000",
        )
        self.vf0_mac = self.pmdout_vf0.get_port_mac(0)

    def testpmd_vf1(self):
        self.out_vf1 = self.pmdout_vf1.start_testpmd(
            "Default",
            eal_param="-a %s --file-prefix testpmd-vf1" % self.vfs_pci[1],
            param="--total-num-mbufs=120000",
        )
        self.vf1_mac = self.pmdout_vf1.get_port_mac(0)

    def check_port_stats(self):
        """
        show and check port stats
        """
        out = self.pmdout_pf.execute_cmd("show port stats all", "testpmd>")
        self.logger.info(out)
        result = re.compile("RX-packets:\s+(.*?)\s+?").findall(out, re.S)
        return result

    def clear_port_stats(self):
        """
        clear port stats in control testpmd
        """
        self.pmdout_pf.execute_cmd("clear vf stats 0 0", "testpmd>", 2)
        self.pmdout_pf.execute_cmd("clear vf stats 0 1", "testpmd>", 2)
        self.pmdout_pf.execute_cmd("clear port stats all", "testpmd>", 2)

    def test_port_representor_vf_stats_show_and_clear(self):
        """
        use control testpmd to get and clear dataplane testpmd ports Stats
        """
        self.testpmd_pf()
        self.pmdout_pf.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_pf.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf0()
        self.pmdout_vf0.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_vf0.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf1()
        self.pmdout_vf1.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_vf1.execute_cmd("start", "testpmd>", 2)
        # send 30 packets
        pkt1 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.pf_mac)
        pkt2 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf0_mac)
        pkt3 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf1_mac)
        pkts = [pkt1, pkt2, pkt3]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf, count=10)
        # check port stats in control testpmd
        result_before = self.check_port_stats()
        self.verify(
            int(result_before[1]) == 10 and int(result_before[2]) == 10,
            "VF Stats show error",
        )
        self.clear_port_stats()
        result_after = self.check_port_stats()
        self.verify(
            int(result_after[1]) == 0 and int(result_after[2]) == 0,
            "VF Stats clear error",
        )

    def test_port_representor_vf_promiscous(self):
        """
        use control testpmd to enable/disable dataplane testpmd ports promiscous mode
        """
        self.testpmd_pf()
        self.pmdout_pf.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_pf.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf0()
        self.pmdout_vf0.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf1()
        self.pmdout_vf1.execute_cmd("start", "testpmd>", 2)

        # set vf promisc enable and send 40 packets
        self.pmdout_pf.execute_cmd("set promisc 1 on", "testpmd>")
        pkt1 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.pf_mac)
        pkt2 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf0_mac)
        pkt3 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf1_mac)
        pkt4 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.unicast_mac)
        pkts = [pkt1, pkt2, pkt3, pkt4]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf, count=10)
        # check port stats in control testpmd
        result_enable = self.check_port_stats()
        self.verify(
            int(result_enable[1]) == 20 and int(result_enable[2]) == 20,
            "VFs receive packets error",
        )
        self.clear_port_stats()
        # set vf promisc disable and send 40 packets
        self.pmdout_pf.execute_cmd("set promisc 1 off", "testpmd>")
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf, count=10)
        # check port stats in control testpmd
        result_disable = self.check_port_stats()
        self.verify(
            int(result_disable[1]) == 10 and int(result_disable[2]) == 20,
            "VFs receive packets error",
        )

    def test_port_representor_vf_mac_addr(self):
        """
        use control testpmd to set vf mac address
        """
        self.testpmd_pf()
        self.pmdout_pf.execute_cmd("mac_addr set 1 aa:11:22:33:44:55", "testpmd>")
        self.pmdout_pf.execute_cmd("mac_addr set 2 aa:22:33:44:55:66", "testpmd>")
        self.pmdout_pf.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_pf.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf0()
        self.pmdout_vf0.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_vf0.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf1()
        self.pmdout_vf1.execute_cmd("set promisc 0 off", "testpmd>")
        self.pmdout_vf1.execute_cmd("start", "testpmd>", 2)
        # send 40 packets
        pkt1 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.pf_mac)
        pkt2 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf0_mac)
        pkt3 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.vf1_mac)
        pkt4 = 'Ether(src="%s",dst="%s")/IP()' % (self.tester_mac, self.unicast_mac)
        pkts = [pkt1, pkt2, pkt3, pkt4]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf, count=10)
        # check port stats in control testpmd
        result = self.check_port_stats()
        self.verify(
            int(result[1]) == 10 and int(result[2]) == 10, "VFs receive packets error"
        )

    def test_port_representor_vlan_filter(self):
        """
        use control testpmd to set vlan
        """
        self.testpmd_pf()
        self.pmdout_pf.execute_cmd("set promisc 1 off", "testpmd>")
        self.pmdout_pf.execute_cmd("vlan set filter on 1", "testpmd>")
        self.pmdout_pf.execute_cmd("rx_vlan add 3 1", "testpmd>")
        self.pmdout_pf.execute_cmd("set promisc 2 off", "testpmd>")
        self.pmdout_pf.execute_cmd("vlan set filter on 2", "testpmd>")
        self.pmdout_pf.execute_cmd("rx_vlan add 4 2", "testpmd>")
        self.pmdout_pf.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf0()
        self.pmdout_vf0.execute_cmd("start", "testpmd>", 2)
        self.testpmd_vf1()
        self.pmdout_vf1.execute_cmd("start", "testpmd>", 2)
        # send 20 packets
        pkt1 = 'Ether(src="%s",dst="%s")/Dot1Q(vlan=3)/IP()' % (
            self.tester_mac,
            self.vf0_mac,
        )
        pkt2 = 'Ether(src="%s",dst="%s")/Dot1Q(vlan=4)/IP()' % (
            self.tester_mac,
            self.vf1_mac,
        )
        pkts = [pkt1, pkt2]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf, count=10)
        # check port stats in control testpmd
        result = self.check_port_stats()
        self.verify(
            int(result[1]) == 10 and int(result[2]) == 10, "VFs receive packets error"
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_env()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)
