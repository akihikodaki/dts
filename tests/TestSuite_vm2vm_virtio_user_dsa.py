# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2022 Intel Corporation
#

import re

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

from .virtio_common import dsa_common as DC


class TestVM2VMVirtioUserDsa(TestCase):
    def set_up_all(self):
        self.dut_ports = self.dut.get_ports()
        self.port_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_list = self.dut.get_core_list(config="all", socket=self.port_socket)
        self.vhost_core_list = self.cores_list[0:2]
        self.virtio0_core_list = self.cores_list[2:4]
        self.virtio1_core_list = self.cores_list[4:6]
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
        self.dump_virtio_pcap = "/tmp/pdump-virtio-rx.pcap"
        self.dump_vhost_pcap = "/tmp/pdump-vhost-rx.pcap"

        self.DC = DC(self)

    def set_up(self):
        self.path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.path.split("/")[-1]
        self.app_pdump = self.dut.apps_name["pdump"]
        self.pdump_name = self.app_pdump.split("/")[-1]

        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("rm -rf %s" % self.dump_virtio_pcap, "#")
        self.dut.send_expect("rm -rf %s" % self.dump_vhost_pcap, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.pdump_name, "#")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect(
            "cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# "
        )
        return True if out == "2048" else False

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
        self.pdump_user.send_expect(command_line % (self.dump_virtio_pcap), "Port")

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

    def clear_virtio_user1_stats(self):
        self.virtio_user1_pmd.execute_cmd("stop")
        self.virtio_user1_pmd.execute_cmd("clear port stats all")
        self.virtio_user1_pmd.execute_cmd("start")
        out = self.virtio_user1_pmd.execute_cmd("show port stats all")
        self.logger.info(out)

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

    def send_502_64byte_and_64_8000byte_pkts(self):
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

    def send_1_64byte_pkts(self):
        """
        send 1 64byte length packets from virtio_user0 testpmd
        """
        self.virtio_user0_pmd.execute_cmd("set burst 1")
        self.virtio_user0_pmd.execute_cmd("start tx_first 1")
        self.virtio_user0_pmd.execute_cmd("stop")
        self.vhost_user_pmd.execute_cmd("start")
        self.vhost_user_pmd.execute_cmd("show port stats all")

    def test_split_non_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 1: VM2VM vhost-user/virtio-user split ring non-mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )
        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q1;txq1@%s-q1;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;txq1@%s-q1;rxq1@%s-q1;rxq1@%s-q1" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_inorder_non_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 2: VM2VM split ring inorder non-mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q2;rxq1@%s-q3" % (
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        port_options = {dsas[0]: "max_queues=4"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )
        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q1;txq1@%s-q1;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;txq1@%s-q1;rxq1@%s-q1;rxq1@%s-q1" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=2",
            dsas[1]: "max_queues=2",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_inorder_mergeable_multi_queues_non_indirect_descriptor_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 3: VM2VM split ring inorder mergeable path and multi-queues test non-indirect descriptor and payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        port_options = {dsas[0]: "max_queues=2"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )
        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q2;rxq1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q1;rxq1@%s-q2;rxq1@%s-q3" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
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

    def test_split_mergeable_multi_queues_indirect_descriptor_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 4: VM2VM split ring mergeable path and multi-queues test indirect descriptor and payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        port_options = {dsas[0]: "max_queues=1"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )
        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )
        self.start_pdump_to_capture_pkt()
        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )
        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q2;rxq1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q1;rxq1@%s-q2;rxq1@%s-q3" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
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

    def test_split_vectorized_multi_queues_payload_check_with_vhost_async_dpdk_driver(
        self,
    ):
        """
        Test Case 5: VM2VM split ring vectorized path and multi-queues payload check with vhost async operation and dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;rxq0@%s-q1;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q3;txq1@%s-q3;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[1],
            dsas[1],
        )
        dmas2 = "txq0@%s-q1;txq1@%s-q1;rxq1@%s-q3;rxq1@%s-q3" % (
            dsas[1],
            dsas[1],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_non_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 6: VM2VM packed ring non-mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;rxq1@%s-q1" % (
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q1;rxq1@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=4",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_inorder_non_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 7: VM2VM packed ring inorder non-mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;rxq1@%s-q1" % (
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        port_options = {
            dsas[0]: "max_queues=2",
            dsas[1]: "max_queues=2",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q5;txq1@%s-q6;rxq0@%s-q5;rxq1@%s-q6" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q5;txq1@%s-q6;rxq1@%s-q5;rxq1@%s-q6" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 8: VM2VM packed ring mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        port_options = {dsas[0]: "max_queues=1"}
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            port_options=port_options,
            ports=dsas[0:1],
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q2;rxq1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q4;txq1@%s-q5;rxq1@%s-q6;rxq1@%s-q7" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas[0:1],
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_inorder_mergeable_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 9: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;rxq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
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
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q0;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q1;rxq1@%s-q0;rxq1@%s-q1" % (
            dsas[1],
            dsas[1],
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            iova_mode="va",
        )
        self.start_pdump_to_capture_pkt()
        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_tx_multi_queues_indirect_descriptor_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 10: VM2VM packed ring vectorized-tx path and multi-queues test indirect descriptor and payload check with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;txq1@%s-q0;rxq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;txq1@%s-q1;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
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

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        dmas1 = "txq0@%s-q0;txq1@%s-q1;rxq0@%s-q2;rxq1@%s-q3" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q1" % (
            dsas[1],
            dsas[1],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        port_options = {
            dsas[0]: "max_queues=4",
            dsas[1]: "max_queues=2",
        }
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=False,
            ports=dsas,
            port_options=port_options,
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

    def test_packed_vectorized_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 11: VM2VM packed ring vectorized path and payload check test with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;txq1@%s-q0;rxq0@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q1;txq1@%s-q1;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
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

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_ringsize_not_powerof_2_multi_queues_payload_check_with_dpdk_driver(
        self,
    ):
        """
        Test Case 12: VM2VM packed ring vectorized path payload check test with ring size is not power of 2 with dsa dpdk driver
        """
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=2, driver_name="vfio-pci", socket=self.port_socket
        )
        dmas1 = "txq0@%s-q0;txq1@%s-q0;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        dmas2 = "txq0@%s-q0;txq1@%s-q0;rxq0@%s-q1;rxq1@%s-q1" % (
            dsas[0],
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )

        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
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

        virtio1_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--force-max-simd-bitwidth=512 --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_448_64byte_and_54_4640byte_pkts()
        check_dict = {64: 448, 4640: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_non_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 13: VM2VM split ring non-mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas1 = "txq0@%s;rxq1@%s" % (wqs[0], wqs[0])
        dmas2 = "txq0@%s;rxq1@%s" % (wqs[1], wqs[1])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_inorder_non_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 14: VM2VM split ring inorder non-mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        dmas1 = "txq0@%s;rxq1@%s" % (wqs[0], wqs[1])
        dmas2 = "txq0@%s;rxq1@%s" % (wqs[2], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_inorder_mergeable_multi_queues_non_indirect_descriptor_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 15: VM2VM split ring inorder mergeable path and multi-queues test non-indirect descriptor and payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        dmas1 = "txq0@%s;rxq1@%s" % (wqs[0], wqs[1])
        dmas2 = "txq0@%s;rxq1@%s" % (wqs[2], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=1,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_mergeable_multi_queues_indirect_descriptor_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 16: VM2VM split ring mergeable path and multi-queues test indirect descriptor and payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq0@%s" % (wqs[0], wqs[0], wqs[0], wqs[0])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq0@%s" % (wqs[1], wqs[1], wqs[1], wqs[1])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_vectorized_multi_queues_payload_check_with_vhost_async_operation_with_kernel_driver(
        self,
    ):
        """
        Test Case 17: VM2VM split ring vectorized path and multi-queues payload check with vhost async operation and dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=4, dsa_idxs=[0])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[0], wqs[0])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[0], wqs[0])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=0,in_order=0,vectorized=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_non_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 18: VM2VM packed ring non-mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas1 = "txq0@%s;rxq1@%s" % (wqs[0], wqs[0])
        dmas2 = "txq0@%s;rxq1@%s" % (wqs[1], wqs[1])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_inorder_non_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 19: VM2VM packed ring inorder non-mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        dmas1 = "txq0@%s;rxq1@%s" % (wqs[0], wqs[1])
        dmas2 = "txq0@%s;rxq1@%s" % (wqs[2], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 20: VM2VM packed ring mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[1], wqs[1])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[1], wqs[1], wqs[0], wqs[0])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=0,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_inorder_mergeable_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 21: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=1, dsa_idxs=[0, 1])
        dmas1 = "txq0@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[0])
        dmas2 = "txq0@%s;txq1@%s;rxq1@%s" % (wqs[1], wqs[1], wqs[1])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_960byte_and_64_64byte_pkts()
        check_dict = {960: 502, 64: 64}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_tx_multi_queues_indirect_descriptor_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 22: VM2VM packed ring vectorized-tx path and multi-queues test indirect descriptor and payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[1], wqs[1])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[2], wqs[2], wqs[3], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_multi_queues_indirect_descriptor_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 23: VM2VM packed ring vectorized path and multi-queues test indirect descriptor and payload check with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[1], wqs[1])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[2], wqs[2], wqs[3], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_ringsize_not_powerof_2_multi_queues_payload_check_with_kernel_driver(
        self,
    ):
        """
        Test Case 24: VM2VM packed ring vectorized path payload check test with ring size is not power of 2 with dsa kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0, 1])
        dmas1 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[1], wqs[1])
        dmas2 = "txq0@%s;txq1@%s;rxq0@%s;rxq1@%s" % (wqs[2], wqs[2], wqs[3], wqs[3])
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
        self.start_vhost_testpmd(
            cores=self.vhost_core_list,
            eal_param=vhost_eal_param,
            param=vhost_param,
            no_pci=True,
            iova_mode="va",
        )

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=0,in_order=1,vectorized=1,queue_size=4097"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4097 --rxd=4097"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 0}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_split_mergeable_multi_queues_indirect_descriptor_payload_check_with_dpdk_and_kernel_driver(
        self,
    ):
        """
        Test Case 25: VM2VM split ring mergeable path and multi-queues test indirect descriptor with dsa dpdk and kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1,
            driver_name="vfio-pci",
            dsa_idxs=[1],
            socket=self.port_socket,
        )
        dmas1 = "txq0@%s;rxq0@%s;rxq1@%s" % (wqs[0], wqs[0], wqs[0])
        dmas2 = "txq0@%s-q0;txq1@%s-q0;rxq1@%s-q0" % (
            dsas[0],
            dsas[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256 --no-flush-rx"
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

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,mrg_rxbuf=1,in_order=0,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_502_64byte_and_64_8000byte_pkts()
        check_dict = {64: 502, 8000: 10}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_inorder_mergeable_multi_queues_payload_check_with_dpdk_and_kernel_driver(
        self,
    ):
        """
        Test Case 26: VM2VM packed ring inorder mergeable path and multi-queues payload check with dsa dpdk and kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1,
            driver_name="vfio-pci",
            dsa_idxs=[1],
            socket=self.port_socket,
        )
        dmas1 = "txq0@%s-q0;txq1@%s;rxq0@%s-q0;rxq1@%s" % (
            dsas[0],
            wqs[0],
            dsas[0],
            wqs[0],
        )
        dmas2 = "txq0@%s;txq1@%s-q0;rxq0@%s;rxq1@%s-q0" % (
            wqs[0],
            dsas[0],
            wqs[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
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

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,queue_size=4096"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_54_4640byte_and_448_64byte_pkts()
        check_dict = {4640: 54, 64: 448}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def test_packed_vectorized_tx_batch_processing_with_dpdk_and_kernel_driver(
        self,
    ):
        """
        Test Case 27: VM2VM packed ring vectorized-tx path test batch processing with dsa dpdk and kernel driver
        """
        wqs = self.DC.create_wq(wq_num=2, dsa_idxs=[0])
        dsas = self.DC.bind_dsa_to_dpdk_driver(
            dsa_num=1,
            driver_name="vfio-pci",
            dsa_idxs=[1],
            socket=self.port_socket,
        )
        dmas1 = "txq0@%s-q0;txq1@%s;rxq0@%s-q0;rxq1@%s" % (
            dsas[0],
            wqs[0],
            dsas[0],
            wqs[0],
        )
        dmas2 = "txq0@%s;txq1@%s-q0;rxq0@%s;rxq1@%s-q0" % (
            wqs[0],
            dsas[0],
            wqs[0],
            dsas[0],
        )
        vhost_eal_param = (
            "--vdev 'eth_vhost0,iface=vhost-net0,queues=2,client=1,dmas=[%s]' "
            "--vdev 'eth_vhost1,iface=vhost-net1,queues=2,client=1,dmas=[%s]'"
            % (dmas1, dmas2)
        )
        vhost_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=4096 --rxd=4096 --no-flush-rx"
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

        virtio1_eal_param = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio1_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net1(
            cores=self.virtio1_core_list,
            eal_param=virtio1_eal_param,
            param=virtio1_param,
        )

        self.start_pdump_to_capture_pkt()

        virtio0_eal_param = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=2,server=1,packed_vq=1,mrg_rxbuf=1,in_order=1,vectorized=1,queue_size=256"
        virtio0_param = "--nb-cores=1 --rxq=2 --txq=2 --txd=256 --rxd=256"
        self.start_virtio_testpmd_with_vhost_net0(
            cores=self.virtio0_core_list,
            eal_param=virtio0_eal_param,
            param=virtio0_param,
        )

        self.send_1_64byte_pkts()
        check_dict = {64: 2}
        self.check_virtio_user1_stats(check_dict)
        self.check_packet_payload_valid(check_dict)

    def quit_all_testpmd(self):
        self.vhost_user_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user0_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user1_pmd.execute_cmd("quit", "#", 60)
        self.pdump_user.send_expect("^c", "# ", 60)

    def tear_down(self):
        self.quit_all_testpmd()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT %s" % self.pdump_name, "#")

    def tear_down_all(self):
        pass
