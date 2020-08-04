# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
Multi-process Test.
"""

import utils
import time
import os

executions = []
from test_case import TestCase
from pktgen import PacketGeneratorHelper


class TestMultiprocess(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Multiprocess prerequisites.
        Requirements:
            OS is not freeBSD
            DUT core number >= 4
            multi_process build pass
        """
        # self.verify('bsdapp' not in self.target, "Multiprocess not support freebsd")

        self.verify(len(self.dut.get_all_cores()) >= 4, "Not enough Cores")
        self.tester.extend_external_packet_generator(TestMultiprocess, self)
        self.dut_ports = self.dut.get_ports()
        self.socket = self.dut.get_numa_id(self.dut_ports[0])

        out = self.dut.build_dpdk_apps("./examples/multi_process/client_server_mp/mp_client")
        self.verify('Error' not in out, "Compilation mp_client failed")
        out = self.dut.build_dpdk_apps("./examples/multi_process/client_server_mp/mp_server")
        self.verify('Error' not in out, "Compilation mp_server failed")
        out = self.dut.build_dpdk_apps("./examples/multi_process/simple_mp")
        self.verify('Error' not in out, "Compilation simple_mp failed")
        out = self.dut.build_dpdk_apps("./examples/multi_process/symmetric_mp")
        self.verify('Error' not in out, "Compilation symmetric_mp failed")

        self.app_mp_client = self.dut.apps_name['mp_client']
        self.app_mp_server = self.dut.apps_name['mp_server']
        self.app_simple_mp = self.dut.apps_name['simple_mp']
        self.app_symmetric_mp = self.dut.apps_name['symmetric_mp']

        executions.append({'nprocs': 1, 'cores': '1S/1C/1T', 'pps': 0})
        executions.append({'nprocs': 2, 'cores': '1S/1C/2T', 'pps': 0})
        executions.append({'nprocs': 2, 'cores': '1S/2C/1T', 'pps': 0})
        executions.append({'nprocs': 4, 'cores': '1S/2C/2T', 'pps': 0})
        executions.append({'nprocs': 4, 'cores': '1S/4C/1T', 'pps': 0})
        executions.append({'nprocs': 8, 'cores': '1S/4C/2T', 'pps': 0})

        self.eal_param = ""
        for i in self.dut_ports:
            self.eal_param += " -w %s" % self.dut.ports_info[i]['pci']

        # start new session to run secondary
        self.session_secondary = self.dut.new_session()

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_multiprocess_simple_mpbasicoperation(self):
        """
        Basic operation.
        """
        # Send message from secondary to primary
        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=primary" % (coremask),
                             "Finished Process Init", 100)
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.session_secondary.send_expect(
            self.app_simple_mp + " -n 1 -c %s --proc-type=secondary" % (coremask), "Finished Process Init",
            100)

        self.session_secondary.send_expect("send hello_primary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")
        self.verify("Received 'hello_primary'" in out, "Message not received on primary process")
        # Send message from primary to secondary
        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(
            self.app_simple_mp + " -n 1 -c %s --proc-type=primary " % (coremask), "Finished Process Init", 100)
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=secondary" % (coremask),
                             "Finished Process Init", 100)
        self.session_secondary.send_expect("send hello_secondary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")

        self.verify("Received 'hello_secondary'" in out,
                    "Message not received on primary process")

    def test_multiprocess_simple_mploadtest(self):
        """
        Load test of Simple MP application.
        """

        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=primary" % (coremask),
                                           "Finished Process Init", 100)
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=secondary" % (coremask),
                             "Finished Process Init", 100)
        stringsSent = 0
        for line in open('/usr/share/dict/words', 'r').readlines():
            line = line.split('\n')[0]
            self.dut.send_expect("send %s" % line, ">")
            stringsSent += 1
            if stringsSent == 3:
                break

        time.sleep(5)
        self.dut.send_expect("quit", "# ")
        self.session_secondary.send_expect("quit", "# ")

    def test_multiprocess_simple_mpapplicationstartup(self):
        """
        Test use of Auto for Application Startup.
        """

        # Send message from secondary to primary (auto process type)
        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        out = self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=auto " % (coremask),
                                   "Finished Process Init", 100)
        self.verify("EAL: Auto-detected process type: PRIMARY" in out, "The type of process (PRIMARY) was not detected properly")
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.session_secondary.send_expect(
            self.app_simple_mp + " -n 1 -c %s --proc-type=auto" % (coremask), "Finished Process Init", 100)
        self.verify("EAL: Auto-detected process type: SECONDARY" in out,
                    "The type of process (SECONDARY) was not detected properly")

        self.session_secondary.send_expect("send hello_primary", ">")
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")
        self.verify("Received 'hello_primary'" in out, "Message not received on primary process")

        # Send message from primary to secondary (auto process type)
        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        out = self.session_secondary.send_expect(
            self.app_simple_mp + " -n 1 -c %s --proc-type=auto" % (coremask), "Finished Process Init", 100)
        self.verify("EAL: Auto-detected process type: PRIMARY" in out, "The type of process (PRIMARY) was not detected properly")
        time.sleep(20)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s --proc-type=auto" % (coremask),
                                   "Finished Process Init", 100)
        self.verify("EAL: Auto-detected process type: SECONDARY" in out, "The type of process (SECONDARY) was not detected properly")
        self.session_secondary.send_expect("send hello_secondary", ">", 100)
        out = self.dut.get_session_output()
        self.session_secondary.send_expect("quit", "# ")
        self.dut.send_expect("quit", "# ")

        self.verify("Received 'hello_secondary'" in out,
                    "Message not received on primary process")

    def test_multiprocess_simple_mpnoflag(self):
        """
        Multiple processes without "--proc-type" flag.
        """

        cores = self.dut.get_core_list('1S/2C/1T', socket=self.socket)
        coremask = utils.create_mask(cores)
        self.session_secondary.send_expect(self.app_simple_mp + " -n 1 -c %s -m 64" % (coremask),
                                           "Finished Process Init", 100)
        coremask = hex(int(coremask, 16) * 0x10).rstrip("L")
        out = self.dut.send_expect(self.app_simple_mp + " -n 1 -c %s" % (coremask), "# ", 100)

        self.verify("Is another primary process running" in out,
                    "No other primary process detected")

        self.session_secondary.send_expect("quit", "# ")

    def test_perf_multiprocess_performance(self):
        """
        Benchmark Multiprocess performance.
        # """
        packet_count = 16
        self.dut.send_expect("fg", "# ")
        txPort = self.tester.get_local_port(self.dut_ports[0])
        rxPort = self.tester.get_local_port(self.dut_ports[1])
        mac = self.tester.get_mac(txPort)
        dmac = self.dut.get_mac_address(self.dut_ports[0])
        tgenInput = []

        # create mutative src_ip+dst_ip package
        for i in range(packet_count):
            package = r'flows = [Ether(src="%s", dst="%s")/IP(src="192.168.1.%d", dst="192.168.1.%d")/("X"*26)]' % (mac, dmac, i + 1, i + 2)
            self.tester.scapy_append(package)
            pcap = os.sep.join([self.output_path, "test_%d.pcap"%i])
            self.tester.scapy_append('wrpcap("%s", flows)' % pcap)
            tgenInput.append([txPort, rxPort, pcap])
        self.tester.scapy_execute()

        # run multiple symmetric_mp process
        validExecutions = []
        for execution in executions:
            if len(self.dut.get_core_list(execution['cores'])) == execution['nprocs']:
                validExecutions.append(execution)

        portMask = utils.create_mask(self.dut_ports)

        for n in range(len(validExecutions)):
            execution = validExecutions[n]
            # get coreList form execution['cores']
            coreList = self.dut.get_core_list(execution['cores'], socket=self.socket)
            # to run a set of symmetric_mp instances, like test plan
            dutSessionList = []
            for index in range(len(coreList)):
                dut_new_session = self.dut.new_session()
                dutSessionList.append(dut_new_session)
                # add -w option when tester and dut in same server
                dut_new_session.send_expect(
                    self.app_symmetric_mp + " -c %s --proc-type=auto %s -- -p %s --num-procs=%d --proc-id=%d" % (
                        utils.create_mask([coreList[index]]), self.eal_param, portMask, execution['nprocs'], index), "Finished Process Init")

            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100, None, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

            execution['pps'] = pps

            # close all symmetric_mp process
            self.dut.send_expect("killall symmetric_mp", "# ")
            # close all dut sessions
            for dut_session in dutSessionList:
                self.dut.close_session(dut_session)

        # get rate and mpps data
        for n in range(len(executions)):
            self.verify(executions[n]['pps'] is not 0, "No traffic detected")
        self.result_table_create(['Num-procs', 'Sockets/Cores/Threads', 'Num Ports', 'Frame Size', '%-age Line Rate', 'Packet Rate(mpps)'])

        for execution in validExecutions:
            self.result_table_add(
                [execution['nprocs'], execution['cores'], 2, 64, execution['pps'] / float(100000000 / (8 * 84)), execution['pps'] / float(1000000)])

        self.result_table_print()

    def test_perf_multiprocess_client_serverperformance(self):
        """
        Benchmark Multiprocess client-server performance.
        """
        self.dut.kill_all()
        self.dut.send_expect("fg", "# ")
        txPort = self.tester.get_local_port(self.dut_ports[0])
        rxPort = self.tester.get_local_port(self.dut_ports[1])
        mac = self.tester.get_mac(txPort)

        self.tester.scapy_append('dmac="%s"' % self.dut.get_mac_address(self.dut_ports[0]))
        self.tester.scapy_append('smac="%s"' % mac)
        self.tester.scapy_append('flows = [Ether(src=smac, dst=dmac)/IP(src="192.168.1.1", dst="192.168.1.1")/("X"*26)]')

        pcap = os.sep.join([self.output_path, "test.pcap"])
        self.tester.scapy_append('wrpcap("%s", flows)' % pcap)
        self.tester.scapy_execute()

        validExecutions = []
        for execution in executions:
            if len(self.dut.get_core_list(execution['cores'])) == execution['nprocs']:
                validExecutions.append(execution)

        for execution in validExecutions:
            coreList = self.dut.get_core_list(execution['cores'], socket=self.socket)
            # get core with socket parameter to specified which core dut used when tester and dut in same server
            coreMask = utils.create_mask(self.dut.get_core_list('1S/1C/1T', socket=self.socket))
            portMask = utils.create_mask(self.dut_ports)
            # specified mp_server core and add -w option when tester and dut in same server
            self.dut.send_expect(self.app_mp_server + " -n %d -c %s %s -- -p %s -n %d" % (
                self.dut.get_memory_channels(), coreMask, self.eal_param, portMask, execution['nprocs']), "Finished Process Init", 20)
            self.dut.send_expect("^Z", "\r\n")
            self.dut.send_expect("bg", "# ")

            for n in range(execution['nprocs']):
                time.sleep(5)
                # use next core as mp_client core, different from mp_server
                coreMask = utils.create_mask([str(int(coreList[n]) + 1)])
                self.dut.send_expect(self.app_mp_client + " -n %d -c %s --proc-type=secondary %s -- -n %d" % (
                    self.dut.get_memory_channels(), coreMask, self.eal_param, n), "Finished Process Init")
                self.dut.send_expect("^Z", "\r\n")
                self.dut.send_expect("bg", "# ")

            tgenInput = []
            tgenInput.append([txPort, rxPort, pcap])

            # clear streams before add new streams
            self.tester.pktgen.clear_streams()
            # run packet generator
            streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100,
                                                                     None, self.tester.pktgen)
            _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)

            execution['pps'] = pps
            self.dut.kill_all()
            time.sleep(5)

        for n in range(len(executions)):
            self.verify(executions[n]['pps'] is not 0, "No traffic detected")

        self.result_table_create(
            ['Server threads', 'Server Cores/Threads', 'Num-procs', 'Sockets/Cores/Threads', 'Num Ports', 'Frame Size', '%-age Line Rate',
             'Packet Rate(mpps)'])

        for execution in validExecutions:
            self.result_table_add([1, '1S/1C/1T', execution['nprocs'], execution['cores'], 2, 64, execution['pps'] / float(100000000 / (8 * 84)),
                                   execution['pps'] / float(1000000)])

        self.result_table_print()

    def set_fields(self):
        ''' set ip protocol field behavior '''
        fields_config = {
            'ip': {
                'src': {'range': 64, 'action': 'inc'},
                'dst': {'range': 64, 'action': 'inc'},
            }, }

        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        pass
