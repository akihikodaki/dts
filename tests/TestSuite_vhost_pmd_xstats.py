# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2017 Intel Corporation
#

"""
DPDK Test suite.

vhost pmd xstats test suite.
"""
import datetime
import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.utils import convert_int2ip, convert_ip2int

ETHER_JUMBO_FRAME_MTU = 9000
DEFAULT_JUMBO_FRAME_MTU = 1500


class TestVhostPmdXstats(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        self.scapy_num = 0
        self.queues = 2
        self.dmac = self.dut.get_mac_address(self.dut_ports[0])
        self.virtio1_mac = "52:54:00:00:00:01"
        self.core_config = "1S/6C/1T"
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len(
            [n for n in self.dut.cores if int(n["socket"]) == self.ports_socket]
        )
        self.verify(self.cores_num >= 6, "There has not enough cores to test this case")
        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.core_list_user = self.core_list[0:3]
        self.core_list_host = self.core_list[3:6]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)

    def set_up(self):
        """
        Run before each test case.
        Launch vhost sample using default params
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def scapy_send_packet(self, pktsize, dmac, num=1):
        """
        Send a packet to port
        """
        self.scapy_num += 1
        options = {
            "ip": {"src": "192.168.0.1", "dst": "192.168.1.1"},
            "layers_config": [],
        }
        # give a default value to ip
        try:
            src_ip_num = convert_ip2int(options["ip"]["src"])
        except:
            src_ip_num = 0
        try:
            dst_ip_num = convert_ip2int(options["ip"]["dst"])
        except:
            dst_ip_num = 0
        if num == 1:
            count = 1
            group = num
        else:
            count = 1000
            group = int(num / count)
        for _ in range(group):
            srcip = convert_int2ip(src_ip_num, ip_type=4)
            dstip = convert_int2ip(dst_ip_num, ip_type=4)
            pkt = Packet(pkt_type="IP_RAW", pkt_len=pktsize)
            pkt.config_layer("ether", {"dst": dmac})
            pkt.config_layer("ipv4", {"src": srcip, "dst": dstip})
            dst_ip_num += 1
            pkt.send_pkt(self.tester, tx_port=self.txItf, count=count)

    def send_verify(self, scope, num):
        """
        according the scope to check results
        """
        out = self.vhost_user_pmd.execute_cmd("show port xstats 1")
        rx_pattern = re.compile("rx_q\d+_%s_packets:\s*(\d+)" % scope)
        packet_rx = rx_pattern.findall(out)
        sum_packet_rx = 0
        for item in packet_rx:
            sum_packet_rx += int(item)

        tx_pattern = re.compile("tx_q\d+_%s_packets:\s*(\d+)" % scope)
        packet_tx = tx_pattern.findall(out)
        sum_packet_tx = 0
        for item in packet_tx:
            sum_packet_tx += int(item)

        self.verify(
            int(sum_packet_rx) == num, "Insufficient the received packets from nic"
        )
        self.verify(
            int(sum_packet_tx) == num, "Insufficient the received packets from virtio"
        )

    def start_vhost_testpmd(self):
        """
        start testpmd on vhost
        """
        vdevs = ["net_vhost0,iface=vhost-net,queues=%d,client=0" % self.queues]
        param = "--nb-cores=2 --rxq=2 --txq=2"
        self.vhost_user_pmd.start_testpmd(
            cores=self.core_list_host,
            param=param,
            vdevs=vdevs,
            ports=[0],
            prefix="vhost",
        )
        self.vhost_user_pmd.execute_cmd("set fwd io")
        self.vhost_user_pmd.execute_cmd("start")

    def start_virtio_testpmd(self, args):
        """
        start testpmd on virtio
        """
        eal_param = ""
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        vdevs = [
            "net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queues=%d,%s"
            % (self.queues, args["version"])
        ]
        param = "%s --nb-cores=2 --rxq=2 --txq=2" % args["path"]
        self.virtio_user0_pmd.start_testpmd(
            cores=self.core_list_user,
            eal_param=eal_param,
            param=param,
            vdevs=vdevs,
            no_pci=True,
            prefix="virtio",
        )
        self.virtio_user0_pmd.execute_cmd("set fwd io")
        self.virtio_user0_pmd.execute_cmd("start")

    def xstats_number_and_type_verify(self):
        """
        Verify receiving and transmitting packets correctly in the Vhost PMD xstats
        """
        out = self.vhost_user_pmd.execute_cmd("show port xstats 1")
        p = re.compile(r"rx_q0_size_[0-9]+_[\w+]*packets")
        categories = p.findall(out)
        categories = categories[:-1]
        self.verify(
            len(categories) > 0, "Unable to find the categories of RX packet size!"
        )
        for cat in categories:
            scope = re.search(r"(?<=rx_)\w+(?=_packets)", cat).group(0)
            pktsize = int(re.search(r"(?<=rx_q0_size_)\d+", cat).group(0))
            if pktsize > 1518:
                self.tester.send_expect(
                    "ifconfig %s mtu %d" % (self.txItf, ETHER_JUMBO_FRAME_MTU), "# "
                )
            types = ["ff:ff:ff:ff:ff:ff", "01:00:00:33:00:01"]
            for p in types:
                if p == "ff:ff:ff:ff:ff:ff":
                    scope = "broadcast"
                    self.dmac = "ff:ff:ff:ff:ff:ff"
                elif p == "01:00:00:33:00:01":
                    scope = "multicast"
                    self.dmac = "01:00:00:33:00:01"
                self.scapy_send_packet(int(pktsize + 4), self.dmac, 10000)
                self.send_verify(scope, 10000)
                self.clear_port_xstats(scope)
            self.tester.send_expect(
                "ifconfig %s mtu %d" % (self.txItf, DEFAULT_JUMBO_FRAME_MTU), "# "
            )

    def test_vhost_xstats_split_ring_inorder_mergeable_path(self):
        """
        Test Case 1: Vhost pmd xstats stability test with split ring inorder mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_split_ring_inorder_no_mergeable_path(self):
        """
        Test Case 2: Vhost pmd xstats test with split ring inorder non-mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=0",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_split_ring_mergeable_path(self):
        """
        Test Case 3: Vhost pmd xstats test with split ring mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=0,mrg_rxbuf=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_split_ring_no_mergeable_path(self):
        """
        Test Case 4: Vhost pmd xstats test with split ring non-mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_split_ring_vector_rx_path(self):
        """
        Test Case 5: Vhost pmd xstats test with split ring vector_rx path
        """
        virtio_pmd_arg = {
            "version": "in_order=0,mrg_rxbuf=0,vectorized=1",
            "path": "--tx-offloads=0x0",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_inorder_mergeable_path(self):
        """
        Test Case 6: Vhost pmd xstats test with packed ring inorder mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=1,packed_vq=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_inorder_no_mergeable_path(self):
        """
        Test Case 7: Vhost pmd xstats test with packed ring inorder non-mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=0,vectorized=1,packed_vq=1",
            "path": "--rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_mergeable_path(self):
        """
        Test Case 8: Vhost pmd xstats test with packed ring mergeable path
        """
        self.scapy_num = 0
        virtio_pmd_arg = {
            "version": "in_order=0,mrg_rxbuf=1,packed_vq=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while 1:
            date_now = datetime.datetime.now()
            scope = "multicast"
            self.dmac = "01:00:00:33:00:01"
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_no_mergeable_path(self):
        """
        Test Case 9: Vhost pmd xstats test with packed ring non-mergeable path
        """
        virtio_pmd_arg = {
            "version": "in_order=0,mrg_rxbuf=0,packed_vq=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_vectorized_path(self):
        """
        Test Case 10: Vhost pmd xstats test with packed ring vectorized path
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=0,vectorized=1,packed_vq=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while 1:
            date_now = datetime.datetime.now()
            scope = "broadcast"
            self.dmac = "ff:ff:ff:ff:ff:ff"
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def test_vhost_xstats_packed_ring_vectorized_path_ringsize_not_powerof_2(self):
        """
        Test Case 11: Vhost pmd xstats test with packed ring vectorized path with ring size is not power of 2
        """
        virtio_pmd_arg = {
            "version": "in_order=1,mrg_rxbuf=0,vectorized=1,queue_size=1221,packed_vq=1",
            "path": "--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --rxd=1221 --txd=1221",
        }
        self.start_vhost_testpmd()
        self.start_virtio_testpmd(virtio_pmd_arg)
        self.xstats_number_and_type_verify()
        # stability test with basic packets number check
        self.scapy_num = 0
        date_old = datetime.datetime.now()
        date_new = date_old + datetime.timedelta(minutes=2)
        while 1:
            date_now = datetime.datetime.now()
            scope = "broadcast"
            self.dmac = "ff:ff:ff:ff:ff:ff"
            self.scapy_send_packet(64, self.dmac, 1)
            if date_now >= date_new:
                break
        self.send_verify(scope, self.scapy_num)
        self.close_all_testpmd()

    def close_all_testpmd(self):
        """
        close all testpmd of vhost and virtio
        """
        self.vhost_user_pmd.quit()
        self.virtio_user0_pmd.quit()

    def clear_port_xstats(self, scope):

        self.vhost_user_pmd.execute_cmd("clear port xstats 1")
        out = self.vhost_user_pmd.execute_cmd("show port xstats 1")
        rx_pattern = re.compile("rx_q\d+_%s_packets:\s*(\d+)" % scope)
        rx_packet_list = rx_pattern.findall(out)
        for rx_packet in rx_packet_list:
            self.verify(int(rx_packet) == 0, "Insufficient the received package")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)
