# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

Test VEB Switch and floating VEB Features by Poll Mode Drivers.
"""

import re
import time
import utils

from virt_dut import VirtDut
from project_dpdk import DPDKdut
from dut import Dut
from test_case import TestCase
from pmd_output import PmdOutput
from settings import HEADER_SIZE
from packet import Packet
from utils import RED


class TestVEBSwitching(TestCase):

    def VEB_get_stats(self, vf0_vf1, portid, rx_tx):
        """
        Get packets number from port statistic
        """
        if vf0_vf1 == "vf0":
            stats = self.pmdout.get_pmd_stats(portid)
        elif vf0_vf1 == "vf1":
            stats = self.pmdout_session_secondary.get_pmd_stats(portid)
        else:
            return None

        if rx_tx == "rx":
            return [stats['RX-packets'], stats['RX-errors'], stats['RX-bytes']]
        elif rx_tx == "tx":
            return [stats['TX-packets'], stats['TX-errors'], stats['TX-bytes']]
        else:
            return None
 
    def veb_get_pmd_stats(self, dev, portid, rx_tx):
        stats = {}
        rx_pkts_prefix = "RX-packets:"
        rx_bytes_prefix = "RX-bytes:"
        rx_error_prefix = "RX-errors:"
        tx_pkts_prefix = "TX-packets:"
        tx_error_prefix = "TX-errors:"
        tx_bytes_prefix = "TX-bytes:"

        if dev == "first":
            out = self.dut.send_expect("show port stats %d" % portid, "testpmd> ")
        elif dev == "second":
            out = self.session_secondary.send_expect("show port stats %d" % portid, "testpmd> ")
        elif dev == "third":
            out = self.session_third.send_expect("show port stats %d" % portid, "testpmd> ")
        else:
            return None

        stats["RX-packets"] = self.veb_get_pmd_value(rx_pkts_prefix, out)
        stats["RX-bytes"] = self.veb_get_pmd_value(rx_bytes_prefix, out)
        stats["RX-errors"] = self.veb_get_pmd_value(rx_error_prefix, out)
        stats["TX-packets"] = self.veb_get_pmd_value(tx_pkts_prefix, out)
        stats["TX-errors"] = self.veb_get_pmd_value(tx_error_prefix, out)
        stats["TX-bytes"] = self.veb_get_pmd_value(tx_bytes_prefix, out)

        if rx_tx == "rx":
            return [stats['RX-packets'], stats['RX-errors'], stats['RX-bytes']]
        elif rx_tx == "tx":
            return [stats['TX-packets'], stats['TX-errors'], stats['TX-bytes']]
        else:
            return None

    def veb_get_pmd_value(self, prefix, out):
        pattern = re.compile(prefix + "(\s+)([0-9]+)")
        m = pattern.search(out)
        if m is None:
            return None
        else:
            return int(m.group(2))

    def send_packet(self, vf_mac, itf, tran_type=""):
        """
        Send 1 packet
        """
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        if tran_type == "vlan":
            pkt = Packet(pkt_type='VLAN_UDP')
            pkt.config_layer('ether', {'dst': vf_mac})
            pkt.config_layer('vlan', {'vlan': 1})
            pkt.send_pkt(self.tester, tx_port=itf)
            time.sleep(.5)
        else:
            pkt = Packet(pkt_type='UDP')
            pkt.config_layer('ether', {'dst': vf_mac})
            pkt.send_pkt(self.tester, tx_port=itf)
            time.sleep(.5)

    def count_packet(self, out, mac):
        """
        Count packet sum number.
        """
        lines = out.split("\r\n")
        cnt = 0
        count_pkt = 0
        # count the packet received from specified mac address.
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.startswith(("src=",)):
                for item in line.split(" "):
                    item = item.strip()
                    if(item == ("src=%s" % mac)):
                        cnt = cnt + 1
                    elif(item == "L4_UDP"):
                        cnt = cnt + 1
                if (cnt == 2):
                    count_pkt = count_pkt + 1
                cnt = 0
        print(utils.GREEN("The number of UDP packets received by pf is %d." % count_pkt))
        return count_pkt

    # Test cases.
    def set_up_all(self):
        """
        Prerequisite steps for each test suite.
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                    "fortville_spirit_single", "fortville_25g", "carlsville",
                                 'columbiaville_100g', 'columbiaville_25g'],
                    "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()
        self.pmdout = PmdOutput(self.dut)
        self.pmdout_2 = PmdOutput(self.dut, self.session_secondary)
        self.pmdout_3 = PmdOutput(self.dut, self.session_third)

        self.pf_kdriver_flag = 0
        self.pf_ddriver_flag = 0
        self.vf0_mac = "00:11:22:33:44:11"
        self.vf1_mac = "00:11:22:33:44:12"
        self.vf2_mac = "00:11:22:33:44:13"
        self.vf3_mac = "00:11:22:33:44:14"
 
        self.used_dut_port = self.dut_ports[0]
        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.used_dut_port]['intf']
        self.pf_mac_address = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.used_dut_port]['pci']

        self.dut.init_reserved_core()
        self.cores_vf0 = self.dut.get_reserved_core('2C', 0)
        self.cores_vf1 = self.dut.get_reserved_core('2C', 0)

    def set_up(self):
        """
        This is to clear up environment before the case run.
        """
        self.dut.kill_all()

    def setup_env(self, driver):
        """
        This is to set up 1pf and 2vfs environment, the pf can be bond to
        kernel driver or dpdk driver.
        """
        if driver == 'default':
            for port_id in self.dut_ports:
                port = self.dut.ports_info[port_id]['port']
                port.bind_driver()
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2, driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
        if driver == 'default':
            self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.pf_interface, self.vf0_mac), "# ", 3)
            self.dut.send_expect("ip link set %s vf 1 mac %s" % (self.pf_interface, self.vf1_mac), "# ", 3)

        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(driver=self.drivername)
            if driver == 'default':
                self.pf_kdriver_flag = 1
            else:
                self.pf_ddriver_flag = 1
        except Exception as e:
            self.destroy_env(driver)
            raise Exception(e)

    def destroy_env(self, driver):
        """
        This is to destroy 1pf and 2vfs environment.
        """
        if driver == self.drivername:
            self.session_third.send_expect("quit", "# ")
            time.sleep(2)
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
        if driver == self.drivername:
            self.pf_ddriver_flag = 0
        else:
            self.pf_kdriver_flag = 0

    def test_VEB_switching_inter_vfs(self):
        """
        Kernel PF, then create 2VFs. VFs running dpdk testpmd,
        send traffic from VF1 to VF2, check if VF2 can receive
        the packets. Check Inter VF-VF MAC switch.
        """
        self.setup_env(driver='default')
        self.pmdout.start_testpmd(self.cores_vf0, prefix="test1", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.vf1_mac)
        self.dut.send_expect("set fwd txonly", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.pmdout_2.start_testpmd(self.cores_vf1, prefix="test2", ports=[self.sriov_vfs_port[1].pci])
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>", 5)
        self.dut.send_expect("start", "testpmd>", 5)
        time.sleep(2)
    
        self.dut.send_expect("stop", "testpmd>", 5)
        self.session_secondary.send_expect("stop", "testpmd>", 5)

        vf0_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        vf1_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        self.verify(vf0_tx_stats[0] != 0, "no packet was sent by VF0")
        self.verify(vf0_tx_stats[0] * 0.5 < vf1_rx_stats[0], "VF1 failed to receive packets from VF0")

    def test_VEB_switching_inter_vfs_mac_fwd(self):
        """
        Kernel PF, then create 2VFs. VFs running dpdk testpmd, send traffic to
        VF1 with VF1's MAC as packet's DEST MAC, set ether peer address to VF2's MAC.
        Check if VF2 can receive the packets. Check Inter VF-VF MAC switch.
        """
        self.setup_env(driver='default')
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.vf1_mac)
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[1].pci])
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
  
        self.send_packet(self.vf0_mac, self.tester_itf)

        self.dut.send_expect("stop", "testpmd>", 2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)
        out = self.session_secondary.send_expect("show port info 0", "testpmd>")
        vf1_driver = re.findall("Driver\s*name:\s*(\w+)", out)[0]

        vf0_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        vf1_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        if self.kdriver == 'ice':
            vf1_rx_stats[-1] = vf1_rx_stats[-1] + 4
        if self.kdriver == 'i40e':
            if vf1_driver == 'net_iavf':
                vf1_rx_stats[-1] = vf1_rx_stats[-1] + 4
            else:
                vf1_rx_stats[-1] = vf1_rx_stats[-1]
        self.verify(vf0_tx_stats[0] != 0, "no packet was sent by VF0")
        self.verify(vf0_tx_stats == vf1_rx_stats, "VF1 failed to receive packets from VF0")
    
    def test_VEB_switching_inter_vfs_vlan(self):
        """
        Kernel PF, then create 2VFs, assign VF1 with VLAN=1 in, VF2 with
        VLAN=2. VFs are running dpdk testpmd, send traffic to VF1 with VLAN=1,
        then let it forwards to VF2, it should not work since they are not in
        the same VLAN; set VF2 with VLAN=1, then send traffic to VF1 with
        VLAN=1, and VF2 can receive the packets. Check inter VF MAC/VLAN switch.
        """
        self.setup_env(driver='default')
        # the two vfs belongs to different vlans
        self.dut.send_expect("ip link set %s vf 0 vlan 1" % self.pf_interface, "# ", 1)
        self.dut.send_expect("ip link set %s vf 1 vlan 2" % self.pf_interface, "# ", 1)
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.vf1_mac)
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[1].pci])
        self.session_secondary.send_expect("set fwd mac", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)

        self.send_packet(self.vf0_mac, self.tester_itf, "vlan")

        self.dut.send_expect("stop", "testpmd>", 2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)

        vf0_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        vf1_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        self.verify(vf0_tx_stats[0] != 0, "no packet was sent by VF0")
        self.verify((vf0_tx_stats[0] == 1) and (vf1_rx_stats[0] == 0), "VF1 received packets from VF0, the vlan filter doen't work")
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(2)
    
        # the two vfs belongs to the same vlan
        self.dut.send_expect("ip link set %s vf 1 vlan 1" % self.pf_interface, "# ", 1)
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.vf1_mac)
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[1].pci])
        self.session_secondary.send_expect("set fwd mac", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)

        self.send_packet(self.vf0_mac, self.tester_itf, "vlan")

        self.dut.send_expect("stop", "testpmd>", 2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)

        vf0_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        vf1_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        self.verify(vf0_tx_stats[0] != 0, "no packet was sent by VF0")
        self.verify((vf0_tx_stats[0] == 1) and (vf1_rx_stats[0] == 1), "VF1 didn't receive packets from VF0, the vlan filter doen't work")

    def test_VEB_switching_inter_vfs_and_pf(self):
        """
        DPDK PF, then create 2VFs, PF in the host running dpdk testpmd, VFs
        running dpdk testpmd, VF1 send traffic to VF2, check if VF2 can receive
        the packets. send traffic from PF to VF1, ensure PF->VF1; send traffic
        from VF1 to PF, ensure VF1->PF can work.
        """
        # VF->PF
        self.setup_env(driver=self.drivername)
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.pf_pci])
        self.dut.send_expect("set fwd rxonly", "testpmd>")
        self.dut.send_expect("set verbose 1", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.pf_mac_address)
        self.session_secondary.send_expect("mac_addr add 0 %s" % self.vf0_mac, "testpmd>")
        self.session_secondary.send_expect("set fwd txonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        # print the packets which received by pf, this caused most packets missed.
        out = self.dut.get_session_output(timeout=1)
        self.session_secondary.send_expect("stop", "testpmd>", 2)
        self.dut.send_expect("stop", "testpmd>", 2)

        count_pkt = self.count_packet(out, self.vf0_mac)
        vf0_tx_stats = self.veb_get_pmd_stats("second", 0, "tx")
        pf_rx_stats = self.veb_get_pmd_stats("first", 0, "rx")
        self.verify(vf0_tx_stats[0] > 1000, "no packet was sent by VF0")
        self.verify(count_pkt > 100, "no packet was received by PF")
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.send_expect("quit", "# ")
        time.sleep(2)
 
        # PF->VF
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.pf_pci], param="--eth-peer=0,%s" % self.vf0_mac)
        self.dut.send_expect("set fwd txonly", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        
        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[0].pci])
        self.session_secondary.send_expect("mac_addr add 0 %s" % self.vf0_mac, "testpmd>")
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.dut.send_expect("stop", "testpmd>", 2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)

        vf0_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        print(utils.GREEN("The number of UDP packets received by vf is %d." % vf0_rx_stats[0]))
        self.verify(vf0_rx_stats[0] > 100, "no packet was received by VF0")
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.send_expect("quit", "# ")
        time.sleep(2)

        # tester->VF
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.pf_pci])
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)

        self.pmdout_2.start_testpmd("Default", prefix="test2", ports=[self.sriov_vfs_port[0].pci])
        self.session_secondary.send_expect("mac_addr add 0 %s" % self.vf0_mac, "testpmd>")
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)

        vf0_start_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        self.send_packet(self.vf0_mac, self.tester_itf)
        time.sleep(2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)
        self.dut.send_expect("stop", "testpmd>", 2)
        vf0_end_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        self.verify(vf0_end_rx_stats[0] - vf0_start_rx_stats[0] == 1, "no packet was received by VF0")
 
        self.dut.send_expect("start", "testpmd>")
        time.sleep(2)
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        vf0_start_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        pf_start_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        pf_start_rx_stats = self.veb_get_pmd_stats("first", 0, "rx")
        self.send_packet(self.pf_mac_address, self.tester_itf)
        time.sleep(2)
        self.session_secondary.send_expect("stop", "testpmd>", 2)
        self.dut.send_expect("stop", "testpmd>", 2)
        vf0_end_rx_stats = self.veb_get_pmd_stats("second", 0, "rx")
        pf_end_tx_stats = self.veb_get_pmd_stats("first", 0, "tx")
        pf_end_rx_stats = self.veb_get_pmd_stats("first", 0, "rx")
        self.verify(pf_end_tx_stats[0] - pf_start_tx_stats[0] == 1, "no packet was sent by PF")
        self.verify(pf_end_rx_stats[0] - pf_start_rx_stats[0] == 1, "no packet was received by PF")
        self.verify(vf0_end_rx_stats[0] - vf0_start_rx_stats[0] == 0, "VF0 received unexpected packet")
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(2)
        self.dut.send_expect("quit", "# ")
        time.sleep(2)

        # VF1->VF2
        self.pmdout.start_testpmd("Default", prefix="test1", ports=[self.pf_pci])
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.pmdout_2.start_testpmd(self.cores_vf0, prefix="test2", ports=[self.sriov_vfs_port[0].pci], param="--eth-peer=0,%s" % self.vf1_mac)
        self.session_secondary.send_expect("set fwd txonly", "testpmd>")
        self.session_secondary.send_expect("set promisc all off", "testpmd>")
        time.sleep(2)

        self.pmdout_3.start_testpmd(self.cores_vf1, prefix="test3", ports=[self.sriov_vfs_port[1].pci])
        self.session_third.send_expect("mac_addr add 0 %s" % self.vf1_mac, "testpmd>")
        self.session_third.send_expect("set fwd rxonly", "testpmd>")
        self.session_third.send_expect("set promisc all off", "testpmd>")
        self.session_third.send_expect("start", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)

        self.session_secondary.send_expect("stop", "testpmd>", 5)
        self.session_third.send_expect("stop", "testpmd>", 5)
        
        vf0_tx_stats = self.veb_get_pmd_stats("second", 0, "tx")
        vf1_rx_stats = self.veb_get_pmd_stats("third", 0, "rx")
        self.verify(vf0_tx_stats[0] != 0, "no packet was sent by VF0")
        self.verify(vf0_tx_stats[0] * 0.5 < vf1_rx_stats[0], "VF1 failed to receive packets from VF0")

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.pf_kdriver_flag == 1:
            self.destroy_env(driver='default')
        if self.pf_ddriver_flag == 1:
            self.destroy_env(driver=self.drivername)

        self.dut.kill_all()
    
    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)
        # Marvin recommended that all the dut ports should be bound to DPDK.
        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver(driver=self.drivername)
