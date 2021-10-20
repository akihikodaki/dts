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
Test support of IEEE1588 Precise Time Protocol.
"""

import re
import time

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.test_case import TestCase

DEV_TX_OFFLOAD_MULTI_SEGS = '0x00008000'

class TestIeee1588(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        IEEE1588 Prerequisites
        """
        dutPorts = self.dut.get_ports()
        self.verify(len(dutPorts) > 0, "No ports found for " + self.nic)

        # Change the config file to support IEEE1588 and recompile the package.
        self.dut.send_expect(
            "sed -i -e 's/IEEE1588=n$/IEEE1588=y/' config/common_base", "# ", 30)
        self.dut.set_build_options({'RTE_LIBRTE_IEEE1588': 'y'})
        self.dut.skip_setup = False
        self.dut.build_install_dpdk(self.target)

        self.pmdout = PmdOutput(self.dut)
        # For IEEE1588, the full-feature tx path needs to be enabled.
        # Enabling any tx offload will force DPDK utilize full tx path.
        # Enabling multiple segment offload is more reasonable for user cases.
        self.pmdout.start_testpmd("Default", " --tx-offloads=%s" % DEV_TX_OFFLOAD_MULTI_SEGS)

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_ieee1588_enable(self):
        """
        IEEE1588 Enable test case.
        """
        self.dut.send_expect("set fwd ieee1588", "testpmd> ", 10)
        if (self.nic in ["cavium_a063", "cavium_a064"]):
            self.dut.send_expect("set port 0 ptype_mask 0xf", "testpmd> ", 10)
        # Waiting for 'testpmd> ' Fails due to log messages, "Received non PTP
        # packet", in the output
        self.dut.send_expect("start", ">", 10)
        # Allow the output from the "start" command to finish before looking
        # for a regexp in expect
        time.sleep(1)

        # use the first port on that self.nic
        dutPorts = self.dut.get_ports()
        mac = self.dut.get_mac_address(dutPorts[0])
        port = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(port)

        self.send_session = self.tester.create_session('send_session')
        self.send_session.send_expect(
            "tcpdump -i %s -e ether src %s" % (itf, mac), "tcpdump", 20)

        setattr(self.send_session, 'tmp_file', self.tester.tmp_file)
        setattr(self.send_session, 'tmp_file', self.tester.get_session_output)
        pkt = Packet(pkt_type='TIMESYNC')
        pkt.config_layer('ether', {'dst': mac})
        pkt.send_pkt(self.tester, tx_port=itf)
        time.sleep(1)

        out = self.send_session.get_session_before(timeout=20)
        self.send_session.send_expect("^C", "# ", 20)
        self.send_session.close()

        self.verify("0x88f7" in out, "Ether type is not PTP")

        time.sleep(1)
        out = self.dut.get_session_output()
        self.dut.send_expect("stop", "testpmd> ")

        text = utils.regexp(out, "(.*) by hardware")
        self.verify("IEEE1588 PTP V2 SYNC" in text, "Not filtered " + text)

        pattern_rx = re.compile("RX timestamp value (\d+) s (\d+) ns")
        pattern_tx = re.compile("TX timestamp value (\d+) s (\d+) ns")

        m_rx = pattern_rx.search(out)
        m_tx = pattern_tx.search(out)
        if m_rx is not None:
            rx_time = m_rx.group(2)
        if m_tx is not None:
            tx_time = m_tx.group(2)

        self.verify(rx_time is not None, "RX timestamp error ")
        self.verify(tx_time is not None, "TX timestamp error ")
        self.verify(int(tx_time, 16) > int(rx_time, 16), "Timestamp mismatch")

    def test_ieee1588_disable(self):
        """
        IEEE1588 Disable test case.
        """
        self.dut.send_expect("stop", "testpmd> ", 10)
        time.sleep(3)

        # use the first port on that self.nic
        dutPorts = self.dut.get_ports()
        mac = self.dut.get_mac_address(dutPorts[0])
        port = self.tester.get_local_port(dutPorts[0])
        itf = self.tester.get_interface(port)

        self.tester.scapy_background()
        self.tester.scapy_append(
            'p = sniff(iface="%s", count=2, timeout=1)' % itf)
        self.tester.scapy_append('RESULT = p[1].summary()')

        self.tester.scapy_foreground()
        self.tester.scapy_append('nutmac="%s"' % mac)
        self.tester.scapy_append(
            'sendp([Ether(dst=nutmac,type=0x88f7)/"\\x00\\x02"], iface="%s")' % itf)

        self.tester.scapy_execute()
        time.sleep(2)

        out = self.tester.scapy_get_result()
        self.verify("Ether" not in out, "Ether type is not PTP")

    def tear_down(self):
        """
        Run after each test case.
        """
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.send_expect("quit", "# ", 30)

        # Restore the config file and recompile the package.
        self.dut.send_expect(
            "sed -i -e 's/IEEE1588=y$/IEEE1588=n/' config/common_base", "# ", 30)
        self.dut.set_build_options({'RTE_LIBRTE_IEEE1588': 'n'})
        self.dut.build_install_dpdk(self.target)
