#
# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Test loopback virtio-user server mode
"""
import utils
import time
import re
from test_case import TestCase


class TestLoopbackVirtioUserServerMode(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.core_config = "1S/6C/1T"
        self.queue_number = 1
        self.nb_cores = 1
        self.cores_num = len([n for n in self.dut.cores if int(n['socket'])
                          == 0])
        self.verify(self.cores_num >= 6,
                    "There has not enought cores to test this case")
        self.core_list = self.dut.get_core_list(self.core_config)
        self.core_list_user = self.core_list[0:3]
        self.core_list_host = self.core_list[3:6]
        self.core_mask_user = utils.create_mask(self.core_list_user)
        self.core_mask_host = utils.create_mask(self.core_list_host)

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT testpmd", "#")
        # Prepare the result table
        self.table_header = ["Mode", "Throughput(Mpps)", "Cycle"]
        self.result_table_create(self.table_header)

        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio_user = self.dut.new_session(suite="virtio-user")

    def lanuch_vhost_testpmd(self, queue_number=1, nb_cores=1, extern_params=""):
        """
        start testpmd on vhost
        """
        command_client = self.dut.target + "/app/testpmd " + \
                         " -n %d -c %s --socket-mem 1024,1024 " + \
                         " --legacy-mem --no-pci --file-prefix=vhost " + \
                         " --vdev 'net_vhost0,iface=vhost-net,client=1,queues=%d' " + \
                         " -- -i --rxq=%d --txq=%d --nb-cores=%d %s"
        command_line_client = command_client % (self.dut.get_memory_channels(),
                              self.core_mask_host, queue_number, queue_number,
                              queue_number, nb_cores, extern_params)
        self.vhost.send_expect(command_line_client, "testpmd> ", 120)
        self.vhost.send_expect("set fwd mac", "testpmd> ", 120)

    def lanuch_virtio_user_testpmd(self):
        """
        start testpmd of vhost user
        """
        command_line_user = self.dut.target + "/app/testpmd -n %d -c %s --socket-mem 1024,1024 " + \
                            "--legacy-mem --no-pci --file-prefix=virtio " + \
                            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues=1 " + \
                            " -- -i --rxq=1 --txq=1 --no-numa"
        command_line_user = command_line_user % (self.dut.get_memory_channels(),
                            self.core_mask_user)
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)

    def lanuch_vhost_testpmd_with_multi_queue(self, extern_params=""):
        """
        start testpmd with multi qeueue
        """
        self.lanuch_vhost_testpmd(self.queue_number, self.nb_cores, extern_params=extern_params)

    def lanuch_virtio_user_testpmd_with_multi_queue(self, mode, extern_params=""):
        """
        start testpmd of vhost user
        """
        command_line_user = self.dut.target + "/app/testpmd -n %d -c %s --socket-mem 1024,1024 " + \
                            "--legacy-mem --no-pci --file-prefix=virtio " + \
                            "--vdev=net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues=%d,%s " + \
                            " -- -i --tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip --nb-cores=%d --rxq=%d --txq=%d %s"
        command_line_user = command_line_user % (self.dut.get_memory_channels(),
                            self.core_mask_user, self.queue_number, mode, self.nb_cores,
                            self.queue_number, self.queue_number, extern_params)
        self.virtio_user.send_expect(command_line_user, "testpmd> ", 120)
        self.virtio_user.send_expect("set fwd mac", "testpmd> ", 120)

    def start_to_send_packets(self, session_rx, session_tx):
        """
        start the testpmd of vhost-user and virtio-user
        start to send packets
        """
        session_rx.send_expect("start", "testpmd> ", 30)
        session_tx.send_expect("start tx_first 32", "testpmd> ", 30)

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while(loop <= 5):
            out = self.vhost.send_expect("show port stats 0", "testpmd>", 60)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            if result == "0":
                break
            time.sleep(3)
            loop = loop + 1
        self.verify(result == "0", "port stop failed, it alse can recevie data after stop.")

    def check_port_link_status_after_port_restart(self):
        """
        check the link status after port restart
        """
        loop = 1
        while(loop <= 5):
            out = self.vhost.send_expect("show port info all", "testpmd> ", 120)
            port_status = re.findall("Link\s*status:\s*([a-z]*)", out)
            if("down" not in port_status):
                break
            time.sleep(3)
            loop = loop + 1

        self.verify("down" not in port_status, "port can not up after restart")

    def check_link_status(self, side, status):
        out = side.send_expect("show port info 0", "testpmd> ", 120)
        res = re.search("Link\s*status:\s*(\S*)", out)
        self.verify(res.group(1) == status,
            "The status not right on virtio side after vhost quit, status: %s" %
            res.group(1))

    def port_restart(self):
        self.vhost.send_expect("stop", "testpmd> ", 120)
        self.vhost.send_expect("port stop 0", "testpmd> ", 120)
        self.check_port_throughput_after_port_stop()
        self.vhost.send_expect("clear port stats all", "testpmd> ", 120)
        self.vhost.send_expect("port start 0", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost.send_expect("start tx_first 32", "testpmd> ", 120)

    def relanuch_vhost_testpmd_with_multi_queue(self):
        self.vhost.send_expect("quit", "#", 60)
        self.check_link_status(self.virtio_user, "down")
        self.lanuch_vhost_testpmd_with_multi_queue()

    def relanuch_virtio_testpmd_with_multi_queue(self, mode, extern_params=""):
        self.virtio_user.send_expect("quit", "#", 60)
        self.check_link_status(self.vhost, "down")
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode, extern_params)

    def calculate_avg_throughput(self, case_info, cycle):
        """
        calculate the average throughput
        """
        results = 0.0
        results_row = []
        for i in range(10):
            out = self.vhost.send_expect("show port stats all", "testpmd>", 60)
            time.sleep(5)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 0, "port can not receive packets")

        results_row.append(case_info)
        results_row.append(Mpps)
        results_row.append(cycle)
        self.result_table_add(results_row)

    def check_packets_of_each_queue(self):
        """
        check all the queue has receive packets
        """
        out = self.vhost.send_expect("stop", "testpmd> ", 60)
        for queue_index in range(0, self.queue_number):
            queue = "Queue= %d" % queue_index
            index = out.find(queue)
            rx = re.search("RX-packets:\s*(\d*)", out[index:])
            tx = re.search("TX-packets:\s*(\d*)", out[index:])
            rx_packets = int(rx.group(1))
            tx_packets = int(tx.group(1))
            self.verify(rx_packets > 0 and tx_packets > 0,
                   "The queue %d rx-packets or tx-packets is 0, rx-packets:%s, tx-packets:%s" %
                   (queue_index, rx_packets, tx_packets))

    def close_all_testpmd(self):
        """
        close testpmd about vhost-user and virtio-user
        """
        self.vhost.send_expect("quit", "#", 60)
        self.virtio_user.send_expect("quit", "#", 60)

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio_user)

    def test_server_mode_launch_vhost_first(self):
        """
        basic test for virtio-user server mode, launch vhost first
        """
        self.queue_number = 1
        self.nb_cores = 1
        self.lanuch_vhost_testpmd()
        self.lanuch_virtio_user_testpmd()
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("lanuch vhost first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_launch_virtio_first(self):
        """
        basic test for virtio-user server mode, launch virtio-user first
        """
        self.queue_number = 1
        self.nb_cores = 1
        self.lanuch_virtio_user_testpmd()
        self.lanuch_vhost_testpmd()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput("lanuch virtio first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_multi_queue_reconnect_from_vhost_side_with_virtio11(self):
        """
        reconnect virtio-user from the vhost side with multi_queues
        """
        self.queue_number = 2
        self.nb_cores = 2
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=1"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("reconnet from vhost with virtio1.1",
                                      "before reconnet")

        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput("reconnet from vhost with virtio1.1",
                                      "after reconnet")
        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_multi_queue_reconnect_from_vhost_side_with_virtio10(self):
        """
        reconnect virtio-user from the vhost side with multi_queues
        """
        self.queue_number = 2
        self.nb_cores = 2
        mode = "packed_vq=0,in_order=1,mrg_rxbuf=1"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("reconnet from vhost with virtio1.0",
                                      "before reconnet")

        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput("reconnet from vhost with virtio1.0",
                                      "after reconnet")
        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_multi_queue_reconnect_from_virito_side_with_virtio10(self):
        """
        reconnect vhost-user from the virtio side with vhost/virtio1.0 loopback multi_queues
        """
        self.queue_number = 2
        self.nb_cores = 2
        mode = "packed_vq=0,in_order=1,mrg_rxbuf=1"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("reconnet from virito with virtio1.0",
                                      "before reconnet")

        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("reconnet from virito with virtio1.0",
                                      "after reconnet")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_port_start_stop_at_vhost(self):
        """
        port start/stop at vhost side with server mode multi queues
        """
        self.queue_number = 2
        self.nb_cores = 2
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=1"
        extern_params = "--txd=1024 --rxd=1024"
        self.lanuch_vhost_testpmd_with_multi_queue(extern_params=extern_params)
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput("vhost port restart", "before restart")

        self.port_restart()
        self.calculate_avg_throughput("vhost port restart", "after restart")
        self.result_table_print()

        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT testpmd", "#")
        self.close_all_session()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
