# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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

Test Shutdown API Feature

"""

import utils
import time
import re
import os
import random
from test_case import TestCase
from pmd_output import PmdOutput
from settings import HEADER_SIZE, PROTOCOL_PACKET_SIZE
from exception import VerifyFailure
from qemu_kvm import QEMUKvm
from settings import get_nic_name
from random import randint
from settings import DRIVERS
#
#
# Test class.
#


VM_CORES_MASK = 'all'
class TestShutdownApi(TestCase):

    #
    #
    #
    # Test cases.
    #
    supported_vf_driver = ['pci-stub', 'vfio-pci']
    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        ports = self.dut.get_ports()
        self.verify(len(ports) >= 1, "Insufficient number of ports.")
        self.ports = ports[:1]
        self.ports_socket = self.dut.get_numa_id(self.ports[0])

        for port in self.ports:
            self.tester.send_expect("ifconfig %s mtu %s" % (
                self.tester.get_interface(self.tester.get_local_port(port)), 5000), "# ")

        self.pmdout = PmdOutput(self.dut)
        self.vm_env_done = False

    def set_up(self):
        """
        Run before each test case.
        """
        if self._suite_result.test_case == "test_change_linkspeed_vf":
            self.used_driver = self.dut.ports_info[0]["port"].get_nic_driver()
            driver_name = DRIVERS.get(self.nic)
            self.dut_ports = self.dut.get_ports(self.nic)
            self.verify(len(self.dut_ports) >= 1, "Insufficient ports")
            self.bind_nic_driver(self.dut_ports, driver=driver_name)
            self.setup_vm_env(driver_name)

    def get_stats(self, portid):
        """
        Get packets number from port statistic.
        @param: stop -- stop forward before get stats
        """
        output = PmdOutput(self.dut)
        stats = output.get_pmd_stats(portid)
        return stats

    def check_forwarding(self, ports=None, pktSize=68, received=True, vlan=False, promisc=False, allmulti=False, vlan_strip=False):
        if ports is None:
            ports = self.ports
        if len(ports) == 1:
            self.send_packet(ports[0], ports[0], pktSize, received, vlan, promisc, allmulti, vlan_strip)
            return

    def send_packet(self, txPort, rxPort, pktSize=68, received=True, vlan=False, promisc=False, allmulti=False, vlan_strip=False):
        """
        Send packages according to parameters.
        """
        # check the ports are UP before sending packets
        res = self.pmdout.wait_link_status_up('all')
        self.verify(res is True, 'there have port link is down')

        port0_stats = self.get_stats(txPort)
        gp0tx_pkts, gp0tx_bytes = [port0_stats['TX-packets'], port0_stats['TX-bytes']]
        port1_stats = self.get_stats(rxPort)
        gp1rx_pkts, gp1rx_err, gp1rx_bytes = [port1_stats['RX-packets'], port1_stats['RX-errors'], port1_stats['RX-bytes']]
        time.sleep(5)

        itf = self.tester.get_interface(self.tester.get_local_port(rxPort))
        smac = self.tester.get_mac(self.tester.get_local_port(rxPort))
        dmac = self.dut.get_mac_address(rxPort)

        # when promisc is true, destination mac should be fake
        if promisc:
            dmac = "00:00:00:00:00:01"
        if allmulti:
            dmac = "01:00:00:33:00:01"
        if vlan:
            padding = pktSize - HEADER_SIZE['eth'] - HEADER_SIZE['ip'] -4
            pkg = 'Ether(src="%s", dst="%s")/Dot1Q(vlan=1)/IP()/Raw(load="P" * %d)' % (smac, dmac, padding)
        else:
            padding = pktSize - HEADER_SIZE['eth'] - HEADER_SIZE['ip']
            pkg = 'Ether(src="%s", dst="%s")/IP()/Raw(load="P" * %d)' % (smac, dmac, padding)

        self.tester.scapy_foreground()
        self.tester.scapy_append('sendp(%s, iface="%s", count=4)' % (pkg, itf))
        self.tester.scapy_execute()
        time.sleep(3)

        port0_stats = self.get_stats(txPort)
        p0tx_pkts, p0tx_bytes = [port0_stats['TX-packets'], port0_stats['TX-bytes']]
        port1_stats = self.get_stats(rxPort)
        p1rx_pkts, p1rx_err, p1rx_bytes = [port1_stats['RX-packets'], port1_stats['RX-errors'], port1_stats['RX-bytes']]
        time.sleep(5)

        p0tx_pkts -= gp0tx_pkts
        p0tx_bytes -= gp0tx_bytes
        p1rx_pkts -= gp1rx_pkts
        p1rx_bytes -= gp1rx_bytes

        rx_bytes_exp = pktSize*4
        tx_bytes_exp = pktSize*4

        if self.kdriver == "fm10k":
            # RRC will always strip rx/tx crc
            rx_bytes_exp -= 4
            tx_bytes_exp -= 4
            if vlan_strip is True:
                # RRC will always strip rx/tx vlan
                rx_bytes_exp -= 4
                tx_bytes_exp -= 4
        else:
            # some NIC will always include tx crc
            rx_bytes_exp -= 16
            tx_bytes_exp -= 16
            if vlan_strip is True:
                # vlan strip default is off
                tx_bytes_exp -= 16
         
        # fortville nic enable send lldp packet function when port setup
        # now the tx-packets size is lldp_size(110) * n + forward packe size
        # so use (tx-packets - forward packet size) % lldp_size, if it is 0, it means forward packet size right
 
        if received:
            self.verify(self.pmdout.check_tx_bytes(p0tx_pkts, p1rx_pkts), "Wrong TX pkts p0_tx=%d, p1_rx=%d" % (p0tx_pkts, p1rx_pkts))
            self.verify(p1rx_bytes == rx_bytes_exp, "Wrong Rx bytes p1_rx=%d, expect=%d" % (p1rx_bytes, rx_bytes_exp))
            self.verify(self.pmdout.check_tx_bytes(p0tx_bytes, tx_bytes_exp) , "Wrong Tx bytes p0_tx=%d, expect=%d" % (p0tx_bytes, tx_bytes_exp))
        else:
            self.verify(self.pmdout.check_tx_bytes(p0tx_pkts), "Packet not dropped p0tx_pkts=%d" % p0tx_pkts)

    def check_ports(self, status=True):
        """
        Check link status of the ports.
        """
        # RRC not support link speed change
        if self.kdriver == "fm10k":
            return

        for port in self.ports:
            out = self.tester.send_expect(
                "ethtool %s" % self.tester.get_interface(self.tester.get_local_port(port)), "# ")
            if status:
                self.verify("Link detected: yes" in out, "Wrong link status")
            else:
                self.verify("Link detected: no" in out, "Wrong link status")


    def check_linkspeed_config(self, configs):
        ret_val = False
        if (configs == None):
            self.verify(False, "Link speed config error.")
            ret_val = False
        elif (len(configs) < 1):
            self.verify(False, "Link speed config error.")
            ret_val = False
        elif len(configs) < 2:
            print("\nOnly one link speed, can't be changed.\n")
            ret_val = False
        else:
            ret_val = True

        return ret_val

    def check_vf_link_status(self):
        self.vm0_testpmd.start_testpmd(VM_CORES_MASK, '--port-topology=chained')
        time.sleep(2)
        for i in range(15):
            out = self.vm0_testpmd.execute_cmd('show port info 0')
            print(out)
            if 'Link status: down' in out:
                time.sleep(2)
            else :
                break
        self.verify("Link status: up" in out, "VF link down!!!")

    def bind_nic_driver(self, ports, driver=""):
        if driver == "igb_uio":
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
    def setup_vm_env(self, driver='default'):
        """
        Create testing environment with 1VF generated from 1PF
        """
        if self.vm_env_done:
            return

        self.vm0 = None

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

        self.used_dut_port = self.dut_ports[0]
        tester_port = self.tester.get_local_port(self.used_dut_port)
        self.tester_intf = self.tester.get_interface(tester_port)
        self.dut.generate_sriov_vfs_by_port(
            self.used_dut_port, 2, driver=driver)
        self.sriov_vfs_port = self.dut.ports_info[
            self.used_dut_port]['vfs_port']
        for port in self.sriov_vfs_port:
            port.bind_driver(self.vf_driver)
        time.sleep(1)

        vf0_prop = {'opt_host': self.sriov_vfs_port[0].pci}
        self.host_intf = self.dut.ports_info[self.used_dut_port]['intf']
        self.vf_mac = "00:01:23:45:67:89"
        self.dut.send_expect("ip link set %s vf 0 mac %s" % (self.host_intf, self.vf_mac), "# ")
        # set up VM0 ENV
        self.vm0 = QEMUKvm(self.dut, 'vm0', 'shutdown_api')
        self.vm0.set_vm_device(driver=self.vf_assign_method, **vf0_prop)
        try:
            self.vm0_dut = self.vm0.start()
            if self.vm0_dut is None:
                raise Exception("Set up VM0 ENV failed!")
        except Exception as e:
            self.destroy_vm_env()
            raise Exception(e)
        self.vm0_dut_ports = self.vm0_dut.get_ports('any')
        self.vm0_testpmd = PmdOutput(self.vm0_dut)

        self.vm_env_done = True


    def destroy_vm_env(self):
        if getattr(self, 'self.vm0_testpmd', None):
            self.vm0_testpmd.quit()

        if getattr(self, 'vm0', None):
            if getattr(self, 'vm0_dut', None):
                self.vm0_dut.kill_all()
            self.vm0_testpmd = None
            self.vm0_dut_ports = None
            # destroy vm0
            self.vm0.stop()
        if getattr(self, 'used_dut_port', None) is not None:
            self.dut.destroy_sriov_vfs_by_port(self.used_dut_port)
            self.used_dut_port = None

        for port in self.ports:
            self.dut.send_expect("ethtool -s %s autoneg on " % self.dut.ports_info[port]["intf"], "#")

        self.bind_nic_driver(self.dut_ports, driver=self.used_driver or self.drivername)

        if not self.vm_env_done:
            return

        self.vm_env_done = False




    def test_stop_restart(self):
        """
        Stop and Restar.
        """
        self.pmdout.start_testpmd("Default", "--portmask=%s  --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()
        self.dut.send_expect("stop", "testpmd> ")
        self.check_forwarding(received=False)
        self.dut.send_expect("port stop all", "testpmd> ", 100)
        time.sleep(5)
        if self.nic in ["columbiaville_25g", "columbiaville_100g"]:
            self.check_ports(status=True)
        else:
            self.check_ports(status=False)
        self.dut.send_expect("port start all", "testpmd> ", 100)
        time.sleep(5)
        self.check_ports(status=True)
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_set_promiscuousmode(self):
        """
        Promiscuous mode.
        """
        ports = [self.ports[0]]

        portmask = utils.create_mask(ports)
        self.pmdout.start_testpmd("Default", "--portmask=%s  --port-topology=loop" % portmask, socket = self.ports_socket)

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("show config rxtx", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")

        try:
            self.check_forwarding(ports)
        except VerifyFailure as e:
            print('promiscuous mode is working correctly')
        except Exception as e:
            print(("   !!! DEBUG IT: " + e.message))
            self.verify(False, e.message)

        self.check_forwarding(ports, received=False, promisc=True)
        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("set promisc all on", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("show config rxtx", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding(ports, promisc=True)
        self.check_forwarding(ports)
        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect("start", "testpmd> ")
        self.dut.send_expect("quit", "# ", 30)

    def test_set_allmulticast(self):
        """
        Allmulticast mode.
        """
        ports = [self.ports[0]]

        portmask = utils.create_mask(ports)
        self.pmdout.start_testpmd("Default", "--portmask=%s  --port-topology=loop" % portmask, socket = self.ports_socket)

        self.dut.send_expect("set promisc all off", "testpmd> ")
        self.dut.send_expect("set allmulti all off", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("start", "testpmd> ")

        self.check_forwarding(ports)
        self.check_forwarding(ports, received=False, promisc=True)
        self.check_forwarding(ports, received=False, allmulti=True)
        self.dut.send_expect("set allmulti all on", "testpmd> ")
        self.check_forwarding(ports)
        self.check_forwarding(ports, allmulti=True)
        self.check_forwarding(ports, received=False, promisc=True)
        self.dut.send_expect("set promisc all on", "testpmd> ")
        self.check_forwarding(ports)
        self.check_forwarding(ports, promisc=True)
        self.dut.send_expect("quit", "# ", 30)

    def test_reset_queues(self):
        """
        Reset RX/TX Queues.
        """
        testcorelist = self.dut.get_core_list("1S/8C/1T", socket=self.ports_socket)

        self.pmdout.start_testpmd(testcorelist, "--portmask=%s  --port-topology=loop" % utils.create_mask([self.ports[0]]), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")
        fwdcoremask = utils.create_mask(testcorelist[-3:])

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config all rxq 2", "testpmd> ")
        self.dut.send_expect("port config all txq 2", "testpmd> ")
        self.dut.send_expect("set coremask %s" % fwdcoremask, "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        self.verify("RX queue number: 2" in out, "RX queues not reconfigured properly")
        self.verify("Tx queue number: 2" in out, "TX queues not reconfigured properly")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()
        self.dut.send_expect("quit", "# ", 30)

    def test_reconfigure_ports(self):
        """
        Reconfigure All Ports With The Same Configurations (CRC)
        """
        RX_OFFLOAD_KEEP_CRC = 0x10000

        if (self.nic in ["cavium_a063", "cavium_a064"]):
            self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        else:
            self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop --disable-crc-strip" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        Rx_offloads = re.compile('Rx offloads=(.*?)\s+?').findall(out, re.S)
        crc_keep_temp = []
        for i in range(len(self.dut.get_ports())):
            crc_keep_temp.append(int(Rx_offloads[i],16) & RX_OFFLOAD_KEEP_CRC)
            crc_keep = crc_keep_temp[0]
            crc_keep = crc_keep and crc_keep_temp[i]
        self.verify(
            crc_keep == RX_OFFLOAD_KEEP_CRC, "CRC keeping not enabled properly")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        for i in range(len(self.dut.get_ports())):
            self.dut.send_expect("port config %s rx_offload keep_crc off" % i, "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        Rx_offloads = re.compile('Rx offloads=(.*?)\s+?').findall(out, re.S)
        crc_strip_temp = []
        for i in range(len(self.dut.get_ports())):
            crc_strip_temp.append(int(Rx_offloads[i],16) | ~RX_OFFLOAD_KEEP_CRC)
            crc_strip = crc_strip_temp[0]
            crc_strip = crc_strip and crc_strip_temp[i]
        self.verify(
            crc_strip == ~RX_OFFLOAD_KEEP_CRC, "CRC stripping not enabled properly")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_change_linkspeed(self):
        """
        Change Link Speed.
        """
        if self.kdriver == "fm10k":
            print((utils.RED("RRC not support\n")))
            return

        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        out = self.tester.send_expect(
            "ethtool %s" % self.tester.get_interface(self.tester.get_local_port(self.ports[0])), "# ")

        self.verify("Supports auto-negotiation: Yes" in out, "Auto-negotiation not support.")

        result_scanner = r"([0-9]+)base\S*/([A-Za-z]+)"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.findall(out)
        configs = m[:-int(len(m) / 2)]

        if not self.check_linkspeed_config(configs):
            return;

        for config in configs:
            print(config)
            if self.nic in ["ironpond"]:
                if config[0] != '1000' or '10000':
                    continue
            elif self.nic in ["sagepond"]:
                if config[0] not in ['1000', '10000']:
                    continue
            self.dut.send_expect("port stop all", "testpmd> ", 100)
            for port in self.ports:
                self.dut.send_expect("port config %d speed %s duplex %s" % (port,
                            config[0], config[1].lower()), "testpmd> ")
            self.dut.send_expect("set fwd mac", "testpmd>")
            self.dut.send_expect("port start all", "testpmd> ", 100)
            time.sleep(8)  # sleep few seconds for link stable

            for port in self.ports:
                out = self.dut.send_expect("show port info %s" % port, "testpmd>")
                self.verify("Link status: up" in out,
                            "Wrong link status reported by the dut")
                if int(config[0]) < 1000:
                    self.verify("Link speed: %s Mbps" % config[0] in out,
                                 "Wrong speed reported by the dut")
                else:
                    num =int(int(config[0])/1000)
                    self.verify("Link speed: %d Gbps" % num in out,
                                 "Wrong speed reported by the dut")
                self.verify("Link duplex: %s-duplex" % config[1].lower() in out,
                            "Wrong link type reported by the dut")
                out = self.tester.send_expect(
                    "ethtool %s" % self.tester.get_interface(self.tester.get_local_port(port)), "# ")
                self.verify("Speed: %sMb/s" % config[0] in out,
                            "Wrong speed reported by the self.tester.")
                self.verify("Duplex: %s" % config[1] in out,
                            "Wrong link type reported by the self.tester.")
            self.dut.send_expect("start", "testpmd> ")
            self.check_forwarding()
            self.dut.send_expect("stop", "testpmd> ")
    def test_change_linkspeed_vf(self):
        """
        Change Link Speed VF .
        """
        self.check_vf_link_status()
        out = self.tester.send_expect(
            "ethtool %s" % self.tester.get_interface(self.tester.get_local_port(self.ports[0])), "# ", 100)

        dut_out=self.dut.send_expect("ethtool %s" % self.dut.ports_info[0]["intf"], "# ", 100)
        check_auto_negotiation="Supports auto-negotiation: Yes"
        self.verify(check_auto_negotiation in out and check_auto_negotiation in dut_out , "tester or dut  Auto-negotiation not support.")
        result_scanner = r"([0-9]+)base\S*/([A-Za-z]+)"
        scanner = re.compile(result_scanner, re.DOTALL)
        m = scanner.findall(dut_out)
        configs = m[:-int(len(m) / 2)]

        if not self.check_linkspeed_config(configs):
            return

        result_linkspeed_scanner = r"Link\s*speed:\s([0-9]+)\s*(\S+)"
        linkspeed_scanner = re.compile(result_linkspeed_scanner, re.DOTALL)
        result_linktype_scanner = r"Link\s*duplex:\s*(\S*)\s*-\s*duplex"
        linktype_scanner = re.compile(result_linktype_scanner, re.DOTALL)
        tx_rx_packets = 3
        self.vm0_testpmd.execute_cmd('set fwd mac', "testpmd> ", 30)
        self.vm0_testpmd.execute_cmd('start')
        for config in configs:
            print(config)
            for port in self.ports:
                if len(configs) != 1:
                    self.dut.send_expect(
                        "ethtool -s %s autoneg off  speed %s duplex %s" % (self.dut.ports_info[port]["intf"],
                                                                           config[0], config[1].lower()), "#")
                    time.sleep(5)
                self.tester_itf_1 = self.tester.get_interface(port)
                pkt = 'Ether(dst="%s", src="02:00:00:00:00:01")/IP()/UDP()/("X"*22)' % self.vf_mac
                self.tester.scapy_append(
                    'sendp([%s], iface="%s", count=%d)'
                    % (pkt, self.tester_intf, tx_rx_packets))
                self.tester.scapy_execute()
                time.sleep(2)
                out = self.vm0_testpmd.execute_cmd('show port stats all')
                self.verify("RX-packets: %d" % tx_rx_packets in out and "TX-packets: %d" % tx_rx_packets in out,
                            "VF Expected results: RX-packets: %d \n Actual results:%s " % (tx_rx_packets, out))
                self.vm0_testpmd.execute_cmd('clear port stats all')
                time.sleep(1)

            out = self.vm0_testpmd.execute_cmd('show port info all')

            linkspeed = linkspeed_scanner.findall(out)[0]
            linktype = linktype_scanner.findall(out)

            actual_speed = int(linkspeed[0])
            if linkspeed[1] == "Gbps":
                actual_speed = actual_speed * 1000
            self.verify(config[0] == str(actual_speed),
                        "Wrong VF speed reported by the self.tester.")
            self.verify(config[1].lower() == linktype[0].lower(),
                        "Wrong VF link type reported by the self.tester.")


    def test_enable_disablejumbo(self):
        """
        Enable/Disable Jumbo Frames.
        """
        if self.kdriver == "fm10k":
            print((utils.RED("RRC not support\n")))
            return

        jumbo_size = 2048
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config all max-pkt-len %d" % jumbo_size, "testpmd> ")
        out = self.dut.send_expect("vlan set strip off all", "testpmd> ")
        if "fail" not in out:
            for port in self.ports:
                self.dut.send_expect("vlan set filter on %d" % port, "testpmd> ")
                self.dut.send_expect("rx_vlan add 1 %d" % port, "testpmd> ")
            self.dut.send_expect("set fwd mac", "testpmd>")
            self.dut.send_expect("port start all", "testpmd> ", 100)
            self.dut.send_expect("start", "testpmd> ")

            if self.nic in ['magnolia_park', 'niantic', 'twinpond', 'kawela_4', 'ironpond', 'springfountain', 'sageville', 'sagepond']:
                # nantic vlan length will not be calculated
                vlan_jumbo_size = jumbo_size + 4
            else:
                vlan_jumbo_size = jumbo_size
            out = self.dut.send_expect("show port %d rx_offload configuration" % port, "testpmd> ")
            if 'VLAN_STRIP' in out:
                vlan_strip = True
            else:
                vlan_strip = False
            self.check_forwarding(pktSize=vlan_jumbo_size - 1, vlan=True, vlan_strip=vlan_strip)
            self.check_forwarding(pktSize=vlan_jumbo_size, vlan=True, vlan_strip=vlan_strip)
            self.check_forwarding(pktSize=vlan_jumbo_size + 1, received=False, vlan=True, vlan_strip=vlan_strip)

            self.dut.send_expect("stop", "testpmd> ")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config all hw-vlan off", "testpmd> ")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("start", "testpmd> ")
        """
        On 1G NICs, when the jubmo frame MTU set as X, the software adjust it to (X + 4).
        """
        if self.nic in ["kawela_4"]:
            jumbo_size += 4
        self.check_forwarding(pktSize=jumbo_size - 1)
        self.check_forwarding(pktSize=jumbo_size)
        self.check_forwarding(pktSize=jumbo_size + 1, received=False)

    def test_enable_disablerss(self):
        """
        Enable/Disable RSS.
        """
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config rss ip", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_change_numberrxdtxd(self):
        """
        Change numbers of rxd and txd.
        """
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config all rxd 1024", "testpmd> ")
        self.dut.send_expect("port config all txd 1024", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        self.verify(
            "RX desc=1024" in out, "RX descriptor not reconfigured properly")
        self.verify(
            "TX desc=1024" in out, "TX descriptor not reconfigured properly")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_change_numberrxdtxdaftercycle(self):
        """
        Change the Number of rxd/txd.
        """
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port config all rxd 1024", "testpmd> ")
        self.dut.send_expect("port config all txd 1024", "testpmd> ")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        self.verify(
            "RX desc=1024" in out, "RX descriptor not reconfigured properly")
        self.verify(
            "TX desc=1024" in out, "TX descriptor not reconfigured properly")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

        self.dut.send_expect("stop", "testpmd> ")
        self.dut.send_expect("port stop all", "testpmd> ", 100)
        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        self.verify(
            "RX desc=1024" in out, "RX descriptor not reconfigured properly")
        self.verify(
            "TX desc=1024" in out, "TX descriptor not reconfigured properly")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_change_thresholds(self):
        """
        Change RX/TX thresholds
        DPDK-24129:1.CVL and FVL not support tx and rx
                   2.Ixgbe not support rx, only support tx.
                   3.foxville, powerville and springville not support txfree and txrs
        """
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        self.dut.send_expect("port stop all", "testpmd> ", 100)
        if self.nic in ["sagepond","sageville","twinpond","niantic"]:
            self.dut.send_expect("port config all txfreet 32", "testpmd> ")
            self.dut.send_expect("port config all txrst 32", "testpmd> ")
        self.dut.send_expect("port config all rxfreet 32", "testpmd> ")
        self.dut.send_expect("port config all txpt 64", "testpmd> ")
        self.dut.send_expect("port config all txht 64", "testpmd> ")
        if self.nic in ["foxville"]:
            self.dut.send_expect("port config all txwt 16", "testpmd> ")
        else:
            self.dut.send_expect("port config all txwt 0", "testpmd> ")

        self.dut.send_expect("port start all", "testpmd> ", 100)
        out = self.dut.send_expect("show config rxtx", "testpmd> ")
        self.verify("RX free threshold=32" in out,
                    "RX descriptor not reconfigured properly")
        if self.nic in ["sagepond","sageville","twinpond","niantic"]:
            self.verify("TX free threshold=32" in out,
                    "TX descriptor not reconfigured properly")
            self.verify("TX RS bit threshold=32" in out,
                    "TX descriptor not reconfigured properly")
        self.verify("pthresh=64" in out, "TX descriptor not reconfigured properly")
        self.verify("hthresh=64" in out, "TX descriptor not reconfigured properly")
        if self.nic in ["foxville"]:
            self.verify("wthresh=16" in out, "TX descriptor not reconfigured properly")
        else:
            self.verify("wthresh=0" in out, "TX descriptor not reconfigured properly")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("start", "testpmd> ")
        self.check_forwarding()

    def test_stress_test(self):
        """
        Start/stop stress test.
        """
        stress_iterations = 10

        self.pmdout.start_testpmd("Default", "--portmask=%s  --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")

        tgenInput = []
        for port in self.ports:
            dmac=self.dut.get_mac_address(port)
            self.tester.scapy_append('wrpcap("test%d.pcap",[Ether(src="02:00:00:00:00:0%d",dst="%s")/IP()/UDP()/()])'% (port, port, dmac))
            tgenInput.append((self.tester.get_local_port(port), self.tester.get_local_port(port), "test%d.pcap" % port))
        for _ in range(stress_iterations):
            self.dut.send_expect("port stop all", "testpmd> ", 100)
            self.dut.send_expect("set fwd mac", "testpmd>")
            self.dut.send_expect("port start all", "testpmd> ", 100)
            self.dut.send_expect("start", "testpmd> ")
            self.check_forwarding()
            self.dut.send_expect("stop", "testpmd> ")

        self.dut.send_expect("quit", "# ")

    def test_link_stats(self):
        """
        port link stats test
        """
        if self.kdriver == "fm10k":
            print((utils.RED("RRC not support\n")))
            return

        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports), socket=self.ports_socket)
        self.dut.send_expect("set promisc all off", "testpmd>")
        self.dut.send_expect("set fwd mac", "testpmd>")
        self.dut.send_expect("start", "testpmd>")

        ports_num = len(self.ports)
        # link down test
        for i in range(ports_num):
            self.dut.send_expect("set link-down port %d" % i, "testpmd>")
        # leep few seconds for NIC link status update
        time.sleep(5)
        self.check_ports(status=False)

        # link up test
        for j in range(ports_num):
            self.dut.send_expect("set link-up port %d" % j, "testpmd>")
        time.sleep(5)
        self.check_ports(status=True)
        self.check_forwarding()

    def test_check_rxtx_desc_status(self):
        """
        Check tx and rx descriptors status.
        When rx_descriptor_status is used, status can be “AVAILABLE”, “DONE” or “UNAVAILABLE”.
        When tx_descriptor_status is used, status can be “FULL”, “DONE” or “UNAVAILABLE.”
        """
        queue_num=16
        if self.nic in ["springville","foxville"]:
            queue_num=4
        if self.nic in ["powerville"]:
            queue_num=8
        self.pmdout.start_testpmd("Default",
                                 "--portmask=%s --port-topology=loop --txq=%s --rxq=%s --txd=4096 --rxd=4096"
                                 % (utils.create_mask(self.ports),queue_num,queue_num), socket=self.ports_socket)

        for i in range(3):
            rxqid = randint(0, queue_num-1)
            self.desc = randint(0, 4095)
            out = self.dut.send_expect("show port %s rxq %s desc %s status" % (self.ports[0], rxqid, self.desc), "testpmd> ")
            self.verify(
                "Desc status = AVAILABLE" in out or "Desc status = DONE" in out or "Desc status = UNAVAILABLE" in out,
                "RX descriptor status is improper")
            self.verify(
                "Bad arguments" not in out and "Invalid queueid" not in out,
                "RX descriptor status is not supported")
            txqid = randint(0, queue_num-1)
            self.desc = randint(0, 511)
            out = self.dut.send_expect("show port %s txq %s desc %s status" % (self.ports[0], txqid, self.desc), "testpmd> ")
            self.verify(
                "Desc status = FULL" in out or "Desc status = DONE" in out or "Desc status = UNAVAILABLE" in out,
                "TX descriptor status is improper")
            self.verify(
                "Bad arguments" not in out and "Invalid queueid" not in out,
                "TX descriptor status is not supported")

    def tear_down(self):
        """
        Run after each test case.
        """
        if self._suite_result.test_case == "test_change_linkspeed_vf":
            self.destroy_vm_env()
        self.dut.kill_all()
        self.pmdout.start_testpmd("Default", "--portmask=%s --port-topology=loop" % utils.create_mask(self.ports),
                                  socket=self.ports_socket)
        ports_num = len(self.ports)
        # link up test, to avoid failing further tests if link was down
        for i in range(ports_num):
            ## sometimes output text messingup testpmd prompt so trimmed prompt
            self.dut.send_expect("set link-up port %d" % i, ">")
        # start ports, to avodi failing further tests if ports are stoped
        self.dut.send_expect("port start all", "testpmd> ", 100)
        self.dut.send_expect("quit", "# ")
             


    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
