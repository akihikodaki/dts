# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

# Allows the type system to handle referencing a class inside it's definition
from typing import Dict, FrozenSet, Iterable, List, Tuple

from scapy.layers.inet import ICMP, IP, TCP, UDP
from scapy.layers.inet6 import IPv6
from scapy.layers.l2 import ARP, GRE, Dot1Q, Ether
from scapy.layers.sctp import SCTP
from scapy.layers.vxlan import VXLAN
from scapy.packet import Packet

from .enums import FlowItemType
from .exceptions import InvalidFlowItemException
from .flow_items import FlowItem

ALWAYS_ALLOWED_ITEMS = {FlowItemType.RAW, FlowItemType.VOID}
L3_FLOW_TYPES = {FlowItemType.IPV4, FlowItemType.IPV6}
L4_FLOW_ITEMS = {
    FlowItemType.UDP,
    FlowItemType.TCP,
    FlowItemType.SCTP,
    FlowItemType.GRE,
}

PATTERN_OPERATION_TYPES = {
    FlowItemType.MARK,
    FlowItemType.META,
    FlowItemType.TAG,
    FlowItemType.FUZZY,
    FlowItemType.INVERT,
}

TUNNELING_PROTOCOL_TYPES = {
    FlowItemType.VLAN,
    FlowItemType.VXLAN,
    FlowItemType.GRE,
    FlowItemType.VXLAN_GPE,
}


class PatternFlowItem(FlowItem):
    allowed_with: FrozenSet[FlowItemType] = frozenset({item for item in FlowItemType})

    valid_next_items: List[FlowItemType] = [item for item in FlowItemType]

    # Only used for building a tree upward
    valid_parent_items: List[FlowItemType] = [item for item in FlowItemType]

    possible_properties: List[Tuple[str, Iterable, Iterable]] = {}

    def __truediv__(self, other: FlowItem):
        """
        Used in a similar way to scapy's packet composition.
        @param other: The other flow item.
        @return: A Flow containing both items
        """
        if other.type in self.valid_next_items or other.type == FlowItemType.END:
            # This import is in here so there is no circular import
            from .flow import Flow

            return Flow(pattern_items=[self, other])
        else:
            raise InvalidFlowItemException(self, other)

    # def to_scapy_packet(self):
    #    scapy_class: type = ITEM_TYPE_SCAPY_CLASS_MAPPING[self.type]


class FlowItemEnd(PatternFlowItem):
    type = FlowItemType.END
    valid_next_items = list({})


class FlowItemVoid(PatternFlowItem):
    type = FlowItemType.VOID


class FlowItemInvert(PatternFlowItem):
    type = FlowItemType.INVERT


class FlowItemAny(PatternFlowItem):
    type = FlowItemType.ANY


class FlowItemRaw(PatternFlowItem):
    type = FlowItemType.RAW


