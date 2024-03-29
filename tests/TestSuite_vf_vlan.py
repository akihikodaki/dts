# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
#

import random
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import DPDK_DCFMODE_SETTING, load_global_setting
from framework.test_case import TestCase
from framework.virt_common import VM

VM_CORES_MASK = "all"
MAX_VLAN = 4095


class TestVfVlan(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False

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

        # get driver version
        self.driver_version = self.nic_obj.driver_version

        # bind to default driver
        self.bind_nic_driver(self.dut_ports[:2], driver="")
        self.host_intf0 = self.dut.ports_info[self.dut_ports[0]]["intf"]
        # get priv-flags default stats
        self.flag = "vf-vlan-pruning"
        self.default_stats = self.dut.get_priv_flags_state(self.host_intf0, self.flag)
        self.dcf_mode = load_global_setting(DPDK_DCFMODE_SETTING)

    def set_up(self):
        self.setup_vm_env()

    def setup_vm_env(self, driver="default"):
        """
        Create testing environment with 2VFs generated from 2PFs
        """
        if self.env_done:
            return

        self.used_dut_port_0 = self.dut_ports[0]
        self.host_intf0 = self.dut.ports_info[self.used_dut_port_0]["intf"]
        tester_port = self.tester.get_local_port(self.used_dut_port_0)
        self.tester_intf0 = self.tester.get_interface(tester_port)
        # check driver whether there is flag vf-vlan-pruning.
        if not self.default_stats:
            self.logger.warning(
                utils.RED(
                    f"{self.kdriver + '_' + self.driver_version} driver does not have vf-vlan-pruning flag."
                )
            )
        if (
            any([self.is_eth_series_nic(800), self.kdriver == "i40e"])
            and self.default_stats
        ):
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s on" % (self.host_intf0, self.flag), "# "
            )
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]
        if self.kdriver == "ice":
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % (self.host_intf0), "# "
            )
        self.vf0_mac = "00:10:00:00:00:00"
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf0, self.vf0_mac), "# "
        )
        if self.dcf_mode:
            self.dut.send_expect(
                "ip link set %s vf 0 trust on" % (self.host_intf0), "# "
            )

        self.used_dut_port_1 = self.dut_ports[1]
        self.host_intf1 = self.dut.ports_info[self.used_dut_port_1]["intf"]
        if self.is_eth_series_nic(800) and self.default_stats:
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s on" % (self.host_intf1, self.flag), "# "
            )
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]["vfs_port"]
        tester_port = self.tester.get_local_port(self.used_dut_port_1)
        self.tester_intf1 = self.tester.get_interface(tester_port)

        self.vf1_mac = "00:20:00:00:00:00"
        self.dut.send_expect(
            "ip link set %s vf 0 mac %s" % (self.host_intf1, self.vf1_mac), "# "
        )
        if self.dcf_mode:
            self.dut.send_expect(
                "ip link set %s vf 0 trust on" % (self.host_intf1), "# "
            )

        try:

            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {"opt_host": self.sriov_vfs_port_0[0].pci}
            vf1_prop = {"opt_host": self.sriov_vfs_port_1[0].pci}

            # set up VM0 ENV
            self.vm0 = VM(self.dut, "vm0", "vf_vlan")
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")
            self.vf0_guest_pci = self.vm0.pci_maps[0]["guestpci"]
            self.vf1_guest_pci = self.vm0.pci_maps[1]["guestpci"]

        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.env_done = True

    def destroy_vm_env(self):
        if getattr(self, "vm0", None):
            if getattr(self, "vm_dut_0", None):
                self.vm_dut_0.kill_all()
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None

        if getattr(self, "used_dut_port_0", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            port = self.dut.ports_info[self.used_dut_port_0]["port"]
            self.used_dut_port_0 = None

        if getattr(self, "used_dut_port_1", None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            port = self.dut.ports_info[self.used_dut_port_1]["port"]
            self.used_dut_port_1 = None

        self.bind_nic_driver(self.dut_ports[:2], driver="")

        self.env_done = False

    def launch_testpmd(self, **kwargs):
        dcf_flag = kwargs.get("dcf_flag")
        force_max_simd_bitwidth = kwargs.get("force-max-simd-bitwidth")
        param = kwargs.get("param") if kwargs.get("param") else ""
        eal_param = ""
        # for dcf mode, the vlan offload support in scalar path
        if dcf_flag:
            eal_param += " --force-max-simd-bitwidth=64 "
            eal_param += " --log-level='dcf,8' "
            self.vm0_testpmd.start_testpmd(
                VM_CORES_MASK,
                ports=[self.vf0_guest_pci, self.vf1_guest_pci],
                param=param,
                eal_param=eal_param,
                port_options={
                    self.vf0_guest_pci: "cap=dcf",
                    self.vf1_guest_pci: "cap=dcf",
                },
            )
        else:
            if force_max_simd_bitwidth:
                eal_param += " --force-max-simd-bitwidth=%d " % force_max_simd_bitwidth
                param += " --enable-rx-cksum "
            if self.kdriver == "ice" or self.kdriver == "i40e":
                eal_param += " --log-level='iavf,8' "
            elif self.kdriver == "ixgbe" or self.kdriver == "igbe":
                eal_param += " --log-level='%svf,8' " % self.kdriver
            self.vm0_testpmd.start_testpmd(
                VM_CORES_MASK, param=param, eal_param=eal_param
            )

    def execute_pvid_vf_tx(self, specific_bitwidth=None):
        """
        Add port based vlan on vf device and check vlan tx work
        """
        random_vlan = random.randint(1, MAX_VLAN)

        self.dut.send_expect(
            "ip link set %s vf 0 vlan %d" % (self.host_intf0, random_vlan), "# "
        )
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" % random_vlan in out, "Failed to add pvid on VF0")

        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("start")

        pkt = Packet(pkt_type="UDP")
        pkt.config_layer("ether", {"dst": self.vf1_mac})
        inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
        pkt.send_pkt(self.tester, tx_port=self.tester_intf1)
        pkts = self.tester.load_tcpdump_sniff_packets(inst)

        self.verify(len(pkts), "Not receive expected packet")
        self.vm0_testpmd.quit()

        # disable pvid
        self.dut.send_expect("ip link set %s vf 0 vlan 0" % (self.host_intf0), "# ")

    def test_pvid_vf_tx(self):
        self.execute_pvid_vf_tx()

    def test_pvid_vf_tx_avx512(self):
        self.execute_pvid_vf_tx(specific_bitwidth=512)

    def send_and_getout(self, vlan=0, pkt_type="UDP"):

        if pkt_type == "UDP":
            pkt = Packet(pkt_type="UDP")
            pkt.config_layer("ether", {"dst": self.vf0_mac})
        elif pkt_type == "VLAN_UDP":
            pkt = Packet(pkt_type="VLAN_UDP")
            pkt.config_layer("vlan", {"vlan": vlan})
            pkt.config_layer("ether", {"dst": self.vf0_mac})

        pkt.send_pkt(self.tester, tx_port=self.tester_intf0)
        out = self.vm_dut_0.get_session_output(timeout=2)

        return out

    def execute_add_pvid_vf(self, specific_bitwidth=None):
        random_vlan = random.randint(1, MAX_VLAN)

        self.dut.send_expect(
            "ip link set %s vf 0 vlan %d" % (self.host_intf0, random_vlan), "# "
        )
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" % random_vlan in out, "Failed to add pvid on VF0")

        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set fwd rxonly")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")

        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        self.verify("received" in out, "Failed to received vlan packet!!!")

        # send packet without vlan
        out = self.send_and_getout(pkt_type="UDP")
        self.verify("received" not in out, "Received packet without vlan!!!")

        # send packet with vlan not matched
        wrong_vlan = (random_vlan + 1) % 4096
        out = self.send_and_getout(vlan=wrong_vlan, pkt_type="VLAN_UDP")
        self.verify("received" not in out, "Received pacekt with wrong vlan!!!")

        # remove vlan
        self.vm0_testpmd.execute_cmd("stop")
        self.vm0_testpmd.quit()
        self.dut.send_expect("ip link set %s vf 0 vlan 0" % self.host_intf0, "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" % random_vlan not in out, "Failed to remove pvid on VF0")

        # restart testpmd
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set fwd rxonly")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")
        # send packet with vlan
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        if (
            (self.kdriver == "i40e" and self.driver_version < "2.13.10")
            or (self.kdriver == "i40e" and not self.default_stats)
            or (self.kdriver == "ice" and not self.default_stats)
            or self.dcf_mode
        ):
            self.verify("received" in out, "Failed to received vlan packet!!!")
        else:
            self.verify("received" not in out, "Received vlan packet without pvid!!!")

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify("received" in out, "Not recevied packet with vlan 0!!!")

        # send packet without vlan
        out = self.send_and_getout(vlan=0, pkt_type="UDP")
        self.verify("received" in out, "Not received packet without vlan!!!")

        self.vm0_testpmd.quit()

        # disable pvid
        self.dut.send_expect("ip link set %s vf 0 vlan 0" % (self.host_intf0), "# ")

    def test_add_pvid_vf(self):
        self.execute_add_pvid_vf()

    def test_add_pvid_vf_avx512(self):
        self.execute_add_pvid_vf(specific_bitwidth=512)

    def tx_and_check(self, tx_vlan=1):
        inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
        self.vm0_testpmd.execute_cmd("set burst 1")
        self.vm0_testpmd.execute_cmd("start tx_first")
        self.vm0_testpmd.execute_cmd("stop")

        # strip sniffered vlans
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        vlans = []
        for i in range(len(pkts)):
            vlan = pkts.strip_element_vlan("vlan", p_index=i)
            vlans.append(vlan)

        self.verify(tx_vlan in vlans, "Tx packet with vlan not received!!!")

    def execute_vf_vlan_tx(self, specific_bitwidth=None):
        self.verify(self.kdriver not in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        random_vlan = random.randint(1, MAX_VLAN)
        tx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set verbose 1")

        for tx_vlan in tx_vlans:
            # for Intel® Ethernet 700 Series ,
            # if you want insert tx_vlan,
            # please enable rx_vlan at the same time
            if self.kdriver == "i40e" or self.kdriver == "ice":
                self.vm0_testpmd.execute_cmd("vlan set filter on 0")
                self.vm0_testpmd.execute_cmd("rx_vlan add %d 0" % tx_vlan)
            self.vm0_testpmd.execute_cmd("stop")
            self.vm0_testpmd.execute_cmd("port stop all")
            self.vm0_testpmd.execute_cmd("tx_vlan set 0 %d" % tx_vlan)
            self.vm0_testpmd.execute_cmd("port start all")
            self.tx_and_check(tx_vlan=tx_vlan)

        self.vm0_testpmd.quit()

    def test_vf_vlan_tx(self):
        self.execute_vf_vlan_tx()

    def test_vf_vlan_tx_avx512(self):
        self.execute_vf_vlan_tx(specific_bitwidth=512)

    def execute_vf_vlan_rx(self, specific_bitwidth=None):
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        param = (
            "--enable-hw-vlan"
            if not self.dcf_mode and self.kdriver is not "ixgbe"
            else ""
        )
        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param=param,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set fwd rxonly")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("vlan set strip on 0")
        self.vm0_testpmd.execute_cmd("vlan set filter on 0")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("start")

        # send packet without vlan
        out = self.send_and_getout(vlan=0, pkt_type="UDP")
        self.verify(
            "received 1 packets" in out, "Not received normal packet as default!!!"
        )

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify("VLAN tci=0x0" in out, "Not received vlan 0 packet as default!!!")

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd("rx_vlan add %d 0" % rx_vlan)
            time.sleep(1)
            # send packet with same vlan
            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            vlan_hex = hex(rx_vlan)
            self.verify(
                "VLAN tci=%s" % vlan_hex in out, "Not received expected vlan packet!!!"
            )

            pkt = Packet(pkt_type="VLAN_UDP")
            if rx_vlan == MAX_VLAN:
                continue
            wrong_vlan = (rx_vlan + 1) % 4096

            # send packet with wrong vlan
            out = self.send_and_getout(vlan=wrong_vlan, pkt_type="VLAN_UDP")
            self.verify(
                "received 1 packets" not in out, "Received filtered vlan packet!!!"
            )

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd("rx_vlan rm %d 0" % rx_vlan)

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify("VLAN tci=0x0" in out, "Not received vlan 0 packet as default!!!")

        # send packet without vlan
        out = self.send_and_getout(pkt_type="UDP")
        self.verify(
            "received 1 packets" in out,
            "Not received normal packet after remove vlan filter!!!",
        )

        # send packet with vlan
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        if (
            (self.kdriver == "i40e" and self.driver_version < "2.13.10")
            or (self.kdriver == "i40e" and not self.default_stats)
            or (self.kdriver == "ice" and not self.default_stats)
        ):
            self.verify(
                "received 1 packets" in out,
                "Received mismatched vlan packet while vlan filter on",
            )
        else:
            self.verify(
                "received 1 packets" not in out,
                "Received mismatched vlan packet while vlan filter on",
            )

        self.vm0_testpmd.quit()

    def test_vf_vlan_rx(self):
        self.execute_vf_vlan_rx()

    def test_vf_vlan_rx_avx512(self):
        self.execute_vf_vlan_rx(specific_bitwidth=512)

    def execute_vf_vlan_strip(self, specific_bitwidth=None):
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports("any")

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        param = (
            "--enable-hw-vlan"
            if not self.dcf_mode and self.kdriver is not "ixgbe"
            else ""
        )

        self.launch_testpmd(
            dcf_flag=self.dcf_mode,
            param=param,
            force_max_simd_bitwidth=specific_bitwidth,
        )
        self.vm0_testpmd.execute_cmd("set fwd rxonly")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd("vlan set strip on 0")
            self.vm0_testpmd.execute_cmd("vlan set filter on 0")
            self.vm0_testpmd.execute_cmd("rx_vlan add %d 0" % rx_vlan)
            time.sleep(1)
            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            # enable strip, vlan will be in mbuf
            vlan_hex = hex(rx_vlan)
            self.verify(
                "VLAN tci=%s" % vlan_hex in out, "Failed to strip vlan packet!!!"
            )
            self.verify(
                "RTE_MBUF_F_RX_VLAN_STRIPPED" in out, "Failed to strip vlan packet!"
            )

            self.vm0_testpmd.execute_cmd("vlan set strip off 0")

            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            self.verify(
                "received 1 packets" in out, "Not received vlan packet as expected!!!"
            )
            self.verify(
                "RTE_MBUF_F_RX_VLAN_STRIPPED" not in out,
                "Failed to disable strip vlan!!!",
            )

        self.vm0_testpmd.quit()

    def test_vf_vlan_strip(self):
        self.execute_vf_vlan_strip()

    def test_vf_vlan_strip_avx512(self):
        self.execute_vf_vlan_strip(specific_bitwidth=512)

    def tear_down(self):
        self.destroy_vm_env()

    def tear_down_all(self):
        self.destroy_vm_env()
        if (
            any([self.is_eth_series_nic(800), self.kdriver == "i40e"])
            and self.default_stats
        ):
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.host_intf0, self.flag, self.default_stats),
                "# ",
            )
