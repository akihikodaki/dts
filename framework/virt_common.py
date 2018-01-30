# BSD LICENSE
#
# Copyright(c) 2010-2014 Intel Corporation. All rights reserved.
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
import os
import exception

from config import VirtConf
from settings import CONFIG_ROOT_PATH

from qemu_kvm import QEMUKvm
from qemu_libvirt import LibvirtKvm

def VM(dut, vm_name, suite_name):
    conf = VirtConf(CONFIG_ROOT_PATH + os.sep + suite_name + '.cfg')
    conf.load_virt_config(vm_name)
    local_conf = conf.get_virt_config()
    # Default virt_type is 'KVM'
    virt_type = 'KVM'
    for param in local_conf:
        if 'virt_type' in param.keys():
            virt_type = param['virt_type'][0]['virt_type']

    if virt_type == 'KVM':
        return QEMUKvm(dut, vm_name, suite_name)
    elif virt_type == 'LIBVIRT':
        return LibvirtKvm(dut, vm_name, suite_name)
    else:
        raise Exception("Virt type %s is not supported!" 
            % virt_type)


