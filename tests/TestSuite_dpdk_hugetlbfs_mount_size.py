# .. Copyright (c) <2019>, Intel Corporation
#   All rights reserved.
#   Redistribution and use in source and binary forms, with or without
#   modification, are permitted provided that the following conditions
#   are met:

#   - Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.

#   - Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#    distribution.

#   - Neither the name of Intel Corporation nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.

#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#   COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#   STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#   ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
#   OF THE POSSIBILITY OF SUCH DAMAGE.

"""
This feature is to limit DPDK to use the exact size which is the mounted hugepage size.
"""

import re
import time

import framework.utils as utils
from framework.test_case import TestCase

DEFAULT_MNT = "/mnt/huge"
MNT_PATH = ["/mnt/huge1", "/mnt/huge2", "/mnt/huge3"]
vhost_name = ["vhost1", "vhost2", "vhost3"]


class DpdkHugetlbfsMountSize(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.packet_num = 100
        self.mem_channels = self.dut.get_memory_channels()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/6C/1T", socket=self.ports_socket)
        self.verify(len(cores) >= 6, "Insufficient cores for speed testing")
        self.core_list1 = ",".join(str(i) for i in cores[0:2])
        self.core_list2 = ",".join(str(i) for i in cores[2:4])
        self.core_list3 = ",".join(str(i) for i in cores[4:6])
        self.pci_info_0 = self.dut.ports_info[0]["pci"]
        self.pci_info_1 = self.dut.ports_info[1]["pci"]
        self.numa_id = self.dut.get_numa_id(self.dut_ports[0])
        self.create_folder([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])
        if self.numa_id == 0:
            self.socket_mem = "1024,0"
            self.socket_mem2 = "2048,0"
        else:
            self.socket_mem = "0,1024"
            self.socket_mem2 = "0,2048"
        self.umount_huge([DEFAULT_MNT])
        self.app_path = self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def close_session(self):
        self.dut.close_session(self.session_first)
        self.dut.close_session(self.session_secondary)

    def send_pkg(self, port_id):
        tx_interface = self.tester.get_interface(
            self.tester.get_local_port(self.dut_ports[port_id])
        )
        mac = self.dut.get_mac_address(self.dut_ports[port_id])
        cmd = 'sendp([Ether(dst="%s")/IP()/("X"*64)], iface="%s", count=%d)'
        excute_cmd = cmd % (mac, tx_interface, self.packet_num)
        self.tester.scapy_append(excute_cmd)
        self.tester.scapy_execute()

    def verify_result(self, session):
        out = session.send_expect("show port stats all", "testpmd> ", 120)
        self.result_first = re.findall(r"RX-packets: (\w+)", out)
        self.result_secondary = re.findall(r"TX-packets: (\w+)", out)
        self.verify(
            int(self.result_first[0]) == self.packet_num
            and int(self.result_secondary[0]) == self.packet_num,
            "forward packets no correctly",
        )

    def create_folder(self, huges=[]):
        for huge in huges:
            cmd = "mkdir -p %s" % huge
            self.dut.send_expect(cmd, "#", 15)

    def del_folder(self, huges=[]):
        for huge in huges:
            cmd = "rm -rf %s" % huge
            self.dut.send_expect(cmd, "#", 15)

    def umount_huge(self, huges=[]):
        for huge in huges:
            cmd = "umount %s" % huge
            self.dut.send_expect(cmd, "#", 15)

    def test_default_hugepage_size(self):
        # Bind one nic port to igb_uio driver, launch testpmd
        self.dut.send_expect("mount -t hugetlbfs hugetlbfs %s" % MNT_PATH[0], "#", 15)
        self.logger.info("test default hugepage size start testpmd without numa")
        ttd = "%s -l %s -n %d --huge-dir %s --file-prefix=%s -a %s -- -i"
        launch_ttd = ttd % (
            self.app_path,
            self.core_list1,
            self.mem_channels,
            MNT_PATH[0],
            vhost_name[0],
            self.pci_info_0,
        )
        self.dut.send_expect(launch_ttd, "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_pkg(0)
        self.verify_result(self.dut)
        self.dut.send_expect("quit", "#", 15)

        # resart testpmd with numa support
        self.logger.info("test default hugepage size start testpmd with numa")
        ttd_secondary = (
            "%s -l %s -n %d --huge-dir %s --file-prefix=%s -a %s -- -i --numa"
        )
        launch_ttd_secondary = ttd_secondary % (
            self.app_path,
            self.core_list1,
            self.mem_channels,
            MNT_PATH[0],
            vhost_name[0],
            self.pci_info_0,
        )
        self.dut.send_expect(launch_ttd_secondary, "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_pkg(0)
        self.verify_result(self.dut)
        self.dut.send_expect("quit", "#", 15)
        self.umount_huge([MNT_PATH[0]])

    def test_mount_size_exactly_match_hugepage_size_two_mount_points(self):
        # Bind two nic ports to igb_uio driver, launch testpmd with numactl
        self.session_first = self.dut.new_session(suite="session_first")
        self.session_secondary = self.dut.new_session(suite="session_secondary")
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=4G hugetlbfs %s" % MNT_PATH[0], "#", 15
        )
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=4G hugetlbfs %s" % MNT_PATH[1], "#", 15
        )

        self.logger.info("start first testpmd")
        ttd = (
            "numactl --membind=%d %s -l %s -n %d --legacy-mem --socket-mem %s"
            " --huge-dir %s --file-prefix=%s -a %s -- -i --socket-num=%d --no-numa"
        )
        launch_ttd = ttd % (
            self.numa_id,
            self.app_path,
            self.core_list1,
            self.mem_channels,
            self.socket_mem2,
            MNT_PATH[0],
            vhost_name[0],
            self.pci_info_0,
            self.numa_id,
        )
        self.session_first.send_expect(launch_ttd, "testpmd> ", 120)
        self.session_first.send_expect("set promisc all off", "testpmd> ", 120)
        self.session_first.send_expect("start", "testpmd> ", 120)
        self.session_first.send_expect("clear port stats all", "testpmd> ", 120)

        self.logger.info("start secondary testpmd")
        ttd_secondary = (
            "numactl --membind=%d %s -l %s -n %d --legacy-mem --socket-mem %s"
            " --huge-dir %s --file-prefix=%s -a %s -- -i --socket-num=%d --no-numa"
        )
        launch_ttd_secondary = ttd_secondary % (
            self.numa_id,
            self.app_path,
            self.core_list2,
            self.mem_channels,
            self.socket_mem2,
            MNT_PATH[1],
            vhost_name[1],
            self.pci_info_1,
            self.numa_id,
        )
        self.session_secondary.send_expect(launch_ttd_secondary, "testpmd> ", 120)
        self.session_secondary.send_expect("set promisc all off", "testpmd> ", 120)
        self.session_secondary.send_expect("start", "testpmd> ", 120)
        self.session_secondary.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_pkg(0)
        self.send_pkg(1)
        self.verify_result(self.session_first)
        self.verify_result(self.session_secondary)
        self.session_first.send_expect("quit", "#", 15)
        self.session_secondary.send_expect("quit", "#", 15)
        self.close_session()
        self.umount_huge([MNT_PATH[0], MNT_PATH[1]])

    def test_mount_size_greater_than_hugepage_size_single_mount_point(self):
        # Bind one nic port to igb_uio driver
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=9G hugetlbfs %s" % MNT_PATH[0], "#", 15
        )
        ttd = "%s -l %s -n %d --legacy-mem --huge-dir %s --file-prefix=%s -a %s -- -i"
        launch_ttd = ttd % (
            self.app_path,
            self.core_list1,
            self.mem_channels,
            MNT_PATH[0],
            vhost_name[0],
            self.pci_info_0,
        )
        self.dut.send_expect(launch_ttd, "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_pkg(0)
        self.verify_result(self.dut)
        self.dut.send_expect("quit", "#", 15)
        self.umount_huge([MNT_PATH[0]])

    def test_mount_size_greater_than_hugepage_size_multiple_mount_points(self):
        # Bind one nic port to igb_uio driver, launch testpmd
        self.session_first = self.dut.new_session(suite="session_first")
        self.session_secondary = self.dut.new_session(suite="session_secondary")
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=4G hugetlbfs %s" % MNT_PATH[0], "#", 15
        )
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=4G hugetlbfs %s" % MNT_PATH[1], "#", 15
        )
        self.dut.send_expect(
            "mount -t hugetlbfs -o size=1G hugetlbfs %s" % MNT_PATH[2], "#", 15
        )
        # launch first testpmd
        self.logger.info("launch first testpmd")
        ttd = (
            "numactl --membind=%d %s -l %s -n %d  --legacy-mem --socket-mem %s --huge-dir %s"
            "  --file-prefix=%s -a %s -- -i --socket-num=%d --no-numa"
        )
        launch_ttd = ttd % (
            self.numa_id,
            self.app_path,
            self.core_list1,
            self.mem_channels,
            self.socket_mem2,
            MNT_PATH[0],
            vhost_name[0],
            self.pci_info_0,
            self.numa_id,
        )
        self.session_first.send_expect(launch_ttd, "testpmd> ", 120)
        self.session_first.send_expect("set promisc all off", "testpmd> ", 120)
        self.session_first.send_expect("start", "testpmd> ", 120)
        self.session_first.send_expect("start", "testpmd> ", 120)

        # launch secondary testpmd
        self.logger.info("launch secondary testpmd")
        ttd_secondary = (
            "numactl --membind=%d %s -l %s -n %d  --legacy-mem --socket-mem %s --huge-dir"
            " %s --file-prefix=%s -a %s -- -i --socket-num=%d --no-numa"
        )
        launch_ttd_secondary = ttd_secondary % (
            self.numa_id,
            self.app_path,
            self.core_list2,
            self.mem_channels,
            self.socket_mem2,
            MNT_PATH[1],
            vhost_name[1],
            self.pci_info_1,
            self.numa_id,
        )
        self.session_secondary.send_expect(launch_ttd_secondary, "testpmd> ", 120)
        self.session_secondary.send_expect("set promisc all off", "testpmd> ", 120)
        self.session_secondary.send_expect("start", "testpmd> ", 120)
        self.session_secondary.send_expect("start", "testpmd> ", 120)

        # launch third testpmd
        self.logger.info("launch third testpmd")
        ttd_third = (
            "numactl --membind=%d %s -l %s -n %d  --legacy-mem --socket-mem %s --huge-dir"
            " %s --file-prefix=%s -a %s -- -i --socket-num=%d --no-numa"
        )
        launch_ttd_third = ttd_third % (
            self.numa_id,
            self.app_path,
            self.core_list3,
            self.mem_channels,
            self.socket_mem,
            MNT_PATH[2],
            vhost_name[2],
            self.pci_info_0,
            self.numa_id,
        )
        expect_str = "Not enough memory available on socket"
        self.dut.get_session_output(timeout=2)
        try:
            self.dut.send_expect(launch_ttd_third, expect_str, 120)
        except Exception as e:
            print(e)
            self.dut.send_expect("quit", "#", 15)
            self.session_first.send_expect("quit", "#", 15)
            self.session_secondary.send_expect("quit", "#", 15)
            self.umount_huge([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])
            self.verify(0, "the expect str: %s ,not in output info" % expect_str)
        self.logger.info("the third testpmd start failed as expect : %s" % expect_str)
        result = self.dut.get_session_output(timeout=2)
        print(result)

        # start send packet and verify the session can receive the packet.
        self.send_pkg(0)
        self.verify_result(self.session_first)
        self.send_pkg(1)
        self.verify_result(self.session_secondary)
        self.session_first.send_expect("quit", "#", 15)
        self.session_secondary.send_expect("quit", "#", 15)
        self.close_session()
        self.umount_huge([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])

    def test_run_dpdk_app_limited_hugepages_controlled_by_cgroup(self):
        # Bind one nic port to igb_uio driver, launch testpmd in limited hugepages
        self.dut.send_expect("mount -t hugetlbfs nodev %s" % MNT_PATH[0], "#", 15)
        self.dut.send_expect("cgcreate -g hugetlb:/test-subgroup", "# ", 15)
        self.dut.send_expect(
            "cgset -r hugetlb.1GB.limit_in_bytes=2147483648 test-subgroup", "#", 15
        )
        ttd = "cgexec -g hugetlb:test-subgroup numactl -m %d %s -l %s -n %d -a %s -- -i --socket-num=%d --no-numa"
        launch_ttd = ttd % (
            self.numa_id,
            self.app_path,
            self.core_list1,
            self.mem_channels,
            self.pci_info_0,
            self.numa_id,
        )
        self.dut.send_expect(launch_ttd, "testpmd> ", 120)
        self.dut.send_expect("set promisc all off", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        self.dut.send_expect("clear port stats all", "testpmd> ", 120)
        self.send_pkg(0)
        self.verify_result(self.dut)
        self.dut.send_expect("quit", "#", 15)
        self.umount_huge([MNT_PATH[0]])

    def tear_down(self):
        """
        Run after each test case.
        """
        # If case fails, the mount should be cancelled to avoid affecting next cases
        self.umount_huge([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.umount_huge([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])
        self.del_folder([MNT_PATH[0], MNT_PATH[1], MNT_PATH[2]])
        self.dut.send_expect("mount -t hugetlbfs nodev %s" % DEFAULT_MNT, "#", 15)
