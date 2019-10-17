# BSD LICENSE
#
# Copyright(c) 2019 Intel Corporation. All rights reserved.
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
import re
import os
from test_case import TestCase
from pmd_output import PmdOutput

class TestEnable_Package_Download_In_Ice_Driver(TestCase):

    def set_up_all(self):
        self.verify(self.nic in ["columbiaville_100g", "columbiaville_25g"], "NIC Unsupported: " + str(self.nic))
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.PF_QUEUE = 16

        localPort0 = self.tester.get_local_port(self.dut_ports[0])
        localPort1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_p0 = self.tester.get_interface(localPort0)
        self.tester_p1 = self.tester.get_interface(localPort1)
        self.tester.send_expect("ifconfig %s -promisc" % self.tester_p0, "#")
        self.tester.send_expect("ifconfig %s -promisc" % self.tester_p1, "#")

        self.dut_p0_mac = self.dut.get_mac_address(self.dut_ports[0])
        self.tester_p0_mac = self.tester.get_mac(localPort0)
        self.dut_testpmd = PmdOutput(self.dut)

        self.pkg_file1 = '/lib/firmware/intel/ice/ddp/ice.pkg'
        self.pkg_file2 = '/lib/firmware/updates/intel/ice/ddp/ice.pkg'
        out = self.dut.send_expect("ls %s" % self.pkg_file1, "#")
        self.verify("No such file or directory" not in out, "Cannot find %s, please check you system/driver." % self.pkg_file1)
        out = self.dut.send_expect("ls %s" % self.pkg_file2, "#")
        self.verify("No such file or directory" not in out, "Cannot find %s, please check you system/driver." % self.pkg_file2)
        self.backup_recover_ice_pkg("backup")

    def set_up(self):
        pass

    def backup_recover_ice_pkg(self, flag="backup"):
        """
        if backup == true: backup /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg to /opt/ice.pkg_backup
        else: recover /opt/ice.pkg_backup to /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        """
        backup_file = '/opt/ice.pkg_backup'
        if flag == "backup":
            self.dut.send_expect("\cp %s %s" % (self.pkg_file1, backup_file), "#")
        else:
            self.dut.send_expect("\cp %s %s" % (backup_file, self.pkg_file1), "#")
            self.dut.send_expect("\cp %s %s" % (backup_file, self.pkg_file2), "#")

    def use_correct_ice_pkg(self, flag="true"):
        """
        if flag == true: use correct /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        else: touch a wrong /lib/firmware/intel/ice/ddp/ice.pkg and /lib/firmware/updates/intel/ice/ddp/ice.pkg
        """
        if flag == "true":
            self.backup_recover_ice_pkg("recover")
        else:
            self.dut.send_expect("rm -rf %s" % self.pkg_file1, "#")
            self.dut.send_expect("touch %s" % self.pkg_file1, "#")
            self.dut.send_expect("rm -rf %s" % self.pkg_file2, "#")
            self.dut.send_expect("touch %s" % self.pkg_file2, "#")

    def start_testpmd(self, ice_pkg="true", safe_mode_support="false"):
        self.eal_param = ""
        if safe_mode_support == "true":
            for i in range(len(self.dut_ports)):
                self.eal_param = self.eal_param + "-w %s,safe-mode-support=1 " % self.dut.ports_info[i]['pci']
        out = self.dut_testpmd.start_testpmd("all", "--nb-cores=8 --rxq=%s --txq=%s --port-topology=chained" % (self.PF_QUEUE, self.PF_QUEUE), eal_param=self.eal_param)
        if ice_pkg == "false":
            if safe_mode_support == "true":
                error_messages = ["ice_load_pkg(): failed to allocate buf of size 0 for package", \
                    "ice_dev_init(): Failed to load the DDP package,Entering Safe Mode", \
                    "ice_init_rss(): RSS is not supported in safe mode"]
            if safe_mode_support == "false":
                error_messages = ["ice_load_pkg(): failed to allocate buf of size 0 for package", \
                    "ice_dev_init(): Failed to load the DDP package,Use safe-mode-support=1 to enter Safe Mode"]
            for error_message in error_messages:
                self.verify(error_message in out, "There should be error messages in out: %s" % out)
        self.dut_testpmd.execute_cmd('set promisc all off')
        self.dut_testpmd.execute_cmd('set verbose 1')

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Starts tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """

        for iface in ifaces:
            command = ('tcpdump -w tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &').format(iface)
            del_cmd = ('rm -f tcpdump_{0}.pcap').format(iface)
            self.tester.send_expect(del_cmd, '#')
            self.tester.send_expect(command, '#')

    def tcpdump_stop_sniff(self):
        """
        Stops the tcpdump process running in the background.
        """
        self.tester.send_expect('killall tcpdump', '#')
        time.sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '#')
        time.sleep(1)

    def tcpdump_command(self, command):
        """
        Sends a tcpdump related command and returns an integer from the output
        """
        result = self.tester.send_expect(command, '#')
        print result
        return int(result.strip())

    def number_of_packets(self, iface):
        """
        By reading the file generated by tcpdump it counts how many packets were
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """
        command = ('tcpdump -A -nn -e -v -r tcpdump_{iface}.pcap 2>/dev/null | ' +
                   'grep -c "IPv4"')
        return self.tcpdump_command(command.format(**locals()))

    def tcpdump_scanner(self, scanner):
        """
        Execute scanner to return results
        """
        scanner_result = self.tester.send_expect(scanner, '#')
        fially_result = re.findall(r'length( \d+)', scanner_result)
        return list(fially_result)

    def send_packet(self, tran_type, flag):
        """
        Sends packets.
        """
        self.loading_size = 30
        self.tester.scapy_foreground()
        self.tester.scapy_append('sys.path.append("./")')
        self.tester.scapy_append('from sctp import *')
        if tran_type == "ipv4-other":
            for i in range(1):
                packet = r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/("X"*%s)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.loading_size, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-tcp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-udp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv4-sctp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IP(src="192.168.0.%d", dst="192.168.0.%d")/SCTP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-tcp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d")/TCP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-udp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d")/UDP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "ipv6-sctp":
            for i in range(16):
                packet = r'sendp([Ether(dst="%s", src="%s")/IPv6(src="::%d", dst="::%d",nh=132)/SCTP(sport=1024,dport=1024)], iface="%s")' % (
                    self.dut_p0_mac, self.tester_p0_mac, i + 1, i + 2, self.tester_p0)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        else:
            print "\ntran_type error!\n"

        self.verifyResult(tran_type=tran_type, flag=flag)

    def verifyResult(self, tran_type, flag):
        """
        if flag == true: all packets should enter different queues of port 0
        else: all packets enter queue 0 of port 0
        """
        if tran_type == "ipv4-other":
            self.tcpdump_stop_sniff()
            p0_stats = self.number_of_packets(self.tester_p0)
            p1_stats = self.number_of_packets(self.tester_p1)
            self.verify(p0_stats == p1_stats, "tester p0 and p1: packet number match")
        else:
            out = self.dut.get_session_output()
            queue_list = []
            lines = out.split("\r\n")
            for line in lines:
                line = line.strip()
                if len(line) != 0 and line.startswith(("port 0/queue ",)):
                    for item in line.split(":"):
                        item = item.strip()
                        if(item.startswith("port 0/queue ")):
                            queue_id = item.split(" ", 2)[-1]
                            queue_list.append(queue_id)
            print list(set(queue_list))
            if flag == "true":
                self.verify(len(list(set(queue_list))) > 1, "All packets enter the same queue: %s" % queue_list)
            else:
                self.verify(len(list(set(queue_list))) == 1 and int(list(set(queue_list))[0]) == 0, \
                            "All packets should enter queue 0, but entered %s" % queue_list)

    def download_the_package(self, ice_pkg="true", safe_mode_support="false"):
        """
        if ice_pkg == true: use the correct ice.pkg file; in rxonly mode, all packets should enter different queues of port 0
        else: use wrong ice.pkg
            if safe_mode_support == true, start testpmd with "safe-mode-suppor=1", all packets enter queue 0 of port 0
            else safe_mode_support == false, start testpmd without "safe-mode-suppor", no port is loaded in testpmd
        """
        self.use_correct_ice_pkg(ice_pkg)
        self.start_testpmd(ice_pkg, safe_mode_support)

        self.dut_testpmd.execute_cmd('set fwd mac')
        self.dut_testpmd.execute_cmd('start')
        self.tcpdump_start_sniffing([self.tester_p0, self.tester_p1])
        self.send_packet(tran_type="ipv4-other", flag=ice_pkg)

        self.dut_testpmd.execute_cmd('stop')
        self.dut_testpmd.execute_cmd('set fwd rxonly')
        self.dut_testpmd.execute_cmd('start')
        for tran_types in ["ipv4-tcp", "ipv4-udp", "ipv4-sctp", "ipv6-tcp", "ipv6-udp", "ipv6-sctp"]:
            print tran_types
            self.send_packet(tran_type=tran_types, flag=ice_pkg)

    def test_download_the_package_successfully(self):
        """
        use the correct ice.pkg file; in rxonly mode, all packets should enter different queues of port 0
        """
        self.download_the_package(ice_pkg="true", safe_mode_support="false")

    def test_driver_enters_Safe_Mode_successfully(self):
        """
        use wrong ice.pkg and start testpmd with "safe-mode-suppor=1", all packets enter queue 0 of port 0
        """
        self.download_the_package(ice_pkg="false", safe_mode_support="true")

    def test_driver_enters_Safe_Mode_failed(self):
        """
        use wrong ice.pkg and start testpmd without "safe-mode-suppor", no port is loaded in testpmd
        """
        self.use_correct_ice_pkg(flag="false")
        cmd = "./%s/app/testpmd -c 0x7 -n 4 -- -i --nb-cores=8 --rxq=%s --txq=%s --port-topology=chained" % (self.target, self.PF_QUEUE, self.PF_QUEUE)
        out = self.dut.send_expect(cmd, "#", 60)
        error_messages = ["ice_load_pkg(): failed to allocate buf of size 0 for package", \
                "ice_dev_init(): Failed to load the DDP package,Use safe-mode-support=1 to enter Safe Mode"]
        for error_message in error_messages:
            self.verify(error_message in out, "There should be '%s' in out: %s" % (error_message, out))

    def tear_down(self):
        self.dut_testpmd.quit()

    def tear_down_all(self):
        """
        After test, recover the default ice.pkg
        """
        self.backup_recover_ice_pkg("recover")
