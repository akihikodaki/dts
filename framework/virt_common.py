# SPDX-License-Identifier: BSD-3-Clause
# Copyright(c) 2010-2014 Intel Corporation
#

import os

from .config import VirtConf
from .qemu_kvm import QEMUKvm
from .qemu_libvirt import LibvirtKvm
from .settings import CONFIG_ROOT_PATH


def VM(dut, vm_name, suite_name):
    conf = VirtConf(CONFIG_ROOT_PATH + os.sep + suite_name + ".cfg")
    conf.load_virt_config(vm_name)
    local_conf = conf.get_virt_config()
    # Default virt_type is 'KVM'
    virt_type = "KVM"
    for param in local_conf:
        if "virt_type" in list(param.keys()):
            virt_type = param["virt_type"][0]["virt_type"]

    if virt_type == "KVM":
        return QEMUKvm(dut, vm_name, suite_name)
    elif virt_type == "LIBVIRT":
        return LibvirtKvm(dut, vm_name, suite_name)
    else:
        raise Exception("Virt type %s is not supported!" % virt_type)
