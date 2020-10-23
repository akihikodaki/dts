# BSD LICENSE
#
# Copyright(c) 2010-2019 Intel Corporation. All rights reserved.
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
Interface for bulk traffic generators.
"""

import re
import subprocess
import os
from time import sleep
from settings import NICS, load_global_setting, PERF_SETTING
from settings import IXIA, USERNAME, PKTGEN, PKTGEN_GRP
from crb import Crb
from net_device import GetNicObj
from etgen import IxiaPacketGenerator, SoftwarePacketGenerator
import random
from utils import (GREEN, convert_int2ip, convert_ip2int,
                   check_crb_python_version)
from exception import ParameterInvalidException
from multiprocessing import Process
from pktgen import getPacketGenerator
from config import PktgenConf
from packet import SCAPY_IMP_CMD

class Tester(Crb):

    """
    Start the DPDK traffic generator on the machine `target`.
    A config file and pcap file must have previously been copied
    to this machine.
    """
    PORT_INFO_CACHE_KEY = 'tester_port_info'
    CORE_LIST_CACHE_KEY = 'tester_core_list'
    NUMBER_CORES_CACHE_KEY = 'tester_number_cores'
    PCI_DEV_CACHE_KEY = 'tester_pci_dev_info'

    def __init__(self, crb, serializer):
        self.NAME = 'tester'
        self.scapy_session = None
        super(Tester, self).__init__(crb, serializer, self.NAME)
        # check the python version of tester
        check_crb_python_version(self)

        self.bgProcIsRunning = False
        self.duts = None
        self.inBg = 0
        self.scapyCmds = []
        self.bgCmds = []
        self.bgItf = ''
        self.re_run_time = 0
        self.pktgen = None
        self.ixia_packet_gen = None
        self.tmp_scapy_module_dir = '/tmp/dep'
        # prepare for scapy env
        self.scapy_sessions_li = list()
        self.scapy_session = self.prepare_scapy_env()
        self.tmp_file = '/tmp/tester/'
        out = self.send_expect('ls -d %s' % self.tmp_file, '# ', verify=True)
        if out == 2:
            self.send_expect('mkdir -p %s' % self.tmp_file, '# ')

    def prepare_scapy_env(self):
        session_name = 'tester_scapy' if not self.scapy_sessions_li else f'tester_scapy_{random.random()}'
        session = self.create_session(session_name)
        self.scapy_sessions_li.append(session)
        session.send_expect('scapy', '>>> ')
        file_dir = os.path.dirname(__file__).split(os.path.sep)
        lib_path = os.path.sep.join(file_dir[:-1]) + '/dep/scapy_modules/'
        exists_flag = self.alt_session.session.send_expect(f'ls {self.tmp_scapy_module_dir}', '# ', verify=True)
        if exists_flag == 2:
            self.alt_session.session.send_expect(f'mkdir -p {self.tmp_scapy_module_dir}', '# ', verify=True)
        scapy_modules_path = [lib_path+i for i in os.listdir(lib_path) if i.endswith('.py')]
        path = ' '.join(scapy_modules_path)
        session.copy_file_to(src=path, dst=self.tmp_scapy_module_dir)
        session.session.send_expect(f"sys.path.append('{self.tmp_scapy_module_dir}')", ">>> ")

        out = session.session.send_expect(SCAPY_IMP_CMD, '>>> ')
        if 'ImportError' in out:
            session.logger.warning(f'entering import error: {out}')
        return session

    def init_ext_gen(self):
        """
        Initialize tester packet generator object.
        """
        if self.it_uses_external_generator():
            if self.is_pktgen:
                self.pktgen_init()
            else:
                self.ixia_packet_gen = IxiaPacketGenerator(self)
            return
        self.packet_gen = SoftwarePacketGenerator(self)

    def set_re_run(self, re_run_time):
        """
        set failed case re-run time
        """
        self.re_run_time = int(re_run_time)

    def get_ip_address(self):
        """
        Get ip address of tester CRB.
        """
        return self.crb['tester IP']
 
    def get_username(self):
        """
        Get login username of tester CRB.
        """
        return USERNAME

    def get_password(self):
        """
        Get tester login password of tester CRB.
        """
        return self.crb['tester pass']

    @property
    def is_pktgen(self):
        """
        Check whether packet generator is configured.
        """
        if PKTGEN not in self.crb or not self.crb[PKTGEN]:
            return False

        if self.crb[PKTGEN].lower() in PKTGEN_GRP:
            return True
        else:
            msg = os.linesep.join([
            "Packet generator <{0}> is not supported".format(self.crb[PKTGEN]),
            "Current supports: {0}".format(' | '.join(PKTGEN_GRP))])
            self.logger.info(msg)
            return False 

    def has_external_traffic_generator(self):
        """
        Check whether performance test will base on IXIA equipment.
        """
        try:
            # if pktgen_group is set, take pktgen config file as first selection
            if self.is_pktgen:
                return True 
            elif self.crb[IXIA] is not None:
                return True
        except Exception as e:
            return False

        return False

    def get_external_traffic_generator(self):
        """
        Return IXIA object.
        """
        return self.crb[IXIA]

    def it_uses_external_generator(self):
        """
        Check whether IXIA generator is ready for performance test.
        """
        return load_global_setting(PERF_SETTING) == 'yes' and self.has_external_traffic_generator()

    def tester_prerequisites(self):
        """
        Prerequest function should be called before execute any test case.
        Will call function to scan all lcore's information which on Tester.
        Then call pci scan function to collect nic device information.
        Then discovery the network topology and save it into cache file.
        At last setup DUT' environment for validation.
        """
        self.init_core_list()
        self.pci_devices_information()
        self.restore_interfaces()
        self.scan_ports()

        self.disable_lldp()

    def disable_lldp(self):
        """
        Disable tester ports LLDP.
        """
        result = self.send_expect("lldpad -d",  "# ")
        if result:
            self.logger.error(result.strip())

        for port in self.ports_info:
            if not "intf" in list(port.keys()):
                continue
            eth = port["intf"]
            out = self.send_expect("ethtool --show-priv-flags %s"
                    % eth, "# ", alt_session=True)
            if "disable-fw-lldp" in out:
                self.send_expect("ethtool --set-priv-flags %s disable-fw-lldp on"
                        % eth, "# ", alt_session=True)
            self.send_expect("lldptool set-lldp -i %s adminStatus=disabled"
                    % eth, "# ", alt_session=True)

    def get_local_port(self, remotePort):
        """
        Return tester local port connect to specified dut port.
        """
        return self.duts[0].ports_map[remotePort]

    def get_local_port_type(self, remotePort):
        """
        Return tester local port type connect to specified dut port.
        """
        return self.ports_info[self.get_local_port(remotePort)]['type']

    def get_local_port_bydut(self, remotePort, dutIp):
        """
        Return tester local port connect to specified port and specified dut.
        """
        for dut in self.duts:
            if dut.crb['My IP'] == dutIp:
                return dut.ports_map[remotePort]

    def get_local_index(self, pci):
        """
        Return tester local port index by pci id
        """
        index = -1
        for port in self.ports_info:
            index += 1
            if pci == port['pci']:
                return index
        return -1

    def get_pci(self, localPort):
        """
        Return tester local port pci id.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        return self.ports_info[localPort]['pci']

    def get_interface(self, localPort):
        """
        Return tester local port interface name.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        if 'intf' not in self.ports_info[localPort]:
            return 'N/A'

        return self.ports_info[localPort]['intf']

    def get_mac(self, localPort):
        """
        Return tester local port mac address.
        """
        if localPort == -1:
            raise ParameterInvalidException("local port should not be -1")

        if self.ports_info[localPort]['type'] in ('ixia', 'trex'):
            return "00:00:00:00:00:01"
        else:
            return self.ports_info[localPort]['mac']

    def get_port_status(self, port):
        """
        Return link status of ethernet.
        """
        eth = self.ports_info[port]['intf']
        out = self.send_expect("ethtool %s" % eth, "# ")

        status = re.search(r"Link detected:\s+(yes|no)", out)
        if not status:
            self.logger.error("ERROR: unexpected output")

        if status.group(1) == 'yes':
            return 'up'
        else:
            return 'down'

    def restore_interfaces(self):
        """
        Restore Linux interfaces.
        """
        if self.skip_setup:
            return

        self.send_expect("modprobe igb", "# ", 20)
        self.send_expect("modprobe ixgbe", "# ", 20)
        self.send_expect("modprobe e1000e", "# ", 20)
        self.send_expect("modprobe e1000", "# ", 20)

        try:
            for (pci_bus, pci_id) in self.pci_devices_info:
                addr_array = pci_bus.split(':')
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                itf = port.get_interface_name()
                self.enable_ipv6(itf)
                self.send_expect("ifconfig %s up" % itf, "# ")
                if port.get_interface2_name():
                    itf = port.get_interface2_name()
                    self.enable_ipv6(itf)
                    self.send_expect("ifconfig %s up" % itf, "# ")

        except Exception as e:
            self.logger.error("   !!! Restore ITF: " + e.message)

        sleep(2)

    def restore_trex_interfaces(self):
        """
        Restore Linux interfaces used by trex
        """
        try:
            for port_info in self.ports_info:
                nic_type = port_info.get('type') 
                if nic_type is not 'trex':
                    continue
                pci_bus = port_info.get('pci')
                port_inst = port_info.get('port')
                port_inst.bind_driver()
                itf = port_inst.get_interface_name()
                self.enable_ipv6(itf)
                self.send_expect("ifconfig %s up" % itf, "# ")
                if port_inst.get_interface2_name():
                    itf = port_inst.get_interface2_name()
                    self.enable_ipv6(itf)
                    self.send_expect("ifconfig %s up" % itf, "# ")
        except Exception as e:
            self.logger.error("   !!! Restore ITF: " + e.message)

        sleep(2)

    def set_promisc(self):
        try:
            for (pci_bus, pci_id) in self.pci_devices_info:
                addr_array = pci_bus.split(':')
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                itf = port.get_interface_name()
                self.enable_promisc(itf)
                if port.get_interface2_name():
                    itf = port.get_interface2_name()
                    self.enable_promisc(itf)
        except Exception as e:
            pass


    def load_serializer_ports(self):
        cached_ports_info = self.serializer.load(self.PORT_INFO_CACHE_KEY)
        if cached_ports_info is None:
            return

        # now not save netdev object, will implemented later
        self.ports_info = cached_ports_info

    def save_serializer_ports(self):
        cached_ports_info = []
        for port in self.ports_info:
            port_info = {}
            for key in list(port.keys()):
                if type(port[key]) is str:
                    port_info[key] = port[key]
                # need save netdev objects
            cached_ports_info.append(port_info)
        self.serializer.save(self.PORT_INFO_CACHE_KEY, cached_ports_info)

    def _scan_pktgen_ports(self):
        ''' packet generator port setting 
        Currently, trex run on tester node
        '''
        new_ports_info = []
        pktgen_ports_info = self.pktgen.get_ports()
        for pktgen_port_info in pktgen_ports_info:
            pktgen_port_type = pktgen_port_info['type']
            if pktgen_port_type.lower() == 'ixia':
                self.ports_info.extend(pktgen_ports_info)
                break
            pktgen_port_name = pktgen_port_info['intf']
            pktgen_pci = pktgen_port_info['pci']
            pktgen_mac = pktgen_port_info['mac']
            for port_info in self.ports_info:
                dts_pci = port_info['pci']
                if dts_pci != pktgen_pci:
                    continue
                port_info['intf'] = pktgen_port_name
                port_info['type'] = pktgen_port_type
                port_info['mac'] = pktgen_mac
                break
            # Since tester port scanning work flow change, non-functional port 
            # mapping config will be ignored. Add tester port mapping if no
            # port in ports info 
            else:
                addr_array = pktgen_pci.split(':')
                port = GetNicObj(self, addr_array[0], addr_array[1], addr_array[2])
                new_ports_info.append({
                    'port': port,
                    'intf': pktgen_port_name,
                    'type': pktgen_port_type,
                    'pci': pktgen_pci,
                    'mac': pktgen_mac,
                    'ipv4': None,
                    'ipv6': None })
        if new_ports_info:
            self.ports_info = self.ports_info + new_ports_info

    def scan_ports(self):
        """
        Scan all ports on tester and save port's pci/mac/interface.
        """
        if self.read_cache:
            self.load_serializer_ports()
            self.scan_ports_cached()

        if not self.read_cache or self.ports_info is None:
            self.scan_ports_uncached()
            if self.it_uses_external_generator():
                if self.is_pktgen:
                    self._scan_pktgen_ports()
                else:
                    self.ports_info.extend(self.ixia_packet_gen.get_ports())
            self.save_serializer_ports()

        for port_info in self.ports_info:
            self.logger.info(port_info)

    def scan_ports_cached(self):
        if self.ports_info is None:
            return

        for port_info in self.ports_info:
            if port_info['type'].lower() in ('ixia', 'trex'):
                continue

            addr_array = port_info['pci'].split(':')
            domain_id = addr_array[0]
            bus_id = addr_array[1]
            devfun_id = addr_array[2]

            port = GetNicObj(self, domain_id, bus_id, devfun_id)
            intf = port.get_interface_name()

            self.logger.info("Tester cached: [000:%s %s] %s" % (
                             port_info['pci'], port_info['type'], intf))
            port_info['port'] = port

    def scan_ports_uncached(self):
        """
        Return tester port pci/mac/interface information.
        """
        self.ports_info = []

        for (pci_bus, pci_id) in self.pci_devices_info:
            # ignore unknown card types
            if pci_id not in list(NICS.values()):
                self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id,
                                                             "unknow_nic"))
                continue

            addr_array = pci_bus.split(':')
            domain_id = addr_array[0]
            bus_id = addr_array[1]
            devfun_id = addr_array[2]

            port = GetNicObj(self, domain_id, bus_id, devfun_id)
            intf = port.get_interface_name()

            if "No such file" in intf:
                self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id,
                                                             "unknow_interface"))
                continue

            self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id, intf))
            macaddr = port.get_mac_addr()

            ipv6 = port.get_ipv6_addr()
            ipv4 = port.get_ipv4_addr()

            # store the port info to port mapping
            self.ports_info.append({'port': port,
                                    'pci': pci_bus,
                                    'type': pci_id,
                                    'intf': intf,
                                    'mac': macaddr,
                                    'ipv4': ipv4,
                                    'ipv6': ipv6})

            # return if port is not connect x3
            if not port.get_interface2_name():
                continue

            intf = port.get_interface2_name()

            self.logger.info("Tester: [%s %s] %s" % (pci_bus, pci_id, intf))
            macaddr = port.get_intf2_mac_addr()

            ipv6 = port.get_ipv6_addr()

            # store the port info to port mapping
            self.ports_info.append({'port': port,
                                    'pci': pci_bus,
                                    'type': pci_id,
                                    'intf': intf,
                                    'mac': macaddr,
                                    'ipv6': ipv6})

    def pktgen_init(self):
        '''
        initialize packet generator instance
        '''
        pktgen_type = self.crb[PKTGEN]
        # init packet generator instance
        self.pktgen = getPacketGenerator(self, pktgen_type)
        # prepare running environment
        self.pktgen.prepare_generator()

    def send_ping(self, localPort, ipv4, mac):
        """
        Send ping4 packet from local port with destination ipv4 address.
        """
        if self.ports_info[localPort]['type'].lower() in ('ixia', 'trex'):
            return "Not implemented yet"
        else:
            return self.send_expect("ping -w 5 -c 5 -A -I %s %s" % (self.ports_info[localPort]['intf'], ipv4), "# ", 10)

    def send_ping6(self, localPort, ipv6, mac):
        """
        Send ping6 packet from local port with destination ipv6 address.
        """
        if self.is_pktgen:
            if self.ports_info[localPort]['type'].lower() in 'ixia':
                return self.pktgen.send_ping6(
                                self.ports_info[localPort]['pci'], mac, ipv6)
            elif self.ports_info[localPort]['type'].lower() == 'trex':
                return "Not implemented yet"
        elif self.ports_info[localPort]['type'].lower() in 'ixia':
            return self.ixia_packet_gen.send_ping6(self.ports_info[localPort]['pci'], mac, ipv6)
        else:
            return self.send_expect("ping6 -w 5 -c 5 -A %s%%%s" % (ipv6, self.ports_info[localPort]['intf']), "# ", 10)

    def get_port_numa(self, port):
        """
        Return tester local port numa.
        """
        pci = self.ports_info[port]['pci']
        out = self.send_expect("cat /sys/bus/pci/devices/%s/numa_node" % pci, "#")
        return int(out)

    def check_port_list(self, portList, ftype='normal'):
        """
        Check specified port is IXIA port or normal port.
        """
        dtype = None
        plist = set()
        for txPort, rxPort, _ in portList:
            plist.add(txPort)
            plist.add(rxPort)

        plist = list(plist)
        if len(plist) > 0:
            dtype = self.ports_info[plist[0]]['type']

        for port in plist[1:]:
            if dtype != self.ports_info[port]['type']:
                return False

        if ftype == 'ixia' and dtype != ftype:
            return False

        return True

    def scapy_append(self, cmd):
        """
        Append command into scapy command list.
        """
        self.scapyCmds.append(cmd)

    def scapy_execute(self, timeout=60):
        """
        Execute scapy command list.
        """
        self.kill_all()

        self.send_expect("scapy", ">>> ")
        if self.bgProcIsRunning:
            self.send_expect('subprocess.call("scapy -c sniff.py &", shell=True)', ">>> ")
            self.bgProcIsRunning = False
        sleep(2)

        for cmd in self.scapyCmds:
            self.send_expect(cmd, ">>> ", timeout)

        sleep(2)
        self.scapyCmds = []
        self.send_expect("exit()", "# ", timeout)

    def scapy_background(self):
        """
        Configure scapy running in background mode which mainly purpose is
        that save RESULT into scapyResult.txt.
        """
        self.inBg = True

    def scapy_foreground(self):
        """
        Running background scapy and convert to foreground mode.
        """
        self.send_expect("echo -n '' >  scapyResult.txt", "# ")
        if self.inBg:
            self.scapyCmds.append('f = open(\'scapyResult.txt\',\'w\')')
            self.scapyCmds.append('f.write(RESULT)')
            self.scapyCmds.append('f.close()')
            self.scapyCmds.append('exit()')

            outContents = "import os\n" + \
                'conf.color_theme=NoTheme()\n' + 'RESULT=""\n' + \
                "\n".join(self.scapyCmds) + "\n"
            self.create_file(outContents, 'sniff.py')

            self.logger.info('SCAPY Receive setup:\n' + outContents)

            self.bgProcIsRunning = True
            self.scapyCmds = []
        self.inBg = False

    def scapy_get_result(self):
        """
        Return RESULT which saved in scapyResult.txt.
        """
        out = self.send_expect("cat scapyResult.txt", "# ")
        self.logger.info('SCAPY Result:\n' + out + '\n\n\n')

        return out

    def traffic_generator_throughput(self, portList, rate_percent=100, delay=5):
        """
        Run throughput performance test on specified ports.
        """
        if self.check_port_list(portList, 'ixia'):
            return self.ixia_packet_gen.throughput(portList, rate_percent, delay)
        if not self.check_port_list(portList):
            self.logger.warning("exception by mixed port types")
            return None
        return self.packet_gen.throughput(portList, rate_percent)

    def verify_packet_order(self, portList, delay):
        if self.check_port_list(portList, 'ixia'):
            return self.ixia_packet_gen.is_packet_ordered(portList, delay)
        else:
            self.logger.warning("Only ixia port support check verify packet order function")
            return False

    def run_rfc2544(self, portlist, delay=120, permit_loss_rate=0):
        """
        test_rate: the line rate we are going to test.
        """
        test_rate = float(100)

        self.logger.info("test rate: %f " % test_rate)
        loss_rate, tx_num, rx_num = self.traffic_generator_loss(portlist, test_rate, delay)
        while loss_rate > permit_loss_rate:
                test_rate = float(1 - loss_rate) * test_rate
                loss_rate, tx_num, rx_num = self.traffic_generator_loss(portlist, test_rate, delay)

        self.logger.info("zero loss rate is %s" % test_rate)
        return test_rate, tx_num, rx_num


    def traffic_generator_loss(self, portList, ratePercent, delay=60):
        """
        Run loss performance test on specified ports.
        """
        if self.check_port_list(portList, 'ixia'):
            return self.ixia_packet_gen.loss(portList, ratePercent, delay)
        elif not self.check_port_list(portList):
            self.logger.warning("exception by mixed port types")
            return None
        return self.packet_gen.loss(portList, ratePercent)

    def traffic_generator_latency(self, portList, ratePercent=100, delay=5):
        """
        Run latency performance test on specified ports.
        """
        if self.check_port_list(portList, 'ixia'):
            return self.ixia_packet_gen.latency(portList, ratePercent, delay)
        else:
            return None

    def parallel_transmit_ptks(self, pkt=None, intf='', send_times=1, interval=0.01):
        """
        Callable function for parallel processes
        """
        print(GREEN("Transmitting and sniffing packets, please wait few minutes..."))
        return pkt.send_pkt_bg_with_pcapfile(crb=self, tx_port=intf, count=send_times, loop=0, inter=interval)

    def check_random_pkts(self, portList, pktnum=2000, interval=0.01, allow_miss=True, seq_check=False, params=None):
        """
        Send several random packets and check rx packets matched
        """
        # load functions in packet module
        module = __import__("packet")
        pkt_c = getattr(module, "Packet")
        compare_f = getattr(module, "compare_pktload")
        strip_f = getattr(module, "strip_pktload")
        tx_pkts = {}
        rx_inst = {}
        # packet type random between tcp/udp/ipv6
        random_type = ['TCP', 'UDP', 'IPv6_TCP', 'IPv6_UDP']
        for txport, rxport in portList:
            txIntf = self.get_interface(txport)
            rxIntf = self.get_interface(rxport)
            self.logger.info(GREEN("Preparing transmit packets, please wait few minutes..."))
            pkt = pkt_c()
            pkt.generate_random_pkts(pktnum=pktnum, random_type=random_type, ip_increase=True, random_payload=True,
                                     options={"layers_config": params})

            tx_pkts[txport] = pkt
            # sniff packets
            inst = module.start_tcpdump(self, rxIntf, count=pktnum,
                                        filters=[{'layer': 'network', 'config': {'srcport': '65535'}},
                                                 {'layer': 'network', 'config': {'dstport': '65535'}}])
            rx_inst[rxport] = inst
        bg_sessions = list()
        for txport, _ in portList:
            txIntf = self.get_interface(txport)
            bg_sessions.append(self.parallel_transmit_ptks(pkt=tx_pkts[txport], intf=txIntf, send_times=1, interval=interval))
        # Verify all packets
        sleep(interval * pktnum + 1)
        timeout = 60
        for i in bg_sessions:
            while timeout:
                try:
                    i.send_expect('', '>>> ', timeout=1)
                except Exception as e:
                    print(e)
                    self.logger.info('wait for the completion of sending pkts...')
                    timeout -= 1
                    continue
                else:
                    break
            else:
                self.logger.info('exceeded timeout, force to stop background packet sending to avoid dead loop')
                pkt_c.stop_send_pkt_bg(i)
        prev_id = -1
        for txport, rxport in portList:
            p = module.stop_and_load_tcpdump_packets(rx_inst[rxport])
            recv_pkts = p.pktgen.pkts
            # only report when received number not matched
            if len(tx_pkts[txport].pktgen.pkts) > len(recv_pkts):
                self.logger.info(("Pkt number not matched,%d sent and %d received\n" % (
                len(tx_pkts[txport].pktgen.pkts), len(recv_pkts))))
                if allow_miss is False:
                    return False

            # check each received packet content
            self.logger.info(GREEN("Comparing sniffed packets, please wait few minutes..."))
            for idx in range(len(recv_pkts)):
                try:
                    l3_type = p.strip_element_layer2('type', p_index=idx)
                    sip = p.strip_element_layer3('dst', p_index=idx)
                except Exception as e:
                    continue
                # ipv4 packet
                if l3_type == 2048:
                    t_idx = convert_ip2int(sip, 4)
                # ipv6 packet
                elif l3_type == 34525:
                    t_idx = convert_ip2int(sip, 6)
                else:
                    continue

                if seq_check:
                    if t_idx <= prev_id:
                        self.logger.info("Packet %d sequence not correct" % t_idx)
                        return False
                    else:
                        prev_id = t_idx

                if compare_f(tx_pkts[txport].pktgen.pkts[idx], recv_pkts[idx], "L4") is False:
                    self.logger.warning("Pkt received index %d not match original " \
                          "index %d" % (idx, idx))
                    self.logger.info("Sent: %s" % strip_f(tx_pkts[txport].pktgen.pkts[idx], "L4"))
                    self.logger.info("Recv: %s" % strip_f(recv_pkts[idx], "L4"))
                    return False

        return True

    def extend_external_packet_generator(self, clazz, instance):
        """
        Update packet generator function, will implement later.
        """
        # packet generator has forbidden suite class to override parent class methods  
        if self.is_pktgen:
            return
        # discard this in future
        if self.it_uses_external_generator():
            self.ixia_packet_gen.__class__ = clazz
            current_attrs = instance.__dict__
            instance.__dict__ = self.ixia_packet_gen.__dict__
            instance.__dict__.update(current_attrs)

    def tcpdump_sniff_packets(self, intf, count=0, filters=None, lldp_forbid=True):
        """
        Wrapper for packet module sniff_packets
        """
        # load functions in packet module
        packet = __import__("packet")
        inst = packet.start_tcpdump(self, intf=intf, count=count, filters=filters, lldp_forbid=lldp_forbid)
        return inst

    def load_tcpdump_sniff_packets(self, index='', timeout=1):
        """
        Wrapper for packet module load_pcapfile
        """
        # load functions in packet module
        packet = __import__("packet")
        p = packet.stop_and_load_tcpdump_packets(index, timeout=timeout)

        return p

    def kill_all(self, killall=False):
        """
        Kill all scapy process or DPDK application on tester.
        """
        if not self.has_external_traffic_generator():
            out = self.session.send_command('')
            if '>>>' in out:
                self.session.send_expect('quit()', '# ', timeout=3)
        if killall:
            super(Tester, self).kill_all()

    def close(self):
        """
        Close ssh session and IXIA tcl session.
        """
        if self.it_uses_external_generator():
            if self.is_pktgen and self.pktgen:
                self.pktgen.quit_generator()
                # only restore ports if start trex in dts
                if 'start_trex' in list(self.pktgen.conf.keys()):
                    self.restore_trex_interfaces()
                self.pktgen = None
            elif self.ixia_packet_gen:
                self.ixia_packet_gen.close()
                self.ixia_packet_gen = None

        if self.scapy_sessions_li:
            for i in self.scapy_sessions_li:
                if i.session.isalive():
                    i.session.send_expect("^c", ">>> ", timeout=2)
                    i.session.send_expect("^d", "#", timeout=2)
                    i.session.close()
            self.scapy_sessions_li.clear()

        if self.alt_session:
            self.alt_session.close()
            self.alt_session = None
        if self.session:
            self.session.close()
            self.session = None

    def crb_exit(self):
        """
        Close all resource before crb exit
        """
        self.close()
        self.logger.logger_exit()
