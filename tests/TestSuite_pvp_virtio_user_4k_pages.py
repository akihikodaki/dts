# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

"""
DPDK Test suite.
vhost/virtio-user pvp with 4K pages.
"""

import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.test_case import TestCase


class TestPvpVirtioUser4kPages(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.core_config = "1S/4C/1T"
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4,
            "There has not enought cores to test this suite %s" % self.suite_name,
        )
        # for this suite, only support for vfio-pci
        self.dut.send_expect("modprobe vfio-pci", "# ")
        for i in self.dut_ports:
            port = self.dut.ports_info[i]["port"]
            port.bind_driver("vfio-pci")

        self.core_list = self.dut.get_core_list(
            self.core_config, socket=self.ports_socket
        )
        self.core_list_virtio_user = self.core_list[0:2]
        self.core_list_vhost_user = self.core_list[2:4]
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.logger.info(
            "You can config packet_size in file %s.cfg," % self.suite_name
            + " in region 'suite' like packet_sizes=[64, 128, 256]"
        )
        if "packet_sizes" in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()["packet_sizes"]

        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.number_of_ports = 1
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost-net*", "# ")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {
            64: 0.08,
            128: 0.10,
            256: 0.18,
            512: 0.20,
            1024: 0.40,
            1280: 0.45,
            1518: 0.50,
        }
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def send_and_verify(self):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            pkt = Packet(pkt_type="UDP", pkt_len=frame_size)
            pkt.config_layer("ether", {"dst": "%s" % self.dst_mac})
            pkt.save_pcapfile(self.tester, "%s/vhost.pcap" % self.out_path)
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(
                tgen_input, 100, None, self.tester.pktgen
            )
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
            Mpps = pps / 1000000.0
            self.verify(
                Mpps > self.check_value[frame_size],
                "%s of frame size %d speed verify failed, expect %s, result %s"
                % (self.running_case, frame_size, self.check_value[frame_size], Mpps),
            )
            throughput = Mpps * 100 / float(self.wirespeed(self.nic, 64, 1))

            results_row = [frame_size]
            results_row.append("4K pages")
            results_row.append(Mpps)
            results_row.append("1")
            results_row.append(throughput)
            self.result_table_add(results_row)

    def start_testpmd_as_vhost(self):
        """
        Start testpmd on vhost
        """
        testcmd = self.app_testpmd_path + " "
        vdev = "net_vhost0,iface=vhost-net,queues=1"
        para = " -- -i --no-numa --socket-num=%d" % self.ports_socket
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_vhost_user,
            prefix="vhost",
            ports=[self.pci_info],
            vdevs=[vdev],
        )
        command_line_client = testcmd + eal_params + " -m 1024 --no-huge" + para
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def start_testpmd_as_virtio(self, packed=False):
        """
        Start testpmd on virtio
        """
        testcmd = self.app_testpmd_path + " "
        vdev = (
            "net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1"
            if not packed
            else "net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,packed_vq=1,queues=1"
        )
        eal_params = self.dut.create_eal_parameters(
            cores=self.core_list_virtio_user,
            prefix="virtio-user",
            ports=[self.pci_info],
            vdevs=[vdev],
        )
        command_line_user = testcmd + eal_params + " --no-huge -m 1024 -- -i"
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)
        self.virtio_user.send_expect("start", "testpmd> ", 120)

    def prepare_tmpfs_for_4k(self):
        """
        Prepare tmpfs with 4K-pages
        """
        self.dut.send_expect("mkdir -p /mnt/tmpfs_nohuge", "# ")
        self.dut.send_expect("mount tmpfs /mnt/tmpfs_nohuge -t tmpfs -o size=4G", "# ")

    def restore_env_of_tmpfs_for_4k(self):
        self.dut.send_expect("umount /mnt/tmpfs_nohuge", "# ")

    def close_all_apps(self):
        """
        Close testpmd
        """
        self.virtio_user.send_expect("quit", "# ", 60)
        self.vhost_user.send_expect("quit", "# ", 60)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

    def test_perf_pvp_virtio_user_split_ring_with_4K_pages(self):
        """
        Basic test for virtio-user 4K pages
        """
        self.start_testpmd_as_vhost()
        self.prepare_tmpfs_for_4k()
        self.start_testpmd_as_virtio()
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def test_perf_pvp_virtio_user_packed_ring_with_4K_pages(self):
        """
        Basic test for virtio-user 4K pages
        """
        self.start_testpmd_as_vhost()
        self.prepare_tmpfs_for_4k()
        self.start_testpmd_as_virtio(packed=True)
        self.send_and_verify()
        self.result_table_print()
        self.close_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.restore_env_of_tmpfs_for_4k()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
