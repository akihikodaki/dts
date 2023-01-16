# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Test Layer-2 Forwarding support
"""
import os
import time

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestVfL2fwd(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.

        L2fwd prerequisites.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.test_queues = [
            {"queues": 1, "Mpps": {}, "pct": {}},
            {"queues": 2, "Mpps": {}, "pct": {}},
            {"queues": 4, "Mpps": {}, "pct": {}},
            {"queues": 8, "Mpps": {}, "pct": {}},
        ]
        self.number_of_ports = 2
        self.headers_size = HEADER_SIZE["eth"] + HEADER_SIZE["ip"] + HEADER_SIZE["udp"]
        self.verify(
            len(self.dut_ports) >= self.number_of_ports,
            "Not enough ports for " + self.nic,
        )
        self.vf_ports = ""
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        # compile
        out = self.dut.build_dpdk_apps("./examples/l2fwd")
        self.app_l2fwd_path = self.dut.apps_name["l2fwd"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def quit_l2fwd(self):
        self.dut.send_expect("fg", "l2fwd ", 5)
        self.dut.send_expect("^C", "# ", 5)

    def test_vf_l2fwd_port_forward(self):
        """
        Check port forwarding testing.
        """
        VF_MAC_ADDR_port0 = "00:11:22:33:44:55"
        VF_MAC_ADDR_port1 = "00:11:22:33:44:66"
        # generate vf
        self.dut.bind_interfaces_linux(self.kdriver)
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 1, self.kdriver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.dut_ports[0]]["vfs_port"]
        self.verify(len(self.sriov_vfs_port_0) != 0, "VF create failed")
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[1], 1, self.kdriver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.dut_ports[1]]["vfs_port"]
        self.vf_ports = [self.dut_ports[0], self.dut_ports[1]]
        self.vf_ports_pci = [self.sriov_vfs_port_0[0].pci, self.sriov_vfs_port_1[0].pci]
        for port in self.sriov_vfs_port_0 + self.sriov_vfs_port_1:
            port.bind_driver(self.drivername)

        # set vf mac address
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s"
            % (self.dut.ports_info[self.dut_ports[0]]["intf"], VF_MAC_ADDR_port0),
            "# ",
        )
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s"
            % (self.dut.ports_info[self.dut_ports[1]]["intf"], VF_MAC_ADDR_port1),
            "# ",
        )
        # the cases use the first two ports
        port_mask = utils.create_mask([self.dut_ports[0], self.dut_ports[1]])
        cores = self.dut.get_core_list(self.core_config, socket=self.ports_socket)
        eal_params = self.dut.create_eal_parameters(
            cores=cores, ports=self.vf_ports_pci
        )
        for queues in self.test_queues:
            command_line = "./%s  %s -- -q %s -p %s &" % (
                self.app_l2fwd_path,
                eal_params,
                str(queues["queues"]),
                port_mask,
            )
            self.dut.send_expect(command_line, "L2FWD: entering main loop", 60)
            # Trigger the packet generator of bursting packets from ``port A``, then check if
            # ``port 0`` could receive them and ``port 1`` could forward them back.
            tgen_input = []
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            rx_port = self.tester.get_local_port(self.dut_ports[1])
            self.tester.is_interface_up(self.tester.get_interface(rx_port))
            tgen_input.append((tx_port, rx_port))
            self.logger.info("check port A -> port 0 -> port 1 -> port B")
            result_B = self.tester.check_random_pkts(
                tgen_input,
                allow_miss=False,
                params=[("ether", {"dst": "%s" % (VF_MAC_ADDR_port0)})],
            )
            # trigger the packet generator of bursting packets from ``port B``, then
            # check if ``port 1`` could receive them and ``port 0`` could forward them back.
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[1])
            tgen_input.append((tx_port, rx_port))
            self.logger.info("check port B -> port 1 -> port 0 -> port A")
            result_A = self.tester.check_random_pkts(
                tgen_input,
                allow_miss=False,
                params=[("ether", {"dst": "%s" % (VF_MAC_ADDR_port1)})],
            )

            self.verify(result_B != False, "result_B Packet integrity check failed")
            self.verify(result_A != False, "result_A Packet integrity check failed")

            self.quit_l2fwd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("fg", "l2fwd|# ", 5)
        self.dut.send_expect("^C", "# ", 5)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        if self.vf_ports:
            for item in self.vf_ports:
                self.dut.destroy_sriov_vfs_by_port(item)
        self.dut.bind_interfaces_linux(self.drivername)
