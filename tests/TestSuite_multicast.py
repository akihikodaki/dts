# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

multicast test script.
"""

import time
from test_case import TestCase
import utils

routeTbl = [
    ["224.0.0.101", "P1"], ["224.0.0.102", "P2"],
    ["224.0.0.103", "P1,P2"], ["224.0.0.104", "P3"],
    ["224.0.0.105", "P1,P3"], ["224.0.0.106", "P2,P3"],
    ["224.0.0.107", "P1,P2,P3"], ["224.0.0.108", "P4"],
    ["224.0.0.109", "P1,P4"], ["224.0.0.110", "P2,P4"],
    ["224.0.0.111", "P1,P2,P4"], ["224.0.0.112", "P3,P4"],
    ["224.0.0.113", "P1,P3,P4"], ["224.0.0.114", "P2,P3,P4"],
    ["224.0.0.115", "P1,P2,P3,P4"]
]

trafficFlow = {
    "F1": ["TG0", "TG0", "10.100.0.1", "224.0.0.101"],
    "F2": ["TG0", "TG1", "10.100.0.2", "224.0.0.104"],
    "F3": ["TG0", "TG0,TG1", "10.100.0.3", "224.0.0.105"],
    "F4": ["TG1", "TG1", "11.100.0.1", "224.0.0.104"],
    "F5": ["TG1", "TG0", "11.100.0.2", "224.0.0.101"],
    "F6": ["TG1", "TG0,TG1", "11.100.0.3", "224.0.0.105"]
}

measureTarget = [
    ["1S/1C/1T", "F1,F4", "ipv4_multicast -c %s -n 3 -- -p %s -q 2"],
    ["1S/1C/2T", "F1,F4", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"],
    ["1S/2C/1T", "F1,F4", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"],
    ["1S/1C/1T", "F2,F5", "ipv4_multicast -c %s -n 3 -- -p %s -q 2"],
    ["1S/1C/2T", "F2,F5", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"],
    ["1S/2C/1T", "F2,F5", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"],
    ["1S/1C/1T", "F3,F6", "ipv4_multicast -c %s -n 3 -- -p %s -q 2"],
    ["1S/1C/2T", "F3,F6", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"],
    ["1S/2C/1T", "F3,F6", "ipv4_multicast -c %s -n 3 -- -p %s -q 1"]
]


class TestMulticast(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Multicast Prerequisites
        """
        global dutPorts
        # Based on h/w type, choose how many ports to use
        dutPorts = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(dutPorts) >= 4, "Insufficient ports for testing")

        # Verify that enough threads are available
        cores = self.dut.get_core_list("1S/2C/2T")
        self.verify(cores is not None, "Insufficient cores for speed testing")

        global P1, P3, TG0, TG1, TGs
        # prepare port mapping TG0<=>P1, TG1<=>P3
        P1 = dutPorts[0]
        P2 = dutPorts[1]
        P3 = dutPorts[2]
        P4 = dutPorts[3]
        TGs = [P1, P3]
        TG0 = self.tester.get_local_port(TGs[0])
        TG1 = self.tester.get_local_port(TGs[1])

        # Prepare multicast route table, replace P(x) port pattern
        repStr = "static struct mcast_group_params mcast_group_table[] = {\\\n"
        for [ip, ports] in routeTbl:
            mask = 0
            for _ in ports.split(','):
                mask = mask | (1 << eval(_))
            entry = '{' + 'RTE_IPV4(' + ip.replace('.', ',') + '),' + str(mask) + '}'
            repStr = repStr + ' ' * 4 + entry + ",\\\n"
        repStr = repStr + "};"

        self.dut.send_expect(r"sed -i '/mcast_group_table\[\].*{/,/^\}\;/c\\%s' examples/ipv4_multicast/main.c" % repStr, "# ")

        # make application
        out = self.dut.build_dpdk_apps('examples/ipv4_multicast')
        self.app_ipv4_multicast_path = self.dut.apps_name['ipv4_multicast']
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_multicast_forwarding(self):
        """
        IP4 Multicast Forwarding F1~F6
        """
        eal_para = self.dut.create_eal_parameters(cores="1S/2C/1T")
        payload = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.dut.send_expect("%s -c %s -n 4 -- -p %s -q 2" % (self.app_ipv4_multicast_path,
                                                              eal_para, '0x5'), "IPv4_MULTICAST:", 60)

        for flow in list(trafficFlow.keys()):
            for tx_port in trafficFlow[flow][0].split(","):
                for rx_port in trafficFlow[flow][1].split(","):
                    sniff_src = "not 00:00:00:00:00:00"

                    inst = self.tester.tcpdump_sniff_packets(intf=self.tester.get_interface(eval(rx_port)),
                        count=1, filters=[{"layer": "ether", "config": {"src": sniff_src}}] )
                    dmac = self.dut.get_mac_address(TGs[int(trafficFlow[flow][0][2])])

                    self.tester.scapy_append('sendp([Ether(src="00:00:00:00:00:00", dst="%s")/IP(dst="%s",src="%s")\
                            /Raw(load="%s")], iface="%s")' % (
                            dmac, trafficFlow[flow][3], trafficFlow[flow][2], payload, self.tester.get_interface(eval(tx_port))))
                    self.tester.scapy_execute()
                    time.sleep(5)  # Wait for the sniffer to finish.

                    pkts = self.tester.load_tcpdump_sniff_packets(inst)
                    for i in range(len(pkts)):
                        result = str(pkts[i].show)

                        print(result)
                        self.verify("Ether" in result, "No packet received")
                        self.verify("src=" + trafficFlow[flow][2] + " dst=" + trafficFlow[flow][3] in result,
                            "Wrong IP address")
                        self.verify("load='%s'" % payload in result, "Wrong payload")
                        splitIP = trafficFlow[flow][3].rsplit(".")
                        expectedMac = "01:00:5e:%s:%s:%s" % (str(int(splitIP[1], 8) & 0b01111111).zfill(2),
                            str(int(splitIP[2], 8)).zfill(2), str(int(splitIP[3], 8)).zfill(2))
                        self.verify("dst=%s" % expectedMac in result, "Wrong MAC address")

        self.dut.send_expect("^C", "#")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^C", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
