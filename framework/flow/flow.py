# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

from __future__ import annotations

import copy
import itertools
import operator
from functools import reduce
from typing import FrozenSet, Iterable, List, Tuple, Union

from scapy.layers.l2 import Ether
from scapy.packet import Raw

from .enums import FlowActionType, FlowItemType
from .exceptions import InvalidFlowItemException
from .flow_action_items import ActionFlowItem
from .flow_items import FlowItem
from .flow_pattern_items import TUNNELING_PROTOCOLS, PatternFlowItem

# Get reserved mac addresses
NEVER_MATCH_PACKET = Ether(src="", dst="") / Raw("\x00" * 64)


def _iterable_deep_compare(i1, i2):
    return reduce(lambda x, y: x and y, map(lambda x, y: x == y, i1, i2), True)


def expand_pattern_list_with_iterable_replacing_item(
    patterns: List[Iterable[FlowItem]],
    it: Iterable[Tuple[FlowItem, FrozenSet[str], FrozenSet[str], str]],
    item,
):
    """
    This function takes a list of patterns and splits each of them into 2
    parts, excluding the item at index. It then uses the provided
    iterator to fill in that value for all patterns.

    Ex:
    if patterns is [['a', 'b', 'c'], ['c','b','a']], it is [1,2], and item is 'b',
    then this function will produce

    [['a', 1], ['a', 2], ['a', 1], ['a', 2], ['a', 1], ['a', 2]]

    if everything is converted into a list. It is not converted
    because that requires using the memory to store all of this at
    the same time, which could be fairly large.
    """

    split_patterns = list(
        map(
            lambda pattern: (
                pattern[: pattern.index(item)],
                pattern[pattern.index(item) + 1 :],
            ),
            filter(lambda pattern: item in pattern, patterns),
        )
    )
    # Tee the iterators so I can consume all of them

    iterators = itertools.tee(it, len(patterns))
    for pattern_before, pattern_after in split_patterns:
        for iterator in iterators:
            for dataset in iterator:
                backup_dataset = copy.deepcopy(dataset)
                yield (
                    [*pattern_before, backup_dataset[0], *pattern_after],
                    *backup_dataset[1:],
                )
            # yield from map(
            #     lambda flow_item_test_properties: (
            #         [*pattern_before, flow_item_test_properties[0], *pattern_after],
            #         *flow_item_test_properties[1:],
            #     ), iterator
            # )

    yield from filter(lambda pattern: item not in pattern, patterns)


class Flow(object):
    action_items: List[ActionFlowItem]
    pattern_items: List[PatternFlowItem]
    entry_points: FrozenSet[FlowItemType]

    def __init__(
        self,
        action_items=None,
        pattern_items=None,
    ):
        if action_items is None:
            action_items = []

        if pattern_items is None:
            pattern_items = []

        self.action_items = action_items
        self.pattern_items = pattern_items

    def __truediv__(self, item: Union[FlowItem, Flow]):
        """
        Used in a similar way to scapy's packet composition. Returns a new flow with the mutated state.
        @param item: The other flow item.
        @return: A Flow containing both items
        """
        if isinstance(item, Flow):
            return Flow(
                pattern_items=[*self.pattern_items, *item.pattern_items],
                action_items=[*self.action_items, *item.action_items],
            )
        elif isinstance(item, PatternFlowItem):
            if len(self.pattern_items) == 0:
                return Flow(
                    pattern_items=[*self.pattern_items, item],
                    action_items=[*self.action_items],
                )
            elif item.type in self.pattern_items[-1].valid_next_items:
                return Flow(
                    pattern_items=[*self.pattern_items, item],
                    action_items=[*self.action_items],
                )
            else:
                raise InvalidFlowItemException(self.pattern_items[-1], item, flow=self)
        elif isinstance(item, ActionFlowItem):
            if len(self.action_items) == 0:
                return Flow(
                    pattern_items=[*self.pattern_items],
                    action_items=[*self.action_items, item],
                )

            for action in self.action_items:
                if item.type not in action.allowed_with:
                    raise InvalidFlowItemException(action, item, flow=self)
            return Flow(
                pattern_items=[*self.pattern_items],
                action_items=[*self.action_items, item],
            )

    def __str__(self):
        return f"ingress pattern %s actions queue index 1 / end" % (
            " / ".join(str(item) for item in self.pattern_items) + " / end"
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return (
            isinstance(other, Flow)
            and len(self.action_items) == len(other.action_items)
            and len(self.pattern_items) == len(other.pattern_items)
            and _iterable_deep_compare(self.pattern_items, other.pattern_items)
            and _iterable_deep_compare(self.action_items, other.action_items)
        )

    def to_scapy_packet(self):
        return reduce(
            operator.truediv, map(lambda x: x.to_scapy_packet(), self.pattern_items)
        )

    def get_test_property_flows(
        self, pattern_item_types_to_update=None, action_item_types_to_update=None
    ) -> Iterable[Flow]:
        if pattern_item_types_to_update is None and action_item_types_to_update is None:
            pattern_item_types_to_update = [self.pattern_items[-1]]
        elif pattern_item_types_to_update is None:
            pattern_item_types_to_update = []
        elif action_item_types_to_update is None:
            action_item_types_to_update = []

        # So that if this object is mutated before the generator is finished, it won't change anything
        base_pattern_items = copy.deepcopy(self.pattern_items)
        base_action_items = copy.deepcopy(self.action_items)

        test_flows: Iterable[Iterable[FlowItem]] = [base_pattern_items]

        tunnelling_protocols = list(
            filter(lambda i: type(i) in TUNNELING_PROTOCOLS, base_pattern_items)
        )
        if len(tunnelling_protocols) > 0:
            test_flows = expand_pattern_list_with_iterable_replacing_item(
                [*test_flows],
                tunnelling_protocols[0].get_property_stream(),
                tunnelling_protocols[0],
            )
        else:
            test_flows = expand_pattern_list_with_iterable_replacing_item(
                [*test_flows],
                self.pattern_items[-1].get_property_stream(),
                self.pattern_items[-1],
            )
        for pattern in test_flows:
            yield Flow(
                pattern_items=pattern[0], action_items=base_action_items
            ), *pattern[1:]
