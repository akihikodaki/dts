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
Test the support of Malicious Driver Detection
"""


import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

VM_CORES_MASK = "all"
send_pks_num = 2000


class TestMDD(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")
        self.dut.send_expect("dmesg -c", "#")

        self.port_id_0 = 0
        self.port_id_1 = 1

        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.rx_port = self.tester.get_local_port(self.dut_ports[1])

    def set_up(self):
        pass

    def setup_2pf_2vf_1vm_env(self):
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver="ixgbe")
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver="ixgbe")
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]["vfs_port"]

        try:

            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {"opt_host": self.sriov_vfs_port_0[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port_1[0].pci}
            # not support driver=igb_uio,because driver is kernel driver
            # set up VM0 ENV
            self.vm0 = VM(self.dut, "vm0", "mdd")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

        except Exception as e:
            self.destroy_2pf_2vf_1vm_env()
            raise Exception(e)

    def destroy_2pf_2vf_1vm_env(self):
        if getattr(self, "vm0", None):
            # destroy testpmd in vm0
            if getattr(self, "vm0_testpmd", None):
                self.vm0_testpmd.execute_cmd("stop")
                self.vm0_testpmd.execute_cmd("quit", "# ")
                self.vm0_testpmd = None

            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.vm0 = None

        self.dut.virt_exit()

        if getattr(self, "used_dut_port_0", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            port = self.dut.ports_info[self.used_dut_port_0]["port"]
            port.bind_driver()
            self.used_dut_port_0 = None

        if getattr(self, "used_dut_port_1", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            port = self.dut.ports_info[self.used_dut_port_1]["port"]
            port.bind_driver()
            self.used_dut_port_1 = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver()

    def start_testpmd_in_vm(self, txoffload=""):
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)

        self.vm0_testpmd.start_testpmd(
            VM_CORES_MASK, "--portmask=0x3 --tx-offloads=%s" % txoffload
        )
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("start")

    def send_packets(self):

        tgen_ports = []
        self.tester_intf = self.tester.get_interface(self.tx_port)
        tgen_ports.append((self.tx_port, self.rx_port))
        self.pmd_vf0_mac = self.vm0_testpmd.get_port_mac(self.port_id_0)

        dst_mac = self.pmd_vf0_mac
        src_mac = self.tester.get_mac(self.tx_port)

        pkt = Packet(pkt_type="UDP", pkt_len=64)
        pkt.config_layer("ether", {"dst": dst_mac, "src": src_mac})
        time.sleep(2)
        self.vm0_testpmd.execute_cmd("clear port stats all")
        self.vm0_testpmd.execute_cmd("show port stats all")
        pkt.send_pkt(self.tester, tx_port=self.tester_intf, count=send_pks_num)
        time.sleep(2)

    def result_verify(self, pkt_fwd=True):
        pmd0_vf0_stats = self.vm0_testpmd.get_pmd_stats(self.port_id_0)
        pmd0_vf1_stats = self.vm0_testpmd.get_pmd_stats(self.port_id_1)
        time.sleep(2)

        vf0_rx_cnt = pmd0_vf0_stats["RX-packets"]
        self.verify(vf0_rx_cnt >= send_pks_num, "no packet was received by vm0_VF0")

        vf0_rx_err = pmd0_vf0_stats["RX-errors"]
        self.verify(vf0_rx_err == 0, "vm0_VF0 rx-errors")

        vf1_tx_cnt = pmd0_vf1_stats["TX-packets"]
        if pkt_fwd:
            self.verify(vf1_tx_cnt == send_pks_num, "Packet forwarding failed")
        else:
            self.verify(vf1_tx_cnt == 0, "Packet is forwarded")

    def config_mdd(self, value):
        self.dut.restore_interfaces()
        self.dut.send_expect("rmmod ixgbe", "# ", 10)
        time.sleep(2)
        count = self.dut.send_expect(
            "./usertools/dpdk-devbind.py -s | grep ixgbe | wc -l", "#"
        )
        m = [value for i in range(int(count))]
        mdd = "MDD=" + str(m).replace("[", "").replace("]", "").replace(" ", "")
        self.dut.send_expect("modprobe ixgbe %s" % mdd, "# ", 10)
        time.sleep(5)
        for port_info in self.dut.ports_info:
            port = port_info["port"]
            intf = port.get_interface_name()
            self.dut.send_expect("ifconfig %s up" % intf, "# ", 10)
            time.sleep(2)

    def test_1enable_mdd_dpdk_disable(self):
        self.config_mdd(1)
        self.setup_2pf_2vf_1vm_env()
        self.start_testpmd_in_vm(txoffload="0x1")
        self.send_packets()
        self.result_verify(False)
        dmesg = self.dut.send_expect("dmesg -c |grep 'event'", "# ", 10)
        self.verify("Malicious event" in dmesg, "mdd error")

    def test_2enable_mdd_dpdk_enable(self):
        self.config_mdd(1)
        self.setup_2pf_2vf_1vm_env()
        self.start_testpmd_in_vm(txoffload="0x0")
        self.send_packets()
        self.result_verify(False)
        dmesg = self.dut.send_expect("dmesg -c |grep 'event'", "# ", 10)
        self.verify("Malicious event" in dmesg, "mdd error")

    def test_3disable_mdd_dpdk_disable(self):
        self.config_mdd(0)
        self.setup_2pf_2vf_1vm_env()
        self.start_testpmd_in_vm(txoffload="0x1")
        self.send_packets()
        self.result_verify(True)
        dmesg = self.dut.send_expect("dmesg -c |grep 'event'", "# ", 10)
        self.verify("Malicious event" not in dmesg, "mdd error")

    def test_4disable_mdd_dpdk_enable(self):
        self.config_mdd(0)
        self.setup_2pf_2vf_1vm_env()
        self.start_testpmd_in_vm(txoffload="0x0")
        self.send_packets()
        self.result_verify(True)
        dmesg = self.dut.send_expect("dmesg -c |grep 'event'", "# ", 10)
        self.verify("Malicious event" not in dmesg, "mdd error")

    def tear_down(self):
        self.destroy_2pf_2vf_1vm_env()

    def tear_down_all(self):
        pass
