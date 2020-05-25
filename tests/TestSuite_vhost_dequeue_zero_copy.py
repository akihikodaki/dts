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
To run this suite, the qemu version should support packed ring.
"""
import utils
import time
import re
from settings import HEADER_SIZE
from virt_common import VM
from test_case import TestCase
from packet import Packet
from pktgen import TRANSMIT_CONT


class TestVhostDequeueZeroCopy(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVhostDequeueZeroCopy, self)
        self.frame_sizes = [64, 128, 256, 512, 1024, 1518]
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.def_driver = self.dut.ports_info[self.dut_ports[0]]["port"].get_nic_driver()
        if self.def_driver != "igb_uio":
            self.dut.setup_modules_linux(self.target, 'igb_uio', '')
            self.dut.bind_interfaces_linux('igb_uio', nics_to_bind=self.dut_ports)
            self.driver_chg = True
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.port_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.vm_dut = None
        self.virtio_user = None
        self.virtio1_mac = "52:54:00:00:00:01"
        self.header_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + HEADER_SIZE['udp']

        self.logger.info("you can config packet_size in file %s.cfg," % self.suite_name + \
                    "in region 'suite' like packet_sizes=[64, 128, 256]")
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.vhost_user = self.dut.new_session(suite="vhost-user")

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        # Prepare the result table
        self.table_header = ["FrameSize(B)", "Throughput(Mpps)",
                            "% linerate", "Queue number", "Cycle"]
        self.result_table_create(self.table_header)
        self.vm_dut = None
        self.big_pkt_record = {}

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def get_core_list(self):
        """
        check whether the server has enough cores to run case
        if want to get the best perf of the vhost, the vhost tesptmd at least
        should have 3 cores to start testpmd
        """
        if self.nb_cores == 1:
            cores_num = 2
        else:
            cores_num = 1
        core_config = "1S/%dC/1T" % (self.nb_cores + cores_num)
        self.core_list = self.dut.get_core_list(
                core_config, socket=self.ports_socket)
        self.verify(len(self.core_list) >= (self.nb_cores + cores_num),
                "There has not enought cores to test this case %s" % self.running_case)

    def launch_testpmd_as_vhost(self, txfreet, zero_copy=True, client_mode=False):
        """
        launch testpmd on vhost
        """
        self.get_core_list()

        mode_info = ""
        if client_mode is True:
            mode_info = ',client=1'
        zero_copy_info = 1
        if zero_copy is False:
            zero_copy_info = 0
        if txfreet == "normal":
            txfreet_args = "--txd=1024 --rxd=1024 --txfreet=992"
        elif txfreet == "maximum":
            txfreet_args = "--txrs=4 --txd=992 --rxd=992 --txfreet=988"
        elif txfreet == "vector_rx":
            txfreet_args = "--txd=1024 --rxd=1024 --txfreet=992 --txrs=32"

        testcmd = self.dut.target + "/app/testpmd "
        vdev = [r"'eth_vhost0,iface=%s/vhost-net,queues=%d,dequeue-zero-copy=%d%s'" % (self.base_dir, self.queue_number, zero_copy_info, mode_info)]
        para = " -- -i --nb-cores=%d --rxq=%d --txq=%d %s" % (self.nb_cores, self.queue_number, self.queue_number, txfreet_args)
        eal_params = self.dut.create_eal_parameters(cores=self.core_list, prefix='vhost', ports=[self.port_pci], vdevs=vdev)
        command_line_client = testcmd + eal_params + para
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd mac", "testpmd> ", 120)

    def launch_testpmd_as_virtio_user(self, path_mode):
        """
        launch testpmd use vhost-net with path mode
        """
        # To get the best perf, the vhost and virtio testpmd should not use same cores,
        # so get the additional 3 cores to start virtio testpmd
        core_config = "1S/%dC/1T" % (len(self.core_list) + 3)
        core_list = self.dut.get_core_list(
                core_config, socket=self.ports_socket)
        self.verify(len(core_list) >= (len(self.core_list) + 3),
                "There has not enought cores to test this case %s" % self.running_case)
        testcmd = self.dut.target + "/app/testpmd "
        vdev = " --vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=./vhost-net,queue_size=1024,%s" % path_mode
        para = " -- -i --tx-offloads=0x0 --nb-cores=%d --txd=1024 --rxd=1024" % self.nb_cores
        eal_params = self.dut.create_eal_parameters(cores=core_list[len(self.core_list):],
                        prefix='virtio', no_pci=True)
        if self.check_2M_env:
            eal_params += " --single-file-segments"
        command_line = testcmd + eal_params + vdev + para
        self.virtio_user.send_expect(command_line, 'testpmd> ', 120)
        self.virtio_user.send_expect('set fwd mac', 'testpmd> ', 120)
        self.virtio_user.send_expect('start', 'testpmd> ', 120)

    def start_testpmd_on_vm(self, fwd_mode='mac'):
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
        self.vm_dut.send_expect('set fwd %s' % fwd_mode, "testpmd> ", 30)
        self.vm_dut.send_expect('start', "testpmd> ", 30)

    def restart_testpmd_on_vm(self, fwd_mode):
        self.vm_dut.send_expect("quit", "# ", 30)
        self.start_testpmd_on_vm(fwd_mode)

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
            if list(self.vm.params[i].keys())[0] == 'cpu':
                if 'number' in list(self.vm.params[i]['cpu'][0].keys()):
                    self.vm.params[i]['cpu'][0]['number'] = 5
                if 'cpupin' in list(self.vm.params[i]['cpu'][0].keys()):
                    self.vm.params[i]['cpu'][0].pop('cpupin')

    def start_one_vm(self, mode='client', packed=False):
        """
        start qemu
        """
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        self.vm.load_config()
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = self.virtio1_mac
        if mode == 'server':
            vm_params['opt_server'] = 'server'
        opt_args = "mrg_rxbuf=on,rx_queue_size=1024,tx_queue_size=1024"
        if self.queue_number > 1:
            vm_params['opt_queue'] = self.queue_number
            opt_args += ",mq=on,vectors=%d" % (2*self.queue_number + 2)
        if packed is True:
            opt_args += ',packed=on'
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
            self.logger.error("ERROR: Failure for %s, " % str(e) + \
                    "if 'packed not found' in output of start qemu log, " + \
                    "please use the qemu version which support packed ring")
            raise e

    def prepare_test_evn(self, vhost_txfreet_mode, vhost_zero_copy, vhost_client_mode,
                vm_testpmd_fwd_mode, packed_mode):
        """
        start vhost testpmd and launch qemu, start testpmd on vm
        """
        if vhost_client_mode is True:
            vm_mode = 'server'
        else:
            vm_mode = 'client'
        self.launch_testpmd_as_vhost(txfreet=vhost_txfreet_mode, zero_copy=vhost_zero_copy,
                                    client_mode=vhost_client_mode)
        self.start_one_vm(mode=vm_mode, packed=packed_mode)
        self.start_testpmd_on_vm(fwd_mode=vm_testpmd_fwd_mode)
        # start testpmd at host side after VM and virtio-pmd launched
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def update_table_info(self, frame_size, Mpps, throughtput, cycle):
        results_row = [frame_size]
        results_row.append(Mpps)
        results_row.append(throughtput)
        results_row.append(self.queue_number)
        results_row.append(cycle)
        self.result_table_add(results_row)

        # record the big pkt Mpps
        if frame_size == 1518:
            self.big_pkt_record[cycle] = Mpps

    def calculate_avg_throughput(self, frame_size, fwd_mode):
        """
        start to send packet and get the throughput
        """
        payload = frame_size - self.header_size
        flow = 'Ether(dst="%s")/IP(src="192.168.4.1",proto=255)/UDP(sport=33,dport=34)/("X"*%d)' % (
            self.dst_mac, payload)
        pkt = Packet(pkt_str=flow)
        pkt.save_pcapfile(self.tester, "%s/zero_copy.pcap" % self.tester.tmp_file)
        stream_option = {
            'pcap': "%s/zero_copy.pcap" % self.tester.tmp_file,
            'fields_config': {
                'ip': {'src': {'action': 'random', 'start': '16.0.0.1', 'step': 1, 'end': '16.0.0.64'}}},
            'stream_config': {
                'rate': 100,
                'transmit_mode': TRANSMIT_CONT,
            }
        }
        self.tester.pktgen.clear_streams()
        stream_id = self.tester.pktgen.add_stream(self.tx_port, self.tx_port,
                                    "%s/zero_copy.pcap" % self.tester.tmp_file)
        self.tester.pktgen.config_stream(stream_id, stream_option)
        traffic_opt = {
            'method': 'throughput',
            'rate': 100,
            'interval': 6,
            'duration': 30}
        stats = self.tester.pktgen.measure([stream_id], traffic_opt)

        if isinstance(stats, list):
            # if get multi result, ignore the first one, because it may not stable
            num = len(stats)
            Mpps = 0
            for index in range(1, num):
                Mpps += stats[index][1]
            Mpps = Mpps / 1000000.0 / (num-1)
        else:
            Mpps = stats[1] / 1000000.0
        # when the fwd mode is rxonly, we can not receive data, so should not verify it
        if fwd_mode != "rxonly":
            self.verify(Mpps > 0, "can not receive packets of frame size %d" % (frame_size))
        throughput = Mpps * 100 / \
                    float(self.wirespeed(self.nic, frame_size, 1))
        return Mpps, throughput

    def check_packets_of_each_queue(self, frame_size, fwd_mode):
        """
        check each queue has receive packets
        """
        if fwd_mode == "rxonly":
            verify_port = 1
        else:
            verify_port = 2
        out = self.vhost_user.send_expect("stop", "testpmd> ", 60)
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

        self.vhost_user.send_expect("start", "testpmd> ", 60)

    def send_and_verify_throughput(self, cycle="", fwd_mode=""):
        """
        start to send packets and verify it
        """
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)

            Mpps, throughput = self.calculate_avg_throughput(frame_size, fwd_mode)
            if fwd_mode != "rxonly":
                self.update_table_info(frame_size, Mpps, throughput, cycle)
            # when multi queues, check each queue can receive packets
            if self.queue_number > 1:
                self.check_packets_of_each_queue(frame_size, fwd_mode)

    def check_perf_drop_between_with_and_without_zero_copy(self):
        """
        for dequeue-zero-copy=0, about the small pkts we expect ~10% gain
        compare to dequeue-zero-copy=1
        """
        value_with_zero_copy = 0
        value_without_zero_copy = 0
        if 'dequeue-zero-copy=1' in list(self.big_pkt_record.keys()):
            value_with_zero_copy = self.big_pkt_record['dequeue-zero-copy=1']
        if 'dequeue-zero-copy=0' in list(self.big_pkt_record.keys()):
            value_without_zero_copy = self.big_pkt_record['dequeue-zero-copy=0']
        self.verify(value_with_zero_copy != 0 and value_without_zero_copy != 0,
                'can not get the value of big pkts, please check self.frame_sizes')
        self.verify(value_with_zero_copy - value_without_zero_copy >= value_with_zero_copy*0.05,
                'the drop with dequeue-zero-copy=0 is not as expected')

    def close_all_testpmd_and_vm(self):
        """
        close testpmd about vhost-user and vm_testpmd
        """
        if getattr(self, 'vhost_user', None):
            self.vhost_user.send_expect("quit", "#", 60)
        if getattr(self, 'virtio_user', None):
            self.virtio_user.send_expect("quit", "#", 60)
            self.dut.close_session(self.virtio_user)
            self.virtio_user = None
        if getattr(self, 'vm_dut', None):
            self.vm_dut.send_expect("quit", "#", 60)
            self.vm.stop()

    def test_perf_pvp_split_ring_dequeue_zero_copy(self):
        """
        pvp split ring dequeue zero-copy test
        """
        self.nb_cores = 1
        self.queue_number = 1
        self.logger.info('start vhost testpmd with dequeue-zero-copy=1 to test')
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=False)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')

        self.close_all_testpmd_and_vm()
        self.logger.info('start vhost testpmd with dequeue-zero-copy=0 to test')
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=False,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=False)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=0')
        self.result_table_print()
        self.check_perf_drop_between_with_and_without_zero_copy()

    def test_perf_pvp_packed_ring_dequeue_zero_copy(self):
        """
        pvp packed ring dequeue zero-copy test
        """
        self.nb_cores = 1
        self.queue_number = 1
        self.logger.info('start vhost testpmd with dequeue-zero-copy=1 to test')
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=True)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')

        self.close_all_testpmd_and_vm()
        self.logger.info('start vhost testpmd with dequeue-zero-copy=0 to test')
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=False,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=True)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=0')
        self.result_table_print()
        self.check_perf_drop_between_with_and_without_zero_copy()

    def test_perf_pvp_split_ring_dequeue_zero_copy_with_2_queue(self):
        """
        pvp split ring dequeue zero-copy test with 2 queues
        """
        self.nb_cores = 2
        self.queue_number = 2
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=False)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')
        self.result_table_print()

    def test_perf_pvp_packed_ring_dequeue_zero_copy_with_2_queue(self):
        """
        pvp packed ring dequeue zero-copy test with 2 queues
        """
        self.nb_cores = 2
        self.queue_number = 2
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=True)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')
        self.result_table_print()

    def test_perf_pvp_split_ring_dequeue_zero_copy_with_driver_unload(self):
        """
        pvp split ring dequeue zero-copy test with driver reload test
        """
        self.nb_cores = 4
        self.queue_number = 16
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='rxonly', packed_mode=False)
        self.send_and_verify_throughput(cycle="before relaunch", fwd_mode="rxonly")

        # relaunch testpmd at virtio side in VM for driver reloading
        self.restart_testpmd_on_vm(fwd_mode='mac')
        self.send_and_verify_throughput(cycle="after relaunch")
        self.result_table_print()

    def test_perf_pvp_packed_ring_dequeue_zero_copy_with_driver_unload(self):
        """
        pvp packed ring dequeue zero-copy test with driver reload test
        """
        self.nb_cores = 4
        self.queue_number = 16
        self.prepare_test_evn(vhost_txfreet_mode='normal', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='rxonly', packed_mode=True)
        self.send_and_verify_throughput(cycle="before relaunch", fwd_mode="rxonly")

        # relaunch testpmd at virtio side in VM for driver reloading
        self.restart_testpmd_on_vm(fwd_mode='mac')
        self.send_and_verify_throughput(cycle="after relaunch")
        self.result_table_print()

    def test_perf_pvp_split_ring_dequeue_zero_copy_with_maximum_txfreet(self):
        """
        pvp split ring dequeue zero-copy test with maximum txfreet
        """
        self.nb_cores = 4
        self.queue_number = 16
        self.prepare_test_evn(vhost_txfreet_mode='maximum', vhost_zero_copy=True,
                    vhost_client_mode=False, vm_testpmd_fwd_mode='mac', packed_mode=False)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')
        self.result_table_print()

    def test_perf_pvp_split_ring_dequeue_zero_copy_with_vector_rx(self):
        """
        pvp split ring dequeue zero-copy test with vector_rx path
        """
        self.nb_cores = 1
        self.queue_number = 1
        path_mode = 'packed_vq=0,in_order=0,mrg_rxbuf=0'
        self.virtio_user = self.dut.new_session(suite="virtio-user")

        self.logger.info('start vhost testpmd with dequeue-zero-copy=1 to test')
        self.launch_testpmd_as_vhost(txfreet="vector_rx", zero_copy=True, client_mode=False)
        self.vhost_user.send_expect("start", "testpmd> ", 120)
        self.launch_testpmd_as_virtio_user(path_mode)
        self.send_and_verify_throughput(cycle='dequeue-zero-copy=1')
        self.result_table_print()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.close_all_testpmd_and_vm()
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        if getattr(self, "driver_chg", None):
            self.dut.bind_interfaces_linux(self.def_driver, nics_to_bind=self.dut_ports)
        if getattr(self, 'vhost_user', None):
            self.dut.close_session(self.vhost_user)
