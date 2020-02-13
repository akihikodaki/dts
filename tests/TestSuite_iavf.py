# BSD LICENSE
#
# Copyright(c) <2019> Intel Corporation. All rights reserved.
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

Test some iavf function in i40e driver

"""

import re
import time
import math

from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput
from packet import Packet
from settings import get_nic_name
import random
from settings import HEADER_SIZE

VM_CORES_MASK = 'Default'



class TestIavf(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        self.tester.extend_external_packet_generator(TestIavf, self)
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False
        self.interrupt_flag = False
        self.broadcast_mac = "ff:ff:ff:ff:ff:ff"
        self.promiscuous_mac = '00:11:22:33:44:99'
        self.multicast_mac = '01:80:C2:00:00:08'
        self.vf0_mac = "00:12:34:56:78:01"
        self.vf1_mac = "00:12:34:56:78:02"
        self.wrong_mac = '11:22:33:44:55:66'
        self.loading_sizes = [128, 800, 801, 1700, 2500]
        self.ETHER_JUMBO_FRAME_MTU = 9000
        self.tester_intf0 = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[0]))
        self.tester_intf1 = self.tester.get_interface(self.tester.get_local_port(self.dut_ports[1]))

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
        self.dut.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_ADAPTIVE_VF) },/a { RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },' drivers/net/iavf/iavf_ethdev.c", "# ")
        self.dut.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x154C/0x164C/g'  drivers/net/i40e/base/i40e_devids.h", "# ")
        self.dut.build_install_dpdk(self.target)
        self.setup_vm_env()

    def set_up(self):
         pass

    def setup_vm_env(self):
        """
        Create testing environment with 2VF generated from 2PF
        """
        if self.env_done:
            return
        try:
            self.dut.send_expect("rmmod igb_uio", "# ", 60)
            self.dut.send_expect("insmod %s/kmod/igb_uio.ko" % self.target, "# ", 60)
        except Exception as e:
            raise Exception(e)
        self.pf_pci0 = self.dut.ports_info[0]['pci']
        self.pf_pci1 = self.dut.ports_info[1]['pci']

        # bind to default driver
        self.dut.ports_info[0]['port'].bind_driver("igb_uio")
        self.dut.ports_info[1]['port'].bind_driver("igb_uio")
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[0], 1, "igb_uio")
        self.dut.generate_sriov_vfs_by_port(self.dut_ports[1], 1, "igb_uio")
        self.vf0_port = self.dut.ports_info[0]['vfs_port']
        self.vf1_port = self.dut.ports_info[1]['vfs_port']
        self.vf0_port_pci = self.dut.ports_info[0]['sriov_vfs_pci'][0]
        self.vf1_port_pci = self.dut.ports_info[1]['sriov_vfs_pci'][0]

        # start testpmd for pf
        self.dut_testpmd = PmdOutput(self.dut)
        host_eal_param = '-w %s -w %s' % (self.pf_pci0, self.pf_pci1)
        self.dut_testpmd.start_testpmd(
            "Default", "--rxq=4 --txq=4 --port-topology=chained", eal_param=host_eal_param)

        # set vf mac
        self.dut_testpmd.execute_cmd("set vf mac addr 0 0 %s" % self.vf0_mac)
        self.dut_testpmd.execute_cmd("set vf mac addr 1 0 %s" % self.vf1_mac)
        self.used_dut_port_0 = self.dut_ports[0]
        self.used_dut_port_1 = self.dut_ports[1]
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]['vfs_port']
        try:
            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)
            time.sleep(1)
            vf0_prop = {'opt_host': self.sriov_vfs_port_0[0].pci}
            vf1_prop = {'opt_host': self.sriov_vfs_port_1[0].pci}

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'iavf')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm_dut_0.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_ADAPTIVE_VF) },/a { RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },' drivers/net/iavf/iavf_ethdev.c", "# ")
        self.vm_dut_0.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x154C/0x164C/g'  drivers/net/i40e/base/i40e_devids.h", "# ")
        self.vm_dut_0.build_install_dpdk(self.target)
        self.env_done = True

    def bind_nic_driver(self, ports, driver=""):
        # modprobe vfio driver
        if driver == "vfio-pci":
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'vfio-pci':
                    netdev.bind_driver(driver='vfio-pci')
        elif driver == "igb_uio":
            # igb_uio should insmod as default, no need to check
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver = netdev.get_nic_driver()
                if driver != 'igb_uio':
                    netdev.bind_driver(driver='igb_uio')
        else:
            for port in ports:
                netdev = self.dut.ports_info[port]['port']
                driver_now = netdev.get_nic_driver()
                if driver == "":
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    def destroy_vm_env(self):
        self.vm_dut_0.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },/d' drivers/net/iavf/iavf_ethdev.c", "# ")
        self.vm_dut_0.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x164C/0x154C/g' drivers/net/i40e/base/i40e_devids.h", "# ")
        self.vm_dut_0.build_install_dpdk(self.target)
        if getattr(self, 'vm0', None):
            if getattr(self, 'vm_dut_0', None):
                self.vm_dut_0.kill_all()
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
            self.dut.virt_exit()
            self.vm0 = None
        if getattr(self, 'used_dut_port_0', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            port = self.dut.ports_info[self.used_dut_port_0]['port']
            self.used_dut_port_0 = None
        if getattr(self, 'used_dut_port_1', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            port = self.dut.ports_info[self.used_dut_port_1]['port']
            self.used_dut_port_1 = None
        self.bind_nic_driver(self.dut_ports[:2], driver='default')
        self.env_done = False

    def send_packet(self, mac, itf, tran_type='udp',count = 1, pktLength=64, VID=100):
        """
        Sends packets.
        """
        # send packet with different source and dest ip
        if tran_type == "ip":
            for i in range(count):
                packet = r'sendp([Ether(dst="%s", src=get_if_hwaddr("%s"))/IP(src="192.168.0.%d", '\
                                  'dst="192.168.0.%d")], iface="%s")' % (mac, itf, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        if tran_type == "tcp":
            for i in range(count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'\
                                  'TCP(sport=1024,dport=1024)], iface="%s")' % (mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        if tran_type == "ip/udp":
            for i in range(count):
                packet = r'sendp([Ether(dst="%s")/IP()/UDP()/Raw("X"*%s)], iface="%s")' % (mac, pktLength,  itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        if tran_type == "vlan":
            for i in range(count):
                packet = r'sendp(Ether(src="00:00:20:00:00:00", dst="%s")/Dot1Q(id=0x8100,vlan=%s)/IP()/UDP()/'\
                                  'Raw(load="XXXXXXXXXXXXXX"), iface="%s")' % (mac, VID, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "udp":
            for i in range(count):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'\
                                  'UDP(sport=1024,dport=1024)], iface="%s")' % (mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        time.sleep(1)

    def number_of_bytes(self, iface):
        """
        Get the length of loading_sizes
        """
        scanner = ('tcpdump  -vv -r tcpdump_{iface}.pcap 2>/dev/null | grep "seq"  | grep "length"')
        scanner_result = scanner.format(**locals())
        scanner_result = self.tester.send_expect(scanner_result, '#')
        fially_result = re.findall(r'length( \d+)', scanner_result)
        return list(fially_result)

    def number_of_packets(self, iface):
        """
        By reading the file generated by tcpdump it counts how many packets were
        forwarded by the sample app and received in the self.tester. The sample app
        will add a known MAC address for the test to look for.
        """
        command = ('tcpdump -A -nn -e -v -r tcpdump_{iface}.pcap 2>/dev/null | grep -c "seq"')
        command_result = command.format(**locals())
        result = self.tester.send_expect(command_result, '#')
        return int(result.strip())

    def tcpdump_stop_sniff(self):
        """
        Stop the tcpdump process running in the background.
        """
        self.tester.send_expect('killall tcpdump', '#')
        time.sleep(1)
        self.tester.send_expect('echo "Cleaning buffer"', '#')
        time.sleep(1)

    def get_tcpdump_vlan(self):
        command = ('tcpdump -A -nn -e -v -r tcpdump_{0}.pcap 2>/dev/null').format(self.tester_intf0)
        result = self.tester.send_expect(command, '#')
        return result

    def tcpdump_start_sniffing(self, ifaces=[]):
        """
        Start tcpdump in the background to sniff the tester interface where
        the packets are transmitted to and from the self.dut.
        All the captured packets are going to be stored in a file for a
        post-analysis.
        """
        for iface in ifaces:
            command = ('tcpdump -w tcpdump_{0}.pcap -i {0} 2>tcpdump_{0}.out &').format(iface)
            del_cmd = ('rm -f tcpdump_{0}.pcap').format(iface)
            self.tester.send_expect(del_cmd, '#')
            self.tester.send_expect(command, '#')

    def test_vf_basic_rx_tx(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vf_mac = self.vm0_testpmd.get_port_mac(self.vm0_dut_ports[0])
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("start")
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==10, "Not receive expected packet")

    def test_vf_unicast(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("set allmulti all off")
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("start")
        self.send_packet(self.wrong_mac, self.tester_intf1, "ip/udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==0, "Not receive expected packet")

        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==10, "Not receive expected packet")

    def test_vf_multicast(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("set allmulti all off")
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd("start")
        self.send_packet(self.vf0_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output()
        self.verify(self.vf0_mac in out, 'vf receive pkt fail with current mac')
        self.send_packet(self.multicast_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output()
        self.verify(self.multicast_mac not in out, 'vf receive pkt with multicast mac')
        self.vm0_testpmd.execute_cmd("set allmulti all on")
        self.send_packet(self.vf0_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output()
        self.verify(self.vf0_mac in out, 'vf receive pkt fail with current mac')
        self.send_packet(self.multicast_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output(timeout=2)
        self.verify(self.multicast_mac in out, 'vf receive pkt fail with multicast mac')

    def test_vf_broadcast(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("start")
        self.send_packet(self.broadcast_mac, self.tester_intf0, "ip/udp", count=10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==10, "Not receive expected packet")

    def test_vf_promiscuous_mode(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set promisc all on")
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd("start")
        self.send_packet(self.vf0_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output()
        self.verify(self.vf0_mac in out, 'vf receive pkt with current mac')
        self.send_packet(self.promiscuous_mac, self.tester_intf0, "ip/udp")
        out = self.vm_dut_0.get_session_output(timeout=2)
        self.verify(self.promiscuous_mac in out, 'vf receive pkt fail with different mac')

    def test_vf_vlan_filter(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("vlan set filter off 0")
        self.vm0_testpmd.execute_cmd("vlan set filter off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip off 0")
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.vm0_testpmd.execute_cmd("vlan set filter on 0")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("start")

        # send 10 vlan tagged packets, and can't forward the packets
        self.send_packet(self.vf0_mac, self.tester_intf0, "vlan", count = 10, VID=200)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==0, "Not receive expected packet")

        # send 10 untagged packets, and forward the packets
        self.send_packet(self.vf0_mac, self.tester_intf0, "ip/udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets==10, "Not receive expected packet")

    def test_vf_rx_vlan(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("vlan set filter off 0")
        self.vm0_testpmd.execute_cmd("vlan set filter off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip off 0")
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.vm0_testpmd.execute_cmd("vlan set filter on 0")
        self.vm0_testpmd.execute_cmd("rx_vlan add 20 0")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")

        # send 10 vid20 tagged packets, and can forward the packets
        self.send_packet(self.vf0_mac, self.tester_intf0, "vlan", count = 10, pktLength=100, VID=20)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 vid200 tagged packets, and can't forward the packets
        self.send_packet(self.vf0_mac, self.tester_intf0, "vlan", count = 10, pktLength=100, VID=200)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 0, "Not receive expected packet")

        # send 10 udp packets, and can forward the packets
        self.send_packet(self.vf0_mac, self.tester_intf0, "udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

    def test_vf_tx_vlan(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("vlan set filter off 0")
        self.vm0_testpmd.execute_cmd("vlan set filter off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip off 0")
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.vm0_testpmd.execute_cmd("tx_vlan set 1 20")
        self.vm0_testpmd.execute_cmd("tx_vlan set 0 20")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")
        self.tcpdump_start_sniffing([self.tester_intf0])
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp")
        self.tcpdump_stop_sniff()
        out = self.get_tcpdump_vlan()
        self.verify(self.vf0_mac and "vlan 20" in out, 'vlan tag not in out')

    def test_vf_vlan_strip(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set promisc all on")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("vlan set filter off 0")
        self.vm0_testpmd.execute_cmd("vlan set filter off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip off 0")
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip on 1")
        self.vm0_testpmd.execute_cmd("vlan set strip on 0")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")
        self.tcpdump_start_sniffing([self.tester_intf0])
        self.send_packet(self.vf1_mac, self.tester_intf1, "vlan")
        self.tcpdump_stop_sniff()
        out = self.get_tcpdump_vlan()
        self.verify('vlan 100' not in out and self.vf0_mac in out, 'vlan tag in out')

        # disable strip
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.tcpdump_start_sniffing([self.tester_intf0])
        self.send_packet(self.vf1_mac, self.tester_intf1, "vlan")
        self.tcpdump_stop_sniff()
        out = self.get_tcpdump_vlan()
        self.verify("vlan 100" in out and self.vf0_mac in out, 'vlan tag not in out')

    def test_vf_vlan_promisc(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("set promisc all on")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("vlan set filter off 0")
        self.vm0_testpmd.execute_cmd("vlan set filter off 1")
        self.vm0_testpmd.execute_cmd("vlan set strip off 0")
        self.vm0_testpmd.execute_cmd("vlan set strip off 1")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")

        # send 10 tagged packets, and check 10 tagged packets received
        self.send_packet(self.vf1_mac, self.tester_intf1, "vlan", count = 10, VID=100)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 untagged packets, and check 10 untagged packets received
        self.send_packet(self.vf1_mac,self.tester_intf1, "udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

    def test_vf_no_jumbo(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("start")

        # set tester port mtu
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf0, self.ETHER_JUMBO_FRAME_MTU), "# ")
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf1, self.ETHER_JUMBO_FRAME_MTU), "# ")

        # send 10 1518 size  packets, and check 10 packets received
        pktLength = 1518
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=payload)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 1519 size  packets, and check 0 packets received
        pktLength = 1519
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=payload)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 0, "Not receive expected packet")

    def test_vf_normal_jumbo(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--max-pkt-len=3000 --tx-offloads=0x8000")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("set fwd mac")
        self.vm0_testpmd.execute_cmd("start")

        # set tester port mtu
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf0, self.ETHER_JUMBO_FRAME_MTU), "# ")
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf1, self.ETHER_JUMBO_FRAME_MTU), "# ")

        # send 10 1517 size  packets, and check 10 packets received
        pktLength = 1517
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=payload)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 1518 size  packets, and check 10 packets received
        pktLength = 1518
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=payload)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 1519 size  packets, and check 10 packets received
        pktLength = 1519
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=payload)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 4500 size  packets, and check 0 packets received
        pktLength = 4500
        payload = pktLength - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] - HEADER_SIZE['udp']
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp", count = 10, pktLength=4500)
        out = self.vm_dut_0.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 0, "Not receive expected packet")

    def validate_checksum_packet(self):
        normal_checksum_values = {}
        checksum_pattern = re.compile("chksum.*=.*(0x[0-9a-z]+)")
        self.tester.send_expect("scapy", ">>> ")
        for packet in normal_packets:
            self.tester.send_expect("p = %s" % normal_packets[packet], ">>>")
            out = self.tester.send_expect("p.show2()", ">>>")
            chksums = checksum_pattern.findall(out)
            if chksums:
                normal_checksum_values[packet] = chksums
        self.tester.send_expect("exit()", "#")
        for index in normal_checksum_values:
            self.logger.info("Good checksum value for %s Packet is: %s" % (index, normal_checksum_values[index]))

        # Send bad checksum packters and check if the checksum fields are correct.
        corrected_checksum_values = {}
        for packet in checksum_error_packets:
            inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
            self.tester.scapy_foreground()
            self.tester.scapy_append('sendp([%s], iface="%s")' % (checksum_error_packets[packet], self.tester_intf1))
            self.tester.scapy_execute()
            rec_pkt = self.tester.load_tcpdump_sniff_packets(inst)
            # collect checksum values for received packet
            chksum = rec_pkt[0].sprintf("%IP.chksum%;%TCP.chksum%;%UDP.chksum%;%SCTP.chksum%").split(";")
            chksum = list(set(chksum))
            chksum.remove("??")
            corrected_checksum_values[packet] = chksum
        for packet in corrected_checksum_values:
            self.logger.info("Corrected checksum value for %s Packet is: %s" % (packet, corrected_checksum_values[packet]))

        # check if the corrected checksum values are same with the normal packets checksum values
        for packet in normal_packets:
            corrected_checksum_values[packet].sort()
            normal_checksum_values[packet].sort()
            self.verify(corrected_checksum_values[packet] == normal_checksum_values[packet], \
                         "Unexpected Checksum Error For Packet %s" % packet)

    def test_vf_checksum_sw(self):
        global checksum_error_packets
        global normal_packets
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)

        # SW checksum not support SCTP packet SW checksum, DPDK-5886
        checksum_error_packets = {'IP/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x0)/UDP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                'IP/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x0)/TCP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                'IPv6/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="::1")/UDP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                 'IPv6/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="::1")/TCP(chksum=0xf)/("X"*46)' % self.vf1_mac}
        normal_packets = {'IP/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="127.0.0.1")/UDP()/("X"*46)' % self.vf1_mac,
                'IP/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="127.0.0.1")/TCP()/("X"*46)' % self.vf1_mac,
                'IPv6/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="::1")/UDP()/("X"*46)' % self.vf1_mac,
                'IPv6/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="::1")/TCP()/("X"*46)' % self.vf1_mac}
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("csum set ip sw 0")
        self.vm0_testpmd.execute_cmd("csum set udp sw 0")
        self.vm0_testpmd.execute_cmd("csum set tcp sw 0")
        self.vm0_testpmd.execute_cmd("csum set sctp sw 0")
        self.vm0_testpmd.execute_cmd("csum set ip sw 1")
        self.vm0_testpmd.execute_cmd("csum set udp sw 1")
        self.vm0_testpmd.execute_cmd("csum set tcp sw 1")
        self.vm0_testpmd.execute_cmd("csum set sctp sw 1")
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")
        self.validate_checksum_packet()

    def test_vf_checksum_hw(self):
        global checksum_error_packets
        global normal_packets
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        checksum_error_packets = {'IP/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x0)/UDP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                'IP/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x0)/TCP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                'IPv6/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="::1")/UDP(chksum=0xf)/("X"*46)' % self.vf1_mac,
                'IP/SCTP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x0)/SCTP(chksum=0xf)/("X"*48)' % self.vf1_mac,
                'IPv6/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IPv6(src="::1")/TCP(chksum=0xf)/("X"*46)' % self.vf1_mac}
        normal_packets = {'IP/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="127.0.0.1")/UDP()/("X"*46)' % self.vf1_mac,
                'IP/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="127.0.0.1")/TCP()/("X"*46)' % self.vf1_mac,
                'IPv6/UDP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="::1")/UDP()/("X"*46)' % self.vf1_mac,
                'IP/SCTP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IP(src="127.0.0.1")/SCTP()/("X"*48)' % self.vf1_mac,
                'IPv6/TCP': 'Ether(dst="02:00:00:00:00:00", src="%s")/IPv6(src="::1")/TCP()/("X"*46)' % self.vf1_mac}
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("csum set ip hw 0")
        self.vm0_testpmd.execute_cmd("csum set udp hw 0")
        self.vm0_testpmd.execute_cmd("csum set tcp hw 0")
        self.vm0_testpmd.execute_cmd("csum set sctp hw 0")
        self.vm0_testpmd.execute_cmd("csum set ip hw 1")
        self.vm0_testpmd.execute_cmd("csum set udp hw 1")
        self.vm0_testpmd.execute_cmd("csum set tcp hw 1")
        self.vm0_testpmd.execute_cmd("csum set sctp hw 1")
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")
        self.validate_checksum_packet()

    def test_vf_tso(self):
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf0, self.ETHER_JUMBO_FRAME_MTU), "#")
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, " --max-pkt-len=%s " % self.ETHER_JUMBO_FRAME_MTU)
        self.vm0_testpmd.execute_cmd("port stop all")
        self.vm0_testpmd.execute_cmd("csum set ip hw 0")
        self.vm0_testpmd.execute_cmd("csum set udp hw 0")
        self.vm0_testpmd.execute_cmd("csum set tcp hw 0")
        self.vm0_testpmd.execute_cmd("csum set sctp hw 0")
        self.vm0_testpmd.execute_cmd("csum set outer-ip hw 0")
        self.vm0_testpmd.execute_cmd("csum parse-tunnel on 0")
        self.vm0_testpmd.execute_cmd("csum set ip hw 1")
        self.vm0_testpmd.execute_cmd("csum set udp hw 1")
        self.vm0_testpmd.execute_cmd("csum set tcp hw 1")
        self.vm0_testpmd.execute_cmd("csum set sctp hw 1")
        self.vm0_testpmd.execute_cmd("csum set outer-ip hw 1")
        self.vm0_testpmd.execute_cmd("csum parse-tunnel on 1")
        self.vm0_testpmd.execute_cmd("tso set 800 1")
        self.vm0_testpmd.execute_cmd("set fwd csum")
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd("start")
        self.tester.scapy_foreground()
        time.sleep(5)
        for loading_size in self.loading_sizes:
            self.tcpdump_start_sniffing([self.tester_intf0, self.tester_intf1])
            self.tester.scapy_append('sendp([Ether(dst="%s",src="52:00:00:00:00:00")/IP(src="192.168.1.1",dst="192.168.1.2") \
                    /TCP(sport=1021,dport=1021)/("X"*%s)], iface="%s")' % (self.vf0_mac, loading_size, self.tester_intf0))
            self.tester.scapy_execute()
            self.tcpdump_stop_sniff()
            rx_stats = self.number_of_packets(self.tester_intf1)
            tx_stats = self.number_of_packets(self.tester_intf0)
            tx_outlist = self.number_of_bytes(self.tester_intf1)
            self.logger.info(tx_outlist)
            if (loading_size <= 800):
                self.verify(rx_stats == tx_stats and int(tx_outlist[0]) == loading_size, "the packet segmentation incorrect, %s" % tx_outlist)
            else:
                num = loading_size // 800
                for i in range(num):
                    self.verify(tx_outlist != [], "the packet segmentation incorrect, %s" % tx_outlist)
                    self.verify(int(tx_outlist[i]) == 800, "the packet segmentation incorrect, %s" % tx_outlist)
                if loading_size% 800 != 0:
                    self.verify(int(tx_outlist[num]) == loading_size% 800, "the packet segmentation incorrect, %s" % tx_outlist)

    def verify_packet_number(self, out):
        queue0_number = len(re.findall('port 1/queue 0', out))
        queue1_number = len(re.findall('port 1/queue 1', out))
        queue2_number = len(re.findall('port 1/queue 2', out))
        queue3_number = len(re.findall('port 1/queue 3', out))
        queue_numbers = [queue0_number, queue1_number, queue2_number, queue3_number]
        self.verify('queue 0' in out and 'queue 1' in out and 'queue 2' in out and 'queue 3' in out, "some queues can't receive packets when send expected packets")
        self.verify(max(queue_numbers)-min(queue_numbers) <= 3, 'packet number on each queue should be similar')

    def test_vf_rss(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, "--txq=4 --rxq=4")
        self.vm0_testpmd.execute_cmd("set verbose 1")
        for i, j in zip(list(range(64)), [0, 1, 2, 3]*16):
            self.vm0_testpmd.execute_cmd("port config 1 rss reta (%d,%d)" % (i, j))
        pkt_types = ["ip", "tcp", "udp"]
        for pkt_type in pkt_types:
            self.vm0_testpmd.execute_cmd("port config all rss %s" % pkt_type)
            self.vm0_testpmd.execute_cmd("start")
            self.send_packet(self.vf1_mac, self.tester_intf1, pkt_type, count = 30)
            time.sleep(2)
            out = self.vm_dut_0.get_session_output()
            self.verify_packet_number(out)
            self.vm0_testpmd.execute_cmd("clear port stats all")

    def test_vf_rx_interrupt(self):
        # build l3fwd-power
        out = self.vm_dut_0.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        self.vm_dut_0.unbind_interfaces_linux()
        self.vm_dut_0.send_expect("modprobe vfio", "# ", 60)
        self.vm_dut_0.send_expect("modprobe -r vfio_iommu_type1", "# ", 60)
        self.vm_dut_0.send_expect("modprobe  vfio enable_unsafe_noiommu_mode=1", "# ", 60)
        self.vm_dut_0.send_expect("modprobe vfio-pci", "# ", 60)
        self.vm_dut_0.bind_interfaces_linux(driver="vfio-pci")
        # start l3fwd-power
        l3fwd_app = "./examples/l3fwd-power/build/l3fwd-power"
        cmd = l3fwd_app + " -l 0,1 -n 4   -- -p 0x3 --config '(0,0,0),(1,0,1)'"
        self.vm_dut_0.send_expect(cmd, "POWER", timeout=40)
        time.sleep(10)
        self.send_packet(self.vf0_mac, self.tester_intf0, "ip/udp")
        self.send_packet(self.vf1_mac, self.tester_intf1, "ip/udp")
        out = self.vm_dut_0.get_session_output()
        self.verify('L3FWD_POWER: lcore 0 is waked up from rx interrupt' in out, 'lcore 0 is not waked up')
        self.verify('L3FWD_POWER: lcore 1 is waked up from rx interrupt' in out, 'lcore 1 is not waked up')
        self.verify('L3FWD_POWER: lcore 0 sleeps until interrupt triggers' in out, 'lcore 0 not sleep')
        self.verify('L3FWD_POWER: lcore 1 sleeps until interrupt triggers' in out, 'lcore 1 not sleep')
        self.send_packet(self.vf0_mac, self.tester_intf0, "udp", count = 10)
        self.send_packet(self.vf1_mac, self.tester_intf1, "udp", count = 10)
        out = self.vm_dut_0.get_session_output()
        self.verify('L3FWD_POWER: lcore 0 is waked up from rx interrupt' in out, 'lcore 0 is not waked up')
        self.verify('L3FWD_POWER: lcore 1 is waked up from rx interrupt' in out, 'lcore 1 is not waked up')
        self.vm_dut_0.send_expect("^C", "# ", 60)
        self.vm_dut_0.bind_interfaces_linux(driver="igb_uio")
        self.interrupt_flag = True

    def tear_down(self):
        if self.running_case == "test_vf_rx_interrupt":
            self.vm_dut_0.send_expect("^C", "# ", 60)
        else:
            self.vm0_testpmd.quit()

    def tear_down_all(self):
        self.dut.send_expect("quit", "# ")
        if self.env_done is True:
            self.destroy_vm_env()
            self.dut.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },/d' drivers/net/iavf/iavf_ethdev.c", "# ")
            self.dut.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x164C/0x154C/g' drivers/net/i40e/base/i40e_devids.h", "# ")
            self.dut.build_install_dpdk(self.target)
            self.env_done = False
        else:
            pass
