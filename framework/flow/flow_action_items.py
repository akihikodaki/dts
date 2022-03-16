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

from typing import Dict, FrozenSet, Tuple

from .enums import FlowActionType
from .flow_items import FlowItem

ALWAYS_ALLOWED_ACTIONS = {FlowActionType.VOID}

ENTRY_POINTS = {
    FlowActionType.VOID,
    FlowActionType.PASSTHRU,
    FlowActionType.FLAG,
    FlowActionType.DROP,
    FlowActionType.COUNT,
    FlowActionType.MAC_SWAP,
    FlowActionType.DEC_TTL,
    FlowActionType.JUMP,
    FlowActionType.MARK,
    FlowActionType.QUEUE,
    FlowActionType.RSS,
    FlowActionType.PF,
    FlowActionType.VF,
    FlowActionType.PHY_PORT,
    FlowActionType.PORT_ID,
    FlowActionType.SECURITY,
    FlowActionType.OF_SET_MPLS_TTL,
    FlowActionType.OF_DEC_MPLS_TTL,
    FlowActionType.OF_SET_NW_TTL,
    FlowActionType.OF_DEC_NW_TTL,
    FlowActionType.OF_COPY_TTL_OUT,
    FlowActionType.OF_COPY_TTL_IN,
    FlowActionType.OF_POP_VLAN,
    FlowActionType.OF_PUSH_VLAN,
    FlowActionType.OF_SET_VLAN_VID,
    FlowActionType.OF_SET_VLAN_PCP,
    FlowActionType.OF_POP_MPLS,
    FlowActionType.OF_PUSH_MPLS,
    FlowActionType.VXLAN_ENCAP,
    FlowActionType.VXLAN_DECAP,
    FlowActionType.NVGRE_ENCAP,
    FlowActionType.NVGRE_DECAP,
    FlowActionType.RAW_ENCAP,
    FlowActionType.RAW_DECAP,
    FlowActionType.SET_IPV4_SRC,
    FlowActionType.SET_IPV4_DST,
    FlowActionType.SET_IPV6_SRC,
    FlowActionType.SET_IPV6_DST,
    FlowActionType.SET_TP_SRC,
    FlowActionType.SET_TP_DST,
    FlowActionType.SET_TTL,
    FlowActionType.SET_MAC_SRC,
    FlowActionType.SET_MAC_DST,
    FlowActionType.INC_TCP_SEQ,
    FlowActionType.DEC_TCP_SEQ,
    FlowActionType.INC_TCP_ACK,
    FlowActionType.DEC_TCP_ACK,
    FlowActionType.SET_TAG,
    FlowActionType.SET_META,
    FlowActionType.SET_IPV4_DSCP,
    FlowActionType.SET_IPV6_DSCP,
    FlowActionType.AGE,
}


class ActionFlowItem(FlowItem):
    allowed_with: FrozenSet[FlowActionType] = frozenset(
        {item for item in FlowActionType}
    )

    valid_next_items: FrozenSet[FlowActionType] = frozenset(
        {item for item in FlowActionType}
    )

    test_case: Dict[str, Tuple[str, frozenset, frozenset]] = dict()


