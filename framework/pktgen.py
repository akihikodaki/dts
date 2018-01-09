# BSD LICENSE
#
# Copyright(c) 2010-2017 Intel Corporation. All rights reserved.
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

import os
import sys
import re
import string
import time
import json
import argparse
import IPy
import logging

from abc import abstractmethod
from config import IxiaConf
from ssh_connection import SSHConnection
from settings import SCAPY2IXIA
from logger import getLogger
from exception import VerifyFailure
from utils import create_mask
from uuid import uuid4
from pickletools import optimize
#from serializer import Serializer

FORMAT = '%(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('TrexA')
logger.setLevel(logging.INFO)
# change operation directory
cwd = os.getcwd()
sys.path.append(cwd + '/nics')
sys.path.append(cwd + '/framework')
sys.path.append(cwd + '/tests')
sys.path.append(cwd + '/dep')

from crb import Crb
from config import PktgenConf, CrbsConf, PortConf


class PacketGenerator(object):
#class PacketGenerator(Crb):
    """
    Basic class for packet generator, define basic function for each kinds of
    generators
    """
    def __init__(self, tester):
        self.__streams = []
        self._ports_map = []
        self.tester = tester

    @abstractmethod
    def _check_options(self, opts={}):
        pass

    def prepare_generator(self):
        self._prepare_generator()

        # extened tester port map and self port map
        ports = self._get_ports()
        print ports
        tester_portnum = len(self.tester.ports_info)
        for port_idx in range(len(ports)):
            port_info = {'type': '%s' % self.pktgen_type, 'pci': '%s' % ports[port_idx]}
            self._ports_map.append(tester_portnum + port_idx)
            self.tester.ports_info.append(port_info)
        print self._ports_map
        # update dut port map
        portconf = PortConf()
        for dut in self.tester.duts:
            dut.map_available_ports()

    def _convert_pktgen_port(self, port_id):
        try:
            port = self._ports_map[port_id]
        except:
            port = -1

        return port

    def _convert_tester_port(self, port_id):
        try:
            port = self._ports_map.index(port_id)
        except:
            port = -1

        return port

    @abstractmethod
    def _prepare_transmission(self, stream_ids=[]):
        pass

    @abstractmethod
    def _start_transmission(self, stream_ids, delay=50):
        pass

    @abstractmethod
    def _stop_transmission(self, stream_id):
        pass

    @abstractmethod
    def _retrieve_port_statistic(self, stream_id):
        pass

    def add_stream(self, tx_port, rx_port, pcap_file):
        stream_id = None

        pktgen_tx_port  = self._convert_tester_port(tx_port)
        pktgen_rx_port  = self._convert_tester_port(rx_port)

        stream_id = len(self.__streams)
        stream = {'tx_port': pktgen_tx_port,
                  'rx_port': pktgen_rx_port,
                  'pcap_file': pcap_file}
        self.__streams.append(stream)

        return stream_id

    def config_stream(self, stream_id=0, opts={}):
        if self._check_options(opts) is not True:
            self.logger.error("Failed to configure stream[%d]" % stream_id)
            return

        stream = self.__streams[stream_id]
        stream['options'] = opts

    def measure_throughput(self, stream_ids=[], delay=50):
        """
        Measure throughput on each tx ports
        """

        bps_rx = []
        pps_rx = []
        self._prepare_transmission(stream_ids=stream_ids)
        self._start_transmission(stream_ids)

        time.sleep(delay)
        for stream_id in stream_ids:
            rxbps_rates, rxpps_rates = self._retrieve_port_statistic(stream_id)

            bps_rx.append(rxbps_rates)
            pps_rx.append(rxpps_rates)
            self._stop_transmission(stream_id)
            bps_rx_total = self._summary_statistic(bps_rx)
            pps_rx_total = self._summary_statistic(pps_rx)

        print "throughput: pps_rx %f, bps_rx %f" % (pps_rx_total, bps_rx_total)

        return bps_rx_total, pps_rx_total

    def _summary_statistic(self, array=[]):
        """
        Summary all values in statistic array
        """
        summary = 0.000
        for value in array:
            summary += value

        return summary

    def _get_stream(self, stream_id):
        return self.__streams[stream_id]

    def _get_generator_conf_instance(self):
        conf_inst = PktgenConf(self.pktgen_type)
        return conf_inst

    @abstractmethod
    def quit_generator(self):
        pass

