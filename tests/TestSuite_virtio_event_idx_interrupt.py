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
Virtio idx interrupt need test with l3fwd-power sample
"""

import utils
import time
import thread
import re
from virt_common import VM
from test_case import TestCase
from etgen import IxiaPacketGenerator


class TestVirtioIdxInterrupt(TestCase, IxiaPacketGenerator):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVirtioIdxInterrupt, self)
        self.queues = 1
        self.nb_cores = 1
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                            == self.ports_socket])
        self.mem_channels = self.dut.get_memory_channels()
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.base_dir = self.dut.base_dir.replace('~', '/root')

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.flag = None
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")
        self.vhost = self.dut.new_session(suite="vhost")

    def ip(self, port, frag, src, proto, tos, dst, chksum, len, options,
                                            version, flags, ihl, ttl, id):
        """
        Configure IP protocol.
        """
        self.add_tcl_cmd("protocol config -name ip")
        self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
        self.add_tcl_cmd('ip config -destIpAddrMode ipRandom')
        self.add_tcl_cmd("ip config -ttl %d" % ttl)
        self.add_tcl_cmd("ip config -totalLength %d" % len)
        self.add_tcl_cmd("ip config -fragment %d" % frag)
        self.add_tcl_cmd("ip config -ipProtocol %d" % proto)
        self.add_tcl_cmd("ip config -identifier %d" % id)
        self.add_tcl_cmd("stream config -framesize %d" % (len + 18))
        self.add_tcl_cmd("ip set %d %d %d" % (self.chasId, port['card'],
                                             port['port']))

    def get_core_mask(self):
        self.core_config = "1S/%dC/1T" % (self.nb_cores + 1)
        self.verify(self.cores_num >= (self.nb_cores + 1),
                    "There has not enough cores to test this case %s" %
                    self.running_case)
        self.core_list = self.dut.get_core_list(self.core_config)
        self.core_mask = utils.create_mask(self.core_list)

    def start_vhost_testpmd(self):
        """
        start the testpmd on vhost side
        """
        # get the core mask depend on the nb_cores number
        self.get_core_mask()
        command_line = self.dut.target + "/app/testpmd -c %s -n %d " + \
                "--socket-mem 2048,2048 --legacy-mem --file-prefix=vhost " + \
                "--vdev 'net_vhost,iface=%s/vhost-net,queues=%d' -- -i " + \
                "--nb-cores=%d --txd=1024 --rxd=1024 --rxq=%d --txq=%d"
        command_line = command_line % (self.core_mask, self.mem_channels, self.base_dir,
                        self.queues, self.nb_cores, self.queues, self.queues)
        self.vhost.send_expect(command_line, "testpmd> ", 30)
        self.vhost.send_expect("start", "testpmd> ", 30)

    def start_vms(self):
        """
        start qemus
        """
        self.vm = VM(self.dut, 'vm0', 'vhost_sample')
        vm_params = {}
        vm_params['driver'] = 'vhost-user'
        vm_params['opt_path'] = '%s/vhost-net' % self.base_dir
        vm_params['opt_mac'] = "00:11:22:33:44:55"
        opt_args = "mrg_rxbuf=on,csum=on,gso=on,guest_csum=on,host_tso4=on,guest_tso4=on"
        if self.queues > 1:
            vm_params['opt_queue'] = self.queues
            opt_args = opt_args + ",mq=on,vectors=%d" % (2*self.queues + 2)
        vm_params['opt_settings'] = opt_args
        self.vm.set_vm_device(**vm_params)
        try:
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed")
        except Exception as e:
            self.logger.error("ERROR: Failure for %s" % str(e))
        self.vm_dut.restore_interfaces()

    def config_virito_net_in_vm(self):
        """
        config ip for virtio net
        set net for multi queues enable
        """
        self.vm_intf = self.vm_dut.ports_info[0]['intf']
        self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
        out = self.vm_dut.send_expect("ifconfig", "#")
        self.verify(self.vm_intf not in out, "the virtio-pci down failed")
        self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")
        if self.queues > 1:
            self.vm_dut.send_expect("ethtool -L %s combined %d" %
                            (self.vm_intf, self.queues), "#", 20)

    def start_to_send_packets(self, delay):
        """
        start send packets
        """
        tgen_input = []
        port = self.tester.get_local_port(self.dut_ports[0])
        self.tester.scapy_append('a=[Ether(dst="%s")/IP(src="0.240.74.101",proto=255)/UDP()/("X"*18)]' % (self.dst_mac))
        self.tester.scapy_append('wrpcap("interrupt.pcap", a)')
        self.tester.scapy_execute()

        tgen_input.append((port, port, "interrupt.pcap"))
        _, self.flag = self.tester.traffic_generator_throughput(tgen_input, delay=delay)

    def check_packets_after_reload_virtio_device(self, reload_times):
        """
        start to send packets and check virtio net has receive packets
        """
        # ixia send packets times equal to reload_times * wait_times
        start_time = time.time()
        thread.start_new_thread(self.start_to_send_packets, (reload_times*20,))
        # wait the ixia begin to send packets
        time.sleep(10)
        self.vm_pci = self.vm_dut.ports_info[0]['pci']
        # reload virtio device to check the virtio-net can receive packets
        for i in range(reload_times+1):
            if time.time() - start_time > reload_times*30:
                self.logger.error("The ixia has stop to send packets, "
                        "please change the delay time of ixia")
                self.logger.info("The virtio device has reload %d times" % i)
                return False
            self.logger.info("The virtio net device reload %d times" % i)
            self.vm_dut.send_expect("tcpdump -n -vv -i %s" % self.vm_intf,
                                    "tcpdump", 30)
            time.sleep(5)
            out = self.vm_dut.get_session_output(timeout=3)
            self.vm_dut.send_expect("^c", "#", 30)
            self.verify("ip-proto-255" in out,
                        "The virtio device can not receive packets"
                        "after reload %d times" % i)
            time.sleep(2)
            # reload virtio device
            self.vm_dut.restore_interfaces()
            time.sleep(3)
            self.vm_dut.send_expect("ifconfig %s down" % self.vm_intf, "#")
            self.vm_dut.send_expect("ifconfig %s up" % self.vm_intf, "#")

        # wait ixia thread exit
        self.logger.info("wait the thread of ixia to exit")
        while(1):
            if self.flag is not None:
                break
            time.sleep(5)
        return True

    def check_each_queue_has_packets_info_on_vhost(self):
        """
        check each queue has receive packets on vhost side
        """
        out = self.vhost.send_expect("stop", "testpmd> ", 60)
        print out
        for queue_index in range(0, self.queues):
            queue = re.search("Port= 0/Queue=\s*%d" % queue_index, out)
            queue = queue.group()
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                   "The queue %d rx-packets or tx-packets is 0 about " %
                   queue_index + \
                   "rx-packets:%d, tx-packets:%d" %
                   (rx_packets, tx_packets))

        self.vhost.send_expect("clear port stats all", "testpmd> ", 60)

    def stop_all_apps(self):
        """
        close all vms
        """
        self.vm.stop()
        self.vhost.send_expect("quit", "#", 20)

    def test_perf_virito_idx_interrupt_with_virtio_pci_driver_reload(self):
        """
        virtio-pci driver reload test
        """
        self.queues = 1
        self.nb_cores = 1
        self.start_vhost_testpmd()
        self.start_vms()
        self.config_virito_net_in_vm()
        res = self.check_packets_after_reload_virtio_device(reload_times=30)
        self.verify(res is True, "Should increase the wait times of ixia")
        self.stop_all_apps()

    def test_perf_virtio_idx_interrupt_with_multi_queue(self):
        """
        wake up virtio-net cores with event idx interrupt mode 16 queues test
        """
        self.queues = 16
        self.nb_cores = 16
        self.start_vhost_testpmd()
        self.start_vms()
        self.config_virito_net_in_vm()
        self.start_to_send_packets(delay=15)
        self.check_each_queue_has_packets_info_on_vhost()
        self.stop_all_apps()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.close_session(self.vhost)
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
