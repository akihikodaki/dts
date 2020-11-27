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

import time
from packet import Packet
from pmd_output import PmdOutput
import re


class FlexibleRxdBase(object):

    def init_base(self, pci, dst_mac, test_type, dut_index=0):
        tester_port_id = self.tester.get_local_port(self.dut_ports[dut_index])
        self.__tester_intf = self.tester.get_interface(tester_port_id)
        self.__src_mac = self.tester.get_mac(tester_port_id)
        self.__dst_mac = dst_mac

        self.__app_path = self.dut.apps_name["test-pmd"]
        self.__pmdout = PmdOutput(self.dut)
        self.__test_type = test_type
        self.__pci = pci
        self.__pkg_count = 1
        self.__is_pmd_on = False

    @property
    def __is_iavf(self):
        return self.__test_type == 'iavf'

    @property
    def __is_pf(self):
        return self.__test_type == 'pf'

    def __get_port_option(self, flex_opt='', queue_num=None):
        nb_core = 2
        num = 4 if self.nic == 'foxville' or self.__is_iavf else 32
        queue_num = queue_num if queue_num else num
        # port option
        port_option = (
            '{queue} '
            '--portmask=0x1 '
            '--nb-cores={nb_core}').format(**{
                'queue': '--rxq={0} --txq={0} '.format(queue_num)
                if flex_opt != 'ip_offset' else '',
                'nb_core': nb_core,
            })
        return port_option

    def __check_rxdid(self, rxdid, out):
        rxdid = rxdid if isinstance(rxdid, list) else [rxdid]
        pat = "RXDID\[(\d+)\]"
        for rx in rxdid:
            if self.__is_pf:
                value = re.findall(pat, rx)
                if not value:
                    continue
                check_str = "RXDID : {}".format(value[0])
                self.verify(
                    check_str in out,
                    "rxdid value error, expected rxdid is %s" % check_str)
            else:
                self.verify(
                    rx in out,
                    "rxdid value error, expected rxdid is %s" % rx)

    def start_testpmd(self, flex_opt, rxdid, queue_num=None):
        """
        start testpmd
        """
        param_type = 'proto_xtr'
        # port option
        port_option = self.__get_port_option(flex_opt, queue_num=queue_num)
        # start test pmd
        out = self.__pmdout.start_testpmd(
            "1S/3C/1T",
            param=port_option,
            eal_param='' if self.__is_iavf else '--log-level="ice,8"',
            ports=[self.__pci],
            port_options={self.__pci: '%s=%s' % (param_type, flex_opt)})
        self.__is_pmd_on = True
        # check rxdid value correct
        self.__check_rxdid(rxdid, out)
        # set test pmd command
        if flex_opt == 'ip_offset':
            cmds = [
                'set verbose 1',
                'start',
            ]
        else:
            cmds = [
                "set verbose 1",
                "set fwd io",
                "set promisc all off",
                "clear port stats all",
                "start", ]
        [self.dut.send_expect(cmd, "testpmd> ", 15) for cmd in cmds]

    def close_testpmd(self):
        if not self.__is_pmd_on:
            return
        try:
            self.__pmdout.quit()
            self.__is_pmd_on = False
        except Exception as e:
            pass

    def __send_pkts_and_get_output(self, pkt_str):
        pkt = Packet(pkt_str)
        pkt.send_pkt(
            self.tester,
            tx_port=self.__tester_intf,
            count=self.__pkg_count,
            timeout=30)
        time.sleep(0.5)
        output = self.dut.get_session_output(timeout=3)
        return output

    def __verify_common(self, pkts_list, msg=None):
        """
        send MPLS type packet, verify packet ip_offset value correct
        param pkts_list:
            [send packets list, ip_offset expected value]
        """
        msg = msg if msg else "ip_offset value error, case test failed"
        for pkt_str, expected_strs in pkts_list:
            out = self.__send_pkts_and_get_output(
                pkt_str.format(**{
                    'src_mac': self.__src_mac,
                    'dst_mac': self.__dst_mac}))
            # validation results
            _expected_strs = [expected_strs] \
                if isinstance(expected_strs, str) else \
                expected_strs
            self.verify(all([e in out for e in _expected_strs]), msg)

    def replace_pkg(self, pkg='comms'):
        ice_pkg_path = ''.join([self.ddp_dir, "ice.pkg"])
        if pkg == 'os_default':
            self.dut.send_expect("cp {} {}".format(self.os_default_pkg, ice_pkg_path), "# ")
        if pkg == 'comms':
            self.dut.send_expect("cp {} {}".format(self.comms_pkg, ice_pkg_path), "# ")
        self.dut.send_expect("echo {0} > /sys/bus/pci/devices/{0}/driver/unbind".format(self.pci), "# ", 60)
        self.dut.send_expect("echo {} > /sys/bus/pci/drivers/ice/bind".format(self.pci), "# ", 60)
        self.dut.send_expect("./usertools/dpdk-devbind.py --force --bind=vfio-pci {}".format(self.pci), "# ", 60)
        dmesg_out = self.dut.send_expect('dmesg | grep Package | tail -1', '#')
        package_version = re.search('version (.*)', dmesg_out).group(1)
        self.logger.info("package version:{}".format(package_version))
        self.verify(package_version in self.os_default_pkg if pkg == 'os_default' else self.comms_pkg,
                    'replace package failed')

    def check_single_VLAN_fields_in_RXD_8021Q(self):
        """
        Check single VLAN fields in RXD (802.1Q)
        """
        self.start_testpmd("vlan", "RXDID[17]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}", type=0x8100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()'
        msg = "The packet does not carry a VLAN tag."
        fields_list = ["vlan"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_single_VLAN_fields_in_RXD_8021ad(self):
        """
        Check single VLAN fields in RXD (802.1ad)
        """
        self.start_testpmd("vlan", "RXDID[17]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}", type=0x88A8)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()'
        msg = "stag result is not expected (stag=1:0:23)"
        fields_list = ["stag=1:0:23"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_double_VLAN_fields_in_RXD_8021Q_1_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) only 1 VLAN tag
        """
        self.start_testpmd("vlan", "RXDID[17]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}", type=0x9100)/Dot1Q(prio=1,vlan=23)/IP()/UDP()/DNS()'
        msg = "stag result is not expected (stag=1:0:23)"
        fields_list = ["stag=1:0:23"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_double_VLAN_fields_in_RXD_8021Q_2_VLAN_tag(self):
        """
        Check double VLAN fields in RXD (802.1Q) 2 VLAN tags
        """
        self.start_testpmd("vlan", "RXDID[17]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}", type=0x9100)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()'
        msg = "There are no related fields in the received VLAN packet"
        fields_list = ["stag=1:0:23", "ctag=4:0:56"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_double_VLAN_fields_in_RXD_8021ad(self):
        """
        Check double VLAN fields in RXD (802.1ad)
        """
        self.start_testpmd("vlan", "RXDID[17]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}", type=0x88A8)/Dot1Q(prio=1,vlan=23)/Dot1Q(prio=4,vlan=56)/IP()/UDP()/DNS()'
        msg = "There are no related fields in the received VLAN packet"
        fields_list = ["stag=1:0:23", "ctag=4:0:56"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_IPv4_fields_in_RXD(self):
        """
        Check IPv4 fields in RXD
        """
        self.start_testpmd("ipv4", "RXDID[18]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}")/IP(tos=23, ttl=98)/UDP()/Raw(load="XXXXXXXXXX")'
        msg = "There are no related fields in the received IPV4 packet"
        fields_list = ["ver=4", "hdrlen=5", "tos=23", "ttl=98", "proto=17"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_IPv6_fields_in_RXD(self):
        """
        Check IPv6 fields in RXD
        """
        self.start_testpmd("ipv6", "RXDID[19]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}")/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load="XXXXXXXXXX")'
        msg = "There are no related fields in the received IPV6 packet"
        fields_list = [
            "ver=6", "tc=12", "flow_hi4=0x9", "nexthdr=17", "hoplimit=34"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_IPv6_flow_field_in_RXD(self):
        """
        Check IPv6 flow field in RXD
        """
        self.start_testpmd("ipv6_flow", "RXDID[20]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}")/IPv6(tc=12,hlim=34,fl=0x98765)/UDP()/Raw(load="XXXXXXXXXX")'
        msg = "There are no related fields in the received IPV6_flow packet"
        fields_list = ["ver=6", "tc=12", "flow=0x98765"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_TCP_fields_in_IPv4_in_RXD(self):
        """
        Check TCP fields in IPv4 in RXD
        """
        self.start_testpmd("tcp", "RXDID[21]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}")/IP()/TCP(flags="AS")/Raw(load="XXXXXXXXXX")'
        msg = "There are no related fields in the received TCP packet"
        fields_list = ["doff=5", "flags=AS"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_TCP_fields_in_IPv6_in_RXD(self):
        """
        Check TCP fields in IPv6 in RXD
        """
        self.start_testpmd("tcp", "RXDID[21]")
        pkts_str = 'Ether(src="{src_mac}", dst="{dst_mac}")/IPv6()/TCP(flags="S")/Raw(load="XXXXXXXXXX")'
        msg = "There are no related fields in the received TCP packet"
        fields_list = ["doff=5", "flags=S"]
        self.__verify_common([[pkts_str, fields_list]], msg)

    def check_IPv4_IPv6_TCP_fields_in_RXD_on_specific_queues(self):
        """
        Check IPv4, IPv6, TCP fields in RXD on specific queues
        """
        self.start_testpmd(
            "'[(2):ipv4,(3):ipv6,(4):tcp]'",
            ["RXDID[18]", "RXDID[19]", "RXDID[22]"] if self.__is_iavf else
            ["RXDID[18]", "RXDID[19]", "RXDID[21]", "RXDID[22]"],
            16)
        self.dut.send_expect(
            "flow create 0 ingress pattern eth {}/ ipv4 src is 192.168.0.1 dst is 192.168.0.2 tos is 23 ttl is 98 / end actions queue index 2 / end".format(
                '' if self.__is_iavf else "dst is {} ".format(self.__dst_mac)),
            "created")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth / ipv6 src is 2001::3 dst is 2001::4 tc is 12 / end actions queue index 3 / end",
            "created")
        # send IPv4
        pkts_str = \
            'Ether(dst="{dst_mac}")/IP(src="192.168.0.1",dst="192.168.0.2",tos=23,ttl=98)/UDP()/Raw(load="XXXXXXXXXX")'
        msg1 = "There are no relevant fields in the received IPv4 packet."
        fields_list1 = ["Receive queue=0x2", "ver=4",
                        "hdrlen=5", "tos=23", "ttl=98", "proto=17"]
        self.__verify_common([[pkts_str, fields_list1]], msg1)

        # send IPv6
        pkts_str = \
            'Ether(src="{src_mac}", dst="{dst_mac}")/IPv6(src="2001::3", dst="2001::4", tc=12, hlim=34,fl=0x98765)/UDP()/Raw(load="XXXXXXXXXX")'
        msg2 = "There are no relevant fields in the received IPv6 packet."
        fields_list2 = [
            "Receive queue=0x3",
            "ver=6",
            "tc=12",
            "flow_hi4=0x9",
            "nexthdr=17",
            "hoplimit=34"]
        self.__verify_common([[pkts_str, fields_list2]], msg2)

        # send TCP
        self.dut.send_expect("flow flush 0", "testpmd>")
        self.dut.send_expect(
            "flow create 0 ingress pattern eth {0}/ ipv4 src is 192.168.0.1 dst is 192.168.0.2 / tcp src is 25 dst is 23 / end actions queue index {1} / end".format(
                '' if self.__is_iavf else "dst is {} ".format(self.__dst_mac),
                4, ),
            "created")
        pkts_str = \
            'Ether(dst="{dst_mac}")/IP(src="192.168.0.1", dst="192.168.0.2")/TCP(flags="AS", dport=23, sport=25)/Raw(load="XXXXXXXXXX")'
        msg3 = "There are no relevant fields in the received TCP packet."
        fields_list3 = [
            "Receive queue=0x4",
            "doff=5",
            "flags=AS"]
        self.__verify_common([[pkts_str, fields_list3]], msg3)

    def check_testpmd_use_different_parameters(self):
        """
        Check testpmd use different parameters start
        """
        param_type = 'proto_xtr'
        # port option
        port_opt = self.__get_port_option()
        # use error parameter Launch testpmd, testpmd can not be started
        cmd = (
            "-l 1,2,3 "
            "-n {mem_channel} "
            "-w {pci},{param_type}=vxlan "
            "-- -i "
            "{port_opt}").format(**{
                'mem_channel': self.dut.get_memory_channels(),
                "pci": self.__pci,
                "param_type": param_type,
                "port_opt": port_opt,
            })
        try:
            out = self.__pmdout.execute_cmd(self.__app_path + cmd, "#")
            self.__is_pmd_on = False
        except Exception as e:
            self.__is_pmd_on = True
        expected = \
            "iavf_lookup_proto_xtr_type(): wrong proto_xtr type, it should be: vlan|ipv4|ipv6|ipv6_flow|tcp|ip_offset" \
            if self.__is_iavf else \
            "handle_proto_xtr_arg(): The protocol extraction parameter is wrong : 'vxlan'"
        self.close_testpmd()
        self.verify(expected in out, "case test failed, testpmd started")
        # don't use parameter launch testpmd, testpmd started and rxdid value
        # is the default
        cmd = (
            "-l 1,2,3 "
            "-n {mem_channel} "
            "-w {pci} "
            "--log-level='ice,8' "
            "-- -i "
            "{port_opt}").format(**{
                'mem_channel': self.dut.get_memory_channels(),
                "pci": self.__pci,
                "param_type": param_type,
                "port_opt": port_opt,
            })
        out = self.__pmdout.execute_cmd(self.__app_path + cmd, "testpmd>")
        self.__is_pmd_on = True
        self.close_testpmd()
        self.__check_rxdid("RXDID[22]", out)

    def check_ip_offset_of_ip(self):
        """
        Check ip offset of ip
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=18'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=18']]
        self.__verify_common(pkts_list)

    def check_ip_offset_with_vlan(self):
        """
        check ip offset with vlan
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=22'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=22']]
        self.__verify_common(pkts_list)

    def check_ip_offset_with_2_vlan_tag(self):
        """
        check offset with 2 vlan tag
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=26']]
        self.__verify_common(pkts_list)

    def check_ip_offset_with_multi_MPLS(self):
        """
        check ip offset with multi MPLS
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=18'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=22'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=34'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=18'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=22'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=34']]
        self.__verify_common(pkts_list)

    def check_ip_offset_with_multi_MPLS_with_vlan_tag(self):
        """
        check ip offset with multi MPLS with vlan tag
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=22'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=34'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=38'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=22'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=34'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=38']]
        self.__verify_common(pkts_list)

    def check_ip_offset_with_multi_MPLS_with_2_vlan_tag(self):
        """
        check ip offset with multi MPLS with 2 vlan tag
        """
        self.start_testpmd("ip_offset", "RXDID[25]")
        pkts_list = [
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IP()',
             'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=34'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=38'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IP()',
                'ip_offset=42'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=1)/IPv6()',
                'ip_offset=26'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=30'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=34'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=38'],
            ['Ether(src="{src_mac}", dst="{dst_mac}",type=0x88A8)/Dot1Q(type=0x8100)/Dot1Q(type=0x8847)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=0)/MPLS(s=1)/IPv6()',
                'ip_offset=42']]
        self.__verify_common(pkts_list)

    def check_effect_replace_pkg_RXID_22_to_RXID_16(self):
        self.logger.info("replace ice-1.3.7.0.pkg with RXID 16")
        self.replace_pkg('os_default')
        out = self.__pmdout.start_testpmd(cores="1S/4C/1T", param='--rxq=64 --txq=64', eal_param=f"-w {self.__pci}")
        self.verify("Fail to start port 0" in out, "RXID #16 not support start testpmd")
        self.__pmdout.execute_cmd("quit", "# ")
        self.replace_pkg('comms')
