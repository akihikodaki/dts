# BSD LICENSE
#
# Copyright(c) <2021> Intel Corporation. All rights reserved.
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
"""

import utils
import re
import time
import os
from test_case import TestCase
from packet import Packet
from pktgen import PacketGeneratorHelper
from pmd_output import PmdOutput
from virt_common import VM


class TestVswitchSampleCBDMA(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.set_max_queues(512)
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.tester_tx_port_num = 1
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.dut_ports = self.dut.get_ports()
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.socket)
        self.vhost_core_list = self.cores[0:2]
        self.vuser0_core_list = self.cores[2:4]
        self.vuser1_core_list = self.cores[4:6]
        self.vhost_core_mask = utils.create_mask(self.vhost_core_list)
        self.mem_channels = self.dut.get_memory_channels()
        # get cbdma device
        self.cbdma_dev_infos = []
        self.dmas_info = None
        self.device_str = None
        self.out_path = '/tmp'
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        txport = self.tester.get_local_port(self.dut_ports[0])
        self.txItf = self.tester.get_interface(txport)
        self.virtio_dst_mac0 = '00:11:22:33:44:10'
        self.virtio_dst_mac1 = '00:11:22:33:44:11'
        self.vm_dst_mac0 = '52:54:00:00:00:01'
        self.vm_dst_mac1 = '52:54:00:00:00:02'
        self.vm_num = 2
        self.vm_dut = []
        self.vm = []
        self.app_testpmd_path = self.dut.apps_name['test-pmd']
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()


    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -I qemu-system-x86_64", '#', 20)
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user0 = self.dut.new_session(suite="virtio-user0")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.virtio_user0_pmd = PmdOutput(self.dut, self.virtio_user0)
        self.virtio_user1_pmd = PmdOutput(self.dut, self.virtio_user1)

    def set_async_threshold(self, async_threshold=256):
        self.logger.info("Configure async_threshold to {}".format(async_threshold))
        self.dut.send_expect("sed -i -e 's/f.async_threshold = .*$/f.async_threshold = {};/' "
                             "./examples/vhost/main.c".format(async_threshold), "#", 20)

    def set_max_queues(self, max_queues=512):
        self.logger.info("Configure MAX_QUEUES to {}".format(max_queues))
        self.dut.send_expect("sed -i -e 's/#define MAX_QUEUES .*$/#define MAX_QUEUES {}/' "
                             "./examples/vhost/main.c".format(max_queues), "#", 20)

    def build_vhost_app(self):
        out = self.dut.build_dpdk_apps('./examples/vhost')
        self.verify('Error' not in out, 'compilation vhost error')

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def start_vhost_app(self, with_cbdma=True, cbdma_num=1, socket_num=1, client_mode=False):
        """
        launch the vhost app on vhost side
        """
        self.app_path = self.dut.apps_name['vhost']
        socket_file_param = ''
        for item in range(socket_num):
            socket_file_param += '--socket-file ./vhost-net{} '.format(item)
        allow_pci = [self.dut.ports_info[0]['pci']]
        for item in range(cbdma_num):
            allow_pci.append(self.cbdma_dev_infos[item])
        allow_option = ''
        for item in allow_pci:
            allow_option += ' -a {}'.format(item)
        if with_cbdma:
            if client_mode:
                params = (" -c {} -n {} {} -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 "
                          + socket_file_param + "--dmas [{}] --client").format(self.vhost_core_mask, self.mem_channels,
                                                                               allow_option, self.dmas_info)
            else:
                params = (" -c {} -n {} {} -- -p 0x1 --mergeable 1 --vm2vm 1 --dma-type ioat --stats 1 "
                          + socket_file_param + "--dmas [{}]").format(self.vhost_core_mask, self.mem_channels,
                                                                      allow_option, self.dmas_info)
        else:
            params = (" -c {} -n {} {} -- -p 0x1 --mergeable 1 --vm2vm 1 --stats 1 " + socket_file_param).format(
                self.vhost_core_mask, self.mem_channels, allow_option)
        self.command_line = self.app_path + params
        self.vhost_user.send_command(self.command_line)
        # After started dpdk-vhost app, wait 3 seconds
        time.sleep(3)

    def start_virtio_testpmd(self, pmd_session, dev_mac, dev_id, cores, prefix,  enable_queues=1, server_mode=False,
                             nb_cores=1, used_queues=1):
        """
        launch the testpmd as virtio with vhost_net0
        """
        if server_mode:
            eal_params = " --vdev=net_virtio_user0,mac={},path=./vhost-net{},queues={},server=1".format(dev_mac, dev_id,
                                                                                                        enable_queues)
        else:
            eal_params = " --vdev=net_virtio_user0,mac={},path=./vhost-net{},queues={}".format(dev_mac, dev_id,
                                                                                               enable_queues)
        if self.check_2M_env:
            eal_params += " --single-file-segments"
        params = "--nb-cores={} --rxq={} --txq={} --txd=1024 --rxd=1024".format(nb_cores, used_queues, used_queues)
        pmd_session.start_testpmd(cores=cores, param=params, eal_param=eal_params, no_pci=True, ports=[], prefix=prefix,
                                  fixed_prefix=True)

    def start_vms(self, mode=0, mergeable=True):
        """
        start two VM, each VM has one virtio device
        """
        if mode == 0:
            setting_args = "disable-modern=true"
        elif mode == 1:
            setting_args = "disable-modern=false"
        elif mode == 2:
            setting_args = "disable-modern=false,packed=on"
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

    def start_vm_testpmd(self, pmd_session):
        """
        launch the testpmd in vm
        """
        self.vm_cores = [1,2]
        param = "--rxq=1 --txq=1 --nb-cores=1 --txd=1024 --rxd=1024"
        pmd_session.start_testpmd(cores=self.vm_cores, param=param)

    def repeat_bind_driver(self, dut, repeat_times=50):
        i = 0
        while i < repeat_times:
            dut.unbind_interfaces_linux()
            dut.bind_interfaces_linux(driver='virtio-pci')
            dut.bind_interfaces_linux(driver='vfio-pci')
            i += 1

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """
        str_info = 'Misc (rawdev) devices using kernel driver'
        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev misc', '# ', 30)
        device_info = out.split('\n')
        for device in device_info:
            pci_info = re.search('\s*(0000:\d*:\d*.\d*)', device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')
        used_cbdma = self.cbdma_dev_infos[0:cbdma_num]
        dmas_info = ''
        for dmas in used_cbdma:
            number = used_cbdma.index(dmas)
            dmas = 'txd{}@{},'.format(number, dmas.replace('0000:', ''))
            dmas_info += dmas
        self.dmas_info = dmas_info[:-1]
        self.device_str = ' '.join(used_cbdma)
        self.dut.setup_modules(self.target, "igb_uio","None")
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s' % ("igb_uio", self.device_str), '# ', 60)

    def send_vlan_packet(self, dts_mac, pkt_size=64, pkt_count=1):
        """
        Send a vlan packet with vlan id 1000
        """
        pkt = Packet(pkt_type='VLAN_UDP', pkt_len=pkt_size)
        pkt.config_layer('ether', {'dst': dts_mac})
        pkt.config_layer('vlan', {'vlan': 1000})
        pkt.send_pkt(self.tester, tx_port=self.txItf, count=pkt_count)

    def verify_receive_packet(self, pmd_session, expected_pkt_count):
        out = pmd_session.execute_cmd("show port stats all")
        rx_num = re.compile('RX-packets: (.*?)\s+?').findall(out, re.S)
        self.verify((int(rx_num[0]) >= int(expected_pkt_count)), "Can't receive enough packets from tester")

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str, '# ', 60)

    def config_stream(self, frame_size, port_num, dst_mac_list):
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        for item in range(port_num):
            for dst_mac in dst_mac_list:
                pkt = Packet(pkt_type='VLAN_UDP', pkt_len=frame_size)
                pkt.config_layer('ether', {'dst': dst_mac})
                pkt.config_layer('vlan', {'vlan': 1000})
                pcap = os.path.join(self.out_path, "vswitch_sample_cbdma_%s_%s_%s.pcap" % (item, dst_mac, frame_size))
                pkt.save_pcapfile(None, pcap)
                tgen_input.append((rx_port, tx_port, pcap))
        return tgen_input

    def perf_test(self, frame_size, dst_mac_list):
        # Create test results table
        table_header = ['Frame Size(Byte)', 'Throughput(Mpps)']
        self.result_table_create(table_header)
        # Begin test perf
        test_result = {}
        for frame_size in frame_size:
            self.logger.info("Test running at parameters: " + "framesize: {}".format(frame_size))
            tgenInput = self.config_stream(frame_size, self.tester_tx_port_num, dst_mac_list)
            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, None, self.tester.pktgen)
            # set traffic option
            traffic_opt = {'duration': 5}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            self.verify(pps > 0, "No traffic detected")
            throughput = pps / 1000000.0
            test_result[frame_size] = throughput
            self.result_table_add([frame_size, throughput])
        self.result_table_print()
        return test_result

    def pvp_test_with_cbdma(self, socket_num=1, with_cbdma=True, cbdma_num=1):
        self.frame_sizes = [64, 512, 1024, 1518]
        self.start_vhost_app(with_cbdma=with_cbdma, cbdma_num=cbdma_num, socket_num=socket_num, client_mode=False)
        self.start_virtio_testpmd(pmd_session=self.virtio_user0_pmd, dev_mac=self.virtio_dst_mac0, dev_id=0,
                                  cores=self.vuser0_core_list, prefix='testpmd0', enable_queues=1, server_mode=False,
                                  nb_cores=1, used_queues=1)
        self.virtio_user0_pmd.execute_cmd('set fwd mac')
        self.virtio_user0_pmd.execute_cmd('start tx_first')
        self.virtio_user0_pmd.execute_cmd('stop')
        self.virtio_user0_pmd.execute_cmd('start')
        dst_mac_list = [self.virtio_dst_mac0]
        perf_result = self.perf_test(frame_size=self.frame_sizes,dst_mac_list=dst_mac_list)
        return perf_result

    def test_perf_check_with_cbdma_channel_using_vhost_async_driver(self):
        """
        Test Case1: PVP performance check with CBDMA channel using vhost async driver
        """
        perf_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(1)

        # test cbdma copy
        # CBDMA copy needs vhost enqueue with cbdma channel using parameter '-dmas'
        self.set_async_threshold(1518)
        self.build_vhost_app()
        cbmda_copy = self.pvp_test_with_cbdma(socket_num=1, with_cbdma=True, cbdma_num=1)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        # test sync copy
        # Sync copy needs vhost enqueue with cbdma channel, but threshold ( can be adjusted by change value of
        # f.async_threshold in dpdk code) is larger than forwarding packet length
        self.set_async_threshold(0)
        self.build_vhost_app()
        sync_copy = self.pvp_test_with_cbdma(socket_num=1, with_cbdma=True, cbdma_num=1)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        # test CPU copy
        # CPU copy means vhost enqueue w/o cbdma channel
        cpu_copy = self.pvp_test_with_cbdma(socket_num=1, with_cbdma=False, cbdma_num=0)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        self.table_header = ['Frame Size(Byte)', 'Mode', 'Throughput(Mpps)']
        self.result_table_create(self.table_header)
        for key in cbmda_copy.keys():
            perf_result.append([key, 'cbdma_copy', cbmda_copy[key]])
        for key in sync_copy.keys():
            perf_result.append([key, 'sync_copy', sync_copy[key]])
        for key in cpu_copy.keys():
            perf_result.append([key, 'cpu_copy', cpu_copy[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def pvp_test_with_multi_cbdma(self, socket_num=2, with_cbdma=True, cbdma_num=1, launch_virtio=True, quit_vhost=False):
        self.frame_sizes = [1518]
        self.start_vhost_app(with_cbdma=with_cbdma, cbdma_num=cbdma_num, socket_num=socket_num, client_mode=True)
        if launch_virtio:
            self.start_virtio_testpmd(pmd_session=self.virtio_user0_pmd, dev_mac=self.virtio_dst_mac0, dev_id=0,
                                      cores=self.vuser0_core_list, prefix='testpmd0', enable_queues=1, server_mode=True,
                                      nb_cores=1, used_queues=1)
            self.start_virtio_testpmd(pmd_session=self.virtio_user1_pmd, dev_mac=self.virtio_dst_mac1, dev_id=1,
                                      cores=self.vuser1_core_list, prefix='testpmd1', enable_queues=1, server_mode=True,
                                      nb_cores=1, used_queues=1)
            self.virtio_user0_pmd.execute_cmd('set fwd mac')
            self.virtio_user0_pmd.execute_cmd('start tx_first')
            self.virtio_user0_pmd.execute_cmd('stop')
            self.virtio_user0_pmd.execute_cmd('start')
            self.virtio_user1_pmd.execute_cmd('set fwd mac')
            self.virtio_user1_pmd.execute_cmd('start tx_first')
            self.virtio_user1_pmd.execute_cmd('stop')
            self.virtio_user1_pmd.execute_cmd('start')
        else:
            self.virtio_user0_pmd.execute_cmd('stop', 'testpmd> ', 30)
            self.virtio_user0_pmd.execute_cmd('start tx_first', 'testpmd> ', 30)
            self.virtio_user1_pmd.execute_cmd('stop', 'testpmd> ', 30)
            self.virtio_user1_pmd.execute_cmd('start tx_first', 'testpmd> ', 30)
        dst_mac_list = [self.virtio_dst_mac0, self.virtio_dst_mac1]
        perf_result = self.perf_test(self.frame_sizes, dst_mac_list)
        if quit_vhost:
            self.vhost_user.send_expect("^C", "# ", 20)
        return perf_result

    def test_perf_check_with_multiple_cbdma_channels_using_vhost_async_driver(self):
        """
        Test Case2: PVP test with multiple CBDMA channels using vhost async driver
        """
        perf_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        self.set_async_threshold(256)
        self.build_vhost_app()

        self.logger.info("Launch vhost app perf test")
        before_relunch= self.pvp_test_with_multi_cbdma(socket_num=2, with_cbdma=True, cbdma_num=2, launch_virtio=True, quit_vhost=True)

        self.logger.info("Relaunch vhost app perf test")
        after_relunch = self.pvp_test_with_multi_cbdma(socket_num=2, with_cbdma=True, cbdma_num=2, launch_virtio=False, quit_vhost=False)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.virtio_user1_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        self.table_header = ['Frame Size(Byte)', 'Mode', 'Throughput(Mpps)']
        self.result_table_create(self.table_header)
        for key in before_relunch.keys():
            perf_result.append([key, 'Before Re-launch vhost', before_relunch[key]])
        for key in after_relunch.keys():
            perf_result.append([key, 'After Re-launch vhost', after_relunch[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        self.verify(abs(before_relunch[1518] - after_relunch[1518]) / before_relunch[1518] < 0.1, "Perf is unstable, \
        before relaunch vhost app: %s, after relaunch vhost app: %s" % (before_relunch[1518], after_relunch[1518]))

    def get_receive_throughput(self, pmd_session, count=5):
        i = 0
        while i < count:
            pmd_session.execute_cmd('show port stats all')
            i += 1
        else:
            out = pmd_session.execute_cmd('show port stats all')
            pmd_session.execute_cmd('stop')
            rx_throughput = re.compile('Rx-pps: \s+(.*?)\s+?').findall(out, re.S)
        return float(rx_throughput[0]) / 1000000.0

    def set_testpmd0_param(self, pmd_session, eth_peer_mac):
        pmd_session.execute_cmd('set fwd mac')
        pmd_session.execute_cmd('start tx_first')
        pmd_session.execute_cmd('stop')
        pmd_session.execute_cmd('set eth-peer 0 %s' % eth_peer_mac)
        pmd_session.execute_cmd('start')

    def set_testpmd1_param(self, pmd_session, eth_peer_mac):
        pmd_session.execute_cmd('set fwd mac')
        pmd_session.execute_cmd('set eth-peer 0 %s' % eth_peer_mac)

    def send_pkts_from_testpmd1(self, pmd_session, pkt_len):
        pmd_session.execute_cmd('set txpkts %s' % pkt_len)
        pmd_session.execute_cmd('start tx_first')

    def vm2vm_check_with_two_cbdma(self, with_cbdma=True, cbdma_num=2, socket_num=2):
        frame_sizes = [256, 2000]
        self.start_vhost_app(with_cbdma=with_cbdma, cbdma_num=cbdma_num, socket_num=socket_num, client_mode=False)
        self.start_virtio_testpmd(pmd_session=self.virtio_user0_pmd, dev_mac=self.virtio_dst_mac0, dev_id=0,
                                  cores=self.vuser0_core_list, prefix='testpmd0', enable_queues=1, server_mode=False,
                                  nb_cores=1, used_queues=1)
        self.start_virtio_testpmd(pmd_session=self.virtio_user1_pmd, dev_mac=self.virtio_dst_mac1, dev_id=1,
                                  cores=self.vuser1_core_list, prefix='testpmd1', enable_queues=1, server_mode=False,
                                  nb_cores=1, used_queues=1)
        self.set_testpmd0_param(self.virtio_user0_pmd, self.virtio_dst_mac1)
        self.set_testpmd1_param(self.virtio_user1_pmd, self.virtio_dst_mac0)

        rx_throughput = {}
        for frame_size in frame_sizes:
            self.send_pkts_from_testpmd1(pmd_session=self.virtio_user1_pmd, pkt_len=frame_size)
            # Create test results table
            table_header = ['Frame Size(Byte)', 'Throughput(Mpps)']
            self.result_table_create(table_header)
            rx_pps = self.get_receive_throughput(pmd_session=self.virtio_user1_pmd)
            self.result_table_add([frame_size, rx_pps])
            rx_throughput[frame_size] = rx_pps
            self.result_table_print()
        return rx_throughput

    def test_vm2vm_check_with_two_cbdma_channels_using_vhost_async_driver(self):
        """
        Test Case3: VM2VM performance test with two CBDMA channels using vhost async driver
        """
        perf_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        self.set_async_threshold(256)
        self.build_vhost_app()

        cbdma_enable = self.vm2vm_check_with_two_cbdma(with_cbdma=True, cbdma_num=2, socket_num=2)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.virtio_user1_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        cbdma_disable = self.vm2vm_check_with_two_cbdma(with_cbdma=False, cbdma_num=2, socket_num=2)

        self.virtio_user0_pmd.execute_cmd("quit", "#")
        self.virtio_user1_pmd.execute_cmd("quit", "#")
        self.vhost_user.send_expect("^C", "# ", 20)

        self.table_header = ['Frame Size(Byte)', 'CBDMA Enable/Disable', 'Throughput(Mpps)']
        self.result_table_create(self.table_header)
        for key in cbdma_enable.keys():
            perf_result.append([key, 'Enable', cbdma_enable[key]])
        for key in cbdma_disable.keys():
            perf_result.append([key, 'Disable', cbdma_disable[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

        for cbdma_key in cbdma_enable.keys():
            if cbdma_key == '2000':
                self.verify(cbdma_enable[cbdma_key] > cbdma_disable[cbdma_key],
                            "CBDMA Enable Performance {} should better than CBDMA Disable Performance {} when send 2000"
                            " length packets".format(cbdma_enable[cbdma_key], cbdma_disable[cbdma_key]))
            elif cbdma_key == '256':
                self.verify(cbdma_disable[cbdma_key] > cbdma_enable[cbdma_key],
                            "CBDMA Enable Performance {}  should lower than CBDMA Disable Performance {} when send 256"
                            " length packets".format(cbdma_enable[cbdma_key], cbdma_disable[cbdma_key]))

    def vm2vm_check_with_two_vhost_device(self, with_cbdma=True, cbdma_num=2, socket_num=2, launch=True):
        frame_sizes = [256, 2000]
        if launch:
            self.start_vhost_app(with_cbdma=with_cbdma, cbdma_num=cbdma_num, socket_num=socket_num, client_mode=False)
            self.start_vms(mode=0, mergeable=False)
            self.vm0_pmd = PmdOutput(self.vm_dut[0])
            self.vm1_pmd = PmdOutput(self.vm_dut[1])
            self.start_vm_testpmd(self.vm0_pmd)
            self.start_vm_testpmd(self.vm1_pmd)
        self.set_testpmd0_param(self.vm0_pmd, self.vm_dst_mac1)
        self.set_testpmd1_param(self.vm1_pmd, self.vm_dst_mac0)

        rx_throughput = {}
        for frame_size in frame_sizes:
            self.send_pkts_from_testpmd1(pmd_session=self.vm1_pmd, pkt_len=frame_size)
            # Create test results table
            table_header = ['Frame Size(Byte)', 'Throughput(Mpps)']
            self.result_table_create(table_header)
            rx_pps = self.get_receive_throughput(pmd_session=self.vm1_pmd)
            self.result_table_add([frame_size, rx_pps])
            rx_throughput[frame_size] = rx_pps
            self.result_table_print()

        return rx_throughput

    def start_vms_testpmd_and_test(self, launch, quit_vm_testpmd=False):
        # start vm0 amd vm1 testpmd, send 256 and 2000 length packets from vm1 testpmd
        perf_result = self.vm2vm_check_with_two_vhost_device(with_cbdma=True, cbdma_num=2, socket_num=2, launch=launch)
        # stop vm1 and clear vm1 stats
        self.vm1_pmd.execute_cmd("stop")
        self.vm1_pmd.execute_cmd("clear port stats all")
        # stop vm0 and clear vm0 stats
        self.vm0_pmd.execute_cmd("stop")
        self.vm0_pmd.execute_cmd("clear port stats all")
        # only start vm0 and send packets from tester, and check vm0 can receive more then tester send packets' count
        self.vm0_pmd.execute_cmd("start")
        self.send_vlan_packet(dts_mac=self.vm_dst_mac0, pkt_size=64, pkt_count=100)
        time.sleep(3)
        self.verify_receive_packet(pmd_session=self.vm0_pmd, expected_pkt_count=100)
        # stop vm0
        self.vm0_pmd.execute_cmd("stop")
        # only start vm1 and send packets from tester, and check vm1 can receive more then tester send packets' count
        self.vm1_pmd.execute_cmd("start")
        # clear vm1 stats after send start command
        self.vm1_pmd.execute_cmd("clear port stats all")
        self.send_vlan_packet(dts_mac=self.vm_dst_mac1, pkt_size=64, pkt_count=100)
        time.sleep(3)
        self.verify_receive_packet(pmd_session=self.vm1_pmd, expected_pkt_count=100)
        if quit_vm_testpmd:
            self.vm0_pmd.execute_cmd("quit", "#")
            self.vm1_pmd.execute_cmd("quit", "#")
        return perf_result

    def test_vm2vm_check_with_two_vhost_device_using_vhost_async_driver(self):
        """
        Test Case4: VM2VM test with 2 vhost device using vhost async driver
        """
        perf_result = []
        self.get_cbdma_ports_info_and_bind_to_dpdk(2)
        self.set_async_threshold(256)
        self.build_vhost_app()

        before_rebind = self.start_vms_testpmd_and_test(launch=True, quit_vm_testpmd=True)
        # repeat bind 50 time from virtio-pci to vfio-pci
        self.repeat_bind_driver(dut=self.vm_dut[0], repeat_times=50)
        self.repeat_bind_driver(dut=self.vm_dut[1], repeat_times=50)
        # start vm0 and vm1 testpmd
        self.start_vm_testpmd(pmd_session=self.vm0_pmd)
        self.start_vm_testpmd(pmd_session=self.vm1_pmd)
        after_bind = self.start_vms_testpmd_and_test(launch=False, quit_vm_testpmd=False)

        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost_user.send_expect("^C", "# ", 20)

        self.table_header = ['Frame Size(Byte)', 'Before/After Bind VM Driver', 'Throughput(Mpps)']
        self.result_table_create(self.table_header)
        for key in before_rebind.keys():
            perf_result.append([key, 'Before rebind driver', before_rebind[key]])
        for key in after_bind.keys():
            perf_result.append([key, 'After rebind driver', after_bind[key]])
        for table_row in perf_result:
            self.result_table_add(table_row)
        self.result_table_print()

    def close_all_session(self):
        if getattr(self, 'vhost_user', None):
            self.dut.close_session(self.vhost_user)
        if getattr(self, 'virtio-user0', None):
            self.dut.close_session(self.virtio_user0)
        if getattr(self, 'virtio-user1', None):
            self.dut.close_session(self.virtio_user1)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.bind_cbdma_device_to_kernel()
        self.close_all_session()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.set_max_queues(128)
        self.set_async_threshold(256)
        self.dut.build_install_dpdk(self.target)