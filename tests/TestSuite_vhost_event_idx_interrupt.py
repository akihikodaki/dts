# BSD LICENSE
#
# Copyright (c) <2019>, Intel Corporation.
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
Vhost event idx interrupt need test with l3fwd-power sample
"""

import utils
import time
from virt_common import VM
from test_case import TestCase


class TestVhostEventIdxInterrupt(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        """
        self.vm_num = 1
        self.queues = 1
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) == 0])
        self.prepare_l3fwd_power()

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.verify_info = []
        self.dut.send_expect("killall -s INT l3fwd-power", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.vhost = self.dut.new_session(suite="vhost-l3fwd")
        self.vm_dut = []
        self.vm = []

    def get_core_mask(self):
        self.core_config = "1S/%dC/1T" % (self.vm_num*self.queues)
        self.verify(self.cores_num >= self.queues*self.vm_num,
                    "There has not enought cores to test this case %s" %
                    self.running_case)
        self.core_list_l3fwd = self.dut.get_core_list(self.core_config)
        self.core_mask_l3fwd = utils.create_mask(self.core_list_l3fwd)

    def prepare_l3fwd_power(self):
        self.dut.send_expect("cp ./examples/l3fwd-power/main.c .", "#")
        self.dut.send_expect(
                "sed -i '/DEV_RX_OFFLOAD_CHECKSUM/d' ./examples/l3fwd-power/main.c", "#", 10)
        out = self.dut.send_expect("make -C examples/l3fwd-power", "#")
        self.verify("Error" not in out, "compilation l3fwd-power error")

    def lanuch_l3fwd_power(self):
        """
        launch l3fwd-power with a virtual vhost device
        """
        res = True
        self.logger.info("Launch l3fwd_sample sample:")
        config_info = ""
        core_index = 0
        # config the interrupt cores info
        for port in range(self.vm_num):
            for queue in range(self.queues):
                if config_info != "":
                    config_info += ','
                config_info += '(%d,%d,%s)' % (port, queue, self.core_list_l3fwd[core_index])
                info = {'core': self.core_list_l3fwd[core_index], 'port': port, 'queue': queue}
                self.verify_info.append(info)
                core_index = core_index + 1
        # config the vdev info, if have 2 vms, it shoule have 2 vdev info
        vdev_info = ""
        for i in range(self.vm_num):
            vdev_info += "--vdev 'net_vhost%d,iface=vhost-net%d,queues=%d,client=1' " % (i, i, self.queues)

        port_info = "0x1" if self.vm_num == 1 else "0x3"

        command_client = "./examples/l3fwd-power/build/app/l3fwd-power " + \
                         "-c %s -n %d --socket-mem 1024,1024 --legacy-mem --no-pci " + \
                         "--log-level=9 %s -- -p %s --parse-ptype 1 --config '%s' "
        command_line_client = command_client % (
                        self.core_mask_l3fwd, self.dut.get_memory_channels(),
                        vdev_info, port_info, config_info)
        self.vhost.send_expect(command_line_client, "POWER", 40)
        time.sleep(10)
        out = self.vhost.get_session_before()
        if ("Error" in out and "Error opening" not in out):
            self.logger.error("Launch l3fwd-power sample error")
            res = False
        else:
            self.logger.info("Launch l3fwd-power sample finished")
        self.verify(res is True, "Lanuch l3fwd failed")

    def relanuch_l3fwd_power(self):
        """
        relauch l3fwd-power sample for port up
        """
        self.dut.send_expect("killall -s INT l3fwd-power", "#")
        self.lanuch_l3fwd_power()

    def set_vm_cpu_number(self, vm_config):
        # config the vcpu numbers when queue number greater than 1
        if self.queues == 1:
            return
        params_number = len(vm_config.params)
        for i in range(params_number):
            if vm_config.params[i].keys()[0] == 'cpu':
                vm_config.params[i]['cpu'][0]['number'] = self.queues

    def start_vms(self, vm_num=1):
        """
        start qemus
        """
        for i in range(vm_num):
            vm_info = VM(self.dut, 'vm%d' % i, 'vhost_sample')
            vm_info.load_config()
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = './vhost-net%d' % i
            vm_params['opt_mac'] = "00:11:22:33:44:5%d" % i
            vm_params['opt_server'] = 'server'
            if self.queues > 1:
                vm_params['opt_queue'] = self.queues
                opt_args = "csum=on,mq=on,vectors=%d" % (2*self.queues + 2)
            else:
                opt_args = "csum=on"
            vm_params['opt_settings'] = opt_args
            vm_info.set_vm_device(**vm_params)
            self.set_vm_cpu_number(vm_info)
            vm_dut = None
            try:
                vm_dut = vm_info.start(load_config=False)
                if vm_dut is None:
                    raise Exception("Set up VM ENV failed")
            except Exception as e:
                self.logger.error("ERROR: Failure for %s" % str(e))
            vm_dut.restore_interfaces()
            self.vm_dut.append(vm_dut)
            self.vm.append(vm_info)

    def config_virito_net_in_vm(self):
        """
        set vitio-net with 2 quques enable
        """
        for i in range(len(self.vm_dut)):
            vm_intf = self.vm_dut[i].ports_info[0]['intf']
            self.vm_dut[i].send_expect("ethtool -L %s combined %d" % (vm_intf, self.queues), "#", 20)

    def check_vhost_core_status(self, vm_index, status):
        """
        check the cpu status
        """
        out = self.vhost.get_session_before()
        for i in range(self.queues):
            # because of the verify_info include all config(vm0 and vm1)
            # so current index shoule vm_index + queue_index
            verify_index = i + vm_index
            if status == "waked up":
                info = "lcore %s is waked up from rx interrupt on port %d queue %d"
                info = info % (self.verify_info[verify_index]["core"], self.verify_info[verify_index]['port'],
                                self.verify_info[verify_index]['queue'])
            elif status == "sleeps":
                info = "lcore %s sleeps until interrupt triggers" % self.verify_info[verify_index]["core"]
            self.logger.info(info)
            self.verify(info in out, "The CPU status not right for %s" % info)

    def send_and_verify(self):
        """
        start to send packets and check the cpu status
        stop and restart to send packets and check the cpu status
        """
        ping_ip = 3
        for vm_index in range(self.vm_num):
            session_info = []
            vm_intf = self.vm_dut[vm_index].ports_info[0]['intf']
            self.vm_dut[vm_index].send_expect("ifconfig %s 1.1.1.%d" % (vm_intf, ping_ip), "#")
            ping_ip = ping_ip + 1
            self.vm_dut[vm_index].send_expect("ifconfig %s up" % vm_intf, "#")
            for queue in range(self.queues):
                session = self.vm_dut[vm_index].new_session(suite="ping_info_%d" % queue)
                session.send_expect("taskset -c %d ping 1.1.1.%d" %
                                    (queue, ping_ip), "PING", 30)
                session_info.append(session)
                ping_ip = ping_ip + 1
            time.sleep(3)
            self.check_vhost_core_status(vm_index=vm_index, status="waked up")
            # close all sessions of ping in vm
            for sess_index in range(len(session_info)):
                session_info[sess_index].send_expect("^c", "#")
                self.vm_dut[vm_index].close_session(session_info[sess_index])

    def stop_all_apps(self):
        """
        close all vms
        """
        for i in range(len(self.vm)):
            self.vm[i].stop()
        self.vhost.send_expect("^c", "#", 10)

    def test_vhost_idx_interrupt(self):
        """
        wake up vhost-user core with l3fwd-power sample
        """
        self.vm_num = 1
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def test_vhost_idx_interrupt_with_multi_queue(self):
        """
        wake up vhost-user core with l3fwd-power sample when multi queues are enabled
        """
        self.vm_num = 1
        self.queues = 16
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.config_virito_net_in_vm()
        self.send_and_verify()
        self.stop_all_apps()

    def test_vhost_idx_interrupt_with_multi_vms(self):
        """
        wake up vhost-user cores with l3fwd-power sample and multi VMs
        """
        self.vm_num = 2
        self.queues = 1
        self.get_core_mask()
        self.lanuch_l3fwd_power()
        self.start_vms(vm_num=self.vm_num)
        self.relanuch_l3fwd_power()
        self.send_and_verify()
        self.stop_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.close_session(self.vhost)
        self.dut.send_expect("killall -s INT l3fwd-power", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("mv ./main.c ./examples/l3fwd-power/", "#")
        self.dut.build_dpdk_apps('examples/l3fwd-power')
