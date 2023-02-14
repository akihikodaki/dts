# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020-2022 Intel Corporation
#

import re
import string
import time

from scapy.contrib.lldp import LLDPDU, LLDPDUManagementAddress
from scapy.contrib.mpls import MPLS
from scapy.contrib.nsh import NSH
from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.inet6 import IPv6, IPv6ExtHdrFragment, IPv6ExtHdrRouting
from scapy.layers.l2 import ARP, GRE, Dot1Q, Ether
from scapy.layers.sctp import SCTP
from scapy.layers.vxlan import VXLAN
from scapy.packet import Raw

import framework.utils as utils
from framework.crb import Crb
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import DPDK_DCFMODE_SETTING, HEADER_SIZE, load_global_setting
from framework.test_case import TestCase, check_supported_nic, skip_unsupported_pkg
from framework.utils import GREEN, RED
from framework.virt_common import VM
from nics.net_device import NetDevice

VM_CORES_MASK = "all"
DEFAULT_MTU = 1500
TSO_MTU = 9000


class TestVfOffload(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()["vf_driver"]
        if self.vf_driver is None:
            self.vf_driver = "pci-stub"
        self.verify(self.vf_driver in self.supported_vf_driver, "Unsupported vf driver")
        if self.vf_driver == "pci-stub":
            self.vf_assign_method = "pci-assign"
        else:
            self.vf_assign_method = "vfio-pci"
            self.dut.send_expect("modprobe vfio-pci", "#")
        self.dcf_mode = load_global_setting(DPDK_DCFMODE_SETTING)

        self.setup_2pf_2vf_1vm_env_flag = 0
        self.setup_2pf_2vf_1vm_env(driver="")
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")
        self.portMask = utils.create_mask(self.vm0_dut_ports)
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.tester.send_expect(
            "ifconfig %s mtu %s"
            % (
                self.tester.get_interface(
                    self.tester.get_local_port(self.dut_ports[0])
                ),
                TSO_MTU,
            ),
            "# ",
        )

    def set_up(self):
        pass

    def ip_link_set(self, host_intf=None, cmd=None, port=None, types=None, value=0):
        if host_intf is None or cmd is None or port is None or types is None:
            return
        set_command = f"ip link set {host_intf} {cmd} {port} {types} {value}"
        out = self.dut.send_expect(set_command, "# ")
        if "RTNETLINK answers: Invalid argument" in out:
            self.dut.send_expect(set_command, "# ")

    def setup_2pf_2vf_1vm_env(self, driver="default"):

        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]["vfs_port"]

        self.host_intf_0 = self.dut.ports_info[self.used_dut_port_0]["intf"]
        self.host_intf_1 = self.dut.ports_info[self.used_dut_port_1]["intf"]

        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="trust",
            value="on",
        )
        self.ip_link_set(
            host_intf=self.host_intf_1,
            cmd="vf",
            port=0,
            types="trust",
            value="on",
        )
        self.ip_link_set(
            host_intf=self.host_intf_0,
            cmd="vf",
            port=0,
            types="spoofchk",
            value="off",
        )
        self.ip_link_set(
            host_intf=self.host_intf_1,
            cmd="vf",
            port=0,
            types="spoofchk",
            value="off",
        )
        try:

            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {"opt_host": self.sriov_vfs_port_0[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port_1[0].pci}

            if driver == "igb_uio":
                # start testpmd without the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                self.host_testpmd.start_testpmd("1S/2C/2T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, "vm0", "vf_offload")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")
            self.vf0_guest_pci = self.vm0.pci_maps[0]["guestpci"]
            self.vf1_guest_pci = self.vm0.pci_maps[1]["guestpci"]

            self.setup_2pf_2vf_1vm_env_flag = 1
        except Exception as e:
            self.destroy_2pf_2vf_1vm_env()
            raise Exception(e)

    def destroy_2pf_2vf_1vm_env(self):
        if getattr(self, "vm0", None):
            # destroy testpmd in vm0
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None

        if getattr(self, "host_testpmd", None):
            self.host_testpmd.execute_cmd("quit", "# ")
            self.host_testpmd = None

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

        self.setup_2pf_2vf_1vm_env_flag = 0

    def launch_testpmd(self, **kwargs):
        dcf_flag = kwargs.get("dcf_flag")
        eal_param = kwargs.get("eal_param") if kwargs.get("eal_param") else ""
        param = kwargs.get("param") if kwargs.get("param") else ""
        if dcf_flag == "enable":
            self.vm0_testpmd.start_testpmd(
                VM_CORES_MASK,
                param=param,
                eal_param=eal_param,
                ports=[self.vf0_guest_pci, self.vf1_guest_pci],
                port_options={
                    self.vf0_guest_pci: "cap=dcf",
                    self.vf1_guest_pci: "cap=dcf",
                },
            )
        else:
            self.vm0_testpmd.start_testpmd(
                VM_CORES_MASK,
                param=param,
                eal_param=eal_param,
            )

    def checksum_enablehw(self, port, dut):
        dut.send_expect("port stop all", "testpmd>")
        dut.send_expect("csum set ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set udp hw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp hw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp hw %d" % port, "testpmd>")
        dut.send_expect("port start all", "testpmd>")

    def checksum_enablehw_tunnel(self, port, dut):
        dut.send_expect("port stop %d" % port, "testpmd>")
        dut.send_expect("csum set ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set udp hw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp hw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-udp hw %d" % port, "testpmd>")
        dut.send_expect("csum parse-tunnel on %d" % port, "testpmd>")
        dut.send_expect("rx_vxlan_port add 4789 %d" % port, "testpmd>")
        dut.send_expect("port start %d" % port, "testpmd>")

    def checksum_enablesw(self, port, dut):
        dut.send_expect("port stop all", "testpmd>")
        dut.send_expect("csum set ip sw %d" % port, "testpmd>")
        dut.send_expect("csum set udp sw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp sw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp sw %d" % port, "testpmd>")
        dut.send_expect("port start all", "testpmd>")

    def tso_enable(self, port, dut):
        dut.send_expect("port stop %d" % port, "testpmd>")
        dut.send_expect("csum set ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set udp hw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp hw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-udp hw %d" % port, "testpmd>")
        dut.send_expect("csum parse-tunnel on %d" % port, "testpmd>")
        dut.send_expect("tso set 800 %d" % port, "testpmd>")
        dut.send_expect("port start %d" % port, "testpmd>")

    def tso_enable_tunnel(self, port, dut):
        dut.send_expect("port stop %d" % port, "testpmd>")
        dut.send_expect("csum set ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set udp hw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp hw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set outer-udp hw %d" % port, "testpmd>")
        dut.send_expect("csum parse-tunnel on %d" % port, "testpmd>")
        dut.send_expect("rx_vxlan_port add 4789 %d" % port, "testpmd>")
        dut.send_expect("tso set 800 %d" % port, "testpmd>")
        dut.send_expect("tunnel_tso set 800 %d" % port, "testpmd>")
        dut.send_expect("port start %d" % port, "testpmd>")

    def filter_packets(self, packets):
        return [
            p
            for p in (packets if packets else [])
            if len(p.layers()) >= 3
            and p.layers()[1] in {IP, IPv6, Dot1Q}
            and p.layers()[2] in {IP, IPv6, Dot1Q, UDP, TCP, SCTP, GRE, MPLS}
            and Raw in p
        ]

    def checksum_validate(self, packets_sent, packets_expected):
        """
        Validate the checksum.
        """
        tx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[0])
        )
        rx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[1])
        )
        sniff_src = self.vm0_testpmd.get_port_mac(0)
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")
        sniff_src = "52:00:00:00:00:00"
        expected_chksum_list = dict()
        result = dict()
        self.tester.send_expect("scapy", ">>> ")
        self.tester.send_expect("from scapy.contrib.gtp import GTP_U_Header", ">>>")
        for packet_type in list(packets_expected.keys()):
            self.tester.send_expect("p = %s" % packets_expected[packet_type], ">>>")
            out = self.tester.send_expect("p.show2()", ">>>")
            chksum = checksum_pattern.findall(out)
            expected_chksum_list[packet_type] = chksum
            print(packet_type, ": ", chksum)

        self.tester.send_expect("exit()", "#")

        self.tester.scapy_background()
        inst = self.tester.tcpdump_sniff_packets(
            intf=rx_interface,
            count=len(packets_sent),
            filters=[{"layer": "ether", "config": {"src": sniff_src}}],
        )

        # Send packet.
        self.tester.scapy_foreground()
        self.tester.scapy_append("from scapy.contrib.gtp import GTP_U_Header")
        for packet_type in list(packets_sent.keys()):
            self.tester.scapy_append(
                'sendp([%s], iface="%s")' % (packets_sent[packet_type], tx_interface)
            )

        self.tester.scapy_execute()
        out = self.tester.scapy_get_result()
        packets_received = self.filter_packets(
            self.tester.load_tcpdump_sniff_packets(inst)
        )
        print(list(packets_received))

        self.verify(
            len(packets_sent) == len(packets_received), "Unexpected Packets Drop"
        )
        for i in range(len(packets_sent)):
            packet_type = list(packets_sent.keys())[i]
            checksum_received = checksum_pattern.findall(
                packets_received[i].show2(dump=True)
            )
            checksum_expected = expected_chksum_list[list(packets_sent.keys())[i]]
            self.logger.debug(f"checksum_received: {checksum_received}")
            self.logger.debug(f"checksum_expected: {checksum_expected}")
            if not len(checksum_expected) == len(checksum_received):
                result[packet_type] = (
                    packet_type
                    + " Failed:"
                    + f"The chksum type {packet_type} length of the actual result is inconsistent with the expected length!"
                )
            elif not (checksum_received == checksum_expected):
                result[packet_type] = (
                    packet_type
                    + " Failed:"
                    + f"The actually received chksum {packet_type} is inconsistent with the expectation"
                )
        return result

    def exec_checksum_offload_enable(self, specific_bitwidth=None):
        """
        Enable HW checksum offload.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=%s " % (self.portMask) + "--enable-rx-cksum " + "",
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        self.vm0_testpmd.execute_cmd("set promisc 1 on")
        self.vm0_testpmd.execute_cmd("set promisc 0 on")

        time.sleep(2)
        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        pkts = {
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IP/SCTP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/SCTP(chksum=0x0)/("X"*48)'
            % (mac, sndIP),
            "IPv6/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
        }

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/UDP()/("X"*46)'
            % (mac, expIP),
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/TCP()/("X"*46)'
            % (mac, expIP),
            "IP/SCTP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s")/SCTP()/("X"*48)'
            % (mac, expIP),
            "IPv6/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP()/("X"*46)'
            % (mac, expIPv6),
            "IPv6/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/TCP()/("X"*46)'
            % (mac, expIPv6),
        }

        self.checksum_enablehw(0, self.vm_dut_0)
        self.checksum_enablehw(1, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd("start")
        result = self.checksum_validate(pkts, pkts_ref)

        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd("stop")
        bad_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 3, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 5, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    def exec_checksum_offload_vlan_enable(self, specific_bitwidth=None):
        """
        Enable HW checksum offload.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=%s " % (self.portMask) + "--enable-rx-cksum " + "",
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        self.vm0_testpmd.execute_cmd("set promisc 1 on")
        self.vm0_testpmd.execute_cmd("set promisc 0 on")

        time.sleep(2)
        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        pkts = {
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s", chksum=0xf)/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s", chksum=0xf)/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IP/SCTP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s", chksum=0xf)/SCTP(chksum=0x0)/("X"*48)'
            % (mac, sndIP),
            "IPv6/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IPv6(src="%s")/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IPv6(src="%s")/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
        }

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s")/UDP()/("X"*46)'
            % (mac, expIP),
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s")/TCP()/("X"*46)'
            % (mac, expIP),
            "IP/SCTP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IP(src="%s")/SCTP()/("X"*48)'
            % (mac, expIP),
            "IPv6/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IPv6(src="%s")/UDP()/("X"*46)'
            % (mac, expIPv6),
            "IPv6/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/Dot1Q(vlan=100)/IPv6(src="%s")/TCP()/("X"*46)'
            % (mac, expIPv6),
        }

        self.checksum_enablehw(0, self.vm_dut_0)
        self.checksum_enablehw(1, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd("start")
        result = self.checksum_validate(pkts, pkts_ref)

        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd("stop")
        bad_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 3, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 5, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    @check_supported_nic(
        ["ICE_100G-E810C_QSFP", "ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP"]
    )
    @skip_unsupported_pkg(["os default"])
    def exec_checksum_offload_tunnel_enable(self, specific_bitwidth=None):
        """
        Enable HW checksum offload.
        Send packet with inner and outer incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=%s " % (self.portMask) + "--enable-rx-cksum " + "",
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("set promisc 1 on")
        self.vm0_testpmd.execute_cmd("set promisc 0 on")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        time.sleep(2)
        port_id_0 = 0
        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        expIP = sndIP
        expIPv6 = sndIPv6

        pkts_outer = {
            "IP/UDP/VXLAN-GPE": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN()',
            "IP/UDP/VXLAN-GPE/ETH": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN() / Ether()',
            "IPv6/UDP/VXLAN-GPE": f'IPv6(src = "{sndIPv6}") / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN()',
            "IPv6/UDP/VXLAN-GPE/ETH": f'IPv6(src = "{sndIPv6}") / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN() / Ether()',
            "IP/GRE": f'IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE()',
            "IP/GRE/ETH": f'IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE() / Ether()',
            "IP/NVGRE/ETH": f'IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IPv6/GRE": f'IPv6(src = "{sndIPv6}", nh = 47) / GRE()',
            "IPv6/GRE/ETH": f'IPv6(src = "{sndIPv6}", nh = 47) / GRE() / Ether()',
            "IPv6/NVGRE/ETH": f'IPv6(src = "{sndIPv6}", nh = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IP/UDP/GTPU": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(dport = 2152, chksum = 0xff) / GTP_U_Header(gtp_type=255, teid=0x123456)',
            "IPv6/UDP/GTPU": f'IPv6(src = "{sndIPv6}") / UDP(dport = 2152, chksum = 0xff) / GTP_U_Header(gtp_type=255, teid=0x123456)',
        }
        pkts_inner = {
            "IP/UDP": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IP/TCP": f'IP(src = "{sndIP}", chksum = 0xff) / TCP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IP/SCTP": f'IP(src = "{sndIP}", chksum = 0xff) / SCTP(sport = 29999, dport = 30000, chksum = 0x0) / Raw("x" * 128)',
            "IPv6/UDP": f'IPv6(src = "{sndIPv6}") / UDP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IPv6/TCP": f'IPv6(src = "{sndIPv6}") / TCP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IPv6/SCTP": f'IPv6(src = "{sndIPv6}") / SCTP(sport = 29999, dport = 30000, chksum = 0x0) / Raw("x" * 128)',
        }

        if self.dcf_mode == "enable":
            pkts_outer.update(
                {
                    "IP/UDP/VXLAN/ETH": f'IP(src = "{sndIP}") / UDP(sport = 4789, dport = 4789, chksum = 0xff) / VXLAN() / Ether()',
                    "IPv6/UDP/VXLAN/ETH": f'IPv6(src = "{sndIPv6}") / UDP(sport = 4789, dport = 4789, chksum = 0xff) / VXLAN() / Ether()',
                }
            )
        pkts = {
            key_outer
            + "/"
            + key_inner: f'Ether(dst="{mac}", src="52:00:00:00:00:00") / '
            + p_outer
            + " / "
            + p_inner
            for key_outer, p_outer in pkts_outer.items()
            for key_inner, p_inner in pkts_inner.items()
        }

        pkts_outer_ref = {
            "IP/UDP/VXLAN-GPE": f'IP(src = "{expIP}") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "IP/UDP/VXLAN-GPE/ETH": f'IP(src = "{expIP}") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "IPv6/UDP/VXLAN-GPE": f'IPv6(src = "{expIPv6}") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "IPv6/UDP/VXLAN-GPE/ETH": f'IPv6(src = "{expIPv6}") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "IP/GRE": f'IP(src = "{expIP}", proto = 47) / GRE()',
            "IP/GRE/ETH": f'IP(src = "{expIP}", proto = 47) / GRE() / Ether()',
            "IP/NVGRE/ETH": f'IP(src = "{expIP}", proto = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IPv6/GRE": f'IPv6(src = "{expIPv6}", nh = 47) / GRE()',
            "IPv6/GRE/ETH": f'IPv6(src = "{expIPv6}", nh = 47) / GRE() / Ether()',
            "IPv6/NVGRE/ETH": f'IPv6(src = "{expIPv6}", nh = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IP/UDP/GTPU": f'IP(src = "{expIP}") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
            "IPv6/UDP/GTPU": f'IPv6(src = "{expIPv6}") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
        }
        pkts_inner_ref = {
            "IP/UDP": f'IP(src = "{expIP}") / UDP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IP/TCP": f'IP(src = "{expIP}") / TCP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IP/SCTP": f'IP(src = "{expIP}") / SCTP(sport = 29999, dport = 30000) / Raw("x" * 128)',
            "IPv6/UDP": f'IPv6(src = "{expIPv6}") / UDP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IPv6/TCP": f'IPv6(src = "{expIPv6}") / TCP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IPv6/SCTP": f'IPv6(src = "{expIPv6}") / SCTP(sport = 29999, dport = 30000) / Raw("x" * 128)',
        }

        if self.dcf_mode == "enable":
            pkts_outer.update(
                {
                    "IP/UDP/VXLAN/ETH": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
                    "IPv6/UDP/VXLAN/ETH": f'IPv6(src = "{sndIPv6}") / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
                }
            )
        pkts_ref = {
            key_outer
            + "/"
            + key_inner: f'Ether(dst="{mac}", src="52:00:00:00:00:00") / '
            + p_outer
            + " / "
            + p_inner
            for key_outer, p_outer in pkts_outer_ref.items()
            for key_inner, p_inner in pkts_inner_ref.items()
        }

        self.checksum_enablehw_tunnel(0, self.vm_dut_0)
        self.checksum_enablehw_tunnel(1, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd("start")
        self.vm0_testpmd.wait_link_status_up(0)
        self.vm0_testpmd.wait_link_status_up(1)
        result = self.checksum_validate(pkts, pkts_ref)
        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd("stop")
        bad_outer_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-outer-ipcsum:", out)
        bad_outer_l4csum = self.vm0_testpmd.get_pmd_value("Bad-outer-l4csum:", out)
        bad_inner_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_inner_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        if self.dcf_mode == "enable":
            # Outer IP checksum error = 7 (outer-ip) * 6 (inner packet)
            self.verify(bad_outer_ipcsum == 42, "Bad-outer-ipcsum check error")
            # Outer IP checksum error = 8 (outer-UDP) * 6 (inner packet)
            self.verify(bad_outer_l4csum == 48, "Bad-outer-l4csum check error")
            # Outer L4 checksum error = 14 (outer packets) * 3 (inner-IP)
            self.verify(bad_inner_ipcsum == 42, "Bad-ipcsum check error")
            # Outer L4 checksum error = 14 (outer packets) * 6 (inner-L4)
            self.verify(bad_inner_l4csum == 84, "Bad-l4csum check error")
        else:
            # Outer IP checksum error = 6 (outer-ip) * 6 (inner packet)
            self.verify(bad_outer_ipcsum == 36, "Bad-outer-ipcsum check error")
            # Outer IP checksum error = 6 (outer-UDP) * 6 (inner packet)
            self.verify(bad_outer_l4csum == 36, "Bad-outer-l4csum check error")
            # Outer L4 checksum error = 12 (outer packets) * 3 (inner-IP)
            self.verify(bad_inner_ipcsum == 36, "Bad-ipcsum check error")
            # Outer L4 checksum error = 12 (outer packets) * 6 (inner-L4)
            self.verify(bad_inner_l4csum == 72, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    @check_supported_nic(
        ["ICE_100G-E810C_QSFP", "ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP"]
    )
    @skip_unsupported_pkg(["os default"])
    def exec_checksum_offload_vlan_tunnel_enable(self, specific_bitwidth=None):
        """
        Enable HW checksum offload.
        Send packet with inner and outer incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=%s " % (self.portMask) + "--enable-rx-cksum " + "",
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("set promisc 1 on")
        self.vm0_testpmd.execute_cmd("set promisc 0 on")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        time.sleep(2)
        port_id_0 = 0
        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        expIP = sndIP
        expIPv6 = sndIPv6

        pkts_outer = {
            "VLAN/IP/UDP/VXLAN-GPE": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN()',
            "VLAN/IP/UDP/VXLAN-GPE/ETH": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN() / Ether()',
            "VLAN/IPv6/UDP/VXLAN-GPE": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}") / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN()',
            "VLAN/IPv6/UDP/VXLAN-GPE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}") / UDP(sport = 4790, dport = 4790, chksum = 0xff) / VXLAN() / Ether()',
            "VLAN/IP/GRE": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE()',
            "VLAN/IP/GRE/ETH": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE() / Ether()',
            "VLAN/IP/NVGRE/ETH": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", proto = 47, chksum = 0xff) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "VLAN/IPv6/GRE": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}", nh = 47) / GRE()',
            "VLAN/IPv6/GRE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}", nh = 47) / GRE() / Ether()',
            "VLAN/IPv6/NVGRE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}", nh = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "VLAN/IP/UDP/GTPU": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", chksum = 0xff) / UDP(dport = 2152, chksum = 0xff) / GTP_U_Header(gtp_type=255, teid=0x123456)',
            "VLAN/IPv6/UDP/GTPU": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}") / UDP(dport = 2152, chksum = 0xff) / GTP_U_Header(gtp_type=255, teid=0x123456)',
        }
        pkts_inner = {
            "IP/UDP": f'IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IP/TCP": f'IP(src = "{sndIP}", chksum = 0xff) / TCP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IP/SCTP": f'IP(src = "{sndIP}", chksum = 0xff) / SCTP(sport = 29999, dport = 30000, chksum = 0x0) / Raw("x" * 128)',
            "IPv6/UDP": f'IPv6(src = "{sndIPv6}") / UDP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IPv6/TCP": f'IPv6(src = "{sndIPv6}") / TCP(sport = 29999, dport = 30000, chksum = 0xff) / Raw("x" * 100)',
            "IPv6/SCTP": f'IPv6(src = "{sndIPv6}") / SCTP(sport = 29999, dport = 30000, chksum = 0x0) / Raw("x" * 128)',
        }

        if self.dcf_mode == "enable":
            pkts_outer.update(
                {
                    "VLAN/IP/UDP/VXLAN/ETH": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4789, dport = 4789, chksum = 0xff) / VXLAN() / Ether()',
                    "VLAN/IPv6/UDP/VXLAN/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}") / UDP(sport = 4789, dport = 4789, chksum = 0xff) / VXLAN() / Ether()',
                }
            )
        pkts = {
            key_outer
            + "/"
            + key_inner: f'Ether(dst="{mac}", src="52:00:00:00:00:00") / '
            + p_outer
            + " / "
            + p_inner
            for key_outer, p_outer in pkts_outer.items()
            for key_inner, p_inner in pkts_inner.items()
        }

        pkts_outer_ref = {
            "VLAN/IP/UDP/VXLAN-GPE": f'Dot1Q(vlan=100) / IP(src = "{expIP}") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "VLAN/IP/UDP/VXLAN-GPE/ETH": f'Dot1Q(vlan=100) / IP(src = "{expIP}") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "VLAN/IPv6/UDP/VXLAN-GPE": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "VLAN/IPv6/UDP/VXLAN-GPE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "VLAN/IP/GRE": f'Dot1Q(vlan=100) / IP(src = "{expIP}", proto = 47) / GRE()',
            "VLAN/IP/GRE/ETH": f'Dot1Q(vlan=100) / IP(src = "{expIP}", proto = 47) / GRE() / Ether()',
            "VLAN/IP/NVGRE/ETH": f'Dot1Q(vlan=100) / IP(src = "{expIP}", proto = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "VLAN/IPv6/GRE": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}", nh = 47) / GRE()',
            "VLAN/IPv6/GRE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}", nh = 47) / GRE() / Ether()',
            "VLAN/IPv6/NVGRE/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}", nh = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "VLAN/IP/UDP/GTPU": f'Dot1Q(vlan=100) / IP(src = "{expIP}") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
            "VLAN/IPv6/UDP/GTPU": f'Dot1Q(vlan=100) / IPv6(src = "{expIPv6}") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
        }
        pkts_inner_ref = {
            "IP/UDP": f'IP(src = "{expIP}") / UDP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IP/TCP": f'IP(src = "{expIP}") / TCP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IP/SCTP": f'IP(src = "{expIP}") / SCTP(sport = 29999, dport = 30000) / Raw("x" * 128)',
            "IPv6/UDP": f'IPv6(src = "{expIPv6}") / UDP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IPv6/TCP": f'IPv6(src = "{expIPv6}") / TCP(sport = 29999, dport = 30000) / Raw("x" * 100)',
            "IPv6/SCTP": f'IPv6(src = "{expIPv6}") / SCTP(sport = 29999, dport = 30000) / Raw("x" * 128)',
        }

        if self.dcf_mode == "enable":
            pkts_outer.update(
                {
                    "VLAN/IP/UDP/VXLAN/ETH": f'Dot1Q(vlan=100) / IP(src = "{sndIP}", chksum = 0xff) / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
                    "VLAN/IPv6/UDP/VXLAN/ETH": f'Dot1Q(vlan=100) / IPv6(src = "{sndIPv6}") / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
                }
            )
        pkts_ref = {
            key_outer
            + "/"
            + key_inner: f'Ether(dst="{mac}", src="52:00:00:00:00:00") / '
            + p_outer
            + " / "
            + p_inner
            for key_outer, p_outer in pkts_outer_ref.items()
            for key_inner, p_inner in pkts_inner_ref.items()
        }

        self.checksum_enablehw_tunnel(0, self.vm_dut_0)
        self.checksum_enablehw_tunnel(1, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd("start")
        self.vm0_testpmd.wait_link_status_up(0)
        self.vm0_testpmd.wait_link_status_up(1)
        result = self.checksum_validate(pkts, pkts_ref)
        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd("stop")
        bad_outer_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-outer-ipcsum:", out)
        bad_outer_l4csum = self.vm0_testpmd.get_pmd_value("Bad-outer-l4csum:", out)
        bad_inner_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_inner_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        if self.dcf_mode == "enable":
            # Outer IP checksum error = 7 (outer-ip) * 6 (inner packet)
            self.verify(bad_outer_ipcsum == 42, "Bad-outer-ipcsum check error")
            # Outer IP checksum error = 8 (outer-UDP) * 6 (inner packet)
            self.verify(bad_outer_l4csum == 48, "Bad-outer-l4csum check error")
            # Outer L4 checksum error = 14 (outer packets) * 3 (inner-IP)
            self.verify(bad_inner_ipcsum == 42, "Bad-ipcsum check error")
            # Outer L4 checksum error = 14 (outer packets) * 6 (inner-L4)
            self.verify(bad_inner_l4csum == 84, "Bad-l4csum check error")
        else:
            # Outer IP checksum error = 6 (outer-ip) * 6 (inner packet)
            self.verify(bad_outer_ipcsum == 36, "Bad-outer-ipcsum check error")
            # Outer IP checksum error = 6 (outer-UDP) * 6 (inner packet)
            self.verify(bad_outer_l4csum == 36, "Bad-outer-l4csum check error")
            # Outer L4 checksum error = 12 (outer packets) * 3 (inner-IP)
            self.verify(bad_inner_ipcsum == 36, "Bad-ipcsum check error")
            # Outer L4 checksum error = 12 (outer packets) * 6 (inner-L4)
            self.verify(bad_inner_l4csum == 72, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    def exec_checksum_offload_disable(self, specific_bitwidth=None):
        """
        Enable SW checksum offload.
        Send same packet with incorrect checksum and verify checksum is valid.
        """

        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=%s " % (self.portMask) + "--enable-rx-cksum " + "",
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        self.vm0_testpmd.execute_cmd("set promisc 1 on")
        self.vm0_testpmd.execute_cmd("set promisc 0 on")

        time.sleep(2)

        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = "10.0.0.1"
        sndIPv6 = "::1"
        sndPkts = {
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s",chksum=0xf)/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s",chksum=0xf)/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIP),
            "IPv6/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
            "IPv6/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/TCP(chksum=0xf)/("X"*46)'
            % (mac, sndIPv6),
        }

        expIP = sndIP
        expIPv6 = sndIPv6
        expPkts = {
            "IP/UDP": 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/UDP()/("X"*46)'
            % (mac, expIP),
            "IP/TCP": 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/TCP()/("X"*46)'
            % (mac, expIP),
            "IPv6/UDP": 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/UDP()/("X"*46)'
            % (mac, expIPv6),
            "IPv6/TCP": 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/TCP()/("X"*46)'
            % (mac, expIPv6),
        }

        self.checksum_enablesw(0, self.vm_dut_0)
        self.checksum_enablesw(1, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd("start")
        result = self.checksum_validate(sndPkts, expPkts)

        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd("stop")
        bad_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    def test_checksum_offload_enable(self):
        self.exec_checksum_offload_enable()

    def test_checksum_offload_enable_scalar(self):
        self.exec_checksum_offload_enable(specific_bitwidth=64)

    def test_checksum_offload_enable_sse(self):
        self.exec_checksum_offload_enable(specific_bitwidth=128)

    def test_checksum_offload_enable_avx2(self):
        self.exec_checksum_offload_enable(specific_bitwidth=256)

    def test_checksum_offload_enable_avx512(self):
        self.exec_checksum_offload_enable(specific_bitwidth=512)

    def test_checksum_offload_vlan_enable(self):
        self.exec_checksum_offload_vlan_enable()

    def test_checksum_offload_vlan_enable_scalar(self):
        self.exec_checksum_offload_vlan_enable(specific_bitwidth=64)

    def test_checksum_offload_vlan_enable_sse(self):
        self.exec_checksum_offload_vlan_enable(specific_bitwidth=128)

    def test_checksum_offload_vlan_enable_avx2(self):
        self.exec_checksum_offload_vlan_enable(specific_bitwidth=256)

    def test_checksum_offload_vlan_enable_avx512(self):
        self.exec_checksum_offload_vlan_enable(specific_bitwidth=512)

    def test_checksum_offload_tunnel_enable(self):
        self.exec_checksum_offload_tunnel_enable()

    def test_checksum_offload_tunnel_enable_scalar(self):
        self.exec_checksum_offload_tunnel_enable(specific_bitwidth=64)

    def test_checksum_offload_tunnel_enable_sse(self):
        self.exec_checksum_offload_tunnel_enable(specific_bitwidth=128)

    def test_checksum_offload_tunnel_enable_avx2(self):
        self.exec_checksum_offload_tunnel_enable(specific_bitwidth=256)

    def test_checksum_offload_tunnel_enable_avx512(self):
        self.exec_checksum_offload_tunnel_enable(specific_bitwidth=512)

    def test_checksum_offload_vlan_tunnel_enable(self):
        self.exec_checksum_offload_vlan_tunnel_enable()

    def test_checksum_offload_vlan_tunnel_enable_scalar(self):
        self.exec_checksum_offload_vlan_tunnel_enable(specific_bitwidth=64)

    def test_checksum_offload_vlan_tunnel_enable_sse(self):
        self.exec_checksum_offload_vlan_tunnel_enable(specific_bitwidth=128)

    def test_checksum_offload_vlan_tunnel_enable_avx2(self):
        self.exec_checksum_offload_vlan_tunnel_enable(specific_bitwidth=256)

    def test_checksum_offload_vlan_tunnel_enable_avx512(self):
        self.exec_checksum_offload_vlan_tunnel_enable(specific_bitwidth=512)

    def test_checksum_offload_disable(self):
        self.exec_checksum_offload_disable()

    def test_checksum_offload_disable_scalar(self):
        self.exec_checksum_offload_disable(specific_bitwidth=64)

    def test_checksum_offload_disable_sse(self):
        self.exec_checksum_offload_disable(specific_bitwidth=128)

    def test_checksum_offload_disable_avx2(self):
        self.exec_checksum_offload_disable(specific_bitwidth=256)

    def test_checksum_offload_disable_avx512(self):
        self.exec_checksum_offload_disable(specific_bitwidth=512)

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Start tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """

        for iface in ifaces:
            command = ("tcpdump -w tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &").format(
                iface
            )
            self.tester.send_expect("rm -f tcpdump_{0}.pcap".format(iface), "#")
            self.tester.send_expect(command, "#")

    def tcpdump_stop_sniff(self):
        """
        Stop the tcpdump process running in the background.
        """
        self.tester.send_expect("killall tcpdump", "#")
        time.sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', "#")
        time.sleep(1)

    def tcpdump_analyse_sniff(self, iface):
        """
        Analyse the tcpdump captured packets. Returning the number of
        packets and the bytes of packets payload.
        """
        packet = Packet()
        pkts = self.filter_packets(
            packet.read_pcapfile("tcpdump_{0}.pcap".format(iface), self.tester)
        )
        rx_packet_count = len(pkts)
        rx_packet_size = [len(p[Raw].load) for p in pkts]
        return rx_packet_count, rx_packet_size

    def segment_validate(
        self,
        segment_size,
        loading_size,
        packet_count,
        tx_stats,
        rx_stats,
        payload_size_list,
    ):
        """
        Validate the segmentation, checking if the result is segmented
        as expected.
        segment_size: segment size,
        loading_size: tx payload size,
        packet_count: tx packet count,
        tx_stats: tx packets count sniffed,
        rx_stats: rx packets count,
        payload_size_list: rx packets payload size list,
        Return a message of validate result.
        """
        num_segs = (loading_size + segment_size - 1) // segment_size
        num_segs_full = loading_size // segment_size
        if not packet_count == tx_stats:
            return "Failed: TX packet count is of inconsitent with sniffed TX packet count."
        elif not packet_count * num_segs == rx_stats:
            return "Failed: RX packet count is of inconsitent with expected RX packet count."
        elif not (
            all(
                [
                    # i * packet_count + j is the i-th segmentation for j-th packet.
                    payload_size_list[i * packet_count + j] == segment_size
                    for j in range(packet_count)
                    for i in range(num_segs_full)
                ]
                + [
                    # i * packet_count + j is i-th segmentation for j-th packet.
                    # i range from num_segs_full to num_segs, means the last
                    # segmentation if exists.
                    payload_size_list[i * packet_count + j]
                    == (loading_size % segment_size)
                    for j in range(packet_count)
                    for i in range(num_segs_full, num_segs)
                ]
            )
        ):
            return (
                "Failed: RX packet segmentation size incorrect, %s." % payload_size_list
            )
        return None

    def tso_validate(
        self,
        tx_interface,
        rx_interface,
        mac,
        inet_type,
        size_and_count,
        outer_pkts=None,
    ):

        validate_result = []

        self.tester.scapy_foreground()
        time.sleep(5)

        packet_l3 = {
            "IP": 'IP(src="192.168.1.1",dst="192.168.1.2")',
            "IPv6": 'IPv6(src="FE80:0:0:0:200:1FF:FE00:200", dst="3555:5555:6666:6666:7777:7777:8888:8888")',
        }

        if not outer_pkts is None:
            for key_outer in outer_pkts:
                for loading_size, packet_count in size_and_count:
                    out = self.vm0_testpmd.execute_cmd(
                        "clear port info all", "testpmd> ", 120
                    )
                    self.tcpdump_start_sniffing([tx_interface, rx_interface])
                    if "GTPU" in key_outer:
                        self.tester.scapy_append(
                            "from scapy.contrib.gtp import GTP_U_Header"
                        )
                    self.tester.scapy_append(
                        (
                            'sendp([Ether(dst="%s",src="52:00:00:00:00:00")/'
                            + outer_pkts[key_outer]
                            + '/%s/TCP(sport=1021,dport=1021)/Raw(RandString(size=%s))], iface="%s", count=%s)'
                        )
                        % (
                            mac,
                            packet_l3[inet_type],
                            loading_size,
                            tx_interface,
                            packet_count,
                        )
                    )
                    out = self.tester.scapy_execute()
                    out = self.vm0_testpmd.execute_cmd("show port stats all")
                    print(out)
                    # In case tcpdump working slower than expected on very limited environments,
                    # an immediate stop sniffing causes a trimed pcap file, leading to wrong
                    # packet statistic.
                    # Uncommenting the following line helps resolving this problem.
                    # time.sleep(1)
                    self.tcpdump_stop_sniff()
                    rx_stats, payload_size_list = self.tcpdump_analyse_sniff(
                        rx_interface
                    )
                    tx_stats, _ = self.tcpdump_analyse_sniff(tx_interface)
                    payload_size_list.sort(reverse=True)
                    self.logger.info(payload_size_list)
                    segment_result = self.segment_validate(
                        800,
                        loading_size,
                        packet_count,
                        tx_stats,
                        rx_stats,
                        payload_size_list,
                    )
                    if segment_result:
                        result_message = (
                            f"Packet: {key_outer}, inet type: {inet_type}, loading size: {loading_size} packet count: {packet_count}: "
                            + segment_result
                        )
                        self.logger.info(result_message)
                        validate_result.append(result_message)
        else:
            for loading_size, packet_count in size_and_count:
                out = self.vm0_testpmd.execute_cmd(
                    "clear port info all", "testpmd> ", 120
                )
                self.tcpdump_start_sniffing([tx_interface, rx_interface])
                self.tester.scapy_append(
                    'sendp([Ether(dst="%s",src="52:00:00:00:00:00")/%s/TCP(sport=1021,dport=1021)/Raw(RandString(size=%s))], iface="%s", count=%s)'
                    % (
                        mac,
                        packet_l3[inet_type],
                        loading_size,
                        tx_interface,
                        packet_count,
                    )
                )
                out = self.tester.scapy_execute()
                out = self.vm0_testpmd.execute_cmd("show port stats all")
                print(out)
                self.tcpdump_stop_sniff()
                rx_stats, payload_size_list = self.tcpdump_analyse_sniff(rx_interface)
                tx_stats, _ = self.tcpdump_analyse_sniff(tx_interface)
                payload_size_list.sort(reverse=True)
                self.logger.info(payload_size_list)
                segment_result = self.segment_validate(
                    800,
                    loading_size,
                    packet_count,
                    tx_stats,
                    rx_stats,
                    payload_size_list,
                )
                if segment_result:
                    result_message = (
                        f"Inet type: {inet_type}, loading size: {loading_size} packet count: {packet_count}: "
                        + segment_result
                    )
                    self.logger.info(result_message)
                    validate_result.append(result_message)
        return validate_result

    def exec_tso(self, specific_bitwidth=None):
        """
        TSO IPv4 TCP, IPv6 TCP testing.
        """
        tx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[0])
        )
        rx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[1])
        )

        # Here size_and_count is a list of tuples for the test scopes that
        # in a tuple (size, count) means, sending packets for count times
        # for TSO with a payload size of size.
        size_and_count = [
            (128, 10),
            (800, 10),
            (801, 10),
            (1700, 10),
            (2500, 10),
            (8500, 1000),
        ]

        self.tester.send_expect(
            "ethtool -K %s rx off tx off tso off gso off gro off lro off"
            % tx_interface,
            "# ",
        )
        self.tester.send_expect("ip l set %s up" % tx_interface, "# ")
        self.dut.send_expect(
            "ifconfig %s mtu %s" % (self.dut.ports_info[0]["intf"], TSO_MTU), "# "
        )
        self.dut.send_expect(
            "ifconfig %s mtu %s" % (self.dut.ports_info[1]["intf"], TSO_MTU), "# "
        )

        self.portMask = utils.create_mask([self.vm0_dut_ports[0]])
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=0x3 "
            + "--enable-rx-cksum "
            + "--max-pkt-len=%s" % TSO_MTU,
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )

        mac = self.vm0_testpmd.get_port_mac(0)
        self.vm0_testpmd.execute_cmd("set verbose 1", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.tso_enable(self.vm0_dut_ports[0], self.vm_dut_0)
        self.tso_enable(self.vm0_dut_ports[1], self.vm_dut_0)
        self.vm0_testpmd.execute_cmd("set promisc 0 on", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("set promisc 1 on", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("start")
        self.vm0_testpmd.wait_link_status_up(self.vm0_dut_ports[0])
        self.vm0_testpmd.wait_link_status_up(self.vm0_dut_ports[1])

        validate_result = []
        validate_result += self.tso_validate(
            tx_interface=tx_interface,
            rx_interface=rx_interface,
            mac=mac,
            inet_type="IP",
            size_and_count=size_and_count,
        )
        validate_result += self.tso_validate(
            tx_interface=tx_interface,
            rx_interface=rx_interface,
            mac=mac,
            inet_type="IPv6",
            size_and_count=size_and_count,
        )
        self.verify(len(validate_result) == 0, ",".join(list(validate_result)))

    @check_supported_nic(
        ["ICE_100G-E810C_QSFP", "ICE_25G-E810C_SFP", "ICE_25G-E810_XXV_SFP"]
    )
    @skip_unsupported_pkg(["os default"])
    def exec_tso_tunnel(self, specific_bitwidth=None):
        """
        TSO tunneled IPv4 TCP, IPv6 TCP testing.
        """
        tx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.vm0_dut_ports[0])
        )
        rx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.vm0_dut_ports[1])
        )

        # Here size_and_count is a list of tuples for the test scopes that
        # in a tuple (size, count) means, sending packets for count times
        # for TSO with a payload size of size.
        size_and_count = [
            (128, 10),
            (800, 10),
            (801, 10),
            (1700, 10),
            (2500, 10),
            (8500, 1000),
        ]

        self.tester.send_expect(
            "ethtool -K %s rx off tx off tso off gso off gro off lro off"
            % tx_interface,
            "# ",
        )
        self.tester.send_expect("ip l set %s up" % tx_interface, "# ")
        self.dut.send_expect(
            "ifconfig %s mtu %s" % (self.dut.ports_info[0]["intf"], TSO_MTU), "# "
        )
        self.dut.send_expect(
            "ifconfig %s mtu %s" % (self.dut.ports_info[1]["intf"], TSO_MTU), "# "
        )

        self.portMask = utils.create_mask([self.vm0_dut_ports[0]])
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param="--portmask=0x3 "
            + "--enable-rx-cksum "
            + "--max-pkt-len=%s" % TSO_MTU,
            eal_param=(
                "--force-max-simd-bitwidth=%d " % specific_bitwidth
                + "--log-level='iavf,7' "
                + "--log-level='dcf,7' "
            )
            if (not specific_bitwidth is None)
            else "",
        )

        mac = self.vm0_testpmd.get_port_mac(0)
        self.vm0_testpmd.execute_cmd("set verbose 0", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("set fwd csum", "testpmd>", 120)
        self.vm0_testpmd.execute_cmd("set promisc 0 on", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("set promisc 1 on", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum mac-swap off 0", "testpmd>")
        self.vm0_testpmd.execute_cmd("csum mac-swap off 1", "testpmd>")
        self.tso_enable_tunnel(self.vm0_dut_ports[0], self.vm_dut_0)
        self.tso_enable_tunnel(self.vm0_dut_ports[1], self.vm_dut_0)
        self.vm0_testpmd.execute_cmd("start")
        self.vm0_testpmd.wait_link_status_up(self.vm0_dut_ports[0])
        self.vm0_testpmd.wait_link_status_up(self.vm0_dut_ports[1])

        pkts_outer = {
            "IP/UDP/VXLAN/ETH": 'IP(src = "192.168.1.1", dst = "192.168.1.2") / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
            "IP/UDP/VXLAN-GPE": 'IP(src = "192.168.1.1", dst = "192.168.1.2") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "IP/UDP/VXLAN-GPE/ETH": 'IP(src = "192.168.1.1", dst = "192.168.1.2") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "IPv6/UDP/VXLAN/ETH": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888") / UDP(sport = 4789, dport = 4789) / VXLAN() / Ether()',
            "IPv6/UDP/VXLAN-GPE": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888") / UDP(sport = 4790, dport = 4790) / VXLAN()',
            "IPv6/UDP/VXLAN-GPE/ETH": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888") / UDP(sport = 4790, dport = 4790) / VXLAN() / Ether()',
            "IP/GRE": 'IP(src = "192.168.1.1", dst = "192.168.1.2", proto = 47) / GRE()',
            "IP/GRE/ETH": 'IP(src = "192.168.1.1", dst = "192.168.1.2", proto = 47) / GRE() / Ether()',
            "IP/NVGRE/ETH": 'IP(src = "192.168.1.1", dst = "192.168.1.2", proto = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IPv6/GRE": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888", nh = 47) / GRE()',
            "IPv6/GRE/ETH": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888", nh = 47) / GRE() / Ether()',
            "IPv6/NVGRE/ETH": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888", nh = 47) / GRE(key_present=1, proto=0x6558, key=0x00000100) / Ether()',
            "IP/UDP/GTPU": 'IP(src = "192.168.1.1", dst = "192.168.1.2") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
            "IPv6/UDP/GTPU": 'IPv6(src = "FE80:0:0:0:200:1FF:FE00:200", dst = "3555:5555:6666:6666:7777:7777:8888:8888") / UDP(dport = 2152) / GTP_U_Header(gtp_type=255, teid=0x123456)',
        }

        validate_result = []
        validate_result += self.tso_validate(
            tx_interface=tx_interface,
            rx_interface=rx_interface,
            mac=mac,
            inet_type="IP",
            size_and_count=size_and_count,
            outer_pkts=pkts_outer,
        )
        validate_result += self.tso_validate(
            tx_interface=tx_interface,
            rx_interface=rx_interface,
            mac=mac,
            inet_type="IPv6",
            size_and_count=size_and_count,
            outer_pkts=pkts_outer,
        )
        self.verify(len(validate_result) == 0, ",".join(list(validate_result)))

    def test_tso(self):
        self.exec_tso()

    def test_tso_scalar(self):
        self.exec_tso(specific_bitwidth=64)

    def test_tso_sse(self):
        self.exec_tso(specific_bitwidth=128)

    def test_tso_avx2(self):
        self.exec_tso(specific_bitwidth=256)

    def test_tso_avx512(self):
        self.exec_tso(specific_bitwidth=512)

    def test_tso_tunnel(self):
        self.exec_tso_tunnel()

    def test_tso_tunnel_scalar(self):
        self.exec_tso_tunnel(specific_bitwidth=64)

    def test_tso_tunnel_sse(self):
        self.exec_tso_tunnel(specific_bitwidth=128)

    def test_tso_tunnel_avx2(self):
        self.exec_tso_tunnel(specific_bitwidth=256)

    def test_tso_tunnel_avx512(self):
        self.exec_tso_tunnel(specific_bitwidth=512)

    def tear_down(self):
        self.vm0_testpmd.execute_cmd("quit", "# ")
        self.dut.send_expect(
            "ifconfig %s mtu %s" % (self.dut.ports_info[0]["intf"], DEFAULT_MTU), "# "
        )

    def tear_down_all(self):
        print("tear_down_all")
        if self.setup_2pf_2vf_1vm_env_flag == 1:
            self.destroy_2pf_2vf_1vm_env()
        self.tester.send_expect(
            "ifconfig %s mtu %s"
            % (
                self.tester.get_interface(
                    self.tester.get_local_port(self.dut_ports[0])
                ),
                DEFAULT_MTU,
            ),
            "# ",
        )
