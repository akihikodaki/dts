# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2018 Intel Corporation
#

import time
from time import sleep

from scapy.layers.inet import ICMP, IP, TCP, UDP, Ether
from scapy.packet import Raw, bind_layers
from scapy.route import *
from scapy.utils import hexstr, rdpcap, wrpcap

from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.test_case import TestCase, skip_unsupported_host_driver


class TestIPPipeline(TestCase):
    def write_pcap_file(self, pcap_file, pkts):
        try:
            wrpcap(pcap_file, pkts)
        except:
            raise Exception("write pcap error")

    def read_pcap_file(self, pcap_file):
        pcap_pkts = []
        try:
            pcap_pkts = rdpcap(pcap_file)
        except:
            raise Exception("write pcap error")

        return pcap_pkts

    def send_and_sniff_pkts(self, from_port, to_port, pcap_file, filters=[], count=1):
        """
        Sent pkts that read from the pcap_file.
        Return the sniff pkts.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[from_port])
        rx_port = self.tester.get_local_port(self.dut_ports[to_port])

        tx_interface = self.tester.get_interface(tx_port)
        rx_interface = self.tester.get_interface(rx_port)

        inst = self.tester.tcpdump_sniff_packets(rx_interface, filters=filters)

        # check that the link status of the port sending the packet is up
        self.tester.is_interface_up(tx_interface)
        self.verify(
            self.tester.is_interface_up(tx_interface), "port link status is down"
        )
        # Prepare the pkts to be sent
        self.tester.scapy_foreground()
        self.tester.scapy_append('pkt = rdpcap("%s")' % (pcap_file))
        self.tester.scapy_append(
            'sendp(pkt, iface="%s", count=%d)' % (tx_interface, count)
        )
        self.tester.scapy_execute()

        return self.tester.load_tcpdump_sniff_packets(inst).pktgen.pkts

    def setup_env(self, port_nums, driver):
        """
        This is to set up vf environment.
        The pf is bound to dpdk driver.
        """
        self.dut.send_expect("modprobe vfio-pci", "# ")
        if driver == "default":
            for port_id in self.dut_ports:
                port = self.dut.ports_info[port_id]["port"]
                port.bind_driver()
        # one PF generate one VF
        for port_num in range(port_nums):
            self.dut.generate_sriov_vfs_by_port(self.dut_ports[port_num], 1, driver)
            self.sriov_vfs_port.append(
                self.dut.ports_info[self.dut_ports[port_num]]["vfs_port"]
            )
        if driver == "default":
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf0_interface, self.vf0_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf1_interface, self.vf1_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf2_interface, self.vf2_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 mac %s" % (self.pf3_interface, self.vf3_mac),
                "# ",
                3,
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf0_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf1_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf2_interface, "# ", 3
            )
            self.dut.send_expect(
                "ip link set %s vf 0 spoofchk off" % self.pf3_interface, "# ", 3
            )

        try:
            for port_num in range(port_nums):
                for port in self.sriov_vfs_port[port_num]:
                    port.bind_driver(driver="vfio-pci")
        except Exception as e:
            self.destroy_env(port_nums, driver)
            raise Exception(e)

    def destroy_env(self, port_nums, driver):
        """
        This is to stop testpmd and destroy vf environment.
        """
        cmd = "^C"
        self.session_secondary.send_expect(cmd, "# ", 20)
        time.sleep(5)
        if driver == self.drivername:
            self.dut.send_expect("quit", "# ")
            time.sleep(5)
        for port_num in range(port_nums):
            self.dut.destroy_sriov_vfs_by_port(self.dut_ports[port_num])

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.port_nums = 4
        self.verify(
            len(self.dut_ports) >= self.port_nums,
            "Insufficient ports for speed testing",
        )

        self.dut_p0_pci = self.dut.get_port_pci(self.dut_ports[0])
        self.dut_p1_pci = self.dut.get_port_pci(self.dut_ports[1])
        self.dut_p2_pci = self.dut.get_port_pci(self.dut_ports[2])
        self.dut_p3_pci = self.dut.get_port_pci(self.dut_ports[3])

        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.dut_p1_mac = self.dut.get_mac_address(self.dut_ports[1])
        self.dut_p2_mac = self.dut.get_mac_address(self.dut_ports[2])
        self.dut_p3_mac = self.dut.get_mac_address(self.dut_ports[3])

        self.pf0_interface = self.dut.ports_info[self.dut_ports[0]]["intf"]
        self.pf1_interface = self.dut.ports_info[self.dut_ports[1]]["intf"]
        self.pf2_interface = self.dut.ports_info[self.dut_ports[2]]["intf"]
        self.pf3_interface = self.dut.ports_info[self.dut_ports[3]]["intf"]

        self.vf0_mac = "00:11:22:33:44:55"
        self.vf1_mac = "00:11:22:33:44:56"
        self.vf2_mac = "00:11:22:33:44:57"
        self.vf3_mac = "00:11:22:33:44:58"

        ports = [self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci]
        self.eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=ports
        )
        self.sriov_vfs_port = []
        self.session_secondary = self.dut.new_session()

        out = self.dut.build_dpdk_apps("./examples/ip_pipeline")
        self.verify("Error" not in out, "Compilation error")
        self.app_ip_pipline_path = self.dut.apps_name["ip_pipeline"]
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_routing_pipeline(self):
        """
        routing pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/route.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/route.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "30:31:32:33:34:35", 60)

        # rule 0 test
        pcap_file = "/tmp/route_0.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.0.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.0.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("a0:a1:a2:a3:a4:a5" in dst_mac_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/route_1.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.64.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.64.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("b0:b1:b2:b3:b4:b5" in dst_mac_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/route_2.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.128.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.128.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("c0:c1:c2:c3:c4:c5" in dst_mac_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/route_3.pcap"
        pkt = [Ether(dst=self.dut_p0_mac) / IP(dst="100.192.0.1") / Raw(load="X" * 26)]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.192.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_mac_list = []
        for packet in sniff_pkts:
            dst_mac_list.append(packet.getlayer(0).dst)
        self.verify("d0:d1:d2:d3:d4:d5" in dst_mac_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_firewall_pipeline(self):
        """
        firewall pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/firewall.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/firewall.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        # rule 0 test
        pcap_file = "/tmp/fw_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.0.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.0.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.0.0.1" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/fw_1.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.64.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.64.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.64.0.1" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/fw_2.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.128.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.128.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.128.0.1" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/fw_3.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(dst="100.192.0.1")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "network", "config": {"dsthost": "100.192.0.1"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("100.192.0.1" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_flow_pipeline(self):
        """
        flow pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/flow.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/flow.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        # rule 0 test
        pcap_file = "/tmp/fl_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/fl_1.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/fl_2.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/fl_3.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    def test_l2fwd_pipeline(self):
        """
        l2fwd pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, self.eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.dut_p1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.dut_p2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.dut_p3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

    @skip_unsupported_host_driver(["vfio-pci"])
    def test_pfdpdk_vf_l2fwd_pipeline(self):
        """
        VF l2fwd pipeline, PF bound to DPDK driver
        """
        self.setup_env(self.port_nums, driver=self.drivername)
        self.dut.send_expect(
            "sed -i '/^link LINK/d' ./examples/ip_pipeline/examples/l2fwd.cli", "# ", 20
        )
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK3 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[3][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK2 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[2][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK1 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[1][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK0 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[0][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PF_PORTS = [
            self.dut_p0_pci,
            self.dut_p1_pci,
            self.dut_p2_pci,
            self.dut_p3_pci,
        ]
        PF_SCRIPT_FILE = "--socket-mem 1024,1024"

        DUT_VF_PORTS = [
            self.sriov_vfs_port[0][0].pci,
            self.sriov_vfs_port[1][0].pci,
            self.sriov_vfs_port[2][0].pci,
            self.sriov_vfs_port[3][0].pci,
        ]
        VF_SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        pf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(4, 8)), prefix="pf", ports=DUT_PF_PORTS
        )
        pf_cmd = "{0} {1} {2} -- -i".format(
            self.app_testpmd_path, pf_eal_para, PF_SCRIPT_FILE
        )
        self.dut.send_expect(pf_cmd, "testpmd> ", 60)
        self.dut.send_expect("set vf mac addr 0 0 %s" % self.vf0_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 1 0 %s" % self.vf1_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 2 0 %s" % self.vf2_mac, "testpmd> ", 30)
        self.dut.send_expect("set vf mac addr 3 0 %s" % self.vf3_mac, "testpmd> ", 30)

        vf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=DUT_VF_PORTS
        )
        vf_cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, vf_eal_para, VF_SCRIPT_FILE
        )
        self.session_secondary.send_expect(vf_cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.vf0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.vf1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.vf2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.vf3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        self.destroy_env(self.port_nums, driver=self.drivername)

    def test_pfkernel_vf_l2fwd_pipeline(self):
        """
        VF l2fwd pipeline, PF bound to kernel driver
        """
        self.setup_env(self.port_nums, driver="default")
        self.dut.send_expect(
            "sed -i '/^link LINK/d' ./examples/ip_pipeline/examples/l2fwd.cli", "# ", 20
        )
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK3 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[3][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK2 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[2][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK1 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[1][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i '/mempool MEMPOOL0/a\link LINK0 dev %s rxq 1 128 MEMPOOL0 txq 1 512 promiscuous on' ./examples/ip_pipeline/examples/l2fwd.cli"
            % self.sriov_vfs_port[0][0].pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_VF_PORTS = [
            self.sriov_vfs_port[0][0].pci,
            self.sriov_vfs_port[1][0].pci,
            self.sriov_vfs_port[2][0].pci,
            self.sriov_vfs_port[3][0].pci,
        ]
        VF_SCRIPT_FILE = "./examples/ip_pipeline/examples/l2fwd.cli"

        vf_eal_para = self.dut.create_eal_parameters(
            cores=list(range(2)), ports=DUT_VF_PORTS
        )
        vf_cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, vf_eal_para, VF_SCRIPT_FILE
        )
        self.session_secondary.send_expect(vf_cmd, "fwd port 2", 60)

        # rule 0 test
        pcap_file = "/tmp/pt_0.pcap"
        pkt = [
            Ether(dst=self.vf0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "rule 0 test fail")

        # rule 1 test
        pcap_file = "/tmp/pt_1.pcap"
        pkt = [
            Ether(dst=self.vf1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "rule 1 test fail")

        # rule 2 test
        pcap_file = "/tmp/pt_2.pcap"
        pkt = [
            Ether(dst=self.vf2_mac)
            / IP(src="100.0.0.12", dst="200.0.0.12")
            / TCP(sport=102, dport=202)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(2, 3, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.12" in dst_ip_list, "rule 2 test fail")

        # rule 3 test
        pcap_file = "/tmp/pt_3.pcap"
        pkt = [
            Ether(dst=self.vf3_mac)
            / IP(src="100.0.0.13", dst="200.0.0.13")
            / TCP(sport=103, dport=203)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(3, 2, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.13" in dst_ip_list, "rule 3 test fail")

        sleep(1)
        self.destroy_env(self.port_nums, driver=self.drivername)
        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]["port"]
            port.bind_driver(driver=self.drivername)

    def test_pipeline_with_tap(self):
        """
        pipeline with tap
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/tap.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/tap.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = [self.dut_p0_pci, self.dut_p1_pci]
        SCRIPT_FILE = "./examples/ip_pipeline/examples/tap.cli"

        eal_para = self.dut.create_eal_parameters(cores=list(range(2)), ports=DUT_PORTS)
        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "fwd port 3", 60)

        tap_session = self.dut.new_session()
        cmd = "ip link set br1 down; brctl delbr br1"
        tap_session.send_expect(cmd, "# ", 20)
        cmd = "brctl addbr br1; brctl addif br1 TAP0; brctl addif br1 TAP1"
        tap_session.send_expect(cmd, "# ", 20)
        cmd = "ifconfig TAP0 up;  ifconfig TAP1 up; ifconfig br1 up"
        tap_session.send_expect(cmd, "# ", 20)
        # rule 0 test
        pcap_file = "/tmp/tap_0.pcap"
        pkt = [
            Ether(dst=self.dut_p0_mac)
            / IP(src="100.0.0.10", dst="200.0.0.10")
            / TCP(sport=100, dport=200)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(0, 1, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.10" in dst_ip_list, "link 1 failed to receive packet")

        # rule 1 test
        pcap_file = "/tmp/tap_1.pcap"
        pkt = [
            Ether(dst=self.dut_p1_mac)
            / IP(src="100.0.0.11", dst="200.0.0.11")
            / TCP(sport=101, dport=201)
            / Raw(load="X" * 6)
        ]
        self.write_pcap_file(pcap_file, pkt)
        filters = [{"layer": "userdefined", "config": {"pcap-filter": "tcp"}}]
        sniff_pkts = self.send_and_sniff_pkts(1, 0, pcap_file, filters)
        dst_ip_list = []
        for packet in sniff_pkts:
            dst_ip_list.append(packet.getlayer(1).dst)
        self.verify("200.0.0.11" in dst_ip_list, "link 0 failed to receive packet")

        sleep(1)
        cmd = "^C"
        self.dut.send_expect(cmd, "# ", 20)

        cmd = "ip link set br1 down; brctl delbr br1"
        tap_session.send_expect(cmd, "# ", 20)
        self.dut.close_session(tap_session)

    def test_rss_pipeline(self):
        """
        rss pipeline
        """
        cmd = (
            "sed -i -e 's/0000:02:00.0/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p0_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:02:00.1/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p1_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.0/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p2_pci
        )
        self.dut.send_expect(cmd, "# ", 20)
        cmd = (
            "sed -i -e 's/0000:06:00.1/%s/' ./examples/ip_pipeline/examples/rss.cli"
            % self.dut_p3_pci
        )
        self.dut.send_expect(cmd, "# ", 20)

        DUT_PORTS = [self.dut_p0_pci, self.dut_p1_pci, self.dut_p2_pci, self.dut_p3_pci]
        SCRIPT_FILE = "./examples/ip_pipeline/examples/rss.cli"

        eal_para = self.dut.create_eal_parameters(cores=list(range(5)), ports=DUT_PORTS)
        cmd = "{0} {1} -- -s {2}".format(
            self.app_ip_pipline_path, eal_para, SCRIPT_FILE
        )
        self.dut.send_expect(cmd, "PIPELINE3 enable", 60)

        pkt = Packet()
        tx_pkt_num = 20
        pkt.generate_random_pkts(
            dstmac="00:11:22:33:44:55",
            pktnum=tx_pkt_num,
            random_type=["IP_RAW"],
            options={"ip": {"dst": "100.0.20.2"}, "layers_config": []},
        )

        all_rx_num = []
        all_rx_packet = []
        for num in range(len(self.dut_ports)):
            inst_list = []
            for port in self.dut_ports:
                rx_interface = self.tester.get_interface(port)
                filters = [
                    {"layer": "ether", "config": {"dst": "not ff:ff:ff:ff:ff:ff"}}
                ]
                inst = self.tester.tcpdump_sniff_packets(
                    intf=rx_interface, filters=filters
                )
                inst_list.append(inst)
            rx_port = self.tester.get_local_port(self.dut_ports[num])
            tport_iface = self.tester.get_interface(rx_port)
            self.verify(
                self.tester.is_interface_up(tport_iface), "port link status is down"
            )
            pkt.send_pkt(crb=self.tester, tx_port=tport_iface, count=1)
            t_rx_ports = []
            t_rx_num = []
            t_rx_packets = []
            t_no_rx_ports = []
            rx_pkt_num = 0
            for port in self.dut_ports:
                p = self.tester.load_tcpdump_sniff_packets(inst_list[port])
                if len(p):
                    t_rx_ports.append(port)
                    t_rx_num.append(len(p))
                    t_rx_packets.append(p)
                    rx_pkt_num += len(p)
                else:
                    t_no_rx_ports.append(port)
            # Verify that the sum of packets received by all ports is 20
            self.verify(
                rx_pkt_num == tx_pkt_num,
                "send packet %s, but receive packet %s" % (tx_pkt_num, rx_pkt_num),
            )
            # Verify all tester_port can received packets
            self.verify(
                len(t_rx_ports) == len(self.dut_ports),
                "port %s not received packets" % t_no_rx_ports,
            )
            all_rx_num.append(tuple(t_rx_num))
            all_rx_packet.append(t_rx_packets)
        # Verify that packets of the same IP can be assigned to the same port through different test ports.
        self.verify(
            len(set(all_rx_num)),
            "pipeline rss failed, all receiced packet num: %s" % all_rx_num,
        )
        for d_port in self.dut_ports:
            if d_port > 0:
                for t_port in range(len(all_rx_packet[d_port])):
                    for i in range(len(all_rx_packet[d_port][t_port])):
                        try:
                            self.verify(
                                all_rx_packet[d_port][t_port][i]
                                in all_rx_packet[0][t_port],
                                "test port %s rss different with test port 0" % d_port,
                            )
                        except VerifyFailure as ex:
                            self.logger.error(
                                "\n%s\n\n%s"
                                % (
                                    all_rx_packet[0][t_port][0].command(),
                                    all_rx_packet[d_port][t_port][0].command(),
                                )
                            )
                            raise ex

    def tear_down(self):
        """
        Run after each test case.
        """
        # close app
        self.dut.send_expect("^C", "# ")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.session_secondary)
        self.dut.kill_all()
