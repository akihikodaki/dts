# BSD LICENSE
#
# Copyright(c) 2010-2015 Intel Corporation. All rights reserved.
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
from random import randint

from .utils import RED, get_obj_funcs, parallel_lock

INIT_FREE_PORT = 6000
INIT_SERIAL_PORT = 7000
INIT_MIGRATE_PORT = 8000
INIT_DISPLAY_PORT = 0

QuickScan = True

class VirtResource(object):

    """
    Class handle dut resource, like cpu, memory, net devices
    """

    def __init__(self, dut):
        self.dut = dut

        self.cores = [int(core['thread']) for core in dut.cores]
        # initialized unused cores
        self.unused_cores = self.cores[:]
        # initialized used cores
        self.used_cores = [-1] * len(self.unused_cores)

        self.ports_info = dut.ports_info
        # initialized unused ports
        self.ports = [port['pci'] for port in dut.ports_info]
        self.unused_ports = self.ports[:]
        # initialized used ports
        self.used_ports = ['unused'] * len(self.unused_ports)

        # initialized vf ports
        self.vfs_info = []
        self.vfs = []
        self.unused_vfs = []
        self.used_vfs = []

        # save allocated cores and related vm
        self.allocated_info = {}

    def __port_used(self, pci):
        index = self.ports.index(pci)
        self.used_ports[index] = pci
        self.unused_ports[index] = 'used'

    def __port_unused(self, pci):
        index = self.ports.index(pci)
        self.unused_ports[index] = pci
        self.used_ports[index] = 'unused'

    def __port_on_socket(self, pci, socket):
        for port in self.ports_info:
            if port['pci'] == pci:
                if socket == -1:
                    return True

                if port['numa'] == socket:
                    return True
                else:
                    return False

        return False

    def __vf_used(self, pci):
        index = self.vfs.index(pci)
        self.used_vfs[index] = pci
        self.unused_vfs[index] = 'used'

    def __vf_unused(self, pci):
        index = self.vfs.index(pci)
        self.used_vfs[index] = 'unused'
        self.unused_vfs[index] = pci

    def __core_used(self, core):
        core = int(core)
        index = self.cores.index(core)
        self.used_cores[index] = core
        self.unused_cores[index] = -1

    def __core_unused(self, core):
        core = int(core)
        index = self.cores.index(core)
        self.unused_cores[index] = core
        self.used_cores[index] = -1

    def __core_on_socket(self, core, socket):
        for dut_core in self.dut.cores:
            if int(dut_core['thread']) == core:
                if socket == -1:
                    return True

                if int(dut_core['socket']) == socket:
                    return True
                else:
                    return False

        return False

    def __core_isused(self, core):
        index = self.cores.index(core)
        if self.used_cores[index] != -1:
            return True
        else:
            return False

    def reserve_cpu(self, coremask=''):
        """
        Reserve dpdk used cpus by mask
        """
        val = int(coremask, base=16)
        cpus = []
        index = 0
        while val != 0:
            if val & 0x1:
                cpus.append(index)

            val = val >> 1
            index += 1

        for cpu in cpus:
            self.__core_used(cpu)

    @parallel_lock()
    def alloc_cpu(self, vm='', number=-1, socket=-1, corelist=None):
        """
        There're two options for request cpu resource for vm.
        If number is not -1, just allocate cpu from not used cores.
        If list is not None, will allocate cpu after checked.
        """
        cores = []

        if vm == '':
            print("Alloc cpu request virtual machine name!!!")
            return cores

        # if vm has been allocated cores, just return them
        if self.__vm_has_resource(vm, 'cores'):
            return self.allocated_info[vm]['cores']

        if number != -1:
            for core in self.unused_cores:
                if core != -1 and number != 0:
                    if self.__core_on_socket(core, socket) is True:
                        self.__core_used(core)
                        cores.append(str(core))
                        number = number - 1
            if number != 0:
                print("Can't allocated requested cpu!!!")

        if corelist is not None:
            for core in corelist:
                if self.__core_isused(int(core)) is True:
                    print("Core %s has been used!!!" % core)
                else:
                    if self.__core_on_socket(int(core), socket) is True:
                        self.__core_used(int(core))
                        cores.append(core)

        if vm not in self.allocated_info:
            self.allocated_info[vm] = {}

        self.allocated_info[vm]['cores'] = cores
        return cores

    def __vm_has_resource(self, vm, resource=''):
        if vm == '':
            self.dut.logger.info("VM name can't be NULL!!!")
            raise Exception("VM name can't be NULL!!!")
        if vm not in self.allocated_info:
            self.dut.logger.info(
                "There is no resource allocated to VM [%s]." % vm)
            return False
        if resource == '':
            return True
        if resource not in self.allocated_info[vm]:
            self.dut.logger.info(
                "There is no resource [%s] allocated to VM [%s] " %
                (resource, vm))
            return False
        return True

    @parallel_lock()
    def free_cpu(self, vm):
        if self.__vm_has_resource(vm, 'cores'):
            for core in self.allocated_info[vm]['cores']:
                self.__core_unused(core)
            self.allocated_info[vm].pop('cores')

    @parallel_lock()
    def alloc_pf(self, vm='', number=-1, socket=-1, pflist=[]):
        """
        There're two options for request pf devices for vm.
        If number is not -1, just allocate pf device from not used pfs.
        If list is not None, will allocate pf devices after checked.
        """
        ports = []

        if number != -1:
            for pci in self.unused_ports:
                if pci != 'unused' and number != 0:
                    if self.__port_on_socket(pci, socket) is True:
                        self.__port_used(pci)
                        ports.append(pci)
                        number = number - 1
            if number != 0:
                print("Can't allocated requested PF devices!!!")

        if pflist is not None:
            for pci in pflist:
                if self.__port_isused(pci) is True:
                    print("Port %s has been used!!!" % pci)
                else:
                    if self.__port_on_socket(pci, socket) is True:
                        self.__port_used(core)
                        ports.append(core)

        if vm not in self.allocated_info:
            self.allocated_info[vm] = {}

        self.allocated_info[vm]['ports'] = ports
        return ports

    @parallel_lock()
    def free_pf(self, vm):
        if self.__vm_has_resource(vm, 'ports'):
            for pci in self.allocated_info[vm]['ports']:
                self.__port_unused(pci)
            self.allocated_info[vm].pop('ports')

    @parallel_lock()
    def alloc_vf_from_pf(self, vm='', pf_pci='', number=-1, vflist=[]):
        """
        There're two options for request vf devices of pf device.
        If number is not -1, just allocate vf device from not used vfs.
        If list is not None, will allocate vf devices after checked.
        """
        vfs = []
        if vm == '':
            print("Alloc VF request vitual machine name!!!")
            return vfs

        if pf_pci == '':
            print("Alloc VF request PF pci address!!!")
            return vfs

        for vf_info in self.vfs_info:
            if vf_info['pf_pci'] == pf_pci:
                if vf_info['pci'] in vflist:
                    vfs.append(vf_info['pci'])
                    continue

                if number > 0:
                    vfs.append(vf_info['pci'])
                    number = number - 1

        for vf in vfs:
            self.__vf_used(vf)

        if vm not in self.allocated_info:
            self.allocated_info[vm] = {}

        self.allocated_info[vm]['vfs'] = vfs
        return vfs

    @parallel_lock()
    def free_vf(self, vm):
        if self.__vm_has_resource(vm, 'vfs'):
            for pci in self.allocated_info[vm]['vfs']:
                self.__vf_unused(pci)
            self.allocated_info[vm].pop('vfs')

    @parallel_lock()
    def add_vf_on_pf(self, pf_pci='', vflist=[]):
        """
        Add vf devices generated by specified pf devices.
        """
        # add vfs into vf info list
        vfs = []
        for vf in vflist:
            if vf not in self.vfs:
                self.vfs_info.append({'pci': vf, 'pf_pci': pf_pci})
                vfs.append(vf)
        used_vfs = ['unused'] * len(vflist)
        self.unused_vfs += vfs
        self.used_vfs += used_vfs
        self.vfs += vfs

    @parallel_lock()
    def del_vf_on_pf(self, pf_pci='', vflist=[]):
        """
        Remove vf devices generated by specified pf devices.
        """
        vfs = []
        for vf in vflist:
            for vfs_info in self.vfs_info:
                if vfs_info['pci'] == vf:
                    vfs.append(vf)

        for vf in vfs:
            try:
                index = self.vfs.index(vf)
            except:
                continue
            del self.vfs_info[index]
            del self.unused_vfs[index]
            del self.used_vfs[index]
            del self.vfs[index]

    @parallel_lock()
    def _check_port_allocated(self, port):
        """
        Check whether port has been pre-allocated
        """
        for vm_info in list(self.allocated_info.values()):
            if 'hostport' in vm_info and port == vm_info['hostport']:
                return True
            if 'serialport' in vm_info and port == vm_info['serialport']:
                return True
            if 'migrateport' in vm_info and port == vm_info['migrateport']:
                return True
            if 'displayport' in vm_info and port == (vm_info['displayport'] + 5900):
                return True
        return False

    @parallel_lock()
    def alloc_port(self, vm='', port_type='connect'):
        """
        Allocate unused host port for vm
        """
        global INIT_FREE_PORT
        global INIT_SERIAL_PORT
        global INIT_MIGRATE_PORT
        global INIT_DISPLAY_PORT

        if vm == '':
            print("Alloc host port request vitual machine name!!!")
            return None

        if port_type == 'connect':
            port = INIT_FREE_PORT
        elif port_type == 'serial':
            port = INIT_SERIAL_PORT
        elif port_type == 'migrate':
            port = INIT_MIGRATE_PORT
        elif port_type == 'display':
            port = INIT_DISPLAY_PORT + 5900

        while True:
            if self.dut.check_port_occupied(port) is False and self._check_port_allocated(port) is False:
                break
            else:
                port += 1
                continue

        if vm not in self.allocated_info:
            self.allocated_info[vm] = {}

        if port_type == 'connect':
            self.allocated_info[vm]['hostport'] = port
        elif port_type == 'serial':
            self.allocated_info[vm]['serialport'] = port
        elif port_type == 'migrate':
            self.allocated_info[vm]['migrateport'] = port
        elif port_type == 'display':
            port -= 5900
            self.allocated_info[vm]['displayport'] = port

        # do not scan port from the beginning
        if QuickScan:
            if port_type == 'connect':
                INIT_FREE_PORT = port
            elif port_type == 'serial':
                INIT_SERIAL_PORT = port
            elif port_type == 'migrate':
                INIT_MIGRATE_PORT = port
            elif port_type == 'display':
                INIT_DISPLAY_PORT = port

        return port

    @parallel_lock()
    def free_port(self, vm):
        if self.__vm_has_resource(vm, 'hostport'):
            self.allocated_info[vm].pop('hostport')
        if self.__vm_has_resource(vm, 'serialport'):
            self.allocated_info[vm].pop('serialport')
        if self.__vm_has_resource(vm, 'migrateport'):
            self.allocated_info[vm].pop('migrateport')
        if self.__vm_has_resource(vm, 'displayport'):
            self.allocated_info[vm].pop('displayport')

    @parallel_lock()
    def free_all_resource(self, vm):
        """
        Free all resource VM has been allocated.
        """
        self.free_port(vm)
        self.free_vf(vm)
        self.free_pf(vm)
        self.free_cpu(vm)

        if self.__vm_has_resource(vm):
            self.allocated_info.pop(vm)

    def get_cpu_on_vm(self, vm=''):
        """
        Return core list on specified VM.
        """
        if vm in self.allocated_info:
            if "cores" in self.allocated_info[vm]:
                return self.allocated_info[vm]['cores']

    def get_vfs_on_vm(self, vm=''):
        """
        Return vf device list on specified VM.
        """
        if vm in self.allocated_info:
            if 'vfs' in self.allocated_info[vm]:
                return self.allocated_info[vm]['vfs']

    def get_pfs_on_vm(self, vm=''):
        """
        Return pf device list on specified VM.
        """
        if vm in self.allocated_info:
            if 'ports' in self.allocated_info[vm]:
                return self.allocated_info[vm]['ports']


