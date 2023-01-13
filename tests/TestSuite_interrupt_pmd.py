# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2019 Intel Corporation
#

"""
DPDK Test suite.
Test interrupt pmd.
"""

import string
import time

import framework.utils as utils
from framework.packet import Packet
from framework.test_case import TestCase, skip_unsupported_host_driver


class TestInterruptPmd(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list("1S/4C/1T", socket=self.ports_socket)
        self.eal_para = self.dut.create_eal_parameters(cores="1S/4C/1T")

        userport = self.tester.get_local_port(self.dut_ports[0])
        self.tport_iface = self.tester.get_interface(userport)
        self.tx_mac = self.tester.get_mac(userport)
        self.rx_mac = self.dut.get_mac_address(self.dut_ports[0])

        self.path = self.dut.apps_name["l3fwd-power"]

        self.trafficFlow = {
            "Flow1": [[0, 0, 1], [1, 0, 2]],
            "Flow2": [[0, 0, 0], [0, 1, 1], [0, 2, 2], [0, 3, 3], [0, 4, 4]],
            "Flow3": [
                [0, 0, 0],
                [0, 1, 1],
                [0, 2, 2],
                [0, 3, 3],
                [0, 4, 4],
                [0, 5, 5],
                [0, 6, 6],
                [0, 7, 7],
                [1, 0, 8],
                [1, 1, 9],
                [1, 2, 10],
                [1, 3, 11],
                [1, 4, 12],
                [1, 5, 13],
                [1, 6, 14],
            ],
        }
        # build sample app
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")
        self.default_driver = self.get_nic_driver()
        test_driver = "vfio-pci"
        if test_driver != self.default_driver:
            self.dut.send_expect("modprobe %s" % test_driver, "#")
        self.set_nic_driver(test_driver)

    def get_nic_driver(self, port_id=0):
        port = self.dut.ports_info[port_id]["port"]
        return port.get_nic_driver()

    def set_nic_driver(self, set_driver="vfio-pci"):
        for i in self.dut_ports:
            port = self.dut.ports_info[i]["port"]
            driver = port.get_nic_driver()
            if driver != set_driver:
                port.bind_driver(driver=set_driver)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def begin_l3fwd_power(self, use_dut, cmd, timeout=60):
        """
        begin l3fwd-power
        """
        try:
            self.logger.info("Launch l3fwd_sample sample:")
            use_dut.send_expect(cmd, " Link up", timeout=timeout)
        except Exception as e:
            self.dut.kill_all()
            self.verify(
                False, "ERROR: Failed to launch  l3fwd-power sample: %s" % str(e)
            )

    def send_packet(self, mac, tport_iface, use_dut):
        """
        Send a packet and verify
        """
        res = self.tester.is_interface_up(tport_iface)
        self.verify(res, "tester port %s link status is down" % tport_iface)
        pkt = Packet(pkt_type="UDP")
        pkt.config_layer("ether", {"dst": mac, "src": self.tx_mac})
        pkt.send_pkt(self.tester, tx_port=tport_iface)
        self.out2 = use_dut.get_session_output(timeout=2)

    def test_different_queue(self):
        cmd = "%s %s -- -p 0x3 -P --config='(0,0,1),(1,0,2)' " % (
            self.path,
            self.eal_para,
        )
        self.begin_l3fwd_power(self.dut, cmd)
        portQueueLcore = self.trafficFlow["Flow1"]
        self.verifier_result(2, 2, portQueueLcore)

        self.dut.kill_all()
        cores = list(range(6))
        eal_para = self.dut.create_eal_parameters(cores=cores)
        cmd = (
            "%s %s -- -p 0x3 -P --config='(0,0,0),(0,1,1),(0,2,2),(0,3,3),(0,4,4)' "
            % (self.path, eal_para)
        )
        self.begin_l3fwd_power(self.dut, cmd)
        portQueueLcore = self.trafficFlow["Flow2"]
        self.verifier_result(20, 1, portQueueLcore)

        self.dut.kill_all()
        cores = list(range(24))
        eal_para = self.dut.create_eal_parameters(cores=cores)
        cmd = (
            "%s %s -- -p 0x3 -P --config='(0,0,0),(0,1,1),(0,2,2),(0,3,3),\
        (0,4,4),(0,5,5),(0,6,6),(0,7,7),(1,0,8),(1,1,9),(1,2,10),(1,3,11),\
        (1,4,12),(1,5,13),(1,6,14)' "
            % (self.path, eal_para)
        )

        self.begin_l3fwd_power(self.dut, cmd)
        portQueueLcore = self.trafficFlow["Flow3"]
        self.verifier_result(40, 2, portQueueLcore)

    def test_nic_interrupt_PF_vfio_pci(self):
        """
        Check Interrupt for PF with vfio-pci driver
        """
        eal_para = self.dut.create_eal_parameters(cores=self.core_list)
        cmd = "%s %s -- -P -p 1 --config='(0,0,%s)'" % (
            self.path,
            eal_para,
            self.core_list[0],
        )

        self.begin_l3fwd_power(self.dut, cmd)

        self.send_packet(self.rx_mac, self.tport_iface, self.dut)

        self.verify(
            "lcore %s is waked up from rx interrupt on port 0" % self.core_list[0]
            in self.out2,
            "Wake up failed",
        )
        self.verify(
            "lcore %s sleeps until interrupt triggers" % self.core_list[0] in self.out2,
            "lcore %s not sleeps" % self.core_list[0],
        )

    @skip_unsupported_host_driver(["vfio-pci"])
    def test_nic_interrupt_PF_igb_uio(self):
        """
        Check Interrupt for PF with igb_uio driver
        """
        self.dut.setup_modules_linux(self.target, "igb_uio", "")
        self.dut.ports_info[0]["port"].bind_driver(driver="igb_uio")

        eal_para = self.dut.create_eal_parameters(cores=self.core_list)
        cmd = "%s %s -- -P -p 1 --config='(0,0,%s)'" % (
            self.path,
            eal_para,
            self.core_list[0],
        )
        self.begin_l3fwd_power(self.dut, cmd)
        self.send_packet(self.rx_mac, self.tport_iface, self.dut)

        self.verify(
            "lcore %s is waked up from rx interrupt on port 0" % self.core_list[0]
            in self.out2,
            "Wake up failed",
        )
        self.verify(
            "lcore %s sleeps until interrupt triggers" % self.core_list[0] in self.out2,
            "lcore %s not sleeps" % self.core_list[0],
        )

    def verifier_result(self, num, portnum, portQueueLcore):
        self.scapy_send_packet(num, portnum)
        result = self.dut.get_session_output(timeout=5)
        for i in range(len(portQueueLcore)):
            lcorePort = portQueueLcore[i]
            self.verify(
                "FWD_POWER: lcore %d is waked up from rx interrupt on port %d queue %d"
                % (lcorePort[2], lcorePort[0], lcorePort[1])
                in result,
                "Wrong: lcore %d is waked up failed" % lcorePort[2],
            )
            self.verify(
                "L3FWD_POWER: lcore %d sleeps until interrupt triggers" % (lcorePort[2])
                in result,
                "Wrong: lcore %d not sleeps until interrupt triggers" % lcorePort[2],
            )

    def scapy_send_packet(self, num, portnum):
        """
        Send a packet to port
        """
        for i in range(len(self.dut_ports[:portnum])):
            txport = self.tester.get_local_port(self.dut_ports[i])
            mac = self.dut.get_mac_address(self.dut_ports[i])
            txItf = self.tester.get_interface(txport)
            self.verify(
                self.tester.is_interface_up(intf=txItf),
                "Tester's %s should be up".format(txItf),
            )
            for j in range(num):
                self.tester.scapy_append(
                    'sendp([Ether()/IP(dst="198.0.0.%d")/UDP()/Raw(\'X\'*18)], iface="%s")'
                    % (j, txItf)
                )
        self.tester.scapy_execute()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.set_nic_driver(self.default_driver)
