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
from __future__ import annotations

import copy
import itertools
import os
import sys
import time
from typing import List, Set, Generator, Iterable, FrozenSet, Tuple

import numpy as np

from flow.flow import Flow
from flow.flow_pattern_items import PATTERN_ITEMS_TYPE_CLASS_MAPPING, PatternFlowItem, \
    PATTERN_OPERATION_TYPES, TUNNELING_PROTOCOL_TYPES, ALWAYS_ALLOWED_ITEMS, FlowItemEnd, FlowItemVxlan, FlowItemIpv4, \
    FlowItemEth, FlowItemGre, L3_FLOW_TYPES, FlowItemVlan, FlowItemUdp
from flow.flow_rule import FlowItemType


def get_valid_next_protocols(current_protocol, protocol_stack, type_denylist):
    return list(filter(
        lambda patent_item: patent_item not in type_denylist and patent_item not in {p.type for p in protocol_stack},
        current_protocol.valid_parent_items))


def _generate(type_denylist=None) -> List[List[PatternFlowItem]]:
    if type_denylist is None:
        type_denylist = set()
    UNUSED_PATTERN_ITEMS = {PATTERN_ITEMS_TYPE_CLASS_MAPPING[i] for i in type_denylist}

    patterns: List[List[PatternFlowItem]] = []
    for pattern_item in [clazz for clazz in PATTERN_ITEMS_TYPE_CLASS_MAPPING.values() if
                         clazz not in UNUSED_PATTERN_ITEMS]:
        protocol_stack = []
        if protocol_stack.count(pattern_item) >= 2:
            continue

        current_protocol = pattern_item()
        valid_next_protocols = get_valid_next_protocols(current_protocol, protocol_stack, type_denylist)
        while len(valid_next_protocols) > 0:
            protocol_stack.append(current_protocol)
            current_protocol = PATTERN_ITEMS_TYPE_CLASS_MAPPING[list(valid_next_protocols)[0]]()
            valid_next_protocols = get_valid_next_protocols(current_protocol, protocol_stack, type_denylist)

        protocol_stack.append(current_protocol)

        patterns.append(list(reversed(protocol_stack)))  # This will place the lowest level protocols first
    return patterns


def convert_protocol_stack_to_flow_pattern(protocol_stack):
    return Flow(pattern_items=protocol_stack)


def _get_patterns_with_type_denylist(type_denylist: Set):
    return [convert_protocol_stack_to_flow_pattern(protocol_stack) for protocol_stack in (_generate(
        type_denylist=type_denylist
    ))]


def _get_normal_protocol_patterns() -> List[Flow]:
    return _get_patterns_with_type_denylist(
        PATTERN_OPERATION_TYPES | ALWAYS_ALLOWED_ITEMS | {FlowItemType.ANY,
                                                          FlowItemType.END})


def _get_tunnelled_protocol_patterns(patterns: List[Flow]) -> Generator[Flow]:
    VXLAN_FLOW = Flow(pattern_items=[FlowItemEth(), FlowItemIpv4(), FlowItemUdp(), FlowItemVxlan()])
    for pattern in patterns:
        yield VXLAN_FLOW / pattern

    GRE_FLOW = Flow(pattern_items=[FlowItemEth(), FlowItemIpv4(), FlowItemGre()])
    for pattern in patterns:
        if len(pattern.pattern_items) >= 2:
            if pattern.pattern_items[1].type in L3_FLOW_TYPES:
                yield GRE_FLOW / pattern


def get_patterns() -> Iterable[Iterable[Flow]]:
    patterns: List[Flow] = _get_normal_protocol_patterns()

    # The flow with only an ethernet header was a consequence of the
    # generation algorithm, but isn't that useful to test since we can't
    # create a failing case without getting each NIC to write arbitrary
    # bytes over the link.
    eth_only_flow = Flow(pattern_items=[FlowItemEth()])
    patterns.remove(eth_only_flow)

    # tunnelled_patterns = _get_tunnelled_protocol_patterns(patterns)

    return patterns


def add_properties_to_patterns(patterns: Iterable[Flow]) -> Iterable[Tuple[Flow, FrozenSet[str], FrozenSet[str], str]]:
    test_property_flow_iters = map(lambda f: f.get_test_property_flows(), patterns)
    for iterator in test_property_flow_iters:
        yield from iterator


def get_patterns_with_properties() -> Iterable[Tuple[Flow, FrozenSet[str], FrozenSet[str], str]]:
    base_patterns = get_patterns()
    return add_properties_to_patterns(base_patterns)


def create_test_function_strings(test_configurations: Iterable[Tuple[Flow, FrozenSet[str], FrozenSet[str], str]]) -> \
        Iterable[str]:
    """
    This will break if the __str__ methods of frozenset ever changes or if % formatting syntax is removed.

    @param test_configurations: An iterable with test configurations to convert into test case strings.
    @return: An iterable containing strings that are function parameters.
    """
    function_template = \
        """
def test_%s(self):
    self.do_test_with_queue_action("%s", %s, %s)
        """
    return map(lambda test_configuration: function_template % (
        test_configuration[-1], test_configuration[0], test_configuration[1], test_configuration[2],),
               test_configurations)


def main():
    """
    Run this file (python3 generator.py) from the flow directory to print
    out the pattern functions which are normally automatically generated
    and added to the RTE Flow test suite at runtime.
    """
    pattern_tests = list(get_patterns_with_properties())
    pattern_functions = create_test_function_strings(pattern_tests)
    print("\n".join(pattern_functions))


if __name__ == "__main__":
    main()
