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
Test cases for vhost/virtio-pmd(0.95/1.0) VM2VM test with 3 rx/tx paths,
includes mergeable, normal, vector_rx.
About mergeable path check the large packet payload.
"""
import re
import time
import utils
from virt_common import VM
from test_case import TestCase
from packet import load_pcapfile


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
        self.dump_pcap = "/root/pdump-rx.pcap"
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        """
        run before each test case.
        """
        self.table_header = ["FrameSize(B)", "Mode",
                            "Throughput(Mpps)", "Queue Number", "Path"]
        self.result_table_create(self.table_header)
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vhost = self.dut.new_session(suite="vhost")
        self.vm_dut = []
        self.vm = []

    def enable_pcap_lib_in_dpdk(self, client_dut):
        """
        enable pcap lib in dpdk code and recompile
        """
        client_dut.send_expect("sed -i 's/CONFIG_RTE_LIBRTE_PMD_PCAP=n$/CONFIG_RTE_LIBRTE_PMD_PCAP=y/' config/common_base", "#")
        client_dut.build_install_dpdk(self.target)

    def disable_pcap_lib_in_dpdk(self, client_dut):
        """
        reset pcap lib in dpdk and recompile
        """
        client_dut.send_expect("sed -i 's/CONFIG_RTE_LIBRTE_PMD_PCAP=y$/CONFIG_RTE_LIBRTE_PMD_PCAP=n/' config/common_base", "#")
        client_dut.build_install_dpdk(self.target)

    def start_vhost_testpmd(self):
        """
        launch the testpmd on vhost side
        """
        self.command_line = self.dut.target + "/app/testpmd -c %s -n %d " + \
            "--socket-mem 2048,2048 --legacy-mem --no-pci --file-prefix=vhost " + \
            "--vdev 'net_vhost0,iface=%s/vhost-net0,queues=1' " + \
            "--vdev 'net_vhost1,iface=%s/vhost-net1,queues=1' " + \
            "-- -i --nb-cores=1 --txd=1024 --rxd=1024"

        self.command_line = self.command_line % (
                            self.coremask, self.memory_channel, self.base_dir, self.base_dir)
        self.vhost.send_expect(self.command_line, "testpmd> ", 30)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def start_vm_testpmd(self, vm_client, path_mode, extern_param=""):
        """
        launch the testpmd in vm
        """
        if path_mode == "mergeable":
            command = self.dut.target + "/app/testpmd -c 0x3 -n 4 " + \
                        "--file-prefix=virtio -- -i --tx-offloads=0x00 " + \
                        "--enable-hw-vlan-strip --txd=1024 --rxd=1024 %s"
        elif path_mode == "normal":
            command = self.dut.target + "/app/testpmd -c 0x3 -n 4 " + \
                        "--file-prefix=virtio -- -i --tx-offloads=0x00 " + \
                        "--enable-hw-vlan-strip --txd=1024 --rxd=1024 %s"
        elif path_mode == "vector_rx":
            command = self.dut.target + "/app/testpmd -c 0x3 -n 4 " + \
                        "--file-prefix=virtio -- -i --txd=1024 --rxd=1024 %s"
        vm_client.send_expect(command % extern_param, "testpmd> ", 20)

    def launch_pdump_in_vm(self, vm_client):
        """
        bootup pdump in VM
        """
        self.vm_dump = vm_client.new_session(suite="pdump")
        command_line = self.target + "/app/dpdk-pdump " + \
                    "-v --file-prefix=virtio -- " + \
                    "--pdump  'port=0,queue=*,rx-dev=%s,mbuf-size=8000'"
        self.vm_dump.send_expect(command_line % self.dump_pcap, 'Port')

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
            vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i
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
        results_row.append(1)
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

    def check_packet_payload_valid(self, vm_dut):
        """
        check the payload is valid
        """
        # stop pdump
        self.vm_dump.send_expect('^c', '# ', 60)
        # quit testpmd
        vm_dut.send_expect('quit', '#', 60)
        time.sleep(2)
        vm_dut.session.copy_file_from(src="%s" % self.dump_pcap, dst="%s" % self.dump_pcap)
        pkts = load_pcapfile(self.dump_pcap)
        self.verify(len(pkts) == 10, "The vm0 do not capture all the packets")
        data = str(pkts[0].pktgen.pkt['Raw'])
        for i in range(1, 10):
            value = str(pkts[i].pktgen.pkt['Raw'])
            self.verify(data == value, "the payload in receive packets has been changed")

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm_dut[i].send_expect("quit", "#", 20)
            self.vm[i].stop()
        self.vhost.send_expect("quit", "#", 30)

    def test_vhost_vm2vm_virtio_pmd_with_normal_path(self):
        """
        vhost-user + virtio-pmd with normal path
        """
        path_mode = "normal"
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95 normal path", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virito_10_pmd_with_normal_path(self):
        """
        vhost-user + virtio1.0-pmd with normal path
        """
        path_mode = "normal"
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0 normal path", path=path_mode)
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
        self.send_and_verify(mode="virtio 0.95 vector_rx", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virtioi10_pmd_with_vector_rx_path(self):
        """
        vhost-user + virtio1.0-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0 vector_rx", path=path_mode)
        self.stop_all_apps()

    def test_vhost_vm2vm_virito_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio-pmd with mergeable path test with payload check
        """
        path_mode = "mergeable"
        extern_param = '--max-pkt-len=9600'
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=True)
        # enable pcap in VM0
        self.enable_pcap_lib_in_dpdk(self.vm_dut[0])
        # git the vm enough huge to run pdump
        self.vm_dut[0].set_huge_pages(2048)
        # start testpmd and pdump in VM0
        self.start_vm_testpmd(self.vm_dut[0], path_mode, extern_param)
        self.vm_dut[0].send_expect('set fwd rxonly', 'testpmd> ', 30)
        self.vm_dut[0].send_expect('start', 'testpmd> ', 30)
        self.launch_pdump_in_vm(self.vm_dut[0])
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect('set txpkts 2000,2000,2000,2000', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('set burst 1', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('start tx_first 10', 'testpmd> ', 30)
         # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])
        # reset the evn in vm
        self.disable_pcap_lib_in_dpdk(self.vm_dut[0])
        self.stop_all_apps()

    def test_vhost_vm2vm_virito_10_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio1.0-pmd with mergeable path test with payload check
        """
        path_mode = "mergeable"
        extern_param = '--max-pkt-len=9600'
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=True)
        # enable pcap in VM0
        self.enable_pcap_lib_in_dpdk(self.vm_dut[0])
        # git the vm enough huge to run pdump
        self.vm_dut[0].set_huge_pages(2048)
        # start testpmd and pdump in VM0
        self.start_vm_testpmd(self.vm_dut[0], path_mode, extern_param)
        self.vm_dut[0].send_expect('set fwd rxonly', 'testpmd> ', 30)
        self.vm_dut[0].send_expect('start', 'testpmd> ', 30)
        self.launch_pdump_in_vm(self.vm_dut[0])
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect('set txpkts 2000,2000,2000,2000', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('set burst 1', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('start tx_first 10', 'testpmd> ', 30)
         # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])
        # reset the evn in vm
        self.disable_pcap_lib_in_dpdk(self.vm_dut[0])
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
