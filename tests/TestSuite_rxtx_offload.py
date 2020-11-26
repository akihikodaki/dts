# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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

New RX/TX offload APIs.

"""

import utils
import time
import re

from test_case import TestCase
from settings import HEADER_SIZE
from pmd_output import PmdOutput
from settings import DRIVERS

from project_dpdk import DPDKdut
from dut import Dut
from packet import Packet

ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000

offloads = {'mbuf_fast_free': 'MBUF_FAST_FREE',
            'vlan_insert': 'VLAN_INSERT',
            'ipv4_cksum': 'IPV4_CKSUM',
            'udp_cksum': 'UDP_CKSUM',
            'tcp_cksum': 'TCP_CKSUM',
            'sctp_cksum': 'SCTP_CKSUM',
            'outer_ipv4_cksum': 'OUTER_IPV4_CKSUM',
            'tcp_tso': 'TCP_TSO',
            'qinq_insert': 'QINQ_INSERT',
            'vxlan_tnl_tso': 'VXLAN_TNL_TSO',
            'gre_tnl_tso': 'GRE_TNL_TSO',
            'ipip_tnl_tso': 'IPIP_TNL_TSO',
            'geneve_tnl_tso': 'GENEVE_TNL_TSO',
            'multi_segs': 'MULTI_SEGS',
            'macsec_insert': 'MACSEC_INSERT',
            'security': 'SECURITY',
            'vlan_strip': 'VLAN_STRIP',
            'tcp_lro': 'TCP_LRO',
            'qinq_strip': 'QINQ_STRIP',
            'vlan_filter': 'VLAN_FILTER',
            'vlan_extend': 'VLAN_EXTEND',
            'jumboframe': 'JUMBO_FRAME',
            'scatter': 'SCATTER',
            'keep_crc': 'KEEP_CRC',
            'macsec_strip': 'MACSEC_STRIP'
            }


class TestRxTx_Offload(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        New rx tx offload API Prerequisites
        """
        # Support i40e/ixgbe NICs
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit","fortville_25g",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville",
                                 "niantic", "twinpond", "sagepond", "sageville", "foxville", "cavium_a063", "cavium_a064"], "NIC Unsupported: " + str(self.nic))
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")

        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_itf0 = self.tester.get_interface(localPort0)
        self.tester_itf1 = self.tester.get_interface(localPort1)

        self.tester_mac0 = self.tester.get_mac(localPort0)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.pmdout = PmdOutput(self.dut)
        self.cores = "1S/4C/1T"

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def verify_link_up(self, max_delay=10):
        ports = self.dut.get_ports(self.nic)
        for port_id in range(len(ports)):
            out = self.dut.send_expect("show port info %s" % port_id, "testpmd> ")
            port_time_up = 0
            while (port_time_up <= max_delay) and ("Link status: down" in out):
                time.sleep(1)
                out = self.dut.send_expect("show port info %s" % port_id, "testpmd> ")
                port_time_up += 1
            self.verify("Link status: down" not in out, "Port %s Link down, please check your link" % port_id)

    def check_port_capability(self, rxtx):
        """
        Check capabilities.
        """
        global offloads
        offload_keys = []
        if rxtx == "rx":
            outstring = self.dut.send_expect("show port 0 rx_offload capabilities", "testpmd> ")
        elif rxtx == "tx":
            outstring = self.dut.send_expect("show port 0 tx_offload capabilities", "testpmd> ")

        # get capability by port
        result_scanner = r"Per Port  : (.*?)\n"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        i = 0
        offload_value = m.group(1).split()
        for key, value in list(offloads.items()):
            if value in offload_value:
                offload_keys.insert(i, key)
                i = i + 1
        return offload_keys

    def check_port_config(self, rxtx, offload, port_id=0):
        """
        Check configuration per port.
        """
        global offloads

        result_config = self.dut.send_expect("port start %d" % port_id, "testpmd> ")
        self.verify("Fail" not in result_config, "Fail to configure port")
        self.verify_link_up(20)

        if rxtx == "rx":
            outstring = self.dut.send_expect("show port %d rx_offload configuration" % port_id, "testpmd> ")
        elif rxtx == "tx":
            outstring = self.dut.send_expect("show port %d tx_offload configuration" % port_id, "testpmd> ")

        result_scanner = r"Port : (.*?)\n"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        if offload == "NULL":
            self.verify(m == None, "The offload failed to be disabled.")
        else:
            exp_offload = m.group(1).split()
            self.verify(exp_offload != None, "There is no offload configured.")
            for each_offload in offload:
                self.verify(each_offload in list(offloads.keys()), "Offload type error!")
                self.verify(offloads[each_offload] in exp_offload, "There is wrong offload configured.")

    def check_queue_config(self, rxtx, offload):
        """
        Check configuration per queue.
        """
        global offloads

        result_config = self.dut.send_expect("port start 0", "testpmd> ")
        self.verify("Fail" not in result_config, "Fail to configure port")
        self.verify_link_up(20)

        acl_offloads = []
        if rxtx == "rx":
            outstring = self.dut.send_expect("show port 0 rx_offload configuration", "testpmd> ")
        elif rxtx == "tx":
            outstring = self.dut.send_expect("show port 0 tx_offload configuration", "testpmd> ")

        lines = outstring.split("\r\n")
        result_scanner = r"Queue[ \d]  : (.*?)"
        scanner = re.compile(result_scanner, re.DOTALL)
        queue_line = []
        i = 0
        for line in lines:
            if len(line) != 0 and line.strip().startswith("Queue"):
                queue_line.insert(i, line)
                i = i + 1
        i = 0
        for i in range(0, 4):
            if offload[i] == "NULL":
                m = scanner.search(queue_line[i])
                self.verify(m == None, "Fail to configure offload by queue.")
            else:
                acl_offload = offloads[offload[i]]
                self.verify(acl_offload in queue_line[i], "Fail to configure offload by queue.")
            i = i + 1
 
    def get_queue_number(self, packet):
        """
        Send packet and get the queue which packet enter.
        """
        self.dut.send_expect("start", "testpmd> ")
        self.verify_link_up(20)
        self.tester.scapy_foreground()
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        outstring = self.dut.send_expect("stop", "testpmd> ")
        self.verify("Queue" in outstring, "the packet is not received.")
        result_scanner = r"Forward Stats for RX Port= %s/Queue=\s?([0-9]+)" % self.dut_ports[0]
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        queue_id = m.group(1)
        print(("queue is %s" % queue_id))
        return queue_id

    def check_flag(self, packet, queue):
        """
        Sends packets and check the flag.
        """
        self.dut.send_expect("start", "testpmd>")
        self.verify_link_up(20)
        self.tester.scapy_foreground()
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        time.sleep(2)
        outstring = self.dut.get_session_output(timeout=1)
        # get queue ID
        result_scanner = r"RSS queue=0x([0-9]+)"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.search(outstring)
        queue_id = m.group(1)
        if int(queue_id) in queue:
            self.verify("PKT_RX_VLAN_STRIPPED" in outstring, "Fail to configure offload by queue.")
        else:
            self.verify("PKT_RX_VLAN_STRIPPED" not in outstring, "Fail to configure offload by queue.")
        self.dut.send_expect("stop", "testpmd>")

    def checksum_valid_flags(self, packet, direction, flags):
        """
        Sends packets and check the checksum valid-flags.
        """
        self.dut.send_expect("start", "testpmd>")
        self.tester.scapy_foreground()
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        out = self.dut.get_session_output(timeout=1)
        lines = out.split("\r\n")

        # collect the rx checksum result
        if (direction == "rx"):
            for line in lines:
                line = line.strip()
                if len(line) != 0 and line.startswith("rx") and ("flags" in line):
                    if ("ipv4" in flags):
                        self.verify("PKT_RX_IP_CKSUM_BAD" in line, "ipv4 checksum flag is wrong!")
                    else:
                        self.verify("PKT_RX_IP_CKSUM_GOOD" in line, "ipv4 checksum flag is wrong!")
                    if ("udp" in flags) or ("tcp" in flags):
                        if self.nic in ['cavium_a063', 'cavium_a064']:
                            self.verify("PKT_RX_L4_CKSUM_BAD" or "PKT_RX_L4_CKSUM_UNKNOWN" in line, "L4 checksum flag is wrong!")
                        else:
                            self.verify("PKT_RX_L4_CKSUM_BAD" in line, "L4 checksum flag is wrong!")
                    else:
                        self.verify(("PKT_RX_L4_CKSUM_GOOD" in line) or ("PKT_RX_L4_CKSUM_UNKNOWN" in line), "L4 checksum flag is wrong!")
        # collect the tx checksum result
        if (direction == "tx"):
            for line in lines:
                line = line.strip()
                if len(line) != 0 and line.startswith("tx") and ("flags" in line):
                    if ("ipv4" in flags):
                        self.verify("PKT_TX_IP_CKSUM" in line, "There is no ipv4 tx checksum flag!")
                    if ("udp" in flags):
                        self.verify("PKT_TX_UDP_CKSUM" in line, "There is no udp tx checksum flag!")
                    if ("tcp") in flags:
                        self.verify("PKT_TX_TCP_CKSUM" in line, "There is no tcp tx checksum flag!")
                    if ("sctp") in flags:
                        self.verify("PKT_TX_SCTP_CKSUM" in line, "There is no sctp tx checksum flag!")
                    if (flags == []):
                        self.verify(("PKT_TX_L4_NO_CKSUM" in line) and ("PKT_TX_IP_CKSUM" not in line), "The tx checksum flag is wrong!")
        self.dut.send_expect("stop", "testpmd>")

    def verify_result(self, packet, expect_rxpkts, expect_queue):
        """
        verify if the packet is to the expected queue
        """
        result_config = self.dut.send_expect("port start 0", "testpmd> ")
        self.verify("Fail" not in result_config, "Fail to configure port")

        self.dut.send_expect("start", "testpmd> ")
        self.verify_link_up(20)
        self.tester.scapy_foreground()
        self.tester.scapy_append(packet)
        self.tester.scapy_execute()
        time.sleep(2)

        outstring = self.dut.send_expect("stop", "testpmd> ", 120)
        time.sleep(2)
        if expect_rxpkts == 0:
            self.verify("Queue" not in outstring, "the packet is still received.")
        else:
            result_scanner = r"Forward Stats for RX Port= %s/Queue=\s?([0-9]+)" % self.dut_ports[0]
            scanner = re.compile(result_scanner, re.DOTALL)
            m = scanner.search(outstring)
            queue_id = m.group(1)
            self.verify(int(expect_queue) == int(queue_id), "the offload setting doesn't take effect.")

    def start_tcpdump(self, rxItf):

        self.tester.send_expect("rm -rf ./getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -i %s -w ./getPackageByTcpdump.cap 2> /dev/null& " % rxItf, "#")

    def get_tcpdump_package(self):

        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect("tcpdump -nn -e -v -c 1024 -r ./getPackageByTcpdump.cap", "#", 120)

    def test_rxoffload_port(self):
        """
        Set Rx offload by port.
        """
        # Define jumboframe packets
        self.jumbo_pkt1 = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1",src="192.168.0.2", len=8981)/Raw(load="P"*8961)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.jumbo_pkt2 = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1",src="192.168.0.3", len=8981)/Raw(load="P"*8961)], iface="%s")' % (self.pf_mac, self.tester_itf0)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --max-pkt-len=9000")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        offload = ['jumboframe']
        self.check_port_config("rx", offload)
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_itf0, ETHER_JUMBO_FRAME_MTU), "# ")
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_itf1, ETHER_JUMBO_FRAME_MTU), "# ")

        pkt1_queue = self.get_queue_number(self.jumbo_pkt1)
        pkt2_queue = self.get_queue_number(self.jumbo_pkt2)

        # Failed to disable jumboframe per_queue, foxvillee 2.5g not support
        if self.nic != 'foxville':
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port 0 rxq %s rx_offload jumbo_frame off" % pkt1_queue, "testpmd> ")
            self.verify_result(self.jumbo_pkt1, 1, pkt1_queue)

        # Succeed to disable jumboframe per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload jumbo_frame off", "testpmd> ")
        self.check_port_config("rx", "NULL")
        self.verify_result(self.jumbo_pkt1, 0, pkt1_queue)
        self.verify_result(self.jumbo_pkt2, 0, pkt2_queue)

        # Failed to enable jumboframe per_queue
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 rxq %s rx_offload jumbo_frame on" % pkt1_queue, "testpmd> ")
        outstring = self.dut.send_expect("port start 0", "testpmd> ")
        self.verify("Fail" in outstring, "jumboframe can be set by queue.")

        # Succeed to enable jumboframe per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload jumbo_frame on", "testpmd> ")
        self.check_port_config("rx", offload)
        self.verify_result(self.jumbo_pkt1, 1, pkt1_queue)
        self.verify_result(self.jumbo_pkt2, 1, pkt2_queue)

        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_itf0, ETHER_STANDARD_MTU), "# ")
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_itf1, ETHER_STANDARD_MTU), "# ")

    def test_rxoffload_port_cmdline(self):
        """
        Set Rx offload by port in cmdline.
        """
        # Define rx checksum packets
        self.rxcksum_pkt1 = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/TCP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.rxcksum_pkt2 = r'sendp([Ether(dst="%s")/IP(chksum=0x0)/TCP(chksum=0xf)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.rxcksum_pkt3 = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/UDP(chksum=0xf)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.rxcksum_pkt4 = r'sendp([Ether(dst="%s")/IP(chksum=0x0)/UDP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        flags = []

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --enable-rx-cksum")
        self.dut.send_expect("set fwd csum", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        offload = ['ipv4_cksum', 'udp_cksum', 'tcp_cksum']
        self.check_port_config("rx", offload)

        # Check the rx checksum flags
        self.checksum_valid_flags(self.rxcksum_pkt1, "rx", [])
        self.checksum_valid_flags(self.rxcksum_pkt2, "rx", ["ipv4","tcp"])
        self.checksum_valid_flags(self.rxcksum_pkt3, "rx", ["udp"])
        self.checksum_valid_flags(self.rxcksum_pkt4, "rx", ["ipv4"])

        # Disable the rx cksum per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload udp_cksum off", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum']
        self.check_port_config("rx", offload)
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload ipv4_cksum off", "testpmd> ")
        offload = ['tcp_cksum']
        self.check_port_config("rx", offload)
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload tcp_cksum off", "testpmd> ")
        self.check_port_config("rx", "NULL")

        # Enable the rx cksum per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload ipv4_cksum on", "testpmd> ")
        offload = ['ipv4_cksum']
        self.check_port_config("rx", offload)
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload tcp_cksum on", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum']
        self.check_port_config("rx", offload)
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload udp_cksum on", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum', 'udp_cksum']
        self.check_port_config("rx", offload)

    def test_rxoffload_port_all(self):
        """
        Set all Rx offload capabilities by port.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4")
        capabilities = self.check_port_capability("rx")
        for capability in capabilities:
            if self.nic in ['foxville', 'cavium_a063', 'cavium_a064']  and capability == 'sctp_cksum':
                continue
            if capability != "jumboframe":
                self.dut.send_expect("port stop 0", "testpmd> ")
                self.dut.send_expect("port config 0 rx_offload %s on" % capability, "testpmd> ")
                offload = [capability]
                self.check_port_config("rx", offload)
                self.dut.send_expect("port stop 0", "testpmd> ")
                self.dut.send_expect("port config 0 rx_offload %s off" % capability, "testpmd> ")
                self.check_port_config("rx", "NULL")

    def test_rxoffload_queue(self):
        """
        Set Rx offload by queue.
        """
        # Only support ixgbe NICs
        self.verify(self.nic in ["niantic", "twinpond", "sagepond", "sageville", "foxville"], "%s nic not support rx offload setting by queue." % self.nic)
        # Define the vlan packets
        self.vlan_pkt1 = r'sendp([Ether(dst="%s")/Dot1Q(vlan=1)/IP(src="192.168.0.1",dst="192.168.0.3")/UDP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.vlan_pkt2 = r'sendp([Ether(dst="%s")/Dot1Q(vlan=1)/IP(src="192.168.0.2",dst="192.168.0.3")/UDP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4")
        self.dut.send_expect("set fwd rxonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        offload = ["NULL", "NULL", "NULL", "NULL"]
        self.check_queue_config("rx", offload)

        # Enable vlan_strip per_queue.
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 rxq 0 rx_offload vlan_strip on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 2 rx_offload vlan_strip on", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        queue = [0, 2]
        self.check_flag(self.vlan_pkt1, queue)
        self.check_flag(self.vlan_pkt2, queue)
        offload = ["vlan_strip", "NULL", "vlan_strip", "NULL"]
        self.check_queue_config("rx", offload)

        # Disable vlan_strip per_queue
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 rxq 3 rx_offload vlan_strip on", "testpmd> ")
        self.dut.send_expect("port 0 rxq 2 rx_offload vlan_strip off", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        queue = [0, 3]
        self.check_flag(self.vlan_pkt1, queue)
        self.check_flag(self.vlan_pkt2, queue)
        offload = ["vlan_strip", "NULL", "NULL", "vlan_strip"]
        self.check_queue_config("rx", offload)

       # Enable vlan_strip per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload vlan_strip on", "testpmd> ")
        offload = ["vlan_strip"]
        self.check_port_config("rx", offload)
        queue = [0, 1, 2, 3]
        self.check_flag(self.vlan_pkt1, queue)
        self.check_flag(self.vlan_pkt2, queue)

        # Disable vlan_strip per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 rx_offload vlan_strip off", "testpmd> ")
        self.check_port_config("rx", "NULL")
        queue = []
        self.check_flag(self.vlan_pkt1, queue)
        self.check_flag(self.vlan_pkt2, queue)

    def test_txoffload_port(self):
        """
        Set Tx offload by port.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --port-topology=loop")
        self.dut.send_expect("set fwd txonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        if (self.nic in ["fortville_eagle", "fortville_spirit","fortville_25g",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville","cavium_a063", "cavium_a064"]):
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port config 0 tx_offload mbuf_fast_free off", "testpmd> ")
        self.check_port_config("tx", "NULL")
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan" not in out, "There is vlan insert.")

        # Enable vlan_insert per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload vlan_insert on", "testpmd> ")
        self.dut.send_expect("tx_vlan set 0 1", "testpmd> ")
        offload = ["vlan_insert"]
        self.check_port_config("tx", offload)
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan 1" in out, "There is no vlan insert.")

        # Disable vlan_insert per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload vlan_insert off", "testpmd> ")
        self.check_port_config("tx", "NULL")
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan" not in out, "There is vlan insert.")

    def test_txoffload_port_cmdline(self):
        """
        Set Tx offload by port in cmdline.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4 --port-topology=loop --tx-offloads=0x0001")
        self.dut.send_expect("set fwd txonly", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")
        if (self.nic in ["fortville_eagle", "fortville_spirit","fortville_25g",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville"]):
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port config 0 tx_offload mbuf_fast_free off", "testpmd> ")
        offload = ["vlan_insert"]
        self.check_port_config("tx", offload)
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("tx_vlan set 0 1", "testpmd> ")
        self.dut.send_expect("port start 0", "testpmd> ")
        self.verify_link_up(20)
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan 1" in out, "There is no vlan insert.")

        # Disable vlan_insert per_queue
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 txq 0 tx_offload vlan_insert off", "testpmd> ")
        self.dut.send_expect("port 0 txq 1 tx_offload vlan_insert off", "testpmd> ")
        self.dut.send_expect("port 0 txq 2 tx_offload vlan_insert off", "testpmd> ")
        self.dut.send_expect("port 0 txq 3 tx_offload vlan_insert off", "testpmd> ")
        offload = ["vlan_insert"]
        self.check_port_config("tx", offload)
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan 1" in out, "There is no vlan insert.")

        # Disable vlan_insert per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload vlan_insert off", "testpmd> ")
        self.check_port_config("tx", "NULL")
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan" not in out, "There is vlan insert.")

        # Enable vlan_insert per_queue
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 txq 0 tx_offload vlan_insert on", "testpmd> ")
        self.dut.send_expect("port 0 txq 1 tx_offload vlan_insert on", "testpmd> ")
        self.dut.send_expect("port 0 txq 2 tx_offload vlan_insert on", "testpmd> ")
        self.dut.send_expect("port 0 txq 3 tx_offload vlan_insert on", "testpmd> ")
        outstring = self.dut.send_expect("port start 0", "testpmd> ")
        self.verify("Fail" in outstring, "vlan_insert can be set by queue.")

        # Enable vlan_insert per_port
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload vlan_insert on", "testpmd> ")
        offload = ["vlan_insert"]
        self.check_port_config("tx", offload)
        self.start_tcpdump(self.tester_itf0)
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("stop", "testpmd> ")
        out = self.get_tcpdump_package()
        self.verify("vlan 1" in out, "There is no vlan insert.")

    def test_txoffload_port_checksum(self):
        """
        Set Tx offload cksum.
        """
        # Define tx checksum packets
        self.txcksum_ipv4 = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.txcksum_tcp = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/TCP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.txcksum_udp = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/UDP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)
        self.txcksum_sctp = r'sendp([Ether(dst="%s")/IP(dst="192.168.0.1")/SCTP(sport=33, dport=34)/Raw("x"*20)], iface="%s")' % (self.pf_mac, self.tester_itf0)

        flags = []
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4")
        self.dut.send_expect("set fwd csum", "testpmd> ")
        self.dut.send_expect("set verbose 1", "testpmd> ")

        # Check the tx checksum flags
        self.checksum_valid_flags(self.txcksum_ipv4, "tx", [])
        self.checksum_valid_flags(self.txcksum_tcp, "tx", [])
        self.checksum_valid_flags(self.txcksum_udp, "tx", [])
        self.checksum_valid_flags(self.txcksum_sctp, "tx", [])

        # Disable the tx cksum per_port
        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port config 1 tx_offload ipv4_cksum on", "testpmd> ")
        self.dut.send_expect("port start 1", "testpmd> ")
        offload = ['ipv4_cksum']
        self.check_port_config("tx", offload, 1)
        self.checksum_valid_flags(self.txcksum_ipv4, "tx", ["ipv4"])

        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port config 1 tx_offload tcp_cksum on", "testpmd> ")
        self.dut.send_expect("port start 1", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum']
        self.check_port_config("tx", offload, 1)
        self.checksum_valid_flags(self.txcksum_tcp, "tx", ["ipv4","tcp"])

        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port config 1 tx_offload udp_cksum on", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum', 'udp_cksum']
        self.check_port_config("tx", offload, 1)
        self.checksum_valid_flags(self.txcksum_udp, "tx", ["ipv4","udp"])

        self.dut.send_expect("port stop 1", "testpmd> ")
        self.dut.send_expect("port config 1 tx_offload sctp_cksum on", "testpmd> ")
        offload = ['ipv4_cksum', 'tcp_cksum', 'udp_cksum', 'sctp_cksum']
        self.check_port_config("tx", offload, 1)
        self.checksum_valid_flags(self.txcksum_sctp, "tx", ["ipv4","sctp"])

    def test_txoffload_port_all(self):
        """
        Set all Tx offload capabilities by port.
        """
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4")
        capabilities = self.check_port_capability("tx")
        # Disable per queue capability first, if it is FVL/Fortpark.
        if (self.nic in ["fortville_eagle", "fortville_spirit","fortville_25g",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville"]):
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port config 0 tx_offload mbuf_fast_free off", "testpmd> ")
            self.dut.send_expect("port start 0", "testpmd> ")
        for capability in capabilities:
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port config 0 tx_offload %s on" % capability, "testpmd> ")
            offload = [capability]
            self.check_port_config("tx", offload)
            self.dut.send_expect("port stop 0", "testpmd> ")
            self.dut.send_expect("port config 0 tx_offload %s off" % capability, "testpmd> ")
            self.check_port_config("tx", "NULL")

    def test_txoffload_queue(self):
        """
        Set Rx offload by queue.
        """
        # Only support i40e NICs
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit","fortville_25g", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T"], "%s nic not support rx offload setting by queue." % self.nic)
        # Check offload configuration by port and by queue.
        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=4 --txq=4")
        offload = ["mbuf_fast_free"]
        self.check_port_config("tx", offload)
        offload = ["NULL", "NULL", "NULL", "NULL"]
        self.check_queue_config("tx", offload)

        # Disable mbuf_fast_free per_port.
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload mbuf_fast_free off", "testpmd> ")
        self.check_port_config("tx", "NULL")

        # Enable mbuf_fast_free per_queue.
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 txq 0 tx_offload mbuf_fast_free on", "testpmd> ")
        self.dut.send_expect("port 0 txq 1 tx_offload mbuf_fast_free on", "testpmd> ")
        self.dut.send_expect("port 0 txq 2 tx_offload mbuf_fast_free on", "testpmd> ")
        self.dut.send_expect("port 0 txq 3 tx_offload mbuf_fast_free on", "testpmd> ")
        offload = ["mbuf_fast_free", "mbuf_fast_free", "mbuf_fast_free", "mbuf_fast_free"]
        self.check_queue_config("tx", offload)

        # Disable mbuf_fast_free per_queue.
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port 0 txq 0 tx_offload mbuf_fast_free off", "testpmd> ")
        self.dut.send_expect("port 0 txq 1 tx_offload mbuf_fast_free off", "testpmd> ")
        self.dut.send_expect("port 0 txq 2 tx_offload mbuf_fast_free off", "testpmd> ")
        self.dut.send_expect("port 0 txq 3 tx_offload mbuf_fast_free off", "testpmd> ")
        offload = ["NULL", "NULL", "NULL", "NULL"]
        self.check_queue_config("tx", offload)

        # Enable mbuf_fast_free per_port.
        self.dut.send_expect("port stop 0", "testpmd> ")
        self.dut.send_expect("port config 0 tx_offload mbuf_fast_free on", "testpmd> ")
        offload = ["mbuf_fast_free"]
        self.check_port_config("tx", offload)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.send_expect("quit", "# ")

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        time.sleep(2)
        self.dut.kill_all()
