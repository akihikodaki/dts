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
Virtio idx interrupt need test with l3fwd-power sample
"""

import utils
import time
import _thread
import re
from virt_common import VM
from test_case import TestCase
from pktgen import PacketGeneratorHelper


class TestVirtioIdxInterrupt(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVirtioIdxInterrupt, self)
        self.queues = 1
        self.nb_cores = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                            == self.ports_socket])
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.pf_pci = self.dut.ports_info[0]['pci']

        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.app_testpmd_path = self.dut.apps_name['test-pmd']
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.device_str = None

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.flag = None
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vhost = self.dut.new_session(suite="vhost")

    def get_core_mask(self):
        self.core_config = "1S/%dC/1T" % (self.nb_cores + 1)
        self.verify(self.cores_num >= (self.nb_cores + 1),
                    "There has not enough cores to test this case %s" %
                    self.running_case)
        self.core_list = self.dut.get_core_list(self.core_config)

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """
        self.dut.setup_modules(self.target, "igb_uio","None")
        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev misc', '# ', 30)
        cbdma_dev_infos = re.findall('\s*(0000:\d+:\d+.\d+)', out)
        self.verify(len(cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')

        used_cbdma = cbdma_dev_infos[0:cbdma_num]
        dmas_info = ''
        for dmas in used_cbdma:
            number = used_cbdma.index(dmas)
            dmas = 'txq{}@{};'.format(number, dmas)
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = ' '.join(used_cbdma)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s %s' %
                             ("igb_uio", self.device_str, self.pf_pci), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    def start_vhost_testpmd(self, dmas=None, mode=False):
        """
        start the testpmd on vhost side
        """
        # get the core mask depend on the nb_cores number
        self.get_core_mask()
        testcmd = self.app_testpmd_path + " "
        if dmas:
            device_str = self.device_str.split(" ")
            device_str.append(self.pf_pci)
            if mode:
                vdev = ["'net_vhost,iface=%s/vhost-net,queues=%d,%s=1,dmas=[%s],dmathr=64'" % (self.base_dir, self.queues, mode, dmas)]
            else:
                vdev = ['net_vhost,iface=%s/vhost-net,queues=%d,dmas=[%s]' % (self.base_dir, self.queues, dmas)]
            eal_params = self.dut.create_eal_parameters(cores=self.core_list, prefix='vhost', ports=device_str, vdevs=vdev)
        else:
            vdev = ['net_vhost,iface=%s/vhost-net,queues=%d ' % (self.base_dir, self.queues)]
            eal_params = self.dut.create_eal_parameters(cores=self.core_list, prefix='vhost', ports=[self.pf_pci], vdevs=vdev)
        para = " -- -i --nb-cores=%d --txd=1024 --rxd=1024 --rxq=%d --txq=%d" % (self.nb_cores, self.queues, self.queues)
        command_line = testcmd + eal_params + para
        self.vhost.send_expect(command_line, "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def start_vms(self, packed=False, mode=False):
        """
        start qemus
        """
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        if mode:
            vm_params['opt_path'] = '%s/vhost-net,%s' % (self.base_dir, mode)
        else:
            vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = "00:11:22:33:44:55"
        opt_args = "mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on"
        if self.queues > 1:
            vm_params['opt_queue'] = self.queues
            opt_args = opt_args + ",mq=on,vectors=%d" % (2*self.queues + 2)
        if packed:
            opt_args = opt_args + ',packed=on'
        vm_params['opt_settings'] = opt_args
        self.vm.set_vm_device(**vm_params)
        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))
        self.vm_dut.restore_interfaces()

    def config_virito_net_in_vm(self):
        """
        config ip for virtio net
        set net for multi queues enable
        """
        self.vm_intf = self.vm_dut.ports_info[0]['intf']
        self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
        out = self.vm_dut.send_expect("ifconfig", "#")
        self.verify(self.vm_intf not in out, "the virtio-pci down failed")
        self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")
        if self.queues > 1:
            self.vm_dut.send_expect("ethtool -L %s combined %d" %
                            (self.vm_intf, self.queues), "#", 20)

    def start_to_send_packets(self, delay):
        """
        start send packets
        """
        tgen_input = []
        port = self.tester.get_local_port(self.dut_ports[0])
        self.tester.scapy_append('a=[Ether(dst="%s")/IP(src="0.240.74.101",proto=255)/UDP()/("X"*18)]' % (self.dst_mac))
        self.tester.scapy_append('wrpcap("%s/interrupt.pcap", a)' % self.out_path)
        self.tester.scapy_execute()

        tgen_input.append((port, port, "%s/interrupt.pcap" % self.out_path))
        self.tester.pktgen.clear_streams()
        fields_config = {'ip':  {'dst': {'action': 'random'}, }, }
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 1, fields_config, self.tester.pktgen)
        traffic_opt = {'delay': 5, 'duration': delay, 'rate': 1}
        _, self.flag = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)

    def check_packets_after_reload_virtio_device(self, reload_times):
        """
        start to send packets and check virtio net has receive packets
        """
        # ixia send packets times equal to reload_times * wait_times
        start_time = time.time()
        _thread.start_new_thread(self.start_to_send_packets, (reload_times*20,))
        # wait the ixia begin to send packets
        time.sleep(10)
        self.vm_pci = self.vm_dut.ports_info[0]['pci']
        # reload virtio device to check the virtio-net can receive packets
        for i in range(reload_times+1):
            if time.time() - start_time > reload_times*30:
                self.logger.error("The ixia has stop to send packets, "
                        "please change the delay time of ixia")
                self.logger.info("The virtio device has reload %d times" % i)
                return False
            self.logger.info("The virtio net device reload %d times" % i)
            self.vm_dut.send_expect("tcpdump -n -vv -i %s" % self.vm_intf,
                                    "tcpdump", 30)
            time.sleep(5)
            out = self.vm_dut.get_session_output(timeout=3)
            self.vm_dut.send_expect("^c", "#", 30)
            self.verify("ip-proto-255" in out,
                        "The virtio device can not receive packets"
                        "after reload %d times" % i)
            time.sleep(2)
            # reload virtio device
            self.vm_dut.restore_interfaces()
            time.sleep(3)
            self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
            self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")

        # wait ixia thread exit
        self.logger.info("wait the thread of ixia to exit")
        while(1):
            if self.flag is not None:
                break
            time.sleep(5)
        return True

    def check_each_queue_has_packets_info_on_vhost(self):
        """
        check each queue has receive packets on vhost side
        """
        out = self.vhost.send_expect("stop", "testpmd> ", 60)
        print(out)
        for queue_index in range(0, self.queues):
            queue = re.search("Port= 0/Queue=\s*%d" % queue_index, out)
            queue = queue.group()
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                   "The queue %d rx-packets or tx-packets is 0 about " %
                   queue_index + \
                   "rx-packets:%d, tx-packets:%d" %
                   (rx_packets, tx_packets))

        self.vhost.send_expect("clear port stats all", "testpmd> ", 60)

    def stop_all_apps(self):
        """
        close all vms
        """
        self.vm.stop()
        self.vhost.send_expect("quit", "#", 20)

    def test_perf_split_ring_virito_pci_driver_reload(self):
        """
        virtio-pci driver reload test
        """
        self.queues = 1
        self.nb_cores = 1
        self.start_vhost_testpmd()
        self.start_vms()
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=30)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_wake_up_split_ring_virtio_net_cores_with_event_idx_interrupt_mode_16queue(self):
        """
        wake up virtio-net cores with event idx interrupt mode 16 queues test
        """
        self.queues = 16
        self.nb_cores = 16
        self.start_vhost_testpmd()
        self.start_vms()
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

    def test_perf_packed_ring_virito_pci_driver_reload(self):
        """
        virtio-pci driver reload test
        """
        self.queues = 1
        self.nb_cores = 1
        self.start_vhost_testpmd()
        self.start_vms(packed=True)
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=30)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_wake_up_packed_ring_virtio_net_cores_with_event_idx_interrupt_mode_16queue(self):
        """
        wake up virtio-net cores with event idx interrupt mode 16 queues test
        """
        self.queues = 16
        self.nb_cores = 16
        self.start_vhost_testpmd()
        self.start_vms(packed=True)
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

    def test_perf_split_ring_virito_pci_driver_reload_with_cbdma_enabled(self):
        """
        Test Case 7: Split ring virtio-pci driver reload test with CBDMA enabled
        """
        self.queues = 1
        self.nb_cores = 1
        used_cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        self.start_vhost_testpmd(dmas=self.dmas_info)
        self.start_vms()
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=30)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_wake_up_split_ring_virtio_net_cores_with_event_idx_interrupt_mode_and_cbdma_enabled_16queue(self):
        """
        Test Case 8: Wake up split ring virtio-net cores with event idx interrupt mode and cbdma enabled 16 queues test
        """
        self.queues = 16
        self.nb_cores = 16
        used_cbdma_num = 16
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        self.start_vhost_testpmd(dmas=self.dmas_info, mode='client')
        self.start_vms(packed=False, mode='server')
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.close_session(self.vhost)
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.bind_cbdma_device_to_kernel()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
