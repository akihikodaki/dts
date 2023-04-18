# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from tests.virtio_common import cbdma_common as CC


class TestVM2VMVirtioUserCbdma(TestCase):
    def set_up_all(self):
        self.memory_channel = self.dut.get_memory_channels()
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.src_dump_virtio_pcap = "%s/pdump-virtio-rx.pcap" % self.base_dir
        self.dst_dump_virtio_pcap = "/tmp/pdump-virtio-rx.pcap"
        self.app_pdump = self.dut.apps_name["pdump"]
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio0_core_list = self.cores_list[10:13]
        self.virtio1_core_list = self.cores_list[13:16]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pdump_user = self.dut.new_session(suite="pdump-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.app_pdump = self.dut.apps_name["pdump"]
        self.pdump_name = self.app_pdump.split("/")[-1]
        self.CC = CC(self)

    def set_up(self):
        """
        run before each test case.
        """
        self.nopci = True
        self.queue_num = 1
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("rm -rf %s" % self.src_dump_virtio_pcap, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.pdump_name, "#")

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num, allow_diff_socket=False):
        """
        get and bind cbdma ports into DPDK driver
        """
        self.all_cbdma_list = []
        cbdmas = []
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
        cbdmas = self.all_cbdma_list[0:cbdma_num]
        self.cbdma_str = " ".join(cbdmas)
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

    def send_502_960byte_and_64_64byte_pkts(self):
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
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def send_502_64byte_and_64_4640byte_pkts(self):
        """
        send 502 64byte and 64 4640byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64,256,2000,64,256,2000")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def send_448_64byte_and_54_4640byte_pkts(self):
        """
        send 448 64byte and 54 4640byte length packets from virtio_user0 testpmd
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
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def send_502_64byte_and_64_8000byte_pkts(self):
        """
        send 54 4640byte and 448 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("set txpkts 64")
        self.virtio_user0_pmd.execute_cmd("start tx_first 27")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set burst 32")
        self.virtio_user0_pmd.execute_cmd("start tx_first 7")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.virtio_user0_pmd.execute_cmd("set txpkts 2000,2000,2000,2000")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def send_54_4640byte_and_448_64byte_pkts(self):
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
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def send_1_64byte_pkts(self):
        """
        send 1 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("show port stats all")

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
        command_line = (
            self.app_pdump
            + "-l 1-2 -n 4 --file-prefix=virtio-user1 -v -- "
            + "--pdump  'device_id=net_virtio_user1,queue=*,rx-dev=%s,mbuf-size=8000'"
        )
        self.pdump_user.send_expect(command_line % (self.src_dump_virtio_pcap), "Port")

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
            src=self.src_dump_virtio_pcap, dst=self.dst_dump_virtio_pcap
        )
        pkt = Packet()
        pkts = pkt.read_pcapfile(self.dst_dump_virtio_pcap)
        for key, value in check_dict.items():
            count = 0
            for i in range(len(pkts)):
                if len(pkts[i]) == key:
                    count += 1
            self.verify(
                value == count,
                "pdump file: {} have not include enough packets {}".format(count, key),
            )

    def quit_all_testpmd(self):
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.pdump_user.send_expect("^c", "# ", 60)

    def test_split_ring_non_mergeable_path_multi_queues_payload_check_with_cbdma_enable(
        self,
    ):
        """
        Test Case 1: VM2VM split ring non-mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
            iova_mode="va",
        )
        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = (
            " --enable-hw-vlan-strip --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = (
            " --enable-hw-vlan-strip --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[1],
            cbdmas[1],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[2],
            cbdmas[2],
            cbdmas[3],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_ping_inorder_non_mergeable_path_multi_queues_payload_check_with_cbdma_enable(
        self,
    ):
        """
        Test Case 2: VM2VM split ring inorder non-mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_4640byte_pkts()
        check_dict = {64: 502, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[1],
            cbdmas[1],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[2],
            cbdmas[2],
            cbdmas[3],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_502_64byte_and_64_4640byte_pkts()
        check_dict = {64: 502, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_ring_verctorized_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 3: VM2VM split ring vectorized path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,,vectorized=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[4],
            cbdmas[5],
            cbdmas[6],
            cbdmas[7],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_ring_inorder_mergeable_path_test_non_indirect_descriptor_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 4: VM2VM split ring inorder mergeable path test non-indirect descriptor with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:2],
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[4],
            cbdmas[5],
            cbdmas[6],
            cbdmas[7],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
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

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_ring_mergeable_path_test_indirect_descriptor_with_cbdma_enable(self):
        """
        Test Case 5: VM2VM split ring mergeable path test indirect descriptor with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq0@%s;rxq1@%s;rxq0@%s" % (
            cbdmas[1],
            cbdmas[1],
            cbdmas[1],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:2],
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio1_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[4],
            cbdmas[5],
            cbdmas[6],
            cbdmas[7],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
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

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_non_mergeable_path_multi_queues_payload_check_with_cbdma_enable(
        self,
    ):
        """
        Test Case 6: VM2VM packed ring non-mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[0],
            cbdmas[1],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[0],
            cbdmas[1],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = (
            " --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = (
            " --enable-hw-vlan-strip --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        )
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[1],
        )
        dmas2 = "txq0@%s;rxq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_mergeable_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 7: VM2VM packed ring mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq0@%s;rxq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[4],
            cbdmas[5],
            cbdmas[6],
            cbdmas[7],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_mergeable_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 8: VM2VM packed ring inorder mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq0@%s;rxq1@%s;rxq0@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_inorder_non_mergeable_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 9: VM2VM packed ring inorder non-mergeable path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq0@%s" % (cbdmas[0], cbdmas[1])
        dmas2 = "txq1@%s;rxq1@%s" % (cbdmas[0], cbdmas[1])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:2],
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

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio0_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_vectorized_rx_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 10: VM2VM packed ring vectorized-rx path multi-queues payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq0@%s" % (cbdmas[0], cbdmas[0])
        dmas2 = "txq1@%s;rxq1@%s" % (cbdmas[0], cbdmas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=2 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_vectorized_path_multi_queues_payload_check_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 11: VM2VM packed ring vectorized path multi-queues payload check test with ring size is not power of 2 with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=8, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
            cbdmas[0],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.clear_virtio_user1_stats()
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[0],
            cbdmas[1],
        )
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[2],
            cbdmas[3],
            cbdmas[2],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = (
            " --nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:4],
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_pakced_packed_ring_vectorized_tx_path_multi_queues_test_indirect_descriptor_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 12: VM2VM packed ring vectorized-tx path multi-queues test indirect descriptor and payload check with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=4, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "rxq0@%s" % (cbdmas[0])
        dmas2 = "txq1@%s" % (cbdmas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas[0:1],
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

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        dmas2 = "txq0@%s;txq0@%s;rxq0@%s;rxq1@%s" % (
            cbdmas[0],
            cbdmas[1],
            cbdmas[2],
            cbdmas[3],
        )
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
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

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_ring_vectorized_tx_path_test_batch_processing_with_cbdma_enabled(
        self,
    ):
        """
        Test Case 13: VM2VM packed ring vectorized-tx path test batch processing with cbdma enable
        """
        cbdmas = self.CC.bind_cbdma_to_dpdk_driver(
            cbdma_num=1, driver_name="vfio-pci", socket=self.ports_socket
        )
        dmas1 = "txq0@%s;rxq0@%s" % (cbdmas[0], cbdmas[0])
        dmas2 = "txq0@%s;rxq0@%s" % (cbdmas[0], cbdmas[0])
        vhost_eal_param = (
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1,client=1,dmas=[%s]' "
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = " --nb-cores=1 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=cbdmas,
            iova_mode="va",
        )

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = " --nb-cores=1 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=1,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = " --nb-cores=1 --txd=256 --rxd=256"
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
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.pdump_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.CC.bind_cbdma_to_kernel_driver(cbdma_idxs="all")
        self.close_all_session()
