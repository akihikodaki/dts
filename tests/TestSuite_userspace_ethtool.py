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
Test support of userspace ethtool feature
"""

import os
import random
import re
import time

import framework.utils as utils
from framework.exception import VerifyFailure
from framework.packet import Packet
from framework.pktgen import PacketGeneratorHelper
from framework.settings import HEADER_SIZE, SCAPY2IXIA
from framework.test_case import TestCase
from framework.utils import RED


class TestUserspaceEthtool(TestCase):

    def set_up_all(self):
        """
        Run at the start of each test suite.
        """
        self.ports = self.dut.get_ports()
        self.verify(len(self.ports) >= 2, "No ports found for " + self.nic)

        # build sample app
        out = self.dut.build_dpdk_apps("examples/ethtool")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

        self.app_ethtool_path = self.dut.apps_name['ethtool']
        used_dut_port_pci = self.dut.ports_info[self.ports[0]]['port'].pci
        out = self.dut.send_expect("cat /sys/bus/pci/devices/%s/numa_node " % used_dut_port_pci, "# ")
        cpu_cores = self.dut.send_expect('lscpu |grep "NUMA node%s CPU(s):"' % out, "# ")
        core = re.findall(r"\d+-(\d+)", cpu_cores)[0]
        core = int(core)
        cores = [core - 1, core - 2, core - 3, core - 4]
        eal_para = self.dut.create_eal_parameters(cores=cores)
        self.cmd = "%s %s" % (self.app_ethtool_path, eal_para)

        # pause frame basic configuration
        self.pause_time = 65535
        self.frame_size = 64
        self.pause_rate = 0.50
        # create an instance to set stream field setting
        self.pktgen_helper = PacketGeneratorHelper()

    def set_up(self):
        """
        Run before each test case.
        """
        pass

    def build_ethtool(self):
        out = self.dut.build_dpdk_apps("examples/ethtool")
        self.verify("Error" not in out, "compilation error 1")
        self.verify("No such file" not in out, "compilation error 2")

    def strip_portstats(self, portid):
        out = self.dut.send_expect("portstats %d " % portid, "EthApp>")
        stats_pattern = r"portstats (\d)(\s+)Port (\d+) stats(\s+)In: (\d+)" \
            " \((\d+) bytes\)(\s+)Out: (\d+) \((\d+) bytes\)" \
            "(\s+)Err: (\d+)"

        m = re.match(stats_pattern, out)
        if m:
            return (int(m.group(5)), int(m.group(8)))
        else:
            return (0, 0)

    def strip_ringparam(self, portid):
        out = self.dut.send_expect("ringparam %d" % portid, "EthApp>")
        ring_pattern = r"ringparam (\d)(\s+)Port (\d+) ring parameters(\s+)" \
            "Rx Pending: (\d+) \((\d+) max\)(\s+)Tx Pending: " \
            "(\d+) \((\d+) max\)"
        m = re.match(ring_pattern, out)
        if m:
            return (int(m.group(5)), int(m.group(6)), int(m.group(8)),
                    int(m.group(9)))
        else:
            return (0, 0, 0, 0)

    def strip_mac(self, portid):
        out = self.dut.send_expect("macaddr %d" % portid, "EthApp>")
        mac_pattern = r"macaddr (\d+)(\s+)Port (\d+) MAC Address: (.*)"
        m = re.match(mac_pattern, out)
        if m:
            return m.group(4)
        else:
            return "00:00:00:00:00:00"

    def strip_mtu(self, intf):
        """
        Strip tester port mtu
        """
        link_info = self.tester.send_expect("ip link show %s" % intf, "# ")
        mtu_pattern = r".* mtu (\d+) .*"
        m = re.match(mtu_pattern, link_info)
        if m:
            return int(m.group(1))
        else:
            return 1518

    def strip_md5(self, filename):
        md5_info = self.dut.send_expect("md5sum %s" % filename, "# ")
        md5_pattern = r"(\w+)  (\w+)"
        m = re.match(md5_pattern, md5_info)
        if m:
            return m.group(1)
        else:
            return ""

    def dpdk_get_nic_info(self, dpdk_driver_msg):
        # get nic driver information using dpdk's ethtool
        info_lines = dpdk_driver_msg.strip().splitlines()
        driver_pattern = r"Port (\d+) driver: (.*) \(ver: (.*)\)"
        pattern = "(.*): (.*)"
        firmwarePat = "0x([0-9a-f]+)"
        check_content = ['firmware-version', 'driver']
        nic_infos = {}
        port = None
        cnt = 0
        while cnt < len(info_lines):
            if not info_lines[cnt]:
                pass
            else:
                m = re.match(driver_pattern, info_lines[cnt])
                if m:
                    port = m.group(1)
                    nic_infos[port] = {}
                    nic_infos[port]['driver'] = m.group(2).split('_').pop()
                    dpdk_version = m.group(3)
                else:
                    if port:
                        out = re.findall(pattern, info_lines[cnt], re.M)[0]
                        if len(out) == 2:
                            if out[0] == 'firmware-version':
                                nic_infos[port][out[0]] = "0x" + re.findall(firmwarePat, out[1], re.M)[0]
                            else:
                                nic_infos[port][out[0]] = out[1]
            cnt += 1
        # check driver content
        status = []
        for port_no in nic_infos:
            nic_info = nic_infos[port_no]
            for item in check_content:
                if item not in list(nic_info.keys()):
                    status.append("port {0} get {1} failed".format(port_no, item))
                    break
        # if there is error in status, clear nic_infos 
        if status:
            msg = os.linesep.join(status)
            nic_infos = None
        else:
            msg = ''
        
        return nic_infos, msg

    def linux_get_nic_info(self, port_name):
        # get nic driver information using linux's ethtool
        pattern = "(.*): (.*)"
        firmwarePat = "0x([0-9a-f]+)"
        infos = self.dut.send_expect("ethtool -i %s"%port_name, "# ").splitlines()
        sys_nic_info = {}
        for info in infos:
            if not info:
                continue
            result = re.findall(pattern, info, re.M)
            if not result:
                continue
            out = result[0]
            if len(out) == 2:
                if out[0] == 'firmware-version':
                    result2 = re.findall(firmwarePat, out[1], re.M)
                    if not result2:
                        msg = ("{} can not get firmware-version,"
                               "ignore left check").format(self.nic)
                        raise VerifyFailure(msg)
                    sys_nic_info[out[0]] = "0x" + result2[0]
                else:
                    sys_nic_info[out[0]] = out[1]
        return sys_nic_info

    def check_driver_info(self, port_name, sys_nic_info, dpdk_drv_info):
        # compare dpdk query nic information with linux query nic information 
        for item, value in list(dpdk_drv_info.items()):
            if item not in list(sys_nic_info.keys()):
                msg = "linux ethtool failed to dump driver info"
                status = False
                break
            if value != sys_nic_info[item]:
                msg = "Userspace ethtool failed to dump driver info"
                status = False
                break
        else:
            msg = "{0}: dpdk ethtool dump nic information done".format(port_name)
            status = True

        return status, msg

    def ethapp_check_link_status(self, port_id, expected_status = 'Up'):
        retries = 0
        reg_str = 'Port\s+{}:\s+(Up|Down)'.format(port_id)
        while retries < 5:
            out = self.dut.send_expect("link", "EthApp> ", 10)
            if out is not None:
                status = re.search(reg_str, out).group(1)
                if status == expected_status:
                    return True
            time.sleep(1)
            retries = retries + 1
        return False

    def test_dump_driver_info(self):
        """
        Test ethtool can dump basic information
        """
        self.dut.send_expect(self.cmd, "EthApp>", 60)
        dpdk_driver_msg = self.dut.send_expect("drvinfo", "EthApp>")
        self.dut.send_expect("quit", "# ")
        dpdk_nic_infos, msg = self.dpdk_get_nic_info(dpdk_driver_msg)
        self.verify(dpdk_nic_infos, msg)
        
        portsinfo = {}
        for index in range(len(self.ports)):
            portsinfo[index] = {}
            portinfo = portsinfo[index]
            port = self.ports[index]
            netdev = self.dut.ports_info[port]['port']
            # strip original driver
            portinfo['ori_driver'] = netdev.get_nic_driver()
            portinfo['net_dev'] = netdev
            # bind to default driver
            netdev.bind_driver()
            # get linux interface
            intf_name = netdev.get_interface_name()
            sys_nic_info = self.linux_get_nic_info(intf_name)
            status, msg = self.check_driver_info(intf_name, sys_nic_info, dpdk_nic_infos[str(index)])
            self.logger.info(msg)
            self.verify(status, msg)

        for index in range(len(self.ports)):
            # bind to original driver
            portinfo = portsinfo[index]
            portinfo['net_dev'].bind_driver(portinfo['ori_driver'])

        self.dut.send_expect(self.cmd, "EthApp>", 60)
        # ethtool doesn't support port disconnect by tools of linux 
        # only detect physical link disconnect status
        verify_pass = True
        verify_msg = ''
        if self.nic.startswith("fortville") == False and self.nic.startswith("columbiaville") == False:
            # check link status dump function
            for port in self.ports:
                tester_port = self.tester.get_local_port(port)
                intf = self.tester.get_interface(tester_port)
                self.tester.send_expect("ip link set dev %s down" % intf, "# ")
            # wait for link stable
            time.sleep(5)
    
            out = self.dut.send_expect("link", "EthApp>", 60)
            link_pattern = r"Port (\d+): (.*)"
            link_infos = out.split("\r\n")
            for link_info in link_infos:
                m = re.match(link_pattern, link_info)
                if m:
                    port = m.group(1)
                    status = m.group(2)
                    # record link down verification result
                    # then continue the test to restore ports link
                    try:
                        self.verify(status == "Down", "Userspace tool failed to detect port %s link down" % port)
                    except VerifyFailure as v:
                        verify_msg += str(v)
                        verify_pass = False

            for port in self.ports:
                tester_port = self.tester.get_local_port(port)
                intf = self.tester.get_interface(tester_port)
                self.tester.send_expect("ip link set dev %s up" % intf, "# ")
            # wait for link stable
            time.sleep(5)

        # check port stats function
        pkt = Packet(pkt_type='UDP')
        for port in self.ports:
            tester_port = self.tester.get_local_port(port)
            intf = self.tester.get_interface(tester_port)
            ori_rx_pkts, ori_tx_pkts = self.strip_portstats(port)
            pkt.send_pkt(self.tester, tx_port=intf, count=4)
            time.sleep(1)
            rx_pkts, tx_pkts = self.strip_portstats(port)
            self.verify((rx_pkts == (ori_rx_pkts + 4)), "Failed to record Rx/Tx packets")

        self.dut.send_expect("quit", "# ")
        # Check port link down verification result
        if verify_pass == False:
            raise VerifyFailure(verify_msg)

    def test_retrieve_reg(self):
        """
        Test ethtool app can retrieve port register
        """
        self.dut.send_expect(self.cmd, "EthApp>", 60)

        portsinfo = []
        ori_drivers = []
        
        for portid in range(len(self.ports)):
            self.dut.send_expect("regs %d regs_%d.bin" % (portid, portid), "EthApp>")
            portinfo = {'portid': portid, 'reg_file': 'regs_%d.bin' % portid}
            portsinfo.append(portinfo)

        self.dut.send_expect("quit", "# ")

        for index in range(len(self.ports)):
            port = self.ports[index]
            netdev = self.dut.ports_info[port]['port']
            portinfo = portsinfo[index]
            # strip original driver
            portinfo['ori_driver'] = netdev.get_nic_driver()
            portinfo['net_dev'] = netdev
            # bind to default driver
            netdev.bind_driver()
            # get linux interface
            intf = netdev.get_interface_name()
            out = self.dut.send_expect("ethtool -d %s raw off file %s" % (intf, portinfo['reg_file']), "# ")
            if "register" not in out or "CTRL" not in out:
                portinfo['net_dev'].bind_driver(portinfo['ori_driver'])
                raise VerifyFailure("Failed to dump %s registers" % intf)

        for index in range(len(self.ports)):
            # bind to original driver
            portinfo = portsinfo[index]
            portinfo['net_dev'].bind_driver(portinfo['ori_driver'])

    def test_retrieve_eeprom(self):
        """
        Test ethtool app dump eeprom function
        """
        # require md5sum to check file
        out = self.dut.send_expect("whereis md5sum", "# ")
        self.verify("/usr/bin/md5sum" in out, "This case required md5sum installed on DUT")

        self.dut.send_expect(self.cmd, "EthApp>", 60)

        portsinfo = []
        ori_drivers = []

        for portid in range(len(self.ports)):
            # dump eeprom by userspace ethtool
            self.dut.send_expect("eeprom %d eeprom_%d.bin" % (portid, portid), "EthApp>")
            portinfo = {'portid': portid, 'eeprom_file': 'eeprom_%d.bin' % portid}
            portsinfo.append(portinfo)

        self.dut.send_expect("quit", "# ")

        for index in range(len(self.ports)):
            port = self.ports[index]
            netdev = self.dut.ports_info[port]['port']
            portinfo = portsinfo[index]
            # strip original driver
            portinfo['ori_driver'] = netdev.get_nic_driver()
            portinfo['net_dev'] = netdev
            # bind to default driver
            netdev.bind_driver()
            # get linux interface
            intf = netdev.get_interface_name()
            ethtool_eeprom = "ethtool_eeprom_%d.bin" % index
            # dump eeprom by linux ethtool
            self.dut.send_expect("ethtool --eeprom-dump %s raw on > %s" % (intf, ethtool_eeprom), "# ")
            # wait for file ready
            time.sleep(2)
            # dpdk userspcae tools dump eeprom file size different with kernel ethtool dump
            dpdk_eeprom_size = int(self.dut.send_expect('stat -c %%s %s' % portinfo['eeprom_file'], '# '))
            self.dut.send_expect('dd if=%s of=%s bs=%d count=1' % (ethtool_eeprom, "ethtool_eeprom_%d_cat.bin" % index, dpdk_eeprom_size), "#")
            portinfo['ethtool_eeprom'] = "ethtool_eeprom_%d_cat.bin" % index
            # bind to original driver
            portinfo['net_dev'].bind_driver(portinfo['ori_driver'])

        for index in range(len(self.ports)):
            md5 = self.strip_md5(portsinfo[index]['eeprom_file'])
            md5_ref = self.strip_md5(portsinfo[index]['ethtool_eeprom'])
            print(utils.GREEN("Reference eeprom md5 %s" % md5))
            print(utils.GREEN("Reference eeprom md5_ref %s" % md5_ref))
            self.verify(md5 == md5_ref, "Dumped eeprom not same as linux dumped")

    def test_ring_parameter(self):
        """
        Test ethtool app ring parameter getting and setting
        """
        for index in range(len(self.ports)):
            self.dut.send_expect(self.cmd, "EthApp>", 60)
            port = self.ports[index]
            ori_rx_pkts, ori_tx_pkts = self.strip_portstats(port)
            _, rx_max, _, tx_max = self.strip_ringparam(index)
            self.dut.send_expect("ringparam %d %d %d" % (index, tx_max, rx_max), "EthApp>")
            rx_ring, _, tx_ring, _ = self.strip_ringparam(index)
            self.verify(rx_ring == rx_max, "Userspace tool failed to set Rx ring parameter")
            self.verify(tx_ring == tx_max, "Userspace tool failed to set Tx ring parameter")
            pkt = Packet(pkt_type='UDP')
            tester_port = self.tester.get_local_port(port)
            self.verify(self.ethapp_check_link_status(index, 'Up') == True,
                    'Fail to Open port{}'.format(index))

            intf = self.tester.get_interface(tester_port)
            pkt.send_pkt(self.tester, tx_port=intf, count=4)
            rx_pkts, tx_pkts = self.strip_portstats(index)
            self.verify(rx_pkts == ori_rx_pkts + 4, "Failed to forward after ring parameter changed")
            self.dut.send_expect("quit", "# ")

    def test_mac_address(self):
        """
        Test ethtool app mac function
        """
        valid_mac = "00:10:00:00:00:00"
        self.dut.send_expect(self.cmd, "EthApp>", 60)
        for index in range(len(self.ports)):
            port = self.ports[index]
            mac = self.dut.ports_info[port]['mac']
            dump_mac = self.strip_mac(index)
            self.verify(mac.lower() == dump_mac.lower(), "Userspace tool failed to dump mac")
            self.dut.send_expect("macaddr %d %s" % (port, valid_mac), "EthApp>")
            dump_mac = self.strip_mac(index)
            self.verify(dump_mac == valid_mac, "Userspace tool failed to set mac")
            # check forwarded mac has been changed
            pkt = Packet(pkt_type='UDP')
            tester_port = self.tester.get_local_port(port)
            intf = self.tester.get_interface(tester_port)
            self.verify(self.ethapp_check_link_status(index, 'Up') == True,
                    'Fail to Open port{}'.format(index))
            # send and sniff packet
            inst = self.tester.tcpdump_sniff_packets(intf)
            pkt.send_pkt(self.tester, tx_port=intf, count=4)
            pkts = self.tester.load_tcpdump_sniff_packets(inst, timeout=3)
            self.verify(len(pkts) == 4, "Packet not forwarded as expected")
            src_mac = pkts.strip_layer_element("layer2", "src", p_index=0)
            self.verify(src_mac == valid_mac, "Forwarded packet not match default mac")

        # check multicast will not be valid mac
        invalid_mac = "01:00:00:00:00:00"
        out = self.dut.send_expect("validate %s" % invalid_mac, "EthApp>")
        self.verify("not unicast" in out, "Failed to detect incorrect unicast mac")
        invalid_mac = "00:00:00:00:00:00"
        out = self.dut.send_expect("validate %s" % invalid_mac, "EthApp>")
        self.verify("not unicast" in out, "Failed to detect incorrect unicast mac")
        out = self.dut.send_expect("validate %s" % valid_mac, "EthApp>")
        self.verify("is unicast" in out, "Failed to detect correct unicast mac")
        self.dut.send_expect("quit", "# ")

    def test_port_config(self):
        """
        Test ethtool app port configure
        """
        self.dut.send_expect(self.cmd, "EthApp>", 60)
        for index in range(len(self.ports)):
            port = self.ports[index]
            ori_rx_pkts, _ = self.strip_portstats(index)
            # add sleep time for update link status with fortville nic
            time.sleep(10)
            # stop port
            self.dut.send_expect("stop %d" % index, "EthApp>")
            # about columbiaville_25g(8086:1593),there have a kernel driver link status issue
            # about Sageville(8086:1563),driver do not write register to set link-down
            # so skip this step of verify status
            if self.nic not in ['columbiaville_25g', 'sageville', 'columbiaville_100g']:
                self.verify(self.ethapp_check_link_status(index, 'Down') == True,
                           'Fail to stop port{}'.format(index))
            # check packet not forwarded when port is stop
            pkt = Packet(pkt_type='UDP')
            tester_port = self.tester.get_local_port(port)
            intf = self.tester.get_interface(tester_port)
            pkt.send_pkt(self.tester, tx_port=intf, count=4)
            rx_pkts, tx_pkts = self.strip_portstats(index)
            self.verify(rx_pkts == ori_rx_pkts, "Failed to stop port")
            # restart port and check packet can normally forwarded
            self.dut.send_expect("open %d" % index, "EthApp>")
            self.verify(self.ethapp_check_link_status(index, 'Up') == True,
                         'Fail to Open port{}'.format(index))
            # wait few time for port ready
            rx_pkts, tx_pkts = self.strip_portstats(index)
            pkt.send_pkt(self.tester, tx_port=intf, count=4)
            rx_pkts_open, tx_pkts_open = self.strip_portstats(index)
            self.verify(rx_pkts_open == rx_pkts + 4, "Failed to reopen port rx")
            self.verify(tx_pkts_open == tx_pkts + 4, "Failed to reopen port tx")

        self.dut.send_expect("quit", "# ")

    def test_port_mtu(self):
        """
        Test ethtool app port mtu configure
        """
        self.dut.send_expect(self.cmd, "EthApp>", 60)
        mtus = [1519, 2048]
        mtu_threshold = 2022
        offset = 0
        if self.nic in ['powerville', 'springville', 'foxville']:
            mtu_threshold = 2026
            offset = 4
        # RTE_ETHER_HDR_LEN + RTE_ETHER_CRC_LEN + ICE_VLAN_TAG_SIZE * 2
        if self.nic in ["columbiaville_25g","columbiaville_100g"]:
            offset = 8
        for index in range(len(self.ports)):
            port = self.ports[index]
            # change mtu
            tester_port = self.tester.get_local_port(port)
            intf = self.tester.get_interface(tester_port)
            ori_mtu = self.strip_mtu(intf)
            self.tester.send_expect("ifconfig %s mtu 9000" % (intf), "# ")
            for mtu in mtus:
                # cvl should stop port before set mtu
                if self.nic in ["columbiaville_25g","columbiaville_100g"]:
                    self.dut.send_expect("stop %s" % index, "EthApp>")

                # The mtu threshold is 2022,When it is greater than 2022, the open/stop port is required.
                if mtu > mtu_threshold:
                    if self.nic in ['powerville', 'springville', 'foxville']:
                        mtu = mtu_threshold
                    self.dut.send_expect("stop %s" % index, "EthApp>")
                    self.dut.send_expect("mtu %d %d" % (index, mtu), "EthApp>")
                    self.dut.send_expect("open %s" % index, "EthApp>")
                self.dut.send_expect("mtu %d %d" % (index, mtu), "EthApp>")

                if self.nic in ["columbiaville_25g","columbiaville_100g"]:
                    self.dut.send_expect("open %s" % index, "EthApp>")

                time.sleep(5)
                ori_rx_pkts, _ = self.strip_portstats(index)
                pkt_size = mtu + HEADER_SIZE['eth'] + offset
                pkt = Packet(pkt_type='UDP', pkt_len=pkt_size)
                pkt.send_pkt(self.tester, tx_port=intf, count=4)
                rx_pkts, _ = self.strip_portstats(index)
                self.verify(rx_pkts == ori_rx_pkts + 4, "Packet match mtu not forwarded as expected")
                if (self.nic in ["cavium_a063","cavium_a064"]):
                    pkt = Packet(pkt_type='UDP', pkt_len=mtu + 9 + HEADER_SIZE['eth'] + offset)
                else:
                    pkt = Packet(pkt_type='UDP', pkt_len=mtu + 1 + HEADER_SIZE['eth'] + offset)
                pkt.send_pkt(self.tester, tx_port=intf, count=4)
                rx_pkts_over, _ = self.strip_portstats(index)
                self.verify(rx_pkts == rx_pkts_over, "Packet over mtu should not be forwarded")

            self.tester.send_expect("ifconfig %s mtu %d" % (intf, ori_mtu), "# ")

        self.dut.send_expect("quit", "# ")

    def test_perf_port_tx_pause(self):
        """
        Test ethtool app flow control configure
        """
        # sleep a while when receive packets
        main_file = "examples/ethtool/ethtool-app/main.c"
        self.dut.send_expect("sed -i -e '/if (cnt_recv_frames > 0) {$/i\\usleep(10);' %s" % main_file, "# ")
        # build sample app
        self.build_ethtool()
        self.dut.send_expect(self.cmd, "EthApp>", 60)
        # enable pause tx
        self.dut.send_expect("pause 0 tx", "EthApp")

        tgen_input = []
        headers_size = HEADER_SIZE['eth'] + HEADER_SIZE['ip'] + \
            HEADER_SIZE['udp']
        payload_size = self.frame_size - headers_size
        dst_mac =  self.dut.get_mac_address(0)
        self.tester.scapy_append(
            'wrpcap("/root/pause_tx.pcap", [Ether(dst="%s")/IP()/UDP()/("X"*%d)])' % (dst_mac, payload_size))
        self.tester.scapy_execute()
        # rx and tx is the same port
        tester_port = self.tester.get_local_port(self.ports[0])
        tgen_input.append((tester_port, tester_port, "/root/pause_tx.pcap"))

        # run traffic generator
        streams = self.pktgen_helper.prepare_stream_from_tginput(tgen_input, 100,
                                        None, self.tester.pktgen)
        traffic_opt = {'throughput_stat_flag': True}
        loss, rx_throughput  = self.tester.pktgen._measure_loss(
            stream_ids=streams, options=traffic_opt)
        tx_pps = rx_throughput[1]
        sent_pkts, recv_pkts = list(loss.values())[0][1:]
        self.dut.send_expect("quit", "# ")
        self.dut.send_expect("sed -i -e '/usleep(10);$/d' %s" % main_file, "# ")
        # rebuild sample app
        self.build_ethtool()
        # verify ixia transmit line rate dropped
        pps = self.wirespeed(self.nic, self.frame_size, 1) * 1000000.0
        rate = tx_pps / pps
        self.verify(rate < 0.1, "Failed to slow down transmit speed")
        # verify received packets more than sent
        self.verify((float(recv_pkts) / float(sent_pkts)) > 1.05, "Failed to transmit pause frame")

    def tear_down(self):
        """
        Run after each test case.
        """
        self.dut.kill_all()
        pass

    def tear_down_all(self):
        """
        Run after each test suite.
        """
        self.dut.kill_all()
