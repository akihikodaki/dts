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
The Link Bonding functions make it possible to dynamically create and manage
link bonding devices from within testpmd interactive prompt.
"""
import re
import time
import utils
from test_case import TestCase
from virt_common import VM
from pmd_output import PmdOutput
from packet import Packet
from pktgen import PacketGeneratorHelper


class TestPVPVirtIOBonding(TestCase):

    def set_up_all(self):
        # Get and verify the ports
        self.core_config = "1S/5C/1T"
        self.queues = 4
        self.dut_ports = self.dut.get_ports()
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket']) ==
                            self.ports_socket])
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.verify(self.cores_num >= 5,
                    "There has not enought cores to test this suite %s" %
                    self.suite_name)
        cores = self.dut.get_core_list(self.core_config, socket=self.ports_socket)
        self.coremask = utils.create_mask(cores)
        self.memory_channel = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])

        self.out_path = '/tmp/%s' % self.suite_name
        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        run before each test case.
        """
        self.dut.send_expect("rm -rf ./vhost.out", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.start_testpmd_on_vhost()
        self.start_one_vm()

    def start_testpmd_on_vhost(self):
        """
        launch vhost testpmd
        """
        vdev_info = ""
        for i in range(self.queues):
            vdev_info += "--vdev 'net_vhost%d,iface=vhost-net%d,client=1,queues=1' " % (i, i)
        params = "--port-topology=chained --nb-cores=4 --txd=1024 --rxd=1024"
        eal_param = "--socket-mem 2048,2048 --legacy-mem --file-prefix=vhost %s " % vdev_info
        self.vhost_testpmd = PmdOutput(self.dut)
        self.vhost_testpmd.start_testpmd(self.core_config, params, eal_param=eal_param)
        self.vhost_testpmd.execute_cmd('set fwd mac')
        self.vhost_testpmd.execute_cmd('start')

    def start_testpmd_on_vm(self):
        """
        launch testpmd in VM
        """
        self.vm_testpmd = PmdOutput(self.vm_dut)
        self.vm_testpmd.start_testpmd("all", "--port-topology=chained --nb-cores=5")

    def create_bonded_device_in_vm(self, mode):
        """
        create one bonded device on socket 0
        """
        self.vm_testpmd.execute_cmd('create bonded device %s 0' % mode)
        self.vm_testpmd.execute_cmd('add bonding slave 0 4')
        self.vm_testpmd.execute_cmd('add bonding slave 1 4')
        self.vm_testpmd.execute_cmd('add bonding slave 2 4')
        out = self.vm_testpmd.execute_cmd('port start 4')
        self.verify("Invalid port" not in out, "Port start failed for %s" % out)
        out = self.vm_testpmd.execute_cmd('show bonding config 4')
        self.logger.info(out)
        self.vm_testpmd.execute_cmd('set portlist 3,4')
        self.vm_testpmd.execute_cmd('set fwd mac')
        self.vm_testpmd.execute_cmd('start')

    def get_port_stats(self, out, port):
        log = "Forward statistics for port %d" % port
        index = out.find(log)
        self.verify(index >= 0, "not have stats info for port %d" % port)
        xstats_info = out[index:]
        stats_rx = re.search("RX-packets:\s*(\d*)", xstats_info)
        stats_tx = re.search("TX-packets:\s*(\d*)", xstats_info)
        result_rx = int(stats_rx.group(1))
        result_tx = int(stats_tx.group(1))
        return result_rx/1000000, result_tx/1000000

    def check_port_stats_on_vhost(self):
        """
        check port stats at vhost side:
        port 0 and port 4 can rx packets,while port 0 and port 1 can tx packets
        """
        out = self.vhost_testpmd.execute_cmd('stop')
        self.vhost_testpmd.execute_cmd('start')
        print out
        rx, tx = self.get_port_stats(out, 0)
        self.verify(rx > 0 and tx > 0, "vhost port 0 can not receive or fwd data")

        rx, tx = self.get_port_stats(out, 4)
        self.verify(rx > 0, "vhost port 4 can not receive data")

        rx, tx = self.get_port_stats(out, 1)
        self.verify(tx > 0, "vhost port 4 can not fwd data")

    def check_port_stats_on_vm(self):
        """
        check port stats at VM side:
        port 4 can rx packets,while port 3 tx packets
        """
        out = self.vm_testpmd.execute_cmd('stop')
        print out
        rx, tx = self.get_port_stats(out, 4)
        self.verify(rx > 0, "vm port 4 can not receive data")

        rx, tx = self.get_port_stats(out, 3)
        self.verify(tx > 0, "vm port 3 can not fwd data")

    def send_packets(self):
        """
        start traffic and verify data stats on vhost and vm
        """
        tgen_input = []
        rx_port = self.tester.get_local_port(self.dut_ports[0])
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        pkt = Packet(pkt_type='UDP')
        pkt.config_layer('ether', {'dst': '%s' % self.dst_mac})
        pkt.save_pcapfile(self.tester, "%s/bonding.pcap" % self.out_path)
        tgen_input.append((tx_port, rx_port, "%s/bonding.pcap" % self.out_path))
        self.tester.pktgen.clear_streams()
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100, None, self.tester.pktgen)
        # set traffic option
        traffic_opt = {'delay': 10}
        _, _ = self.tester.pktgen.measure_throughput(stream_ids=streams, options=traffic_opt)

    def set_vm_vcpu(self):
        """
        set the vcpu number of vm
        """
        params_number = len(self.vm.params)
        for i in range(params_number):
            if self.vm.params[i].keys()[0] == 'cpu':
                self.vm.params[i]['cpu'][0]['number'] = 6

    def start_one_vm(self):
        """
        bootup one vm with four virtio-net devices
        """
        virtio_mac = "52:54:00:00:00:0"
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        self.vm.load_config()
        vm_params = {}
        for i in range(self.queues):
            vm_params['opt_server'] = 'server'
            vm_params['driver'] = 'vhost-user'
            vm_params['opt_path'] = './vhost-net%d' % i
            vm_params['opt_mac'] = "%s%d" % (virtio_mac, i+1)
            self.vm.set_vm_device(**vm_params)
        self.set_vm_vcpu()
        try:
            # Due to we have change the params info before,
            # so need to start vm with load_config=False
            self.vm_dut = self.vm.start(load_config=False)
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))

    def stop_testpmd_and_vm(self):
        """
        quit testpmd on vhost and stop vm
        """
        self.vhost_testpmd.quit()
        self.vm.stop()

    def test_perf_vhost_virtio_bonding_mode_from_0_to_6(self):
        """
        test the pvp performance for vector path
        """
        # start testpmd on VM
        mode = ["0", "1", "2", "3", "4", "5", "6"]
        for i in mode:
            self.start_testpmd_on_vm()
            self.create_bonded_device_in_vm(i)
            # about the mode 4, just verify it can bonded ok
            if i == "4":
                self.vm_testpmd.quit()
                continue
            self.send_packets()
            self.check_port_stats_on_vhost()
            self.check_port_stats_on_vm()
            self.vm_testpmd.quit()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.stop_testpmd_and_vm()
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
