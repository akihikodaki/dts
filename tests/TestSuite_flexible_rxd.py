# Copyright (c) <2019> Intel Corporation
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# - Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# - Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in
#   the documentation and/or other materials provided with the
#   distribution.
#
# - Neither the name of Intel Corporation nor the names of its
#   contributors may be used to endorse or promote products derived
#   from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.


import time
from test_case import TestCase
from packet import Packet
from pmd_output import PmdOutput


class TestFlexibleRxd(TestCase):

    def set_up_all(self):
        """
        run at the start of each test suite.
        """
        self.verify(self.nic in ["columbiaville_25g", "columbiaville_100g", "foxville"],
                    "flexible rxd only supports CVL NIC.")
        self.nb_core = 2
        self.pkg_count = 1
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports for testing")
        self.pci_info = self.dut.ports_info[0]['pci']
        self.ports_socket = self.dut.get_numa_id(self.dut_ports[0])
        self.cores = self.dut.get_core_list("1S/3C/1T", socket=self.ports_socket)
        self.verify(len(self.cores) >= 3, "The machine has too few cores.")
        self.tx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        self.dst_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.src_mac = self.tester.get_mac(self.tester.get_local_port(self.dut_ports[0]))
        self.pmdout = PmdOutput(self.dut)
        self.prepare_test_pmd()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def prepare_test_pmd(self):
        """
        Modify the dpdk code.
        """
        self.dut.send_expect("cp ./app/test-pmd/util.c .", "#", 15)
        self.dut.send_expect("cp ./app/test-pmd/meson.build /root/", "#", 15)
        pattern = r"/if dpdk_conf.has('RTE_NET_IXGBE')/i\if dpdk_conf.has('RTE_NET_ICE')\n\tdeps += 'net_ice'\nendif"
        self.dut.send_expect(f'sed -i "{pattern}" app/test-pmd/meson.build', "#", 15)
        self.dut.send_expect(
            "sed -i '/#include <rte_flow.h>/a\#include <rte_pmd_ice.h>' app/test-pmd/util.c", "#", 15)
        self.dut.send_expect(
            "sed -i '/if (ol_flags & PKT_RX_TIMESTAMP)/i\                rte_net_ice_dump_proto_xtr_metadata(mb);' app/test-pmd/util.c", "#", 15)
        self.dut.build_install_dpdk(self.dut.target)

    def restory_test_pmd(self):
        """
         Resume editing operation.
        """
        self.dut.send_expect("\cp ./util.c ./app/test-pmd/", "#", 15)
        self.dut.send_expect("\cp /root/meson.build ./app/test-pmd/", "#", 15)
        self.dut.send_expect("rm -rf  /root/meson.build", "#", 15)
        self.dut.send_expect("rm -rf  ./util.c", "#", 15)
        self.dut.build_install_dpdk(self.dut.target)

    def start_testpmd(self, proto_xdr):
        """
        start testpmd
        """
        num = '4' if self.nic == 'foxville' else '32'
        para = '--rxq=%s --txq=%s --portmask=0x1 --nb-cores=%d' % (num, num, self.nb_core)
        self.pmdout.start_testpmd("1S/3C/1T", param=para, ports=[self.pci_info], port_options={self.pci_info: 'proto_xtr=%s' % proto_xdr})
        self.pmdout.execute_cmd("set verbose 1", "testpmd> ", 120)
        self.pmdout.execute_cmd("set fwd io", "testpmd> ", 120)
        self.pmdout.execute_cmd("set promisc all off", "testpmd> ", 120)
        self.pmdout.execute_cmd("clear port stats all", "testpmd> ", 120)
        self.pmdout.execute_cmd("start", "testpmd> ", 120)

    def verify_result(self, fields_list, out, mesg):
        """
        Validation results
        """
        for field in fields_list:
            self.verify(field in out, mesg)
        self.dut.send_expect("quit", "#", 15)

    def send_pkts_and_get_output(self, pkts_str):
        pkt = Packet(pkts_str)
        pkt.send_pkt(self.tester, tx_port=self.tx_interface, count=self.pkg_count, timeout=30)
        time.sleep(3)
        out_info = self.dut.get_session_output(timeout=3)
        return out_info

    def test_check_single_VLAN_fields_in_RXD_8021Q(self):
        """
        Check single VLAN fields in RXD (802.1Q)
        """
        self.start_testpmd("vlan")
        pkts_str = 'Ether(src="%s", dst="%s", type=0x8100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "The packet does not carry a VLAN tag."
        fields_list = ["vlan"]
        self.verify_result(fields_list, out, mesg)

    def test_check_single_VLAN_fields_in_RXD_8021ad(self):
        """
        Check single VLAN fields in RXD (802.1ad)
        """
        self.start_testpmd("vlan")
        pkts_str = 'Ether(src="%s", dst="%s", type=0x88A8)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "stag result is not expected (stag=1:0:23)"
        fields_list = ["stag=1:0:23"]
        self.verify_result(fields_list, out, mesg)

    def test_check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
        """
        self.start_testpmd("vlan")
        pkts_str = 'Ether(src="%s", dst="%s", type=0x9100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "stag result is not expected (stag=1:0:23)"
        fields_list = ["stag=1:0:23"]
        self.verify_result(fields_list, out, mesg)

    def test_check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
        """
        self.start_testpmd("vlan")
        pkts_str = 'Ether(src="%s", dst="%s", type=0x9100)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received VLAN packet"
        fields_list = ["stag=1:0:23", "ctag=4:0:56"]
        self.verify_result(fields_list, out, mesg)

    def test_check_double_VLAN_fields_in_RXD_8021ad(self):
        """
        Check double VLAN fields in RXD (802.1ad)
        """
        self.start_testpmd("vlan")
        pkts_str = 'Ether(src="%s", dst="%s", type=0x88A8)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received VLAN packet"
        fields_list = ["stag=1:0:23", "ctag=4:0:56"]
        self.verify_result(fields_list, out, mesg)

    def test_check_IPv4_fields_in_RXD(self):
        """
        Check IPv4 fields in RXD
        """
        self.start_testpmd("ipv4")
        pkts_str = 'Ether(src="%s", dst="%s")/IP(tos=23, ttl=98)/UDP()/Raw(load="XXXXXXXXXX")' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received IPV4 packet"
        fields_list = ["ver=4", "hdrlen=5", "tos=23", "ttl=98", "proto=17"]
        self.verify_result(fields_list, out, mesg)

    def test_check_IPv6_fields_in_RXD(self):
        """
        Check IPv6 fields in RXD
        """
        self.start_testpmd("ipv6")
        pkts_str = 'Ether(src="%s", dst="%s")/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load="XXXXXXXXXX")' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received IPV6 packet"
        fields_list = ["ver=6", "tc=12", "flow_hi4=0x9", "nexthdr=17", "hoplimit=34"]
        self.verify_result(fields_list, out, mesg)

    def test_check_IPv6_flow_field_in_RXD(self):
        """
        Check IPv6 flow field in RXD
        """
        self.start_testpmd("ipv6_flow")
        pkts_str = 'Ether(src="%s", dst="%s")/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load="XXXXXXXXXX")' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received IPV6_flow packet"
        fields_list = ["ver=6", "tc=12", "flow=0x98765"]
        self.verify_result(fields_list, out, mesg)

    def test_check_TCP_fields_in_IPv4_in_RXD(self):
        """
        Check TCP fields in IPv4 in RXD
        """
        self.start_testpmd("tcp")
        pkts_str = 'Ether(src="%s", dst="%s")/IP()/TCP(flags="AS")/Raw(load="XXXXXXXXXX")' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received TCP packet"
        fields_list = ["doff=5", "flags=AS"]
        self.verify_result(fields_list, out, mesg)

    def test_check_TCP_fields_in_IPv6_in_RXD(self):
        """
        Check TCP fields in IPv6 in RXD
        """
        self.start_testpmd("tcp")
        pkts_str = 'Ether(src="%s", dst="%s")/IPv6()/TCP(flags="S")/Raw(load="XXXXXXXXXX")' % (self.src_mac, self.dst_mac)
        out = self.send_pkts_and_get_output(pkts_str)
        mesg = "There are no related fields in the received TCP packet"
        fields_list = ["doff=5", "flags=S"]
        self.verify_result(fields_list, out, mesg)

    def test_check_IPv4_IPv6_TCP_fields_in_RXD_on_specific_queues(self):
        """
        Check IPv4, IPv6, TCP fields in RXD on specific queues
        """
        self.start_testpmd("'[(2):ipv4,(3):ipv6,(4):tcp]'")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is %s / ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 23 ttl is 98 / end actions queue index 2 / end" % self.dst_mac, "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 12 / end actions queue index 3 / end", "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth dst is %s / ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp src is 25 dst is 23 / end actions queue index 4 / end" % self.dst_mac, "created")

        # send IPv4
        pkts_str = 'Ether(dst="%s")/IP(src="192.168.0.1",dst="192.168.0.2",tos=23,ttl=98)/UDP()/Raw(load="XXXXXXXXXX")' % (self.dst_mac)
        out1 = self.send_pkts_and_get_output(pkts_str)
        mesg1 = "There are no relevant fields in the received IPv4 packet."
        fields_list1 = ["Receive queue=0x2", "ver=4", "hdrlen=5", "tos=23", "ttl=98", "proto=17"]
        for field1 in fields_list1:
            self.verify(field1 in out1, mesg1)

        # send IPv6
        pkts_str = "Ether(src='%s', dst='%s')/IPv6(src='2001::3', dst='2001::4', tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load='XXXXXXXXXX')" % (self.src_mac, self.dst_mac)
        out2 = self.send_pkts_and_get_output(pkts_str)
        mesg2 = "There are no relevant fields in the received IPv6 packet."
        fields_list2 = ["Receive queue=0x3", "ver=6", "tc=12", "flow_hi4=0x9", "nexthdr=17", "hoplimit=34"]
        for field2 in fields_list2:
            self.verify(field2 in out2, mesg2)

        # send TCP
        pkts_str = 'Ether(dst="%s")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(flags="AS", dport=23, sport=25)/Raw(load="XXXXXXXXXX")' % (self.dst_mac)
        out3 = self.send_pkts_and_get_output(pkts_str)
        mesg3 = "There are no relevant fields in the received TCP packet."
        fields_list3 = ["Receive queue=0x4", "doff=5", "flags=AS"]
        for field3 in fields_list3:
            self.verify(field3 in out3, mesg3)
        self.dut.send_expect("quit", "#", 15)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        time.sleep(2)

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.restory_test_pmd()
