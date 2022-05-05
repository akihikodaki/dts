# BSD LICENSE
#
# Copyright(c) <2022> Intel Corporation.
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

Test cases for vm2vm virtio-user
This suite include split virtqueue vm2vm in-order mergeable,
in-order non-mergeable,mergeable, non-mergeable, vector_rx path
test and packed virtqueue vm2vm in-order mergeable, in-order non-mergeable,
mergeable, non-mergeable path test
"""
import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase


class TestVM2VMVirtioUserCbdma(TestCase):
    def set_up_all(self):
        self.memory_channel = self.dut.get_memory_channels()
        self.dump_virtio_pcap = "/tmp/pdump-virtio-rx.pcap"
        self.dump_vhost_pcap = "/tmp/pdump-vhost-rx.pcap"
        self.app_pdump = self.dut.apps_name["pdump"]
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio0_core_list = self.cores_list[10:12]
        self.virtio1_core_list = self.cores_list[12:14]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pdump_user = self.dut.new_session(suite="pdump-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)
        self.testpmd_name = self.dut.apps_name['test-pmd'].split("/")[-1]

    def set_up(self):
        """
        run before each test case.
        """
        self.nopci = True
        self.queue_num = 1
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("rm -rf %s" % self.dump_virtio_pcap, "#")
        self.dut.send_expect("rm -rf %s" % self.dump_vhost_pcap, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

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

    @staticmethod
    def generate_dms_param(queues):
        das_list = []
        for i in range(queues):
            das_list.append("txq{}".format(i))
        das_param = "[{}]".format(";".join(das_list))
        return das_param

    @staticmethod
    def generate_lcore_dma_param(cbdma_list, core_list):
        group_num = int(len(cbdma_list) / len(core_list))
        lcore_dma_list = []
        if len(cbdma_list) == 1:
            for core in core_list:
                lcore_dma_list.append("lcore{}@{}".format(core, cbdma_list[0]))
        elif len(core_list) == 1:
            for cbdma in cbdma_list:
                lcore_dma_list.append("lcore{}@{}".format(core_list[0], cbdma))
        else:
            for cbdma in cbdma_list:
                core_list_index = int(cbdma_list.index(cbdma) / group_num)
                lcore_dma_list.append(
                    "lcore{}@{}".format(core_list[core_list_index], cbdma)
                )
        lcore_dma_param = "[{}]".format(",".join(lcore_dma_list))
        return lcore_dma_param

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

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

    def start_vhost_testpmd(
        self, cores, eal_param="", param="", ports="", iova_mode=""
    ):
        if iova_mode:
            eal_param += " --iova=" + iova_mode
        self.vhost_user_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            ports=ports,
            prefix="vhost",
            fixed_prefix=True,
        )

    def start_virtio_testpmd_with_vhost_net1(self, cores, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net1
        """
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user1_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user1",
            fixed_prefix=True,
        )
        self.virtio_user1_pmd.execute_cmd("set fwd rxonly")
        self.virtio_user1_pmd.execute_cmd("start")

    def start_virtio_testpmd_with_vhost_net0(self, cores, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        self.virtio_user0_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )

    def send_251_960byte_and_32_64byte_pkts(self):
        """
        send 251 960byte and 32 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64,128,256,512")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        out = self.vhost_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def send_27_4640byte_and_224_64byte_pkts(self):
        """
        send 54 4640byte and 448 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64,256,2000,64,256,2000")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        out = self.vhost_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def send_224_64byte_and_27_4640byte_pkts(self):
        """
        send 54 4640byte and 448 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64,256,2000,64,256,2000")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        out = self.vhost_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def send_251_64byte_and_32_8000byte_pkts(self):
        """
        send 54 4640byte and 448 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set txpkts 2000,2000,2000,2000")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        out = self.vhost_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def send_1_64byte_pkts(self):
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        out = self.vhost_user_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def clear_virtio_user1_stats(self):
        self.virtio_user1_pmd.execute_cmd("stop")
        self.virtio_user1_pmd.execute_cmd("clear port stats all")
        self.virtio_user1_pmd.execute_cmd("start")
        out = self.virtio_user1_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

    def start_pdump_to_capture_pkt(self):
        """
        launch pdump app with dump_port and file_prefix
        the pdump app should start after testpmd started
        if dump the vhost-testpmd, the vhost-testpmd should started before launch pdump
        if dump the virtio-testpmd, the virtio-testpmd should started before launch pdump
        """
        eal_params = self.dut.create_eal_parameters(
            cores="Default", prefix="virtio-user1", fixed_prefix=True
        )
        command_line = (
            self.app_pdump
            + " %s -v -- "
            + "--pdump  'device_id=net_virtio_user1,queue=*,rx-dev=%s,mbuf-size=8000'"
        )
        self.pdump_user.send_expect(
            command_line % (eal_params, self.dump_virtio_pcap), "Port"
        )

    def check_virtio_user1_stats(self, check_dict):
        """
        check the virtio-user1 show port stats
        """
        out = self.virtio_user1_pmd.execute_cmd("show port stats all")
        self.logger.info(out)
        rx_packets = re.search("RX-packets:\s*(\d*)", out)
        rx_bytes = re.search("RX-bytes:\s*(\d*)", out)
        rx_num = int(rx_packets.group(1))
        byte_num = int(rx_bytes.group(1))
        packet_count = 0
        byte_count = 0
        for key, value in check_dict.items():
            packet_count += value
            byte_count += key * value
        self.verify(
            rx_num == packet_count,
            "receive pakcet number: {} is not equal as send:{}".format(
                rx_num, packet_count
            ),
        )
        self.verify(
            byte_num == byte_count,
            "receive pakcet byte:{} is not equal as send:{}".format(
                byte_num, byte_count
            ),
        )

    def check_packet_payload_valid(self, check_dict):
        """
        check the payload is valid
        """
        self.pdump_user.send_expect("^c", "# ", 60)
        self.dut.session.copy_file_from(
            src=self.dump_virtio_pcap, dst=self.dump_virtio_pcap
        )
        pkt = Packet()
        pkts = pkt.read_pcapfile(self.dump_virtio_pcap)
        for key, value in check_dict.items():
            count = 0
            for i in range(len(pkts)):
                if len(pkts[i]) == key:
                    count += 1
            self.verify(
                value == count,
                "pdump file: {} have not include enough packets {}".format(count, key),
            )

    def check_vhost_user_testpmd_logs(self):
        out = self.vhost_user.get_session_before(timeout=30)
        check_logs = [
            "DMA completion failure on channel",
            "DMA copy failed for channel",
        ]
        for check_log in check_logs:
            self.verify(check_log not in out, "Vhost-user testpmd Exception")

    def quit_all_testpmd(self):
        self.vhost_user_pmd.quit()
        self.virtio_user0_pmd.quit()
        self.virtio_user1_pmd.quit()
        self.pdump_user.send_expect("^c", "# ", 60)

    def test_split_ring_non_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 1: split virtqueue vm2vm non-mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = (
            " --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = (
            " --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_251_960byte_and_32_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)
        self.check_vhost_user_testpmd_logs()

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_251_960byte_and_32_64byte_pkts()
            check_dict = {960: 502, 64: 64}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)
            self.check_vhost_user_testpmd_logs()

    def test_split_ring_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 2: split virtqueue vm2vm mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list[0:1], core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_27_4640byte_and_224_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_27_4640byte_and_224_64byte_pkts()
            check_dict = {4640: 54, 64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_split_ring_inorder_non_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 3: split virtqueue vm2vm inorder non-mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(5)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=0,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_27_4640byte_and_224_64byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_27_4640byte_and_224_64byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_split_ring_vectorized_path_multi_queues_with_cbdma(self):
        """
        Test Case 4: split virtqueue vm2vm vectorized path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0],dma_ring_size=2048'"
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq1],dma_ring_size=2048'"
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_224_64byte_and_27_4640byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_224_64byte_and_27_4640byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_split_ring_inorder_mergeable_path_multi_queues_test_non_indirect_descriptor_with_cbdma(
        self,
    ):
        """
        Test Case 5: Split virtqueue vm2vm inorder mergeable path test non-indirect descriptor with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(4)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=256 --rxd=256 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_251_64byte_and_32_8000byte_pkts()
        check_dict = {64: 502, 8000: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.virtio_user1_pmd.quit()
            self.virtio_user0_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_virtio_testpmd_with_vhost_net1(
                cores=self.virtio1_core_list,
                eal_param=virtio1_eal_param,
                param=virtio1_param,
            )
            self.start_pdump_to_capture_pkt()
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio0_eal_param,
                param=virtio0_param,
            )

            self.send_251_64byte_and_32_8000byte_pkts()
            check_dict = {64: 502, 8000: 2}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_split_ring_inorder_mergeable_path_multi_queues_test_indirect_descriptor_with_cbdma(
        self,
    ):
        """
        Test Case 6: Split virtqueue vm2vm mergeable path test indirect descriptor with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(4)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=256 --rxd=256 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=0,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_251_64byte_and_32_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.virtio_user1_pmd.quit()
            self.virtio_user0_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_virtio_testpmd_with_vhost_net1(
                cores=self.virtio1_core_list,
                eal_param=virtio1_eal_param,
                param=virtio1_param,
            )
            self.start_pdump_to_capture_pkt()
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio0_eal_param,
                param=virtio0_param,
            )

            self.send_251_64byte_and_32_8000byte_pkts()
            check_dict = {64: 502, 8000: 10}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_non_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 7: packed virtqueue vm2vm non-mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_224_64byte_and_27_4640byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_224_64byte_and_27_4640byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 8: packed virtqueue vm2vm mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list[0:1], core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_27_4640byte_and_224_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_27_4640byte_and_224_64byte_pkts()
            check_dict = {4640: 54, 64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 9: packed virtqueue vm2vm inorder mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(5)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_27_4640byte_and_224_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_27_4640byte_and_224_64byte_pkts()
            check_dict = {4640: 54, 64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_non_mergeable_path_multi_queues_with_cbdma(self):
        """
        Test Case 10: packed virtqueue vm2vm inorder non-mergeable path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        dmas = self.generate_dms_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_224_64byte_and_27_4640byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_224_64byte_and_27_4640byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_vectorized_rx_path_multi_queues_with_cbdma(self):
        """
        Test Case 11: packed virtqueue vm2vm vectorized-rx path multi-queues payload check with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:3]
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[txq0],dma_ring_size=2048'"
            + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[txq1],dma_ring_size=2048'"
        )
        vhost_param = (
            " --nb-cores=2 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_224_64byte_and_27_4640byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_224_64byte_and_27_4640byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_vectorized_path_multi_queues_check_with_ring_size_is_not_power_of_2_queues_with_cbdma(
        self,
    ):
        """
        Test Case 12: packed virtqueue vm2vm vectorized path multi-queues payload check with ring size is not power of 2 and cbdma enabled
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=4096 --rxd=4096 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_224_64byte_and_27_4640byte_pkts()
        check_dict = {64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.clear_virtio_user1_stats()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_pdump_to_capture_pkt()

            self.send_224_64byte_and_27_4640byte_pkts()
            check_dict = {64: 448}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_vectorized_tx_path_multi_queues_test_indirect_descriptor_with_cbdma(
        self,
    ):
        """
        Test Case 13: packed virtqueue vm2vm vectorized-tx path multi-queues test indirect descriptor with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        dmas = self.generate_dms_param(2)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=256 --rxd=256 --txq=2 --rxq=2 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_251_64byte_and_32_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        if not self.check_2M_env:
            self.logger.info("Quit and relaunch vhost with iova=pa")
            self.vhost_user_pmd.quit()
            self.virtio_user1_pmd.quit()
            self.virtio_user0_pmd.quit()
            self.start_vhost_testpmd(
                cores=self.vhost_core_list,
                eal_param=vhost_eal_param,
                param=vhost_param,
                ports=self.cbdma_list,
                iova_mode="pa",
            )
            self.start_virtio_testpmd_with_vhost_net1(
                cores=self.virtio1_core_list,
                eal_param=virtio1_eal_param,
                param=virtio1_param,
            )
            self.start_pdump_to_capture_pkt()
            self.start_virtio_testpmd_with_vhost_net0(
                cores=self.virtio0_core_list,
                eal_param=virtio0_eal_param,
                param=virtio0_param,
            )

            self.send_251_64byte_and_32_8000byte_pkts()
            check_dict = {64: 502, 8000: 10}
            self.check_virtio_user1_stats(check_dict)
            self.check_packet_payload_valid(check_dict)

    def test_packed_ring_vectorized_tx_path_test_batch_processing_with_cbdma(self):
        """
        Test Case 14: packed virtqueue vm2vm vectorized-tx path test batch processing with cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(8)
        dmas = self.generate_dms_param(1)
        lcore_dma = self.generate_lcore_dma_param(
            cbdma_list=self.cbdma_list, core_list=self.vhost_core_list[1:2]
        )
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=1,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        ) + " --vdev 'net_vhost1,iface=vhost-net1,queues=1,client=1,dmas={},dma_ring_size=2048'".format(
            dmas
        )
        vhost_param = (
            " --nb-cores=1 --txd=256 --rxd=256 --txq=1 --rxq=1 --no-flush-rx"
            + " --lcore-dma={}".format(lcore_dma)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=self.cbdma_list,
            iova_mode="va",
        )

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=1 --txq=1 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_1_64byte_pkts()
        check_dict = {64: 1}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def close_all_session(self):
        if getattr(self, "vhost_user", None):
            self.dut.close_session(self.vhost_user)
        if getattr(self, "virtio-user0", None):
            self.dut.close_session(self.virtio_user0)
        if getattr(self, "virtio-user1", None):
            self.dut.close_session(self.virtio_user1)
        if getattr(self, "pdump_session", None):
            self.dut.close_session(self.pdump_user)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.quit_all_testpmd()
        self.dut.kill_all()
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_all_session()
