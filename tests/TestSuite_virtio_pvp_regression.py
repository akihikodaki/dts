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

This suite capture regression issue:
cover 2 queues + reconnect + multi qemu version + multi-paths with virtio1.0 and virtio0.95
In this suite, the qemu will start as server mode, and qemu supports server mode starting with version 2.7

Can config the qemu version in config file like:
qemu =
    path=qemu-2.7/bin/qemu-system-x86_64;
    path=qemu-2.8/bin/qemu-system-x86_64;
"""
import re
import time
import utils
from test_case import TestCase
from settings import HEADER_SIZE
from virt_common import VM
from pktgen import PacketGeneratorHelper


class TestVirtioPVPRegression(TestCase):
    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.pf = self.dut_ports[0]
        # Get the port's socket
        netdev = self.dut.ports_info[self.pf]['port']
        self.socket = netdev.get_nic_socket()
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.socket)

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(len(self.cores) >= 3,
                    "There has not enought cores to test this suite")
        self.coremask = utils.create_mask(self.cores)
        self.memory_channel = self.dut.get_memory_channels()
        self.port_number = 2
        self.queues_number = 2
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.vm_dut = None
        self.packet_params_set()

        self.logger.info("You can config all the path of qemu version you want to" + \
                        " tested in the conf file %s.cfg" % self.suite_name)
        self.logger.info("You can config packet_size in file %s.cfg," % self.suite_name + \
                        " in region 'suite' like packet_sizes=[64, 128, 256]")
        # check the qemu version config in cfg file
        res = self.verify_qemu_version_config()
        self.verify(res is True, "The path of qemu version in config file not right")

        if len(set([int(core['socket']) for core in self.dut.cores])) == 1:
            self.socket_mem = '1024'
        else:
            self.socket_mem = '1024,1024'

        # the path of pcap file
        self.out_path = '/tmp/%s' % self.suite_name
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
        self.vhost = self.dut.new_session(suite="vhost-user")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def packet_params_set(self):
        self.frame_sizes = [64, 1518]
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.virtio1_mac = "52:54:00:00:00:01"
        self.src1 = "192.168.4.1"
        self.header_row = ["case_info", "QemuVersion", "FrameSize(B)",
                        "Throughput(Mpps)", "LineRate(%)", "Queue Number",
                        "Cycle"]

    def get_qemu_list_from_config(self):
        """
        get the config of qemu path in vm params
        """
        config_qemu = False
        params_num = len(self.vm.params)
        for qemu_index in range(params_num):
            if list(self.vm.params[qemu_index].keys())[0] == "qemu":
                qemu_num = len(self.vm.params[qemu_index]["qemu"])
                config_qemu = True
                break
        self.verify(config_qemu is True,
                "Please config qemu path which you want to test in conf file")
        self.qemu_pos = qemu_index
        self.qemu_list = self.vm.params[qemu_index]["qemu"]

    def verify_qemu_version_config(self):
        """
        verify the config has config right qemu version
        """
        self.vm = VM(self.dut, 'vm0', self.suite_name)
        self.vm.load_config()
        # get qemu version list from config file
        self.get_qemu_list_from_config()
        qemu_num = len(self.qemu_list)
        for i in range(qemu_num):
            qemu_path = self.qemu_list[i]["path"]

            out = self.dut.send_expect("ls %s" % qemu_path, "#")
            if 'No such file or directory' in out:
                self.logger.error("No emulator [ %s ] on the DUT [ %s ]" %
                                (qemu_path, self.dut.get_ip_address()))
                return False
            out = self.dut.send_expect("[ -x %s ];echo $?" % qemu_path, '# ')
            if out != '0':
                self.logger.error("Emulator [ %s ] not executable on the DUT [ %s ]" %
                                (qemu_path, self.dut.get_ip_address()))
                return False

            out = self.dut.send_expect("%s --version" % qemu_path, "#")
            result = re.search("QEMU\s*emulator\s*version\s*(\d*.\d*)", out)
            version = result.group(1)

            # verify the qemu version is greater or equal to 2.7
            index = version.find('.')
            self.verify(int(version[:index]) > 2 or (int(version[:index]) == 2
                        and int(version[index+1:]) >= 7),
                        'This qemu version should greater than 2.7 ' + \
                        'in this suite, please config it in %s.cfg file' % self.suite_name)
            # update the version info to self.qemu_list
            self.qemu_list[i].update({"version": "qemu-%s" % version})

        # print all the qemu version you config
        config_qemu_version = ""
        for i in range(len(self.qemu_list)):
            config_qemu_version += self.qemu_list[i]["version"] + " "
        self.logger.info("The suite will test the qemu version of: %s" % config_qemu_version)

        return True

    def rm_vm_qemu_path_config(self):
        """
        According it has config all qemu path, so pop the qemu path info in params
        when start the vm set the qemu path info
        """
        params_num = len(self.vm.params)
        for qemu_index in range(params_num):
            if list(self.vm.params[qemu_index].keys())[0] == "qemu":
                qemu_num = len(self.vm.params[qemu_index]["qemu"])
                break
        self.verify(qemu_index < params_num, "Please config qemu path in conf gile")
        self.vm.params.pop(qemu_index)

    def rm_cpupin_info_from_config(self):
        """
        remove the cpupin param from vm_params
        when the cores in cpupin is the isolcpus, it will reduce the
        performance of pvp
        And if we not use the cpupin params(taskset -c xxx), it will use
        the cpu which not set in isolcpus, and it number equal to the vcpus
        """
        params_number = len(self.vm.params)
        for i in range(params_number):
            if list(self.vm.params[i].keys())[0] == 'cpu':
                if 'cpupin' in list(self.vm.params[i]['cpu'][0].keys()):
                    self.vm.params[i]['cpu'][0].pop('cpupin')

    def start_vm(self, qemu_path, qemu_version, modem, virtio_path):
        """
        start vm
        """
        self.vm = VM(self.dut, 'vm0', self.suite_name)
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = self.virtio1_mac
        vm_params['opt_server'] = 'server'
        vm_params['opt_queue'] = self.queues_number

        # if the qemu version greater or equal to 2.10, the args should add
        # 'rx_queue_size=1024,tx_queue_size=1024'
        opt_args = 'mq=on,vectors=15'
        version = qemu_version[qemu_version.find('-')+1:]
        index = version.find('.')
        if (int(version[:index]) > 2 or int(version[index+1:]) >= 10):
            opt_args = 'rx_queue_size=1024,tx_queue_size=1024,' + opt_args

        if virtio_path == 'mergeable':
            opt_args = 'mrg_rxbuf=on,' + opt_args
        else:
            opt_args = 'mrg_rxbuf=off,' + opt_args

        if modem == 1:
            opt_args = 'disable-modern=false,' + opt_args
        elif(modem == 0):
            opt_args = 'disable-modern=true,' + opt_args
        vm_params['opt_settings'] = opt_args
        self.vm.set_vm_device(**vm_params)
        self.vm.load_config()
        self.rm_vm_qemu_path_config()
        self.rm_cpupin_info_from_config()
        # set qemu version info
        self.vm.set_qemu_emulator(qemu_path)
        # Due to we have change the params info before,
        # so need to start vm with load_config=False
        try:
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def start_testpmd_as_vhost(self):
        """
        Launch the vhost testpmd
        """
        command_line_client = self.dut.target + "/app/testpmd -n %d -c %s \
            --socket-mem %s --file-prefix=vhost -w %s \
            --vdev 'eth_vhost0,iface=%s/vhost-net,queues=%d,client=1' -- \
            -i --nb-cores=%d --rxq=%d --txq=%d  --txd=1024 --rxd=1024"
        command_line_client = command_line_client % (
                        self.memory_channel, self.coremask, self.socket_mem,
                        self.dut.ports_info[self.pf]['pci'], self.base_dir,
                        self.queues_number, self.queues_number, self.queues_number,
                        self.queues_number)
        self.vhost.send_expect(command_line_client, "testpmd> ", 30)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def start_testpmd_in_vm(self, vritio_path):
        """
        Start testpmd in vm
        """
        self.verify(len(self.vm_dut.cores) >= 3,
                'The vm does not have enough core to start testpmd, ' \
                'please config it in %s.cfg' % self.suite_name)
        if self.vm_dut is not None:
            opt_args = ''
            if vritio_path in ['mergeable', 'normal']:
                opt_args = '--enable-hw-vlan-strip'
            vm_testpmd = self.dut.target + "/app/testpmd -c 0x7 -n 4 " \
                "-- -i %s --nb-cores=%s " \
                "--rxq=%s --txq=%s --txd=1024 --rxd=1024"
            vm_testpmd = vm_testpmd % (opt_args, self.queues_number,
                        self.queues_number, self.queues_number)
            self.vm_dut.send_expect(vm_testpmd, "testpmd> ", 20)
            self.vm_dut.send_expect("set fwd mac", "testpmd> ", 20)
            self.vm_dut.send_expect("start", "testpmd> ")

    def check_packets_of_each_queue(self, frame_size):
        """
        check each queue has receive packets
        """
        out = self.vhost.send_expect("stop", "testpmd> ", 60)
        print(out)
        for port_index in range(0, self.port_number):
            for queue_index in range(0, self.queues_number):
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

    def send_verify(self, case_info, qemu_version, tag):
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            payload = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip']
            flow = '[Ether(dst="%s")/IP(src="%s")/("X"*%d)]' % (
                self.dst_mac, self.src1, payload)
            self.tester.scapy_append('wrpcap("%s/pvp_diff_qemu_version.pcap", %s)' % (
                                self.out_path, flow))
            self.tester.scapy_execute()

            tgenInput = []
            port = self.tester.get_local_port(self.pf)
            tgenInput.append((port, port, "%s/pvp_diff_qemu_version.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            fields_config = {'ip':  {'dst': {'range': 127, 'step': 1, 'action': 'random'}, }, }
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100,
                                                fields_config, self.tester.pktgen)
            # set traffic option
            traffic_opt = {'delay': 5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            Mpps = pps / 1000000.0
            pct = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            self.verify(Mpps != 0, "can not received data of frame size %d" % frame_size)
            # check each queue has data
            self.check_packets_of_each_queue(frame_size)
            # update print table info
            data_row = [case_info, qemu_version, frame_size, str(Mpps),
                        str(pct), self.queues_number, tag]
            self.result_table_add(data_row)

    def close_testpmd_and_qemu(self):
        """
        stop testpmd in vhost and qemu
        close the qemu
        """
        self.vm_dut.send_expect("quit", "#", 20)
        self.vhost.send_expect("quit", "#", 20)
        self.vm.stop()
        self.dut.send_expect("killall -I testpmd", '#', 20)
        self.dut.send_expect('killall -s INT qemu-system-x86_64', '# ')
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def pvp_regression_run(self, case_info, modem, virtio_path):
        """
        run different qemu verssion on different virtio path of pvp regression
        modem = 0, start vm as virtio 0.95
        modem = 1, start vm as virtio 1.0
        virtio_path = mergeable/normal/vector_rx
        """
        for i in range(len(self.qemu_list)):
            self.result_table_create(self.header_row)
            path = self.qemu_list[i]["path"]
            version = self.qemu_list[i]["version"]
            self.start_testpmd_as_vhost()
            # use different modem and different path to start vm
            self.start_vm(path, version, modem, virtio_path)
            self.start_testpmd_in_vm(virtio_path)
            self.logger.info("now testing the qemu path of %s" % path)
            time.sleep(5)
            self.send_verify(case_info, version, "before reconnect")

            self.logger.info('now reconnect from vhost')
            self.dut.send_expect("killall -s INT testpmd", "# ")
            self.start_testpmd_as_vhost()
            self.send_verify(case_info, version, "reconnect from vhost")

            self.logger.info('now reconnect from vm')
            self.dut.send_expect('killall -s INT qemu-system-x86_64', '# ')
            self.start_vm(path, version, modem, virtio_path)
            self.start_testpmd_in_vm(virtio_path)
            self.send_verify(case_info, version, "reconnect from vm")

            self.result_table_print()
            self.close_testpmd_and_qemu()

    def test_perf_pvp_regression_with_mergeable_path(self):
        """
        Test the performance of one vm with virtio 0.95 on mergeable path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-0.95 mergeable'
        modem = 0
        virtio_path = 'mergeable'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def test_perf_pvp_regression_modern_mergeable_path(self):
        """
        Test the performance of one vm with virtio 1.0 on mergeable path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-1.0 mergeable'
        modem = 1
        virtio_path = 'mergeable'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def test_perf_pvp_regression_normal_path(self):
        """
        Test the performance of one vm with virtio 0.95 on normal path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-0.95 normal'
        modem = 0
        virtio_path = 'normal'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def test_perf_pvp_regression_modern_normal_path(self):
        """
        Test the performance of one vm with virtio 1.0 on normal path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-1.0 normal'
        modem = 1
        virtio_path = 'normal'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def test_perf_pvp_regression_vector_rx_path(self):
        """
        Test the performance of one vm with virtio 0.95 on vector_rx path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-0.95 vector_rx'
        modem = 0
        virtio_path = 'vector_rx'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def test_perf_pvp_regression_modern_vector_rx_path(self):
        """
        Test the performance of one vm with virtio 1.0 on vector_rx path
        diff qemu + multi queue + reconnect
        """
        case_info = 'virtio-1.0 normal'
        modem = 1
        virtio_path = 'vector_rx'
        self.pvp_regression_run(case_info, modem, virtio_path)

    def tear_down(self):
        """
        Run after each test case.
        Clear qemu and testpmd to avoid blocking the following TCs
        """
        self.dut.close_session(self.vhost)
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
