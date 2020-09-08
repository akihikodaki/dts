from scapy.packet import Packet, bind_layers, Padding
from scapy.fields import *
from scapy.layers.inet import UDP

class PFCP(Packet):
    name = "PFCP"
    fields_desc =  [ BitField("version", 1, 3),
                     BitField("MP", 0, 4),
                     BitField("Sfield", 0, 1),
                     ByteField("MsgType", 0),
                     ShortField("len", None),
                     LongField("SEID", 0),
                     ThreeBytesField("SeqNum", 0),
                     BitField("MsgPrio", 0, 4),
                     BitField("spare", 0, 4)]


    def post_build(self, pkt, pay):
        if self.len is None:
            l = len(pkt)+len(pay)
            pkt = pkt[:2]+struct.pack("!H", l)+pkt[4:]
        return pkt+pay

bind_layers(UDP, PFCP, dport=8805)
