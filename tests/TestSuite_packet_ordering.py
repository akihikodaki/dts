# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2020 Intel Corporation
#

"""
DPDK Test suite.
Packet ordering example app test cases.
"""

import os
import time

import framework.utils as utils
from framework.packet import Packet
from framework.test_case import TestCase


class TestPacketOrdering(TestCase):
    def set_up_all(self):
        """
        Executes the Packet Ordering prerequisites. Creates a simple scapy
        packet to be used later on the tests. It also compiles the example app.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]

        # Verify that enough ports are available
        self.verify(len(valports) >= 1, "Insufficient ports for speed testing")
        self.port = self.tester.get_local_port(valports[0])

        # get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/4C/1T", socket=self.socket)
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")
        self.verify(self.cores is not None, "Insufficient cores for speed testing")

        self.core_mask = utils.create_mask(self.cores)
        self.port_mask = utils.create_mask(valports)

        # Builds the packet ordering example app and checks for errors.
        # out = self.dut.send_expect("make -C examples/packet_ordering", "#")
        out = self.dut.build_dpdk_apps("./examples/packet_ordering")
        self.verify(
            "Error" not in out and "No such file" not in out, "Compilation error"
        )

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def start_application(self):

        app_name = self.dut.apps_name["packet_ordering"]
        cmdline = app_name + "{0} -- -p {1}".format(self.eal_para, self.port_mask)
        # Executes the packet ordering example app.
        self.dut.send_expect(cmdline, "REORDERAPP", 120)

    def remove_dhcp_from_revpackets(self, inst, timeout=3):

        pkts = self.tester.load_tcpdump_sniff_packets(inst, timeout)
        i = 0
        while len(pkts) != 0 and i <= len(pkts) - 1:
            if pkts[i].pktgen.pkt.haslayer("DHCP"):
                pkts.remove(pkts[i])
                i = i - 1
            i = i + 1
        return pkts

    def send_ordered_packet(self):
        """
        send the packets with ordered of src-ip info.
        compose the pcap file, each queue has same 5 tuple and diff load info
        """

        pkt = Packet()
        src_ip = "11.12.13.1"
        pay_load = "000001"
        packet_num = 1000
        smac = "00:00:00:00:00:00"
        rx_interface = self.tester.get_interface(self.port)
        tx_interface = rx_interface
        for _port in valports:
            index = valports[_port]
            dmac = self.dut.get_mac_address(index)
            config_opt = [
                ("ether", {"dst": dmac, "src": smac}),
                ("ipv4", {"src": src_ip, "dst": "11.12.1.1"}),
                ("udp", {"src": 123, "dst": 12}),
            ]
            pkt.generate_random_pkts(
                pktnum=packet_num,
                random_type=["UDP"],
                ip_increase=False,
                random_payload=False,
                options={"layers_config": config_opt},
            )
            # config raw info in pkts
            for i in range(packet_num):
                payload = "0000%.3d" % (i + 1)
                pkt.pktgen.pkts[i + packet_num * _port]["Raw"].load = payload

        filt = [{"layer": "ether", "config": {"src": "%s" % smac}}]
        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=filt)
        pkt.send_pkt(crb=self.tester, tx_port=tx_interface, timeout=300)
        self.pkts = self.remove_dhcp_from_revpackets(inst)

    def check_packet_order(self):
        """
        observe the packets sended by scapy, check the packets order
        """

        for _port in valports:
            src_ip = "11.12.13.%d" % (_port + 1)
            packet_index = 0
            for i in range(len(self.pkts)):
                pay_load = "0000%.2d" % packet_index
                if self.pkts[i]["IP"].src == src_ip:
                    print(self.pkts[i].show)
                    if packet_index == 0:
                        packet_index = int(self.pkts[i]["Raw"].load[-2:])
                        pay_load = "0000%.2d" % packet_index
                    self.verify(
                        self.pkts[i]["Raw"].load == pay_load, "The packets not ordered"
                    )
                    packet_index = packet_index + 1

    def test_keep_packet_oeder(self):
        """
        keep the packets order with one ordered stage in single-flow and multi-flow
        according to the tcpdump may be capture the packets whitch not belong current
        flow, so set different src_mac of flow to identify the packets
        """
        self.start_application()
        # send packets
        self.send_ordered_packet()
        # check packet ordering
        self.check_packet_order()
        self.dut.send_expect("^c", "#", 10)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
