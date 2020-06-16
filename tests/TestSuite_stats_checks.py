# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
# Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
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
Stats Checks example.
"""
from time import sleep
from typing import List, Iterator, Tuple

import utils
from pmd_output import PmdOutput

from port import Port

from test_case import TestCase

ETHER_HEADER_LEN = 18
IP_HEADER_LEN = 20
ETHER_STANDARD_MTU = 1518


class TestStatsChecks(TestCase):
    #
    #
    # Helper methods and setup methods.
    #
    # Some of these methods may not be used because they were inlined from a child
    # of TestCase. This was done because the current test system doesn't support
    # inheritance.
    #
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
        self.tester.send_expect(f"ifconfig {self.tester.get_interface(self.tester.get_local_port(self.rx_port))} " +
                                f"mtu {ETHER_STANDARD_MTU}", "# ")
        super().tear_down_all()

    def exec(self, command: str) -> str:
        """
        An abstraction to remove repeated code throughout the subclasses of this class
        """
        return self.dut.send_expect(command, "testpmd>")

    def get_mac_address_for_port(self, port_id: int) -> str:
        return self.dut.get_mac_address(port_id)

    def send_scapy_packet(self, port_id: int, packet: str):
        itf = self.tester.get_interface(port_id)

        self.tester.scapy_foreground()
        mac = self.dut.get_mac_address(port_id)
        self.tester.scapy_append(f'dutmac="{mac}"')
        self.tester.scapy_append(f'sendp({packet}, iface="{itf}")')
        return self.tester.scapy_execute()

    def send_packet_of_size_to_port(self, port_id: int, pktsize: int):

        # The packet total size include ethernet header, ip header, and payload.
        # ethernet header length is 18 bytes, ip standard header length is 20 bytes.
        # pktlen = pktsize - ETHER_HEADER_LEN
        padding = pktsize - IP_HEADER_LEN
        out = self.send_scapy_packet(port_id,
                                     f'Ether(dst=dutmac, src="52:00:00:00:00:00")/IP()/Raw(load="\x50"*{padding})')
        return out

    def send_packet_of_size_to_tx_port(self, pktsize, received=True):
        """
        Send 1 packet to portid
        """
        tx_pkts_ori, tx_err_ori, tx_bytes_ori = [int(_) for _ in self.get_port_status_rx(self.tx_port)]
        rx_pkts_ori, rx_err_ori, rx_bytes_ori = [int(_) for _ in self.get_port_status_tx(self.rx_port)]

        out = self.send_packet_of_size_to_port(self.tx_port, pktsize)

        sleep(5)

        tx_pkts, tx_err, tx_bytes = [int(_) for _ in self.get_port_status_rx(self.tx_port)]
        rx_pkts, rx_err, rx_bytes = [int(_) for _ in self.get_port_status_tx(self.rx_port)]

        tx_pkts_difference = tx_pkts - tx_pkts_ori
        tx_err_difference = tx_err - tx_err_ori
        tx_bytes_difference = tx_bytes - tx_bytes_ori
        rx_pkts_difference = rx_pkts - rx_pkts_ori
        rx_err_difference = rx_err - rx_err_ori
        rx_bytes_difference = rx_bytes - rx_bytes_ori

        if received:
            self.verify(tx_pkts_difference >= 1, "No packet was sent")
            self.verify(tx_bytes_difference == pktsize + ETHER_HEADER_LEN)
            self.verify(tx_pkts_difference == rx_pkts_difference, "different numbers of packets sent and received")
            self.verify(tx_bytes_difference == rx_bytes_difference, "different number of bytes sent and received")
            self.verify(tx_err_difference == 0, "unexpected tx error")
            self.verify(rx_err_difference == 0, "unexpected rx error")
        else:
            self.verify(rx_err_difference == 1 or tx_pkts_difference == 0 or tx_err_difference == 1,
                        "packet that either should have either caused an error " +
                        "or been rejected for transmission was not")
        return out

    def get_port_status_rx(self, portid) -> Tuple[str, str, str]:
        stats = self.pmdout.get_pmd_stats(portid)
        return stats['RX-packets'], stats['RX-errors'], stats['RX-bytes']

    def get_port_status_tx(self, portid) -> Tuple[str, str, str]:
        stats = self.pmdout.get_pmd_stats(portid)
        return stats['TX-packets'], stats['TX-errors'], stats['TX-bytes']

    def set_up_all(self):
        """
        Prerequisite steps for each test suit.
        """
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.rx_port = self.dut_ports[0]
        self.tx_port = self.dut_ports[1]

        cores = self.dut.get_core_list("1S/2C/1T")
        self.coremask = utils.create_mask(cores)

        self.port_mask = utils.create_mask([self.rx_port, self.tx_port])

        self.pmdout = PmdOutput(self.dut)

    def set_up(self):
        """
        This is to clear up environment before the case run.
        """
        self.dut.kill_all()

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
        self.dut.kill_all()

    #
    #
    #
    # Test cases.
    #

    def test_stats_checks(self):
        self.pmdout.start_testpmd("Default")
        self.exec("port start all")
        self.exec("set fwd mac")
        self.exec("start")

        self.send_packet_of_size_to_tx_port(50, received=True)

        self.exec("stop")
        self.pmdout.quit()
