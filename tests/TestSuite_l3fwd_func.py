# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

from framework.packet import Packet
from framework.test_case import TestCase


class TestL3fwdFunc(TestCase):
    """
    This suite is focus on l3fwd application, so any standard Ethernet Network Adapter is qualified.
    """

    def set_up_all(self):
        """
        Run at the start of each test suite.
        L3fwd Prerequisites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.app_path = self.dut.build_dpdk_apps("examples/l3fwd")
        self.pkt = Packet()
        self.dport_info0 = self.dut.ports_info[self.dut_ports[0]]
        tport = self.tester.get_local_port(self.dut_ports[0])
        self.tport_info0 = self.tester.ports_info[tport]
        self.tport_intf0 = self.tport_info0["intf"]
        # judgment is added to avoid errors caused by the absence of port 1
        if len(self.dut_ports) >= 2:
            self.dport_info1 = self.dut.ports_info[self.dut_ports[1]]
            self.tport_info1 = self.tester.ports_info[self.dut_ports[1]]
            self.tport_intf1 = self.tport_info1["intf"]
        self.ip_src = "1.2.3.4"
        self.ip_dst = "198.168.0.%s"
        self.ipv6_src = "fe80::b696:91ff:fe9f:64b9"
        self.ipv6_dst = "2001:200::%s"

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def launch_l3fwd(self, eal_params, params):
        """
        launch l3fwd and return echo information
        :param eal_params: the eal parameter of launch l3fwd
        :param params: other params
        :return: echo information after launch l3fwd
        """
        expected = "Link up"
        out = self.dut.send_expect(
            "%s %s -- %s" % (self.app_path, eal_params, params), expected, timeout=30
        )
        return out

    def check_l3fwd_message(self, message, check_mesg):
        """
        check check_mesg in message
        :param message: information to be detected
        :param check_mesg: detection information, list or str
        :return:
        """
        mesg = [check_mesg] if isinstance(check_mesg, str) else check_mesg
        for info in mesg:
            self.verify(info in message, "%s not found in l3fwd" % info)

    def build_packet(self, packet_pattern, type, num, dstmac, srcmac):
        """
        build the required packages
        :param packet_pattern: 'Ether(dst="%s", src="%s")/IP(src="%s",dst="%s")/Raw("x"*80)'
        :param type: ipv4 or ipv6
        :param num: number of packets required
        :param dstip: Ether dts mac
        :param srcip: Ether src mac
        :return: the list of packets
        """
        packets = []
        if type == "ipv4":
            for i in range(num):
                pkt = packet_pattern % (
                    dstmac,
                    srcmac,
                    self.ip_src,
                    self.ip_dst % (1 + i),
                )
                packets.append(pkt)
        elif type == "ipv6":
            for i in range(num):
                pkt = packet_pattern % (
                    dstmac,
                    srcmac,
                    self.ipv6_src,
                    self.ipv6_dst % (1 + i),
                )
                packets.append(pkt)
        else:
            self.verify(False, "The type of packet is not defined")
        return packets

    def check_package_received(self, send_pkt_num, type):
        """
        check the type and number of packets received
        :param send_pkt_num: the number of send packets, list
        :param type: the type of packet, ipv4 or ipv6
        :return:
        """
        out = self.tester.send_expect(
            "tcpdump -n -r /tmp/tester/sniff_%s.pcap" % (self.tport_intf0),
            "# ",
            timeout=30,
        )
        lost_list = []
        for i in range(send_pkt_num):
            if type == "ipv4":
                lost_list if "IP %s > %s" % (
                    self.ip_src,
                    self.ip_dst % (i + 1),
                ) in out else lost_list.append(self.ip_dst % (i + 1))

            elif type == "ipv6":
                lost_list if "IP6 %s > %s" % (
                    self.ipv6_src,
                    self.ipv6_dst % (i + 1),
                ) in out else lost_list.append(self.ip_dst % (i + 1))

            else:
                self.verify(False, "The type of packet is not defined")

        if lost_list:
            self.verify(False, "Packet with DST mac %s is missing" % lost_list)

    def test_1_port_1_queue_default(self):
        """
        1 port 1 queue with default setting
        """
        eal_params = self.dut.create_eal_parameters(
            cores=[1], ports=self.dut_ports[0:1]
        )
        params = '-p 0x1 --config="(0,0,1)" --eth-dest=0,b4:96:91:9f:64:b9'
        out = self.launch_l3fwd(eal_params, params)
        mesg_list = [
            "Neither LPM, EM, or FIB selected, defaulting to LPM",
            "L3FWD: Missing 1 or more rule files, using default instead",
        ]
        self.check_l3fwd_message(out, mesg_list)
        packets = {
            "ipv4": 'Ether(dst="%s", src="%s")/IP(src="%s",dst="%s")/Raw("x"*80)',
            "ipv6": 'Ether(dst="%s", src="%s")/IPv6(src="%s",dst="%s")/Raw("x"*80)',
        }
        match_dst = self.dport_info0["mac"]
        src = self.tport_info0["mac"]
        for type in packets.keys():
            pkts = self.build_packet(packets[type], type, 10, match_dst, src)
            inst = self.tester.tcpdump_sniff_packets(self.tport_intf0)
            self.pkt.pktgen.pkts = []
            self.pkt.update_pkt(pkts)
            self.pkt.send_pkt(self.tester, self.tport_intf0)
            self.tester.load_tcpdump_sniff_packets(inst)
            self.check_package_received(len(pkts), type)

    def test_1_port_4_queues_non_default(self):
        """
        1 port 4 queue with non-default setting
        """
        # if port number > 1, skip this case
        self.skip_case(len(self.dut_ports) <= 1, "Only support 1 port")
        eal_params = self.dut.create_eal_parameters(
            cores=[1, 2], ports=self.dut_ports[0:2]
        )
        params = (
            '-p 0x1 --config="(0,0,1),(0,1,1),(0,2,2),(0,3,2)" -P '
            '--rule_ipv4="./examples/l3fwd/em_default_v4.cfg" --rule_ipv6="./examples/l3fwd/em_default_v6.cfg"'
            " --lookup=em --rx-queue-size=2048 --tx-queue-size=2048 --parse-ptype"
        )
        out = self.launch_l3fwd(eal_params, params)
        mesg_list = "EM: Adding route 198.18.0.0, 198.18.0.1, 9, 9, 17 (0) [%s]" % (
            self.dport_info0["pci"]
        )
        self.check_l3fwd_message(out, mesg_list)
        packets = {
            "ipv4": 'Ether(dst="%s", src="%s")/IP(src="%s",dst="%s")/Raw("x"*80)',
            "ipv6": 'Ether(dst="%s", src="%s")/IPv6(src="%s",dst="%s")/Raw("x"*80)',
        }
        unmatch_dst = "0123456"
        src = self.tport_info0["mac"]
        for type in packets.keys():
            pkts = self.build_packet(packets[type], type, 20, unmatch_dst, src)
            inst = self.tester.tcpdump_sniff_packets(self.tport_intf0)
            self.pkt.pktgen.pkts = []
            self.pkt.update_pkt(pkts)
            self.pkt.send_pkt(self.tester, self.tport_intf0)
            self.tester.load_tcpdump_sniff_packets(inst)
            self.check_package_received(len(pkts), type)

    def test_2_ports_4_queues_non_default(self):
        """
        2 ports 4 queues with non-default setting
        """
        # if port number < 2, skip this case
        self.skip_case(len(self.dut_ports) >= 2, "At least 2 ports are required")
        eal_params = self.dut.create_eal_parameters(
            cores=[1, 2], ports=self.dut_ports[0:2]
        )
        params = (
            '-p 0x3 --config="(0,0,1),(0,1,1),(0,2,2),(0,3,2),(1,0,1),(1,1,1),(1,2,2),(1,3,2)" -P '
            '--rule_ipv4="./examples/l3fwd/em_default_v4.cfg" --rule_ipv6="./examples/l3fwd/em_default_v6.cfg" '
            "--lookup=em --rx-queue-size=2048 --tx-queue-size=2048 --parse-ptype"
        )
        out = self.launch_l3fwd(eal_params, params)
        mesg_list = [
            "EM: Adding route 198.18.0.0, 198.18.0.1, 9, 9, 17 (0) [%s]"
            % (self.dport_info0["pci"]),
            "EM: Adding route 198.18.1.0, 198.18.1.1, 9, 9, 17 (1) [%s]"
            % (self.dport_info1["pci"]),
        ]
        self.check_l3fwd_message(out, mesg_list)
        packets = {
            "ipv4": 'Ether(dst="%s", src="%s")/IP(src="%s",dst="%s")/Raw("x"*80)',
            "ipv6": 'Ether(dst="%s", src="%s")/IPv6(src="%s",dst="%s")/Raw("x"*80)',
        }
        unmatch_dst = "0123456"
        src0 = self.tport_info0["mac"]
        src1 = self.tport_info1["mac"]
        for type in packets.keys():
            # port 0
            pkts0 = self.build_packet(packets[type], type, 20, unmatch_dst, src0)
            inst0 = self.tester.tcpdump_sniff_packets(self.tport_intf0)
            self.pkt.pktgen.pkts = []
            self.pkt.update_pkt(pkts0)
            self.pkt.send_pkt(self.tester, self.tport_intf0)
            self.tester.load_tcpdump_sniff_packets(inst0)
            self.check_package_received(len(pkts0), type)

            # port 1
            pkts1 = self.build_packet(packets[type], type, 20, unmatch_dst, src1)
            inst1 = self.tester.tcpdump_sniff_packets(self.tport_intf1)
            self.pkt.update_pkt(pkts1)
            self.pkt.send_pkt(self.tester, self.tport_intf1)
            self.tester.load_tcpdump_sniff_packets(inst1)
            self.check_package_received(len(pkts1), type)

    def tear_down(self):
        """
        run after each test case.
        """
        # close l3fwd
        self.dut.send_expect("^C", "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        run after each test suite.
        """
        pass
