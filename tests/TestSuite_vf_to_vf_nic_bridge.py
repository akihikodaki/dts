# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

"""
DPDK Test suite
Test vf to vf nic bridge
"""

import pdb
import re
import time

import framework.utils as utils
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM

VF_NUMS_ON_ONE_PF = 2
VF_TEMP_MAC = "52:54:12:45:67:1%d"
SEND_PACKET = 100


class TestVfToVfNicBridge(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vm0 = None
        self.vm1 = None

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
        self.set_up_vf_to_vf_env()

    def set_up_vf_to_vf_env(self, driver="default"):
        self.pf_port_for_vfs = self.dut_ports[0]
        self.dut.restore_interfaces()
        self.dut.generate_sriov_vfs_by_port(
            self.pf_port_for_vfs, VF_NUMS_ON_ONE_PF, driver=driver
        )
        self.sriov_vfs_ports = self.dut.ports_info[self.pf_port_for_vfs]["vfs_port"]
        self.host_port_intf = self.dut.ports_info[self.pf_port_for_vfs]["intf"]
        for i in range(VF_NUMS_ON_ONE_PF):
            self.dut.send_expect(
                "ip link set dev %s vf %d mac %s"
                % (self.host_port_intf, i, VF_TEMP_MAC % i),
                "#",
                10,
            )
        try:
            for port in self.sriov_vfs_ports:
                port.bind_driver(self.vf_driver)
            time.sleep(1)
        except Exception as e:
            raise Exception(e)

        vf0_prop = {"opt_host": self.sriov_vfs_ports[0].pci}
        vf1_prop = {"opt_host": self.sriov_vfs_ports[1].pci}
        time.sleep(1)
        self.vm0 = VM(self.dut, "vm0", "vf_to_vf_bridge")
        self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM0 failed")
        except Exception as e:
            print(utils.RED(str(e)))

        self.vm1 = VM(self.dut, "vm1", "vf_to_vf_bridge")
        self.vm1.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
        try:
            self.vm1_dut = self.vm1.start()
            if self.vm1_dut is None:
                raise Exception("Set up VM1 failed")
        except Exception as e:
            print(utils.RED(str(e)))

    def clear_vf_to_vf_env(self):
        if self.vm0 is not None:
            self.vm0.stop()
            self.vm0 = None
        if self.vm1 is not None:
            self.vm1.stop()
            self.vm1 = None
        self.dut.virt_exit()
        if self.pf_port_for_vfs is not None:
            self.dut.destroy_sriov_vfs_by_port(self.pf_port_for_vfs)
            port = self.dut.ports_info[self.pf_port_for_vfs]["port"]
            port.bind_driver()
            self.pf_port_for_vfs = 0

    def test_2vf_d2d_testpmd_stream(self):
        self.vm0_ports = self.vm0_dut.get_ports("any")
        self.vm0_pmd = PmdOutput(self.vm0_dut)
        self.vm0_pmd.start_testpmd("all")
        self.vm0_pmd.execute_cmd("set fwd rxonly")
        self.vm0_pmd.execute_cmd("set promisc all off")
        self.vm0_pmd.execute_cmd("start")

        vm0_mac = self.vm0_dut.ports_info[self.vm0_ports[0]]["mac"]

        self.vm1_pmd = PmdOutput(self.vm1_dut)
        self.vm1_pmd.start_testpmd("all")
        self.vm1_pmd.execute_cmd("set fwd mac")
        self.vm1_pmd.execute_cmd("set promisc all off")
        self.vm1_pmd.execute_cmd("set eth-peer 0 %s" % vm0_mac)
        self.vm1_pmd.execute_cmd("set burst 50")
        self.vm1_pmd.execute_cmd("start tx_first 2")

        recv_num = self.vm0_pmd.get_pmd_stats(0)["RX-packets"]
        time.sleep(1)
        self.vm0_pmd.execute_cmd("stop")
        self.vm0_pmd.execute_cmd("quit", "# ")

        self.vm1_pmd.execute_cmd("stop")
        self.vm1_pmd.execute_cmd("quit", "# ")

        self.verify(recv_num is SEND_PACKET, "Rx port recv error: %d" % recv_num)

    def test_2vf_d2k_testpmd_stream(self):
        self.vm0_dut.restore_interfaces()
        self.vm0_ports = self.vm0_dut.get_ports("any")
        vf0_intf = self.vm0_dut.ports_info[self.vm0_ports[0]]["intf"]

        self.vm1_ports = self.vm1_dut.get_ports("any")

        vm0_mac = self.vm0_dut.ports_info[self.vm0_ports[0]]["mac"]
        filename = "m.pcap"

        self.vm0_dut.send_expect(
            "tcpdump -i %s ether dst %s -w %s" % (vf0_intf, vm0_mac, filename),
            "tcpdump",
            30,
        )

        self.vm1_pmd = PmdOutput(self.vm1_dut)
        self.vm1_pmd.start_testpmd("all")
        self.vm1_pmd.execute_cmd("set fwd mac")
        self.vm1_pmd.execute_cmd("set promisc all off")
        self.vm1_pmd.execute_cmd("set eth-peer 0 %s" % vm0_mac)
        self.vm1_pmd.execute_cmd("set burst 50")
        self.vm1_pmd.execute_cmd("start tx_first 2")

        time.sleep(1)
        recv_tcpdump = self.vm0_dut.send_expect("^C", "#", 30)
        time.sleep(5)
        recv_pattern = re.compile("(\d+) packet\w{0,1} captured")
        recv_info = recv_pattern.search(recv_tcpdump)
        recv_str = recv_info.group(0).split(" ")[0]
        recv_number = int(recv_str, 10)
        self.vm0_dut.bind_interfaces_linux(self.drivername)

        self.vm1_pmd.execute_cmd("stop")
        self.vm1_pmd.execute_cmd("quit", "# ")

        self.verify(recv_number is SEND_PACKET, "Rx port recv error: %d" % recv_number)

    def test_2vf_k2d_scapy_stream(self):
        self.vm0_ports = self.vm0_dut.get_ports("any")
        self.vm0_pmd = PmdOutput(self.vm0_dut)
        self.vm0_pmd.start_testpmd("all")

        self.vm1_ports = self.vm1_dut.get_ports("any")
        self.vm1_dut.restore_interfaces()
        vf1_intf = self.vm1_dut.ports_info[self.vm1_ports[0]]["intf"]

        dst_mac = self.vm0_dut.ports_info[self.vm0_ports[0]]["mac"]
        src_mac = self.vm1_dut.ports_info[self.vm1_ports[0]]["mac"]
        pkt_content = 'Ether(dst="%s", src="%s")/IP()/Raw(load="X"*46)' % (
            dst_mac,
            src_mac,
        )
        self.vm1_dut.send_expect("scapy", ">>> ", 10)

        self.vm0_pmd.execute_cmd("set promisc all off")
        self.vm0_pmd.execute_cmd("set fwd rxonly")
        self.vm0_pmd.execute_cmd("set verbose 1")
        self.vm0_pmd.execute_cmd("start")

        self.vm1_dut.send_expect(
            'sendp([%s], iface="%s", count=%d)' % (pkt_content, vf1_intf, SEND_PACKET),
            ">>> ",
            30,
        )

        out = self.vm0_dut.get_session_output(timeout=60)
        rx_packets = re.findall("src=%s - dst=%s" % (src_mac, dst_mac), out)
        recv_num = len(rx_packets)

        self.vm1_dut.send_expect("quit()", "# ", 10)
        self.vm1_dut.bind_interfaces_linux(self.drivername)
        self.vm0_pmd.execute_cmd("stop")
        self.vm0_pmd.execute_cmd("quit", "# ")

        self.verify(recv_num is SEND_PACKET, "Rx port recv error: %d" % recv_num)

    def tear_down(self):
        self.clear_vf_to_vf_env()

    def tear_down_all(self):
        pass