class simple_dut(object):

    def __init__(self):
        self.ports_info = []
        self.cores = []

    def check_port_occupied(self, port):
        return False

if __name__ == "__main__":
    dut = simple_dut()
    dut.cores = [{'thread': '1', 'socket': '0'}, {'thread': '2', 'socket': '0'},
                 {'thread': '3', 'socket': '0'}, {'thread': '4', 'socket': '0'},
                 {'thread': '5', 'socket': '0'}, {'thread': '6', 'socket': '0'},
                 {'thread': '7', 'socket': '1'}, {'thread': '8', 'socket': '1'},
                 {'thread': '9', 'socket': '1'}, {'thread': '10', 'socket': '1'},
                 {'thread': '11', 'socket': '1'}, {'thread': '12', 'socket': '1'}]

    dut.ports_info = [{'intf': 'p786p1', 'source': 'cfg', 'mac': '90:e2:ba:69:e5:e4',
                       'pci': '08:00.0', 'numa': 0, 'ipv6': 'fe80::92e2:baff:fe69:e5e4',
                       'peer': 'IXIA:6.5', 'type': '8086:10fb'},
                      {'intf': 'p786p2', 'source': 'cfg', 'mac': '90:e2:ba:69:e5:e5',
                       'pci': '08:00.1', 'numa': 0, 'ipv6': 'fe80::92e2:baff:fe69:e5e5',
                       'peer': 'IXIA:6.6', 'type': '8086:10fb'},
                      {'intf': 'p787p1', 'source': 'cfg', 'mac': '90:e2:ba:69:e5:e6',
                       'pci': '84:00.0', 'numa': 1, 'ipv6': 'fe80::92e2:baff:fe69:e5e6',
                       'peer': 'IXIA:6.7', 'type': '8086:10fb'},
                      {'intf': 'p787p2', 'source': 'cfg', 'mac': '90:e2:ba:69:e5:e7',
                       'pci': '84:00.1', 'numa': 1, 'ipv6': 'fe80::92e2:baff:fe69:e5e7',
                       'peer': 'IXIA:6.8', 'type': '8086:10fb'}]

    virt_pool = VirtResource(dut)
    print("Alloc two PF devices on socket 1 from VM")
    print(virt_pool.alloc_pf(vm='test1', number=2, socket=1))

    virt_pool.add_vf_on_pf(pf_pci='08:00.0', vflist=[
                           '08:10.0', '08:10.2', '08:10.4', '08:10.6'])
    virt_pool.add_vf_on_pf(pf_pci='08:00.1', vflist=[
                           '08:10.1', '08:10.3', '08:10.5', '08:10.7'])
    print("Add VF devices to resource pool")
    print(virt_pool.vfs_info)

    print("Alloc VF device from resource pool")
    print(virt_pool.alloc_vf_from_pf(vm='test1', pf_pci='08:00.0', number=2))
    print(virt_pool.used_vfs)
    print("Alloc VF device from resource pool")
    print(virt_pool.alloc_vf_from_pf(vm='test2', pf_pci='08:00.1', vflist=['08:10.3', '08:10.5']))
    print(virt_pool.used_vfs)

    print("Del VF devices from resource pool")
    virt_pool.del_vf_on_pf(pf_pci='08:00.0', vflist=['08:10.4', '08:10.2'])
    print(virt_pool.vfs_info)

    virt_pool.reserve_cpu('e')
    print("Reserve three cores from resource pool")
    print(virt_pool.unused_cores)
    print("Alloc two cores on socket1 for VM-test1")
    print(virt_pool.alloc_cpu(vm="test1", number=2, socket=1))
    print("Alloc two cores in list for VM-test2")
    print(virt_pool.alloc_cpu(vm="test2", corelist=['4', '5']))
    print("Alloc two cores for VM-test3")
    print(virt_pool.alloc_cpu(vm="test3", number=2))
    print("Alloc port for VM-test1")
    print(virt_pool.alloc_port(vm='test1'))
    print("Alloc information after allocated")
    print(virt_pool.allocated_info)

    print("Get cores on VM-test1")
    print(virt_pool.get_cpu_on_vm("test1"))
    print("Get pfs on VM-test1")
    print(virt_pool.get_pfs_on_vm("test1"))
    print("Get vfs on VM-test2")
    print(virt_pool.get_vfs_on_vm("test2"))
