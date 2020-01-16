# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Test Niantic ixgbe_get_vf_queue Include Extra Information function.
"""
import time
import random
import re
import utils

# Use scapy to send packets with different source and dest ip.
# and collect the hash result of five tuple and the queue id.
from test_case import TestCase
from pmd_output import PmdOutput
from virt_common import VM
from qemu_kvm import QEMUKvm

class TestIxgbeVfGetExtraInfo(TestCase):


    def get_packet_bytes(self, queue):
        """
        Get rx queue packets and bytes.
        """
        out = self.vm0_dut.send_expect("ethtool -S %s" % self.vm0_intf0, "#")
        lines = out.split("\r\n")

        for line in lines:
            line = line.strip()
            if ("rx_queue_%s_packets" % queue) in line:
                rev_queue, rev_num = line.split(': ', 1)
        for line in lines:
            line = line.strip()
            if ("rx_queue_%s_bytes" % queue) in line:
                rev_queue, rev_byte = line.split(': ', 1)

        return rev_num, rev_byte

    def send_verify_up(self, prio="", vlan=""):
        """
        Send packets including user priority and verify the result.
        """
        if prio=="1" or prio=="2" or prio=="3":
            rev_num, rev_byte = self.get_packet_bytes(prio)
        else:
            rev_num, rev_byte = self.get_packet_bytes("0")

        self.tester.scapy_foreground()
        self.tester.scapy_append('sys.path.append("./")')
        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        # send packet with different parameters
        packet = r'sendp([Ether(src="%s",dst="%s")/Dot1Q(prio=%s, vlan=%s)/IP()/Raw("x"*20)], iface="%s")' % (
            self.src_mac, self.vm0_vf0_mac, prio, vlan, self.tester_intf)
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        time.sleep(.5)

        if prio=="1" or prio=="2" or prio=="3":
            rev_num_after, rev_byte_after = self.get_packet_bytes(prio)
        else:
            rev_num_after, rev_byte_after = self.get_packet_bytes("0")

        rev_num_added = int(rev_num_after) - int(rev_num)
        rev_byte_added = int(rev_byte_after) - int(rev_byte)

        if vlan == "0":
            self.verify((rev_num_added == 1 and rev_byte_added == 60), "the packet is not sent to the right queue.")
        else:
            self.verify((rev_num_added == 0 and rev_byte_added == 0), "the packet is received.")

    def send_verify_queue(self, ptype="ip"):
        """
        Send different packets, return the received queue.
        """
        rev_num0, rev_byte0 = self.get_packet_bytes("0")
        rev_num1, rev_byte1 = self.get_packet_bytes("1")
        self.tester.scapy_foreground()
        self.tester.scapy_append('sys.path.append("./")')
        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        # send packet with different parameters
        if ptype == "ip":
            packet = r'sendp([Ether(src="%s",dst="%s")/IP()/Raw("x"*20)], count=100, iface="%s")' % (
                self.src_mac, self.vm0_vf0_mac, self.tester_intf)
        elif ptype == "udp":
            packet = r'sendp([Ether(src="%s",dst="%s")/IP(src="192.168.0.1", dst="192.168.0.3")/UDP(sport=23,dport=24)/Raw("x"*20)], count=100, iface="%s")' % (
                self.src_mac, self.vm0_vf0_mac, self.tester_intf)
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()

        rev_num_after0, rev_byte_after0 = self.get_packet_bytes("0")
        rev_num_after1, rev_byte_after1 = self.get_packet_bytes("1")

        rev_num_added0 = int(rev_num_after0) - int(rev_num0)
        rev_byte_added0 = int(rev_byte_after0) - int(rev_byte0)
        rev_num_added1 = int(rev_num_after1) - int(rev_num1)
        rev_byte_added1 = int(rev_byte_after1) - int(rev_byte1)

        if rev_num_added0 == 100 and rev_byte_added0 != 0:
            queue = 0
        elif rev_num_added1 == 100 and rev_byte_added1 != 0:
            queue = 1
        else:
            print(utils.RED("There is no packet received."))

        return queue

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.nic in ["niantic"],
            "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.cores = "1S/8C/1T"

        self.pf_mac = self.dut.get_mac_address(self.dut_ports[0])
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(txport)
        self.tester_mac = self.tester.get_mac(txport)

        self.pf_intf = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.src_mac = '00:02:00:00:00:01'
        self.dut.send_expect('modprobe vfio-pci', '#')

        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 1, driver='igb_uio')
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        for port in self.sriov_vfs_port:
            port.bind_driver('vfio-pci')
        time.sleep(1)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def setup_vm_env(self):
        """
        1pf -> 1vf , vf->vm0
        """
        vf0_prop_1 = {'opt_host': self.sriov_vfs_port[0].pci}
        self.vm0 = QEMUKvm(self.dut, 'vm0', 'ixgbe_vf_get_extra_queue_information')
        self.vm0.set_vm_device(driver='vfio-pci', **vf0_prop_1)
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

        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        self.vm0_intf0 = self.vm0_dut.ports_info[0]['intf']

        self.vm0_dut.restore_interfaces_linux()

    def destroy_vm_env(self):
        """
        destroy vm environment
        """
        if getattr(self, 'vm0', None):
            self.vm0_dut.kill_all()
            self.vm0_dut_ports = None
            self.vm0.stop()
            self.vm0 = None

        self.dut.virt_exit()

    def destroy_vf_env(self):
        """
        destroy vf
        """
        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            self.used_dut_port = None

    def verify_rx_queue(self, num):
        """
        verify the rx queue number
        """
        # pf up + vf up -> vf up
        self.vm0_dut.send_expect("ifconfig %s up" % self.vm0_intf0, "#")
        time.sleep(10)
        out = self.vm0_dut.send_expect("ethtool -S %s" % self.vm0_intf0, "#")
        self.verify(("rx_queue_%d" % (num-1)) in out, "Wrong rx queue number")
        time.sleep(3)

    def test_enable_dcb(self):
        """
        DPDK PF, kernel VF, enable DCB mode with TC=4
        """
        # start testpmd with PF on the host
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd(
            "%s" % self.cores, "--rxq=4 --txq=4 --nb-cores=4", "-w %s" % self.pf_pci)
        self.dut_testpmd.execute_cmd("port stop 0")
        self.dut_testpmd.execute_cmd("port config 0 dcb vt on 4 pfc off")
        self.dut_testpmd.execute_cmd("port start 0")
        time.sleep(5)
        self.setup_vm_env()
        # verify the vf get the extra info.
        self.verify_rx_queue(4)
        # verify the packet enter into the expected queue.
        self.send_verify_up(prio="0",vlan="0")
        self.send_verify_up(prio="1",vlan="0")
        self.send_verify_up(prio="2",vlan="0")
        self.send_verify_up(prio="3",vlan="0")
        self.send_verify_up(prio="4",vlan="0")
        self.send_verify_up(prio="5",vlan="0")
        self.send_verify_up(prio="6",vlan="0")
        self.send_verify_up(prio="7",vlan="0")
        self.send_verify_up(prio="0",vlan="1")

    def test_disable_dcb(self):
        """
        DPDK PF, kernel VF, disable DCB mode
        """
        # start testpmd with PF on the host
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd(
            "%s" % self.cores, "--rxq=2 --txq=2 --nb-cores=2", "-w %s" % self.pf_pci)
        self.dut_testpmd.execute_cmd("start")
        time.sleep(5)
        self.setup_vm_env()
        # verify the vf get the extra info.
        self.verify_rx_queue(2)
        # verify the packet enter into the expected queue.
        rss_queue0 = self.send_verify_queue(ptype="ip")
        rss_queue1 = self.send_verify_queue(ptype="udp")
        self.verify(rss_queue0 != rss_queue1, "Different packets not mapping to different queues.")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut_testpmd.quit()
        self.destroy_vm_env()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.destroy_vf_env()
        self.dut.kill_all()
        time.sleep(2)
