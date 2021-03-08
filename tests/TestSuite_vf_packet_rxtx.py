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

from virt_common import VM
from test_case import TestCase
from pmd_output import PmdOutput
from packet import Packet

VM_CORES_MASK = 'all'


class TestVfPacketRxtx(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) > 1, "Insufficient ports")
        self.vm0 = None
        self.vm1 = None

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



    def set_up(self):

        self.setup_2pf_2vf_1vm_env_flag = 0
        self.setup_3vf_2vm_env_flag = 0

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
                if (self.nic in ["niantic", "sageville", "sagepond", "twinpond"]):
                    self.host_testpmd.start_testpmd("1S/9C/1T", "--txq=4 --rxq=4 ")
                else:
                    self.host_testpmd.start_testpmd("1S/5C/1T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'vf_packet_rxtx')
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
            if getattr(self, 'vm0_testpmd', None):
                self.vm0_testpmd.execute_cmd('stop')
                self.vm0_testpmd.execute_cmd('quit', '# ')
                self.vm0_testpmd = None
            self.vm0_dut_ports = None
            #destroy vm0
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'host_testpmd', None):
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None

        self.dut.virt_exit()

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


    def packet_rx_tx(self, driver='default'):

        if driver == 'igb_uio':
            self.setup_2pf_2vf_1vm_env(driver='igb_uio')
        else:
            self.setup_2pf_2vf_1vm_env(driver='')

        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')
        port_id_0 = 0
        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        out = self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        pmd_vf0_mac = self.vm0_testpmd.get_port_mac(port_id_0)
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd('start')

        time.sleep(2)

        tgen_ports = []
        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = self.tester.get_local_port(self.dut_ports[1])
        tgen_ports.append((tx_port, rx_port))

        dst_mac = pmd_vf0_mac
        src_mac = self.tester.get_mac(tx_port)

        pkt_param=[("ether", {'dst': dst_mac, 'src': src_mac})]

        result = self.tester.check_random_pkts(tgen_ports, allow_miss=False, params=pkt_param)
        print(self.vm0_testpmd.execute_cmd('show port stats all'))
        self.verify(result != False, "VF0 failed to forward packets to VF1")


######1. test case for kernel pf and dpdk vf 2pf_2vf_1vm scenario packet rx tx.
    def test_kernel_2pf_2vf_1vm(self):

        self.packet_rx_tx(driver='')

