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

import framework.utils as utils
from framework.packet import Packet
from framework.pmd_output import PmdOutput
from framework.settings import HEADER_SIZE
from framework.test_case import TestCase
from framework.utils import RED
from framework.virt_common import VM

VM_CORES_MASK = 'all'

ETHER_STANDARD_MTU = 1518
ETHER_JUMBO_FRAME_MTU = 9000


class TestVfJumboFrame(TestCase):

    supported_vf_driver = ['pci-stub', 'vfio-pci']

    def set_up_all(self):

        self.dut_ports = self.dut.get_ports(self.nic)
        self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
        self.vm0 = None
        self.env_done = False

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
        
        # enable tester mtu
        tester_port = self.tester.get_local_port(self.port)
        self.netobj = self.tester.ports_info[tester_port]['port']
        self.netobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU + 100)

        self.setup_vm_env()

    def set_up(self):
        pass

    def setup_vm_env(self, driver='default'):
        """
        Create testing environment with 1VF generated from 1PF
        """
        if self.env_done:
            return

        # bind to default driver
        self.bind_nic_driver(self.dut_ports[:1], driver="")

        self.used_dut_port = self.dut_ports[0]
        self.host_intf = self.dut.ports_info[self.used_dut_port]['intf']
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)

        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 1, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        self.vf_mac = "00:10:00:00:00:00"
        self.dut.send_expect("ip link set %s vf 0 mac %s" %
                             (self.host_intf, self.vf_mac), "# ")

        try:

            for port in self.sriov_vfs_port:
                port.bind_driver(self.vf_driver)

            time.sleep(1)
            vf_popt = {'opt_host': self.sriov_vfs_port[0].pci}

            # set up VM ENV
            self.vm = VM(self.dut, 'vm0', 'vf_jumboframe')
            self.vm.set_vm_device(driver=self.vf_assign_method, **vf_popt)
            self.vm_dut = self.vm.start()
            if self.vm_dut is None:
                raise Exception("Set up VM ENV failed!")

            self.vm_testpmd = PmdOutput(self.vm_dut)

        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)

        self.env_done = True

    def destroy_vm_env(self):
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

        if getattr(self, 'used_dut_port', None) != None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None
        self.bind_nic_driver(self.dut_ports[:1], driver='default')

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

    def jumboframes_send_packet(self, pktsize, received=True):
        """
        Send 1 packet to portid
        """
        tx_pkts_ori, _, tx_bytes_ori = [int(_) for _ in self.jumboframes_get_stat(self.vm_port, "tx")]
        rx_pkts_ori, rx_err_ori, rx_bytes_ori = [int(_) for _ in self.jumboframes_get_stat(self.vm_port, "rx")]

        mac = self.vm_dut.get_mac_address(self.vm_port)

        pkt = Packet(pkt_type='UDP', pkt_len=pktsize)
        pkt.config_layer('ether', {'dst': mac})
        pkt.send_pkt(self.tester, tx_port=self.tester_intf, timeout=30)

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

            if self.kdriver in ["ixgbe", "ice", "i40e"]:
                self.verify((rx_bytes + 4) == pktsize, "Rx packet size should be packet size - 4")

            if self.kdriver == "igb":
                self.verify(tx_bytes == pktsize, "Tx packet size should be packet size")
            else:
                self.verify((tx_bytes + 4) == pktsize, "Tx packet size should be packet size - 4")
        else:
            self.verify(rx_err == 1 or tx_pkts == 0, "Packet drop assert error")

    def test_vf_normal_nojumbo(self):
        """
        This case aims to test transmitting normal size packet without jumbo enable
        """
        # should enable jumbo on host
        self.dutobj = self.dut.ports_info[self.port]['port']
        self.dutobj.enable_jumbo(framesize=ETHER_STANDARD_MTU)

        self.vm_testpmd.start_testpmd("Default", "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000" % (ETHER_STANDARD_MTU))

        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("start")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU - 1)
        self.jumboframes_send_packet(ETHER_STANDARD_MTU)

    def test_vf_normal_withjumbo(self):
        """
        When jumbo frame supported, this case is to verify that the normal size
        packet forwarding should be support correct.
        """
        # should enable jumbo on host
        self.dutobj = self.dut.ports_info[self.port]['port']
        self.dutobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU)

        self.vm_testpmd.start_testpmd("Default", "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000" % (ETHER_JUMBO_FRAME_MTU))

        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("start")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU - 1)
        self.jumboframes_send_packet(ETHER_STANDARD_MTU)

    def test_vf_jumbo_nojumbo(self):
        """
        This case aims to test transmitting jumbo frame packet on testpmd without
        jumbo frame support.
        """
        # should enable jumbo on host
        self.dutobj = self.dut.ports_info[self.port]['port']
        self.dutobj.enable_jumbo(framesize=ETHER_STANDARD_MTU)

        self.vm_testpmd.start_testpmd("Default", "--port-topology=loop --tx-offloads=0x8000" )

        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("start")

        # On igb, for example i350, refer to :DPDK-1117
        # For PF, the max-pkt-len = mtu + 14(IP_hearder_len) + 4(CRC) + 4(VLAN header len) + 4(VLAN header len).
        # For VF, the real max-pkt-len = the given max-pkt-len + 4(VLAN header len).
        # This behavior is leveraged from kernel driver.
        # And it means max-pkt-len is always 4 bytes longer than assumed.

        if self.kdriver == "igb":
            self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1 + 4, False)
        else:
            self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1 + 4 + 4, False)

    def test_vf_jumbo_withjumbo(self):
        """
        When jumbo frame supported, this case is to verify that jumbo frame
        packet can be forwarded correct.
        """
        # should enable jumbo on host
        self.dutobj = self.dut.ports_info[self.port]['port']
        self.dutobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU)

        self.vm_testpmd.start_testpmd("Default", "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000" % (ETHER_JUMBO_FRAME_MTU))

        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("start")

        self.jumboframes_send_packet(ETHER_STANDARD_MTU + 1)
        self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU - 1)
        self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU)

    def test_vf_jumbo_overjumbo(self):
        """
        When the jubmo frame MTU set as 9000, this case is to verify that the
        packet which the length bigger than MTU can not be forwarded.
        """
        # should enable jumbo on host
        self.dutobj = self.dut.ports_info[self.port]['port']
        self.dutobj.enable_jumbo(framesize=ETHER_JUMBO_FRAME_MTU)

        self.vm_testpmd.start_testpmd("Default", "--max-pkt-len=%d --port-topology=loop --tx-offloads=0x8000" % (ETHER_JUMBO_FRAME_MTU))

        self.vm_testpmd.execute_cmd("set fwd mac")
        self.vm_testpmd.execute_cmd("set promisc all off")
        self.vm_testpmd.execute_cmd("start")

        # On 1G NICs, when the jubmo frame MTU set as 9000, the software adjust it to 9004.
        if self.kdriver == "igb":
            self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU + 4 + 1, False)
        else:
            self.jumboframes_send_packet(ETHER_JUMBO_FRAME_MTU + 1, False)

    def tear_down(self):
        """
        Run after each test case.
        """
        self.vm_testpmd.execute_cmd("stop")
        self.vm_testpmd.quit()

    def tear_down_all(self):
        """
        When the case of this test suite finished, the environment should
        clear up.
        """
        self.destroy_vm_env()
        self.netobj.enable_jumbo(framesize=ETHER_STANDARD_MTU)
