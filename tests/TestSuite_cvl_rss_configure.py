import json
import time
import re
import packet
import os
from scapy.contrib.gtp import *
from test_case import TestCase
from pmd_output import PmdOutput
from utils import BLUE, RED
from collections import OrderedDict
from packet import IncreaseIP, IncreaseIPv6
import rte_flow_common as rfc

out = os.popen("pip list|grep scapy ")
version_result =out.read()
p=re.compile('scapy\s+2\.3\.\d+')
m=p.search(version_result)

tv_mac_ip_ipv4 = {
    "name":"tv_mac_ip_ipv4",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ip_ipv6 = {
    "name":"tv_mac_ip_ipv6",
    "scapy_str": ['Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::%d", dst="2001::%d")/("X"*480)' %(i, i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_l3_random = {
    "name":"tv_mac_ipv4_udp_l3_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_udp_l4_random = {
    "name":"tv_mac_ipv4_udp_l4_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP()/UDP(sport=%d, dport=%d)/("X"*480)' %(i+50,i+55) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_udp_l3_random = {
    "name":"tv_mac_ipv6_udp_l3_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::%d", dst="2001::%d")/UDP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_udp_l4_random = {
    "name":"tv_mac_ipv6_udp_l4_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IPv6()/UDP(sport=%d, dport=%d)/("X"*480)' %(i+50,i+55) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_l3_random = {
    "name":"tv_mac_ipv4_tcp_l3_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_tcp_l4_random = {
    "name":"tv_mac_ipv4_tcp_l4_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP()/TCP(sport=%d, dport=%d)/("X"*480)' %(i+50,i+55) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_tcp_l3_random = {
    "name":"tv_mac_ipv6_tcp_l3_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::%d", dst="2001::%d")/TCP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_tcp_l4_random = {
    "name":"tv_mac_ipv6_tcp_l4_random",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IPv6()/TCP(sport=%d, dport=%d)/("X"*480)' %(i+50,i+55) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv4_sctp = {
    "name":"tv_mac_ipv4_sctp",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tv_mac_ipv6_sctp = {
    "name":"tv_mac_ipv6_sctp",
    "scapy_str":['Ether(dst="00:00:00:00:01:00")/IPv6(src="2001::%d", dst="2001::%d")/SCTP()/("X"*480)' %(i,i+10) for i in range(0,100)],
    "check_func_param": {"expect_port":0}
}

tvs_mac_rss_ip = [
    tv_mac_ip_ipv4,
    tv_mac_ip_ipv6
    ]

tvs_mac_rss_l3 = [
    tv_mac_ip_ipv4,
    tv_mac_ip_ipv6,
    tv_mac_ipv4_udp_l3_random,
    tv_mac_ipv6_udp_l3_random,
    tv_mac_ipv4_tcp_l3_random,
    tv_mac_ipv6_tcp_l3_random,
    tv_mac_ipv4_sctp,
    tv_mac_ipv6_sctp
    ]

tvs_mac_rss_l4 = [
    tv_mac_ipv4_udp_l4_random,
    tv_mac_ipv6_udp_l4_random,
    tv_mac_ipv4_tcp_l4_random,
    tv_mac_ipv6_tcp_l4_random
    ]

tvs_mac_rss_udp = [
    tv_mac_ipv4_udp_l3_random,
    tv_mac_ipv4_udp_l4_random,
    tv_mac_ipv6_udp_l3_random,
    tv_mac_ipv6_udp_l4_random
    ]

tvs_mac_rss_udp_l4 = [
    tv_mac_ipv4_udp_l4_random,
    tv_mac_ipv6_udp_l4_random
    ]

tvs_mac_rss_tcp = [
    tv_mac_ipv4_tcp_l3_random,
    tv_mac_ipv4_tcp_l4_random,
    tv_mac_ipv6_tcp_l3_random,
    tv_mac_ipv6_tcp_l4_random
    ]

tvs_mac_rss_tcp_l4 = [
    tv_mac_ipv4_tcp_l4_random,
    tv_mac_ipv6_tcp_l4_random
    ]

tvs_mac_rss_sctp = [
    tv_mac_ipv4_sctp,
    tv_mac_ipv6_sctp
    ]

tvs_mac_rss_all = [
    tv_mac_ip_ipv4,
    tv_mac_ip_ipv6,
    tv_mac_ipv4_udp_l3_random,
    tv_mac_ipv4_udp_l4_random,
    tv_mac_ipv6_udp_l3_random,
    tv_mac_ipv6_udp_l4_random,
    tv_mac_ipv4_tcp_l3_random,
    tv_mac_ipv4_tcp_l4_random,
    tv_mac_ipv6_tcp_l3_random,
    tv_mac_ipv6_tcp_l4_random,
    tv_mac_ipv4_sctp,
    tv_mac_ipv6_sctp
    ]

test_results = OrderedDict()

class RSSConfigureTest(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        Generic filter Prerequistites
        """
        self.dut_ports = self.dut.get_ports(self.nic)
        # Verify that enough ports are available
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        #self.cores = "1S/8C/1T"
        self.pmdout = PmdOutput(self.dut)

        localPort = self.tester.get_local_port(self.dut_ports[0])
        self.__tx_iface = self.tester.get_interface(localPort)
        self.pf_interface = self.dut.ports_info[self.dut_ports[0]]['intf']
        self.pf_mac = self.dut.get_mac_address(0)
        self.pf_pci = self.dut.ports_info[self.dut_ports[0]]['pci']
        self.verify(self.nic in ["columbiaville_25g","columbiaville_100g"], "%s nic not support ethertype filter" % self.nic)

    def set_up(self):
        """
        Run before each test case.
        """
        self.dut.kill_all()

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
    
    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()

    def create_testpmd_command(self, line_option):
        """
        Create testpmd command for non-pipeline mode
        """
        #Prepare testpmd EAL and parameters 
        all_eal_param = self.dut.create_eal_parameters(ports=[self.pf_pci])
        print(all_eal_param)   #print eal parameters
        command = "./%s/app/testpmd %s  -- -i %s" % (self.dut.target, all_eal_param, "--rxq=10 --txq=10" + line_option)
        return command

    def _rss_validate_pattern(self, test_vectors, command, rss_type, is_rss):

        global test_results
        out = self.dut.send_expect(command, "testpmd> ", 120)
        self.logger.debug(out)  #print the log
        self.dut.send_expect("set fwd rxonly", "testpmd> ", 15)
        self.dut.send_expect("set verbose 1", "testpmd> ", 15)
        if rss_type != "":
            self.dut.send_expect("port config all rss %s" % rss_type, "testpmd> ", 15)

        test_results.clear()
        self.count = 1
        self.mac_count=100
        for tv in test_vectors:
            self.dut.send_expect("start", "testpmd> ", 15)
            time.sleep(2)
            tv["check_func_param"]["expect_port"] = self.dut_ports[0]
            print("expect_port is", self.dut_ports[0])

            #send a packet
            pkt = packet.Packet()
            pkt.update_pkt(tv["scapy_str"])
            pkt.send_pkt(self.tester, tx_port=self.__tx_iface, count=self.count)

            out = self.dut.send_expect("stop", "testpmd> ",60)
            print(out)
            check_result = []
            check_result = rfc.check_packets_of_each_queue(out)
            self.verify(check_result[0] == is_rss, check_result[1])

        self.dut.send_expect("quit", "#")

    def test_command_line_option_rss_ip(self):
        command = self.create_testpmd_command(line_option = " --rss-ip")
        self._rss_validate_pattern(tvs_mac_rss_l3, command, rss_type = "", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_l4, command, rss_type = "", is_rss = False)

    def test_command_line_option_rss_udp(self):
        command = self.create_testpmd_command(line_option = " --rss-udp")
        self._rss_validate_pattern(tvs_mac_rss_udp, command, rss_type = "", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_ip, command, rss_type = "", is_rss = False)
        self._rss_validate_pattern(tvs_mac_rss_tcp, command, rss_type = "", is_rss = False)
        self._rss_validate_pattern(tvs_mac_rss_sctp, command, rss_type = "", is_rss = False)

    def test_command_line_option_rss_disable(self):
        command = self.create_testpmd_command(line_option = " --disable-rss")
        self._rss_validate_pattern(tvs_mac_rss_all, command, rss_type = "", is_rss = False)

    def test_rss_configure_to_ip(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_l3, command, rss_type = "", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_l4, command, rss_type = "", is_rss = False)

    def test_rss_configure_to_udp(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_udp, command, rss_type = "udp", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_tcp_l4, command, rss_type = "udp", is_rss = False)

    def test_rss_configure_to_tcp(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_tcp, command, rss_type = "tcp", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_udp_l4, command, rss_type = "tcp", is_rss = False)

    def test_rss_configure_to_sctp(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_sctp, command, rss_type = "sctp", is_rss = True)
        self._rss_validate_pattern(tvs_mac_rss_udp_l4, command, rss_type = "sctp", is_rss = False)
        self._rss_validate_pattern(tvs_mac_rss_tcp_l4, command, rss_type = "sctp", is_rss = False)

    def test_rss_configure_to_all(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_all, command, rss_type = "all", is_rss = True)

    def test_rss_configure_to_default(self):
        command = self.create_testpmd_command(line_option = "")
        self._rss_validate_pattern(tvs_mac_rss_all, command, rss_type = "default", is_rss = True)
