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
MTU Checks example.
"""
import os
import re
import subprocess
import time
from time import sleep
from typing import List, Tuple

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import TRANSMIT_CONT
from framework.pktgen_base import TRANSMIT_S_BURST
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase

ETHER_HEADER_LEN = 18
VLAN=4
IP_HEADER_LEN = 20
ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestMtuUpdate(TestCase):
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
        itf = self.tester.get_interface(self.tester.get_local_port(port_id))

        self.tester.scapy_foreground()
        mac = self.dut.get_mac_address(port_id)
        self.tester.scapy_append(f'dutmac="{mac}"')
        self.tester.scapy_append(f'sendp({packet}, iface="{itf}")')
        return self.tester.scapy_execute()

    def send_packet_of_size_to_port(self, port_id: int, pktsize: int):

        # The packet total size include ethernet header, ip header, and payload.
        # ethernet header length is 18 bytes, ip standard header length is 20 bytes.
        # pktlen = pktsize - ETHER_HEADER_LEN
        if self.kdriver in ["igb", "igc", "ixgbe"]:
            max_pktlen = pktsize + ETHER_HEADER_LEN + VLAN
            padding = max_pktlen - IP_HEADER_LEN - ETHER_HEADER_LEN-VLAN
        else:
            max_pktlen = pktsize + ETHER_HEADER_LEN + VLAN * 2
            padding = max_pktlen - IP_HEADER_LEN - ETHER_HEADER_LEN
        out = self.send_scapy_packet(port_id,
                                     f'Ether(dst=dutmac, src="52:00:00:00:00:00")/IP()/Raw(load="\x50"*{padding})')
        return out


    def send_packet_of_size_to_tx_port(self, pktsize, received=True):
        """
        Send 1 packet to portid
        """
        tx_pkts_ori, tx_err_ori, _ = [int(_) for _ in self.get_port_status_tx(self.tx_port)]
        rx_pkts_ori, rx_err_ori, _ = [int(_) for _ in self.get_port_status_rx(self.rx_port)]

        out = self.send_packet_of_size_to_port(self.rx_port, pktsize)

        sleep(5)

        tx_pkts, tx_err, _ = [int(_) for _ in self.get_port_status_tx(self.tx_port)]
        rx_pkts, rx_err, _ = [int(_) for _ in self.get_port_status_rx(self.rx_port)]

        tx_pkts_difference = tx_pkts - tx_pkts_ori
        tx_err_difference = tx_err - tx_err_ori
        rx_pkts_difference = rx_pkts - rx_pkts_ori
        rx_err_difference = rx_err - rx_err_ori

        if received:
            self.verify(tx_pkts_difference >= 1, "No packet was sent")
            self.verify(tx_pkts_difference == rx_pkts_difference, "different numbers of packets sent and received")
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
        self.set_mtu(ETHER_JUMBO_FRAME_MTU + 200)

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

    def admin_tester_port(self, local_port, status):
        """
        Do some operations to the network interface port, such as "up" or "down".
        """
        if self.tester.get_os_type() == 'freebsd':
            self.tester.admin_ports(local_port, status)
        else:
            eth = self.tester.get_interface(local_port)
            self.tester.admin_ports_linux(eth, status)
        time.sleep(10)

    def set_mtu(self, mtu) -> None:
        """
        A function which sets the MTU of the ports on the tester to a provided value.
        This function is primarily used to make sure that the tester will
        always be able to send packets that are larger than a standard mtu
        while testing.

        @param mtu: The desired MTU for local ports
        @return: None
        """
        self.admin_tester_port(self.tester.get_local_port(self.tx_port), f"mtu {mtu:d}")
        self.admin_tester_port(self.tester.get_local_port(self.rx_port), f"mtu {mtu:d}")
    #
    #
    #
    # Test cases.
    #

    def helper_test_mut_checks(self, packet_size):
        """
        Sends a packet of the given size into the testing machine.
        """
        if self.kdriver == "mlx5_core" or self.kdriver == "mlx4_core" or self.kdriver == "ixgbe":
        # Mellanox will need extra options to start testpmd
            self.pmdout.start_testpmd("Default", "--max-pkt-len=9500 --tx-offloads=0x8000 --enable-scatter -a")
        else:
            self.pmdout.start_testpmd("Default")

        self.exec("port stop all")
        self.exec(f"port config mtu 0 {packet_size:d}")
        self.exec(f"port config mtu 1 {packet_size:d}")
        self.verify(int(self.pmdout.get_detail_from_port_info("MTU: ", "\d+", 0)) == packet_size, "MTU did not update")
        self.verify(int(self.pmdout.get_detail_from_port_info("MTU: ", "\d+", 1)) == packet_size, "MTU did not update")
        self.exec("port start all")
        self.exec("set fwd mac")
        self.exec("start")
        self.pmdout.wait_link_status_up(self.dut_ports[0])
        """
        On 1G NICs, when the jubmo frame MTU set > 1500, the software adjust it to MTU+4.
        """
        if self.nic in ["powerville", "springville", "foxville"] and packet_size > 1500:
            self.send_packet_of_size_to_tx_port(packet_size + 8 - 1, received=True)
            self.send_packet_of_size_to_tx_port(packet_size + 8, received=True)
            self.send_packet_of_size_to_tx_port(packet_size + 8 + 1, received=False)
        else:
            self.send_packet_of_size_to_tx_port(packet_size - 1, received=True)
            self.send_packet_of_size_to_tx_port(packet_size, received=True)
            self.send_packet_of_size_to_tx_port(packet_size + 1, received=False)

        self.exec("stop")
        self.pmdout.quit()

    def test_mtu_checks_100(self):
        """
        Checks that the port responds properly to having it's MTU set to 100 and
         then being sent packets of size 100 and 101.
        """
        self.helper_test_mut_checks(100)

    def test_mtu_checks_1500(self):
        """
        Checks that the port responds properly to having it's MTU set to 1500 and
         then being sent packets of size 1500 and 1501.
        """
        self.helper_test_mut_checks(1500)

    def test_mtu_checks_2400(self):
        """
        Checks that the port responds properly to having it's MTU set to 2400 and
         then being sent packets of size 2400 and 2401.
        """
        self.helper_test_mut_checks(2400)

    def test_mtu_checks_4800(self):
        """
        Checks that the port responds properly to having it's MTU set to 4800 and
         then being sent packets of size 4800 and 4801.
        """
        self.helper_test_mut_checks(4800)

    def test_mtu_checks_9000(self):
        """
        Checks that the port responds properly to having it's MTU set to 9000 and
         then being sent packets of size 8999 and 9000.
        """
        self.helper_test_mut_checks(9000)
