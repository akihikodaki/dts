# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC


class TestLoopbackVirtioUserServerModeDsa(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.core_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.core_list[0:9]
        self.virtio0_core_list = self.core_list[10:15]
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.app_pdump = self.dut.apps_name["pdump"]
        self.dump_pcap_q0 = "/root/pdump-rx-q0.pcap"
        self.dump_pcap_q1 = "/root/pdump-rx-q1.pcap"
        self.device_str = None
        self.cbdma_dev_infos = []
        self.vhost_user = self.dut.new_session(suite="vhost_user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.pdump_session = self.dut.new_session(suite="pdump")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.DC = DC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.table_header = [
            "Mode",
            "Pkt_size",
            "Throughput(Mpps)",
            "Queue Number",
            "Cycle",
        ]
        self.result_table_create(self.table_header)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def send_6192_packets_from_vhost(self, set_csum=True):
        if set_csum:
            self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("set txpkts 64,64,64,2000,2000,2000")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")

    def send_960_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("set txpkts 64,128,256,512")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")

    def send_chain_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set txpkts 65535,65535")
        self.vhost_user_pmd.execute_cmd("start tx_first 32", timeout=30)

    def verify_virtio_user_receive_packets(self):
        results = 0.0
        for _ in range(3):
            out = self.virtio_user_pmd.execute_cmd("show port stats all")
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 3)
        self.logger.info(Mpps)
        self.vhost_user_pmd.execute_cmd("stop")
        self.verify(Mpps > 0, "virtio-user can not receive packets")

    def launch_pdump_to_capture_pkt(self):
        command = (
            self.app_pdump
            + " "
            + "-v --file-prefix=virtio-user0 -- "
            + "--pdump  'device_id=net_virtio_user0,queue=0,rx-dev=%s,mbuf-size=8000' "
            + "--pdump  'device_id=net_virtio_user0,queue=1,rx-dev=%s,mbuf-size=8000'"
        )
        self.pdump_session.send_expect(
            command % (self.dump_pcap_q0, self.dump_pcap_q1), "Port"
        )

    def check_packet_payload_valid(self, pkt_len, check_payload=True):
        self.pdump_session.send_expect("^c", "# ", 60)
        dump_file_list = [self.dump_pcap_q0, self.dump_pcap_q1]
        for pcap in dump_file_list:
            self.dut.session.copy_file_from(src="%s" % pcap, dst="%s" % pcap)
            pkt = Packet()
            pkts = pkt.read_pcapfile(pcap)
            expect_data = str(pkts[0]["Raw"])
            for i in range(len(pkts)):
                self.verify(
                    len(pkts[i]) == pkt_len,
                    "virtio-user0 receive packet's length not equal %s Byte" % pkt_len,
                )
                if check_payload:
                    check_data = str(pkts[i]["Raw"])
                    self.verify(
                        check_data == expect_data,
                        "the payload in receive packets has been changed from %s" % i,
                    )

    def start_vhost_testpmd(
        self,
        cores,
        eal_param="",
        param="",
        no_pci=False,
        ports="",
        port_options="",
        iova_mode="va",
    ):
        if iova_mode:
            eal_param += " --iova=" + iova_mode
        if not no_pci and port_options != "":
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                port_options=port_options,
                ports=ports,
                prefix="vhost",
                fixed_prefix=True,
            )
        elif not no_pci and port_options == "":
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                ports=ports,
                prefix="vhost",
                fixed_prefix=True,
            )
        else:
            self.vhost_user_pmd.start_testpmd(
                cores=cores,
                eal_param=eal_param,
                param=param,
                no_pci=no_pci,
                prefix="vhost",
                fixed_prefix=True,
            )

    def start_virtio_testpmd_with_vhost_net0(
        self, cores, eal_param, param, set_fwd_csum=True
    ):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )
        if set_fwd_csum:
            self.virtio_user_pmd.execute_cmd("set fwd csum")
        self.virtio_user_pmd.execute_cmd("start")

    def test_loopback_split_server_mode_large_chain_packets_stress_test_with_dpdk_driver(
        self,
    ):
        """
        Test Case 1: Loopback split ring server mode large chain packets stress test with dsa dpdk driver
        """
        if not self.check_2M_env:
            dsas = self.DC.bind_dsa_to_dpdk_driver(
                dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
            )
            dmas = "txq0@%s-q0;rxq0@%s-q0" % (dsas[0], dsas[0])
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[%s],client=1'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=65535"
            port_options = {dsas[0]: "max_queues=1"}
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                no_pci=False,
                ports=dsas,
                port_options=port_options,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1"
            virtio_param = "--nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_packed_server_mode_large_chain_packets_stress_test_with_dpdk_driver(
        self,
    ):
        """
        Test Case 2: Loopback packed ring server mode large chain packets stress test with dsa dpdk driver
        """
        if not self.check_2M_env:
            dsas = self.DC.bind_dsa_to_dpdk_driver(
                dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
            )
            dmas = "txq0@%s-q0;rxq0@%s-q0" % (dsas[0], dsas[0])
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[%s],client=1'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=65535"
            port_options = {dsas[0]: "max_queues=1"}
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                no_pci=False,
                ports=dsas,
                port_options=port_options,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_split_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 3: Loopback split ring inorder mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 4: Loopback split ring mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_non_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 5: Loopback split ring non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
        virtio_param = (
            "--enable-hw-vlan-strip --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 6: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_vectorized_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 7: Loopback split ring vectorized path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 8: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 9: Loopback packed ring mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_non_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 10: Loopback packed ring non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 11: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_vectorized_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 12: Loopback packed ring vectorized path multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_vectorized_not_power_of_2_multi_queues_payload_check_with_server_mode_and_dpdk_driver(
        self,
    ):
        """
        Test Case 13: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas = (
            "txq0@%s-q0;"
            "txq1@%s-q0;"
            "txq2@%s-q0;"
            "txq3@%s-q0;"
            "txq4@%s-q1;"
            "txq5@%s-q1;"
            "rxq2@%s-q2;"
            "rxq3@%s-q2;"
            "rxq4@%s-q3;"
            "rxq5@%s-q3;"
            "rxq6@%s-q3;"
            "rxq7@%s-q3"
            % (
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=8"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,vectorized=1,packed_vq=1,queue_size=1025,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_server_mode_large_chain_packets_stress_test_with_kernel_driver(
        self,
    ):
        """
        Test Case 14: Loopback split ring server mode large chain packets stress test with dsa kernel driver
        """
        if not self.check_2M_env:
            wqs = self.DC.create_wq(wq_num=1, dsa_idxs=[0])
            dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[0])
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[%s],client=1'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=65535"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                no_pci=True,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048,server=1"
            virtio_param = "--nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_packed_server_mode_large_chain_packets_stress_test_with_kernel_driver(
        self,
    ):
        """
        Test Case 15: Loopback packed ring server mode large chain packets stress test with dsa kernel driver
        """
        if not self.check_2M_env:
            wqs = self.DC.create_wq(wq_num=1, dsa_idxs=[0])
            dmas = "txq0@%s;rxq0@%s" % (wqs[0], wqs[0])
            vhost_eal_param = (
                "--vdev 'net_vhost0,iface=vhost-net0,queues=1,dmas=[%s],client=1'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --txd=1024 --rxd=1024 --mbuf-size=65535"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                no_pci=True,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_split_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 16: Loopback split ring inorder mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 17: Loopback split ring mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_non_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 18: Loopback split ring non-mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
        virtio_param = (
            "--enable-hw-vlan-strip --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 19: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_vectorized_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 20: Loopback split ring vectorized path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 21: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 22: Loopback packed ring mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_non_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 23: Loopback packed ring non-mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 24: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_vectorized_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 25: Loopback packed ring vectorized path multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_vectorized_not_power_of_2_multi_queues_payload_check_with_server_mode_and_kernel_driver(
        self,
    ):
        """
        Test Case 26: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[1],
                wqs[1],
                wqs[8],
                wqs[8],
                wqs[9],
                wqs[9],
                wqs[9],
                wqs[9],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "rxq2@%s;"
            "rxq3@%s;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[1],
                wqs[2],
                wqs[3],
                wqs[4],
                wqs[5],
                wqs[10],
                wqs[11],
                wqs[12],
                wqs[13],
                wqs[14],
                wqs[15],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=960)

    def test_pv_split_and_packed_server_mode_txonly_mode_with_dpdk_and_kernel_driver(
        self,
    ):
        """
        Test Case 27: PV split and packed ring server mode test txonly mode with dsa dpdk and kernel driver
        """
        wqs = self.DC.create_wq(wq_num=8, dsa_idxs=[0, 1])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2,
            driver_name="vfio-pci",
            dsa_idxs=[2, 3],
            socket=self.ports_socket,
        )
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s-q0;"
            "txq5@%s-q0;"
            "rxq2@%s-q1;"
            "rxq3@%s-q1;"
            "rxq4@%s;"
            "rxq5@%s;"
            "rxq6@%s;"
            "rxq7@%s"
            % (
                wqs[0],
                wqs[0],
                wqs[0],
                wqs[0],
                dsas[0],
                dsas[0],
                dsas[0],
                dsas[0],
                wqs[8],
                wqs[8],
                wqs[8],
                wqs[8],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas[0:1],
            port_options=port_options,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd txonly")
        self.vhost_user_pmd.execute_cmd("async_vhost tx poll completed on")
        self.send_6192_packets_from_vhost(set_csum=False)
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192, check_payload=False)

        self.vhost_user_pmd.quit()
        vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1'"
        vhost_param = "--nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd txonly")
        self.vhost_user_pmd.execute_cmd("async_vhost tx poll completed on")
        self.send_6192_packets_from_vhost(set_csum=False)
        self.verify_virtio_user_receive_packets()
        self.check_packet_payload_valid(pkt_len=6192, check_payload=False)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)
