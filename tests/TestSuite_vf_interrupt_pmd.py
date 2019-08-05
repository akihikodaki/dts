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
import time
import re

from test_case import TestCase
from packet import Packet

class TestVfInterruptPmd(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")

        cores = "1S/4C/1T"
        self.number_of_ports = 1

        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        ports = []
        for port in range(self.number_of_ports):
            ports.append(self.dut_ports[port])

        self.core_list = self.dut.get_core_list(cores, socket=self.ports_socket)
        self.core_user = self.core_list[0]

        self.port_mask = utils.create_mask(ports)
        self.core_mask_user = utils.create_mask(self.core_list[0:1])

        testport_0 = self.tester.get_local_port(self.dut_ports[0])
        self.rx_intf_0 = self.tester.get_interface(testport_0)
        self.tester_mac = self.tester.get_mac(testport_0)

        self.mac_port_0 = self.dut.get_mac_address(self.dut_ports[0])

        self.prepare_l3fwd_power()
        self.dut.send_expect('modprobe vfio-pci', '#')

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.restore_interfaces()

    def prepare_l3fwd_power(self):
        """
        Change the DPDK source code and recompile
        """
        self.dut.send_expect(
                "sed -i -e '/DEV_RX_OFFLOAD_CHECKSUM,/d' ./examples/l3fwd-power/main.c", "#", 10)

        out = self.dut.send_expect("make -C examples/l3fwd-power", "#")
        self.verify("Error" not in out, "compilation error")

    def send_and_verify(self, mac, testinterface):
        """
        Send a packet and verify
        """
        pkt = Packet(pkt_type='UDP')
        pkt.config_layer('ether', {'dst': mac, 'src': self.tester_mac})
        pkt.send_pkt(tx_port=testinterface)

        out1 = self.dut.get_session_output(timeout=2)
        self.verify(
                "lcore %s is waked up from rx interrupt on port 0" % self.core_user in out1, "Wake up failed")
        self.verify(
                "lcore %s sleeps until interrupt triggers" % self.core_user in out1, "lcore 1 not sleeps")

    def set_NIC_link(self):
        """
        When starting l3fwd-power on vf, ensure that PF link is up
        """
        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]['intf']

        self.dut.send_expect("ifconfig %s up" % self.host_intf, '#', 3)

    def begin_l3fwd_power(self):
        """
        begin l3fwd-power
        """
        cmd_vhost_net = "./examples/l3fwd-power/build/l3fwd-power -n %d -c %s" % (
                self.dut.get_memory_channels(), self.core_mask_user) + \
                        " -- -P -p 1 --config='(0,0,%s)'" % self.core_user
        try:
            self.logger.info("Launch l3fwd_sample sample:")
            self.out = self.dut.send_expect(cmd_vhost_net, "L3FWD_POWER", 60)
            if "Error" in self.out:
                raise Exception("Launch l3fwd-power sample failed")
            else:
                self.logger.info("Launch l3fwd-power sample finished")
        except Exception as e:
            self.logger.error("ERROR: Failed to launch  l3fwd-power sample: %s" % str(e))

    def test_nic_interrupt_VF_vfio_pci(self, driver='default'):
        """
        Check Interrupt for VF with vfio driver
        """
        self.set_NIC_link()

        # generate VF and bind to vfio-pci
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']

        for port in self.sriov_vfs_port_0:
            port.bind_driver('vfio-pci')

        self.begin_l3fwd_power()
        pattern = re.compile(r"(([A-Fa-f0-9]{2}:){5}[A-Fa-f0-9]{2})")
        self.vf_mac = pattern.search(self.out).group()

        self.send_and_verify(self.vf_mac, self.rx_intf_0)

    def test_nic_interrupt_PF_vfio_pci(self):
        """
        Check Interrupt for PF with vfio-pci driver
        """
        self.dut.ports_info[0]['port'].bind_driver(driver='vfio-pci')

        self.begin_l3fwd_power()

        self.send_and_verify(self.mac_port_0, self.rx_intf_0)

    def test_nic_interrupt_PF_igb_uio(self):
        """
        Check Interrupt for PF with igb_uio driver
        """
        self.dut.ports_info[0]['port'].bind_driver(driver='igb_uio')

        self.begin_l3fwd_power()

        self.send_and_verify(self.mac_port_0, self.rx_intf_0)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("^c", "#", 20)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
