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

import os
from copy import deepcopy

from scapy.all import conf
from scapy.packet import NoPayload
from scapy.packet import Packet as scapyPacket
from scapy.fields import ConditionalField
from scapy.utils import rdpcap

# dts libs
from utils import (convert_int2ip, convert_ip2int,
                   convert_mac2long, convert_mac2str)

from pktgen_base import (PKTGEN_DPDK, PKTGEN_TREX, PKTGEN_IXIA,
                         TRANSMIT_CONT, TRANSMIT_M_BURST, TRANSMIT_S_BURST)
from pktgen_base import DpdkPacketGenerator
from pktgen_ixia import IxiaPacketGenerator
from pktgen_trex import TrexPacketGenerator


class PacketGeneratorHelper(object):
    ''' default packet generator stream option for all streams '''
    default_opt = {
        'stream_config':{
            'txmode' : {},
            'transmit_mode': TRANSMIT_CONT,
            # for temporary usage because current pktgen design don't support
            # port level configuration, here using stream configuration to pass
            # rate percent
            'rate': 100,}}

    def __init__(self):
        self.packetLayers = dict()

    def _parse_packet_layer(self, pkt_object):
        ''' parse one packet every layers' fields and value '''
        if pkt_object == None:
            return

        self.packetLayers[pkt_object.name] = dict()
        for curfield in pkt_object.fields_desc:
            if isinstance(curfield, ConditionalField) and \
                not curfield._evalcond(pkt_object):
                continue
            field_value = pkt_object.getfieldval(curfield.name)
            if isinstance(field_value, scapyPacket) or (curfield.islist and \
                        curfield.holds_packets and type(field_value) is list):
                continue
            repr_value = curfield.i2repr(pkt_object, field_value)
            if isinstance(repr_value, str):
                repr_value = repr_value.replace(os.linesep,
                                    os.linesep + " "*(len(curfield.name) +4))
            self.packetLayers[pkt_object.name][curfield.name] = repr_value

        if isinstance(pkt_object.payload, NoPayload):
            return
        else:
            self._parse_packet_layer(pkt_object.payload)

    def _parse_pcap(self, pcapFile, number=0):
        ''' parse one packet content '''
        pcap_pkts = []
        if os.path.exists(pcapFile) == False:
            warning = "{0} is not exist !".format(pcapFile)
            raise Exception(warning)

        pcap_pkts = rdpcap(pcapFile)
        # parse packets' every layers and fields
        if len(pcap_pkts) == 0:
            warning = "{0} is empty".format(pcapFile)
            raise Exception(warning)
        elif number>= len(pcap_pkts):
            warning = "{0} is missing No.{1} packet".format(pcapFile, number)
            raise Exception(warning)
        else:
            self._parse_packet_layer(pcap_pkts[number])

    def _set_pktgen_fields_config(self, pcap, suite_config):
        '''
        get default fields value from a pcap file and unify layer fields
        variables for trex/ixia
        '''
        self._parse_pcap(pcap)
        if not self.packetLayers:
            msg = "pcap content is empty"
            raise Exception(msg)
        # suite fields config convert to pktgen fields config
        fields_config = {}
        # set ethernet protocol layer fields
        layer_name = 'mac'
        if layer_name in list(suite_config.keys()) and \
           'Ethernet' in self.packetLayers:
            fields_config[layer_name] = {}
            suite_fields = suite_config.get(layer_name)
            pcap_fields = self.packetLayers.get('Ethernet')
            for name, config in suite_fields.items():
                action = config.get('action') or 'default'
                range = config.get('range') or 64
                step = config.get('step') or 1
                start_mac = pcap_fields.get(name)
                end_mac = convert_mac2str(convert_mac2long(start_mac) + range-1)
                fields_config[layer_name][name] = {}
                fields_config[layer_name][name]['start'] = start_mac
                fields_config[layer_name][name]['end'] = end_mac
                fields_config[layer_name][name]['step'] = step
                fields_config[layer_name][name]['action'] = action
        # set ip protocol layer fields
        layer_name = 'ip'
        if layer_name in list(suite_config.keys()) and \
           'IP' in self.packetLayers:
            fields_config[layer_name] = {}
            suite_fields = suite_config.get(layer_name)
            pcap_fields = self.packetLayers.get('IP')
            for name, config in suite_fields.items():
                action = config.get('action') or 'default'
                range = config.get('range') or 64
                step = config.get('step') or 1
                start_ip = pcap_fields.get(name)
                end_ip = convert_int2ip(convert_ip2int(start_ip) + range - 1)
                fields_config[layer_name][name] = {}
                fields_config[layer_name][name]['start'] = start_ip
                fields_config[layer_name][name]['end'] = end_ip
                fields_config[layer_name][name]['step'] = step
                fields_config[layer_name][name]['action'] = action
        # set vlan protocol layer fields, only support one layer vlan here
        layer_name = 'vlan'
        if layer_name in list(suite_config.keys()) and \
           '802.1Q' in self.packetLayers:
            fields_config[layer_name] = {}
            suite_fields = suite_config.get(layer_name)
            pcap_fields = self.packetLayers.get('802.1Q')
            # only support one layer vlan here, so set name to `0`
            name = 0
            if name in list(suite_fields.keys()):
                config = suite_fields[name]
                action = config.get('action') or 'default'
                range = config.get('range') or 64
                # ignore 'L' suffix
                if 'L' in pcap_fields.get(layer_name):
                    start_vlan = int(pcap_fields.get(layer_name)[:-1])
                else:
                    start_vlan = int(pcap_fields.get(layer_name))
                end_vlan = start_vlan + range - 1
                fields_config[layer_name][name] = {}
                fields_config[layer_name][name]['start'] = start_vlan
                fields_config[layer_name][name]['end'] = end_vlan
                fields_config[layer_name][name]['step'] = 1
                fields_config[layer_name][name]['action'] = action

        return fields_config

    def prepare_stream_from_tginput(self, tgen_input, ratePercent,
                                    vm_config, pktgen_inst):
        ''' create streams for ports, one port one stream '''
        # set stream in pktgen
        stream_ids = []
        for config in tgen_input:
            stream_id = pktgen_inst.add_stream(*config)
            pcap = config[2]
            _options = deepcopy(self.default_opt)
            _options['pcap'] = pcap
            _options['stream_config']['rate'] = ratePercent
            # if vm is set
            if vm_config:
                _options['fields_config'] = \
                    self._set_pktgen_fields_config(pcap, vm_config)
            pktgen_inst.config_stream(stream_id, _options)
            stream_ids.append(stream_id)
        return stream_ids

def getPacketGenerator(tester, pktgen_type=PKTGEN_IXIA):
    """
    Get packet generator object
    """
    pktgen_type = pktgen_type.lower()

    pktgen_cls = {
        PKTGEN_DPDK: DpdkPacketGenerator,
        PKTGEN_IXIA: IxiaPacketGenerator,
        PKTGEN_TREX: TrexPacketGenerator,}

    if pktgen_type in list(pktgen_cls.keys()):
        CLS = pktgen_cls.get(pktgen_type)
        return CLS(tester)
    else:
        msg = "not support <{0}> packet generator".format(pktgen_type)
        raise Exception(msg)
