# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Test VF PF reset
"""
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.qemu_kvm import QEMUKvm
from framework.test_case import TestCase


class TestVfPfReset(TestCase):

    supported_vf_driver = ["vfio-pci"]
    TIMEOUT = 60

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.cores = self.dut.get_core_list("1S/4C/1T")
        self.coremask = utils.create_mask(self.cores)

        # dut mac
        self.dst_mac_intf1 = self.dut.get_mac_address(self.dut_ports[0])
        self.dst_mac_intf2 = self.dut.get_mac_address(self.dut_ports[1])

        # tester txport
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.tester_intf = self.tester.get_interface(txport)
        self.tester_mac = self.tester.get_mac(txport)

        # dut intf
        self.intf_0 = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pci_0 = self.dut.ports_info[self.dut_ports[0]]["pci"].split(":")

        self.intf_1 = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pci_1 = self.dut.ports_info[self.dut_ports[0]]["pci"].split(":")

        self.dut.send_expect("modprobe vfio-pci", "#")
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")

        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]

        self.host_intf_0 = self.dut.ports_info[self.used_dut_port_0]["intf"]
        self.host_intf_1 = self.dut.ports_info[self.used_dut_port_1]["intf"]

        tester_port_0 = self.tester.get_local_port(self.used_dut_port_0)
        self.tester_intf_0 = self.tester.get_interface(self.used_dut_port_0)
        self.tester_mac_0 = self.tester.get_mac(self.used_dut_port_0)

        tester_port_1 = self.tester.get_local_port(self.used_dut_port_1)
        self.tester_intf_1 = self.tester.get_interface(self.used_dut_port_1)
        self.tester_mac_1 = self.tester.get_mac(self.used_dut_port_1)

        self.vf_mac1 = "00:11:22:33:44:11"
        self.vf_mac2 = "00:11:22:33:44:12"
        # Bind to default driver
        self.bind_nic_driver(self.dut_ports, driver="")
        # Init pmd first
        self.pmd_output = PmdOutput(self.dut)
        # Init pmd second
        session_second = self.dut.new_session()
        self.pmd_output_2 = PmdOutput(self.dut, session_second)

    def set_up(self):
        """
        Run before each test case.
        """
        # ice enable vf-vlan-pruning flag
        self.flag = "vf-vlan-pruning"
        self.default_stats = self.dut.get_priv_flags_state(self.host_intf_0, self.flag)
        if self.is_eth_series_nic(800) and self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s on" % (self.host_intf_0, self.flag),
                "# ",
            )

        # PF new session
        self.dut_new_session = self.dut.new_session("pf")
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 2, driver="")
        out = self.set_priv_flags_state(self.host_intf_0, "on")
        self.verify(out == "on", "link-down-on-close flag is not enable.")
        out = self.set_priv_flags_state(self.host_intf_1, "on")
        self.verify(out == "on", "link-down-on-close flag is not enable.")
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]

        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_driver)

    def create_vf_port(self, port, vfs_num, driver=""):
        self.dut.generate_sriov_vfs_by_port(port, vfs_num, driver=driver)
        self.sriov_vfs_port_general = self.dut.ports_info[port]["vfs_port"]

        for port in self.sriov_vfs_port_general:
            port.bind_driver(self.vf_driver)

    def reset_Pf(self, host_intf):
        """
        Reset PF
        """
        # Set PF down
        self.dut_new_session.send_expect(f"ifconfig {host_intf} down", "# ")
        # Check link status down
        self.check_link_status(host_intf, "down")
        # Set PF up
        self.dut_new_session.send_expect(f"ifconfig {host_intf} up", "# ")
        # check link status up
        self.check_link_status(host_intf, "up")

    def ip_link_set(self, host_intf=None, cmd=None, port=None, types=None, value=0):
        if host_intf is None or cmd is None or port is None or types is None:
            return
        set_command = f"ip link set {host_intf} {cmd} {port} {types} {value}"
        self.dut.send_expect(set_command, "# ", self.TIMEOUT)

    def check_link_status(self, host_intf, status):
        retry_times = 20
        while retry_times > 0:
            set_command = f"ethtool {host_intf}"
            out = self.dut_new_session.send_expect(set_command, "# ", self.TIMEOUT)
            pattern = "Link detected:\s+(\w+)"
            regex = re.compile(pattern)
            mo = regex.search(out)
            if mo is None:
                self.verify(False, "Ethtool check Link status not obtained!")
            link_status = mo.group(1)
            if status == "down":
                status = "no"
            else:
                status = "yes"
            if link_status == status:
                break
            retry_times -= 1
            time.sleep(1)
        self.verify(link_status == status, f"Link is not {status}")

    def set_priv_flags_state(self, host_intf, flag):
        """
        enable link-down-on-close flag
        """
        set_flag = f"ethtool --set-priv-flags {host_intf} link-down-on-close {flag}"
        self.dut_new_session.send_expect(set_flag, "# ", timeout=self.TIMEOUT)
        check_flag = f"ethtool --show-priv-flags {host_intf}"
        res = self.dut_new_session.send_expect(check_flag, "# ", timeout=self.TIMEOUT)

        pattern = r"link-down-on-close\s+:\s+(\w+)"
        regex = re.compile(pattern)
        mo = regex.search(res)

        if mo is None:
            self.verify(False, "enable link-down-on-close flag failed.")

        flag = mo.group(1)
        if "on" in flag:
            return "on"
        if "off" in flag:
            return "off"

    def send_packet(self, mac, pkt_lens=64, num=1, vlan_id="", tx_port="", vm=False):
        if vlan_id == "":
            pkt = Packet(pkt_type="TCP", pkt_len=pkt_lens)
            pkt.config_layer("ether", {"dst": mac, "src": self.tester_mac})
            pkt.send_pkt(self.tester, tx_port=tx_port, count=num)
        else:
            pkt = Packet(pkt_type="VLAN_UDP", pkt_len=pkt_lens)
            pkt.config_layer("ether", {"dst": mac, "src": self.tester_mac})
            pkt.config_layer("vlan", {"vlan": vlan_id})
            pkt.send_pkt(self.tester, tx_port=tx_port, count=num)
        if vm:
            if self.running_case == "test_vfs_passed_through_to_1VM":
                out = self.vm0_dut.get_session_output(timeout=10)
            if self.running_case == "test_2vfs_passed_through_to_2VM":
                out = self.vm1_dut.get_session_output(timeout=10)
        else:
            out = self.dut.get_session_output(timeout=10)
        return out

    def verify_send_packets(
        self,
        tester_intf,
        vf_mac,
        expect_value=10,
        count=10,
        vlan="",
        tx_port="",
        vm=False,
    ):
        filter = [{"layer": "ether", "config": {"dst": "not ff:ff:ff:ff:ff:ff"}}]
        inst = self.tester.tcpdump_sniff_packets(tester_intf, filters=filter)
        if vlan:
            out = self.send_packet(
                vf_mac, num=count, vlan_id=vlan, tx_port=tx_port, vm=vm
            )
            if expect_value:
                self.verify(
                    "received" in out, "Failed to received vlan packet with PF!"
                )
        else:
            out = self.send_packet(vf_mac, num=count, tx_port=tx_port, vm=vm)
            if expect_value:
                self.verify(
                    "received" in out, "Failed to received vlan packet with PF!"
                )
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        self.verify(
            len(pkts) == expect_value,
            "Send random packets vf wrong receive expected packets!",
        )

    def start_tester_tcpdump(self, tester_intf):
        """
        tester start tcpdump
        """
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            f"tcpdump -i {tester_intf} -n -e -x -v -w getPackageByTcpdump.cap 2> /dev/null&",
            "# ",
        )

    def get_tester_tcpdump_package(self):
        """
        tester get tcpdump package
        """
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect(
            "tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap", "# "
        )

    def reset_vf_ports(self, pmd_output, port="all"):
        """
        reset vf
        """
        pmd_output.execute_cmd("stop")
        pmd_output.execute_cmd(f"port stop {port}")
        pmd_output.execute_cmd(f"port reset {port}")
        pmd_output.execute_cmd(f"port start {port}")
        pmd_output.execute_cmd("start")
        pmd_output.execute_cmd(f"show port info {port}")

    def setup_vm_env(self):
        """
        setup vm
        """
        vf0_prop_1 = {"opt_host": self.sriov_vfs_port[0].pci}
        vf0_prop_2 = {"opt_host": self.sriov_vfs_port[1].pci}
        self.vm0 = QEMUKvm(self.dut, "vm0", "vf_pf_reset")
        if self.running_case == "test_2vfs_passed_through_to_2VM":
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop_1)
        else:
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop_1)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop_2)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.destroy_vm_env()
            self.logger.error("Failure for %s" % str(e))
        self.vm0_testpmd = PmdOutput(self.vm0_dut)
        self.vm0_vf0_mac = self.vm0_dut.get_mac_address(0)
        if self.running_case == "test_2vfs_passed_through_to_2VM":
            self.vm0_intf0 = self.vm0_dut.ports_info[0]["intf"]
        else:
            self.vm0_intf0 = self.vm0_dut.ports_info[0]["intf"]
            self.vm0_intf1 = self.vm0_dut.ports_info[1]["intf"]
        self.vm0_dut.restore_interfaces_linux()
        if self.vm0_intf0 == "N/A":
            self.vm0_intf0 = self.check_intf_exists(0)
        self.vm0_dut.send_expect("systemctl stop NetworkManager", "# ", 60)

        if self.running_case == "test_2vfs_passed_through_to_2VM":
            vf1_prop_5 = {"opt_host": self.sriov_vfs_port[1].pci}
            self.vm1 = QEMUKvm(self.dut, "vm1", "vf_pf_reset")
            self.vm1.set_vm_device(driver=self.vf_assign_method, **vf1_prop_5)
            try:
                self.vm1_dut = self.vm1.start()
                if self.vm1_dut is None:
                    raise Exception("Set up VM1 ENV failed!")
            except Exception as e:
                self.destroy_vm_env()
                raise Exception(e)
            self.vm1_testpmd = PmdOutput(self.vm1_dut)
            self.vm1_vf0_mac = self.vm1_dut.get_mac_address(0)
            self.vm1_intf0 = self.vm1_dut.ports_info[0]["intf"]
            self.vm1_dut.restore_interfaces_linux()
            if self.vm1_intf0 == "N/A":
                self.vm0_intf0 = self.check_intf_exists(1)
            self.vm1_dut.send_expect("systemctl stop NetworkManager", "# ", 60)

    def check_intf_exists(self, port=None):
        """
        check vm intf name whether it exists
        """
        if port is not None:
            pci = self.vm0_dut.ports_info[port]["pci"]
            domain_id = pci.split(":")[0]
            bus_id = pci.split(":")[1]
            devfun_id = pci.split(":")[2]
            retry_times = 20
            while retry_times > 0:
                cmd_unbind = f"echo {pci} > /sys/bus/pci/devices/{domain_id}\:{bus_id}\:{devfun_id}/driver/unbind"
                self.vm0_dut.send_expect(cmd_unbind, "# ")
                cmd_bind = f"echo {pci} > /sys/bus/pci/drivers/iavf/bind"
                self.vm0_dut.send_expect(cmd_bind, "# ")
                cmd_net = f"ls --color=never /sys/bus/pci/devices/{domain_id}\:{bus_id}\:{devfun_id}/net"
                intf_name = self.vm0_dut.send_expect(cmd_net, "# ")
                if "No such file or directory" not in intf_name:
                    return intf_name
                retry_times -= 1

    def destroy_vm_env(self):
        """
        destroy vm
        """
        if self.running_case in [
            "test_vfs_passed_through_to_1VM",
            "test_2vfs_passed_through_to_2VM",
        ]:
            if getattr(self, "vm0", None):
                self.vm0_dut.kill_all()
                self.vm0_testpmd = None
                self.vm0_dut_ports = None
                # destroy vm0
                self.vm0.stop()
                self.vm0 = None
            if getattr(self, "vm1", None):
                self.vm1_dut.kill_all()
                self.vm1_testpmd = None
                self.vm1_dut_ports = None
                # destroy vm1
                self.vm1.stop()
                self.vm1 = None

    def test_create_2vfs_on_1pf(self):
        """
        create two vfs on one pf
        """
        # Set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )

        # Set the VLAN id of VF0 and VF1
        self.ip_link_set(
            host_intf=self.host_intf_0, cmd="vf", port=0, types="vlan", value="1"
        )
        self.ip_link_set(
            host_intf=self.host_intf_0, cmd="vf", port=1, types="vlan", value="1"
        )

        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci],
            param=param,
        )

        # Input pmd command
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("set allmulti all on")
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("set verbose 1")
        out = self.pmd_output.execute_cmd("show port info all")
        self.logger.info(out)
        # Diable Promiscuous mode and enable Allmulticast mode
        self.verify(
            "Promiscuous mode: disabled" in out, "disable promiscuous mode failed."
        )
        self.verify(
            "Allmulticast mode: enabled" in out, "enabled allmulticast mode failed."
        )

        # The packets can be received
        # By one VF and can be forward to another VF correctly
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
        )

        # Set pf down
        self.dut_new_session.send_expect(f"ifconfig {self.host_intf_0} down", "# ")
        # Send the same 10 packets with scapy from tester,
        # The vf cannot receive any packets, including vlan=0 and vlan=1
        self.check_link_status(self.host_intf_0, "down")

        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=0,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=0,
            count=10,
            vlan=0,
            tx_port=self.tester_intf_0,
        )

        # Set pf up
        self.dut_new_session.send_expect(f"ifconfig {self.host_intf_0} up", "# ")
        # Send the same 10 packets with scapy from tester, verify the packets can be
        # Received by one VF and can be forward to another VF correctly
        self.check_link_status(self.host_intf_0, "up")

        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
        )

        # Reset the vfs, run the command
        self.reset_vf_ports(self.pmd_output)
        out = self.pmd_output.execute_cmd("show port info all")
        self.verify(
            "Promiscuous mode: disabled" in out,
            "disable promiscuous mode failed after reset vf.",
        )
        self.verify(
            "Allmulticast mode: enabled" in out,
            "enabled Allmulticast mode failed after reset vf.",
        )
        # Send the same 10 packets with scapy from tester, verify the packets can be
        # Received by one VF and can be forward to another VF correctly
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
        )
        self.pmd_output.quit()

    def test_create_2vfs_on_1pf_separately_pmd(self):
        """
        create two vfs on one pf, run testpmd separately
        """
        # Set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )

        # Launch pmd
        eal_param = "--socket-mem 1024,1024"
        param = "--eth-peer=0,00:11:22:33:44:12"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            eal_param=eal_param,
            ports=[self.sriov_vfs_port[0].pci],
            param=param,
        )

        # Launch second pmd
        eal_param = "--socket-mem 1024,1024"
        self.pmd_output_2.start_testpmd(
            cores="1S/4C/1T",
            prefix="pmd_output_2",
            eal_param=eal_param,
            ports=[self.sriov_vfs_port[1].pci],
        )

        # Set fwd mode on vf0
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("set verbose 1")

        # Set rxonly mode on vf1
        self.pmd_output_2.execute_cmd("set fwd rxonly")
        self.pmd_output_2.execute_cmd("start")
        self.pmd_output_2.execute_cmd("set verbose 1")

        # Send packets with scapy from tester, vf0 can forward the packets to vf1.
        out = self.send_packet(self.vf_mac1, tx_port=self.tester_intf_0, num=10)
        self.verify("received" in out, "Failed to received vlan packet with VF0!")
        out_second = self.pmd_output_2.get_output()
        self.verify("received" in out_second, "Vf0 forward failed the packets to vf1.")

        # Reset pf, don't reset vf0 and vf1, send the packets,vf0 can forward the packet to vf1.
        self.reset_Pf(self.host_intf_0)
        out = self.send_packet(self.vf_mac1, tx_port=self.tester_intf_0, num=10)
        self.verify("received" in out, "Failed to received vlan packet with VF0!")
        out_second = self.pmd_output_2.get_output()
        self.verify(
            "received" in out_second,
            "Vf0 forward failed the packets to vf1 after reset PF.",
        )

        # Reset vf0 and vf1, send the packets,vf0 can forward the packet to vf1.
        self.reset_vf_ports(self.pmd_output)
        self.reset_vf_ports(self.pmd_output_2)
        out = self.send_packet(self.vf_mac1, tx_port=self.tester_intf_0, num=10)
        self.verify("received" in out, "Failed to received vlan packet with VF0!")
        out_second = self.pmd_output_2.get_output()
        self.verify(
            "received" in out_second,
            "Vf0 forward failed the packets to vf1 after reset VF0 VF1.",
        )

    def test_create_1vf_on_each_pf(self):
        """
        create one vf on each pf
        """
        # Other pf create vf
        self.create_vf_port(self.used_dut_port_1, 1)
        # Set mac1 vf 0 of pf1, mac2 vf 0 of pf2
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_1,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac2,
        )

        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port_general[0].pci],
            param=param,
        )

        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("start")
        self.pmd_output.execute_cmd("set verbose 1")
        # Send packets with scapy from tester, vfs can fwd the packets normally.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )

        # Reset pf0 and pf1, don't reset vf0 and vf1, send the packets,vfs can fwd the packets normally.
        self.reset_Pf(self.host_intf_0)
        self.reset_Pf(self.host_intf_1)
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )

        # Reset vf0 and vf1, send the packets, vfs can fwd the packets normally.
        self.reset_vf_ports(self.pmd_output)
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )

        self.pmd_output.quit()
        self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)

    def test_vlan_rx_restore_vf_reset_all_ports(self):
        """
        vlan rx restore -- vf reset all ports
        """
        # Set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )

        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci],
            param=param,
        )
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        # Add vlan on both ports
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.pmd_output.execute_cmd("vlan set filter on 1")
        self.pmd_output.execute_cmd("rx_vlan add 1 1")
        self.pmd_output.execute_cmd("start")

        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:11 with vlan 1.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:12 with vlan 1.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:12 with vlan 2,can't receive any packets.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=0,
            count=10,
            vlan=2,
            tx_port=self.tester_intf,
        )

    def test_vlan_rx_restore_vf_reset_1port(self):
        """
        vlan rx restore -- vf reset one port
        """
        # Set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )

        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci],
            param=param,
        )
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        # Add vlan on both ports
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.pmd_output.execute_cmd("vlan set filter on 1")
        self.pmd_output.execute_cmd("rx_vlan add 1 1")
        self.pmd_output.execute_cmd("start")
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:11 with vlan 1.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:12 with vlan 1.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )

        # Reset pf0 and pf1, don't reset vf0 and vf1, send the packets,vfs can fwd the packets normally.
        self.reset_Pf(self.host_intf_0)
        # Reset vf0
        self.reset_vf_ports(self.pmd_output, port="0")
        # Send packets from tester
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        # Reset vf1
        self.reset_vf_ports(self.pmd_output, port="1")
        # Send packets from tester
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )

    def test_vlan_rx_restore_create_vf_each_pf(self):
        """
        vlan rx restore -- create one vf on each pf
        """
        # Other pf create vf
        self.create_vf_port(self.used_dut_port_1, 1)
        # Set mac1 vf 0 of pf1, mac2 vf 0 of pf2
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_1,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac2,
        )

        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port_general[0].pci],
            param=param,
        )
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        # Add vlan on both ports
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("rx_vlan add 1 0")
        self.pmd_output.execute_cmd("vlan set filter on 1")
        self.pmd_output.execute_cmd("rx_vlan add 1 1")
        self.pmd_output.execute_cmd("start")
        # Send packets with scapy from tester
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:11 with vlan 1.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )
        # Send mac 00:11:22:33:44:11 with vlan 2,can't receive any packets.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=0,
            count=10,
            vlan=2,
            tx_port=self.tester_intf,
        )

        # Remove vlan 0 on vf1, vf0 can receive the packets, but vf1 can't transmit the packets
        self.pmd_output.execute_cmd("rx_vlan rm 0 1")
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )

        # Reset pf, don't reset vf, send packets from tester
        self.reset_Pf(self.host_intf_0)
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )

        # Reset both vfs, send packets from tester
        self.reset_vf_ports(self.pmd_output)
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf,
        )

    def test_vlan_tx_restore(self):
        """
        vlan tx restore
        """
        # ice nic need set tx vf spoofchk off
        if self.kdriver == "ice":
            self.dut.send_expect(
                "ip link set dev {} vf 1 spoofchk off".format(self.host_intf_0), "# "
            )
        # Set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )
        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port[1].pci],
            param=param,
        )
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("vlan set filter on 0")
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("vlan set strip off 0")
        self.pmd_output.execute_cmd("set nbport 2")
        self.pmd_output.execute_cmd("port stop 1")
        self.pmd_output.execute_cmd("tx_vlan set 1 51")
        self.pmd_output.execute_cmd("port start 1")
        self.pmd_output.execute_cmd("start")

        # Send packets with scapy from tester, check the packet received, the packet is configured with vlan 51
        self.start_tester_tcpdump(self.tester_intf_0)
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        out = self.get_tester_tcpdump_package()
        self.verify("vlan 51" in out, "The packet is not configured with vlan 51!")

        # Reset the pf, then reset the two vfs
        # Send the same packet with no vlan tag,
        # Check packets received by tester, the packet is configured with vlan 51.
        self.reset_Pf(self.host_intf_0)
        self.reset_vf_ports(self.pmd_output)
        self.start_tester_tcpdump(self.tester_intf_0)
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf,
        )
        out = self.get_tester_tcpdump_package()
        self.verify("vlan 51" in out, "The packet is not configured with vlan 51!")

    def test_mac_address_restore(self):
        """
        MAC address restore
        """
        # Other pf create vf
        self.create_vf_port(self.used_dut_port_1, 1)
        # Launch pmd
        param = "--portmask=0x3"
        self.pmd_output.start_testpmd(
            cores="1S/4C/1T",
            ports=[self.sriov_vfs_port[0].pci, self.sriov_vfs_port_general[0].pci],
            param=param,
        )
        self.pmd_output.execute_cmd("mac_addr add 0 00:11:22:33:44:11")
        self.pmd_output.execute_cmd("mac_addr add 1 00:11:22:33:44:12")
        self.pmd_output.execute_cmd("set promisc all off")
        self.pmd_output.execute_cmd("set fwd mac")
        self.pmd_output.execute_cmd("set verbose 1")
        self.pmd_output.execute_cmd("start")

        # Send packets with scapy from tester
        # Vfs can forward both of the two type packets
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_1,
        )

        # Reset pf0 and pf1, don't reset vf, send packets from tester
        # Vfs can forward both of the two type packets
        self.reset_Pf(self.host_intf_0)
        self.reset_Pf(self.host_intf_1)
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_1,
        )

        # Reset vf0 and vf1, send the two packets
        # Vfs can forward both of the two type packets
        self.reset_vf_ports(self.pmd_output)
        self.pmd_output.execute_cmd("mac_addr add 0 00:11:22:33:44:11")
        self.pmd_output.execute_cmd("mac_addr add 1 00:11:22:33:44:12")
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_1,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_1,
        )

    def test_vfs_passed_through_to_1VM(self):
        """
        vf reset (two vfs passed through to one VM)
        """
        # Setup vm
        try:
            self.setup_vm_env()
        except Exception as e:
            self.destroy_vm_env()

        self.vm0_dut.send_expect("ifconfig %s up " % self.vm0_intf0, "#")
        self.vm0_dut.send_expect("ifconfig %s up " % self.vm0_intf1, "#")
        for port in self.vm0_dut.ports_info:
            port["port"].bind_driver("vfio-pci")
        # Launch pmd
        param = "--portmask=0x3"
        self.vm0_testpmd.start_testpmd(
            cores="1S/4C/1T",
            ports=[
                self.vm0_dut.ports_info[0]["pci"],
                self.vm0_dut.ports_info[1]["pci"],
            ],
            param=param,
        )
        self.vm0_testpmd.execute_cmd("mac_addr add 0 00:11:22:33:44:11")
        self.vm0_testpmd.execute_cmd("mac_addr add 0 00:11:22:33:44:12")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")
        # Send packets with scapy from tester
        # Vfs can forward both of the two type packets
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )

        # Reset pf0 and pf1, don't reset vf, send packets from tester
        self.reset_Pf(self.host_intf_0)
        self.reset_Pf(self.host_intf_1)
        # Vfs can forward both of the two type packets
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )

        # Reset vf0 and vf1, send the two packets
        self.reset_vf_ports(self.vm0_testpmd)
        self.vm0_testpmd.execute_cmd("mac_addr add 0 00:11:22:33:44:11")
        self.vm0_testpmd.execute_cmd("mac_addr add 0 00:11:22:33:44:12")
        # Vfs can forward both of the two type packets
        # Send mac 00:11:22:33:44:11 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        # Send mac 00:11:22:33:44:12 with out vlan.
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac2,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )

        self.vm0_testpmd.quit()

    def test_2vfs_passed_through_to_2VM(self):
        """
        two vfs passed through to two VM
        """
        # IP link set mac
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="mac",
            value=self.vf_mac1,
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=1,
            types="mac",
            value=self.vf_mac2,
        )
        try:
            self.setup_vm_env()
        except Exception as e:
            self.destroy_vm_env()

        self.vm0_dut.send_expect("ifconfig %s up " % self.vm0_intf0, "#")
        self.vm1_dut.send_expect("ifconfig %s up " % self.vm1_intf0, "#")
        for port in self.vm0_dut.ports_info:
            port["port"].bind_driver("vfio-pci")
        for port in self.vm1_dut.ports_info:
            port["port"].bind_driver("vfio-pci")
        # Vm0 start testpmd
        param = f"--eth-peer=0,{self.vf_mac2}"
        self.vm0_testpmd.start_testpmd(
            cores="1S/4C/1T", ports=[self.vm0_dut.ports_info[0]["pci"]], param=param
        )
        self.vm0_testpmd.execute_cmd("vlan set filter on 0")
        self.vm0_testpmd.execute_cmd("rx_vlan add 1 0")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")
        # Vm1 start testpmd
        self.vm1_testpmd.start_testpmd(
            cores="1S/4C/1T", ports=[self.vm1_dut.ports_info[0]["pci"]]
        )
        self.vm1_testpmd.execute_cmd("vlan set filter on 0")
        self.vm1_testpmd.execute_cmd("rx_vlan add 1 0")
        self.vm1_testpmd.execute_cmd("set fwd mac")
        self.vm1_testpmd.execute_cmd("set verbose 1")
        self.vm1_testpmd.execute_cmd("start")
        # Send packets with scapy from tester,vf0 can forward the packets to vf1
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        # Reset pf, don't reset vf0 and vf1, send the two packets,
        # Vf0 can forward both of the two type packets to VF1
        self.reset_Pf(self.host_intf_0)
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        # Reset vf0 and vf1, send the two packets,
        # Vf0 can forward both of the two type packets to VF1.
        self.reset_vf_ports(self.vm0_testpmd)
        self.reset_vf_ports(self.vm1_testpmd)
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        self.verify_send_packets(
            self.tester_intf_0,
            self.vf_mac1,
            expect_value=10,
            count=10,
            vlan=1,
            tx_port=self.tester_intf_0,
            vm=True,
        )
        self.vm0_testpmd.quit()
        self.vm1_testpmd.quit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_vm_env()
        self.dut.kill_all()
        self.pmd_output.quit()
        self.dut_new_session.send_expect(f"ifconfig {self.host_intf_0} up", "# ")
        self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
        self.bind_nic_driver(self.dut_ports, driver="")
        if self.is_eth_series_nic(800) and self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.host_intf_0, self.flag, self.default_stats),
                "# ",
            )

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        pass
