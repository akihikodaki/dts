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

import time
import os
import re
import random
import string
import utils
from test_case import TestCase
from packet import Packet


class TestMultiplePthread(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.verify(self.dut.get_os_type() == 'linux', "Test suite currently only supports Linux platforms")
        self.dut_ports = self.dut.get_ports(self.nic)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        # Verify that enough ports are available
        self.verify(len(valports) >= 1, "Insufficient ports for testing")
        # get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/8C/1T", socket=self.socket)
        self.verify(self.cores is not None, "Requested 8 cores failed")
        self.out_view = {'header': [], 'data': []}

    def set_up(self):
        """
        Run before each test case.
        """
        self.send_sessions = []

    def send_packet(self):
        """
        Send packets continuous.
        """
        for index in valports:
            localPort = self.tester.get_local_port(index)
            iface = self.tester.get_interface(localPort)
            pcap_str = 'Ether()/IP(src="1.2.3.4", dst="192.168.0.%d")' % (index)
            self.pkt = Packet(pcap_str)
            intf = self.pkt.send_pkt_bg(crb=self.tester, tx_port=iface)
            self.send_sessions.append(intf)

    def get_cores_statistic(self, cmdline):
        """
        Get cpu and thread statistics.
        """
        mutiple_pthread_session = self.dut.new_session()
        out = mutiple_pthread_session.send_expect("ps -C testpmd -L -opid,tid,%cpu,psr,args", "#", 20)
        m = cmdline.replace('"', '', 2)
        out_list = out.split(m)
        mutiple_pthread_session.send_expect("^C", "#")
        self.dut.close_session(mutiple_pthread_session)
        return out_list

    def verify_before_send_packets(self, out_list):
        """
        handle out info before send packets and recode the status.
        """
        for data in out_list:
            if data != '':
                data_row = re.findall(r'[\d\.]+', data)
                if data_row[0] == data_row[1]:
                    self.verify(float(data_row[2]) > 0, "master thread are not running")
                    # add data to the table
                self.result_table_add(data_row)
                self.out_view['data'].append(data_row)

    def verify_after_send_packets(self, out_list, lcore_list):
        """
        handle out info after send packets and verify the core's status.
        """
        for data in out_list:
            if data != '':
                data_row = re.findall(r'[\d\.]+', data)
                for lcore in lcore_list:
                    if data_row[3] == lcore:
                        self.verify(float(data_row[2]) > 0, "TID:%s not running" % data_row[1])
                self.result_table_add(data_row)
                self.out_view['data'].append(data_row)
        # print table
        self.result_table_print()

    def multiple_pthread_test(self, lcores, cpu_list, lcore_list):
        """
        multiple pthread test according to lcores, cpus, etc.
        """
        header_row = ["PID", "TID", "%CPU", "PSRF"]
        self.out_view['header'] = header_row
        self.result_table_create(header_row)
        self.out_view['data'] = []

        # Allocate enough streams based on the number of CPUs
        if len(cpu_list) > 2:
            queue_num = len(cpu_list)
            cmdline = './%s/app/testpmd --lcores="%s" -n 4 -- -i --txq=%d --rxq=%d' % (self.target, lcores, queue_num, queue_num)
        else:
            cmdline = './%s/app/testpmd --lcores="%s" -n 4 -- -i' % (self.target, lcores)
        # start application
        self.dut.send_expect(cmdline, "testpmd", 60)

        out_list = self.get_cores_statistic(cmdline)
        self.verify_before_send_packets(out_list)

        # set testpmd corelist
        m = ""
        for cpu in cpu_list:
            m += "%s," % cpu
        setline = "set corelist %s" % m[:-1]
        self.dut.send_expect(setline, "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        out = self.dut.send_expect("show config fwd", "testpmd> ")
        # check fwd config
        if len(cpu_list) >= 2:
            for core in cpu_list[:2]:
                self.verify('Logical Core %s' % core in out, "set corelist config failed")
        else:
            for core in cpu_list:
                self.verify('Logical Core %s' % core in out, "set corelist config failed")
        self.send_packet()
        # get cpu statictis and verify the result
        out_list = self.get_cores_statistic(cmdline)
        self.verify_after_send_packets(out_list, lcore_list)
        # quit application
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_basic_operation(self):
        """
        Test an basic operation.
        """
        # prepare cmdline
        n = random.sample(self.cores, 5)
        n.sort()
        lcores = "%s@%s,(%s,%s)@%s" % (n[0], n[1], n[2], n[3], n[4])
        self.multiple_pthread_test(lcores, n[2:4], [n[1], n[4]])

    def test_positive(self):
        """
        Test an random parameter from an defined table which has a couple of valid lcore parameters.
        """
        n = self.cores
        CONFIG_RTE_MAX_LCORE = 128
        test_list = [
                     {"lcores": "(%s,%s)@(%s,%s)" % (n[0], CONFIG_RTE_MAX_LCORE-1, n[1], n[2]),
                      "cpu_list":[CONFIG_RTE_MAX_LCORE-1],
                      "core_list":n[1:3]},
                     {"lcores": "%s@%s,(%s,%s)@(%s,%s,%s,%s)" % (n[0], n[1], n[2], n[3], n[4], n[5], n[6], n[7]),
                      "cpu_list":n[2:4],
                      "core_list":n[4:]},
                     {"lcores": "(%s,%s,%s,%s)@(%s,%s)" % (n[0], n[1], n[2], n[3], n[4], n[5]),
                      "cpu_list":n[1:4],
                      "core_list":n[4:6]},
                     {"lcores": "%s,(%s,%s,%s)@%s" % (n[0], n[1], n[2], n[3], n[4]),
                      "cpu_list":n[1:4],
                      "core_list":n[4:5]},
                     {"lcores": "(%s,%s,%s,%s,%s)@(%s,%s)" % (n[0], n[1], n[2], n[3], n[4], n[5], n[6]),
                      "cpu_list":n[1:5],
                      "core_list":n[5:7]},
                     {"lcores": "%s,%s@(%s,%s,%s,%s,%s,%s),(%s,%s,%s)@%s,(%s,%s)"
                                % (n[0], n[1], n[0], n[1], n[2], n[3], n[4], n[5], n[2], n[3], n[5], n[4], n[6], n[7]),
                      "cpu_list":[n[1], n[2], n[3], n[5]],
                      "core_list":n[1:6]}
                     ]
        params_list = random.sample(test_list, 1)
        params = params_list[0]
        self.multiple_pthread_test(params["lcores"], params["cpu_list"], params["core_list"])

    def test_negative(self):
        """
        Test an random parameter from an defined table which has a couple of invalid lcore parameters.
        """
        cmdline_list = ["./%s/app/testpmd --lcores='(0-,4-7)@(4,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(-1,4-7)@(4,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7-9)@(4,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,abcd)@(4,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)@(1-,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)@(-1,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)@(4,5-8-9)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)@(abc,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)@(4,xyz)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0,4-7)=(8,9)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='2,3 at 4,(0-1,,4))' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='[0-,4-7]@(4,5)' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='(0-,4-7)@[4,5]' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='3-4 at 3,2 at 5-6' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='2,,3''2--3' -n 4 -- -i",
                        "./%s/app/testpmd --lcores='2,,,3''2--3' -n 4 -- -i"]

        cmdline = random.sample(cmdline_list, 1)
        out = self.dut.send_expect(cmdline[0] % self.target, "#", 60)
        self.verify("invalid parameter" in out, "it's a valid parameter")

    def tear_down(self):
        """
        Run after each test case.
        """
        if len(self.send_sessions) != 0:
            self.pkt.stop_send_pkt_bg(self.tester, self.send_sessions)
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
