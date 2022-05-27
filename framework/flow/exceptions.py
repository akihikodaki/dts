# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2020 Intel Corporation
# Copyright(c) 2018-2019 The University of New Hampshire
#


class CompositionException(Exception):
    def __init__(self):
        self.message = "There was an unexpected error in composition"


class InvalidFlowItemException(CompositionException):
    def __init__(self, first_item, second_item, flow=None):
        if flow is not None:
            self.message = f'"{first_item}" was not able to accept "{second_item}" as the next item in flow {flow}.'
        else:
            self.message = f'"{first_item}" was not able to accept "{second_item}".'
