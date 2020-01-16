# BSD LICENSE
# Copyright (c) <2019>, Intel Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# - Neither the name of Intel Corporation nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""
DPDK Test suite.
This test is a multi-process test which demonstrates how multiple processes can
work together to perform packet I/O and packet processing in parallel, much as
other example application work by using multiple threads. In this example, each
process reads packets from all network ports being used - though from a different
RX queue in each case. Those packets are then forwarded by each process which
sends them out by writing them directly to a suitable TX queue.
"""

import time
import re
import utils
from test_case import TestCase
from virt_common import VM


class TestVdevPrimarySecondary(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.queues = 2
        self.mem_channels = self.dut.get_memory_channels()
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        cores = self.dut.get_core_list("1S/12C/1T", socket=self.ports_socket)
        self.coremask = utils.create_mask(cores)
        self.verify(len(self.coremask) >= 6, "The machine has too few cores.")
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")


    def setup_vm_env(self):
        """
        Create testing environment
        """
        self.virtio_mac = "52:54:00:00:00:0"
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        for i in range(self.queues):
            vm_params = {}
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = self.base_dir + '/vhost-net%d' % i
            vm_params['opt_mac'] = "%s%d" % (self.virtio_mac, i+2)
            vm_params['opt_queue'] = self.queues
            vm_params['opt_server'] = 'server'
            vm_params['opt_settings'] = 'mrg_rxbuf=on,mq=on,vectors=%d' % (2*self.queues+2)
            self.vm.set_vm_device(**vm_params)

        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

        return True


    def launch_testpmd(self):
        """
        launch testpmd
        """
        cmd = "./%s/app/testpmd -l 1-6 -n %d --socket-mem 2048,2048 --legacy-mem --file-prefix=vhost" + \
              " --vdev 'net_vhost0,iface=%s/vhost-net0,queues=%d,client=1'" + \
              " --vdev 'net_vhost1,iface=%s/vhost-net1,queues=%d,client=1'" + \
              " -- -i --nb-cores=4 --rxq=%d --txq=%d --txd=1024 --rxd=1024"
        start_cmd = cmd % (self.target, self.mem_channels, self.base_dir, self.queues, self.base_dir, self.queues, self.queues, self.queues)
        self.dut.send_expect(start_cmd, "testpmd> ", 120)
        self.dut.send_expect("set fwd txonly", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)


    def launch_examples(self):
        example_cmd_auto = "./examples/multi_process/symmetric_mp/build/symmetric_mp -l 0 -n %d --proc-type=auto -- -p 3 --num-procs=%d --proc-id=0"
        example_cmd_secondary = "./examples/multi_process/symmetric_mp/build/symmetric_mp -l 1 -n %d --proc-type=secondary -- -p 3 --num-procs=%d --proc-id=1"
        final_cmd_first = example_cmd_auto % (self.mem_channels, self.queues)
        final_cmd_secondary = example_cmd_secondary % (self.mem_channels, self.queues)
        self.vhost_first.send_expect(final_cmd_first, "Lcore", 120)
        time.sleep(3)
        self.vhost_secondary.send_expect(final_cmd_secondary, "Lcore", 120)


    def prepare_symmetric_mp(self):
        self.vm_dut.send_expect("cp ./examples/multi_process/symmetric_mp/main.c .", "#")
        self.vm_dut.send_expect(
                "sed -i '/.offloads = DEV_RX_OFFLOAD_CHECKSUM,/d' ./examples/multi_process/symmetric_mp/main.c", "#")
        self.vm_dut.send_expect(
                "sed -i 's/ETH_MQ_RX_RSS,/ETH_MQ_RX_NONE,/g' ./examples/multi_process/symmetric_mp/main.c", "#")
        out = self.vm_dut.build_dpdk_apps('./examples/multi_process/symmetric_mp')
        self.verify("Error" not in out, "compilation symmetric_mp error")


    def restore_symmetric_mp_env(self):
        self.vm_dut.send_expect("\cp ./main.c ./examples/multi_process/symmetric_mp/", "#", 15)
        out = self.vm_dut.build_dpdk_apps('./examples/multi_process/symmetric_mp')
        self.verify("Error" not in out, "compilation symmetric_mp error")

    def close_session(self):
        self.vm_dut.close_session(self.vhost_first)
        self.vm_dut.close_session(self.vhost_secondary)


    def test_Virtio_primary_and_secondary_process(self):
        # start testpmd
        self.launch_testpmd()
        self.setup_vm_env()
        # Modify code
        self.prepare_symmetric_mp()
        # create 2 new session
        self.vhost_first = self.vm_dut.new_session(suite="vhost_first")
        self.vhost_secondary = self.vm_dut.new_session(suite="vhsot_secondary")
        # start symmetric_mp
        self.launch_examples()
        time.sleep(3)
        vhost_first_out =  self.vhost_first.send_expect("^c", "#", 15)
        print(vhost_first_out)
        time.sleep(3)
        vhost_secondary_out = self.vhost_secondary.send_expect("^c", "#", 15)
        print(vhost_secondary_out)
        result_first = re.findall(r'Port \d: RX - (\w+)', vhost_first_out)
        result_secondary = re.findall(r'Port \d: RX - (\w+)', vhost_secondary_out)
        self.verify(len(result_first[0]) != 0 and len(result_first[1]) != 0 and len(result_secondary[0]) != 0 and len(result_secondary[1]) != 0, "RX no data")
        self.dut.send_expect("quit", "#", 15)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.restore_symmetric_mp_env()
        self.close_session()
        self.vm_dut.kill_all()
        self.dut.kill_all()
        self.vm.stop()
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)



    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
