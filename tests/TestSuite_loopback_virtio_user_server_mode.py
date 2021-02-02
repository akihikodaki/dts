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
from pmd_output import PmdOutput
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
        self.path=self.dut.apps_name['test-pmd']
        self.testpmd_name = self.path.split("/")[-1]

    def set_up(self):
        """
        Run before each test case.
        """
        # Clean the execution ENV
        self.dut.send_expect("rm -rf ./vhost-net*", "#")
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        # Prepare the result table
        self.table_header = ["Mode", "Pkt_size", "Throughput(Mpps)",
                            "Queue Number", "Cycle"]
        self.result_table_create(self.table_header)

        self.vhost = self.dut.new_session(suite="vhost")
        self.virtio_user = self.dut.new_session(suite="virtio-user")
        self.vhost_pmd = PmdOutput(self.dut, self.vhost)
        self.virtio_user_pmd = PmdOutput(self.dut, self.virtio_user)

    def lanuch_vhost_testpmd(self, queue_number=1, nb_cores=1, extern_params=""):
        """
        start testpmd on vhost
        """
        eal_params = "--vdev 'net_vhost0,iface=vhost-net,client=1,queues={}'".format(queue_number)
        param = "--rxq={} --txq={} --nb-cores={} {}".format(queue_number, queue_number, nb_cores, extern_params)
        self.vhost_pmd.start_testpmd(self.core_list_host, param=param, no_pci=True, ports=[], eal_param=eal_params, prefix='vhost', fixed_prefix=True)
        self.vhost_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    @property
    def check_2M_env(self):
        out = self.dut.send_expect("cat /proc/meminfo |grep Hugepagesize|awk '{print($2)}'", "# ")
        return True if out == '2048' else False

    def lanuch_virtio_user_testpmd(self, args, set_fwd_mac=True, expected='testpmd> '):
        """
        start testpmd of vhost user
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues=1,{}'".format(args["version"])
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if 'vectorized_path' in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "--rxq=1 --txq=1 --no-numa"
        self.virtio_user_pmd.start_testpmd(cores=self.core_list_user, param=param, eal_param=eal_param, \
                no_pci=True, ports=[], prefix="virtio", fixed_prefix=True, expected=expected)
        if set_fwd_mac:
            self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    def lanuch_vhost_testpmd_with_multi_queue(self, extern_params=""):
        """
        start testpmd with multi qeueue
        """
        self.lanuch_vhost_testpmd(self.queue_number, self.nb_cores, extern_params=extern_params)

    def lanuch_virtio_user_testpmd_with_multi_queue(self, mode, extern_params=""):
        """
        start testpmd of vhost user
        """
        eal_param = "--vdev 'net_virtio_user0,mac=00:01:02:03:04:05,path=vhost-net,server=1,queues={},{}'".format(self.queue_number, mode)
        if self.check_2M_env:
            eal_param += " --single-file-segments"
        if 'vectorized_path' in self.running_case:
            eal_param += " --force-max-simd-bitwidth=512"
        param = "{} --nb-cores={} --rxq={} --txq={}".format(extern_params, self.nb_cores, self.queue_number, self.queue_number)
        self.virtio_user_pmd.start_testpmd(cores=self.core_list_user, param=param, eal_param=eal_param, \
                no_pci=True, ports=[], prefix="virtio", fixed_prefix=True)
        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)

    def start_to_send_packets(self, session_rx, session_tx):
        """
        start the testpmd of vhost-user and virtio-user
        start to send packets
        """
        session_rx.send_command("start", 3)
        session_tx.send_expect("start tx_first 32", "testpmd> ", 30)

    def check_port_throughput_after_port_stop(self):
        """
        check the throughput after port stop
        """
        loop = 1
        while(loop <= 5):
            out = self.vhost_pmd.execute_cmd("show port stats 0", "testpmd>", 60)
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
            out = self.vhost_pmd.execute_cmd("show port info all", "testpmd> ", 120)
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
        self.vhost_pmd.execute_cmd("stop", "testpmd> ", 120)
        self.vhost_pmd.execute_cmd("port stop 0", "testpmd> ", 120)
        self.check_port_throughput_after_port_stop()
        self.vhost_pmd.execute_cmd("clear port stats all", "testpmd> ", 120)
        self.vhost_pmd.execute_cmd("port start 0", "testpmd> ", 120)
        self.check_port_link_status_after_port_restart()
        self.vhost_pmd.execute_cmd("start tx_first 32", "testpmd> ", 120)

    def relanuch_vhost_testpmd_with_multi_queue(self):
        self.vhost_pmd.execute_cmd("quit", "#", 60)
        self.check_link_status(self.virtio_user, "down")
        self.lanuch_vhost_testpmd_with_multi_queue()

    def relanuch_virtio_testpmd_with_multi_queue(self, mode, extern_params=""):
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)
        self.check_link_status(self.vhost, "down")
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode, extern_params)

    def calculate_avg_throughput(self, case_info, cycle):
        """
        calculate the average throughput
        """
        results = 0.0
        results_row = []
        self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
        for i in range(10):
            out = self.vhost_pmd.execute_cmd("show port stats all", "testpmd>", 60)
            time.sleep(1)
            lines = re.search("Rx-pps:\s*(\d*)", out)
            result = lines.group(1)
            results += float(result)
        Mpps = results / (1000000 * 10)
        self.verify(Mpps > 5, "port can not receive packets")

        results_row.append(case_info)
        results_row.append('64')
        results_row.append(Mpps)
        results_row.append(self.queue_number)
        results_row.append(cycle)
        self.result_table_add(results_row)

    def check_packets_of_each_queue(self):
        """
        check all the queue has receive packets
        """
        out = self.vhost_pmd.execute_cmd("stop", "testpmd> ", 60)
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
        self.vhost_pmd.execute_cmd("quit", "#", 60)
        self.virtio_user_pmd.execute_cmd("quit", "#", 60)

    def close_all_session(self):
        """
        close session of vhost-user and virtio-user
        """
        self.dut.close_session(self.vhost)
        self.dut.close_session(self.virtio_user)

    def test_server_mode_launch_virtio_first(self):
        """
        basic test for virtio-user server mode, launch virtio-user first
        """
        self.queue_number = 1
        self.nb_cores = 1
        virtio_pmd_arg = {"version": "packed_vq=0,in_order=0,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.lanuch_virtio_user_testpmd(virtio_pmd_arg, set_fwd_mac=False, expected='waiting for client connection...')
        self.lanuch_vhost_testpmd()
        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput("lanuch virtio first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_launch_virtio11_first(self):
        """
        basic test for virtio-user server mode, launch virtio-user first
        """
        self.queue_number = 1
        self.nb_cores = 1
        virtio_pmd_arg = {"version": "packed_vq=1,in_order=0,mrg_rxbuf=1",
                          "path": "--tx-offloads=0x0 --enable-hw-vlan-strip"}
        self.lanuch_virtio_user_testpmd(virtio_pmd_arg, set_fwd_mac=False, expected='waiting for client connection...')
        self.lanuch_vhost_testpmd()
        self.virtio_user_pmd.execute_cmd("set fwd mac", "testpmd> ", 120)
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput("lanuch virtio first", "")
        self.result_table_print()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_mergeable_path(self):
        """
        reconnect test with virtio 1.1 mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.1 mergeable path'
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_non_mergeable_path(self):
        """
        reconnect test with virtio 1.1 non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.1 non_mergeable path'
        mode = "packed_vq=1,in_order=0,mrg_rxbuf=0"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_mergeable_path(self):
        """
        reconnect test with virtio 1.1 inorder mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.1 inorder mergeable path'
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_non_mergeable_path(self):
        """
        reconnect test with virtio 1.1 inorder non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.1 non_mergeable path'
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        extern_params = '--rx-offloads=0x10 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio11_inorder_vectorized_path(self):
        """
        reconnect test with virtio 1.1 inorder non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.1 non_mergeable path'
        mode = "packed_vq=1,in_order=1,mrg_rxbuf=0,vectorized=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnect from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_inorder_mergeable_path(self):
        """
        reconnect test with virtio 1.0 inorder mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.0 inorder mergeable path'
        mode = "in_order=1,mrg_rxbuf=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_inorder_non_mergeable_path(self):
        """
        reconnect test with virtio 1.0 inorder non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.0 inorder non_mergeable path'
        mode = "in_order=1,mrg_rxbuf=0"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_mergeable_path(self):
        """
        reconnect test with virtio 1.0 mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.0 mergeable path'
        mode = "in_order=0,mrg_rxbuf=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_non_mergeable_path(self):
        """
        reconnect test with virtio 1.0 non_mergeable path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.0 non_mergeable path'
        mode = "in_order=0,mrg_rxbuf=0,vectorized=1"
        extern_params = '--tx-offloads=0x0 --enable-hw-vlan-strip --rss-ip'
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode, extern_params=extern_params)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def test_server_mode_reconnect_with_virtio10_vector_rx_path(self):
        """
        reconnect test with virtio 1.0 vector_rx path and server mode
        """
        self.queue_number = 2
        self.nb_cores = 2
        case_info = 'virtio1.0 vector_rx path'
        mode = "in_order=0,mrg_rxbuf=0,vectorized=1"
        self.lanuch_vhost_testpmd_with_multi_queue()
        self.lanuch_virtio_user_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "before reconnet")

        # reconnet from vhost
        self.logger.info('now reconnet from vhost')
        self.relanuch_vhost_testpmd_with_multi_queue()
        self.start_to_send_packets(self.virtio_user, self.vhost)
        self.calculate_avg_throughput(case_info, "reconnet from vhost")

        # reconnet from virtio
        self.logger.info('now reconnet from virtio_user')
        self.relanuch_virtio_testpmd_with_multi_queue(mode=mode)
        self.start_to_send_packets(self.vhost, self.virtio_user)
        self.calculate_avg_throughput(case_info, "reconnet from virtio_user")

        # port restart
        self.logger.info('now vhost port restart')
        self.port_restart()
        self.calculate_avg_throughput(case_info, "after port restart")

        self.result_table_print()
        self.check_packets_of_each_queue()
        self.close_all_testpmd()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("killall -s INT %s" % self.testpmd_name, "#")
        self.close_all_session()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
