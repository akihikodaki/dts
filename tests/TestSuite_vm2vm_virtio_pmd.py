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
Test cases fro vhost/virtio-pmd(1.1) VM2VM test with mergeable path.
About mergeable path check the large packet payload.
"""
import re
import time
import utils
from virt_common import VM
from test_case import TestCase
from packet import Packet


class TestVM2VMVirtioPMD(TestCase):
    def set_up_all(self):
        self.memory_channel = self.dut.get_memory_channels()
        self.vm_num = 2
        self.dump_pcap = "/root/pdump-rx.pcap"
        socket_num = len(set([int(core['socket']) for core in self.dut.cores]))
        self.socket_mem = ','.join(['1024']*socket_num)
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.vhost_user = self.dut.new_session(suite="vhost")
        self.enable_pcap_lib_in_dpdk(self.dut)
        self.virtio_user0 = None
        self.virtio_user1 = None
        self.flag_compiled = False
        self.backup_speed = self.dut.skip_setup
        self.pci_info = self.dut.ports_info[0]['pci']

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
        self.vm_dut = []
        self.vm = []

    def get_core_list(self, cores_num):
        """
        create core mask
        """
        self.core_config = "1S/%dC/1T" % cores_num
        self.cores_list = self.dut.get_core_list(self.core_config)
        self.verify(len(self.cores_list) >= cores_num,
                    "There has not enough cores to test this case %s" %
                    self.running_case)

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
        vhost_mask = self.cores_list[0:2]
        testcmd = self.dut.target + "/app/testpmd "
        vdev1 = "--vdev 'net_vhost0,iface=%s/vhost-net0,queues=1' " % self.base_dir
        vdev2 = "--vdev 'net_vhost1,iface=%s/vhost-net1,queues=1' " % self.base_dir
        eal_params = self.dut.create_eal_parameters(cores=vhost_mask, no_pci=True, prefix='vhost', ports=[self.pci_info])
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
        self.command_line = testcmd + eal_params + vdev1 + vdev2 + para
        self.vhost_user.send_expect(self.command_line, "testpmd> ", 30)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost_user.send_expect("start", "testpmd> ", 30)

    def start_virtio_testpmd_with_vhost_net1(self, path_mode, extern_param):
        """
        launch the testpmd as virtio with vhost_net1
        """
        self.virtio_user1 = self.dut.new_session(suite="virtio_user1")
        virtio_mask = self.cores_list[2:4]
        testcmd = self.dut.target + "/app/testpmd "
        vdev = "--vdev=net_virtio_user1,mac=00:01:02:03:04:05,path=./vhost-net1,queues=1,%s " % path_mode
        eal_params = self.dut.create_eal_parameters(cores=virtio_mask, no_pci=True, prefix='virtio', ports=[self.pci_info])
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024 %s" % extern_param
        command_line = testcmd + eal_params + vdev + para
        self.virtio_user1.send_expect(command_line, 'testpmd> ', 30)
        self.virtio_user1.send_expect('set fwd rxonly', 'testpmd> ', 30)
        self.virtio_user1.send_expect('start', 'testpmd> ', 30)

    def start_virtio_testpmd_with_vhost_net0(self, path_mode, extern_param):
        """
        launch the testpmd as virtio with vhost_net0
        """
        self.virtio_user0 = self.dut.new_session(suite="virtio_user0")
        virtio_mask = self.cores_list[4:6]
        testcmd = self.dut.target + "/app/testpmd "
        vdev = "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net0,queues=1,%s " % path_mode
        eal_params = self.dut.create_eal_parameters(cores=virtio_mask, no_pci=True, prefix='virtio0', ports=[self.pci_info])
        para = " -- -i --nb-cores=1 --txd=1024 --rxd=1024 %s" % extern_param
        command_line = testcmd + eal_params + vdev + para
        self.virtio_user0.send_expect(command_line, 'testpmd> ', 30)
        self.virtio_user0.send_expect('set txpkts 2000,2000,2000,2000', 'testpmd> ', 30)
        self.virtio_user0.send_expect('set burst 1', 'testpmd> ', 30)
        self.virtio_user0.send_expect('start tx_first 10', 'testpmd> ', 30)

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

    def launch_pdump_to_capture_pkt(self, client_dut, dump_port):
        """
        bootup pdump in VM
        """
        self.pdump_session = client_dut.new_session(suite="pdump")
        if hasattr(client_dut, "vm_name"):
            command_line = self.target + "/app/dpdk-pdump " + \
                    "-v --file-prefix=virtio -- " + \
                    "--pdump  '%s,queue=*,rx-dev=%s,mbuf-size=8000'"
            self.pdump_session.send_expect(command_line % (dump_port, self.dump_pcap), 'Port')
        else:
            command_line = self.target + "/app/dpdk-pdump " + \
                    "-v --file-prefix=virtio_%s -- " + \
                    "--pdump  '%s,queue=*,rx-dev=%s,mbuf-size=8000'"
            self.pdump_session.send_expect(command_line % (self.dut.prefix_subfix, dump_port, self.dump_pcap), 'Port')

    def start_vms(self, mode=0, mergeable=True):
        """
        start two VM, each VM has one virtio device
        """
        # for virtio 0.95, start vm with "disable-modern=true"
        # for virito 1.0, start vm with "disable-modern=false"
        if self.flag_compiled:
            self.dut.skip_setup = True
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
                print((utils.RED("Failure for %s" % str(e))))
                raise e

            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)
        self.flag_compiled = True

    def calculate_avg_throughput(self):
        results = 0.0
        for i in range(10):
            out = self.vhost_user.send_expect("show port stats 1", "testpmd> ", 60)
            time.sleep(5)
            lines = re.search("Rx-pps:\s*(\d*)", out)
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

    def check_packet_payload_valid(self, client_dut):
        """
        check the payload is valid
        """
        # stop pdump
        self.pdump_session.send_expect('^c', '# ', 60)
        # quit testpmd
        client_dut.send_expect('quit', '#', 60)
        time.sleep(2)
        client_dut.session.copy_file_from(src="%s" % self.dump_pcap, dst="%s" % self.dump_pcap)
        pkt = Packet()
        pkts = pkt.read_pcapfile(self.dump_pcap)
        self.verify(len(pkts) == 10, "The vm0 do not capture all the packets")
        data = str(pkts[0]['Raw'])
        for i in range(1, 10):
            value = str(pkts[i]['Raw'])
            self.verify(data == value, "the payload in receive packets has been changed")

    def stop_all_apps(self):
        for i in range(len(self.vm)):
            self.vm_dut[i].send_expect("quit", "#", 20)
            self.vm[i].stop()
        self.vhost_user.send_expect("quit", "#", 30)
        if self.virtio_user1:
            self.virtio_user1.send_expect('quit', '# ', 30)
            self.dut.close_session(self.virtio_user1)
            self.virtio_user1 = None
        if self.virtio_user0:
            self.virtio_user0.send_expect('quit', '# ', 30)
            self.dut.close_session(self.virtio_user0)
            self.virtio_user0 = None

    def test_vhost_vm2vm_virtio_pmd_with_normal_path(self):
        """
        vhost-user + virtio-pmd with normal path
        """
        path_mode = "normal"
        self.get_core_list(2)
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95 normal path", path=path_mode)

    def test_vhost_vm2vm_virito_10_pmd_with_normal_path(self):
        """
        vhost-user + virtio1.0-pmd with normal path
        """
        path_mode = "normal"
        self.get_core_list(2)
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0 normal path", path=path_mode)

    def test_vhost_vm2vm_virtio_pmd_with_vector_rx_path(self):
        """
        vhost-user + virtio-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        self.get_core_list(2)
        self.start_vhost_testpmd()
        self.start_vms(mode=0, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 0.95 vector_rx", path=path_mode)

    def test_vhost_vm2vm_virtioi10_pmd_with_vector_rx_path(self):
        """
        vhost-user + virtio1.0-pmd with vector_rx path
        """
        path_mode = "vector_rx"
        self.get_core_list(2)
        self.start_vhost_testpmd()
        self.start_vms(mode=1, mergeable=False)
        self.start_vm_testpmd(self.vm_dut[0], path_mode)
        self.start_vm_testpmd(self.vm_dut[1], path_mode)
        self.send_and_verify(mode="virtio 1.0 vector_rx", path=path_mode)

    def test_vhost_vm2vm_virito_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio-pmd with mergeable path test with payload check
        """
        path_mode = "mergeable"
        extern_param = '--max-pkt-len=9600'
        dump_port = 'port=0'
        self.get_core_list(2)
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
        self.launch_pdump_to_capture_pkt(self.vm_dut[0], dump_port)
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect('set txpkts 2000,2000,2000,2000', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('set burst 1', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('start tx_first 10', 'testpmd> ', 30)
         # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])
        # reset the evn in vm
        self.disable_pcap_lib_in_dpdk(self.vm_dut[0])

    def test_vhost_vm2vm_virito_10_pmd_with_mergeable_path(self):
        """
        vhost-user + virtio1.0-pmd with mergeable path test with payload check
        """
        path_mode = "mergeable"
        extern_param = '--max-pkt-len=9600'
        dump_port = 'port=0'
        self.get_core_list(2)
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
        self.launch_pdump_to_capture_pkt(self.vm_dut[0], dump_port)
        # start testpmd in VM1 and start to send packet
        self.start_vm_testpmd(self.vm_dut[1], path_mode, extern_param)
        self.vm_dut[1].send_expect('set txpkts 2000,2000,2000,2000', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('set burst 1', 'testpmd> ', 30)
        self.vm_dut[1].send_expect('start tx_first 10', 'testpmd> ', 30)
         # check the packet in vm0
        self.check_packet_payload_valid(self.vm_dut[0])
        # reset the evn in vm
        self.disable_pcap_lib_in_dpdk(self.vm_dut[0])

    def test_vhost_vm2vm_virtio_11_pmd_with_mergeable_path(self):
        """
        vm2vm vhost-user/virtio1.1-pmd mergeable path test with payload check
        """
        mode_info = 'packed_vq=1,mrg_rxbuf=1,in_order=0'
        extern_param = '--max-pkt-len=9600'
        dump_port = 'device_id=net_virtio_user1'
        self.get_core_list(6)
        self.start_vhost_testpmd()
        self.start_virtio_testpmd_with_vhost_net1(mode_info, extern_param)
        self.launch_pdump_to_capture_pkt(self.dut, dump_port)
        self.start_virtio_testpmd_with_vhost_net0(mode_info, extern_param)
        self.check_packet_payload_valid(self.dut)

    def tear_down(self):
        #
        # Run after each test case.
        #
        self.stop_all_apps()
        self.dut.kill_all()
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.disable_pcap_lib_in_dpdk(self.dut)
        self.dut.close_session(self.vhost_user)
        self.dut.skip_setup = self.backup_speed
