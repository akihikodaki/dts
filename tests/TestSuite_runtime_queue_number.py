# BSD LICENSE
#
# Copyright(c) 2010-2018 Intel Corporation. All rights reserved.
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

Set the VF max queue number when running the DPDK APP instead of compiling.

"""

import utils
import time
import re

from test_case import TestCase
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from settings import DRIVERS

from packet import Packet


class TestRuntime_Queue_Number(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Run time Queue Number Prerequisites
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit",
                                 "fortville_spirit_single", "fortpark_TLV"], "NIC Unsupported: " + str(self.nic))

        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(localPort)
        self.tester_mac = self.tester.get_mac(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pmdout = PmdOutput(self.dut)
        self.cores = "1S/4C/1T"

        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()
        self.vf_mac = "00:11:22:33:44:55"

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def setup_env(self, vfs_num):
        """
        This is to set up vf environment.
        The pf is bound to dpdk driver.
        """
        # assigned number of VFs
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], vfs_num, self.drivername)
        self.sriov_vfs_port = self.dut.ports_info[self.dut_ports[0]]['vfs_port']

        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)
        except Exception as e:
            self.destroy_env()
            raise Exception(e)

    def destroy_env(self):
        """
        This is to stop testpmd and destroy vf environment.
        """
        self.session_third.send_expect("quit", "# ")
        time.sleep(5)
        self.session_secondary.send_expect("quit", "# ")
        time.sleep(5)
        self.dut.send_expect("quit", "# ")
        time.sleep(5)
        self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])

    def verify_result(self, outstring, max_rxqn, max_txqn, cur_rxqn, cur_txqn):
        """
        verify the packet to the expected queue or be dropped
        """
        self.verify("Max possible RX queues: %d" % max_rxqn in outstring, "the vf RX max queue number is not set successfully")
        self.verify("Max possible TX queues: %d" % max_txqn in outstring, "the vf TX max queue number is not set successfully")
        self.verify("Current number of RX queues: %d" % cur_rxqn in outstring, "the vf RX queue number is not set successfully")
        self.verify("Current number of TX queues: %d" % cur_txqn in outstring, "the vf TX queue number is not set successfully")

    def send_packet(self, itf):
        """
        Sends packets.
        """
        self.tester.scapy_foreground()
        time.sleep(2)
        for i in range(254):
            packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", dst="192.168.0.%d")], iface="%s")' % (
                self.vf_mac, itf, i + 1, i + 2, itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(2)

    def check_packet_queue(self, out):
        """
        get the queue which packet enter.
        """
        self.verify("Queue= 0" in out and "Queue= 1" in out and "Queue= 2" in out and "Queue= 3" in out
                    and "Queue= 4" in out and "Queue= 5" in out and "Queue= 6" in out and "Queue= 7" in out, "there is some queues doesn't work")
        lines = out.split("\r\n")
        reta_line = {}
        queue_flag = 0
        packet_sumnum = 0
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if queue_flag == 1:
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_num = m.group(1)
                packet_sumnum = packet_sumnum + int(packet_num)
                queue_flag = 0
            elif line.strip().startswith("------- Forward"):
                queue_flag = 1
            elif line.strip().startswith("RX-packets"):
                result_scanner = r"RX-packets:\s?([0-9]+)"
                scanner = re.compile(result_scanner, re.DOTALL)
                m = scanner.search(line)
                packet_rec = m.group(1)
            
        self.verify(packet_sumnum == int(packet_rec) == 254, "There are some packets lost.")

    def test_set_valid_vf_max_qn(self):
        """
        try to set all the valid queue number of VF
        """
        self.setup_env(2)
        max_qn = (1, 2, 4, 8, 16)
        # set all the valid queue number per VF
        for i in max_qn:
            # start testpmd on pf 
            self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=%d --file-prefix=test1 --socket-mem 1024,1024" % (self.pf_pci, i))
            # start testpmd on vf0
            self.session_secondary.send_expect("./%s/app/testpmd -c 0xf0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i --rxq=%d --txq=%d" % (self.target, self.sriov_vfs_port[0].pci, i, i), "testpmd>", 120)
            outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
            self.verify_result(outstring, max_rxqn=i, max_txqn=i, cur_rxqn=i, cur_txqn=i)
            self.session_secondary.send_expect("quit", "# ")
            time.sleep(5)
            self.dut.send_expect("quit", "# ")
            time.sleep(5)

    def test_set_invalid_vf_max_qn(self):
        """
        try to set several invalid queue number of VF
        """
        self.setup_env(2)
        max_qn = (0, 6, 17, 32)
        # set several invalid queue number per vf
        for i in max_qn:
            # start testpmd on pf
            out = self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=%d --file-prefix=test1 --socket-mem 1024,1024" % (self.pf_pci, i))
            self.verify("Wrong VF queue number = %d" % i in out, "the setting of invalid vf max queue number failed.")
            # start testpmd on vf0
            self.session_secondary.send_expect("./%s/app/testpmd -c 0xf0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i" % (self.target, self.sriov_vfs_port[0].pci), "testpmd>", 120)
            outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
            self.verify_result(outstring, max_rxqn=4, max_txqn=4, cur_rxqn=1, cur_txqn=1)
            self.session_secondary.send_expect("quit", "# ")
            time.sleep(5)
            self.dut.send_expect("quit", "# ")
            time.sleep(5)

    def test_set_vf_qn(self):
        """
        set vf queue number with testpmd eal parameters.
        """
        self.setup_env(2)
        self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=8 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
        self.session_secondary.send_expect("./%s/app/testpmd -c 0xf0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i --rxq=9 --txq=9" % (self.target, self.sriov_vfs_port[0].pci), "# ", 120)
        self.session_secondary.send_expect("./%s/app/testpmd -c 0xf0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i --rxq=3 --txq=3" % (self.target, self.sriov_vfs_port[0].pci), "testpmd>", 120)
        outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=3, cur_txqn=3)

    def test_set_vf_qn_in_testpmd(self):
        """
        set vf queue number with testpmd command.
        """
        self.setup_env(2)
        self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=8 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
        self.session_secondary.send_expect("./%s/app/testpmd -c 0xf0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i" % (self.target, self.sriov_vfs_port[0].pci), "testpmd>", 120)
        outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=1, cur_txqn=1)
        self.session_secondary.send_expect("port stop all", "testpmd> ")
        self.session_secondary.send_expect("port config all rxq 8", "testpmd> ")
        self.session_secondary.send_expect("port config all txq 8", "testpmd> ")
        self.session_secondary.send_expect("port start all", "testpmd> ")
        outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=8, cur_txqn=8)
        self.session_secondary.send_expect("port stop all", "testpmd> ")
        self.session_secondary.send_expect("port config all rxq 9", "Fail")
        self.session_secondary.send_expect("port config all txq 9", "Fail")
        self.session_secondary.send_expect("port start all", "testpmd> ")
        outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=8, cur_txqn=8)

    def test_set_maxvfs_1pf(self):
        """
        set max queue number when setting max VFs on 1 PF port.
        """
        if (self.nic in ["fortville_eagle", "fortpark_TLV"]):
            self.setup_env(32)
            # failed to set VF max queue num to 16.
            out = self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=16 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
            self.verify("exceeds the hardware maximum 384" in out, "the queue num exceeds the hardware maximum 384")
        elif (self.nic in ["fortville_spirit", "fortville_spirit_single"]):
            self.setup_env(64)
            # failed to set VF max queue num to 16.
            out = self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=16 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
            self.verify("exceeds the hardware maximum 768" in out, "the queue num exceeds the hardware maximum 768")
        self.dut.send_expect("quit", "# ")
        time.sleep(5)
        # succeed in setting VF max queue num to 8
        self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=8 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
        # start testpmd on vf0
        self.session_secondary.send_expect("./%s/app/testpmd -c 0x1e0 -n 4 -w %s --file-prefix=test2 --socket-mem 1024,1024 -- -i --rxq=%d --txq=%d" % (self.target, self.sriov_vfs_port[0].pci, 8, 8), "testpmd>", 120)
        # start testpmd on vf31 with different rxq/txq number
        self.session_third.send_expect("./%s/app/testpmd -c 0x1e00 -n 4 -w %s --file-prefix=test3 --socket-mem 1024,1024 -- -i" % (self.target, self.sriov_vfs_port[31].pci), "testpmd>", 120)
        # check the max queue number and current queue number
        outstring = self.session_secondary.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=8, cur_txqn=8)
        outstring = self.session_third.send_expect("show port info all", "testpmd> ", 120)
        self.verify_result(outstring, max_rxqn=8, max_txqn=8, cur_rxqn=1, cur_txqn=1)
        # modify the queue number of VF1 to max queue number
        self.session_third.send_expect("stop", "testpmd> ", 120)
        self.session_third.send_expect("port stop all", "testpmd> ", 120)
        self.session_third.send_expect("port config all rxq 8", "testpmd> ", 120)
        self.session_third.send_expect("port config all txq 8", "testpmd> ", 120)
        self.session_third.send_expect("port start all", "testpmd> ", 120)

        # check all the queues can be used to distributed packets.
        self.session_secondary.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.session_secondary.send_expect("set verbose 1", "testpmd> ", 120)
        self.session_secondary.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        self.send_packet(self.tester_intf)
        out = self.session_secondary.send_expect("stop", "testpmd> ", 120)
        time.sleep(2)
        self.check_packet_queue(out)

        # check all the queues can be used to distributed packets.
        self.session_third.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.session_third.send_expect("set verbose 1", "testpmd> ", 120)
        self.session_third.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        self.send_packet(self.tester_intf)
        out = self.session_third.send_expect("stop", "testpmd> ", 120)
        time.sleep(2)
        self.check_packet_queue(out)

    def test_vf_bound_to_kerneldriver(self):
        """
        set vf queue number when vf bound to kernel driver.
        """
        self.setup_env(2)
        # bind vf to kernel driver
        for port in self.sriov_vfs_port:
            port.bind_driver(driver="i40evf")
        # set vf max queue number to 8
        self.pmdout.start_testpmd("%s" % self.cores, eal_param="-w %s,queue-num-per-vf=8 --file-prefix=test1 --socket-mem 1024,1024" % self.pf_pci)
        # get the vf interface
        for port in self.sriov_vfs_port:
            vf_intf = port.get_interface_name()
        # list all the vf rx/tx queues of one of the vfs
        outstring = self.session_secondary.send_expect("ethtool -S %s" % vf_intf, "# ", 120)
        self.verify("rx-7.packets" in outstring, "the vf RX max queue number is not set successfully")
        self.verify("tx-7.packets" in outstring, "the vf TX max queue number is not set successfully")
        self.dut.send_expect("quit", "# ")
        for port in self.sriov_vfs_port:
            port.bind_driver(driver="vfio-pci")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_env()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)
