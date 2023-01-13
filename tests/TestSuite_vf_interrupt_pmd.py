# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2017 Intel Corporation
#

"""
DPDK Test suite.
Test vf_interrupt_pmd.
"""

import pdb
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.test_case import TestCase
from framework.virt_common import VM


class TestVfInterruptPmd(TestCase):
    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.env_done = False
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
        self.vf0_mac = "00:12:34:56:78:01"
        self.vf_mac = "00:12:34:56:78:02"
        self.mac_port_0 = self.dut.get_mac_address(self.dut_ports[0])
        self.queues = 1
        self.vf_driver = "vfio-pci"
        self.vf_assign_method = "vfio-pci"
        """
        If self.vf_driver == 'pci-stub', self.vf_assign_method = 'pci-assign'
        """

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.restore_interfaces()

    def prepare_l3fwd_power(self, use_dut):
        """
        Compile dpdk-l3fwd-power
        """
        out = use_dut.build_dpdk_apps("./examples/l3fwd-power")
        self.path = use_dut.apps_name["l3fwd-power"]
        self.verify("Error" not in out, "compilation error")

    def send_packet(self, mac, testinterface, use_dut):
        """
        Send a packet and verify
        """
        pkt = Packet(pkt_type="UDP")
        pkt.config_layer("ether", {"dst": mac, "src": self.tester_mac})
        pkt.send_pkt(self.tester, tx_port=testinterface)
        self.out2 = use_dut.get_session_output(timeout=2)

    def send_packet_loop(self, mac, testinterface, use_dut, ip_addr):
        """
        Send a packet and verify
        """
        pkt = Packet(pkt_type="UDP")
        pkt.config_layer("ether", {"dst": mac, "src": self.tester_mac})
        pkt.config_layer("ipv4", {"dst": "2.1.1.5", "src": "2.1.1.%s" % ip_addr})
        pkt.send_pkt(self.tester, tx_port=testinterface)
        self.out2 = use_dut.get_session_output(timeout=2)

    def set_NIC_link(self):
        """
        When starting l3fwd-power on vf, ensure that PF link is up
        """
        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]["intf"]
        self.dut.send_expect("ifconfig %s up" % self.host_intf, "#", 3)

    def begin_l3fwd_power(self, use_dut):
        """
        begin l3fwd-power
        """
        cmd_vhost_net = (
            self.path
            + "-n %d -c %s" % (use_dut.get_memory_channels(), self.core_mask_user)
            + " -- -P -p 1 --config='(0,0,%s)'" % self.core_user
        )
        try:
            self.logger.info("Launch l3fwd_sample sample:")
            self.out = use_dut.send_expect(cmd_vhost_net, "Link up", 60)
            if "Error" in self.out:
                raise Exception("Launch l3fwd-power sample failed")
            else:
                self.logger.info("Launch l3fwd-power sample finished")
        except Exception as e:
            self.logger.error(
                "ERROR: Failed to launch  l3fwd-power sample: %s" % str(e)
            )

    def begin_l3fwd_power_multi_queues(self, use_dut):
        """
        begin l3fwd-power
        """
        config_info = ""
        for queue in range(self.queues):
            if config_info != "":
                config_info += ","
            config_info += "(0,%d,%d)" % (queue, queue)
        cmd_vhost_net = (
            self.path
            + "-l 0-%d -n 4 -- -P -p 0x1" % queue
            + " --config='%s'" % config_info
        )
        try:
            self.logger.info("Launch l3fwd_sample sample:")
            self.out = use_dut.send_expect(
                cmd_vhost_net, "Checking link statusdone", 60
            )
            self.logger.info(self.out)
            if "Error" in self.out:
                raise Exception("Launch l3fwd-power sample failed")
            else:
                self.logger.info("Launch l3fwd-power sample finished")
        except Exception as e:
            self.logger.error("ERROR: Failed to launch l3fwd-power sample: %s" % str(e))

    def setup_vm_env(self, driver="default"):
        """
        Start a vm using a virtual NIC
        """
        if self.env_done:
            return
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]

        self.host_intf0 = self.dut.ports_info[self.used_dut_port_0]["intf"]
        # set vf mac
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf0, self.vf0_mac), "# "
        )

        for port in self.sriov_vfs_port_0:
            port.bind_driver(self.vf_driver)

        vf0_prop_0 = {"opt_host": self.sriov_vfs_port_0[0].pci}
        self.vm0 = VM(self.dut, "vm0", "vf_interrupt_pmd")
        self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop_0)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM ENV failed")
            else:
                self.verify(
                    self.vm0_dut.ports_info[0]["intf"] != "N/A", "Not interface"
                )
        except Exception as e:
            self.destroy_vm_env()
            self.logger.error("Failure for %s" % str(e))

        self.env_done = True

    def destroy_vm_env(self):
        """
        destroy vm environment
        """
        if getattr(self, "vm0", None):
            self.vm0_dut.kill_all()
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, "used_dut_port_0", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            self.used_dut_port_0 = None

        self.env_done = False

    def VF0_bind_vfio_pci(self):
        """
        Bind VF0 to vfio-pci
        """
        self.vm0_dut.send_expect("modprobe -r vfio_iommu_type1", "#", 3)
        self.vm0_dut.send_expect("modprobe -r vfio", "#", 3)
        self.vm0_dut.send_expect("modprobe vfio enable_unsafe_noiommu_mode=1", "#", 3)
        self.vm0_dut.send_expect("modprobe vfio-pci", "#", 3)
        self.vm0_dut.bind_interfaces_linux(driver="vfio-pci")

    def test_nic_interrupt_VM_vfio_pci(self):
        """
        Check for interrupts within the VM
        """
        self.setup_vm_env()
        self.prepare_l3fwd_power(self.vm0_dut)
        self.vm0_dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf0, self.vf0_mac), "# "
        )
        self.VF0_bind_vfio_pci()
        cores = "1S/1C/1T"
        core_list = self.vm0_dut.get_core_list(cores)
        core_user = core_list[0]
        core_mask_user = utils.create_mask(core_list)

        cmd = self.path + "-c %s -n %d -- -P  -p 0x01 --config='(0,0,%s)'" % (
            core_mask_user,
            self.vm0_dut.get_memory_channels(),
            core_user,
        )
        self.vm0_dut.send_expect(cmd, "Checking link statusdone", 60)
        self.send_packet(self.vf0_mac, self.rx_intf_0, self.vm0_dut)
        self.destroy_vm_env()
        self.verify(
            "lcore %s is waked up from rx interrupt on port 0" % core_user in self.out2,
            "Wake up failed",
        )
        self.verify(
            "lcore %s sleeps until interrupt triggers" % core_user in self.out2,
            "lcore %s not sleeps" % core_user,
        )

    def test_nic_interrupt_VF_vfio_pci(self, driver="default"):
        """
        Check Interrupt for VF with vfio driver
        """
        self.prepare_l3fwd_power(self.dut)
        self.set_NIC_link()
        # generate VF and bind to vfio-pci
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        for port in self.sriov_vfs_port_0:
            port.bind_driver("vfio-pci")
        # set vf mac
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf, self.vf_mac), "# "
        )
        self.begin_l3fwd_power(self.dut)
        self.send_packet(self.vf_mac, self.rx_intf_0, self.dut)
        self.verify(
            "lcore %s is waked up from rx interrupt on port 0" % self.core_user
            in self.out2,
            "Wake up failed",
        )
        self.verify(
            "lcore %s sleeps until interrupt triggers" % self.core_user in self.out2,
            "lcore %s not sleeps" % self.core_user,
        )

    def test_nic_multi_queues_interrupt_VF_vfio_pci(self, driver="default"):
        """
        Check Interrupt for VF with vfio driver, need test with i40e driver
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_25G-25G_SFP28",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
                "I40E_10G-10G_BASE_T_BC",
            ],
            "%s nic port not support vf multi-queues interrupt" % str(self.nic),
        )
        self.queues = 4
        self.prepare_l3fwd_power(self.dut)
        self.set_NIC_link()
        # generate VF and bind to vfio-pci
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        for port in self.sriov_vfs_port_0:
            port.bind_driver("vfio-pci")
        # set vf mac
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf, self.vf_mac), "# "
        )
        self.begin_l3fwd_power_multi_queues(self.dut)
        stroutput = ""
        for ip in range(2, 30):
            self.send_packet_loop(self.vf_mac, self.rx_intf_0, self.dut, ip)
            stroutput = stroutput + self.out2
        for queue in range(self.queues):
            self.verify(
                "lcore %d is waked up from rx interrupt on port 0" % queue in stroutput,
                "Wake up failed",
            )
            self.verify(
                "lcore %d sleeps until interrupt triggers" % queue in stroutput,
                "lcore %d not sleeps" % queue,
            )

    def test_nic_multi_queues_interrupt_VM_vfio_pci(self):
        """
        Check for interrupts within the VM, need test with i40e driver
        """
        self.verify(
            self.nic
            in [
                "I40E_10G-SFP_XL710",
                "I40E_40G-QSFP_A",
                "I40E_25G-25G_SFP28",
                "I40E_40G-QSFP_B",
                "I40E_10G-SFP_X722",
                "I40E_10G-10G_BASE_T_X722",
                "I40E_10G-10G_BASE_T_BC",
            ],
            "%s nic port not support vf multi-queues interrupt" % str(self.nic),
        )
        self.setup_vm_env()
        self.vm0_dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf0, self.vf0_mac), "# "
        )
        self.queues = 4
        self.prepare_l3fwd_power(self.vm0_dut)
        self.VF0_bind_vfio_pci()
        cores = "1S/4C/1T"
        core_list = self.vm0_dut.get_core_list(cores)
        core_mask_user = utils.create_mask(core_list)
        config_info = ""
        for queue in range(self.queues):
            if config_info != "":
                config_info += ","
            config_info += "(0,%d,%d)" % (queue, queue)
        cmd = (
            self.path
            + "-c %s -n 4 -- -P -p 0x1" % core_mask_user
            + " --config='%s'" % config_info
        )
        self.vm0_dut.send_expect(cmd, "Checking link statusdone", 60)
        stroutput = ""
        for ip in range(2, 30):
            self.send_packet_loop(self.vf0_mac, self.rx_intf_0, self.vm0_dut, ip)
            stroutput = stroutput + self.out2
        self.destroy_vm_env()
        for queue in range(self.queues):
            self.verify(
                "lcore %d is waked up from rx interrupt on port 0" % queue in stroutput,
                "Wake up failed",
            )
            self.verify(
                "lcore %d sleeps until interrupt triggers" % queue in stroutput,
                "lcore %d not sleeps" % queue,
            )

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect(
            "killall %s" % self.path.strip().split("/")[-1], "# ", 10, alt_session=True
        )

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if self.env_done:
            self.destroy_vm_env()
