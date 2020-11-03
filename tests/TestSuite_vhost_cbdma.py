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
We introduce a new vdev parameter to enable DMA acceleration for Tx
operations of queues:
 - dmas: This parameter is used to specify the assigned DMA device of
   a queue.
 - dmathr: If packets length >= dmathr, leverage I/OAT device to perform memory copy;
   otherwise, leverage librte_vhost to perform memory copy.

Here is an example:
 $ ./testpmd -c f -n 4 \
   --vdev 'net_vhost0,iface=/tmp/s0,queues=1,dmas=[txq0@80:04.0],dmathr=1024'
"""
import re
import time
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper
from pmd_output import PmdOutput


class TestVirTioVhostCbdma(TestCase):
    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.number_of_ports = 1

        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.pmdout_vhost_user = PmdOutput(self.dut, self.vhost_user)
        self.pmdout_virtio_user = PmdOutput(self.dut, self.virtio_user)
        self.frame_sizes = [64, 1518]
        self.virtio_mac = "00:01:02:03:04:05"
        self.headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip']
        self.pci_info = self.dut.ports_info[0]['pci']
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.socket)
        self.cbdma_dev_infos = []

        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.bind_nic_driver(self.dut_ports)
        # the path of pcap file
        self.out_path = '/tmp/%s' % self.suite_name
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        self.pktgen_helper = PacketGeneratorHelper()
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        """
        Run before each test case.
        """
        self.table_header = ['Frame']
        self.used_cbdma = []
        self.table_header.append("Mode")
        self.table_header.append("Mpps")
        self.table_header.append("% linerate")
        self.result_table_create(self.table_header)
        self.vhost = self.dut.new_session(suite="vhost-user")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("rm -rf /tmp/s0", "#")

    def bind_nic_driver(self, ports, driver=""):
        if driver == "igb_uio":
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'igb_uio':
                    netdev.bind_driver(driver='igb_uio')
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    def get_cbdma_ports_info_and_bind_to_dpdk(self, cbdma_num):
        """
        get all cbdma ports
        """

        out = self.dut.send_expect('./usertools/dpdk-devbind.py --status-dev misc', '# ', 30)
        device_info = out.split('\n')
        for device in device_info:
            pci_info = re.search('\s*(0000:\d*:\d*.\d*)', device)
            if pci_info is not None:
                dev_info = pci_info.group(1)
                # the numa id of ioat dev, only add the device which
                # on same socket with nic dev
                bus = int(dev_info[5:7], base=16)
                if bus >= 128:
                    cur_socket = 1
                else:
                    cur_socket = 0
                if self.ports_socket == cur_socket:
                    self.cbdma_dev_infos.append(pci_info.group(1))
        self.verify(len(self.cbdma_dev_infos) >= cbdma_num, 'There no enough cbdma device to run this suite')

        self.used_cbdma = self.cbdma_dev_infos[0:cbdma_num]

        self.device_str = ' '.join(self.used_cbdma)
        self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=%s %s %s' %
                             ("igb_uio", self.device_str, self.pci_info), '# ', 60)

    def bind_cbdma_device_to_kernel(self):
        if self.device_str is not None:
            self.dut.send_expect('modprobe ioatdma', '# ')
            self.dut.send_expect('./usertools/dpdk-devbind.py -u %s' % self.device_str, '# ', 30)
            self.dut.send_expect('./usertools/dpdk-devbind.py --force --bind=ioatdma  %s' % self.device_str,
                                 '# ', 60)

    @property
    def check_2m_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def launch_testpmd_as_vhost_user(self, command, cores="Default", dev=""):
        self.pmdout_vhost_user.start_testpmd(cores=cores, param=command, vdevs=[dev], ports=[],

                                             prefix="vhost", fixed_prefix=True)

        self.vhost_user.send_expect('set fwd mac', 'testpmd> ', 120)
        self.vhost_user.send_expect('start', 'testpmd> ', 120)

    def launch_testpmd_as_virtio_user(self, command, cores="Default", dev=""):
        eal_params = ""
        if self.check_2m_env:
            eal_params += " --single-file-segments"
        self.pmdout_virtio_user.start_testpmd(cores, command, vdevs=[dev], ports=[], no_pci=True,
                                              prefix="virtio", fixed_prefix=True, eal_param=eal_params)

        self.virtio_user.send_expect('set fwd mac', 'testpmd> ', 120)
        self.virtio_user.send_expect('start', 'testpmd> ', 120)

    def diff_param_launch_send_and_verify(self, mode, params, dev, cores, is_quit=True):
        self.launch_testpmd_as_virtio_user(params,
                                           cores,
                                           dev=dev)

        self.send_and_verify(mode)
        if is_quit:
            self.virtio_user.send_expect("quit", "# ")
            time.sleep(3)

    def test_perf_pvp_spilt_all_path_with_cbdma_vhost_enqueue_operations(self):
        """
        used one cbdma port  bonding igb_uio
        :return:
        """
        txd_rxd = 1024
        dmathr = 1024
        eal_tx_rxd = ' --nb-cores=%d --txd=%d --rxd=%d'
        queue = 1
        used_cbdma_num = 1
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        vhost_vdevs = f"'net_vhost0,iface=/tmp/s0,queues=%d,dmas=[txq0@{self.device_str}],dmathr=%d'"
        dev_path_mode_mapper = {
            "inorder_mergeable_path": 'mrg_rxbuf=1,in_order=1',
            "mergeable_path": 'mrg_rxbuf=1,in_order=0',
            "inorder_non_mergeable_path": 'mrg_rxbuf=0,in_order=1',
            "non_mergeable_path": 'mrg_rxbuf=0,in_order=0',
            "vector_rx_path": 'mrg_rxbuf=0,in_order=0',
        }

        pvp_split_all_path_virtio_params = "--tx-offloads=0x0 --enable-hw-vlan-strip --nb-cores=%d --txd=%d " \
                                           "--rxd=%d" % (queue, txd_rxd, txd_rxd)
        self.launch_testpmd_as_vhost_user(eal_tx_rxd % (queue, txd_rxd, txd_rxd), self.cores[0:2],
                                          dev=vhost_vdevs % (queue, dmathr), )

        for key, path_mode in dev_path_mode_mapper.items():
            if key == "vector_rx_path":
                pvp_split_all_path_virtio_params = eal_tx_rxd % (
                    queue, txd_rxd, txd_rxd)
            vdevs = f"'net_virtio_user0,mac={self.virtio_mac},path=/tmp/s0,{path_mode},queues=%d'" % queue
            self.diff_param_launch_send_and_verify(key, pvp_split_all_path_virtio_params, vdevs,
                                                   self.cores[2:4],
                                                   )
        self.result_table_print()

    def test_perf_dynamic_queue_number_cbdma_vhost_enqueue_operations(self):
        """
        # used 2 cbdma ports  bonding igb_uio
        :return:
        """
        used_cbdma_num = 2
        queue = 2
        txd_rxd = 1024
        dmathr = 1024
        nb_cores = 1
        virtio_path = "/tmp/s0"
        path_mode = 'mrg_rxbuf=1,in_order=1'
        self.get_cbdma_ports_info_and_bind_to_dpdk(used_cbdma_num)
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]};txq1@{self.used_cbdma[1]}],dmathr={dmathr}"

        eal_params = " --nb-cores=%d --txd=%d --rxd=%d --txq=%d --rxq=%d " % (nb_cores, txd_rxd, txd_rxd, queue, queue)

        dynamic_queue_number_cbdma_virtio_params = f"  --tx-offloads=0x0 --enable-hw-vlan-strip {eal_params}"

        virtio_dev = f"net_virtio_user0,mac={self.virtio_mac},path={virtio_path},{path_mode},queues={queue},server=1"
        vhost_dev = f"'net_vhost0,iface={virtio_path},queues={queue},client=1,%s'"

        # launch vhost testpmd
        self.launch_testpmd_as_vhost_user(eal_params, self.cores[0:2],
                                          dev=vhost_dev % vhost_dmas)
        #
        #  queue 2 start virtio testpmd,virtio queue 2 to 1
        mode = "dynamic_queue2"
        self.launch_testpmd_as_virtio_user(dynamic_queue_number_cbdma_virtio_params,
                                           self.cores[2:4],
                                           dev=virtio_dev)
        self.send_and_verify(mode)
        self.vhost_or_virtio_set_one_queue(self.virtio_user)
        self.send_and_verify("virtio_user_" + mode + "_change_to_1", multiple_queue=False)

        self.virtio_user.send_expect("stop", "testpmd> ")
        self.virtio_user.send_expect("quit", "# ")
        time.sleep(5)
        self.dut.send_expect(f"rm -rf {virtio_path}", "#")
        # queue 2 start virtio testpmd,vhost queue 2 to 1
        self.launch_testpmd_as_virtio_user(dynamic_queue_number_cbdma_virtio_params,
                                           self.cores[2:4],
                                           dev=virtio_dev)
        mode = "Relaunch_dynamic_queue2"
        self.send_and_verify(mode)
        self.vhost_or_virtio_set_one_queue(self.vhost_user)
        self.send_and_verify("vhost_user" + mode + "_change_to_1")
        self.vhost_user.send_expect("quit", "# ")
        time.sleep(2)

        # Relaunch vhost with another two cbdma channels
        mode = "Relaunch_vhost_2_cbdma"
        dmathr = 512
        vhost_dmas = f"dmas=[txq0@{self.used_cbdma[0]}],dmathr={dmathr}"
        self.launch_testpmd_as_vhost_user(eal_params, self.cores[0:2],
                                          dev=vhost_dev % vhost_dmas)
        self.send_and_verify(mode)
        self.virtio_user.send_expect("quit", "# ")
        self.vhost_user.send_expect("quit", "# ")
        time.sleep(2)
        self.result_table_print()

    @staticmethod
    def vhost_or_virtio_set_one_queue(session):
        session.send_expect('start', 'testpmd> ', 120)
        session.send_expect('stop', 'testpmd> ', 120)
        session.send_expect('port stop all', 'testpmd> ', 120)
        session.send_expect('port config all rxq 1', 'testpmd> ', 120)
        session.send_expect('port start all', 'testpmd> ', 120)
        session.send_expect('start', 'testpmd> ', 120)
        time.sleep(5)

    @property
    def check_value(self):
        check_dict = dict.fromkeys(self.frame_sizes)
        linerate = {64: 0.085, 128: 0.12, 256: 0.20, 512: 0.35, 1024: 0.50, 1280: 0.55, 1518: 0.60}
        for size in self.frame_sizes:
            speed = self.wirespeed(self.nic, size, self.number_of_ports)
            check_dict[size] = round(speed * linerate[size], 2)
        return check_dict

    def send_and_verify(self, mode, multiple_queue=True):
        """
        Send packet with packet generator and verify
        """
        for frame_size in self.frame_sizes:
            payload_size = frame_size - self.headers_size
            tgen_input = []
            rx_port = self.tester.get_local_port(self.dut_ports[0])
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            ip_src = 'src=RandIP()'
            if not multiple_queue:
                ip_src = ""

            pacp = 'wrpcap("%s/vhost.pcap", [Ether(dst="%s")/IP(%s)/("X"*%d)])' \
                   % (self.out_path, self.virtio_mac, ip_src, payload_size)
            self.tester.scapy_append(pacp)
            tgen_input.append((tx_port, rx_port, "%s/vhost.pcap" % self.out_path))

            self.tester.scapy_execute()
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                                                     None, self.tester.pktgen)
            trans_options = {'delay': 5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=trans_options)
            Mpps = pps / 1000000.0
            self.verify(Mpps > 0,
                        "%s can not receive packets of frame size %d" % (self.running_case, frame_size))
            throughput = Mpps * 100 / \
                         float(self.wirespeed(self.nic, frame_size, 1))

            results_row = [frame_size]
            results_row.append(mode)
            results_row.append(Mpps)
            results_row.append(throughput)
            self.result_table_add(results_row)

    def tear_down(self):
        """
        Run after each test case.
        Clear qemu and testpmd to avoid blocking the following TCs
        """
        self.bind_cbdma_device_to_kernel()
        self.bind_nic_driver(self.dut_ports)

    def tear_down_all(self):
        """
        Run after each test suite.
        """

        self.bind_nic_driver(self.dut_ports, self.drivername)
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user)