class FlowActionVoid(ActionFlowItem):
    type = FlowActionType.VOID

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions void / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionPassthru(ActionFlowItem):
    type = FlowActionType.PASSTHRU
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions passthru / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionFlag(ActionFlowItem):
    type = FlowActionType.FLAG
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions flag / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionDrop(ActionFlowItem):
    type = FlowActionType.DROP
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions drop / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionCount(ActionFlowItem):
    type = FlowActionType.COUNT
    test_case = {
        "test_shared": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions count shared 0 id 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        "test_id": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions count id 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionMac_swap(ActionFlowItem):
    type = FlowActionType.MAC_SWAP

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions mac_swap / end",
            frozenset(
                {
                    'Ether(src="90:61:ae:fd:41:43", dst = "ab:cd:ef:12:34:56") '
                    "/ IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether(src="90:61:ae:fd:41:43", dst = "ab:cd:ef:12:34:56") '
                    "/ IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    'Ether(src="90:61:ae:fd:41:43", dst = "ab:cd:ef:12:34:56") '
                    "/ IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    'Ether(src="90:61:ae:fd:41:43", dst = "ab:cd:ef:12:34:56") '
                    "/ IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    'Ether(src="90:61:ae:fd:41:43", dst = "ab:cd:ef:12:34:56") '
                    "/ IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionDec_ttl(ActionFlowItem):
    type = FlowActionType.DEC_TTL

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions dec_ttl / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\", ttl = 128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\", ttl = 128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\", ttl = 128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\", ttl = 128 ) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\", ttl = 128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionJump(ActionFlowItem):
    type = FlowActionType.JUMP

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions jump group 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionMark(ActionFlowItem):
    type = FlowActionType.MARK
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions mark id 0xABCDEF / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionQueue(ActionFlowItem):
    type = FlowActionType.QUEUE
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions queue index 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionRss(ActionFlowItem):
    type = FlowActionType.RSS

    # RSS already has a test suite.
    """
     test_case = {
         'case1': ('ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions / end',
                   frozenset({"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}),
                   frozenset({"Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)"})),
     }
     """


class FlowActionPf(ActionFlowItem):
    type = FlowActionType.PF
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions pf / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionVf(ActionFlowItem):
    type = FlowActionType.VF
    test_case = {
        "test_original": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 /"
            " udp / end actions vf original 1/ end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        "test_id": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vf id 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionPhy_port(ActionFlowItem):
    type = FlowActionType.PHY_PORT

    test_case = {
        # original port index
        "test_original": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions phy_port original / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # physical port index
        "test_index": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions phy_port index 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionPort_id(ActionFlowItem):
    type = FlowActionType.PORT_ID

    test_case = {
        # original DPDK port ID
        "test_original": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions port_id original / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # DPDK port ID
        "test_id": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions port_id id 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionMeter(ActionFlowItem):
    type = FlowActionType.METER
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions meter mtr_id 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSecurity(ActionFlowItem):
    type = FlowActionType.SECURITY
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions security security_session 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_set_mpls_ttl(ActionFlowItem):
    type = FlowActionType.OF_SET_MPLS_TTL

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_set_mpls_ttl mpls_ttl 64 / end",
            frozenset(
                {
                    'Ether() / IP(src="192.168.0.1") / MPLS(label = 0xab, ttl=128)'
                    " / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    'Ether() / IP(src="132.177.0.99") / MPLS(label = 0xab, ttl=128)'
                    " / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_dec_mpls_ttl(ActionFlowItem):
    type = FlowActionType.OF_DEC_MPLS_TTL

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_dec_mpls_ttl / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_set_nw_ttl(ActionFlowItem):
    type = FlowActionType.OF_SET_NW_TTL

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_set_nw_ttl nw_ttl 64 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\", ttl=128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_dec_nw_ttl(ActionFlowItem):
    type = FlowActionType.OF_DEC_NW_TTL
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_dec_nw_ttl / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\", ttl=128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\", ttl=128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_copy_ttl_out(ActionFlowItem):
    type = FlowActionType.OF_COPY_TTL_OUT

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_copy_ttl_out / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_copy_ttl_in(ActionFlowItem):
    type = FlowActionType.OF_COPY_TTL_IN

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_copy_ttl_out / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_pop_vlan(ActionFlowItem):
    type = FlowActionType.OF_POP_VLAN

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions of_pop_vlan / end",
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.1") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.2") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="10.0.30.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="8.8.8.8") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="132.177.0.99")'
                    " / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_push_vlan(ActionFlowItem):
    type = FlowActionType.OF_PUSH_VLAN
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions of_push_vlan ethertype 0x8100 / end",
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.1") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.2") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="10.0.30.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="8.8.8.8") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="132.177.0.99")'
                    " / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_set_vlan_vid(ActionFlowItem):
    type = FlowActionType.OF_SET_VLAN_VID

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_set_vlan_vid vlan_vid 0xbbb / end",
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.1")'
                    " / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.2") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="10.0.30.99") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="8.8.8.8") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="132.177.0.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_set_vlan_pcp(ActionFlowItem):
    type = FlowActionType.OF_SET_VLAN_PCP
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions of_set_vlan_vid vlan_pcp 0x7 / end",
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.1") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="192.168.0.2") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="10.0.30.99") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="8.8.8.8") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / Dot1Q(prio = 0x5, id = 0x0, vlan = 0xaaa) / IP(src="132.177.0.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_pop_mpls(ActionFlowItem):
    type = FlowActionType.OF_POP_MPLS
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions of_pop_mpls ethertype 0x0806 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionOf_push_mpls(ActionFlowItem):
    type = FlowActionType.OF_PUSH_MPLS

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions of_push_mpls ethertype 0x0806 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / MPLS(label = 0xab, ttl=128) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionVxlan_encap(ActionFlowItem):
    type = FlowActionType.VXLAN_ENCAP

    test_case = {
        # VXLAN encap definition is the VNI?
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions vxlan_encap definition 0x112233 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionVxlan_decap(ActionFlowItem):
    type = FlowActionType.VXLAN_DECAP

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions vxlan_decap / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") / UDP() / VXLAN() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / VXLAN() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / VXLAN() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / VXLAN() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / VXLAN() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionNvgre_encap(ActionFlowItem):
    type = FlowActionType.NVGRE_ENCAP
    # NVGRE PACKETS NOT SUPPORTED BY SCAPY.
    """
     test_case = {
         'test': ('ingress pattern eth / ipv4 src is 192.168.0.1
         / udp / end actions nvgre_encap definition 0x112233 / end',
                   frozenset({"Ether() / IP(src=\"192.168.0.1\") / UDP() /  NVGRE() / Raw('\\x00' * 64)"}),
                   frozenset({"Ether() / IP(src=\"192.168.0.2\") / UDP() /  NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"10.0.30.99\") / UDP() /  NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"8.8.8.8\") / UDP() /  NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"132.177.0.99\") / UDP() /  NVGRE() / Raw('\\x00' * 64)"})),
     }
     """


class FlowActionNvgre_decap(ActionFlowItem):
    type = FlowActionType.NVGRE_DECAP
    # NVGRE PACKETS NOT SUPPORTED BY SCAPY.
    """
     test_case = {
         'test': ('ingress pattern eth / ipv4 src is 192.168.0.1 / udp / end actions nvgre_decap / end',
                   frozenset({"Ether() / IP(src=\"192.168.0.1\") / UDP() / NVGRE() / Raw('\\x00' * 64)"}),
                   frozenset({"Ether() / IP(src=\"192.168.0.2\") / UDP() / NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"10.0.30.99\") / UDP() / NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"8.8.8.8\") / UDP() / NVGRE() / Raw('\\x00' * 64)",
                              "Ether() / IP(src=\"132.177.0.99\") / UDP() / NVGRE() / Raw('\\x00' * 64)"})),
     }
     """


class FlowActionRaw_encap(ActionFlowItem):
    type = FlowActionType.RAW_ENCAP
    # Assume we are encapsulating with a VLAN header with the following values:
    # TPID: 0x8100
    # Prio: 0x5
    # PCP: 0
    # VID: 0xaaa
    # This makes the full header: 0x8100aaaa
    test_case = {
        "test_data": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions raw_encap data 0x8100aaaa / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        "test_preserve": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions raw_encap data 0x8100aaaa preserve 0xffffffff / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # Is "size" in bits or bytes? Unclear in documentation, defaulting to bits.
        "test_size": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions raw_encap data 0x8100aaaa size 32 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionRaw_decap(ActionFlowItem):
    type = FlowActionType.RAW_DECAP
    test_case = {
        "test_data": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions raw_decap data 0x8100aaaa / end",
            frozenset(
                {"Ether()  / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="192.168.0.2")'
                    " / UDP() / Raw('\\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="10.0.30.99") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="8.8.8.8")'
                    " / UDP() / Raw('\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="132.177.0.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # Is "size" in bits or bytes? Unclear in documentation, defaulting to bits.
        "test_size": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions raw_decap data 0x8100aaaa size 32 / end",
            frozenset(
                {
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="192.168.0.1") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="192.168.0.2") '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="10.0.30.99")'
                    " / UDP() / Raw('\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="8.8.8.8") '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() /  Dot1Q(prio = 0x5, id = 0x0, vlan = 0xbbb) / IP(src="132.177.0.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv4_src(ActionFlowItem):
    type = FlowActionType.SET_IPV4_SRC

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_ipv4_src ipv4_addr 172.16.0.10  / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv4_dst(ActionFlowItem):
    type = FlowActionType.SET_IPV4_DST

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 dst is 192.168.0.1"
            " / udp / end actions set_ipv4_dst ipv4_addr 172.16.0.10 / end",
            frozenset(
                {"Ether() / IP(dst=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(dst=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(dst=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv6_src(ActionFlowItem):
    type = FlowActionType.SET_IPV6_SRC

    test_case = {
        "test": (
            "ingress pattern eth / ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 "
            "/ udp / end actions set_ipv6_src ipv6_addr 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb",
            frozenset(
                {
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IPv6(src=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / UDP() / Raw('\x00' * 64)",
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv6_dst(ActionFlowItem):
    type = FlowActionType.SET_IPV6_DST

    test_case = {
        "test": (
            "ingress pattern eth / ipv6 dst is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 "
            "/ udp / end actions set_ipv6_dst ipv6_addr 2001:0000:9d38:6ab8:1c48:9999:aaaa:bbbb",
            frozenset(
                {
                    'Ether() / IPv6(dst="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2")'
                    " / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IPv6(dst=\"2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5\") / UDP() / Raw('\x00' * 64)",
                    'Ether() / IPv6(dst="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_tp_src(ActionFlowItem):
    type = FlowActionType.SET_TP_SRC

    test_case = {
        # UDP
        "test_udp": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions set_tp_src port 1998 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") UDP(sport=3838) / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") UDP(sport=3838) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") UDP(sport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") UDP(sport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") UDP(sport=3838) / Raw('\\x00' * 64)",
                }
            ),
        ),
        # TCP
        "test_tcp": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions set_tp_src port 1998 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") TCP(sport=3838) / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") TCP(sport=3838) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") TCP(sport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") TCP(sport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") TCP(sport=3838) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_tp_dst(ActionFlowItem):
    type = FlowActionType.SET_TP_DST

    test_case = {
        # UDP
        "test_udp": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_tp_dst port 1998 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") UDP(dport=3838) / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") UDP(dport=3838) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") UDP(dport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") UDP(dport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") UDP(dport=3838) / Raw('\\x00' * 64)",
                }
            ),
        ),
        # TCP
        "test_tcp": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions set_tp_dst port 1998 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\") TCP(dport=3838) / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") TCP(dport=3838) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") TCP(dport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") TCP(dport=3838) / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") TCP(dport=3838) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ttl(ActionFlowItem):
    type = FlowActionType.SET_TTL

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions set_ttl ttl_value 64 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\" , ttl=128 ) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\" , ttl=128 ) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\" , ttl=128 ) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\", ttl=128 ) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\", ttl=128 ) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_mac_src(ActionFlowItem):
    type = FlowActionType.SET_MAC_SRC

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions set_mac_src mac_addr 10:20:30:40:50:60 / end",
            frozenset(
                {
                    'Ether(src="90:61:ae:fd:41:43") / IP(src="192.168.0.1") / UDP() / Raw(\'\\x00\' * 64)'
                }
            ),
            frozenset(
                {
                    'Ether(src="90:61:ae:fd:41:43") / IP(src="192.168.0.2") / UDP() / Raw(\'\\x00\' * 64)',
                    'Ether(src="90:61:ae:fd:41:43") / IP(src="10.0.30.99") / UDP() / Raw(\'\\x00\' * 64)',
                    'Ether(src="90:61:ae:fd:41:43") / IP(src="8.8.8.8") / UDP() / Raw(\'\\x00\' * 64)',
                    'Ether(src="90:61:ae:fd:41:43") / IP(src="132.177.0.99") / UDP() / Raw(\'\\x00\' * 64)',
                }
            ),
        ),
    }


class FlowActionSet_mac_dst(ActionFlowItem):
    type = FlowActionType.SET_MAC_DST
    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1"
            " / udp / end actions set_mac_dst mac_addr 10:20:30:40:50:60 / end",
            frozenset(
                {
                    'Ether(dst="90:61:ae:fd:41:43") / IP(src="192.168.0.1") '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether(dst="90:61:ae:fd:41:43") / IP(src="192.168.0.2") / UDP() / Raw(\'\\x00\' * 64)',
                    'Ether(dst="90:61:ae:fd:41:43") / IP(src="10.0.30.99") / UDP() / Raw(\'\x00\' * 64)',
                    'Ether(dst="90:61:ae:fd:41:43") / IP(src="8.8.8.8") / UDP() / Raw(\'\x00\' * 64)',
                    'Ether(dst="90:61:ae:fd:41:43") / IP(src="132.177.0.99") '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionInc_tcp_seq(ActionFlowItem):
    type = FlowActionType.INC_TCP_SEQ

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions inc_tcp_seq / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / TCP(seq=2) / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / TCP(seq=2) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionDec_tcp_seq(ActionFlowItem):
    type = FlowActionType.DEC_TCP_SEQ

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions dec_tcp_seq / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / TCP(seq=2) / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / TCP(seq=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / TCP(seq=2) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionInc_tcp_ack(ActionFlowItem):
    type = FlowActionType.INC_TCP_ACK

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions inc_tcp_ack / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / TCP(ack=2) / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / TCP(ack=2) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionDec_tcp_ack(ActionFlowItem):
    type = FlowActionType.DEC_TCP_ACK

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 / tcp / end actions dec_tcp_ack / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / TCP(ack=2) / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / TCP(ack=2) / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / TCP(ack=2) / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_tag(ActionFlowItem):
    type = FlowActionType.SET_TAG

    test_case = {
        "test_data": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_tag data 0xabc / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # bit-mask applies to "data"
        "test_mask": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_tag data 0xabc mask 0xcba / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        "test_index": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_tag data 0xabc index 1 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_meta(ActionFlowItem):
    type = FlowActionType.SET_META

    test_case = {
        "test_data": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_meta data 0xabc / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # bit-mask applies to "data"
        "test_mask": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_meta data 0xabc mask 0xcb / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv4_dscp(ActionFlowItem):
    type = FlowActionType.SET_IPV4_DSCP

    test_case = {
        "test": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions set_ipv4_dscp dscp 2 / end",
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.1\", tos = 0) / UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\", tos = 0) / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\", tos = 0) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\", tos = 0) / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\", tos = 0) / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionSet_ipv6_dscp(ActionFlowItem):
    type = FlowActionType.SET_IPV6_DSCP

    test_case = {
        "test": (
            "ingress pattern eth / ipv6 src is 2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2 "
            "/ udp / end actions set_ipv6_dscp dscp 0x30",
            frozenset(
                {
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c2", tc = 0) '
                    "/ UDP() / Raw('\\x00' * 64)"
                }
            ),
            frozenset(
                {
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c3", tc = 0) '
                    "/ UDP() / Raw('\\x00' * 64)",
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c4", tc = 0) '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c5", tc = 0) '
                    "/ UDP() / Raw('\x00' * 64)",
                    'Ether() / IPv6(src="2001:0000:9d38:6ab8:1c48:3a1c:a95a:b1c6", tc = 0) '
                    "/ UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


class FlowActionAge(ActionFlowItem):
    type = FlowActionType.AGE

    test_case = {
        "test_timeout": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions age timeout 128 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # 8 bits reserved, must be zero
        "test_reserved": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions age timeout 128 reserved 0 / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
        # The user flow context, NULL means the rte_flow pointer.
        "test_context": (
            "ingress pattern eth / ipv4 src is 192.168.0.1 "
            "/ udp / end actions age timeout 128 context NULL / end",
            frozenset(
                {"Ether() / IP(src=\"192.168.0.1\") / UDP() / Raw('\\x00' * 64)"}
            ),
            frozenset(
                {
                    "Ether() / IP(src=\"192.168.0.2\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"10.0.30.99\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"8.8.8.8\") / UDP() / Raw('\\x00' * 64)",
                    "Ether() / IP(src=\"132.177.0.99\") / UDP() / Raw('\\x00' * 64)",
                }
            ),
        ),
    }


ACTION_ITEMS_TYPE_CLASS_MAPPING: Dict[FlowActionType, ActionFlowItem] = {
    FlowActionType.PASSTHRU: FlowActionPassthru,
    FlowActionType.FLAG: FlowActionFlag,
    FlowActionType.DROP: FlowActionDrop,
    FlowActionType.COUNT: FlowActionCount,
    FlowActionType.MAC_SWAP: FlowActionMac_swap,
    FlowActionType.DEC_TTL: FlowActionDec_ttl,
    FlowActionType.JUMP: FlowActionJump,
    FlowActionType.MARK: FlowActionMark,
    FlowActionType.QUEUE: FlowActionQueue,
    FlowActionType.RSS: FlowActionRss,
    FlowActionType.PF: FlowActionPf,
    FlowActionType.VF: FlowActionVf,
    FlowActionType.PHY_PORT: FlowActionPhy_port,
    FlowActionType.PORT_ID: FlowActionPort_id,
    FlowActionType.METER: FlowActionMeter,
    FlowActionType.SECURITY: FlowActionSecurity,
    FlowActionType.OF_SET_MPLS_TTL: FlowActionOf_set_mpls_ttl,
    FlowActionType.OF_DEC_MPLS_TTL: FlowActionOf_dec_mpls_ttl,
    FlowActionType.OF_SET_NW_TTL: FlowActionOf_set_nw_ttl,
    FlowActionType.OF_DEC_NW_TTL: FlowActionOf_dec_nw_ttl,
    FlowActionType.OF_COPY_TTL_OUT: FlowActionOf_copy_ttl_out,
    FlowActionType.OF_COPY_TTL_IN: FlowActionOf_copy_ttl_in,
    FlowActionType.OF_POP_VLAN: FlowActionOf_pop_vlan,
    FlowActionType.OF_PUSH_VLAN: FlowActionOf_push_vlan,
    FlowActionType.OF_SET_VLAN_VID: FlowActionOf_set_vlan_vid,
    FlowActionType.OF_SET_VLAN_PCP: FlowActionOf_set_vlan_pcp,
    FlowActionType.OF_POP_MPLS: FlowActionOf_pop_mpls,
    FlowActionType.OF_PUSH_MPLS: FlowActionOf_push_mpls,
    FlowActionType.VXLAN_ENCAP: FlowActionVxlan_encap,
    FlowActionType.VXLAN_DECAP: FlowActionVxlan_decap,
    FlowActionType.NVGRE_ENCAP: FlowActionNvgre_encap,
    FlowActionType.NVGRE_DECAP: FlowActionNvgre_decap,
    FlowActionType.RAW_ENCAP: FlowActionRaw_encap,
    FlowActionType.RAW_DECAP: FlowActionRaw_decap,
    FlowActionType.SET_IPV4_SRC: FlowActionSet_ipv4_src,
    FlowActionType.SET_IPV4_DST: FlowActionSet_ipv4_dst,
    FlowActionType.SET_IPV6_SRC: FlowActionSet_ipv6_src,
    FlowActionType.SET_IPV6_DST: FlowActionSet_ipv6_dst,
    FlowActionType.SET_TP_SRC: FlowActionSet_tp_src,
    FlowActionType.SET_TP_DST: FlowActionSet_tp_dst,
    FlowActionType.SET_TTL: FlowActionSet_ttl,
    FlowActionType.SET_MAC_SRC: FlowActionSet_mac_src,
    FlowActionType.SET_MAC_DST: FlowActionSet_mac_dst,
    FlowActionType.INC_TCP_SEQ: FlowActionInc_tcp_seq,
    FlowActionType.DEC_TCP_SEQ: FlowActionDec_tcp_seq,
    FlowActionType.INC_TCP_ACK: FlowActionInc_tcp_ack,
    FlowActionType.DEC_TCP_ACK: FlowActionDec_tcp_ack,
    FlowActionType.SET_TAG: FlowActionSet_tag,
    FlowActionType.SET_META: FlowActionSet_meta,
    FlowActionType.SET_IPV4_DSCP: FlowActionSet_ipv4_dscp,
    FlowActionType.SET_IPV6_DSCP: FlowActionSet_ipv6_dscp,
    FlowActionType.AGE: FlowActionAge,
}
