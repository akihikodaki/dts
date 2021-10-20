# BSD LICENSE
#
# Copyright(c) 2010-2016 Intel Corporation. All rights reserved.
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
Test RSS reta (redirection table) update function.
"""
import random
import re
import time

testQueues = [4]
reta_entries = []
reta_lines = []

from framework.pmd_output import PmdOutput

# Use scapy to send packets with different source and dest ip.
# and collect the hash result of five tuple and the queue id.
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVfRss(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def send_packet(self, itf, tran_type, queue, packet_count=16):
        """
        Sends packets.
        """
        global reta_lines
        reta_lines = []
        self.tester.scapy_foreground()
        self.tester.scapy_append('sys.path.append("./")')
        self.tester.scapy_append('from sctp import *')
        self.vm_dut_0.send_expect("start", "testpmd>")
        mac = self.vm0_testpmd.get_port_mac(0)
        # send packet with different source and dest ip
        if tran_type == "ipv4-other":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-frag":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d", frag=1, flags="MF")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-tcp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-udp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-sctp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1025,tag=1)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet = r'sendp([Ether(dst="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1025,dport=1024,tag=1)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "l2_payload":
            for i in range(packet_count):
                packet = r'sendp([Ether(src="00:00:00:00:00:%02d",dst="%s")], iface="%s")' % (
                    i + 1, mac, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)

        elif tran_type == "ipv6-other":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-frag":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=44)/IPv6ExtHdrFragment()], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-tcp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-udp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-sctp":
            for i in range(packet_count):
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1024,dport=1025,tag=1)], iface="%s")' % (
                    mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
                packet = r'sendp([Ether(dst="%s")/IPv6(src="3ffe:2501:200:1fff::%d", dst="3ffe:2501:200:3::%d", nh=132)/SCTP(sport=1025,dport=1024,tag=1)], iface="%s")' % (
                    mac, i + 2, i + 1, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)

        else:
            print("\ntran_type error!\n")

        out = self.vm_dut_0.get_session_output()
        print('*******************************************')
        print(out)
        if not reta_entries:
            # for test_vfpmd_rss, check every queue can receive packet.
            for i in range(queue):
                if self.kdriver == 'ixgbe' and i > 1:
                    self.logger.info('NIC with kernel driver ixgbe only enable queue 0 and queue 1 as default')
                    break
                self.verify('RSS queue={}'.format(hex(i)) in out, 'queue {} did not receive packets'.format(i))
            return
        lines = out.split("\r\n")
        out = ''
        reta_line = {}

        # collect the hash result of five tuple and the queue id
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.startswith(("src=",)):
                for item in line.split("-"):
                    item = item.strip()
                    if item.startswith("RSS hash"):
                        name, value = item.split("=", 1)
                        print(name + "-" + value)
                        reta_line[name.strip()] = value.strip()
                        reta_lines.append(reta_line)
                        reta_line = {}
            elif len(line) != 0 and line.strip().startswith("port "):
                rexp = r"port (\d)/queue (\d{1,2}): received (\d) packets"
                m = re.match(rexp, line.strip())
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)
            elif len(line) != 0 and line.startswith("stop"):
                break
            else:
                pass
        self.verifyResult()

    def verifyResult(self):
        """
        Verify whether or not the result passes.
        """

        global reta_lines
        result = []
        self.result_table_create(
            ['packet index', 'hash value', 'hash index', 'queue id', 'actual queue id', 'pass '])

        i = 0
        self.verify(len(reta_lines) > 0, "The testpmd output has no RSS hash!")
        for tmp_reta_line in reta_lines:
            status = "false"
            if self.kdriver == 'i40e' or self.kdriver == 'ice' or self.nic in ['sageville', 'sagepond']:
                # compute the hash result of five tuple into the 7 LSBs value.
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 64
            else:
                hash_index = int(tmp_reta_line["RSS hash"], 16) % 512

            if reta_entries[hash_index] == int(tmp_reta_line["queue"]):
                status = "true"
                result.insert(i, 0)
            else:
                status = "fail"
                result.insert(i, 1)
            self.result_table_add(
                [i, tmp_reta_line["RSS hash"], hash_index, reta_entries[hash_index], tmp_reta_line["queue"], status])
            i = i + 1

        self.result_table_print()
        reta_lines = []
        self.verify(sum(result) == 0, "the reta update function failed!")

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.verify(
            self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g",
                         "sageville", "sagepond", "fortpark_TLV","fortpark_BASE-T", "carlsville",
                         "columbiaville_25g", "columbiaville_100g"],
            "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Not enough ports available")

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unsupported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

        self.vm0 = None
        self.host_testpmd = None
        self.setup_1pf_1vf_1vm_env_flag = 0
        self.setup_1pf_1vf_1vm_env(driver='')

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def setup_1pf_1vf_1vm_env(self, driver='default'):
        
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']

        try:
            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prot = {'opt_host': self.sriov_vfs_port_0[0].pci}

            if driver == 'igb_uio':
                # start testpmd without the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                self.host_testpmd.start_testpmd("1S/2C/2T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'vf_rss')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prot)

            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

            self.vm0_testpmd = PmdOutput(self.vm_dut_0)

            self.setup_1pf_1vf_1vm_env_flag = 1
        except Exception as e:
            self.destroy_1pf_1vf_1vm_env()
            raise Exception(e)

    def destroy_1pf_1vf_1vm_env(self):
        if getattr(self, 'vm0', None):
            if getattr(self, 'vm0_testpmd', None):
                self.vm0_testpmd.execute_cmd('quit', '# ')
                self.vm0_testpmd = None
            self.vm0_dut_ports = None
            #destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None

        if getattr(self, 'host_testpmd', None):
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None

        if getattr(self, 'used_dut_port_0', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            port = self.dut.ports_info[self.used_dut_port_0]['port']
            port.bind_driver()
            self.used_dut_port_0 = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()

        self.setup_1pf_2vf_1vm_env_flag = 0

    def test_vf_pmdrss_reta(self):
        
        vm0dutPorts = self.vm_dut_0.get_ports('any')
        localPort = self.tester.get_local_port(vm0dutPorts[0])
        itf = self.tester.get_interface(localPort)
        self.vm0_ports_socket = self.vm_dut_0.get_numa_id(vm0dutPorts[0])
        iptypes = {
                   'ipv4-other': 'ip',
                   'ipv4-frag': 'ip',
                   'ipv4-udp': 'udp',
                   'ipv4-tcp': 'tcp',
                   'ipv4-sctp': 'sctp',
                   'ipv6-other': 'ip',
                   'ipv6-frag': 'ip',
                   'ipv6-udp': 'udp',
                   'ipv6-tcp': 'tcp',
                   'ipv6-sctp': 'sctp',
                 #  'l2_payload': 'ether'
                   }

        self.vm_dut_0.kill_all()

        # test with different rss queues
        eal_param = ''
        for queue in testQueues:

            self.vm0_testpmd.start_testpmd(
                "all", "--rxq=%d --txq=%d %s" % (queue, queue, eal_param), socket=self.vm0_ports_socket)

            for iptype, rss_type in list(iptypes.items()):
                self.vm_dut_0.send_expect("set verbose 8", "testpmd> ")
                self.vm_dut_0.send_expect("set fwd rxonly", "testpmd> ")
                self.vm_dut_0.send_expect(
                    "set nbcore %d" % (queue + 1), "testpmd> ")

                # configure the reta with specific mappings.
                if self.kdriver == 'i40e' or self.kdriver == 'ice' or self.nic in ['sageville', 'sagepond']:
                    if self.nic in ['sageville', 'sagepond'] and rss_type == 'sctp':
                        self.logger.info('sageville and sagepond do not support rsstype sctp')
                        continue
                    for i in range(64):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.vm_dut_0.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")
                    self.vm_dut_0.send_expect("port config all rss %s" % rss_type, "testpmd> ")
                else:
                    for i in range(512):
                        reta_entries.insert(i, random.randint(0, queue - 1))
                        self.vm_dut_0.send_expect(
                            "port config 0 rss reta (%d,%d)" % (i, reta_entries[i]), "testpmd> ")
                    self.vm_dut_0.send_expect("port config all rss %s" % rss_type, "testpmd> ")

                self.send_packet(itf, iptype, queue)

            self.vm_dut_0.send_expect("quit", "# ", 30)

    def test_vf_pmdrss(self): 
        vm0dutPorts = self.vm_dut_0.get_ports('any')
        localPort = self.tester.get_local_port(vm0dutPorts[0])
        itf = self.tester.get_interface(localPort)
        self.vm0_ports_socket = self.vm_dut_0.get_numa_id(vm0dutPorts[0])
        iptypes = {
                   'ipv4-other':'ip',
                   'ipv4-udp':'udp',
                   'ipv4-tcp':'tcp',
                   'ipv4-sctp':'sctp',
                   'ipv6-other':'ip',
                   'ipv6-udp':'udp',
                   'ipv6-tcp':'tcp',
                   'ipv6-sctp':'sctp',
                 #  'l2_payload':'ether'
                  }

        self.vm_dut_0.kill_all()

        eal_param = ''
        # test with different rss queues
        for queue in testQueues:

            self.vm0_testpmd.start_testpmd(
                "all", "--rxq=%d --txq=%d %s" % (queue, queue, eal_param), socket=self.vm0_ports_socket)

            for iptype, rsstype in list(iptypes.items()):
                self.vm_dut_0.send_expect("set verbose 8", "testpmd> ")
                self.vm_dut_0.send_expect("set fwd rxonly", "testpmd> ")
                if self.nic in ['sageville', 'sagepond'] and rsstype == 'sctp':
                    self.logger.info('sageville and sagepond do not support rsstype sctp')
                    continue
                out = self.vm_dut_0.send_expect("port config all rss %s" % rsstype, "testpmd> ")
                self.verify("Operation not supported" not in out, "Operation not supported")
                self.vm_dut_0.send_expect(
                    "set nbcore %d" % (queue + 1), "testpmd> ")

                self.send_packet(itf, iptype, queue, 128)
            self.vm_dut_0.send_expect("quit", "# ", 30)

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        #self.vm_dut_0.kill_all()
        self.destroy_1pf_1vf_1vm_env()
