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

import re
import time

import framework.utils as utils
from framework.test_case import TestCase
from framework.virt_common import VM
from framework.pmd_output import PmdOutput


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
        self.cores = self.dut.get_core_list("all", socket=self.ports_socket)
        self.vhost_cores = self.cores[0:6]
        self.verify(len(self.vhost_cores) >= 6, "The machine has too few cores.")
        self.base_dir = self.dut.base_dir.replace("~", "/root")
        self.app_testpmd_path = self.dut.apps_name["test-pmd"]
        self.app_symmetric_mp_path = self.dut.apps_name["symmetric_mp"]
        self.app_hotplug_mp_path = self.dut.apps_name["hotplug_mp"]
        self.testpmd_name = self.app_testpmd_path.split("/")[-1]
        self.vhost_user = self.dut.create_session("vhost-user")
        self.vhost_user_pmd = PmdOutput(self.dut, self.vhost_user)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def setup_vm_env(self):
        """
        Create testing environment
        """
        self.virtio_mac = "52:54:00:00:00:0"
        self.vm = VM(self.dut, "vm0", "vhost_sample")
        for i in range(self.queues):
            vm_params = {}
            vm_params["driver"] = "vhost-user"
            vm_params["opt_path"] = self.base_dir + "/vhost-net%d" % i
            vm_params["opt_mac"] = "%s%d" % (self.virtio_mac, i + 2)
            vm_params["opt_queue"] = self.queues
            vm_params["opt_server"] = "server"
            vm_params["opt_settings"] = "mrg_rxbuf=on,csum=on,mq=on,vectors=%d" % (
                2 * self.queues + 2
            )
            self.vm.set_vm_device(**vm_params)

        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

        return True

    def launch_testpmd(self, param, eal_param):
        """
        launch testpmd
        """
        self.vhost_user_pmd.start_testpmd(cores=self.vhost_cores, param=param, eal_param=eal_param, prefix='vhost', fixed_prefix=True, no_pci=True)

    def launch_symmetric_mp(self):
        example_cmd_primary = (
            self.app_symmetric_mp_path
            + " -l 0 -n %d --proc-type=auto -- -p 3 --num-procs=%d --proc-id=0"
        )
        example_cmd_secondary = (
            self.app_symmetric_mp_path
            + " -l 1 -n %d --proc-type=secondary -- -p 3 --num-procs=%d --proc-id=1"
        )
        final_cmd_primary = example_cmd_primary % (self.mem_channels, self.queues)
        final_cmd_secondary = example_cmd_secondary % (self.mem_channels, self.queues)
        self.vm_primary.send_expect(final_cmd_primary, "Lcore", 120)
        time.sleep(3)
        self.vm_secondary.send_expect(final_cmd_secondary, "Lcore", 120)

    def launch_hotplug_mp(self):
        example_cmd_primary = (
            self.app_hotplug_mp_path
            + " -l 0 -n %d --proc-type=auto -- -p 3 --num-procs=%d --proc-id=0"
        )
        example_cmd_secondary = (
            self.app_hotplug_mp_path
            + " -l 1 -n %d --proc-type=secondary -- -p 3 --num-procs=%d --proc-id=1"
        )
        final_cmd_primary = example_cmd_primary % (self.mem_channels, self.queues)
        final_cmd_secondary = example_cmd_secondary % (self.mem_channels, self.queues)
        self.vm_primary.send_expect(final_cmd_primary, "example>", 120)
        time.sleep(3)
        self.vm_secondary.send_expect(final_cmd_secondary, "example>", 120)

    def check_etherdev(self, dev_list):
        primary_out = self.vm_primary.send_expect("list", "example", 120)
        for dev in dev_list:
            self.verify(dev in primary_out, "dev {} not in the list")
        secondary_out = self.vm_secondary.send_expect("list", "example", 120)
        for dev in dev_list:
            self.verify(dev in secondary_out, "dev {} not in the list")

    def detach_etherdev_from_primary(self, dev_pci):
        self.vm_primary.send_expect("detach {}".format(dev_pci), "example", 120)

    def attach_etherdev_from_secondary(self, dev_pci):
        self.vm_secondary.send_expect("attach {}".format(dev_pci), "example", 120)

    def prepare_symmetric_mp(self):
        out = self.vm_dut.build_dpdk_apps("./examples/multi_process/symmetric_mp")
        self.verify("Error" not in out, "compilation symmetric_mp error")

    def prepare_hotplug_mp(self):
        out = self.vm_dut.build_dpdk_apps("./examples/multi_process/hotplug_mp")
        self.verify("Error" not in out, "compilation hotplug_mp error")

    def close_session(self):
        self.vm_dut.close_session(self.vm_primary)
        self.vm_dut.close_session(self.vm_secondary)
        self.dut.close_session(self.vhost_user)

    def test_virtio_primary_and_secondary_process(self):
        vhost_eal_param = "--vdev 'net_vhost,iface=vhost-net0,queues=2,client=1' --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1'"
        vhost_param = "--nb-cores=4 --rxq=2 --txq=2 --txd=1024 --rxd=1024"
        self.launch_testpmd(param=vhost_param, eal_param=vhost_eal_param)
        self.setup_vm_env()
        self.prepare_symmetric_mp()
        self.vm_primary = self.vm_dut.new_session(suite="vm_primary")
        self.vm_secondary = self.vm_dut.new_session(suite="vm_secondary")
        self.launch_symmetric_mp()
        self.vhost_user_pmd.execute_cmd("set fwd mac")
        self.vhost_user_pmd.execute_cmd("start tx_first")
        time.sleep(3)
        vm_primary_out = self.vm_primary.send_expect("^c", "#", 15)
        print(vm_primary_out)
        time.sleep(3)
        vm_secondary_out = self.vm_secondary.send_expect("^c", "#", 15)
        print(vm_secondary_out)
        result_primary = re.findall(r"Port \d: RX - (\w+)", vm_primary_out)
        result_secondary = re.findall(r"Port \d: RX - (\w+)", vm_secondary_out)
        self.verify(
            len(result_primary[0]) != 0
            and len(result_primary[1]) != 0
            and len(result_secondary[0]) != 0
            and len(result_secondary[1]) != 0,
            "RX no data",
        )
        self.dut.send_expect("quit", "#", 15)

    def test_virtio_primay_and_secondary_process_hotplug(self):
        vhost_eal_param = "--vdev 'net_vhost0,iface=vhost-net0,queues=2,client=1' --vdev 'net_vhost1,iface=vhost-net1,queues=2,client=1'"
        vhost_param = "--nb-cores=4 --rxq=2 --txq=2 --txd=1024 --rxd=1024"
        self.launch_testpmd(param=vhost_param, eal_param=vhost_eal_param)
        self.vhost_user_pmd.execute_cmd("set fwd txonly")
        self.vhost_user_pmd.execute_cmd("start")
        self.setup_vm_env()
        self.prepare_hotplug_mp()
        self.vm_primary = self.vm_dut.new_session(suite="vm_primary")
        self.vm_secondary = self.vm_dut.new_session(suite="vm_secondary")
        self.launch_hotplug_mp()
        vm_ports = []
        for pci_info in self.vm_dut.ports_info:
            vm_ports.append(pci_info['pci'])
        self.check_etherdev(dev_list=vm_ports)
        detach_pci = vm_ports[0]
        for _ in range(2):
            self.detach_etherdev_from_primary(dev_pci=detach_pci)
            vm_ports.remove(detach_pci)
            self.check_etherdev(dev_list=vm_ports)
            self.attach_etherdev_from_secondary(dev_pci=detach_pci)
            vm_ports.append(detach_pci)
            self.check_etherdev(dev_list=vm_ports)
        self.dut.send_expect("quit", "#", 15)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.vm_dut.kill_all()
        self.dut.kill_all()
        self.vm.stop()
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.close_session()
