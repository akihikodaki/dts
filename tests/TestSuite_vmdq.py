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

Tests for vmdq.

"""
import os
import re
from time import sleep

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestVmdq(TestCase):
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])

        self.dut.build_install_dpdk(self.target)
        # out = self.dut.send_expect("make -C examples/vmdq", "#", 10)
        out = self.dut.build_dpdk_apps("examples/vmdq")
        self.verify("Error" not in out, "Compilation error")

        self.app_vmdq_path = self.dut.apps_name["vmdq"]
        self.frame_size = 64
        self.header_size = HEADER_SIZE["ip"] + HEADER_SIZE["eth"]
        self.destmac_port = ["52:54:00:12:0%d:00" % i for i in self.dut_ports]
        self.core_configs = []
        self.core_configs.append({"cores": "1S/1C/1T", "mpps": {}})
        self.core_configs.append({"cores": "1S/2C/1T", "mpps": {}})
        self.core_configs.append({"cores": "1S/2C/2T", "mpps": {}})
        self.core_configs.append({"cores": "1S/4C/1T", "mpps": {}})

        # Put different number of pools: in the case of 10G 82599 Nic is 64, in the case
        # of FVL spirit is 63,in case of FVL eagle is 34.
        if self.nic in ("niantic", "springfountain"):
            self.pools = 64
        elif self.nic in ("fortville_spirit", "fortville_spirit_single"):
            self.pools = 63
        elif self.nic in ("fortville_eagle"):
            self.pools = 34
        else:
            self.pools = 8

        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        # get dts output path
        if self.logger.log_path.startswith(os.sep):
            self.output_path = self.logger.log_path
        else:
            cur_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            self.output_path = os.sep.join([cur_path, self.logger.log_path])
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()
        self.prios = range(8)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def start_application(self, npools, core_config):
        """
        Prepare the commandline and start vmdq app
        """
        core_list = self.dut.get_core_list(core_config, socket=self.ports_socket)
        self.verify(core_list is not None, "Requested cores failed")
        core_mask = utils.create_mask(core_list)
        port_mask = utils.create_mask(self.dut_ports)
        eal_param = ""
        for i in self.dut_ports:
            eal_param += " -a %s" % self.dut.ports_info[i]["pci"]
        # Run the application
        self.dut.send_expect(
            "./%s -c %s -n 4 %s -- -p %s --nb-pools %s --enable-rss"
            % (self.app_vmdq_path, core_mask, eal_param, port_mask, str(npools)),
            "reading queues",
            120,
        )

    def get_tgen_input(self, prios):
        """
        create streams for ports.
        """
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])
        tgen_input = []
        for prio in prios:
            pcap = os.sep.join(
                [self.output_path, "%s%d.pcap" % (self.suite_name, prio)]
            )
            tgen_input.append((tx_port, rx_port, "%s" % pcap))
        return tgen_input

    def create_pcaps(self, prios):
        """
        create traffic flows to pcap files
        """
        payload = self.frame_size - self.header_size
        for prio in prios:
            self.tester.scapy_append(
                'flows = [Ether(dst="%s")/Dot1Q(vlan=0,prio=%d)/IP(src="1.2.3.4", dst="1.1.1.1")/("X"*%d)]'
                % (self.destmac_port[0], prio, payload)
            )
            pcap = os.sep.join(
                [self.output_path, "%s%d.pcap" % (self.suite_name, prio)]
            )
            self.tester.scapy_append('wrpcap("%s", flows)' % pcap)
        self.tester.scapy_execute()

    def verify_all_vmdq_stats(self):
        """
        Every RX queue should have received approximately (+/-15%) the same number of incoming packets.
        """
        out = self.get_vmdq_stats()
        lines_list = out.split("\r\n")
        nb_packets = []
        for pool_info in lines_list:
            if pool_info.startswith("Pool"):
                nb_packets += pool_info.split()[2:]
        nb_packets = list(map(int, nb_packets))
        self.verify(min(nb_packets) > 0, "Some queues don't get any packet!")
        self.verify(
            float((max(nb_packets) - min(nb_packets)) / max(nb_packets)) <= 0.15,
            "Too wide variation in queue stats",
        )

    def get_vmdq_stats(self):
        vmdq_session = self.dut.new_session()
        app_name = self.dut.apps_name["vmdq"].split("/")[-1]
        vmdq_session.send_expect(
            "kill -s SIGHUP  `pgrep -fl %s | awk '{print $1}'`" % app_name, "#", 20
        )
        out = self.dut.get_session_output()
        self.logger.info(out)
        vmdq_session.close()
        return out

    def test_perf_vmdq_max_queues(self):
        """
        Every RX queue should have received approximately (+/-15%) the same number of
        incoming packets.
        """
        # Run the application
        self.start_application(self.pools, "1S/4C/1T")
        # Transmit traffic
        self.create_pcaps(self.prios)
        tgen_input = self.get_tgen_input(self.prios)
        vm_config = self.set_fields(self.pools, self.pools)
        # Start traffic transmission using approx 10% of line rate.
        ratePercent = 10
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(
            tgen_input, ratePercent, vm_config, self.tester.pktgen
        )
        # set traffic option
        options = {"duration": 15}
        loss = self.tester.pktgen.measure_loss(stream_ids=streams, options=options)
        self.logger.info(
            "loss is [loss rate, SendNumbers, ReceNumbers]{}!".format(loss)
        )
        # Verify there is no packet loss
        self.verify(
            loss[1] == loss[2],
            "Packet Loss! Send: %d, but only Receive: %d!".format(loss[1], loss[2]),
        )
        self.verify_all_vmdq_stats()

    def create_throughput_traffic(self, frame_size):
        payload = frame_size - self.header_size
        tgen_Input = []
        for _port in self.dut_ports:
            if _port % len(self.dut_ports) == 0 or len(self.dut_ports) % _port == 2:
                txIntf = self.tester.get_local_port(self.dut_ports[_port + 1])
                dst_port = _port + 1
            else:
                txIntf = self.tester.get_local_port(self.dut_ports[_port - 1])
                dst_port = _port - 1
            rxIntf = self.tester.get_local_port(self.dut_ports[_port])
            self.tester.scapy_append(
                'flows = [Ether(dst="%s")/Dot1Q(vlan=0)/IP(src="1.2.3.4", dst="1.1.1.1")/("X"*%d)]'
                % (self.destmac_port[dst_port], payload)
            )
            pcap = os.sep.join(
                [self.output_path, "%s-%d.pcap" % (self.suite_name, _port)]
            )
            self.tester.scapy_append('wrpcap("%s", flows)' % pcap)
            self.tester.scapy_execute()
            tgen_Input.append((txIntf, rxIntf, pcap))
        return tgen_Input

    def test_perf_vmdq_performance(self):
        """
        Try different configuration and different packet size
        """
        frame_sizes = [64, 128, 256, 512, 1024, 1280, 1518]
        for config in self.core_configs:
            self.logger.info(config["cores"])
            self.dut.kill_all()
            core_config = config["cores"]
            self.start_application(self.pools, core_config)
            self.logger.info("Waiting for application to initialize")
            sleep(5)
            for frame_size in frame_sizes:
                self.logger.info(str(frame_size))
                tgen_input = self.create_throughput_traffic(frame_size)
                # clear streams before add new streams
                self.tester.pktgen.clear_streams()
                vm_config = self.set_fields(self.pools, self.pools)
                # run packet generator
                streams = self.pktgen_helper.prepare_stream_from_tginput(
                    tgen_input, 100, vm_config, self.tester.pktgen
                )
                _, pps = self.tester.pktgen.measure_throughput(stream_ids=streams)
                self.verify(pps > 0, "No traffic detected")
                config["mpps"][frame_size] = pps / 1000000.0
        # Print results
        self.result_table_create(
            ["Frame size"] + [n["cores"] for n in self.core_configs]
        )

        for size in frame_sizes:
            self.result_table_add([size] + [n["mpps"][size] for n in self.core_configs])

        self.result_table_print()

    # Override etgen.dot1q function
    def set_fields(self, vid_range, dmac_range):
        """
        set ip protocol field behavior
        """
        fields_config = {
            "vlan": {0: {"range": vid_range, "action": "inc"}},
            "mac": {"dst": {"range": dmac_range, "action": "inc"}},
            "ip": {"src": {"action": "random"}},
        }
        return fields_config

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        # resume setting
        self.dut.build_install_dpdk(self.target)
