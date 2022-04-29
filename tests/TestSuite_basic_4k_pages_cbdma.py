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
vhost/virtio-user pvp with 4K pages.
"""

import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase
from framework.virt_common import VM


class TestBasic4kPagesCbdma(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n["socket"]) == 0])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(
            self.cores_num >= 4,
            "There has not enought cores to test this suite %s" % self.suite_name,
        )
        self.cores_list = self.dut.get_core_list(config="all", socket=self.ports_socket)
        self.vhost_core_list = self.cores_list[0:9]
        self.virtio0_core_list = self.cores_list[9:11]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.pci_info = self.dut.ports_info[0]["pci"]
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.out_path = "/tmp/%s" % self.suite_name
        out = self.tester.send_expect("ls -d %s" % self.out_path, "# ")
        if "No such file or directory" in out:
            self.tester.send_expect("mkdir -p %s" % self.out_path, "# ")
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.number_of_ports = 1
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vm_num = 2
        self.virtio_ip1 = "1.1.1.1"
        self.virtio_ip2 = "1.1.1.2"
        self.virtio_mac1 = "52:54:00:00:00:01"
        self.virtio_mac2 = "52:54:00:00:00:02"
        self.base_dir = self.dut.base_dir.replace("~", "/root")

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf /tmp/vhost-net*", "# ")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.umount_tmpfs_for_4k()
        # Prepare the result table
        self.table_header = ["Frame"]
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("Queue Num")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.vm_dut = []
        self.vm = []

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
            # self.verify(Mpps > self.check_value[frame_size],
            #             "%s of frame size %d speed verify failed, expect %s, result %s" % (
            #                 self.running_case, frame_size, self.check_value[frame_size], Mpps))
            throughput = Mpps * 100 / float(self.wirespeed(self.nic, 64, 1))
            results_row = [frame_size]
            results_row.append("4K pages")
            results_row.append(Mpps)
            results_row.append("1")
            results_row.append(throughput)
            self.result_table_add(results_row)

    def start_vhost_user_testpmd(self, cores, param="", eal_param="", ports=""):
        """
        launch the testpmd as virtio with vhost_user
        """
        self.vhost_user_pmd.start_testpmd(
            cores=cores,
            param=param,
            eal_param=eal_param,
            ports=ports,
            prefix="vhost",
            fixed_prefix=True,
        )

    def start_virtio_user0_testpmd(self, cores, eal_param="", param=""):
        """
        launch the testpmd as virtio with vhost_net0
        """
        self.virtio_user0_pmd.start_testpmd(
            cores=cores,
            eal_param=eal_param,
            param=param,
            no_pci=True,
            prefix="virtio-user0",
            fixed_prefix=True,
        )

    def start_vms(
        self,
        setting_args="",
        server_mode=False,
        opt_queue=None,
        vm_config="vhost_sample",
    ):
        """
        start one VM, each VM has one virtio device
        """
        vm_params = {}
        if opt_queue is not None:
            vm_params["opt_queue"] = opt_queue

        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, "vm%d" % i, vm_config)

            vm_params["driver"] = "vhost-user"
            if not server_mode:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            else:
                vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i + ",server"
            vm_params["opt_mac"] = "52:54:00:00:00:0%d" % (i + 1)
            vm_params["opt_settings"] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start(set_target=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print((utils.RED("Failure for %s" % str(e))))
                raise e
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_vm_ip(self):
        """
        set virtio device IP and run arp protocal
        """
        vm1_intf = self.vm_dut[0].ports_info[0]["intf"]
        vm2_intf = self.vm_dut[1].ports_info[0]["intf"]
        self.vm_dut[0].send_expect(
            "ifconfig %s %s" % (vm1_intf, self.virtio_ip1), "#", 10
        )
        self.vm_dut[1].send_expect(
            "ifconfig %s %s" % (vm2_intf, self.virtio_ip2), "#", 10
        )
        self.vm_dut[0].send_expect(
            "arp -s %s %s" % (self.virtio_ip2, self.virtio_mac2), "#", 10
        )
        self.vm_dut[1].send_expect(
            "arp -s %s %s" % (self.virtio_ip1, self.virtio_mac1), "#", 10
        )

    def config_vm_combined(self, combined=1):
        """
        set virtio device combined
        """
        vm1_intf = self.vm_dut[0].ports_info[0]["intf"]
        vm2_intf = self.vm_dut[1].ports_info[0]["intf"]
        self.vm_dut[0].send_expect(
            "ethtool -L %s combined %d" % (vm1_intf, combined), "#", 10
        )
        self.vm_dut[1].send_expect(
            "ethtool -L %s combined %d" % (vm2_intf, combined), "#", 10
        )

    def start_iperf(self):
        """
        run perf command between to vms
        """
        iperf_server = "iperf -s -i 1"
        iperf_client = "iperf -c {} -i 1 -t 60".format(self.virtio_ip1)
        self.vm_dut[0].send_expect(
            "{} > iperf_server.log &".format(iperf_server), "", 10
        )
        self.vm_dut[1].send_expect(
            "{} > iperf_client.log &".format(iperf_client), "", 60
        )
        time.sleep(60)

    def get_iperf_result(self):
        """
        get the iperf test result
        """
        self.table_header = ["Mode", "[M|G]bits/sec"]
        self.result_table_create(self.table_header)
        self.vm_dut[0].send_expect("pkill iperf", "# ")
        self.vm_dut[1].session.copy_file_from("%s/iperf_client.log" % self.dut.base_dir)
        fp = open("./iperf_client.log")
        fmsg = fp.read()
        fp.close()
        # remove the server report info from msg
        index = fmsg.find("Server Report")
        if index != -1:
            fmsg = fmsg[:index]
        iperfdata = re.compile("\S*\s*[M|G]bits/sec").findall(fmsg)
        # the last data of iperf is the ave data from 0-30 sec
        self.verify(len(iperfdata) != 0, "The iperf data between to vms is 0")
        self.logger.info("The iperf data between vms is %s" % iperfdata[-1])

        # put the result to table
        results_row = ["vm2vm", iperfdata[-1]]
        self.result_table_add(results_row)

        # print iperf resut
        self.result_table_print()
        # rm the iperf log file in vm
        self.vm_dut[0].send_expect("rm iperf_server.log", "#", 10)
        self.vm_dut[1].send_expect("rm iperf_client.log", "#", 10)

    def verify_xstats_info_on_vhost(self):
        """
        check both 2VMs can receive and send big packets to each other
        """
        self.vhost_user_pmd.execute_cmd("show port stats all")
        out_tx = self.vhost_user_pmd.execute_cmd("show port xstats 0")
        out_rx = self.vhost_user_pmd.execute_cmd("show port xstats 1")

        tx_info = re.search("tx_size_1523_to_max_packets:\s*(\d*)", out_tx)
        rx_info = re.search("rx_size_1523_to_max_packets:\s*(\d*)", out_rx)

        self.verify(
            int(rx_info.group(1)) > 0, "Port 1 not receive packet greater than 1522"
        )
        self.verify(
            int(tx_info.group(1)) > 0, "Port 0 not forward packet greater than 1522"
        )

    def mount_tmpfs_for_4k(self, number=1):
        """
        Prepare tmpfs with 4K-pages
        """
        for num in range(number):
            self.dut.send_expect("mkdir /mnt/tmpfs_nohuge{}".format(num), "# ")
            self.dut.send_expect(
                "mount tmpfs /mnt/tmpfs_nohuge{} -t tmpfs -o size=4G".format(num), "# "
            )

    def umount_tmpfs_for_4k(self):
        """
        Prepare tmpfs with 4K-pages
        """
        out = self.dut.send_expect(
            "mount |grep 'mnt/tmpfs' |awk -F ' ' {'print $3'}", "#"
        )
        mount_infos = out.replace("\r", "").split("\n")
        if len(mount_infos) != 0:
            for mount_info in mount_infos:
                self.dut.send_expect("umount {}".format(mount_info), "# ")

    def umount_huge_pages(self):
        self.dut.send_expect("mount |grep '/mnt/huge' |awk -F ' ' {'print $3'}", "#")
        self.dut.send_expect("umount /mnt/huge", "# ")

    def mount_huge_pages(self):
        self.dut.send_expect("mkdir -p /mnt/huge", "# ")
        self.dut.send_expect("mount -t hugetlbfs nodev /mnt/huge", "# ")

    def test_perf_pvp_virtio_user_split_ring_with_4K_pages_and_cbdma_enable(self):
        """
        Test Case 1: Basic test vhost/virtio-user split ring with 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        lcore_dma = f"lcore{self.vhost_core_list[1]}@{self.cbdma_list[0]}"
        vhost_eal_param = "--no-huge -m 1024 --vdev 'net_vhost0,iface=./vhost-net,queues=1,dmas=[txq0]'"
        vhost_param = " --no-numa --socket-num={} --lcore-dma=[{}]".format(
            self.ports_socket, lcore_dma
        )
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.cbdma_list:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list[0:2],
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.mount_tmpfs_for_4k(number=1)
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,queues=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_and_verify()
        self.result_table_print()

    def test_perf_pvp_virtio_user_packed_ring_with_4K_pages_and_cbdma_enable(self):
        """
        Test Case 2: Basic test vhost/virtio-user packed ring with 4K-pages and cbdma enable
        """
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)
        lcore_dma = f"lcore{self.vhost_core_list[1]}@{self.cbdma_list[0]}"
        vhost_eal_param = "--no-huge -m 1024 --vdev 'net_vhost0,iface=./vhost-net,queues=1,dmas=[txq0]'"
        vhost_param = " --no-numa --socket-num={} --lcore-dma=[{}]".format(
            self.ports_socket, lcore_dma
        )
        ports = [self.dut.ports_info[0]["pci"]]
        for i in self.cbdma_list:
            ports.append(i)
        self.start_vhost_user_testpmd(
            cores=self.vhost_core_list[0:2],
            eal_param=vhost_eal_param,
            param=vhost_param,
            ports=ports,
        )
        self.vhost_user_pmd.execute_cmd("start")
        self.mount_tmpfs_for_4k(number=1)
        virtio_eal_param = "--no-huge -m 1024 --vdev net_virtio_user0,mac=00:11:22:33:44:10,path=./vhost-net,packed_vq=1,queues=1"
        self.start_virtio_user0_testpmd(
            cores=self.virtio0_core_list, eal_param=virtio_eal_param
        )
        self.virtio_user0_pmd.execute_cmd("set fwd mac")
        self.virtio_user0_pmd.execute_cmd("start")
        self.send_and_verify()
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.virtio_user0_pmd.quit()
        self.vhost_user_pmd.quit()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "# ")
        self.bind_cbdma_device_to_kernel()
        self.umount_tmpfs_for_4k()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user0)
