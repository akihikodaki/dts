# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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

import os
import re
import time

import framework.packet as packet
import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


class TestPortControl(TestCase):

    def set_up_all(self):
        """
        Run before each test suite
        """
        # initialize ports topology
        self.vm0 = None
        self.env_done = False
        self.port_id_0 = 0
        self.pkt_count = 1000
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.pf_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.vf_mac = "00:01:23:45:67:89"
        self.txitf = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        self.host_testpmd = PmdOutput(self.dut)
        self.vf_assign_method = 'vfio-pci'
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        port = self.dut.ports_info[0]['port']
        self.pf_default_driver = port.get_nic_driver()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def setup_vm_env(self, driver='default'):
        """
        Create testing environment with 1VF generated from 1PF
        """
        if self.env_done:
            return

        # bind to default driver
        self.bind_nic_driver(self.dut_ports[:1], driver="")
        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]['intf']
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_assign_method)
            time.sleep(1)
            vf_popt = {'opt_host': self.sriov_vfs_port[0].pci}

            # set up VM ENV
            self.vm = VM(self.dut, 'vm0', 'port_control')
            self.vm.set_vm_device(driver=self.vf_assign_method, **vf_popt)
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed!")
            else:
                self.start_vf_pmd(self.vm_dut)

            self.vm_testpmd = PmdOutput(self.vm_dut)

        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.env_done = True

    def destroy_vm_env(self):
        if getattr(self, 'vm', None):
            if getattr(self, 'vm_dut', None):
                self.vm_dut.kill_all()
            self.vm_testpmd = None
            self.vm_dut_ports = None
            # destroy vm0
            self.vm.stop()
            self.dut.virt_exit()
            time.sleep(3)
            self.vm = None

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None
        self.bind_nic_driver(self.dut_ports[:1], driver=self.pf_default_driver)

        self.env_done = False

    def start_vf_pmd(self, terminal):

        drive_info = terminal.send_expect("./usertools/dpdk-devbind.py -s", "#")
        vf_if = re.findall(r"if=(\w+)", drive_info.split("kernel")[1])
        vf_pci = re.findall(r"(\d+.\d+.\d+.\d+)", drive_info.split("kernel")[1])
        terminal.send_expect("ifconfig %s hw ether %s" % (vf_if[1], self.vf_mac), "#")
        terminal.send_expect("ifconfig %s up" % vf_if[1], "#")
        terminal.send_expect("ip addr flush %s " % vf_if[1], "#")
        terminal.send_expect("./usertools/dpdk-devbind.py -b vfio-pci --force %s" % vf_pci[1], "#")
        app_name = terminal.apps_name['test-pmd']
        cmd = app_name + "-n 1 -a %s --vfio-intr=legacy -- -i" % vf_pci[1]
        terminal.send_expect(cmd, "testpmd>", 10)

    def start_testpmd(self, terminal):
        terminal.start_testpmd(ports=[0], socket=self.socket)
        res = terminal.wait_link_status_up('all', timeout=5)
        self.verify(res is True, 'there have port link is down')
        terminal.execute_cmd('set fwd mac')
        terminal.execute_cmd('set promisc all off')

    def start_pmd_port(self, terminal):
        terminal.execute_cmd("port start all")
        terminal.execute_cmd("start")
        time.sleep(5)
        terminal.wait_link_status_up('all', timeout=5)
        ret = terminal.get_port_link_status(self.port_id_0)
        self.verify(ret == "up", "port not up!")

    def stop_pmd_port(self, terminal):
        terminal.execute_cmd("stop")
        terminal.execute_cmd("port stop all")
        ret = terminal.get_port_link_status(self.port_id_0)
        if self.nic.startswith('columbiaville') or (getattr(self, 'vm_testpmd', None) and terminal is self.vm_testpmd):
            self.verify(ret != "", "port status error!")
        else:
            self.verify(ret == "down", "port not down!")


    def reset_pmd_port(self, terminal):
        terminal.execute_cmd("port reset all")
        ret = terminal.get_port_link_status(self.port_id_0)
        if self.nic.startswith('columbiaville') or (getattr(self, 'vm_testpmd', None) and terminal is self.vm_testpmd):
            self.verify(ret != "", "port status error!")
        else:
            self.verify(ret == "down", "port not down!")

    def close_pmd_port(self, terminal):
        terminal.execute_cmd("port close all")
        ret = terminal.execute_cmd("show port info all")
        ret = ret.split('\r')
        self.verify(ret[1] == '', "close all port fail!")

    def calculate_stats(self, start_stats, end_stats):
        ret_stats = {}
        ret_stats['RX-packets'] = int(end_stats['RX-packets']) - int(start_stats['RX-packets'])
        ret_stats['TX-packets'] = int(end_stats['TX-packets']) - int(start_stats['TX-packets'])
        return ret_stats

    def send_and_verify_packets(self, terminal):
        """
        Send packets according to parameters.
        """
        if terminal is self.host_testpmd:
            self.dts_mac = self.pf_mac
        else:
            self.dts_mac = self.vf_mac

        self.pkt = packet.Packet('Ether(dst="%s")/IP()/Raw("x"*40)' % self.dts_mac)

        pf_start_stats = terminal.get_pmd_stats(self.port_id_0)
        self.pkt.send_pkt(crb=self.tester, tx_port=self.txitf, count=self.pkt_count, timeout=30)
        pf_end_stats = terminal.get_pmd_stats(self.port_id_0)
        pf_ret_stats = self.calculate_stats(pf_start_stats, pf_end_stats)

        self.verify(pf_ret_stats['RX-packets'] == self.pkt_count and pf_ret_stats['TX-packets'] == self.pkt_count,
                    "Packets receive and forward fail!")

    def test_pf_start_stop_reset_close(self):
        self.start_testpmd(self.host_testpmd)
        # start port
        self.start_pmd_port(self.host_testpmd)
        self.send_and_verify_packets(self.host_testpmd)
        # stop port and start port
        self.stop_pmd_port(self.host_testpmd)
        self.start_pmd_port(self.host_testpmd)
        self.send_and_verify_packets(self.host_testpmd)
        # reset port
        self.stop_pmd_port(self.host_testpmd)
        self.reset_pmd_port(self.host_testpmd)
        self.start_pmd_port(self.host_testpmd)
        self.send_and_verify_packets(self.host_testpmd)
        # close all port
        self.stop_pmd_port(self.host_testpmd)
        self.close_pmd_port(self.host_testpmd)

    def test_e1000_start_stop_reset_close(self):
        self.setup_vm_env()
        # start port
        self.start_pmd_port(self.vm_testpmd)
        # stop port and start port
        self.stop_pmd_port(self.vm_testpmd)
        self.start_pmd_port(self.vm_testpmd)
        # reset port
        self.stop_pmd_port(self.vm_testpmd)
        self.reset_pmd_port(self.vm_testpmd)
        self.start_pmd_port(self.vm_testpmd)
        # close all port
        self.stop_pmd_port(self.vm_testpmd)
        self.close_pmd_port(self.vm_testpmd)

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.env_done:
            self.vm_testpmd.quit()
            self.destroy_vm_env()
        else:
            self.host_testpmd.quit()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if self.env_done:
            self.destroy_vm_env()
        self.dut.kill_all()
