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
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
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

"""

import math
import re
import time

from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestRuntimeVfQnMaxinum(TestCase):
    supported_vf_driver = ["igb_uio", "vfio-pci"]
    rss_key = "6EA6A420D5138E712433B813AE45B3C4BECB2B405F31AD6C331835372D15E2D5E49566EE0ED1962AFA1B7932F3549520FD71C75E"
    max_allow_per_testpmd = 18

    def set_up_all(self):
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_25G-25G_SFP28",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
            ],
            "Only supported by Intel® Ethernet 700 Series",
        )
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.src_intf = self.tester.get_interface(self.tester.get_local_port(0))
        self.src_mac = self.tester.get_mac(self.tester.get_local_port(0))
        self.dst_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]["pci"]
        self.used_dut_port = self.dut_ports[0]
        self.pmdout = PmdOutput(self.dut)
        self.setup_test_env("igb_uio")

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def setup_test_env(self, driver="default"):
        """
        Bind Intel® Ethernet 700 Series nic to DPDK PF, and create 32/64 vfs on it.
        Start testpmd based on the created vfs.
        """
        if self.nic in ["I40E_10G-SFP_XL710"]:
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 32, driver=driver)
        elif self.nic in [
            "I40E_25G-25G_SFP28",
            "I40E_40G-QSFP_A",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 64, driver=driver)

        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port]["vfs_port"]

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "vfio-pci"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")

        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)
        self.vf1_session = self.dut.new_session()
        self.vf2_session = self.dut.new_session()
        self.pf_pmdout = PmdOutput(self.dut)
        self.vf1_pmdout = PmdOutput(self.dut, self.vf1_session)
        self.vf2_pmdout = PmdOutput(self.dut, self.vf2_session)

    def destroy_test_env(self):
        if getattr(self, "pf_pmdout", None):
            self.pf_pmdout.execute_cmd("quit", "# ")
            self.pf_pmdout = None

        if getattr(self, "vf1_pmdout", None):
            self.vf1_pmdout.execute_cmd("quit", "# ", timeout=200)
            self.vf1_pmdout = None
        if getattr(self, "vf1_session", None):
            self.dut.close_session(self.vf1_session)

        if getattr(self, "vf2_pmdout", None):
            self.vf2_pmdout.execute_cmd("quit", "# ")
            self.vf2_pmdout = None
        if getattr(self, "vf2_session", None):
            self.dut.close_session(self.vf2_session)

        if getattr(self, "vf3_pmdout", None):
            self.vf3_pmdout.execute_cmd("quit", "# ", timeout=150)
            self.vf3_pmdout = None
        if getattr(self, "vf3_session", None):
            self.dut.close_session(self.vf3_session)

        # reset used port's sriov
        if getattr(self, "used_dut_port", None):
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]["port"]
            port.bind_driver()
            self.used_dut_port = None

    def send_packet(self, dest_mac, itf, count):
        """
        Sends packets.
        """
        self.tester.scapy_foreground()
        time.sleep(2)
        for i in range(count):
            quotient = i // 254
            remainder = i % 254
            packet = (
                r'sendp([Ether(dst="{0}", src=get_if_hwaddr("{1}"))/IP(src="10.0.{2}.{3}", '
                r'dst="192.168.{2}.{3}")],iface="{4}")'.format(
                    dest_mac, itf, quotient, remainder + 1, itf
                )
            )
            self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        time.sleep(2)

    def test_vf_consume_max_queues_on_one_pf(self):
        """
        Test case 1: VF consume max queue number on one PF port.
        For four port Intel® Ethernet 700 Series nic, each port has 384 queues,
        and for two port Intel® Ethernet 700 Series nic, each port has 768 queues.
        PF will use 65 queues on each port, the firmware will reserve 4 queues
        for each vf, when requested queues exceed 4 queues, it need to realloc queues
        in the left queues, the reserved queues generally can't be reused.
        """
        pf_eal_param = "-a {} --file-prefix=test1 --socket-mem 1024,1024".format(
            self.pf_pci
        )
        self.pf_pmdout.start_testpmd(
            self.pf_pmdout.default_cores, eal_param=pf_eal_param
        )
        vf1_allow_index = 0
        vf1_allow_list = ""
        vf2_queue_number = 0
        vf3_allow_index = 0
        vf3_allow_list = ""
        if self.nic in ["I40E_10G-SFP_XL710"]:
            left_queues = 384 - 65 - 32 * 4
            vf1_allow_index = left_queues / 16
            vf2_queue_number = left_queues % 16
        elif self.nic in [
            "I40E_25G-25G_SFP28",
            "I40E_40G-QSFP_A",
            "I40E_10G-SFP_X722",
            "I40E_10G-10G_BASE_T_X722",
        ]:
            left_queues = 768 - 65 - 64 * 4
            vf1_allow_index = left_queues / 16
            vf2_queue_number = left_queues % 16

        # The allow list max length is 18
        if vf1_allow_index > self.max_allow_per_testpmd:
            vf3_allow_index = vf1_allow_index % self.max_allow_per_testpmd
            vf1_allow_index = vf1_allow_index - vf3_allow_index
            self.vf3_session = self.dut.new_session()
            self.vf3_pmdout = PmdOutput(self.dut, self.vf3_session)

        self.logger.info(
            "vf2_queue_number: {}, vf3_allow_index: {}".format(
                vf2_queue_number, vf3_allow_index
            )
        )

        if vf2_queue_number > 0:
            # The driver will alloc queues as power of 2, and queue must be equal or less than 16
            vf2_queue_number = pow(2, int(math.log(vf2_queue_number, 2)))

        # we test found that if vfs do not sort, the vf2 testpmd could not start
        vf_pcis = []
        for vf in self.sriov_vfs_port_0:
            vf_pcis.append(vf.pci)
        vf_pcis.sort()
        for pci in vf_pcis[:vf1_allow_index]:
            vf1_allow_list = vf1_allow_list + "-a {} ".format(pci)
        for pci in vf_pcis[vf1_allow_index : vf1_allow_index + vf3_allow_index]:
            vf3_allow_list = vf3_allow_list + "-a {} ".format(pci)

        self.logger.info("vf1 allow list: {}".format(vf1_allow_list))
        self.logger.info("vf3_allow_list: {}".format(vf3_allow_list))
        self.logger.info("vf2_queue_number: {}".format(vf2_queue_number))

        vf1_eal_param = "{} --file-prefix=vf1 --socket-mem 1024,1024".format(
            vf1_allow_list
        )
        self.start_testpmd_multiple_times(
            self.vf1_pmdout, "--rxq=16 --txq=16", vf1_eal_param
        )

        if vf3_allow_index > 0:
            vf3_eal_param = "{} --file-prefix=vf3 --socket-mem 1024,1024".format(
                vf3_allow_list
            )
            self.start_testpmd_multiple_times(
                self.vf3_pmdout, "--rxq=16 --txq=16", vf3_eal_param
            )

        if vf2_queue_number > 0:
            vf2_eal_param = "-a {} --file-prefix=vf2 --socket-mem 1024,1024".format(
                vf_pcis[vf1_allow_index + vf3_allow_index]
            )
            self.vf2_pmdout.start_testpmd(
                self.vf2_pmdout.default_cores,
                param="--rxq={0} --txq={0}".format(vf2_queue_number),
                eal_param=vf2_eal_param,
            )

        # Check the Max possible RX queues and TX queues of the two VFs
        vf1_out = self.vf1_pmdout.execute_cmd("show port info all")
        self.verify(
            "Max possible RX queues: 16" in vf1_out, "vf1 max RX queues is not 16"
        )
        if vf2_queue_number > 0:
            vf2_out = self.vf2_pmdout.execute_cmd("show port info all")
            self.verify(
                "Max possible RX queues: 16" in vf2_out, "vf2 max RX queues is not 16"
            )
        if vf3_allow_index > 0:
            vf3_out = self.vf3_pmdout.execute_cmd("show port info all")
            self.verify(
                "Max possible RX queues: 16" in vf3_out, "vf3 max RX queues is not 16"
            )

        # check the actual queue number
        vf1_out = self.vf1_pmdout.execute_cmd("start")
        self.verify(
            "RX queue number: 16 Tx queue number: 16" in vf1_out,
            "vf1 actual RX/TX queues is not 16",
        )
        if vf2_queue_number > 0:
            vf2_out = self.vf2_pmdout.execute_cmd("start")
            self.verify(
                "port 0: RX queue number: {0} Tx queue number: {0}".format(
                    vf2_queue_number
                )
                in vf2_out,
                "vf2 actual RX/TX queues is not {}".format(vf2_queue_number),
            )
        if vf3_allow_index > 0:
            vf3_out = self.vf3_pmdout.execute_cmd("start")
            self.verify(
                "RX queue number: 16 Tx queue number: 16" in vf3_out,
                "vf3 actual RX/TX queues is not 16",
            )

        # Set all the ports share a same rss-hash key in testpmd vf1, vf3
        for i in range(vf1_allow_index):
            self.vf1_pmdout.execute_cmd(
                "port config {} rss-hash-key ipv4 {}".format(i, self.rss_key)
            )

        for i in range(vf3_allow_index):
            self.vf3_pmdout.execute_cmd(
                "port config {} rss-hash-key ipv4 {}".format(i, self.rss_key)
            )

        # send packets to vf1/vf2, and check all the queues could receive packets
        # as set promisc on, packets send by tester could be received by both vf1 and vf2
        self.vf1_pmdout.execute_cmd("set promisc all on")
        if vf2_queue_number > 0:
            self.vf2_pmdout.execute_cmd("set promisc all on")
        if vf3_allow_index > 0:
            self.vf3_pmdout.execute_cmd("set promisc all on")

        self.send_packet("00:11:22:33:44:55", self.src_intf, 256)
        vf1_out = self.vf1_pmdout.execute_cmd("stop")
        if vf2_queue_number > 0:
            vf2_out = self.vf2_pmdout.execute_cmd("stop")
        if vf3_allow_index > 0:
            vf3_out = self.vf3_pmdout.execute_cmd("stop")

        # check all queues in vf1 can receive packets
        for i in range(16):
            for j in range(vf1_allow_index):
                self.verify(
                    "Forward Stats for RX Port={:>2d}/Queue={:>2d}".format(j, i)
                    in vf1_out,
                    "Testpmd vf1 port {}, queue {} did not receive packet".format(j, i),
                )
            for m in range(vf3_allow_index):
                self.verify(
                    "Forward Stats for RX Port={:>2d}/Queue={:>2d}".format(m, i)
                    in vf3_out,
                    "Testpmd vf3 port {}, queue {} did not receive packet".format(m, i),
                )

        # check all queues in vf2 can receive packets
        for i in range(vf2_queue_number):
            self.verify(
                "Forward Stats for RX Port= 0/Queue={:>2d}".format(i) in vf2_out,
                "Testpmd vf2 queue {} did not receive packet".format(i),
            )

    def test_set_max_queue_per_vf_on_one_pf(self):
        """
        Test case 2: set max queue number per vf on one pf port
        Testpmd should not crash.
        """
        # test queue-number-per-vf exceed hardware maximum
        pf_eal_param = "-a {},queue-num-per-vf=16 --file-prefix=test1 --socket-mem 1024,1024".format(
            self.pf_pci
        )
        out = self.pf_pmdout.start_testpmd(
            self.pf_pmdout.default_cores, eal_param=pf_eal_param
        )
        self.verify(
            "exceeds the hardware maximum" in out, "queue number per vf limited error"
        )
        out = self.pf_pmdout.execute_cmd("start")
        self.verify("io packet forwarding" in out, "testpmd not work normally")

    def start_testpmd_multiple_times(self, pmdout, param, eal_param, retry_times=3):
        # There is bug that start testpmd with multiple vf for the first time will fail,
        # and it has been fixed at commit id dbda2092deb5ee5988449330c6e28e9d1fb97c19.
        while retry_times:
            try:
                pmdout.start_testpmd(
                    pmdout.default_cores, param=param, eal_param=eal_param
                )
                break
            except Exception as e:
                self.logger.info("start testpmd occurred exception: {}".format(e))
            retry_times = retry_times - 1
            time.sleep(1)
            self.logger.info("try start testpmd the {} times".format(retry_times))

    def tear_down(self):
        if getattr(self, "pf_pmdout", None):
            self.pf_pmdout.execute_cmd("quit", "# ")

        if getattr(self, "vf1_pmdout", None):
            self.vf1_pmdout.execute_cmd("quit", "# ", timeout=200)

        if getattr(self, "vf2_pmdout", None):
            self.vf2_pmdout.execute_cmd("quit", "# ")

        if getattr(self, "vf3_pmdout", None):
            self.vf3_pmdout.execute_cmd("quit", "# ", timeout=150)

    def tear_down_all(self):
        self.destroy_test_env()
