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

import re
import time
import string

import utils
from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput
from utils import RED, GREEN
from net_device import NetDevice
from crb import Crb
from settings import HEADER_SIZE
VM_CORES_MASK = 'all'
DEFAULT_MTU = 1500
TSO_MTU = 9000

class TestVfOffload(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unsupported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

        self.setup_2pf_2vf_1vm_env_flag = 0
        self.setup_2pf_2vf_1vm_env(driver='')
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')
        self.portMask = utils.create_mask([self.vm0_dut_ports[0]])
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0])), TSO_MTU), "# ")

        
    def set_up(self):
        pass

    def setup_2pf_2vf_1vm_env(self, driver='default'):

        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]['vfs_port']

        try:

            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {'opt_host': self.sriov_vfs_port_0[0].pci}
            vf1_prop = {'opt_host': self.sriov_vfs_port_1[0].pci}

            if driver == 'igb_uio':
                # start testpmd without the two VFs on the host
                self.host_testpmd = PmdOutput(self.dut)
                self.host_testpmd.start_testpmd("1S/2C/2T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'vf_offload')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

            self.setup_2pf_2vf_1vm_env_flag = 1
        except Exception as e:
            self.destroy_2pf_2vf_1vm_env()
            raise Exception(e)

    def destroy_2pf_2vf_1vm_env(self):
        if getattr(self, 'vm0', None):
            #destroy testpmd in vm0
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            #destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None

        if getattr(self, 'host_testpmd', None):
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None

        if getattr(self, 'used_dut_port_0', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            port = self.dut.ports_info[self.used_dut_port_0]['port']
            port.bind_driver()
            self.used_dut_port_0 = None

        if getattr(self, 'used_dut_port_1', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            port = self.dut.ports_info[self.used_dut_port_1]['port']
            port.bind_driver()
            self.used_dut_port_1 = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()

        self.setup_2pf_2vf_1vm_env_flag = 0

    def checksum_enablehw(self, port, dut):
        dut.send_expect("port stop all", "testpmd>")
        dut.send_expect("csum set ip hw %d" % port, "testpmd>")
        dut.send_expect("csum set udp hw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp hw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp hw %d" % port, "testpmd>")
        dut.send_expect("port start all", "testpmd>")

    def checksum_enablesw(self, port, dut):
        dut.send_expect("port stop all", "testpmd>")
        dut.send_expect("csum set ip sw %d" % port, "testpmd>")
        dut.send_expect("csum set udp sw %d" % port, "testpmd>")
        dut.send_expect("csum set tcp sw %d" % port, "testpmd>")
        dut.send_expect("csum set sctp sw %d" % port, "testpmd>")
        dut.send_expect("port start all", "testpmd>")

    def checksum_validate(self, packets_sent, packets_expected):
        """
        Validate the checksum.
        """
        tx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        rx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))

        sniff_src = self.vm0_testpmd.get_port_mac(0)
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")

        chksum = dict()
        result = dict()

        self.tester.send_expect("scapy", ">>> ")

        for packet_type in list(packets_expected.keys()):
            self.tester.send_expect("p = %s" % packets_expected[packet_type], ">>>")
            out = self.tester.send_expect("p.show2()", ">>>")
            chksums = checksum_pattern.findall(out)
            chksum[packet_type] = chksums
            print(packet_type, ": ", chksums)

        self.tester.send_expect("exit()", "#")

        self.tester.scapy_background()
        self.tester.scapy_append('p = sniff(filter="ether src %s", iface="%s", count=%d)' % (sniff_src, rx_interface, len(packets_sent)))
        self.tester.scapy_append('nr_packets=len(p)')
        self.tester.scapy_append('reslist = [p[i].sprintf("%IP.chksum%;%TCP.chksum%;%UDP.chksum%;%SCTP.chksum%") for i in range(nr_packets)]')
        self.tester.scapy_append('import string')
        self.tester.scapy_append('RESULT = ",".join(reslist)')

        # Send packet.
        self.tester.scapy_foreground()

        for packet_type in list(packets_sent.keys()):
            self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent[packet_type], tx_interface))

        self.tester.scapy_execute()
        out = self.tester.scapy_get_result()
        packets_received = out.split(',')
        self.verify(len(packets_sent) == len(packets_received), "Unexpected Packets Drop")

        for packet_received in packets_received:
            ip_checksum, tcp_checksum, udp_checksup, sctp_checksum = packet_received.split(';')
            print("ip_checksum: ", ip_checksum, "tcp_checksum:, ", tcp_checksum, "udp_checksup: ", udp_checksup, "sctp_checksum: ", sctp_checksum)

            packet_type = ''
            l4_checksum = ''
            if tcp_checksum != '??':
                packet_type = 'TCP'
                l4_checksum = tcp_checksum
            elif udp_checksup != '??':
                packet_type = 'UDP'
                l4_checksum = udp_checksup
            elif sctp_checksum != '??':
                packet_type = 'SCTP'
                l4_checksum = sctp_checksum

            if ip_checksum != '??':
                packet_type = 'IP/' + packet_type
                if chksum[packet_type] != [ip_checksum, l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"
            else:
                packet_type = 'IPv6/' + packet_type
                if chksum[packet_type] != [l4_checksum]:
                    result[packet_type] = packet_type + " checksum error"

        return result

    def test_checksum_offload_enable(self):
        """
        Enable HW checksum offload.
        Send packet with incorrect checksum,
        can rx it and report the checksum error,
        verify forwarded packets have correct checksum.
        """
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--portmask=%s " %
                                      (self.portMask) + "--enable-rx-cksum " + "" +
                                      "--port-topology=loop")
        self.vm0_testpmd.execute_cmd('set fwd csum')

        time.sleep(2)
        port_id_0 = 0
        mac = self.vm0_testpmd.get_port_mac(0)

        sndIP = '10.0.0.1'
        sndIPv6 = '::1'
        pkts = {'IP/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/UDP(chksum=0xf)/("X"*46)' % (mac, sndIP),
                'IP/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/TCP(chksum=0xf)/("X"*46)' % (mac, sndIP),
                'IP/SCTP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s", chksum=0xf)/SCTP(chksum=0xf)/("X"*48)' % (mac, sndIP),
                'IPv6/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(chksum=0xf)/("X"*46)' % (mac, sndIPv6),
                'IPv6/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/TCP(chksum=0xf)/("X"*46)' % (mac, sndIPv6)}

        expIP = sndIP
        expIPv6 = sndIPv6
        pkts_ref = {'IP/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/UDP()/("X"*46)' % (mac, expIP),
                    'IP/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/TCP()/("X"*46)' % (mac, expIP),
                    'IP/SCTP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/SCTP()/("X"*48)' % (mac, expIP),
                    'IPv6/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/UDP()/("X"*46)' % (mac, expIPv6),
                    'IPv6/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/TCP()/("X"*46)' % (mac, expIPv6)}

        if self.nic in ['redrockcanyou', 'atwood']:
            del pkts['IP/SCTP']
            del pkts_ref['IP/SCTP']

        self.checksum_enablehw(0,self.vm_dut_0)

        self.vm0_testpmd.execute_cmd('start')
        result = self.checksum_validate(pkts, pkts_ref)

        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd('stop')
        bad_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 3, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 5, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    def test_checksum_offload_disable(self):
        """
        Enable SW checksum offload.
        Send same packet with incorrect checksum and verify checksum is valid.
        """

        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--portmask=%s " %
                                      (self.portMask) + "--enable-rx-cksum " +
                                      "--port-topology=loop")
        self.vm0_testpmd.execute_cmd('set fwd csum')

        time.sleep(2)

        mac = self.vm0_testpmd.get_port_mac(0)
        sndIP = '10.0.0.1'
        sndIPv6 = '::1'
        sndPkts = {'IP/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s",chksum=0xf)/UDP(chksum=0xf)/("X"*46)' % (mac, sndIP),
                   'IP/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(src="%s",chksum=0xf)/TCP(chksum=0xf)/("X"*46)' % (mac, sndIP),
                   'IPv6/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/UDP(chksum=0xf)/("X"*46)' % (mac, sndIPv6),
                   'IPv6/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="%s")/TCP(chksum=0xf)/("X"*46)' % (mac, sndIPv6)}

        expIP = sndIP
        expIPv6 = sndIPv6
        expPkts = {'IP/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/UDP()/("X"*46)' % (mac, expIP),
                   'IP/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="%s")/TCP()/("X"*46)' % (mac, expIP),
                   'IPv6/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/UDP()/("X"*46)' % (mac, expIPv6),
                   'IPv6/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="%s")/TCP()/("X"*46)' % (mac, expIPv6)}

        self.checksum_enablesw(0, self.vm_dut_0)

        self.vm0_testpmd.execute_cmd('start')
        result = self.checksum_validate(sndPkts, expPkts)

        # Validate checksum on the receive packet
        out = self.vm0_testpmd.execute_cmd('stop')
        bad_ipcsum = self.vm0_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm0_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 2, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 4, "Bad-l4csum check error")

        self.verify(len(result) == 0, ",".join(list(result.values())))

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Start tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """

        for iface in ifaces:
            command = ('tcpdump -w tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &').format(iface)
            self.tester.send_expect('rm -f tcpdump_{0}.pcap', '#').format(iface)
            self.tester.send_expect(command, '#')

    def tcpdump_stop_sniff(self):
        """
        Stop the tcpdump process running in the background.
        """
        self.tester.send_expect('killall tcpdump', '#')
        time.sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '#')
        time.sleep(1)

    def tcpdump_command(self, command):
        """
        Send a tcpdump related command and return an integer from the output.
        """

        result = self.tester.send_expect(command, '#')
        print(result)
        return int(result.strip())

    def number_of_packets(self, iface):
        """
        By reading the file generated by tcpdump it counts how many packets are
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """

        command = ('tcpdump -A -nn -e -v -r tcpdump_{iface}.pcap 2>/dev/null | ' +
                   'grep -c "seq"')
        return self.tcpdump_command(command.format(**locals()))

    def tcpdump_scanner(self, scanner):
        """
        Execute scanner to return results
        """
        scanner_result = self.tester.send_expect(scanner, '#')
        fially_result = re.findall(r'length( \d+)', scanner_result)
        return list(fially_result)

    def number_of_bytes(self, iface):
        """
        Get the length of loading_sizes
        """
        scanner = ('tcpdump  -vv -r tcpdump_{iface}.pcap 2>/dev/null | grep "seq"  | grep "length"')
        return self.tcpdump_scanner(scanner.format(**locals()))

    def test_tso(self):
        """
        TSO IPv4 TCP, IPv6 TCP testing.
        """
        tx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        rx_interface = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[1]))

        self.loading_sizes = [128, 800, 801, 1700, 2500]

        self.tester.send_expect("ethtool -K %s rx off tx off tso off gso off gro off lro off" % tx_interface, "# ")
        self.tester.send_expect("ip l set %s up" % tx_interface, "# ")
        self.dut.send_expect("ifconfig %s mtu %s" % (self.dut.ports_info[0]['intf'], TSO_MTU), "# ")

        self.portMask = utils.create_mask([self.vm0_dut_ports[0]])
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--portmask=0x3 "  + "--enable-rx-cksum " + "--max-pkt-len=%s" % TSO_MTU)

        mac = self.vm0_testpmd.get_port_mac(0)

        self.vm0_testpmd.execute_cmd("set verbose 1", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("port stop all", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set udp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set tcp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set sctp hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set outer-ip hw %d" % self.dut_ports[0], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum parse-tunnel on %d" % self.dut_ports[0], "testpmd> ", 120)

        self.vm0_testpmd.execute_cmd("csum set ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set udp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set tcp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set sctp hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum set outer-ip hw %d" % self.dut_ports[1], "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("csum parse-tunnel on %d" % self.dut_ports[1], "testpmd> ", 120)

        self.vm0_testpmd.execute_cmd("tso set 800 %d" % self.vm0_dut_ports[1])
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("port start all", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("set promisc all off", "testpmd> ", 120)
        self.vm0_testpmd.execute_cmd("start")

        self.tester.scapy_foreground()
        time.sleep(5)

        for loading_size in self.loading_sizes:
            # IPv4 tcp test
            out = self.vm0_testpmd.execute_cmd("clear port info all", "testpmd> ", 120)
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            self.tester.scapy_append('sendp([Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.vm0_testpmd.execute_cmd("show port stats all")
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "IPV4 RX or TX packet number not correct")
            else:
                num = loading_size // 800
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)

        for loading_size in self.loading_sizes:
            # IPv6 tcp test
            out = self.vm0_testpmd.execute_cmd("clear port info all", "testpmd> ", 120)
            self.tcpdump_start_sniffing([tx_interface, rx_interface])
            self.tester.scapy_append('sendp([Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="FE80:0:0:0:200:1FF:FE00:200", dst="3555:5555:6666:6666:7777:7777:8888:8888")/TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (mac, loading_size, tx_interface))
            out = self.tester.scapy_execute()
            out = self.vm0_testpmd.execute_cmd("show port stats all")
            print(out)
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(rx_interface)
            tx_stats = self.number_of_packets(tx_interface)
            tx_outlist = self.number_of_bytes(rx_interface)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "IPV6 RX or TX packet number not correct")
            else:
                num = loading_size // 800
                for i in range(num):
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)

    def tear_down(self):
        self.vm0_testpmd.execute_cmd('quit', '# ')
        self.dut.send_expect("ifconfig %s mtu %s" % (self.dut.ports_info[0]['intf'], DEFAULT_MTU), "# ")

    def tear_down_all(self):
        print("tear_down_all")
        if self.setup_2pf_2vf_1vm_env_flag == 1:
            self.destroy_2pf_2vf_1vm_env()
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0])), DEFAULT_MTU), "# ")