######2. test case for dpdk pf and dpdk vf 2pf_2vf_1vm scenario packet rx tx.
    def test_dpdk_2pf_2vf_1vm(self):

        self.packet_rx_tx(driver='igb_uio')

    def setup_3vf_2vm_env(self, driver='default'):

        self.used_dut_port = self.dut_ports[0]
        self.dut.generate_sriov_vfs_by_port(self.used_dut_port, 3, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[self.used_dut_port]['vfs_port']

        try:

            for port in self.sriov_vfs_port:
                print(port.pci)
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
            vf1_prop = {'opt_host': self.sriov_vfs_port[1].pci}
            vf2_prop = {'opt_host': self.sriov_vfs_port[2].pci}

            for port_id in self.dut_ports:
                if port_id == self.used_dut_port:
                    continue
                port = self.dut.ports_info[port_id]['port']
                port.bind_driver()

            if driver == 'igb_uio':
                self.host_testpmd = PmdOutput(self.dut)
                if (self.nic in ["niantic", "sageville", "sagepond","twinpond"]):
                    self.host_testpmd.start_testpmd("1S/9C/1T", "--txq=4 --rxq=4 ")
                else:
                    self.host_testpmd.start_testpmd("1S/2C/2T")

            # set up VM0 ENV
            self.vm0 = VM(self.dut, 'vm0', 'vf_packet_rxtx')
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
            self.vm0.set_vm_device(driver=self.vf_assign_method, **vf1_prop)
            self.vm_dut_0 = self.vm0.start()
            if self.vm_dut_0 is None:
                raise Exception("Set up VM0 ENV failed!")
            # set up VM1 ENV
            self.vm1 = VM(self.dut, 'vm1', 'vf_packet_rxtx')
            self.vm1.set_vm_device(driver=self.vf_assign_method, **vf2_prop)
            self.vm_dut_1 = self.vm1.start()
            if self.vm_dut_1 is None:
                raise Exception("Set up VM1 ENV failed!")

            self.setup_3vf_2vm_env_flag = 1
        except Exception as e:
            self.destroy_3vf_2vm_env()
            raise Exception(e)

    def destroy_3vf_2vm_env(self):
        if getattr(self, 'vm0', None):
            if getattr(self, 'vm0_testpmd', None):
                self.vm0_testpmd.execute_cmd('stop')
                self.vm0_testpmd.execute_cmd('quit', '# ')
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            self.vm_dut_0 = None
            self.vm0.stop()
            self.vm0 = None

        if getattr(self, 'vm1', None):
            if getattr(self, 'vm1_testpmd', None):
                self.vm1_testpmd.execute_cmd('stop')
                self.vm1_testpmd.execute_cmd('quit', '# ')
            self.vm1_testpmd = None
            self.vm1_dut_ports = None
            self.vm_dut_1 = None
            self.vm1.stop()
            self.vm1 = None

        self.dut.virt_exit()

        if getattr(self, 'host_testpmd', None) != None:
            self.host_testpmd.execute_cmd('quit', '# ')
            self.host_testpmd = None

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            port = self.dut.ports_info[self.used_dut_port]['port']
            port.bind_driver()
            self.used_dut_port = None

        for port_id in self.dut_ports:
            port = self.dut.ports_info[port_id]['port']
            port.bind_driver()

        self.setup_3vf_2vm_env_flag = 0

    def test_kernel_pf_vf_reset(self):

        self.setup_3vf_2vm_env(driver='')
        self.vf_reset()

    def test_dpdk_pf_vf_reset(self):
        self.setup_3vf_2vm_env(driver='igb_uio')
        self.vf_reset()

    def vf_reset(self):
        self.vm0_dut_ports = self.vm_dut_0.get_ports('any')
        self.vm1_dut_ports = self.vm_dut_1.get_ports('any')

        port_id_0 = 0
        port_id_1 = 1

        self.vm0_testpmd = PmdOutput(self.vm_dut_0)
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm0_testpmd.execute_cmd('show port info all')
        pmd0_vf0_mac = self.vm0_testpmd.get_port_mac(port_id_0)
        self.vm0_testpmd.execute_cmd('set fwd mac')
        self.vm0_testpmd.execute_cmd("set promisc all off")
        self.vm0_testpmd.execute_cmd('start')

        time.sleep(2)

        self.vm1_testpmd = PmdOutput(self.vm_dut_1)
        self.vm1_testpmd.start_testpmd(VM_CORES_MASK)
        self.vm1_testpmd.execute_cmd('show port info all')

        tx_port = self.tester.get_local_port(self.dut_ports[0])
        rx_port = tx_port

        dst_mac = pmd0_vf0_mac
        self.vm0_testpmd.execute_cmd('clear port stats all')
        pkt = Packet("Ether(dst='%s', src='%s')/IP(len=46)" % (dst_mac, self.tester.get_mac(tx_port)))
        session_bg = pkt.send_pkt_bg(crb=self.tester, tx_port=self.tester.get_interface(tx_port), loop=1)

        #vf port stop/start can trigger reset action
        for num in range(1000):
            self.vm1_testpmd.execute_cmd('port stop all')
            time.sleep(0.1)
            self.vm1_testpmd.execute_cmd('port start all')
            time.sleep(0.1)

        pkt.stop_send_pkt_bg(session_bg)

        pmd0_vf0_stats = self.vm0_testpmd.get_pmd_stats(port_id_0)
        pmd0_vf1_stats = self.vm0_testpmd.get_pmd_stats(port_id_1)

        vf0_rx_cnt = pmd0_vf0_stats['RX-packets']
        self.verify(vf0_rx_cnt != 0, "no packet was received by vm0_VF0")
    
        vf0_rx_err = pmd0_vf0_stats['RX-errors']
        self.verify(vf0_rx_err == 0, "vm0_VF0 rx-errors")
    
        vf1_tx_cnt = pmd0_vf1_stats['TX-packets']
        self.verify(vf1_tx_cnt != 0, "no packet was transmitted by vm0_VF1")

        vf1_tx_err = pmd0_vf1_stats['TX-errors']
        self.verify(vf1_tx_err == 0, "vm0_VF0 tx-errors")

        self.verify(vf0_rx_cnt == vf1_tx_cnt, "vm0_VF0 failed to forward packets to vm0_VF1 when reset vm1_VF0 frequently")

    def tear_down(self):

        if self.setup_2pf_2vf_1vm_env_flag == 1:
            self.destroy_2pf_2vf_1vm_env()
        if self.setup_3vf_2vm_env_flag == 1:
            self.destroy_3vf_2vm_env()

        if getattr(self, 'vm0', None):
            self.vm0.stop()

        if getattr(self, 'vm1', None):
            self.vm1.stop()

        self.dut.virt_exit()

        for port_id in self.dut_ports:
            self.dut.destroy_sriov_vfs_by_port(port_id)
            # DPDK-1754
            intf = self.dut.ports_info[port_id]['intf']
            self.dut.send_expect("ethtool -s %s autoneg on" % intf, "# ")

    def tear_down_all(self):
        pass

