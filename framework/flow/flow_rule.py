# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#

from typing import Union

import framework.flow.flow_action_items as flow_action_items

from .enums import *
from .flow import Flow


class FlowPattern(Flow):
    entry_points = {FlowItemType.ETH, FlowItemType.FUZZY}

    def __str__(self):
        return f"pattern {super(FlowPattern, self).__str__()} / end"


class FlowActions(Flow):
    entry_points = flow_action_items.ENTRY_POINTS

    def __str__(self):
        return f"action {super(FlowActions, self).__str__()} / end"


class FlowRule(object):
    port: int
    group: Union[int, None]
    priority: Union[int, None]

    ingress: bool
    egress: bool
    transfer: bool

    pattern: FlowPattern
    actions: FlowActions
