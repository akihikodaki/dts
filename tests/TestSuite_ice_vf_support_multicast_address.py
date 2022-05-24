# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

vf0_mac = "00:11:22:33:44:55"
vf1_mac = "00:11:22:33:44:66"
mul_mac_0 = "33:33:00:00:00:01"
mul_mac_1 = "33:33:00:40:10:01"
vf0_wrong_mac = "00:11:22:33:44:56"


class TestICEVfSupportMulticastAdress(TestCase):
    def set_up_all(self):
        """
        Prerequisite steps for each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        self.used_dut_port = self.dut_ports[0]
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.vf_flag = False
        self.create_iavf()
        self.pmd_output = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)

    def set_up(self):
        """
        Run before each test case.
        """
        if self.running_case == "test_maxnum_multicast_address_with_vfs_trust_off":
            # set two VFs trust off
            self.dut.send_expect(
                "ip link set dev %s vf 0 trust off" % self.pf_interface, "# "
            )
            self.dut.send_expect(
                "ip link set dev %s vf 1 trust off" % self.pf_interface, "# "
            )
        else:
            self.dut.send_expect(
                "ip link set dev %s vf 0 trust on" % self.pf_interface, "# "
            )
            self.dut.send_expect(
                "ip link set dev %s vf 1 trust on" % self.pf_interface, "# "
            )
        self.launch_testpmd()

    def create_iavf(self):
        # Generate 2 VFs on PF
        if self.vf_flag is False:
            self.dut.bind_interfaces_linux("ice")
            # get priv-flags default stats
            self.flag = "vf-vlan-pruning"
            self.default_stats = self.dut.get_priv_flags_state(
                self.pf_interface, self.flag
            )
            if self.default_stats:
                self.dut.send_expect(
                    "ethtool --set-priv-flags %s %s on"
                    % (self.pf_interface, self.flag),
                    "# ",
                )
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
            self.vf_flag = True

            try:
                for port in self.sriov_vfs_port:
                    port.bind_driver(self.drivername)

                self.dut.send_expect("ifconfig %s up" % self.pf_interface, "# ")
                self.dut.send_expect(
                    "ethtool --set-priv-flags %s vf-true-promisc-support on"
                    % self.pf_interface,
                    "# ",
                )
                self.dut.send_expect(
                    "ip link set %s vf 0 mac %s" % (self.pf_interface, vf0_mac), "# "
                )
                self.dut.send_expect(
                    "ip link set %s vf 1 mac %s" % (self.pf_interface, vf1_mac), "# "
                )
            except Exception as e:
                self.destroy_iavf()
                raise Exception(e)

    def destroy_iavf(self):
        if self.vf_flag is True:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.vf_flag = False

    def launch_testpmd(self):
        param = "--portmask=0x3 --rxq=16 --txq=16"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            param=param,
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci],
        )
        self.pmd_output.execute_cmd("set fwd rxonly")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("set allmulti all off")

    def check_ports_multicast_address_number(self, num_0, num_1):
        out_0 = self.pmd_output.execute_cmd("show port 0 mcast_macs")
        number_0 = re.compile(
            "Number of Multicast MAC address added:\s+(.*?)\s+?"
        ).findall(out_0)
        if not len(number_0):
            number_0 = 0
            self.verify(
                number_0 == num_0, "configure multicast address on port 0 failed"
            )
        else:
            self.verify(
                int(number_0[0]) == num_0,
                "configure multicast address on port 0 failed",
            )
        out_1 = self.pmd_output.execute_cmd("show port 1 mcast_macs")
        number_1 = re.compile(
            "Number of Multicast MAC address added:\s+(.*?)\s+?"
        ).findall(out_1)
        if not len(number_1):
            number_1 = 0
            self.verify(
                number_1 == num_1, "configure multicast address on port 1 failed"
            )
        else:
            self.verify(
                int(number_1[0]) == num_1,
                "configure multicast address on port 1 failed",
            )

    def check_pkts_received(self):
        out = self.pmd_output.get_output(timeout=1)
        result = re.compile(r"port\s+(.*?)/queue.*?dst=(.*?)\s+").findall(
            "".join(out.split("\n"))
        )
        return result

    def config_mac(self, num_start, num_end):
        list = []
        Mac_list = []
        for i in range(num_start, num_end):
            list.append(hex(i))
        for j in list:
            if j.startswith("0x"):
                Mac_list.append("33:33:00:00:00:{}".format((j[2:].upper()).zfill(2)))
        return Mac_list

    def config_pkts_and_send(self, num_start, num_end):
        pkts = []
        mac_list = self.config_mac(num_start, num_end)
        if num_end == 17:
            for i in range(0, num_end - 1):
                pkt = 'Ether(dst="{}")/IP(src="224.0.0.{}")/UDP(sport=22,dport=23)/("X"*480)'.format(
                    mac_list[i], i + 1
                )
                pkts.append(pkt)
        else:
            for i in range(0, num_end):
                pkt = 'Ether(dst="{}")/IP(src="224.0.0.{}")/UDP(sport=22,dport=23)/("X"*480)'.format(
                    mac_list[i], i
                )
                pkts.append(pkt)
        pkt_last = 'Ether(dst="33:33:00:00:00:{}")/IP(src="224.0.0.{}")/UDP(sport=22,dport=23)/("X"*480)'.format(
            hex(num_end)[2:], num_end
        )
        pkts.append(pkt_last)
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)

    def test_one_multicast_address(self):
        # send 4 packets
        pkt1 = (
            'Ether(dst="%s")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt2 = (
            'Ether(dst="%s")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkt3 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf0_mac
        )
        pkt4 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf1_mac
        )
        pkts = [pkt1, pkt2, pkt3, pkt4]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_1 = self.check_pkts_received()
        self.verify(len(out_1) == 2, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in out_1, "pkt3 can't be received by port 0")
        self.verify(("1", vf1_mac) in out_1, "pkt4 can't be received by port 1")

        # configure multicast address
        self.pmd_output.execute_cmd("mcast_addr add 0 %s" % mul_mac_0)
        self.check_ports_multicast_address_number(1, 0)
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_2 = self.check_pkts_received()
        self.verify(len(out_2) == 3, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in out_2, "pkt3 can't be received by port 0")
        self.verify(("1", vf1_mac) in out_2, "pkt4 can't be received by port 1")
        self.verify(("0", mul_mac_0) in out_2, "pkt1 can't be received by port 0")

        # remove the multicast address configuration
        self.pmd_output.execute_cmd("mcast_addr remove 0 %s" % mul_mac_0)
        self.check_ports_multicast_address_number(0, 0)
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_3 = self.check_pkts_received()
        self.verify(len(out_3) == 2, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in out_3, "pkt3 can't be received by port 0")
        self.verify(("1", vf1_mac) in out_3, "pkt4 can't be received by port 1")

    def test_two_multicast_address(self):
        # configure multicast address
        self.pmd_output.execute_cmd("mcast_addr add 0 %s" % mul_mac_0)
        self.pmd_output.execute_cmd("mcast_addr add 0 %s" % mul_mac_1)
        self.check_ports_multicast_address_number(2, 0)

        # send 4 packets
        pkt1 = (
            'Ether(dst="%s")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt2 = (
            'Ether(dst="%s")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkt3 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf0_mac
        )
        pkt4 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf1_mac
        )
        pkts = [pkt1, pkt2, pkt3, pkt4]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_1 = self.check_pkts_received()
        self.verify(len(out_1) == 4, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in out_1, "pkt3 can't be received by port 0")
        self.verify(("1", vf1_mac) in out_1, "pkt4 can't be received by port 1")
        self.verify(
            ("0", mul_mac_0) in out_1 and ("0", mul_mac_1) in out_1,
            "pkt1-2 can't be received by port 0",
        )

        # remove the multicast address configuration
        self.pmd_output.execute_cmd("mcast_addr remove 0 %s" % mul_mac_0)
        self.check_ports_multicast_address_number(1, 0)
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_2 = self.check_pkts_received()
        self.verify(len(out_2) == 3, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in out_2, "pkt3 can't be received by port 0")
        self.verify(("1", vf1_mac) in out_2, "pkt4 can't be received by port 1")
        self.verify(("0", mul_mac_1) in out_2, "pkt2 can't be received by port 0")

    def test_multicast_address_on_two_vf_ports(self):
        # configure multicast address on port 0 and port 1
        self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:01")
        self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:01")
        self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:02")
        self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:03")
        self.check_ports_multicast_address_number(2, 2)

        # send 3 packets
        pkt1 = 'Ether(dst="33:33:00:00:00:01")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
        pkt2 = 'Ether(dst="33:33:00:00:00:02")/IP(src="224.0.0.2")/UDP(sport=22,dport=23)/("X"*480)'
        pkt3 = 'Ether(dst="33:33:00:00:00:03")/IP(src="224.0.0.3")/UDP(sport=22,dport=23)/("X"*480)'
        pkts = [pkt1, pkt2, pkt3]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_1 = self.check_pkts_received()
        self.verify(len(out_1) == 4, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:01") in out_1, "pkt1 can't be received by port 0"
        )
        self.verify(
            ("1", "33:33:00:00:00:01") in out_1, "pkt1 can't be received by port 1"
        )
        self.verify(
            ("0", "33:33:00:00:00:02") in out_1, "pkt2 can't be received by port 0"
        )
        self.verify(
            ("1", "33:33:00:00:00:03") in out_1, "pkt3 can't be received by port 1"
        )

        # remove some multicast address configurations
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:01")
        self.pmd_output.execute_cmd("mcast_addr remove 1 33:33:00:00:00:03")
        self.check_ports_multicast_address_number(1, 1)
        # send 3 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_2 = self.check_pkts_received()
        self.verify(len(out_2) == 2, "Wrong number of pkts received")
        self.verify(
            ("1", "33:33:00:00:00:01") in out_2, "pkt1 can't be received by port 1"
        )
        self.verify(
            ("0", "33:33:00:00:00:02") in out_2, "pkt2 can't be received by port 0"
        )

    def test_maxnum_multicast_address_with_vfs_trust_off(self):
        # configure 16 multicast address on port 0 and port 1
        mac_addr_list = self.config_mac(1, 17)
        for i in mac_addr_list:
            self.pmd_output.execute_cmd("mcast_addr add 0 %s" % i)
            self.pmd_output.execute_cmd("mcast_addr add 1 %s" % i)
        self.check_ports_multicast_address_number(16, 16)

        # configure one more multicast address on port 0 and port 1
        out_0 = self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:11")
        self.verify(
            "rte_eth_dev_set_mc_addr_list(port=0, nb=17) failed" in out_0,
            "Configure one more multicast address on port 0 successfullly",
        )
        out_1 = self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:11")
        self.verify(
            "rte_eth_dev_set_mc_addr_list(port=1, nb=17) failed" in out_1,
            "Configure one more multicast address on port 1 successfullly",
        )
        self.check_ports_multicast_address_number(16, 16)
        # send packets
        self.config_pkts_and_send(1, 17)
        output_1 = self.check_pkts_received()
        self.verify(len(output_1) == 32, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:11") not in output_1,
            "pkt last can be received by port 0",
        )
        self.verify(
            ("1", "33:33:00:00:00:11") not in output_1,
            "pkt last can be received by port 1",
        )
        for i in range(len(mac_addr_list)):
            self.verify(
                ("0", mac_addr_list[i]) in output_1,
                "pkt%s can't be received by port 0" % (i + 1),
            )
            self.verify(
                ("1", mac_addr_list[i]) in output_1,
                "pkt%s can't be received by port 1" % (i + 1),
            )

        # remove one multicast address on port 0
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:0B")
        self.pmd_output.execute_cmd("mcast_addr remove 1 33:33:00:00:00:01")
        self.check_ports_multicast_address_number(15, 15)
        self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:11")
        self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:11")
        self.check_ports_multicast_address_number(16, 16)
        # send packts
        self.config_pkts_and_send(1, 17)
        output_2 = self.check_pkts_received()
        self.verify(len(output_2) == 32, "Wrong number of pkts received")
        for i in range(len(mac_addr_list)):
            if mac_addr_list[i] == "33:33:00:00:00:0B":
                self.verify(
                    ("0", "33:33:00:00:00:0B") not in output_2,
                    "pkt11 can be received by port 0",
                )
                self.verify(
                    ("1", "33:33:00:00:00:0B") in output_2,
                    "pkt11 can't be received by port 1",
                )
            elif mac_addr_list[i] == "33:33:00:00:00:01":
                self.verify(
                    ("1", "33:33:00:00:00:01") not in output_2,
                    "pkt1 can be received by port 1",
                )
                self.verify(
                    ("0", "33:33:00:00:00:01") in output_2,
                    "pkt1 can't be received by port 0",
                )
            else:
                self.verify(
                    ("0", mac_addr_list[i]) in output_2,
                    "pkt%s can't be received by port 0" % (i + 1),
                )
                self.verify(
                    ("1", mac_addr_list[i]) in output_2,
                    "pkt%s can't be received by port 1" % (i + 1),
                )

        # remove all the multicast address configuration on two ports
        for i in mac_addr_list:
            self.pmd_output.execute_cmd("mcast_addr remove 0 %s" % i)
            self.pmd_output.execute_cmd("mcast_addr remove 1 %s" % i)
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:11")
        self.pmd_output.execute_cmd("mcast_addr remove 1 33:33:00:00:00:11")
        self.check_ports_multicast_address_number(0, 0)
        # send packts
        self.config_pkts_and_send(1, 17)
        output_3 = self.check_pkts_received()
        self.verify(len(output_3) == 0, "Wrong number of pkts received")

    def test_maxnum_multicast_address_with_vfs_trust_on(self):
        # configure 64 multicast address on port 0 and port 1
        mac_addr_list = self.config_mac(0, 64)
        for i in mac_addr_list:
            self.pmd_output.execute_cmd("mcast_addr add 0 %s" % i)
            self.pmd_output.execute_cmd("mcast_addr add 1 %s" % i)
        self.check_ports_multicast_address_number(64, 64)

        # configure one more multicast address on each port
        out_0 = self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:40")
        self.verify(
            "rte_eth_dev_set_mc_addr_list(port=0, nb=65) failed" in out_0,
            "Configure one more multicast address on port 0 successfullly",
        )
        out_1 = self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:40")
        self.verify(
            "rte_eth_dev_set_mc_addr_list(port=1, nb=65) failed" in out_1,
            "Configure one more multicast address on port 1 successfullly",
        )
        self.check_ports_multicast_address_number(64, 64)

        # send packets
        self.config_pkts_and_send(0, 64)
        output_1 = self.check_pkts_received()
        self.verify(len(output_1) == 128, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:40") not in output_1,
            "pkt last can be received by port 0",
        )
        self.verify(
            ("1", "33:33:00:00:00:40") not in output_1,
            "pkt lsat can be received by port 1",
        )
        for i in range(len(mac_addr_list)):
            self.verify(
                ("0", mac_addr_list[i]) in output_1,
                "pkt%s can't be received by port 0" % i,
            )
            self.verify(
                ("1", mac_addr_list[i]) in output_1,
                "pkt%s can't be received by port 1" % i,
            )

        # remove one multicast address on port 0
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:0B")
        self.pmd_output.execute_cmd("mcast_addr remove 1 33:33:00:00:00:01")
        self.check_ports_multicast_address_number(63, 63)
        self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:40")
        self.pmd_output.execute_cmd("mcast_addr add 1 33:33:00:00:00:40")
        self.check_ports_multicast_address_number(64, 64)

        # send packts
        self.config_pkts_and_send(0, 64)
        output_2 = self.check_pkts_received()
        self.verify(len(output_2) == 128, "Wrong number of pkts received")
        for i in range(len(mac_addr_list)):
            if mac_addr_list[i] == "33:33:00:00:00:0B":
                self.verify(
                    ("0", "33:33:00:00:00:0B") not in output_2,
                    "pkt11 can be received by port 0",
                )
                self.verify(
                    ("1", "33:33:00:00:00:0B") in output_2,
                    "pkt11 can't be received by port 1",
                )
            elif mac_addr_list[i] == "33:33:00:00:00:01":
                self.verify(
                    ("1", "33:33:00:00:00:01") not in output_2,
                    "pkt1 can be received by port 1",
                )
                self.verify(
                    ("0", "33:33:00:00:00:01") in output_2,
                    "pkt1 can't be received by port 0",
                )
            else:
                self.verify(
                    ("0", mac_addr_list[i]) in output_2,
                    "pkt%s can't be received by port 0" % i,
                )
                self.verify(
                    ("1", mac_addr_list[i]) in output_2,
                    "pkt%s can't be received by port 1" % i,
                )

        # remove all the multicast address configuration on port 0
        for i in mac_addr_list:
            self.pmd_output.execute_cmd("mcast_addr remove 0 %s" % i)
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:40")
        self.check_ports_multicast_address_number(0, 64)
        # send packts
        self.config_pkts_and_send(0, 64)
        output_3 = self.check_pkts_received()
        self.verify(len(output_3) == 64, "Wrong number of pkts received")
        for i in range(len(mac_addr_list)):
            self.verify(
                ("0", mac_addr_list[i]) not in output_3,
                "pkt%s can be received by port 0" % i,
            )

        # remove all the multicast address configuration on port 1
        for i in mac_addr_list:
            self.pmd_output.execute_cmd("mcast_addr remove 1 %s" % i)
        self.pmd_output.execute_cmd("mcast_addr remove 1 33:33:00:00:00:40")
        self.check_ports_multicast_address_number(0, 0)
        # send packts
        self.config_pkts_and_send(0, 64)
        output_4 = self.check_pkts_received()
        self.verify(len(output_4) == 0, "Wrong number of pkts received")

    def test_set_allmulti_on(self):
        # set allmulti on and promisc off
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("set allmulti all on")

        # send 5 packets
        pkt1 = (
            'Ether(dst="%s")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt2 = (
            'Ether(dst="%s")/Dot1Q(vlan=1)/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt3 = (
            'Ether(dst="%s")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkt4 = (
            'Ether(dst="%s")/Dot1Q(vlan=2)/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkt5 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf0_mac
        )
        pkt6 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf1_mac
        )
        pkt7 = (
            'Ether(dst="%s")/IP(src="192.168.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % vf0_wrong_mac
        )
        pkts = [pkt1, pkt2, pkt3, pkt4, pkt5, pkt6, pkt7]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_1 = self.check_pkts_received()
        self.verify(len(output_1) == 10, "Wrong number of pkts received")
        self.verify(("0", vf0_mac) in output_1, "pkt5 can't be received by port 0")
        self.verify(("1", vf1_mac) in output_1, "pkt6 can't be received by port 1")
        self.verify(
            ("0", mul_mac_0) in output_1 and ("0", mul_mac_1) in output_1,
            "pkt1-4 can't be received by port 0",
        )
        self.verify(
            ("1", mul_mac_0) in output_1 and ("1", mul_mac_1) in output_1,
            "pkt1-4 can't be received by port 1",
        )

        # set allmulti off and promisc on
        self.pmd_output.execute_cmd("set promisc all on")
        self.pmd_output.execute_cmd("set allmulti all off")
        # send 5 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_2 = self.check_pkts_received()
        self.verify(len(output_2) == 6, "Wrong number of pkts received")
        self.verify(
            ("0", vf0_mac) in output_2
            and ("0", vf1_mac) in output_2
            and ("0", vf0_wrong_mac) in output_2,
            "pkt5-7 can't be received by port 0",
        )
        self.verify(
            ("1", vf0_mac) in output_2
            and ("1", vf1_mac) in output_2
            and ("1", vf0_wrong_mac) in output_2,
            "pkt5-7 can't be received by port 1",
        )

    def test_negative_case(self):
        # send one packet
        p = Packet()
        p.append_pkt(
            'Ether(dst="33:33:00:00:00:40")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
        )
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_1 = self.check_pkts_received()
        self.verify(len(output_1) == 0, "Wrong number of pkts received")

        # add a multicast address
        self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:40")
        # send one packet
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_2 = self.check_pkts_received()
        self.verify(len(output_2) == 1, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:40") in output_2, "pkt can't be received by port 0"
        )

        # add a same multicast address
        result = self.pmd_output.execute_cmd("mcast_addr add 0 33:33:00:00:00:40")
        self.verify(
            "multicast address already filtered by port" in result,
            "add a same multicast address successfully",
        )
        # send one packet
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_3 = self.check_pkts_received()
        self.verify(len(output_3) == 1, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:40") in output_3, "pkt can't be received by port 0"
        )

        # remove nonexistent multicast address
        result = self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:41")
        self.verify(
            "multicast address not filtered by port 0" in result,
            "remove nonexistent multicast address successfully",
        )
        # send one packet
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_4 = self.check_pkts_received()
        self.verify(len(output_4) == 1, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:40") in output_4, "pkt can't be received by port 0"
        )

        # add wrong multicast address
        result = self.pmd_output.execute_cmd("mcast_addr add 0 32:33:00:00:00:41")
        self.verify(
            "Invalid multicast addr 32:33:00:00:00:41" in result,
            "add wrong multicast address successfully",
        )
        # send one packet
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_5 = self.check_pkts_received()
        self.verify(len(output_5) == 1, "Wrong number of pkts received")
        self.verify(
            ("0", "33:33:00:00:00:40") in output_5, "pkt can't be received by port 0"
        )

        # remove the multicast address
        self.pmd_output.execute_cmd("mcast_addr remove 0 33:33:00:00:00:40")
        # send one packet
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        output_6 = self.check_pkts_received()
        self.verify(len(output_6) == 0, "Wrong number of pkts received")

    def test_set_vlan_filter_on(self):
        # send 4 packets
        pkt1 = (
            'Ether(dst="%s")/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt2 = (
            'Ether(dst="%s")/Dot1Q(vlan=1)/IP(src="224.0.0.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_0
        )
        pkt3 = (
            'Ether(dst="%s")/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkt4 = (
            'Ether(dst="%s")/Dot1Q(vlan=1)/IP(src="224.192.16.1")/UDP(sport=22,dport=23)/("X"*480)'
            % mul_mac_1
        )
        pkts = [pkt1, pkt2, pkt3, pkt4]
        p = Packet()
        for i in pkts:
            p.append_pkt(i)
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_1 = self.check_pkts_received()
        self.verify(len(out_1) == 0, "pkt1-4 can be received by any port")

        # configure multicast address
        self.pmd_output.execute_cmd("mcast_addr add 0 %s" % mul_mac_0)
        self.check_ports_multicast_address_number(1, 0)
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_2 = self.check_pkts_received()
        self.verify(len(out_2) == 1, "Wrong number of pkts received")
        self.verify(("0", mul_mac_0) in out_2, "pkt1 can't be received by port 0")

        # set vlan filter on
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_3 = self.check_pkts_received()
        self.verify(len(out_3) == 2, "Wrong number of pkts received")
        self.verify(("0", mul_mac_0) in out_3, "pkt1-2 can't be received by port 0")
        self.verify(
            ("0", mul_mac_1) not in out_3, "other pkt can be received by port 0"
        )

        # remove the vlan filter
        self.pmd_output.execute_cmd("rx_vlan rm 1 0")
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_4 = self.check_pkts_received()
        self.verify(len(out_4) == 1, "Wrong number of pkts received")
        self.verify(("0", mul_mac_0) in out_4, "pkt1 can't be received by port 0")

        # remove the multicast address configuration
        self.pmd_output.execute_cmd("mcast_addr remove 0 %s" % mul_mac_0)
        self.check_ports_multicast_address_number(0, 0)
        # send 4 packets
        p.send_pkt(self.tester, tx_port=self.tester_itf)
        out_5 = self.check_pkts_received()
        self.verify(len(out_5) == 0, "pkt1-4 can be received by any port")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("quit", "# ", 30)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.destroy_iavf()
        if self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.pf_interface, self.flag, self.default_stats),
                "# ",
            )
