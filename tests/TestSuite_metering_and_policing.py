#BSD LICENSE
#
# Copyright(c) 2010-2016 Intel Corporation. All rights reserved.
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
Test metering_and_policing.
"""
import utils
import string
import time
import re
from test_case import TestCase
from plotting import Plotting
from settings import HEADER_SIZE
from dut import Dut


class TestMeteringAndPolicing(TestCase):

    def copy_config_files_to_dut(self):
        """
        Copy firmware.cli, dscp_*.sh from tester to DUT.
        """
        file = 'meter_and_policy_config.tar.gz'
        src_file = r'./dep/%s' % file
        dst1 = '/tmp'
        dst2 = '/root/dpdk/drivers/net/softnic'
        self.dut.session.copy_file_to(src_file, dst1)
        self.dut.send_expect("tar xf %s/%s -C %s" % (dst1, file, dst2), "#", 30)

    def update_firmware_cli(self, caseID):
        """
        Update firmware.cli.
        """
        self.ori_firmware_cli = "/root/dpdk/drivers/net/softnic/meter_and_policing_firmware.cli"
        if len(self.dut_ports) == 4:
            self.ori_firmware_cli = "/root/dpdk/drivers/net/softnic/meter_and_policing_firmware_4ports.cli"
        self.new_firmware_cli = "%s-%s" % (self.ori_firmware_cli, caseID)
        self.dut.send_expect("rm -f %s" % self.new_firmware_cli, "#")
        self.dut.send_expect("cp %s %s" % (self.ori_firmware_cli, self.new_firmware_cli), "#")

        # link dev
        self.dut.send_expect("sed -i -e 's/^.*link LINK0 dev.*$/link LINK0 dev %s/g' %s"
                             % (self.dut_p0_pci, self.new_firmware_cli), "#")
        self.dut.send_expect("sed -i -e 's/^.*link LINK1 dev.*$/link LINK1 dev %s/g' %s"
                             % (self.dut_p1_pci, self.new_firmware_cli), "#")
        if len(self.dut_ports) == 4:
            self.dut.send_expect("sed -i -e 's/^.*link LINK2 dev.*$/link LINK2 dev %s/g' %s"
                                 % (self.dut_p2_pci, self.new_firmware_cli), "#")
            self.dut.send_expect("sed -i -e 's/^.*link LINK3 dev.*$/link LINK3 dev %s/g' %s"
                                 % (self.dut_p3_pci, self.new_firmware_cli), "#")

        # table action
        temp = "table action profile AP0"
        if caseID == 8:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s ipv6 offset 270 fwd meter trtcm tc 1 stats pkts/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")
        else:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s ipv4 offset 270 fwd meter trtcm tc 1 stats pkts/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")

        # pipeline RX table
        temp = "pipeline RX table match"
        if caseID == 7:
            target = "hash ext key 16 mask 00FF0000FFFFFFFFFFFFFFFFFFFFFFFF offset 278 buckets 16K size 65K action AP0"
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s %s/g' %s"
                                 % (temp, temp, target, self.new_firmware_cli), "#")
        elif caseID == 8:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s acl ipv6 offset 270 size 4K action AP0/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")
        else:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s acl ipv4 offset 270 size 4K action AP0/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")

        # use .sh file as RX table
        temp = "pipeline RX table 0 dscp"
        if caseID == 10:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s  \/root\/dpdk\/drivers\/net\/softnic\/dscp_red.sh/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")
        elif caseID == 11:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s  \/root\/dpdk\/drivers\/net\/softnic\/dscp_yellow.sh/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")
        elif caseID == 12:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s  \/root\/dpdk\/drivers\/net\/softnic\/dscp_green.sh/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")
        elif caseID == 13:
            self.dut.send_expect("sed -i -e 's/^.*%s.*$/%s  \/root\/dpdk\/drivers\/net\/softnic\/dscp_default.sh/g' %s"
                                 % (temp, temp, self.new_firmware_cli), "#")

        # thread * pipeline RX/TX enable
        self.dut.send_expect("sed -i -e 's/thread 5 pipeline RX enable/thread %d pipeline RX enable/g' %s"
                             % (len(self.dut_ports), self.new_firmware_cli), "#")
        self.dut.send_expect("sed -i -e 's/thread 5 pipeline TX enable/thread %d pipeline TX enable/g' %s"
                             % (len(self.dut_ports), self.new_firmware_cli), "#")

    def start_testpmd(self, filename):
        """
        Start testpmd.
        """
        if len(self.dut_ports) == 2:
            portmask = "0x4"
            Corelist = "0x7"
            Servicecorelist = "0x4"
        if len(self.dut_ports) == 4:
            portmask = "0x10"
            Corelist = "0x1f"
            Servicecorelist = "0x10"
        self.path = "./%s/app/testpmd" % self.target
        cmd = self.path + " -c %s -s %s -n %d --vdev 'net_softnic0,firmware=%s,cpu_id=0,conn_port=8086' \
         -- -i --rxq=%d --txq=%d --portmask=%s" \
              % (Corelist, Servicecorelist, self.dut.get_memory_channels(), filename, self.port_id, self.port_id, portmask)
        self.dut.send_expect(cmd, "testpmd>", 60)

    def add_port_meter_profile(self, profile_id, cbs=400, pbs=500):
        """
        Add port meter profile (trTCM rfc2968).
        """
        cir = 3125000000
        pir = 3125000000
        self.dut.send_expect("add port meter profile trtcm_rfc2698 %d %d %d %d %d %d"
                             % (self.port_id, profile_id, cir, pir, cbs, pbs), "testpmd>")

    def create_port_meter(self, mtr_id, profile_id, gyrd_action):
        """
        Create new meter object for the ethernet device.
        """
        self.dut.send_expect("create port meter %d %d %d yes %s"
                             % (self.port_id, mtr_id, profile_id, gyrd_action), "testpmd>")

    def create_flow_rule(self, ret_id, ip_ver, protocol, spec_id,  mtr_id, queue_index_id):
        """
        Create flow rule based on port meter.
        """
        if ip_ver == "ipv4":
            src_mask = "255.255.255.255"
            dst_mask = "255.255.255.255"
            src_ip = "1.10.11.12"
            dst_ip = "2.20.21.22"
        if ip_ver == "ipv6":
            src_mask = "ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff"
            dst_mask = "0:0:0:0:0:0:0:0"
            src_ip = "ABCD:EF01:2345:6789:ABCD:EF01:2345:5789"
            dst_ip = "0:0:0:0:0:0:0:0"
        protocol = protocol.lower()
        if protocol == "tcp":
            proto_id = 6
        if protocol == "udp":
            proto_id = 17
        if protocol == "sctp":
            proto_id = 132

        out = self.dut.send_expect("flow create %d group 0 ingress pattern eth / %s proto mask 255 src mask %s dst mask"
                                   " %s src spec %s dst spec %s proto spec %d / %s src mask 65535 dst mask 65535 src "
                                   "spec %d dst spec %d / end actions meter mtr_id %d / queue index %d / end"
                                   % (self.port_id, ip_ver, src_mask, dst_mask, src_ip, dst_ip, proto_id, protocol,
                                      spec_id, spec_id, mtr_id, queue_index_id), "testpmd>")
        if ret_id == 1:
            self.verify("Flow rule #" in out, "flow create fail")
        else:
            self.verify("METER: Meter already attached to a flow: Invalid argument" in out,
                        "flow create should fail, but NOT failed")

    def scapy_send_packet(self, ip_ver, protocol, fwd_port, pktsize):
        """
        Send a packet to DUT port 0
        """
        source_port = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        protocol = protocol.upper()
        if ip_ver == "ipv4":
            src_ip = "1.10.11.12"
            dst_ip = "2.20.21.22"
            tag = "IP"
            if protocol == "TCP":
                proto_str = "proto=6"
            if protocol == "UDP":
                proto_str = "proto=17"
            if protocol == "SCTP":
                proto_str = "proto=132"

        if ip_ver == "ipv6":
            src_ip = "ABCD:EF01:2345:6789:ABCD:EF01:2345:5789"
            dst_ip = "2001::1"
            tag = "IPv6"
            if protocol == "TCP":
                proto_str = "nh=6"
            if protocol == "UDP":
                proto_str = "nh=17"

        self.tester.scapy_append(
            'sendp([Ether(dst="%s")/%s(src="%s",dst="%s",%s)/%s(sport=%d,dport=%d)/Raw(load="P"*%d)], iface="%s")'
            % (self.dut_p0_mac, tag, src_ip, dst_ip, proto_str, protocol, fwd_port, fwd_port, pktsize, source_port))
        self.tester.scapy_execute()

    def send_packet_and_check(self, ip_ver, protocol, fwd_port, pktsize, expect_port):
        """
        Send packet and check the stats. If expect_port == -1, the packet should be dropped.
        """
        time.sleep(3)
        rx_before = []
        tx_before = []
        for i in range(0, len(self.dut_ports)):
            output = self.dut.send_expect("show port stats %d" %(i),"testpmd>")
            if i == 0:
                rx_before.append(re.compile('RX-packets:\s+(.*?)\s+?').findall(output, re.S))
            tx_before.append(re.compile('TX-packets:\s+(.*?)\s+?').findall(output, re.S))

        self.scapy_send_packet(ip_ver, protocol, fwd_port, pktsize)

        rx_after = []
        tx_after = []
        for i in range(0, len(self.dut_ports)):
            output = self.dut.send_expect("show port stats %d" %(i),"testpmd>")
            if i == 0:
                rx_after.append(re.compile('RX-packets:\s+(.*?)\s+?').findall(output, re.S))
            tx_after.append(re.compile('TX-packets:\s+(.*?)\s+?').findall(output, re.S))

        rx_packets_port = []
        tx_packets_port = []
        temp1 = int(rx_after[0][0]) - int(rx_before[0][0])
        rx_packets_port.append(temp1)
        for i in range(0, len(self.dut_ports)):
            temp2 = int(tx_after[i][0]) - int(tx_before[i][0])
            tx_packets_port.append(temp2)
        self.verify(int(rx_packets_port[0]) == 1, "Wrong: port 0 did not recieve any packet")
        if expect_port == -1:
            for i in range(0, len(self.dut_ports)):
                self.verify(int(tx_packets_port[i]) == 0, "Wrong: the packet is not dropped")
        else:
            self.verify(int(tx_packets_port[expect_port]) == 1, "Wrong: can't forward package to port %d " % expect_port)

    def run_param(self, cbs, pbs, head):
        """
        Set cbs, pbs and head; return the packet size
        """
        pkt1 = pbs - head + 1
        pkt2 = pbs - head
        pkt3 = cbs - head + 1
        pkt4 = cbs - head
        pkt_list = [pkt1,pkt2,pkt3,pkt4]
        return pkt_list

    def run_port_list(self,ip_ver,protocol,fwd_port,pkt_list,port_list):
        for i in range(len(port_list)):
            self.send_packet_and_check(ip_ver=ip_ver, protocol=protocol, fwd_port=fwd_port, pktsize=pkt_list[i], expect_port=port_list[i])

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.dut_ports = self.dut.get_ports()
        self.port_nums = 2
        self.verify(len(self.dut_ports) >= self.port_nums,
                    "Insufficient ports for speed testing")
        self.dut_p0_pci = self.dut.get_port_pci(self.dut_ports[0])
        self.dut_p1_pci = self.dut.get_port_pci(self.dut_ports[1])
        if len(self.dut_ports) == 4:
            self.dut_p2_pci = self.dut.get_port_pci(self.dut_ports[2])
            self.dut_p3_pci = self.dut.get_port_pci(self.dut_ports[3])
        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.port_id = len(self.dut_ports)
        self.copy_config_files_to_dut()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def test_ipv4_ACL_table_RFC2698_GYR(self):
        """
        Test Case 1: ipv4 ACL table RFC2698 GYR
        """
        self.update_firmware_cli(caseID=1)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

    def test_ipv4_ACL_table_RFC2698_GYD(self):
        """
        Test Case 2: ipv4 ACL table RFC2698 GYD
        """
        self.update_firmware_cli(caseID=2)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,0,0,0])

    def test_ipv4_ACL_table_RFC2698_GDR(self):
        """
        Test Case 3: ipv4 ACL table RFC2698 GDR
        """
        self.update_firmware_cli(caseID=3)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=32)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="sctp", spec_id=2, mtr_id=0, queue_index_id=1)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","sctp",2,pkt_list,[1,-1,-1,1])

    def test_ipv4_ACL_table_RFC2698_DYR(self):
        """
        Test Case 4: ipv4 ACL table RFC2698 DYR
        """
        self.update_firmware_cli(caseID=4)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=28)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="udp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","udp",2,pkt_list,[0,0,0,-1])

    def test_ipv4_ACL_table_RFC2698_DDD(self):
        """
        Test Case 5: ipv4 ACL table RFC2698 DDD
        """
        self.update_firmware_cli(caseID=5)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="d d d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,-1,-1,-1])

    def test_ipv4_with_same_cbs_and_pbs_GDR(self):
        """
        Test Case 6: ipv4 with same cbs and pbs GDR
        """
        self.update_firmware_cli(caseID=6)
        cbs = 500
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=32)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="sctp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","sctp",2,pkt_list,[0,0])

    def test_ipv4_HASH_table_RFC2698(self):
        """
        Test Case 7: ipv4 HASH table RFC2698
        """
        self.update_firmware_cli(caseID=7)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)

        # test 1 'g y r 0 0 0'
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])
        self.dut.send_expect("quit", "#", 30)

        # test 2 'g y d 0 0 0'
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,0,0,0])
        self.dut.send_expect("quit", "#", 30)

        # test 5 'd d d 0 0 0'
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="d d d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,-1,-1,-1])
        self.dut.send_expect("quit", "#", 30)

        # test 3 'g d r 0 0 0'
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=32)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="sctp", spec_id=2, mtr_id=0, queue_index_id=1)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","sctp",2,pkt_list,[1,-1,-1,1])
        self.dut.send_expect("quit", "#", 30)

        # test 4 'd y r 0 0 0'
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=28)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="udp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.dut.send_expect("start", "testpmd>")
        self.run_port_list("ipv4","udp",2,pkt_list,[0,0,0,-1])
        self.dut.send_expect("quit", "#", 30)

    def test_ipv6_ACL_table_RFC2698(self):
        """
        Test Case 8: ipv6 ACL table RFC2698
        """
        self.update_firmware_cli(caseID=8)
        cbs = 400
        pbs = 500
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_port_meter(mtr_id=1, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv6", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.create_flow_rule(ret_id=1, ip_ver="ipv6", protocol="udp", spec_id=2, mtr_id=1, queue_index_id=1)
        self.dut.send_expect("start","testpmd>")

        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=60)
        self.run_port_list("ipv6","tcp",2,pkt_list,[-1,0,0,0])

        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=48)
        self.run_port_list("ipv6","udp",2,pkt_list,[1,1,1,-1])

    def test_ipv4_multiple_meter_and_profile(self):
        """
        Test Case 9: multiple meter and profile
        """
        self.update_firmware_cli(caseID=9)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=400, pbs=500)
        self.add_port_meter_profile(profile_id=1, cbs=300, pbs=400)

        gyrd_action_list = ["g y r 0 0 0", "g y d 0 0 0", "g d r 0 0 0", "d y r 0 0 0", "g y d 0 0 0", "g d r 0 0 0", "d y r 0 0 0", "d d d 0 0 0"]
        for i in range(0,len(gyrd_action_list)):
            self.create_port_meter(mtr_id=i, profile_id=i*2/len(gyrd_action_list), gyrd_action=gyrd_action_list[i])
            self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=i, mtr_id=i, queue_index_id=i%len(self.dut_ports))
        self.create_flow_rule(ret_id=0, ip_ver="ipv4", protocol="tcp", spec_id=8, mtr_id=7, queue_index_id=0)

        self.dut.send_expect("start", "testpmd>")
        output = self.dut.send_expect("flow list %d" % (self.port_id), "testpmd>")
        print(output)

        pkt_list = self.run_param(cbs=400,pbs=500,head=40)
        if len(self.dut_ports) == 4:
            self.run_port_list("ipv4","tcp",0,pkt_list,[0,0,0,0])
            self.run_port_list("ipv4","tcp",1,pkt_list,[-1,1,1,1])
            self.run_port_list("ipv4","tcp",2,pkt_list,[2,-1,-1,2])
            self.run_port_list("ipv4","tcp",3,pkt_list,[3,3,3,-1])
        if len(self.dut_ports) == 2:
            self.run_port_list("ipv4","tcp",0,pkt_list,[0,0,0,0])
            self.run_port_list("ipv4","tcp",1,pkt_list,[-1,1,1,1])
            self.run_port_list("ipv4","tcp",2,pkt_list,[0,-1,-1,0])
            self.run_port_list("ipv4","tcp",3,pkt_list,[1,1,1,-1])


        pkt_list = self.run_param(cbs=300,pbs=400,head=40)
        if len(self.dut_ports) == 4:
            self.run_port_list("ipv4","tcp",4,pkt_list,[-1,0,0,0])
            self.run_port_list("ipv4","tcp",5,pkt_list,[1,-1,-1,1])
            self.run_port_list("ipv4","tcp",6,pkt_list,[2,2,2,-1])
            self.run_port_list("ipv4","tcp",7,pkt_list,[-1,-1,-1,-1])
        if len(self.dut_ports) == 2:
            self.run_port_list("ipv4","tcp",4,pkt_list,[-1,0,0,0])
            self.run_port_list("ipv4","tcp",5,pkt_list,[1,-1,-1,1])
            self.run_port_list("ipv4","tcp",6,pkt_list,[0,0,0,-1])
            self.run_port_list("ipv4","tcp",7,pkt_list,[-1,-1,-1,-1])

    def test_ipv4_RFC2698_pre_colored_red_by_DSCP_table(self):
        """
        Test Case 10: ipv4 RFC2698 pre-colored red by DSCP table
        """
        self.update_firmware_cli(caseID=10)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.dut.send_expect("start", "testpmd>")

        # test 0: GYR
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

        # test 1: GYD
        self.create_port_meter(mtr_id=1, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=1, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,-1,-1,-1])

        # test 2: GDR
        self.create_port_meter(mtr_id=2, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=2, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

        # test 3: DYR
        self.create_port_meter(mtr_id=3, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=3, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

    def test_ipv4_RFC2698_pre_colored_yellow_by_DSCP_table(self):
        """
        Test Case 11: ipv4 RFC2698 pre-colored yellow by DSCP table
        """
        self.update_firmware_cli(caseID=11)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.dut.send_expect("start", "testpmd>")

        # test 0: GYR
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

        # test 1: GYD
        self.create_port_meter(mtr_id=1, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=1, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,0,0,0])

        # test 2: GDR
        self.create_port_meter(mtr_id=2, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=2, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,-1,-1,-1])

        # test 3: DYR
        self.create_port_meter(mtr_id=3, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=3, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

    def test_ipv4_RFC2698_pre_colored_green_by_DSCP_table(self):
        """
        Test Case 12: ipv4 RFC2698 pre-colored green by DSCP table
        """
        self.update_firmware_cli(caseID=12)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.dut.send_expect("start", "testpmd>")

        # test 0: GYR
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

        # test 1: GYD
        self.create_port_meter(mtr_id=1, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=1, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,0,0,0])

        # test 2: GDR
        self.create_port_meter(mtr_id=2, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=2, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,-1,-1,0])

        # test 3: DYR
        self.create_port_meter(mtr_id=3, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=3, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,-1])

    def test_ipv4_RFC2698_pre_colored_default_by_DSCP_table(self):
        """
        Test Case 13: ipv4 RFC2698 pre-colored by default DSCP table
        """
        self.update_firmware_cli(caseID=13)
        cbs = 400
        pbs = 500
        pkt_list = self.run_param(cbs=cbs, pbs=pbs, head=40)
        self.start_testpmd(self.new_firmware_cli)
        self.add_port_meter_profile(profile_id=0, cbs=cbs, pbs=pbs)
        self.dut.send_expect("start", "testpmd>")

        # test 0: GYR
        self.create_port_meter(mtr_id=0, profile_id=0, gyrd_action="g y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=0, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,0])

        # test 1: GYD
        self.create_port_meter(mtr_id=1, profile_id=0, gyrd_action="g y d 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=1, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[-1,0,0,0])

        # test 2: GDR
        self.create_port_meter(mtr_id=2, profile_id=0, gyrd_action="g d r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=2, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,-1,-1,0])

        # test 3: DYR
        self.create_port_meter(mtr_id=3, profile_id=0, gyrd_action="d y r 0 0 0")
        self.create_flow_rule(ret_id=1, ip_ver="ipv4", protocol="tcp", spec_id=2, mtr_id=3, queue_index_id=0)
        self.run_port_list("ipv4","tcp",2,pkt_list,[0,0,0,-1])

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
        pass
