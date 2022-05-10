# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

import random
import sys
import time

from scapy.utils import rdpcap

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.settings import get_nic_name
from framework.test_case import TestCase

VM_CORES_MASK = "all"
PF_MAX_QUEUE = 64
VF_MAX_QUEUE = 4


class Testddp_mpls(TestCase):
    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        self.verify(
            self.is_eth_series_nic(700), "ddp mpls can not support %s nic" % self.nic
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False
        profile_file = r"dep/mpls.pkgo"
        profile_dst = "/tmp/"
        self.dut.session.copy_file_to(profile_file, profile_dst)

        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")

    def set_up(self):
        self.setup_vm_env()

    def setup_vm_env(self, driver="default"):
        """
        Create testing environment with VF generated from 1PF
        """
        if self.env_done == False:
            self.bind_nic_driver(self.dut_ports[:1], driver="igb_uio")
            self.used_dut_port = self.dut_ports[0]
            tester_port = self.tester.get_local_port(self.used_dut_port)
            self.tester_intf = self.tester.get_interface(tester_port)

            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1, driver=driver)
            self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)
            time.sleep(1)
            self.dut_testpmd = PmdOutput(self.dut)
            time.sleep(1)
            vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}

            # set up VM0 ENV
            self.vm0 = QEMUKvm(self.dut, "vm0", "ddp_mpls")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            try:
                self.vm0_dut = self.vm0.start()
                if self.vm0_dut is None:
                    raise Exception("Set up VM0 ENV failed!")
            except Exception as e:
                self.destroy_vm_env()
                raise Exception(e)

            self.vm0_dut_ports = self.vm0_dut.get_ports("any")
            self.vm0_testpmd = PmdOutput(self.vm0_dut)
            self.env_done = True

        self.dut_testpmd.start_testpmd(
            "Default",
            "--port-topology=chained --txq=%s --rxq=%s" % (PF_MAX_QUEUE, PF_MAX_QUEUE),
        )
        self.vm0_testpmd.start_testpmd(
            VM_CORES_MASK,
            "--port-topology=chained --txq=%s --rxq=%s --disable-rss"
            % (VF_MAX_QUEUE, VF_MAX_QUEUE),
        )

    def destroy_vm_env(self):

        if getattr(self, "vm0", None):
            self.vm0_dut.kill_all()
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, "used_dut_port", None):
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]["port"]
            self.used_dut_port = None

        self.env_done = False

    def load_profile(self):
        """
        Load profile to update Intel® Ethernet 700 Series configuration tables,
        profile will be stored in binary file and need to be passed to AQ to
        program Intel® Ethernet 700 Series during initialization stage.
        """
        self.dut_testpmd.execute_cmd("port stop all")
        time.sleep(1)
        out = self.dut_testpmd.execute_cmd("ddp get list 0")
        self.verify(
            "Profile number is: 0" in out, "Failed to get ddp profile info list!!!"
        )
        self.dut_testpmd.execute_cmd("ddp add 0 /tmp/mpls.pkgo,/tmp/mpls.bak")
        out = self.dut_testpmd.execute_cmd("ddp get list 0")
        self.verify("Profile number is: 1" in out, "Failed to load ddp profile!!!")
        self.dut_testpmd.execute_cmd("port start all")
        time.sleep(1)

    def mpls_test(self, port="pf", pkt="udp"):
        """
        Send mpls packet to dut, receive packet from configured queue.
        Input: port type, packet type
        """
        pkts = []
        if port == "pf":
            queue = random.randint(1, PF_MAX_QUEUE - 1)
            self.dut_testpmd.execute_cmd("set fwd rxonly")
            self.dut_testpmd.execute_cmd("set verbose 1")
            self.dut_testpmd.execute_cmd("start")
        else:
            queue = random.randint(1, VF_MAX_QUEUE - 1)
            self.vm0_testpmd.execute_cmd("set fwd rxonly")
            self.vm0_testpmd.execute_cmd("set verbose 1")
            self.vm0_testpmd.execute_cmd("start")
        random_label = random.randint(0x0, 0xFFFFF)
        label = hex(random_label)
        wrong_label = hex((random_label + 2) % int(0xFFFFF))
        self.dut_testpmd.execute_cmd(
            "flow create 0 ingress pattern eth / ipv4\
            / %s / mpls label is %s / end actions %s / queue index %d / end"
            % (pkt, label, port, queue)
        )
        for times in range(2):
            if pkt == "udp":
                pkts = {
                    "mpls/good chksum udp": "Ether()/IP()/UDP(dport=6635)\
                            /MPLS(label=%s)/Ether()/IP()/TCP()"
                    % label,
                    "mpls/bad chksum udp": "Ether()/IP()/UDP(chksum=0x1234,\
                            dport=6635)/MPLS(label=%s)/Ether()/IP()/TCP()"
                    % label,
                }
            else:
                pkts = {
                    "mpls/good chksum gre": "Ether()/IP(proto=47)/GRE(proto=0x8847)\
                            /MPLS(label=%s)/Ether()/IP()/UDP()"
                    % label,
                    "mpls/bad chksum gre": "Ether()/IP(proto=47)/GRE(chksum=0x1234,\
                            proto=0x8847)/MPLS(label=%s)/Ether()/IP()/UDP()"
                    % label,
                }
            for packet_type in list(pkts.keys()):
                self.tester.scapy_append(
                    'sendp([%s], iface="%s")' % (pkts[packet_type], self.tester_intf)
                )
                self.tester.scapy_execute()
                if port == "pf":
                    out = self.dut.get_session_output(timeout=2)
                else:
                    out = self.vm0_dut.get_session_output(timeout=2)

                self.verify(
                    "port 0/queue %d" % queue in out,
                    "Failed to receive packet in this queue!!!",
                )
                self.verify(
                    "RTE_MBUF_F_RX_L4_CKSUM_GOOD" in out, "Failed to check CKSUM!!!"
                )
            label = wrong_label
            queue = 0

    def test_load_ddp(self):
        """
        Load profile to update Intel® Ethernet 700 Series configuration tables.
        """
        self.load_profile()

    def test_mpls_udp_pf(self):
        """
        MPLS is supported by NVM with profile updated. Send mpls udp packet to PF,
        check PF could receive packet using configured queue, checksum is good.
        """
        self.load_profile()
        self.mpls_test(port="pf", pkt="udp")

    def test_mpls_gre_pf(self):
        """
        MPLS is supported by NVM with profile updated. Send mpls gre packet to PF,
        check PF could receive packet using configured queue, checksum is good.
        """
        self.load_profile()
        self.mpls_test(port="pf", pkt="gre")

    def test_mpls_udp_vf(self):
        """
        MPLS is supported by NVM with profile updated. Send mpls udp packet to VF,
        check VF could receive packet using configured queue, checksum is good.
        """
        self.load_profile()
        self.mpls_test(port="vf id 0", pkt="udp")

    def test_mpls_gre_vf(self):
        """
        MPLS is supported by NVM with profile updated. Send mpls gre packet to VF,
        check VF could receive packet using configured queue, checksum is good.
        """
        self.load_profile()
        self.mpls_test(port="vf id 0", pkt="gre")

    def tear_down(self):
        self.vm0_testpmd.execute_cmd("stop")
        self.dut_testpmd.execute_cmd("stop")
        out = self.dut_testpmd.execute_cmd("ddp get list 0")
        if "Profile number is: 0" not in out:
            self.dut_testpmd.execute_cmd("port stop all")
            time.sleep(1)
            self.dut_testpmd.execute_cmd("ddp del 0 /tmp/mpls.bak")
            out = self.dut_testpmd.execute_cmd("ddp get list 0")
            self.verify(
                "Profile number is: 0" in out, "Failed to delete mpls profile!!!"
            )
            self.dut_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.quit()
        self.dut_testpmd.quit()

    def tear_down_all(self):
        self.destroy_vm_env()
        pass
