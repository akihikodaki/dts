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

Vhost PVP performance using differnet Qemu test suite.
Can config the qemu version in config file like:
qemu =
    path=qemu-2.5/bin/qemu-system-x86_64;
    path=qemu-2.6/bin/qemu-system-x86_64;
"""
import re
import time
import utils
from scapy.utils import wrpcap
from test_case import TestCase
from settings import HEADER_SIZE
from virt_common import VM
from pktgen import PacketGeneratorHelper


class TestVhostPVPDiffQemuVersion(TestCase):
    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.pf = self.dut_ports[0]
        # Get the port's socket
        netdev = self.dut.ports_info[self.pf]['port']
        self.socket = netdev.get_nic_socket()
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                        == self.socket])

        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(self.cores_num >= 3,
                    "There has not enought cores to test this suite")
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.socket)
        self.coremask = utils.create_mask(self.cores)
        self.memory_channel = 4
        self.vm_dut = None
        self.packet_params_set()

        self.logger.info("You can config all the path of qemu version you want to" + \
                        " tested in the conf file %s.cfg" % self.suite_name)
        self.logger.info("You can config packet_size in file %s.cfg," % self.suite_name + \
                        " in region 'suite' like packet_sizes=[64, 128, 256]")
        res = self.verify_qemu_version_config()
        self.verify(res is True, "The path of qemu version in config file not right")

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
        self.vhost = self.dut.new_session(suite="vhost-user")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -I qemu-system-x86_64", '#', 20)

    def packet_params_set(self):
        self.frame_sizes = [64, 128, 256, 512, 1024, 1500]
        # get the frame_sizes from cfg file
        if 'packet_sizes' in self.get_suite_cfg():
            self.frame_sizes = self.get_suite_cfg()['packet_sizes']

        self.virtio1_mac = "52:54:00:00:00:01"
        self.src1 = "192.168.4.1"
        self.dst1 = "192.168.3.1"
        self.header_row = ["QemuVersion", "FrameSize(B)", "Throughput(Mpps)",
                           "LineRate(%)", "Cycle"]

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
                "Please config qemu path which you want to test in conf gile")
        self.qemu_pos = qemu_index
        self.qemu_list = self.vm.params[qemu_index]["qemu"]

    def verify_qemu_version_config(self):
        """
        verify the config has config enough qemu version
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

    def start_vm(self, path, modem):
        """
        start vm
        """
        self.vm = VM(self.dut, 'vm0', 'pvp_diff_qemu_version')
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = self.virtio1_mac
        if(modem == 1):
            vm_params['opt_settings'] = "disable-modern=false,mrg_rxbuf=on"
        elif(modem == 0):
            vm_params['opt_settings'] = "disable-modern=true,mrg_rxbuf=on"
        self.vm.set_vm_device(**vm_params)
        self.vm.load_config()
        self.rm_vm_qemu_path_config()
        # set qemu version info
        self.vm.set_qemu_emulator(path)
        # Due to we have change the params info before,
        # so need to start vm with load_config=False
        try:
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def start_vhost_testpmd(self):
        """
        Launch the vhost testpmd
        """
        command_line_client = self.dut.target + "/app/testpmd -n %d -c %s \
            --socket-mem 1024,1024 --file-prefix=vhost \
            --vdev 'eth_vhost0,iface=%s/vhost-net,queues=1' -- \
            -i --nb-cores=1 --txd=1024 --rxd=1024"
        command_line_client = command_line_client % (
                              self.memory_channel, self.coremask, self.base_dir)
        self.vhost.send_expect(command_line_client, "testpmd> ", 30)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def vm_testpmd_start(self):
        """
        Start testpmd in vm
        """
        if self.vm_dut is not None:
            vm_testpmd = self.dut.target + "/app/testpmd -c 0x3 -n 3" \
                + " -- -i --nb-cores=1 --txd=1024 --rxd=1024"
            self.vm_dut.send_expect(vm_testpmd, "testpmd> ", 20)
            self.vm_dut.send_expect("set fwd mac", "testpmd> ", 20)
            self.vm_dut.send_expect("start", "testpmd> ")

    def send_verify(self, qemu_version, vlan_id1=0, tag="Performance"):
        self.result_table_create(self.header_row)
        for frame_size in self.frame_sizes:
            info = "Running test %s, and %d frame size." % (self.running_case, frame_size)
            self.logger.info(info)
            payload = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip']
            flow = '[Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="%s",dst="%s")/("X"*%d)]' % (
                self.virtio1_mac, vlan_id1, self.src1, self.dst1, payload)
            self.tester.scapy_append('wrpcap("%s/pvp_diff_qemu_version.pcap", %s)' % (
                                self.out_path, flow))
            self.tester.scapy_execute()

            tgenInput = []
            port = self.tester.get_local_port(self.pf)
            tgenInput.append((port, port, "%s/pvp_diff_qemu_version.pcap" % self.out_path))

            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, None, self.tester.pktgen)
            # set traffic option
            traffic_opt = {'delay': 5, 'duration': 20}
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)
            Mpps = pps / 1000000.0
            pct = Mpps * 100 / float(self.wirespeed(self.nic, frame_size, 1))
            self.verify(Mpps != 0, "can not received data of frame size %d" % frame_size)
            # update print table info
            data_row = [qemu_version, frame_size, str(Mpps), str(pct), tag]
            self.result_table_add(data_row)

        self.result_table_print()

    def close_testpmd_and_qemu(self):
        """
        stop testpmd in vhost and qemu
        close the qemu
        """
        self.vm_dut.send_expect("quit", "#", 20)
        self.vhost.send_expect("quit", "#", 20)
        self.vm.stop()
        self.dut.send_expect("killall -I testpmd", '#', 20)
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    def test_perf_vhost_pvp_diffrent_qemu_version_mergeable_mac(self):
        """
        Test the performance of one vm with virtio 0.95 on mergeable path
        """
        for i in range(len(self.qemu_list)):
            path = self.qemu_list[i]["path"]
            version = self.qemu_list[i]["version"]
            self.start_vhost_testpmd()
            self.start_vm(path, 0)
            # Start testpmd in vm
            self.vm_testpmd_start()
            self.logger.info("now testing the qemu path of %s" % path)
            time.sleep(5)
            vlan_id1 = 1000
            self.send_verify(version, vlan_id1, "virtio-0.95, Mergeable")
            self.close_testpmd_and_qemu()

    def test_perf_vhost_pvp_diffrent_qemu_version_modern_mergeable_mac(self):
        """
        Test the performance of one vm with virtio 1.0 on mergeable path
        """
        for i in range(len(self.qemu_list)):
            path = self.qemu_list[i]["path"]
            version = self.qemu_list[i]["version"]
            self.start_vhost_testpmd()
            self.start_vm(path, 1)
            # Start testpmd in vm
            self.vm_testpmd_start()
            self.logger.info("now testing the qemu path of %s" % path)
            time.sleep(5)
            vlan_id1 = 1000
            self.send_verify(version, vlan_id1, "virtio-1.0, Mergeable")
            self.close_testpmd_and_qemu()

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
