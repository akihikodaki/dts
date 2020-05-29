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

Test some vf function in ice driver

"""

import re
import time
import random
import utils
from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput
from settings import HEADER_SIZE
from packet import Packet
from utils import RED

VM_CORES_MASK = 'all'
MAX_VLAN = 4095
ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestKernelpfIavf(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):
        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 2, "Insufficient ports")
        self.vm0 = None
        self.env_done = False
        self.interrupt_flag = False
        self.vf_mac = '00:01:23:45:67:89'
        self.add_addr = '00:11:22:33:44:55'
        self.wrong_mac = '00:11:22:33:44:99'

        self.port = self.dut_ports[0]
        self.vm_port = 0
        cores = self.dut.get_core_list("1S/1C/1T")
        self.port_mask = utils.create_mask([self.port])

        # set vf assign method and vf driver
        self.dut.send_expect('modprobe vfio-pci', '#')
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')
        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]['intf']
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        self.tester_mac = self.tester.get_mac(tester_port)

        tester_port1 = self.tester.get_local_port(self.dut_ports[1])
        self.tester_intf1 = self.tester.get_interface(tester_port1)

    def set_up(self):

        if self.running_case == "test_vf_mac_filter":
            self.destroy_vm_env()
            if self.env_done is False:
                self.setup_vm_env(driver='', set_vf_mac=False)
        elif self.running_case == "test_vf_rx_interrupt":
            self.destroy_vm_env()
        elif self.env_done is False:
            self.setup_vm_env()

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
                if driver is None:
                    driver = netdev.default_driver
                if driver != driver_now:
                    netdev.bind_driver(driver=driver)

    def setup_vm_env(self, driver='default', set_vf_mac=True):
        """
        Create testing environment with 1VF generated from 1PF
        """
        if self.env_done:
            return

        # bind to default driver
        self.bind_nic_driver(self.dut_ports, driver="")
        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 1, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        out = self.dut.send_expect('ethtool %s' % self.host_intf, '#')
        self.speed = re.findall('Speed: (\d*)', out)[0]
        if self.nic.startswith('columbiaville'):
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" %(self.host_intf), "# ")
        if self.running_case == "test_vf_multicast":
            self.dut.send_expect("ethtool --set-priv-flags %s vf-true-promisc-support on" %(self.host_intf), "# ")
        if set_vf_mac is True:
            self.vf_mac = "00:01:23:45:67:89"
            self.dut.send_expect("ip link set %s vf 0 mac %s" %
                                 (self.host_intf, self.vf_mac), "# ")

        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf_popt = {'opt_host': self.sriov_vfs_port[0].pci}

            # set up VM ENV
            self.vm = VM(self.dut, 'vm0', 'kernelpf_iavf')
            self.vm.set_vm_device(driver=self.vf_assign_method, **vf_popt)
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed!")

            self.vm_testpmd = PmdOutput(self.vm_dut)
        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)
        netdev = self.dut.ports_info[0]['port']
        nic_drive = netdev.get_nic_driver()
        if nic_drive == "i40e":
            self.vm_dut.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_ADAPTIVE_VF) },/a { RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },' drivers/net/iavf/iavf_ethdev.c", "# ")
            self.vm_dut.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x154C/0x164C/g'  drivers/net/i40e/base/i40e_devids.h", "# ")
            self.vm_dut.build_install_dpdk(self.target)
        self.env_done = True

    def destroy_vm_env(self):
        netdev = self.dut.ports_info[0]['port']
        nic_drive = netdev.get_nic_driver()
        if nic_drive == "i40e":
            self.vm_dut.send_expect("sed -i '/{ RTE_PCI_DEVICE(IAVF_INTEL_VENDOR_ID, IAVF_DEV_ID_VF) },/d' drivers/net/iavf/iavf_ethdev.c", "# ")
            self.vm_dut.send_expect("sed -i -e '/I40E_DEV_ID_VF/s/0x164C/0x154C/g' drivers/net/i40e/base/i40e_devids.h", "# ")
            self.vm_dut.build_install_dpdk(self.target)
        if getattr(self, 'vm', None):
            if getattr(self, 'vm_dut', None):
                self.vm_dut.kill_all()
            self.vm_testpmd = None
            self.vm_dut_ports = None
            # destroy vm0
            self.vm.stop()
            self.dut.virt_exit()
            time.sleep(3)
            self.vm = None

        if getattr(self, 'used_dut_port', None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None

        self.bind_nic_driver(self.dut_ports, driver='default')

        self.env_done = False

    def jumboframes_get_stat(self, portid, rx_tx):
        """
        Get packets number from port statistic
        """
        stats = self.vm_testpmd.get_pmd_stats(portid)
        if rx_tx == "rx":
            return [stats['RX-packets'], stats['RX-errors'], stats['RX-bytes']]
        elif rx_tx == "tx":
            return [stats['TX-packets'], stats['TX-errors'], stats['TX-bytes']]
        else:
            return None

    def send_random_pkt(self, dts, count=1):
        tgen_ports = []
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])
        tgen_ports.append((tx_port, rx_port))
        src_mac = self.tester.get_mac(tx_port)
        dst_mac = dts
        pkt_param = [("ether", {'dst': dst_mac, 'src': src_mac})]
        result = self.tester.check_random_pkts(tgen_ports, pktnum=count, allow_miss=False, params=pkt_param)
        return result

    def test_vf_basic_rxtx(self):
        '''
        Set rxonly forward,Send 100 random packets from tester, check packets can be received
        '''
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd rxonly")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        time.sleep(1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, "vf receive packet fail")
        stats = self.vm_testpmd.get_pmd_stats(0)
        self.verify(stats['RX-packets'] >= 100, 'vf receive packet num is not match')
        '''
        Set txonly forward,check packets can be received by tester
        '''
        self.vm_testpmd.execute_cmd("stop")
        self.vm_testpmd.execute_cmd("set fwd txonly")
        self.tester.send_expect('rm -f tcpdump.pcap', '#')
        self.tester.send_expect("tcpdump -i %s 2>tcpdump.out &" % self.tester_intf, "#")
        self.vm_testpmd.execute_cmd("start")
        time.sleep(1)
        self.vm_testpmd.execute_cmd("stop")
        self.tester.send_expect('killall tcpdump', '#')
        time.sleep(1)
        cap_packet = self.tester.send_expect('cat tcpdump.out', '#', 30)
        stats = self.vm_testpmd.get_pmd_stats(0)
        cap_tcp_num = re.findall('(\d+) packets', cap_packet)
        nums = sum(map(int,cap_tcp_num))
        self.verify(stats['TX-packets'] !=0 and nums > 0, 'vf send packet num is not match')

    def test_vf_mac_filter(self):
        """
        Not set VF MAC from kernel PF for this case, if set, will print
        "not permitted error" when add new MAC for VF.
        """
        out = self.vm_testpmd.start_testpmd("all")
        self.testpmd_mac = self.get_testpmd_vf_mac(out)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("mac_addr add 0 %s" % self.add_addr)
        self.vm_testpmd.execute_cmd("start")
        # send packet with current mac
        self.send_random_pkt(self.testpmd_mac, count=100)
        self.verify_packet_count(100)
        self.vm_testpmd.execute_cmd('clear port stats all')
        # send packet with add mac
        self.send_random_pkt(self.add_addr, count=100)
        self.verify_packet_count(100)
        self.vm_testpmd.execute_cmd('clear port stats all')
        # send packet with wrong mac
        self.send_random_pkt(self.wrong_mac, count=100)
        self.verify_packet_count(0)

    def get_testpmd_vf_mac(self, out):
        result = re.search("([a-f0-9]{2}:){5}[a-f0-9]{2}", out, re.IGNORECASE)
        mac = result.group()
        return mac

    def verify_packet_count(self, count):

        pmd0_vf0_stats = self.vm_testpmd.get_pmd_stats(0)
        vf0_rx_cnt = pmd0_vf0_stats['RX-packets']
        vf0_tx_cnt = pmd0_vf0_stats['TX-packets']
        self.verify(vf0_rx_cnt == vf0_tx_cnt == count, "vf receive packet count not match!")

    def test_vf_promisc_mode(self):
        """
        Enable kernel trust mode
        """
        self.dut.send_expect("ip link set dev %s vf 0 trust on" % self.host_intf, "# ")
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, 'vf receive pkt fail with current mac')
        # send packet with wrong mac, vf can receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac in out, 'vf receive pkt fail with wrong mac')

        self.vm_testpmd.execute_cmd("set promisc all off")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, 'vf receive pkt fail with current mac')
        # send packet with wrong mac, vf can not receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac not in out, 'vf receive pkt with wrong mac')

        self.vm_testpmd.execute_cmd("set promisc all on")
        # send packet with current mac, vf can receive and forward packet
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, 'vf receive pkt fail with current mac')
        # send packet with wrong mac, vf can receive and forward packet
        self.send_random_pkt(self.wrong_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.wrong_mac in out, 'vf receive pkt fail with wrong mac')

        self.dut.send_expect("ip link set dev %s vf 0 trust off" % self.host_intf, "# ")

    def test_vf_multicast(self):
        """
        enable kernel trust mode
        """
        multicast_mac = '01:80:C2:00:00:08'
        self.dut.send_expect("ip link set dev %s vf 0 trust on" % self.host_intf, "# ")
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set allmulti all off")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, 'vf receive pkt fail with current mac')
        self.send_random_pkt(multicast_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(multicast_mac not in out, 'vf receive pkt with multicast mac')

        self.vm_testpmd.execute_cmd("set allmulti all on")
        self.send_random_pkt(self.vf_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(self.vf_mac in out, 'vf receive pkt fail with current mac')
        self.send_random_pkt(multicast_mac, count=1)
        out = self.vm_dut.get_session_output()
        self.verify(multicast_mac in out, 'vf receive pkt fail with multicast mac')
        self.dut.send_expect("ip link set dev %s vf 0 trust off" % self.host_intf, "# ")

    def test_vf_broadcast(self):
        """
        """
        broadcast_mac = 'ff:ff:ff:ff:ff:ff'
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(broadcast_mac, count=1)
        time.sleep(1)
        out = self.vm_dut.get_session_output()
        print(out)
        self.verify(broadcast_mac.upper() in out and self.tester_mac.upper() in out, 'vf receive pkt fail with broadcast mac')

    def test_vf_add_pvid(self):
        '''
        vf can receive packet with right vlan id, can't receive wrong vlan id packet
        '''
        random_vlan = random.randint(1, MAX_VLAN)
        self.dut.send_expect("ip link set %s vf 0 vlan %s" % (self.host_intf, random_vlan), "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf, "# ")
        self.verify("vlan %d" % random_vlan in out, "Failed to add pvid on VF0")

        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        self.verify(self.vf_mac in out, "testpmd can't receive packet")
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 2, 'Failed to received vlan packet!!!')
        wrong_vlan = (random_vlan + 1) % 4096
        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(vlan=wrong_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        self.verify(self.vf_mac not in out, 'received wrong vlan packet!!!')
        receive_pkt = re.findall('vlan %s' % wrong_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 1, "tester received wrong vlan packet!!!")

        # remove vlan
        self.vm_testpmd.execute_cmd("stop")
        self.vm_testpmd.execute_cmd("port stop all")
        self.dut.send_expect("ip link set %s vf 0 vlan 0" % self.host_intf, "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf, "# ")
        self.verify("vlan %d" % random_vlan not in out, "Failed to remove pvid on VF0")
        # send packet without vlan
        self.vm_testpmd.execute_cmd("port reset 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")
        out = self.send_and_getout(vlan=0, pkt_type="UDP")
        self.verify(self.vf_mac in out, "Not received packet without vlan!!!")

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify(
            self.vf_mac in out, "Not recevied packet with vlan 0!!!")

        # send random vlan packet
        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 2, "fail to tester received vlan packet!!!")
        self.verify(self.vf_mac in out, "Failed to received vlan packet!!!")

    def send_and_getout(self, vlan=0, pkt_type="UDP"):

        if pkt_type == "UDP":
            pkt = Packet(pkt_type='UDP')
            pkt.config_layer('ether', {'dst': self.vf_mac})
        elif pkt_type == "VLAN_UDP":
            pkt = Packet(pkt_type='VLAN_UDP')
            pkt.config_layer('vlan', {'vlan': vlan})
            pkt.config_layer('ether', {'dst': self.vf_mac})

        pkt.send_pkt(self.tester, tx_port=self.tester_intf)
        out = self.vm_dut.get_session_output(timeout=2)

        return out

    def test_vf_vlan_rx(self):
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd rxonly")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("vlan set strip on 0")
        self.vm_testpmd.execute_cmd("start")
        # send packet without vlan, vf can receive packet
        out = self.send_and_getout(pkt_type="UDP")
        self.verify(self.vf_mac in out, "Failed to received without vlan packet!!!")

        # send packet vlan 0, vf can receive packet
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify(self.vf_mac in out, "Failed to received vlan 0 packet!!!")

        self.vm_testpmd.execute_cmd("rx_vlan add 1 0")

        # send packet vlan 1, vf can receive packet
        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(vlan=1, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan 1', tcpdump_out)
        self.verify(len(receive_pkt) == 1 , 'Failed to received vlan packet!!!')
        self.verify(self.vf_mac in out, "Failed to received vlan 1 packet!!!")

        # send random vlan packet, vf can not receive packet
        random_vlan = random.randint(1, MAX_VLAN)
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        self.verify(self.vf_mac not in out, 'fail to vf receive pkt')

        # send max vlan 4095, vf can not receive packet
        out = self.send_and_getout(vlan=MAX_VLAN, pkt_type="VLAN_UDP")
        self.verify(self.vf_mac not in out, "received max vlan packet!!!")

        # remove vlan
        self.vm_testpmd.execute_cmd("rx_vlan rm 1 0")

        # send packet without vlan, vf can receive packet
        out = self.send_and_getout(pkt_type="UDP")
        self.verify(self.vf_mac in out, "Failed to received without vlan packet!!!")

        # send packet vlan 0, vf can receive packet
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify(self.vf_mac in out, "Failed to received vlan 0 packet!!!")

        # send vlan 1 packet, vf can receive packet
        out = self.send_and_getout(vlan=1, pkt_type="VLAN_UDP")
        self.verify(self.vf_mac in out, "received vlan 1 packet!!!")

    def test_vf_vlan_insertion(self):
        self.vm_testpmd.start_testpmd("all")
        random_vlan = random.randint(1, MAX_VLAN)
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("tx_vlan set 0 %s" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("rx_vlan add %s 0" % random_vlan)
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")

        self.start_tcpdump(self.tester_intf)
        out = self.send_and_getout(pkt_type="UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        print(out)
        self.verify(len(receive_pkt) == 1, 'Failed to received vlan packet!!!')

    def test_vf_vlan_strip(self):
        random_vlan = random.randint(1, MAX_VLAN)
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("vlan set filter off 0")
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("vlan set strip on 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 1, 'Failed to received vlan packet!!!')

        # disable strip
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 2, 'Failed to not received vlan packet!!!')

    def test_vf_vlan_filter(self):
        random_vlan = random.randint(2, MAX_VLAN)
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("vlan set filter on 0")
        self.vm_testpmd.execute_cmd("rx_vlan add %d 0" % random_vlan) 
        self.vm_testpmd.execute_cmd("vlan set strip on 0")
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")

        # error vlan id
        out = self.send_and_getout(vlan=random_vlan - 1, pkt_type="VLAN_UDP")
        receive_pkt = re.findall('received 1 packets', out)
        self.verify(len(receive_pkt) == 0, 'Failed error received vlan packet!')

        # passed vlan id
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        receive_pkt = re.findall('received 1 packets', out)
        self.verify(len(receive_pkt) == 1, 'Failed pass received vlan packet!')

        # disable filter
        self.vm_testpmd.execute_cmd("rx_vlan rm %d 0" % random_vlan)
        self.vm_testpmd.execute_cmd("vlan set filter off 0")
        self.start_tcpdump(self.tester_intf)
        self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        time.sleep(1)
        tcpdump_out = self.get_tcpdump_package()
        receive_pkt = re.findall('vlan %s' % random_vlan, tcpdump_out)
        self.verify(len(receive_pkt) == 2, 'Failed to received vlan packet!!!')

    def test_vf_without_jumboframe(self):
        self.tester.send_expect('ifconfig %s mtu %s' % (self.tester_intf, ETHER_JUMBO_FRAME_MTU), '#')

        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("start")
        self.jumboframes_send_packet(ETHER_STANDARD_MTU - 1, True)
        self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1, False)
        self.tester.send_expect("ifconfig %s mtu %s" % (self.tester_intf, ETHER_STANDARD_MTU), "#")

    def test_vf_with_jumboframe(self):
        self.tester.send_expect('ifconfig %s mtu %d' % (self.tester_intf, ETHER_JUMBO_FRAME_MTU), '#')
        conf_pkt_len = 3000
        self.vm_testpmd.start_testpmd("all", "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000" % conf_pkt_len)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("start")
        self.jumboframes_send_packet(conf_pkt_len - 1, True)
        self.jumboframes_send_packet(conf_pkt_len + 1, False)
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf, ETHER_STANDARD_MTU), "#")

    def jumboframes_send_packet(self, pktsize, received=True):
        """
        Send 1 packet to portid
        """
        tx_pkts_ori, _, tx_bytes_ori = [int(_) for _ in self.jumboframes_get_stat(self.vm_port, "tx")]
        rx_pkts_ori, rx_err_ori, rx_bytes_ori = [int(_) for _ in self.jumboframes_get_stat(self.vm_port, "rx")]

        pkt = Packet(pkt_type='UDP', pkt_len=pktsize)
        pkt.config_layer('ether', {'dst': self.vf_mac, 'src': self.tester_mac})
        self.vm_testpmd.execute_cmd("clear port stats all")
        pkt.send_pkt(self.tester, tx_port=self.tester_intf)

        time.sleep(1)

        tx_pkts, _, tx_bytes = [int(_) for _ in self.jumboframes_get_stat(self.port, "tx")]
        rx_pkts, rx_err, rx_bytes = [int(_) for _ in self.jumboframes_get_stat(self.vm_port, "rx")]

        tx_pkts -= tx_pkts_ori
        tx_bytes -= tx_bytes_ori
        rx_pkts -= rx_pkts_ori
        rx_bytes -= rx_bytes_ori
        rx_err -= rx_err_ori
        if received:
            self.verify((rx_pkts == 1) and (tx_pkts == 1), "Packet forward assert error")

            self.verify(rx_bytes + 4 == pktsize, "Rx packet size should be packet size")

            self.verify(tx_bytes + 4 == pktsize, "Tx packet size should be packet size")
        else:
            self.verify(rx_err == 1 or tx_pkts == -1, "Packet drop assert error")

    def test_vf_rss(self):
        self.vm_testpmd.start_testpmd("all", "--txq=4 --rxq=4")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        for i, j in zip(list(range(64)), [0, 1, 2, 3]*16):
            self.vm_testpmd.execute_cmd("port config 0 rss reta (%d,%d)" % (i, j))
        self.vm_testpmd.execute_cmd("port config all rss ip")
        self.vm_testpmd.execute_cmd("port config all rss tcp")
        self.vm_testpmd.execute_cmd("port config all rss udp")
        self.vm_testpmd.execute_cmd("start")
        self.send_packet(self.tester_intf, 'IPV4')
        time.sleep(2)
        out = self.vm_dut.get_session_output()
        self.verify_packet_number(out)

        self.vm_testpmd.execute_cmd("clear port stats all")
        self.send_packet(self.tester_intf, 'IPV4&TCP')
        time.sleep(2)
        out = self.vm_dut.get_session_output()
        self.verify_packet_number(out)

        self.vm_testpmd.execute_cmd("clear port stats all")
        self.send_packet(self.tester_intf, 'IPV4&UDP')
        time.sleep(2)
        out = self.vm_dut.get_session_output()
        self.verify_packet_number(out)

    def verify_packet_number(self, out):
        queue0_number = len(re.findall('port 0/queue 0', out))
        queue1_number = len(re.findall('port 0/queue 1', out))
        queue2_number = len(re.findall('port 0/queue 2', out))
        queue3_number = len(re.findall('port 0/queue 3', out))
        queue_numbers = [queue0_number, queue1_number, queue2_number, queue3_number]
        self.verify('queue 0' in out and 'queue 1' in out and 'queue 2' in out and 'queue 3' in out, "some queue can't receive packet when send ip packet")
        self.verify(max(queue_numbers)-min(queue_numbers) <= 3, 'packet number on each queue should be similar')

    def send_packet(self, itf, tran_type):
        """
        Sends packets.
        """
        mac = self.vf_mac
        # send packet with different source and dest ip
        if tran_type == "IPV4":
            for i in range(30):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", '\
                                  'dst="192.168.0.%d")], iface="%s")' % (mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "IPV4&TCP":
            for i in range(30):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'\
                                  'TCP(sport=1024,dport=1024)], iface="%s")' % (mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        elif tran_type == "IPV4&UDP":
            for i in range(30):
                packet = r'sendp([Ether(dst="%s", src="02:00:00:00:00:00")/IP(src="192.168.0.%d", dst="192.168.0.%d")/'\
                                  'UDP(sport=1024,dport=1024)], iface="%s")' % (mac, i + 1, i + 2, itf)
                self.tester.scapy_append(packet)
            self.tester.scapy_execute()
            time.sleep(.5)
        self.tester.scapy_execute()
        time.sleep(1)

    def enable_hw_checksum(self):
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("csum set ip hw 0")
        self.vm_testpmd.execute_cmd("csum set udp hw 0")
        self.vm_testpmd.execute_cmd("csum set tcp hw 0")
        self.vm_testpmd.execute_cmd("csum set sctp hw 0")
        self.vm_testpmd.execute_cmd("set fwd csum")
        self.vm_testpmd.execute_cmd("set verbose 1")

    def enable_sw_checksum(self):
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("csum set ip sw 0")
        self.vm_testpmd.execute_cmd("csum set udp sw 0")
        self.vm_testpmd.execute_cmd("csum set tcp sw 0")
        self.vm_testpmd.execute_cmd("csum set sctp sw 0")
        self.vm_testpmd.execute_cmd("set fwd csum")
        self.vm_testpmd.execute_cmd("set verbose 1")

    def checksum_verify(self):
        packets_sent = {'IP/': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP(chksum=0x1234)/UDP()/("X"*46)' % self.vf_mac,
                        'IP/UDP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP()/UDP(chksum=0x1234)/("X"*46)' % self.vf_mac,
                        'IP/TCP': 'Ether(dst="%s", src="52:00:00:00:00:00")/IP()/TCP(chksum=0x1234)/("X"*46)' % self.vf_mac}

        # Send packet.
        self.tester.scapy_foreground()

        for packet_type in list(packets_sent.keys()):
            self.tester.scapy_append('sendp([%s], iface="%s")' % (packets_sent[packet_type], self.tester_intf))
            self.start_tcpdump(self.tester_intf)
            self.tester.scapy_execute()
            time.sleep(1)
            tcpdump_out = self.get_tcpdump_package()
            if packet_type == 'IP/UDP':
                # verify udp checksum
                self.verify('bad udp cksum' in tcpdump_out and 'udp sum ok' in tcpdump_out, 'udp checksum verify fail')
            elif packet_type == 'IP/TCP':
                # verify tcp checksum
                self.verify("cksum 0x1234 (incorrect" in tcpdump_out and 'correct' in tcpdump_out, 'tcp checksum verify fail')
            else:
                # verify ip checksum
                self.verify('bad cksum 1234' in tcpdump_out and 'udp sum ok' in tcpdump_out, 'ip checksum verify fail')
        out = self.vm_testpmd.execute_cmd("stop")
        bad_ipcsum = self.vm_testpmd.get_pmd_value("Bad-ipcsum:", out)
        bad_l4csum = self.vm_testpmd.get_pmd_value("Bad-l4csum:", out)
        self.verify(bad_ipcsum == 1, "Bad-ipcsum check error")
        self.verify(bad_l4csum == 2, "Bad-ipcsum check error")

    def test_vf_hw_checksum_offload(self):
        self.vm_testpmd.start_testpmd("all")
        self.enable_hw_checksum()
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.checksum_verify()

    def test_vf_sw_checksum_offload(self):
        self.vm_testpmd.start_testpmd("all")
        self.enable_sw_checksum()
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")
        self.checksum_verify()

    def test_vf_tso(self):
        self.tester.send_expect("ethtool -K %s rx off tx off tso off gso off gro off lro off" % self.tester_intf, "#")
        self.tester.send_expect("ifconfig %s mtu %d" % (self.tester_intf, ETHER_JUMBO_FRAME_MTU), "#")
        self.vm_testpmd.start_testpmd("all", "--port-topology=chained --max-pkt-len=%d" % ETHER_JUMBO_FRAME_MTU)
        self.vm_testpmd.execute_cmd("set fwd csum")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.enable_hw_checksum()
        self.vm_testpmd.execute_cmd("tso set 1460 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")
        self.tester.scapy_foreground()
        time.sleep(5)
        self.start_tcpdump(self.tester_intf)
        pkt = 'sendp([Ether(dst="%s")/IP(chksum=0x1234)/TCP(flags=0x10,chksum=0x1234)/'\
                      'Raw(RandString(5214))], iface="%s")' % (self.vf_mac, self.tester_intf)
        self.tester.scapy_append(pkt)
        self.tester.scapy_execute()
        time.sleep(5)
        out = self.get_tcpdump_package()
        self.verify_packet_segmentation(out)
        self.vm_testpmd.execute_cmd("stop")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("tso set 0 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")

        self.start_tcpdump(self.tester_intf)
        self.tester.scapy_append(pkt)
        self.tester.scapy_execute()
        time.sleep(5)
        out = self.get_tcpdump_package()
        self.verify_packet_segmentation(out, seg=False)

    def start_tcpdump(self, rxItf):
        self.tester.send_expect("rm -rf getPackageByTcpdump.cap", "#")
        self.tester.send_expect("tcpdump -A -nn -e -vv -w getPackageByTcpdump.cap -i %s 2> /dev/null& " % rxItf, "#")
        time.sleep(2)

    def get_tcpdump_package(self):
        time.sleep(1)
        self.tester.send_expect("killall tcpdump", "#")
        return self.tester.send_expect("tcpdump -A -nn -e -vv -r getPackageByTcpdump.cap", "#")

    def verify_packet_segmentation(self, out, seg=True):
        if seg:
            number1 = re.findall('length 1460: HTTP', out)
            number2 = re.findall('length 834: HTTP', out)
            self.verify(len(number1) == 3 and len(number2) == 1, 'packet has no segment')
        else:
            self.verify('length 1460: HTTP' not in out, 'packet has segment')
            # tester send packet with incorrect checksum
            # vf fwd packet with corrent checksum
            self.verify('incorrect' in out and 'correct' in out, 'checksum has incorrect')
        self.tester.send_expect("^C", "#")

    def test_vf_port_start_stop(self):
        self.vm_testpmd.start_testpmd("all")
        for i in range(10):
            self.vm_testpmd.execute_cmd("port stop all")
            self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        port_id_0 = 0
        vf0_stats = self.vm_testpmd.get_pmd_stats(port_id_0)
        vf0_rx_cnt = vf0_stats['RX-packets']
        self.verify(vf0_rx_cnt == 100, "no packet was received by vm0_VF0")

        vf0_rx_err = vf0_stats['RX-errors']
        self.verify(vf0_rx_err == 0, "vm0_VF0 rx-errors")

        vf0_tx_cnt = vf0_stats['TX-packets']
        self.verify(vf0_tx_cnt == 100, "no packet was fwd by vm0_VF0")

    def test_vf_statistic_reset(self):
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify("RX-packets: 0" in out and "TX-packets: 0" in out, "receive some misc packet")
        self.vm_testpmd.execute_cmd("clear port stats all")
        self.send_random_pkt(self.vf_mac, count=100)
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify("RX-packets: 100" in out and "TX-packets: 100" in out, "receive packet fail")
        self.vm_testpmd.execute_cmd("clear port stats all")
        out = self.vm_testpmd.execute_cmd("show port stats all")
        self.verify("RX-packets: 0" in out and "TX-packets: 0" in out, "clear port stats fail")

    def test_vf_information(self):
        self.vm_testpmd.start_testpmd("all")
        out = self.vm_testpmd.execute_cmd("show port info 0")
        self.verify('Link status: up' in out, 'link stats has error')
        self.verify('Link speed: %s' % self.speed in out, 'link speed has error')
        print(out)
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("start")
        self.send_random_pkt(self.vf_mac, count=100)
        out = self.vm_testpmd.execute_cmd("show port stats all")
        print(out)
        self.verify("RX-packets: 100" in out and "TX-packets: 100" in out, "receive packet fail")

    def test_vf_rx_interrupt(self):
        # build l3-power
        out = self.dut.build_dpdk_apps("./examples/l3fwd-power")
        self.verify("Error" not in out, "Compilation error")
        self.verify("No such" not in out, "Compilation error")
        self.bind_nic_driver(self.dut_ports, driver="")
        self.create_2vf_in_host()
        # start l3fwd-power
        l3fwd_app = "./examples/l3fwd-power/build/l3fwd-power"

        cmd = l3fwd_app + " -l 6,7 -n 4 -- -p 0x3 --config " + \
                          "'(0,0,6),(1,0,7)'"
        self.dut.send_expect(cmd, "POWER", timeout=40)
        out = self.dut.get_session_output()
        print(out)
        pattern = re.compile(r"(([a-f0-9]{2}:){5}[a-f0-9]{2})")
        mac_list = pattern.findall(out.lower())
        vf0_mac = mac_list[0][0]
        vf1_mac = mac_list[1][0]
        # send packet to vf0 and vf1
        self.scapy_send_packet(vf0_mac, self.tester_intf)
        self.scapy_send_packet(vf1_mac, self.tester_intf1)
        out = self.dut.get_session_output()
        self.verify('L3FWD_POWER: lcore 6 is waked up from rx interrupt' in out, 'lcore 6 is not waked up')
        self.verify('L3FWD_POWER: lcore 7 is waked up from rx interrupt' in out, 'lcore 7 is not waked up')
        self.verify('L3FWD_POWER: lcore 6 sleeps until interrupt triggers' in out, 'lcore 6 not sleep')
        self.verify('L3FWD_POWER: lcore 7 sleeps until interrupt triggers' in out, 'lcore 7 not sleep')
        self.scapy_send_packet(vf0_mac, self.tester_intf, count=16)
        self.scapy_send_packet(vf1_mac, self.tester_intf1, count=16)
        out = self.dut.get_session_output()
        self.verify('L3FWD_POWER: lcore 6 is waked up from rx interrupt' in out, 'lcore 6 is not waked up')
        self.verify('L3FWD_POWER: lcore 7 is waked up from rx interrupt' in out, 'lcore 7 is not waked up')
        self.dut.send_expect("killall l3fwd-power", "# ", 60, alt_session=True)
        self.interrupt_flag = True
        time.sleep(1)
        self.destroy_2vf_in_2pf()

    def test_vf_unicast(self):
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd('set verbose 1')
        self.vm_testpmd.execute_cmd('set fwd mac')
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("set allmulti all off")
        self.vm_testpmd.execute_cmd('set fwd mac')
        self.vm_testpmd.execute_cmd("start")
        self.scapy_send_packet(self.wrong_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 0, "Not receive expected packet")

        self.scapy_send_packet(self.vf_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

    def test_vf_vlan_promisc(self):
        self.vm_testpmd.start_testpmd("all")
        self.vm_testpmd.execute_cmd("port stop all")
        self.vm_testpmd.execute_cmd("set promisc all on")
        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set verbose 1")
        self.vm_testpmd.execute_cmd("vlan set filter off 0")
        self.vm_testpmd.execute_cmd("vlan set strip off 0")
        self.vm_testpmd.execute_cmd("port start all")
        self.vm_testpmd.execute_cmd("start")

        # send 10 tagged packets, and check 10 tagged packets received
        self.scapy_send_packet(self.vf_mac, self.tester_intf, vlan_flags=True, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

        # send 10 untagged packets, and check 10 untagged packets received
        self.scapy_send_packet(self.vf_mac, self.tester_intf, count=10)
        out = self.vm_dut.get_session_output()
        packets = len(re.findall('received 1 packets', out))
        self.verify(packets == 10, "Not receive expected packet")

    def scapy_send_packet(self, mac, testinterface, vlan_flags=False, count=1):
        """
        Send a packet to port
        """
        if count == 1:
            self.tester.scapy_append(
                'sendp([Ether(dst="%s")/IP()/UDP()/'\
                        'Raw(\'X\'*18)], iface="%s")' % (mac, testinterface))
        else:
            for i in range(count):
                if vlan_flags:
                    self.tester.scapy_append(
                        'sendp([Ether(dst="%s")/Dot1Q(id=0x8100, vlan=100)/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], '
                        'iface="%s")' % (mac, i, testinterface))
                else:
                    self.tester.scapy_append(
                        'sendp([Ether(dst="%s")/IP(dst="127.0.0.%d")/UDP()/Raw(\'X\'*18)], '
                        'iface="%s")' % (mac, i, testinterface))
        self.tester.scapy_execute()

    def create_2vf_in_host(self, driver=''):
        self.used_dut_port_0 = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[self.used_dut_port_0]['vfs_port']

        self.used_dut_port_1 = self.dut_ports[1]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[self.used_dut_port_1]['vfs_port']
        self.dut.send_expect('modprobe vfio', "#")
        self.dut.send_expect('modprobe vfio-pci', "#")
        for port in self.sriov_vfs_port_0:
            port.bind_driver('vfio-pci')

        for port in self.sriov_vfs_port_1:
            port.bind_driver('vfio-pci')

    def destroy_2vf_in_2pf(self):
        if getattr(self, 'used_dut_port_0', None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_0)
            self.used_dut_port_0 = None
        if getattr(self, 'used_dut_port_1', None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port_1)
            self.used_dut_port_1 = None

    def tear_down(self):
        """
        Run after each test case.
        """
        if self.interrupt_flag is True:
            self.interrupt_flag = False
        else:
            self.vm_testpmd.execute_cmd("quit", "#")
            time.sleep(1)
        if self.running_case == 'test_vf_mac_filter':
            self.destroy_vm_env()
        if self.running_case == 'test_vf_add_pvid':
            self.dut.send_expect("ip link set %s vf 0 vlan 0" % self.host_intf, "# ")
        self.dut.send_expect("ip link set dev %s vf 0 trust off" % self.host_intf, "# ")

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        if self.env_done:
            self.destroy_vm_env()

