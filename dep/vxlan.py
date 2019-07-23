'''
Created on Jul 29, 2014

@author: yliu86
'''
from scapy.packet import *
from scapy.fields import *
from scapy.layers.inet import UDP, IP
from scapy.layers.dns import DNS
from scapy.layers.l2 import Ether

vxlanmagic = "0x8"

VXLAN_PORT=4789

class VXLAN(Packet):
    name = "VXLAN"
    fields_desc = [ByteField("flags", 8),
                   X3BytesField("reserved1", 0),
                   X3BytesField("vni", 0),
                   ByteField("reserved2", 0)]

    def guess_payload_class(self, payload):
        if self.flag == vxlanmagic:
            return VXLAN
        else:
            return Packet.guess_payload_class(self, payload)

    def mysummary(self):
        return self.sprintf("VXLAN (vni=%VXLAN.vni%)")

split_layers(UDP, DNS, sport=53)
bind_layers(UDP, VXLAN, dport=VXLAN_PORT)
bind_layers(VXLAN, Ether)
