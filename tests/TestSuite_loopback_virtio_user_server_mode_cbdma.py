# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

"""
DPDK Test suite.
Test loopback virtio-user server mode
"""
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


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
        self.dump_pcap_q0 = "/root/pdump-rx-q0.pcap"
        self.dump_pcap_q1 = "/root/pdump-rx-q1.pcap"
        self.device_str = None
        self.cbdma_dev_infos = []
        self.vhost_user = self.dut.new_session(suite="vhost_user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.pdump_session = self.dut.new_session(suite="pdump")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)

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

    def send_6192_packets_from_vhost(self):
        """
        start the testpmd of vhost-user, start to send 8k packets
        """
        time.sleep(3)
        self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("set txpkts 64,64,64,2000,2000,2000")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")
        self.vhost_user_pmd.execute_cmd("stop")

    def send_960_packets_from_vhost(self):
        """
        start the testpmd of vhost-user, start to send 8k packets
        """
        time.sleep(3)
        self.vhost_user_pmd.execute_cmd("set fwd csum")
        self.vhost_user_pmd.execute_cmd("set txpkts 64,128,256,512")
        self.vhost_user_pmd.execute_cmd("set burst 1")
        self.vhost_user_pmd.execute_cmd("start tx_first 1")
        self.vhost_user_pmd.execute_cmd("stop")

    def send_chain_packets_from_vhost(self):
        time.sleep(3)
        self.vhost_user_pmd.execute_cmd("set txpkts 65535,65535,65535,65535,65535")
        self.vhost_user_pmd.execute_cmd("start tx_first 32", timeout=30)

    def verify_virtio_user_receive_packets(self):
        results = 0.0
        time.sleep(3)
        for _ in range(10):
            out = self.virtio_user_pmd.execute_cmd("show port stats all")
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.logger.info(Mpps)
        self.verify(Mpps > 0, "virtio-user can not receive packets")

    def launch_pdump_to_capture_pkt(self, capture_all_queue=True):
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

    def check_packet_payload_valid(self, pkt_len):
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

    @staticmethod
    def generate_dms_param(queues):
        das_list = []
        for i in range(queues):
            das_list.append("txq{}".format(i))
        das_param = "[{}]".format(";".join(das_list))
        return das_param

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get and bind cbdma ports into DPDK driver
        """
        self.all_cbdma_list = []
        self.cbdma_list = []
        self.cbdma_str = ""
        out = self.dut.send_expect(
            "./usertools/dpdk-devbind.py --status-dev dma", "# ", 30
        )
        device_info = out.split("\n")
        for device in device_info:
            pci_info = re.search("\s*(0000:\S*:\d*.\d*)", device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if allow_diff_socket:
                    self.all_cbdma_list.append(pci_info.group(1))
                else:
                    if self.ports_socket == cur_socket:
                        self.all_cbdma_list.append(pci_info.group(1))
        self.verify(
            len(self.all_cbdma_list) >= cbdma_num, "There no enough cbdma device"
        )
        self.cbdma_list = self.all_cbdma_list[0:cbdma_num]
        self.cbdma_str = " ".join(self.cbdma_list)
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=%s %s"
            % (self.drivername, self.cbdma_str),
            "# ",
            60,
        )

    def bind_cbdma_device_to_kernel(self):
        self.dut.send_expect("modprobe ioatdma", "# ")
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -u %s" % self.cbdma_str, "# ", 30
        )
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py --force --bind=ioatdma  %s" % self.cbdma_str,
            "# ",
            60,
        )

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_loopback_packed_ring_all_path_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 1: Loopback packed ring all path multi-queues payload check with server mode and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=8)
        vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]'"
        lcore_dma = (
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s"
            % (
                self.vhost_core_list[1],
                self.cbdma_list[0],
                self.vhost_core_list[1],
                self.cbdma_list[1],
                self.vhost_core_list[2],
                self.cbdma_list[2],
                self.vhost_core_list[2],
                self.cbdma_list[3],
                self.vhost_core_list[3],
                self.cbdma_list[4],
                self.vhost_core_list[3],
                self.cbdma_list[5],
                self.vhost_core_list[4],
                self.cbdma_list[6],
                self.vhost_core_list[4],
                self.cbdma_list[7],
            )
        )
        vhost_param = (
            " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024 --lcore-dma=[%s]"
            % lcore_dma
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )

        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1"
        virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        if not self.check_2M_env:
            self.virtio_user_pmd.quit()
            self.vhost_user_pmd.quit()
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7;rxq0;rxq1;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]'"
            vhost_param = (
                " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024 --lcore-dma=[%s]"
                % lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
            virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.logger.info("Launch virtio with packed ring mergeable inorder path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )

            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_ring_all_path_multi_queues_payload_check_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 2: Loopback split ring all path multi-queues payload check with server mode and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=3)
        vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]'"
        lcore_dma = (
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s,"
            "lcore%s@%s"
            % (
                self.vhost_core_list[1],
                self.cbdma_list[0],
                self.vhost_core_list[2],
                self.cbdma_list[0],
                self.vhost_core_list[3],
                self.cbdma_list[1],
                self.vhost_core_list[3],
                self.cbdma_list[2],
                self.vhost_core_list[4],
                self.cbdma_list[1],
                self.vhost_core_list[4],
                self.cbdma_list[2],
                self.vhost_core_list[5],
                self.cbdma_list[1],
                self.vhost_core_list[5],
                self.cbdma_list[2],
            )
        )
        vhost_param = (
            " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 --lcore-dma=[%s]"
            % lcore_dma
        )

        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )

        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
        virtio_param = (
            "--enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.vhost_user_pmd.quit()
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        if not self.check_2M_env:
            self.virtio_user_pmd.quit()
            self.vhost_user_pmd.quit()
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;rxq2;rxq3;rxq4;rxq5;rxq6;rxq7]'"
            vhost_param = (
                " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024 --lcore-dma=[%s]"
                % lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
            virtio_param = " --nb-cores=4 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.logger.info("Launch virtio with packed ring mergeable inorder path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )

            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

    def test_loopback_split_ring_large_chain_packets_stress_test_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 3: Loopback split ring large chain packets stress test with server mode and cbdma enable
        """
        if not self.check_2M_env:
            self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0;rxq0]'"
            lcore_dma = "lcore%s@%s" % (self.vhost_core_list[1], self.cbdma_list[0])

            vhost_param = " --nb-cores=1 --mbuf-size=65535 --lcore-dma=[%s]" % lcore_dma
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
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

            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def test_loopback_packed_ring_large_chain_packets_stress_test_with_server_mode_and_cbdma_enable(
        self,
    ):
        """
        Test Case 4: Loopback packed ring large chain packets stress test with server mode and cbdma enable
        """
        if not self.check_2M_env:
            self.get_cbdma_ports_info_and_bind_to_dpdk(cbdma_num=1)
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0;rxq0]'"
            lcore_dma = "lcore%s@%s" % (self.vhost_core_list[1], self.cbdma_list[0])

            vhost_param = " --nb-cores=1 --mbuf-size=65535 --lcore-dma=[%s]" % lcore_dma
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
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

            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.kill_all()
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()
