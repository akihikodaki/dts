# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite.
Test the support of Jumbo Frames by Poll Mode Drivers
"""

import re
from time import sleep

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.settings import PROTOCOL_PACKET_SIZE
from framework.test_case import TestCase

ETHER_HEADER_LEN = 18
IP_HEADER_LEN = 20
ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestJumboframes(TestCase):
    def jumboframes_get_stat(self, portid, rx_tx):
        """
        Get packets number from port statistic
        """
        stats = self.pmdout.get_pmd_stats(portid)
        if rx_tx == "rx":
            return [stats["RX-packets"], stats["RX-errors"], stats["RX-bytes"]]
        elif rx_tx == "tx":
            return [stats["TX-packets"], stats["TX-errors"], stats["TX-bytes"]]
        else:
            return None

    def jumboframes_send_packet(self, pktsize, received=True):
        """
        Send 1 packet to portid
        """
        tx_pkts_ori, _, tx_bytes_ori = [
            int(_) for _ in self.jumboframes_get_stat(self.rx_port, "tx")
        ]
        rx_pkts_ori, rx_err_ori, rx_bytes_ori = [
            int(_) for _ in self.jumboframes_get_stat(self.tx_port, "rx")
        ]

        itf = self.tester.get_interface(self.tester.get_local_port(self.tx_port))
        mac = self.dut.get_mac_address(self.tx_port)

        # The packet total size include ethernet header, ip header, and payload.
        # ethernet header length is 18 bytes, ip standard header length is 20 bytes.
        pktlen = pktsize - ETHER_HEADER_LEN
        padding = pktlen - IP_HEADER_LEN

        self.tester.scapy_foreground()
        self.tester.scapy_append('nutmac="%s"' % mac)
        self.tester.scapy_append(
            'sendp([Ether(dst=nutmac, src="52:00:00:00:00:00")/IP(len=%s)/Raw(load="\x50"*%s)], iface="%s")'
            % (pktlen, padding, itf)
        )

        out = self.tester.scapy_execute()
        sleep(5)

        tx_pkts, _, tx_bytes = [
            int(_) for _ in self.jumboframes_get_stat(self.rx_port, "tx")
        ]
        rx_pkts, rx_err, rx_bytes = [
            int(_) for _ in self.jumboframes_get_stat(self.tx_port, "rx")
        ]

        tx_pkts -= tx_pkts_ori
        tx_bytes -= tx_bytes_ori
        rx_pkts -= rx_pkts_ori
        rx_bytes -= rx_bytes_ori
        rx_err -= rx_err_ori

        if received:
            if self.nic.startswith("fastlinq"):
                self.verify(
                    self.pmdout.check_tx_bytes(tx_pkts, rx_pkts)
                    and (self.pmdout.check_tx_bytes(tx_bytes, pktsize))
                    and (rx_bytes == pktsize),
                    "packet pass assert error",
                )
            else:
                self.verify(
                    self.pmdout.check_tx_bytes(tx_pkts, rx_pkts)
                    and (self.pmdout.check_tx_bytes(tx_bytes + 4, pktsize))
                    and ((rx_bytes + 4) == pktsize),
                    "packet pass assert error",
                )
        else:
            self.verify(rx_err == 1 or tx_pkts == 0, "packet drop assert error")
        return out

    #
    #
    #
    # Test cases.
    #
    def set_up_all(self):
        """
        Prerequisite steps for each test suit.
        """
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.rx_port = self.dut_ports[0]
        self.tx_port = self.dut_ports[0]

        cores = self.dut.get_core_list("1S/2C/1T")
        self.coremask = utils.create_mask(cores)

        self.port_mask = utils.create_mask([self.rx_port, self.tx_port])

        self.tester.send_expect(
            "ifconfig %s mtu %s"
            % (
                self.tester.get_interface(self.tester.get_local_port(self.rx_port)),
                ETHER_JUMBO_FRAME_MTU + 200,
            ),
            "# ",
        )

        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        This is to clear up environment before the case run.
        """
        self.dut.kill_all()

    def test_jumboframes_normal_nojumbo(self):
        """
        This case aims to test transmitting normal size packet without jumbo
        frame on testpmd app.
        """
        self.pmdout.start_testpmd(
            "Default",
            "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000"
            % (ETHER_STANDARD_MTU),
        )
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU - 1)
        self.jumboframes_send_packet(ETHER_STANDARD_MTU)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_jumboframes_jumbo_nojumbo(self):
        """
        This case aims to test transmitting jumbo frame packet on testpmd without
        jumbo frame support.
        """
        self.pmdout.start_testpmd(
            "Default",
            "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000"
            % (ETHER_STANDARD_MTU),
        )
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1, False)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_jumboframes_normal_jumbo(self):
        """
        When jumbo frame is supported, this case is to verify that the normal size
        packet forwarding should be supported correctly.
        """
        self.pmdout.start_testpmd(
            "Default",
            "--max-pkt-len=%s --port-topology=loop --tx-offloads=0x8000"
            % (ETHER_JUMBO_FRAME_MTU),
        )
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU - 1)
        self.jumboframes_send_packet(ETHER_STANDARD_MTU)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_jumboframes_jumbo_jumbo(self):
        """
        When jumbo frame supported, this case is to verify that jumbo frame
        packet can be forwarded correct.
        """
        self.pmdout.start_testpmd(
            "Default",
            "--max-pkt-len=%s --port-topology=loop --tx-offloads=0x8000"
            % (ETHER_JUMBO_FRAME_MTU),
        )
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1)
        self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU - 1)
        self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU)

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_jumboframes_bigger_jumbo(self):
        """
        When the jubmo frame MTU set as 9000, this case is to verify that the
        packet with a length bigger than MTU can not be forwarded.
        """
        self.pmdout.start_testpmd(
            "Default",
            "--max-pkt-len=%s --port-topology=loop --tx-offloads=0x8000"
            % (ETHER_JUMBO_FRAME_MTU),
        )
        self.dut.send_expect("set fwd mac", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        """
        On 1G NICs, when the jubmo frame MTU set as 9000, the software adjust it to 9004.
        """
        if self.nic in [
            "IGB_1G-I350_COPPER",
            "IGB_1G-I210_COPPER",
            "IGB_1G-82576_QUAD_COPPER_ET2",
            "IGC-I225_LM",
        ]:
            self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU + 4 + 1, False)
        else:
            self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU + 1, False)

        self.dut.send_expect("quit", "# ", 30)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        self.tester.send_expect(
            "ifconfig %s mtu %s"
            % (
                self.tester.get_interface(self.tester.get_local_port(self.rx_port)),
                ETHER_STANDARD_MTU,
            ),
            "# ",
        )
