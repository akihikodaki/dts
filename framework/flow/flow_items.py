# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

from __future__ import annotations

import copy
import itertools
from functools import reduce
from typing import Any, Dict, FrozenSet, Hashable, Iterable, Set, Tuple, Union

from .enums import FlowActionType, FlowItemType
from .exceptions import InvalidFlowItemException

PATTERN_ACTION_ITEMS = {
    FlowItemType.INVERT,
    FlowItemType.VOID,
    FlowItemType.MARK,
    FlowItemType.META,
}


class FlowItem(object):
    type: Union[FlowItemType, FlowActionType]
    # Defines what items this may not appear with
    allowed_with: FrozenSet[Union[FlowItemType, FlowActionType]]
    # OSI Model layer of the protocol
    # This should be the lowest layer a protocol is used in, for example
    # QUIC would be considered L5 since it needs to go after UDP (L4),
    # even though it has capabilities in L6.
    layer: int
    valid_next_items: FrozenSet[Union[FlowItemType, FlowActionType]]

    # Types subject to change, should only be accessed through
    possible_properties: Dict[str, Tuple[str, FrozenSet[str], FrozenSet[str]]]
    properties: str

    def get_property_stream(
        self,
    ) -> Iterable[Tuple[FlowItem, FrozenSet[str], FrozenSet[str], str]]:
        """
        This function will return a generator that will provide all
        configured property combinations.

        This function will not mutate the instance it is called on.

        @return: a generator that will provide all
        permutations of possible properties this object has as a flow
        item with properties
        """
        base_copy = copy.deepcopy(self)
        for key, value in self.possible_properties.items():
            new_copy = copy.deepcopy(base_copy)
            new_copy.properties = value[0]  # The properties string
            yield new_copy, *value[1:], f"{self.type.value}_{key}"

    def __init__(self):
        self.properties = ""

    def __truediv__(self, other: FlowItem):
        """
        Used in a similar way to scapy's packet composition.
        @param other: The other flow item.
        @return: A Flow containing both items
        """
        if type(self) != type(other):
            raise InvalidFlowItemException(self, other)
        elif other.type in self.valid_next_items:
            # These imports are in here so there is no circular import
            from framework.flow.flow_action_items import ActionFlowItem
            from framework.flow.flow_pattern_items import PatternFlowItem

            from .flow import Flow

            if isinstance(self, PatternFlowItem):
                return Flow(pattern_items=[self, other])
            elif isinstance(self, ActionFlowItem):
                return Flow(action_items=[self, other])
            else:
                raise TypeError(
                    f"{type(self):s} is not one of {PatternFlowItem:s}, {ActionFlowItem:s}."
                )
        else:
            raise InvalidFlowItemException(self, other)

    def __eq__(self, other) -> bool:
        return (
            type(self) == type(other)
            and self.type == other.type
            and self.properties == other.properties
        )

    def __str__(self):
        if self.properties != "":
            return self.properties
        else:
            return self.type.value

    def __repr__(self):
        return str(self)
