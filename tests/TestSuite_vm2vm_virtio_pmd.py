# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation.
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

Test cases for Vhost-user/Virtio-pmd VM2VM
"""
import re
import time
import utils
from virt_common import VM
from test_case import TestCase


class TestVM2VMVirtioPMD(TestCase):
    def set_up_all(self):
        self.core_config = "1S/4C/1T"
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                            == 0])
        self.verify(self.cores_num >= 4,
                    "There has not enough cores to test this suite %s" %
                    self.suite_name)
        self.cores = self.dut.get_core_list(self.core_config)
        self.coremask = utils.create_mask(self.cores)
        self.memory_channel = self.dut.get_memory_channels()
        self.vm_num = 2

    def set_up(self):
        """
        run before each test case.
        """
        self.table_header = ["FrameSize(B)", "Mode",
                            "Throughput(Mpps)", "Path"]
        self.result_table_create(self.table_header)
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.vhost = self.dut.new_session(suite="vhost")
        self.vm_dut = []
        self.vm = []

    def start_vhost_testpmd(self):
        """
        launch the testpmd on vhost side
        """
        self.command_line = self.dut.target + "/app/testpmd -c %s -n %d " + \
            "--socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost " + \
            "--vdev 'net_vhost0,iface=vhost-net0,queues=1' " + \
            "--vdev 'net_vhost1,iface=vhost-net1,queues=1' " + \
            "-- -i --nb-cores=1 --txd=1024 --rxd=1024"

        self.command_line = self.command_line % (
                            self.coremask, self.memory_channel)
        self.vhost.send_expect(self.command_line, "testpmd> ", 30)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def start_vm_testpmd(self, vm_client, path_mode):
        """
        launch the testpmd in vm
        """
        if path_mode == "mergeable":
            command = self.dut.target + "/app/testpmd " + \
                        "-c 0x3 -n 4 -- -i --tx-offloads=0x00 " + \
                        "--enable-hw-vlan-strip --txd=1024 --rxd=1024"
        elif path_mode == "normal":
            command = self.dut.target + "/app/testpmd " + \
                        "-c 0x3 -n 4 -- -i --tx-offloads=0x00 " + \
                        "--enable-hw-vlan-strip --txd=1024 --rxd=1024"
        elif path_mode == "vector_rx":
            command = self.dut.target + "/app/testpmd " + \
                        "-c 0x3 -n 4 -- -i --txd=1024 --rxd=1024"
        vm_client.send_expect(command, "testpmd> ", 20)

    def start_vms(self, mode=0, mergeable=True):
        """
        start two VM, each VM has one virtio device
        """
        # for virtio 0.95, start vm with "disable-modern=true"
        # for virito 1.0, start vm with "disable-modern=false"
        if mode == 0:
            setting_args = "disable-modern=true"
        else:
            setting_args = "disable-modern=false"
        if mergeable is True:
            setting_args += "," + "mrg_rxbuf=on"
        else:
            setting_args += "," + "mrg_rxbuf=off"
        setting_args += ",csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on,guest_ecn=on"

        for i in range(self.vm_num):
            vm_dut = None
            vm_info = VM(self.dut, 'vm%d' % i, 'vhost_sample')
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = './vhost-net%d' % i
            vm_params['opt_mac'] = "52:54:00:00:00:0%d" % (i+1)
            vm_params['opt_settings'] = setting_args
            vm_info.set_vm_device(**vm_params)
            time.sleep(3)
            try:
                vm_dut = vm_info.start()
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                print utils.RED("Failure for %s" % str(e))

            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def calculate_avg_throughput(self):
        results = 0.0
        for i in range(10):
            out = self.vhost.send_expect("show port stats 0", "testpmd> ", 60)
            time.sleep(5)
            lines = re.search("Tx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 0, "%s can not receive packets" % self.running_case)
        return Mpps

    def update_table_info(self, case_info, frame_size, Mpps, path):
        results_row = [frame_size]
        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(path)
        self.result_table_add(results_row)

    def send_and_verify(self, mode, path):
        """
        start to send packets and verify it
        """
        # start to send packets
        self.vm_dut[0].send_expect("set fwd rxonly", "testpmd> ", 10)
        self.vm_dut[0].send_expect("start", "testpmd> ", 10)
        self.vm_dut[1].send_expect("set fwd txonly", "testpmd> ", 10)
        self.vm_dut[1].send_expect("set txpkts 64", "testpmd> ", 10)
        self.vm_dut[1].send_expect("start tx_first 32", "testpmd> ", 10)
        Mpps = self.calculate_avg_throughput()
        self.update_table_info(mode, 64, Mpps, path)
        self.result_table_print()

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm_dut[i].send_expect("quit", "#", 20)
            self.vm[i].stop()
        self.vhost.send_expect("quit", "#", 30)

    def test_vhost_vm2vm_virito_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio-pmd with mergeable path
        """
        path_mode = "mergeable"
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=True)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virtio_pmd_with_normal_path(self):
        """
        vhost-user + virtio-pmd with normal path
        """
        path_mode = "normal"
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virtio_pmd_with_vector_rx_path(self):
        """
        vhost-user + virtio-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virito_10_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio1.0-pmd with mergeable path
        """
        path_mode = "mergeable"
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=True)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0", path=path_mode)
        self.stop_all_apps()

    def tear_down(self):
        #
        # Run after each test case.
        #
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
