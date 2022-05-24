# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2021 Intel Corporation
#

"""
Misc functions.
"""

from typing import List, NamedTuple


class IxiaNetworkConfig(NamedTuple):
    ixia_ip: str
    tg_ip: str
    tg_ip_port: str
    tg_ports: List
