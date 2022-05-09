#
# BSD LICENSE
#
# Copyright(c) <2022> Intel Corporation. All rights reserved.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
#   * Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


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
        self.virtio0_core_list = self.core_list[10:12]
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
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
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
        self.vhost_user_pmd.execute_cmd("start tx_first 32")

    def verify_virtio_user_receive_packets(self):
        out = self.virtio_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)
        rx_pkts = int(re.search("RX-packets: (\d+)", out).group(1))
        self.verify(rx_pkts > 0, "virtio-user can not received packets")

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

    def start_virtio_testpmd_with_vhost_net0(self, cores, eal_param, param):
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

    def test_server_mode_packed_ring_all_path_multi_queues_payload_check_with_cbdma(
        self,
    ):
        """
        Test Case 1: loopback packed ring all path cbdma test payload check with server mode and multi-queues
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]'"
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        core5 = self.vhost_core_list[5]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        cbdma4 = self.cbdma_list[3]
        cbdma5 = self.cbdma_list[4]
        cbdma6 = self.cbdma_list[5]
        cbdma7 = self.cbdma_list[6]
        cbdma8 = self.cbdma_list[7]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},lcore{core1}@{cbdma8},"
            f"lcore{core2}@{cbdma2},lcore{core2}@{cbdma3},lcore{core2}@{cbdma4},"
            f"lcore{core3}@{cbdma3},lcore{core3}@{cbdma4},lcore{core3}@{cbdma5},"
            f"lcore{core4}@{cbdma3},lcore{core4}@{cbdma4},lcore{core4}@{cbdma5},lcore{core4}@{cbdma6},"
            f"lcore{core5}@{cbdma1},lcore{core5}@{cbdma2},lcore{core5}@{cbdma3},lcore{core5}@{cbdma4},lcore{core5}@{cbdma5},lcore{core5}@{cbdma6},lcore{core5}@{cbdma7},lcore{core5}@{cbdma8}]"
        )
        vhost_param = (
            " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.logger.info("Launch virtio with packed ring mergeable inorder path")
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )

        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.logger.info("Quit and relaunch vhost and rerun step 4-6")
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

        self.logger.info("Quit and relaunch virtio with packed ring mergeable path")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.logger.info("Quit and relaunch vhost and rerun step 4-6")
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

        self.logger.info("Quit and relaunch virtio with packed ring non-mergeable path")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 10-12")
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

        self.logger.info(
            "Quit and relaunch virtio with packed ring inorder non-mergeable path"
        )
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 10-12")
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

        self.logger.info(
            "Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 "
        )
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 10-12")
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

        self.logger.info("Quit and relaunch vhost w/ iova=pa, Rerun steps 2-19")
        if not self.check_2M_env:
            self.virtio_user_pmd.quit()
            self.vhost_user_pmd.quit()
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq6;txq7]'"
            vhost_param = (
                " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
                + " --lcore-dma={}".format(lcore_dma)
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,packed_vq=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.logger.info("Launch virtio with packed ring mergeable inorder path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )

            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch vhost and rerun step 4-6")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch virtio with packed ring mergeable path")
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,packed_vq=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch vhost and rerun step 4-6")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info(
                "Quit and relaunch virtio with packed ring non-mergeable path"
            )
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,packed_vq=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 10-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info(
                "Quit and relaunch virtio with packed ring inorder non-mergeable path"
            )
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 10-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info(
                "Quit and relaunch virtio with packed ring vectorized path and ring size is not power of 2 "
            )
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,packed_vq=1,vectorized=1,queue_size=1025,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1025 --rxd=1025"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 10-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

    def test_server_mode_split_ring_all_path_multi_queues_payload_check_with_cbdma(
        self,
    ):
        """
        Test Case 2: loopback split ring all path cbdma test payload check with server mode and multi-queues
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(3)
        vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
        core1 = self.vhost_core_list[1]
        core2 = self.vhost_core_list[2]
        core3 = self.vhost_core_list[3]
        core4 = self.vhost_core_list[4]
        core5 = self.vhost_core_list[5]
        cbdma1 = self.cbdma_list[0]
        cbdma2 = self.cbdma_list[1]
        cbdma3 = self.cbdma_list[2]
        lcore_dma = (
            f"[lcore{core1}@{cbdma1},"
            f"lcore{core2}@{cbdma1},"
            f"lcore{core3}@{cbdma2},lcore{core3}@{cbdma3},"
            f"lcore{core4}@{cbdma2},lcore{core4}@{cbdma3},"
            f"lcore{core5}@{cbdma2},lcore{core5}@{cbdma3}]"
        )
        vhost_param = (
            " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            + " --lcore-dma={}".format(lcore_dma)
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
        self.logger.info("Launch virtio with split ring mergeable inorder path")
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.logger.info("Quit and relaunch vhost and rerun step 4-6")
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

        self.logger.info("Quit and relaunch virtio with split ring mergeable path")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_6192_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=6192)

        self.logger.info("Quit and relaunch vhost and rerun step 4-6")
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

        self.logger.info("Quit and relaunch virtio with split ring non-mergeable path")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
        virtio_param = (
            " --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 11-12")
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

        self.logger.info(
            "Quit and relaunch virtio with split ring inorder non-mergeable path"
        )
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 11-12")
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

        self.logger.info("Quit and relaunch virtio with split ring vectorized path")
        self.virtio_user_pmd.quit()
        virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1"
        virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param, param=virtio_param
        )
        self.launch_pdump_to_capture_pkt()
        self.send_960_packets_from_vhost()
        self.check_packet_payload_valid(pkt_len=960)

        self.logger.info("Quit and relaunch vhost and rerun step 11-12")
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

        self.logger.info("Quit and relaunch vhost w/ iova=pa, Rerun steps 2-19")
        if not self.check_2M_env:
            self.virtio_user_pmd.quit()
            self.vhost_user_pmd.quit()
            vhost_eal_param = "--vdev 'eth_vhost0,iface=vhost-net0,queues=8,client=1,dmas=[txq0;txq1;txq2;txq3;txq4;txq5;txq6]'"
            vhost_param = (
                " --nb-cores=5 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
                + " --lcore-dma={}".format(lcore_dma)
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.logger.info("Launch virtio with split ring mergeable inorder path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch vhost and rerun step 4-6")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch virtio with split ring mergeable path")
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=1,in_order=0,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info("Quit and relaunch vhost and rerun step 4-6")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_6192_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=6192)

            self.logger.info(
                "Quit and relaunch virtio with split ring non-mergeable path"
            )
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,server=1"
            virtio_param = " --enable-hw-vlan-strip --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 11-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info(
                "Quit and relaunch virtio with split ring inorder non-mergeable path"
            )
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 11-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch virtio with split ring vectorized path")
            self.virtio_user_pmd.quit()
            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=8,mrg_rxbuf=0,in_order=0,vectorized=1,server=1"
            virtio_param = " --nb-cores=1 --rxq=8 --txq=8 --txd=1024 --rxd=1024"
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

            self.logger.info("Quit and relaunch vhost and rerun step 11-12")
            self.vhost_user_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.launch_pdump_to_capture_pkt()
            self.send_960_packets_from_vhost()
            self.check_packet_payload_valid(pkt_len=960)

    def test_server_mode_split_ring_large_chain_packets_stress_test_with_cbdma(self):
        """
        Test Case 3: loopback split ring large chain packets stress test with server mode and cbdma enqueue
        """
        if not self.check_2M_env:
            self.get_cbdma_ports_info_and_bind_to_dpdk(1)
            vhost_eal_param = (
                "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0]'"
            )
            core1 = self.vhost_core_list[1]
            cbdma1 = self.cbdma_list[0]
            lcore_dma = f"[lcore{core1}@{cbdma1}]"
            vhost_param = " --nb-cores=1 --mbuf-size=65535" + " --lcore-dma={}".format(
                lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="va",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,server=1,mrg_rxbuf=1,in_order=0,vectorized=1,queue_size=2048"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.logger.info("Launch virtio with split ring vectorized path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )

            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

            self.logger.info(
                "Stop and quit vhost testpmd and relaunch vhost with iova=pa"
            )
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

    def test_server_mode_packed_ring_large_chain_packets_stress_test_with_cbdma(self):
        """
        Test Case 4: loopback split packed large chain packets stress test with server mode and cbdma enqueue
        """
        if not self.check_2M_env:
            self.get_cbdma_ports_info_and_bind_to_dpdk(1)
            vhost_eal_param = (
                "--vdev 'eth_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[txq0]'"
            )
            core1 = self.vhost_core_list[1]
            cbdma1 = self.cbdma_list[0]
            lcore_dma = f"[lcore{core1}@{cbdma1}]"
            vhost_param = " --nb-cores=1 --mbuf-size=65535" + " --lcore-dma={}".format(
                lcore_dma
            )
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="va",
            )

            virtio_eal_param = "--vdev=net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net0,queues=1,mrg_rxbuf=1,in_order=0,vectorized=1,packed_vq=1,queue_size=2048,server=1"
            virtio_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=2048 --rxd=2048"
            self.logger.info("Launch virtio with split ring vectorized path")
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio_eal_param,
                param=virtio_param,
            )

            self.send_chain_packets_from_vhost()
            self.verify_virtio_user_receive_packets()

            self.logger.info(
                "Stop and quit vhost testpmd and relaunch vhost with iova=pa"
            )
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
        self.virtio_user_pmd.quit()
        self.vhost_user_pmd.quit()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()