class TrexPacketGenerator(PacketGenerator):
    """
    Trex packet generator, detail usage can be seen at
    https://trex-tgn.cisco.com/trex/doc/trex_manual.html
    """
    def __init__(self, tester):
        self.pktgen_type = "trex"
        self._conn = None
        self._ports = []
        self._traffic_ports = []
        self._transmit_streams = {}
        self.trex_app = "scripts/t-rex-64"
    
        self.conf_inst = self._get_generator_conf_instance()
        self.conf = self.conf_inst.load_pktgen_config()
        self.options_keys = [ 'rate', 'ip', 'vlan']
        self.ip_keys = ['start', 'end','action', 'mask', 'step']
        self.vlan_keys = ['start', 'end', 'action', 'step', 'count']
        super(TrexPacketGenerator, self).__init__(tester)

    def connect(self):
        self._conn = self.trex_client(server=self.conf["server"])
        time.sleep(30)
        self._conn.connect()
        for p in self._conn.get_all_ports():
            self._ports.append(p)

        logger.debug(self._ports)

    def _get_ports(self):
        """
        Return self ports information
        """
        ports = []
        for idx in range(len(self._ports)):
            ports.append('TREX:%d' % idx)
        return ports

    def disconnect(self):
        self._conn.disconnect()

    def _check_options(self, opts={}):
        for key in opts:
            if key in self.options_keys:
                if key == 'ip':
                    ip = opts['ip']
                    for ip_key in ip:
                        if not ip_key in self.ip_keys:
                            print " %s is invalid ip option" % ip_key
                            return False
                        if key == 'action':
                            if not ip[key] == 'inc' or not ip[key] == 'dec':
                                print " %s is invalid ip action" % ip[key]
                                return False
                elif key == 'vlan':
                    vlan = opts['vlan']
                    for vlan_key in vlan:
                        if not vlan_key in self.vlan_keys:
                            print " %s is invalid vlan option" % vlan_key
                            return False
                        if key == 'action':
                            if not vlan[key] == 'inc' or not ip[key] == 'dec':
                                print " %s is invalid vlan action" % vlan[key]
                                return False
            else:
                print " %s is invalid option" % key
                return False
        return True

    def create_vm (self, ip_src_range, ip_dst_range, action='inc', step=1):
        if not ip_src_range and not ip_dst_range:
            return None

        vm = []

        if ip_src_range:
            vm += [self.trex_vm_flow(name="src", min_value = ip_src_range['start'], max_value = ip_src_range['end'], size = 4, op = action),
                   self.trex_vm_wr_flow(fv_name="src",pkt_offset= "IP.src")
                  ]

        if ip_dst_range:
            vm += [self.trex_vm_flow(name="dst", min_value = ip_dst_range['start'], max_value = ip_dst_range['end'], size = 4, op = action),
                   self.trex_vm_wr_flow(fv_name="dst",pkt_offset = "IP.dst")
                   ]

        vm += [self.trex_vm_ipv4(offset = "IP")
              ]

        return vm

    def _prepare_generator(self):
        app_param_temp = "-i"

        for key in self.conf:
            #key, value = pktgen_conf
            if key == 'config_file':
                app_param_temp = app_param_temp + " --cfg " + self.conf[key]
            elif key == 'core_num':
                app_param_temp = app_param_temp + " -c " + self.conf[key]


        # Insert Trex api library
        sys.path.insert(0, "{0}/scripts/automation/trex_control_plane/stl".format(self.conf['trex_root_path']))
        #from trex_stl_lib.api import *
        from trex_stl_lib.api import STLStream, STLPktBuilder, STLTXCont, STLVmFlowVar, STLVmWrFlowVar,\
                                     STLVmFixIpv4

	mod = __import__("trex_stl_lib.api")
        client_mod = getattr(mod, "trex_stl_client", None)
        self.trex_client = getattr(client_mod, "STLClient", None)
        self.trex_vm_flow = getattr(client_mod, "STLVmFlowVar", None)
        self.trex_vm_wr_flow = getattr(client_mod, "STLVmWrFlowVar", None)
        self.trex_vm_ipv4 = getattr(client_mod, "STLVmFixIpv4", None)
        self.trex_stream = getattr(client_mod, "STLStream", None)
        self.trex_pkt_builder = getattr(client_mod, "STLPktBuilder", None)
        self.trex_tx_count = getattr(client_mod, "STLTXCont", None)

        self.connect()
        #self.control_session.send_expect("cd " + cwd, "", 70)

    def _prepare_transmission(self, stream_ids=[]):
        # Create base packet and pad it to size
        streams = []
        ip_src_range = {}
        ip_dst_range = {}
        ip_src_range_temp = []
        ip_dst_range_temp = []

        # prepare stream configuration
        for stream_id in stream_ids:
            stream = self._get_stream(stream_id)
            tx_port = stream['tx_port']
            rx_port = stream['rx_port']
            rx_port_name = "port%d" % rx_port
            option = stream['options']
            pcap_file = stream["pcap_file"]
            #set rate
            rate = option['rate']
            if "ip" not in option:
                stl_stream = self.trex_stream(packet=self.trex_pkt_builder(pkt=pcap_file), mode=self.trex_tx_count(percentage=100))
                self._transmit_streams[stream_id] = stl_stream
                continue

            ip = option['ip']
            mask = ip['mask']
            step_temp = ip['step'].split('.')

            #get the subnet range of src and dst ip
            if self.conf.has_key("ip_src"):
                ip_src = self.conf['ip_src']
                ip_src_range_string = IPy.IP(IPy.IP(ip_src).make_net(mask).strNormal()).strNormal(3)
                ip_src_range_temp = ip_src_range_string.split('-')
                ip_src_range['start'] = ip_src_range_temp[0]
                ip_src_range['end'] = ip_src_range_temp[1]

            if self.conf.has_key("ip_dst"):
                ip_dst = self.conf['ip_dst']
                ip_dst_range_string = IPy.IP(IPy.IP(ip_dst).make_net(mask).strNormal()).strNormal(3)
                ip_dst_range_temp = ip_dst_range_string.split('-')
                ip_dst_range['start'] = ip_dst_range_temp[0]
                ip_dst_range['end'] = ip_dst_range_temp[1]

            # pcap_file = stream['pcap_file']

            vm = self.create_vm(ip_src_range, ip_dst_range, action=ip['action'], step=step_temp[3])

            stl_stream = self.trex_streampacket(self.trex_pkt_builder(pkt=pcap_file, vm=vm), mode=self.trex_tx_count(percentage=100)) 

            self._transmit_streams[stream_id] = stl_stream

    def _start_transmission(self, stream_ids, delay=50):
        self._conn.reset(ports=self._ports)
        self._conn.clear_stats()
        self._conn.set_port_attr(self._ports, promiscuous=True)
        duration_int = int(self.conf["duration"])
        rate = "100%"
        warmup = 15

        if self.conf.has_key("warmup"):
            warmup = int(self.conf["warmup"])

        for stream_id in stream_ids:
            stream = self._get_stream(stream_id)
            # tester port to Trex port
            tx_port = stream["tx_port"]
            p = self._ports[tx_port]
            self._conn.add_streams(self._transmit_streams[stream_id], ports=[p])
            rate = stream["options"]["rate"]
            self._traffic_ports.append(p)

        print self._traffic_ports

        if self.conf.has_key("core_mask"):
            self._conn.start(ports=self._traffic_ports, mult=rate, duration=warmup, core_mask=self.conf["core_mask"])
            self._conn.wait_on_traffic(ports=self._traffic_ports, timeout=warmup+30)
        else:
            self._conn.start(ports=self._traffic_ports, mult=rate, duration=warmup)
            self._conn.wait_on_traffic(ports=self._traffic_ports, timeout=warmup+30)

        self._conn.clear_stats()

        if self.conf.has_key("core_mask"):
            self._conn.start(ports=self._traffic_ports, mult=rate, duration=duration_int, core_mask=self.conf["core_mask"])
        else:
            self._conn.start(ports=self._traffic_ports, mult=rate, duration=duration_int)

        if self._conn.get_warnings():
            for warning in self._conn.get_warnings():
                logger.warn(warning)

    def _stop_transmission(self, stream_id):
        self._conn.stop(ports=self._traffic_ports, rx_delay_ms=5000)

    def _retrieve_port_statistic(self, stream_id):
        stats = self._conn.get_stats()
        stream = self._get_stream(stream_id)
        port_id = stream["rx_port"]
        port_stats = stats[port_id]
        print "Port %d stats: %s " % (port_id,port_stats)
        rate_rx_pkts = port_stats["rx_pps"]
        rate_rx_bits = port_stats["rx_bps_L1"]
        print "rx_port: %d,  rate_rx_pkts: %f, rate_rx_bits:%f " % (port_id,rate_rx_pkts,rate_rx_bits)
        return rate_rx_bits, rate_rx_pkts

    def quit_generator(self):
        self.disconnect()

