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
Test vf_interrupt_pmd.
"""

import utils
import string
import time
import re
from pmd_output import PmdOutput
from qemu_kvm import QEMUKvm
from test_case import TestCase


class TestVfInterruptPmd(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(cores)
        self.portmask = utils.create_mask(self.dut_ports)

        self.path = "./examples/l3fwd-power/build/l3fwd-power"

        testport_0 = self.tester.get_local_port(self.dut_ports[0])
        self.rx_intf_0 = self.tester.get_interface(testport_0)
        testport_1 = self.tester.get_local_port(self.dut_ports[1])
        self.rx_intf_1 = self.tester.get_interface(testport_1)

        self.mac_port_0 = self.dut.get_mac_address(self.dut_ports[0])
        self.mac_port_1 = self.dut.get_mac_address(self.dut_ports[1])

        self.dut.virt_exit()

    def build_app(self, use_dut):
        # build sample app
        out = use_dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def generate_sriov_vfport(self, use_driver):
        """
        generate sriov vfs by port
        """
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port_0, 1, driver=use_driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[
            self.used_dut_port_0]['vfs_port']
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port_1, 1, driver=use_driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[
            self.used_dut_port_1]['vfs_port']

    def bind_vfs(self, driver):
        """
        bind vfs to driver
        """
        for port in self.sriov_vfs_port_0:
            port.bind_driver(driver)
        time.sleep(1)
        for port in self.sriov_vfs_port_1:
            port.bind_driver(driver)
        time.sleep(1)

    def setup_vm_env(self):
        """
        Start One VM with one virtio device
        """
        self.dut_testpmd = PmdOutput(self.dut)
        self.dut_testpmd.start_testpmd(
            "Default", "--rxq=4 --txq=4 --port-topology=chained")
        self.dut_testpmd.execute_cmd("start")

        vf0_prop_1 = {'opt_host': self.sriov_vfs_port_0[0].pci}
        vf0_prop_2 = {'opt_host': self.sriov_vfs_port_1[0].pci}
        self.vm0 = QEMUKvm(self.dut, 'vm0', 'vf_interrupt_pmd')
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_1)
        self.vm0.set_vm_device(driver='pci-assign', **vf0_prop_2)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM ENV failed")
            else:
                self.verify(self.vm0_dut.ports_info[
                            0]['intf'] != 'N/A', "Not interface")
        except Exception as e:
            self.destroy_vm_env()
            self.logger.error("Failure for %s" % str(e))

        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        self.vm0_vf1_mac = self.vm0_dut.get_mac_address(1)
        self.vm0_dut.send_expect("systemctl stop NetworkManager", "# ", 60)

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

        if getattr(self, 'used_dut_port_0', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            self.used_dut_port_0 = None

        if getattr(self, 'used_dut_port_1', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            self.used_dut_port_1 = None

        self.env_done = False

    def change_port_conf(self, use_dut, lsc_enable=True, rxq_enable=True):
        """
        change interrupt enable
        """
        sed_cmd_fmt = "/intr_conf.*=.*{/,/\}\,$/c\    .intr_conf = {\\n\\t\\t.lsc = %d,\\n\\t\\t.rxq = %d,\\n\\t},"
        lsc = 1
        rxq = 1
        if lsc_enable:
            lsc = 0
        if rxq_enable:
            rxq = 1
        sed_cmd_str = sed_cmd_fmt % (lsc, rxq)
        out = use_dut.send_expect(
            "sed -i '%s' examples/l3fwd-power/main.c" % sed_cmd_str, "# ", 60)

    def scapy_send_packet(self, mac, testinterface, queuenum=1):
        """
        Send a packet to port
        """
        if queuenum == 1:
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP()/UDP()/Raw(\'X\'*18)], iface="%s")' % (mac, testinterface))
        elif queuenum == 2:
            for dst in range(16):
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], iface="%s")' % (mac, dst, testinterface))
        else:
            for dst in range(256):
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s")/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], iface="%s")' % (mac, dst, testinterface))
        self.tester.scapy_execute()

    def test_vf_VM_uio(self):
        """
        verify VF interrupt pmd in VM with uio
        """
        self.verify(self.drivername in ['igb_uio'], "NOT Support")
        self.generate_sriov_vfport('igb_uio')
        self.bind_vfs('pci-stub')
        self.setup_vm_env()
        self.change_port_conf(self.vm0_dut, lsc_enable=True, rxq_enable=False)
        self.build_app(self.vm0_dut)

        cmd = self.path + \
            " -c f -n %d -- -p 0x3 -P --config='(0,0,1),(1,0,2)'" % (
                self.vm0_dut.get_memory_channels())
        self.vm0_dut.send_expect(cmd, "L3FWD_POWER", 60)
        self.scapy_send_packet(self.vm0_vf0_mac, self.rx_intf_0)
        self.scapy_send_packet(self.vm0_vf1_mac, self.rx_intf_1)
        out = self.vm0_dut.get_session_output(timeout=30)
        self.destroy_vm_env()
        self.dut.send_expect("quit", "# ", 60)
        self.verify(
            "lcore 1 is waked up from rx interrupt on port 0" in out, "lcore 1 not waked up")
        self.verify(
            "lcore 1 sleeps until interrupt triggers" in out, "lcore 1 not sleeps")
        self.verify(
            "lcore 2 is waked up from rx interrupt on port 1" in out, "lcore 2 not waked up")
        self.verify(
            "lcore 2 sleeps until interrupt triggers" in out, "lcore 2 not sleeps")

    def test_vf_host_uio(self):
        """
        verify VF interrupt pmd in Host with uio
        """
        self.verify(self.drivername in ['igb_uio'], "NOT Support")
        self.dut.restore_interfaces()
        self.generate_sriov_vfport('ixgbe')
        self.bind_vfs('igb_uio')
        self.change_port_conf(self.dut, lsc_enable=True, rxq_enable=False)
        self.build_app(self.dut)

        cmd = self.path + " -c %s -n %d -- -p %s -P --config='(0,0,1),(1,0,2)'" % (
            self.coremask, self.dut.get_memory_channels(), self.portmask)
        self.dut.send_expect(cmd, "L3FWD_POWER", 60)
        self.scapy_send_packet(self.mac_port_0, self.rx_intf_0)
        self.scapy_send_packet(self.mac_port_1, self.rx_intf_1)
        out = self.dut.get_session_output(timeout=60)
        self.dut.send_expect("^C", "# ", 60)
        self.verify(
            "lcore 1 is waked up from rx interrupt on port 0" in out, "lcore 1 not waked up")
        self.verify(
            "lcore 1 sleeps until interrupt triggers" in out, "lcore 1 not sleeps")
        self.verify(
            "lcore 2 is waked up from rx interrupt on port 1" in out, "lcore 2 not waked up")
        self.verify(
            "lcore 2 sleeps until interrupt triggers" in out, "lcore 2 not sleeps")

    def test_vf_host_vfio(self):
        """
        verify VF interrupt pmd in Host with vfio
        """
        self.verify(self.drivername in ['vfio-pci'], "NOT Support")
        self.dut.restore_interfaces()
        self.generate_sriov_vfport('ixgbe')
        self.bind_vfs('vfio-pci')
        self.change_port_conf(self.dut, lsc_enable=True, rxq_enable=False)
        self.build_app(self.dut)

        cmd = self.path + " -c %s -n %d -- -p %s -P --config='(0,0,1),(0,1,2)(1,0,3),(1,1,4)'" % (
            self.coremask, self.dut.get_memory_channels(), self.portmask)
        self.dut.send_expect(cmd, "L3FWD_POWER", 60)
        self.scapy_send_packet(self.mac_port_0, self.rx_intf_0, 2)
        self.scapy_send_packet(self.mac_port_1, self.rx_intf_1, 2)
        out = self.dut.get_session_output(timeout=60)
        self.dut.send_expect("^C", "# ", 60)
        print out
        self.verify(
            "lcore 1 is waked up from rx interrupt on port 0" in out, "lcore 1 not waked up")
        self.verify(
            "lcore 1 sleeps until interrupt triggers" in out, "lcore 1 not sleeps")
        self.verify(
            "lcore 2 is waked up from rx interrupt on port 0" in out, "lcore 2 not waked up")
        self.verify(
            "lcore 2 sleeps until interrupt triggers" in out, "lcore 2 not sleeps")
        self.verify(
            "lcore 3 is waked up from rx interrupt on port 1" in out, "lcore 2 not waked up")
        self.verify(
            "lcore 3 sleeps until interrupt triggers" in out, "lcore 2 not sleeps")
        self.verify(
            "lcore 4 is waked up from rx interrupt on port 1" in out, "lcore 2 not waked up")
        self.verify(
            "lcore 4 sleeps until interrupt triggers" in out, "lcore 2 not sleeps")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.virt_exit()
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
