# BSD LICENSE
#
# Copyright(c) <2021> Intel Corporation. All rights reserved.
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
"""

import re

from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

DEFAULT_MTU = 1500
TSO_MTU = 9000

class TestVirtioSmoke(TestCase):


    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dst_mac = "00:01:02:03:04:05"
        self.dut_ports = self.dut.get_ports()
        self.txItf = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("all", socket=self.socket)
        self.vhost_cores = self.cores[0:3]
        self.virtio1_cores = self.cores[3:6]
        self.base_dir = self.dut.base_dir.replace('~', '/root')
        self.path = self.dut.apps_name['test-pmd']
        self.testpmd_name = self.path.split("/")[-1]
        self.vhost_user = self.dut.new_session(suite="vhost-user")
        self.virtio_user1 = self.dut.new_session(suite="virtio-user1")
        self.pmdout_vhost_user = PmdOutput(self.dut, self.vhost_user)
        self.pmdout_virtio_user1 = PmdOutput(self.dut, self.virtio_user1)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.dut.send_expect("rm -rf %s/vhost-net*" % self.base_dir, "#")

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        # On CentOS, sometimes return ' 2048'
        resp = out.replace(' ', '')
        return True if resp == '2048' else False

    def launch_testpmd_as_vhost_user(self, param, cores="Default", udev="", ports=[], no_pci=True):
        self.pmdout_vhost_user.start_testpmd(cores=cores, param=param, vdevs=[udev], ports=ports, prefix="vhost",
                                             fixed_prefix=True, no_pci=no_pci)
        self.pmdout_vhost_user.execute_cmd('set fwd mac')

    def launch_testpmd_as_virtio_user1(self, param, cores="Default", udev="", no_pci=True):
        eal_param = ""
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if 'vectorized' in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        self.pmdout_virtio_user1.start_testpmd(cores=cores, param=param, vdevs=[udev], ports=[], prefix="virtio1",
                                               fixed_prefix=True, eal_param=eal_param, no_pci=no_pci)

    def verify_vhost_queue_rx_tx_pkts(self, queue_list):
        out = self.pmdout_vhost_user.execute_cmd('stop')
        for queue_index in queue_list:
            queue = "Queue= %d" % queue_index
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                        "The queue %d rx-packets or tx-packets is 0 about " % queue_index +
                        "rx-packets:%d, tx-packets:%d" % (rx_packets, tx_packets))

    def test_virtio_loopback(self):
        param = " --nb-cores={} --rxq={} --txq={}"
        other_param = " --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip"
        vhost_dev = f"'eth_vhost0,iface=vhost-net,client=1,queues=8'"
        virtio_dev = f"'net_virtio_user0,mac={self.dst_mac},path=./vhost-net,server=1,queues=8,mrg_rxbuf=1,in_order=1'"

        self.logger.info("Launch vhost as client mode with 2 queues")
        nb_core = 2
        vhost_rxq_txq = 2
        virtio_rxq_txq = 8
        vhost_param = param.format(nb_core, vhost_rxq_txq, vhost_rxq_txq)
        virtio_param = (other_param + param).format(nb_core, virtio_rxq_txq, virtio_rxq_txq)
        self.launch_testpmd_as_vhost_user(param=vhost_param, cores=self.vhost_cores, udev=vhost_dev, no_pci=True)
        self.pmdout_vhost_user.execute_cmd('start')
        self.logger.info("Launch virtio-user as server mode with 8 queues")
        self.launch_testpmd_as_virtio_user1(param=virtio_param, cores=self.virtio1_cores, udev=virtio_dev, no_pci=True)
        self.pmdout_virtio_user1.execute_cmd('set fwd mac')
        self.pmdout_virtio_user1.execute_cmd('start tx_first 32')
        self.verify_vhost_queue_rx_tx_pkts(queue_list=range(vhost_rxq_txq))
        self.pmdout_vhost_user.execute_cmd('quit', '#')

        self.logger.info("Relaunch vhost with 8 queues and send packets")
        vhost_rxq_txq = 8
        vhost_param = param.format(nb_core, vhost_rxq_txq, vhost_rxq_txq)
        self.launch_testpmd_as_vhost_user(param=vhost_param, cores=self.cores[0:3], udev=vhost_dev, no_pci=True)
        self.pmdout_vhost_user.execute_cmd('start tx_first 32')
        self.pmdout_vhost_user.execute_cmd('stop')
        self.pmdout_vhost_user.execute_cmd('set burst 1')
        self.pmdout_vhost_user.execute_cmd('start tx_first 1')
        self.verify_vhost_queue_rx_tx_pkts(queue_list=range(vhost_rxq_txq))

        self.pmdout_virtio_user1.execute_cmd('quit', '#')
        self.pmdout_vhost_user.execute_cmd('quit', '#')

    def send_packets(self, frame_size, pkt_count):
        pkt = "Ether(dst='%s')/IP()/('x'*%d)" %(self.dst_mac, frame_size)
        self.tester.scapy_append('sendp([%s], iface="%s", count=%s)' % (pkt, self.txItf, pkt_count))
        self.tester.scapy_execute()

    def verify_virtio_user_receive_packets(self, pkt_count):
        out = self.pmdout_virtio_user1.execute_cmd('show port stats all')
        rx = re.search("RX-packets:\s*(\d*)", out)
        tx = re.search("TX-packets:\s*(\d*)", out)
        rx_packets = int(rx.group(1))
        tx_packets = int(tx.group(1))
        self.verify(rx_packets >= pkt_count and tx_packets >= pkt_count,
                    "Virtio-user receive no enough packets, RX-packets: {},RX-packets: {}".format(rx_packets, tx_packets))

    def test_virtio_pvp(self):
        param = " --nb-cores={} --txd={} --rxd={}"
        vhost_dev = f"'net_vhost0,iface=vhost-net,queues=1'"
        virtio_dev = f"'net_virtio_user0,mac={self.dst_mac},path=./vhost-net,packed_vq=1,mrg_rxbuf=0,in_order=1," \
            f"vectorized=1,queue_size=1024'"
        self.logger.info("Launch vhost")
        nb_core = 2
        vhost_rxd_txd = 1024
        vhost_param = param.format(nb_core, vhost_rxd_txd, vhost_rxd_txd)
        port = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.launch_testpmd_as_vhost_user(param=vhost_param, cores=self.vhost_cores, udev=vhost_dev,
                                          ports=[port], no_pci=False)
        self.pmdout_vhost_user.execute_cmd('start')

        self.logger.info("Launch virtio")
        nb_core = 1
        virtio_param = param.format(nb_core, vhost_rxd_txd, vhost_rxd_txd)
        self.launch_testpmd_as_virtio_user1(param=virtio_param, cores=self.virtio1_cores, udev=virtio_dev, no_pci=True)
        self.pmdout_virtio_user1.execute_cmd('set fwd mac')
        self.pmdout_virtio_user1.execute_cmd('start')

        self.logger.info("Start send packets and verify")
        # set tester port MTU=9000 when need to send big packets.
        self.tester.send_expect("ifconfig %s mtu %s" % (self.txItf, TSO_MTU), "# ")
        # set vhost testpmd port MTU=9000
        self.pmdout_vhost_user.execute_cmd('stop')
        self.pmdout_vhost_user.execute_cmd('port stop 0')
        self.pmdout_vhost_user.execute_cmd('port config mtu 0 %s' % TSO_MTU)
        self.pmdout_vhost_user.execute_cmd('port start 0')
        self.pmdout_vhost_user.execute_cmd('start')
        self.send_packets(frame_size=64, pkt_count=10)
        self.send_packets(frame_size=1518, pkt_count=10)
        self.verify_virtio_user_receive_packets(pkt_count=20)

        self.pmdout_virtio_user1.execute_cmd('quit', '#')
        self.pmdout_vhost_user.execute_cmd('quit', '#')

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.close_session(self.vhost_user)
        self.dut.close_session(self.virtio_user1)
        self.tester.send_expect("ifconfig %s mtu %s" % (self.txItf, DEFAULT_MTU), "# ")
