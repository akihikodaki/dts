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

import re
import time
import string

import utils
from test_case import TestCase
from pmd_output import PmdOutput
from etgen import IxiaPacketGenerator
from settings import HEADER_SIZE

class TestVfL3fwd(TestCase, IxiaPacketGenerator):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVfL3fwd, self)
        self.verify(self.nic in ["fortville_spirit", "fortville25g", "fortville_eagle", "niantic"],
                    "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.requirt_ports_num = len(self.dut_ports)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]

        # Verify that enough ports are available
        self.verify(len(valports) == 2 or len(valports) == 4, "Port number must be 2 or 4.")
        # define vf's mac address
        self.vfs_mac = ["00:12:34:56:78:0%d" % (i+1) for i in valports]
        # get socket and cores
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/6C/1T", socket=self.socket)
        self.verify(self.cores is not None, "Requested 6 cores failed")

        # get test parameters: frames size, queues number
        self.perf_params = self.get_suite_cfg()['perf_params']
        self.frame_sizes = self.perf_params['frame_size']
        self.queue = self.perf_params['queue_number'][self.nic]

        self.l3fwd_methods = ['lpm']
        self.l3fwd_test_results = {'header': [], 'data': []}
        self.logger.info("Configure RX/TX descriptor to 2048, and re-build ./examples/l3fwd")
        self.dut.send_expect("sed -i -e 's/define RTE_TEST_RX_DESC_DEFAULT.*$/"
                             + "define RTE_TEST_RX_DESC_DEFAULT 2048/' ./examples/l3fwd/main.c", "#", 20)
        self.dut.send_expect("sed -i -e 's/define RTE_TEST_TX_DESC_DEFAULT.*$/"
                             + "define RTE_TEST_TX_DESC_DEFAULT 2048/' ./examples/l3fwd/main.c", "#", 20)
        out = self.dut.build_dpdk_apps("./examples/l3fwd")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

    def set_up(self):
        """
        Run before each test case.
        """
        self.setup_vf_env_flag = 0

    def setup_vf_env(self, host_driver='default'):
        """
        require enough PF ports,using kernel or dpdk driver, create 1 VF from each PF.
        """
        self.used_dut_port = [port for port in self.dut_ports]
        self.sriov_vfs_port = []
        for i in valports:
            if host_driver != '':
                self.dut.generate_sriov_vfs_by_port(self.used_dut_port[i], 1)
            else:
                self.dut.generate_sriov_vfs_by_port(self.used_dut_port[i], 1, host_driver)
            sriov_vfs_port = self.dut.ports_info[self.used_dut_port[i]]['vfs_port']
            self.sriov_vfs_port.append(sriov_vfs_port)
        # bind vf to vf driver
        try:
            for i in valports:
                for port in self.sriov_vfs_port[i]:
                    port.bind_driver(self.vf_driver)
            time.sleep(1)
            # set vf mac address.
            if host_driver == '':
                for i in valports:
                    pf_intf = self.dut.ports_info[i]['port'].get_interface_name()
                    self.dut.send_expect("ip link set %s vf 0 mac %s" % (pf_intf, self.vfs_mac[i]), "#")
            else:
                self.host_testpmd = PmdOutput(self.dut)
                eal_param = '--socket-mem=1024,1024 --file-prefix=pf'
                for i in valports:
                    eal_param += ' -b %s' % self.sriov_vfs_port[i][0].pci
                core_config = self.cores[:len(valports)]
                self.host_testpmd.start_testpmd(core_config, "", eal_param=eal_param)
                for i in valports:
                    self.host_testpmd.execute_cmd('set vf mac addr %d 0 %s' % (i, self.vfs_mac[i]))
                time.sleep(1)
            self.setup_vf_env_flag = 1
        except Exception as e:
            self.destroy_vf_env()
            raise Exception(e)

    def destroy_vf_env(self):
        """
        destroy the setup VFs
        """
        if getattr(self, 'host_testpmd', None):
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None
        for i in valports:
            if getattr(self, '%d' % self.used_dut_port[i] , None) != None:
                self.dut.destroy_sriov_vfs_by_port(self.used_dut_port[i])
                port = self.dut.ports_info[self.used_dut_port[i]]['port']
                port.bind_driver()
                self.used_dut_port[i] = None
        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()
        self.setup_vf_env_flag = 0

    def flows(self):
        """
        Return a list of packets that implements the flows described in l3fwd.
        """
        return [
            'IP(src="1.2.3.4",dst="192.18.1.0")',
            'IP(src="1.2.3.4",dst="192.18.1.1")',
            'IP(src="1.2.3.4",dst="192.18.0.0")',
            'IP(src="1.2.3.4",dst="192.18.0.1")',
            'IP(src="1.2.3.4",dst="192.18.3.0")',
            'IP(src="1.2.3.4",dst="192.18.3.1")',
            'IP(src="1.2.3.4",dst="192.18.2.0")',
            'IP(src="1.2.3.4",dst="192.18.2.1")']

    def create_pacap_file(self, frame_size):
        """
        Prepare traffic flow
        """
        dmac = self.vfs_mac
        smac = ["02:00:00:00:00:0%d" % i for i in valports]
        payload_size = frame_size - HEADER_SIZE['ip'] - HEADER_SIZE['eth']
        for _port in valports:
            flows = ['Ether(dst="%s", src="%s")/%s/("X"*%d)' % (dmac[_port], smac[_port], flow, payload_size) for
                     flow in self.flows()[_port*2:(_port + 1)*2]]
            self.tester.scapy_append('wrpcap("dst%d.pcap", [%s])' % (valports[_port], string.join(flows, ',')))
        self.tester.scapy_execute()

    def prepare_steam(self):
        """
        create streams for ports,one port one stream
        """
        tgen_input = []
        for rxPort in valports:
            if rxPort % len(valports) == 0 or rxPort % len(valports) == 2:
                txIntf = self.tester.get_local_port(valports[rxPort + 1])
                rxIntf = self.tester.get_local_port(valports[rxPort])
                tgen_input.append((txIntf, rxIntf, "dst%d.pcap" % valports[rxPort+1]))
            elif rxPort % len(valports) == 1 or rxPort % len(valports) == 3:
                txIntf = self.tester.get_local_port(valports[rxPort - 1])
                rxIntf = self.tester.get_local_port(valports[rxPort])
                tgen_input.append((txIntf, rxIntf, "dst%d.pcap" % valports[rxPort-1]))
        return tgen_input

    def perf_test(self, cmdline):
        """
        vf l3fwd performance test
        """
        l3fwd_session = self.dut.new_session()
        header_row = ["Frame", "mode", "Mpps", "%linerate"]
        self.l3fwd_test_results['header'] = header_row
        self.result_table_create(header_row)
        self.l3fwd_test_results['data'] = []
        for frame_size in self.frame_sizes:
            self.create_pacap_file(frame_size)

            for mode in self.l3fwd_methods:
                info = "Executing l3fwd using %s mode, %d ports, %d frame size.\n" % (mode, len(valports), frame_size)
                self.logger.info(info)
                if frame_size > 1518:
                    cmdline = cmdline + " --max-pkt-len %d" % frame_size
                l3fwd_session.send_expect(cmdline, "L3FWD:", 120)
                # send the traffic and Measure test
                tgenInput = self.prepare_steam()
                _, pps = self.tester.traffic_generator_throughput(tgenInput, rate_percent=100, delay=30)
                self.verify(pps > 0, "No traffic detected")
                pps /= 1000000.0
                linerate = self.wirespeed(self.nic, frame_size, len(valports))
                percentage = pps * 100 / linerate
                # Stop l3fwd
                l3fwd_session.send_expect("^C", "#")
                time.sleep(5)
                data_row = [frame_size, mode, str(pps), str(percentage)]
                self.result_table_add(data_row)
                self.l3fwd_test_results['data'].append(data_row)

        self.dut.close_session(l3fwd_session)
        self.result_table_print()

    def measure_vf_performance(self, host_driver='default'):
        """
        start l3fwd and run the perf test
        """
        self.setup_vf_env(host_driver)
        eal_param = ""
        for i in valports:
            eal_param += " -w " + self.sriov_vfs_port[i][0].pci
        port_mask = utils.create_mask(self.dut_ports)

        # for fvl40g, fvl25g, use 2c/2q per VF port for performance test ,
        # for fvl10g, nnt, use 1c/1q per VF port for performance test
        core_list = self.cores[-len(valports)*self.queue:]
        core_mask = utils.create_mask(core_list)
        self.logger.info("Executing Test Using cores: %s" % core_list)
        queue_config = ""
        m = 0
        for i in valports:
            for j in range(self.queue):
                queue_config += "({0}, {1}, {2})," .format(i, j, core_list[m])
                m += 1
        cmdline = "./examples/l3fwd/build/l3fwd -c {0} -n 4 {1} -- -p {2} --config '{3}' ". \
            format(core_mask, eal_param, port_mask, queue_config)
        self.perf_test(cmdline)

    def test_perf_kernel_pf_dpdk_vf_perf_host_only(self):

        self.measure_vf_performance(host_driver='')

    def test_perf_dpdk_pf_dpdk_vf_perf_host_only(self):

        self.measure_vf_performance(host_driver=self.vf_driver)

    def ip(self, port, frag, src, proto, tos, dst, chksum, len, options, version, flags, ihl, ttl, id):

        self.add_tcl_cmd("protocol config -name ip")
        self.add_tcl_cmd('ip config -sourceIpAddr "%s"' % src)
        self.add_tcl_cmd("ip config -sourceIpAddrMode ipRandom")
        self.add_tcl_cmd('ip config -destIpAddr "%s"' % dst)
        self.add_tcl_cmd("ip config -destIpAddrMode ipIdle")
        self.add_tcl_cmd("ip config -ttl %d" % ttl)
        self.add_tcl_cmd("ip config -totalLength %d" % len)
        self.add_tcl_cmd("ip config -fragment %d" % frag)
        self.add_tcl_cmd("ip config -ipProtocol ipV4ProtocolReserved255")
        self.add_tcl_cmd("ip config -identifier %d" % id)
        self.add_tcl_cmd("stream config -framesize %d" % (len + 18))
        self.add_tcl_cmd("ip set %d %d %d" % (self.chasId, port['card'], port['port']))

    def tear_down(self):

        if self.setup_vf_env_flag == 1:
            self.destroy_vf_env()
        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)

    def tear_down_all(self):
        pass
