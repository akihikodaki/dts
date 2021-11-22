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
Test for Ethernet Link Flow Control Features by Poll Mode Drivers
"""

import os
import re
from time import sleep

import framework.utils as utils
from framework.pktgen import PacketGeneratorHelper
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase


class TestLinkFlowctrl(TestCase):
    pause_frame_dst = "01:80:C2:00:00:01"
    pause_frame_type = "0x8808"
    pause_frame_opcode = "\\x00\\x01"
    pause_frame_control = "\\x00\\xFF"
    pause_frame_paddign = "\\x00" * 42

    pause_frame = '[Ether(src="%s",dst="%s",type=%s)/(b"%s%s%s")]'

    frames_to_sent = 12

    packet_size = 66    # 66 allows frame loss
    payload_size = packet_size - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']

    def set_up_all(self):
        """
        Run at the start of each test suite.

        Link flow control Prerequisites
        """

        self.dutPorts = self.dut.get_ports()
        self.verify(len(self.dutPorts) > 1, "Insuficient ports")

        self.rx_port = self.dutPorts[0]
        self.tester_tx_mac = self.tester.get_mac(self.tester.get_local_port(self.rx_port))

        self.tx_port = self.dutPorts[1]

        self.portMask = utils.create_mask([self.rx_port, self.tx_port])

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
        self.pmdout = PmdOutput(self.dut)
        self.pmdout.start_testpmd("all", "--portmask=%s" % self.portMask)

    def get_tgen_input(self):
        """
        create streams for ports.
        """

        tester_tx_port = self.tester.get_local_port(self.rx_port)
        tester_rx_port = self.tester.get_local_port(self.tx_port)

        tgenInput = []
        pcap = os.sep.join([self.output_path, "test.pcap"])

        tgenInput.append((tester_tx_port, tester_rx_port, pcap))
        return tgenInput

    def start_traffic(self, tgenInput):

        pcap = os.sep.join([self.output_path, "test.pcap"])
        self.tester.scapy_append('wrpcap("%s",[Ether()/IP()/UDP()/("X"*%d)])' %
                                 (pcap, TestLinkFlowctrl.payload_size))

        self.tester.scapy_execute()

        # clear streams before add new streams
        self.tester.pktgen.clear_streams()
        # run packet generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgenInput, 100,
                                                                 None, self.tester.pktgen)
        options = {'duration': 60}
        result = self.tester.pktgen.measure_loss(stream_ids=streams, options=options)
        return result[0]

    def set_flow_ctrl(self, rx_flow_control='off',
                                  tx_flow_control='off',
                                  pause_frame_fwd='off'):

        self.dut.send_expect("set flow_ctrl rx %s tx %s 300 50 10 1 mac_ctrl_frame_fwd %s autoneg on %d " % (
                              rx_flow_control,
                              tx_flow_control,
                              pause_frame_fwd,
                              self.rx_port),
                              "testpmd> ")

        self.dut.send_expect("set fwd csum", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ", 60)
        self.pmdout.wait_link_status_up(self.dutPorts[0])

    def pause_frame_loss_test(self, rx_flow_control='off',
                              tx_flow_control='off',
                              pause_frame_fwd='off'):

        tgenInput = self.get_tgen_input()
        self.set_flow_ctrl(rx_flow_control, tx_flow_control, pause_frame_fwd)
        result = self.start_traffic(tgenInput)
        self.dut.send_expect("stop", "testpmd> ")

        return result

    def get_testpmd_port_stats(self, ports):
        """
            Returns the number of packets transmitted and received from testpmd.
            Uses testpmd show port stats.
        """

        rx_pattern = "RX-packets: (\d*)"
        tx_pattern = "TX-packets: (\d*)"
        rx = re.compile(rx_pattern)
        tx = re.compile(tx_pattern)

        port_stats = {}

        for port in ports:
            out = self.dut.send_expect("show port stats %d" % port,
                                       "testpmd> ")

            rx_packets = int(rx.search(out).group(1))
            tx_packets = int(tx.search(out).group(1))

            port_stats[port] = (rx_packets, tx_packets)

        return port_stats

    def send_packets(self, frame):
        self.pmdout.wait_link_status_up(self.dutPorts[0])
        tester_tx_port = self.tester.get_local_port(self.rx_port)
        tx_interface = self.tester.get_interface(tester_tx_port)
        tester_rx_port = self.tester.get_local_port(self.tx_port)

        tgenInput = []
        tgenInput.append((tester_tx_port, tester_rx_port, "test.pcap"))
        self.tester.scapy_foreground()
        self.tester.scapy_append('sendp(%s, iface="%s", count=%d)' % (frame,
                                                                      tx_interface,
                                                                      TestLinkFlowctrl.frames_to_sent))

        self.tester.scapy_execute()
        # The following sleep is needed to allow all the packets to arrive.
        # 1s works for Crown Pass (FC18) DUT, Lizard Head Pass (FC14) tester
        # using Niantic. Increase it in case of packet loosing.
        sleep(1)

        self.dut.send_expect("stop", "testpmd> ")

        port_stats = self.get_testpmd_port_stats((self.rx_port, self.tx_port))
        return port_stats

    def pause_frame_test(self, frame, flow_control='off',
                         pause_frame_fwd='off'):
        """
            Sets testpmd flow control and mac ctrl frame fwd according to the
            parameters, starts forwarding and clears the stats, then sends the
            passed frame and stops forwarding.
            Returns the testpmd port stats.
        """

        if (self.nic in ["cavium_a063", "cavium_a064"]):
            self.dut.send_expect("set flow_ctrl rx %s tx %s 300 50 10 1 autoneg %s %d " % (
                             flow_control,
                             flow_control,
                             flow_control,
                             self.rx_port),
                             "testpmd> ")
        elif self.running_case == "test_pause_fwd_port_stop_start":
            self.dut.send_expect("set flow_ctrl mac_ctrl_frame_fwd %s %d " % (pause_frame_fwd,
                                                                              self.rx_port), "testpmd> ")
        else:
            self.dut.send_expect("set flow_ctrl rx %s tx %s 300 50 10 1 mac_ctrl_frame_fwd %s autoneg %s %d " % (
                             flow_control,
                             flow_control,
                             pause_frame_fwd,
                             flow_control,
                             self.rx_port),
                             "testpmd> ")

        self.dut.send_expect("set fwd io", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("clear port stats all", "testpmd> ")

        port_stats = self.send_packets(frame)
        return port_stats

    def check_pause_frame_test_result(self, result, expected_rx=False, expected_fwd=False):
        """
            Verifies the test results (use pause_frame_test before) against
            the expected behavior.
        """
        self.logger.info("Result (port, rx, tx) %s,  expected rx %s, expected fwd %s" % (result,
                                                                              expected_rx,
                                                                              expected_fwd))

        if expected_rx:
            self.verify(result[self.rx_port][0] == TestLinkFlowctrl.frames_to_sent,
                        "Pause Frames are not being received by testpmd (%d received)" %
                        result[self.rx_port][0])
            if expected_fwd:
                self.verify(result[self.tx_port][1] == TestLinkFlowctrl.frames_to_sent,
                            "Pause Frames are not being forwarded by testpmd (%d sent)" % (
                                result[self.tx_port][1]))
            else:
                self.verify(result[self.tx_port][1] == 0,
                            "Pause Frames are being forwarded by testpmd (%d sent)" % (
                                result[self.tx_port][1]))
        else:
            self.verify(result[self.rx_port][0] == 0,
                        "Pause Frames are being received by testpmd (%d received)" %
                        result[self.rx_port][0])

    def build_pause_frame(self, option=0):
        """
        Build the PAUSE Frame for the tests. 3 available options:
        0: Correct frame (correct src and dst addresses and opcode)
        1: Wrong source frame (wrong src, correct and dst address and opcode)
        2: Wrong opcode frame (correct src and dst address and wrong opcode)
        3: Wrong destination frame (correct src and opcode, wrong dst address)
        """

        if option == 1:
            return TestLinkFlowctrl.pause_frame % ("00:01:02:03:04:05",
                                                   TestLinkFlowctrl.pause_frame_dst,
                                                   TestLinkFlowctrl.pause_frame_type,
                                                   TestLinkFlowctrl.pause_frame_opcode,
                                                   TestLinkFlowctrl.pause_frame_control,
                                                   TestLinkFlowctrl.pause_frame_paddign)

        elif option == 2:
            return TestLinkFlowctrl.pause_frame % (self.tester_tx_mac,
                                                   TestLinkFlowctrl.pause_frame_dst,
                                                   TestLinkFlowctrl.pause_frame_type,
                                                   "\\x00\\x02",
                                                   TestLinkFlowctrl.pause_frame_control,
                                                   TestLinkFlowctrl.pause_frame_paddign)
        elif option == 3:
            return TestLinkFlowctrl.pause_frame % (self.tester_tx_mac,
                                                   "01:80:C2:00:AB:10",
                                                   TestLinkFlowctrl.pause_frame_type,
                                                   TestLinkFlowctrl.pause_frame_opcode,
                                                   TestLinkFlowctrl.pause_frame_control,
                                                   TestLinkFlowctrl.pause_frame_paddign)

        return TestLinkFlowctrl.pause_frame % (self.tester_tx_mac,
                                               TestLinkFlowctrl.pause_frame_dst,
                                               TestLinkFlowctrl.pause_frame_type,
                                               TestLinkFlowctrl.pause_frame_opcode,
                                               TestLinkFlowctrl.pause_frame_control,
                                               TestLinkFlowctrl.pause_frame_paddign)

    def test_flowctrl_off_pause_fwd_off(self):
        """
        Flow control disabled, MAC PAUSE frame forwarding disabled.
        PAUSE Frames must not be received by testpmd
        """

        if (self.nic in ["cavium_a063", "cavium_a064"]):
            pause_frames = [self.build_pause_frame(0),
                            self.build_pause_frame(1)]
        else:
            pause_frames = [self.build_pause_frame(0),
                            self.build_pause_frame(1),
                            self.build_pause_frame(2),
                            self.build_pause_frame(3)]

        for frame in pause_frames:
            port_stats = self.pause_frame_test(frame)
            self.check_pause_frame_test_result(port_stats)

    def test_flowctrl_on_pause_fwd_off(self):
        """
        Flow control enabled, MAC PAUSE frame forwarding disabled.
        PAUSE Frames must not be received by testpmd
        """

        if (self.nic in ["cavium_a063", "cavium_a064"]):
            pause_frames = [self.build_pause_frame(0),
                            self.build_pause_frame(1)]
        else:
            pause_frames = [self.build_pause_frame(0),
                            self.build_pause_frame(1),
                            self.build_pause_frame(2),
                            self.build_pause_frame(3)]

        for frame in pause_frames:
            port_stats = self.pause_frame_test(frame, flow_control='on')
            self.check_pause_frame_test_result(port_stats)

    def test_flowctrl_off_pause_fwd_on(self):
        """
        Flow control disabled, MAC PAUSE frame forwarding enabled.
        All PAUSE Frames must be forwarded by testpmd.
        """

        # Regular frames, check for no frames received
        pause_frame = self.build_pause_frame()
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

        # Wrong src MAC, check for no frames received
        pause_frame = self.build_pause_frame(1)
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

        # Unrecognized frames (wrong opcode), check for all frames received and fwd
        pause_frame = self.build_pause_frame(2)
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

        # Wrong dst MAC, check for all frames received
        pause_frame = self.build_pause_frame(3)
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

    def test_flowctrl_on_pause_fwd_on(self):
        """
        Flow control enabled, MAC PAUSE frame forwarding enabled.
        Only unrecognized PAUSE Frames must be forwarded by testpmd.
        """

        # Regular frames, check for no frames received
        pause_frame = self.build_pause_frame()
        port_stats = self.pause_frame_test(pause_frame, flow_control='on',
                                           pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats)

        # Wrong src MAC, check for no frames received
        pause_frame = self.build_pause_frame(1)
        port_stats = self.pause_frame_test(pause_frame, flow_control='on',
                                           pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats)

        # Unrecognized frames (wrong opcode), check for all frames received and fwd
        pause_frame = self.build_pause_frame(2)
        port_stats = self.pause_frame_test(pause_frame, flow_control='on',
                                           pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

        # Wrong dst MAC, check for all frames received
        pause_frame = self.build_pause_frame(3)
        port_stats = self.pause_frame_test(pause_frame, flow_control='on',
                                           pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

    def test_pause_fwd_port_stop_start(self):
        """
        Check werther the MAC Control Frame Forwarding setting still working after port stop/start.
        """

        # Regular frames, check for no frames received
        pause_frame = self.build_pause_frame()

        # Enable mac control Frame Forwarding, and validate packets are received.
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='on')
        self.check_pause_frame_test_result(port_stats, True, True)

        # test again after port stop/start
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ", 60)
        self.dut.send_expect("start", "testpmd> ", 60)
        self.dut.send_expect("clear port stats all", "testpmd> ")
        port_stats = self.send_packets(pause_frame)
        self.check_pause_frame_test_result(port_stats, True, True)

        # Disable mac control Frame Forwarding, and validate no packets are received.
        port_stats = self.pause_frame_test(pause_frame, pause_frame_fwd='off')
        self.check_pause_frame_test_result(port_stats)

        # test again after port stop/start
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ", 60)
        self.dut.send_expect("start", "testpmd> ", 60)
        self.dut.send_expect("clear port stats all", "testpmd> ")
        port_stats = self.send_packets(pause_frame)
        self.check_pause_frame_test_result(port_stats)

    def test_perf_flowctrl_on_pause_fwd_on(self):
        """
        Enable link flow control and PAUSE frame forwarding
        """

        result = self.pause_frame_loss_test(rx_flow_control='on',
                                            tx_flow_control='on',
                                            pause_frame_fwd='on')

        self.logger.info("Packet loss: %.3f" % result)

        self.verify(result <= 0.01,
                    "Link flow control fail, the loss percent is more than 1%")

    def test_perf_flowctrl_on_pause_fwd_off(self):
        """
        Enable link flow control and disable PAUSE frame forwarding
        """

        result = self.pause_frame_loss_test(rx_flow_control='on',
                                            tx_flow_control='on',
                                            pause_frame_fwd='off')

        self.logger.info("Packet loss: %.3f" % result)

        self.verify(result <= 0.01,
                    "Link flow control fail, the loss percent is more than 1%")

    def test_perf_flowctrl_rx_on(self):
        """
        Enable only rx link flow control
        """

        result = self.pause_frame_loss_test(rx_flow_control='on',
                                            tx_flow_control='off',
                                            pause_frame_fwd='off')

        self.logger.info("Packet loss: %.3f" % result)
        if self.nic == "niantic":
            self.verify(result >= 0.3,
                        "Link flow control fail, the loss percent is less than 30%")
        else:
            self.verify(result >= 0.5,
                        "Link flow control fail, the loss percent is less than 50%")

    def test_perf_flowctrl_off_pause_fwd_on(self):
        """
        Disable link flow control and enable PAUSE frame forwarding
        """

        result = self.pause_frame_loss_test(rx_flow_control='off',
                                            tx_flow_control='off',
                                            pause_frame_fwd='on')

        self.logger.info("Packet loss: %.3f" % result)
        if self.nic == "niantic":
            self.verify(result >= 0.3,
                        "Link flow control fail, the loss percent is less than 30%")
        else:
            self.verify(result >= 0.5,
                        "Link flow control fail, the loss percent is less than 50%")

    def test_perf_flowctrl_off_pause_fwd_off(self):
        """
        Disable link flow control and PAUSE frame forwarding
        """

        result = self.pause_frame_loss_test(rx_flow_control='off',
                                            tx_flow_control='off',
                                            pause_frame_fwd='off')

        self.logger.info("Packet loss: %.3f" % result)
        if self.nic == "niantic":
            self.verify(result >= 0.3,
                        "Link flow control fail, the loss percent is less than 30%")
        else:
            self.verify(result >= 0.5,
                        "Link flow control fail, the loss percent is less than 50%")

    def test_perf_flowctrl_tx_on(self):
        """
        Enable only tx link flow control
        """

        result = self.pause_frame_loss_test(rx_flow_control='off',
                                            tx_flow_control='on',
                                            pause_frame_fwd='off')

        self.logger.info("Packet loss: %.3f" % result)

        self.verify(result <= 0.01,
                    "Link flow control fail, the loss percent is more than 1%")

    def test_perf_flowctrl_on_port_stop_start(self):
        """
        Check werther the link flow control setting is still working after port stop/start.
        """

        # Enable link flow control and PAUSE frame forwarding
        result = self.pause_frame_loss_test(rx_flow_control='on',
                                            tx_flow_control='on',
                                            pause_frame_fwd='off')
        self.logger.info("Packet loss: %.3f" % result)
        self.verify(result <= 0.01,
                    "Link flow control fail, the loss percent is more than 1%")

        # test again after port stop/start
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ", 60)
        self.dut.send_expect("start", "testpmd> ", 60)
        self.pmdout.wait_link_status_up(self.dutPorts[0])
        tgenInput = self.get_tgen_input()
        result = self.start_traffic(tgenInput)
        self.logger.info("Packet loss: %.3f" % result)
        self.verify(result <= 0.01,
                    "Link flow control fail after port stop/start, the loss percent is more than 1%")
        self.dut.send_expect("stop", "testpmd> ")

        # Disable link flow control and PAUSE frame forwarding
        self.set_flow_ctrl(rx_flow_control="off",
                           tx_flow_control='off',
                           pause_frame_fwd='off')
        result = self.start_traffic(tgenInput)
        self.logger.info("Packet loss: %.3f" % result)
        if self.nic == "niantic":
            self.verify(result >= 0.3,
                        "Link flow control fail, the loss percent is less than 30%")
        else:
            self.verify(result >= 0.5,
                        "Link flow control fail, the loss percent is less than 50%")
        # test again after port Stop/start
        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ", 60)
        self.dut.send_expect("start", "testpmd> ", 60)
        self.pmdout.wait_link_status_up(self.dutPorts[0])
        result = self.start_traffic(tgenInput)
        self.logger.info("Packet loss: %.3f" % result)
        if self.nic == "niantic":
            self.verify(result >= 0.3,
                        "Link flow control fail, the loss percent is less than 30%")
        else:
            self.verify(result >= 0.5,
                        "Link flow control fail, the loss percent is less than 50%")
        self.dut.send_expect("stop", "testpmd> ")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("quit", "# ")
        self.dut.kill_all()
    
    def tear_down_all(self):
        """
        Run after each test suite.
        """
        pass
