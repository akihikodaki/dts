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

Test the support of generic flow API by Poll Mode Drivers.

"""

import os
import random
import re
import time

import scapy.layers.inet
from scapy.utils import rdpcap

import framework.packet as packet
import framework.utils as utils
from framework.crb import Crb
from framework.dut import Dut
from framework.exception import VerifyFailure
from framework.pmd_output import PmdOutput
from framework.project_dpdk import DPDKdut
from framework.settings import DRIVERS, HEADER_SIZE
from framework.test_case import TestCase
from framework.virt_dut import VirtDut
from framework.test_case import check_supported_nic

MAX_VLAN = 4095
MAX_QUEUE = 15
testQueues = [16]
reta_lines = []
MAX_VFQUEUE = 3
MAX_PORT = 65535
MAX_TTL = 255
MAX_TOS = 255
TCP_PROTO = 6
UDP_PROTO = 17
SCTP_PROTO = 132
RESERVED_PROTO = 255

class TestGeneric_flow_api(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        global MAX_QUEUE
        if self.nic in ["powerville", "bartonhills", "kawela", "kawela_4"]:
            MAX_QUEUE = 7
        elif self.nic in ['foxville']:
            MAX_QUEUE = 3
        # Based on h/w type, choose how many ports to use
        self.dut_ports = self.dut.get_ports(self.nic)
        global valports
        valports = [_ for _ in self.dut_ports if self.tester.get_local_port(_) != -1]
        global portMask
        portMask = utils.create_mask(valports[:2])
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.cores = "1S/8C/1T"
        self.pf_cores = "1S/8C/1T"
        self.pmdout = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.tester_itf = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']

        self.session_secondary = self.dut.new_session()
        self.session_third = self.dut.new_session()
        self.outer_mac = "00:11:22:33:44:55"
        self.inner_mac = "00:11:22:33:44:66"
        self.wrong_mac = "00:11:22:33:44:77"
        self.vf_flag = 0
        self.pkt_obj = packet.Packet()
        self.app_path=self.dut.apps_name["test-pmd"]

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def setup_env(self):
        """
        This is to set up 1pf and 2vfs environment.
        The pf is bound to dpdk driver.
        """
        self.vf_flag = 1

        # PF is bound to igb_uio, while VF is bound to vfio-pci.
        self.dut.send_expect("modprobe uio", "#", 70)
        self.dut.send_expect("insmod ./" + self.target + "/kmod/igb_uio.ko", "#", 60)
        self.dut.send_expect("modprobe vfio-pci", "#", 70)

        # create two vfs
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 2, "igb_uio")
        self.sriov_vfs_port = self.dut.ports_info[self.dut_ports[0]]['vfs_port']
        try:
            for port in self.sriov_vfs_port:
                port.bind_driver(driver="vfio-pci")
        except Exception as e:
            self.destroy_env()
            raise Exception(e)

    def destroy_env(self):
        """
        This is to stop testpmd and destroy 1pf and 2vfs environment.
        """
        if self.vf_flag == 1:
            self.session_third.send_expect("quit", "# ")
            time.sleep(2)
            self.session_secondary.send_expect("quit", "# ")
            time.sleep(2)
            self.dut.send_expect("quit", "# ")
            time.sleep(2)
            self.dut.destroy_sriov_vfs_by_port(self.dut_ports[0])
        else:
            self.dut.send_expect("quit", "# ")
            time.sleep(2)
        self.vf_flag = 0

    def request_mbufs(self, queue_num):
        """
        default txq/rxq descriptor is 64
        """
        return 1024 * queue_num + 512

    def verify_result(self, pf_vf, expect_rxpkts, expect_queue, verify_mac, check_fdir=''):
        """
        verify the packet to the expected queue or be dropped
        : check_fdir=[exist|non-exist]
        """
        # self.tester.scapy_execute()
        # time.sleep(2)
        verify_mac = verify_mac.upper()

        if self.vf_flag == 1:
            out_vf0 = self.session_secondary.get_session_before(timeout=2)
            outstring_vf0 = self.session_secondary.send_expect("stop", "testpmd> ", 120)
            out_vf1 = self.session_third.get_session_before(timeout=2)
            outstring_vf1 = self.session_third.send_expect("stop", "testpmd> ", 120)
            self.logger.info("vf0: %s" % out_vf0)
            self.logger.info("vf1: %s" % out_vf1)
        out_pf = self.dut.get_session_output(timeout=2)
        outstring_pf = self.dut.send_expect("stop", "testpmd> ", 120)
        self.logger.info("pf: %s" % out_pf)
        time.sleep(2)

        if expect_rxpkts == "0":
            if pf_vf == "pf":
                self.verify(verify_mac not in out_pf, "the packet is not dropped.")
            elif pf_vf == "vf0":
                self.verify(verify_mac not in out_vf0, "the packet is not dropped.")
            else:
                self.verify(verify_mac not in out_vf1, "the packet is not dropped.")
        else:
            result_scanner = r"port\s*%s/queue\s?[0-9]+" % self.dut_ports[0]
            scanner = re.compile(result_scanner, re.DOTALL)
            if pf_vf == "pf":
                self.verify(verify_mac in out_pf, "the pf not receive the expect packet.")
                out_info = out_pf
            elif pf_vf == "vf0":
                self.verify(verify_mac in out_vf0, "the vf0 not receive the expect packet.")
                out_info = out_vf0
            else:
                self.verify(verify_mac in out_vf1, "the vf1 not receive the expect packet.")
                out_info = out_vf1

            # find the expected packet receive position
            mac_index = out_info.find("dst=%s" % verify_mac)
            m = scanner.findall(out_info)
            # get all the port 0/queue X str position
            # and calculate the port 0/queue X info of expected packet
            all_queue_index = []
            queue_index = 0
            find_index = False
            for i in range(len(m)):
                cur = out_info.find(m[i], all_queue_index[i - 1] + len(m[i - 1]) if i > 0 else 0)
                if cur > mac_index:
                    queue_index = i - 1
                    find_index = True
                    break
                all_queue_index.append(cur)
            if find_index is False:
                queue_index = len(m) - 1
            curr_queue = int(m[queue_index][len("port 0/queue"):])
            self.verify(int(expect_queue) == curr_queue, "the actual queue doesn't equal to the expected queue.")
        if check_fdir == 'exist':
            self.verify("RTE_MBUF_F_RX_FDIR" in out_pf, 'FDIR information should be printed.')
        elif check_fdir == 'non-exist':
            self.verify("FDIR" not in out_pf, 'FDIR information should not be printed.')
        self.dut.send_expect("start", "testpmd> ")

        if self.vf_flag == 1:
            self.session_secondary.send_expect("start", "testpmd> ")
            self.session_third.send_expect("start", "testpmd> ")
        return out_pf

    def launch_start_testpmd(self, queue='', pkt_filter_mode='', report_hash='', disable_rss=False, fwd='', verbose=''):
        """
        Launch and start testpmd
        """
        param = ''
        eal_param = ''
        if queue:
            param += '--rxq={} --txq={} '.format(queue, queue)
        if pkt_filter_mode:
            param += '--pkt-filter-mode={} '.format(pkt_filter_mode)
        if disable_rss:
            param += '--disable-rss '
        if report_hash:
            param += '--pkt-filter-report-hash={} '.format(report_hash)
        self.pmdout.start_testpmd("{}".format(self.cores), param=param, eal_param=eal_param)
        if fwd:
            self.pmdout.execute_cmd('set fwd rxonly', )
        if verbose:
            self.pmdout.execute_cmd('set verbose 1')
        self.pmdout.execute_cmd('start')
        self.pmdout.execute_cmd('show port info all')
        self.pmdout.wait_link_status_up(self.dut_ports[0])

    def compare_memory_rules(self, expectedRules):
        """
        dump all flow rules that have been created in memory and compare that total rules number with the given expected number
        to see if they are equal, as to get your conclusion after you have deleted any flow rule entry.
        """
        outstring = self.dut.send_expect("flow list 0", "testpmd> ")
        result_scanner = r'\d*.*?\d*.*?\d*.*?=>*'
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.findall(outstring)
        print("All flow entries are: ")
        for i in range(len(m)):
            print(m[i])
        print('Expected rules are: %d - actual are: %d' % (expectedRules, len(m)))
        self.verify(expectedRules == len(m), 'Total rules number mismatched')

    def all_flows_process(self, basic_flow_actions):
        """
        Verify all the flows' action and return the created rule number.
        Return all the rules' elements to create inconsistet packets.
        Return all the expect queues which are consistent to the rules.
        """
        extra_packet = []
        expected_queue = []
        rule_num = 0
        for flow_action in basic_flow_actions:
            # generate the flow rule and corresponding packet.
            flow_process = self.generate_random_command(**flow_action)
            # caculate the rule number created.
            rule_created = self.flow_test_process(flow_process, flow_action)
            if rule_created:
                rule_num += 1
                expected_queue.append(flow_process['queue'])
                extra_packet.append(flow_process['extrapacket'])
        # Configure a return value.
        extrapkt_rulenum = {'extrapacket': extra_packet, 'rulenum': rule_num, 'queue': expected_queue}

        return extrapkt_rulenum

    def verify_rulenum(self, rule_num):
        """
        Verify all the rules created.
        """
        # check if there are expected flow rules have been created
        self.compare_memory_rules(rule_num)
        # check if one rule destoried with success
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        self.compare_memory_rules(rule_num - 1)
        # check if all flow rules have been removed with success
        self.dut.send_expect("flow flush 0", "testpmd> ")
        self.compare_memory_rules(0)

    def flow_test_process(self, flow_process, flow_action):
        """
        Add a flow rule and verify the action
        """
        rule_created = 0
        flow_cmd = flow_process['cmd']
        flow_pkt = flow_process['pkt']
        flow_queue = flow_process['queue']
        if "validate" in flow_cmd:
            # ethertype invalid or queue id exceeds max queue number.
            if "86dd" in flow_cmd or "0800" in flow_cmd or "index %s" % str(MAX_QUEUE + 1) in flow_cmd:
                if self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T",
                                "niantic", "kawela_4", "kawela", "bartonhills", "twinville", "sagepond", "sageville",
                                "powerville", "carlsville"]:
                    self.dut.send_expect(flow_cmd, "error")
            elif "type is 0x8100" in flow_cmd:
                if self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville"]:
                    self.dut.send_expect(flow_cmd, "error")
            # vf queue id exceeds max vf queue number.
            elif (("vf0" in flow_action['flows']) or ("vf1" in flow_action['flows']) or (
                    "vf0" in flow_action['actions']) or ("vf1" in flow_action['actions'])) and (
                    ("index %s" % str(MAX_VFQUEUE + 1)) in flow_cmd):
                self.dut.send_expect(flow_cmd, "error")
            else:
                self.dut.send_expect(flow_cmd, "validated")
        elif "create" in flow_cmd:
            # ethertype invalid or queue id exceeds max queue number.
            if "86dd" in flow_cmd or "0800" in flow_cmd or "index %s" % str(MAX_QUEUE + 1) in flow_cmd:
                if self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T",
                                "niantic", "kawela_4", "kawela", "bartonhills", "twinville", "sagepond", "sageville",
                                "powerville", "carlsville"]:
                    self.dut.send_expect(flow_cmd, "error")
            elif "type is 0x8100" in flow_cmd:
                if self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville"]:
                    self.dut.send_expect(flow_cmd, "error")
            # vf queue id exceeds max vf queue number.
            elif (("vf0" in flow_action['flows']) or ("vf1" in flow_action['flows']) or (
                    "vf0" in flow_action['actions']) or ("vf1" in flow_action['actions'])) and (
                    ("index %s" % str(MAX_VFQUEUE + 1)) in flow_cmd):
                self.dut.send_expect(flow_cmd, "error")
            else:
                self.dut.send_expect(flow_cmd, "created")
                rule_created = 1

                # The rule is created successfully, so send the consistent packet.
                self.sendpkt(pktstr=flow_pkt)
                cur_mac = re.search("dst='(\S\S:\S\S:\S\S:\S\S:\S\S:\S\S)'", flow_pkt)
                cur_mac = cur_mac.group(1)
                if ("queue" in flow_action['actions']) or ("passthru" in flow_action['actions']):
                    if ("vf0" in flow_action['flows']) or ("vf0" in flow_action['actions']):
                        self.verify_result("vf0", expect_rxpkts="1", expect_queue=flow_queue, verify_mac=cur_mac)
                    elif "vf1" in flow_action['flows'] or "vf1" in flow_action['actions']:
                        self.verify_result("vf1", expect_rxpkts="1", expect_queue=flow_queue, verify_mac=cur_mac)
                    else:
                        self.verify_result("pf", expect_rxpkts="1", expect_queue=flow_queue, verify_mac=cur_mac)
                elif "drop" in flow_action['actions']:
                    if ("vf0" in flow_action['flows']) or ("vf0" in flow_action['actions']):
                        self.verify_result("vf0", expect_rxpkts="0", expect_queue="NULL", verify_mac=cur_mac)
                    elif ("vf1" in flow_action['flows']) or ("vf1" in flow_action['actions']):
                        self.verify_result("vf1", expect_rxpkts="0", expect_queue="NULL", verify_mac=cur_mac)
                    else:
                        self.verify_result("pf", expect_rxpkts="0", expect_queue="NULL", verify_mac=cur_mac)
                # L2-tunnel filter
                else:
                    if "vf0" in flow_action['actions']:
                        self.verify_result("vf0", expect_rxpkts="1", expect_queue="0", verify_mac=cur_mac)
                    elif "vf1" in flow_action['actions']:
                        self.verify_result("vf1", expect_rxpkts="1", expect_queue="0", verify_mac=cur_mac)
                    elif "pf" in flow_action['actions']:
                        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=cur_mac)
        # Return the status of the rule.
        return rule_created

    def generate_random_mac(self):
        return ':'.join('%02x' % random.randint(0, 255) for i in range(6))

    def generate_random_ip(self, is_ipv4):
        if is_ipv4 == True:
            return '.'.join('%s' % random.randint(0, 255) for i in range(4))
        else:
            return ':'.join('{:x}'.format(random.randint(0, 2 ** 16 - 1)) for i in range(8))

    def generate_random_int(self, minimum, maximum):
        return random.randint(minimum, maximum)

    def generate_random_command(self, create, flows=[], actions=[]):
        """
        Return random content for flow and action commands
        Parameters:
                    create           : create the rule or validate the rule
                    flows []         : assigned flow layers
                    actions []       : flow actions
        Return the packets including the consistent packet and inconsistent
        packet.
        Return the expected queue which the packet distributed.
        """
        # Define the flow rule command.
        if ('vf0' in flows) or ('vf1' in flows):
            cmd_fmt = "flow %(create)s 0 ingress transfer pattern %(flow)s / end actions %(action)s end"
        else:
            cmd_fmt = "flow %(create)s 0 ingress pattern %(flow)s / end actions %(action)s end"
        # Record the elements of the rule, ready for the configuration
        # of packets inconsistent to the rule.
        extrapacket = {'vlan': '', 'for ': '', 'ipv4': '', 'ipv6': '', 'sip': '', 'dip': '', 'proto': '', 'tos': '',
                       'ttl': '', 'tcp': '', 'udp': '', 'sctp': '', 'sport': '', 'dport': '', 'vni': '', 'tni': '',
                       'ineth': '', 'invlan': ''}
        # Define the packet string, which is consistent to the flow rule.
        if ('vf0' in flows) or ('vf1' in flows) or ('vf0' in actions) or ('vf1' in actions):
            pkt = "Ether(dst='%s')" % self.wrong_mac
        else:
            pkt = "Ether(dst='%s')" % self.pf_mac
        # Define the flow string of the rule
        # Signature mode
        if 'fuzzy' in flows:
            thresh = self.generate_random_int(1, 15)
            flow_str = "fuzzy thresh is %d " % thresh
        else:
            flow_str = "eth "
        # Configure the flow and packet and extrapacket string
        for flow_type in flows:
            if flow_type == "dst_mac":
                dmac = self.outer_mac
                flow_str += "dst is %s " % dmac
                pkt = "Ether(dst='%s')" % dmac
            elif flow_type == "ether":
                if "dst_mac" in flows:
                    dmac = self.outer_mac
                    pkt = "Ether(dst='%s'" % dmac
                else:
                    pkt = "Ether(dst='%s'" % self.pf_mac
                if 'eaps' in flows:
                    eth_type = "0x8100"
                    pkt += ",type=0x8100)/Raw('x' * 20)"
                elif 'lwapp' in flows:
                    eth_type = "0x86bb"
                    pkt += ",type=0x86bb)/Raw('x' * 20)"
                elif 'lldp' in flows:
                    eth_type = "0x88cc"
                    pkt += ",type=0x88cc)/Raw('x' * 20)"
                elif 'ipv6_eth' in flows:
                    eth_type = "0x86dd"
                    pkt += ",type=0x86dd)/Raw('x' * 20)"
                elif 'arp' in flows:
                    eth_type = "0x0806"
                    pkt = "Ether(dst='ff:ff:ff:ff:ff:ff')/ARP(pdst='192.168.1.1')"
                elif 'ip_eth' in flows:
                    eth_type = "0x0800"
                    pkt += ",type=0x0800)/Raw('x' * 20)"
                elif 'ppp' in flows:
                    eth_type = "0x8864"
                    pkt += ",type=0x8864)/Raw('x' * 20)"
                elif 'mpls' in flows:
                    eth_type = "0x8847"
                    pkt += ",type=0x8847)/Raw('x' * 20)"
                else:
                    eth_type = "0x8000"
                    pkt += ",type=0x8000)/Raw('x' * 20)"
                flow_str += "type is %s " % eth_type
            elif flow_type == "vlan":
                vlan = self.generate_random_int(0, MAX_VLAN)
                flow_str += "/ vlan tci is %d " % vlan
                pkt += "/Dot1Q(vlan=%d)" % vlan
                extrapacket['vlan'] = str(vlan)
            elif flow_type == "ipv4":
                is_ipv4 = True
                flow_str += "/ ipv4 "
                pkt += "/IP("
                sip = self.generate_random_ip(is_ipv4)
                dip = self.generate_random_ip(is_ipv4)
                if 'dip' in flows:
                    flow_str += "dst is %s " % dip
                    extrapacket['dip'] = dip
                    pkt += "dst='%s'" % dip
                if 'sip' in flows:
                    flow_str += "src is %s " % sip
                    extrapacket['sip'] = sip
                    pkt += ", src='%s'" % sip
                if 'proto' in flows:
                    if "udp" in flows:
                        proto = UDP_PROTO
                    elif "tcp" in flows:
                        proto = TCP_PROTO
                    elif "sctp" in flows:
                        proto = SCTP_PROTO
                    else:
                        proto = RESERVED_PROTO
                    extrapacket['proto'] = str(proto)
                    flow_str += "proto is %d " % proto
                    if 'sip' in flows or 'dip' in flows:
                        pkt += ", proto=%d" % proto
                    # for 2-tuple
                    else:
                        pkt += "proto=%d" % proto
                if 'tos' in flows:
                    tos = self.generate_random_int(0, MAX_TOS)
                    flow_str += "tos is %d " % tos
                    pkt += ", tos=%d" % tos
                    extrapacket['tos'] = tos
                if 'ttl' in flows:
                    ttl = self.generate_random_int(1, MAX_TTL)
                    flow_str += "ttl is %d " % ttl
                    pkt += ", ttl=%d" % ttl
                    extrapacket['ttl'] = ttl
                pkt += ")"
            elif flow_type == "ipv6":
                is_ipv4 = False
                flow_str += "/ ipv6 "
                sip = self.generate_random_ip(is_ipv4)
                dip = self.generate_random_ip(is_ipv4)
                if 'sip' in flows:
                    flow_str += "src is %s " % sip
                    extrapacket['sip'] = sip
                if 'dip' in flows:
                    flow_str += "dst is %s " % dip
                    extrapacket['dip'] = dip
                pkt += "/IPv6(src='%s', dst='%s'" % (sip, dip)
                if 'proto' in flows:
                    if "udp" in flows:
                        proto = UDP_PROTO
                    elif "tcp" in flows:
                        proto = TCP_PROTO
                    elif "sctp" in flows:
                        proto = SCTP_PROTO
                    else:
                        proto = RESERVED_PROTO
                    extrapacket['proto'] = str(proto)
                    flow_str += "proto is %d " % proto
                    pkt += ", nh=%d" % proto
                if 'tc' in flows:
                    tc = self.generate_random_int(0, 255)
                    flow_str += "tc is %d " % tc
                    pkt += ", tc=%d" % tc
                    extrapacket['tos'] = str(tc)
                if 'hop' in flows:
                    hop = self.generate_random_int(1, 255)
                    flow_str += "hop is %d " % hop
                    pkt += ", hlim=%d" % hop
                    extrapacket['ttl'] = str(hop)
                if 'sctp' in flows:
                    pkt += ", nh=%d" % SCTP_PROTO
                    extrapacket['proto'] = str(SCTP_PROTO)
                pkt += ")"
            elif flow_type == "tcp":
                flow_str += "/ tcp "
                pkt += "/TCP("
                dport = self.generate_random_int(0, MAX_PORT)
                sport = self.generate_random_int(0, MAX_PORT)
                if 'dport' in flows:
                    flow_str += "dst is %s " % dport
                    extrapacket['dport'] = dport
                    pkt += "dport=%s" % dport
                if 'sport' in flows:
                    flow_str += "src is %s " % sport
                    extrapacket['sport'] = sport
                    pkt += ", sport=%s" % sport
                pkt += ")"
            elif flow_type == "udp":
                flow_str += "/ udp "
                pkt += "/UDP("
                dport = self.generate_random_int(0, MAX_PORT)
                sport = self.generate_random_int(0, MAX_PORT)
                if 'dport' in flows:
                    flow_str += "dst is %s " % dport
                    extrapacket['dport'] = dport
                    pkt += "dport=%s" % dport
                if 'sport' in flows:
                    flow_str += "src is %s " % sport
                    extrapacket['sport'] = sport
                    pkt += ", sport=%s" % sport
                pkt += ")"
            elif flow_type == "sctp":
                flow_str += "/ sctp "
                pkt += "/SCTP("
                dport = self.generate_random_int(0, MAX_PORT)
                sport = self.generate_random_int(0, MAX_PORT)
                if 'dport' in flows:
                    flow_str += "dst is %s " % dport
                    extrapacket['dport'] = dport
                    pkt += "dport=%s" % dport
                if 'sport' in flows:
                    flow_str += "src is %s " % sport
                    extrapacket['sport'] = sport
                    pkt += ", sport=%s" % sport
                if 'tag' in flows:
                    flow_str += "tag is 1 "
                    pkt += ", tag=1"
                pkt += ")"
            elif flow_type == "vxlan":
                flow_str += "/ vxlan "
                if 'vni' in flows:
                    vni = self.generate_random_int(0, MAX_VLAN)
                    flow_str += "vni is %d " % vni
                    pkt += "/VXLAN(vni=%d, flags=8)" % vni
                    extrapacket['vni'] = str(vni)
                else:
                    pkt += "/VXLAN()"
            elif flow_type == "nvgre":
                flow_str += "/ nvgre "
                if 'tni' in flows:
                    vni = self.generate_random_int(0, MAX_VLAN)
                    flow_str += "tni is %d " % vni
                    pkt += "/NVGRE(TNI=%d)" % vni
                    extrapacket['tni'] = str(vni)
                else:
                    pkt += "/NVGRE()"
            elif flow_type == "ineth":
                inmac = self.inner_mac
                flow_str += "/ eth dst is %s " % inmac
                pkt += "/Ether(dst='%s')" % inmac
                extrapacket['ineth'] = inmac
            elif flow_type == "invlan":
                invlan = self.generate_random_int(0, MAX_VLAN)
                flow_str += "/ vlan tci is %d " % invlan
                pkt += "/Dot1Q(vlan=%d)" % invlan
                extrapacket['invlan'] = str(invlan)
            elif flow_type == "vf0":
                flow_str += "/ vf id is 0"
            elif flow_type == "vf1":
                flow_str += "/ vf id is 1"
        pkt += "/Raw('x' * 20)"
        # Define the action string of the rule.
        act_str = ""
        index = 0
        for action in actions:
            if action == "pf":
                act_str += "pf / "
            elif action == "vf0":
                act_str += "vf id 0 / "
            elif action == "vf1":
                act_str += "vf id 1 / "
            elif action == "queue":
                if ("vf0" in flows) or ("vf1" in flows) or ("vf0" in actions) or ("vf1" in actions):
                    index = self.generate_random_int(0, MAX_VFQUEUE)
                else:
                    index = self.generate_random_int(0, MAX_QUEUE)
                act_str += "queue index %d / " % index
            elif action == "invalid":
                if ("vf0" in flows) or ("vf1" in flows):
                    index = MAX_VFQUEUE + 1
                else:
                    index = MAX_QUEUE + 1
                act_str += "queue index %d / " % index
            elif action == "drop":
                act_str += "drop / "
                index = "NULL"
            elif action == "passthru":
                act_str += "passthru / "
                index = 0
            elif action == "flag":
                act_str += "flag / "
            elif action == "mark":
                act_str += "mark id 3 / "
        # Configure the whole flow rule.
        command = cmd_fmt % {"create": create,
                             "flow": flow_str,
                             "action": act_str}
        # Configure the return value.
        flow_process = {'cmd': command, 'pkt': pkt, 'queue': index, 'extrapacket': extrapacket}

        return flow_process

    def sendpkt(self, pktstr, count=1):
        import sys
        py_version = sys.version
        if py_version.startswith('3.'):
            self.pkt_obj.pktgen.pkts.clear()
        else:
            del self.pkt_obj.pktgen.pkts[:]
        self.pkt_obj.append_pkt(pktstr)
        self.pkt_obj.send_pkt(self.tester, tx_port=self.tester_itf, count=count)

    def send_packet(self, itf, tran_type, enable=None):
        """
        Sends packets for l2_payload.
        """
        global reta_lines
        global name
        global value
        self.tester.scapy_foreground()
        self.dut.send_expect("start", "testpmd>")
        mac = self.dut.get_mac_address(0)

        # send packet with different source and dest ip
        if tran_type == "l2_payload":
            if enable == "ovlan":
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/Dot1Q(id=0x8100,vlan=4)/Dot1Q(id=0x8100,vlan=2,type=0xaaaa)/Raw(load="x"*60)], iface="%s")' % (
                mac, itf, itf)
            elif enable == "ivlan":
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/Dot1Q(id=0x8100,vlan=1)/Dot1Q(id=0x8100,vlan=3,type=0xaaaa)/Raw(load="x"*60)], iface="%s")' % (
                mac, itf, itf)
            else:
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/Dot1Q(id=0x8100,vlan=1)/Dot1Q(id=0x8100,vlan=2,type=0xaaaa)/Raw(load="x"*60)], iface="%s")' % (
                mac, itf, itf)
            self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        else:
            print("\ntran_type error!\n")

        out = self.dut.get_session_output(timeout=1)
        self.dut.send_expect("stop", "testpmd>")
        lines = out.split("\r\n")
        reta_line = {}
        # collect the hash result and the queue id
        for line in lines:
            line = line.strip()
            if len(line) != 0 and line.strip().startswith("port "):
                reta_line = {}
                rexp = r"port (\d)/queue (\d{1,2}): received (\d) packets"
                m = re.match(rexp, line.strip())
                if m:
                    reta_line["port"] = m.group(1)
                    reta_line["queue"] = m.group(2)

            elif len(line) != 0 and line.startswith(("src=",)):
                for item in line.split("-"):
                    item = item.strip()

                    if(item.startswith("RSS hash")):
                        name, value = item.split("=", 1)

                reta_line[name.strip()] = value.strip()
                reta_lines.append(reta_line)

        self.append_result_table()

    def append_result_table(self):
        """
        Append the hash value and queue id into table.
        """

        global reta_lines

        # append the the hash value and queue id into table
        self.result_table_create(
            ['packet index', 'hash value', 'hash index', 'queue id'])
        i = 0

        for tmp_reta_line in reta_lines:

            # compute the hash result of five tuple into the 7 LSBs value.
            hash_index = int(tmp_reta_line["RSS hash"], 16)
            self.result_table_add(
                [i, tmp_reta_line["RSS hash"], hash_index, tmp_reta_line["queue"]])
            i = i + 1
    def test_syn_filter(self):
        """
        Only supported by ixgbe and igb.
        """
        self.verify(self.nic in ["niantic", "kawela_4", "kawela", "bartonhills", "twinville", "sagepond", "sageville",
                                 "powerville", "foxville"], "%s nic not support SYN filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # validate and create the flow rules
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 3 / end",
            "validated")

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 3 / end",
            "created")
        # send the packets and verify the results
        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)

        self.verify_result("pf", expect_rxpkts="1", expect_queue="3", verify_mac=self.pf_mac)
        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="PA")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)

        # the ipv6 rule is conflicted with ipv4 rule.
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 120)

        # validate and create the flow rules
        q_idx = '2' if self.nic == 'foxville' else '4'
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth / ipv6 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index %s / end" %(q_idx),
            "validated")

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index %s / end" %(q_idx),
            "created")
        # send the packets and verify the results
        self.sendpkt(pktstr='Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue=q_idx, verify_mac=self.pf_mac)

        self.sendpkt(pktstr='Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/TCP(dport=80,flags="PA")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)

        self.verify_rulenum(1)

    def test_n_tuple_filter(self):
        """
        only supported by ixgbe and igb
        """
        self.verify(self.nic in ["niantic", "kawela_4", "kawela",
                                 "twinville", "foxville"], "%s nic not support n-tuple filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        # create the flow rules
        basic_flow_actions = [
            {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'udp', 'sport', 'dport'],
             'actions': ['queue']},
            {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'tcp', 'sport', 'dport'],
             'actions': ['queue']},
            {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'sctp', 'sport', 'dport'],
             'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'sip', 'dip'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'udp', 'sport', 'dport'],
             'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'tcp', 'sport', 'dport'],
             'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'sctp', 'sport', 'dport'],
             'actions': ['queue']}
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        extra_packet = extrapkt_rulenum['extrapacket']
        # send the packets inconsistent to the rules.
        self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s")/Raw("x" * 20)' % (self.pf_mac, extra_packet[0]['dip'], extra_packet[0]['sip']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s")/SCTP(sport=%s,dport=%s)/Raw("x" * 20)' % (
            self.pf_mac, extra_packet[3]['dip'], extra_packet[3]['sip'], extra_packet[3]['sport'],
            extra_packet[3]['dport']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s")/SCTP(sport=%s,dport=%s)/Raw("x" * 20)' % (self.pf_mac, extra_packet[0]['sip'], extra_packet[0]['dip'], extra_packet[3]['sport'],
            extra_packet[3]['dport']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][0], verify_mac=self.pf_mac)

        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_2_tuple_filter(self):
        """
        only supported by igb
        """
        self.verify(self.nic in ["bartonhills", "powerville", "foxville", "fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g"], "%s nic not support 2-tuple filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # i350 and 82580 only support 2-tuple, and don't support SCTP
        # create the flow rules
        if self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g"]:
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['ipv4', 'udp', 'dport'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ipv4', 'tcp', 'dport'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'udp', 'dport'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'tcp', 'dport'], 'actions': ['queue']},
            ]
        else:
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['ipv4', 'proto', 'udp', 'dport'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ipv4', 'proto', 'tcp', 'dport'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'proto', 'udp', 'dport'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'proto', 'tcp', 'dport'], 'actions': ['queue']},
            ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        extra_packet = extrapkt_rulenum['extrapacket']
        # send the packets inconsistent to the rules.
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=22,dport=24)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=32,dport=34)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_ethertype_filter(self):
        """
        supported by i40e, ixgbe and igb
        """
        self.verify(self.nic in ["niantic", "columbiaville_25g","columbiaville_100g","kawela_4", "kawela", "bartonhills", "twinville", "sagepond", "sageville",
                                 "powerville", "fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville","columbiaville_25g","columbiaville_100g"], "%s nic not support ethertype filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # i40e,ixgbe and igb support different packet types.
        if (self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T","columbiaville_25g","columbiaville_100g"]):

            basic_flow_actions = [
                {'create': 'validate', 'flows': ['ether', 'arp'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ether', 'arp'], 'actions': ['invalid']},
                {'create': 'validate', 'flows': ['ether', 'lldp'], 'actions': ['invalid']},
                {'create': 'validate', 'flows': ['ether', 'ipv6_eth'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ether', 'ip_eth'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ether', 'eaps'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'arp'], 'actions': ['invalid']},
                {'create': 'create', 'flows': ['ether', 'arp'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'lwapp'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'ppp'], 'actions': ['drop']},
                {'create': 'create', 'flows': ['dst_mac', 'ether', 'mpls'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'lldp'], 'actions': ['queue']},
            ]
            extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
            rule_num = extrapkt_rulenum['rulenum']
            self.verify_rulenum(rule_num)

        else:
            # create the flow rules
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['ether', 'arp'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ether', 'lldp'], 'actions': ['invalid']},
                {'create': 'validate', 'flows': ['ether', 'ipv6_eth'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'lldp'], 'actions': ['invalid']},
                {'create': 'create', 'flows': ['ether', 'arp'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ether', 'lldp'], 'actions': ['queue']},
            ]
            extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
            self.sendpkt(pktstr='Ether(dst="%s",type=0x88E5)/Raw("x" * 20)' % self.pf_mac)

            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
            rule_num = extrapkt_rulenum['rulenum']
            self.verify_rulenum(rule_num)

    def test_fdir_for_L2_payload(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir L2 payload filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.pf_cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        basic_flow_actions = [
            {'create': 'validate', 'flows': ['vlan'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['ether', 'ppp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['ether', 'ppp'], 'actions': ['queue']},
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def sendpkt_check_result(self, src_mac, dst_mac, mark, mark_id, rss, pctype=""):

        mark_info = "FDIR matched ID=0x%d" % mark_id

        if pctype == "ipv4-other":
            # packet type:I40E_FILTER_PCTYPE_NONF_IPV4_OTHER
            self.sendpkt(pktstr='Ether(src="%s",dst="%s")/IP()' % (src_mac, dst_mac))
        elif pctype == "ipv4-udp":
            # packet type:I40E_FILTER_PCTYPE_NONF_IPV4_UDP
            self.sendpkt(pktstr='Ether(src="%s",dst="%s")/IP()/UDP()' % (src_mac, dst_mac))
        elif pctype == "ipv4-tcp":
            # packet type:I40E_FILTER_PCTYPE_NONF_IPV4_UDP
            self.sendpkt(pktstr='Ether(src="%s",dst="%s")/IP()/TCP()' % (src_mac, dst_mac))

        out_pf = self.dut.get_session_output(timeout=2)
        if mark == 1:
            self.verify(mark_info in out_pf, "the packet not mark the expect index.")
        else:
            if mark_info in out_pf:
                raise Exception("the packet should not mark the expect index.")
        if rss == 1:
            self.verify("RSS queue=" in out_pf, "the packet not rss.")

    def test_fdir_L2_mac_filter_basic_for_ipv4_other(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV",
                                 "fortpark_BASE-T","fortville_25g","carlsville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # only dst mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-other")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")

        self.compare_memory_rules(0)

        # only src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")

        self.compare_memory_rules(0)

        # dst mac and src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-other")
        self.sendpkt_check_result('88:88:88:88:88:88', '22:22:22:22:22:22', 0, 1, 0, "ipv4-other")

        # list
        self.compare_memory_rules(1)

        # destroy
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 120)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0)

        self.compare_memory_rules(0)

    def test_fdir_L2_mac_filter_basic_for_ipv4_udp(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV",
                                 "fortpark_BASE-T","fortville_25g","carlsville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # only dst mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-udp")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-udp")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-udp")

        self.compare_memory_rules(0)

        # only src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / udp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / udp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-udp")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-udp")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-udp")

        self.compare_memory_rules(0)

        # dst mac and src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / udp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-udp")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-udp")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-udp")
        self.sendpkt_check_result('88:88:88:88:88:88', '22:22:22:22:22:22', 0, 1, 0, "ipv4-udp")

        # list
        self.compare_memory_rules(1)

        # destroy
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 120)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-udp")

        self.compare_memory_rules(0)

    def test_fdir_L2_mac_filter_basic_for_ipv4_tcp(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV",
                                 "fortpark_BASE-T","fortville_25g","carlsville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # only dst mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-tcp")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-tcp")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-tcp")

        self.compare_memory_rules(0)

        # only src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-tcp")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-tcp")

        # list
        self.compare_memory_rules(1)

        # flush
        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-tcp")

        self.compare_memory_rules(0)

        # dst mac and src mac
        # validate
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "validated")

        # create
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / tcp / end actions mark id 1 / rss / end",
            "created")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-tcp")
        self.sendpkt_check_result('88:88:88:88:88:88', '11:11:11:11:11:11', 0, 1, 0, "ipv4-tcp")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 1, 0, "ipv4-tcp")
        self.sendpkt_check_result('88:88:88:88:88:88', '22:22:22:22:22:22', 0, 1, 0, "ipv4-tcp")

        # list
        self.compare_memory_rules(1)

        # destroy
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 120)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-tcp")

        self.compare_memory_rules(0)

    def test_fdir_L2_mac_filter_complex(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV",
                                 "fortpark_BASE-T","fortville_25g","carlsville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("port config all rss all", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # delete the first rule of three rules
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end",
            "created")

        self.compare_memory_rules(3)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 1, 2, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '33:33:33:33:33:33', 1, 3, 1, "ipv4-other")

        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ", 120)

        self.compare_memory_rules(2)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 1, 2, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '33:33:33:33:33:33', 1, 3, 1, "ipv4-other")

        self.dut.send_expect("flow flush 0", "testpmd> ")

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 0, 1, 0, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 2, 0, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '33:33:33:33:33:33', 0, 3, 0, "ipv4-other")

        # delete the second rule of three rules
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end",
            "created")

        self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ", 120)

        self.compare_memory_rules(2)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 0, 2, 0, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '33:33:33:33:33:33', 1, 3, 1, "ipv4-other")

        self.dut.send_expect("flow flush 0", "testpmd> ")

        # delete the third rule of three rules
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 22:22:22:22:22:22 / ipv4 / end actions mark id 2 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 33:33:33:33:33:33 / ipv4 / end actions mark id 3 / rss / end",
            "created")

        self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ", 120)

        self.compare_memory_rules(2)

        self.sendpkt_check_result('99:99:99:99:99:99', '11:11:11:11:11:11', 1, 1, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '22:22:22:22:22:22', 1, 2, 1, "ipv4-other")
        self.sendpkt_check_result('99:99:99:99:99:99', '33:33:33:33:33:33', 0, 3, 0, "ipv4-other")

        self.dut.send_expect("flow flush 0", "testpmd> ")

    def test_fdir_L2_mac_filter_negative(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV",
                                 "fortpark_BASE-T","fortville_25g","carlsville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=test1" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # ip in command
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 dst is 1.1.1.1 / end actions mark id 2 / rss / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 dst is 1.1.1.1 / end actions mark id 2 / rss / end",
            "error")

        # udp in command
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp dst is 111 / end actions mark id 2 / rss / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / udp dst is 111 / end actions mark id 2 / rss / end",
            "error")

        # tcp in command
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp dst is 111 / end actions mark id 2 / rss / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / tcp dst is 111 / end actions mark id 2 / rss / end",
            "error")

        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 3 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end",
            "Invalid")

        self.dut.send_expect("flow flush 0", "testpmd> ", 120)

        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 / ipv4 / end actions mark id 1 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "Invalid")

        self.dut.send_expect("flow flush 0", "testpmd> ", 120)

        self.dut.send_expect(
            "flow create 0 ingress pattern eth src is 99:99:99:99:99:99 dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 1 / rss / end",
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is 11:11:11:11:11:11 / ipv4 / end actions mark id 3 / rss / end",
            "Invalid")

    def test_fdir_for_vlan(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir vlan filter" % self.nic)
        self.setup_env()
        # start testpmd on pf
        self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024 --legacy-mem" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        # start testpmd on vf0
        self.session_secondary.send_expect("%s -c 0x1e0000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf1 -- -i --rxq=4 --txq=4 --disable-rss --pkt-filter-mode=perfect" % (self.app_path, self.sriov_vfs_port[0].pci), "testpmd>", 120)
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set verbose 1", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        # start testpmd on vf1
        self.session_third.send_expect("%s -c 0x1e000000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf2 -- -i --rxq=4 --txq=4 --disable-rss --pkt-filter-mode=perfect" % (self.app_path, self.sriov_vfs_port[1].pci), "testpmd>", 120)
        self.session_third.send_expect("set fwd rxonly", "testpmd>")
        self.session_third.send_expect("set verbose 1", "testpmd>")
        self.session_third.send_expect("start", "testpmd>")
        time.sleep(2)
        # create the flow rules
        basic_flow_actions = [
            {'create': 'create', 'flows': ['vlan', 'ipv4'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'udp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'tcp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'sctp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'vf0'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'sctp', 'vf1'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'sctp'], 'actions': ['drop']},
            {'create': 'create', 'flows': ['vlan', 'ipv4', 'udp', 'vf1'], 'actions': ['drop']},
            {'create': 'create', 'flows': ['vlan', 'ipv6'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'udp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'tcp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'sctp'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'vf0'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'tcp', 'vf1'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'sctp'], 'actions': ['drop']},
            {'create': 'create', 'flows': ['vlan', 'ipv6', 'tcp', 'vf1'], 'actions': ['drop']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'udp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'tcp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'sctp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'vf0'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'sctp', 'vf1'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'sctp'], 'actions': ['drop']},
            {'create': 'validate', 'flows': ['vlan', 'ipv4', 'udp', 'vf1'], 'actions': ['drop']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'udp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'tcp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sctp'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'vf0'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'tcp', 'vf1'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sctp'], 'actions': ['drop']},
            {'create': 'validate', 'flows': ['vlan', 'ipv6', 'tcp', 'vf1'], 'actions': ['drop']}
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        extra_packet = extrapkt_rulenum['extrapacket']
        # send the packets with dst/src ip and dst/src port.
        self.sendpkt(pktstr='Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.1", dst="192.168.0.2", proto=3)/Raw("x" * 20)' % (self.pf_mac, extra_packet[0]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][0], verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3)/UDP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[1]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][1], verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[2]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][2], verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.1", dst="192.168.0.2", tos=3, ttl=3)/SCTP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[3]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][3], verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.1", dst="192.168.0.2", ttl=3)/TCP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[3]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP()/UDP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[2]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/SCTP(sport=44,dport=45,tag=1)/Raw("x" * 20)' % (self.pf_mac, extra_packet[6]['vlan']))
        self.verify_result("pf", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IP(src="192.168.0.5", dst="192.168.0.6", tos=3, ttl=3)/UDP(sport=44,dport=45)/SCTPChunkData(data="X" * 20)' % (
            self.outer_mac, extra_packet[7]['vlan']))
        self.verify_result("vf1", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.outer_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=1, nh=5, hlim=10)/Raw("x" * 20)' % (
            self.pf_mac, extra_packet[8]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][8], verify_mac=self.pf_mac)
        self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)' % (self.pf_mac, extra_packet[9]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][9], verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/TCP(sport=32,dport=33)/Raw("x" * 20)' % (
            self.pf_mac, extra_packet[10]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][10], verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)' % (
            self.pf_mac, extra_packet[11]['vlan']))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][11], verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=4, nh=132, hlim=40)/SCTP(sport=44,dport=45,tag=1)/SCTPChunkData(data="X" * 20)' % (
            self.pf_mac, extra_packet[14]['vlan']))
        self.verify_result("pf", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.pf_mac)
        self.sendpkt(
            'Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/TCP(sport=32,dport=33)/Raw("x" * 20)' % (
                self.outer_mac, extra_packet[15]['vlan']))
        self.verify_result("vf1", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.outer_mac)

        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_fdir_for_ipv4(self):
        """
        only supported by i40e and ixgbe
        """
        self.verify(self.nic in ["niantic", "columbiaville_25g","columbiaville_100g","twinville", "sagepond", "sageville",
                                 "fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville"],
                    "%s nic not support fdir ipv4 filter" % self.nic)
        # i40e
        if (self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville", "carlsville"]):
            self.setup_env()
            # start testpmd on pf
            self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024 --legacy-mem" % self.pf_pci)
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)
            # start testpmd on vf0
            self.session_secondary.send_expect("%s -c 0x1e0000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf1 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[0].pci), "testpmd>", 120)
            self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
            self.session_secondary.send_expect("set verbose 1", "testpmd>")
            self.session_secondary.send_expect("start", "testpmd>")
            time.sleep(2)
            # start testpmd on vf1
            self.session_third.send_expect("%s -c 0x1e000000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf2 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[1].pci), "testpmd>", 120)
            self.session_third.send_expect("set fwd rxonly", "testpmd>")
            self.session_third.send_expect("set verbose 1", "testpmd>")
            self.session_third.send_expect("start", "testpmd>")
            time.sleep(2)

            # validate and create the flow rules
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'ttl', 'udp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'tos', 'tcp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['drop']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'vf0'], 'actions': ['invalid']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'vf0'], 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag', 'vf1'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['passthru', 'flag']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'ttl', 'udp', 'sport', 'dport'],
                 'actions': ['queue', 'flag']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'tos', 'tcp', 'sport', 'dport'],
                 'actions': ['queue', 'mark']},
                {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'proto'], 'actions': ['passthru', 'mark']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'ttl', 'udp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'tos', 'tcp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['drop']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'vf0'], 'actions': ['invalid']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto', 'vf0'], 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag', 'vf1'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv4', 'sip', 'dip', 'tos', 'ttl', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['passthru', 'flag']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'ttl', 'udp', 'sport', 'dport'],
                 'actions': ['queue', 'flag']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'tos', 'tcp', 'sport', 'dport'],
                 'actions': ['queue', 'mark']},
                {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'proto'], 'actions': ['passthru', 'mark']}
            ]
            extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
            extra_packet = extrapkt_rulenum['extrapacket']
            self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.0.4", proto=%s)/Raw("x" * 20)' % (self.pf_mac, extra_packet[0]['proto']))
            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
            rule_num = extrapkt_rulenum['rulenum']
            self.verify_rulenum(rule_num)

        # ixgbe
        else:
            self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            if (self.nic in ["sagepond", "sageville"]):
                # create the flow rules
                basic_flow_actions = [
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['drop']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['drop']},
                ]
                extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
                extra_packet = extrapkt_rulenum['extrapacket']
                self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s")/SCTP(sport=%s,dport=%s)/Raw("x" * 20)'% (
                    self.pf_mac, extra_packet[2]['sip'], extra_packet[2]['dip'], extra_packet[2]['dport'],
                    extra_packet[2]['sport']))
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                rule_num = extrapkt_rulenum['rulenum']
                self.verify_rulenum(rule_num)
            else:
                basic_flow_actions = [
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                    {'create': 'validate', 'flows': ['ipv4', 'sip', 'dip', 'sctp'], 'actions': ['drop']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                    {'create': 'create', 'flows': ['ipv4', 'sip', 'dip', 'sctp'], 'actions': ['drop']},
                ]
                extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
                extra_packet = extrapkt_rulenum['extrapacket']
                self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s")/SCTP()/Raw("x" * 20)' % (self.pf_mac, extra_packet[2]['dip'], extra_packet[2]['sip']))
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                rule_num = extrapkt_rulenum['rulenum']
                self.verify_rulenum(rule_num)

    def test_fdir_for_ipv6(self):
        """
        only supported by i40e and ixgbe
        """
        self.verify(self.nic in ["niantic", "twinville", "sagepond", "sageville","columbiaville_25g","columbiaville_100g",
                                 "fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville"],
                    "%s nic not support fdir ipv6 filter" % self.nic)
        # i40e
        if (self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "carlsville"]):
            self.setup_env()
            self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024 --legacy-mem" % self.pf_pci)
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)
            self.session_secondary.send_expect("%s -c 0x1e0000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf1 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[0].pci), "testpmd>", 120)
            self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
            self.session_secondary.send_expect("set verbose 1", "testpmd>")
            self.session_secondary.send_expect("start", "testpmd>")
            time.sleep(2)
            self.session_third.send_expect("%s -c 0x1e000000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf2 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[1].pci), "testpmd>", 120)
            self.session_third.send_expect("set fwd rxonly", "testpmd>")
            self.session_third.send_expect("set verbose 1", "testpmd>")
            self.session_third.send_expect("start", "testpmd>")
            time.sleep(2)

            # create the flow rules
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'proto', 'tc', 'hop'],
                 'actions': ['queue']},
                {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'udp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['queue']},
                {'create': 'validate', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'proto', 'tc', 'hop', 'vf0'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport', 'vf1'],
                 'actions': ['queue']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['drop']},
                {'create': 'validate',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport', 'vf1'],
                 'actions': ['drop']},
                {'create': 'create', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'proto', 'tc', 'hop'],
                 'actions': ['queue']},
                {'create': 'create', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'udp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'create', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['queue']},
                {'create': 'create', 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'proto', 'tc', 'hop', 'vf0'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport', 'vf1'],
                 'actions': ['queue']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'sctp', 'sport', 'dport', 'tag'],
                 'actions': ['drop']},
                {'create': 'create',
                 'flows': ['vlan', 'ipv6', 'sip', 'dip', 'tc', 'hop', 'tcp', 'sport', 'dport', 'vf1'],
                 'actions': ['drop']},
            ]
            extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
            extra_packet = extrapkt_rulenum['extrapacket']
            self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=%s)/IPv6(src="2001::1", dst="2001::2", tc=2, hlim=20)/UDP(sport=22,dport=23)/Raw("x" * 20)' % (self.pf_mac, extra_packet[1]['vlan']))
            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
            rule_num = extrapkt_rulenum['rulenum']
            self.verify_rulenum(rule_num)

        # ixgbe signature
        else:
            self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=signature --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)
            if (self.nic in ["niantic", "twinville"]):
                # create the flow rules
                basic_flow_actions = [
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip'], 'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip'], 'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip'], 'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip'], 'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'sctp'], 'actions': ['queue']},
                ]
                extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
                self.dut.send_expect(
                    "flow validate 0 ingress pattern fuzzy thresh spec 2 thresh last 5 thresh mask 0xffffffff / ipv6 src is 2001::1 dst is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / end",
                    "validated")
                self.dut.send_expect(
                    "flow create 0 ingress pattern fuzzy thresh spec 2 thresh last 5 thresh mask 0xffffffff / ipv6 src is 2001::1 dst is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / end",
                    "created")
                extra_packet = extrapkt_rulenum['extrapacket']
                self.sendpkt('Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2",nh=132)/SCTP()/Raw("x" * 20)' % self.pf_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP()/Raw("x" * 20)' % self.pf_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                self.sendpkt('Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/UDP(sport=22,dport=23)/Raw("x" * 20)' % self.pf_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)
                rule_num = extrapkt_rulenum['rulenum']
                self.verify_rulenum(rule_num + 1)
            elif (self.nic in ["sagepond", "sageville"]):
                # create the flow rules
                basic_flow_actions = [
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'validate', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'udp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'tcp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv6', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                    {'create': 'create', 'flows': ['fuzzy', 'ipv4', 'sip', 'dip', 'sctp', 'sport', 'dport'],
                     'actions': ['queue']},
                ]
                extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
                self.dut.send_expect(
                    "flow validate 0 ingress pattern fuzzy thresh spec 2 thresh last 5 thresh mask 0xffffffff / ipv6 src is 2001::1 dst is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / end",
                    "validated")
                self.dut.send_expect(
                    "flow create 0 ingress pattern fuzzy thresh spec 2 thresh last 5 thresh mask 0xffffffff / ipv6 src is 2001::1 dst is 2001::2 / udp src is 22 dst is 23 / end actions queue index 1 / end",
                    "created")
                extra_packet = extrapkt_rulenum['extrapacket']
                self.sendpkt('Ether(dst="%s")/IPv6(src="%s", dst="%s", nh=132)/SCTP(sport=32,dport=33,tag=1)/Raw("x" * 20)' % (self.pf_mac, extra_packet[3]['sip'], extra_packet[3]['dip']))
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                self.sendpkt('Ether(dst="%s")/IP(src="%s", dst="%s", proto=132)/SCTP(sport=32,dport=33)/Raw("x" * 20)' % (self.pf_mac, extra_packet[4]['dip'], extra_packet[4]['sip']))
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
                self.sendpkt('Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/UDP(sport=22,dport=23)/Raw("x" * 20)' % self.pf_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)
                rule_num = extrapkt_rulenum['rulenum']
                self.verify_rulenum(rule_num + 1)

    def test_fdir_for_flexbytes(self):
        """
        The filter structure is different between igb, ixgbe and i40e
        """
        self.verify(self.nic in ["niantic", "twinville", "sagepond", "sageville",
                                 "fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville","columbiaville_25g","columbiaville_100g"],
                    "%s nic not support fdir flexbytes filter" % self.nic)
        # i40e
        if (self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit", "carlsville",
                         "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T","columbiaville_25g","columbiaville_100g"]):
            self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf" % self.pf_pci)
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            # creat the flow rules
            # l2-payload exceeds the  max length of raw match is 16bytes
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnopq / end actions queue index 1 / end",
                "error")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnopq / end actions queue index 1 / end",
                "Exceeds maximal payload limit")
            # l2-payload equal the max length of raw match is 16bytes
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnop / end actions queue index 1 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnop / end actions queue index 1 / end",
                "created")
            # ipv4-other the most 3 fields can be matched, and the max sum bytes of the three fields is 16 bytes.
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / vlan tci is 4095 / ipv4 proto is 255 ttl is 40 / raw relative is 1 offset is 2 pattern is ab / raw relative is 1 offset is 10 pattern is abcdefghij / raw relative is 1 offset is 0 pattern is abcd / end actions queue index 2 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth / vlan tci is 4095 / ipv4 proto is 255 ttl is 40 / raw relative is 1 offset is 2 pattern is ab / raw relative is 1 offset is 10 pattern is abcdefghij / raw relative is 1 offset is 0 pattern is abcd / end actions queue index 2 / end",
                "created")
            # ipv4-udp
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / udp src is 22 dst is 23 / raw relative is 1 offset is 2 pattern is fhds / end actions queue index 3 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / udp src is 22 dst is 23 / raw relative is 1 offset is 2 pattern is fhds / end actions queue index 3 / end",
                "created")
            # ipv4-tcp
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 tos is 4 ttl is 3 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern is hijk / end actions queue index 4 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 tos is 4 ttl is 3 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern is hijk / end actions queue index 4 / end",
                "created")
            # ipv4-sctp
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcd / end actions queue index 5 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcd / end actions queue index 5 / end",
                "created")

            # flush all the rules, then re-create the rules, fix DPDK-23826
            self.dut.send_expect(
                "flow flush 0", "testpmd> ")
            # l2-payload equal the max length of raw match is 16bytes
            self.dut.send_expect(
                "flow create 0 ingress pattern eth type is 0x0807 / raw relative is 1 pattern is abcdefghijklmnop / end actions queue index 1 / end",
                "created")
            # ipv4-other the most 3 fields can be matched, and the max sum bytes of the three fields is 16 bytes.
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / vlan tci is 4095 / ipv4 proto is 255 ttl is 40 / raw relative is 1 offset is 2 pattern is ab / raw relative is 1 offset is 10 pattern is abcdefghij / raw relative is 1 offset is 0 pattern is abcd / end actions queue index 2 / end",
                "created")
            # ipv4-udp
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / udp src is 22 dst is 23 / raw relative is 1 offset is 2 pattern is fhds / end actions queue index 3 / end",
                "created")
            # ipv4-tcp
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 tos is 4 ttl is 3 / tcp src is 32 dst is 33 / raw relative is 1 offset is 2 pattern is hijk / end actions queue index 4 / end",
                "created")
            # ipv4-sctp
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 2.2.2.4 dst is 2.2.2.5 / sctp src is 42 / raw relative is 1 offset is 2 pattern is abcd / end actions queue index 5 / end",
                "created")

            # send the packets and verify the results
            self.sendpkt('Ether(dst="%s", type=0x0807)/Raw(load="abcdefghijklmnop")' % self.pf_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)

            self.sendpkt('Ether(dst="%s")/Dot1Q(vlan=4095)/IP(src="192.168.0.1", dst="192.168.0.2", proto=255, ttl=40)/Raw(load="xxabxxxxxxxxxxabcdefghijabcdefg")' % self.pf_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.pf_mac)

            self.sendpkt('Ether(dst="%s")/IP(src="2.2.2.4", dst="2.2.2.5")/UDP(sport=22,dport=23)/Raw(load="fhfhdsdsfwef")' % self.pf_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="3", verify_mac=self.pf_mac)

            self.sendpkt(
                'Ether(dst="%s")/IP(src="2.2.2.4", dst="2.2.2.5", tos=4, ttl=3)/TCP(sport=32,dport=33)/Raw(load="fhhijk")' % self.pf_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="4", verify_mac=self.pf_mac)
            self.sendpkt(
                'Ether(dst="%s")/IP(src="2.2.2.4", dst="2.2.2.5")/SCTP(sport=42,dport=43,tag=1)/Raw(load="xxabcdefghijklmnopqrst")' % self.pf_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="5", verify_mac=self.pf_mac)
            self.sendpkt(
                'Ether(dst="%s")/IP(src="2.2.2.4", dst="2.2.2.5")/SCTP(sport=42,dport=43,tag=1)/Raw(load="xxabxxxabcddxxabcdefghijklmn")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

            self.verify_rulenum(5)

            self.dut.send_expect("quit", "# ")
            time.sleep(2)

            self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024" % self.pf_pci)
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            # ipv6-tcp
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / raw relative is 1 offset is 0 pattern is hijk / raw relative is 1 offset is 8 pattern is abcdefgh / end actions queue index 6 / end",
                "validated")

            self.dut.send_expect(
                "flow create 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / raw relative is 1 offset is 0 pattern is hijk / raw relative is 1 offset is 8 pattern is abcdefgh / end actions queue index 6 / end",
                "created")

            # send the packet and verify the result
            self.sendpkt(
                'Ether(dst="%s")/Dot1Q(vlan=1)/IPv6(src="2001::1", dst="2001::2", tc=3, hlim=30)/TCP(sport=32,dport=33)/Raw(load="hijkabcdefghabcdefghijklmn")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="6", verify_mac=self.outer_mac)

            # destroy the rule, then re-create the rule, fix DPDK-23826
            self.dut.send_expect(
                "flow destroy 0 rule 0", "testpmd> ")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / vlan tci is 1 / ipv6 src is 2001::1 dst is 2001::2 tc is 3 hop is 30 / tcp src is 32 dst is 33 / raw relative is 1 offset is 0 pattern is hijk / raw relative is 1 offset is 8 pattern is abcdefgh / end actions queue index 6 / end",
                "created")
            self.sendpkt(
                'Ether(dst="%s")/Dot1Q(vlan=1)/IPv6(src="2001::1", dst="2001::2", tc=3, hlim=30)/TCP(sport=32,dport=33)/Raw(load="hijkabcdefghabcdefghijklmn")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="6", verify_mac=self.outer_mac)

        # ixgbe
        else:
            self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            # ipv4-udp-flexbytes
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 44 limit is 0 pattern is 86 / end actions queue index 1 / end",
                "validated")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / udp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 44 limit is 0 pattern is 86 / end actions queue index 1 / end",
                "created")

            # send the packet and verify the result
            self.sendpkt(
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/UDP(sport=24,dport=25)/Raw(load="xx86ddef")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.outer_mac)

            self.dut.send_expect("quit", "# ")
            time.sleep(2)

            # the second flexbytes rule should be created after the testpmd reset, because the flexbytes rule is global bit masks
            self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            # ipv4-tcp-flexbytes spec-mask
            self.dut.send_expect(
                "flow validate 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / tcp src is 22 dst is 23 / raw relative spec 0 relative mask 1 search spec 0 search mask 1 offset spec 54 offset mask 0xffffffff limit spec 0 limit mask 0xffff pattern is ab pattern is cd / end actions queue index 2 / end",
                "validated")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / tcp src is 22 dst is 23 / raw relative spec 0 relative mask 1 search spec 0 search mask 1 offset spec 54 offset mask 0xffffffff limit spec 0 limit mask 0xffff pattern is ab pattern is cd / end actions queue index 2 / end",
                "created")
            # destroy the rule, then re-create the rule, fix DPDK-23826
            self.dut.send_expect(
                "flow destroy 0 rule 0", "testpmd> ")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.3 dst is 192.168.0.4 / tcp src is 22 dst is 23 / raw relative spec 0 relative mask 1 search spec 0 search mask 1 offset spec 54 offset mask 0xffffffff limit spec 0 limit mask 0xffff pattern is ab pattern is cd / end actions queue index 2 / end",
                "created")

            # send the packet and verify the result
            self.sendpkt(
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.0.4")/TCP(sport=22,dport=23)/Raw(load="abcdxxx")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)
            self.sendpkt(
                'Ether(dst="%s")/IP(src="192.168.0.3", dst="192.168.0.4")/TCP(sport=22,dport=23)/Raw(load="cdcdxxx")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.outer_mac)

            self.dut.send_expect("quit", "# ")
            time.sleep(2)

            # signature mode
            self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=signature --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
            self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
            self.dut.send_expect("set verbose 1", "testpmd> ", 120)
            self.dut.send_expect("start", "testpmd> ", 120)
            time.sleep(2)

            # ipv4-sctp-flexbytes
            if (self.nic in ["sagepond", "sageville"]):
                self.dut.send_expect(
                    "flow validate 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 3 / end",
                    "validated")
                self.dut.send_expect(
                    "flow create 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp src is 24 dst is 25 / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 3 / end",
                    "created")
            else:
                self.dut.send_expect(
                    "flow validate 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 3 / end",
                    "validated")
                self.dut.send_expect(
                    "flow create 0 ingress pattern fuzzy thresh is 6 / eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / sctp / raw relative is 0 search is 0 offset is 48 limit is 0 pattern is ab / end actions queue index 3 / end",
                    "created")

            # send the packet and verify the result
            self.sendpkt(
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=24,dport=25)/Raw(load="xxabcdef")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="3", verify_mac=self.outer_mac)
            self.sendpkt(
                'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/SCTP(sport=24,dport=25)/Raw(load="xxaccdef")' % self.outer_mac)
            self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

            # ipv6-other-flexbytes
            if (self.nic in ["niantic", "twinville"]):
                self.dut.send_expect("quit", "# ")
                time.sleep(2)

                self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=signature --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
                self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
                self.dut.send_expect("set verbose 1", "testpmd> ", 120)
                self.dut.send_expect("start", "testpmd> ", 120)
                time.sleep(2)

                self.dut.send_expect(
                    "flow validate 0 ingress pattern fuzzy thresh is 6 / ipv6 src is 2001::1 dst is 2001::2 / raw relative is 0 search is 0 offset is 56 limit is 0 pattern is 86 / end actions queue index 4 / end",
                    "validated")
                self.dut.send_expect(
                    "flow create 0 ingress pattern fuzzy thresh is 6 / ipv6 src is 2001::1 dst is 2001::2 / raw relative is 0 search is 0 offset is 56 limit is 0 pattern is 86 / end actions queue index 4 / end",
                    "created")
                self.sendpkt(
                    'Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xx86abcd")' % self.outer_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="4", verify_mac=self.outer_mac)
                self.sendpkt(
                    'Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xxx86abcd")' % self.outer_mac)
                self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

    def test_flexbytes_filter(self):
        """
        The filter structure is different between igb, ixgbe and i40e
        """
        self.verify(self.nic in ["bartonhills", "powerville", "foxville"], "%s nic not support flexbytes filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # create the flow rules
        # l2_payload
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 14 pattern is fhds / end actions queue index 1 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 14 pattern is fhds / end actions queue index 1 / end",
            "created")
        # ipv4 packet
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 34 pattern is ab / end actions queue index 2 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 34 pattern is ab / end actions queue index 2 / end",
            "created")
        # ipv6 packet
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 58 pattern is efgh / end actions queue index 3 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 58 pattern is efgh / end actions queue index 3 / end",
            "created")
        # 3 fields relative is 0
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 38 pattern is ab / raw relative is 0 offset is 34 pattern is cd / raw relative is 0 offset is 42 pattern is efgh / end actions queue index 4 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 38 pattern is ab / raw relative is 0 offset is 34 pattern is cd / raw relative is 0 offset is 42 pattern is efgh / end actions queue index 4 / end",
            "created")
        # 4 fields relative is 0 and 1
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 48 pattern is ab / raw relative is 1 offset is 0 pattern is cd / raw relative is 0 offset is 44 pattern is efgh / raw relative is 1 offset is 10 pattern is hijklmnopq / end actions queue index 5 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 48 pattern is ab / raw relative is 1 offset is 0 pattern is cd / raw relative is 0 offset is 44 pattern is efgh / raw relative is 1 offset is 10 pattern is hijklmnopq / end actions queue index 5 / end",
            "created")
        # 3 fields offset confilict
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 64 pattern is ab / raw relative is 1 offset is 4 pattern is cdefgh / raw relative is 0 offset is 68 pattern is klmn / end actions queue index 6 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 64 pattern is ab / raw relative is 1 offset is 4 pattern is cdefgh / raw relative is 0 offset is 68 pattern is klmn / end actions queue index 6 / end",
            "created")

        # send the packet and verify the result
        self.sendpkt('Ether(dst="%s")/Raw(load="fhdsab")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/Raw(load="afhdsb")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="abcdef")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/Raw(load="xxxxefgh")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="3", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IPv6(src="2001::1", dst="2001::2")/TCP(sport=32,dport=33)/Raw(load="abcdefgh")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw(load="cdxxabxxefghxxxx")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="4", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2", tos=4, ttl=3)/UDP(sport=32,dport=33)/Raw(load="xxefghabcdxxxxxxhijklmnopqxxxx")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="5", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxabxxklmnefgh")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="6", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxabxxklcdefgh")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.dut.send_expect("flow flush 0", "testpmd> ", 120)

        # 1 field 128bytes
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 128 pattern is ab / end actions queue index 1 / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 128 pattern is ab / end actions queue index 1 / end",
            "Failed to create flow")
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 126 pattern is abcd / end actions queue index 1 / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 126 pattern is abcd / end actions queue index 1 / end",
            "Failed to create flow")
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 126 pattern is ab / end actions queue index 1 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 126 pattern is ab / end actions queue index 1 / end",
            "created")
        # 2 field 128bytes
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 58 pattern is cd / end actions queue index 2 / end",
            "error")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 58 pattern is cd / end actions queue index 2 / end",
            "Failed to create flow")
        self.dut.send_expect(
            "flow validate 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 56 pattern is cd / end actions queue index 2 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern raw relative is 0 offset is 68 pattern is ab / raw relative is 1 offset is 56 pattern is cd / end actions queue index 2 / end",
            "created")

        # send the packet and verify the result
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxab")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxcb")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxabxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxcd")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.outer_mac)
        self.sendpkt('Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(sport=22,dport=23)/Raw(load="xxxxxxxxxxxxxxabxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxce")' % self.outer_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.verify_rulenum(2)

    def test_fdir_for_mac_vlan(self):
        """
        only supported by ixgbe
        """
        self.verify(self.nic in ["twinville", "sagepond", "sageville", "foxville", "fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g"], "%s nic not support fdir mac vlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect-mac-vlan --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("vlan set strip off 0", "testpmd> ", 120)
        self.dut.send_expect("vlan set filter off 0", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # create the flow rules
        if self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g"]:
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['vlan'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['vlan'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['vlan'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['vlan'], 'actions': ['queue']}
            ]
        else:
            basic_flow_actions = [
                {'create': 'validate', 'flows': ['dst_mac', 'vlan'], 'actions': ['queue']},
                {'create': 'validate', 'flows': ['dst_mac', 'vlan'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['dst_mac', 'vlan'], 'actions': ['queue']},
                {'create': 'create', 'flows': ['dst_mac', 'vlan'], 'actions': ['queue']},
            ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_fdir_for_vxlan(self):
        """
        only supported by ixgbe
        """
        self.verify(self.nic in ["twinville", "sagepond", "sageville","columbiaville_25g","columbiaville_100g", "foxville"], "%s nic not support fdir vxlan filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect-tunnel --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # create the flow rules
        basic_flow_actions = [
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'], 'actions': ['drop']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'], 'actions': ['drop']},
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_fdir_for_nvgre(self):
        """
        only supported by ixgbe
        """
        self.verify(self.nic in ["twinville", "sagepond", "sageville", "foxville"], "%s nic not support fdir nvgre filter" % self.nic)

        self.pmdout.start_testpmd("%s" % self.cores, "--pkt-filter-mode=perfect-tunnel --disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        # create the flow rules
        basic_flow_actions = [
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['drop']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['queue']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['drop']},
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_tunnel_filter_vxlan(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville", "carlsville"],
                    "%s nic not support tunnel vxlan filter" % self.nic)

        self.setup_env()
        self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024 --legacy-mem" % self.pf_pci)
        self.dut.send_expect("rx_vxlan_port add 4789 0", "testpmd> ", 120)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        self.session_secondary.send_expect("%s -c 0x1e0000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf1 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[0].pci), "testpmd>", 120)
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set verbose 1", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        self.session_third.send_expect("%s -c 0x1e000000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf2 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[1].pci), "testpmd>", 120)
        self.session_third.send_expect("set fwd rxonly", "testpmd>")
        self.session_third.send_expect("set verbose 1", "testpmd>")
        self.session_third.send_expect("start", "testpmd>")
        time.sleep(2)

        # create the flow rules
        basic_flow_actions = [
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'],
             'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['dst_mac', 'ipv4', 'udp', 'vxlan', 'vni', 'ineth'],
             'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'],
             'actions': ['vf0', 'queue']},
            {'create': 'create', 'flows': ['dst_mac', 'ipv4', 'udp', 'vxlan', 'vni', 'ineth'],
             'actions': ['vf1', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'],
             'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['dst_mac', 'ipv4', 'udp', 'vxlan', 'vni', 'ineth'],
             'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'udp', 'vxlan', 'vni', 'ineth', 'invlan'],
             'actions': ['vf0', 'queue']},
            {'create': 'validate', 'flows': ['dst_mac', 'ipv4', 'udp', 'vxlan', 'vni', 'ineth'],
             'actions': ['vf1', 'queue']}
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        extra_packet = extrapkt_rulenum['extrapacket']

        self.sendpkt('Ether(dst="%s")/IP()/UDP()/VXLAN()/Ether(dst="%s")/Dot1Q(vlan=11)/IP()/TCP()/Raw("x" * 20)' % (self.outer_mac, self.inner_mac))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][0],
                           verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/UDP()/VXLAN(vni=5)/Ether(dst="%s")/IP()/TCP()/Raw("x" * 20)' % (self.outer_mac, self.wrong_mac))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/UDP()/VXLAN(vni=%s)/Ether(dst="%s")/Dot1Q(vlan=%s)/IP()/TCP()/Raw("x" * 20)' % (
        self.outer_mac, extra_packet[5]['vni'], self.wrong_mac, extra_packet[5]['invlan']))
        self.verify_result("vf0", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/UDP()/VXLAN(vni=%s)/Ether(dst="%s")/IP()/TCP()/Raw("x" * 20)' % (
        self.wrong_mac, extra_packet[6]['vni'], self.inner_mac))
        self.verify_result("vf1", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.wrong_mac)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_tunnel_filter_nvgre(self):
        """
        only supported by i40e
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_25g", "fortville_spirit","columbiaville_25g","columbiaville_100g",
                                 "fortville_spirit_single", "fortpark_TLV","fortpark_BASE-T", "foxville",  "carlsville"],
                    "%s nic not support tunnel nvgre filter" % self.nic)

        self.setup_env()
        self.pmdout.start_testpmd("%s" % self.pf_cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1), "-a %s --file-prefix=pf --socket-mem 1024,1024  --legacy-mem" % self.pf_pci)
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)
        self.session_secondary.send_expect("%s -c 0x1e0000 -n 4 --socket-mem 1024,1024  --legacy-mem -a %s --file-prefix=vf1 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[0].pci), "testpmd>", 120)
        self.session_secondary.send_expect("set fwd rxonly", "testpmd>")
        self.session_secondary.send_expect("set verbose 1", "testpmd>")
        self.session_secondary.send_expect("start", "testpmd>")
        time.sleep(2)
        self.session_third.send_expect("%s -c 0x1e000000 -n 4 --socket-mem 1024,1024 --legacy-mem -a %s --file-prefix=vf2 -- -i --rxq=4 --txq=4 --disable-rss" % (self.app_path, self.sriov_vfs_port[1].pci), "testpmd>", 120)
        self.session_third.send_expect("set fwd rxonly", "testpmd>")
        self.session_third.send_expect("set verbose 1", "testpmd>")
        self.session_third.send_expect("start", "testpmd>")
        time.sleep(2)

        # create the flow rules
        basic_flow_actions = [
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['dst_mac', 'ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'create', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['vf0', 'queue']},
            {'create': 'create', 'flows': ['dst_mac', 'ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['vf1', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['dst_mac', 'ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['pf', 'queue']},
            {'create': 'validate', 'flows': ['ipv4', 'nvgre', 'tni', 'ineth', 'invlan'], 'actions': ['vf0', 'queue']},
            {'create': 'validate', 'flows': ['dst_mac', 'ipv4', 'nvgre', 'tni', 'ineth'], 'actions': ['vf1', 'queue']}
        ]
        extrapkt_rulenum = self.all_flows_process(basic_flow_actions)
        extra_packet = extrapkt_rulenum['extrapacket']

        self.sendpkt('Ether(dst="%s")/IP()/NVGRE()/Ether(dst="%s")/Dot1Q(vlan=1)/IP()/TCP()/Raw("x" * 20)' % (self.outer_mac, self.inner_mac))
        self.verify_result("pf", expect_rxpkts="1", expect_queue=extrapkt_rulenum['queue'][0],
                           verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/NVGRE(TNI=%s)/Ether(dst="%s")/IP()/TCP()/Raw("x" * 20)' % (
        self.outer_mac, extra_packet[4]['tni'], self.wrong_mac))
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/NVGRE(TNI=%s)/Ether(dst="%s")/Dot1Q(vlan=%s)/IP()/TCP()/Raw("x" * 20)' % (
        self.outer_mac, extra_packet[5]['tni'], self.wrong_mac, extra_packet[5]['invlan']))
        self.verify_result("vf0", expect_rxpkts="1", expect_queue="0", verify_mac=self.outer_mac)

        self.sendpkt('Ether(dst="%s")/IP()/NVGRE(TNI=%s)/Ether(dst="%s")/IP()/TCP()/Raw("x" * 20)' % (
        self.wrong_mac, extra_packet[6]['tni'], self.inner_mac))
        self.verify_result("vf1", expect_rxpkts="0", expect_queue="NULL", verify_mac=self.wrong_mac)
        rule_num = extrapkt_rulenum['rulenum']
        self.verify_rulenum(rule_num)

    def test_create_same_rule_after_destroy(self):

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 20)
        self.dut.send_expect("set verbose 1", "testpmd> ", 20)
        self.dut.send_expect("start", "testpmd> ", 20)
        time.sleep(2)

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end", "created")

        out = self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        p = re.compile(r"Flow rule #(\d+) destroyed")
        m = p.search(out)
        self.verify(m, "flow rule 0 delete failed" )

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end", "created")

        self.sendpkt(pktstr='Ether(dst="%s")/IP()/UDP(sport=32)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.pf_mac)
        self.sendpkt(pktstr='Ether(dst="%s")/IP()/UDP(dport=32)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)

    def test_create_different_rule_after_destroy(self):

        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 20)
        self.dut.send_expect("set verbose 1", "testpmd> ", 20)
        self.dut.send_expect("start", "testpmd> ", 20)
        time.sleep(2)

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp src is 32 / end actions queue index 2 / end", "created")

        out = self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        p = re.compile(r"Flow rule #(\d+) destroyed")
        m = p.search(out)
        self.verify(m, "flow rule 0 delete failed" )

        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / udp dst is 32 / end actions queue index 2 / end", "created")

        self.sendpkt(pktstr='Ether(dst="%s")/IP()/UDP(sport=32)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.sendpkt(pktstr='Ether(dst="%s")/IP()/UDP(dport=32)/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.pf_mac)

    def test_dual_vlan(self):
        """
        Test with flow type dual vlan(QinQ).
        """
        self.verify(self.nic in ["fortville_eagle", "fortville_spirit", "fortville_spirit_single", "fortville_25g",
                                 "carlsville", "fortpark_BASE-T", "fortpark_TLV"], "NIC Unsupported: " + str(self.nic))
        for queue in testQueues:
            self.pmdout.start_testpmd(
                "Default", "  --portmask=0x1 --rxq=%d --txq=%d" % (queue, queue))

            self.dut.send_expect("set verbose 8", "testpmd> ")
            self.dut.send_expect("set fwd rxonly", "testpmd> ")

            self.dut.send_expect("port stop all", "testpmd> ")
            self.dut.send_expect("vlan set extend on 0", "testpmd> ")
            self.dut.send_expect(
                "flow create 0 ingress pattern eth / end actions rss types l2-payload end queues end func toeplitz / end", "testpmd> ")
            self.dut.send_expect("port start all", "testpmd> ")
            res = self.pmdout.wait_link_status_up("all")
            self.verify(res is True, "link is down")

            self.send_packet(self.tester_itf, "l2_payload")

            # set flow rss type s-vlan c-vlan set by testpmd on dut
            self.dut.send_expect("flow create 0 ingress pattern eth / end actions rss types s-vlan c-vlan end key_len 0 queues end / end", "testpmd> ")
            self.send_packet(self.tester_itf, "l2_payload")

            self.send_packet(self.tester_itf, "l2_payload", enable="ovlan")

            self.send_packet(self.tester_itf, "l2_payload", enable="ivlan")

            self.dut.send_expect("quit", "# ", 30)

        self.result_table_print()
        result_rows = self.result_table_getrows()
        self.verify(len(result_rows) > 1, "There is no data in the table, testcase failed!")

        # check the results
        self.verify(result_rows[1][1] != result_rows[2][1], "The hash values should be different when setting rss to 'l2-payload' and 's-vlan c-vlan and sending the same packets.")
        self.verify(result_rows[1][1] != result_rows[3][1], "The hash values should be different when setting rss to 'l2-payload' and 's-vlan c-vlan' and sending packets with different ovlan.")
        self.verify(result_rows[1][1] != result_rows[4][1], "The hash values should be different when setting rss to 'l2-payload' and 's-vlan c-vlan' and sending packets with different ivlan.")
        self.verify(result_rows[2][1] != result_rows[3][1], "The hash values should be different when setting rss to 's-vlan c-vlan' and sending packet with different ovlan.")
        self.verify(result_rows[2][1] != result_rows[4][1], "The hash values should be different when setting rss to 's-vlan c-vlan' and sending packet with different ivlan.")
        self.verify(result_rows[3][1] != result_rows[4][1], "The hash values should be different when setting rss to 's-vlan c-vlan' and sending packet with different ovlan and ivlan")

    def test_multiple_filters_10GB(self):
        """
        only supported by ixgbe and igb
        """
        self.verify(self.nic in ["niantic", "kawela_4", "kawela",
                        "twinville", "foxville"], "%s nic not support n-tuple filter" % self.nic)
        self.pmdout.start_testpmd("%s" % self.cores, "--disable-rss --rxq=%d --txq=%d" % (MAX_QUEUE+1, MAX_QUEUE+1))
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        self.dut.send_expect(
            "flow validate 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 1 / end", "validated")
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth type is 0x0806  / end actions queue index 2 /  end", "validated")
        self.dut.send_expect(
            "flow validate 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 proto is 17 / udp dst is 1 src is 1  / end actions queue index 3 /  end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 1 / end", "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth type is 0x0806  / end actions queue index 2 /  end", "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 dst is 2.2.2.5 src is 2.2.2.4 proto is 17 / udp dst is 1 src is 1  / end actions queue index 3 /  end", "create")
        time.sleep(2)
        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)

        self.sendpkt(pktstr='Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")/Raw("x" * 20)')
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac="ff:ff:ff:ff:ff:ff")

        self.sendpkt(pktstr='Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/UDP(sport=1,dport=1)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="3", verify_mac=self.pf_mac)
        # destroy rule 2
        out = self.dut.send_expect("flow destroy 0 rule 2", "testpmd> ")
        p = re.compile(r"Flow rule #(\d+) destroyed")
        m = p.search(out)
        self.verify(m, "flow rule 2 delete failed" )
        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)

        self.sendpkt(pktstr='Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")/Raw("x" * 20)')
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac="ff:ff:ff:ff:ff:ff")

        self.sendpkt(pktstr='Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/UDP(sport=1,dport=1)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        # destroy rule 1
        out = self.dut.send_expect("flow destroy 0 rule 1", "testpmd> ")
        p = re.compile(r"Flow rule #(\d+) destroyed")
        m = p.search(out)
        self.verify(m, "flow rule 1 delete failed" )

        self.sendpkt(pktstr='Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")/Raw("x" * 20)')
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac="ff:ff:ff:ff:ff:ff")

        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac)
        # destroy rule 0
        out = self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        p = re.compile(r"Flow rule #(\d+) destroyed")
        m = p.search(out)
        self.verify(m, "flow rule 0 delete failed" )

        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(dport=80,flags="S")/Raw("x" * 20)' % self.pf_mac)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.dut.send_expect("stop", "testpmd> ")

    def test_jumbo_frame_size(self):

        self.verify(self.nic in ["niantic", "kawela_4", "kawela", "bartonhills", "twinville", "sagepond", "sageville",
                                 "powerville", "foxville"], "%s nic not support" % self.nic)
        if (self.nic in ["cavium_a063", "cavium_a064", "foxville"]):
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1 --mbcache=200 --mbuf-size=2048 --max-pkt-len=9200" % portMask)
        else:
            self.pmdout.start_testpmd(
                "%s" % self.cores, "--disable-rss --rxq=4 --txq=4 --portmask=%s --nb-cores=4 --nb-ports=1 --mbcache=200 --mbuf-size=2048 --max-pkt-len=9600" % portMask)
        port = self.tester.get_local_port(valports[0])
        txItf = self.tester.get_interface(port)

        port = self.tester.get_local_port(valports[1])
        rxItf = self.tester.get_interface(port)
        self.tester.send_expect("ifconfig %s mtu %s" % (txItf, 9200), "# ")
        self.tester.send_expect("ifconfig %s mtu %s" % (rxItf, 9200), "# ")
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 120)
        self.dut.send_expect("set verbose 1", "testpmd> ", 120)
        self.dut.send_expect("start", "testpmd> ", 120)
        time.sleep(2)

        self.dut.send_expect(
            "flow validate 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 2 / end",
            "validated")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv4 / tcp flags spec 0x02 flags mask 0x02 / end actions queue index 2 / end",
            "created")

        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="2.2.2.5",dst="2.2.2.4")/TCP(dport=80,flags="S")/Raw(load="\x50"*8962)' % self.pf_mac)
        time.sleep(1)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.pf_mac)

        self.sendpkt(pktstr='Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst="192.168.1.1")')
        time.sleep(1)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac="ff:ff:ff:ff:ff:ff")
        # destroy rule
        self.dut.send_expect("flow destroy 0 rule 0", "testpmd> ")
        self.sendpkt(pktstr='Ether(dst="%s")/IP(src="2.2.2.5",dst="2.2.2.4")/TCP(dport=80,flags="S")/Raw(load="\x50"*8962)' % self.pf_mac)
        time.sleep(1)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac)
        self.dut.send_expect("stop", "testpmd> ")

        self.tester.send_expect("ifconfig %s mtu %s" % (txItf, 1500), "# ")
        self.tester.send_expect("ifconfig %s mtu %s" % (rxItf, 1500), "# ")

    def test_64_queues(self):

        set_filter_flag = 1
        packet_flag = 1
        if self.kdriver == "ixgbe":
            global valports
            total_mbufs = self.request_mbufs(64) * len(valports)
            self.pmdout.start_testpmd(
                "all", "--disable-rss --rxq=64 --txq=64 --portmask=%s --nb-cores=4 --total-num-mbufs=%d" % (portMask, total_mbufs))
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "set stat_qmap rx %s 0 0" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set strip off %s" % valports[1], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[0], "testpmd> ")
            self.dut.send_expect(
                "vlan set filter off %s" % valports[1], "testpmd> ")
            queue = ['16', '32', '64']
            for i in [0, 1, 2]:
                if i == 2:
                    out = self.dut.send_expect(
                        "set stat_qmap rx %s %s %s" % (valports[0], queue[i], (i + 1)), "testpmd> ")
                    if 'Invalid RX queue %s' % (queue[i]) not in out:
                        set_filter_flag = 0
                        break
                    cmd = "flow create {} ingress pattern eth / ".format(
                        valports[0]) + "ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is {} src is 1 / ".format(
                        i + 1) + "end actions queue index {} / end".format(queue[i])
                    out = self.dut.send_expect(cmd, "testpmd> ")
                    if 'Invalid argument' not in out:
                        set_filter_flag = 0
                        break
                    continue
                else:
                    self.dut.send_expect("set stat_qmap rx %s %s %s" %
                                         (valports[0], queue[i], (i + 1)), "testpmd> ")
                    cmd = "flow create {} ingress pattern eth / ".format(
                        valports[0]) + "ipv4 dst is 2.2.2.5 src is 2.2.2.4 / tcp dst is {} src is 1 / ".format(
                        i + 1) + "end actions queue index {} / end".format(queue[i])
                    self.dut.send_expect(cmd, "testpmd> ")
                    self.dut.send_expect("start", "testpmd> ", 120)
                global filters_index
                filters_index = i
                if (filters_index == 0):
                    self.sendpkt(pktstr='Ether(dst="%s")/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=1,flags=0)' % self.pf_mac)
                if (filters_index == 1):
                    self.sendpkt(pktstr='Ether(dst="%s")/Dot1Q(prio=3)/IP(src="2.2.2.4",dst="2.2.2.5")/TCP(sport=1,dport=2,flags=0)' % self.pf_mac)
                time.sleep(1)
                out = self.dut.send_expect("stop", "testpmd> ")
                p = re.compile(r"Forward Stats for RX Port= \d+/Queue=(\s?\d+)")
                res = p.findall(out)
                queues = [int(i) for i in res]
                if queues[0] != int(queue[i]):
                    packet_flag = 0
                    break
            self.dut.send_expect("quit", "#", timeout=30)
            self.verify(set_filter_flag == 1, "set filters error")
            self.verify(packet_flag == 1, "packet pass assert error")
        else:
            self.verify(False, "%s not support this test" % self.nic)

    @check_supported_nic(["niantic"])
    def test_fdir_for_match_report(self):
        """
        Test case: IXGBE fdir for Control levels of FDir match reporting
        only supported by ixgbe
        """
        fdir_scanner = re.compile("FDIR matched hash=(0x\w+) ID=(0x\w+)")
        pkt0 = 'Ether(dst="{}")/IP(src="192.168.0.1", dst="192.168.0.2")/Raw("x" * 20)'.format(self.pf_mac)
        pkt1 = 'Ether(dst="{}")/IP(src="192.168.1.1", dst="192.168.1.2")/Raw("x" * 20)'.format(self.pf_mac)
        rule0 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / end actions queue index 1 / mark id 1 / end"
        rule1 = "flow create 0 ingress pattern eth / ipv4 src is 192.168.1.1 dst is 192.168.1.2 / end actions queue index 2 / mark id 2 / end"

        self.logger.info("Sub-case1: ``--pkt-filter-report-hash=none`` mode")
        pkt_filter_report_hash = "none"
        self.launch_start_testpmd(queue=MAX_QUEUE + 1, pkt_filter_mode='perfect', report_hash=pkt_filter_report_hash,
                                  disable_rss=True, fwd='rxonly', verbose='1')

        # Send the matched packet with Scapy on the traffic generator and check that no FDir information is printed
        self.sendpkt(pktstr=pkt0)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac, check_fdir="non-exist")

        # Add flow filter rule, and send the matched packet again.
        # No FDir information is printed, but it can be seen that the packet went to queue 1
        self.pmdout.execute_cmd(rule0)
        self.sendpkt(pktstr=pkt0)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac, check_fdir="non-exist")
        self.pmdout.quit()

        self.logger.info("Sub-case2: ``--pkt-filter-report-hash=match`` mode")
        pkt_filter_report_hash = "match"
        self.launch_start_testpmd(queue=MAX_QUEUE + 1, pkt_filter_mode='perfect', report_hash=pkt_filter_report_hash,
                                  disable_rss=True, fwd='rxonly', verbose='1')

        # Send the matched packet with Scapy on the traffic generator and check that no FDir information is printed
        self.sendpkt(pktstr=pkt0)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac, check_fdir="non-exist")

        # Add flow filter rule, and send the matched packet again.
        # the match is indicated (``RTE_MBUF_F_FDIR``), and its details (hash, id) printed
        self.pmdout.execute_cmd(rule0)
        self.sendpkt(pktstr=pkt0)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac, check_fdir="exist")

        # Add flow filter rule by using different scr,dst, and send the matched pkt1 packet again.
        # the match is indicated (``RTE_MBUF_F_FDIR``), and its details (hash, id) printed
        self.pmdout.execute_cmd(rule1)
        self.sendpkt(pktstr=pkt1)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="2", verify_mac=self.pf_mac, check_fdir="exist")

        # Remove rule1 and send the matched pkt0 packet again. Check that no FDir information is printed
        self.pmdout.execute_cmd('flow destroy 0 rule 0')
        self.sendpkt(pktstr=pkt0)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac, check_fdir="non-exist")

        # Remove rule2, and send the match pkt1 packet again. Check that no FDir information is printed
        self.pmdout.execute_cmd('flow destroy 0 rule 1')
        self.sendpkt(pktstr=pkt1)
        self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac, check_fdir="non-exist")
        self.pmdout.quit()

        self.logger.info("Sub-case3: ``--pkt-filter-report-hash=always`` mode")
        pkt_filter_report_hash = "always"
        self.launch_start_testpmd(queue=MAX_QUEUE + 1, pkt_filter_mode='perfect', report_hash=pkt_filter_report_hash,
                                  disable_rss=True, fwd='rxonly', verbose='1')

        # Send matched pkt0 packet with Scapy on the traffic generator and check the output (FDIR id=0x0)
        self.sendpkt(pktstr=pkt0)
        out1 = self.verify_result("pf", expect_rxpkts="1", expect_queue="0", verify_mac=self.pf_mac, check_fdir="exist")

        # Add flow filter rule, and send the matched pkt0 packet again.
        # the filter ID is different, and the packet goes to queue 1Add flow filter rule, and send the matched packet again.
        self.pmdout.execute_cmd(rule0)
        self.sendpkt(pktstr=pkt0)
        out2 = self.verify_result("pf", expect_rxpkts="1", expect_queue="1", verify_mac=self.pf_mac, check_fdir="exist")

        # check fdir id is different
        self.logger.info("FDIR ID1=" + fdir_scanner.search(out1).group(0) + "; FDIR ID2=" + fdir_scanner.search(out2).group(0))
        self.verify(fdir_scanner.search(out1).group(0) != fdir_scanner.search(out2).group(0),
                    'Sub-case3.3: FDIR ID should be different')

    def tear_down(self):
        """
        Run after each test case.
        """
        self.destroy_env()
        self.dut.kill_all()

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
        self.dut.close_session(self.session_secondary)
        self.dut.close_session(self.session_third)

