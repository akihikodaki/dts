# BSD LICENSE
#
# Copyright(c) 2020 Intel Corporation. All rights reserved.
# Copyright © 2018[, 2019] The University of New Hampshire. All rights reserved.
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
from enum import Enum


class FlowRuleType(Enum):
    INGRESS = "ingress"
    EGRESS = "egress"
    BOTH = ""


class FlowItemType(Enum):
    UDP = "udp"
    TCP = "tcp"
    SCTP = "sctp"
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    END = "end"
    VOID = "void"
    INVERT = "invert"
    ANY = "any"
    RAW = "raw"
    ETH = "eth"
    VLAN = "vlan"
    VXLAN = "vxlan"
    GRE = "gre"
    VXLAN_GPE = "vxlan_gpe"
    ARP_ETH_IPV4 = "arp_eth_ipv4"
    ICMP = "icmp"
    ICMP6 = "icmp6"
    MARK = "mark"
    META = "meta"
    TAG = "tag"
    FUZZY = "fuzzy"


class FlowActionType(Enum):
    # "Simple" actions that don't need parameters
    VOID = "void"
    PASSTHRU = "passthru"
    FLAG = "flag"
    DROP = "drop"
    COUNT = "count"
    MAC_SWAP = "mac_swap"
    DEC_TTL = "dec_ttl"

    # Actions that do need parameters
    JUMP = "jump"
    MARK = "mark"
    QUEUE = "queue"
    RSS = "rss"
    PF = "pf"
    VF = "vf"
    PHY_PORT = "phy_port"
    PORT_ID = "port_id"
    METER = "meter"
    SECURITY = "security"
    OF_SET_MPLS_TTL = "of_set_mpls_ttl"
    OF_DEC_MPLS_TTL = "of_dec_mpls_ttl"
    OF_SET_NW_TTL = "of_set_nw_ttl"
    OF_DEC_NW_TTL = "of_dec_nw_ttl"
    OF_COPY_TTL_OUT = "of_copy_ttl_out"
    OF_COPY_TTL_IN = "of_copy_ttl_in"
    OF_POP_VLAN = "of_pop_vlan"
    OF_PUSH_VLAN = "of_push_vlan"
    OF_SET_VLAN_VID = "of_set_vlan_vid"
    OF_SET_VLAN_PCP = "of_set_vlan_pcp"
    OF_POP_MPLS = "of_pop_mpls"
    OF_PUSH_MPLS = "of_push_mpls"
    VXLAN_ENCAP = "vxlan_encap"
    VXLAN_DECAP = "vxlan_decap"
    NVGRE_ENCAP = "nvgre_encap"
    NVGRE_DECAP = "nvgre_decap"
    RAW_ENCAP = "raw_encap"
    RAW_DECAP = "raw_decap"
    SET_IPV4_SRC = "set_ipv4_src"
    SET_IPV4_DST = "set_ipv4_dst"
    SET_IPV6_SRC = "set_ipv6_src"
    SET_IPV6_DST = "set_ipv6_dst"
    SET_TP_SRC = "set_tp_src"
    SET_TP_DST = "set_tp_dst"
    SET_TTL = "set_ttl"
    SET_MAC_SRC = "set_mac_src"
    SET_MAC_DST = "set_mac_dst"
    INC_TCP_SEQ = "inc_tcp_seq"
    DEC_TCP_SEQ = "dec_tcp_seq"
    INC_TCP_ACK = "inc_tcp_ack"
    DEC_TCP_ACK = "dec_tcp_ack"
    SET_TAG = "set_tag"
    SET_META = "set_meta"
    SET_IPV4_DSCP = "set_ipv4_dscp"
    SET_IPV6_DSCP = "set_ipv6_dscp"
    AGE = "age"
