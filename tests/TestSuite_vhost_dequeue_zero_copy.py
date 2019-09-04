#
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
Test the performance of dequeue zero-copy.
There are three topology test (PVP/VM2VM/VM2NIC) for this feature.
And this testsuite implement the topology of PVP.
Testsuite vm2vm_net_perf implement the topology VM2VM
Testsuite gso implement the topology VM2NIC
"""
import utils
import time
import re
from settings import HEADER_SIZE
from virt_common import VM
from test_case import TestCase
from pktgen import PacketGeneratorHelper


class TestVhostDequeueZeroCopy(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVhostDequeueZeroCopy, self)
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.queue_number = 1
        self.nb_cores = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                          == self.ports_socket])
        self.mem_channels = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.vm_dut = None
        self.virtio1_mac = "52:54:00:00:00:01"

        self.logger.info("you can config packet_size in file %s.cfg," % self.suite_name + \
                    "in region 'suite' like packet_sizes=[64, 128, 256]")
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        # Prepare the result table
        self.table_header = ["FrameSize(B)", "Throughput(Mpps)",
                            "% linerate", "Queue number", "Cycle"]
        self.result_table_create(self.table_header)

        self.vhost = self.dut.new_session(suite="vhost-user")

    def get_core_mask(self):
        """
        check whether the server has enough cores to run case
        """
        core_config = "1S/%dC/1T" % (self.nb_cores + 1)
        self.verify(self.cores_num >= (self.nb_cores + 1),
                "There has not enought cores to test this case %s" % self.running_case)
        core_list = self.dut.get_core_list(
                core_config, socket=self.ports_socket)
        self.core_mask = utils.create_mask(core_list)

    def launch_testpmd_on_vhost(self, txfreet):
        """
        launch testpmd on vhost
        """
        self.get_core_mask()

        if txfreet == "normal":
            txfreet_args = "--txfreet=992"
        elif txfreet == "maximum":
            txfreet_args = "--txfreet=1020 --txrs=4"
        command_client = self.dut.target + "/app/testpmd " + \
                         " -n %d -c %s --socket-mem 1024,1024 " + \
                         " --legacy-mem --file-prefix=vhost " + \
                         " --vdev 'eth_vhost0,iface=%s/vhost-net,queues=%d,dequeue-zero-copy=1' " + \
                         " -- -i --nb-cores=%d --rxq=%d --txq=%d " + \
                         "--txd=1024 --rxd=1024 %s"
        command_line_client = command_client % (
            self.mem_channels, self.core_mask, self.base_dir,
            self.queue_number, self.nb_cores,
            self.queue_number, self.queue_number, txfreet_args)
        self.vhost.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)

    def launch_testpmd_on_vm(self):
        """
        start testpmd in vm depend on different path
        """
        command = self.dut.target + "/app/testpmd " + \
                  "-c 0x1f -n 3 -- -i " + \
                  "--nb-cores=%d --rxq=%d --txq=%d " + \
                  "--txd=1024 --rxd=1024"
        command_line = command % (self.nb_cores,
                                  self.queue_number, self.queue_number)
        self.vm_dut.send_expect(command_line, "testpmd> ", 30)

    def relaunch_testpmd_on_vm(self):
        self.vm_dut.send_expect("quit", "# ", 30)
        self.launch_testpmd_on_vm()
        self.vm_dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)

    def set_vm_vcpu(self):
        """
        config the vcpu numbers
        remove the cpupin param from vm_params
        when the cores in cpupin is the isolcpus, it will reduce the
        performance of dequeue zero copy
        And if we not use the cpupin params(taskset -c xxx), it will use
        the cpu which not set in isolcpus, and it number equal to the vcpus
        """
        params_number = len(self.vm.params)
        for i in range(params_number):
            if self.vm.params[i].keys()[0] == 'cpu':
                if 'number' in self.vm.params[i]['cpu'][0].keys():
                    self.vm.params[i]['cpu'][0]['number'] = 5
                if 'cpupin' in self.vm.params[i]['cpu'][0].keys():
                    self.vm.params[i]['cpu'][0].pop('cpupin')

    def start_one_vm(self):
        """
        start qemu
        """
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        self.vm.load_config()
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = self.virtio1_mac
        opt_args = "mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024"
        if self.queue_number > 1:
            vm_params['opt_queue'] = self.queue_number
            opt_args += ",mq=on,vectors=%d" % (2*self.queue_number + 2)
        vm_params['opt_settings'] = opt_args
        self.vm.set_vm_device(**vm_params)
        self.set_vm_vcpu()
        try:
            # Due to we have change the params info before,
            # so need to start vm with load_config=False
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def update_table_info(self, frame_size, Mpps, throughtput, cycle):
        results_row = [frame_size]
        results_row.append(Mpps)
        results_row.append(throughtput)
        results_row.append(self.queue_number)
        results_row.append(cycle)
        self.result_table_add(results_row)

    def set_fields(self):
        """
        set ip protocol field behavior
        """
        fields_config = {'ip':  {'dst': {'action': 'random'}, }, }
        return fields_config

    def calculate_avg_throughput(self, frame_size, loopback):
        """
        start to send packet and get the throughput
        """
        payload = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        flow = '[Ether(dst="%s")/IP(src="192.168.4.1",proto=255)/UDP()/("X"*%d)]' % (
            self.dst_mac, payload)
        self.tester.scapy_append('wrpcap("%s/zero_copy.pcap", %s)' % (
                                self.out_path, flow))
        self.tester.scapy_execute()

        tgenInput = []
        port = self.tester.get_local_port(self.dut_ports[0])
        tgenInput.append((port, port, "%s/zero_copy.pcap" % self.out_path))
        vm_config = self.set_fields()
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, vm_config, self.tester.pktgen)
        # set traffic option
        traffic_opt = {'delay': 5, 'duration': 20}
        _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
        Mpps = pps / 1000000.0
        # when the fwd mode is rxonly, we can not receive data, so should not verify it
        if loopback != "rxonly":
            self.verify(Mpps > 0, "can not receive packets of frame size %d" % (frame_size))
        throughput = Mpps * 100 / \
                    float(self.wirespeed(self.nic, frame_size, 1))
        return Mpps, throughput

    def check_packets_of_each_queue(self, frame_size, loopback):
        """
        check each queue has receive packets
        """
        if loopback == "rxonly":
            verify_port = 1
        else:
            verify_port = 2
        out = self.vhost.send_expect("stop", "testpmd> ", 60)
        for port_index in range(0, verify_port):
            for queue_index in range(0, self.queue_number):
                queue_info = re.findall("RX\s*Port=\s*%d/Queue=\s*%d" %
                                (port_index, queue_index),  out)
                queue = queue_info[0]
                index = out.find(queue)
                rx = re.search("RX-packets:\s*(\d*)", out[index:])
                tx = re.search("TX-packets:\s*(\d*)", out[index:])
                rx_packets = int(rx.group(1))
                tx_packets = int(tx.group(1))
                self.verify(rx_packets > 0 and tx_packets > 0,
                      "The queue %d rx-packets or tx-packets is 0 about " %
                      queue_index + \
                      "frame_size:%d, rx-packets:%d, tx-packets:%d" %
                      (frame_size, rx_packets, tx_packets))

        self.vhost.send_expect("start", "testpmd> ", 60)

    def send_and_verify(self, cycle="", loopback=""):
        """
        start to send packets and verify it
        """
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)

            Mpps, throughput = self.calculate_avg_throughput(frame_size, loopback)
            if loopback != "rxonly":
                self.update_table_info(frame_size, Mpps, throughput, cycle)
            # when multi queues, check each queue can receive packets
            if self.queue_number > 1:
                self.check_packets_of_each_queue(frame_size, loopback)

    def close_all_testpmd_and_vm(self):
        """
        close testpmd about vhost-user and vm_testpmd
        """
        self.vhost.send_expect("quit", "#", 60)
        self.vm_dut.send_expect("quit", "#", 60)
        self.dut.close_session(self.vhost)
        self.vm.stop()

    def test_perf_pvp_dequeue_zero_copy(self):
        """
        performance of pvp zero-copy with [frame_sizes]
        """
        self.nb_cores = 1
        self.queue_number = 1
        self.launch_testpmd_on_vhost(txfreet="normal")
        self.start_one_vm()
        self.launch_testpmd_on_vm()
        # set fwd mode on vm
        self.vm_dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)
        # start testpmd at host side after VM and virtio-pmd launched
        self.vhost.send_expect("start", "testpmd> ", 120)
        self.send_and_verify()
        self.close_all_testpmd_and_vm()
        self.result_table_print()

    def test_perf_pvp_dequeue_zero_copy_with_2_queue(self):
        """
        pvp dequeue zero-copy test with 2 queues
        """
        self.nb_cores = 2
        self.queue_number = 2
        self.launch_testpmd_on_vhost(txfreet="normal")
        self.start_one_vm()
        self.launch_testpmd_on_vm()
        # set fwd mode on vm
        self.vm_dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)
        # start testpmd at host side after VM and virtio-pmd launched
        self.vhost.send_expect("start", "testpmd> ", 120)
        # when multi queues, the function will check each queue can receive packets
        self.send_and_verify()
        self.close_all_testpmd_and_vm()
        self.result_table_print()

    def test_perf_pvp_dequeue_zero_copy_with_driver_unload(self):
        """
        pvp dequeue zero-copy test with driver unload test
        """
        self.nb_cores = 4
        self.queue_number = 16
        self.launch_testpmd_on_vhost(txfreet="normal")
        self.start_one_vm()
        self.launch_testpmd_on_vm()
        # set fwd mode on vm
        self.vm_dut.send_expect("set fwd rxonly", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)
        # start testpmd at host side after VM and virtio-pmd launched
        self.vhost.send_expect("start", "testpmd> ", 120)
        # when multi queues, the function will check each queue can receive packets
        self.send_and_verify(cycle="befor relaunch", loopback="rxonly")

        # relaunch testpmd at virtio side in VM for driver reloading
        self.relaunch_testpmd_on_vm()
        self.send_and_verify(cycle="after relaunch")
        self.close_all_testpmd_and_vm()
        self.result_table_print()

    def test_perf_pvp_dequeue_zero_copy_with_maximum_txfreet(self):
        """
        pvp dequeue zero-copy test with maximum txfreet
        """
        self.nb_cores = 4
        self.queue_number = 16
        self.launch_testpmd_on_vhost(txfreet="maximum")
        self.start_one_vm()
        self.launch_testpmd_on_vm()
        # set fwd mode on vm
        self.vm_dut.send_expect("set fwd mac", "testpmd> ", 30)
        self.vm_dut.send_expect("start", "testpmd> ", 30)
        # start testpmd at host side after VM and virtio-pmd launched
        self.vhost.send_expect("start", "testpmd> ", 120)
        # when multi queues, the function will check each queue can receive packets
        self.send_and_verify()
        self.close_all_testpmd_and_vm()
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
