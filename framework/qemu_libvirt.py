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

import os
import re
import time
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import ElementTree

import framework.utils as utils

from .config import VIRTCONF, VirtConf
from .dut import Dut
from .exception import StartVMFailedException
from .logger import getLogger
from .ssh_connection import SSHConnection
from .virt_base import VirtBase
from .virt_resource import VirtResource


class LibvirtKvm(VirtBase):
    DEFAULT_BRIDGE = 'br0'
    QEMU_IFUP = "#!/bin/sh\n\n" + \
                "set -x\n\n" + \
                "switch=%(switch)s\n\n" + \
                "if [ -n '$1' ];then\n" + \
                "   tunctl -t $1\n" + \
                "   ip link set $1 up\n" + \
                "   sleep 0.5s\n" + \
                "   brctl addif $switch $1\n" + \
                "   exit 0\n" + \
                "else\n" + \
                "   echo 'Error: no interface specified'\n" + \
                "   exit 1\n" + \
                "fi"
    QEMU_IFUP_PATH = '/etc/qemu-ifup'

    def __init__(self, dut, name, suite):
        # initialize virtualization base module
        super(LibvirtKvm, self).__init__(dut, name, suite)

        # initialize qemu emulator, example: qemu-system-x86_64
        self.qemu_emulator = self.get_qemu_emulator()

        self.logger = dut.logger
        # disk and pci device default index
        self.diskindex = 'a'
        self.controllerindex = 0
        self.pciindex = 10

        # configure root element
        self.root = ElementTree()
        self.domain = ET.Element('domain')
        # replace root element
        self.root._setroot(self.domain)
        # add xml header
        self.domain.set('type', 'kvm')
        self.domain.set('xmlns:qemu',
                        'http://libvirt.org/schemas/domain/qemu/1.0')
        ET.SubElement(self.domain, 'name').text = name

        # devices pass-through into vm
        self.pci_maps = []

        # default login user,password
        self.username = self.host_dut.crb['user']
        self.password = self.host_dut.crb['pass']

        # internal variable to track whether default nic has been added
        self.__default_nic = False
        self.__default_nic_pci = ''

        # set some default values for vm,
        # if there is not the values of the specified options
        self.set_vm_default()

    def get_qemu_emulator(self):
        """
        Get the qemu emulator based on the crb.
        """
        arch = self.host_session.send_expect('uname -m', '# ')
        return '/usr/bin/qemu-system-' + arch

    def get_virt_type(self):
        return 'LIBVIRT'

    def has_virtual_ability(self):
        """
        check and setup host virtual ability
        """
        arch = self.host_session.send_expect('uname -m', '# ')
        if arch == 'aarch64':
            out = self.host_session.send_expect(
                'service libvirtd status', "# ")
            if 'active (running)' not in out:
                return False
            return True

        out = self.host_session.send_expect('cat /proc/cpuinfo | grep flags',
                                            '# ')
        rgx = re.search(' vmx ', out)
        if rgx:
            pass
        else:
            self.host_logger.warning("Hardware virtualization "
                                     "disabled on host!!!")
            return False

        out = self.host_session.send_expect('lsmod | grep kvm', '# ')
        if 'kvm' not in out or 'kvm_intel' not in out:
            return False

        out = self.host_session.send_expect('service libvirtd status', "# ")
        if 'active (running)' not in out:
            return False

        return True

    def load_virtual_mod(self):
        self.host_session.send_expect('modprobe kvm', '# ')
        self.host_session.send_expect('modprobe kvm_intel', '# ')

    def unload_virtual_mod(self):
        self.host_session.send_expect('rmmod kvm_intel', '# ')
        self.host_session.send_expect('rmmod kvm', '# ')

    def disk_image_is_ok(self, image):
        """
        Check if the image is OK and no error.
        """
        pass

    def add_vm_mem(self, **options):
        """
        Options:
            size : memory size, measured in MB
            hugepage : guest memory allocated using hugepages
        """
        if 'size' in list(options.keys()):
            memory = ET.SubElement(self.domain, 'memory', {'unit': 'MB'})
            memory.text = options['size']
        if 'hugepage' in list(options.keys()):
            memoryBacking = ET.SubElement(self.domain, 'memoryBacking')
            ET.SubElement(memoryBacking, 'hugepages')

    def set_vm_cpu(self, **options):
        """
        Set VM cpu.
        """
        index = self.find_option_index('cpu')
        if index:
            self.params[index] = {'cpu': [options]}
        else:
            self.params.append({'cpu': [options]})

    def add_vm_cpu(self, **options):
        """
        'number' : '4' #number of vcpus
        'cpupin' : '3 4 5 6' # host cpu list
        """
        vcpu = 0
        if 'number' in list(options.keys()):
            vmcpu = ET.SubElement(self.domain, 'vcpu', {'placement': 'static'})
            vmcpu.text = options['number']
        if 'cpupin' in list(options.keys()):
            cputune = ET.SubElement(self.domain, 'cputune')
            # cpu resource will be allocated
            req_cpus = options['cpupin'].split()
            cpus = self.virt_pool.alloc_cpu(vm=self.vm_name, corelist=req_cpus)
            for cpu in cpus:
                ET.SubElement(cputune, 'vcpupin', {
                              'vcpu': '%d' % vcpu, 'cpuset': cpu})
                vcpu += 1
        else:  # request cpu from vm resource pool
            cpus = self.virt_pool.alloc_cpu(
                self.vm_name, number=int(options['number']))
            for cpu in cpus:
                ET.SubElement(cputune, 'vcpupin', {
                              'vcpu': '%d' % vcpu, 'cpuset': cpu})
                vcpu += 1

    def get_vm_cpu(self):
        cpus = self.virt_pool.get_cpu_on_vm(self.vm_name)
        return cpus

    def add_vm_qga(self, options):
        qemu = ET.SubElement(self.domain, 'qemu:commandline')
        ET.SubElement(qemu, 'qemu:arg', {'value': '-chardev'})
        ET.SubElement(qemu, 'qemu:arg',
                      {'value': 'socket,path=/tmp/' +
                                '%s_qga0.sock,' % self.vm_name +
                                'server,nowait,id=%s_qga0' % self.vm_name})
        ET.SubElement(qemu, 'qemu:arg', {'value': '-device'})
        ET.SubElement(qemu, 'qemu:arg', {'value': 'virtio-serial'})
        ET.SubElement(qemu, 'qemu:arg', {'value': '-device'})
        ET.SubElement(qemu, 'qemu:arg',
                      {'value': 'virtserialport,' +
                                'chardev=%s_qga0' % self.vm_name +
                                ',name=org.qemu.guest_agent.0'})
        self.qga_sock_path = '/tmp/%s_qga0.sock' % self.vm_name

    def add_vm_os(self, **options):
        os = self.domain.find('os')
        if 'loader' in list(options.keys()):
            loader = ET.SubElement(
                os, 'loader', {'readonly': 'yes', 'type': 'pflash'})
            loader.text = options['loader']
        if 'nvram' in list(options.keys()):
            nvram = ET.SubElement(os, 'nvram')
            nvram.text = options['nvram']

    def set_vm_default_aarch64(self):
        os = ET.SubElement(self.domain, 'os')
        type = ET.SubElement(
            os, 'type', {'arch': 'aarch64', 'machine': 'virt'})
        type.text = 'hvm'
        ET.SubElement(os, 'boot', {'dev': 'hd'})
        features = ET.SubElement(self.domain, 'features')
        ET.SubElement(features, 'acpi')

        ET.SubElement(self.domain, 'cpu',
                      {'mode': 'host-passthrough', 'check': 'none'})

    def set_vm_default_x86_64(self):
        os = ET.SubElement(self.domain, 'os')
        type = ET.SubElement(
            os, 'type', {'arch': 'x86_64', 'machine': 'pc-i440fx-1.6'})
        type.text = 'hvm'
        ET.SubElement(os, 'boot', {'dev': 'hd'})
        features = ET.SubElement(self.domain, 'features')
        ET.SubElement(features, 'acpi')
        ET.SubElement(features, 'apic')
        ET.SubElement(features, 'pae')

        ET.SubElement(self.domain, 'cpu', {'mode': 'host-passthrough'})
        self.__default_nic_pci = '00:1f.0'

    def set_vm_default(self):
        arch = self.host_session.send_expect('uname -m', '# ')
        set_default_func = getattr(self, 'set_vm_default_' + arch)
        if callable(set_default_func):
            set_default_func()

        # qemu-kvm for emulator
        device = ET.SubElement(self.domain, 'devices')
        ET.SubElement(device, 'emulator').text = self.qemu_emulator

        # qemu guest agent
        self.add_vm_qga(None)

        # add default control interface
        if not self.__default_nic:
            if len(self.__default_nic_pci) > 0:
                def_nic = {'type': 'nic', 'opt_hostfwd': '',
                           'opt_addr': self.__default_nic_pci}
            else:
                def_nic = {'type': 'nic', 'opt_hostfwd': ''}
            self.add_vm_net(**def_nic)
            self.__default_nic = True

    def set_qemu_emulator(self, qemu_emulator_path):
        """
        Set the qemu emulator in the specified path explicitly.
        """
        out = self.host_session.send_expect(
            'ls %s' % qemu_emulator_path, '# ')
        if 'No such file or directory' in out:
            self.host_logger.error("No emulator [ %s ] on the DUT" %
                                   (qemu_emulator_path))
            return None
        out = self.host_session.send_expect("[ -x %s ];echo $?" %
                                            (qemu_emulator_path), '# ')
        if out != '0':
            self.host_logger.error("Emulator [ %s ] " % qemu_emulator_path +
                                   "not executable on the DUT")
            return None
        self.qemu_emulator = qemu_emulator_path

    def add_vm_qemu(self, **options):
        """
        Options:
            path: absolute path for qemu emulator
        """
        if 'path' in list(options.keys()):
            self.set_qemu_emulator(options['path'])
            # update emulator config
            devices = self.domain.find('devices')
            ET.SubElement(devices, 'emulator').text = self.qemu_emulator

    def add_vm_disk(self, **options):
        """
        Options:
            file: absolute path of disk image file
            type: image file formats
        """
        devices = self.domain.find('devices')
        disk = ET.SubElement(
            devices, 'disk', {'type': 'file', 'device': 'disk'})

        if 'file' not in options:
            return False

        ET.SubElement(disk, 'source', {'file': options['file']})
        if 'opt_format' not in options:
            disk_type = 'raw'
        else:
            disk_type = options['opt_format']

        ET.SubElement(disk, 'driver', {'name': 'qemu', 'type': disk_type})

        if 'opt_bus' not in options:
            bus = 'virtio'
        else:
            bus = options['opt_bus']
        if 'opt_dev' not in options:
            dev = 'vd%c' % self.diskindex
            self.diskindex = chr(ord(self.diskindex) + 1)
        else:
            dev = options['opt_dev']
        ET.SubElement(
            disk, 'target', {'dev': dev, 'bus': bus})

        if 'opt_controller' in options:
            controller = ET.SubElement(devices, 'controller',
                                       {'type': bus,
                                        'index': hex(self.controllerindex)[2:],
                                        'model': options['opt_controller']})
            self.controllerindex += 1
            ET.SubElement(
                controller, 'address',
                {'type': 'pci', 'domain': '0x0000', 'bus': hex(self.pciindex),
                 'slot': '0x00', 'function': '0x00'})
            self.pciindex += 1

    def add_vm_daemon(self, **options):
        pass

    def add_vm_vnc(self, **options):
        """
        Add VM display option
        """
        disable = options.get('disable')
        if disable and disable == 'True':
            return
        else:
            displayNum = options.get('displayNum')
            port = \
                displayNum if displayNum else \
                self.virt_pool.alloc_port(self.vm_name, port_type="display")
        ip = self.host_dut.get_ip_address()
        # set main block
        graphics = {
            'type': 'vnc',
            'port': port,
            'autoport': 'yes',
            'listen': ip,
            'keymap': 'en-us', }

        devices = self.domain.find('devices')
        graphics = ET.SubElement(devices, 'graphics', graphics)
        # set sub block
        listen = {
            'type': 'address',
            'address': ip, }
        ET.SubElement(graphics, 'listen', listen)

    def add_vm_serial_port(self, **options):
        if 'enable' in list(options.keys()):
            if options['enable'].lower() == 'yes':
                devices = self.domain.find('devices')
                if 'opt_type' in list(options.keys()):
                    serial_type = options['opt_type']
                else:
                    serial_type = 'unix'
                if serial_type == 'pty':
                    serial = ET.SubElement(
                        devices, 'serial', {'type': serial_type})
                    ET.SubElement(serial, 'target', {'port': '0'})
                elif serial_type == 'unix':
                    serial = ET.SubElement(
                        devices, 'serial', {'type': serial_type})
                    self.serial_path = "/tmp/%s_serial.sock" % self.vm_name
                    ET.SubElement(
                        serial,
                        'source',
                        {'mode': 'bind', 'path': self.serial_path})
                    ET.SubElement(serial, 'target', {'port': '0'})
                else:
                    msg = "Serial type %s is not supported!" % serial_type
                    self.logger.error(msg)
                    return False
                console = ET.SubElement(
                    devices, 'console', {'type': serial_type})
                ET.SubElement(
                    console, 'target', {'type': 'serial', 'port': '0'})

    def add_vm_login(self, **options):
        """
        options:
            user: login username of virtual machine
            password: login password of virtual machine
        """
        if 'user' in list(options.keys()):
            user = options['user']
            self.username = user

        if 'password' in list(options.keys()):
            password = options['password']
            self.password = password

    def get_vm_login(self):
        return (self.username, self.password)

    def __parse_pci(self, pci_address):
        pci_regex = r"([0-9a-fA-F]{1,2}):([0-9a-fA-F]{1,2})" + \
            ".([0-9a-fA-F]{1,2})"
        pci_regex_domain = r"([0-9a-fA-F]{1,4}):([0-9a-fA-F]{1,2}):" + \
            "([0-9a-fA-F]{1,2}).([0-9a-fA-F]{1,2})"
        m = re.match(pci_regex, pci_address)
        if m is not None:
            bus = m.group(1)
            slot = m.group(2)
            func = m.group(3)
            dom = '0'
            return (bus, slot, func, dom)
        m = re.match(pci_regex_domain, pci_address)
        if m is not None:
            bus = m.group(2)
            slot = m.group(3)
            func = m.group(4)
            dom = m.group(1)
            return (bus, slot, func, dom)
        return None

    def set_vm_device(self, driver='pci-assign', **opts):
        opts['driver'] = driver
        self.add_vm_device(**opts)

    def __generate_net_config_script(self, switch=DEFAULT_BRIDGE):
        """
        Generate a script for qemu emulator to build a tap device
        between host and guest.
        """
        qemu_ifup = self.QEMU_IFUP % {'switch': switch}
        file_name = os.path.basename(self.QEMU_IFUP_PATH)
        tmp_file_path = '/tmp/%s' % file_name
        self.host_dut.create_file(qemu_ifup, tmp_file_path)
        self.host_session.send_expect(
            'mv -f ~/%s %s' % (file_name, self.QEMU_IFUP_PATH), '# ')
        self.host_session.send_expect(
            'chmod +x %s' % self.QEMU_IFUP_PATH, '# ')

    def __parse_opt_setting(self, opt_settings):
        if '=' not in opt_settings:
            msg = 'wrong opt_settings setting'
            raise Exception(msg)
        setting = [item.split('=') for item in opt_settings.split(',')]
        return dict(setting)

    def __get_pci_addr_config(self, pci):
        pci = self.__parse_pci(pci)
        if pci is None:
            msg = 'Invalid guestpci for host device pass-through !!!'
            self.logger.error(msg)
            return False
        bus, slot, func, dom = pci
        config = {
            'type': 'pci', 'domain': '0x%s' % dom, 'bus': '0x%s' % bus,
            'slot': '0x%s' % slot, 'function': '0x%s' % func}
        return config

    def __write_config(self, parent, configs):
        for config in configs:
            node_name = config[0]
            opt = config[1]
            node = ET.SubElement(parent, node_name, opt)
            if len(config) == 3:
                self.__write_config(node, config[2])

    def __set_vm_bridge_interface(self, **options):
        mac = options.get('opt_mac')
        opt_br = options.get('opt_br')
        if not mac or not opt_br:
            msg = "Missing some bridge device option !!!"
            self.logger.error(msg)
            return False
        _config = [
            ['mac', {'address': mac}],
            ['source', {'bridge': opt_br, }],
            ['model', {'type': 'virtio', }]]
        config = [['interface', {'type': 'bridge'}, _config]]
        # set xml file
        parent = self.domain.find('devices')
        self.__write_config(parent, config)

    def __add_vm_virtio_user_pci(self, **options):
        mac = options.get('opt_mac')
        mode = options.get('opt_server') or 'client'
        # unix socket path of character device
        sock_path = options.get('opt_path')
        queue = options.get('opt_queue')
        settings = options.get('opt_settings')
        # pci address in virtual machine
        pci = options.get('opt_host')
        if not mac or not sock_path:
            msg = "Missing some vhostuser device option !!!"
            self.logger.error(msg)
            return False
        node_name = 'interface'
        # basic options
        _config = [
            ['mac', {'address': mac}],
            ['source', {'type': 'unix',
                        'path': sock_path,
                        'mode': mode, }],
            ['model', {'type': 'virtio', }]]
        # append pci address
        if pci:
            _config.append(['address', self.__get_pci_addr_config(pci)])
        if queue or settings:
            drv_config = {'name': 'vhost'}
            if settings:
                _sub_opt = self.__parse_opt_setting(settings)
                drv_opt = {}
                guest_opt = {}
                host_opt = {}
                for key, value in _sub_opt.items():
                    if key.startswith('host_'):
                        host_opt[key[5:]] = value
                        continue
                    if key.startswith('guest_'):
                        guest_opt[key[6:]] = value
                        continue
                    drv_opt[key] = value
                drv_config.update(drv_opt)
                sub_drv_config = []
                if host_opt:
                    sub_drv_config.append(['host', host_opt])
                if guest_opt:
                    sub_drv_config.append(['guest', guest_opt])
            # The optional queues attribute controls the number of queues to be
            # used for either Multiqueue virtio-net or vhost-user network
            # interfaces. Each queue will potentially be handled by a different
            # processor, resulting in much higher throughput. virtio-net since
            # 1.0.6 (QEMU and KVM only) vhost-user since 1.2.17(QEMU and KVM
            # only).
            if queue:
                drv_config.update({'queues': queue, })
            # set driver config
            if sub_drv_config:
                _config.append(['driver', drv_config, sub_drv_config])
            else:
                _config.append(['driver', drv_config])
        config = [[node_name, {'type': 'vhostuser'}, _config]]
        # set xml file
        parent = self.domain.find('devices')
        self.__write_config(parent, config)

    def __add_vm_pci_assign(self, **options):
        devices = self.domain.find('devices')
        # add hostdev config block
        config = {
            'mode': 'subsystem',
            'type': 'pci',
            'managed': 'yes'}
        hostdevice = ET.SubElement(devices, 'hostdev', config)
        # add hostdev/source config block
        pci_addr = options.get('opt_host')
        if not pci_addr:
            msg = "Missing opt_host for device option!!!"
            self.logger.error(msg)
            return False
        pci = self.__parse_pci(pci_addr)
        if pci is None:
            return False
        bus, slot, func, dom = pci
        source = ET.SubElement(hostdevice, 'source')
        config = {
            'domain': '0x%s' % dom,
            'bus': '0x%s' % bus,
            'slot': '0x%s' % slot,
            'function': '0x%s' % func}
        ET.SubElement(source, 'address', config)
        # add hostdev/source/address config block
        guest_pci_addr = options.get('guestpci')
        if not guest_pci_addr:
            guest_pci_addr = '0000:%s:00.0' % hex(self.pciindex)[2:]
            self.pciindex += 1
        config = self.__get_pci_addr_config(guest_pci_addr)
        ET.SubElement(hostdevice, 'address', config)
        # save host and guest pci address mapping
        pci_map = {}
        pci_map['hostpci'] = pci_addr
        pci_map['guestpci'] = guest_pci_addr
        self.pci_maps.append(pci_map)

    def add_vm_device(self, **options):
        """
        options:
            pf_idx: device index of pass-through device
            guestpci: assigned pci address in vm
        """
        driver_table = {
            'vhost-user':
                self.__add_vm_virtio_user_pci,
            'bridge':
                self.__set_vm_bridge_interface,
            'pci-assign':
                self.__add_vm_pci_assign,
        }
        driver = options.get('driver')
        if not driver or driver not in list(driver_table.keys()):
            driver = 'pci-assign'
            msg = 'use {0} configuration as default driver'.format(driver)
            self.logger.warning(msg)
        func = driver_table.get(driver)
        func(**options)

    def add_vm_net(self, **options):
        """
        Options:
            default: create e1000 netdev and redirect ssh port
        """
        if 'type' in list(options.keys()):
            if options['type'] == 'nic':
                self.__add_vm_net_nic(**options)
            elif options['type'] == 'tap':
                self.__add_vm_net_tap(**options)

    def __add_vm_net_nic(self, **options):
        """
        type: nic
        opt_model: ["e1000" | "virtio" | "i82551" | ...]
                   Default is e1000.
        opt_addr: ''
            note: PCI cards only.
        """
        if 'opt_model' in list(options.keys()):
            model = options['opt_model']
        else:
            model = 'e1000'

        if 'opt_hostfwd' in list(options.keys()):
            port = self.virt_pool.alloc_port(self.vm_name)
            if port is None:
                return
            dut_ip = self.host_dut.crb['IP']
            self.vm_ip = '%s:%d' % (dut_ip, port)

        qemu = ET.SubElement(self.domain, 'qemu:commandline')
        ET.SubElement(qemu, 'qemu:arg', {'value': '-net'})
        if 'opt_addr' in list(options.keys()):
            pci = self.__parse_pci(options['opt_addr'])
            if pci is None:
                return False
            bus, slot, func, dom = pci
            ET.SubElement(qemu, 'qemu:arg',
                          {'value': 'nic,model=e1000,addr=0x%s' % slot})
        else:
            ET.SubElement(qemu, 'qemu:arg',
                          {'value': 'nic,model=e1000,addr=0x%x'
                           % self.pciindex})
            self.pciindex += 1

        if 'opt_hostfwd' in list(options.keys()):
            ET.SubElement(qemu, 'qemu:arg', {'value': '-net'})
            ET.SubElement(qemu, 'qemu:arg', {'value': 'user,hostfwd='
                                             'tcp:%s:%d-:22' % (dut_ip, port)})

    def __add_vm_net_tap(self, **options):
        """
        type: tap
        opt_br: br0
            note: if choosing tap, need to specify bridge name,
                  else it will be br0.
        opt_script: QEMU_IFUP_PATH
            note: if not specified, default is self.QEMU_IFUP_PATH.
        """
        _config = [['target', {'dev': 'tap0'}]]
        # add bridge info
        opt_br = options.get('opt_br')
        bridge = opt_br if opt_br else self.DEFAULT_BRIDGE
        _config.append(['source', {'bridge': bridge}])
        self.__generate_net_config_script(str(bridge))
        # add network configure script path
        opt_script = options.get('opt_script')
        script_path = opt_script if opt_script else self.QEMU_IFUP_PATH
        _config.append(['script', {'path': script_path}])
        config = [['interface', {'type': 'bridge'}, _config]]
        # set xml file
        parent = self.domain.find('devices')
        self.__write_config(parent, config)

    def add_vm_virtio_serial_channel(self, **options):
        """
        Options:
            path: virtio unix socket absolute path
            name: virtio serial name in vm
        """
        devices = self.domain.find('devices')
        channel = ET.SubElement(devices, 'channel', {'type': 'unix'})
        for opt in ['path', 'name']:
            if opt not in list(options.keys()):
                msg = "invalid virtio serial channel setting"
                self.logger.error(msg)
                return

        ET.SubElement(
            channel, 'source', {'mode': 'bind', 'path': options['path']})
        ET.SubElement(
            channel, 'target', {'type': 'virtio', 'name': options['name']})
        ET.SubElement(channel, 'address', {'type': 'virtio-serial',
                                           'controller': '0', 'bus': '0',
                                           'port': '%d' % self.pciindex})
        self.pciindex += 1

    def get_vm_ip(self):
        return self.vm_ip

    def get_pci_mappings(self):
        """
        Return guest and host pci devices mapping structure
        """
        return self.pci_maps

    def __control_session(self, command, *args):
        """
        Use the qemu guest agent service to control VM.
        Note:
            :command: there are these commands as below:
                       cat, fsfreeze, fstrim, halt, ifconfig, info,\
                       ping, powerdown, reboot, shutdown, suspend
            :args: give different args by the different commands.
        """
        if not self.qga_sock_path:
            self.host_logger.info(
                "No QGA service between host [ %s ] and guest [ %s ]" %
                (self.host_dut.Name, self.vm_name))
            return None

        cmd_head = '~/QMP/' + \
            "qemu-ga-client " + \
            "--address=%s %s" % \
            (self.qga_sock_path, command)

        cmd = cmd_head
        for arg in args:
            cmd = cmd_head + ' ' + str(arg)

        if command is "ping":
            out = self.host_session.send_expect(cmd, '# ', int(args[0]))
        else:
            out = self.host_session.send_expect(cmd, '# ')

        return out

    def _start_vm(self):
        xml_file = "/tmp/%s.xml" % self.vm_name
        if os.path.exists(xml_file):
            os.remove(xml_file)
        self.root.write(xml_file)
        with open(xml_file, 'r') as fp:
            content = fp.read()
        doc = minidom.parseString(content)
        vm_content = doc.toprettyxml(indent='    ')
        with open(xml_file, 'w') as fp:
            fp.write(vm_content)
        self.host_session.copy_file_to(xml_file)
        time.sleep(2)

        self.host_session.send_expect("virsh", "virsh #")
        self.host_session.send_expect(
            "create /root/%s.xml" % self.vm_name, "virsh #")
        self.host_session.send_expect("quit", "# ")
        out = self.__control_session('ping', '120')

        if "Not responded" in out:
            raise StartVMFailedException("Not response in 120 seconds!!!")

        self.__wait_vmnet_ready()

    def __wait_vmnet_ready(self):
        """
        wait for 120 seconds for vm net ready
        10.0.2.* is the default ip address allocated by qemu
        """
        count = 20
        while count:
            out = self.__control_session('ifconfig')
            if "10.0.2" in out:
                pos = self.vm_ip.find(':')
                ssh_key = '[' + self.vm_ip[:pos] + ']' + self.vm_ip[pos:]
                os.system('ssh-keygen -R %s' % ssh_key)
                return True
            time.sleep(6)
            count -= 1

        raise StartVMFailedException("Virtual machine control net not ready " +
                                     "in 120 seconds!!!")

    def stop(self):
        self.__control_session("shutdown")
        time.sleep(5)
