# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2015 Intel Corporation
#

"""
DPDK Test suite.

Test queue start stop Feature

"""

import os
import re
import time

from framework.packet import Packet, strip_pktload
from framework.pmd_output import PmdOutput
from framework.settings import FOLDERS
from framework.test_case import TestCase

#
#
# Test class.
#


class TestQueueStartStop(TestCase):
    #
    #
    #
    # Test cases.
    #

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports(self.nic)
        self.verify(len(self.ports) >= 1, "Insufficient number of ports.")
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        try:
            patch_file = FOLDERS["Depends"] + r"/macfwd_log.patch"
        except:
            self.logger.warning(str(FOLDERS))
            patch_file = r"dep/macfwd_log.patch"
            FOLDERS["Depends"] = "dep"
        patch_dst = "/tmp/"

        # dpdk patch and build
        try:
            self.dut.session.copy_file_to(patch_file, patch_dst)
            self.patch_hotfix_dpdk(patch_dst + "macfwd_log.patch", True)
            self.dut.build_install_dpdk(self.target)
        except Exception as e:
            raise IOError("dpdk setup failure: %s" % e)

    def check_forwarding(self, ports, nic, pktSize=64, received=True):
        self.send_packet(ports[0], ports[1], self.nic, pktSize, received)

    def send_packet(self, txPort, rxPort, nic, pktSize=64, received=True):
        """
        Send packages according to parameters.
        """
        rxitf = self.tester.get_interface(self.tester.get_local_port(rxPort))
        txitf = self.tester.get_interface(self.tester.get_local_port(txPort))

        dmac = self.dut.get_mac_address(txPort)

        pkt = Packet(pkt_type="UDP", pkt_len=pktSize)
        inst = self.tester.tcpdump_sniff_packets(rxitf)
        pkt.config_layer("ether", {"dst": dmac})
        pkt.send_pkt(self.tester, tx_port=txitf, count=4)
        sniff_pkts = self.tester.load_tcpdump_sniff_packets(inst)

        if received:
            res = strip_pktload(sniff_pkts, layer="L4")
            self.verify(
                "58 58 58 58 58 58 58 58" in res, "receive queue not work as expected"
            )
        else:
            self.verify(len(sniff_pkts) == 0, "stop queue not work as expected")

    def patch_hotfix_dpdk(self, patch_dir, on=True):
        """
        This function is to apply or remove patch for dpdk.
        patch_dir: the abs path of the patch
        on: True for apply, False for remove
        """
        try:
            if on:
                self.dut.send_expect("patch -p0 < %s" % patch_dir, "[~|~\]]# ")
            else:
                self.dut.send_expect("patch -p0 -R < %s" % patch_dir, "[~|~\]]# ")
        except Exception as e:
            raise ValueError("patch_hotfix_dpdk failure: %s" % e)

    def test_queue_start_stop(self):
        """
        queue start/stop test
        """
        # dpdk start
        eal_para = self.dut.create_eal_parameters()
        try:
            self.dut.send_expect(
                "%s %s -- -i --portmask=0x1 --port-topology=loop"
                % (self.app_testpmd_path, eal_para),
                "testpmd>",
                120,
            )
            time.sleep(5)
            self.dut.send_expect("set fwd mac", "testpmd>")
            self.dut.send_expect("start", "testpmd>")
            self.check_forwarding([0, 0], self.nic)
        except Exception as e:
            raise IOError("dpdk start and first forward failure: %s" % e)

            # stop rx queue test
        try:
            print("test stop rx queue")
            self.dut.send_expect("stop", "testpmd>")
            self.dut.send_expect("port 0 rxq 0 stop", "testpmd>")
            self.dut.send_expect("start", "testpmd>")
            self.check_forwarding([0, 0], self.nic, received=False)

            # start rx queue test
            print("test start rx queue stop tx queue")
            self.dut.send_expect("stop", "testpmd>")
            self.dut.send_expect("port 0 rxq 0 start", "testpmd>")
            self.dut.send_expect("port 0 txq 0 stop", "testpmd>")
            self.dut.send_expect("start", "testpmd>")
            self.check_forwarding([0, 0], self.nic, received=False)
            out = self.dut.get_session_output()
        except Exception as e:
            raise IOError("queue start/stop forward failure: %s" % e)
        self.verify(
            "ports 0 queue 0 receive " not in out,
            "start queue revice package failed, out = %s" % out,
        )

        try:
            # start tx queue test
            print("test start rx and tx queue")
            self.dut.send_expect("stop", "testpmd>")
            self.dut.send_expect("port 0 txq 0 start", "testpmd>")
            self.dut.send_expect("start", "testpmd>")
            self.check_forwarding([0, 0], self.nic)
            out = self.dut.get_session_output()
        except Exception as e:
            raise IOError("queue start/stop forward failure: %s" % e)
        self.verify(
            "ports 0 queue 0 receive " in out,
            "start queue revice package failed, out = %s" % out,
        )

    def tear_down(self):
        """
        Run after each test case.
        """
        patch_dst = "/tmp/"

        try:
            self.dut.send_expect("stop", "testpmd>")
            self.dut.send_expect("quit", "#")
        except:
            print("Failed to quit testpmd")

        self.dut.kill_all()

        try:
            self.patch_hotfix_dpdk(patch_dst + "macfwd_log.patch", False)
        except Exception as e:
            print(("patch_hotfix_dpdk remove failure :%s" % e))

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.send_expect("rm -rf ./app/test-pmd/testpmd", "#")
        self.dut.send_expect("rm -rf ./app/test-pmd/*.o", "#")
        self.dut.send_expect("rm -rf ./app/test-pmd/build", "#")