class FlowItemArp_eth_ipv4(PatternFlowItem):
    type = FlowItemType.ARP_ETH_IPV4
    valid_next_items = list({FlowItemType.RAW, FlowItemType.VOID})
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4]
    """
    - ``hdr``: hardware type, normally 1. => hwtype
    - ``pro``: protocol type, normally 0x0800. => ptype = 2048
    - ``hln``: hardware address length, normally 6. => hwlen
    - ``pln``: protocol address length, normally 4. => plen
    - ``op``: opcode (1 for request, 2 for reply). => op
    - ``sha``: sender hardware address. => hwsrc
    - ``spa``: sender IPv4 address => psrc
    - ``tha``: target hardware address. => hwdst
    - ``tpa``: target IPv4 address. => pdst
    - Default ``mask`` matches SHA, SPA, THA and TPA.
    """
    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'hdr':
        #     ('arp_eth_ipv4 hdr is 1',
        #      frozenset({"Ether() / ARP(hwtype=1) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ARP(hwtype=2) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwtype=3) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwtype=6) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwtype-15) / Raw('\\x00' * 64)"
        #                 })),
        # 'pro':
        #     ('arp_eth_ipv4 pro is 0x0800',
        #      frozenset({"Ether() / ARP(ptype=0x0800) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ARP(ptype=0x0800) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(ptype=0x0842) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(ptype=0x6004) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(ptype=0x809b) / Raw('\\x00' * 64)"
        #                 })),
        #
        # 'hln':
        #     ('arp_eth_ipv4 hln is 6',
        #      frozenset({"Ether() / ARP(hwlen=6) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ARP(hwlen=12) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwlen=2) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwlen=8) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(hwlen=4) / Raw('\\x00' * 64)"
        #                 })),
        #
        # 'pln':
        #     ('arp_eth_ipv4 pln is 4',
        #      frozenset({"Ether() / ARP(plen=4) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ARP(plen=6) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(plen=2) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(plen=8) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(plen=12) / Raw('\\x00' * 64)"
        #                 })),
        #
        # 'op':
        #     ('arp_eth_ipv4 op is 1',
        #      frozenset({"Ether() / ARP(op=1) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ARP(op=2) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(op=3) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(op=4) / Raw('\\x00' * 64)",
        #                 "Ether() / ARP(op=5) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "sha": (
            "arp_eth_ipv4 sha is 90:61:ae:fd:41:43",
            frozenset(
                {"Ether() / ARP(hwsrc=\"90:61:ae:fd:41:43\") / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / ARP(hwsrc=\"90:61:ae:fd:41:44\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwsrc=\"90:61:ae:fd:41:45\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwsrc=\"90:61:ae:fd:41:46\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwsrc=\"90:61:ae:fd:41:47\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "spa": (
            "arp_eth_ipv4 spa is 192.168.0.80",
            frozenset({"Ether() / ARP(psrc=\"192.168.0.80\") / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ARP(psrc=\"10.0.30.10\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(psrc=\"8.8.8.8\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(psrc=\"132.177.0.5\") / Raw('\\x00' * 64)",
                    "Ether() / ARP(psrc=\"123.4.5.6\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "tha": (
            "arp_eth_ipv4 tha is 00:00:00:00:00:00",
            frozenset({"Ether() / ARP(hwdst=00:00:00:00:00:00) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ARP(hwdst=90:61:ae:fd:41:45) / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwdst=90:61:ae:fd:41:46) / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwdst=90:61:ae:fd:41:47) / Raw('\\x00' * 64)",
                    "Ether() / ARP(hwdst=90:61:ae:fd:41:48) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "tpa": (
            "arp_eth_ipv4 tpa is 192.168.0.1",
            frozenset({"Ether() / ARP(pdst=192.168.0.1) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ARP(pdst=10.0.30.10) / Raw('\\x00' * 64)",
                    "Ether() / ARP(pdst=8.8.8.8) / Raw('\\x00' * 64)",
                    "Ether() / ARP(pdst=132.177.0.5) / Raw('\\x00' * 64)",
                    "Ether() / ARP(pdst=123.4.5.6) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemEth(PatternFlowItem):
    type = FlowItemType.ETH
    valid_next_items = list(
        ALWAYS_ALLOWED_ITEMS
        | L3_FLOW_TYPES
        | {FlowItemType.VLAN, FlowItemType.ARP_ETH_IPV4}
    )
    valid_parent_items: List[FlowItemType] = list({})
    # Matches an Ethernet header (not Ethernet frame).

    """
    - ``dst``: destination MAC.
    - ``src``: source MAC.
    - ``type``: EtherType or TPID. (TPID value is 0x8100, any others are normal EtherType)
    - Default ``mask`` matches destination and source addresses only.
    """
    possible_properties = {
        "dst": (
            "eth dst is 90:61:ae:fd:41:43",
            frozenset({"Ether(dst=\"90:61:ae:fd:41:43\") / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether(dst=\"90:61:ae:fd:41:44\") / Raw('\\x00' * 64)",
                    "Ether(dst=\"90:61:ae:fd:41:45\") / Raw('\\x00' * 64)",
                    "Ether(dst=\"90:61:ae:fd:41:46\") / Raw('\\x00' * 64)",
                    "Ether(dst=\"91:61:ae:fd:41:43\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "src": (
            "eth src is 90:61:ae:fd:41:43",
            frozenset({"Ether(src=\"90:61:ae:fd:41:43\") / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether(src=\"90:61:ae:fd:41:44\") / Raw('\\x00' * 64)",
                    "Ether(src=\"90:61:ae:fd:41:45\") / Raw('\\x00' * 64)",
                    "Ether(src=\"90:61:ae:fd:41:46\") / Raw('\\x00' * 64)",
                    "Ether(src=\"91:61:ae:fd:41:43\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "type": (
            "eth type is 0x0800",  # IPv4 EtherType
            frozenset({"Ether(type=0x0800) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether(type=0x0842) / Raw('\\x00' * 64)",
                    "Ether(type=0x8100) / Raw('\\x00' * 64)",  # Possibly a special case? TPID/VLAN
                    "Ether(type=0x9100) / Raw('\\x00' * 64)",  # Possibly special, VLAN double tagging
                    "Ether(type=0x8863) / Raw('\\x00' * 64)",
                    "Ether(type=0x9000) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemGre(PatternFlowItem):
    type = FlowItemType.GRE
    valid_next_items = list(L3_FLOW_TYPES | ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4, FlowItemType.IPV6]
    """
    - ``c_rsvd0_ver``: checksum, reserved 0 and version.
    - ``protocol``: protocol type.
    - Default ``mask`` matches protocol only.
    """
    possible_properties = {
        "c_rsvd0_ver": (
            "gre c_rsvd0_ver is 0",
            frozenset(
                {"Ether() / GRE(chksum_present=0, version=0) / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / GRE(chksum_present=1, version=0)) / Raw('\\x00' * 64)",
                    # this is the only other option
                }
            ),
        ),
        "protocol": (
            "gre protocol is 0x0800",
            frozenset({"Ether() / GRE(proto=0x0800) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / GRE(proto=0x0842) / Raw('\\x00' * 64)",
                    "Ether() / GRE(proto=0x8100) / Raw('\\x00' * 64)",
                    "Ether() / GRE(proto=0x0806) / Raw('\\x00' * 64)",
                    "Ether() / GRE(proto=0x809B) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemIcmp(PatternFlowItem):
    type = FlowItemType.ICMP
    valid_next_items = list({FlowItemType.RAW, FlowItemType.VOID})
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4]
    """
    - ``hdr``: ICMP header definition (``rte_icmp.h``).
    This definition includes:
    icmp_type (8 bits; for IPv4 echo request it's "8")
    icmp_code (8 bits)
    THE FOLLOWING ARE NOT SUPPORTED IN TESTPMD:
    icmp_cksum (16 bits)
    icmp_ident (16 bits)
    icmp_seq_nb (16 bits)
    - Default ``mask`` matches ICMP type and code only.
    """
    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'icmp_cksum':
        #     ('icmp cksum is 0x0800',
        #      frozenset({"Ether() / ICMP() / UDP() / Raw('\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
        #                 "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
        #                 "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
        #                 "Ether() / ICMP() / UDP() / Raw('\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "icmp_type": (
            "icmp type is 3",
            frozenset({"Ether() / ICMP(type=3) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMP(type=3) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=11) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=13) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=0) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "icmp_code": (
            "icmp type is 3 code is 3",  # Assume type 3 code 3; code meanings/options are dependent on type.
            frozenset({"Ether() / ICMP(type=3, code=3) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMP(type=3, code=0) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=3, code=2) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=11, code=1) / Raw('\\x00' * 64)",
                    "Ether() / ICMP(type=12, code=2) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "icmp_ident": (
            "icmp ident is 0x0800",
            frozenset({"Ether() / ICMP() / UDP() / Raw('\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                }
            ),
        ),
        "icmp_seq": (
            "icmp seq is 0x0800",
            frozenset({"Ether() / ICMP(proto=0x0800) / UDP() / Raw('\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                    "Ether() / ICMP() / UDP() / Raw('\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemIcmp6(PatternFlowItem):
    type = FlowItemType.ICMP6
    valid_next_items = list({FlowItemType.RAW, FlowItemType.VOID})
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV6]
    """
    - ``type``: ICMPv6 type.
    - ``code``: ICMPv6 code.
    - ``checksum``: ICMPv6 checksum.
    - Default ``mask`` matches ``type`` and ``code``.
    """
    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'checksum':
        #     ('icmp6 cksum is 0x1234',
        #      frozenset({"Ether() / ICMPv6DestUnreach(cksum=0x1234) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / ICMPv6DestUnreach(cksum=0x4321) / Raw('\\x00' * 64)",
        #                 "Ether() / ICMPv6DestUnreach(cksum=0xffff) / Raw('\\x00' * 64)",
        #                 "Ether() / ICMPv6DestUnreach(cksum=0x1233) / Raw('\\x00' * 64)",
        #                 "Ether() / ICMPv6DestUnreach(cksum=0x1010) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "type": (
            "icmp6 type is 1",  # Destination Unreachable
            frozenset({"Ether() / ICMPv6DestUnreach(type=1) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMPv6DestUnreach(type=128) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(type=129) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(type=3) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(type=135) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "code": (  # ICMP code is dependent on type; these are possible Destination Unreachable codes
            "icmp6 code is 0",
            frozenset({"Ether() / ICMPv6DestUnreach(code=0) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / ICMPv6DestUnreach(code=1) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(code=2) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(code=3) / Raw('\\x00' * 64)",
                    "Ether() / ICMPv6DestUnreach(code=4) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemIpv4(PatternFlowItem):
    type = FlowItemType.IPV4
    valid_next_items = list(L4_FLOW_ITEMS | {FlowItemType.ICMP} | ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.ETH, FlowItemType.GRE]
    """
    Note: IPv4 options are handled by dedicated pattern items.
    
    - ``hdr``: IPv4 header definition (``rte_ip.h``).
    - Default ``mask`` matches source and destination addresses only.
    """

    possible_properties = {
        "tos": (
            "ipv4 tos is 0",
            frozenset({"Ether() / IP(tos=0) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP(tos=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(tos=4) / Raw('\\x00' * 64)",
                    "Ether() / IP(tos=8) / Raw('\\x00' * 64)",
                    "Ether() / IP(tos=16) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "ttl": (
            "ipv4 ttl is 64",
            frozenset({"Ether() / IP(ttl=64) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP(ttl=128) / Raw('\\x00' * 64)",
                    "Ether() / IP(ttl=255) / Raw('\\x00' * 64)",
                    "Ether() / IP(ttl=32)  / Raw('\\x00' * 64)",
                    "Ether() / IP(ttl=100) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "proto": (
            "ipv4 proto is 0x06",  # TCP
            frozenset({"Ether() / IP(proto=0x06) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP(proto=0x01) / Raw('\\x00' * 64)",
                    "Ether() / IP(proto=0x11) / Raw('\\x00' * 64)",
                    "Ether() / IP(proto=0x12) / Raw('\\x00' * 64)",
                    "Ether() / IP(proto=0x58) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "src": (
            "ipv4 src is 192.168.0.5",
            frozenset({"Ether() / IP(src=\"192.168.0.5\") / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP(src=\"10.10.10.10\") / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.127.6\") / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"192.168.0.4\") / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"192.168.0.250\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dst": (
            "ipv4 dst is 192.168.0.5",
            frozenset({"Ether() / IP(dst=\"192.168.0.5\") / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP(dst=\"10.10.10.10\") / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"132.177.127.6\") / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"192.168.0.4\") / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"192.168.0.250\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        # CHECKSUM PROPERTY NOT SUPPORTED BY TESTPMD; DO NOT UNCOMMENT UNTIL SUPPORTED
        # 'checksum':
        #     ('ipv4 chksum is 0x1234',
        #     frozenset({"Ether() / ICMPv6DestUnreach(cksum=0x1234) / Raw('\\x00' * 64)"}),
        #     frozenset({"Ether() / ICMPv6DestUnreach(cksum=0x4321) / Raw('\\x00' * 64)",
        #                "Ether() / ICMPv6DestUnreach(cksum=0xffff) / Raw('\\x00' * 64)",
        #                "Ether() / ICMPv6DestUnreach(cksum=0x1233) / Raw('\\x00' * 64)",
        #                "Ether() / ICMPv6DestUnreach(cksum=0x1010) / Raw('\\x00' * 64)"
        #                })),
        ##########################################################################
    }


class FlowItemIpv6(PatternFlowItem):
    type = FlowItemType.IPV6
    valid_next_items = list(L4_FLOW_ITEMS | {FlowItemType.ICMP6} | ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.ETH, FlowItemType.GRE]
    """
    Note: IPv6 options are handled by dedicated pattern items, see `Item:
    IPV6_EXT`_.
    
    - ``hdr``: IPv6 header definition (``rte_ip.h``).
    - Default ``mask`` matches source and destination addresses only.
    """

    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'vtc_flow':
        #     ('ipv6 vtc_flow is 0x0',
        #      frozenset({"Ether() / IPv6(tc=0, fl=0, version=0) / Raw('\\x00' * 64)"}),
        #      frozenset({"Ether() / IPv6(tc=1, fl=0, version=0) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(tc=0, fl=0xABCD, version=0) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(tc=0, fl=0, version=1) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(tc=6, fl=0x9999, version=1) / Raw('\\x00' * 64)"
        #                 })),
        # 'payload_len':
        #     ('ipv6 payload_len is 64',
        #      frozenset({"Ether() / IPv6(plen=64) / Raw('\\x00' * 64)"}),
        #      frozenset({"Ether() / IPv6(plen=32) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(plen=128) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(plen=5000) / Raw('\\x00' * 64)",
        #                 "Ether() / IPv6(plen=4) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "tc": (
            "ipv6 tc is 0",
            frozenset({"Ether() / IPv6(tc=0) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IPv6(tc=1) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(tc=2) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(tc=4) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(tc=6) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "flow": (
            "ipv6 flow is 0xABCD",
            frozenset({"Ether() / IPv6(fl=0xABCD) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IPv6(fl=0xABCE) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(fl=0x0001) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(fl=0xFFFF) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(fl=0x1234) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "proto": (  # next header (nh)
            "ipv6 proto is 6",  # TCP
            frozenset({"Ether() / IPv6(nh=6) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IPv6(nh=17) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(nh=41) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(nh=0) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(nh=60) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "hop": (  # hop limit
            "ipv6 hop is 64",
            frozenset({"Ether() / IPv6(hlim=64) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IPv6(hlim=128) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(hlim=32) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(hlim=255) / Raw('\\x00' * 64)",
                    "Ether() / IPv6(hlim=100) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dst": (
            "ipv6 dst is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2",
            frozenset(
                {
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / Raw('\\x00' * 64)",
                }
            ),
        ),
        "src": (
            "ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2",
            frozenset(
                {
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2\") / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / Raw('\\x00' * 64)",
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6\") / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemSctp(PatternFlowItem):
    type = FlowItemType.SCTP
    valid_next_items = list(ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4, FlowItemType.IPV6]
    """
    
    **chunks?
    - ``hdr``: SCTP header definition (``rte_sctp.h``).
    - Default ``mask`` matches source and destination ports only.
    """
    possible_properties = {
        "src": (
            "sctp src is 3838",
            frozenset({"Ether() / IP() / SCTP(sport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / SCTP(sport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(sport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(sport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(sport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dst": (
            "sctp dst is 3838",
            frozenset({"Ether() / IP() / SCTP(dport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / SCTP(dport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(dport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(dport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(dport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "tag": (
            "sctp tag is 12345",
            frozenset({"Ether() / IP() / SCTP(tag=12345) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / SCTP(tag=12346) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(tag=12) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(tag=9999) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(tag=42) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "cksum": (
            "sctp cksum is 0x01535b67",
            frozenset({"Ether() / IP() / SCTP(chksum=0x01535b67) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / SCTP(chksum=0x01535b68) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(chksum=0xdeadbeef) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(chksum=0x12345678) / Raw('\\x00' * 64)",
                    "Ether() / IP() / SCTP(chksum=0x385030fe) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemTcp(PatternFlowItem):
    type = FlowItemType.TCP
    valid_next_items = list(ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4, FlowItemType.IPV6]
    """
    - ``hdr``: TCP header definition (``rte_tcp.h``).
    - Default ``mask`` matches source and destination ports only.
    
    #define 	RTE_TCP_CWR_FLAG   0x80

    #define 	RTE_TCP_ECE_FLAG   0x40

    #define 	RTE_TCP_URG_FLAG   0x20

    #define 	RTE_TCP_ACK_FLAG   0x10

    #define 	RTE_TCP_PSH_FLAG   0x08

    #define 	RTE_TCP_RST_FLAG   0x04

    #define 	RTE_TCP_SYN_FLAG   0x02

    #define 	RTE_TCP_FIN_FLAG   0x01

    Can we set multiple flags at once in testing (ex. SYN, ACK)?
    Probably, and we can definitely test them if necessary.
    """
    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'data_off':
        #     ('tcp data_off is 0',
        #      frozenset({"Ether() / IP() / TCP(dataofs=0) / Raw('\\x00' * 64)"}),
        #      frozenset({"Ether() /  IP() / TCP(dataofs=1) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(dataofs=2) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(dataofs=3) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(dataofs=4) / Raw('\\x00' * 64)"
        #                 })),
        # 'rx_win':
        #     ('tcp rx_win is 64',
        #      frozenset({"Ether() /  IP() / TCP(window=64)/ Raw('\\x00' * 64)"}),
        #      frozenset({"Ether() /  IP() / TCP(window=16)/ Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(window=128) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(window=32) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(window=255) / Raw('\\x00' * 64)"
        #                 })),
        # 'cksum':
        #     ('tcp cksum is 0x1234',
        #      frozenset({"Ether() /  IP() / TCP(chksum=0x1234) / Raw('\\x00' * 64)"}),
        #      frozenset({"Ether() / IP() / TCP(chksum=0x4321) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(chksum=0xffff) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(chksum=0x9999) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / TCP(chksum=0x1233)  / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "src": (
            "tcp src is 3838",
            frozenset({"Ether() / IP() / TCP(sport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / TCP(sport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(sport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(sport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(sport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dst": (
            "tcp dst is 3838",
            frozenset({"Ether() / IP() / TCP(dport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / TCP(dport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(dport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(dport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(dport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "flags": (
            "tcp flags is 0x02",
            frozenset({"Ether() / IP() / TCP(flags=0x02) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / TCP(flags=0x01) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(flags=0x04) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(flags=0x08) / Raw('\\x00' * 64)",
                    "Ether() / IP() / TCP(flags=0x10) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemUdp(PatternFlowItem):
    type = FlowItemType.UDP
    valid_next_items = list(
        {FlowItemType.VXLAN, FlowItemType.VXLAN_GPE} | ALWAYS_ALLOWED_ITEMS
    )
    valid_parent_items: List[FlowItemType] = [FlowItemType.IPV4, FlowItemType.IPV6]
    """
    - ``hdr``: UDP header definition (``rte_udp.h``).
    - Default ``mask`` matches source and destination ports only.
    """

    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY MAY BE RE-ENABLED ONCE TESTPMD SUPPORTS THEIR USE
        # 'dgram_len':
        #     ('udp dgram_len is 64',
        #      frozenset({"Ether() / IP() / UDP(len=64) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() /  IP() / UDP(len=128) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(len=32) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(len=16) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(len=255) / Raw('\\x00' * 64)"
        #                 })),
        # 'dgram_cksum':
        #     ('udp dgram_cksum is 0x1234',
        #      frozenset({"Ether() /  IP() / UDP(chksum=0x1234) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() / UDP(chksum=0x4321) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(chksum=0xffff) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(chksum=0x9999) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / UDP(chksum=0x1233)  / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "src": (
            "udp src is 3838",
            frozenset({"Ether() / IP() / UDP(sport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / UDP(sport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(sport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(sport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(sport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dst": (
            "udp dst is 3838",
            frozenset({"Ether() / IP() / UDP(dport=3838) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / UDP(dport=3939) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(dport=5000) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(dport=1998) / Raw('\\x00' * 64)",
                    "Ether() / IP() / UDP(dport=1028) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemVlan(PatternFlowItem):
    type = FlowItemType.VLAN
    valid_next_items = list(ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.ETH]
    """
    The corresponding standard outer EtherType (TPID) values are
    ``RTE_ETHER_TYPE_VLAN`` or ``RTE_ETHER_TYPE_QINQ``. It can be overridden by the
    preceding pattern item.
    If a ``VLAN`` item is present in the pattern, then only tagged packets will
    match the pattern.
    
    - ``tci``: tag control information.
    - ``inner_type``: inner EtherType or TPID.
    - Default ``mask`` matches the VID part of TCI only (lower 12 bits).
    
    tci in testpmd = pcp, dei, and vid, altogether.
    
    pcp in testpmd = prio in scapy
    dei in testpmd = id in scapy? 
    vid in testpmd = vlan in scapy
    
    tpid in testpmd = type in scapy
    """
    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY MAY BE RE-ENABLED ONCE TESTPMD SUPPORTS THEIR USE
        # 'tpid':
        #     ('vlan tpid is 0x8100',  # standard value
        #      frozenset({"Ether() / Dot1Q(type=0x8100) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() /  Dot1Q(type=0x0800) / Raw('\\x00' * 64)",
        #                 "Ether() /  Dot1Q(type=0x0842) / Raw('\\x00' * 64)",
        #                 "Ether() /  Dot1Q(type=0x809b) / Raw('\\x00' * 64)",
        #                 "Ether() /  Dot1Q(type=0x86dd) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "tci": (
            "vlan tci is 0xaaaa",
            frozenset(
                {
                    "Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() /  Dot1Q(prio = 0x0, id = 0x1, vlan = 0xbbb) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xccc) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio = 0x5, id = 0x1, vlan = 0xaaa) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio = 0x4, id = 0x0, vlan = 0xaaa) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "pcp": (
            "vlan pcp is 0x0",
            frozenset({"Ether() / Dot1Q(prio=0x0) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() /  Dot1Q(prio=0x1) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio=0x2) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio=0x3) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(prio=0x7) / Raw('\\x00' * 64)",
                }
            ),
        ),
        "dei": (
            "vlan dei is 0",
            frozenset({"Ether() / Dot1Q(id=0) / Raw('\\x00' * 64)"}),
            frozenset({"Ether() /  Dot1Q(id=1) / Raw('\\x00' * 64)"}),
        ),
        "vid": (
            "vlan vid is 0xabc",
            frozenset({"Ether() / Dot1Q(vlan=0xabc) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() /  Dot1Q(vlan=0xaaa) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(vlan=0x123) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(vlan=0x1f5) / Raw('\\x00' * 64)",
                    "Ether() /  Dot1Q(vlan=0x999) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemVxlan(PatternFlowItem):
    type = FlowItemType.VXLAN
    valid_next_items = frozenset({FlowItemType.ETH} | ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: FrozenSet[FlowItemType] = frozenset({FlowItemType.UDP})
    """
    - ``flags``: normally 0x08 (I flag).
    - ``rsvd0``: reserved, normally 0x000000.
    - ``vni``: VXLAN network identifier.
    - ``rsvd1``: reserved, normally 0x00.
    - Default ``mask`` matches VNI only.
    
    TESTPMD ONLY SUPPORTS VNI.
    """

    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'rsvd0':
        #     ('vxlan rsvd0 is 0x000000',
        #      frozenset({"Ether() / IP() / VXLAN(reserved0=0) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() /  IP() / VXLAN(reserved0=1) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=2) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=3) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP()  / VXLAN(reserved0=4) / Raw('\\x00' * 64)"
        #                 })),
        # 'rsvd1':
        #     ('vxlan rsvd1 is 0x00',
        #      frozenset({"Ether() /  IP() /  VXLAN(reserved0=0) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() /  VXLAN(reserved0=1) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=2) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / VXLAN(reserved0=3) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=4) / Raw('\\x00' * 64)"
        #                 })),
        # 'flags':
        #     ('vxlan flags is 0x08',
        #      frozenset({"Ether() /  IP() /  VXLAN(flags=0x08) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() /  VXLAN(flags=0x80) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(flags=0x00) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / VXLAN(flags=0x99) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(flags=0x01) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "vni": (  # a 3-byte value
            "vxlan vni is 0x112233",
            frozenset({"Ether() / IP() / VXLAN(vni=0x112233) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / VXLAN(vni=0x112234) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0x123456) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0xaabbcc) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0x999999) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemVxlan_gpe(PatternFlowItem):
    type = FlowItemType.VXLAN_GPE
    valid_next_items = list({FlowItemType.ETH} | ALWAYS_ALLOWED_ITEMS)
    valid_parent_items: List[FlowItemType] = [FlowItemType.UDP]
    """
    - ``flags``: normally 0x0C (I and P flags).
    - ``rsvd0``: reserved, normally 0x0000.
    - ``protocol``: protocol type. => NextProtocol?
    - ``vni``: VXLAN network identifier.
    - ``rsvd1``: reserved, normally 0x00.
    - Default ``mask`` matches VNI only.
    
    NOT CURRENTLY SUPPORTED BY TESTPMD.
    """

    possible_properties = {
        # THE FOLLOWING PROPERTIES ARE UNSUPPORTED BY TESTPMD AT THE TIME OF WRITING.
        # THEY CAN BE ENABLED ONCE TESTPMD SUPPORTS THEM
        # 'rsvd0':
        #     ('vxlan rsvd0 is 0x000000',
        #      frozenset({"Ether() / IP() / VXLAN(reserved0=0) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() /  IP() / VXLAN(reserved0=1) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=2) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=3) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP()  / VXLAN(reserved0=4) / Raw('\\x00' * 64)"
        #                 })),
        # 'rsvd1':
        #     ('vxlan rsvd1 is 0x00',
        #      frozenset({"Ether() /  IP() /  VXLAN(reserved0=0) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() /  VXLAN(reserved0=1) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=2) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / VXLAN(reserved0=3) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(reserved0=4) / Raw('\\x00' * 64)"
        #                 })),
        # 'flags':
        #     ('vxlan flags is 0x08',
        #      frozenset({"Ether() /  IP() /  VXLAN(flags=0x08) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() /  VXLAN(flags=0x80) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(flags=0x00) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() / VXLAN(flags=0x99) / Raw('\\x00' * 64)",
        #                 "Ether() /  IP() /  VXLAN(flags=0x01) / Raw('\\x00' * 64)"
        #                 })),
        # 'protocol':
        #     ('vxlan protocol is 0x01',
        #      frozenset({"Ether() / IP() / VXLAN(NextProtocol=0x01) / Raw('\\x00' * 64)"}),
        #
        #      frozenset({"Ether() / IP() / VXLAN(NextProtocol=0x01) / Raw('\\x00' * 64)",
        #                 "Ether() / IP() / VXLAN(NextProtocol=0x11) / Raw('\\x00' * 64)",
        #                 "Ether() / IP() / VXLAN(NextProtocol=0x22) / Raw('\\x00' * 64)",
        #                 "Ether() / IP() / VXLAN(NextProtocol=0x33) / Raw('\\x00' * 64)"
        #                 })),
        # END UNSUPPORTED PROPERTIES
        "vni": (  # a 3-byte value
            "vxlan vni is 0x112233",
            frozenset({"Ether() / IP() / VXLAN(vni=0x112233) / Raw('\\x00' * 64)"}),
            frozenset(
                {
                    "Ether() / IP() / VXLAN(vni=0x112234) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0x123456) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0xaabbcc) / Raw('\\x00' * 64)",
                    "Ether() / IP() / VXLAN(vni=0x999999) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowItemFuzzy(PatternFlowItem):
    type = FlowItemType.FUZZY
    layer = 1  # This field needs to go before ethernet, and we ignore layer 1 in these filters
    valid_next_items = list({FlowItemType.ETH, FlowItemType.RAW, FlowItemType.VOID})
    """
   +----------+---------------+--------------------------------------------------+
   | Field    |   Subfield    | Value                                            |
   +==========+===============+==================================================+
   | ``spec`` | ``threshold`` | 0 as perfect match, 0xffffffff as fuzziest match |
   +----------+---------------+--------------------------------------------------+
   | ``last`` | ``threshold`` | upper range value                                |
   +----------+---------------+--------------------------------------------------+
   | ``mask`` | ``threshold`` | bit-mask apply to "spec" and "last"              |
   +----------+---------------+--------------------------------------------------+
    """


class FlowItemMark(PatternFlowItem):
    type = FlowItemType.MARK
    """
    +----------+----------+---------------------------+
    | Field    | Subfield | Value                     |
    +==========+==========+===========================+
    | ``spec`` | ``id``   | integer value             |
    +----------+--------------------------------------+
    | ``last`` | ``id``   | upper range value         |
    +----------+----------+---------------------------+
    | ``mask`` | ``id``   | zeroed to match any value |
    +----------+----------+---------------------------+
    """


class FlowItemMeta(PatternFlowItem):
    type = FlowItemType.META
    """
    Matches an application specific 32 bit metadata item.
  
    - Default ``mask`` matches the specified metadata value.
    """


class FlowItemTag(PatternFlowItem):
    type = FlowItemType.TAG
    """
    Matches tag item set by other flows. Multiple tags are supported by specifying
    ``index``.
    
    - Default ``mask`` matches the specified tag value and index.
   +----------+----------+----------------------------------------+
   | Field    | Subfield  | Value                                 |
   +==========+===========+=======================================+
   | ``spec`` | ``data``  | 32 bit flow tag value                 |
   |          +-----------+---------------------------------------+
   |          | ``index`` | index of flow tag                     |
   +----------+-----------+---------------------------------------+
   | ``last`` | ``data``  | upper range value                     |
   |          +-----------+---------------------------------------+
   |          | ``index`` | field is ignored                      |
   +----------+-----------+---------------------------------------+
   | ``mask`` | ``data``  | bit-mask applies to "spec" and "last" |
   |          +-----------+---------------------------------------+
   |          | ``index`` | field is ignored                      |
   +----------+-----------+---------------------------------------+
    """


PATTERN_ITEMS_TYPE_CLASS_MAPPING: Dict[FlowItemType, PatternFlowItem] = {
    FlowItemType.UDP: FlowItemUdp,
    FlowItemType.TCP: FlowItemTcp,
    FlowItemType.SCTP: FlowItemSctp,
    FlowItemType.IPV4: FlowItemIpv4,
    FlowItemType.IPV6: FlowItemIpv6,
    FlowItemType.ETH: FlowItemEth,
    FlowItemType.VLAN: FlowItemVlan,
    FlowItemType.VXLAN: FlowItemVxlan,
    FlowItemType.GRE: FlowItemGre,
    FlowItemType.VXLAN_GPE: FlowItemVxlan_gpe,
    FlowItemType.ARP_ETH_IPV4: FlowItemArp_eth_ipv4,
    FlowItemType.ICMP: FlowItemIcmp,
    FlowItemType.ICMP6: FlowItemIcmp6,
    FlowItemType.MARK: FlowItemMark,
    FlowItemType.META: FlowItemMeta,
    FlowItemType.TAG: FlowItemTag,
    FlowItemType.FUZZY: FlowItemFuzzy,
    FlowItemType.END: FlowItemEnd,
    FlowItemType.VOID: FlowItemVoid,
    FlowItemType.INVERT: FlowItemInvert,
    FlowItemType.ANY: FlowItemAny,
    FlowItemType.RAW: FlowItemRaw,
}

ITEM_TYPE_SCAPY_CLASS_MAPPING: Dict[FlowItemType, Packet] = {
    FlowItemType.UDP: UDP,
    FlowItemType.TCP: TCP,
    FlowItemType.SCTP: SCTP,
    FlowItemType.IPV4: IP,
    FlowItemType.IPV6: IPv6,
    FlowItemType.ETH: Ether,
    FlowItemType.VLAN: Dot1Q,
    FlowItemType.VXLAN: VXLAN,
    FlowItemType.GRE: GRE,
    FlowItemType.VXLAN_GPE: VXLAN,
    FlowItemType.ARP_ETH_IPV4: ARP,  # The type rules prevent this from being under anything except Ether / IPv4
    FlowItemType.ICMP: ICMP,
    FlowItemType.ICMP6: ICMP,
    FlowItemType.MARK: None,
    FlowItemType.META: None,
    FlowItemType.TAG: None,
    FlowItemType.FUZZY: None,
    FlowItemType.END: None,
    FlowItemType.VOID: None,
    FlowItemType.INVERT: None,
    FlowItemType.ANY: None,
    FlowItemType.RAW: None,
}

TUNNELING_PROTOCOLS = {FlowItemVlan, FlowItemVxlan, FlowItemGre, FlowItemVxlan_gpe}

PATTERN_OPERATIONS = {
    FlowItemMark,
    FlowItemMeta,
    FlowItemTag,
    FlowItemFuzzy,
    FlowItemInvert,
}
