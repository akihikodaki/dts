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
vhost virtio pmd interrupt need test with l3fwd-power sample
"""

import utils
import time
from virt_common import VM
from test_case import TestCase
from etgen import IxiaPacketGenerator


class TestVhostVirtioPmdInterrupt(TestCase, IxiaPacketGenerator):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVhostVirtioPmdInterrupt, self)
        self.fix_ip = False
        self.nb_cores = 4
        self.queues = 4
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) ==
                        self.ports_socket])
        self.mem_channels = self.dut.get_memory_channels()
        self.tx_port = self.tester.get_local_port(self.dut_ports[0])
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.logger.info("Please comfirm the kernel of vm greater than 4.8.0 "
                        "and enable vfio-noiommu in kernel")

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.vm_dut = None

    def ip(self, port, frag, src, proto, tos, dst, chksum, len,
                            options, version, flags, ihl, ttl, id):
        """
        Configure IP protocol.
        """
        self.add_tcl_cmd("protocol config -name ip")
        self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
        if self.fix_ip is False:
            self.add_tcl_cmd('ip config -destIpAddrMode ipRandom')
        else:
            self.add_tcl_cmd('ip config -destIpAddr "%s"' % dst)
        self.add_tcl_cmd("ip config -ttl %d" % ttl)
        self.add_tcl_cmd("ip config -totalLength %d" % len)
        self.add_tcl_cmd("ip config -fragment %d" % frag)
        self.add_tcl_cmd("ip config -ipProtocol %d" % proto)
        self.add_tcl_cmd("ip config -identifier %d" % id)
        self.add_tcl_cmd("stream config -framesize %d" % (len + 18))
        self.add_tcl_cmd("ip set %d %d %d" % (self.chasId, port['card'], port['port']))

    def get_core_list(self):
        """
        get core list about testpmd
        """
        core_config = "1S/%dC/1T" % (self.nb_cores + 1)
        self.verify(self.cores_num >= (self.nb_cores + 1),
                    "There has not enough cores to running case: %s" %
                    self.running_case)
        self.core_list = self.dut.get_core_list(core_config,
                                    socket=self.ports_socket)
        self.core_mask = utils.create_mask(self.core_list)

    def prepare_vm_env(self):
        """
        rebuild l3fwd-power in vm and set the virtio-net driver
        """
        self.vm_dut.send_expect("cp ./examples/l3fwd-power/main.c /tmp/", "#")
        self.vm_dut.send_expect(
                "sed -i '/DEV_RX_OFFLOAD_CHECKSUM/d' ./examples/l3fwd-power/main.c", "#", 10)
        out = self.vm_dut.build_dpdk_apps('examples/l3fwd-power')
        self.verify("Error" not in out, "compilation l3fwd-power error")

        self.vm_dut.send_expect("modprobe vfio enable_unsafe_noiommu_mode=1", "#")
        self.vm_dut.send_expect("modprobe vfio-pci", "#")
        self.vm_dut.ports_info[0]['port'].bind_driver('vfio-pci')

    def start_testpmd_on_vhost(self):
        """
        start testpmd on vhost side
        """
        # get the core list depend on current nb_cores number
        self.get_core_list()

        command_client = self.dut.target + "/app/testpmd -c %s -n %d " + \
                        "--socket-mem 1024,1024 --legacy-mem " + \
                        "--vdev 'net_vhost0,iface=vhost-net,queues=%d' " + \
                        "-- -i --nb-cores=%d --rxq=%d --txq=%d --rss-ip"
        command_line_client = command_client % (
                        self.core_mask, self.mem_channels,
                        self.queues, self.nb_cores, self.queues, self.queues)
        self.vhost_user.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def launch_l3fwd_power_in_vm(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        self.verify(len(self.vm_dut.cores) >= self.nb_cores,
                "The vm done not has enought cores to use, please config it")
        core_config = "1S/%dC/1T" % self.nb_cores
        core_list_l3fwd = self.vm_dut.get_core_list(core_config)
        core_mask_l3fwd = utils.create_mask(core_list_l3fwd)

        res = True
        self.logger.info("Launch l3fwd_sample sample:")
        config_info = ""
        for queue in range(self.queues):
            if config_info != "":
                config_info += ','
            config_info += '(%d,%d,%s)' % (0, queue, core_list_l3fwd[queue])
            info = {'core': core_list_l3fwd[queue], 'port': 0, 'queue': queue}
            self.verify_info.append(info)

        command_client = "./examples/l3fwd-power/build/app/l3fwd-power " + \
                         "-c %s -n 4 --log-level='user1,7' -- -p 1 -P " + \
                         "--config '%s' --no-numa  --parse-ptype "
        command_line_client = command_client % (core_mask_l3fwd, config_info)
        self.vm_dut.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vm_dut.get_session_output()
        if ("Error" in out and "Error opening" not in out):
            self.logger.error("Launch l3fwd-power sample error")
            res = False
        else:
            self.logger.info("Launch l3fwd-power sample finished")
        self.verify(res is True, "Lanuch l3fwd failed")

    def set_vm_vcpu_number(self):
        # config the vcpu numbers
        params_number = len(self.vm.params)
        for i in range(params_number):
            if self.vm.params[i].keys()[0] == 'cpu':
                self.vm.params[i]['cpu'][0]['number'] = self.queues

    def start_vms(self, mode=0):
        """
        start qemus
        """
        self.vm = VM(self.dut, 'vm0', self.suite_name)
        self.vm.load_config()
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = './vhost-net'
        vm_params['opt_mac'] = "00:11:22:33:44:55"
        vm_params['opt_queue'] = self.queues
        opt_param = "mrg_rxbuf=on,csum=on,mq=on,vectors=%d" % (2*self.queues+2)
        if mode == 0:
            vm_params['opt_settings'] = "disable-modern=true," + opt_param
        elif mode == 1:
            vm_params['opt_settings'] = "disable-modern=false," + opt_param
        self.vm.set_vm_device(**vm_params)
        self.set_vm_vcpu_number()
        try:
            # Due to we have change the params info before,
            # so need to start vm with load_config=False
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def check_related_cores_status_in_l3fwd(self, out_result, status, fix_ip):
        """
        check the vcpu status
        when tester send fix_ip packet, the cores in l3fwd only one can change the status
        when tester send not fix_ip packets, all the cores in l3fwd will change the status
        """
        change = 0
        for i in range(len(self.verify_info)):
            if status == "waked up":
                info = "lcore %s is waked up from rx interrupt on port %d queue %d"
                info = info % (self.verify_info[i]["core"], self.verify_info[i]['port'],
                                self.verify_info[i]['queue'])
            elif status == "sleeps":
                info = "lcore %s sleeps until interrupt triggers" % self.verify_info[i]["core"]
            if info in out_result:
                change = change + 1
                self.logger.info(info)
        # if use fix ip, only one cores can waked up/sleep
        # if use dynamic ip, all the cores will waked up/sleep
        if fix_ip is True:
            self.verify(change == 1, "There has other cores change the status")
        else:
            self.verify(change == self.queues,
                        "There has cores not change the status")

    def send_packets(self):
        tgen_input = []
        self.tester.scapy_append('a=[Ether(dst="%s")/IP(src="0.240.74.101",proto=255)/UDP()/("X"*18)]' % (self.dst_mac))
        self.tester.scapy_append('wrpcap("interrupt.pcap", a)')
        self.tester.scapy_execute()
        tgen_input.append((self.tx_port, self.tx_port, "interrupt.pcap"))
        _, pps = self.tester.traffic_generator_throughput(tgen_input)

    def send_and_verify(self):
        """
        start to send packets and check the cpu status
        stop to send packets and check the cpu status
        """
        # Send random dest ip address packets to host nic
        # packets will distribute to all queues
        self.fix_ip = False
        self.send_packets()
        out = self.vm_dut.get_session_output(timeout=5)
        self.check_related_cores_status_in_l3fwd(out, "waked up", fix_ip=False)
        self.check_related_cores_status_in_l3fwd(out, "sleeps", fix_ip=False)

        # Send fixed dest ip address packets to host nic
        # packets will distribute to 1 queue
        self.fix_ip = True
        self.send_packets()
        out = self.vm_dut.get_session_output(timeout=5)
        self.check_related_cores_status_in_l3fwd(out, "waked up", fix_ip=True)
        self.check_related_cores_status_in_l3fwd(out, "sleeps", fix_ip=True)

    def stop_all_apps(self):
        """
        close all vms
        """
        self.vm_dut.send_expect("^c", "#", 15)
        self.vm_dut.send_expect("cp /tmp/main.c ./examples/l3fwd-power/", "#", 15)
        out = self.vm_dut.build_dpdk_apps('examples/l3fwd-power')
        self.vm.stop()
        self.vhost_user.send_expect("quit", "#", 10)
        self.dut.close_session(self.vhost_user)

    def test_perf_virtio_pmd_interrupt_with_4queues(self):
        """
        wake up virtio_user 0.95 core with l3fwd-power sample
        """
        self.queues = 4
        self.nb_cores = 4
        self.start_testpmd_on_vhost()
        self.start_vms(mode=0)
        self.prepare_vm_env()
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def test_perf_virtio_pmd_interrupt_with_16queues(self):
        """
        wake up virtio_user 0.95 core with l3fwd-power sample
        """
        self.queues = 16
        self.nb_cores = 16
        self.start_testpmd_on_vhost()
        self.start_vms(mode=0)
        self.prepare_vm_env()
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def test_perf_virito10_pmd_interrupt_with_4queues(self):
        """
        wake up virtio_user 1.0 core with l3fwd-power sample
        """
        self.queues = 4
        self.nb_cores = 4
        self.start_testpmd_on_vhost()
        self.start_vms(mode=1)
        self.prepare_vm_env()
        self.launch_l3fwd_power_in_vm()
        self.send_and_verify()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_all_apps()
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
