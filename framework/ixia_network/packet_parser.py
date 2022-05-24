# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

import os
from collections import OrderedDict

from scapy.all import conf
from scapy.fields import ConditionalField
from scapy.packet import NoPayload
from scapy.packet import Packet as scapyPacket
from scapy.utils import rdpcap


class PacketParser(object):
    """parse packet full layers information"""

    def __init__(self):
        self.packetLayers = OrderedDict()
        self.framesize = 64

    def _parse_packet_layer(self, pkt_object):
        """parse one packet every layers' fields and value"""
        if pkt_object is None:
            return

        self.packetLayers[pkt_object.name] = OrderedDict()
        for curfield in pkt_object.fields_desc:
            if isinstance(curfield, ConditionalField) and not curfield._evalcond(
                pkt_object
            ):
                continue
            field_value = pkt_object.getfieldval(curfield.name)
            if isinstance(field_value, scapyPacket) or (
                curfield.islist and curfield.holds_packets and type(field_value) is list
            ):
                continue
            repr_value = curfield.i2repr(pkt_object, field_value)
            if isinstance(repr_value, str):
                repr_value = repr_value.replace(
                    os.linesep, os.linesep + " " * (len(curfield.name) + 4)
                )
            self.packetLayers[pkt_object.name][curfield.name] = repr_value

        if isinstance(pkt_object.payload, NoPayload):
            return
        else:
            self._parse_packet_layer(pkt_object.payload)

    def _parse_pcap(self, pcapFile, number=0):
        """parse one packet content"""
        self.packetLayers = OrderedDict()
        pcap_pkts = []
        if isinstance(pcapFile, str):
            if os.path.exists(pcapFile) is False:
                warning = "{0} is not exist !".format(pcapFile)
                raise Exception(warning)
            pcap_pkts = rdpcap(pcapFile)
        else:
            pcap_pkts = pcapFile
        # parse packets' every layers and fields
        if len(pcap_pkts) == 0:
            warning = "{0} is empty".format(pcapFile)
            raise Exception(warning)
        elif number >= len(pcap_pkts):
            warning = "{0} is missing No.{1} packet".format(pcapFile, number)
            raise Exception(warning)
        else:
            self._parse_packet_layer(pcap_pkts[number])
            self.framesize = len(pcap_pkts[number]) + 4
