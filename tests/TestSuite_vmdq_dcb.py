# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
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

Test  example vmdq_dcb.

"""
import utils
import os
import re
import random
from test_case import TestCase
from settings import HEADER_SIZE
from pktgen import PacketGeneratorHelper


class TestVmdqDcb(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.tester.extend_external_packet_generator(TestVmdqDcb, self)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.socket = self.dut.get_numa_id(self.dut_ports[0])
        self.frame_size = 64
        self.destmac_port = "52:54:00:12:00:00"

        # get dts output path to place pcap files
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(
                                os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])

        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

        self.prios = range(8)
        self.create_pcaps(self.prios)

    def set_up(self):
        """
        Run before each test case.
        """
        if self.running_case == "test_perf_16pools_8tcs":
            self.rebuild_dpdk(8)
        else:
            self.rebuild_dpdk(4)
        self.build_app()

    def build_app(self):
        """
        Build example "Vmdq_dcb".
        """
        out = self.dut.send_expect("make -C examples/vmdq_dcb", "#", 10)
        self.verify("Error" not in out, "Compilation error")

    def rebuild_dpdk(self, nb_queue_per_vm=4):
        """
        Rebuild dpdk
        """
        out = self.dut.send_expect("grep 'CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM' ./config/common_base", "#", 20)
        vm_num = re.findall(r'\d+', out)[-1]
        if str(nb_queue_per_vm) == vm_num:
            return
        else:
            self.dut.send_expect("sed -i -e 's/CONFIG_RTE_LIBRTE_I40E_QUEUE_NUM_PER_VM=%s/CONFIG_RTE_LIBRTE_I40E_"
                             "QUEUE_NUM_PER_VM=%s/' ./config/common_base" % (vm_num, nb_queue_per_vm), "#", 20)
            self.dut.build_install_dpdk(self.target)

    def start_application(self, npools, ntcs):
        """
        Prepare the commandline and start vmdq_dcb app
        """
        core_list = self.dut.get_core_list("1S/%dC/1T" % ntcs, socket=self.socket)
        self.verify(core_list is not None, "Requested %d cores failed" % ntcs)
        core_mask = utils.create_mask(core_list)
        port_mask = utils.create_mask(self.dut_ports)
        eal_param = ""
        for i in self.dut_ports:
            eal_param += " -w %s" % self.dut.ports_info[i]['pci']
        # Run the application
        self.dut.send_expect("./examples/vmdq_dcb/build/vmdq_dcb_app -c %s -n 4 %s -- -p %s --nb-pools %s --nb-tcs %s "
                             "--enable-rss" % (core_mask, eal_param, port_mask, str(npools), str(ntcs)), "reading queues", 120)

    def create_pcaps(self, prios):
        """
        create traffic flows to pcap files
        """
        payload = self.frame_size - HEADER_SIZE['ip'] - HEADER_SIZE['eth']
        for prio in prios:
            self.tester.scapy_append(
                'flows = [Ether(dst="%s")/Dot1Q(vlan=0,prio=%d)/IP(src="1.2.3.4", dst="1.1.1.1")/("X"*%d)]'
                % (self.destmac_port, prio, payload))
            pcap = os.sep.join([self.output_path, "%s%d.pcap" % (self.suite_name, prio)])
            self.tester.scapy_append('wrpcap("%s", flows)' % pcap)
        self.tester.scapy_execute()

    def get_tgen_input(self, prios):
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])
        tgen_input = []
        for prio in prios:
            pcap = os.sep.join([self.output_path, "%s%d.pcap" % (self.suite_name, prio)])
            tgen_input.append((tx_port, rx_port, "%s" % pcap))
        return tgen_input


    def set_fields(self, vid_range, dmac_range):
        """
        set ip protocol field behavior
        """

        fields_config = {
            'vlan': {
                0: {'range': vid_range, 'action': 'inc'}},
            'mac': {
                'dst': {'range': dmac_range, 'action': 'inc'}},
               'ip': { 'src': {'action': 'random'}},
            }

        return fields_config

    def get_vmdq_stats(self):
        vmdq_dcb_session = self.dut.new_session()
        vmdq_dcb_session.send_expect("kill -s SIGHUP  `pgrep -fl vmdq_dcb_app | awk '{print $1}'`", "#", 20)
        out = self.dut.get_session_output()
        self.logger.info(out)
        return out

    def verify_all_vmdq_stats(self):
        """
        Every RX queue should have received approximately (+/-15%) the same number of incoming packets.
        """
        out = self.get_vmdq_stats()
        lines_list = out.split("\r\n")
        nb_packets = []
        for pool_info in lines_list:
            if pool_info.startswith('Pool'):
                nb_packets += pool_info.split()[2:]
        nb_packets = list(map(int, nb_packets))
        self.verify(min(nb_packets) > 0, "Some queues don't get any packet!")
        self.verify(float((max(nb_packets) - min(nb_packets))/max(nb_packets)) <= 0.15, "Too wide variation in queue stats")

    def vmdq_dcb_test(self, npools, ntcs):
        """
        vmdq_dcb test according to pools, tcs.
        """
        self.start_application(npools, ntcs)

        # Transmit traffic
        tgen_input = self.get_tgen_input(self.prios)
        vm_config = self.set_fields(npools, npools)
        self.tester.pktgen.clear_streams()
        # Start traffic transmission using approx 10% of line rate.
        ratePercent = 50
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, ratePercent, vm_config, self.tester.pktgen)
        # set traffic option
        options = {'duration': 15}
        loss = self.tester.pktgen.measure_loss(stream_ids=streams, options=options)
        self.logger.info("loss is [loss rate, SendNumbers, ReceNumbers]{}!".format(loss))
        # Verify there is no packet loss
        self.verify(loss[1] == loss[2], "Packet Loss! Send: %d, but only Receive: %d!".format(loss[1], loss[2]))
        self.verify_all_vmdq_stats()

    def test_perf_32pools_4tcs(self):

        self.vmdq_dcb_test(32, 4)

    def test_perf_16pools_8tcs(self):

        self.vmdq_dcb_test(16, 8)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.rebuild_dpdk(4)
