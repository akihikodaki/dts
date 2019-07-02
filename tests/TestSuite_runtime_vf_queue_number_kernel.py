# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
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
runtime_vf_queue_number_kernel test script.
"""

import random
import time

import utils
from pmd_output import PmdOutput
from test_case import TestCase
from virt_common import VM

VM_CORES_MASK = 'all'


class TestRuntimeVfQueueNumberKernel(TestCase):
    supported_vf_driver = ['pci-stub', 'vfio-pci']
    max_queue = 16

    def set_up_all(self):
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "fortville_25g", "fortville_spirit_single"],
                    "Only supported by Fortville")
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

        self.setup_1pf_2vf_1vm_env_flag = 0
        self.setup_1pf_2vf_1vm_env(driver='')
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')
        self.portMask = utils.create_mask([self.vm0_dut_ports[0]])
        self.vm_dut_0.vm_pci0 = self.vm_dut_0.ports_info[0]['pci']

    def set_up(self):
        pass
    def setup_1pf_2vf_1vm_env(self,driver="default"):

        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 2,driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)
            time.sleep(1)

            vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
            vf1_prop = {'opt_host': self.sriov_vfs_port[1].pci}
            if driver == 'igb_uio':
                # start testpmd without the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                eal_param = '-b %(vf0)s -b %(vf1)s' % {'vf0': self.sriov_vfs_port[0].pci,
                                                       'vf1': self.sriov_vfs_port[1].pci}
                self.host_testpmd.start_testpmd("Default", eal_param=eal_param)
            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'runtime_vf_queue_number_kernel')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

            self.setup_1pf_2vf_1vm_env_flag = 1
        except Exception as e:
            self.destroy_1pf_2vf_1vm_env()
            raise Exception(e)

    def destroy_1pf_2vf_1vm_env(self):
        if getattr(self, 'vm0', None):
            # destroy testpmd in vm0
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None
        if getattr(self, 'host_testpmd', None):
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            port.bind_driver()
            self.used_dut_port = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()

        self.setup_1pf_2vf_1vm_env_flag = 0

    def send_packet2different_queue(self, dts, src, iface, count):
        self.tester.scapy_foreground()
        for i in range(1,count+1):
            j = (i//255)%255
            k = i%255
            pkt = 'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.%d.%d",dst="192.168.13.%d")/("test"*10)],iface="%s")' % (
                dts, src, j,k,k, iface)
            self.tester.scapy_append(pkt)
        self.tester.scapy_execute()

    def check_result(self, nr_queue, out, out2, pkts_num, count, misc):
        if nr_queue == 1:
            self.verify('port 0/queue 0: received 1 packets' in out, "queue %s can not receive pkt" % (nr_queue - 1))
        else:
            for i in range(nr_queue):
                if i < 10:
                    i = ' ' + str(i)
                self.verify('Queue=%s' % i in out2, "queue %s can not receive pkt" % i)
        self.verify(pkts_num == count,
                    'Received incorrect pkts number! send %d pkts,received %d pkts' % (count, pkts_num))
        self.verify('RX-total: %d' % (count + misc) in out2 and 'TX-total: %d' % (count + misc) in out2,
                    "statistic shows rx or tx pkts number: %d incorrect" % (count + misc))
        self.vm0_testpmd.execute_cmd("clear port stats all")
        self.vm0_testpmd.execute_cmd("port stop all")
        time.sleep(5)
        self.vm0_testpmd.execute_cmd('quit', '# ')
        time.sleep(3)

    def test_set_valid_vf_queue_num(self):
        """
        set valid VF queue number in testpmd command-line options
        """
        random_queue = random.randint(2, 15)
        queue_nums = [1, random_queue, self.max_queue]
        for nr_queue in queue_nums:
            self.vm0_testpmd = PmdOutput(self.vm_dut_0)
            eal_param = '-w %(vf0)s' % {'vf0': self.vm_dut_0.vm_pci0}
            tx_port = self.tester.get_local_port(self.dut_ports[0])
            tester_mac = self.tester.get_mac(tx_port)
            iface = self.tester.get_interface(tx_port)
            count = nr_queue * 20
            times = 3

            # try tree times to make sure testpmd launched normally
            while times > 0:
                out = self.vm0_testpmd.start_testpmd("all", "--rss-ip --txq=%s --rxq=%s" % (nr_queue, nr_queue), eal_param=eal_param)
                self.logger.info(out)
                if 'Failed' in out or 'failed' in out:
                    self.vm0_testpmd.execute_cmd("port stop all")
                    time.sleep(5)
                    self.vm0_testpmd.execute_cmd('quit', '# ')
                    times -= 1
                    time.sleep(3)
                else:
                    times = 0

            self.vm0_testpmd.execute_cmd('set verbose 1')
            self.vm0_testpmd.execute_cmd('set promisc all off')
            time.sleep(1)
            self.vm0_testpmd.execute_cmd('set fwd mac')
            self.vm0_testpmd.execute_cmd("clear port stats all")
            out = self.vm0_testpmd.execute_cmd('start')
            vf0_mac = self.vm0_testpmd.get_port_mac(0).lower()
            self.verify("port 0: RX queue number: %s Tx queue number: %s" % (nr_queue, nr_queue) in out, "queue number maybe error")
            self.send_packet2different_queue(vf0_mac, tester_mac, iface, count)
            out = self.vm0_testpmd.get_output()
            out2 = self.vm0_testpmd.execute_cmd('stop')
            pkts_num = out.count("src=%s - dst=%s"%(tester_mac.upper(),vf0_mac.upper()))
            misc = out.count("dst=FF:FF:FF:FF:FF:FF")
            self.logger.info("get %d boadcast misc packages " % misc)
            self.check_result(nr_queue, out, out2, pkts_num, count, misc)

    def test_set_invalid_vf_queue_num_command_line(self):
        invalid_queue_num = [0, 17]
        for i in invalid_queue_num:
            self.vm0_testpmd = PmdOutput(self.vm_dut_0)
            self.vm_dut_0.session_secondary = self.vm_dut_0.new_session()
            out = self.vm_dut_0.session_secondary.send_expect(
                './x86_64-native-linuxapp-gcc/app/testpmd -c 0xf -n 1 -w %s -- -i --txq=%s --rxq=%s' % (
                    self.vm_dut_0.vm_pci0, i, i), '# ', 40)
            if i == 0:
                self.verify('Either rx or tx queues should be non-zero' in out, "queue number can't be zero")
            else:
                # the dpdk output non-zero conflict with >=0, to be fixed...
                self.verify('txq 17 invalid - must be >= 0 && <= 16' in out, "queue number is too big")

    def test_set_valid_vf_queue_num_with_function(self):
        random_queue = random.randint(2, 15)
        queue_nums = [1, random_queue, self.max_queue]
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        eal_param = '-w %(vf0)s' % {'vf0': self.vm_dut_0.vm_pci0}
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        tester_mac = self.tester.get_mac(tx_port)
        iface = self.tester.get_interface(tx_port)
        for nr_queue in queue_nums:
            times = 3
            count = nr_queue * 20

            #try tree times to make sure testpmd launched normally
            while times > 0:
                self.vm0_testpmd = PmdOutput(self.vm_dut_0)
                out = self.vm0_testpmd.start_testpmd("all", eal_param=eal_param)
                self.logger.info(out)
                self.vm0_testpmd.execute_cmd("port stop all")
                self.vm0_testpmd.execute_cmd('set fwd mac')
                self.vm0_testpmd.execute_cmd("set verbose 1")
                self.vm0_testpmd.execute_cmd('set promisc all off')
                time.sleep(1)
                self.vm0_testpmd.execute_cmd("port config all rxq %s" % nr_queue)
                self.vm0_testpmd.execute_cmd("port config all txq %s" % nr_queue)
                out = self.vm0_testpmd.execute_cmd("port start all")
                self.logger.info(out)
                if 'failed' in out or 'fail to' in out:
                    self.vm0_testpmd.execute_cmd("port stop all")
                    time.sleep(5)
                    self.vm0_testpmd.execute_cmd('quit', '# ')
                    times -= 1
                    time.sleep(3)
                    self.vm0_testpmd.quit()
                else:
                    times = 0

            self.vm0_testpmd.execute_cmd("clear port stats all")
            out = self.vm0_testpmd.execute_cmd("start")
            self.logger.info(out)
            vf0_mac = self.vm0_testpmd.get_port_mac(0).lower()
            self.verify("port 0: RX queue number: %s Tx queue number: %s" % (nr_queue, nr_queue) in out,
                        "queue number %s maybe error" % nr_queue)
            self.send_packet2different_queue(vf0_mac, tester_mac, iface, count)
            out = self.vm0_testpmd.get_output()
            out2 = self.vm0_testpmd.execute_cmd('stop')
            pkts_num=out.count("src=%s - dst=%s"%(tester_mac.upper(),vf0_mac.upper()))
            misc = out.count("dst=FF:FF:FF:FF:FF:FF")
            self.logger.info("get %d broadcast misc packages " % misc)
            self.check_result(nr_queue, out, out2, pkts_num, count, misc)

    def test_set_invalid_vf_queue_num_with_testpmd_command(self):
        invalid_queue_num = [0, 17]
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        eal_param = '-w %(vf0)s' % {'vf0': self.vm_dut_0.vm_pci0}
        self.vm0_testpmd.start_testpmd("all", eal_param=eal_param)
        self.vm0_testpmd.execute_cmd('set promisc all off')
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("port stop all")
        for i in invalid_queue_num:
            if i == 0:
                out1 = self.vm0_testpmd.execute_cmd("port config all rxq %s" % i)
                # when set rxq or txq to 0 alone, dpdk didn't show warning, only when they are both set to 0.
                # so comment out the line below for now.
                # self.verify('Either rx or tx queues should be non zero' in out1, "queue number can't be zero")
                out = self.vm0_testpmd.execute_cmd("port config all txq %s" % i)
                self.verify('Either rx or tx queues should be non zero' in out, "queue number can't be zero")
            else:
                out = self.vm0_testpmd.execute_cmd("port config all rxq %s" % i)
                self.verify("input rxq (17) can't be greater than max_rx_queues (16) of port 0" in out,
                            "queue number is too big")
            self.vm0_testpmd.execute_cmd("clear port stats all")
            time.sleep(1)
        self.vm0_testpmd.execute_cmd('quit', '# ')

    def tear_down(self):
        self.vm0_testpmd.execute_cmd('quit', '# ')

    def tear_down_all(self):
        self.logger.info("tear_down_all")
        if self.setup_1pf_2vf_1vm_env_flag == 1:
            self.destroy_1pf_2vf_1vm_env()
