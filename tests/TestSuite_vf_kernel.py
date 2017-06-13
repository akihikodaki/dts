# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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
Test VF kernel
"""

import utils
import time
import datetime
import re
import random
import threading
from test_case import TestCase
from qemu_kvm import QEMUKvm
from pmd_output import PmdOutput
from packet import Packet
import random
from utils import GREEN, RED


class TestVfKernel(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut.send_expect("service network-manager stop", "#", 60)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(self.cores)

        self.dmac = self.dut.get_mac_address(self.dut_ports[0])
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(txport)
        self.tester_mac = self.tester.get_mac(txport)

        self.intf = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pci = self.dut.ports_info[self.dut_ports[0]]['pci'].split(':')

        self.src_logo = '12:34:56:78:90:10'
        self.setup_vm_env()

    def set_up(self):
        """
        Run before each test case.
        """
        self.start_pf_vf()
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "vf link down")

        pass

    def generate_pcap_pkt(self, macs, pktname='flow.pcap'):
        """
        generate pcap pkt
        """
        pkts = ''
        for mac in macs:
            pkt = "Ether(dst='%s',src='%s')/IP()/Raw(load='X'*18)," % (mac,
                                                                       self.src_logo)
            pkts += pkt
        self.tester.send_expect("rm -rf flow.pcap", "#", 10)
        self.tester.scapy_append('wrpcap("flow.pcap", [%s])' % pkts)
        self.tester.scapy_execute()

    def setup_vm_env(self):
        """
        1pf -> 6vfs , 4vf->vm0, 2vf->vm1
        """
        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 6, driver='igb_uio')
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        for port in self.sriov_vfs_port:
            port.bind_driver('pci-stub')
        time.sleep(1)

        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd(
            "Default", "--rxq=4 --txq=4 --port-topology=chained")
        # dpdk-2208
        # since there is no forward engine on DPDK PF to forward or drop packet in packet pool,
        # so finally the pool will be full, then no more packet will be
        # received by VF
        self.dut_testpmd.execute_cmd("start")

        vf0_prop_1 = {'opt_host': self.sriov_vfs_port[0].pci}
        vf0_prop_2 = {'opt_host': self.sriov_vfs_port[1].pci}
        vf0_prop_3 = {'opt_host': self.sriov_vfs_port[2].pci}
        vf0_prop_4 = {'opt_host': self.sriov_vfs_port[3].pci}

        self.vm0 = QEMUKvm(self.dut, 'vm0', 'vf_kernel')
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_1)
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_2)
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_3)
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_4)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM ENV failed")
            else:
                self.verify(self.vm0_dut.ports_info[0][
                            'intf'] != 'N/A', "Not interface")
        except Exception as e:
            self.destroy_vm_env()
            self.logger.error("Failure for %s" % str(e))

        vf1_prop_5 = {'opt_host': self.sriov_vfs_port[4].pci}
        vf1_prop_6 = {'opt_host': self.sriov_vfs_port[5].pci}
        self.vm1 = QEMUKvm(self.dut, 'vm1', 'vf_kernel')
        self.vm1.set_vm_device(driver='pci-assign', **vf1_prop_5)
        self.vm1.set_vm_device(driver='pci-assign', **vf1_prop_6)

        try:
            self.vm1_dut = self.vm1.start()
            if self.vm1_dut is None:
                raise Exception("Set up VM1 ENV failed!")
            else:
                # fortville: PF not up ,vf will not get interface
                self.verify(self.vm1_dut.ports_info[0][
                            'intf'] != 'N/A', "Not interface")
        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.vm0_testpmd = PmdOutput(self.vm0_dut)
        self.vm1_testpmd = PmdOutput(self.vm1_dut)

        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        self.vm0_vf1_mac = self.vm0_dut.get_mac_address(1)
        self.vm0_vf2_mac = self.vm0_dut.get_mac_address(2)
        self.vm0_vf3_mac = self.vm0_dut.get_mac_address(3)

        self.vm1_vf0_mac = self.vm1_dut.get_mac_address(0)
        self.vm1_vf1_mac = self.vm1_dut.get_mac_address(1)

        self.vm0_intf0 = self.vm0_dut.ports_info[0]['intf']
        self.vm0_intf1 = self.vm0_dut.ports_info[1]['intf']

        self.vm1_intf0 = self.vm1_dut.ports_info[0]['intf']

        self.vm0_dut.restore_interfaces_linux()
        self.vm1_dut.restore_interfaces_linux()

        # stop NetworkManager, this if for centos7
        # you may change it when the os no support
        self.vm0_dut.send_expect("systemctl stop NetworkManager", "# ", 60)
        self.vm1_dut.send_expect("systemctl stop NetworkManager", "# ", 60)

        self.dut_testpmd.quit()

    def destroy_vm_env(self):
        """
        destroy vm environment
        """
        if getattr(self, 'vm0', None):
            self.vm0_dut.kill_all()
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'vm1', None):
            self.vm1_dut.kill_all()
            self.vm1_dut_ports = None
            # destroy vm1
            self.vm1.stop()
            self.vm1 = None

        self.dut.virt_exit()

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            self.used_dut_port = None

    def test_link(self):
        """
        verify the link state
        """
        for i in range(5):
            # pf up + vf up -> vf up
            self.vm0_dut.send_expect("ifconfig %s up" % self.vm0_intf0, "#")
            out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
            self.verify("Link detected: yes" in out, "Wrong link status")

            # pf up + vf down -> vf down
            self.vm0_dut.send_expect("ifconfig %s down" % self.vm0_intf0, "#")
            out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
            self.verify("Link detected: no" in out, "Wrong link status")

            self.dut_testpmd.quit()
            # pf down + vf up -> vf down
            self.vm0_dut.send_expect("ifconfig %s up" % self.vm0_intf0, "#")
            out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
            self.verify("Link detected: no" in out, "Wrong link status")

            # pf down + vf down -> vf down
            self.vm0_dut.send_expect("ifconfig %s down" % self.vm0_intf0, "#")
            out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
            self.verify("Link detected: no" in out, "Wrong link status")

            self.start_pf_vf()
            self.verify(self.check_pf_vf_link_status(
                self.vm0_dut, self.vm0_intf0), "vf link down")

    def ping4(self, session, intf, ipv4):
        """
        using seesion , ping -I $intf $ip
        sometimes it failed, so we try 5 times.
        """
        for i in range(5):
            out = session.send_expect(
                "ping -w 5 -c 5 -A -I %s %s" % (intf, ipv4), "# ")
            if '64 bytes from' not in out:
                print GREEN("%s ping %s failed, retry" % (intf, ipv4))
            else:
                return True
        return False

    def test_ping(self):
        """
        verify the ping state
        """
        for i in range(5):
            random_ip = random.randint(2, 249)
            vm0_ip0 = "5.5.5.%d" % random_ip
            vm0_ip1 = "5.5.5.%d" % (random_ip + 1)
            pf_ip = "5.5.5.%d" % (random_ip + 2)

            # down-up link
            for port_info in self.vm0_dut.ports_info:
                vm0_intf = port_info['intf']
                self.verify(self.check_pf_vf_link_status(
                    self.vm0_dut, vm0_intf), "VM0_vf: %s link down" % vm0_intf)

            self.vm0_dut.send_expect(
                "ifconfig %s %s netmask 255.255.255.0" % (self.vm0_intf0, vm0_ip0), "#")
            self.vm0_dut.send_expect(
                "ifconfig %s %s netmask 255.255.255.0" % (self.vm0_intf1, vm0_ip1), "#")
            self.tester.send_expect(
                "ifconfig %s %s netmask 255.255.255.0" % (self.tester_intf, pf_ip), "#")

            # pf ping vm0_vf0
            self.verify(self.ping4(self.tester, self.tester_intf, vm0_ip0),
                        "%s ping %s failed" % (self.tester_intf, vm0_ip0))
            # vm0_vf0 ping pf
            self.verify(self.ping4(self.vm0_dut, self.vm0_intf0, pf_ip),
                        "%s ping %s failed" % (self.vm0_intf0, pf_ip))

            # pf ping vm0_vf1
            self.verify(self.ping4(self.tester, self.tester_intf, vm0_ip1),
                        "%s ping %s failed" % (self.tester_intf, vm0_ip1))
            # vm0_pf1 ping pf
            self.verify(self.ping4(self.vm0_dut, self.vm0_intf1, pf_ip),
                        "%s ping %s failed" % (self.vm0_intf1, pf_ip))

            # clear ip
            self.vm0_dut.send_expect(
                "ifconfig %s 0.0.0.0" % self.vm0_intf0, "#")
            self.vm0_dut.send_expect(
                "ifconfig %s 0.0.0.0" % self.vm0_intf1, "#")
            self.tester.send_expect("ifconfig %s 0.0.0.0" %
                                    self.tester_intf, "#")
            self.dut_testpmd.quit()
            self.start_pf_vf()

    def test_reset(self):
        """
        verify reset the vf1 impact on VF0
        """
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "VM0_VF0 link up failed")
        self.verify(self.check_pf_vf_link_status(
            self.vm1_dut, self.vm1_intf0), "VM1_VF0 link up failed")

        # Link down VF1 in VM1 and check no impact on VF0 status
        self.vm1_dut.send_expect("ifconfig %s down" % self.vm1_intf0, "#")
        out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
        self.verify("Link detected: yes" in out, "Wrong link status")

        # Unload VF1 kernel driver and expect no problem for VF0
        self.vm1_dut.send_expect("rmmod %svf" % self.kdriver, "#")
        out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
        self.verify("Link detected: yes" in out, "Wrong link status")
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac), "Unload VF1 kernel driver impact VF0")

        self.dut_testpmd.quit()
        self.start_pf_vf()
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "vm0_vf0 link down")

        time.sleep(10)
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac), "reset PF testpmd impact VF RX failure")

        self.vm1_dut.send_expect("modprobe %svf" % self.kdriver, "#")
        out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
        self.verify("Link detected: yes" in out, "Wrong link status")
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac), "load VF1 kernel driver impact VF0")

        self.vm1_dut.send_expect("rmmod %svf" % self.kdriver, "#")
        out = self.vm0_dut.send_expect("ethtool %s" % self.vm0_intf0, "#")
        self.verify("Link detected: yes" in out, "Wrong link status")
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac), "Reset VF1 kernel driver impact VF0")

    def test_address(self):
        """
        verify add/delete IP/MAC address
        """
        # ipv4 test:
        random_ip = random.randint(2, 249)
        vm0_ip0 = "5.5.5.%d" % random_ip
        pf_ip = "5.5.5.%d" % (random_ip + 2)
        self.vm0_dut.send_expect(
            "ifconfig %s %s netmask 255.255.255.0" % (self.vm0_intf0, vm0_ip0), "#")
        self.tester.send_expect(
            "ifconfig %s %s netmask 255.255.255.0" % (self.tester_intf, pf_ip), "#")
        # pf ping vm0_vf0
        self.verify(self.ping4(self.tester, self.tester_intf, vm0_ip0),
                    "%s ping %s failed" % (self.tester_intf, vm0_ip0))
        # vm0_vf0 ping pf
        self.verify(self.ping4(self.vm0_dut, self.vm0_intf0, pf_ip),
                    "%s ping %s failed" % (self.vm0_intf0, pf_ip))
        # clear ip
        self.vm0_dut.send_expect("ifconfig %s 0.0.0.0" % self.vm0_intf0, "#")
        self.tester.send_expect("ifconfig %s 0.0.0.0" % self.tester_intf, "#")

        # ipv6 test:
        add_ipv6 = 'efdd::9fc8:6a6d:c232:f1c0'
        self.vm0_dut.send_expect("ifconfig %s add %s" %
                                 (self.vm0_intf0, add_ipv6), "#")
        out = self.vm0_dut.send_expect(
            "ifconfig %s " % self.vm0_intf0, "#", 10)
        self.verify(add_ipv6 in out, "Failed to add ipv6 address")
        self.vm0_dut.send_expect("ifconfig %s del %s" %
                                 (self.vm0_intf0, add_ipv6), "#")
        out = self.vm0_dut.send_expect(
            "ifconfig %s " % self.vm0_intf0, "#", 10)
        self.verify(add_ipv6 not in out, "Failed to del ipv6 address")

        # mac test:
        modify_mac = 'aa:bb:cc:dd:ee:ff'
        self.vm0_dut.send_expect("ifconfig %s hw ether %s" %
                                 (self.vm0_intf0, modify_mac), "#")
        out = self.vm0_dut.send_expect(
            "ifconfig %s " % self.vm0_intf0, "#", 10)
        self.verify(modify_mac in out, "Failed to add mac address")
        time.sleep(5)
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           modify_mac), "modify mac address can't received packet")

    def verify_vm_tcpdump(self, vm_dut, intf, mac, pkt_lens=64, num=1, vlan_id='', param=''):
        vm_dut.send_expect("tcpdump -i %s %s -e ether src %s" %
                           (intf, param, self.tester_mac), "tcpdump", 10)
        self.send_packet(mac, pkt_lens, num, vlan_id)
        out = vm_dut.get_session_output(timeout=10)
        vm_dut.send_expect("^C", "#", 10)
        if self.tester_mac in out:
            return True
        else:
            return False

    def send_packet(self, mac, pkt_lens=64, num=1, vlan_id=''):
        if vlan_id == '':
            pkt = Packet(pkt_type='TCP', pkt_len=pkt_lens)
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.send_pkt(tx_port=self.tester_intf, count=num)
        else:
            pkt = Packet(pkt_type='VLAN_UDP', pkt_len=pkt_lens)
            pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
            pkt.config_layer('vlan', {'vlan': vlan_id})
            pkt.send_pkt(tx_port=self.tester_intf, count=num)

    def test_vlan(self):
        """
        verify add/delete vlan
        """
        vlan_ids = random.randint(1, 4095)
        self.vm0_dut.send_expect("ifconfig %s up" % self.vm0_intf0, "#")
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()

        self.vm0_dut.send_expect("modprobe 8021q", "#")
        out = self.vm0_dut.send_expect("lsmod |grep 8021q", "#")
        self.verify("8021q" in out, "modprobe 8021q failure")

        # Add random vlan id(0~4095) on kernel VF0
        self.vm0_dut.send_expect("vconfig add %s %s" %
                                 (self.vm0_intf0, vlan_ids), "#")
        out = self.vm0_dut.send_expect("ls /proc/net/vlan/ ", "#")
        self.verify("%s.%s" % (self.vm0_intf0, vlan_ids)
                    in out, "take vlan id failure")

        # Send packet from tester to VF MAC with not-matching vlan id, check
        # the packet can't be received at the vlan device
        wrong_vlan = vlan_ids % 4095 + 1
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0, vm0_vf0_mac,
                                           vlan_id='%d' % wrong_vlan) == False, "received wrong vlan packet")

        # Send packet from tester to VF MAC with matching vlan id, check the packet can be received at the vlan device.
        # check_result = self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0, self.vm0_vf0_mac, vlan_id='%d' %vlan_ids)
        check_result = self.verify_vm_tcpdump(
            self.vm0_dut, self.vm0_intf0, vm0_vf0_mac, vlan_id='%d' % vlan_ids)
        self.verify(check_result, "can't received vlan_id=%d packet" % vlan_ids)

        # Delete configured vlan device
        self.vm0_dut.send_expect("vconfig rem %s.%s" %
                                 (self.vm0_intf0, vlan_ids), "#")
        out = self.vm0_dut.send_expect("ls /proc/net/vlan/ ", "#")
        self.verify("%s.%s" % (self.vm0_intf0, vlan_ids)
                    not in out, "vlan error")
        # behavior is diffrent bettwn niantic and fortville ,because of kernel
        # driver
        if self.nic.startswith('fortville'):
            self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                               vm0_vf0_mac, vlan_id='%d' % vlan_ids) == True, "delete vlan error")
        else:
            self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                               vm0_vf0_mac, vlan_id='%d' % vlan_ids) == False, "delete vlan error")

    def test_packet_statistic(self):
        """
        verify packet statistic
        """

        out = self.vm0_dut.send_expect("ethtool -S %s" % self.vm0_intf0, "#")
        rx_packets_before = re.findall("\s*rx.*packets:\s*(\d*)", out)
        nb_rx_pkts_before = 0
        for i in range(len(rx_packets_before)):
            nb_rx_pkts_before += int(rx_packets_before[i])

        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac, num=10), "VM reveive packet failed")

        out = self.vm0_dut.send_expect("ethtool -S %s" % self.vm0_intf0, "#")
        rx_packets_after = re.findall("\s*rx.*packets:\s*(\d*)", out)
        nb_rx_pkts_after = 0
        for i in range(len(rx_packets_after)):
            nb_rx_pkts_after += int(rx_packets_after[i])

        self.verify(nb_rx_pkts_after == 10 + nb_rx_pkts_before,
                    "rx_packets calculate error")

    def start_pf_vf(self):
        """
        know issue DPDK-2208. dpdk-2849
        """
        self.dut_testpmd.start_testpmd(
            "Default", "--rxq=4 --txq=4 --port-topology=chained")
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd("start")
        time.sleep(10)
        self.vm0_dut.send_expect("rmmod %svf" % self.kdriver, "#")
        self.vm1_dut.send_expect("rmmod %svf" % self.kdriver, "#")
        self.vm0_dut.send_expect("modprobe %svf" % self.kdriver, "#")
        self.vm1_dut.send_expect("modprobe %svf" % self.kdriver, "#")

    def check_pf_vf_link_status(self, session, intf):
        """
        sometimes pf/vf will up abnormal, retry 5 times
        """
        for i in range(5):
            # down-up get new mac form pf.
            # because  dpdk pf will give an random mac when dpdk pf restart.
            session.send_expect("ifconfig %s down" % intf, "#")
            out = session.send_expect("ifconfig %s up" % intf, "#")
            # SIOCSIFFLAGS: Network is down
            # i think the pf link abnormal
            if "Network is down" in out:
                print GREEN(out)
                print GREEN("Try again")
                self.dut_testpmd.quit()
                self.vm0_dut.restore_interfaces_linux()
                self.start_pf_vf()
            else:
                out = session.send_expect("ethtool %s" % intf, "#")
                if "Link detected: yes" in out:
                    return True
            time.sleep(1)
        return False

    def test_mtu(self):
        """
        verify mtu change
        HW limitation on 82599, need add '--max-pkt-len=<length>' on testpmd to set mtu value, 
        all the VFs and PF share same MTU, the largest one take effect.
        """
        vm0_intf0 = self.vm0_dut.ports_info[0]['intf']
        vm0_intf1 = self.vm0_dut.ports_info[1]['intf']
        self.vm0_dut.send_expect("ifconfig %s up" % self.vm0_intf0, "#")
        out = self.vm0_dut.send_expect("ifconfig %s" % self.vm0_intf0, "#")
        self.verify('mtu 1500' in out, "modify MTU failed")
        self.tester.send_expect("ifconfig %s mtu 3000" % self.tester_intf, "#")

        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set promisc all off')
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')

        # Send one packet with length as 2000 with DPDK PF MAC as DEST MAC,
        # check that DPDK PF can't receive packet
        self.send_packet(self.dmac, pkt_lens=2000)
        out = self.dut.get_session_output(timeout=10)
        self.verify(self.dmac.upper() not in out, "PF receive error packet")

        # send one packet with length as 2000 with kernel VF MAC as DEST MAC,
        # check that Kernel VF can't receive packet
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac, pkt_lens=2000) == False, "kernel VF receive error packet")

        # Change DPDK PF mtu as 3000,check no confusion/crash on kernel VF
        if self.nic.startswith('niantic'):
            self.dut_testpmd.quit()
            self.dut_testpmd.start_testpmd(
                "Default", "--rxq=4 --txq=4 --port-topology=chained --max-pkt-len=3000")
        elif self.nic.startswith('fortville'):
            self.dut_testpmd.execute_cmd('stop')
            self.dut_testpmd.execute_cmd('port stop all')
            self.dut_testpmd.execute_cmd('port config mtu 0 3000')
            self.dut_testpmd.execute_cmd('port start all')

        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set promisc all off')
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')

        # sleep 5s to wait vf up , because of pf down-up
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "VM0_VF0 link down")

        # clear output
        self.dut.get_session_output(timeout=10)

        # send one packet with length as 2000 with DPDK PF MAC as DEST MAC ,
        # check that DPDK PF can receive packet
        self.send_packet(self.dmac, pkt_lens=2000)
        out = self.dut.get_session_output(timeout=10)
        self.verify(self.dmac.upper() in out, "PF can't receive packet")

        # Change kernel VF mtu as 3000,check no confusion/crash on DPDK PF
        if self.nic.startswith('fortville'):
            self.vm0_dut.send_expect(
                "ifconfig %s mtu 3000" % self.vm0_intf0, "#")

        # send one packet with length as 2000 with kernel VF MAC as DEST MAC,
        # check Kernel VF can receive packet
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac, pkt_lens=2000), "VF can't receive packet")

        if self.nic.startswith('niantic'):
            self.dut_testpmd.quit()
            self.dut_testpmd.start_testpmd(
                "Default", "--rxq=4 --txq=4 --port-topology=chained")
        elif self.nic.startswith('fortville'):
            self.dut_testpmd.execute_cmd('stop')
            self.dut_testpmd.execute_cmd('port stop all')
            self.dut_testpmd.execute_cmd('port config mtu 0 1500')
            self.dut_testpmd.execute_cmd('port start all')

        self.dut_testpmd.execute_cmd('start')

        self.vm0_dut.send_expect("ifconfig %s mtu 1500" %
                                 self.vm0_intf0, "#", 10)

    def test_promisc_mode(self):
        """
        verify Enable/disable promisc mode
        """
        self.verify(self.nic not in ["niantic"],
                    "%s NIC not support" % self.nic)
        wrong_mac = '01:02:03:04:05:06'
        # Set up kernel VF tcpdump with -p parameter, which means disable promisc
        # Start DPDK PF, enable promisc mode, set rxonly forwarding
        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set promisc all on')
        self.dut_testpmd.execute_cmd('start')
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "VM0_VF0 link down")
        self.dut.get_session_output()

        # Send packet from tester to VF with correct DST MAC, check the packet
        # can be received by kernel VF
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(
            self.vm0_dut, self.vm0_intf0, vm0_vf0_mac), "VM reveive packet failed")
        # Send packet from tester to PF with correct DST MAC, check the packet
        # can be received by DPDK PF
        self.send_packet(self.dmac)
        out = self.dut.get_session_output()
        self.verify(self.tester_mac.upper() in out, "PF reveive packet failed")

        # Send packet from tester with random DST MAC, check the packet can be
        # received by DPDK PF and kernel VF
        self.verify(self.verify_vm_tcpdump(
            self.vm0_dut, self.vm0_intf0, wrong_mac), "VM reveive misc packet failed")
        self.send_packet(wrong_mac)
        out = self.dut.get_session_output()
        self.verify(self.tester_mac.upper() in out,
                    "PF reveive misc packet failed")

        # Send packet from tester to VF with correct DST MAC, check the packet
        # can be received by kernel VF
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(
            self.vm0_dut, self.vm0_intf0, vm0_vf0_mac), "VM reveive packet failed")
        # Send packet from tester to PF with correct DST MAC, check the packet
        # can be received by DPDK PF
        self.send_packet(self.dmac)
        out = self.dut.get_session_output()
        self.verify(self.tester_mac.upper() in out, "PF reveive packet failed")

        # Disable DPDK PF promisc mode
        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set promisc all off')
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('set verbose 1')
        self.dut_testpmd.execute_cmd('start')
        self.dut.get_session_output()

        # Set up kernel VF tcpdump with -p parameter, which means disable promisc mode
        # Send packet from tester with random DST MAC, check the packet can't
        # be received by DPDK PF and kernel VF
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           wrong_mac, param='-p') == False, "VM should not reveive misc packet")
        self.send_packet(wrong_mac)
        out = self.dut.get_session_output()
        self.verify(wrong_mac not in out, "PF should not receive misc packet")

        # Send packet from tester to VF with correct DST MAC, check the packet
        # can be received by kernel VF
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        self.verify(self.verify_vm_tcpdump(self.vm0_dut, self.vm0_intf0,
                                           vm0_vf0_mac, param='-p'), "VM reveive packet failed")
        # Send packet from tester to PF with correct DST MAC, check the packet
        # can be received by DPDK PF
        self.send_packet(self.dmac)
        out = self.dut.get_session_output()
        self.verify(self.tester_mac.upper() in out, "PF reveive packet failed")

    def test_rss(self):
        """
        verify kernel VF each queue can receive packets
        """
        self.verify(self.nic not in ["niantic"],
                    "%s NIC not support tcpid " % self.nic)

        # Verify kernel VF RSS using ethtool -"l" (lower case L) <devx> that the
        # default RSS setting is equal to the number of CPUs in the system and
        # that the maximum number of RSS queues displayed is correct for the
        # DUT
        self.verify(self.check_pf_vf_link_status(
            self.vm0_dut, self.vm0_intf0), "VM0_VF0 link down")

        cpus = self.vm0_dut.send_expect(
            "cat /proc/cpuinfo| grep 'processor'| wc -l", "#")
        out = self.vm0_dut.send_expect(
            "ethtool -l %s" % self.vm0_intf0, "#", 10)
        combined = re.findall("Combined:\s*(\d*)", out)
        self.verify(cpus == combined[0], "the queues count error")

        # Run "ethtool -S <devx> | grep rx_bytes | column" to see the current
        # queue count and verify that it is correct to step 1
        out = self.vm0_dut.send_expect(
            "ethtool -S %s |grep rx-.*bytes" % self.vm0_intf0, "#")
        rx_bytes_before = re.findall("rx-.*bytes:\s*(\d*)", out)
        self.verify(len(rx_bytes_before) == int(
            combined[0]), "the queues count error")

        # Send multi-threaded traffics to the DUT with a number of threads
        # Check kernel VF each queue can receive packets
        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        for i in xrange(5):
            mythread = threading.Thread(target=self.send_packet(vm0_vf0_mac))
            mythread.start()

        out = self.vm0_dut.send_expect(
            "ethtool -S %s |grep rx-*bytes" % self.vm0_intf0, "#")
        rx_bytes_after = re.findall("rx-*.bytes:\s*(\d*)", out)
        for i in range(len(rx_bytes_after)):
            self.verify(rx_bytes_after[i] > rx_bytes_before[
                        i], "NOT each queue receive packets")

    def test_dpf_kvf_dvf(self):
        """
        Check DPDK VF0 and kernel VF1 don't impact each other and no performance drop
        """
        self.vm0_dut.send_expect("ifconfig %s up " % self.vm0_intf0, "#")
        self.vm0_dut.send_expect("ifconfig %s up " % self.vm0_intf1, "#")
        self.vm0_dut.ports_info[1]['port'].bind_driver('igb_uio')

        self.vm0_testpmd.start_testpmd("Default")
        self.vm0_testpmd.execute_cmd('set promisc all on')
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('start')

        vm0_vf0_mac = self.vm0_dut.ports_info[0]['port'].get_mac_addr()
        vm0_vf1_mac = self.vm0_testpmd.get_port_mac(0)

        macs = [vm0_vf0_mac, vm0_vf1_mac]
        self.generate_pcap_pkt(macs)

        vm0_newvmsession = self.vm0_dut.new_session()
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=.5)
        while(1):
            date_now = datetime.datetime.now()
            vm0_newvmsession.send_expect(
                "tcpdump -i %s -e ether src %s " % (self.vm0_intf0, self.src_logo), "tcpdump")
            self.send_packets()

            out = self.vm0_dut.get_session_output(timeout=20)
            self.verify(self.src_logo in out,
                        "VM PF Confiscated to the specified package")

            put = vm0_newvmsession.send_expect("^C", "#", 10)
            rx_packet = re.findall("(\d*) packe.* captured", put)
            if rx_packet[0] == '1':
                self.verify(
                    rx_packet[0] == '1', "VM KF Confiscated to the specified package\n'%s'" % put)

            if date_now >= date_new:
                break

    def send_packets(self):
        self.tester.scapy_foreground()
        self.tester.scapy_append("pkts=rdpcap('flow.pcap')")
        self.tester.scapy_append("sendp(pkts, iface='%s')" % self.tester_intf)
        self.tester.scapy_execute()

    def reboot_vm1(self):
        """
        reboot vm1.
        """
        self.vm1.stop()
        vf1_prop_5 = {'opt_host': self.sriov_vfs_port[4].pci}
        vf1_prop_6 = {'opt_host': self.sriov_vfs_port[5].pci}
        self.vm1 = QEMUKvm(self.dut, 'vm1', 'vf_kernel')
        self.vm1.set_vm_device(driver='pci-assign', **vf1_prop_5)
        self.vm1.set_vm_device(driver='pci-assign', **vf1_prop_6)

        try:
            self.vm1_dut = self.vm1.start()
            if self.vm1_dut is None:
                raise Exception("Set up VM1 ENV failed!")
            else:
                self.verify(self.vm1_dut.ports_info[0][
                            'intf'] != 'N/A', "Not interface")
        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

    def test_zdpf_2kvf_2dvf_2vm(self):
        """
        Check DPDK PF 2kernel VFs 2DPDK VFs 2VMs link change impact on other VFs
        DPDK PF + 2kernel VFs + 2DPDK VFs + 2VMs
        Host one DPDK PF and create 6 VFs, pass through VF0, VF1, VF2 and VF3 to VM0, pass through VF4, VF5 to VM1, power on VM0 and VM1.
        Load host DPDK driver, VM DPDK driver and kernel driver.
        """
        for port_info in self.vm0_dut.ports_info:
            vm0_intf = port_info['intf']
            self.verify(self.check_pf_vf_link_status(
                self.vm0_dut, vm0_intf), "VM0_vf: %s link down" % vm0_intf)

        for port_info in self.vm1_dut.ports_info:
            vm1_intf = port_info['intf']
            self.verify(self.check_pf_vf_link_status(
                self.vm1_dut, vm1_intf), "VM1_vf: %s link down" % vm1_intf)

        # Bind kernel VF0, VF1 to igb_uio in VM0, bind kernel VF4 to igb_uio in
        # VM1
        self.vm0_dut.ports_info[0]['port'].bind_driver('igb_uio')
        self.vm0_dut.ports_info[1]['port'].bind_driver('igb_uio')
        self.vm1_dut.ports_info[0]['port'].bind_driver('igb_uio')

        # Start DPDK VF0, VF1 in VM0 and VF4 in VM1, enable promisc mode
        self.vm0_testpmd.start_testpmd("Default")
        self.vm0_testpmd.execute_cmd('set promisc all on')
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('start')

        self.vm1_testpmd.start_testpmd("Default")
        self.vm1_testpmd.execute_cmd('set promisc all on')
        self.vm1_testpmd.execute_cmd('set fwd rxonly')
        self.vm1_testpmd.execute_cmd('set verbose 1')
        self.vm1_testpmd.execute_cmd('start')

        vm0_vf0_mac = self.vm0_testpmd.get_port_mac(0)
        vm0_vf1_mac = self.vm0_testpmd.get_port_mac(1)
        vm0_vf2_mac = self.vm0_dut.ports_info[2]['port'].get_mac_addr()
        vm0_vf3_mac = self.vm0_dut.ports_info[3]['port'].get_mac_addr()
        vm1_vf0_mac = self.vm1_testpmd.get_port_mac(0)
        vm1_vf1_mac = self.vm1_dut.ports_info[1]['port'].get_mac_addr()
        pf0_mac = self.dut_testpmd.get_port_mac(0)
        pf1_mac = self.dut_testpmd.get_port_mac(1)

        macs = [vm0_vf0_mac, vm0_vf1_mac, vm0_vf2_mac, vm0_vf3_mac,
                vm1_vf0_mac, vm1_vf1_mac, pf0_mac, pf1_mac]
        self.generate_pcap_pkt(macs)

        self.send_packets()

        vm0_vf2_newvmsession = self.vm0_dut.new_session()
        vm0_vf3_newvmsession = self.vm0_dut.new_session()
        vm1_newvmsession = self.vm1_dut.new_session()

        # Set up kernel VF2, VF3 in VM0 and VF5 in VM1  tcpdump without -p
        # parameter on promisc mode
        vm0_vf2_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[2]['intf'], self.src_logo), "tcpdump", 10)
        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump", 10)
        vm1_newvmsession.send_expect("tcpdump -i %s -e -p ether src %s" % (
            self.vm0_dut.ports_info[1]['intf'], self.src_logo), "tcpdump", 10)

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "VM0 PF Confiscated to the specified package")

        vm0_vf2_out = vm0_vf2_newvmsession.send_expect("^C", "#")
        vm0_vf2_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm0_vf2_out_rx_packet[
                    0] == '1', "vm0 vf2 Confiscated to the specified package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#")
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "vm0 vf3 Confiscated to the specified package")

        out = self.vm1_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "VM1 PF Confiscated to the specified package")

        vm1_vf1_out = vm1_newvmsession.send_expect("^C", "#")
        vm1_vf1_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm1_vf1_out_rx_packet[
                    0] == '1', "vm1 vf1 Confiscated to the specified package")

        # Link down DPDK VF0 and expect no impact on other VFs
        self.vm0_testpmd.quit()
        eal_param = '-b %(vf0)s' % ({'vf0': self.vm0_dut.ports_info[0]['pci']})
        self.vm0_testpmd.start_testpmd("Default", eal_param=eal_param)
        self.vm0_testpmd.execute_cmd('set promisc all on')
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('start')

        vm0_vf2_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[2]['intf'], self.src_logo), "tcpdump", 10)
        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump", 10)
        vm1_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[1]['intf'], self.src_logo), "tcpdump", 10)

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "link down impact VM0 PF receive package")

        vm0_vf2_out = vm0_vf2_newvmsession.send_expect("^C", "#")
        vm0_vf2_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm0_vf2_out_rx_packet[
                    0] == '1', "link down impact vm0 vf2 receive package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#")
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "link down impact vm0 vf3 receive package")

        out = self.vm1_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "link down impact VM1 PF receive package")

        vm1_vf1_out = vm1_newvmsession.send_expect("^C", "#")
        vm1_vf1_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm1_vf1_out_rx_packet[
                    0] == '1', "link down impact vm1 vf1 receive package")

        # Link down kernel VF2 and expect no impact on other VFs
        vm0_vf2_newvmsession.send_expect(
            "ifconfig %s down" % self.vm0_dut.ports_info[2]['intf'], "#", 10)

        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump", 10)
        vm1_newvmsession.send_expect("tcpdump -i -p %s -e ether src %s" % (
            self.vm0_dut.ports_info[1]['intf'], self.src_logo), "tcpdump", 10)

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "link down kernel vf2 impact VM0 PF receive package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#")
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "link down kernel vf2 impact vm0 vf3 receive package")

        out = self.vm1_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "link down kernel vf2 impact VM1 PF receive package")

        vm1_vf1_out = vm1_newvmsession.send_expect("^C", "#")
        vm1_vf1_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm1_vf1_out_rx_packet[
                    0] == '1', "link down kernel vf2 impact vm1 vf1 receive package")

        vm0_vf2_newvmsession.send_expect(
            "ifconfig %s up" % self.vm0_dut.ports_info[2]['intf'], "#")

        # Quit VF4 DPDK testpmd and expect no impact on other VFs
        self.vm1_testpmd.quit()

        vm0_vf2_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[2]['intf'], self.src_logo), "tcpdump", 10)
        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump", 10)
        vm1_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[1]['intf'], self.src_logo), "tcpdump", 10)

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "quit vf4 DPDK testpmd impact VM0 PF receive package")

        vm0_vf2_out = vm0_vf2_newvmsession.send_expect("^C", "#")
        vm0_vf2_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm0_vf2_out_rx_packet[
                    0] == '1', "quit vf4 DPDK testpmd impact vm0 vf2 receive package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#")
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "quit vf4 DPDK testpmd impact vm0 vf3 receive package")

        vm1_vf1_out = vm1_newvmsession.send_expect("^C", "#")
        vm1_vf1_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm1_vf1_out_rx_packet[
                    0] == '1', "quit vf4 DPDK testpmd impact vm1 vf1 receive package")

        self.vm1_testpmd.start_testpmd("Default")
        self.vm1_testpmd.execute_cmd('set promisc all on')
        self.vm1_testpmd.execute_cmd('set fwd rxonly')
        self.vm1_testpmd.execute_cmd('set verbose 1')
        self.vm1_testpmd.execute_cmd('start')

        # Unload VF5 kernel driver and expect no impact on other VFs
        vm1_newvmsession.send_expect(
            "./usertools/dpdk-devbind.py -b pci-stub %s" % (self.vm1_dut.ports_info[1]['pci']), "#")

        vm0_vf2_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[2]['intf'], self.src_logo), "tcpdump")
        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump")

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "unload vf5 kernel driver impact VM0 PF receive package")

        vm0_vf2_out = vm0_vf2_newvmsession.send_expect("^C", "#")
        vm0_vf2_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm0_vf2_out_rx_packet[
                    0] == '1', "unload vf5 kernel driver impact vm0 vf2 receive package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#", 10)
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "unload vf5 kernel driver impact vm0 vf3 receive package")

        out = self.vm1_dut.get_session_output(timeout=20)
        self.verify(self.src_logo in out,
                    "unload vf5 kernel driver impact VM1 PF receive package")

        # Reboot VM1 and expect no impact on VFs of VM0
        self.vm1_dut.send_expect("quit", "#")
        self.reboot_vm1()

        vm0_vf2_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[2]['intf'], self.src_logo), "tcpdump")
        vm0_vf3_newvmsession.send_expect("tcpdump -i %s -p -e ether src %s" % (
            self.vm0_dut.ports_info[3]['intf'], self.src_logo), "tcpdump")

        self.send_packets()

        out = self.vm0_dut.get_session_output()
        self.verify(self.src_logo in out,
                    "reboot vm1 impact VM0 PF receive package")

        vm0_vf2_out = vm0_vf2_newvmsession.send_expect("^C", "#")
        vm0_vf2_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf2_out)
        self.verify(vm0_vf2_out_rx_packet[
                    0] == '1', "reboot vm1 impact vm0 vf2 receive package")

        vm0_vf3_out = vm0_vf3_newvmsession.send_expect("^C", "#")
        vm0_vf3_out_rx_packet = re.findall(
            "(\d*) packe.* captured", vm0_vf3_out)
        self.verify(vm0_vf3_out_rx_packet[
                    0] == '1', "reboot vm1 impact vm0 vf3 receive package")

    def test_stress(self):
        """
        Load kernel driver stress
        """
        for i in xrange(100):
            out = self.vm0_dut.send_expect("rmmod %svf" % self.kdriver, "#")
            self.verify('error' not in out,
                        "stress error for rmmod %svf:%s" % (self.kdriver, out))
            out = self.vm0_dut.send_expect("modprobe %svf" % self.kdriver, "#")
            self.verify('error' not in out, "stress error for modprobe %svf:%s" % (
                self.kdriver, out))

    def tear_down(self):
        """
        Run after each test case.
        """
        self.vm0_testpmd.quit()
        self.vm0_dut.restore_interfaces_linux()
        if getattr(self, 'vm0_newvmsession', None):
            self.vm0_dut.close_session(vm0_newvmsession)
        if getattr(self, 'vm0_vf2_newvmsession', None):
            self.vm0_dut.close_session(vm0_vf2_newvmsession)
        if getattr(self, 'vm0_vf3_newvmsession', None):
            self.vm0_dut.close_session(vm0_vf3_newvmsession)
        self.dut_testpmd.quit()

        # Sometime test failed ,we still need clear ip.
        self.vm0_dut.send_expect(
            "ifconfig %s 0.0.0.0" % self.vm0_intf0, "#")
        self.vm0_dut.send_expect(
            "ifconfig %s 0.0.0.0" % self.vm0_intf1, "#")
        self.tester.send_expect("ifconfig %s 0.0.0.0" %
                                self.tester_intf, "#")


    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.destroy_vm_env()
        self.dut.kill_all()
        time.sleep(2)
