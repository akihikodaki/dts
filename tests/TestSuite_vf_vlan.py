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

import random
import re
import time

from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import get_nic_name
from framework.test_case import TestCase
from framework.virt_common import VM

VM_CORES_MASK = 'all'
MAX_VLAN = 4095


class TestVfVlan(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False

        # set vf assign method and vf driver
        self.vf_driver = self.get_suite_cfg()['vf_driver']
        if self.vf_driver is None:
            self.vf_driver = 'pci-stub'
        self.verify(self.vf_driver in self.supported_vf_driver, "Unspported vf driver")
        if self.vf_driver == 'pci-stub':
            self.vf_assign_method = 'pci-assign'
        else:
            self.vf_assign_method = 'vfio-pci'
            self.dut.send_expect('modprobe vfio-pci', '#')

        # get driver version
        self.driver_version = self.nic_obj.driver_version

        # bind to default driver
        self.bind_nic_driver(self.dut_ports[:2], driver="")
        self.host_intf0 = self.dut.ports_info[self.dut_ports[0]]['intf']
        # get priv-flags default stats
        self.flag = 'vf-vlan-pruning'
        self.default_stats = self.dut.get_priv_flags_state(self.host_intf0, self.flag)

    def set_up(self):
        self.setup_vm_env()

    def setup_vm_env(self, driver='default'):
        """
        Create testing environment with 2VFs generated from 2PFs
        """
        if self.env_done:
            return

        self.used_dut_port_0 = self.dut_ports[0]
        self.host_intf0 = self.dut.ports_info[self.used_dut_port_0]['intf']
        tester_port = self.tester.get_local_port(self.used_dut_port_0)
        self.tester_intf0 = self.tester.get_interface(tester_port)
        if self.nic.startswith('columbiaville') and self.default_stats:
            self.dut.send_expect("ethtool --set-priv-flags %s %s on" % (self.host_intf0, self.flag), "# ")
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port_0, 1, driver=driver)
        self.sriov_vfs_port_0 = self.dut.ports_info[
            self.used_dut_port_0]['vfs_port']
        if self.kdriver == 'ice':
            self.dut.send_expect("ip link set %s vf 0 spoofchk off" %(self.host_intf0), "# ")
        self.vf0_mac = "00:10:00:00:00:00"
        self.dut.send_expect("ip link set %s vf 0 mac %s" %
                             (self.host_intf0, self.vf0_mac), "# ")

        self.used_dut_port_1 = self.dut_ports[1]
        self.host_intf1 = self.dut.ports_info[self.used_dut_port_1]['intf']
        if self.nic.startswith('columbiaville') and self.default_stats:
            self.dut.send_expect("ethtool --set-priv-flags %s %s on" % (self.host_intf1, self.flag), "# ")
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port_1, 1, driver=driver)
        self.sriov_vfs_port_1 = self.dut.ports_info[
            self.used_dut_port_1]['vfs_port']
        tester_port = self.tester.get_local_port(self.used_dut_port_1)
        self.tester_intf1 = self.tester.get_interface(tester_port)

        self.vf1_mac = "00:20:00:00:00:00"
        self.dut.send_expect("ip link set %s vf 0 mac %s" %
                             (self.host_intf1, self.vf1_mac), "# ")

        try:

            for port in self.sriov_vfs_port_0:
                port.bind_driver(self.vf_driver)

            for port in self.sriov_vfs_port_1:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {'opt_host': self.sriov_vfs_port_0[0].pci}
            vf1_prop = {'opt_host': self.sriov_vfs_port_1[0].pci}

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'vf_vlan')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")

        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.env_done = True

    def destroy_vm_env(self):
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

        self.bind_nic_driver(self.dut_ports[:2], driver="")

        self.env_done = False

    def test_pvid_vf_tx(self):
        """
        Add port based vlan on vf device and check vlan tx work
        """
        random_vlan = random.randint(1, MAX_VLAN)

        self.dut.send_expect(
            "ip link set %s vf 0 vlan %d" % (self.host_intf0, random_vlan), "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" %
                    random_vlan in out, "Failed to add pvid on VF0")

        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd('start')

        pkt = Packet(pkt_type='UDP')
        pkt.config_layer('ether', {'dst': self.vf1_mac})
        inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
        pkt.send_pkt(self.tester, tx_port=self.tester_intf1)
        pkts = self.tester.load_tcpdump_sniff_packets(inst)

        self.verify(len(pkts), "Not receive expected packet")
        self.vm0_testpmd.quit()

        # disable pvid
        self.dut.send_expect(
            "ip link set %s vf 0 vlan 0" % (self.host_intf0), "# ")

    def send_and_getout(self, vlan=0, pkt_type="UDP"):

        if pkt_type == "UDP":
            pkt = Packet(pkt_type='UDP')
            pkt.config_layer('ether', {'dst': self.vf0_mac})
        elif pkt_type == "VLAN_UDP":
            pkt = Packet(pkt_type='VLAN_UDP')
            pkt.config_layer('vlan', {'vlan': vlan})
            pkt.config_layer('ether', {'dst': self.vf0_mac})

        pkt.send_pkt(self.tester, tx_port=self.tester_intf0)
        out = self.vm_dut_0.get_session_output(timeout=2)

        return out

    def test_add_pvid_vf(self):
        random_vlan = random.randint(1, MAX_VLAN)

        self.dut.send_expect(
            "ip link set %s vf 0 vlan %d" % (self.host_intf0, random_vlan), "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" %
                    random_vlan in out, "Failed to add pvid on VF0")

        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('start')

        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        self.verify("received" in out, "Failed to received vlan packet!!!")

        # send packet without vlan
        out = self.send_and_getout(pkt_type="UDP")
        self.verify("received" not in out, "Received packet without vlan!!!")

        # send packet with vlan not matched
        wrong_vlan = (random_vlan + 1) % 4096
        out = self.send_and_getout(vlan=wrong_vlan, pkt_type="VLAN_UDP")
        self.verify(
            "received" not in out, "Received pacekt with wrong vlan!!!")

        # remove vlan
        self.vm0_testpmd.execute_cmd("stop")
        self.vm0_testpmd.execute_cmd("port stop all")
        self.dut.send_expect("ip link set %s vf 0 vlan 0" % self.host_intf0, "# ")
        out = self.dut.send_expect("ip link show %s" % self.host_intf0, "# ")
        self.verify("vlan %d" % random_vlan not in out, "Failed to remove pvid on VF0")

        # send packet with vlan
        self.vm0_testpmd.execute_cmd("port reset 0", 'testpmd> ', 120)
        self.vm0_testpmd.execute_cmd("port start all")
        self.vm0_testpmd.execute_cmd("start")

        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        if self.kdriver == 'i40e' and self.driver_version < "2.13.10":
            self.verify("received" in out, "Failed to received vlan packet!!!")
        else:
            self.verify(
                "received" not in out, "Received vlan packet without pvid!!!")

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify(
            "received" in out, "Not recevied packet with vlan 0!!!")

        # send packet without vlan
        out = self.send_and_getout(vlan=0, pkt_type="UDP")
        self.verify("received" in out, "Not received packet without vlan!!!")

        self.vm0_testpmd.quit()

        # disable pvid
        self.dut.send_expect(
            "ip link set %s vf 0 vlan 0" % (self.host_intf0), "# ")

    def tx_and_check(self, tx_vlan=1):
        inst = self.tester.tcpdump_sniff_packets(self.tester_intf0)
        self.vm0_testpmd.execute_cmd('set burst 1')
        self.vm0_testpmd.execute_cmd('start tx_first')
        self.vm0_testpmd.execute_cmd('stop')

        # strip sniffered vlans
        pkts = self.tester.load_tcpdump_sniff_packets(inst)
        vlans = []
        for i in range(len(pkts)):
            vlan = pkts.strip_element_vlan("vlan", p_index=i)
            vlans.append(vlan)

        self.verify(
            tx_vlan in vlans, "Tx packet with vlan not received!!!")

    def test_vf_vlan_tx(self):
        self.verify(self.kdriver not in ["ixgbe"], "NIC Unsupported: " + str(self.nic))
        random_vlan = random.randint(1, MAX_VLAN)
        tx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set verbose 1')

        for tx_vlan in tx_vlans:
            # for fortville ,
            # if you want insert tx_vlan,
            # please enable rx_vlan at the same time
            if self.kdriver == "i40e" or self.kdriver == 'ice':
                self.vm0_testpmd.execute_cmd('vlan set filter on 0')
                self.vm0_testpmd.execute_cmd('rx_vlan add %d 0' % tx_vlan)
            self.vm0_testpmd.execute_cmd('stop')
            self.vm0_testpmd.execute_cmd('port stop all')
            self.vm0_testpmd.execute_cmd('tx_vlan set 0 %d' % tx_vlan)
            self.vm0_testpmd.execute_cmd('port start all')
            self.tx_and_check(tx_vlan=tx_vlan)

        self.vm0_testpmd.quit()

    def test_vf_vlan_rx(self):
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('vlan set strip on 0')
        self.vm0_testpmd.execute_cmd('vlan set filter on 0')
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd('start')

        # send packet without vlan
        out = self.send_and_getout(vlan=0, pkt_type="UDP")
        self.verify(
            "received 1 packets" in out, "Not received normal packet as default!!!")

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify("VLAN tci=0x0"
                    in out, "Not received vlan 0 packet as default!!!")

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd('rx_vlan add %d 0' % rx_vlan)
            time.sleep(1)
            # send packet with same vlan
            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            vlan_hex = hex(rx_vlan)
            self.verify("VLAN tci=%s" %
                        vlan_hex in out, "Not received expected vlan packet!!!")

            pkt = Packet(pkt_type='VLAN_UDP')
            if rx_vlan == MAX_VLAN:
                continue
            wrong_vlan = (rx_vlan + 1) % 4096

            # send packet with wrong vlan
            out = self.send_and_getout(vlan=wrong_vlan, pkt_type="VLAN_UDP")
            self.verify(
                "received 1 packets" not in out, "Received filtered vlan packet!!!")

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd('rx_vlan rm %d 0' % rx_vlan)

        # send packet with vlan 0
        out = self.send_and_getout(vlan=0, pkt_type="VLAN_UDP")
        self.verify("VLAN tci=0x0"
                    in out, "Not received vlan 0 packet as default!!!")

        # send packet without vlan
        out = self.send_and_getout(pkt_type="UDP")
        self.verify("received 1 packets" in out,
                    "Not received normal packet after remove vlan filter!!!")

        # send packet with vlan
        out = self.send_and_getout(vlan=random_vlan, pkt_type="VLAN_UDP")
        if self.kdriver == 'i40e' and self.driver_version < "2.13.10":
            self.verify(
                "received 1 packets" in out, "Received mismatched vlan packet while vlan filter on")
        else:
            self.verify(
                "received 1 packets" not in out, "Received mismatched vlan packet while vlan filter on")

        self.vm0_testpmd.quit()

    def test_vf_vlan_strip(self):
        random_vlan = random.randint(1, MAX_VLAN - 1)
        rx_vlans = [1, random_vlan, MAX_VLAN]
        # start testpmd in VM
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        if self.kdriver == "i40e":
            self.vm0_testpmd.start_testpmd(VM_CORES_MASK, '')
        else:
            self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('set fwd rxonly')
        self.vm0_testpmd.execute_cmd('set verbose 1')
        self.vm0_testpmd.execute_cmd('start')

        for rx_vlan in rx_vlans:
            self.vm0_testpmd.execute_cmd('vlan set strip on 0')
            self.vm0_testpmd.execute_cmd('vlan set filter on 0')
            self.vm0_testpmd.execute_cmd('rx_vlan add %d 0' % rx_vlan)
            time.sleep(1)
            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            # enable strip, vlan will be in mbuf
            vlan_hex = hex(rx_vlan)
            self.verify("VLAN tci=%s" %
                        vlan_hex in out, "Failed to strip vlan packet!!!")
            self.verify("RTE_MBUF_F_RX_VLAN_STRIPPED" in out, "Failed to strip vlan packet!")

            self.vm0_testpmd.execute_cmd('vlan set strip off 0')

            out = self.send_and_getout(vlan=rx_vlan, pkt_type="VLAN_UDP")
            self.verify(
                "received 1 packets" in out, "Not received vlan packet as expected!!!")
            self.verify(
                "RTE_MBUF_F_RX_VLAN_STRIPPED" not in out, "Failed to disable strip vlan!!!")

        self.vm0_testpmd.quit()

    def tear_down(self):
        self.destroy_vm_env()

    def tear_down_all(self):
        self.destroy_vm_env()
        if self.nic.startswith('columbiaville') and self.default_stats:
            self.dut.send_expect("ethtool --set-priv-flags %s %s %s" % (self.host_intf0, self.flag, self.default_stats), "# ")
