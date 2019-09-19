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

virtio user as exception path test suite.
"""
import re
import time
import utils
from test_case import TestCase
from settings import HEADER_SIZE
import vhost_peer_conf as peer
from pktgen import PacketGeneratorHelper

class TestVirtioUserAsExceptionalPath(TestCase):

    def set_up_all(self):
        # Get and verify the ports
        self.dut_ports = self.dut.get_ports()
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.memory_channel = self.dut.get_memory_channels()
        self.pci0 = self.dut.ports_info[0]['pci']
        pf_info = self.dut_ports[0]
        netdev = self.dut.ports_info[pf_info]['port']
        self.socket = netdev.get_nic_socket()
        self.virtio_ip1 = "2.2.2.1"
        self.virtio_ip2 = "2.2.2.21"
        self.virtio_mac = "52:54:00:00:00:01"
        self.out_path = '/tmp'

        out = self.tester.send_expect('ls -d %s' % self.out_path, '# ')
        if 'No such file or directory' in out:
            self.tester.send_expect('mkdir -p %s' % self.out_path, '# ')
        # set diff arg about mem_socket base on socket number
        if len(set([int(core['socket']) for core in self.dut.cores])) == 1:
            self.socket_mem = '1024'
        else:
            self.socket_mem = '1024,1024'
        self.pktgen_helper = PacketGeneratorHelper()
        self.peer_pci_setup = False
        self.prepare_dpdk()

    def set_up(self):
        #
        # Run before each test case.
        #
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("modprobe vhost-net", "#")
        self.peer_pci_setup = False

    def get_pci_info_from_cfg(self):
        # Get the port's socket and get the core for testpmd
        self.cores = self.dut.get_core_list("1S/2C/1T", socket=self.socket)

        self.pci = peer.get_pci_info()
        self.pci_drv = peer.get_pci_driver_info()
        self.peer_pci = peer.get_pci_peer_info()
        self.nic_in_kernel = peer.get_pci_peer_intf_info()
        self.verify(len(self.pci) != 0 and len(self.pci_drv) != 0
                    and len(self.peer_pci) != 0
                    and len(self.nic_in_kernel) != 0,
                    'Pls config the direct connection info in vhost_peer_conf.cfg')
        # unbind the port conf in ports.cfg
        for i in self.dut_ports:
            port = self.dut.ports_info[i]['port']
            port.bind_driver()
        self.dut.send_expect(
            "./usertools/dpdk-devbind.py -b igb_uio %s" %
            self.pci, '#', 30)
        self.peer_pci_setup = True

    def launch_testpmd_vhost(self):
        if self.queue == 1:
            comment = ""
            cores_number = 3
        else:
            comment = " --txq=2 --rxq=2 --nb-cores=1"
            cores_number = 4
        cores_config = '1S/%sC/1T' % cores_number
        cores_list = self.dut.get_core_list(cores_config, socket=self.socket)
        self.verify(len(cores_list) >= cores_number, "Failed to get cores list")
        core_mask = utils.create_mask(cores_list[0:2])
        self.testcmd = self.target + "/app/testpmd -c %s -n %d -w %s  --socket-mem %s" \
                        + " --vdev=virtio_user0,mac=%s,path=/dev/vhost-net,"\
                        "queue_size=1024,queues=%s -- -i --rxd=1024 --txd=1024 %s"
        self.testcmd_start = self.testcmd % (core_mask, self.memory_channel,
                self.pci0, self.socket_mem, self.virtio_mac, self.queue, comment)
        self.vhost_user = self.dut.new_session(suite="user")
        self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd>", 120)
        vhost_pid = self.dut.send_expect("ps -aux | grep vhost | grep -v grep | awk '{print $2}'", "# ")
        vhost_pid_list = vhost_pid.split("\r\n")
        self.dut.send_expect("taskset -pc %s %s" % (cores_list[-1], vhost_pid_list[1]), "# ")
        if self.queue == 2:
            self.dut.send_expect("taskset -pc %s %s" % (cores_list[-2], vhost_pid_list[2]), "# ")

    def launch_testpmd_exception_path(self):
        self.testcmd = self.target + "/app/testpmd -c %s -n %d --socket-mem %s --legacy-mem" \
                + " --vdev=virtio_user0,mac=%s,path=/dev/vhost-net,queue_size=1024 -- -i" \
                + " --rxd=1024 --txd=1024"
        self.coremask = utils.create_mask(self.cores)
        self.testcmd_start = self.testcmd % (self.coremask, self.memory_channel,
                                    self.socket_mem, self.virtio_mac)
        self.vhost_user = self.dut.new_session(suite="user")
        self.vhost_user.send_expect("modprobe vhost-net", "#", 120)
        self.vhost_user.send_expect(self.testcmd_start, "testpmd> ", 120)
        self.vhost_user.send_expect("set fwd csum", "testpmd> ", 120)
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 1", "testpmd> ", 120)
        self.vhost_user.send_expect("port config 0 tx_offload tcp_cksum on", "testpmd> ", 120)
        self.vhost_user.send_expect("port config 0 tx_offload ipv4_cksum on", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip sw 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set tcp hw 0", "testpmd> ", 120)
        self.vhost_user.send_expect("tso set 1448 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 0", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def set_route_table(self):
        self.dut.send_expect("ifconfig tap0 up", "#")
        self.dut.send_expect("ifconfig tap0 2.2.2.2/24 up", "#")
        self.dut.send_expect("route add -net 2.2.2.0/24 gw 2.2.2.1 dev tap0", "#")
        self.dut.send_expect("arp -s 2.2.2.1 %s" % self.virtio_mac, "#")

    def prepare_tap_device(self):
        self.dut.send_expect("ifconfig tap0 up", "#")
        self.dut.send_expect("ifconfig tap0 1.1.1.2", "#")

    def testpmd_reset(self):
        self.vhost_user.send_expect("stop", "testpmd> ", 120)
        self.vhost_user.send_expect("port stop 1", "testpmd> ", 120)
        self.vhost_user.send_expect("csum set ip sw 1", "testpmd> ", 120)
        self.vhost_user.send_expect("port start 1", "testpmd> ", 120)
        self.vhost_user.send_expect("start", "testpmd> ", 120)

    def config_kernel_nic_host(self):
        #
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.send_expect("ip netns add ns1", "#")
        self.dut.send_expect("ip link set %s netns ns1" % self.nic_in_kernel, "#")
        self.dut.send_expect("ip netns exec ns1 ifconfig %s 1.1.1.8 up" % self.nic_in_kernel, "#")
        self.dut.send_expect("ip netns exec ns1 ethtool -K %s gro on" % self.nic_in_kernel, "#")
        self.dut.send_expect("ip netns exec ns1 ethtool -K %s tso on" % self.nic_in_kernel, "#")

    def prepare_dpdk(self):
        #
        # Changhe the testpmd checksum fwd code for mac change
        self.dut.send_expect(
            "cp ./app/test-pmd/csumonly.c ./app/test-pmd/csumonly_backup.c",
            "#")
        self.dut.send_expect(
            "sed -i '/ether_addr_copy(&peer_eth/i\#if 0' ./app/test-pmd/csumonly.c", "#")
        self.dut.send_expect(
            "sed -i '/parse_ethernet(eth_hdr, &info/i\#endif' ./app/test-pmd/csumonly.c", "#")
        self.dut.build_install_dpdk(self.dut.target)
        time.sleep(3)

    def unprepare_dpdk(self):
        # Recovery the DPDK code to original
        self.dut.send_expect(
            "cp ./app/test-pmd/csumonly_backup.c ./app/test-pmd/csumonly.c ",
            "#")
        self.dut.send_expect("rm -rf ./app/test-pmd/csumonly_backup.c", "#")
        self.dut.build_install_dpdk(self.dut.target)

    def iperf_result_verify(self, vm_client):
        '''
        Get the iperf test result
        '''
        fmsg = vm_client.send_expect("cat /root/iperf_client.log", "#")
        print fmsg
        iperfdata = re.compile('[\d+]*.[\d+]* [M|G]bits/sec').findall(fmsg)
        print iperfdata
        self.verify(iperfdata, 'There no data about this case')
        self.result_table_create(['Data', 'Unit'])
        results_row = ['exception path']
        results_row.append(iperfdata[-1])
        self.result_table_add(results_row)
        self.result_table_print()
        self.output_result = "Iperf throughput is %s" % iperfdata[-1]
        self.logger.info(self.output_result)

    def send_and_verify_loss(self):
        header_row = ["Frame Size", "zero_loss_rate", "tx_pkts", "rx_pkts", "queue"]
        self.result_table_create(header_row)
        frame_size = 64
        tgen_input = []
        port = self.tester.get_local_port(self.dut_ports[0])
        payload = frame_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['tcp']
        flow1 = 'Ether(dst="%s")/IP(dst="%s", src="%s")/TCP()/("X"*%d)' % \
                (self.virtio_mac, self.virtio_ip2, self.virtio_ip1, payload)
        self.tester.scapy_append('wrpcap("%s/exceptional_path.pcap", %s)' % (self.out_path, flow1))
        self.tester.scapy_execute()
        tgen_input.append((port, port, "%s/exceptional_path.pcap" % self.out_path))
        for rate_value in range(20, -1, -1):
            rate_value = rate_value * 0.5
            vm_config = {'mac': {'dst': {'range': 1, 'step': 1, 'action': 'inc'}, }, }
            self.tester.pktgen.clear_streams()
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, rate_value, vm_config, self.tester.pktgen)
            options = {'duration': 5, 'rate': rate_value, 'delay': 5}
            result = self.tester.pktgen.measure_loss(stream_ids=streams, options=options)
            tx_pkts = result[1]
            rx_pkts = result[2]
            if tx_pkts - rx_pkts <= 20:
                break
        data_row = [frame_size, rate_value, tx_pkts, rx_pkts, self.queue]
        self.result_table_add(data_row)
        self.result_table_print()
        self.vhost_user.send_expect("quit", "#")
        self.verify(rate_value > 0, "The received package did not reach the expected value")

    def test_vhost_exception_path_TAP_original(self):
        self.get_pci_info_from_cfg()
        self.config_kernel_nic_host()
        self.launch_testpmd_exception_path()
        self.dut.get_session_output(timeout=2)
        time.sleep(5)
        # Get the virtio-net device name
        self.prepare_tap_device()
        self.testpmd_reset()
        self.dut.send_expect('ip netns exec ns1 iperf -s -i 1', '', 10)
        self.iperf = self.dut.new_session(suite="iperf")
        self.iperf.send_expect('rm /root/iperf_client.log', '#', 10)
        self.iperf.send_expect('iperf -c 1.1.1.8 -i 1 -t 10 > /root/iperf_client.log &', '', 180)
        time.sleep(30)
        self.dut.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.iperf)
        self.logger.info("TAP->virtio-user->Kernel_NIC %s " % (self.output_result))
        self.iperf.send_expect('rm /root/iperf_client.log', '#', 10)
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.close_session(self.iperf)

    def test_vhost_exception_path_NIC_original(self):
        self.get_pci_info_from_cfg()
        self.config_kernel_nic_host()
        self.launch_testpmd_exception_path()
        time.sleep(5)
        self.dut.get_session_output(timeout=2)
        self.prepare_tap_device()
        self.testpmd_reset()
        self.iperf = self.dut.new_session(suite="iperf")
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.iperf.send_expect('iperf -s -i 1', '', 180)
        self.dut.send_expect('ip netns exec ns1 iperf -c 1.1.1.2 -i 1 -t 10 > /root/iperf_client.log &', '', 10)
        time.sleep(30)
        self.iperf.send_expect('^C', '#', 10)
        self.iperf_result_verify(self.dut)
        self.dut.get_session_output(timeout=2)
        self.logger.info("Kernel_NIC<-virtio-user<-TAP %s " % (self.output_result))
        self.dut.send_expect('rm /root/iperf_client.log', '#', 10)
        self.vhost_user.send_expect("quit", "#", 120)
        self.dut.close_session(self.vhost_user)
        self.dut.send_expect("ip netns del ns1", "#")
        self.dut.close_session(self.iperf)

    def test_perf_vhost_single_queue(self):
        self.queue = 1
        self.launch_testpmd_vhost()
        self.set_route_table()
        self.send_and_verify_loss()

    def test_perf_vhost_multiple_queue(self):
        self.queue = 2
        self.launch_testpmd_vhost()
        self.set_route_table()
        self.send_and_verify_loss()

    def tear_down(self):
        #
        # Run after each test case.
        #
        self.dut.kill_all()
        self.dut.close_session(self.vhost_user)
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.dut.send_expect("killall -s INT qemu-system-x86_64", "#")
        self.dut.send_expect("rm -rf ./vhost-net", "#")
        time.sleep(2)
        if self.peer_pci_setup:
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -u %s" % (self.peer_pci), '# ', 30)
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -b %s %s" %
                (self.pci_drv, self.peer_pci), '# ', 30)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.unprepare_dpdk()
        if self.peer_pci_setup:
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -u %s" % (self.pci), '# ', 30)
            self.dut.send_expect(
                "./usertools/dpdk-devbind.py -b %s %s" %
                (self.pci_drv, self.pci), '# ', 30)
