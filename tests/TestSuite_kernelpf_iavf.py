# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.

Test some vf function in ice driver

"""

import random
import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import DPDK_DCFMODE_SETTING, load_global_setting
from framework.test_case import TestCase
from framework.utils import RED
from framework.virt_common import VM

VM_CORES_MASK = "all"
MAX_VLAN = 4095
ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestKernelpfIavf(TestCase):

    supported_vf_driver = ["pci-stub", "vfio-pci"]

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.vm0 = None
        self.env_done = False
        self.interrupt_flag = False
        self.vf_mac = "00:01:23:45:67:89"
        self.add_addr = "00:11:22:33:44:55"
        self.wrong_mac = "00:11:22:33:44:99"
        # get driver version
        self.driver_version = self.nic_obj.driver_version

        self.port = self.dut_ports[0]
        self.vm_port = 0
        cores = self.dut.get_core_list("1S/1C/1T")
        self.port_mask = utils.create_mask([self.port])

        # set vf assign method and vf driver
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
        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]["intf"]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        self.tester_mac = self.tester.get_mac(tester_port)

        tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_intf1 = self.tester.get_interface(tester_port1)
        self.l3fwdpower_name = self.dut.apps_name["l3fwd-power"].strip().split("/")[-1]

        # bind to default driver
        self.bind_nic_driver(self.dut_ports, driver="")
        # get priv-flags default stats
        self.flag = "vf-vlan-pruning"
        self.default_stats = self.dut.get_priv_flags_state(self.host_intf, self.flag)
        self.dcf_mode = load_global_setting(DPDK_DCFMODE_SETTING)

    def set_up(self):

        if self.running_case == "test_vf_rx_interrupt":
            self.destroy_vm_env()
        elif self.env_done is False:
            self.setup_vm_env()

    def setup_vm_env(self, driver="default", set_vf_mac=True):
        """
        Create testing environment with 1VF generated from 1PF
        """
        if self.env_done:
            return

        # bind to default driver
        self.bind_nic_driver(self.dut_ports, driver="")
        self.used_dut_port = self.dut_ports[0]
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
                "ethtool --set-priv-flags %s %s on" % (self.host_intf, self.flag), "# "
            )
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 1, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]["vfs_port"]
        self.dut.send_expect("ifconfig %s up" % self.host_intf, "#")
        res = self.dut.is_interface_up(self.host_intf)
        self.verify(res, "%s link status is down" % self.host_intf)
        out = self.dut.send_expect("ethtool %s" % self.host_intf, "#")
        self.speed = int(re.findall("Speed: (\d*)", out)[0]) // 1000
        if self.is_eth_series_nic(800):
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % (self.host_intf), "# "
            )
        if self.running_case == "test_vf_multicast":
            self.dut.send_expect(
                "ethtool --set-priv-flags %s vf-true-promisc-support on"
                % (self.host_intf),
                "# ",
            )
        if set_vf_mac is True:
            self.vf_mac = "00:01:23:45:67:89"
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.host_intf, self.vf_mac), "# "
            )
        if self.dcf_mode:
            self.dut.send_expect(
                "ip link set %s vf 0 trust on" % (self.host_intf), "# "
            )
        time.sleep(1)
        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)

            vf_popt = {"opt_host": self.sriov_vfs_port[0].pci}

            # set up VM ENV
            self.vm = VM(self.dut, "vm0", "kernelpf_iavf")
            self.vm.set_vm_device(driver=self.vf_assign_method, **vf_popt)
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed!")

            self.vm_testpmd = PmdOutput(self.vm_dut)
            self.vf_guest_pci = self.vm.pci_maps[0]["guestpci"]
        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)
        self.env_done = True

    def destroy_vm_env(self):
        if getattr(self, "vm", None):
            if getattr(self, "vm_dut", None):
                self.vm_dut.kill_all()
            self.vm_testpmd = None
            self.vm_dut_ports = None
            # destroy vm0
            self.vm.stop()
            self.dut.virt_exit()
            time.sleep(3)
            self.vm = None

        if getattr(self, "used_dut_port", None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None

        self.env_done = False

    def jumboframes_get_stat(self, portid, rx_tx):
        """
        Get packets number from port statistic
        """
        stats = self.vm_testpmd.get_pmd_stats(portid)
        if rx_tx == "rx":
            return [stats["RX-packets"], stats["RX-errors"], stats["RX-bytes"]]
        elif rx_tx == "tx":
            return [stats["TX-packets"], stats["TX-errors"], stats["TX-bytes"]]
        else:
            return None

    def send_random_pkt(self, dts, count=1, allow_miss=False):
        tgen_ports = []
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tgen_ports.append((tx_port, rx_port))
        src_mac = self.tester.get_mac(tx_port)
        dst_mac = dts
        pkt_param = [("ether", {"dst": dst_mac, "src": src_mac})]
        self.vm_testpmd.wait_link_status_up(0, timeout=15)
        result = self.tester.check_random_pkts(
            tgen_ports, pktnum=count, allow_miss=allow_miss, params=pkt_param
        )
        return result
        self.verify(result, "tcpdump not capture %s packets" % count)

    def launch_testpmd(self, **kwargs):
        dcf_flag = kwargs.get("dcf_flag")
        param = kwargs.get("param") if kwargs.get("param") else ""
        if dcf_flag == "enable":
            self.dut.send_expect(
                "ip link set dev %s vf 0 trust on" % self.host_intf, "# "
            )
            out = self.vm_testpmd.start_testpmd(
                "all",
                param=param,
                ports=[self.vf_guest_pci],
                port_options={self.vf_guest_pci: "cap=dcf"},
            )
        else:
            out = self.vm_testpmd.start_testpmd("all", param=param)
        return out

    def test_vf_basic_rxtx(self):
        """
        Set rxonly forward,Send 100 random packets from tester, check packets can be received
        """
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set fwd rxonly")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        time.sleep(1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive packet fail")
        stats = self.vm_testpmd.get_pmd_stats(0)
        self.verify(stats["RX-packets"] >= 100, "vf receive packet num is not match")
        """
        Set txonly forward,check packets can be received by tester
        """
        self.vm_testpmd.execute_cmd("stop")
        self.vm_testpmd.execute_cmd("set fwd txonly")
        self.tester.send_expect("rm -f tcpdump.pcap", "#")
        self.tester.send_expect("tcpdump -i %s 2>tcpdump.out &" % self.tester_intf, "#")
        self.vm_testpmd.execute_cmd("start")
        time.sleep(1)
        self.vm_testpmd.execute_cmd("stop")
        self.tester.send_expect("killall tcpdump", "#")
        time.sleep(1)
        cap_packet = self.tester.send_expect("cat tcpdump.out", "#", 30)
        stats = self.vm_testpmd.get_pmd_stats(0)
        cap_tcp_num = re.findall("(\d+) packets", cap_packet)
        nums = sum(map(int, cap_tcp_num))
        self.verify(
            stats["TX-packets"] != 0 and nums > 0, "vf send packet num is not match"
        )

    def get_testpmd_vf_mac(self, out):
        result = re.search("([a-f0-9]{2}:){5}[a-f0-9]{2}", out, re.IGNORECASE)
        mac = result.group()
        return mac

    def verify_packet_count(self, count):

        pmd0_vf0_stats = self.vm_testpmd.get_pmd_stats(0)
        vf0_rx_cnt = pmd0_vf0_stats["RX-packets"]
        vf0_tx_cnt = pmd0_vf0_stats["TX-packets"]
        self.verify(
            vf0_rx_cnt == vf0_tx_cnt == count, "vf receive packet count not match!"
        )

    def test_vf_promisc_mode(self):
        """
        Enable kernel trust mode
        """
        self.dut.send_expect("ip link set dev %s vf 0 trust on" % self.host_intf, "# ")
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive pkt fail with current mac")
        # send packet with wrong mac, vf can receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac in out, "vf receive pkt fail with wrong mac")

        self.vm_testpmd.execute_cmd("set promisc all off")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive pkt fail with current mac")
        # send packet with wrong mac, vf can not receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1, allow_miss=True)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac not in out, "vf receive pkt with wrong mac")

        self.vm_testpmd.execute_cmd("set promisc all on")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive pkt fail with current mac")
        # send packet with wrong mac, vf can receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac in out, "vf receive pkt fail with wrong mac")

    def test_vf_multicast(self):
        """
        enable kernel trust mode
        """
        multicast_mac = "01:80:C2:00:00:08"
        self.dut.send_expect("ip link set dev %s vf 0 trust off" % self.host_intf, "# ")
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set allmulti all off")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive pkt fail with current mac")
        self.send_random_pkt(multicast_mac, count=1, allow_miss=True)
        out = self.vm_dut.get_session_output()
        self.verify(multicast_mac not in out, "vf receive pkt with multicast mac")

        self.vm_testpmd.execute_cmd("set allmulti all on")
        self.vm_testpmd.execute_cmd(f"mcast_addr add 0 {multicast_mac}")
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive pkt fail with current mac")
        self.send_random_pkt(multicast_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(multicast_mac in out, "vf receive pkt fail with multicast mac")

    def test_vf_broadcast(self):
        """ """
        broadcast_mac = "ff:ff:ff:ff:ff:ff"
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(broadcast_mac, count=1)
        time.sleep(1)
        out = self.vm_dut.get_session_output()
        print(out)
        self.verify(
            broadcast_mac.upper() in out and self.tester_mac.upper() in out,
            "vf receive pkt fail with broadcast mac",
        )

    def send_and_getout(self, vlan=0, pkt_type="UDP"):

        if pkt_type == "UDP":
            pkt = Packet(pkt_type="UDP")
            pkt.config_layer("ether", {"dst": self.vf_mac})
        elif pkt_type == "VLAN_UDP":
            pkt = Packet(pkt_type="VLAN_UDP")
            pkt.config_layer("vlan", {"vlan": vlan})
            pkt.config_layer("ether", {"dst": self.vf_mac})

        pkt.send_pkt(self.tester, tx_port=self.tester_intf)
        out = self.vm_dut.get_session_output(timeout=2)

        return out

    def test_vf_vlan_insertion(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        random_vlan = random.randint(1, MAX_VLAN)
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("tx_vlan set 0 %s" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("rx_vlan add %s 0" % random_vlan)
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")

        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(pkt_type="UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall("vlan %s" % random_vlan, tcpdump_out)
        print(out)
        self.verify(len(receive_pkt) == 1, "Failed to received vlan packet!!!")

    def test_vf_vlan_strip(self):
        random_vlan = random.randint(1, MAX_VLAN)
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("rx_vlan add %s 0" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")

        # enable strip
        self.vm_testpmd.execute_cmd("vlan set strip on 0")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        self.verify(
            "> %s" % self.vf_mac in tcpdump_out and "%s >" % self.vf_mac in tcpdump_out,
            "Failed to received packet!!!",
        )
        receive_vlan_pkt = re.findall("vlan %s" % random_vlan, tcpdump_out)
        self.verify(len(receive_vlan_pkt) == 1, "Failed to received vlan packet!!!")

        # disable strip
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        self.verify(
            "> %s" % self.vf_mac in tcpdump_out and "%s >" % self.vf_mac in tcpdump_out,
            "Failed to received packet!!!",
        )
        receive_vlan_pkt = re.findall("vlan %s" % random_vlan, tcpdump_out)
        self.verify(len(receive_vlan_pkt) == 2, "Failed to not received vlan packet!!!")

    def test_vf_vlan_filter(self):
        random_vlan = random.randint(2, MAX_VLAN)
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("rx_vlan add %d 0" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set strip on 0")
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")

        # error vlan id
        out = self.send_and_getout(vlan=random_vlan - 1, pkt_type="VLAN_UDP")
        receive_pkt = re.findall("received 1 packets", out)
        self.verify(len(receive_pkt) == 0, "Failed error received vlan packet!")

        # passed vlan id
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        receive_pkt = re.findall("received 1 packets", out)
        self.verify(len(receive_pkt) == 1, "Failed pass received vlan packet!")

        # disable filter
        self.vm_testpmd.execute_cmd("rx_vlan rm %d 0" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set filter off 0")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        time.sleep(1)
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall("vlan %s" % random_vlan, tcpdump_out)
        if (
            (self.kdriver == "i40e" and self.driver_version < "2.13.10")
            or (self.kdriver == "i40e" and not self.default_stats)
            or (self.kdriver == "ice" and not self.default_stats)
        ):
            self.verify(len(receive_pkt) == 2, "Failed to received vlan packet!!!")
        else:
            self.verify(len(receive_pkt) == 1, "Failed to received vlan packet!!!")

    def test_vf_rss(self):
        rss_type = ["ip", "tcp", "udp"]
        self.launch_testpmd(dcf_flag=self.dcf_mode, param="--txq=4 --rxq=4")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        default_rss_reta = self.vm_testpmd.execute_cmd(
            "show port 0 rss reta 64 (0xffffffffffffffff)"
        )
        for i, j in zip(list(range(64)), [3, 2, 1, 0] * 16):
            self.vm_testpmd.execute_cmd("port config 0 rss reta (%d,%d)" % (i, j))
        change_rss_reta = self.vm_testpmd.execute_cmd(
            "show port 0 rss reta 64 (0xffffffffffffffff)"
        )
        self.verify(default_rss_reta != change_rss_reta, "port config rss reta failed")
        for type in rss_type:
            self.vm_testpmd.execute_cmd("port config all rss %s" % type)
            self.vm_testpmd.execute_cmd("start")
            self.send_packet(self.tester_intf, "IPV4&%s" % type)
            time.sleep(1)
            out = self.vm_dut.get_session_output()
            self.verify_packet_number(out)
            self.vm_testpmd.execute_cmd("clear port stats all")

    def test_vf_rss_hash_key(self):
        update_hash_key = "1b9d58a4b961d9cd1c56ad1621c3ad51632c16a5d16c21c3513d132c135d132c13ad1531c23a51d6ac49879c499d798a7d949c8a"
        self.launch_testpmd(dcf_flag=self.dcf_mode, param="--txq=4 --rxq=4")
        self.vm_testpmd.execute_cmd("show port 0 rss-hash key")
        self.vm_testpmd.execute_cmd("set fwd rxonly")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        pkt1_info = self.send_pkt_gethash()
        self.vm_testpmd.execute_cmd(
            "port config 0 rss-hash-key ipv4 {}".format(update_hash_key)
        )
        out = self.vm_testpmd.execute_cmd("show port 0 rss-hash key")
        self.verify(update_hash_key in out.lower(), "rss hash key update failed")
        pkt2_info = self.send_pkt_gethash()
        self.verify(
            pkt1_info[0][0] != pkt2_info[0][0], "hash value should be different"
        )

    def send_pkt_gethash(self, pkt=""):
        if pkt == "":
            pkt = (
                "sendp([Ether(dst='%s')/IP(src='1.2.3.4')/Raw(load='X'*30)], iface='%s')"
                % (self.vf_mac, self.tester_intf)
            )
        self.tester.scapy_append(pkt)
        self.tester.scapy_execute()
        out = self.vm_dut.get_session_output()
        p = re.compile("RSS hash=(0x\w+) - RSS queue=(0x\w+)")
        pkt_info = p.findall(out)
        self.verify(pkt_info, "received pkt have no hash")
        self.logger.info("hash values:{}".format(pkt_info))
        return pkt_info

    def verify_packet_number(self, out):
        queue_number = len(re.findall("port 0", out))
        self.verify(
            "queue 0" in out
            and "queue 1" in out
            and "queue 2" in out
            and "queue 3" in out,
            "some queue can't receive packet when send ip packet",
        )
        p = re.compile("RSS\shash=(\w+)\s-\sRSS\squeue=(\w+)")
        pkt_info = p.findall(out)
        self.verify(
            len(pkt_info) == queue_number, "some packets no hash:{}".format(p.pattern)
        )
        hit_rssHash = False
        for rss_hash, rss_queue in pkt_info:
            for i, j in zip(list(range(64)), [3, 2, 1, 0] * 16):
                if int(rss_hash, 16) % 64 == i and int(rss_queue, 16) == j:
                    hit_rssHash = True
                    break
                else:
                    hit_rssHash = False
            self.verify(hit_rssHash, "some pkt not directed by rss.")

    def send_packet(self, itf, tran_type):
        """
        Sends packets.
        """
        mac = self.vf_mac
        # send packet with different source and dest ip
        if tran_type == "IPV4&ip":
            for i in range(30):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", '
                    'dst="192.168.0.%d")], iface="%s")' % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV4&tcp":
            for i in range(30):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'
                    'TCP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        elif tran_type == "IPV4&udp":
            for i in range(30):
                packet = (
                    r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'
                    'UDP(sport=1024,dport=1024)], iface="%s")'
                    % (mac, i + 1, i + 2, itf)
                )
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(0.5)
        self.tester.scapy_execute()
        time.sleep(1)

    def enable_hw_checksum(self):
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("csum set ip hw 0")
        self.vm_testpmd.execute_cmd("csum set udp hw 0")
        self.vm_testpmd.execute_cmd("csum set tcp hw 0")
        self.vm_testpmd.execute_cmd("csum set sctp hw 0")
        self.vm_testpmd.execute_cmd("set fwd csum")
        self.vm_testpmd.execute_cmd("set verbose 1")

    def enable_sw_checksum(self):
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("csum set ip sw 0")
        self.vm_testpmd.execute_cmd("csum set udp sw 0")
        self.vm_testpmd.execute_cmd("csum set tcp sw 0")
        self.vm_testpmd.execute_cmd("csum set sctp sw 0")
        self.vm_testpmd.execute_cmd("set fwd csum")
        self.vm_testpmd.execute_cmd("set verbose 1")

    def checksum_verify(self):
        packets_sent = {
            "IP/": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x1234)/UDP()/("X"*46)'
            % self.vf_mac,
            "IP/UDP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP()/UDP(chksum=0x1234)/("X"*46)'
            % self.vf_mac,
            "IP/TCP": 'Ether(dst="%s", src="52:00:00:00:00:00")/IP()/TCP(chksum=0x1234)/("X"*46)'
            % self.vf_mac,
        }

        # Send packet.
        self.tester.scapy_foreground()

        for packet_type in list(packets_sent.keys()):
            self.tester.scapy_append(
                'sendp([%s], iface="%s")'
                % (packets_sent[packet_type], self.tester_intf)
            )
            self.start_tcpdump(self.tester_intf)
            self.tester.scapy_execute()
            time.sleep(1)
            tcpdump_out = self.get_tcpdump_package()
            if packet_type == "IP/UDP":
                # verify udp checksum
                self.verify(
                    "bad udp cksum" in tcpdump_out and "udp sum ok" in tcpdump_out,
                    "udp checksum verify fail",
                )
            elif packet_type == "IP/TCP":
                # verify tcp checksum
                self.verify(
                    "cksum 0x1234 (incorrect" in tcpdump_out
                    and "correct" in tcpdump_out,
                    "tcp checksum verify fail",
                )
            else:
                # verify ip checksum
                self.verify(
                    "bad cksum 1234" in tcpdump_out and "udp sum ok" in tcpdump_out,
                    "ip checksum verify fail",
                )
        out = self.vm_testpmd.execute_cmd("stop")
        bad_ipcsum = self.vm_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 1, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 2, "Bad-ipcsum check error")

    def start_tcpdump(self, rxItf):
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect(
            "tcpdump -A -nn -e -vv -w getPackageByTcpdump.cap -i %s 2> /dev/null& "
            % rxItf,
            "#",
        )
        time.sleep(2)

    def get_tcpdump_package(self):
        time.sleep(1)
        self.tester.send_expect("killall tcpdump", "#")
        time.sleep(1)
        return self.tester.send_expect(
            "tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap", "#"
        )

    def verify_packet_segmentation(self, out, seg=True):
        if seg:
            number1 = re.findall("length 1460: HTTP", out)
            number2 = re.findall("length 834: HTTP", out)
            self.verify(
                len(number1) == 3 and len(number2) == 1, "packet has no segment"
            )
        else:
            self.verify("length 1460: HTTP" not in out, "packet has segment")
            # tester send packet with incorrect checksum
            # vf fwd packet with corrent checksum
            self.verify(
                "incorrect" in out and "correct" in out, "checksum has incorrect"
            )
        self.tester.send_expect("^C", "#")

    def test_vf_port_start_stop(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        for i in range(10):
            self.vm_testpmd.execute_cmd("port stop all")
            self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        port_id_0 = 0
        vf0_stats = self.vm_testpmd.get_pmd_stats(port_id_0)
        vf0_rx_cnt = vf0_stats["RX-packets"]
        self.verify(vf0_rx_cnt == 100, "no packet was received by vm0_VF0")

        vf0_rx_err = vf0_stats["RX-errors"]
        self.verify(vf0_rx_err == 0, "vm0_VF0 rx-errors")

        vf0_tx_cnt = vf0_stats["TX-packets"]
        self.verify(vf0_tx_cnt == 100, "no packet was fwd by vm0_VF0")

    def test_vf_statistic_reset(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify(
            "RX-packets: 0" in out and "TX-packets: 0" in out,
            "receive some misc packet",
        )
        self.vm_testpmd.execute_cmd("clear port stats all")
        self.send_random_pkt(self.vf_mac, count=100)
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify(
            "RX-packets: 100" in out and "TX-packets: 100" in out, "receive packet fail"
        )
        self.vm_testpmd.execute_cmd("clear port stats all")
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify(
            "RX-packets: 0" in out and "TX-packets: 0" in out, "clear port stats fail"
        )

    def test_vf_information(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        out = self.vm_testpmd.execute_cmd("show port info 0")
        self.verify("Link status: up" in out, "link stats has error")
        self.verify("Link speed: %s" % self.speed in out, "link speed has error")
        print(out)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        out = self.vm_testpmd.execute_cmd("show port stats all")
        print(out)
        self.verify(
            "RX-packets: 100" in out and "TX-packets: 100" in out, "receive packet fail"
        )

    def test_vf_rx_interrupt(self):
        # build l3-power
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        self.bind_nic_driver(self.dut_ports, driver="")
        self.create_2vf_in_host()
        # start l3fwd-power
        l3fwd_app = self.dut.apps_name["l3fwd-power"]

        cmd = l3fwd_app + " -l 6,7 -n 4 -- -p 0x3 --config " + "'(0,0,6),(1,0,7)'"
        self.dut.send_expect(cmd, "POWER", timeout=40)
        out = self.dut.get_session_output()
        print(out)
        pattern = re.compile(r"(([a-f0-9]{2}:){5}[a-f0-9]{2})")
        mac_list = pattern.findall(out.lower())
        vf0_mac = mac_list[0][0]
        vf1_mac = mac_list[1][0]
        # send packet to vf0 and vf1
        self.scapy_send_packet(vf0_mac, self.tester_intf)
        self.scapy_send_packet(vf1_mac, self.tester_intf1)
        out = self.dut.get_session_output()
        self.verify(
            "L3FWD_POWER: lcore 6 is waked up from rx interrupt" in out,
            "lcore 6 is not waked up",
        )
        self.verify(
            "L3FWD_POWER: lcore 7 is waked up from rx interrupt" in out,
            "lcore 7 is not waked up",
        )
        self.verify(
            "L3FWD_POWER: lcore 6 sleeps until interrupt triggers" in out,
            "lcore 6 not sleep",
        )
        self.verify(
            "L3FWD_POWER: lcore 7 sleeps until interrupt triggers" in out,
            "lcore 7 not sleep",
        )
        self.scapy_send_packet(vf0_mac, self.tester_intf, count=16)
        self.scapy_send_packet(vf1_mac, self.tester_intf1, count=16)
        out = self.dut.get_session_output()
        self.verify(
            "L3FWD_POWER: lcore 6 is waked up from rx interrupt" in out,
            "lcore 6 is not waked up",
        )
        self.verify(
            "L3FWD_POWER: lcore 7 is waked up from rx interrupt" in out,
            "lcore 7 is not waked up",
        )
        self.dut.send_expect(
            "killall %s" % self.l3fwdpower_name, "# ", 60, alt_session=True
        )

    def test_vf_unicast(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set allmulti all off")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("start")
        self.scapy_send_packet(self.wrong_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall("received 1 packets", out))
        self.verify(packets == 0, "Not receive expected packet")

        self.scapy_send_packet(self.vf_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall("received 1 packets", out))
        self.verify(packets == 10, "Not receive expected packet")

    def test_vf_vlan_promisc(self):
        self.launch_testpmd(dcf_flag=self.dcf_mode)
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("set promisc all on")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("vlan set filter off 0")
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")

        # send 10 tagged packets, and check 10 tagged packets received
        self.scapy_send_packet(self.vf_mac, self.tester_intf, vlan_flags=True, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall("received 1 packets", out))
        if (
            (self.kdriver == "i40e" and self.driver_version < "2.13.10")
            or (self.kdriver == "i40e" and not self.default_stats)
            or (self.kdriver == "ice" and not self.default_stats)
            or self.dcf_mode
        ):
            self.verify(packets == 10, "Not receive expected packet")
        else:
            self.verify(packets == 0, "Receive expected packet")

        # send 10 untagged packets, and check 10 untagged packets received
        self.scapy_send_packet(self.vf_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall("received 1 packets", out))
        self.verify(packets == 10, "Not receive expected packet")

    def scapy_send_packet(self, mac, testinterface, vlan_flags=False, count=1):
        """
        Send a packet to port
        """
        if count == 1:
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP()/UDP()/'
                "Raw('X'*18)], iface=\"%s\")" % (mac, testinterface)
            )
        else:
            for i in range(count):
                if vlan_flags:
                    self.tester.scapy_append(
                        'sendp([Ether(dst="%s")/Dot1Q(id=0x8100, vlan=100)/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], '
                        'iface="%s")' % (mac, i, testinterface)
                    )
                else:
                    self.tester.scapy_append(
                        'sendp([Ether(dst="%s")/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], '
                        'iface="%s")' % (mac, i, testinterface)
                    )
        self.tester.scapy_execute()

    def create_2vf_in_host(self, driver=""):
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]["vfs_port"]

        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]["vfs_port"]
        self.dut.send_expect("modprobe vfio", "#")
        self.dut.send_expect("modprobe vfio-pci", "#")
        for port in self.sriov_vfs_port_0:
            port.bind_driver("vfio-pci")

        for port in self.sriov_vfs_port_1:
            port.bind_driver("vfio-pci")

    def destroy_2vf_in_2pf(self):
        if getattr(self, "used_dut_port_0", None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            self.used_dut_port_0 = None
        if getattr(self, "used_dut_port_1", None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            self.used_dut_port_1 = None

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.running_case == "test_vf_rx_interrupt":
            self.dut.send_expect(
                "killall %s" % self.l3fwdpower_name, "# ", 60, alt_session=True
            )
            self.destroy_2vf_in_2pf()
        else:
            self.vm_testpmd.execute_cmd("quit", "#")
            time.sleep(1)
        if not self.dcf_mode:
            self.dut.send_expect(
                "ip link set dev %s vf 0 trust off" % self.host_intf, "# "
            )

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        if self.env_done:
            self.destroy_vm_env()

        if (
            any([self.is_eth_series_nic(800), self.kdriver == "i40e"])
            and self.default_stats
        ):
            self.dut.send_expect(
                "ethtool --set-priv-flags %s %s %s"
                % (self.host_intf, self.flag, self.default_stats),
                "# ",
            )
        self.bind_nic_driver(self.dut_ports, driver=self.drivername)
