# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from tests.virtio_common import basic_common as BC
from tests.virtio_common import cbdma_common as CC


class TestLoopbackVirtioUserServerModeCbama(TestCase):
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
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.dump_pcap_q0 = "%s/pdump-rx-q0.pcap" % self.base_dir
        self.dump_pcap_q1 = "%s/pdump-rx-q1.pcap" % self.base_dir
        self.device_str = None
        self.cbdma_dev_infos = []
        self.vhost_user = self.dut.new_session(suite="vhost_user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.pdump_session = self.dut.new_session(suite="pdump")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)
        self.CC = CC(self)
        self.BC = BC(self)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.table_header = [
            "Mode",
            "Pkt_size",
            "Throughput(Mpps)",
            "Queue Number",
            "Cycle",
        ]
        self.result_table_create(self.table_header)

    def send_6192_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set txpkts 64,64,64,2000,2000,2000")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")

    def send_960_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set txpkts 64,128,256,512")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")

    def send_chain_packets_from_vhost(self):
        self.vhost_user_pmd.execute_cmd("set txpkts 65535,65535")
        self.vhost_user_pmd.execute_cmd("start tx_first 32", timeout=30)

    def verify_virtio_user_receive_packets(self):
        results = 0.0
        for _ in range(5):
            out = self.virtio_user_pmd.execute_cmd("show port stats 0")
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 5)
        self.logger.info(Mpps)
        self.verify(Mpps > 0, "virtio-user can not receive packets")

    def check_each_queue_has_packets_info_on_virtio_user(
        self, queues, check_rx=True, check_tx=True
    ):
        """
        check each queue has receive packets on virtio-user0 side
        """
        out = self.virtio_user_pmd.execute_cmd("stop")
        for queue_index in range(0, queues):
            queue = re.search("Port= 0/Queue=\s*%d" % queue_index, out)
            queue = queue.group()
            index = out.find(queue)
            if check_rx:
                rx = re.search("RX-packets:\s*(\d*)", out[index:])
                rx_packets = int(rx.group(1))
            self.verify(
                rx_packets > 0,
                "The queue %d rx-packets is 0 about " % queue_index
                + "rx-packets:%d" % rx_packets,
            )
            if check_tx:
                tx = re.search("TX-packets:\s*(\d*)", out[index:])
                tx_packets = int(tx.group(1))
                self.verify(
                    tx_packets > 0,
                    "The queue %d tx-packets is 0 about " % queue_index
                    + "tx-packets:%d" % tx_packets,
                )

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
            pkt = Packet()
            self.logger.info("Check capture file: %s payload " % pcap)
            pkts = pkt.read_pcapfile(pcap, crb=self.dut)
            expect_data = str(pkts[0]["Raw"])
            for i in range(len(pkts)):
                self.verify(
                    len(pkts[i]) == pkt_len,
                    "virtio-user0 receive packet's length %s not equal %s Byte"
                    % (len(pkts[i]), pkt_len),
                )
                if check_payload:
                    check_data = str(pkts[i]["Raw"])
                    self.verify(
                        check_data == expect_data,
                        "the payload in receive packets has been changed from %s" % i,
                    )

    def start_vhost_testpmd(self, cores, eal_param, param, ports, iova_mode="va"):
        eal_param += " --iova=" + iova_mode
        self.vhost_user_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            ports=ports,
            prefix="vhost",
            fixed_prefix=True,
        )

    def start_virtio_testpmd_with_vhost_net0(
        self,
        cores,
        eal_param,
        param,
        set_fwd_csum=True,
        set_fwd_rxonly=False,
    ):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.BC.check_2M_hugepage_size():
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
        if set_fwd_rxonly:
            self.virtio_user_pmd.execute_cmd("set fwd rxonly")
        self.virtio_user_pmd.execute_cmd("start")

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_loopback_packed_ring_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 1: Loopback packed ring inorder mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_ring_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 2: Loopback packed ring mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_packed_ring_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 3: Loopback packed ring inorder non-mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_ring_non_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 4: Loopback packed ring non-mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[1],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[2],
                cbdmas[3],
                cbdmas[4],
                cbdmas[5],
                cbdmas[6],
                cbdmas[7],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_ring_vectorized_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 5: Loopback packed ring vectorized path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_packed_ring_vectorized_not_power_of_2_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 6: Loopback packed ring vectorized path and ring size is not power of 2 multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_ring_inorder_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 7: Loopback split ring inorder mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_ring_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 8: Loopback split ring mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_ring_inorder_non_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 9: Loopback split ring inorder non-mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[1],
                cbdmas[1],
                cbdmas[2],
                cbdmas[2],
                cbdmas[3],
                cbdmas[3],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_ring_non_mergeable_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 10: Loopback split ring non-mergeable path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_ring_vectorized_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 11: Loopback split ring vectorized path multi-queues payload check with server mode and cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
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
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,vectorized=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.vhost_user_pmd.execute_cmd("show port stats all")
        self.vhost_user_pmd.execute_cmd("stop")
        self.check_packet_payload_valid(pkt_len=960)

    def test_loopback_split_ring_large_chain_packets_stress_test_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 12: Loopback split ring large chain packets stress test with server mode and cbdma enable
        """
        if not self.BC.check_2M_hugepage_size():
            cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
                cbdma_num=1, socket=self.ports_socket
            )
            dmas = "txq0@%s;" "rxq0@%s" % (
                cbdmas[0],
                cbdmas[0],
            )
            vhost_eal_param = (
                "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[%s]'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --mbuf-size=65535"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=cbdmas,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_packed_ring_large_chain_packets_stress_test_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 13: Loopback packed ring large chain packets stress test with server mode and cbdma enable
        """
        if not self.BC.check_2M_hugepage_size():
            cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
                cbdma_num=1, socket=self.ports_socket
            )
            dmas = "txq0@%s;" "rxq0@%s" % (
                cbdmas[0],
                cbdmas[0],
            )
            vhost_eal_param = (
                "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[%s]'"
                % dmas
            )
            vhost_param = "--nb-cores=1 --mbuf-size=65535"
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=cbdmas,
                iova_mode="va",
            )
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
                set_fwd_csum=False,
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_pv_split_and_packed_test_txonly_mode_with_cbdma_enable(self):
        """
        Test Case 14: PV split and packed ring test txonly mode with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=2, socket=self.ports_socket
        )
        dmas = (
            "txq0@%s;"
            "txq1@%s;"
            "txq2@%s;"
            "txq3@%s;"
            "txq4@%s;"
            "txq5@%s;"
            "txq6@%s;"
            "txq7@%s"
            % (
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[0],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
                cbdmas[1],
            )
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[%s]'" % dmas
        )
        vhost_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = "--nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=False,
            set_fwd_rxonly=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd txonly")
        self.vhost_user_pmd.execute_cmd("async_vhost tx poll completed on")
        self.send_6192_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_each_queue_has_packets_info_on_virtio_user(
            queues=8, check_rx=True, check_tx=False
        )
        self.check_packet_payload_valid(pkt_len=6192, check_payload=False)

        self.vhost_user_pmd.execute_cmd("stop")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,packed_vq=1,server=1,queue_size=1025"
        virtio_param = "--nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio_eal_param,
            param=virtio_param,
            set_fwd_csum=False,
            set_fwd_rxonly=True,
        )
        self.launch_pdump_to_capture_pkt()
        self.vhost_user_pmd.execute_cmd("set fwd txonly")
        self.vhost_user_pmd.execute_cmd("async_vhost tx poll completed on")
        self.send_960_packets_from_vhost()
        self.verify_virtio_user_receive_packets()
        self.check_each_queue_has_packets_info_on_virtio_user(
            queues=8, check_rx=True, check_tx=False
        )
        self.check_packet_payload_valid(pkt_len=960, check_payload=False)

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
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.close_all_session()