def getPacketGenerator(tester, pktgen_type="trex"):
    """
    Get packet generator object
    """
    pktgen_type = pktgen_type.lower()

    if pktgen_type == "dpdk":
        return DpdkPacketGenerator(tester)
    elif pktgen_type == "ixia":
        return IxiaPacketGenerator(tester)
    elif pktgen_type == "trex":
        return TrexPacketGenerator(tester)


if __name__ == "__main__":
    # init pktgen stream options

    from tester import Tester
    options = {
    'rate' : '100%',
    'ip': {'action': 'inc', 'mask' : '255.255.255.0', 'step':'0.0.0.1'}
    }
    crbsconf = CrbsConf()
    crb = (crbsconf.load_crbs_config())[0]
    tester = Tester(crb, None)
    # framework initial
    trex = getPacketGenerator(tester, pktgen_type="trex")
    
    conf = conf_inst.load_pktgen_config()
    # prepare running environment
    trex.prepare_generator()

    #config stream and convert options into pktgen commands
    stream_id1 = trex.add_stream(0, 1, conf['pcap_file'])
    trex.config_stream(stream_id=stream_id1, opts=options)
    stream_id2 = trex.add_stream(1, 0, conf['pcap_file'])
    trex.config_stream(stream_id=stream_id2, opts=options)
    stream_id3 = trex.add_stream(0, 1, conf['pcap_file'])
    trex.config_stream(stream_id=stream_id3, opts=options)
    stream_id4 = trex.add_stream(1, 0, conf['pcap_file'])
    trex.config_stream(stream_id=stream_id4, opts=options)
    #pktgen.prepare_transmission(stream_ids=[stream_id])
    trex.measure_throughput(stream_ids=[stream_id1,stream_id2,stream_id3,stream_id4], delay=5)
    #trex.measure_throughput(stream_ids=[stream_id1,stream_id2], delay=5)
    # comeback to framework
    trex.quit_generator()
