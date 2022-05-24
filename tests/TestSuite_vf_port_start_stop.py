# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

VM_CORES_MASK = "all"


class TestVfPortStartStop(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vm0 = None
        self.tester_tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.tester_tintf = self.tester.get_interface(self.tester_tx_port)
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

    def set_up(self):

        self.setup_1pf_2vf_1vm_env_flag = 0
        self.send_pks_session = None
        self.pkts = Packet()

    def send_and_verify(self, dst_mac, testpmd):
        """
        Generates packets by pktgen
        """
        self.testpmd_reset_status(testpmd)

        src_mac = self.tester.get_mac(self.tester_tx_port)
        if src_mac == "N/A":
            src_mac = "02:00:00:00:01"
        self.send_pkts(dst_mac, src_mac)
        time.sleep(1)
        self.check_port_start_stop(testpmd)

    def send_pkts(self, dst_mac, src_mac):
        """
        Generates a valid PCAP file with the given configuration.
        """
        def_pkts = {
            "IP/UDP": 'Ether(dst="%s", src="%s")/IP(src="127.0.0.2")/UDP()/("X"*46)'
            % (dst_mac, src_mac),
            "IP/TCP": 'Ether(dst="%s", src="%s")/IP(src="127.0.0.2")/TCP()/("X"*46)'
            % (dst_mac, src_mac),
            "IP/SCTP": 'Ether(dst="%s", src="%s")/IP(src="127.0.0.2")/SCTP()/("X"*48)'
            % (dst_mac, src_mac),
            "IPv6/UDP": 'Ether(dst="%s", src="%s")/IPv6(src="::2")/UDP()/("X"*46)'
            % (dst_mac, src_mac),
            "IPv6/TCP": 'Ether(dst="%s", src="%s")/IPv6(src="::2")/TCP()/("X"*46)'
            % (dst_mac, src_mac),
        }

        for key in list(def_pkts.keys()):
            self.pkts.append_pkt(def_pkts[key])
        self.send_pks_session = self.pkts.send_pkt_bg(self.tester, self.tester_tintf)

    def testpmd_reset_status(self, testpmd):
        """
        Reset testpmd :stop forward & stop port
        """
        testpmd.execute_cmd("stop")
        testpmd.execute_cmd("port stop all")
        testpmd.execute_cmd("clear port stats all")

    def check_port_start_stop(self, testpmd, times=10):
        """
        VF port start/stop several times , check if it work well.
        """
        for i in range(times):
            out = testpmd.execute_cmd("port start all")
            self.verify("Checking link statuses" in out, "ERROR: port start all")
            testpmd.execute_cmd("start")
            time.sleep(0.5)
            testpmd.execute_cmd("stop")
            out = testpmd.execute_cmd("port stop all")
            self.verify("Checking link statuses" in out, "ERROR: port stop all")

        port_id_0 = 0
        port_id_1 = 1
        vf0_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
        vf1_stats = self.vm0_testpmd.get_pmd_stats(port_id_1)

        vf0_rx_cnt = vf0_stats["RX-packets"]
        self.verify(vf0_rx_cnt != 0, "no packet was received by vm0_VF0")

        vf0_rx_err = vf0_stats["RX-errors"]
        self.verify(vf0_rx_err == 0, "vm0_VF0 rx-errors")

        vf1_tx_cnt = vf1_stats["TX-packets"]
        self.verify(vf1_tx_cnt != 0, "no packet was transmitted by vm0_VF1")

        vf1_tx_err = vf1_stats["TX-errors"]
        self.verify(vf1_tx_err == 0, "vm0_VF0 tx-errors")

    def setup_1pf_2vf_1vm_env(self, driver="default"):

        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]

        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)

            time.sleep(1)

            vf0_prop = {"opt_host": self.sriov_vfs_port[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port[1].pci}

            if driver == "igb_uio":
                # start testpmd without the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                self.host_testpmd.start_testpmd("1S/2C/2T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, "vm0", "vf_port_start_stop")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

            self.setup_1pf_2vf_1vm_env_flag = 1
        except Exception as e:
            self.destroy_1pf_2vf_1vm_env()
            raise Exception(e)

    def destroy_1pf_2vf_1vm_env(self):
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

        if getattr(self, "host_testpmd", None):
            self.host_testpmd.execute_cmd("quit", "# ")
            self.host_testpmd = None

        if getattr(self, "used_dut_port", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]["port"]
            port.bind_driver()
            self.used_dut_port = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver()

        self.setup_1pf_2vf_1vm_env_flag = 0

    def test_start_stop_with_kernel_1pf_2vf_1vm(self):

        self.setup_1pf_2vf_1vm_env(driver="")

        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set fwd mac")

        time.sleep(2)

        dst_mac = self.vm0_testpmd.get_port_mac(self.vm0_dut_ports[0])
        self.send_and_verify(dst_mac, self.vm0_testpmd)

    def tear_down(self):

        if self.send_pks_session:
            self.pkts.stop_send_pkt_bg(self.send_pks_session)
        if self.setup_1pf_2vf_1vm_env_flag == 1:
            self.destroy_1pf_2vf_1vm_env()

    def tear_down_all(self):

        if getattr(self, "vm0", None):
            self.vm0.stop()

        self.dut.virt_exit()

        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)
