'''
Created on Jul 29, 2014

@author: yliu86
'''
from scapy.packet import *
from scapy.fields import *
from scapy.layers.inet import UDP, IP
from scapy.layers.inet6 import IPv6
from scapy.layers.dns import DNS
from scapy.layers.l2 import Ether

vxlanmagic = "0x8"

VXLAN_PORT=4789
_GP_FLAGS = ["R", "R", "R", "A", "R", "R", "D", "R"]

class VXLAN(Packet):
    name = "VXLAN"
    fields_desc = [
        FlagsField("flags", 0x8, 8,
            ['OAM', 'R', 'NextProtocol', 'Instance',
            'V1', 'V2', 'R', 'G']),
        ConditionalField(
            ShortField("reserved0", 0),
            lambda pkt: pkt.flags & 0x04,
        ),
        ConditionalField(
            ByteEnumField('NextProtocol', 0,
                          {0: 'NotDefined',
                           1: 'IPv4',
                           2: 'IPv6',
                           3: 'Ethernet',
                           4: 'NSH'}),
            lambda pkt: pkt.flags & 0x04,
        ),
        ConditionalField(
            X3BytesField("reserved1", 0x000000),
            lambda pkt: (not pkt.flags & 0x80) and (not pkt.flags & 0x04),
        ),
        ConditionalField(
            FlagsField("gpflags", 0x0, 8, _GP_FLAGS),
            lambda pkt: pkt.flags & 0x80,
        ),
        ConditionalField(
            ShortField("gpid", 0),
            lambda pkt: pkt.flags & 0x80,
        ),
        X3BytesField("vni", 0),
        XByteField("reserved2", 0x00),
    ]

    # Use default linux implementation port
    overload_fields = {
        UDP: {'dport': 8472},
    }

    def mysummary(self):
        if self.flags & 0x80:
            return self.sprintf("VXLAN (vni=%VXLAN.vni% gpid=%VXLAN.gpid%)")
        else:
            return self.sprintf("VXLAN (vni=%VXLAN.vni%)")

    def guess_payload_class(self, payload):
        if self.flag == vxlanmagic:
            return VXLAN
        else:
            return Packet.guess_payload_class(self, payload)

split_layers(UDP, DNS, sport=53)
bind_layers(UDP, VXLAN, dport=4789)  # RFC standard port
bind_layers(UDP, VXLAN, dport=6633)  # New IANA assigned port for use with NSH
bind_layers(UDP, VXLAN, dport=8472)  # Linux implementation port
bind_layers(VXLAN, Ether, {'flags': 0x8})
bind_layers(VXLAN, Ether, {'flags': 0x88})
bind_layers(VXLAN, Ether, {'flags': 0xC, 'NextProtocol': 0}, NextProtocol=0)
bind_layers(VXLAN, IP, {'flags': 0xC, 'NextProtocol': 1}, NextProtocol=1)
bind_layers(VXLAN, IPv6, {'flags': 0xC, 'NextProtocol': 2}, NextProtocol=2)
bind_layers(VXLAN, Ether, {'flags': 0xC, 'NextProtocol': 3}, NextProtocol=3)
