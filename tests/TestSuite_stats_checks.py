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
import random
import re
import socket
import struct
from time import sleep
from typing import Iterator, List, Tuple

import framework.packet as packet
import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

ETHER_HEADER_LEN = 18
IP_HEADER_LEN = 20
RANDOM_IP_POOL = ['192.168.10.222/0']
prefix_list = ['rx_good_packets', 'tx_good_packets', 'rx_good_bytes', 'tx_good_bytes']


class TestStatsChecks(TestCase):
    #
    #
    # Helper methods and setup methods.
    #
    # Some of these methods may not be used because they were inlined from a child
    # of TestCase. This was done because the current test system doesn't support
    # inheritance.
    #
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

    def get_random_ip(self):
        str_ip = RANDOM_IP_POOL[random.randint(0, len(RANDOM_IP_POOL) - 1)]
        str_ip_addr = str_ip.split('/')[0]
        str_ip_mask = str_ip.split('/')[1]
        ip_addr = struct.unpack('>I', socket.inet_aton(str_ip_addr))[0]
        mask = 0x0
        for i in range(31, 31 - int(str_ip_mask), -1):
            mask = mask | (1 << i)
        ip_addr_min = ip_addr & (mask & 0xffffffff)
        ip_addr_max = ip_addr | (~mask & 0xffffffff)
        return socket.inet_ntoa(struct.pack('>I', random.randint(ip_addr_min, ip_addr_max)))

    def send_packet_of_size_to_port(self, port_id: int, pktsize: int):

        # The packet total size include ethernet header, ip header, and payload.
        # ethernet header length is 18 bytes, ip standard header length is 20 bytes.
        # pktlen = pktsize - ETHER_HEADER_LEN
        padding = pktsize - IP_HEADER_LEN
        out = self.send_scapy_packet(port_id,
                                     f'Ether(dst=dutmac, src="52:00:00:00:00:00")/IP()/Raw(load="\x50"*{padding})')
        return out

    def send_pkt_with_random_ip(self, port, count, if_vf=False):
        """
        send pkt with random ip
        port: send pkt port
        count: pkt count
        """
        pkt = packet.Packet()
        pkt.assign_layers(['ether', 'ipv4'])
        mac = self.pmdout.get_port_mac(port) if if_vf else self.dut.get_mac_address(port)
        for i in range(count):
            src_ip = self.get_random_ip()
            pkt.config_layers([('ether', {'dst': mac}),
                               ('ipv4', {'src': src_ip})])
            pkt.send_pkt(crb=self.tester,
                         tx_port=self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0])))

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

    def get_xstats(self, port_id_list):
        xstats_data = dict()
        for port_id in port_id_list:
            out = self.exec('show port xstats %s' % port_id)
            tmp_data = dict()
            for prefix in prefix_list:
                pattern = re.compile('%s:(\\s+)([0-9]+)' % prefix)
                m = pattern.search(out)
                if not m:
                    tmp_data.setdefault(prefix, 0)
                else:
                    tmp_data.setdefault(prefix, int(m.group(2)))
            xstats_data[port_id] = tmp_data
        return xstats_data

    def verify_results(self, xstats_data, rx_port, tx_port, stats_data={}, if_zero=False):
        if if_zero:
            for port in xstats_data.keys():
                self.verify(not any(xstats_data[port].values()), 'xstats Initial value error! port {} xstats '
                                                                 'data is {}'.format(port, xstats_data[port]))
        else:
            self.verify(xstats_data[rx_port]['rx_good_packets'] == stats_data[rx_port]['RX-packets']
                        == xstats_data[tx_port]['tx_good_packets'] == stats_data[tx_port]['TX-packets']
                        == 100, "pkt recieve or transport count error!")
            self.verify(xstats_data[rx_port]['rx_good_bytes'] == stats_data[rx_port]['RX-bytes'] ==
                        xstats_data[tx_port]['tx_good_bytes'] == stats_data[tx_port]['TX-bytes'],
                        'pkt recieve or transport bytes error!')

    def xstats_check(self, rx_port, tx_port, if_vf=False):
        self.exec("port config all rss all")
        self.exec("set fwd mac")
        self.exec("clear port xstats all")
        org_xstats = self.get_xstats([rx_port, tx_port])
        self.verify_results(org_xstats, rx_port, tx_port, if_zero=True)
        final_xstats, stats_data = self.sendpkt_get_xstats(rx_port, tx_port, if_vf)
        self.verify_results(final_xstats, rx_port, tx_port, stats_data=stats_data)
        self.exec("clear port stats all")
        clear_stats = self.get_xstats([rx_port, tx_port])
        self.verify_results(clear_stats, rx_port, tx_port, if_zero=True)

        final_xstats, stats_data = self.sendpkt_get_xstats(rx_port, tx_port, if_vf)
        self.verify_results(final_xstats, rx_port, tx_port, stats_data=stats_data)
        self.exec("clear port xstats all")
        clear_xstats = self.get_xstats([rx_port, tx_port])
        self.verify_results(clear_xstats, rx_port, tx_port, if_zero=True)
        self.pmdout.quit()

    def sendpkt_get_xstats(self, rx_port, tx_port, if_vf):
        self.exec("start")
        self.send_pkt_with_random_ip(tx_port, count=100, if_vf=if_vf)
        self.exec("stop")
        if rx_port == tx_port:
            final_xstats = self.get_xstats([rx_port])
            stats_data = {
                rx_port: self.pmdout.get_pmd_stats(rx_port)
            }
        else:
            rx_stats_info = self.pmdout.get_pmd_stats(rx_port)
            tx_stats_info = self.pmdout.get_pmd_stats(tx_port)
            final_xstats = self.get_xstats([rx_port, tx_port])
            stats_data = {
                rx_port: rx_stats_info,
                tx_port: tx_stats_info
            }
        return final_xstats, stats_data

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

    def test_stats_checks(self):
        self.pmdout.start_testpmd("Default")
        self.exec("port start all")
        self.exec("set fwd mac")
        self.exec("start")

        self.send_packet_of_size_to_tx_port(50, received=True)

        self.exec("stop")
        self.pmdout.quit()

    def test_xstats_check_pf(self):
        self.pmdout.start_testpmd('default', '--rxq=4 --txq=4')
        self.xstats_check(self.rx_port, self.tx_port)

    def test_xstats_check_vf(self):
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 1, self.kdriver)
        self.vf_port = self.dut.ports_info[self.dut_ports[0]]["vfs_port"][0]
        self.vf_port.bind_driver(driver="vfio-pci")
        self.vf_port_pci = self.dut.ports_info[self.dut_ports[0]]['sriov_vfs_pci'][0]
        self.pmdout.start_testpmd('default', '--rxq=4 --txq=4', eal_param='-a %s' % self.vf_port_pci)
        self.xstats_check(0, 0, if_vf=True)
