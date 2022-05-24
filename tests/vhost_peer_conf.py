# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2019 Intel Corporation
#

import os

from framework.config import UserConf
from framework.settings import CONFIG_ROOT_PATH

conf_file = os.path.join(CONFIG_ROOT_PATH, "vhost_peer_conf.cfg")
conf_peer = UserConf(conf_file)
conf_session = conf_peer.conf._sections["peerconf"]


def get_pci_info():
    return conf_session["pci"]


def get_pci_peer_info():
    return conf_session["peer"]


def get_pci_driver_info():
    return conf_session["pci_drv"]


def get_pci_peer_intf_info():
    return conf_session["peer_intf"]
